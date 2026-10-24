"""gpu/01_baseline.ipynb: ince ayar öncesi model, Ollama ile (docs/12, Bölüm 4).

Kullanım: python gpu/tools/nb_01_baseline.py [hedef.ipynb]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbbuild import code, md, write  # noqa: E402

cells = [
    md("""
# 01 — Baseline: ince ayar öncesi Gemma 4 E4B

Test kümesi (720 firma-ay, `reference_seed42`) için üç varyantın yorumlarını üretir (CLAUDE.md, Bölüm 7):

| Varyant | Girdi | Karşılaştırmadaki yeri |
|---|---|---|
| `ohne_kontext` | FACTS; WISSEN ve KONTEXTNOTIZEN „Keine.“ | Çıplak model |
| `rag_k8` | FACTS + WISSEN + Firmenprofil + top-8 not | Yalnızca RAG |
| `rag_alle` | FACTS + WISSEN + Firmenprofil + penceredeki bütün notlar | Retrieval'ın katkısı (`docs/09`, 5.3) |

- **Çalıştırıcı:** Ollama (llama.cpp), `gemma4:e4b-it-q4_K_M`. Deneme turundaki model ve nicemlemeyle aynı (`docs/08`); dizüstündeki demo da bununla çalışır.
  - Her GPU'ya bir Ollama sunucusu açılır; her sunucu aynı anda birkaç istem işler.
  - 23.10 deneme koşusunda Transformers + Unsloth yolu tek T4'te 5 token/s verdi (tam koşu ~60 saat). Ayrıntı: `docs/12`, Bölüm 4.
- **İstemler:** Repoda hazırlandı (istem 1.1, `gpu/data/test_*.jsonl.gz`). GPU tarafında facts ve embedding hesaplanmaz.
- **Ayarlar:** Deneme turuyla aynı: `temperature 0.2`, `top_p 0.95`, `top_k 64`, `seed 42`, en fazla 1.500 yeni token, düşünme kipi kapalı.
- **Çıktı:**
  - `/kaggle/working/outputs/baseline_<varyant>.jsonl` ve günlük.
  - Hepsi ayrıca tek dosyada: `ergebnisse_<MODE>.zip`.
- **Devam:** Yarıda kalırsa yeniden çalıştırınca kaldığı yerden devam eder. Önceki sürümün çıktısı Input olarak eklenirse oradan da devam eder (`gpu/README.md`, Bölüm 4).
- **Kullanım:** `gpu/README.md`. Önce `MODE = "smoke"` (varyant başına 8 istem); sorun yoksa `MODE = "full"`.
"""),
    code("""
MODE = "smoke"                              # "smoke": varyant başına 8 istem · "full": bütün test kümesi (720 ay)
VARIANTS = ["ohne_kontext", "rag_k8", "rag_alle"]   # çıplak model, yalnızca RAG (top-8, bütün notlar)
MODEL = "gemma4:e4b-it-q4_K_M"              # Ollama; deneme turundaki model ve nicemleme (docs/08)
OPTIONS = {"temperature": 0.2, "top_p": 0.95, "top_k": 64, "seed": 42,
           "num_predict": 1500,             # en fazla yeni token
           "num_ctx": 12288}                # en uzun istem ~7.500 token + 1.500 yeni token, pay ile
PARALLEL = 4                                # GPU başına aynı anda işlenen istem
SMOKE_N = 8
TIME_BUDGET_H = 11.0                        # Kaggle oturumu en fazla 12 saat; sonrası çıktıları paketlemeye kalır
"""),
    code("""
# Ollama kurulumu. zstd: kurulum paketi için gerekli; pciutils: kurulumun GPU'yu tanıması için
!apt-get -qq update > /dev/null && apt-get -qq install -y zstd pciutils > /dev/null
!curl -fsSL https://ollama.com/install.sh | sh
"""),
    code("""
import glob, gzip, json, os, queue, statistics, subprocess, threading, time, traceback, zipfile
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

START = time.time()

def find(stem):
    \"\"\"Veri dosyası: .jsonl.gz ya da (Kaggle yüklerken sıkıştırmayı açtıysa) .jsonl.\"\"\"
    for pattern in (f"/kaggle/input/**/{stem}.jsonl.gz", f"/kaggle/input/**/{stem}.jsonl"):
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return Path(hits[0])
    seen = sorted(glob.glob("/kaggle/input/**/*", recursive=True))[:30]
    raise FileNotFoundError(f"{stem} bulunamadı. Sağ panel → Input → Add Input → veri setini ekle. "
                            f"/kaggle/input içinde görülen: {seen or 'hiçbir şey'}")

def load(variant):
    path = find(f"test_{variant}")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

OUT = Path("/kaggle/working/outputs")
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"log_{MODE}.txt"
_log_lock = threading.Lock()

def log(*parts):
    \"\"\"Ekrana ve günlük dosyasına (Output'tan indirilebilir; oturum kapansa da kalır).\"\"\"
    line = " ".join(str(p) for p in parts)
    with _log_lock:
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {line}\\n")

