# 00 — Karar kaydı

> **Kapsam:** CLAUDE.md Bölüm 12'deki ilk üç adım (firma, BWA satır yapısı, olay kataloğu), bunlardan doğan açık noktalar (tur 2), veri üreteci (tur 3), Katman 1 eşikleri ve yol haritası (tur 4), `facts.json` şeması ve Katman 1 (tur 5) · **Tarih:** 14–15.10.2026
>
> **Belgeler:** [`01_firma_profili.md`](01_firma_profili.md) · [`02_bwa_satir_yapisi.md`](02_bwa_satir_yapisi.md) · [`03_olay_katalogu.md`](03_olay_katalogu.md) · [`04_veri_ureteci.md`](04_veri_ureteci.md) · [`05_facts_semasi.md`](05_facts_semasi.md) · [`yol_haritasi.md`](yol_haritasi.md)

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

Güncel liste ve iş paketlerine göre dağılımı: [`yol_haritasi.md`](yol_haritasi.md), Bölüm 3.

- Eğitim hedeflerinin (ideal yorumların) üretim yöntemi (CLAUDE.md 9). Ertelendi.
- Eğitim/test ayrımı: hangi arketipin test olacağı ve arketip başına varyant sayısı (CLAUDE.md 9). Ertelendi; üreteç bunları parametre olarak alıyor.
- Teknik tercihler (CLAUDE.md 10) ve üslup değerlendirme yöntemi (CLAUDE.md 8).

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
| E18 (malzeme satırı, tur 5) | %15–40 | %5–20 | A2'de kaydedilen Rohertragsquote ayların %11'inde negatifti |

### 7.3 Kullanıcıya sorulan noktalar (tur 4'te cevaplandı, Bölüm 8.1)

1. **A2'de "notla açıkla" vakası az** (referans koşuda 2 `cite`, 2 `either`, 217 `warn`). Nedeni, A2 varyantlarının %80'inin stok değişimini yalnızca envanterde kaydetmesi. Seçenekler:
   - (a) Olduğu gibi bırakmak.
   - (b) A2'de P3 olasılığını düşürmek (ör. %50).
   - (c) A2'de E04/E05 sıklığını artırmak.
   - (d) Ayrım metriği için ayrı, küçük bir test kümesi üretmek.
2. **Muster GmbH'nin olay profili.** v00'ın olayları rastgele. Seed 42'de 2024'te kalıcı bir malzeme zammı ve müşteri kaybı yaşıyor. Faaliyet sonucu −%5,1 → −%2,3 → +%2,7 (2024–2026). Seçenekler:
   - (a) Toparlanma hikâyesi olarak bırakmak.
   - (b) v00'a kalıcı büyük olay içermeyen "sakin" bir profil vermek.
3. **Olay yoğunluğu:** Ayda ~1,5 havuz olayı (ilk tahmin ~2). Olaysız ay hedefi (~%15) tutuluyor; yoğunluğu artırmak olaysız ay oranını düşürür.

---

## 8. Karar turu 4 (15.10.2026)

### 8.1 Kararlar [KARAR]

| Kod | Konu | Karar | Ayrıntı |
|---|---|---|---|
| 1 | A2'de "notla açıkla" vakasının azlığı | **(d):** Ana veri gerçekçi kalır. Ayrım metriği için `cite`/`warn` dengeli ayrı bir test kümesi üretilir; raporda "dengelenmiş set" olarak belirtilir. Bütün arketiplerde eğitim verisindeki `cite` sayısı gösterilir; çok düşükse yalnızca eğitim verisinde fiyat olayları ölçülü artırılır. | 04, Bölüm 8 |
| 2 | Muster GmbH'nin olay profili | **(a):** Toparlanma hikâyesi olarak kalır. | 04, Bölüm 7 |
| 3 | Olay yoğunluğu | Ayda ~1,5 olay kabul edildi. | 03, Bölüm 4 |
| 4 | RAG penceresi | **13 ay** (t−12 … t) + `Firmenprofil`. | 03, Bölüm 5.2 |
| 5 | Katman 1 eşikleri (başlangıç değerleri) | Kalem anlamlı: \|Δ\| ≥ %10 **ve** \|Δ\| ≥ aylık Gesamtleistung'un %0,5'i. Oran anlamlı: ≥ 2 puan. Yorumda en fazla 5 kalem, büyüklüğe göre sıralı. Referans veride sonuçlar gösterilir; gerekirse kalibre edilir. | 05, Bölüm 2 |
| 6 | `facts.json` gereksinimleri | Özetteki yapı temel alınır. Her kalemde bütün karşılaştırmalar (önceki ay, önceki yılın aynı ayı, kümülatif) ve anlamlılık gerekçesi bulunur. Rohertrag adayları `warn` değil nötr "aday" olarak işaretlenir; doğru cevap yalnızca ground truth'ta kalır. Tutarlar tam sayı €, yüzdeler 1 ondalık, şema sürüm alanı var. **Şema kodlamadan önce örnek bir ay üzerinde onaya sunulur.** | 05 |
| 7 | Yol haritası | Proje durumu iş yüküne göre yüzdeyle hesaplanır. Yol haritası ayrı bir dosyada tutulur ve **her adımdan sonra güncellenir**. | `yol_haritasi.md` |

### 8.2 Uygulama (asistan)

- **Profil mekanizması:** `--profile`, `generator/config/profiles/*.toml`. Ana parametre dosyaları değişmez.
- **`--first-variant`:** Ayrı kümelerin referans koşuyla aynı firmaları paylaşmasını önler.
- **Dengelenmiş V2 kümesi:**
  - `data/synthetic/v2_balanced_seed4242/` (seed 4242, v50–v59). Repoda tutulur; `.gitignore` istisnası eklendi.
  - 148 ay: A1 10/10/7, A2 27/27/12, A3 21/21/13 (`cite`/`warn`/`either`).
  - A2'de yeterli `cite` için profilde E04 2–4/yıl ve E05 1–3/yıl kullanıldı. İlk denemede (E04 2–3, E05 1–2) A2'de 14 `cite` vardı.
