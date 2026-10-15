# 05 — `facts.json` şeması (Katman 1 çıktısı)

> **Durum:** Şema 1.0 **[KARAR, tur 5]**. Kodlandı: `facts/` · Testler: `tests/test_facts.py` · Tam örnek: [`examples/facts_A1-v00_2025-06.json`](examples/facts_A1-v00_2025-06.json)
>
> **Tarih:** 15.10.2026 · **İlgili:** CLAUDE.md 6.2 (Katman 1), `docs/03` 9.1 (V2 adayı), `docs/02` (satır anahtarları)

---

## 1. İlkeler [KARAR, tur 4–5]

1. **Modelin bütün rakamları buradan gelir.** Model hiçbir rakamı kendisi hesaplamaz (CLAUDE.md 6.1). `facts.json`'da geçen her rakam, Katman 4'te geçerli rakam sayılır.
2. **Katman 1 yalnızca modele görünür dosyaları okur** (`model_input/bwa_raw.csv`, `model_input/firms.json`). Ground truth `facts.json`'a hiç girmez: olay kimliği, beklenen uyarı veya "doğru cevap" yoktur.
   - Rohertrag adayları nötr "aday" (`kandidat`) olarak işaretlenir. Notla açıklanıp açıklanmadığına model karar verir; doğru karar yalnızca `ground_truth_months.jsonl`'dadır.
   - Diğer bayraklar yalnızca gözlem ve kanıt içerir (`hinweis`).
3. **Biçim:**
   - Tutarlar tam sayı €, yüzdeler ve yüzde puanları 1 ondalık, `schema_version` zorunlu.
   - Eşik karşılaştırmaları yuvarlanmamış değerlerle yapılır; yalnızca çıktı yuvarlanır.
4. **Satır adları** kanonik Almanca addır (`docs/02`, D1); yanında makine anahtarı (`key`) bulunur. Açıklama metinleri (`reason`, `evidence`) Almancadır.

---

## 2. Eşikler ve anlamlılık [KARAR, tur 4–5]

| Kural | Değer |
|---|---|
| Kalem anlamlı | **Önceki yılın aynı ayına göre** \|Δ\| ≥ %10 **ve** \|Δ\| ≥ cari ayın Gesamtleistung'unun %0,5'i |
| Önceki ay, kümülatif | Yalnızca bilgi amaçlı; sıralamaya ve seçime girmez |
| Oran anlamlı | Önceki yılın aynı ayına göre ≥ 2 yüzde puanı |
| Yorumdaki kalem sayısı | En fazla 5; önceki yılın aynı ayına göre \|Δ €\| büyüklüğüne göre sıralı |
| Rohertrag adayı | Rohertragsquote hem önceki aya **hem** önceki yılın aynı ayına göre ≥ 2 puan değişmiş. Bütün arketiplerde, nötr. |
| `delta_pct = null` | Sonuç satırlarında (Betriebsergebnis, Ergebnis vor Steuern, Vorläufiges Ergebnis) her zaman. Diğer satırlarda taban küçükse (\|taban\| < mutlak eşik) veya işaret değiştiriyorsa. |

**Referans veride sonuç** (seed 42, 720 yorumlanabilir firma-ay; `python -m facts --run data/synthetic/reference_seed42`):

| Ölçüt | Değer |
|---|---|
| Anlamlı kalem sayısı (medyan) | 3 |
| 0 kalemli ay | %4,3 |
| 5'ten fazla kalemli ay (5 kalem sınırı devreye giriyor) | %3,6 |

Karşılaştırma için: "önceki ay VEYA önceki yılın aynı ayı" kuralıyla hiçbir ayda 0 kalem çıkmıyordu, ayların %22'sinde ise 5'ten fazla kalem vardı (tur 4 analizi).

---

## 3. Yapı

### 3.1 Üst düzey alanlar

