"""
Is 7 (c) - son modelin egitim ornegindeki essiz dosya sayisi, egitim / dogrulama / test ortusmesi ve
yanlis alarm kaymasi (on kayit: ciftleme_on_kayit.md, olcumden once).

Ornek son_model.py ile AYNI kodla yeniden kurulur (ortak_deney.tip_ici_dengeli(havuz, 483.224, 42));
egitim YENILENMEZ. Ortusme: O1 sha (Dosya_Adi), O2 86 model sutunu (float32) birebir ayni vektor.
Kayma olcumu tekil dosyalarla; esikler meta'dan (EXE 0,70 / DLL 0,61), DEGISTIRILMEZ.
Kullanim: python ciftleme_c.py   (log icin > ciftleme_c.log)
"""

import hashlib
import os
import sys
import time

import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", ".."))
import ortak_deney as o  # noqa: E402
import tahmin_et  # noqa: E402

DOGRULAMA_HAFTA, BOYUT, TOHUM, KUCUK_N = 48, 483_224, 42, 30


def sha16(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()[:16]


def yukle_adli(adlar):
    d = o.yukle(adlar)
    a = pd.concat([pd.read_parquet(os.path.join(o.EMBER2024_PARQUET_KLASORU, f"{x}.parquet"), columns=["Dosya_Adi"])
                   for x in adlar], ignore_index=True)
    if len(a) != len(d):
        sys.exit("Hata: Dosya_Adi satir sayisi tutmuyor")
    d["Dosya_Adi"] = a.Dosya_Adi.to_numpy()
    return d


def vektor_hash(df):
    return pd.util.hash_pandas_object(df[o.E3_KOLON].astype("float32"), index=False).to_numpy()


def oran(k, n):
    if n == 0:
        return "-", float("nan"), float("nan"), float("nan")
    alt, ust = o.wilson(k, n)
    return f"%{100 * k / n:.3f} [{alt:.3f}-{ust:.3f}] ({k}/{n})", 100 * k / n, alt, ust


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True, encoding="utf-8")
    t0 = time.monotonic()
    paket = tahmin_et.model_yukle()                      # SHA-256 dogrulamali (Kural 10)
    model, meta = paket["model"], paket["meta"]
    model.set_params(n_jobs=8)
    esik = meta["esikler"]

    # --- G5 ---
    g5 = True
    for a, beklenen in meta["egitim_verisi"]["parquet_sha256_16"].items():
        h = sha16(os.path.join(o.EMBER2024_PARQUET_KLASORU, f"{a}.parquet"))
        if h != beklenen:
            g5 = False
            print(f"[!] G5 {a} sha256_16 {h} != meta {beklenen}")
    egitim = yukle_adli(["Win32_train", "Win64_train"])
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    if o.tamami(havuz, "E3") != BOYUT:
        g5 = False
        print(f"[!] G5 havuz E3 tamami {o.tamami(havuz, 'E3')} != {BOYUT}")
    ornek = o.tip_ici_dengeli(havuz, BOYUT, TOHUM)
    hucre = {f"{int(d)}_{e}": int(n) for (d, e), n in ornek.groupby(["DLL_mi", "Etiket"]).size().items()}
    if hucre != meta["egitim_verisi"]["orneklem_hucreler_DLLmi_Etiket"] or len(havuz) != meta["egitim_verisi"]["havuz_satir"]:
        g5 = False
        print(f"[!] G5 hucreler {hucre} / havuz {len(havuz)} != meta")
    if not g5:
        sys.exit("GECIT BASARISIZ (G5): hukum yok")
    print(f"[+] G5: Parquet sha256_16 x4, havuz {len(havuz)}, ornek hucreleri {hucre} == meta ({time.monotonic() - t0:.0f} sn)")

    # --- Essiz dosya sayisi ---
    print("\n=== Egitim ornegi (483.224 satir) ===")
    kopya = ornek.groupby("Dosya_Adi").size()
    print(f"  essiz dosya {ornek.Dosya_Adi.nunique()} (%{100 * ornek.Dosya_Adi.nunique() / len(ornek):.2f}); "
          f"iki kopyasi birden ornekte {int((kopya >= 2).sum())}; kopya dagilimi {kopya.value_counts().sort_index().to_dict()}")
    for (d, e), g in ornek.groupby(["DLL_mi", "Etiket"]):
        hv = havuz[(havuz.DLL_mi == d) & (havuz.Etiket == e)]
        print(f"  hucre DLL_mi={int(d)} Etiket={e}: satir {len(g)}, essiz {g.Dosya_Adi.nunique()} | havuzda satir {len(hv)}, essiz {hv.Dosya_Adi.nunique()}")
    print(f"  havuz: satir {len(havuz)}, essiz {havuz.Dosya_Adi.nunique()}; dogrulama: satir {len(dog)}, essiz {dog.Dosya_Adi.nunique()}")

    test = yukle_adli(["Win32_test", "Win64_test"])
    S = {"ornek": set(ornek.Dosya_Adi), "havuz": set(havuz.Dosya_Adi), "dogrulama": set(dog.Dosya_Adi), "test": set(test.Dosya_Adi)}
    print("\n=== O1 sha ortusmesi (essiz) ===")
    for a, b in (("ornek", "dogrulama"), ("ornek", "test"), ("havuz", "dogrulama"), ("dogrulama", "test"), ("havuz", "test")):
        print(f"  {a} x {b}: {len(S[a] & S[b])}")

    # --- Kayma: tekil zararsizlar, dogrulama ve test ---
    dog_t = dog[~dog.Dosya_Adi.duplicated()]
    test_t = test[~test.Dosya_Adi.duplicated()]
    dog_z, test_z = dog_t[dog_t.Etiket == 0].copy(), test_t[test_t.Etiket == 0].copy()
    dog_z_c = dog[dog.Etiket == 0]
    del egitim, test
    p_dog_c = model.predict_proba(dog_z_c[o.E3_KOLON])[:, 1]
    dog_z["p"] = model.predict_proba(dog_z[o.E3_KOLON])[:, 1]
    test_z["p"] = model.predict_proba(test_z[o.E3_KOLON])[:, 1]
    print(f"\n[*] tahminler hazir ({time.monotonic() - t0:.0f} sn)")

    print("\n=== Betimleyici: esik yeniden secimi (DEGISTIRILMEZ) ===")
    for tur, deger in (("EXE", 0), ("DLL", 1)):
        c = float(np.quantile(p_dog_c[dog_z_c.DLL_mi.to_numpy() == deger], 0.99, method="higher"))
        t = float(np.quantile(dog_z.p[dog_z.DLL_mi == deger], 0.99, method="higher"))
        print(f"  {tur}: ciftli dogrulama -> {c:.4f} (meta {esik[tur]}), tekil dogrulama -> {t:.4f}")

    vh = set(vektor_hash(ornek))
    for df in (dog_z, test_z):
        df["O1"] = df.Dosya_Adi.isin(S["ornek"]).to_numpy()
        df["O2"] = np.isin(vektor_hash(df), np.fromiter(vh, dtype=np.uint64))
    print("\n=== Kayma: tekil zararsizlar (dogrulama hafta 48-51, test 52-63) ===")
    for tur, deger in (("DLL", 1), ("EXE", 0)):
        tau = esik[tur]
        d, t = dog_z[dog_z.DLL_mi == deger], test_z[test_z.DLL_mi == deger]
        ya_d, ya_t = (d.p > tau).mean() * 100, (t.p > tau).mean() * 100
        print(f"\n  [{tur}, esik {tau}] YA dogrulama {oran(int((d.p > tau).sum()), len(d))[0]} | test {oran(int((t.p > tau).sum()), len(t))[0]}")
        for tanim in ("O1", "O2"):
            sd, st = oran(int(d[tanim].sum()), len(d)), oran(int(t[tanim].sum()), len(t))
            alt = {}
            for ad, df in (("dog", d), ("test", t)):
                for grup, m in (("ortusen", df[tanim]), ("ortusmeyen", ~df[tanim])):
                    alt[(ad, grup)] = oran(int((df.p[m] > tau).sum()), int(m.sum()))
            print(f"    {tanim}: ortusen pay dogrulama {sd[0]}, test {st[0]}")
            for (ad, grup), r in alt.items():
                print(f"       YA {ad:<4} {grup:<10}: {r[0]}")
            n_ort = int(d[tanim].sum())
            if tanim == "O1" and n_ort == 0:
                hukum = "sha duzeyinde dogrulama ortusmesi yok; kayma bu mekanizmayla aciklanamaz"
            elif n_ort < KUCUK_N:
                hukum = f"hukum yok: ortusen n kucuk ({n_ort} < {KUCUK_N})"
            else:
                s_t = st[1] / 100
                ya_karsi = s_t * alt[("dog", "ortusen")][1] + (1 - s_t) * alt[("dog", "ortusmeyen")][1]
                pay = (ya_karsi - ya_d) / (ya_t - ya_d) if ya_t != ya_d else float("nan")
                i = sd[2] > st[3]
                ii = alt[("dog", "ortusen")][3] < alt[("dog", "ortusmeyen")][2]
                iii = pay > 0
                print(f"       karsi-olgusal YA*_dog %{ya_karsi:.3f}; aciklanan pay {pay:.3f} | kosullar (i) {i} (ii) {ii} (iii) {iii}")
                if i and ii and iii:
                    hukum = f"KISMEN DESTEKLENDI: aciklanan pay {pay:.3f}"
                elif st[2] > sd[3]:
                    hukum = "desteklenmedi (ortusme payi testte anlamli olarak YUKSEK)"
                else:
                    hukum = "gosterilemedi"
            print(f"    -> {tanim} {tur}: {hukum}")
    print(f"\n[+] bitti ({time.monotonic() - t0:.0f} sn)")
