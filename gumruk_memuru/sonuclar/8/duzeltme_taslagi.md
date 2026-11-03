# İş 7 — Belgeler ve Site İçin Düzeltme Taslağı (Onay Bekliyor)

**Durum:** TASLAK — `ciftleme_on_kayit.md` Kural 3 ve `FAZ1_KAPANIS.md` İş 7 uyarınca yayındaki belgeler (`README.md`, `README.tr.md`, `CLAUDE.md`, `GELISIM_SURECI.md`) ve site deposu (`ahmtrntsdln.github.io`) **henüz değiştirilmemiştir**. Kullanıcı onayından sonra uygulanacaktır.

**Dayanak:** `envanter.csv` (`G6` geçti: 14 dosya, 3.994 satır, 907 sayı; `satır` = 54, `eşsiz` = 5, `belirsiz` = 0), `ciftleme_b.csv` (94 ölçü), `ciftleme_b_hukum.csv` (20 hüküm; 19 aynı, **1 HÜKÜM DEĞİŞTİ**) ve `ciftleme_c.log`.

---

## 1. Hızlı Eşdeğerlik Özeti (Satır → Eşsiz Dosya)

| Küme / Örneklem | Belgelerdeki Satır Sayısı (`satır`) | Eşsiz `sha256` Dosya Sayısı (`eşsiz`) | Kopya Yapısı / Not |
|---|---:|---:|---|
| Win32/Win64 eğitim (hafta 0–51) | `4.158.450` (`4,16 milyon`) | **`2.079.225`** (`2,08 milyon`) | Her `sha256` 2 kez (`is_pe=0` atlanan: `1.550` satır = `775` eşsiz) |
| Win32/Win64 eğitim havuzu (hafta 0–47) | `3.838.526` | **`1.919.263`** | Her `sha256` 2 kez |
| Win32/Win64 doğrulama dilimi (hafta 48–51) | `319.924` | **`159.962`** | Her `sha256` 2 kez |
| Win32/Win64 test kümesi (hafta 52–63) | `959.738` | **`479.856`** | `479.843` × 2 kopya + `13` (`.NET`) × 4 kopya (`is_pe=0` atlanan: `262` satır = `131` eşsiz) |
| Son model eğitim örneklemi (`son_model.py`, 4×120.806) | `483.224` | **`402.129`** (`%83,22`) | `{1: 321.034, 2: 81.095}`; zararlı DLL hücresinde havuzdaki tüm `60.403` eşsiz dosyanın 2 kopyası (`120.806` satır) |
| Hafta 0–51 tip-içi 4 hücre tavanı (4×130.550) | `522.200` | **`261.100`** (4×65.275 tavanı) | Zararlı DLL (hafta 0–51): `130.550` satır = `65.275` eşsiz |
| Win32/Win64 `300 bin` örneklem (tohum 42) | `300.000` | **`268.625`** (48h) / **`271.385`** (52h) | Hafta 0–47 tip-içi: `268.625` eşsiz; hafta 0–51 tip-içi: `271.385` eşsiz |
| Win32/Win64 `100K` / `100 bin` örneklem (tohum 42, 52h) | `100.000` | **`96.828`** (E3) / **`98.787`** (E1–E2) | Tip-içi (E3): `96.828` eşsiz; sınıf dengeli (E1/E2): `98.787` eşsiz |
| `Win64_test` (12 hafta, haftada `20K`) | `240.000` (`240K`) | **`120.000`** (`120K`, haftada `10K`) | `datadirectories` olmayan: `236` satır = `118` eşsiz |
| `Dot_Net_train` (hafta 0–51) | `519.992` PE (`520.000` ham) | **`259.996`** (`~130K/~130K`) | `259.996` × 2 kopya (`is_pe=0` atlanan: `8` satır = `4` eşsiz) |
| `Dot_Net_test` (hafta 52–63) | `120.000` (`60K/60K`) | **`59.953`** (`30.000` zararlı + `29.953` zararsız) | `59.906` × 2 + `47` × 4 kopya. **EMBER2024 belgesindeki "60K" sayısı hatalı değil, `59.953` eşsiz dosya sayısıdır.** |
| `.NET` uzman `100K` örneklem (hafta 0–51, `net_model.py`) | `100.000` | **`90.330`** (M1/M2) / **`74.542`** (M2d) | Sınıf dengeli (M1/M2): `90.330` eşsiz; tip-içi (M2d): `74.542` eşsiz |
| `.NET` uzman hafta 0–47 (`uzman_native.py`: M2 `100K`, M2d `96.416`) | `100.000` / `96.416` | **`89.696`** (M2) / **`70.634`** (M2d) | M2d `4 × 24.104 = 96.416` satır; zararsız EXE havuzu `24.104` satır = `12.052` eşsiz |
| `5/ A` Win32/Win64 testte `.NET` zararsız EXE (`n=208`) | `208` | **`101`** | `94` × 2 + `5` × 4 kopya; YA `6/208 = %2,88` → **`3/101 = %2,97 [1,02–8,37]`** |
| `5/ A` Win32/Win64 testte `.NET` zararlı DLL (`n=308`) | `308` | **`154`** | `154` × 2 kopya; kaçan `72/308 = %23,38 [19,00–28,42]` → **`36/154 = %23,38 [17,39–30,66]`** |

