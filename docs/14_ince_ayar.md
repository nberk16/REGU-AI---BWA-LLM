# 14 — İnce ayar (LoRA) ve ince ayarlı modellerin değerlendirmesi

> **Durum (24.10.2026):**
> - İki Kaggle defteri hazır: `gpu/02_finetune.ipynb` (eğitim) ve `gpu/03_eval.ipynb` (test kümesinin üretimi).
> - GPU gerektirmeyen bütün parçalar yerelde denendi: şablon, veri, bağdaştırıcının GGUF'a çevrilmesi, llama-server'da LoRA ile üretim, puanlama.
> - Kaggle deneme koşusu 3 (24.10.2026): eğitim çalışıyor. En yüksek bellek 11,6 GB; hız 140 token/s; tahmini süre `rag` ~10 saat, `ohne` ~7,6 saat (Bölüm 2).
> - Tam eğitimler tamamlandı (25.10.2026; Bölüm 2.1–2.2).
> - `03_eval` deneme koşusu (26.10.2026): 5 × 8 metin, hata yok. İnce ayarlı modellerde format %100. RAG + FT'nin zayıf noktası: notu yanlış satıra bağlamak (Bölüm 4.1).
> - **[ÖNERİ]:** hiperparametreler, çıkarım yolu (bu belge).
>
> **İlgili:** CLAUDE.md 6.2 (Katman 3), 7, 10 · `12_egitim_verisi.md` (eğitim verisi) · `13_degerlendirme.md` (puanlama) · Kullanıcı adımları: `gpu/README.md`, Bölüm 6–7 · Karar kaydı: `00`, Bölüm 23

---

## 1. İki model [KARAR, tur 12]

| Model | Eğitim verisi | Örnek | Token (toplam / en uzun) | Değerlendirmedeki varyantlar |
|---|---|---:|---:|---|
| **RAG + FT** (`ft_rag`) | `train_rag`: istem `rag_k8` + ideal metin | 898 | 4,80 Mio. / 7.076 | `rag_k8` (hedef), `ohne_kontext` (ek satır), `rag_alle` (retrieval) |
| **Yalnızca FT** (`ft_ohne`) | `train_ohne`: bağlamsız istem + bağlamsız ideal metin | 933 | 3,62 Mio. / 5.011 | `ohne_kontext` |

Yanıt (ideal metin) ortalama ~830 token. Kayıp yalnızca bu kısımda hesaplanır (Bölüm 2).

## 2. Eğitim (`gpu/02_finetune.ipynb`) [ÖNERİ]

| Ayar | Değer | Gerekçe |
|---|---|---|
| Taban | `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` (QLoRA) | Deneme koşusu 1'de T4'te yüklendi; 4-bit taban T4'e sığıyor |
| LoRA | r 16, alpha 16, dropout 0; yalnızca dil katmanları: q, k, v, o, gate, up, down | Unsloth Gemma 4 kılavuzu; görüntü/ses katmanları eğitilmez |
| Öğrenme oranı | 2e-4, doğrusal azalma, %5 ısınma | Kılavuzdaki değer |
| Epoch / etkin parti | 1 / 8 (1 × 8 birikim) | `rag` ~113, `ohne` ~117 adım |
| Optimizer | AdamW 8-bit, weight decay 0,01 | Bellek |
| En uzun dizi | 7.168 token | En uzun örnek 7.076; hiçbir örnek kesilmez |
| Kayıp | Yalnızca model turu (`train_on_responses_only`, `<\|turn>user\n` / `<\|turn>model\n`) | Model istemi değil yanıtı öğrenir |

**Denetimler (defterin içinde, eğitimden önce):**
- **Şablon:** Test istemlerinin token sayısı baseline'daki Ollama sayımıyla aynı olmalı (5.033 ve 3.218). Eğitim, baseline ve değerlendirme aynı biçimi görür. Yerelde doğrulandı: HF şablonu, llama-server ve Ollama aynı token kimliklerini veriyor.
- **İstem öneki:** Her örnekte üretim istemi, eğitim metninin önekidir.
- **Maske:** Kayıp hesaplanan tokenlar ideal metinle başlamalı; BOS bir kez. Değilse defter eğitime başlamaz.
- **BOS (deneme koşusu 1, 24.10.2026):**
  - Unsloth kılavuzu, BOS'u tokenizer'ın ekleyeceğini varsayıp metinden silmeyi öneriyor. Gemma 4 tokenizer'ı ise BOS eklemiyor.
  - Maske denetimi bunu yakaladı: en uzun örnek 7.076 yerine 7.075 token. Eğitim başlamadı.
  - Düzeltme: metin BOS'la verilir. Tokenizer yine de eklerse metindeki silinir. Her iki durumda dizi tam bir BOS ile başlar; kullanımdaki biçimle aynı.
