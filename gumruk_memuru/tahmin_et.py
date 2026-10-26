"""
Sef Projesi - Tek Dosya Tahmini (native EMBER2024 modeli: RF E3, 86 ozellik)
============================================================

Model: sef_ayarlar.NATIVE_MODEL_YOLU (OneDrive disinda, repoda yok), meta veri:
NATIVE_META_YOLU (repoda; ozellik sirasi, tur esikleri, model sha256). Ikisini
sonuclar/3/son_model.py uretir.

Ozellikler ozellik_cikar.dosya_ozellikleri ile cikarilir: dis dogrulamada olculen AYNI kod.
Ayri bir cikarim yazmak raporlanan sayilarin gecmedigi yeni bir olcum olurdu (Kritik Kural 1).
Meta'daki sha256 model dosyasiyla tutmazsa calismaz: baska bir model eski esiklerle
eslesmesin.

Esik: dosya turune gore (EXE / DLL), egitimde kullanilmayan dogrulama diliminde
(hafta 48-51) zararsizlarin %1'i asacak sekilde secildi.

Karar (karar()): .NET disi dosyada esik ustu ZARARLI, alti zararsiz. .NET dosyasinda (NET_mi:
CLR veri dizini ISIMLE, toplu_tarama.net_ozellikleri) esigin alti ASLA "zararsiz" degil, BELIRSIZ:
native model bu grupta zararlilarin onemli bir kismini kaciriyor (olcum sonuclar/5/net_sonuc.md).
.NET EXE'de esik ustu OLASI ZARARLI (o grupta yanlis alarm .NET disi EXE'lerden yuksek), .NET
DLL'de ZARARLI. Skor NaN, sonsuz ya da [0, 1] disindaysa her dosyada BELIRSIZ (fail-closed,
Kritik Kural 7). Olculen oranlar koda GOMULMEZ; kaynaga yonlendirilir.

Kullanim: python tahmin_et.py <dosya_yolu>
Cikis kodu (CIKIS_KODU): 0 temiz (zararsiz), 1 hata (dosya yok, PE degil, model / hash),
2 BELIRSIZ (ek inceleme), 3 ZARARLI, 4 OLASI ZARARLI. Kabuk betigi yalniz 0'i "temiz" saymali.
"""

import hashlib
import json
import math
import os
import sys

import joblib
import pandas as pd
import sklearn

from ozellik_cikar import dosya_ozellikleri
from sef_ayarlar import NATIVE_META_YOLU, NATIVE_MODEL_YOLU


def _sha256(yol):
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def model_yukle():
    for yol in (NATIVE_META_YOLU, NATIVE_MODEL_YOLU):
        if not os.path.exists(yol):
            sys.exit(f"Hata: bulunamadi ({yol}).\n"
                     "Once 'python sonuclar/3/son_model.py' calistir; modeli ve meta veriyi uretir.")
    with open(NATIVE_META_YOLU, encoding="utf-8") as f:
        meta = json.load(f)
    if _sha256(NATIVE_MODEL_YOLU) != meta["model_sha256"]:
        sys.exit("Hata: model dosyasi meta verideki sha256 ile tutmuyor; esikler bu modele ait degil. "
                 "son_model.py'yi yeniden calistir.")
    if meta["surumler"]["scikit-learn"] != sklearn.__version__:
        print(f"[!] Uyari: model scikit-learn {meta['surumler']['scikit-learn']} ile kaydedilmis, "
              f"kurulu {sklearn.__version__}.", file=sys.stderr)
    return {"model": joblib.load(NATIVE_MODEL_YOLU), "meta": meta}


ZARARLI, OLASI_ZARARLI, ZARARSIZ, BELIRSIZ = "ZARARLI", "OLASI ZARARLI", "zararsiz", "BELIRSIZ"
CIKIS_HATA = 1                  # sys.exit("mesaj") ile; Python mesajli cikista 1 dondurur
CIKIS_KODU = {ZARARSIZ: 0, BELIRSIZ: 2, ZARARLI: 3, OLASI_ZARARLI: 4}
NET_OLCUM_KAYNAGI = "README 'Native model' bolumu ve gumruk_memuru/sonuclar/5/net_sonuc.md"


def gecerli_skor(olasilik):
    return math.isfinite(olasilik) and 0.0 <= olasilik <= 1.0


