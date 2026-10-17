# 07 — Doğrulama katmanı (Katman 4)

> **Durum:** v1.1 (`validation/`, 53 test), 17.10.2026. v1.1, deneme turunun ilk gerçek model çıktılarına göre biçimsel toleranslar ekledi (Bölüm 11).
> - **[KARAR]:** kurallar (CLAUDE.md 6.2, Katman 4; tur 6: B3–B4; tur 8: yuvarlama kuralı (a)).
> - **[ÖNERİ]:** kelime listeleri, kısa ad listesi, uzunluk toleransı ve "rakam hangi satıra ait" kuralı (`validation/config.toml`).
>
> **İlgili:** CLAUDE.md 6.2–6.3 · `06_model_tarafi_secenekler.md` (B3, B4) · Karar kaydı: `00`, Bölüm 12

---

## 1. Amaç ve girdiler

Katman 4, modelin yazdığı taslağı denetler ve insana bir **uyarı listesi** verir. Ground truth'a erişmez; yalnızca modelin de gördüğü bilgileri kullanır:

| Girdi | Kaynak |
|---|---|
| Yorum metni | Model çıktısı (Markdown, CLAUDE.md 6.3 yapısında) |
| `facts.json` | Katman 1 (`docs/05`) |
| Bağlam notları | Modele verilen notlar (K-C). Katman 2 hazır olana kadar: 13 aylık penceredeki bütün notlar ve `Firmenprofil` |

**Kullanıldığı yerler:**
- **Üründe:** taslak + uyarı listesi insana gösterilir.
- **İdeal yorumlar (paket 5):** öğretmen modelin metni ancak hiç `fehler` bulgusu yoksa kabul edilir.
- **Deneme turu (paket 6):** aday modellerin rakam sadakati ve format uyumu.
- **Değerlendirme (paket 9):** "Rakam sadakati" ve "Format uyumu" metrikleri; kaynak/hipotez işaretleme oranı.

## 2. Format kuralları — [KARAR, tur 6] (B4)

Kanonik yapı:

```
**Kernaussagen <Monat Jahr>**

1. …
2. …
3. …

**Abweichungen im Detail**

| Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese |
|---|---|---|---|---|---|
| Umsatzerlöse | 886.365 € | Vj. 744.725 € | +141.640 € (+19,0 %) | … | [Quelle: Kontextnotiz 2025-06 #2] |

**Hinweise auf mögliche Verzerrungen**

- …

**Offene Fragen an Buchhaltung / Steuerberater**

- …?
```

**Kurallar:**
- Dört başlık tam bu metinle, birer kez ve bu sırayla yer alır. Kernaussagen başlığı `facts.json`'daki `period_label` ile biter (ör. „Kernaussagen Juni 2025“).
- Kernaussagen: 1–3 numaralı madde („1. …“), sıralı numaralandırma.
- Abweichungen: başlık satırı sabit olan, 6 sütunlu bir tablo. Tablodaki `Position`, bir BWA satırının ya da oranın kanonik adıdır (`docs/02`, D1).
- Hinweise ve Offene Fragen: „- “ ile başlayan maddeler. Her soru „?“ ile biter.
- İçeriği olmayan bölümde yalnızca „Keine.“ yazar. Kernaussagen hiçbir zaman boş olamaz.
- Başlıkların dışında metin olmaz.
- **Uzunluk:** Tablo dışında ~250–350 kelime. Bu aralığın ±50 kelime dışına çıkılırsa bulgu yalnızca `hinweis` olur.
- **Kaynak gösterimi:** `[Quelle: <kimlik>]`. Birden fazla kaynak `;` ile ayrılır: `[Quelle: Kontextnotiz 2025-06 #2; Kontextnotiz 2025-06]`.
- **Tahmin işareti:** `(Hypothese)`. Tabloda son sütuna „Hypothese“ yazılır.
- **Biçimsel tolerans (v1.1):** Kalın yazı (`**…**`), yatay çizgiler (`---`) ve girintili devam satırları yok sayılır; içerik denetimi aynen yapılır.

## 3. Rakam kuralları

### 3.1 Ayıklama

