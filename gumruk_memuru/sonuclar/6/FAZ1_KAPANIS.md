# Faz 1 kapanışı (native model) - ölçütler, kapsam, iş paketleri

Bu dosya iş paketlerinin sonuçlarından ÖNCE yazıldı ve commit'lendi (26 Ekim 2026). Ölçütler
sonradan gevşetilmez; değişiklik gerekirse ayrı commit'le, gerekçesiyle ve kullanıcı onayıyla yapılır.
Her iş paketi: ön kayıt commit'i → iş → sonuç commit'i (geçti / kaldı tablosu) → DUR (kullanıcı onayı).
Hiçbir paket kendi başına main'e almaz; main'e alma ve site yayını yalnız İş 1 ve İş 6'da, onayla.

**Revizyon 1 (26 Ekim 2026, kullanıcı kararı, iş paketlerinin sonuçlarından önce):** ölçüt 3'e
toplu aracın çıkış kodu eklendi; ölçüt 7-11 eklendi; iş paketleri 1-6 olarak yeniden sıralandı
(ilk sürüm `1881249`: 1-5). Kapsam dışı listesi değişmedi. İş 0 ilk sürümle yapıldı (14/14).

**Revizyon 2 (26 Ekim 2026, kullanıcı kararı, İş 3-5'in sonuçlarından önce):** ön kayıt şablonu
dört maddeye çıktı ("hüküm verilmeyen durumlar"); İş 3, 4, 5 ön kayıtlarının içermesi ZORUNLU
maddeler eklendi (aşağıda). Ölçütler ve iş sırası değişmedi.

**Revizyon 3 (26 Ekim 2026, kullanıcı kararı, İş 5'in sonuçlarından önce):** İş 5'e yukarı
yuvarlama, fail-closed gerekçesi ve ondalık / tam sayı yolu karar farkının sayısı ve yönü ölçütü.
İş 1'de her main birleştirmesinden sonra main bu dala birleştirilir (rebase yok).

**Revizyon 4 (26 Ekim 2026, kullanıcı kararı, düzeltmenin sonuçlarından önce):** ölçüt 1'e "üç ardışık
koşuda tam geçer (+ dosya kilidi regresyon testi) ve her test tek başına da geçer" eklendi. Neden:
bağımsız doğrulayıcı `test_olasi_zararli_cikis_kodu`'nu Windows dosya kilidiyle düşürdü; test tek
başına koşulunca belirlenimci olarak düşüyor, paket içinde önceki testlerin tetiklediği çöp toplama
kilidi gizliyordu.

## Ön kayıt şablonu (İş 2'den itibaren her ön kayıt dört bölümü içerir)

1. **Soru ve sabitler:** ne ölçülüyor; veri, dönem, model, eşik; sonuçtan sonra değişmeyecek her şey.
2. **Ölçüm ve kontroller:** her kontrolün geçme koşulu (geçit dahil), hesaplama yolu, güven aralığı.
3. **Yorum / karar kuralı:** hangi sonuç hangi cümleyi yazdırır.
4. **Hüküm verilmeyen durumlar:** hangi koşulda hüküm YAZILMAZ (ör. geçit tutmadı, hücre n < 30,
   karşılaştırılan modellerin test yanlış alarmı eşit sağlanamadı, ölçüm çözünürlüğü hedefi
   ayırt edemiyor, veri alanı bulunamadı); bu durumda sonuç tablosunda "hüküm yok" ve nedeni yazılır,
   aralık örtüşmesi "eşit" diye okunmaz.

## Kapanış ölçütleri

Faz 1, aşağıdaki on bir ölçütün HEPSİ origin/main'de ve canlı sitede sağlandığında kapanır.

1. **Yeniden üretilebilirlik:** origin/main boş klasöre temiz klonlanır, yeni venv `requirements.txt`
   (+ dev) ile kurulur: test paketinin tamamı geçer (gcc ile, atlanan yok); Faz 1 yeniden üretimi
   %90.1 ve 197/5700; `tahmin_et.py` modelsiz anlaşılır hata, doğru hash'le çalışır, bir baytı
   değişmiş modeli reddeder; uçtan uca 20/20 (86/86). Test paketi ÜÇ ARDIŞIK koşuda tam geçer
   (111/111 + dosya kilidi regresyon testi; Revizyon 4) ve her test TEK BAŞINA da geçer (paket
   içindeki sıra ya da çöp toplama zamanlaması bir hatayı gizlemesin).
2. **Raporlanan sayılar = ölçülen sayılar:** README'deki native model sayıları ölçüm dosyalarıyla
   (`model_native_meta.json`, `sonuclar/5/`, `sonuclar/6/`) aynı; zamansal bölme, doğrulamadan
   seçilen eşik, %50 zararlı uyarısı, DLL yanlış alarmının hedefi aşması, yerel setin eskimesi ve
   .NET karışımı yazılı. Sitedeki her rakam README'de var (betik), TR = EN.
3. **.NET güvenli davranış:** `tahmin_et.py` .NET dosyasına eşik altında asla "zararsız" demez
   (BELİRSİZ); çıkış kodları 0 temiz / 1 hata / 2 BELİRSİZ / 3 ZARARLI / 4 OLASI ZARARLI, testli;
   toplu kullanımda BELİRSİZ hata sayılmaz, ayrı sayılır. Toplu aracın çıkış kodunu EN KÖTÜ sonuç
   belirler (ZARARLI 3 > OLASI ZARARLI 4 > BELİRSİZ 2 > hata 1 > temiz 0); "PE değil" kodu
   yükseltmez; yol yok / okunamıyor 1; hiç PE bulunmadıysa uyarı ve 1 (fail-closed). 0 yalnız
   "her şey temiz" demektir.
4. **.NET ölçümleri kayıtlı:** native modelin .NET ölçümü (`sonuclar/5/`) ve uzman (M2, M2d) vs
   native eşit yanlış alarm karşılaştırması (`sonuclar/6/`) ön kayıtlarıyla main'de; uzman modelin
   bağlanıp bağlanmayacağı kararı ve gerekçesi yazılı.
5. **Yayın tutarlı:** canlı site commit'le bayt bayt aynı; tarihli notlar silinmeden "Güncelleme"
   satırıyla düzeltilmiş; paylaşım kartları güncel etiketli.
6. **Açık işler açıkça devredildi:** kapsam dışı listesi ve Faz 2'ye devredilenler (Linux'ta eşik
   sınır testi, UBSan, CI) README / CLAUDE.md'de; GELISIM_SURECI.md'de Faz 1 kapanış bölümü; main
   üzerinde `faz1-kapanis` etiketi.
7. **Eşik kalibrasyonu:** eşikler her tür için doğrulama diliminden, hedefe MARJLA seçilmiş; test bir
   kez ölçülmüş; yanlış alarm kayması (doğrulama → test, ör. uzman ölçümünde altı hücrenin beşinde
   test YA hedefin üstünde) ölçülmüş ve ele alınış yöntemi sonuçtan önce yazılmış.
8. **Gerçekçi zararlı oranı:** π = %1 ve %0,1 için "alarmların ne kadarı gerçek" (kesinlik / PPV)
   test sonuçlarından (tür başına yakalama ve yanlış alarm oranı) hesaplanmış, aralıklarıyla
   README'de.
9. **Üç bölgeli karar:** temiz / belirsiz / zararlı; bölge sınırları doğrulamadan, test bir kez;
   `tahmin_et.py` ve `toplu_tahmin.py` aynı kuralı kullanır; .NET kuralı (eşik altı asla temiz değil)
   korunur.
10. **İmza / hash filtresi:** ölçülebilirliği araştırılmış (ne ölçülebilir, hangi veriyle, eğitim ve
    yerel tarafta aynı ölçüm mümkün mü - Kural 1) ve karar (uygula / uygulama) gerekçesiyle yazılı.
11. **Denetçi modülü ayrı:** yalnız karar + aralık doğrulaması + hash kontrolü; model ve ayrıştırıcı
    YOK. Python referansı ve C sürümü aynı sınır tablosundan geçer; rastgele girdilerle ikisi aynı
    sonucu verir; C sürümü `-Wall -Wextra -Wconversion -Wsign-conversion -Werror` ile temiz derlenir.

## Kapsam dışı (Faz 1 kapanışını bekletmez)

- LightGBM ayarı (ayarlı LightGBM deneyi; ön kayıtlı, ayrı).
- .NET özellik mühendisliği (dnfile düzeyi: metod / P/Invoke sayısı, IL boyutu, yönetilen kaynaklar).
- ELF (Linux ikili dosyaları) ve diğer dosya türleri.
- eBPF ile sistem çağrısı izleme (Faz 2).
- Donanımsal izolasyon, NPU / TEE (Faz 3).
- Ayrıca: is_dotnet + .NET katmanlı dengeleme deneyi (gerekçe `on_kayit_uzman_native.md`).

## İş paketleri ve "bitti" ölçütleri

- **İş 0 - Bekleyenleri paketle (yerel, gönderim yok).** Site commit'leri (yerel yanlış alarm
  cümlesi dahil), `ozellik/net-belirsiz` (çıkış kodu tablosu, toplu kullanımda BELİRSİZ sayacı),
  etiket düzeltmeleri. BİTTİ: ön kaydındaki her kontrol GEÇTİ (`is0_on_kayit.md`).
