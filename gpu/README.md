# Kaggle adımları (GPU)

Bu klasördekiler Kaggle'da (ücretsiz T4 GPU) çalışır. Kod ve veriyi ben hazırlıyorum, sen Kaggle'da çalıştırıp çıktıları repoya yüklüyorsun. Anahtar ya da şifre gerekmiyor.

- **Veri:** `gpu/data/*.jsonl.gz` (repoda; `python -m training` üretir, `docs/12_egitim_verisi.md`).
- **Defterler:**
  - `01_baseline.ipynb`: ince ayar öncesi model (çıplak model, yalnızca RAG).
  - Sonrakiler: ince ayar (yalnızca FT, RAG + FT) ve değerlendirme.

---

## 1. Veri setini Kaggle'a yükle (bir kez)

1. Repoyu ZIP olarak indir: bu bağlantıya tıklamak indirmeyi doğrudan başlatır. Sonra ZIP'i çıkart.
   https://github.com/nberk16/REGU-AI---BWA-LLM/archive/refs/heads/claude/repodaki-project-analysis-al4o1f.zip
2. **En kolay yol, defterin içinden:** Sağ panel → **Input** → **Upload** → **New Dataset**.
   - **Başka yol:** sol menü → **Datasets** → **New Dataset**. Bu durumda Bölüm 2.4'te veri setini ayrıca eklersin.
3. Çıkarttığın klasörde `gpu/data/` içindeki **7 dosyayı** (`.jsonl.gz`) sürükle. Kaggle bunları kendiliğinden açabilir (`.jsonl`); defter iki biçimi de okur.
4. Başlık: `bwa-kommentar-daten`. Görünürlük: **Private**. **Create**.
5. Sağ paneldeki **Input** altında `bwa-kommentar-daten` görünmeli. Yalnızca defterin adı görünüyorsa veri seti eklenmemiştir.

Veri değişirse aynı veri setine yeni sürüm yüklenir: veri setinin sayfası → **New Version**. Bunu ayrıca söyleyeceğim.

## 2. Defteri aç

1. Kaggle'da sol menü → **Code** → **New Notebook**.
2. Üst menü → **File** → **Import Notebook** → `gpu/01_baseline.ipynb` dosyasını seç → **Import**.
3. Sağ panelde **Session options**:
   - **Accelerator:** `GPU T4 x2`. Defter yalnızca birini kullanır.
   - **Internet:** **On**. Kapalıysa ayarlar menüsünden telefon doğrulaması gerekir; sende yapıldı.
4. Sağ panelde **Input** → **Add Input** → **Your Datasets** → `bwa-kommentar-daten` → **Add**.

## 3. Deneme koşusu (smoke test, arka planda ~20–40 dakika)

Etkileşimli oturum başında kimse yokken kapanabilir. Bu yüzden deneme koşusu da arka planda yapılır.

1. Defter güncel olmalı: GitHub'dan en son `gpu/01_baseline.ipynb` dosyasını indir (**Download raw file**), sonra Kaggle'da **File** → **Import Notebook**.
2. **Session options** (Bölüm 2.3) ve **Input** (Bölüm 1.5) yerinde olmalı. Parametre hücresinde `MODE = "smoke"` kalsın.
3. Sağ üst → **Save Version** → **Save & Run All (Commit)** → **Save**. Tarayıcıyı kapatabilirsin.
4. Durumu izle: sol menü → **Code** → **Your Work** → defter → **Versions**. Durum „Running“den „Succeeded“ ya da „Error“a geçer.
5. Bitince (başarılı ya da hatalı) sürümün sayfası → **Output** → `outputs/` içindeki bütün dosyaları indir ve Bölüm 5'teki bağlantıyla yükle:
   - `log_smoke.txt`: her durumda oluşur; süreler, GPU belleği, varsa hatanın tam metni, üretilen yorumlar.
   - `baseline_*.jsonl`: üretilen yorumlar.
   Output boşsa sürüm sayfasındaki **Logs** bölümünün son satırlarının ekran görüntüsünü gönder.

## 4. Tam koşu (benim onayımdan sonra)

1. Parametre hücresinde `MODE = "smoke"` → `MODE = "full"`.
2. Sağ üst → **Save Version** → **Save & Run All (Commit)** → **Save**.
   - Kaggle defteri arka planda çalıştırır; tarayıcıyı kapatabilirsin. Bir oturum en fazla 12 saat sürer.
   - Haftalık GPU kotası ~30 saat; kalan kotayı profil → **Settings** altında görürsün.
3. Durum: defterin sayfası → **Versions**. Çalışan sürüm „Running“, biten „Succeeded“ olur.

Süre, deneme koşusundaki hıza bağlı; tahmini ben deneme sonucundan sonra veririm. Koşu 12 saati aşacaksa varyantları ayrı koşulara bölerim.

## 5. Çıktıları repoya yükle

1. Biten sürümün sayfası → **Output** → `outputs/` içindeki dosyaları (`log_*.txt`, `baseline_*.jsonl`) indir.
2. Bu bağlantıyla yükle: https://github.com/nberk16/REGU-AI---BWA-LLM/upload/claude/repodaki-project-analysis-al4o1f/gpu
3. Altta „Commit directly to the `claude/repodaki-project-analysis-al4o1f` branch“ seçili olmalı → **Commit changes** → sayfanın üstünde „Add files via upload“ yazısını gör.

## Sorun giderme

| Durum | Ne yapmalı |
|---|---|
| `… bulunamadı. Sağ panel → Input → Add Input …` | Veri seti defterin girdisi değil (Bölüm 1.5 ve 2.4). Hata satırı `/kaggle/input` içinde görüleni de yazar; onu bana gönder |
| `pip` hücresinde ağ hatası | **Internet: On** olmalı (Bölüm 2.3) |
| `CUDA out of memory` ve defter durdu | Hatanın son satırlarını gönder; parti boyutunu düşürürüm |
| `bellek yetmedi; parti boyutu → …` satırı | Hata değil; defter partiyi küçültüp devam eder |
| Oturum kapandı ya da 12 saat doldu | Aynı defteri yeniden çalıştır; biten aylar `outputs/` içinde korunmaz. Bu durumda bana haber ver, koşuyu bölerim |
