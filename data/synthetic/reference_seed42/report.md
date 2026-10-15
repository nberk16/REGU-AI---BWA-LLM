# Sentetik veri koşusu — sağlama raporu

- Seed: `42` · Arketipler: A1, A2, A3 · Arketip başına varyant: 10 (ilk varyant: v00)
- Profil: yok (ana parametreler)
- Dönem: 2024-01 – 2026-12 (yorumlanabilir: 2025-01 itibarıyla)
- Üreteç sürümü: 0.1.0 · Parametre özeti: `72dc78e45b68504e`

## Hedef oranlar (docs/03) ve gerçekleşen

| Ölçüt | Hedef | Gerçekleşen |
|---|---|---|
| Notlanan gerçek olaylar (E01–E12) | ~%70 | 70.7% |
| Firma notu (sezon) olan varyantlar | ~%70 | 70.0% |
| Havuz olayı / ay | ~2 | 1.51 |
| Olaysız ay (yorumlanabilir aylar) | ~%15 | 15.4% |
| Çeldirici notlu ay | %10–15 | 10.6% |
| Rakamlı olay notları | ~%50 | 49.3% |
| Eşik yakını havuz olayları | ~%20 | 17.7% |
| Çakışan havuz olayları | ~%10 | 13.0% |

## V2 kararları (Rohertrag adayları)

Rohertrag adayı: Rohertragsquote önceki aya **ve** önceki yılın aynı ayına göre ≥ 2.0 puan değişmiş (Katman 1 kuralı). Doğru karar yalnızca ground truth'ta: cite = notla açıkla, warn = uyar, either = ikisi de kabul, None = Rohertragsquote'yi değiştiren olay yok.

| Arketip | Kapsam | cite | warn | either | None |
|---|---|---:|---:|---:|---:|
| A1 | bütün yorumlanabilir aylar | 14 | 136 | 11 | 79 |
| A1 | Rohertrag adayı aylar | 10 | 98 | 7 | 20 |
| A2 | bütün yorumlanabilir aylar | 2 | 217 | 2 | 19 |
| A2 | Rohertrag adayı aylar | 0 | 193 | 1 | 9 |
| A3 | bütün yorumlanabilir aylar | 22 | 92 | 12 | 114 |
| A3 | Rohertrag adayı aylar | 14 | 85 | 8 | 33 |

## Olay türleri

| Tür | Adet | Notlu |
|---|---:|---:|
| E01 | 195 | 141 |
| E02 | 135 | 97 |
| E03 | 90 | 65 |
| E04 | 132 | 96 |
| E05 | 43 | 31 |
| E06 | 269 | 187 |
| E07 | 18 | 11 |
| E08 | 49 | 32 |
| E09 | 15 | 11 |
| E10 | 51 | 31 |
| E11 | 75 | 53 |
| E12 | 225 | 162 |
| E13 | 39 | 0 |
| E14 | 39 | 0 |
| E15 | 63 | 0 |
| E16 | 112 | 0 |
| E17 | 42 | 0 |
| E18 | 274 | 0 |
| E19 | 30 | 21 |

## Varyantlar

