"""
Is 2(b) - M2d'nin gercek akistaki .NET alt kumesinde (A kumesi) performansi; native ile McNemar.
On kayit: is2b_on_kayit.md (commit 75e5216, olcumden once).

M2d uzman_native.py tarifiyle yeniden egitilir (hafta 0-47, 4 x 24.104, tohum 42; ciftli havuz); esikler
hafta 48-51 dogrulama diliminden, uzman_native.csv ile AYNI olmali (K2/K3). Tum sonuc sayilari TEKIL
kumeden; ciftli kume yalniz gecitlerde. Gecit tutmazsa olcum DURUR, sonuc tablosu yazilmaz.
Kullanim: python -u is2b_a_kumesi.py > is2b_a_kumesi.log
"""

import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

BURASI = os.path.dirname(os.path.abspath(__file__))
for alt in ("..", os.path.join("..", "2c"), os.path.join("..", "5"), os.path.join("..", "6"), os.path.join("..", "..")):
    sys.path.insert(0, os.path.join(BURASI, alt))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from ember2024_net_cikar import cikti_yolu  # noqa: E402
from is2a_yerel_net import BEKLENEN_ESIK, M2D, NATIVE, esikler  # noqa: E402
from karar_tablosu import mcnemar  # noqa: E402
from net_model import DIZGELI_TIPLI  # noqa: E402
from sef_ayarlar import EMBER2024_PARQUET_KLASORU  # noqa: E402
from uzman_native import DOGRULAMA_HAFTA, HEDEFLER, egit, olc  # noqa: E402

KUCUK_N, MCNEMAR_MIN, ALFA = 30, 6, 0.05
# (DLL_mi, Etiket) -> satir / essiz sayisi (on kayit, K1)
BEKLENEN_CIFTLI = {(0, 0): 208, (1, 0): 1054, (0, 1): 3278, (1, 1): 308}
BEKLENEN_TEKIL = {(0, 0): 101, (1, 0): 517, (0, 1): 1639, (1, 1): 154}
# Karma_Mod -> (DLL_mi, Etiket) -> essiz sayisi (on kayit, Revizyon 1; betimleyici, gecit degil)
BEKLENEN_KATMAN = {0: {(0, 0): 48, (1, 0): 222, (0, 1): 1583, (1, 1): 140},
                   1: {(0, 0): 53, (1, 0): 295, (0, 1): 56, (1, 1): 14}}
BEKLENEN_DOT_NET_TEST_TEKIL = 59953
NET_OLCUM_A = {"EXE": (1106, 3278, 6, 208), "DLL": (72, 308, 10, 1054)}   # on kayit, K3
TURLER = ("EXE", "DLL")


def dur(mesaj):
    sys.exit(f"GECIT BASARISIZ: {mesaj}")


def oran(k, n):
    k, n = int(k), int(n)
    if n == 0:
        return {"k": 0, "n": 0, "%": float("nan"), "alt": float("nan"), "ust": float("nan")}
    alt, ust = o.wilson(k, n)
    return {"k": k, "n": n, "%": 100 * k / n, "alt": float(alt), "ust": float(ust)}


def metin(r):
    if r["n"] == 0:
        return "-"
    if r["n"] < KUCUK_N:
        return f"{r['k']}/{r['n']} (n<{KUCUK_N}, yorumlanmaz)"
    return f"%{r['%']:.2f} [{r['alt']:.2f}-{r['ust']:.2f}] ({r['k']}/{r['n']})"


def ortusuyor(a, b):
    return not (a["ust"] < b["alt"] or b["ust"] < a["alt"])


def kacirdi(p, df, esik):
    return p <= np.where(df.DLL_mi.to_numpy() == 1, esik["DLL"], esik["EXE"])


