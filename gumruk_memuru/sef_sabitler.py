"""
Sef Projesi - ortak olcum sabitleri
============================================================

Zararli (EMBER JSON) ve zararsiz (pefile ile yerel tarama) taraflar AYNI
olcumle uretilmeli (CLAUDE.md, Kritik Kural 1). Bu sabitler eskiden
Chief_1.2.py, toplu_tarama.py ve ember_zararli_cikar.py'de ayri ayri
kopyalanmisti; birinde yapilan degisiklik digerine yansimazsa iki sinif
sessizce farkli olculur ve model olcum farkini ogrenir. Tek kaynak burasi.

Fonksiyonlar birlestirilmedi: girdiler farkli (pefile nesnesi vs EMBER
JSON dict), ortak olan sadece veri. Tutarlilik testleri:
tests/test_olcum_tutarliligi.py.
"""

import re

# Supheli Windows API kara listesi (tam esleme, substring DEGIL: 'VirtualAlloc'
# 'VirtualAllocEx' icinde gecer - v1.1'deki cift sayim hatasi).
# EMBER JSON import adlari str, pefile imp.name bytes: ikisi AYNI kumeden turer.
KARA_LISTE = frozenset({
    "VirtualAlloc", "VirtualAllocEx", "WriteProcessMemory",
    "CreateRemoteThread", "SetWindowsHookEx", "IsDebuggerPresent",
})
KARA_LISTE_BAYT = frozenset(ad.encode("ascii") for ad in KARA_LISTE)

# Sihirli bayt imzalari: imza -> (kisa ad, okunur aciklama).
# toplu_tarama.py kisa adi ("PE"), Chief_1.2.py aciklamayi kullanir.
SIHIRLI_IMZALAR = {
    b"MZ": ("PE", "Windows Calistirilabilir Dosya (PE)"),
    b"\x7fELF": ("ELF", "Linux Calistirilabilir Dosya (ELF)"),
    b"%PDF": ("PDF", "PDF Belgesi"),
    b"PK\x03\x04": ("ZIP", "ZIP Arsivi"),
    b"\xFF\xD8\xFF": ("JPEG", "JPEG Gorseli"),
}

# Isimsiz (ordinal) import'lar: pefile'da imp.name None, sayilmaz. EMBER
# bunlari metin olarak yazar: 2018 "ordinal5", 2024 "WS2_32.dll:ordinal5".
ORDINAL_DESENI = re.compile(r"^(?:.+:)?ordinal\d+$")

# CLR (.NET) veri dizininin adi - INDEKSLE degil ISIMLE aranir: EMBER2024
# listesinin basinda dizin olmayan bir girdi var, indeks bir kayar.
CLR_DIZIN_ADLARI = frozenset({"CLR_RUNTIME_HEADER",   # EMBER 2018 (lief)
                              "COM_DESCRIPTOR"})      # EMBER2024 (thrember/pefile)
PEFILE_CLR_DIZIN_ADI = "IMAGE_DIRECTORY_ENTRY_COM_DESCRIPTOR"   # yerel pefile
