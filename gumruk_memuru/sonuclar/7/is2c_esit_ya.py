"""
Is 2(c) - Esit yanlis alarmda M2d ile native: ROC, essiz dosya, eslenik bootstrap; iki kume (Dot_Net_test, A).
On kayit: is2c_on_kayit.md (revizyon 1 dahil; olcumden once commit'lendi).

Esit YA aralik ortusmesiyle degil, her model icin AYNI kumede FPR = H noktasi secilerek KURULUR. Bu nokta
kumenin icinden secilir: Kural 6 geregi ROC noktasidir, uretim esigi degil. Uzman BAGLANMAZ.
Kullanim: python -u is2c_esit_ya.py > is2c_esit_ya.log
"""

import os
import sys
import time

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)
import is2b_a_kumesi as b  # noqa: E402  (sys.path'i de kurar)
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402
from ember2024_net_cikar import cikti_yolu  # noqa: E402
from is2a_yerel_net import BEKLENEN_ESIK, M2D, NATIVE, esikler  # noqa: E402
from net_model import DIZGELI_TIPLI  # noqa: E402
from uzman_native import DOGRULAMA_HAFTA, HEDEFLER, egit, olc  # noqa: E402

B_SAYI, TOHUM = 10000, 42
ASGARI_ALARM, KUCUK_N, DELTA = 5, 30, 2.0
KUMELER = ("Dot_Net_test", "A")
TURLER = ("EXE", "DLL")
K_LISTE = {"EXE": (0, 1, 2, 3), "DLL": tuple(range(8))}


def dur(mesaj):
    sys.exit(f"GECIT BASARISIZ: {mesaj}")


# --- ROC (sayimlardan; alarm = skor > t) ---
def roc_sayim(nz, nr):
    """nz, nr: seviye basina zararsiz / zararli sayisi, skor BUYUKTEN kucuge. (fpr, tpr), (0,0) ile baslar."""
    fpr = np.concatenate(([0.0], np.cumsum(nz) / nz.sum()))
    tpr = np.concatenate(([0.0], np.cumsum(nr) / nr.sum()))
    return fpr, tpr


def hdeki_nokta(fpr, tpr, h):
    """FPR = h'de TPR (dogrusal ic degerleme). (tpr_h, i, j, w). i: FPR'si h'yi asmayan son kose, j = i + 1."""
    i = int(np.searchsorted(fpr, h, side="right") - 1)
    j = min(i + 1, len(fpr) - 1)
    if j == i or fpr[j] == fpr[i]:
        return float(tpr[i]), i, j, 0.0
    w = (h - fpr[i]) / (fpr[j] - fpr[i])
    return float(tpr[i] + w * (tpr[j] - tpr[i])), i, j, float(w)


def auc_roc(fpr, tpr):
    return float(np.trapezoid(tpr, fpr))


def kismi_auc(fpr, tpr, h):
    """FPR <= h araliginda ROC alti alan / h (o araliktaki ortalama TPR)."""
    t, i, _, _ = hdeki_nokta(fpr, tpr, h)
    x, y = np.append(fpr[: i + 1], h), np.append(tpr[: i + 1], t)
    return float(np.trapezoid(y, x) / h)


class Hucre:
    """Bir kume x tur (ya da 'hepsi') icin iki modelin skor seviyeleri; bootstrap burada."""

    def __init__(self, p_m, p_n, y, tabaka):
        self.y = y
        self.uyeler = [np.nonzero(tabaka == g)[0] for g in np.unique(tabaka)]   # tur x Etiket gruplari
        self.modeller = {}
        for ad, p in ((M2D, p_m), (NATIVE, p_n)):
            sev, ters = np.unique(-p, return_inverse=True)     # -p: indis 0 = en buyuk skor
            self.modeller[ad] = (-sev, ters.astype(np.int64), len(sev))

    def _say(self, ad, idx):
        _, ters, L = self.modeller[ad]
        y = self.y[idx]
        return (np.bincount(ters[idx[y == 0]], minlength=L).astype(float),
                np.bincount(ters[idx[y == 1]], minlength=L).astype(float))

    def roc(self, ad, idx=None):
        idx = np.arange(len(self.y)) if idx is None else idx
        return roc_sayim(*self._say(ad, idx))

    def yeniden(self, rng):
        """Tabaka (tur x Etiket) icinde yerine koyarak cekilmis indisler; iki model AYNI indisleri kullanir."""
        return np.concatenate([uye[rng.integers(0, len(uye), len(uye))] for uye in self.uyeler])