def api(host, path, body=None, timeout=60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(host + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def gpus():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]

log(f"Başlangıç · MODE={MODE} · GPU: {gpus() or 'YOK'}")
log("İstemler:", {v: len(load(v)) for v in VARIANTS})
"""),
    code("""
# Her GPU'ya bir Ollama sunucusu (11434, 11435, …). Modeller ortak klasörde; bir kez indirilir.
HOSTS = []
for i, _ in enumerate(gpus() or ["cpu"]):
    port = 11434 + i
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(i), "OLLAMA_HOST": f"127.0.0.1:{port}",
           "OLLAMA_NUM_PARALLEL": str(PARALLEL), "OLLAMA_KEEP_ALIVE": "-1", "OLLAMA_MAX_LOADED_MODELS": "1"}
    subprocess.Popen(["ollama", "serve"], env=env, stdout=open(OUT / f"ollama_gpu{i}.log", "w"),
                     stderr=subprocess.STDOUT)
    HOSTS.append(f"http://127.0.0.1:{port}")

try:
    for host in HOSTS:
        for _ in range(60):
            try:
                VERSION = api(host, "/api/version")["version"]
                break
            except (urllib.error.URLError, OSError):
                time.sleep(1)
        else:
            raise RuntimeError(f"Ollama sunucusu açılmadı: {host} (outputs/ollama_gpu*.log)")
    t0 = time.time()
    api(HOSTS[0], "/api/pull", {"model": MODEL, "stream": False}, timeout=3600)
    info = next(m for m in api(HOSTS[0], "/api/tags")["models"] if m["name"] == MODEL)
    DIGEST = info["digest"]
    log(f"Ollama {VERSION} · {len(HOSTS)} sunucu · {MODEL} indirildi: {time.time() - t0:.0f} s · "
        f"{info['size'] / 1e9:.1f} GB · {info.get('details', {}).get('quantization_level')} · {DIGEST[:12]}")
    for host in HOSTS:                      # modeli her GPU'ya yükle; num_ctx aynı kalmalı, yoksa yeniden yüklenir
        t0 = time.time()
        api(host, "/api/chat", {"model": MODEL, "messages": [{"role": "user", "content": "Hallo"}], "stream": False,
                                "think": False, "options": {**OPTIONS, "num_predict": 1}}, timeout=1800)
        ps = next(m for m in api(host, "/api/ps")["models"] if m["name"] == MODEL)
        on_gpu = ps.get("size_vram", 0) / max(ps.get("size", 1), 1)
        log(f"  {host}: yüklendi {time.time() - t0:.0f} s · bellek {ps.get('size', 0) / 1e9:.1f} GB, "
            f"GPU'da %{100 * on_gpu:.0f}" + ("" if on_gpu > 0.99 else " · UYARI: model tamamen GPU'da değil, yavaş çalışır"))
    log("GPU belleği:", gpus())
except Exception:
    log("OLLAMA HAZIRLANAMADI:\\n" + traceback.format_exc())
    raise
"""),
    code("""
def ns(x):
    return round(x / 1e9, 1) if x else None

def valid(rec):
    \"\"\"Aynı model ve ayarlarla tamamlanmış kayıt (devam ederken yeniden çalıştırılmaz).\"\"\"
    return (rec.get("model") == MODEL and rec.get("model_digest") == DIGEST and rec.get("adapter") is None
            and rec.get("settings") == OPTIONS and bool(rec.get("text")))

def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def resume_from_input(variant, path):
    \"\"\"Önceki sürümün çıktısı Input olarak eklendiyse geçerli kayıtları al.\"\"\"
    if path.exists():
        return
    recs, seen = {}, 0
    for p in sorted(glob.glob(f"/kaggle/input/**/baseline_{variant}.jsonl", recursive=True)):
        rows = read(p)
        seen += len(rows)
        recs.update({r["id"]: r for r in rows if valid(r)})
    if seen:     # geçersiz: başka model sürümü (digest) ya da ayar; bunlar yeniden çalıştırılır
        log(f"{variant}: önceki çıktıda {seen} kayıt, {len(recs)} geçerli")
    if recs:
        with open(path, "w", encoding="utf-8") as f:
            for r in recs.values():
                f.write(json.dumps(r, ensure_ascii=False) + "\\n")

def chat(host, messages):
    body = {"model": MODEL, "messages": messages, "stream": False, "think": False, "options": OPTIONS,
            "keep_alive": -1}
    t0 = time.time()
    return api(host, "/api/chat", body, timeout=3600), time.time() - t0

