# Puanlar — ablation (ince ayarlı modeller 26.10.2026 + baseline 24.10.2026)

Puanlama 1.1 (`python -m scoring`). Tanımlar: `docs/13_degerlendirme.md`.

## Bütün test kümesi

| Ölçüt | `base_rag_k8` | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Metin | 720 | 720 | 720 | 720 | 720 | 720 | 720 | 720 | |
| Format uyumu | %34 | %39 | %34 | %30 | %100 | %99 | %96 | %97 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %5 | %18 | %6 | %4 | %93 | %81 | %81 | %82 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %94 | %95 | %93 | %94 | %100 | %100 | %99 | %99 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %43 | %53 | %42 | %45 | %0 | %1 | %0 | %0 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 171 | 162 | 168,8 | 169,2 | 257,4 | 230,7 | 247,4 | 248,5 | hedef 250–350 |
| Kelime 200–400 arası | %20 | %13 | %16 | %17 | %86 | %76 | %81 | %81 | metin payı |
| Neden cümlesi / metin | 2,52 | 0,16 | 2,5 | 2,4 | 2,11 | 2,19 | 3,68 | 3,58 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %48 | %0 | %48 | %48 | %0 | %0 | %42 | %41 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %8 | %0 | %10 | %10 | %100 | %93 | %56 | %57 | nedenlerin payı |
| … işaretsiz | %44 | %100 | %42 | %42 | %0 | %7 | %2 | %2 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 1,11 | 0,16 | 1,05 | 1,01 | 0 | 0,15 | 0,06 | 0,06 |  |
| Kaynak isabeti (precision) | %57 | – | %55 | %54 | – | – | %74 | %75 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | %35 | – | %30 | %34 | – | – | %55 | %59 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | %38 | – | %38 | %37 | – | – | %64 | %64 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %38 | %0 | %38 | %38 | %0 | %0 | %28 | %26 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 1 | 0 | 2 | 2 | 0 | 0 | 3 | 3 | toplam sayı |
| Uydurma kaynak | %0 | %0 | %1 | %0 | %0 | %0 | %1 | %1 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %95 | %93 | %96 | %96 | %100 | %100 | %100 | %100 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,69 | 4,86 | 4,64 | 4,72 | 0,08 | 0,03 | 0,08 | 0,07 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %68 | %75 | %65 | %66 | %100 | %100 | %97 | %97 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %65 | %66 | %62 | %64 | %84 | %84 | %82 | %82 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %85 | %86 | %85 | %85 | %88 | %88 | %88 | %87 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 439 | 439 | 439 | 439 | 439 | 439 | 439 | 439 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %88 | %76 | %85 | %86 | %100 | %99 | %96 | %96 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 17 | 0 | 17 | 17 | 0 | 0 | 17 | 17 | ay sayısı |
| … bunlarda doğru | %6 | – | %12 | %12 | – | – | %6 | %6 |  |

## A1 — yeni sektör (eğitimde hiç yok)

| Ölçüt | `base_rag_k8` | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Metin | 240 | 240 | 240 | 240 | 240 | 240 | 240 | 240 | |
| Format uyumu | %22 | %24 | %22 | %22 | %100 | %99 | %98 | %99 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %1 | %11 | %3 | %2 | %93 | %87 | %86 | %83 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %94 | %95 | %94 | %94 | %100 | %100 | %100 | %100 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %59 | %70 | %61 | %63 | %0 | %1 | %0 | %0 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 169,4 | 160 | 166,8 | 167,8 | 252,5 | 231,2 | 244,7 | 247,3 | hedef 250–350 |
| Kelime 200–400 arası | %20 | %15 | %14 | %16 | %88 | %77 | %80 | %80 | metin payı |
| Neden cümlesi / metin | 2,47 | 0,15 | 2,52 | 2,46 | 2,08 | 2,06 | 3,68 | 3,71 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %49 | %0 | %52 | %53 | %0 | %0 | %49 | %44 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %6 | %0 | %7 | %5 | %100 | %95 | %50 | %54 | nedenlerin payı |
| … işaretsiz | %45 | %100 | %41 | %42 | %0 | %5 | %1 | %2 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 1,1 | 0,15 | 1,02 | 1,02 | 0 | 0,1 | 0,04 | 0,08 |  |
| Kaynak isabeti (precision) | %61 | – | %56 | %58 | – | – | %73 | %76 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | %36 | – | %31 | %37 | – | – | %53 | %58 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | %42 | – | %44 | %40 | – | – | %63 | %66 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %38 | %0 | %36 | %39 | %0 | %0 | %28 | %27 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 0 | 0 | 0 | 1 | 0 | 0 | 2 | 1 | toplam sayı |
| Uydurma kaynak | %1 | %0 | %0 | %0 | %0 | %0 | %1 | %1 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %94 | %92 | %95 | %95 | %100 | %100 | %100 | %100 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,78 | 4,72 | 4,78 | 4,79 | 0,03 | 0,02 | 0 | 0,01 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %72 | %79 | %67 | %71 | %100 | %100 | %98 | %98 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %68 | %72 | %65 | %68 | %85 | %86 | %84 | %84 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %81 | %82 | %80 | %82 | %84 | %85 | %84 | %83 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 115 | 115 | 115 | 115 | 115 | 115 | 115 | 115 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %84 | %71 | %83 | %84 | %100 | %96 | %95 | %95 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 5 | 0 | 5 | 5 | 0 | 0 | 5 | 5 | ay sayısı |
| … bunlarda doğru | %0 | – | %20 | %20 | – | – | %0 | %0 |  |

