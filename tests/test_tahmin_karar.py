"""
tahmin_et.karar sinir testleri: .NET dosyasinda esigin alti BELIRSIZ (asla "zararsiz"), .NET EXE'de
esik ustu OLASI ZARARLI, .NET DLL'de ZARARLI; .NET disi davranis degismedi; gecersiz skor (NaN,
sonsuz, [0, 1] disi) her dosyada BELIRSIZ (fail-closed, Kritik Kural 7).

Model dosyasi GEREKMEZ: sahte model sabit skor dondurur. Esikler meta verideki degerlerle ayni.
Calistirma (repo kokunden): python -m pytest tests
"""

import glob
import math
import os
import sys

import numpy as np
import pefile
import pytest

import tahmin_et as te
import toplu_tarama as tt
from ozellik_cikar import MODEL_KOLONLARI, dosya_turu

ESIK = {"EXE": 0.70, "DLL": 0.61}          # model_native_meta.json "esikler"
UST = {t: math.nextafter(e, 1.0) for t, e in ESIK.items()}   # esigin hemen ustu

NET_ORNEKLERI = sorted(glob.glob(os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                                              "Microsoft.NET", "Framework64", "v4.*", "System.dll")))
net_yok = pytest.mark.skipif(not NET_ORNEKLERI, reason=".NET Framework yok")


class SabitModel:
    def __init__(self, p):
        self.p = p

    def predict_proba(self, X):
        return np.array([[1.0 - self.p, self.p]] * len(X))


def paket(p):
    return {"model": SabitModel(p), "meta": {"ozellikler": MODEL_KOLONLARI, "esikler": dict(ESIK)}}


def test_net_exe_tam_esikte_belirsiz():
    # karar "skor > esik": tam esik esigi GECMEZ -> .NET'te BELIRSIZ (zararsiz degil)
    assert te.karar(ESIK["EXE"], ESIK["EXE"], True, "EXE") == te.BELIRSIZ


def test_net_exe_esik_ustu_olasi_zararli():
    assert te.karar(UST["EXE"], ESIK["EXE"], True, "EXE") == te.OLASI_ZARARLI
    assert te.karar(1.0, ESIK["EXE"], True, "EXE") == te.OLASI_ZARARLI


def test_net_hicbir_skorda_zararsiz_degil():
    for p in [0.0, 5e-324, *np.linspace(0, 1, 101), ESIK["EXE"], ESIK["DLL"], 1.0]:
        for tur in ("EXE", "DLL"):
            assert te.karar(float(p), ESIK[tur], True, tur) != te.ZARARSIZ


def test_net_dll_kendi_esigini_kullanir():
    assert te.karar(ESIK["DLL"], ESIK["DLL"], True, "DLL") == te.BELIRSIZ
    assert te.karar(UST["DLL"], ESIK["DLL"], True, "DLL") == te.ZARARLI
    # 0,65 EXE esiginin (0,70) altinda: DLL esigi yerine EXE esigi uygulansaydi BELIRSIZ olurdu
    assert te.karar(0.65, ESIK["DLL"], True, "DLL") == te.ZARARLI


def test_net_disi_davranis_degismedi():
    for tur in ("EXE", "DLL"):
        assert te.karar(ESIK[tur], ESIK[tur], False, tur) == te.ZARARSIZ
        assert te.karar(UST[tur], ESIK[tur], False, tur) == te.ZARARLI
        assert te.karar(0.0, ESIK[tur], False, tur) == te.ZARARSIZ


@pytest.mark.parametrize("p", [float("nan"), float("inf"), float("-inf"), -0.01, math.nextafter(1.0, 2.0), 1.01])
def test_gecersiz_skor_her_dosyada_belirsiz(p):
    for net in (True, False):
        for tur in ("EXE", "DLL"):
            assert te.karar(p, ESIK[tur], net, tur) == te.BELIRSIZ


def test_karma_mod_net_kurali():
    satir = {"NET_mi": 1, "Karma_Mod": 1, "DLL_mi": 0}
    assert dosya_turu(satir) == ".NET"
    assert te.karar(0.1, ESIK["EXE"], dosya_turu(satir) == ".NET", "EXE") == te.BELIRSIZ


@pytest.mark.parametrize("net, dll, beklenen", [("1", "0", ".NET"), ("1.0", "1.0", ".NET"),
                                                 ("0", "1.0", "DLL"), ("0.0", "0", "EXE")])
def test_net_mi_csv_bicimleri(net, dll, beklenen):
    assert dosya_turu({"NET_mi": net, "DLL_mi": dll}) == beklenen


@net_yok
def test_az_veri_dizini_net_sayilmaz():
    """NumberOfRvaAndSizes = 14: CLR (15. girdi, indeks 14) listelenmez -> .NET degil, hata yok."""
    with open(NET_ORNEKLERI[0], "rb") as f:
        veri = bytearray(f.read())
    assert tt.net_ozellikleri(pefile.PE(data=bytes(veri)))[0] == 1          # kontrol: asil dosya .NET
    ofset = pefile.PE(data=bytes(veri), fast_load=True).OPTIONAL_HEADER.get_field_absolute_offset("NumberOfRvaAndSizes")
    veri[ofset:ofset + 4] = (14).to_bytes(4, "little")
    pe = pefile.PE(data=bytes(veri))
    assert len(pe.OPTIONAL_HEADER.DATA_DIRECTORY) == 14
    assert tt.net_ozellikleri(pe) == (0, 0)


@net_yok
def test_gercek_dosyada_tahmin_karari():
    s = te.tahmin(NET_ORNEKLERI[0], paket(0.0))                 # gercek .NET DLL
    assert (s["Dosya_Turu"], s["esik_turu"], s["karar"]) == (".NET", "DLL", te.BELIRSIZ)
    assert te.tahmin(NET_ORNEKLERI[0], paket(1.0))["karar"] == te.ZARARLI
    native = te.tahmin(sys.executable, paket(0.0))              # native EXE: davranis ayni
    assert (native["Dosya_Turu"], native["karar"]) == ("EXE", te.ZARARSIZ)
