# 04 — Sentetik veri üreteci

> **Kapsam:** CLAUDE.md Bölüm 12'deki veri üreteci adımı · **Tarih:** 14.10.2026
>
> **Kod:** `generator/` · **Testler:** `tests/test_generator.py` · **Referans koşu:** `data/synthetic/reference_seed42/` · **Dengelenmiş V2 kümesi:** `data/synthetic/v2_balanced_seed4242/`
>
> **Odak (G7):** Üreteç bir destek bileşenidir. Amacı, LLM'i eğitmek ve ölçmek için gereken BWA serilerini, bağlam notlarını ve ground truth'u üretmektir. Bu yüzden gerçekçilik "yeterli" düzeyde, kod olabildiğince basit tutuldu.

---

## 1. Kullanım

```bash
pip install -e ".[dev]"     # numpy + pytest

# Referans koşu (repoda tutulur)
python -m generator --archetypes A1,A2,A3 --variants 10 --seed 42 --out data/synthetic/reference_seed42

# Dengelenmiş V2 kümesi (repoda tutulur; Bölüm 8)
python -m generator --profile v2_balanced --variants 10 --first-variant 50 --seed 4242 --out data/synthetic/v2_balanced_seed4242

# Başka koşular (varsayılan: data/synthetic/run_seed<seed>_<arketip>x<varyant>[_<profil>], .gitignore'da)
python -m generator --variants 50 --seed 7
python -m generator --profile train_price_boost --variants 30 --seed 7   # yalnızca eğitim verisi için

python -m pytest
```

- **[KARAR, tur 2]** Arketip listesi (`--archetypes`) ve arketip başına varyant sayısı (`--variants`) parametredir. Eğitim/test ayrımı kararı verildiğinde kod değiştirmek gerekmez.
- Aynı seed ve parametrelerle üretilen dosyalar byte düzeyinde aynıdır.
- Her varyantın kendi rastgele sayı akışı vardır: `[seed, arketip, varyant, aşama]`. Bu yüzden varyant sayısını artırmak mevcut varyantları değiştirmez (test: `test_more_variants_do_not_change_existing_ones`).
- `--first-variant` varyant numaralarını kaydırır (ör. v50–v59). Ayrı kümeler böylece referans koşuyla aynı firmaları ve adları paylaşmaz.
- `--profile` ana parametrelerin üzerine küçük bir TOML dosyası yazar (`generator/config/profiles/`). Ana parametre dosyaları değişmez.

---

## 2. Nasıl çalışır?

**Temel fikir:** Her varyant için iki seri üretilir.

| Seri | Anlamı | Nerede |
|---|---|---|
| **Ekonomik gerçek** | Her şey doğru ve zamanında kaydedilseydi BWA'nın göstereceği değerler | `evaluation/bwa_true.csv` |
| **Kaydedilen BWA** | Muhasebe pratikleri (V1–V4) uygulandıktan sonraki hali; modelin gördüğü seri | `model_input/bwa_raw.csv` |

Çarpıklıkların büyüklüğü bu iki serinin farkıdır. Bu yüzden ground truth'taki her rakam kesin değerdir, tahmin değil.

**Akış** (`generator/pipeline.py`):

1. **Varyant** (`variant.py`): Arketipten büyüklük, maliyet oranları, sezon genliği, trend ve muhasebe pratikleri çekilir. v00 arketipin değerlerini aynen alır; `A1-v00` = Muster GmbH.
2. **Taban seri** (`model.py`): trend × sezon × maliyet oranları.
   - Üreticilerde stok değişimi = (üretim − satış) × Herstellkostenfaktor.
   - Sabit giderlerde yıllık %2 enflasyon kayması var.
   - AfA tabanı yılda %6, faiz tabanı yılda %10 azalır (amortisman bitişi, kredi geri ödemesi).
3. **Gerçek olaylar** (`events.py`, E01–E12): Olaylar satırları doğrudan değil, **sürücüleri** değiştirir: hacim, fiyat, malzeme oranı, çalışan sayısı, ücret düzeyi vb. Her olaydan sonra satırlar yeniden hesaplanır; aradaki fark olayın kesin etkisidir. Örneğin E06 Großauftrag hacmi artırır, Umsatz, Material ve Kosten der Warenabgabe birlikte değişir.
4. **Gürültü**: Her satır-aya çarpımsal ±%1,5 (en fazla ±%4) gürültü eklenir.
5. **Muhasebe pratikleri** (`practices.py`, E13–E18): Ekonomik gerçek seri kaydedilen seriye dönüştürülür. Her dönüşüm bir olay olarak kaydedilir.
6. **Sezon kaydı** (E19), olay kimlikleri ve çakışmalar.
7. **Notlar** (`notes.py`): %70 notlama, çeldiriciler, `Firmenprofil` notu, şablonlar (`docs/03`, Bölüm 5).
8. **Ground truth** (`ground_truth.py`): Olay kayıtları, ay kayıtları, kabul edilebilir uyarılar, V2 adayı kararı.

