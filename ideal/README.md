# İdeal yorumlar: kullanıcı adımları (öğretmen modeli)

Öğretmen model (Mistral Large 3), kodun hazırladığı içerik planlarını Almanca yoruma çevirir. Betik senin bilgisayarında çalışır; API anahtarı yalnızca orada durur.

- **Tasarım:** [`docs/11_ideal_yorumlar.md`](../docs/11_ideal_yorumlar.md)
- **Önce pilot:** ~24 ay, ~10–20 dakika. Sonuçları okuyup istemi gerekirse düzelttikten sonra büyük koşu (960 + 144 ay) gelir.

**Anahtar kuralları:**
- Anahtarı bana yazma, GitHub'a ya da repo klasöründeki bir dosyaya koyma.
- Aşağıdaki komut anahtarı yalnızca açık PowerShell penceresine verir; pencere kapanınca silinir. Her yeni pencerede yeniden girersin.
- Betik anahtarı hiçbir dosyaya yazmaz ve ekrana basmaz.

---

## 1. Hazırlık

1. **Repoyu yeniden indir** (dal güncellendi). Deneme turundaki gibi ZIP bağlantısı:
   https://github.com/nberk16/REGU-AI---BWA-LLM/archive/refs/heads/claude/repodaki-project-analysis-al4o1f.zip
   ZIP'e sağ tık → **Tümünü ayıkla**. Eski klasörü silebilir ya da yeni bir yere çıkartabilirsin.
2. **PowerShell'i klasörde aç:** Çıkarttığın klasöre gir (içinde `ideal`, `docs`, `validation` … görünmeli), adres çubuğuna `powershell` yaz, Enter.
3. **Python:** `python --version` → 3.11 veya üstü olmalı (sende 3.14 var). Ek paket gerekmez.

## 2. Anahtarı gir ve dene

```
$env:MISTRAL_API_KEY = "BURAYA-ANAHTARIN"
python ideal/run_teacher.py --check
```

- Tırnakların arasına Mistral konsolundaki „BWA Kommentar“ anahtarını yapıştır.
- Beklenen çıktı: `Anahtar geçerli; mistral-large-2512 kullanılabilir.`
- Başka bir mesaj görürsen ekrandaki satırları bana gönder. **`$env:MISTRAL_API_KEY = …` satırını asla kopyalama**; yalnızca altındaki satırları gönder. Anahtar yanlışlıkla bir yere yapıştırılırsa konsolda silip yenisini oluştur.

## 3. Pilot

```
python ideal/run_teacher.py --set pilot
```

- Her ay için bir satır görünür: `[3/24] A2-v121_2025-06 ✓ (1 deneme, 25 s)`. ✓ kabul edildi, ✗ üç denemede kontrolü geçemedi.
- Hız sınırı hatası alırsan ya da çok yavaşsa: `--workers 1` ekle.
- Yarıda kalırsa aynı komut kaldığı yerden devam eder.

## 4. Sonucu gönder

Çıktı: `ideal/outputs/pilot.jsonl`. **Bizim dala** yükle; `main` dalına değil:

1. Bu bağlantıyı aç: https://github.com/nberk16/REGU-AI---BWA-LLM/upload/claude/repodaki-project-analysis-al4o1f/ideal
2. Sayfanın üstünde dal adı `claude/repodaki-project-analysis-al4o1f` görünmeli.
3. `pilot.jsonl` dosyasını sürükle.
4. Altta „Commit directly to the `claude/repodaki-project-analysis-al4o1f` branch“ seçili olmalı. „main“ yazıyorsa durdur ve bana haber ver.
5. **Commit changes**.

Sonra bana haber ver. Metinleri okurum, altın küme adaylarını seçerim ve gerekirse istemi düzeltirim. Büyük koşunun komutlarını ondan sonra veririm.

## 5. Büyük koşu

Önce doğrulama kümesi (144 ay, tahminen ~20–30 dakika):

```
python ideal/run_teacher.py --set val
```

`ideal/outputs/val.jsonl` dosyasını Bölüm 4'teki gibi yükle. Ben okuyup onaylayınca eğitim kümesi (960 ay, tahminen ~2–3 saat; yarıda kalırsa aynı komut kaldığı yerden devam eder):

```
python ideal/run_teacher.py --set train
python ideal/run_teacher.py --set train --retry-failed
```

