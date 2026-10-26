# Şef Projesi - CLAUDE.md

## Proje
"Şef": yapay zeka destekli, donanımsal izolasyonlu bir siber güvenlik motoru
(savunma amaçlı, EDR/antivirüs benzeri bir sistem). Uzun vadeli mimari TEE/NPU
donanımsal izolasyon, eBPF ile Linux çekirdek izleme ve zero-knowledge
biyometrik kasa içeriyor. Faz 1 KAPANDI; Faz 2 (eBPF) henüz başlamadı.

## Faz 1: Gümrük Memuru - KAPANDI
Dosyaları çalıştırılmadan önce statik analizle (entropi + PE header/IAT
bilgisi) zararlı/zararsız sınıflandıran, doğrulanmış bir Random Forest.
Kararların gerekçeleri ve hikayesi: `GELISIM_SURECI.md`.

### Nihai sonuç (`gumruk_memuru/rf_egit_gercek.py`)
- Eğitim: EMBER zararlı (5700) + EMBER zararsız (5700). İki sınıf da aynı
  kaynaktan, aynı ölçümle.
- EMBER test seti: %90.1 doğruluk (yanlış alarm %8.1, kaçan zararlı %11.7).
- Dış doğrulama: bu makinedeki 5700 gerçek zararsız PE (eğitimde hiç
  görülmedi) -> yanlış alarm %3.5.
- Özellik önemleri: Toplam_API 0.30, Boyut 0.25, Entropi 0.24, Sıfır oranı
  0.18, Supheli_API 0.03 (6 isimlik KARA_LISTE zayıf sinyal).
- Sinsi 2 örneği (%17 sıfır, 3.8 entropi) %68 zararlı çıkıyor; EMBER'de bu
  profile benzeyen 22 gerçek dosyanın %64'ü zararlı -> model hatası değil,
  profil gerçekten belirsiz.
- ÖLÇÜM NOTU (`dizge_dll_dogrulama.py`): %90.1 İYİMSER. Örneklem havuzu
  EMBER dosyalarının alfabetik ilkinden (test_features.jsonl) sırayla
  toplanmış: 11.400 satırın hepsi dosyanın ilk ~34 bin kaydından, hepsi
  Kasım 2018. 80/20 bölme bu dar pencerenin içinde. Aynı dosyanın geri
  kalan 188.600 kaydında (Kasım+Aralık) ana model: %87.4 doğruluk, AUC
  0.947. Aynı 5 özellik tasarımı zamansal bölmeyle (Ocak-Ekim eğit ->
  Kasım-Aralık test): %83.8, AUC 0.920. Sızıntı değil, ama raporlanacak
  gerçekçi sayı bunlar; %3.5 dış doğrulama ayrı ölçüm, etkilenmiyor.
  Genel ders: Kritik Kural 6.

### BİLİNEN SINIRLAMA: model .NET zararlılarına neredeyse kör (`net_dogrulama.py`)
- Genel %90 doğruluk bir alt grubun çöküşünü gizliyor. EMBER 2018 CV'de
  .NET zararlılarının %52'si kaçıyor (.NET-dışı: %11.5).
