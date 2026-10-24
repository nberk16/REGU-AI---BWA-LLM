# 14 — İnce ayar (LoRA) ve ince ayarlı modellerin değerlendirmesi

> **Durum (24.10.2026):**
> - İki Kaggle defteri hazır: `gpu/02_finetune.ipynb` (eğitim) ve `gpu/03_eval.ipynb` (test kümesinin üretimi).
> - GPU gerektirmeyen bütün parçalar yerelde denendi: şablon, veri, bağdaştırıcının GGUF'a çevrilmesi, llama-server'da LoRA ile üretim, puanlama.
> - Eğitimin kendisi (hız, bellek) Kaggle'daki deneme koşusunda ölçülecek.
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

**Açık risk: hız ve bellek.**
- Unsloth T4'te Gemma 4 için float32 hesaplamaya geçiyor (deneme koşusu 1). Model yüklenince 11,3 / 15,6 GB bellek kullanılıyordu.
- 7 bin tokenlık dizilerle eğitimin sığıp sığmadığı ve süresi deneme koşusunda ölçülecek.
- Tahmin 1 epoch için birkaç saatten 10 saatin üstüne kadar geniş bir aralıkta.
- Çok yavaş ya da bellek yetersizse kullanıcıya seçenekler sunulur:
  - en uzun örnekleri dışarıda bırakmak (ör. 6.500 token üstü, ~%3);
  - görüntü/ses katmanlarını bellekten çıkarmak;
  - daha kısa eğitim;
  - Gemma 4 E2B ya da Qwen3.5 9B (tur 9);
  - kiralık GPU (tur 7).

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

## 5. Sıradaki

1. **Kullanıcı:** 02'nin deneme koşusu (`TRAIN = "rag"`). Hız ve bellek ölçülür.
2. **Asistan:** Ölçüme göre tam eğitimin süresi. Gerekirse seçenekler (Bölüm 2, açık risk).
3. **Tam eğitimler ve değerlendirme koşusu:**
   - `rag`;
   - `ohne`;
   - `03_eval`.
4. **Ablation tablosu ve okuma:** `docs/13`, Bölüm 6.
