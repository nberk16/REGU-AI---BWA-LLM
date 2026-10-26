# Deneme turu sonuçları

Örnek sayısı: 10 (doğrulama varyantları; `trial/inputs/selection.md`). Puanlama: doğrulama katmanı (`docs/07`).

## Özet

| Model | Örnek | Format uyumu | Rakam sadakati (toplam) | İtiraz edilen rakam | Kaynaklı neden | İşaretsiz neden | İçerik hatası / örnek | Eksik kalem/bayrak | Kelime (medyan) | Çıktı token/s | İstem token/s | Süre / örnek |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemma4-e4b | 10 | 6/10 | 0,99 | 4 | 5 | 18 | 2,2 | 6 | 167 | 4,3 | 16,4 | 391,8 s |
| ministral-3-8b | 10 | 0/10 | 0,8 | 92 | 43 | 32 | 12,7 | 6 | 300,5 | 2,5 | 12,5 | 845,3 s |
| qwen3.5-9b | 10 | 7/10 | 0,96 | 13 | 29 | 16 | 3,7 | 2 | 218 | 2,8 | 11,3 | 579,1 s |

**Sütunlar:**
- **Format uyumu:** CLAUDE.md 6.3 yapısına uyan çıktı sayısı.
- **Rakam sadakati:** `facts.json`'la ya da kaynak gösterilen notla eşleşen rakamların payı.
- **İtiraz edilen rakam:** belgelenmemiş, yanlış satıra ait, işareti ters ya da birimi karışmış rakamlar.
- **Kaynaklı / işaretsiz neden:** bir bağlam notunu gösteren ve ne not ne `(Hypothese)` taşıyan neden cümleleri.
- **İçerik hatası:** biçim dışındaki `fehler` bulguları (rakam, kaynak, neden; `docs/07`, Bölüm 6).
- **Eksik kalem/bayrak:** metinde geçmeyen önemli kalemler ve bayraklar (`hinweis`).
- Bellek payı gösterilmez: Ollama'nın `/api/ps` değerleri bu sürümde güvenilir değil (ör. 9B model için 26 MB).

## Örnek başına bulgular (içerik hatası · rakam sadakati)

| Örnek | gemma4-e4b | ministral-3-8b | qwen3.5-9b |
|---|---|---|---|
| A2-v120_2025-09 | 3 · 1 · Format ✗ | 9 · 0,87 · Format ✗ | 5 · 1 |
| A2-v120_2026-05 | 3 · 1 · Format ✗ | 28 · 0,53 · Format ✗ | 3 · 0,91 |
| A2-v121_2026-03 | 1 · 1 | 14 · 0,88 · Format ✗ | 1 · 1 |
| A2-v122_2025-06 | 1 · 0,97 | 9 · 0,84 · Format ✗ | 2 · 0,96 · Format ✗ |
| A3-v120_2025-02 | 2 · 1 · Format ✗ | 13 · 0,74 · Format ✗ | 5 · 0,95 |
| A3-v120_2025-12 | 0 · 1 | 16 · 0,69 · Format ✗ | 3 · 1 |
| A3-v121_2025-03 | 2 · 1 | 6 · 0,93 · Format ✗ | 6 · 0,88 · Format ✗ |
| A3-v121_2026-07 | 2 · 0,97 | 6 · 0,9 · Format ✗ | 5 · 0,98 |
| A3-v122_2025-10 | 2 · 0,95 | 12 · 0,84 · Format ✗ | 3 · 0,96 |
| A3-v122_2026-09 | 6 · 1 · Format ✗ | 14 · 0,76 · Format ✗ | 4 · 0,98 · Format ✗ |

## En sık bulgular

- **gemma4-e4b:** `quelle_facts` × 81, `tabelle_ohne_quelle` × 18, `laenge` × 8, `flag_fehlt` × 5, `frage_format` × 4, `zahl_unbelegt` × 2, `einheit` × 2, `position_fehlt` × 1
- **ministral-3-8b:** `quellenformat` × 63, `zahl_unbelegt` × 63, `zahl_falsche_position` × 20, `quelle_facts` × 20, `begruendung_ohne_kennzeichnung` × 18, `tabelle_ohne_quelle` × 14, `tabellenkopf` × 10, `zahl_notiz_ohne_quelle` × 6
- **qwen3.5-9b:** `quelle_facts` × 19, `quellenformat` × 11, `begruendung_ohne_kennzeichnung` × 10, `quelle_unbekannt` × 8, `zahl_unbelegt` × 7, `tabelle_ohne_quelle` × 6, `zahl_notiz_ohne_quelle` × 5, `flag_fehlt` × 2

## Okuma değerlendirmesi (asistan, ground truth ile karşılaştırarak)

