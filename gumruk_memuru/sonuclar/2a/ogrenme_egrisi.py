"""
Adim 2a - LightGBM ogrenme egrisi: E2 ve E3, 100 bin / 300 bin / 1 milyon / tamami, 5 tohum.

Tanimlar ve ayarlar: ../karar_olcutleri.md (sonuclardan once yazildi). Egitim ilk 52 hafta,
test son 12 hafta (9 Ekim'le ayni), yerel = saklı 5.635 satir. Gecis kosulu yok.

E3 1 milyon KURULAMAZ: egitimde zararli DLL 130.550, hucre basina 250.000 gerekir;
yerine koyarak orneklem yapilmaz -> atlanir ve loga yazilir. E3 "tamami" = 522.200.

Her hucre bitince ogrenme_egrisi.csv'ye bir satir eklenir; yeniden calistirinca biten
hucreler atlanir (--devam varsayilan). Kullanim: python ogrenme_egrisi.py
"""

import os
import sys
import time

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BURASI, ".."))
import ortak_deney as o  # noqa: E402

BOYUTLAR = [100_000, 300_000, 1_000_000, "tamami"]
CEKIRDEK = 8   # sonucu degistirmez (deterministic=True); laptop isinmasin

if __name__ == "__main__":
    sys.stdout.reconfigure(line_buffering=True)
    t0 = time.monotonic()
    egitim, test, yerel = o.veri()
    print(f"[*] egitim {len(egitim)}, test {len(test)}, yerel {len(yerel)} | LightGBM ayar: {o.LGBM_AYAR}")
    hucreler = []
    for aday in o.ADAYLAR:
        ust = o.tamami(egitim, aday)
        for b in BOYUTLAR:
            boyut = ust if b == "tamami" else b
            if boyut > ust:
                print(f"[atlandi] {aday} {b}: yerine koymadan kurulamaz (en buyuk dengeli boyut {ust})")
                continue
            hucreler += [(aday, boyut, tohum) for tohum in o.TOHUMLAR]
    sonuc = o.SonucCSV(os.path.join(BURASI, "ogrenme_egrisi.csv"))
    yapilacak = [h for h in hucreler if f"LGBM_{h[0]}_{h[1]}_{h[2]}" not in sonuc.biten]
    print(f"[*] {len(hucreler)} hucre, {len(hucreler) - len(yapilacak)} zaten bitmis, {len(yapilacak)} kosulacak")
    for i, (aday, boyut, tohum) in enumerate(yapilacak, 1):
        satir = o.hucre_kos("LGBM", aday, boyut, tohum, egitim, test, yerel, CEKIRDEK)
        sonuc.ekle(satir)
        o.ilerleme(i, len(yapilacak), t0, f"| {aday} {boyut} tohum {tohum}: AUC {satir['genel_AUC']}, "
                   f"DLL kacan@1 {satir['DLL_kacan_%@1']}, {satir['sure_sn']} sn")
    print(f"[+] {(time.monotonic() - t0) / 60:.1f} dk")