---

## 2. Depo Belgeleri (`main` `c303d8d`) Düzeltme Taslağı

### 2.1 `README.md`

| Satır | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---:|---|---|
| 121 | `80 string features + DLL flag): Random Forest, 483,224 training files sampled` | `80 string features + DLL flag): Random Forest, 402,129 unique training files (483,224 rows; each EMBER2024 JSONL week lists every sha256 twice, so the malicious-DLL cell contains both copies of all 60,403 unique malicious DLLs in the pool) sampled` |
| 128 | `file type); the test weeks 52-63 (959,738 files) were measured once with` | `file type); the test weeks 52-63 (479,856 unique files / 959,738 rows) were measured once with` |

### 2.2 `README.tr.md`

| Satır | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---:|---|---|
| 117 | `DLL bayragi) Random Forest geldi: 483.224 egitim dosyasi, her dosya turunun` | `DLL bayragi) Random Forest geldi: 402.129 essiz egitim dosyasi (483.224 satir; EMBER2024 JSONL haftalarinda her sha256 iki kez yer aldigindan zararli DLL hucresinde havuzdaki 60.403 essiz dosyanin iki kopyasi), her dosya turunun` |
| 124 | `alarm); test haftalari 52-63 (959.738 dosya) bu sabit esiklerle bir kez olculdu:` | `alarm); test haftalari 52-63 (479.856 essiz dosya / 959.738 satir) bu sabit esiklerle bir kez olculdu:` |

### 2.3 `GELISIM_SURECI.md`

| Satır | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---:|---|---|
| 107 | `Win32/Win64 test kümesinde (son 12 hafta, 959.738 dosya) ölçtüğümüzde AUC` | `Win32/Win64 test kümesinde (son 12 hafta, 479.856 eşsiz dosya / 959.738 satır) ölçtüğümüzde AUC` |
| 127 | `483.224 örnek, 300 binden 1,69 puan daha az zararlı DLL kaçırdı (tohum` | `483.224 satırlık örneklem (402.129 eşsiz dosya), 300 bin satırdan (tohum 42'de 268.625 eşsiz dosya) 1,69 puan daha az zararlı DLL kaçırdı (tohum` |

### 2.4 `CLAUDE.md`

