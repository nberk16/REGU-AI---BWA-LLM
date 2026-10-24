"""gpu/03_eval.ipynb: ince ayarlı modellerle test kümesinin üretimi (llama-server + LoRA; docs/14).

Kullanım: python gpu/tools/nb_03_eval.py [hedef.ipynb]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbbuild import code, md, write  # noqa: E402

cells = [
    md("""
# 03 — Değerlendirme: ince ayarlı modellerle test kümesi

İnce ayarlı modellerin test yorumlarını üretir (720 firma-ay, `reference_seed42`). Puanlama repoda `python -m scoring` ile yapılır (`docs/13`).

| Sistem | Varyant | Karşılaştırmadaki yeri (CLAUDE.md 7) |
|---|---|---|
| `ft_rag` | `rag_k8` | **RAG + FT**: hedeflenen varyant |
| `ft_ohne` | `ohne_kontext` | Yalnızca FT |
| `ft_rag` | `ohne_kontext` | RAG + FT modeli bağlamsız (ek satır, karar turu 12) |
| `ft_rag` | `rag_alle` | RAG + FT, penceredeki bütün notlar (retrieval'ın katkısı) |
| `base` | `rag_k8` | Taban model aynı yoldan: Ollama baseline'ıyla tutarlılık kontrolü |

**Nasıl çalışır:**
- **Model:** Baseline'daki model dosyası (`gemma4:e4b-it-q4_K_M`, Ollama 0.40.10) Ollama'nın içindeki llama-server ile çalışır. Ollama 0.40 LoRA bağdaştırıcısını desteklemiyor; llama-server destekliyor.
- **Bağdaştırıcılar:** 02_finetune'un çıktısından gelir (`adapter_rag.gguf`, `adapter_ohne.gguf`) ve istek başına seçilir.
- **İstem:** Gemma 4 şablonuyla burada yazılır. Token sayıları baseline ile karşılaştırılarak denetlenir.
- **Ayarlar:** Baseline ile aynı örnekleme: `temperature 0.2`, `top_p 0.95`, `top_k 64`, `seed 42`, en fazla 1.500 token.
- **Düzen:** Her T4'e bir sunucu, sunucu başına 4 eşzamanlı istem. Süre sınırı ve kaldığı yerden devam 01'deki gibi.

**Kullanım:** `gpu/README.md`, Bölüm 7. Önce `MODE = "smoke"` (koşu başına 8 istem).
"""),
    code("""
MODE = "smoke"                  # "smoke": koşu başına 8 istem · "full": 720
RUNS = [                        # (sistem, varyant); sistem → bağdaştırıcı (base: bağdaştırıcısız)
    ("ft_rag", "rag_k8"),       # RAG + FT (hedeflenen varyant)
    ("ft_ohne", "ohne_kontext"),  # yalnızca FT
    ("ft_rag", "ohne_kontext"), # RAG + FT bağlamsız (ek satır)
    ("ft_rag", "rag_alle"),     # RAG + FT, bütün notlar
    ("base", "rag_k8"),         # taban model aynı yoldan (tutarlılık kontrolü)
]
ADAPTERS = {"ft_rag": "adapter_rag.gguf", "ft_ohne": "adapter_ohne.gguf"}
OLLAMA_VERSION = "0.40.10"      # baseline tam koşusuyla aynı
OLLAMA_MODEL = "gemma4:e4b-it-q4_K_M"
HF_TOKENIZER = "unsloth/gemma-4-E4B-it"
GEN = {"temperature": 0.2, "top_k": 64, "top_p": 0.95, "min_p": 0.0, "repeat_penalty": 1.0, "seed": 42,
       "n_predict": 1500}       # baseline (Ollama) ile aynı örnekleme
CTX = 12288                     # en uzun istem ~7.500 token + 1.500 yeni token, pay ile
PARALLEL = 4                    # GPU başına aynı anda işlenen istem
SMOKE_N = 8
TIME_BUDGET_H = 11.0
"""),
    code("""
# llama-server (Ollama'nın içinde) ve sohbet şablonu için güncel transformers
!apt-get -qq update > /dev/null && apt-get -qq install -y zstd pciutils > /dev/null
!curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION=0.40.10 sh
!pip install -q --upgrade transformers
"""),
    code("""
import glob, gzip, hashlib, json, os, queue, statistics, subprocess, threading, time, traceback, zipfile
import urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

START = time.time()
OUT = Path("/kaggle/working/outputs")
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"log_eval_{MODE}.txt"
OLLAMA_LIB = Path("/usr/local/lib/ollama")
_log_lock = threading.Lock()

def log(*parts):
    \"\"\"Ekrana ve günlük dosyasına (Output'tan indirilebilir; oturum kapansa da kalır).\"\"\"
    line = " ".join(str(p) for p in parts)
    with _log_lock:
        print(line, flush=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} {line}\\n")

def find(stem):
    \"\"\"Veri dosyası: .jsonl.gz ya da (Kaggle yüklerken sıkıştırmayı açtıysa) .jsonl.\"\"\"
    for pattern in (f"/kaggle/input/**/{stem}.jsonl.gz", f"/kaggle/input/**/{stem}.jsonl"):
        hits = sorted(glob.glob(pattern, recursive=True))
        if hits:
            return Path(hits[0])
    seen = sorted(glob.glob("/kaggle/input/**/*", recursive=True))[:30]
    raise FileNotFoundError(f"{stem} bulunamadı. Sağ panel → Input → Add Input → veri setini ekle. "
                            f"/kaggle/input içinde görülen: {seen or 'hiçbir şey'}")

def load(stem):
    path = find(stem)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def read(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def api(url, body=None, timeout=60):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def wait(url, seconds, proc=None, logfile=None):
    for _ in range(seconds):
        try:
            return api(url)
        except (urllib.error.URLError, OSError):
            if proc is not None and proc.poll() is not None:
                raise RuntimeError(f"süreç kapandı: {logfile}")
            time.sleep(1)
    raise RuntimeError(f"yanıt yok: {url} ({logfile})")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def gpus():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader"],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]

log(f"Başlangıç · MODE={MODE} · GPU: {gpus() or 'YOK'}")

# Bağdaştırıcılar: 02_finetune'un çıktısı Input olarak eklenmiş olmalı
ADAPTER_PATH, ADAPTER_SHA = {}, {}
for system, name in ADAPTERS.items():
    hits = sorted(glob.glob(f"/kaggle/input/**/{name}", recursive=True))
    if not hits:
        log(f"{system}: {name} bulunamadı (02_finetune çıktısını Input olarak ekle); bu sistemin koşuları atlanır")
        continue
    path = Path(hits[0])
    info_path = path.parent / name.replace("adapter_", "run_info_").replace(".gguf", ".json")
    info = json.loads(info_path.read_text()) if info_path.exists() else {}
    ready = info.get("mode") == "full" and info.get("complete")
    log(f"{system}: {path} · eğitim {info.get('mode')}, adım {info.get('global_step')}/{info.get('max_steps')}, "
        f"doğrulama kaybı {info.get('eval_loss_before')} → {info.get('eval_loss_after')}")
    if MODE == "full" and not ready:
        log(f"{system}: bağdaştırıcı tam eğitilmemiş (smoke ya da yarım); tam koşuda kullanılmıyor")
        continue
    ADAPTER_PATH[system], ADAPTER_SHA[system] = path, sha256(path)
RUNS = [(s, v) for s, v in RUNS if s == "base" or s in ADAPTER_PATH]
if not RUNS:
    raise RuntimeError("Çalışacak koşu yok: bağdaştırıcılar bulunamadı")
LORA_IDS = {s: i for i, s in enumerate(ADAPTER_PATH)}
log("Koşular:", RUNS, "· istemler:", {v: len(load(f"test_{v}")) for v in sorted({v for _, v in RUNS})})
"""),
    code("""
from transformers import AutoTokenizer

tok = AutoTokenizer.from_pretrained(HF_TOKENIZER)
BOS = tok.bos_token or "<bos>"

def render(messages):
    \"\"\"Modelin kendi sohbet şablonu, düşünme kipi kapalı (eğitim ve baseline ile aynı).\"\"\"
    return tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)

def n_tokens(text):
    return len(tok(text, add_special_tokens=False)["input_ids"])

for variant, rid, expected in (("rag_k8", "A1-v00_2025-02", 5033), ("ohne_kontext", "A1-v00_2025-02", 3218)):
    rec = next(r for r in load(f"test_{variant}") if r["id"] == rid)
    got = n_tokens(render(rec["messages"]))
    if got != expected:
        log(f"ŞABLON FARKLI: {variant} {rid} {got} token, baseline'da {expected}")
        raise AssertionError("sohbet şablonu baseline'dan farklı")
log("Şablon: test istemlerinin token sayısı baseline ile aynı (5033, 3218)")
"""),
    code("""
def base_blobs(port=11500):
    \"\"\"Taban modeli Ollama ile indirir; model ve taslak (draft) dosyalarının yolunu döner.\"\"\"
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "OLLAMA_HOST": f"127.0.0.1:{port}"}
    proc = subprocess.Popen(["ollama", "serve"], env=env, stdout=open(OUT / "ollama_pull.log", "w"),
                            stderr=subprocess.STDOUT)
    try:
        wait(f"http://127.0.0.1:{port}/api/version", 60, proc, "ollama_pull.log")
        api(f"http://127.0.0.1:{port}/api/pull", {"model": OLLAMA_MODEL, "stream": False}, timeout=3600)
        modelfile = api(f"http://127.0.0.1:{port}/api/show", {"model": OLLAMA_MODEL})["modelfile"]
    finally:
        proc.terminate()
    model = next(l.split(" ", 1)[1] for l in modelfile.splitlines() if l.startswith("FROM /"))
    draft = next((l.split(" ", 1)[1] for l in modelfile.splitlines() if l.startswith("DRAFT /")), None)
    return model, draft

