"""
Sef Projesi - Dis dogrulama setini (AYNI 5700 dosya) yeni sutunlarla yeniden olc
============================================================

Neden tam tarama degil: ayni dosyalari yeniden olcmek, "ozellik degisince
sonuc nasil degisti" sorusunu orneklem farki karismadan cevaplar. Tam
tarama (~2.5 saat) ancak populasyonun kendisi degisti mi sorusu icin gerekir.

Adimlar:
  1. Orneklemi yeniden kur: sef_tarama_tum_dosyalar.csv'deki PE satirlari,
     random.seed(42) ile toplu_tarama.py'deki AYNI cekim. Repodaki
     dogrulama setiyle satir satir ayni degilse DURUR.
  2. Klasorleri listele. O tarama dosyasi eski surumden: tam yol YOK, sadece
     Dosya_Adi -> yol, (ad, boyut) eslesmesiyle bulunur.
  3. Adaylari toplu_tarama.dosyayi_analiz_et ile oku; eski 5 sutunun HEPSI
     birebir tutan ilk aday alinir. Tutmayan satir ELENIR (sebebiyle
     kaydedilir): dosya silinmis/guncellenmis ya da olcum kodu degismis.
  4. Yaz: YENIDEN_OLCUM_CSV (Dosya_Adi'siz), isimli yedek ve elenenler
     (ikisi de .gitignore'da). Repodaki dogrulama setinin UZERINE YAZMAZ.

Kullanim: python dogrulama_yeniden_olc.py [--devam]
"""

import argparse
import csv
import os
import random
import sys
import time
from collections import Counter, defaultdict

from sef_ayarlar import (TARAMA_ZARARSIZ_CSV, TARANACAK_KLASORLER, TUM_TARAMA_CSV,
                         YENIDEN_OLCUM_CSV, YENIDEN_OLCUM_ELENEN_CSV, YENIDEN_OLCUM_ISIMLI_CSV)
from toplu_tarama import HEDEF_SAYI, PE_KOLONLARI, dosyayi_analiz_et, ilerleme_satiri

ESKI_SUTUNLAR = ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi", "Toplam_API", "Supheli_API"]
TAHMINI_DOSYA = 533_081   # onceki tam taramadaki dosya sayisi; listeleme yuzdesi icin TAHMIN
ISIMLI_KOLONLAR = ["Sira", "Dosya_Adi", "Dosya_Yolu"] + PE_KOLONLARI
ELENEN_KOLONLAR = ["Sira", "Dosya_Adi", "Boyut_Bayt", "Sebep", "Tutmayan_Sutunlar", "Aday_Sayisi"]
YAZDIRMA_SANIYESI = 15


def orneklemi_kur() -> list:
    with open(TUM_TARAMA_CSV, newline="", encoding="utf-8") as f:
        pe = [s for s in csv.DictReader(f) if s["PE_mi"] == "True"]
    random.seed(42)
    ornek = random.sample(pe, HEDEF_SAYI)
    with open(TARAMA_ZARARSIZ_CSV, newline="", encoding="utf-8") as f:
        kayitli = list(csv.DictReader(f))
    ortak = [k for k in kayitli[0] if k in ornek[0]]
    ayni = sum(all(o[k] == r[k] for k in ortak) for o, r in zip(ornek, kayitli))
    print(f"[1/4] Orneklem: {len(pe)} PE satirindan seed 42 ile {len(ornek)} -> repodaki "
          f"dogrulama setiyle {ayni}/{len(kayitli)} satir birebir ayni ({', '.join(ortak)})")
    if ayni != len(kayitli) or len(ornek) != len(kayitli):
        sys.exit("[!] Orneklem yeniden kurulamadi; tarama dosyasi degismis olabilir. DURDU.")
    return ornek


def yollari_listele(adlar: set) -> dict:
    """Sadece orneklemdeki adlar icin yol toplar (533K yolun hepsini tutmaz)."""
    adaylar = defaultdict(list)
    goruldu = 0
    baslangic = son = time.monotonic()
    for klasor in TARANACAK_KLASORLER:
        for kok, _, dosyalar in os.walk(klasor):
            for ad in dosyalar:
                goruldu += 1
                if ad in adlar:
                    adaylar[ad].append(os.path.join(kok, ad))
            simdi = time.monotonic()
            if simdi - son >= YAZDIRMA_SANIYESI:
                son = simdi
                oran = min(goruldu / TAHMINI_DOSYA, 0.999)
                gecen = simdi - baslangic
                print(f"  listeleme: {goruldu} dosya (~%{100 * oran:.0f}, tahmini toplam "
                      f"{TAHMINI_DOSYA}) | {len(adaylar)}/{len(adlar)} ad bulundu | "
                      f"gecen {gecen / 60:.1f} dk, kalan ~{gecen / oran * (1 - oran) / 60:.1f} dk")
        print(f"  listeleme: '{klasor}' bitti ({goruldu} dosya, {time.monotonic() - baslangic:.0f} sn)")
    print(f"[2/4] Listeleme: {goruldu} dosya, {(time.monotonic() - baslangic) / 60:.1f} dk | "
          f"orneklemdeki {len(adlar)} farkli addan {len(adaylar)} tanesi en az bir yolda var")
    return adaylar


