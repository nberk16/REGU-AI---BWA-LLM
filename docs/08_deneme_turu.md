# 08 — Almanca deneme turu (temel model seçimi)

> **Durum:** Hızlı deneme yapıldı (17.10.2026, her modelden 1 örnek); tam tur kullanıcının bilgisayarında çalışıyor.
> - **Hız (örnek başına):** Ministral ~15 dk (2,4 token/s), Gemma ~7 dk (4,3 token/s), Qwen ~12 dk (2,8 token/s).
> - **İstem okuma:** ~11–14 token/s; ~3.700 token'lık istem 5–6 dakika sürüyor. Model büyük ölçüde işlemcide çalışıyor.
> - **Tam tur:** ~5 saat (tahmini).
> - **[KARAR, tur 6]:** üç aday; ~10 örnek; aynı istem; sıfır atış.
> - **[ÖNERİ]:** seçim ölçütleri, istem metni ve üretim ayarları (bu belge).
>
> **İlgili:** `06_model_tarafi_secenekler.md` (A1, A2) · `07_dogrulama_katmani.md` · Kullanıcı adımları: [`trial/README.md`](../trial/README.md)

---

## 1. Amaç

Üç aday modelden hangisinin temel model olacağına karar vermek. Ölçütler [KARAR, tur 6]:
- Almanca akıcılık,
- format uyumu,
- rakam sadakati,
- bellek ve hız.

Sonuçlar eşit çıkarsa Ministral 3 8B seçilir [ÖNERİ].

**Dikkat:** Bu bir **sıfır atış** karşılaştırmasıdır.
- Fine-tuning formatı ve kaynak gösterme alışkanlığını sonradan öğretecek. Bu yüzden asıl önemli olan Almanca kalitesi, talimata uyma ve rakam sadakati.
- Çıktılar aynı zamanda "çıplak model" baseline'ının ilk görüntüsüdür (CLAUDE.md 7). Ancak baseline asıl olarak test kümesinde ölçülür.

## 2. Adaylar ve ayarlar

| Ad | Ollama etiketi | İndirme | Düşünme modu |
|---|---|---:|---|
| ministral-3-8b | `ministral-3:8b-instruct-2512-q4_K_M` | 6,0 GB | yok |
| gemma4-e4b | `gemma4:e4b-it-q4_K_M` | 6,6 GB | kapalı (`think: false`) |
| qwen3.5-9b | `qwen3.5:9b-q4_K_M` | 6,6 GB | kapalı (`think: false`) |

- **Nicemleme:** Hepsi aynı (q4_K_M); karşılaştırma adil olsun diye.
- **Düşünme modu kapalı:** Kullanıcının bilgisayarında saniyede birkaç token üretildiği için düşünme metni süreyi katlardı. Son model de düşünmeden yazacak.
- **Üretim ayarları** [ÖNERİ]: `temperature 0.2`, `seed 42`, `num_ctx 8192`, `num_predict 1500`.
  - İstemler ~9–12,5 bin karakter (tahminen 4–5 bin token).
  - Betik, istem bağlam sınırına yaklaşırsa ya da çıktı uzunluk sınırında kesilirse uyarır.
- **Bellek:** İndirme boyutları 4 GB'lık GPU'dan büyük. Ollama modelin bir kısmını GPU'ya, kalanını RAM'e koyar. Betik bu payı kaydeder (`/api/ps`).

## 3. İstem (`prompting/`, sürüm 1.0)

Deneme turu, baseline'lar ve fine-tuning aynı istem biçimini kullanır. Değişiklikte `PROMPT_VERSION` artırılır.

- **Sistem mesajı (Almanca):**
  - Rol: Mittelstand firmasında Controller; okuyucu Geschäftsführung.
  - 7 kural:
    1. Yalnızca FACTS'teki ya da bir nottaki rakamlar; hesaplama yok.
    2. Almanca rakam biçimi ve ticari yuvarlama.
    3. Her nedende `[Quelle: …]` veya `(Hypothese)`; nottan gelen rakamda kaynak şart.
    4. Neden uydurma yok; „Ursache offen“ ve soru.
    5. `positions`'taki bütün kalemler tabloda.
    6. `hinweis` bayrakları uyarı dilinde; `kandidat` notla açıklanır ya da uyarılır.
    7. ~250–350 kelime.
  - Çıktı şablonu: CLAUDE.md 6.3, `docs/07` Bölüm 2. Kernaussagen başlığı ayın adıyla doldurulur.
- **Kullanıcı mesajı:**
  - `facts.json`, sıkıştırılmış JSON olarak.
  - Bağlam notları: `- [kimlik] ay, süre: metin`; önce `Firmenprofil`, sonra kronolojik.
  - Notlar: 13 aylık penceredeki bütün notlar. Katman 2 (top-k) henüz yok; doğrulama katmanı da aynı not kümesini kullanır.
- **Ground truth modele gitmez.** Testle denetlenir: istemlerde `event_id`, `expected_flags`, `v2_candidate_decision` vb. yok.

## 4. Örnekler (`trial/inputs/`)

