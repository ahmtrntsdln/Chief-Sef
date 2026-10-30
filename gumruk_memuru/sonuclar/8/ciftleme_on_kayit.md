# İş 7 ön kaydı - Çiftleme denetimi

`FAZ1_KAPANIS.md` Revizyon 5 (commit `4638afd`, dal `faz1/kapanis`), İş 7 ve ölçüt 12. Bu dosya
ölçümden ÖNCE yazıldı ve commit'lendi (30 Ekim 2026, dal `denetim/ciftleme`, main `c303d8d`'den).
Eğitim YENİLENMEZ (çiftsiz yeniden eğitim yok); main'e alınmaz; site gönderilmez; düzeltmeler TASLAK.

**Arka plan (ön kayıttan önce bilinen, `olcum/is2-uzman` dalı `sonuclar/7/is2b_on_kayit.md`):**
EMBER2024 haftalık JSONL'lerinde her kayıt iki kez (ilk yarı / ikinci yarı, aynı sha256 sırası;
kopyalar yalnız capa alanlarında farklı). Satır → eşsiz: Win32/Win64 train 4.158.450 → 2.079.225,
test 959.738 → 479.856; Dot_Net_train 519.992 → 259.996, Dot_Net_test 120.000 → 59.953. Win32/Win64
test'te `NET_mi`=0 satırlarının her sha'sı TAM 2 kopya; `NET_mi`=1'de 13 sha 4 kopya (iki farklı
haftada). Train × test ortak eşsiz sha 0.

**Matematiksel not (yorum kuralının temeli):** bir kümede her sha tam k kopyaysa, sabit eşikte her
oran (kaçan, YA) ve AUC çiftli ve tekil kümede AYNIDIR; yalnız n (dolayısıyla Wilson genişliği ve
test istatistikleri) değişir. Fark yalnız kopya sayısı 2'den farklı sha'lardan gelebilir.

## 1. Soru ve sabitler

**(a) Envanter.** Yayındaki ve belgelerdeki tüm "dosya / kayıt / örnek / file / record / sample"
sayıları: site deposu (`CLionProjects\ahmtrntsdln.github.io`, `5a7ccb9`; Chief sayfaları TR/EN, notlar
TR/EN), README.md, README.tr.md, CLAUDE.md, GELISIM_SURECI.md (main `c303d8d` hali). Her sayı için:
kaynak (dosya:satır), değer, sınıf: **satır** (EMBER2024 CSV/Parquet satırı, tekilleştirilmemiş) /
**eşsiz** (sha256 düzeyinde) / **yerel** (bu makinedeki dosya yolu sayısı; içerik çiftlemesi ayrı
konu) / **EMBER 2018** / **oran-yüzde** (sayı değil, envantere girer ama düzeltme gerektirmez) /
**ilgisiz** (dosya sayısı değil). Satır sayısı "dosya" diye yazılmışsa düzeltme taslağı:
"N eşsiz dosya (M satır)" ya da "M satır". Örnek: "959.738" → "479.856 eşsiz dosya (959.738 satır)".
Taslak `sonuclar/8/duzeltme_taslagi.md`'ye yazılır; site ve README dosyaları DEĞİŞTİRİLMEZ.

**(b) Yeniden hesap: 3/, 5/, 6/.** Eşikler ve τ'lar YAYINLANDIĞI GİBİ sabit (yeniden seçilmez).
- 3/ son model (`model_native_meta.json`, kayıtlı model, SHA-256 doğrulamalı): test (hafta 52-63)
  EXE / DLL kaçan ve YA (eşik 0,70 / 0,61), AUC; tekil kümede, Wilson ile. Ayrıca kayıtlı
  `V48_RF_E3_300000_42` ve `V48_RF_E3_483224_42` modelleri (boyut kuralının tohum-42 hücreleri)
  aynı biçimde. 3/'ün diğer hücreleri (LightGBM, diğer tohumlar) için model kayıtlı değil;
  yeniden eğitim yasak → yalnız yapısal argüman (matematiksel not + kopya dağılımı) yazılır.
  Betimleyici: tekil doğrulama diliminde (hafta 48-51) `np.quantile(·, 0,99, "higher")` aynı
  eşikleri veriyor mu (eşik DEĞİŞTİRİLMEZ, yalnız rapor).
- 5/ `net_olcum.py`: A (tekil, `NET_mi` × tür hücreleri) ve B (tekil Dot_Net_test) kaçan / YA,
  Wilson, AUC; yorum kuralları 1-2 tekil sayılarla yeniden. C (yerel) EMBER değil → değişmez.
  `esit_ya.py` EK: Faz 1 modeli aynı kodla (EMBER 2018 verisi, belirlenimci) ve native; τ 0,76 /
  0,43 ve native sabit eşikler SABİT; tekil B'de kaçan / YA / Wilson ve iki kural yeniden.
