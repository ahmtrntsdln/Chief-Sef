# İş 2(b) sonucu: M2d'nin gerçek akıştaki .NET alt kümesinde (A kümesi) performansı (3 Kasım 2026)

Ön kayıt `is2b_on_kayit.md` (commit `b031e88`, revizyon 1 `75e5216`; ölçümden önce). Betik
`is2b_a_kumesi.py`, çıktı `is2b_a_kumesi.log`, `is2b_a_kumesi.csv`, `is2b_hukum.csv`. Gerçek veriyle bir
kez koşuldu. Betik önce yalnız sentetik veriyle denendi (gerçek veri ve model okunmadan); o denemeden
sonra tek değişiklik boş aile adının "(bilinmiyor)" yazılması oldu. Uzman bağlanmadı; `tahmin_et.py`
değişmedi.

**Özet:** M2d'nin Dot_Net_test'te görülen üstünlüğü A kümesine taşınmadı. Hüküm verilebilen iki EXE
hücresinden birinde (H %0,45) M2d anlamlı olarak daha çok kaçırıyor, diğerinde (H %1,05) fark
gösterilemedi. DLL'de hüküm yok. M2d'nin kaçanı A'da, dört hücrenin hepsinde, Dot_Net_test'tekinin
1,81-3,61 katı.

## Geçitler: hepsi TUTTU

| # | Sonuç |
|---|---|
| K1 | çiftli A .NET 4.848 (208 / 1.054 / 3.278 / 308); kopya dağılımı 2 kopya 2.398 sha, 4 kopya 13 sha; kopyalar arasında farklı etiket ya da sütun 0; tekil 2.411 (101 / 517 / 1.639 / 154); hafta 52-63; 87 sütun tam, eksik değer yok |
| K2 | M2d (4 × 24.104): eşikler 0,86 / 0,69 ve 0,76 / 0,59; Dot_Net_test 6 satır `uzman_native.csv` ile birebir |
| K3 | native: eşikler 0,83 / 0,69 ve 0,79 / 0,60; Dot_Net_test 6 satır birebir; çiftli A üretim eşiğinde EXE kaçan 1.106/3.278, YA 6/208; DLL kaçan 72/308, YA 10/1.054 = `net_olcum.csv` |
| K4 | tekil A × Dot_Net_train ortak eşsiz sha 0; dosya çıkarılmadı |
| K5 | Dot_Net_test tekil 59.953; aynı sha'da farklı etiket 0 |

Ön kayıttaki saf .NET / karma mod hücre sayıları da beklenenle aynı çıktı. Ek denetim: her McNemar
hücresinde b − c, kaçan sayılarının farkına eşit (204, 29, 36, 10).

## Tablo (tekil A, 2.411 eşsiz dosya; Wilson %95)

| H | Tür | Eşik M2d / native | M2d kaçan | native kaçan | M2d YA | native YA |
|---|---|---|---|---|---|---|
| %0,45 | EXE | 0,86 / 0,83 | %61,62 [59,24-63,95] (1.010/1.639) | %49,18 [46,76-51,60] (806/1.639) | %0,00 [0,00-3,66] (0/101) | %0,99 [0,17-5,40] (1/101) |
| | DLL | 0,69 / 0,69 | %44,81 [37,17-52,69] (69/154) | %25,97 [19,69-33,42] (40/154) | %0,39 [0,11-1,40] (2/517) | %0,97 [0,41-2,24] (5/517) |
| | hepsi | | %60,18 [57,89-62,42] (1.079/1.793) | %47,18 [44,88-49,50] (846/1.793) | %0,32 [0,09-1,17] (2/618) | %0,97 [0,45-2,10] (6/618) |
| %1,05 | EXE | 0,76 / 0,79 | %46,61 [44,21-49,03] (764/1.639) | %44,42 [42,03-46,83] (728/1.639) | %2,97 [1,02-8,37] (3/101) | %0,99 [0,17-5,40] (1/101) |
| | DLL | 0,59 / 0,60 | %29,22 [22,61-36,84] (45/154) | %22,73 [16,82-29,96] (35/154) | %1,35 [0,66-2,77] (7/517) | %0,97 [0,41-2,24] (5/517) |
| | hepsi | | %45,12 [42,83-47,43] (809/1.793) | %42,55 [40,28-44,86] (763/1.793) | %1,62 [0,88-2,95] (10/618) | %0,97 [0,45-2,10] (6/618) |

