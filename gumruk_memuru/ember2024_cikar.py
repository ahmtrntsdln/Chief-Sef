"""
Sef Projesi - EMBER2024 Win32/Win64 zip'lerinden ozellik cikarma (acmadan)
============================================================

ember2024_indir.py'nin indirdigi zip'ler ACILMADAN okunur (acilmis hali ~4.5 kat).
Olcum ember2024_net_cikar.py ile BIREBIR AYNI fonksiyonlardan gelir (Kritik Kural 1):
kayittan_ozellik_cikar (temel + NET_mi/Karma_Mod) + kayittan_dizge_ozellikleri
(thrember string_counts, 80 sutun) + dll_mi; ek olarak Aile, Hafta, Tur.

Kayit bicimi Kritik Kural 5 ile incelendi (Win64_test, 240.000 kayit): alanlar
Dot_Net kayitlariyla ayni; string_counts seyrek (eslesmeyen desen yazilmaz -> 0);
datadirectories basinda isimsiz girdi, 236 kayitta dizin yok (isimle arandigi icin
sorun degil); ordinal "DLL:ordinal5"; is_pe=0 kayitlar atlanir (Kural 3).

Devam: her haftalik JSONL ayri CSV'ye yazilir (once .part, bitince yeniden adlandirilir);
yeniden calistirinca biten haftalar atlanir. Ciktilar proje DISINDA:
  <EMBER2024_KLASORU>\\ozellik\\<zip adi>\\<hafta dosyasi>.csv

Kullanim: python ember2024_cikar.py Win64_test [Win32_test Win64_train Win32_train ...]
"""

import collections
import csv
import json
import os
import sys
import time
import zipfile

from dizge_ozellikleri import DIZGE_SUTUNLARI, kayittan_dizge_ozellikleri
from ember_zararli_cikar import CSV_KOLONLARI, dll_mi, kayittan_ozellik_cikar
from sef_ayarlar import EMBER2024_KLASORU, EMBER2024_ZIP_KLASORU

KOLONLAR = CSV_KOLONLARI + DIZGE_SUTUNLARI + ["DLL_mi", "Aile", "Hafta", "Tur"]
CIKTI_KOK = os.path.join(EMBER2024_KLASORU, "ozellik")


def cikti_klasoru(ad: str) -> str:
    return os.path.join(CIKTI_KOK, ad)


def zip_cikar(ad: str) -> collections.Counter:
    zip_yolu = os.path.join(EMBER2024_ZIP_KLASORU, ad + ".zip")
    if not os.path.exists(zip_yolu):
        sys.exit(f"Hata: '{zip_yolu}' yok (once ember2024_indir.py).")
    hedef = cikti_klasoru(ad)
    os.makedirs(hedef, exist_ok=True)
    sayac = collections.Counter()
    with zipfile.ZipFile(zip_yolu) as z:
        uyeler = sorted((u for u in z.infolist() if u.filename.endswith(".jsonl")), key=lambda u: u.filename)
        toplam_bayt = sum(u.file_size for u in uyeler)
        okunan = 0
        baslangic = son = time.monotonic()
        print(f"[*] {ad}: {len(uyeler)} hafta, acilmis {toplam_bayt / 1e9:.1f} GB")
        for u in uyeler:
            csv_yolu = os.path.join(hedef, os.path.basename(u.filename).replace(".jsonl", ".csv"))
            if os.path.exists(csv_yolu):
                okunan += u.file_size
                sayac["atlanan_hafta (zaten var)"] += 1
                continue
            gecici = csv_yolu + ".part"
            with z.open(u) as girdi, open(gecici, "w", newline="", encoding="utf-8") as f:
                yazici = csv.DictWriter(f, fieldnames=KOLONLAR)
                yazici.writeheader()
                for satir in girdi:
                    okunan += len(satir)
                    kayit = json.loads(satir)
                    if kayit.get("label") not in (0, 1):
                        sayac["etiketsiz"] += 1
                        continue
                    if not kayit["general"]["is_pe"]:
                        sayac["PE degil (is_pe=0)"] += 1
                        continue
                    # Sessiz varsayilan riskini gorunur kil: bu alanlar bossa ozellik 0 olur (gercek olabilir).
                    if not any(b.get("size", 0) > 0 for b in kayit["section"]["sections"]):
                        sayac["olculebilir bolum yok (Ortalama_Entropi=0)"] += 1
                    if not kayit["imports"]:
                        sayac["import yok"] += 1
                    if not kayit["histogram"]:
                        sayac["histogram bos"] += 1
                    ozellik = kayittan_ozellik_cikar(kayit, kayit["label"])
                    ozellik.update(kayittan_dizge_ozellikleri(kayit))
                    ozellik["DLL_mi"] = dll_mi(kayit)
                    ozellik["Aile"] = kayit.get("family") or ""
                    ozellik["Hafta"] = kayit["week_id"]
                    ozellik["Tur"] = kayit["file_type"]
                    yazici.writerow(ozellik)
                    sayac[f"etiket_{kayit['label']}"] += 1
                    simdi = time.monotonic()
                    if simdi - son >= 20:
                        son = simdi
                        oran = okunan / toplam_bayt
                        gecen = simdi - baslangic
                        print(f"  {ad}: %{100 * oran:5.1f} | {sayac['etiket_0'] + sayac['etiket_1']} kayit | "
                              f"gecen {gecen / 60:.1f} dk, kalan ~{gecen / oran * (1 - oran) / 60:.1f} dk")
            os.replace(gecici, csv_yolu)
    print(f"[+] {ad}: {dict(sayac)} ({(time.monotonic() - baslangic) / 60:.1f} dk) -> {hedef}")
    return sayac


if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    if len(sys.argv) < 2:
        sys.exit("Kullanim: python ember2024_cikar.py Win64_test [Win32_test ...]")
    for ad in sys.argv[1:]:
        zip_cikar(ad)
