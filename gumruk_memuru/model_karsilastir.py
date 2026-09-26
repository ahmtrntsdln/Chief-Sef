"""
Sef Projesi - Faz 1: Model Karsilastirmasi ve Kalibrasyon
============================================================

Random Forest ile LightGBM'i (EMBER'in kendi referans modeli de LightGBM),
ham ve kalibre edilmis (CalibratedClassifierCV) halleriyle karsilastirir.

Protokol:
  1) EMBER (5700 zararli + 5700 zararsiz) uzerinde 5 katli CV. Kalibrasyon
     her dis katin SADECE egitim kisminda ogrenilir; test kismi hic
     gorulmez (yoksa kalibrasyonu ezberledigi veride olcmus oluruz).
  2) Bu makinedeki PE havuzundan (64.263) 11 farkli 5700'luk orneklem ve
     havuzun tamami: hepsi zararsiz -> isabet = zararsiz'i dogru bilme orani.
     rf_egit_gercek.py ile ayni 80/20 egitim bolmesi kullanilir, boylece
     ham Random Forest onceki sonuclari birebir tekrar etmeli.
  3) "Supheli" bant (olasilik 0.2-0.8): bant disinda otomatik karar,
     icinde "emin degilim".

Kurulum: pip install -r requirements-experimental.txt (LightGBM icin).

Sonuc (5 ozellik, ayarsiz modeller): RandomForest > LightGBM (CV AUC
0.963 vs 0.952). Bu SIMDILIK gecerli: ozellik sayisi artinca (10-15+)
boosting genelde daha iyi olceklenir, bu script o zaman tekrar calistirilmali.

ONEMLI: EMBER egitim verisi %50 zararli. Kalibre edilmis "%90 zararli",
zararlilarin yarisi oldugu bir dunyada %90 demek. Gercek hayatta zararli
dosya cok daha nadir; ayni skor orada daha dusuk bir gercek olasiliga
karsilik gelir. Esik secilirken bu unutulmamali.
"""

import os
import random
import sys
import time

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split

from rf_egit_gercek import (EMBER_ZARARLI_CSV, EMBER_ZARARSIZ_CSV, OZELLIKLER,
                            SINSI_ORNEKLER, TARAMA_ZARARSIZ_CSV)

TUM_TARAMA_CSV = "sef_tarama_tum_dosyalar.csv"   # yerel, .gitignore'da
TOHUMLAR = [42] + list(range(1, 11))
ORNEK = 5700
KAT_SAYISI = 5
KALIBRASYON = "isotonic"   # ~9000 egitim ornegiyle isotonic icin yeterli veri var
SUPHELI_BANT = (0.2, 0.8)

TABAN_MODELLER = {
    "RandomForest": lambda: RandomForestClassifier(n_estimators=100, random_state=42),
    "LightGBM": lambda: LGBMClassifier(random_state=42, verbose=-1),
}
VARYANTLAR = [(ad, kalibre) for ad in TABAN_MODELLER for kalibre in (False, True)]


def varyant_adi(ad, kalibre):
    return f"{ad} + kalibre" if kalibre else ad


def varyant_olustur(ad, kalibre):
    taban = TABAN_MODELLER[ad]()
    return CalibratedClassifierCV(taban, method=KALIBRASYON, cv=5) if kalibre else taban


def kutular(p, kutu=10):
    return np.digitize(p, np.linspace(0, 1, kutu + 1)[1:-1])


def ece(y, p, kutu=10):
    """Beklenen kalibrasyon hatasi: 'ortalama tahmin' ile 'gercekte zararli
    orani' arasindaki farkin, ornek sayisiyla agirliklandirilmis ortalamasi."""
    idx = kutular(p, kutu)
    return sum((idx == b).sum() * abs(y[idx == b].mean() - p[idx == b].mean())
               for b in range(kutu) if (idx == b).any()) / len(y)


def guvenilirlik_tablosu(y, p_ham, p_kal, kutu=10):
    kenar = np.linspace(0, 1, kutu + 1)
    satirlar = []
    for b in range(kutu):
        satir = {"olasilik araligi": f"{kenar[b]:.1f}-{kenar[b + 1]:.1f}"}
        for etiket, p in (("ham", p_ham), ("kalibre", p_kal)):
            m = kutular(p, kutu) == b
            satir[f"{etiket} n"] = int(m.sum())
            satir[f"{etiket} gercek zararli %"] = round(100 * y[m].mean(), 1) if m.any() else None
        satirlar.append(satir)
    return pd.DataFrame(satirlar).to_string(index=False)


def bant_ozeti(p, y=None):
    alt, ust = SUPHELI_BANT
    zararsiz, supheli, zararli = p <= alt, (p > alt) & (p < ust), p >= ust
    ozet = {"zararsiz bolge %": 100 * zararsiz.mean(), "supheli bolge %": 100 * supheli.mean(),
            "zararli bolge %": 100 * zararli.mean()}
    if y is not None:
        emin = zararsiz | zararli
        ozet["bant disi hata %"] = 100 * ((p[emin] > 0.5) != y[emin]).mean()
    return {k: round(v, 2) for k, v in ozet.items()}


