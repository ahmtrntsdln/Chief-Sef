"""
Sef Projesi - Faz 1: Konseptin Ispati
Gumruk Memuru - Entropi Hesaplayici

Bu modul bir dosyanin "Shannon Entropisi"ni hesaplar.
Entropi, verinin ne kadar rastgele / ongorulemez oldugunun olcusudur (0-8 bit/byte araligi).

  - Dusuk entropi  -> duz metin, kaynak kodu gibi ongorulebilir veri
  - Yuksek entropi -> sifrelenmis veya sikistirilmis (paketlenmis) veri

Formul (Claude Shannon, 1948):
    H(X) = - sum( p(x) * log2(p(x)) )   [her olasi byte degeri x icin]

Bu fark, Gumruk Memuru'nun bir dosyayi hic calistirmadan once
"supheli" olarak isaretlemesinin ilk ve en basit yoludur.
"""

import math
from collections import Counter


def shannon_entropy(data: bytes) -> float:
    """Bayt dizisinin Shannon entropisini (bit/byte) dondurur."""
    if not data:
        return 0.0

    sayimlar = Counter(data)
    toplam = len(data)

    entropi = 0.0
    for adet in sayimlar.values():
        olasilik = adet / toplam
        entropi -= olasilik * math.log2(olasilik)

    return entropi


def dosya_entropisi(dosya_yolu: str) -> float:
    """Dosyayi okuyup entropisini hesaplar."""
    with open(dosya_yolu, "rb") as f:
        return shannon_entropy(f.read())


if __name__ == "__main__":
    import os
    import random
    import zipfile

    print("=== Gumruk Memuru: Ilk Entropi Testi ===\n")

    # 1) Duz metin - tahmin edilebilir, dusuk entropi beklenir
    with open("test_metin.txt", "w") as f:
        f.write("Merhaba dunya, bu Sef projesinin ilk satirlari. " * 100)

    # 2) Tamamen rastgele bayt - sifreli/paketlenmis dosya simulasyonu
    with open("test_rastgele.bin", "wb") as f:
        f.write(bytes(random.getrandbits(8) for _ in range(8000)))

    # 3) Zip - gercekten sikistirilmis dosya
    with zipfile.ZipFile("test_zip.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("icerik.txt", "Merhaba dunya, bu Sef projesinin ilk satirlari. " * 100)

    testler = [
        ("Duz metin      (.txt)", "test_metin.txt"),
        ("Rastgele bayt  (.bin)", "test_rastgele.bin"),
        ("Sikistirilmis  (.zip)", "test_zip.zip"),
    ]

    for isim, yol in testler:
        e = dosya_entropisi(yol)
        bar = "#" * int(e * 5)
        print(f"{isim} -> {e:.3f} bit/byte  {bar}")
        os.remove(yol)
