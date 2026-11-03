# İş 2(c) ön kaydı - Eşit yanlış alarmda M2d ile native (ROC, eşlenik bootstrap)

`FAZ1_KAPANIS.md` (dal `faz1/kapanis`) İş 2 (c) ve kullanıcı talimatı (3 Kasım 2026). Bu dosya ölçümden
ÖNCE yazıldı ve commit'lendi. Ölçüm bir kez yapılır; model, veri, tekilleştirme, tohum ve kurallar
sonuçtan sonra DEĞİŞMEZ. Uzman model `tahmin_et.py`'ye BAĞLANMAZ.

**Kapsam notu:** `FAZ1_KAPANIS.md` bu ölçümü "tanı amaçlı" diye tanımlıyor. Bölüm 3'teki karar kuralı ve
varsayılan karar, kullanıcının 3 Kasım talimatıyla eklendi.

**Ön kayıttan önce bilinenler (bu ölçüm körlemesine DEĞİL):** İş 2(b) sonucu aynı iki küme ve aynı iki
modelle görüldü (`is2b_sonuc.md`, `50f2ade`): Dot_Net_test'te sabit eşiklerde M2d çok daha az kaçırıyor; A
kümesinde H %0,45 EXE'de M2d daha çok kaçırıyor, H %1,05 EXE'de fark gösterilemedi; DLL'de E1 tutmadığı
için hüküm yok, ama nokta tahminleri native lehine (H %1,05: 29,22'ye karşı 22,73). Asgari örnek eşiği
(bölüm 3.1) bu bilgiyle yazıldı. Hücre sayıları skordan bağımsız olarak önceden biliniyordu; hangi hücrenin
hüküm alacağı aşağıda skorsuz hesaplandı. Model ve küme yeni değil; yeni olan yalnız karşılaştırma yöntemi.

## 1. Soru ve sabitler

**Soru:** İki model tam aynı yanlış alarm oranında çalıştırıldığında, eşsiz dosyalarda, M2d native'den
daha az zararlı kaçırıyor mu; bu Dot_Net_test'te VE A kümesinde birlikte geçerli mi?

- **Kümeler (ikisi de `Dosya_Adi` ile tekil, ilk kopya tutulur; `is2b_a_kumesi.py` ile aynı yol):**
  - **Dot_Net_test:** 59.953 eşsiz dosya (zararsız EXE 3.713, DLL 26.240; zararlı EXE 27.370, DLL 2.630).
  - **A:** Win32_test + Win64_test, hafta 52-63, `NET_mi` = 1: 2.411 eşsiz dosya (zararsız EXE 101, DLL
    517; zararlı EXE 1.639, DLL 154).
- **M2d:** `sonuclar/6/uzman_native.py` tarifi aynen (2(a), 2(b) ile aynı): Dot_Net_train hafta 0-47, hücre
  başına 24.104, `random_state=42`, 87 özellik, çiftli havuz.
- **Native:** kayıtlı son model, `tahmin_et.model_yukle()` (SHA-256, Kural 10).
- **Tür:** EXE ve DLL AYRI (`DLL_mi`). Hüküm yalnız tür içinde; "hepsi" tür karışımını taşıdığı için
  (Kural 8) yalnız betimleyici AUC olarak yazılır.
- **Hedef YA (H):** %0,45 ve %1,05 (2(b) ile aynı).
- **Bootstrap:** eşsiz dosya düzeyinde, B = 10.000, tohum 42, yüzdelik %95 aralık (2,5 ve 97,5).
  Her küme × tür içinde zararsız ve zararlılar ayrı ayrı yerine koyarak çekilir (sınıf sayıları sabit).
  **Eşlenik:** her yeniden örneklemde iki model AYNI dosyalarla değerlendirilir. Eşik her yeniden örneklemde
  yeniden belirlenir, yani eşik seçiminin belirsizliği aralığa dahildir.

## 2. Ölçüm ve kontroller

Geçit tutmazsa ölçüm DURUR; log saklanır, sonuç tablosu yazılmaz.

| # | Kontrol | Geçme koşulu |
|---|---|---|
| K1-K5 | İş 2(b) geçitleri | `is2b_on_kayit.md`'deki koşullarla aynı (A sayıları ve kopyalar, M2d ve native eşikleri, Dot_Net_test 6'şar satır, çiftli A üretim eşiği, ortak sha 0, Dot_Net_test tekil 59.953) |
| K6 | 2(b) yeniden üretimi | tekil A ve tekil Dot_Net_test'te 2(b)'nin sabit eşikleriyle kaçan ve YA k/n ve AUC, `is2b_a_kumesi.csv` ile birebir |
| K7 | ROC kodu | nokta AUC, `roc_auc_score` ile 1e-12 içinde aynı; bir modelin kendisiyle eşlenik farkı her yeniden örneklemde tam 0; aynı tohumla bootstrap iki kez aynı |

