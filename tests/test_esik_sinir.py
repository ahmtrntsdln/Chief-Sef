"""
Sef Projesi - Esik karsilastirmasinin sinir-deger testi (Python kosucusu)
=========================================================================

Iki seyi ayni tabloyla sinar:

  1) PYTHON tarafi - Faz 1'in bugunku kodu. Python tamsayilari keyfi
     buyuklukte oldugu icin burada tasma YOKTUR; bu testin Python kismi
     "zaten saglam" oldugunu sabitler, ileride biri tipi daraltirsa
     (ornegin numpy int8'e gecerse) kirilir ve haber verir.

  2) C tarafi - Faz 2/3'te ajan C'ye tasindiginda olusacak hal.
     esik_sinir.c derlenip ctypes ile yuklenir. Dar tipe yazilan skor
     128'de negatife sarar ve esik kontrolunu atlatir; test bunu
     BEKLENEN bir cokme olarak dogrular.

Kullanim:
    python tests/test_esik_sinir.py    # tek basina, pytest gerekmez
    python -m pytest tests             # diger testlerle birlikte

  3) DERLEYICI - projenin C varsayilan uyari bayraklariyla (-Wall -Wextra
     -Wconversion -Wsign-conversion) derleyici hatali satiri SATIR
     NUMARASIYLA gostermeli, dogru surumde tek uyari vermemeli. En ucuz
     savunma bu: bedeli sifir, hatayi calistirmadan yakaliyor. Bu dosya
     hatayi bilerek icerdigi icin burada -Werror YOK; ajan kodunda var.

C derleyicisi yoksa C kismi atlanir (pytest'te "skipped" gorunur, gecti
sayilmaz), Python kismi yine calisir.
"""

import ctypes
import os
import re
import shutil
import subprocess
import sys
import tempfile

ESIK = 100
SKOR_MIN = 0
SKOR_MAX = 255

BURASI = os.path.dirname(os.path.abspath(__file__))
C_KAYNAK = os.path.join(BURASI, "esik_sinir.c")
# Projenin C varsayilani (CLAUDE.md, Kritik Kural 7); -Werror ajan kodunda eklenir.
UYARI_BAYRAKLARI = ["-Wall", "-Wextra", "-Wconversion", "-Wsign-conversion"]
# Satir BASINDA (girinti haric) aranir: yorumlardaki ayni metin sayilmaz.
HATALI_SATIR = re.compile(r"^\s*signed char skor = ham_skor;")

# (skor, beklenen_supheli, aciklama)
# 128 ve 255 satirlari C'deki hatali surumu dusuren satirlar.
TABLO = [
    (0,   False, "taban"),
    (100, False, "esige esit - asmiyor"),
    (101, True,  "esigin bir ustu"),
    (127, True,  "signed char tavani"),
    (128, True,  "TASMA SINIRI - dar tipte -128 olur"),
    (255, True,  "unsigned tavani - dar tipte -1 olur"),
    (-1,  True,  "aralik disi - fail-closed, supheli sayilir"),
]


def esik_asti(ham_skor: int) -> bool:
    """Faz 1'in esik kontrolu: genis tip + aralik dogrulamasi.

    Aralik disindaki bir deger hesabin bozuldugunu gosterir. Guvenlik
    kapisinda dogru varsayilan dosyayi iceri almak degil, supheli
    isaretlemektir (fail-closed), bu yuzden True doner.
    """
    if not isinstance(ham_skor, int) or isinstance(ham_skor, bool):
        raise TypeError(f"skor tamsayi olmali, gelen: {type(ham_skor).__name__}")
    if ham_skor < SKOR_MIN or ham_skor > SKOR_MAX:
        return True
    return ham_skor > ESIK


# --------------------------------------------------------------------------
# 1) Python tarafi
# --------------------------------------------------------------------------

