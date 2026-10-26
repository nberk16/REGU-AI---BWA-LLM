"""Katman 2 (bilgi tabanı ve getirme) testleri (docs/09). Testler BGE-M3 yerine hafif karma embedding kullanır."""

import importlib.util
import json
import re
import shutil
from pathlib import Path

import pytest

pytest.importorskip("chromadb")

from facts.build import build_facts, commentable_periods  # noqa: E402
from facts.schema import BASE_LINES, RATIOS, SUMMARY_LINES  # noqa: E402
from facts.schema import load_config as load_facts_config  # noqa: E402
from facts.series import load_run  # noqa: E402
from generator.pipeline import generate_run  # noqa: E402
from generator.writer import write_run  # noqa: E402
from rag.cli import main as rag_main  # noqa: E402
from rag.documents import load_knowledge, load_notes, notes_to_docs, period_index  # noqa: E402
from rag.embedding import HashingEmbedder  # noqa: E402
from rag.retrieve import knowledge_keys, retrieve  # noqa: E402
from rag.store import KnowledgeBase, load_config  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def run_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("rag_run")
    write_run(generate_run(["A1", "A2", "A3"], 1, 42), path)
    return path


@pytest.fixture(scope="module")
def kb(run_dir):
    kb = KnowledgeBase(HashingEmbedder())
    kb.add(load_knowledge() + notes_to_docs(load_notes(run_dir)))
    return kb


@pytest.fixture(scope="module")
def months(run_dir):
    cfg = load_facts_config()
    return [build_facts(fs, p, cfg) for fs in load_run(run_dir).values() for p in commentable_periods(fs)]


def test_knowledge_covers_all_lines_ratios_and_flag_rules():
    docs = load_knowledge()
    ka = {d.meta["key"] for d in docs if d.kind == "K-A"}
    lines = set(BASE_LINES) | set(SUMMARY_LINES) | {"betrieblicher_rohertrag", "neutraler_aufwand", "neutraler_ertrag"}
    assert ka == lines | set(RATIOS)
    rules = set(re.findall(r'_flag\("V\d", "([a-z_]+)"', (ROOT / "facts" / "flags.py").read_text(encoding="utf-8")))
    assert {d.meta["key"] for d in docs if d.kind == "K-B"} == rules | {"grundsaetze"}
    assert len({d.source_id for d in docs}) == len(docs)
    for d in docs:
        assert not re.search(r"\d", d.text), d.source_id          # rakamlar yalnızca facts ve notlardan
        assert "SKR" not in d.text                                 # [KARAR, tur 10]


def test_add_is_idempotent(kb, run_dir):
    assert kb.add(load_knowledge() + notes_to_docs(load_notes(run_dir))) == 0


def test_window_profile_and_k(kb, months):
    k = load_config()["retrieval"]["top_k"]
    for facts in months[::7]:
        res = retrieve(facts, kb)
        notes = res["notes"]
        assert notes[0].source_id == "Firmenprofil"
        dated = notes[1:]
        assert len(dated) <= k
        end = period_index(facts["period"])
        for d in dated:
            assert d.meta["firm_id"] == facts["company"]["firm_id"]
            assert end - 12 <= d.meta["period_index"] <= end
        assert [d.meta["period_index"] for d in dated] == sorted(d.meta["period_index"] for d in dated)


def test_k0_returns_whole_window(kb, months):
    facts = months[20]
    end = period_index(facts["period"])
    window = kb.window_notes(facts["company"]["firm_id"], end - 12, end)
    assert len(retrieve(facts, kb, k=0)["notes"]) == len(window) + 1


def test_knowledge_matches_flags_and_positions(kb, months):
    for facts in months[::5]:
        res = retrieve(facts, kb)
        ids = [d.meta["key"] for d in res["knowledge"]]
        assert ids[0] == "grundsaetze" and ids == knowledge_keys(facts)
        assert {f["rule"] for f in facts["flags"]} <= set(ids)
        assert {p["key"] for p in facts["positions"]} <= set(ids)


def test_deterministic(kb, months):
    facts = months[30]
    a, b = retrieve(facts, kb), retrieve(facts, kb)
    assert [d.doc_id for d in a["notes"]] == [d.doc_id for d in b["notes"]]


def test_reads_model_input_only(run_dir, tmp_path):
    copy = tmp_path / "run"
    shutil.copytree(run_dir / "model_input", copy / "model_input")
    kb = KnowledgeBase(HashingEmbedder())
    assert kb.add(notes_to_docs(load_notes(copy))) > 0


def test_embedder_mismatch_is_rejected(tmp_path):
    KnowledgeBase(HashingEmbedder(), path=tmp_path / "db").add(load_knowledge()[:2])

    class Other(HashingEmbedder):
        name = "other"

    with pytest.raises(ValueError):
        KnowledgeBase(Other(), path=tmp_path / "db")


def test_cli_retrieve_and_export(run_dir, capsys):
    firm = "A1-v00"
    assert rag_main(["retrieve", "--run", str(run_dir), "--embedder", "hashing", "--firm", firm, "--period", "2025-06"]) == 0
    out = capsys.readouterr().out
    assert "[Leitfaden Grundsätze]" in out and "[Firmenprofil]" in out
    assert rag_main(["export", "--run", str(run_dir), "--embedder", "hashing"]) == 0
    records = [json.loads(line) for line in (run_dir / "rag" / "retrieval.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(records) == 3 * 24 and all(r["notes"][0]["source_id"] == "Firmenprofil" for r in records)


def test_quality_tool_runs(run_dir, capsys):
    spec = importlib.util.spec_from_file_location("retrieval_quality", ROOT / "tools" / "retrieval_quality.py")
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    tool.main([str(run_dir), "--embedder", "hashing", "--k", "8"])
    out = capsys.readouterr().out
    assert "| multi_expanded | 8 |" in out and "| alle | alle | 100.0% | 100.0% |" in out
