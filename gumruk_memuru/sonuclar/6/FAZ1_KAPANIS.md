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

**Revizyon 5 (30 Ekim 2026, kullanıcı kararı, denetimin sonuçlarından önce):** ölçüt 12 ve İş 7
(Çiftleme denetimi) eklendi. Neden: İş 2(b) ön kaydı hazırlanırken EMBER2024 ham JSONL'lerinde her
kaydın İKİ KEZ bulunduğu görüldü (kopyalar yalnız capa alanlarında farklı; Win32/Win64 test 959.738
satır = 479.856 eşsiz dosya; ayrıntı `olcum/is2-uzman` dalı, `sonuclar/7/is2b_on_kayit.md`). Belgelerde
satır sayıları "dosya" diye yazılmış, Wilson aralıkları ve McNemar p'leri iki kat n ile hesaplanmış
olabilir. İş 7, İş 6'dan ÖNCE yapılır. Eğitim yenilenmez (kullanıcı kararı, şimdilik).

**Revizyon 6 (3 Kasım 2026, kullanıcı kararı, İş 2(c) sonucundan sonra, İş 3-6'dan önce):** İş 2(c)'ye karar
kuralı eklendi (ön kaydı `4c21a5b` ve `eea4c8d`, ölçümden önce) ve **İş 2 kararı yazıldı: uzman Faz 1 dışı, native
tek model.** ".NET'te eşik altı = BELİRSİZ" kalıcı kural oldu; yerel BELİRSİZ oranı ölçüldü (%61,58) ve buna göre
**iş sırası değişti: İş 4, İş 3'ün önüne alındı.** "Faz 1 sonrası açık sorular" bölümü eklendi. İş 5'e not
düşüldü. Ölçüt gevşetilmedi. İş 2'nin sonuç dosyaları `olcum/is2-uzman` dalında (`bb6d81d`, origin'de), main'de değil.

## Ön kayıt şablonu (İş 2'den itibaren her ön kayıt dört bölümü içerir)

1. **Soru ve sabitler:** ne ölçülüyor; veri, dönem, model, eşik; sonuçtan sonra değişmeyecek her şey.
2. **Ölçüm ve kontroller:** her kontrolün geçme koşulu (geçit dahil), hesaplama yolu, güven aralığı.
3. **Yorum / karar kuralı:** hangi sonuç hangi cümleyi yazdırır.
4. **Hüküm verilmeyen durumlar:** hangi koşulda hüküm YAZILMAZ (ör. geçit tutmadı, hücre n < 30,
   karşılaştırılan modellerin test yanlış alarmı eşit sağlanamadı, ölçüm çözünürlüğü hedefi
   ayırt edemiyor, veri alanı bulunamadı); bu durumda sonuç tablosunda "hüküm yok" ve nedeni yazılır,
   aralık örtüşmesi "eşit" diye okunmaz.

## Kapanış ölçütleri

