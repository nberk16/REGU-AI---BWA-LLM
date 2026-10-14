# 04 — Sentetik veri üreteci

> **Kapsam:** CLAUDE.md Bölüm 12'deki veri üreteci adımı · **Tarih:** 14.10.2026
>
> **Kod:** `generator/` · **Testler:** `tests/test_generator.py` · **Referans koşu:** `data/synthetic/reference_seed42/`
>
> **Odak (G7):** Üreteç bir destek bileşenidir. Amacı, LLM'i eğitmek ve ölçmek için gereken BWA serilerini, bağlam notlarını ve ground truth'u üretmektir. Bu yüzden gerçekçilik "yeterli" düzeyde, kod olabildiğince basit tutuldu.

---

## 1. Kullanım

```bash
pip install -e ".[dev]"     # numpy + pytest

# Referans koşu (repoda tutulur)
python -m generator --archetypes A1,A2,A3 --variants 10 --seed 42 --out data/synthetic/reference_seed42

# Başka koşular (varsayılan: data/synthetic/run_seed<seed>_<arketip>x<varyant>, .gitignore'da)
python -m generator --variants 50 --seed 7

python -m pytest
```

- **[KARAR, tur 2]** Arketip listesi (`--archetypes`) ve arketip başına varyant sayısı (`--variants`) parametredir. Eğitim/test ayrımı kararı verildiğinde kod değiştirmek gerekmez.
- Aynı seed ve parametrelerle üretilen dosyalar byte düzeyinde aynıdır.
- Her varyantın kendi rastgele sayı akışı vardır: `[seed, arketip, varyant, aşama]`. Bu yüzden varyant sayısını artırmak mevcut varyantları değiştirmez (test: `test_more_variants_do_not_change_existing_ones`).

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

`python -m pytest`: 29 test. Neyi kontrol ettikleri:

| Grup | Kontrol |
|---|---|
| Belirlenimcilik | Aynı seed → aynı çıktı; varyant eklemek mevcutları değiştirmez; farklı seed → farklı çıktı |
| Seri kimlikleri | Yukarıdaki iki eşitlik; periyodik çarpıklıklarda yıllık toplamın korunması; v00 taban oranlarının docs/01 ile aynı olması |
| Olay kayıtları | Her olay eksiksiz (ay, satır, büyüklük, kalıcı/geçici, notlu mu); kimlikler tekil; V1–V4 hiç notlanmamış; notlu olayların notu var; V1–V5 olaylarında beklenen bayrak var; A2'de V2 Material satırında; çakışma sınırı |
| Notlar | Nottaki her rakam kayıtlı, başka rakam yok; modele görünür alanlar; boş yer tutucu yok; şablon sayıları; şablonlarda düz rakam yok |
| Oranlar | Notlama, firma notu, olaysız ay, çeldirici, rakamlı not, eşik yakını oranları hedef aralıkta |
| Ay kayıtları | 36 ay; V2 adayı karar kuralı; notsuz E04/E05 → kabul edilebilir V2 |
| Dosyalar | `model_input/` ile `evaluation/` ayrımı; CSV başlığı ve satır sayısı |

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

1. **A2'de "notla açıkla" vakası az.** A2 varyantlarının %80'i stok değişimini yalnızca envanterde kaydediyor (P3). Bu yüzden A2'nin neredeyse her ayında bir çarpıklık nedeni var. V2 adayı ayrımını ölçmek için `cite` vakası referans koşuda yalnızca 2 (`docs/03`, 9.1). Çözüm seçenekleri `00_karar_kaydi.md`, Bölüm 7'de.
2. **Muster GmbH (v00) bu seed'de zor bir dönemden geçiyor.**
   - 2024'te kalıcı +6 puanlık bir malzeme zammı (E04) ve %8'lik bir müşteri kaybı (E07) var. v00'ın olayları da diğer varyantlar gibi rastgele.
   - Faaliyet sonucu (ekonomik gerçek): 2024'te −%5,1, 2025'te −%2,3, 2026'da +%2,7.
   - Bu bir toparlanma hikâyesi olarak kullanılabilir (P4 banka iletişimi). Ama `docs/01`'deki "tipik ay" tablosundan (%6,5) belirgin biçimde farklı.
3. **`expected_flags` eşiksiz.** Çok küçük çarpıklıklar da beklenen uyarı olarak listeleniyor. Anlamlılık eşikleri [AÇIK]; belirlendiğinde değerlendirme `effects.csv`'deki büyüklüklerle süzecek.
4. **Notlar şablonla üretiliyor.** Dil çeşitliliği sınırlı. LLM ile yeniden ifade etme ileride eklenebilecek bir seçenek ([ÖNERİ], `docs/03`, 5.5).
5. **Olaylar birbirinden bağımsız çekiliyor.** Örneğin işe alımla sipariş artışı arasında nedensel bir bağ yok. Kalibrasyon (`00_karar_kaydi.md`, Bölüm 7) beklenen etkileri dengeliyor, ama tek tek varyantlarda marjlar belirgin biçimde dalgalanabiliyor.
6. **Ertelenmiş kararlara bağımlılık:** Hangi arketipin test olacağı, varyant sayısı ve eğitim hedeflerinin üretim yöntemi [AÇIK]. Üreteç bunları parametre olarak kabul ediyor.
