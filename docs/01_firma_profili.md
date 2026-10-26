# 01 — Kurgusal firmalar

> **Kapsam:** CLAUDE.md Bölüm 12, adım 1 · **Tarih:** 14.10.2026
>
> **Etiket kuralı:** Başlıklarda belirtilen seçimler **[KARAR]**. Sayısal parametreler (oranlar, endeksler, aralıklar, olasılıklar) aksi yazmadıkça **[ÖNERİ]**. Bunlar veri üreteci yazılırken kalibre edilecek; her değişiklik kullanıcıya bildirilip `00_karar_kaydi.md` dosyasına işlenecek.
>
> **Odak:** Firmaların amacı LLM için eğitim ve test durumları üretmek (CLAUDE.md G7). Gerçekçilik "yeterli" düzeyde tutulur, karmaşıklık en aza indirilir.

---

## 1. Yapı [KARAR: K1 = C]

- **Üç arketip** elle tanımlanır (Bölüm 3).
- Veri üreteci her arketipten **çok sayıda varyant** üretir. Varyantlar büyüklük, oranlar, sezon genliği, muhasebe pratiği ve olay dizisi bakımından farklılaşır (Bölüm 5).
- **Muster GmbH**, A1 arketipinin sabit vitrin varyantıdır (`A1-v00`). Portfolyodaki örnek çıktılar bu firmadan gelir.
- **Test**, eğitimde hiç görülmemiş bir arketip üzerinde yapılır.
- **[AÇIK, ertelendi]** Hangi arketipin test için ayrılacağı ve arketip başına kaç varyant üretileceği, CLAUDE.md Bölüm 9'daki eğitim/test ayrımı kararıyla birlikte belirlenecek.
- **[KARAR, tur 2]** Bu karar beklenirken üreteç arketip listesini ve arketip başına varyant sayısını **parametre** olarak alır. Böylece sonradan verilecek karar kod değişikliği gerektirmez.

**Gerekçe:** 36 aylık bir seride önceki yıl karşılaştırması yapılabilen ay sayısı 24'tür. Tek firmayla ~24 örnek çıkar ve bu LoRA için çok az. Varyant üretimi bu hacmi yüzlerce aya çıkarır.

---

## 2. Zaman aralığı [KARAR: K5 = A]

| Özellik | Değer |
|---|---|
| Seri | 01/2024 – 12/2026, 36 ay, bütün varyantlarda aynı takvim |
| Yalnızca karşılaştırma tabanı | 2024 (yorum üretilmez) |
| Yorumlanabilir aylar | 01/2025 – 12/2026, varyant başına 24 ay |
| Not | Son aylar bugünün (14.10.2026) ilerisinde kalıyor; veri sentetik olduğu için sorun değil. |

---

## 3. Arketipler [KARAR: K2 = A (+ B, C), K3 = B]

| Kod | Firma | Sektör | Çalışan | Ciro 2024 | Projedeki rolü |
|---|---|---|---|---|---|
| **A1** | **Muster GmbH** | Metallverarbeitung / Zulieferer für Maschinenbau (CNC-Dreh- und Frästeile, Baugruppen) | 55 | 8,4 Mio € | Vitrin firması. FE/UE stoku olduğu için V2 anlamlı; makine yoğun olduğu için AfA belirgin. Hafif sezon. |
| A2 | Beispiel Haustechnik GmbH | Sanitär- und Heizungsgroßhandel | 40 | 14 Mio € | Ticaret yapısı: yüksek Wareneinkauf, düşük Rohertrag. V2 farklı biçimde görünür (Bölüm 4). |
| A3 | Exempel Outdoor GmbH | Hersteller von Gartenmöbeln | 110 | 15 Mio € | Güçlü sezon (V6). Satış ve üretim zamanlaması çok farklı olduğu için stok hareketi büyük (V2 çok belirgin). |

- K3 kararı (≈55 çalışan, ≈8,4 Mio €) Muster GmbH için geçerli. A2 ve A3'ün büyüklükleri, 20–200 çalışan bandında çeşitlilik sağlamak için seçildi [ÖNERİ].
- Firma adları kurgusaldır.

### 3.1 Maliyet yapısı (% Gesamtleistung, yıllık ortalama) [ÖNERİ]

