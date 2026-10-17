# 09 — Bilgi tabanı ve getirme (Katman 2)

> **Durum:** v1 kodlandı (`rag/`, 10 test), 17.10.2026.
> - **[KARAR]:**
>   - BGE-M3 + Chroma; K-C için 13 ay + top-k (k = 8); K-D kapalı (tur 6).
>   - K-A yalnızca açıklama, SKR03 aralıkları hiçbir zaman eklenmez; K-E kapsam dışı (tur 10).
> - **[ÖNERİ]:** Bilgi metinleri, sorgu yöntemi ve K-A/K-B seçimi (bu belge).
>
> **İlgili:** CLAUDE.md 6.2 (Katman 2) · `06_model_tarafi_secenekler.md`, Bölüm D · Karar kaydı: `00`, Bölüm 16

---

## 1. Bileşenler

| Kod | İçerik | Kaynak | Kaynak kimliği (örnek) |
|---|---|---|---|
| K-A | BWA satır ve oran açıklamaları (30 satır + 4 oran) | `rag/knowledge.toml` | `BWA-Erläuterung Personalkosten` |
| K-B | Çarpıklık rehberi: Katman 1'in 9 bayrak kuralı + „Grundsätze“ | `rag/knowledge.toml` | `Leitfaden V1 (fehlende Abgrenzung)` |
| K-C | Firma bağlam notları | Üreteç koşusu: `model_input/context_notes.jsonl` | `Kontextnotiz 2025-06 #2`, `Firmenprofil` |
| K-D | Önceki ayların onaylı yorumları | — | İlk sürümde kapalı [KARAR, tur 6] |
| K-E | Sektör karşılaştırma oranları | — | **Kapsam dışı** [KARAR, tur 10] |

**K-A ve K-B metinleri:**
- Almanca yazıldı; her parça ~40–110 kelime.
- **Rakam yok:** modelin kullandığı her rakam `facts.json`'dan ya da bir bağlam notundan gelmeli. Testle denetlenir.
- **SKR03 hesap aralıkları yok** [KARAR, tur 10]. Kesin hesap ataması BWA'nın Kontennachweis'ında görülür.
- **Yön bilgisi:** K-A, oranların yönünü açıkça söyler; örneğin alış fiyatı artışı Rohertragsquote'yi düşürür, satış fiyatı artışı yükseltir. Deneme turunda iki modelin tam bu yönü karıştırdığı görüldü (`trial/review.md`, örnek 5).
- **Hipotez dayanağı:** K-B, notta karşılığı olmayan nedenlerde kullanılabilecek tipik nedenleri ve soruları içerir. Hipotezler yalnızca görülebilir bilgiden türetilir (B3).

**K-E neden yok:** Güvenilir sektör oranları (ör. DATEV'in sektör karşılaştırmaları) herkese açık değil. Uydurulmuş ya da doğrulanamayan karşılaştırma değerleri, projenin „kaynaksız iddia yok“ ilkesiyle çelişirdi.

## 2. Depo

- **Chroma** (gömülü). Embedding'ler dışarıda hesaplanıp Chroma'ya verilir.
  - Kalıcı depo `<koşu>/rag/chroma-bge-m3/` altında; repoda tutulmaz.
  - İki koleksiyon: genel bilgi (K-A, K-B) ve bağlam notları (K-C).
  - Not meta verileri: firma, dönem, dönem sırası, süre (`dauerhaft`/`temporär`), Firmenprofil işareti.
- **Embedding:** BGE-M3 (`BAAI/bge-m3`, normalize edilmiş yoğun vektörler, sentence-transformers).
  - Referans koşunun 1.097 parçası CPU'da ~2 dakikada işleniyor.
  - Testler bağımlılıksız bir karma embedding kullanır.
  - Koleksiyon hangi embedding ile doldurulduğunu kaydeder; farklı bir modelle sorgulamak hata verir.
- **Ground truth'a erişim yok:** Katman 2 yalnızca `model_input/` okur.

## 3. Getirme (`rag/retrieve.py`)

Bir firma-ay için bağlam üç kısımdan oluşur:

1. **K-B (anahtarla):** „Grundsätze“ ve `facts.json`'daki her bayrak kuralının rehber parçası.
2. **K-A (anahtarla):** Anlamlı kalemlerin, bayraklı satırların ve önceki yılın aynı ayına göre anlamlı oranların açıklamaları.
3. **K-C (anlamsal):**
   - Firma + 13 aylık pencere (t−12 … t) Chroma'nın meta veri filtresiyle seçilir.
   - Pencere içinden top-k (k = 8) not, sorgularla benzerliğe göre seçilir.
   - Dönemsiz `Firmenprofil` her zaman eklenir.
   - Seçilen notlar kronolojik sıralanır.
   - Penceredeki not sayısı k'yı aşmıyorsa hepsi verilir.

K-A ve K-B anahtarla getirilir, çünkü 44 sabit parçadan hangisinin gerektiği `facts.json`'dan kesin olarak bellidir. Anlamsal arama burada yalnızca hata riski eklerdi.

**K-C sorgusu** `facts.json`'dan otomatik üretilir (CLAUDE.md 6.2). Öğeler:
- Her anlamlı kalem: „Personalkosten gestiegen gegenüber dem Vorjahresmonat“.
- Her bayrak: satır adı + kanıt metni.
- Her anlamlı oran.
- Sakin aylarda Gesamtleistung ve Betriebsergebnis.

Üç yöntem [ÖNERİ, `rag/config.toml`]:

| Yöntem | Sorgu |
|---|---|
| `single` | Bütün öğeler tek bir sorguda (+ ayın adı) |
| `multi` | Öğe başına bir sorgu; sıralamalar Reciprocal Rank Fusion ile birleştirilir |
| `multi_expanded` | `multi` + her sorguya kalemin K-A açıklaması eklenir. Böylece „Personalkosten gestiegen“ sorgusu „Neueinstellungen“, „Tariferhöhung“ gibi not kelimelerine yaklaşır |

## 4. Kullanım

```bash
python -m rag build    --run data/synthetic/reference_seed42              # depoyu kurar (BGE-M3)
python -m rag retrieve --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06
python -m rag export   --run data/synthetic/reference_seed42              # <run>/rag/retrieval.jsonl
python tools/retrieval_quality.py data/synthetic/reference_seed42         # getirme isabeti (ground truth)
```

`export` her firma-ay için bağlamı (kaynak kimliği, tür, metin; notlarda dönem ve süre) JSONL olarak yazar. Prompting ve Kaggle defterleri bu dosyayı kullanır; böylece GPU tarafında embedding modeli gerekmez.

## 5. Getirme isabeti (recall@k)

_Ölçüm sürüyor._
