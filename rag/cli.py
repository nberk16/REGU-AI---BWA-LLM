"""Komut satırı (docs/09, Bölüm 6).

    python -m rag build    --run DIR [--embedder bge-m3|hashing]
    python -m rag retrieve --run DIR --firm A1-v00 --period 2025-06 [--mode …] [--k 8]
    python -m rag export   --run DIR [--mode …] [--k 8] [--firms A2-v120 …] [--out FILE]

Depo: <run>/rag/chroma-<embedder>/ (repoda tutulmaz). export: <run>/rag/retrieval.jsonl.
"""

import argparse
import json
from pathlib import Path

from .documents import load_knowledge, load_notes, notes_to_docs
from .embedding import get_embedder
from .retrieve import MODES, as_records, retrieve
from .store import KnowledgeBase, load_config


def open_kb(run: Path, embedder_name: str, cfg: dict) -> KnowledgeBase:
    embedder = get_embedder(embedder_name, cfg)
    slug = "hashing" if embedder_name == "hashing" else "bge-m3"
    return KnowledgeBase(embedder, cfg, Path(run) / "rag" / f"chroma-{slug}")


def build(run: Path, embedder_name: str, cfg: dict) -> KnowledgeBase:
    kb = open_kb(run, embedder_name, cfg)
    added = kb.add(load_knowledge() + notes_to_docs(load_notes(run)))
    print(f"{added} yeni parça eklendi; depoda: {kb.count()}")
    return kb


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m rag", description="Katman 2: bilgi tabanı ve getirme (docs/09).")
    parser.add_argument("command", choices=["build", "retrieve", "export"])
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--embedder", default="bge-m3", choices=["bge-m3", "hashing"])
    parser.add_argument("--firm")
    parser.add_argument("--period")
    parser.add_argument("--mode", choices=MODES)
    parser.add_argument("--k", type=int, help="not sayısı; 0 = penceredeki bütün notlar")
    parser.add_argument("--firms", nargs="*", help="export: yalnızca bu firmalar (ör. A2-v120)")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)

    from facts.build import build_facts, commentable_periods
    from facts.schema import load_config as load_facts_config
    from facts.series import load_run

    cfg = load_config()
    kb = build(args.run, args.embedder, cfg)
    if args.command == "build":
        return 0

    firms = load_run(args.run)
    fcfg = load_facts_config()
    if args.command == "retrieve":
        if not (args.firm and args.period):
            parser.error("retrieve için --firm ve --period gerekli")
        result = as_records(retrieve(build_facts(firms[args.firm], args.period, fcfg), kb, args.mode, args.k))
        for r in result["knowledge"] + result["notes"]:
            print(f"[{r['source_id']}] {r['text']}")
        return 0

    out = args.out or args.run / "rag" / "retrieval.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    mode = args.mode or cfg["retrieval"]["mode"]
    k = cfg["retrieval"]["top_k"] if args.k is None else args.k
    n = 0
    with open(out, "w", encoding="utf-8") as f:
        for firm_id, fs in sorted(firms.items()):
            if args.firms and firm_id not in args.firms:
                continue
            for period in commentable_periods(fs):
                rec = as_records(retrieve(build_facts(fs, period, fcfg), kb, mode, k))
                f.write(json.dumps({"firm_id": firm_id, "period": period, "mode": mode, "k": k,
                                    "embedding": kb.embedder.name, **rec}, ensure_ascii=False) + "\n")
                n += 1
    print(f"{n} firma-ay → {out}")
    return 0
