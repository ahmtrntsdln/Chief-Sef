"""
Is 2(a) - M2d'nin yerel mesru .NET dosyalarinda yanlis alarmi; ayni dosyalarda native ile McNemar.
On kayit: is2a_on_kayit.md (olcumden once commit'lendi).

M2d uzman_native.py tarifiyle yeniden egitilir (hafta 0-47, 4 x 24.104, tohum 42); esikler hafta 48-51
dogrulama diliminden, uzman_native.csv ile AYNI olmali (K3/K4). Yerel set dondurulmus, sha256 kontrollu.
Kullanim: python is2a_yerel_net.py   (log icin > is2a_yerel_net.log)
"""

import hashlib
import os
import sys
import time

import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
for alt in ("..", os.path.join("..", "2c"), os.path.join("..", "5"), os.path.join("..", "6"), os.path.join("..", "..")):
    sys.path.insert(0, os.path.join(BURASI, alt))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from ember2024_net_cikar import cikti_yolu  # noqa: E402
from esit_ya import esik_bul  # noqa: E402
from karar_tablosu import mcnemar  # noqa: E402
from net_model import DIZGELI_TIPLI  # noqa: E402
from sef_ayarlar import YEREL_DOGRULAMA_5635_CSV  # noqa: E402
from uzman_native import DOGRULAMA_HAFTA, HEDEFLER, egit, olc  # noqa: E402

M2D, NATIVE = "M2d (uzman, tip-ici)", "native"
BEKLENEN_ESIK = {(0.45, M2D): (0.86, 0.69), (0.45, NATIVE): (0.83, 0.69),
                 (1.05, M2D): (0.76, 0.59), (1.05, NATIVE): (0.79, 0.60)}
BEKLENEN_SAYI = {"hepsi": 3471, "EXE": 49, "DLL": 3422}
URETIM_NET_ALARM = 1           # sonuclar/5/net_sonuc.md, C: 1/3471
KUCUK_N, MCNEMAR_MIN = 30, 6


def dur(mesaj):
    sys.exit(f"GECIT BASARISIZ: {mesaj}")


def esikler(p_dog, dog, h):
    e = {}
    for tur, deger in (("EXE", 0), ("DLL", 1)):
        m = (dog.DLL_mi.to_numpy() == deger) & (dog.Etiket.to_numpy() == 0)
        e[tur] = float(esik_bul(p_dog[m], h)[0])
    return e


def alarm(p, dll, e):
    return p > np.where(dll, e["DLL"], e["EXE"])


