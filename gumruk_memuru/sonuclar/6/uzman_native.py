"""
Adim 6 - .NET uzman modeli (M2, M2d) ile native model, Dot_Net_test'te esit yanlis alarmda.
On kayit: on_kayit_uzman_native.md (olcumden once commit'lendi).

GECIT: net_model.py tarifi aynen (hafta 0-51, 100K) -> M2d EXE YA (esik 0,5) == 7,34.
Uzmanlar: hafta 0-47 havuzu (M2 100K sinif dengeli, M2d 4 x 24.104 tip-ici); esik hafta 48-51
dogrulama diliminden (tur basina, hedef %0,45 / %1,05); test BIR KEZ. Native: kayitli model.
Kullanim: python uzman_native.py   (log icin > uzman_native.log)
"""

import os
import sys
import time

import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", "5"))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from ember2024_net_cikar import cikti_yolu  # noqa: E402
from esit_ya import esik_bul  # noqa: E402
from net_model import DIZGELI, DIZGELI_TIPLI, EGITIM_ORNEK, rf, sinif_dengeli, tip_ici_dengeli  # noqa: E402

HEDEFLER = [0.45, 1.05]
DOGRULAMA_HAFTA = 48
CEKIRDEK = 8


def egit(ornek, kolon):
    return rf().set_params(n_jobs=CEKIRDEK).fit(ornek[kolon], ornek["Etiket"])


def oran(k, n):
    alt, ust = o.wilson(k, n)
    return {"k": int(k), "n": int(n), "%": round(100 * k / n, 2), "alt": round(alt, 2), "ust": round(ust, 2)}


def olc(ad, h, p_dog, dog, p_test, test):
    """Tur basina esik dogrulamadan, test bir kez. Satirlar: EXE, DLL, hepsi."""
    esik, dog_ya = {}, {}
    for tur, deger in (("EXE", 0), ("DLL", 1)):
        m = (dog.DLL_mi.to_numpy() == deger) & (dog.Etiket.to_numpy() == 0)
        t, ya, _ = esik_bul(p_dog[m], h)
        esik[tur], dog_ya[tur] = float(t), round(float(ya), 3)
    y, dll = test.Etiket.to_numpy(), test.DLL_mi.to_numpy() == 1
    e = np.where(dll, esik["DLL"], esik["EXE"])
    satirlar = []
    for tur, m in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
        zr, zs = m & (y == 1), m & (y == 0)
        satirlar.append({"model": ad, "hedef_YA_%": h, "tur": tur,
                         "esik": esik.get(tur, f"EXE {esik['EXE']:.4f} / DLL {esik['DLL']:.4f}"),
                         "dogrulama_YA_%": dog_ya.get(tur, ""),
                         **{f"kacan_{a}": v for a, v in oran(int((p_test[zr] <= e[zr]).sum()), int(zr.sum())).items()},
                         **{f"YA_{a}": v for a, v in oran(int((p_test[zs] > e[zs]).sum()), int(zs.sum())).items()}})
    return satirlar


