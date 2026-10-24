# 12 — Eğitim verisi, altın küme ve Kaggle hazırlığı

> **Durum (23.10.2026):**
> - Eğitim verisi birleştirildi (`training/`, `gpu/data/`); altın küme hazır (`ideal/gold/`, 30 metin).
> - Test istemleri yazıldı (3 varyant × 720 ay). Kaggle defteri: `gpu/01_baseline.ipynb`.
> - Deneme koşusu 1 (Transformers + Unsloth) çok yavaştı (~60 saat). Defter Ollama'ya geçti; deneme koşusu 2'de tam koşu tahmini ~1,8 saat (Bölüm 4).
> - **[ÖNERİ]:** temizlik kuralları, üretim ayarları, çıkarım altyapısı (bu belge).
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

- **Varyantlar:** Çıplak model (`ohne_kontext`), yalnızca RAG (`rag_k8`) ve bütün notlarla RAG (`rag_alle`, retrieval'ın katkısı), test kümesinin 720 ayı. `rag_alle` deneme koşusu 2'den sonra eklendi [ÖNERİ]: Ollama ile ek maliyeti ~40 dakika.
- **Şablon ve ayarlar [ÖNERİ]:** Modelin kendi sohbet şablonu, düşünme kipi kapalı. Deneme turuyla aynı üretim ayarları: `temperature 0.2`, `top_p 0.95`, `top_k 64`, `seed 42`, en fazla 1.500 yeni token.

### 4.1 Deneme koşusu 1 (23.10.2026): Transformers + Unsloth

- **Kurulum:**
  - Unsloth 2026.10.7, Transformers 5.16.1, Torch 2.11, tek T4.
  - Model `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit`.
  - Varyant başına 2 istem.
- **Çıktılar:** `gpu/outputs/smoke_2026-10-23_transformers/`. Kullanıcı yükleyemediği için elle aktardı; kayıtlar günlükten yeniden kuruldu.
- **Sonuç:** Hat uçtan uca çalışıyor, ama tam koşu için çok yavaş.

| Ölçüm | Değer |
|---|---|
| Model yükleme | 81 s |
| GPU belleği, yüklemeden sonra | 11,3 / 15,6 GB |
| Parametreler | 4,60 Mrd. float16 + 1,67 Mrd. uint8 (4-bit katmanlar) |
| Parti boyutu | 8 → 4 → 2 → 1 (her adımda bellek yetmedi) |
| Hız | ~5 token/s; istem başına 116–169 s |
| Tam koşu tahmini | 1.440 istem × ~150 s ≈ **60 saat** (oturum en fazla 12 saat, haftalık kota ~30 saat) |

**Neden yavaş (tahmin, ölçülmedi):**
- **Bellek:** Belleğin ~9 GB'ı float16 parametreler. Bunlar 4-bit'e çevrilmiyor; çoğu büyük olasılıkla Gemma 4'ün gömme tabloları (katman başına gömmeler dahil) ve görüntü/ses kodlayıcıları. Kalan bellek 3–5 bin token'lık ikinci bir isteme yetmiyor.
- **Hesaplama:** Unsloth, T4'te Gemma 4 için float32'ye geçiyor („Using float16 precision for gemma4 won't work! Using float32.“). T4'ün float32 hızı float16'nın kabaca sekizde biri.
- **Karşılaştırma:** Deneme turunda Gemma, kullanıcının dizüstünde büyük ölçüde işlemcide 4,3 token/s üretmişti (`trial/results.md`). T4'teki 5 token/s neredeyse aynı. Sorun GPU'da değil, çalıştırma yolunda.

### 4.2 Çıkarım Ollama ile [ÖNERİ, 23.10.2026]

- **Değişiklik:** Baseline Ollama (llama.cpp) ile çalışır, model `gemma4:e4b-it-q4_K_M`. İnce ayarlı modellerin değerlendirmesi de aynı yoldan yapılır. 22.10'daki „Unsloth + Transformers 4-bit“ önerisinin yerini alır.
- **Gerekçe:**
  1. **Hız:** llama.cpp gömme tablolarını işlemcide tutar ve GPU'da nicemli çekirdeklerle çalışır. T4'te istem başına birkaç on saniye bekleniyor; deneme koşusu 2 ölçecek.
  2. **Karşılaştırılabilirlik:** Model, nicemleme ve ayarlar deneme turuyla aynı (`docs/08`).
  3. **Demo:** Dizüstündeki demo da Ollama ile çalışacak. Değerlendirilen model ile gösterilen model aynı biçimde olur.
- **Düzen:**
  - Her T4'e bir Ollama sunucusu; sunucu başına aynı anda 4 istem.
  - Süre sınırı 11 saat; sonra çıktılar paketlenir.
  - Kaldığı yerden devam: aynı oturumda ya da önceki sürümün çıktısı Input olarak eklenince.
  - Çıktılar tek dosyada: `ergebnisse_<MODE>.zip`.
- **Kayıtta ayrıca:** model özeti (digest), Ollama sürümü, `done_reason` (1.500 token sınırına takıldı mı), düşünme metni uzunluğu, istem ve üretim süreleri.
- **Doğrulama:** Sahte bir Ollama sunucusuyla denendi. Denenenler:
  - deneme kipi;
  - hatadan sonra yeniden deneme;
  - süre sınırında durma;
  - önceki sürümün çıktısından devam (yinelenen kayıt yok);
  - zip.
- **İnce ayarlı modeller için sonuç (paket 7):**
  - LoRA ağırlıkları eğitimden sonra GGUF'a aktarılır (Unsloth `save_pretrained_gguf`, Q4_K_M) ve aynı düzende çalıştırılır.
  - Açık teknik nokta: bağdaştırıcı (adapter) aynı Ollama tabanına mı eklenecek, yoksa birleştirilmiş model mi yeniden nicemlenecek. Taban dönüşümü farklı olursa baseline aynı yoldan bir kez daha koşulur (birkaç saat).
- **Açık risk, eğitim hızı:**
  - Eğitim yine Unsloth ile T4'te yapılacak; float32 hesaplama eğitimi de yavaşlatabilir.
  - İnce ayar defterinde önce kısa bir hız ölçümü yapılır.
  - Çok yavaşsa donanım (tur 7) ya da model (tur 9) kararı yeniden kullanıcıya sorulur.

Kaynaklar: [Unsloth — Gemma 4 Fine-tuning Guide](https://unsloth.ai/docs/models/gemma-4/train) (VRAM, GGUF'a aktarma) · [Unsloth — Saving to Ollama](https://unsloth.ai/docs/basics/inference-and-deployment/saving-to-ollama) · [Ollama kurulum betiği](https://ollama.com/install.sh) (zstd gerekiyor)

### 4.3 Dört baseline metninin ilk okuması (deneme koşusu 1)

Bu metinler Transformers yolundan geldi; asıl baseline Ollama ile yeniden üretilecek. Yalnızca ilk izlenim için:

| Metin | Format | Rakam: değer doğru | Rakam biçimi | İşaretsiz neden | Kelime |
|---|---|---:|---|---:|---:|
| `ohne_kontext` 2025-01 | ✓ | 31/31 | ✓ | 0 | 136 |
| `ohne_kontext` 2025-02 | ✓ | 41/41 | binlik ayırıcı boşluk | 0 | 152 |
| `rag_k8` 2025-01 | ✓ | 44/44 | ✓ | 2 | 183 |
| `rag_k8` 2025-02 | ✗ (5 sütunlu tablo satırı) | 38/38 | binlik ayırıcı boşluk | 0 | 155 |

- **Rakam biçimi:**
  - İki metinde binlik ayırıcı boşluk („14 054 €“). İstem kuralı „886.365 €“.
  - Doğrulama bu rakamları iki ayrı sayı olarak okuyor (rakam sadakati 0,18 ve 0,24). Boşluklar noktaya çevrilince bütün değerler FACTS'le aynı.
  - Puanlamada biçim hatası değer hatasından ayrı sayılmalı (paket 8).
- **Okumada görülenler:**
  - **Ara toplamlar:** Anlamlı olmayan ara toplamlar ve sonuç satırları tabloda (Gesamtleistung, Rohertrag, Ergebnis vor Steuern, Vorläufiges Ergebnis). Bütün satırlarda „Ursache offen“; son sütun „–>“.
  - **Yön ve mantık hataları:**
    - Betriebsergebnis Vorjahr'a göre 29.532 € düşmüşken „verbesserte sich signifikant im Vergleich zum Vorjahresmonat“.
    - Materialquote'nin artışı „deutliche Verbesserung“ deniyor.
    - „Noch nicht das Normalniveau von -61 721 €“ deniyor, oysa 14.054 € bu seviyenin zaten üstünde.
  - **Yanlış kaynak:**
    - `rag_k8`, Personalkosten artışını (+%14,2) [Quelle: Kontextnotiz 2024-02] ile açıklıyor. O not geçen yılki bir personel azaltımı.
    - Ayın asıl notu (Kontextnotiz 2025-02, Sonderauftrag) hiç kullanılmamış.
  - **İşaretsiz neden:** „primär auf den Rückgang der Gesamtleistung … zurückzuführen“, „Tendenz zu geringeren Verkaufspreisen“.
  - **Uzunluk:** Metinler kısa (136–183 kelime; hedef 250–350). Sorular genel.
  - **Olumlu:** Dört başlık var. Layer 1'in V1 ve V2 bayrakları uyarı olarak anılıyor. 2025-02'deki V6 (sezon) bayrağı iki metinde de eksik.
- **Yorum:** Bunlar beklenen baseline zayıflıkları ve ablation için iyi kanıt (CLAUDE.md 7): biçim tutarsız, olgu ile tahmin karışık, bağlam notu yanlış kullanılıyor. Ama yalnızca 4 metin var; sonuç tam koşudan sonra.

### 4.4 Deneme koşusu 2 (23.10.2026): Ollama

- **Kurulum:** Ollama 0.40.9, iki T4, sunucu başına 4 eşzamanlı istem, varyant başına 8 istem (A1-v00, 2025-01 … 08).
- **Çıktılar:** `gpu/outputs/smoke_2026-10-23_ollama/` (Ollama günlükleri dahil).
- **Hazırlık:** Kurulum + model indirme (6,6 GB) ~1 dakika; ilk GPU'ya yükleme 2 dakika, ikincisi 8 saniye. GPU başına ~5,7 GB bellek; model tamamen GPU'da.
- **Tutarlılık:** Aynı istemlerin token sayısı Transformers koşusundakiyle birebir aynı (ör. 3.218 ve 5.033). Şablon ve tokenizer aynı.
- **Hata:** Hiç yok. 1.500 token sınırına takılan ya da düşünme metni üreten istem yok.

| Ölçüm | Deneme koşusu 1 (Transformers) | Deneme koşusu 2 (Ollama) |
|---|---|---|
| Akış başına hız | ~5 token/s | 37–52 token/s |
| Aynı anda işlenen istem | 1 | 8 (2 GPU × 4) |
| İstem başına süre (medyan) | ~150 s | 46 s (`ohne_kontext`, soğuk başlangıç dahil) / 21 s (`rag_k8`) |
| Saatte istem | ~24 | 593 / 1.250 |
| Tam koşu, 2 varyant | ~60 saat | **~1,8 saat** |

`ohne_kontext`'in daha yavaş görünmesi büyük olasılıkla soğuk başlangıçtan: ilk isteklerde istem okuma 27 s, sonrakilerde 3–4 s. Üç varyantlı tam koşu için tahmin 2–3 saat, tek oturuma sığıyor.

**İlk ölçüm (16 metin, doğrulama katmanı; paket 9'un ön izlemesi):**

| | `ohne_kontext` (8) | `rag_k8` (8) |
|---|---:|---:|
| Format uyumu | 7/8 | 6/8 |
| Rakam değeri doğru (boşluklar noktaya çevrilince) | 281/291 (%97) | 247/256 (%96) |
| Binlik ayırıcı boşluk olan metin | 4/8 | 3/8 |
| Kelime, tablo hariç (ortalama; hedef 250–350) | 169 | 152 |
| Neden cümlesi: kaynaklı / „(Hypothese)“ / işaretsiz | 0 / 0 / 2 | 12 / 0 / 2 |
| Eksik bayrak uyarısı (`flag_fehlt`) | 3 | 7 |
| Kaynak biçimi hatası (`quellenformat`) | 0 | 9 |

**Okumada görülenler (`rag_k8`):**
- **Kaynak biçimi:** `[Firmenprofil]`, „[Quelle: V4]“. Kural `[Quelle: <not kimliği>]`; bayraklar kaynak değil.
- **Uygun olmayan kaynak:** V1 uyarısı (sigortanın tahakkuk edilmemesi) Firmenprofil'e dayandırılıyor.
- **Yanlış ad ve yön:** „Kostenquote von 40,6 % im Vergleich zum Vorjahresmonat (45,0 %) gestiegen“. Bu değerler Personalkostenquote'ye ait ve oran 4,4 puan düşmüş.
- **Hipotez yok:** Model kaynağı olmayan nedenlerde „(Hypothese)“ hiç kullanmıyor. Ya kaynak gösteriyor (bazen yanlış) ya da işaretsiz bırakıyor.
- **Not kullanımı:** RAG'li metinler notları gerçekten kullanıyor (8 metinde 12 kaynaklı neden). Kaynakların doğruluğu ground truth ile paket 9'da ölçülecek.

**Yorum:** Bu metinler, ince ayarın neyi düzeltmesi gerektiğini somut olarak gösteriyor:
- biçim (rakam, kaynak);
- hipotez işareti;
- bayrakların eksiksiz uyarıya çevrilmesi;
- uzunluk.

## 5. Sıradaki

1. **Kullanıcı:** Kaggle'da tam koşu, `MODE = "full"`, üç varyant, ~2–3 saat (`gpu/README.md`, Bölüm 4).
2. **Asistan:**
   - Baseline çıktılarının puanlanması (doğrulama katmanı + ground truth metrikleri, paket 9). Rakam biçimi ayrı sayılır.
   - İnce ayar defteri (paket 7); önce kısa hız ölçümü.