| Metindeki biçim | Birim |
|---|---|
| `886.365 €`, `886.365 EUR` | € |
| `886 T€`, `886 TEUR`, `886 Tsd. €` | € × 1.000 |
| `0,9 Mio. €` | € × 1.000.000 |
| `19,0 %`, `19 Prozent` | yüzde |
| `3,8 Pp.`, `3,8 Prozentpunkte`, `3,8 %-Punkte` | yüzde puanı |
| `1,5-fach`, `das 1,5-Fache` | kat |
| `12` (birimsiz) | birimsiz |

- İşaret (`+`, `-`, `−`, `–`) yalnızca rakama bitişikse işaret sayılır.
- **Rakam sayılmayanlar:**
  - tarihler (`2025-06`, `30.06.2025`, `06/2025`, `1. Juli`, `Q2`),
  - yıllar (1990–2099 arası birimsiz tam sayılar),
  - madde numaraları,
  - başlıklar,
  - `[Quelle: …]` içindeki kimlikler,
  - kod içindeki rakamlar (`V4`, `A1-v00`).
- Almanca olmayan ondalık yazım (`19.0 %`) ayrı bir bulgudur.

### 3.2 Yuvarlama kuralı (a) — [KARAR, tur 8]

Metindeki rakam, karşılaştırılan değerin **metinde gösterilen hassasiyete doğru yuvarlanmış** hâliyse eşleşir. Yuvarlama ticari kurala göre yapılır (yarım yukarı).

| Değer | Kabul | Red |
|---|---|---|
| 41.712 € | „42 T€“, „41,7 T€“, „41.712 €“ | „41 T€“, „41.700 €“ |
| 18,4 % | „18 %“, „18,4 %“ | „19 %“ |

Karşılaştırma mutlak değerle yapılır; işaret ayrıca denetlenir (3.5).

### 3.3 Birim uyumu

- € rakamları yalnızca € değerleriyle, yüzdeler yüzdelerle, yüzde puanları yüzde puanlarıyla, katlar katlarla karşılaştırılır.
- Birimsiz bir rakam her birimle karşılaştırılabilir; € değeriyle eşleşmesi için tam sayı olması gerekir.
- Oran farkını „%“ ile yazmak (ör. Rohertragsquote „3,8 % gesunken“; doğrusu „3,8 Prozentpunkte“) `einheit` bulgusudur.

### 3.4 Rakam hangi satıra ait? — [ÖNERİ]

`facts.json`'daki her değer bir satıra veya orana aittir (ör. `Umsatzerlöse`, `Rohertragsquote`). Bayrak kanıtlarındaki rakamlar bayrağın satırına aittir. Eşikler geneldir.

- Bir madde (Kernaussage veya Hinweis) ya da bir tablo satırı satır/oran adı içeriyorsa, içindeki rakamlar **yalnızca o satırların değerleriyle** ve genel eşiklerle karşılaştırılır.
- `facts.json`'da var olan ama başka bir satıra ait bir rakam `zahl_falsche_position` bulgusudur. Örnek: Werbe-/Reisekosten satırında Material-/Wareneinkauf'un tutarı.
- Hiç ad geçmiyorsa (ör. zamirle anlatım) bütün değerlerle karşılaştırılır.
- Kısa adlar ("Umsatz", "Marge", "AfA" …) `config.toml`'daki listeyle kanonik ada çevrilir.
- **Gerekçe:** Yüzdeler 0–30 aralığında yoğun olduğu için kapsam olmadan uydurma bir „5 %“ çoğu zaman tesadüfen bir değerle eşleşirdi.

### 3.5 İşaret

Metinde açık işaret varsa (`+141.640 €`, `−17.002 €`), eşleşen değerlerden en az birinin işareti aynı olmalı. Aksi hâlde `vorzeichen` bulgusu verilir.

### 3.6 Bağlam notundaki rakamlar — [KARAR, tur 2]

`facts.json`'da olmayan bir rakam şu iki koşulda kabul edilir:
- Aynı cümle (veya tablo satırı) bir notu `[Quelle: …]` ile gösteriyor.
- Rakam o notta geçiyor; aynı yuvarlama kuralı geçerli, ör. notta „ca. 7.000 €“ → metinde „7 T€“ ✓.

Rakam verilen bir notta geçiyor ama cümle o notu göstermiyorsa bulgu `zahl_notiz_ohne_quelle` olur.

