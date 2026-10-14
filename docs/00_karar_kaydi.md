# 00 — Karar kaydı: Adım 1–3

> **Kapsam:** CLAUDE.md Bölüm 12'deki ilk üç adım (firma, BWA satır yapısı, olay kataloğu) ve bunlardan doğan açık noktalar (tur 2) · **Tarih:** 14.10.2026
>
> **Belgeler:** [`01_firma_profili.md`](01_firma_profili.md) · [`02_bwa_satir_yapisi.md`](02_bwa_satir_yapisi.md) · [`03_olay_katalogu.md`](03_olay_katalogu.md)

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

**Asistanın uygulama yorumları [ÖNERİ — onay bekliyor]:**
- **3a:** "Açıklanamayan" kavramı iki parçaya bölündü. Sayısal kısmı Katman 1 kontrol eder: önceki aya ve önceki yılın aynı ayına göre birlikte sapma (sezon dışı). Bağlamsal kısmı model kontrol eder: o ayda açıklayan bir not var mı? Ground truth'a `acceptable_flags` alanı eklendi (03, Bölüm 7.2 ve 9.1).
- **3b:** Notlu olayların ~%50'sinin notu rakam içerecek. Rakamlar yuvarlanacak ve BWA'daki etkiden biraz farklı olabilecek (03, Bölüm 5.4).
- **Şema:** Olay kaydındaki `persistence` alanı `shape` olarak yeniden adlandırıldı. Kalıcı/geçici bilgisi ayrı bir `duration` alanında tutuluyor (03, Bölüm 7.1).

## 5. Açık kalan noktalar [AÇIK]

- Eğitim hedeflerinin (ideal yorumların) üretim yöntemi (CLAUDE.md 9). Ertelendi.
- Eğitim/test ayrımı: hangi arketipin test olacağı ve arketip başına varyant sayısı (CLAUDE.md 9). Ertelendi; üreteç bunları parametre olarak alıyor.
- RAG penceresinin kesin değeri (şimdilik 12 ay).
- Anlamlılık eşikleri ve `facts.json` şeması (CLAUDE.md 6.2).
- Teknik tercihler (CLAUDE.md 10) ve üslup değerlendirme yöntemi (CLAUDE.md 8).

---

## 6. Sonraki adımlar için notlar [ÖNERİ]

- CLAUDE.md 6.3'teki örnek çıktıda Rohertragsquote %31 (önceki yıl %38). Bu değer metal işleyici profiline (~%58) uymuyor. Veri üretildikten sonra örneğin Muster GmbH verisiyle yeniden yazılmasını öneriyorum.
- Bölüm 12'deki sıradaki adım: **veri üreteci**. Üreteç, 01–03'teki parametrelerle ham BWA verisini, bağlam notlarını (K-C) ve ground truth dosyalarını üretecek.

## Kaynak

- DATEV-BWA örneği (yapı doğrulaması): [Bundestag lobi sicili, BWA 12/2023](https://www.lobbyregister.bundestag.de/media/db/a9/485560/BWA-12-2023-8-1-2024-Auszug.pdf)
