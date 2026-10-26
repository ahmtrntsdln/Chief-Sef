# Chief-Sef
Machine learning-powered software-hardware security engine

> English: [README.md](README.md)

> Projenin gelişim sürecini ve alınan kararların gerekçelerini
> [GELISIM_SURECI.md](GELISIM_SURECI.md) dosyasında bulabilirsiniz.

## About Şef-Chief

This repository contains the initial version (prototype) of Şef-Chief, a machine learning-powered software and hardware security engine.

AI-Assisted Development: Developed with the support of Large Language Models (LLMs). The core project concept and direction belong entirely to me, while the coding phase was fully handled by Claude and Gemini.

Project Milestone: This serves as a functional prototype and represents a personal milestone as both my first-ever project and my first AI-supported venture.

---

# Sef Projesi

Yapay zeka destekli, donanimsal izolasyonlu siber guvenlik motoru.

## Faz 1: Konseptin Ispati - Gumruk Memuru

Ilk hedef: dosyalarin Shannon Entropisini olcup normal dosyalarla
sifrelenmis/paketlenmis (potansiyel supheli) dosyalari ayirt edebilen
basit bir statik analiz katmani kurmak.

- `gumruk_memuru/entropy.py` -> Entropi hesaplama modulu
- `gumruk_memuru/sef_sabitler.py` -> Ortak olcum sabitleri (KARA_LISTE, sihirli
  imzalar, ordinal deseni, CLR dizin adlari). Zararli ve zararsiz taraf ayni
  olcumle uretilmeli; sabitler tek yerde durunca biri degisip digeri eski
  kalamaz.
- `gumruk_memuru/sef_ayarlar.py` -> Makineye ozel yollar ve veri dosyasi adlari.
  Olcum sabitlerinden ayri tutuldu: yol degistirmek hicbir sayiyi
  degistirmez, sabit degistirmek tum veriyi yeniden uretmeyi gerektirir.
- `gumruk_memuru/Chief_1.2.py` -> Tam statik analiz motoru (magic byte, bolum-bazli entropi, IAT/API)
- `gumruk_memuru/ember_zararli_cikar.py`, `ember_zararsiz_cikar.py` -> EMBER'den gercek veri cikarma
- `gumruk_memuru/toplu_tarama.py` -> Bu makinedeki dosyalari tarama (dis dogrulama seti)
- `gumruk_memuru/rf_egit_gercek.py` -> Egitim, dis dogrulama ve sinsi ornek testleri;
  ana modeli `model.pkl` olarak kaydeder (repo'da yok: ~10 sn'de ayni model
  yeniden uretilir, pickle da sklearn surumune bagli)
- `gumruk_memuru/tahmin_et.py` -> Native modelle tek dosya tahmini (asagida
  "Native model"): `python tahmin_et.py <dosya>`. Ozellikler dis dogrulamayla
  ayni modulden (`gumruk_memuru/ozellik_cikar.py`); model yalnizca SHA-256'si
  repodaki meta veriyle (`gumruk_memuru/model_native_meta.json`) tutarsa yuklenir.
- `gumruk_memuru/model_karsilastir.py` -> RF vs LightGBM ve kalibrasyon karsilastirmasi

Kurulum: `pip install -r requirements.txt` (model karsilastirmasi icin
`requirements-experimental.txt`). Veri klasorleri farkliysa
`gumruk_memuru/sef_ayarlar.py`'yi duzenle.

Testler: `pip install -r requirements-dev.txt` ve repo kokunden
`python -m pytest tests`. `tests/test_olcum_tutarliligi.py`, zararli (EMBER
JSON) ve zararsiz (pefile) tarafin ayni dosyayi ayni sayilara cevirdigini
kontrol eder. Bu projede en pahali hatalar model hatasi degil olcum
farkiydi: iki taraf farkli olculunce model zararliligi degil olcum farkini
ogreniyor. `tests/test_esik_sinir.py` + `tests/esik_sinir.c`: esik
karsilastirmasi icin Faz 2'ye hazirlik olarak yazilmis sinir-deger
regresyon testi (bkz. yol haritasi); gcc/clang yoksa C kismi atlanir.

## Faz 1 Sonuclari

Model: Random Forest, 5 ozellik (boyut, sifir orani, ortalama bolum
entropisi, toplam API, supheli API). Egitim: EMBER 2018'den 5700 zararli +
5700 zararsiz gercek PE dosyasi.