- **Doğrulama kaybı:** Eğitim öncesi ve sonrası, aynı tanımla (yalnızca yanıt tokenları), `val` kümesinden 32 örnek.

**Kipler:**
- **`smoke`:** En uzun 12 örnekle 3 adım. Bellekte en kötü durum. Ölçülenler:
  - token/s;
  - en yüksek GPU belleği;
  - iki modelin 1 epoch süre tahmini;
  - GGUF ve llama-server hattının tamamı.
- **`full`:**
  - 1 epoch; her 10 adımda checkpoint.
  - 10 saatte durur. Bu sürümün çıktısı Input olarak eklenince aynı ayarlarla kaldığı yerden devam eder.
  - Diğer modelin bağdaştırıcısı önceki çıktıdan taşınır. Böylece son sürümün çıktısında iki bağdaştırıcı birlikte bulunur.

**Bellek (deneme koşusu 2, 24.10.2026):**
- Denetimler geçti; eğitim öncesi doğrulama kaybı 0,786 (4 örnek). Eğitimin ilk adımı, 7.076 tokenlık örnekte bellek yetmediği için durdu (14,4 / 14,6 GB).
- Modeli yükledikten sonra GPU'da 11,3 GB vardı. Bunun büyük kısmı eğitimde kullanılmayan parçalar:

| Parça | Parametre | float16 |
|---|---:|---:|
| Dil katmanları (4-bit) | 3,95 Mrd. | ~2 GB (4-bit) |
| Katman başına gömme tablosu (`embed_tokens_per_layer`) | 2,82 Mrd. | 5,64 GB |
| Ana gömme tablosu | 0,67 Mrd. | 1,34 GB |
| Ses ve görüntü kodlayıcıları | ~0,47 Mrd. | ~0,95 GB |

- **Düzeltme:**
  - Katman başına gömme tablosu işlemciye taşınır. Bu tablo yalnızca bir aramadır: her token için bir satır okunur, sonuç GPU'ya taşınır. Tablo donmuş, eğitilmez.
  - Ses ve görüntü kodlayıcıları da işlemciye taşınır.
  - Beklenen kazanç ~6,5 GB.
  - Küçük bir Gemma 4 modelinde (PEFT ile sarılmış) denendi: kayıp birebir aynı, LoRA gradyanları hesaplanıyor, `model.to(...)` tabloyu geri taşımıyor.
- **Güvenlik ağı:** Deneme koşusunda bellek yine yetmezse, hız 6.000 tokenın altındaki örneklerle ölçülür. Günlükte bellek sınırı da kaydedilir. `train_rag`'de 115 örnek (%13) bu sınırın üstünde; `train_ohne`'de hiçbiri.

**Deneme koşusu 3 (24.10.2026): eğitim çalışıyor.** Günlük: `gpu/outputs/finetune_smoke_2026-10-24/log_smoke_rag_3.txt`.

| Ölçüm | Değer |
|---|---|
| GPU belleği: yükleme sonrası / taşıma sonrası / eğitimde en yüksek | 11,3 / 4,8 / **11,6 GB** (en uzun örnek 7.076 token; sığıyor) |
| Hız | **140 token/s** (en uzun örneklerle), 4 örneklik adım 197 s |
| Tahmini 1 epoch | **`rag` ~10 saat, `ohne` ~7,6 saat**. Ölçüm en uzun örneklerle yapıldı; ortalama örnek daha kısa, gerçek süre biraz daha az olmalı |
| Doğrulama kaybı (4 örnek) | 0,786 → 0,635 (yalnızca 3 adım sonra) |
| Bağdaştırıcı | 516 tensör, GGUF 70 MB; anahtar adları beklenen biçimde (`base_model.model.model.language_model.layers.…`) |

- **llama-server denemesi „GPU'yu kullanmıyor“ hatası verdi. Bu yanlış alarm:**
  - Denetim, sunucu günlüğünde „CUDA“ kelimesini arıyordu.
  - llama-server varsayılan ayarda kullandığı donanımı günlüğe yazmıyor (yerelde doğrulandı; Ollama bunu daha ayrıntılı günlük ayarıyla görüyordu).
