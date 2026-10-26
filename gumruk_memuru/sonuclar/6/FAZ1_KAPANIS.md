# Faz 1 kapanışı (native model) - ölçütler, kapsam, iş paketleri

Bu dosya iş paketlerinin sonuçlarından ÖNCE yazıldı ve commit'lendi (26 Ekim 2026). Ölçütler
sonradan gevşetilmez; değişiklik gerekirse ayrı commit'le, gerekçesiyle ve kullanıcı onayıyla yapılır.
Her iş paketi: ön kayıt commit'i → iş → sonuç commit'i (geçti / kaldı tablosu) → DUR (kullanıcı onayı).
Hiçbir paket kendi başına main'e almaz; main'e alma ve site yayını yalnız İş 1 ve İş 5'te, onayla.

## Kapanış ölçütleri

Faz 1, aşağıdaki altı ölçütün HEPSİ origin/main'de ve canlı sitede sağlandığında kapanır.

1. **Yeniden üretilebilirlik:** origin/main boş klasöre temiz klonlanır, yeni venv `requirements.txt`
   (+ dev) ile kurulur: test paketinin tamamı geçer (gcc ile, atlanan yok); Faz 1 yeniden üretimi
   %90.1 ve 197/5700; `tahmin_et.py` modelsiz anlaşılır hata, doğru hash'le çalışır, bir baytı
   değişmiş modeli reddeder; uçtan uca 20/20 (86/86).
2. **Raporlanan sayılar = ölçülen sayılar:** README'deki native model sayıları ölçüm dosyalarıyla
   (`model_native_meta.json`, `sonuclar/5/`, `sonuclar/6/`) aynı; zamansal bölme, doğrulamadan
   seçilen eşik, %50 zararlı uyarısı, DLL yanlış alarmının hedefi aşması, yerel setin eskimesi ve
   .NET karışımı yazılı. Sitedeki her rakam README'de var (betik), TR = EN.
3. **.NET güvenli davranış:** `tahmin_et.py` .NET dosyasına eşik altında asla "zararsız" demez
   (BELİRSİZ); çıkış kodları 0 temiz / 1 hata / 2 BELİRSİZ / 3 ZARARLI / 4 OLASI ZARARLI, testli;
   toplu kullanımda BELİRSİZ hata sayılmaz, ayrı sayılır.
4. **.NET ölçümleri kayıtlı:** native modelin .NET ölçümü (`sonuclar/5/`) ve uzman (M2, M2d) vs
   native eşit yanlış alarm karşılaştırması (`sonuclar/6/`) ön kayıtlarıyla main'de; uzman modelin
   bağlanıp bağlanmayacağı kararı ve gerekçesi yazılı.
5. **Yayın tutarlı:** canlı site commit'le bayt bayt aynı; tarihli notlar silinmeden "Güncelleme"
   satırıyla düzeltilmiş; paylaşım kartları güncel etiketli.
6. **Açık işler açıkça devredildi:** kapsam dışı listesi ve Faz 2'ye devredilenler (Linux'ta eşik
   sınır testi, UBSan, CI) README / CLAUDE.md'de; GELISIM_SURECI.md'de Faz 1 kapanış bölümü; main
   üzerinde `faz1-kapanis` etiketi.

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
- **İş 1 - Main'e alım (kullanıcı onayıyla).** `belge/yerel-karisim`, `olcum/uzman-native`,
  `ozellik/net-belirsiz` sırayla `--no-ff`; her birinden sonra test paketi ve 20/20; force yok.
  BİTTİ: origin/main üç dalı içerir, her adımda testler geçti. → ölçüt 2, 3, 4 (kısmen).
- **İş 2 - Uzman model kararı.** Ön kayıtlı karar ölçütü (EXE'de gösterilen kazanç, DLL'de eşit
  yanlış alarmda yeniden ölçüm); karar "bağla" ise M2d ayrı model dosyası + meta + SHA-256 (Kural
  10), `NET_mi`'ye göre yönlendirme, doğrulama diliminden eşik, testler, 20/20; "bağlama" ise
  gerekçe. BİTTİ: kararın kendisi ve dayanağı main'de. → ölçüt 4.
- **İş 3 - Temiz klon doğrulaması (son main üzerinde).** Ölçüt 1'in tüm maddeleri + `git ls-files`
  içinde model / Parquet / dz80 / yerel set yok. BİTTİ: tüm satırlar GEÇTİ. → ölçüt 1.
- **İş 4 - Belgeler.** GELISIM_SURECI.md Faz 1 kapanış bölümü; CLAUDE.md ve README durum satırları;
  kapsam dışı + Faz 2 devir listesi; "DOĞRULANMADI" kalan her yer ya ölçülmüş ya devredilmiş.
  BİTTİ: kullanıcı belgelerin son halini onayladı. → ölçüt 2, 6.
- **İş 5 - Yayın ve etiket (kullanıcı onayıyla).** Site gönderimi, canlı = commit (bayt), canlı
  rakamlar = README (betik), kartlar; main üzerinde `faz1-kapanis` etiketi. BİTTİ: canlı doğrulama
  GEÇTİ, etiket origin'de. → ölçüt 5, 6.
