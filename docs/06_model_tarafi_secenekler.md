# 06 — Model tarafı: kararlar ve seçenekler

> **Durum:** **[AÇIK]** Seçenekler kullanıcıya sunuldu (tur 6); önerilerin hepsi **[ÖNERİ]**.
>
> **Tarih:** 15.10.2026 · **İlgili:** CLAUDE.md 6.2–6.3, 7, 8, 10 · `docs/yol_haritasi.md` paketleri 4–9
>
> Model bilgileri Ekim 2026 itibarıyla web aramasıyla doğrulandı; kaynaklar dosyanın sonunda. Lisansları kullanmadan önce model kartında bir kez daha kontrol etmek gerekir. Bu belge hukuki danışmanlık değildir (CLAUDE.md, talimat 5).

Kararlar birbirine bağlı. Önerilen sıra: **C (eğitim/test) → A (model) → B (ideal yorumlar) → D (bilgi tabanı)**.

---

## A. Temel model ve altyapı

### A1. Temel model

| Seçenek | Boyut | Lisans / menşe | Artı | Eksi |
|---|---|---|---|---|
| **Ministral 3 8B Instruct** | 8B | Apache 2.0, Mistral (Fransa), Aralık 2025 | AB menşeli (Mittelstand algısı, veri koruma argümanı); 256K bağlam; 3–8B sınıfına tam uyuyor | Bu görevde Almanca kalitesi henüz denenmedi |
| **Gemma 4 E4B** | ~4,5B etkin | Apache 2.0 (Nisan 2026'dan itibaren), Google | Çok küçük; "4B bile yeterli" anlatısı; düşük donanım | Küçük boyutta sayıya ve formata bağlılık riski |
| **Qwen3.5 9B** | 9B | Apache 2.0, Alibaba (Çin) | Küçük sınıfta güçlü genel performans | Alman firmalarında algı sorunu (CLAUDE.md 10) |
| EuroLLM-9B (2512) | 9B | Apache 2.0, AB projesi | 24 AB dili, Avrupa menşeli | Genel akıl yürütmede diğerlerinin gerisinde olabilir |
| Ministral 3 14B / Gemma 4 26B MoE | 14B / 26B (3,8B etkin) | Apache 2.0 | Daha yüksek kalite | 3–8B hedefinin dışında; MoE'de LoRA daha karmaşık |
| Soofi S (30B-A3B) | — | Lisans henüz kesin değil, kapalı beta | Almanca odaklı | Şu an kullanılamıyor; izleme listesi |

**Önerim:** Önce kısa bir **Almanca deneme turu** yapılsın: Ministral 3 8B, Gemma 4 E4B ve Qwen3.5 9B. Her biri ~10 `facts.json` örneğiyle, aynı istemle, sıfır atışla (zero-shot) denenir.
- Ölçütler: Almanca akıcılık, format uyumu, rakam sadakati (Katman 4'ün ilk sürümüyle), Q4 nicemlemede bellek ve hız.
- Eşitlik durumunda **Ministral 3 8B**: AB menşeli ve Apache 2.0 olması projenin "lokal ve veri korumalı" argümanını güçlendiriyor.

### A2. Fine-tuning araç seti ve donanım

| Seçenek | Açıklama |
|---|---|
| **Unsloth + TRL (QLoRA)** | Düşük bellek, hızlı; yeni modelleri hızlı destekliyor. 8B QLoRA için resmî alt sınır ~6 GB VRAM, pratikte ~8 GB. Bizim örnekler ~5–6K token olduğu için 12–16 GB daha gerçekçi. |
| Hugging Face TRL + PEFT | Standart ve şeffaf; biraz daha fazla bellek |
| Axolotl | Yapılandırma dosyasıyla eğitim; deney takibi kolay |
| MLX-LM | Apple Silicon üzerinde yerel eğitim |

**Donanım** — kullanıcıya soru: Kendi GPU'n var mı, yoksa bulut mu?
- Ücretsiz Colab/Kaggle (T4 16 GB): mümkün ama yavaş, oturum süreleri sınırlı.
- Saatlik kiralık GPU (L4 / A100 / RTX 4090 sınıfı): birkaç eğitim koşusu için en pratik yol.
- Veri sentetik olduğu için bulutta eğitim sorun değil (CLAUDE.md 10).

**Önerim:** Unsloth + TRL, QLoRA. Donanım kullanıcının imkânına göre.

### A3. Çıkarım (inference)

| Seçenek | Kullanım |
|---|---|
| **vLLM** (veya transformers) | Değerlendirmede binlerce üretimi GPU'da toplu çalıştırmak |
| **llama.cpp / Ollama** (GGUF, Q4) | Yerel demo; "lokal çalışabilirlik" argümanını göstermek |

**Önerim:** İkisi birlikte. Değerlendirme vLLM ile, portfolyo demosu llama.cpp/Ollama ile.

---

## B. İdeal yorumların üretimi (eğitim hedefleri)

### B1. Üretim yöntemi — CLAUDE.md 9, [AÇIK]

| Seçenek | Nasıl | Artı | Eksi |
|---|---|---|---|
| (a) Şablon | Kurallar `facts.json` + ground truth + notlardan metni doğrudan üretir | %100 doğru, ucuz, tekrarlanabilir | Tekdüze dil; model kalıp ezberler |
| (b) Öğretmen model | Büyük bir model metni yazar; otomatik doğrulama ve örnekleme ile elle kontrol | Doğal Almanca | Hata riski; maliyet; lisans/kullanım koşulları |
| **(c) Karma** | Kurallar bir **içerik planı** çıkarır: hangi kalemler, hangi neden kaynaklı / hipotez / uyarı, hangi açık sorular. Öğretmen model bu planı Almanca metne döker. Doğrulama, metnin plana ve rakamlara uyduğunu kontrol eder. | Doğruluk kurallardan, dil modelden gelir; "olgu / kaynaklı neden / tahmin" ayrımı garanti | Biraz daha mühendislik |
| (d) Elle yazma | Uzman gibi elle yazmak | En yüksek kalite | Yüzlerce örnek için uygun değil |

**Önerim:**
- **(c) karma.** Ek olarak elle yazılmış ya da elle düzeltilmiş **20–30 örneklik küçük bir altın küme (d)** hazırlansın; üslup değerlendirmesinde ve istem örneklerinde kullanılır.
- Doğrulama katmanı (paket 8) bu yüzden ideal yorumlardan **önce** yazılmalı.

### B2. Öğretmen model (b veya c seçilirse)

| Seçenek | Not |
|---|---|
| **Açık ağırlıklı, izin verici lisanslı büyük bir model** (ör. Mistral Large 3, Gemma 4 31B, Qwen3.5'in büyük modelleri) | Çıktıyla model eğitmek lisans açısından en temiz yol. Kiralık GPU ya da bir çıkarım sağlayıcısı gerekir. |
| Ticari bir API (ör. Claude, GPT) | Kalite yüksek, kurulum kolay. Bazı sağlayıcıların kullanım koşulları, çıktılarla başka model eğitmeyi kısıtlayabilir; kullanmadan önce koşullar okunmalı. |

**Önerim:** Açık ağırlıklı ve Apache 2.0 lisanslı bir öğretmen. Lisansını model kartında doğrulamak gerekir.

### B3. Notta geçmeyen nedenlerde hedef metin ne der?

Bu karar, "uydurma neden oranı" metriğini doğrudan etkiler.

| Seçenek | Örnek | Risk |
|---|---|---|
| **(a) Açık soru** | "Ursache aus den Unterlagen nicht ersichtlich – Rückfrage: Neueinstellungen oder Tarifeffekt?" | Yok |
| **(b) Genel hipotez, açıkça işaretli** | "Vermutlich personalbedingt (Hypothese)" | Düşük |
| (c) Ground truth'taki gerçek nedeni "vermutlich" diye vermek | "Vermutlich drei Neueinstellungen" | **Sızıntı:** Model bilemeyeceği nedenleri tahmin etmeyi öğrenir; uydurma neden metriği bozulur |

**Önerim:** (a) ve (b) birlikte; (c) hiçbir zaman.

### B4. Çıktı yapısı — CLAUDE.md 6.3, [ÖNERİ]

**Önerim:** 6.3'teki dört bölüm kalsın:
1. Kernaussagen (en fazla 3)
2. Abweichungen im Detail (tablo)
3. Hinweise auf mögliche Verzerrungen
4. Offene Fragen

Eklemeler:
- Uzunluk sınırı ~250–350 kelime.
- Tablo sütunları sabit.
- Her neden cümlesinde ya `[Quelle: …]` ya da `(Hypothese)`.
- 6.3'teki örnek, Muster GmbH'nin gerçek verisiyle yeniden yazılır.

---

## C. Eğitim/test ayrımı — CLAUDE.md 9, [AÇIK]

### C1. Test arketipi (eğitimde hiç görülmez)

| Seçenek | Artı | Eksi |
|---|---|---|
| **A1 (Muster GmbH)** | Portfolyodaki vitrin örnekleri gerçekten "hiç görülmemiş" firmadan gelir; en güçlü kanıt anlatısı. Eğitimde (A2 + A3) bütün çarpıklık türleri var (`docs/01`, 4.1). | Eğitimdeki `cite` örneği daha az (A2 + A3: 13 / 10 varyant; `train_price_boost` ile ~27) |
| A2 (toptancı) | V2 ayrımı en zor arketipte ölçülür; eğitimde `cite` örneği en çok (A1 + A3) | Muster GmbH eğitimde; vitrin örnekleri "görülmüş" firmadan |
| A3 (sezonlu üretici) | Mevsimselliğe genelleme ölçülür | Güçlü sezon eğitimde hiç görülmez; çok zor bir test |

**Önerim:** **A1.** Ek olarak eğitim arketiplerinin **görülmemiş varyantları** da test edilsin. Böylece iki genelleme düzeyi ayrı ayrı raporlanır: yeni firma, yeni sektör.

### C2. Kümeler ve varyant sayıları (A1 test seçilirse)

| Küme | Kaynak | Hacim (yorumlanabilir ay) |
|---|---|---|
| Eğitim | Yeni koşu: A2 ve A3, `--profile train_price_boost --first-variant 100 --variants 25`, ayrı seed | 2 × 25 × 24 = **1.200** |
| Doğrulama (erken durdurma, hiperparametre) | Aynı koşudan ayrılmış 3 + 3 varyant | 144 |
| Test — yeni firma (aynı sektör) | Referans koşu, A2 ve A3, v00–v09 | 480 |
| Test — yeni sektör | Referans koşu, A1, v00–v09 (Muster GmbH dahil) | 240 |
| V2 ayrımı | Dengelenmiş küme (A1 kısmı yeni sektör; A2/A3 kısmı yeni firma olarak raporlanır) | 147 |

- 1.200 eğitim örneği, 8B bir modelde LoRA için yeterli bir başlangıç.
- İdeal yorum maliyeti ve süresi bu sayıyla doğru orantılı. Gerekirse 15 varyantla (720 örnek) başlanır.

---

## D. Bilgi tabanı (Katman 2)

### D1. Embedding modeli

| Seçenek | Lisans | Not |
|---|---|---|
| **BGE-M3** | MIT | Çok dilli, 8.192 token; yoğun + seyrek (hibrit) arama. Almanca birleşik kelimelerde seyrek arama işe yarar. DACH bölgesinde RAG için yaygın tercih. |
| multilingual-e5-large | (model kartında doğrulanmalı) | Almanca soru-cevapta BGE-M3'e yakın sonuçlar bildiriliyor |
| Qwen3-Embedding (0,6B / 4B / 8B) | Apache 2.0 (bildirilen) | Güçlü, ama Almanca için bağımsız ölçüm bulamadım |
| Almanca'ya özel küçük modeller (ör. Boldt-Embed-DE-350M) | (doğrulanmalı) | Almanca FAQ/RAG'de iyi sonuç bildiriliyor; topluluk modeli |

**Önerim:** **BGE-M3.** Lisans net, Almanca desteği güçlü, hibrit arama yapabiliyor.

### D2. Vektör deposu

| Seçenek | Not |
|---|---|
| **Chroma** (gömülü) | Kurulumu kolay, meta veri filtresi var (firma, 13 aylık dönem), kalıcı |
| NumPy / FAISS (bellekte) | En basit, tamamen deterministik; derlem küçük |
| Qdrant | Güçlü filtreleme ve hibrit arama; ayrı servis |

**Önerim:** **Chroma.** Derlem küçük; K-A ve K-B birkaç yüz parça, K-C firma başına ~200 not. Tanınan bir araç olması portfolyo için de faydalı.

### D3. K-C (bağlam notları) nasıl getirilir?

Önemli bir gözlem: 13 aylık pencerede bir firmanın yalnızca ~20–30 notu var (çeldiriciler dahil).

| Seçenek | Artı | Eksi |
|---|---|---|
| **(a) Pencere filtresi + anlamsal top-k** (ör. k = 8; sorgu `facts.json`'daki kalemler ve bayraklardan) | Gerçek bir retrieval; retrieval isabeti ayrıca ölçülebilir (ground truth hangi notun hangi olayı açıkladığını biliyor) | İlgili not kaçabilir |
| (b) Penceredeki bütün notlar | Retrieval hatası yok | Bağlam uzar; retrieval'ın katkısı gösterilemez |

**Önerim:** **(a).** (b) ise ablation'da ek bir karşılaştırma olarak kullanılsın. Retrieval isabeti (recall@k) yeni bir metrik olarak eklensin.

### D4. K-D (önceki ayların onaylı yorumları)

| Seçenek | Not |
|---|---|
| **(a) İlk sürümde kapalı** | Model geçen ayın metnini kopyalamayı öğrenmez; ideal yorumlara bağımlılık yok |
| (b) Son 1–2 ayın ideal yorumu | Gerçekçi (insan onaylı geçmiş); kopyalama riski |

**Önerim:** **(a).** (b) daha sonra ayrı bir deney olarak denensin.

---

## Özet: önerilen paket

| Karar | Önerim |
|---|---|
| A1 Temel model | Deneme turu (Ministral 3 8B, Gemma 4 E4B, Qwen3.5 9B); eşitlikte Ministral 3 8B |
| A2 Araç seti | Unsloth + TRL, QLoRA; donanım kullanıcının imkânına göre |
| A3 Çıkarım | Değerlendirme vLLM, demo llama.cpp / Ollama |
| B1 İdeal yorum | Karma: kural tabanlı içerik planı + öğretmen modelin metni + otomatik doğrulama; 20–30 örneklik altın küme |
| B2 Öğretmen | Açık ağırlıklı, Apache 2.0 lisanslı büyük model |
| B3 Notsuz nedenler | Açık soru veya işaretli genel hipotez; ground truth nedeni asla |
| B4 Çıktı yapısı | 6.3'teki dört bölüm + uzunluk sınırı |
| C1 Test arketipi | A1 (+ eğitim arketiplerinin görülmemiş varyantları) |
| C2 Hacim | Eğitim 2 × 25 varyant (1.200 ay), doğrulama 3 + 3, testler referans koşudan |
| D1 Embedding | BGE-M3 |
| D2 Vektör deposu | Chroma |
| D3 K-C | 13 ay filtre + top-k; recall@k ölçülsün |
| D4 K-D | İlk sürümde kapalı |

---

## Kaynaklar

- Mistral 3 / Ministral 3: [mistral.ai/news/mistral-3](https://mistral.ai/news/mistral-3), [DeepLearning.AI](https://charonhub.deeplearning.ai/mistral-uses-cascade-distillation-on-mistral-3-to-build-ministral-family/)
- Gemma 4 (Apache 2.0): [The Decoder](https://the-decoder.com/googles-gemma-4-is-now-available-with-apache-2-0-licensing-for-the-first-time/), [DataNorth](https://datanorth.ai/news/google-releases-gemma-4-open-models)
- Qwen3.5 küçük modeller: [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models)
- EuroLLM-22B / 9B: [teknik rapor](https://arxiv.org/html/2602.05879v1), [OSAI Index](https://osai-index.eu/model/eurollm)
- Soofi S: [arXiv 2607.09424](https://arxiv.org/abs/2607.09424), [Fraunhofer IIS](https://www.iis.fraunhofer.de/en/ff/amm/allinga/ai-model-factory/soofi.html), [innfactory](https://innfactory.ai/en/ai-models/soofi/)
- Almanca embedding karşılaştırması: [WZ-IT](https://wz-it.com/en/blog/best-embedding-models-german/), [Boldt-Embed-DE-350M](https://huggingface.co/mayflowergmbh/Boldt-Embed-DE-350M)
- Unsloth bellek gereksinimleri: [docs.unsloth.ai](https://docs.unsloth.ai/get-started/beginner-start-here/unsloth-requirements)
