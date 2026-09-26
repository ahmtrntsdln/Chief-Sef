"""
Sef Projesi - makineye ozel yollar ve veri dosyasi adlari
============================================================

Neden sef_sabitler.py'den AYRI: oradaki sabitler OLCUMU tanimlar (degisirse
tum veri yeniden uretilmeli); buradakiler sadece dosyalarin NEREDE durdugunu.
Baska bir makineye tasirken sadece bu dosya degisir, hicbir sayi degismez.

Neden tek yerde: ayni CSV'yi yazan ve okuyan scriptler adini ayri ayri
tanimliyordu (ornek: toplu_tarama yaziyor, rf_egit_gercek okuyor); biri
degisince digeri eski dosyayi okumaya devam ederdi. Proje ici yollar bu
klasore gore mutlak: scriptler hangi klasorden calistirilirsa calistirilsin
ayni dosyalari kullanir.
"""

import os

PROJE_KLASORU = os.path.dirname(os.path.abspath(__file__))   # gumruk_memuru/


def _proje(ad: str) -> str:
    return os.path.join(PROJE_KLASORU, ad)


# --- Ham veri: proje (OneDrive) DISINDA, buyuk ---
EMBER2018_KLASORU = r"C:\ember2018\ember2018"     # tar -xf ile acilan gercek klasor
EMBER2018_CIKTI_KLASORU = r"C:\ember2018"         # ember2018_tam_cikar.py'nin buyuk CSV'leri
EMBER2024_KLASORU = r"C:\ember2024"               # Dot_Net_test JSONL + uretilen CSV'ler
EMBER2024_TRAIN_KLASORU = os.path.join(EMBER2024_KLASORU, "train")   # Dot_Net_train JSONL

# --- Yerel dis dogrulama taramasi (toplu_tarama.py) ---
TARANACAK_KLASORLER = [
    r"C:\Windows\System32",
    r"C:\Program Files",
    r"C:\Program Files (x86)",
]

# --- Proje ici veri dosyalari ---
EMBER_ZARARLI_CSV = _proje("sef_dataset_zararli_gercek.csv")        # EMBER 2018 label==1
EMBER_ZARARSIZ_CSV = _proje("sef_dataset_ember_zararsiz.csv")       # EMBER 2018 label==0
TARAMA_ZARARSIZ_CSV = _proje("sef_dataset_zararsiz_gercek.csv")     # dis dogrulama (Dosya_Adi'siz)
TARAMA_ZARARSIZ_ISIMLI_CSV = _proje("sef_dataset_zararsiz_gercek_isimli.csv")   # .gitignore
TUM_TARAMA_CSV = _proje("sef_tarama_tum_dosyalar.csv")              # .gitignore, tam yollar
# dogrulama_yeniden_olc.py: ayni 5700 dosyanin yeni sutunlarla yeniden olcumu.
# Repodaki TARAMA_ZARARSIZ_CSV'nin UZERINE YAZILMAZ; karar sonuca gore verilir.
YENIDEN_OLCUM_CSV = _proje("sef_dataset_zararsiz_gercek_yeniden.csv")                  # Dosya_Adi'siz
YENIDEN_OLCUM_ISIMLI_CSV = _proje("sef_dataset_zararsiz_gercek_yeniden_isimli.csv")    # .gitignore
YENIDEN_OLCUM_ELENEN_CSV = _proje("sef_dogrulama_elenenler_isimli.csv")                # .gitignore
MODEL_YOLU = _proje("model.pkl")                                     # .gitignore, uretilmis
