# İş 7 — Çiftleme Denetimi Sonucu (`denetim/ciftleme`)

- **Ön kayıt:** `gumruk_memuru/sonuclar/8/ciftleme_on_kayit.md` (`57e5b53`, ölçümden önce commit'lendi) ve `gumruk_memuru/sonuclar/6/FAZ1_KAPANIS.md` (Revizyon 5, İş 7).
- **Betikler:** `envanter_aday.py`, `envanter.py`, `ciftleme_b.py`, `ciftleme_c.py`.
- **Çıktılar:** `envanter.csv`, `envanter.log`, `ciftleme_b.csv` (94 satır), `ciftleme_b_hukum.csv` (20 satır), `ciftleme_b.log`, `ciftleme_c.log`, `duzeltme_taslagi.md`.

---

## 1. Geçit Kontrolleri (G1–G6)

| # | Kontrol | Sonuç | Kanıt / Özet |
|---|---|---|---|
| **G1** | Çiftleme yapısı (her kullanılan küme) | **GEÇTİ** | Win32/Win64 test: `959.738` satır → **`479.856` eşsiz** (`{2: 479.843, 4: 13}`), çelişkili `sha256` = **0**. `Dot_Net_test`: `120.000` satır → **`59.953` eşsiz** (`{2: 59.906, 4: 47}`), çelişkili `sha256` = **0**. |
| **G2** | `3/` yeniden üretim (çiftli) | **GEÇTİ** *(Kural 10 notuyla)* | `model_native.joblib` (SHA-256 doğrulandı) çiftli testte `test_bir_kez` ile birebir: EXE kaçan `17,749` / YA `0,828`, DLL kaçan `19,524` / YA `1,428`, AUC `0,9865`. *(Not: `V48_RF_E3_*` dosyaları meta veride SHA-256 kaydı olmadığından Kritik Kural 10 gereği yüklenmedi; bkz. Bölüm 6).* |
| **G3** | `5/` yeniden üretim (çiftli) | **GEÇTİ** | `net_olcum.csv` A ve B satırlarının `k/n`'leri birebir; `esit_ya.log` geçidi (Faz 1 kaçan `55.662/60.000 = %92,77`) ve tüm `k/n`'ler birebir. |
| **G4** | `6/` yeniden üretim (çiftli) | **GEÇTİ** | `uzman_native.csv` içindeki 18 satırın `kacan_k` ve `YA_k` değerleri birebir. |
| **G5** | `(c)` örnek kimliği | **GEÇTİ** | 4 Parquet dosyasının `sha256_16` özetleri `model_native_meta.json` ile birebir; havuz `3.838.526` satır, örnek hücreleri `{'0_0': 120806, '0_1': 120806, '1_0': 120806, '1_1': 120806}` meta ile birebir. |
| **G6** | Envanter tamlığı | **GEÇTİ** | 14 kaynak dosya (`3.994` satır) tarandı, `907` sayı bulundu; `"dosya"`/`"files"` geçen satırlardaki `448/448` rakam ve tüm adaylar sınıflandı (`sınıf belirsiz` = **0**). |

---

## 2. (a) Sayı Envanteri Özeti (`envanter.py`, `envanter.csv`)

Taranan 14 kaynak dosyada (`README.md`, `README.tr.md`, `CLAUDE.md`, `GELISIM_SURECI.md` ve `ahmtrntsdln.github.io` içindeki 10 HTML dosyası; `AGENTS.md` depoda izlenmeyen dış dosya olduğundan kapsam dışı bırakıldı) toplam **907** sayı/ifade sınıflanmıştır:

| Sınıf | Adet | Açıklama |
|---|---:|---|
| `satır` | **54** | EMBER2024 CSV/Parquet çiftli satır sayısı (`959.738`, `483.224`, `4.158.450`, `120.000`, `520.000`, `120.806`, `522.200`, `96.416`, `300 bin`, `100K`, `240K`, `20K`, `1.550`, `262`, `236`, `208`, `308`, `8`) — `duzeltme_taslagi.md`'de eşsiz karşılıklarıyla taslaklandı |
| `eşsiz` | **5** | EMBER2024 `sha256` bazlı tekil sayılar (`CLAUDE.md:562` `60K`, `net-kor-nokta.html:44` `60 bin`, `dotnet-blind-spot.html:44` `60 thousand`, `CLAUDE.md:398` `3.2M`, `CLAUDE.md:65` `0`). EMBER2024 belgesindeki "60K" ifadesinin hatalı değil, `Dot_Net_test`'in **`59.953` eşsiz dosya sayısı** olduğu doğrulandı |
| `yerel` | **97** | Bu makineden çekilen gerçek dosya yolu sayıları (`5.635`, `5.700`, `533.081`, `64.263`, `3.471`, `857`, `500` vb.) — EMBER çiftlemesinden etkilenmez |
| `EMBER 2018` | **35** | EMBER 2018 kayıt/dosya sayıları (`5.700`, `11.400`, `34 bin`, `188.600`, `60 bin`, `200.000`, `600.000`, `162`, `22`, `2000`) — `Dosya_Adi` tekrarı **0** olduğundan düzeltme gerekmez |
| `oran-yüzde` | **244** | Oran, yüzde, AUC, eşik ve Wilson sınırları (değişen Wilson aralıkları ayrıca `duzeltme_taslagi.md`'de) |
| `ilgisiz` | **472** | Dosya sayısı olmayan rakamlar (yıl, CSS renk kodu, piksel, özellik sayısı, hafta numarası, çıkış kodu vb.) |
| `sınıf belirsiz` | **0** | Kaynağı bulunamayan sayı yok |

---

## 3. (b) `3/`, `5/`, `6/` Tekil Dosyada Yeniden Hesap (`ciftleme_b.py`)

### 3.1 Kural 1 Özeti (Nokta Tahminleri)
- `ciftleme_b.csv` içindeki **94 ölçünün tamamında** tekil ve çiftli yüzdeler arasındaki fark `|Δ%| ≤ Δ_max` sınırındadır (**`BEKLENMEYEN FARK = 0`**).
- En büyük mutlak fark `5/ A .NET EXE YA` hücresindedir: çiftli `6/208 = %2,885` vs tekil `3/101 = %2,970` (`|Δ%| = 0,086` puan ≤ `Δ_max = 2,885` puan; 5 zararsız `.NET` EXE `sha256` kaydının iki ayrı haftada yer alıp 4 kopyaya çıkmasından).
- Yalnız 2 kopyalı kayıtlardan oluşan hücrelerde (`3/` DLL kaçan ve DLL YA, `5/ A` `.NET` DLL kaçan ve YA, `5/ B` zararlı `.NET` EXE ve DLL kaçanları) tekil ve çiftli nokta tahminleri matematiksel olarak **virgülden sonra tüm basamaklarda birebir aynıdır** (`|Δ%| = 0,000`).

### 3.2 `3/` Son Model (`model_native.joblib`, Test Haftaları 52–63)

| Alt Küme / Ölçü | Çiftli (`959.738` satır) | Tekil (`479.856` eşsiz dosya) | `|Δ%|` | `Δ_max` | Kural 1 |
|---|---|---|---:|---:|---|
| **EXE kaçan** (eşik `0,70`) | `%17,749 [17,638–17,861] (80.120/451.402)` | **`%17,749 [17,592–17,907] (40.060/225.701)`** | `0,000` | `0,004` | nokta tahmini aynı |
| **EXE yanlış alarm** (eşik `0,70`) | `%0,828 [0,780–0,879] (1.056/127.546)` | **`%0,828 [0,761–0,901] (528/63.770)`** | `0,000` | `0,010` | nokta tahmini aynı |
| **DLL kaçan** (eşik `0,61`) | `%19,524 [19,069–19,988] (5.582/28.590)` | **`%19,524 [18,883–20,182] (2.791/14.295)`** | `0,000` | `0,000` | nokta tahmini aynı |
| **DLL yanlış alarm** (eşik `0,61`) | `%1,428 [1,390–1,468] (5.030/352.200)` | **`%1,428 [1,374–1,485] (2.515/176.090)`** | `0,000` | `0,000` | nokta tahmini aynı |
| **Genel / EXE / DLL AUC** | `0,98651` / `0,98373` / `0,98439` | **`0,98651` / `0,98373` / `0,98439`** | `0,00000` | — | aynı |

- **Yapısal argüman (`3/` diğer hücreler):** Kayıtlı modeli olmayan LightGBM ve diğer tohum hücrelerinde test kümesinin `%99,997`'si (`479.843 / 479.856`) tam 2 kopyalı olduğundan her dosyanın ağırlığı `2/2N = 1/N` kalır; yalnızca `13` `.NET` `sha256` kaydı 4 kopyalıdır (`EXE`'de `Δ_max ≤ %0,010`, `DLL`'de `0`). Dolayısıyla `3/` boyut ve model seçim kararları tekil test kümesinde de değişmez.
- **Betimleyici (eşik yeniden seçimi, DEĞİŞTİRİLMEZ):** Hafta 48–51 doğrulama diliminde (`319.924` satır → `159.962` eşsiz dosya; her `sha256` tam 2 kopya) `np.quantile(·, 0.99, "higher")` tekil kümede de **birebir aynı eşikleri** (`EXE 0,7000`, `DLL 0,6100`) verir.

### 3.3 `5/` `.NET` Ölçümü (`net_olcum.py` ve `esit_ya.py` EK)

| Bölüm / Küme | Ölçü | Çiftli `% [Wilson] (k/n)` | Tekil `% [Wilson] (k/n)` | Hüküm |
|---|---|---|---|---|
| `5/ A` (Win32/64 test) | `.NET=1` EXE kaçan | `%33,74 [32,12–35,40] (1.083/3.210)` | **`%33,73 [31,46–36,08] (540/1.601)`** | hüküm aynı (`.NET` EXE anlamlı daha kötü) |
| `5/ A` (Win32/64 test) | `.NET=1` EXE YA | `%2,88 [1,33–6,15] (6/208)` | **`%2,97 [1,02–8,37] (3/101)`** | hüküm aynı (`.NET` dışı `[0,76–0,90]` ile örtüşmüyor) |
| `5/ A` (Win32/64 test) | `.NET=1` DLL kaçan | `%23,38 [19,00–28,42] (72/308)` | **`%23,38 [17,39–30,66] (36/154)`** | hüküm aynı (`[18,88–20,18]` ile örtüşüyor → fark gösterilemedi) |
| `5/ A` (Win32/64 test) | `.NET=1` DLL YA | `%0,00 [0,00–0,26] (0/1.466)` | **`%0,00 [0,00–0,52] (0/732)`** | hüküm aynı |
| `5/ B` (`Dot_Net_test`, tür eşiği) | `hepsi` kaçan / YA | `%49,77 [49,37–50,17] (29.860/60.000)` / `%1,05 [0,97–1,13] (630/60.000)` | **`%49,77 [49,20–50,33] (14.930/30.000)`** / **`%1,05 [0,94–1,17] (315/29.953)`** | hüküm aynı |
| `5/ B` (`Dot_Net_test`, tür eşiği) | `EXE` kaçan / YA | `%45,87 [45,45–46,29] (24.716/53.880)` / `%0,89 [0,70–1,13] (66/7.436)` | **`%45,87 [45,28–46,46] (12.358/26.940)`** / **`%0,89 [0,63–1,25] (33/3.713)`** | hüküm aynı |
| `5/ B` (`Dot_Net_test`, tür eşiği) | `DLL` kaçan / YA | `%84,19 [83,25–85,08] (5.144/6.110)` / `%1,07 [0,99–1,16] (564/52.564)` | **`%84,19 [82,85–85,44] (2.572/3.055)`** / **`%1,07 [0,96–1,21] (282/26.240)`** | hüküm aynı |
| `5/ EK` (`esit_ya.py`, `B`) | Nokta 1 (`YA ~%0,46`) Faz 1 vs native kaçan | `%92,77 [92,56–92,97]` vs `%59,79 [59,40–60,18]` | **`%92,77 [92,47–93,06]`** vs **`%59,79 [59,23–60,34]`** | hüküm aynı (`NATIVE daha az kaçırıyor`) |
| `5/ EK` (`esit_ya.py`, `B`) | Nokta 2 (`YA ~%1,05`) Faz 1 vs native kaçan | `%89,39 [89,14–89,64]` vs `%49,77 [49,37–50,17]` | **`%89,39 [89,04–89,74]`** vs **`%49,77 [49,20–50,33]`** | hüküm aynı (`NATIVE daha az kaçırıyor`) |

### 3.4 `6/` Uzman vs Native (`uzman_native.py`) ve `HÜKÜM DEĞİŞTİ` Tablosu

`6/` içindeki 18 ölçüm satırının tamamı `ciftleme_b.csv`'de, 12 karşılaştırma hücresinin tamamı `ciftleme_b_hukum.csv`'de raporlanmıştır. 20 toplam hüküm hücresinden (`5/` 8 + `6/` 12) **19'unda hüküm aynı kalmış, 1 hücrede hüküm değişmiştir**:

| Küme / Hücre | Eski Cümle (Çiftli, `n_YA = 7.436`) | Yeni Cümle (Tekil, `n_YA = 3.713`) | Neden |
|---|---|---|---|
| **`6/ | H %1,05 | M2 (uzman, kestirmeli) vs native | EXE`** | `eşit yanlış alarm SAĞLANAMADI (test YA %1,48 [1,23–1,78] vs %0,89 [0,70–1,13]) → hüküm yok` | **`UZMAN daha az kaçırıyor`** `(test YA %1,48 [1,14–1,92] vs %0,89 [0,63–1,25] örtüşüyor; kaçan %31,40 [30,86–31,96] vs %62,80 [62,23–63,37])` | Tekil kümede zararsız EXE örneklem boyutu `7.436`'dan `3.713`'e inince %95 Wilson güven aralıkları genişledi (`[1,14–1,92]` ve `[0,63–1,25]`) ve `[1,14–1,25]` aralığında örtüştü; ön kayıtlı kurala göre eşit YA koşulu sağlandığından kaçan zararlı karşılaştırmasına geçildi. |

### 3.5 McNemar ve Betimleyici Kontroller (Yerel Set ve EMBER 2018)
- **McNemar:** `3/`, `5/`, `6/` paketlerinde EMBER2024 verisi üzerinde McNemar testi yoktur (McNemar yalnız yerel `5.635` doğrulama setinde uygulanmıştır; yerel set EMBER2024 çiftlemesinden etkilenmez).
- **Yerel `5.635` sette 94 sütun tekrarı (betimleyici üst sınır):** Dondurulmuş `sef_yerel_dogrulama_5635.csv` içindeki `5.635` farklı dosya yolundan, 94 CSV sütununun tamamında ilk geçişiyle birebir aynı olan satır sayısı **`174`**'tür (`5.461` tekil 94-sütun vektörü; `.NET` alt kümesinde `3.471` satırın `151`'i, `3.320` tekil vektör). Aynı özellik vektörü aynı dosya demek değildir; yalnız içerik çiftlemesi için üst sınır göstergesidir.
- **EMBER 2018 `Dosya_Adi` tekrarı (betimleyici):**
  - `C:\ember2018\ember2018_train_ozellik.csv`: `600.000` satır, **`600.000` eşsiz** (`tekrar = 0`).
  - `C:\ember2018\ember2018_test_ozellik.csv`: `200.000` satır, **`200.000` eşsiz** (`tekrar = 0`).
  - `sef_dataset_zararli_gercek.csv` ve `sef_dataset_ember_zararsiz.csv`: `5.700`'er satır, **`5.700`'er eşsiz** (`tekrar = 0`).

---

## 4. (c) Son Modelin Eğitim Örneği ve Yanlış Alarm Kayması Hipotezi (`ciftleme_c.py`)

### 4.1 Son Model Eğitim Örneklemi (`483.224` Satır) Eşsiz Dosya Yapısı
`ortak_deney.tip_ici_dengeli(havuz, 483_224, 42)` ile hafta 0–47 havuzundan (`3.838.526` satır = `1.919.263` eşsiz dosya) birebir yeniden kurulan örneklemde:
- **Toplam:** `483.224` satır = **`402.129` eşsiz dosya (`%83,22`)**.
- **Kopya dağılımı:** `321.034` dosya örneklemde **1 kez**, `81.095` dosya **2 kez** (iki kopyası birden) yer alır (`321.034 + 2 × 81.095 = 483.224`).

| Hücre (`DLL_mi`, `Etiket`) | Örneklem Satır | Örneklem Eşsiz | İki Kopyası Birden Giren | Havuz Satır (Hafta 0–47) | Havuz Eşsiz |
|---|---:|---:|---:|---:|---:|
| `DLL_mi=0, Etiket=0` (Zararsız EXE) | `120.806` | **`109.943`** | `10.863` | `677.186` | `338.593` |
| `DLL_mi=0, Etiket=1` (Zararlı EXE) | `120.806` | **`116.809`** | `3.997` | `1.798.488` | `899.244` |
| `DLL_mi=1, Etiket=0` (Zararsız DLL) | `120.806` | **`114.974`** | `5.832` | `1.242.046` | `621.023` |
| `DLL_mi=1, Etiket=1` (Zararlı DLL) | `120.806` | **`60.403`** | **`60.403`** *(tamamı)* | `120.806` | `60.403` |
| **TOPLAM** | **`483.224`** | **`402.129`** | **`81.095`** | **`3.838.526`** | **`1.919.263`** |

### 4.2 Eşsiz `sha256` (`Ö1`) Dilimler Arası Örtüşme
- `örnek (402.129) × doğrulama (159.962)` = **`0`**
- `örnek (402.129) × test (479.856)` = **`0`**
- `havuz (1.919.263) × doğrulama (159.962)` = **`0`**
- `doğrulama (159.962) × test (479.856)` = **`0`**
- `havuz (1.919.263) × test (479.856)` = **`0`**

EMBER2024 Win32/Win64 eğitim havuzu (hafta 0–47), doğrulama dilimi (hafta 48–51) ve test kümesi (hafta 52–63) arasında **`sha256` düzeyinde tek bir ortak dosya bile yoktur**. Çiftleme yalnızca her haftalık JSONL dosyasının kendi içindedir.

### 4.3 Yanlış Alarm Kayması Hipotezi (`Ö1` ve `Ö2`, Tekil Zararsızlar)

| Tür (Eşik) | Tanım | Doğrulama Örtüşen Pay `s_dog` | Test Örtüşen Pay `s_test` | Doğrulama `YA_örtüşen` | Doğrulama `YA_örtüşmeyen` | Karşı-Olgusal `YA*_dog` | Açıklanan Pay | Koşullar `(i)/(ii)/(iii)` | Karar |
|---|---|---|---|---|---|---:|---:|---|---|
| **DLL (`0,61`)** *(YA dog `%0,988` → test `%1,428`)* | **Ö1 (`sha256`)** | `%0,000 [0,000–0,007] (0/53.945)` | `%0,000 [0,000–0,002] (0/176.090)` | — | `%0,988 [0,908–1,075] (533/53.945)` | — | — | — | **sha düzeyinde doğrulama örtüşmesi yok; kayma bu mekanizmayla açıklanamaz** |
| **DLL (`0,61`)** | **Ö2 (86 sütun vektör)** | `%0,810 [0,738–0,889] (437/53.945)` | `%0,354 [0,328–0,383] (624/176.090)` | `%0,229 [0,040–1,285] (1/437)` | `%0,994 [0,914–1,082] (532/53.508)` | `%0,992` | `0,008` (`%0,8`) | `True / False / True` | **`gösterilemedi`** *(Wilson `[0,040–1,285]` ile `[0,914–1,082]` örtüşüyor; açıklanan pay yalnızca `%0,8`)* |
| **EXE (`0,70`)** *(YA dog `%0,942` → test `%0,828`)* | **Ö1 (`sha256`)** | `%0,000 [0,000–0,015] (0/26.017)` | `%0,000 [0,000–0,006] (0/63.770)` | — | `%0,942 [0,831–1,067] (245/26.017)` | — | — | — | **sha düzeyinde doğrulama örtüşmesi yok; kayma bu mekanizmayla açıklanamaz** |
| **EXE (`0,70`)** | **Ö2 (86 sütun vektör)** | `%1,203 [1,078–1,343] (313/26.017)` | `%0,913 [0,842–0,989] (582/63.770)` | `%0,000 [0,000–1,212] (0/313)` | `%0,953 [0,841–1,079] (245/25.704)` | `%0,944` | `-0,024` | `True / False / False` | **`gösterilemedi`** |

**Yorum:** DLL yanlış alarmının doğrulama dilimindeki `%0,988`'den test kümesinde `%1,428`'e çıkışı (44 baz puanlık kayma), eğitim örneklemiyle doğrulama dilimi arasındaki `sha256` örtüşmesiyle (`Ö1 = 0`) açıklanamaz; birebir 86-sütun vektör örtüşmesi (`Ö2`) ise karşı-olgusal olarak kaymanın yalnızca `%0,8`'ini (`0,35` baz puan) açıklamakta ve `(ii)` koşulunu sağlamamaktadır (`gösterilemedi`). Kayma, dilimler arası kopya sızıntısından değil, hafta 48–51 ile hafta 52–63 arasındaki zamansal dağılım değişiminden kaynaklanmaktadır.

---

## 5. Ön Kayıttan Sapmalar ve Sınırlar

1. **Kritik Kural 10 sapması (`G2` / Bölüm 1b):** `ciftleme_on_kayit.md` içinde `V48_RF_E3_300000_42` ve `V48_RF_E3_483224_42` modellerinin de yükleneceği yazılmıştı. Ancak `CLAUDE.md` Kritik Kural 10 (*"SHA-256 doğrulaması olmadan pickle/joblib yükleme YASAK"*) uyarınca, `model_native_meta.json`'da yalnızca son modelin (`model_native.joblib`, SHA-256 `f6b74df812f02d75...`) özeti kayıtlı olduğundan bu iki ara model dosyası yüklenmemiştir. `V48_RF_E3_483224_42` zaten son model ile aynı tarif ve aynı tohumdur (`483.224`, tohum 42); `300.000` hücresi için Bölüm 3.2'deki yapısal argüman geçerlidir.
2. **Eğitim etkisi kapsam dışı:** Modeller çiftli havuzdan örneklenen verilerle eğitilmiştir (`483.224` satırda `81.095` dosyanın iki kopyası ≈ ağırlık 2). Kullanıcı kararı ve ön kayıt gereği modeller yeniden eğitilmemiştir.
3. **Yakın kopyalar:** `Ö2` yalnızca 86 model sütununda `float32` birebir vektör eşitliğini ölçer; yakın kopyalar (küçük bayt farkları) bu paketin kapsamı dışındadır.
4. **Düzeltme taslağı onayı:** `duzeltme_taslagi.md` içindeki belge ve site düzeltmeleri kullanıcı onayına sunulmuştur; onay olmadan `README*`, `CLAUDE.md`, `GELISIM_SURECI.md` ve site deposuna dokunulmamıştır.
