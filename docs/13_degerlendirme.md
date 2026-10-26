# 13 — Değerlendirme: puanlama ve baseline sonuçları

> **Durum (26.10.2026):**
> - **Ablation tamamlandı (Bölüm 6):** RAG + FT format %97, işaretsiz neden 0,06/metin, kaynak precision/recall %75 / %59 (yalnızca RAG: %30, 1,01, %54 / %34). Zayıf nokta: V2'de notla açıklanacak aylar (1/17).
> - Puanlama 1.0 kodlandı (`scoring/`, `python -m scoring`, 8 test).
> - Kalibrasyon: ideal metinler plana dayalı ölçütlerde %100 alıyor.
> - Baseline'lar puanlandı: 3 varyant × 720 ay.
> - **Puanlama 1.1 (26.10.2026):** satır düzeyinde atıf ölçütü ve birden çok klasör (Bölüm 2, 1). 10 test. Baseline yeniden puanlandı; eski ölçütler değişmedi.
> - **[ÖNERİ]:** ölçütlerin tanımları ve eşikleri (bu belge).
> - **[AÇIK]:** üslup değerlendirmesi (CLAUDE.md 8).
>
> **İlgili:** CLAUDE.md 7–8 · `07_dogrulama_katmani.md` (Katman 4, v1.8) · `11_ideal_yorumlar.md` (içerik planı) · `12_egitim_verisi.md`, Bölüm 4 (Kaggle koşuları) · Karar kaydı: `00`, Bölüm 22

---

## 1. Puanlama nasıl çalışıyor

```
python -m scoring gpu/outputs/baseline_2026-10-24
  → gpu/outputs/baseline_2026-10-24/scores.jsonl   (metin başına puanlar)
  → gpu/outputs/baseline_2026-10-24/scores.md      (özet tablo: bütün küme, A1, A2/A3)
```

Klasördeki her `*.jsonl` bir sistemdir (ör. `baseline_rag_k8`).

**Birden çok klasör (1.1):** Ablation tablosu için ince ayarlı modellerin çıktıları ile baseline birlikte puanlanır. Puanlar ilk klasöre yazılır; aynı sistem adı iki klasörde olamaz.

```
python -m scoring gpu/outputs/eval_<tarih> gpu/outputs/baseline_2026-10-24
```

Her metin üç kaynağa karşı ölçülür:

| Kaynak | Ne verir | Bağımsız mı? |
|---|---|---|
| **Doğrulama katmanı** (Katman 4, v1.8) | Format, rakam değerleri ve biçimi, neden işaretleri, kelime sayısı | Evet: yalnızca facts.json ve verilen notlar |
| **İçerik planı** (`ideal/plan.py`, plan 1.5) | Modelin gördüğü notlarla hangi notlar kaynak gösterilmeli, hangi kalemler tabloda olmalı, V2 adayında doğru karar | Kısmen: ince ayar hedefleri de aynı plandan üretildi (Bölüm 5) |
| **Ground truth** | Beklenen ve kabul edilebilir çarpıklıklar, çeldirici notlar | Evet |

- **Görünen notlar:** Plan, modelin o varyantta gördüğü notlarla kurulur. Notlar test isteminin KONTEXTNOTIZEN bölümünden okunur. Bu yüzden aynı ay için `ohne_kontext`, `rag_k8` ve `rag_alle` planları farklıdır. Örneğin bağlamsız modelden hiçbir kaynak beklenmez.

## 2. Ölçütler [ÖNERİ]

