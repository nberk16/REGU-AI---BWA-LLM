# 05 — `facts.json` şeması (Katman 1 çıktısı)

> **Durum:** Şema **[ÖNERİ — kullanıcı onayı bekleniyor]**. Katman 1 modülü, şema onaylandıktan sonra yazılacak.
> Eşikler **[KARAR, tur 4 — başlangıç değerleri]**; referans veriye göre kalibre edilebilir.
>
> **Tarih:** 15.10.2026 · **İlgili:** CLAUDE.md 6.2 (Katman 1), `docs/03` 9.1 (V2 adayı), `docs/02` (satır anahtarları)

---

## 1. İlkeler

1. **Modelin bütün rakamları buradan gelir.** Model hiçbir rakamı kendisi hesaplamaz (CLAUDE.md 6.1). `facts.json`'da geçen her rakam, Katman 4'te geçerli rakam sayılır.
2. **Ground truth `facts.json`'a hiç girmez.** Olay kimliği, beklenen uyarı veya "doğru cevap" yoktur.
   - Rohertrag adayları nötr "aday" (`kandidat`) olarak işaretlenir. Notla açıklanıp açıklanmadığına model karar verir; doğru karar yalnızca `ground_truth_months.jsonl`'dadır [KARAR, tur 4].
   - Diğer bayraklar da yalnızca gözlem ve kanıt içerir (`hinweis`); öneri veya sonuç içermez.
3. **Biçim [KARAR, tur 4]:**
   - Tutarlar tam sayı €.
   - Yüzdeler ve yüzde puanları 1 ondalık.
   - `schema_version` alanı zorunlu.
   - Eşik karşılaştırmaları yuvarlanmamış değerlerle yapılır; yalnızca çıktı yuvarlanır.
4. **Satır adları** kanonik Almanca addır (`docs/02`, D1). Yanında makine anahtarı (`key`) bulunur.
5. **Açıklama metinleri Almancadır** (`reason`, `evidence`): Almanca sayı biçimi, model girdisi diliyle aynı.

---

## 2. Eşikler [KARAR, tur 4 — başlangıç değerleri]

| Eşik | Değer |
|---|---|
| Kalem anlamlı | \|Δ\| ≥ %10 **ve** \|Δ\| ≥ cari ayın Gesamtleistung'unun %0,5'i |
| Oran anlamlı | \|Δ\| ≥ 2 yüzde puanı |
| Yorumdaki kalem sayısı | En fazla 5, büyüklüğe göre sıralı |
| Rohertrag adayı | Rohertragsquote hem önceki aya hem önceki yılın aynı ayına göre ≥ 2 puan değişmiş (`docs/03` 9.1) |

### 2.1 Referans veride sonuç (seed 42, 720 yorumlanabilir firma-ay, 21 temel satır)

| Anlamlılık hangi karşılaştırmayla? | 0 kalemli ay | 5'ten fazla kalemli ay | Medyan kalem | Olaysız aylarda 0 kalem |
|---|---|---|---|---|
| **Önceki ay VEYA önceki yılın aynı ayı** (kararın harfiyen uygulanması) | %0,0 | %22,1 | 4 | %0,0 |
| Yalnızca önceki yılın aynı ayı | %3,2 | %3,6 | 3 | %8,1 |
| İkisi birden | %12,5 | %0,4 | 2 | %24,3 |
| (karşılaştırma) %15 / %1 GL, VEYA | %0,8 | %7,4 | 3 | %1,8 |

**Gözlem:**
- Önceki aya göre karşılaştırma işe karıştığında mevsim dalgalanması neredeyse her ayı "hareketli" gösteriyor.
  - Hiçbir ayda 0 kalem çıkmıyor; ayların %22'sinde 5 kalem sınırı devreye giriyor.
  - Olaysız aylarda da (yeni olay yok) her zaman anlamlı kalem var. Model bu aylarda "olay yok, mevsim etkisi" demeyi öğrenmeli; V6 bayrağı burada yardımcı olur.
