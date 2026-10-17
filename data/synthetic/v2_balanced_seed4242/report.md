# Sentetik veri koşusu — sağlama raporu

- Seed: `4242` · Arketipler: A1, A2, A3 · Arketip başına varyant: 10 (ilk varyant: v50)
- Profil: `v2_balanced` (ana parametrelerden farklı; docs/04, Bölüm 8)
- Dönem: 2024-01 – 2026-12 (yorumlanabilir: 2025-01 itibarıyla)
- Üreteç sürümü: 0.1.0 · Parametre özeti: `3dcebe2f2750b413`

## Hedef oranlar (docs/03) ve gerçekleşen

| Ölçüt | Hedef | Gerçekleşen |
|---|---|---|
| Notlanan gerçek olaylar (E01–E12) | ~%70 | 70.9% |
| Firma notu (sezon) olan varyantlar | ~%70 | 60.0% |
| Havuz olayı / ay | ~2 | 1.67 |
| Olaysız ay (yorumlanabilir aylar) | ~%15 | 14.0% |
| Çeldirici notlu ay | %10–15 | 14.1% |
| Rakamlı olay notları | ~%50 | 46.6% |
| Eşik yakını havuz olayları | ~%20 | 21.1% |
| Çakışan havuz olayları | ~%10 | 16.1% |

## V2 kararları (Rohertrag adayları)

Rohertrag adayı: Rohertragsquote önceki aya **ve** önceki yılın aynı ayına göre ≥ 2.0 puan değişmiş (Katman 1 kuralı). Doğru karar yalnızca ground truth'ta: cite = notla açıkla, warn = uyar, either = ikisi de kabul, None = Rohertragsquote'yi değiştiren olay yok.

| Arketip | Kapsam | cite | warn | either | None |
|---|---|---:|---:|---:|---:|
| A1 | bütün yorumlanabilir aylar | 28 | 154 | 17 | 41 |
| A1 | Rohertrag adayı aylar | 12 | 83 | 6 | 9 |
| A2 | bütün yorumlanabilir aylar | 38 | 136 | 17 | 49 |
| A2 | Rohertrag adayı aylar | 26 | 115 | 12 | 18 |
| A3 | bütün yorumlanabilir aylar | 45 | 85 | 24 | 86 |
| A3 | Rohertrag adayı aylar | 20 | 72 | 13 | 29 |

### Dengelenmiş V2 kümesi

**Bu küme dengelenmiştir; gerçek dağılımı yansıtmaz.** Yalnızca "V2 adayı ayrımı" metriği için kullanılır (`evaluation/v2_balanced_set.jsonl`). Her arketipte cite ve warn aylarından eşit sayıda, either aylarından en fazla aynı sayıda Rohertrag adayı ay seçildi.

| Arketip | cite | warn | either |
|---|---:|---:|---:|
| A1 | 12 | 12 | 6 |
| A2 | 26 | 26 | 12 |
| A3 | 20 | 20 | 13 |

## Olay türleri

| Tür | Adet | Notlu |
|---|---:|---:|
| E01 | 180 | 124 |
| E02 | 139 | 99 |
| E03 | 90 | 63 |
| E04 | 274 | 197 |
| E05 | 163 | 117 |
| E06 | 265 | 189 |
| E07 | 14 | 11 |
| E08 | 36 | 27 |
| E09 | 16 | 10 |
| E10 | 48 | 32 |
| E11 | 77 | 54 |
| E12 | 223 | 158 |
| E13 | 51 | 0 |
| E14 | 51 | 0 |
| E15 | 54 | 0 |
| E16 | 121 | 0 |
| E17 | 30 | 0 |
| E18 | 219 | 0 |
| E19 | 30 | 18 |

## Varyantlar

