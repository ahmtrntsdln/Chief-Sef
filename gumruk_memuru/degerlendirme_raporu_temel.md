# Değerlendirme raporu

Üretildi: 2026-10-07 20:43 · komut: `python degerlendirme.py --ozellik-seti temel --egitim-ornek 100000`

## Kurulum

- Özellikler (5, `temel`): Boyut_Bayt, Sifir_Orani, Ortalama_Entropi, Toplam_API, Supheli_API
- Eğitim(fit): 450,817 kayıt, dönem 2006-12 → 2018-08; her tohumda sınıf dengeli 100,000 örnek, TÜM modellerde aynı
- Eşik doğrulaması: 149,183 kayıt, dönem 2018-09 → 2018-10 (modelin eğitiminde YOK)
- Test `zaman`: 200,000 kayıt, dönem 2018-11 → 2018-12
- Test `zaman+aile`: 100,363 kayıt; zararlılar yalnızca eğitimde görülmeyen 168 aileden (2732 aile eğitimde görüldü); ailesi bilinmeyen zararlılar dışarıda
- Modeller (ayarsız varsayılanlar, 5 tohum [42, 1, 2, 3, 4]): RandomForest, HistGradientBoosting, LightGBM
- Esik: sabit FPR hedefi için DOĞRULAMA zararsızlarından; tek model, tek eşik, alt gruplara ayrı eşik YOK.

## Sızıntı kontrolleri

| Kontrol | Durum | Ayrıntı |
|---|---|---|
| ozellik listesinde etiket/meta yok | gecti | 5 ozellik |
| egitim donemleri < test donemleri | gecti | egitim son 2018-10, test ilk 2018-11 |
| egitim(fit) < esik dogrulamasi | gecti | fit son 2018-08, dogrulama ilk 2018-09 |
| egitim/test dosya kimligi (Dosya_Adi) ortak degil | gecti | 0 ortak dosya |
| zaman+aile test kumesinde egitim ailesi yok | gecti | 168 test ailesi, kesisim 0 |
| birebir ayni ozellik vektoru (sadece rapor) | bilgi | testin %21.7'i egitimde ayni vektorle var (5 ozellikle dogal; etiket celiskisi olcumu bozmaz, ama kolaylastirir) |

## Hedef FPR %1: yakalama oranı (TPR %) ve gerçekleşen FPR %

Hücre: ortalama (en düşük–en yüksek tohum). `†` = alt grupta hedef FPR'de beklenen yanlış pozitif < 10 (zararsız n az), FPR/TPR güvenilmez.

### Test: zaman

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 100,000 | 50.25 (48.38–53.11) | 1.05 (0.97–1.13) | 22.45 (15.44–37.85) | 1.18 (1.03–1.29) | 19.49 (17.74–20.98) | 1.17 (1.12–1.23) |
| PE (.NET disi) | 77,274 / 97,093 | 50.72 (48.79–53.65) | 1.11 (1.02–1.19) | 23.09 (15.87–38.95) | 1.52 (1.33–1.66) | 20.03 (18.24–21.56) | 1.50 (1.44–1.57) |
| .NET | 22,726 / 2,907 | 34.65 (33.09–35.26) | 0.85 (0.65–0.98) | 1.06 (0.93–1.17) | 0.04 (0.04–0.04) | 1.19 (1.00–1.41) | 0.04 (0.03–0.05) |
| EXE | 71,195 / 92,815 | 50.57 (48.57–53.58) | 1.32 (1.20–1.42) | 21.44 (13.99–38.00) | 1.53 (1.38–1.67) | 18.25 (16.37–19.85) | 1.50 (1.43–1.59) |
| DLL | 28,805 / 7,185 | 46.17 (45.50–47.06) | 0.40 (0.38–0.42) | 35.47 (34.18–36.03) | 0.32 (0.18–0.39) | 35.49 (34.93–35.85) | 0.36 (0.30–0.41) |

### Test: zaman+aile

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 363 | 11.79 (8.26–14.88) | 1.05 (0.97–1.13) | 11.79 (7.44–14.33) | 1.18 (1.03–1.29) | 10.52 (6.89–13.50) | 1.17 (1.12–1.23) |
| PE (.NET disi) | 77,274 / 328 | 11.65 (7.93–14.63) | 1.11 (1.02–1.19) | 13.05 (8.23–15.85) | 1.52 (1.33–1.66) | 11.65 (7.62–14.94) | 1.50 (1.44–1.57) |
| .NET | 22,726 / 35 | 13.14 (8.57–17.14) | 0.85 (0.65–0.98) | 0.00 (0.00–0.00) | 0.04 (0.04–0.04) | 0.00 (0.00–0.00) | 0.04 (0.03–0.05) |
| EXE | 71,195 / 341 | 12.32 (8.50–15.25) | 1.32 (1.20–1.42) | 11.73 (7.33–14.37) | 1.53 (1.38–1.67) | 10.32 (6.45–13.20) | 1.50 (1.43–1.59) |
| DLL | 28,805 / 22 | 3.64 (0.00–9.09) | 0.40 (0.38–0.42) | 12.73 (9.09–22.73) | 0.32 (0.18–0.39) | 13.64 (9.09–18.18) | 0.36 (0.30–0.41) |

## Hedef FPR %0.1: yakalama oranı (TPR %) ve gerçekleşen FPR %

Hücre: ortalama (en düşük–en yüksek tohum). `†` = alt grupta hedef FPR'de beklenen yanlış pozitif < 10 (zararsız n az), FPR/TPR güvenilmez.

