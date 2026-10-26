"""
Tarama bittikten sonra dosya silinebilir / yeniden adlandirilabilir olmali (dosya tutamaci ya da
bellek eslemesi sizmamali).

Neden: toplu_tarama.dosyayi_analiz_et pefile.PE'yi dosya YOLUNDAN aciyordu ve kapatmiyordu. pefile
dosyayi bellege esler; nesne ancak dongusel cop toplayici calisinca serbest kaliyordu. Windows'ta
o zamana kadar dosya kilitli: test_olasi_zararli_cikis_kodu tek basina belirlenimci olarak
dusuyordu (paket icinde onceki testlerin tetikledigi cop toplama hatayi gizliyordu). Gercek
kullanimda toplu_tahmin taranan dosyalari kilitli birakabilirdi.

Test sirasinda cop toplayici KAPALI: sizinti varsa toplayici onu tesadufen gizleyemez.
Not: Linux'ta acik dosya silinebildigi icin bu test orada sizintiyi yakalamaz; Windows'ta yakalar.
Calistirma: python -m pytest tests
"""

import contextlib
import gc
import io
import os
import shutil
import sys

import pytest

import ozellik_cikar
import toplu_tahmin as tp
import toplu_tarama as tt
from test_tahmin_karar import NET_ORNEKLERI, paket


@pytest.fixture
def gc_kapali():
    acikti = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        if acikti:
            gc.enable()


def _chief_analiz(chief, yol):
    with contextlib.redirect_stdout(io.StringIO()):
        chief.gumruk_memuru_tam_analiz(yol)


TARAYICILAR = {
    "toplu_tarama.dosyayi_analiz_et": lambda yol, chief: tt.dosyayi_analiz_et(yol),
    "ozellik_cikar.dosya_ozellikleri": lambda yol, chief: ozellik_cikar.dosya_ozellikleri(yol),
    "toplu_tahmin.tara": lambda yol, chief: tp.tara([yol], paket(0.0)),
    "Chief_1.2.gumruk_memuru_tam_analiz": lambda yol, chief: _chief_analiz(chief, yol),
}


@pytest.mark.parametrize("ad", TARAYICILAR)
def test_tarama_sonrasi_dosya_kilitli_kalmaz(ad, tmp_path, gc_kapali, chief, capsys):
    kaynaklar = {"native.exe": sys.executable}
    if NET_ORNEKLERI:
        kaynaklar["net.dll"] = NET_ORNEKLERI[0]
    for hedef, kaynak in kaynaklar.items():
        yol = tmp_path / hedef
        shutil.copy(kaynak, yol)
        TARAYICILAR[ad](str(yol), chief)
        yeni = tmp_path / (hedef + ".yeni")
        os.rename(yol, yeni)          # kilit varsa PermissionError [WinError 32]
        os.unlink(yeni)
        assert not yeni.exists()
    capsys.readouterr()
