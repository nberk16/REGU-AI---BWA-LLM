"""Katman 4 (doğrulama) testleri (docs/07_dogrulama_katmani.md)."""

import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

from facts.build import build_facts, commentable_periods
from facts.formatting import de_int, de_signed
from facts.schema import load_config as load_facts_config
from facts.series import load_run
from validation import numbers as N
from validation.check import validate
from validation.cli import main as cli_main
from validation.context import load_notes, shift, window_notes

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data" / "synthetic" / "reference_seed42"
EXAMPLE = ROOT / "docs" / "examples" / "kommentar_A1-v00_2025-06.md"
FACTS = ROOT / "docs" / "examples" / "facts_A1-v00_2025-06.json"


@pytest.fixture(scope="module")
def facts():
    return json.loads(FACTS.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def notes():
    return window_notes(load_notes(REFERENCE), "A1-v00", "2025-06")


@pytest.fixture(scope="module")
def example():
    return EXAMPLE.read_text(encoding="utf-8")


def codes(report: dict, severity: str = "fehler") -> list[str]:
    return [f["code"] for f in report["findings"] if f["severity"] == severity]


# --- Rakam ayıklama ve yuvarlama kuralı (a) ----------------------------------------------------------

@pytest.mark.parametrize("text, unit, scale, value, decimals, sign", [
    ("886.365 €", N.EUR, 1, "886365", 0, ""),
    ("886 T€", N.EUR, 1000, "886", 0, ""),
    ("0,9 Mio. €", N.EUR, 1_000_000, "0.9", 1, ""),
    ("+19,0 %", N.PCT, 1, "19.0", 1, "+"),
    ("−4,4 Prozentpunkte", N.PP, 1, "4.4", 1, "-"),
    ("3,8 Pp.", N.PP, 1, "3.8", 1, ""),
    ("das 1,5-Fache", N.FACTOR, 1, "1.5", 1, ""),
    ("-17.002 €", N.EUR, 1, "17002", 0, "-"),
    ("12 Monate", N.PLAIN, 1, "12", 0, ""),
])
def test_extract(text, unit, scale, value, decimals, sign):
    [num] = N.extract(text)
    assert (num.unit, num.scale, num.value, num.decimals, num.sign) == (unit, scale, Decimal(value), decimals, sign)


def test_dates_and_codes_are_not_numbers():
    text = "Kontextnotiz 2025-06, Stand 30.06.2025, Periode 06/2025, zum 1. Juli, Q2, Flag V4, Variante A1-v00"
    assert N.extract(text) == []
    [year] = N.extract("Juni 2025")
    assert N.is_year(year)


@pytest.mark.parametrize("value, text, ok", [
    (41712, "42 T€", True),
    (41712, "41,7 T€", True),
    (41712, "41 T€", False),
    (41500, "42 T€", True),          # yarım yukarı
    (41499, "41 T€", True),
    (41712, "41.712 €", True),
    (41712, "41.700 €", False),      # € tam sayı ister
    (870947, "0,9 Mio. €", True),
    (18.4, "18 %", True),
    (18.4, "18,4 %", True),
    (18.4, "19 %", False),
    (18.45, "18,5 %", True),
    (-60.7, "−60,7 %", True),        # karşılaştırma mutlak değerle; işaret ayrıca denetlenir
])
def test_rounding_rule_a(value, text, ok):
    [num] = N.extract(text)
    assert N.rounds_to(value, num) is ok


def test_non_german_format():
    assert N.non_german("um 19.0 % gestiegen") == ["19.0"]
    assert N.non_german("um 19,0 % gestiegen, 1.583 €, am 30.06.2025") == []


# --- Örnek yorum ------------------------------------------------------------------------------------

def test_example_passes(example, facts, notes):
    report = validate(example, facts, notes)
    assert report["ok"], report["findings"]
    assert report["hints"] == 0
    m = report["metrics"]
    assert m["format_ok"]
    assert m["numbers"]["fidelity"] == 1.0
    assert m["numbers"]["notiz"] >= 1                     # „rund 5 %“ notla belgeli
    assert m["reasons"]["unmarked"] == 0
    assert m["reasons"]["with_source"] >= 3 and m["reasons"]["with_hypothesis"] >= 2
    assert 250 <= m["words"] <= 350


def test_example_facts_file_is_current(facts):
    firms = load_run(REFERENCE)
    assert build_facts(firms["A1-v00"], "2025-06", load_facts_config()) == facts


# --- Rakam bulguları ---------------------------------------------------------------------------------

@pytest.mark.parametrize("old, new, code", [
    ("auf 886 T€", "auf 887 T€", "zahl_unbelegt"),
    ("| −17.002 € |", "| +17.002 € |", "vorzeichen"),
    ("bei einer Rohertragsquote von 48,6 % (Vj. 52,4 %)", "bei einer um 3,8 % gesunkenen Rohertragsquote", "einheit"),
    ("| Werbe-/Reisekosten | 4.303 € |", "| Werbe-/Reisekosten | 444.983 € |", "zahl_falsche_position"),
    ("um 19,0 % auf", "um 19.0 % auf", "zahlenformat"),
])
def test_number_findings(example, facts, notes, old, new, code):
    assert example.count(old) == 1
    report = validate(example.replace(old, new), facts, notes)
    assert codes(report) == [code]


def test_note_number_needs_citation(example, facts, notes):
    anchor = "Die Gesamtleistung liegt"
    without = example.replace(anchor, "Im Vorjahresmonat fielen Messekosten von ca. 7.000 € an. " + anchor)
    assert codes(validate(without, facts, notes)) == ["zahl_notiz_ohne_quelle"]
    cited = example.replace(anchor, "Im Vorjahresmonat fielen Messekosten von ca. 7.000 € an "
                                    "[Quelle: Kontextnotiz 2024-06 #2]. " + anchor)
    report = validate(cited, facts, notes)
    assert report["ok"] and report["metrics"]["numbers"]["notiz"] == 3


# --- Kaynak ve hipotez -------------------------------------------------------------------------------

def test_reason_needs_source_or_hypothesis(example, facts, notes):
    anchor = "Die Gesamtleistung liegt"
    bad = example.replace(anchor, "Die Umsatzerlöse steigen wegen eines Großauftrags. " + anchor)
    assert codes(validate(bad, facts, notes)) == ["begruendung_ohne_kennzeichnung"]
    for ok in ("Die Umsatzerlöse steigen vermutlich wegen eines Großauftrags (Hypothese). ",
               "Die Ursache ist aus den Unterlagen nicht ersichtlich. "):
        assert validate(example.replace(anchor, ok + anchor), facts, notes)["ok"]


def test_unknown_source(example, facts, notes):
    report = validate(example.replace("[Quelle: Kontextnotiz 2025-06].", "[Quelle: Kontextnotiz 2025-07]."), facts, notes)
    assert "quelle_unbekannt" in codes(report)


def test_table_row_needs_source(example, facts, notes):
    old = "| Der Vorjahresmonat enthielt die Kosten der Fachmesse | [Quelle: Kontextnotiz 2024-06 #2] |"
    assert codes(validate(example.replace(old, "| Der Vorjahresmonat enthielt die Kosten der Fachmesse | – |"),
                          facts, notes)) == ["tabelle_ohne_quelle"]
    assert validate(example.replace(old, "| Ursache offen | – |"), facts, notes)["ok"]


# --- Format ------------------------------------------------------------------------------------------

@pytest.mark.parametrize("old, new, code", [
    ("**Hinweise auf mögliche Verzerrungen**", "**Hinweise**", "ueberschrift_unbekannt"),
    ("**Kernaussagen Juni 2025**", "**Kernaussagen Mai 2025**", "periode"),
    ("| Position | Ist |", "| Zeile | Ist |", "tabellenkopf"),
    ("**Abweichungen im Detail**", "4. Weitere Aussage.\n\n**Abweichungen im Detail**", "kernaussagen_anzahl"),
    ("und wie verteilt sie sich auf die einzelnen Monate?", "und wie verteilt sie sich.", "frage_format"),
    ("- Personalkosten: 353.499 €", "* Personalkosten: 353.499 €", "liste_format"),
])
def test_format_findings(example, facts, notes, old, new, code):
    assert example.count(old) == 1
    report = validate(example.replace(old, new), facts, notes)
    assert code in codes(report)
    assert not report["metrics"]["format_ok"]


def test_missing_section_and_text_outside(example, facts, notes):
    head, _, _ = example.partition("**Offene Fragen")
    report = validate("Entwurf:\n\n" + head, facts, notes)
    assert {"abschnitt_fehlt", "text_ausserhalb"} <= set(codes(report))


def test_coverage_hints(example, facts, notes):
    row = next(l for l in example.splitlines() if l.startswith("| Werbe-/Reisekosten"))
    report = validate(example.replace(row + "\n", ""), facts, notes)
    assert report["ok"] and codes(report, "hinweis") == ["position_fehlt"]


# --- Bağlam notları ve CLI ----------------------------------------------------------------------------

def test_window_notes(notes):
    assert shift("2025-06", -12) == "2024-06" and shift("2025-01", -1) == "2024-12"
    periods = {n["period"] for n in notes}
    assert None in periods                                   # Firmenprofil
    assert min(p for p in periods if p) >= "2024-06" and max(p for p in periods if p) <= "2025-06"
    assert {"Kontextnotiz 2024-06 #2", "Kontextnotiz 2025-06 #2"} <= {n["source_id"] for n in notes}


def test_cli(tmp_path, capsys, notes):
    out = tmp_path / "report.json"
    code = cli_main(["--text", str(EXAMPLE), "--run", str(REFERENCE), "--firm", "A1-v00", "--period", "2025-06",
                     "--json", str(out)])
    assert code == 0 and json.loads(out.read_text(encoding="utf-8"))["ok"]
    assert "Fehler: 0" in capsys.readouterr().out
    bad = tmp_path / "bad.md"
    bad.write_text(EXAMPLE.read_text(encoding="utf-8").replace("auf 886 T€", "auf 887 T€"), encoding="utf-8")
    notes_file = tmp_path / "notes.jsonl"
    notes_file.write_text("".join(json.dumps(n, ensure_ascii=False) + "\n" for n in notes), encoding="utf-8")
    assert cli_main(["--text", str(bad), "--facts", str(FACTS), "--notes", str(notes_file)]) == 1


# --- Yanlış alarm yok: facts.json'dan doğru biçimde yazılmış rakamlar her ayda kabul edilir ------------

def _tsd(x: float) -> str:
    return de_int(float(Decimal(repr(abs(x) / 1000)).quantize(Decimal(1), rounding=ROUND_HALF_UP))) + " T€"


def _pct(x: float) -> str:
    return f"{x:+.1f}".replace(".", ",") + " %"


def render(facts: dict) -> str:
    """facts.json'dan biçimsel olarak doğru, içerikçe en yalın yorum (yalnızca test için)."""
    s = {e["key"]: e for e in facts["summary"]}
    be, gl = s["betriebsergebnis"], s["gesamtleistung"]
    rq = next(r for r in facts["ratios"] if r["ratio"] == "Rohertragsquote")
    lines = [f"**Kernaussagen {facts['period_label']}**", "",
             f"1. Das Betriebsergebnis beträgt {de_int(be['actual'])} € (Vj. {de_int(be['previous_year_month']['value'])} €).",
             f"2. Die Gesamtleistung liegt bei {_tsd(gl['actual'])}; die Rohertragsquote bei "
             f"{str(rq['actual']).replace('.', ',')} % (Vj. {str(rq['previous_year_month']['value']).replace('.', ',')} %).",
             "", "**Abweichungen im Detail**", ""]
    if facts["positions"]:
        lines += ["| Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese |", "|---|---|---|---|---|---|"]
        for p in facts["positions"]:
            v = p["previous_year_month"]
            dev = de_signed(v["delta_abs"]) + " €" + (f" ({_pct(v['delta_pct'])})" if v["delta_pct"] is not None else "")
            lines.append(f"| {p['position']} | {de_int(p['actual'])} € | Vj. {de_int(v['value'])} € | {dev} | Ursache offen | – |")
    else:
        lines.append("Keine.")
    lines += ["", "**Hinweise auf mögliche Verzerrungen**", ""]
    lines += [f"- {f['position']}: {f['evidence']}" for f in facts["flags"] if f["status"] == "hinweis"] or ["Keine."]
    lines += ["", "**Offene Fragen an Buchhaltung / Steuerberater**", "", "Keine."]
    return "\n".join(lines) + "\n"


def test_no_false_alarms_on_reference_run():
    firms = load_run(REFERENCE)
    cfg = load_facts_config()
    checked = 0
    for firm in firms.values():
        for period in commentable_periods(firm):
            facts = build_facts(firm, period, cfg)
            report = validate(render(facts), facts, [])
            assert report["ok"], (firm.firm_id, period, report["findings"])
            assert report["metrics"]["numbers"]["fidelity"] == 1.0
            checked += 1
    assert checked == len(firms) * 24


# --- v1.1: deneme turundaki gerçek çıktılardan gelen toleranslar (docs/07, Bölüm 11) ------------------

def test_cosmetic_markdown_is_ignored(example, facts, notes):
    noisy = (example
             .replace("| Umsatzerlöse | 886.365 € |", "| **Umsatzerlöse** | **886.365 €** |")
             .replace("**Abweichungen im Detail**", "---\n**Abweichungen im Detail**")
             .replace("- Bestandsveränderungen FE/UE: April und Mai je 0 €, Juni −15.419 €. ",
                      "- **Bestandsveränderungen FE/UE:**\n  April und Mai je 0 €, Juni −15.419 €. "))
    report, clean = validate(noisy, facts, notes), validate(example, facts, notes)
    assert report["ok"], report["findings"]
    assert report["metrics"]["numbers"] == clean["metrics"]["numbers"]


def test_citation_without_prefix_counts_but_is_flagged(example, facts, notes):
    variant = (example.replace("[Quelle: Kontextnotiz 2025-06].", "[Kontextnotiz 2025-06].")
               .replace("[Quelle: Kontextnotiz 2025-06 #2; Kontextnotiz 2025-06]", "[Kontextnotiz 2025-06 #2; 2025-06]"))
    report = validate(variant, facts, notes)
    assert set(codes(report)) == {"quellenformat"} and report["content_errors"] == 0
    assert report["metrics"]["numbers"]["notiz"] == 2             # „rund 5 %“ weiterhin der Notiz zugeordnet
    assert not report["metrics"]["format_ok"]


def test_facts_reference_is_not_a_source(example, facts, notes):
    anchor = "Die Gesamtleistung liegt"
    report = validate(example.replace(anchor, "Die Umsatzerlöse steigen wegen höherer Mengen [Quelle: FACTS]. " + anchor),
                      facts, notes)
    assert codes(report) == ["begruendung_ohne_kennzeichnung"]
    assert codes(report, "hinweis") == ["quelle_facts"]
    flag_ref = validate(example.replace("(Hypothese). Dann wäre der Juni", "(Hypothese) [Flag V1]. Dann wäre der Juni"),
                        facts, notes)
    assert flag_ref["ok"] and codes(flag_ref, "hinweis") == ["quelle_facts"]


@pytest.mark.parametrize("text, unit, scale", [("1,91 Mio.", N.EUR, 1_000_000), ("4,2 pp.", N.PP, 1), ("4,2 PP", N.PP, 1)])
def test_more_units(text, unit, scale):
    [num] = N.extract(text)
    assert (num.unit, num.scale) == (unit, scale)


def test_genitive_alias(example, facts, notes):
    anchor = "Die Gesamtleistung liegt"
    sentence = "Der Rückgang des Ergebnisses vor Steuern im Vorjahresmonat lag bei 107.104 €. "
    assert validate(example.replace(anchor, sentence + anchor), facts, notes)["ok"]