- **Düzeltme:** Sunucu iki şekilde denetleniyor:
  - başlamadan önce `--list-devices` ile CUDA cihazının görünmesi;
  - başladıktan sonra o GPU'da belleğin en az 2 GB artması (nvidia-smi).

  Bulamazsa, CUDA arka ucu ikinci bir yolla aranıyor (`GGML_BACKEND_PATH`). Hata olursa sunucu günlüğünün sonu ana günlüğe yazılıyor. Bu kod 02 ve 03'te ortak (`gpu/tools/nbbuild.py`).
- **Süre sınırı:** 10,5 saat. Oturum 12 saat; sonrasında doğrulama kaybı, GGUF ve deneme için ~30 dakika kalıyor. `rag` bu sınıra yakın; aşarsa ikinci bir kısa oturumda checkpoint'ten devam edilir.

**Hız ve bellek: çözüldü (deneme koşusu 3).**
- Bellek sığıyor.
- Hız Kaggle'ın haftalık kotasıyla uyumlu:
  - iki eğitim ~17–18 saat;
  - değerlendirme ~4–5 saat;
  - haftalık kota ~30 saat.
- Açık soru: `rag` eğitiminin 10,5 saatlik sınıra sığıp sığmadığı. Sığmazsa devam koşusu gerekir.

### 2.1 Tam eğitim: RAG + FT (24–25.10.2026)

Günlük ve kayıtlar: `gpu/outputs/finetune_rag_2026-10-25/` (`log_full_rag.txt`, `train_history_rag.json`, `run_info_rag.json`, `check_rag.json`).

| Ölçüm | Değer |
|---|---|
| Adım | 113/113 (1 epoch, 898 örnek); 468 dk (~7,8 saat), adım başına ~4,1 dk |
| En yüksek GPU belleği | 11,6 GB |
| Eğitim kaybı (ortalama) | adım 1–10: 0,75 · 11–30: 0,36 · 31–60: 0,19 · 61–90: 0,16 · 91–113: 0,15 |
| **Doğrulama kaybı (32 örnek, yalnızca yanıt)** | **0,834 → 0,130** |
| Bağdaştırıcı | 516 tensör, GGUF 70 MB (`sha256 d9a9720b…`) |
| llama-server (GPU 1) | CUDA0 görüldü, bellek 0 → 3.739 MiB; yeni denetim çalışıyor |

- **Ezber yok:** Son adımlardaki eğitim kaybı (~0,13–0,15) doğrulama kaybına (0,130) yakın. 1 epoch'ta her örnek bir kez görüldü.
- **Deneme üretimi** (`A2-v120_2025-01`, doğrulama kümesi; aynı istem, aynı ayarlar). Puanlama 1.0 ile:

| | Taban (ölçek 0) | **İnce ayarlı (ölçek 1)** | İdeal metin |
|---|---|---|---|
| Format uyumu | ✗ (13 boşluklu rakam, kaynak biçimi) | ✓ | ✓ |
| Kelime | 186 | 315 | 290 |
| Rakam: değeri doğru | 24/24 | 48/50 | 44/44 |
| Neden: kaynaklı / hipotez / işaretsiz | 2 / 0 / 0 | 1 / 3 / 0 | 1 / 4 / 0 |
| Kaynak: doğru / plandaki | 1/2 (bir atıf yanlış) | 1/2 (yanlış yok, biri eksik) | 2/2 |
| Uyarılar (Katman 1 bayrakları) | 2/2 | 2/2 | 2/2 |
| V2 adayı (uyarı gerekiyordu) | ✗ uyarmadı | ✓ | ✓ |

- **İnce ayarlı metindeki iki rakam hatası:**
  - Betriebsergebnis 117.851 € yerine „118.051 €“ (kopyalama hatası).
  - Versicherungen/Beiträge için kendi hesapladığı „+760 €“ fark.
  - İkisini de doğrulama katmanı yakalıyor (`zahl_unbelegt`). Katman 4'ün gerekçesi bu: model kuralları öğrense de rakam hatası tamamen bitmiyor.
- Tek örnek; asıl karşılaştırma 03_eval ile test kümesinde yapılacak.

### 2.2 Tam eğitim: yalnızca FT (25.10.2026)

Günlük ve kayıtlar: `gpu/outputs/finetune_ohne_2026-10-25/`. Önceki sürümün çıktısından `adapter_rag` taşındı. 02'nin son sürümünün çıktısında iki bağdaştırıcı birlikte var.

