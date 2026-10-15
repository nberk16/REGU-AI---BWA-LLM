"""Komut satırı.

Tek ay (ekrana):      python -m facts --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06
Bütün aylar (JSONL):  python -m facts --run data/synthetic/reference_seed42
                      → <run>/facts/facts.jsonl (repoda tutulmaz; .gitignore)
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

from .build import build_facts, commentable_periods
from .schema import load_config
from .series import load_run


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m facts", description="BWA → facts.json (Katman 1, docs/05).")
    parser.add_argument("--run", type=Path, required=True, help="üreteç koşusu klasörü (model_input/ içerir)")
    parser.add_argument("--firm", help="tek firma (ör. A1-v00)")
    parser.add_argument("--period", help="tek ay (ör. 2025-06); --firm ile birlikte")
    parser.add_argument("--out", type=Path, help="çıktı dosyası (varsayılan: <run>/facts/facts.jsonl)")
    args = parser.parse_args(argv)

    cfg = load_config()
    firms = load_run(args.run)

    if args.firm and args.period:
        facts = build_facts(firms[args.firm], args.period, cfg)
        text = json.dumps(facts, ensure_ascii=False, indent=2) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return

    out = args.out or args.run / "facts" / "facts.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    counts, rules = [], Counter()
    with open(out, "w", encoding="utf-8") as f:
        for firm_id in sorted(firms):
            if args.firm and firm_id != args.firm:
                continue
            fs = firms[firm_id]
            for period in commentable_periods(fs):
                facts = build_facts(fs, period, cfg)
                f.write(json.dumps(facts, ensure_ascii=False) + "\n")
                counts.append(len(facts["positions"]) + len(facts["further_significant"]))
                rules.update(f"{x['code']}:{x['rule']}" for x in facts["flags"])
    n = len(counts)
    print(f"{n} firma-ay → {out}")
    print(f"Anlamlı kalem: medyan {statistics.median(counts):.0f} · 0 kalemli ay %{sum(c == 0 for c in counts) / n * 100:.1f}"
          f" · 5'ten fazla kalemli ay %{sum(c > 5 for c in counts) / n * 100:.1f}")
    print("Bayraklar:", ", ".join(f"{k} {v}" for k, v in sorted(rules.items())))