def oran_metni(k, n):
    if n < KUCUK_N:
        return f"{k}/{n} (n<{KUCUK_N}, yorumlanmaz)"
    alt, ust = o.wilson(k, n)
    return f"%{100 * k / n:.2f} [{alt:.2f}-{ust:.2f}] ({k}/{n})"


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    paket = tahmin_et.model_yukle()                        # SHA-256 dogrulamali (Kural 10)
    native, meta = paket["model"], paket["meta"]
    native.set_params(n_jobs=8)
    nk = meta["ozellikler"]

    # --- K1, K2: yerel set ---
    h = hashlib.sha256(open(YEREL_DOGRULAMA_5635_CSV, "rb").read()).hexdigest()
    if h != meta["yerel_dogrulama_seti"]["sha256"]:
        dur(f"K1 yerel set sha256 {h[:16]} tutmuyor")
    print(f"[+] K1 yerel set sha256 {h[:16]}... == meta")
    yerel = pd.read_csv(YEREL_DOGRULAMA_5635_CSV)
    p_uretim_tum = native.predict_proba(yerel[nk])[:, 1]   # net_olcum.py C ile ayni cagri
    net_m = yerel.NET_mi.to_numpy() == 1
    yn, p_uretim = yerel[net_m].reset_index(drop=True), p_uretim_tum[net_m]
    dll_y = yn.DLL_mi.to_numpy() == 1
    sayi = {"hepsi": len(yn), "EXE": int((~dll_y).sum()), "DLL": int(dll_y.sum())}
    eksik = [k for k in DIZGELI_TIPLI if k not in yn.columns]
    if sayi != BEKLENEN_SAYI or eksik or yn[DIZGELI_TIPLI].isna().any().any():
        dur(f"K2 sayilar {sayi}, eksik sutun {eksik}, NaN {int(yn[DIZGELI_TIPLI].isna().sum().sum())}")
    print(f"[+] K2 yerel .NET {sayi}, Karma_Mod {int(yn.Karma_Mod.sum())}, 87 sutun tam")

    # --- M2d (uzman_native.py tarifi) ---
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    hucre_min = int(havuz.groupby(["DLL_mi", "Etiket"]).size().min())
    m2d = egit(havuz.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=hucre_min, random_state=42), DIZGELI_TIPLI)
    print(f"[*] M2d egitildi: 4 x {hucre_min} = {4 * hucre_min} ({time.monotonic() - t0:.0f} sn)")
    skor = {
        M2D: (m2d.predict_proba(dog[DIZGELI_TIPLI])[:, 1], m2d.predict_proba(test[DIZGELI_TIPLI])[:, 1],
              m2d.predict_proba(yn[DIZGELI_TIPLI])[:, 1]),
        NATIVE: (native.predict_proba(dog[nk].astype("float32"))[:, 1],
                 native.predict_proba(test[nk].astype("float32"))[:, 1], p_uretim),
    }

    # --- K3, K4: esikler ve Dot_Net_test sayilari uzman_native.csv ile birebir ---
    onceki = pd.read_csv(os.path.join(BURASI, "..", "6", "uzman_native.csv"))
    esik, test_ya = {}, {}
    for hd in HEDEFLER:
        for ad, (p_dog, p_test, _) in skor.items():
            gecit = "K3" if ad == M2D else "K4"
            e = esikler(p_dog, dog, hd)
            bek = BEKLENEN_ESIK[(hd, ad)]
            if not np.allclose([e["EXE"], e["DLL"]], bek, rtol=0, atol=1e-9):
                dur(f"{gecit} H %{hd} {ad} esik {e} != {bek}")
            for s in olc(ad, hd, p_dog, dog, p_test, test):
                r = onceki[(onceki.model == ad) & (onceki["hedef_YA_%"] == hd) & (onceki.tur == s["tur"])].iloc[0]
                if (s["kacan_k"], s["YA_k"]) != (r.kacan_k, r.YA_k):
                    dur(f"{gecit} H %{hd} {ad} {s['tur']}: kacan/YA {s['kacan_k']}/{s['YA_k']} != csv {r.kacan_k}/{r.YA_k}")
                test_ya[(hd, ad, s["tur"])] = f"%{s['YA_%']:.2f} ({s['YA_k']}/{s['YA_n']})"
            esik[(hd, ad)] = e
            print(f"[+] {gecit} H %{hd} {ad}: esik EXE {e['EXE']:.2f} / DLL {e['DLL']:.2f} ve Dot_Net_test 3 satir == csv")
    k_uretim = int(alarm(p_uretim, dll_y, meta["esikler"]).sum())
    if k_uretim != URETIM_NET_ALARM:
        dur(f"K4 native uretim esiginde yerel .NET alarm {k_uretim} != {URETIM_NET_ALARM}")
    print(f"[+] K4 native uretim esikleri {meta['esikler']}: yerel .NET alarm {k_uretim}/{len(yn)} == net_sonuc.md")

    # --- Olcum (bir kez) ---
    satirlar, alarmlar = [], {}
    for hd in HEDEFLER:
        for ad in (M2D, NATIVE):
            a = alarm(skor[ad][2], dll_y, esik[(hd, ad)])
            alarmlar[(hd, ad)] = a
            for tur, m in (("EXE", ~dll_y), ("DLL", dll_y), ("hepsi", np.ones_like(dll_y))):
                k, n = int(a[m].sum()), int(m.sum())
                alt, ust = o.wilson(k, n)
                satirlar.append({"hedef_YA_%": hd, "model": ad, "tur": tur,
                                 "esik": f"{esik[(hd, ad)]['EXE']:.2f} / {esik[(hd, ad)]['DLL']:.2f}",
                                 "YA_k": k, "YA_n": n, "YA_%": round(100 * k / n, 3),
                                 "YA_alt": round(alt, 3), "YA_ust": round(ust, 3),
                                 "alarm_Karma_Mod": int((a & m & (yn.Karma_Mod.to_numpy() == 1)).sum()),
                                 "Dot_Net_test_YA": test_ya[(hd, ad, tur)]})
    df = pd.DataFrame(satirlar)
    df.to_csv(os.path.join(BURASI, "is2a_yerel_net.csv"), index=False)

    print("\n| H | model | tur | esik EXE / DLL | yerel .NET YA % [Wilson %95] (k/n) | alarmda Karma_Mod | Dot_Net_test YA (ayni esik) |")
    print("|---|---|---|---|---|---|---|")
    for s in satirlar:
        print(f"| %{s['hedef_YA_%']} | {s['model']} | {s['tur']} | {s['esik']} | {oran_metni(s['YA_k'], s['YA_n'])} | "
              f"{s['alarm_Karma_Mod']} | {s['Dot_Net_test_YA']} |")

    p05 = skor[M2D][2] > 0.5
    print(f"\n[*] Betimleyici: M2d esik 0,5'te yerel .NET YA: EXE {oran_metni(int(p05[~dll_y].sum()), sayi['EXE'])}, "
          f"DLL {oran_metni(int(p05[dll_y].sum()), sayi['DLL'])}")

    # --- Yorum kurallari (on kayit) ---
    print("\n=== Yorum kurallari (is2a_on_kayit.md) ===")
    for hd in HEDEFLER:
        for tur in ("EXE", "DLL"):
            s = df[(df["hedef_YA_%"] == hd) & (df.model == M2D) & (df.tur == tur)].iloc[0]
            if s.YA_n < KUCUK_N:
                h1 = f"n={s.YA_n} < {KUCUK_N} -> yorumlanmaz"
            elif o.wilson(0, s.YA_n)[1] >= hd:
                h1 = f"hukum yok: cozunurluk yetersiz (wilson(0, {s.YA_n}) ust %{o.wilson(0, s.YA_n)[1]:.2f} >= H)"
            elif s.YA_ust < hd:
                h1 = f"M2d yerel mesru .NET {tur} dosyalarinda hedefin ALTINDA yanlis alarm veriyor"
            elif s.YA_alt > hd:
                h1 = f"M2d yerel mesru .NET {tur} dosyalarinda hedefin USTUNDE yanlis alarm veriyor"
            else:
                h1 = "hedefle farki gosterilemedi"
            print(f"1) H %{hd} M2d {tur}: YA %{s['YA_%']} [{s.YA_alt}-{s.YA_ust}] ({s.YA_k}/{s.YA_n}) -> {h1}")
    for hd in HEDEFLER:
        for tur, m in (("EXE", ~dll_y), ("DLL", dll_y)):
            b, c, p = mcnemar(alarmlar[(hd, M2D)][m], alarmlar[(hd, NATIVE)][m])
            if b + c < MCNEMAR_MIN:
                h2 = f"hukum yok: uyusmayan cift sayisi yetersiz (b + c = {b + c} < {MCNEMAR_MIN})"
            elif p < 0.05:
                h2 = f"M2d yerelde native'den anlamli olarak daha {'COK' if b > c else 'AZ'} yanlis alarm veriyor"
            else:
                h2 = "fark gosterilemedi"
            print(f"2) H %{hd} M2d - native {tur}: yalniz M2d {b}, yalniz native {c}, p = {p:.4g} -> {h2}")
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> is2a_yerel_net.csv")
