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

## 5. Ölçüm Tutarlılığı: EMBER ile pefile Farkı

Zararlı veri EMBER'in hazır özelliklerinden, zararsız veri ise kendi
taramamızda `pefile` ile çıkarılıyordu. Aynı sütun adları aynı ölçümü
garanti etmiyor: EMBER, isimsiz (ordinal) import'ları `ordinal5` gibi
girdiler olarak listeliyordu (incelenen ilk 2000 kayıtta import
girdilerinin %14'ü), `pefile` tarafı ise bunları hiç saymıyordu. Ayrıca
EMBER boyutu 0 olan bölümleri 0 entropiyle ortalamaya katıyor, bizim
tarafımız bu bölümleri atlıyordu. Yani `Toplam_API` ve `Ortalama_Entropi`
iki sınıfta farklı yöntemle ölçülüyordu; bu da modelin gerçek bir sinyal
yerine ölçüm farkını öğrenmesine yol açabilirdi. `ember_zararli_cikar.py`
ordinal girdileri ve boş bölümleri atlayacak şekilde düzeltildi, zararlı
veri yeniden üretildi.

## 6. Kaynak Yanlılığı: İkinci Bir Sızıntı Türü

Zararsız veri, kendi bilgisayarımdan(System32, Program
Files) tarandı. Yeni model %97 başarı verdi, ancak özellik önem
analizinde entropi ve sıfır-oranı özelliklerinin payı %70'e ulaştı.
Neden araştırıldığında: zararsız veri tek, homojen bir kaynaktan
(Microsoft'un imzaladığı sistem dosyaları) geliyordu, zararlı veri ise
EMBER'in çok çeşitli kaynaklarından. Model kısmen "zararlı mı" değil
"Microsoft'un kalıbına mı uyuyor" sorusunu öğreniyordu.

## 7. Çözüm: Simetrik Veri Kaynağı

Bu yanlılığı gidermek için zararsız veri de EMBER'den (`label==0`)
çekildi (`ember_zararsiz_cikar.py`) — artık iki sınıf da aynı kaynaktan,
aynı çeşitlilikte. bilgisayar taramam çöpe atılmadı;
bağımsız bir gerçek dünya doğrulama seti olarak yeniden konumlandırıldı:
"EMBER ile eğitilen model, gerçek bir bilgisayardaki meşru dosyaları
yanlış pozitif işaretliyor mu?" sorusuna cevap veriyor.

## 8. Donanım Sınırları

Büyük klasörlerin taranması sırasında CPU sıcaklığı 97°C'ye çıktı;
neden, bazı dosyaların (multi-GB) tamamen belleğe okunup entropi
hesaplanmasıydı. 100 MB'lık bir dosya boyutu filtresi eklendi, sıcaklık
89-94°C bandında stabilize oldu. Ayrıca uzun süren işlemler için
ilerleme çubuğu, anlık çıktı ve ara kayıt (checkpoint) mekanizması
eklendi.

## 9. Nihai Sonuçlar

EMBER zararlı + EMBER zararsız ile eğitilen model, EMBER test setinde
**%90.1** doğruluk verdi (yanlış alarm %8.1, kaçan zararlı %11.7).
Eğitimde hiç görmediği, bu bilgisayardaki 5700 gerçek zararsız PE
dosyasında yanlış alarm oranı **%3.5** oldu. Önceki %97'lik sonuçtan
düşük olması bilinçli: o sonucun bir kısmı sınıf farkından değil kaynak
farkından geliyordu.

Kaynak yanlılığı varsayımı ölçümle sınandı. Ölçüm yöntemi sabit
tutularak zararsız veri sadece System32'den System32 + Program Files'a
genişletildiğinde, entropi ve sıfır-oranının toplam önem payı **%70.1'den
%50.5'e** düştü; ölçüm düzeltmesinin bu paya etkisi yalnızca ~3 puan.
Ancak çeşitlenmiş haliyle bile "EMBER mi, bu makine mi" ayrımı %96
doğrulukla yapılabiliyordu — bu yüzden eğitimde iki sınıfın da aynı
kaynaktan gelmesi şart.

Senaryo-dışı "sinsi" örnekler de açıklanabilir sonuç verdi. Düşük
sıfır-oranlı (%17), orta entropili (3.8) ve hiç şüpheli API'si olmayan
bir profil %68 olasılıkla zararlı bulundu. İlk bakışta hata gibi görünse
de EMBER'de bu profile benzeyen 22 gerçek dosyanın %64'ü zararlı:
model veriyi doğru yansıtıyor, "zararsız görünüyor" sezgisi yanlıştı.

## 10. Sonuç

Faz 1, aynı temel dersi iki farklı biçimde öğretti: **bir sınıfın verisi
diğerinden daha dar/temiz bir süreçten geliyorsa, model gerçek sinyali
değil o farkı öğrenir.** Bu ilke hem sentetik veri hem farklı kaynaklı
gerçek veri senaryosunda doğrulandı.
