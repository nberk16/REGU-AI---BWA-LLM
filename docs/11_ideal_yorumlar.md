# 11 — İdeal yorumlar (eğitim hedefleri)

> **Durum:** Hat kodlandı (`ideal/`, 8 test). Pilotlar: 1.0 %38 · 1.1 %88 · 1.2 %92. Öğretmen 1.3 ile yeniden deneme sonrası: eğitim 908/960 (%95), doğrulama 138/144 (%96) (Bölüm 13–14). Tur 12: bağlamsız hedefler („yalnızca FT“) ve iki düzeltme (Bölüm 15–16). `train_ohne` 923/960 (Bölüm 17). Plan 1.4 (yön tutarlılığı): 555 ay yeniden üretilecek, 21.10.2026.
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

- **Sistem mesajı:** 12 kural (sürüm 1.3; 1.0'da 10). Planı eksiksiz al ve hiçbir şey ekleme. Yalnızca plandaki rakamlar (T€ biçimi serbest). Kaynak ve hipotez işareti aynı cümlede. Kausal kelimeler yalnızca kaynaklı ya da hipotezli cümlede. 250–350 kelime, 6.3 biçimi, akıcı ve çeşitli Almanca.
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

Geçemeyen metin için bulunan sorunlar Almanca olarak modele geri verilir ve metin yeniden istenir. 1.1'den beri her sorunun yanında ilgili cümle de verilir. En fazla 4 deneme yapılır (1.0'da 3); sonra ay `failed` olarak kaydedilir. `--retry-failed` bu ayları sonra bir kez yeniden dener (`--max-rounds 2`). Girdisi değişmiş kayıtlar (parmak izi `input_sha` farklı) atlanmaz, yeniden üretilir (Bölüm 15, 17).

**Tutarlılık sınaması:** Her plan, sabit cümlelerle kurulan bir kalıp metne de dökülür (`tests/ideal_template.py`). 1.104 ayın hepsinde bu metin, uzunluk dışında bütün kontrolleri geçiyor. Yani plan, rakam biçimleri ve kaynaklar doğrulama katmanıyla tutarlı.

## 5. Kümeler ve dosyalar

| Küme | Kaynak | Ay | Dosya |
|---|---|---:|---|
| `train` | A2/A3 v100–v119 (`train_seed7`) | 960 | `ideal/requests/train.jsonl.gz` (1,4 MB) |
| `val` | A2/A3 v120–v122 | 144 | `ideal/requests/val.jsonl.gz` |
| `pilot` | `val` içinden 24 çeşitli ay (V1–V6, V2 cite/warn, çeldirici, nedeni açık kalem, sakin ay) | 24 | `ideal/requests/pilot.jsonl.gz` |
| `train_ohne` | `train` ile aynı aylar, bağlamsız („yalnızca FT“, Bölüm 15) | 960 | `ideal/requests/train_ohne.jsonl.gz` |
| `val_ohne` | `val` ile aynı aylar, bağlamsız | 144 | `ideal/requests/val_ohne.jsonl.gz` |

