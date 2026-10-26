"""Katman 1 bayraklarının ground truth'a karşı kabaca isabeti (geliştirme aracı; docs/05, Bölüm 7).

Kullanım: python tools/flag_quality.py data/synthetic/reference_seed42

- Bayrak, firma-ay ve kod düzeyinde karşılaştırılır (V1–V6).
- Rohertrag adayı (rule = rohertrag_sprung) bir uyarı değil, nötr bir adaydır; ayrıca raporlanır.
- V2 yalnızca üreticilerde ölçülür (kural: bestand_fehlt). Ticarette V2'nin karşılığı Rohertrag adayıdır.
- "Eşik üstü recall": yalnızca o aydaki etkisi |Δ| ≥ Gesamtleistung'un %0,5'i olan beklenen bayraklar.
  V6'nın etkisi ayrıca kaydedilmediği için V6'da iki değer aynıdır.
Bu araç ground truth okur; Katman 1'in parçası değildir.
"""

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from facts.build import build_facts, commentable_periods  # noqa: E402
from facts.schema import load_config  # noqa: E402
from facts.series import load_run  # noqa: E402

CODES = ("V1", "V2", "V3", "V4", "V5", "V6")


def main(run_dir: Path) -> None:
    cfg = load_config()
    firms = load_run(run_dir)
    months = {}
    for line in open(run_dir / "evaluation" / "ground_truth_months.jsonl", encoding="utf-8"):
        m = json.loads(line)
        months[(m["firm_id"], m["period"])] = m
    effects = defaultdict(float)
    with open(run_dir / "evaluation" / "effects.csv", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            effects[(row["event_id"], row["line"], row["period"])] += float(row["delta"])

    kinds = {v["firm_id"]: v["kind"] for v in json.loads((run_dir / "evaluation" / "variants.json").read_text(encoding="utf-8"))}
    stats = {c: defaultdict(int) for c in CODES}
    candidate = defaultdict(lambda: defaultdict(int))
    for firm_id, fs in firms.items():
        for period in commentable_periods(fs):
            facts = build_facts(fs, period, cfg)
            thr = facts["thresholds"]["position_abs_eur"]
            gt = months[(firm_id, period)]
            flagged = {x["code"] for x in facts["flags"] if x["rule"] != "rohertrag_sprung"}
            expected = {x["code"] for x in gt["expected_flags"]}
            acceptable = {x["code"] for x in gt["acceptable_flags"]}
            material = {x["code"] for x in gt["expected_flags"]
                        if x["code"] == "V6" or abs(effects[(x["event_id"], x["line"], period)]) >= thr}
            for c in CODES:
                if c == "V2" and kinds[firm_id] != "producer":
                    continue
                s = stats[c]
                if c in flagged:
                    s["flagged"] += 1
                    s["tp"] += c in expected
                    s["fp"] += c not in expected and c not in acceptable
                if c in expected:
                    s["expected"] += 1
                    s["found"] += c in flagged
                if c in material:
                    s["expected_material"] += 1
                    s["found_material"] += c in flagged
            if any(x["rule"] == "rohertrag_sprung" for x in facts["flags"]):
                candidate[firm_id[:2]][str(gt["v2_candidate_decision"])] += 1

    def share(a, b):
        return f"{a / b:.0%}" if b else "–"

    print("| Kod | Bayraklı ay | Precision | Recall (ham) | Recall (eşik üstü) | Beklenen (ham / eşik üstü) |")
    print("|---|---:|---:|---:|---:|---:|")
    for c in CODES:
        s = stats[c]
        print(f"| {c} | {s['flagged']} | {share(s['flagged'] - s['fp'], s['flagged'])} | "
              f"{share(s['found'], s['expected'])} | {share(s['found_material'], s['expected_material'])} | "
              f"{s['expected']} / {s['expected_material']} |")
    print()
    print("V2 satırı yalnızca üreticiler (A1, A3) içindir.")
    print()
    print("Rohertrag adayı aylarda ground truth kararı:")
    for code, counts in sorted(candidate.items()):
        print(f"- {code}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