def hucreler(bolum, df, p, esik, model, h):
    """Bir kume / model / esik icin EXE, DLL, hepsi: kacan, YA, AUC."""
    y, dll = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1
    kac = kacirdi(p, df, esik)
    sonuc = {}
    for tur, m in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
        zr, zs = m & (y == 1), m & (y == 0)
        auc = float(roc_auc_score(y[m], p[m])) if zr.any() and zs.any() else float("nan")
        sonuc[(bolum, h, model, tur)] = {"kacan": oran(kac[zr].sum(), zr.sum()),
                                         "YA": oran((~kac[zs]).sum(), zs.sum()), "AUC": auc,
                                         "esik": f"{esik['EXE']:.2f} / {esik['DLL']:.2f}"}
    return sonuc


# --- Yorum kurallari (on kayit, bolum 3 ve 4) ---
def kural1(kacan_m, kacan_n, e1, e2, b, c, p):
    if kacan_m["n"] < KUCUK_N or kacan_n["n"] < KUCUK_N:
        return f"oran yorumlanmaz (n<{KUCUK_N})"
    eksik = [ad for ad, tuttu in (("E1", e1), ("E2", e2)) if not tuttu]
    if eksik:
        return f"hukum yok: esit yanlis alarm saglanamadi ({', '.join(eksik)})"
    if b + c < MCNEMAR_MIN:
        return f"hukum yok: uyusmayan cift sayisi yetersiz (b + c = {b + c} < {MCNEMAR_MIN})"
    if p < ALFA and b < c:
        return "M2d A kumesinde native'den anlamli olarak daha az kaciriyor"
    if p < ALFA and b > c:
        return "M2d A kumesinde native'den anlamli olarak daha cok kaciriyor"
    return "fark gosterilemedi"


def kural2(ya, h):
    if ya["n"] < KUCUK_N:
        return f"oran yorumlanmaz (n<{KUCUK_N})"
    cozunurluk = float(o.wilson(0, ya["n"])[1])
    if cozunurluk >= h:
        return f"hukum yok: cozunurluk yetersiz (wilson(0, {ya['n']}) ust %{cozunurluk:.2f} >= H)"
    if ya["ust"] < h:
        return "A'da hedefin altinda"
    if ya["alt"] > h:
        return "A'da hedefin ustunde"
    return "hedefle farki gosterilemedi"


def kural3(a, d):
    if a["n"] < KUCUK_N or d["n"] < KUCUK_N:
        return f"oran yorumlanmaz (n<{KUCUK_N})"
    if ortusuyor(a, d):
        return "fark gosterilemedi"
    yon = "yuksek" if a["%"] > d["%"] else "dusuk"
    return f"M2d'nin kacani A'da Dot_Net_test'ten anlamli olarak farkli ({yon})"