30 çıktının hepsi okundu ve her ay, ground truth ile karşılaştırıldı (`inputs/selection.md`). Ground truth şunları içeriyor: olaylar, notla açıklanması gereken nedenler, beklenen uyarılar, V2 kararı.

Bu bir **sıfır atış** karşılaştırmasıdır: 10 örnek, tek istem. Amaç temel modeli seçmek; modellerin fine-tuning sonrası performansını tahmin etmez.

### Örnek başına

| # | Örnek ve beklenen | gemma4-e4b | qwen3.5-9b | ministral-3-8b |
|---|---|---|---|---|
| 1 | A3 03/25 · V2 adayı **notla açıklanmalı** (alüminyum zammı) · onarım notu | V2 yalnızca „auffällig“ ✗ · onarım notu kullanılmadı ✗ · onarım giderini „önceki yıl daha yüksek“ diye ters yazdı ✗ | V2'yi alüminyum notuyla açıkladı ✓ · onarım notu ✓ · kendi hesapladığı yüzdeler ✗ | Alüminyum notu ✓ ama ücret artışını da brüt kâr oranının nedeni saydı ✗ · %19 düşüşe „yarıya indi“ dedi ✗ |
| 2 | A2 09/25 · V2 adayı (`either`) · onarım notu · V3 | Onarım notu kullanılmadı ✗ · V3 ✓ · -5,6 Pp. düşüşe „iyileşme“ dedi ✗ | Onarım notu ✓ · V3 ✓ · malzeme artışını satış fiyat listesine bağladı ✗ | „2,45 Mrd. €“ (1.000 kat hata) ✗ · uydurma „birikmiş zarar“ ✗ |
| 3 | A2 03/26 · V2 adayı **uyarılmalı** · notsuz ay · V3 | V2'yi uyarı olarak verdi ✓ · V3 ✓ | V2'yi olgu gibi sundu ✗ · V3 ✓ | V2'yi „daha iyi marj“ diye yorumladı ✗ · uydurma kümülatif rakamlar („5,39 Mrd. €“) ✗ |
| 4 | A2 06/25 · **V1 tuzağı:** personel gideri sıçraması bir tahakkuk çarpıklığı; o ay işe alım notu da var · V3 | V1'i tarafsız uyarı olarak verdi ✓ · işe alım notunu kullanmadı | V1 uyarısı ✓ ama „Haziran için not yok“ dedi, oysa var ✗ | Sıçramayı işe alım notuyla açıkladı: **tuzağa düştü** ✗ · uydurma tutar ✗ |
| 5 | A2 05/26 · V2 adayı **uyarılmalı** (geç fatura) · alış fiyatı notu (+%4) · V3 | V2 uyarısı ✓ ama oran artışını alış zammına bağladı (yön ters) ✗ | Alış zammını „marja olumlu“ diye okudu ✗ · V2 uyarılmadı ✗ | Yuvarlanmış uydurma rakamlar („764.800 €“) ✗ · toplu sözleşme zammını marj artışının nedeni saydı ✗ |
| 6 | A3 10/25 · V4 · V6 · eski işe alım notları | V4 ✓ · işe alım ✓ · yüzde ile yüzde puanı karışık ✗ | V4 ✓ · işe alım ✓ · diğer giderleri ilgisiz bir notla (Steuerberater değişikliği) açıkladı ✗ | İşaret hataları ✗ · uydurma kümülatif zarar ✗ |
| 7 | A3 12/25 · onarım notu · işe alım notu (7 kişi) · V4 · nedeni olmayan V2 adayı | Onarım ✓ · malzeme oranını sevkiyat ekibine bağladı ✗ | Onarım ✓ · işe alım ✓ · V4 ✓ · V2'yi eski bir ziyaret notuna bağladı ✗ | Uydurma ciro rakamları ✗ · uydurma birim („Ts€“) |
| 8 | A3 07/26 · yalnızca V6 · olay yok | Temkinli, „Ursache offen“ ✓ · V6 ✓ | Müşteri kaybı notunu neden olarak verdi (makul) · **var olmayan kaynak** („Kontextnotiz 2026-07“) ✗ | Uydurma kümülatif zarar ✗ |
| 9 | A3 02/25 · sakin ay · V6 | Temkinli ✓ · V6 ✓ | Kendi hesapladığı „+229,1 %“ ✗ · yazım hatası („Fevuar“) | Notlarla ilgisiz nedenler kurdu ✗ |
| 10 | A3 09/26 · **çeldirici not** (müşteri heyeti) · onarım notu · V4 × 2 · V2 adayı **uyarılmalı** | Onarım ✓ · V4 ✓ · V2'yi olgu gibi sundu ✗ · çeldiriciye kanmadı ✓ | Onarım ✓ · V4 ✓ · V2 uyarısı ✓ · stok değişimini çeldirici nota bağladı ✗ | „1,14 Mrd. €“ ✗ · V2'yi maliyetlerle açıkladı ✗ |

