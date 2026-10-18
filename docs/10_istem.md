# 10 — İstem (sürüm 1.1)

> **Durum:** İstem 1.1 kodlandı (`prompting/`, 7 test), 18.10.2026.
> - **[KARAR]** (önceki turlardan): çıktı yapısı 6.3 (tur 6); notsuz nedende açık soru ya da işaretli hipotez (tur 6, B3); nottaki rakam kaynakla birlikte (tur 2); 13 aylık pencere + top-8 (turlar 4, 6).
> - **[ÖNERİ]:** istem metni, varyantlar, facts'in model görünümü, „WISSEN kaynak değildir“ kuralı (bu belge).
>
> **İlgili:** `08_deneme_turu.md` (istem 1.0 ve sonuçları) · `trial/review.md` (dersler) · `09_bilgi_tabani.md` (bağlam) · `07_dogrulama_katmani.md` (denetim) · Karar kaydı: `00`, Bölüm 17

---

## 1. Neden yeni bir sürüm?

- **Katman 2 hazır.** İstem artık getirilen bağlamı taşıyor: K-B rehberi, K-A açıklamaları, seçilen notlar (`docs/09`).
- **Deneme turu dersleri.** Üç modelde ortak hatalar vardı: FACTS'i kaynak gösterme, kendi yüzde hesabı, `(Hypothese)` işaretinin kullanılmaması, yön hataları (`trial/review.md`). Fine-tuning bunları zaten öğretecek. Ama istem ne kadar açıksa baseline'lar o kadar adil olur ve ideal yorumların öğretmen modeli de aynı kuralları görür.
- **1.0 dondurulur.** Deneme turu girdileri, modellerin gördüğü hâliyle kalır (`prompting/v1_0.py`; test birebir aynılığı denetler).

Baseline'lar, ideal yorumlar (öğretmen modelin girdisi) ve fine-tuning bu istemi kullanır. Her değişiklik `PROMPT_VERSION`'ı artırır.

## 2. Değişiklikler: ders → kural

