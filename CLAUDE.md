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
  yanlış alarm 26.3 -> 7.9, EXE AUC 0.966 -> 0.978, DLL AUC 0.986 -> 0.993;
  EXE kaçan 3.1 -> 8.1 (M2 "EXE ise zararlı" önselini kullanıyordu). Genel
  doğruluk 95.97 -> 94.90: bu KAYIP DEĞİL, gerçekçi hale gelmenin bedeli
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
- `ember_zararsiz_cikar.py` - aynı fonksiyonlarla EMBER zararsız üretir.
- `toplu_tarama.py` - bu makinedeki dosyaları tarar; PE CSV'si SADECE dış
  doğrulama için. İlerleme çubuğu (%/ETA), satır tamponlu çıktı, ara kayıt
  ve `--devam` ile sürdürme var.
- `rf_egit_gercek.py` - ana eğitim + dış doğrulama + eski tasarımla
  karşılaştırma + sinsi örnekler. Sonunda ana modeli `model.pkl`'e kaydeder
  (özellik listesi ve sklearn sürümüyle birlikte).
- `tahmin_et.py` - `python tahmin_et.py <dosya>`: model.pkl ile tek dosya.
  Özellikleri `toplu_tarama.dosyayi_analiz_et` ile çıkarır - dış
  doğrulamada ölçülen AYNI kod; ayrı bir çıkarıcı yazmak raporlanan
  sayıların geçmediği yeni bir ölçüm olurdu. PE olmayan dosyayı reddeder
  (Kural 3), .NET dosyasında körlük uyarısı basar.
- `model_karsilastir.py` - RF vs LightGBM, ham vs kalibre (5 katlı CV +
  makinedeki 11 örneklem + şüpheli bant). `requirements-experimental.txt`
  gerektirir.
- `ember2024_net_cikar.py` - EMBER2024 .NET kümelerini (`test|train`) aynı
  çıkarıcıyla CSV'ye çevirir (+ dizgeler, DLL_mi, Aile, Hafta).
- `dizge_ozellikleri.py` - thrember'ın `string_counts` regex'leri ve dizge
  kuralı (Apache-2.0); JSON kaydından ve ham dosyadan aynı 80 sütun.
- `net_dogrulama.py` - 5 vs 7 özellik; EMBER 2018 CV (.NET / .NET-dışı) ve
  EMBER2024 .NET üzerinde kestirme/körlük testi.
- `net_model.py` - DENEYSEL .NET uzman modeli: M0/M1/M2/M2d ablasyonu,
  tum/EXE/DLL alt grupları, aile bazında kaçma oranı.
- NOT: `toplu_tarama.py` henüz DLL_mi ve dizge özelliklerini üretmiyor
  (Sonraki Adımlar 2'deki yeniden taramada eklenecek).

## Model Seçimi - ŞİMDİLİK KAPALI, özellik sayısı artınca YENİDEN AÇ
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
2. Makinedeki doğrulama setini yeniden tara (~2.5 saat) - özellik seti
   kesinleşince, BİR KEZ.
3. `model_karsilastir.py` ile RF vs boosting'i yeniden karşılaştır.
4. Üç bölgeli eşikler (zararsız / şüpheli / zararlı).
   Şu an 0.2-0.8 bandı EMBER'in 1/4'ünü, makinenin 1/6'sını yutuyor ->
   5 özellik yetersiz; eşikleri şimdi kilitleme. Eşik kuralı: gerçek
   olasılık > C_FP / (C_FP + C_FN) ise işaretle. Maliyet oranı kullanıcı
   kararı (EDR'de kaçan zararlı genelde daha pahalı); gerçek olasılık π'ye
   bağlı olduğu için π için kaba bir aralık da gerekir (FN 10x pahalıyken
   π=%1 -> skor eşiği ~0.91, π=%10 -> ~0.47).

### Veri dosyaları (`gumruk_memuru/`)
- `sef_dataset_zararli_gercek.csv` - EMBER label==1, 5700 kayıt
- `sef_dataset_ember_zararsiz.csv` - EMBER label==0, 5700 kayıt
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
- Git: `C:\Program Files\Git\cmd\git.exe` (PATH'te olmayabilir).
- Remote: `origin` = https://github.com/ahmtrntsdln/Chief-Sef (main takip
  ediliyor). Repo'daki eski dosyalar (Chief 1.0/1.1, mimari PDF'ler) korunmalı.
- Tüm yollar `gumruk_memuru/sef_ayarlar.py`'de; yeni makinede orayı düzenle.
- Ham EMBER verisi (~10 GB) proje DIŞINDA: `C:\ember2018\ember2018`
  (OneDrive'ı şişirmemek için). EMBER2024 .NET: test JSONL + CSV'ler
  `C:\ember2024`, train JSONL `C:\ember2024\train`.
- Tam tarama (System32 + Program Files x2) bu makinede ~2.5 saat sürüyor.
