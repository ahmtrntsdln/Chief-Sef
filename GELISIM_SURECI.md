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

Zararsız veri, kendi bilgisayarımdan (System32, Program
Files) tarandı. Yeni model %97 başarı verdi, ancak özellik önem
analizinde entropi ve sıfır-oranı özelliklerinin payı %70'e ulaştı.
Neden araştırıldığında: zararsız veri tek, homojen bir kaynaktan
(Microsoft'un imzaladığı sistem dosyaları) geliyordu, zararlı veri ise
EMBER'in çok çeşitli kaynaklarından. Model kısmen "zararlı mı" değil
"Microsoft'un kalıbına mı uyuyor" sorusunu öğreniyordu.

## 7. Çözüm: Simetrik Veri Kaynağı

Bu yanlılığı gidermek için zararsız veri de EMBER'den (`label==0`)
çekildi (`ember_zararsiz_cikar.py`) — artık iki sınıf da aynı kaynaktan,
aynı çeşitlilikte. Bilgisayar taramam çöpe atılmadı;
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

## 10. 2018 Modeli 2024'te: Çöküş, Kestirme ve Yeni Model

Faz 1'in modeli EMBER 2018 ile eğitilmişti. Aynı modeli EMBER2024'ün
Win32/Win64 test kümesinde (son 12 hafta, 959.738 dosya) ölçtüğümüzde AUC
**0,663**'e düştü; import'suz zararlıların neredeyse tamamı kaçıyordu. Altı
yıllık zaman farkı, Kural 6'nın (zaman ekseni) en sert örneği oldu: "geçmişte
iyi" bir model bugünün dosyalarında yazı-turaya yaklaşabiliyor.

Yeni veriyle eğitince ikinci tanıdık sorun çıktı: **dosya tipi kestirmesi.**
EMBER2024'te zararsızların ~%65-73'ü DLL, zararlıların yalnızca ~%6'sı. Model
"DLL ise zararsız" demeyi öğrenebiliyordu; genel doğruluk bunu ödüllendiriyor,
zararlı DLL'ler gözden kaçıyordu. Bu, projede beşinci kez karşılaşılan aynı
dersti. Çözüm .NET modelinde ve 2018 denemesinde olduğu gibi: eğitim
örneklemini her dosya tipinin İÇİNDE 50/50 dengelemek (E3). Genel doğruluk
biraz düşüyor, ama bu gerçekçi olmanın bedeli.

Karar sırası bilinçli kuruldu. Ölçütler (her türde %1 yanlış alarmda DLL'de
kaçan zararlı; yerel yanlış alarm McNemar'a göre kötüleşmemeli) sonuçlara
bakılmadan yazılıp commit'lendi. İlk karşılaştırmada eşik test kümesinden
seçilmişti; bu, iki modeli aynı noktada kıyaslamak için yeterli ama raporlanacak
bir sayı değil. Eşik sonra eğitim haftalarından ayrılan bir doğrulama
diliminden (hafta 48-51) seçildi ve test bu sabit eşikle bir kez ölçüldü.
Sonuç değişmedi: RF E3. Son boyut için de kural ölçümden önce yazıldı;
483.224 örnek, 300 binden 1,69 puan daha az zararlı DLL kaçırdı (tohum
oynaması 0,72) ve seçildi.

Son model testte bir kez ölçüldü: AUC 0,9865; kaçan zararlı EXE'de %17,7,
DLL'de %19,5; yanlış alarm EXE'de %0,83, DLL'de %1,43. DLL'deki yanlış alarm,
doğrulamada %1'e ayarlanan hedefi aştı: doğrulama haftalarından test
haftalarına geçerken zararsız DLL'lerin dağılımı kayıyor. Bu bir hata değil,
eşiğin zamanla eskidiğinin ölçümü.

**18/20 koşusu.** Tahmin aracının özellikleri ile doğrulama setindekilerin
aynı olduğunu 20 dosyada uçtan uca sınadık. İlk koşu 18/20 geçti: iki .NET
dosyasının değerleri tutmadı. Kod mu yanlıştı, dosya mı değişmişti? İki dosya
da ölçümden beş gün sonra, aynı boyutla güncellenmişti; eski kod yolu ve yeni
tek modül o dosyalarda da birebir aynı sayıyı veriyordu. Test "boyut aynıysa
dosya aynıdır" varsayımına dayanıyordu ve bu varsayım yanlıştı. Başarı
ölçütünü gevşetmek yerine aday seçimini düzelttik (son değişikliği ölçümden
önce olan dosyalar) ve testi yeniden koştuk: 20/20. İlk koşunun kaydı da
saklandı. Bu olay, yerel doğrulama setinin eskidiğini de gösterdi: 9 Ekim'den
bu yana 857 dosya silinmiş, yüzlercesi güncellenmişti. Ölçümlerin dayandığı
5.635 satır bu yüzden donduruldu.

## 11. Sonuç

Faz 1, aynı temel dersi iki farklı biçimde öğretti: **bir sınıfın verisi
diğerinden daha dar/temiz bir süreçten geliyorsa, model gerçek sinyali
değil o farkı öğrenir.** Bu ilke hem sentetik veri hem farklı kaynaklı
gerçek veri senaryosunda doğrulandı.
