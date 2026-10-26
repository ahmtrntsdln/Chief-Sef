"""
Sef Projesi - Toplu tahmin (native model, klasor ya da dosyalar)
============================================================

Her dosya tahmin_et.tahmin ile siniflanir (tek ozellik modulu, Kural 9; model SHA-256 dogrulamali,
Kural 10). Sayaclar AYRI: temiz / BELIRSIZ / ZARARLI / OLASI ZARARLI / PE degil / hata.
BELIRSIZ hata DEGILDIR: .NET'te esik alti ya da gecersiz skor; ek inceleme ister (tahmin_et.karar).
"hata" yalniz analiz edilemeyen dosya (bos, 100 MiB ustu, okunamiyor).

toplu_tarama.py'den AYRI: o dis dogrulama setinin ozelliklerini uretir ve model yuklemez; ona tahmin
eklemek dogrulama setini ureten kodu tahmin koduna baglardi. Buradan yalniz dosya gezme alinir.
Dosya adlari varsayilan olarak yazilmaz (kurulu yazilimlari gosterir); --liste temiz olmayanlari
ekrana basar, dosyaya yazmaz.

Kullanim: python toplu_tahmin.py <klasor_ya_da_dosya> [...] [--liste]
"""

import argparse
import os
import sys
import time
from collections import Counter

import tahmin_et as te
from toplu_tarama import dosyalari_listele

PE_DEGIL, HATA = "PE degil", "hata"
SAYAC_SIRASI = [te.ZARARSIZ, te.BELIRSIZ, te.ZARARLI, te.OLASI_ZARARLI, PE_DEGIL, HATA]
ILERLEME_SANIYE = 30


def yollari_topla(girdiler):
    yollar = []
    for g in girdiler:
        if os.path.isfile(g):
            yollar.append(g)
        elif os.path.isdir(g):
            yollar.extend(dosyalari_listele([g]))
        else:
            sys.exit(f"Hata: bulunamadi -> {g}")
    return yollar


def sinifla(yol, paket):
    """Tek dosyanin sayaci: karar, PE degil ya da hata (beklenmeyen istisnalar yutulmaz)."""
    try:
        return te.tahmin(yol, paket)["karar"]
    except te.PEDegilHatasi:
        return PE_DEGIL
    except ValueError:
        return HATA


def tara(yollar, paket, liste=False):
    sayac = Counter()
    t0 = son = time.monotonic()
    for i, yol in enumerate(yollar, 1):
        k = sinifla(yol, paket)
        sayac[k] += 1
        if liste and k in (te.BELIRSIZ, te.ZARARLI, te.OLASI_ZARARLI):
            print(f"  {k:<13} {yol}")
        simdi = time.monotonic()
        if simdi - son >= ILERLEME_SANIYE or i == len(yollar):
            son = simdi
            kalan = (simdi - t0) / i * (len(yollar) - i)
            print(f"  [{i}/{len(yollar)}] %{100 * i / len(yollar):5.1f} | gecen {(simdi - t0) / 60:.1f} dk, "
                  f"kalan ~{kalan / 60:.1f} dk | " + ", ".join(f"{a}: {sayac[a]}" for a in SAYAC_SIRASI))
    return sayac


def main(argv):
    ap = argparse.ArgumentParser(description="Native modelle toplu tahmin (BELIRSIZ hata sayilmaz)")
    ap.add_argument("girdiler", nargs="+", help="klasor(ler) ya da dosya(lar)")
    ap.add_argument("--liste", action="store_true", help="temiz olmayan dosyalari ekrana bas")
    a = ap.parse_args(argv)
    yollar = yollari_topla(a.girdiler)
    print(f"[*] {len(yollar)} dosya")
    paket = te.model_yukle()
    sayac = tara(yollar, paket, a.liste)
    print("\n=== Ozet ===")
    for ad in SAYAC_SIRASI:
        print(f"  {ad:<14}: {sayac[ad]}")
    print("  (BELIRSIZ hata degil: .NET'te esik alti ya da gecersiz skor; ek inceleme gerekir.)")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main(sys.argv[1:]))