İkinci komut, kontrolü geçemeyen ayları yeni bir rastgelelik tohumuyla bir kez daha dener. Doğrulama kümesi için de aynısı: `python ideal/run_teacher.py --set val --retry-failed`.

## 6. Düzeltilen aylar ve bağlamsız hedefler (tur 12)

Repoyu yeniden indir (Bölüm 1; yeni bir klasöre çıkart). İçindeki `ideal/outputs/` dosyaları güncel; kendi eski klasöründekileri kullanma.

**a) Düzeltmelerden etkilenen ayları yeniden üret** (96 ay, tahminen ~20 dakika). İki düzeltme var: V6 (sezon) bayrağı ve eşit etkili kaynakların sırası (`docs/11`, Bölüm 15).

```
python ideal/run_teacher.py --set val
python ideal/run_teacher.py --set train
```

- İlk satırda „… tamamlanmış, N çalışacak“ yazar. Doğrulama kümesinde N = 9, eğitim kümesinde N = 87 olmalı.
- **N 144 ya da 960 çıkarsa durdur** (Ctrl+C): eski klasörü kullanıyorsun.
- Betik yalnızca girdisi değişen ayları üretir; geri kalanlar olduğu gibi kalır.

**b) Bağlamsız hedefler** („yalnızca fine-tuning“ modeli için). Önce doğrulama kümesi (144 ay, ~25 dakika):

```
python ideal/run_teacher.py --set val_ohne
```

`ideal/outputs/` klasöründeki `val.jsonl`, `train.jsonl` ve `val_ohne.jsonl` dosyalarını Bölüm 4'teki gibi yükle ve bana haber ver. Metinleri okuyup onaylayınca eğitim kümesi gelir (960 ay, ~2–3 saat):

```
python ideal/run_teacher.py --set train_ohne
python ideal/run_teacher.py --set train_ohne --retry-failed
python ideal/run_teacher.py --set val_ohne --retry-failed
```

## 7. Bağlamsız eğitim kümesi ve kalan 9 ay

Aynı klasörde devam edebilirsin; yeniden indirmen gerekmiyor (yüklediğin dosyalar repodakilerle aynı).

```
python ideal/run_teacher.py --set val
python ideal/run_teacher.py --set train_ohne
python ideal/run_teacher.py --set train_ohne --retry-failed
python ideal/run_teacher.py --set val_ohne --retry-failed
```

- **İlk komut:** düzeltilen 9 doğrulama ayı. İlk satırda „135 tamamlanmış, 9 çalışacak“ yazmalı.
- **İkinci komut:** 960 ay, ~2–3 saat. Yarıda kalırsa aynı komut kaldığı yerden devam eder.
- **Son iki komut:** kontrolü geçemeyen ayları bir kez daha, yeni tohumlarla dener.
- **Bitince yükle:** `ideal/outputs/` içindeki `val.jsonl`, `train_ohne.jsonl` ve `val_ohne.jsonl` dosyalarını Bölüm 4'teki gibi yükle.

**Uzun koşu için:** Başlık çubuğuna sağ tık → **Özellikler** → **Seçenekler** → „Hızlı Düzenleme Modu“ işaretini kaldır. Böylece pencereye yanlışlıkla tıklamak koşuyu duraklatmaz. Koşu sürerken **Ctrl+C**'ye basma; bu tuş betiği durdurur.

## Sorun giderme

| Mesaj | Ne yapmalı |
|---|---|
| `MISTRAL_API_KEY tanımlı değil` | Bölüm 2'deki `$env:…` satırını bu pencerede yeniden çalıştır |
| `Anahtar geçersiz (401)` | Anahtarı konsoldan yeniden kopyala; gerekirse yeni bir anahtar oluştur |
| `Model listesinde … yok` / `Deneme başarısız` | Mistral konsolunda bir planın (ücretsiz „Experiment“) etkin olduğunu kontrol et; ekrandaki satırları bana gönder |
| `hata (…); sonra aynı komutla yeniden denenir` | Ağ sorunu olabilir; komutu yeniden çalıştır |
| Ekran uzun süre değişmiyor | Pencereye tıklandıysa Windows ekrana yazmayı durdurur (başlıkta „Seç“/„Select“); **Esc**'ye bas |
| `KeyboardInterrupt` | Ctrl+C'ye basıldı. Biten aylar kayıtlı; aynı komutu yeniden çalıştır, kaldığı yerden devam eder |