| Ölçüt (rapordaki ad) | Tanım | CLAUDE.md 8 |
|---|---|---|
| Format uyumu | Doğrulamada biçim hatası (`FORMAT_CODES`) olmayan metin payı | Format uyumu |
| Hatasız metin | Hiç `fehler` bulgusu olmayan metin payı | — |
| Rakam sadakati (değer) | Denetlenen rakamlardan değeri facts.json'la ya da kaynak gösterilen notla örtüşenlerin payı. Biçim ayrı sayılır (v1.7) | Rakam sadakati |
| Binlik ayırıcı boşluk | „14 054 €“ yazan metin payı | (format) |
| Kelime | Tablo dışı kelime; hedef 250–350, rapor 200–400 arasını sayar | (format) |
| Neden cümlesi: kaynaklı / hipotez / işaretsiz | Doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları. „Ursache offen“ neden sayılmaz | Kaynaklı neden oranı; uydurma neden adayı |
| Kaynak isabeti (precision) | Gösterilen notlardan planın kaynak saydığı notların payı | Kaynaklı neden oranı |
| Kaynak kapsamı (recall) | Planın kaynak saydığı notlardan gösterilenlerin payı | — |
| Tablo atıfı doğru satırda (1.1) | Tablodaki her (satır, not) atıfından, notun planda o satırın kaynağı olduğu atıfların payı | Kaynaklı neden oranı |
| Yanlış satıra atıf (1.1) | Bir notu, planda açıklamadığı bir satırın nedeni yapan metin payı | Uydurma neden |
| Çeldirici nota atıf | Ground truth'taki çeldirici notlara yapılan atıf sayısı | Uydurma neden |
| Uydurma kaynak | Verilmemiş bir nota atıf yapan metin payı | Uydurma neden |
| Sapma yakalama (recall) | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı | Sapma yakalama |
| Gereksiz tablo satırı | Anlamlı, bayraklı ya da planda olmayan tablo satırı / metin | — |
| Uyarı kapsamı (Katman 1) | Katman 1'in `hinweis` bayraklarından Hinweise bölümünde adı geçenlerin payı | Çarpıklık uyarısı |
| Uyarı recall / precision (ground truth) | Beklenen çarpıklıklardan uyarılanlar / Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenler | Çarpıklık uyarısı isabeti |
| V2 adayı: doğru karar | Katman 1'in Rohertragsquote adayında plana göre doğru karar: notla açıkla ya da uyar (`either` ise ikisi de) | V2 adayı ayrımı |

**Ayrıntılar:**
- **Kaynak doğru mu:** Plan bir notu, olayı yıllık sapmanın en az %25'ini aynı yönde açıklıyorsa kaynak sayar (`CAUSE_SHARE`). Sapmanın küçük bir kısmını açıklayan not „yanlış“ sayılır; ölçüt katıdır.
- **Satır düzeyi (1.1):**
  - Not düzeyindeki precision yalnızca „bu not o ay bir şeyi açıklıyor mu“ diye bakar. Doğru bir notun yanlış satırın nedeni yapılmasını görmez.
  - Örnek: Sonderauftrag notu Umsatzerlöse için doğru kaynak, ama „Sonstige Kosten“ satırına da yazılmış (`docs/14`, 4.1).
  - Satır düzeyi ölçüt yalnızca tablo satırlarını sayar. Planda olmayan bir satıra yapılan atıf da yanlış sayılır.
- **Uyarının satırı:** Hinweise maddesinde adı geçen BWA satırları (kısa adlar dahil, `validation/config.toml`). „Rohertrag(squote)“ V2 satırlarına (malzeme, stok) sayılır.
- **V2 kararı:**
  - Model uyarıyor sayılır: Hinweise'de „Rohertrag“ geçiyorsa.
  - Model notla açıklıyor sayılır: planın Rohertragsquote satırı için öngördüğü nota atıf yapıyorsa.

## 3. Kalibrasyon: ideal metinler

İdeal (öğretmen) metinler, kendi doğrulama kümelerinde (`val_rag` 133, `val_ohne` 140; koşu `train_seed7`) puanlandı:

