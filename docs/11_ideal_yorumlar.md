# 11 — İdeal yorumlar (eğitim hedefleri)

> **Durum:** Hat kodlandı (`ideal/`, 8 test), istek dosyaları hazır, 18.10.2026. Sıradaki adım: kullanıcının dizüstünde pilot (24 ay).
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

- **Sistem mesajı:** 10 kural. Planı eksiksiz al ve hiçbir şey ekleme. Yalnızca plandaki rakamlar (T€ biçimi serbest). Kaynak ve hipotez işareti aynı cümlede. Kausal kelimeler yalnızca kaynaklı ya da hipotezli cümlede. 250–350 kelime, 6.3 biçimi, akıcı ve çeşitli Almanca.
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
2. **Tablo:** Tablo satırları plandakiyle aynı ve aynı sırada. Son sütun plana uygun (kaynak / Hypothese / –).
3. **Kaynaklar:** Plandaki her kaynak var, plan dışında kaynak yok.
4. **Hinweise ve sorular:** Her Hinweis maddesi var; soru sayısı plandakinden az değil.
5. **Uzunluk:** 200–400 kelime (hedef 250–350, doğrulama toleransı ±50).

Geçemeyen metin için bulunan sorunlar Almanca olarak modele geri verilir ve metin yeniden istenir. En fazla 3 deneme yapılır; sonra ay `failed` olarak kaydedilir. `--retry-failed` bu ayları sonra yeniden dener.

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
