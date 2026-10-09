"""
Sef Projesi - Dis dogrulama setine EMBER2024 dizge sutunlarini (80) ekle
============================================================

Girdi: dogrulama_yeniden_olc.py'nin isimli ciktisi (ayni 5700 dosyanin 5637'si; 63'u
o olcumde elendi). EMBER2024 modelini bu makinede sinamak icin thrember'in 80 dizge
sutunu gerekiyor (string_counts; EMBER 2018 olcumunde yoktu).

Her dosya icin:
  1. Dosyayi yolundan oku; toplu_tarama.dosyayi_analiz_et ile eski 5 sutunu YENIDEN olc.
     Tutmuyorsa dosya 7 Ekim'den beri degismis (guncelleme) -> ELENIR, sebebiyle sayilir.
  2. dizge_ozellikleri.dosyadan_dizge_ozellikleri ile 80 sutun (thrember koduyla yerelde
     500/500 birebir dogrulanmis kod).
  3. Tutarlilik: onceki olcumdeki DZ_sayi / DZ_ort_uzunluk / DZ_entropi yeni olcumle ayni
     olmali (ayni tanim); tutmayan sayilir ve raporlanir.
Ciktilar: DOGRULAMA_DZ80_ISIMLI_CSV (.gitignore) ve Dosya_Adi'siz DOGRULAMA_DZ80_CSV.
Ilerleme yuzde/kalan sure ile; --devam isimli ciktidaki satirlari atlar.

Kullanim: python dogrulama_dizge80.py [--devam]
"""

import argparse
import csv
import os
import sys
import time
from collections import Counter

from dizge_ozellikleri import DIZGE_SUTUNLARI, dosyadan_dizge_ozellikleri
from sef_ayarlar import DOGRULAMA_DZ80_CSV, DOGRULAMA_DZ80_ISIMLI_CSV, YENIDEN_OLCUM_ISIMLI_CSV
from toplu_tarama import dosyayi_analiz_et

ESKI_SUTUNLAR = ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi", "Toplam_API", "Supheli_API"]
ORTAK_DIZGE = ["DZ_sayi", "DZ_ort_uzunluk", "DZ_entropi"]
YAZDIRMA_SANIYESI = 15


def esit(a, b) -> bool:
    try:
        return abs(float(a) - float(b)) < 1e-6
    except ValueError:
        return str(a) == str(b)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--devam", action="store_true")
    args = ap.parse_args()

    with open(YENIDEN_OLCUM_ISIMLI_CSV, encoding="utf-8") as f:
        girdi = list(csv.DictReader(f))
    temel = [k for k in girdi[0] if k not in ("Sira", "Dosya_Adi", "Dosya_Yolu") and k not in ORTAK_DIZGE]
    kolonlar = ["Sira", "Dosya_Adi", "Dosya_Yolu"] + temel + DIZGE_SUTUNLARI
    bitmis = set()
    if args.devam and os.path.exists(DOGRULAMA_DZ80_ISIMLI_CSV):
        with open(DOGRULAMA_DZ80_ISIMLI_CSV, encoding="utf-8") as f:
            bitmis = {r["Sira"] for r in csv.DictReader(f)}
    mod = "a" if bitmis else "w"
    sayac = Counter()
    baslangic = son = time.monotonic()
    yapilacak = [r for r in girdi if r["Sira"] not in bitmis]
    print(f"[*] {len(girdi)} dosya ({len(bitmis)} onceden bitmis), {len(yapilacak)} olculecek")
    with open(DOGRULAMA_DZ80_ISIMLI_CSV, mod, newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=kolonlar)
        if mod == "w":
            yazici.writeheader()
        for i, satir in enumerate(yapilacak, 1):
            yol = satir["Dosya_Yolu"]
            yeni = dosyayi_analiz_et(yol)
            if yeni is None:
                sayac["okunamadi / silinmis"] += 1
            elif not all(esit(yeni[s], satir[s]) for s in ESKI_SUTUNLAR):
                sayac["eski sutunlar tutmadi (dosya degismis)"] += 1
            else:
                try:
                    with open(yol, "rb") as d:
                        bytez = d.read()
                except OSError:
                    sayac["okunamadi / silinmis"] += 1
                else:
                    dz = dosyadan_dizge_ozellikleri(bytez)
                    if not all(esit(dz[s], satir[s]) for s in ORTAK_DIZGE):
                        sayac["ortak dizge sutunlari tutmadi"] += 1
                    cikti = {k: satir[k] for k in ["Sira", "Dosya_Adi", "Dosya_Yolu"] + temel}
                    cikti.update(dz)
                    yazici.writerow(cikti)
                    f.flush()
                    sayac["yazildi"] += 1
            simdi = time.monotonic()
            if simdi - son >= YAZDIRMA_SANIYESI or i == len(yapilacak):
                son = simdi
                gecen = simdi - baslangic
                print(f"  %{100 * i / len(yapilacak):5.1f} | {i}/{len(yapilacak)} | {dict(sayac)} | "
                      f"gecen {gecen / 60:.1f} dk, kalan ~{gecen / i * (len(yapilacak) - i) / 60:.1f} dk")

    # Dosya_Adi'siz kopya (repo'ya girebilecek bicim; karar birlestirmede verilir)
    with open(DOGRULAMA_DZ80_ISIMLI_CSV, encoding="utf-8") as f:
        satirlar = list(csv.DictReader(f))
    with open(DOGRULAMA_DZ80_CSV, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=[k for k in kolonlar if k not in ("Sira", "Dosya_Adi", "Dosya_Yolu")])
        yazici.writeheader()
        for r in satirlar:
            yazici.writerow({k: r[k] for k in yazici.fieldnames})
    print(f"[+] {len(satirlar)} satir -> {DOGRULAMA_DZ80_CSV} | bu calisma: {dict(sayac)}")
