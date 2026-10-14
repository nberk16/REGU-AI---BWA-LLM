# 03 — Olay kataloğu (ground truth)

> **Kapsam:** CLAUDE.md Bölüm 12, adım 3 · **Tarih:** 14.10.2026
>
> **Etiket kuralı:** `01_firma_profili.md` ile aynı. Başlıklardaki seçimler [KARAR], sayısal parametreler (büyüklükler, sıklıklar, oranlar) [ÖNERİ].

---

## 1. Amaç: hangi model davranışı test ediliyor?

Proje LLM odaklı (CLAUDE.md G7). Olay kataloğu, modelin karşılaşacağı durumları tanımlar. Her durum, Katman 3'te öğretilen bir davranışa ve Bölüm 8'deki bir metriğe karşılık gelir.

| Durum | Beklenen model davranışı | Üreten olaylar | Metrik (CLAUDE.md 8) |
|---|---|---|---|
| Bağlam notunda geçen gerçek olay | Nedeni kaynak atfıyla verir (`[Quelle: Kontextnotiz …]`) | E01–E12, E19 (notlu olanlar) | Kaynaklı neden oranı |
| Bağlam notunda geçmeyen gerçek olay | Nedeni olgu gibi sunmaz; "vermutlich" / "Hypothese" der veya açık soru sorar | E01–E12, E19 (notsuz olanlar) | Uydurma neden oranı |
| Muhasebe çarpıklığı | Olgu yerine uyarı dili kullanır; Buchhaltung'a açık soru sorar | E13–E18 | Çarpıklık uyarısı isabeti |
| Sezon | Önceki yılın aynı ayıyla karşılaştırarak normal olduğunu söyler, alarm vermez | E19 | Çarpıklık uyarısı isabeti (V6), uydurma neden oranı |
| Olaysız ay | Neden uydurmaz | ~%15 ay (Bölüm 4) | Uydurma neden oranı |
| Çeldirici not | Notu ilgisiz bir sapmaya bağlamaz | Bölüm 5.3 | Uydurma neden oranı |
| Hepsi | Önemli sapmaları atlamaz, yalnızca `facts.json`'daki rakamları kullanır | – | Sapma yakalama, rakam sadakati |

---

## 2. Kategoriler

| Kategori | Anlamı |
|---|---|
| **R** | Gerçek ekonomik gelişme (işe alım, fiyat, sipariş, yatırım …) |
| **V1–V6** | CLAUDE.md 5.4'teki çarpıklıklar: V1 eksik tahakkuk, V2 girilmemiş stok değişimi, V3 yıl sonu AfA, V4 zamanlama kayması, V5 tek seferlik etki, V6 sezon |

V5 ve V6 gerçek etkilerdir ve bağlam notlarında geçebilir. V1–V4 ise muhasebe kaynaklıdır; bağlam notlarında **hiç** geçmez (Bölüm 5).

---

## 3. Katalog [KARAR: E1 = A, 19 tür]

Büyüklükler, ilgili satırın aylık taban değerine göredir [ÖNERİ].

