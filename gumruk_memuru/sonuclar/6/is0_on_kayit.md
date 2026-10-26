# İş 0 ön kaydı - bekleyenleri paketle (yerel, gönderim yok)

`FAZ1_KAPANIS.md` (commit `1881249`) İş 0. Kontroller işten ÖNCE yazıldı. Hiçbir şey gönderilmez,
main'e alınmaz. Not: maddelerin bir kısmı (site commit'leri, çıkış kodu tablosu, etiketler) bu
kayıttan önce yapıldı; İş 0 onları bu kontrollerle KABUL eder ya da reddeder, yeni ölçüm değil.

## Yorum: "toplu taramada BELİRSİZ sayacı"
`toplu_tarama.py` tahmin YAPMIYOR (model yüklemez; dış doğrulama setinin özelliklerini üretir; "atlandi"
yalnız okunamayan dosya). Ona model eklemek doğrulama setini üreten kodu tahmin koduna bağlar. Bu
yüzden: `toplu_tarama.py` DEĞİŞMEZ; `ozellik/net-belirsiz` dalına `toplu_tahmin.py` eklenir: aynı
dosya gezme (`toplu_tarama.dosyalari_listele`) + `tahmin_et.tahmin` (tek özellik modülü, Kural 9;
model SHA-256 doğrulamalı, Kural 10); sayaçlar: temiz / BELİRSİZ / ZARARLI / OLASI ZARARLI /
PE değil / hata - BELİRSİZ hata DEĞİL. İlerleme %/ETA. Dosya adı yalnız istenirse (`--liste`)
ekrana basılır, dosyaya yazılmaz.

## Kontroller (hepsi GEÇMELİ)

| # | Kontrol | Geçme koşulu |
|---|---|---|
| G1 | Chief-Sef main / origin/main | ikisi de `4c58a37`, değişmedi |
| S1 | Site deposu | çalışma ağacı temiz; origin/main `be87d21` değişmedi; yerel main onun 4 commit önünde (`c475ef0`, `2f5fff5`, `3934d21`, `5a7ccb9`) |
| S2 | Site rakamları (betik `rakam_karsilastir.py`) | README (= `belge/yerel-karisim`, main + 1) dışında kalan rakam yalnız EN çıktı açıklaması (`2.0`, `0.700`); ana sayfa TR = EN; `<pre>` gerçek çıktıyla birebir |
| S3 | Yerel yanlış alarm cümlesi | TR ve EN proje sayfasında var (%61,6 / 61.6%, 0,51 / 0.51) |
| S4 | .NET notu, eski metin | origin/main'e göre notlarda SİLİNEN satır yalnız `og:image` ve `og:image:alt`; "Güncelleme (26 Ekim 2026)" / "Update (26 October 2026)" satırı var |
| S5 | Kartlar | `og-not-net-{tr,en}-v2.png` ve `og-chief-v2.png` var, 1200×630; eski adlara HTML'de referans yok; etiketler "Faz 1 modeli" / "M2, kestirmeli" (gözle) |
| S6 | Önizleme | proje (TR/EN), ana sayfa penceresi (TR/EN), notlar (TR/EN): 1366 ve 390 px'te yatay taşma yok |
| N1 | Çıkış kodu tablosu | `CIKIS_KODU` 0 temiz / 2 BELİRSİZ / 3 ZARARLI / 4 OLASI ZARARLI, hata 1; README (EN/TR) ve CLAUDE.md aynı tabloyu yazar |
| N2 | Test paketi | tamamı geçer, gcc ile, atlanan yok; `toplu_tahmin` testleri dahil |
| N3 | Davranış korunuyor | uçtan uca 20/20; notepad.exe çıktısı değişiklik öncesiyle bayt bayt aynı |
| N4 | `toplu_tahmin.py` | sahte modelle test: native EXE, .NET DLL, PE olmayan dosya, boş dosya → temiz 1, BELİRSİZ 1, PE değil 1, hata 1; BELİRSİZ hata sayacına girmez. Gerçek modelle duman koşusu (notepad.exe, System.dll, MSBuild.exe, bir .txt kopyası) sayaçları basar |
| N5 | Bozucu değişiklikler | çıkış kodu değişiklikleri ayrı commit'lerde, mesajda "BOZUCU DEGISIKLIK" |
| N6 | Gönderim yok | `ozellik/net-belirsiz`, `belge/yerel-karisim`, `olcum/uzman-native`, `faz1/kapanis` origin'de yok |
