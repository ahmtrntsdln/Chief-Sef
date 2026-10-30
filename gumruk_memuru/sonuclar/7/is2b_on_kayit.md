# İş 2(b) ön kaydı - M2d'nin gerçek akıştaki .NET alt kümesinde (A kümesi) performansı

`FAZ1_KAPANIS.md` (dal `faz1/kapanis`) İş 2 (b). Bu dosya ölçümden ÖNCE yazıldı ve commit'lendi
(30 Ekim 2026). Ölçüm bir kez yapılır; model, eşik, veri, tekilleştirme ve kurallar sonuçtan sonra
DEĞİŞMEZ. Uzman model `tahmin_et.py`'ye BAĞLANMAZ; karar kullanıcınındır.

Ön kayıttan önce yapılan, model skoru İÇERMEYEN yapı incelemeleri (sonuçlar bu tasarımı belirledi):

- **KAYIT ÇİFTLEMESİ (yeni bulgu, ham veride):** EMBER2024 haftalık JSONL'lerinde her kayıt İKİ KEZ
  var: dosyanın ilk yarısı N kayıt, ikinci yarısı aynı N sha256 aynı sırayla (Win64_test ilk hafta:
  20.000 satır, 10.000 eşsiz, kopya farkı tam 10.000 satır). Kopyalar yalnız capa alanlarında
  (`caps`, `mbc`, `ttps`) farklı; projenin kullandığı alanlarda birebir aynı. Sayımlar: Win32/Win64
  test 959.738 satır → 479.856 eşsiz; train 4.158.450 → 2.079.225; Dot_Net_test 120.000 → 59.953
  (ham JSONL'de de 120.000 / 59.953: çıkarım hatası DEĞİL; CLAUDE.md'deki "60K dendi, gerçekte 120K"
  notunun açıklaması bu); Dot_Net_train 519.992 → 259.996. A .NET: 4.848 satır → 2.411 eşsiz (2.398
  sha 2 kopya, 13 sha 4 kopya = iki farklı haftada); aynı sha'da farklı etiket 0, farklı özellik
  vektörü 0. Train × test ortak eşsiz sha 0 (Win32/Win64), A × Dot_Net_train 0, A × Dot_Net_test 0.
  Oranlar çiftlemeden (neredeyse) etkilenmez; n'ler iki katı sayıldığı için önceki Wilson aralıkları
  ve McNemar p'leri DAR / küçük. Bu bulgunun önceki sonuçlara etkisi bu paketin konusu DEĞİL; ayrı
  iş olarak kullanıcıya bildirildi.
- **Popülasyon farkı:** A .NET'te Karma_Mod payı %17,3 (418/2.411 eşsiz); zararsızlarda %56,3
  (348/618), zararlılarda %3,9 (70/1.793). Dot_Net_train'de Karma_Mod payı %0,13: M2d karma mod
  dosyaları neredeyse hiç görmedi. Native ise Win32/Win64 train haftalarında bu popülasyonu gördü
  → A'da karşılaştırma native lehine yapısal olarak yanlı olabilir.

## 1. Soru ve sabitler

**Soru:** M2d, Dot_Net_test dışında, gerçek akıştaki .NET dosyalarında (native test haftalarındaki
`NET_mi`=1 dosyalar) ne kadar kaçırıyor ve ne kadar yanlış alarm veriyor; aynı dosyalarda, aynı
yöntemle seçilmiş eşiklerde native modelden daha az mı kaçırıyor?

- **A kümesi:** Win32_test + Win64_test Parquet (`C:\ember2024\parquet`), hafta 52-63, `NET_mi` = 1,
  `Dosya_Adi` (sha256'nın ilk 12 hanesi) ile TEKİLLEŞTİRİLMİŞ, ilk görülen kopya tutulur (Win32
  önce, haftalar sıralı). Beklenen: 2.411 (zararsız EXE 101, zararsız DLL 517, zararlı EXE 1.639,
  zararlı DLL 154). Bu paketin TÜM sayıları tekil kümeden; çiftli küme yalnız geçit K3'te.
