# Kaggle adımları (GPU)

Bu klasördekiler Kaggle'da (ücretsiz T4 GPU) çalışır. Kod ve veriyi ben hazırlıyorum, sen Kaggle'da çalıştırıp çıktıları repoya yüklüyorsun. Anahtar ya da şifre gerekmiyor.

- **Veri:** `gpu/data/*.jsonl.gz` (repoda; `python -m training` üretir, `docs/12_egitim_verisi.md`).
- **Defterler:**
  - `01_baseline.ipynb`: ince ayar öncesi model (çıplak model, yalnızca RAG, bütün notlarla RAG). Ollama ile çalışır; deneme turundaki model ve nicemleme (`docs/12`, Bölüm 4).
  - Sonrakiler: ince ayar (yalnızca FT, RAG + FT) ve değerlendirme.
- **Önceki koşuların çıktıları:** `gpu/outputs/`.

---

## 1. Veri setini Kaggle'a yükle (bir kez)

1. Repoyu ZIP olarak indir: bu bağlantıya tıklamak indirmeyi doğrudan başlatır. Sonra ZIP'i çıkart.
   https://github.com/nberk16/REGU-AI---BWA-LLM/archive/refs/heads/claude/repodaki-project-analysis-al4o1f.zip
2. **En kolay yol, defterin içinden:** Sağ panel → **Input** → **Upload** → **New Dataset**.
   - **Başka yol:** sol menü → **Datasets** → **New Dataset**. Bu durumda Bölüm 2.4'te veri setini ayrıca eklersin.
3. Çıkarttığın klasörde `gpu/data/` içindeki **7 dosyayı** (`.jsonl.gz`) sürükle. Kaggle bunları kendiliğinden açabilir (`.jsonl`); defter iki biçimi de okur.
4. Başlık: `bwa-kommentar-daten`. Görünürlük: **Private**. **Create**.
5. Sağ paneldeki **Input** altında `bwa-kommentar-daten` görünmeli. Yalnızca defterin adı görünüyorsa veri seti eklenmemiştir.

Veri değişirse aynı veri setine yeni sürüm yüklenir: veri setinin sayfası → **New Version**. Bunu ayrıca söyleyeceğim. **23.10'daki defter değişikliğinde veri değişmedi;** veri setin olduğu gibi kalır.

## 2. Defteri aç

1. Kaggle'da sol menü → **Code** → **New Notebook**.
2. Üst menü → **File** → **Import Notebook** → `gpu/01_baseline.ipynb` dosyasını seç → **Import**.
3. Sağ panelde **Session options**:
   - **Accelerator:** `GPU T4 x2`. Defter iki GPU'yu da kullanır; her birinde ayrı bir Ollama sunucusu çalışır.
   - **Internet:** **On**. Ollama ve model internetten indirilir. Kapalıysa ayarlar menüsünden telefon doğrulaması gerekir; sende yapıldı.
4. Sağ panelde **Input** → **Add Input** → **Your Datasets** → `bwa-kommentar-daten` → **Add**.

## 3. Deneme koşusu (smoke test, arka planda ~15–30 dakika)

Etkileşimli oturum başında kimse yokken kapanabilir. Bu yüzden deneme koşusu da arka planda yapılır.

1. Defter güncel olmalı: GitHub'dan en son `gpu/01_baseline.ipynb` dosyasını indir (**Download raw file**), sonra Kaggle'da **File** → **Import Notebook**. İlk hücrenin başlığında „Çalıştırıcı: Ollama“ yazmalı.
2. **Session options** (Bölüm 2.3) ve **Input** (Bölüm 1.5) yerinde olmalı. Parametre hücresinde `MODE = "smoke"` kalsın.
3. Sağ üst → **Save Version** → **Save & Run All (Commit)** → **Save**. Tarayıcıyı kapatabilirsin.
4. Durumu izle: sol menü → **Code** → **Your Work** → defter → **Versions**. Durum „Running“den „Succeeded“ ya da „Error“a geçer.
5. Bitince (başarılı ya da hatalı) **`ergebnisse_smoke.zip`** dosyasını indir ve yükle (Bölüm 5). Çıktılar düzenleyicide değil, sürümün görüntüleme sayfasında.
   - Zip'te her şey var: `log_smoke.txt` (süreler, GPU belleği, varsa hatanın tam metni, örnek yorumlar), `baseline_*.jsonl`, Ollama günlükleri.
   - Hata erken çıktıysa zip oluşmamış olabilir. O zaman `outputs/` içindeki `log_smoke.txt` dosyasını yükle.
   - Output boşsa sürüm sayfasındaki **Logs** bölümünün son satırlarının ekran görüntüsünü gönder.

Deneme koşusu varyant başına 8 istem çalıştırır ve günlüğün sonuna tam koşunun tahmini süresini yazar („Tahmin: tam koşu … saat“).

## 4. Tam koşu (benim onayımdan sonra)

Üç varyant × 720 istem; deneme koşusu 2'ye göre tahmini süre **2–3 saat** (tek oturum).

