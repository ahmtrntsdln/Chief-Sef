# İş 4 ön kaydı - İmza ve bilinen dosya özeti (hash) filtresi: ölçülebilirlik, yük, risk

`FAZ1_KAPANIS.md` (dal `faz1/kapanis`, `ccb9c48`; Revizyon 2, 6, 7) İş 4 ve ölçüt 10. Bu dosya ölçümden ÖNCE yazıldı ve
commit'lendi (3 Kasım 2026, dal `olcum/is4-imza`, main `b34e1eb`'den). Ölçüm bir kez yapılır; veri, tanımlar, liste sürümü
ve kurallar sonuçtan sonra DEĞİŞMEZ. Bu pakette `tahmin_et.py` DEĞİŞMEZ, imza modele ÖZELLİK olarak KATILMAZ, hiçbir
filtre devreye alınmaz.

**Ön kayıttan önce yapılan, oran ve skor İÇERMEYEN yapı incelemeleri (3 Kasım):**

- **EMBER2024 alanları (Win64_test ve Dot_Net_test, ilk 3 / 1 kayıt; thrember 0.1.0 `features.py` okundu):**
  `datadirectories` listesinde isimle `SECURITY` (`name`, `size`, `virtual_address`; thrember `IMAGE_DIRECTORY_ENTRY_`
  önekini siler, başta isimsiz girdi var). Ayrıca `authenticode` grubu, 8 alan: `num_certs`, `self_signed`,
  `empty_program_name`, `no_countersigner`, `parse_error`, `chain_max_depth`, `latest_signing_time`, `signing_time_diff`
  (signify 0.7.1 `SignedPEFile` ile; zincir ve iptal DOĞRULANMAZ). Tam `sha256` alanı kayıtta var; Parquet / CSV'de yalnız
  ilk 12 hane (`Dosya_Adi`), imza alanları yok: ölçüm JSONL'den yapılır.
- **Yerel karşılık:** pefile `OPTIONAL_HEADER.DATA_DIRECTORY`, ad `IMAGE_DIRECTORY_ENTRY_SECURITY`. Bu dizinde
  `VirtualAddress` dosya ofsetidir, RVA değil; yalnız varlık için kullanılır.
- **Hazır Kural 1 girdisi:** `C:\ember2024\thrember_karsilastirma_50.jsonl` (15 Ekim; 50 yerel dosya, thrember çıktısı,
  `sha256`, `_yol`, `datadirectories`, `authenticode` var). İçindeki imza oranı bakılmadı.
- **Bilinen dosya listeleri (kaynak: NIST sayfaları, aşağıda):** NSRL RDSv3. Son tam sürüm 2026.03.1 (`RDS_2026.03.1_modern_minimal.zip`, 18 GB); sonraki delta 2026.06.1, 2026.09.1. Etiketler Mart / Haziran /
  Eylül / Aralık; tam sürüm yılda bir görünüyor (bu çıkarım, NIST takvim yazmıyor). RDSv3 SSS'si minimal veritabanının
  tekil SHA-256, SHA-1, MD5 içerdiğini söylüyor; **sütun adı ve şema henüz doğrulanmadı (K6).**
- **NSRL "bilinen İYİ" listesi DEĞİLDİR:** NIST "bilinen kötü / zararlı" kararı vermediğini açıkça yazıyor; liste "bilinen
  yazılım" listesidir. Kalıcı kuraldaki "bilinen iyi liste" koşulunu kendiliğinden sağlamaz; bu yüzden risk ölçülür (M6).

