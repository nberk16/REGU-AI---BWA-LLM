# 11 — İdeal yorumlar (eğitim hedefleri)

> **Durum:** Hat kodlandı (`ideal/`, 8 test). Pilot 1 (öğretmen 1.0): kabul %38. Pilot 2 (1.1): kabul %88, ama okumada içerik sorunları çıktı (Bölüm 11). Öğretmen 1.2, plan 1.2 ve sıkılaştırılmış kontrolle pilot 3 bekleniyor, 19.10.2026.
> - **[KARAR]:**
>   - Karma yöntem ve 20–30 örneklik altın küme (tur 7, B1).
>   - Notsuz nedende açık soru veya görülebilir bilgiden işaretli hipotez; ground truth nedeni asla (tur 6, B3).
>   - Öğretmen Mistral Large 3, Mistral API; anahtar yalnızca kullanıcının bilgisayarında (tur 11).
> - **[ÖNERİ]:** plan kuralları ve eşikleri, öğretmen istemi, üretim ayarları, kontrol ve yeniden deneme (bu belge).
>
> **İlgili:** `06_model_tarafi_secenekler.md` (B1–B4) · `10_istem.md` (öğrenci istemi) · `07_dogrulama_katmani.md` · Kullanıcı adımları: [`ideal/README.md`](../ideal/README.md) · Karar kaydı: `00`, Bölüm 18

---

## 1. Akış

```
facts.json + Katman 2 bağlamı (top-8) + ground truth
        │  1. İçerik planı (kod, ideal/plan.py) ── ne söylenecek
        ▼
istek dosyası (ideal/requests/*.jsonl.gz, repoda)
        │  2. Öğretmen (Mistral Large 3, kullanıcının dizüstü) ── nasıl söylenecek
        ▼
metin ──► 3. Kontrol (doğrulama katmanı + plan) ── geçemezse sorunlarla birlikte yeniden istenir (en fazla 3 deneme)
        ▼
ideal/outputs/*.jsonl ──► altın küme (elle) ──► eğitim verisi: öğrenci istemi 1.1 (rag_k8) + metin
```

**Sıra:**
1. **Pilot:** 24 ay; çıktılar okunur. Bunlar altın küme adaylarıdır.
2. **Düzeltme:** Gerekirse istem ve plan düzeltilir. Altın kümeden 1–2 örnek öğretmen istemine örnek olarak eklenebilir.
3. **Büyük koşu:** 960 eğitim + 144 doğrulama ayı.

## 2. İçerik planı (`ideal/plan.py`)

Plan, öğrenci modelin **gördüğü** bağlamla kurulur: Katman 2'nin o ay için getirdiği notlar (top-8 + Firmenprofil). Ground truth yalnızca görünen bir notun gerçekten neden olup olmadığına karar verir.

### 2.1 Tablo: anlamlı kalemler

Kalemin önceki yılın aynı ayına göre sapması için nedenler `evaluation/effects.csv`'den bulunur:
- **Olay başına yıllık fark:** etki(t) − etki(t−12).
- **Neden sayılma şartı [ÖNERİ]:** Fark sapmayla aynı yönde ve sapmanın en az %25'i kadar.
- **Önceki yıl olayları da dahil.** Örnek: geçen yılın fuarı bu yılki Werbekosten düşüşünü açıklar („Ereignis im Vorjahresmonat“).

Her satırda açıklama şu sırayla belirlenir:

| Durum | Açıklama | Son sütun |
|---|---|---|
| Nedenin notu **görünen** notlar arasında | Notun içeriği | `[Quelle: …]` |
| Satırda yıllık sapmayı açıklayabilen bir bayrak var (V5, V2 stok, V3, V4) | K-B'den türetilmiş vermutung | Hypothese |
| Önceki yılın değeri olağan dışı (`base_unusual`) | „ungewöhnlich hoher/niedriger Vergleichswert im Vorjahresmonat“ | Hypothese |
| Hiçbiri | „Ursache offen“ + soru | – |

- **Hariç tutulan bayraklar:** V6 (sezon) yalnızca önceki aya göre farkı, V1 ise iki yılda da görülen bir sıçramayı açıklar. İkisi de yıllık sapmanın nedeni sayılmaz.
- **Gerçek neden görünmüyorsa:** Not hiç yazılmamışsa ya da getirilmemişse neden **hiç söylenmez** (B3).

