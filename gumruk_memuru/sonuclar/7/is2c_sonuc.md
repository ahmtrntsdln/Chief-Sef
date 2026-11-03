# İş 2(c) sonucu: Eşit yanlış alarmda M2d ile native (3 Kasım 2026)

Ön kayıt `is2c_on_kayit.md` (commit `4c21a5b`, revizyon 1 `eea4c8d`; ölçümden önce). Betik `is2c_esit_ya.py`,
çıktı `is2c_esit_ya.log`, `is2c_esit_ya.csv`, `is2c_hukum.csv`. Gerçek veriyle bir kez koşuldu. Betik önce yalnız
sentetik veriyle denendi (elle hesaplı ROC değerleri, karar kuralı dalları; aynı dağılımdan iki modelle %95
aralığı sıfırı 40 tekrarın 40'ında kapsadı, tekrar az olduğu için kaba bir kontrol). Uzman bağlanmadı;
`tahmin_et.py` değişmedi.

**Karar (kural 3-5): hiçbir tür bağlanmaya aday değil. Varsayılan karar geçerli: uzman Faz 1 kapsamı dışında,
native tek model.** Bu "native daha iyi" hükmü DEĞİLDİR. Sınanabilen tek hücrede (A, DLL, %1,05) aralık çok geniş
ve sıfırı içeriyor; EXE A'da hiç sınanamadı. Dot_Net_test'te ise M2d çok daha az kaçırıyor; iki küme çelişiyor ve
nedeni ölçülmedi.

## Geçitler: hepsi TUTTU

| # | Sonuç |
|---|---|
| K1 | çiftli A 4.848, tekil 2.411 (101 / 517 / 1.639 / 154); çelişkili sha 0; hafta 52-63 |
| K2, K3 | M2d (4 × 24.104) ve native eşikleri, Dot_Net_test 12 satır `uzman_native.csv` ile birebir; çiftli A üretim eşiği `net_olcum` değerleriyle birebir |
| K4, K5 | tekil A × Dot_Net_train ortak sha 0; Dot_Net_test tekil 59.953, aynı sha'da farklı etiket 0 |
| K6 | tekil A ve tekil Dot_Net_test, 2(b)'nin sabit eşikleri: 24 satır (k/n, AUC) `is2b_a_kumesi.csv` ile birebir |
| K7 | ROC AUC = `roc_auc_score` (1e-12, 6 hücre × 2 model); modelin kendisiyle eşlenik fark her yeniden örneklemde 0; aynı tohum aynı sonuç |

## Birincil: eşit YA'da kaçan

Δ = M2d − native, yüzde puan; negatif = M2d daha az kaçırıyor. Eşlenik bootstrap, eşsiz dosya, B = 10.000, %95.
Eşit YA her modelde aynı kümede FPR = H noktasıdır: bir ROC noktası, üretim eşiği değil (Kural 6). Aralık
örtüşmesi kuralı kullanılmadı.

| Küme | Tür | H | n·H | M2d | Native | Δ [%95] | Hüküm |
|---|---|---|---|---|---|---|---|
| Dot_Net_test | EXE | %0,45 | 16,71 | %33,59 | %70,26 | −36,66 [−42,00, −29,79] | M2d daha az kaçırıyor |
| Dot_Net_test | EXE | %1,05 | 38,99 | %25,89 | %60,36 | −34,47 [−39,19, −31,21] | M2d daha az kaçırıyor |
| Dot_Net_test | DLL | %0,45 | 118,08 | %21,61 | %89,22 | −67,61 [−71,42, −65,23] | M2d daha az kaçırıyor |
| Dot_Net_test | DLL | %1,05 | 275,52 | %9,04 | %84,13 | −75,09 [−76,98, −72,98] | M2d daha az kaçırıyor |
| A | EXE | %0,45 | 0,45 | | | | hüküm yok: asgari örnek altında |
| A | EXE | %1,05 | 1,06 | | | | hüküm yok: asgari örnek altında |
| A | DLL | %0,45 | 2,33 | | | | hüküm yok: asgari örnek altında |
| A | DLL | %1,05 | 5,43 | %31,82 | %22,17 | +9,65 [−63,03, +22,02] | fark gösterilemedi |

Asgari örnek altındaki A hücrelerinin sayıları `.csv`'de işaretli; yorumlanmaz, karara girmez. TOST koşulu
(%90 aralığı ±2 puan içinde) hiçbir hücrede sağlanmadı; A DLL %1,05 için %90 aralık [−60,63, +19,57]: bu hücre
"eşdeğer" diye OKUNMAZ.

**Aday dökümü:** EXE: A'da hüküm alan hücre yok, aday olamaz (ön kayıtta önceden yazılı). DLL: tek ortak hücre
(%1,05) A'da sıfırı dışlamadı. Engel ("native daha az kaçırıyor") hiçbir hüküm alan hücrede yok.

**A DLL %1,05'in aralığı neden bu kadar geniş:** native'in en üst skor seviyesi tek bağlı grup: 4 alarmda kaçan
%70,78, 5 alarmda %22,73 (aşağıdaki tablo). Eşit YA noktası bu uçurumun hemen yanına düşüyor; birkaç zararsız dosya
yeniden örneklemde yer değiştirince değer büyük sıçrıyor. Yani bu hücre 5 yanlış alarm civarındaki birkaç dosyaya
bağlı. Yüzdelik aralık da böyle kesikli bir dağılımda yalnız yaklaşıktır.

## 2(b) %0,45 EXE: yanlış alarm sayıları ve takas (kullanıcı uyarısı)

2(b)'deki "M2d anlamlı olarak daha çok kaçırıyor" (61,62'ye karşı 49,18) hükmünde yanlış alarmlar: **A'da M2d 0/101,
native 1/101**; Dot_Net_test'te 15/3.713 ve 14/3.713. Karşılaştırma sıfır alarm ile bir alarm arasındaydı. Aynı alarm
sayısına getirilince (betimleyici; iç değerleme ve aralık yok, k birkaç dosya):

