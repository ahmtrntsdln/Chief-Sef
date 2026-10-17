"""
Adim 3 - Uctan uca test: 20 yerel dosyada
  (1) tahmin_et'in ozellikleri (ozellik_cikar) dogrulama CSV'sindekiyle (sef_dogrulama_dz80)
      86 sutunun HEPSINDE ayni mi,
  (2) tek dosya tahmini (tahmin_et.tahmin) toplu tahminle (CSV satirlari, ayni model) ayni mi.
HEPSI gecmeli; biri bile tutmazsa cikis kodu 1.

  (3) ozellik_cikar (tek modul) refactor oncesi yolla (dosyayi_analiz_et + ayri okumayla
      dosyadan_dizge_ozellikleri) ayni mi.

Secim (tohum 42, deterministik): dogrulama setinden diskte HALA duran, boyutu CSV'dekiyle ayni
VE son degisikligi olcumden (dz80 CSV'sinin yazilma ani) ONCE olan dosyalar; 7 native EXE +
8 native DLL + 5 .NET. Neden degisiklik zamani: ilk kosuda 2 .NET dosyasi 14 Ekim'de ayni
boyutla guncellenmisti (icerik farkli; eski ve yeni kod o dosyalarda da birebir ayniydi) -
boyut tek basina "dosya degismedi" demek degil. Log'a dosya adi/yol YAZILMAZ (kurulu
yazilimlari gosterir), sadece sira no ve tur.
Kullanim: python uctan_uca.py
"""

import csv
import os
import random
import sys

import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(BURASI, "..", "..")))
import tahmin_et  # noqa: E402
from dizge_ozellikleri import dosyadan_dizge_ozellikleri  # noqa: E402
from ozellik_cikar import MODEL_KOLONLARI, dosya_turu  # noqa: E402
from sef_ayarlar import DOGRULAMA_DZ80_ISIMLI_CSV  # noqa: E402
from toplu_tarama import dosyayi_analiz_et  # noqa: E402

KOTA = {"EXE": 7, "DLL": 8, ".NET": 5}

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    with open(DOGRULAMA_DZ80_ISIMLI_CSV, encoding="utf-8") as f:
        satirlar = sorted(csv.DictReader(f), key=lambda r: int(r["Sira"]))
    olcum_ani = os.path.getmtime(DOGRULAMA_DZ80_ISIMLI_CSV)
    adaylar = {t: [] for t in KOTA}
    for r in satirlar:
        yol = r["Dosya_Yolu"]
        if (os.path.isfile(yol) and os.path.getsize(yol) == int(float(r["Boyut_Bayt"]))
                and os.path.getmtime(yol) < olcum_ani):
            adaylar[dosya_turu(r)].append(r)
    rng = random.Random(42)
    secilen = [r for t, n in KOTA.items() for r in rng.sample(adaylar[t], n)]
    print(f"[*] dogrulama setinde {len(satirlar)} satir; diskte ve boyutu ayni aday: "
          f"{ {t: len(v) for t, v in adaylar.items()} }; secilen {len(secilen)}")

    paket = tahmin_et.model_yukle()
    if paket["meta"]["ozellikler"] != MODEL_KOLONLARI:
        sys.exit("BASARISIZ: model meta ozellik sirasi ozellik_cikar ile ayni degil")
    toplu = pd.DataFrame([{k: float(r[k]) for k in MODEL_KOLONLARI} for r in secilen])
    p_toplu = paket["model"].predict_proba(toplu[MODEL_KOLONLARI])[:, 1]

    hata = 0
    for i, (r, pt) in enumerate(zip(secilen, p_toplu), 1):
        tek = tahmin_et.tahmin(r["Dosya_Yolu"], paket)
        farkli = [k for k in MODEL_KOLONLARI if not np.isclose(float(tek[k]), float(r[k]), rtol=0, atol=1e-9)]
        ayni_tahmin = tek["olasilik"] == pt
        eski = dosyayi_analiz_et(r["Dosya_Yolu"])         # refactor oncesi yol
        with open(r["Dosya_Yolu"], "rb") as f:
            eski.update(dosyadan_dizge_ozellikleri(f.read()))
        kod_ayni = all(float(tek[k]) == float(eski[k]) for k in MODEL_KOLONLARI)
        durum = "GECTI" if not farkli and ayni_tahmin and kod_ayni else "BASARISIZ"
        hata += durum != "GECTI"
        print(f"  {i:2d} sira {r['Sira']:>5} {tek['Dosya_Turu']:<4} | CSV ile 86/86 "
              f"{'ayni' if not farkli else f'FARKLI: {farkli}'} | tek {tek['olasilik']:.6f} toplu {pt:.6f} "
              f"{'ayni' if ayni_tahmin else 'FARKLI'} | eski kod {'ayni' if kod_ayni else 'FARKLI'} | {durum}")
    print(f"\nSONUC: {len(secilen) - hata}/{len(secilen)} gecti -> {'BASARILI' if hata == 0 else 'BASARISIZ'}")
    sys.exit(1 if hata else 0)