### 3.7 Denetim sırası ve durumlar

| Sıra | Koşul | Durum |
|---|---|---|
| 1 | Yıl veya başlık | `ausgenommen` (sayıma girmez) |
| 2 | `facts.json` değeriyle eşleşir (3.4 kapsamında) ve işaret uygun | `fakt` |
| 2a | Eşleşir ama işaret ters | `vorzeichen` |
| 3 | Gösterilen notta geçer | `notiz` |
| 4 | Gösterilmeyen, ama verilmiş bir notta geçer | `notiz_ohne_quelle` |
| 5 | Yalnızca öteki birimle (yüzde ↔ yüzde puanı) eşleşir | `einheit` |
| 6 | Başka bir satırın değeriyle eşleşir | `unbelegt` (`zahl_falsche_position`) |
| 7 | Hiçbiriyle eşleşmez | `unbelegt` (`zahl_unbelegt`) |

**Rakam sadakati** = (`fakt` + `notiz`) / denetlenen rakam sayısı.

## 4. Neden cümleleri — [KARAR, tur 6] (B3, B4)

**Kural:** Her neden cümlesi ya `[Quelle: …]` ya da `(Hypothese)` içerir.

Bir cümle şu durumlarda neden cümlesi sayılır [ÖNERİ, `config.toml`]:
- **Nedensellik kelimesi** içerir: *wegen, aufgrund, durch, ursächlich, Ursache, zurückzuführen, …bedingt, infolge, weil, erklärt, …*
- **Tahmin kelimesi** içerir: *vermutlich, wahrscheinlich, möglicherweise, dürfte, könnte, spricht für, …*
  - Hinweise bölümünde uyarı dili doğal olduğu için tahmin kelimeleri orada işaret gerektirmez. Nedensellik kelimeleri ise orada da gerektirir.

**İstisnalar:**
- Nedenin bilinmediğini söyleyen cümleler işaret gerektirmez: *nicht ersichtlich, unklar, offen, Rückfrage, …* (B3: açık soru).
- Sorular denetlenmez.

**Tablo:** „Erklärung“ hücresi doluysa ve bir neden içeriyorsa, son sütunda `[Quelle: …]` ya da „Hypothese“ olmalı. „Ursache offen“ veya „–“ yazılan satırlar muaftır.

**Kaynak kimliği:** `[Quelle: …]` içindeki her kimlik modele verilmiş bir notun kimliği olmalı; değilse `quelle_unbekannt`. K-A ve K-B kimlikleri, Katman 2 kurulunca eklenecek.

**Kanonik olmayan kaynak gösterimi (v1.1):**
- „Quelle:“ öneki olmadan köşeli parantez içinde verilen bilinen not kimlikleri de kaynak sayılır, ama `quellenformat` bulgusu alır. Örnekler: `[Kontextnotiz 2025-03 #3]`, kısaltılmış `[Kontextnotiz 2025-03 #3; 2024-11]`, tabloda parantezsiz kimlik.
- `FACTS`'e veya bayraklara atıf (`[Quelle: FACTS]`, `[Flag V2]`, `[V5]`) kaynak sayılmaz; `quelle_facts` (`hinweis`) bulgusu verilir. Rakamlar zaten facts'ten gelir; neden cümlesi yine bir not ya da `(Hypothese)` ister.

## 5. Kapsam ipuçları (`hinweis`)

- `facts.json`'daki sıralı bir kalem (`positions`) metinde hiç geçmiyorsa: `position_fehlt`.
- `hinweis` durumundaki bir bayrağın satırı Hinweise bölümünde geçmiyorsa: `flag_fehlt`.
- Rohertrag adayları (`kandidat`) için zorunluluk yoktur; notla açıklamak ya da uyarmak modelin kararıdır (`docs/03`, 9.1).

## 6. Bulgu kataloğu

