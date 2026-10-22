# V0 / V2 / V4 karşılaştırması: doğrulamadan seçilen eşikle, tip bazında

> **V4 henüz ana model DEĞİL.** Bu rapor karar girdisidir; ana model (`rf_egit_gercek.py`, 5 özellik) değişmedi.

## Kurulum

- Üretildi: 2026-10-07 21:26 · kod: `eval-harness` @ `958b62d` (+ bu raporun ekindeki betik) · komut (gumruk_memuru içinden): `python v_karsilastir.py <yerel_zararsiz_csv> <rapor.md> <commit>`
- Ortam: Python 3.13.7, scikit-learn 1.9.0, numpy 2.5.1, pandas 3.0.3
- Veri: EMBER 2018 v2 özellik dosyaları (`ember_dataset_2018_2`), `ember2018_tam_cikar.py` ile CSV. train 600,000 satır (sha256 `56d971587f771752`), test 200,000 satır (sha256 `fbf2bb6290239e2c`). Yerel: bu makinedeki zararsız dış doğrulama setinin `dogrulama_yeniden_olc.py` ile yeniden ölçülen hali, 5,637 satır (5700'den 63 elendi; Dosya_Adi içermez; sha256 `7d1e63c60e3b1a03`).
- Bölme: fit 450,817 (2006-12 → 2018-08), eşik doğrulaması 149,183 (2018-09 → 2018-10, kayıt payına göre son ≥%20), test 200,000 (2018-11 → 2018-12). Yeni aile testi: zararlılar yalnızca fit+doğrulamada hiç görülmeyen ailelerden (168 aile), zararsızlar aynı.
- Modeller: RandomForest 100 ağaç, ayarsız. Her tohumda fit'ten 11,400 örnek: V0 ve V2 sınıf dengeli, V4 tip içi dengeli (DLL_mi × Etiket, her hücre ¼). Tohumlar [42, 1, 2, 3, 4].
  - V0: 5 temel özellik · V2: + EMBER 2018 dizge grubu (8) · V4: V2 + DLL_mi, tip içi dengeli
- Gruplar ÖRTÜŞMEZ: EXE = native EXE, DLL = native DLL, .NET = NET_mi=1 (EXE ya da DLL).
- Eşik (ana tablo): her model ve tohum için, doğrulama penceresinde HER GRUBUN kendi zararsızlarının %1'i eşiği aşacak şekilde (tipe göre eşik). Ek tablo: tek genel eşik (tüm doğrulama zararsızlarında %1). Test ve yerel kümeye dokunulmadan seçildi.

## Sızıntı kontrolleri

| Kontrol | Durum | Ayrıntı |
|---|---|---|
| ozellik listesinde etiket/meta yok | gecti | 14 ozellik |
| egitim donemleri < test donemleri | gecti | egitim son 2018-10, test ilk 2018-11 |
| egitim(fit) < esik dogrulamasi | gecti | fit son 2018-08, dogrulama ilk 2018-09 |
| egitim/test dosya kimligi (Dosya_Adi) ortak degil | gecti | 0 ortak dosya |
| zaman+aile test kumesinde egitim ailesi yok | gecti | 168 test ailesi, kesisim 0 |
| birebir ayni ozellik vektoru (sadece rapor) | bilgi | testin %7.5'i egitimde ayni vektorle var (5 ozellikle dogal; etiket celiskisi olcumu bozmaz, ama kolaylastirir) |

## Ana tablo (tipe göre eşik, hedef %1 yanlış alarm)

EMBER hücreleri: 5 tohum ortalaması (en düşük–en yüksek). Yerel hücreler: 5 tohum ortalama yanlış alarm sayısı üzerinden %95 Wilson aralığı. Yerel küme yalnızca zararsız: orada yakalama ÖLÇÜLEMEZ. PR-AUC grubun zararlı oranına bağlıdır: gruplar arasında değil, aynı grupta modeller arasında karşılaştırılır.

| Küme | Grup | n zararsız / zararlı | Ölçüm | V0 | V2 | V4 |
|---|---|---|---|---|---|---|
| EMBER zaman | EXE | 59,842 / 89,991 | Yakalama % @%1 | 35.3 (17.4–44.5) | 43.2 (40.0–44.8) | 35.7 (20.2–41.8) |
| EMBER zaman | EXE | 59,842 / 89,991 | Gerçekleşen yanlış alarm % | 0.9 (0.7–1.1) | 0.9 (0.7–1.0) | 0.9 (0.8–1.0) |
| EMBER zaman | EXE | 59,842 / 89,991 | PR-AUC | 0.923 (0.915–0.926) | 0.937 (0.931–0.943) | 0.934 (0.920–0.941) |
| EMBER zaman | DLL | 17,432 / 7,102 | Yakalama % @%1 | 43.9 (39.1–47.4) | 54.8 (51.5–57.5) | 58.5 (57.6–59.5) |
| EMBER zaman | DLL | 17,432 / 7,102 | Gerçekleşen yanlış alarm % | 1.2 (1.0–1.3) | 0.9 (0.9–1.1) | 1.2 (1.1–1.3) |
| EMBER zaman | DLL | 17,432 / 7,102 | PR-AUC | 0.818 (0.802–0.831) | 0.895 (0.888–0.902) | 0.915 (0.909–0.919) |
| EMBER zaman | .NET | 22,726 / 2,907 | Yakalama % @%1 | 27.5 (19.9–33.4) | 52.7 (45.7–58.5) | 48.9 (45.2–54.2) |
| EMBER zaman | .NET | 22,726 / 2,907 | Gerçekleşen yanlış alarm % | 1.4 (1.2–1.5) | 1.3 (1.1–1.4) | 1.3 (1.0–1.6) |
| EMBER zaman | .NET | 22,726 / 2,907 | PR-AUC | 0.507 (0.432–0.549) | 0.729 (0.692–0.753) | 0.720 (0.695–0.746) |
| EMBER yeni aile | EXE | 59,842 / 309 | Yakalama % @%1 | 5.4 (3.9–6.8) | 7.2 (4.5–10.0) | 7.9 (6.8–9.7) |
| EMBER yeni aile | EXE | 59,842 / 309 | Gerçekleşen yanlış alarm % | 0.9 (0.7–1.1) | 0.9 (0.7–1.0) | 0.9 (0.8–1.0) |
| EMBER yeni aile | EXE | 59,842 / 309 | PR-AUC | 0.017 (0.017–0.019) | 0.021 (0.017–0.024) | 0.022 (0.020–0.024) |
| EMBER yeni aile | DLL | 17,432 / 19 | Yakalama % @%1 | 17.9 (15.8–21.1) | 18.9 (10.5–26.3) | 17.9 (10.5–21.1) |
| EMBER yeni aile | DLL | 17,432 / 19 | Gerçekleşen yanlış alarm % | 1.2 (1.0–1.3) | 0.9 (0.9–1.1) | 1.2 (1.1–1.3) |
| EMBER yeni aile | DLL | 17,432 / 19 | PR-AUC | 0.017 (0.010–0.033) | 0.016 (0.011–0.024) | 0.026 (0.021–0.033) |
| EMBER yeni aile | .NET | 22,726 / 35 | Yakalama % @%1 | 14.9 (8.6–20.0) | 58.3 (54.3–62.9) | 53.1 (45.7–60.0) |
| EMBER yeni aile | .NET | 22,726 / 35 | Gerçekleşen yanlış alarm % | 1.4 (1.2–1.5) | 1.3 (1.1–1.4) | 1.3 (1.0–1.6) |
| EMBER yeni aile | .NET | 22,726 / 35 | PR-AUC | 0.014 (0.007–0.031) | 0.098 (0.063–0.122) | 0.074 (0.044–0.113) |
| Yerel zararsiz | EXE | 353 / 0 | Yanlış alarm % | 0.00 [0.00–1.08] | 0.00 [0.00–1.08] | 0.00 [0.00–1.08] |
| Yerel zararsiz | DLL | 1,813 / 0 | Yanlış alarm % | 0.44 [0.22–0.87] | 0.22 [0.09–0.57] | 0.11 [0.03–0.40] |
| Yerel zararsiz | .NET | 3,471 / 0 | Yanlış alarm % | 0.09 [0.03–0.25] | 0.00 [0.00–0.11] | 0.00 [0.00–0.11] |

## Ek tablo (tek genel eşik)

| Küme | Grup | Ölçüm | V0 | V2 | V4 |
|---|---|---|---|---|---|
| EMBER zaman | EXE | Yakalama % | 42.0 (40.4–46.6) | 46.5 (44.2–48.1) | 37.3 (22.0–43.5) |
| EMBER zaman | EXE | Gerçekleşen yanlış alarm % | 1.3 (1.2–1.5) | 1.3 (1.2–1.5) | 1.1 (1.0–1.2) |
| EMBER zaman | DLL | Yakalama % | 39.7 (34.1–43.6) | 44.4 (40.1–48.3) | 60.4 (59.0–61.8) |
| EMBER zaman | DLL | Gerçekleşen yanlış alarm % | 0.5 (0.5–0.6) | 0.3 (0.2–0.3) | 1.4 (1.2–1.6) |
| EMBER zaman | .NET | Yakalama % | 21.6 (16.1–26.2) | 28.8 (25.7–32.9) | 27.2 (25.6–31.2) |
| EMBER zaman | .NET | Gerçekleşen yanlış alarm % | 0.4 (0.3–0.5) | 0.3 (0.2–0.4) | 0.2 (0.1–0.3) |
| EMBER yeni aile | EXE | Yakalama % | 7.4 (5.5–8.7) | 10.5 (7.8–12.0) | 9.6 (7.1–12.6) |
| EMBER yeni aile | EXE | Gerçekleşen yanlış alarm % | 1.3 (1.2–1.5) | 1.3 (1.2–1.5) | 1.1 (1.0–1.2) |
| EMBER yeni aile | DLL | Yakalama % | 8.4 (5.3–10.5) | 8.4 (0.0–15.8) | 18.9 (10.5–21.1) |
| EMBER yeni aile | DLL | Gerçekleşen yanlış alarm % | 0.5 (0.5–0.6) | 0.3 (0.2–0.3) | 1.4 (1.2–1.6) |
| EMBER yeni aile | .NET | Yakalama % | 7.4 (2.9–11.4) | 20.6 (11.4–28.6) | 12.0 (0.0–22.9) |
| EMBER yeni aile | .NET | Gerçekleşen yanlış alarm % | 0.4 (0.3–0.5) | 0.3 (0.2–0.4) | 0.2 (0.1–0.3) |
| Yerel zararsiz | EXE | Yanlış alarm % | 0.00 [0.00–1.08] | 0.00 [0.00–1.08] | 0.00 [0.00–1.08] |
| Yerel zararsiz | DLL | Yanlış alarm % | 0.17 [0.06–0.49] | 0.06 [0.01–0.31] | 0.17 [0.06–0.49] |
| Yerel zararsiz | .NET | Yanlış alarm % | 0.00 [0.00–0.11] | 0.00 [0.00–0.11] | 0.00 [0.00–0.11] |

## Hangi model hangi tipte öne geçiyor (elle yazılan yorum)

Kural: EMBER'de 5 tohumun en düşük–en yüksek aralıkları çakışmıyorsa "öne geçer"; çakışıyorsa "ayırt edilemiyor". Yerelde aynı kural Wilson aralıklarıyla.

| Tip | EMBER zaman (Kasım–Aralık) | EMBER yeni aile | Yerel zararsız |
|---|---|---|---|
| EXE | **V2**: PR-AUC'de V0'ı geçiyor (0.937 vs 0.923, aralıklar ayrık). V2–V4 ayırt edilemiyor (0.934). Yakalamada V2'nin ortalaması en yüksek ve en kararlısı (43.2; 40.0–44.8), V0 (17.4–44.5) ve V4 (20.2–41.8) tohuma çok bağlı | Ayırt edilemiyor (5–8 %, n=309) | Ayırt edilemiyor (üçü de 0/353) |
| DLL | **V4**: yakalama 58.5 (57.6–59.5) vs V2 54.8 (51.5–57.5), PR-AUC 0.915 vs 0.895; ikisi de ayrık. V0 en geride (43.9 / 0.818) | Ayırt edilemiyor (n=19 zararlı) | Ayırt edilemiyor (V4 0.11, V2 0.22, V0 0.44; aralıklar çakışıyor) |
| .NET | **V2 ≈ V4**, ikisi de V0'ı açık farkla geçiyor (yakalama 52.7 / 48.9 vs 27.5; PR-AUC 0.73 / 0.72 vs 0.51) | **V2 ≈ V4 > V0** (58.3 / 53.1 vs 14.9; n=35, aralıklar geniş) | Ayırt edilemiyor (hepsi ≤ 0.09) |

Notlar:
- V4'ün DLL kazancı tipe göre eşikte de sürüyor: sadece kalibrasyon kayması değil, DLL'leri gerçekten daha iyi sıralıyor. Bedeli EXE: ortalama yakalama 43.2 → 35.7 ve tohuma bağlılık artıyor.
- Tek genel eşikte (ek tablo) V4, DLL'de %1.4 gerçekleşen yanlış alarma kayıyor (V2 %0.3): tip içi dengeleme önseli değiştiriyor, tek eşik bunu taşımıyor. Tipe göre eşik bu farkı nötrlüyor.
- Yeni ailelere genelleme her modelde zayıf (EXE yakalama %5–8). Bu, model seçiminden bağımsız asıl açık.
- Yerel yanlış alarmlar %1 FPR eşiklerinde çok düşük (≤%0.44). Aynı modeller 0.5 eşiğinde yerelde %1–15 veriyordu: doğrulamadan seçilen eşikler 0.5'ten çok daha yüksek. Yerel küme EMBER zararsızlarından kolay (Microsoft/tanınmış yazılım, %93 DLL), bu yüzden modelleri ayırmıyor.
- Yeni aile PR-AUC değerleri çok küçük çünkü o gruplarda zararlı oranı ~%0.1–0.5; mutlak değil aynı grupta modeller arası okunmalı.
- Sonuç: tek bir model her tipte önde değil. EXE için V2, DLL için V4 önde; .NET'te ikisi eşdeğer. **V4 henüz ana model değil**; karar, tipe göre eşik kullanılıp kullanılmayacağına ve EXE kararsızlığına bağlı.

## Ek: raporu üreten betik (`v_karsilastir.py`, repoda yok, tek dosya kuralı)

Ham sayılar (her model × tohum × küme × grup) betiğin `_ham.csv` çıktısında; repoya eklenmedi.

```python
"""V0 / V2 / V4 karsilastirmasi: dogrulamadan secilen esiklerle, tip bazinda.

Kullanim (gumruk_memuru klasorunden, eval-harness dali):
  python v_karsilastir.py <yerel_zararsiz_csv> <rapor.md> <kod_commit>
yerel_zararsiz_csv: dogrulama_yeniden_olc.py ciktisi (Dosya_Adi icermez).
"""
import hashlib
import math
import os
import platform
import sys
import time

import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score

sys.path.insert(0, os.getcwd())
from degerlendirme import aile_ayrik_test, esik_sec, sizinti_kontrolleri, zaman_bol  # noqa: E402
from dizge_dll_dogrulama import EGITIM_ORNEK, TOHUMLAR, VARYANTLAR  # noqa: E402
from ember2018_tam_cikar import cikti_yolu  # noqa: E402

sys.stdout.reconfigure(line_buffering=True)
SECILEN = {"V0": "V0 5 temel", "V2": "V2 +dizge", "V4": "V4 +dizge +DLL_mi, tip-ici"}
FPR = 0.01
GRUPLAR = ("EXE", "DLL", ".NET")


def grup_maskeleri(df):
    """Ortusmeyen tipler: native EXE, native DLL, .NET (EXE ya da DLL)."""
    net, dll = df.NET_mi.to_numpy() == 1, df.DLL_mi.to_numpy() == 1
    return {"EXE": ~net & ~dll, "DLL": ~net & dll, ".NET": net}


def ozet_hash(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()[:16]


def wilson(k, n, z=1.96):
    if n == 0:
        return "—"
    p = k / n
    d = 1 + z * z / n
    m = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return f"{100 * p:.2f} [{100 * max(0, m - h):.2f}–{100 * (m + h):.2f}]"


def aralik(seri, k=100, d=1):
    if seri.isna().all():
        return "—"
    return f"{k * seri.mean():.{d}f} ({k * seri.min():.{d}f}–{k * seri.max():.{d}f})"


yerel_yol, rapor_yol, kod_commit = sys.argv[1:4]
t0 = time.monotonic()
egitim = pd.read_csv(cikti_yolu("train"), keep_default_na=False)
test = pd.read_csv(cikti_yolu("test"), keep_default_na=False)
yerel = pd.read_csv(yerel_yol)
fit, dog = zaman_bol(egitim, "Ay")
gorulen = set(fit.Aile.astype(str)) | set(dog.Aile.astype(str))
test_aile = aile_ayrik_test(test, gorulen)
tum_kolon = VARYANTLAR[SECILEN["V4"]][1]
kontroller = sizinti_kontrolleri(fit, dog, test, test_aile, tum_kolon, "Ay", "Ay")
print(f"[*] fit {len(fit)}, dogrulama {len(dog)}, test {len(test)}, test_aile {len(test_aile)}, yerel {len(yerel)}")

kumeler = {"EMBER zaman": test, "EMBER yeni aile": test_aile, "Yerel zararsiz": yerel}
kayit = []
for kisa, ad in SECILEN.items():
    ornekle, kolonlar = VARYANTLAR[ad]
    for tohum in TOHUMLAR:
        o = ornekle(fit, tohum)
        model = RandomForestClassifier(n_estimators=100, random_state=tohum).fit(o[kolonlar], o.Etiket)
        p_dog = model.predict_proba(dog[kolonlar])[:, 1]
        y_dog = dog.Etiket.to_numpy()
        gm_dog = grup_maskeleri(dog)
        esik_tip = {g: esik_sec(p_dog[gm_dog[g] & (y_dog == 0)], FPR) for g in GRUPLAR}
        esik_genel = esik_sec(p_dog[y_dog == 0], FPR)
        for kume_adi, df in kumeler.items():
            p = model.predict_proba(df[kolonlar])[:, 1]
            y = df.Etiket.to_numpy()
            for g, m in grup_maskeleri(df).items():
                z, k = m & (y == 0), m & (y == 1)
                satir = {"model": kisa, "kume": kume_adi, "grup": g, "tohum": tohum,
                         "n0": int(z.sum()), "n1": int(k.sum()),
                         "ya0": int((p[z] > esik_tip[g]).sum()), "ya0_genel": int((p[z] > esik_genel).sum()),
                         "FPR": (p[z] > esik_tip[g]).mean() if z.any() else np.nan,
                         "TPR": (p[k] > esik_tip[g]).mean() if k.any() else np.nan,
                         "FPR_genel": (p[z] > esik_genel).mean() if z.any() else np.nan,
                         "TPR_genel": (p[k] > esik_genel).mean() if k.any() else np.nan,
                         "PRAUC": average_precision_score(y[m], p[m]) if z.any() and k.any() else np.nan}
                kayit.append(satir)
    print(f"  {kisa}: {len(TOHUMLAR)} tohum, {time.monotonic() - t0:.0f} sn")

s = pd.DataFrame(kayit)
modeller = list(SECILEN)


def hucre(d, metrik):
    if metrik == "YA_yerel":
        n = int(d.n0.iloc[0])
        return wilson(round(d.ya0.mean()), n)
    if metrik == "YA_yerel_genel":
        n = int(d.n0.iloc[0])
        return wilson(round(d.ya0_genel.mean()), n)
    if metrik == "PRAUC":
        return aralik(d.PRAUC, k=1, d=3)
    return aralik(d[metrik])


R = []
a = R.append
a("# V0 / V2 / V4 karşılaştırması: doğrulamadan seçilen eşikle, tip bazında\n")
a("> **V4 henüz ana model DEĞİL.** Bu rapor karar girdisidir; ana model (`rf_egit_gercek.py`, "
  "5 özellik) değişmedi.\n")
a("## Kurulum\n")
a(f"- Üretildi: {time.strftime('%Y-%m-%d %H:%M')} · kod: `eval-harness` @ `{kod_commit}` "
  f"(+ bu raporun ekindeki betik) · komut (gumruk_memuru içinden): "
  f"`python v_karsilastir.py <yerel_zararsiz_csv> <rapor.md> <commit>`")
a(f"- Ortam: Python {platform.python_version()}, scikit-learn {sklearn.__version__}, "
  f"numpy {np.__version__}, pandas {pd.__version__}")
a(f"- Veri: EMBER 2018 v2 özellik dosyaları (`ember_dataset_2018_2`), `ember2018_tam_cikar.py` ile CSV. "
  f"train {len(egitim):,} satır (sha256 `{ozet_hash(cikti_yolu('train'))}`), test {len(test):,} satır "
  f"(sha256 `{ozet_hash(cikti_yolu('test'))}`). Yerel: bu makinedeki zararsız dış doğrulama setinin "
  f"`dogrulama_yeniden_olc.py` ile yeniden ölçülen hali, {len(yerel):,} satır (5700'den 63 elendi; "
  f"Dosya_Adi içermez; sha256 `{ozet_hash(yerel_yol)}`).")
a(f"- Bölme: fit {len(fit):,} ({fit.Ay.min()} → {fit.Ay.max()}), eşik doğrulaması {len(dog):,} "
  f"({dog.Ay.min()} → {dog.Ay.max()}, kayıt payına göre son ≥%20), test {len(test):,} "
  f"({test.Ay.min()} → {test.Ay.max()}). Yeni aile testi: zararlılar yalnızca fit+doğrulamada hiç "
  f"görülmeyen ailelerden ({int(test_aile[test_aile.Etiket == 1].Aile.nunique())} aile), zararsızlar aynı.")
a(f"- Modeller: RandomForest 100 ağaç, ayarsız. Her tohumda fit'ten {EGITIM_ORNEK:,} örnek: V0 ve V2 "
  f"sınıf dengeli, V4 tip içi dengeli (DLL_mi × Etiket, her hücre ¼). Tohumlar {TOHUMLAR}.")
a("  - V0: 5 temel özellik · V2: + EMBER 2018 dizge grubu (8) · V4: V2 + DLL_mi, tip içi dengeli")
a("- Gruplar ÖRTÜŞMEZ: EXE = native EXE, DLL = native DLL, .NET = NET_mi=1 (EXE ya da DLL).")
a(f"- Eşik (ana tablo): her model ve tohum için, doğrulama penceresinde HER GRUBUN kendi zararsızlarının "
  f"%{100 * FPR:g}'i eşiği aşacak şekilde (tipe göre eşik). Ek tablo: tek genel eşik (tüm doğrulama "
  f"zararsızlarında %{100 * FPR:g}). Test ve yerel kümeye dokunulmadan seçildi.\n")

a("## Sızıntı kontrolleri\n")
a("| Kontrol | Durum | Ayrıntı |\n|---|---|---|")
for ad, durum, ayr in kontroller:
    a(f"| {ad} | {durum} | {ayr} |")
a("")

a("## Ana tablo (tipe göre eşik, hedef %1 yanlış alarm)\n")
a("EMBER hücreleri: 5 tohum ortalaması (en düşük–en yüksek). Yerel hücreler: 5 tohum ortalama "
  "yanlış alarm sayısı üzerinden %95 Wilson aralığı. Yerel küme yalnızca zararsız: orada yakalama "
  "ÖLÇÜLEMEZ. PR-AUC grubun zararlı oranına bağlıdır: gruplar arasında değil, aynı grupta modeller "
  "arasında karşılaştırılır.\n")
a("| Küme | Grup | n zararsız / zararlı | Ölçüm | " + " | ".join(modeller) + " |")
a("|---|---|---|---|" + "---|" * len(modeller))
for kume in kumeler:
    for g in GRUPLAR:
        d = s[(s.kume == kume) & (s.grup == g)]
        n = f"{int(d.n0.iloc[0]):,} / {int(d.n1.iloc[0]):,}"
        if kume == "Yerel zararsiz":
            olcumler = [("Yanlış alarm %", "YA_yerel")]
        else:
            olcumler = [("Yakalama % @%1", "TPR"), ("Gerçekleşen yanlış alarm %", "FPR"), ("PR-AUC", "PRAUC")]
        for etiket, metrik in olcumler:
            a(f"| {kume} | {g} | {n} | {etiket} | "
              + " | ".join(hucre(d[d.model == m], metrik) for m in modeller) + " |")
a("")

a("## Ek tablo (tek genel eşik)\n")
a("| Küme | Grup | Ölçüm | " + " | ".join(modeller) + " |\n|---|---|---|" + "---|" * len(modeller))
for kume in kumeler:
    for g in GRUPLAR:
        d = s[(s.kume == kume) & (s.grup == g)]
        if kume == "Yerel zararsiz":
            olcumler = [("Yanlış alarm %", "YA_yerel_genel")]
        else:
            olcumler = [("Yakalama %", "TPR_genel"), ("Gerçekleşen yanlış alarm %", "FPR_genel")]
        for etiket, metrik in olcumler:
            a(f"| {kume} | {g} | {etiket} | " + " | ".join(hucre(d[d.model == m], metrik) for m in modeller) + " |")
a("")

metin = "\n".join(R) + "\n"
with open(rapor_yol, "w", encoding="utf-8") as f:
    f.write(metin)
s.to_csv(os.path.splitext(rapor_yol)[0] + "_ham.csv", index=False)
print(metin)
print(f"[+] {time.monotonic() - t0:.0f} sn -> {rapor_yol}")
```
