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

## Dosyalar
- `entropy.py` - Shannon entropi hesaplayıcı.
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
  karşılaştırma + sinsi örnekler.
- `model_karsilastir.py` - RF vs LightGBM, ham vs kalibre (5 katlı CV +
  makinedeki 11 örneklem + şüpheli bant). `requirements-experimental.txt`
  gerektirir.
- `ember2024_net_cikar.py` - EMBER2024 .NET test kümesini (C:\ember2024,
  Dot_Net_test.zip) aynı çıkarıcıyla CSV'ye çevirir (+ Aile, Hafta).
- `net_dogrulama.py` - 5 vs 7 özellik; EMBER 2018 CV (.NET / .NET-dışı) ve
  EMBER2024 .NET üzerinde kestirme/körlük testi.

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
- `sef_dataset_ember2024_net_test.csv` - EMBER2024 .NET test, 120.000
  kayıt (60K zararlı + 60K zararsız), 6.8 MB. SADECE doğrulama.
  REPO'DA YOK (`.gitignore`). Yeniden üretmek (~10 sn):
  1. `curl.exe -L -o C:\ember2024\Dot_Net_test.zip https://huggingface.co/datasets/joyce8/EMBER2024/resolve/main/Dot_Net_test.zip`
     (210 MB, Apache-2.0)
  2. `tar -xf Dot_Net_test.zip` (C:\ember2024 içinde; 12 haftalık JSONL, ~1 GB)
  3. `gumruk_memuru` içinde `python ember2024_net_cikar.py`
- EMBER CSV'lerinde NET_mi ve Karma_Mod sütunları da var.
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

## Çalışma Alışkanlıkları
- Uzun işler (tarama, çıkarım, eğitim döngüsü): başta işi say ve %/ETA
  ilerleme bas, `python -u` / `sys.stdout.reconfigure(line_buffering=True)`,
  sonuçları anında dosyaya yaz ve sürdürme (`--devam`) desteği ver.
  Örnek uygulama: `toplu_tarama.py`.
- Dosya içeriğini tamamen belleğe okuyan işlerde boyut sınırı koy
  (toplu_tarama.py: 100 MiB = 100*1024*1024). Sınırsız taramada laptop
  97°C'ye çıktı.

## Ortam Notları
- Bağımlılıklar: `requirements.txt` (ana pipeline, sürümler sabit) ve
  `requirements-experimental.txt` (+ LightGBM, sadece model_karsilastir.py).
- Git: `C:\Program Files\Git\cmd\git.exe` (PATH'te olmayabilir).
- Remote: `origin` = https://github.com/ahmtrntsdln/Chief-Sef (main takip
  ediliyor). Repo'daki eski dosyalar (Chief 1.0/1.1, mimari PDF'ler) korunmalı.
- Ham EMBER verisi (~10 GB) proje DIŞINDA: `C:\ember2018\ember2018`
  (OneDrive'ı şişirmemek için). EMBER2024 .NET test (~1 GB açılmış):
  `C:\ember2024`.
- Tam tarama (System32 + Program Files x2) bu makinede ~2.5 saat sürüyor.