| Olcum | Sonuc |
|---|---|
| EMBER test dogrulugu: ayni donem (Kasim 2018 icinde 80/20) | %90.1 |
| EMBER test dogrulugu: zamansal bolme (Ocak-Ekim egitim -> Kasim-Aralik test) | %83.8 (AUC 0.920) |
| EMBER icinde yanlis alarm / kacan zararli (ayni donem) | %8.1 / %11.7 |
| Bu makinedeki 5700 gercek zararsiz PE'de yanlis alarm (egitimde hic gorulmedi) | %3.5 |
| En onemli ozellikler | Toplam_API 0.30, Boyut 0.25, Entropi 0.24, Sifir orani 0.18 |
| Bilinen sinirlama | .NET zararlilarina neredeyse kor: guncel (2024) .NET zararlilarinin %93'u kaciyor (bkz. CLAUDE.md) |

Gercekci sayi zamansal olan: train ve test ayni aydan gelince ayni
kampanyalar iki tarafta da bulunuyor ve skor yapay olarak kolaylasiyor
(%90.1 -> %83.8). Ayrintilar ve deneysel duzeltmeler (.NET uzman modeli,
dizge ozellikleri): CLAUDE.md.

%90 bilincli olarak %99'dan daha guvenilir bir sonuc: onceki %99.9 (sentetik
veri) ve %97 (zararsiz verinin tek makineden gelmesi) sonuclari, modelin
zararli davranisi degil veri kaynaklari arasindaki farki ogrendigini
gosteriyordu. Ayrintilar: [GELISIM_SURECI.md](GELISIM_SURECI.md).

Model karsilastirmasi (5 katli CV): Random Forest (AUC 0.963) ayarsiz
LightGBM'i (0.952) geciyor. Bu sonuc 5 ozellige ozgu; ozellik sayisi
artinca karsilastirma tekrarlanacak.

## Native model (EMBER2024, Ekim 2026)

2018 verisiyle egitilen Faz 1 modeli 2024 dosyalarinda cokuyor (AUC 0.663).
Yerine EMBER2024 Win32/Win64 ile egitilen, 86 ozellikli (5 temel + 80 dizge +
DLL bayragi) Random Forest geldi: 483.224 egitim dosyasi, her dosya turunun
ICINDE 50/50 orneklenmis. Neden: veri setinde zararsizlarin cogu DLL,
zararlilarin cok azi; aksi halde model "DLL ise zararsiz" demeyi ogreniyor.
Karar olcutleri hicbir sonuca bakilmadan yazilip commit'lendi
(`gumruk_memuru/sonuclar/`).

Esikler egitimden ayrilan 48-51. haftalardan secildi (her turde %1 yanlis
alarm); test haftalari 52-63 (959.738 dosya) bu sabit esiklerle bir kez olculdu:

| Dosya turu | Kacan zararli | EMBER2024 zararsizlarinda yanlis alarm |
|---|---|---|
| EXE | %17.7 | %0.83 |
| DLL | %19.5 | %1.43 |

Genel test AUC 0.9865. Bu makinedeki 5.635 gercek zararsiz dosyada yanlis
alarm: EXE %0.25, DLL %0.21.

Bu sayilar nasil okunmali:
- **Test dosyalarinin %50'si zararli.** EMBER2024 haftalik 50/50 orneklenmis;
  gercek kullanimda zararli cok daha nadir, bu yuzden bir skorun arkasindaki
  gercek olasilik daha dusuk, alarmlarin yanlis olan payi daha yuksektir.
- **DLL yanlis alarmi %1 hedefini asiyor** (%1.43). Esik 48-51. haftalarda
  ayarlandi. Olasi neden zaman kaymasi: test haftalarinda zararsiz DLL kitlesi
  farkli (zararsiz DLL payi egitim haftalarinda %64.9, testte %73.4). Bu
  nedensellik OLCULMEDI: bu paylar esigin secildigi 48-51. haftalara ait degil
  ve DLL icindeki yanlis alarm orani DLL'lerin payindan dogrudan etkilenmez.
  Esik zamanla yeniden dogrulanmali.
