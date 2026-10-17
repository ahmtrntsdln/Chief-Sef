"""
Sef Projesi - Tek Dosya Tahmini (native EMBER2024 modeli: RF E3, 86 ozellik)
============================================================

Model: sef_ayarlar.NATIVE_MODEL_YOLU (OneDrive disinda, repoda yok), meta veri:
NATIVE_META_YOLU (repoda; ozellik sirasi, tur esikleri, model sha256). Ikisini
sonuclar/3/son_model.py uretir.

Ozellikler ozellik_cikar.dosya_ozellikleri ile cikarilir: dis dogrulamada olculen AYNI kod.
Ayri bir cikarim yazmak raporlanan sayilarin gecmedigi yeni bir olcum olurdu (Kritik Kural 1).
Meta'daki sha256 model dosyasiyla tutmazsa calismaz: baska bir model eski esiklerle
eslesmesin.

Esik: dosya turune gore (EXE / DLL), egitimde kullanilmayan dogrulama diliminde
(hafta 48-51) zararsizlarin %1'i asacak sekilde secildi.

Kullanim: python tahmin_et.py <dosya_yolu>
"""

import hashlib
import json
import os
import sys

import joblib
import pandas as pd
import sklearn

from ozellik_cikar import dosya_ozellikleri
from sef_ayarlar import NATIVE_META_YOLU, NATIVE_MODEL_YOLU


def _sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def model_yukle():
    for yol in (NATIVE_META_YOLU, NATIVE_MODEL_YOLU):
        if not os.path.exists(yol):
            sys.exit(f"Hata: bulunamadi ({yol}).\n"
                     "Once 'python sonuclar/3/son_model.py' calistir; modeli ve meta veriyi uretir.")
    with open(NATIVE_META_YOLU, encoding="utf-8") as f:
        meta = json.load(f)
    if _sha256(NATIVE_MODEL_YOLU) != meta["model_sha256"]:
        sys.exit("Hata: model dosyasi meta verideki sha256 ile tutmuyor; esikler bu modele ait degil. "
                 "son_model.py'yi yeniden calistir.")
    if meta["surumler"]["scikit-learn"] != sklearn.__version__:
        print(f"[!] Uyari: model scikit-learn {meta['surumler']['scikit-learn']} ile kaydedilmis, "
              f"kurulu {sklearn.__version__}.", file=sys.stderr)
    return {"model": joblib.load(NATIVE_MODEL_YOLU), "meta": meta}


def tahmin(dosya_yolu, paket):
    """Tek dosya: ozellikler + zararli olasiligi + tur esigi + karar. Analiz edilemezse ValueError."""
    ozellik = dosya_ozellikleri(dosya_yolu)
    if ozellik is None:
        raise ValueError("dosya analiz edilemedi (bos, 100 MiB ustu ya da okunamiyor)")
    if not ozellik["PE_mi"]:
        # Model sadece PE ile egitildi (Kritik Kural 3); baska dosyada skor anlamsiz.
        raise ValueError("gecerli bir Windows PE degil; model sadece PE dosyalari icin egitildi")
    X = pd.DataFrame([ozellik])[paket["meta"]["ozellikler"]]
    olasilik = float(paket["model"].predict_proba(X)[0, 1])
    esik_turu = "DLL" if int(float(ozellik["DLL_mi"])) else "EXE"
    esik = paket["meta"]["esikler"][esik_turu]
    return {**ozellik, "olasilik": olasilik, "esik_turu": esik_turu, "esik": esik, "zararli_mi": olasilik > esik}


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Kullanim: python tahmin_et.py <dosya_yolu>")
    dosya_yolu = sys.argv[1]
    if not os.path.isfile(dosya_yolu):
        sys.exit(f"Hata: dosya bulunamadi -> {dosya_yolu}")
    paket = model_yukle()
    try:
        s = tahmin(dosya_yolu, paket)
    except ValueError as e:
        sys.exit(f"Bu dosya icin tahmin yok: {e}.")

    print(f"Dosya: {os.path.basename(dosya_yolu)} | tur: {s['Dosya_Turu']}")
    for ad in ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi", "Toplam_API", "Supheli_API", "DLL_mi",
               "DZ_sayi", "DZ_entropi"]:
        print(f"  {ad:<17}: {s[ad]}")
    print(f"  (+ {len(paket['meta']['ozellikler']) - 8} dizge ozelligi daha; toplam {len(paket['meta']['ozellikler'])})")
    print(f"Zararli olasiligi: %{100 * s['olasilik']:.1f} -> {'ZARARLI' if s['zararli_mi'] else 'zararsiz'} "
          f"({s['esik_turu']} esigi {s['esik']:.3f}: dogrulamada zararsiz {s['esik_turu']}'lerin %1'i asar)")
    print("  Not: skor EMBER2024'un %50 zararli ornekleminden; gercek ortamda zararli cok daha nadir, "
          "gercek olasilik daha dusuktur.")
    if s["Dosya_Turu"] == ".NET":
        print("  [!] .NET dosyasi: bu skor native modelden. .NET uzman modeli (net_model.py) henuz "
              "tahmin_et'e baglanmadi; native modelin .NET alt grubu kucuk ve oynak.")
