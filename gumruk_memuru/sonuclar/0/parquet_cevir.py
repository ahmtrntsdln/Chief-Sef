"""
Adim 0 - EMBER2024 Win32/Win64 ozellik CSV'lerini (128 hafta) tek seferde Parquet'e cevirir.

Neden: sonraki adimlar (2a ogrenme egrisi: 1 milyon ve tamami) 4.2M satiri defalarca
okuyacak; 128 CSV'yi her seferinde ayristirmak dakikalar suruyor. Parquet tipleri korur
ve sutun bazinda okunur.

Girdi : <EMBER2024_KLASORU>/ozellik/<zip>/*.csv  (ember2024_cikar.py)
Cikti : <EMBER2024_KLASORU>/parquet/<zip>.parquet (proje DISINDA, buyuk)
Kontrol (Kural 5): her zip icin CSV satir toplami == Parquet satiri; tur basina
zararli orani, DLL orani, hafta araligi; (DLL_mi x Etiket) hucre sayilari (E3 tip-ici
orneklem boyutlarinin ust siniri). Ozet: sonuclar/0/parquet_ozet.csv.

Kullanim (repo kokunden ya da herhangi bir yerden): python gumruk_memuru/sonuclar/0/parquet_cevir.py
"""

import glob
import os
import sys
import time

import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BURASI, "..", "..")))
from ember2024_cikar import cikti_klasoru  # noqa: E402
from sef_ayarlar import EMBER2024_PARQUET_KLASORU as PARQUET_KLASORU  # noqa: E402

ZIPLER = ["Win32_train", "Win64_train", "Win32_test", "Win64_test"]


def parquet_yolu(ad: str) -> str:
    return os.path.join(PARQUET_KLASORU, f"{ad}.parquet")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    os.makedirs(PARQUET_KLASORU, exist_ok=True)
    t0 = time.monotonic()
    ozet = []
    for i, ad in enumerate(ZIPLER, 1):
        dosyalar = sorted(glob.glob(os.path.join(cikti_klasoru(ad), "*.csv")))
        if not dosyalar:
            sys.exit(f"Hata: '{cikti_klasoru(ad)}' bos.")
        parcalar, csv_satir = [], 0
        for j, f in enumerate(dosyalar, 1):
            d = pd.read_csv(f, keep_default_na=False, dtype={"Aile": str, "Tur": str, "Dosya_Adi": str})
            csv_satir += len(d)
            parcalar.append(d)
            if j % 13 == 0 or j == len(dosyalar):
                print(f"  [{i}/{len(ZIPLER)}] {ad}: {j}/{len(dosyalar)} hafta okundu | {time.monotonic() - t0:.0f} sn")
        df = pd.concat(parcalar, ignore_index=True)
        df.to_parquet(parquet_yolu(ad), index=False)
        geri = pd.read_parquet(parquet_yolu(ad), columns=["Etiket", "DLL_mi", "Hafta", "Tur"])
        if len(geri) != csv_satir:
            sys.exit(f"Hata: {ad} CSV {csv_satir} satir, Parquet {len(geri)} satir.")
        hucre = geri.groupby(["DLL_mi", "Etiket"]).size()
        ozet.append({
            "zip": ad, "satir": len(geri), "csv_satir": csv_satir, "hafta_min": int(geri.Hafta.min()),
            "hafta_max": int(geri.Hafta.max()), "zararli_%": round(100 * geri.Etiket.mean(), 2),
            "DLL_zararsiz_%": round(100 * geri[geri.Etiket == 0].DLL_mi.mean(), 2),
            "DLL_zararli_%": round(100 * geri[geri.Etiket == 1].DLL_mi.mean(), 2),
            **{f"hucre_DLL{int(d)}_E{int(e)}": int(n) for (d, e), n in hucre.items()},
            "MB": round(os.path.getsize(parquet_yolu(ad)) / 2**20, 1),
        })
        print(f"  [{i}/{len(ZIPLER)}] {ad}: {len(geri)} satir -> {parquet_yolu(ad)} ({ozet[-1]['MB']} MB)")
    tablo = pd.DataFrame(ozet)
    tablo.to_csv(os.path.join(BURASI, "parquet_ozet.csv"), index=False)
    print("\n" + tablo.to_string(index=False))
    print(f"\n[+] {(time.monotonic() - t0) / 60:.1f} dk")
