"""İdeal yorumlar: öğretmen modeli (Mistral API) çalıştırır — kullanıcının bilgisayarında (docs/11, Bölüm 6).

API anahtarı yalnızca kullanıcının bilgisayarında, MISTRAL_API_KEY ortam değişkeninde durur [KARAR, tur 11].
Betik anahtarı hiçbir dosyaya yazmaz ve ekrana basmaz.

Kullanım (repo klasöründe, PowerShell):
    $env:MISTRAL_API_KEY = "<anahtar>"            # yalnızca bu pencere için geçerli
    python ideal/run_teacher.py --check            # anahtar ve model erişimi
    python ideal/run_teacher.py --set pilot        # ~24 ay
    python ideal/run_teacher.py --set train        # 960 ay (kaldığı yerden devam eder)
    python ideal/run_teacher.py --set train --retry-failed   # kabul edilmeyenleri yeniden dene

- Her metin hemen kontrol edilir (doğrulama katmanı + plan). Geçemezse sorunlar modele bildirilir ve metin yeniden
  istenir (en fazla --max-attempts deneme).
- Sonuçlar ideal/outputs/<küme>.jsonl dosyasına, her aydan sonra eklenir. Yarıda kalırsa aynı komutla devam eder.
- Yalnızca standart kütüphane ve bu repodaki paketler (validation, ideal); ek kurulum gerekmez. Python ≥ 3.11.
"""

import argparse
import gzip
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if sys.version_info < (3, 11):
    sys.exit("Python 3.11 veya daha yenisi gerekli (python --version).")

from ideal.check import check  # noqa: E402
from ideal.teacher import feedback_message  # noqa: E402

API = "https://api.mistral.ai/v1"
# [ÖNERİ] Mistral Large 3 (v25.12). Erişilemezse --check mevcut "large" modellerini listeler.
MODEL = "mistral-large-2512"
OPTIONS = {"temperature": 0.4, "max_tokens": 2000}


class Fatal(Exception):
    """Devam etmenin anlamsız olduğu hata (geçersiz anahtar, bilinmeyen model)."""


def api(path: str, key: str, body: dict | None = None, timeout: float = 240) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def chat(key: str, model: str, messages: list[dict], seed: int, temperature: float,
         max_tokens: int = OPTIONS["max_tokens"]) -> tuple[str, dict]:
    """Bir istek; 429/5xx/ağ hatasında bekleyip yeniden dener."""
    body = {"model": model, "messages": messages, "random_seed": seed, "temperature": temperature,
            "max_tokens": max_tokens}
    for attempt in range(8):
        try:
            res = api("/chat/completions", key, body)
            return res["choices"][0]["message"]["content"], res.get("usage", {})
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401:
                raise Fatal("Anahtar geçersiz (401). MISTRAL_API_KEY'i kontrol et.") from None
            if e.code in (400, 403, 404, 422):
                raise Fatal(f"İstek reddedildi ({e.code}): {detail}") from None
            wait = float(e.headers.get("Retry-After") or min(60, 2 ** (attempt + 1)))
        except (urllib.error.URLError, TimeoutError, OSError):
            wait = min(60, 2 ** (attempt + 1))
        time.sleep(wait)
    raise RuntimeError("API birkaç denemede yanıt vermedi")


