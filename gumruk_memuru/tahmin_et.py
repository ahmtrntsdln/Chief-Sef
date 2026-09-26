"""
Sef Projesi - Faz 1: Tek Dosya Tahmini
============================================================

rf_egit_gercek.py'nin kaydettigi ana modeli (model.pkl) yukler ve tek bir
dosyayi siniflandirir.

Ozellikler toplu_tarama.dosyayi_analiz_et ile cikarilir: dis dogrulamada
(bu makinede %3.5 yanlis alarm) olculen AYNI kod. Ayri bir cikarim yazmak,
raporlanan sayilarin gecmedigi yeni bir olcum demek olurdu (Kritik Kural 1).

Kullanim: python tahmin_et.py <dosya_yolu>
"""

import os
import sys

import joblib
import pandas as pd
import sklearn

from sef_ayarlar import MODEL_YOLU
from toplu_tarama import dosyayi_analiz_et


def model_yukle():
    if not os.path.exists(MODEL_YOLU):
        sys.exit(f"Hata: model bulunamadi ({MODEL_YOLU}).\n"
                 "Once 'python rf_egit_gercek.py' calistir; modeli egitip bu dosyaya kaydeder.")
    paket = joblib.load(MODEL_YOLU)
    if paket["sklearn_surumu"] != sklearn.__version__:
        print(f"[!] Uyari: model scikit-learn {paket['sklearn_surumu']} ile kaydedilmis, "
              f"kurulu surum {sklearn.__version__}. Sonuclar farkli olabilir; "
              "rf_egit_gercek.py'yi yeniden calistir.", file=sys.stderr)
    return paket


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Kullanim: python tahmin_et.py <dosya_yolu>")
    dosya_yolu = sys.argv[1]
    if not os.path.isfile(dosya_yolu):
        sys.exit(f"Hata: dosya bulunamadi -> {dosya_yolu}")

    paket = model_yukle()
    ozellik = dosyayi_analiz_et(dosya_yolu)
    if ozellik is None:
        sys.exit("Hata: dosya analiz edilemedi (bos, 100 MiB ustu ya da okunamiyor).")
    if not ozellik["PE_mi"]:
        # Model sadece PE ile egitildi (Kritik Kural 3); baska dosyada skor anlamsiz.
        sys.exit("Bu dosya gecerli bir Windows PE degil; model sadece PE dosyalari icin egitildi.")

    X = pd.DataFrame([ozellik])[paket["ozellikler"]]
    olasilik = paket["model"].predict_proba(X)[0, 1]

    print(f"Dosya: {os.path.basename(dosya_yolu)}")
    for ad in paket["ozellikler"]:
        print(f"  {ad:<17}: {ozellik[ad]}")
    print(f"Zararli olasiligi: %{olasilik * 100:.1f} -> "
          f"{'ZARARLI' if olasilik > 0.5 else 'zararsiz'} (esik 0.5)")
    print("  Not: skor EMBER'in %50 zararli dunyasina gore; gercek ortamda zararli "
          "cok daha nadir oldugu icin gercek olasilik daha dusuktur (CLAUDE.md, Model Secimi).")
    if ozellik["NET_mi"]:
        print("  [!] .NET dosyasi: bu model .NET zararlilarinin cogunu kaciriyor "
              "(CLAUDE.md, BILINEN SINIRLAMA); dusuk skor guvence degil.")
