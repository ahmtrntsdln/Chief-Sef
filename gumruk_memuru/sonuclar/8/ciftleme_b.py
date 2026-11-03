"""
Is 7 (b) - 3/, 5/, 6/ sonuclari essiz dosyalarla (on kayit: ciftleme_on_kayit.md, olcumden once).

Esikler ve tau'lar YAYINLANDIGI GIBI sabit. Her bolum once CIFTLI kumede yayinlanan sayilari birebir
yeniden uretir (G2-G4), sonra ayni tahminleri Dosya_Adi (sha256'nin ilk 12 hanesi) ile tekillestirip
yeniden hesaplar. Tekillestirme: ilk kopya tutulur.
Sapma (sonucta yazili): V48_* ara modelleri meta'da hash'i olmadigi icin YUKLENMEZ (Kritik Kural 10).
Kullanim: python ciftleme_b.py   (log icin > ciftleme_b.log)
"""

import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

BURASI = os.path.dirname(os.path.abspath(__file__))
for alt in ("..", os.path.join("..", "5"), os.path.join("..", "6"), os.path.join("..", "..")):
    sys.path.insert(0, os.path.join(BURASI, alt))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from ember2024_net_cikar import cikti_yolu  # noqa: E402
from net_dogrulama import EMBER2024_NET_CSV, MODELLER, yeni_model  # noqa: E402
from net_model import DIZGELI, DIZGELI_TIPLI, EGITIM_ORNEK  # noqa: E402
from net_olcum import FAZ1_NET_KACAN, KUCUK_N, esik_dizisi, hucreler  # noqa: E402
from sef_ayarlar import (EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV, EMBER2018_CIKTI_KLASORU,  # noqa: E402
                         YEREL_DOGRULAMA_5635_CSV)
from uzman_native import DOGRULAMA_HAFTA, HEDEFLER, egit, olc, ortusuyor  # noqa: E402

SATIRLAR = []          # tum hucreler -> ciftleme_b.csv
HUKUMLER = []          # (bolum, hucre, ciftli cumle, tekil cumle)


def dur(mesaj):
    print(f"[!] GECIT BASARISIZ: {mesaj}")
    return False


def ilk_kopya(adlar):
    """Dosya_Adi dizisi -> ilk kopya maskesi."""
    return ~pd.Series(adlar).duplicated(keep="first").to_numpy()


def kopya_yapisi(ad, df, kolon):
    """G1: ayni sha'nin kopyalarinda etiket ve model sutunlari birebir mi; kopya dagilimi."""
    h = pd.util.hash_pandas_object(df[kolon + ["Etiket"]], index=False).to_numpy()
    g = pd.DataFrame({"a": df.Dosya_Adi.to_numpy(), "h": h}).groupby("a").h
    celiski = int((g.nunique() > 1).sum())
    dagilim = g.size().value_counts().sort_index().to_dict()
    print(f"[{'+' if celiski == 0 else '!'}] G1 {ad}: satir {len(df)}, essiz {int(g.ngroups)}, "
          f"kopya dagilimi {dagilim}, celiskili sha {celiski}")
    return celiski == 0


def delta_max(adlar, maske):
    """Hucredeki kopya sayisi != 2 olan sha'larin en kotu etkisi (yuzde puan): 100 * D / (2N + D)."""
    c = pd.Series(adlar[maske]).value_counts()
    d = float((c - 2).abs().sum())
    return 100 * d / (2 * len(c) + d) if len(c) else 0.0