| Tür | k | M2d gerçek alarm, kaçan | Native gerçek alarm, kaçan | Az kaçıran |
|---|---|---|---|---|
| EXE | 0 | 0, %61,62 (1.010/1.639) | 0, %65,28 (1.070/1.639) | M2d |
| EXE | 1 | 1, %59,37 (973/1.639) | 1, %43,44 (712/1.639) | native |
| EXE | 2 | 2, %55,16 (904/1.639) | 2, %36,85 (604/1.639) | native |
| EXE | 3 | 3, %42,40 (695/1.639) | 3, %25,81 (423/1.639) | native |
| DLL | 0 | 0, %51,30 (79/154) | 0, %100,00 (154/154) | M2d |
| DLL | 3 | 3, %36,36 (56/154) | 0, %100,00 (154/154) | (alarm sayıları farklı) |
| DLL | 4 | 4, %31,82 (49/154) | 4, %70,78 (109/154) | M2d |
| DLL | 5 | 4, %31,82 (49/154) | 5, %22,73 (35/154) | (alarm sayıları farklı) |
| DLL | 6 | 6, %31,82 (49/154) | 6, %19,48 (30/154) | native |

Tamamı (DLL k = 0-7) `is2c_esit_ya.log`'da. Okuma: 2(b)'nin hükmü bir takas içeriyordu; sıfır alarmda yön tersine
dönüyor, küçük bir fark olarak M2d lehine. Bir alarm ve üzeri EXE'de native belirgin biçimde daha az kaçırıyor. Hüküm
"aynı yanlış alarmda" diye okunamaz. Bu tablo hüküm üretmez: 101 zararsızda k, tek tek dosyalardır.

## Betimleyici (hüküm üretmez)

**AUC** (eşlenik %95):

| Küme | Tür | M2d | Native | Fark [%95] |
|---|---|---|---|---|
| Dot_Net_test | EXE | 0,9769 | 0,9024 | +0,0744 [+0,0704, +0,0787] |
| Dot_Net_test | DLL | 0,9919 | 0,8378 | +0,1540 [+0,1474, +0,1608] |
| A | EXE | 0,9063 | 0,9635 | −0,0573 [−0,0851, −0,0310] |
| A | DLL | 0,9455 | 0,9799 | −0,0345 [−0,0565, −0,0147] |

"Hepsi" AUC'leri `.log`'da; tür karışımını taşır (Kural 8). **Kısmi AUC** (FPR ≤ H, o aralıktaki ortalama TPR):
Dot_Net_test'te dört hücrede de M2d lehine (fark +0,36 ile +0,66, aralıklar sıfırı dışlıyor). A DLL %1,05: M2d 0,6041,
native 0,1707, fark +0,4334 [−0,0597, +0,6253]; bu, native'in en üstteki 4 alarmlı bağlı grubundan geliyor. A'nın öteki
üç hücresi asgari örnek altında. Yani A'da AUC'de native önde, ama çok düşük FPR ucunda bu üstünlük görünmüyor.