def olculer(h_, ad_a, ad_b, idx=None):
    """ad_a - ad_b farklari: her H icin kacan (puan) ve kismi AUC; AUC."""
    fa, ta = h_.roc(ad_a, idx)
    fb, tb = h_.roc(ad_b, idx)
    d = {"AUC": auc_roc(fa, ta) - auc_roc(fb, tb)}
    for h in HEDEFLER:
        k = h / 100
        d[f"kacan_{h}"] = 100 * (hdeki_nokta(fb, tb, k)[0] - hdeki_nokta(fa, ta, k)[0])
        d[f"pAUC_{h}"] = kismi_auc(fa, ta, k) - kismi_auc(fb, tb, k)
    return d


def bootstrap(h_, tohum_liste, B=B_SAYI, ad_a=M2D, ad_b=NATIVE):
    rng = np.random.default_rng(np.random.SeedSequence(tohum_liste))
    birikim = {}
    for _ in range(B):
        for k, v in olculer(h_, ad_a, ad_b, h_.yeniden(rng)).items():
            birikim.setdefault(k, []).append(v)
    return {k: np.array(v) for k, v in birikim.items()}


def aralik(x, alt=2.5, ust=97.5):
    return float(np.percentile(x, alt)), float(np.percentile(x, ust))


# --- Yorum kurallari (on kayit, bolum 3 ve 4) ---
def hucre_hukmu(n_z, n_r, h, bosluk_m, bosluk_n, a95, a90):
    """(hukum aliyor mu, cumle). bosluk: i-j kose FPR farki (yuzde)."""
    if n_z * h / 100 < ASGARI_ALARM:
        return False, f"hukum yok: asgari ornek altinda (n*H = {n_z * h / 100:.2f} < {ASGARI_ALARM})"
    if n_r < KUCUK_N:
        return False, f"hukum yok: zararli n = {n_r} < {KUCUK_N}"
    if max(bosluk_m, bosluk_n) > h:
        return False, f"hukum yok: ROC cozunurlugu yetersiz (kose boslugu M2d %{bosluk_m:.3f}, native %{bosluk_n:.3f} > H)"
    if a95[1] < 0:
        return True, "M2d esit YA'da daha az kaciriyor"
    if a95[0] > 0:
        return True, "native esit YA'da daha az kaciriyor"
    if a90[0] > -DELTA and a90[1] < DELTA:
        return True, f"fark gosterilemedi; +-{DELTA:.0f} puan icinde esdeger (TOST)"
    return True, "fark gosterilemedi"


def karar(satirlar):
    """satirlar: [{kume, tur, H, hukum_aliyor, cumle, a95_ust}]. (aday turler, aday hucreler, dokum)."""
    aday_hucre, dokum = {}, []
    idx = {(s["kume"], s["tur"], s["H"]): s for s in satirlar}
    for tur in TURLER:
        hucreler = []
        for h in HEDEFLER:
            d, a = idx[("Dot_Net_test", tur, h)], idx[("A", tur, h)]
            if d["hukum_aliyor"] and a["hukum_aliyor"] and d["a95_ust"] < 0 and a["a95_ust"] < 0:
                hucreler.append(h)
        engel = [(k, h) for k in KUMELER for h in HEDEFLER
                 if idx[(k, tur, h)]["hukum_aliyor"] and idx[(k, tur, h)]["cumle"].startswith("native")]
        aday_hucre[tur] = hucreler if hucreler and not engel else []
        dokum.append((tur, hucreler, engel))
    return [t for t, h in aday_hucre.items() if h], aday_hucre, dokum


