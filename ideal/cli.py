"""Komut satırı (docs/11_ideal_yorumlar.md, Bölüm 7).

    python -m ideal build  --run data/synthetic/train_seed7 [--retrieval FILE]   # istek dosyaları (repoda)
    python -m ideal report --set pilot                                          # öğretmen çıktılarının özeti

Öğretmenin kendisi kullanıcının bilgisayarında çalışır: python ideal/run_teacher.py (anahtar yalnızca orada).
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def latest(path: Path) -> dict[str, dict]:
    """Her ay için son kayıt (yeniden denemede son kayıt geçerli)."""
    out: dict[str, dict] = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = json.loads(line)
                out[rec["id"]] = rec
    return out


def report(name: str, outputs: Path) -> str:
    recs = list(latest(outputs / f"{name}.jsonl").values())
    ok = [r for r in recs if r["status"] == "ok"]
    attempts = Counter(r["attempts"] for r in ok)
    problems = Counter(p.split(":")[0][:70] for r in recs for p in r["problems"])
    tokens_in = sum(r["usage"].get("prompt_tokens", 0) for r in recs)
    tokens_out = sum(r["usage"].get("completion_tokens", 0) for r in recs)
    lines = [f"# Öğretmen çıktıları: {name}", "",
             f"- Ay: {len(recs)} · kabul: {len(ok)} ({len(ok) / len(recs):.0%}) · reddedilen: {len(recs) - len(ok)}",
             "- Kabul edilenlerde deneme sayısı: " + ", ".join(f"{k}: {v}" for k, v in sorted(attempts.items())),
             f"- Token: girdi {tokens_in:,} · çıktı {tokens_out:,}".replace(",", "."),
             f"- Süre / ay (medyan): {statistics.median(r['seconds'] for r in recs):.0f} s"]
    if problems:
        lines += ["", "**Reddedilen metinlerde son sorunlar:**", ""]
        lines += [f"- {p} × {n}" for p, n in problems.most_common(10)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ideal", description="İdeal yorumlar (docs/11).")
    parser.add_argument("command", choices=["build", "report"])
    parser.add_argument("--run", type=Path, default=ROOT / "data" / "synthetic" / "train_seed7")
    parser.add_argument("--retrieval", type=Path, help="python -m rag export çıktısı (varsayılan: <run>/rag/)")
    parser.add_argument("--set", default="pilot")
    parser.add_argument("--outputs", type=Path, default=ROOT / "ideal" / "outputs")
    args = parser.parse_args(argv)

    if args.command == "report":
        print(report(args.set, args.outputs))
        return 0

    from .build import build_requests, write_requests

    requests = build_requests(args.run, args.retrieval or args.run / "rag" / "retrieval.jsonl")
    for name, path in write_requests(requests).items():
        print(f"{name}: {len(requests[name])} istek → {path.relative_to(ROOT)} ({path.stat().st_size / 1e6:.1f} MB)")
    return 0