- EMBER2024 .NET test (120.000 dosya, Eylül-Aralık 2024, eğitimde hiç
  görülmedi): doğruluk %53, kaçan zararlı %92.8, AUC 0.63 -> yazı-tura.
  Kaçanlar: xworm, njrat, asyncrat, agenttesla, redline, clipbanker...
  (ailelerin %83-99'u).
- Sebep NET_mi bayrağı DEĞİL (bayraksız model A da aynı körlükte): 5
  PE-başlık özelliği .NET dosyalarını birbirinden ayıramıyor (hepsi ~1
  import, benzer entropi) ve EMBER 2018 eğitiminde .NET zararlı az (162).

## .NET Bayrağı (NET_mi, Karma_Mod) - çıkarıcılarda VAR, ana modelde HENÜZ YOK
- `ember_zararli_cikar.py` ve `toplu_tarama.py` aynı kuralla üretiyor: CLR
  dizini İSİMLE aranır, boyut > 0 VE adres > 0. Karma_Mod = .NET + mscoree
  dışında native import (gerçek ILONLY biti EMBER'de yok; bu makinede 68
  mixed-mode dosyanın 62'sini yakaladı, 0 yanlış pozitif).
- Tutarlılık doğrulandı (60 bin EMBER kaydı + 5228 yerel PE): indeks
  kayması, eksik dizin, boyut/adres çelişkisi pratikte yok.
- Etkisi (EMBER 2018 CV): doğruluk %89.65 -> %90.16, .NET yanlış alarmı
  3.1 -> 2.0; ama .NET kaçan zararlısı 52.5 -> 56.8 (".NET ise zararsız"
  kestirmesi gerçek, küçük). EMBER2024 .NET'te kaçan 92.8 -> 93.4.
- `rf_egit_gercek.py` hâlâ 5 özellikte: makinedeki doğrulama seti bu iki
  sütunu içermiyor (yeni tarama gerekir, ~2.5 saat).

## .NET Uzman Modeli - DENEYSEL (`net_model.py`)
- Mimari: NET_mi=1 -> EMBER2024 .NET ile eğitilen uzman model; NET_mi=0 ->
  EMBER 2018 ana model. Kaynaklar tek modelde karıştırılmaz (Kritik Kural 2;
  string_counts EMBER 2018'de yok).
- Veri: Dot_Net_train (520K, ilk 52 hafta) -> 100K alt örnek; test
  Dot_Net_test (120K, son 12 hafta) - zamansal bölme. Eğitim/test ortak
  dosya 0; birebir aynı özellik vektörü %1.6 (çıkarınca sonuç değişmiyor).
  Train'deki 8 kayıt PE değil (`is_pe=0`, 146 baytlık JSON hata metni);
  eskiden `coff` alanı olmadığı için sessizce DLL_mi=0 alıyordu, artık
  atlanıyor (Kural 3). Bu yüzden M1-M2d sayıları ilk ölçümden örneklem
  gürültüsü kadar farklı (ör. M2d EXE yanlış alarm 7.88 -> 7.34);
  sonuçlar aynı. Bu makinedeki 500+500 .NET ölçümü ilk eğitimle yapıldı.
- Dizge özellikleri (`dizge_ozellikleri.py`) thrember'ın KENDİ koduyla aynı
  500 yerel dosyada (148 .NET) karşılaştırıldı: 500/500 birebir aynı.
  Yerelde dosya başına ~0.25 sn (tam tarama süresini uzatır).
- Ablasyon (EMBER2024 .NET test): M0 mevcut model kaçan %92.8 / AUC 0.63;
  M1 yeni veri + temel özellikler kaçan %12.3 / AUC 0.94 (kazancın büyüğü
  VERİDEN); M2 + dizgeler kaçan %3.8, yanlış alarm %4.2, AUC 0.993.
- KESTİRME (üçüncü kez aynı ders): EMBER2024 .NET'te zararsızların ~%90'ı
  DLL, zararlıların ~%90'ı EXE. En önemli özellik DZ_privilege aslında
  manifest/EXE vekili (EXE içinde zararsız %90, zararlı %87'sinde var). M2
  EXE'lerde yanlış alarm %26.3 - genel %4.2 bunu gizliyordu. Manifest
  kelimelerini çıkarmak çözmüyor (%21; tip bilgisi başka özelliklerde de var).
- Çözüm (M2d): eğitim örneklemi her tipin İÇİNDE 50/50 + DLL_mi girdi. EXE
  yanlış alarm 26.5 -> 7.3, EXE AUC 0.966 -> 0.979, DLL AUC 0.986 -> 0.993;
  EXE kaçan 2.9 -> 8.0 (M2 "EXE ise zararlı" önselini kullanıyordu). Genel
  doğruluk 95.97 -> 94.97: bu KAYIP DEĞİL, gerçekçi hale gelmenin bedeli
  (test kümesi de aynı tip dengesizliğini taşıdığı için kestirme orada
  ödüllendiriliyordu). M2d'de en önemli özellikler artık içerik sinyali
  (DZ_http_url, DZ_ort_uzunluk, DZ_url, DZ_entropi, DZ_crypt, DZ_base64);
  DZ_privilege ilk 15'te yok.
- Aile bazında bedel (M2 -> M2d kaçan): xworm/njrat/clipbanker ~0-2'de
  kalıyor; agenttesla 7.0 -> 11.1, formbook 2.8 -> 6.2, remcos 3.2 -> 6.9.
  "(bilinmiyor)" (15.4) ve wacatac (11.9; Microsoft'un jenerik tespit adı)
  homojen aile DEĞİL - bunlardan "M2d X'e karşı zayıf" sonucu çıkarılmaz.
  İzlenecek tanımlı aile: agenttesla. Kaçanların skorları: M2d'de
  agenttesla kaçanlarının %69'u 0.2-0.5 bandında (üç bölgeli eşikte
  "şüpheli" olur), ama 0.2 altında kalan "sessiz kaçan" ~%0.5 -> ~%3.5'e
  çıkıyor. Eşik tasarımında (Sonraki Adımlar 4) bu aile ayrıca ölçülmeli.
- UZMAN vs NATIVE, EŞİT YA'DA (26 Ekim, ön kayıt `sonuclar/6/on_kayit_uzman_native.md`,
  sonuç `.../uzman_native_sonuc.md`): geçit M2d EXE YA 7.34 tuttu; M2 yeniden üretimi eşik
  0.5'te kaçan 3.74 / YA 4.32 / EXE YA 26.47 (belgedeki 3.8 / 4.2). Uzmanlar hafta 0-47'de (M2
  100K, M2d 96.416), eşikler hafta 48-51'den tür başına, test bir kez. Hüküm verilebilen hücreler
  (test YA örtüşüyor) yalnız EXE: H %0.45 M2d kaçan 34.07 vs native 72.58, H %1.05 23.46 vs
  62.80 -> uzman daha az kaçırıyor. DLL ve "hepsi"de uzmanların test YA'sı native'den anlamlı
  yüksek (ör. 0.78 vs 0.42) -> kural gereği hüküm yok (kaçan farkı büyük: 8-20 vs 86-90).
  M2d her hücrede M2'den az kaçırıyor. Uzman henüz tahmin_et'e BAĞLI DEĞİL.
  (1) Karşılaştırma YALNIZCA Dot_Net_test'te; gerçek akıştaki .NET alt kümesinde (A kümesi:
  Win32/Win64 test haftalarındaki NET_mi=1 dosyalar) ve yerel 3.471 meşru .NET dosyasında
  henüz DOĞRULANMADI. (2) DLL'de hüküm yok; eşit yanlış alarmda ROC tabanlı tanı
  karşılaştırması planlı (İş 2c). (3) Bağlama kararı İş 2'nin (a)(b)(c) ölçümlerinden
  SONRA, kullanıcı tarafından verilecek (`sonuclar/6/FAZ1_KAPANIS.md`).
- Üretimde eşik/kalibrasyon: M2d her tip için %50 önsel varsayar. Gerçek
  EXE/DLL zararlı oranı farkı gerçek bir bilgi, atılmamalı: eşik anında
  tipe özel önselle düzelt: p' = p·π_t / (p·π_t + (1-p)(1-π_t)),
  t ∈ {EXE, DLL}. EMBER2024'teki %88/%9 örnekleme artefaktı, gerçek π_t değil.
- Bu makinedeki gerçek zararsız .NET dosyaları (500 EXE + 500 DLL; Program
  Files x2 + Microsoft.NET, <=20 MB), yanlış alarm, %95 Wilson aralığı:
  M2 EXE %15.6 [12.7-19.0], M2d EXE %1.6 [0.8-3.1]; DLL ikisinde de 0/500
  [0-0.8]. Kestirme gerçek dünyada da vardı, M2d onu gideriyor. Uyarı:
  örneklem rastgele değil (os.walk sırasıyla ilk 500) ve kümeli (aynı
  paketten çok dosya) -> gerçek belirsizlik aralıktan geniş. M2d'nin
  alarmları çoğunlukla az-import'lu komut satırı geliştirici araçları.

## Native Model: DLL_mi + EMBER 2018 dizgeleri - DENEYSEL (`dizge_dll_dogrulama.py`)
- Soru: EMBER2024 Win32/Win64'ü (17 GB) indirmeden native modele dizge
  sinyali eklenebilir mi? EMBER 2018 JSON'unda `strings` grubu var ama
  string_counts (77 regex) YOK. Olan: numstrings, avlength, entropy,
  printables (thrember ile satır satır AYNI kod) + tüm dosyada 4 kaba sayım
  (`C:\`, `http(s)://`, `HKEY_`, `MZ`). Tanım EMBER'in kendi koduyla
  doğrulandı: 60K kayıtta iç tutarlılık (printabledist toplamı, entropi,
  histogram sınırı, MZ>=1) ihlalsiz; yerel `dosyadan_ember2018_dizge`
  EMBER'in StringExtractor koduyla 500 yerel dosyada 500/500 birebir.
  Yerelde ucuz (77 regex döngüsü yok).
- KESTİRME BURADA DA VAR (dördüncü kez): EMBER 2018 train'de zararsızların
  %45.7'si, zararlıların %6.3'ü DLL (test: %28.8 / %7.2). Mevcut 5 özellik
  bile tipi dolaylı öğrenmiş: V0 EXE yanlış alarm %19.1 / DLL %8.4, DLL
  kaçan %21.6 / EXE %15.9. DLL_mi'yi DÜZ eklemek (V1) kestirmeyi büyütür:
  DLL yanlış alarm 2.0 ama DLL kaçan %38, EXE yanlış alarm %24.5; genel
  doğruluk sadece +0.3 -> yine genel skor gizliyor.
- Sonuç (zamansal test, Kasım-Aralık 200K, 5 tohum ortalaması; tohum farkı
  genel ~1 puan, AUC ~0.006, .NET kaçan ~12 puan):
  V0 5 temel %83.8 / AUC 0.920; V2 +dizge %86.8 / 0.945 (.NET AUC 0.865 ->
  0.939); V4 +dizge +DLL_mi tip-içi dengeli %86.3 / 0.944, DLL AUC 0.982
  (V2 0.970), DLL kaçan 7.8 (V2 18.6), EXE yanlış alarm 14.2 (V2 17.0),
  EXE kaçan 16.2 (V2 12.7). V4'te DLL_mi önemi 0.027 (V3'te 0.106);
  en önemliler DZ_entropi, Toplam_API, DZ_ort_uzunluk, DZ18_http.
- Yorum: dizge grubu gerçek kazanç (AUC +0.025, tohum farkının ~4 katı).
  EXE'de V2/V4 farkı çoğunlukla eşik/önsel kayması (EXE AUC ikisinde de
  ~0.93) -> .NET modelindeki gibi tipe özel kalibrasyonla çözülür. Aday:
  V4. Ana modele ALINMADI: önce bu makinedeki dış doğrulama setinde
  DLL_mi + dizge sütunları gerekiyor (bkz. Sonraki Adımlar 2).

## Native Model: EMBER2024 (Win32+Win64) + thrember dizgeleri - SEÇİLDİ: RF E3 (`tahmin_et.py`)
- Çalışma kuralı: her yeni model kendi `model/<ad>` dalında; main ile aynı
  protokolle karşılaştırılır, hangi dalın alınacağına kullanıcı karar verir.
- Veri (9 Ekim 2026): HF joyce8/EMBER2024 Win32/Win64 train+test zip'leri
  (21.9 GB, SHA-256 doğrulandı, `ember2024_indir.py`), AÇILMADAN okunur
  (`ember2024_cikar.py`; açılmış ~100 GB). Eğitim 4.158.450 kayıt (hafta 0-51),
  test 959.738 (hafta 52-63). is_pe=0 atlandı (train 1.550, test 262).
- Kural 5 incelemesi (Win64_test, 240K): alanlar Dot_Net kaydıyla aynı;
  string_counts SEYREK (eşleşmeyen desen yazılmaz -> 0, yerel taraf da aynı);
  datadirectories başında isimsiz girdi, 236 kayıtta hiç dizin yok (isimle
  okunduğu için sorun değil); ordinal "DLL:ordinal5"; haftada 20K, 50/50.
- KESTİRME (beşinci kez): zararsızların ~%73'ü DLL, zararlıların ~%6'sı
  (train %64.9 / %6.3). Import'suz: Win32 zararsız DLL'lerin %45'i (bu
  makinedeki zararsız DLL'lerde %19.2 -> örüntü gerçek ama veri setinde abartılı).
  Train->test kayması: zararsız DLL %64.9 -> %73.4, import'suz %13.5 -> %18.4.
- Dış doğrulama: `dogrulama_dizge80.py` aynı 5637 dosyaya 80 dizge sütunu ekledi
  -> 5635 (2 silinmiş, değişen 0; 7 Ekim'deki 3 ortak dizge sütunu 5635/5635
  birebir). %93'ü DLL (EXE yalnız 402 -> geniş aralık).
  SET ESKİYOR: 15 Ekim'de 5635 dosyanın 857'si (%15) diskte yok (güncellemeler,
  ör. dotnet paketleri). 9 Ekim ölçümü geçerli; yeniden ölçüm bu dosyaları kaybeder.
- Kural 1, GERÇEK dosyalarla (yerel ölçüm = thrember ölçümü mü?): 80 dizge sütunu
  Eylül'de 500 yerel dosyada thrember ile 500/500 (o betik repoda YOK). Kalan 6
  sütun (5 temel + DLL_mi) ve NET_mi/Karma_Mod: `thrember_karsilastir.py`, thrember
  0.1.0, 50 yerel dosya (20 EXE, 20 DLL, 5 .NET, 5 import'suz DLL; seed 42) -> 50/50
  birebir (15 Ekim). Böylece 86 model sütununun hepsi gerçek dosyada doğrulandı.
- Sonuç (`ember2024_native_dogrulama.py`; RF 100 ağaç, 100K alt örneklem,
  5 tohum ortalaması; tohum farkı genel ≤0.35 puan, AUC ≤0.001):
  | | doğruluk | YA | kaçan | AUC | EXE YA | DLL kaçan | yerel YA (EXE / DLL) |
  |---|---|---|---|---|---|---|---|
  | ANA (EMBER 2018, 5 öz.) | 55.5 | 10.3 | 78.7 | 0.663 | 11.7 | 68.4 | 3.4 (10.9 / 2.8) |
  | E1 2024, 5 temel | 88.2 | 7.1 | 16.5 | 0.953 | 11.6 | 35.6 | 6.5 (10.9 / 6.1) |
  | E2 +dizge, sınıf dengeli | 93.8 | 3.4 | 9.0 | 0.986 | 7.4 | 24.6 | 1.2 (4.7 / 1.0) |
  | E3 +dizge +DLL_mi, tip-içi | 92.5 | 4.7 | 10.3 | 0.979 | 5.3 | 12.4 | 1.4 (2.7 / 1.3) |
  Yerel YA Wilson %95: ANA 2.9-3.9, E3 1.1-1.7 (EXE 1.5-4.8).
- Yorum: ana model 2024 verisinde çöküyor (import'suz zararlıların %99'u
  kaçıyor). Kazancın büyüğü VERİDEN (E1), dizgeler AUC'yi 0.953 -> 0.986 taşıyor.
  E2'nin genel üstünlüğü DLL kestirmesinden: DLL kaçan 24.6 (E3 12.4), EXE YA
  7.4 (E3 5.3); DLL AUC E3'te daha iyi (0.978 / 0.969), EXE AUC aynı (~0.976).
  Genel doğruluktaki 1.2 puanlık kayıp M2d ve V4'teki gibi gerçekçi olmanın bedeli.
  En önemli özellikler içerik: DZ_http_url, DZ_ort_uzunluk, Sifir_Orani, DZ_url.
- Zayıf kalanlar (tohum 42, E3 kaçan %): floxif 49.7, virut 32.2 (dosya
  bulaştırıcıları: zararsız taşıyıcı statik olarak zararsız görünüyor),
  (bilinmiyor) 16.6, lummastealer 15.1 (E2 12.1), wacatac 9.3.
- .NET alt grubu küçük (testin %0.5'i), tohum farkı 3-5 puan; .NET dosyaları
  zaten uzman modele gidecek (mimari, .NET bölümü). Bu 9 Ekim deneyinden (100 bin,
  eşik testten).
- SON MODEL .NET'TE (26 Ekim, ön kayıt `sonuclar/5/on_kayit_net.md` ölçümden önce
  commit'lendi; sonuç `sonuclar/5/net_sonuc.md`; sabit eşikler, Wilson %95):
  A native test .NET alt grubu: EXE kaçan %33.74 [32.1-35.4] (.NET dışı 17.63), YA
  %2.88 [1.3-6.2] (n=208; .NET dışı 0.82) -> EXE'de anlamlı olarak daha kötü; DLL kaçan
  23.38 [19.0-28.4] vs 19.48 -> fark gösterilemedi (n=308).
  B Dot_Net_test (Faz 1'in %92.8'iyle aynı küme): kaçan %49.77 tür eşiklerinde (YA
  %1.05), %23.29 eşik 0.5'te (YA %4.42); zararlı .NET DLL'lerin %86.71'i kaçıyor (AUC
  0.838). Faz 1'den iyi, ama .NET için yeterli değil -> uzman model bağlanmalı.
  C yerel .NET zararsız YA %0.03 (1/3471); .NET dışı %0.51 [0.28-0.91] (11/2164;
  EXE 0.28, DLL 0.55). Yerel setin %61.6'sı .NET -> raporlanan yerel EXE %0.25 /
  DLL %0.21 kısmen bu karışımla düşük (DLL'in 3422/5233'ü .NET).
  EŞİT YA'DA (ön kayıt `on_kayit_esit_ya.md`, Faz 1 net_dogrulama A modeli aynı kodla
  yeniden üretildi, geçit 92.77 = 92.8): Faz 1'in B'deki YA'sı %0.46 (sitedeki "%3,8"
  M2'nin kaçanı, YA değil). Native o YA'da (τ 0.76, B'den seçilen ROC noktası, üretim eşiği
  değil) kaçan %59.79, zararlı .NET DLL %92.70; Faz 1 native'in %1.05 YA'sında %89.39.
- KARAR SÜRECİ (15-17 Ekim, ayrıntı `gumruk_memuru/sonuclar/`): ölçütler
  sonuçlardan ÖNCE yazıldı ve commit'lendi (`sonuclar/karar_olcutleri.md`): ana
  ölçüt her türde %1 yanlış alarmda DLL'de kaçan zararlı; yerel yanlış alarm
  McNemar'a göre anlamlı kötüleşmemeli; tohum oynaması içindeki fark eşit,
  eşitlikte LightGBM. Kullanıcı kararı: RF E3.
- Eşik (`sonuclar/3/`, ön kayıt `on_kayit_esik_boyut.md`): eğitim havuzu hafta
  0-47, eşik hafta 48-51 doğrulama diliminden (İKİ sınıf), test hafta 52-63 SABİT
  eşikle BİR KEZ. 2c'deki ilk tablo eşiği testten seçmişti (`karar_tablosu.md`'de
  UYARI); doğrulama eşiğiyle yeniden ölçümde mekanik sonuç aynı: 300 binde DLL
  kaçan RF E3 20.9, RF E2 25.6, LightGBM E3 35.8, E2 39.7.
