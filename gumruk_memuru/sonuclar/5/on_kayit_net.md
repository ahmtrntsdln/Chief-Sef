# Ön kayıt: native model .NET alt grubunda

Bu dosya ölçümden ÖNCE yazıldı ve commit'lendi. Ölçüm bir kez yapılır; model, eşik, özellik ve
alt grup tanımı sonuçtan sonra DEĞİŞMEZ.

## Soru

Son native model (RF E3, `model_native_meta.json`, sha256 `f6b74df8…69ba536`) .NET dosyalarında
ne kadar zararlı kaçırıyor ve ne kadar yanlış alarm veriyor? .NET olmayan dosyalarla ve Faz 1
modelinin güncel .NET zararlılarındaki %92,8'lik (README'de "%93") kaçırma oranıyla karşılaştırma.
Şimdiye kadar son model yalnızca EXE / DLL ayrımıyla ölçüldü; .NET alt grubu ölçülmedi.

## Sabitler (değişmez)

- Model: kayıtlı son model, `tahmin_et.model_yukle()` ile (SHA-256 doğrulamalı, Kural 10).
  Yeniden eğitim yok.
- Eşikler: meta verideki tür eşikleri, EXE 0,70 / DLL 0,61 (`DLL_mi`'ye göre). Hafta 48-51
  doğrulama diliminden seçilmişti; burada AYARLANMAZ. Kaçan = zararlı ve skor ≤ eşik;
  yanlış alarm = zararsız ve skor > eşik (`ortak_deney.olc` ile aynı tanım).
- .NET tanımı: `NET_mi` = 1 (CLR dizini İSİMLE, boyut > 0 ve adres > 0; çıkarıcıların ortak
  kuralı). Model `NET_mi`'yi girdi olarak KULLANMIYOR; yalnız alt grup ayırmak için.
- Güven aralığı: her oran için Wilson %95 (`ortak_deney.wilson`). n < 30 olan hücrede oran
  yorumlanmaz, yalnız k/n yazılır.

## Kümeler

- **A (birincil):** native test kümesi, Win32_test + Win64_test, hafta 52-63 (959.738), modelin
  bir kez ölçüldüğü küme. Yeni test kullanımı değil: aynı tahminlerin alt grup dökümü.
  Bölme: `NET_mi` = 1 / 0, her biri EXE / DLL.
  GEÇİT: alt grupsuz yeniden hesaplanan EXE/DLL kaçan ve yanlış alarm meta verideki
  `test_bir_kez` değerleriyle birebir tutmazsa ölçüm DURUR (tahminler aynı model değil demektir).
- **B (Faz 1 ile aynı küme):** EMBER2024 `Dot_Net_test` (`C:\ember2024\ember2024_net_test_ozellik.csv`,
  120.000 kayıt). Faz 1'in %92,8'i bu kümede, eşik 0,5'te ölçüldü (`net_dogrulama.py`).
  Kontroller: 86 model sütununun hepsi var ve sayısal, eksik değer yok, etiket {0, 1}; hafta
  aralığı raporlanır. Native model `Dot_Net_train`'i görmedi; eğitimi Win32/Win64 hafta 0-47.
  Raporlanan: sabit tür eşiklerinde kaçan / yanlış alarm (EXE / DLL ayrı ve birlikte) ve Faz 1
  ile AYNI eşikte (0,5) kaçan / yanlış alarm.
- **C (üçüncül):** dondurulmuş yerel set (`sef_yerel_dogrulama_5635.csv`, sha256 `5d96007d…262987`,
  YENİDEN TARANMAZ): `NET_mi` = 1 / 0 satırlarında yanlış alarm, EXE / DLL ayrı. sha256 tutmazsa
  C atlanır.

## Yorum kuralları (sonuçtan önce)

1. **Faz 1 ile karşılaştırma (B):** native modelin B'de sabit eşiklerdeki toplam kaçanının Wilson
   üst sınırı %92,8'in altındaysa "native model Faz 1'in .NET körlüğünü azaltıyor" denir. Aynı
   cümle 0,5 eşiğinde de ayrıca sınanır; iki sonuç da yazılır.
2. **.NET hâlâ zayıf nokta mı (A):** aynı tür içinde (EXE ile EXE, DLL ile DLL) .NET kaçanının Wilson
   alt sınırı .NET olmayanın üst sınırından büyükse ".NET'te anlamlı olarak daha çok kaçırıyor"
   denir. Aralıklar örtüşürse "fark gösterilemedi" denir, "eşit" denmez. Yanlış alarm için aynı kural.
3. A ve B farklı çıkarsa ikisi de raporlanır; biri diğerini geçersiz kılmaz (A modelin kendi test
   dağılımı, B EMBER2024'ün ayrı .NET kümesi).
4. Sonuç ne olursa olsun `tahmin_et.py`'deki .NET uyarısı bu ölçümle kaldırılmaz: .NET uzman modeli
   hâlâ bağlı değil. Bu ölçüm uzman modeli bağlama kararının girdisidir, kararın kendisi değil.
5. Sonuç gelene kadar belgelerde ".NET: native modelde ölçülmedi" yazar.
