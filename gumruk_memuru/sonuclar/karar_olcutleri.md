# Karar ölçütleri: E2 / E3 ve RF / LightGBM (native EMBER2024 modeli)

Bu dosya 2a/2b/2c'nin HİÇBİR sonucuna bakılmadan yazıldı ve sonuçlardan önce
commit'lendi (git geçmişindeki tarih kanıttır). Sonuç gördükten sonra ölçüt
değiştirilmez; değiştirilmesi gerekirse eski hali korunur ve nedeni yazılır.

Adaylar (9 Ekim tanımları, `ember2024_native_dogrulama.py`):
- E2: 5 temel + 80 dizge (85 özellik), sınıf dengeli örneklem.
- E3: E2 + DLL_mi (86 özellik), dosya türü (DLL_mi) içinde 50/50 dengeli örneklem.

Veri: eğitim EMBER2024 Win32+Win64 ilk 52 hafta (4.158.450); test son 12 hafta
(hafta 52-63, 959.738). Yerel: `sef_dogrulama_dz80.csv` içindeki saklı 5.635
zararsız satır (YENİDEN TARANMAZ). Tohumlar: 42, 1, 2, 3, 4.

## Tanımlar (ölçütlerden önce sabitlenir)

- Tür: EXE = DLL_mi 0, DLL = DLL_mi 1.
- %1 yanlış alarm noktası: her model ve tohum için, her tür t ayrı:
  τ_t = test kümesindeki t türü ZARARSIZLARIN skorlarının %99'luk dilimi
  (`np.quantile(p, 0.99, method="higher")`); t türü zararsızların en fazla
  %1'i τ_t'yi aşar. Bu, test üzerindeki ROC çalışma noktasıdır (iki adayı aynı
  yanlış alarmda karşılaştırmak için); ÜRETİM EŞİĞİ DEĞİLDİR (o, eşik adımında
  ayrıca seçilir).
- Kaçan zararlı @%1 (t) = t türü test zararlılarından skoru ≤ τ_t olanların oranı.
- Yerel yanlış alarm (t) = yerel t türü satırlardan skoru > τ_t olanların oranı
  (aynı τ_t; yerel küme eşiği belirlemekte kullanılmaz). Wilson %95 aralığıyla.
- Tohum oynaması (bir aday, bir ölçü) = 5 tohumdaki en büyük - en küçük değer.

## Ölçütler (öncelik sırasıyla)

1. ANA ÖLÇÜT: her türde yanlış alarm %1'e sabitlenmişken DLL'de kaçan zararlı
   oranı (5 tohum ortalaması). Düşük olan kazanır.
2. Yerel yanlış alarm, eşleştirilmiş McNemar testine göre anlamlı biçimde
   (p < 0,05) kötüleşmemeli; EXE ve DLL ayrı. Uygulama: her tohumda iki aday
   aynı 5.635 yerel satırda karşılaştırılır; b = yalnız A'nın alarm verdiği,
   c = yalnız B'nin alarm verdiği satır sayısı; kesin (binom) McNemar,
   iki yönlü. A'nın B'ye göre "anlamlı kötüleşmesi" = A'nın alarmı fazla VE
   p < 0,05, 5 tohumun EN AZ 3'ünde. Kötüleşen aday, ölçüt 1'de önde olsa da
   kazanamaz; karar kullanıcıya bırakılır.
3. Ortalamalar arasındaki fark, iki adayın tohum oynamalarının büyüğünden
   küçük ya da eşitse adaylar EŞİT sayılır. Algoritma (RF / LightGBM)
   karşılaştırmasında eşitlikte LightGBM tercih edilir (küçük model, ileride C
   ajanı için). E2 / E3 eşitliğinde karar kullanıcıya bırakılır.

## Karşılaştırma noktası (2c)

- E2 - E3 karşılaştırması, her iki algoritmada da bulunan en büyük ORTAK
  eğitim boyutunda yapılır: 300 bin (RF 1 milyonda koşmaz; E3 1 milyonda
  kurulamaz, bkz. aşağı). Öğrenme eğrisinin diğer noktaları bilgi içindir;
  son modelin eğitim boyutu kararı kullanıcınındır.
- RF - LightGBM karşılaştırması aynı noktada (300 bin), E2 ve E3 için ayrı.

## Veriden gelen sınır (sonuç değil, sayım; Parquet dönüşümünde ölçüldü)

- Eğitimdeki zararlı DLL sayısı 130.550 (Win32 90.608 + Win64 39.942).
  E3 tür içi dengede her (DLL_mi × Etiket) hücresine boyut/4 gerekir:
  300 bin -> 75.000 (yeterli), 1 milyon -> 250.000 (YETERSİZ: bu hücre
  koşturulmaz, yerine koyarak örnekleme yapılmaz). E3 "tamamı" = 4 × 130.550
  = 522.200. E2 "tamamı" = 2 × 2.079.156 = 4.158.312.

## Sabit ayarlar

- RF: `n_estimators=100`, diğerleri varsayılan, `random_state=tohum`.
- LightGBM: varsayılanlar (100 ağaç, öğrenme hızı 0,1, 31 yaprak),
  `random_state=tohum`, `deterministic=True`, `force_row_wise=True`
  (iş parçacığı sayısı sonucu değiştirmesin), `verbose=-1`. Her hücrede aynı.
