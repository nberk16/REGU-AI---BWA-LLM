# Yol haritası ve proje durumu

> **Bu dosya her adımdan sonra güncellenir** [KARAR, tur 4]. · **Son güncelleme:** 25.10.2026 (iki model eğitildi: RAG + FT 0,834 → 0,130, yalnızca FT 1,013 → 0,106; sırada 03_eval)

---

## 1. Genel durum: ~%93 tamamlandı (toplam iş 51 gün)

**Nasıl hesaplandı?** Yüzde, adım sayısına göre değil tahmini iş yüküne göre hesaplandı:

1. Proje 10 iş paketine bölündü.
2. Her pakete, tek bir geliştiricinin yapay zekâ desteğiyle harcayacağı tahmini **iş günü** verildi.
3. Her paketin tamamlanma oranı kendi iş günüyle çarpıldı ve toplam iş gününe bölündü.

```
tamamlanan iş = Σ (paketin iş günü × tamamlanma oranı) = 47,2 gün
toplam iş     = 51 gün
durum         = 47,2 / 51 ≈ %93
```

**Belirsizlik:**
- Tahminler en çok model tarafındaki paketlerde belirsiz: ideal yorumların üretimi, baseline'lar, fine-tuning, değerlendirme. Bu paketler GPU erişimine, temel modelin Almanca kalitesine ve deneme–yanılma döngülerine bağlı.
- Kullanıcının dizüstünde 4 GB GPU var; eğitim ve değerlendirme bulutta (Kaggle) yapılacak. Defterlerin kullanıcı tarafından çalıştırılması turları uzatabilir.
- Gerçekçi aralık %56–63.
- Kalan işin ~%70'i model tarafında. Bu, G7'deki odakla uyumlu.

---

## 2. İş paketleri

