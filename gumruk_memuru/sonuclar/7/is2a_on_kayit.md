# İş 2(a) ön kaydı - M2d'nin yerel meşru .NET dosyalarında yanlış alarmı

`FAZ1_KAPANIS.md` (dal `faz1/kapanis`) İş 2 (a). Bu dosya ölçümden ÖNCE yazıldı ve commit'lendi
(30 Ekim 2026). Ölçüm bir kez yapılır; model, eşik, veri ve kurallar sonuçtan sonra DEĞİŞMEZ.
Uzman model `tahmin_et.py`'ye BAĞLANMAZ; bu ölçüm bağlama kararının girdisidir, kararın kendisi değil.

Kullanıcı kararları (30 Ekim, ölçümden önce): iş dış repoda `olcum/is2-uzman` dalında; yerel setteki
.NET EXE sayısı (49) %1 düzeyindeki hedefi ayırt edemediği için EXE satırı raporlanır ama hüküm
verilmez (madde 4); daha büyük .NET EXE ölçümü ayrı iş olarak not edilir, bu pakette yapılmaz.

## 1. Soru ve sabitler

**Soru:** .NET uzman modeli M2d, bu makinedeki meşru .NET dosyalarında ne kadar yanlış alarm veriyor;
aynı dosyalarda, aynı yöntemle (hafta 48-51 doğrulama dilimi, tür başına) seçilmiş eşiklerde native
modelden farklı mı? Şimdiye kadar M2d yalnız Dot_Net_test'te (`sonuclar/6/`) ve eski bir 500+500
örneklemde (farklı model: hafta 0-51; os.walk sırasıyla ilk 500, rastgele değil) ölçüldü.

- **M2d:** `sonuclar/6/uzman_native.py`'deki model, AYNI tarifle yeniden eğitilir: Dot_Net_train
  hafta 0-47 havuzu, (DLL_mi × Etiket) hücrelerinin her birinden 24.104 (toplam 96.416),
  `sample(random_state=42)`; `net_model.rf()` (RF 100 ağaç, random_state=42); 87 özellik
  (`net_model.DIZGELI_TIPLI`). `n_jobs` yalnız hız.
- **Native:** kayıtlı son model, `tahmin_et.model_yukle()` (SHA-256 doğrulamalı, Kural 10).
- **Eşikler (AYARLANMAZ; `sonuclar/6/uzman_native.csv`, hafta 48-51 doğrulama diliminden):**

  | Hedef YA (H) | M2d EXE / DLL | native EXE / DLL |
  |---|---|---|
  | %0,45 | 0,86 / 0,69 | 0,83 / 0,69 |
  | %1,05 | 0,76 / 0,59 | 0,79 / 0,60 |

  İkincil (yalnız betimleyici): M2d eşik 0,5 (eski 500+500 ölçümüyle aynı çalışma noktası, ama
  model ve örneklem farklı); native üretim eşikleri EXE 0,70 / DLL 0,61 (yalnız geçit K4).
- **Alarm** = skor > eşik (`uzman_native.py` ile aynı tanım). Tür `DLL_mi`'ye göre.
- **Veri:** dondurulmuş yerel set `sef_yerel_dogrulama_5635.csv` (sha256 `5d96007d…262987`,
  YENİDEN TARANMAZ), `NET_mi` = 1 satırları: 3.471 (EXE 49, DLL 3.422; Karma_Mod 7). Hepsi
  zararsız: yalnız yanlış alarm ölçülür, kaçan ölçülemez.
- **Güven aralığı:** Wilson %95 (`ortak_deney.wilson`). **Eşleştirilmiş karşılaştırma:** McNemar
  kesin binom testi, iki yönlü (`sonuclar/2c/karar_tablosu.mcnemar`; native seçiminde kullanılan aynı
  fonksiyon), α = 0,05; b = yalnız M2d alarm, c = yalnız native alarm.

## 2. Ölçüm ve kontroller

Her geçit tutmazsa ölçüm DURUR; log saklanır, sonuç tablosu yazılmaz.

