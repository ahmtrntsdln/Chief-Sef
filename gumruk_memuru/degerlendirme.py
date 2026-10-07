"""
Sef Projesi - Degerlendirme duzenegi (zaman + aile ayrimi, sizinti kontrolu)
============================================================

RF ile boosting'i AYNI kosullarda (ayni ozellikler, ayni egitim orneklemi,
ayni tohumlar, ayni esik prosedurü) karsilastirir ve markdown rapor yazar.

Ayrim (Kritik Kural 6 + aile):
  egitim (eski)  : EMBER 2018 train, Ocak-Ekim. Son %20'lik donemi ESIK
                   DOGRULAMASI icin ayrilir (modeli o doneme egitmez).
  test "zaman"   : Kasim-Aralik, tum dosyalar (aileler egitimde gorulmus olabilir).
  test "zaman+aile": ayni test, ama zararlilardan SADECE egitimde (dogrulama
                   dahil) hic gorulmeyen aileler. Ailesi bilinmeyen ("") zararlilar
                   buraya ALINMAZ: yeni olduklari kanitlanamaz. Zararsizlarin
                   ailesi yok, oldugu gibi kalir.

Esik: sabit yanlis pozitif orani (FPR) icin esik DOGRULAMA zararsizlarindan
secilir, teste dokunmaz; raporda testte GERCEKLESEN FPR ve yakalama orani
(TPR) yan yana. Tek model, tek esik: alt grup (.NET) FPR'si hedeften sapiyorsa
bu gercek bir bulgudur, duzeltilmez.

Sizinti kontrolleri (egitime baslamadan, ihlalde SizintiHatasi ile durur):
  zaman sirasi, dogrulama-egitim sirasi, dosya kimligi (Dosya_Adi) cakismasi,
  ozellik listesinde etiket/meta sutunu, aile-ayrik kume gercekten ayrik mi.
  Sadece raporlananlar: birebir ayni ozellik vektoru orani, sinif dengesi.

Kullanim:
  python degerlendirme.py [--cikti rapor.md] [--ozellik-seti temel|dizgeli]
                          [--egitim-ornek 100000] [--tohumlar 5]
On kosul: python ember2018_tam_cikar.py train  ve  ... test.
"""

import argparse
import sys
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.metrics import roc_auc_score

from dizge_ozellikleri import EMBER2018_DIZGE_SUTUNLARI
from rf_egit_gercek import OZELLIKLER

try:
    from lightgbm import LGBMClassifier
except ImportError:   # requirements-experimental.txt
    LGBMClassifier = None

YASAK_OZELLIK = {"Etiket", "Aile", "Ay", "Hafta", "Dosya_Adi"}
FPR_HEDEFLERI = (0.01, 0.001)
DOGRULAMA_ORANI = 0.2          # egitim DONEMLERININ son %20'si
MIN_BEKLENEN_YP = 10           # alt grupta hedef FPR'de beklenen yanlis pozitif < 10 -> "n az"
SUPHELI_AUC = 0.999            # Kural 4: bundan yuksek AUC sizinti suphesi
OZELLIK_SETLERI = {
    "temel": OZELLIKLER,
    "dizgeli": OZELLIKLER + ["DLL_mi"] + EMBER2018_DIZGE_SUTUNLARI,
}


class SizintiHatasi(RuntimeError):
    pass


# --------------------------------------------------------------------------
# Modeller: ayni girdi, ayarsiz varsayilanlar (ayar bir tarafa avantaj olmasin)
# --------------------------------------------------------------------------

def model_uretecleri():
    m = {
        "RandomForest": lambda s: RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=s),
        "HistGradientBoosting": lambda s: HistGradientBoostingClassifier(random_state=s),
    }
    if LGBMClassifier is not None:
        m["LightGBM"] = lambda s: LGBMClassifier(random_state=s, verbose=-1)
    return m