def karsilastir(bolum, ciftli, tekil, adlar_c, maskeler):
    """ciftli/tekil: hucreler()-bicimli satir listeleri, ayni sirada. maskeler: her satirin (zr, zs) maskesi (ciftli)."""
    for c, t, (zr, zs) in zip(ciftli, tekil, maskeler):
        for on, m in (("kacan", zr), ("YA", zs)):
            if c[f"{on}_n"] == 0:
                continue
            dm = delta_max(adlar_c, m)
            fark = abs(c[f"{on}_%"] - t[f"{on}_%"])
            SATIRLAR.append({
                "bolum": bolum, "hucre": " | ".join(str(c[k]) for k in ("kume", "esik", "grup", "tur") if k in c),
                "olcu": on, "ciftli_k": c[f"{on}_k"], "ciftli_n": c[f"{on}_n"], "ciftli_%": c[f"{on}_%"],
                "ciftli_alt": c[f"{on}_alt"], "ciftli_ust": c[f"{on}_ust"],
                "tekil_k": t[f"{on}_k"], "tekil_n": t[f"{on}_n"], "tekil_%": t[f"{on}_%"],
                "tekil_alt": t[f"{on}_alt"], "tekil_ust": t[f"{on}_ust"],
                "fark_puan": round(fark, 3), "delta_max_puan": round(dm, 3),
                "nokta": "ayni (fark kopya dagilimindan)" if fark <= dm + 0.005 else "BEKLENMEYEN FARK"})


def hukum_kaydet(bolum, hucre, c, t):
    HUKUMLER.append({"bolum": bolum, "hucre": hucre, "ciftli": c, "tekil": t,
                     "durum": "hukum ayni" if c == t else "HUKUM DEGISTI"})


# ---------------------------------------------------------------- 5/ kurallari (net_olcum.py ile ayni mantik)
def net_kural1(df, etk):
    s = df[(df.kume == "B Dot_Net_test") & (df.esik == etk) & (df.grup == ".NET") & (df.tur == "hepsi")].iloc[0]
    return "AZALTIYOR" if s.kacan_ust < FAZ1_NET_KACAN else "azalttigi gosterilemedi"


def net_kural2(df, tur, on):
    a = df[df.kume == "A native test"]
    n_, d_ = a[(a.grup == ".NET") & (a.tur == tur)].iloc[0], a[(a.grup == ".NET disi") & (a.tur == tur)].iloc[0]
    if n_[f"{on}_n"] < KUCUK_N:
        return "yorumlanmaz (n<30)"
    if n_[f"{on}_alt"] > d_[f"{on}_ust"]:
        return ".NET anlamli olarak DAHA KOTU"
    if n_[f"{on}_ust"] < d_[f"{on}_alt"]:
        return ".NET anlamli olarak DAHA IYI"
    return "fark gosterilemedi"


