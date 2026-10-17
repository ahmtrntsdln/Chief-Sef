"""
Adim 3 (on kayit: on_kayit_esik_boyut.md) - esik dogrulama diliminden, test bir kez; son boyut kurali.

A) Yeniden olcum: RF/LGBM x E2/E3 x 300 bin x 5 tohum. Egitim havuzu hafta 0-47, esik hafta
   48-51 (iki sinif), test hafta 52-63 SABIT esikle bir kez. (2c esigi testten secmisti.)
B) RF E3 483.224 (havuzda tip-ici dengeli en buyuk), tohum 42/1/2.
C) Kural: kazanc = ort(300K) - ort(483K) DLL kacan; s = max(std) (ddof=1, tohum 42/1/2);
   kazanc < s -> 300.000, degilse 483.224. Kaynak: dosya boyutu, bellek, tek dosya tahmin suresi.

Her hucre esik_boyut.csv'ye eklenir; yeniden calistirinca biten hucreler atlanir.
Kullanim: python esik_boyut.py   ->  esik_boyut.csv, kaynak.csv, esik_boyut_sonuc.md
"""

import gc
import os
import sys
import time

import joblib
import numpy as np
import pandas as pd
import psutil

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
sys.path.insert(0, os.path.join(BURASI, "..", "2c"))
import ortak_deney as o  # noqa: E402
from karar_tablosu import aralik, mcnemar  # noqa: E402

DOGRULAMA_HAFTA = 48          # 48-51 dogrulama; 0-47 havuz
ONEK = "V48_"
CEKIRDEK = 8
BUYUK = 483_224
KURAL_TOHUM = [42, 1, 2]
MODEL_KLASORU = os.path.join(o.EMBER2024_KLASORU, "sonuc", "modeller")   # repoda yok