# --- Olcum (tekil A, bir kez) ---
def olc_ve_raporla(a, skor_a, dn, skor_dn, esik, uretim, csv_yolu, hukum_yolu):
    """a, dn: TEKIL kumeler. skor_*: {model: p}. esik: {(h, model): {EXE, DLL}}. uretim: native uretim esikleri."""
    T = {}
    for h in HEDEFLER:
        for ad in (M2D, NATIVE):
            T.update(hucreler("A tekil", a, skor_a[ad], esik[(h, ad)], ad, h))
            T.update(hucreler("Dot_Net_test tekil", dn, skor_dn[ad], esik[(h, ad)], ad, h))
    T.update(hucreler("A tekil", a, skor_a[NATIVE], uretim, NATIVE, "uretim"))

    karma = a.Karma_Mod.to_numpy() == 1
    for katman, m in (("A saf .NET", ~karma), ("A karma mod", karma)):
        alt, idx = a[m], np.nonzero(m)[0]
        for h in HEDEFLER:
            for ad in (M2D, NATIVE):
                T.update(hucreler(katman, alt, skor_a[ad][idx], esik[(h, ad)], ad, h))
        T.update(hucreler(katman, alt, skor_a[NATIVE][idx], uretim, NATIVE, "uretim"))

    pd.DataFrame([{"bolum": b, "hedef": h, "model": ad, "tur": tur, "esik_EXE_DLL": r["esik"],
                   **{f"kacan_{k}": v for k, v in r["kacan"].items()},
                   **{f"YA_{k}": v for k, v in r["YA"].items()}, "AUC": r["AUC"]}
                  for (b, h, ad, tur), r in T.items()]).round(4).to_csv(csv_yolu, index=False)

    print("\n=== Tekil A: kacan ve YA ===")
    print("| H | model | tur | esik EXE / DLL | kacan % [Wilson %95] (k/n) | YA % [Wilson %95] (k/n) | AUC |")
    print("|---|---|---|---|---|---|---|")
    for h in HEDEFLER:
        for ad in (M2D, NATIVE):
            for tur in (*TURLER, "hepsi"):
                r = T[("A tekil", h, ad, tur)]
                print(f"| %{h} | {ad} | {tur} | {r['esik']} | {metin(r['kacan'])} | {metin(r['YA'])} | {r['AUC']:.4f} |")

    print("\n=== Tekil Dot_Net_test, ayni esikler (E1 ve kural 3 icin) ===")
    print("| H | model | tur | kacan | YA |")
    print("|---|---|---|---|---|")
    for h in HEDEFLER:
        for ad in (M2D, NATIVE):
            for tur in TURLER:
                r = T[("Dot_Net_test tekil", h, ad, tur)]
                print(f"| %{h} | {ad} | {tur} | {metin(r['kacan'])} | {metin(r['YA'])} |")

    y, dll = a.Etiket.to_numpy(), a.DLL_mi.to_numpy() == 1
    hukum = []
    print("\n=== Kural 1: M2d - native kacan (McNemar; b = yalniz M2d kacirdi, c = yalniz native kacirdi) ===")
    for h in HEDEFLER:
        k_m, k_n = kacirdi(skor_a[M2D], a, esik[(h, M2D)]), kacirdi(skor_a[NATIVE], a, esik[(h, NATIVE)])
        for tur, m in (("EXE", ~dll), ("DLL", dll)):
            zr = m & (y == 1)
            b, c, p = mcnemar(k_m[zr], k_n[zr])
            am, an = T[("A tekil", h, M2D, tur)], T[("A tekil", h, NATIVE, tur)]
            dm, dn_ = T[("Dot_Net_test tekil", h, M2D, tur)], T[("Dot_Net_test tekil", h, NATIVE, tur)]
            e1, e2 = ortusuyor(dm["YA"], dn_["YA"]), ortusuyor(am["YA"], an["YA"])
            cumle = kural1(am["kacan"], an["kacan"], e1, e2, b, c, p)
            print(f"H %{h} {tur}: kacan M2d {metin(am['kacan'])} vs native {metin(an['kacan'])} | "
                  f"E1 {'tuttu' if e1 else 'TUTMADI'} (Dot_Net_test YA {metin(dm['YA'])} vs {metin(dn_['YA'])}) | "
                  f"E2 {'tuttu' if e2 else 'TUTMADI'} (A YA {metin(am['YA'])} vs {metin(an['YA'])}) | "
                  f"b {b}, c {c}, p {p:.4g} -> {cumle}")
            hukum.append({"kural": 1, "H": h, "tur": tur, "b": b, "c": c, "p": p, "E1": e1, "E2": e2, "cumle": cumle})

    print("\n=== Kural 2: M2d YA mutlak (A) ===")
    for h in HEDEFLER:
        for tur in TURLER:
            ya = T[("A tekil", h, M2D, tur)]["YA"]
            cumle = kural2(ya, h)
            print(f"H %{h} {tur}: YA {metin(ya)} -> {cumle}")
            hukum.append({"kural": 2, "H": h, "tur": tur, "cumle": cumle})

    print("\n=== Kural 3: aktarim (M2d kacan, A vs Dot_Net_test, ikisi de tekil) ===")
    for h in HEDEFLER:
        for tur in TURLER:
            ka, kd = T[("A tekil", h, M2D, tur)]["kacan"], T[("Dot_Net_test tekil", h, M2D, tur)]["kacan"]
            cumle = kural3(ka, kd)
            print(f"H %{h} {tur}: A {metin(ka)} vs Dot_Net_test {metin(kd)} -> {cumle}")
            hukum.append({"kural": 3, "H": h, "tur": tur, "cumle": cumle})
    pd.DataFrame(hukum).to_csv(hukum_yolu, index=False)

    print("\n=== BETIMLEYICI (hukum uretmez): native uretim esikleri, tekil A ===")
    for tur in (*TURLER, "hepsi"):
        r = T[("A tekil", "uretim", NATIVE, tur)]
        print(f"{tur}: esik {r['esik']} | kacan {metin(r['kacan'])} | YA {metin(r['YA'])} | AUC {r['AUC']:.4f}")

    print("\n=== BETIMLEYICI: saf .NET / karma mod katmanlari (katmanlar arasi fark 'anlamli' diye yazilmaz) ===")
    print("| katman | H | model | tur | kacan | YA |")
    print("|---|---|---|---|---|---|")
    for katman, m in (("A saf .NET", ~karma), ("A karma mod", karma)):
        for mk, et in (((0, 0), "zararsiz EXE"), ((1, 0), "zararsiz DLL"), ((0, 1), "zararli EXE"), ((1, 1), "zararli DLL")):
            n = int((m & (dll == bool(mk[0])) & (y == mk[1])).sum())
            bek = BEKLENEN_KATMAN[0 if katman == "A saf .NET" else 1][mk]
            if n != bek:
                print(f"[!] {katman} {et}: n {n} != on kayittaki {bek}")
        for h, modeller in ((0.45, (M2D, NATIVE)), (1.05, (M2D, NATIVE)), ("uretim", (NATIVE,))):
            for ad in modeller:
                for tur in (*TURLER, "hepsi"):
                    r = T[(katman, h, ad, tur)]
                    print(f"| {katman} | {h} | {ad} | {tur} | {metin(r['kacan'])} | {metin(r['YA'])} |")

    print("\n=== BETIMLEYICI: aileler (tekil A zararlilari, H %1,05; n >= 30 ve agenttesla) ===")
    zr = y == 1
    aile = a.Aile.fillna("(bilinmiyor)").astype(str).replace("", "(bilinmiyor)").to_numpy()
    k_m, k_n = kacirdi(skor_a[M2D], a, esik[(1.05, M2D)]), kacirdi(skor_a[NATIVE], a, esik[(1.05, NATIVE)])
    sayim = pd.Series(aile[zr]).value_counts()
    secili = [ad for ad, n in sayim.items() if n >= KUCUK_N]
    if "agenttesla" not in secili:
        secili.append("agenttesla")
    print("| aile | n | M2d kacan | native kacan |")
    print("|---|---|---|---|")
    for ad in secili:
        m = zr & (aile == ad)
        print(f"| {ad} | {int(m.sum())} | {metin(oran(k_m[m].sum(), m.sum()))} | {metin(oran(k_n[m].sum(), m.sum()))} |")
    return T