- RF > LightGBM yalnızca AYARSIZ LightGBM için: öğrenme eğrisi düz (100 bin ->
  4,16 milyon AUC 0.9766 -> 0.9776) = kapasite sınırı. Ayarlı LightGBM ayrı,
  ön kayıtlı deney olarak bekliyor.
- Son boyut: ön kayıtlı kural (kazanç < tohum std -> 300 bin). 522.200 zamansal
  doğrulamayla kurulamaz (havuzda zararlı DLL 120.806) -> 483.224. Kazanç 1.69
  puan ≥ s 0.72 -> **483.224**. Kaynak (tohum 42): 300 bin 279 MB / 4.2 ms,
  483.224 395 MB / 3.6 ms (tek satır tahmin, özellik çıkarma hariç).
- SON MODEL (`sonuclar/3/son_model.py`): RF E3, 483.224, tohum 42, hafta 0-47;
  eşik EXE 0.70 / DLL 0.61. Test (bir kez): AUC 0.9865; kaçan EXE %17.7, DLL
  %19.5; yanlış alarm EXE %0.83, DLL %1.43. Yerel yanlış alarm EXE %0.25
  [0.04-1.40], DLL %0.21 [0.12-0.38]. Model `C:\ember2024\model` (414 MB, repoda
  yok); meta `gumruk_memuru/model_native_meta.json` (repoda).