| Satır | A1 Muster | A2 Haustechnik | A3 Outdoor |
|---|---:|---:|---:|
| Material-/Wareneinkauf | 42,0 | 72,0 | 45,0 |
| **Rohertrag** | **58,0** | **28,0** | **55,0** |
| Sonstige betriebliche Erlöse | 0,3 | 0,3 | 0,3 |
| Personalkosten | 33,0 | 14,0 | 30,0 |
| Raumkosten | 3,0 | 2,5 | 3,0 |
| Betriebliche Steuern | 0,2 | 0,1 | 0,2 |
| Versicherungen/Beiträge | 0,8 | 0,4 | 0,7 |
| Besondere Kosten | 0,3 | 0,1 | 0,2 |
| Fahrzeugkosten (ohne Steuer) | 1,0 | 1,8 | 0,8 |
| Werbe-/Reisekosten | 0,6 | 0,6 | 3,0 |
| Kosten der Warenabgabe | 1,2 | 1,5 | 3,0 |
| Abschreibungen | 5,0 | 0,8 | 3,5 |
| Reparatur/Instandhaltung | 2,2 | 0,4 | 1,2 |
| Sonstige Kosten | 4,5 | 2,8 | 4,0 |
| **Gesamtkosten** | **51,8** | **25,0** | **49,6** |
| **Betriebsergebnis** | **6,5** | **3,3** | **5,7** |
| Zinsaufwand | 0,4 | 0,3 | 0,5 |
| **Ergebnis vor Steuern** | **6,1** | **3,0** | **5,2** |

**Çalışan başına yaklaşık personel maliyeti:** A1 ≈ 50 T€, A2 ≈ 49 T€, A3 ≈ 41 T€ yıllık (işveren payları dahil).

### 3.2 Muster GmbH — tahakkuk edilmiş ortalama ay (2024) [ÖNERİ]

Bu ay, mevsim etkisinden, muhasebe pratiğinden ve gürültüden arındırılmış ekonomik ortalamadır. Gerçek aylar bundan sapar.

| Satır | € / ay | % GL |
|---|---:|---:|
| Umsatzerlöse | 700.000 | 100,0 |
| Bestandsveränderungen FE/UE (yıllık ortalama) | 0 | 0,0 |
| Aktivierte Eigenleistungen | 0 | 0,0 |
| **Gesamtleistung** | **700.000** | **100,0** |
| Material-/Wareneinkauf | 294.000 | 42,0 |
| **Rohertrag** | **406.000** | **58,0** |
| Sonstige betriebliche Erlöse | 2.100 | 0,3 |
| **Betrieblicher Rohertrag** | **408.100** | **58,3** |
| Personalkosten | 231.000 | 33,0 |
| Raumkosten | 21.000 | 3,0 |
| Betriebliche Steuern | 1.400 | 0,2 |
| Versicherungen/Beiträge | 5.600 | 0,8 |
| Besondere Kosten | 2.100 | 0,3 |
| Fahrzeugkosten (ohne Steuer) | 7.000 | 1,0 |
| Werbe-/Reisekosten | 4.200 | 0,6 |
| Kosten der Warenabgabe | 8.400 | 1,2 |
| Abschreibungen | 35.000 | 5,0 |
| Reparatur/Instandhaltung | 15.400 | 2,2 |
| Sonstige Kosten | 31.500 | 4,5 |
| **Gesamtkosten** | **362.600** | **51,8** |
| **Betriebsergebnis** | **45.500** | **6,5** |
| Zinsaufwand | 2.800 | 0,4 |
| **Ergebnis vor Steuern** | **42.700** | **6,1** |
| Steuern vom Einkommen und Ertrag | 0 | 0,0 |
| **Vorläufiges Ergebnis** | **42.700** | **6,1** |

Yıllık: Betriebsergebnis ≈ 546 T€. Personalkosten düzeyi (~230 T€/ay), CLAUDE.md 6.3'teki örnekle aynı büyüklükte.

### 3.3 Sezon profilleri (ay endeksi, ortalama = 1,00) [ÖNERİ]