| ID | Olay | Kat. | Satır(lar) | Etki biçimi | Büyüklük | Arketip | Notlanabilir | Beklenen bayrak |
|---|---|---|---|---|---|---|---|---|
| E01 | Neueinstellungen | R | Personalkosten | kalıcı basamak | +%2 … +8 | hepsi | evet | – |
| E02 | Personalabgang | R | Personalkosten | kalıcı basamak | −%2 … −6 | hepsi | evet | – |
| E03 | Tariferhöhung / Lohnrunde | R | Personalkosten | kalıcı basamak; her yıl, arketipe göre sabit bir ayda | +%2,5 … +5,5 | hepsi | evet | – |
| E04 | Materialpreiserhöhung | R | Material-/Wareneinkauf → Rohertragsquote | kalıcı ya da 3–6 ay | Materialquote +2 … +6 puan | hepsi | evet | – |
| E05 | Verkaufspreiserhöhung | R | Umsatzerlöse → Rohertragsquote ↑ | kalıcı basamak (hacim sabit) | +%2 … +6 | hepsi | evet | – |
| E06 | Großauftrag | R | Umsatzerlöse, Material (oransal) | 1–3 ay | Umsatz +%10 … +30 | hepsi | evet | – |
| E07 | Kundenverlust / Auftragsrückgang | R | Umsatzerlöse, Material (oransal) | kalıcı basamak | −%5 … −15 | hepsi | evet | – |
| E08 | Investition, kreditfinanziert | R | Abschreibungen, Zinsaufwand | kalıcı basamak | AfA +%10 … +30; faiz +%10 … +40 | A1, A3 (A2: depo/araç) | evet | – |
| E09 | Mieterhöhung / zusätzliche Halle | R | Raumkosten | kalıcı basamak | +%8 … +30 | hepsi (seri boyunca en fazla 1) | evet | – |
| E10 | Einmaliger neutraler Ertrag (ör. Anlagenverkauf) | R | Sonstiger neutraler Ertrag | tek ay | aylık Umsatz'ın %0,5 … 3'ü | hepsi | evet | – (Betriebsergebnis etkilenmez) |
| E11 | Messeteilnahme | V5 | Werbe-/Reisekosten | 1–2 ay | taban × 2 … 5 | A1, A3 (A3'te her yıl aynı ay) | evet | V5 |
| E12 | Große Reparatur | V5 | Reparatur/Instandhaltung | tek ay | taban × 3 … 8 | hepsi | evet | V5 |
| E13 | Urlaubsgeld ohne Abgrenzung | V1 | Personalkosten | her yıl Haziran | +%30 … +60 | P1 olan varyantlar | **hayır** | V1 |
| E14 | Weihnachtsgeld ohne Abgrenzung | V1 | Personalkosten | her yıl Kasım | +%50 … +90 | P1 olan varyantlar | **hayır** | V1 |
| E15 | Jahresversicherungsprämie | V1 | Versicherungen/Beiträge | her yıl Ocak | yıllık ortalamanın × 5 … 8'i | P2 olan varyantlar | **hayır** | V1 |
| E16 | Bestandsveränderung nicht gebucht | V2 | Bestandsveränd. FE/UE (A2: Material-/Wareneinkauf) → Rohertragsquote | **sistematik** (P3) veya **epizodik** (unutulur, ertesi ay telafi edilir) | gerçek stok değişiminin tamamı | hepsi (01, Bölüm 4) | **hayır** | V2; epizodik türde telafi ayında V4. A2'de V2 farklı bir kuralla tespit edilir (Bölüm 9.1). |
| E17 | AfA nur zum Jahresende | V3 | Abschreibungen | Ocak–Kasım 0, Aralık'ta yıllık toplam | – | P4 olan varyantlar | **hayır** | V3 |
| E18 | Verspätete Eingangsrechnungen | V4 | Material-/Wareneinkauf veya Sonstige Kosten | t ayında −X, t+1 ayında +X | X = tabanın %15 … 40'ı | P5'e göre | **hayır** | V4 (t+1 ayında tespit edilebilir) |
| E19 | Saisonmuster (Betriebsferien dahil) | V6 | Umsatz ve oransal satırlar | yıllık desen | 01, Bölüm 3.3 | hepsi | evet (dönemsiz firma notu) | V6 (önceki aya göre sapma büyük, önceki yılın aynı ayına göre normal) |

**Kapsam dışı bırakılanlar** (ileride eklenebilir):
- Energiepreisanstieg
- Leasingfahrzeuge
- Kurzarbeit
- Beratungskosten
- BG-Beitrag
- Kfz-Steuer
- Steuervorauszahlungen
- verspätete Ausgangsrechnungen

---

## 4. Sıklık ve yoğunluk [KARAR: E3 = B; sayılar ÖNERİ]

**Havuz olayları:** E01–E12, E16 (epizodik) ve E18. Varyant başına yıllık sıklıklar:

| ID | Yılda | ID | Yılda |
|---|---|---|---|
| E01 | 2–4 | E08 | 0–1 |
| E02 | 1–2 | E09 | seri boyunca 0–1 |
| E03 | 1 (sabit ay) | E10 | 0–1 |
| E04 | 1–2 | E11 | 1–2 |
| E05 | 0–1 | E12 | 2–3 |
| E06 | 2–3 | E16 epizodik | 0–2 |
| E07 | 0–1 | E18 | 0–6 (P5'e göre) |

- Ortalama yaklaşık **21 havuz olayı/yıl ≈ 1,8/ay**.
- Bu sıklık, **ayların ~%15'inde yeni olay olmaması** sonucunu verir ("olaysız ay").
- Pratiklerden doğan desenler (E13–E15, sistematik E16, E17) ve sezon (E19) bu sayıya dahil değildir.
- "Olaysız ay" yeni olay olmadığı anlamına gelir. Önceki aylardaki kalıcı olayların etkisi sürebilir; ground truth bunları "aktif olaylar" olarak listeler.

**Çakışma (D8):**
- Aynı ay ve aynı satırda en fazla 2 olay olabilir.
- Olayların ~%10'u bir başka olayla çakışır (ör. Nisan'da E01 + E03 ikisi de Personalkosten'te).

---

## 5. Kasıtlı boşluk ve bağlam notları [KARAR: E2 = B]

### 5.1 Hangi olaylar notlanır?

| Grup | Notlanma |
|---|---|
| R (E01–E10), V5 (E11–E12) | **~%70 notlu, ~%30 notsuz.** Seçim her olay türü içinde dengeli ve varyant bazında rastgele yapılır. Böylece model "hangi tür notlu olur" kuralını ezberleyemez. |
| V6 (E19) | Varyantların ~%70'inde dönemsiz bir firma notu bulunur (sezon, Betriebsferien). |
| V1–V4 (E13–E18) | **Hiç notlanmaz.** Bunların kaynağı muhasebe kaydıdır; yönetim bu durumdan habersizdir. |

### 5.2 Notların zamanı, kimliği ve süresi

- **Zaman [ÖNERİ]:** Not, olayın başladığı ayın tarihini taşır. Kalıcı olaylar için sonraki aylarda tekrar not yazılmaz.
- **Kaynak kimlikleri [ÖNERİ]:**
  - `Kontextnotiz JJJJ-MM`
  - Aynı ayda birden fazla not varsa `Kontextnotiz JJJJ-MM #2`
  - Dönemsiz firma notu: `Firmenprofil`
- **Süre alanı [KARAR, tur 2]:** Her not `duration` alanı taşır: `dauerhaft` veya `temporär`. Alan, bilgi tabanında notun meta verisidir ve modele görünür.
  - Olayın biçimi `dauerhaft` ise not da `dauerhaft` olur.
  - Biçimi `einmalig`, `temporär` veya `periodisch` olan olayların notları `temporär` olur.
  - `Firmenprofil` notu `dauerhaft` olur.
  - Çeldirici notlar, içeriğine uygun değeri alır.
- **RAG penceresi [KARAR, tur 2 — çalışma varsayımı]:** Cari ay t için t−11 … t aralığındaki notlar (12 ay) ve dönemsiz `Firmenprofil` notu getirilir. Kesin pencere daha sonra netleşecek **[AÇIK]**.
  - Gerekçe: Kalıcı bir basamak, önceki yılın aynı ayına göre karşılaştırmada tam 12 ay boyunca (t … t+11) sapma olarak görünür. 12 aylık pencere bu süreyi kapsar.

### 5.3 Çeldirici notlar

- Ayların ~%10–15'inde, BWA'da görünür etkisi olmayan bir olay notlanır. Örnekler: yeni bir Azubi, ERP güncellemesi, Hausbank ziyareti, telefon operatörü değişikliği.
- Ground truth'ta bu notlar `distractor = true` olarak işaretlenir. Beklenen davranış: model bu notu hiçbir sapmaya bağlamaz.

### 5.4 Notlardaki rakamlar [KARAR, tur 2]

- Notlar rakam içerebilir: kişi sayısı, yüzde, yaklaşık tutar, süre. Örnekler: "drei neue Mitarbeiter", "rund 4 % Preiserhöhung", "ca. 25.000 € Messekosten".
- **Katman 4 kuralı:** Yorum metnindeki bir rakam iki durumda kabul edilir:
  1. `facts.json`'daki bir değerle tolerans dahilinde eşleşiyorsa, **veya**
  2. RAG'in getirdiği bir notta geçiyorsa **ve** aynı cümle o notun kaynak kimliğine atıf yapıyorsa.

  Diğer bütün rakamlar işaretlenir.
- **Üreteç [ÖNERİ]:**
  - Notlu olayların ~%50'sinin notu en az bir rakam içerir.
  - Rakamlar olay parametrelerinden türetilir ve not üslubunda yuvarlanır. Bu yüzden BWA'daki etkiden biraz farklı olabilir (ör. not "ca. 25.000 €" der, BWA'daki sapma 23.412 € olur). Model BWA rakamlarını `facts.json`'dan, not rakamlarını yalnızca atıfla kullanmalı.
  - Notta geçen rakamlar değerlendirme için kaydedilir (Bölüm 7.4).

---

## 6. Gürültü ve eşik yakınlığı [KARAR: D7; sayılar ÖNERİ]

- Değeri 0 olmayan her temel satıra ±%2–4 rastgele dalgalanma eklenir.
- Olayların ~%20'si, anlamlılık eşiğine yakın bir büyüklükle üretilir (`near_threshold = true`). Bu, sapma yakalama (recall) metriğini zorlar.
- Eşiklerin kendisi CLAUDE.md 6.2'de **[AÇIK]**. Eşik yakını büyüklükler, eşikler belirlendikten sonra kalibre edilecek.

---

## 7. Ground truth şeması [KARAR: D9; alan adları ÖNERİ]

- Alan adları, `facts.json` örneğiyle tutarlı olsun diye İngilizcedir. Satır anahtarları `02_bwa_satir_yapisi.md`'den gelir.
- **[KARAR, tur 2]** Üreteç **her olayı eksiksiz kaydeder**: ay(lar), satır(lar), büyüklük (mutlak ve %), kalıcı/geçici (`duration`) ve nota yazılıp yazılmadığı (`documented`).
- Bu kural yalnızca havuz olayları için değil; pratiklerden doğan olaylar (E13–E17, her gerçekleşme ayrı kayıt) ve sezon deseni (E19, varyant başına bir kayıt) için de geçerlidir.

### 7.1 Olay kaydı (`events.jsonl`, olay başına bir kayıt)

```json
{
  "event_id": "A1-v00-E01-2025-06",
  "firm_id": "A1-v00",
  "type": "E01",
  "category": "R",
  "start": "2025-06",
  "end": null,
  "shape": "dauerhaft",
  "duration": "dauerhaft",
  "effects": [
    {"line": "personalkosten", "from": "2025-06", "to": null, "abs_per_month": 12600.00, "pct_of_baseline": 6.0}
  ],
  "documented": true,
  "source_id": "Kontextnotiz 2025-06",
  "expected_flag": null,
  "expected_treatment": "cite",
  "near_threshold": false,
  "overlaps_with": []
}
```

- `shape` (etki biçimi) değerleri: `einmalig` · `temporär` · `dauerhaft` · `periodisch`
- `duration` (kalıcı/geçici) değerleri: `dauerhaft` · `temporär`. `shape` değerinden türetilir (Bölüm 5.2).
- Tek ayı aşan geçici etkilerde (ör. E06, 1–3 ay) `effects` dizisi her ay için ayrı tutar içerebilir.
- `expected_treatment` değerleri:
  - `cite`: nedeni kaynakla verir
  - `hypothesis`: tahmin olarak işaretler veya açık soru sorar
  - `warning`: uyarı dili kullanır ve açık soru sorar
  - `seasonal`: sezonla açıklar
  - `ignore`: yalnızca çeldirici notlarda; nota dayanmaz

### 7.2 Ay kaydı (`ground_truth_months.jsonl`, firma-ay başına bir kayıt)

```json
{
  "firm_id": "A1-v00",
  "period": "2026-06",
  "new_events": ["A1-v00-E11-2026-06"],
  "active_events": ["A1-v00-E01-2025-06", "A1-v00-E13-2026-06"],
  "expected_flags": [
    {"code": "V1", "line": "personalkosten", "event_id": "A1-v00-E13-2026-06"},
    {"code": "V5", "line": "werbe_reisekosten", "event_id": "A1-v00-E11-2026-06"}
  ],
  "acceptable_flags": [],
  "distractor_notes": [],
  "quiet_month": false,
  "seasonal_lines": []
}
```

- `expected_flags`: beklenen uyarılar. Bunların atlanması recall'ı düşürür.
- `acceptable_flags` [ÖNERİ]: Beklenmeyen ama cezalandırılmayan uyarılar. Örnek: A2'de not bulunmayan bir fiyat olayının tetiklediği V2 uyarısı (Bölüm 9.1), ya da A3'te her yıl tekrarlanan fuarın V1'e benzeyen deseni.

### 7.3 Not kaydı (`context_notes.jsonl`, modele görünür, K-C'ye yüklenir)

```json
{
  "source_id": "Kontextnotiz 2025-06",
  "firm_id": "A1-v00",
  "period": "2025-06",
  "duration": "dauerhaft",
  "text": "Zum 1. Juni haben drei neue Mitarbeiter in der CNC-Fertigung angefangen."
}
```

`Firmenprofil` notunda `period` alanı `null` olur.

### 7.4 Not–olay eşlemesi (`notes_ground_truth.jsonl`, yalnızca değerlendirme)

```json
{"source_id": "Kontextnotiz 2025-06", "firm_id": "A1-v00", "event_id": "A1-v00-E01-2025-06", "distractor": false, "numbers": [3]}
```

**Ayrım ilkesi [ÖNERİ]:** Modelin gördüğü dosyalar (ham BWA, `context_notes.jsonl`) ile değerlendirme dosyaları (`events.jsonl`, `ground_truth_months.jsonl`, `notes_ground_truth.jsonl`, varyantların pratik profilleri) ayrı tutulur. Değerlendirme dosyaları hiçbir zaman RAG'e veya model girdisine girmez.

---

## 8. Bilinçli zor vakalar

Bu durumlar üreteçte kasıtlı olarak oluşturulur; model farklarını en çok bunlarda göstermeli.

1. **E04 + E16 aynı dönemde:** İkisi de Rohertragsquote'yi düşürür. Model notlu fiyat artışını kaynağıyla vermeli, V2 uyarısını ayrıca eklemeli.
2. **A3'te her yıl aynı ayda tekrarlanan fuar (E11):** Desen V1 heuristiğine benzer. Bu vaka hem bayrak isabetini hem de modelin uyarı dilini sınar.
3. **P4 (yıl sonu AfA) + E08 yatırım:** Yatırımın AfA etkisi yıl içinde görünmez; yalnızca Zinsaufwand artar.
4. **Kalıcı olay notu yalnızca başlangıç ayında:** Sonraki 12 ay boyunca önceki yılın aynı ayına göre sapma sürer. RAG'in eski notu bulabilmesi gerekir.
5. **Çakışma (E01 + E03, ikisi de Personalkosten):** Biri notlu, diğeri notsuzsa model yalnızca notlu olanı kaynaklı olarak vermeli.
6. **Epizodik E16 (A3):** t ayında V2, t+1 ayında telafi kaydı nedeniyle V4 benzeri bir desen oluşur.
7. **Notsuz gerçek olaylar (~%30), çeldirici notlar, olaysız aylar ve eşik yakını olaylar.**

---

## 9. Katmanlara yansıyan kararlar (tur 2, 14.10.2026)

İlk turda açık kalan üç nokta kullanıcı tarafından karara bağlandı.

### 9.1 V2 tespiti arketipe göre ayrılır [KARAR]

| Arketip | Kural |
|---|---|
| Üretici (A1, A3) | Mevcut kural: Bestandsveränderungen = 0 iken Material-/Wareneinkauf belirgin biçimde değişmiş |
| Ticaret (A2) | Uyarı, **açıklanamayan ani Rohertragsquote değişimine** bağlanır |

**"Açıklanamayan" kavramının uygulanması [ÖNERİ — kullanıcı onayı bekleniyor]:**

- **Katman 1 (sayısal kısım):** Rohertragsquote hem önceki aya hem önceki yılın aynı ayına göre eşiği aşan bir sapma gösteriyorsa bir V2 adayı üretir. İki karşılaştırmanın birlikte aranması, sapmanın sezonla açıklanamadığı anlamına gelir.
- **Model (bağlamsal kısım):** O ayda Rohertragsquote'yi açıklayan bir not varsa (ör. notlu E04 veya E05), model nedeni kaynağıyla verir ve V2 uyarısı vermez. Not yoksa uyarı dili kullanır.
- **Ground truth:**
  - Gerçek E16 etkisi olan aylarda V2 → `expected_flags`.
  - Notsuz bir gerçek olayın tetiklediği V2 uyarısı → `acceptable_flags` (model o ayda bu ayrımı yapamaz).
  - Notlu bir olayın açıkladığı aylarda V2 uyarısı yanlış alarm sayılır.
- Gerekçe: Bu dağılım, notları dikkate alma işini modele bırakır. Katman 1 deterministik kalır, bağlamsal yargı modele (RAG + fine-tuning) geçer; bu da G7'deki odağa uyar.

### 9.2 Notlardaki rakamlar [KARAR]

Notlar rakam içerebilir. Doğrulama katmanı bu rakamları kaynak gösterilmesi şartıyla kabul eder. Ayrıntılar Bölüm 5.4'te.

### 9.3 Süre alanı ve RAG penceresi [KARAR; pencere çalışma varsayımı]

Notlar `dauerhaft`/`temporär` alanı taşır. RAG penceresi şimdilik 12 ay. Ayrıntılar Bölüm 5.2'de.

### 9.4 Hâlâ açık [AÇIK]

- **Anlamlılık eşikleri** (CLAUDE.md 6.2): Eşik yakını olayların kalibrasyonu ve A2'deki V2 adayı buna bağlı.
- **RAG penceresinin kesin değeri** (şimdilik 12 ay).
