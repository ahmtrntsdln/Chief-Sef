"""
Olcum tutarliligi testleri - CLAUDE.md Kritik Kural 1 ve 5'in otomatik hali.

Zararli taraf EMBER JSON'dan (ember_zararli_cikar), zararsiz taraf pefile ile
yerel dosyadan (toplu_tarama, Chief_1.2) olculur. Ayni sutun adi ayni olcum
demek degil: iki taraf ayni dosyayi ayni sayilara cevirmezse model olcum
farkini "zararlilik" diye ogrenir. Bu testler gecmis hatalarin (ordinal
import'lar, bos bolumler, EMBER2024'te kayan datadirectories indeksi) geri
gelmesini yakalar.

Yeni veri kaynagi eklenince: o kaynagin kayit bicimiyle yeni bir
EMBER_KAYITLARI girdisi ve ORDINAL/CLR orneklerine yeni bicimler ekle.

Calistirma (repo kokunden): python -m pytest tests
"""

import glob
import os
import re
import sys
from collections import Counter
from types import SimpleNamespace

import numpy as np
import pefile
import pytest

import ember_zararli_cikar as ezc
from dizge_ozellikleri import (EMBER2018_DIZGE_SUTUNLARI, kayittan_dizge_ozellikleri,
                               kayittan_ember2018_dizge)
import sef_sabitler
import toplu_tarama as tt

# --------------------------------------------------------------------------
# 1. Uc dosya da sabitleri AYNI kaynaktan kullaniyor
# --------------------------------------------------------------------------


def test_kara_liste_tek_kaynaktan(chief):
    assert chief.KARA_LISTE_BAYT is sef_sabitler.KARA_LISTE_BAYT
    assert tt.KARA_LISTE_BAYT is sef_sabitler.KARA_LISTE_BAYT
    assert ezc.KARA_LISTE is sef_sabitler.KARA_LISTE
    # pefile tarafi bytes, EMBER tarafi str: icerik birebir ayni olmali
    assert {ad.decode("ascii") for ad in sef_sabitler.KARA_LISTE_BAYT} == sef_sabitler.KARA_LISTE


def test_diger_sabitler_tek_kaynaktan(chief):
    assert chief.SIHIRLI_IMZALAR is sef_sabitler.SIHIRLI_IMZALAR
    assert tt.SIHIRLI_IMZALAR is sef_sabitler.SIHIRLI_IMZALAR
    assert ezc.ORDINAL_DESENI is sef_sabitler.ORDINAL_DESENI
    assert ezc.CLR_DIZIN_ADLARI is sef_sabitler.CLR_DIZIN_ADLARI
    assert tt.PEFILE_CLR_DIZIN_ADI == sef_sabitler.PEFILE_CLR_DIZIN_ADI


def test_pefile_clr_dizin_adi_gercek():
    """Sabit, kurulu pefile surumunun gercekten kullandigi ad olmali (14. dizin)."""
    assert pefile.DIRECTORY_ENTRY[sef_sabitler.PEFILE_CLR_DIZIN_ADI] == 14


# --------------------------------------------------------------------------
# 2. Ayni dosya: EMBER JSON kaydi == pefile tarafi
# --------------------------------------------------------------------------

# Sahte PE'nin icerigi. Bos bolum ve ordinal import bilerek var: ikisi de
# gecmiste iki tarafin farkli saydigi seyler.
BOLUMLER = [(".text", bytes(range(256)) * 8),
            (".data", b"\x00" * 300 + b"ab" * 100),
            (".bss", b"")]                                     # boyutu 0
IMPORTLAR = {"KERNEL32.dll": ["VirtualAlloc", "VirtualAllocEx",   # Ex: substring tuzagi
                              "VirtualAllocExNuma",                # listede YOK, iki adi da icerir
                              "GetProcAddress", None],            # None = ordinal
             "mscoree.dll": ["_CorExeMain"]}
# EMBER 2018 strings grubu icin kuyruk: buyuk/kucuk harf ve 5 karakter
# siniri tuzaklari (paths/urls harf duyarsiz, HKEY_ duyarli, "MZMZ" dizge sayilmaz).
KUYRUK = (b"\x00C:\\Windows\\a.dll\x00c:\\x\\yyyy\x00http://ornek.com\x00HTTPS://b.org/x\x00"
          b"HKEY_LOCAL_MACHINE\x00hkey_kucuk\x00MZMZ\x00")