**Kesinlik eşitlikleri** (testlerle doğrulanıyor):

- `ekonomik seri (gürültüsüz) = taban + Σ gerçek olay etkileri`
- `kaydedilen BWA − ekonomik gerçek = Σ çarpıklık etkileri (V1–V4)`
- Periyodik V1–V3 çarpıklıkları yalnızca zamanlamayı kaydırır; yıllık toplamı değiştirmez.

---

## 3. Çıktılar

```
data/synthetic/<koşu>/
├── model_input/                    ← modele ve RAG'e girebilir
│   ├── bwa_raw.csv                 kaydedilen BWA, 21 temel satır, uzun format (docs/02, B2)
│   ├── context_notes.jsonl         bağlam notları (K-C), duration alanıyla
│   └── firms.json                  firma kimliği ve adı
├── evaluation/                     ← yalnızca değerlendirme
│   ├── bwa_true.csv                ekonomik gerçek seri
│   ├── effects.csv                 her olayın her satır-aya kesin etkisi
│   ├── events.jsonl                olay kayıtları (docs/03, 7.1)
│   ├── ground_truth_months.jsonl   firma-ay kayıtları (docs/03, 7.2)
│   ├── notes_ground_truth.jsonl    not–olay eşlemesi, çeldirici işareti, nottaki rakamlar
│   └── variants.json               varyant parametreleri ve muhasebe pratikleri
├── manifest.json                   seed, parametre özeti, dosya listesi, istatistikler
└── report.md                       sağlama raporu (hedef oranlar, kalibrasyon, Muster GmbH)
```

**Ayrım ilkesi [KARAR, tur 3]:** `evaluation/` klasöründeki hiçbir dosya RAG'e veya model girdisine girmez. Muhasebe pratikleri gibi gizli bilgiler (`variants.json`) de bu klasördedir. `test_written_files_separate_model_input_and_evaluation` testi, model dosyalarında olay kimliği ya da bayrak bulunmadığını kontrol eder.

---

## 4. Parametreler

| Dosya | İçerik |
|---|---|
| `generator/config/archetypes.toml` | Arketipler: büyüklük, maliyet oranları, sezon, üretim kayması, muhasebe pratiği olasılıkları, v00 profilleri, not kelime havuzları (docs/01) |
| `generator/config/generation.toml` | Seri, varyant aralıkları, olay sıklıkları ve büyüklükleri, not oranları (docs/03) |
| `generator/config/note_templates.toml` | Not şablonları: tür başına 5, `Firmenprofil` için arketip başına 4, 11 çeldirici (docs/03, 5.5) |

- Bütün sayısal değerler [ÖNERİ] etiketlidir. Bir değer değiştiğinde kullanıcıya bildirilir ve `00_karar_kaydi.md`'ye işlenir.
- `manifest.json`'daki `config_fingerprint`, koşunun hangi parametrelerle üretildiğini gösterir.

---

## 5. Testler

`python -m pytest`: 50 test. Bunların 35'i üreteç testleri (`tests/test_generator.py`); Katman 1 testleri için bkz. `docs/05`. Üreteç testlerinin kontrol ettikleri:

| Grup | Kontrol |
|---|---|
| Belirlenimcilik | Aynı seed → aynı çıktı; varyant eklemek mevcutları değiştirmez; farklı seed → farklı çıktı |
| Seri kimlikleri | Yukarıdaki iki eşitlik; periyodik çarpıklıklarda yıllık toplamın korunması; v00 taban oranlarının docs/01 ile aynı olması |
| Olay kayıtları | Her olay eksiksiz (ay, satır, büyüklük, kalıcı/geçici, notlu mu); kimlikler tekil; V1–V4 hiç notlanmamış; notlu olayların notu var; V1–V5 olaylarında beklenen bayrak var; A2'de V2 Material satırında; çakışma sınırı |
| Notlar | Nottaki her rakam kayıtlı, başka rakam yok; modele görünür alanlar; boş yer tutucu yok; şablon sayıları; şablonlarda düz rakam yok |
| Oranlar | Notlama, firma notu, olaysız ay, çeldirici, rakamlı not, eşik yakını oranları hedef aralıkta |
| Ay kayıtları | 36 ay; V2 adayı karar kuralı; notsuz E04/E05 → kabul edilebilir V2 |
| Dosyalar | `model_input/` ile `evaluation/` ayrımı; CSV başlığı ve satır sayısı |
| Profiller ve V2 kümesi | Profilin parametreleri değiştirmesi (diğer alanlar korunur); bilinmeyen profilin reddi; varyant numarası kaydırma; Rohertrag adayı kuralı; dengelenmiş kümede `cite` = `warn`; arketip başına V2 karar sayıları |

