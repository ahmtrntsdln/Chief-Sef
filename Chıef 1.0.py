"""
Sef Projesi - Faz 1: Konseptin Ispati
Gumruk Memuru - Sihirli Numara (Magic Bytes) ve Bolum Bazli Entropi Analizi
"""

import pefile
import math
import os
from collections import Counter

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
    """Dosyanin ilk baytlarina (Magic Bytes) bakarak gercek formatini tespit eder."""
    # Yaygin sihirli numaralar (Hexadecimal/Byte karsiliklari)
    sihirli_imzalar = {
        b'MZ': "Windows Calistirilabilir Dosya (PE / .exe / .dll)",
        b'\x7fELF': "Linux Calistirilabilir Dosya (ELF)",
        b'%PDF': "PDF Belgesi",
        b'PK\x03\x04': "ZIP Arşivi / Paketlenmis Dosya",
        b'\xFF\xD8\xFF': "JPEG Gorseli",
        b'\x89PNG\x0D\x0A\x1A\x0A': "PNG Gorseli"
    }
    
    try:
        with open(dosya_yolu, "rb") as f:
            # Cogu formati tanimak icin ilk 8 bayti okumak yeterlidir
            dosya_basi = f.read(8) 
            
        for imza, aciklama in sihirli_imzalar.items():
            if dosya_basi.startswith(imza):
                return aciklama
        return "Bilinmeyen Format veya Duz Metin"
    except Exception as e:
        return f"Okuma Hatasi: {e}"

def gumruk_memuru_tam_analiz(dosya_yolu: str):
    """Sihirli Numara kontrolunu ve PE Bolum entropilerini tek potada eritir."""
    if not os.path.exists(dosya_yolu):
        print(f"Hata: Dosya bulunamadi -> {dosya_yolu}")
        return

    dosya_adi = os.path.basename(dosya_yolu)
    uzanti = os.path.splitext(dosya_adi)[1].lower()
    
    print(f"\n{'='*50}")
    print(f"GUMRUK MEMURU ANALIZ RAPORU: {dosya_adi}")
    print(f"{'='*50}")

    # 1. Aşama: Sihirli Numara ve Uzantı Kontrolü
    gercek_tur = gercek_dosya_turunu_bul(dosya_yolu)
    print("[*] KIMLIK KONTROLU")
    print(f"    Gorunen Uzanti : {uzanti if uzanti else 'Yok'}")
    print(f"    Gercek Format  : {gercek_tur}")
    
    # Basit bir anomali tespiti mantigi (Ornegin uzanti txt ama gercek format exe ise)
    if "Windows Calistirilabilir" in gercek_tur and uzanti not in ['.exe', '.dll', '.sys']:
        print("    [!] TEHLIKE: Dosya uzantisi gizlenmis! Gercekte bir calistirilabilir dosya.")

    print("\n[*] BOLUM BAZLI ENTROPI ANALIZI (RONTGEN)")
    # 2. Aşama: Eger dosya gercekten bir PE (Windows) dosyasiysa icine gir
    if "Windows Calistirilabilir" in gercek_tur:
        try:
            pe = pefile.PE(dosya_yolu)
            for section in pe.sections:
                bolum_adi = section.Name.decode('utf-8', errors='ignore').rstrip('\x00')
                veri = section.get_data()
                boyut = len(veri)
                
                entropi = shannon_entropy(veri) if boyut > 0 else 0.0
                bar = "#" * int(entropi * 5)
                
                # Sifrelenmis/Paketlenmis bolum tespiti icin basit bir esik degeri (Threshold)
                uyari = " [!] YUKSEK ENTROPI (Sifreli/Paketli Olabilir)" if entropi > 7.5 else ""
                
                print(f"    Bolum: {bolum_adi:<8} | Boyut: {boyut:<8} bayt | Entropi: {entropi:.3f} {bar}{uyari}")
                
        except pefile.PEFormatError:
            print("    [!] Hata: Dosya PE formatina sahip degil veya bozuk.")
    else:
        print("    [i] Bu dosya bir Windows calistirilabilir (PE) dosyasi degil, bolum analizi atlandi.")

if __name__ == "__main__":
    # Testleri kendi bilgisayarindaki dosyalar uzerinde yapabilirsin.
    # Ornegin bir metin dosyasi olusturup uzantisini .exe yapmayi deneyebilirsin.
    test_dosyasi = "C:\\Windows\\System32\\cmd.exe" 
    gumruk_memuru_tam_analiz(test_dosyasi)