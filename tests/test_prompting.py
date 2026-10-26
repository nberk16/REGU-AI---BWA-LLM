"""İstem testleri (docs/10_istem.md): sürüm 1.1, bağlamsız ve RAG varyantları, dondurulmuş 1.0."""

import json
import re
from pathlib import Path

import pytest

from facts.build import build_facts, commentable_periods
from facts.schema import load_config as load_facts_config
from facts.series import load_run
from generator.pipeline import generate_run
from generator.writer import write_run
from prompting import PROMPT_VERSION, build_messages, model_facts, v1_0
from prompting.cli import main as prompting_main
from rag.documents import load_knowledge
from rag.retrieve import knowledge_keys
from validation.check import load_config as load_validation_config
from validation.context import load_notes, window_notes

ROOT = Path(__file__).resolve().parents[1]
FACTS = ROOT / "docs" / "examples" / "facts_A1-v00_2025-06.json"
REFERENCE = ROOT / "data" / "synthetic" / "reference_seed42"
LEAKS = ("event_id", "expected_flags", "v2_candidate_decision", "distractor", "rohertrag_causes", "documented")


@pytest.fixture(scope="module")
def facts():
    return json.loads(FACTS.read_text(encoding="utf-8"))


def context_for(facts: dict, notes: list[dict]) -> dict:
    """Katman 2 kaydının yerine geçen bağlam (Chroma gerekmez): anahtarla K-A/K-B + verilen notlar."""
    by_key = {d.meta["key"]: d for d in load_knowledge()}
    knowledge = [{"source_id": by_key[k].source_id, "kind": by_key[k].kind, "text": by_key[k].text}
                 for k in knowledge_keys(facts)]
    return {"knowledge": knowledge, "notes": [{"source_id": n["source_id"], "kind": "K-C", "text": n["text"],
                                               "period": n["period"], "duration": n["duration"]} for n in notes]}


def test_trial_inputs_are_frozen_at_1_0():
    # Deneme turunda modellerin gördüğü istemler v1_0 ile birebir yeniden üretilir (docs/08, Bölüm 3).
    for line in (ROOT / "trial" / "inputs" / "cases.jsonl").read_text(encoding="utf-8").splitlines():
        case = json.loads(line)
        assert case["prompt_version"] == v1_0.PROMPT_VERSION == "1.0"
        assert v1_0.build_messages(case["facts"], case["notes"]) == case["messages"]
    assert PROMPT_VERSION != v1_0.PROMPT_VERSION


def test_system_prompt_matches_validation_format(facts):
    system = build_messages(facts)[0]["content"]
    fmt = load_validation_config()["format"]
    assert f"**Kernaussagen {facts['period_label']}**" in system
    for key in ("abweichungen", "hinweise", "fragen"):
        assert f"**{fmt[key]}**" in system
    assert "| " + " | ".join(fmt["table_header"]) + " |" in system
    assert f"{fmt['words_min']}–{fmt['words_max']} Wörter" in system
    # Deneme turu dersleri (docs/10, Bölüm 2)
    assert "nie FACTS, flags oder WISSEN" in system and "(Hypothese)" in system
    assert "keine eigenen Differenzen, Prozentsätze" in system and "null" in system
    assert "Prozentpunkte, nicht Prozent" in system


def test_model_facts_hides_only_unused_fields(facts):
    view = model_facts(facts)
    text = json.dumps(view, ensure_ascii=False)
    for hidden in ('"schema_version"', '"thresholds"', '"significance"', '"key"', "Schwelle"):
        assert hidden not in text
    assert facts["schema_version"] and "significance" in facts["positions"][0]    # orijinal değişmez
    for section in ("summary", "positions", "ratios", "flags"):
        assert len(view[section]) == len(facts[section])
    assert view["positions"][0]["previous_year_month"] == facts["positions"][0]["previous_year_month"]
    assert view["flags"] == facts["flags"] and view["comparisons"] == facts["comparisons"]


