"""
Adim 5 - Native son model .NET alt grubunda (on kayit: on_kayit_net.md, olcumden once commit'lendi).

A (birincil): Win32_test + Win64_test hafta 52-63, NET_mi = 1 / 0, EXE / DLL.
   GECIT: alt grupsuz EXE/DLL kacan ve yanlis alarm meta'daki test_bir_kez ile birebir olmali.
B (Faz 1 ile ayni kume): EMBER2024 Dot_Net_test; sabit tur esikleri ve 0,5.
C (ucuncul): dondurulmus yerel set (sha256 kontrollu, yeniden TARANMAZ), yanlis alarm.
Esikler meta'dan, AYARLANMAZ. Wilson %95; n < 30 hucrede oran yorumlanmaz.
Kullanim: python net_olcum.py   (cikti: net_olcum.csv + stdout; log icin > net_olcum.log)
"""

import hashlib
import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from sef_ayarlar import EMBER2024_KLASORU, YEREL_DOGRULAMA_5635_CSV  # noqa: E402

FAZ1_NET_KACAN = 92.8          # net_dogrulama.py, Dot_Net_test, esik 0,5 (CLAUDE.md, README "%93")
DOT_NET_TEST_CSV = os.path.join(EMBER2024_KLASORU, "ember2024_net_test_ozellik.csv")
KUCUK_N = 30


def oran(k, n):
    if n == 0:
        return {"k": 0, "n": 0, "%": float("nan"), "alt": float("nan"), "ust": float("nan")}
    alt, ust = o.wilson(k, n)
    return {"k": int(k), "n": int(n), "%": round(100 * k / n, 2), "alt": round(alt, 2), "ust": round(ust, 2)}


def hucreler(kume, df, p, esik_dizi, etiket_esik):
    """df'nin her (NET grubu x tur) hucresi icin kacan ve yanlis alarm (+ Wilson)."""
    y, dll, net = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1, df.NET_mi.to_numpy() == 1
    satirlar = []
    for grup, gm in ((".NET", net), (".NET disi", ~net)):
        for tur, tm in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
            m = gm & tm
            zr, zs = m & (y == 1), m & (y == 0)
            if not m.any():
                continue
            kac = oran(int((p[zr] <= esik_dizi[zr]).sum()), int(zr.sum()))
            ya = oran(int((p[zs] > esik_dizi[zs]).sum()), int(zs.sum()))
            auc = round(roc_auc_score(y[m], p[m]), 4) if zr.any() and zs.any() else float("nan")
            satirlar.append({"kume": kume, "esik": etiket_esik, "grup": grup, "tur": tur,
                             **{f"kacan_{a}": v for a, v in kac.items()},
                             **{f"YA_{a}": v for a, v in ya.items()}, "AUC": auc})
    return satirlar


def goster(s):
    def f(on):
        if s[f"{on}_n"] == 0:
            return "—"
        if s[f"{on}_n"] < KUCUK_N:
            return f"{s[f'{on}_k']}/{s[f'{on}_n']} (n<{KUCUK_N}, yorumlanmaz)"
        return f"%{s[f'{on}_%']:.2f} [{s[f'{on}_alt']:.2f}-{s[f'{on}_ust']:.2f}] ({s[f'{on}_k']}/{s[f'{on}_n']})"
    return f"| {s['kume']} | {s['esik']} | {s['grup']} | {s['tur']} | {f('kacan')} | {f('YA')} | {s['AUC']} |"


