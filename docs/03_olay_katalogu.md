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
| E01 | Neueinstellungen | R | Personalkosten | kalıcı basamak | +%2 … +5 (en az 2 kişi) | hepsi | evet | – |
| E02 | Personalabgang | R | Personalkosten | kalıcı basamak | −%2 … −5 (en az 2 kişi) | hepsi | evet | – |
| E03 | Tariferhöhung / Lohnrunde | R | Personalkosten | kalıcı basamak; her yıl, arketipe göre sabit bir ayda | +%2 … +4 | hepsi | evet | – |
| E04 | Materialpreiserhöhung | R | Material-/Wareneinkauf → Rohertragsquote | %80 geçici (3–6 ay), %20 kalıcı | Materialquote +2 … +6 puan | hepsi | evet | – |
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
| E01 | 1–3 | E08 | 0–1 |
| E02 | 1–2 | E09 | seri boyunca 0–1 |
| E03 | 1 (sabit ay) | E10 | 0–1 |
| E04 | 1–2 | E11 | 1–2 (A3: her yıl aynı ayda 1) |
| E05 | 0–1 | E12 | 2–3 |
| E06 | 2–4 | E16 epizodik | 0–2 |
| E07 | seri boyunca 0–1 | E18 | 0–6 (P5'e göre) |

- **Kalibrasyon (tur 3):** İlk taslakta E01 (2–4/yıl, +%2–8), E07 (0–1/yıl), E03 (+%2,5–5,5) ve E04'ün kalıcı payı (%50) maliyet yönünde birikiyordu. Sonuç olarak firmaların faaliyet sonucu 2026'ya kadar ortalama −%15'e düşüyordu. Yukarıdaki değerlerle yıllık ortalama marjlar %0–5 aralığında kalıyor ve hafif bir marj baskısı var. Ayrıntılar `00_karar_kaydi.md`, Bölüm 7'de.
- **Referans koşu (seed 42, 3 × 10):** ayda **~1,5 havuz olayı**, yorumlanabilir ayların **%15,4'ü olaysız**. İlk taslaktaki "~2/ay" tahmini, olaysız ay hedefiyle (~%15) birlikte tutmuyordu; olaysız ay hedefi öncelikli tutuldu.
- Pratiklerden doğan desenler (E13–E15, sistematik E16, E17) ve sezon (E19) bu sayıya dahil değildir.
- "Olaysız ay" yeni olay olmadığı anlamına gelir. Önceki aylardaki olayların etkisi sürebilir; ground truth bunları `active_events` olarak listeler (Bölüm 7.2).

**Çakışma (D8):**
- Bir satır-ayda en fazla 2 olay olabilir. Aynı türden iki olay aynı ayda başlayamaz.
- Olayların ~%10'u bir başka olayla çakışır (ör. Nisan'da E01 + E03, ikisi de Personalkosten'te). Bunun için dolu bir satır-aya ikinci olay yalnızca %30 olasılıkla eklenir. Referans koşuda çakışma oranı %13.
- Sabit aylı olaylar (E03 tarife ayı, A3'ün fuar ayı) her yıl önce yerleştirilir; rastgele olaylar sınıra bunlara göre uyar.

---

## 5. Kasıtlı boşluk ve bağlam notları [KARAR: E2 = B]

### 5.1 Hangi olaylar notlanır?

| Grup | Notlanma |
|---|---|
| R (E01–E10), V5 (E11–E12) | **~%70 notlu, ~%30 notsuz.** Seçim her olay türü içinde dengeli ve varyant bazında rastgele yapılır. Böylece model "hangi tür notlu olur" kuralını ezberleyemez. |
| V6 (E19) | Varyantların ~%70'inde dönemsiz bir firma notu bulunur (sezon, Betriebsferien). Varyant sayısı az olduğu için seçim yazı-tura ile değil, dengeli bir diziyle yapılır: her arketipte 10 varyanttan 7'si not alır, v00 her zaman alır. |
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

- Notlar rakam içerebilir: kişi sayısı, yüzde, yaklaşık tutar. Örnekler: "3 neue Mitarbeiter", "rund 4 % Preiserhöhung", "ca. 25.000 € Messekosten".
- Rakamlar her zaman rakamla yazılır ("drei" değil "3"). Böylece Katman 4 onları ayıklayabilir. Şablonlarda yer tutucular dışında hiç rakam yoktur; ay adları da yazıyla verilir ("ab Juni").
- **Katman 4 kuralı:** Yorum metnindeki bir rakam iki durumda kabul edilir:
  1. `facts.json`'daki bir değerle tolerans dahilinde eşleşiyorsa, **veya**
  2. RAG'in getirdiği bir notta geçiyorsa **ve** aynı cümle o notun kaynak kimliğine atıf yapıyorsa.

  Diğer bütün rakamlar işaretlenir.
- **Üreteç [ÖNERİ]:**
  - Notlu olayların ~%50'sinin notu en az bir rakam içerir.
  - Rakamlar olay parametrelerinden türetilir ve not üslubunda yuvarlanır. Bu yüzden BWA'daki etkiden biraz farklı olabilir (ör. not "ca. 25.000 €" der, BWA'daki sapma 23.412 € olur). Model BWA rakamlarını `facts.json`'dan, not rakamlarını yalnızca atıfla kullanmalı.
  - Notta geçen rakamlar değerlendirme için kaydedilir (Bölüm 7.4).

### 5.5 Not şablonları [KARAR, tur 3]

- Şablonlar `generator/config/note_templates.toml` dosyasında.
- **E01–E12:** her olay türü için 5 cümle kalıbı (3 rakamlı, 2 rakamsız).
- **E19:** her arketip için 4 kalıplı `Firmenprofil` notu.
- **Çeldiriciler:** 11 kalıp.
- Hangi kalıbın seçileceğini ve kalıptaki boşlukların (bölüm, malzeme, müşteri türü, makine) nasıl doldurulacağını seed belirler. Aynı seed her zaman aynı notları verir.
- **[ÖNERİ — ileride]** Şablonla üretilen notlar bir LLM ile yeniden ifade edilerek çeşitlendirilebilir. Bu, notların doğallığını artırır ama ek bir bağımlılık ve maliyet getirir. Rakamların ve olay eşlemesinin korunması gerekir (Bölüm 7.4). Şimdilik uygulanmadı.

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

### 7.1 Olay kaydı (`evaluation/events.jsonl`, olay başına bir kayıt)

Referans koşudan gerçek bir kayıt:

```json
{
  "event_id": "A1-v00-E01-2024-05",
  "firm_id": "A1-v00",
  "type": "E01",
  "category": "R",
  "start": "2024-05",
  "end": null,
  "shape": "dauerhaft",
  "duration": "dauerhaft",
  "lines": ["personalkosten"],
  "magnitude": {"people": 3},
  "effects": [
    {"line": "personalkosten", "from": "2024-05", "to": "2026-12",
     "abs_at_start": 12889.8, "pct_at_start": 5.7, "total_abs": 412473.6}
  ],
  "documented": true,
  "source_id": "Kontextnotiz 2024-05",
  "expected_flags": [],
  "acceptable_flags": [],
  "expected_treatment": "cite",
  "near_threshold": false,
  "overlaps_with": []
}
```

- `start`: olayın ayı. V1 olaylarında ödeme ayı (E13 Haziran, E14 Kasım, E15 Ocak), tahakkuk farkı ise yılın bütün aylarına yayılır. E16 ve E17'de dönemin ilk ayı.
- `end`: son etkili ay; kalıcı olaylarda `null`.
- `shape` (etki biçimi) değerleri: `einmalig` · `temporär` · `dauerhaft` · `periodisch`.
- `duration` (kalıcı/geçici) değerleri: `dauerhaft` · `temporär`. `shape` değerinden türetilir (Bölüm 5.2). E19 istisnadır: `dauerhaft`.
- `magnitude`: olayın parametreleri (ör. kişi sayısı, yüzde, puan, kaydırılan pay).
- `effects`: satır başına özet; ilk ve son etkili ay, ilk aydaki mutlak ve yüzde etki, toplam etki.
- **Aylık kesin etkiler** `evaluation/effects.csv` dosyasında: `firm_id, period, line, event_id, delta`. Her olayın her satıra ve aya etkisi burada. Bu dosya sayesinde iki eşitlik kontrol edilebilir:
  - `ekonomik seri = taban + Σ gerçek olay etkileri + gürültü`
  - `kaydedilen BWA = ekonomik gerçek + Σ çarpıklık etkileri (V1–V4)`
- `expected_treatment` değerleri:
  - `cite`: nedeni kaynakla verir
  - `hypothesis`: tahmin olarak işaretler veya açık soru sorar
  - `warning`: uyarı dili kullanır ve açık soru sorar
  - `seasonal`: sezonla açıklar
- Çeldirici notlar bir olaya bağlı olmadığı için olay kaydı yoktur; `notes_ground_truth.jsonl`'da `distractor = true` olarak işaretlenir. Beklenen davranış: nota dayanmamak.

### 7.2 Ay kaydı (`evaluation/ground_truth_months.jsonl`, firma-ay başına bir kayıt)

Referans koşudan (kısaltılmış):

```json
{
  "firm_id": "A1-v00",
  "period": "2025-06",
  "commentable": true,
  "new_events": ["A1-v00-E05-2025-06", "A1-v00-E06-2025-06", "A1-v00-E13-2025-06"],
  "active_events": ["A1-v00-E01-2024-11", "...", "A1-v00-E13-2025-06"],
  "vorjahr_events": ["A1-v00-E06-2024-06", "A1-v00-E11-2024-06", "..."],
  "expected_flags": [
    {"code": "V4", "line": "bestandsveraenderungen_fe_ue", "event_id": "A1-v00-E16-2025-04"},
    {"code": "V1", "line": "personalkosten", "event_id": "A1-v00-E13-2025-06"}
  ],
  "acceptable_flags": [],
  "rohertrag_causes": [
    {"event_id": "A1-v00-E16-2025-04", "type": "E16", "kind": "distortion", "documented": false},
    {"event_id": "A1-v00-E05-2025-06", "type": "E05", "kind": "real", "documented": true}
  ],
  "v2_candidate_decision": "warn",
  "notes": ["Kontextnotiz 2025-06", "Kontextnotiz 2025-06 #2"],
  "distractor_notes": [],
  "quiet_month": false,
  "seasonal_change_pct": 1.9
}
```

| Alan | Anlamı |
|---|---|
| `commentable` | Ay yorumlanabilir mi (2025-01'den itibaren) |
| `new_events` | Bu ay başlayan olaylar |
| `active_events` | Bu ayın önceki aya veya önceki yılın aynı ayına göre karşılaştırmasını etkileyebilecek olaylar. Kalıcı bir basamak yalnızca ilk 12 ayında listelenir. |
| `vorjahr_events` | Önceki yılın aynı ayında etkili olup bu ay etkili olmayan geçici olaylar. Önceki yıla göre farkları açıklar (ör. geçen yılki fuar). |
| `expected_flags` | Beklenen uyarılar; atlanması recall'ı düşürür |
| `acceptable_flags` | Beklenmeyen ama cezalandırılmayan uyarılar (Bölüm 9.1; A3'ün her yıl tekrarlanan fuarı) |
| `rohertrag_causes`, `v2_candidate_decision` | Rohertragsquote'yi değiştiren nedenler ve V2 adayı karşısında beklenen karar (Bölüm 9.1) |
| `notes`, `distractor_notes` | Bu ayın not kimlikleri ve bunlardan hangilerinin çeldirici olduğu |
| `quiet_month` | Bu ay yeni havuz olayı başlamadı |
| `seasonal_change_pct` | Satış endeksinin önceki aya göre sezonsal değişimi. V6 beklentisi ≥ %10 değişimde (geçici eşik; anlamlılık eşikleri [AÇIK]). |

**Not:** `expected_flags` henüz anlamlılık eşiğine göre süzülmüyor. Örneğin çok küçük bir çarpıklık da beklenen uyarı olarak listeleniyor. Eşikler belirlendiğinde değerlendirme bu listeyi `effects.csv`'deki büyüklüklere göre süzecek.

### 7.3 Not kaydı (`model_input/context_notes.jsonl`, modele görünür, K-C'ye yüklenir)

```json
{
  "source_id": "Kontextnotiz 2024-05",
  "firm_id": "A1-v00",
  "period": "2024-05",
  "duration": "dauerhaft",
  "text": "Verstärkung im Bereich Montage: Seit Anfang Mai sind neue Kolleginnen und Kollegen an Bord."
}
```

`Firmenprofil` notunda `period` alanı `null` olur.

### 7.4 Not–olay eşlemesi (`evaluation/notes_ground_truth.jsonl`, yalnızca değerlendirme)

```json
{"source_id": "Kontextnotiz 2024-05", "firm_id": "A1-v00", "event_id": "A1-v00-E01-2024-05", "distractor": false, "numbers": []}
```

`numbers`: notta geçen rakamlar, notta göründükleri yuvarlanmış haliyle (ör. `[3]`, `[270000]`, `[3.5]`).

**Ayrım ilkesi [KARAR, tur 3]:** Modelin gördüğü dosyalar `model_input/` klasöründe: ham BWA, `context_notes.jsonl` ve `firms.json` (yalnızca firma adı). Değerlendirme dosyaları ayrı bir `evaluation/` klasöründe: ekonomik gerçek seri, etkiler, olaylar, ay kayıtları, not eşlemesi ve varyant parametreleri (pratik profilleri dahil). Değerlendirme dosyaları hiçbir zaman RAG'e veya model girdisine girmez.

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
8. **A2'de notlu fiyat olayı + V2 adayı:** Katman 1 Rohertragsquote sıçraması için V2 adayı üretir, ama nedeni notlu bir E04/E05'tir. Model nedeni kaynağıyla vermeli ve V2 uyarısı vermemeli (`v2_candidate_decision = cite`, Bölüm 9.1).

---

## 9. Katmanlara yansıyan kararlar (tur 2 ve 3, 14.10.2026)

İlk turda açık kalan üç nokta kullanıcı tarafından karara bağlandı (tur 2). V2 ayrımının uygulanma biçimi tur 3'te onaylandı.

### 9.1 V2 tespiti arketipe göre ayrılır [KARAR]

| Arketip | Kural |
|---|---|
| Üretici (A1, A3) | Mevcut kural: Bestandsveränderungen = 0 iken Material-/Wareneinkauf belirgin biçimde değişmiş |
| Ticaret (A2) | Uyarı, **açıklanamayan ani Rohertragsquote değişimine** bağlanır |

**"Açıklanamayan" kavramının uygulanması [KARAR, tur 3]:**

- **Katman 1 (sayısal kısım):** Rohertragsquote hem önceki aya hem önceki yılın aynı ayına göre eşiği aşan bir sapma gösteriyorsa bir V2 adayı üretir. İki karşılaştırmanın birlikte aranması, sapmanın sezonla açıklanamadığı anlamına gelir.
- **Model (bağlamsal kısım):** O ayda Rohertragsquote'yi açıklayan bir not varsa (ör. notlu E04 veya E05), model nedeni kaynağıyla verir ve V2 uyarısı vermez. Not yoksa uyarı dili kullanır.
- **Ground truth:**
  - Gerçek E16 etkisi olan aylarda V2 → `expected_flags`.
  - Notsuz bir gerçek olayın tetiklediği V2 uyarısı → `acceptable_flags` (model o ayda bu ayrımı yapamaz).
  - Notlu bir olayın açıkladığı aylarda V2 uyarısı yanlış alarm sayılır.
- Gerekçe: Bu dağılım, notları dikkate alma işini modele bırakır. Katman 1 deterministik kalır, bağlamsal yargı modele (RAG + fine-tuning) geçer; bu da G7'deki odağa uyar.

**Ayrımın ayrıca ölçülmesi [KARAR, tur 3]:** Ay kaydında iki alan bu ayrımı ölçülebilir kılar (Bölüm 7.2):

- `rohertrag_causes`: o ayda Rohertragsquote'yi değiştiren olaylar. Her neden için `kind` (`real` / `distortion`) ve `documented` bilgisi tutulur. Nedenler:
  - E04 (başladığı ay ve geçici zammın bittiği ay)
  - E05 (başladığı ay)
  - E16 (etkili her ay)
  - Material satırındaki E18
- `v2_candidate_decision`: Katman 1'in V2 adayı karşısında beklenen model kararı.
  - `warn`: muhasebe kaynaklı bir neden var; uyarı dili beklenir.
  - `cite`: yalnızca notlu gerçek nedenler var; model kaynağıyla açıklamalı, V2 uyarısı yanlış alarmdır.
  - `either`: yalnızca notsuz gerçek nedenler var; uyarı da hipotez de kabul edilir.

Değerlendirmede bu karar ayrı bir metrik olarak raporlanacak (CLAUDE.md Bölüm 8: "V2 adayı ayrımı").

**Referans koşudaki dağılım ve bir sınırlama:** A2'nin yorumlanabilir aylarında 217 `warn`, 2 `cite`, 2 `either` var. Nedeni şu: A2 varyantlarının %80'i stok değişimini yalnızca envanterde kaydediyor (P3) ve bu, hemen her ayı bir çarpıklık ayı yapıyor. Bu dağılımla "notla açıkla" vakası ölçmek için çok az. Çözüm seçenekleri kullanıcıya sunuldu (`00_karar_kaydi.md`, Bölüm 7).

### 9.2 Notlardaki rakamlar [KARAR]

Notlar rakam içerebilir. Doğrulama katmanı bu rakamları kaynak gösterilmesi şartıyla kabul eder. Ayrıntılar Bölüm 5.4'te.

### 9.3 Süre alanı ve RAG penceresi [KARAR; pencere çalışma varsayımı]

Notlar `dauerhaft`/`temporär` alanı taşır. RAG penceresi şimdilik 12 ay. Ayrıntılar Bölüm 5.2'de.

### 9.4 Hâlâ açık [AÇIK]

- **Anlamlılık eşikleri** (CLAUDE.md 6.2): Eşik yakını olayların kalibrasyonu, A2'deki V2 adayı ve `expected_flags`'in süzülmesi buna bağlı.
- **RAG penceresinin kesin değeri** (şimdilik 12 ay). Üreteçten çıkan bir gözlem bu karara girdi olacak:
  - Önceki yılın aynı ayına göre farkı, önceki yıldaki geçici bir olay da açıklayabilir (ör. geçen Haziran'daki fuar). Ay kaydında bunlar `vorjahr_events` olarak listeleniyor.
  - Bu olayın notu t−12 ayındadır ve 12 aylık pencerenin (t−11 … t) hemen dışında kalır.
  - Seçenekler: pencereyi 13 ay yapmak; t−12 ayını ayrıca getirmek; ya da bu bilgiyi önceki ayların onaylanmış yorumlarına (K-D) bırakmak.