| # | İş paketi | Tahmini iş (gün) | Tamamlanma | Tamamlanan (gün) | Durum |
|---|---|---:|---:|---:|---|
| 1 | Problem tanımı, tasarım ve kararlar | 3 | %100 | 3,0 | ✅ tamamlandı |
| 2 | Veri üreteci (+ dengelenmiş V2 kümesi, eğitim profili) | 5 | %100 | 5,0 | ✅ tamamlandı |
| 3 | Hesaplama modülü (Katman 1, `facts.json`) | 5 | %90 | 4,5 | ✅ tamamlandı (ince ayar kaldı) |
| 4 | Bilgi tabanı ve retrieval (Katman 2) | 6 | %90 | 5,4 | ✅ v1, ölçüm, istemle bütünleşme; katkısı ablation'da ölçüldü |
| 5 | İdeal yorumların üretimi (eğitim hedefleri; tur 12'den beri bağlamsız hedefler dahil) | 9 | %100 | 9,0 | ✅ tamamlandı: öğretmen metinleri, altın küme, eğitim verisi |
| 6 | Model seçimi, çıkarım altyapısı, baseline'lar (çıplak model, yalnızca RAG) | 5 | %100 | 5,0 | ✅ tamamlandı: 3 varyant × 720 ay, puanlandı |
| 7 | Fine-tuning (LoRA): yalnızca FT ve RAG + FT | 6 | %100 | 6,0 | ✅ iki model eğitildi (doğrulama kaybı 0,834 → 0,130 ve 1,013 → 0,106) |
| 8 | Doğrulama katmanı (Katman 4) | 3 | %90 | 2,7 | 🔄 v1.8 |
| 9 | Değerlendirme ve ablation | 6 | %90 | 5,4 | ✅ ablation tamam (`docs/13`, Bölüm 6); V2 kümesi koşulmuyor (tur 13); üslup [AÇIK] |
| 10 | Portfolyo dokümantasyonu ve yayın | 3 | %40 | 1,2 | 🔄 model Hugging Face'te yayında; anlatı, README ve demo kaldı |
| | **Toplam** | **51** | | **47,2** | **≈ %93** |

---

## 3. Paket ayrıntıları ve açık kararlar

### 1. Problem tanımı, tasarım ve kararlar — ✅ tamamlandı
- **Yapılan:** Firma arketipleri, BWA satır yapısı, olay kataloğu, karar turları 1–4 (`docs/00`–`03`).
- **Açık kararlar:** Yok. Paketlere özgü açık kararlar aşağıda.

### 2. Veri üreteci — ✅ tamamlandı
- **Yapılan:**
  - `generator/` ve 35 test.
  - Referans koşu: `data/synthetic/reference_seed42/`.
  - Dengelenmiş V2 kümesi: `data/synthetic/v2_balanced_seed4242/`.
  - Eğitim profili: `train_price_boost`.
  - E18 kalibrasyonu (tur 5).
  - Ayrıntılar `docs/04`'te.
- **Açık kararlar:** Yok.

### 3. Hesaplama modülü (Katman 1) — ✅ tamamlandı (ince ayar kaldı)
- **Yapılan:**
  - `facts.json` şeması 1.0 onaylandı ve kodlandı (`facts/`, 15 test).
  - Referans veride medyan 3 anlamlı kalem; ayların %4,3'ünde 0, %3,6'sında 5'ten fazla.
  - Bayrak isabeti ölçüldü (`tools/flag_quality.py`, `docs/05` Bölüm 7).
  - Rohertrag adayı kuralının üreteçle aynı çalıştığı testle doğrulandı.
- **V6 düzeltmesi (19.10.2026):** Önceki yıla göre değişim ters yönde ya da en fazla yarı büyüklükte olmalı; precision %72 → %78, recall %63 → %58 (`docs/05`, Bölüm 7).
- **Kalan (%10):** Bayrak parametrelerinin ince ayarı. Gerekirse model sonuçlarına göre yapılır; ör. V4 ve V6 recall'ı (%58–61).
- **Açık kararlar:** Bayrak parametreleri [ÖNERİ] (`facts/config.toml`).

### 4. Bilgi tabanı ve retrieval (Katman 2) — ✅ v1 (ayar kaldı)
- **Yapılan (`rag/`, `docs/09`):**
  - Almanca K-A (34) ve K-B (10) metinleri; rakamsız, SKR03'süz.
  - BGE-M3 + Chroma deposu.
  - K-A/K-B anahtarla, K-C 13 ay + top-k ile getiriliyor; Firmenprofil hep ekleniyor.
  - CLI, `retrieval.jsonl` dışa aktarma, getirme isabeti aracı, 10 test.
- **Kararlaştırılan (tur 10):** SKR03 aralıkları hiç eklenmez; K-E kapsam dışı.
- **Ölçüm (18.10.2026):** Doğrulama varyantlarında `single` + top-8 seçildi. Test kümesinde recall %91,4 (çekirdek) / %83,3 (geniş); çeldirici payı %5,2, bütün notlarda %11,3 (`docs/09`, Bölüm 5).
- **İstemle bütünleşme (18.10.2026):** İstem 1.1 bağlamı „WISSEN“ (K-B, K-A) ve „KONTEXTNOTIZEN“ olarak taşıyor; doğrulama K-A/K-B kimliklerini tanıyor (`docs/10`). `rag export --firms` eklendi.
- **Ablation (26.10.2026):** Recall@8 test istemlerinden yeniden ölçüldü (%91,4 / %83,2). Top-8, bütün notlardan biraz daha iyi: RAG + FT'de kaynak recall %59'a karşı %55 (`docs/13`, 6.4).
- **Kalan (%10):**
  - Model sonuçlarına göre ayar (ör. k, K-A/K-B metinleri).
  - K-D deneyi (isteğe bağlı, tur 6'ya göre sonra).
- **Açık kararlar:** Yok. Sorgu yöntemi ölçümle seçildi (`single`, [ÖNERİ]).

### 5. İdeal yorumların üretimi — ✅ tamamlandı
- **Yapılan (`ideal/`, `docs/11`):**
  - İçerik planı: `effects.csv` ile kaynaklı neden, hipotez ya da „Ursache offen“; yalnızca öğrencinin gördüğü notlar kaynak.
  - Öğretmen istemi (Almanca, 10 kural).
  - Kontrol: doğrulama katmanı + plana uygunluk.
  - Dizüstü betiği (Mistral API; kontrol ve yeniden deneme dizüstünde), kullanıcı kılavuzu `ideal/README.md`.
  - İstek dosyaları: pilot 24, eğitim 960, doğrulama 144 ay. 8 test.
  - Kalıp metinler 1.104 ayın hepsinde kontrolü geçiyor (plan ↔ doğrulama tutarlı).
- **Kararlaştırılan:**
  - Turlar 6–7: karma yöntem, altın küme, B3, 6.3.
  - Tur 11: öğretmen Mistral Large 3, anahtar yalnızca kullanıcının bilgisayarında.
- **Pilot 1 (19.10.2026):** 24 ayın 9'u kabul (%38). Nedenler ve düzeltmeler `docs/11`, Bölüm 10: öğretmen istemi 1.1, cümle bazında geri bildirim, plan 1.1, doğrulama v1.4.
- **Pilot 2 (19.10.2026):** Kabul %88, ama okumada içerik sorunları çıktı. Öğretmen 1.2, plan 1.2, içerik kontrolleri, doğrulama v1.5 (`docs/11`, Bölüm 11).
- **Pilot 3 (19.10.2026):** Kabul %92, içerik büyük ölçüde temiz; Kernaussage'lerde neden eksikti → öğretmen 1.3, plan 1.3, doğrulama v1.6 (`docs/11`, Bölüm 12).
- **Doğrulama kümesi (19.10.2026):** 144 ayın 132'si kabul (%92); okumada içerik temiz (`docs/11`, Bölüm 13).
- **Eğitim kümesi ve yeniden deneme (19.10.2026):** eğitim 908/960 (%95), doğrulama 138/144 (%96). Metinlerin ~%5'inde bir cümlelik plan dışı yorum; rakam ve kaynak sadakati etkilenmiyor (`docs/11`, Bölüm 14).
- **Karar turu 12 (19.10.2026):** „Yalnızca FT“ için bağlamsız hedefler (B): `train_ohne` 960 + `val_ohne` 144 ay. Okumada iki düzeltme: V6 bayrağı (Katman 1) ve eşit etkili kaynakların sırası. Girdisi değişen 96 ay yeniden üretilecek; betik bunları parmak iziyle (`input_sha`) kendisi bulur (`docs/11`, Bölüm 15).
- **Düzeltme sonrası (20.10.2026):** Eğitim 901/960 (yeniden üretilen 87 ayın 80'i kabul). `val_ohne` 134/144; kaynak ve uydurma neden izi yok (`docs/11`, Bölüm 16).
- **`train_ohne` ve plan 1.4 (21.10.2026):** `train_ohne` 923/960. Okumada taban hipotezinin yönünde sistematik hata bulundu; plan 1.4 düzeltiyor, girdisi değişen 555 ay yeniden üretilecek (`docs/11`, Bölüm 17).
- **Öğretmen aşaması tamam (22.10.2026):** `train` 907/960, `val` 138/144, `train_ohne` 940/960, `val_ohne` 142/144; taramalar temiz (`docs/11`, Bölüm 18).
- **Altın küme ve eğitim verisi (22.10.2026, `docs/12`):**
  - Altın küme 30 metin; baskın kusur, uyarı Kernaussage'sinde eksik uyarı dili (~%40) → eğitim verisinde otomatik tamamlanıyor.
  - Eğitim verisi: `train_rag` 898, `train_ohne` 933 örnek (+ doğrulama 133 / 140).
  - Plan 1.5 / öğretmen 1.4: karışık zamanlı kaynaklar; 8 ay dışarıda.
- **İsteğe bağlı:** Dışarıda kalan 8 ayın kısa bir öğretmen koşusuyla geri alınması.
- **Açık kararlar:** Yok. Plan parametreleri, üretim ayarları ve veri temizliği (`docs/11`, Bölüm 14) [ÖNERİ].

### 6. Model seçimi, çıkarım altyapısı, baseline'lar — ✅ tamamlandı
- **Yapılan:**
  - Ortak istem modülü `prompting/` (sürüm 1.0).
  - Deneme turu kiti `trial/`: doğrulama varyantlarından 10 örnek, Ollama betiği, puanlama, kullanıcı kılavuzu, 4 test.
  - Ayrıntılar `docs/08`.
- **Deneme turu tamamlandı (17.10.2026):**
  - 3 model × 10 örnek; puanlama ve okuma: `trial/results.md`.
  - Ministral açık ara en zayıfı. Öneri Gemma 4 E4B, yedek Qwen3.5 9B.
- **Kararlaştırılan (tur 9):** Temel model Gemma 4 E4B, yedek Qwen3.5 9B.
- **İstem 1.1 (18.10.2026, `docs/10`):**
  - Katman 2 bağlamı (WISSEN + top-8 not) ve deneme turu dersleri 8 kurala işlendi.
  - Varyantlar: `ohne_kontext`, `rag_k8`, `rag_alle`; sistem mesajı hepsinde aynı.
  - `python -m prompting` istemleri Kaggle için JSONL olarak yazıyor; 7 test.
  - İstem 1.0 deneme turu için donduruldu.
- **Kaggle hazırlığı (22.10.2026, `docs/12`, Bölüm 2 ve 4):**
  - Test istemleri: 3 varyant × 720 ay.
  - `gpu/01_baseline.ipynb`: Unsloth, 4-bit, deneme turu ayarları. Sahte modelle denendi.
  - Kullanıcı kılavuzu `gpu/README.md`.
- **Deneme koşusu 1 (23.10.2026, `docs/12`, Bölüm 4):**
  - Transformers + Unsloth yolu tek T4'te 5 token/s verdi; parti boyutu bellekten 1'e düştü. Tam koşu ~60 saat sürerdi.
  - Defter Ollama'ya geçti (`gemma4:e4b-it-q4_K_M`, deneme turuyla aynı): iki T4, GPU başına 4 eşzamanlı istem, süre sınırı, önceki çıktıdan devam, tek zip. Sahte sunucuyla denendi.
  - Dört metnin ilk okuması: rakam değerleri doğru; biçim, yön ve kaynak hataları var (beklenen baseline zayıflıkları).
- **Deneme koşusu 2 (23.10.2026, `docs/12`, Bölüm 4.4):**
  - Ollama, iki T4, 16 istem, hata yok.
  - Akış başına 37–52 token/s; tam koşu tahmini 2 varyant için ~1,8 saat.
  - `rag_alle` de baseline'a eklendi [ÖNERİ].
  - İlk ölçüm (16 metin): rakam değerleri %96–97 doğru. Görülen sorunlar:
    - biçim hataları (binlik boşluk, kaynak biçimi);
    - hiç „(Hypothese)“ yok;
    - eksik bayrak uyarıları;
    - metinler kısa.
- **Tam koşu (24.10.2026):**
  - 3 varyant × 720 ay, hata yok, ~2 saat; çıktılar `gpu/outputs/baseline_2026-10-24/`.
  - Puanlar `docs/13`, Bölüm 4.
- **Kalan:** Yok. İsteğe bağlı: Gemma ile istem 1.1 ön kontrolü artık gereksiz (baseline bunu kapsıyor).
  - Çıktıların puanlanması.
  - İsteğe bağlı: aynı 10 örnekte Gemma ile istem 1.1 ön kontrolü (kullanıcının dizüstünde ~1,5 saat; `docs/10`, Bölüm 8).
- **Kararlaştırılan (tur 6):** Deneme turu adayları Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B. Deneme turu kullanıcının dizüstünde (Ollama) yapılabilir.
- **Kararlaştırılan (tur 7):** Değerlendirme Kaggle'da; deneme turu örnekleri doğrulama varyantlarından.
- **Açık kararlar:** Çıkarım altyapısı [ÖNERİ, 23.10.2026: baseline, değerlendirme ve demo Ollama (llama.cpp, Q4_K_M); ince ayarlı modeller GGUF'a aktarılır (`docs/00`, Bölüm 21)].

### 7. Fine-tuning (LoRA) — ✅ tamamlandı
- **Yapılan (24.10.2026, `docs/14`):**
  - `gpu/02_finetune.ipynb`: QLoRA, kayıp yalnızca yanıtta, şablon/maske denetimleri, doğrulama kaybı öncesi ve sonrası.
  - Hız ölçümü (smoke), checkpoint ve süre sınırıyla devam, bağdaştırıcı → GGUF → llama-server denemesi.
  - Bulgu: Ollama 0.40 LoRA desteklemiyor; çıkarım Ollama'nın içindeki llama-server ile (yerelde doğrulandı).
- **Deneme koşuları (24.10.2026, `docs/14`, Bölüm 2):**
  - 1: eksik BOS maske denetiminde yakalandı.
  - 2: bellek yetmedi.
  - 3: başarılı. Katman başına gömme tablosu ve ses/görüntü kodlayıcıları işlemcide; en yüksek bellek 11,6 GB; 140 token/s; doğrulama kaybı 3 adımda 0,786 → 0,635; tahmini süre `rag` ~10 saat, `ohne` ~7,6 saat.
- **RAG + FT tam eğitimi (25.10.2026, `docs/14`, Bölüm 2.1):**
  - 113 adım, 7,8 saat, en yüksek bellek 11,6 GB.
  - Doğrulama kaybı 0,834 → 0,130.
  - Deneme üretiminde format, hipotez işareti ve V2 uyarısı doğru. İki rakam hatası var; ikisini de doğrulama katmanı yakalıyor.
- **Yalnızca FT tam eğitimi (25.10.2026, `docs/14`, Bölüm 2.2):**
  - 117 adım, 5,6 saat, en yüksek bellek 9,8 GB.
  - Doğrulama kaybı 1,013 → 0,106.
  - Deneme üretimi hatasız; ideal metinle aynı profil.
- **Kalan:** Yok. Değerlendirme paket 9'da (03_eval).
  - Eğitim kayıtlarının okunması (kayıp eğrileri).
- **Kararlaştırılan (tur 7):** Donanım: Kaggle (ücretsiz T4); dizüstünün 4 GB GPU'su eğitime yetmiyor. Eğitim verisi: 960 ay.
- **Açık kararlar:**
  - Fine-tuning araç seti [ÖNERİ: Unsloth + TRL, QLoRA].
  - Hiperparametreler [ÖNERİ, `docs/14`, Bölüm 2].
  - Çıkarım yolu [ÖNERİ, `docs/14`, Bölüm 3]: llama-server + LoRA.
  - **Olası karar (hız ölçümünden sonra):** Unsloth, T4'te Gemma 4 için float32'ye geçiyor; eğitim yavaş olabilir. İnce ayar defteri önce kısa bir hız ölçümü yapar. Çok yavaşsa seçenekler kullanıcıya sunulur: daha kısa eğitim, Gemma 4 E2B, Qwen3.5 9B (tur 9) ya da kiralık GPU (tur 7).
- **Kararlaştırılan (tur 12):** „Yalnızca fine-tuning“ varyantı bağlamsız girdilerle ayrı bir model olarak eğitilir (B). RAG + FT modelinin bağlamsız çalıştırılması ek satır olarak raporlanır (`docs/00`, Bölüm 19).

### 8. Doğrulama katmanı (Katman 4) — 🔄 v1.7
- **Yapılan:**
  - `validation/` ve 46 test; kurallar `docs/07`.
  - Almanca rakam ayıklama ve yuvarlama kuralı (a).
  - Birim uyumu, işaret, "rakam hangi satıra ait".
  - Not istisnası (kaynak şartı).
  - Neden cümlelerinde kaynak/hipotez işareti.
  - Format (6.3), kapsam ipuçları, JSON raporu, CLI.
  - Örnek yorum: `docs/examples/kommentar_A1-v00_2025-06.md`.
  - Referans verinin 720 ayında yanlış alarm yok.
- **v1.3 (18.10.2026):** K-A/K-B kimlikleri tanınıyor (`quelle_wissen`, kaynak sayılmaz); CLI'de `--retrieval` (`docs/07`, Bölüm 12). 56 test.
- **Kalan (%20):**
  - Baseline çıktılarına göre kelime listelerinin ve kuralların ayarı.
  - ~~Rakam biçimi: binlik ayırıcı boşluk~~ ✅ v1.7 (24.10.2026): tek rakam olarak okunur, `zahlenformat` biçim hatası (`docs/07`, Bölüm 13).
  - ~~„geht auf + rakam“ yanlış alarmı~~ ✅ v1.8 (26.10.2026): düşüş cümlesi neden sayılmıyor (`docs/07`, Bölüm 14).
  - Karşılaştırma sözcüğü yön hataları („über“ yerine „unter“) denetlenmiyor; gerekirse tam koşudan sonra.
  - v2 adayı: karşılaştırma etiketi kontrolü („Vj.“ değeri gerçekten önceki yılın aynı ayı mı?).
- **Kararlaştırılan (tur 8):** Yuvarlama kuralı (a).
- **Açık kararlar:** Yok. Parametreler [ÖNERİ] (`validation/config.toml`).

### 9. Değerlendirme ve ablation — 🔄 ablation tamam
- **Hazır olan:**
  - Ground truth: olaylar, ay kayıtları, kabul edilebilir uyarılar, V2 kararı.
  - Dengelenmiş V2 kümesi.
  - Metrik tanımları (CLAUDE.md 8).
  - Bayrak isabeti aracı (`tools/flag_quality.py`; eşik üstü süzme dahil).
- **Puanlama 1.0 (24.10.2026, `scoring/`, `docs/13`):**
  - CLAUDE.md 8'deki ölçütler kodlandı; üç kaynak: doğrulama, içerik planı, ground truth. 8 test.
  - Kalibrasyon: ideal metinler plana dayalı ölçütlerde %100.
  - Baseline: rakam değeri %93–95; format %30–39; RAG'de nedenlerin %42'si işaretsiz; kaynak precision %54, recall %30–34.
- **Değerlendirme defteri (24.10.2026):** `gpu/03_eval.ipynb`; 5 koşu (RAG + FT, yalnızca FT, iki ek satır, taban modelle tutarlılık kontrolü). Yerelde sahte bağdaştırıcıyla uçtan uca denendi.
- **Deneme koşusu (26.10.2026, `docs/14`, 4.1):**
  - 5 × 8 metin (A1), hata yok; tam koşu ~4,5 saat.
  - İnce ayarlı sistemlerde format %100. Yalnızca FT 8/8 hatasız.
  - RAG + FT kaynak recall %50 (baseline %27); zayıf nokta notu yanlış satıra bağlamak.
- **Puanlama 1.1 (26.10.2026):** satır düzeyinde atıf ölçütü (baseline %37–38 doğru satırda); birden çok klasörle ablation tablosu. 10 test.
- **Ablation (26.10.2026, `docs/13`, Bölüm 6):**
  - 5 sistem × 720 ay, 4,3 saat; baseline ile birlikte puanlandı.
  - Çıplak / yalnızca RAG / yalnızca FT / RAG + FT:
    - format %39 / %30 / %100 / %97;
    - işaretsiz neden 0,16 / 1,01 / 0 / 0,06 metin başına;
    - kaynak precision/recall – / %54 / %34 → %75 / %59.
  - Yeni sektörde (A1) aynı düzey. Retrieval isabeti tabloda.
  - Zayıf noktalar: V2'de notla açıklanacak aylar (1/17; eğitimde bu karar %5) ve metinlerin %26'sında notun yanlış satıra bağlanması.
- **Kararlaştırılan (tur 13):** Dengelenmiş V2 kümesi şimdilik koşulmuyor, ikinci eğitim turu yok. V2 zayıflığı bilinen sınır olarak raporlanıyor.
- **Kalan:**
  - Sonuç anlatısı (paket 10 ile birlikte).
- **Açık kararlar:**
  - Üslup değerlendirmesi: insan mı, LLM-as-judge mı? (CLAUDE.md 8)
  - Retrieval isabeti (recall@k) metriği eklendi (tur 6).
- **Kararlaştırılan (tur 7):** Test: yeni sektör (A1, öğretilmemiş tür) + yeni firma (A2/A3'ün görülmemiş varyantları, öğretilmiş tür) + dengelenmiş V2 kümesi (`docs/04`, Bölüm 9.2).
  - `expected_flags`'in anlamlılık eşiğine göre süzülmesi.

### 10. Portfolyo dokümantasyonu ve yayın — 🔄 model yayında
- **Hazır olan:**
  - Tasarım belgeleri (`docs/`).
  - **Hugging Face yayını (tur 13):**
    - Model kartı (İngilizce), örnek istem ve çıktı, istek betiği: `release/huggingface/`.
    - Yükleme adımları: `gpu/README.md`, Bölüm 8.
    - Yalnızca RAG + FT modeli yayınlanıyor; depo şimdilik gizli.
    - **Yayında (26.10.2026):** https://huggingface.co/nberkc16/bwa-kommentar-gemma4-e4b-lora. Dosyalar doğrulandı: GGUF SHA256 eğitimdekiyle aynı, safetensors 516 tensör.
- **Kalan:**
  - README.
  - Problem → çözüm → kanıt (ablation) anlatısı.
  - Örnek çıktılar (Muster GmbH'nin toparlanma hikâyesi).
  - Görseller.
- **Açık kararlar:** Formatı (README, rapor, demo defteri?).

---

## 4. Sıradaki adımlar

Model tarafının ana işi tamam: baseline'lar, iki ince ayar, ablation (26.10.2026). Önerilen sıra:

1. ~~Hugging Face yayını~~ ✅ https://huggingface.co/nberkc16/bwa-kommentar-gemma4-e4b-lora.
2. **Paket 10, devam:**
   - README;
   - problem → çözüm → kanıt anlatısı;
   - örnek çıktılar;
   - dizüstü demosu (llama-server + LoRA).
3. **[AÇIK] Üslup değerlendirmesi.**
4. ~~Dengelenmiş V2 kümesi, ikinci eğitim turu~~: yapılmıyor (tur 13).

## 5. Değişiklik geçmişi

| Tarih | Değişiklik |
|---|---|
| 15.10.2026 | İlk sürüm (karar turu 4 sonrası): %21 |
| 15.10.2026 | Karar turu 5: E18 kalibrasyonu, Katman 1 (şema 1.0) kodlandı, bayrak isabeti ölçüldü: %28 |
| 15.10.2026 | Model tarafı seçenekleri sunuldu (`06_model_tarafi_secenekler.md`); durum değişmedi: %28 |
| 15.10.2026 | Karar turu 6: deneme turu adayları, çıktı yapısı, notsuz neden kuralı, bilgi tabanı (BGE-M3, Chroma, top-k, K-D kapalı). Paket 4 → %10, 5 → %5, 6 → %5: %30 |
| 15.10.2026 | Karar turu 7: test tasarımı (A1 + görülmemiş varyantlar), 20 + 3 varyant, Kaggle, karma yöntem, açık ağırlıklı öğretmen. Paket 5 → %10, 9 → %20: %32 |
| 15.10.2026 | Karar turu 8: yuvarlama kuralı (a); doğrulama katmanı v1 kodlandı (`validation/`, 46 test). Paket 8 → %70: %36 |
| 15.10.2026 | Deneme turu kiti: `prompting/` (istem 1.0), `trial/` (10 örnek, Ollama betiği, puanlama, kılavuz), `docs/08`. Paket 6 → %25: %38 |
| 17.10.2026 | `trial/README.md`: indirme adımları netleştirildi (doğrudan ZIP bağlantısı, dal açıklaması); durum değişmedi: %38 |
| 17.10.2026 | `trial/README.md`: ZIP'i çıkartma ve PowerShell'i klasörde açma adımları eklendi; durum değişmedi: %38 |
| 17.10.2026 | `trial/run_ollama.py` Python 3.8 uyumlu yapıldı (kullanıcının bilgisayarı); durum değişmedi: %38 |
| 17.10.2026 | `trial/run_ollama.py`: sonuç ekrana yazılmadan önce dosyaya kaydediliyor (Windows QuickEdit donması); kılavuza sorun giderme satırı; durum değişmedi: %38 |
| 17.10.2026 | Deneme turu: hızlı deneme (3 model × 1 örnek) tamamlandı; doğrulama katmanı v1.1 (biçimsel toleranslar, kaynak gösterimi; 53 test); puanlama tablosu biçim/içerik ayrımıyla. Paket 8 → %75: %38 |
| 17.10.2026 | Deneme turu tamamlandı (3 model × 10 örnek); puanlama + okuma (`trial/results.md`); doğrulama v1.2. Paket 6 → %40: %39 |
| 17.10.2026 | Karar turu 9: temel model Gemma 4 E4B (yedek Qwen3.5 9B); E04/E05 not kalıpları netleştirildi, veri kümeleri yeniden üretildi (yalnızca not metinleri). Paket 6 → %45: %40 |
| 17.10.2026 | Karar turu 10: SKR03 yok, K-E kapsam dışı. Bilgi tabanı v1 (`rag/`: K-A/K-B metinleri, BGE-M3 + Chroma, getirme, 10 test). Paket 4 → %55: %45 |
| 18.10.2026 | Getirme isabeti ölçüldü (BGE-M3): sorgu yöntemi doğrulama varyantlarında seçildi (`single`, k = 8); test kümesinde recall %91 / %83, çeldirici payı %11 → %5. Paket 4 → %70: %47 |
| 18.10.2026 | İstem 1.1 (`prompting/`, `docs/10`): Katman 2 bağlamı (WISSEN + top-8), deneme turu dersleri, varyantlar, Kaggle için istem dışa aktarma; istem 1.0 donduruldu. Doğrulama v1.3 (K-A/K-B kimlikleri). Paket 4 → %85, 6 → %55, 8 → %80: %50 |
| 18.10.2026 | Karar turu 11: öğretmen Mistral Large 3 (API), anahtar yalnızca kullanıcının bilgisayarında. İdeal yorum hattı (`ideal/`, `docs/11`): içerik planı, öğretmen istemi, kontrol, dizüstü betiği, istek dosyaları (24 + 960 + 144 ay), 8 test. Paket 5 → %35: %54 |
| 19.10.2026 | Pilot 1 (öğretmen 1.0): kabul %38; öğretmen istemi 1.1, cümle bazında geri bildirim, daha sıkı tablo/soru kontrolü, plan 1.1, doğrulama v1.4. Durum değişmedi: %54 |
| 19.10.2026 | Pilot 2 (öğretmen 1.1): kabul %88; okumada içerik sorunları → öğretmen 1.2, plan 1.2 (Einordnung), içerik kontrolleri, doğrulama v1.5. Durum değişmedi: %54 |
| 19.10.2026 | Pilot 3 (öğretmen 1.2): kabul %92, içerik büyük ölçüde temiz; Kernaussage neden kontrolü → öğretmen 1.3, plan 1.3, doğrulama v1.6. Paket 5 → %40: %55 |
| 19.10.2026 | Doğrulama kümesi (öğretmen 1.3): 144 ayın 132'si kabul; içerik temiz; `--retry-failed` yeni tohumlarla. Paket 5 → %50: %56 |
| 19.10.2026 | Eğitim kümesi (öğretmen 1.3): 908/960 kabul; yeniden deneme sonrası doğrulama 138/144. Okuma ve tarama: ~%5 metinde plan dışı yan cümle. Paket 5 → %80: %61 |
| 19.10.2026 | Karar turu 12: „yalnızca FT“ için bağlamsız hedefler (B), istek dosyaları `train_ohne`/`val_ohne`. V6 bayrağı ve kaynak sırası düzeltildi; girdisi değişen 96 ay yeniden üretilecek (`input_sha`). Paket 5'in işi 8 → 9 gün, %75; toplam 51 gün: %61 |
| 20.10.2026 | Düzeltilen eğitim ayları üretildi (87 → 80 kabul; toplam 901/960). `val_ohne` 134/144, okumada temiz. Rapor bekleyen ayları gösteriyor. Paket 5 → %78: %61 |
| 21.10.2026 | `train_ohne` 923/960, `val` 138/144, `val_ohne` 139/144. Plan 1.4: taban ve bayrak hipotezlerinde yön tutarlılığı; 555 ay yeniden üretilecek. Betik: geçerlilik parmak iziyle, en fazla bir yeniden deneme. Paket 5 → %80: %62 |
| 22.10.2026 | Plan 1.4 ile 555 ay yeniden üretildi. Öğretmen aşaması tamam: `train` 907/960, `val` 138/144, `train_ohne` 940/960, `val_ohne` 142/144. Paket 5 → %85: %63 |
| 22.10.2026 | Altın küme (30 metin) ve eğitim verisi (`train_rag` 898, `train_ohne` 933); uyarı Kernaussage'si otomatik tamamlama; plan 1.5 / öğretmen 1.4; test istemleri; Kaggle baseline defteri ve kılavuzu. Paket 5 → %100, 6 → %65: %66 |
| 23.10.2026 | Kaggle deneme koşusu 1 (Transformers + Unsloth): hat çalışıyor, ama 5 token/s (tam koşu ~60 saat). Baseline defteri Ollama'ya geçti (iki T4, eşzamanlı istem, devam, zip); dört metnin ilk okuması. Paket 6 → %70: %67 |
| 24.10.2026 | `gpu/README.md`: Commit sürümünün çıktılarının yeri (düzenleyici değil, sürümün görüntüleme sayfası → Output) netleştirildi; durum değişmedi: %67 |
| 24.10.2026 | Kaggle deneme koşusu 2 (Ollama, iki T4): 16 istem, hata yok, 37–52 token/s; tam koşu ~1,8 saat (önce ~60). `rag_alle` baseline'a eklendi; 16 metnin ilk ölçümü. Paket 6 → %75: %67 |
| 24.10.2026 | `gpu/README.md`: Commit koşusunun durumunu ve ilerlemesini izleme adımları (Logs sekmesi, kalan süre satırları); durum değişmedi: %67 |
| 24.10.2026 | Baseline tam koşusu (3 × 720, ~2 saat) ve puanlama 1.0 (`scoring/`, `docs/13`): kalibrasyon ve baseline sonuçları. Doğrulama v1.7 (boşluklu binlik ayırıcı). Paket 6 → %100, 8 → %85, 9 → %45: %73 |
| 24.10.2026 | İnce ayar (`02_finetune`) ve değerlendirme (`03_eval`) defterleri; Ollama 0.40'ın LoRA desteklemediği bulundu, çıkarım llama-server + LoRA ile (yerelde doğrulandı). Paket 7 → %25, 9 → %50: %76 |
| 24.10.2026 | İnce ayar deneme koşusu 1: maske denetimi eksik BOS'u yakaladı (Gemma 4 tokenizer'ı BOS eklemiyor); defter düzeltildi, eğitim başlamadan durdu. Durum değişmedi: %76 |
| 24.10.2026 | İnce ayar deneme koşusu 2: denetimler geçti, ilk adımda bellek yetmedi (7.076 token). Katman başına gömme tablosu (5,6 GB) ve ses/görüntü kodlayıcıları işlemciye taşınıyor; bellek yetmezse kısa örneklerle hız ölçümü. Durum değişmedi: %76 |
| 24.10.2026 | İnce ayar deneme koşusu 3 başarılı: bellek 11,6 GB, 140 token/s, tahmini `rag` ~10 saat, `ohne` ~7,6 saat; doğrulama kaybı 0,786 → 0,635 (3 adım). llama-server GPU denetimi yanlış alarmdı; `--list-devices` + bellek denetimiyle değişti. Paket 7 → %35: %78 |
| 25.10.2026 | RAG + FT tam eğitimi: 113 adım, 7,8 saat, doğrulama kaybı 0,834 → 0,130; deneme üretiminde format ve hipotez işareti doğru, 2 rakam hatası (Katman 4 yakalıyor). Paket 7 → %60: %80 |
| 25.10.2026 | Yalnızca FT tam eğitimi: 117 adım, 5,6 saat, doğrulama kaybı 1,013 → 0,106; deneme üretimi hatasız. İki bağdaştırıcı 02'nin son çıktısında. Paket 7 → %100: %85 |
| 26.10.2026 | Değerlendirme deneme koşusu (5 × 8 metin, hata yok; tam koşu ~4,5 saat). İnce ayarlı sistemlerde format %100; RAG + FT notu yanlış satıra bağlıyor. Doğrulama v1.8 (yanlış alarm), puanlama 1.1 (satır düzeyinde atıf, birden çok klasör). Paket 8 → %90, 9 → %60: %87 |
| 26.10.2026 | Ablation tamam: 5 sistem × 720 ay (4,3 saat), baseline ile puanlandı. RAG + FT format %97, işaretsiz neden 0,06/metin, kaynak precision/recall %75 / %59 (yalnızca RAG %54 / %34); yeni sektörde aynı düzey. Zayıf nokta V2 notla açıklama (1/17). Recall@8 istemlerden yeniden ölçüldü. Paket 4 → %90, 9 → %80: %90 |
| 26.10.2026 | Karar turu 13: V2 kümesi ve ikinci eğitim turu yok; RAG + FT Hugging Face'te yayınlanacak, depo şimdilik gizli. Model kartı ve örnekler hazır (`release/huggingface/`), yükleme adımları `gpu/README.md` Bölüm 8. Paket 9 → %90, 10 → %30: %92 |
| 26.10.2026 | RAG + FT modeli Hugging Face'te yayınlandı (https://huggingface.co/nberkc16/bwa-kommentar-gemma4-e4b-lora); dosyalar doğrulandı. Paket 10 → %40: %93 |
