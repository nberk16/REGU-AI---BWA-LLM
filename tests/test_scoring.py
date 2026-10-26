"""Puanlama (paket 9; docs/13): örnek yorum, bozulmuş metinler, toplama ve komut satırı."""

import gzip
import json
from pathlib import Path

import pytest

from facts.build import MonthContext, build_facts
from facts.schema import load_config as load_facts_config
from facts.series import load_run
from ideal.build import load_truth
from scoring import aggregate, make_month, score_text
from scoring.cli import main, visible_note_ids
from validation.context import load_notes, window_notes

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "synthetic" / "reference_seed42"
EXAMPLE = ROOT / "docs" / "examples" / "kommentar_A1-v00_2025-06.md"


@pytest.fixture(scope="module")
def month():
    fs = load_run(REFERENCE)["A1-v00"]
    cfg = load_facts_config()
    facts = build_facts(fs, "2025-06", cfg)
    mc = MonthContext(fs, fs.index("2025-06"), cfg)
    base_normals = {p["key"]: mc.normal_for_base(p["key"], mc.i - 12) for p in facts["positions"]}
    notes = window_notes(load_notes(REFERENCE), "A1-v00", "2025-06")
    return make_month(facts, notes, load_truth(REFERENCE), base_normals)


@pytest.fixture(scope="module")
def example():
    return EXAMPLE.read_text(encoding="utf-8")


def test_example_scores_well(example, month):
    s = score_text(example, month)
    assert s["format_ok"] and s["fehler"] == 0
    assert s["zahlen"]["richtig"] == s["zahlen"]["geprueft"] > 0
    assert s["quellen"]["zitiert"] == s["quellen"]["richtig"] == 3       # her kaynak planla uyumlu
    assert s["quellen"]["erfunden"] == s["quellen"]["ablenkung"] == 0
    assert s["quellen"]["zeile_zitiert"] == 4 and s["quellen"]["zeile_falsch"] == 0
    assert s["tabelle"]["gefunden"] == s["tabelle"]["kalemler"] and s["tabelle"]["ueberfluessig"] == 0
    assert s["flags"]["l1_gefunden"] == s["flags"]["l1"] == 2
    assert s["flags"]["hinweise_richtig"] == s["flags"]["hinweise"]


def test_space_thousands_count_as_format_not_value(example, month):
    s = score_text(example.replace("| 886.365 € |", "| 886 365 € |"), month)
    assert s["zahlen"]["zahlenformat"] == 1
    assert s["zahlen"]["richtig"] == s["zahlen"]["geprueft"]             # değer yine doğru
    assert not s["format_ok"]


def test_wrong_and_invented_sources(example, month):
    # Görünen ama bu sapmayı açıklamayan bir not: kaynak isabeti düşer.
    wrong = example.replace("[Quelle: Kontextnotiz 2024-06 #2]", "[Quelle: Kontextnotiz 2024-09]")
    s = score_text(wrong, month)
    assert s["quellen"]["zitiert"] - s["quellen"]["richtig"] == 1
    # Verilmemiş bir not: uydurma kaynak.
    invented = example.replace("[Quelle: Kontextnotiz 2024-06 #2]", "[Quelle: Kontextnotiz 2023-06]")
    assert score_text(invented, month)["quellen"]["erfunden"] == 1


def test_source_on_wrong_row(example, month):
    # 1.1: Planlanmış bir not, açıklamadığı bir satırın nedeni yapılıyor. Not düzeyindeki precision bunu görmez.
    moved = example.replace("[Quelle: Kontextnotiz 2024-06 #2]", "[Quelle: Kontextnotiz 2025-06 #2]")
    s = score_text(moved, month)
    assert s["quellen"]["zitiert"] == s["quellen"]["richtig"]
    assert s["quellen"]["zeile_falsch"] == 1
    agg = aggregate([s])
    assert agg["satir_atif_isabeti"] == 0.75 and agg["yanlis_satir_atif_metin"] == 1.0


def test_extra_table_row(example, month):
    row = "| Gesamtleistung | 870.947 € | Vj. 746.309 € | +124.638 € | Ursache offen | – |\n"
    anchor = "| Umsatzerlöse |"
    s = score_text(example.replace(anchor, row + anchor, 1), month)
    assert s["tabelle"]["ueberfluessig"] == 1


def test_missing_warning(example, month):
    hinweise = example.split("**Hinweise auf mögliche Verzerrungen**")[1].split("**Offene Fragen")[0]
    s = score_text(example.replace(hinweise, "\n\nKeine.\n\n"), month)
    assert s["flags"]["l1_gefunden"] == 0 and s["flags"]["hinweise"] == 0


def test_aggregate(example, month):
    good = score_text(example, month)
    bad = score_text(example.replace("| 886.365 € |", "| 886 365 € |"), month)
    agg = aggregate([good, bad])
    assert agg["n"] == 2 and agg["format_uyumu"] == 0.5 and agg["binlik_bosluk_metin"] == 0.5
    assert agg["rakam_sadakati"] == 1.0 and agg["kaynak_precision"] == 1.0


def test_visible_note_ids():
    prompt = {"messages": [{"role": "user", "content": "FACTS: …\nKONTEXTNOTIZEN:\n- [Firmenprofil] dauerhaft: x\n"
                                                       "- [Kontextnotiz 2025-06 #2] 2025-06, temporär: y\n"}]}
    assert visible_note_ids(prompt) == ["Firmenprofil", "Kontextnotiz 2025-06 #2"]
    assert visible_note_ids({"messages": [{"role": "user", "content": "KONTEXTNOTIZEN:\nKeine."}]}) == []


def test_cli_end_to_end(tmp_path, example):
    prompts = {json.loads(l)["id"]: json.loads(l)
               for l in gzip.open(ROOT / "gpu/data/test_rag_alle.jsonl.gz", "rt", encoding="utf-8")}
    assert "A1-v00_2025-06" in prompts
    with open(tmp_path / "demo_rag_alle.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "A1-v00_2025-06", "variant": "rag_alle", "text": example}) + "\n")
    assert main([str(tmp_path)]) == 0
    [row] = [json.loads(l) for l in open(tmp_path / "scores.jsonl", encoding="utf-8")]
    assert row["system"] == "demo_rag_alle" and row["score"]["format_ok"]
    assert "Format uyumu" in (tmp_path / "scores.md").read_text(encoding="utf-8")


def test_cli_several_folders(tmp_path, example):
    # Ablation tablosu: FT çıktıları ve baseline ayrı klasörlerde; puanlar ilk klasöre yazılır.
    a, b = tmp_path / "eval", tmp_path / "baseline"
    for folder, name in ((a, "ft_rag_rag_alle"), (b, "baseline_rag_alle")):
        folder.mkdir()
        with open(folder / f"{name}.jsonl", "w", encoding="utf-8") as f:
            f.write(json.dumps({"id": "A1-v00_2025-06", "variant": "rag_alle", "text": example}) + "\n")
    assert main([str(a), str(b)]) == 0
    systems = [json.loads(l)["system"] for l in open(a / "scores.jsonl", encoding="utf-8")]
    assert systems == ["baseline_rag_alle", "ft_rag_rag_alle"] and not (b / "scores.jsonl").exists()
    with pytest.raises(SystemExit):
        main([str(a), str(a)])