| Satır | Tür | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---:|---|---|---|
| 38 | `satır` | `- EMBER2024 .NET test (120.000 dosya, Eylül-Aralık 2024, eğitimde hiç` | `- EMBER2024 .NET test (59.953 eşsiz dosya / 120.000 satır, Eylül-Aralık 2024, eğitimde hiç` |
| 63–66 | `satır` | `- Veri: Dot_Net_train (520K, ilk 52 hafta) -> 100K alt örnek; test Dot_Net_test (120K, son 12 hafta) - zamansal bölme. Eğitim/test ortak dosya 0; birebir aynı özellik vektörü %1.6 (çıkarınca sonuç değişmiyor). Train'deki 8 kayıt PE değil (`is_pe=0`, 146 baytlık JSON hata metni);` | `- Veri: Dot_Net_train (259.996 eşsiz dosya / 519.992 PE satırı, ham JSONL 520K, ilk 52 hafta) -> 100K satırlık alt örnek (M1/M2'de 90.330, M2d'de 74.542 eşsiz dosya); test Dot_Net_test (59.953 eşsiz dosya / 120K satır, son 12 hafta) - zamansal bölme. Eğitim/test ortak dosya 0; birebir aynı özellik vektörü %1.6 (çıkarınca sonuç değişmiyor). Train'deki 4 eşsiz kayıt (8 satır) PE değil (`is_pe=0`, 146 baytlık JSON hata metni);` |
| 100–103 | `satır` + **HÜKÜM DEĞİŞTİ** | `Uzmanlar hafta 0-47'de (M2 100K, M2d 96.416), eşikler hafta 48-51'den tür başına, test bir kez. Hüküm verilebilen hücreler (test YA örtüşüyor) yalnız EXE: H %0.45 M2d kaçan 34.07 vs native 72.58, H %1.05 23.46 vs 62.80 -> uzman daha az kaçırıyor.` | `Uzmanlar hafta 0-47'de (M2 100K satır / 89.696 eşsiz dosya, M2d 96.416 satır / 70.634 eşsiz dosya), eşikler hafta 48-51'den tür başına, test bir kez (59.953 eşsiz dosya / 120.000 satır). Hüküm verilebilen hücreler (test YA örtüşüyor) yalnız EXE: H %0.45 M2d kaçan 34.07 vs native 72.58, H %1.05 M2d 23.46 vs 62.80 ve (tekil dosyada Wilson genişlemesiyle YA [1.14-1.92] vs [0.63-1.25] örtüştüğünden) H %1.05 M2 31.40 vs 62.80 -> uzman daha az kaçırıyor (çiftlide H %1.05 M2 EXE eşit YA sağlanamadıydı; İş 7).` |
| 157–162 | `satır` | `Eğitim 4.158.450 kayıt (hafta 0-51), test 959.738 (hafta 52-63). is_pe=0 atlandı (train 1.550, test 262).` / `- Kural 5 incelemesi (Win64_test, 240K): ... 236 kayıtta hiç dizin yok ... haftada 20K, 50/50.` | `Eğitim 2.079.225 eşsiz dosya / 4.158.450 satır (hafta 0-51), test 479.856 eşsiz dosya / 959.738 satır (hafta 52-63). is_pe=0 atlandı (train 775 eşsiz / 1.550 satır, test 131 eşsiz / 262 satır).` / `- Kural 5 incelemesi (Win64_test, 120K eşsiz dosya / 240K satır): ... 118 eşsiz kayıtta (236 satır) hiç dizin yok ... haftada 10K eşsiz dosya (20K satır), 50/50.` |
| 177 | `satır` | `- Sonuç (`ember2024_native_dogrulama.py`; RF 100 ağaç, 100K alt örneklem,` | `- Sonuç (`ember2024_native_dogrulama.py`; RF 100 ağaç, 100K satırlık alt örneklem [tohum 42'de E3 96.828, E1/E2 98.787 eşsiz dosya],` |
| 196 | `satır` | `zaten uzman modele gidecek (mimari, .NET bölümü). Bu 9 Ekim deneyinden (100 bin,` | `zaten uzman modele gidecek (mimari, .NET bölümü). Bu 9 Ekim deneyinden (100 bin satır,` |
| 200–202 | `satır` + **Wilson** | `A native test .NET alt grubu: EXE kaçan %33.74 [32.1-35.4] (.NET dışı 17.63), YA %2.88 [1.3-6.2] (n=208; .NET dışı 0.82) -> EXE'de anlamlı olarak daha kötü; DLL kaçan 23.38 [19.0-28.4] vs 19.48 -> fark gösterilemedi (n=308).` | `A native test .NET alt grubu (tekil dosyada): EXE kaçan %33.74 [31.5-36.1] (.NET dışı 17.63), YA %2.97 [1.0-8.4] (3/101 eşsiz dosya; çiftlide %2.88 [1.3-6.2], 6/208 satır; .NET dışı 0.82) -> EXE'de anlamlı olarak daha kötü; DLL kaçan 23.38 [17.4-30.7] vs 19.48 -> fark gösterilemedi (n=154 eşsiz dosya / 308 satır).` |
| 221–230 | `satır` | `300 binde ...` / `(100 bin -> 4,16 milyon ...)` / `(kazanç < tohum std -> 300 bin). 522.200 zamansal doğrulamayla kurulamaz (havuzda zararlı DLL 120.806) -> 483.224. Kazanç 1.69 puan ≥ s 0.72 -> **483.224**. Kaynak (tohum 42): 300 bin 279 MB / 4.2 ms, 483.224 395 MB / 3.6 ms` / `- SON MODEL (`sonuclar/3/son_model.py`): RF E3, 483.224, tohum 42, hafta 0-47;` | `300 bin satırda (tohum 42'de 268.625 eşsiz dosya) ...` / `(100 bin satır -> 4,16 milyon satır / 2,08 milyon eşsiz dosya ...)` / `(kazanç < tohum std -> 300 bin satır). 522.200 satır (4×65.275 = 261.100 eşsiz tavanı) zamansal doğrulamayla kurulamaz (havuzda zararlı DLL 60.403 eşsiz dosya / 120.806 satır) -> 483.224 satır (402.129 eşsiz dosya; zararlı DLL hücresinde 60.403 eşsiz dosyanın iki kopyası). ...` / `- SON MODEL (`sonuclar/3/son_model.py`): RF E3, 483.224 satır (402.129 eşsiz dosya), tohum 42, hafta 0-47;` |
| 331, 373 | `satır` | `` `2b/` RF 300 bin (+ 9 Ekim 100 bin) `` / `300 binde her türde %1 yanlış alarmda` | `` `2b/` RF 300 bin satır (+ 9 Ekim 100 bin satır) `` / `300 bin satırda her türde %1 yanlış alarmda` |
| 466–468 | `satır` | `` `C:\ember2024\ember2024_net_test_ozellik.csv` (120.000 kayıt, 60K/60K, son 12 hafta) ve `...\ember2024_net_train_ozellik.csv` (520.000 kayıt, 260K/260K, ilk 52 hafta). `` | `` `C:\ember2024\ember2024_net_test_ozellik.csv` (120.000 satır / 59.953 eşsiz dosya: 30.000 zararlı + 29.953 zararsız, 60K/60K satır, son 12 hafta) ve `...\ember2024_net_train_ozellik.csv` (519.992 PE satırı / 259.996 eşsiz dosya: 129.997 zararlı + 129.999 zararsız, ham JSONL 520.000 satır, 260K/260K satır, ilk 52 hafta). `` |
| 562 | `eşsiz` + `satır` | `EMBER2024 .NET test "60K" dendi, gerçekte 120K).` | `EMBER2024 .NET test belgede "60K" dendi: bu 59.953 eşsiz dosya sayısıydı; her haftalık JSONL'da aynı sha256 iki kez yer aldığından satır sayısı 120K çıktı).` |