| Alan | Açıklama |
|---|---|
| `schema_version` | `"1.0"` |
| `company` | `firm_id`, `name` |
| `period`, `period_label` | `"2025-06"`, `"Juni 2025"` |
| `comparisons` | Önceki ay, önceki yılın aynı ayı, kümülatif (Ocak–cari ay) ve önceki yılın kümülatifi |
| `thresholds` | `significance_basis` (`previous_year_month`), göreli eşik, € olarak hesaplanmış mutlak eşikler (aylık ve kümülatif), oran eşiği, en fazla kalem sayısı |
| `summary` | Gesamtleistung, Rohertrag, Gesamtkosten, Betriebsergebnis, Ergebnis vor Steuern, Vorläufiges Ergebnis. Her zaman var, sıralanmaz. |
| `positions` | Anlamlı temel satırlar, sıralı, en fazla 5 |
| `further_significant` | 5'in dışında kalan anlamlı satırlar (`rank`, `key`, `position`) |
| `ratios` | Rohertragsquote, Materialquote, Personalkostenquote, Betriebsergebnis-Marge |
| `flags` | Çarpıklık bayrakları ve Rohertrag adayı (Bölüm 4) |

### 3.2 Kalem nesnesi (`summary` ve `positions`)

| Alan | Açıklama |
|---|---|
| `rank` | Yalnızca `positions`'ta |
| `key`, `position` | Makine anahtarı ve kanonik ad |
| `actual` | Cari ay değeri |
| `normal_level` | Önceki 12 ayın medyanı |
| `previous_month` | `value`, `delta_abs`, `delta_pct`, `base_unusual` (bilgi amaçlı, anlamlılık yok) |
| `previous_year_month` | `value`, `delta_abs`, `delta_pct`, **`significant`**, `base_unusual` |
| `cumulative` | `actual`, `previous_year`, `delta_abs`, `delta_pct`, `significant`. Bilgi amaçlı; mutlak eşik kümülatif Gesamtleistung'un %0,5'i. |
| `significance` | Yalnızca `positions`'ta: `basis` ve Almanca gerekçe (`reason`) |

- **`base_unusual`:** Karşılaştırma tabanı normal düzeyden anlamlı biçimde (≥ %10 ve ≥ mutlak eşik) sapıyor mu?
  - Önceki ay tabanı için normal düzey, cari ayın normal düzeyidir.
  - Önceki yılın aynı ayı tabanı için normal düzey, o aydan önceki 12 ayın medyanıdır (en az 6 ay geçmiş varsa; yoksa cari ayın normal düzeyi).

### 3.3 Oran nesnesi

`ratio`, `actual`, `previous_month` (`value`, `delta_pp`), `previous_year_month` (`value`, `delta_pp`, `significant`), `cumulative` (`actual`, `previous_year`, `delta_pp`, `significant`).

---

## 4. Bayraklar

Her bayrağın alanları şunlar: `code`, `status` (`hinweis` | `kandidat`), `rule`, `position`, `evidence` (Almanca, rakamlı gözlem).

Kural parametreleri **[ÖNERİ]** `facts/config.toml`'dadır.