- 6/ `uzman_native.py`: M2, M2d (aynı tarif, aynı tohum; çiftli havuz - tarif böyle tanımlı) ve
  native; `uzman_native.csv` eşikleri SABİT; tekil Dot_Net_test'te 18 satır (2 H × 3 model × 3 tür)
  kaçan / YA / Wilson ve ön kayıtlı yorum kuralı yeniden.
- **McNemar:** 3/, 5/, 6/'da EMBER verisi üzerinde McNemar YOK (3/ ve 2c'deki McNemar yerel sette;
  yerel set EMBER değil, bu çiftlemeden etkilenmez). Bu durum sonuçta açıkça yazılır; yerel sette
  içerik çiftlemesi ayrı bir sorudur → betimleyici: dondurulmuş setin 94 sütunda birebir aynı
  satır sayısı (aynı vektör ≠ aynı dosya; yalnız üst sınır göstergesi).
- Betimleyici: EMBER 2018 CSV'lerinde (`C:\ember2018\*_ozellik.csv`, repodaki iki 5.700'lük CSV)
  `Dosya_Adi` (sha256'nın ilk 12 hanesi) tekrarı sayılır (Faz 1 ve EMBER 2018 sayılarının
  envanteri için).

**(c) Son modelin eğitim örneği ve örtüşme.** `son_model.py` örneği AYNI kodla yeniden kurulur
(`ortak_deney.tip_ici_dengeli(havuz, 483.224, 42)`, havuz hafta 0-47, satır sırası `ortak_deney.yukle`
ile aynı; `Dosya_Adi` sütunu yalnız kimlik için eklenir). Ölçülenler: örnekteki eşsiz dosya sayısı
(toplam ve 4 hücre); iki kopyası birden örneğe giren dosya sayısı; eşsiz sha örtüşmeleri: örnek ×
doğrulama (48-51), örnek × test, havuz × doğrulama, doğrulama × test.
**Ayrı ölçüm - yanlış alarm kayması (hipotez: kayma kısmen örtüşmeden):** iki örtüşme tanımı:
- **Ö1 (sha):** doğrulama dilimindeki eşsiz dosyanın sha'sı eğitim örneğinde var.
- **Ö2 (vektör, birebir):** dosyanın 86 model sütunu (float32) eğitim örneğindeki bir satırla
  birebir aynı (farklı sha olabilir: aynı özellik vektörü).
Her tanım için zararsız DLL'lerde (kayma DLL'de: doğrulama ~%1 → test %1,43; EXE de yazılır):
doğrulama ve testte örtüşen pay s, örtüşen / örtüşmeyen alt gruplarda YA (eşik 0,61 / EXE 0,70),
Wilson. Karşı-olgusal: doğrulama YA'sı testin örtüşme payına yeniden ağırlıklandırılır,
YA*_dog = s_test · YA_dog,örtüşen + (1 − s_test) · YA_dog,örtüşmeyen; açıklanan pay
= (YA*_dog − YA_dog) / (YA_test − YA_dog). Tüm sayılar tekil dosyalarla.

## 2. Ölçüm ve kontroller

Geçit tutmazsa ilgili bölüm DURUR, "hüküm yok: geçit" yazılır; diğer bölümler sürer.

| # | Kontrol | Geçme koşulu |
|---|---|---|
| G1 | Çiftleme yapısı (her kullanılan küme) | aynı sha'nın kopyalarında etiket ve model sütunları birebir; kopya sayısı dağılımı raporlanır |
| G2 | 3/ yeniden üretim (çiftli) | son model çiftli testte `test_bir_kez` (EXE 17,749 / 0,828; DLL 19,524 / 1,428; AUC 0,9865) birebir; V48 modelleri `esik_boyut.csv`'deki kendi hücreleriyle birebir (kaçan, test YA, AUC) |
| G3 | 5/ yeniden üretim (çiftli) | `net_olcum.csv` A ve B satırlarının k/n'leri birebir; `esit_ya.log` geçidi (Faz 1 kaçan 55662/60000) ve log'daki k/n'ler birebir |
| G4 | 6/ yeniden üretim (çiftli) | `uzman_native.csv` 18 satırın kaçan_k / YA_k'si birebir |
| G5 | (c) örnek kimliği | Parquet sha256_16'lar meta ile aynı; yeniden kurulan örneğin 4 hücre sayısı meta `orneklem_hucreler_DLLmi_Etiket` ile aynı |
| G6 | Envanter tamlığı | her kaynak dosya için taranan satır sayısı ve bulunan sayı adedi raporlanır; "dosya/files" geçen her rakam bir sınıfa atanmış |

