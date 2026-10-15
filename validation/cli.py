"""Komut satırı.

Üreteç koşusundan (facts ve notlar otomatik):
    python -m validation --text yorum.md --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06
Hazır dosyalarla:
    python -m validation --text yorum.md --facts facts.json [--notes notlar.jsonl]

Çıkış kodu: 0 = hata yok, 1 = en az bir "fehler" bulgusu.
"""

import argparse
import json
from pathlib import Path

from .check import validate
from .context import load_notes, window_notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m validation", description="Yorum taslağını denetler (Katman 4, docs/07).")
    parser.add_argument("--text", type=Path, required=True, help="yorum metni (Markdown)")
    parser.add_argument("--run", type=Path, help="üreteç koşusu klasörü")
    parser.add_argument("--firm", help="firma (ör. A1-v00); --run ile")
    parser.add_argument("--period", help="ay (ör. 2025-06); --run ile")
    parser.add_argument("--facts", type=Path, help="facts.json dosyası (--run yerine)")
    parser.add_argument("--notes", type=Path, help="modele verilen notlar, JSONL (--facts ile)")
    parser.add_argument("--json", type=Path, help="raporu JSON olarak yaz")
    args = parser.parse_args(argv)

    if args.facts:
        facts = json.loads(args.facts.read_text(encoding="utf-8"))
        notes = [json.loads(l) for l in args.notes.read_text(encoding="utf-8").splitlines() if l.strip()] if args.notes else []
    elif args.run and args.firm and args.period:
        from facts.build import build_facts
        from facts.schema import load_config
        from facts.series import load_run

        facts = build_facts(load_run(args.run)[args.firm], args.period, load_config())
        notes = window_notes(load_notes(args.run), args.firm, args.period)
    else:
        parser.error("--facts veya --run/--firm/--period gerekli")

    report = validate(args.text.read_text(encoding="utf-8"), facts, notes)
    if args.json:
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    m = report["metrics"]
    nums = m["numbers"]
    print(f"Fehler: {report['errors']} · Hinweise: {report['hints']} · Format: {'ok' if m['format_ok'] else 'fehlerhaft'}")
    print(f"Zahlen: {nums['checked']} geprüft, {nums['fakt']} facts, {nums['notiz']} Notiz, "
          f"{nums['checked'] - nums['fakt'] - nums['notiz']} beanstandet · Zahlentreue: {nums['fidelity']}")
    r = m["reasons"]
    print(f"Begründungen: {r['total']} ({r['with_source']} mit Quelle, {r['with_hypothesis']} als Hypothese, "
          f"{r['unmarked']} ohne Kennzeichnung) · Wörter ohne Tabelle: {m['words']}")
    for f in report["findings"]:
        where = f"Z. {f['line']}" if "line" in f else (f.get("section") or "")
        print(f"  [{f['severity']}] {f['code']} ({where}): {f['message']}")
    return 0 if report["ok"] else 1