DOSYA = b"MZ" + b"\x00" * 62 + b"".join(v for _, v in BOLUMLER) + b"\x90" * 50 + KUYRUK
DLL_KARAKTERISTIKLERI = ["EXECUTABLE_IMAGE", "DLL"]    # EMBER coff.characteristics
DLL_BAYRAKLARI = 0x0002 | 0x2000                          # pefile: EXECUTABLE_IMAGE | DLL


def _pefile_nesnesi(dizinler, bayraklar=DLL_BAYRAKLARI):
    return SimpleNamespace(
        FILE_HEADER=SimpleNamespace(Characteristics=bayraklar),
        sections=[SimpleNamespace(get_data=lambda v=v: v) for _, v in BOLUMLER],
        DIRECTORY_ENTRY_IMPORT=[
            SimpleNamespace(dll=dll.encode(),
                            imports=[SimpleNamespace(name=a.encode() if a else None) for a in adlar])
            for dll, adlar in IMPORTLAR.items()],
        OPTIONAL_HEADER=SimpleNamespace(DATA_DIRECTORY=dizinler),
    )


def _pefile_dizinleri(clr_indeksi=14, clr=(0x2008, 0x48)):
    """pefile DATA_DIRECTORY listesi; CLR girdisi istenen indekse konur."""
    dizinler = [SimpleNamespace(name=f"IMAGE_DIRECTORY_ENTRY_{i}", VirtualAddress=0x1000 * (i + 1), Size=0x10)
                for i in range(16)]
    dizinler[clr_indeksi] = SimpleNamespace(name=sef_sabitler.PEFILE_CLR_DIZIN_ADI,
                                            VirtualAddress=clr[0], Size=clr[1])
    return dizinler


def _ember_kaydi(bicim):
    ordinal = "ordinal5" if bicim == "2018" else "KERNEL32.dll:ordinal5"
    imports = {dll: [a if a else ordinal for a in adlar] for dll, adlar in IMPORTLAR.items()}
    if bicim == "2018":   # lief: 15 dizin, CLR 14. indekste
        dizinler = [{"name": f"DIZIN_{i}", "size": 16, "virtual_address": 4096} for i in range(15)]
        dizinler[14] = {"name": "CLR_RUNTIME_HEADER", "size": 0x48, "virtual_address": 0x2008}
    else:                 # thrember: basta dizin olmayan girdi, CLR 15. indekste
        dizinler = [{"name": "BASTAKI_GIRDI"}] + [
            {"name": f"DIZIN_{i}", "size": 16, "virtual_address": 4096} for i in range(15)]
        dizinler[15] = {"name": "COM_DESCRIPTOR", "size": 0x48, "virtual_address": 0x2008}
    sayim = Counter(DOSYA)
    dizgeler = re.findall(b"[\x20-\x7f]{5,}", DOSYA)
    c = np.bincount(np.frombuffer(b"".join(dizgeler), dtype=np.uint8) - 0x20, minlength=96)
    p = c[c > 0] / c.sum()
    strings = {"numstrings": len(dizgeler), "avlength": c.sum() / len(dizgeler),
               "printabledist": c.tolist(), "printables": int(c.sum()),
               "entropy": float(-(p * np.log2(p)).sum())}
    if bicim == "2018":   # ember v2: tum dosyada 4 sayim (elle, KUYRUK'tan)
        strings.update(paths=2, urls=2, registry=1, MZ=3)
    else:                 # thrember: 4 sayim yok, yerine regex sayimlari
        strings["string_counts"] = {}
    return {
        "sha256": "0" * 64,
        "general": {"size": len(DOSYA)},
        "histogram": [sayim.get(b, 0) for b in range(256)],
        "strings": strings,
        "header": {"coff": {"characteristics": DLL_KARAKTERISTIKLERI}},
        "section": {"sections": [{"name": ad, "size": len(v), "entropy": tt.shannon_entropy(v)}
                                 for ad, v in BOLUMLER]},
        "imports": imports,
        "datadirectories": dizinler,
    }


@pytest.fixture
def pefile_tarafi(tmp_path, monkeypatch):
    yol = tmp_path / "ornek.exe"
    yol.write_bytes(DOSYA)
    monkeypatch.setattr(tt.pefile, "PE", lambda *a, **k: _pefile_nesnesi(_pefile_dizinleri()))
    return tt.dosyayi_analiz_et(str(yol))