### 2.2 Rohertragsquote adayı (V2, `kandidat`)

- **Karşılaştırma önceki ayla:** Sıçrama önceki aya göre tanımlı; ground truth'taki nedenler de o ayki sıçramayı açıklar (`docs/03`, 9.1). Bu yüzden tabloda ayrı bir satır olarak önceki ayla karşılaştırılır („Vm.“).
- **Kaynak gösterme şartları:** Ground truth kararı `cite`/`either` olmalı, notlu gerçek neden görünmeli ve **yönü tutmalı**:
  - Satış fiyatı artışı (E05): oran yükselir.
  - Alış fiyatı zammı (E04): oran düşer; befristeten zammın bitişinde yükselir.
- **Aksi hâlde uyarı:** Hinweise'de uyarı ve soru verilir.
- **Etkisi:** Yön şartı, ground truth'un `cite` dediği 47 eğitim ayından 10'unu uyarıya çevirdi. O aylarda görünen not sıçramanın yönünü açıklamıyor.

### 2.3 Hinweise, Kernaussagen, sorular

- **Hinweise:** Her `hinweis` bayrağı için bir madde:
  - `erklaert`: Görünen not açıklıyor (V5 + onarım/fuar notu, V6 + Firmenprofil).
  - `saison`: Firmenprofil yok; sezon hipotezi verilir, soru yok.
  - `warnung`: Bayrağın kanıtı + K-B hipotezi + sonucu + soru.
- **Kernaussagen (en fazla 3):**
  1. Betriebsergebnis (önceki yıl; anlamlıysa marj ve kümülatif).
  2. En büyük sapma ve nedeni.
  3. Rohertrag adayı > en önemli uyarı > ikinci sapma.
- **Sorular:** En fazla 5. Önce uyarılar, sonra nedeni açık kalemler.
- **Rakamlar:** Plandaki bütün rakamlar `facts.json`'dan, doğrulama katmanının yuvarlama kuralıyla (a) biçimlendirilir. Tutarlar ayrıca T€ olarak verilir.

### 2.4 Dağılım (eğitim kümesi, 960 ay)

| | Kaynaklı | Hipotez | Ursache offen |
|---|---:|---:|---:|
| Tablo satırları (3.067) | 1.184 (%39) | 1.573 (%51) | 310 (%10) |

- **Hinweise:** 1.432 uyarı, 366 notla açıklanan, 129 sezon.
- **Sorular:** Ayda ortalama 1,8.
- **Hipotez payının yüksek olmasının nedeni:** Eğitim verisinde ayların ~%65'inde Rohertrag adayı var (`train_price_boost` profili; `docs/04`, Bölüm 8) ve çoğu uyarı gerektiriyor.

## 3. Öğretmen istemi (`ideal/teacher.py`)