---

## 3. Site Deposu (`ahmtrntsdln.github.io`, `5a7ccb9`) Düzeltme Taslağı

### 3.1 `projects/chief-sef.html` ve `en/projects/chief-sef.html`

| Dosya:Satır | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---|---|---|
| `projects/chief-sef.html:54` | `test haftaları 52–63 (959.738 dosya) bu sabit eşiklerle bir kez ölçüldü:` | `test haftaları 52–63 (479.856 eşsiz dosya / 959.738 satır) bu sabit eşiklerle bir kez ölçüldü:` |
| `en/projects/chief-sef.html:54` | `test weeks 52–63 (959,738 files) were measured once with these fixed thresholds:` | `test weeks 52–63 (479,856 unique files / 959,738 rows) were measured once with these fixed thresholds:` |

### 3.2 `notes/net-kor-nokta.html` ve `en/notes/dotnet-blind-spot.html`

| Dosya:Satır | Mevcut Metin | Önerilen Düzeltme Taslağı |
|---|---|---|
| `notes/net-kor-nokta.html:38` | `eğitiminden altı yıl sonra çıkan 120.000 güncel .NET dosyasında sınadığımda` | `eğitiminden altı yıl sonra çıkan 59.953 eşsiz güncel .NET dosyasında (120.000 satır) sınadığımda` |
| `notes/net-kor-nokta.html:44` | `Belgesinde yaklaşık 60 bin dosya olduğu yazıyordu; dosyaları saydığımda gerçekte 120.000 çıktı.` | `Belgesinde yaklaşık 60 bin dosya olduğu yazıyordu; sonradan yaptığımız çiftleme denetiminde (İş 7) belgedeki sayının 59.953 eşsiz dosya sayısı olduğu, haftalık JSONL dosyalarında her sha256 kaydının iki kez yer alması nedeniyle satır sayısının 120.000 çıktığı anlaşıldı (nokta tahminleri değişmez).` |
| `notes/net-kor-nokta.html:52` | `EMBER2024'ün .NET eğitim kümesinin ilk 52 haftasından aldığım 100 bin dosyalık örneklemle eğittim` | `EMBER2024'ün .NET eğitim kümesinin ilk 52 haftasından aldığım 100 bin satırlık örneklemle (M2'de 90.330, M2d'de 74.542 eşsiz dosya) eğittim` |
| `en/notes/dotnet-blind-spot.html:38` | `when I tested it on 120,000 recent .NET files from 2024, six years after its training data` | `when I tested it on 59,953 unique recent .NET files (120,000 rows) from 2024, six years after its training data` |
| `en/notes/dotnet-blind-spot.html:44` | `Its documentation said about 60 thousand files; when I counted them, in practice there were 120,000.` | `Its documentation said about 60 thousand files; our subsequent duplication audit (Work Package 7) showed that 59,953 was the unique file count, whereas each sha256 record appeared twice in the weekly JSONL files, yielding 120,000 rows (point estimates are unchanged).` |
| `en/notes/dotnet-blind-spot.html:52` | `I trained it on a 100-thousand-file sample from the first 52 weeks of EMBER2024's .NET training set` | `I trained it on a 100-thousand-row sample (90,330 unique files in M2, 74,542 in M2d) from the first 52 weeks of EMBER2024's .NET training set` |