| Ölçüm | Değer |
|---|---|
| Adım | 117/117 (1 epoch, 933 örnek); 333 dk (~5,6 saat), adım başına ~2,8 dk |
| En yüksek GPU belleği | 9,8 GB (en uzun örnek 5.011 token) |
| Eğitim kaybı (ortalama) | adım 1–10: 0,87 · 11–30: 0,39 · 31–60: 0,18 · 61–90: 0,14 · 91–117: 0,12 |
| **Doğrulama kaybı (32 örnek)** | **1,013 → 0,106** |
| Bağdaştırıcı | 516 tensör, GGUF 70 MB (`sha256 37090a00…`) |

**Deneme üretimi** (`A2-v120_2025-01`, bağlamsız istem):

| | Taban | **Yalnızca FT** | İdeal metin |
|---|---|---|---|
| Format uyumu | ✗ (26 boşluklu rakam) | ✓ | ✓ |
| Doğrulama hatası | 26 | **0** | 0 |
| Kelime | 192 | 294 | 281 |
| Neden: hipotez / işaretsiz | 0 / 0 | 3 / 0 | 3 / 0 |
| Gereksiz tablo satırı | 5 | 0 | 0 |
| Uyarılar (Katman 1) / V2 | 2/2 / ✗ | 2/2 / ✓ | 2/2 / ✓ |

**Okuma:**
- Bağlamsız model kaynak göstermiyor; uydurma kaynak da yok.
- Nedenleri „(Hypothese)“ ile işaretliyor. İdeal metinle aynı profil.
- Eğitim öncesi kayıp RAG modelinden yüksekti (1,01'e karşı 0,83). Bağlamsız hedef metinler taban model için daha alışılmadık; eğitimden sonra ikisi de ~0,1.

## 3. Çıkarım yolu: llama-server + LoRA [ÖNERİ]

**Bulgu (yerelde, 24.10.2026):** Ollama 0.40.10, `ADAPTER` satırlı bir Modelfile'ı „LoRA adapters are no longer supported“ hatasıyla reddediyor. Önceki plan (bağdaştırıcıyı Ollama'ya eklemek) bu yüzden çalışmıyor.

**Çözüm:** Ollama 0.40 modelleri kendi içindeki **llama-server** ile çalıştırıyor (baseline günlüğünde komut satırı görülüyor). Bu sunucu doğrudan başlatılır:

```
llama-server --model <baseline'daki model dosyası> --lora adapter_rag.gguf,adapter_ohne.gguf --lora-init-without-apply
             -c 49152 -np 4 --flash-attn auto -b 1024 -ub 1024 --spec-type draft-mtp … (baseline'daki ayarlar)
POST /completion {"prompt": <Gemma 4 şablonuyla yazılmış istem>, "lora": [{"id": 0, "scale": 1}, {"id": 1, "scale": 0}], …}
```

**Yerelde denendi:**

| Kontrol | Sonuç |
|---|---|
| Bağdaştırıcı → GGUF (`convert_lora_to_gguf.py`, llama.cpp `3f03b17`) | Gemma 4'ün gerçek katman boyutlarıyla 516 tensör (42 katman; KV paylaşan 18 katmanda k/v yok) |
| llama-server bağdaştırıcıyı yüklüyor ve istek başına uyguluyor | Ölçek 0 → taban modelin çıktısı; yüksek ölçek → değişen çıktı |
| Taslak model (hızlandırma) ile birlikte | Çalışıyor |
| İstem token kimlikleri | HF şablonu = llama-server = Ollama (5.033 ve 4.935 token örnekleri) |
| BOS | İstem `<bos>` olmadan gönderilir; sunucu kendisi ekler (aksi hâlde iki BOS) |
| Örnekleme | Baseline günlüğündeki ayarlarla aynı: `top_k 64`, `top_p 0.95`, `min_p 0`, `temp 0.2`, `repeat_penalty 1.0` |
| 02 ve 03 defterlerinin GPU gerektirmeyen hücreleri | Sahte bağdaştırıcıyla uçtan uca çalıştı; puanlama çıktıları okuyor |

**Neden temiz bir karşılaştırma:**
- Taban model dosyası, örnekleme ayarları ve şablon baseline ile aynı.
- Değişen tek şey bağdaştırıcı.
- Tutarlılık kontrolü olarak taban model de aynı yoldan bir kez daha koşulur (`base_rag_k8`). Sonuçları Ollama baseline'ıyla aynı aralıkta olmalı.

