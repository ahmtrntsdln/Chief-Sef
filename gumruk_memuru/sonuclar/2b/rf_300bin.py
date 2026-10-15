"""
Adim 2b - RF 300 bin: E2 ve E3, 5 tohum, ayni test kumesi. n_estimators=100, gerisi varsayilan.

100 bin hucresi (E1/E2/E3, 5 tohum) 9 Ekim'de kosuldu, yeniden kosulmaz: native_ozet.json,
native_tum_kayitlar.csv. Parquet'ten yuklemenin 9 Ekim'i birebir verdigi bir hucrede dogrulandi
(E3 100 bin tohum 42: dogruluk 92.59, AUC 0.9791; DLL kacan 12.35).
E3 300 bin: (DLL_mi x Etiket) hucre basina 75.000 gerekir, en kucuk hucre (zararli DLL)
130.550 -> yerine koymadan kurulabiliyor. 1 milyonda RF kosulmaz (plan).

Cikti: rf_300bin.csv (2a ile ayni format). Kullanim: python rf_300bin.py
"""

import os
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
import ortak_deney as o  # noqa: E402

BOYUT = 300_000
CEKIRDEK = 8   # sonucu degistirmez (random_state sabit); laptop isinirsa dusur

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim, test, yerel = o.veri()
    hucre_min = int(egitim.groupby(["DLL_mi", "Etiket"]).size().min())
    if hucre_min < BOYUT // 4:
        sys.exit(f"DUR: E3 {BOYUT} icin hucre basina {BOYUT // 4} gerekir, en kucuk hucre {hucre_min}.")
    print(f"[*] egitim {len(egitim)}, test {len(test)}, yerel {len(yerel)} | en kucuk tip-ici hucre {hucre_min}")
    sonuc = o.SonucCSV(os.path.join(BURASI, "rf_300bin.csv"))
    hucreler = [(a, t) for a in o.ADAYLAR for t in o.TOHUMLAR if f"RF_{a}_{BOYUT}_{t}" not in sonuc.biten]
    print(f"[*] {len(hucreler)} hucre kosulacak")
    for i, (aday, tohum) in enumerate(hucreler, 1):
        satir = o.hucre_kos("RF", aday, BOYUT, tohum, egitim, test, yerel, CEKIRDEK)
        sonuc.ekle(satir)
        o.ilerleme(i, len(hucreler), t0, f"| {aday} tohum {tohum}: AUC {satir['genel_AUC']}, "
                   f"DLL kacan@1 {satir['DLL_kacan_%@1']}, {satir['sure_sn']} sn")
    print(f"[+] {(time.monotonic() - t0) / 60:.1f} dk")