| Ay | A1 Umsatz | A2 Umsatz | A3 Umsatz | A3 Üretim |
|---|---:|---:|---:|---:|
| Ocak | 0,92 | 0,80 | 0,45 | 1,05 |
| Şubat | 0,98 | 0,85 | 0,70 | 1,10 |
| Mart | 1,08 | 1,00 | 1,30 | 1,15 |
| Nisan | 1,02 | 1,02 | 1,70 | 1,10 |
| Mayıs | 1,04 | 1,02 | 1,75 | 1,00 |
| Haziran | 1,06 | 1,00 | 1,50 | 0,95 |
| Temmuz | 1,00 | 0,98 | 1,10 | 0,85 |
| Ağustos | 0,78 | 0,92 | 0,85 | 0,70 |
| Eylül | 1,08 | 1,08 | 0,65 | 0,90 |
| Ekim | 1,08 | 1,15 | 0,55 | 1,05 |
| Kasım | 1,06 | 1,15 | 0,70 | 1,05 |
| Aralık | 0,90 | 1,03 | 0,75 | 1,10 |

**A1:**
- Ağustos'ta Betriebsferien, Aralık'ta tatil ve yavaş Ocak başlangıcı var.
- Siparişe göre üretim yapıldığı için üretim ≈ satış. Bestandsveränderung küçüktür (Umsatz'ın ±%1–3'ü).
- İstisna: Betriebsferien'den önce Temmuz'da stok için üretilir (üretim endeksi satıştan +0,12 fazla), Ağustos'ta stoktan satılır (−0,12). Bu, V2 için anlamlı bir yaz deseni oluşturur [ÖNERİ, veri üreteci].

**A2:**
- Ocak–Şubat'ta inşaat yavaş. Sonbaharda ısıtma sezonu var.
- Mal alımı satıştan yaklaşık bir ay önce gelir (Einkauf_t ∝ Umsatz_t+1).

**A3:**
- Satış ilkbaharda, üretim ise kış ve ilkbaharda yoğun.
- `Bestandsveränderung ≈ (Üretim − Satış) × Herstellkostenfaktor (~0,7)`.
- Yıl içinde stok Şubat sonunda en yüksek, Ağustos sonunda en düşük düzeyde. Yıllık toplam 0.

**Trend:**
- Muster GmbH: olaylardan bağımsız temel büyüme 2025'te +%3, 2026'da +%2.
- Varyantlarda yıllık −%2 … +%6 arasında çekilir.

---

## 4. Muhasebe pratiği profilleri [KARAR: K4 = C]

Çarpıklıkların kaynağı firmanın muhasebe pratiğidir. Her arketipin **baskın bir profili** var:

| Arketip | Baskın profil | Organizasyonla bağlantısı |
|---|---|---|
| A1 Muster | **Karma** | Kaufmännischer Leiter Controlling'i de yürütüyor; zamanı kısıtlı. |
| A2 Haustechnik | **Tipik KOBİ** | Controlling yok; ay sonu kayıtlarının bir kısmı Jahresabschluss'a kalıyor. |
| A3 Outdoor | **Disiplinli** | Ayrı bir Controller var; aylık kapanış düzenli. |

### 4.1 Varyant düzeyinde pratik olasılıkları [ÖNERİ]

**Neden:** Pratikler arketip başına sabit olsaydı, örneğin V3 yalnızca A2'de görülürdü. A2 test için ayrılırsa model V3'ü eğitimde hiç görmezdi. Bu yüzden her varyant pratiklerini arketipe özgü olasılıklarla çeker. Böylece hangi arketip ayrılırsa ayrılsın her çarpıklık türü eğitimde görülür. A3 varyantlarının çoğu yine de "temiz" kalır; bu da yanlış alarm (precision) ölçümü için gerekli.

| Kod | Pratik | Tetiklediği olay (03) | A1 | A2 | A3 |
|---|---|---|---:|---:|---:|
| P1 | Urlaubs- ve Weihnachtsgeld tahakkuksuz, ödeme ayında kaydedilir | E13, E14 (V1) | 0,6 | 0,9 | 0,1 |
| P2 | Yıllık primler (sigorta) tahakkuksuz, Ocak'ta tek seferde kaydedilir | E15 (V1) | 0,6 | 0,9 | 0,1 |
| P3 | Bestandsveränderung her ay kaydedilmez | E16 sistematik (V2) | 0,5 (yalnızca çeyrek sonları) | 0,8 (yalnızca envanterde, Wareneinkauf satırında) | 0,0 |
| P4 | AfA yalnızca yıl sonunda kaydedilir | E17 (V3) | 0,3 | 0,7 | 0,0 |
| P5 | Geç gelen alış faturaları (yıllık sıklık) | E18 (V4) | 2–4 | 4–6 | 0–2 |
| – | Bestandsveränderung'ün ara sıra unutulması (yıllık sıklık) | E16 epizodik (V2) | 0–1 (P3 yoksa) | – | 1–2 |

