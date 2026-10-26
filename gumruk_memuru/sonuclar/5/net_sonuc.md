# Sonuç: native model .NET alt grubunda (26 Ekim 2026)

Ön kayıt: `on_kayit_net.md` (commit `e5ad54e`, ölçümden önce). Betik `net_olcum.py`, çıktı
`net_olcum.log` / `net_olcum.csv`. Bir kez koşuldu. GEÇİT tuttu: alt grupsuz EXE / DLL kaçan ve
yanlış alarm meta verideki `test_bir_kez` ile birebir (17.749 / 0.828, 19.524 / 1.428).
Eşikler sabit: EXE 0,70 / DLL 0,61. Aralıklar Wilson %95.

## Tablo

| Küme | Eşik | Grup | Tür | Kaçan zararlı | Yanlış alarm |
|---|---|---|---|---|---|
| A native test (52-63) | tür eşiği | .NET | EXE | %33,74 [32,14-35,38] (1106/3278) | %2,88 [1,33-6,15] (6/208) |
| | | .NET | DLL | %23,38 [19,00-28,41] (72/308) | %0,95 [0,52-1,74] (10/1054) |
| | | .NET dışı | EXE | %17,63 [17,52-17,74] (79014/448124) | %0,82 [0,78-0,88] (1050/127338) |
| | | .NET dışı | DLL | %19,48 [19,02-19,95] (5510/28282) | %1,43 [1,39-1,47] (5020/351146) |
| B Dot_Net_test (52-63) | tür eşiği | .NET | EXE | %46,22 [45,80-46,64] (25302/54740) | %3,52 [3,13-3,97] (262/7436) |
| | | .NET | DLL | %86,71 [85,77-87,61] (4556/5254) | %0,70 [0,64-0,78] (370/52564) |
| | | .NET | hepsi | %49,77 [49,37-50,17] (29858/59994) | %1,05 [0,97-1,14] (632/60000) |
| | 0,5 (Faz 1 ile aynı) | .NET | hepsi | %23,29 [22,95-23,63] (13970/59994) | %4,42 [4,26-4,59] (2654/60000) |
| Faz 1 modeli, B | 0,5 | .NET | hepsi | %92,8 (CLAUDE.md, `net_dogrulama.py`) | — |
| C yerel zararsız | tür eşiği | .NET | hepsi | — | %0,03 [0,01-0,16] (1/3471) |
| | | .NET dışı | hepsi | — | %0,51 [0,28-0,91] (11/2164) |

B'de 6 zararlı .NET bayrağı taşımıyor (n < 30, yorumlanmaz). Tüm hücreler ve AUC: `net_olcum.csv`.

## Ön kayıtlı kurallara göre

1. **Faz 1 ile (B):** native model Dot_Net_test'te tür eşiklerinde %49,77 kaçırıyor (üst sınır
   50,17), 0,5'te %23,29 (üst 23,63); ikisi de %92,8'in altında → "Faz 1'in .NET körlüğünü
   azaltıyor". Ama bu iki çalışma noktası aynı yanlış alarmda değil: 0,5'te B yanlış alarmı %4,42.
2. **.NET hâlâ zayıf nokta mı (A):** EXE'de EVET: kaçan %33,74 vs %17,63, yanlış alarm %2,88 vs
   %0,82 (aralıklar örtüşmüyor). DLL'de fark gösterilemedi (kaçan 23,38 [19,0-28,4] vs 19,48;
   .NET zararlı DLL n = 308, aralık geniş).
3. **A ile B farklı:** B (EMBER2024'ün ayrı .NET kümesi) A'dan çok daha kötü, özellikle DLL:
   zararlı .NET DLL'lerin %86,71'i kaçıyor (AUC 0,838). A'daki .NET dosyaları Win32/Win64
   kümelerinin içinden gelen az sayıdaki dosya; B'nin dağılımı farklı (zararsızların %87,6'sı DLL: 52564/60000).
4. `tahmin_et.py`'deki .NET uyarısı kalıyor: native model .NET için yeterli değil; uzman modelin
   bağlanması gerekçelendi ama karar ayrı.

## Sınırlar

- Faz 1 karşılaştırması aynı yanlış alarmda yapılmadı (ön kayıtta yoktu); eşit yanlış alarm
  karşılaştırması ayrı, ön kayıtlı bir ölçüm olur. → Yapıldı, aşağıdaki EK.
- B'nin %50'si zararlı (README'deki uyarı burada da geçerli).
- Yerel (C) .NET zararsızlarının %99'u DLL (3422/3471); EXE yalnız 49 dosya.

## EK: eşit yanlış alarmda (26 Ekim 2026)

Ön kayıt `on_kayit_esit_ya.md` (commit `48994e6`, ölçümden önce), betik `esit_ya.py`, çıktı
`esit_ya.log`. Faz 1 modeli `net_dogrulama.py`'nin "A (5 ozellik)" modeli, aynı kodla yeniden
üretildi; GEÇİT tuttu: eşik 0,5'te kaçan %92,77 (55662/60000; belgede 92,8). Native model kayıtlı
model. τ test kümesinden (B) seçilen ROC çalışma noktası; üretim eşiği değil.

Faz 1'in B'deki yanlış alarmı (eşik 0,5): **%0,46** [0,41-0,51] (274/60000); AUC 0,6328.
(Sitedeki "%3,8" bu değil: uzman model M2'nin kaçan oranı.)

| Çalışma noktası | Model | τ | Yanlış alarm | Kaçan zararlı (B, hepsi) |
|---|---|---|---|---|
| Faz 1'in yanlış alarmı (≤ %0,457) | Faz 1 | 0,5 | %0,46 | %92,77 [92,56-92,97] |
| | native | 0,76 | %0,45 | **%59,79** [59,39-60,18] |
| native'in sabit eşiklerdeki yanlış alarmı (≤ %1,05) | native | EXE 0,70 / DLL 0,61 | %1,05 | %49,77 [49,37-50,17] |
| | Faz 1 | 0,43 | %0,95 | %89,39 [89,14-89,63] |

Tür ayrımı (aynı τ): native τ=0,76'da EXE kaçan %56,62 (YA %1,43), DLL kaçan **%92,70** (YA %0,32);
Faz 1 τ=0,43'te EXE %88,46, DLL %99,05. Bir alt adımlar (hedefi aşan) logda.

Kural: iki yönde de native modelin üst sınırı Faz 1'in alt sınırının altında → "eşit yanlış alarmda
native model .NET'te daha az kaçırıyor". Ama Faz 1'in düşük yanlış alarmında native model .NET
zararlılarının %59,8'ini, zararlı .NET DLL'lerin %92,7'sini kaçırıyor: .NET için yeterli değil.
