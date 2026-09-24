# Sef Projesi

Yapay zeka destekli, donanimsal izolasyonlu siber guvenlik motoru.

## Faz 1: Konseptin Ispati - Gumruk Memuru

Ilk hedef: dosyalarin Shannon Entropisini olcup normal dosyalarla
sifrelenmis/paketlenmis (potansiyel supheli) dosyalari ayirt edebilen
basit bir statik analiz katmani kurmak.

- `gumruk_memuru/entropy.py` -> Entropi hesaplama modulu

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
4. [ ] EMBER'den gercek 5700 zararli kayit cikarma (`ember_zararli_cikar.py`
       hazir - EMBER verisinin indirilip acilmasi gerekiyor)
5. [ ] Gercek zararsiz (Chief_1.2.py ile 5700 dosyadan) + gercek zararli
       (EMBER'den) veriyle Random Forest'i yeniden egitme
6. [ ] (Ileride) eBPF ile Linux sistem cagrisi izleme
7. [ ] (Ileride) NPU / TEE donanimsal izolasyon
