"""Komut satırı (docs/11_ideal_yorumlar.md, Bölüm 7).

    python -m ideal build  --run data/synthetic/train_seed7 [--retrieval FILE]   # istek dosyaları (repoda)
    python -m ideal build  --run data/synthetic/train_seed7 --variant ohne_kontext   # bağlamsız: {train,val}_ohne
    python -m ideal report --set pilot                                          # öğretmen çıktılarının özeti

Öğretmenin kendisi kullanıcının bilgisayarında çalışır: python ideal/run_teacher.py (anahtar yalnızca orada).
"""

import argparse
import gzip
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


def current_inputs(requests: Path, name: str) -> dict[str, tuple]:
    """İstek dosyasındaki her ay için (sürümler, input_sha): kaydın hâlâ geçerli olup olmadığını belirler."""
    from .teacher import input_sha
    with gzip.open(requests / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return {r["id"]: (r["versions"], input_sha(r)) for r in map(json.loads, f)}


def report(name: str, outputs: Path, requests: Path | None = None) -> str:
    """`requests` verilirse yalnızca güncel girdiyle üretilmiş kayıtlar sayılır; eksik ve eskimiş aylar ayrıca yazılır."""
    recs = list(latest(outputs / f"{name}.jsonl").values())
    stale = missing = 0
    if requests is not None:
        current = current_inputs(requests, name)
        valid = [r for r in recs if (r.get("versions"), r.get("input_sha")) == current.get(r["id"])]
        stale, missing = len(recs) - len(valid), len(set(current) - {r["id"] for r in recs})
        recs = valid
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
    if stale or missing:
        lines.append(f"- Henüz güncel girdiyle üretilmemiş: {stale + missing} ay (eski girdi {stale}, kaydı yok {missing})")
    if problems:
        lines += ["", "**Reddedilen metinlerde son sorunlar:**", ""]
        lines += [f"- {p} × {n}" for p, n in problems.most_common(10)]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m ideal", description="İdeal yorumlar (docs/11).")
    parser.add_argument("command", choices=["build", "report"])
    parser.add_argument("--run", type=Path, default=ROOT / "data" / "synthetic" / "train_seed7")
    parser.add_argument("--retrieval", type=Path, help="python -m rag export çıktısı (varsayılan: <run>/rag/)")
    parser.add_argument("--variant", choices=["rag_k8", "ohne_kontext"], default="rag_k8",
                        help="öğrencinin göreceği bağlam (docs/11, Bölüm 15)")
    parser.add_argument("--set", default="pilot")
    parser.add_argument("--outputs", type=Path, default=ROOT / "ideal" / "outputs")
    args = parser.parse_args(argv)

    if args.command == "report":
        print(report(args.set, args.outputs, ROOT / "ideal" / "requests"))
        return 0

    from .build import build_requests, write_requests

    retrieval = None if args.variant == "ohne_kontext" else args.retrieval or args.run / "rag" / "retrieval.jsonl"
    requests = build_requests(args.run, retrieval)
    for name, path in write_requests(requests).items():
        print(f"{name}: {len(requests[name])} istek → {path.relative_to(ROOT)} ({path.stat().st_size / 1e6:.1f} MB)")
    return 0
