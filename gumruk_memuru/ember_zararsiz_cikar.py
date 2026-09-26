"""
Sef Projesi - Faz 1: EMBER'den Gercek Zararsiz Veri Cikarma

ember_zararli_cikar.py ile AYNI olcum fonksiyonlarini kullanir, sadece
label==0 (zararsiz) kayitlari toplar. Egitimin iki sinifi da ayni kaynaktan
(EMBER) gelirse model "System32'ye mi ait?" gibi kaynak-kokenli bir sinyal
ogrenemez; kendi taramamiz (toplu_tarama.py) sadece dis dogrulama icin kalir.
"""

from ember_zararli_cikar import EMBER_KLASORU, HEDEF_SAYI, csv_yaz, kayitlari_topla
from sef_ayarlar import EMBER_ZARARSIZ_CSV as CIKTI_DOSYASI

if __name__ == "__main__":
    secilenler = kayitlari_topla(EMBER_KLASORU, HEDEF_SAYI, etiket=0)
    csv_yaz(secilenler, CIKTI_DOSYASI)
    print(f"[+] {len(secilenler)} gercek zararsiz kayit '{CIKTI_DOSYASI}' dosyasina yazildi.")