# --------------------------------------------------------------------------
# Bolme
# --------------------------------------------------------------------------

def donem_sirasi(seri: pd.Series) -> list:
    """Donem etiketlerini kronolojik sirala. ISO benzeri metin ('2018-11') ve
    sayi desteklenir; ikisi de degilse sozluksel sira zamani bozabilir -> dur."""
    degerler = sorted(seri.dropna().unique())
    if not degerler:
        raise SizintiHatasi("Zaman sutunu bos.")
    if not all(isinstance(d, (int, float, np.integer, np.floating)) for d in degerler):
        if not all(isinstance(d, str) and d[:4].isdigit() for d in degerler):
            raise SizintiHatasi(f"Zaman etiketleri sirali degil/taninmiyor: {degerler[:3]}...")
    return degerler


def zaman_bol(egitim: pd.DataFrame, zaman: str, oran: float = DOGRULAMA_ORANI):
    """Egitimi donem sinirindan 'fit' ve 'dogrulama'ya ayirir. Dogrulama: KAYITLARIN
    en az `oran`'ini kapsayan en son donemler. Donem SAYISI degil kayit payi: EMBER
    2018 train'de appeared 2006'ya kadar gidiyor (~140 ay, 2018 oncesi sadece 50K
    zararsiz); donem sayisinin %20'si son 28 ay = tum 2018 olur ve fit'te hic
    zararli kalmaz."""
    donemler = donem_sirasi(egitim[zaman])
    if len(donemler) < 2:
        raise SizintiHatasi("Dogrulama ayirmak icin en az 2 egitim donemi gerekir.")
    sayim = egitim[zaman].value_counts()
    dogrulama_donemleri, kapsanan = [], 0
    for donem in reversed(donemler[1:]):          # en eski donem her zaman fit'te kalir
        if kapsanan >= oran * len(egitim):
            break
        dogrulama_donemleri.append(donem)
        kapsanan += sayim[donem]
    m = egitim[zaman].isin(set(dogrulama_donemleri))
    fit, dog = egitim[~m].copy(), egitim[m].copy()
    for ad, x in (("fit", fit), ("dogrulama", dog)):
        if x["Etiket"].nunique() < 2:
            raise SizintiHatasi(f"{ad} kumesinde tek sinif var ({x['Etiket'].unique().tolist()}); "
                                f"zaman bolmesi veriye uymuyor.")
    return fit, dog


def aile_ayrik_test(test: pd.DataFrame, gorulen_aileler: set) -> pd.DataFrame:
    """Zararlilar: ailesi bilinen VE egitimde gorulmeyen. Zararsizlar: hepsi."""
    aile = test["Aile"].astype(str)
    yeni = (test["Etiket"] == 1) & (aile != "") & ~aile.isin(gorulen_aileler)
    return test[(test["Etiket"] == 0) | yeni].copy()


# --------------------------------------------------------------------------
# Sizinti kontrolleri
# --------------------------------------------------------------------------