- **Sistem mesajı:** 12 kural (sürüm 1.2; 1.0'da 10). Planı eksiksiz al ve hiçbir şey ekleme. Yalnızca plandaki rakamlar (T€ biçimi serbest). Kaynak ve hipotez işareti aynı cümlede. Kausal kelimeler yalnızca kaynaklı ya da hipotezli cümlede. 250–350 kelime, 6.3 biçimi, akıcı ve çeşitli Almanca.
- **Kullanıcı mesajı:** Planın okunur hâli: Kernaussagen, tablo satırları (rakamlar hazır), Hinweise, sorular ve **yalnızca kaynak gösterilecek notların** metni.
- Öğretmen `facts.json`'u ve çeldirici notları görmez; uyduracağı malzeme yoktur.
- **Üretim ayarları [ÖNERİ]:**
  - Model `mistral-large-2512`.
  - `temperature 0.4`; çeşitli dil için sıfırdan biraz yüksek.
  - `random_seed` ay kimliğinden türetilir; tekrarlanabilirlik için.
  - `max_tokens 2000`.
- **Boyut:** Öğretmen istemi ortalama ~5.000 karakter (~1.700 token). 1.104 ay × (~2.000 girdi + ~700 çıktı token) ≈ 2,2 M + 0,8 M token. Yeniden denemelerle biraz daha fazla.

## 4. Kontrol ve yeniden deneme (`ideal/check.py`)

Bir metin şu şartların hepsini sağlarsa kabul edilir:
1. **Doğrulama katmanında `fehler` yok.** Rakamlar, kaynaklar, işaretsiz neden ve biçim denetlenir; öğrencinin göreceği notlarla (`docs/07`).
2. **Tablo:** Tablo satırları plandakiyle aynı ve aynı sırada. Ist, Vergleich ve Abweichung hücreleri plandakiyle birebir aynı (1.1). Son sütun plana uygun (kaynak / Hypothese / –).
3. **Kaynaklar:** Plandaki her kaynak var, plan dışında kaynak yok.
4. **Hinweise ve sorular:** Her Hinweis maddesi var. Soru sayısı plandakiyle aynı (1.1; 1.0'da „en az“).
5. **Uzunluk:** 180–400 kelime (hedef ~250–350; 1.2'den beri alt sınır 180, Bölüm 11).
6. **İçerik (1.2):**
   - Tablodaki açıklama hücresi boş olamaz; plan etiketi ya da yalnızca yön („gestiegen“) olamaz.
   - Kaynak gösteren her cümle ve satır, notun içeriğinden en az bir kelime içermeli. Satır adları, aylar ve genel kelimeler sayılmaz; birleşik kelimeler de eşleşir. Yalnızca atıf yetmez.
   - Değerlendirme, çıkarım ve öneri kalıpları yasak („Handlungsbedarf“, „unterstreicht“, „kompensieren“, „folgt auf“ …).

Geçemeyen metin için bulunan sorunlar Almanca olarak modele geri verilir ve metin yeniden istenir. 1.1'den beri her sorunun yanında ilgili cümle de verilir. En fazla 4 deneme yapılır (1.0'da 3); sonra ay `failed` olarak kaydedilir. `--retry-failed` bu ayları sonra yeniden dener. Çıktı dosyasındaki eski sürüm kayıtları (plan/öğretmen sürümü farklı) atlanmaz, yeniden üretilir.

**Tutarlılık sınaması:** Her plan, sabit cümlelerle kurulan bir kalıp metne de dökülür (`tests/ideal_template.py`). 1.104 ayın hepsinde bu metin, uzunluk dışında bütün kontrolleri geçiyor. Yani plan, rakam biçimleri ve kaynaklar doğrulama katmanıyla tutarlı.

## 5. Kümeler ve dosyalar

| Küme | Kaynak | Ay | Dosya |
|---|---|---:|---|
| `train` | A2/A3 v100–v119 (`train_seed7`) | 960 | `ideal/requests/train.jsonl.gz` (1,4 MB) |
| `val` | A2/A3 v120–v122 | 144 | `ideal/requests/val.jsonl.gz` |
| `pilot` | `val` içinden 24 çeşitli ay (V1–V6, V2 cite/warn, çeldirici, nedeni açık kalem, sakin ay) | 24 | `ideal/requests/pilot.jsonl.gz` |

- **İstek kaydı:** `id`, küme, sürümler (plan, öğretmen, öğrenci istemi, getirme), `random_seed`, öğretmen mesajları, plan, `facts.json`, öğrencinin gördüğü notlar.
- **Çıktılar:** `ideal/outputs/<küme>.jsonl`. Kullanıcı yükler; her ay için son kayıt geçerlidir.
- **Test kümesi** (A1 + `reference_seed42`) için ideal yorum üretilmez. Test, ground truth ile ölçülür.

## 6. Dizüstü betiği (`ideal/run_teacher.py`)

- **Anahtar [KARAR, tur 11]:** Yalnızca kullanıcının bilgisayarında, PowerShell oturumundaki `MISTRAL_API_KEY` değişkeninde durur. Betik anahtarı dosyaya yazmaz ve ekrana basmaz (testle denetlenir).
- **Bağımlılık:** Standart kütüphane + repodaki `validation` ve `ideal` paketleri; Python ≥ 3.11. Kontrol dizüstünde, üretimle aynı anda yapılır; çıktı tek seferde yüklenir.
- **`--check`:** Anahtarı ve modelin kullanılabilirliğini dener. Model yoksa mevcut „large“ modelleri listeler.
- **Hata yönetimi:**
  - 429/5xx/ağ hatasında bekleyip yeniden dener.
  - 401 ve 400/404'te durur.
  - Kaldığı yerden devam eder.
  - `--workers 2` varsayılan; hız sınırında `--workers 1`.

## 7. Komutlar

```bash
python -m rag export --run data/synthetic/train_seed7          # bağlam (BGE-M3, ~30 dk işlemcide)
python -m ideal build --run data/synthetic/train_seed7         # planlar + istek dosyaları
python ideal/run_teacher.py --set pilot                        # kullanıcının dizüstü (ideal/README.md)
python -m ideal report --set pilot                             # özet: kabul oranı, denemeler, sorunlar, token
```

## 8. Testler (`tests/test_ideal.py`, 8 test)

- **Rakam biçimi:** Yuvarlama kuralı (a) ile uyumlu.
- **Referans ay (Muster GmbH, 06/2025):**
  - Kaynaklı nedenler, önceki yıl olayı (fuar), hipotezler, Hinweise ve sorular beklendiği gibi.
  - Plan, elle yazılmış örnek yorumdan bir kaynak fazla buldu: çelik zammı notu (`Kontextnotiz 2025-03`) malzeme artışını da açıklıyor.
- **Görünürlük:** Yalnızca görünen ve çeldirici olmayan notlar kaynak gösterilir. Öğretmen mesajlarında ground truth izi (olay kimliği, kod) yok.
- **Kalıp metin:** Kontrolü geçer. Kontrol, eksik kaynak, eksik Hinweis ve plan dışı kaynağı yakalar.
- **Repodaki istek dosyaları:** Kodla uyumlu: sürümler ve öğretmen mesajları.
- **Dizüstü betiği (sahte Mistral sunucusuyla):**
  - Düzeltme isteğiyle yeniden deneme ve kaldığı yerden devam.
  - Anahtar ve model kontrolleri.
  - Anahtar ekrana basılmıyor.

## 9. Açık noktalar

- **[AÇIK, paket 7]** „Yalnızca fine-tuning“ varyantı için bağlamsız girdilere ayrı hedefler gerekip gerekmediği (`00`, 17.3). Gerekirse aynı plan kodu, görünen not kümesi boş verilerek çalıştırılır; bu durumda bütün nedenler hipotez ya da açık soru olur.
- **Altın küme:** Pilot çıktılarından 20–30 ay seçilip elle düzeltilecek. Kullanım alanları: kalite ölçümü, üslup referansı, öğretmen istemine örnek.

## 10. Pilot 1 (öğretmen 1.0, 19.10.2026)

Kullanıcının dizüstünde 24 ay çalıştı. Çıktı: `ideal/outputs/pilot_v1_0.jsonl`; yanlışlıkla `main` dalına yüklendi, buraya kopyalandı.

| | Değer |
|---|---|
| Kabul | 9 / 24 (%38) |
| Kabul edilenlerde deneme | 1 deneme: 1 · 2 deneme: 4 · 3 deneme: 4 |
| Token | girdi 156 bin · çıktı 47 bin (ay başına ~6.500 + ~2.000, denemeler dahil) |
| Süre | ay başına medyan 27 s |

**Ret nedenleri ve 1.1'deki karşılıkları:**

| Neden | Sıklık | Düzeltme |
|---|---:|---|
| Olası nedenler `(Hypothese)` olmadan, çoğu Hinweise'de („könnte durch … verfälscht sein“, „Sollte … zurückzuführen sein“) | 13 | İstem: kural 4 her bölüm ve kalıp için açık. Geri bildirim: hangi cümle olduğu yazılıyor (1.0'da yalnızca bulgu türü vardı; model neyi düzelteceğini bilmiyordu). |
| Hinweise madde yerine paragraf, giriş cümlesi | 3 | İstem kural 8: yalnızca „- <Position>: …“ maddeleri. |
| Hinweise'de pozisyon adı plandakinden farklı ya da eksik | 5 | İstem kural 8 + geri bildirimde beklenen madde başı. |
| Kısa metin (177–199 kelime) | 5 | İstem kural 10: en az 250 kelime, Einordnung cümleleri; geri bildirimde ne ekleneceği. |
| „Ursache offen“ satırı yanlış biçimde | 1 | Geri bildirim. |
| Uydurulmuş yuvarlama („-360 T€“) | 1 | Doğrulama yakaladı; geri bildirim. |
| **Doğrulama katmanında boşluk:** „Ursache … nicht identifiziert“ cümleleri neden sayıldı | 2 | `unknown_cause_phrases`'e „nicht identifiziert“, „nicht geklärt“, „unbekannt“ eklendi (doğrulama v1.4). |

**Kabul edilenlerde bile görülen ve 1.1'de sıkılaştırılanlar:**
- Tabloda T€ ya da „Vj.“ öneki olmadan değerler. Artık hücreler plandakiyle birebir aynı olmalı; öğrencinin tablo değerlerini her zaman aynı biçimde kopyalaması için.
- Plan dışı ek soru. Artık soru sayısı plandakiyle aynı olmalı.
- Kernaussage 2 ve 3'ün aynı kalemi anlatması. Plan 1.1'de üçüncü madde ikincinin kalemini tekrarlamıyor.

**Not:** 1.0 metinlerinin hiçbiri 1.1 kontrollerini geçmiyor; en sık neden tablo hücreleri. Yeni istem bunu açıkça istediği ve geri bildirim beklenen değerleri verdiği için yeniden denemede düzelmesi bekleniyor. Pilot 2 bunu ölçecek.

## 11. Pilot 2 (öğretmen 1.1, 19.10.2026)

Çıktı: `ideal/outputs/pilot_v1_1.jsonl`.

| | Değer |
|---|---|
| Kabul | 21 / 24 (%88; pilot 1'de %38) |
| Kabul edilenlerde deneme | 1 deneme: 9 · 2 deneme: 9 · 3 deneme: 3 |
| Token | girdi 118 bin · çıktı 38 bin |
| Süre | ay başına medyan 19 s |

Cümle bazında geri bildirim ve netleştirilmiş kurallar biçim sorunlarını büyük ölçüde çözdü. Ama 21 kabul edilen metnin hepsi okunduğunda, otomatik kontrolün o sırada denetlemediği içerik sorunları görüldü:

| Sorun | Kabul edilen metin | Örnek | 1.2'deki karşılığı |
|---|---:|---|---|
| Kaynak gösterilmiş, ama nedenin kendisi yazılmamış | 10 | „Die Umsatzerlöse … übertrafen den Vorjahresmonat um 394 T€ (+26,7 %) [Quelle: Kontextnotiz 2026-01].“ | İstem kural 3; kontrol: cümlede notun içeriğinden bir kelime |
| Açıklama hücresi boş, plan etiketinin kopyası ya da yalnızca yön | 7 | „Ursache mit Quelle“, „gestiegen“, boş hücre | Plan metni talimat biçiminde (etiket kopyalanmıyor); istem kural 7; kontrol |
| Kendi değerlendirmesi ve çıkarımı | 1 (+ reddedilen 2) | „signalisiert Handlungsbedarf“, „kann … nicht kompensieren“, „der Einbruch folgt auf …“ | İstem kural 1 örneklerle; kontrol: yasak kalıplar |

**Yeni kontrollerle:** Kabul edilen 21 metnin 11'i geçmiyor. Kontrol, 1.104 ayın kalıp metinlerinde yanlış alarm vermiyor.

**Uzunluk ve uydurma arasındaki gerilim:**
- Az maddeli planlarda öğretmen, 250 kelimeye ulaşmak için kendi yorumunu ekledi. Reddedilen bir metinde bu, öneri ve sonuç cümlelerine dönüştü.
- Çözüm [ÖNERİ]:
  - Plana yalnızca `facts.json`'dan „Einordnung“ bilgisi eklendi: kalemin önceki ayı ve kümülatif değeri, Gesamtleistung. Öğretmen ek cümleleri yalnızca bundan kurar.
  - İstem, az maddede kısa metni açıkça doğru sayar.
  - Kabul alt sınırı 200'den 180 kelimeye indi.
- B4'teki „~250–350“ [KARAR] bir hedef olarak kalır. „Uydurma neden yok“ ilkesi (6.1) daha önceliklidir.

**Doğrulama v1.5:** Satır adları büyük-küçük harfe duyarsız eşleşir („den Sonstigen Kosten“). Sıfat çekimli kısa adlar eklendi („sonstigen neutralen Ertrag“). Pilot 2'deki bir ret bu boşluktan kaynaklanıyordu.
