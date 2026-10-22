# Değerlendirme raporu

Üretildi: 2026-10-07 20:44 · komut: `python degerlendirme.py --ozellik-seti dizgeli --egitim-ornek 100000`

## Kurulum

- Özellikler (14, `dizgeli`): Boyut_Bayt, Sifir_Orani, Ortalama_Entropi, Toplam_API, Supheli_API, DLL_mi, DZ_sayi, DZ_ort_uzunluk…
- Eğitim(fit): 450,817 kayıt, dönem 2006-12 → 2018-08; her tohumda sınıf dengeli 100,000 örnek, TÜM modellerde aynı
- Eşik doğrulaması: 149,183 kayıt, dönem 2018-09 → 2018-10 (modelin eğitiminde YOK)
- Test `zaman`: 200,000 kayıt, dönem 2018-11 → 2018-12
- Test `zaman+aile`: 100,363 kayıt; zararlılar yalnızca eğitimde görülmeyen 168 aileden (2732 aile eğitimde görüldü); ailesi bilinmeyen zararlılar dışarıda
- Modeller (ayarsız varsayılanlar, 5 tohum [42, 1, 2, 3, 4]): RandomForest, HistGradientBoosting, LightGBM
- Esik: sabit FPR hedefi için DOĞRULAMA zararsızlarından; tek model, tek eşik, alt gruplara ayrı eşik YOK.

## Sızıntı kontrolleri

| Kontrol | Durum | Ayrıntı |
|---|---|---|
| ozellik listesinde etiket/meta yok | gecti | 14 ozellik |
| egitim donemleri < test donemleri | gecti | egitim son 2018-10, test ilk 2018-11 |
| egitim(fit) < esik dogrulamasi | gecti | fit son 2018-08, dogrulama ilk 2018-09 |
| egitim/test dosya kimligi (Dosya_Adi) ortak degil | gecti | 0 ortak dosya |
| zaman+aile test kumesinde egitim ailesi yok | gecti | 168 test ailesi, kesisim 0 |
| birebir ayni ozellik vektoru (sadece rapor) | bilgi | testin %7.5'i egitimde ayni vektorle var (5 ozellikle dogal; etiket celiskisi olcumu bozmaz, ama kolaylastirir) |

## Hedef FPR %1: yakalama oranı (TPR %) ve gerçekleşen FPR %

Hücre: ortalama (en düşük–en yüksek tohum). `†` = alt grupta hedef FPR'de beklenen yanlış pozitif < 10 (zararsız n az), FPR/TPR güvenilmez.

### Test: zaman

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 100,000 | 61.28 (58.99–63.22) | 1.00 (0.94–1.07) | 45.16 (30.57–51.82) | 1.22 (1.17–1.25) | 34.29 (28.65–51.49) | 1.20 (1.13–1.24) |
| PE (.NET disi) | 77,274 / 97,093 | 61.48 (59.12–63.43) | 1.13 (1.04–1.24) | 45.95 (30.84–52.95) | 1.53 (1.47–1.57) | 34.75 (29.02–52.42) | 1.50 (1.42–1.55) |
| .NET | 22,726 / 2,907 | 54.39 (53.29–56.14) | 0.56 (0.51–0.64) | 18.84 (13.90–22.46) | 0.17 (0.16–0.19) | 18.99 (16.13–22.26) | 0.17 (0.12–0.26) |
| EXE | 71,195 / 92,815 | 62.69 (60.23–64.78) | 1.40 (1.31–1.49) | 46.53 (30.45–53.48) | 1.71 (1.64–1.75) | 34.52 (28.64–52.94) | 1.68 (1.58–1.73) |
| DLL | 28,805 / 7,185 | 43.01 (42.44–43.42) | 0.02 (0.01–0.03) | 27.49 (7.72–33.92) | 0.02 (0.01–0.05) | 31.23 (28.70–32.75) | 0.02 (0.00–0.02) |

### Test: zaman+aile

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 363 | 19.56 (19.28–19.83) | 1.00 (0.94–1.07) | 19.34 (18.18–19.83) | 1.22 (1.17–1.25) | 18.79 (16.80–20.11) | 1.20 (1.13–1.24) |
| PE (.NET disi) | 77,274 / 328 | 16.16 (15.55–16.77) | 1.13 (1.04–1.24) | 18.72 (17.68–19.82) | 1.53 (1.47–1.57) | 18.11 (16.77–19.51) | 1.50 (1.42–1.55) |
| .NET | 22,726 / 35 | 51.43 (42.86–54.29) | 0.56 (0.51–0.64) | 25.14 (20.00–31.43) | 0.17 (0.16–0.19) | 25.14 (17.14–31.43) | 0.17 (0.12–0.26) |
| EXE | 71,195 / 341 | 20.65 (20.23–21.11) | 1.40 (1.31–1.49) | 20.53 (19.35–21.11) | 1.71 (1.64–1.75) | 20.00 (17.89–21.41) | 1.68 (1.58–1.73) |
| DLL | 28,805 / 22 | 2.73 (0.00–4.55) | 0.02 (0.01–0.03) | 0.91 (0.00–4.55) | 0.02 (0.01–0.05) | 0.00 (0.00–0.00) | 0.02 (0.00–0.02) |

## Hedef FPR %0.1: yakalama oranı (TPR %) ve gerçekleşen FPR %

Hücre: ortalama (en düşük–en yüksek tohum). `†` = alt grupta hedef FPR'de beklenen yanlış pozitif < 10 (zararsız n az), FPR/TPR güvenilmez.