- **İş 1 - Main'e alım (kullanıcı onayıyla).** Dallar origin'e gönderilir (force yok, PR yok);
  sonra `belge/yerel-karisim`, `ozellik/net-belirsiz`, `olcum/uzman-native` sırayla `--no-ff`; her
  birleştirmeden ÖNCE kısa diff özeti ve onay, SONRA test paketi + 20/20. Site (4 commit) yalnız
  `belge/yerel-karisim` main'deyken ve kullanıcı "gönder" derse; sonra canlı sayfalar önbelleksiz
  çekilip rakamlar README ile betikle karşılaştırılır. BİTTİ: origin/main üç dalı içerir, her
  adımda testler geçti. → ölçüt 2, 3, 4 (kısmen), 5 (site gönderildiyse).
- **İş 2 - .NET uzman kararı + ek ölçümler.** Ön kayıt önce: (a) M2d'nin yerel 3.471 meşru .NET
  dosyasında yanlış alarmı, (b) M2d'nin Win32/Win64 test haftalarındaki .NET alt kümesinde (A
  kümesi) performansı, (c) tam eşit yanlış alarmda ROC tabanlı M2d-native karşılaştırması (EXE / DLL
  ayrı, tanı amaçlı). Uzman BAĞLANMAZ; karar kullanıcının. BİTTİ: ölçümler ön kayıtlarıyla ve
  kullanıcının kararı yazılı. → ölçüt 4.
