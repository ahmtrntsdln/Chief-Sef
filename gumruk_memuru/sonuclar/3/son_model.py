"""
Adim 3 - Son model: RF E3, tohum 42, havuz (hafta 0-47), esik dogrulama diliminden (48-51).

Boyut ELLE YAZILMAZ: on_kayit_esik_boyut.md'deki kural esik_boyut.csv'den yeniden hesaplanir.
Determinizm kontrolu: ayni hucre esik_boyut.csv'de var; olculer birebir tutmazsa DURUR.
Cikti: sef_ayarlar.NATIVE_MODEL_YOLU (OneDrive disi, repoda yok) ve NATIVE_META_YOLU (repoda).
Kullanim: python son_model.py
"""

import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

import joblib
import numpy as np
import pandas as pd

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
import ortak_deney as o  # noqa: E402
from esik_boyut import BUYUK, DOGRULAMA_HAFTA, KURAL_TOHUM, ONEK  # noqa: E402
from ozellik_cikar import MODEL_KOLONLARI  # noqa: E402
from sef_ayarlar import NATIVE_META_YOLU, NATIVE_MODEL_YOLU  # noqa: E402

TOHUM = 42


def sha256(yol, kisa=False):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()[:16] if kisa else h.hexdigest()


def boyut_kurali(df):
    k3 = df[(df.algoritma == "RF") & (df.aday == "E3") & (df.boyut == 300_000) & df.tohum.isin(KURAL_TOHUM)]
    kb = df[(df.algoritma == "RF") & (df.aday == "E3") & (df.boyut == BUYUK) & df.tohum.isin(KURAL_TOHUM)]
    if len(k3) != len(KURAL_TOHUM) or len(kb) != len(KURAL_TOHUM):
        sys.exit("Hata: kural hucreleri eksik; once esik_boyut.py.")
    kazanc = k3["DLL_kacan_%@1"].mean() - kb["DLL_kacan_%@1"].mean()
    s = max(k3["DLL_kacan_%@1"].std(ddof=1), kb["DLL_kacan_%@1"].std(ddof=1))
    return (300_000 if kazanc < s else BUYUK), kazanc, s


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if MODEL_KOLONLARI != o.E3_KOLON:
        sys.exit("Hata: ozellik_cikar.MODEL_KOLONLARI ile deney kolonlari farkli.")
    olcum = pd.read_csv(os.path.join(BURASI, "esik_boyut.csv"))
    boyut, kazanc, s = boyut_kurali(olcum)
    print(f"[*] boyut kurali: kazanc {kazanc:+.3f}, s {s:.3f} -> {boyut}")

    egitim, test, yerel = o.veri()
    havuz, dog = egitim[egitim.Hafta < DOGRULAMA_HAFTA], egitim[egitim.Hafta >= DOGRULAMA_HAFTA]
    satir, model = o.hucre_kos("RF", "E3", boyut, TOHUM, havuz, test, yerel, 8, dogrulama=dog,
                               onek="SON_", model_dondur=True)
    beklenen = olcum[olcum.hucre == f"{ONEK}RF_E3_{boyut}_{TOHUM}"].iloc[0]
    for k in ("DLL_kacan_%@1", "EXE_kacan_%@1", "EXE_esik@1", "DLL_esik@1", "genel_AUC",
              "EXE_yerel_YA_k", "DLL_yerel_YA_k"):
        if not np.isclose(float(satir[k]), float(beklenen[k]), rtol=0, atol=1e-9):
            sys.exit(f"Hata: determinizm tutmadi: {k} {satir[k]} != {beklenen[k]}")
    print("[*] determinizm: esik_boyut.csv'deki ayni hucreyle birebir")

    os.makedirs(os.path.dirname(NATIVE_MODEL_YOLU), exist_ok=True)
    model.set_params(n_jobs=1)                  # tek dosya tahmininde gereksiz is parcacigi yok
    joblib.dump(model, NATIVE_MODEL_YOLU)
    ornek = o.tip_ici_dengeli(havuz, boyut, TOHUM)
    try:
        kod = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=BURASI).stdout.strip()
    except OSError:
        kod = subprocess.run([r"C:\Program Files\Git\cmd\git.exe", "rev-parse", "HEAD"],
                             capture_output=True, text=True, cwd=BURASI).stdout.strip()
    import lightgbm, pefile, pyarrow, sklearn  # noqa: E401  (surum kaydi)
    meta = {
        "model": "RF E3 (EMBER2024 Win32+Win64, 86 ozellik, tip-ici dengeli)",
        "ozellikler": MODEL_KOLONLARI,
        "algoritma": {"sinif": "sklearn.ensemble.RandomForestClassifier",
                      "parametreler": {k: v for k, v in model.get_params().items() if k != "n_jobs"}},
        "tohum": TOHUM, "egitim_boyutu": boyut,
        "boyut_karari": {"kural": "on_kayit_esik_boyut.md", "kazanc_puan": round(kazanc, 4),
                         "s_puan": round(s, 4), "secilen": boyut},
        "egitim_verisi": {
            "kaynak": "EMBER2024 Win32_train + Win64_train (HF joyce8/EMBER2024)",
            "havuz_haftalar": f"0-{DOGRULAMA_HAFTA - 1}", "havuz_satir": len(havuz),
            "havuz_hucreler_DLLmi_Etiket": {f"{int(d)}_{e}": int(n) for (d, e), n in havuz.groupby(["DLL_mi", "Etiket"]).size().items()},
            "orneklem_hucreler_DLLmi_Etiket": {f"{int(d)}_{e}": int(n) for (d, e), n in ornek.groupby(["DLL_mi", "Etiket"]).size().items()},
            "parquet_sha256_16": {a: sha256(os.path.join(o.EMBER2024_PARQUET_KLASORU, f"{a}.parquet"), True)
                                  for a in ("Win32_train", "Win64_train", "Win32_test", "Win64_test")},
        },
        "esikler": {"EXE": satir["EXE_esik@1"], "DLL": satir["DLL_esik@1"]},
        "esik_tanimi": f"hafta {DOGRULAMA_HAFTA}-51 dogrulama diliminde her turun zararsizlarinin %1'i asar",
        "test_bir_kez": {"haftalar": "52-63", "satir": len(test),
                         **{k: satir[k] for k in ("genel_AUC", "EXE_kacan_%@1", "DLL_kacan_%@1",
                                                  "EXE_test_YA_%@1", "DLL_test_YA_%@1", "EXE_AUC", "DLL_AUC")}},
        "yerel_zararsiz": {"satir": len(yerel), **{k: satir[k] for k in (
            "EXE_yerel_YA_%@1", "EXE_yerel_YA_alt", "EXE_yerel_YA_ust", "DLL_yerel_YA_%@1",
            "DLL_yerel_YA_alt", "DLL_yerel_YA_ust")}},
        "surumler": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__, "pefile": pefile.__version__,
                     "pyarrow": pyarrow.__version__, "lightgbm": lightgbm.__version__},
        "tarih": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "kod_commit": kod,
        "model_dosyasi": os.path.basename(NATIVE_MODEL_YOLU),
        "model_bayt": os.path.getsize(NATIVE_MODEL_YOLU),
        "model_sha256": sha256(NATIVE_MODEL_YOLU),
    }
    with open(NATIVE_META_YOLU, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=float)
    print(json.dumps({k: meta[k] for k in ("egitim_boyutu", "esikler", "test_bir_kez", "yerel_zararsiz",
                                           "model_bayt")}, ensure_ascii=False, indent=1, default=float))
    print(f"[+] model -> {NATIVE_MODEL_YOLU}\n[+] meta  -> {NATIVE_META_YOLU}")
