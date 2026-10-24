"""gpu/02_finetune.ipynb: QLoRA ince ayarı (yalnızca FT ve RAG + FT), bağdaştırıcının GGUF'a çevrilmesi ve denenmesi.

Kullanım: python gpu/tools/nb_02_finetune.py [hedef.ipynb]   (docs/14_ince_ayar.md)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nbbuild import code, md, write  # noqa: E402

cells = [
    md("""
# 02 — İnce ayar (QLoRA): yalnızca FT ve RAG + FT

Bir koşu bir model eğitir (`TRAIN`):

| `TRAIN` | Eğitim verisi | Model | Karşılaştırmadaki yeri (CLAUDE.md 7) |
|---|---|---|---|
| `rag` | `train_rag` (898 örnek): istem `rag_k8` + ideal metin | RAG + FT | Hedeflenen varyant |
| `ohne` | `train_ohne` (933 örnek): bağlamsız istem + bağlamsız ideal metin | Yalnızca FT | Karar turu 12 (B) |

**Ne yapar:**
1. Taban model `unsloth/gemma-4-E4B-it` 4-bit; LoRA yalnızca dil katmanlarında. Kayıp yalnızca modelin yanıtında hesaplanır, istemde hesaplanmaz.
2. Eğitim öncesi ve sonrası doğrulama kaybını ölçer (`val_*`, 32 örnek).
3. Bağdaştırıcıyı kaydeder ve GGUF'a çevirir (`adapter_<TRAIN>.gguf`, llama.cpp).
4. Bağdaştırıcıyı baseline'daki modelin üzerinde llama-server ile dener (GPU 1). Aynı doğrulama örneği bir kez bağdaştırıcısız, bir kez bağdaştırıcıyla üretilir.

**Kipler:**
- `smoke`: en uzun 12 örnekle 3 adım; hız ve bellek ölçümü, tam eğitim süresinin tahmini ve bütün hattın denemesi (~30–45 dk).
- `full`: 1 epoch. Checkpoint'ler `checkpoints_<TRAIN>/` altına yazılır. Süre dolarsa durur; bu sürümün çıktısı Input olarak eklenince kaldığı yerden devam eder.

**Çıktı:** `/kaggle/working/outputs/`. Bağdaştırıcılar Kaggle'da kalır (03_eval onları Input olarak alır); repoya yalnızca `ergebnisse_finetune_<TRAIN>_<MODE>.zip` yüklenir. Kullanım: `gpu/README.md`, Bölüm 6.
"""),
    code("""
MODE = "smoke"              # "smoke": hız/bellek ölçümü + hat denemesi · "full": eğitim
TRAIN = "rag"               # "rag": RAG + FT (train_rag) · "ohne": yalnızca FT (train_ohne)

MODEL = "unsloth/gemma-4-E4B-it-unsloth-bnb-4bit"   # 4-bit taban (QLoRA); deneme koşusu 1'de yüklendi
HF_BASE = "unsloth/gemma-4-E4B-it"                   # yapılandırma: bağdaştırıcının GGUF'a çevrilmesi için
OLLAMA_VERSION = "0.40.10"                           # baseline tam koşusuyla aynı (llama-server ve model dosyası)
OLLAMA_MODEL = "gemma4:e4b-it-q4_K_M"
LLAMA_CPP_COMMIT = "3f03b17724ad8b69040825f45c43c59b092a0244"   # convert_lora_to_gguf.py (Gemma 4 ile denendi)

MAX_SEQ = 7168              # en uzun eğitim örneği 7.076 token (train_rag)
LORA_R, LORA_ALPHA = 16, 16
LR, EPOCHS, GRAD_ACC = 2e-4, 1, 8                    # etkin parti 8 → rag ~113, ohne ~117 adım
EVAL_N = 32                 # doğrulama kaybı için val örneği (eğitim öncesi ve sonrası)
SAVE_STEPS = 10             # checkpoint aralığı (adım)
TIME_BUDGET_H = 10.0        # bu süreden sonra eğitim durur ve kaydeder (oturum en fazla 12 saat)
SEED = 3407
SMOKE = {"examples": 12, "grad_acc": 4, "eval_n": 4}   # smoke: en uzun 12 örnek, 3 adım (bellekte en kötü durum)
SMOKE_FALLBACK = 6000       # smoke'ta bellek yetmezse hız bu uzunluğun altındaki örneklerle ölçülür
GEN = {"temperature": 0.2, "top_k": 64, "top_p": 0.95, "min_p": 0.0, "repeat_penalty": 1.0, "seed": 42,
       "n_predict": 1500}   # baseline (Ollama) ile aynı örnekleme
