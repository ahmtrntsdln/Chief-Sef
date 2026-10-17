"""
Sef Projesi - TEK ozellik modulu (native EMBER2024 modeli, 86 ozellik)
============================================================

Dis dogrulama (dogrulama_dizge80.py) ve tek dosya tahmini (tahmin_et.py) ozellikleri
BURADAN alir. Iki ayri birlestirme kopyasi olunca biri degisip digeri eski kalabilir ve
raporlanan yanlis alarm, tahmin aracinin olctugu sey olmaktan cikar (Kritik Kural 1).

Olcum: toplu_tarama.dosyayi_analiz_et (5 temel + DLL_mi + NET_mi/Karma_Mod; thrember ile
50 yerel dosyada 50/50) + dizge_ozellikleri.dosyadan_dizge_ozellikleri (80 sutun; thrember
ile 500/500). Ikisi dosyanin AYNI baytlarindan tek okumayla hesaplanir.
"""

from dizge_ozellikleri import DIZGE_SUTUNLARI
from rf_egit_gercek import OZELLIKLER
from toplu_tarama import dosyayi_analiz_et

# E3 sirasi (sonuclar/ortak_deney.E3_KOLON ile ayni; model meta verisi de bu sirayi tasir)
MODEL_KOLONLARI = OZELLIKLER + DIZGE_SUTUNLARI + ["DLL_mi"]


def dosya_turu(satir: dict) -> str:
    """Yonlendirme icin: .NET (uzman modele gidecek), native DLL, native EXE."""
    if int(float(satir["NET_mi"])):
        return ".NET"
    return "DLL" if int(float(satir["DLL_mi"])) else "EXE"


def dosya_ozellikleri(yol: str):
    """Tek dosyanin tum ozellikleri. None: bos, 100 MiB ustu ya da okunamiyor.
    PE degilse PE_mi=False doner ve 80 dizge sutunu EKLENMEZ (model sadece PE icin)."""
    satir = dosyayi_analiz_et(yol, dizge80=True)
    if satir is not None and satir["PE_mi"]:
        satir["Dosya_Turu"] = dosya_turu(satir)
    return satir