- **Kaynak:** Doğrulama varyantları (A2/A3 v120–v122, `train_seed7`; `docs/04`, 9.1). Test kümesi model seçiminde kullanılmaz.
- **Seçim** (`trial/prepare.py`): ground truth'a bakarak çeşitlilik sağlanır, sabit bir sırayla. Her ölçüt için o ölçüte uyan aylardan biri seçilir. Önce en az örneği seçilmiş firmaya, sonra hedef aya en yakın olana bakılır.

| # | Örnek | Ölçüt |
|---|---|---|
| 1 | A3-v121 2025-03 | V2 adayı, notla açıklanmalı (`cite`), A3 |
| 2 | A2-v120 2025-09 | V2 adayı, notla açıklanabilir (`either`), A2 |
| 3 | A2-v121 2026-03 | V2 adayı, uyarılmalı (`warn`), A2 |
| 4 | A2-v122 2025-06 | V1 eksik tahakkuk |
| 5 | A2-v120 2026-05 | V3 amortisman yalnızca yıl sonunda |
| 6 | A3-v122 2025-10 | V4 geç kayıt |
| 7 | A3-v120 2025-12 | V5 tek seferlik etki, rakamlı not |
| 8 | A3-v121 2026-07 | V6 mevsimsellik |
| 9 | A3-v120 2025-02 | Sakin ay |
| 10 | A3-v122 2026-09 | Çeldirici not (5 anlamlı kalem) |

Ayrıntılar (bayraklar, beklenen kararlar, notlar): [`trial/inputs/selection.md`](../trial/inputs/selection.md). `cases.jsonl` yeniden üretilebilir; bir test, dosyanın üreteç ve Katman 1 ile birebir aynı çıktığını denetler.

## 5. Akış

1. **Kullanıcı:** Ollama + üç model + Python; `python trial/run_ollama.py --limit 1` (hızlı deneme), sonra bütün örnekler (`trial/README.md`).
2. **Kullanıcı:** `trial/outputs/*.jsonl` dosyalarını dala yükler.
3. **Asistan:** `python trial/score.py` → `trial/results.md`. Tabloda:
   - format uyumu,
   - rakam sadakati,
   - itiraz edilen rakamlar,
   - işaretsiz nedenler,
   - eksik kalem ve bayraklar,
   - kelime sayısı,
   - token/s,
   - örnek başına süre,
   - GPU payı.
4. **Asistan:** Çıktıları okur ve Almanca kalite ile üslubu değerlendirir. Örnekler: dilbilgisi, terimler (Rohertrag, Vorjahresmonat …), olgu/tahmin ayrımı, uydurma neden var mı.
5. **Kullanıcı:** Temel modeli seçer [KARAR].

## 6. Betikler

| Dosya | Nerede çalışır | Görev |
|---|---|---|
| `trial/prepare.py` | Repo ortamı (asistan) | Doğrulama koşusunu üretir (yoksa), örnekleri seçer, `inputs/` yazar |
| `trial/run_ollama.py` | Kullanıcının bilgisayarı | Yalnızca standart kütüphane. Modelleri çalıştırır; çıktı, süre, token ve GPU payını kaydeder. Kaldığı yerden devam eder |
| `trial/score.py` | Repo ortamı (asistan) | Doğrulama katmanıyla puanlar, `results.md` yazar |

Testler (`tests/test_trial.py`):
- girdilerin yeniden üretilebilirliği,
- ground truth sızıntısı olmaması,
- betiğin sahte bir Ollama sunucusuyla uçtan uca çalışması: düşünme metninin ayıklanması, devam etme, eksik model uyarısı, puanlama.

## 7. Sonuçlar (17.10.2026)

Tam tur tamamlandı: 3 model × 10 örnek, hata yok, istem kesilmedi. Ayrıntılar ve okuma değerlendirmesi: [`trial/results.md`](../trial/results.md).

| Model | Format uyumu | Rakam sadakati | İçerik hatası / örnek | Kaynaklı neden | V2 kararı (4 net örnek) | Süre / örnek |
|---|---:|---:|---:|---:|---:|---:|
| gemma4-e4b | 6/10 | 0,99 | 2,2 | 5 | ~1,5/4 | ~6,5 dk |
| qwen3.5-9b | 7/10 | 0,96 | 3,7 | 29 | 2/4 | ~9,5 dk |
| ministral-3-8b | 0/10 | 0,80 | 12,7 | 43 (çoğu biçimsiz) | ~0,5/4 | ~14 dk |

**Özet:**
- **Gemma:** güvenilir ama yüzeysel; notları az kullanıyor; en hızlısı.
- **Qwen:** içerik ve Almanca açısından en iyisi; yüzdeleri kendisi hesaplıyor ve bazen yanlış nota bağlıyor.
- **Ministral:** bu görevde açık ara en zayıfı; uydurma rakamlar ve büyüklük hataları var, biçim hiç tutmuyor.
- Eşitlik yok, bu yüzden eşitlik kuralı (Ministral) uygulanmaz.

**Karar kullanıcıda [AÇIK]** (`00_karar_kaydi.md`, Bölüm 14).