<<SERVER>>

try:
    t0 = time.time()
    MODEL_BLOB, DRAFT = base_blobs()
    BLOB = Path(MODEL_BLOB).name
    log(f"Taban model: {OLLAMA_MODEL} · {BLOB[:19]} · taslak model {'var' if DRAFT else 'yok'} · {time.time() - t0:.0f} s")
    LORAS = [ADAPTER_PATH[s] for s in LORA_IDS]
    SERVERS, HOSTS = [], []
    for i, _ in enumerate(gpus() or ["cpu"]):
        t0 = time.time()
        SERVERS.append(start_server(i, 8090 + i, MODEL_BLOB, LORAS, PARALLEL, CTX, DRAFT))
        HOSTS.append(f"http://127.0.0.1:{8090 + i}")
        log(f"  llama-server GPU {i}: hazır · {time.time() - t0:.0f} s · bağdaştırıcılar {list(LORA_IDS)}")
    log("GPU belleği:", gpus())
except Exception:
    log("SUNUCU HAZIRLANAMADI:\\n" + traceback.format_exc())
    raise
"""),
    code("""
def ns(ms):
    return round(ms / 1000, 1) if ms else None

def valid(rec, system):
    \"\"\"Aynı model, bağdaştırıcı ve ayarlarla tamamlanmış kayıt (devam ederken yeniden çalıştırılmaz).\"\"\"
    return (rec.get("system") == system and rec.get("model_blob") == BLOB
            and rec.get("adapter_sha256") == ADAPTER_SHA.get(system) and rec.get("settings") == GEN
            and bool(rec.get("text")))