def clean(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def run_one(req: dict, key: str, model: str, max_attempts: int, temperature: float) -> dict:
    messages = list(req["messages"])
    started, usage = time.time(), {"prompt_tokens": 0, "completion_tokens": 0}
    text, result = "", {"ok": False, "problems": []}
    for attempt in range(1, max_attempts + 1):
        raw, u = chat(key, model, messages, req["random_seed"] + attempt - 1, temperature)
        for k in usage:
            usage[k] += u.get(k, 0)
        text = clean(raw)
        result = check(text, req["plan"], req["facts"], req["notes"])
        if result["ok"]:
            break
        messages += [{"role": "assistant", "content": raw}, feedback_message(result["problems"])]
    return {"id": req["id"], "set": req["set"], "status": "ok" if result["ok"] else "failed", "attempts": attempt,
            "text": text, "problems": result["problems"], "model": model, "versions": req["versions"],
            "options": {"temperature": temperature, "random_seed": req["random_seed"]}, "usage": usage,
            "seconds": round(time.time() - started, 1), "finished": datetime.now(timezone.utc).isoformat()}


def load_requests(name: str, folder: Path) -> list[dict]:
    with gzip.open(folder / f"{name}.jsonl.gz", "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Öğretmen modeli çalıştırır (docs/11).")
    parser.add_argument("--set", choices=["pilot", "train", "val"], help="hangi istek kümesi")
    parser.add_argument("--check", action="store_true", help="yalnızca anahtar ve model erişimini dene")
    parser.add_argument("--limit", type=int, help="en fazla bu kadar yeni ay")
    parser.add_argument("--workers", type=int, default=2, help="aynı anda kaç istek (hız sınırına takılırsa 1)")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--retry-failed", action="store_true", help="kabul edilmeyen ayları yeniden dene")
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--temperature", type=float, default=OPTIONS["temperature"])
    parser.add_argument("--requests", type=Path, default=ROOT / "ideal" / "requests")
    parser.add_argument("--out", type=Path, default=ROOT / "ideal" / "outputs")
    args = parser.parse_args(argv)

    key = os.environ.get("MISTRAL_API_KEY", "").strip()
    if not key:
        print("MISTRAL_API_KEY tanımlı değil. PowerShell'de önce şunu yaz (tırnak içine kendi anahtarın):\n"
              '    $env:MISTRAL_API_KEY = "..."')
        return 2
    try:
        models = sorted(m["id"] for m in api("/models", key, timeout=60).get("data", []))
    except urllib.error.HTTPError as e:
        print("Anahtar geçersiz (401)." if e.code == 401 else f"Mistral API hatası: {e.code}")
        return 2
    except (urllib.error.URLError, OSError) as e:
        print(f"Mistral API'ye ulaşılamadı: {e}")
        return 2
    if args.model not in models:
        # Liste eksik olabilir: modeli kısa bir istekle doğrudan dene ve gerçek hatayı göster.
        print(f"Model listesinde {args.model} yok. Listedeki modeller ({len(models)}): {', '.join(models) or 'yok'}")
        print("Kısa bir deneme isteği gönderiliyor …")
        try:
            chat(key, args.model, [{"role": "user", "content": "Antworte nur mit: OK"}], 1, 0.0, max_tokens=5)
        except Fatal as e:
            print(f"Deneme başarısız: {e}\nBu satırları gönder (anahtarı gönderme).")
            return 2
        print("Deneme isteği çalıştı; model kullanılabilir.")
    if args.check or not args.set:
        print(f"Anahtar geçerli; {args.model} kullanılabilir. Şimdi: python ideal/run_teacher.py --set pilot")
        return 0

    requests = load_requests(args.set, args.requests)
    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"{args.set}.jsonl"
    last: dict[str, str] = {}                      # id → son kaydın durumu (yeniden denemede son kayıt geçerli)
    if out_path.exists():
        with open(out_path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rec = json.loads(line)
                    last[rec["id"]] = rec["status"]
    done = {i for i, s in last.items() if s == "ok" or not args.retry_failed}
    todo = [r for r in requests if r["id"] not in done][:args.limit]
    print(f"{args.set}: {len(requests)} ay, {len(done)} tamamlanmış, {len(todo)} çalışacak · model {args.model} · "
          f"{args.workers} paralel", flush=True)

    lock, counter, stop = threading.Lock(), [0, 0], threading.Event()

    def work(req: dict) -> None:
        if stop.is_set():
            return
        try:
            rec = run_one(req, key, args.model, args.max_attempts, args.temperature)
        except Fatal as e:
            stop.set()
            print(f"DURDU: {e}", flush=True)
            return
        except Exception as e:  # noqa: BLE001 — bir ay başarısız olsa da diğerleri devam eder
            print(f"  {req['id']}: hata ({e}); sonra aynı komutla yeniden denenir", flush=True)
            return
        with lock:
            with open(out_path, "a", encoding="utf-8") as f:   # önce dosyaya, sonra ekrana
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            counter[0] += 1
            counter[1] += rec["status"] == "ok"
            mark = "✓" if rec["status"] == "ok" else "✗"
            print(f"[{counter[0]}/{len(todo)}] {rec['id']} {mark} ({rec['attempts']} deneme, {rec['seconds']} s)",
                  flush=True)

    with ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        list(pool.map(work, todo))
    print(f"Bitti: {counter[1]}/{counter[0]} kabul edildi → {out_path}")
    return 1 if stop.is_set() else 0


if __name__ == "__main__":
    sys.exit(main())
