# Puanlar — baseline_2026-10-24

Puanlama 1.1 (`python -m scoring`). Tanımlar: `docs/13_degerlendirme.md`.

## Bütün test kümesi

| Ölçüt | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | Açıklama |
|---|---:|---:|---:|---|
| Metin | 720 | 720 | 720 | |
| Format uyumu | %39 | %34 | %30 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %18 | %6 | %4 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %95 | %93 | %94 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %53 | %42 | %45 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 162 | 168,8 | 169,2 | hedef 250–350 |
| Kelime 200–400 arası | %13 | %16 | %17 | metin payı |
| Neden cümlesi / metin | 0,16 | 2,5 | 2,4 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %0 | %48 | %48 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %0 | %10 | %10 | nedenlerin payı |
| … işaretsiz | %100 | %42 | %42 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 0,16 | 1,05 | 1,01 |  |
| Kaynak isabeti (precision) | – | %55 | %54 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | – | %30 | %34 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | – | %38 | %37 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %0 | %38 | %38 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 2 | 2 | toplam sayı |
| Uydurma kaynak | %0 | %1 | %0 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %93 | %96 | %96 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,86 | 4,64 | 4,72 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %75 | %65 | %66 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %66 | %62 | %64 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %86 | %85 | %85 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 439 | 439 | 439 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %76 | %85 | %86 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 0 | 17 | 17 | ay sayısı |
| … bunlarda doğru | – | %12 | %12 |  |

## A1 — yeni sektör (eğitimde hiç yok)

| Ölçüt | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | Açıklama |
|---|---:|---:|---:|---|
| Metin | 240 | 240 | 240 | |
| Format uyumu | %24 | %22 | %22 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %11 | %3 | %2 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %95 | %94 | %94 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %70 | %61 | %63 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 160 | 166,8 | 167,8 | hedef 250–350 |
| Kelime 200–400 arası | %15 | %14 | %16 | metin payı |
| Neden cümlesi / metin | 0,15 | 2,52 | 2,46 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %0 | %52 | %53 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %0 | %7 | %5 | nedenlerin payı |
| … işaretsiz | %100 | %41 | %42 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 0,15 | 1,02 | 1,02 |  |
| Kaynak isabeti (precision) | – | %56 | %58 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | – | %31 | %37 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | – | %44 | %40 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %0 | %36 | %39 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 0 | 1 | toplam sayı |
| Uydurma kaynak | %0 | %0 | %0 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %92 | %95 | %95 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,72 | 4,78 | 4,79 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %79 | %67 | %71 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %72 | %65 | %68 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %82 | %80 | %82 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 115 | 115 | 115 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %71 | %83 | %84 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 0 | 5 | 5 | ay sayısı |
| … bunlarda doğru | – | %20 | %20 |  |

## A2/A3 — yeni firma (görülmemiş varyantlar)

| Ölçüt | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | Açıklama |
|---|---:|---:|---:|---|
| Metin | 480 | 480 | 480 | |
| Format uyumu | %46 | %40 | %34 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %22 | %7 | %5 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %95 | %93 | %93 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %44 | %32 | %35 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 163 | 169,8 | 169,9 | hedef 250–350 |
| Kelime 200–400 arası | %12 | %17 | %18 | metin payı |
| Neden cümlesi / metin | 0,16 | 2,49 | 2,37 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %0 | %46 | %45 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %0 | %11 | %12 | nedenlerin payı |
| … işaretsiz | %100 | %43 | %42 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 0,16 | 1,07 | 1 |  |
| Kaynak isabeti (precision) | – | %55 | %52 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | – | %29 | %32 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | – | %36 | %36 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %0 | %40 | %38 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 2 | 1 | toplam sayı |
| Uydurma kaynak | %0 | %1 | %0 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %94 | %96 | %96 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,93 | 4,58 | 4,69 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %73 | %63 | %64 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %64 | %61 | %62 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %87 | %87 | %87 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 324 | 324 | 324 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %78 | %86 | %86 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 0 | 12 | 12 | ay sayısı |
| … bunlarda doğru | – | %8 | %8 |  |

