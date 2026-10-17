"""
Adim 4 - Yerel 5.635'lik dogrulama setini AYRI, dondurulmus dosya yap; kimligini belgele.

Kaynak: DOGRULAMA_DZ80_CSV (9 Ekim olcumu; Adim 2-3'teki tum yerel olculer bu icerikten).
Hedef : YEREL_DOGRULAMA_5635_CSV - bayt bayt ayni kopya, .gitignore'da (repoya GIRMEZ).
Kontrol (once): Dosya_Adi / Dosya_Yolu / Sira sutunu yok; HER hucre sayi (yol, kullanici,
makine adi metin olarak bulunamaz); satir 5.635. Sonra sha256 ve satir sayisi
sonuclar/4/yerel_set.md'ye ve model_native_meta.json'a yazilir.
Kullanim: python yerel_set.py
"""

import csv
import getpass
import hashlib
import json
import os
import platform
import shutil
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")))
from sef_ayarlar import DOGRULAMA_DZ80_CSV, NATIVE_META_YOLU, YEREL_DOGRULAMA_5635_CSV  # noqa: E402

BEKLENEN_SATIR = 5635


def sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


if __name__ == "__main__":
    with open(DOGRULAMA_DZ80_CSV, encoding="utf-8") as f:
        okuyucu = csv.reader(f)
        baslik = next(okuyucu)
        satirlar = list(okuyucu)
    yasak = {"Dosya_Adi", "Dosya_Yolu", "Sira"} & set(baslik)
    if yasak:
        sys.exit(f"DUR: kimlik sutunu var: {yasak}")
    sayi_degil = []
    for i, s in enumerate(satirlar):
        for k, v in zip(baslik, s):
            try:
                float(v)
            except ValueError:
                sayi_degil.append((i, k, v[:20]))
    if sayi_degil:
        sys.exit(f"DUR: sayi olmayan hucre var (ilk 3): {sayi_degil[:3]}")
    metin = open(DOGRULAMA_DZ80_CSV, encoding="utf-8").read()
    for iz in {getpass.getuser(), platform.node(), os.environ.get("USERNAME", ""), os.environ.get("COMPUTERNAME", "")} - {""}:
        if iz.lower() in metin.lower():
            sys.exit("DUR: kullanici/makine adi metinde geciyor")
    if len(satirlar) != BEKLENEN_SATIR:
        sys.exit(f"DUR: {len(satirlar)} satir, {BEKLENEN_SATIR} bekleniyordu")

    shutil.copyfile(DOGRULAMA_DZ80_CSV, YEREL_DOGRULAMA_5635_CSV)
    ozet = sha256(YEREL_DOGRULAMA_5635_CSV)
    if ozet != sha256(DOGRULAMA_DZ80_CSV):
        sys.exit("DUR: kopya kaynakla bayt bayt ayni degil")
    exe = sum(1 for s in satirlar if float(s[baslik.index("DLL_mi")]) == 0)
    net = sum(1 for s in satirlar if float(s[baslik.index("NET_mi")]) == 1)
    kimlik = {"dosya": os.path.basename(YEREL_DOGRULAMA_5635_CSV), "satir": len(satirlar), "sutun": len(baslik),
              "sha256": ozet, "EXE": exe, "DLL": len(satirlar) - exe, ".NET": net,
              "kaynak": "dogrulama_dizge80.py, 9 Ekim 2026 olcumu (DOGRULAMA_DZ80_CSV'nin bayt bayt kopyasi)",
              "repoda": False}

    with open(NATIVE_META_YOLU, encoding="utf-8") as f:
        meta = json.load(f)
    meta["yerel_dogrulama_seti"] = kimlik
    with open(NATIVE_META_YOLU, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    md = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yerel_set.md")
    with open(md, "w", encoding="utf-8") as f:
        f.write("# Yerel doğrulama seti (5.635) - kimlik\n\n"
                "Native model ölçümlerinin (Adım 2-3: yerel yanlış alarm, McNemar, uçtan uca test) "
                "dayandığı yerel zararsız set. REPODA YOK (`.gitignore`): kurulu yazılımların özellik "
                "vektörleri; dosya adı ve yol İÇERMEZ (her hücre sayı, kontrol edildi).\n\n"
                f"| Alan | Değer |\n|---|---|\n" + "".join(f"| {k} | {v} |\n" for k, v in kimlik.items()) +
                "\nKopya, 9 Ekim ölçümünün dondurulmuş halidir; `dogrulama_dizge80.py` yeniden çalışırsa "
                "`sef_dogrulama_dz80.csv` değişebilir, bu dosya değişmez. SHA-256 tutmuyorsa raporlanan "
                "yerel sayılar o dosyaya ait değildir.\n")
    print(json.dumps(kimlik, ensure_ascii=False, indent=1))