---

## 6. Referans koşu (seed 42, 3 arketip × 10 varyant)

| Ölçüt | Hedef (docs/03) | Gerçekleşen |
|---|---|---|
| Notlanan gerçek olaylar | ~%70 | %70,7 |
| Firma notu olan varyantlar | ~%70 | %70 |
| Havuz olayı / ay | ~2 (ilk tahmin) | 1,51 |
| Olaysız ay (yorumlanabilir) | ~%15 | %15,4 |
| Çeldirici notlu ay | %10–15 | %10,6 |
| Rakamlı olay notları | ~%50 | %49,3 |
| Eşik yakını havuz olayları | ~%20 | %17,7 |
| Çakışan havuz olayları | ~%10 | %13,0 |

- Toplam 1.896 olay, 30 varyant × 36 ay.
- Yıllık ortalama faaliyet sonucu marjları %0–5 aralığında; varyantlar arasında −%9 ile +%11 arasında dağılıyor.
- Boyut ~5,7 MB. Model dosyaları ~1,2 MB, değerlendirme dosyaları ~4,5 MB.
  - Plan aşamasında verdiğim "~1 MB" tahmini yalnızca ham BWA içindi.
  - Her olayın eksiksiz kaydı (tur 2) ve ekonomik gerçek seri boyutu büyütüyor.

---

## 7. Bilinen sınırlamalar

1. **A2'de "notla açıkla" vakası az** (ana veride). Bu durum bilinçli olarak korunuyor: ana veri gerçekçi kalıyor; ayrım metriği dengelenmiş V2 kümesiyle ölçülüyor (Bölüm 8, karar turu 4).
2. **Muster GmbH (v00) bu seed'de bir toparlanma hikâyesi çiziyor** [KARAR, tur 4: böyle kalıyor].
   - 2024'te kalıcı +6 puanlık bir malzeme zammı (E04) ve %8'lik bir müşteri kaybı (E07) var.
   - Faaliyet sonucu (ekonomik gerçek): 2024'te −%5,1, 2025'te −%2,3, 2026'da +%2,7.
   - Portfolyoda banka iletişimi (P4) örneği olarak kullanılabilir.
3. **`expected_flags` eşiksiz.** Çok küçük çarpıklıklar da beklenen uyarı olarak listeleniyor. Anlamlılık eşikleri [AÇIK]; belirlendiğinde değerlendirme `effects.csv`'deki büyüklüklerle süzecek.
4. **Notlar şablonla üretiliyor.** Dil çeşitliliği sınırlı. LLM ile yeniden ifade etme ileride eklenebilecek bir seçenek ([ÖNERİ], `docs/03`, 5.5).
5. **A2'de Rohertragsquote oynak** [KARAR, tur 5: E18 kalibre edildi].
   - Geç gelen faturaların (E18) malzeme satırındaki kayması %15–40'tan %5–20'ye indirildi.
   - A2'de kaydedilen Rohertragsquote: p5 / p95 = %1,9 / %48,3; negatif ay sayısı 26'dan 8'e indi. Ekonomik gerçek %17–34 aralığında.
   - Kalan oynaklığın nedeni envanter pratiği: alışlar büyük siparişlerden bir ay önce geliyor. Bu, envanteri yıl sonunda yapan bir toptancı için gerçekçi.
6. **Olaylar birbirinden bağımsız çekiliyor.** Örneğin işe alımla sipariş artışı arasında nedensel bir bağ yok. Kalibrasyon (`00_karar_kaydi.md`, Bölüm 7) beklenen etkileri dengeliyor, ama tek tek varyantlarda marjlar belirgin biçimde dalgalanabiliyor.
7. **Ertelenmiş kararlara bağımlılık:** Hangi arketipin test olacağı, varyant sayısı ve eğitim hedeflerinin üretim yöntemi [AÇIK]. Üreteç bunları parametre olarak kabul ediyor.

---

## 8. Profiller ve dengelenmiş V2 kümesi [KARAR, tur 4]

### 8.1 Neden?

- "V2 adayı ayrımı" metriği (CLAUDE.md 8), Rohertrag adayı aylarda modelin doğru kararı verip vermediğini ölçer: `cite` (notla açıkla) / `warn` (uyar) / `either`.
- Ana veride bu kararlar çok dengesiz. Özellikle A2'de hemen her ay `warn`.
- Karar: **Ana veri gerçekçi kalır.** Metrik için ayrı ve dengeli bir test kümesi üretilir.

### 8.2 Profiller (`generator/config/profiles/`)