| Firma | Ad | Çalışan | Ciro 2024 | P1 | P2 | P3 | P4 | E18/yıl |
|---|---|---:|---:|:-:|:-:|:-:|:-:|---|
| A1-v50 | Vorlage Metalltechnik 5 GmbH | 76 | 11.607.273 | ✓ | – | ✓ | ✓ | 4, 4, 3 |
| A1-v51 | Schema Zerspanung 5 GmbH | 48 | 7.330.909 | ✓ | ✓ | ✓ | – | 4, 3, 2 |
| A1-v52 | Demo Drehteile 5 GmbH | 68 | 10.385.455 | – | ✓ | – | – | 2, 4, 2 |
| A1-v53 | Probe Präzisionsteile 5 GmbH | 72 | 10.996.364 | – | – | ✓ | ✓ | 2, 3, 3 |
| A1-v54 | Typus Metalltechnik 5 GmbH | 48 | 7.330.909 | ✓ | ✓ | – | – | 2, 4, 3 |
| A1-v55 | Exemplar Zerspanung 5 GmbH | 50 | 7.636.364 | ✓ | – | – | – | 4, 4, 3 |
| A1-v56 | Prototyp Drehteile 5 GmbH | 50 | 7.636.364 | ✓ | ✓ | – | – | 2, 2, 4 |
| A1-v57 | Musterbau Präzisionsteile 5 GmbH | 63 | 9.621.818 | ✓ | ✓ | – | – | 2, 2, 3 |
| A1-v58 | Beispielwerk Metalltechnik 5 GmbH | 57 | 8.705.455 | – | ✓ | ✓ | – | 2, 3, 4 |
| A1-v59 | Vorbild Zerspanung 5 GmbH | 72 | 10.996.364 | ✓ | – | ✓ | – | 4, 3, 4 |
| A2-v50 | Vorlage Sanitärgroßhandel 5 GmbH | 46 | 16.100.000 | ✓ | ✓ | ✓ | ✓ | 4, 5, 5 |
| A2-v51 | Schema Heizungsbedarf 5 GmbH | 61 | 21.350.000 | ✓ | ✓ | – | ✓ | 4, 5, 4 |
| A2-v52 | Demo Haustechnik Handel 5 GmbH | 32 | 11.200.000 | ✓ | – | – | ✓ | 4, 6, 4 |
| A2-v53 | Probe Sanitärgroßhandel 5 GmbH | 31 | 10.850.000 | ✓ | ✓ | – | ✓ | 5, 6, 6 |
| A2-v54 | Typus Heizungsbedarf 5 GmbH | 62 | 21.700.000 | ✓ | – | – | ✓ | 6, 5, 6 |
| A2-v55 | Exemplar Haustechnik Handel 5 GmbH | 40 | 14.000.000 | ✓ | ✓ | – | ✓ | 5, 4, 5 |
| A2-v56 | Prototyp Sanitärgroßhandel 5 GmbH | 54 | 18.900.000 | ✓ | ✓ | – | ✓ | 5, 5, 5 |
| A2-v57 | Musterbau Heizungsbedarf 5 GmbH | 59 | 20.650.000 | ✓ | ✓ | ✓ | – | 6, 4, 5 |
| A2-v58 | Beispielwerk Haustechnik Handel 5 GmbH | 56 | 19.600.000 | ✓ | ✓ | – | – | 4, 4, 4 |
| A2-v59 | Vorbild Sanitärgroßhandel 5 GmbH | 36 | 12.600.000 | ✓ | ✓ | – | ✓ | 5, 5, 4 |
| A3-v50 | Vorlage Outdoor Living 5 GmbH | 82 | 11.181.818 | – | – | – | – | 2, 2, 2 |
| A3-v51 | Schema Freiraummöbel 5 GmbH | 104 | 14.181.818 | – | ✓ | – | – | 1, 2, 1 |
| A3-v52 | Demo Gartenmöbel 5 GmbH | 93 | 12.681.818 | – | ✓ | – | – | 0, 0, 0 |
| A3-v53 | Probe Outdoor Living 5 GmbH | 114 | 15.545.455 | – | ✓ | – | – | 1, 0, 1 |
| A3-v54 | Typus Freiraummöbel 5 GmbH | 67 | 9.136.364 | – | – | – | – | 1, 2, 0 |
| A3-v55 | Exemplar Gartenmöbel 5 GmbH | 69 | 9.409.091 | – | – | – | – | 0, 2, 1 |
| A3-v56 | Prototyp Outdoor Living 5 GmbH | 139 | 18.954.545 | – | – | – | – | 0, 2, 1 |
| A3-v57 | Musterbau Freiraummöbel 5 GmbH | 134 | 18.272.727 | – | ✓ | – | – | 1, 0, 0 |
| A3-v58 | Beispielwerk Gartenmöbel 5 GmbH | 89 | 12.136.364 | – | – | – | – | 0, 1, 2 |
| A3-v59 | Vorbild Outdoor Living 5 GmbH | 146 | 19.909.091 | – | – | – | – | 0, 0, 1 |

## Kalibrasyon: v00 varyantları, 2024 taban serisi (olaysız, gürültüsüz)

| Firma | Materialquote | Personalquote | Betriebsergebnis-Marge |
|---|---:|---:|---:|

## Dosyalar

- `model_input/bwa_raw.csv` (modele görünür)
- `model_input/context_notes.jsonl` (modele görünür)
- `model_input/firms.json` (modele görünür)
- `evaluation/bwa_true.csv` (yalnızca değerlendirme)
- `evaluation/effects.csv` (yalnızca değerlendirme)
- `evaluation/events.jsonl` (yalnızca değerlendirme)
- `evaluation/ground_truth_months.jsonl` (yalnızca değerlendirme)
- `evaluation/notes_ground_truth.jsonl` (yalnızca değerlendirme)
- `evaluation/variants.json` (yalnızca değerlendirme)
- `evaluation/v2_balanced_set.jsonl` (yalnızca değerlendirme)