def bolum_3_5(paket):
    """3/ son model testte + 5/ A ve B (ayni native tahminleri)."""
    model, meta = paket["model"], paket["meta"]
    kolon, esik = meta["ozellikler"], meta["esikler"]
    test = o.yukle(["Win32_test", "Win64_test"])
    adlar = pd.concat([pd.read_parquet(os.path.join(o.EMBER2024_PARQUET_KLASORU, f"{a}.parquet"), columns=["Dosya_Adi", "Karma_Mod"])
                       for a in ("Win32_test", "Win64_test")], ignore_index=True)
    if len(adlar) != len(test):
        sys.exit("Hata: Dosya_Adi satir sayisi tutmuyor")
    test["Dosya_Adi"], test["Karma_Mod"] = adlar.Dosya_Adi.to_numpy(), adlar.Karma_Mod.to_numpy()
    g1 = kopya_yapisi("Win32/Win64 test", test, kolon)
    p = model.predict_proba(test[kolon])[:, 1]
    y, dll = test.Etiket.to_numpy(), test.DLL_mi.to_numpy() == 1
    e = esik_dizisi(test, esik)
    t1 = ilk_kopya(test.Dosya_Adi.to_numpy())

    # --- 3/: test_bir_kez ---
    print("\n=== 3/ son model, test (hafta 52-63) ===")
    g2 = True
    for tur, m in (("EXE", ~dll), ("DLL", dll)):
        kac = round(100 * (p[m & (y == 1)] <= esik[tur]).mean(), 3)
        ya = round(100 * (p[m & (y == 0)] > esik[tur]).mean(), 3)
        bk, by = meta["test_bir_kez"][f"{tur}_kacan_%@1"], meta["test_bir_kez"][f"{tur}_test_YA_%@1"]
        if (kac, ya) != (bk, by):
            g2 = dur(f"G2 {tur} kacan/YA {kac}/{ya} != meta {bk}/{by}")
    auc = round(roc_auc_score(y, p), 4)
    if auc != meta["test_bir_kez"]["genel_AUC"]:
        g2 = dur(f"G2 AUC {auc} != {meta['test_bir_kez']['genel_AUC']}")
    if g1 and g2:
        print("[+] G2: ciftli test meta test_bir_kez ile birebir (kacan, YA, AUC)")
        c3, t3, mk = [], [], []
        for tur, m in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
            for maske, liste in ((np.ones_like(t1), c3), (t1, t3)):
                mm = m & maske
                zr, zs = mm & (y == 1), mm & (y == 0)
                ka, ya_ = int((p[zr] <= e[zr]).sum()), int((p[zs] > e[zs]).sum())
                r = {"kume": "3/ test", "esik": "uretim", "tur": tur}
                for on, k, n in (("kacan", ka, int(zr.sum())), ("YA", ya_, int(zs.sum()))):
                    alt, ust = o.wilson(k, n)
                    r.update({f"{on}_k": k, f"{on}_n": n, f"{on}_%": round(100 * k / n, 3),
                              f"{on}_alt": round(alt, 3), f"{on}_ust": round(ust, 3)})
                r["AUC"] = round(roc_auc_score(y[mm], p[mm]), 5)
                liste.append(r)
            mk.append((m & (y == 1), m & (y == 0)))
        karsilastir("3/ son model", c3, t3, test.Dosya_Adi.to_numpy(), mk)
        for c, t in zip(c3, t3):
            print(f"  {c['tur']:<5} kacan %{c['kacan_%']} [{c['kacan_alt']}-{c['kacan_ust']}] ({c['kacan_k']}/{c['kacan_n']}) -> "
                  f"%{t['kacan_%']} [{t['kacan_alt']}-{t['kacan_ust']}] ({t['kacan_k']}/{t['kacan_n']}) | "
                  f"YA %{c['YA_%']} ({c['YA_k']}/{c['YA_n']}) -> %{t['YA_%']} [{t['YA_alt']}-{t['YA_ust']}] ({t['YA_k']}/{t['YA_n']}) | "
                  f"AUC {c['AUC']} -> {t['AUC']}")
    else:
        print("[!] 3/: hukum yok (gecit)")

    # --- 5/ A ---
    print("\n=== 5/ A: native test .NET alt grubu ===")
    onceki = pd.read_csv(os.path.join(BURASI, "..", "5", "net_olcum.csv"))
    c_a = hucreler("A native test", test, p, e, "tur esigi")
    g3 = g1
    for s in c_a:
        r = onceki[(onceki.kume == s["kume"]) & (onceki.esik == s["esik"]) & (onceki.grup == s["grup"]) & (onceki.tur == s["tur"])].iloc[0]
        if (s["kacan_k"], s["kacan_n"], s["YA_k"], s["YA_n"]) != (r.kacan_k, r.kacan_n, r.YA_k, r.YA_n):
            g3 = dur(f"G3 A {s['grup']} {s['tur']}")
    tek = test[t1].reset_index(drop=True)
    t_a = hucreler("A native test", tek, p[t1], e[t1], "tur esigi")
    net = test.NET_mi.to_numpy() == 1
    mk_a = []
    for grup, gm in ((".NET", net), (".NET disi", ~net)):
        for tur, tm in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
            if (gm & tm).any():
                mk_a.append((gm & tm & (y == 1), gm & tm & (y == 0)))
    return test, p, c_a, t_a, mk_a, g3


