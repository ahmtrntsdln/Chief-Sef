# Şef Projesi - CLAUDE.md

## Proje
"Şef": yapay zeka destekli, donanımsal izolasyonlu bir siber güvenlik motoru
(savunma amaçlı, EDR/antivirüs benzeri bir sistem). Uzun vadeli mimari TEE/NPU
donanımsal izolasyon, eBPF ile Linux çekirdek izleme ve zero-knowledge
biyometrik kasa içeriyor. Faz 1 KAPANDI; Faz 2 (eBPF) henüz başlamadı -
kullanıcı açıkça istemeden Faz 2/3 işine girme.

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

## Kritik Kurallar (Tekrar Sızıntı Yaratma)
1. İki sınıf AYNI ölçüm yöntemiyle üretilmeli. Aynı sütun adı aynı ölçüm
   demek değil: EMBER ordinal import'ları (`ordinal5`) ve boyutu 0 olan
   bölümleri listeliyor, pefile tarafı saymıyor - `ember_zararli_cikar.py`
   bunları atlıyor. Yeni özellik eklerken iki tarafı örnek veriyle karşılaştır.
2. İki sınıf AYNI kaynaktan gelmeli. Zararsız veri tek makineden gelince
   model "bu makineden mi?" sorusunu öğrendi (System32-only: Entropi+Sıfır
   payı %70; çeşitlenince %50; kaynak farkı yine de %96 doğrulukla
   ayırt edilebiliyordu).
3. Zararsız tarafa PE olmayan dosya karıştırma (EMBER sadece PE).
4. Yüksek doğruluk şüphe sebebidir; her modelde feature_importances_ ve
   senaryo-dışı sinsi örneklerle kontrol et.

## Çalışma Alışkanlıkları
- Uzun işler (tarama, çıkarım, eğitim döngüsü): başta işi say ve %/ETA
  ilerleme bas, `python -u` / `sys.stdout.reconfigure(line_buffering=True)`,
  sonuçları anında dosyaya yaz ve sürdürme (`--devam`) desteği ver.
  Örnek uygulama: `toplu_tarama.py`.
- Dosya içeriğini tamamen belleğe okuyan işlerde boyut sınırı koy
  (toplu_tarama.py: 100 MiB = 100*1024*1024). Sınırsız taramada laptop
  97°C'ye çıktı.

## Ortam Notları
- Git: `C:\Program Files\Git\cmd\git.exe` (PATH'te olmayabilir).
- Remote: `origin` = https://github.com/ahmtrntsdln/Chief-Sef (main takip
  ediliyor). Repo'daki eski dosyalar (Chief 1.0/1.1, mimari PDF'ler) korunmalı.
- Ham EMBER verisi (~10 GB) proje DIŞINDA: `C:\ember2018\ember2018`
  (OneDrive'ı şişirmemek için).
- Tam tarama (System32 + Program Files x2) bu makinede ~2.5 saat sürüyor.
