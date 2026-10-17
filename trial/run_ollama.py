"""Deneme turu: aday modelleri Ollama ile çalıştırır (kullanıcının bilgisayarında; docs/08).

Yalnızca Python standart kütüphanesini kullanır; proje paketlerini kurmak gerekmez.

Kullanım (repo klasöründe):
    python trial/run_ollama.py                     # üç model, bütün örnekler
    python trial/run_ollama.py --limit 1           # hızlı deneme: her modelden 1 örnek
    python trial/run_ollama.py --models gemma4-e4b # tek model

- Sonuçlar trial/outputs/<model>.jsonl dosyasına, her örnekten sonra eklenir.
- Yarıda kalırsa aynı komutla devam eder; biten örnekler atlanır.
"""

from __future__ import annotations  # Python 3.8 uyumluluğu (kullanıcının bilgisayarı)

import argparse
import json
import platform
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Adaylar [KARAR, tur 6]. Hepsi aynı nicemleme (q4_K_M). "think": False → düşünme modu kapatılır
# (yalnızca bu yeteneği olan modellere gönderilir).
MODELS = [
    {"name": "ministral-3-8b", "tag": "ministral-3:8b-instruct-2512-q4_K_M", "think": None},
    {"name": "gemma4-e4b", "tag": "gemma4:e4b-it-q4_K_M", "think": False},
    {"name": "qwen3.5-9b", "tag": "qwen3.5:9b-q4_K_M", "think": False},
]

OPTIONS = {"temperature": 0.2, "seed": 42, "num_ctx": 8192, "num_predict": 1500}


def api(host: str, path: str, body: dict | None = None, timeout: float = 30) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(host + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def seconds(ns: int | None) -> float | None:
    return round(ns / 1e9, 2) if ns else None


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Deneme turu: aday modelleri Ollama ile çalıştırır.")
    parser.add_argument("--models", nargs="*", help="model adları (varsayılan: hepsi): "
                        + ", ".join(m["name"] for m in MODELS))
    parser.add_argument("--limit", type=int, help="model başına en fazla bu kadar örnek")
    parser.add_argument("--cases", type=Path, default=HERE / "inputs" / "cases.jsonl")
    parser.add_argument("--out", type=Path, default=HERE / "outputs")
    parser.add_argument("--host", default="http://localhost:11434")
    args = parser.parse_args(argv)

    try:
        version = api(args.host, "/api/version")["version"]
        installed = {m["name"] for m in api(args.host, "/api/tags")["models"]}
    except (urllib.error.URLError, OSError) as e:
        print(f"Ollama'ya ulaşılamadı ({args.host}): {e}\nOllama açık mı? (Windows: görev çubuğundaki simge)")
        return 2

    models = [m for m in MODELS if not args.models or m["name"] in args.models or m["tag"] in args.models]
    missing = [m for m in models if m["tag"] not in installed]
    if missing:
        print("Şu modeller kurulu değil; önce indirin:")
        for m in missing:
            print(f"  ollama pull {m['tag']}")
        return 2

    cases = load_jsonl(args.cases)[: args.limit] if args.limit else load_jsonl(args.cases)
    args.out.mkdir(parents=True, exist_ok=True)
    machine = {"platform": platform.platform(), "processor": platform.processor(), "ollama": version}
    print(f"Ollama {version} · {len(models)} model × {len(cases)} örnek · {machine['platform']}")

    for m in models:
        out_path = args.out / f"{m['name']}.jsonl"
        done = {r["case_id"] for r in load_jsonl(out_path) if not r.get("error")}
        todo = [c for c in cases if c["id"] not in done]
        print(f"\n[{m['name']}] {m['tag']}: {len(todo)} örnek ({len(done)} tamamlanmış)")
        durations: list[float] = []
        for i, case in enumerate(todo, 1):
            body = {"model": m["tag"], "messages": case["messages"], "stream": False, "options": OPTIONS}
            if m["think"] is not None:
                body["think"] = m["think"]
            started = time.time()
            record = {"case_id": case["id"], "model": m["name"], "tag": m["tag"],
                      "prompt_version": case["prompt_version"], "options": OPTIONS, "machine": machine,
                      "started": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            try:
                resp = api(args.host, "/api/chat", body, timeout=3 * 3600)
            except (urllib.error.URLError, OSError) as e:
                record["error"] = str(e)
                print(f"  {i}/{len(todo)} {case['id']}: HATA {e}")
            else:
                wall = time.time() - started
                content = resp["message"].get("content", "")
                thinking = resp["message"].get("thinking", "") or ""
                think_inline = re.findall(r"<think>.*?</think>", content, flags=re.S)
                content = re.sub(r"<think>.*?</think>", "", content, flags=re.S).strip()
                stats = {
                    "wall_s": round(wall, 1),
                    "load_s": seconds(resp.get("load_duration")),
                    "prompt_tokens": resp.get("prompt_eval_count"),
                    "prompt_s": seconds(resp.get("prompt_eval_duration")),
                    "output_tokens": resp.get("eval_count"),
                    "output_s": seconds(resp.get("eval_duration")),
                    "done_reason": resp.get("done_reason"),
                    "thinking_chars": len(thinking) + sum(len(t) for t in think_inline),
                }
                if stats["output_tokens"] and stats["output_s"]:
                    stats["output_tok_per_s"] = round(stats["output_tokens"] / stats["output_s"], 2)
                if stats["prompt_tokens"] and stats["prompt_s"]:
                    stats["prompt_tok_per_s"] = round(stats["prompt_tokens"] / stats["prompt_s"], 1)
                record.update(output=content, stats=stats)
                if i == 1:
                    try:
                        ps = next((p for p in api(args.host, "/api/ps")["models"] if p["name"] == m["tag"]), None)
                        if ps:
                            record["memory"] = {"size": ps.get("size"), "size_vram": ps.get("size_vram")}
                    except (urllib.error.URLError, OSError):
                        pass
                durations.append(wall)
                eta = (len(todo) - i) * sum(durations) / len(durations) / 60
                warn = ""
                if (stats["prompt_tokens"] or 0) >= OPTIONS["num_ctx"] - 64:
                    warn += " · UYARI: istem bağlam sınırına dayandı (kesilmiş olabilir)"
                if stats["done_reason"] == "length":
                    warn += " · UYARI: çıktı uzunluk sınırında kesildi"
                if stats["thinking_chars"]:
                    warn += " · not: model düşünme metni üretti"
                print(f"  {i}/{len(todo)} {case['id']}: {stats['output_tokens']} token, {wall:.0f} s "
                      f"({stats.get('output_tok_per_s', '?')} token/s) · kalan ~{eta:.0f} dk{warn}")
            with open(out_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nBitti. Sonuçlar: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