| Kod | `rule` | Kural | `status` |
|---|---|---|---|
| V1 | `wiederkehrende_spitze` | Sabit gider satırı ≥ 1,25 × normal düzey **ve** önceki yılın aynı ayında da ≥ 1,25 × normal düzey | `hinweis` |
| V2 | `bestand_fehlt` | Üretici (geçmişte stok değişimi kaydedilmiş): bu ay stok değişimi 0 iken Material-/Wareneinkauf önceki aya veya önceki yılın aynı ayına göre anlamlı değişmiş | `hinweis` |
| V2 | `rohertrag_sprung` | Rohertragsquote önceki aya **ve** önceki yılın aynı ayına göre ≥ 2 puan değişmiş. Bütün arketiplerde. | **`kandidat`** |
| V3 | `afa_fehlt` | AfA, son 12 ayın aylık ortalamasının %10'unun altında | `hinweis` |
| V3 | `afa_jahresbuchung` | AfA ≥ 3 × aylık ortalama ve son 11 ayın en az 6'sında AfA yok | `hinweis` |
| V4 | `zeitverschiebung` | Materialquote önceki ay normalin ≥ 2 puan altında, bu ay ≥ 2 puan üstünde; ya da sabit gider satırı önceki ay normal düzeyin ≥ %10 altında, bu ay ≥ %10 üstünde | `hinweis` |
| V4 | `bestand_nachbuchung` | Üretici: stok değişimi önceki ay 0, bu ay ≥ mutlak eşik | `hinweis` |
| V5 | `einmalige_spitze` | Sabit gider satırı ≥ 2 × normal düzey, önceki yılın aynı ayında benzer sıçrama yok | `hinweis` |
| V6 | `saisonal` | Umsatzerlöse önceki aya göre anlamlı değişmiş (≥ %10 ve ≥ mutlak eşik), önceki yılın aynı ayına göre < %15 | `hinweis` |

- Sabit gider satırları: Personalkosten, Raumkosten, Betriebliche Steuern, Versicherungen/Beiträge, Besondere Kosten, Fahrzeugkosten, Werbe-/Reisekosten, Reparatur/Instandhaltung, Sonstige Kosten.
- Ciroya bağlı satırlar (Material, Kosten der Warenabgabe) V1/V5'e girmez; aksi halde sezon dalgası sıçrama sanılır.
- Abschreibungen V3 ile ele alınır.

---

## 5. Örnek: Muster GmbH, Haziran 2025 (referans koşu)

Tam çıktı: [`examples/facts_A1-v00_2025-06.json`](examples/facts_A1-v00_2025-06.json). Bu dosya `python -m facts` ile üretilir; bir test, dosyanın güncel olduğunu kontrol eder. Aşağıda kısaltılmış hali var (`…`).

