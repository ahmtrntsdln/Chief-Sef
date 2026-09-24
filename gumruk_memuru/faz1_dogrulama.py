"""
Sef Projesi - Faz 1 Dogrulama
Sentetik Zararli Veri Sizintisi Testi

Bu script, Faz 1'deki Random Forest modelinin %100 basarisinin
gercek bir ogrenme mi yoksa veri sizintisi mi oldugunu test eder.

Yontem:
1. Senin 5-senaryolu sentetik zararli veri ureticini birebir kullanir.
2. Gercekci (varsayimsal) bir "zararsiz" dagilim olusturur.
3. Modeli egitip test eder - sonuc gercek denemenle (%99.9) neredeyse birebir eslesir.
4. En onemlisi: 5 senaryonun HICBIRINE uymayan, gercekci "sinsi" bir
   zararli ornegiyle modeli test eder. Bu, modelin gercekten ne
   ogrendigini ortaya cikarir.
"""

import random
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report


def sentetik_zararli_uret(n=2000, tohum=42):
    """Senin orijinal 5-senaryolu ureticinin birebir kopyasi."""
    random.seed(tohum)
    satirlar = []
    for _ in range(n):
        senaryo = random.choice(["1", "2", "3", "4", "5"])
        if senaryo == "1":  # Saf yuksek entropi (packer/sifreleme)
            boyut = random.randint(50_000, 2_000_000)
            sifir = random.uniform(0.1, 3.0)
            entropi = random.uniform(7.6, 7.99)
            toplam_api = random.randint(5, 15)
            supheli_api = random.randint(0, 1)
        elif senaryo == "2":  # Uzanti sahteciligi + injection API
            boyut = random.randint(100_000, 500_000)
            sifir = random.uniform(5.0, 15.0)
            entropi = random.uniform(6.0, 6.8)
            toplam_api = random.randint(50, 150)
            supheli_api = random.randint(3, 8)
        elif senaryo == "3":  # PE olmayan payload
            boyut = random.randint(10_000, 100_000)
            sifir = random.uniform(0.0, 1.0)
            entropi = random.uniform(7.8, 7.99)
            toplam_api = 0
            supheli_api = 0
        elif senaryo == "4":  # Sahte resim + gizli API
            boyut = random.randint(300_000, 800_000)
            sifir = random.uniform(0.5, 2.0)
            entropi = random.uniform(7.5, 7.9)
            toplam_api = random.randint(10, 40)
            supheli_api = random.randint(2, 5)
        else:  # Sifir dolgusuyla boyut sisirme
            boyut = random.randint(50_000_000, 150_000_000)
            sifir = random.uniform(40.0, 80.0)
            entropi = random.uniform(2.0, 4.0)
            toplam_api = random.randint(20, 60)
            supheli_api = random.randint(2, 6)
        satirlar.append([boyut, sifir, entropi, toplam_api, supheli_api, 1])
    return satirlar


def gercekci_zararsiz_uret(n=5700, tohum=42):
    """
    Gercek 5700 dosyanin tam sayisal degerlerini bilmiyoruz (o veri
    senin bilgisayarinda), bu yuzden makul varsayimlarla temsili bir
    dagilim uretiyoruz. Entropi kismi senin histogramina (ort. ~6.1,
    kritik sinir ~7.5) benzeyecek sekilde ayarlandi.
    """
    rng = np.random.default_rng(tohum)
    boyut = rng.lognormal(10.5, 2.0, n).astype(int)
    sifir = np.clip(rng.exponential(3.0, n), 0, 100)
    entropi = np.clip(rng.normal(6.1, 0.85, n), 0, 8)
    pe_mi = rng.random(n) < 0.15  # dosyalarin ~%15'i calistirilabilir varsayimi
    toplam_api = np.where(pe_mi, rng.integers(20, 300, n), 0)
    supheli_api = np.where(pe_mi, rng.poisson(1.0, n), 0)
    return list(zip(boyut, sifir, entropi, toplam_api, supheli_api, [0] * n))


if __name__ == "__main__":
    kolonlar = ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
                "Toplam_API", "Supheli_API", "Etiket"]

    df = pd.DataFrame(
        gercekci_zararsiz_uret() + sentetik_zararli_uret(),
        columns=kolonlar,
    )

    X, y = df.drop(columns="Etiket"), df["Etiket"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    print("=== Test Sonucu (senin sonucunla karsilastir) ===")
    print(classification_report(y_test, model.predict(X_test),
                                 target_names=["Zararsiz", "Zararli"], digits=3))

    print("=== Ozellik Onemleri ===")
    print(pd.Series(model.feature_importances_, index=X.columns)
          .sort_values(ascending=False).to_string())

    print("\n=== Asil Test: 5 Senaryonun HICBIRINE Uymayan 'Sinsi' Ornek ===")
    print("(Dusuk-orta entropi, normal API sayisi, sadece 1 supheli cagri)")
    sinsi_ornek = pd.DataFrame([{
        "Boyut_Bayt": 250_000,
        "Sifir_Orani": 4.0,
        "Ortalama_Entropi": 5.6,
        "Toplam_API": 80,
        "Supheli_API": 1,
    }])
    tahmin = model.predict(sinsi_ornek)[0]
    olasilik = model.predict_proba(sinsi_ornek)[0]
    print(f"Tahmin: {'ZARARLI' if tahmin == 1 else 'ZARARSIZ'}  "
          f"(guven: zararsiz={olasilik[0]:.2%}, zararli={olasilik[1]:.2%})")
