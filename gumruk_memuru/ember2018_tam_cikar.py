"""
Sef Projesi - EMBER 2018'in TAMAMINDAN ozellik CSV'si
============================================================

Ana model 5700+5700'luk orneklemle egitildi (sef_dataset_*.csv, repo'da).
Bu script etiketli kayitlarin HEPSINI cikarir; neden:
  - EMBER 2018'de zararsizlarin ~%23'u, zararlilarin ~%3'u DLL. Tip-ici
    dengeli egitim (net_model.py'deki M2d gibi) icin orneklemdeki ~165
    zararli DLL yetmez; tum veride binlerce var.
  - EMBER'in kendi zamansal bolmesiyle olcum: train Ocak-Ekim 2018,
    test Kasim-Aralik 2018 (egitimde hic gorulmeyen, daha yeni dosyalar).

Sutunlar ember_zararli_cikar.ember2018_kayittan ile AYNI (temel + DLL_mi +
EMBER 2018 strings grubu) + Aile (avclass) + Ay (appeared).
Ciktilar buyuk: proje (OneDrive) DISINA, sef_ayarlar.EMBER2018_CIKTI_KLASORU'ne.

Kullanim: python ember2018_tam_cikar.py test|train
"""

import csv
import glob
import json
import os
import sys
import time

from ember_zararli_cikar import EMBER2018_KOLONLARI, ember2018_kayittan
from sef_ayarlar import EMBER2018_CIKTI_KLASORU, EMBER2018_KLASORU

DESEN = {"test": "test_features.jsonl", "train": "train_features_*.jsonl"}
KOLONLAR = EMBER2018_KOLONLARI + ["Aile", "Ay"]


def cikti_yolu(bolum: str) -> str:
    return os.path.join(EMBER2018_CIKTI_KLASORU, f"ember2018_{bolum}_ozellik.csv")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if len(sys.argv) != 2 or sys.argv[1] not in DESEN:
        sys.exit("Kullanim: python ember2018_tam_cikar.py test|train")
    bolum = sys.argv[1]
    dosyalar = sorted(glob.glob(os.path.join(EMBER2018_KLASORU, DESEN[bolum])))
    if not dosyalar:
        raise FileNotFoundError(f"'{EMBER2018_KLASORU}' icinde {DESEN[bolum]} yok.")
    toplam_bayt = sum(os.path.getsize(d) for d in dosyalar)

    sayac = {0: 0, 1: 0}
    etiketsiz = basliksiz = okunan_bayt = 0
    baslangic = son = time.monotonic()
    with open(cikti_yolu(bolum), "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=KOLONLAR)
        yazici.writeheader()
        for dosya in dosyalar:
            with open(dosya, "rb") as girdi:
                for satir in girdi:
                    okunan_bayt += len(satir)
                    kayit = json.loads(satir)
                    if kayit["label"] not in (0, 1):
                        etiketsiz += 1
                        continue
                    if "coff" not in kayit["header"]:
                        # DLL_mi olculemez; 0 ("EXE") yazmak sessiz varsayilan olurdu
                        basliksiz += 1
                        continue
                    ozellik = ember2018_kayittan(kayit, kayit["label"])
                    ozellik["Aile"] = kayit.get("avclass") or ""
                    ozellik["Ay"] = kayit["appeared"]
                    yazici.writerow(ozellik)
                    sayac[kayit["label"]] += 1
                    simdi = time.monotonic()
                    if simdi - son >= 15:
                        son = simdi
                        oran = okunan_bayt / toplam_bayt
                        gecen = simdi - baslangic
                        print(f"  %{100 * oran:5.1f} | {sum(sayac.values())} kayit | "
                              f"gecen {gecen / 60:.1f} dk, kalan ~{gecen / oran * (1 - oran) / 60:.1f} dk")

    print(f"[+] {bolum}: {sum(sayac.values())} kayit ({sayac[1]} zararli, {sayac[0]} zararsiz; "
          f"{etiketsiz} etiketsiz, {basliksiz} coff'suz atlandi) -> '{cikti_yolu(bolum)}' "
          f"({(time.monotonic() - baslangic) / 60:.1f} dk)")