- **Eğitim verisindeki `cite` sayısı:** Ana veride Rohertrag adayı aylarda A1 10, A2 0, A3 14 (10 varyant/arketip). Bu düşük bulundu ve `train_price_boost` profili hazırlandı (A1 16, A2 3, A3 23). Profil, eğitim verisi üretildiğinde kullanılacak; referans koşu değişmedi.
- **Raporlar:** Her `report.md`'de arketip başına V2 karar tablosu var (bütün aylar ve Rohertrag adayı aylar).
- **`facts.json` şeması** önerildi (`05_facts_semasi.md`): Muster GmbH, Haziran 2025 örneğiyle. Onay bekliyor.
- **Yol haritası:** `yol_haritasi.md`. Durum ~%21; hesap yöntemi dosyada.

### 8.3 Bu turda ortaya çıkan sorular (tur 5'te cevaplandı, Bölüm 9.1)

1. **Anlamlılık hangi karşılaştırmaya göre?** Kararın harfiyen uygulanmasıyla (önceki ay VEYA önceki yılın aynı ayı) referans veride hiçbir ayda 0 kalem çıkmıyor, ayların %22'sinde 5'ten fazla kalem var. Yalnızca önceki yılın aynı ayına göre: %3,2 / %3,6 (`05`, Bölüm 2.1).
2. **`facts.json` şema soruları:** Rohertrag adayının kapsamı, `normal_level` / `base_unusual`, `delta_pct = null` kuralları, kümülatifin rolü (`05`, Bölüm 6).
3. **E18 kalibrasyonu.** Malzeme satırındaki geç fatura kayması %15–40. A2'de kaydedilen Rohertragsquote 26 ayda negatif; ekonomik gerçek %17–34. %5–20'ye indirmek negatif ayları 8'e düşürür. Kabul edilirse referans koşu ve dengelenmiş küme yeniden üretilir.

---

## 9. Karar turu 5 (15.10.2026)

### 9.1 Kararlar [KARAR]