def eslestir(satir: dict, adaylar: list, kullanilan: set):
    """(yeni_olcum, None) ya da (None, (sebep, tutmayan_sutunlar, aday_sayisi))."""
    boyut = int(satir["Boyut_Bayt"])
    uygun = []
    for yol in adaylar:
        try:
            if os.path.getsize(yol) == boyut:
                uygun.append(yol)
        except OSError:
            pass
    if not uygun:
        return None, ("ad+boyut adayi yok", "", 0)
    # Kullanilmamis yollar once: ayni ad+boyutta birden cok kopya varsa hepsini dene
    uygun.sort(key=lambda y: y in kullanilan)
    en_iyi_tutmayan, okunan = None, 0
    for yol in uygun:
        yeni = dosyayi_analiz_et(yol)
        if yeni is None or not yeni["PE_mi"]:
            continue
        okunan += 1
        tutmayan = [k for k in ESKI_SUTUNLAR if str(yeni[k]) != satir[k]]
        if not tutmayan:
            return yeni, None
        if en_iyi_tutmayan is None or len(tutmayan) < len(en_iyi_tutmayan):
            en_iyi_tutmayan = tutmayan
    if okunan == 0:
        return None, ("aday okunamadi / PE degil", "", len(uygun))
    return None, ("eski sutunlar tutmadi", "|".join(en_iyi_tutmayan), len(uygun))


def onceki(yol: str) -> list:
    if not os.path.exists(yol):
        return []
    with open(yol, newline="", encoding="utf-8") as f:
        return [s for s in csv.DictReader(f) if s.get("Sira")]


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--devam", action="store_true", help="yarim kalan olcumu surdur")
    args = parser.parse_args()
    t0 = time.monotonic()

    ornek = orneklemi_kur()
    adaylar = yollari_listele({s["Dosya_Adi"] for s in ornek})

    tutulan = onceki(YENIDEN_OLCUM_ISIMLI_CSV) if args.devam else []
    elenen = onceki(YENIDEN_OLCUM_ELENEN_CSV) if args.devam else []
    biten = {int(s["Sira"]) for s in tutulan + elenen}
    kullanilan = {s["Dosya_Yolu"] for s in tutulan}
    if args.devam:
        print(f"[*] --devam: {len(biten)} satir ara kayittan yuklendi")

    print(f"[3/4] {HEDEF_SAYI - len(biten)} dosya okunuyor (eski 5 sutun birebir tutmali)...")
    basla = son = time.monotonic()
    islenen = bu_elenen = 0
    yapilacak = [(i, s) for i, s in enumerate(ornek) if i not in biten]
    with open(YENIDEN_OLCUM_ISIMLI_CSV, "w", newline="", encoding="utf-8") as ft, \
            open(YENIDEN_OLCUM_ELENEN_CSV, "w", newline="", encoding="utf-8") as fe:
        yt = csv.DictWriter(ft, fieldnames=ISIMLI_KOLONLAR, extrasaction="ignore")
        ye = csv.DictWriter(fe, fieldnames=ELENEN_KOLONLAR)
        yt.writeheader(); yt.writerows(tutulan)
        ye.writeheader(); ye.writerows(elenen)
        for i, satir in yapilacak:
            yeni, hata = eslestir(satir, adaylar.get(satir["Dosya_Adi"], []), kullanilan)
            if yeni:
                yeni["Sira"] = i
                kullanilan.add(yeni["Dosya_Yolu"])
                tutulan.append(yeni)
                yt.writerow(yeni)
            else:
                e = {"Sira": i, "Dosya_Adi": satir["Dosya_Adi"], "Boyut_Bayt": satir["Boyut_Bayt"],
                     "Sebep": hata[0], "Tutmayan_Sutunlar": hata[1], "Aday_Sayisi": hata[2]}
                elenen.append(e)
                ye.writerow(e)
                bu_elenen += 1
            islenen += 1
            simdi = time.monotonic()
            if simdi - son >= YAZDIRMA_SANIYESI or islenen == len(yapilacak):
                son = simdi
                ft.flush(); fe.flush()
                print(ilerleme_satiri(islenen, len(yapilacak), islenen - bu_elenen, bu_elenen, basla)
                      .replace("basarili", "tutuldu").replace("atlandi", "elendi"))

    tutulan.sort(key=lambda s: int(s["Sira"]))
    with open(YENIDEN_OLCUM_CSV, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=PE_KOLONLARI, extrasaction="ignore")
        yazici.writeheader()
        yazici.writerows(tutulan)

    sebepler = Counter(e["Sebep"] for e in elenen)
    sutunlar = Counter(k for e in elenen for k in e["Tutmayan_Sutunlar"].split("|") if k)
    print(f"\n[4/4] SONUC ({(time.monotonic() - t0) / 60:.1f} dk):")
    print(f"  {HEDEF_SAYI} dosyadan {len(tutulan)} TUTULDU, {len(elenen)} ELENDI "
          f"(%{100 * len(elenen) / HEDEF_SAYI:.1f})")
    for sebep, n in sebepler.most_common():
        print(f"    - {sebep}: {n}")
    if sutunlar:
        print(f"  Tutmayan sutunlar (en yakin adayda): {dict(sutunlar.most_common())}")
    if len(elenen) > 0.2 * HEDEF_SAYI:
        print("  [!] Elenen oran %20'nin ustunde: dosya degisiminden cok olcum kodu farki "
              "olabilir. Tutmayan sutunlari incelemeden sonuclari KULLANMA.")
    if tutulan:
        n = len(tutulan)
        print(f"  Tutulanlarda: DLL %{100 * sum(int(s['DLL_mi']) for s in tutulan) / n:.1f}, "
              f".NET %{100 * sum(int(s['NET_mi']) for s in tutulan) / n:.1f}")
    print(f"  -> '{YENIDEN_OLCUM_CSV}' (Dosya_Adi'siz)")
    print(f"  -> '{YENIDEN_OLCUM_ISIMLI_CSV}', '{YENIDEN_OLCUM_ELENEN_CSV}' (yerel, .gitignore)")