- **İş 3 - Gerçekçi oran + eşik kalibrasyonu + üç bölge.** Ön kayıt, yanlış alarm kaymasını açıkça
  konu eder ve ele alış yöntemlerini (doğrulama dilimini teste yakınlaştırma, hedefi marjla seçme
  vb.) sonuçtan ÖNCE yazar. BİTTİ: ölçüt 7, 8, 9'un her maddesi GEÇTİ; README'de π tablosu.
  Ön kaydın içermesi ZORUNLU (Revizyon 2):
  - PPV ("alarmların ne kadarı gerçek") tablosu README ve fizibilite metni için: ÖLÇÜLMÜŞ tür başına
    yakalama oranı (TPR = 1 − kaçan) ve yanlış alarm oranıyla, EXE ve DLL ayrı; zararlı oranı
    π = %50 / %1 / %0,1, her satır "senaryo varsayımı" diye etiketli (π ölçülmedi). Sınırlılık
    yazılı: π değişince TPR ve yanlış alarm oranının sabit kaldığı varsayılıyor (gerçekte zararlı ve
    zararsız dağılımı da değişir).
  - "Zararlı" bölgesi için çok düşük yanlış alarm hedefinin ÇÖZÜNÜRLÜĞÜ: doğrulama dilimindeki tür
    başına zararsız dosya sayısı n ile ölçülebilen en küçük adım (1/n) ve hedefte beklenen alarm
    sayısı hesaplanır; hedef birkaç alarmdan azına düşüyorsa eşik o hedefe göre seçilmez, hüküm yok
    (şablon madde 4). Eşik marjla seçilir (marj kuralı ön kayıtta sayıyla).