def sizinti_kontrolleri(fit, dogrulama, test, test_aile, kolonlar, zaman_egitim, zaman_test):
    """[(ad, durum, ayrinti)] dondurur; sert ihlalde SizintiHatasi."""
    sonuc = []

    def sert(ad, ihlal, ayrinti):
        sonuc.append((ad, "IHLAL" if ihlal else "gecti", ayrinti))
        if ihlal:
            raise SizintiHatasi(f"{ad}: {ayrinti}")

    # 1) ozellik listesi
    yasak = sorted(set(kolonlar) & YASAK_OZELLIK)
    sert("ozellik listesinde etiket/meta yok", bool(yasak), f"yasak sutunlar: {yasak}" if yasak else
         f"{len(kolonlar)} ozellik")

    # 2) zaman sirasi (kronolojik karsilastirma, her iki yanin tum donemleri)
    tum_egitim = pd.concat([fit[zaman_egitim], dogrulama[zaman_egitim]])
    e_son = max(donem_sirasi(tum_egitim))
    t_ilk = min(donem_sirasi(test[zaman_test]))
    sert("egitim donemleri < test donemleri", not e_son < t_ilk, f"egitim son {e_son}, test ilk {t_ilk}")
    f_son, d_ilk = max(donem_sirasi(fit[zaman_egitim])), min(donem_sirasi(dogrulama[zaman_egitim]))
    sert("egitim(fit) < esik dogrulamasi", not f_son < d_ilk, f"fit son {f_son}, dogrulama ilk {d_ilk}")

    # 3) dosya kimligi cakismasi
    if "Dosya_Adi" in test:
        kimlik = set(fit["Dosya_Adi"]) | set(dogrulama["Dosya_Adi"])
        ortak = kimlik & set(test["Dosya_Adi"])
        sert("egitim/test dosya kimligi (Dosya_Adi) ortak degil", bool(ortak), f"{len(ortak)} ortak dosya")

    # 4) aile-ayrik kume gercekten ayrik mi
    gorulen = set(fit["Aile"].astype(str)) | set(dogrulama["Aile"].astype(str))
    zararli_aile = set(test_aile[test_aile["Etiket"] == 1]["Aile"].astype(str))
    kesisim = (zararli_aile & gorulen) | ({""} & zararli_aile)
    sert("zaman+aile test kumesinde egitim ailesi yok", bool(kesisim), f"{len(zararli_aile)} test ailesi, "
         f"kesisim {sorted(kesisim)[:3]}" if kesisim else f"{len(zararli_aile)} test ailesi, kesisim 0")

    # 5) sadece rapor: birebir ayni ozellik vektoru
    egit_hash = set(map(tuple, pd.concat([fit, dogrulama])[kolonlar].to_numpy()))
    ayni = np.fromiter((tuple(r) in egit_hash for r in test[kolonlar].to_numpy()), bool, len(test))
    sonuc.append(("birebir ayni ozellik vektoru (sadece rapor)", "bilgi",
                  f"testin %{100 * ayni.mean():.1f}'i egitimde ayni vektorle var "
                  f"(5 ozellikle dogal; etiket celiskisi olcumu bozmaz, ama kolaylastirir)"))
    return sonuc


# --------------------------------------------------------------------------
# Metrikler
# --------------------------------------------------------------------------

def esik_sec(p_zararsiz_dogrulama: np.ndarray, fpr: float) -> float:
    """Dogrulama zararsizlarinin en fazla `fpr` kadari esigin USTUNDE kalir."""
    return float(np.quantile(p_zararsiz_dogrulama, 1 - fpr, method="higher"))


def tpr_fpr(y, p, esik):
    """(gerceklesen FPR, TPR, zararsiz n, zararli n); bos taraf icin nan."""
    zararsiz, zararli = y == 0, y == 1
    fpr = (p[zararsiz] > esik).mean() if zararsiz.any() else np.nan
    tpr = (p[zararli] > esik).mean() if zararli.any() else np.nan
    return fpr, tpr, int(zararsiz.sum()), int(zararli.sum())


def alt_gruplar(df: pd.DataFrame) -> dict:
    net = df["NET_mi"].to_numpy() == 1
    g = {"tum": np.ones(len(df), bool), "PE (.NET disi)": ~net, ".NET": net}
    if "DLL_mi" in df:
        dll = df["DLL_mi"].to_numpy() == 1
        g |= {"EXE": ~dll, "DLL": dll}
    return g