def test_without_context(facts):
    user = build_messages(facts)[1]["content"]
    assert "WISSEN:\nKeine." in user and "KONTEXTNOTIZEN:\nKeine." in user
    assert "[Quelle:" not in user and "Kontextnotiz" not in user
    assert user.endswith(f"Schreibe jetzt den Kommentar für Muster GmbH, {facts['period_label']}.")


def test_with_context(facts):
    notes = window_notes(load_notes(REFERENCE), "A1-v00", "2025-06")
    ctx = context_for(facts, notes)
    user = build_messages(facts, ctx)[1]["content"]
    wissen = user.split("WISSEN:\n")[1].split("\n\nKONTEXTNOTIZEN:")[0].splitlines()
    assert wissen[0].startswith("- Leitfaden Grundsätze: ")
    assert [line.split(": ")[0][2:] for line in wissen] == [k["source_id"] for k in ctx["knowledge"]]
    assert not any(line.startswith("- [") for line in wissen)              # köşeli parantez yalnızca notlarda
    kontext = user.split("KONTEXTNOTIZEN:\n")[1].split("\n\nSchreibe")[0].splitlines()
    assert kontext[0].startswith("- [Firmenprofil] dauerhaft: ")
    assert len(kontext) == len(notes)
    assert all(f"[{n['source_id']}]" in user for n in notes)


def test_no_ground_truth_and_no_foreign_digits(tmp_path):
    write_run(generate_run(["A2"], 1, 3), tmp_path)
    fs = load_run(tmp_path)["A2-v00"]
    notes = load_notes(tmp_path)
    cfg = load_facts_config()
    for period in commentable_periods(fs)[::6]:
        facts = build_facts(fs, period, cfg)
        ctx = context_for(facts, window_notes(notes, "A2-v00", period))
        user = build_messages(facts, ctx)[1]["content"]
        assert not any(leak in user for leak in LEAKS)
        wissen = user.split("WISSEN:\n")[1].split("\n\nKONTEXTNOTIZEN:")[0].splitlines()
        # Rakamlar yalnızca FACTS ve notlardan; kimliklerdeki kodlar ("Leitfaden V1") metin değildir.
        assert not any(re.search(r"\d", line.split(": ", 1)[1]) for line in wissen)


def test_cli_writes_both_variants(tmp_path, capsys):
    write_run(generate_run(["A1"], 1, 42), tmp_path)
    fs = load_run(tmp_path)["A1-v00"]
    notes = load_notes(tmp_path)
    cfg = load_facts_config()
    retrieval = tmp_path / "retrieval.jsonl"
    with open(retrieval, "w", encoding="utf-8") as f:
        for period in commentable_periods(fs):
            ctx = context_for(build_facts(fs, period, cfg), window_notes(notes, "A1-v00", period))
            f.write(json.dumps({"firm_id": "A1-v00", "period": period, "mode": "single", "k": 8, **ctx},
                               ensure_ascii=False) + "\n")

    assert prompting_main(["--run", str(tmp_path)]) == 0
    assert prompting_main(["--run", str(tmp_path), "--retrieval", str(retrieval)]) == 0
    bare = [json.loads(line) for line in (tmp_path / "prompts" / "ohne_kontext.jsonl").read_text(encoding="utf-8").splitlines()]
    rag = [json.loads(line) for line in (tmp_path / "prompts" / "rag_k8.jsonl").read_text(encoding="utf-8").splitlines()]
    assert len(bare) == len(rag) == 24
    assert [r["id"] for r in bare] == [r["id"] for r in rag]
    assert {r["prompt_version"] for r in bare + rag} == {PROMPT_VERSION}
    assert bare[0]["messages"][0] == rag[0]["messages"][0]                 # sistem mesajı aynı
    assert "[Firmenprofil]" in rag[0]["messages"][1]["content"]
    assert "[Firmenprofil]" not in bare[0]["messages"][1]["content"]
    assert "24 istem (rag_k8" in capsys.readouterr().out
