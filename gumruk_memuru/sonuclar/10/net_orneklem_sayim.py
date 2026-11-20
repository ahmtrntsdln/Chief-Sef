"""
.NET uzman modeli orneklem sayimi - net_model.py'nin M2 ve M2d egitim orneklemlerini KURAR ve SAYAR.

Neden: M2 / M2d orneklem boyutlari (100.000 satir; 90.330 / 74.542 essiz dosya) bugun yalniz koddaki
sabitlerde geciyor (net_model.EGITIM_ORNEK, sonuclar/8/envanter.py); onlari hesaplayan kodun bastigi
bir log yok. Kaynak kurali: bir sayinin kaynagi onu hesaplayan kodun bastigi log / sonuc dosyasidir.

Ne yapar: net_model.py'nin okudugu girdiyi (Dot_Net_train) net_model.py ile AYNI bicimde okur
(keep_default_na=False) ve orneklemleri net_model.py'nin KENDI fonksiyonlariyla kurar
(net_model.sinif_dengeli -> M1/M2, net_model.tip_ici_dengeli -> M2d; kopya degil, import: tohum ve
mantik tek yerde). Her orneklem icin toplam ve hucre basina satir ve essiz dosya (Dosya_Adi = sha256'nin
ilk 12 hanesi, Is 7 ile ayni anahtar) sayisini, havuzdaki karsiliklariyla yazar.

Ne yapmaz: egitim YOK, model YAZILMAZ, girdi degistirilmez. Yazdigi tek dosyalar bu klasordeki
net_orneklem_sayim.log ve net_orneklem_sayim.csv (ya da --cikti-klasoru).
Log yolu gostermez (yalniz dosya adi + sha256): yerel yollar paylasilmaz.

Kullanim (Windows, bu klasorde):   python net_orneklem_sayim.py
Test / baska girdi:                python net_orneklem_sayim.py --girdi <csv> --cikti-klasoru <klasor>
"""

import argparse
import csv
import hashlib
import os
import platform
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import net_model  # noqa: E402  (orneklem fonksiyonlari ve EGITIM_ORNEK buradan; kopya yok)

LOG_ADI = "net_orneklem_sayim.log"
CSV_ADI = "net_orneklem_sayim.csv"
CSV_KOLONLARI = ["orneklem", "hucre", "satir", "essiz", "havuz_satir", "havuz_essiz"]
GEREKLI = ["Dosya_Adi", "Etiket", "DLL_mi"]


class Gunluk:
    """Her satiri hem ekrana hem UTF-8 log dosyasina yazar (PowerShell yonlendirmesi UTF-16/BOM uretebilir)."""

    def __init__(self, yol):
        self.dosya = open(yol, "w", encoding="utf-8", newline="\n")

    def __call__(self, metin=""):
        print(metin, flush=True)
        self.dosya.write(metin + "\n")
        self.dosya.flush()

    def kapat(self):
        self.dosya.close()


def dosya_sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def sira_ozeti(df):
    """Orneklemin satir sirasiyla Dosya_Adi dizisinin sha256'si: ayni girdi + ayni kod -> ayni ozet."""
    return hashlib.sha256("\n".join(df["Dosya_Adi"].astype(str)).encode("utf-8")).hexdigest()


def hucre_etiketi(anahtarlar, deger):
    deger = deger if isinstance(deger, tuple) else (deger,)
    return " ".join(f"{a}={d}" for a, d in zip(anahtarlar, deger))


def say(ad, orneklem, havuz):
    """Toplam + hucre satirlari (sozluk listesi). Hucreler: Etiket ve (DLL_mi, Etiket)."""
    satirlar = [{"orneklem": ad, "hucre": "toplam", "satir": len(orneklem),
                 "essiz": int(orneklem["Dosya_Adi"].nunique()),
                 "havuz_satir": len(havuz), "havuz_essiz": int(havuz["Dosya_Adi"].nunique())}]
    for anahtarlar in (["Etiket"], ["DLL_mi", "Etiket"]):
        h_grup = havuz.groupby(anahtarlar)["Dosya_Adi"]
        o_grup = orneklem.groupby(anahtarlar)["Dosya_Adi"]
        o_satir, o_essiz = o_grup.size(), o_grup.nunique()
        for deger, h_satir in h_grup.size().items():
            satirlar.append({"orneklem": ad, "hucre": hucre_etiketi(anahtarlar, deger),
                             "satir": int(o_satir.get(deger, 0)), "essiz": int(o_essiz.get(deger, 0)),
                             "havuz_satir": int(h_satir), "havuz_essiz": int(h_grup.nunique()[deger])})
    return satirlar