def karar(olasilik, esik, net_mi, esik_turu):
    """Skor -> karar (modul belgesindeki tablo). Aralik disi / NaN / sonsuz skor: BELIRSIZ."""
    if not gecerli_skor(olasilik):
        return BELIRSIZ
    if not net_mi:
        return ZARARLI if olasilik > esik else ZARARSIZ
    if olasilik <= esik:
        return BELIRSIZ
    return OLASI_ZARARLI if esik_turu == "EXE" else ZARARLI


def tahmin(dosya_yolu, paket):
    """Tek dosya: ozellikler + zararli olasiligi + tur esigi + karar. Analiz edilemezse ValueError."""
    ozellik = dosya_ozellikleri(dosya_yolu)
    if ozellik is None:
        raise ValueError("dosya analiz edilemedi (bos, 100 MiB ustu ya da okunamiyor)")
    if not ozellik["PE_mi"]:
        # Model sadece PE ile egitildi (Kritik Kural 3); baska dosyada skor anlamsiz.
        raise ValueError("gecerli bir Windows PE degil; model sadece PE dosyalari icin egitildi")
    X = pd.DataFrame([ozellik])[paket["meta"]["ozellikler"]]
    olasilik = float(paket["model"].predict_proba(X)[0, 1])
    esik_turu = "DLL" if int(float(ozellik["DLL_mi"])) else "EXE"
    esik = paket["meta"]["esikler"][esik_turu]
    k = karar(olasilik, esik, ozellik["Dosya_Turu"] == ".NET", esik_turu)
    return {**ozellik, "olasilik": olasilik, "esik_turu": esik_turu, "esik": esik,
            "zararli_mi": olasilik > esik, "karar": k}


def main(argv):
    """Komut satiri. Donus: CIKIS_KODU[karar]; hatalar sys.exit ile mesajli (kod 1)."""
    if len(argv) != 1:
        sys.exit("Kullanim: python tahmin_et.py <dosya_yolu>")
    dosya_yolu = argv[0]
    if not os.path.isfile(dosya_yolu):
        sys.exit(f"Hata: dosya bulunamadi -> {dosya_yolu}")
    paket = model_yukle()
    try:
        s = tahmin(dosya_yolu, paket)
    except ValueError as e:
        sys.exit(f"Bu dosya icin tahmin yok: {e}.")

    print(f"Dosya: {os.path.basename(dosya_yolu)} | tur: {s['Dosya_Turu']}")
    for ad in ["Boyut_Bayt", "Sifir_Orani", "Ortalama_Entropi", "Toplam_API", "Supheli_API", "DLL_mi",
               "DZ_sayi", "DZ_entropi"]:
        print(f"  {ad:<17}: {s[ad]}")
    print(f"  (+ {len(paket['meta']['ozellikler']) - 8} dizge ozelligi daha; toplam {len(paket['meta']['ozellikler'])})")
    print(f"Zararli olasiligi: %{100 * s['olasilik']:.1f} -> {s['karar']} "
          f"({s['esik_turu']} esigi {s['esik']:.3f}: dogrulamada zararsiz {s['esik_turu']}'lerin %1'i asar)")
    print("  Not: skor EMBER2024'un %50 zararli ornekleminden; gercek ortamda zararli cok daha nadir, "
          "gercek olasilik daha dusuktur.")
    if s["karar"] == BELIRSIZ and s["Dosya_Turu"] == ".NET" and gecerli_skor(s["olasilik"]):
        print("  [!] BELIRSIZ - ek inceleme: .NET dosyasinda esigin altindaki skor 'zararsiz' icin yeterli "
              "kanit degil; native model bu grupta zararlilarin onemli bir kismini kaciriyor "
              f"(olcum: {NET_OLCUM_KAYNAGI}).")
    elif s["karar"] == BELIRSIZ:
        print("  [!] BELIRSIZ - ek inceleme: model skoru gecerli aralikta degil (NaN, sonsuz ya da [0, 1] disi).")
    elif s["karar"] == OLASI_ZARARLI:
        print("  [!] OLASI ZARARLI: .NET EXE'lerde native modelin yanlis alarmi .NET disi EXE'lerden "
              f"yuksek (olcum: {NET_OLCUM_KAYNAGI}).")
    if s["Dosya_Turu"] == ".NET":
        print("  [!] .NET dosyasi: bu skor native modelden. .NET uzman modeli (net_model.py) henuz "
              "tahmin_et'e baglanmadi.")
    return CIKIS_KODU[s["karar"]]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
