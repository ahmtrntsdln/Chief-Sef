# Şef Projesi - CLAUDE.md

## Proje
"Şef": yapay zeka destekli, donanımsal izolasyonlu bir siber güvenlik motoru
(savunma amaçlı, EDR/antivirüs benzeri bir sistem). Uzun vadeli mimari TEE/NPU
donanımsal izolasyon, eBPF ile Linux çekirdek izleme ve zero-knowledge
biyometrik kasa içeriyor - ama şu an SADECE Faz 1'deyiz, bunlara dokunma.

## Faz 1 Hedefi: Gümrük Memuru (kavram kanıtı)
Dosyaları çalıştırılmadan önce statik analizle (entropi + PE header/IAT
bilgisi) inceleyip zararlı/zararsız sınıflandıran, doğrulanmış bir
Random Forest modeli üretmek.

## Mevcut Durum - ÖNCE BUNLARI OKU
- `gumruk_memuru/entropy.py` - Shannon entropi hesaplayıcı (çalışıyor, test edildi)
- `gumruk_memuru/Chief_1.2.py` - tam statik analiz motoru (magic byte tespiti,
  bölüm-bazlı entropi, pefile ile IAT/API analizi). v1.1'de KARA_LISTE'de
  substring/çift-sayım hatası vardı (VirtualAlloc, VirtualAllocEx içinde
  geçtiği için iki kez sayılıyordu) - v1.2'de düzeltildi (liste->set, tam eşleme).
- `gumruk_memuru/faz1_dogrulama.py` - ilk Random Forest denemesi %99.9 başarı
  verdi AMA sentetik "zararlı" veri (5 sabit senaryo, random.uniform ile
  üretilmiş) veri sızıntısına yol açmıştı: senaryoların HİÇBİRİNE uymayan
  "sinsi" bir test örneği modeli %100 güvenle kandırdı. BU RİSKİ TEKRARLAMA.
- `gumruk_memuru/toplu_tarama.py` - gerçek zararsız PE dosyalarını tarayıp
  aynı özellikleri çıkarır (non-PE yol test edildi, gerçek PE taraması henüz
  çalıştırılmadı)
- `gumruk_memuru/ember_zararli_cikar.py` - EMBER veri setinden gerçek zararlı
  PE özellik çıkarır. **Çalıştırıldı**: EMBER 2018 v2
  `C:\ember2018\ember2018`'e indirilip açıldı (proje klasörü DIŞINDA,
  OneDrive senkronizasyonunu şişirmemek için - repo'ya girmiyor).
  `EMBER_KLASORU` gerçek yola, JSONL okuma `encoding="utf-8"`'e
  güncellendi. Çıktı: `gumruk_memuru/sef_dataset_zararli_gercek.csv`
  (5700 gerçek zararlı kayıt, repo'ya commit'lendi). Gözlem: ortalama
  bölüm-entropisi ~4.6 (beklenenden düşük - küçük/düşük entropili
  bölümler ortalamayı çekiyor), kayıtların ~%67'sinde Supheli_API=0
  (6 isimlik KARA_LISTE gerçek zararlıda bile zayıf sinyal) - Adım 4
  doğrulamasında bunlara dikkat et.

## Kritik Kural (Tekrar Sızıntı Yaratma)
Zararsız ve zararlı veri AYNI ölçüm yöntemiyle (aynı KARA_LISTE, aynı entropi
mantığı) üretilmeli. Zararsız tarafına PE olmayan dosyalar KARIŞTIRILMAMALI -
EMBER'deki zararlı veri sadece PE dosyalarından oluşuyor, karıştırırsak model
"zararlı mı" yerine "çalıştırılabilir mi" gibi anlamsız bir sinyali öğrenir.

## Kalan Faz 1 İşleri
1. [x] EMBER 2018 v2'yi indir, `ember_zararli_cikar.py` ile 5700 gerçek
       zararlı kayıt çıkar -> `gumruk_memuru/sef_dataset_zararli_gercek.csv`
2. [ ] `toplu_tarama.py`'deki TARANACAK_KLASORLER'i gerçek klasörlerle
       doldurup çalıştır, gerçek zararsız PE CSV'si üret (sadece
       PE_mi=True satırları eğitimde kullan) - SIRADAKİ ADIM, hangi
       klasörlerin taranacağı henüz kullanıcıyla netleşmedi
3. [ ] İki CSV'yi birleştir, Random Forest'i yeniden eğit
4. [ ] `faz1_dogrulama.py`'deki gibi feature_importances_ kontrolü ve
       senaryo-dışı "sinsi" test örnekleriyle doğrula - hedef %100 değil,
       GERÇEKÇİ ve açıklanabilir bir sonuç. Zararlı CSV'deki gözlemlere
       dikkat: ortalama entropi ~4.6 (düşük), %67 kayıtta Supheli_API=0
5. [ ] Sonuçları ve yeni durumu `README.md`'deki yol haritasına işle

## Ortam Notları
- Bu makinede Git YOKTU, bu oturumda `winget install --id Git.Git -e`
  ile kuruldu (2.55.0, `C:\Program Files\Git\cmd\git.exe`). PATH'e
  henüz yansımamış olabilir - yeni terminal gerekebilir.
- Repo şu an SADECE yerel (`git init` yapıldı, henüz GitHub remote'u yok).
  GitHub'a push edilmesi istenirse önce remote + kimlik doğrulama
  (SSH key / `gh auth login` / PAT) kurulmalı.
- Ham EMBER verisi (~10 GB) bilinçli olarak proje klasörü DIŞINDA:
  `C:\ember2018\ember2018`. OneDrive senkronizasyonunu şişirmemek ve
  repo'yu büyütmemek için `.gitignore`'da hariç tutuldu.
