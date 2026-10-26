# Sonuç: uzman model (M2, M2d) ile native model, Dot_Net_test'te (26 Ekim 2026)

Ön kayıt `on_kayit_uzman_native.md` (commit `9b8ed38`, ölçümden önce). Betik `uzman_native.py`,
çıktı `uzman_native.log` / `uzman_native.csv`. Bir kez koşuldu.

- GEÇİT tuttu: `net_model.py` tarifi (hafta 0-51, 100K) M2d EXE yanlış alarmı %7,34.
- M2 yeniden üretimi (eşik 0,5, belge 3,8 / 4,2 / ~26): kaçan %3,74, yanlış alarm %4,32, EXE yanlış
  alarm %26,47. Yani "%3,8", %4,3 genel ve %26,5 EXE yanlış alarmında ölçülmüş bir kaçan oranı.
- Uzmanlar hafta 0-47'de eğitildi (M2 100.000, M2d 96.416); eşikler hafta 48-51 doğrulama
  diliminden, tür başına; test bir kez. Native kayıtlı model; onun eşikleri de AYNI doğrulama
  diliminden (üretim eşikleri EXE 0,70 / DLL 0,61 burada kullanılmadı).

## Tablo (test: Dot_Net_test, 60.000 zararlı / 60.000 zararsız; Wilson %95)

| Hedef YA | Tür | M2 kaçan (YA) | M2d kaçan (YA) | native kaçan (YA) |
|---|---|---|---|---|
| %0,45 | EXE | %50,07 [49,65-50,49] (%0,27) | %34,07 [33,67-34,46] (%0,40) | %72,58 [72,21-72,96] (%0,38) |
| | DLL | %20,08 [19,02-21,18] (%0,71) | %12,40 [11,53-13,31] (%0,78) | %89,54 [88,69-90,34] (%0,42) |
| | hepsi | %47,44 (%0,66) | %32,17 (%0,74) | %74,07 (%0,42) |
| %1,05 | EXE | %31,40 [31,02-31,79] (%1,48) | %23,46 [23,10-23,81] (%1,21) | %62,80 [62,40-63,21] (%0,89) |
| | DLL | %12,62 [11,75-13,55] (%1,16) | %8,56 [7,83-9,34] (%1,13) | %86,08 [85,12-86,99] (%0,77) |
| | hepsi | %29,76 (%1,20) | %22,15 (%1,14) | %64,84 (%0,79) |

Zararlı EXE 54.740, zararlı DLL 5.260; zararsız EXE 7.436, zararsız DLL 52.564. Eşikler ve
doğrulama yanlış alarmları logda.

## Ön kayıtlı kurala göre

- **Hüküm verilebilen hücreler** (test yanlış alarmları örtüşüyor): EXE'de, H %0,45'te M2 ve M2d,
  H %1,05'te M2d → **uzman model native modelden daha az kaçırıyor** (M2d: %34,07 vs %72,58 ve
  %23,46 vs %62,80).
- **Diğer hücreler:** uzmanların test yanlış alarmı native'inkinden anlamlı olarak yüksek çıktı
  (ör. DLL H %0,45: M2d %0,78 vs native %0,42) → kural gereği "eşit yanlış alarm sağlanamadı",
  hüküm YOK. Kaçan farkları büyük (DLL'de %8-20 vs %86-90) ama bu kural altında karar sayılmaz.
- M2 / M2d (karar konusu değil): her hücrede M2d daha az kaçırıyor; yanlış alarmları yakın.

## Sınırlar

- Eşikler doğrulamadan seçildi ve teste kaydı: doğrulama 48-51 → test 52-63 arasında uzmanların
  yanlış alarmı hedefin üstüne çıktı (zaman kayması; Kural 6'nın beklediği şey).
- H %0,45'te EXE doğrulama eşiği ~2.600 zararsız EXE'den seçildi (8 alarm): kaba.
- Native modelin eşikleri burada .NET doğrulama diliminden seçildi; üretim eşikleriyle (önceki ölçüm,
  %49,77 kaçan / %1,05 YA) karıştırılmamalı.
- Uzman model `tahmin_et.py`'ye bağlanmadı; bağlama ayrı karar.