Faz 1, aşağıdaki on iki ölçütün (12. ölçüt Revizyon 5) HEPSİ origin/main'de ve canlı sitede sağlandığında kapanır.

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
   bağlanıp bağlanmayacağı kararı ve gerekçesi yazılı. (Revizyon 6: karar İş 2'de yazılı; ölçüt için `sonuclar/7/`
   de main'e girmeli, henüz girmedi.)
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
12. **Dosya sayıları eşsiz dosya sayısıdır (Revizyon 5):** belgelerde ve yayında (site, README TR/EN,
    CLAUDE.md, notlar) "dosya" diye yazılan her sayı eşsiz dosya (sha256) sayısıdır; satır sayısı
    yazılıyorsa "satır" diye etiketlidir (ör. "479.856 eşsiz dosya (959.738 satır)"). EMBER2024
    üzerindeki Wilson aralıkları ve McNemar p'leri eşsiz dosyalarla yeniden hesaplanmış; hükmü
    değişen her sonuç ayrıca listelenmiş ve belgelerde düzeltilmiş.

## Kapsam dışı (Faz 1 kapanışını bekletmez)

- LightGBM ayarı (ayarlı LightGBM deneyi; ön kayıtlı, ayrı).
- .NET özellik mühendisliği (dnfile düzeyi: metod / P/Invoke sayısı, IL boyutu, yönetilen kaynaklar).
- ELF (Linux ikili dosyaları) ve diğer dosya türleri.
- eBPF ile sistem çağrısı izleme (Faz 2).
- Donanımsal izolasyon, NPU / TEE (Faz 3).
- Ayrıca: is_dotnet + .NET katmanlı dengeleme deneyi (gerekçe `on_kayit_uzman_native.md`).
- Uzman modelleri (M2, M2d) `tahmin_et.py`'ye bağlamak (Revizyon 6, İş 2 kararı).

## Kalıcı kural: .NET'te eşik altı skor "temiz" değildir, BELİRSİZ'dir (Revizyon 6)

Faz 1 kapanışından sonra da geçerlidir. `tahmin_et.py` ve `toplu_tahmin.py` bir .NET dosyasına eşik altı skorda asla
"temiz" demez (`tahmin_et.karar`, testli; ölçüt 3). Gerekçe: native, 2(c)'de eşit yanlış alarmda Dot_Net_test
zararlılarının %60-89'unu kaçırıyor. Kural yalnız yeni bir ön kayıtlı ölçüm ve kullanıcı kararıyla değişir; imza, hash
ya da skor bölgesi bu kuralı kendiliğinden gevşetmez.

**Bedeli (yerel küme, betimleyici, hüküm üretmez; `sonuclar/7/yerel_belirsiz.py`, `.log`).** Dondurulmuş 5.635 satır,
`tahmin_et.karar` ile, sha256 ve alarm sayıları `net_sonuc.md` C ile aynı:

| Grup | n | temiz | BELİRSİZ | ZARARLI | BELİRSİZ oranı (Wilson %95) |
|---|---|---|---|---|---|
| .NET EXE | 49 | 0 | 49 | 0 | %100,00 [92,73-100,00] |
| .NET DLL | 3.422 | 0 | 3.421 | 1 | %99,97 [99,83-99,99] |
| .NET dışı | 2.164 | 2.153 | 0 | 11 | %0 (kural gereği) |
| **Tüm yerel küme** | **5.635** | **2.153** | **3.470** | **12** | **%61,58 [60,30-62,84]** |

- Okuma: zararsız yerel .NET'te BELİRSİZ neredeyse her dosyayı kapsıyor; dolayısıyla burada **"BELİRSİZ" bilgi
  taşımıyor, "bu bir .NET dosyası" demeye yakın.** Bu kümede `toplu_tahmin.py`'nin çıkış kodu pratikte hep 2 ya da
  3 olur. Kural bilerek bu bedeli ödüyor (kaçan zararlıyı temiz saymamak için).
- Skor: BELİRSİZ dosyaların %85,82'si skor ≤ 0,2 (medyan 0,040). Bu bir "düşük skorlu .NET temizdir" önerisi DEĞİLDİR:
  zararlı .NET'in bu banttaki payı burada ölçülmedi (küme yalnız zararsız).
- Sınırlar: küme zararsız ve tek makineden; %61,58 bu makinenin klasör karışımına bağlı (.NET payı %61,6; ~%61'i
  Microsoft klasörlerinde, iki üretici ~%35), başka makineye genellenmez. Küme eskiyor, yeniden taranmadı.
  Wilson aralığı kümeliliği yok sayar, iyimserdir.

## Faz 1 sonrası açık sorular (Faz 1 kapanışını bekletmez; her biri ayrı ön kayıt ister)

1. **A ile Dot_Net .NET popülasyonlarını ayıran özellik nedir?** 2(c)'de AUC iki kümede ters yönde. Hipotez (ÖLÇÜLMEDİ):
   her model kendi eğitim popülasyonunda kazanıyor. Bilinen tek fark Karma_Mod payı (A %17,3, Dot_Net_train %0,13); ama
   2(b)'de H %0,45 EXE farkının 203/204'ü saf .NET, yani bu tek başına açıklamıyor.
2. **Büyük bir zararsız .NET EXE kümesi.** A'da 101, yerelde 49 zararsız .NET EXE var. Bu olmadan EXE'de eşit yanlış
   alarmda M2d - native sorusu cevaplanamaz (2(c)'de sınanamadı) ve uzman kararı EXE için yeniden açılamaz.
3. **Eşsiz verilerle yeniden eğitim.** EMBER2024'te her kayıt iki kez var; son modelin 483.224 satırlık örneği 402.129
   eşsiz dosya (zararlı DLL hücresinde 120.806 satır = 60.403 dosya; İş 7, commit'lenmemiş ölçüm). Etkisi ölçülmedi.

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
  **Revizyon 6: (c) artık karar kuralı taşıyor** (kullanıcı talimatı, ölçümden önce; `sonuclar/7/is2c_on_kayit.md`):
  eşit yanlış alarm her modelde aynı kümede ROC'tan kurulur (aralık örtüşmesi kullanılmaz), eşsiz dosya, eşlenik bootstrap;
  uzman ancak Dot_Net_test VE A'da, aralık sıfırı dışlayacak şekilde native'den iyiyse bağlanmaya ADAY olur; n·H < 5
  hücrede hüküm yok; aile sonuçları betimleyici; hüküm çıkmazsa varsayılan karar geçerli.
  **DURUM: ÖLÇÜMLER BİTTİ, KARAR YAZILI (3 Kasım 2026; dal `olcum/is2-uzman`, `bb6d81d`, main'de değil).**
  (a) yerel .NET DLL'de hedefin altında, EXE'de hüküm yok; (b) `is2b_sonuc.md`; (c) `is2c_sonuc.md`.
  **KARAR: önceden yazılmış varsayılan. Uzman Faz 1 dışı, native tek model.** Gerekçe:
  - Dot_Net_test'te M2d belirgin önde: eşit yanlış alarmda dört hücrede de daha az kaçırıyor (fark −34 ile −75 puan).
  - A'da hüküm yok / sınanamadı: EXE'de iki H ve DLL %0,45 asgari örnek altında; DLL %1,05'te fark gösterilemedi
    (+9,65 [−63,03, +22,02]). Aday olma koşulu sağlanmadı.
  - AUC kümeler arasında ters yönde (Dot_Net_test M2d lehine: EXE 0,9769 / 0,9024, DLL 0,9919 / 0,8378; A native
    lehine: EXE 0,9063 / 0,9635, DLL 0,9455 / 0,9799).
  - Hipotez (ÖLÇÜLMEDİ): her model kendi eğitim popülasyonunda kazanıyor. Açık soru 1.
  Bu karar "native daha iyi" hükmü değildir; .NET zayıf nokta olarak kalır ve kalıcı kural geçerlidir.
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
  **Öncelik (Revizyon 6): İş 4, İş 3'ün ÖNÜNE alındı.** Güncel sıra: İş 7 → İş 4 → İş 3 → İş 5 → İş 6. Neden: kalıcı kural
  yerel kümenin %61,58'ini BELİRSİZ yapıyor (.NET'in %99,97'si) ve native eşikleri bu grubu ayıramıyor; ayırabilecek planlı
  tek iş bu. İş 3'ün üç bölgesi de bu sonucu bilerek kurulmalı. Sonuç olumsuz da çıkabilir: imza bilgisinin BELİRSİZ yükünü
  azaltacağı VARSAYILMAZ.
  Ön kaydın içermesi ZORUNLU (Revizyon 2):
  - EMBER2024 kayıtlarında sertifika / imza dizininin GERÇEK alan adı veriden bulunur: İSİMLE, indeksle
    değil (Kural 5); yerel pefile tarafındaki karşılığı (ad) ve iki tarafın aynı ölçüldüğü örnekle
    gösterilir (Kural 1).
  - İmza bloğunun VARLIĞI zararlı / zararsız oranları olarak ölçülür (EXE / DLL ayrı, eğitim ve test
    haftaları, Wilson).
  - Bu "geçerli imza" diye YORUMLANMAZ (varlık ≠ doğrulanmış imza; sertifika zinciri ve iptal
    kontrolü yok) ve bu pakette modele ÖZELLİK olarak KATILMAZ.
  - (Revizyon 6) İmza varlığı oranları .NET için AYRICA verilir (EXE / DLL, zararlı / zararsız, A ve Dot_Net): yük
    (zararsız .NET'te ne kadar var) ve risk (zararlı .NET'te ne kadar var) aynı tabloda. Yerel küme yeniden TARANMAZ;
    yerel ölçüm gerekiyorsa yeni ön kayıtla, eskiyen dosyaların sayısı yazılarak yapılır.
  - (Revizyon 6) Kalıcı kuralı çiğnemez: imza varlığı bir .NET dosyasını kendiliğinden "temiz" yapamaz. Kuralı
    değiştiren bir öneri ayrı ön kayıtlı ölçüm ve kullanıcı kararı ister.
- **İş 5 - Denetçi ayırma.** Python referansı + C sürümü, ortak sınır tablosu, rastgele girdi
  eşitliği, derleyici bayrakları. BİTTİ: ölçüt 11'in her maddesi GEÇTİ.
  **Not (Revizyon 6, yapılacak):** `tahmin_et.py:141` ".NET uzman modeli ... henuz tahmin_et'e baglanmadi" mesajı İş 2
  kararıyla yanıltıcı oldu ("henüz" bağlanacağını ima ediyor). Şimdi DEĞİŞTİRİLMEDİ; İş 5'te ele alınır. Çıktıya bağlı
  testleri de birlikte kontrol et.
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
- **İş 7 - Çiftleme denetimi (Revizyon 5; İş 6'dan ÖNCE).** Ön kayıt önce (dört bölümlü şablon),
  sonra ölçüm. Eğitim YENİLENMEZ; hiçbir şey main'e alınmaz, site gönderilmez.
  (a) Yayındaki ve belgelerdeki tüm "dosya" sayılarının envanteri (site TR/EN, README TR/EN,
  CLAUDE.md, notlar): her biri satır mı eşsiz dosya mı; düzeltme TASLAĞI (yayınlanmaz, kullanıcı
  onaylar). (b) 3/, 5/, 6/ sonuçları eşsiz dosyalarla yeniden: nokta tahminleri aynı kalmalı
  (fark varsa nedeni), Wilson aralıkları ve McNemar p'leri yeniden; hükmü değişen her şey ayrıca
  listelenir. (c) Son modelin eğitim örneğindeki eşsiz dosya sayısı; eğitim / doğrulama / test
  örtüşmesi; doğrulama örtüşmesi varsa yanlış alarm kaymasına etkisi AYRI ölçüm olarak (hipotez:
  kayma kısmen bundan). BİTTİ: (a)(b)(c) ön kaydıyla, sonuç tablosu ve düzeltme taslağı yazılı;
  kullanıcı taslağı onaylayana kadar yayın değişmez. → ölçüt 12.
