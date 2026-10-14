# 00 — Karar kaydı

> **Kapsam:** CLAUDE.md Bölüm 12'deki ilk üç adım (firma, BWA satır yapısı, olay kataloğu), bunlardan doğan açık noktalar (tur 2) ve veri üreteci (tur 3) · **Tarih:** 14.10.2026
>
> **Belgeler:** [`01_firma_profili.md`](01_firma_profili.md) · [`02_bwa_satir_yapisi.md`](02_bwa_satir_yapisi.md) · [`03_olay_katalogu.md`](03_olay_katalogu.md) · [`04_veri_ureteci.md`](04_veri_ureteci.md)

---

## 1. Proje odağı [KARAR]

Kullanıcı, 14.10.2026: Projenin odak noktası, **fine-tuning ve RAG uygulanan LLM'dir**. Sentetik veri üreteci ve hesaplama katmanı bu modeli eğitmek ve ölçmek için gereken destek bileşenleridir. Gerçekçilikleri yeterli düzeyde tutulur, karmaşıklıkları en aza indirilir. CLAUDE.md'de **G7** olarak kayıtlı.

### Odakla uyum kontrolü

Önerilen kararlar bu odakla çelişmiyor. Çoğu doğrudan model davranışını ölçmek için tasarlandı:

| Karar | Model tarafına katkısı |
|---|---|
| K1 = C (arketip + varyant) | Fine-tuning için yeterli örnek hacmi; eğitimde görülmemiş arketipte genelleme testi |
| K4 = C (farklı muhasebe pratikleri) | Bayraklı aylarda uyarı dili; "temiz" firmada yanlış alarm vermeme |
| B2 = A (yalnızca aylık temel değerler) | Veri tarafını hafif tutar; emek modelde kalır |
| E2 = B (%70/%30 + çeldirici notlar) | Kaynaklı neden ile tahmin ayrımını ve uydurma neden oranını ölçülebilir kılar |
| E3 = B (olaysız aylar dahil) | Olay yokken neden uydurmama davranışını test eder |

**Odak nedeniyle yapılan tek ince ayar:** Muhasebe pratikleri arketip başına sabit değil; her varyant pratiklerini arketipe özgü olasılıklarla çeker (01, Bölüm 4.1). Böylece hangi arketip test için ayrılırsa ayrılsın, her çarpıklık türü eğitimde görülür. Arketiplerin baskın profilleri (karma / tipik KOBİ / disiplinli) K4 kararındaki gibi kalır.

---

## 2. Kararlar [KARAR]

Bütün kararlar kullanıcının onayıyla asistanın önerileri doğrultusunda verildi.