| Profil | Ne değiştirir | Kullanım |
|---|---|---|
| `v2_balanced` | A2'de P3 olasılığı 0,8 → 0,2; E04 2–4/yıl, E05 1–3/yıl | Yalnızca dengelenmiş V2 kümesi |
| `train_price_boost` | E04 1–3/yıl, E05 1–2/yıl ("ölçülü" artış) | Yalnızca eğitim verisi; referans koşu ve test kümeleri kullanmaz |

### 8.3 Dengelenmiş V2 kümesi (`data/synthetic/v2_balanced_seed4242/`)

- **Komut:** `--profile v2_balanced --variants 10 --first-variant 50 --seed 4242`.
  - Farklı seed ve v50–v59 varyant numaraları, referans koşuyla firma paylaşımını önler.
- **Seçim** (`evaluation/v2_balanced_set.jsonl`):
  - Yalnızca Rohertrag adayı aylar: Rohertragsquote önceki aya **ve** önceki yılın aynı ayına göre ≥ 2 puan değişmiş (Katman 1 kuralı).
  - Her arketipte `cite` ve `warn` aylarından eşit sayıda; `either` aylarından en fazla aynı sayıda.
- Raporda ve dosyada **"dengelenmiş set"** olarak işaretli; gerçek dağılımı yansıtmaz.

| Arketip | cite | warn | either | Toplam |
|---|---:|---:|---:|---:|
| A1 | 12 | 12 | 6 | 30 |
| A2 | 26 | 26 | 12 | 64 |
| A3 | 20 | 20 | 13 | 53 |

### 8.4 Eğitim verisindeki `cite` örnekleri

Rohertrag adayı aylarda beklenen kararlar, 10 varyant / arketip, yorumlanabilir aylar:

| Arketip | Ana veri (referans koşu): cite / warn / either | `train_price_boost` ile: cite / warn / either |
|---|---|---|
| A1 | 6 / 88 / 7 | 15 / 73 / 10 |
| A2 | 0 / 177 / 1 | 3 / 172 / 1 |
| A3 | 13 / 85 / 7 | 24 / 79 / 11 |

(E18 kalibrasyonundan sonraki değerler, tur 5.)

- Ana veride bir `cite` örneğine ~7–15 `warn` düşüyor. Bu, modelin "notla açıklanan aday" durumunu öğrenmesi için az.
- `train_price_boost` `cite` sayısını yaklaşık iki katına çıkarıyor; A2'de etkisi küçük, çünkü orada P3 baskın.
- Eğitim verisindeki toplam örnek sayısı tur 7'de kararlaştırıldı: arketip başına 20 eğitim varyantı (Bölüm 9).
- Her koşunun `report.md` dosyasında arketip başına bu tablo otomatik olarak yer alır.

## 9. Eğitim, doğrulama ve test kümeleri [KARAR, tur 7]

Ayrıntı ve gerekçe: `06_model_tarafi_secenekler.md`, Bölüm C; karar kaydı: `00`, Bölüm 11.

### 9.1 Eğitim + doğrulama koşusu

```bash
python -m generator --archetypes A2,A3 --variants 23 --first-variant 100 \
    --seed 7 --profile train_price_boost --out data/synthetic/train_seed7
```

- **v100–v119:** eğitim. **v120–v122:** doğrulama (erken durdurma, hiperparametre, deneme turu örnekleri).
- Koşu repoya konmaz (`.gitignore`, tur 3 kuralı); bu komutla birebir yeniden üretilir. Kaggle defterleri de veriyi bu komutla üretir.
- Her varyant kendi rastgele akışıyla `[seed, arketip, varyant, aşama]` üretilir. Bu yüzden v100–v119, toplam varyant sayısından bağımsız olarak aynıdır; 20 ve 23 varyantlık koşular karşılaştırılarak kontrol edildi.

| Küme | Varyantlar | Yorumlanabilir ay | Rohertrag adayı aylar: cite / warn / either |
|---|---|---:|---|
| Eğitim | A2 + A3, v100–v119 | 960 | 47 / 509 / 19 |
| Doğrulama | A2 + A3, v120–v122 | 144 | 14 / 65 / 7 |

### 9.2 Test kümeleri (eğitimde hiç kullanılmaz)

| Küme | Kaynak | Yorumlanabilir ay | Ne ölçer |
|---|---|---:|---|
| Yeni sektör (öğretilmemiş tür) | `reference_seed42`, A1 v00–v09 (Muster GmbH dahil) | 240 | Hiç görülmemiş arketipe genelleme |
| Yeni firma (öğretilmiş tür) | `reference_seed42`, A2 + A3 v00–v09 | 480 | Bilinen arketipte yeni firmaya genelleme |
| V2 ayrımı (dengelenmiş set) | `v2_balanced_seed4242`. A1 kısmı yeni sektör, A2/A3 kısmı yeni firma olarak raporlanır | 147 aday ay | `cite` / `warn` / `either` kararı |