```json
{
  "schema_version": "1.0",
  "company": {"firm_id": "A1-v00", "name": "Muster GmbH"},
  "period": "2025-06",
  "period_label": "Juni 2025",
  "comparisons": {
    "previous_month": "2025-05", "previous_year_month": "2024-06",
    "cumulative": "2025-01 – 2025-06", "cumulative_previous_year": "2024-01 – 2024-06"
  },
  "thresholds": {
    "significance_basis": "previous_year_month", "position_rel_pct": 10.0,
    "position_abs_eur": 4355, "cumulative_abs_eur": 22537, "ratio_pp": 2.0, "max_positions": 5
  },
  "summary": [
    {
      "key": "gesamtleistung", "position": "Gesamtleistung", "actual": 870947, "normal_level": 702126,
      "previous_month":      {"value": 682843, "delta_abs": 188104, "delta_pct": 27.5, "base_unusual": false},
      "previous_year_month": {"value": 746309, "delta_abs": 124638, "delta_pct": 16.7, "significant": true, "base_unusual": false},
      "cumulative": {"actual": 4507355, "previous_year": 4222203, "delta_abs": 285152, "delta_pct": 6.8, "significant": false}
    },
    "… Rohertrag, Gesamtkosten …",
    {
      "key": "betriebsergebnis", "position": "Betriebsergebnis", "actual": -56003, "normal_level": -67878,
      "previous_month":      {"value": -79756,  "delta_abs": 23753, "delta_pct": null, "base_unusual": true},
      "previous_year_month": {"value": -104366, "delta_abs": 48363, "delta_pct": null, "significant": true, "base_unusual": true},
      "cumulative": {"actual": -176065, "previous_year": -42537, "delta_abs": -133528, "delta_pct": null, "significant": true}
    },
    "… Ergebnis vor Steuern, Vorläufiges Ergebnis …"
  ],
  "positions": [
    {
      "rank": 1, "key": "umsatzerloese", "position": "Umsatzerlöse", "actual": 886365, "normal_level": 702446,
      "previous_month":      {"value": 682843, "delta_abs": 203523, "delta_pct": 29.8, "base_unusual": false},
      "previous_year_month": {"value": 744725, "delta_abs": 141640, "delta_pct": 19.0, "significant": true, "base_unusual": false},
      "cumulative": {"actual": 4510044, "previous_year": 4211994, "delta_abs": 298050, "delta_pct": 7.1, "significant": false},
      "significance": {
        "basis": "previous_year_month",
        "reason": "Vorjahresmonat +141.640 € (+19,0 %); Schwelle: ≥ 10,0 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    },
    "… rank 2: Material-/Wareneinkauf (Vorjahresmonat +63.912 €, +16,8 %) …",
    "… rank 3: Bestandsveränderungen FE/UE (Vorjahresmonat -17.002 €, delta_pct null) …",
    {
      "rank": 4, "key": "werbe_reisekosten", "position": "Werbe-/Reisekosten", "actual": 4303, "normal_level": 4211,
      "previous_month":      {"value": 4185,  "delta_abs": 117,   "delta_pct": null,  "base_unusual": false},
      "previous_year_month": {"value": 10942, "delta_abs": -6640, "delta_pct": -60.7, "significant": true, "base_unusual": true},
      "cumulative": {"actual": 25411, "previous_year": 41401, "delta_abs": -15990, "delta_pct": -38.6, "significant": false},
      "significance": {
        "basis": "previous_year_month",
        "reason": "Vorjahresmonat -6.640 € (-60,7 %); Schwelle: ≥ 10,0 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    }
  ],
  "further_significant": [],
  "ratios": [
    "… Rohertragsquote 48,9 % (Vorjahresmonat 48,9 %), Materialquote …",
    {
      "ratio": "Personalkostenquote", "actual": 40.6,
      "previous_month":      {"value": 35.0, "delta_pp": 5.5},
      "previous_year_month": {"value": 45.0, "delta_pp": -4.4, "significant": true},
      "cumulative": {"actual": 33.7, "previous_year": 32.5, "delta_pp": 1.3, "significant": false}
    },
    "… Betriebsergebnis-Marge …"
  ],
  "flags": [
    {
      "code": "V1", "status": "hinweis", "rule": "wiederkehrende_spitze", "position": "Personalkosten",
      "evidence": "Personalkosten 353.499 € = 1,5-faches des Normalniveaus (228.780 €); Vorjahresmonat ebenfalls erhöht (335.873 €)"
    },
    {
      "code": "V4", "status": "hinweis", "rule": "bestand_nachbuchung", "position": "Bestandsveränderungen FE/UE",
      "evidence": "Bestandsveränderungen April und Mai je 0 €, Juni -15.419 €: möglicherweise Buchung für mehrere Monate"
    }
  ]
}
```

**Bu örnekte modelin görmesi gerekenler** (ground truth ile karşılaştırma):

| `facts.json`'daki işaret | Ground truth | Modelden beklenen |
|---|---|---|
| Umsatz +%19 (önceki yılın aynı ayına göre) | E05 (notlu: "Die Verkaufspreise wurden ab Juni um rund 5 % angehoben."), E06 (notlu) | Kaynakla açıklama |
| Personalkosten: kalem değil (önceki yıla göre +%5,2), ama V1 bayrağı | E13 Urlaubsgeld, `expected_flags: V1` | Uyarı dili, Buchhaltung'a soru |
| Bestandsveränderungen (3. sıra) + V4 bayrağı | E16 çeyreklik, `expected_flags: V4` | Uyarı dili |
| Werbe-/Reisekosten −%60,7, `base_unusual` (önceki yıl tabanı) | `vorjahr_events`: Haziran 2024 fuarı (notlu) | Önceki yıl etkisi; bu yıl normal |
| Reparatur: kalem değil (önceki yıla göre +%1,4) | Mayıs'taki E12 (geçen ay) | (önceki ay farkı bilgi amaçlı; yorumda öne çıkmaz) |

