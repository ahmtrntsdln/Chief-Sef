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

EMBER_KLASORU = r"C:\ember2018\ember2018"   # tar -xf ile acilan gercek klasor
HEDEF_SAYI = 5700
CIKTI_DOSYASI = "sef_dataset_zararli_gercek.csv"

# Chief_1.2.py ile BIREBIR AYNI blacklist - iki taraf da ayni olcume gore
# etiketlenmezse, yeni bir sizinti kaynagi yaratmis oluruz.
KARA_LISTE = {
    "VirtualAlloc", "VirtualAllocEx", "WriteProcessMemory",
    "CreateRemoteThread", "SetWindowsHookEx", "IsDebuggerPresent",
}


def kayittan_ozellik_cikar(kayit: dict) -> dict:
    """EMBER'in ham JSON kaydindan, Chief_1.2.py'daki ayni 5 sutunu cikarir."""
    boyut = kayit.get("general", {}).get("size", 0)

    histogram = kayit.get("histogram", [])
    toplam_bayt = sum(histogram) or 1
    sifir_orani = (histogram[0] / toplam_bayt * 100) if histogram else 0.0

    # Chief_1.2.py bolum-bazli entropi hesapliyordu; EMBER da her PE
    # bolumunun entropisini hazir veriyor - ayni mantigin ortalamasini aliyoruz.
    bolumler = kayit.get("section", {}).get("sections", [])
    entropiler = [b.get("entropy", 0.0) for b in bolumler]
    ortalama_entropi = sum(entropiler) / len(entropiler) if entropiler else 0.0

    toplam_api = 0
    supheli_api = 0
    for fonksiyonlar in kayit.get("imports", {}).values():
        toplam_api += len(fonksiyonlar)
        supheli_api += sum(1 for f in fonksiyonlar if f in KARA_LISTE)

    return {
        "Dosya_Adi": f"ember_{kayit.get('sha256', 'bilinmeyen')[:12]}.exe",
        "Boyut_Bayt": boyut,
        "Sifir_Orani": round(sifir_orani, 2),
        "Ortalama_Entropi": round(ortalama_entropi, 3),
        "Toplam_API": toplam_api,
        "Supheli_API": supheli_api,
        "Etiket": 1,
    }


def zararlilari_topla(klasor: str, hedef: int):
    """JSONL dosyalarini tarar, label==1 (zararli) kayitlari toplar."""
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
                if kayit.get("label") == 1:  # 1=zararli, 0=zararsiz, -1=etiketsiz
                    havuz.append(kayittan_ozellik_cikar(kayit))
                    if len(havuz) >= havuz_hedefi:
                        break
        if len(havuz) >= havuz_hedefi:
            break

    if len(havuz) < hedef:
        print(f"[!] Uyari: sadece {len(havuz)} zararli kayit bulundu, {hedef} istenmisti.")
        return havuz

    random.seed(42)
    return random.sample(havuz, hedef)


if __name__ == "__main__":
    secilenler = zararlilari_topla(EMBER_KLASORU, HEDEF_SAYI)

    with open(CIKTI_DOSYASI, "w", newline="", encoding="utf-8") as f:
        yazici = csv.DictWriter(f, fieldnames=[
            "Dosya_Adi", "Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi",
            "Toplam_API", "Supheli_API", "Etiket",
        ])
        yazici.writeheader()
        yazici.writerows(secilenler)

    print(f"[+] {len(secilenler)} gercek zararli kayit '{CIKTI_DOSYASI}' dosyasina yazildi.")