**Kabaca sayım** (V2 kararı net olan 4 örnek: 1, 3, 5, 10):
- **V2 adayında doğru karar:** Gemma ~1,5/4, Qwen 2/4, Ministral ~0,5/4.
- **V1 tuzağı (örnek 4):** Gemma ve Qwen uyardı; Ministral tuzağa düştü.
- **Çeldirici ve ilgisiz notlar:** Gemma hiç kullanmadı; Qwen üç kez yanlış nota bağladı; Ministral sık sık ilgisiz not gösterdi.

### Model başına

**gemma4-e4b — güvenilir ama yüzeysel**
- **Güçlü yanları:**
  - Rakam sadakati en yüksek (0,99); neredeyse hiç uydurma rakam yok.
  - Biçim büyük ölçüde doğru.
  - En hızlısı: örnek başına ~6,5 dk, diğerlerinin yaklaşık iki katı hızlı.
- **Zayıf yanları:**
  - Bağlam notlarını nadiren kullanıyor (10 örnekte 5 kaynaklı neden); çoğu yerde „Ursache offen“ ya da totoloji („gegenüber Vorjahresmonat gestiegen“).
  - Kaynak olarak sürekli „FACTS“ gösteriyor.
  - Kısa yazıyor (medyan 167 kelime; hedef ~250–350).
  - Birkaç anlam hatası var: yön ters, yüzde ile yüzde puanı karışık.
- **Almanca:** Dilbilgisi doğru ama kalıplaşmış ve bürokratik („Es liegt ein Hinweis vor, da …“).

**qwen3.5-9b — en zengin içerik, en iyi Almanca**
- **Güçlü yanları:**
  - Notları en çok ve çoğunlukla doğru kullanıyor (29 kaynaklı neden).
  - Akıcı, yöneticiye uygun bir Almanca.
  - Uyarı dili çoğunlukla yerinde.
- **Zayıf yanları:**
  - Yasak olmasına rağmen yüzdeleri kendisi hesaplıyor.
  - Bazen ilgisiz ya da çeldirici notu neden olarak gösteriyor; bir kez var olmayan bir kaynak uydurdu.
  - Kaynak biçimi tutarsız.
  - „pp.“ gibi İngilizce kısaltmalar ve birkaç yazım hatası var.
- **Diğer:** Örnek başına ~9,5 dk. Çin menşei nedeniyle Alman firmalarında algı sorunu olabilir (CLAUDE.md 10).

**ministral-3-8b — bu görevde en zayıfı**
- **Rakamlar:**
  - Rakam sadakati 0,80.
  - Büyüklük hataları („Mrd.“ yerine „Mio.“) ve yuvarlanmış uydurma rakamlar („764.800 €“) var.
  - Kümülatif tutarlar ve dönemler uydurulmuş.
- **Biçim:** 10 çıktının hiçbiri doğru değil; her yerde kalın yazı, ayırıcı çizgi ve değiştirilmiş tablo başlıkları var.
- **Akıl yürütme:** Hatalı; V1 tuzağına düştü ve toplu sözleşme zammını brüt kâr oranının nedeni saydı.
- **Almanca:** Akıcı görünüyor ama uydurma bileşik kelimeler var („Materialkostenstaucher“, „Saisonaleffekte“).
- **Hız:** En uzun yazan ve en yavaş model (örnek başına ~14 dk).

### Üç modelde ortak (fine-tuning'in hedefi)

- Kaynak gösterme biçimi `[Quelle: …]` tutarsız; „FACTS“ ya da bayrak kodları kaynak gibi gösteriliyor.
- `(Hypothese)` işareti neredeyse hiç kullanılmıyor; tahminler olgu gibi yazılıyor.
- Yasak olmasına rağmen yüzde ve fark hesaplanıyor.
- V2 adayında not ile uyarı arasındaki ayrım tutarsız.

Bunlar CLAUDE.md 7'deki „çıplak model“ beklentisini doğruluyor: neden uyduruyor, biçim tutarsız, rakam hataları yapıyor.

### Veri tarafında bir bulgu

Alış fiyatı notları (E04) bazı kalıplarda belirsiz: „Heizungstechnik wird ab Mai etwa 4 % teurer.“ Cümle, alış fiyatı mı satış fiyatı mı olduğunu söylemiyor. Gemma ve Qwen bunu satış fiyatı artışı gibi okudu (örnek 5). Not kalıplarını netleştirmek („Unser Lieferant …“, „Einkaufspreise …“) eğitim ve değerlendirme verisini daha adil yapar [ÖNERİ].