> **Not:** Taranan diğer 6 site dosyasında (`notes/zaman-ekseni.html`, `en/notes/temporal-split.html`, `index.html`, `en/index.html`, `notes/index.html`, `en/notes/index.html`) EMBER2024 `satır` sınıfında sayı yoktur; bu dosyalardaki sayılar `EMBER 2018` (çiftleme 0), `yerel`, `oran-yüzde` veya `ilgisiz` sınıfındadır.

---

## 4. `gumruk_memuru/sonuclar/` Altındaki Tablolarda Değişen Wilson Aralıkları ve Hüküm

Tam metin taramasından muaf olan ancak İş 7 (b)'de yeniden hesaplanan `3/`, `5/`, `6/` sonuç belgelerine eklenecek düzeltme notları:

1. **`gumruk_memuru/sonuclar/3/son_model_not.md` (Son model test_bir_kez, hafta 52–63):**
   - Test kümesi: `959.738` satır → **`479.856` eşsiz dosya** (`{2: 479.843, 4: 13}`).
   - EXE kaçan: `%17,749 [17,638–17,861] (80.120/451.402)` → **`%17,749 [17,592–17,907] (40.060/225.701)`**.
   - EXE YA: `%0,828 [0,780–0,879] (1.056/127.546)` → **`%0,828 [0,761–0,901] (528/63.770)`**.
   - DLL kaçan: `%19,524 [19,069–19,988] (5.582/28.590)` → **`%19,524 [18,883–20,182] (2.791/14.295)`**.
   - DLL YA: `%1,428 [1,390–1,468] (5.030/352.200)` → **`%1,428 [1,374–1,485] (2.515/176.090)`**.
   - AUC: genel `0,98651`, EXE `0,98373`, DLL `0,98439` (değişmedi).

