"""
Sef Projesi - EMBER2024 .NET kumelerinden ozellik cikarma
============================================================

EMBER2024 (Eylul 2023 - Aralik 2024, VirusTotal) .NET kumeleri:
  train: ilk 52 hafta   test: son 12 hafta (zamansal bolme)
Haftalik kotayla zararli/zararsiz dengelenmis (gercek dunyadaki oran DEGIL).

Sutunlar: ember_zararli_cikar.kayittan_ozellik_cikar (EMBER 2018 ve
toplu_tarama.py ile AYNI kurallar) + dizge_ozellikleri (thrember ile
birebir, yerel dosyalarda dogrulandi) + DLL_mi + Aile, Hafta.

ON KOSUL (C:\\ember2024 icinde, Apache-2.0):
  test : Dot_Net_test.zip  (210 MB) -> C:\\ember2024\\*.jsonl
  train: Dot_Net_train.zip (894 MB) -> C:\\ember2024\\train\\*.jsonl
  https://huggingface.co/datasets/joyce8/EMBER2024/resolve/main/<zip adi>
Ciktilar buyuk oldugu icin proje (OneDrive) DISINA, C:\\ember2024'e yazilir.

Kullanim: python ember2024_net_cikar.py test|train
"""

import csv
import glob
import json
import os
import sys
import time

from dizge_ozellikleri import DIZGE_SUTUNLARI, kayittan_dizge_ozellikleri
from ember_zararli_cikar import CSV_KOLONLARI, kayittan_ozellik_cikar
from sef_ayarlar import EMBER2024_KLASORU, EMBER2024_TRAIN_KLASORU

GIRDI = {"test": EMBER2024_KLASORU, "train": EMBER2024_TRAIN_KLASORU}
KOLONLAR = CSV_KOLONLARI + DIZGE_SUTUNLARI + ["DLL_mi", "Aile", "Hafta"]


def dll_mi(kayit: dict) -> int:
    """thrember coff.characteristics = pefile FILE_HEADER'daki IMAGE_FILE_* bayraklari
    ("IMAGE_FILE_" kirpilmis); yerelde karsiligi pe.FILE_HEADER.IMAGE_FILE_DLL."""
    return int("DLL" in kayit.get("header", {}).get("coff", {}).get("characteristics", []))


def cikti_yolu(bolum: str) -> str:
    return os.path.join(EMBER2024_KLASORU, f"ember2024_net_{bolum}_ozellik.csv")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if len(sys.argv) != 2 or sys.argv[1] not in GIRDI:
        sys.exit("Kullanim: python ember2024_net_cikar.py test|train")
    bolum = sys.argv[1]
    dosyalar = sorted(glob.glob(os.path.join(GIRDI[bolum], "*_Dot_Net_*.jsonl")))
    if not dosyalar:
        raise FileNotFoundError(f"'{GIRDI[bolum]}' icinde *_Dot_Net_*.jsonl yok (ON KOSUL).")
    toplam_bayt = sum(os.path.getsize(d) for d in dosyalar)

    sayac = {0: 0, 1: 0}
    atlanan, okunan_bayt = 0, 0
    baslangic = son = time.monotonic()
    with open(cikti_yolu(bolum), "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=KOLONLAR)
        yazici.writeheader()
        for dosya in dosyalar:
            with open(dosya, "rb") as girdi:
                for satir in girdi:
                    okunan_bayt += len(satir)
                    kayit = json.loads(satir)
                    if kayit.get("label") not in (0, 1):
                        atlanan += 1
                        continue
                    ozellik = kayittan_ozellik_cikar(kayit, kayit["label"])
                    ozellik.update(kayittan_dizge_ozellikleri(kayit))
                    ozellik["DLL_mi"] = dll_mi(kayit)
                    ozellik["Aile"] = kayit.get("family") or ""
                    ozellik["Hafta"] = kayit.get("week_id", "")
                    yazici.writerow(ozellik)
                    sayac[kayit["label"]] += 1
                    simdi = time.monotonic()
                    if simdi - son >= 10:
                        son = simdi
                        oran = okunan_bayt / toplam_bayt
                        gecen = simdi - baslangic
                        print(f"  %{100 * oran:5.1f} | {sum(sayac.values())} kayit | "
                              f"gecen {gecen:.0f} sn, kalan ~{gecen / oran * (1 - oran):.0f} sn")

    print(f"[+] {bolum}: {sum(sayac.values())} kayit ({sayac[1]} zararli, {sayac[0]} zararsiz, "
          f"{atlanan} etiketsiz atlandi) -> '{cikti_yolu(bolum)}' "
          f"({time.monotonic() - baslangic:.0f} sn)")
