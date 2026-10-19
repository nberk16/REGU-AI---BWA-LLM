# BWA Yorumlayıcısı — Proje Özeti (Brief)

> **Amaç:** Bu belge, bir önceki sohbette yapılan problem/çözüm çalışmasının özetidir. Bir yapay zekâ asistanının (Claude Code) projeye kaldığı yerden devam edebilmesi için yazılmıştır.
>
> **Etiketler:**
> - **[KARAR]** = kullanıcıyla netleşti, değiştirmeden önce kullanıcıya sor
> - **[ÖNERİ]** = önerildi, henüz onaylanmadı
> - **[AÇIK]** = karar verilmedi
>
> **Tarih:** 18.10.2026 · **Aşama:** Tasarım, **veri üreteci**, **hesaplama modülü (Katman 1)**, **bilgi tabanı v1 (Katman 2)**, **doğrulama katmanı (Katman 4)**, **istem 1.1** ve **ideal yorum hattı** tamamlandı (karar turları 1–11). Model tarafının yöntem kararları alındı (turlar 6–7, [`docs/06_model_tarafi_secenekler.md`](docs/06_model_tarafi_secenekler.md)); temel model Gemma 4 E4B (tur 9). Proje durumu ~%55, iş yüküne göre; bkz. [`docs/yol_haritasi.md`](docs/yol_haritasi.md).

---

## 0. Asistan için çalışma talimatları

1. Kullanıcıyla **Türkçe** konuş. Ürünün ürettiği yorum metni **Almanca** olacak. Almanca muhasebe terimleri olduğu gibi kullanılır (bkz. Bölüm 13, Sözlük).
2. Proje **eğitim ve portfolyo** amaçlı. Öncelik model performansı değil, **problem–çözüm ilişkisinin net ve ölçülebilir şekilde gösterilmesi**.
3. **[AÇIK]** maddelerde kendi başına karar verme. Seçenekleri gerekçeleriyle sun ve kullanıcıya sor.
4. Gerçek müşteri verisi yok ve kullanılmayacak. **Tüm veri sentetik.**
5. Bu belge hukuki veya vergi danışmanlığı değildir. Sektör bilgileri genel çerçevedir.
6. Kaynak sektör belgesindeki "rakipler", "REGU AI", satış stratejisi ve donanım paketi gibi kısımlar başka bir projeye aittir. **Bu projede kullanılmaz.**
7. **[KARAR]** Her adımdan sonra [`docs/yol_haritasi.md`](docs/yol_haritasi.md) güncellenir: iş paketlerinin durumu, iş yüküne göre tamamlanma yüzdesi ve açık kararlar. Kararlar ayrıca [`docs/00_karar_kaydi.md`](docs/00_karar_kaydi.md)'ye işlenir.

---

## 1. Tek cümlede proje

Bir Mittelstand işletmesinin aylık **BWA** raporunu alan bir sistem: rakamları **kodla** hesaplar, firmanın bağlam bilgisini **RAG** ile getirir ve **LoRA ile ince ayar yapılmış küçük bir LLM** kullanarak kaynak gösteren, Almanca bir **yönetim yorumu taslağı** üretir.

---

## 2. Kullanıcının koyduğu gereksinimler [KARAR]

| # | Gereksinim |
|---|---|
| G1 | Sektör: Almanya muhasebe sektörü, Mittelstand ağırlıklı |
| G2 | Problem **işletme** (şirket içi finans) tarafından gelmeli; vergi danışmanlığı bürosu (Steuerkanzlei) tarafından değil |
| G3 | Çözüm **küçük bir LLM**; **RAG + fine-tuning** ile |
| G4 | Amaç eğitim ve portfolyo, piyasa ürünü değil |
| G5 | Performanstan çok problem–çözüm ilişkisi ön planda |
| G6 | Kaynak belgeden yalnızca sektör bilgisi kullanılır (bkz. talimat 6) |
| G7 | Projenin odak noktası **fine-tuning ve RAG uygulanan LLM'dir**. Veri üreteci ve hesaplama katmanı bu modeli eğitmek ve ölçmek için gereken destek bileşenleridir; yeterli gerçekçilikte ve olabildiğince basit tutulur (14.10.2026) |

---

## 3. Seçim süreci (bağlam)

Değerlendirilen üç fikir:

| Fikir | Özet | Durum |
|---|---|---|
| Kontierung asistanı | Gelen faturaya hesap (SKR03/04), vergi anahtarı ve maliyet merkezi önerisi | Asistanın ilk önerisiydi; seçilmedi |
| E-fatura hata açıklayıcısı | XRechnung/ZUGFeRD doğrulama hatalarını açıklama + tedarikçiye düzeltme e-postası taslağı | Seçilmedi (problem dar) |
| **BWA yorumlayıcısı** | Aylık BWA'dan Almanca yönetim yorumu taslağı | **[KARAR] Kullanıcı bunu seçti** |

**BWA fikrinde baştan belirlenen risk:** Küçük LLM'ler sayısal akıl yürütmede zayıf.
**Tasarım cevabı:** Hesaplamayı kod yapar, model yalnızca yorumlar (bkz. Bölüm 6).

---

## 4. Sektör bağlamı (yalnızca projeyle ilgili kısım)

### 4.1 Veri zinciri

- Mittelstand işletmesi belgeyi üretir. Muhasebe ya şirket içinde ya da Steuerberater bürosunda tutulur. Çoğu firma karma model kullanır: günlük muhasebe şirket içinde, bilanço ve beyannameler büroda.
- Kayıt sistemi çoğunlukla **DATEV** veya ERP'nin muhasebe modülüdür. Tüm raporlar kayıt satırlarından türetilir.
- Zincir: **belge → kayıt → mutabakat → aylık değerlendirme (BWA) → beyan ve bilanço**.