def python_testi() -> int:
    """Python esik fonksiyonunu sinir tablosunda dener. Hata sayisini doner."""
    hata = 0
    print("=== 1) PYTHON tarafi ===")
    print("skor | beklenen | sonuc    | not")
    print("-----+----------+----------+---------------------------------")
    for skor, beklenen, aciklama in TABLO:
        sonuc = esik_asti(skor)
        tamam = sonuc == beklenen
        if not tamam:
            hata += 1
        print(f"{skor:4d} | {'supheli' if beklenen else 'temiz':<8} | "
              f"{'supheli' if sonuc else 'temiz':<8} | "
              f"{'' if tamam else '[HATA] '}{aciklama}")
    print(f"\nPython: {len(TABLO) - hata}/{len(TABLO)} gecti"
          f"{' - BASARISIZ' if hata else ''}\n")
    return hata


# --------------------------------------------------------------------------
# 2) C tarafi
# --------------------------------------------------------------------------

def c_kutuphanesi_derle(hedef_dizin: str):
    """esik_sinir.c'yi paylasimli kutuphane olarak derler.

    Derleyici ya da kaynak yoksa None doner (test atlanir).
    """
    derleyici = shutil.which("gcc") or shutil.which("clang")
    if derleyici is None or not os.path.exists(C_KAYNAK):
        return None

    cikti = os.path.join(hedef_dizin, "esik_sinir.so")
    try:
        subprocess.run(
            [derleyici, "-shared", "-fPIC", "-O1", "-o", cikti, C_KAYNAK],
            check=True, capture_output=True, timeout=60,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"[!] C derlenemedi, C kismi atlaniyor: {e}")
        return None

    lib = ctypes.CDLL(cikti)
    lib.esik_asti_dogru.argtypes = [ctypes.c_int32]
    lib.esik_asti_dogru.restype = ctypes.c_bool
    lib.esik_asti_hatali.argtypes = [ctypes.c_int]
    lib.esik_asti_hatali.restype = ctypes.c_bool
    return lib


def hatali_satir_no() -> int:
    """esik_sinir.c'de sessiz daralmanin yapildigi satirin numarasi."""
    with open(C_KAYNAK, encoding="utf-8") as f:
        bulunan = [no for no, satir in enumerate(f, 1) if HATALI_SATIR.match(satir)]
    assert len(bulunan) == 1, f"esik_sinir.c'de tam bir daralma satiri bekleniyordu: {bulunan}"
    return bulunan[0]


def derleyici_uyarilari(hedef_dizin: str):
    """esik_sinir.c'yi proje uyari bayraklariyla derler; uyari verilen satir
    numaralarini dondurur. Derleyici yoksa None."""
    derleyici = shutil.which("gcc") or shutil.which("clang")
    if derleyici is None or not os.path.exists(C_KAYNAK):
        return None
    sonuc = subprocess.run(
        [derleyici, "-c", *UYARI_BAYRAKLARI, "-o", os.path.join(hedef_dizin, "esik_sinir.o"), C_KAYNAK],
        capture_output=True, text=True, timeout=60,
    )
    desen = re.compile(r"esik_sinir\.c:(\d+):\d+: warning:")
    return sorted({int(m.group(1)) for m in desen.finditer(sonuc.stderr)}), sonuc.stderr


def c_testi(lib) -> int:
    """C'nin dogru ve hatali surumunu ayni tabloda dener.

    Dogru surum tabloyu tam gecmeli. Hatali surum EN AZ BIR satiri
    kacirmali - kacirmiyorsa tablo artik tasmayi olcmuyor demektir.
    """
    dogru_hata = hatali_kacirdi = 0
    print("=== 2) C tarafi (Faz 2'de olusacak hal) ===")
    print("skor | beklenen | dogru    | hatali   | not")
    print("-----+----------+----------+----------+------------------------")
    for skor, beklenen, aciklama in TABLO:
        d = bool(lib.esik_asti_dogru(skor))
        h = bool(lib.esik_asti_hatali(skor))
        if d != beklenen:
            dogru_hata += 1
        if h != beklenen:
            hatali_kacirdi += 1
        print(f"{skor:4d} | {'supheli' if beklenen else 'temiz':<8} | "
              f"{'supheli' if d else 'temiz':<8} | "
              f"{'supheli' if h else 'temiz':<8} | "
              f"{'[KACIRDI] ' if h != beklenen else ''}{aciklama}")

    print(f"\nC dogru surum : {len(TABLO) - dogru_hata}/{len(TABLO)} gecti")
    print(f"C hatali surum: {len(TABLO) - hatali_kacirdi}/{len(TABLO)} gecti "
          f"(kacirmasi BEKLENIYOR)\n")

    hata = 0
    if dogru_hata:
        print("[HATA] C'nin dogru surumu sinirlarda yanlis karar verdi.")
        hata += 1
    if hatali_kacirdi == 0:
        print("[HATA] Hatali surum de gecti - tablo tasmayi artik olcmuyor.")
        hata += 1
    return hata