- **Önerim:** Anlamlılık ve sıralama **önceki yılın aynı ayına** göre yapılsın. Önceki ay karşılaştırması her kalemde bilgi olarak dursun; V6 ve "baz etkisi" (`base_unusual`) bu karşılaştırmayı açıklasın. Bu ayarla aylarda medyan 3 kalem çıkıyor; %3,2'sinde 0, %3,6'sında 5'ten fazla. **[AÇIK — kullanıcıya soruldu]**

---

## 3. Yapı

### 3.1 Üst düzey alanlar

| Alan | Tür | Açıklama |
|---|---|---|
| `schema_version` | metin | Şema sürümü, ör. `"1.0"` |
| `company` | nesne | `firm_id`, `name` |
| `period`, `period_label` | metin | `"2025-06"`, `"Juni 2025"` |
| `comparisons` | nesne | Karşılaştırma dönemleri: önceki ay, önceki yılın aynı ayı, kümülatif (Ocak–cari ay) ve önceki yılın kümülatifi |
| `thresholds` | nesne | Bu ayda kullanılan eşikler; mutlak eşik € olarak hesaplanmış haliyle |
| `summary` | dizi | Ara toplam ve sonuç satırları: Gesamtleistung, Rohertrag, Gesamtkosten, Betriebsergebnis, Ergebnis vor Steuern, Vorläufiges Ergebnis. Her zaman var, sıralanmaz. |
| `positions` | dizi | Anlamlı temel satırlar; büyüklüğe göre sıralı, en fazla 5 |
| `further_significant` | dizi | 5'in dışında kalan anlamlı satırlar (yalnızca ad ve sıra) |
| `ratios` | dizi | Rohertragsquote, Materialquote, Personalkostenquote, Betriebsergebnis-Marge |
| `flags` | dizi | Çarpıklık bayrakları ve Rohertrag adayı (Bölüm 4) |

### 3.2 Kalem nesnesi (`summary` ve `positions`)

| Alan | Açıklama |
|---|---|
| `key`, `position` | Makine anahtarı ve kanonik ad |
| `rank` | Yalnızca `positions`'ta: büyüklük sırası (anlamlı karşılaştırmalardaki en büyük \|Δ €\|) |
| `actual` | Cari ay değeri |
| `normal_level` | Önceki 12 ayın medyanı. "Normal düzey"; tek seferlik sapmaları ve normale dönüşü görünür kılar. **[ÖNERİ, yeni]** |
| `previous_month`, `previous_year_month` | Karşılaştırma: `value`, `delta_abs`, `delta_pct`, `significant`, `base_unusual` |
| `cumulative` | `actual`, `previous_year`, `delta_abs`, `delta_pct`, `significant`. Kümülatif için mutlak eşik, kümülatif Gesamtleistung'un %0,5'i. Bilgi amaçlıdır; sıralamaya girmez. |
| `significance` | Yalnızca `positions`'ta: hangi karşılaştırmalarda anlamlı olduğu ve Almanca gerekçe metni |

- `base_unusual` **[ÖNERİ, yeni]:** Karşılaştırma tabanı normal düzeyden anlamlı biçimde sapıyor mu? Örneğin geçen ayki tek seferlik onarım veya geçen yılın aynı ayındaki fuar. Model bununla "baz etkisi"ni açıklayabilir.
- `delta_pct = null` **[ÖNERİ]:**
  - Tabanın mutlak değeri mutlak eşiğin altındaysa veya taban ile cari değerin işareti farklıysa (ör. stok değişimi 1.583 € → −15.419 €; yüzde −1.073,9 olurdu).
  - Sonuç satırlarında (Betriebsergebnis, Ergebnis vor Steuern, Vorläufiges Ergebnis) her zaman. Bu satırlar yorumda mutlak farkla anlatılır ("42 T€ unter Vorjahresmonat").

### 3.3 Oran nesnesi

`ratio`, `actual`, `previous_month` / `previous_year_month` (`value`, `delta_pp`, `significant`) ve `cumulative` (`actual`, `previous_year`, `delta_pp`, `significant`).

---

## 4. Bayraklar

Her bayrağın alanları şunlar:

