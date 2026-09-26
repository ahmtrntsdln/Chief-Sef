"""
Sef Projesi - Faz 1: Konseptin Ispati
Gumruk Memuru - Tam Statik Analiz Motoru (v1.2 - duzeltilmis)

Degisiklik (v1.1 -> v1.2):
  KARA_LISTE bir liste yerine artik bir set, ve "substring" kontrolu
  yerine TAM ESLESME kontrol ediliyor. Eskiden 'VirtualAlloc' ifadesi
  'VirtualAllocEx' icinde de gectigi icin tek bir import iki kez
  sayiliyordu (supheli_api yanlislikla sisiyordu). Ayrica set kullanmak
  aramayi O(n)'den O(1)'e dusurur.
  KARA_LISTE ve sihirli imzalar artik sef_sabitler.py'de (tek kaynak).
"""

import pefile
import math
import os
import sys
from collections import Counter

from sef_sabitler import KARA_LISTE_BAYT, SIHIRLI_IMZALAR


def shannon_entropy(data: bytes) -> float:
    """Bayt dizisinin Shannon entropisini hesaplar."""
    if not data:
        return 0.0
    sayimlar = Counter(data)
    toplam = len(data)
    entropi = 0.0
    for adet in sayimlar.values():
        olasilik = adet / toplam
        entropi -= olasilik * math.log2(olasilik)
    return entropi


def gercek_dosya_turunu_bul(dosya_yolu: str) -> str:
    """Sihirli Numaralara (Magic Bytes) bakarak dosyanin gercek kimligini bulur."""
    try:
        with open(dosya_yolu, "rb") as f:
            dosya_basi = f.read(8)
        for imza, (_, aciklama) in SIHIRLI_IMZALAR.items():
            if dosya_basi.startswith(imza):
                return aciklama
        return "Bilinmeyen Format"
    except OSError as e:
        # Sadece beklenen okuma hatasi (izin, kilitli dosya) yakalanir; kod
        # hatalari "Okuma Hatasi" kilifina girip gizlenmesin diye Exception degil.
        print(f"[!] Uyari: dosya turu okunamadi ({dosya_yolu}): {e}", file=sys.stderr)
        return f"Okuma Hatasi: {e}"


def supheli_fonksiyonlari_say(pe) -> dict:
    """IAT tablosunu okur ve kritik Windows API cagrilarini tespit eder."""
    sonuc = {"toplam": 0, "supheli": 0, "detay": []}

    if not hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        return sonuc

    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if imp.name:
                sonuc["toplam"] += 1
                # DUZELTME: "in" (substring) yerine kume uyeligi (tam esleme)
                if imp.name in KARA_LISTE_BAYT:
                    sonuc["supheli"] += 1
                    sonuc["detay"].append(imp.name.decode('utf-8'))
    return sonuc


def boyut_ve_sifir_yogunlugu_hesapla(dosya_yolu: str) -> dict:
    """Dosyanin boyutunu ve icindeki 0x00 (sifir) baytlarinin oranini hesaplar."""
    boyut = os.path.getsize(dosya_yolu)
    if boyut == 0:
        return {"boyut_bayt": 0, "sifir_orani": 0.0}
    try:
        with open(dosya_yolu, "rb") as f:
            veri = f.read()
            sifir_sayisi = veri.count(b'\x00')
            oran = (sifir_sayisi / boyut) * 100
            return {"boyut_bayt": boyut, "sifir_orani": oran}
    except OSError as e:
        # 0.0 gercek bir olcum gibi gorunur; en azindan olcum yapilamadigi duyulsun.
        print(f"[!] Uyari: sifir orani hesaplanamadi, 0.0 kullaniliyor "
              f"({dosya_yolu}): {e}", file=sys.stderr)
        return {"boyut_bayt": boyut, "sifir_orani": 0.0}


def gumruk_memuru_tam_analiz(dosya_yolu: str):
    """Tum statik analiz modulunu calistirir ve sonuclari raporlar."""
    if not os.path.exists(dosya_yolu):
        print(f"Hata: Dosya bulunamadi -> {dosya_yolu}")
        return

    print(f"\n{'='*60}")
    print(f" GUMRUK MEMURU: {os.path.basename(dosya_yolu)}")
    print(f"{'='*60}")

    gercek_tur = gercek_dosya_turunu_bul(dosya_yolu)
    boyut_bilgisi = boyut_ve_sifir_yogunlugu_hesapla(dosya_yolu)

    print("[*] GENEL ANALIZ")
    print(f"    Gercek Format  : {gercek_tur}")
    print(f"    Dosya Boyutu   : {boyut_bilgisi['boyut_bayt']} bayt")
    print(f"    Sifir Yogunlugu: %{boyut_bilgisi['sifir_orani']:.2f}")

    if boyut_bilgisi['sifir_orani'] > 30.0:
        print("    [!] UYARI: Anormal derecede yuksek 0x00 bayt orani (Zero-Padding tespiti)")

    if "Windows Calistirilabilir" in gercek_tur:
        print("\n[*] BOLUM BAZLI ENTROPI (RONTGEN)")
        try:
            pe = pefile.PE(dosya_yolu)
            for section in pe.sections:
                bolum_adi = section.Name.decode('utf-8', errors='ignore').rstrip('\x00')
                veri = section.get_data()
                entropi = shannon_entropy(veri) if len(veri) > 0 else 0.0
                bar = "#" * int(entropi * 5)
                uyari = " [!] YUKSEK (Paketli?)" if entropi > 7.5 else ""
                print(f"    {bolum_adi:<8} | Entropi: {entropi:.3f} {bar}{uyari}")

            print("\n[*] IAT (API CAGRISI) ANALIZI")
            iat_sonuc = supheli_fonksiyonlari_say(pe)
            print(f"    Toplam API Cagrisi: {iat_sonuc['toplam']}")
            print(f"    Supheli API Sayisi: {iat_sonuc['supheli']}")
            if iat_sonuc['supheli'] > 0:
                print(f"    Tespit Edilenler  : {', '.join(iat_sonuc['detay'])}")

        except pefile.PEFormatError:
            print("    [!] Hata: Gecerli bir PE dosyasi degil.")
    else:
        print("\n[i] PE dosyasi olmadigi icin IAT ve Bolum analizi atlandi.")


if __name__ == "__main__":
    # Test asamasinda Windows'un kendi guvenli araclari uzerinde deneyebilirsin
    # Ornegin: "C:\\Windows\\System32\\notepad.exe"
    test_dosyasi = "C:\\Windows\\System32\\cmd.exe"
    gumruk_memuru_tam_analiz(test_dosyasi)
