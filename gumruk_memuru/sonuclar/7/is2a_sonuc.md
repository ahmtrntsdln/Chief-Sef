# İş 2(a) sonucu: M2d'nin yerel meşru .NET dosyalarında yanlış alarmı (30 Ekim 2026)

Ön kayıt `is2a_on_kayit.md` (commit `0366db5`, ölçümden önce). Betik `is2a_yerel_net.py`, çıktı
`is2a_yerel_net.log` / `is2a_yerel_net.csv`. Bir kez koşuldu.

## Geçitler: hepsi TUTTU

| # | Sonuç |
|---|---|
| K1 | yerel set sha256 `5d96007d…` = meta |
| K2 | `NET_mi`=1: 3.471 (EXE 49, DLL 3.422), Karma_Mod 7, 87 M2d sütunu tam, eksik değer yok |
| K3 | yeniden eğitilen M2d (4 × 24.104): eşikler 0,86 / 0,69 ve 0,76 / 0,59; Dot_Net_test 6 satırda kaçan / YA sayıları `uzman_native.csv` ile birebir |
| K4 | native: eşikler 0,83 / 0,69 ve 0,79 / 0,60, Dot_Net_test 6 satır birebir; üretim eşiklerinde yerel .NET alarm 1/3.471 (= `sonuclar/5/net_sonuc.md`) |

## Tablo (yerel meşru .NET, hepsi zararsız; Wilson %95)

| H | Model | EXE (n = 49) | DLL (n = 3.422) | Dot_Net_test YA, aynı eşik (EXE / DLL) |
|---|---|---|---|---|
| %0,45 | M2d | 0/49 [0-7,27] | 0/3.422 [0-0,11] | %0,40 / %0,78 |
| | native | 0/49 [0-7,27] | 0/3.422 [0-0,11] | %0,38 / %0,42 |
| %1,05 | M2d | 0/49 [0-7,27] | 0/3.422 [0-0,11] | %1,21 / %1,13 |
| | native | 0/49 [0-7,27] | 1/3.422 (%0,03) [0,01-0,17] | %0,89 / %0,77 |

Alarm veren dosyalarda Karma_Mod: 0. Betimleyici (hüküm yok): M2d eşik 0,5'te EXE 1/49
(%2,04 [0,36-10,69]), DLL 2/3.422 (%0,06 [0,02-0,21]).

## Ön kayıtlı kurala göre

1. **M2d mutlak:**
   - **DLL:** her iki H'de 0/3.422, Wilson üst sınırı %0,11 < H → **"M2d yerel meşru .NET DLL
     dosyalarında hedefin altında yanlış alarm veriyor."**
   - **EXE:** hüküm yok, çözünürlük yetersiz (0/49'da bile üst sınır %7,27 ≥ H).
2. **M2d ile native (McNemar):** dört hücrenin hepsinde hüküm yok, çünkü uyuşmayan çift sayısı
   yetersiz (b + c = 0, 0, 0, 1 < 6). Bu sonuç "eşit" diye okunmaz.
3. Uzman bağlanmadı; `tahmin_et.py` değişmedi.

## Yorum (betimleyici, hüküm değil)

- Dot_Net_test'te M2d'nin DLL yanlış alarmı aynı eşiklerde %0,78 / %1,13; yerelde 0/3.422. Yerel
  meşru .NET DLL'ler (çoğu Microsoft / dotnet çalışma zamanı) EMBER2024'ün zararsız .NET DLL'lerinden
  "kolay" görünüyor. Native için de aynı tablo var (yerel 0-1 alarm, testte %0,42-0,77).
- Bu ölçüm, Dot_Net_test'teki "uzmanın DLL yanlış alarmı native'den yüksek" bulgusunu yerelde ne
  doğruluyor ne çürütüyor: iki model de bu sette neredeyse hiç alarm vermiyor.

## Sınırlar (ön kayıttaki gibi)

- Kümelilik: .NET dosyalarının çoğu aynı paketlerden geliyor, bu yüzden gerçek belirsizlik
  aralıklardan geniş.
- Asimetri: native seçilirken bu setin yerel YA'sı bir ölçüttü; M2d bu seti hiç görmedi.
- EXE n = 49 olduğu için M2d'nin bilinen zayıf noktası (EXE yanlış alarmı) burada ölçülemedi.
  Daha büyük bir .NET EXE ölçümü ayrı iş olarak not edildi (yapılmadı).
- Bu pakette kaçan zararlı yok; kaçan için İş 2(b) gerekiyor.