### 4.2 Hedef kullanıcı

- Ayrı bir CFO'su olmayan, yaklaşık **20–200 çalışanlı** Mittelstand firması.
- Roller: **Geschäftsführer** (genel müdür), **kaufmännischer Leiter** (ticari müdür), **Controlling** (çoğu zaman tek kişi).
- Kaynak belgeye göre Controlling'in görevleri: bütçe ve plan-gerçekleşen analizi, maliyet merkezleri, yönetim raporları, likidite planı.

### 4.3 Aylık kapanış akışı (kaynak belge, Bölüm 1.3-D)

1. Tahakkuk ve dönemsellik kayıtları (Abgrenzungen), amortisman, stok değişimi.
2. Hesap mutabakatları (banka, kasa, ara hesaplar).
3. Raporlar: **BWA**, mizan (SuSa), açık kalem listesi (OPOS).
4. KDV ön beyanı; ardından yönetimle **BWA görüşmesi**, çoğu zaman Excel'de ek analiz.

→ **Proje, 4. adımdaki "yorum ve ek analiz" kısmını hedefler.**

Not: 1. adım eksik veya geç yapılırsa BWA çarpık görünür. Bu, projenin ana konularından biridir (bkz. 5.4).

### 4.4 Kaynak belgeden ilgili veri noktaları

- **Bitkom (Eylül 2026):** Alman firmalarının %57'si AI kullanıyor; AI kullananların %66'sı veri korumasını en büyük engel sayıyor. → Lokal çalışabilen küçük bir model anlamlı bir tasarım argümanı.
- **Kaynak belgedeki acılı nokta #4:** BWA ve mizan yorumu, Excel analizleri ve banka görüşmesi dosyaları. Raporlar statik; pivot ve yorum elle yapılıyor; BI araçları uzmanlık istiyor.
- Kaynak belgedeki personel açığı istatistikleri vergi bürolarına ait. İşletme tarafı için sayısal veri yok, bu yüzden yalnızca genel ifade olarak kullanılmalı.

---

## 5. Problem tanımı [KARAR]

### 5.1 Özet

BWA her ay geliyor, ama işletmenin onu doğru okuyup karara çevirmesi için gereken **yorum katmanı** ya eksik, ya pahalı, ya da tek bir kişiye bağlı.

### 5.2 Alt problemler

| Kod | Alt problem | Açıklama |
|---|---|---|
| P1 | Bağlamsız rakamlar | BWA bir sayı tablosu. "Personel gideri %18 arttı" okunabiliyor, ama nedeni (işe alım, prim, yanlış ay) raporda yok. |
| P2 | Çarpıklıklar | Eksik tahakkuk, girilmemiş stok değişimi, yıl sonunda kaydedilen amortisman gibi nedenlerle BWA gerçek durumu yanlış gösterebilir. Muhasebe bilgisi olmayan yönetici bunu gerçek gelişme sanar (bkz. 5.4). |
| P3 | Kişiye bağlı manuel yorum | Rapor Excel'e aktarılır, karşılaştırılır, yorum elle yazılır. Bilgi bir kişide kalır. |
| P4 | Banka iletişimi | Kredi kullanan firmalar BWA'yı düzenli olarak bankaya gönderir. Açıklamasız gönderilen olumsuz bir ay gereksiz sorulara yol açar. |
| P5 | Danışmanlık maliyeti | Büroların sunduğu BWA görüşmesi ücretli ve zaman alıyor. Küçük firmalar çoğu zaman atlıyor; rapor okunmadan dosyalanıyor. |

### 5.3 BWA hakkında bilinmesi gerekenler

Proje, **DATEV Standard-BWA (Form 01, "Kurzfristige Erfolgsrechnung")** yapısına yakın bir satır listesi kullanır.
**[KARAR]** Satır listesi gerçek bir DATEV-BWA örneğiyle doğrulandı ve kesinleştirildi (30 satır; nötr kalemler alt satırlara ayrıldı; `Verrechnete kalk. Kosten` ve `Kontenklasse unbesetzt` çıkarıldı). Ayrıntılar, makine anahtarları ve hesaplama kuralları: [`docs/02_bwa_satir_yapisi.md`](docs/02_bwa_satir_yapisi.md).

