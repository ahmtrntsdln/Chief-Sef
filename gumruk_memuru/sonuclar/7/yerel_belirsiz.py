"""
Kalici kural (.NET'te esik alti skor BELIRSIZ) yerel kumede ne kadar BELIRSIZ uretiyor - BETIMLEYICI, hukum uretmez.
Kaynak: FAZ1_KAPANIS.md Revizyon 6. Karar icin tahmin_et.karar kullanilir (ikinci kopya yok, Kural 9).
Kume: dondurulmus yerel set (repoda yok, sha256 meta ile dogrulanir; yeniden TARANMAZ). Hepsi zararsiz kabul edilir.
Gecit: uretim esiginde alarm sayilari sonuclar/5/net_sonuc.md C ile ayni (.NET 1/3471, .NET disi 11/2164).
Kullanim: python -u yerel_belirsiz.py <sef_yerel_dogrulama_5635.csv yolu> > yerel_belirsiz.log
"""

import hashlib
import os
import sys

import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))
import ortak_deney as o  # noqa: E402
import tahmin_et as t  # noqa: E402

BEKLENEN = {"net": (3471, 1), "disi": (2164, 11)}
KARARLAR = (t.ZARARSIZ, t.BELIRSIZ, t.OLASI_ZARARLI, t.ZARARLI)


def yuzde(k, n):
    alt, ust = o.wilson(k, n)
    return f"%{100 * k / n:.2f} [{alt:.2f}-{ust:.2f}] ({k}/{n})"


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if len(sys.argv) != 2:
        sys.exit("Kullanim: python yerel_belirsiz.py <csv yolu>")
    paket = t.model_yukle()
    model, meta = paket["model"], paket["meta"]
    model.set_params(n_jobs=8)
    h = hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest()
    if h != meta["yerel_dogrulama_seti"]["sha256"]:
        sys.exit(f"GECIT BASARISIZ: yerel set sha256 {h[:16]} tutmuyor")
    print(f"[+] yerel set sha256 {h[:16]}... == meta; esikler {meta['esikler']}")
    d = pd.read_csv(sys.argv[1])
    p = model.predict_proba(d[meta["ozellikler"]])[:, 1]
    net, dll = d.NET_mi.to_numpy() == 1, d.DLL_mi.to_numpy() == 1
    tur = np.where(dll, "DLL", "EXE")
    esik = np.where(dll, meta["esikler"]["DLL"], meta["esikler"]["EXE"])
    k = np.array([t.karar(float(a), float(e), bool(n), str(u)) for a, e, n, u in zip(p, esik, net, tur)])

    for ad, m in (("net", net), ("disi", ~net)):
        alarm = int((p[m] > esik[m]).sum())
        if (int(m.sum()), alarm) != BEKLENEN[ad]:
            sys.exit(f"GECIT BASARISIZ: {ad} (n, alarm) {(int(m.sum()), alarm)} != {BEKLENEN[ad]}")
    print("[+] alarm sayilari net_sonuc.md C ile ayni (.NET 1/3471, .NET disi 11/2164)\n")

    print("| grup | tur | n | zararsiz | BELIRSIZ | OLASI ZARARLI | ZARARLI |")
    print("|---|---|---|---|---|---|---|")
    for g, gm in ((".NET", net), (".NET disi", ~net), ("hepsi", np.ones_like(net))):
        for u, um in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(net))):
            m = gm & um
            print(f"| {g} | {u} | {int(m.sum())} | " + " | ".join(str(int((k[m] == x).sum())) for x in KARARLAR) + " |")

    print("\nBELIRSIZ orani (Wilson %95; kumeli ornek, aralik iyimser):")
    for g, gm in ((".NET EXE", net & ~dll), (".NET DLL", net & dll), (".NET hepsi", net), ("tum yerel set", np.ones_like(net))):
        print(f"  {g}: {yuzde(int((k[gm] == t.BELIRSIZ).sum()), int(gm.sum()))}")
    karma = d.Karma_Mod.to_numpy() == 1
    print(f"  .NET icinde Karma_Mod: {int((net & karma).sum())}, BELIRSIZ {int((net & karma & (k == t.BELIRSIZ)).sum())}")

    print("\nBELIRSIZ dosyalarda skor dagilimi (esige uzaklik; tek esik yerine bolge dusunen Is 3 icin):")
    b = k == t.BELIRSIZ
    for alt, ust, et in ((0.0, 0.2, "skor <= 0,2"), (0.2, 0.5, "0,2 < skor <= 0,5"), (0.5, 1.01, "0,5 < skor <= esik")):
        m = b & (p > alt if alt else p >= 0) & (p <= ust)
        print(f"  {et}: {yuzde(int(m.sum()), int(b.sum()))}")
    print(f"  ozet: medyan {np.median(p[b]):.3f}, ceyrekler {np.quantile(p[b], .25):.3f} / {np.quantile(p[b], .75):.3f}, en yuksek {p[b].max():.3f}")