| Kod | Konu | Seçim |
|---|---|---|
| K1 | Firma yapısı | **C** — 3 arketip + üreteçle çok sayıda varyant; Muster GmbH vitrin varyantı; test, eğitimde görülmemiş arketipte |
| K2 | Sektör | **A1 Muster GmbH:** Metallverarbeitung / Zulieferer · **A2:** Sanitär-/Heizungsgroßhandel · **A3:** Gartenmöbel-Hersteller |
| K3 | Büyüklük (Muster GmbH) | **B** — ~55 çalışan, ~8,4 Mio € ciro (aylık ~700 T€) |
| K4 | Muhasebe pratiği | **C** — arketip başına farklı baskın profil: A1 karma, A2 tipik KOBİ, A3 disiplinli |
| K5 | Zaman aralığı | **A** — 01/2024–12/2026, 36 ay |
| B1 | Satır listesi | **C** — DATEV Form 01'e yakın; nötr alt satırlar ayrı; `Verrechnete kalk. Kosten` ve `Kontenklasse unbesetzt` çıkarıldı (30 satır) |
| B2 | Ham veri formatı | **A** — yalnızca 21 temel satırın aylık değerleri; geri kalan her şey Katman 1'de hesaplanır |
| E1 | Katalog kapsamı | **A** — önerilen 19 olay türü (E01–E19) |
| E2 | Kasıtlı boşluk | **B** — gerçek olayların ~%70'i notlu; V1–V4 notsuz; ayların ~%10–15'inde çeldirici not |
| E3 | Olay yoğunluğu | **B** — ayda ~2 olay; ayların ~%15'inde yeni olay yok |
| D1 | Satır adları | Kanonik açık adlar; DATEV kısaltmaları alias |
| D2 | Tutarlar | EUR, 2 ondalık |
| D3 | İşaretler | DATEV gösterimi; giderler pozitif; Bestandsveränderung ve sonuç satırları ± |
| D4 | Wareneinsatz ayarı | "Wareneinkauf" |
| D5 | Hesap planı | SKR03 |
| D6 | Plan verisi | İlk sürümde yok |
| D7 | Gürültü | Temel satırlara ±%2–4; olayların ~%20'si eşik yakınında |
| D8 | Çakışma | Aynı satır ve ayda en fazla 2 olay; olayların ~%10'u çakışır |
| D9 | Ground truth alanları | 03, Bölüm 7 |
| D10 | Organizasyon | Karma model (günlük muhasebe şirket içinde, Jahresabschluss Steuerberater'da); Hausbank; BWA her ay bankaya |

## 3. Etiket kuralı (docs/ içinde)

- Yukarıdaki başlık düzeyindeki seçimler **[KARAR]**.
- Belgelerdeki sayısal parametreler (maliyet oranları, sezon endeksleri, olasılıklar, büyüklük aralıkları, sıklıklar) **[ÖNERİ]**. Veri üreteci yazılırken kalibre edilecekler; her değişiklik kullanıcıya bildirilip bu kayda işlenecek.

---

## 4. Karar turu 2 (14.10.2026) [KARAR]

İlk turda açık kalan noktalar için kullanıcının kararları:

| Kod | Konu | Karar | Ayrıntı |
|---|---|---|---|
| 3a | A2'de V2 tespiti | V2 kuralı arketipe göre ayrılır. Üreticide (A1, A3) mevcut kural kalır; toptancıda (A2) uyarı, açıklanamayan ani Rohertragsquote değişimine bağlanır. | 03, Bölüm 9.1 |
| 3b | Notlardaki rakamlar | Notlarda rakam olabilir. Doğrulama katmanı, RAG'in getirdiği notlardaki rakamları kaynak gösterilmesi şartıyla kabul eder. | 03, Bölüm 5.4 |
| 3c | Süre alanı ve RAG penceresi | Notlara `dauerhaft`/`temporär` alanı eklenir. RAG penceresi şimdilik 12 ay (çalışma varsayımı, sonra netleşecek). | 03, Bölüm 5.2 |
| 1, 2 | Eğitim hedefleri, eğitim/test ayrımı | **Ertelendi.** Üreteç, arketip ve varyant sayısını parametre olarak alır ve her olayı eksiksiz kaydeder: ay, satır, büyüklük, kalıcı/geçici, nota yazılıp yazılmadığı. | 01, Bölüm 1; 03, Bölüm 7 |

**Asistanın uygulama yorumları** (3a yorumu tur 3'te onaylandı; diğerleri [ÖNERİ]):
- **3a [KARAR, tur 3]:** "Açıklanamayan" kavramı iki parçaya bölündü. Sayısal kısmı Katman 1 kontrol eder: önceki aya ve önceki yılın aynı ayına göre birlikte sapma (sezon dışı). Bağlamsal kısmı model kontrol eder: o ayda açıklayan bir not var mı? Ground truth'a `acceptable_flags` alanı eklendi (03, Bölüm 7.2 ve 9.1).
- **3b:** Notlu olayların ~%50'sinin notu rakam içerecek. Rakamlar yuvarlanacak ve BWA'daki etkiden biraz farklı olabilecek (03, Bölüm 5.4).
- **Şema:** Olay kaydındaki `persistence` alanı `shape` olarak yeniden adlandırıldı. Kalıcı/geçici bilgisi ayrı bir `duration` alanında tutuluyor (03, Bölüm 7.1).

## 5. Açık kalan noktalar [AÇIK]

- Eğitim hedeflerinin (ideal yorumların) üretim yöntemi (CLAUDE.md 9). Ertelendi.
- Eğitim/test ayrımı: hangi arketipin test olacağı ve arketip başına varyant sayısı (CLAUDE.md 9). Ertelendi; üreteç bunları parametre olarak alıyor.
- RAG penceresinin kesin değeri (şimdilik 12 ay). Üreteçten gelen bir gözlem bu karara girdi olacak (03, Bölüm 9.4).
- Anlamlılık eşikleri ve `facts.json` şeması (CLAUDE.md 6.2). `expected_flags`'in süzülmesi de buna bağlı.
- Teknik tercihler (CLAUDE.md 10) ve üslup değerlendirme yöntemi (CLAUDE.md 8).
- Tur 3'ten doğan iki soru (Bölüm 7.3): A2'de "notla açıkla" vakasının azlığı ve Muster GmbH'nin olay profili.

---

## 6. Sonraki adımlar için notlar [ÖNERİ]

- CLAUDE.md 6.3'teki örnek çıktıda Rohertragsquote %31 (önceki yıl %38). Bu değer metal işleyici profiline (~%58) uymuyor. Veri üretildikten sonra örneğin Muster GmbH verisiyle yeniden yazılmasını öneriyorum.
- Veri üreteci tamamlandı (Bölüm 7). Bölüm 12'deki sıradaki adım: **hesaplama modülü (Katman 1)**. Bu adım anlamlılık eşiklerine (CLAUDE.md 6.2, [AÇIK]) ihtiyaç duyacak.

---

## 7. Karar turu 3 ve veri üreteci (14.10.2026)

### 7.1 Kararlar [KARAR]

| Kod | Konu | Karar | Ayrıntı |
|---|---|---|---|
| 1 | V2 ayrımının uygulanması | Onaylandı: Katman 1 yalnızca sayısal adayı işaretler; notla açıklanıp açıklanmadığına model karar verir. **Değerlendirmede bu ayrım ayrıca ölçülür.** Ay kaydında `rohertrag_causes` ve `v2_candidate_decision` alanları; CLAUDE.md 8'e "V2 adayı ayrımı" metriği eklendi. | 03, Bölüm 7.2 ve 9.1 |
| 2 | Referans koşu | Seed 42, 3 arketip × 10 varyant repoda: `data/synthetic/reference_seed42/`. Diğer koşular `.gitignore`'da. | 04, Bölüm 1 ve 6 |
| 3 | Not metinleri | Şablonla başlanır. Her olay türü için 4–5 cümle kalıbı (uygulamada 5); seçimi seed yapar. LLM ile çeşitlendirme ileride eklenebilecek bir seçenek olarak not edildi. | 03, Bölüm 5.5 |

**Asistanın uygulama kararları** (karar 2 ve 3'ün uygulanması):
- Dosyalar `model_input/` ve `evaluation/` olarak iki klasöre ayrıldı (03, Bölüm 7.4).
- Bir firmanın sezon notu (`Firmenprofil`) yazı-tura yerine dengeli bir diziyle seçiliyor; böylece her arketipte varyantların tam %70'i not alıyor.

### 7.2 Kalibrasyon değişiklikleri [ÖNERİ etiketli parametreler]

İlk deneme koşusunda olaylar maliyet yönünde birikiyordu ve firmaların faaliyet sonucu marjı 2026'ya kadar ortalama −%15'e düşüyordu (A1 −%15,5; A2 −%8,3; A3 −%10,8). Aşağıdaki değişikliklerden sonra yıllık ortalama marjlar %0–5 aralığında kalıyor ve hafif bir marj baskısı var:

| Parametre | Önceki | Yeni | Neden |
|---|---|---|---|
| E01 sıklığı / büyüklüğü | 2–4/yıl, +%2–8 | 1–3/yıl, +%2–5 | Kadro yılda ~%9 büyüyordu |
| E02 büyüklüğü | −%2–6 | −%2–5 | E01 ile simetri |
| E03 (tarife) | +%2,5–5,5 | +%2–4 | Ücretler ciro trendinden belirgin hızlı artıyordu |
| E04 kalıcı payı | %50 | %20 | Kalıcı zamlar Rohertragsquote'yi yılda ~3 puan düşürüyordu |
| E06 sıklığı | 2–3/yıl | 2–4/yıl | Olaysız ay oranını ~%15'te tutmak için (marjı bozmayan geçici olay) |
| E07 sıklığı | 0–1/yıl (en fazla 2) | Seri boyunca 0–1 | Kalıcı ciro kaybı birikiyordu |
| AfA / faiz tabanı | Sabit | Yılda −%6 / −%10 | Yeni yatırımlar (E08), eski varlıkların ve kredilerin bitişi olmadan birikiyordu |
| Çakışma kabulü | Yalnızca üst sınır (2) | Dolu satır-aya ikinci olay %30 olasılıkla; aynı tür aynı ayda başlayamaz | Çakışma oranı %23'tü (hedef ~%10) |

### 7.3 Kullanıcıya sorulan noktalar [AÇIK]

1. **A2'de "notla açıkla" vakası az** (referans koşuda 2 `cite`, 2 `either`, 217 `warn`). Nedeni, A2 varyantlarının %80'inin stok değişimini yalnızca envanterde kaydetmesi. Seçenekler:
   - (a) Olduğu gibi bırakmak.
   - (b) A2'de P3 olasılığını düşürmek (ör. %50).
   - (c) A2'de E04/E05 sıklığını artırmak.
   - (d) Ayrım metriği için ayrı, küçük bir test kümesi üretmek.
2. **Muster GmbH'nin olay profili.** v00'ın olayları rastgele. Seed 42'de 2024'te kalıcı bir malzeme zammı ve müşteri kaybı yaşıyor. Faaliyet sonucu −%5,1 → −%2,3 → +%2,7 (2024–2026). Seçenekler:
   - (a) Toparlanma hikâyesi olarak bırakmak.
   - (b) v00'a kalıcı büyük olay içermeyen "sakin" bir profil vermek.
3. **Olay yoğunluğu:** Ayda ~1,5 havuz olayı (ilk tahmin ~2). Olaysız ay hedefi (~%15) tutuluyor; yoğunluğu artırmak olaysız ay oranını düşürür.

## Kaynak

- DATEV-BWA örneği (yapı doğrulaması): [Bundestag lobi sicili, BWA 12/2023](https://www.lobbyregister.bundestag.de/media/db/a9/485560/BWA-12-2023-8-1-2024-Auszug.pdf)