def kopya_dagilimi(df):
    """Orneklemde bir Dosya_Adi kac kez geciyor -> {kopya sayisi: dosya sayisi}."""
    return {int(k): int(v) for k, v in df["Dosya_Adi"].value_counts().value_counts().sort_index().items()}


def celiskili_sha(havuz):
    """Ayni Dosya_Adi farkli Etiket ya da DLL_mi ile geciyor mu (hucre sayimini bozar)."""
    g = havuz.groupby("Dosya_Adi")[["Etiket", "DLL_mi"]].nunique()
    return int(((g["Etiket"] > 1) | (g["DLL_mi"] > 1)).sum())


def calistir(girdi, cikti_klasoru):
    os.makedirs(cikti_klasoru, exist_ok=True)
    yaz = Gunluk(os.path.join(cikti_klasoru, LOG_ADI))
    try:
        t0 = time.monotonic()
        if not os.path.isfile(girdi):
            yaz(f"[!] girdi yok: {os.path.basename(girdi)} (once: python ember2024_net_cikar.py train)")
            return 1
        girdi_ozet = dosya_sha256(girdi)
        havuz = pd.read_csv(girdi, keep_default_na=False)          # net_model.py ile ayni okuma
        eksik = [k for k in GEREKLI if k not in havuz.columns]
        if eksik:
            yaz(f"[!] girdide eksik kolon: {eksik}")
            return 1

        hafta = pd.to_numeric(havuz["Hafta"], errors="coerce") if "Hafta" in havuz.columns else None
        hafta_metni = (f"hafta {int(hafta.min())}-{int(hafta.max())}, bos hafta {int(hafta.isna().sum())}"
                       if hafta is not None and hafta.notna().any() else "hafta kolonu yok/bos")
        yaz(f"[*] girdi {os.path.basename(girdi)} sha256 {girdi_ozet}")
        yaz(f"[*] havuz: satir {len(havuz)}, essiz {havuz['Dosya_Adi'].nunique()}, {hafta_metni}, "
            f"celiskili sha {celiskili_sha(havuz)} ({time.monotonic() - t0:.0f} sn)")
        yaz(f"[*] surumler: python {platform.python_version()}, pandas {pd.__version__}, numpy {np.__version__}")
        yaz(f"[*] parametre (olcum DEGIL): net_model.EGITIM_ORNEK = {net_model.EGITIM_ORNEK}")

        orneklemler = {
            "M2 (sinif_dengeli; M1 ile ayni orneklem)": net_model.sinif_dengeli(havuz),
            "M2d (tip_ici_dengeli)": net_model.tip_ici_dengeli(havuz),
        }
        tum = []
        for ad, orneklem in orneklemler.items():
            satirlar = say(ad.split()[0], orneklem, havuz)
            tum.extend(satirlar)
            toplam = satirlar[0]
            yaz(f"\n=== {ad} ===")
            yaz(f"  toplam: satir {toplam['satir']}, essiz dosya {toplam['essiz']} | "
                f"kopya dagilimi {kopya_dagilimi(orneklem)} | sira ozeti {sira_ozeti(orneklem)[:16]}")
            for s in satirlar[1:]:
                yaz(f"  hucre {s['hucre']}: satir {s['satir']}, essiz {s['essiz']} | "
                    f"havuzda satir {s['havuz_satir']}, essiz {s['havuz_essiz']}")

        with open(os.path.join(cikti_klasoru, CSV_ADI), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_KOLONLARI, lineterminator="\n")
            w.writeheader()
            w.writerows(tum)
        yaz(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn); egitim yok, model yazilmadi")
        return 0
    finally:
        yaz.kapat()


def main(argv=None):
    from ember2024_net_cikar import cikti_yolu
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--girdi", default=None, help="varsayilan: ember2024_net_cikar.cikti_yolu('train')")
    ap.add_argument("--cikti-klasoru", default=BURASI)
    a = ap.parse_args(argv)
    return calistir(a.girdi or cikti_yolu("train"), a.cikti_klasoru)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main())