- **Yerel dogrulama seti eskiyor.** 9 Ekim'deki olcumden bu yana dosyalarinin
  857'si silindi, yuzlercesi guncellendi. Olcumlerin dayandigi 5.635 satir
  yeniden taranmak yerine donduruldu (repoda yok; SHA-256
  `gumruk_memuru/sonuclar/4/yerel_set.md`'de).
- Random Forest yalnizca AYARSIZ LightGBM'i gecti; ayarli LightGBM ayri,
  henuz yapilmamis bir deney.
- **.NET hala zayif nokta.** Onceden yazilan olcutlerle ayrica olculdu
  (`gumruk_memuru/sonuclar/5/`), ayni sabit esiklerle: test haftalarinda .NET
  EXE'lerde kacan %33.7 (.NET disi EXE %17.6). EMBER2024'un ayri .NET test
  kumesinde native model %1.05 yanlis alarmda zararlilarin %49.8'ini
  kaciriyor (zararli .NET DLL'lerin %86.7'si); Faz 1 modeli orada %0.46
  yanlis alarmda %92.8 kaciriyordu. Faz 1 ile AYNI yanlis alarmda native
  model %59.8 kaciriyor (zararli .NET DLL'lerin %92.7'si). Daha iyi ama
  yeterli degil: .NET dosyalari henuz bagli olmayan uzman modele gitmeli.

## Yol Haritasi

1. [x] Entropi hesaplayici (ilk calisan parca)
2. [x] Ilk Random Forest modeli kuruldu - %99.9 sonuc ANCAK veri sizintisi
       tespit edildi: sentetik "zararli" veri 5 sabit senaryodan (random.uniform)
       uretildigi icin gercekci degil. Senaryo disi "sinsi" ornekler
       %100 guvenle kaciyor. Bkz. `faz1_dogrulama.py`.
3. [x] Gercek ozellik cikarim motoru yazildi (`Chief_1.2.py` - magic byte,
       bolum-bazli entropi, pefile ile IAT/API analizi). v1.1'deki
       KARA_LISTE substring/cift-sayim hatasi duzeltildi (liste->set,
       tam esleme).
4. [x] EMBER'den gercek 5700 zararli kayit cikarildi. EMBER'in olcumu
       pefile tarafiyla esitlendi (ordinal import'lar ve bos bolumler).
5. [x] Zararsiz veri once bu makineden (System32 + Program Files) tarandi;
       bunun kaynak yanliligi yarattigi goruldu. Zararsiz egitim verisi de
       EMBER'den alindi, makine taramasi (533.081 dosya, 64.263 PE) dis
       dogrulama setine donustu.
6. [x] Random Forest gercek veriyle yeniden egitildi ve dogrulandi
       (ayni donem %90.1 / zamansal %83.8, gercek makinede %3.5 yanlis
       alarm). **Faz 1 kapandi.**
6b. [x] Native model EMBER2024'e tasindi (Random Forest, 86 ozellik, tur
       ici dengeli egitim; bkz. "Native model"). 2018 modeli git etiketi
       `eski-5-ozellik` altinda duruyor.
7. [ ] (Faz 2) eBPF ile Linux sistem cagrisi izleme
   - [x] Esik karsilastirmasi icin sinir-deger regresyon testi
         (`tests/test_esik_sinir.py`, `tests/esik_sinir.c`). Python'da
         tamsayi tasmasi yok; ama ajan C'ye tasininca dar tipe yazilan skor
         128'de negatife sariyor ve `skor > 100` kontrolunu atlatiyor:
         supheli dosya temiz geciyor. Test hatali ve dogru surumu (genis tip
         + aralik dogrulamasi + fail-closed) birlikte sabitliyor.
   - [x] C/C++ varsayilan bayraklari: `-Wall -Wextra -Wconversion
         -Wsign-conversion -Werror`. Derleyiciyi konusturmak en ucuz
         savunma: `-Wconversion` tasma satirini kod hic calismadan
         gosteriyor. Test, bu bayraklarin tam o satirda ve sadece orada
         uyari verdigini de denetliyor.
   - [x] Windows'ta MinGW gcc 16.2 ile dogrulandi (Ekim 2026): uyari
         bayraklari tek uyari veriyor, daralma satirinda; dogru C surumu 7
         sinir durumunun hepsini geciyor, hatali surum 128 ve 255'i
         kaciriyor. Faz 2'de Linux'ta yeniden kosulacak.
   - [ ] C kismini CI'da gercek bir derleyiciyle calistir; "atlandi"
         sessizce kalici olmasin.
8. [ ] (Faz 3) NPU / TEE donanimsal izolasyon
