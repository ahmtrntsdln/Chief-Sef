"""
Sef Projesi - Faz 1: Toplu Zararsiz Tarama
============================================================

Chief_1.2.py'daki ayni fonksiyonlari kullanarak bir klasor agacindaki
TUM dosyalari tarar ve sef_dataset_zararsiz_gercek.csv uretir.

ONEMLI TASARIM KARARI:
EMBER'deki zararli veri SADECE Windows PE (calistirilabilir) dosyalarindan
olusuyor. Zararsiz tarafina .docx, .jpg, .txt gibi calistirilamayan
dosyalari da katarsak, model "zararli mi?" sorusunu degil, "bu dosya
calistirilabilir mi?" sorusunu ogrenir - ki gecen seferki sizintinin
baska bir versiyonu olur. Bu yuzden bu script HEM tum dosyalari tarayip
genel bir kayit tutuyor, HEM DE egitim icin sadece PE dosyalarini
iceren ayri, filtrelenmis bir CSV uretiyor. Random Forest'i o filtrelenmis
CSV (PE-vs-PE) uzerinde egitmelisin, EMBER'deki zararliyla karsilastirmak icin.
"""

import csv
import math
import os
from collections import Counter

import pefile

# Kendi 5700 dosyalik taramani yaptigin klasorleri buraya ekle
TARANACAK_KLASORLER = [
    r"C:\Windows\System32",
    r"C:\Program Files",
]

TAM_CIKTI = "sef_tarama_tum_dosyalar.csv"          # her sey (PE olsun olmasin)
PE_CIKTI = "sef_dataset_zararsiz_gercek.csv"        # egitimde kullanilacak olan

KARA_LISTE = {
    b'VirtualAlloc', b'VirtualAllocEx', b'WriteProcessMemory',
    b'CreateRemoteThread', b'SetWindowsHookEx', b'IsDebuggerPresent',
}

SIHIRLI_IMZALAR = {
    b'MZ': "PE",
    b'\x7fELF': "ELF",
    b'%PDF': "PDF",
    b'PK\x03\x04': "ZIP",
    b'\xFF\xD8\xFF': "JPEG",
}


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    sayimlar = Counter(data)
    toplam = len(data)
    entropi = 0.0
    for adet in sayimlar.values():
        olasilik = adet / toplam
        entropi -= olasilik * math.log2(olasilik)
    return entropi


def dosya_turunu_bul(dosya_yolu: str) -> str:
    try:
        with open(dosya_yolu, "rb") as f:
            bas = f.read(8)
        for imza, ad in SIHIRLI_IMZALAR.items():
            if bas.startswith(imza):
                return ad
        return "Bilinmeyen"
    except Exception:
        return "Okuma_Hatasi"


def supheli_api_say(pe) -> tuple:
    toplam, supheli = 0, 0
    if not hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        return toplam, supheli
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if imp.name:
                toplam += 1
                if imp.name in KARA_LISTE:
                    supheli += 1
    return toplam, supheli


def dosyayi_analiz_et(dosya_yolu: str) -> dict:
    """Chief_1.2.py mantigiyla tek bir dosyadan ozellik cikarir."""
    try:
        boyut = os.path.getsize(dosya_yolu)
    except OSError:
        return None

    if boyut == 0:
        return None  # bos dosyalar analiz acisindan anlamsiz

    tur = dosya_turunu_bul(dosya_yolu)

    try:
        with open(dosya_yolu, "rb") as f:
            veri = f.read()
    except (OSError, PermissionError):
        return None

    sifir_orani = (veri.count(b"\x00") / boyut) * 100

    pe_mi = False
    toplam_api = 0
    supheli_api = 0
    ortalama_entropi = shannon_entropy(veri)  # varsayilan: tum dosya entropisi

    if tur == "PE":
        try:
            pe = pefile.PE(dosya_yolu)
            entropiler = []
            for section in pe.sections:
                sveri = section.get_data()
                if len(sveri) > 0:
                    entropiler.append(shannon_entropy(sveri))
            if entropiler:
                ortalama_entropi = sum(entropiler) / len(entropiler)
            toplam_api, supheli_api = supheli_api_say(pe)
            pe_mi = True
        except pefile.PEFormatError:
            pe_mi = False  # MZ ile basliyor ama gecerli PE degil

    return {
        "Dosya_Adi": os.path.basename(dosya_yolu),
        "Boyut_Bayt": boyut,
        "Sifir_Orani": round(sifir_orani, 2),
        "Ortalama_Entropi": round(ortalama_entropi, 3),
        "Toplam_API": toplam_api,
        "Supheli_API": supheli_api,
        "PE_mi": pe_mi,
        "Etiket": 0,
    }


def klasorleri_tara(klasorler):
    sonuclar = []
    islenen, atlanan = 0, 0
    for klasor in klasorler:
        for kok, _, dosyalar in os.walk(klasor):
            for ad in dosyalar:
                yol = os.path.join(kok, ad)
                sonuc = dosyayi_analiz_et(yol)
                islenen += 1
                if sonuc is None:
                    atlanan += 1
                else:
                    sonuclar.append(sonuc)
                if islenen % 500 == 0:
                    print(f"  ... {islenen} dosya tarandi "
                          f"({len(sonuclar)} basarili, {atlanan} atlandi)")
    return sonuclar, islenen, atlanan


if __name__ == "__main__":
    print("=== Gumruk Memuru: Toplu Zararsiz Tarama ===")
    tum_sonuclar, islenen, atlanan = klasorleri_tara(TARANACAK_KLASORLER)

    kolonlar = ["Dosya_Adi", "Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
                "Toplam_API", "Supheli_API", "PE_mi", "Etiket"]

    with open(TAM_CIKTI, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=kolonlar)
        yazici.writeheader()
        yazici.writerows(tum_sonuclar)

    pe_satirlar = [s for s in tum_sonuclar if s["PE_mi"]]
    egitim_kolonlari = ["Dosya_Adi", "Boyut_Bayt", "Sifir_Orani",
                         "Ortalama_Entropi", "Toplam_API", "Supheli_API", "Etiket"]
    with open(PE_CIKTI, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=egitim_kolonlari)
        yazici.writeheader()
        for s in pe_satirlar:
            yazici.writerow({k: s[k] for k in egitim_kolonlari})

    print(f"\n[+] Toplam {islenen} dosya tarandi ({atlanan} atlandi)")
    print(f"[+] {len(tum_sonuclar)} dosya basariyla analiz edildi -> '{TAM_CIKTI}'")
    print(f"[+] Bunlardan {len(pe_satirlar)} tanesi gercek PE dosyasi -> '{PE_CIKTI}'")
    print("    (EMBER'deki zararliyla karsilastirmak icin SADECE bu dosyayi kullan)")