def olc(df: pd.DataFrame, p: np.ndarray, esikler: dict) -> list:
    """Her alt grup icin bir satir: AUC + her hedef FPR icin gerceklesen FPR/TPR."""
    y = df["Etiket"].to_numpy()
    satirlar = []
    for ad, m in alt_gruplar(df).items():
        ym, pm = y[m], p[m]
        satir = {"grup": ad, "n_zararsiz": int((ym == 0).sum()), "n_zararli": int((ym == 1).sum())}
        satir["AUC"] = roc_auc_score(ym, pm) if len(set(ym)) == 2 else np.nan
        for f, e in esikler.items():
            fpr, tpr, nz, _ = tpr_fpr(ym, pm, e)
            satir[f"FPR@{f}"], satir[f"TPR@{f}"] = fpr, tpr
            satir[f"az@{f}"] = nz * f < MIN_BEKLENEN_YP
        satirlar.append(satir)
    return satirlar


# --------------------------------------------------------------------------
# Calistirma
# --------------------------------------------------------------------------

def sinif_dengeli_ornek(df, n_toplam, tohum):
    n = min(n_toplam // 2, int(df["Etiket"].value_counts().min()))
    return df.groupby("Etiket", group_keys=False).sample(n=n, random_state=tohum)


def degerlendir(egitim, test, kolonlar, zaman_egitim="Ay", zaman_test="Ay",
                egitim_ornek=100_000, tohumlar=(42, 1, 2, 3, 4), log=print):
    """Tum akis; (sonuc DataFrame, sizinti kontrolleri, bilgi dict) dondurur."""
    fit, dog = zaman_bol(egitim, zaman_egitim)
    gorulen = set(fit["Aile"].astype(str)) | set(dog["Aile"].astype(str))
    test_aile = aile_ayrik_test(test, gorulen)
    kontroller = sizinti_kontrolleri(fit, dog, test, test_aile, kolonlar, zaman_egitim, zaman_test)
    for ad, durum, ayr in kontroller:
        log(f"  [{durum}] {ad}: {ayr}")
    if (dog["Etiket"] == 0).sum() * min(FPR_HEDEFLERI) < 1:
        log("  [uyari] dogrulama zararsiz sayisi en kucuk hedef FPR icin az; esik kaba olur.")

    testler = {"zaman": test, "zaman+aile": test_aile}
    kayit = []
    ilk = time.monotonic()
    for ad, uretec in model_uretecleri().items():
        for tohum in tohumlar:
            ornek = sinif_dengeli_ornek(fit, egitim_ornek, tohum)   # tum modellerde AYNI ornek
            model = uretec(tohum).fit(ornek[kolonlar], ornek["Etiket"])
            p_dog = model.predict_proba(dog[kolonlar])[:, 1]
            esikler = {f: esik_sec(p_dog[dog["Etiket"].to_numpy() == 0], f) for f in FPR_HEDEFLERI}
            for test_adi, t in testler.items():
                p = model.predict_proba(t[kolonlar])[:, 1]
                for satir in olc(t, p, esikler):
                    kayit.append({"model": ad, "test": test_adi, "tohum": tohum, **satir})
        log(f"  {ad}: {len(tohumlar)} tohum, {time.monotonic() - ilk:.0f} sn")
    bilgi = {
        "fit": len(fit), "dogrulama": len(dog), "test": len(test), "test_aile": len(test_aile),
        "fit_donem": (min(donem_sirasi(fit[zaman_egitim])), max(donem_sirasi(fit[zaman_egitim]))),
        "dog_donem": (min(donem_sirasi(dog[zaman_egitim])), max(donem_sirasi(dog[zaman_egitim]))),
        "test_donem": (min(donem_sirasi(test[zaman_test])), max(donem_sirasi(test[zaman_test]))),
        "egitim_ornek": egitim_ornek, "tohumlar": list(tohumlar),
        "gorulen_aile": len(gorulen),
        "test_zararli_aile": int(test_aile[test_aile.Etiket == 1]["Aile"].nunique()),
        "lightgbm": LGBMClassifier is not None,
    }
    return pd.DataFrame(kayit), kontroller, bilgi


# --------------------------------------------------------------------------
# Rapor
# --------------------------------------------------------------------------

def _pct(x):
    return "—" if pd.isna(x) else f"{100 * x:.2f}"


def _aralik(seri, yuzde=True):
    if seri.isna().all():
        return "—"
    k = 100 if yuzde else 1
    d = 2 if yuzde else 4
    return f"{k * seri.mean():.{d}f} ({k * seri.min():.{d}f}–{k * seri.max():.{d}f})"


def rapor_yaz(sonuc, kontroller, bilgi, kolonlar, ozellik_seti) -> str:
    s = []
    a = s.append
    a("# Değerlendirme raporu\n")
    a(f"Üretildi: {time.strftime('%Y-%m-%d %H:%M')} · komut: `python degerlendirme.py "
      f"--ozellik-seti {ozellik_seti} --egitim-ornek {bilgi['egitim_ornek']}`\n")
    a("## Kurulum\n")
    a(f"- Özellikler ({len(kolonlar)}, `{ozellik_seti}`): {', '.join(kolonlar[:8])}"
      f"{'…' if len(kolonlar) > 8 else ''}")
    a(f"- Eğitim(fit): {bilgi['fit']:,} kayıt, dönem {bilgi['fit_donem'][0]} → {bilgi['fit_donem'][1]}; "
      f"her tohumda sınıf dengeli {bilgi['egitim_ornek']:,} örnek, TÜM modellerde aynı")
    a(f"- Eşik doğrulaması: {bilgi['dogrulama']:,} kayıt, dönem {bilgi['dog_donem'][0]} → "
      f"{bilgi['dog_donem'][1]} (modelin eğitiminde YOK)")
    a(f"- Test `zaman`: {bilgi['test']:,} kayıt, dönem {bilgi['test_donem'][0]} → {bilgi['test_donem'][1]}")
    a(f"- Test `zaman+aile`: {bilgi['test_aile']:,} kayıt; zararlılar yalnızca eğitimde görülmeyen "
      f"{bilgi['test_zararli_aile']} aileden ({bilgi['gorulen_aile']} aile eğitimde görüldü); "
      f"ailesi bilinmeyen zararlılar dışarıda")
    modeller = list(sonuc["model"].unique())
    a(f"- Modeller (ayarsız varsayılanlar, {len(bilgi['tohumlar'])} tohum {bilgi['tohumlar']}): "
      f"{', '.join(modeller)}" + ("" if bilgi["lightgbm"] else
                                  " — LightGBM kurulu değil, atlandı (`requirements-experimental.txt`)"))
    a("- Esik: sabit FPR hedefi için DOĞRULAMA zararsızlarından; tek model, tek eşik, alt gruplara "
      "ayrı eşik YOK.\n")

    a("## Sızıntı kontrolleri\n")
    a("| Kontrol | Durum | Ayrıntı |\n|---|---|---|")
    for ad, durum, ayr in kontroller:
        a(f"| {ad} | {durum} | {ayr} |")
    a("")

    for f in FPR_HEDEFLERI:
        a(f"## Hedef FPR %{100 * f:g}: yakalama oranı (TPR %) ve gerçekleşen FPR %\n")
        a("Hücre: ortalama (en düşük–en yüksek tohum). `†` = alt grupta hedef FPR'de beklenen yanlış "
          "pozitif < 10 (zararsız n az), FPR/TPR güvenilmez.\n")
        for test_adi in ("zaman", "zaman+aile"):
            a(f"### Test: {test_adi}\n")
            a("| Grup | n zararsız / zararlı | " + " | ".join(f"{m} TPR | {m} FPR" for m in modeller) + " |")
            a("|---|---|" + "---|---|" * len(modeller))
            d = sonuc[sonuc["test"] == test_adi]
            for grup in d["grup"].unique():
                g = d[d["grup"] == grup]
                n = g.iloc[0]
                isaret = "†" if n[f"az@{f}"] else ""
                hucre = []
                for m in modeller:
                    gm = g[g["model"] == m]
                    hucre += [_aralik(gm[f"TPR@{f}"]) + isaret, _aralik(gm[f"FPR@{f}"]) + isaret]
                a(f"| {grup} | {int(n['n_zararsiz']):,} / {int(n['n_zararli']):,} | " + " | ".join(hucre) + " |")
            a("")

    a("## AUC\n")
    a("| Test | Grup | " + " | ".join(modeller) + " |\n|---|---|" + "---|" * len(modeller))
    for test_adi in ("zaman", "zaman+aile"):
        d = sonuc[sonuc["test"] == test_adi]
        for grup in d["grup"].unique():
            a(f"| {test_adi} | {grup} | " + " | ".join(
                _aralik(d[(d.grup == grup) & (d.model == m)]["AUC"], yuzde=False) for m in modeller) + " |")
    a("")

    uyarilar = []
    tum_auc = sonuc[(sonuc.grup == "tum")].groupby(["model", "test"])["AUC"].mean()
    for (m, t), v in tum_auc.items():
        if v > SUPHELI_AUC:
            uyarilar.append(f"{m}/{t}: AUC {v:.4f} > {SUPHELI_AUC} — Kural 4: sızıntı şüphesi, "
                            f"feature_importances_ ve sinsi örneklerle kontrol et.")
    a("## Okuma notları\n")
    a("- **Yorum eşiği:** tohumlar arası fark (parantez) modeller arası farktan büyük/benzerse model "
      "üstünlüğü iddia edilmez.")
    a("- `zaman+aile` satırları `zaman` satırlarından düşükse fark \"yeni aileye genelleme bedeli\"dir; "
      "zararsız tarafı değişmediği için FPR sütunları iki testte aynı tohumda yakın olmalı.")
    a("- Gerçekleşen FPR hedeften belirgin sapıyorsa (özellikle .NET veya DLL'de) tek eşiğin o grupta "
      "kalibre olmadığı anlamına gelir; bu düzeltilmedi, bulgu olarak bırakıldı.")
    a("- Kullanılmayanlar: tip-içi dengeli eğitim, kalibrasyon, π önsel düzeltmesi "
      "(PROJE_DURUMU.md); üretim eşiği için ayrıca ele alınmalı.")
    a("- Veri EMBER'in örnekleme dağılımıdır (zararlı oranı gerçek yaygınlık DEĞİL); bu rapordaki FPR "
      "EMBER zararsızlarında ölçülür, kendi makinedeki zararsızlarda değil.")
    for u in uyarilar:
        a(f"- **UYARI** {u}")
    return "\n".join(s) + "\n"


# --------------------------------------------------------------------------

def yukle(ozellik_seti):
    from ember2018_tam_cikar import cikti_yolu
    egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
    test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
    return egitim, test


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--cikti", default="degerlendirme_raporu.md")
    ap.add_argument("--ozellik-seti", choices=OZELLIK_SETLERI, default="temel")
    ap.add_argument("--egitim-ornek", type=int, default=100_000)
    ap.add_argument("--tohumlar", type=int, default=5)
    arg = ap.parse_args()

    kolonlar = OZELLIK_SETLERI[arg.ozellik_seti]
    egitim, test = yukle(arg.ozellik_seti)
    print(f"[*] egitim {len(egitim):,}, test {len(test):,} | ozellik seti: {arg.ozellik_seti} ({len(kolonlar)})")
    sonuc, kontroller, bilgi = degerlendir(
        egitim, test, kolonlar, egitim_ornek=arg.egitim_ornek,
        tohumlar=[42, 1, 2, 3, 4, 5, 6, 7, 8, 9][:arg.tohumlar])
    with open(arg.cikti, "w", encoding="utf-8") as f:
        f.write(rapor_yaz(sonuc, kontroller, bilgi, kolonlar, arg.ozellik_seti))
    print(f"[+] rapor -> '{arg.cikti}'")
