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
1. Özellik genişletme (.NET bayrağı, overlay/paketleyici belirtileri,
   import kategorileri). Kritik Kural 1: her yeni özellik hem EMBER ham
   JSON'undan hem pefile'dan AYNI şekilde hesaplanabilmeli; önce iki
   tarafı örnek veriyle karşılaştır. En emin verilen yanlış alarmlar
   .NET DLL'leri (tek import, entropi ~4.3).
2. `model_karsilastir.py` ile RF vs boosting'i yeniden karşılaştır.
3. Ancak ondan sonra üç bölgeli eşikler (zararsız / şüpheli / zararlı).
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
- Bağımlılıklar: `requirements.txt` (ana pipeline, sürümler sabit) ve
  `requirements-experimental.txt` (+ LightGBM, sadece model_karsilastir.py).
- Git: `C:\Program Files\Git\cmd\git.exe` (PATH'te olmayabilir).
- Remote: `origin` = https://github.com/ahmtrntsdln/Chief-Sef (main takip
  ediliyor). Repo'daki eski dosyalar (Chief 1.0/1.1, mimari PDF'ler) korunmalı.
- Ham EMBER verisi (~10 GB) proje DIŞINDA: `C:\ember2018\ember2018`
  (OneDrive'ı şişirmemek için).
- Tam tarama (System32 + Program Files x2) bu makinede ~2.5 saat sürüyor.