# --------------------------------------------------------------------------
# pytest arayuzu (pytest varsa bu testleri toplar)
# --------------------------------------------------------------------------

def _derleyici_yoksa_atla(lib):
    """Derleyici yokken C testi 'gecti' gorunmesin: pytest'te acikca atlanir."""
    if lib is None:
        import pytest
        pytest.skip("C derleyicisi (gcc/clang) yok; C kismi calismadi")


def test_python_esik_sinirlari():
    for skor, beklenen, aciklama in TABLO:
        assert esik_asti(skor) is beklenen, f"skor={skor} ({aciklama})"


def test_c_dogru_surum_sinirlari():
    with tempfile.TemporaryDirectory() as d:
        lib = c_kutuphanesi_derle(d)
        _derleyici_yoksa_atla(lib)
        for skor, beklenen, aciklama in TABLO:
            assert bool(lib.esik_asti_dogru(skor)) is beklenen, \
                f"skor={skor} ({aciklama})"


def test_c_hatali_surum_tasmayi_gosteriyor():
    """128 dar tipte negatife sarip esigi atlatmali.

    Bu test 'hata hala orada' demek icin degil, tablonun tasmayi
    gercekten olctugunu dogrulamak icin var.
    """
    with tempfile.TemporaryDirectory() as d:
        lib = c_kutuphanesi_derle(d)
        _derleyici_yoksa_atla(lib)
        assert bool(lib.esik_asti_hatali(128)) is False, \
            "128 artik sarmiyor - tablo tasmayi olcmuyor"
        assert bool(lib.esik_asti_dogru(128)) is True, \
            "dogru surum 128'i supheli saymali"


def test_derleyici_daralmayi_satir_numarasiyla_gosteriyor():
    """Proje uyari bayraklariyla: hatali satir uyari almali, BASKA HICBIR satir
    almamali (dogru surum bu bayraklarla temiz derlenmeli)."""
    with tempfile.TemporaryDirectory() as d:
        sonuc = derleyici_uyarilari(d)
        _derleyici_yoksa_atla(sonuc)
        satirlar, cikti = sonuc
        beklenen = hatali_satir_no()
        assert beklenen in satirlar, \
            f"{' '.join(UYARI_BAYRAKLARI)} hatali satiri ({beklenen}) gostermedi:\n{cikti}"
        assert satirlar == [beklenen], \
            f"hatali satir disinda da uyari var (dogru surum temiz olmali): {satirlar}\n{cikti}"


# --------------------------------------------------------------------------

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    print("Sef - Esik sinir-deger testi\n")

    hata = python_testi()

    with tempfile.TemporaryDirectory() as d:
        lib = c_kutuphanesi_derle(d)
        if lib is None:
            print("=== 2) C tarafi ATLANDI (derleyici bulunamadi) ===\n")
        else:
            hata += c_testi(lib)

        sonuc = derleyici_uyarilari(d)
        if sonuc is None:
            print("=== 3) DERLEYICI uyarilari ATLANDI (derleyici bulunamadi) ===\n")
        else:
            satirlar, _ = sonuc
            beklenen = hatali_satir_no()
            tamam = satirlar == [beklenen]
            print(f"=== 3) DERLEYICI ({' '.join(UYARI_BAYRAKLARI)}) ===\n"
                  f"uyari verilen satirlar: {satirlar}, beklenen: [{beklenen}] -> "
                  f"{'tamam' if tamam else '[HATA]'}\n")
            hata += 0 if tamam else 1

    print("SONUC:", "BASARILI" if hata == 0 else f"BASARISIZ ({hata} sorun)")
    sys.exit(1 if hata else 0)
