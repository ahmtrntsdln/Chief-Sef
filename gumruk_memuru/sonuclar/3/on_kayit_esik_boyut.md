# Ön kayıt: eşik doğrulama dilimi ve son model boyutu (RF E3)

Bu dosya aşağıdaki ölçümlerden ÖNCE yazıldı ve commit'lendi. Karar (RF E3) kullanıcınındır;
`karar_olcutleri.md` DEĞİŞMEZ. Sonradan ayar (ör. `min_samples_leaf`) EKLENMEZ; gerekirse ayrı
ön kayıtlı deney olur.

## 1. Eşik: doğrulama dilimi, test bir kez

- 2c'deki (`karar_tablosu.md`) "%1 noktası" TEST kümesinden seçilmişti (ROC çalışma noktası).
  Bu, iki modeli aynı yanlış alarmda karşılaştırmak için geçerli ama üretim eşiği değil ve
  test bilgisini kullanıyor. Burada yeniden ölçülür.
- Doğrulama dilimi: eğitim haftalarının son 4'ü (hafta 48-51), İKİ SINIF BİRDEN: 319.924 kayıt
  (%7,7). Eğitim havuzu: hafta 0-47 (3.838.526). Test: hafta 52-63 (959.738), dokunulmaz.
- Neden iki sınıf birden: yalnız zararsızları ayırıp zararlıları eğitimde tutmak, iki sınıfı
  eğitimde farklı zaman dilimlerinden getirir (Kural 2'nin yasakladığı türden kaynak farkı).
- τ_t (t ∈ {EXE, DLL}) = doğrulama dilimindeki t türü ZARARSIZ skorlarının %99'luk dilimi
  (`np.quantile(p, 0.99, method="higher")`). Model ve tohum başına sabitlenir; test ve yerel
  küme bu SABİT eşikle bir kez ölçülür. Testte gerçekleşen yanlış alarm raporlanır (%1 olmak
  zorunda değil: zaman kayması).
- Yeniden ölçüm (bilgi + kontrol): RF ve LightGBM × E2 ve E3 × 300 bin × 5 tohum, havuzdan
  eğitim, doğrulamadan eşik, test bir kez. Ölçütlerin mekanik sonucu RF E3'ten farklı çıkarsa
  açıkça raporlanır; karar kullanıcıya döner.

## 2. Son boyut kuralı

- 522.200 bu tasarımda KURULAMAZ: hafta 48-51 eğitimden çıkınca havuzdaki zararlı DLL 120.806.
  Havuzda tip içi dengeli en büyük boyut 4 × 120.806 = **483.224** ("tamamı"). Kural, ön kayıtlı
  522.200 yerine bu boyutla uygulanır (aynı anlam: yerine koymadan en büyük E3).
- Karşılaştırma: RF E3 300.000 ve RF E3 483.224, İKİSİ DE tohum 42, 1, 2 (3 tohum), aynı
  havuz, eşik doğrulamadan, test bir kez.
- Ölçü: DLL'de kaçan zararlı % (test, τ_DLL'de) - karar_olcutleri.md'nin ana ölçütü.
- kazanç = ort(300K) − ort(483.224) (pozitif = büyük model daha az kaçırıyor).
  s = max(std_300K, std_483K), std = 3 tohumun örneklem standart sapması (ddof=1).
- KURAL: kazanç < s ise son boyut **300.000**; değilse **483.224**.
- Kurala girmeyen ama ikisi için de kaydedilen: model dosya boyutu (joblib, sıkıştırmasız),
  bellek (yüklemeden sonra süreç RSS artışı ve ağaç dizilerinin bayt toplamı), dosya başına
  tahmin süresi (tek satır `predict_proba`, `n_jobs=1`, 1000 çağrının medyanı, ısınmadan sonra;
  özellik çıkarma HARİÇ).

## 3. Son model

- Seçilen boyutta RF E3, tohum 42, havuzdan (hafta 0-47) eğitilir. Hafta 48-51 eğitime
  EKLENMEZ: eşikler modelin görmediği veriden gelmeli.
- Yanına meta veri: özellik sırası, sürümler, tohum, boyut, eğitim verisi özeti (haftalar,
  hücre sayıları, Parquet özetleri), eşikler (τ_EXE, τ_DLL), testte bir kez ölçülen değerler,
  tarih, kod commit'i.