def kaynak_olc(anahtar, model, ornek_x):
    os.makedirs(MODEL_KLASORU, exist_ok=True)
    yol = os.path.join(MODEL_KLASORU, f"{anahtar}.joblib")
    joblib.dump(model, yol)                      # sikistirmasiz
    agac_bayt = sum(e.tree_.__getstate__()["nodes"].nbytes + e.tree_.__getstate__()["values"].nbytes
                    for e in model.estimators_)
    del model
    gc.collect()
    surec = psutil.Process()
    rss0 = surec.memory_info().rss
    m = joblib.load(yol)
    rss1 = surec.memory_info().rss
    m.set_params(n_jobs=1)
    for _ in range(20):
        m.predict_proba(ornek_x)
    sureler = []
    for _ in range(1000):
        t = time.perf_counter()
        m.predict_proba(ornek_x)
        sureler.append(1000 * (time.perf_counter() - t))
    return {"hucre": anahtar, "dosya_MB": round(os.path.getsize(yol) / 2**20, 1),
            "rss_artis_MB": round((rss1 - rss0) / 2**20, 1), "agac_dizileri_MB": round(agac_bayt / 2**20, 1),
            "tahmin_ms_medyan": round(float(np.median(sureler)), 2),
            "tahmin_ms_p95": round(float(np.percentile(sureler, 95)), 2),
            "dugum_sayisi": int(sum(e.tree_.node_count for e in m.estimators_))}


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim, test, yerel = o.veri()
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    print(f"[*] havuz {len(havuz)} (hafta 0-{DOGRULAMA_HAFTA - 1}), dogrulama {len(dog)} "
          f"(hafta {DOGRULAMA_HAFTA}-51), test {len(test)}, yerel {len(yerel)}")
    if o.tamami(havuz, "E3") != BUYUK:
        sys.exit(f"Hata: havuz E3 tamami {o.tamami(havuz, 'E3')} != on kayitli {BUYUK}")

    hucreler = [(alg, ad, 300_000, t) for alg in ("RF", "LGBM") for ad in ("E2", "E3") for t in o.TOHUMLAR]
    hucreler += [("RF", "E3", BUYUK, t) for t in KURAL_TOHUM]
    sonuc = o.SonucCSV(os.path.join(BURASI, "esik_boyut.csv"))
    kaynak = o.SonucCSV(os.path.join(BURASI, "kaynak.csv"))
    kaynak_hedef = {f"{ONEK}RF_E3_300000_42", f"{ONEK}RF_E3_{BUYUK}_42"}
    yapilacak = [h for h in hucreler
                 if f"{ONEK}{h[0]}_{h[1]}_{h[2]}_{h[3]}" not in sonuc.biten
                 or (f"{ONEK}{h[0]}_{h[1]}_{h[2]}_{h[3]}" in kaynak_hedef
                     and f"{ONEK}{h[0]}_{h[1]}_{h[2]}_{h[3]}" not in kaynak.biten)]
    print(f"[*] {len(hucreler)} hucre, {len(yapilacak)} kosulacak")
    ornek_x = test[o.E3_KOLON].iloc[[0]]
    for i, (alg, ad, boyut, tohum) in enumerate(yapilacak, 1):
        satir, model = o.hucre_kos(alg, ad, boyut, tohum, havuz, test, yerel, CEKIRDEK,
                                   dogrulama=dog, onek=ONEK, model_dondur=True)
        if satir["hucre"] not in sonuc.biten:
            sonuc.ekle(satir)
        if satir["hucre"] in kaynak_hedef and satir["hucre"] not in kaynak.biten:
            kaynak.ekle(kaynak_olc(satir["hucre"], model, ornek_x))
        del model
        o.ilerleme(i, len(yapilacak), t0, f"| {alg} {ad} {boyut} t{tohum}: DLL kacan {satir['DLL_kacan_%@1']}, "
                   f"test YA EXE/DLL {satir['EXE_test_YA_%@1']}/{satir['DLL_test_YA_%@1']}")

    # --- Ozet ve kurallar ---
    df = pd.read_csv(sonuc.yol)
    kay = pd.read_csv(kaynak.yol)
    R = []
    a = R.append
    a("# Eşik doğrulamadan, test bir kez; son boyut (ön kayıt: on_kayit_esik_boyut.md)\n")
    a(f"Havuz hafta 0-{DOGRULAMA_HAFTA - 1} ({len(havuz):,}), eşik doğrulaması hafta {DOGRULAMA_HAFTA}-51 "
      f"({len(dog):,}, iki sınıf), test hafta 52-63 ({len(test):,}) SABİT eşikle bir kez. Hücre: tohum "
      "ortalaması (en düşük–en yüksek). 2c'deki `karar_tablosu.md` eşiği TESTTEN seçmişti; bu tablo onun "
      "yerini alan ölçümdür.\n")
    a("## A. 300 bin, 5 tohum\n")
    a("| Model | DLL kaçan % (ANA) | EXE kaçan % | Test YA % EXE / DLL (hedef 1) | Doğrulama YA % EXE / DLL | "
      "Yerel YA % EXE / DLL | AUC |")
    a("|---|---|---|---|---|---|---|")
    p3 = df[df.boyut == 300_000]
    for (alg, ad), d in p3.groupby(["algoritma", "aday"], sort=False):
        a(f"| {alg} {ad} | {aralik(d['DLL_kacan_%@1'])} | {aralik(d['EXE_kacan_%@1'])} | "
          f"{d['EXE_test_YA_%@1'].mean():.2f} / {d['DLL_test_YA_%@1'].mean():.2f} | "
          f"{d['EXE_dogrulama_YA_%'].mean():.2f} / {d['DLL_dogrulama_YA_%'].mean():.2f} | "
          f"{d['EXE_yerel_YA_%@1'].mean():.2f} / {d['DLL_yerel_YA_%@1'].mean():.2f} | {aralik(d['genel_AUC'], 4)} |")
    a("\n### Ölçütlerin mekanik uygulaması (karar_olcutleri.md, değiştirilmedi)\n")

    def alarm(alg, ad, tohum, boyut=300_000):
        z = np.load(os.path.join(o.YEREL_TAHMIN_KLASORU, f"{ONEK}{alg}_{ad}_{boyut}_{tohum}.npz"))
        dll = yerel.DLL_mi.to_numpy() == 1
        return {"EXE": z["p"][~dll] > float(z["esik_EXE"]), "DLL": z["p"][dll] > float(z["esik_DLL"])}

    a("| A vs B | DLL kaçan A−B (tohum oynaması) | Ölçüt 1 | McNemar anlamlı kötü (A / B) EXE | DLL |")
    a("|---|---|---|---|---|")
    for A, B in [(("RF", "E2"), ("RF", "E3")), (("LGBM", "E2"), ("LGBM", "E3")),
                 (("RF", "E2"), ("LGBM", "E2")), (("RF", "E3"), ("LGBM", "E3"))]:
        ka = p3[(p3.algoritma == A[0]) & (p3.aday == A[1])].sort_values("tohum")["DLL_kacan_%@1"]
        kb = p3[(p3.algoritma == B[0]) & (p3.aday == B[1])].sort_values("tohum")["DLL_kacan_%@1"]
        fark, oyn = ka.mean() - kb.mean(), max(ka.max() - ka.min(), kb.max() - kb.min())
        o1 = "EŞİT" if abs(fark) <= oyn else (f"{A[0]} {A[1]}" if fark < 0 else f"{B[0]} {B[1]}")
        mc = []
        for tur in ("EXE", "DLL"):
            r = [mcnemar(alarm(*A, t)[tur], alarm(*B, t)[tur]) for t in o.TOHUMLAR]
            mc.append(f"{sum(ya > yb and p < 0.05 for ya, yb, p in r)} / {sum(yb > ya and p < 0.05 for ya, yb, p in r)}")
        a(f"| {A[0]} {A[1]} vs {B[0]} {B[1]} | {fark:+.2f} ({oyn:.2f}) | {o1} | {mc[0]} | {mc[1]} |")

    a("\n## B/C. Son boyut kuralı (RF E3, tohum 42/1/2)\n")
    k3 = df[(df.algoritma == "RF") & (df.aday == "E3") & (df.boyut == 300_000) & df.tohum.isin(KURAL_TOHUM)]
    kb = df[(df.algoritma == "RF") & (df.aday == "E3") & (df.boyut == BUYUK) & df.tohum.isin(KURAL_TOHUM)]
    if len(k3) == len(kb) == len(KURAL_TOHUM):
        kazanc = k3["DLL_kacan_%@1"].mean() - kb["DLL_kacan_%@1"].mean()
        s = max(k3["DLL_kacan_%@1"].std(ddof=1), kb["DLL_kacan_%@1"].std(ddof=1))
        karar = "300.000" if kazanc < s else f"{BUYUK:,}".replace(",", ".")
        a("| Boyut | DLL kaçan % (tohum 42 / 1 / 2) | ort. | std | EXE kaçan % | Test YA % EXE / DLL | Yerel YA % EXE / DLL |")
        a("|---|---|---|---|---|---|---|")
        for ad, d in (("300.000", k3), (f"{BUYUK:,}".replace(",", "."), kb)):
            d = d.set_index("tohum").loc[KURAL_TOHUM]
            a(f"| {ad} | {' / '.join(f'{v:.2f}' for v in d['DLL_kacan_%@1'])} | {d['DLL_kacan_%@1'].mean():.2f} | "
              f"{d['DLL_kacan_%@1'].std(ddof=1):.2f} | {d['EXE_kacan_%@1'].mean():.2f} | "
              f"{d['EXE_test_YA_%@1'].mean():.2f} / {d['DLL_test_YA_%@1'].mean():.2f} | "
              f"{d['EXE_yerel_YA_%@1'].mean():.2f} / {d['DLL_yerel_YA_%@1'].mean():.2f} |")
        a(f"\nkazanç = {kazanc:+.3f} puan, s = {s:.3f} → kazanç {'<' if kazanc < s else '≥'} s → "
          f"**son boyut {karar}** (mekanik kural).\n")
    a("## Kaynak (tohum 42 modelleri; kurala girmez)\n")
    a("| Model | Dosya MB (joblib, sıkıştırmasız) | RSS artışı MB | Ağaç dizileri MB | Düğüm | Tahmin ms medyan / p95 (tek satır, n_jobs=1, özellik çıkarma hariç) |")
    a("|---|---|---|---|---|---|")
    for _, r in kay.iterrows():
        a(f"| {r.hucre} | {r.dosya_MB} | {r.rss_artis_MB} | {r.agac_dizileri_MB} | {r.dugum_sayisi:,} | "
          f"{r.tahmin_ms_medyan} / {r.tahmin_ms_p95} |")
    metin = "\n".join(R) + "\n"
    with open(os.path.join(BURASI, "esik_boyut_sonuc.md"), "w", encoding="utf-8") as f:
        f.write(metin)
    print(metin)
    print(f"[+] {(time.monotonic() - t0) / 60:.1f} dk")