Betik gerçek veriyle koşmadan önce yalnız sentetik veriyle denenebilir; denendiyse sonuçta yazılır.

**ROC ve eşit YA.** Skor seviyeleri büyükten küçüğe taranır; alarm = skor > t (2(b) ile aynı yön). RF
skorları kesikli olduğundan (100 ağaç) ROC bir merdivendir ve çoğu H'ye hiçbir eşik tam denk gelmez. Bu yüzden
FPR = H noktasındaki yakalama oranı, FPR'si H'den büyük olmayan SON köşe i ile sonraki j arasında DOĞRUSAL
İÇ DEĞERLEMEYLE bulunur (eşik i ile j arasındaki rastgele karara denk). Kaçan(H) = 1 − TPR(H).
Bu nokta **değerlendirme kümesinin kendisinden** seçilir: Kural 6 gereği bir ROC noktasıdır, üretim eşiği
ya da raporlanacak çalışma noktası DEĞİLDİR.

**Birincil ölçü:** Δkaçan(küme, tür, H) = Kaçan_M2d(H) − Kaçan_native(H), yüzde puan; nokta tahmini ve
eşlenik bootstrap %95 aralığı. Negatif = M2d daha az kaçırıyor.

**İkincil ölçüler (karar kuralına girmez):**
- ΔAUC, küme × tür (ve betimleyici "hepsi").
- Δ kısmi AUC, küme × tür × H: FPR ∈ [0, H] aralığında ROC altı alan / H (o aralıktaki ortalama TPR),
  yamuk kuralı, H'de aynı iç değerlemeyle kapatılır.
- Duyarlılık: iç değerleme olmadan, FPR'si H'yi aşmayan son köşede kaçan ve gerçek FPR'si, iki model için.
- Tablolanır: i ve j köşelerinin FPR'leri, beklenen alarm n·H.

**Betimleyici:** eşit YA'da aile bazında beklenen kaçan (iç değerleme ağırlığıyla), H %1,05, her iki küme,
zararlı n ≥ 30 aileler ve `agenttesla`; yalnız nokta tahmini, güven aralığı yazılmaz, karar kuralına girmez.

## 3. Yorum / karar kuralı

1. **A için asgari zararsız örnek:** bir küme × tür × H hücresi ancak beklenen alarm n·H ≥ 5 ise (n = o
   türün zararsız eşsiz dosya sayısı) hüküm alır. Gerekçe: daha azında FPR adımı (1/n) hedefin beşte birinden
   büyük olur ve H'deki değer birkaç dosyaya bağlı kalır. Önceden hesap (skorsuz):

   | Küme | Tür | n | n·H, %0,45 | n·H, %1,05 | Hüküm alır |
   |---|---|---|---|---|---|
   | A | EXE | 101 | 0,45 | 1,06 | **hiçbirinde** |
   | A | DLL | 517 | 2,33 | 5,43 | **yalnız %1,05** |
   | Dot_Net_test | EXE | 3.713 | 16,71 | 38,99 | ikisinde |
   | Dot_Net_test | DLL | 26.240 | 118,08 | 275,52 | ikisinde |

   **Sonuç, ölçümden önce:** "İki yerde de" koşulu yalnız **DLL, H %1,05** hücresinde sınanabilir. EXE için
   bu pakette aday olma yolu YOKTUR; bu bir bulgu değil, A'daki zararsız EXE sayısının sınırıdır.