def ortusuyor(a, b, on):
    return not (a[f"{on}_ust"] < b[f"{on}_alt"] or b[f"{on}_ust"] < a[f"{on}_alt"])


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    print(f"[*] Dot_Net_train {len(egitim)} (hafta {egitim.Hafta.min()}-{egitim.Hafta.max()}), "
          f"Dot_Net_test {len(test)} ({time.monotonic() - t0:.0f} sn)")
    y_t, dll_t = test.Etiket.to_numpy(), test.DLL_mi.to_numpy() == 1

    # --- GECIT: net_model.py tarifi aynen ---
    m2d_gecit = egit(tip_ici_dengeli(egitim), DIZGELI_TIPLI)
    p = m2d_gecit.predict_proba(test[DIZGELI_TIPLI])[:, 1]
    exe_ya = round(100 * (p[~dll_t & (y_t == 0)] > 0.5).mean(), 2)
    if exe_ya != 7.34:
        sys.exit(f"GECIT BASARISIZ: M2d EXE YA {exe_ya} != 7,34")
    print(f"[+] GECIT: M2d (hafta 0-51, 100K) EXE YA %{exe_ya} == 7,34 ({time.monotonic() - t0:.0f} sn)")
    m2_gecit = egit(sinif_dengeli(egitim), DIZGELI)
    p = m2_gecit.predict_proba(test[DIZGELI])[:, 1]
    print(f"[*] M2 yeniden uretim (esik 0,5): kacan %{100 * (p[y_t == 1] <= 0.5).mean():.2f}, YA %{100 * (p[y_t == 0] > 0.5).mean():.2f} "
          f"(EXE YA %{100 * (p[~dll_t & (y_t == 0)] > 0.5).mean():.2f}) | belge: kacan 3,8 / YA 4,2 / EXE YA ~26")
    del m2d_gecit, m2_gecit

    # --- Dogrulama dilimi ayrilmis uzmanlar ---
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    hucre_min = int(havuz.groupby(["DLL_mi", "Etiket"]).size().min())
    print(f"[*] havuz {len(havuz)}, dogrulama {len(dog)}; M2d boyutu 4 x {hucre_min} = {4 * hucre_min}")
    m2 = egit(havuz.groupby("Etiket", group_keys=False).sample(n=EGITIM_ORNEK // 2, random_state=42), DIZGELI)
    m2d = egit(havuz.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=hucre_min, random_state=42), DIZGELI_TIPLI)
    paket = tahmin_et.model_yukle()
    paket["model"].set_params(n_jobs=CEKIRDEK)
    nk = paket["meta"]["ozellikler"]
    skor = {
        "M2 (uzman, kestirmeli)": (m2.predict_proba(dog[DIZGELI])[:, 1], m2.predict_proba(test[DIZGELI])[:, 1]),
        "M2d (uzman, tip-ici)": (m2d.predict_proba(dog[DIZGELI_TIPLI])[:, 1], m2d.predict_proba(test[DIZGELI_TIPLI])[:, 1]),
        "native": (paket["model"].predict_proba(dog[nk].astype("float32"))[:, 1],
                   paket["model"].predict_proba(test[nk].astype("float32"))[:, 1]),
    }
    print(f"[*] modeller hazir ({time.monotonic() - t0:.0f} sn)")

    satirlar = [s for h in HEDEFLER for ad, (pd_, pt) in skor.items() for s in olc(ad, h, pd_, dog, pt, test)]
    df = pd.DataFrame(satirlar)
    df.to_csv(os.path.join(BURASI, "uzman_native.csv"), index=False)

    print("\n| hedef YA | model | tur | esik (dogrulamadan) | dogrulama YA | test kacan % [Wilson] (k/n) | test YA % [Wilson] (k/n) |")
    print("|---|---|---|---|---|---|---|")
    for s in satirlar:
        esik = f"{s['esik']:.4f}" if isinstance(s["esik"], float) else s["esik"]
        print(f"| %{s['hedef_YA_%']} | {s['model']} | {s['tur']} | {esik} | {s['dogrulama_YA_%']} | "
              f"%{s['kacan_%']:.2f} [{s['kacan_alt']:.2f}-{s['kacan_ust']:.2f}] ({s['kacan_k']}/{s['kacan_n']}) | "
              f"%{s['YA_%']:.2f} [{s['YA_alt']:.2f}-{s['YA_ust']:.2f}] ({s['YA_k']}/{s['YA_n']}) |")

    print("\n=== Yorum kurali (on kayit) ===")
    for h in HEDEFLER:
        for uzman in ("M2 (uzman, kestirmeli)", "M2d (uzman, tip-ici)"):
            for tur in ("EXE", "DLL", "hepsi"):
                u = df[(df["hedef_YA_%"] == h) & (df.model == uzman) & (df.tur == tur)].iloc[0]
                n = df[(df["hedef_YA_%"] == h) & (df.model == "native") & (df.tur == tur)].iloc[0]
                if not ortusuyor(u, n, "YA"):
                    hukum = f"esit yanlis alarm SAGLANAMADI (test YA {u['YA_%']} vs {n['YA_%']}) -> hukum yok"
                elif ortusuyor(u, n, "kacan"):
                    hukum = "fark gosterilemedi"
                else:
                    hukum = f"{'UZMAN' if u['kacan_%'] < n['kacan_%'] else 'NATIVE'} daha az kaciriyor"
                print(f"  H %{h} {uzman:<24} vs native, {tur:<5}: kacan {u['kacan_%']} vs {n['kacan_%']} | "
                      f"YA {u['YA_%']} vs {n['YA_%']} -> {hukum}")
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> uzman_native.csv")
