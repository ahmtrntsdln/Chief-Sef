#!/bin/bash
# kaldir.sh - kurulum.sh'nin yaptigi her seyi geri alir. Calistirma: sudo ./kaldir.sh
#   /etc/sudoers.d/sef-kirmizi (once; sonra visudo -c), /usr/local/bin/sef-tara ve sef-toplu,
#   /opt/sef, /var/tmp'deki sef-tara.* / sef-toplu.* / sef-kurulum-uv.* kalintilari,
#   sef kullanicisi ve grubu, kirmizi kullanicisi.
# kirmizi'nin ev klasoru (kirmizi takimin notlari/bulgulari orada olabilir) AYRICA sorulur;
# "hayir" denirse klasor yerinde kalir (sahibi artik var olmayan bir UID olur).
# Calisan sef / kirmizi sureci varsa DURUR (surecleri kendisi oldurmez).
set -euo pipefail
BURASI=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=ortak.sh
source "$BURASI/ortak.sh"

readonly SEF_KOK=/opt/sef
readonly BIN=/usr/local/bin
readonly SUDOERS=/etc/sudoers.d/sef-kirmizi

[ "$EUID" -eq 0 ] || dur "root gerekir: sudo $0"
[ -r /dev/tty ] || dur "onay icin terminal gerekli"

adim "On denetim (degisiklik yok)"
for k in sef kirmizi; do
    if id "$k" >/dev/null 2>&1 && pgrep -u "$k" >/dev/null; then
        dur "$k kullanicisinin calisan surecleri var: $(pgrep -u "$k" | tr '\n' ' ')- once sonlandirin (ornek: sudo pkill -u $k)"
    fi
done
[ ! -L "$SEF_KOK" ] || dur "$SEF_KOK bir sembolik baglanti; elle inceleyin"
if [ -d "$SEF_KOK" ] && [ ! -f "$SEF_KOK/SURUM.txt" ] && [ -n "$(ls -A "$SEF_KOK")" ]; then
    dur "$SEF_KOK bu kurulumun degil gibi (SURUM.txt yok, bos degil); elle inceleyin"
fi
KIRMIZI_EV=""
if id kirmizi >/dev/null 2>&1; then KIRMIZI_EV=$(getent passwd kirmizi | cut -d: -f6); fi

var_mi() { if [ -e "$1" ] || [ -L "$1" ]; then echo "[var]"; else echo "[yok]"; fi; }
kullanici_var_mi() { if id "$1" >/dev/null 2>&1; then echo "[var]"; else echo "[yok]"; fi; }
cat <<OZET

Kaldirilacaklar:
  $SUDOERS $(var_mi "$SUDOERS")
  $BIN/sef-tara $(var_mi "$BIN/sef-tara"), $BIN/sef-toplu $(var_mi "$BIN/sef-toplu")
  $SEF_KOK $(var_mi "$SEF_KOK") (kod, python, venv, model kopyasi; asil model ve repo YERINDE kalir)
  /var/tmp/sef-tara.*, /var/tmp/sef-toplu.*, /var/tmp/sef-kurulum-uv.* kalintilari
  kullanici + grup sef $(kullanici_var_mi sef)
  kullanici kirmizi $(kullanici_var_mi kirmizi) (ev klasoru: ayrica sorulacak)

OZET
read -r -p "Devam edilsin mi? [e/H] " CEVAP </dev/tty
[ "$CEVAP" = e ] || [ "$CEVAP" = E ] || dur "iptal edildi (degisiklik yapilmadi)"

EV_SIL=0
if [ -n "$KIRMIZI_EV" ] && [ -d "$KIRMIZI_EV" ]; then
    echo
    echo "kirmizi'nin ev klasoru: $KIRMIZI_EV ($(du -sh -- "$KIRMIZI_EV" | cut -f1); kirmizi takimin notlari burada olabilir)"
    read -r -p "Bu klasor de SILINSIN mi? Geri alinamaz. [e/H] " CEVAP </dev/tty
    if [ "$CEVAP" = e ] || [ "$CEVAP" = E ]; then EV_SIL=1; fi
fi

adim "1. sudoers"
if [ -e "$SUDOERS" ]; then rm -f -- "$SUDOERS"; bilgi "silindi"; else bilgi "yok, atlandi"; fi
visudo -c >/dev/null || dur "visudo -c basarisiz: sudoers'i hemen inceleyin"
bilgi "visudo -c tamam"

adim "2. sarmalayicilar"
for b in sef-tara sef-toplu; do
    if [ -e "$BIN/$b" ]; then rm -f -- "$BIN/$b"; bilgi "$BIN/$b silindi"; else bilgi "$BIN/$b yok, atlandi"; fi
done

adim "3. $SEF_KOK"
if [ -d "$SEF_KOK" ]; then rm -rf -- "$SEF_KOK"; bilgi "silindi"; else bilgi "yok, atlandi"; fi

adim "4. /var/tmp kalintilari"
find /var/tmp -maxdepth 1 \( -name 'sef-tara.*' -o -name 'sef-toplu.*' -o -name 'sef-kurulum-uv.*' \) \
    -print -exec rm -rf -- {} + | sed 's/^/    silindi: /'

adim "5. kullanicilar"
if id sef >/dev/null 2>&1; then userdel sef; bilgi "sef silindi"; else bilgi "sef yok, atlandi"; fi
if getent group sef >/dev/null; then groupdel sef; bilgi "grup sef silindi"; fi
if id kirmizi >/dev/null 2>&1; then
    if [ "$EV_SIL" -eq 1 ]; then
        userdel --remove kirmizi; bilgi "kirmizi ve ev klasoru ($KIRMIZI_EV) silindi"
    else
        userdel kirmizi; bilgi "kirmizi silindi; ev klasoru YERINDE: $KIRMIZI_EV (sahibi eski UID)"
    fi
    if getent group kirmizi >/dev/null; then groupdel kirmizi; bilgi "grup kirmizi silindi"; fi
else
    bilgi "kirmizi yok, atlandi"
fi

adim "Kaldirma bitti"