def bolum_5b(paket, c_a, t_a, adlar_a, mk_a, g3_a):
    model, meta = paket["model"], paket["meta"]
    kolon, esik = meta["ozellikler"], meta["esikler"]
    b = pd.read_csv(EMBER2024_NET_CSV, usecols=kolon + ["NET_mi", "Etiket", "Hafta", "Dosya_Adi", "Karma_Mod"], keep_default_na=False)
    g1 = kopya_yapisi("Dot_Net_test", b, kolon + ["NET_mi", "Karma_Mod"])
    p_b = model.predict_proba(b[kolon].astype("float32"))[:, 1]
    onceki = pd.read_csv(os.path.join(BURASI, "..", "5", "net_olcum.csv"))
    e_b, e_05 = esik_dizisi(b, esik), np.full(len(b), 0.5)
    c_b = hucreler("B Dot_Net_test", b, p_b, e_b, "tur esigi") + hucreler("B Dot_Net_test", b, p_b, e_05, "0,5 (Faz 1 ile ayni)")
    g3 = g1 and g3_a
    for s in c_b:
        r = onceki[(onceki.kume == s["kume"]) & (onceki.esik == s["esik"]) & (onceki.grup == s["grup"]) & (onceki.tur == s["tur"])].iloc[0]
        if (s["kacan_k"], s["kacan_n"], s["YA_k"], s["YA_n"]) != (r.kacan_k, r.kacan_n, r.YA_k, r.YA_n):
            g3 = dur(f"G3 B {s['esik']} {s['grup']} {s['tur']}")
    t1 = ilk_kopya(b.Dosya_Adi.to_numpy())
    bt = b[t1].reset_index(drop=True)
    t_b = hucreler("B Dot_Net_test", bt, p_b[t1], e_b[t1], "tur esigi") + hucreler("B Dot_Net_test", bt, p_b[t1], e_05[t1], "0,5 (Faz 1 ile ayni)")
    y, dll, net = b.Etiket.to_numpy(), b.DLL_mi.to_numpy() == 1, b.NET_mi.to_numpy() == 1
    mk_b = []
    for _ in ("tur", "0,5"):
        for grup, gm in ((".NET", net), (".NET disi", ~net)):
            for tur, tm in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
                if (gm & tm).any():
                    mk_b.append((gm & tm & (y == 1), gm & tm & (y == 0)))
    if not g3:
        print("[!] 5/: hukum yok (gecit)")
        return b, p_b, False
    print("[+] G3: net_olcum.csv A ve B satirlari ciftli kumede birebir")
    karsilastir("5/ A", c_a, t_a, adlar_a, mk_a)
    karsilastir("5/ B", c_b, t_b, b.Dosya_Adi.to_numpy(), mk_b)
    dc, dt = pd.DataFrame(c_a + c_b), pd.DataFrame(t_a + t_b)
    for etk in ("tur esigi", "0,5 (Faz 1 ile ayni)"):
        hukum_kaydet("5/ kural 1", f"B {etk}", net_kural1(dc, etk), net_kural1(dt, etk))
    for tur in ("EXE", "DLL"):
        for on in ("kacan", "YA"):
            hukum_kaydet("5/ kural 2", f"A {tur} {on}", net_kural2(dc, tur, on), net_kural2(dt, tur, on))
    return b, p_b, True


