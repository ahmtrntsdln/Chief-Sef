"""
Sef Projesi - Faz 1: Gercek Veriyle Random Forest Egitimi ve Dogrulama
============================================================

Egitim: iki sinif da AYNI kaynaktan (EMBER) gelir:
  - sef_dataset_zararli_gercek.csv  (EMBER label==1, ember_zararli_cikar.py)
  - sef_dataset_ember_zararsiz.csv  (EMBER label==0, ember_zararsiz_cikar.py)

Neden: zararsiz tarafi kendi taramamizdan (System32/Program Files) gelince
model "zararli mi?" yerine "EMBER'den mi, bu bilgisayardan mi?" sorusunu
ogreniyordu (kaynak sizintisi). Kendi taramamiz artik SADECE dis dogrulama
icin kullanilir: hepsi zararsiz oldugu icin, modelin onlardan kacini
"zararli" sandigi = bu makinedeki gercek yanlis-alarm orani.

Karsilastirma icin eski tasarim (EMBER zararli vs kendi taramamiz) da
egitilip ozellik onemleri yan yana basilir.
"""

import os
import sys

import joblib
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

EMBER_ZARARLI_CSV = "sef_dataset_zararli_gercek.csv"
EMBER_ZARARSIZ_CSV = "sef_dataset_ember_zararsiz.csv"
TARAMA_ZARARSIZ_CSV = "sef_dataset_zararsiz_gercek.csv"
OZELLIKLER = ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
              "Toplam_API", "Supheli_API"]
# Uretilmis veri: commit'lenmez (.gitignore), bu script ~10 sn'de birebir
# ayni modeli yeniden uretir (random_state=42). Bkz. CLAUDE.md, Veri dosyalari.
MODEL_YOLU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")

SINSI_ORNEKLER = {
    "Sinsi 1 (faz1_dogrulama.py): entropi 5.6, sifir %4, 1 supheli API": {
        "Boyut_Bayt": 250_000, "Sifir_Orani": 4.0, "Ortalama_Entropi": 5.6,
        "Toplam_API": 80, "Supheli_API": 1,
    },
    "Sinsi 2: gercekci zararsiz profil, dusuk sifir orani (%17), orta entropi": {
        "Boyut_Bayt": 180_000, "Sifir_Orani": 17.0, "Ortalama_Entropi": 3.8,
        "Toplam_API": 60, "Supheli_API": 0,
    },
}


def egit(df: pd.DataFrame):
    X, y = df[OZELLIKLER], df["Etiket"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    return model, X_test, y_test


def onemler(model) -> pd.Series:
    return pd.Series(model.feature_importances_, index=OZELLIKLER) \
        .sort_values(ascending=False)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)

    ember_zararli = pd.read_csv(EMBER_ZARARLI_CSV)
    ember_zararsiz = pd.read_csv(EMBER_ZARARSIZ_CSV)
    tarama_zararsiz = pd.read_csv(TARAMA_ZARARSIZ_CSV)

    # --- Ana model: EMBER vs EMBER ---
    ana_df = pd.concat([ember_zararli, ember_zararsiz], ignore_index=True)
    model, X_test, y_test = egit(ana_df)
    print(f"=== ANA MODEL: EMBER zararli ({len(ember_zararli)}) vs "
          f"EMBER zararsiz ({len(ember_zararsiz)}) ===")
    y_pred = model.predict(X_test)
    print(classification_report(y_test, y_pred,
                                target_names=["Zararsiz", "Zararli"], digits=3))
    cm = confusion_matrix(y_test, y_pred)
    print(f"Karisiklik matrisi: gercek zararsiz -> {cm[0][0]} dogru, {cm[0][1]} yanlis alarm | "
          f"gercek zararli -> {cm[1][1]} yakalandi, {cm[1][0]} kacti")

    # --- Dis dogrulama: bu makinedeki gercek zararsiz PE'ler ---
    dis_tahmin = model.predict(tarama_zararsiz[OZELLIKLER])
    yanlis_alarm = dis_tahmin.mean()
    print(f"\n=== DIS DOGRULAMA: kendi taramamiz ({len(tarama_zararsiz)} zararsiz PE, "
          f"egitimde HIC gorulmedi) ===")
    print(f"'Zararli' diye isaretlenen: {int(dis_tahmin.sum())} / {len(tarama_zararsiz)} "
          f"-> yanlis alarm orani %{yanlis_alarm * 100:.1f}")
    print(f"(EMBER icindeki yanlis alarm orani: %{cm[0][1] / cm[0].sum() * 100:.1f} - "
          f"fark buyukse model EMBER disina iyi genellenmiyor demektir)")

    # --- Ozellik onemleri: yeni tasarim vs eski (kaynak-karisik) tasarim ---
    eski_df = pd.concat([ember_zararli, tarama_zararsiz], ignore_index=True)
    eski_model, eski_X_test, eski_y_test = egit(eski_df)
    eski_dogruluk = (eski_model.predict(eski_X_test) == eski_y_test).mean()
    yeni_dogruluk = (y_pred == y_test).mean()

    karsilastirma = pd.DataFrame({
        "ANA (EMBER vs EMBER)": onemler(model),
        "ESKI (EMBER zararli vs tarama)": onemler(eski_model),
    }).loc[OZELLIKLER].sort_values("ANA (EMBER vs EMBER)", ascending=False)
    print("\n=== OZELLIK ONEMLERI ===")
    print(karsilastirma.round(3).to_string())
    for ad, seri in [("ANA", onemler(model)), ("ESKI", onemler(eski_model))]:
        ikili = seri["Ortalama_Entropi"] + seri["Sifir_Orani"]
        print(f"{ad}: Ortalama_Entropi + Sifir_Orani payi = %{ikili * 100:.1f}")
    print(f"Test dogrulugu: ANA %{yeni_dogruluk * 100:.1f} | ESKI %{eski_dogruluk * 100:.1f}")

    # --- Sinsi ornekler ---
    print("\n=== SINSI ORNEKLER (ana model / eski model) ===")
    for ad, ozellik in SINSI_ORNEKLER.items():
        ornek = pd.DataFrame([ozellik])[OZELLIKLER]
        p_ana = model.predict_proba(ornek)[0][1]
        p_eski = eski_model.predict_proba(ornek)[0][1]
        print(f"{ad}\n    zararli olasiligi: ANA %{p_ana * 100:.0f} | ESKI %{p_eski * 100:.0f}")

    # --- Ana modeli kaydet (tahmin_et.py icin) ---
    # Ozellik listesi ve sklearn surumu de saklanir: tahmin tarafi sutun
    # sirasini modelden okur, surum farki olursa uyarabilir.
    joblib.dump({"model": model, "ozellikler": OZELLIKLER,
                 "sklearn_surumu": sklearn.__version__}, MODEL_YOLU)
    print(f"\n[+] Ana model kaydedildi -> '{MODEL_YOLU}'")