- **İstek kaydı:** `id`, küme, sürümler (plan, öğretmen, öğrenci istemi, getirme), `random_seed`, öğretmen mesajları, plan, `facts.json`, öğrencinin gördüğü notlar.
- **Çıktılar:** `ideal/outputs/<küme>.jsonl`. Kullanıcı yükler; her ay için son kayıt geçerlidir.
- **Girdi parmak izi (`input_sha`):** Her kayıt, öğretmene giden mesajların SHA-256 özetini (16 karakter) taşır. Sürümü ya da girdisi değişen ayın eski kaydı sayılmaz; betik o ayı yeniden üretir (Bölüm 15).
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
python -m ideal build --run data/synthetic/train_seed7 --variant ohne_kontext   # bağlamsız: {train,val}_ohne
python ideal/run_teacher.py --set pilot                        # kullanıcının dizüstü (ideal/README.md)
python -m ideal report --set pilot                             # özet: kabul oranı, denemeler, sorunlar, token, bekleyen aylar
```

## 8. Testler (`tests/test_ideal.py`, 11 test)

- **Rakam biçimi:** Yuvarlama kuralı (a) ile uyumlu.
- **Referans ay (Muster GmbH, 06/2025):**
  - Kaynaklı nedenler, önceki yıl olayı (fuar), hipotezler, Hinweise ve sorular beklendiği gibi.
  - Plan, elle yazılmış örnek yorumdan bir kaynak fazla buldu: çelik zammı notu (`Kontextnotiz 2025-03`) malzeme artışını da açıklıyor.
- **Görünürlük:** Yalnızca görünen ve çeldirici olmayan notlar kaynak gösterilir. Öğretmen mesajlarında ground truth izi (olay kimliği, kod) yok.
- **Kalıp metin:** Kontrolü geçer. Kontrol, eksik kaynak, eksik Hinweis ve plan dışı kaynağı yakalar.
- **Repodaki istek dosyaları:** Kodla uyumlu: sürümler ve öğretmen mesajları.
- **Dizüstü betiği (sahte Mistral sunucusuyla):**
  - Düzeltme isteğiyle yeniden deneme ve kaldığı yerden devam.
  - Girdisi değişen ay yeniden üretilir, değişmeyen ay atlanır (`input_sha`).
  - Anahtar ve model kontrolleri.
- **Bağlamsız planlar:** Aynı aylar; kaynak yok, V2 adayı hep uyarı, kalıp metin kontrolü geçiyor.
- **Belirlenimcilik:** Eşit etkili olaylar olay kimliğine göre sıralanır; plan Python'un hash tohumuna bağlı değil.
- **Yön tutarlılığı (plan 1.4):** Taban hipotezi yalnızca ters yönde olağandışı tabanda; geç fatura yalnızca artışta.
  - Anahtar ekrana basılmıyor.

## 9. Açık noktalar

- ~~„Yalnızca fine-tuning“ varyantı için ayrı hedefler~~ → **[KARAR, tur 12]** B: bağlamsız hedeflerle ayrı model (Bölüm 15).
- **Altın küme:** Doğrulama kümesinin kabul edilen metinlerinden (pilot ayları dahil) 20–30 ay seçilip elle düzeltilecek. Kullanım alanları: kalite ölçümü, üslup referansı, öğretmen istemine örnek.

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

## 12. Pilot 3 (öğretmen 1.2, 19.10.2026)

Çıktı: `ideal/outputs/pilot_v1_2.jsonl`.

| | Değer |
|---|---|
| Kabul | 22 / 24 (%92) |
| Kabul edilenlerde deneme | 1: 11 · 2: 9 · 3: 1 · 4: 1 |
| Token | girdi 118 bin · çıktı 34 bin |
| Süre | ay başına medyan 16 s |

**Okuma (24 metnin hepsi):**
- **İyileşenler:**
  - Nedenler notun içeriğiyle yazılıyor („Sonderauftrag eines Bauträgers“, „Reparatur des Trockenofens“).
  - Açıklama hücreleri anlamlı.
  - Önceki yıl olayları doğru kuruluyor („Großauftrag … im Vorjahresmonat“).
  - Eklenmiş değerlendirme neredeyse yok.
  - Einordnung cümleleri yalnızca plandaki rakamları kullanıyor.
- **Kalan sorunlar ve 1.3'teki karşılıkları:**

| Sorun | Sıklık | Karşılık |
|---|---:|---|
| Bir kalemi anlatan Kernaussage, nedeni söylemiyor (neden yalnızca tabloda) | 17 / 22 | Plan metni bunu madde başına açıkça istiyor; kontrol: kaynak / „(Hypothese)“ / „offen“ Kernaussage'de de olmalı (öğretmen 1.3) |
| İşaretsiz nedensellik: „steht im Zusammenhang mit …“ | 1 | Doğrulama v1.6: „Zusammenhang“, „verantwortlich“, „folgt auf“, „ergibt sich aus“ nedensellik kelimesi |
| Öneri cümlesi: „… würde diese Verzerrung vermeiden“ | 1 | Kontrol: „vermeid…“ yasak kalıplarda. „folgt auf“ yasak listesinden çıktı; kaynakla birlikte meşru (validasyonda nedensellik kelimesi) |
| Sezon hipotezi „Veränderung gegenüber dem Vorjahresmonat gering“ ama yıllık fark %13,6 | 1 | Plan 1.3: „deutlich kleiner als gegenüber dem Vormonat“ |

**Sonraki adım:** Öğretmen 1.3 ile doğrulama kümesi (144 ay; pilot ayları dahil). Kabul oranı ve içerik yeterliyse eğitim kümesi (960 ay). Ayrı bir pilot yerine doğrulama kümesinin kullanılması bir tur kazandırır; çıktısı zaten gerekli.

## 13. Doğrulama kümesi (öğretmen 1.3, 19.10.2026)

Çıktı: `ideal/outputs/val.jsonl`.

| | Değer |
|---|---|
| Kabul | 132 / 144 (%92) |
| Kabul edilenlerde deneme | 1: 53 · 2: 55 · 3: 17 · 4: 7 |
| Kelime (kabul edilenler) | en az 180 · medyan 240 · en fazla 393 |
| Token | girdi 858 bin · çıktı 244 bin (ay başına ~6.000 + ~1.700, denemeler dahil) |
| Süre | ay başına medyan 20 s |

**Ret nedenleri (12 ay):** Çoğunlukla işaretsiz bir neden cümlesi (7). Ayrıca Kernaussage biçimi, Kernaussage'de eksik neden ve kısa metin.

**Okuma:** Pilot dışından rastgele 8 kabul edilmiş metin okundu. Pilot 3 ile aynı düzeyde:
- Nedenler notun içeriğiyle yazılmış, Kernaussage'ler de nedeni söylüyor.
- Varsayımlar işaretli, açık nedenler „offen“.
- Küçük kusurlar:
  - Önceki yılın bir zammını „vorübergehend niedrigere Einkaufspreise“ diye ters yönden anlatma.
  - Değeri 0 olan Vorjahresmonat için „ungewöhnlich hoher Vergleichswert“ ifadesi (negatif satırda cebirsel olarak doğru, okurken garip).
- Kusurların hiçbiri eğitim hedefini bozacak türden değil.

**Yeniden deneme düzeltmesi:** `--retry-failed` önceden aynı tohumları kullanıyordu; aynı reddedilen metin büyük olasılıkla yeniden üretilirdi. Artık her yeni turda tohum, önceki tur başına 100 kaydırılıyor (test).

## 14. Eğitim kümesi ve yeniden deneme turu (öğretmen 1.3, 19.10.2026)

Çıktılar: `ideal/outputs/train.jsonl` (1.049 kayıt), `ideal/outputs/val.jsonl` (156 kayıt). Her ay için son kayıt geçerli. Bütün kayıtlar öğretmen 1.3 / plan 1.3 / istem 1.1 sürümünde. Kabul edilen 1.046 metin güncel kontrolden yeniden geçirildi; hepsi geçiyor.

| | Eğitim (`train`) | Doğrulama (`val`) |
|---|---|---|
| Kabul | **908 / 960 (%95)** | **138 / 144 (%96)** |
| İlk tur | 871 kabul | 132 kabul (Bölüm 13) |
| `--retry-failed` (yeni tohumlar) | 89 ay → 37 kabul | 12 ay → 6 kabul |
| Kabul edilenlerde deneme | 1: 327 · 2: 409 · 3: 114 · 4: 58 | 1: 53 · 2: 56 · 3: 21 · 4: 8 |
| Kelime (tablo hariç) | en az 180 · medyan 233 · en fazla 389 | en az 180 · medyan 239 · en fazla 393 |
| Token (bütün denemeler) | girdi 6,68 Mio · çıktı 1,82 Mio | girdi 0,99 Mio · çıktı 0,28 Mio |
| Süre | ay başına medyan 19 s | ay başına medyan 20 s |
| Kaynaklı neden içeren metin | 717 (%79) | 110 (%80) |
| `(Hypothese)` içeren metin | 852 (%94) | 133 (%96) |

**Ret dağılımı (eğitim, 52 ay):**
- Arketip: A2 7/480 (%1), A3 45/480 (%9). A3'te sezon Hinweise'i ve Kernaussage biçimi daha sık bozuluyor.
- Sakin aylar 16/147 (%11). Tablosu boş aylar 5/11.
- En sık son sorunlar: işaretsiz neden cümlesi (22), Kernaussage biçimi (19), değerlendirici ifade (11), boş tabloda „Keine.“ yerine uydurma satır (6).
- Sorunlar dağınık; tek bir plan ya da istem hatasına işaret etmiyor. Kontrol doğru reddediyor.

**Okuma (rastgele 6 metin: 3'ü ilk denemede, 3'ü 3–4. denemede kabul):**
- İlk denemede kabul edilenler doğrulama kümesi düzeyinde: nedenler notun içeriğiyle yazılmış, önceki yıl olayları „im Vorjahresmonat“ diye doğru yönde, hipotezler işaretli.
- Geç kabul edilenlerde ara sıra plan dışı bir yan cümle var. Örnek: „…, da die Gesamtleistung leicht um 1,7 % stieg“ (kümülatif sonucu aylık hasılata bağlıyor) ya da bir bayrağı Kernaussage'de uyarı yerine olgu diliyle anlatma.

**Otomatik tarama (kabul edilen 908 eğitim metni, tablo dışı):**

| Kalıp | 1. deneme | 2. deneme | 3–4. deneme |
|---|---:|---:|---:|
| İşaretsiz „…, da …“ yan cümlesi | %3 | %5 | %8 |
| „Trend / Tendenz / Kontrast / Jahresentwicklung“ | %0 | %0 | %3 |
| Tire ile eksi („–102 T€“; plan ASCII `-` kullanıyor) | %2 | %15 | %12 |

- „da“ cümlelerinin bir kısmı zararsız. Örnek: „Kumuliert entspricht das Ergebnis dem Monatswert, da es sich um den ersten Berichtsmonat handelt.“
- Toplamda metinlerin ~%5'inde bir cümlelik plan dışı yorum var. Rakam ve kaynak sadakatini bozmuyor (doğrulama geçiyor), ama öğrenci bunu da öğrenebilir.

**Öneriler [ÖNERİ]:**
- **İkinci yeniden deneme turu yok.** 908 örnek yeterli. Ret çarpıklığı küçük: eğitimde A2 473 · A3 435 ay, sakin ay 131. Bir tur daha ~20 ay kazandırır, ama bunlar en çok denemeyle kabul edilen, yani en gürültülü metinler olur.
- **Eğitim verisinde biçim birliği:** Rakamdan önceki tire (`–`) ASCII eksiye (`-`) çevrilir. Metnin geri kalanı değişmez.
- **Plan dışı yan cümleler** bilinen sınırlama olarak kalır. Altın küme ve öğrencinin değerlendirmesi, öğrencinin bunları kopyalayıp kopyalamadığını gösterir. Gerekirse 3–4. denemede kabul edilen 172 metin eğitimde ayrı bir ablation olarak çıkarılabilir.

## 15. Bağlamsız hedefler ve iki düzeltme (tur 12, 19.10.2026)

### 15.1 „Yalnızca fine-tuning“ hedefleri [KARAR, tur 12]

- **Karar:** B. Bağlamsız girdilerle ayrı bir model eğitilir (`00`, Bölüm 19). RAG + FT modelinin bağlamsız çalıştırılması ayrıca ek satır olarak raporlanır.
- **Kümeler:** `train_ohne` (960) ve `val_ohne` (144), `train`/`val` ile aynı aylar. `python -m ideal build --variant ohne_kontext`.
- **Plan:** Aynı kod, görünen not kümesi boş. Kaynak yok; nedenler hipotez ya da „Ursache offen“, V2 adayı hep uyarı, sezon bayrağı hipotez.

| Tablo satırı açıklaması | Bağlamlı (`train`) | Bağlamsız (`train_ohne`) |
|---|---:|---:|
| Kaynaklı (`quelle`) | 1.184 | 0 |
| Hipotez | 1.573 | 2.371 |
| Açık („Ursache offen“) | 310 | 696 |

- **Öğrenci girdisi [ÖNERİ]:** İstem 1.1 `ohne_kontext`: FACTS var, WISSEN ve KONTEXTNOTIZEN „Keine.“ Hedeflerdeki genel hipotez metinleri (K-B'den türetilmiş) bu girdide yok; model bunları ince ayarla öğrenir. Bunlar firmaya özgü bilgi ya da ground truth değil, genel muhasebe bilgisi; B3 korunuyor.
- **Kontrol:** Kalıp metin 1.104 bağlamsız planın hepsinde kontrolü geçiyor. Öğretmen istemi değişmedi.
- **Sıra:** Önce `val_ohne`; okuma ve onaydan sonra `train_ohne` (`ideal/README.md`, Bölüm 6).

### 15.2 Düzeltme 1: V6 (sezon) bayrağı

- **Bulgu:** Bağlamsız planları okurken görüldü. Örnek: Umsatzerlöse önceki aya göre −%14,8, önceki yıla göre −%14,9. Eski kural bunu „mevsimsel“ sayıyordu. Plan da „Veränderung gegenüber dem Vorjahresmonat deutlich kleiner“ gerekçesini yazıyordu; bu, girdideki rakamlarla çelişen bir akıl yürütme.
- **Ölçek:** Eğitim kümesinde 394 V6 bayrağının 103'ünde önceki yıla göre değişim, önceki aya göre değişimin yarısından büyüktü.
- **Düzeltme:**
  - Katman 1: Önceki yıla göre değişim ya ters yönde ya da önceki aya göre değişimin en fazla yarısı olmalı (`v6_max_ratio = 0.5`; `05_facts_semasi.md`, Bölüm 7: precision %72 → %78, recall %63 → %58).
  - Plan: Ters yönde ve benzer büyüklükte değişimde gerekçe „…in die entgegengesetzte Richtung geht“.
- **Bağlam:** Getirme sorgusu ve WISSEN bayraklara bağlı. Bayrağı kalkan 58 ayın bağlamı BGE-M3 ile yeniden getirildi; 21'inde not listesi değişti. Diğer 1.046 ayın bağlamı bayt bayt aynı.

### 15.3 Düzeltme 2: kaynak sırası

- **Bulgu:** Yeniden kurulumda, bayrağı değişmeyen bazı aylarda kaynak sırası değişti. Nedeni: eşit etkili iki olayın sırası Python'un hash tohumuna bağlıydı.
- **Düzeltme:** Eşitlikte olay kimliği belirler. Üç farklı hash tohumuyla kurulan istek dosyaları artık bayt bayt aynı (test).

### 15.4 Yeniden üretilecek aylar

Betik, her kayda öğretmen girdisinin parmak izini (`input_sha`) yazar. Mevcut kayıtlara parmak izi, üretildikleri eski istek dosyalarından eklendi. Girdisi değişen aylar betik tarafından otomatik olarak yeniden üretilir:

| Neden | Eğitim | Doğrulama |
|---|---:|---:|
| V6 bayrağı kalktı | 53 | 5 |
| Yalnızca V6 gerekçe metni | 14 | 1 |
| Yalnızca kaynak sırası | 20 | 3 |
| **Toplam** | **87** | **9** |

- 50 „ters yönlü“ V6 ayının yalnızca 14'ünde metin değişiyor; ötekilerde sezon bayrağı Firmenprofil notuyla açıklanıyor ve gerekçe metni kullanılmıyor.
- Değişmeyen ayların kabul edilmiş metinleri (eğitim 821, doğrulama 129) yeni isteklerle de kontrolü geçiyor.
- Pilot istek dosyasında 3 ay değişti; pilot çıktıları tarihî kayıttır.

## 16. Düzeltilen aylar ve bağlamsız doğrulama kümesi (20.10.2026)

Çıktılar: `ideal/outputs/train.jsonl` (1.136 kayıt), `ideal/outputs/val_ohne.jsonl` (144 kayıt). Yalnızca güncel girdiyle (sürüm + `input_sha`) üretilmiş kayıtlar sayıldı; kabul edilenlerin hepsi güncel kontrolden yeniden geçti.

| | Eğitim (`train`) | Doğrulama (`val`) | Bağlamsız doğrulama (`val_ohne`) |
|---|---|---|---|
| Kabul | **901 / 960 (%94)** | 129 / 135 güncel (9 ay bekliyor) | **134 / 144 (%93)** |
| Bu turda üretilen | 87 ay → 80 kabul, 7 ret (hepsi önceden kabul edilmişti) | 0 (yüklenen dosya değişmemişti) | 144 ay |
| Kabul edilenlerde deneme | 1: 326 · 2: 403 · 3: 108 · 4: 64 | 1: 47 · 2: 53 · 3: 21 · 4: 8 | 1: 60 · 2: 67 · 3: 6 · 4: 1 |
| Kelime (tablo hariç) | 180 / medyan 232 / 395 | — | 180 / medyan 256 / 373 |
| Token (son kayıtlar) | — | — | girdi 689 bin · çıktı 210 bin |

**`val_ohne` okuması (rastgele 5 metin) ve taraması (134 metin):**
- `[Quelle: …]` hiç yok. Somut neden kelimesi de yok („Neueinstellung“, „Großauftrag“, „Preiserhöhung“, „Firmenprofil“ …). Öğretmen plan dışı bir olay uydurmuyor.
- Hipotezler işaretli. Açık nedenler tabloda „Ursache offen“, soru bölümünde Rückfrage.
- V6 Hinweis'leri yeni kuralla rakamlarla tutarlı. Örnek: „Rückgang um 10,1 % gegenüber dem Vormonat … stärker als der Vorjahresvergleich (-3,0 %)“.
- Bağlamlı kümelere göre daha az deneme gerekiyor: kabul edilenlerin %95'i ilk iki denemede (bağlamlıda ~%80). Kaynak kuralları olmadığı için hata yüzeyi daha küçük.
- **Küçük kusurlar:**
  - Çok bayraklı aylarda Hinweise kısa kalıyor; plandaki „Folge“ cümlesi atlanıyor.
  - Rohertragsquote Kernaussage'si bazen uyarı işareti taşımıyor.
  - Üslup: „Verlust von –199.604 €“ (çift olumsuz) ve „kumuliert entspricht der Wert dem Monatsergebnis“ („Monatswert“ olmalı).
  - 7 metinde eksi işareti tire ile (eğitim verisi birleştirilirken düzeltilecek, Bölüm 14).
- **Ret nedenleri (10 ay):** İşaretsiz neden cümlesi (5), değerlendirici ifade (4), Kernaussage biçimi (3), rakamın yanlış kaleme yazılması (4).

**Sonuç [ÖNERİ]:** Kusurların hiçbiri eğitim hedefini bozmuyor; `train_ohne` başlatılabilir (`ideal/README.md`, Bölüm 7).

**Diğer:**
- Eğitimde reddedilen 7 yeni ay için ayrı bir yeniden deneme yok. `--retry-failed` eski 52 reddi de ikinci kez dener; bu, Bölüm 14'teki „ikinci tur yok“ önerisiyle çelişir. Kayıp 7 ay (%0,7).
- `python -m ideal report` artık yalnızca güncel girdiyle üretilmiş kayıtları sayar; bekleyen ayları ayrıca yazar (test).

## 17. Bağlamsız eğitim kümesi ve plan 1.4 (21.10.2026)

### 17.1 Sonuçlar (plan 1.3 girdileriyle)

| | `train_ohne` | `val` | `val_ohne` |
|---|---|---|---|
| Kabul | **923 / 960 (%96)** | 138 / 144 (bekleyen 9 ay üretildi, hepsi kabul) | 139 / 144 (yeniden denemeyle +5) |
| Yeniden deneme | 61 ay → 24 kabul | — | 10 ay → 5 kabul |
| Kabul edilenlerde deneme | 1: 443 · 2: 368 · 3: 78 · 4: 34 | | |
| Kelime | 180 / medyan 238 / 387 | | 180 / medyan 253 / 373 |
| Token (bütün denemeler) | girdi 5,17 Mio · çıktı 1,50 Mio | | |

- `train_ohne` arketip dengesi: A2 474, A3 449.
- Taramada `[Quelle]` ya da somut neden kelimesi yok. İşaretsiz „da“ yan cümlesi %4, „Trend/Tendenz“ 6 metin, tire ile eksi %7; bağlamlı kümelerle aynı düzey.

### 17.2 Bulgu: taban hipotezinin yönü

- **Okumada görüldü:** A3-v119_2025-04. Reparatur satırı tabloda „ungewöhnlich niedriger Vergleichswert“ diyor. Hinweise ise aynı Vorjahresmonat değerinin yüksek olduğunu söylüyor (48 T€, normal 14 T€).
- **Neden:** Plan, „hoher/niedriger“ kelimesini farkın yönünden türetiyordu: artış varsa taban düşük, düşüş varsa yüksek. Oysa facts yalnızca tabanın olağandışı olduğunu söylüyor, yönünü değil.
  - Tipik örnek: her yıl ikramiye ödenen ay. Taban yüksek, cari ay daha da yüksek. Plan „ungewöhnlich niedriger Vergleichswert“ diyordu, girdideki rakamlar tersini gösteriyor.
- **Ölçek:** Bağlamlı eğitim kümesinde taban hipotezlerinin %30'u (718 satırın 215'i) tutarsızdı.
- **İkinci, küçük bulgu:** „Mögliche zeitversetzte Buchung“ (geç fatura cari ayı yükseltir) 29 satırda bir düşüşün açıklaması olarak kullanılmıştı.

### 17.3 Plan 1.4

- **Taban hipotezi:** Yalnızca taban sapmayı açıklıyorsa kullanılır: artışta düşük, düşüşte yüksek taban.
  - Taban hem cari normal düzeyle (FACTS'te görünür) hem de kendi dönemindeki normal düzeyle (facts'teki `base_unusual`'ın ölçütü) karşılaştırılır; ikisi de aynı yönü göstermeli.
  - Böyle değilse „Ursache offen“ + soru.
- **Bayrak hipotezi:** Yönü uyuşmalı. Tek seferlik sıçrama, geç fatura ve yıllık amortisman yalnızca artışı, eksik amortisman yalnızca düşüşü açıklar; stok bayrakları iki yönde de açıklayabilir.
- **Doğrulama:** 2.208 planın hepsinde kalıp metin kontrolü geçiyor; yön ihlali yok (test).

**Etkilenen aylar:**

| Küme | Girdisi değişen | Geçerli kalan (kabul) |
|---|---:|---:|
| `train` | 163 | 797 (745) |
| `val` | 27 | 117 (111) |
| `train_ohne` | 319 | 641 (622) |
| `val_ohne` | 46 | 98 (96) |

Değişikliklerin büyük kısmı: „ungewöhnlich … Vergleichswert“ → „Ursache offen“ (bağlamlı eğitimde 233 satır).

### 17.4 Betikteki değişiklikler

- **Geçerlilik yalnızca `input_sha` ile:** Sürüm alanları kayıt içindir. Plan sürümü değişse bile girdisi aynı kalan ay yeniden üretilmez.
- **`--max-rounds` (varsayılan 2):** `--retry-failed` her girdiyi en fazla bir kez yeniden dener; Bölüm 14'teki „ikinci tur yok“ önerisi artık betikte.
- **Yeniden üretim:** `ideal/README.md`, Bölüm 8.