- DLL YANLIŞ ALARMI HEDEFİ AŞIYOR: eşik doğrulamada %1 için seçildi, testte %1.43.
  OLASI neden (ölçülmedi): zaman kayması, hafta 48-51 -> 52-63. Train->test
  zararsız DLL payı %64.9 -> %73.4 (import'suz %13.5 -> %18.4) kaymayı
  gösteriyor ama nedeni kanıtlamıyor: paylar eşiğin seçildiği 48-51. haftalara
  ait değil ve DLL içi yanlış alarm oranı DLL'lerin zararsızlar içindeki
  payından doğrudan etkilenmez. Üretim eşiği zamanla yeniden doğrulanmalı
  (Sonraki Adımlar 4).
- Uçtan uca (`sonuclar/3/uctan_uca.py`): 20/20 - CSV ile 86/86 özellik aynı, tek
  dosya == toplu tahmin, tek modül == eski kod yolu. İlk koşu 18/20: 2 .NET
  dosyası 14 Ekim'de AYNI BOYUTLA güncellenmişti (eski ve yeni kod onlarda da
  aynı) -> aday seçimine "son değişiklik ölçümden önce" koşulu eklendi; başarı
  ölçütü gevşetilmedi, ilk koşunun logu saklı.
- Yerel set ESKİYOR: 857 dosya diskte yok, aynı boyutla güncellenen .NET adayı
  452. Ölçümlerin dayandığı 5.635 satır DONDURULDU: `sef_yerel_dogrulama_5635.csv`
  (repoda yok; sha256 `5d96007d…262987`, `sonuclar/4/yerel_set.md`). Yeniden
  TARANMAZ; yeni ölçüm yeni ön kayıtla yapılır.

## Dosyalar
- `entropy.py` - Shannon entropi hesaplayıcı.
- `sef_sabitler.py` - ölçüm sabitlerinin TEK kaynağı: KARA_LISTE (str) ve
  KARA_LISTE_BAYT (pefile bytes, aynı kümeden türetilir), SIHIRLI_IMZALAR,
  ORDINAL_DESENI, CLR dizin adları. Neden: bunlar 3 dosyada ayrı kopyaydı;
  birini güncelleyip diğerini unutmak iki sınıfı sessizce farklı ölçer
  (Kritik Kural 1). Fonksiyonlar bilerek birleştirilmedi (girdi tipleri
  farklı: pefile nesnesi vs EMBER JSON). Sabit eklerken buraya ekle.
- `sef_ayarlar.py` - makineye özel yollar (EMBER klasörleri, taranacak
  klasörler) ve proje içi veri dosyası adları (CSV'ler, model.pkl).
  sef_sabitler'den AYRI: sabitler ölçümü tanımlar (değişirse veri yeniden
  üretilir), buradakiler sadece yeri - başka makinede sadece bu dosya
  değişir. Neden tek yer: aynı CSV'yi yazan ve okuyan script adını ayrı
  ayrı tanımlıyordu (toplu_tarama yazar, rf_egit_gercek okur). Proje içi
  yollar bu klasöre göre mutlak: script hangi klasörden çalışırsa çalışsın
  aynı dosyalar.
- `Chief_1.2.py` - tam statik analiz motoru (magic byte, bölüm-bazlı entropi,
  pefile ile IAT/API analizi). v1.1'deki KARA_LISTE substring/çift-sayım
  hatası düzeltildi (liste->set, tam eşleme).
- `faz1_dogrulama.py` - TARİHSEL: sentetik veriyle %99.9 veren ilk modelin
  sızıntı kanıtı. Yeni işte kullanma.
- `ember_zararli_cikar.py` - EMBER JSONL'den label'a göre özellik çıkarır
  (`kayitlari_topla(klasor, hedef, etiket)`); ana çalıştırma zararlı üretir.
  `dll_mi` (2018 ve 2024 ortak) ve `ember2018_kayittan` (temel + DLL_mi +
  EMBER 2018 dizge grubu) burada. Repodaki iki EMBER 2018 CSV'si 17 Ekim'de
  şema değişikliğiyle (`7ff591d`) 9 -> 18 sütun oldu; eski 9 sütun birebir
  korundu (doğrulandı, bkz. Veri dosyaları).
- `ember2018_tam_cikar.py` - EMBER 2018'in tüm etiketli kayıtlarını
  (`test|train`) proje dışına CSV'ye çevirir (+ Aile, Ay); ~2 dk.
- `dizge_dll_dogrulama.py` - native model için DLL_mi / dizge ablasyonu,
  zamansal test, 5 tohum, tum/EXE/DLL/.NET.
- `dogrulama_yeniden_olc.py` - dış doğrulama setinin AYNI 5700 dosyasını
  yeni sütunlarla yeniden ölçer (tam tarama yerine). Neden aynı dosyalar:
  özellik değişiminin etkisi örneklem farkı karışmadan ölçülür. Örneklemi
  seed 42 ile kurar (repodakiyle birebir değilse durur), klasörleri
  listeleyip (ad, boyut) ile bulur, eski 5 sütunun HEPSİ tutmayanı eler
  ve sebebini yazar. Repodaki doğrulama setinin üzerine YAZMAZ:
  `..._yeniden.csv` üretir; eleme sayısı rapor edilmeden kullanılmaz.
- `ember_zararsiz_cikar.py` - aynı fonksiyonlarla EMBER zararsız üretir.
- `toplu_tarama.py` - bu makinedeki dosyaları tarar; PE CSV'si SADECE dış
  doğrulama için. İlerleme çubuğu (%/ETA), satır tamponlu çıktı, ara kayıt
  ve `--devam` ile sürdürme var.
- `rf_egit_gercek.py` - ana eğitim + dış doğrulama + eski tasarımla
  karşılaştırma + sinsi örnekler. Sonunda ana modeli `model.pkl`'e kaydeder
  (özellik listesi ve sklearn sürümüyle birlikte).
