# İş 1 sonucu - main'e alım (26 Ekim 2026)

Ön kayıt: `FAZ1_KAPANIS.md` revizyon 1 (commit `d212b7e`), İş 1 tanımı ve "bitti" ölçütü (ayrı ön kayıt
dosyası yazılmadı; kontroller orada tanımlıydı). Her birleştirmeden önce diff özeti gösterildi ve
kullanıcı onayı alındı.

| # | Kontrol | Sonuç | Kanıt |
|---|---|---|---|
| 1 | Dallar origin'de, force / PR yok | **GEÇTİ** | `belge/yerel-karisim` `eed565f`, `ozellik/net-belirsiz` `846805e`, `olcum/uzman-native` `3b6a758`; `faz1/kapanis` yedek |
| 2 | `belge/yerel-karisim` → main (`--no-ff`) | **GEÇTİ** | `7e5a293`; testler 63/63 (main'de beklenen), uçtan uca 20/20, gönderildi |
| 3 | `ozellik/net-belirsiz` → main | **GEÇTİ** | `e293cb9`; testler 111/111 (beklenen), 20/20, gönderildi |
| 4 | `olcum/uzman-native` → main | **GEÇTİ** | `3dc7b9e`; birleştirmeden önce CLAUDE.md'ye kapsam sınırı cümleleri (kullanıcı isteği, `3b6a758`); testler 111/111, 20/20, gönderildi |
| 5 | Her birleştirmeden sonra main → `faz1/kapanis` (rebase yok) | **GEÇTİ** | `cfc6933`, `e6c0fdf`, `840a6a6` |
| 6 | Site (4 commit) yalnız `belge/yerel-karisim` main'deyken ve "gönder" ile | **GEÇTİ** | `be87d21..5a7ccb9`, `e293cb9`'dan sonra, kullanıcı onayıyla |
| 7 | Site rakamları = main README (betik), main dışı içerik yok | **GEÇTİ** | README dışı yalnız EN çıktı açıklaması (`2.0`, `0.700`); eklenen her satırın rakamı README'de ya da notun kendi 9 Ekim metninde; uzman sonuçları / çıkış kodu sitede yok |
| 8 | Canlı = commit (önbelleksiz), canlı rakamlar = README, kartlar | **GEÇTİ** | 6 sayfa + 3 `-v2` kart bayt bayt aynı (2. deneme); `og:image` adresleri `-v2`, 200; eski adlar 404 |

**İş 1: BİTTİ (8 / 8 GEÇTİ).** origin/main `3dc7b9e`, site `5a7ccb9`.

Notlar:
- `olcum/uzman-native` gönderimi ilk denemede ağ hatasıyla (DNS) başarısız oldu; birleştirme
  yerelde yapıldıktan ve testler geçtikten sonra dal ve main yeniden gönderildi (force yok).
- Kontrol betiklerindeki iki hata düzeltildi, sonuçları değiştirmedi: aralıkların ("48-51") ikinci
  sayısı okunmuyordu; canlı kontrol yayın gelmeden 404'te duruyordu (artık yeniden deniyor).
- `belge/yerel-karisim`, `ozellik/net-belirsiz` ve `olcum/uzman-native` dalları origin'de duruyor
  (silinmedi).