AUC (betimleyici; eşiksiz, H'ye bağlı değil): M2d EXE 0,9063 / DLL 0,9455 / hepsi 0,9450; native EXE
0,9635 / DLL 0,9799 / hepsi 0,9792.

Tekil Dot_Net_test, aynı eşikler (eşit YA koşulu E1 ve kural 3 için):

| H | Tür | M2d kaçan | native kaçan | M2d YA | native YA |
|---|---|---|---|---|---|
| %0,45 | EXE | %34,07 [33,51-34,63] | %72,58 [72,05-73,11] | %0,40 [0,24-0,67] (15/3.713) | %0,38 [0,22-0,63] (14/3.713) |
| | DLL | %12,40 [11,19-13,71] | %89,54 [88,32-90,66] | %0,79 [0,69-0,90] (206/26.240) | %0,42 [0,35-0,51] (111/26.240) |
| %1,05 | EXE | %23,46 [22,96-23,96] | %62,80 [62,23-63,37] | %1,21 [0,91-1,62] (45/3.713) | %0,89 [0,63-1,25] (33/3.713) |
| | DLL | %8,56 [7,55-9,69] | %86,08 [84,71-87,35] | %1,13 [1,01-1,26] (296/26.240) | %0,77 [0,67-0,89] (203/26.240) |

## Ön kayıtlı kurallara göre

**Kural 1, M2d − native kaçan** (b = yalnız M2d kaçırdı, c = yalnız native kaçırdı):

| H | Tür | E1 (Dot_Net_test) | E2 (A) | b | c | p | Hüküm |
|---|---|---|---|---|---|---|---|
| %0,45 | EXE | tuttu | tuttu | 346 | 142 | 1,07e-20 | **M2d A kümesinde native'den anlamlı olarak daha çok kaçırıyor** |
| %0,45 | DLL | TUTMADI | tuttu | 38 | 9 | (2,49e-05) | hüküm yok: eşit yanlış alarm sağlanamadı (E1) |
| %1,05 | EXE | tuttu | tuttu | 262 | 226 | 0,113 | fark gösterilemedi |
| %1,05 | DLL | TUTMADI | tuttu | 29 | 19 | (0,193) | hüküm yok: eşit yanlış alarm sağlanamadı (E1) |

Parantezli p'ler kural gereği karar sayılmaz. "Fark gösterilemedi" eşit demek değildir. E2 küçük n ile
zayıf bir koşuldur (ön kayıt): H %1,05 EXE'de M2d'nin A'daki YA'sı %2,97 (3/101), native'in %0,99 (1/101);
aralıklar örtüştüğü için koşul tuttu, ama bu iki yanlış alarm oranının eşit olduğunu göstermez.

**Kural 2, M2d YA mutlak (A):**

| H | Tür | YA | Hüküm |
|---|---|---|---|
| %0,45 | EXE | 0/101 | hüküm yok: çözünürlük yetersiz (üst %3,66 ≥ H) |
| %0,45 | DLL | 2/517 | hüküm yok: çözünürlük yetersiz (üst %0,74 ≥ H) |
| %1,05 | EXE | 3/101 | hüküm yok: çözünürlük yetersiz (üst %3,66 ≥ H) |
| %1,05 | DLL | %1,35 [0,66-2,77] (7/517) | hedefle farkı gösterilemedi |

**Kural 3, aktarım:** M2d'nin kaçanı A'da Dot_Net_test'ten dört hücrenin hepsinde anlamlı olarak farklı
(**yüksek**): H %0,45 EXE 61,62 vs 34,07, DLL 44,81 vs 12,40; H %1,05 EXE 46,61 vs 23,46, DLL 29,22 vs 8,56.

**Kural 5:** sonuç ne olursa olsun uzman bağlanmaz; `tahmin_et.py` .NET kuralı değişmez.

## Betimleyici (hüküm üretmez)

**Native üretim eşikleri (0,70 / 0,61), tekil A:** EXE kaçan %33,74 [31,49-36,06] (553/1.639), YA %2,97
[1,02-8,37] (3/101); DLL kaçan %23,38 [17,39-30,66] (36/154), YA %0,97 [0,41-2,24] (5/517). Kaçan
oranları `sonuclar/5/net_sonuc.md`'deki çiftli değerlerle aynı. YA'lar 4 kopyalı sha'lar yüzünden biraz
farklı (EXE 6/208 = %2,88 → 3/101 = %2,97; DLL 10/1.054 = %0,95 → 5/517 = %0,97). Aralıklar genişledi.

**Saf .NET / karma mod.** Katmanlar arası fark "anlamlı" diye yazılmaz:

| Katman | H | Tür | M2d kaçan | native kaçan | M2d YA | native YA |
|---|---|---|---|---|---|---|
| saf .NET | %0,45 | EXE | %60,58 (959/1.583) | %47,76 (756/1.583) | 0/48 | 1/48 |
| | | DLL | %40,71 (57/140) | %27,14 (38/140) | 2/222 | 5/222 |
| | %1,05 | EXE | %45,42 (719/1.583) | %42,89 (679/1.583) | 3/48 | 1/48 |
| | | DLL | %25,00 (35/140) | %23,57 (33/140) | 2/222 | 5/222 |
| karma mod | %0,45 | EXE | %91,07 (51/56) | %89,29 (50/56) | 0/53 | 0/53 |
| | | DLL | 12/14 (n<30) | 2/14 (n<30) | 0/295 | 0/295 |
| | %1,05 | EXE | %80,36 (45/56) | %87,50 (49/56) | 0/53 | 0/53 |
| | | DLL | 10/14 (n<30) | 2/14 (n<30) | 5/295 | 0/295 |

Wilson aralıkları `is2b_a_kumesi.log` ve `.csv`'de. Zararlı EXE'lerin %96,6'sı (1.583/1.639) saf .NET:
H %0,45 EXE'deki 204 dosyalık kaçan farkının 203'ü saf .NET katmanında. Ön kayıttaki "M2d karma modu
eğitimde neredeyse görmedi" asimetrisi bu EXE farkını sayıca açıklayamaz. Nedeni ölçülmedi. Karma mod
DLL'lerde H %0,45'te 12/14'e karşı 2/14 var, ama n = 14 ve oran yorumlanmaz.

**Aileler (tekil A zararlıları, H %1,05):**

| Aile | n | M2d kaçan | native kaçan |
|---|---|---|---|
| (bilinmiyor) | 662 | %55,74 [51,93-59,48] | %40,33 [36,66-44,11] |
| wacatac | 226 | %35,40 [29,46-41,83] | %42,48 [36,21-49,00] |
| asyncrat | 78 | %33,33 [23,87-44,36] | %41,03 [30,78-52,11] |
| heracles | 64 | %34,38 [23,92-46,60] | %26,56 [17,30-38,48] |
| redline | 60 | %11,67 [5,77-22,18] | %45,00 [33,09-57,51] |
| njrat | 43 | %44,19 [30,43-58,89] | %44,19 [30,43-58,89] |
| jalapeno | 41 | %9,76 [3,86-22,55] | %21,95 [12,00-36,71] |
| xworm | 36 | %27,78 [15,85-43,99] | %27,78 [15,85-43,99] |
| puwaders | 30 | %16,67 [7,34-33,56] | %33,33 [19,23-51,22] |
| agenttesla | 25 | 17/25 (n<30) | 16/25 (n<30) |

Üstünlük aileye göre değişiyor. "(bilinmiyor)" homojen bir aile değil; bu tablo "M2d X'e karşı zayıf"
sonucu vermez.

## Sınırlar (ön kayıttaki gibi)

- **Eşik popülasyonu ≠ A:** eşikler Dot_Net doğrulama diliminden; A'daki YA kayması bunu ölçer. Eşikler A
  için seçilmediğinden bu tablo, modellerin A için ayarlanmış halini göstermez.
- **Yapısal asimetri:** native bu popülasyonu eğitimde gördü, M2d görmedi. Bu ölçüm iki modelin mimari
  olarak hangisinin üstün olduğunu değil, mevcut hallerinin A'daki davranışını gösterir.
- **Küçük zararsız n:** EXE 101, DLL 517; YA aralıkları geniş, E2 zayıf.
- **Kümelilik:** haftalık kota ve aileler nedeniyle gerçek belirsizlik aralıklardan geniş olabilir.
- **Çiftli eğitim havuzu:** M2d tarifi çiftli havuzla tanımlı; etkisi burada ölçülmedi.
- **A'nın temsil gücü:** A, EMBER2024'ün kotalı Win32/Win64 örneklemindeki .NET dosyalarıdır; "gerçek
  akış" terimi bu kümeyi adlandırır, sahadaki .NET dağılımının ölçüldüğü anlamına gelmez.

## Sonraki adım

İş 2(c) (tam eşit yanlış alarmda ROC tabanlı M2d - native tanısı, EXE / DLL ayrı) ayrı ön kayıtla. Uzmanın
bağlanıp bağlanmayacağı kararı (a)(b)(c)'den sonra kullanıcınındır.