- **M2d:** `sonuclar/6/uzman_native.py` tarifi aynen (2(a) ile aynı): Dot_Net_train hafta 0-47,
  (DLL_mi × Etiket) hücre başına 24.104, `random_state=42`, `net_model.rf()`, 87 özellik
  (`DIZGELI_TIPLI`). Eğitim havuzu ÇİFTLİ haliyle kullanılır (tarif ve geçit onunla tanımlı;
  tekilleştirilmiş M2d bu paketin konusu değil).
- **Native:** kayıtlı son model, `tahmin_et.model_yukle()` (SHA-256, Kural 10).
- **Eşikler (AYARLANMAZ; `uzman_native.csv`, Dot_Net hafta 48-51 doğrulama diliminden):** H %0,45:
  M2d 0,86 / 0,69, native 0,83 / 0,69; H %1,05: M2d 0,76 / 0,59, native 0,79 / 0,60 (EXE / DLL).
  İkincil (betimleyici): native üretim eşikleri EXE 0,70 / DLL 0,61.
- **Tanımlar:** kaçan = zararlı ve skor ≤ eşik; yanlış alarm (YA) = zararsız ve skor > eşik; tür
  `DLL_mi`'ye göre. Wilson %95 (`ortak_deney.wilson`). McNemar kesin binom, iki yönlü
  (`karar_tablosu.mcnemar`), α = 0,05.
- **Dot_Net_test (eşit YA koşulu için):** `ember2024_net_test_ozellik.csv`, `Dosya_Adi` ile
  tekilleştirilmiş (beklenen 59.953).

## 2. Ölçüm ve kontroller

Geçit tutmazsa ölçüm DURUR; log saklanır, sonuç tablosu yazılmaz.

| # | Kontrol | Geçme koşulu |
|---|---|---|
| K1 | A verisi | çiftli A .NET 4.848 (208 / 1.054 / 3.278 / 308); her sha 2 ya da 4 kopya, kopyalar arasında etiket ve 87 M2d sütunu birebir; tekil 2.411 ve hücreleri yukarıdaki gibi; 87 sütun var, eksik değer yok; hafta 52-63 |
| K2 | M2d geçidi | doğrulama diliminden `esik_bul` ile eşikler yukarıdaki gibi; Dot_Net_test (çiftli) M2d 6 satırında `kacan_k`/`YA_k` `uzman_native.csv` ile birebir |
| K3 | Native geçidi | aynı yolla native eşikleri ve Dot_Net_test 6 satırı csv ile birebir; ÇİFTLİ A .NET'te üretim eşikleriyle `sonuclar/5/net_olcum.csv` A .NET satırları birebir (EXE kaçan 1.106/3.278, YA 6/208; DLL kaçan 72/308, YA 10/1.054) |
| K4 | Ortak dosya | tekil A × Dot_Net_train eşsiz sha = 0 (değilse o dosyalar çıkarılır, sayısı yazılır) |
| K5 | Dot_Net_test tekil | 59.953 eşsiz; aynı sha'da farklı etiket 0 |