- **İş 4 - İmza / hash filtresi.** Ön kayıtlı araştırma: ölçülebilirlik ve Kural 1 (iki tarafta aynı
  ölçüm). BİTTİ: karar ve gerekçesi yazılı. → ölçüt 10.
  Ön kaydın içermesi ZORUNLU (Revizyon 2):
  - EMBER2024 kayıtlarında sertifika / imza dizininin GERÇEK alan adı veriden bulunur: İSİMLE, indeksle
    değil (Kural 5); yerel pefile tarafındaki karşılığı (ad) ve iki tarafın aynı ölçüldüğü örnekle
    gösterilir (Kural 1).
  - İmza bloğunun VARLIĞI zararlı / zararsız oranları olarak ölçülür (EXE / DLL ayrı, eğitim ve test
    haftaları, Wilson).
  - Bu "geçerli imza" diye YORUMLANMAZ (varlık ≠ doğrulanmış imza; sertifika zinciri ve iptal
    kontrolü yok) ve bu pakette modele ÖZELLİK olarak KATILMAZ.
- **İş 5 - Denetçi ayırma.** Python referansı + C sürümü, ortak sınır tablosu, rastgele girdi
  eşitliği, derleyici bayrakları. BİTTİ: ölçüt 11'in her maddesi GEÇTİ.
  Ön kaydın içermesi ZORUNLU (Revizyon 2):
  - Denetçi YALNIZ tam sayı skor alır (sabit nokta); ölçek ve yuvarlama kuralı (yön dahil) yazılı.
    Dönüşüm modelin Python tarafında yapılır; NaN / ±sonsuz dönüşümden ÖNCE BELİRSİZ olur (tam sayıya
    hiç çevrilmez).
  - YUVARLAMA YUKARI (Revizyon 3): tam sayı skor = ⌈p × ölçek⌉; skor hiçbir zaman düşürülmez.
    Fail-closed gerekçesi: yuvarlama bir dosyayı eşiğin altına (daha "temiz" tarafa) itebilseydi,
    eşiğin hemen üstündeki zararlı bir skor tam sayı yolunda kaçabilirdi; yukarı yuvarlama hatayı
    yalnız daha sıkı tarafa (BELİRSİZ / ZARARLI) bırakır - Kritik Kural 7'deki "aralık dışı = şüpheli"
    ilkesinin aynısı.
  - ÖLÇÜT (Revizyon 3): ondalık yol ile tam sayı yolu arasındaki karar farklarının SAYISI ve YÖNÜ
    raporlanır (test kümesi skorları + rastgele skorlar). GEÇME: tam sayı yolunun DAHA GEVŞEK
    (ondalık yoldan daha temiz) karar verdiği fark sayısı **0**; daha sıkı yöndeki farklar sayılır ve
    yazılır (hangi skor aralığında oldukları dahil), sıfır olmak zorunda değil.
  - Eşikler meta veride tam sayı olarak da bulunur (ondalık eşikle birlikte, tutarlılığı testli).
  - Sınır değer testleri: 0.7, nextafter(0.7, 0) ve nextafter(0.7, 1), 1.0, -0.0, NaN, ±inf
    (ve DLL eşiği için aynıları).
  - Ondalık (float) yol ile tam sayı yolundan AYNI karar sayıları çıktığı gösterilir (test kümesi
    skorları ve rastgele skorlar; fark varsa sayısı ve yeri).
  - Çıkış kodları TEK tablodan: ya hem `.py` hem `.h` o tablodan üretilir ya da test ikisinin eşit
    olduğunu doğrular.
- **İş 6 - Temiz klon doğrulaması + belgeler + site + etiket.** Ölçüt 1'in tüm maddeleri (son main
  üzerinde) + `git ls-files`'ta model / Parquet / dz80 / yerel set yok; GELISIM_SURECI.md Faz 1
  kapanış bölümü, CLAUDE.md / README durum satırları, kapsam dışı + Faz 2 devir listesi,
  "DOĞRULANMADI" kalan her yer ölçülmüş ya da devredilmiş; site (onayla), canlı = commit (bayt),
  canlı rakamlar = README (betik); main üzerinde `faz1-kapanis` etiketi (onayla). BİTTİ: tüm
  satırlar GEÇTİ ve kullanıcı belgelerin son halini onayladı. → ölçüt 1, 2, 5, 6.