| Kod | Önem | Anlamı |
|---|---|---|
| `zahl_unbelegt` | fehler | Rakam ne `facts.json`'da ne gösterilen bir notta var |
| `zahl_falsche_position` | fehler | Rakam `facts.json`'da var, ama adı geçen satıra ait değil |
| `zahl_notiz_ohne_quelle` | fehler | Rakam bir nottan geliyor, kaynak gösterilmemiş |
| `vorzeichen` | fehler | İşaret ters |
| `einheit` | fehler | Yüzde ile yüzde puanı karışmış |
| `zahlenformat` | fehler | Almanca olmayan ondalık yazım (biçim bulgusu) |
| `quellenformat` | fehler | Bilinen not kimliği „[Quelle: …]“ biçiminde verilmemiş (biçim bulgusu; neden kaynaklı sayılır) |
| `quelle_facts` | hinweis | FACTS'e veya bir bayrağa atıf; kaynak sayılmaz |
| `begruendung_ohne_kennzeichnung` | fehler | Neden cümlesinde kaynak da tahmin işareti de yok |
| `tabelle_ohne_quelle` | fehler | Tablodaki açıklamada kaynak da tahmin işareti de yok |
| `quelle_unbekannt` | fehler | Gösterilen kaynak modele verilmemiş |
| `abschnitt_fehlt`, `abschnitt_doppelt`, `abschnitt_reihenfolge`, `abschnitt_leer` | fehler | Bölüm yapısı |
| `ueberschrift_unbekannt`, `periode`, `text_ausserhalb` | fehler | Başlıklar |
| `kernaussagen_anzahl`, `kernaussagen_format` | fehler | Kernaussagen |
| `tabellenkopf`, `tabellenzeile`, `tabelle_leer`, `position_unbekannt` | fehler | Tablo |
| `liste_format`, `frage_format` | fehler | Maddeler ve sorular |
| `laenge` | hinweis | Uzunluk hedefin dışında |
| `position_fehlt`, `flag_fehlt` | hinweis | Kapsam |

**Format uyumu** = biçim bulgusu yok: bölüm, başlık, tablo, liste kodları, `quellenformat` ve `zahlenformat` (`validation.check.FORMAT_CODES`). Raporun `content_errors` alanı, geri kalan `fehler` bulgularını sayar.

## 7. Rapor

```json
{
  "ok": true, "errors": 0, "content_errors": 0, "hints": 0,
  "metrics": {
    "numbers": {"fakt": 38, "notiz": 2, "ausgenommen": 1, "unbelegt": 0, "notiz_ohne_quelle": 0,
                "vorzeichen": 0, "einheit": 0, "checked": 40, "fidelity": 1.0},
    "reasons": {"total": 6, "with_source": 4, "with_hypothesis": 2, "unmarked": 0},
    "words": 252, "format_ok": true
  },
  "findings": [{"severity": "fehler", "code": "…", "message": "…", "section": "…", "line": 4, "text": "…"}],
  "numbers": [{"text": "886 T€", "section": "kernaussagen", "line": 4, "status": "fakt"}]
}
```

Bulgu mesajları Almancadır, çünkü ürünün kullanıcısına gösterilir.

## 8. Kullanım

```bash
# Üreteç koşusundan (facts ve 13 aylık notlar otomatik)
python -m validation --text yorum.md --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06

# Hazır dosyalarla
python -m validation --text yorum.md --facts facts.json --notes notlar.jsonl --json rapor.json
```

Çıkış kodu: 0 = `fehler` yok, 1 = en az bir `fehler`.

Örnek yorum ([`examples/kommentar_A1-v00_2025-06.md`](examples/kommentar_A1-v00_2025-06.md)) için çıktı:

```
Fehler: 0 · Hinweise: 0 · Format: ok
Zahlen: 40 geprüft, 38 facts, 2 Notiz, 0 beanstandet · Zahlentreue: 1.0
Begründungen: 6 (4 mit Quelle, 2 als Hypothese, 0 ohne Kennzeichnung) · Wörter ohne Tabelle: 252
```

İki rakam bozulduğunda („886 T€“ → „887 T€“, „−17.002 €“ → „+17.002 €“):

```
Fehler: 2 · Hinweise: 0 · Format: ok
Zahlen: 40 geprüft, 36 facts, 2 Notiz, 2 beanstandet · Zahlentreue: 0.95
  [fehler] zahl_unbelegt (Z. 4): „887 T€“ ist weder in facts.json noch in einer zitierten Quelle belegt.
  [fehler] vorzeichen (Z. 13): Vorzeichen von „+17.002 €“ widerspricht facts.json.
```

