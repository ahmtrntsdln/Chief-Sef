"""
Sef Projesi - Faz 1: EMBER'den Gercek Zararli Veri Cikarma
============================================================

Onceki sentetik uretici (random.uniform ile 5 senaryo) yerine, bu script
EMBER veri setinin HAM (vektorlestirilmemis) JSONL kayitlarindan gercek
zararli dosyalarin ozelliklerini cikarir. Ayni KARA_LISTE'yi kullanir,
boylece zararsiz (Chief_1.2.py ile senin 5700 dosyandan cikan) ve zararli
(burada EMBER'den cikan) veriler AYNI olcume gore uretilmis olur.

ON KOSUL (bunlari SEN, kendi bilgisayarinda yapmalisin - ben internete
cikamiyorum, bu yuzden indirmeyi senin icin yapamam):

  1) Indir: https://ember.elastic.co/ember_dataset_2018_2.tar.bz2
     (elastic/ember reposunun resmi indirme linki, ~birkac GB)
  2) Ac:  tar -xjf ember_dataset_2018_2.tar.bz2
     Bu islem train_features_0.jsonl ... train_features_5.jsonl ve
     test_features.jsonl dosyalarini bir klasore cikarir.
  3) Asagidaki EMBER_KLASORU degiskenini o klasorun yoluyla degistir.

Alternatif (daha kolay/hizli): Kaggle'daki temizlenmis tablo hali
  "dhoogla/ember-2018-v2-features" - CSV/parquet olarak hazir, indirip
  bu scripti o formata gore ufak degisiklikle uyarlayabiliriz.
"""

import csv
import glob
import json
import os
import random
import re

EMBER_KLASORU = r"C:\ember2018\ember2018"   # tar -xf ile acilan gercek klasor
HEDEF_SAYI = 5700
CIKTI_DOSYASI = "sef_dataset_zararli_gercek.csv"

# Chief_1.2.py ile BIREBIR AYNI blacklist - iki taraf da ayni olcume gore
# etiketlenmezse, yeni bir sizinti kaynagi yaratmis oluruz.
KARA_LISTE = {
    "VirtualAlloc", "VirtualAllocEx", "WriteProcessMemory",
    "CreateRemoteThread", "SetWindowsHookEx", "IsDebuggerPresent",
}


ORDINAL_DESENI = re.compile(r"^ordinal\d+$")


def kayittan_ozellik_cikar(kayit: dict, etiket: int) -> dict:
    """EMBER'in ham JSON kaydindan, Chief_1.2.py'daki ayni 5 sutunu cikarir."""
    boyut = kayit.get("general", {}).get("size", 0)

    histogram = kayit.get("histogram", [])
    toplam_bayt = sum(histogram) or 1
    sifir_orani = (histogram[0] / toplam_bayt * 100) if histogram else 0.0

    # toplu_tarama.py bos (ham boyutu 0) bolumleri atliyor; ayni olcum icin
    # burada da atlanmali, yoksa 0 entropili bolumler ortalamayi asagi ceker.
    bolumler = kayit.get("section", {}).get("sections", [])
    entropiler = [b.get("entropy", 0.0) for b in bolumler if b.get("size", 0) > 0]
    ortalama_entropi = sum(entropiler) / len(entropiler) if entropiler else 0.0

    # EMBER isimsiz (ordinal) import'lari "ordinal5" gibi yaziyor; pefile
    # tarafi (imp.name None) bunlari saymiyor - ayni olcum icin burada da sayma.
    toplam_api = 0
    supheli_api = 0
    for fonksiyonlar in kayit.get("imports", {}).values():
        isimli = [f for f in fonksiyonlar if not ORDINAL_DESENI.match(f)]
        toplam_api += len(isimli)
        supheli_api += sum(1 for f in isimli if f in KARA_LISTE)

    return {
        "Dosya_Adi": f"ember_{kayit.get('sha256', 'bilinmeyen')[:12]}.exe",
        "Boyut_Bayt": boyut,
        "Sifir_Orani": round(sifir_orani, 2),
        "Ortalama_Entropi": round(ortalama_entropi, 3),
        "Toplam_API": toplam_api,
        "Supheli_API": supheli_api,
        "Etiket": etiket,
    }


def kayitlari_topla(klasor: str, hedef: int, etiket: int):
    """JSONL dosyalarini tarar, label==etiket olan kayitlari toplar
    (1=zararli, 0=zararsiz, -1=etiketsiz)."""
    jsonl_dosyalari = sorted(glob.glob(os.path.join(klasor, "*.jsonl")))
    if not jsonl_dosyalari:
        raise FileNotFoundError(
            f"'{klasor}' icinde .jsonl dosyasi bulunamadi. "
            "Once EMBER arsivini indirip actigina emin ol (yukaridaki ON KOSUL)."
        )

    havuz = []
    havuz_hedefi = hedef * 3  # biraz fazla toplayip sonra rastgele sececegiz

    for dosya in jsonl_dosyalari:
        with open(dosya, "r", encoding="utf-8") as f:
            for satir in f:
                kayit = json.loads(satir)
                if kayit.get("label") == etiket:
                    havuz.append(kayittan_ozellik_cikar(kayit, etiket))
                    if len(havuz) >= havuz_hedefi:
                        break
        if len(havuz) >= havuz_hedefi:
            break

    if len(havuz) < hedef:
        print(f"[!] Uyari: sadece {len(havuz)} kayit (label={etiket}) bulundu, "
              f"{hedef} istenmisti.")
        return havuz

    random.seed(42)
    return random.sample(havuz, hedef)


def csv_yaz(kayitlar, yol: str):
    with open(yol, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=[
            "Dosya_Adi", "Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
            "Toplam_API", "Supheli_API", "Etiket",
        ])
        yazici.writeheader()
        yazici.writerows(kayitlar)


if __name__ == "__main__":
    secilenler = kayitlari_topla(EMBER_KLASORU, HEDEF_SAYI, etiket=1)
    csv_yaz(secilenler, CIKTI_DOSYASI)
    print(f"[+] {len(secilenler)} gercek zararli kayit '{CIKTI_DOSYASI}' dosyasina yazildi.")
