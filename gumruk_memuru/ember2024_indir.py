"""
Sef Projesi - EMBER2024 zip'lerini indir (devam ettirilebilir, SHA-256 dogrulamali)
============================================================

Kaynak: https://huggingface.co/datasets/joyce8/EMBER2024 (Apache-2.0).
Dosyalar sef_ayarlar.EMBER2024_ZIP_KLASORU'ne iner ve ACILMAZ; ozellikler
ember2024_cikar.py ile zip'in icinden okunur (acilmis JSONL ~4.5 kat yer tutar).

- Yarim kalan dosya HTTP Range ile kaldigi yerden devam eder (yeniden calistirmak yeter).
- Her dosyanin boyutu ve SHA-256'si Hugging Face API'sinin bildirdigiyle karsilastirilir;
  tutmayan dosya ".bozuk" uzantisiyla kenara alinir, kullanilmaz.
- Ilerleme: yuzde, hiz, kalan sure (satir tamponlu cikti).

Kullanim: python ember2024_indir.py [zip adlari...]
  (varsayilan: Win64_test, Win32_test, Win64_train, Win32_train; kucukten buyuge)
"""

import hashlib
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request

from sef_ayarlar import EMBER2024_ZIP_KLASORU

DEPO = "https://huggingface.co/datasets/joyce8/EMBER2024"
VARSAYILAN = ["Win64_test.zip", "Win32_test.zip", "Win64_train.zip", "Win32_train.zip"]
PARCA = 1024 * 1024
# Ag kesintisi (ornek: universite aginda gecici DNS hatasi "getaddrinfo failed") yeniden denenir;
# indirme Range ile kaldigi bayttan surer. Bekleme her denemede artar (15 sn, 30 sn ... en cok 5 dk).
AG_HATALARI = (urllib.error.URLError, ConnectionError, TimeoutError, http.client.IncompleteRead, http.client.RemoteDisconnected)
DENEME = 12


def yeniden_dene(is_adi: str, fonksiyon, *args):
    for deneme in range(1, DENEME + 1):
        try:
            return fonksiyon(*args)
        except AG_HATALARI as hata:
            if deneme == DENEME:
                raise
            bekle = min(300, 15 * deneme)
            print(f"[!] {is_adi}: ag hatasi ({hata}); {bekle} sn sonra yeniden denenecek ({deneme}/{DENEME - 1})")
            time.sleep(bekle)


def depo_bilgisi() -> dict:
    """Hugging Face API: dosya adi -> (boyut, sha256)."""
    with urllib.request.urlopen(f"https://huggingface.co/api/datasets/joyce8/EMBER2024/tree/main", timeout=60) as yanit:
        liste = json.load(yanit)
    return {o["path"]: (o["lfs"]["size"], o["lfs"]["oid"]) for o in liste if "lfs" in o}


def sha256(yol: str) -> str:
    ozet = hashlib.sha256()
    with open(yol, "rb") as f:
        while blok := f.read(8 * PARCA):
            ozet.update(blok)
    return ozet.hexdigest()


def indir(ad: str, boyut: int, hedef: str) -> None:
    gecici = hedef + ".part"
    mevcut = os.path.getsize(gecici) if os.path.exists(gecici) else 0
    if mevcut > boyut:
        os.remove(gecici)
        mevcut = 0
    istek = urllib.request.Request(f"{DEPO}/resolve/main/{ad}", headers={"Range": f"bytes={mevcut}-"} if mevcut else {})
    with urllib.request.urlopen(istek, timeout=60) as yanit, open(gecici, "ab" if mevcut else "wb") as f:
        if mevcut and yanit.status != 206:
            sys.exit(f"Hata: sunucu devam etmeyi (Range) desteklemedi ({yanit.status}); '{gecici}' silinip yeniden baslatilmali.")
        baslangic, son_yazim, ilk = time.monotonic(), 0.0, mevcut
        while blok := yanit.read(PARCA):
            f.write(blok)
            mevcut += len(blok)
            simdi = time.monotonic()
            if simdi - son_yazim >= 15 or mevcut == boyut:
                son_yazim = simdi
                hiz = (mevcut - ilk) / max(simdi - baslangic, 1e-6)
                kalan = (boyut - mevcut) / hiz if hiz else 0
                print(f"  {ad}: %{100 * mevcut / boyut:5.1f} | {mevcut / 1e9:.2f}/{boyut / 1e9:.2f} GB | "
                      f"{hiz * 8 / 1e6:.0f} Mbit/s | kalan ~{kalan / 60:.0f} dk")
    os.replace(gecici, hedef)


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    adlar = sys.argv[1:] or VARSAYILAN
    os.makedirs(EMBER2024_ZIP_KLASORU, exist_ok=True)
    bilgi = yeniden_dene("depo bilgisi", depo_bilgisi)
    bilinmeyen = [a for a in adlar if a not in bilgi]
    if bilinmeyen:
        sys.exit(f"Depoda yok: {bilinmeyen}")
    toplam = sum(bilgi[a][0] for a in adlar)
    print(f"[*] {len(adlar)} dosya, toplam {toplam / 1e9:.2f} GB -> {EMBER2024_ZIP_KLASORU}")
    for ad in adlar:
        boyut, beklenen = bilgi[ad]
        hedef = os.path.join(EMBER2024_ZIP_KLASORU, ad)
        if os.path.exists(hedef) and os.path.getsize(hedef) == boyut:
            print(f"[=] {ad} zaten var, ozet kontrol ediliyor...")
        else:
            print(f"[>] {ad} ({boyut / 1e9:.2f} GB)")
            yeniden_dene(ad, indir, ad, boyut, hedef)
        bulunan = sha256(hedef)
        if bulunan != beklenen:
            os.replace(hedef, hedef + ".bozuk")
            sys.exit(f"[!] {ad}: SHA-256 tutmadi (beklenen {beklenen[:12]}..., bulunan {bulunan[:12]}...); '.bozuk' olarak ayrildi.")
        print(f"[+] {ad}: boyut ve SHA-256 dogru ({bulunan[:12]}...)")
    print("[+] Tum dosyalar indi ve dogrulandi.")