1. Defteri güncelle: GitHub'dan en son `gpu/01_baseline.ipynb` dosyasını indir → Kaggle'da **File** → **Import Notebook**. Parametre hücresinde `VARIANTS` satırında üç varyant görünmeli (`rag_alle` dahil). Dokunma.
2. Parametre hücresinde `MODE = "smoke"` → `MODE = "full"`.
3. **Session options** ve **Input** yerinde olmalı (Bölüm 2.3 ve 1.5). Önceki sürümün çıktısı Input'ta duruyorsa sorun değil: defter yalnızca aynı model ve ayarlarla üretilmiş kayıtları alır.
4. Sağ üst → **Save Version** → **Save & Run All (Commit)** → **Save**.
   - Kaggle defteri arka planda çalıştırır; tarayıcıyı kapatabilirsin. Bir oturum en fazla 12 saat sürer. Defter 11 saatte yeni istem almayı bırakır ve çıktıları paketler.
   - Haftalık GPU kotası ~30 saat; kalan kotayı profil → **Settings** altında görürsün.
5. Durum: defterin sayfası → **Versions**. Çalışan sürüm „Running“, biten „Succeeded“ olur.
6. Bitince `ergebnisse_full.zip` dosyasını indir ve yükle (Bölüm 5). Zip'i açmadan yüklemen de olur, açarak yüklemen de.

**Süre yetmezse (günlükte „süre doldu, … istem kaldı“):**
1. Defteri aç → sağ panel → **Input** → **Add Input** → **Notebooks** (ya da **Your Work**) → bu defterin kendisi → **Add**. Böylece önceki sürümün çıktısı girdi olur.
2. Yeniden **Save & Run All (Commit)**. Defter önceki çıktıdaki kayıtları alır ve yalnızca kalan istemleri çalıştırır.

Kaggle arayüzündeki adlar biraz farklı olabilir; bulamazsan ekran görüntüsü gönder.

## 5. Çıktıları repoya yükle

**Önemli:** Defter düzenleyicisinin sağ panelindeki **Output → /kaggle/working** yalnızca o anki etkileşimli oturumun dosyalarını gösterir. Arka planda (Commit) çalışan sürümün çıktıları orada **görünmez**; sürümün kendi sayfasındadır.

1. Sürümün sayfasını aç:
   - **Yol 1:** Kaggle ana sayfası → sol menü → **Code** → **Your Work** → defterin adı. Bu, düzenleyici değil, defterin görüntüleme sayfasıdır.
   - **Yol 2:** Düzenleyicide sağ üstteki sürüm sayısına ya da **Save Version** yanındaki geçmiş simgesine tıkla → sürüm listesi → biten sürüm → **Open in Viewer** (adlar biraz farklı olabilir).
2. Görüntüleme sayfasının üstünde sekmeler var: **Notebook · Input · Output · Logs · …**. Sürümün „Succeeded“ ya da „Error“ olduğunu kontrol et, sonra **Output** sekmesine tıkla.
3. Dosya listesinde `outputs/` → `ergebnisse_<MODE>.zip` → dosyayı seçince sağ üstte çıkan **indirme simgesi** (aşağı ok). Bölümün üstünde bütün çıktıyı tek seferde indiren bir **Download** düğmesi de olabilir; o da olur.
4. İndirdiğin zip'i bu bağlantıyla yükle: https://github.com/nberk16/REGU-AI---BWA-LLM/upload/claude/repodaki-project-analysis-al4o1f/gpu
5. Altta „Commit directly to the `claude/repodaki-project-analysis-al4o1f` branch“ seçili olmalı → **Commit changes** → sayfanın üstünde „Add files via upload“ yazısını gör.

Yükleme olmazsa hangi adımda takıldığını yaz: zip Kaggle'dan inmedi mi, yoksa GitHub sayfası mı hata verdi? Hata mesajı ya da ekran görüntüsü yeterli. Deneme koşusunun günlüğünü yapıştırmak geçici bir çözümdü; tam koşunun dosyaları bunun için çok büyük.

## Sorun giderme

| Durum | Ne yapmalı |
|---|---|
| `… bulunamadı. Sağ panel → Input → Add Input …` | Veri seti defterin girdisi değil (Bölüm 1.5 ve 2.4). Hata satırı `/kaggle/input` içinde görüleni de yazar; onu bana gönder |
| Kurulum hücresinde ağ hatası ya da `curl` hatası | **Internet: On** olmalı (Bölüm 2.3) |
| `OLLAMA HAZIRLANAMADI` | Günlüğü ve `ollama_gpu0.log` dosyasını gönder (ikisi de `outputs/` içinde) |
| `UYARI: model tamamen GPU'da değil` | Hata değil, ama koşu yavaşlar. Accelerator'ın `GPU T4 x2` olduğunu kontrol et; günlüğü gönder |
| `HATA <ay> (…, deneme 1)` | Defter o ayı bir kez daha dener. Çok sayıda görürsen günlüğü gönder |
| `süre doldu, … istem kaldı` | Bölüm 4'teki devam adımları |
| Düzenleyicide Output → `/kaggle/working` boş | Normal: Commit sürümünün çıktıları orada görünmez. Bölüm 5, adım 1–3 |
| Sürüm sayfasında Output sekmesi yok ya da boş | Sürüm hâlâ „Running“ olabilir; bitmesini bekle. Bittiyse **Logs** sekmesinin son satırlarının ekran görüntüsünü gönder |
| Oturum hatayla kapandı | Aynı defteri yeniden çalıştır. Önceki sürümün çıktısı Input olarak eklenirse biten aylar korunur (Bölüm 4) |