| Satır (Almanca) | Türkçe karşılık | Tür |
|---|---|---|
| Umsatzerlöse | Satış gelirleri | Gelir |
| Bestandsveränderungen (FE/UE) | Mamul/yarı mamul stok değişimi | Gelir düzeltmesi |
| Aktivierte Eigenleistungen | Aktifleştirilen kendi üretimi | Gelir düzeltmesi |
| **Gesamtleistung** | Toplam faaliyet hasılatı | Ara toplam |
| Material-/Wareneinkauf | Malzeme / ticari mal alımı | Gider |
| **Rohertrag** | Brüt kâr | Ara toplam |
| Sonstige betriebliche Erlöse | Diğer faaliyet gelirleri | Gelir |
| **Betrieblicher Rohertrag** | Faaliyet brüt kârı | Ara toplam |
| Personalkosten | Personel giderleri | Gider |
| Raumkosten | Kira ve bina giderleri | Gider |
| Betriebliche Steuern | Faaliyet vergileri | Gider |
| Versicherungen/Beiträge | Sigortalar / aidatlar | Gider |
| Besondere Kosten | Özel giderler | Gider |
| Fahrzeugkosten (ohne Steuer) | Araç giderleri (vergi hariç) | Gider |
| Werbe-/Reisekosten | Reklam / seyahat giderleri | Gider |
| Kosten der Warenabgabe | Mal teslim giderleri | Gider |
| Abschreibungen | Amortisman | Gider |
| Reparatur/Instandhaltung | Onarım / bakım | Gider |
| Sonstige Kosten | Diğer giderler | Gider |
| **Gesamtkosten** | Toplam giderler | Ara toplam |
| **Betriebsergebnis** | Faaliyet sonucu | Sonuç |
| Zinsaufwand | Faiz gideri | Faaliyet dışı |
| Sonstiger neutraler Aufwand | Diğer faaliyet dışı gider | Faaliyet dışı |
| **Neutraler Aufwand** | Faaliyet dışı gider toplamı | Ara toplam |
| Zinserträge | Faiz geliri | Faaliyet dışı |
| Sonstiger neutraler Ertrag | Diğer faaliyet dışı gelir | Faaliyet dışı |
| **Neutraler Ertrag** | Faaliyet dışı gelir toplamı | Ara toplam |
| **Ergebnis vor Steuern** | Vergi öncesi sonuç | Sonuç |
| Steuern vom Einkommen und Ertrag | Gelir üzerinden vergiler | Gider |
| **Vorläufiges Ergebnis** | Geçici sonuç | Sonuç |

**Sütunlar:** DATEV Form 01'de cari ay değeri, Gesamtleistung / Gesamtkosten / Personalkosten'a oranları (%) ve bunların kümülatif (Ocak–cari ay) karşılıkları bulunur. Önceki yıl karşılaştırması DATEV'de ayrı bir "Vorjahresvergleich" sayfasındadır. Projede ham veri yalnızca aylık değerlerden oluşur; bütün sütunlar ve karşılaştırmalar Katman 1'de hesaplanır (bkz. `docs/02_bwa_satir_yapisi.md`).

**Önemli:** BWA **geçicidir** (vorläufig). Yıl sonu kapanışında değerler değişebilir.

### 5.4 Bilinen çarpıklıklar (sistemin tanıması gerekenler)

| Kod | Çarpıklık | BWA'da nasıl görünür | Tespit ipucu (heuristic) |
|---|---|---|---|
| V1 | Eksik aylık tahakkuk (yıllık sigorta, yılbaşı/tatil ikramiyesi, yıllık lisans) | Bir ayda ani sıçrama, diğer aylarda düşük değer | Ödemenin geldiği ayda satır değeri aylık ortalamanın katları; önceki yıl aynı ayda da benzer sıçrama |
| V2 | Stok değişimi (Bestandsveränderung) girilmemiş | Rohertragsquote anormal düşer veya yükselir | **[KARAR] Arketipe göre:** Üreticide Bestandsveränderungen = 0 iken Materialeinkauf belirgin biçimde değişmiş. Ticarette (FE/UE satırı hep 0) açıklanamayan ani Rohertragsquote değişimi (bkz. `docs/03`, Bölüm 9.1) |
| V3 | Amortisman yalnızca yıl sonunda kaydediliyor | Ocak–Kasım sonuç olduğundan iyi, Aralık kötü | Abschreibungen satırı 11 ay boyunca 0 veya çok düşük |
| V4 | Geç kaydedilen belgeler (zamanlama kayması) | Bir ayda düşük, ertesi ayda yüksek gider | Ardışık iki ayda zıt yönlü, birbirini dengeleyen sapmalar |
| V5 | Tek seferlik etkiler (fuar, büyük onarım) | Tek satırda tek aylık sıçrama | Reparatur, Werbekosten vb. satırlarda izole sapma |
| V6 | Sezonsallık | Önceki aya göre büyük sapma | Önceki yılın aynı ayıyla karşılaştırınca normale döner |

---

## 6. Çözüm tasarımı

### 6.1 Ana ilkeler [KARAR]

1. **Hesaplamayı kod yapar, yorumu model yapar.** Model hiçbir rakamı kendisi hesaplamaz.
2. **Bilgi RAG'de, davranış fine-tuning'de.** Firmaya özgü ve değişebilen bilgi RAG ile gelir. Üslup, yapı ve akıl yürütme kalıbı fine-tuning ile öğretilir.
3. **Olgu, kaynaklı neden ve tahmin birbirinden ayrı tutulur.** Ürünün değeri bu ayrımda.
4. **Taslak üretir, insan onaylar.** Otomatik gönderim yok.

### 6.2 Mimari

```
BWA (CSV/Excel) + önceki dönemler + [opsiyonel: plan]
        │
        ▼
[1] Hesaplama katmanı (Python)  ──► facts.json
        │
        ▼
[2] RAG: sorgu facts.json'dan üretilir ──► bağlam parçaları (kaynak kimlikli)
        │
        ▼
[3] Fine-tuned küçük LLM (girdi: facts + bağlam) ──► Almanca yorum taslağı
        │
        ▼
[4] Doğrulama: rakam kontrolü + kaynak kontrolü ──► işaretli taslak
        │
        ▼
İnsan onayı
```

#### Katman 1: Hesaplama (deterministik, Python)

