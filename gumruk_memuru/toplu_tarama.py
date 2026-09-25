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
genel bir kayit tutuyor, HEM DE sadece PE dosyalarini iceren ayri,
filtrelenmis bir CSV uretiyor.

Bu PE CSV'si EGITIMDE KULLANILMAZ: zararsiz veri tek bir makineden gelince
model "zararli mi?" yerine "bu makineden mi?" sorusunu ogreniyordu (kaynak
yanliligi). Model EMBER zararli + EMBER zararsiz ile egitilir; bu CSV
rf_egit_gercek.py'de dis dogrulama (gercek makinede yanlis alarm orani)
icin kullanilir.
"""

import argparse
import csv
import math
import os
import random
import sys
import time
from collections import Counter

import pefile

# Kendi 5700 dosyalik taramani yaptigin klasorleri buraya ekle
TARANACAK_KLASORLER = [
    r"C:\Windows\System32",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
]

TAM_CIKTI = "sef_tarama_tum_dosyalar.csv"          # her sey (PE olsun olmasin)
PE_CIKTI = "sef_dataset_zararsiz_gercek.csv"        # dis dogrulama seti (egitimde kullanilmaz)
HEDEF_SAYI = 5700   # EMBER siniflariyla ayni boyut

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

    if boyut > 100 * 1024 * 1024:
        return None  # 100 MB ustu: gercek PE dosyalari bu kadar buyuk olmaz,
                      # tum dosyayi belleğe okumak (f.read()) asiri yavasliyor

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
        "Dosya_Yolu": dosya_yolu,
        "Dosya_Adi": os.path.basename(dosya_yolu),
        "Boyut_Bayt": boyut,
        "Sifir_Orani": round(sifir_orani, 2),
        "Ortalama_Entropi": round(ortalama_entropi, 3),
        "Toplam_API": toplam_api,
        "Supheli_API": supheli_api,
        "PE_mi": pe_mi,
        "Etiket": 0,
    }


def dosyalari_listele(klasorler):
    yollar = []
    for klasor in klasorler:
        for kok, _, dosyalar in os.walk(klasor):
            yollar.extend(os.path.join(kok, ad) for ad in dosyalar)
    return yollar


def onceki_kayitlari_yukle(yol: str):
    """Yarim kalan taramanin ara kaydini okur; kesilme aninda yarim yazilmis
    son satir varsa (eksik alanli) onu atar."""
    if not os.path.exists(yol):
        return []
    with open(yol, newline="", encoding="utf-8") as f:
        satirlar = [s for s in csv.DictReader(f)
                    if all(s.get(k) not in (None, "") for k in KOLONLAR)]
    for s in satirlar:
        s["PE_mi"] = s["PE_mi"] == "True"
    return satirlar


def ilerleme_satiri(islenen, toplam, basarili, atlanan, baslangic):
    gecen = time.monotonic() - baslangic
    hiz = islenen / gecen if gecen > 0 else 0.0
    kalan = (toplam - islenen) / hiz if hiz > 0 else 0.0
    oran = islenen / toplam if toplam else 1.0
    dolu = int(oran * 30)
    cubuk = "#" * dolu + "-" * (30 - dolu)
    return (f"  [{cubuk}] %{oran * 100:5.1f} | {islenen}/{toplam} | "
            f"{basarili} basarili, {atlanan} atlandi | {hiz:.0f} dosya/sn | "
            f"gecen {gecen / 60:.1f} dk, kalan ~{kalan / 60:.1f} dk")


KOLONLAR = ["Dosya_Yolu", "Dosya_Adi", "Boyut_Bayt", "Sifir_Orani",
            "Ortalama_Entropi", "Toplam_API", "Supheli_API", "PE_mi", "Etiket"]
ILERLEME_DOSYA_ARALIGI = 500
ILERLEME_SANIYE_ARALIGI = 30


if __name__ == "__main__":
    # stdout bir dosyaya/pipe'a yonlendirildiginde Python blok-tamponlar;
    # satir tamponuna gecmezsek ilerleme ancak is bitince gorunur.
    sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="Gumruk Memuru toplu zararsiz tarama")
    parser.add_argument("--devam", action="store_true",
                        help=f"yarim kalan taramayi '{TAM_CIKTI}' ara kaydindan surdur")
    args = parser.parse_args()

    print("=== Gumruk Memuru: Toplu Zararsiz Tarama ===")
    print("[*] Dosyalar listeleniyor (ilerleme yuzdesi icin)...")
    tum_yollar = dosyalari_listele(TARANACAK_KLASORLER)
    print(f"[*] {len(tum_yollar)} dosya bulundu")

    tum_sonuclar = onceki_kayitlari_yukle(TAM_CIKTI) if args.devam else []
    bitenler = {s["Dosya_Yolu"] for s in tum_sonuclar}
    yapilacaklar = [y for y in tum_yollar if y not in bitenler]
    if args.devam:
        print(f"[*] --devam: {len(bitenler)} dosya ara kayittan yuklendi, "
              f"{len(yapilacaklar)} dosya kaldi")

    islenen, atlanan = 0, 0
    baslangic = son_yazdirma = time.monotonic()
    # Ara kayit: her sonuc aninda TAM_CIKTI'ya yazilir ve duzenli flush edilir,
    # boylece kesilen bir tarama --devam ile kaldigi yerden surdurulebilir.
    with open(TAM_CIKTI, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=KOLONLAR)
        yazici.writeheader()
        yazici.writerows(tum_sonuclar)
        try:
            for yol in yapilacaklar:
                sonuc = dosyayi_analiz_et(yol)
                islenen += 1
                if sonuc is None:
                    atlanan += 1
                else:
                    tum_sonuclar.append(sonuc)
                    yazici.writerow(sonuc)
                simdi = time.monotonic()
                if (islenen % ILERLEME_DOSYA_ARALIGI == 0
                        or simdi - son_yazdirma >= ILERLEME_SANIYE_ARALIGI
                        or islenen == len(yapilacaklar)):
                    f.flush()
                    son_yazdirma = simdi
                    print(ilerleme_satiri(islenen, len(yapilacaklar),
                                          islenen - atlanan, atlanan, baslangic))
        except KeyboardInterrupt:
            print(f"\n[!] Durduruldu. {len(tum_sonuclar)} sonuc '{TAM_CIKTI}' dosyasinda; "
                  f"'python toplu_tarama.py --devam' ile kaldigin yerden surdur.")
            sys.exit(1)

    pe_satirlar = [s for s in tum_sonuclar if s["PE_mi"]]
    bulunan_pe_sayisi = len(pe_satirlar)

    # ember_zararli_cikar.py ile ayni mantik: HEDEF_SAYI'dan fazlaysa
    # random.seed(42) ile rastgele orneklem al, sinif dengesini koru.
    if bulunan_pe_sayisi > HEDEF_SAYI:
        random.seed(42)
        pe_satirlar = random.sample(pe_satirlar, HEDEF_SAYI)

    egitim_kolonlari = ["Dosya_Adi", "Boyut_Bayt", "Sifir_Orani",
                         "Ortalama_Entropi", "Toplam_API", "Supheli_API", "Etiket"]
    with open(PE_CIKTI, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=egitim_kolonlari)
        yazici.writeheader()
        for s in pe_satirlar:
            yazici.writerow({k: s[k] for k in egitim_kolonlari})

    print(f"\n[+] Bu calismada {islenen} dosya tarandi ({atlanan} atlandi), "
          f"sure {(time.monotonic() - baslangic) / 60:.1f} dk")
    print(f"[+] {len(tum_sonuclar)} dosya basariyla analiz edildi -> '{TAM_CIKTI}'")
    print(f"[+] Bunlardan {bulunan_pe_sayisi} tanesi gercek PE dosyasi")
    if bulunan_pe_sayisi > HEDEF_SAYI:
        print(f"[+] HEDEF_SAYI={HEDEF_SAYI} icin random.seed(42) ile rastgele secildi "
              f"-> '{PE_CIKTI}' ({len(pe_satirlar)} kayit)")
    else:
        print(f"[+] Tumu -> '{PE_CIKTI}' ({len(pe_satirlar)} kayit, HEDEF_SAYI={HEDEF_SAYI} altinda)")
    print("    (egitimde degil, rf_egit_gercek.py'deki dis dogrulamada kullanilir)")
