# Yol haritası ve proje durumu

> **Bu dosya her adımdan sonra güncellenir** [KARAR, tur 4]. · **Son güncelleme:** 15.10.2026 (karar turu 6: model tarafı kararlarının bir kısmı)

---

## 1. Genel durum: ~%30 tamamlandı

**Nasıl hesaplandı?** Yüzde, adım sayısına göre değil tahmini iş yüküne göre hesaplandı:

1. Proje 10 iş paketine bölündü.
2. Her pakete, tek bir geliştiricinin yapay zekâ desteğiyle harcayacağı tahmini **iş günü** verildi.
3. Her paketin tamamlanma oranı kendi iş günüyle çarpıldı ve toplam iş gününe bölündü.

```
tamamlanan iş = Σ (paketin iş günü × tamamlanma oranı) = 15,1 gün
toplam iş     = 50 gün
durum         = 15,1 / 50 ≈ %30
```

**Belirsizlik:**
- Tahminler en çok model tarafındaki paketlerde belirsiz: ideal yorumların üretimi, baseline'lar, fine-tuning, değerlendirme. Bu paketler GPU erişimine, temel modelin Almanca kalitesine ve deneme–yanılma döngülerine bağlı.
- Kullanıcının dizüstünde 4 GB GPU var; eğitim ve değerlendirme bulutta (Kaggle) yapılacak. Defterlerin kullanıcı tarafından çalıştırılması turları uzatabilir.
- Gerçekçi aralık %24–35.
- Kalan işin ~%70'i model tarafında. Bu, G7'deki odakla uyumlu.

---

## 2. İş paketleri

| # | İş paketi | Tahmini iş (gün) | Tamamlanma | Tamamlanan (gün) | Durum |
|---|---|---:|---:|---:|---|
| 1 | Problem tanımı, tasarım ve kararlar | 3 | %100 | 3,0 | ✅ tamamlandı |
| 2 | Veri üreteci (+ dengelenmiş V2 kümesi, eğitim profili) | 5 | %100 | 5,0 | ✅ tamamlandı |
| 3 | Hesaplama modülü (Katman 1, `facts.json`) | 5 | %90 | 4,5 | ✅ tamamlandı (ince ayar kaldı) |
| 4 | Bilgi tabanı ve retrieval (Katman 2) | 6 | %10 | 0,6 | ⏳ başlamadı (tasarım kararları alındı) |
| 5 | İdeal yorumların üretimi (eğitim hedefleri) | 8 | %5 | 0,4 | ⏳ başlamadı (çıktı yapısı kararlaştırıldı) |
| 6 | Model seçimi, çıkarım altyapısı, baseline'lar (çıplak model, yalnızca RAG) | 5 | %5 | 0,25 | ⏳ başlamadı (aday listesi kararlaştırıldı) |
| 7 | Fine-tuning (LoRA): yalnızca FT ve RAG + FT | 6 | %0 | 0,0 | ⏳ başlamadı |
| 8 | Doğrulama katmanı (Katman 4) | 3 | %5 | 0,15 | ⏳ başlamadı |
| 9 | Değerlendirme ve ablation | 6 | %15 | 0,9 | ⏳ başlamadı (altyapı hazır) |
| 10 | Portfolyo dokümantasyonu | 3 | %10 | 0,3 | ⏳ başlamadı |
| | **Toplam** | **50** | | **15,1** | **≈ %30** |

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
- **Kalan (%10):** Bayrak parametrelerinin ince ayarı. Gerekirse model sonuçlarına göre yapılır; ör. V4 ve V6 recall'ı (%61–63).
- **Açık kararlar:** Bayrak parametreleri [ÖNERİ] (`facts/config.toml`).

