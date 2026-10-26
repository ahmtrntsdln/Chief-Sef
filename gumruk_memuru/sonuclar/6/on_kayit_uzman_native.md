# Ön kayıt: .NET uzman modeli (M2, M2d) ile native model, Dot_Net_test'te eşit yanlış alarmda

Bu dosya ölçümden ÖNCE yazıldı ve commit'lendi. Model tarifi, eşik kuralı, hedefler ve yorum kuralı
sonuçtan sonra DEĞİŞMEZ. M2 ve M2d AYRI ele alınır.

## Uzman model: bugüne kadar bilinen (`net_model.py`, CLAUDE.md)

- Veri: EMBER2024 `Dot_Net_train` (519.992 kayıt, hafta 0-51; 8 `is_pe=0` kayıt atlandı),
  test `Dot_Net_test` (120.000, hafta 52-63; 60.000 / 60.000). Zamansal bölme.
- Özellikler: `TEMEL` = 5 temel + `Karma_Mod` (NET_mi bu veride hep 1); M2 = TEMEL + 80 thrember
  dizge sütunu (86); M2d = M2 + `DLL_mi` (87). Native model: 5 temel + 80 dizge + DLL_mi (86;
  `Karma_Mod` YOK).
- Model: RandomForest(100 ağaç, random_state=42), varsayılan ayarlar. Örneklem 100.000: M2 sınıfa
  göre dengeli (50K / 50K), M2d (DLL_mi × Etiket) hücrelerinde eşit (4 × 25K).
- %3,8: M2'nin Dot_Net_test'teki kaçan oranı, eşik 0,5'te; aynı noktada genel yanlış alarm %4,2,
  EXE yanlış alarmı ~%26. M2d: EXE yanlış alarm %7,34 (is_pe düzeltmesinden sonraki değer), EXE
  kaçan %8,0. Bu sayılar eşik 0,5'te ve TEST'ten bakılarak raporlandı; eşik doğrulamadan seçilmedi.

## Bu ölçüm

1. **GEÇİT (tarif doğru mu):** `net_model.py`'nin tarifi aynen (hafta 0-51, 100K) yeniden
   üretilir; M2d EXE yanlış alarmı (eşik 0,5, Dot_Net_test) iki ondalığa yuvarlanınca **7,34**
   olmalı, değilse DURUR. M2'nin yeniden üretilen kaçan / yanlış alarmı belgedeki 3,8 / 4,2 ile
   yan yana yazılır (belgedeki değer düzeltmeden önceki koşudan olabilir; geçit değil).
2. **Uzman modeller (doğrulama dilimi ayrılmış):** aynı tarif, havuz `Dot_Net_train` hafta 0-47
   (479.994 kayıt). Doğrulama dilimi hafta 48-51 (39.998 kayıt, %7,7; iki sınıf birden; Kural 6
   kayıt payı). M2: 100.000 (50K / 50K). M2d: hafta 0-47'de en küçük hücre zararsız EXE 24.104 <
   25.000 olduğundan yerine koymadan en büyük tip-içi boyut **4 × 24.104 = 96.416**.
   `n_jobs` yalnız hız içindir (RF sonucu `random_state` ile belirlenir).
3. **Native model:** kayıtlı son model (SHA-256 doğrulamalı), yeniden eğitilmez. Dot_Net_train'i hiç
   görmedi; doğrulama dilimi onun için de görülmemiş veridir.
4. **Eşikler (üç model için aynı kural):** hedef H ∈ {%0,45, %1,05} (önceki ölçümde native modelin
   Faz 1 noktasındaki ve sabit eşiklerindeki B yanlış alarmı). Her tür t ∈ {EXE, DLL} için
   τ_t = doğrulama dilimindeki t türü zararsız skorlarının farklı değerleri içinde
   pay(p > τ) ≤ H olan EN KÜÇÜK τ (`esit_ya.esik_bul`). Tür, dosyanın `DLL_mi`'sinden.
   Doğrulama n'leri: zararsız EXE 2.604, zararsız DLL 17.396 (H = %0,45'te EXE için ~11 alarm:
   eşik kaba olabilir, raporlanır).
5. **Test BİR KEZ:** Dot_Net_test, her model × H × {EXE, DLL, hepsi}: kaçan zararlı ve gerçekleşen
   yanlış alarm, Wilson %95. Doğrulamadaki yanlış alarm da yazılır.

## Yorum kuralı

- Her H ve tür için uzman (M2 ve M2d ayrı) ile native karşılaştırılır: kaçan Wilson aralıkları
  örtüşmüyorsa "X daha az kaçırıyor", örtüşüyorsa "fark gösterilemedi".
- EŞİTLİK ŞARTI: iki modelin o hücredeki gerçekleşen TEST yanlış alarmının Wilson aralıkları
  örtüşmüyorsa karşılaştırma "eşit yanlış alarm sağlanamadı" diye işaretlenir ve kaçan farkı hüküm
  sayılmaz (eşik doğrulamadan seçildiği için testte kayabilir).
- M2 ile M2d arasındaki fark ayrıca yazılır ama karar konusu değildir.
- Sonuç ne olursa olsun uzman model bu ölçümle `tahmin_et.py`'ye BAĞLANMAZ; bağlama ayrı karar.

## İsteğe bağlı deney (is_dotnet + .NET katmanlı dengeleme): YAPILMAYACAK, gerekçe

Win32 + Win64 havuzunda (hafta 0-47) (DLL_mi, NET_mi, Etiket) hücreleri: zararlı .NET DLL 1.446,
zararsız .NET EXE 2.766. Sekiz hücrede eşit sayı en çok 8 × 1.446 = 11.568 örnek verir (son model
483.224). Bu boyutta sonuç modelin değil örneklemin etkisi olur. Ayrı ön kayıtla, eşit hücre yerine
örnek ağırlığıyla tasarlanabilir; bu ölçümün parçası değil.
