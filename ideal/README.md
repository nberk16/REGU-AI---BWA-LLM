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
- Başka bir mesaj görürsen (ör. model kullanılamıyor) ekrandaki satırları bana gönder; anahtarı gönderme.

## 3. Pilot

```
python ideal/run_teacher.py --set pilot
```

- Her ay için bir satır görünür: `[3/24] A2-v121_2025-06 ✓ (1 deneme, 25 s)`. ✓ kabul edildi, ✗ üç denemede kontrolü geçemedi.
- Hız sınırı hatası alırsan ya da çok yavaşsa: `--workers 1` ekle.
- Yarıda kalırsa aynı komut kaldığı yerden devam eder.

## 4. Sonucu gönder

Çıktı: `ideal/outputs/pilot.jsonl`. Deneme turundaki gibi yükle:

- GitHub → dal `claude/repodaki-project-analysis-al4o1f` → `ideal` klasörü → **Add file → Upload files**.
- Dosyayı sürüklerken klasör yolunun `ideal/outputs/` olmasına dikkat et.
- **Commit changes**.

Sonra bana haber ver. Metinleri okurum, altın küme adaylarını seçerim ve gerekirse istemi düzeltirim. Büyük koşunun komutlarını ondan sonra veririm.

## Sorun giderme

| Mesaj | Ne yapmalı |
|---|---|
| `MISTRAL_API_KEY tanımlı değil` | Bölüm 2'deki `$env:…` satırını bu pencerede yeniden çalıştır |
| `Anahtar geçersiz (401)` | Anahtarı konsoldan yeniden kopyala; gerekirse yeni bir anahtar oluştur |
| `Model … bu anahtarla kullanılamıyor` | Ekrandaki model listesini bana gönder |
| `hata (…); sonra aynı komutla yeniden denenir` | Ağ sorunu olabilir; komutu yeniden çalıştır |
| Ekran uzun süre değişmiyor | Pencereye tıklandıysa Windows ekrana yazmayı durdurur; pencereye tıkla ve **Esc**'ye bas |
