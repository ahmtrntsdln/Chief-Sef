# İş 0 sonucu - bekleyenleri paketle (26 Ekim 2026)

Ön kayıt `is0_on_kayit.md` (commit `3395f10`). Hiçbir şey gönderilmedi, main'e alınmadı.

| # | Kontrol | Sonuç | Kanıt |
|---|---|---|---|
| G1 | Chief-Sef main / origin/main | **GEÇTİ** | ikisi de `4c58a37` |
| S1 | Site deposu | **GEÇTİ** | ağaç temiz; origin/main `be87d21`; yerel `c475ef0`, `2f5fff5`, `3934d21`, `5a7ccb9` |
| S2 | Site rakamları = README (`belge/yerel-karisim`, `eed565f`) | **GEÇTİ** | README dışı yalnız EN çıktı açıklaması (`2.0`, `0.700`); ana sayfa TR = EN; `<pre>` gerçek çıktıyla birebir |
| S3 | Yerel yanlış alarm cümlesi | **GEÇTİ** | TR (%61,6; %0,51 [0,28-0,91]) ve EN (61.6%; 0.51% [0.28-0.91]) |
| S4 | .NET notu, eski metin | **GEÇTİ** | iki notta silinen satır yalnız `og:image` ve `og:image:alt`; "Güncelleme (26 Ekim 2026)" / "Update (26 October 2026)" var |
| S5 | Kartlar | **GEÇTİ** | üç `-v2` kart 1200×630; eski adlara referans 0; etiketler "Faz 1 modeli" / "uzman model M2, kestirmeli" (gözle) |
| S6 | Önizleme | **GEÇTİ** | 6 sayfa × 1366 / 390 px: yatay taşma yok |
| N1 | Çıkış kodu tablosu | **GEÇTİ** | `CIKIS_KODU` {zararsiz 0, BELIRSIZ 2, ZARARLI 3, OLASI ZARARLI 4}, `CIKIS_HATA` 1; README EN/TR ve CLAUDE.md aynı |
| N2 | Test paketi | **GEÇTİ** | 95 passed, atlanan yok (gcc 16.2) |
| N3 | Davranış korunuyor | **GEÇTİ** | uçtan uca 20/20; notepad.exe çıktısı bayt bayt aynı |
| N4 | `toplu_tahmin.py` | **GEÇTİ** | sahte modelle temiz 1 / BELİRSİZ 1 / PE değil 1 / hata 1 (BELİRSİZ hata değil); gerçek modelle duman: notepad temiz, System.dll ve MSBuild.exe BELİRSİZ, .txt PE değil, hata 0 |
| N5 | Bozucu değişiklikler ayrı | **GEÇTİ** | `3214cfb`, `4031de9` ("BOZUCU DEGISIKLIK"); `be062f9` ve `9ca107f` bozucu değil |
| N6 | Gönderim yok | **GEÇTİ** | `ozellik/net-belirsiz`, `belge/yerel-karisim`, `olcum/uzman-native`, `faz1/kapanis` origin'de yok |

**İş 0: BİTTİ (14 / 14 GEÇTİ).**

Notlar:
- "Toplu taramada BELİRSİZ sayacı" ön kayıttaki yorumla yapıldı: `toplu_tarama.py` değişmedi,
  sayaç yeni `toplu_tahmin.py`'de (`9ca107f`).
- S2 README kaynağı henüz main'de değil: site, `belge/yerel-karisim` main'e girmeden (İş 1)
  yayınlanamaz.
- Açık soru (İş 0 kapsamı dışında): `toplu_tahmin.py` tamamlanınca 0 döndürüyor; içinde ZARARLI ya
  da BELİRSİZ varsa farklı bir çıkış kodu verip vermemesi kullanıcı kararı.
