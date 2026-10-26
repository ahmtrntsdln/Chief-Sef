"""
toplu_tahmin sayaclari: BELIRSIZ hata sayilmaz, ayri sayilir; PE olmayan ve analiz edilemeyen dosya
ayri. Model dosyasi GEREKMEZ (sahte model sabit skor). Calistirma: python -m pytest tests
"""

import shutil
import sys

import pytest

import tahmin_et as te
import toplu_tahmin as tp
from test_tahmin_karar import NET_ORNEKLERI, paket

net_yok = pytest.mark.skipif(not NET_ORNEKLERI, reason=".NET Framework yok")


@pytest.fixture
def klasor(tmp_path):
    shutil.copy(sys.executable, tmp_path / "native.exe")         # native EXE
    shutil.copy(NET_ORNEKLERI[0], tmp_path / "net.dll")           # .NET DLL
    (tmp_path / "metin.txt").write_text("PE degil\n", encoding="utf-8")
    (tmp_path / "bos.bin").write_bytes(b"")                       # analiz edilemez -> hata
    return tmp_path


@net_yok
def test_belirsiz_hata_sayilmaz(klasor):
    sayac = tp.tara(tp.yollari_topla([str(klasor)]), paket(0.0))
    assert sayac == {te.ZARARSIZ: 1, te.BELIRSIZ: 1, tp.PE_DEGIL: 1, tp.HATA: 1}


@net_yok
def test_esik_ustu_ve_gecersiz_skor(klasor):
    assert tp.tara(tp.yollari_topla([str(klasor)]), paket(1.0))[te.ZARARLI] == 2
    sayac = tp.tara(tp.yollari_topla([str(klasor)]), paket(float("nan")))
    assert (sayac[te.BELIRSIZ], sayac[tp.HATA]) == (2, 1)        # gecersiz skor: BELIRSIZ, hata degil


@net_yok
def test_liste_yalniz_temiz_olmayanlari_basar(klasor, monkeypatch, capsys):
    monkeypatch.setattr(te, "model_yukle", lambda: paket(0.0))
    assert tp.main([str(klasor), "--liste"]) == 0
    cikti = capsys.readouterr().out
    assert "net.dll" in cikti and "native.exe" not in cikti
    assert "BELIRSIZ      : 1" in cikti and "hata          : 1" in cikti
