# 09 — Bilgi tabanı ve getirme (Katman 2)

> **Durum:** v1 kodlandı (`rag/`, 10 test); sorgu yöntemi ölçümle seçildi (`single`, k = 8), 18.10.2026.
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

**Varsayılan: `single`**, doğrulama varyantlarındaki ölçümle seçildi (Bölüm 5).

## 4. Kullanım

```bash
python -m rag build    --run data/synthetic/reference_seed42              # depoyu kurar (BGE-M3)
python -m rag retrieve --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06
python -m rag export   --run data/synthetic/reference_seed42              # <run>/rag/retrieval.jsonl
python tools/retrieval_quality.py data/synthetic/reference_seed42         # getirme isabeti (ground truth)
```

`export` her firma-ay için bağlamı (kaynak kimliği, tür, metin; notlarda dönem ve süre) JSONL olarak yazar. `--firms` ile yalnızca seçilen firmalar yazılır. İstem 1.1 bu dosyayı kullanır (`python -m prompting --retrieval …`, [`10_istem.md`](10_istem.md)); böylece GPU tarafında embedding modeli gerekmez.

**İstemdeki rolü (istem 1.1):** K-A ve K-B „WISSEN“ başlığı altında arka plan bilgisi olarak verilir; neden kaynağı sayılmaz. Atıf yapılabilir kaynaklar yalnızca K-C notlarıdır (`10_istem.md`, Bölüm 3 ve 7).

## 5. Getirme isabeti (recall@k)

Araç: `tools/retrieval_quality.py`. Ground truth'u yalnızca bu araç okur; Katman 2 okumaz.

**İlgili notlar** (yalnızca 13 aylık penceredeki, notlanmış olaylar):
- **Çekirdek:** O ay başlayan olayların notları.
- **Geniş:** Çekirdek + sürmekte olan ya da önceki yılın aynı ayındaki olayların notları; bu olaylar ayın anlamlı kalemlerini veya bayraklı satırlarını etkiliyorsa. Rohertrag adayı varsa ground truth'taki nedenlerin notları da eklenir.

**Çeldirici payı:** Getirilen notlardan hiçbir olaya ait olmayanların oranı.

### 5.1 Seçim: doğrulama varyantları (A2/A3 v120–v122, 144 firma-ay)

Sorgu yöntemi, deneme turundaki ilkeyle aynı şekilde **doğrulama varyantlarında** seçildi; test kümesi seçimde kullanılmadı.

| Yöntem | k | Recall çekirdek | Recall geniş | Geniş: tam getirilen ay | Çeldirici payı | Ort. not |
|---|---:|---:|---:|---:|---:|---:|
| **single** | 8 | **94,3 %** | **86,3 %** | **64,7 %** | 7,3 % | 8,0 |
| multi | 8 | 68,9 % | 79,8 % | 51,5 % | 8,9 % | 8,0 |
| multi_expanded | 8 | 78,7 % | 82,1 % | 55,9 % | 7,0 % | 8,0 |
| bütün notlar | – | 100 % | 100 % | 100 % | 16,5 % | 12,8 |

### 5.2 Rapor: test kümesi (`reference_seed42`, 720 firma-ay)

| Yöntem | k | Recall çekirdek | Recall geniş | Geniş: tam getirilen ay | Çeldirici payı | Ort. not |
|---|---:|---:|---:|---:|---:|---:|
| single | 4 | 67,2 % | 51,6 % | 23,4 % | 2,7 % | 4,0 |
| **single** | **8** | **91,4 %** | **83,3 %** | **59,1 %** | **5,2 %** | 8,0 |
| single | 12 | 99,0 % | 97,1 % | 91,0 % | 9,9 % | 11,2 |
| multi | 8 | 69,1 % | 74,9 % | 42,8 % | 7,2 % | 8,0 |
| multi_expanded | 8 | 70,6 % | 76,5 % | 45,5 % | 5,9 % | 8,0 |
| bütün notlar | – | 100 % | 100 % | 100 % | 11,3 % | 12,2 |

### 5.3 Yorum

- **Pencere küçük.** 13 ayda firma başına ortalama ~12 not var; önceki tahmin 20–30'du. Top-8 pencerenin yaklaşık üçte ikisini alıyor.
- **`single` açık ara en iyisi.**
  - O ayın notlarının %91–94'ünü ve geniş anlamda ilgili notların %83–86'sını getiriyor.
  - Çeldirici payını yarıya indiriyor: %11–17 yerine %5–7.
  - Nedeni büyük olasılıkla dönem bilgisi. Tek sorgu ayın adını içeriyor; notlarda da ay adı geçiyor („ab Juni“, „im Juni“). Bu da hem o ayın hem önceki yılın aynı ayının notlarını öne çıkarıyor.
  - Öğe başına sorgularda dönem bilgisi yok. K-A ile genişletmek biraz yardımcı oluyor ama yetmiyor.
- **k'nın etkisi:** k = 12 neredeyse bütün pencereyi alıyor. k = 4 ilgili notların yarısını kaçırıyor. k = 8 [KARAR, tur 6] dengeli bir nokta.
- **Ablation'a etkisi:** „Bütün notlar“ ile „top-8“ arasındaki fark küçük bir bağlam farkı (~4 not), ama çeldirici sayısını yarıya indiriyor. Retrieval'ın modele katkısı değerlendirmede bu iki varyantla ölçülecek (CLAUDE.md 7, `06` D3).
- **Süre:** BGE-M3 işlemcide çalıştığı için 720 ayın üç yöntemle ölçümü ~53 dakika sürdü. Üretimde yalnızca bir yöntem kullanılır; `export` her ay için bir sorgu çalıştırır.