def esik_dizisi(df, esik):
    return np.where(df.DLL_mi.to_numpy() == 1, esik["DLL"], esik["EXE"])


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    paket = tahmin_et.model_yukle()                       # SHA-256 dogrulamali (Kural 10)
    model, meta = paket["model"], paket["meta"]
    model.set_params(n_jobs=8)                            # yalniz hiz; tahmin degismez
    kolon, esik = meta["ozellikler"], meta["esikler"]
    print(f"[*] model sha256 {meta['model_sha256'][:16]}..., esikler {esik}")

    # --- A: native test kumesi ---
    test = o.yukle(["Win32_test", "Win64_test"])
    print(f"[*] A: {len(test)} satir, hafta {int(test.Hafta.min())}-{int(test.Hafta.max())}, "
          f".NET {int((test.NET_mi == 1).sum())} ({time.monotonic() - t0:.0f} sn)")
    p_a = model.predict_proba(test[kolon])[:, 1]
    e_a = esik_dizisi(test, esik)
    y = test.Etiket.to_numpy()
    for tur, deger in (("EXE", 0), ("DLL", 1)):         # GECIT
        m = test.DLL_mi.to_numpy() == deger
        kac = round(100 * (p_a[m & (y == 1)] <= esik[tur]).mean(), 3)
        ya = round(100 * (p_a[m & (y == 0)] > esik[tur]).mean(), 3)
        bek_k, bek_y = meta["test_bir_kez"][f"{tur}_kacan_%@1"], meta["test_bir_kez"][f"{tur}_test_YA_%@1"]
        if not (np.isclose(kac, bek_k, rtol=0, atol=1e-9) and np.isclose(ya, bek_y, rtol=0, atol=1e-9)):
            sys.exit(f"GECIT BASARISIZ: {tur} kacan {kac} / YA {ya}, meta {bek_k} / {bek_y}")
        print(f"[+] GECIT {tur}: kacan {kac} YA {ya} == meta")
    satirlar = hucreler("A native test", test, p_a, e_a, "tur esigi")
    del test

    # --- B: Dot_Net_test ---
    b = pd.read_csv(DOT_NET_TEST_CSV, usecols=kolon + ["NET_mi", "Etiket", "Hafta"])
    if b[kolon].isna().any().any() or not set(b.Etiket.unique()) <= {0, 1}:
        sys.exit("B: eksik deger ya da beklenmeyen etiket")
    print(f"[*] B: {len(b)} satir, hafta {int(b.Hafta.min())}-{int(b.Hafta.max())}, NET_mi=1 {int((b.NET_mi == 1).sum())}, "
          f"DLL {int((b.DLL_mi == 1).sum())}, zararli {int((b.Etiket == 1).sum())} ({time.monotonic() - t0:.0f} sn)")
    p_b = model.predict_proba(b[kolon].astype("float32"))[:, 1]
    satirlar += hucreler("B Dot_Net_test", b, p_b, esik_dizisi(b, esik), "tur esigi")
    satirlar += hucreler("B Dot_Net_test", b, p_b, np.full(len(b), 0.5), "0,5 (Faz 1 ile ayni)")

    # --- C: dondurulmus yerel set ---
    h = hashlib.sha256(open(YEREL_DOGRULAMA_5635_CSV, "rb").read()).hexdigest()
    if h != meta["yerel_dogrulama_seti"]["sha256"]:
        print(f"[!] C ATLANDI: yerel set sha256 tutmuyor ({h[:16]})")
    else:
        c = pd.read_csv(YEREL_DOGRULAMA_5635_CSV)
        p_c = model.predict_proba(c[kolon])[:, 1]
        c["Etiket"] = 0
        satirlar += hucreler("C yerel (zararsiz)", c, p_c, esik_dizisi(c, esik), "tur esigi")
        print(f"[*] C: {len(c)} satir, sha256 tutuyor, .NET {int((c.NET_mi == 1).sum())}")

    df = pd.DataFrame(satirlar)
    df.to_csv(os.path.join(BURASI, "net_olcum.csv"), index=False)
    print("\n| kume | esik | grup | tur | kacan zararli % [Wilson %95] (k/n) | yanlis alarm % [Wilson %95] (k/n) | AUC |")
    print("|---|---|---|---|---|---|---|")
    for s in satirlar:
        print(goster(s))

    # --- Yorum kurallari (on kayit) ---
    print("\n=== Yorum kurallari (on_kayit_net.md) ===")
    for etk in ("tur esigi", "0,5 (Faz 1 ile ayni)"):
        s = df[(df.kume == "B Dot_Net_test") & (df.esik == etk) & (df.grup == ".NET") & (df.tur == "hepsi")].iloc[0]
        karar = "AZALTIYOR" if s.kacan_ust < FAZ1_NET_KACAN else "azalttigi gosterilemedi"
        print(f"1) B, {etk}: native kacan %{s['kacan_%']} [ust {s.kacan_ust}] vs Faz 1 %{FAZ1_NET_KACAN} -> {karar}")
    a = df[df.kume == "A native test"]
    for tur in ("EXE", "DLL"):
        n_, d_ = a[(a.grup == ".NET") & (a.tur == tur)], a[(a.grup == ".NET disi") & (a.tur == tur)]
        if n_.empty:
            continue
        n_, d_ = n_.iloc[0], d_.iloc[0]
        for on, ad in (("kacan", "kacan"), ("YA", "yanlis alarm")):
            if n_[f"{on}_n"] < KUCUK_N:
                print(f"2) A {tur} {ad}: .NET n={n_[f'{on}_n']} < {KUCUK_N} -> yorumlanmaz")
            elif n_[f"{on}_alt"] > d_[f"{on}_ust"]:
                print(f"2) A {tur} {ad}: .NET anlamli olarak DAHA KOTU ({n_[f'{on}_%']} [{n_[f'{on}_alt']}-{n_[f'{on}_ust']}] vs "
                      f"{d_[f'{on}_%']} [{d_[f'{on}_alt']}-{d_[f'{on}_ust']}])")
            elif n_[f"{on}_ust"] < d_[f"{on}_alt"]:
                print(f"2) A {tur} {ad}: .NET anlamli olarak DAHA IYI ({n_[f'{on}_%']} vs {d_[f'{on}_%']})")
            else:
                print(f"2) A {tur} {ad}: fark gosterilemedi (araliklar ortusuyor: {n_[f'{on}_%']} "
                      f"[{n_[f'{on}_alt']}-{n_[f'{on}_ust']}] vs {d_[f'{on}_%']} [{d_[f'{on}_alt']}-{d_[f'{on}_ust']}])")
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> net_olcum.csv")