def bolum_5ek(paket, b, p_n, g3):
    """esit_ya.py: Faz 1 (ayni kod) ve native; tau SABIT (0,76 / 0,43 / native sabit)."""
    print("\n=== 5/ EK esit_ya: Faz 1 vs native, tau sabit ===")
    ember = pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)], ignore_index=True)
    y18 = ember["Etiket"].to_numpy()
    idx_tr, _ = train_test_split(np.arange(len(y18)), test_size=0.2, stratify=y18, random_state=42)
    kol_f = MODELLER["A (5 ozellik)"]
    faz1 = yeni_model().fit(ember.iloc[idx_tr][kol_f], y18[idx_tr])
    bb = pd.read_csv(EMBER2024_NET_CSV, usecols=kol_f + ["Dosya_Adi", "Etiket", "DLL_mi"], keep_default_na=False)
    if not (bb.Dosya_Adi.to_numpy() == b.Dosya_Adi.to_numpy()).all():
        sys.exit("Hata: B satir sirasi tutmuyor")
    p_f = faz1.predict_proba(bb[kol_f])[:, 1]
    y, dll = b.Etiket.to_numpy(), b.DLL_mi.to_numpy() == 1
    esik = paket["meta"]["esikler"]
    noktalar = {   # ad: (skor, esik dizisi)
        "Faz 1 @0,5": (p_f, np.full(len(b), 0.5)),
        "native @0,76": (p_n, np.full(len(b), 0.76)),
        "Faz 1 @0,43": (p_f, np.full(len(b), 0.43)),
        "native sabit tur esikleri": (p_n, esik_dizisi(b, esik)),
    }
    beklenen = {"Faz 1 @0,5": {"hepsi": (55662, 274)}, "native @0,76": {"hepsi": (35872, None), "EXE": (30996, 106), "DLL": (4876, 166)},
                "Faz 1 @0,43": {"hepsi": (53634, None), "EXE": (48424, 318), "DLL": (5210, 254)},
                "native sabit tur esikleri": {"hepsi": (29864, None)}}
    t1 = ilk_kopya(b.Dosya_Adi.to_numpy())
    g = g3
    sonuc = {}
    for ad, (s, e) in noktalar.items():
        for maske, etk in ((np.ones(len(b), bool), "ciftli"), (t1, "tekil")):
            for tur, tm in (("hepsi", np.ones_like(dll)), ("EXE", ~dll), ("DLL", dll)):
                m = maske & tm
                zr, zs = m & (y == 1), m & (y == 0)
                k, ya_k = int((s[zr] <= e[zr]).sum()), int((s[zs] > e[zs]).sum())
                sonuc[(ad, etk, tur)] = (k, int(zr.sum()), ya_k, int(zs.sum()))
                if etk == "ciftli" and tur in beklenen[ad]:
                    bk, by = beklenen[ad][tur]
                    if k != bk or (by is not None and ya_k != by):
                        g = dur(f"G3 esit_ya {ad} {tur}: {k}/{ya_k} != {bk}/{by}")
    if not g:
        print("[!] 5/ EK: hukum yok (gecit)")
        return
    print("[+] G3: esit_ya.log k/n'leri ciftli kumede birebir")
    adlar = b.Dosya_Adi.to_numpy()
    for ad in noktalar:
        for tur, tm in (("hepsi", np.ones_like(dll)), ("EXE", ~dll), ("DLL", dll)):
            kc, nc, yc, mc = sonuc[(ad, "ciftli", tur)]
            kt, nt, yt, mt = sonuc[(ad, "tekil", tur)]
            c = {"kume": "5/ EK B", "esik": ad, "tur": tur}
            t = dict(c)
            for d, (k, n, yk, yn) in ((c, (kc, nc, yc, mc)), (t, (kt, nt, yt, mt))):
                for on, kk, nn in (("kacan", k, n), ("YA", yk, yn)):
                    alt, ust = o.wilson(kk, nn)
                    d.update({f"{on}_k": kk, f"{on}_n": nn, f"{on}_%": round(100 * kk / nn, 3),
                              f"{on}_alt": round(alt, 3), f"{on}_ust": round(ust, 3)})
            karsilastir("5/ EK", [c], [t], adlar, [(tm & (y == 1), tm & (y == 0))])
    for etk in ("ciftli", "tekil"):
        k, n, _, _ = sonuc[("native @0,76", etk, "hepsi")]
        kf, nf, _, _ = sonuc[("Faz 1 @0,5", etk, "hepsi")]
        r1 = "native DAHA AZ" if o.wilson(k, n)[1] < o.wilson(kf, nf)[0] else "fark gosterilemedi"
        k2, n2, _, _ = sonuc[("native sabit tur esikleri", etk, "hepsi")]
        kf2, nf2, _, _ = sonuc[("Faz 1 @0,43", etk, "hepsi")]
        r2 = "native DAHA AZ" if o.wilson(k2, n2)[1] < o.wilson(kf2, nf2)[0] else "fark gosterilemedi"
        sonuc[("kural", etk)] = (r1, r2)
    hukum_kaydet("5/ EK", "birincil (Faz 1 YA'sinda)", sonuc[("kural", "ciftli")][0], sonuc[("kural", "tekil")][0])
    hukum_kaydet("5/ EK", "ikincil (native sabit YA'sinda)", sonuc[("kural", "ciftli")][1], sonuc[("kural", "tekil")][1])


