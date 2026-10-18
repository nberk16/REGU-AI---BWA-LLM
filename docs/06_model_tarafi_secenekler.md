# 06 — Model tarafı: kararlar ve seçenekler

> **Durum (tur 7, 15.10.2026):** Bu belgedeki ana kararların hepsi alındı.
> - **Tur 6:** A1 deneme turu, B3, B4, D1–D4. B3, B4 ve D maddelerini kullanıcı asistana bıraktı; asistanın önerisi olduğu gibi karar olarak kaydedildi.
> - **Tur 7:** C1, C2, A2 (Kaggle), B1, B2.
> - **[ÖNERİ] olarak kalanlar:** eşitlikte Ministral 3 8B; araç seti (Unsloth + TRL); çıkarım altyapısı; somut öğretmen model ve sağlayıcı (Mistral Large 3, Mistral API).
>
> **İlgili:** CLAUDE.md 6.2–6.3, 7, 8, 10 · `docs/yol_haritasi.md` paketleri 4–9 · Karar kaydı: `00_karar_kaydi.md`, Bölüm 10–11 · Kümeler: `04_veri_ureteci.md`, Bölüm 9
>
> Model bilgileri Ekim 2026 itibarıyla web aramasıyla doğrulandı; kaynaklar dosyanın sonunda. Lisanslar, kullanmadan önce model kartında bir kez daha kontrol edilmeli. Bu belge hukuki danışmanlık değildir (CLAUDE.md, talimat 5).

Kararlar birbirine bağlı. Önerilen sıra: **C (eğitim/test) → A (model) → B (ideal yorumlar) → D (bilgi tabanı)**.

---

## A. Temel model ve altyapı

### A1. Temel model