| Firma | Ad | Çalışan | Ciro 2024 | P1 | P2 | P3 | P4 | E18/yıl |
|---|---|---:|---:|:-:|:-:|:-:|:-:|---|
| A1-v00 | Muster GmbH | 55 | 8.400.000 | ✓ | ✓ | ✓ | – | 3, 3, 3 |
| A1-v01 | Modell Präzisionsteile GmbH | 65 | 9.927.273 | ✓ | ✓ | – | – | 4, 4, 3 |
| A1-v02 | Vorlage Metalltechnik GmbH | 61 | 9.316.364 | ✓ | ✓ | – | ✓ | 4, 4, 2 |
| A1-v03 | Schema Zerspanung GmbH | 60 | 9.163.636 | – | ✓ | – | – | 3, 4, 3 |
| A1-v04 | Demo Drehteile GmbH | 72 | 10.996.364 | – | ✓ | – | – | 3, 2, 2 |
| A1-v05 | Probe Präzisionsteile GmbH | 84 | 12.829.091 | – | ✓ | – | ✓ | 4, 3, 4 |
| A1-v06 | Typus Metalltechnik GmbH | 62 | 9.469.091 | – | – | – | – | 2, 4, 2 |
| A1-v07 | Exemplar Zerspanung GmbH | 55 | 8.400.000 | – | ✓ | – | ✓ | 2, 4, 2 |
| A1-v08 | Prototyp Drehteile GmbH | 54 | 8.247.273 | ✓ | ✓ | ✓ | ✓ | 2, 4, 3 |
| A1-v09 | Musterbau Präzisionsteile GmbH | 79 | 12.065.455 | – | – | – | – | 4, 2, 3 |
| A2-v00 | Beispiel Haustechnik GmbH | 40 | 14.000.000 | ✓ | ✓ | ✓ | ✓ | 5, 5, 5 |
| A2-v01 | Modell Haustechnik Handel GmbH | 43 | 15.050.000 | ✓ | ✓ | ✓ | ✓ | 4, 6, 5 |
| A2-v02 | Vorlage Sanitärgroßhandel GmbH | 41 | 14.350.000 | ✓ | ✓ | ✓ | ✓ | 5, 5, 6 |
| A2-v03 | Schema Heizungsbedarf GmbH | 25 | 8.750.000 | ✓ | ✓ | – | ✓ | 6, 5, 5 |
| A2-v04 | Demo Haustechnik Handel GmbH | 37 | 12.950.000 | ✓ | ✓ | ✓ | ✓ | 6, 5, 6 |
| A2-v05 | Probe Sanitärgroßhandel GmbH | 59 | 20.650.000 | ✓ | ✓ | – | ✓ | 5, 5, 4 |
| A2-v06 | Typus Heizungsbedarf GmbH | 57 | 19.950.000 | – | ✓ | ✓ | ✓ | 4, 4, 5 |
| A2-v07 | Exemplar Haustechnik Handel GmbH | 58 | 20.300.000 | – | ✓ | ✓ | ✓ | 5, 5, 6 |
| A2-v08 | Prototyp Sanitärgroßhandel GmbH | 53 | 18.550.000 | ✓ | ✓ | ✓ | ✓ | 5, 6, 5 |
| A2-v09 | Musterbau Heizungsbedarf GmbH | 62 | 21.700.000 | ✓ | ✓ | ✓ | ✓ | 5, 5, 6 |
| A3-v00 | Exempel Outdoor GmbH | 110 | 15.000.000 | – | – | – | – | 1, 1, 1 |
| A3-v01 | Modell Gartenmöbel GmbH | 141 | 19.227.273 | – | – | – | – | 0, 2, 2 |
| A3-v02 | Vorlage Outdoor Living GmbH | 139 | 18.954.545 | – | ✓ | – | – | 2, 2, 1 |
| A3-v03 | Schema Freiraummöbel GmbH | 70 | 9.545.455 | – | – | – | – | 0, 2, 1 |
| A3-v04 | Demo Gartenmöbel GmbH | 126 | 17.181.818 | – | – | – | – | 2, 1, 2 |
| A3-v05 | Probe Outdoor Living GmbH | 156 | 21.272.727 | ✓ | – | – | – | 2, 0, 2 |
| A3-v06 | Typus Freiraummöbel GmbH | 87 | 11.863.636 | – | – | – | – | 2, 0, 1 |
| A3-v07 | Exemplar Gartenmöbel GmbH | 69 | 9.409.091 | – | – | – | – | 0, 0, 2 |
| A3-v08 | Prototyp Outdoor Living GmbH | 94 | 12.818.182 | – | ✓ | – | – | 2, 1, 0 |
| A3-v09 | Musterbau Freiraummöbel GmbH | 119 | 16.227.273 | – | ✓ | – | – | 0, 2, 0 |

## Kalibrasyon: v00 varyantları, 2024 taban serisi (olaysız, gürültüsüz)

| Firma | Materialquote | Personalquote | Betriebsergebnis-Marge |
|---|---:|---:|---:|
| A1-v00 | 42.0% | 33.0% | 6.5% |
| A2-v00 | 72.0% | 14.0% | 3.3% |
| A3-v00 | 45.0% | 30.0% | 5.7% |

## Muster GmbH (A1-v00), 2025: aylık Betriebsergebnis, kaydedilen ve ekonomik gerçek

| Ay | Kaydedilen | Gerçek | Fark |
|---|---:|---:|---:|
| 2025-01 | -104.521 | -99.675 | -4.846 |
| 2025-02 | 14.054 | -3.549 | 17.603 |
| 2025-03 | 36.430 | 8.353 | 28.077 |
| 2025-04 | 13.730 | -6.772 | 20.503 |
| 2025-05 | -79.756 | -128.036 | 48.280 |
| 2025-06 | -56.003 | 63.142 | -119.145 |
| 2025-07 | -73.231 | -36.799 | -36.433 |
| 2025-08 | -62.876 | -158.848 | 95.972 |
| 2025-09 | 236.457 | 145.510 | 90.947 |
| 2025-10 | 2.978 | 36.097 | -33.119 |
| 2025-11 | -124.380 | 4.941 | -129.321 |
| 2025-12 | 92.938 | -25.822 | 118.760 |

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