### 4. Bilgi tabanı ve retrieval (Katman 2) — ⏳ başlamadı
- **Hazır olan:** K-C notları üretiliyor, `dauerhaft`/`temporär` alanı var, RAG penceresi 13 ay.
- **Kalan:**
  - K-A: BWA satır açıklamaları ve SKR03 → BWA eşlemesi.
  - K-B: çarpıklık rehberi.
  - K-C'nin yüklenmesi.
  - K-D: önceki ayların onaylı yorumları; paket 5'e bağlı.
  - Sorgu üretimi (`facts.json`'dan), meta veri filtresi, retrieval'ın ölçülmesi.
- **Kararlaştırılan (tur 6):**
  - BGE-M3 + Chroma.
  - K-C: 13 ay filtre + top-k (k = 8); "bütün notlar" ablation'da.
  - recall@k metriği.
  - K-D ilk sürümde kapalı.
- **Açık kararlar:**
  - K-E (sektör oranları) dahil edilecek mi? Şu an [ÖNERİ]; güvenilir kaynak bulunursa.
  - SKR03 eşlemesinin kaynağı ve doğrulanması.

### 5. İdeal yorumların üretimi — ⏳ başlamadı
- **Kalan:**
  - Eğitim hedeflerinin üretimi ve kalite kontrolü.
  - Doğrulama katmanıyla (paket 8) otomatik kontrol.
  - Eğitim formatı.
- **Kararlaştırılan (tur 6):**
  - Çıktı yapısı (CLAUDE.md 6.3).
  - Notta geçmeyen nedenlerde açık soru veya işaretli hipotez; ground truth nedeni hedef metne yazılmaz.
- **Açık kararlar** (`docs/06`, B ve C; ek açıklamayla yeniden soruldu):
  - **Üretim yöntemi** [AÇIK]. Öneri: karma + altın küme.
  - **Öğretmen model** [AÇIK]. Öneri: açık ağırlıklı, API üzerinden.
  - **Eğitim/test ayrımı** [AÇIK]. Öneri: test arketipi A1; 20 eğitim + 3 doğrulama varyantı / arketip.
  - `train_price_boost` profilinin eğitim verisinde kullanılması.

### 6. Model seçimi, çıkarım altyapısı, baseline'lar — ⏳ başlamadı
- **Kalan:**
  - Aday modellerin Almanca kalitesinin denenmesi.
  - Çıkarım altyapısı ve istem (prompt).
  - Çıplak model ve yalnızca RAG varyantlarının test kümesinde çalıştırılması.
- **Kararlaştırılan (tur 6):** Deneme turu adayları Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B. Deneme turu kullanıcının dizüstünde (Ollama) yapılabilir.
- **Açık kararlar:** Donanım ve bütçe (Kaggle / kiralık GPU); çıkarım altyapısı [ÖNERİ: değerlendirme vLLM, demo Ollama].

### 7. Fine-tuning (LoRA) — ⏳ başlamadı
- **Kalan:**
  - Eğitim verisinin hazırlanması (paket 5).
  - LoRA eğitimi: yalnızca FT ve RAG + FT varyantları.
  - Hiperparametreler, eğitim kayıtları.
- **Açık kararlar:** Fine-tuning araç seti [ÖNERİ: Unsloth + TRL, QLoRA], donanım (Kaggle / kiralık GPU; dizüstünün 4 GB GPU'su eğitime yetmiyor), eğitim verisi hacmi [ÖNERİ: 960 ay].

### 8. Doğrulama katmanı (Katman 4) — ⏳ başlamadı
- **Hazır olan:** Kural kararlaştırıldı: rakam ya `facts.json`'la eşleşir ya da atıf yapılan nottan gelir. Notlardaki rakamlar ground truth'ta kayıtlı.
- **Kalan:**
  - Almanca rakam ayıklama (`1.234,5`, `42 T€`, `18 %`).
  - Toleranslı eşleştirme.
  - Kaynak atfı ve tahmin işareti kontrolü.
  - Uyarı listesi.
- **Açık kararlar:** Yuvarlama toleransları (ör. `42 T€` ile 41.712 € eşleşir mi?).

### 9. Değerlendirme ve ablation — ⏳ başlamadı (altyapı hazır)
- **Hazır olan:**
  - Ground truth: olaylar, ay kayıtları, kabul edilebilir uyarılar, V2 kararı.
  - Dengelenmiş V2 kümesi.
  - Metrik tanımları (CLAUDE.md 8).
  - Bayrak isabeti aracı (`tools/flag_quality.py`; eşik üstü süzme dahil).
- **Kalan:**
  - Metriklerin kodlanması.
  - 4 varyantın aynı test kümesinde çalıştırılması.
  - Sonuçların analizi.
- **Açık kararlar:**
  - Üslup değerlendirmesi: insan mı, LLM-as-judge mı? (CLAUDE.md 8)
  - Test arketipi [ÖNERİ: A1 + iki test düzeyi].
  - Retrieval isabeti (recall@k) metriği eklendi (tur 6).
  - `expected_flags`'in anlamlılık eşiğine göre süzülmesi.

### 10. Portfolyo dokümantasyonu — ⏳ başlamadı
- **Hazır olan:** Tasarım belgeleri (`docs/`).
- **Kalan:**
  - README.
  - Problem → çözüm → kanıt (ablation) anlatısı.
  - Örnek çıktılar (Muster GmbH'nin toparlanma hikâyesi).
  - Görseller.
- **Açık kararlar:** Formatı (README, rapor, demo defteri?).

---

## 4. Sıradaki adımlar

1. **Model tarafında açık kalan kararlar** ([`06_model_tarafi_secenekler.md`](06_model_tarafi_secenekler.md)). Tur 6'da kısmen karara bağlandı; açık olanlar:
   - Test arketipi ve varyant sayısı (paket 5).
   - Donanım ve bütçe (paket 6–7).
   - İdeal yorum yöntemi ve öğretmen model (paket 5).
2. **Bilgi tabanı (paket 4):** K-A ve K-B metinleri, K-C yükleme, 13 aylık pencereyle retrieval.
3. **Doğrulama katmanı (paket 8):** Ideal yorumların otomatik kontrolünde de kullanılacağı için paket 5'ten önce yazılması önerilir.

## 5. Değişiklik geçmişi

| Tarih | Değişiklik |
|---|---|
| 15.10.2026 | İlk sürüm (karar turu 4 sonrası): %21 |
| 15.10.2026 | Karar turu 5: E18 kalibrasyonu, Katman 1 (şema 1.0) kodlandı, bayrak isabeti ölçüldü: %28 |
| 15.10.2026 | Model tarafı seçenekleri sunuldu (`06_model_tarafi_secenekler.md`); durum değişmedi: %28 |
| 15.10.2026 | Karar turu 6: deneme turu adayları, çıktı yapısı, notsuz neden kuralı, bilgi tabanı (BGE-M3, Chroma, top-k, K-D kapalı). Paket 4 → %10, 5 → %5, 6 → %5: %30 |