| # | Kontrol | Geçme koşulu |
|---|---|---|
| K1 | Yerel set kimliği | sha256 = meta'daki `yerel_dogrulama_seti.sha256` |
| K2 | Yerel .NET satırları | `NET_mi`=1: 3.471, EXE 49, DLL 3.422; 87 M2d sütunu var, eksik değer yok |
| K3 | M2d geçidi | yeniden eğitilen M2d'nin doğrulama diliminden `esit_ya.esik_bul` ile seçtiği eşikler yukarıdaki tabloyla AYNI; Dot_Net_test'te M2d'nin 6 satırında (2 H × EXE/DLL/hepsi) `kacan_k` ve `YA_k` `uzman_native.csv` ile birebir |
| K4 | Native geçidi | aynı yolla native eşikleri tabloyla AYNI ve Dot_Net_test'te 6 satırda `kacan_k`/`YA_k` csv ile birebir; yerel .NET'te üretim eşikleriyle alarm 1/3.471 (`sonuclar/5/net_sonuc.md`, C) |

**Ölçüm** (geçitlerden sonra, bir kez): her H × model × tür (EXE, DLL, hepsi) için yerel .NET
yanlış alarm k/n, % ve Wilson; her H × tür (EXE, DLL) için McNemar (b, c, p). Betimleyici: M2d'nin
aynı eşikteki Dot_Net_test YA'sı (csv'den) yan yana; alarm veren dosyaların Karma_Mod dağılımı;
M2d eşik 0,5'te yerel YA.

## 3. Yorum / karar kuralı

1. **M2d mutlak (tür ve H başına):** yerel YA'nın Wilson üst sınırı H'nin altındaysa "M2d yerel
   meşru .NET <tür> dosyalarında hedefin altında yanlış alarm veriyor"; alt sınırı H'nin üstündeyse
   "hedefin üstünde"; aralık H'yi içeriyorsa "hedefle farkı gösterilemedi".
2. **M2d - native (eşleştirilmiş, tür ve H başına):** p < 0,05 ve b > c ise "M2d yerelde native'den
   anlamlı olarak daha çok yanlış alarm veriyor"; p < 0,05 ve b < c ise "daha az"; aksi halde
   "fark gösterilemedi" ("eşit" DENMEZ).
3. Eşik 0,5 ve Dot_Net_test yan yana sütunu yalnız betimleyicidir; hüküm üretmez.
4. Sonuç ne olursa olsun uzman bağlanmaz; `tahmin_et.py`'deki .NET kuralı (eşik altı BELİRSİZ)
   değişmez. Sonuç İş 2 karar notuna girer; karar kullanıcınındır.

## 4. Hüküm verilmeyen durumlar

- K1-K4'ten biri tutmadı → hiçbir sayı sonuç olarak raporlanmaz ("hüküm yok: geçit").
- Hücre n < 30 → oran yorumlanmaz, yalnız k/n.
- **Çözünürlük:** 0 alarmda bile Wilson üst sınırı H'ye eşit ya da büyükse (wilson(0, n) üst ≥ H)
  kural 1 uygulanmaz: "hüküm yok: çözünürlük yetersiz". Önceden hesap: EXE n = 49 → üst %7,27 > H
  (her iki H) → EXE'de kural 1 için hüküm yok; DLL n = 3.422 → üst %0,11 < %0,45 → uygulanır.
- **McNemar gücü:** b + c < 6 ise iki yönlü kesin testte en küçük olası p ≥ 0,05 → kural 2 için
  "hüküm yok: uyuşmayan çift sayısı yetersiz" (aralık örtüşmesi "eşit" diye okunmaz).

## Sınırlar (sonuçtan önce yazıldı)

- **Kümelilik:** set seed 42 ile 64.263 yerel PE'den (System32 + Program Files ×2) örneklendi;
  .NET dosyalarının çoğu aynı paketlerden (ör. dotnet çalışma zamanı) gelir. Wilson ve McNemar
  bağımsızlık varsayar → gerçek belirsizlik raporlanan aralıktan geniş.
- **Asimetri:** native model seçilirken bu setin yerel YA'sı ölçüttü (`karar_olcutleri.md`, McNemar);
  M2d bu seti hiç görmedi. Karşılaştırma native lehine hafif yanlı olabilir.
- **Kapsam:** tek makine, Ekim 2026 kurulumu (set eskiyor, `sonuclar/4/yerel_set.md`); EXE 49
  dosya. Sonuç "meşru .NET dosyaları" geneline genellenmez.
- Kaçan zararlı bu ölçümde YOK (yerel zararlı yok); M2d'nin kaçanı İş 2(b) ve Dot_Net_test'ten gelir.