### Test: zaman

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 100,000 | 37.91 (35.38–39.09) | 0.09 (0.08–0.10) | 3.96 (3.60–4.38) | 0.15 (0.12–0.17) | 3.44 (3.13–3.68) | 0.14 (0.12–0.17) |
| PE (.NET disi) | 77,274 / 97,093 | 38.37 (35.72–39.59) | 0.09 (0.08–0.11) | 4.07 (3.70–4.51) | 0.19 (0.16–0.22) | 3.54 (3.22–3.79) | 0.18 (0.15–0.23) |
| .NET | 22,726 / 2,907 | 22.68 (20.26–25.66) | 0.10 (0.07–0.11) | 0.24 (0.14–0.34) | 0.00 (0.00–0.01) | 0.17 (0.10–0.31) | 0.00 (0.00–0.01) |
| EXE | 71,195 / 92,815 | 37.64 (34.93–38.90) | 0.11 (0.09–0.13) | 3.91 (3.52–4.38) | 0.20 (0.16–0.23) | 3.36 (3.06–3.61) | 0.19 (0.16–0.23) |
| DLL | 28,805 / 7,185 | 41.34 (41.04–41.63) | 0.05 (0.03–0.06) | 4.58 (4.41–4.87) | 0.04 (0.03–0.04) | 4.46 (4.08–4.79) | 0.03 (0.02–0.04) |

### Test: zaman+aile

| Grup | n zararsız / zararlı | RandomForest TPR | RandomForest FPR | HistGradientBoosting TPR | HistGradientBoosting FPR | LightGBM TPR | LightGBM FPR |
|---|---|---|---|---|---|---|---|
| tum | 100,000 / 363 | 1.93 (0.83–3.03) | 0.09 (0.08–0.10) | 1.65 (1.10–2.20) | 0.15 (0.12–0.17) | 1.65 (1.10–2.48) | 0.14 (0.12–0.17) |
| PE (.NET disi) | 77,274 / 328 | 1.40 (0.30–2.13) | 0.09 (0.08–0.11) | 1.83 (1.22–2.44) | 0.19 (0.16–0.22) | 1.83 (1.22–2.74) | 0.18 (0.15–0.23) |
| .NET | 22,726 / 35 | 6.86 (2.86–11.43) | 0.10 (0.07–0.11) | 0.00 (0.00–0.00) | 0.00 (0.00–0.01) | 0.00 (0.00–0.00) | 0.00 (0.00–0.01) |
| EXE | 71,195 / 341 | 2.05 (0.88–3.23) | 0.11 (0.09–0.13) | 1.70 (1.17–2.05) | 0.20 (0.16–0.23) | 1.70 (1.17–2.64) | 0.19 (0.16–0.23) |
| DLL | 28,805 / 22 | 0.00 (0.00–0.00) | 0.05 (0.03–0.06) | 0.91 (0.00–4.55) | 0.04 (0.03–0.04) | 0.91 (0.00–4.55) | 0.03 (0.02–0.04) |

## AUC

| Test | Grup | RandomForest | HistGradientBoosting | LightGBM |
|---|---|---|---|---|
| zaman | tum | 0.9145 (0.9116–0.9179) | 0.8840 (0.8800–0.8874) | 0.8871 (0.8859–0.8889) |
| zaman | PE (.NET disi) | 0.9131 (0.9104–0.9170) | 0.8773 (0.8720–0.8827) | 0.8807 (0.8792–0.8824) |
| zaman | .NET | 0.8665 (0.8621–0.8701) | 0.7965 (0.7828–0.8065) | 0.8013 (0.7896–0.8118) |
| zaman | EXE | 0.9005 (0.8965–0.9056) | 0.8624 (0.8572–0.8676) | 0.8664 (0.8647–0.8684) |
| zaman | DLL | 0.9374 (0.9334–0.9400) | 0.9243 (0.9229–0.9261) | 0.9248 (0.9242–0.9255) |
| zaman+aile | tum | 0.7946 (0.7552–0.8103) | 0.7369 (0.7281–0.7447) | 0.7360 (0.7230–0.7466) |
| zaman+aile | PE (.NET disi) | 0.7852 (0.7371–0.8070) | 0.7194 (0.7096–0.7286) | 0.7181 (0.7044–0.7301) |
| zaman+aile | .NET | 0.8279 (0.8094–0.8497) | 0.7962 (0.7945–0.7983) | 0.7990 (0.7931–0.8041) |
| zaman+aile | EXE | 0.7598 (0.7157–0.7806) | 0.6914 (0.6820–0.7042) | 0.6904 (0.6756–0.7039) |
| zaman+aile | DLL | 0.8662 (0.8437–0.8798) | 0.8300 (0.8096–0.8451) | 0.8257 (0.8194–0.8319) |

## Okuma notları

- **Yorum eşiği:** tohumlar arası fark (parantez) modeller arası farktan büyük/benzerse model üstünlüğü iddia edilmez.
- `zaman+aile` satırları `zaman` satırlarından düşükse fark "yeni aileye genelleme bedeli"dir; zararsız tarafı değişmediği için FPR sütunları iki testte aynı tohumda yakın olmalı.
- Gerçekleşen FPR hedeften belirgin sapıyorsa (özellikle .NET veya DLL'de) tek eşiğin o grupta kalibre olmadığı anlamına gelir; bu düzeltilmedi, bulgu olarak bırakıldı.
- Kullanılmayanlar: tip-içi dengeli eğitim, kalibrasyon, π önsel düzeltmesi (PROJE_DURUMU.md); üretim eşiği için ayrıca ele alınmalı.
- Veri EMBER'in örnekleme dağılımıdır (zararlı oranı gerçek yaygınlık DEĞİL); bu rapordaki FPR EMBER zararsızlarında ölçülür, kendi makinedeki zararsızlarda değil.