| Deneme turunda görülen (`trial/review.md`) | 1.1'deki karşılığı |
|---|---|
| „FACTS“ ya da bayrak kodları kaynak gibi gösteriliyor (üç model) | Kural 4: FACTS'ten gelen rakam kaynak istemez. `[Quelle: …]` içinde yalnızca not kimlikleri olur; FACTS, flags ve WISSEN hiçbir zaman olmaz. |
| Yüzdeler modelce hesaplanıyor (Qwen: „+229,1 %“, FACTS'te `null`) | Kural 1: kendi farkı, yüzdesi, payı, toplamı yok. FACTS'te `null` olan değer için rakam verilmez. |
| Yüzde ile yüzde puanı karışıyor (Gemma) | Kural 2: oranlar yüzde, oran farkları (`delta_pp`) yüzde puanıdır. |
| Yön ters okunuyor: −5,6 puanlık düşüş „iyileşme“; alış zammı „marja olumlu“ | Kural 3: yön FACTS'teki işaretten okunur; maliyet artışı sonucu kötüleştirir. Fiyatların oranlara etkisi WISSEN'de (K-A, `docs/09` Bölüm 1). |
| İlgisiz ya da çeldirici not neden olarak gösteriliyor (Qwen, 3 kez) | Kural 5: not yalnızca satırı, dönemi ve yönü uyuyorsa kaynaktır. Ayrıca top-8 çeldirici payını yarıya indiriyor (`docs/09`, 5.3). |
| `(Hypothese)` neredeyse hiç kullanılmıyor | Kural 5: uygun not yoksa „Ursache offen“ + soru ya da `(Hypothese)`. Hipotez yalnızca FACTS, flags ve WISSEN'den türetilir (B3). K-B rehberi tipik nedenleri veriyor. |
| Totoloji: „Erklärung: gegenüber Vorjahresmonat gestiegen“ (Gemma) | Kural 5: açıklama bir neden söyler, sapmayı tekrarlamaz. |
| Kalın yazı, ayırıcı çizgi (Ministral) | Kural 8: başka başlık, çizgi ya da vurgu yok. |
| `hinweis` bayrağında soru eksik | Kural 7: uyarıya bir soru eklenir (K-B „Grundsätze“ ile aynı). |
| Kısa metinler (Gemma medyan 167 kelime) | Kural değişmedi (250–350). Bunu fine-tuning öğretecek. |

Kural sayısı 7'den 8'e çıktı (yön ayrı bir kural oldu). Çıktı şablonu 1.0 ile aynı; yalnızca tablo örneğindeki açıklama hücresi „Ursache oder „Ursache offen““ oldu.

## 3. Model girdisi

**Sistem mesajı:** Rol, üç girdi (FACTS, WISSEN, KONTEXTNOTIZEN), 8 kural, çıktı şablonu (CLAUDE.md 6.3). Kernaussagen başlığı ayın adıyla doldurulur. Bütün varyantlarda aynıdır.

**Kullanıcı mesajı:**

```
FACTS:
```json
{…}                                        ← facts.json'un model görünümü
```

WISSEN:
- Leitfaden Grundsätze: …                  ← K-B: Grundsätze + her bayrak kuralı
- Leitfaden V1 (fehlende Abgrenzung): …
- BWA-Erläuterung Personalkosten: …        ← K-A: anlamlı kalemler, bayraklı satırlar, anlamlı oranlar

KONTEXTNOTIZEN:
- [Firmenprofil] dauerhaft: …              ← firmada varsa (varyantların ~%70'i; docs/03)
- [Kontextnotiz 2025-06 #2] 2025-06, temporär: …   ← top-8, kronolojik

Schreibe jetzt den Kommentar für Muster GmbH, Juni 2025.
```

**Biçim farkı bilinçli:** Notlar köşeli parantezli kimlikle (`[Kontextnotiz …]`), WISSEN parçaları parantezsiz (`Leitfaden …:`) yazılır. Böylece yalnızca notların atıf yapılabilir kaynak olduğu biçimden de belli olur.

**facts.json'un model görünümü** (`prompting.model_facts`) [ÖNERİ]:
- Çıkarılan alanlar: `schema_version`, `thresholds`, her kalemdeki `significance` ve makine anahtarı `key`.
- **Gerekçe:**
  - Model bu alanları kullanmaz. Kalemin anlamlı olduğu, `positions` listesinde yer almasından zaten belli.
  - Eşik metnindeki rakamlar („Schwelle: ≥ 10,0 % und ≥ 4.355 €“) modelin yanlışlıkla aktarabileceği rakamlardır.
  - İstem ~%15 kısalır (Bölüm 6).
- Bütün tutarlar, karşılaştırmalar, oranlar ve bayraklar olduğu gibi kalır. Doğrulama her zaman tam `facts.json` ile yapılır.

## 4. Varyantlar (ablation, CLAUDE.md 7) [ÖNERİ]

| Varyant | Kullanıcı mesajı | Kullanıldığı yer |
|---|---|---|
| `ohne_kontext` | FACTS; WISSEN ve KONTEXTNOTIZEN „Keine.“ | Çıplak model; yalnızca fine-tuning |
| `rag_k8` | FACTS + WISSEN + Firmenprofil + top-8 not | Yalnızca RAG; RAG + fine-tuning |
| `rag_alle` | FACTS + WISSEN + Firmenprofil + penceredeki bütün notlar | Retrieval'ın katkısı (`docs/09`, 5.3) |

- **Sistem mesajı her varyantta aynı.** Varyantlar yalnızca bağlamda ayrılır; sonuçtaki fark bağlama bağlanabilir.
- **Bağlamsız varyant** CLAUDE.md 7'deki tanıma uyar: model firma bağlamını bilmez. „Keine.“ yazılması, modelin nedenleri kaynaktan değil, hipotez ya da soru olarak vermesi gerektiğini açıkça gösterir.
- **Açık nokta (paket 7):** „Yalnızca fine-tuning“ modelinin hangi girdi–hedef çiftleriyle eğitileceği henüz kararlaştırılmadı (bkz. `yol_haritasi.md`, paket 7).

## 5. Kullanım

```bash
python -m rag export --run data/synthetic/reference_seed42                       # bağlam: <run>/rag/retrieval.jsonl (top-8)
python -m rag export --run data/synthetic/reference_seed42 --k 0 --out …/retrieval_alle.jsonl   # bütün notlar
python -m prompting --run data/synthetic/reference_seed42                        # → <run>/prompts/ohne_kontext.jsonl
python -m prompting --run data/synthetic/reference_seed42 --retrieval data/synthetic/reference_seed42/rag/retrieval.jsonl   # → rag_k8.jsonl
python -m validation --text yorum.md --run … --firm A1-v00 --period 2025-06 --retrieval …/retrieval.jsonl
```

- İstem kaydı: `id`, `firm_id`, `period`, `prompt_version`, `variant`, `messages`.
- Kaggle defterleri bu dosyaları okur; GPU tarafında `facts` ve embedding hesaplamak gerekmez. `prompts/` ve `rag/` klasörleri repoda tutulmaz; her zaman yeniden üretilebilir.
- `rag export --firms …` yalnızca seçilen firmaları yazar (ör. doğrulama varyantları).
- Doğrulamada `--retrieval` verilirse „modele verilen notlar“ getirilen notlardır; verilmezse 13 aylık penceredeki bütün notlar.

## 6. İstem uzunluğu

Ölçüm: doğrulama varyantları (A2/A3 v120–v122, 144 firma-ay), BGE-M3 ile getirme. Token tahmini: deneme turunda Gemma'nın tokenizer'ı bu tür istemlerde token başına ~2,75 karakter saydı.

| İstem | Medyan karakter | En fazla | Medyan token (tahmini) | En fazla token (tahmini) |
|---|---:|---:|---:|---:|
| 1.0 (deneme turu: tam facts + penceredeki bütün notlar) | 10.162 | 12.500 | ~3.700 | ~4.550 |
| 1.1 `ohne_kontext` | 8.934 | 10.533 | ~3.250 | ~3.830 |
| 1.1 `rag_k8` | 14.514 | 18.558 | ~5.300 | ~6.750 |
| 1.1 `rag_alle` | 15.139 | 18.933 | ~5.500 | ~6.900 |

`rag_k8` isteminin bileşenleri (medyan karakter): sistem mesajı 3.576, FACTS 5.242, WISSEN 4.470, notlar 1.244.

**Yorum:**
- **En büyük yeni parça WISSEN** (~1.600 token). Notlar kısa; top-8 ile bütün notlar arasındaki fark ~600 karakter.
- **Model görünümü** facts kısmını kısaltıyor: bağlamsız 1.1, 1.0'dan ~%12 kısa. Bu fark, yeni kuralların eklediği uzunluğu karşılıyor.
- **Bağlam penceresi:** Girdi en fazla ~6.900 token, çıktı ~600–1.500 token. Kaggle'daki çıkarım ve eğitimde en az ~10.000 token'lık pencere gerekir [ÖNERİ: 12.288]. Gemma 4 E4B'nin penceresi bundan çok büyük; T4 belleğine sığması eğitimde denenerek doğrulanacak.
- **Dizüstünde demo:** Gemma deneme turunda istemi saniyede ~11–14 token okudu. `rag_k8` istemi yalnızca okumada ~6–8 dakika sürer. Gerekirse WISSEN kısaltılabilir; örneğin K-A yalnızca oranlar ve bayraklı satırlar için verilir. Bu ayar ablation sonuçlarına göre yapılır.

## 7. Doğrulama katmanıyla ilişki (`docs/07`, Bölüm 11)

- **Yeni bulgu `quelle_wissen` (hinweis):** `[Quelle: Leitfaden …]`, `[BWA-Erläuterung …]` ya da `WISSEN` atfı tanınır. Bilinmeyen kaynak hatası (`quelle_unbekannt`) vermez, ama neden **kaynaklı sayılmaz**.
  - Böyle bir cümle `(Hypothese)` taşımıyorsa olağan `begruendung_ohne_kennzeichnung` hatası verilir.
  - Gerekçe: WISSEN firma hakkında bilgi değil. Ondan türetilen neden, B3'e göre bir hipotezdir. „Kaynaklı neden oranı“ metriği yalnızca firma notlarını sayar (CLAUDE.md 8).
- `quelle_facts` ile aynı mantık: ikisi de içerik hatası değil, ipucudur.

## 8. Deneme turu girdileri ve isteğe bağlı karşılaştırma

- `trial/inputs/cases.jsonl` istem 1.0 ile dondurulmuş kalır. `trial/prepare.py` dondurulmuş `prompting/v1_0.py`'yi kullanır.
- `python trial/prepare.py --retrieval FILE` aynı 10 ay için güncel istemle `trial/inputs/cases_1_1.jsonl` yazar. Bağlam BGE-M3 ile getirilir.
  - Not metinleri güncel veriden gelir: E04/E05 kalıpları tur 9'da netleşti. 1.0 girdileriyle fark yalnızca o notlarda.
- **İsteğe bağlı [ÖNERİ]:** Kullanıcı aynı 10 örneği Gemma ile istem 1.1'de çalıştırabilir (~1,5 saat; `trial/README.md`, Bölüm 6). Bu, 1.0'a göre kaynak gösterme ve hesaplama hatalarının istemle ne kadar azaldığını gösteren küçük bir ön kontrol olur; asıl ölçüm Kaggle'daki baseline'lardır.
  - Üretim ayarları 1.0 turuyla aynı kalır (`num_ctx 8192`). En uzun örnek ~6.300 token; 1.500 token'lık çıktıyla birlikte pencereye sığar.

```
python trial/run_ollama.py --models gemma4-e4b --cases trial/inputs/cases_1_1.jsonl --out trial/outputs_1_1
python trial/score.py --cases trial/inputs/cases_1_1.jsonl --outputs trial/outputs_1_1 --report trial/results_1_1.md --review trial/review_1_1.md
```