| Seçenek | Boyut | Lisans / menşe | Artı | Eksi |
|---|---|---|---|---|
| **Ministral 3 8B Instruct** | 8B | Apache 2.0; Mistral (Fransa); Aralık 2025 | AB menşeli (Mittelstand algısı, veri koruma argümanı); 256K bağlam; 3–8B sınıfına tam uyuyor | Bu görevdeki Almanca kalitesi henüz denenmedi |
| **Gemma 4 E4B** | ~4,5B etkin | Apache 2.0 (Nisan 2026'dan beri); Google | Çok küçük; 4 GB GPU'ya büyük ölçüde sığar; "4B bile yeterli" anlatısı | Küçük boyutta sayıya ve formata bağlılık riski |
| **Qwen3.5 9B** | 9B | Apache 2.0; Alibaba (Çin) | Küçük sınıfta güçlü genel performans | Alman firmalarında algı sorunu (CLAUDE.md 10) |
| EuroLLM-9B (2512) | 9B | Apache 2.0; AB projesi | 24 AB dili, Avrupa menşeli | Genel akıl yürütmede diğerlerinin gerisinde olabilir |
| Ministral 3 14B / Gemma 4 26B MoE | 14B / 26B (3,8B etkin) | Apache 2.0 | Daha yüksek kalite | 3–8B hedefinin dışında; MoE'de LoRA daha karmaşık |
| Soofi S (30B-A3B) | — | Lisans henüz kesin değil; kapalı beta | Almanca odaklı | Şu an kullanılamıyor; izleme listesinde |

**[KARAR, tur 6] Almanca deneme turu** üç adayla yapılır:
- Adaylar: Ministral 3 8B, Gemma 4 E4B ve Qwen3.5 9B.
- Yöntem: ~10 `facts.json` örneği, aynı istem, sıfır atış (zero-shot).
- Ölçütler: Almanca akıcılık, format uyumu, rakam sadakati (Katman 4'ün ilk sürümüyle), Q4 nicemlemede bellek ve hız.
- **[ÖNERİ]** Sonuçlar eşit çıkarsa Ministral 3 8B seçilir: AB menşeli ve Apache 2.0 lisanslı olması "lokal ve veri korumalı" argümanını güçlendiriyor.
- Deneme turu kullanıcının dizüstü bilgisayarında (Ollama) çalışabilir; bkz. A2.

### A2. Fine-tuning araç seti ve donanım

| Seçenek | Açıklama |
|---|---|
| **Unsloth + TRL (QLoRA)** | Düşük bellek, hızlı; yeni modelleri çabuk destekliyor. 8B QLoRA için resmî alt sınır ~6 GB VRAM, pratikte ~8 GB. Örneklerimiz ~5–6K token olduğu için 12–16 GB daha gerçekçi. |
| Hugging Face TRL + PEFT | Standart ve şeffaf; biraz daha fazla bellek |
| Axolotl | Yapılandırma dosyasıyla eğitim; deney takibi kolay |
| MLX-LM | Apple Silicon'da yerel eğitim |

**[ÖNERİ]** Unsloth + TRL, QLoRA.

#### A2.1 Kullanıcının bilgisayarı (tur 6)

Monster Abra V15.2, ~2019:
- CPU: Intel i7-9750H (6 çekirdek)
- RAM: 16 GB
- GPU: NVIDIA GTX 1650, 4 GB GDDR5 (Turing)

| İş | Bu bilgisayarda? | Gerekçe (tahmini değerler) |
|---|---|---|
| Kod, testler, Katman 1 ve 4 | ✅ | GPU gerekmez |
| Embedding (BGE-M3) ve Chroma | ✅ | Model ~570M parametre. Derlem küçük; CPU'da da dakikalar sürer |
| Deneme turu (3 model × 10 örnek) | ✅ yavaş ama mümkün | 8B Q4 modeli ~5 GB, 4 GB'a sığmaz. Ollama/llama.cpp katmanların bir kısmını GPU'ya, kalanını RAM'e koyar: saniyede ~2–4 token. Örnek başına birkaç dakika, toplam ~1,5–3 saat |
| Demo (tek bir aylık yorum) | ✅ | 8B Q4 ile birkaç dakika. 4 GB'a sığan 3–4B sınıfı bir model çok daha hızlı. BWA ayda bir geldiği için kabul edilebilir |
| Fine-tuning (LoRA) | ❌ | 8B QLoRA için en az ~6 GB, uzun örneklerle 12–16 GB VRAM gerekir. 3–4B modellerde de 5–6K token'lık örnekler 4 GB'a pratikte sığmaz |
| Toplu değerlendirme | ❌ pratikte | 4 varyant × ~870 test ayı ≈ 3.500 üretim. Örnek başına birkaç dakikayla 1–2 hafta kesintisiz çalışma. Bulutta GPU ile saatler |

Ek not: 7 yıllık bir dizüstünün saatlerce tam yükte çalışması ısınma ve yavaşlama (throttling) riski taşır.

**Portfolyo açısından:** Son modelin 7 yıllık, 4 GB GPU'lu bir dizüstünde çalışması, CLAUDE.md 4.4'teki "lokal çalışabilirlik" argümanının somut kanıtı olur.

#### A2.2 Bulut seçenekleri

| Seçenek | Ne sunuyor | Maliyet |
|---|---|---|
| **Kaggle Notebooks** | T4 (16 GB; ikili T4 seçeneği de var) veya P100. Haftada ~30 GPU saati. Oturum başına 12 saate kadar; arka planda çalıştırma (commit) mümkün. Telefon doğrulaması gerekir. | Ücretsiz |
| Google Colab (ücretsiz) | T4. Erişim ve süre garanti değil | Ücretsiz |
| Saatlik kiralık GPU (RunPod, Vast.ai) | RTX 4090 (24 GB): ~0,34 $/saat (topluluk bulutu) ile ~0,69 $/saat (güvenli bulut) | Kullandıkça öde |

**Kabaca ihtiyaç (tahmini; ilk koşuda ölçülür):**
- Bir eğitim koşusu: 960 örnek × ~5,5K token × 3 epoch ≈ 16M token. T4'te ~5–9 saat (bir Kaggle oturumuna sığar); RTX 4090'da ~1–3 saat.
- En az iki eğitim gerekir (yalnızca FT ile RAG + FT), artı bir iki deneme.
- Değerlendirme: GPU'da vLLM ile birkaç saat.
- Toplam: Kaggle'ın ücretsiz kotasında 2–3 haftaya yayılır; kiralık GPU'da muhtemelen 10 $ civarı.

**Çalışma şekli:** Bu oturumun çalıştığı bulut ortamında GPU yok.
- Asistan defterleri (notebook) ve betikleri repoda hazırlar.
- Kullanıcı bunları Kaggle'da ya da dizüstünde çalıştırır.
- Sonuç dosyaları repoya eklenir.

**[KARAR, tur 7]** Dizüstü + Kaggle (ücretsiz):
- Dizüstü: geliştirme, embedding, deneme turu, demo.
- Kaggle: fine-tuning ve değerlendirme.
- Kiralık GPU şimdilik yok; kota yetmezse kullanıcıya sorulur.

### A3. Çıkarım (inference)

| Seçenek | Kullanım |
|---|---|
| **vLLM** (veya transformers) | Değerlendirmede binlerce üretimi GPU'da toplu çalıştırmak |
| **llama.cpp / Ollama** (GGUF, Q4) | Yerel demo; "lokal çalışabilirlik" argümanı |

**[ÖNERİ]** İkisi birlikte: değerlendirme vLLM ile (Kaggle veya kiralık GPU), demo Ollama ile (dizüstü).

---

## B. İdeal yorumların üretimi (eğitim hedefleri)

**Terimler:**
- **İdeal yorum (eğitim hedefi):** Her eğitim örneği için modelin yazmasını istediğimiz "doğru cevap" metni. Model, `facts.json` ve bağlam notlarını görüp bu metni yazmayı öğrenir. 20 varyantla ~960 metin gerekir.
- **Öğretmen model:** İdeal yorumları yazan büyük model. Yalnızca veri hazırlığında kullanılır, üründe yer almaz. Büyük modelden küçük modele bu tür aktarıma *damıtma (distillation)* denir.
- **Altın küme:** Metni insanın satır satır kontrol edip kusursuz hâle getirdiği küçük bir örnek kümesi; bir "cevap anahtarı".

### B1. Üretim yöntemi — CLAUDE.md 9, **[KARAR, tur 7]**

| Seçenek | Nasıl | Artı | Eksi |
|---|---|---|---|
| (a) Şablon | Kod, sabit cümle kalıplarını doldurur ("Personalkosten stiegen um {pct} % …") | %100 doğru, ücretsiz, tekrarlanabilir | Tekdüze, robot gibi dil; model kalıp ezberler |
| (b) Öğretmen model | Büyük model metni baştan sona kendisi yazar | Doğal Almanca | Büyük model de hata yapar (yanlış rakam, uydurma neden); küçük model bu hataları da öğrenir |
| **(c) Karma** | İş üçe bölünür. Bkz. aşağıdaki adımlar. | Doğruluk koddan, dil modelden gelir; "olgu / kaynaklı neden / tahmin" ayrımı garanti | Biraz daha mühendislik |
| (d) Elle yazma | Bütün metinler elle | En yüksek kalite | ~1.000 metin için uygun değil |

**Karma yöntemin üç adımı:**
1. **Ne söylenecek?** Kod, `facts.json`, bağlam notları ve ground truth'tan bir **içerik planı** çıkarır: hangi kalemler anlatılacak, hangi neden hangi notla kaynaklanacak, hangisi uyarı ya da açık soru olacak.
2. **Nasıl söylenecek?** Öğretmen model yalnızca bu planı akıcı Almancaya döker; bir şey eklemesi yasak.
3. **Kontrol.** Kod metni plana karşı denetler: rakamlar `facts.json`'da ya da atıf yapılan notta var mı, plandaki her madde metinde var mı, planda olmayan bir neden eklenmiş mi? Geçemeyen metin yeniden ürettirilir ya da atılır.

**Örnek (Muster GmbH, Juni 2025; referans veriden):**

İçerik planı (kısaltılmış):
```
Kernaussage 1: Umsatzerlöse +141.640 € (+19,0 %) ggü. Vorjahresmonat
   Ursache (Quelle): Großauftrag eines Anlagenbauers → Kontextnotiz 2025-06 #2
   Ursache (Quelle): Preiserhöhung ~5 %              → Kontextnotiz 2025-06
Kernaussage 2: Personalkosten 353.499 € = 1,5-faches Normalniveau (Flag V1)
   Ursache: keine Notiz → Hinweis + offene Frage (monatliche Abgrenzung?)
Kernaussage 3: Bestandsveränderungen -15.419 € nach zwei Nullmonaten (Flag V4)
   → Hinweis + offene Frage (Nachbuchung für April/Mai?)
Abweichung: Werbe-/Reisekosten -60,7 % → Vorjahresmonat mit Messe → Kontextnotiz 2024-06 #2
```

Öğretmen modelin metni (bir cümle):
> „Die Umsatzerlöse liegen mit 886 T€ um 19,0 % über dem Vorjahresmonat; ursächlich sind der Großauftrag eines Anlagenbauers [Quelle: Kontextnotiz 2025-06 #2] und die Preiserhöhung um rund 5 % [Quelle: Kontextnotiz 2025-06].“

Kontrol:
- 886 T€ ↔ 886.365 € ✓
- 19,0 % ✓
- 5 % atıf yapılan notta geçiyor ✓
- İki neden de planda var ✓

**[KARAR, tur 7]**
- **(c) karma.** Ek olarak 20–30 örneklik bir **altın küme**. Kullanım alanları:
  - otomatik metinlerin kalitesini ölçmek,
  - üslup değerlendirmesinde referans olmak,
  - öğretmen modelin istemine örnek vermek.
- Doğrulama katmanı (paket 8), adım 3'te kullanılacağı için ideal yorumlardan **önce** yazılmalı.

### B2. Öğretmen model — **[KARAR, tur 7]**

| Seçenek | Ne demek | Artı | Eksi |
|---|---|---|---|
| **(a) Açık ağırlıklı büyük model, API üzerinden** (ör. Mistral Large 3: 675B MoE / 41B etkin, Apache 2.0, AB) | Model dosyaları herkese açık ve lisans her kullanıma izin veriyor. Model, kendi çalıştıramayacağımız kadar büyük; token başına ücretle bir sağlayıcının API'si üzerinden kullanılır. | Lisans açısından en temiz yol. Ağırlıklar kaybolmadığı için tekrarlanabilir. Ministral ile aynı aile: "Mistral Large → Ministral" damıtma anlatısı, AB menşei korunur | Hesap ve API anahtarı gerekir; küçük bir ücret. Sağlayıcının kendi kullanım koşulları da okunmalı |
| (b) Ticari kapalı model API'si (ör. Claude, GPT, Gemini) | Ağırlıkları kapalı, yalnızca API ile erişilen modeller | En yüksek dil kalitesi, kurulum kolay | Bazı sağlayıcıların koşulları, çıktılarla "rakip" model geliştirmeyi yasaklıyor; küçük bir BWA modelinin buna girip girmediği yoruma açık. Model sürümleri emekliye ayrılır, tekrarlanabilirlik zayıflar |
| (c) Açık bir modeli ücretsiz GPU'da kendimiz çalıştırmak (ör. Gemma 4 31B, Kaggle'da) | API yok, ücret yok | Ücretsiz, lisans temiz | Kurulum zahmetli ve yavaş; Kaggle kotasından yer |

**Gözlem:** Karma yöntemde doğruluk kurallardan geldiği için öğretmen yalnızca dil işini yapar. Bu yüzden en üst düzey ticari modele ihtiyaç azalır.

**Hacim:** ~1.000 metin; metin başına ~3–4K girdi ve ~0,6K çıktı token'ı, toplam ~4M girdi ve ~0,6M çıktı token'ı. Maliyet, sağlayıcı seçilince güncel fiyatla hesaplanır.

**[KARAR, tur 7]** (a) Açık ağırlıklı model, API üzerinden.

**[KARAR, tur 11] Somut model ve sağlayıcı:** Mistral Large 3, Mistral API (`mistral-large-2512`). API anahtarı yalnızca kullanıcının bilgisayarında durur; öğretmen betiği orada çalışır (`11_ideal_yorumlar.md`).
- **Fiyat:** Kaynaklar farklı fiyatlar veriyor: 1M token başına 0,50 $ / 1,50 $ ile 2 $ / 5–6 $ arası. Yukarıdaki hacimle ~3–12 $, tekrarlarla ~5–20 $. Resmî fiyat listesi API anahtarı alınırken kontrol edilir.
- **Koşullar:** Üçüncü taraf bir özete göre Mistral'ın ticari koşullarındaki çıktı kısıtı görsel çıktılarla ilgili; metin çıktıları için kısıt bulunamadı. Resmî metin kontrol edilecek; bu not hukuki görüş değildir.

### B3. Notta geçmeyen nedenlerde hedef metin — **[KARAR, tur 6]**

- Notta karşılığı olmayan bir sapmada hedef metin ya açık soru sorar ya da açıkça işaretli genel bir hipotez verir:
  - Açık soru: „Ursache aus den Unterlagen nicht ersichtlich – Rückfrage: …“
  - İşaretli hipotez: „vermutlich … (Hypothese)“
- Hipotez yalnızca modelin **görebildiği** bilgiden türetilebilir: `facts.json`, bayraklar ve K-B rehberi. Örnek: V1 bayrağında K-B rehberinin saydığı tipik nedenler ("Sonderzahlung, z. B. Urlaubsgeld").
- Ground truth'taki gerçek olay (ör. "drei Neueinstellungen") notta yoksa hedef metne **hiçbir zaman** yazılmaz. Yazılsaydı model bilemeyeceği nedenleri tahmin etmeyi öğrenirdi ve "uydurma neden oranı" metriği anlamını yitirirdi.

### B4. Çıktı yapısı (CLAUDE.md 6.3) — **[KARAR, tur 6]**

- 6.3'teki dört bölüm:
  1. Kernaussagen (en fazla 3)
  2. Abweichungen im Detail (tablo)
  3. Hinweise auf mögliche Verzerrungen
  4. Offene Fragen
- Tablo sütunları sabit: Position | Ist | Vergleich | Abweichung | Erklärung | Quelle oder Hypothese.
- Uzunluk ~250–350 kelime (tablo hariç).
- Her neden cümlesinde ya `[Quelle: …]` ya da `(Hypothese)`.
- Bölümde içerik yoksa bölüm kalır ve „Keine.“ yazılır. Böylece format kontrolü basit kalır.
- 6.3'teki örnek, ideal yorumlar üretilirken Muster GmbH'nin gerçek verisiyle yeniden yazılır.

---

## C. Eğitim/test ayrımı — CLAUDE.md 9, **[KARAR, tur 7]**

### C1. Test arketipi

**Neden ayrı bir test?** Model, eğitimde gördüğü verilerde iyi görünür; ezberlemiş olabilir. Gerçek başarı, hiç görmediği veride ölçülür.

**Arketip ve varyant:**
- Arketip bir firma tipidir: A1 metal Zulieferer, A2 toptancı, A3 bahçe mobilyası üreticisi.
- Varyantlar aynı tipin "kardeş" firmalarıdır: sektör, maliyet yapısı ve sezon kalıbı aynı; rakamlar, olaylar ve muhasebe pratiği farklı.
- Kardeşler birbirine çok benzediği için, aynı arketipten hem eğitimde hem testte firma bulunursa sonuç gerçekte olduğundan iyi görünebilir.
- Bu yüzden ilke [KARAR]: test, eğitimde hiç görülmemiş bir **arketip** üzerinde yapılır.

**İki test düzeyi.** Benzetme: ehliyet sınavı.

| Düzey | Ne ölçer | Benzetme |
|---|---|---|
| **Yeni sektör:** test arketipi, eğitimde hiç yok | Model hiç görmediği tipte bir firmayı yorumlayabiliyor mu? (zor) | Sınavı hiç gitmediğin bir şehirde vermek |
| **Yeni firma:** eğitim arketiplerinin görülmemiş varyantları | Bildiği sektörde yeni bir firmayı yorumlayabiliyor mu? (daha kolay) | Aynı şehirde hiç girmediğin bir mahallede sınav |

- İkisi de iyiyse model sağlam.
- Yeni firma iyi, yeni sektör zayıfsa model sektöre özgü kalıpları öğrenmiş demektir. Bu da portfolyo için dürüst ve bilgilendirici bir sonuçtur.
- İkinci düzey ek eğitim gerektirmez. Yalnızca ~480 ek test üretimi gerekir; veri referans koşuda zaten var.

| Seçenek | Artı | Eksi |
|---|---|---|
| **A1 (Muster GmbH) test** | Vitrin örnekleri gerçekten "hiç görülmemiş" firmadan gelir; en güçlü kanıt anlatısı. Eğitimdeki A2 + A3 bütün çarpıklık türlerini içerir (`docs/01`, 4.1). | Eğitimdeki `cite` örneği daha az (bkz. C2) |
| A2 (toptancı) test | V2 ayrımı en zor arketipte ölçülür; eğitimde `cite` örneği en çok | Muster GmbH eğitimde kalır; vitrin örnekleri "görülmüş" firmadan |
| A3 (sezonlu üretici) test | Mevsimselliğe genelleme ölçülür | Güçlü sezon eğitimde hiç görülmez; çok zor bir test |

**[KARAR, tur 7]** A1 ve iki test düzeyi. Kullanıcının isteği, testte hem öğretilmiş hem öğretilmemiş türden örnekler olmasıydı: "yeni firma" öğretilmiş türü, "yeni sektör" öğretilmemiş türü karşılıyor.

### C2. Kümeler ve varyant sayısı (A1 test seçilirse)

Eğitim için yeni bir koşu yapılır:
- Arketipler A2 + A3.
- Profil `train_price_boost`.
- Varyant numaraları 100'den başlar; ayrı seed.

Deneme koşusunun (seed 7) sayıları:

| Eğitim varyantı / arketip | Eğitim ayı | V2 adayı: `cite` / `warn` / `either` | Bir eğitim koşusu (T4, tahmini) |
|---:|---:|---|---|
| 15 | 720 | 35 / 389 / 8 | ~4–7 saat |
| **20** | **960** | **47 / 509 / 19** | ~5–9 saat |
| 25 | 1.200 | 68 / 620 / 29 | ~6–11 saat |

**Neden 20?**
- Literatürde ~1.000 özenli örneğin üslup ve format öğretmeye yettiği bildiriliyor (LIMA).
- Bir eğitim koşusu tek bir Kaggle oturumuna sığar.
- İdeal yorum maliyeti ve elle kontrol yükü 25'e göre %20 daha az.
- Üreteç parametrik olduğu için, sonuçlar gerektirirse sonradan artırılabilir.
- İsteğe bağlı: 5 / 10 / 20 varyantla bir öğrenme eğrisi, "veri miktarı ne kadar önemli?" sorusuna kanıt olur (ek eğitim koşuları gerektirir).

| Küme | Kaynak | Hacim (yorumlanabilir ay) |
|---|---|---|
| Eğitim | Yeni koşu: A2 + A3 × 20 varyant | 960 |
| Doğrulama (erken durdurma, hiperparametre) | Aynı koşu, ayrı 3 + 3 varyant | 144 |
| Test — yeni firma | Referans koşu, A2 + A3, v00–v09 | 480 |
| Test — yeni sektör | Referans koşu, A1, v00–v09 (Muster GmbH dahil) | 240 |
| V2 ayrımı | Dengelenmiş küme. A1 kısmı yeni sektör, A2/A3 kısmı yeni firma olarak raporlanır | 147 |

**[KARAR, tur 7]** 20 eğitim + 3 doğrulama varyantı / arketip. Koşu komutu ve kesin sayılar: `04_veri_ureteci.md`, Bölüm 9. Deneme turu örnekleri doğrulama varyantlarından seçilir; test kümesi model seçiminde kullanılmaz.

---

## D. Bilgi tabanı (Katman 2) — **[KARAR, tur 6]**

### D1. Embedding modeli: **BGE-M3**

| Seçenek | Lisans | Not |
|---|---|---|
| **BGE-M3** ✅ | MIT | Çok dilli, 8.192 token. Yoğun ve seyrek (hibrit) arama yapabiliyor; seyrek arama Almanca birleşik kelimelerde işe yarar. DACH bölgesinde RAG için yaygın tercih. |
| multilingual-e5-large | (model kartında doğrulanmalı) | Almanca soru-cevapta BGE-M3'e yakın sonuçlar bildiriliyor |
| Qwen3-Embedding (0,6B / 4B / 8B) | Apache 2.0 (bildirilen) | Güçlü, ama Almanca için bağımsız ölçüm bulunamadı |
| Almancaya özel küçük modeller (ör. Boldt-Embed-DE-350M) | (doğrulanmalı) | Almanca FAQ/RAG'de iyi sonuç bildiriliyor; topluluk modeli |

### D2. Vektör deposu: **Chroma** (gömülü)

- Kurulumu kolay, meta veri filtresi var (firma, 13 aylık dönem), kalıcı.
- Derlem küçük: K-A ve K-B birkaç yüz parça, K-C firma başına ~200 not.
- Alternatifler (NumPy/FAISS, Qdrant) gerekmedi.

### D3. K-C getirme: **pencere filtresi + anlamsal top-k**

- Önce firma + 13 aylık pencere (t−12 … t) + `Firmenprofil` filtresi uygulanır.
- Ardından `facts.json`'dan üretilen sorguyla anlamsal top-k seçilir; başlangıç değeri k = 8 [ÖNERİ, ayarlanabilir].
- Pencerede bir firmanın yalnızca ~20–30 notu var. Bu yüzden ablation'da karşılaştırma olarak "penceredeki bütün notlar" varyantı da çalıştırılır.
- **Yeni metrik: retrieval isabeti (recall@k).** Ground truth hangi notun hangi olayı açıkladığını biliyor; ilgili notun ilk k parçada olup olmadığı ölçülür.

### D4. K-D (önceki ayların onaylı yorumları): **ilk sürümde kapalı**

- Gerekçe: model geçen ayın metnini kopyalamayı öğrenmez ve ideal yorumlara bağımlılık doğmaz.
- Son 1–2 ayın ideal yorumunu bağlama katmak daha sonra ayrı bir deney olarak denenebilir.

---

## Özet

| Karar | Durum | İçerik |
|---|---|---|
| A1 Temel model | **[KARAR, tur 9]** | **Gemma 4 E4B**, yedek Qwen3.5 9B. Deneme turu sonuçları: `trial/results.md`, `docs/08` |
| A2 Araç seti / donanım | [ÖNERİ] / **[KARAR]** | Unsloth + TRL (QLoRA) / Dizüstü: geliştirme, deneme turu, demo; Kaggle: eğitim ve değerlendirme |
| A3 Çıkarım | [ÖNERİ] | Değerlendirme vLLM, demo Ollama |
| B1 İdeal yorum | **[KARAR]** | Karma + 20–30 örneklik altın küme |
| B2 Öğretmen | **[KARAR]** | Açık ağırlıklı model, API üzerinden; **Mistral Large 3** (tur 11), anahtar yalnızca kullanıcının bilgisayarında |
| B3 Notsuz nedenler | **[KARAR]** | Açık soru veya görülebilir bilgiden türetilmiş işaretli hipotez; ground truth nedeni asla |
| B4 Çıktı yapısı | **[KARAR]** | 6.3'teki dört bölüm, ~250–350 kelime, sabit tablo, boş bölümde „Keine.“ |
| C1 Test arketipi | **[KARAR]** | A1 (öğretilmemiş tür) + görülmemiş A2/A3 varyantları (öğretilmiş tür) |
| C2 Hacim | **[KARAR]** | 20 eğitim + 3 doğrulama varyantı / arketip (960 eğitim ayı) |
| D1 Embedding | **[KARAR]** | BGE-M3 |
| D2 Vektör deposu | **[KARAR]** | Chroma |
| D3 K-C | **[KARAR]** | 13 ay filtre + top-k (k = 8), recall@k metriği, "bütün notlar" ablation'da |
| D4 K-D | **[KARAR]** | İlk sürümde kapalı |

---

## Kaynaklar

- Mistral 3 / Ministral 3 / Mistral Large 3: [mistral.ai/news/mistral-3](https://mistral.ai/news/mistral-3), [DeepLearning.AI](https://charonhub.deeplearning.ai/mistral-uses-cascade-distillation-on-mistral-3-to-build-ministral-family/)
- Gemma 4 (Apache 2.0): [The Decoder](https://the-decoder.com/googles-gemma-4-is-now-available-with-apache-2-0-licensing-for-the-first-time/), [DataNorth](https://datanorth.ai/news/google-releases-gemma-4-open-models)
- Qwen3.5 küçük modeller: [Artificial Analysis](https://artificialanalysis.ai/articles/qwen3-5-small-models)
- EuroLLM-22B / 9B: [teknik rapor](https://arxiv.org/html/2602.05879v1), [OSAI Index](https://osai-index.eu/model/eurollm)
- Soofi S: [arXiv 2607.09424](https://arxiv.org/abs/2607.09424), [Fraunhofer IIS](https://www.iis.fraunhofer.de/en/ff/amm/allinga/ai-model-factory/soofi.html), [innfactory](https://innfactory.ai/en/ai-models/soofi/)
- Almanca embedding karşılaştırması: [WZ-IT](https://wz-it.com/en/blog/best-embedding-models-german/), [Boldt-Embed-DE-350M](https://huggingface.co/mayflowergmbh/Boldt-Embed-DE-350M)
- Unsloth bellek gereksinimleri: [docs.unsloth.ai](https://docs.unsloth.ai/get-started/beginner-start-here/unsloth-requirements)
- 4 GB GPU'da 8B model (tahminî değerler): [willitrunai.com](https://willitrunai.com/can-run/hf-maziyarpanahi--llama-3-8b-instruct-32k-v0-1-gguf-on-gtx-1650-4gb), [bestllmfor.com](https://bestllmfor.com/guide/llm-gtx-1650-1660/), [P1000 ölçümü (databasemart)](https://www.databasemart.com/blog/ollama-gpu-benchmark-P1000)
- Mistral Large 3 fiyatları (üçüncü taraf): [CloudZero](https://www.cloudzero.com/blog/mistral-api-pricing), [anotherwrapper](https://anotherwrapper.com/tools/llm-pricing/mistral-large-latest); koşullar: [Mistral terms](https://mistral.ai/en/terms), [ConductAtlas özeti](https://conductatlas.com/platform/mistral-ai/mistral-ai-commercial-terms/)
- Ücretsiz GPU (Kaggle kotası): [gpuperhour.com](https://gpuperhour.com/blog/free-cloud-gpus-and-credits)
- Kiralık GPU fiyatları: [Spheron, RunPod vs Vast.ai 2026](https://www.spheron.network/blog/gpu-cloud-pricing-comparison-runpod-vs-vastai-2026/), [hackceleration, RunPod fiyatları](https://www.hackceleration.com/labs/runpod-pricing)
