# Yol haritası ve proje durumu

> **Bu dosya her adımdan sonra güncellenir** [KARAR, tur 4]. · **Son güncelleme:** 15.10.2026 (karar turu 4: dengelenmiş V2 kümesi, `facts.json` şema önerisi)

---

## 1. Genel durum: ~%21 tamamlandı

**Nasıl hesaplandı?** Yüzde, adım sayısına göre değil tahmini iş yüküne göre hesaplandı:

1. Proje 10 iş paketine bölündü.
2. Her pakete, tek bir geliştiricinin yapay zekâ desteğiyle harcayacağı tahmini **iş günü** verildi.
3. Her paketin tamamlanma oranı kendi iş günüyle çarpıldı ve toplam iş gününe bölündü.

```
tamamlanan iş = Σ (paketin iş günü × tamamlanma oranı) = 10,4 gün
toplam iş     = 50 gün
durum         = 10,4 / 50 ≈ %21
```

**Belirsizlik:**
- Tahminler en çok model tarafındaki paketlerde belirsiz: ideal yorumların üretimi, baseline'lar, fine-tuning, değerlendirme. Bu paketler GPU erişimine, temel modelin Almanca kalitesine ve deneme–yanılma döngülerine bağlı.
- Gerçekçi aralık %15–25.
- Kalan işin ~%60'ı model tarafında. Bu, G7'deki odakla uyumlu.

---

## 2. İş paketleri

| # | İş paketi | Tahmini iş (gün) | Tamamlanma | Tamamlanan (gün) | Durum |
|---|---|---:|---:|---:|---|
| 1 | Problem tanımı, tasarım ve kararlar | 3 | %100 | 3,0 | ✅ tamamlandı |
| 2 | Veri üreteci (+ dengelenmiş V2 kümesi, eğitim profili) | 5 | %100 | 5,0 | ✅ tamamlandı |
| 3 | Hesaplama modülü (Katman 1, `facts.json`) | 5 | %20 | 1,0 | 🔄 devam ediyor |
| 4 | Bilgi tabanı ve retrieval (Katman 2) | 6 | %5 | 0,3 | ⏳ başlamadı |
| 5 | İdeal yorumların üretimi (eğitim hedefleri) | 8 | %0 | 0,0 | ⏳ başlamadı |
| 6 | Model seçimi, çıkarım altyapısı, baseline'lar (çıplak model, yalnızca RAG) | 5 | %0 | 0,0 | ⏳ başlamadı |
| 7 | Fine-tuning (LoRA): yalnızca FT ve RAG + FT | 6 | %0 | 0,0 | ⏳ başlamadı |
| 8 | Doğrulama katmanı (Katman 4) | 3 | %5 | 0,15 | ⏳ başlamadı |
| 9 | Değerlendirme ve ablation | 6 | %10 | 0,6 | ⏳ başlamadı (altyapı hazır) |
| 10 | Portfolyo dokümantasyonu | 3 | %10 | 0,3 | ⏳ başlamadı |
| | **Toplam** | **50** | | **10,4** | **≈ %21** |

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
  - Ayrıntılar `docs/04`'te.
- **Açık kararlar:**
  - **E18 kalibrasyonu (yeni soru):** Geç gelen faturalar malzeme satırında %15–40 kayıyor. Bu yüzden A2'de ayların %11'inde Rohertragsquote negatif çıkıyor. %5–20'ye indirmek bu oranı %3'e düşürür. Kabul edilirse referans koşu ve dengelenmiş küme yeniden üretilir.

### 3. Hesaplama modülü (Katman 1) — 🔄 devam ediyor
- **Yapılan:**
  - Eşik başlangıç değerleri kararlaştırıldı.
  - Referans veride eşik analizi yapıldı.
  - `facts.json` şema önerisi gerçek bir ay üzerinde hazırlandı (`docs/05`).
  - Prototip hesap yapıldı (repoda değil).
- **Kalan:**
  - Modülün kodlanması.
  - Bayrak kurallarının (V1–V6) kalibrasyonu.
  - Testler; ground truth ile tutarlılık (ör. Rohertrag adayı kuralı üreteçle aynı mı?).
  - Bütün ayların `facts.json`'ı.
- **Açık kararlar (`docs/05`, Bölüm 6):**
  1. Anlamlılık hangi karşılaştırmaya göre?
  2. Rohertrag adayı bütün arketiplerde mi?
  3. `normal_level` ve `base_unusual` alanları.
  4. `delta_pct = null` kuralları.
  5. Kümülatif yalnızca bilgi amaçlı mı?

