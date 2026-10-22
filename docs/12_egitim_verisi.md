# 12 — Eğitim verisi, altın küme ve Kaggle hazırlığı

> **Durum (22.10.2026):**
> - Eğitim verisi birleştirildi (`training/`, `gpu/data/`); altın küme hazır (`ideal/gold/`, 30 metin).
> - Test istemleri yazıldı (3 varyant × 720 ay). İlk Kaggle defteri hazır: `gpu/01_baseline.ipynb`.
> - **[ÖNERİ]:** temizlik kuralları, üretim ayarları (bu belge).
>
> **İlgili:** `11_ideal_yorumlar.md` (öğretmen metinleri) · `10_istem.md` (öğrenci istemi 1.1) · Kullanıcı adımları: [`gpu/README.md`](../gpu/README.md) · Karar kaydı: `00`, Bölüm 20

---

## 1. Eğitim verisi (`python -m training`)

Her örnek bir sohbettir: sistem mesajı + kullanıcı mesajı (öğrenci istemi 1.1) + asistan mesajı (öğretmenin kabul edilmiş, temizlenmiş metni).

| Dosya | Model | Öğrenci istemi | Örnek |
|---|---|---|---:|
| `train_rag.jsonl.gz` | RAG + FT (ana model) | `rag_k8` | **898** |
| `val_rag.jsonl.gz` | RAG + FT | `rag_k8` | 133 |
| `train_ohne.jsonl.gz` | yalnızca FT (karşılaştırma) | `ohne_kontext` | **933** |
| `val_ohne.jsonl.gz` | yalnızca FT | `ohne_kontext` | 140 |

**Adımlar (sırayla):**
1. **Yalnızca güncel ve kabul edilmiş metinler.** Kaydın `input_sha`'sı güncel istekle aynı olmalı.
2. **Not eşitliği.** Öğrencinin istemindeki notlar, planın gördüğü notlarla birebir aynı olmalı; değilse dur. Bağlamsız istekte not yok.
3. **Eksi işareti.** Rakamdan önceki tire ASCII eksiye çevrilir (`docs/11`, Bölüm 14). `train_rag`'de 78, `train_ohne`'de 68 metin.
4. **Kernaussage uyarısı.** Plan bir Kernaussage'yi uyarı olarak istiyorsa ve metin uyarı dili içermiyorsa, planın kısa hipotezi eklenir: `Hinweis: möglicher Buchungseffekt (Hypothese).` (CLAUDE.md 6.3'teki örnekle aynı biçim). Altın kümede bulunan en sık kusur bu (Bölüm 3). Eklenen: `train_rag` 261, `train_ohne` 322.
5. **Plandan sapan Kernaussage.** Uyarı yerine başka bir kalemi anlatan aylar alınmaz: `train_rag` 4, `train_ohne` 7.
6. **Yeniden kontrol.** Temizlenmiş her metin `ideal/check.py`'den yeniden geçer; geçmezse dur.

**Ayrıca dışarıda kalan 8 ay (eğitim 5, doğrulama 3):**
- Bu aylarda bir tablo satırı hem cari hem önceki yıl olayına dayanıyordu. Öğretmen istemi yalnızca ilk notun zamanını söylüyordu.
- Altın kümede bir önceki yıl siparişi bu yüzden „verzögerte Auslieferung“ diye yorumlanmıştı.
- Plan 1.5 ve öğretmen 1.4 her notun zamanını ayrıca söylüyor. Girdisi değiştiği için bu aylar parmak iziyle kendiliğinden dışarıda kalıyor. İstenirse kısa bir öğretmen koşusuyla geri alınabilir.

**Kayıt alanları:** `id`, `firm_id`, `period`, `variant`, `prompt_version`, `plan_version`, `teacher{set, input_sha, attempts, model}`, `messages`.

