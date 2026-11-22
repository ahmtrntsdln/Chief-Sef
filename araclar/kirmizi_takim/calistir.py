"""sef-tara / sef-toplu baslaticisi: /opt/sef/calistir.py olarak kurulur.

main'in kodu (/opt/sef/kod) DEGISTIRILMEDEN calistirilir. Tek fark model yolu:
sef_ayarlar.NATIVE_MODEL_YOLU Windows yolu (C:\\ember2024\\model\\...); Linux'ta goreli bir
yola donusur. Burada, betik ice aktarilmadan ONCE /opt/sef/model'e yonlendirilir
(tahmin_et `from sef_ayarlar import NATIVE_MODEL_YOLU` ile ice aktarirken bu degeri alir).
Hash denetimi (Kural 10) tahmin_et.model_yukle'de oldugu gibi kalir.

Kullanim (yalniz sarmalayicilardan): python -I -B calistir.py <tahmin_et|toplu_tahmin> [arg...]
Cikis kodu ve stdout/stderr betigin kendisinindir (runpy, ayni surec).
"""
import os
import runpy
import sys

KOK = os.path.dirname(os.path.abspath(__file__))
KOD = os.path.join(KOK, "kod", "gumruk_memuru")
MODEL = os.path.join(KOK, "model", "model_native.joblib")
IZINLI = ("tahmin_et", "toplu_tahmin")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in IZINLI:
        sys.exit(f"calistir.py: betik {IZINLI} disinda olamaz")
    betik = os.path.join(KOD, sys.argv[1] + ".py")
    sys.path.insert(0, KOD)
    import sef_ayarlar
    sef_ayarlar.NATIVE_MODEL_YOLU = MODEL
    sys.argv = [betik] + sys.argv[2:]
    runpy.run_path(betik, run_name="__main__")


if __name__ == "__main__":
    main()