| Kod | Konu | Karar |
|---|---|---|
| 1 | Anlamlılık hangi karşılaştırmaya göre? | **Yalnızca önceki yılın aynı ayına göre.** Önceki ay ve kümülatif bilgi amaçlı. |
| 2 | Rohertrag adayı kapsamı | **Bütün arketiplerde, nötr.** Üreticilerde mevcut stok kuralı (`bestand_fehlt`) ayrıca kalır. Böylece hangi arketip test için ayrılırsa ayrılsın ayrım metriği ölçülebilir. |
| 3 | `normal_level` ve `base_unusual` | Eklenir. |
| 4 | `delta_pct = null` | Sonuç satırlarında ve küçük ya da işaret değiştiren tabanlarda `null`. |
| 5 | Kümülatif | Bilgi amaçlı; sıralamaya girmez. |
| 6 | E18 kalibrasyonu | Malzeme satırında %5–20 (Sonstige Kosten'te %15–40 kalır). Referans koşu ve dengelenmiş V2 kümesi yeniden üretildi. |

Bu cevaplarla `facts.json` şeması 1.0 onaylandı (`05_facts_semasi.md`).

### 9.2 Uygulama (asistan)

- **E18:** `E18_pct_material = [5, 20]`, `E18_pct_other = [15, 40]`.
  - A2'de negatif Rohertragsquote ayları 26 → 8.
  - Dengelenmiş küme: A1 12/12/6, A2 26/26/12, A3 20/20/13 (`cite`/`warn`/`either`).
  - Muster GmbH'nin ekonomik gerçek serisi ve toparlanma hikâyesi değişmedi; E18 yalnızca kaydedilen seriyi etkiler.
- **Katman 1 kodlandı** (`facts/`, 15 test). Referans veride medyan 3 anlamlı kalem; ayların %4,3'ünde 0, %3,6'sında 5'ten fazla kalem.
- **Bayrak isabeti** ölçüldü (`tools/flag_quality.py`, `05`, Bölüm 7). Tek parametre değişikliği: V6'da önceki yıl sınırı %10 → %15 (precision %75 → %72, recall %49 → %63).
- **Tam örnek:** `docs/examples/facts_A1-v00_2025-06.json`. Bir test, dosyanın referans veriyle güncel olduğunu kontrol eder.

## 10. Karar turu 6 (15.10.2026): model tarafı

Seçenekler, gerekçeler ve kullanıcının istediği ek açıklamalar: `06_model_tarafi_secenekler.md`.

### 10.1 Kararlar [KARAR]

| Kod | Konu | Karar |
|---|---|---|
| A1 | Temel model | **Almanca deneme turu** üç adayla: Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B. ~10 `facts.json` örneği, aynı istem, sıfır atış. Ölçütler: akıcılık, format, rakam sadakati, bellek ve hız. Eşitlikte Ministral 3 8B [ÖNERİ]. |
| B3 | Notta geçmeyen nedenler | Hedef metin açık soru sorar ya da `(Hypothese)` işaretli genel bir hipotez verir. Hipotez yalnızca modelin görebildiği bilgiden (facts, bayraklar, K-B) türetilir. Ground truth'taki gerçek neden hedef metne hiçbir zaman yazılmaz. |
| B4 | Çıktı yapısı (CLAUDE.md 6.3) | Dört bölüm; Kernaussagen en fazla 3; sabit tablo sütunları; ~250–350 kelime (tablo hariç); her neden cümlesinde `[Quelle: …]` veya `(Hypothese)`; boş bölümde „Keine.“ |
| D1 | Embedding | BGE-M3 |
| D2 | Vektör deposu | Chroma (gömülü) |
| D3 | K-C getirme | Firma + 13 aylık pencere filtresi, ardından anlamsal top-k (başlangıç k = 8). "Penceredeki bütün notlar" ablation'da karşılaştırma. Yeni metrik: retrieval isabeti (recall@k). |
| D4 | K-D | İlk sürümde kapalı; sonra ayrı deney. |

A1'i kullanıcı onayladı. B3, B4 ve D1–D4'ü kullanıcı asistana bıraktı; asistanın önerisi olduğu gibi karar olarak kaydedildi.

### 10.2 Donanım bilgisi

- Kullanıcının bilgisayarı: Monster Abra V15.2 (~2019), Intel i7-9750H, 16 GB RAM, NVIDIA GTX 1650 4 GB.
- Asistanın değerlendirmesi (`06`, A2.1) [ÖNERİ]:
  - Geliştirme, embedding, deneme turu ve demo bu makinede yapılabilir.
  - Fine-tuning ve toplu değerlendirme bulutta yapılmalı: Kaggle (ücretsiz) veya kiralık GPU.
- Bu oturumun bulut ortamında GPU yok. Asistan defterleri hazırlar, kullanıcı çalıştırır.

### 10.3 Açık kalanlar (tur 7'de cevaplandı, Bölüm 11)

| Kod | Konu | Asistanın önerisi |
|---|---|---|
| C1 | Test arketipi | A1 (Muster GmbH) ve iki test düzeyi: yeni sektör + yeni firma |
| C2 | Varyant sayısı | Kullanıcı 20'yi sordu. Öneri: 20 eğitim + 3 doğrulama varyantı / arketip → 960 eğitim ayı. Deneme koşusunda (seed 7) `cite` / `warn` / `either`: 47 / 509 / 19 |
| A2 | Donanım ve bütçe | Dizüstü + Kaggle; kota yetmezse birkaç saatlik kiralık GPU |
| B1 | İdeal yorum yöntemi | Karma (kural tabanlı içerik planı + öğretmen modelin dili + otomatik kontrol) + 20–30 örneklik altın küme |
| B2 | Öğretmen model | Açık ağırlıklı model (ör. Mistral Large 3, Apache 2.0), API üzerinden |

## 11. Karar turu 7 (15.10.2026): eğitim/test, donanım, ideal yorumlar

### 11.1 Kararlar [KARAR]

| Kod | Konu | Karar |
|---|---|---|
| C1 | Test tasarımı | Kullanıcının isteği: testte hem **öğretilmiş** hem **öğretilmemiş** türden örnekler olsun. Buna göre iki test düzeyi var: (1) **Yeni sektör (öğretilmemiş tür):** test arketipi **A1** (Muster GmbH), eğitimde hiç görülmez. (2) **Yeni firma (öğretilmiş tür):** A2 ve A3'ün eğitimde görülmemiş varyantları. Eğitim örneklerinin kendisi teste girmez. |
| C2 | Hacim | A2 + A3, arketip başına 20 eğitim + 3 doğrulama varyantı; profil `train_price_boost` → 960 eğitim ayı, 144 doğrulama ayı. |
| A2 | Donanım | Fine-tuning ve değerlendirme **Kaggle**'da (ücretsiz). Geliştirme, deneme turu ve demo kullanıcının dizüstünde. Kiralık GPU şimdilik yok; gerekirse kullanıcıya sorulur. |
| B1 | İdeal yorum yöntemi | **Karma:** kural tabanlı içerik planı + öğretmen modelin dili + otomatik kontrol. Ek olarak 20–30 örneklik altın küme. |
| B2 | Öğretmen model | **Açık ağırlıklı bir model, API üzerinden.** Somut model ve sağlayıcı [ÖNERİ]: Mistral Large 3, Mistral API (Bölüm 11.2). |

### 11.2 Uygulama ve notlar (asistan)

- **Kümeler tanımlandı** (`04`, Bölüm 9):
  - Eğitim + doğrulama koşusu: seed 7, A2 + A3, v100–v122.
  - Eğitim kümesi (v100–v119) varyant sayısından bağımsız olarak aynı kalıyor; kontrol edildi.
- **Deneme turu örnekleri doğrulama varyantlarından seçilir.** Test kümesi model seçiminde kullanılmaz; aksi hâlde test sonuçları iyimser olur.
- **Öğretmen maliyeti** (tahmini):
  - ~1.000 metin: ~4M girdi ve ~0,6M çıktı token'ı.
  - Kaynaklar Mistral Large 3 için farklı fiyatlar veriyor: 1M token başına 0,50 $ / 1,50 $ ile 2 $ / 5–6 $ arası. Bu da ~3–12 $, tekrarlarla ~5–20 $ demek.
  - Resmî fiyat listesi API anahtarı alınırken kontrol edilecek.
- **Kullanım koşulları:** Üçüncü taraf bir özete göre Mistral'ın ticari koşullarındaki çıktı kısıtı görsel çıktılarla ilgili. Metin çıktıları için bir kısıt bulunamadı; resmî metin kontrol edilecek. Bu not hukuki görüş değildir.

## 12. Karar turu 8 (15.10.2026): doğrulama katmanı

### 12.1 Karar [KARAR]

| Konu | Karar |
|---|---|
| Yuvarlama toleransı (Katman 4) | **(a) Yuvarlamaya uygunluk.** Metindeki rakam, değerin gösterilen hassasiyete doğru yuvarlanmış hâliyse eşleşir (yarım yukarı). 41.712 € → „42 T€“ ✓, „41,7 T€“ ✓, „41 T€“ ✗; 18,4 % → „18 %“ ✓, „19 %“ ✗. |

Reddedilen seçenekler:
- (b) Göreli tolerans: yanlış yuvarlamayı yakalamaz.
- (c) Tam eşleşme: „T€“ kullanılamaz, metin hantallaşır.

### 12.2 Uygulama (asistan)

- **`validation/`** (Katman 4 v1) ve 46 test. Kurallar: `07_dogrulama_katmani.md`.
  - B4'ün uygulama ayrıntıları:
    - numaralı Kernaussagen,
    - sabit tablo başlığı,
    - „- “ maddeleri,
    - boş bölümde „Keine.“,
    - `[Quelle: A; B]` biçimi,
    - `(Hypothese)` işareti.
  - [ÖNERİ] parametreler (`validation/config.toml`):
    - neden ve tahmin kelime listeleri,
    - kısa ad listesi,
    - uzunluk toleransı ±50.
  - [ÖNERİ] **Rakam hangi satıra ait?** Madde veya tablo satırı bir satır adı içeriyorsa rakam yalnızca o satırın değerleriyle karşılaştırılır.
    - Gerekçe: yüzdeler dar bir aralıkta yoğun olduğu için kapsam olmadan uydurma rakamlar tesadüfen eşleşiyordu. Örnek yorumdaki notlu „rund 5 %“ önce `facts.json`'daki 4,9 %'e eşleşiyordu.
- **Örnek yorum:** `examples/kommentar_A1-v00_2025-06.md` (Muster GmbH, Juni 2025). Hatasız geçer, rakam sadakati 1,0. Format örneğidir; altın kümenin ilk adayı olabilir.
- **Yanlış alarm testi:** Referans koşunun 720 ayında, `facts.json`'dan doğru yazılmış rakamlar için hiç `fehler` çıkmıyor.

## 13. Almanca deneme turu: kit (15.10.2026)

Kullanıcının onayıyla hazırlandı ("evet, sen hazırlamaya başla"). Ayrıntılar: `08_deneme_turu.md`.

### 13.1 Uygulama (asistan) [ÖNERİ]

- **Ollama etiketleri** (ollama.com'da doğrulandı), hepsi q4_K_M:
  - `ministral-3:8b-instruct-2512-q4_K_M` (6,0 GB),
  - `gemma4:e4b-it-q4_K_M` (6,6 GB),
  - `qwen3.5:9b-q4_K_M` (6,6 GB).
- **Düşünme modu kapalı.**
- **Üretim ayarları:** `temperature 0.2`, `seed 42`, `num_ctx 8192`, `num_predict 1500`.
- **İstem:** `prompting/` (sürüm 1.0). Almanca sistem mesajı (7 kural ve 6.3 şablonu), sıkıştırılmış `facts.json` ve 13 aylık notlar. Baseline'lar ve fine-tuning da aynı biçimi kullanacak.
- **Örnekler:** Doğrulama varyantlarından 10 ay. Seçimde ground truth yalnızca çeşitlilik için kullanılır: V1–V6, V2 `cite`/`either`/`warn`, sakin ay, çeldirici not.
- **Betikler:**
  - `trial/run_ollama.py`: yalnızca standart kütüphane; kullanıcının bilgisayarında çalışır.
  - `trial/score.py`: doğrulama katmanıyla puanlar.
  - 4 test.

## 14. Almanca deneme turu: sonuçlar (17.10.2026)

### 14.1 Uygulama (asistan)

- **Tam tur:** 3 model × 10 örnek. Kullanıcının bilgisayarında ~5 saat; çıktılar `trial/outputs/`.
- **Puanlama:** `trial/score.py` → `trial/results.md`. Okuma değerlendirmesi: `trial/review.md`.
- **Doğrulama katmanı v1.1–v1.2:** Gerçek çıktılara göre biçimsel toleranslar, kaynak gösterimi ve birimler eklendi (`07`, Bölüm 11). İçerik kuralları değişmedi.
- **Veri bulgusu [ÖNERİ]:** E04 not kalıplarından biri („{material} wird ab {monat} etwa {p} teurer.“) alış fiyatı mı satış fiyatı mı belirsiz. İki model satış fiyatı olarak okudu. Kalıbı netleştirmek veri kümelerini yeniden üretmeyi gerektirir (rakamlar değişmez, yalnızca not metinleri değişir).

### 14.2 Açık karar

| Konu | Seçenekler | Asistanın önerisi |
|---|---|---|
| Temel model (A1) | Gemma 4 E4B / Qwen3.5 9B / Ministral 3 8B | **Gemma 4 E4B.** Rakam sadakati ve uydurmazlık en iyi; en hızlı ve en küçük model. Zayıf yanı (notları az kullanması) RAG + fine-tuning'in tam hedefi. Yedek: Qwen3.5 9B. → Tur 9'da karara bağlandı (Bölüm 15). |

## 15. Karar turu 9 (17.10.2026): temel model ve not kalıpları

### 15.1 Kararlar [KARAR]

| Konu | Karar |
|---|---|
| Temel model | **Gemma 4 E4B.** Yedek: **Qwen3.5 9B**; fine-tuning sonrası sonuçlar yetersiz kalırsa kullanılır. Ministral 3 8B elendi. |
| Fiyat notlarının kalıpları | Alış ve satış fiyatı notları netleştirilir; veri kümeleri yeniden üretilir. |

### 15.2 Uygulama (asistan)

- **Not kalıpları** (`generator/config/note_templates.toml`):
  - E04: „{material} wird ab {monat} etwa {p} teurer.“ → „Im Einkauf wird {material} ab {monat} etwa {p} teurer.“
  - E05: „Neue Preisliste …“ → „Neue Verkaufspreisliste …“ (iki kalıp).
  - Kalıp sayısı değişmediği için seed ile kalıp seçimi aynı kalır.
- **Veri kümeleri yeniden üretildi:** `reference_seed42` ve `v2_balanced_seed4242`. Yalnızca `context_notes.jsonl` metinleri değişti (101 satır), manifest'te de parmak izi değişti. BWA rakamları, olaylar ve ground truth değişmedi; Katman 1 çıktıları ve örnek dosyalar aynı.
- **Deneme turu girdileri dondu:** `trial/inputs/cases.jsonl` modellerin gördüğü hâliyle kalır. Test artık ay seçiminin, facts'in ve not kimliklerinin yeniden üretilebilirliğini denetliyor.

## 16. Karar turu 10 (17.10.2026): bilgi tabanının kapsamı

### 16.1 Kararlar [KARAR]

| Konu | Karar |
|---|---|
| K-A kapsamı | Yalnızca Almanca satır ve oran açıklamaları. **SKR03 hesap aralıkları hiçbir zaman eklenmez.** |
| K-E (sektör oranları) | **Kapsam dışı.** Gerekçe: güvenilir sektör oranları herkese açık değil; doğrulanamayan değerler „kaynaksız iddia yok“ ilkesiyle çelişir. |

### 16.2 Uygulama (asistan)

- **`rag/` (Katman 2 v1):** Ayrıntılar `09_bilgi_tabani.md`'de.
  - `knowledge.toml`: 34 K-A ve 10 K-B parçası, Almanca, rakamsız.
  - BGE-M3 + Chroma.
  - K-A/K-B `facts.json`'dan anahtarla, K-C 13 ay penceresinden anlamsal top-k ile getirilir.
  - CLI ve dışa aktarma (`retrieval.jsonl`).
  - Getirme isabeti aracı: `tools/retrieval_quality.py`.
- **[ÖNERİ] Parametreler:**
  - K-A/K-B'nin anahtarla seçilmesi.
  - Sorgu yöntemi: `single` / `multi` / `multi_expanded`; ölçümle seçilir (`09`, Bölüm 5).
- **Ölçüm (18.10.2026):** Doğrulama varyantlarında `single` en iyisi. Recall çekirdek %94,3, geniş %86,3; çeldirici payı %7,3, bütün notlarda %16,5. Varsayılan `single`, k = 8. Test kümesindeki sonuç rapor için: %91,4 / %83,3 / %5,2.

## 17. İstem 1.1 (18.10.2026)

Kullanıcı istem 1.1'e başlanmasını onayladı („Sen başla“). Yeni bir [KARAR] alınmadı; aşağıdakiler [ÖNERİ]'dir. Ayrıntılar: `10_istem.md`.

### 17.1 Uygulama (asistan)

- **`prompting/` sürüm 1.1:**
  - Katman 2'nin bağlamı isteme girdi: WISSEN (K-B rehberi + K-A açıklamaları) ve KONTEXTNOTIZEN (Firmenprofil + top-8).
  - Deneme turu dersleri 8 kurala işlendi: FACTS/flags/WISSEN kaynak gösterilmez; kendi hesabı yok, `null` değere rakam yok; yüzde ile yüzde puanı; yön; uygun not şartı; `(Hypothese)`; totoloji yok; ek biçim yok.
  - CLI: `python -m prompting` → `<run>/prompts/<varyant>.jsonl` (Kaggle defterleri için).
- **İstem 1.0 donduruldu:** `prompting/v1_0.py`; deneme turu girdileri onunla birebir yeniden üretiliyor (test).
- **Doğrulama v1.3:** K-A/K-B kimlikleri tanınıyor (`quelle_wissen`, hinweis); CLI'de `--retrieval`.
- **`rag export --firms`**, `trial/prepare.py --retrieval` (aynı 10 örnek, istem 1.1), `trial/score.py --review`.

### 17.2 Öneriler [ÖNERİ]

| Konu | Öneri | Gerekçe |
|---|---|---|
| WISSEN'in rolü | Arka plan bilgisi; neden kaynağı sayılmaz. Ondan türetilen neden `(Hypothese)` ister. | B3: notta karşılığı olmayan neden hipotezdir. „Kaynaklı neden oranı“ yalnızca firma notlarını sayar. |
| Varyantlar | `ohne_kontext` (çıplak model, yalnızca FT), `rag_k8` (yalnızca RAG, RAG + FT), `rag_alle` (retrieval katkısı). Sistem mesajı hepsinde aynı. | CLAUDE.md 7'deki tanımlar; fark yalnızca bağlamda kalır. |
| facts'in model görünümü | `schema_version`, `thresholds`, `significance`, `key` modele gitmez. | Model kullanmıyor; eşik rakamları yanlışlıkla aktarılabilir; istem kısalır. |

### 17.3 Açık karar → çözüldü (tur 12)

- **„Yalnızca fine-tuning“ varyantının eğitimi (paket 7):** Aynı modeli bağlamlı eğitip bağlamsız mı çalıştırmalı, yoksa bağlamsız girdilerle ayrı bir model mi eğitmeli? İkincisi, bağlamsız girdiler için ayrı ideal yorumlar gerektirir (paket 5). Seçenekler fine-tuning'den önce kullanıcıya sunulacak.
- **Seçenekler (kullanıcıya sunuldu, 19.10.2026):**
  - **A — Aynı model, testte bağlam çıkarılır.** Ek maliyet yok. Ama model eğitimde hiç görmediği bir girdiyle karşılaşır (hep not görüp atıf yapmayı öğrendi); sonuç „FT yetmez“ yerine dağılım kaymasını ölçebilir.
  - **B — Bağlamsız girdilerle ayrı model.** Plan, görünen not kümesi boş verilerek yeniden kurulur; bütün nedenler hipotez ya da açık soru olur. Ek maliyet: bir öğretmen koşusu (~960 ay, kullanıcının dizüstü), bir eğitim koşusu (Kaggle, girdiler kısa), ~0,5 gün kod. A, ek eğitim gerektirmeden ayrı satır olarak yine raporlanabilir.
  - **C — Tek karma model:** eğitim örneklerinin yarısında bağlam boş. Tek eğitim, ama ana varyant (RAG + FT) daha az bağlamlı örnek görür ve iki davranış birbirine karışabilir.
  - **Asistanın önerisi [ÖNERİ]:** B (+ A ek satır olarak). Adil karşılaştırma ve „bilgi RAG'de, davranış FT'de“ ilkesinin temiz gösterimi.
- **→ Karar (19.10.2026): B** (tur 12, Bölüm 19).

## 18. Karar turu 11 (18.10.2026): öğretmen model ve anahtar

### 18.1 Kararlar [KARAR]

| Konu | Karar |
|---|---|
| Öğretmen model | **Mistral Large 3**, Mistral API üzerinden (B2'deki öneri onaylandı). Kullanıcı hesabı ve „BWA Kommentar“ adlı API anahtarını oluşturdu. Plan: ücretsiz „Experiment“; gerekirse ücretli plana geçmeden önce sorulur. |
| API anahtarı | **Yalnızca kullanıcının bilgisayarında** durur. Sohbete, repoya ya da bulut ortamına girmez. Öğretmen betiği kullanıcının dizüstünde çalışır. |

**Kullanıcıya sunulan bilgi (18.10.2026):**
- Mistral'ın ücretsiz planında API girdileri varsayılan olarak model eğitiminde kullanılabiliyor; veri sentetik olduğu için sorun değil.
- Ücretli planda Mistral Large 3 için kaynakların çoğu 1 milyon token başına ~0,50 $ girdi, ~1,50 $ çıktı veriyor; resmî fiyat kontrol edilecek.
- Bulunan tek çıktı kısıtı görsel çıktılarla ilgili; metin çıktıları için kısıt bulunamadı. Bu bilgi üçüncü taraf bir özetten geliyor; resmî koşullar öğretmen çalışmadan önce kontrol edilecek. Hukuki görüş değildir.
- Gemma 4 Apache 2.0; ince ayarlı model Hugging Face'te yayınlanabilir. Yayın adında „REGU AI“ kullanılmaz (talimat 6); karar paket 10'da.

### 18.2 Uygulama (asistan)

- **`ideal/` hattı** (`11_ideal_yorumlar.md`):
  - İçerik planı: `effects.csv`'deki yıllık farklar; yalnızca görünen notlar kaynak; bayrak/K-B hipotezi ya da „Ursache offen“.
  - Öğretmen istemi, kontrol (doğrulama + plan), dizüstü betiği (stdlib; kontrol ve en fazla 3 deneme dizüstünde).
  - İstek dosyaları: pilot 24, eğitim 960, doğrulama 144 ay.
- **[ÖNERİ] Parametreler:** neden payı %25, en fazla 5 soru, `temperature 0.4`, en fazla 3 deneme, kabul aralığı 200–400 kelime.
- **Rohertrag adayı:** Önceki ayla karşılaştırılır; nedenin yönü tutmalı. 47 `cite` ayından 10'u uyarıya döndü (`11`, 2.2).
- **Sıradaki adım:** Kullanıcı dizüstünde pilotu çalıştırır (`ideal/README.md`).

### 18.3 Pilot 1 (19.10.2026)

- Kullanıcı `--check` ile erişimi doğruladı. İlk denemede model listesi boş geldi; betik artık listeyi gösterip modeli doğrudan deniyor.
- **Güvenlik olayı:** Kullanıcı bir terminal çıktısıyla birlikte API anahtarını sohbete yapıştırdı. Anahtarın silinip yenisinin oluşturulması önerildi; kılavuza „`$env:…` satırını kopyalama“ uyarısı eklendi.
- Pilot: 24 ayın 9'u kabul (%38). Ret nedenleri ve düzeltmeler: `11_ideal_yorumlar.md`, Bölüm 10. Öğretmen istemi 1.1, plan 1.1, doğrulama v1.4.
- Çıktı dosyası yanlışlıkla `main` dalına yüklendi. Çalışma dalına kopyalandı (`ideal/outputs/pilot_v1_0.jsonl`); `main`'e dokunulmadı.

### 18.4 Pilot 2 (19.10.2026)

- 24 ayın 21'i kabul (%88). Okumada içerik sorunları çıktı: kaynaksız neden içeriği, boş ya da etiket kopyası açıklama hücreleri, eklenmiş değerlendirmeler. Kabul edilenlerin 11'i yeni kontrollere takılıyor (`11_ideal_yorumlar.md`, Bölüm 11).
- Öğretmen istemi 1.2, plan 1.2 (yalnızca facts'ten „Einordnung“), içerik kontrolleri, doğrulama v1.5.
- **[ÖNERİ]** Kabul alt sınırı 180 kelime. B4'teki ~250–350 hedef olarak kalır; az maddeli planlarda öğretmenin uydurarak uzatmasını önlemek için.

### 18.5 Pilot 3 (19.10.2026)

- 24 ayın 22'si kabul (%92). İçerik büyük ölçüde temiz.
- Kalan ana sorun: kalem Kernaussage'lerinde neden yok (17/22). Öğretmen 1.3, plan 1.3, Kernaussage neden kontrolü, doğrulama v1.6 (`11_ideal_yorumlar.md`, Bölüm 12).
- **[ÖNERİ]** Ayrı bir pilot 4 yerine doğrulama kümesi (144 ay) çalıştırılır; sonuç iyiyse eğitim kümesi.

### 18.6 Doğrulama kümesi (19.10.2026)

- Öğretmen 1.3: 144 ayın 132'si kabul (%92). Okumada içerik pilot 3 düzeyinde (`11_ideal_yorumlar.md`, Bölüm 13).
- `--retry-failed` artık her turda yeni tohum kullanıyor.
- Sıradaki: eğitim kümesi (960 ay), ardından reddedilenler için `--retry-failed` (eğitim ve doğrulama).

### 18.7 Eğitim kümesi ve yeniden deneme (19.10.2026)

- Öğretmen 1.3, yeniden deneme turu dahil: eğitim **908/960 (%95)**, doğrulama **138/144 (%96)**. Kabul edilen bütün metinler güncel kontrolden yeniden geçti (`11_ideal_yorumlar.md`, Bölüm 14).
- Okuma ve otomatik tarama: metinlerin ~%5'inde bir cümlelik plan dışı yorum (işaretsiz „da“ yan cümlesi, nadiren „Trend“). Oran deneme sayısıyla artıyor (1. deneme %3, 3–4. deneme %8). Rakam ve kaynak sadakati etkilenmiyor.
- **[ÖNERİ]** İkinci yeniden deneme turu yapılmaz; ret çarpıklığı küçük (A3 %9, A2 %1).
- **[ÖNERİ]** Eğitim verisi birleştirilirken rakamdan önceki tire ASCII eksiye çevrilir (metinlerin ~%10'u).
- **[ÖNERİ]** Plan dışı yan cümleler bilinen sınırlama; gerekirse 3–4. denemede kabul edilen 172 metin ablation olarak çıkarılır.
- Sıradaki: altın küme (20–30 doğrulama ayı) ve eğitim verisinin birleştirilmesi (öğrenci istemi 1.1 `rag_k8` + kabul edilen metin).

## 19. Karar turu 12 (19.10.2026): „yalnızca fine-tuning“ varyantı

### 19.1 Karar [KARAR]

| Konu | Karar |
|---|---|
| „Yalnızca FT“ varyantı | **B:** Bağlamsız girdilerle (istem 1.1 `ohne_kontext`) ayrı bir model eğitilir. Hedefleri aynı plan kodu, görünen not kümesi boş verilerek kurar; kaynak yoktur, bütün nedenler hipotez ya da açık soru olur. RAG + FT modelinin bağlamsız çalıştırılması (A) ek eğitim gerektirmeden ayrı satır olarak raporlanır. |

### 19.2 Uygulama (asistan)

- `python -m ideal build --variant ohne_kontext` → `ideal/requests/{train,val}_ohne.jsonl.gz` (960 + 144 ay; `train`/`val` ile aynı aylar). Plan kodu değişmedi.
- **[ÖNERİ]** Öğrenci girdisi istem 1.1 `ohne_kontext`: FACTS var, WISSEN ve KONTEXTNOTIZEN „Keine.“ Hedeflerdeki genel hipotez metinleri (K-B'den) bu modelin girdisinde yok; ince ayarla öğrenilir. Bu B3'ü bozmaz: firmaya özgü bilgi ya da ground truth değil, genel muhasebe bilgisi.
- Kalıp metin 1.104 bağlamsız planın hepsinde kontrolü geçiyor.
- Öğretmen betiği: `--set train_ohne|val_ohne`. Kayıtlar girdinin parmak izini (`input_sha`) taşır; girdisi değişen ay yeniden üretilir. Mevcut kayıtlara, üretildikleri istek dosyalarından hesaplanan parmak izi eklendi (başka alan değişmedi).
- Sıra: önce `val_ohne` (okuma), sonra `train_ohne` (`ideal/README.md`, Bölüm 6).

### 19.3 V6 düzeltmesi (Katman 1, [ÖNERİ] parametre)

- **Bulgu:** Bağlamsız planları okurken görüldü. V6 kuralı yalnızca „önceki yıla göre değişim < %15“ diye bakıyordu. Örnek: önceki aya göre −%14,8, önceki yıla göre −%14,9 olan bir ay da „mevsimsel“ sayılıyordu. Plan bu bayrağa „Veränderung gegenüber dem Vorjahresmonat deutlich kleiner“ gerekçesini yazıyordu. Eğitim kümesinde 394 V6 bayrağının 103'ünde bu gerekçe rakamlarla çelişiyordu (önceki yıla göre değişim, önceki aya göre değişimin yarısından büyük).
- **Değişiklik:**
  - Katman 1: V6 için ayrıca önceki yıla göre değişim ya ters yönde ya da önceki aya göre değişimin en fazla yarısı olmalı (`facts/config.toml`, `v6_max_ratio = 0.5`). Referans koşuda precision %72 → %78, recall %63 → %58 (`05_facts_semasi.md`, Bölüm 7).
  - Plan: Ters yönde ve benzer büyüklükteki değişimde gerekçe „in die entgegengesetzte Richtung“ olur.
- **Etki:** Bayrağı kalkan 58 ayın bağlamı (sorgu ve WISSEN bayrağa bağlı) yeniden getirildi. Öğretmen girdisi değişen aylar: eğitim 67, doğrulama 6 (`11_ideal_yorumlar.md`, Bölüm 15.4).
- K-B metni değişmedi; yeni kuralla uyumlu.
- Deneme turu girdileri (`trial/inputs/`) tarihî kayıt olarak eski kuralla kalır.
- Getirme isabeti (`09`, Bölüm 5) eski kuralla ölçüldü; test kümesinde 720 ayın 44'ünde bayrak değişiyor. Paket 9'da yeniden ölçülecek.

### 19.4 Kaynak sırası düzeltmesi

- Eşit etkili iki olayın sırası Python'un hash tohumuna bağlıydı; aynı ay iki kurulumda farklı kaynak sırası alabiliyordu.
- Düzeltme: eşitlikte olay kimliği belirler. İstek dosyaları artık her kurulumda bayt bayt aynı.
- Bu yüzden ayrıca yeniden üretilecek aylar: eğitim 20, doğrulama 3. Toplam yeniden üretim: eğitim 87, doğrulama 9.

### 19.5 Sonuçlar (20.10.2026)

- Eğitim: yeniden üretilen 87 ayın 80'i kabul; toplam **901/960**. Doğrulamadaki 9 ay henüz üretilmedi (yüklenen dosya değişmemişti).
- `val_ohne`: **134/144** kabul. Kaynak ve somut neden izi yok; içerik bağlamlı kümelerle aynı düzeyde (`11_ideal_yorumlar.md`, Bölüm 16).
- **[ÖNERİ]** `train_ohne` başlatılır. Eğitimde reddedilen 7 yeni ay için ayrı bir yeniden deneme yapılmaz.

### 19.6 Plan 1.4: yön tutarlılığı (21.10.2026)

- `train_ohne` 923/960 kabul. Okumada bulgu: plan „ungewöhnlich hoher/niedriger Vergleichswert“ kelimesini farkın yönünden türetiyordu. Örnek: ikramiye ayında taban yüksekken „niedriger“ diyordu. Bağlamlı eğitimde taban hipotezlerinin %30'u rakamlarla çelişiyordu. Ayrıca 29 satırda geç fatura hipotezi bir düşüşü açıklıyordu.
- **[ÖNERİ] Plan 1.4:** Taban hipotezi yalnızca taban sapmayı açıklıyorsa (cari ve kendi dönemindeki normal düzeye göre ters yönde olağandışı); bayrak hipotezi yalnızca yönü uyuşuyorsa. Aksi hâlde „Ursache offen“ + soru (`11_ideal_yorumlar.md`, Bölüm 17).
- Girdisi değişen 555 ay yeniden üretilecek (eğitim 163, doğrulama 27, `train_ohne` 319, `val_ohne` 46).
- Betik: geçerlilik yalnızca girdinin parmak iziyle; `--retry-failed` her girdiyi en fazla bir kez yeniden dener (`--max-rounds 2`).

### 19.7 Öğretmen aşaması tamamlandı (22.10.2026)

- Kabul: `train` 907/960, `val` 138/144, `train_ohne` 940/960, `val_ohne` 142/144. Bütün kayıtlar plan 1.4 girdisiyle; taramalar temiz (`11_ideal_yorumlar.md`, Bölüm 18).
- Toplam öğretmen kullanımı: girdi 17,7 Mio, çıktı 5,0 Mio token (ücretsiz plan).
- Sıradaki: altın küme ve eğitim verisinin birleştirilmesi.

## 20. Eğitim verisi, altın küme ve baseline defteri (22.10.2026)

- **Eğitim verisi** (`12_egitim_verisi.md`, Bölüm 1): `train_rag` 898, `val_rag` 133, `train_ohne` 933, `val_ohne` 140 örnek.
  - **[ÖNERİ] Temizlik:** eksi işareti; uyarı Kernaussage'sine eksikse planın kısa hipotezi („Hinweis: … (Hypothese).“); plandan sapan Kernaussage'li aylar dışarıda; temizlenen her metin yeniden kontrol.
- **Altın küme:** 30 metin. 14'ü düzeltmesiz, 10'u yalnızca otomatik düzeltmeyle, 6'sı elle düzeltildi. Baskın kusur, uyarı Kernaussage'sinde eksik uyarı dili (~%40); otomatik tamamlamanın gerekçesi bu.
- **Plan 1.5 / öğretmen 1.4:** Karışık zamanlı kaynaklarda hangi notun önceki yıla ait olduğu ayrıca söylenir. 8 ay girdisi değiştiği için eğitimde dışarıda.
- **Test istemleri:** `ohne_kontext`, `rag_k8`, `rag_alle` × 720 ay (`reference_seed42`).
- **[ÖNERİ] Çıkarım altyapısı (değişti; 23.10.2026 yeniden değişti, Bölüm 21):**
  - Değerlendirme vLLM yerine Unsloth + Transformers ile, 4-bit.
  - Gerekçe: E4B gömmelerle 8B parametre; float16'da tek T4'e (16 GB) sığmıyor. Gemma'nın T4'teki float16 taşmalarına Unsloth'ta düzeltme var. Bütün varyantlar aynı 4-bit tabanı kullanır.
  - Demo yine Ollama (GGUF).
- **[ÖNERİ] Üretim ayarları:** deneme turuyla aynı (`temperature 0.2`, `seed 42`, en fazla 1.500 token).
- **Kaggle:** `gpu/01_baseline.ipynb` (çıplak model ve yalnızca RAG); kullanıcı adımları `gpu/README.md`. Önce 2 istemlik deneme koşusu.

## 21. Kaggle deneme koşusu ve çıkarım altyapısı (23.10.2026)

- **Deneme koşusu 1 (Transformers + Unsloth, tek T4):** Hat uçtan uca çalıştı, ama çok yavaş (`12_egitim_verisi.md`, Bölüm 4.1).
  - Yüklemeden sonra 11,3 / 15,6 GB bellek; parti boyutu 1'e kadar düştü.
  - ~5 token/s, istem başına ~150 s. Tam baseline ~60 saat sürerdi (oturum 12 saat, haftalık kota ~30 saat).
- **[ÖNERİ] Çıkarım altyapısı (yeniden değişti):**
  - Baseline ve değerlendirme Ollama (llama.cpp) ile, `gemma4:e4b-it-q4_K_M`. Her T4'e bir sunucu, sunucu başına 4 eşzamanlı istem.
  - Gerekçe:
    - Hız.
    - Deneme turuyla aynı model ve nicemleme.
    - Demo ile aynı biçim.
  - İnce ayarlı modeller GGUF'a aktarılıp aynı düzende çalıştırılır.
  - 22.10'daki „Unsloth + Transformers 4-bit“ önerisinin (Bölüm 20) yerini alır.
- **Karar gerektirmeyen değişiklik:** Donanım (Kaggle T4, tur 7) ve model (Gemma 4 E4B, tur 9) aynı kalıyor.
- **Açık risk:**
  - Eğitim de T4'te float32 hesaplamayla yavaş olabilir.
  - İnce ayar defteri önce hızı ölçer.
  - Çok yavaşsa tur 7 ya da tur 9 kararı yeniden kullanıcıya sorulur. Seçenekler:
    - daha kısa eğitim;
    - Gemma 4 E2B;
    - Qwen3.5 9B;
    - kiralık GPU.
- **İlk okuma (4 metin):**
  - Rakam değerleri doğru; iki metinde binlik ayırıcı boşluk.
  - Yön hataları var; bir kaynak yanlış kullanılmış; işaretsiz nedenler var; metinler kısa.
  - Doğrulama, boşluklu rakamları iki sayı olarak okuyor. Puanlamada biçim, değerden ayrı sayılacak (paket 8).
- **Deneme koşusu 2 (Ollama, iki T4):** 16 istem, hata yok (`12_egitim_verisi.md`, Bölüm 4.4).
  - Akış başına 37–52 token/s, 8 eşzamanlı istem.
  - Tam koşu tahmini 2 varyant için ~1,8 saat (önce ~60 saat).
  - Token sayıları Transformers koşusuyla birebir aynı: şablon ve tokenizer aynı.
- **[ÖNERİ] `rag_alle` baseline'a eklendi:** Bütün notlarla RAG da çıplak modelle çalışır. Ek maliyet ~40 dakika. Retrieval'ın katkısı böylece hem taban hem ince ayarlı modelde ölçülür.

## Kaynak

- DATEV-BWA örneği (yapı doğrulaması): [Bundestag lobi sicili, BWA 12/2023](https://www.lobbyregister.bundestag.de/media/db/a9/485560/BWA-12-2023-8-1-2024-Auszug.pdf)
