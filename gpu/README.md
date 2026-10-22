# Kaggle adımları (GPU)

Bu klasördekiler Kaggle'da (ücretsiz T4 GPU) çalışır. Kod ve veriyi ben hazırlıyorum, sen Kaggle'da çalıştırıp çıktıları repoya yüklüyorsun. Anahtar ya da şifre gerekmiyor.

- **Veri:** `gpu/data/*.jsonl.gz` (repoda; `python -m training` üretir, `docs/12_egitim_verisi.md`).
- **Defterler:**
  - `01_baseline.ipynb`: ince ayar öncesi model (çıplak model, yalnızca RAG).
  - Sonrakiler: ince ayar (yalnızca FT, RAG + FT) ve değerlendirme.

---

## 1. Veri setini Kaggle'a yükle (bir kez)

1. Repoyu ZIP olarak indir ve çıkart: https://github.com/nberk16/REGU-AI---BWA-LLM/archive/refs/heads/claude/repodaki-project-analysis-al4o1f.zip
2. Kaggle'da sol menü → **Datasets** → **New Dataset**.
3. Çıkarttığın klasörde `gpu/data/` içindeki **7 dosyayı** (`.jsonl.gz`) sürükle. Dosyaları açma; `.gz` hâliyle yükle.
4. Başlık: `bwa-kommentar-daten`. Görünürlük: **Private**. **Create**.

Veri değişirse aynı veri setine yeni sürüm yüklenir: veri setinin sayfası → **New Version**. Bunu ayrıca söyleyeceğim.

## 2. Defteri aç

1. Kaggle'da sol menü → **Code** → **New Notebook**.
2. Üst menü → **File** → **Import Notebook** → `gpu/01_baseline.ipynb` dosyasını seç → **Import**.
3. Sağ panelde **Session options**:
   - **Accelerator:** `GPU T4 x2`. Defter yalnızca birini kullanır.
   - **Internet:** **On**. Kapalıysa ayarlar menüsünden telefon doğrulaması gerekir; sende yapıldı.
4. Sağ panelde **Input** → **Add Input** → **Your Datasets** → `bwa-kommentar-daten` → **Add**.

## 3. Deneme (smoke test, ~10 dakika)

1. Hücrelerde `MODE = "smoke"` yazıyor; değiştirme.
2. Üst menü → **Run All**.
   - İlk hücre paketleri kurar (2–4 dakika). Ardından model indirilir (~16 GB, birkaç dakika).
3. Son hücre her varyanttan bir yorum yazdırır. Satırlarda `… token/s` hızı görünür.
4. **Bana gönder:**
   - Son hücrenin çıktısı: iki yorum metni ve hız satırları.
   - Herhangi bir hücre kırmızı hata verirse, hatanın son 15–20 satırı.

## 4. Tam koşu (benim onayımdan sonra)

1. Parametre hücresinde `MODE = "smoke"` → `MODE = "full"`.
2. Sağ üst → **Save Version** → **Save & Run All (Commit)** → **Save**.
   - Kaggle defteri arka planda çalıştırır; tarayıcıyı kapatabilirsin. Bir oturum en fazla 12 saat sürer.
   - Haftalık GPU kotası ~30 saat; kalan kotayı profil → **Settings** altında görürsün.
3. Durum: defterin sayfası → **Versions**. Çalışan sürüm „Running“, biten „Succeeded“ olur.

Süre, deneme koşusundaki hıza bağlı; tahmini ben deneme sonucundan sonra veririm. Koşu 12 saati aşacaksa varyantları ayrı koşulara bölerim.

## 5. Çıktıları repoya yükle

1. Biten sürümün sayfası → **Output** → `outputs/baseline_ohne_kontext.jsonl` ve `outputs/baseline_rag_k8.jsonl` dosyalarını indir.
2. Bu bağlantıyla yükle: https://github.com/nberk16/REGU-AI---BWA-LLM/upload/claude/repodaki-project-analysis-al4o1f/gpu
3. Altta „Commit directly to the `claude/repodaki-project-analysis-al4o1f` branch“ seçili olmalı → **Commit changes** → sayfanın üstünde „Add files via upload“ yazısını gör.

## Sorun giderme

| Durum | Ne yapmalı |
|---|---|
| `… bulunamadı: sağ panelde Add Input …` | Bölüm 2.4: veri setini defterin girdisine ekle |
| `pip` hücresinde ağ hatası | **Internet: On** olmalı (Bölüm 2.3) |
| `CUDA out of memory` ve defter durdu | Hatanın son satırlarını gönder; parti boyutunu düşürürüm |
| `bellek yetmedi; parti boyutu → …` satırı | Hata değil; defter partiyi küçültüp devam eder |
| Oturum kapandı ya da 12 saat doldu | Aynı defteri yeniden çalıştır; biten aylar `outputs/` içinde korunmaz. Bu durumda bana haber ver, koşuyu bölerim |