def run(variant):
    rows = load(variant)[: SMOKE_N if MODE == "smoke" else None]
    path = OUT / f"baseline_{variant}.jsonl"
    resume_from_input(variant, path)
    done = {r["id"] for r in read(path) if valid(r)} if path.exists() else set()
    todo = [r for r in rows if r["id"] not in done]
    log(f"{variant}: {len(rows)} istem, {len(done)} tamam, {len(todo)} çalışacak "
        f"({len(HOSTS)} sunucu × {PARALLEL} eşzamanlı)")
    jobs = queue.Queue()
    for r in todo:
        jobs.put((r, 1))
    lock, state = threading.Lock(), {"n": 0, "errors": 0, "t0": time.time()}
    every = 1 if MODE == "smoke" else 20

    def worker(k):
        host = HOSTS[k % len(HOSTS)]
        while time.time() < START + TIME_BUDGET_H * 3600:
            try:
                r, attempt = jobs.get_nowait()
            except queue.Empty:
                return
            try:
                resp, wall = chat(host, r["messages"])
            except Exception as e:
                log(f"  HATA {r['id']} ({host}, deneme {attempt}): {e!r}")
                with lock:
                    state["errors"] += 1
                if attempt < 2:
                    jobs.put((r, attempt + 1))
                continue
            msg = resp.get("message", {})
            rec = {"id": r["id"], "variant": variant, "prompt_version": r["prompt_version"], "model": MODEL,
                   "model_digest": DIGEST, "adapter": None, "engine": f"ollama {VERSION}",
                   "text": msg.get("content", "").strip(), "prompt_tokens": resp.get("prompt_eval_count"),
                   "completion_tokens": resp.get("eval_count"), "done_reason": resp.get("done_reason"),
                   "thinking_chars": len(msg.get("thinking") or ""), "seconds": round(wall, 1),
                   "prompt_seconds": ns(resp.get("prompt_eval_duration")),
                   "output_seconds": ns(resp.get("eval_duration")), "gpu": HOSTS.index(host), "settings": OPTIONS,
                   "finished": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            if (rec["prompt_tokens"] or 0) + OPTIONS["num_predict"] > OPTIONS["num_ctx"]:
                log(f"  UYARI {r['id']}: istem {rec['prompt_tokens']} token; num_ctx dar olabilir")
            with lock:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\\n")
                state["n"] += 1
                n, elapsed = state["n"], time.time() - state["t0"]
                if n % every == 0 or n == len(todo):
                    tps = (rec["completion_tokens"] or 0) / (rec["output_seconds"] or 1)
                    log(f"  [{len(done) + n}/{len(rows)}] {r['id']} · {wall:.0f} s · {tps:.0f} token/s · "
                        f"{n / elapsed * 3600:.0f} istem/saat · kalan ~{(len(todo) - n) / n * elapsed / 3600:.1f} saat")

    workers = len(HOSTS) * PARALLEL
    with ThreadPoolExecutor(workers) as pool:
        list(pool.map(worker, range(workers)))
    left = jobs.qsize()
    if left:
        log(f"{variant}: süre doldu, {left} istem kaldı. Bu sürümün çıktısını Input olarak ekleyip yeniden çalıştır.")
    return path, state, time.time() - state["t0"]
"""),
    code("""
summary = {}
try:
    for v in VARIANTS:
        path, state, seconds = run(v)
        recs = [r for r in read(path) if valid(r)] if path.exists() else []
        summary[v] = {"kayıt": len(recs), "hata": state["errors"], "süre_s": round(seconds),
                      "istem_saat": round(state["n"] / seconds * 3600) if state["n"] else None,
                      "medyan_s": statistics.median(r["seconds"] for r in recs) if recs else None,
                      "medyan_çıktı_token": statistics.median(r["completion_tokens"] or 0 for r in recs) if recs else None,
                      "sınıra_takılan": sum(r["done_reason"] == "length" for r in recs),
                      "düşünme_metni": sum(r["thinking_chars"] > 0 for r in recs)}
except Exception:
    log("ÜRETİM HATASI:\\n" + traceback.format_exc())
    raise
finally:
    log("Özet:", json.dumps(summary, ensure_ascii=False))
    rates = [s["istem_saat"] for s in summary.values() if s["istem_saat"]]
    if MODE == "smoke" and rates:
        log(f"Tahmin: tam koşu (varyant başına 720 istem) ~{sum(720 / r for r in rates):.1f} saat")
    if MODE == "smoke":
        for v in VARIANTS:
            path = OUT / f"baseline_{v}.jsonl"
            for rec in (read(path)[:2] if path.exists() else []):
                log(f"\\n===== {rec['variant']} · {rec['id']} · girdi {rec['prompt_tokens']} · "
                    f"çıktı {rec['completion_tokens']} token · {rec['seconds']} s\\n{rec['text']}")
    log("Bitti.")
    with zipfile.ZipFile(OUT / f"ergebnisse_{MODE}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.suffix in (".jsonl", ".txt", ".log"):
                z.write(p, p.name)
"""),
    md("""
**Bitince:** Sürümün sayfası → **Output** → `ergebnisse_<MODE>.zip` dosyasını indir ve repoya yükle (`gpu/README.md`, Bölüm 5). Zip, `outputs/` klasöründeki bütün dosyaları içerir.
"""),
]

write("01_baseline.ipynb", cells, Path(sys.argv[1]) if len(sys.argv) > 1 else None)
