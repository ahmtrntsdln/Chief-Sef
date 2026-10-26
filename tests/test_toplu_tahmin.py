"""
toplu_tahmin sayaclari ve cikis kodu: BELIRSIZ hata sayilmaz, ayri sayilir; PE olmayan ve analiz
edilemeyen dosya ayri. Cikis kodunu EN KOTU sonuc belirler (ZARARLI 3 > OLASI ZARARLI 4 > BELIRSIZ 2
> hata 1 > temiz 0); "PE degil" kodu yukseltmez; hic PE yoksa / yol yoksa 1 (fail-closed).
Model dosyasi GEREKMEZ (sahte model sabit skor). Calistirma: python -m pytest tests
"""

import shutil
import sys
from collections import Counter

import pytest

import tahmin_et as te
import toplu_tahmin as tp
from test_tahmin_karar import NET_EXE, NET_ORNEKLERI, paket

net_yok = pytest.mark.skipif(not NET_ORNEKLERI, reason=".NET Framework yok")
T, B, Z, O, P, H = te.ZARARSIZ, te.BELIRSIZ, te.ZARARLI, te.OLASI_ZARARLI, tp.PE_DEGIL, tp.HATA


@pytest.fixture
def klasor(tmp_path):
    shutil.copy(sys.executable, tmp_path / "native.exe")         # native EXE
    shutil.copy(NET_ORNEKLERI[0], tmp_path / "net.dll")           # .NET DLL
    (tmp_path / "metin.txt").write_text("PE degil\n", encoding="utf-8")
    (tmp_path / "bos.bin").write_bytes(b"")                       # analiz edilemez -> hata
    return tmp_path


@pytest.mark.parametrize("sayac, kod", [
    ({Z: 1, O: 1, B: 1, H: 1, T: 1}, 3),     # herhangi bir ZARARLI -> 3
    ({O: 1, B: 1, H: 1, T: 1}, 4),           # yoksa OLASI ZARARLI -> 4
    ({B: 1, H: 1, T: 1}, 2),                 # yoksa BELIRSIZ -> 2
    ({H: 1, T: 1}, 1),                       # yoksa hata -> 1
    ({T: 3}, 0),                             # hepsi temiz -> 0
    ({T: 1, P: 5}, 0),                       # "PE degil" kodu yukseltmez
    ({P: 4}, 1),                             # hic PE yok -> 1 (fail-closed)
    ({}, 1),                                 # hic dosya yok -> 1
    ({H: 2, P: 1}, 1),                       # yalniz hata
])
def test_oncelik_tablosu(sayac, kod):
    assert tp.toplu_cikis_kodu(Counter(sayac)) == kod


@net_yok
def test_belirsiz_hata_sayilmaz(klasor):
    sayac = tp.tara(tp.yollari_topla([str(klasor)])[0], paket(0.0))
    assert sayac == {T: 1, B: 1, P: 1, H: 1}


@net_yok
def test_esik_ustu_ve_gecersiz_skor(klasor):
    assert tp.tara(tp.yollari_topla([str(klasor)])[0], paket(1.0))[Z] == 2
    sayac = tp.tara(tp.yollari_topla([str(klasor)])[0], paket(float("nan")))
    assert (sayac[B], sayac[H]) == (2, 1)                        # gecersiz skor: BELIRSIZ, hata degil


@net_yok
@pytest.mark.parametrize("p, kod", [(0.0, 2), (1.0, 3), (float("nan"), 2)])
def test_karma_klasor_cikis_kodu(klasor, monkeypatch, capsys, p, kod):
    monkeypatch.setattr(te, "model_yukle", lambda: paket(p))
    assert tp.main([str(klasor)]) == kod
    capsys.readouterr()


@pytest.mark.skipif(not NET_EXE, reason=".NET Framework yok")
def test_olasi_zararli_cikis_kodu(tmp_path, monkeypatch, capsys):
    shutil.copy(NET_EXE[0], tmp_path / "net.exe")
    shutil.copy(sys.executable, tmp_path / "native.exe")
    monkeypatch.setattr(te, "model_yukle", lambda: paket(0.80))   # EXE esigi 0,70 ustu
    assert tp.main([str(tmp_path)]) == 3                           # native EXE ZARARLI, en kotu
    (tmp_path / "native.exe").unlink()
    assert tp.main([str(tmp_path)]) == 4                           # yalniz .NET EXE: OLASI ZARARLI
    capsys.readouterr()


@net_yok
def test_liste_yalniz_temiz_olmayanlari_basar(klasor, monkeypatch, capsys):
    monkeypatch.setattr(te, "model_yukle", lambda: paket(0.0))
    assert tp.main([str(klasor), "--liste"]) == 2
    cikti = capsys.readouterr().out
    assert "net.dll" in cikti and "native.exe" not in cikti
    assert "BELIRSIZ      : 1" in cikti and "hata          : 1" in cikti


def _model_yuklenmemeli():
    raise AssertionError("model yuklenmemeliydi")


def test_bos_klasor(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(te, "model_yukle", _model_yuklenmemeli)
    assert tp.main([str(tmp_path)]) == 1
    assert "UYARI" in capsys.readouterr().err


def test_olmayan_yol(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(te, "model_yukle", _model_yuklenmemeli)
    assert tp.main([str(tmp_path / "yok")]) == 1
    assert "bulunamadi" in capsys.readouterr().err


def test_yalniz_txt_klasoru(tmp_path, monkeypatch, capsys):
    for i in range(3):
        (tmp_path / f"not{i}.txt").write_text("metin\n", encoding="utf-8")
    monkeypatch.setattr(te, "model_yukle", lambda: paket(0.0))
    assert tp.main([str(tmp_path)]) == 1                           # PE yok: 0 DEGIL
    c = capsys.readouterr()
    assert "PE degil      : 3" in c.out and "hic PE" in c.err