2. **`gumruk_memuru/sonuclar/5/net_sonuc.md` (`net_olcum.csv` ve `esit_ya.log`):**
   - `A` kümesi `.NET` EXE kaçan: `%33,74 [32,14–35,38] (1.106/3.278)` → **`%33,74 [31,49–36,06] (553/1.639)`**; `.NET` EXE YA: `%2,88 [1,33–6,15] (6/208)` → **`%2,97 [1,02–8,37] (3/101)`**.
   - `A` kümesi `.NET` DLL kaçan: `%23,38 [19,00–28,41] (72/308)` → **`%23,38 [17,39–30,66] (36/154)`**; `.NET` DLL YA: `%0,95 [0,52–1,74] (10/1.054)` → **`%0,97 [0,41–2,24] (5/517)`**.
   - `B` kümesi (`Dot_Net_test`, `120.000` satır → **`59.953` eşsiz dosya**): tüm nokta tahminleri `Δ_max` içinde aynı, 8 hükmün 8'i de **hüküm aynı** (`ciftleme_b.csv` ve `ciftleme_b_hukum.csv`).

3. **`gumruk_memuru/sonuclar/6/uzman_native_sonuc.md` (`uzman_native.csv`):**
   - 12 hüküm hücresinin 11'i **hüküm aynı**, **1 hücrede HÜKÜM DEĞİŞTİ**:
     - **`H %1,05 | M2 (uzman, kestirmeli) vs native | EXE`:**
       - Çiftli (`n = 7.436` zararsız EXE satırı): M2 test YA `%1,48 [1,23–1,78] (110/7.436)` vs native `%0,89 [0,70–1,13] (66/7.436)` — Wilson aralıkları örtüşmediğinden (`1,23 > 1,13`) **`eşit yanlış alarm SAĞLANAMADI → hüküm yok`**.
       - Tekil (`n = 3.713` eşsiz zararsız EXE dosyası): M2 test YA `%1,48 [1,14–1,92] (55/3.713)` vs native `%0,89 [0,63–1,25] (33/3.713)` — `n` yarıya inince Wilson aralıkları genişleyerek `[1,14–1,25]` bandında örtüştü; kaçan M2 `%31,40 [30,86–31,96] (8.595/27.370)` vs native `%62,80 [62,23–63,37] (17.189/27.370)` olduğundan hüküm mekanik olarak **`UZMAN daha az kaçırıyor`** oldu. *(Not: Bu değişen hüküm aralık örtüşmesini eşitlik sayan kuraldan doğmuştur — M2 YA ≈ native'in 1,7 katı — uzman üstünlüğü kanıtı değildir; eski hükümler korunmuş, yalnız not eklenmiştir).*
