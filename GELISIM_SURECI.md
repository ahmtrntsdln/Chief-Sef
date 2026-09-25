# Şef Projesi — Faz 1 Gelişim Süreci

Bu belge, Şef'in Faz 1'inin ("Gümrük Memuru") nasıl geliştiğini, hangi
kararların neden alındığını ve yol boyunca çıkan sorunların nasıl çözüldüğünü
anlatır. Amaç, sadece "ne yapıldığını" değil, "neden öyle yapıldığını"
belgelemek.

## 1. Başlangıç Konsepti

Şef'in nihai mimarisi üç fazdan oluşuyor: yazılım tabanlı statik analiz →
eBPF ile çekirdek seviyesi izleme → TEE/NPU ile donanımsal izolasyon. İlk
somut adım olarak Faz 1 seçildi: dosyaları çalıştırmadan önce Shannon
Entropisi ve PE (Windows çalıştırılabilir dosya) özellikleriyle statik
analiz yapan bir katman.

## 2. İlk Model ve Veri Sızıntısı

İlk Random Forest modeli, sentetik olarak üretilmiş 2000 "zararlı" satırla
%99.9 başarı gösterdi. Ancak güvenlik modellerinde mükemmel sonuç genelde
iyi haber değildir. İnceleme sonucu neden bulundu: sentetik veri 5 sabit
senaryodan dar aralıklarla (`random.uniform`) üretilmişti. Model gerçek
"zararlı davranışı" değil, bu yapay kalıpları ezberlemişti — senaryoların
hiçbirine uymayan gerçekçi bir test örneği modeli kolayca yanılttı.

## 3. Gerçek Veriye Geçiş: EMBER

Sentetik veri, endüstri standardı **EMBER** veri setiyle değiştirildi.
`ember_zararli_cikar.py`, EMBER'in ham JSONL kayıtlarından gerçek PE
dosyalarının özelliklerini çıkarıyor — aynı API kara listesi ve entropi
mantığıyla, statik analiz motoruyla birebir tutarlı.

## 4. Kod Düzeltmesi: API Sayım Hatası

Statik analiz motorunda (`Chief_1.2.py`) bir substring çakışması bulundu:
`KARA_LISTE` liste olduğu için `"VirtualAlloc"`, `"VirtualAllocEx"` içinde
de eşleşiyor, tek bir API çağrısı iki kez sayılıyordu. Liste `set`'e
çevrilip tam eşleşme kontrolüne geçildi.

## 5. Kaynak Yanlılığı: İkinci Bir Sızıntı Türü

Zararsız veri, kullanıcının kendi bilgisayarından (System32, Program
Files) tarandı. Yeni model %97 başarı verdi, ancak özellik önem
analizinde entropi ve sıfır-oranı özelliklerinin payı %70'e ulaştı.
Neden araştırıldığında: zararsız veri tek, homojen bir kaynaktan
(Microsoft'un imzaladığı sistem dosyaları) geliyordu, zararlı veri ise
EMBER'in çok çeşitli kaynaklarından. Model kısmen "zararlı mı" değil
"Microsoft'un kalıbına mı uyuyor" sorusunu öğreniyordu.

## 6. Çözüm: Simetrik Veri Kaynağı

Bu yanlılığı gidermek için zararsız veri de EMBER'den (`label==0`)
çekildi (`ember_zararsiz_cikar.py`) — artık iki sınıf da aynı kaynaktan,
aynı çeşitlilikte. Kullanıcının bilgisayar taraması çöpe atılmadı;
bağımsız bir gerçek dünya doğrulama seti olarak yeniden konumlandırıldı:
"EMBER ile eğitilen model, gerçek bir bilgisayardaki meşru dosyaları
yanlış pozitif işaretliyor mu?" sorusuna cevap veriyor.

## 7. Donanım Sınırları

Büyük klasörlerin taranması sırasında CPU sıcaklığı 97°C'ye çıktı;
neden, bazı dosyaların (multi-GB) tamamen belleğe okunup entropi
hesaplanmasıydı. 100 MB'lık bir dosya boyutu filtresi eklendi, sıcaklık
89-94°C bandında stabilize oldu. Ayrıca uzun süren işlemler için
ilerleme çubuğu, anlık çıktı ve ara kayıt (checkpoint) mekanizması
eklendi.

## 8. Sonuç

Faz 1, aynı temel dersi iki farklı biçimde öğretti: **bir sınıfın verisi
diğerinden daha dar/temiz bir süreçten geliyorsa, model gerçek sinyali
değil o farkı öğrenir.** Bu ilke hem sentetik veri hem farklı kaynaklı
gerçek veri senaryosunda doğrulandı.