2. **Hücre cümlesi** (hüküm alan hücrelerde): aralık üstü < 0 → "M2d eşit YA'da daha az kaçırıyor"; aralık
   altı > 0 → "native eşit YA'da daha az kaçırıyor"; aralık sıfırı içeriyorsa "fark gösterilemedi" ("eşit"
   DENMEZ). Sıfırı dışlama kesindir: sınırın tam 0 olması dışlamaz.
3. **Aday hücre:** aynı tür × H'de Dot_Net_test VE A hücrelerinin ikisi de hüküm alır ve ikisinin de aralık
   üstü < 0 ise.
4. **Bağlanmaya aday (tür düzeyinde):** bir tür için en az bir aday hücre var VE o türün hüküm alan hiçbir
   hücresinde (iki küme, iki H) "native daha az kaçırıyor" yok. Adaylık yalnız o tür içindir: DLL'de aday
   çıkması EXE için hiçbir şey söylemez. Aday olmak bağlanmak değildir; karar kullanıcınındır.
5. **Varsayılan karar (kullanıcı talimatı):** hiçbir tür aday olmazsa, geçit tutmazsa ya da hüküm çıkmazsa
   uzman **Faz 1 kapsamı dışında kalır, native tek model olur**; `tahmin_et.py` .NET kuralı (eşik altı
   BELİRSİZ) değişmez. Yalnız DLL aday olursa EXE tarafı bu varsayılanda kalır.
6. AUC, kısmi AUC, duyarlılık satırları ve aileler betimleyicidir; hüküm üretmez, kural 2-5'i değiştirmez.
   Birden çok karşılaştırma düzeltmesi yapılmaz: kural 1'in sonucu olarak aday kararı tek hücreye dayanır;
   Dot_Net_test'in öteki hücreleri yalnız kural 4'ün engel koşulu için okunur.
7. Sonuç ne olursa olsun bu pakette uzman bağlanmaz.

## 4. Hüküm verilmeyen durumlar

- K1-K7'den biri tutmadı → "hüküm yok: geçit"; hiçbir sayı sonuç olarak raporlanmaz; neden aranır ve
  kullanıcıya bildirilir. Yeniden ölçüm ayrı ön kayıt ister; o zamana dek kural 5 geçerlidir.
- n·H < 5 → "hüküm yok: asgari örnek altında". Hesaplanan sayı `.csv`'de ve betimleyici tabloda işaretli
  kalır, hükme ve aday kararına girmez.
- Zararlı n < 30 (küme × tür ya da aile) → oran yorumlanmaz, yalnız k/n.
- Nokta tahmininde H'yi çevreleyen köşeler arasındaki FPR boşluğu H'den büyükse (j − i > H, iki modelden
  herhangi birinde) → "hüküm yok: ROC çözünürlüğü yetersiz".
- Aralığın sıfırı içermesi "eşit" diye okunmaz.

## Sınırlar (sonuçtan önce yazıldı)

- **Tek hücre:** bağlanma adaylığı fiilen DLL, H %1,05'e (A'da 517 zararsız, 154 zararlı, beklenen 5,43 alarm)
  dayanır. Bu güçlü bir kanıt tabanı değildir; aralığın geniş çıkması beklenir.
- **EXE sınanamıyor:** A'daki EXE zararsız sayısı (101) iki hedefte de yetersiz. Eğitim haftalarından ek
  örnek alınamaz (native o dosyaları gördü). 2(b)'nin EXE hükümleri olduğu gibi kalır.
- **Çalışma noktası değil:** eşit YA, tanı için kümenin içinden kurulur. Gerçek kullanımda eşik doğrulamadan
  seçilir ve kayar; 2(b) bu kaymayı gösterdi.
- **Bootstrap yalnız örnekleme belirsizliğini ölçer:** dosyalar bağımsız varsayılır. Aile ve hafta kümeliliği
  aralığı olduğundan dar gösterebilir; yüzdelik aralık uç oranlarda yaklaşıktır.
- **Yapısal asimetri ve çiftli eğitim:** 2(b) ön kaydındaki gibi. Native A popülasyonunu eğitimde gördü, M2d
  görmedi; M2d tarifi çiftli havuzla tanımlı.
- **İç değerleme:** kesikli skorda FPR = H'deki değer, iki köşe arasındaki doğruya bağlıdır ve tek bir
  deterministik eşikle elde edilemez; duyarlılık satırları bu yüzden yazılır.