**Uzunluk (karakter; Gemma'da kabaca 2,75 karakter/token):**

| Dosya | Medyan | En fazla | ≈ en fazla token |
|---|---:|---:|---:|
| `train_rag` | 16.734 | 22.623 | ~8.200 |
| `train_ohne` | 11.382 | 14.642 | ~5.300 |

## 2. Test istemleri

`reference_seed42` (A1 + görülmemiş A2/A3 varyantları, 720 firma-ay), hedef metin yok:

| Dosya | Varyant | Kullanıldığı yer |
|---|---|---|
| `test_ohne_kontext.jsonl.gz` | bağlamsız | çıplak model, yalnızca FT, RAG + FT modeli bağlamsız (ek satır) |
| `test_rag_k8.jsonl.gz` | top-8 not | yalnızca RAG, RAG + FT |
| `test_rag_alle.jsonl.gz` | penceredeki bütün notlar | retrieval'ın katkısı (`docs/09`, 5.3) |

- Bağlam BGE-M3 ile yeni V6 kuralına göre getirildi (`data/synthetic/reference_seed42/rag/`, repoda değil).
- `rag_k8` istemi medyan 14.512, en fazla 20.249 karakter (~7.400 token).

## 3. Altın küme (`python -m ideal gold`)

- **Kaynak:** Pilot için seçilmiş 24 çeşitli doğrulama ayı (bütün çarpıklık türleri, notla açıklanan ve uyarılan V2, çeldirici, sakin ay) ve 6 rastgele bağlamsız doğrulama ayı.
- **Okuma:** Plan ve notlarla birlikte satır satır okundu.
- **Düzeltme:** Önce eğitim verisinin otomatik temizliği uygulanır, sonra elle düzeltmeler (`ideal/gold/edits.json`). Bütün altın metinler kontrolden geçiyor.
- **Çıktı:** `ideal/gold/gold.jsonl` (öğretmen metni, altın metin, bulgular).

| Sonuç | Metin |
|---|---:|
| Düzeltme gerekmedi | 14 |
| Yalnızca otomatik düzeltme (Kernaussage uyarısı) | 10 |
| Elle düzeltme | 6 |

| Elle bulgu | Metin | Not |
|---|---:|---|
| Plandan sapan Kernaussage | 2 | Eğitimde otomatik dışarıda |
| Önceki yıl olayı yanlış yorumlanmış | 1 | Karışık zamanlı satır; eğitimde dışarıda |
| Yön sözcüğü („verringerten sich“, değer arttığı hâlde) | 1 | |
| Plan dışı muhasebe iddiası („Gegenbuchung“) | 1 | |
| Kernaussage'de Vorjahr karşılaştırması eksik | 1 | |
| Belirsiz „Minus“ (kümülatif kayıp mı, fark mı?) | 1 | |
| Üslup („um das 16,5-Fache über“) | 1 | |

**Yorum:**
- Otomatik temizlikten sonra 30 metnin 24'ü altın kalitede.
- Eğitim verisinde kalan kusurlar, metinlerin kabaca %10–15'inde tek bir sözcük ya da cümle düzeyinde. Rakam ve kaynak hataları yok (kontrol).
- **Kullanım alanları:**
  - Öğretmen kalitesinin ölçüsü (portfolyo).
  - Üslup değerlendirmesinde referans (`CLAUDE.md` 8, [AÇIK]).
  - Model çıktılarını okurken karşılaştırma örneği.

## 4. Kaggle defteri 01: baseline (`gpu/01_baseline.ipynb`)

- **Varyantlar:** Çıplak model (`ohne_kontext`) ve yalnızca RAG (`rag_k8`), test kümesinin 720 ayı.
- **Model:** `unsloth/gemma-4-E4B-it` (Apache 2.0, kapılı değil), Unsloth ile 4-bit.
  - Neden Unsloth: T4'te Gemma'nın float16 taşmalarına karşı düzeltme içeriyor.
  - İnce ayar da QLoRA ile aynı 4-bit taban üzerinde yapılacak; şablon ve niceleme bütün varyantlarda aynı kalır.
- **Şablon:** Modelin kendi sohbet şablonu, düşünme kipi kapalı (`enable_thinking=False`). Sistem rolü destekleniyor.
- **Üretim [ÖNERİ]:** Deneme turuyla aynı ayarlar: `temperature 0.2`, `top_p 0.95`, `top_k 64`, `seed 42`, en fazla 1.500 yeni token.
- **Çalışma:**
  - Partiler: bağlamsız 8, RAG 4. Bellek yetmezse yarıya iner.
  - Uzun istemler önce gelir. Her partiden sonra kayıt yazılır; aynı oturumda kaldığı yerden devam eder.
- **Doğrulama:** Defter GPU olmadan sahte bir modelle denendi: dosya bulma, deneme kipi, parti küçültme, devam, 720 kayıt.
- **Belirsizlik:**
  - Gemma 4 + Unsloth + Kaggle T4 birleşimi henüz Kaggle'da denenmedi.
  - Kaynaklar E4B QLoRA için ~10 GB, LoRA için ~17 GB VRAM veriyor.
  - Bu yüzden önce 2 istemlik bir deneme koşusu var (`gpu/README.md`, Bölüm 3).

Kaynaklar: [Unsloth — Gemma 4 Fine-tuning Guide](https://unsloth.ai/docs/models/gemma-4/train) · [unsloth/gemma-4-E4B-it](https://huggingface.co/unsloth/gemma-4-E4B-it)

## 5. Sıradaki

1. Kullanıcı: Kaggle'da veri seti ve deneme koşusu (`gpu/README.md`). Hız ölçülünce tam koşunun süresi tahmin edilir.
2. Asistan: baseline çıktılarının puanlanması (doğrulama katmanı + ground truth metrikleri, paket 9) ve ince ayar defteri (paket 7).