**Duyarlılık (iç değerlemesiz, FPR'si H'yi aşmayan son köşe):** A DLL %1,05: M2d %31,82 (FPR %0,774), native %22,73
(FPR %0,967). Dot_Net_test hücreleri iç değerlemeli değerlerden en çok 2,33 puan ayrılıyor (native EXE %0,45: 70,26 ve 72,58); farkın
yönü değişmiyor. Köşelerin FPR'leri eşit olmadığından bu satırlar eşit YA değildir.

**Aile (eşit YA, H %1,05; beklenen kaçan, aralık yok; n ≥ 30 ve agenttesla):**

| Aile | A n | A M2d | A native | Dot_Net_test n | Dot_Net_test M2d | Dot_Net_test native |
|---|---|---|---|---|---|---|
| (bilinmiyor) | 662 | %70,81 | %40,14 | 4.815 | %45,95 | %78,83 |
| wacatac | 226 | %44,17 | %41,35 | 3.042 | %32,71 | %66,38 |
| asyncrat | 78 | %42,23 | %41,03 | 817 | %5,26 | %33,13 |
| heracles | 64 | %40,62 | %24,91 | 1.162 | %21,64 | %66,21 |
| redline | 60 | %31,46 | %41,57 | 491 | %11,61 | %67,58 |
| njrat | 43 | %69,77 | %44,05 | 1.034 | %11,51 | %62,88 |
| jalapeno | 41 | %17,07 | %18,48 | 1.550 | %19,68 | %81,14 |
| xworm | 36 | %27,78 | %24,83 | 2.805 | %1,64 | %32,26 |
| puwaders | 30 | %20,00 | %28,57 | 265 | %34,34 | %61,68 |
| agenttesla | 25 | 21,0/25 (n<30) | 14,9/25 (n<30) | 1.009 | %26,07 | %48,44 |

Dot_Net_test'in tamamı `.log`'da (86 aile). Aynı aile iki kümede farklı davranıyor (njrat M2d %69,77 ve %11,51).
2(b)'de redline'daki M2d üstünlüğü (sabit eşiklerde 11,67'ye karşı 45,00) eşit YA'da 31,46'ya karşı 41,57'ye
daralıyor: 2(b)'nin aile tablosu da eşikler farklı olduğu için takas içerir. "(bilinmiyor)" homojen bir aile değildir.
Aileler karar kuralına girmez.

## Sınırlar

- **Hüküm tek hücreye dayanıyordu** ve o hücre belirsiz çıktı. "Fark gösterilemedi", M2d'nin A'da eşdeğer ya da
  kötü olduğunu kanıtlamaz; %95 aralığı M2d lehine 63 puandan native lehine 22 puana uzanıyor.
- **EXE sınanamadı** (A'da 101 zararsız); bu bir bulgu değil, verinin sınırı.
- **Kümeler çelişiyor, neden ölçülmedi.** Dot_Net_test'te fark −34 ile −75 puan ve AUC M2d lehine; A'da AUC native
  lehine. Hangisinin sahayı temsil ettiği bilinmiyor. Native A popülasyonunu eğitimde gördü, M2d görmedi (yapısal asimetri).
- **Varsayılan kararın bedeli:** native, bu YA'larda Dot_Net_test'in zararlılarının %60-89'unu kaçırıyor. .NET'in zayıf
  nokta olması sürüyor; bu yüzden `tahmin_et.py`'nin "eşik altı .NET asla temiz değil" (BELİRSİZ) kuralı korunur.
- **Körlemesine değil:** aynı kümeler ve modeller 2(b)'de görüldü; asgari örnek eşiği bu bilgiyle yazıldı. n·H ≥ 3 aynı
  hücreyi seçerdi; n·H ≥ 2 A DLL %0,45'i de katardı.
- **Bootstrap** yalnız dosya örneklemesini ölçer; aile ve hafta kümeliliği aralıkları dar gösterebilir. Dot_Net_test'in
  dar aralıkları bu yüzden iyimser olabilir.
- **ROC noktası çalışma noktası değildir:** üretimde eşik doğrulamadan seçilir ve kayar (2(b)).
- **Çiftli eğitim havuzu:** M2d tarifi çiftli havuzla tanımlı; etkisi ölçülmedi.

## İş 2 durumu

(a), (b), (c) ön kayıtlarıyla ölçüldü. Ön kayıtlı kural gereği varsayılan karar: uzman Faz 1 kapsamı dışında, native tek
model. Uzmanın ileride yeniden ele alınması ancak yeni ve ön kayıtlı bir ölçümle olur: özellikle büyük bir zararsız .NET
EXE örneği olmadan EXE'de bu soru cevaplanamaz.