### 5.1 Rohertrag adayı örneği (dengelenmiş V2 kümesi, A2-v51, Mart 2025)

```json
{
  "code": "V2", "status": "kandidat", "rule": "rohertrag_sprung", "position": "Rohertragsquote",
  "evidence": "Rohertragsquote 19,5 % (Vormonat 23,3 %, Vorjahresmonat 28,9 %); Veränderung -3,8 Prozentpunkte bzw. -9,4 Prozentpunkte"
}
```

- Aynı ayın bağlam notu: "Deutliche Preissteigerungen bei Kupferrohr ab März; eine Weitergabe an die Kunden wird geprüft. Der Zuschlag gilt voraussichtlich nur für einige Monate."
- Ground truth: `v2_candidate_decision = cite`. Model nedeni nota dayanarak açıklamalı ve stok uyarısı vermemeli.
- `facts.json` bu doğru cevabı içermez.

---

## 6. Kullanım

```bash
python -m facts --run data/synthetic/reference_seed42 --firm A1-v00 --period 2025-06   # tek ay, ekrana
python -m facts --run data/synthetic/reference_seed42                                   # bütün aylar → <run>/facts/facts.jsonl
python tools/flag_quality.py data/synthetic/reference_seed42                            # bayrak isabeti (ground truth okur)
```

- `<run>/facts/` repoda tutulmaz (`.gitignore`); her zaman yeniden üretilebilir.
- facts.json yalnızca önceki yılın aynı ayı bulunan aylar için üretilir (2025-01'den itibaren).

---

## 7. Bayrak isabeti (referans koşu) [ÖNERİ parametreleriyle]

`tools/flag_quality.py` ile ölçüldü. Ölçüm firma-ay ve bayrak kodu düzeyinde yapıldı.

- **Precision:** Bayrak verilen aylardan kaçında ground truth bu bayrağı bekliyor veya kabul ediyor?
- **Recall:** Beklenen bayrakların kaçı verildi?
- **"Eşik üstü":** Yalnızca o aydaki etkisi Gesamtleistung'un %0,5'ini aşan çarpıklıklar.

| Kod | Bayraklı ay | Precision | Recall | Recall (eşik üstü) | Not |
|---|---:|---:|---:|---:|---|
| V1 | 146 | %80 | %98 | %98 | Yanlış alarmların bir kısmı tesadüfen aynı ayda tekrarlanan tek seferlik giderler |
| V2 (`bestand_fehlt`) | 60 | %100 | %77 | %77 | Yalnızca üreticiler; ticarette V2'nin karşılığı Rohertrag adayı |
| V3 | 336 | %100 | %100 | %100 | |
| V4 | 174 | %91 | %61 | %64 | Küçük geç fatura kaymaları (%5–20) Materialquote'yi 2 puandan az oynatıyor |
| V5 | 138 | %100 | %70 | %72 | İki aya bölünmüş fuarların ilk ayı ve A3'ün her yıl tekrarlanan fuarı (V1 olarak işaretleniyor; kabul edilebilir) kaçıyor |
| V6 | 309 | %72 | %63 | %63 | Önceki yıl sınırı %10'dan %15'e çekildi (önceden precision %75, recall %49) |

**Rohertrag adayı** (439 firma-ay), ground truth kararına göre:

| Arketip | warn | cite | either | None (Rohertragsquote'yi değiştiren olay yok; gürültü) |
|---|---:|---:|---:|---:|
| A1 | 88 | 6 | 7 | 14 |
| A2 | 177 | 0 | 1 | 8 |
| A3 | 85 | 13 | 7 | 33 |

`cite` vakası ana veride az. Bu nedenle ayrım metriği dengelenmiş V2 kümesiyle ölçülüyor (`docs/04`, Bölüm 8).