"""),
    code("""
# Unsloth (QLoRA) ve TRL; deneme koşusu 1'de aynı kurulum çalıştı
!pip install -q --upgrade unsloth
"""),
    code("""
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"     # eğitim GPU 0'da; GPU 1 sondaki bağdaştırıcı denemesi için boş kalır
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"   # parçalanmaya karşı (PyTorch önerisi)

import dataclasses, gc, glob, gzip, hashlib, json, shutil, subprocess, time, traceback, urllib.error, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

START = time.time()
OTHER = {"rag": "ohne", "ohne": "rag"}[TRAIN]
OUT = Path("/kaggle/working/outputs")
OUT.mkdir(parents=True, exist_ok=True)
LOG = OUT / f"log_{MODE}_{TRAIN}.txt"
CKPT = OUT / f"checkpoints_{TRAIN}"
ADAPTER = OUT / f"adapter_{TRAIN}"
GGUF = OUT / f"adapter_{TRAIN}.gguf"
INFO = OUT / f"run_info_{TRAIN}.json"
HISTORY = OUT / f"train_history_{TRAIN}.json"
CHECK = OUT / f"check_{TRAIN}.json"
OLLAMA_LIB = Path("/usr/local/lib/ollama")

def log(*parts):
    \"\"\"Ekrana ve günlük dosyasına (Output'tan indirilebilir; oturum kapansa da kalır).\"\"\"
    line = " ".join(str(p) for p in parts)
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

def sh(cmd, check=True):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and r.returncode != 0:
        log(f"KOMUT HATASI ({r.returncode}): {cmd}\\n{(r.stdout + r.stderr)[-3000:]}")
        raise RuntimeError(cmd)
    return r

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

CONFIG = {"train": TRAIN, "model": MODEL, "max_seq": MAX_SEQ, "lora_r": LORA_R, "lora_alpha": LORA_ALPHA, "lr": LR,
          "epochs": EPOCHS, "grad_acc": GRAD_ACC, "seed": SEED, "data": sha256(find(f"train_{TRAIN}"))[:16]}

log(f"Başlangıç · MODE={MODE} · TRAIN={TRAIN} · GPU: "
    f"{sh('nvidia-smi --query-gpu=name,memory.total --format=csv,noheader', check=False).stdout.split(chr(10))[:2]}")

# Önceki sürümün çıktısı Input olarak eklendiyse diğer modelin dosyalarını taşı: 03_eval iki bağdaştırıcıyı bir arada bulur
carried = []
for p in sorted(glob.glob("/kaggle/input/**/*", recursive=True)):
    name = Path(p).name
    if Path(p).is_file() and name.startswith((f"adapter_{OTHER}.gguf", f"run_info_{OTHER}", f"train_history_{OTHER}",
                                              f"check_{OTHER}")) and not (OUT / name).exists():
        shutil.copy(p, OUT / name)
        carried.append(name)
if carried:
    log("Önceki çıktıdan taşınan:", carried)
"""),
    code("""
import torch
from unsloth import FastModel

def call(fn, **kw):
    \"\"\"Sürüme göre bilinmeyen bir argüman varsa onsuz yeniden dener (ör. use_gradient_checkpointing).\"\"\"
    try:
        return fn(**kw)
    except TypeError as e:
        bad = [k for k in kw if f"'{k}'" in str(e)]
        if not bad:
            raise
        log(f"  {fn.__name__}: {bad} desteklenmiyor, onsuz")
        return call(fn, **{k: v for k, v in kw.items() if k not in bad})