**Hesaplama:** tekilleştirme `Dosya_Adi` ile, ilk kopya tutulur (Parquet / CSV satır sırası).
Wilson %95 (`ortak_deney.wilson`). Her yeniden hesaplanan hücre için: çiftli k/n, tekil k/n, %
(iki küme), |Δ%|, çiftli Wilson, tekil Wilson.

## 3. Yorum / karar kuralı

1. **Nokta tahmini:** bir hücrede tekil ve çiftli % arasındaki fark, o hücredeki çok-kopyalı
   (≠ 2) sha'ların en kötü durum etkisinden (Δ_max = o hücredeki fazla satır / tekil n) büyük
   değilse "nokta tahmini aynı (fark kopya dağılımından)" yazılır. Büyükse "BEKLENMEYEN FARK" ve
   neden aranır (ölçüm bitmez; ayrıca listelenir).
2. **Hüküm değişimi:** ön kayıtlı her yorum kuralı (5/ kural 1-2, 5/ EK iki kural, 6/ kuralı)
   tekil sayılarla yeniden uygulanır. Cümlesi değişen her hücre "HÜKÜM DEĞİŞTİ" tablosunda (eski
   cümle, yeni cümle, neden). Değişmeyenler "hüküm aynı". Aralık genişlemesiyle "anlamlı" →
   "fark gösterilemedi" geçişi hüküm değişimidir.
3. **Belgeler:** düzeltme taslağındaki her satır sayısı → eşsiz sayı + "(M satır)"; değişen
   Wilson aralıkları taslağa girer; HÜKÜM DEĞİŞTİ tablosundaki her cümle taslakta düzeltilir.
   Taslak yayınlanmaz, kullanıcı onaylar.
4. **Kayma hipotezi (c):**
   - Ö1'de doğrulama × örnek ortak sha 0 ise "sha düzeyinde doğrulama örtüşmesi yok; kayma bu
     mekanizmayla açıklanamaz".
   - Bir tanımda (Ö1 ya da Ö2) hipotez "KISMEN DESTEKLENDİ" ancak ÜÇ koşul birden sağlanırsa:
     (i) s_dog > s_test, Wilson aralıkları örtüşmüyor; (ii) doğrulamada YA_örtüşen < YA_örtüşmeyen,
     aralıklar örtüşmüyor; (iii) açıklanan pay > 0. O zaman açıklanan pay (nokta) yazılır.
   - Aksi halde "desteklenmedi" (koşul (i) ters yönde anlamlıysa) ya da "gösterilemedi".

## 4. Hüküm verilmeyen durumlar

- Geçit (G1-G6) tutmadı → o bölüm için "hüküm yok: geçit"; diğer bölümler raporlanır.
- 3/'ün kayıtlı modeli olmayan hücreleri → yeniden hesap yok, "hüküm yok: model kayıtlı değil,
  yeniden eğitim kapsam dışı"; yalnız yapısal argüman.
- Hücre n < 30 → oran yorumlanmaz, yalnız k/n (ör. 5/ B'de bayraksız 6 zararlı).
- Kayma (c): örtüşen alt grupta zararsız DLL n < 30 → o tanım için "hüküm yok: örtüşen n küçük".
- Ö2 yalnız BİREBİR vektör eşitliğidir; yakın kopyalar ölçülmez → "örtüşme yok" sonucu yakın
  kopya yokluğu diye yazılmaz.
- Envanterde sınıfı belirlenemeyen sayı (kaynağı bulunamayan) → "sınıf belirsiz" diye listelenir,
  tahminle düzeltilmez.

## Sınırlar (sonuçtan önce)

- Çiftli havuzla eğitilmiş modeller değiştirilmez; çiftlemenin EĞİTİME etkisi (aynı kaydın iki
  kopyası ≈ ağırlık 2) bu pakette ölçülmez - ayrı karar (kullanıcı: şimdilik eğitim yenilenmez).
- 2a / 2b / 2c ve 9 Ekim deneyleri, `net_model.py` ablasyonu, Faz 1 `net_dogrulama.py` bu pakette
  yeniden hesaplanmaz; sayıları belgelerde geçiyorsa envanterde (a) sınıflanır.
- AGENTS.md (dış depoda izlenmeyen dosya) envantere girmez; yalnız varlığı not edilir.