**Kapsama kontrolü:**

| Test için ayrılan | Eğitimde V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| A1 | A2, A3 | A2, A3 | A2 | A2, A3 |
| A2 | A1, A3 | A1, A3 | A1 | A1, A3 |
| A3 | A1, A2 | A1, A2 | A1, A2 | A1, A2 |

### 4.2 Muster GmbH'nin sabit profili

| Pratik | Muster GmbH (`A1-v00`) |
|---|---|
| P1 Sonderzahlungen tahakkuksuz | evet |
| P2 Yıllık sigorta primi Ocak'ta | evet |
| P3 Bestandsveränderung | yalnızca çeyrek sonlarında (Mart, Haziran, Eylül, Aralık) |
| P4 AfA yalnızca yıl sonunda | hayır (aylık) |
| P5 Geç gelen alış faturaları | yılda ~3 |

**Diğer v00 varyantları [ÖNERİ, veri üreteci]:** `A2-v00` (Beispiel Haustechnik GmbH) ve `A3-v00` (Exempel Outdoor GmbH) arketiplerinin baskın profilini birebir alır.
- A2-v00: P1–P4 evet, yılda 5 geç fatura.
- A3-v00: P1–P4 hayır, yılda 1 geç fatura, yılda 1 unutulan stok değişimi.

---

## 5. Varyant üretimi [ÖNERİ]

| Parametre | Aralık |
|---|---|
| Büyüklük çarpanı | 0,6 – 1,6 × arketip (çalışan sayısı her zaman 20–200 bandında) |
| Maliyet oranları | arketip değerinin ±%10'u (göreli) |
| Sezon genliği | endeksin 1,00'dan sapması × 0,7 – 1,3 |
| Temel büyüme | yıllık −%2 … +%6 |
| Muhasebe pratiği | Bölüm 4.1'deki olasılıklarla |
| Olay dizisi | `03_olay_katalogu.md`'deki sıklıklarla |
| Gürültü | `03_olay_katalogu.md`, Bölüm 6 |
| Adlandırma | v00 arketipin adını taşır (`A1-v00` = Muster GmbH). Diğer varyantlar sabit bir kurgusal ad listesinden ad alır (ör. "Modell Präzisionsteile GmbH"). Böylece model tek bir firma adını ezberlemez. |
| Varyant sayısı | Üretecin parametresi [KARAR]. Kesin değer **[AÇIK]**, eğitim/test kararıyla birlikte belirlenecek. İlk fikir: arketip başına ~10 varyant → 3 × 10 × 24 = 720 yorumlanabilir ay. |

---

## 6. Organizasyon ve paydaşlar [KARAR: D10]

| | A1 Muster | A2 Haustechnik | A3 Outdoor |
|---|---|---|---|
| Rechtsform | GmbH | GmbH | GmbH |
| Yönetim | Gesellschafter-Geschäftsführer; kaufmännischer Leiter (Controlling dahil) | Geschäftsführer; Leitung Buchhaltung | Geschäftsführer; kaufmännischer Leiter; 1 Controller |
| Günlük finans muhasebesi | Şirket içinde, DATEV tabanlı | Şirket içinde, ERP'nin Fibu modülü | Şirket içinde, DATEV tabanlı |
| Steuerberater | Lohnabrechnung + Jahresabschluss | Lohnabrechnung + Jahresabschluss | Jahresabschluss (Lohn şirket içinde) |
| Hausbank | Kontokorrent + Investitionsdarlehen | Kontokorrent (stok finansmanı) | Kontokorrent (sezon finansmanı) + Investitionsdarlehen |
| BWA bankaya | Her ay (P4 problemi) | Her ay | Her ay |
| Hesap planı | SKR03 (D5) | SKR03 | SKR03 |
| Plan verisi | İlk sürümde yok (D6) | yok | yok |

Bu yapı CLAUDE.md 4.1'deki karma modele uyuyor: günlük muhasebe şirket içinde, bilanço büroda.