@pytest.mark.parametrize("bicim", ["2018", "2024"])
@pytest.mark.parametrize("sutun", ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
                                   "Toplam_API", "Supheli_API", "NET_mi", "Karma_Mod"])
def test_ember_ve_pefile_ayni_dosyayi_ayni_olcer(pefile_tarafi, bicim, sutun):
    ember_tarafi = ezc.kayittan_ozellik_cikar(_ember_kaydi(bicim), etiket=1)
    assert pefile_tarafi["PE_mi"]
    assert ember_tarafi[sutun] == pefile_tarafi[sutun]


def test_beklenen_degerler(pefile_tarafi):
    """Tutarlilik tek basina yetmez (iki taraf ayni yanlisi yapabilir):
    elle hesaplanan beklenen degerler."""
    assert pefile_tarafi["Toplam_API"] == 5        # ordinal sayilmaz
    assert pefile_tarafi["Supheli_API"] == 2       # tam esleme: ExNuma sayilmaz, cift sayim yok
    assert pefile_tarafi["NET_mi"] == 1
    assert pefile_tarafi["Karma_Mod"] == 1         # mscoree disinda KERNEL32
    beklenen = round((tt.shannon_entropy(BOLUMLER[0][1]) + tt.shannon_entropy(BOLUMLER[1][1])) / 2, 3)
    assert pefile_tarafi["Ortalama_Entropi"] == beklenen   # bos bolum ortalamaya girmez
    assert pefile_tarafi["DLL_mi"] == 1


# --- DLL_mi ve EMBER 2018 strings grubu ---

@pytest.mark.parametrize("bicim", ["2018", "2024"])
def test_dll_mi_ayni(pefile_tarafi, bicim):
    assert ezc.dll_mi(_ember_kaydi(bicim)) == pefile_tarafi["DLL_mi"] == 1


def test_exe_iki_tarafta_da_dll_degil():
    kayit = _ember_kaydi("2018")
    kayit["header"]["coff"]["characteristics"] = ["EXECUTABLE_IMAGE"]
    assert ezc.dll_mi(kayit) == tt.dll_mi(_pefile_nesnesi(_pefile_dizinleri(), bayraklar=0x0002)) == 0


@pytest.mark.parametrize("sutun", EMBER2018_DIZGE_SUTUNLARI)
def test_ember2018_dizge_ayni(pefile_tarafi, sutun):
    ember_tarafi = ezc.ember2018_kayittan(_ember_kaydi("2018"), etiket=1)
    assert ember_tarafi[sutun] == pytest.approx(pefile_tarafi[sutun], abs=1e-3)


def test_ember2018_dizge_beklenen(pefile_tarafi):
    """Elle: .text'te 8 x 96 karakterlik dizge (0x20-0x7f), .data'da 200, kuyrukta
    6 (MZMZ 4 karakter -> dizge degil). paths: C:\\ + c:\\, urls: http + HTTPS,
    registry: sadece buyuk harfli HKEY_, MZ: baslik + MZMZ'deki 2."""
    kuyruk = [16, 9, 16, 15, 18, 10]
    assert pefile_tarafi["DZ_sayi"] == 8 + 1 + len(kuyruk)
    assert pefile_tarafi["DZ18_yazdirilabilir"] == 8 * 96 + 200 + sum(kuyruk)
    assert (pefile_tarafi["DZ18_c_yolu"], pefile_tarafi["DZ18_http"],
            pefile_tarafi["DZ18_hkey"], pefile_tarafi["DZ18_mz"]) == (2, 2, 1, 3)


def test_eksik_dizge_alani_sessiz_sifir_olmaz():
    """EMBER 2018'de string_counts, EMBER2024'te paths/urls/registry/MZ yok:
    yanlis kaynaktan okumak hata vermeli, 0 yazmamali."""
    with pytest.raises(KeyError):
        kayittan_dizge_ozellikleri(_ember_kaydi("2018"))
    with pytest.raises(KeyError):
        kayittan_ember2018_dizge(_ember_kaydi("2024"))


