# Kara kutu kırmızı takım altyapısı

Amaç: Şef'i hiç tanımayan bir ajan (kullanıcı `kirmizi`), yalnız dosya verip cevap alarak test eder.
Kodu, modeli ve proje sahibinin dosyalarını göremez.

## Kullanıcılar ve erişim

| Kullanıcı | Rol | Erişim |
|---|---|---|
| ahmtrntsdln | sahip | ev klasörü 700; `kirmizi` okuyamaz |
| sef | çalıştırıcı (sistem kullanıcısı, nologin) | `/opt/sef`'i okur, yazamaz |
| kirmizi | kırmızı takım (ev klasörü 700, ek grubu yok) | yalnız `sudo -u sef` ile iki sarmalayıcı |

`/etc/sudoers.d/sef-kirmizi`, bu tek kural:

    kirmizi ALL=(sef) NOPASSWD: /usr/local/bin/sef-tara, /usr/local/bin/sef-toplu

`/opt/sef`: sahibi root, grubu sef; dizinler 750, dosyalar 640. Çalıştırılabilir dosyalar 750
(Python yorumlayıcısı; 640 olsaydı çalışmazdı). İçeriği:

- `kod/`: origin/main'in `git archive` kopyası, değiştirilmemiş.
- `python/`: kullanıcının uv ortamındaki CPython 3.13.7'nin kopyası.
- `venv/`: `gereksinimler.lock` ile birebir (uv ortamının `uv pip freeze` çıktısı).
- `model/model_native.joblib`: SHA-256 `f6b74df8…69ba536` olmak zorunda; tutmazsa kurulum durur.
- `calistir.py`, `arsiv_ac.py`.
- `SURUM.txt`: kod commit'i, model SHA-256'sı, Python ve paket sürümleri.

`calistir.py` main'deki koda tek bir şey ekler: `sef_ayarlar.NATIVE_MODEL_YOLU`'nu
(`C:\ember2024\...`, Linux'ta geçersiz) betik içe aktarılmadan önce `/opt/sef/model`'e yönlendirir.
Hash denetimi (Kural 10) `tahmin_et.model_yukle`'de olduğu gibi kalır.

## kirmizi'nin kullanımı

    sudo -u sef /usr/local/bin/sef-tara < dosya             # tek dosya
    sudo -u sef /usr/local/bin/sef-tara --ozet < dosya      # + stderr'e girdi boyutu ve sha256'sı
    sudo -u sef /usr/local/bin/sef-toplu [--liste] < arsiv.tar   # tar (gz/bz2/xz da olur)
    sudo -u sef /usr/local/bin/sef-tara --surum             # sınırlar + SURUM.txt

stdout, stderr ve çıkış kodu `tahmin_et.py` / `toplu_tahmin.py`'nin kendisinindir:
0 temiz, 1 hata, 2 BELİRSİZ, 3 ZARARLI, 4 OLASI ZARARLI. Toplu araçta en kötü sonuç geçerlidir.
Sarmalayıcının kendi kodları:

| Kod | Anlamı |
|---|---|
| 64 | girdi reddedildi: bilinmeyen argüman, 2 GiB'lık girdi sınırı aşıldı, arşiv reddedildi (tar değil; `..` ile dışarı çıkan yol; mutlak ya da dışarı gösteren bağlantı; aygıt dosyası; açık boyut 2 GiB'ı aşıyor) |
| 124 | ZAMAN AŞIMI: bütün çağrı (okuma + açma + tarama) 300 sn |

Sarmalayıcının kendi mesajları stderr'e, `sef-tara:` / `sef-toplu:` önekiyle yazılır.

Sınırlar: 300 sn, bellek 8 GiB (`prlimit --as`, adres alanı), girdi 2 GiB. Gerçek modelle
ölçülen: tek dosya ~1,5 sn, ~1 GB RSS.

Arşiv açılırken kural "ya hepsi ya hiç": önce bütün üyeler tarfile'ın `data` süzgecinden geçer,
tek üye bile reddedilirse hiçbir şey açılmaz. Mutlak dosya yolu reddedilmez: süzgeç baştaki `/`'yi
kırpar, dosya hedefin içine yazılır (PEP 706'da belgelenmiş davranış).

Her çağrı `sef`'e ait, 700 izinli bir geçici klasörde çalışır (`/var/tmp/sef-tara.*`). Klasör
her durumda silinir: normal çıkışta, hatada, zaman aşımında ve HUP/INT/TERM sinyalinde (sinyal
gelince çocuk süreç de sonlandırılır). SIGKILL yakalanamaz; o durumda kalan klasörü sonraki
çağrı siler (60 dakikadan eski olanları).

## Dosyalar

| Dosya | Çalıştıran | Ne yapar |
|---|---|---|
| `kurulum.sh` | Ahmet, `sudo ./kurulum.sh` | önce yalnız okuyarak denetler, özet yazar, onay ister; sonra kullanıcılar, `/opt/sef`, sarmalayıcılar, sudoers (`visudo -cf`, ardından `visudo -c`), `restorecon`. İdempotent. |
| `kaldir.sh` | Ahmet, `sudo ./kaldir.sh` | hepsini geri alır; `kirmizi`'nin ev klasörünü silmeden önce ayrıca sorar. Çalışan `sef` / `kirmizi` süreci varsa durur. |
| `dogrula.sh` | Ahmet, kendi kullanıcısıyla | her kontrol GEÇTİ ya da KALDI yazar. `[sudo]` işaretli kontroller sudo ister; `--sudosuz` bunları atlar. Olumsuz kontroller ("kirmizi okuyamaz") ancak aynı kimlikle olumlu bir komut çalıştıysa GEÇTİ verir. |
| `test_sudosuz.sh` | herkes | aynı kurma işlevleriyle (`ortak.sh`) geçici bir klasöre `/opt/sef` kopyası kurar; sarmalayıcıların yolları ve sınırları değiştirilmiş kopyalarını sınar. İnternet bağlantısı gerekir (PyPI). |
| `ortak.sh` | yukarıdakiler (`source`) | kod, python, venv, model, SURUM.txt kurma işlevleri |
| `sef-tara`, `sef-toplu` | kirmizi → sudo → sef | sarmalayıcılar |
| `calistir.py`, `arsiv_ac.py` | sarmalayıcılar | başlatıcı ve tar açıcı |
| `sudoers.sef-kirmizi` | kurulum | sudoers parçası |
| `gereksinimler.lock` | kurulum | venv paket listesi |

## Kurulum sırası (Ahmet)

1. Bu dizindeki dosyaları oku (`kurulum.sh` önce özet gösterir, onay ister).
2. `./test_sudosuz.sh`: sudo gerektirmez.
3. `sudo ./kurulum.sh`
4. `./dogrula.sh`: bütün satırlar GEÇTİ olmalı.
5. kirmizi'ye geçmek için: `sudo machinectl shell kirmizi@` ya da `sudo -iu kirmizi`.