# --- Betimleyiciler ---
def ayni_alarm_sayisi(h_, k):
    """Alarmi k'yi asmayan son kose: {model: (gercek alarm, kacan k, zararli n)}. Ic degerleme yok."""
    sonuc = {}
    for ad in (M2D, NATIVE):
        nz, nr = h_._say(ad, np.arange(len(h_.y)))
        a, y = np.cumsum(nz), np.cumsum(nr)
        i = int(np.searchsorted(a, k, side="right") - 1)
        yak = 0 if i < 0 else int(y[i])
        sonuc[ad] = (0 if i < 0 else int(a[i]), int(nr.sum()) - yak, int(nr.sum()))
    return sonuc


def aile_beklenen_kacan(h_, ad, h, zr_idx):
    """Zararli dosya basina beklenen kacma olasiligi (FPR = h'deki ic degerleme agirligiyla)."""
    sev, ters, _ = h_.modeller[ad]
    f, t = h_.roc(ad)
    _, i, j, w = hdeki_nokta(f, t, h / 100)
    tespit_i = ters[zr_idx] < i          # kose i: ilk i seviye alarmda
    tespit_j = ters[zr_idx] < j
    return 1 - ((1 - w) * tespit_i + w * tespit_j)


def hepsini_olc(kumeler, csv_yolu, hukum_yolu, B=B_SAYI):
    """kumeler: {ad: (df, p_m, p_n)}; df: Etiket, DLL_mi, Aile. Tum olcum ve rapor."""
    satirlar, hukum, oz = [], [], {}
    for k_i, kume in enumerate(KUMELER):
        df, p_m, p_n = kumeler[kume]
        y, dll = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1
        for t_i, tur in enumerate((*TURLER, "hepsi")):
            m = {"EXE": ~dll, "DLL": dll, "hepsi": np.ones_like(dll)}[tur]
            tabaka = (dll[m].astype(int) * 2 + y[m])
            h_ = Hucre(p_m[m], p_n[m], y[m], tabaka)
            n_z, n_r = int((y[m] == 0).sum()), int((y[m] == 1).sum())
            t0 = time.monotonic()
            bs = bootstrap(h_, [TOHUM, k_i, t_i], B)
            nokta = olculer(h_, M2D, NATIVE)
            print(f"[*] {kume} {tur}: n zararsiz {n_z}, zararli {n_r}; B = {B} ({time.monotonic() - t0:.0f} sn)")
            f = {ad: h_.roc(ad) for ad in (M2D, NATIVE)}
            auc = {ad: auc_roc(*f[ad]) for ad in f}
            a = aralik(bs["AUC"])
            satirlar.append({"kume": kume, "tur": tur, "olcu": "AUC", "H": "", "M2d": auc[M2D], "native": auc[NATIVE],
                             "fark": nokta["AUC"], "alt": a[0], "ust": a[1]})
            oz[(kume, tur, "AUC")] = satirlar[-1]
            if tur == "hepsi":
                continue
            for h in HEDEFLER:
                k = h / 100
                ka, bos, duy = {}, {}, {}
                for ad in (M2D, NATIVE):
                    t, i, j, _ = hdeki_nokta(*f[ad], k)
                    ka[ad] = 100 * (1 - t)
                    bos[ad] = 100 * (f[ad][0][j] - f[ad][0][i])
                    duy[ad] = (100 * f[ad][0][i], 100 * (1 - f[ad][1][i]), 100 * f[ad][0][j])
                a95, a90 = aralik(bs[f"kacan_{h}"]), aralik(bs[f"kacan_{h}"], 5, 95)
                aliyor, cumle = hucre_hukmu(n_z, n_r, h, bos[M2D], bos[NATIVE], a95, a90)
                satirlar.append({"kume": kume, "tur": tur, "olcu": "kacan", "H": h, "M2d": ka[M2D], "native": ka[NATIVE],
                                 "fark": nokta[f"kacan_{h}"], "alt": a95[0], "ust": a95[1], "alt90": a90[0], "ust90": a90[1],
                                 "n_zararsiz": n_z, "n_zararli": n_r, "n_x_H": n_z * k, "hukum_aliyor": aliyor, "cumle": cumle,
                                 "M2d_kose_FPR_i": duy[M2D][0], "M2d_kose_FPR_j": duy[M2D][2], "M2d_kose_kacan": duy[M2D][1],
                                 "native_kose_FPR_i": duy[NATIVE][0], "native_kose_FPR_j": duy[NATIVE][2], "native_kose_kacan": duy[NATIVE][1]})
                hukum.append({"kume": kume, "tur": tur, "H": h, "hukum_aliyor": aliyor, "cumle": cumle, "a95_ust": a95[1],
                              "fark": nokta[f"kacan_{h}"], "alt": a95[0], "ust": a95[1]})
                oz[(kume, tur, "kacan", h)] = satirlar[-1]
                pm, pn = kismi_auc(*f[M2D], k), kismi_auc(*f[NATIVE], k)
                ap = aralik(bs[f"pAUC_{h}"])
                satirlar.append({"kume": kume, "tur": tur, "olcu": "pAUC", "H": h, "M2d": pm, "native": pn, "fark": nokta[f"pAUC_{h}"],
                                 "alt": ap[0], "ust": ap[1], "n_x_H": n_z * k, "hukum_aliyor": n_z * k >= ASGARI_ALARM})
                oz[(kume, tur, "pAUC", h)] = satirlar[-1]
    pd.DataFrame(satirlar).round(6).to_csv(csv_yolu, index=False)
    pd.DataFrame(hukum).round(6).to_csv(hukum_yolu, index=False)

    print("\n=== BIRINCIL: esit YA'da kacan (Delta = M2d - native, puan; eslenik bootstrap %95) ===")
    print("| kume | tur | H | n*H | M2d kacan | native kacan | Delta [%95] | %90 | hukum |")
    print("|---|---|---|---|---|---|---|---|---|")
    for kume in KUMELER:
        for tur in TURLER:
            for h in HEDEFLER:
                s = oz[(kume, tur, "kacan", h)]
                print(f"| {kume} | {tur} | %{h} | {s['n_x_H']:.2f} | %{s['M2d']:.2f} | %{s['native']:.2f} | "
                      f"{s['fark']:+.2f} [{s['alt']:+.2f}, {s['ust']:+.2f}] | [{s['alt90']:+.2f}, {s['ust90']:+.2f}] | {s['cumle']} |")

    aday, hucreler, dokum = karar(hukum)
    print("\n=== KARAR (kural 3-5) ===")
    for tur, h_aday, engel in dokum:
        print(f"{tur}: iki kumede de M2d lehine hucreler {h_aday}; engel (native daha az) {engel}; aday hucre {hucreler[tur]}")
    if aday:
        print(f"-> Baglanmaya aday tur: {aday} (aday baglanmak degildir; karar kullanicinin). Diger turler varsayilanda.")
    else:
        print("-> Aday yok. VARSAYILAN KARAR: uzman Faz 1 kapsami disi, native tek model.")

    print("\n=== BETIMLEYICI: AUC (eslenik bootstrap %95) ===")
    for kume in KUMELER:
        for tur in (*TURLER, "hepsi"):
            s = oz[(kume, tur, "AUC")]
            print(f"{kume} {tur}: M2d {s['M2d']:.4f}, native {s['native']:.4f}, fark {s['fark']:+.4f} [{s['alt']:+.4f}, {s['ust']:+.4f}]")

    print("\n=== BETIMLEYICI: kismi AUC (FPR <= H, ortalama TPR; asgari ornek altindaki hucre isaretli) ===")
    for kume in KUMELER:
        for tur in TURLER:
            for h in HEDEFLER:
                s = oz[(kume, tur, "pAUC", h)]
                isaret = "" if s["hukum_aliyor"] else "  [asgari ornek altinda, yorumlanmaz]"
                print(f"{kume} {tur} %{h}: M2d {s['M2d']:.4f}, native {s['native']:.4f}, fark {s['fark']:+.4f} [{s['alt']:+.4f}, {s['ust']:+.4f}]{isaret}")

    print("\n=== BETIMLEYICI: duyarlilik (ic degerleme yok; FPR'si H'yi asmayan son kose) ===")
    for kume in KUMELER:
        for tur in TURLER:
            for h in HEDEFLER:
                s = oz[(kume, tur, "kacan", h)]
                print(f"{kume} {tur} %{h}: M2d kacan %{s['M2d_kose_kacan']:.2f} (FPR %{s['M2d_kose_FPR_i']:.3f}, sonraki %{s['M2d_kose_FPR_j']:.3f}) | "
                      f"native kacan %{s['native_kose_kacan']:.2f} (FPR %{s['native_kose_FPR_i']:.3f}, sonraki %{s['native_kose_FPR_j']:.3f})")

    print("\n=== BETIMLEYICI: A'da ayni zararsiz alarm sayisinda kacan (takas; hukum uretmez) ===")
    print("| tur | k | M2d gercek alarm | M2d kacan | native gercek alarm | native kacan |")
    print("|---|---|---|---|---|---|")
    df, p_m, p_n = kumeler["A"]
    y, dll = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1
    for tur in TURLER:
        m = dll if tur == "DLL" else ~dll
        h_ = Hucre(p_m[m], p_n[m], y[m], dll[m].astype(int) * 2 + y[m])
        for k in K_LISTE[tur]:
            r = ayni_alarm_sayisi(h_, k)
            am, kn, nr = r[M2D]
            an, kn2, _ = r[NATIVE]
            print(f"| {tur} | {k} | {am} | %{100 * kn / nr:.2f} ({kn}/{nr}) | {an} | %{100 * kn2 / nr:.2f} ({kn2}/{nr}) |")

    print("\n=== BETIMLEYICI: aile bazinda beklenen kacan, esit YA, H %1,05 (aralik yok; zararli n >= 30 ve agenttesla) ===")
    for kume in KUMELER:
        df, p_m, p_n = kumeler[kume]
        y, dll = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1
        aile = df.Aile.fillna("(bilinmiyor)").astype(str).replace("", "(bilinmiyor)").to_numpy()
        beklenen = {M2D: np.zeros(len(df)), NATIVE: np.zeros(len(df))}
        for tur in TURLER:
            m = dll if tur == "DLL" else ~dll
            ind = np.nonzero(m)[0]
            h_ = Hucre(p_m[m], p_n[m], y[m], dll[m].astype(int) * 2 + y[m])
            for ad in (M2D, NATIVE):
                ic_z = np.nonzero(y[m] == 1)[0]
                beklenen[ad][ind[ic_z]] = aile_beklenen_kacan(h_, ad, 1.05, ic_z)
        zr = y == 1
        sayim = pd.Series(aile[zr]).value_counts()
        secili = [a for a, n in sayim.items() if n >= KUCUK_N]
        if "agenttesla" not in secili:
            secili.append("agenttesla")
        print(f"-- {kume} --")
        print("| aile | n | M2d | native |")
        print("|---|---|---|---|")
        for ad_a in secili:
            q = zr & (aile == ad_a)
            n = int(q.sum())
            if n == 0:
                continue
            bm, bn = beklenen[M2D][q].sum(), beklenen[NATIVE][q].sum()
            if n < KUCUK_N:
                print(f"| {ad_a} | {n} | {bm:.1f}/{n} (n<{KUCUK_N}) | {bn:.1f}/{n} (n<{KUCUK_N}) |")
            else:
                print(f"| {ad_a} | {n} | %{100 * bm / n:.2f} | %{100 * bn / n:.2f} |")
    return oz, hukum


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()

    # --- K1 (2(b) ile ayni) ---
    ciftli = b.a_yukle()
    eksik = [k for k in DIZGELI_TIPLI if k not in ciftli.columns]
    if len(DIZGELI_TIPLI) != 87 or eksik or ciftli[DIZGELI_TIPLI].isna().any().any():
        dur(f"K1 sutun {len(DIZGELI_TIPLI)}, eksik {eksik}")
    if not (ciftli.Hafta.min() >= 52 and ciftli.Hafta.max() <= 63):
        dur(f"K1 hafta {ciftli.Hafta.min()}-{ciftli.Hafta.max()}")
    kopya = ciftli.groupby("Dosya_Adi").size()
    if not kopya.isin([2, 4]).all():
        dur(f"K1 kopya dagilimi {kopya.value_counts().to_dict()}")
    celiski = int((ciftli.groupby("Dosya_Adi")[DIZGELI_TIPLI + ["Etiket"]].nunique(dropna=False).max(axis=1) > 1).sum())
    tekil = ciftli.drop_duplicates("Dosya_Adi", keep="first").reset_index(drop=True)
    sc, st = b.hucre_say(ciftli), b.hucre_say(tekil)
    if celiski or sc != b.BEKLENEN_CIFTLI or st != b.BEKLENEN_TEKIL:
        dur(f"K1 celiski {celiski}, ciftli {sc}, tekil {st}")
    print(f"[+] K1 ciftli {len(ciftli)}, tekil {len(tekil)} {st}; celiskili sha 0; hafta 52-63")
    for d in (ciftli, tekil):
        d[o.SAYISAL] = d[o.SAYISAL].astype("float32")
        d["Etiket"] = d["Etiket"].astype(int)

    # --- M2d, native ---
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False, dtype={"Dosya_Adi": str})
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False, dtype={"Dosya_Adi": str})
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    hucre_min = int(havuz.groupby(["DLL_mi", "Etiket"]).size().min())
    m2d = egit(havuz.groupby(["DLL_mi", "Etiket"], group_keys=False).sample(n=hucre_min, random_state=42), DIZGELI_TIPLI)
    paket = tahmin_et.model_yukle()
    native, meta = paket["model"], paket["meta"]
    native.set_params(n_jobs=8)
    nk, uretim = meta["ozellikler"], meta["esikler"]
    print(f"[*] M2d 4 x {hucre_min}; native sha256 {meta['model_sha256'][:16]}... ({time.monotonic() - t0:.0f} sn)")
    skor_g = {M2D: (m2d.predict_proba(dog[DIZGELI_TIPLI])[:, 1], m2d.predict_proba(test[DIZGELI_TIPLI])[:, 1]),
              NATIVE: (native.predict_proba(dog[nk].astype("float32"))[:, 1], native.predict_proba(test[nk].astype("float32"))[:, 1])}

    # --- K2, K3 ---
    onceki = pd.read_csv(os.path.join(BURASI, "..", "6", "uzman_native.csv"))
    esik = {}
    for hd in HEDEFLER:
        for ad, (p_dog, p_test) in skor_g.items():
            e = esikler(p_dog, dog, hd)
            if not np.allclose([e["EXE"], e["DLL"]], BEKLENEN_ESIK[(hd, ad)], rtol=0, atol=1e-9):
                dur(f"K2/K3 H %{hd} {ad} esik {e}")
            for s in olc(ad, hd, p_dog, dog, p_test, test):
                r = onceki[(onceki.model == ad) & (onceki["hedef_YA_%"] == hd) & (onceki.tur == s["tur"])].iloc[0]
                if (s["kacan_k"], s["YA_k"]) != (r.kacan_k, r.YA_k):
                    dur(f"K2/K3 H %{hd} {ad} {s['tur']} sayilar csv ile ayni degil")
            esik[(hd, ad)] = e
    print("[+] K2, K3 esikler ve Dot_Net_test 12 satir == uzman_native.csv")
    p_c = native.predict_proba(ciftli[nk])[:, 1]
    kac_c = b.kacirdi(p_c, ciftli, uretim)
    y_c, dll_c = ciftli.Etiket.to_numpy(), ciftli.DLL_mi.to_numpy() == 1
    for tur, m in (("EXE", ~dll_c), ("DLL", dll_c)):
        zr, zs = m & (y_c == 1), m & (y_c == 0)
        bulunan = (int(kac_c[zr].sum()), int(zr.sum()), int((~kac_c[zs]).sum()), int(zs.sum()))
        if bulunan != b.NET_OLCUM_A[tur]:
            dur(f"K3 ciftli A {tur} {bulunan}")
    print("[+] K3 ciftli A uretim esigi == net_olcum.csv")

    # --- K4, K5 ---
    ortak = set(tekil.Dosya_Adi) & set(egitim.Dosya_Adi)
    if ortak:
        dur(f"K4 ortak sha {len(ortak)}")
    tut = ~test.duplicated("Dosya_Adi", keep="first").to_numpy()
    dn = test[tut].reset_index(drop=True)
    farkli = int((test.groupby("Dosya_Adi").Etiket.nunique() > 1).sum())
    if len(dn) != b.BEKLENEN_DOT_NET_TEST_TEKIL or farkli:
        dur(f"K5 {len(dn)}, farkli etiket {farkli}")
    print(f"[+] K4 ortak sha 0; K5 Dot_Net_test tekil {len(dn)}, farkli etiket 0")

    skor_a = {M2D: m2d.predict_proba(tekil[DIZGELI_TIPLI])[:, 1], NATIVE: native.predict_proba(tekil[nk])[:, 1]}
    skor_dn = {ad: skor_g[ad][1][tut] for ad in (M2D, NATIVE)}

    # --- K6: 2(b) yeniden uretimi ---
    is2b = pd.read_csv(os.path.join(BURASI, "is2b_a_kumesi.csv"), dtype={"hedef": str})
    denetlenen = 0
    for bolum, df, sk in (("A tekil", tekil, skor_a), ("Dot_Net_test tekil", dn, skor_dn)):
        for hd in HEDEFLER:
            for ad in (M2D, NATIVE):
                for (bo, h2, a2, tur), r in b.hucreler(bolum, df, sk[ad], esik[(hd, ad)], ad, hd).items():
                    q = is2b[(is2b.bolum == bo) & (is2b.hedef == str(h2)) & (is2b.model == a2) & (is2b.tur == tur)].iloc[0]
                    if (r["kacan"]["k"], r["kacan"]["n"], r["YA"]["k"], r["YA"]["n"]) != (q.kacan_k, q.kacan_n, q.YA_k, q.YA_n) \
                            or abs(round(r["AUC"], 4) - q.AUC) > 1e-9:
                        dur(f"K6 {bo} H {h2} {a2} {tur}")
                    denetlenen += 1
    print(f"[+] K6 {denetlenen} satir (k/n ve AUC) == is2b_a_kumesi.csv")

    # --- K7: ROC kodu ---
    for ad_k, df, sk in (("A", tekil, skor_a), ("Dot_Net_test", dn, skor_dn)):
        y, dll = df.Etiket.to_numpy(), df.DLL_mi.to_numpy() == 1
        for tur, m in (("EXE", ~dll), ("DLL", dll), ("hepsi", np.ones_like(dll))):
            h_ = Hucre(sk[M2D][m], sk[NATIVE][m], y[m], dll[m].astype(int) * 2 + y[m])
            for ad in (M2D, NATIVE):
                if abs(auc_roc(*h_.roc(ad)) - roc_auc_score(y[m], sk[ad][m])) > 1e-12:
                    dur(f"K7 {ad_k} {tur} {ad} AUC")
    y, dll = tekil.Etiket.to_numpy(), tekil.DLL_mi.to_numpy() == 1
    h_ = Hucre(skor_a[M2D], skor_a[M2D], y, dll.astype(int) * 2 + y)
    oz_fark = bootstrap(h_, [TOHUM, 99], 200)
    if any(np.any(v != 0) for v in oz_fark.values()):
        dur("K7 modelin kendisiyle farki 0 degil")
    h2_ = Hucre(skor_a[M2D], skor_a[NATIVE], y, dll.astype(int) * 2 + y)
    i1, i2 = bootstrap(h2_, [TOHUM, 98], 200), bootstrap(h2_, [TOHUM, 98], 200)
    if any(not np.array_equal(i1[k], i2[k]) for k in i1):
        dur("K7 ayni tohumla bootstrap ayni degil")
    print(f"[+] K7 AUC == roc_auc_score (1e-12), kendisiyle fark 0, tohum belirlenimci ({time.monotonic() - t0:.0f} sn)")
    print("[+] Tum gecitler tuttu; olcum basliyor\n")

    hepsini_olc({"Dot_Net_test": (dn, skor_dn[M2D], skor_dn[NATIVE]), "A": (tekil, skor_a[M2D], skor_a[NATIVE])},
                os.path.join(BURASI, "is2c_esit_ya.csv"), os.path.join(BURASI, "is2c_hukum.csv"))
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn) -> is2c_esit_ya.csv, is2c_hukum.csv")