def a_yukle():
    kol = list(dict.fromkeys(o.SAYISAL + DIZGELI_TIPLI + ["Aile", "Tur", "Dosya_Adi"]))
    d = pd.concat([pd.read_parquet(os.path.join(EMBER2024_PARQUET_KLASORU, f"{ad}.parquet"), columns=kol)
                   for ad in ("Win32_test", "Win64_test")], ignore_index=True)
    return d[d.NET_mi == 1].reset_index(drop=True)


def hucre_say(df):
    return {k: int(v) for k, v in df.groupby(["DLL_mi", "Etiket"]).size().items()}


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()

    # --- K1: A verisi (float32'ye cevirmeden once, ham degerlerle) ---
    ciftli = a_yukle()
    eksik = [k for k in DIZGELI_TIPLI if k not in ciftli.columns]
    if len(DIZGELI_TIPLI) != 87 or eksik or ciftli[DIZGELI_TIPLI].isna().any().any():
        dur(f"K1 sutun {len(DIZGELI_TIPLI)}, eksik {eksik}, NaN {int(ciftli[DIZGELI_TIPLI].isna().sum().sum())}")
    if not (ciftli.Hafta.min() >= 52 and ciftli.Hafta.max() <= 63):
        dur(f"K1 hafta {ciftli.Hafta.min()}-{ciftli.Hafta.max()}")
    kopya = ciftli.groupby("Dosya_Adi").size()
    if not kopya.isin([2, 4]).all():
        dur(f"K1 kopya dagilimi {kopya.value_counts().to_dict()}")
    celiski = int((ciftli.groupby("Dosya_Adi")[DIZGELI_TIPLI + ["Etiket"]].nunique(dropna=False).max(axis=1) > 1).sum())
    if celiski:
        dur(f"K1 kopyalar arasinda farkli etiket / sutun: {celiski} sha")
    tekil = ciftli.drop_duplicates("Dosya_Adi", keep="first").reset_index(drop=True)
    sc, st = hucre_say(ciftli), hucre_say(tekil)
    if sc != BEKLENEN_CIFTLI or st != BEKLENEN_TEKIL or len(ciftli) != 4848 or len(tekil) != 2411:
        dur(f"K1 sayilar ciftli {len(ciftli)} {sc}, tekil {len(tekil)} {st}")
    print(f"[+] K1 ciftli {len(ciftli)} {sc}; kopya dagilimi {kopya.value_counts().to_dict()}; celiskili sha 0; "
          f"tekil {len(tekil)} {st}; hafta {ciftli.Hafta.min()}-{ciftli.Hafta.max()}; 87 sutun tam ({time.monotonic() - t0:.0f} sn)")
    for d in (ciftli, tekil):
        d[o.SAYISAL] = d[o.SAYISAL].astype("float32")      # ortak_deney.yukle ile ayni
        d["Etiket"] = d["Etiket"].astype(int)

    # --- M2d (uzman_native.py tarifi, ciftli havuz) ---
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False, dtype={"Dosya_Adi": str})
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False, dtype={"Dosya_Adi": str})
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    hucre_min = int(havuz.groupby(["DLL_mi", "Etiket"]).size().min())
    m2d = egit(havuz.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=hucre_min, random_state=42), DIZGELI_TIPLI)
    print(f"[*] M2d egitildi: 4 x {hucre_min} = {4 * hucre_min} ({time.monotonic() - t0:.0f} sn)")

    paket = tahmin_et.model_yukle()                        # SHA-256 dogrulamali (Kural 10)
    native, meta = paket["model"], paket["meta"]
    native.set_params(n_jobs=8)
    nk = meta["ozellikler"]
    uretim = meta["esikler"]
    print(f"[*] native sha256 {meta['model_sha256'][:16]}..., uretim esikleri {uretim} ({time.monotonic() - t0:.0f} sn)")

    skor_gecit = {
        M2D: (m2d.predict_proba(dog[DIZGELI_TIPLI])[:, 1], m2d.predict_proba(test[DIZGELI_TIPLI])[:, 1]),
        NATIVE: (native.predict_proba(dog[nk].astype("float32"))[:, 1],
                 native.predict_proba(test[nk].astype("float32"))[:, 1]),
    }

    # --- K2, K3: esikler ve Dot_Net_test sayilari uzman_native.csv ile birebir ---
    onceki = pd.read_csv(os.path.join(BURASI, "..", "6", "uzman_native.csv"))
    esik = {}
    for hd in HEDEFLER:
        for ad, (p_dog, p_test) in skor_gecit.items():
            gecit = "K2" if ad == M2D else "K3"
            e = esikler(p_dog, dog, hd)
            bek = BEKLENEN_ESIK[(hd, ad)]
            if not np.allclose([e["EXE"], e["DLL"]], bek, rtol=0, atol=1e-9):
                dur(f"{gecit} H %{hd} {ad} esik {e} != {bek}")
            for s in olc(ad, hd, p_dog, dog, p_test, test):
                r = onceki[(onceki.model == ad) & (onceki["hedef_YA_%"] == hd) & (onceki.tur == s["tur"])].iloc[0]
                if (s["kacan_k"], s["YA_k"]) != (r.kacan_k, r.YA_k):
                    dur(f"{gecit} H %{hd} {ad} {s['tur']}: kacan/YA {s['kacan_k']}/{s['YA_k']} != csv {r.kacan_k}/{r.YA_k}")
            esik[(hd, ad)] = e
            print(f"[+] {gecit} H %{hd} {ad}: esik EXE {e['EXE']:.2f} / DLL {e['DLL']:.2f} ve Dot_Net_test 3 satir == csv")

    # --- K3 devam: ciftli A .NET, uretim esikleri, net_olcum.csv ---
    p_ciftli = native.predict_proba(ciftli[nk])[:, 1]
    kac_c = kacirdi(p_ciftli, ciftli, uretim)
    y_c, dll_c = ciftli.Etiket.to_numpy(), ciftli.DLL_mi.to_numpy() == 1
    net_csv = pd.read_csv(os.path.join(BURASI, "..", "5", "net_olcum.csv"))
    for tur, m in (("EXE", ~dll_c), ("DLL", dll_c)):
        zr, zs = m & (y_c == 1), m & (y_c == 0)
        bulunan = (int(kac_c[zr].sum()), int(zr.sum()), int((~kac_c[zs]).sum()), int(zs.sum()))
        r = net_csv[(net_csv.kume == "A native test") & (net_csv.esik == "tur esigi") & (net_csv.grup == ".NET") & (net_csv.tur == tur)].iloc[0]
        csv_deger = (int(r.kacan_k), int(r.kacan_n), int(r.YA_k), int(r.YA_n))
        if bulunan != NET_OLCUM_A[tur] or bulunan != csv_deger:
            dur(f"K3 ciftli A {tur}: {bulunan}, on kayit {NET_OLCUM_A[tur]}, net_olcum.csv {csv_deger}")
        print(f"[+] K3 ciftli A {tur} uretim esiginde (kacan k/n, YA k/n) {bulunan} == on kayit == net_olcum.csv")

    # --- K4: tekil A x Dot_Net_train ---
    ortak = set(tekil.Dosya_Adi) & set(egitim.Dosya_Adi)
    print(f"[{'+' if not ortak else '!'}] K4 tekil A x Dot_Net_train ortak essiz sha: {len(ortak)}")
    if ortak:                                               # on kayit: cikarilir, sayisi yazilir
        tekil = tekil[~tekil.Dosya_Adi.isin(ortak)].reset_index(drop=True)
        print(f"[!] K4 {len(ortak)} dosya cikarildi; kalan tekil A {len(tekil)}")

    # --- K5: Dot_Net_test tekil ---
    n_tekil = test.Dosya_Adi.nunique()
    farkli = int((test.groupby("Dosya_Adi").Etiket.nunique() > 1).sum())
    if n_tekil != BEKLENEN_DOT_NET_TEST_TEKIL or farkli:
        dur(f"K5 Dot_Net_test essiz {n_tekil}, ayni sha'da farkli etiket {farkli}")
    tut = ~test.duplicated("Dosya_Adi", keep="first").to_numpy()
    dn = test[tut].reset_index(drop=True)
    print(f"[+] K5 Dot_Net_test tekil {len(dn)}, ayni sha'da farkli etiket 0; hucreler {hucre_say(dn)}")
    print(f"[+] Tum gecitler tuttu ({time.monotonic() - t0:.0f} sn); olcum basliyor")

    # --- Olcum (tekil, bir kez) ---
    skor_a = {M2D: m2d.predict_proba(tekil[DIZGELI_TIPLI])[:, 1], NATIVE: native.predict_proba(tekil[nk])[:, 1]}
    skor_dn = {ad: skor_gecit[ad][1][tut] for ad in (M2D, NATIVE)}
    olc_ve_raporla(tekil, skor_a, dn, skor_dn, esik, uretim, os.path.join(BURASI, "is2b_a_kumesi.csv"),
                   os.path.join(BURASI, "is2b_hukum.csv"))
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> is2b_a_kumesi.csv, is2b_hukum.csv")
