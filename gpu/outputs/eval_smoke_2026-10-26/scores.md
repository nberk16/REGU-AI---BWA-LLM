# Puanlar — 03_eval smoke (26.10.2026, A1-v00, 8 ay)

Puanlama 1.1 (`python -m scoring`). Tanımlar: `docs/13_degerlendirme.md`.

## Bütün test kümesi

| Ölçüt | `base_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---|
| Metin | 8 | 8 | 8 | 8 | 8 | |
| Format uyumu | %38 | %100 | %100 | %100 | %100 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %12 | %100 | %62 | %50 | %75 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %96 | %100 | %99 | %99 | %98 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %62 | %0 | %0 | %0 | %0 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 159,4 | 248,2 | 226,6 | 211,6 | 220,8 | hedef 250–350 |
| Kelime 200–400 arası | %12 | %88 | %75 | %62 | %88 | metin payı |
| Neden cümlesi / metin | 3 | 1,75 | 2,12 | 4,88 | 4 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %58 | %0 | %0 | %67 | %69 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %17 | %100 | %94 | %23 | %28 | nedenlerin payı |
| … işaretsiz | %25 | %0 | %6 | %10 | %3 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 0,75 | 0 | 0,12 | 0,5 | 0,12 |  |
| Kaynak isabeti (precision) | %70 | – | – | %90 | %81 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | %27 | – | – | %64 | %50 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | %31 | – | – | %84 | %69 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %50 | %0 | %0 | %38 | %38 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 0 | 0 | 0 | 0 | toplam sayı |
| Uydurma kaynak | %0 | %0 | %0 | %12 | %0 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %100 | %100 | %100 | %100 | %100 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,5 | 0 | 0 | 0 | 0 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %60 | %100 | %100 | %100 | %100 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %60 | %80 | %80 | %80 | %80 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %100 | %81 | %81 | %81 | %81 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 1 | 1 | 1 | 1 | 1 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %0 | %100 | %100 | %100 | %100 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 0 | 0 | 0 | 0 | 0 | ay sayısı |
| … bunlarda doğru | – | – | – | – | – |  |

## A1 — yeni sektör (eğitimde hiç yok)

| Ölçüt | `base_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---|
| Metin | 8 | 8 | 8 | 8 | 8 | |
| Format uyumu | %38 | %100 | %100 | %100 | %100 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %12 | %100 | %62 | %50 | %75 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %96 | %100 | %99 | %99 | %98 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %62 | %0 | %0 | %0 | %0 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 159,4 | 248,2 | 226,6 | 211,6 | 220,8 | hedef 250–350 |
| Kelime 200–400 arası | %12 | %88 | %75 | %62 | %88 | metin payı |
| Neden cümlesi / metin | 3 | 1,75 | 2,12 | 4,88 | 4 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %58 | %0 | %0 | %67 | %69 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %17 | %100 | %94 | %23 | %28 | nedenlerin payı |
| … işaretsiz | %25 | %0 | %6 | %10 | %3 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 0,75 | 0 | 0,12 | 0,5 | 0,12 |  |
| Kaynak isabeti (precision) | %70 | – | – | %90 | %81 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | %27 | – | – | %64 | %50 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | %31 | – | – | %84 | %69 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %50 | %0 | %0 | %38 | %38 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 0 | 0 | 0 | 0 | toplam sayı |
| Uydurma kaynak | %0 | %0 | %0 | %12 | %0 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %100 | %100 | %100 | %100 | %100 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,5 | 0 | 0 | 0 | 0 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %60 | %100 | %100 | %100 | %100 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %60 | %80 | %80 | %80 | %80 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %100 | %81 | %81 | %81 | %81 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 1 | 1 | 1 | 1 | 1 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %0 | %100 | %100 | %100 | %100 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 0 | 0 | 0 | 0 | 0 | ay sayısı |
| … bunlarda doğru | – | – | – | – | – |  |

## A2/A3 — yeni firma (görülmemiş varyantlar)

| Ölçüt | `base_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---|
| Metin | 0 | 0 | 0 | 0 | 0 | |
| Format uyumu | – | – | – | – | – | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | – | – | – | – | – | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | – | – | – | – | – | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | – | – | – | – | – | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | – | – | – | – | – | hedef 250–350 |
| Kelime 200–400 arası | – | – | – | – | – | metin payı |
| Neden cümlesi / metin | – | – | – | – | – | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | – | – | – | – | – | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | – | – | – | – | – | nedenlerin payı |
| … işaretsiz | – | – | – | – | – | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | – | – | – | – | – |  |
| Kaynak isabeti (precision) | – | – | – | – | – | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | – | – | – | – | – | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | – | – | – | – | – | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | – | – | – | – | – | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | – | – | – | – | – | toplam sayı |
| Uydurma kaynak | – | – | – | – | – | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | – | – | – | – | – | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | – | – | – | – | – | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | – | – | – | – | – | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | – | – | – | – | – | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | – | – | – | – | – | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | – | – | – | – | – | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | – | – | – | – | – | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | – | – | – | – | – | ay sayısı |
| … bunlarda doğru | – | – | – | – | – |  |