t0 = time.time()
try:
    model, tokenizer = call(FastModel.from_pretrained, model_name=MODEL, max_seq_length=MAX_SEQ, load_in_4bit=True,
                            full_finetuning=False, dtype=None)
    model = call(FastModel.get_peft_model, model=model, finetune_vision_layers=False, finetune_language_layers=True,
                 finetune_attention_modules=True, finetune_mlp_modules=True, r=LORA_R, lora_alpha=LORA_ALPHA,
                 lora_dropout=0, bias="none", random_state=SEED, use_gradient_checkpointing="unsloth")
except Exception:
    log("MODEL YÜKLENEMEDİ:\\n" + traceback.format_exc())
    raise
trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
free, total = torch.cuda.mem_get_info()
log(f"Model + LoRA: {time.time() - t0:.0f} s · eğitilen parametre {trainable / 1e6:.1f} Mio. · "
    f"GPU belleği {(total - free) / 1e9:.1f} / {total / 1e9:.1f} GB")

# Bellek (deneme koşusu 2'de 7.076 tokenlık örnekte yetmedi): eğitimde gerekmeyen büyük parçalar GPU'dan çıkar.
# - Katman başına gömme tablosu (2,8 Mrd. parametre, ~5,6 GB): yalnızca tablo araması; işlemcide yapılır.
# - Ses ve görüntü kodlayıcıları (~0,9 GB): metin eğitiminde kullanılmaz.
class CpuEmbedding(torch.nn.Module):
    \"\"\"Gömme tablosu işlemcide; arama sonucu girdinin cihazına taşınır. Tablo donmuş (LoRA'da eğitilmez).\"\"\"
    def __init__(self, inner):
        super().__init__()
        object.__setattr__(self, "_inner", inner.to("cpu"))   # kayıtlı alt modül değil: model.to(...) geri taşımaz
    @property
    def weight(self):
        return self._inner.weight
    def forward(self, input_ids):
        return self._inner(input_ids.to("cpu")).to(input_ids.device)

moved = []
for name, mod in list(model.named_modules()):
    short = name.rsplit(".", 1)[-1]
    try:
        if short == "embed_tokens_per_layer" and not isinstance(mod, CpuEmbedding):
            setattr(model.get_submodule(name.rsplit(".", 1)[0]), short, CpuEmbedding(mod))
            moved.append(short)
        elif short in ("audio_tower", "vision_tower", "embed_audio", "embed_vision"):
            mod.to("cpu")
            moved.append(short)
    except Exception as e:
        log(f"  {name} taşınamadı: {e!r}")
gc.collect()
torch.cuda.empty_cache()
free, total = torch.cuda.mem_get_info()
log(f"İşlemciye taşınan: {moved} · GPU belleği {(total - free) / 1e9:.1f} / {total / 1e9:.1f} GB")
"""),
    code("""
from datasets import Dataset

tok = getattr(tokenizer, "tokenizer", tokenizer)     # çok kipli modelde metin tokenizer'ı
BOS = tok.bos_token or "<bos>"

def render(messages, gen):
    \"\"\"Modelin kendi sohbet şablonu, düşünme kipi kapalı (baseline ve değerlendirmeyle aynı).\"\"\"
    kw = dict(tokenize=False, add_generation_prompt=gen, enable_thinking=False)
    try:
        return tokenizer.apply_chat_template(messages, **kw)
    except Exception:
        msgs = [{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]} for m in messages]
        return tokenizer.apply_chat_template(msgs, **kw)

def n_tokens(text):
    return len(tok(text, add_special_tokens=False)["input_ids"])

# Şablon baseline ile aynı mı? Ollama'nın baseline koşusunda saydığı istem uzunlukları
for variant, rid, expected in (("rag_k8", "A1-v00_2025-02", 5033), ("ohne_kontext", "A1-v00_2025-02", 3218)):
    rec = next(r for r in load(f"test_{variant}") if r["id"] == rid)
    got = n_tokens(render(rec["messages"], True))
    if got != expected:
        log(f"ŞABLON FARKLI: {variant} {rid} {got} token, baseline'da {expected}")
        raise AssertionError("sohbet şablonu baseline'dan farklı")
log("Şablon: test istemlerinin token sayısı baseline ile aynı (5033, 3218)")

