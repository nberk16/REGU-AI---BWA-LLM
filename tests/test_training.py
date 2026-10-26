"""Eğitim verisi testleri (docs/12_egitim_verisi.md): biçim birliği ve repodaki dosyaların tutarlılığı."""

import gzip
import json
from pathlib import Path

from ideal.check import check
from ideal.teacher import input_sha
from prompting.templates import build_messages, render_notes
from ideal.gold import build as build_gold
from training.data import SETS, accepted, normalize, warn_kernaussagen

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> list[dict]:
    with gzip.open(ROOT / "gpu" / "data" / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def test_normalize_only_minus_before_digits():
    assert normalize("Ergebnis –102 T€ (Vj. –5,0 %), Marge −3,1 %") == "Ergebnis -102 T€ (Vj. -5,0 %), Marge -3,1 %"
    assert normalize("Buchungseffekt – etwa Wareneingänge") == "Buchungseffekt – etwa Wareneingänge"
    assert normalize("| Hypothese | – |") == "| Hypothese | – |"


def test_committed_training_data_matches_outputs():
    for out_name, teacher_set, variant in SETS:
        rows = _load(out_name)
        requests, ok = accepted(teacher_set)
        kept = [r["id"] for r in requests if r["id"] in ok
                and not warn_kernaussagen(normalize(ok[r["id"]]["text"]), r["plan"])[2]]
        assert [r["id"] for r in rows] == kept
        by_id = {r["id"]: r for r in requests}
        for row in rows[::25]:
            req = by_id[row["id"]]
            system, user, assistant = row["messages"]
            assert row["variant"] == variant and assistant["role"] == "assistant"
            assert row["teacher"]["input_sha"] == input_sha(req) == ok[row["id"]]["input_sha"]
            expected = warn_kernaussagen(normalize(ok[row["id"]]["text"]), req["plan"])[0]
            assert assistant["content"] == expected and "–1" not in assistant["content"]
            assert check(assistant["content"], req["plan"], req["facts"], req["notes"])["ok"]
            if variant == "ohne_kontext":
                assert [system, user] == build_messages(req["facts"], None)
            else:
                assert f"KONTEXTNOTIZEN:\n{render_notes(req['notes'])}\n\n" in user["content"]
                assert system == build_messages(req["facts"], None)[0]


def test_warning_added_only_where_missing():
    plan = {"kernaussagen": [{"art": "ergebnis", "position": "Betriebsergebnis"},
                             {"art": "position", "position": "Umsatzerlöse"},
                             {"art": "hinweis", "position": "Rohertragsquote"}],
            "hinweise": [{"position": "Rohertragsquote", "art": "warnung",
                          "hypothese": "möglicher Buchungseffekt, etwa Wareneingänge im falschen Monat"}]}
    head = "**Kernaussagen Mai 2026**\n\n1. Ergebnis.\n2. Umsatz.\n3. Die Rohertragsquote fällt auf 24,2 %.\n\n"
    text, added, deviates = warn_kernaussagen(head + "**Abweichungen im Detail**\n", plan)
    assert (added, deviates) == (1, False)
    assert "3. Die Rohertragsquote fällt auf 24,2 %. Hinweis: möglicher Buchungseffekt (Hypothese).\n" in text
    assert warn_kernaussagen(text, plan)[1] == 0                       # bereits gewarnt: nichts doppelt
    other = head.replace("3. Die Rohertragsquote", "3. Die Personalkosten")
    assert warn_kernaussagen(other + "**Abweichungen im Detail**", plan)[2]


def test_gold_set_matches_committed_file():
    rows = build_gold()                                                # bricht ab, wenn ein Goldtext die Kontrolle nicht besteht
    with open(ROOT / "ideal" / "gold" / "gold.jsonl", encoding="utf-8") as f:
        assert [json.loads(line) for line in f] == rows
    assert len(rows) == 30 and sum(r["set"] == "val_ohne" for r in rows) == 6