- **Girdi:** Cari ay BWA'sı, önceki aylar, önceki yıl; opsiyonel plan değerleri.
- **Hesaplar:**
  - Önceki aya göre fark (mutlak ve %)
  - Önceki yılın aynı ayına göre fark (mutlak ve %)
  - Kümülatif karşılaştırma
  - Opsiyonel plan-gerçekleşen farkı
  - Oranlar: `Rohertragsquote = Rohertrag / Gesamtleistung`, `Personalkostenquote = Personalkosten / Gesamtleistung`, `Materialquote = Materialeinkauf / Gesamtleistung`, `Betriebsergebnis-Marge = Betriebsergebnis / Gesamtleistung`
  - En büyük N sapma. **[KARAR, tur 4 — başlangıç değerleri]**
    - Kalem anlamlı: \|Δ\| ≥ %10 **ve** \|Δ\| ≥ aylık Gesamtleistung'un %0,5'i.
    - Oran anlamlı: ≥ 2 yüzde puanı.
    - Yorumda en fazla 5 kalem, büyüklüğe göre sıralı.
    - **[KARAR, tur 5]** Anlamlılık yalnızca **önceki yılın aynı ayına** göre; önceki ay ve kümülatif bilgi amaçlı, sıralamaya girmez.
  - Çarpıklık bayrakları (Bölüm 5.4'teki heuristikler)
- **Çıktı:** `facts.json`.
  - **[KARAR, tur 4] Gereksinimler:**
    - Her kalemde bütün karşılaştırmalar (önceki ay, önceki yılın aynı ayı, kümülatif) ve anlamlılık gerekçesi.
    - Rohertrag adayları `warn` değil nötr "aday"; doğru cevap yalnızca ground truth'ta.
    - Tutarlar tam sayı €, yüzdeler 1 ondalık, `schema_version` alanı.
  - **[KARAR, tur 5]** Şema 1.0 ve kodu: [`docs/05_facts_semasi.md`](docs/05_facts_semasi.md), `facts/` (`python -m facts`). Tam örnek: [`docs/examples/facts_A1-v00_2025-06.json`](docs/examples/facts_A1-v00_2025-06.json).
    - Her kalemde `normal_level` (önceki 12 ayın medyanı) ve tabanların `base_unusual` işareti var.
    - `delta_pct` sonuç satırlarında ve küçük ya da işaret değiştiren tabanlarda `null`.
    - Rohertrag adayı bütün arketiplerde nötr (`kandidat`); üreticilerde stok kuralı ayrıca kalır.
    - Bayrak kuralları ve parametreleri **[ÖNERİ]** (`facts/config.toml`); isabetleri `docs/05`, Bölüm 7'de.
  - İlk taslaktaki örnek JSON, şema 1.0 ile değiştirildi.

#### Katman 2: RAG bilgi tabanı

| Kod | Belge türü | Kapsam | Değişkenlik |
|---|---|---|---|
| K-A | BWA satır ve oran açıklamaları (SKR03 aralıkları yok, tur 10) | Genel | Düşük |
| K-B | Çarpıklık ve uyarı rehberi (Bölüm 5.4'ün genişletilmiş hali) | Genel | Düşük |
| K-C | Firma bağlam notları (aylık olaylar: işe alımlar, fuarlar, fiyat değişiklikleri, sezon bilgisi) | Firmaya özgü | Yüksek |
| K-D | Önceki ayların onaylanmış yorumları | Firmaya özgü | Yüksek |
| ~~K-E~~ | ~~Sektör karşılaştırma oranları~~ | — | **[KARAR, tur 10] Kapsam dışı** |

- **[KARAR, tur 10]** K-A yalnızca Almanca satır ve oran açıklamalarından oluşur; SKR03 hesap aralıkları hiçbir zaman eklenmez.
- **[KARAR, tur 10]** K-E kapsam dışı: güvenilir sektör oranları herkese açık değil.
- **Sorgu:** Anlamlı sapma gösteren satır adları + dönem + bayraklar facts.json'dan otomatik üretilir.
- K-C ve K-D için tarih/dönem metadata filtresi kullanılmalı.
- **[KARAR]** K-C notları `dauerhaft`/`temporär` alanı taşır. Bu alan meta veridir ve modele görünür.
- **[KARAR, tur 4]** K-C için RAG penceresi **13 ay** (t−12 … t), artı dönemsiz `Firmenprofil` notu. Önceki yılın aynı ayındaki geçici olayların notu da böylece pencereye girer (`docs/03`, 5.2).
- Her parça bir **kaynak kimliği** taşımalı (ör. `Kontextnotiz 2026-06`), çünkü model yorumda bu kimliğe atıf yapar.
- **[KARAR, tur 6]** (`docs/06`, Bölüm D):
  - Embedding modeli **BGE-M3**, vektör deposu **Chroma** (gömülü).
  - K-C: firma + 13 aylık pencere filtresi, ardından anlamsal top-k (başlangıç k = 8). "Penceredeki bütün notlar" ablation'da karşılaştırma olarak çalıştırılır.
  - Retrieval isabeti (recall@k) ölçülür (Bölüm 8).
  - K-D ilk sürümde kapalı; sonra ayrı deney.
- **v1 kodlandı** (`rag/`, [`docs/09_bilgi_tabani.md`](docs/09_bilgi_tabani.md)):
  - K-A/K-B anahtarla getirilir; K-C için tek sorgu + top-8 kullanılır (doğrulama varyantlarında seçildi).
  - Test kümesinde: recall %91 (o ayın notları) / %83 (geniş); çeldirici payı %11'den %5'e iniyor.
- **[ÖNERİ] İstemdeki rolü (istem 1.1, [`docs/10_istem.md`](docs/10_istem.md)):** K-A/K-B „WISSEN“ başlığı altında arka plan bilgisidir ve neden kaynağı sayılmaz; ondan türetilen neden `(Hypothese)` ister. `[Quelle: …]` yalnızca K-C notlarına yapılır.

#### Katman 3: Fine-tuning (LoRA)

**Öğretilecek davranışlar:**
- Sabit çıktı yapısı (Bölüm 6.3)
- Önceliklendirme: en önemli üç mesaj başta
- Yalnızca facts.json'daki rakamları kullanma, yeni rakam üretmeme
- Her nedeni ya kaynağıyla birlikte verme ya da açıkça tahmin olarak işaretleme ("vermutlich", "Hypothese")
  - **[KARAR, tur 6]** Notta karşılığı olmayan nedende hedef metin açık soru sorar ya da işaretli genel bir hipotez verir. Hipotez yalnızca modelin görebildiği bilgiden (facts, bayraklar, K-B) türetilir. Ground truth'taki gerçek neden hedef metne hiçbir zaman yazılmaz (`docs/06`, B3).
- Çarpıklık bayrağında olgu yerine uyarı dili kullanma
- Açık soruları listeleme
- Kısa, sade, yöneticiye uygun Almanca

**Öğretilmeyecekler:** Rakam hesaplama, firmaya özgü bilginin ezberlenmesi (bunlar RAG'in işi).

**Model girdisi — istem 1.1** (`prompting/`, [`docs/10_istem.md`](docs/10_istem.md)) [ÖNERİ]:
- Sistem mesajı: rol, 8 kural (deneme turu dersleri dahil), 6.3 şablonu. Bütün varyantlarda aynı.
- Kullanıcı mesajı: FACTS (model görünümü) + WISSEN (K-B, K-A) + KONTEXTNOTIZEN (Firmenprofil + top-8).
- Varyantlar: `ohne_kontext` (çıplak model, yalnızca FT), `rag_k8` (yalnızca RAG, RAG + FT), `rag_alle` (retrieval katkısı).
- İstem 1.0 deneme turu için dondurulmuş (`prompting/v1_0.py`).

#### Katman 4: Doğrulama

- Metindeki tüm rakamları Almanca biçimde ayıkla (`1.234,5`, `42 T€`, `18 %`) ve facts.json ile tolerans dahilinde karşılaştır. Tabloda olmayan rakamı işaretle.
- **[KARAR]** İstisna: RAG'in getirdiği bir bağlam notunda geçen rakam, aynı cümle o notun kaynak kimliğine atıf yapıyorsa kabul edilir (ör. "drei Neueinstellungen [Quelle: Kontextnotiz 2026-06]"). Bkz. `docs/03`, Bölüm 5.4.
- Her neden cümlesinde bir kaynak atfı veya tahmin işareti olup olmadığını kontrol et.
- Sonuç: taslak + uyarı listesi. Uyarılar insana gösterilir.
- **[KARAR, tur 8]** Yuvarlama kuralı (a): metindeki rakam, değerin gösterilen hassasiyete doğru yuvarlanmış hâliyse eşleşir. Örnek: 41.712 € → „42 T€“ ✓, „41 T€“ ✗.
- **v1 kodlandı:** [`docs/07_dogrulama_katmani.md`](docs/07_dogrulama_katmani.md), `validation/` (`python -m validation`).
  - Rakamlar, kaynak/hipotez işaretleri, format ve kapsam denetlenir.
  - Örnek: [`docs/examples/kommentar_A1-v00_2025-06.md`](docs/examples/kommentar_A1-v00_2025-06.md).

### 6.3 Çıktı yapısı [KARAR, tur 6]

- Dört bölüm sabit; Kernaussagen en fazla 3 madde.
- Tablo sütunları sabit.
- Uzunluk ~250–350 kelime (tablo hariç).
- Her neden cümlesinde `[Quelle: …]` veya `(Hypothese)`.
- Boş bölüm kalır ve „Keine.“ yazılır.
- Ayrıntılar: `docs/06`, B4.

```
**Kernaussagen <Monat Jahr>**                       (en fazla 3 madde)
**Abweichungen im Detail**                          (Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese)
**Hinweise auf mögliche Verzerrungen**              (bayraklı satırlar)
**Offene Fragen an Buchhaltung / Steuerberater**
```

**Örnek çıktı:**

> **Kernaussagen Juni 2026**
> 1. Betriebsergebnis 42 T€ unter Vorjahresmonat, im Wesentlichen durch Personalkosten (+18 %).
> 2. Der Anstieg passt zu den drei Neueinstellungen im Juni [Quelle: Kontextnotiz 2026-06], ist also voraussichtlich dauerhaft.
> 3. Rohertragsquote fällt auf 31 % (Vj. 38 %). **Hinweis:** Keine Bestandsveränderung gebucht, Wert möglicherweise verzerrt.
>
> **Offene Fragen an die Buchhaltung:** Wurde die Inventurveränderung für Juni erfasst?

Bu örnekte rakamlar tablodan, neden firma notundan (kaynaklı) geliyor; olası çarpıklık ise olgu olarak değil uyarı olarak veriliyor. Örnek açıklayıcıdır; ideal yorumlar üretilirken Muster GmbH'nin gerçek verisiyle yeniden yazılacak.

### 6.4 Kapsam dışı [KARAR]

- Tahmin (forecast)
- Yatırım veya vergi tavsiyesi
- OCR ve PDF okuma (girdi yapılandırılmış CSV/Excel)
- DATEV veya ERP'ye gerçek entegrasyon
- Yorumun otomatik gönderilmesi (her zaman insan onayı)

---

## 7. Neden RAG + fine-tuning birlikte (portfolyonun ana argümanı)

| Varyant | Beklenen davranış | Beklenen zayıflık |
|---|---|---|
| Çıplak küçük model | Genel, yüzeysel yorum | Nedenleri uydurur, format tutarsız, rakam hataları |
| Yalnızca RAG | Doğru bağlama erişir | Dağınık, uzun, tutarsız format; olgu ile tahmini ayırmaz |
| Yalnızca fine-tuning | Tutarlı ve düzgün üslup | Firma bağlamını bilmez; nedenleri uydurur |
| **RAG + fine-tuning** | Doğru bağlam + tutarlı üslup + kaynak gösterimi | Hedeflenen varyant |

Bu dört varyantın aynı test setinde karşılaştırılması (ablation) projenin **kanıt kısmıdır**.

---

## 8. Değerlendirme [ÖNERİ]

| Metrik | Tanım | Ölçüm |
|---|---|---|
| Rakam sadakati | Metindeki rakamların facts.json ile örtüşme oranı | Otomatik |
| Kaynaklı neden oranı | Belirtilen nedenlerin bağlam notlarında karşılığı olma oranı | Otomatik / yarı otomatik |
| Uydurma neden oranı | Notlarda olmayan bir olayın olgu gibi sunulma oranı | Otomatik (ground truth ile) |
| Sapma yakalama | Ground truth'taki önemli sapmaların yorumda geçme oranı (recall) | Otomatik |
| Çarpıklık uyarısı isabeti | V1–V6 uyarılarında precision ve recall | Otomatik (ground truth ile) |
| **V2 adayı ayrımı [KARAR]** | Katman 1'in V2 adayı karşısında modelin doğru kararı verme oranı: notla açıkla (`cite`) / uyar (`warn`) / ikisi de kabul (`either`). Özellikle A2 (ticaret) için. | Otomatik (`ground_truth_months.jsonl` → `v2_candidate_decision`; bkz. `docs/03`, 9.1) |
| Format uyumu | Çıktının 6.3'teki yapıya uyması | Otomatik |
| Üslup ve okunabilirlik | Yöneticiye uygunluk, kısalık | **[AÇIK]** İnsan değerlendirmesi veya LLM-as-judge |
| **Retrieval isabeti [KARAR, tur 6]** | İlgili bağlam notunun getirilen ilk k parçada olma oranı (recall@k) | Otomatik (ground truth: hangi not hangi olayı açıklıyor) |

---

## 9. Sentetik veri

Kararların tamamı ve gerekçeleri: [`docs/00_karar_kaydi.md`](docs/00_karar_kaydi.md). Bu belgelerdeki sayısal parametreler **[ÖNERİ]** etiketini taşır ve veri üreteci yazılırken kalibre edilecek.

- **[KARAR] Firmalar:** Üç arketip var:
  - **A1 Muster GmbH:** Metallverarbeitung / Zulieferer, ~55 çalışan, ~8,4 Mio €. Vitrin firması.
  - **A2:** Sanitär-/Heizungsgroßhandel.
  - **A3:** Gartenmöbel-Hersteller (güçlü sezon).

  Üreteç her arketipten çok sayıda varyant üretir. Her arketipin baskın bir muhasebe pratiği profili var (karma / tipik KOBİ / disiplinli). Bkz. [`docs/01_firma_profili.md`](docs/01_firma_profili.md).
- **[KARAR] Seri:** 36 ay (01/2024–12/2026). 2024 yalnızca karşılaştırma tabanıdır; varyant başına 24 ay yorumlanabilir. Plan verisi ilk sürümde yok.
- **[KARAR] Olay kataloğu (ground truth):** 19 olay türü (E01–E19): gerçek gelişmeler (R) ve V1–V6 çarpıklıkları. Her olayın ayı, satırı, büyüklüğü, kalıcılığı ve beklenen bayrağı kaydedilir. Bkz. [`docs/03_olay_katalogu.md`](docs/03_olay_katalogu.md).
- **[KARAR] Kasıtlı boşluk:**
  - Gerçek olayların ~%70'i bağlam notlarına (K-C) yazılır, ~%30'u yazılmaz.
  - Muhasebe kaynaklı çarpıklıklar (V1–V4) hiç notlanmaz.
  - Ayların ~%10–15'ine etkisiz "çeldirici" notlar eklenir.
  - Böylece modelin nedeni kaynaktan mı aldığı, yoksa tahmin mi ettiği ölçülebilir.
- **[KARAR] Ground truth dosyaları:** Olay başına bir kayıt (`events.jsonl`) ve firma-ay başına bir kayıt (`ground_truth_months.jsonl`). Şema `docs/03`, Bölüm 7'de.
- **[KARAR] Üreteç kuralları (tur 2):**
  - Arketip listesi ve arketip başına varyant sayısı **parametredir**.
  - Her olay eksiksiz kaydedilir: ay, satır, büyüklük, kalıcı/geçici, nota yazılıp yazılmadığı.
  - Notlar rakam içerebilir ve `dauerhaft`/`temporär` alanı taşır.
- **[KARAR] V2 tespiti arketipe göre ayrılır** (bkz. 5.4 ve `docs/03`, Bölüm 9.1). Katman 1 yalnızca sayısal adayı işaretler; notla açıklanıp açıklanmadığına model karar verir. Bu ayrım değerlendirmede ayrıca ölçülür (Bölüm 8).
- **[KARAR] Veri üreteci (tur 3)** — bkz. [`docs/04_veri_ureteci.md`](docs/04_veri_ureteci.md):
  - Referans koşu (seed 42, 3 arketip × 10 varyant) repoda; diğer koşular `.gitignore`'da.
  - Notlar şablonla üretilir: olay türü başına 5 kalıp, seçimi seed yapar. LLM ile çeşitlendirme ileride eklenebilecek bir seçenek ([ÖNERİ]).
  - **[KARAR, tur 9]** Alış (E04) ve satış (E05) fiyatı notlarının kalıpları netleştirildi; veri kümeleri yeniden üretildi, yalnızca not metinleri değişti (`docs/00`, Bölüm 15).
  - Modelin gördüğü dosyalar (`model_input/`) ve değerlendirme dosyaları (`evaluation/`) ayrı klasörlerde.
- **[KARAR, tur 4]** (`docs/00`, Bölüm 8):
  - **Dengelenmiş V2 kümesi.** Ana veri gerçekçi kalır. "V2 adayı ayrımı" metriği için `cite`/`warn` dengeli ayrı bir küme üretildi: `data/synthetic/v2_balanced_seed4242/`, raporlarda "dengelenmiş set".
  - **Eğitim profili.** Eğitim verisindeki `cite` sayısı düşük olduğu için, yalnızca eğitim verisinde kullanılacak `train_price_boost` profili hazırlandı (`docs/04`, Bölüm 8).
  - **Muster GmbH** toparlanma hikâyesi olarak kalıyor.
  - **Olay yoğunluğu** ayda ~1,5 olarak kabul edildi.
- **[KARAR, tur 5]** E18 kalibrasyonu: Malzeme satırındaki geç fatura kayması %5–20'ye indirildi; iki veri kümesi yeniden üretildi (`docs/00`, Bölüm 9).
- **[KARAR, tur 7] İdeal yorumlar (eğitim hedefleri)** (`docs/06`, B1–B2):
  - Karma yöntem: kural tabanlı içerik planı (ne söylenecek) + öğretmen modelin Almancası (nasıl söylenecek) + otomatik kontrol.
  - Ek olarak 20–30 örneklik, elle kontrol edilmiş altın küme.
  - Öğretmen: açık ağırlıklı bir model, API üzerinden. **[KARAR, tur 11]** Mistral Large 3, Mistral API. API anahtarı **yalnızca kullanıcının bilgisayarında** durur; öğretmen betiği orada çalışır.
  - **Hat kodlandı** (`ideal/`, [`docs/11_ideal_yorumlar.md`](docs/11_ideal_yorumlar.md)): içerik planı (yalnızca öğrencinin gördüğü notlar kaynak), öğretmen istemi, kontrol + yeniden deneme, istek dosyaları (pilot 24, eğitim 960, doğrulama 144 ay). Üç pilot tamamlandı (kabul %38 → %88 → %92; öğretmen istemi 1.3). Sıradaki: doğrulama kümesi, sonra eğitim kümesi ([`ideal/README.md`](ideal/README.md)).
- **[KARAR, tur 7] Eğitim/test ayrımı** (`docs/04`, Bölüm 9; `docs/06`, C):
  - Testte hem öğretilmemiş hem öğretilmiş türden örnekler var:
    - **Yeni sektör:** test arketipi **A1** (Muster GmbH), eğitimde hiç görülmez.
    - **Yeni firma:** A2 ve A3'ün görülmemiş varyantları (`reference_seed42`).
  - Eğitim: A2 + A3 × 20 varyant (`train_price_boost`, seed 7, v100–v119) → 960 ay.
  - Doğrulama: v120–v122 → 144 ay. Deneme turu örnekleri de buradan seçilir.

---

## 10. Teknik tercihler

Seçenekler ve öneriler (Ekim 2026 itibarıyla güncel modellerle): [`docs/06_model_tarafi_secenekler.md`](docs/06_model_tarafi_secenekler.md). Turlar 6–7'de karara bağlandı.

| Konu | Not |
|---|---|
| Temel model | Küçük, açık ağırlıklı, Almanca'sı iyi bir model (ör. 3–8B sınıfı). **[KARAR, tur 6]** Almanca deneme turu: Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B. Eşitlikte Ministral 3 8B [ÖNERİ]. Deneme turu tamamlandı (17.10.2026): [`trial/results.md`](trial/results.md), [`docs/08_deneme_turu.md`](docs/08_deneme_turu.md). **[KARAR, tur 9]** Temel model **Gemma 4 E4B**, yedek **Qwen3.5 9B**. Ministral elendi (uydurma rakamlar, biçim 0/10). |
| Lisans notları (kaynak belgeden) | Mistral: Apache 2.0, AB menşeli. gpt-oss: Apache 2.0 (20b yaklaşık 16 GB'a sığıyor). Llama: 3.2'den beri çok modlu modeller AB merkezli firmalara lisanslanmıyor; metin modelleri kullanılabilir. Proje yalnızca metin kullandığı için bu kısıt doğrudan etkilemez. Qwen: Apache 2.0, ama Çin menşeli; Alman firmalarında kullanımı yaklaşık %1, algı sorunu olabilir. |
| Fine-tuning araç seti | [ÖNERİ] Unsloth + TRL (QLoRA) |
| Vektör veritabanı ve embedding modeli | **[KARAR, tur 6]** BGE-M3 + Chroma |
| Donanım | **[KARAR, tur 7]** Fine-tuning ve değerlendirme **Kaggle**'da (ücretsiz T4). Geliştirme, deneme turu ve demo kullanıcının dizüstünde (GTX 1650, 4 GB). Kiralık GPU şimdilik yok. "Lokal çalışabilirlik", son modelin bu dizüstünde çalışmasıyla gösterilir (`docs/06`, A2). |

---

## 11. Riskler ve karşılıkları

| Risk | Karşılık |
|---|---|
| Küçük model sayı hesaplamada hata yapar | Hesaplama tamamen Katman 1'de (kod); model yalnızca verilen rakamları kullanır; Katman 4 kontrol eder |
| Model neden uydurur | Kaynak atfı zorunlu; kaynak yoksa tahmin işareti; "uydurma neden oranı" metriği |
| Çarpıklık gerçek gelişme gibi sunulur | Heuristik bayraklar + uyarı dili fine-tuning ile öğretilir |
| Sentetik veri gerçekçi olmaz | Satır yapısı DATEV Standard-BWA'ya yakın; olaylar sektörde bilinen çarpıklıklara dayanır (5.4) |
| Değerlendirme öznel kalır | Metriklerin çoğu ground truth ile otomatik ölçülür |

---

## 12. Sonraki adım

**[KARAR] Tamamlandı (14.10.2026):**

1. ✅ Kurgusal firmayı tanımla → [`docs/01_firma_profili.md`](docs/01_firma_profili.md)
2. ✅ BWA satır yapısını sabitle → [`docs/02_bwa_satir_yapisi.md`](docs/02_bwa_satir_yapisi.md)
3. ✅ Olay kataloğunu çıkar → [`docs/03_olay_katalogu.md`](docs/03_olay_katalogu.md)
4. ✅ Veri üreteci → [`docs/04_veri_ureteci.md`](docs/04_veri_ureteci.md), `generator/`, `tests/`, `data/synthetic/reference_seed42/` (tur 3)
5. ✅ Hesaplama modülü (Katman 1) → [`docs/05_facts_semasi.md`](docs/05_facts_semasi.md), `facts/`, `tests/test_facts.py` (tur 5)
6. ✅ Model tarafının yöntem kararları → [`docs/06_model_tarafi_secenekler.md`](docs/06_model_tarafi_secenekler.md) (turlar 6–7)
7. ✅ Doğrulama katmanı v1 (Katman 4) → [`docs/07_dogrulama_katmani.md`](docs/07_dogrulama_katmani.md), `validation/`, `tests/test_validation.py` (tur 8)
8. ✅ Almanca deneme turu ve temel model → [`docs/08_deneme_turu.md`](docs/08_deneme_turu.md), `trial/` (tur 9)
9. ✅ Bilgi tabanı v1 (Katman 2) → [`docs/09_bilgi_tabani.md`](docs/09_bilgi_tabani.md), `rag/`, `tests/test_rag.py` (tur 10)
10. ✅ İstem 1.1 → [`docs/10_istem.md`](docs/10_istem.md), `prompting/`, `tests/test_prompting.py`
11. 🔄 İdeal yorum hattı → [`docs/11_ideal_yorumlar.md`](docs/11_ideal_yorumlar.md), `ideal/`, `tests/test_ideal.py` (tur 11; pilotlar tamam, büyük koşu bekleniyor)

Karar özeti: [`docs/00_karar_kaydi.md`](docs/00_karar_kaydi.md). Karar turu 2 (V2 kuralı, notlardaki rakamlar, süre alanı, RAG penceresi) dosyanın 4. bölümünde; karar turu 3 (V2 ayrımının ölçülmesi, referans koşu, not şablonları) ve kalibrasyon değişiklikleri 7. bölümünde.

**Yol haritası ve proje durumu:** [`docs/yol_haritasi.md`](docs/yol_haritasi.md). Her adımdan sonra güncellenir.

**[ÖNERİ]** Sıradaki adımlar: ideal yorumlar (pilot → altın küme → büyük koşu) → Kaggle'da baseline'lar ve fine-tuning → değerlendirme ve ablation. Açık kararlar: [`docs/yol_haritasi.md`](docs/yol_haritasi.md), Bölüm 3.

**[ÖNERİ]** Bundan sonraki olası sıra: (veri üreteci ✅) → (hesaplama modülü ✅) → bilgi tabanı → baseline (çıplak model ve yalnızca RAG) → fine-tuning → değerlendirme ve ablation → portfolyo dokümantasyonu. G7 gereği emeğin ağırlığı model tarafında (bilgi tabanı, fine-tuning, ablation) olmalı; veri üreteci ve hesaplama modülü bu adımları besleyecek kadar basit tutulmalı.

---

## 13. Sözlük

| Terim | Açıklama |
|---|---|
| BWA (Betriebswirtschaftliche Auswertung) | Aylık kısa dönem kâr-zarar raporu; genelde DATEV'den veya Steuerberater'dan gelir |
| SuSa (Summen- und Saldenliste) | Mizan |
| OPOS (Offene-Posten-Liste) | Açık kalem listesi |
| SKR03 / SKR04 | DATEV standart hesap planları |
| Gesamtleistung | Toplam faaliyet hasılatı (satış + stok değişimi + aktifleştirilen üretim) |
| Rohertrag | Brüt kâr (Gesamtleistung − malzeme/mal alımı) |
| Betriebsergebnis | Faaliyet sonucu |
| Abgrenzung | Dönemsellik / tahakkuk kaydı |
| Bestandsveränderung | Stok değişimi |
| Abschreibung | Amortisman |
| Vorjahresmonat / Vormonat | Önceki yılın aynı ayı / önceki ay |
| Plan-Ist | Plan-gerçekleşen karşılaştırması |
| Kontierung | Belgeye hesap atama |
| Steuerberater / Steuerkanzlei | Vergi danışmanı / vergi danışmanlığı bürosu |
| Mittelstand | Alman orta ölçekli işletmeleri |
| Geschäftsführer | Genel müdür |
| kaufmännischer Leiter | Ticari / mali işler müdürü |
| DATEV | Vergi danışmanlarının kooperatifi; Almanya'da baskın muhasebe ve büro yazılımı |
| GoBD | Dijital defter ve belge tutma ilkeleri (izlenebilirlik, değiştirilemezlik) |
| vorläufig | Geçici (BWA değerleri yıl sonunda değişebilir) |
