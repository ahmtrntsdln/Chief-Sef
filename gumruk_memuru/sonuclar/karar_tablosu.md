# Karar tablosu (Adım 2c): E2 / E3 ve RF / LightGBM, 300 bin

Ölçütler ve tanımlar: [karar_olcutleri.md](karar_olcutleri.md) (sonuçlardan önce commit'lendi). Bu dosya ölçütleri MEKANİK olarak uygular; **karar kullanıcınındır.**

Test: EMBER2024 Win32+Win64 hafta 52-63 (5635 yerel satır ayrıca). Eğitim boyutu 300,000, tohumlar [42, 1, 2, 3, 4]. Hücre: 5 tohum ortalaması (en düşük–en yüksek). %1 noktası: her türde test zararsızlarının %1'i eşiği aşar (ROC çalışma noktası, üretim eşiği değil).

## 1. Ölçüler

| Model | DLL kaçan %@1 (ANA ÖLÇÜT) | EXE kaçan %@1 | AUC genel | AUC EXE | AUC DLL | Yerel YA %@1 EXE | Yerel YA %@1 DLL | Yerel YA %@0.5 EXE / DLL |
|---|---|---|---|---|---|---|---|---|
| RF E2 | 26.05 (25.53–26.69) | 20.03 (19.02–21.39) | 0.9899 (0.9898–0.9900) | 0.9837 (0.9834–0.9841) | 0.9769 (0.9760–0.9775) | 0.50 [0.14–1.80] (ort. 2.0/402) | 0.31 [0.19–0.50] (ort. 16.0/5233) | 3.83 / 0.74 |
| RF E3 | 23.53 (22.93–24.38) | 18.00 (16.84–19.34) | 0.9854 (0.9851–0.9856) | 0.9831 (0.9826–0.9835) | 0.9840 (0.9839–0.9842) | 0.35 [0.04–1.40] (ort. 1.4/402) | 0.14 [0.06–0.28] (ort. 7.4/5233) | 2.69 / 0.96 |
| LGBM E2 | 39.49 (38.97–40.16) | 30.25 (29.13–30.80) | 0.9771 (0.9767–0.9774) | 0.9607 (0.9599–0.9614) | 0.9568 (0.9563–0.9578) | 0.20 [0.04–1.40] (ort. 0.8/402) | 0.29 [0.17–0.47] (ort. 15.2/5233) | 8.31 / 1.56 |
| LGBM E3 | 35.47 (34.69–36.15) | 29.90 (29.14–30.38) | 0.9638 (0.9634–0.9642) | 0.9573 (0.9566–0.9579) | 0.9677 (0.9675–0.9679) | 0.30 [0.04–1.40] (ort. 1.2/402) | 0.22 [0.13–0.40] (ort. 11.6/5233) | 5.27 / 2.96 |

Gerçekleşen test yanlış alarmı (%1 hedefi, kontrol): RF E2 EXE 0.98 / DLL 0.97; RF E3 EXE 0.96 / DLL 0.97; LGBM E2 EXE 1.00 / DLL 1.00; LGBM E3 EXE 1.00 / DLL 1.00

## 2. Ölçütlerin mekanik uygulaması

| Karşılaştırma (A vs B) | Ölçüt 1: DLL kaçan farkı A−B (tohum oynaması) | Ölçüt 1 sonucu | Ölçüt 2: yerel YA McNemar, anlamlı kötüleşen tohum sayısı (A / B), EXE | aynısı, DLL | Ölçüt 3 |
|---|---|---|---|---|---|
| RF E2 vs RF E3 | +2.52 (1.45) | RF E3 | 0 / 0 | 3 / 0 | —; ÖLÇÜT 2 İHLALİ: RF E2 DLL'de anlamlı kötü |
| LGBM E2 vs LGBM E3 | +4.02 (1.46) | LGBM E3 | 0 / 0 | 0 / 0 | — |
| RF E2 vs LGBM E2 | -13.44 (1.20) | RF E2 | 0 / 0 | 0 / 0 | — |
| RF E3 vs LGBM E3 | -11.95 (1.46) | RF E3 | 0 / 0 | 0 / 0 | — |

Ölçüt 2 eşiği: anlamlı kötüleşme = alarmı fazla olan taraf VE p < 0,05, 5 tohumun en az 3'ünde.

## 3. McNemar ayrıntısı (her tohum: yalnız A alarm / yalnız B alarm, p)

- RF E2 vs RF E3, EXE: t42: 2/0, p=0.5; t1: 0/0, p=1; t2: 1/0, p=1; t3: 0/1, p=1; t4: 3/2, p=1
- RF E2 vs RF E3, DLL: t42: 15/1, p=0.000519; t1: 11/1, p=0.00635; t2: 9/2, p=0.0654; t3: 6/3, p=0.508; t4: 10/1, p=0.0117
- LGBM E2 vs LGBM E3, EXE: t42: 0/0, p=1; t1: 0/0, p=1; t2: 0/2, p=0.5; t3: 0/0, p=1; t4: 0/0, p=1
- LGBM E2 vs LGBM E3, DLL: t42: 7/3, p=0.344; t1: 12/6, p=0.238; t2: 6/5, p=1; t3: 12/10, p=0.832; t4: 9/4, p=0.267
- RF E2 vs LGBM E2, EXE: t42: 3/1, p=0.625; t1: 1/1, p=1; t2: 2/0, p=0.5; t3: 0/1, p=1; t4: 4/1, p=0.375
- RF E2 vs LGBM E2, DLL: t42: 12/8, p=0.503; t1: 9/11, p=0.824; t2: 11/6, p=0.332; t3: 5/11, p=0.21; t4: 11/8, p=0.648
- RF E3 vs LGBM E3, EXE: t42: 1/1, p=1; t1: 1/1, p=1; t2: 1/2, p=1; t3: 1/1, p=1; t4: 3/1, p=0.625
- RF E3 vs LGBM E3, DLL: t42: 5/11, p=0.21; t1: 3/9, p=0.146; t2: 5/6, p=1; t3: 5/12, p=0.143; t4: 3/4, p=1

## 4. Öğrenme eğrisi (LightGBM, bilgi için; ölçüt bu noktada uygulanmadı)

| Aday | Boyut | DLL kaçan %@1 | EXE kaçan %@1 | AUC genel | Yerel YA %@1 EXE / DLL |
|---|---|---|---|---|---|
| E2 | 100,000 | 39.94 (39.73–40.13) | 31.10 (29.61–31.98) | 0.9766 (0.9764–0.9769) | 0.20 / 0.34 |
| E2 | 300,000 | 39.49 (38.97–40.16) | 30.25 (29.13–30.80) | 0.9771 (0.9767–0.9774) | 0.20 / 0.29 |
| E2 | 1,000,000 | 39.39 (39.03–39.64) | 29.34 (29.14–29.47) | 0.9775 (0.9774–0.9777) | 0.25 / 0.32 |
| E2 | 4,158,312 | 39.25 (38.41–39.78) | 29.22 (28.67–29.61) | 0.9776 (0.9774–0.9778) | 0.25 / 0.32 |
| E3 | 100,000 | 35.91 (35.50–36.46) | 31.63 (30.86–32.95) | 0.9628 (0.9620–0.9636) | 0.25 / 0.15 |
| E3 | 300,000 | 35.47 (34.69–36.15) | 29.90 (29.14–30.38) | 0.9638 (0.9634–0.9642) | 0.30 / 0.22 |
| E3 | 522,200 | 35.11 (34.80–35.74) | 30.55 (29.87–31.11) | 0.9640 (0.9638–0.9644) | 0.25 / 0.21 |

E3 1 milyon kurulamadı (eğitimde zararlı DLL 130.550 < 250.000); E3 'tamamı' = 522.200.

**DUR: karar kullanıcının.**

## Not (tablo üretildikten sonra eklendi, ölçütleri değiştirmez)

LightGBM öğrenme eğrisi neredeyse düz (E2 AUC 100 bin 0.9766 → 4,16 milyon 0.9776). Boosting'de bu, veri değil KAPASİTE sınırına işaret eder: varsayılan 100 ağaç / öğrenme hızı 0,1 fazla veriyi kullanamıyor. Ölçütler LightGBM'i bilerek varsayılan ve sabit ayarla kilitledi; bu yüzden "RF > LightGBM" sonucu yalnızca AYARSIZ LightGBM için geçerlidir. Ayarlı LightGBM (ör. daha çok ağaç + erken durdurma) ayrı bir deney olur ve bu karşılaştırmanın parçası değildir.

## UYARI (17 Ekim): bu tablodaki eşik TESTTEN seçildi

Bu tablodaki "%1 noktası" test kümesinin (hafta 52-63) zararsızlarından seçildi: iki adayı aynı yanlış alarmda karşılaştıran bir ROC noktası, ama test bilgisi kullanıyor ve üretim eşiği değil. Yerine geçen ölçüm: [3/esik_boyut_sonuc.md](3/esik_boyut_sonuc.md) — eğitim hafta 0-47, eşik hafta 48-51 doğrulama diliminden (iki sınıf), test SABİT eşikle bir kez (ön kayıt: [3/on_kayit_esik_boyut.md](3/on_kayit_esik_boyut.md)). Ölçütlerin mekanik sonucu değişmedi: RF E3 (DLL kaçan 300 binde %20,9; RF E2 %25,6; LightGBM %35,8 / %39,7).