### 4. Bilgi tabanı ve retrieval (Katman 2) — ⏳ başlamadı
- **Hazır olan:** K-C notları üretiliyor, `dauerhaft`/`temporär` alanı var, RAG penceresi 13 ay.
- **Kalan:**
  - K-A: BWA satır açıklamaları ve SKR03 → BWA eşlemesi.
  - K-B: çarpıklık rehberi.
  - K-C'nin yüklenmesi.
  - K-D: önceki ayların onaylı yorumları; paket 5'e bağlı.
  - Sorgu üretimi (`facts.json`'dan), meta veri filtresi, retrieval'ın ölçülmesi.
- **Açık kararlar:**
  - Embedding modeli ve vektör veritabanı (CLAUDE.md 10).
  - K-E (sektör oranları) dahil edilecek mi? Şu an [ÖNERİ]; güvenilir kaynak bulunursa.
  - SKR03 eşlemesinin kaynağı ve doğrulanması.

### 5. İdeal yorumların üretimi — ⏳ başlamadı
- **Kalan:**
  - Eğitim hedeflerinin üretimi ve kalite kontrolü.
  - Doğrulama katmanıyla (paket 8) otomatik kontrol.
  - Eğitim formatı.
- **Açık kararlar:**
  - **Üretim yöntemi** [AÇIK, ertelendi]: büyük modelle üretip elle gözden geçirme / şablon / elle yazma / karışım.
  - **Çıktı yapısı** (CLAUDE.md 6.3, [ÖNERİ]).
  - **Eğitim/test ayrımı** [AÇIK, ertelendi]: hangi arketip test, arketip başına kaç varyant.
  - `train_price_boost` profilinin eğitim verisinde kullanılması.

### 6. Model seçimi, çıkarım altyapısı, baseline'lar — ⏳ başlamadı
- **Kalan:**
  - Aday modellerin Almanca kalitesinin denenmesi.
  - Çıkarım altyapısı ve istem (prompt).
  - Çıplak model ve yalnızca RAG varyantlarının test kümesinde çalıştırılması.
- **Açık kararlar:** Temel model (3–8B sınıfı, lisans notları CLAUDE.md 10), donanım, çıkarım altyapısı.

### 7. Fine-tuning (LoRA) — ⏳ başlamadı
- **Kalan:**
  - Eğitim verisinin hazırlanması (paket 5).
  - LoRA eğitimi: yalnızca FT ve RAG + FT varyantları.
  - Hiperparametreler, eğitim kayıtları.
- **Açık kararlar:** Fine-tuning araç seti, donanım (bulut GPU), eğitim verisi hacmi.

### 8. Doğrulama katmanı (Katman 4) — ⏳ başlamadı
- **Hazır olan:** Kural kararlaştırıldı: rakam ya `facts.json`'la eşleşir ya da atıf yapılan nottan gelir. Notlardaki rakamlar ground truth'ta kayıtlı.
- **Kalan:**
  - Almanca rakam ayıklama (`1.234,5`, `42 T€`, `18 %`).
  - Toleranslı eşleştirme.
  - Kaynak atfı ve tahmin işareti kontrolü.
  - Uyarı listesi.
- **Açık kararlar:** Yuvarlama toleransları (ör. `42 T€` ile 41.712 € eşleşir mi?).

### 9. Değerlendirme ve ablation — ⏳ başlamadı (altyapı hazır)
- **Hazır olan:** Ground truth (olaylar, ay kayıtları, kabul edilebilir uyarılar, V2 kararı), dengelenmiş V2 kümesi, metrik tanımları (CLAUDE.md 8).
- **Kalan:**
  - Metriklerin kodlanması.
  - 4 varyantın aynı test kümesinde çalıştırılması.
  - Sonuçların analizi.
- **Açık kararlar:**
  - Üslup değerlendirmesi: insan mı, LLM-as-judge mı? (CLAUDE.md 8)
  - Test arketipi.
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

1. `facts.json` şema sorularının cevaplanması (`docs/05`, Bölüm 6) ve E18 kalibrasyon kararı.
2. Katman 1 modülünün kodlanması ve testleri.
3. Paket 4 (bilgi tabanı) ile paket 5 (ideal yorumlar) için yöntem kararları. İkisi birbirine bağlı (K-D).

---

## 5. Değişiklik geçmişi

| Tarih | Değişiklik |
|---|---|
| 15.10.2026 | İlk sürüm (karar turu 4 sonrası): %21 |