def test_chief_supheli_sayimi_ayni(chief):
    nesne = _pefile_nesnesi(_pefile_dizinleri())
    sonuc = chief.supheli_fonksiyonlari_say(nesne)
    assert (sonuc["toplam"], sonuc["supheli"]) == tt.supheli_api_say(nesne) == (5, 2)


# --------------------------------------------------------------------------
# 3. Ordinal bicimleri
# --------------------------------------------------------------------------

@pytest.mark.parametrize("ad", ["ordinal5", "ordinal123", "WS2_32.dll:ordinal5", "KERNEL32.dll:ordinal1"])
def test_ordinal_eslesir(ad):
    assert sef_sabitler.ORDINAL_DESENI.match(ad)


@pytest.mark.parametrize("ad", ["VirtualAlloc", "ordinal", "ordinal5x", "GetOrdinal5",
                                "WS2_32.dll:connect", "Ordinal5"])
def test_ordinal_olmayan_eslesmez(ad):
    assert not sef_sabitler.ORDINAL_DESENI.match(ad)


# --------------------------------------------------------------------------
# 4. CLR dizini INDEKSLE degil ISIMLE bulunur
# --------------------------------------------------------------------------

def _ember_dizinleri(clr_adi, clr_indeksi, n=17):
    dizinler = [{"name": f"DIZIN_{i}", "size": 16, "virtual_address": 4096} for i in range(n)]
    if clr_adi:
        dizinler[clr_indeksi] = {"name": clr_adi, "size": 0x48, "virtual_address": 0x2008}
    return {"datadirectories": dizinler, "imports": {"mscoree.dll": ["_CorExeMain"]}}


@pytest.mark.parametrize("clr_adi", sorted(sef_sabitler.CLR_DIZIN_ADLARI))
@pytest.mark.parametrize("clr_indeksi", [3, 14, 15, 16])
def test_ember_clr_isimle_bulunur(clr_adi, clr_indeksi):
    assert ezc.net_ozellikleri(_ember_dizinleri(clr_adi, clr_indeksi)) == (1, 0)


def test_ember_14_indeksteki_baska_dizin_clr_sayilmaz():
    # CLR yok, 14. (ve 15.) indekste boyutu > 0 baska dizinler var
    assert ezc.net_ozellikleri(_ember_dizinleri(None, 0)) == (0, 0)


@pytest.mark.parametrize("clr_indeksi", [3, 14, 15])
def test_pefile_clr_isimle_bulunur(clr_indeksi):
    assert tt.net_ozellikleri(_pefile_nesnesi(_pefile_dizinleri(clr_indeksi))) == (1, 1)


def test_pefile_14_indeksteki_baska_dizin_clr_sayilmaz():
    dizinler = _pefile_dizinleri()
    dizinler[14] = SimpleNamespace(name="IMAGE_DIRECTORY_ENTRY_BASKA", VirtualAddress=0x2008, Size=0x48)
    assert tt.net_ozellikleri(_pefile_nesnesi(dizinler)) == (0, 0)


@pytest.mark.parametrize("va, boyut", [(0, 0x48), (0x2008, 0)])
def test_clr_boyut_ve_adres_ikisi_de_gerekli(va, boyut):
    kayit = _ember_dizinleri("COM_DESCRIPTOR", 15)
    kayit["datadirectories"][15].update(size=boyut, virtual_address=va)
    assert ezc.net_ozellikleri(kayit) == (0, 0)
    assert tt.net_ozellikleri(_pefile_nesnesi(_pefile_dizinleri(clr=(va, boyut)))) == (0, 0)


# --------------------------------------------------------------------------
# Gercek PE dosyalariyla duman testi (sahte nesnelerin gercek pefile ile
# ayni arayuzu kullandigini dogrular)
# --------------------------------------------------------------------------

def test_gercek_native_pe():
    sonuc = tt.dosyayi_analiz_et(sys.executable)
    assert sonuc["PE_mi"] and sonuc["NET_mi"] == 0 and sonuc["Toplam_API"] > 0


NET_ORNEKLERI = sorted(glob.glob(os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                                              "Microsoft.NET", "Framework64", "v4.*", "System.dll")))


@pytest.mark.skipif(not NET_ORNEKLERI, reason=".NET Framework yok")
def test_gercek_net_pe():
    assert tt.dosyayi_analiz_et(NET_ORNEKLERI[0])["NET_mi"] == 1
