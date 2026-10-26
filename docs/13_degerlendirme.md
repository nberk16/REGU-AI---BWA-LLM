# 13 — Değerlendirme: puanlama ve baseline sonuçları

> **Durum (24.10.2026):**
> - Puanlama 1.0 kodlandı (`scoring/`, `python -m scoring`, 8 test).
> - Kalibrasyon: ideal metinler plana dayalı ölçütlerde %100 alıyor.
> - Baseline'lar puanlandı: 3 varyant × 720 ay.
> - **[ÖNERİ]:** ölçütlerin tanımları ve eşikleri (bu belge).
> - **[AÇIK]:** üslup değerlendirmesi (CLAUDE.md 8).
>
> **İlgili:** CLAUDE.md 7–8 · `07_dogrulama_katmani.md` (Katman 4, v1.7) · `11_ideal_yorumlar.md` (içerik planı) · `12_egitim_verisi.md`, Bölüm 4 (Kaggle koşuları) · Karar kaydı: `00`, Bölüm 22

---

## 1. Puanlama nasıl çalışıyor

```
python -m scoring gpu/outputs/baseline_2026-10-24
  → gpu/outputs/baseline_2026-10-24/scores.jsonl   (metin başına puanlar)
  → gpu/outputs/baseline_2026-10-24/scores.md      (özet tablo: bütün küme, A1, A2/A3)
```

Klasördeki her `*.jsonl` bir sistemdir (ör. `baseline_rag_k8`). Her metin üç kaynağa karşı ölçülür:

| Kaynak | Ne verir | Bağımsız mı? |
|---|---|---|
| **Doğrulama katmanı** (Katman 4, v1.7) | Format, rakam değerleri ve biçimi, neden işaretleri, kelime sayısı | Evet: yalnızca facts.json ve verilen notlar |
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
| Çeldirici nota atıf | Ground truth'taki çeldirici notlara yapılan atıf sayısı | Uydurma neden |
| Uydurma kaynak | Verilmemiş bir nota atıf yapan metin payı | Uydurma neden |
| Sapma yakalama (recall) | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı | Sapma yakalama |
| Gereksiz tablo satırı | Anlamlı, bayraklı ya da planda olmayan tablo satırı / metin | — |
| Uyarı kapsamı (Katman 1) | Katman 1'in `hinweis` bayraklarından Hinweise bölümünde adı geçenlerin payı | Çarpıklık uyarısı |
| Uyarı recall / precision (ground truth) | Beklenen çarpıklıklardan uyarılanlar / Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenler | Çarpıklık uyarısı isabeti |
| V2 adayı: doğru karar | Katman 1'in Rohertragsquote adayında plana göre doğru karar: notla açıkla ya da uyar (`either` ise ikisi de) | V2 adayı ayrımı |

**Ayrıntılar:**
- **Kaynak doğru mu:** Plan bir notu, olayı yıllık sapmanın en az %25'ini aynı yönde açıklıyorsa kaynak sayar (`CAUSE_SHARE`). Sapmanın küçük bir kısmını açıklayan not „yanlış“ sayılır; ölçüt katıdır.
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
- **Kelime listeleri:** Neden cümlesi tanıma doğrulamanın kelime listelerine dayanıyor (`validation/config.toml`). „Ursache offen“ gibi açık soru neden sayılmaz; bu yüzden çıplak modelin „işaretsiz %100“ü yalnızca 0,16 neden/metin üzerinden.
- **V2 notla açıklama:** Örnek az (17 ay). Dengelenmiş V2 kümesi ayrıca koşulacak.
- **Tek koşu:**
  - Her varyant bir kez üretildi (seed 42). Ollama eşzamanlı istemlerde tam deterministik değil.
  - Farklar küçükse (ör. top-8'e karşı bütün notlar) ihtiyatla yorumlanmalı. İleride önyükleme (bootstrap) güven aralığı eklenebilir.
- **Üslup:** Okunabilirlik otomatik ölçülmüyor ([AÇIK], CLAUDE.md 8).

## 6. Sıradaki

1. İnce ayar defteri (paket 7): yalnızca FT (`train_ohne`) ve RAG + FT (`train_rag`).
2. İnce ayarlı modellerin aynı Ollama düzeninde koşulması ve aynı puanlamayla karşılaştırılması: dört varyant + ek satırlar (RAG + FT bağlamsız, RAG + FT bütün notlar).
3. Dengelenmiş V2 kümesi ve retrieval isabeti (recall@k) tabloya eklenir.
4. Üslup değerlendirmesi kararı ([AÇIK]).