### Test: zaman

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 100,000 | 41.27 (39.18–43.70) | 0.09 (0.07–0.11) | 7.78 (7.29–8.23) | 0.14 (0.13–0.17) | 7.71 (7.24–8.49) | 0.15 (0.12–0.17) |
| PE (.NET disi) | 77,274 / 97,093 | 41.52 (39.37–44.14) | 0.11 (0.07–0.13) | 7.93 (7.42–8.39) | 0.17 (0.16–0.20) | 7.86 (7.37–8.66) | 0.18 (0.15–0.21) |
| .NET | 22,726 / 2,907 | 32.94 (28.90–35.50) | 0.05 (0.02–0.08) | 2.79 (2.61–2.99) | 0.04 (0.03–0.04) | 2.81 (2.55–2.96) | 0.03 (0.02–0.04) |
| EXE | 71,195 / 92,815 | 41.35 (39.10–43.93) | 0.13 (0.09–0.15) | 7.98 (7.50–8.46) | 0.20 (0.18–0.23) | 7.91 (7.43–8.78) | 0.21 (0.17–0.24) |
| DLL | 28,805 / 7,185 | 40.23 (39.62–40.75) | 0.00 (0.00–0.00) | 5.25 (4.61–5.80) | 0.00 (0.00–0.00) | 5.09 (4.59–5.86) | 0.00 (0.00–0.00) |

### Test: zaman+aile

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 363 | 3.42 (2.20–4.96) | 0.09 (0.07–0.11) | 7.60 (4.96–8.82) | 0.14 (0.13–0.17) | 7.93 (6.89–8.54) | 0.15 (0.12–0.17) |
| PE (.NET disi) | 77,274 / 328 | 2.50 (0.91–3.66) | 0.11 (0.07–0.13) | 7.44 (4.57–8.84) | 0.17 (0.16–0.20) | 7.74 (6.71–8.54) | 0.18 (0.15–0.21) |
| .NET | 22,726 / 35 | 12.00 (2.86–17.14) | 0.05 (0.02–0.08) | 9.14 (8.57–11.43) | 0.04 (0.03–0.04) | 9.71 (8.57–11.43) | 0.03 (0.02–0.04) |
| EXE | 71,195 / 341 | 3.58 (2.35–5.28) | 0.13 (0.09–0.15) | 8.09 (5.28–9.38) | 0.20 (0.18–0.23) | 8.45 (7.33–9.09) | 0.21 (0.17–0.24) |
| DLL | 28,805 / 22 | 0.91 (0.00–4.55) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) | 0.00 (0.00–0.00) |

## AUC

| Test | Grup | RandomForest | HistGradientBoosting | LightGBM |
|---|---|---|---|---|
| zaman | tum | 0.9492 (0.9477–0.9511) | 0.9227 (0.9222–0.9234) | 0.9231 (0.9217–0.9251) |
| zaman | PE (.NET disi) | 0.9441 (0.9424–0.9464) | 0.9154 (0.9148–0.9165) | 0.9155 (0.9140–0.9180) |
| zaman | .NET | 0.9565 (0.9545–0.9608) | 0.9178 (0.9145–0.9225) | 0.9209 (0.9187–0.9239) |
| zaman | EXE | 0.9436 (0.9417–0.9463) | 0.9099 (0.9090–0.9107) | 0.9106 (0.9088–0.9133) |
| zaman | DLL | 0.9696 (0.9675–0.9713) | 0.9635 (0.9627–0.9643) | 0.9629 (0.9621–0.9637) |
| zaman+aile | tum | 0.8620 (0.8438–0.8785) | 0.8181 (0.8128–0.8314) | 0.8171 (0.8053–0.8287) |
| zaman+aile | PE (.NET disi) | 0.8401 (0.8196–0.8575) | 0.7923 (0.7873–0.8050) | 0.7903 (0.7774–0.8021) |
| zaman+aile | .NET | 0.9478 (0.9443–0.9541) | 0.9279 (0.9206–0.9324) | 0.9318 (0.9274–0.9384) |
| zaman+aile | EXE | 0.8332 (0.8065–0.8550) | 0.7762 (0.7684–0.7968) | 0.7746 (0.7576–0.7933) |
| zaman+aile | DLL | 0.9143 (0.9026–0.9205) | 0.8679 (0.8553–0.8899) | 0.8728 (0.8597–0.8970) |

## Okuma notları

- **Yorum eşiği:** tohumlar arası fark (parantez) modeller arası farktan büyük/benzerse model üstünlüğü iddia edilmez.
- `zaman+aile` satırları `zaman` satırlarından düşükse fark "yeni aileye genelleme bedeli"dir; zararsız tarafı değişmediği için FPR sütunları iki testte aynı tohumda yakın olmalı.
- Gerçekleşen FPR hedeften belirgin sapıyorsa (özellikle .NET veya DLL'de) tek eşiğin o grupta kalibre olmadığı anlamına gelir; bu düzeltilmedi, bulgu olarak bırakıldı.
- Kullanılmayanlar: tip-içi dengeli eğitim, kalibrasyon, π önsel düzeltmesi (PROJE_DURUMU.md); üretim eşiği için ayrıca ele alınmalı.
- Veri EMBER'in örnekleme dağılımıdır (zararlı oranı gerçek yaygınlık DEĞİL); bu rapordaki FPR EMBER zararsızlarında ölçülür, kendi makinedeki zararsızlarda değil.