**Demo için sonuç:** Ollama bağdaştırıcı yükleyemediği için dizüstündeki demo da llama-server (llama.cpp) ile yapılmalı. Diğer seçenek, bağdaştırıcının modele birleştirilip yeniden nicemlenmesi. Karar demo aşamasında verilecek (paket 10).

## 4. Değerlendirme (`gpu/03_eval.ipynb`)

| Sistem · varyant | Satır (CLAUDE.md 7) |
|---|---|
| `ft_rag` · `rag_k8` | RAG + FT |
| `ft_ohne` · `ohne_kontext` | Yalnızca FT |
| `ft_rag` · `ohne_kontext` | RAG + FT, bağlamsız (ek satır) |
| `ft_rag` · `rag_alle` | RAG + FT, bütün notlar |
| `base` · `rag_k8` | Tutarlılık kontrolü |

- **Ayarlar:** Her T4'e bir sunucu, sunucu başına 4 eşzamanlı istem.
- **Süre sınırı ve devam:** 01'deki gibi.
- **Tam koşu bağdaştırıcıları:** Yalnızca `full` kipte tamamlanmış bağdaştırıcılar kullanılır (`run_info_*.json`).
- **Puanlama:** `python -m scoring <klasör>`. Baseline ile aynı tabloya şu satırlar eklenir:
  - Çıplak model (`baseline_ohne_kontext`)
  - Yalnızca RAG (`baseline_rag_k8`)
  - Yalnızca FT (`ft_ohne_ohne_kontext`)
  - RAG + FT (`ft_rag_rag_k8`)
  - Ek satırlar

### 4.1 Deneme koşusu (26.10.2026)

**Dosyalar:** `gpu/outputs/eval_smoke_2026-10-26/` (5 × 8 metin, log, sunucu logları, `scores.md`). İstemler: test kümesinin ilk 8 ayı (A1-v00, 2025-01 … 2025-08), yani yalnızca **yeni sektör**.

**Mekanik: her şey beklendiği gibi.**
- **Bağdaştırıcılar:** İkisi de `full`, tamamlanmış (`rag` 113/113 adım, sha `d9a9720b…`; `ohne` 117/117, sha `37090a00…`).
- **Şablon:** Token sayıları baseline ile aynı (5033, 3218).
- **GPU:** İki sunucu da CUDA'da (`CUDA0: Tesla T4`). Sunucu başına bellek ~4,7 GB: taban model, taslak model, iki bağdaştırıcı ve 4 × 12.288 bağlam.
- **Koşular:** 40 metin, hata 0. Sınıra takılan çıktı 0, düşünme metni 0.
- **Taslak (MTP) kabulü:** %51–73.
- **Hız:** Ilk koşunun ilk istemleri ~50 saniyelik bir ısınma içeriyor (ilk istem işleme). Sonraki koşular sistem başına 700–950 istem/saat (2 sunucu × 4 eşzamanlı).
- **Tam koşu tahmini:** 5 × 720 istem, ~4,5 saat. Log'daki „~5,7 saat“ ısınmayı da hıza kattığı için karamsar.

**Motor tutarlılığı (`base_rag_k8`).** Taban model llama-server'da, aynı istemlerle:
- İstem token sayıları Ollama baseline'ıyla aynı.
- Metinler 50–260 karakterden sonra ayrışıyor. Örnekleme iki motorda farklı uygulanıyor; sıcaklık 0,2'de bu beklenen bir durum.
- Ölçütler aynı aralıkta (aynı 8 ay): format %38 / %38, hatasız %12 / %12, rakam %96 / %96, kelime 159 / 152.
- Tam koşuda 720 ay üzerinden yeniden karşılaştırılacak.

**Puanlar** (puanlama 1.1, doğrulama v1.8; 8 ay, A1). Baseline sütunları aynı 8 ayın Ollama çıktıları.