**Ölçüm** (tekil A, bir kez): her H × model (M2d, native) × tür (EXE, DLL, hepsi): kaçan ve YA k/n,
%, Wilson; AUC (eşiksiz, betimleyici). Her H × tür (EXE, DLL): zararlılarda McNemar (b = yalnız M2d
kaçırdı, c = yalnız native kaçırdı). Tekil Dot_Net_test'te aynı eşiklerle M2d ve native YA (koşul
E1 için) ve M2d kaçan (kural 3 için). Betimleyici: Karma_Mod = 0 / 1 alt grupları; tekil A'da en sık
zararlı aileler (n ≥ 30) ve ayrıca `agenttesla` (CLAUDE.md'de izlenecek aile) için kaçan, H %1,05;
native üretim eşiklerinde tekil A.

## 3. Yorum / karar kuralı

1. **M2d - native kaçan (H ve tür başına; EXE, DLL):** hüküm için İKİ eşit-YA koşulu da sağlanmalı:
   E1 tekil Dot_Net_test'te M2d ve native YA'larının Wilson aralıkları örtüşüyor (büyük n, güçlü
   koşul); E2 tekil A'da aynı örtüşme (küçük n, yalnız kaba kaymayı yakalar). İkisi de sağlanırsa
   McNemar: p < 0,05 ve b < c → "M2d A kümesinde native'den anlamlı olarak daha az kaçırıyor";
   p < 0,05 ve b > c → "daha çok"; aksi halde "fark gösterilemedi" ("eşit" DENMEZ).
2. **M2d YA mutlak (A, H ve tür başına):** Wilson üst < H → "A'da hedefin altında"; alt > H →
   "hedefin üstünde"; aralık H'yi içeriyorsa "hedefle farkı gösterilemedi".
3. **Aktarım (M2d, kaçan, tür başına):** tekil A ve tekil Dot_Net_test'teki M2d kaçan aralıkları
   örtüşmüyorsa "M2d'nin kaçanı A'da Dot_Net_test'ten anlamlı olarak farklı (yüksek / düşük)";
   örtüşüyorsa "fark gösterilemedi".
4. AUC, Karma_Mod alt grupları, aileler ve native üretim eşiği satırları betimleyicidir; hüküm üretmez.
5. Sonuç ne olursa olsun uzman bağlanmaz; `tahmin_et.py` .NET kuralı değişmez.

## 4. Hüküm verilmeyen durumlar

- K1-K5'ten biri tutmadı → "hüküm yok: geçit"; hiçbir sayı sonuç olarak raporlanmaz.
- Hücre n < 30 → oran yorumlanmaz, yalnız k/n (ör. Karma_Mod = 1 zararlı DLL, n = 14).
- E1 ya da E2 sağlanmadı → kural 1 için "hüküm yok: eşit yanlış alarm sağlanamadı" (hangisi
  olduğu yazılır). Not: 6/'da (çiftli n ile) DLL ve "hepsi"de E1 sağlanmamıştı; tekil n ile yeniden
  sınanır, sonuç önceden varsayılmaz.
- **Çözünürlük (kural 2):** wilson(0, n) üst ≥ H ise "hüküm yok: çözünürlük yetersiz". Önceden hesap
  (tekil): zararsız EXE n = 101 → %3,66 (her iki H'de hüküm yok); zararsız DLL n = 517 → %0,74
  (H %0,45'te hüküm yok, H %1,05'te uygulanır).
- **McNemar gücü:** b + c < 6 → kural 1 için "hüküm yok: uyuşmayan çift sayısı yetersiz".

## Sınırlar (sonuçtan önce yazıldı)

- **Eşik popülasyonu ≠ A:** eşikler Dot_Net doğrulama diliminden; A'daki .NET zararsızları (hafta
  48-51'de tür başına yalnız onlarca) eşik seçmeye yetmez. A'daki YA kayması tam olarak bunu ölçer.
- **Yapısal asimetri:** native bu popülasyonu (karma mod dahil) eğitimde gördü, M2d görmedi; ayrıca
  native seçilirken A'nın içinde bulunduğu test kümesi bir kez ölçülmüştü (yeni test kullanımı
  değil: aynı tahminlerin alt grup dökümü, 5/'teki gibi).
- **Küçük zararsız n:** EXE 101, DLL 517 → YA aralıkları geniş; E2 zayıf bir koşul.
- **Kümelilik:** EMBER haftalık kotası ve aileler; bağımsızlık varsayan aralıklar iyimser.
- **Çiftli eğitim havuzu:** M2d tarifi çiftli havuzla tanımlı (eğitimde aynı kaydın iki kopyası
  bulunabilir); etkisi bu pakette ölçülmez.
