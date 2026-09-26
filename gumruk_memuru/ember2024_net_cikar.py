"""
Sef Projesi - EMBER2024 .NET test kumesinden ozellik cikarma
============================================================

EMBER2024 (Eylul 2023 - Aralik 2024, VirusTotal) .NET test kumesi: son 12
hafta, haftalik kotayla zararli/zararsiz dengelenmis (gercek dunyadaki
oran DEGIL). Sadece dogrulama icin: EMBER 2018 ile egitilen modelin guncel
.NET zararlilarinda nasil davrandigini olcer. Egitimde kullanilmaz.

Ozellikler ember_zararli_cikar.kayittan_ozellik_cikar ile, EMBER 2018 ve
toplu_tarama.py ile AYNI kurallarla cikarilir (ordinal bicimi ve CLR dizini
farklari orada ele aliniyor).

ON KOSUL: https://huggingface.co/datasets/joyce8/EMBER2024 -> Dot_Net_test.zip
(210 MB, Apache-2.0) EMBER2024_KLASORU'ne acilmis olmali.
"""

import glob
import json
import os
import sys
import time

from ember_zararli_cikar import CSV_KOLONLARI, csv_yaz, kayittan_ozellik_cikar

EMBER2024_KLASORU = r"C:\ember2024"
CIKTI_DOSYASI = "sef_dataset_ember2024_net_test.csv"
KOLONLAR = CSV_KOLONLARI + ["Aile", "Hafta"]

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    dosyalar = sorted(glob.glob(os.path.join(EMBER2024_KLASORU, "*_Dot_Net_test.jsonl")))
    if not dosyalar:
        raise FileNotFoundError(f"'{EMBER2024_KLASORU}' icinde *_Dot_Net_test.jsonl yok (ON KOSUL).")
    toplam_bayt = sum(os.path.getsize(d) for d in dosyalar)

    kayitlar, atlanan, okunan_bayt = [], 0, 0
    baslangic = son = time.monotonic()
    for dosya in dosyalar:
        with open(dosya, "rb") as f:
            for satir in f:
                okunan_bayt += len(satir)
                kayit = json.loads(satir)
                if kayit.get("label") not in (0, 1):
                    atlanan += 1
                    continue
                ozellik = kayittan_ozellik_cikar(kayit, kayit["label"])
                ozellik["Aile"] = kayit.get("family") or ""
                ozellik["Hafta"] = kayit.get("week_id", "")
                kayitlar.append(ozellik)
                simdi = time.monotonic()
                if simdi - son >= 10:
                    son = simdi
                    oran = okunan_bayt / toplam_bayt
                    gecen = simdi - baslangic
                    print(f"  %{100 * oran:5.1f} | {len(kayitlar)} kayit | gecen {gecen:.0f} sn, "
                          f"kalan ~{gecen / oran * (1 - oran):.0f} sn")

    csv_yaz(kayitlar, CIKTI_DOSYASI, KOLONLAR)
    zararli = sum(k["Etiket"] for k in kayitlar)
    print(f"[+] {len(kayitlar)} kayit ({zararli} zararli, {len(kayitlar) - zararli} zararsiz, "
          f"{atlanan} etiketsiz atlandi) -> '{CIKTI_DOSYASI}' "
          f"({(time.monotonic() - baslangic):.0f} sn)")