def bolum_6(paket):
    print("\n=== 6/ uzman (M2, M2d) vs native, Dot_Net_test ===")
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    hucre_min = int(havuz.groupby(["DLL_mi", "Etiket"]).size().min())
    m2 = egit(havuz.groupby("Etiket", group_keys=False).sample(n=EGITIM_ORNEK // 2, random_state=42), DIZGELI)
    m2d = egit(havuz.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=hucre_min, random_state=42), DIZGELI_TIPLI)
    nat = paket["model"]
    nk = paket["meta"]["ozellikler"]
    skor = {
        "M2 (uzman, kestirmeli)": (m2.predict_proba(dog[DIZGELI])[:, 1], m2.predict_proba(test[DIZGELI])[:, 1]),
        "M2d (uzman, tip-ici)": (m2d.predict_proba(dog[DIZGELI_TIPLI])[:, 1], m2d.predict_proba(test[DIZGELI_TIPLI])[:, 1]),
        "native": (nat.predict_proba(dog[nk].astype("float32"))[:, 1], nat.predict_proba(test[nk].astype("float32"))[:, 1]),
    }
    onceki = pd.read_csv(os.path.join(BURASI, "..", "6", "uzman_native.csv"))
    t1 = ilk_kopya(test.Dosya_Adi.to_numpy())
    tt = test[t1].reset_index(drop=True)
    c_s, t_s, g4 = [], [], True
    for h in HEDEFLER:
        for ad, (pd_, pt) in skor.items():
            for c, t in zip(olc(ad, h, pd_, dog, pt, test), olc(ad, h, pd_, dog, pt[t1], tt)):
                r = onceki[(onceki.model == ad) & (onceki["hedef_YA_%"] == h) & (onceki.tur == c["tur"])].iloc[0]
                esik_farkli = c["tur"] != "hepsi" and not np.isclose(float(c["esik"]), float(r.esik), rtol=0, atol=1e-9)
                if (c["kacan_k"], c["YA_k"]) != (r.kacan_k, r.YA_k) or esik_farkli:
                    g4 = dur(f"G4 H {h} {ad} {c['tur']}")
                c_s.append(c)
                t_s.append(t)
    if not g4:
        print("[!] 6/: hukum yok (gecit)")
        return
    print("[+] G4: uzman_native.csv 18 satir ciftli kumede birebir")
    y, dll = test.Etiket.to_numpy(), test.DLL_mi.to_numpy() == 1
    mk = []
    for _h in HEDEFLER:
        for _ad in skor:
            for tm in (~dll, dll, np.ones_like(dll)):
                mk.append((tm & (y == 1), tm & (y == 0)))
    for c, t in zip(c_s, t_s):
        c["kume"] = t["kume"] = f"6/ H {c['hedef_YA_%']} {c['model']}"
    karsilastir("6/", c_s, t_s, test.Dosya_Adi.to_numpy(), mk)
    dc, dt = pd.DataFrame(c_s), pd.DataFrame(t_s)

    def kural(df, h, uzman, tur):
        u = df[(df["hedef_YA_%"] == h) & (df.model == uzman) & (df.tur == tur)].iloc[0]
        n = df[(df["hedef_YA_%"] == h) & (df.model == "native") & (df.tur == tur)].iloc[0]
        if not ortusuyor(u, n, "YA"):
            return "esit YA SAGLANAMADI -> hukum yok"
        if ortusuyor(u, n, "kacan"):
            return "fark gosterilemedi"
        return f"{'UZMAN' if u['kacan_%'] < n['kacan_%'] else 'NATIVE'} daha az kaciriyor"
    for h in HEDEFLER:
        for uzman in ("M2 (uzman, kestirmeli)", "M2d (uzman, tip-ici)"):
            for tur in ("EXE", "DLL", "hepsi"):
                hukum_kaydet("6/", f"H {h} {uzman} {tur}", kural(dc, h, uzman, tur), kural(dt, h, uzman, tur))


def betimleyici():
    print("\n=== Betimleyici ===")
    y = pd.read_csv(YEREL_DOGRULAMA_5635_CSV)
    print(f"  yerel set: {len(y)} satir, 94 sutunda birebir ayni satir (ilk haric) {int(y.duplicated().sum())}; "
          f".NET icinde {int(y[y.NET_mi == 1].duplicated().sum())}")
    for ad, yol in (("EMBER 2018 train (C:)", os.path.join(EMBER2018_CIKTI_KLASORU, "ember2018_train_ozellik.csv")),
                    ("EMBER 2018 test (C:)", os.path.join(EMBER2018_CIKTI_KLASORU, "ember2018_test_ozellik.csv")),
                    ("repo zararli 5700", EMBER_ZARARLI_CSV), ("repo EMBER zararsiz 5700", EMBER_ZARARSIZ_CSV)):
        if not os.path.exists(yol):
            print(f"  {ad}: dosya yok ({yol})")
            continue
        d = pd.read_csv(yol, usecols=["Dosya_Adi"], keep_default_na=False)
        print(f"  {ad}: satir {len(d)}, essiz Dosya_Adi {d.Dosya_Adi.nunique()}")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    paket = tahmin_et.model_yukle()
    paket["model"].set_params(n_jobs=8)
    print(f"[*] native model sha256 {paket['meta']['model_sha256'][:16]}... (Kural 10)")
    print("[*] SAPMA: V48_RF_E3_300000_42 / 483224_42 YUKLENMEDI - meta'da hash yok (Kural 10). "
          "483.224 hucresi son modelle ayni tarif (son model kapsar); 300.000 icin yapisal arguman.")
    test, p, c_a, t_a, mk_a, g3_a = bolum_3_5(paket)
    b, p_b, g3 = bolum_5b(paket, c_a, t_a, test.Dosya_Adi.to_numpy(), mk_a, g3_a)
    del test, p
    bolum_5ek(paket, b, p_b, g3)
    bolum_6(paket)
    betimleyici()

    df = pd.DataFrame(SATIRLAR)
    df.to_csv(os.path.join(BURASI, "ciftleme_b.csv"), index=False)
    print(f"\n=== Nokta tahmini (kural 1): {len(df)} olcu; BEKLENMEYEN FARK {int((df.nokta != 'ayni (fark kopya dagilimindan)').sum())} ===")
    if (df.nokta != "ayni (fark kopya dagilimindan)").any():
        print(df[df.nokta != "ayni (fark kopya dagilimindan)"].to_string())
    print(f"  en buyuk fark {df.fark_puan.max():.3f} puan; en buyuk delta_max {df.delta_max_puan.max():.3f}")
    h = pd.DataFrame(HUKUMLER)
    h.to_csv(os.path.join(BURASI, "ciftleme_b_hukum.csv"), index=False)
    print(f"\n=== Hukum (kural 2): {len(h)} kural hucresi; HUKUM DEGISTI {int((h.durum != 'hukum ayni').sum())} ===")
    for _, r in h.iterrows():
        print(f"  [{r.durum}] {r.bolum} | {r.hucre}: {r.ciftli} -> {r.tekil}")
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> ciftleme_b.csv, ciftleme_b_hukum.csv")