Kaynaklar: [NSRL indirme](https://www.nist.gov/itl/csd/secure-systems-and-applications/national-software-reference-library-nsrl/nsrl-download-0),
[2026.03.1 README](https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2026.03.1/README.txt),
[2026.09.1 README](https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/rds_2026.09.1/README.txt),
[RDSv3 SSS](https://s3.amazonaws.com/rds.nsrl.nist.gov/RDS/RDSv3_Docs/RDSv3_FAQs.pdf).

## 1. Soru ve sabitler

**Sorular:** (1) İmza bloğunun varlığı iki tarafta aynı ölçülebiliyor mu (Kural 1)? (2) Zararlı ve zararsızlarda ne sıklıkta
var (yük ve risk)? (3) Zararlı .NET'in ne kadarı düşük skorda kalıyor (kalıcı kuralın kanıtı)? (4) Yerel .NET'in ne kadarı
bilinen dosya listesiyle kapsanabilir ve liste zararlı içeriyor mu? (5) Hash filtresi uygulansın mı (ölçüt 10)?

- **İmza bloğu var (birincil):** `SECURITY` dizini İSİMLE bulunur, `size` > 0 VE `virtual_address` > 0. Dizin yoksa "yok" sayılır ve
  ayrıca sayılır (Kural 5). **İkincil:** `authenticode.num_certs` > 0; `parse_error` = 1 ayrı sayılır.
  Varlık ≠ geçerli imza: bu paketin hiçbir cümlesi "imzalı" ya da "güvenilir" demez, "imza bloğu var" der.
- **Veri (hepsi tam `sha256` ile eşsiz dosya, ilk kopya; `general.is_pe` = 0 atlanır; ölçüt 12):** zip'lerden açmadan
  (`C:\ember2024\zip`, `Dot_Net_*.zip`). Beklenen eşsiz: Win32 + Win64 train 2.079.225 (hafta 0-51; is_pe = 0 sonrası K2'de doğrulanır),
  test 479.856 (hafta 52-63); Dot_Net train 259.996, test 59.953.
- **Gruplar:** A = Win32 / Win64 test, `NET_mi` = 1 (2.411 eşsiz). Native .NET dışı = aynı, `NET_mi` = 0. Dot_Net test. Eğitim
  haftaları karşılıkları. Tür `dll_mi` (`ember_zararli_cikar`), `NET_mi` CLR kuralıyla (iki taraf aynı kod).
- **Skor:** kayıtlı son model, `tahmin_et.model_yukle()` (SHA-256, Kural 10); üretim eşikleri EXE 0,70 / DLL 0,61, AYARLANMAZ.
- **Yerel küme:** dondurulmuş 5.635 satır (sha256 `5d96007d…`), .NET 3.471. Özellikler YENİDEN ÖLÇÜLMEZ, küme değişmez. Yol bilgisi
  `sef_dogrulama_dz80_isimli.csv`'den (repoda yok).
- **Bilinen dosya listesi:** NSRL RDSv3 `RDS_2026.03.1_modern_minimal.zip`, proje dışına (`C:\ember2024\nsrl`), `.sha` dosyasıyla
  doğrulanır. Delta'lar birincil ölçüme girmez. **Karşılaştırma yalnız yerel:** hash'ler hiçbir dış servise GÖNDERİLMEZ. Bu yüzden
  CIRCL hashlookup kullanılmaz (kurulu yazılımı üçüncü tarafa açar; toplu SHA-256 uç noktası da doğrulanamadı). Yerel dosya özetleri ve
  yolları repoya girmez; repoda yalnız toplu sayılar.

## 2. Ölçüm ve kontroller

Geçit tutmazsa ilgili bölüm DURUR, "hüküm yok: geçit" yazılır; diğer bölümler sürer.

| # | Kontrol | Geçme koşulu |
|---|---|---|
| K1 | Kural 1, imza varlığı | 50 kayıtlık dosyada, sha256'sı bugünkü dosyayla aynı olanlarda pefile SECURITY (size, VA) = thrember kaydı, birebir. Değişen / silinen sayılır. Karşılaştırılan dosyalarda blok var ≥ 5 VE yok ≥ 5; değilse "Kural 1 gösterilemedi, kanıt yetersiz" |
| K2 | Eşsiz sayılar | dört kümede eşsiz sayılar beklenenle aynı; A 2.411 ve hücreler 101 / 517 / 1.639 / 154 |
| K3 | Kopyalar | aynı sha'nın kopyalarında `label`, SECURITY (size, VA) ve `authenticode` birebir; aykırı sayı yazılır, > 0 ise bölüm durur |
| K4 | Skor | tekil Dot_Net_test üretim eşiği kaçan ve YA k/n, `sonuclar/8/ciftleme_b.csv` B satırlarıyla birebir; model SHA-256 tutuyor |
| K5 | Yerel küme | sha256 = meta; isimli kopya 94 ortak sütunda satır satır aynı; .NET 3.471 (EXE 49, DLL 3.422) |
| K6 | Liste | zip `.sha` ile tutuyor; SQLite şemasında SHA-256 sütunu İSİMLE bulunuyor; değerler 64 hane onaltılı (büyük / küçük harf normalize); `hash_counts.txt` ile sayı tutarlı; listeden rastgele 3 değer ölçümdeki aynı arama yoluyla bulunuyor (arama kodu sınaması) |

**M1 Tutarlılık (betimleyici):** EMBER'de SECURITY var ama `num_certs` = 0 ve tersi; `parse_error`; dizin hiç olmayan kayıt sayısı.

**M2 İmza bloğu varlığı (Revizyon 2):** Win32 / Win64, EXE ve DLL ayrı, zararlı ve zararsız, eğitim ve test haftaları, k/n, %, Wilson %95.
Birincil ve ikincil tanım.

**M3 .NET yük ve risk (Revizyon 6), tek tablo:** A ve Dot_Net (eğitim, test), EXE / DLL, zararsız (yük) ve zararlı (risk), Wilson.
Yerel küme YENİDEN TARANMAZ; yerel imza oranı M5'in okuduğu baytlardan betimleyici olarak verilir, eskiyen dosya sayısıyla.

**M4 Zararlı .NET skor dağılımı (Revizyon 7, kalıcı kuralın kanıtı):** tekil Dot_Net_test zararlı .NET, native skor, EXE / DLL ayrı:
≤ 0,2; (0,2, 0,5]; (0,5, eşik]; > eşik. k/n, Wilson. Karşılaştırma için aynı bantlar: Dot_Net_test zararsız, A zararlı ve zararsız; yerel
.NET değerleri `yerel_belirsiz.log`'dan (`faz1/kapanis`, `9f7acf4`; %85,82 ≤ 0,2).

**M5 Yerel .NET kapsama (Revizyon 7):** her .NET satırının yolu okunur ve SHA-256 alınır (özellik ölçülmez). Üç sınıf: **yok** (dosya
silinmiş); **değişmiş** (boyut CSV'den farklı YA DA son değişiklik 9 Ekim 2026'dan sonra; ölçülen dosya olduğu söylenemez); **ölçülebilir**.
Sayılar: ölçülebilir içinde listede olan k/n, Wilson (birincil); k / 3.471 (silinen ve değişen "yok" sayılır; alt sınır); EXE ve DLL
ayrı; üst klasöre göre "Microsoft" (`Program Files\dotnet`, `Program Files\Microsoft*` ve `Windows*`, `Reference Assemblies`,
`System32` / `SysWOW64`) ve diğer. Aynı sayılar .NET dışı 2.164 için betimleyici. Aynı içerikli satırlar birden çok yolda olabilir: eşsiz
SHA-256 sayısı yazılır, kapsama eşsiz dosyayla da verilir. Birincil kapsama satır (yol) düzeyindedir, çünkü BELİRSİZ yükü dosya başınadır.

**M6 Listenin riski:** dört EMBER2024 kümesinin eşsiz tam sha256'ları liste ile: zararlı ∩ liste ve zararsız ∩ liste, k/n, Wilson,
A ve Dot_Net ayrı, tür ayrı. Eşleşen zararlılar için `family` ve `detection_ratio` dağılımı. Dosya baytı işlenmez; yalnız özet karşılaştırılır.

## 3. Yorum / karar kuralı

1. **İmza (Kural 1):** K1 geçerse "imza bloğu varlığı iki tarafta aynı ölçülüyor"; "aynı ölçülüyor" yalnız bloğun varlığı içindir,
   `authenticode` alanları için değil.
2. **İmza filtresi kararı önceden sabit: UYGULANMAZ.** Kalıcı kural (Revizyon 7) imza varlığının .NET'te "temiz" vermesini yasaklıyor; M2-M3
   hangi sonucu verirse versin bu değişmez. Oranlar yük ve risk diye raporlanır, "ayırt ediciliği yüksek" denmez.
3. **Kalıcı kuralın kanıtı (M4):** rapor cümlesi "Dot_Net_test zararlı .NET'in %X'i ≤ 0,2 bandında", hüküm değil. X'in büyüklüğü kuralı
   kaldırmaz ya da zayıflatmaz.
4. **Hash filtresi önerisi (öneri mekanik, karar kullanıcının):** "UYGULANABİLİR" ancak üçü birden sağlanırsa:
   (a) K5 ve K6 geçti; (b) **risk:** M6'da zararlı ∩ liste = 0 (dört küme); (c) **fayda:** M5 birincil kapsamanın Wilson alt sınırı ≥ %25 (yerel
   .NET BELİRSİZ yükünün en az dörtte birini kaldıracak büyüklük; eşik çözümleyicinin seçimi, sonuçtan önce). Aksi halde:
   - (b) tutmazsa "UYGULANMAMALI: liste zararlı içeriyor" (k ve aile yazılır). Bir eşleşme bile, kuralın koruduğu hatanın ta kendisidir.
   - (c) tutmazsa "UYGULANMAMALI: fayda yetersiz".
5. **Sonuç ne olursa olsun:** filtre bu pakette eklenmez, `tahmin_et.py` değişmez. Kullanıcı "uygula" derse ayrı iş: liste sürümü ve hash kimliği
   (Kural 10 benzeri), güncelleme yöntemi, ölçüt 3 ve 9'un güncellenmesi. Ölçüt 10 kararla kapanır: "uygulama" da geçerli bir karardır.

## 4. Hüküm verilmeyen durumlar

- K1 kanıt yetersizse (blok var < 5 ya da yok < 5): kural 1 için "hüküm yok"; M2-M3 EMBER içi sayı olarak yine raporlanır, yerel tarafla
  karşılaştırma cümlesi yazılmaz.
- K2-K4 tutmadı → ilgili bölümde "hüküm yok: geçit", sayı sonuç olarak raporlanmaz.
- K5 ya da K6 tutmadı (liste indirilemedi, SHA-256 sütunu yok) → kural 4 için "hüküm yok: liste ölçülemedi"; ölçüt 10 için karar kullanıcıya
  gerekçesiyle sorulur, varsayılan "uygulama".
- Hücre n < 30 → oran yorumlanmaz, yalnız k/n. M5 ölçülebilir n < 30 → "hüküm yok: yerel küme büyük ölçüde değişmiş".
- Zararlı ∩ liste = 0, listenin zararsız olduğunu göstermez: yalnız EMBER2024 örneğinde eşleşme yok demektir (Wilson üst sınırı yazılır).

## Sınırlar (sonuçtan önce)

- **"Bilinen" ≠ "iyi":** NSRL yazılım koleksiyonudur, zararlılık kararı vermez. Listede çift kullanımlı araçlar olabilir.
- **EMBER etiketi kusursuz değildir:** M6'daki eşleşen bir "zararlı" etiket hatası olabilir; kural yine de "uygulanmamalı" der (fail-closed).
  Ayrıntı ailelerle raporlanır, sonuç sonradan yorumla değiştirilmez.
- **Zaman:** liste EMBER örneklerinden (2023-2024) sonra. Yerel dosyalar liste tarihinden yeni olabilir; kapsama güncelleme gecikmesi nedeniyle
  düşük çıkabilir. Yerel küme 9 Ekim'de donduruldu ve eskiyor (2(a), `sonuclar/4/`): silinen ve değişen dosyalar kapsamayı belirsizleştirir.
- **Tek makine, kümeli:** yerel kümenin ~%61'i Microsoft klasörlerinde, iki üretici ~%35; kapsama başka makineye genellenmez. Wilson bu kümeliliği yok sayar.
- **Yerel küme zararlı içermez:** M5 yalnız yükü ölçer, riski değil; risk M6'da ve yalnız EMBER örneğinde.
- **Yalnız modern minimal:** legacy, Android, iOS dışarıda. Delta'lar dışarıda; uygulama yöntemi README'de yok, ölçülen sürüm 2026.03.1.
- **Maliyet:** 18 GB indirme, tüm zip'lerden (21,9 GB + Dot_Net) akışla okuma. Uzun işler %/ETA ve `--devam` ile (Çalışma Alışkanlıkları).
  İndirme ölçüm adımında, kullanıcı onayından sonra yapılır.