| Ölçüt | Çıplak model | Yalnızca RAG | Yalnızca FT | RAG + FT | RAG + FT bağlamsız | RAG + FT bütün notlar |
|---|---:|---:|---:|---:|---:|---:|
| Format uyumu | %38 | %38 | %100 | %100 | %100 | %100 |
| Hatasız metin | %12 | %12 | %100 | %75 | %62 | %50 |
| Rakam sadakati (değer) | %97 | %96 | %100 | %98 | %99 | %99 |
| Kelime (ort.) | 168 | 152 | 248 | 221 | 227 | 212 |
| Neden / metin | 0,25 | 1,75 | 1,75 | 4,0 | 2,1 | 4,9 |
| … kaynaklı / hipotez / işaretsiz | %0 / %0 / %100 | %86 / %0 / %14 | %0 / %100 / %0 | %69 / %28 / %3 | %0 / %94 / %6 | %67 / %23 / %10 |
| Kaynak precision / recall | – | %88 / %27 | – | %81 / %50 | – | %90 / %64 |
| Tablo atıfı doğru satırda | – | %62 | – | %69 | – | %84 |
| Yanlış satıra atıf (metin payı) | %0 | %12 | %0 | %38 | %0 | %38 |
| Uydurma kaynak (metin payı) | %0 | %0 | %0 | %0 | %0 | %12 |
| Gereksiz tablo satırı / metin | 5,4 | 4,1 | 0 | 0 | 0 | 0 |
| Uyarı kapsamı (Katman 1) | %80 | %53 | %100 | %100 | %100 | %100 |
| Uyarı recall / precision (ground truth) | %73 / %85 | %60 / %90 | %80 / %81 | %80 / %81 | %80 / %81 | %80 / %81 |

**Okuma (8 ay; yön gösterir, kanıt değil).**
1. **Yapı tamamen öğrenildi.** Bütün ince ayarlı sistemlerde:
   - format %100;
   - gereksiz satır yok;
   - binlik ayırıcı doğru;
   - uzunluk hedefe yakın;
   - Katman 1 bayraklarının hepsi Hinweise'de.

   Bu, eğitimde görülmeyen sektörde (A1) ve eğitimde görülmeyen girdilerde (bağlamsız, bütün notlar) de geçerli.
2. **Yalnızca FT:** 8 metnin hepsi hatasız. Nedenlerin hepsi „(Hypothese)“ ya da açık soru. Not olmadığı için atıf yok; beklenen davranış.
3. **RAG + FT'nin zayıf noktası: notu yanlış satıra bağlamak.**
   - 2025-04: „Sonderauftrag“ notu, „Sonstiger neutraler Ertrag“ ve „Sonstige Kosten“ satırlarının nedeni olarak gösterilmiş. Planda bu satırlar „offen“ ve „Hypothese“.
   - 2025-02: Haziran 2024 fuarı notu, Şubat'taki reklam gideri farkının nedeni olarak gösterilmiş.
   - Not düzeyindeki kaynak isabeti bunu görmüyordu, çünkü atıf yapılan not o ay başka bir satır için doğru kaynak. Puanlama 1.1'deki satır düzeyi ölçüt bunun için eklendi (`docs/13`, Bölüm 2).
4. **Diğer RAG + FT hataları:**
   - Umsatzerlöse değerini Gesamtleistung'tan çıkarmış. Sayı doğru, ama facts'te o satır için yok (`zahl_falsche_position`).
   - Bir kez „[Hypothese]“ köşeli parantezle yazılmış.
   - Bir cümlede yön hatası var: „237.140 € … deutlich über dem Vormonatswert von 428.567 €“. Bu hatayı doğrulama yakalamıyor (`docs/13`, Bölüm 5).
5. **RAG + FT bağlamsız:**
   - Model kendi hesapladığı rakamlar üretiyor (+32.583 €, +1.120 %).
   - İşaret hataları yapıyor.
   - Bu, yalnızca FT modelinin ayrı eğitilmesi kararını (tur 12) destekliyor.
6. **RAG + FT bütün notlarla:**
   - Kaynak recall en yüksek (%64).
   - Bir metinde bayrak kodu kaynak gibi gösterilmiş („[Quelle: Hinweis V4]“).
   - Eğitimde yalnızca top-8 görüldü; daha uzun not listesi dağılım dışı.
7. **Doğrulama düzeltmesi (v1.8):** „Die Gesamtleistung geht auf 743.213 € zurück“ bir düşüştür, ama „geht auf“ nedensellik kelimesi olduğu için işaretsiz neden sayılıyordu. Düzeltildi (`docs/07`, Bölüm 14). Baseline puanları değişmedi.

## 5. Sıradaki

1. ~~02'nin deneme koşusu~~ ✅ (deneme koşusu 3).
2. ~~Tam eğitimler~~ ✅ `rag` (7,8 saat; 0,834 → 0,130) ve `ohne` (5,6 saat; 1,013 → 0,106).
3. ~~`03_eval` deneme koşusu~~ ✅ (Bölüm 4.1). **Kullanıcı:** tam koşu (`MODE = "full"`, ~4,5 saat).
4. **Ablation tablosu ve okuma:** `docs/13`, Bölüm 6.
