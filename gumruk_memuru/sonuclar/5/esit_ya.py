"""
Adim 5b - Faz 1 ve native model Dot_Net_test'te ESIT yanlis alarmda (on kayit: on_kayit_esit_ya.md).

Faz 1: net_dogrulama.py'nin "A (5 ozellik)" modeli, ayni kodla yeniden uretilir.
   GECIT: esik 0,5'te kacan 1 ondaliga yuvarlaninca 92,8 olmali.
Native: kayitli son model (SHA-256 dogrulamali), yeniden egitilmez.
tau, test kumesinden secilen ROC calisma noktasidir; uretim esigi DEGIL (Kural 6).
Kullanim: python esit_ya.py   (log icin > esit_ya.log)
"""

import os
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from net_dogrulama import EMBER2024_NET_CSV, MODELLER, yeni_model  # noqa: E402
from sef_ayarlar import EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV  # noqa: E402

NATIVE_SABIT_YA = 1.05        # net_sonuc.md: native, tur esiklerinde, B "hepsi" yanlis alarm %


def oran(k, n):
    alt, ust = o.wilson(k, n)
    return f"%{100 * k / n:.2f} [{alt:.2f}-{ust:.2f}] ({k}/{n})", alt, ust


def esik_bul(p_zs, hedef_yuzde):
    """pay(p_zs > t) <= hedef olan EN KUCUK t (aday: farkli skorlar) ve bir alt adim."""
    s = np.sort(p_zs)
    aday = np.unique(s)
    ya = 100 * (len(s) - np.searchsorted(s, aday, side="right")) / len(s)   # pay(p > t)
    uygun = np.nonzero(ya <= hedef_yuzde + 1e-12)[0]
    i = uygun[0]
    return aday[i], ya[i], (aday[i - 1], ya[i - 1]) if i > 0 else (None, None)


def calisma_noktasi(ad, y, p, dll, hedef):
    t, ya_t, (t_alt, ya_alt) = esik_bul(p[y == 0], hedef)
    zr = y == 1
    kac = int((p[zr] <= t).sum())
    metin, alt, ust = oran(kac, int(zr.sum()))
    print(f"  {ad}: hedef YA <= %{hedef:.3f} -> tau {t:.4f}, gerceklesen YA %{ya_t:.3f}, kacan {metin}")
    if t_alt is not None:
        print(f"      bir alt adim: tau {t_alt:.4f} -> YA %{ya_alt:.3f} (hedefi asar), "
              f"kacan %{100 * (p[zr] <= t_alt).mean():.2f}")
    for tur, m in (("EXE", ~dll), ("DLL", dll)):
        k_ya = int((p[m & (y == 0)] > t).sum())
        k_kac = int((p[m & zr] <= t).sum())
        print(f"      {tur}: kacan {oran(k_kac, int((m & zr).sum()))[0]} | YA {oran(k_ya, int((m & (y == 0)).sum()))[0]}")
    return alt, ust


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    b = pd.read_csv(EMBER2024_NET_CSV, keep_default_na=False)
    y = b.Etiket.to_numpy()
    dll = b.DLL_mi.to_numpy() == 1
    print(f"[*] B: {len(b)} satir, zararli {int((y == 1).sum())}, zararsiz {int((y == 0).sum())}")

    # --- Faz 1 (net_dogrulama A, ayni kod) ---
    ember = pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)], ignore_index=True)
    y18 = ember["Etiket"].to_numpy()
    idx_tr, _ = train_test_split(np.arange(len(y18)), test_size=0.2, stratify=y18, random_state=42)
    kol_f = MODELLER["A (5 ozellik)"]
    faz1 = yeni_model().fit(ember.iloc[idx_tr][kol_f], y18[idx_tr])
    p_f = faz1.predict_proba(b[kol_f])[:, 1]
    kac_f = int((p_f[y == 1] <= 0.5).sum())
    if round(100 * kac_f / int((y == 1).sum()), 1) != 92.8:
        sys.exit(f"GECIT BASARISIZ: Faz 1 kacan %{100 * kac_f / (y == 1).sum():.3f} != 92,8")
    ya_f_k = int((p_f[y == 0] > 0.5).sum())
    ya_f = 100 * ya_f_k / int((y == 0).sum())
    print(f"[+] GECIT: Faz 1 kacan {oran(kac_f, int((y == 1).sum()))[0]} (belge: 92,8)")
    print(f"[*] Faz 1 yanlis alarm (esik 0,5): {oran(ya_f_k, int((y == 0).sum()))[0]} | AUC {roc_auc_score(y, p_f):.4f}")
    faz1_alt = oran(kac_f, int((y == 1).sum()))[1]

    # --- Native (kayitli model) ---
    paket = tahmin_et.model_yukle()
    paket["model"].set_params(n_jobs=8)
    p_n = paket["model"].predict_proba(b[paket["meta"]["ozellikler"]].astype("float32"))[:, 1]
    print(f"[*] native AUC {roc_auc_score(y, p_n):.4f}")

    print("\n=== Birincil: native model, Faz 1'in yanlis alarminda ===")
    n_alt, n_ust = calisma_noktasi("native", y, p_n, dll, ya_f)
    print(f"  Faz 1 (esik 0,5): kacan alt sinir %{faz1_alt:.2f}")
    print("  KURAL: " + ("esit yanlis alarmda native .NET'te DAHA AZ kaciriyor" if n_ust < faz1_alt
                         else "fark gosterilemedi"))

    print(f"\n=== Ikincil: Faz 1, native'in sabit esiklerdeki yanlis alarminda (%{NATIVE_SABIT_YA}) ===")
    f_alt, f_ust = calisma_noktasi("Faz 1", y, p_f, dll, NATIVE_SABIT_YA)
    k_n = int((p_n[(y == 1)] <= np.where(dll, paket["meta"]["esikler"]["DLL"], paket["meta"]["esikler"]["EXE"])[y == 1]).sum())
    metin, n2_alt, n2_ust = oran(k_n, int((y == 1).sum()))
    print(f"  native sabit tur esikleri: kacan {metin}")
    print("  KURAL: " + ("native DAHA AZ kaciriyor" if n2_ust < f_alt else "fark gosterilemedi"))
