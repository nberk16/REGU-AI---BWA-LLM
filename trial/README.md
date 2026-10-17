# Almanca deneme turu: kullanıcı adımları

Üç aday modeli kendi bilgisayarında, 10 örnek ay üzerinde çalıştırırsın. Ben çıktıları doğrulama katmanıyla puanlar ve okurum, sonra temel modeli birlikte seçeriz.

- **Tasarım:** [`docs/08_deneme_turu.md`](../docs/08_deneme_turu.md)
- **Seçilen aylar:** [`inputs/selection.md`](inputs/selection.md)

**Tahmini süre:**
- Kurulum ve indirme: ~1 saat (internet hızına bağlı).
- Çalıştırma: model başına ~40–80 dakika, toplam ~2–4 saat. Bilgisayar bu sırada başka işe kullanılmasa iyi olur.

---

## 1. Ollama

1. [ollama.com/download](https://ollama.com/download) → Windows sürümünü indir ve kur. Kurulumdan sonra arka planda çalışır (görev çubuğunda lama simgesi).
2. NVIDIA sürücüsü güncel olmalı (GeForce Experience veya nvidia.com).
3. PowerShell'i aç ve modelleri indir (toplam ~19 GB disk):

```
ollama pull ministral-3:8b-instruct-2512-q4_K_M
ollama pull gemma4:e4b-it-q4_K_M
ollama pull qwen3.5:9b-q4_K_M
```

4. Kontrol: `ollama list` üç modeli göstermeli.

## 2. Python

- Python 3.11 veya üstü gerekir. Kontrol: `python --version`.
- Yoksa: [python.org/downloads](https://www.python.org/downloads/) veya `winget install Python.Python.3.12`.
- Kurulumda **"Add python.exe to PATH"** kutusunu işaretle.
- Ek paket gerekmez; betik yalnızca Python'un kendi kütüphanesini kullanır.

## 3. Proje dosyalarını indir

**Neden ana sayfada göremiyorsun:** GitHub bir repoyu açınca varsayılan dalı (`main`) gösterir. Bu çalışma ayrı bir dalda, `claude/repodaki-project-analysis-al4o1f`'te duruyor. `trial` klasörü yalnızca orada var.

**En kolay yol: doğrudan ZIP bağlantısı.** GitHub'a giriş yapmış olarak bu bağlantıyı aç; indirme hemen başlar:

https://github.com/nberk16/REGU-AI---BWA-LLM/archive/refs/heads/claude/repodaki-project-analysis-al4o1f.zip

1. İnen ZIP dosyasına sağ tıkla → **Tümünü ayıkla**.
2. Çıkan klasörün adı uzun olur (ör. `REGU-AI---BWA-LLM-claude-repodaki-project-analysis-al4o1f`). İçinde `trial`, `docs`, `validation` … klasörlerini görmelisin.

**Dalı tarayıcıda görmek istersen:** [github.com/nberk16/REGU-AI---BWA-LLM/tree/claude/repodaki-project-analysis-al4o1f](https://github.com/nberk16/REGU-AI---BWA-LLM/tree/claude/repodaki-project-analysis-al4o1f)

Elle seçmek için: repo sayfasında dosya listesinin üstündeki **`main`** düğmesine tıkla → açılan listede `claude/repodaki-project-analysis-al4o1f`'i seç (görünmüyorsa arama kutusuna `claude` yaz) → yeşil **Code** düğmesi → **Download ZIP**.

**Git kullanıyorsan:**

```
git clone -b claude/repodaki-project-analysis-al4o1f https://github.com/nberk16/REGU-AI---BWA-LLM.git
```

## 4. Çalıştır

**PowerShell'i doğru klasörde açmak:** Dosya Gezgini'nde ayıkladığın klasörü aç (içinde `trial`, `docs` … klasörleri görünen klasör). Üstteki adres çubuğuna tıkla, `powershell` yaz, Enter'a bas. PowerShell bu klasörde açılır.

**Önce hızlı deneme** (her modelden 1 örnek, ~15–30 dakika):

```
python trial/run_ollama.py --limit 1
```

Ekranda her örnek için token sayısı, süre ve hız görünür. İstersen bu çıktıyı bana yapıştır; hız beklendiği gibiyse devam edelim.

**Sonra hepsi:**

```
python trial/run_ollama.py
```

- **Kaldığı yerden devam:** Bitmiş örnekler atlanır; yarıda keserseniz (Ctrl+C) aynı komut kaldığı yerden devam eder.
- **Tek model:** `python trial/run_ollama.py --models gemma4-e4b`. Model adları: `ministral-3-8b`, `gemma4-e4b`, `qwen3.5-9b`.
- **Hazırlık:** Şarja tak, uyku modunu kapat, tarayıcı gibi bellek kullanan programları kapat (16 GB RAM'in büyük kısmı gerekiyor).

## 5. Sonuçları gönder

Çıktılar `trial/outputs/` klasöründe, model başına bir dosya:
- `ministral-3-8b.jsonl`
- `gemma4-e4b.jsonl`
- `qwen3.5-9b.jsonl`

Üçünü aynı dala yükle:
- **Tarayıcıdan:** GitHub → dal `claude/repodaki-project-analysis-al4o1f` → `trial/outputs` klasörü yoksa `trial` klasörü → **Add file → Upload files** → dosyaları sürükle (klasör yolu `trial/outputs/` olacak şekilde) → **Commit changes**.
- **Git ile:** `git add trial/outputs` → `git commit -m "Deneme turu çıktıları"` → `git push`.

Sonra bana haber ver. `python trial/score.py` ile puanlarım, çıktıları okurum ve `trial/results.md`'yi yazarım.

## Sorun giderme

| Mesaj | Ne yapmalı |
|---|---|
| `Ollama'ya ulaşılamadı` | Ollama açık değil: Başlat menüsünden Ollama'yı çalıştır |
| `Şu modeller kurulu değil` | Gösterilen `ollama pull …` komutunu çalıştır |
| `UYARI: istem bağlam sınırına dayandı` | Bana haber ver (bağlam penceresini büyütürüz) |
| `UYARI: çıktı uzunluk sınırında kesildi` | Not edilir; puanlamada görünür, bir şey yapmana gerek yok |
| Çok yavaş (örnek başına > 15 dk) | Ekrandaki satırları bana gönder; daha küçük bir model çeşidi deneriz |