def examples(stem):
    out = []
    for r in load(stem):
        full, prompt = render(r["messages"], False), render(r["messages"][:2], True)
        if not full.startswith(prompt):
            raise AssertionError(f"{r['id']}: istem, eğitim metninin başı değil")
        # Metin BOS'la başlar: Gemma 4 tokenizer'ı BOS eklemiyor (deneme koşusu 24.10). Eğitimde tokenizer yine de
        # eklerse aşağıda bir kez silinir; her iki durumda dizi tam olarak bir BOS ile başlar.
        out.append({"id": r["id"], "text": full, "tokens": n_tokens(full),
                    "answer": r["messages"][2]["content"], "messages": r["messages"]})
    return out

train_all, val_all = examples(f"train_{TRAIN}"), examples(f"val_{TRAIN}")
too_long = [e["id"] for e in train_all if e["tokens"] > MAX_SEQ]
train_all = [e for e in train_all if e["tokens"] <= MAX_SEQ]
step = max(1, len(val_all) // EVAL_N)
val_eval = sorted(val_all, key=lambda e: e["id"])[::step][:EVAL_N]
totals = {TRAIN: sum(e["tokens"] for e in train_all)}
if MODE == "smoke":
    totals[OTHER] = sum(n_tokens(render(r["messages"], False)) for r in load(f"train_{OTHER}"))
    train_sel = sorted(train_all, key=lambda e: -e["tokens"])[:SMOKE["examples"]]
    val_eval = val_eval[:SMOKE["eval_n"]]
else:
    train_sel = train_all
log(f"Veri: train_{TRAIN} {len(train_all)} örnek (MAX_SEQ üstü dışarıda: {too_long or 'yok'}), "
    f"eğitimde {len(train_sel)} · val {len(val_all)}, kayıp için {len(val_eval)} · token toplamı {totals}")
"""),
    code("""
from transformers import TrainerCallback
from trl import SFTConfig, SFTTrainer
from unsloth.chat_templates import train_on_responses_only

smoke = MODE == "smoke"
args = dict(output_dir=str(CKPT), dataset_text_field="text", per_device_train_batch_size=1,
            gradient_accumulation_steps=SMOKE["grad_acc"] if smoke else GRAD_ACC, per_device_eval_batch_size=1,
            learning_rate=LR, lr_scheduler_type="linear", warmup_ratio=0.0 if smoke else 0.05, optim="adamw_8bit",
            weight_decay=0.01, seed=SEED, logging_steps=1, save_strategy="no" if smoke else "steps",
            save_steps=SAVE_STEPS, save_total_limit=2, report_to="none", eval_strategy="no",
            evaluation_strategy="no", packing=False, dataset_num_proc=2, max_length=MAX_SEQ, max_seq_length=MAX_SEQ)
if smoke:
    args["max_steps"] = SMOKE["examples"] // SMOKE["grad_acc"]
else:
    args["num_train_epochs"] = EPOCHS
fields = {f.name for f in dataclasses.fields(SFTConfig)}
config = SFTConfig(**{k: v for k, v in args.items() if k in fields})

def build_trainer(texts):
    kw = dict(model=model, train_dataset=Dataset.from_list([{"text": t} for t in texts]), args=config)
    try:
        tr = SFTTrainer(tokenizer=tokenizer, **kw)
    except TypeError:
        tr = SFTTrainer(processing_class=tokenizer, **kw)
    # Kayıp yalnızca model turunda (Gemma 4 şablonu; Unsloth Gemma 4 kılavuzu)
    return train_on_responses_only(tr, instruction_part="<|turn>user\\n", response_part="<|turn>model\\n")

def first_ids(tr):
    return tr.train_dataset[0]["input_ids"]

strip_bos = False
trainer = build_trainer([e["text"] for e in train_sel])
ids = first_ids(trainer)
if ids[0] == ids[1] == tok.bos_token_id:          # tokenizer BOS'u kendisi de ekliyor: metindekini sil
    log("Eğitim tokenizasyonu BOS ekliyor; metindeki BOS siliniyor")
    strip_bos = True
    trainer = build_trainer([e["text"].removeprefix(BOS) for e in train_sel])

def check_mask(dataset, name):
    \"\"\"Kayıp hesaplanan tokenlar yalnızca ideal metin mi? Değilse eğitime başlama.

    Her ideal metin „**Kernaussagen <Monat Jahr>**“ ile başlar; istemin hiçbir parçası kayba girmemeli.
    \"\"\"
    row = {k: v for k, v in dataset[0].items() if k in ("input_ids", "attention_mask", "labels")}
    batch = trainer.data_collator([row])
    if "labels" not in batch:
        log(f"Maske ({name}): toplayıcı labels üretmiyor; anahtarlar {list(batch)}")
        raise AssertionError("maske denetlenemedi")
    ids, labels = batch["input_ids"][0].tolist(), batch["labels"][0].tolist()
    kept = tok.decode([i for i, l in zip(ids, labels) if l != -100])
    checks = {"yanit_basi": kept.lstrip().startswith("**Kernaussagen "),
              "istem_yok": "<|turn>" not in kept and "FACTS" not in kept,
              "tek_bos": ids[0] == tok.bos_token_id and ids[1] != tok.bos_token_id}
    ok = all(checks.values())
    log(f"Maske ({name}): {len(ids)} token, kayıpta {sum(l != -100 for l in labels)} · başı {kept[:50]!r} · "
        f"sonu {kept[-20:]!r} · {checks} · {'tamam' if ok else 'HATALI'}")
    if not ok:
        raise AssertionError(f"maske hatalı ({name}): kayıp ideal metinle başlamıyor ya da BOS yanlış")

check_mask(trainer.train_dataset, "train")

class Watch(TrainerCallback):
    \"\"\"Günlük, adım süreleri ve süre sınırı.\"\"\"
    def __init__(self):
        self.ends = []
    def on_step_end(self, args, state, control, **kw):
        self.ends.append(time.time())
        if time.time() > START + TIME_BUDGET_H * 3600:
            log(f"Süre sınırı ({TIME_BUDGET_H} saat): eğitim adım {state.global_step}'de durduruluyor, kaydediliyor")
            control.should_save = True
            control.should_training_stop = True
    def on_log(self, args, state, control, logs=None, **kw):
        if logs:
            vals = ", ".join(f"{k}={v:.4g}" if isinstance(v, float) else f"{k}={v}" for k, v in logs.items())
            log(f"  adım {state.global_step}/{state.max_steps} · {vals}")

watch = Watch()
trainer.add_callback(watch)
"""),
    code("""
@torch.no_grad()
def evaluate(tag):
    \"\"\"Doğrulama kaybı yalnızca ideal metnin tokenlarında (eğitimdeki maskeyle aynı tanım).

    Ölçüm başarısız olursa eğitim yine de sürer (kayıp `None` olarak kaydedilir).
    \"\"\"
    try:
        return _evaluate(tag)
    except Exception:
        log(f"Doğrulama kaybı ({tag}) ölçülemedi; eğitim sürüyor:\\n" + traceback.format_exc()[-1500:])
        model.train()
        return None

@torch.no_grad()
def _evaluate(tag):
    t0, total, count = time.time(), 0.0, 0
    model.eval()
    for e in val_eval:
        ids = tok(e["text"], add_special_tokens=False)["input_ids"]            # metin BOS'la başlar
        n_prompt = len(tok(render(e["messages"][:2], True), add_special_tokens=False)["input_ids"])
        x = torch.tensor([ids], device="cuda")
        labels = x.clone()
        labels[:, :n_prompt] = -100
        out = model(input_ids=x, attention_mask=torch.ones_like(x), labels=labels)
        total += out.loss.item() * (len(ids) - n_prompt)
        count += len(ids) - n_prompt
    model.train()
    loss = total / count
    log(f"Doğrulama kaybı ({tag}): {loss:.4f} · {len(val_eval)} örnek, {count} yanıt tokenı · {time.time() - t0:.0f} s")
    return loss

def find_checkpoint():
    \"\"\"Önceki sürümün checkpoint'i (Input): aynı ayarlarla en ileri adım.\"\"\"
    best = None
    for state in glob.glob(f"/kaggle/input/**/checkpoints_{TRAIN}/checkpoint-*/trainer_state.json", recursive=True):
        d = Path(state).parent
        info = d.parent.parent / f"run_info_{TRAIN}.json"
        if not info.exists() or json.loads(info.read_text()).get("config") != CONFIG:
            log(f"  {d}: ayarlar farklı ya da run_info yok; devam için kullanılmıyor")
            continue
        n = int(d.name.split("-")[1])
        if best is None or n > best[0]:
            best = (n, d, json.loads(info.read_text()))
    return best

previous, resume = {}, None
if not smoke:
    found = find_checkpoint()
    if found:
        n, src, previous = found
        resume = CKPT / src.name
        shutil.copytree(src, resume, dirs_exist_ok=True)
        log(f"Devam: önceki sürümün checkpoint'i adım {n}")

info = {"config": CONFIG, "mode": MODE, "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "versions": {m: __import__(m).__version__ for m in ("unsloth", "transformers", "trl", "torch", "peft")},
        "n_train": len(train_sel), "n_eval": len(val_eval)}
INFO.write_text(json.dumps(info, indent=1))
try:
    info["eval_loss_before"] = previous.get("eval_loss_before") if resume else evaluate("eğitim öncesi")
    torch.cuda.reset_peak_memory_stats()
    t0 = time.time()
    try:
        trainer.train(resume_from_checkpoint=str(resume) if resume else None)
    except torch.OutOfMemoryError:
        if not smoke:
            raise
        # Deneme koşusu: bellek sınırını kaydet ve hızı daha kısa örneklerle yine de ölç
        info["oom_tokens"] = train_sel[0]["tokens"]
        info["peak_gpu_gb_oom"] = round(torch.cuda.max_memory_reserved() / 1e9, 1)
        log(f"BELLEK YETMEDİ: en uzun örnek {train_sel[0]['tokens']} token. Hız {SMOKE_FALLBACK} token altındaki "
            f"örneklerle ölçülüyor (train_rag'de bu sınırın üstünde 115 örnek var).")
        del trainer
        gc.collect()
        torch.cuda.empty_cache()
        train_sel = [e for e in sorted(train_all, key=lambda e: -e["tokens"])
                     if e["tokens"] <= SMOKE_FALLBACK][:SMOKE["examples"]]
        trainer = build_trainer([e["text"].removeprefix(BOS) if strip_bos else e["text"] for e in train_sel])
        watch.ends.clear()
        trainer.add_callback(watch)
        torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        trainer.train()
        info["fallback_tokens"] = train_sel[0]["tokens"]
    state = trainer.state
    info |= {"global_step": state.global_step, "max_steps": state.max_steps, "complete": state.global_step >= state.max_steps,
             "train_seconds": round(time.time() - t0), "peak_gpu_gb": round(torch.cuda.max_memory_reserved() / 1e9, 1)}
    log(f"Eğitim: adım {state.global_step}/{state.max_steps} · {info['train_seconds'] / 60:.0f} dk · "
        f"en yüksek GPU belleği {info['peak_gpu_gb']} GB · {'tamamlandı' if info['complete'] else 'YARIDA KALDI'}")
    info["eval_loss_after"] = evaluate("eğitim sonrası")
except Exception:
    log("EĞİTİM HATASI:\\n" + traceback.format_exc())
    INFO.write_text(json.dumps(info, indent=1))
    raise

if smoke and len(watch.ends) >= 2:      # ilk adım ısınma; hız sonraki adımlardan
    per_step = (watch.ends[-1] - watch.ends[0]) / (len(watch.ends) - 1)
    tps = sum(e["tokens"] for e in train_sel) / len(watch.ends) / per_step
    info["tokens_per_second"] = round(tps)
    est = {k: round(v / tps / 3600 * 1.05, 1) for k, v in totals.items()}
    info["epoch_hours_estimate"] = est
    log(f"Hız: {tps:.0f} token/s (en uzun örneklerle) · adım başına {per_step:.0f} s · "
        f"tahmini 1 epoch: " + ", ".join(f"{k} ~{h} saat" for k, h in est.items()))

model.save_pretrained(str(ADAPTER))
tokenizer.save_pretrained(str(ADAPTER))
HISTORY.write_text(json.dumps(trainer.state.log_history, indent=1))
info["finished"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
INFO.write_text(json.dumps(info, indent=1))
from safetensors import safe_open
with safe_open(str(ADAPTER / "adapter_model.safetensors"), "pt") as f:
    keys = list(f.keys())
log(f"Bağdaştırıcı kaydedildi: {ADAPTER.name} · {len(keys)} tensör · ör. {keys[0]}")
"""),
    code("""
# Bağdaştırıcı → GGUF (llama.cpp convert_lora_to_gguf.py) → baseline'daki modelin üzerinde llama-server ile deneme.
# Ollama 0.40 LoRA bağdaştırıcısını desteklemiyor; içindeki llama-server ise destekliyor (docs/14, Bölüm 3).

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

def export_gguf():
    src = Path("/tmp/llama.cpp")
    if not (src / "convert_lora_to_gguf.py").exists():
        sh(f"git init -q {src} && git -C {src} remote add origin https://github.com/ggml-org/llama.cpp && "
           f"git -C {src} fetch -q --depth 1 origin {LLAMA_CPP_COMMIT} && git -C {src} checkout -q FETCH_HEAD")
    from huggingface_hub import snapshot_download
    base = snapshot_download(HF_BASE, allow_patterns=["config.json", "tokenizer.json", "tokenizer_config.json",
                                                      "chat_template.jinja", "special_tokens_map.json"])
    r = sh(f"python {src}/convert_lora_to_gguf.py {ADAPTER} --base {base} --outfile {GGUF} --outtype f16")
    n = next((l.split("n_tensors = ")[1].split(",")[0] for l in (r.stdout + r.stderr).splitlines() if "n_tensors" in l), "?")
    log(f"GGUF: {GGUF.name} · {GGUF.stat().st_size / 1e6:.0f} MB · {n} tensör (tam dil LoRA'sı: 516)")

def install_ollama():
    if not (OLLAMA_LIB / "llama-server").exists():
        sh("apt-get -qq update > /dev/null && apt-get -qq install -y zstd pciutils > /dev/null")
        sh(f"curl -fsSL https://ollama.com/install.sh | OLLAMA_VERSION={OLLAMA_VERSION} sh")

def base_blobs(port=11500):
    \"\"\"Taban modeli Ollama ile indirir; model ve taslak (draft) dosyalarının yolunu döner.\"\"\"
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": "", "OLLAMA_HOST": f"127.0.0.1:{port}"}
    proc = subprocess.Popen(["ollama", "serve"], env=env, stdout=open(OUT / "ollama_pull.log", "w"), stderr=subprocess.STDOUT)
    try:
        wait(f"http://127.0.0.1:{port}/api/version", 60, proc, "ollama_pull.log")
        api(f"http://127.0.0.1:{port}/api/pull", {"model": OLLAMA_MODEL, "stream": False}, timeout=3600)
        modelfile = api(f"http://127.0.0.1:{port}/api/show", {"model": OLLAMA_MODEL})["modelfile"]
    finally:
        proc.terminate()
    model = next(l.split(" ", 1)[1] for l in modelfile.splitlines() if l.startswith("FROM /"))
    draft = next((l.split(" ", 1)[1] for l in modelfile.splitlines() if l.startswith("DRAFT /")), None)
    return model, draft

def start_server(gpu, port, model_blob, loras, slots=1, ctx=12288, draft=None):
    \"\"\"Ollama'nın içindeki llama-server; baseline'daki komutla aynı ayarlar + LoRA (istek başına ölçek).\"\"\"
    cuda = sorted(OLLAMA_LIB.glob("cuda_v*"))
    libdir = cuda[-1] if cuda else OLLAMA_LIB
    env = {**os.environ, "CUDA_VISIBLE_DEVICES": str(gpu),
           "LD_LIBRARY_PATH": f"{libdir}:{OLLAMA_LIB}:" + os.environ.get("LD_LIBRARY_PATH", "")}
    cmd = [str(OLLAMA_LIB / "llama-server"), "--model", model_blob, "--port", str(port), "--host", "127.0.0.1",
           "--no-webui", "--offline", "-c", str(slots * ctx), "-np", str(slots), "-ngl", "999", "--flash-attn", "auto",
           "-b", "1024", "-ub", "1024"]
    if draft:
        cmd += ["--spec-type", "draft-mtp", "--spec-draft-n-max", "3", "--spec-draft-backend-sampling",
                "--spec-draft-model", draft]
    if loras:
        cmd += ["--lora", ",".join(str(p) for p in loras), "--lora-init-without-apply"]
    logfile = OUT / f"llama_server_gpu{gpu}.log"
    proc = subprocess.Popen(cmd, env=env, cwd=libdir, stdout=open(logfile, "w"), stderr=subprocess.STDOUT)
    wait(f"http://127.0.0.1:{port}/health", 900, proc, logfile.name)
    text = logfile.read_text(errors="replace")
    if "CUDA" not in text:
        proc.terminate()
        raise RuntimeError(f"llama-server GPU'yu kullanmıyor ({logfile.name})")
    return proc

def complete(port, prompt, scales):
    body = {"prompt": prompt, **GEN, "cache_prompt": True, "lora": [{"id": i, "scale": s} for i, s in enumerate(scales)]}
    t0 = time.time()
    r = api(f"http://127.0.0.1:{port}/completion", body, timeout=3600)
    return r, time.time() - t0

def summary(text):
    heads = ["**Kernaussagen", "**Abweichungen im Detail**", "**Hinweise auf mögliche Verzerrungen**",
             "**Offene Fragen an Buchhaltung / Steuerberater**"]
    return {"ueberschriften": sum(h in text for h in heads), "hypothese": text.count("(Hypothese)"),
            "quelle": text.count("[Quelle:"), "woerter": len(text.split())}

stage = "GGUF"
try:
    export_gguf()
    stage = "Ollama"
    install_ollama()
    model_blob, _ = base_blobs()
    stage = "llama-server"
    server = start_server(1, 8090, model_blob, [GGUF])
    ex = val_eval[0]
    prompt = render(ex["messages"][:2], True).removeprefix(BOS)    # BOS'u sunucu ekler
    check = {"id": ex["id"], "adapter_sha256": sha256(GGUF)}
    for name, scale in (("taban", 0.0), ("ince_ayar", 1.0)):
        r, secs = complete(8090, prompt, [scale])
        check[name] = {"text": r["content"], "stop": r.get("stop_type"), "tokens": r.get("tokens_predicted"),
                       "seconds": round(secs, 1), **summary(r["content"])}
        log(f"\\n===== Deneme · {ex['id']} · {name} (LoRA ölçeği {scale}) · {r.get('tokens_predicted')} token · "
            f"{secs:.0f} s · {summary(r['content'])}\\n{r['content']}")
    check["ideal"] = summary(ex["answer"])
    log(f"İdeal metin: {check['ideal']}")
    CHECK.write_text(json.dumps(check, ensure_ascii=False, indent=1))
    server.terminate()
    info["gguf_sha256"] = check["adapter_sha256"]
except Exception:
    log(f"{stage} AŞAMASINDA HATA (bağdaştırıcı yine de kaydedildi):\\n" + traceback.format_exc())
    info["export_error"] = stage
INFO.write_text(json.dumps(info, indent=1))
"""),
    code("""
# Repoya yüklenecek küçük dosyalar (bağdaştırıcılar Kaggle'da kalır; 03_eval onları Input olarak alır)
zpath = OUT / f"ergebnisse_finetune_{TRAIN}_{MODE}.zip"
with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (LOG, INFO, HISTORY, CHECK):
        if p.exists():
            z.write(p, p.name)
log(f"Bitti · {zpath.name} · toplam {(time.time() - START) / 3600:.1f} saat")
"""),
    md("""
**Bitince:** Sürümün sayfası → **Output** → `ergebnisse_finetune_<TRAIN>_<MODE>.zip` dosyasını indir ve repoya yükle (`gpu/README.md`, Bölüm 6). Bağdaştırıcıları (`adapter_*.gguf`, `adapter_*/`) indirmen gerekmez.
"""),
]

write("02_finetune.ipynb", cells, Path(sys.argv[1]) if len(sys.argv) > 1 else None)
