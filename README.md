# Chief-Sef
Machine learning-powered software-hardware security engine

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
- `gumruk_memuru/Chief_1.2.py` -> Tam statik analiz motoru (magic byte, bolum-bazli entropi, IAT/API)
- `gumruk_memuru/ember_zararli_cikar.py`, `ember_zararsiz_cikar.py` -> EMBER'den gercek veri cikarma
- `gumruk_memuru/toplu_tarama.py` -> Bu makinedeki dosyalari tarama (dis dogrulama seti)
- `gumruk_memuru/rf_egit_gercek.py` -> Egitim, dis dogrulama ve sinsi ornek testleri;
  ana modeli `model.pkl` olarak kaydeder (repo'da yok: ~10 sn'de ayni model
  yeniden uretilir, pickle da sklearn surumune bagli)
- `gumruk_memuru/tahmin_et.py` -> Tek dosya tahmini: `python tahmin_et.py <dosya>`.
  Ozellikler dis dogrulamadaki ayni kodla cikarilir, boylece %3.5 yanlis
  alarm olcumu bu script icin de gecerli.
- `gumruk_memuru/model_karsilastir.py` -> RF vs LightGBM ve kalibrasyon karsilastirmasi

Kurulum: `pip install -r requirements.txt` (model karsilastirmasi icin
`requirements-experimental.txt`).

## Faz 1 Sonuclari

Model: Random Forest, 5 ozellik (boyut, sifir orani, ortalama bolum
entropisi, toplam API, supheli API). Egitim: EMBER 2018'den 5700 zararli +
5700 zararsiz gercek PE dosyasi.

| Olcum | Sonuc |
|---|---|
| EMBER test dogrulugu | %90.1 |
| EMBER icinde yanlis alarm / kacan zararli | %8.1 / %11.7 |
| Bu makinedeki 5700 gercek zararsiz PE'de yanlis alarm (egitimde hic gorulmedi) | %3.5 |
| En onemli ozellikler | Toplam_API 0.30, Boyut 0.25, Entropi 0.24, Sifir orani 0.18 |

%90 bilincli olarak %99'dan daha guvenilir bir sonuc: onceki %99.9 (sentetik
veri) ve %97 (zararsiz verinin tek makineden gelmesi) sonuclari, modelin
zararli davranisi degil veri kaynaklari arasindaki farki ogrendigini
gosteriyordu. Ayrintilar: [GELISIM_SURECI.md](GELISIM_SURECI.md).

Model karsilastirmasi (5 katli CV): Random Forest (AUC 0.963) ayarsiz
LightGBM'i (0.952) geciyor. Bu sonuc 5 ozellige ozgu; ozellik sayisi
artinca karsilastirma tekrarlanacak.

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
       (%90.1, gercek makinede %3.5 yanlis alarm). **Faz 1 kapandi.**
7. [ ] (Faz 2) eBPF ile Linux sistem cagrisi izleme
8. [ ] (Faz 3) NPU / TEE donanimsal izolasyon