- `tahmin_et.py` - `python tahmin_et.py <dosya>`: NATIVE model (RF E3, 86
  özellik) ile tek dosya. Özellikleri `ozellik_cikar.dosya_ozellikleri` ile
  çıkarır (dış doğrulamayla AYNI kod, Kural 9); dosya türünü (EXE / DLL /
  .NET) ve türe göre eşiği (EXE 0.70, DLL 0.61) uygular. Model dosyası meta
  verideki SHA-256 ile tutmazsa YÜKLEMEZ (Kural 10). PE olmayan dosyayı
  reddeder (Kural 3); .NET dosyasında uzman modelin henüz bağlı olmadığını
  yazar. KARAR (`karar()`, 26 Ekim): .NET dışı eşik üstü ZARARLI / altı zararsız;
  .NET'te eşik altı BELİRSİZ (asla zararsız; ölçüm `sonuclar/5/net_sonuc.md`),
  eşik üstü .NET EXE OLASI ZARARLI, .NET DLL ZARARLI; NaN / sonsuz / [0, 1] dışı
  skor her dosyada BELİRSİZ (Kural 7). Ölçülen oranlar koda gömülmez, kaynağa
  yönlendirilir. Testler `tests/test_tahmin_karar.py` (model dosyası gerekmez).
  ÇIKIŞ KODLARI (bozucu değişiklik, ayrı commit'ler; `tahmin_et.CIKIS_KODU`): 0 temiz,
  1 hata, 2 BELİRSİZ, 3 ZARARLI, 4 OLASI ZARARLI - yalnız 0 "temiz".
  Komut satırını çağıran betik / CI yok (26 Ekim'de tarandı); içe aktaranlar
  (`uctan_uca.py`, `net_olcum.py`, `esit_ya.py`) çıkış kodunu kullanmıyor. Faz 1'in 5 özellikli `model.pkl`'i artık burada kullanılmıyor
  (`rf_egit_gercek.py` onu hâlâ üretir; tarihsel karşılaştırma için).
- `toplu_tahmin.py` - klasör / çok dosya için `tahmin_et.tahmin`; sayaçlar ayrı: temiz,
  BELİRSİZ, ZARARLI, OLASI ZARARLI, PE değil (`tahmin_et.PEDegilHatasi`), hata (analiz
  edilemeyen). BELİRSİZ hata DEĞİL. `toplu_tarama.py`'den bilerek ayrı: o model yüklemez,
  dış doğrulama setini üretir. Dosya adı yalnız `--liste` ile ekrana. ÇIKIŞ KODU
  (bozucu değişiklik, ayrı commit): EN KÖTÜ sonuç - ZARARLI 3 > OLASI ZARARLI 4 > BELİRSİZ 2 >
  hata 1 > temiz 0; "PE değil" kodu yükseltmez; yol yok ya da hiç PE sınıflanmadı -> uyarı + 1
  (fail-closed: yanlış yol sessizce "temiz" dönmesin). Test: `tests/test_toplu_tahmin.py`.
- `ozellik_cikar.py` - TEK özellik modülü (Kural 9): `MODEL_KOLONLARI` (86,
  E3 sırası), `dosya_ozellikleri(yol)` (toplu_tarama.dosyayi_analiz_et
  `dizge80=True`: 80 thrember dizge sütunu aynı baytlardan, tek okuma) ve
  `dosya_turu`.
- `model_native_meta.json` - son modelin kimliği (repoda): özellik sırası,
  RF parametreleri, tohum, boyut ve boyut kararı, eğitim verisi özeti
  (haftalar, hücreler, Parquet sha256), eşikler, testte bir kez ölçülen
  değerler, yerel set kimliği, sürümler, tarih, kod commit'i, model sha256.
- `sonuclar/` - native model kararının tüm izi; her adımın betiği, logu ve
  küçük tabloları kendi klasöründe: `karar_olcutleri.md` (ön kayıt),
  `ortak_deney.py` (yükleme/örneklem/ölçüm, tek tanım), `0/` Parquet,
  `2a/` LightGBM öğrenme eğrisi, `2b/` RF 300 bin (+ 9 Ekim 100 bin),
  `2c/` + `karar_tablosu.md`, `3/` eşik ve boyut ön kaydı, ölçümü, son model,
  uçtan uca test; `4/` yerel set kimliği; `5/` son modelin .NET ölçümü (ön kayıt + sonuç); `6/` uzman (M2, M2d) vs native, eşit YA. Büyük çıktılar (model, yerel
  tahminler) `C:\ember2024\sonuc` ve `C:\ember2024\model` altında.
- `model_karsilastir.py` - RF vs LightGBM, ham vs kalibre (5 katlı CV +
  makinedeki 11 örneklem + şüpheli bant). `requirements-experimental.txt`
  gerektirir.
- `ember2024_net_cikar.py` - EMBER2024 .NET kümelerini (`test|train`) aynı
  çıkarıcıyla CSV'ye çevirir (+ dizgeler, DLL_mi, Aile, Hafta).
- `dizge_ozellikleri.py` - thrember'ın `string_counts` regex'leri ve dizge
  kuralı (Apache-2.0); JSON kaydından ve ham dosyadan aynı 80 sütun. Ayrıca
  EMBER 2018 strings grubu (8 sütun: DZ_sayi, DZ_ort_uzunluk, DZ_entropi,
  DZ18_*). Yanlış kaynağın kaydı verilirse KeyError - eskiden eksik
  string_counts 77 sütuna sessizce 0 yazardı.
- `net_dogrulama.py` - 5 vs 7 özellik; EMBER 2018 CV (.NET / .NET-dışı) ve
  EMBER2024 .NET üzerinde kestirme/körlük testi.
- `net_model.py` - DENEYSEL .NET uzman modeli: M0/M1/M2/M2d ablasyonu,
  tum/EXE/DLL alt grupları, aile bazında kaçma oranı.
- `toplu_tarama.py` artık DLL_mi + EMBER 2018 dizge grubunu da üretiyor
  (8 sütun, ucuz). thrember'ın 80 sütununu tam taramada VARSAYILAN olarak
  üretmiyor (dosya başına ~0.25 sn, 64K PE'de ~4.5 saat ek);
  `dosyayi_analiz_et(yol, dizge80=True)` aynı baytlardan 80 sütunu da
  üretiyor - `ozellik_cikar.dosya_ozellikleri` (Kural 9) bunu kullanır.
- `ember2024_indir.py` - EMBER2024 zip'lerini indirir: Range ile devam,
  ağ hatasında artan beklemeyle yeniden deneme, HF API'sine göre boyut +
  SHA-256 kontrolü (tutmayan `.bozuk` olarak ayrılır).
- `ember2024_cikar.py` - Win32/Win64 zip'lerinden açmadan özellik çıkarır
  (ember2024_net_cikar ile aynı fonksiyonlar + Tur); haftalık CSV'ler,
  biten hafta atlanır; olağandışı kayıtları sayar (import yok, ölçülebilir
  bölüm yok). Çıktı `C:\ember2024\ozellik\<zip>\`.
- `dogrulama_dizge80.py` - dış doğrulama setine 80 thrember dizge sütunu;
  eski 5 sütun ve 3 ortak dizge sütunu tutmayan dosyayı eler/sayar; `--devam`.
- `ember2024_native_dogrulama.py` - native adaylar (ANA/E1/E2/E3), zamansal
  test, 5 tohum, alt gruplar, yerel YA (Wilson), aile bazında kaçan.
- `thrember_karsilastir.py` - yerel ölçüm ile thrember ölçümü aynı mı (gerçek
  dosyalar, 6 sütun + NET_mi/Karma_Mod). İki adım, iki ortam: `uret` thrember
  ortamında (`C:\ember2024\thr_env`; Windows yol sınırı yüzünden kısa yol,
  signify==0.7.1 sabit), `karsilastir` proje ortamında. 50 kayıt yoksa BAŞARISIZ
  (boş girdiyle "fark yok" sahte geçişi engellenir).

## Model Seçimi
- YENİDEN AÇILDI (86 özellik, 15-17 Ekim): RF vs ayarsız LightGBM, aynı örneklem
  ve tohumlar, eşik doğrulama diliminden. RF açık farkla önde (300 binde DLL
  kaçan RF E3 20.9 / LightGBM E3 35.8). LightGBM'in öğrenme eğrisi düz -> sonuç
  yalnız AYARSIZ LightGBM için; ayarlı LightGBM (sabit bütçe, doğrulama
  diliminde ayar, test bir kez) ayrı ön kayıtlı deney, henüz yapılmadı.
  Aşağısı Faz 1'in (5 özellik) tarihsel karşılaştırması.
- 5 özellik, ayarsız modellerle: RF CV doğruluk %89.65 / AUC 0.963,
  LightGBM %87.96 / 0.952 (fark katlar arası oynaklığın üstünde). RF ile
  devam. Özellik sayısı 10-15+ olunca `model_karsilastir.py` tekrar
  çalıştırılmalı; boosting daha fazla özellikle genelde daha iyi ölçeklenir.
- Kalibrasyon (isotonic): ham RF zaten iyi kalibre (ECE %1.72 -> %0.92).
  Makinedeki isabet artışı (%96.89 -> %97.36) net kazanç değil, eşik
  kayması: yanlış alarm 8.0 -> 6.2, kaçan zararlı 12.7 -> 14.3.
- Olasılıklar EMBER'in %50 zararlı dünyasına göre. Gerçek ortamda zararlı
  çok daha nadir: skor p, ortamdaki zararlı oranı π ise gerçek olasılık
  p·π / (p·π + (1-p)(1-π)) (ör. p=0.93, π=%1 -> ~%12).

## Sonraki Adımlar (bu sırayla)
Sıralama gerekçesi: sonraki adımlar özellik setine bağlı; özellik seti
EMBER2024'e bağlı. 2-4'ü önce yapmak, geçişten sonra hepsini tekrarlamak
demek (taramayı erteleme mantığının aynısı).

1. EMBER2024'e geçiş + `string_counts` tabanlı özellikler - TEK ADIM.
   - İKİ SINIF BİRDEN taşınır (Kritik Kural 2): zararlı 2024 / zararsız
     2018 olursa model yine "hangi veri seti" (2018 vs 2024, lief vs
     pefile) sorusunu öğrenir; ayrıca string_counts EMBER 2018'de yok.
   - Kaynak: 3.2M dosya, 2023-2024, pefile (thrember) ile çıkarılmış,
     Apache-2.0, HuggingFace joyce8/EMBER2024'ten dosya tipi bazında
     (Win32/Win64/Dot_Net train+test zip'leri; Win32_train 11.7 GB,
     Win64_train 5.6 GB, Dot_Net_train 0.9 GB). Haftalık kotayla dengeli ->
     oranlar gerçek yaygınlık değil. Tüm pipeline Kritik Kural 5 kontrol
     listesinden geçmeli.
   - Özellik: `strings.string_counts` (ASCII dizgelerde thrember regex'leri:
     keyboard, clipboard, password, wallet, base64string, url...; .NET
     tip/metod/P/Invoke adları ASCII olduğu için kısmi .NET-içi sinyal).
     Yerel tarafta thrember'ın regex'leri ve `[\x20-\x7f]{5,}` dizge kuralı
     birebir uygulanır (Apache-2.0). Belki `caps` (capa) da.
   - KISIT (Kritik Kural 1): dnfile düzeyindeki özellikler (metod/P/Invoke
     sayısı, IL boyutu, yönetilen kaynak entropisi) hiçbir eğitim
     kaynağında YOK - EMBER ikili dosya dağıtmıyor. Yönetilen kaynaklar
     .rsrc'de değil CLR metadata bölgesinde. Canlı zararlı ikili dosya
     (MalwareBazaar vb.) bu laptopta işlenmez - izolasyon Faz 3'ün konusu.
   - Diğer adaylar (EMBER2024 JSON'unda varsa): overlay/paketleyici
     belirtileri, import kategorileri.
   - YAPILDI (native kısmı, indirmesiz): DLL_mi + EMBER 2018 dizge grubu
     (bkz. "Native Model"). Win32/Win64 string_counts için 17 GB indirme
     hâlâ gerekir; karar .NET ve native sonuçlarına bağlı.
2. Makinedeki doğrulama setini yeniden tara (~2.5 saat) - özellik seti
   kesinleşince, BİR KEZ. Alternatif (daha ucuz): 5700'lük set
   `sef_tarama_tum_dosyalar.csv`'den seed 42 ile birebir yeniden
   kurulabiliyor (5700/5700 doğrulandı). Ama o dosya eski tarama sürümünden:
   tam yol YOK, sadece Dosya_Adi. Klasörleri listeleyip (ad, boyut) ile
   eşleştir, sadece o dosyaları yeniden oku, eski 5 sütunun birebir
   tuttuğunu satır satır kontrol et (dosya taramadan beri değiştiyse at).
3. `model_karsilastir.py` ile RF vs boosting'i yeniden karşılaştır.
   - YAPILDI (native, `sonuclar/2a-2c`, `3/`): RF > AYARSIZ LightGBM. Kalan:
     ayarlı LightGBM, ayrı ön kayıtlı deney (sabit bütçe, doğrulamada ayar,
     test bir kez).
4. Üç bölgeli eşikler (zararsız / şüpheli / zararlı).
   - KISMEN: native modelde türe göre tek eşik (EXE 0.70, DLL 0.61), doğrulama
     diliminden %1 yanlış alarm için. Testte DLL %1.43 (olası neden zaman
     kayması, ölçülmedi) -> üretim eşiği zamanla yeniden doğrulanmalı ve
     gerçek zararlı oranını (π) hesaba katmalı. Şüpheli bant
     ve maliyet oranı hâlâ açık.
   Şu an 0.2-0.8 bandı EMBER'in 1/4'ünü, makinenin 1/6'sını yutuyor ->
   5 özellik yetersiz; eşikleri şimdi kilitleme. Eşik kuralı: gerçek
   olasılık > C_FP / (C_FP + C_FN) ise işaretle. Maliyet oranı kullanıcı
   kararı (EDR'de kaçan zararlı genelde daha pahalı); gerçek olasılık π'ye
   bağlı olduğu için π için kaba bir aralık da gerekir (FN 10x pahalıyken
   π=%1 -> skor eşiği ~0.91, π=%10 -> ~0.47).

### Veri dosyaları (`gumruk_memuru/`)
- `sef_dataset_zararli_gercek.csv` - EMBER label==1, 5700 kayıt
- `sef_dataset_ember_zararsiz.csv` - EMBER label==0, 5700 kayıt
  İkisi 17 Ekim'de ŞEMA DEĞİŞİKLİĞİYLE bir kez yeniden yazıldı: 9 -> 18 sütun
  (DLL_mi + EMBER 2018 dizge grubu), aynı satırlar, eski 9 sütun birebir
  (doğrulandı; rf_egit_gercek.py çıktısı değişmedi: %90.1, 197/5700).
- `sef_yerel_dogrulama_5635.csv` - native model ölçümlerinin dayandığı yerel
  zararsız set (9 Ekim dz80 ölçümünün dondurulmuş kopyası; 5.635 satır, 94
  sütun, dosya adı/yol yok). REPODA YOK (kullanıcı kararı). sha256
  `5d96007d6f21dd1b1b128669639d07cc1b4b56ce73bdc9ce69b213f02b262987`.
  Eski 5700'lük `sef_dataset_zararsiz_gercek.csv` DEĞİŞMEDİ (Faz 1 sayıları
  birebir yeniden üretilebilir kalsın).
- EMBER2024 Win32/Win64 Parquet - proje DIŞINDA: `C:\ember2024\parquet\
  <zip>.parquet` (`sonuclar/0/parquet_cevir.py`, ~36 sn; satır sayıları CSV'lerle
  birebir). Native model: `C:\ember2024\model\model_native.joblib` (414 MB).
- `sef_dataset_zararsiz_gercek.csv` - bu makinenin taraması, 5700 PE
  (533.081 dosyadan 64.263 PE bulundu, random.seed(42) ile örneklendi).
  Repo'da, `Dosya_Adi` sütunu OLMADAN (kurulu yazılımları ortaya koyar).
  toplu_tarama.py onu baştan sütunsuz yazar; isimli hali
  `sef_dataset_zararsiz_gercek_isimli.csv`'ye gider (`.gitignore`'da).
- `sef_tarama_tum_dosyalar.csv` - tüm tarama (tam yollar içerir, büyük);
  `.gitignore`'da.
- EMBER2024 .NET CSV'leri - proje DIŞINDA, REPO'DA YOK (büyük, üretilmiş):
  `C:\ember2024\ember2024_net_test_ozellik.csv` (120.000 kayıt, 60K/60K,
  son 12 hafta) ve `...\ember2024_net_train_ozellik.csv` (520.000 kayıt,
  260K/260K, ilk 52 hafta). Sütunlar: temel + NET_mi/Karma_Mod + 80 dizge
  (DZ_*) + DLL_mi + Aile + Hafta. Yeniden üretmek (Apache-2.0):
  1. `curl.exe -L -o C:\ember2024\Dot_Net_test.zip https://huggingface.co/datasets/joyce8/EMBER2024/resolve/main/Dot_Net_test.zip`
     (210 MB) -> C:\ember2024 içinde `tar -xf Dot_Net_test.zip` (~1 GB JSONL)
  2. Aynı adresten `Dot_Net_train.zip` (894 MB) -> `C:\ember2024\train`
     içinde `tar -xf` (52 haftalık JSONL)
  3. `gumruk_memuru` içinde `python ember2024_net_cikar.py test` (~15 sn)
     ve `python ember2024_net_cikar.py train` (~1 dk)
- EMBER CSV'lerinde NET_mi ve Karma_Mod sütunları da var.
- EMBER 2018 tam CSV'leri - proje DIŞINDA, REPO'DA YOK:
  `C:\ember2018\ember2018_train_ozellik.csv` (600.000 etiketli, Ocak-Ekim)
  ve `..._test_ozellik.csv` (200.000, Kasım-Aralık). Yeniden üretmek: ham
  EMBER 2018 (`C:\ember2018\ember2018`) varken `python ember2018_tam_cikar.py
  test` ve `... train` (toplam ~2 dk).
- `model.pkl` - REPO'DA YOK (`.gitignore`). Neden: (1) üretilmiş veri;
  `python rf_egit_gercek.py` repodaki CSV'lerden ~10 sn'de birebir aynı
  modeli üretir (random_state=42; kayıtlı model dış doğrulamada yine
  197/5700). (2) Pickle sklearn sürümüne bağlı ikili dosya. (3) Pickle
  yüklemek kod çalıştırmak demek - güvenlik projesi indirilen pickle'a
  güvenmeyi alışkanlık haline getirmemeli.
- Veri politikası: üretilmiş veri commit'lenmez; bunun yerine kaynak + script
  talimatı yazılır. İstisnalar (kullanıcı kararı): iki EMBER 2018 CSV'si
  (raporlanan sayılar birebir bunlara dayanıyor; EMBER sunucusunun yıllar
  sonra aynı içerikle kalacağı garanti değil) ve makine taraması CSV'si
  (başka yerde yeniden üretilemez). SINIR: bu dosyalar SADECE şema
  değişikliğinde (yeni sütun) yeniden yazılır, kozmetik sebeple asla -
  her yeniden yazım tüm satırları git geçmişine tekrar ekler.

## Faz 2 (gerçek zamanlı ajan, C/C++) - Yapılacaklar
Faz 2 henüz başlamadı; bunlar ajan C/C++'a taşınırken uyulacak kurallar ve
açık işler.
- [x] KURAL: Ajanın C/C++ tarafında eşik karşılaştırması dar tipte
  yapılmayacak; int32/double + aralık doğrulaması + fail-closed (aralık
  dışı skor = şüpheli). Neden: Faz 1 Python'da, tamsayı taşması yok; C'de
  skor `signed char`'a yazılırsa 128 -> -128 olur ve `skor > 100` kontrolü
  sessizce atlanır (Kritik Kural 7).
- [x] KURAL: C/C++ varsayılan bayrakları `-Wall -Wextra -Wconversion
  -Wsign-conversion -Werror` (Kritik Kural 7). İlk ajan kodu, Makefile /
  CMake ve CI adımı bunlarla yazılır, sonradan eklenmez.
- [x] Regresyon testi yazıldı: `tests/test_esik_sinir.py` +
  `tests/esik_sinir.c`. Üç kontrol: (1) Python eşiği, (2) C'de hatalı sürüm
  tabloda KAÇIRMALI, doğru sürüm GEÇMELİ (hatalı sürüm de geçerse tablo
  taşmayı artık ölçmüyor demektir), (3) proje bayraklarıyla derleyici
  TEK uyarı vermeli, o da hatalı satırda (doğru sürüm temiz derlenmeli).
- [x] -Wconversion'ın daralmayı satır numarasıyla gösterdiği kullanıcının
  ortamında doğrulandı.
- [x] WINDOWS MinGW'DE DOĞRULANDI (17 Ekim 2026; gcc 16.2.0, winget paketi
  `BrechtSanders.WinLibs.POSIX.UCRT` 16.2.0-14.0.0-r2, resmî winget deposu,
  kullanıcı kapsamı, ~916 MB): testin C kısmı ve derleyici kontrolü gerçekten
  koştu. `-Wall -Wextra -Wconversion -Wsign-conversion` TEK uyarı verdi,
  hatalı satırda (`esik_sinir.c:48`, "conversion from 'int' to 'signed char'
  may change value [-Wconversion]"); doğru sürüm temiz. C doğru sürüm 7/7;
  hatalı sürüm 128 ve 255'i (taşma) ve -1'i (aralık kontrolü yok) "temiz"
  sayıyor - beklenen. pytest 63/63 (gcc'siz: 3 skipped). Çıktı:
  `tests/esik_sinir_mingw.log`. Windows uyarlaması: `.dll`, `-fPIC` yalnız
  Linux'ta, uyarı kontrolü `-fsyntax-only` ile, yüklü DLL temizlikten önce
  `FreeLibrary` ile bırakılır (Windows yüklü DLL'i sildirmez).
- [ ] LİNUX'TA YENİDEN KOŞ (Faz 2, WSL/eBPF ortamı): aynı test Linux gcc ile
  (`.so`, `-fPIC`). UBSan iddiası DOĞRULANMADI: MinGW Windows'ta UBSan
  çalışma zamanı sağlamıyor; Linux'ta `-fsanitize=undefined` vermiyor mu,
  clang `-fsanitize=implicit-integer-truncation` veriyor mu, orada ölç.
- [ ] Bu test CI'da derleyiciyle koşsun; yoksa "skipped" sessizce kalıcı
  hale gelir.
- [ ] Skor ölçeğini sabitle: model olasılığı (0-1, double) mı, tamsayı
  yüzde (0-100) mi? Test 0-255 aralığını sınır değerleri denemek için
  kullanıyor; gerçek ölçek kararlaşınca SKOR_MIN/MAX ve ESIK ona uydurulur.

## Kritik Kurallar (Tekrar Sızıntı Yaratma)
1. İki sınıf AYNI ölçüm yöntemiyle üretilmeli. Aynı sütun adı aynı ölçüm
   demek değil: EMBER ordinal import'ları (`ordinal5`) ve boyutu 0 olan
   bölümleri listeliyor, pefile tarafı saymıyor - `ember_zararli_cikar.py`
   bunları atlıyor. Yeni özellik eklerken iki tarafı örnek veriyle karşılaştır.
   EMBER2024 (thrember) farklı: ordinal `DLL:ordinal5` biçiminde; ve
   datadirectories listesinin başında dizin olmayan bir girdi var + isimler
   farklı (CLR = `COM_DESCRIPTOR`, 15. indeks). Alanları İNDEKSLE değil
   İSİMLE oku.
2. İki sınıf AYNI kaynaktan gelmeli. Zararsız veri tek makineden gelince
   model "bu makineden mi?" sorusunu öğrendi (System32-only: Entropi+Sıfır
   payı %70; çeşitlenince %50; kaynak farkı yine de %96 doğrulukla
   ayırt edilebiliyordu).
3. Zararsız tarafa PE olmayan dosya karıştırma (EMBER sadece PE).
4. Yüksek doğruluk şüphe sebebidir; her modelde feature_importances_ ve
   senaryo-dışı sinsi örneklerle kontrol et. Genel skor alt grup
   çöküşünü gizleyebilir (genel doğruluk %90 iken .NET zararlılarının
   sadece %48'i yakalanıyordu) ->
   önemli alt grupları (.NET, paketli, dosya tipi) AYRICA ölç.
5. Her yeni veri kaynağında (EMBER 2018, EMBER2024, ileride başka bir
   kaynak) ordinal/indeks/alan adı varsayımları sabit sayılmaz, isimle ve
   örnekle doğrulanır. Kontrol listesi:
   - Kaynak kodu varsa oku (ör. thrember features.py); yoksa örnek kayıtla.
   - Ordinal / isimsiz girdilerin biçimi (`ordinal5` mi `DLL:ordinal5` mi?)
   - Liste alanlarında indeks -> isim eşlemesi, dizin olmayan ek girdiler,
     isim yazımları (CLR_RUNTIME_HEADER / COM_DESCRIPTOR). İNDEKSLE okuma.
   - Etiket değerleri ve sınıf sayıları (belgelenen sayıya güvenme:
     EMBER2024 .NET test "60K" dendi, gerçekte 120K).
   - Değişiklikten sonra mevcut sütunların birebir aynı kaldığını doğrula.
   - Bozuk/PE olmayan kayıtlar (EMBER2024 `is_pe=0`, eksik `header.coff`):
     `.get(..., [])` ile okuma - sessizce varsayılan değer alırlar. Alanı
     doğrudan oku, eksikse say ve açıkça atla.
   OTOMATİK HALİ: `tests/test_olcum_tutarliligi.py` (`python -m pytest
   tests`, `requirements-dev.txt`). Aynı sahte dosyayı hem EMBER 2018 hem
   EMBER2024 biçimli JSON'a hem pefile tarafına verip 7 sütunun eşitliğini,
   ordinal biçimlerini, CLR'nin isimle bulunmasını, KARA_LISTE'nin tek
   kaynaktan geldiğini kontrol eder. Testler geçmiş hataların (ordinal
   sayımı, boş bölüm, indeksle CLR, v1.1 substring, bytes/str liste
   ayrışması) her biri koda geri sokularak denendi: hepsi yakalanıyor.
   YENİ VERİ KAYNAĞI EKLENİNCE: o kaynağın kayıt biçimini `_ember_kaydi`'na
   yeni bir biçim olarak, yeni ordinal/dizin adlarını ilgili örnek
   listelerine ekle. Test yazılmadan yeni kaynak eğitime girmez.
   Özellik çıkaran kodu değiştirdikten sonra da testleri çalıştır.

6. ZAMAN EKSENİ: train ve test aynı dönemden gelirse (aynı ay, aynı
   dosyanın ardışık kayıtları) aynı kampanyalar/aileler iki tarafta da
   bulunur ve skor yapay olarak kolaylaşır. Kural 4'ten farklı: o "hangi
   alt grup", bu "hangi zaman". Örnek: Faz 1 ana modeli %90.1 (tek dosyanın
   ilk 34K kaydı, hepsi Kasım 2018, içinde 80/20) -> aynı dosyanın geri
   kalanında %87.4 -> zamansal bölmede %83.8. Güvenlik ML'de bilinen
   problem (BODMAS gibi zamansal veri setlerinin varlık sebebi).
   Kontrol listesi (her yeni model / veri kaynağında):
   - Raporlanan ana sayı zamansal bölmeden gelsin: eğitim eski dönem,
     test sonraki dönem (EMBER 2018: Ocak-Ekim -> Kasım-Aralık; EMBER2024:
     ilk 52 hafta -> son 12 hafta).
   - Örneklem havuzu dosya sırasıyla toplanıyorsa hangi döneme düştüğünü
     kontrol et (`kayitlari_topla` alfabetik ilk dosyadan, sırayla topluyor).
   - Aynı-dönem sayısı raporlanacaksa zamansal sayıyla YAN YANA yaz.
   - EŞİK de tarihsel bölmeye tabi: eğitim haftalarından ayrılmış doğrulama
     diliminden seçilir (EMBER2024: hafta 48-51, iki sınıf birden; yalnız
     zararsızları ayırmak iki sınıfı farklı zamanlardan getirir, Kural 2),
     test bu SABİT eşikle BİR KEZ ölçülür. Testten seçilen eşik bir ROC
     noktasıdır, raporlanacak çalışma noktası değildir.
   - Doğrulama dilimini dönem SAYISIYLA değil KAYIT payıyla seç: EMBER 2018
     train'de appeared 2006'ya kadar gidiyor; dönem sayısının %20'si tüm
     2018'i doğrulamaya atıp eğitimde hiç zararlı bırakmıyordu.

7. Eşik ve skor karşılaştırmalarında dar tip kullanma. Genişte tut,
   aralığı doğrula, aralık dışını şüpheli say (fail-closed).
   C/C++ VARSAYILAN BAYRAKLARI: `-Wall -Wextra -Wconversion
   -Wsign-conversion -Werror`. Neden: derleyiciyi konuşturmak en ucuz
   savunma - -Wconversion eşik taşmasını kullanıcının ortamında satır
   numarasıyla gösterdi, bedeli sıfır, kod çalışmadan. -Werror'sız uyarı
   kaybolur. Tek istisna hatayı BİLEREK içeren regresyon dosyaları
   (`tests/esik_sinir.c`): -Werror'sız derlenir, uyarının tam o satırda ve
   sadece orada çıktığı test edilir.
   Ölçüm: Windows MinGW gcc 16.2'de doğrulandı (tek uyarı, hatalı satırda;
   bkz. Faz 2 Yapılacaklar); Linux'ta Faz 2'de yeniden koşulacak.
   UBSan bu daralmayı yakalamaz (gerekçe; ölçüm henüz YOK, Linux'ta
   yapılacak): int -> signed char dönüşümü tanımsız davranış değil,
   uygulamaya bağlı davranış, `-fsanitize=undefined` kapsamıyor (clang'ın
   ayrı `-fsanitize=implicit-integer-truncation`'ı yakalar ama varsayılan
   değil). Test: `tests/test_esik_sinir.py`.

8. TİP-DENGELİ EĞİTİM: dosya tipi (EXE/DLL) sınıfla karışıksa (kestirme beş
   kez görüldü: EMBER2024 .NET %90/%10, EMBER 2018 %45.7/%6.3, EMBER2024
   native %64.9/%6.3 zararsız/zararlı DLL payı) eğitim örneklemi (DLL_mi ×
   Etiket) hücrelerinin HER BİRİNDE eşit sayıda alınır ve DLL_mi girdi olur.
   Tip bilgisini DÜZ eklemek kestirmeyi büyütür (V1: DLL kaçan %38). Ölçüm
   tipe göre ayrı yapılır (EXE / DLL kaçan ve yanlış alarm); genel doğruluk
   bu kestirmeyi ödüllendirir. Genel doğruluktaki düşüş gerçekçi olmanın
   bedelidir, kayıp değil. Tip içi dengenin üst sınırı en küçük hücredir
   (EMBER2024: zararlı DLL); yerine koyarak örnekleme yapılmaz.
9. TEK ÖZELLİK MODÜLÜ: modelin özellikleri tek yerden çıkar
   (`ozellik_cikar.dosya_ozellikleri`); dış doğrulama (`dogrulama_dizge80.py`)
   ve tahmin (`tahmin_et.py`) ONU içe aktarır. İkinci bir birleştirme kopyası
   yazılmaz: biri değişip diğeri eski kalırsa raporlanan yanlış alarm, tahmin
   aracının ölçtüğü şey olmaktan çıkar (Kural 1'in kod tarafı). Kanıt:
   `sonuclar/3/uctan_uca.py` (20/20: CSV ile 86/86, tek == toplu, tek modül ==
   eski kod). Özellik eklenince bu test yeniden koşar.
10. MODEL YALNIZCA HASH DOĞRULANDIKTAN SONRA YÜKLENİR: joblib/pickle yüklemek
   kod çalıştırmak demek. `tahmin_et.model_yukle` model dosyasının SHA-256'sını
   meta verideki (`model_native_meta.json`, repoda) değerle karşılaştırır,
   tutmazsa YÜKLEMEZ. Bu ayrıca eşiklerin başka bir modele uygulanmasını
   engeller (eşikler o modelin doğrulama skorlarından seçildi). Model dosyası
   repoya ve paylaşıma girmez; yalnız meta veri (özellik sırası, sürümler,
   tohum, eşikler, test sonuçları, sha256) girer.

## Çalışma Alışkanlıkları
- Uzun işler (tarama, çıkarım, eğitim döngüsü): başta işi say ve %/ETA
  ilerleme bas, `python -u` / `sys.stdout.reconfigure(line_buffering=True)`,
  sonuçları anında dosyaya yaz ve sürdürme (`--devam`) desteği ver.
  Örnek uygulama: `toplu_tarama.py`.
- `except Exception` ile varsayılan değer döndürme. Neden: özellik
  çıkarımında sessiz bir varsayılan (ör. sıfır oranı 0.0) gerçek ölçüm gibi
  görünür, modele ve raporlara hatasız karışır. Sadece BEKLENEN hatayı
  yakala (dosya okuma: `OSError`, PE: `pefile.PEFormatError`); tek dosya
  araçlarında stderr'e uyarı bas. Toplu taramada dosya başına uyarı yerine
  sayaç kullan (toplu_tarama "atlandi"), yoksa ilerleme çıktısı gömülür.
  Kök dizindeki `Chief 1.1.py` / `Chıef 1.0.py` tarihsel, bilerek dokunulmadı.
- Dosya içeriğini tamamen belleğe okuyan işlerde boyut sınırı koy
  (toplu_tarama.py: 100 MiB = 100*1024*1024). Sınırsız taramada laptop
  97°C'ye çıktı.

## Ortam Notları
- Bağımlılıklar: `requirements.txt` (ana pipeline, sürümler sabit),
  `requirements-experimental.txt` (+ LightGBM, sadece model_karsilastir.py)
  ve `requirements-dev.txt` (+ pytest, testler için).
- Windows uzun yol sınırı (26 Ekim, temiz klon doğrulaması): venv uzun bir yoldaysa
  (ör. Temp altında) `pip install` scikit-learn test dosyalarında MAX_PATH'e takılıyor ve
  paket YARIM kalabiliyor; pytest yine geçti (testler sklearn'ü içe aktarmıyor), hata ancak
  `rf_egit_gercek.py`'de çıktı (`sklearn.utils` yok). Venv'i kısa yolda kur ya da
  `LongPathsEnabled`'ı aç (yönetici); kurulumdan sonra `python -c "import sklearn.ensemble"`.
- Git: `C:\Program Files\Git\cmd\git.exe` (PATH'te olmayabilir).
- Remote: `origin` = https://github.com/ahmtrntsdln/Chief-Sef (main takip
  ediliyor). Repo'daki eski dosyalar (Chief 1.0/1.1, mimari PDF'ler) korunmalı.
- Tüm yollar `gumruk_memuru/sef_ayarlar.py`'de; yeni makinede orayı düzenle.
- Ham EMBER verisi (~10 GB) proje DIŞINDA: `C:\ember2018\ember2018`
  (OneDrive'ı şişirmemek için). EMBER2024 .NET: test JSONL + CSV'ler
  `C:\ember2024`, train JSONL `C:\ember2024\train`.
- Tam tarama (System32 + Program Files x2) bu makinede ~2.5 saat sürüyor.
- C derleyicisi (17 Ekim): MinGW-w64 gcc 16.2.0, resmî winget deposundan
  `BrechtSanders.WinLibs.POSIX.UCRT` 16.2.0-14.0.0-r2 (taşınabilir, kullanıcı
  kapsamı, ~916 MB, yönetici gerekmez). PATH'te `gcc` yok (winget yalnız önekli
  adlar ekledi): `%LOCALAPPDATA%\Microsoft\WinGet\Packages\BrechtSanders.WinLibs.
  POSIX.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\mingw64\bin`'i PATH'e ekle.
  WSL kurulu değil (Faz 2 eBPF için gerekecek; yönetici + yeniden başlatma ister).
  Kaldırma: `winget uninstall --id BrechtSanders.WinLibs.POSIX.UCRT`.
