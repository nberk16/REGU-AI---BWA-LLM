# Yol haritası ve proje durumu

> **Bu dosya her adımdan sonra güncellenir** [KARAR, tur 4]. · **Son güncelleme:** 15.10.2026 (karar turu 7: eğitim/test, Kaggle, ideal yorum yöntemi, öğretmen model)

---

## 1. Genel durum: ~%32 tamamlandı

**Nasıl hesaplandı?** Yüzde, adım sayısına göre değil tahmini iş yüküne göre hesaplandı:

1. Proje 10 iş paketine bölündü.
2. Her pakete, tek bir geliştiricinin yapay zekâ desteğiyle harcayacağı tahmini **iş günü** verildi.
3. Her paketin tamamlanma oranı kendi iş günüyle çarpıldı ve toplam iş gününe bölündü.

```
tamamlanan iş = Σ (paketin iş günü × tamamlanma oranı) = 15,8 gün
toplam iş     = 50 gün
durum         = 15,8 / 50 ≈ %32
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
| 5 | İdeal yorumların üretimi (eğitim hedefleri) | 8 | %10 | 0,8 | ⏳ başlamadı (yöntem ve kümeler kararlaştırıldı) |
| 6 | Model seçimi, çıkarım altyapısı, baseline'lar (çıplak model, yalnızca RAG) | 5 | %5 | 0,25 | ⏳ başlamadı (aday listesi kararlaştırıldı) |
| 7 | Fine-tuning (LoRA): yalnızca FT ve RAG + FT | 6 | %0 | 0,0 | ⏳ başlamadı |
| 8 | Doğrulama katmanı (Katman 4) | 3 | %5 | 0,15 | ⏳ başlamadı |
| 9 | Değerlendirme ve ablation | 6 | %20 | 1,2 | ⏳ başlamadı (altyapı ve test tasarımı hazır) |
| 10 | Portfolyo dokümantasyonu | 3 | %10 | 0,3 | ⏳ başlamadı |
| | **Toplam** | **50** | | **15,8** | **≈ %32** |

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
- **Kararlaştırılan (turlar 6–7):**
  - Çıktı yapısı (CLAUDE.md 6.3).
  - Notta geçmeyen nedenlerde açık soru veya işaretli hipotez; ground truth nedeni hedef metne yazılmaz.
  - Yöntem: karma (içerik planı + öğretmen modelin dili + otomatik kontrol) ve 20–30 örneklik altın küme.
  - Öğretmen: açık ağırlıklı model, API üzerinden.
  - Kümeler: eğitim A2 + A3 × 20 varyant (`train_price_boost`, seed 7) = 960 ay; doğrulama 3 + 3 varyant (`docs/04`, Bölüm 9).
- **Açık kararlar:**
  - Somut öğretmen model ve sağlayıcı [ÖNERİ: Mistral Large 3, Mistral API]. Kullanıcının API anahtarı alması gerekir.

### 6. Model seçimi, çıkarım altyapısı, baseline'lar — ⏳ başlamadı
- **Kalan:**
  - Aday modellerin Almanca kalitesinin denenmesi.
  - Çıkarım altyapısı ve istem (prompt).
  - Çıplak model ve yalnızca RAG varyantlarının test kümesinde çalıştırılması.
- **Kararlaştırılan (tur 6):** Deneme turu adayları Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B. Deneme turu kullanıcının dizüstünde (Ollama) yapılabilir.
- **Kararlaştırılan (tur 7):** Değerlendirme Kaggle'da; deneme turu örnekleri doğrulama varyantlarından.
- **Açık kararlar:** Çıkarım altyapısı [ÖNERİ: değerlendirme vLLM, demo Ollama].

### 7. Fine-tuning (LoRA) — ⏳ başlamadı
- **Kalan:**
  - Eğitim verisinin hazırlanması (paket 5).
  - LoRA eğitimi: yalnızca FT ve RAG + FT varyantları.
  - Hiperparametreler, eğitim kayıtları.
- **Kararlaştırılan (tur 7):** Donanım: Kaggle (ücretsiz T4); dizüstünün 4 GB GPU'su eğitime yetmiyor. Eğitim verisi: 960 ay.
- **Açık kararlar:** Fine-tuning araç seti [ÖNERİ: Unsloth + TRL, QLoRA].

### 8. Doğrulama katmanı (Katman 4) — ⏳ başlamadı
- **Hazır olan:** Kural kararlaştırıldı: rakam ya `facts.json`'la eşleşir ya da atıf yapılan nottan gelir. Notlardaki rakamlar ground truth'ta kayıtlı.
- **Kalan:**
  - Almanca rakam ayıklama (`1.234,5`, `42 T€`, `18 %`).
  - Toleranslı eşleştirme.
  - Kaynak atfı ve tahmin işareti kontrolü.
  - Uyarı listesi.
- **Açık kararlar:** Yuvarlama toleransları (ör. `42 T€` ile 41.712 € eşleşir mi?). Tur 7'de seçenekleriyle soruldu.

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
  - Retrieval isabeti (recall@k) metriği eklendi (tur 6).
- **Kararlaştırılan (tur 7):** Test: yeni sektör (A1, öğretilmemiş tür) + yeni firma (A2/A3'ün görülmemiş varyantları, öğretilmiş tür) + dengelenmiş V2 kümesi (`docs/04`, Bölüm 9.2).
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

Model tarafının yöntem kararları alındı (turlar 6–7, [`06_model_tarafi_secenekler.md`](06_model_tarafi_secenekler.md)). Önerilen sıra:

1. **Doğrulama katmanı v1 (paket 8):** Almanca rakam ayıklama, `facts.json` ve notlarla eşleştirme, kaynak/hipotez kontrolü, format kontrolü. Deneme turunu puanlamak ve ideal yorumları denetlemek için gerekli. Önkoşul: yuvarlama toleransı kararı.
2. **Almanca deneme turu (paket 6):**
   - Asistan hazırlar: istem, doğrulama varyantlarından ~10 örnek, Ollama betiği.
   - Kullanıcı dizüstünde çalıştırır.
   - Sonuçlar doğrulama katmanıyla puanlanır ve temel model seçilir.
3. **Bilgi tabanı (paket 4):** K-A ve K-B metinleri, Chroma indeksi, 13 ay + top-k getirme, recall@k.
4. **İdeal yorumlar (paket 5):** İçerik planı kodu, öğretmen modelle metin üretimi (kullanıcının API anahtarıyla), altın küme.
5. **Kaggle defterleri (paket 6, 7, 9):** Fine-tuning, baseline'lar, değerlendirme.

## 5. Değişiklik geçmişi

| Tarih | Değişiklik |
|---|---|
| 15.10.2026 | İlk sürüm (karar turu 4 sonrası): %21 |
| 15.10.2026 | Karar turu 5: E18 kalibrasyonu, Katman 1 (şema 1.0) kodlandı, bayrak isabeti ölçüldü: %28 |
| 15.10.2026 | Model tarafı seçenekleri sunuldu (`06_model_tarafi_secenekler.md`); durum değişmedi: %28 |
| 15.10.2026 | Karar turu 6: deneme turu adayları, çıktı yapısı, notsuz neden kuralı, bilgi tabanı (BGE-M3, Chroma, top-k, K-D kapalı). Paket 4 → %10, 5 → %5, 6 → %5: %30 |
| 15.10.2026 | Karar turu 7: test tasarımı (A1 + görülmemiş varyantlar), 20 + 3 varyant, Kaggle, karma yöntem, açık ağırlıklı öğretmen. Paket 5 → %10, 9 → %20: %32 |
