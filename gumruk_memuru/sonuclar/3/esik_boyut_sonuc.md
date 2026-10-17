# Eşik doğrulamadan, test bir kez; son boyut (ön kayıt: on_kayit_esik_boyut.md)

Havuz hafta 0-47 (3,838,526), eşik doğrulaması hafta 48-51 (319,924, iki sınıf), test hafta 52-63 (959,738) SABİT eşikle bir kez. Hücre: tohum ortalaması (en düşük–en yüksek). 2c'deki `karar_tablosu.md` eşiği TESTTEN seçmişti; bu tablo onun yerini alan ölçümdür.

## A. 300 bin, 5 tohum

| Model | DLL kaçan % (ANA) | EXE kaçan % | Test YA % EXE / DLL (hedef 1) | Doğrulama YA % EXE / DLL | Yerel YA % EXE / DLL | AUC |
|---|---|---|---|---|---|---|
| RF E2 | 25.57 (25.23–25.91) | 23.66 (20.91–25.42) | 0.85 / 1.09 | 0.96 / 0.95 | 0.40 / 0.35 | 0.9891 (0.9889–0.9894) |
| RF E3 | 20.90 (20.11–21.52) | 18.46 (17.22–19.52) | 1.02 / 1.37 | 0.94 / 0.98 | 0.50 / 0.21 | 0.9841 (0.9837–0.9845) |
| LGBM E2 | 39.71 (39.45–39.97) | 30.37 (28.78–33.26) | 1.08 / 0.96 | 1.00 / 1.00 | 0.20 / 0.29 | 0.9764 (0.9763–0.9765) |
| LGBM E3 | 35.83 (35.17–36.18) | 30.43 (29.43–31.03) | 1.10 / 1.01 | 1.00 / 1.00 | 0.30 / 0.16 | 0.9621 (0.9616–0.9627) |

### Ölçütlerin mekanik uygulaması (karar_olcutleri.md, değiştirilmedi)

| A vs B | DLL kaçan A−B (tohum oynaması) | Ölçüt 1 | McNemar anlamlı kötü (A / B) EXE | DLL |
|---|---|---|---|---|
| RF E2 vs RF E3 | +4.67 (1.42) | RF E3 | 0 / 0 | 1 / 0 |
| LGBM E2 vs LGBM E3 | +3.89 (1.01) | LGBM E3 | 0 / 0 | 2 / 0 |
| RF E2 vs LGBM E2 | -14.15 (0.69) | RF E2 | 0 / 0 | 1 / 0 |
| RF E3 vs LGBM E3 | -14.93 (1.42) | RF E3 | 0 / 0 | 0 / 0 |

## B/C. Son boyut kuralı (RF E3, tohum 42/1/2)

| Boyut | DLL kaçan % (tohum 42 / 1 / 2) | ort. | std | EXE kaçan % | Test YA % EXE / DLL | Yerel YA % EXE / DLL |
|---|---|---|---|---|---|---|
| 300.000 | 21.52 / 21.02 / 20.11 | 20.88 | 0.72 | 18.57 | 1.02 / 1.38 | 0.50 / 0.20 |
| 483.224 | 19.52 / 19.39 / 18.66 | 19.19 | 0.46 | 16.32 | 0.97 / 1.38 | 0.42 / 0.17 |

kazanç = +1.691 puan, s = 0.720 → kazanç ≥ s → **son boyut 483.224** (mekanik kural).

## Kaynak (tohum 42 modelleri; kurala girmez)

| Model | Dosya MB (joblib, sıkıştırmasız) | RSS artışı MB | Ağaç dizileri MB | Düğüm | Tahmin ms medyan / p95 (tek satır, n_jobs=1, özellik çıkarma hariç) |
|---|---|---|---|---|---|
| V48_RF_E3_300000_42 | 279.0 | 285.2 | 278.9 | 3,656,012 | 4.17 / 6.34 |
| V48_RF_E3_483224_42 | 395.2 | 368.1 | 395.2 | 5,179,764 | 3.64 / 7.47 |