class Ilerleme:
    def __init__(self, toplam):
        self.toplam, self.adim, self.baslangic = toplam, 0, time.monotonic()

    def __call__(self, mesaj):
        self.adim += 1
        gecen = time.monotonic() - self.baslangic
        kalan = gecen / self.adim * (self.toplam - self.adim)
        print(f"  [{self.adim}/{self.toplam}] {mesaj} | gecen {gecen:.0f} sn, kalan ~{kalan:.0f} sn")


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    ember = pd.concat([pd.read_csv(EMBER_ZARARLI_CSV), pd.read_csv(EMBER_ZARARSIZ_CSV)],
                      ignore_index=True)
    X, y = ember[OZELLIKLER], ember["Etiket"].to_numpy()
    adlar = [varyant_adi(*v) for v in VARYANTLAR]
    ilerleme = Ilerleme(KAT_SAYISI * len(VARYANTLAR) + len(VARYANTLAR))

    # --- 1) EMBER 5 katli CV ---
    print(f"=== 1) EMBER {KAT_SAYISI} katli capraz dogrulama ===")
    oof = {a: np.zeros(len(y)) for a in adlar}
    kat_dogruluk = {a: [] for a in adlar}
    skf = StratifiedKFold(n_splits=KAT_SAYISI, shuffle=True, random_state=42)
    for kat, (tr, te) in enumerate(skf.split(X, y), 1):
        for (ad, kalibre), a in zip(VARYANTLAR, adlar):
            model = varyant_olustur(ad, kalibre).fit(X.iloc[tr], y[tr])
            p = model.predict_proba(X.iloc[te])[:, 1]
            oof[a][te] = p
            kat_dogruluk[a].append(((p > 0.5) == y[te]).mean())
            ilerleme(f"kat {kat}: {a}")

    cv_tablo = pd.DataFrame({a: {
        "dogruluk %": f"{100 * np.mean(kat_dogruluk[a]):.2f} ± {100 * np.std(kat_dogruluk[a]):.2f}",
        "AUC": round(roc_auc_score(y, oof[a]), 4),
        "yanlis alarm %": round(100 * (oof[a][y == 0] > 0.5).mean(), 2),
        "kacan zararli %": round(100 * (oof[a][y == 1] <= 0.5).mean(), 2),
        "Brier (dusuk=iyi)": round(brier_score_loss(y, oof[a]), 4),
        "LogLoss (dusuk=iyi)": round(log_loss(y, np.clip(oof[a], 1e-6, 1 - 1e-6)), 4),
        "ECE % (dusuk=iyi)": round(100 * ece(y, oof[a]), 2),
    } for a in adlar})

    # --- 2) Bu makinedeki PE havuzu (rf_egit_gercek.py ile ayni 80/20 bolme) ---
    X_tr, _, y_tr, _ = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
    son_modeller = {}
    for (ad, kalibre), a in zip(VARYANTLAR, adlar):
        son_modeller[a] = varyant_olustur(ad, kalibre).fit(X_tr, y_tr)
        ilerleme(f"son model: {a}")

    if os.path.exists(TUM_TARAMA_CSV):
        tum = pd.read_csv(TUM_TARAMA_CSV)
        havuz = tum[tum.PE_mi == True][OZELLIKLER].reset_index(drop=True)  # noqa: E712
        orneklemler = {}
        for t in TOHUMLAR:
            random.seed(t)
            orneklemler[f"tohum {t}"] = random.sample(range(len(havuz)), ORNEK)
    else:
        print(f"[i] '{TUM_TARAMA_CSV}' yok (repo'da degil); sadece kayitli 5700'luk orneklem kullaniliyor.")
        havuz = pd.read_csv(TARAMA_ZARARSIZ_CSV)[OZELLIKLER]
        orneklemler = {"kayitli (tohum 42)": list(range(len(havuz)))}

    p_havuz = {a: m.predict_proba(havuz)[:, 1] for a, m in son_modeller.items()}
    dis_tablo = pd.DataFrame({a: {ad: 100 * (p_havuz[a][idx] <= 0.5).mean()
                                  for ad, idx in orneklemler.items()} for a in adlar})

    # --- Rapor ---
    print(f"\n=== 1) EMBER {KAT_SAYISI} katli CV sonuclari (11.400 ornek, her biri tam bir kez testte) ===")
    print(cv_tablo.to_string())

    print(f"\n=== 2) Bu makinedeki zararsiz PE'ler: isabet % (= zararsiz'i dogru bilme) ===")
    print(dis_tablo.round(2).to_string())
    ozet = pd.DataFrame({"ortalama": dis_tablo.mean(), "std": dis_tablo.std(),
                         "en dusuk": dis_tablo.min(), "en yuksek": dis_tablo.max(),
                         f"havuzun tamami ({len(havuz)})":
                             {a: 100 * (p_havuz[a] <= 0.5).mean() for a in adlar}})
    print(ozet.T.round(2).to_string())

    print("\n=== 3) Guvenilirlik: 'model %X diyor' -> gercekte % kaci zararli? (EMBER CV) ===")
    for ad in TABAN_MODELLER:
        print(f"\n{ad}:")
        print(guvenilirlik_tablosu(y, oof[ad], oof[varyant_adi(ad, True)]))

    alt, ust = SUPHELI_BANT
    print(f"\n=== 4) Supheli bant ({alt}-{ust}): bant disinda otomatik karar, icinde 'emin degilim' ===")
    bant = pd.DataFrame({f"{a} | EMBER": bant_ozeti(oof[a], y) for a in adlar}
                        | {f"{a} | bu makine": bant_ozeti(p_havuz[a]) for a in adlar})
    print(bant.T.to_string())

    print("\n=== 5) Sinsi ornekler: zararli olasiligi % ===")
    sinsi = pd.DataFrame({ad: {a: round(100 * m.predict_proba(pd.DataFrame([o])[OZELLIKLER])[0][1])
                               for a, m in son_modeller.items()}
                          for ad, o in SINSI_ORNEKLER.items()})
    sinsi.columns = [f"Sinsi {i}" for i in range(1, len(sinsi.columns) + 1)]
    print(sinsi.to_string())
