"""
Sef Projesi - Yerel olcum ile thrember (EMBER2024) olcumu ayni mi? (Kritik Kural 1, gercek dosyalar)
============================================================

EMBER2024 modeli egitimde thrember'in JSON kayitlarindan (ember2024_cikar.py), yerelde ise
toplu_tarama.dosyayi_analiz_et'ten beslenir. Ayni dosyada iki yol ayni sayilari vermeli.
Dizge sutunlari (80) Eylul 2026'da 500 gercek yerel dosyada thrember ile 500/500 birebir
dogrulandi; bu betik kalan 6 sutunu karsilastirir: Boyut_Bayt, Sifir_Orani, Ortalama_Entropi,
Toplam_API, Supheli_API, DLL_mi (+ bilgi icin NET_mi, Karma_Mod).

Iki adim, iki ortam (thrember'in bagimliliklari proje ortamina girmesin):
  1. thrember ortaminda: python thrember_karsilastir.py uret
     -> 50 yerel dosyanin thrember raw_features kaydi (EMBER2024 JSON bicimi) bir JSONL'e.
     thrember ortami (Windows 260 karakter yol siniri yuzunden kisa yolda):
       python -m venv C:\\ember2024\\thr_env
       C:\\ember2024\\thr_env\\Scripts\\python -m pip install scikit-learn==1.9.0 signify==0.7.1 ^
           git+https://github.com/FutureComputing4AI/EMBER2024.git
       (signify 0.9 thrember'in kullandigi SignedPEFile'i kaldirdi; 0.7.1 uyumlu)
  2. proje ortaminda: python thrember_karsilastir.py karsilastir
     -> ayni dosyalar yerel kodla yeniden olculur, sutun sutun esitlik raporlanir.

Orneklem (seed 42, dis dogrulama setinden): 20 EXE, 20 DLL, 5 .NET, 5 import'suz DLL.
"""

import csv
import json
import os
import random
import sys

GIRDI = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sef_dogrulama_dz80_isimli.csv")
CIKTI = r"C:\ember2024\thrember_karsilastirma_50.jsonl"
SUTUNLAR = ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi", "Toplam_API", "Supheli_API", "DLL_mi"]
BILGI = ["NET_mi", "Karma_Mod"]
BEKLENEN = 50


def orneklem():
    with open(GIRDI, encoding="utf-8") as f:
        tum = list(csv.DictReader(f))
    # Dosyalar olcumden sonra silinmis/guncellenmis olabilir (ornek: .NET paket guncellemesi): yalnizca
    # hala var olanlardan sec; kac tanesinin elendigi raporlanir.
    satirlar = [s for s in tum if os.path.exists(s["Dosya_Yolu"])]
    print(f"[*] dis dogrulama setinde {len(tum)} dosya, {len(tum) - len(satirlar)} tanesi artik yok; {len(satirlar)} arasindan secilecek")
    rng = random.Random(42)
    kume = {
        ".NET": [s for s in satirlar if s["NET_mi"] == "1"],
        "import'suz DLL": [s for s in satirlar if s["DLL_mi"] == "1" and s["Toplam_API"] == "0" and s["NET_mi"] == "0"],
        "EXE": [s for s in satirlar if s["DLL_mi"] == "0" and s["NET_mi"] == "0"],
        "DLL": [s for s in satirlar if s["DLL_mi"] == "1" and s["Toplam_API"] != "0" and s["NET_mi"] == "0"],
    }
    secim = []
    for grup, n in ((".NET", 5), ("import'suz DLL", 5), ("EXE", 20), ("DLL", 20)):
        for s in rng.sample(kume[grup], n):
            secim.append((grup, s["Dosya_Yolu"]))
    return secim


def uret():
    import thrember  # yalnizca thrember ortaminda
    cikarici = thrember.PEFeatureExtractor()
    # Once gecici dosyaya; yarida kalirsa eski/eksik bir JSONL karsilastirmaya girmez.
    gecici = CIKTI + ".part"
    with open(gecici, "w", encoding="utf-8") as f:
        for i, (grup, yol) in enumerate(orneklem(), 1):
            with open(yol, "rb") as d:
                kayit = cikarici.raw_features(d.read())
            kayit["_grup"], kayit["_yol"] = grup, yol
            f.write(json.dumps(kayit) + "\n")
            print(f"  {i}/{BEKLENEN} {grup}: {os.path.basename(yol)}")
    os.replace(gecici, CIKTI)
    print(f"[+] {CIKTI}")


def karsilastir():
    from ember_zararli_cikar import dll_mi, kayittan_ozellik_cikar
    from toplu_tarama import dosyayi_analiz_et

    def esit(a, b):
        return abs(float(a) - float(b)) < 1e-6

    with open(CIKTI, encoding="utf-8") as f:
        kayitlar = [json.loads(s) for s in f]
    farklar, tutan = [], {s: 0 for s in SUTUNLAR + BILGI}
    for k in kayitlar:
        yerel = dosyayi_analiz_et(k["_yol"])
        thr = kayittan_ozellik_cikar(k, 0)
        thr["DLL_mi"] = dll_mi(k)
        for s in SUTUNLAR + BILGI:
            if esit(yerel[s], thr[s]):
                tutan[s] += 1
            else:
                farklar.append(f"{k['_grup']} {os.path.basename(k['_yol'])} {s}: yerel {yerel[s]} / thrember {thr[s]}")
    n = len(kayitlar)
    print(f"[*] {n} dosya: " + ", ".join(f"{g} {sum(1 for k in kayitlar if k['_grup'] == g)}" for g in (".NET", "import'suz DLL", "EXE", "DLL")))
    for s in SUTUNLAR + BILGI:
        print(f"  {s:<17} {tutan[s]}/{n}{'' if s in SUTUNLAR else '  (bilgi)'}")
    if n != BEKLENEN:
        # Bos ya da eksik girdiyle "fark yok" demek sahte bir gecis olurdu.
        print(f"[!] {n} kayit var, {BEKLENEN} bekleniyordu: once 'uret' adimini basariyla tamamla.")
        return False
    print("\n".join(["Farklar:"] + farklar) if farklar else "Fark yok: 6 sutun (ve NET_mi, Karma_Mod) birebir ayni.")
    return not any(f.split(": ")[0].split()[-1] in SUTUNLAR for f in farklar)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if len(sys.argv) != 2 or sys.argv[1] not in ("uret", "karsilastir"):
        sys.exit("Kullanim: python thrember_karsilastir.py uret|karsilastir")
    if sys.argv[1] == "uret":
        uret()
    else:
        sys.exit(0 if karsilastir() else 1)
