# 02 — BWA satır yapısı

> **Kapsam:** CLAUDE.md Bölüm 12, adım 2 (Bölüm 5.3'teki [AÇIK] maddenin kapatılması) · **Tarih:** 14.10.2026
>
> **Etiket kuralı:** `01_firma_profili.md` ile aynı. Başlıklardaki seçimler [KARAR], sayısal parametreler [ÖNERİ].

---

## 1. Doğrulama kaynağı

Satır listesi, kamuya açık gerçek bir DATEV-BWA ile karşılaştırıldı. Belge Bundestag lobi sicilinde yayımlanmış: "Kurzfristige Erfolgsrechnung", Dezember 2023, `BWA-Form: DATEV-BWA`, `Wareneinsatz: Wareneinkauf`, SKR04 ([kaynak](https://www.lobbyregister.bundestag.de/media/db/a9/485560/BWA-12-2023-8-1-2024-Auszug.pdf)). Belgeden yalnızca yapı alındı; rakamları kullanılmadı.

**CLAUDE.md 5.3'teki ilk listeye göre bulunan farklar:**

1. Nötr kalemler alt satırlara ayrılıyor: Zinsaufwand + Sonstiger neutraler Aufwand → Neutraler Aufwand; Zinserträge + Sonstiger neutraler Ertrag + Verrechnete kalk. Kosten → Neutraler Ertrag.
2. Ergebnis vor Steuern'den önce bir "Kontenklasse unbesetzt" kontrol satırı var.
3. Form 01'de önceki yıl sütunu yok. Sütunlar şunlar: ay değeri, % Ges.-Leistung, % Ges.-Kosten, % Pers.-Kosten, Aufschlag ve bunların kümülatif (Ocak–ay) karşılıkları. Önceki yıl karşılaştırması DATEV'de ayrı bir "Vorjahresvergleich" sayfasında verilir.
4. Tutarlar EUR cinsinden ve iki ondalıklı.

---

## 2. Kesin satır listesi [KARAR: B1 = C]

DATEV'e yakın ama sade bir liste: nötr alt satırlar korunur, sentetik veride hep 0 olacak iki satır çıkarılır.

| # | Anahtar (`line`) | Kanonik ad | DATEV baskı etiketi (alias) | Tür |
|---:|---|---|---|---|
| 1 | `umsatzerloese` | Umsatzerlöse | Umsatzerlöse | Temel |
| 2 | `bestandsveraenderungen_fe_ue` | Bestandsveränderungen FE/UE | Bestandsveränderg. FE/UE | Temel (±) |
| 3 | `aktivierte_eigenleistungen` | Aktivierte Eigenleistungen | Aktivierte Eigenleistungen | Temel |
| 4 | `gesamtleistung` | **Gesamtleistung** | Gesamtleistung | Ara toplam |
| 5 | `material_wareneinkauf` | Material-/Wareneinkauf | Material-/Wareneinkauf | Temel |
| 6 | `rohertrag` | **Rohertrag** | Rohertrag | Ara toplam |
| 7 | `sonstige_betriebliche_erloese` | Sonstige betriebliche Erlöse | So. betr. Erlöse | Temel |
| 8 | `betrieblicher_rohertrag` | **Betrieblicher Rohertrag** | Betrieblicher Rohertrag | Ara toplam |
| 9 | `personalkosten` | Personalkosten | Personalkosten | Temel |
| 10 | `raumkosten` | Raumkosten | Raumkosten | Temel |
| 11 | `betriebliche_steuern` | Betriebliche Steuern | Betriebliche Steuern | Temel |
| 12 | `versicherungen_beitraege` | Versicherungen/Beiträge | Versicherungen/Beiträge | Temel |
| 13 | `besondere_kosten` | Besondere Kosten | Besondere Kosten | Temel |
| 14 | `fahrzeugkosten` | Fahrzeugkosten (ohne Steuer) | Fahrzeugkosten (ohne Steuer) | Temel |
| 15 | `werbe_reisekosten` | Werbe-/Reisekosten | Werbe-/Reisekosten | Temel |
| 16 | `kosten_warenabgabe` | Kosten der Warenabgabe | Kosten Warenabgabe | Temel |
| 17 | `abschreibungen` | Abschreibungen | Abschreibungen | Temel |
| 18 | `reparatur_instandhaltung` | Reparatur/Instandhaltung | Reparatur/Instandhaltung | Temel |
| 19 | `sonstige_kosten` | Sonstige Kosten | Sonstige Kosten | Temel |
| 20 | `gesamtkosten` | **Gesamtkosten** | Gesamtkosten | Ara toplam |
| 21 | `betriebsergebnis` | **Betriebsergebnis** | Betriebsergebnis | Sonuç |
| 22 | `zinsaufwand` | Zinsaufwand | Zinsaufwand | Temel |
| 23 | `sonstiger_neutraler_aufwand` | Sonstiger neutraler Aufwand | Sonstiger neutraler Aufwand | Temel |
| 24 | `neutraler_aufwand` | **Neutraler Aufwand** | Neutraler Aufwand | Ara toplam |
| 25 | `zinsertraege` | Zinserträge | Zinserträge | Temel |
| 26 | `sonstiger_neutraler_ertrag` | Sonstiger neutraler Ertrag | Sonstiger neutraler Ertrag | Temel |
| 27 | `neutraler_ertrag` | **Neutraler Ertrag** | Neutraler Ertrag | Ara toplam |
| 28 | `ergebnis_vor_steuern` | **Ergebnis vor Steuern** | Ergebnis vor Steuern | Sonuç |
| 29 | `steuern_einkommen_ertrag` | Steuern vom Einkommen und Ertrag | Steuern Einkommen u. Ertrag | Temel |
| 30 | `vorlaeufiges_ergebnis` | **Vorläufiges Ergebnis** | Vorläufiges Ergebnis | Sonuç |

Toplam 30 satır: 21 temel satır ve 9 hesaplanan satır.

**Çıkarılan DATEV satırları:**
- `Verrechnete kalk. Kosten`: Kalkulatorische Kosten kullanılmıyor; değeri her zaman 0 olurdu.
- `Kontenklasse unbesetzt`: Atanmamış hesaplar için bir kontrol satırı; sentetik veride her zaman 0 olurdu.

DATEV çıktısındaki "Kostenarten:" bir ara başlıktır, satır değildir.

---

## 3. Hesaplama kuralları

Ara toplamlar ham veride **tutulmaz**; her zaman Katman 1'de hesaplanır.

```
gesamtleistung          = umsatzerloese + bestandsveraenderungen_fe_ue + aktivierte_eigenleistungen
rohertrag               = gesamtleistung − material_wareneinkauf
betrieblicher_rohertrag = rohertrag + sonstige_betriebliche_erloese
gesamtkosten            = Σ (personalkosten … sonstige_kosten)          # satır 9–19
betriebsergebnis        = betrieblicher_rohertrag − gesamtkosten
neutraler_aufwand       = zinsaufwand + sonstiger_neutraler_aufwand
neutraler_ertrag        = zinsertraege + sonstiger_neutraler_ertrag
ergebnis_vor_steuern    = betriebsergebnis − neutraler_aufwand + neutraler_ertrag
vorlaeufiges_ergebnis   = ergebnis_vor_steuern − steuern_einkommen_ertrag
```

Oranlar (CLAUDE.md 6.2, Katman 1): Rohertragsquote, Personalkostenquote, Materialquote ve Betriebsergebnis-Marge, her biri Gesamtleistung'a bölünerek hesaplanır.

---

## 4. Gösterim kuralları [KARAR: D1–D4]

| Kod | Kural |
|---|---|
| D1 | **Satır adları:** Kanonik ad açık yazılır (tablodaki "Kanonik ad" sütunu). Model girdisinde ve çıktısında bu ad kullanılır. DATEV baskı etiketleri yalnızca alias olarak durur; DATEV görünümlü dışa aktarımda kullanılabilir. Makine anahtarı `line` sütunundaki ASCII addır. |
| D2 | **Tutarlar:** EUR, iki ondalıklı. Yorum metnindeki yuvarlama (`42 T€`) Katman 4'te toleransla eşleştirilir. |
| D3 | **İşaretler:** DATEV gösterimi kullanılır. Gelir ve gider satırları pozitif yazılır; işareti satırın türü belirler. `bestandsveraenderungen_fe_ue` pozitif veya negatif olabilir (artış = +). Hesaplanan sonuç satırları negatif olabilir. Gider satırları da istisna olarak negatif olabilir (ör. alacak dekontu). |
| D4 | **Wareneinsatz ayarı = "Wareneinkauf":** `material_wareneinkauf` satırı alışları gösterir. Üretici arketiplerde (A1, A3) hammadde stok değişimi modellenmez; mamul/yarı mamul stok değişimi yalnızca satır 2'de görünür. Ticaret arketipinde (A2) satır 2 her zaman 0'dır; ticari malın stok değişimi kaydedilirse (P3'e bağlı) satır 5'in içinde yer alır. |

---

## 5. Ham veri formatı [KARAR: B2 = A]

- Ham veri **yalnızca 21 temel satırın aylık değerlerini** içerir. Ara toplam, kümülatif değer, oran ve karşılaştırma ham veride bulunmaz.
- Format: uzun (tidy) CSV, her satırda bir firma–ay–BWA satırı.

```csv
firm_id,period,line,value
A1-v00,2025-06,umsatzerloese,765312.40
A1-v00,2025-06,bestandsveraenderungen_fe_ue,21480.00
A1-v00,2025-06,personalkosten,305870.20
...
```

*(Değerler açıklayıcıdır. Haziran Muster GmbH için çeyrek sonudur; bu yüzden Bestandsveränderung bu ayda kayıtlıdır ve Urlaubsgeld Personalkosten'e eklenmiştir.)*

- Firma meta verisi (arketip, pratik profili, sezon parametreleri) ayrı bir dosyada tutulur; bkz. `01_firma_profili.md`.
- **Plan verisi yok** (D6).

**Türetilmiş görünümler** (Katman 1 veya dışa aktarım, ham veri değil):

| Görünüm | Sütunlar |
|---|---|
| DATEV Form 01 görünümü | Monat · % Ges.-Leistung · % Ges.-Kosten · % Pers.-Kosten · kumuliert (Jan–Monat) · % Ges.-Leistung · % Ges.-Kosten · % Pers.-Kosten |
| Vorjahresvergleich görünümü | Monat · Vorjahresmonat · Abw. absolut · Abw. % · kumuliert · Vorjahr kumuliert · Abw. absolut · Abw. % |
| `facts.json` | Önceki aya ve önceki yılın aynı ayına göre farklar, kümülatif karşılaştırma, oranlar, bayraklar (CLAUDE.md 6.2; şema [AÇIK]) |

---

## 6. Satırların sentetik veride davranışı [ÖNERİ]

| Satır | Temel davranış | Etkileyen olaylar (03) |
|---|---|---|
| Umsatzerlöse | taban × trend × sezon endeksi × gürültü | E05, E06, E07, E19 |
| Bestandsveränderungen FE/UE | (üretim − satış) × Herstellkostenfaktor; A1'de küçük, A3'te büyük, A2'de hep 0. Kayıt zamanı P3'e bağlı. | E16 |
| Aktivierte Eigenleistungen | 0 (katalogda ilgili olay yok) | – |
| Material-/Wareneinkauf | Materialquote × gerçek Gesamtleistung (A2'de alış bir ay önce gelir) | E04, E06, E07, E18 |
| Sonstige betriebliche Erlöse | küçük sabit + gürültü | – |
| Personalkosten | çalışan sayısı × aylık maliyet; Sonderzahlungen P1'e göre ya her aya yayılır ya da ödeme ayında görünür | E01, E02, E03, E13, E14 |
| Raumkosten | sabit | E09 |
| Betriebliche Steuern | küçük sabit | – |
| Versicherungen/Beiträge | sabit (tahakkuklu) ya da Ocak'ta yıllık prim (P2) | E15 |
| Besondere Kosten | küçük sabit | – |
| Fahrzeugkosten (ohne Steuer) | sabit | – |
| Werbe-/Reisekosten | sabit | E11 |
| Kosten der Warenabgabe | Umsatz'a oransal | (dolaylı: E06, E07) |
| Abschreibungen | sabit aylık ya da yalnızca Aralık'ta (P4) | E08, E17 |
| Reparatur/Instandhaltung | sabit | E12 |
| Sonstige Kosten | sabit | E18 |
| Zinsaufwand | sabit | E08 |
| Sonstiger neutraler Aufwand | 0 | – |
| Zinserträge | 0 | – |
| Sonstiger neutraler Ertrag | 0 | E10 |
| Steuern vom Einkommen und Ertrag | 0. Sadeleştirme: gelir vergileri Jahresabschluss'ta kaydedilir. Çeyreklik ön ödemeler kataloğa alınmadı. | – |

- Sabit giderler yıllık ~%2 oranında yavaşça artar (enflasyon kayması).
- Gürültü ve olay büyüklükleri: `03_olay_katalogu.md`.

---

## 7. Hesap planı [KARAR: D5]

- Hesap planı **SKR03**.
- Hangi hesabın hangi BWA satırına aktığı (SKR03 → BWA eşlemesi) bilgi tabanı K-A'nın içeriğidir ve o adımda yazılacak.
- Veri üreteci doğrudan BWA satırı düzeyinde çalıştığı için (B2 = A) bu eşlemeye ihtiyaç duymaz.
