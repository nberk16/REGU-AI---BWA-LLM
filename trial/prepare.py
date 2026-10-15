"""Deneme turu girdileri: doğrulama varyantlarından çeşitli ~10 ay seçer ve istemleri yazar (docs/08).

Kullanım: python trial/prepare.py [--run data/synthetic/train_seed7] [--n 10]

- Örnekler yalnızca doğrulama varyantlarından (v120–v122) seçilir; test kümesi model seçiminde kullanılmaz (docs/04, 9).
- Seçim, ground truth'a bakarak çeşitlilik sağlar (V1–V6, V2 adayı cite/warn, sakin ay, çeldirici not).
  Ground truth modele gitmez; yalnızca trial/inputs/selection.md'ye yazılır.
- Çıktı: trial/inputs/cases.jsonl (istem + facts + notlar) ve trial/inputs/selection.md.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from facts.build import build_facts, commentable_periods  # noqa: E402
from facts.schema import load_config  # noqa: E402
from facts.series import load_run  # noqa: E402
from prompting import PROMPT_VERSION, build_messages  # noqa: E402
from validation.context import load_notes, window_notes  # noqa: E402

VALIDATION_VARIANTS = (120, 121, 122)
OUT_DIR = ROOT / "trial" / "inputs"


def ensure_run(run_dir: Path) -> None:
    if (run_dir / "model_input").exists():
        return
    from generator.pipeline import generate_run
    from generator.writer import write_run

    print(f"{run_dir} yok; üretiliyor (A2 + A3, 23 varyant, seed 7, train_price_boost) …")
    write_run(generate_run(["A2", "A3"], 23, 7, profile="train_price_boost", first_variant=100), run_dir)


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def candidates(run_dir: Path) -> list[dict]:
    cfg = load_config()
    firms = load_run(run_dir)
    notes = load_notes(run_dir)
    gt = {(r["firm_id"], r["period"]): r for r in load_jsonl(run_dir / "evaluation" / "ground_truth_months.jsonl")}
    note_numbers = {(n["firm_id"], n["source_id"]): n["numbers"]
                    for n in load_jsonl(run_dir / "evaluation" / "notes_ground_truth.jsonl")}
    out = []
    for firm_id, fs in sorted(firms.items()):
        if int(firm_id.split("-v")[1]) not in VALIDATION_VARIANTS:
            continue
        for period in commentable_periods(fs):
            facts = build_facts(fs, period, cfg)
            g = gt[(firm_id, period)]
            out.append({
                "firm_id": firm_id, "period": period, "facts": facts,
                "notes": window_notes(notes, firm_id, period), "gt": g,
                "flags": {(f["code"], f["status"]) for f in facts["flags"]},
                "expected": {f["code"] for f in g["expected_flags"]},
                "numbered_note": any(note_numbers.get((firm_id, sid)) for sid in g["notes"]),
            })
    return out


def has(c, code, status="hinweis") -> bool:
    return code in c["expected"] and (code, status) in c["flags"]


def kandidat(c) -> bool:
    return any(code == "V2" and status == "kandidat" for code, status in c["flags"])


# (etiket, koşul, hedef ay) — sırayla, her biri bir ay seçer.
CRITERIA = [
    ("V2 adayı, notla açıklanmalı (cite), A3", lambda c: c["firm_id"].startswith("A3") and kandidat(c)
     and c["gt"]["v2_candidate_decision"] == "cite", "2025-04"),
    ("V2 adayı, notla açıklanabilir (cite/either), A2", lambda c: c["firm_id"].startswith("A2") and kandidat(c)
     and c["gt"]["v2_candidate_decision"] in ("cite", "either"), "2025-09"),
    ("V2 adayı, uyarılmalı (warn), A2", lambda c: c["firm_id"].startswith("A2") and kandidat(c)
     and c["gt"]["v2_candidate_decision"] == "warn", "2026-03"),
    ("V1 eksik tahakkuk", lambda c: has(c, "V1"), "2025-06"),
    ("V3 amortisman yalnızca yıl sonunda", lambda c: has(c, "V3"), "2026-05"),
    ("V4 geç kayıt", lambda c: has(c, "V4"), "2025-10"),
    ("V5 tek seferlik etki, rakamlı not", lambda c: has(c, "V5") and c["numbered_note"], "2026-01"),
    ("V6 mevsimsellik", lambda c: has(c, "V6"), "2026-07"),
    ("Sakin ay", lambda c: c["gt"]["quiet_month"], "2025-02"),
    ("Çeldirici not", lambda c: bool(c["gt"]["distractor_notes"]), "2026-10"),
]


def _month_index(period: str) -> int:
    y, m = map(int, period.split("-"))
    return y * 12 + m


def select(cands: list[dict], n: int) -> list[tuple[str, dict]]:
    chosen: list[tuple[str, dict]] = []
    per_firm: dict[str, int] = {}
    for label, cond, target in CRITERIA[:n]:
        taken = {(c["firm_id"], c["period"]) for _, c in chosen}
        pool = [c for c in cands if cond(c) and (c["firm_id"], c["period"]) not in taken]
        if not pool:
            print(f"uyarı: '{label}' için aday yok, atlandı")
            continue
        best = min(pool, key=lambda c: (per_firm.get(c["firm_id"], 0),
                                        abs(_month_index(c["period"]) - _month_index(target)), c["firm_id"]))
        chosen.append((label, best))
        per_firm[best["firm_id"]] = per_firm.get(best["firm_id"], 0) + 1
    return chosen


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Deneme turu girdilerini hazırlar (docs/08).")
    parser.add_argument("--run", type=Path, default=ROOT / "data" / "synthetic" / "train_seed7")
    parser.add_argument("--n", type=int, default=len(CRITERIA))
    args = parser.parse_args(argv)

    ensure_run(args.run)
    chosen = select(candidates(args.run), args.n)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(OUT_DIR / "cases.jsonl", "w", encoding="utf-8") as f:
        for _, c in chosen:
            case = {"id": f"{c['firm_id']}_{c['period']}", "firm_id": c["firm_id"], "period": c["period"],
                    "prompt_version": PROMPT_VERSION, "messages": build_messages(c["facts"], c["notes"]),
                    "facts": c["facts"], "notes": c["notes"]}
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    rows = ["# Deneme turu: seçilen aylar", "",
            "Kaynak: doğrulama varyantları (A2/A3 v120–v122; `train_seed7`). Bu tablo ground truth içerir; "
            "modele gönderilmez.", "",
            "| # | Örnek | Seçim ölçütü | Bayraklar (facts) | Beklenen bayraklar (GT) | V2 kararı (GT) | Ayın notları | Çeldirici | Kalem sayısı |",
            "|---|---|---|---|---|---|---|---|---|"]
    for i, (label, c) in enumerate(chosen, 1):
        g = c["gt"]
        flags = ", ".join(sorted(f"{code} ({status})" for code, status in c["flags"])) or "–"
        rows.append(f"| {i} | {c['firm_id']} {c['period']} | {label} | {flags} | "
                    f"{', '.join(sorted(c['expected'])) or '–'} | {g['v2_candidate_decision'] or '–'} | "
                    f"{', '.join(g['notes']) or '–'} | {', '.join(g['distractor_notes']) or '–'} | "
                    f"{len(c['facts']['positions'])} |")
    (OUT_DIR / "selection.md").write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"{len(chosen)} örnek → {OUT_DIR / 'cases.jsonl'}")
    for i, (label, c) in enumerate(chosen, 1):
        print(f"  {i:2d}. {c['firm_id']} {c['period']}: {label}")


if __name__ == "__main__":
    main()
