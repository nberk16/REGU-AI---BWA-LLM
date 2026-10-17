"""Katman 2 getirme isabeti: ground truth'a karşı recall@k (geliştirme aracı; docs/09, Bölüm 5).

Kullanım: python tools/retrieval_quality.py data/synthetic/reference_seed42 [--embedder bge-m3] [--k 4 8 12]

İlgili notlar (ground truth'tan; yalnızca 13 aylık penceredeki ve notlanmış olaylar):
- **çekirdek:** o ay başlayan olayların notları;
- **geniş:** çekirdek + sürmekte olan ya da önceki yılın aynı ayındaki olayların notları; bu olaylar ayın anlamlı
  kalemlerini veya bayraklı satırlarını etkiliyorsa. Rohertrag adayı varsa ground truth'taki nedenlerin notları da.
Çeldirici payı: getirilen notların ne kadarı çeldirici (hiçbir olaya ait olmayan) not.
Bu araç ground truth okur; Katman 2'nin parçası değildir.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from facts.build import build_facts, commentable_periods  # noqa: E402
from facts.schema import RATIOS  # noqa: E402
from facts.schema import load_config as load_facts_config  # noqa: E402
from facts.series import load_run  # noqa: E402
from rag.cli import build  # noqa: E402
from rag.documents import load_notes, period_index  # noqa: E402
from rag.retrieve import MODES, NAME_TO_KEY, build_queries, items  # noqa: E402
from rag.store import load_config  # noqa: E402


def load_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def relevant(facts: dict, gt: dict, events: dict, window: set[str]) -> tuple[set[str], set[str]]:
    keys = {p["key"] for p in facts["positions"]}
    keys |= {NAME_TO_KEY.get(f["position"]) for f in facts["flags"]}
    keys |= {RATIOS[k] for k in list(keys) if k in RATIOS}
    core = {events[e]["source_id"] for e in gt["new_events"] if events[e]["documented"]}
    ext = set(core)
    for e in set(gt["active_events"]) | set(gt["vorjahr_events"]):
        ev = events[e]
        if ev["documented"] and set(ev["lines"]) & keys:
            ext.add(ev["source_id"])
    if any(f["rule"] == "rohertrag_sprung" for f in facts["flags"]):
        ext |= {events[c["event_id"]]["source_id"] for c in gt["rohertrag_causes"] if c["documented"]}
    return core & window, ext & window


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Katman 2 getirme isabeti (docs/09).")
    parser.add_argument("run", type=Path)
    parser.add_argument("--embedder", default="bge-m3", choices=["bge-m3", "hashing"])
    parser.add_argument("--k", type=int, nargs="+", default=[4, 8, 12])
    parser.add_argument("--firms", nargs="*", help="yalnızca bu firmalar (ör. A1-v00)")
    args = parser.parse_args(argv)

    cfg = load_config()
    rcfg = cfg["retrieval"]
    kb = build(args.run, args.embedder, cfg)
    fcfg = load_facts_config()
    firms = load_run(args.run)
    gt = {(r["firm_id"], r["period"]): r for r in load_jsonl(args.run / "evaluation" / "ground_truth_months.jsonl")}
    events = {e["event_id"]: e for e in load_jsonl(args.run / "evaluation" / "events.jsonl")}
    distractors = {(n["firm_id"], n["source_id"]) for n in load_jsonl(args.run / "evaluation" / "notes_ground_truth.jsonl")
                   if n["distractor"]}
    note_ids = {(n["firm_id"], n["source_id"]) for n in load_notes(args.run)}
    assert note_ids                                    # notlar modele görünen dosyadan

    variants = [(m, k) for m in MODES for k in args.k] + [("alle", 0)]
    agg = defaultdict(lambda: defaultdict(float))
    window_sizes, months = [], 0
    for firm_id, fs in sorted(firms.items()):
        if args.firms and firm_id not in args.firms:
            continue
        for period in commentable_periods(fs):
            facts = build_facts(fs, period, fcfg)
            end = period_index(period)
            start = end - (rcfg["window_months"] - 1)
            window = {d.doc_id: d for d in kb.window_notes(firm_id, start, end)}
            window_ids = {d.source_id for d in window.values()}
            core, ext = relevant(facts, gt[(firm_id, period)], events, window_ids)
            window_sizes.append(len(window))
            months += 1
            ka = {d.meta["key"]: d.text for d in kb.general([i["key"] for i in items(facts) if i.get("key")])}
            rrf = {}
            for mode in MODES:
                scores: dict[str, float] = defaultdict(float)
                for ranking in kb.rank_notes(firm_id, start, end, build_queries(facts, mode, ka)):
                    for rank, (doc_id, _) in enumerate(ranking, start=1):
                        scores[doc_id] += 1.0 / (rcfg["rrf_k"] + rank)
                rrf[mode] = sorted(window, key=lambda d: (-scores.get(d, 0.0), d))
            for mode, k in variants:
                chosen = list(window) if k == 0 else rrf[mode][:k]
                got = {window[d].source_id for d in chosen}
                a = agg[(mode, k)]
                a["core_hit"] += len(got & core)
                a["core_all"] += len(core)
                a["ext_hit"] += len(got & ext)
                a["ext_all"] += len(ext)
                a["retrieved"] += len(got)
                a["distractor"] += sum(1 for s in got if (firm_id, s) in distractors)
                a["months_full_ext"] += int(bool(ext) and ext <= got)
                a["months_with_ext"] += int(bool(ext))

    print(f"Koşu: {args.run} · embedding: {kb.embedder.name} · {months} firma-ay · "
          f"pencerede ortalama {sum(window_sizes) / months:.1f} not (Firmenprofil hariç)\n")
    print("| Yöntem | k | Recall çekirdek | Recall geniş | Geniş: tam getirilen ay | Çeldirici payı | Ort. not |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for mode, k in variants:
        a = agg[(mode, k)]
        print(f"| {mode} | {k or 'alle'} | {a['core_hit'] / a['core_all']:.1%} | {a['ext_hit'] / a['ext_all']:.1%} | "
              f"{a['months_full_ext'] / a['months_with_ext']:.1%} | {a['distractor'] / a['retrieved']:.1%} | "
              f"{a['retrieved'] / months:.1f} |")


if __name__ == "__main__":
    main()