## A2/A3 — yeni firma (görülmemiş varyantlar)

| Ölçüt | `base_rag_k8` | `baseline_ohne_kontext` | `baseline_rag_alle` | `baseline_rag_k8` | `ft_ohne_ohne_kontext` | `ft_rag_ohne_kontext` | `ft_rag_rag_alle` | `ft_rag_rag_k8` | Açıklama |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Metin | 480 | 480 | 480 | 480 | 480 | 480 | 480 | 480 | |
| Format uyumu | %39 | %46 | %40 | %34 | %100 | %100 | %96 | %96 | 6.3 yapısı; doğrulamada biçim hatası olmayan metin payı |
| Hatasız metin | %6 | %22 | %7 | %5 | %92 | %78 | %78 | %81 | doğrulamada hiç `fehler` bulgusu olmayan metin payı |
| Rakam sadakati (değer) | %94 | %95 | %93 | %93 | %100 | %100 | %99 | %99 | değeri facts.json ya da kaynak gösterilen notla örtüşen rakam payı |
| Binlik ayırıcı boşluk | %34 | %44 | %32 | %35 | %0 | %0 | %1 | %0 | „14 054 €“ yazan metin payı (istem: „14.054 €“) |
| Kelime (ort., tablo hariç) | 171,9 | 163 | 169,8 | 169,9 | 259,8 | 230,5 | 248,8 | 249,2 | hedef 250–350 |
| Kelime 200–400 arası | %20 | %12 | %17 | %18 | %85 | %75 | %82 | %82 | metin payı |
| Neden cümlesi / metin | 2,55 | 0,16 | 2,49 | 2,37 | 2,12 | 2,26 | 3,67 | 3,51 | doğrulamanın tanıdığı neden cümleleri ve tablo açıklamaları |
| … kaynaklı | %47 | %0 | %46 | %45 | %0 | %0 | %39 | %39 | nedenlerin payı: [Quelle: …] |
| … „(Hypothese)“ | %10 | %0 | %11 | %12 | %100 | %92 | %59 | %59 | nedenlerin payı |
| … işaretsiz | %44 | %100 | %43 | %42 | %0 | %8 | %2 | %1 | nedenlerin payı: ne kaynak ne hipotez (uydurma neden adayı) |
| İşaretsiz neden / metin | 1,11 | 0,16 | 1,07 | 1 | 0 | 0,18 | 0,07 | 0,05 |  |
| Kaynak isabeti (precision) | %56 | – | %55 | %52 | – | – | %74 | %75 | gösterilen notlardan planın kaynak saydığı notların payı |
| Kaynak kapsamı (recall) | %34 | – | %29 | %32 | – | – | %56 | %60 | planın kaynak saydığı notlardan gösterilenlerin payı |
| Tablo atıfı doğru satırda | %36 | – | %36 | %36 | – | – | %64 | %62 | tablodaki atıflardan notun planda o satırın kaynağı olduğu pay (1.1) |
| Yanlış satıra atıf | %38 | %0 | %40 | %38 | %0 | %0 | %28 | %26 | bir notu planda açıklamadığı satırın nedeni yapan metin payı (1.1) |
| Çeldirici nota atıf | 1 | 0 | 2 | 1 | 0 | 0 | 1 | 2 | toplam sayı |
| Uydurma kaynak | %0 | %0 | %1 | %0 | %0 | %0 | %1 | %1 | verilmemiş bir kaynağa atıf yapan metin payı |
| Sapma yakalama (recall) | %96 | %94 | %96 | %96 | %100 | %100 | %100 | %100 | facts.json'daki anlamlı kalemlerden tabloda yer alanların payı |
| Gereksiz tablo satırı / metin | 4,64 | 4,93 | 4,58 | 4,69 | 0,11 | 0,04 | 0,11 | 0,1 | anlamlı, bayraklı ya da planda olmayan satırlar |
| Uyarı kapsamı (Katman 1) | %67 | %73 | %63 | %64 | %100 | %100 | %97 | %97 | Katman 1 bayraklarından Hinweise'de anılanların payı |
| Uyarı recall (ground truth) | %64 | %64 | %61 | %62 | %84 | %84 | %82 | %82 | beklenen çarpıklıklardan uyarılanların payı |
| Uyarı precision (ground truth) | %87 | %87 | %87 | %87 | %90 | %90 | %89 | %89 | Hinweise maddelerinden gerçek ya da kabul edilebilir çarpıklığa denk gelenlerin payı |
| V2 adayı: ay sayısı | 324 | 324 | 324 | 324 | 324 | 324 | 324 | 324 | Katman 1'in Rohertragsquote adayı olan aylar |
| V2 adayı: doğru karar | %90 | %78 | %86 | %86 | %100 | %100 | %96 | %96 | plana göre: notla açıkla ya da uyar |
| … notla açıklanacak | 12 | 0 | 12 | 12 | 0 | 0 | 12 | 12 | ay sayısı |
| … bunlarda doğru | %8 | – | %8 | %8 | – | – | %8 | %8 |  |