def resume_from_input(system, variant, path):
    \"\"\"Önceki sürümün çıktısı Input olarak eklendiyse geçerli kayıtları al.\"\"\"
    if path.exists():
        return
    recs, seen = {}, 0
    for p in sorted(glob.glob(f"/kaggle/input/**/{path.name}", recursive=True)):
        rows = read(p)
        seen += len(rows)
        recs.update({r["id"]: r for r in rows if valid(r, system)})
    if seen:
        log(f"{path.stem}: önceki çıktıda {seen} kayıt, {len(recs)} geçerli")
    if recs:
        with open(path, "w", encoding="utf-8") as f:
            for r in recs.values():
                f.write(json.dumps(r, ensure_ascii=False) + "\\n")

def complete(host, prompt, system):
    scales = [1.0 if LORA_IDS.get(system) == i else 0.0 for i in range(len(LORA_IDS))]
    body = {"prompt": prompt, **GEN, "cache_prompt": True, "lora": [{"id": i, "scale": s} for i, s in enumerate(scales)]}
    t0 = time.time()
    return api(f"{host}/completion", body, timeout=3600), time.time() - t0

def run(system, variant):
    rows = load(f"test_{variant}")[: SMOKE_N if MODE == "smoke" else None]
    path = OUT / f"{system}_{variant}.jsonl"
    resume_from_input(system, variant, path)
    done = {r["id"] for r in read(path) if valid(r, system)} if path.exists() else set()
    todo = [r for r in rows if r["id"] not in done]
    log(f"{system} · {variant}: {len(rows)} istem, {len(done)} tamam, {len(todo)} çalışacak "
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
            full = render(r["messages"])
            try:
                resp, wall = complete(host, full.removeprefix(BOS), system)   # BOS'u sunucu ekler
            except Exception as e:
                log(f"  HATA {r['id']} ({host}, deneme {attempt}): {e!r}")
                with lock:
                    state["errors"] += 1
                if attempt < 2:
                    jobs.put((r, attempt + 1))
                continue
            t = resp.get("timings", {})
            text = resp.get("content", "")
            rec = {"id": r["id"], "variant": variant, "system": system, "prompt_version": r["prompt_version"],
                   "model": OLLAMA_MODEL, "model_blob": BLOB, "adapter": ADAPTERS.get(system),
                   "adapter_sha256": ADAPTER_SHA.get(system), "engine": f"llama-server (ollama {OLLAMA_VERSION})",
                   "text": text.strip(), "prompt_tokens": n_tokens(full), "completion_tokens": resp.get("tokens_predicted"),
                   "done_reason": {"eos": "stop", "limit": "length"}.get(resp.get("stop_type"), resp.get("stop_type")),
                   "thinking_chars": len(text) if "<|channel>" in text else 0, "seconds": round(wall, 1),
                   "prompt_seconds": ns(t.get("prompt_ms")), "output_seconds": ns(t.get("predicted_ms")),
                   "draft_accepted": round(t["draft_n_accepted"] / t["draft_n"], 2) if t.get("draft_n") else None,
                   "gpu": HOSTS.index(host), "settings": GEN,
                   "finished": datetime.now(timezone.utc).isoformat(timespec="seconds")}
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
        log(f"{system} · {variant}: süre doldu, {left} istem kaldı. Bu sürümün çıktısını Input olarak ekleyip yeniden çalıştır.")
    return path, state, time.time() - state["t0"]
"""),
    code("""
summary = {}
try:
    for system, variant in RUNS:
        path, state, seconds = run(system, variant)
        recs = [r for r in read(path) if valid(r, system)] if path.exists() else []
        summary[f"{system}_{variant}"] = {
            "kayıt": len(recs), "hata": state["errors"], "süre_s": round(seconds),
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
        log(f"Tahmin: tam koşu (koşu başına 720 istem) ~{sum(720 / r for r in rates):.1f} saat")
    if MODE == "smoke":
        for system, variant in RUNS:
            path = OUT / f"{system}_{variant}.jsonl"
            for rec in (read(path)[:2] if path.exists() else []):
                log(f"\\n===== {system} · {variant} · {rec['id']} · girdi {rec['prompt_tokens']} · "
                    f"çıktı {rec['completion_tokens']} token · {rec['seconds']} s\\n{rec['text']}")
    for proc in globals().get("SERVERS", []):
        proc.terminate()
    log("Bitti.")
    with zipfile.ZipFile(OUT / f"ergebnisse_eval_{MODE}.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.iterdir()):
            if p.suffix in (".jsonl", ".txt", ".log"):
                z.write(p, p.name)
"""),
    md("""
**Bitince:** Sürümün sayfası → **Output** → `ergebnisse_eval_<MODE>.zip` dosyasını indir ve repoya yükle (`gpu/README.md`, Bölüm 7).
"""),
]

write("03_eval.ipynb", cells, Path(sys.argv[1]) if len(sys.argv) > 1 else None)
