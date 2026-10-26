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

Cikis kodu EN KOTU sonuctan (toplu_cikis_kodu): herhangi bir ZARARLI 3; yoksa OLASI ZARARLI 4;
yoksa BELIRSIZ 2; yoksa hata 1; hepsi temiz 0. "PE degil" kodu yukseltmez (ozette sayilir).
Yol yok / okunamiyor: 1. Hic PE dosyasi siniflanmadiysa (bos klasor, yanlis yol, yalniz .txt)
uyari ve 1 (fail-closed): yanlis yol yazilinca sessizce "her sey temiz" cikmasin. Kodlar
tahmin_et.CIKIS_KODU ile ayni: 0 yalniz "her sey temiz".

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
KARARLAR = (te.ZARARSIZ, te.BELIRSIZ, te.ZARARLI, te.OLASI_ZARARLI)      # PE dosyasi siniflandi
ONCELIK = (te.ZARARLI, te.OLASI_ZARARLI, te.BELIRSIZ)                     # en kotu once
ILERLEME_SANIYE = 30


def toplu_cikis_kodu(sayac):
    """En kotu sonuc: ZARARLI 3 > OLASI ZARARLI 4 > BELIRSIZ 2 > hata 1 > temiz 0; PE yoksa 1."""
    for k in ONCELIK:
        if sayac[k]:
            return te.CIKIS_KODU[k]
    if sayac[HATA] or not any(sayac[k] for k in KARARLAR):
        return te.CIKIS_HATA
    return te.CIKIS_KODU[te.ZARARSIZ]


def yollari_topla(girdiler):
    """(yollar, bulunamayan girdiler)."""
    yollar, eksik = [], []
    for g in girdiler:
        if os.path.isfile(g):
            yollar.append(g)
        elif os.path.isdir(g):
            yollar.extend(dosyalari_listele([g]))
        else:
            eksik.append(g)
    return yollar, eksik


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
    yollar, eksik = yollari_topla(a.girdiler)
    if eksik:
        print(f"Hata: bulunamadi -> {', '.join(eksik)}", file=sys.stderr)
        return te.CIKIS_HATA
    print(f"[*] {len(yollar)} dosya")
    if not yollar:
        print("[!] UYARI: hic dosya bulunamadi (bos klasor ya da okunamiyor); 'temiz' denmez.", file=sys.stderr)
        return te.CIKIS_HATA
    paket = te.model_yukle()
    sayac = tara(yollar, paket, a.liste)
    print("\n=== Ozet ===")
    for ad in SAYAC_SIRASI:
        print(f"  {ad:<14}: {sayac[ad]}")
    print("  (BELIRSIZ hata degil: .NET'te esik alti ya da gecersiz skor; ek inceleme gerekir.)")
    if not any(sayac[k] for k in KARARLAR):
        print("[!] UYARI: hic PE dosyasi siniflanmadi; 'temiz' denmez.", file=sys.stderr)
    kod = toplu_cikis_kodu(sayac)
    print(f"  cikis kodu: {kod} (en kotu sonuc; 0 yalniz her sey temizse)")
    return kod


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    sys.exit(main(sys.argv[1:]))
