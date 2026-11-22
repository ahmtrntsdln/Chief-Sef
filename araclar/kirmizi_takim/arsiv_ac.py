"""sef-toplu icin tar acici: /opt/sef/arsiv_ac.py olarak kurulur.

Kullanim: python -I -B arsiv_ac.py <arsiv> <hedef_klasor> <acik_boyut_siniri_bayt>

Kural: arsiv YA TAMAMEN acilir YA HIC acilmaz. Once butun uyeler tarfile'in 'data'
suzgecinden (PEP 706) gecirilir: '..' ile hedef disina cikan yol, mutlak ya da hedef disina
isaret eden sembolik/sabit baglanti, aygit/FIFO dosyasi reddedilir. Mutlak DOSYA yolu
reddedilmez: suzgec bastaki '/'yi kirpar, dosya hedefin icine yazilir (belgelenmis davranis). Tek bir uye reddedilirse
hicbir sey yazilmadan cikis 64. Normal dosyalarin toplam boyutu sinirdan buyukse de 64.
Sonra acma yine filter='data' ile yapilir (denetim ile acma arasinda kural farki yok).

Cikis: 0 acildi; 64 reddedildi (stderr'de 'ARŞİV REDDEDİLDİ: <neden>');
beklenmeyen hata (disk dolu vb.) Python'un kendi hatasi, 1.
"""
import os
import sys
import tarfile

REDDEDILDI = 64


def reddet(neden):
    print(f"sef-toplu: ARŞİV REDDEDİLDİ: {neden}", file=sys.stderr)
    sys.exit(REDDEDILDI)


def main(argv):
    if len(argv) != 3:
        sys.exit("Kullanim: arsiv_ac.py <arsiv> <hedef_klasor> <acik_boyut_siniri_bayt>")
    arsiv, hedef, sinir = argv[0], argv[1], int(argv[2])
    hedef = os.path.realpath(hedef)
    try:
        with tarfile.open(arsiv, "r:*") as tar:
            uyeler = tar.getmembers()
            toplam = 0
            for uye in uyeler:
                try:
                    tarfile.data_filter(uye, hedef)
                except tarfile.FilterError as e:
                    reddet(f"{type(e).__name__}: {e}")
                if uye.isfile():
                    toplam += uye.size
            if toplam > sinir:
                reddet(f"acik boyut {toplam} bayt > sinir {sinir} bayt")
            tar.extractall(hedef, members=uyeler, filter="data")
    except tarfile.TarError as e:
        reddet(f"gecerli bir tar arsivi degil ya da okunamadi ({type(e).__name__}: {e})")
    print(f"sef-toplu: arsiv acildi: {len(uyeler)} uye, {toplam} bayt", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