Python'dan: `validation.check.validate(text, facts, notes) -> dict`.

## 9. Testler (`tests/test_validation.py`, 46 test)

- **Ayıklama:** bütün biçimler; tarihlerin ve kodların rakam sayılmaması.
- **Yuvarlama kuralı (a):** 13 durum.
- **Örnek yorum:** hatasız geçer; `facts` örneği referans veriyle güncel.
- **Rakam bulguları:** her bulgu türü için bir bozma testi.
- **Not istisnası:** kaynak gösterilmeden ✗, gösterilince ✓.
- **Nedenler:** işaretsiz neden ✗; `(Hypothese)` veya „nicht ersichtlich“ ✓; bilinmeyen kaynak; tablo satırı.
- **Format:** başlık, dönem, tablo başlığı, madde sayısı, soru işareti, liste biçimi, eksik bölüm, bölüm dışı metin.
- **Kapsam ipucu, 13 aylık not penceresi, CLI.**
- **Yanlış alarm testi:** Referans koşunun **720 ayının hepsinde**, `facts.json`'dan doğru biçimde yazılmış yalın bir yorum üretilir: tutarlar, T€ yuvarlaması, yüzdeler, işaretli farklar ve bayrak kanıtları. Doğrulayıcı hiçbirinde `fehler` vermez ve rakam sadakati 1,0 çıkar.

## 10. Bilinen sınırlamalar (v1)

- **Yazıyla rakamlar** („drei Neueinstellungen“) denetlenmez. Notlarda rakamlar hep sayıyla yazılı.
- **Neden cümlesi tanıma kelime listesine dayanır.** Örtük bir nedensellik („Der Großauftrag ließ den Umsatz steigen“) kaçabilir. Uydurma nedenler asıl olarak değerlendirmede, ground truth ile ölçülür (CLAUDE.md 8).
- **Anlamsal kontrol yoktur.** Gösterilen notun iddiayı gerçekten destekleyip desteklemediğine ve hipotezin görülebilir bilgiden türetilip türetilmediğine (B3) bakılmaz. İdeal yorumlarda bunu içerik planı garanti eder; model çıktılarında değerlendirme ölçer.
- **Karşılaştırma etiketi denetlenmez.** „Vj. …“ yazılan değerin gerçekten önceki yılın aynı ayına mı, yoksa önceki aya mı ait olduğuna bakılmaz; ikisi de aynı satırın değeri. v2 için aday.
- **Tesadüfi eşleşme:** Yanlış bir rakam, aynı satırın başka bir değerine tesadüfen eşit olabilir.

## 11. Sürüm 1.1 (17.10.2026): deneme turundan öğrenilenler

Hızlı denemede üç model aynı örneği yazdı (`trial/outputs/`). v1 bulgularının bir kısmı içerik hatası değil, biçimsel farklılıktı. Değişiklikler, içerik kurallarını gevşetmeden biçimsel farklılıkları ayrı saymak içindir:

| Gözlem | v1 | v1.1 |
|---|---|---|
| Kaynak „Quelle:“ öneki olmadan verildi: `[Kontextnotiz 2025-03 #3]` | Neden işaretsiz, notun rakamı `zahl_notiz_ohne_quelle` | Kaynak sayılır; ayrıca `quellenformat` (biçim) |
| `[Quelle: FACTS]`, `[Flag V2]` | `quelle_unbekannt` (fehler) | `quelle_facts` (hinweis); kaynak sayılmaz |
| Kalın yazı, `---`, girintili madde devamı | Tablo, liste ve Kernaussagen biçim hataları | Yok sayılır |
| „1,91 Mio.“ (€ yok), „4,2 pp.“ | Birimsiz rakam, `zahl_unbelegt` | Mio. € ve yüzde puanı |
| „des Ergebnisses vor Steuern“ | Satır adı tanınmadı, `zahl_falsche_position` | Kısa ad listesine eklendi |

Puanlama tablosu (`trial/score.py`) artık biçim ve içerik hatalarını ayrı gösteriyor. Ollama'nın bellek değerleri (`/api/ps`) bu sürümde güvenilir olmadığı için GPU payı sütunu kaldırıldı.