| Ölçüt | `ohne_kontext` | `rag_k8` |
|---|---:|---:|
| Format uyumu, hatasız metin, rakam sadakati | %100 | %100 |
| Binlik ayırıcı boşluk | %0 | %0 |
| Kelime (ort.) / 200–400 arası | 260 / %93 | 250 / %87 |
| Neden: kaynaklı / hipotez / işaretsiz | %0 / %100 / %0 | %42 / %58 / %0 |
| Kaynak precision / recall | – | %100 / %100 |
| Tablo atıfı doğru satırda / yanlış satıra atıf (1.1) | – / %0 | %100 / %0 |
| Sapma yakalama / gereksiz satır | %100 / 0 | %100 / 0 |
| Uyarı kapsamı (Katman 1) | %100 | %100 |
| Uyarı recall / precision (ground truth) | %84 / %82 | %85 / %86 |
| V2 doğru karar | %100 (98 ay) | %100 (97 ay; 14'ü notla) |

- Plana dayalı ölçütler ideal metinlerde tam puan veriyor; ölçütler beklendiği gibi çalışıyor.
- Ground truth'a göre uyarı isabetinin tavanı ~%85. Sınırı model değil, Katman 1 bayraklarının isabeti çiziyor (`docs/05`, Bölüm 7).

## 4. Baseline sonuçları (24.10.2026)

- **Koşu:** Kaggle, Ollama 0.40.10, `gemma4:e4b-it-q4_K_M`, deneme turu ayarları. 3 varyant × 720 ay, hata yok, ~2 saat (`12_egitim_verisi.md`, Bölüm 4).
- **Dosyalar:** Çıktılar ve puanlar `gpu/outputs/baseline_2026-10-24/`; tam tablo `scores.md`.

| Ölçüt | Çıplak model (`ohne_kontext`) | Yalnızca RAG (`rag_k8`) | Bütün notlarla RAG (`rag_alle`) | İdeal (tavan) |
|---|---:|---:|---:|---:|
| Format uyumu | %39 | %30 | %34 | %100 |
| Hatasız metin | %18 | %4 | %6 | %100 |
| Rakam sadakati (değer) | %95 | %94 | %93 | %100 |
| Binlik ayırıcı boşluk | %53 | %45 | %42 | %0 |
| Kelime (ort.) / 200–400 arası | 162 / %13 | 169 / %17 | 169 / %16 | 250–260 / ~%90 |
| Neden cümlesi / metin | 0,16 | 2,4 | 2,5 | 3,4–4,4 |
| … kaynaklı / hipotez / işaretsiz | %0 / %0 / %100 | %48 / %10 / %42 | %48 / %10 / %42 | işaretsiz %0 |
| Kaynak precision / recall | – | %54 / %34 | %55 / %30 | %100 / %100 |
| Tablo atıfı doğru satırda / yanlış satıra atıf (1.1) | – / %0 | %37 / %38 | %38 / %38 | %100 / %0 |
| Çeldirici nota atıf / uydurma kaynak | 0 / %0 | 2 / %0 | 2 / %1 | 0 / %0 |
| Sapma yakalama | %93 | %96 | %96 | %100 |
| Gereksiz tablo satırı / metin | 4,9 | 4,7 | 4,6 | 0 |
| Uyarı kapsamı (Katman 1) | %75 | %66 | %65 | %100 |
| Uyarı recall / precision (ground truth) | %66 / %86 | %64 / %85 | %62 / %85 | ~%85 / ~%84 |
| V2 doğru karar (439 ay) | %76 | %86 | %85 | %100 |
| … notla açıklanacak 17 ayda | – | %12 | %12 | %100 |

**Alt kümeler:**
- **A1 (yeni sektör):** Biçim daha zayıf (format %22–24, binlik boşluk %61–70). Kaynak isabeti biraz daha iyi (%56–58).
- **A2/A3 (yeni firma):** Format %34–46.
- Model henüz eğitilmediği için bu fark sektörden değil, verinin kendisinden geliyor. İnce ayardan sonra „öğretilmemiş sektör“ karşılaştırması anlam kazanacak.

### 4.1 Okuma

1. **Rakamların değeri büyük ölçüde doğru (%93–95).**
   - „Hesabı kod yapar“ ilkesi (CLAUDE.md 6.1) çıplak modelde bile işe yarıyor.
   - Kalan hatalar: rakamın yanlış satıra yazılması ve modelin kendi hesapladığı farklar (`zahl_falsche_position`, `zahl_unbelegt`).
2. **Biçim zayıf.** En sık sorunlar:
   - kısa metin (%83–87, hedefin altında);
   - binlik ayırıcı boşluk (%42–53);
   - RAG'de köşeli parantezli ama „Quelle:“ öneksiz kaynak (%40, `quellenformat`);
   - tabloya anlamsız ara toplamlar (metin başına ~4,7 gereksiz satır).
3. **Olgu ile tahmin ayrılmıyor (CLAUDE.md 6.1, ilke 3).**
   - Çıplak model neredeyse hiç neden söylemiyor; her satıra „Ursache offen“ yazıyor.
   - RAG'li model neden söylüyor, ama nedenlerin %42'si işaretsiz. „(Hypothese)“ yalnızca %10.
4. **RAG, notlara erişimi sağlıyor ama doğru notu seçmeyi sağlamıyor.**
   - Nedenlerin yarısı kaynaklı, ama gösterilen notların yalnızca %54'ü sapmayı gerçekten açıklıyor. Planın beklediği notların yalnızca üçte biri gösteriliyor.
   - Satır düzeyinde (1.1) daha da düşük: tablodaki atıfların %37'si doğru satırda. Metinlerin %38'i bir notu açıklamadığı bir satıra bağlıyor.
   - Okumada yanlış atıf türleri:
     - ters yönlü olay (personel azaltımı → personel gideri artışı);
     - önceki yılın aynı ayında zaten var olan olay;
     - ilgisiz not.
5. **Bütün notlar ile top-8 neredeyse aynı.** Recall top-8'de biraz daha yüksek (%34'e karşı %30). Getirmenin katkısı taban modelde küçük; ince ayarlı modelde yeniden ölçülecek.
6. **Uyarılar:**
   - Çıplak model Katman 1 bayraklarını daha sık aktarıyor (%75'e karşı %65–66); RAG bağlamı dikkati dağıtıyor olabilir.
   - Precision tavana yakın (%85–86): model uyarıları büyük ölçüde Katman 1'den alıyor.
7. **V2:** Uyarı gereken aylar çoğunlukla doğru, çünkü model Rohertragsquote'yi sık uyarıyor. Notla açıklanacak 17 ayın yalnızca 2'si doğru. Sayı küçük; dengelenmiş V2 kümesi (`v2_balanced_seed4242`) ince ayardan sonra ayrıca koşulacak.

**Sonuç:** Baseline, CLAUDE.md 7'deki beklentiyle uyumlu.
- Çıplak model yüzeysel.
- Yalnızca RAG bağlama erişiyor, ama olgu ile tahmini ayırmıyor ve biçim tutarsız.

İnce ayarın kapatması gereken açıklar şunlar: biçim (uzunluk, rakam ve kaynak biçimi, gereksiz satırlar), hipotez işareti ve doğru not seçimi.

## 5. Sınırlar ve dikkat

- **Plana dayalı ölçütler:**
  - Kaynak precision/recall, sapma yakalama, gereksiz satır ve V2, içerik planıyla uyumu ölçer.
  - İnce ayar hedefleri aynı planla üretildi. Bu yüzden ince ayarlı modeller bu ölçütlere doğrudan eğitilmiş olacak.
  - Raporlarda ground truth'a dayalı bağımsız ölçütler ayrıca verilir: uyarı recall/precision, çeldirici, uydurma kaynak.
- **Satır düzeyi atıf (1.1):** Yalnızca tablo satırları. Kernaussagen'deki bir cümlenin hangi satırı açıkladığı güvenilir biçimde okunamıyor; orada not düzeyi ölçüt geçerli.
- **Yön hataları:** „237.140 € … deutlich über dem Vormonatswert von 428.567 €“ gibi karşılaştırma sözcüğü hataları ölçülmüyor. Doğrulama yalnızca rakamın değerini ve farkların işaretini denetler (`docs/14`, 4.1).
- **Kelime listeleri:** Neden cümlesi tanıma doğrulamanın kelime listelerine dayanıyor (`validation/config.toml`). „Ursache offen“ gibi açık soru neden sayılmaz; bu yüzden çıplak modelin „işaretsiz %100“ü yalnızca 0,16 neden/metin üzerinden.
- **V2 notla açıklama:** Örnek az (17 ay). Dengelenmiş V2 kümesi ayrıca koşulacak.
- **Tek koşu:**
  - Her varyant bir kez üretildi (seed 42). Ollama eşzamanlı istemlerde tam deterministik değil.
  - Farklar küçükse (ör. top-8'e karşı bütün notlar) ihtiyatla yorumlanmalı. İleride önyükleme (bootstrap) güven aralığı eklenebilir.
- **Üslup:** Okunabilirlik otomatik ölçülmüyor ([AÇIK], CLAUDE.md 8).

## 6. Ablation sonuçları (26.10.2026)

- **Koşu:** Kaggle, llama-server (Ollama 0.40.10'un içindeki), aynı model dosyası, aynı istem ve örnekleme ayarları. 5 sistem × 720 ay, hata yok, 4,3 saat (`14_ince_ayar.md`, 4.2).
- **Dosyalar:** `gpu/outputs/eval_full_2026-10-26/` (çıktılar, log, `scores.md`). Puanlar baseline ile birlikte:

```
python -m scoring gpu/outputs/eval_full_2026-10-26 gpu/outputs/baseline_2026-10-24
```

### 6.1 Ana tablo: dört varyant (CLAUDE.md 7)

Test kümesinin 720 ayı. İdeal sütunu, öğretmen metinlerinin doğrulama kümesindeki puanı (Bölüm 3); tavanı gösterir.

| Ölçüt | Çıplak model | Yalnızca RAG | Yalnızca FT | **RAG + FT** | İdeal (tavan) |
|---|---:|---:|---:|---:|---:|
| Format uyumu | %39 | %30 | %100 | **%97** | %100 |
| Hatasız metin | %18 | %4 | %93 | **%82** | %100 |
| Rakam sadakati (değer) | %95 | %94 | %100 | **%99** | %100 |
| Binlik ayırıcı boşluk | %53 | %45 | %0 | **%0** | %0 |
| Kelime (ort.) / 200–400 arası | 162 / %13 | 169 / %17 | 257 / %86 | **249 / %81** | 250–260 / ~%90 |
| Neden cümlesi / metin | 0,16 | 2,4 | 2,1 | **3,6** | 3,4–4,4 |
| … kaynaklı / hipotez / işaretsiz | %0 / %0 / %100 | %48 / %10 / %42 | %0 / %100 / %0 | **%41 / %57 / %2** | %42 / %58 / %0 |
| İşaretsiz neden / metin | 0,16 | 1,01 | 0 | **0,06** | 0 |
| Kaynak precision / recall | – | %54 / %34 | – | **%75 / %59** | %100 / %100 |
| Tablo atıfı doğru satırda | – | %37 | – | **%64** | %100 |
| Yanlış satıra atıf (metin payı) | %0 | %38 | %0 | **%26** | %0 |
| Çeldirici nota atıf / uydurma kaynak | 0 / %0 | 2 / %0 | 0 / %0 | **3 / %1** | 0 / %0 |
| Sapma yakalama | %93 | %96 | %100 | **%100** | %100 |
| Gereksiz tablo satırı / metin | 4,9 | 4,7 | 0,08 | **0,07** | 0 |
| Uyarı kapsamı (Katman 1) | %75 | %66 | %100 | **%97** | %100 |
| Uyarı recall / precision (ground truth) | %66 / %86 | %64 / %85 | %84 / %88 | **%82 / %87** | ~%85 / ~%84 |
| V2 doğru karar (439 ay) | %76 | %86 | %100 | **%96** | %100 |
| … notla açıklanacak 17 ayda | – | %12 | – | **%6** | %100 |

Sistemler: `baseline_ohne_kontext`, `baseline_rag_k8`, `ft_ohne_ohne_kontext`, `ft_rag_rag_k8`.

### 6.2 Ek satırlar

| Ölçüt | RAG + FT bağlamsız | RAG + FT bütün notlar | Yalnızca RAG, bütün notlar | Taban model, llama-server (tutarlılık) |
|---|---:|---:|---:|---:|
| Format uyumu | %99 | %96 | %34 | %34 |
| Hatasız metin | %81 | %81 | %6 | %5 |
| Rakam sadakati | %100 | %99 | %93 | %94 |
| İşaretsiz neden / metin | 0,15 | 0,06 | 1,05 | 1,11 |
| Kaynak precision / recall | – | %74 / %55 | %55 / %30 | %57 / %35 |
| Tablo atıfı doğru satırda / yanlış satıra atıf | – / %0 | %64 / %28 | %38 / %38 | %38 / %38 |
| Uyarı recall / precision (ground truth) | %84 / %88 | %82 / %88 | %62 / %85 | %65 / %85 |
| V2 doğru karar | %99 | %96 | %85 | %88 |

Sistemler: `ft_rag_ohne_kontext`, `ft_rag_rag_alle`, `baseline_rag_alle`, `base_rag_k8`.

**Retrieval isabeti** (modelin gördüğü notlar; `python tools/retrieval_quality.py data/synthetic/reference_seed42 --prompts gpu/data/test_rag_k8.jsonl.gz gpu/data/test_rag_alle.jsonl.gz`):

| Bağlam | Recall çekirdek | Recall geniş | Çeldirici payı | Ort. not |
|---|---:|---:|---:|---:|
| Top-8 (`rag_k8`) | %91,4 | %83,2 | %5,2 | 8,0 |
| Bütün notlar (`rag_alle`) | %100 | %100 | %11,3 | 12,2 |

### 6.3 Alt kümeler: yeni sektör ve yeni firma

| Ölçüt (RAG + FT) | A1, yeni sektör (240 ay) | A2/A3, yeni firma (480 ay) |
|---|---:|---:|
| Format uyumu | %99 | %96 |
| Hatasız metin | %83 | %81 |
| Rakam sadakati | %100 | %99 |
| Kaynak precision / recall | %76 / %58 | %75 / %60 |
| Tablo atıfı doğru satırda | %66 | %62 |
| Uyarı recall (ground truth) | %84 | %82 |

Yalnızca FT'de de tablo aynı: A1'de hatasız %93, A2/A3'te %92.

### 6.4 Okuma

1. **CLAUDE.md 7'deki beklenti büyük ölçüde doğrulandı.**

   | Varyant | Beklenti | Gözlem |
   |---|---|---|
   | Çıplak model | Yüzeysel, format tutarsız, nedenleri uydurur | Yüzeysel ve format tutarsız (%39). Ama neden **uydurmuyor**: neredeyse hiç neden söylemiyor (0,16/metin), her satıra „Ursache offen“ yazıyor. |
   | Yalnızca RAG | Bağlama erişir; dağınık, tutarsız format; olgu ile tahmini ayırmaz | Doğru. Nedenlerin %48'i kaynaklı, ama %42'si işaretsiz. Format %30. |
   | Yalnızca FT | Tutarlı üslup; firma bağlamını bilmez; nedenleri uydurur | Tutarlı (format %100, hatasız %93). Bağlamı bilmiyor. Ama nedenleri **uydurmuyor**: bütün nedenler „(Hypothese)“ ile işaretli. |
   | RAG + FT | Doğru bağlam + tutarlı üslup + kaynak | Doğru. En yüksek kaynak isabeti ve kapsamı, işaretsiz neden 0,06/metin, format %97. |

   İki „uydurur“ beklentisi tutmadı. Çıplak model bilmediği nedeni söylemiyor. Yalnızca FT modeli ise B3 kuralıyla (tur 6) üretilmiş hedeflerden notsuz nedeni hipotez olarak işaretlemeyi öğrenmiş.
2. **İki bileşenin katkısı ayrı ayrı görünüyor.**
   - **İnce ayar yapıyı ve işaretlemeyi getiriyor:**
     - format %30–39 → %97–100;
     - gereksiz satır 4,7 → 0,1;
     - binlik boşluk %45–53 → %0;
     - işaretsiz neden 1,01 → 0,06 metin başına;
     - Katman 1 bayraklarının hepsi Hinweise'de.
   - **RAG kaynaklı nedeni getiriyor.** Yalnızca FT modeli hiçbir nedeni kaynağa bağlayamıyor.
   - **Kaynak seçimi:** İkisi birlikte, RAG'in tek başına bulduğundan daha iyi kaynak seçiyor:
     - precision %54 → %75;
     - recall %34 → %59;
     - doğru satırda atıf %37 → %64.
3. **Öğretilmemiş sektöre genelleme var (Bölüm 6.3).** A1 eğitimde hiç görülmedi. Bütün ölçütler A2/A3 ile aynı düzeyde, bazıları biraz daha iyi. Model, firmaya özgü bilgiyi değil davranışı öğrenmiş (CLAUDE.md 6.1, ilke 2).
4. **Retrieval'ın katkısı küçük ama tutarlı.**
   - Top-8 ile bütün notlar karşılaştırması:
     - RAG + FT'de recall %59'a karşı %55;
     - taban modelde %34'e karşı %30.
   - Top-8, ilgili notların %91'ini getiriyor ve çeldirici payını yarıya indiriyor.
   - Fark küçük, çünkü 13 aylık pencere de küçük (~12 not).
5. **„RAG + FT bağlamsız“ ek satırı tur 12 kararını destekliyor.** Ayrı eğitilen yalnızca FT modeli daha iyi: hatasız %93'e karşı %81, işaretsiz neden 0'a karşı 0,15. RAG modeli not görmeyince kendi hesapladığı rakamlar ve işaretsiz nedenler üretiyor.
6. **Motor tutarlılığı:** Taban model llama-server'da Ollama baseline'ıyla aynı aralıkta:
   - format %34 / %30;
   - rakam %94 / %94;
   - kaynak %57 / %54 (precision) ve %35 / %34 (recall);
   - V2 %88 / %86.

   İnce ayarlı modellerdeki fark motordan gelmiyor.

### 6.5 RAG + FT'nin kalan zayıflıkları

1. **V2: notla açıklanacak aylarda model her zaman uyarıyor.**
   - Test kümesindeki 17 ayın 17'sinde uyarı var, 4'ünde not da gösteriliyor. Yalnızca 1 ay doğru: o ayda ikisi de kabul ediliyor.
   - **Neden:** Eğitim verisinde 623 V2 adayı ayın yalnızca 33'ü (%5) notla açıklanıyordu (`train_price_boost` profiline rağmen). Model baskın kararı öğrenmiş.
   - Dengelenmiş V2 kümesi (147 ay, `cite` = `warn`) şimdilik koşulmuyor (tur 13).
2. **Notu yanlış satıra bağlamak:**
   - metinlerin %26'sı (yalnızca RAG'de %38);
   - örnek: tek bir „Sonderauftrag“ notunun gelir, malzeme ve diğer giderlerin hepsine yazılması (`14_ince_ayar.md`, 4.1).
3. **Rakam hataları:** Metinlerin %12'sinde en az bir rakam hatası var (yalnızca FT: %7); rakamların %99'u doğru. „Hatasız metin“ %82'nin geri kalanı işaretsiz neden (25 metin) ve kaynak biçimi (21 metin). Rakam hatası türleri:
   - sonuç satırında kopyalama hatası;
   - normal düzeye göre kendi hesapladığı fark („Normalniveau 4.492 € | +15.908 € (+450,0 %)“);
   - facts'te `null` olan yüzdeyi kendisi hesaplaması.

   Bunların hepsi Katman 4'ün işaretlediği türler. İnsan onayından önce uyarı listesinde görünüyorlar (CLAUDE.md 6.1, ilke 4).
4. **Uzunluk:** Metinlerin %19'u 200 kelimenin altında, 400'ün üstünde neredeyse hiç yok (%0,4). Doğrulamada `hinweis`, hata değil.

## 7. Sıradaki

1. ~~İnce ayar defteri (paket 7)~~ ✅ yalnızca FT (`train_ohne`) ve RAG + FT (`train_rag`).
2. ~~İnce ayarlı modellerin değerlendirmesi~~ ✅ (Bölüm 6).
3. ~~Dengelenmiş V2 kümesi~~: şimdilik koşulmuyor (tur 13; `00`, Bölüm 28).
4. ~~Retrieval isabeti tabloya~~ ✅ (Bölüm 6.2).
5. Üslup değerlendirmesi kararı ([AÇIK]).
6. ~~İkinci eğitim turu~~: yapılmıyor (tur 13). V2 zayıflığı model kartında sınır olarak yazılı (`release/huggingface/README.md`).