- `code`: V1–V6
- `status`: `hinweis` ya da `kandidat`
- `rule`: hangi kuralın tetiklendiği
- `position`: ilgili satır veya oran
- `evidence`: Almanca, rakamlı gözlem

Kural parametreleri **[ÖNERİ]**; kodlama sırasında referans veriyle kalibre edilecek.

| Kod | `rule` | Kural (taslak) | `status` |
|---|---|---|---|
| V1 | `wiederkehrende_spitze` | Satır ≥ 1,25 × normal düzey **ve** önceki yılın aynı ayında da benzer sıçrama | `hinweis` |
| V2 | `bestand_fehlt` (üretici) | Bestandsveränderungen = 0 iken Material-/Wareneinkauf anlamlı değişmiş | `hinweis` |
| V2 | `rohertrag_sprung` (Rohertrag adayı) | Rohertragsquote önceki aya **ve** önceki yılın aynı ayına göre ≥ 2 puan değişmiş | **`kandidat`** |
| V3 | `afa_fehlt` | Abschreibungen bu ay ve önceki 2 ayda 0 (veya normal düzeyin %10'unun altında), önceki yıl > 0 | `hinweis` |
| V4 | `zeitverschiebung` | Önceki ay normal düzeyin anlamlı altında, bu ay anlamlı üstünde (veya tersi) | `hinweis` |
| V4 | `bestand_nachbuchung` | Stok değişimi önceki 2 ayda 0, bu ay ≠ 0 | `hinweis` |
| V5 | `einmalige_spitze` | Satır ≥ 2 × normal düzey, önceki yılın aynı ayında sıçrama yok | `hinweis` |
| V6 | `saisonal` | Umsatzerlöse önceki aya göre anlamlı değişmiş, önceki yılın aynı ayına göre değişmemiş | `hinweis` |

**Açık soru:** Rohertrag adayı (`rohertrag_sprung`) yalnızca A2 (ticaret) için mi üretilsin, yoksa bütün arketipler için mi? **[AÇIK — kullanıcıya soruldu]**
- Tur 2 kararına göre üreticide V2 için mevcut kural (`bestand_fehlt`) geçerli.
- Önerim: Aday her arketipte nötr olarak üretilsin, `bestand_fehlt` üreticide ayrıca dursun. Aday kuralı tamamen sayısal ve nötr olduğu için çelişki yaratmaz. Böylece "V2 adayı ayrımı" metriği hangi arketip test için ayrılırsa ayrılsın ölçülebilir; dengelenmiş V2 kümesi de üç arketipi içeriyor.

---

## 5. Örnek: Muster GmbH, Haziran 2025 (referans koşu)

Bu ayda aynı anda şunlar var:
- notlu bir satış fiyatı artışı ve büyük sipariş (E05, E06)
- tahakkuksuz Urlaubsgeld (E13 → V1)
- çeyrek sonu stok kaydı (E16 → V4)
- Mayıs'taki büyük onarımdan kalan baz etkisi
- geçen Haziran'daki fuardan kalan önceki yıl etkisi

Değerler bir prototip betikle hesaplandı. Kısaltılmış yerler `…` ile gösterildi. Eşikler kararın harfiyen uygulanmasıyla (önceki ay VEYA önceki yılın aynı ayı) uygulandı.

```json
{
  "schema_version": "1.0",
  "company": {"firm_id": "A1-v00", "name": "Muster GmbH"},
  "period": "2025-06",
  "period_label": "Juni 2025",
  "comparisons": {
    "previous_month": "2025-05",
    "previous_year_month": "2024-06",
    "cumulative": "2025-01 – 2025-06",
    "cumulative_previous_year": "2024-01 – 2024-06"
  },
  "thresholds": {
    "position_rel_pct": 10.0,
    "position_abs_eur": 4355,
    "cumulative_abs_eur": 22537,
    "ratio_pp": 2.0,
    "max_positions": 5
  },
  "summary": [
    {
      "key": "gesamtleistung", "position": "Gesamtleistung",
      "actual": 870947, "normal_level": 702126,
      "previous_month":      {"value": 682843, "delta_abs": 188104, "delta_pct": 27.5, "significant": true, "base_unusual": false},
      "previous_year_month": {"value": 746309, "delta_abs": 124638, "delta_pct": 16.7, "significant": true, "base_unusual": false},
      "cumulative": {"actual": 4507355, "previous_year": 4222203, "delta_abs": 285152, "delta_pct": 6.8, "significant": false}
    },
    "… Rohertrag, Gesamtkosten …",
    {
      "key": "betriebsergebnis", "position": "Betriebsergebnis",
      "actual": -56003, "normal_level": -67878,
      "previous_month":      {"value": -79756,  "delta_abs": 23753, "delta_pct": null, "significant": true, "base_unusual": true},
      "previous_year_month": {"value": -137506, "delta_abs": 81504, "delta_pct": null, "significant": true, "base_unusual": true},
      "cumulative": {"actual": -176065, "previous_year": -42537, "delta_abs": -133528, "delta_pct": null, "significant": true}
    },
    "… Ergebnis vor Steuern, Vorläufiges Ergebnis …"
  ],
  "positions": [
    {
      "rank": 1, "key": "umsatzerloese", "position": "Umsatzerlöse",
      "actual": 886365, "normal_level": 702446,
      "previous_month":      {"value": 682843, "delta_abs": 203523, "delta_pct": 29.8, "significant": true, "base_unusual": false},
      "previous_year_month": {"value": 744725, "delta_abs": 141640, "delta_pct": 19.0, "significant": true, "base_unusual": false},
      "cumulative": {"actual": 4510044, "previous_year": 4211994, "delta_abs": 298050, "delta_pct": 7.1, "significant": false},
      "significance": {
        "comparisons": ["previous_month", "previous_year_month"],
        "reason": "Vormonat +203.523 € (+29,8 %); Vorjahresmonat +141.640 € (+19,0 %); Schwelle: ≥ 10 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    },
    {
      "rank": 2, "key": "personalkosten", "position": "Personalkosten",
      "actual": 353499, "normal_level": 228780,
      "previous_month":      {"value": 239296, "delta_abs": 114203, "delta_pct": 47.7, "significant": true,  "base_unusual": false},
      "previous_year_month": {"value": 335873, "delta_abs": 17626,  "delta_pct": 5.2,  "significant": false, "base_unusual": true},
      "cumulative": {"actual": 1519877, "previous_year": 1370334, "delta_abs": 149543, "delta_pct": 10.9, "significant": true},
      "significance": {
        "comparisons": ["previous_month"],
        "reason": "Vormonat +114.203 € (+47,7 %); Schwelle: ≥ 10 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    },
    "… rank 3: Material-/Wareneinkauf (Vormonat +98.126 €, +28,3 %) …",
    {
      "rank": 4, "key": "reparatur_instandhaltung", "position": "Reparatur/Instandhaltung",
      "actual": 15250, "normal_level": 15359,
      "previous_month":      {"value": 65598, "delta_abs": -50347, "delta_pct": -76.8, "significant": true,  "base_unusual": true},
      "previous_year_month": {"value": 15042, "delta_abs": 208,    "delta_pct": 1.4,   "significant": false, "base_unusual": false},
      "cumulative": {"actual": 142431, "previous_year": 167393, "delta_abs": -24961, "delta_pct": -14.9, "significant": true},
      "significance": {
        "comparisons": ["previous_month"],
        "reason": "Vormonat -50.347 € (-76,8 %); Schwelle: ≥ 10 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    },
    {
      "rank": 5, "key": "bestandsveraenderungen_fe_ue", "position": "Bestandsveränderungen FE/UE",
      "actual": -15419, "normal_level": 0,
      "previous_month":      {"value": 0,    "delta_abs": -15419, "delta_pct": null, "significant": true, "base_unusual": false},
      "previous_year_month": {"value": 1583, "delta_abs": -17002, "delta_pct": null, "significant": true, "base_unusual": false},
      "cumulative": {"actual": -2688, "previous_year": 10210, "delta_abs": -12898, "delta_pct": null, "significant": false},
      "significance": {
        "comparisons": ["previous_month", "previous_year_month"],
        "reason": "Vormonat -15.419 € (n. a.); Vorjahresmonat -17.002 € (n. a.); Schwelle: ≥ 10 % und ≥ 4.355 € (0,5 % der Gesamtleistung)"
      }
    }
  ],
  "further_significant": [
    {"rank": 6, "key": "werbe_reisekosten", "position": "Werbe-/Reisekosten"}
  ],
  "ratios": [
    {
      "ratio": "Rohertragsquote", "actual": 48.9,
      "previous_month":      {"value": 49.2, "delta_pp": -0.3, "significant": false},
      "previous_year_month": {"value": 44.5, "delta_pp": 4.4,  "significant": true},
      "cumulative": {"actual": 48.6, "previous_year": 52.4, "delta_pp": -3.8, "significant": true}
    },
    "… Materialquote …",
    {
      "ratio": "Personalkostenquote", "actual": 40.6,
      "previous_month":      {"value": 35.0, "delta_pp": 5.6,  "significant": true},
      "previous_year_month": {"value": 45.0, "delta_pp": -4.4, "significant": true},
      "cumulative": {"actual": 33.7, "previous_year": 32.5, "delta_pp": 1.2, "significant": false}
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

| `facts.json`'daki işaret | Ground truth (`ground_truth_months.jsonl`) | Modelden beklenen |
|---|---|---|
| Umsatz +%19 (önceki yılın aynı ayına göre) | E05 (notlu: "Verkaufspreise … um rund 5 % angehoben"), E06 (notlu) | Kaynakla açıklama |
| Personalkosten +%47,7 (önceki aya göre) + V1 | E13 Urlaubsgeld, `expected_flags: V1` | Uyarı dili, Buchhaltung'a soru |
| Reparatur −%76,8 (önceki aya göre), `base_unusual` | Mayıs'taki E12 (geçen ay, tek seferlik) | Normale dönüş; neden uydurmamak |
| Bestandsveränderungen + V4 | E16 çeyreklik, `expected_flags: V4` | Uyarı dili |
| Werbe-/Reisekosten (6. sıra, yorumda yok) | `vorjahr_events`: Haziran 2024 fuarı | (5 kalem sınırı nedeniyle yorumda yer almaz) |

### 5.1 Rohertrag adayı örneği (dengelenmiş V2 kümesi, A2-v51, Eylül 2026)

```json
"flags": [
  {
    "code": "V2", "status": "kandidat", "rule": "rohertrag_sprung", "position": "Rohertragsquote",
    "evidence": "Rohertragsquote 22,9 % (Vormonat 17,6 %, Vorjahresmonat 24,9 %); Veränderung +5,3 bzw. -2,0 Prozentpunkte"
  }
]
```

- Aynı ayın bağlam notu: `Kontextnotiz 2026-09`: "Preisanpassung bei den wichtigsten Kunden ab September durchgesetzt."
- Ground truth: `v2_candidate_decision = cite`. Model nedeni nota dayanarak açıklamalı ve stok uyarısı vermemeli.
- `facts.json` bu doğru cevabı içermez.

---

## 6. Onay bekleyen sorular

1. **Anlamlılık hangi karşılaştırmaya göre?**
   - Kararın harfiyen uygulanması (önceki ay VEYA önceki yılın aynı ayı): ayların %22'sinde 5'ten fazla kalem, hiçbir ayda 0 kalem.
   - Önerim: yalnızca önceki yılın aynı ayı (Bölüm 2.1).
2. **Rohertrag adayı bütün arketiplerde mi?** Önerim: evet, nötr (Bölüm 4).
3. **Yeni alanlar:** `normal_level` ve `base_unusual`. Önerim: eklensin.
4. **`delta_pct = null` kuralları:** küçük ya da işaret değiştiren tabanlarda ve sonuç satırlarında. Önerim: uygulansın.
5. **Kümülatif karşılaştırma** yalnızca bilgi amaçlı, sıralamaya girmez. Önerim: böyle kalsın.
