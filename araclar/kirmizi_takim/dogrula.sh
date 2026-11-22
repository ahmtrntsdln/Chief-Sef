#!/bin/bash
# dogrula.sh - kurulumun dogrulamasi. KENDI kullanicinizla calistirin (root ile DEGIL):
#   ./dogrula.sh             tum kontroller; [sudo] isaretliler sudo parolasi ister
#   ./dogrula.sh --sudosuz   yalniz sudo gerektirmeyen kontroller
# Her kontrol GEÇTİ / KALDI yazar; sonunda toplam. Cikis: 0 hepsi gecti, 1 en az biri kaldi.
# [sudo] isaretli kontroller sudo ile kirmizi / sef kimligine gecer ya da root'a ait yerleri okur;
# hicbiri sistemi degistirmez (yalniz /var/tmp'de sef'in kendi gecici klasorleri acilip silinir).
set -uo pipefail
BURASI=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$BURASI/../.." && pwd)
# shellcheck source=ortak.sh
source "$BURASI/ortak.sh"

readonly SEF_KOK=/opt/sef
readonly BIN=/usr/local/bin
readonly SUDOERS=/etc/sudoers.d/sef-kirmizi
SUDOSUZ=0
case "${1:-}" in
    --sudosuz) SUDOSUZ=1 ;;
    "") ;;
    *) dur "Kullanim: $0 [--sudosuz]" ;;
esac
[ "$EUID" -ne 0 ] || dur "root ile degil, kendi kullanicinizla calistirin (sudo gerekenleri kendisi ister)"
BEN=$(id -un)
EV=$HOME
PY_ARAC="$REPO/.venv/bin/python"
ORNEK=/usr/x86_64-w64-mingw32/sys-root/mingw/bin/libwinpthread-1.dll
GECICI=$(mktemp -d)
trap 'rm -rf -- "$GECICI"' EXIT
cd / || exit 1   # kirmizi/sef olarak calisan komutlar okuyamadiklari bir klasorde baslamasin

GECEN=0; KALAN=0; ATLANAN=0
kontrol() {
    local ad=$1; shift
    if "$@" >/dev/null 2>&1; then echo "GEÇTİ  $ad"; GECEN=$((GECEN + 1)); else echo "KALDI  $ad"; KALAN=$((KALAN + 1)); fi
}
olmamali() {   # komut BASARISIZ olmali (erisim yok)
    local ad=$1; shift
    if "$@" >/dev/null 2>&1; then echo "KALDI  $ad"; KALAN=$((KALAN + 1)); else echo "GEÇTİ  $ad"; GECEN=$((GECEN + 1)); fi
}
skontrol() { if [ "$SUDOSUZ" -eq 1 ]; then echo "ATLANDI [sudo] $1"; ATLANAN=$((ATLANAN + 1)); else kontrol "[sudo] $1" "${@:2}"; fi; }
# solmamali ON_KOSUL AD KOMUT...: erisim olmamali. Yanlis GEÇTİ'yi onlemek icin once ayni
# kimlikle olumlu bir komutun calistigi (ON_KOSUL=1) gosterilmis olmali; yoksa KALDI.
solmamali() {
    if [ "$SUDOSUZ" -eq 1 ]; then echo "ATLANDI [sudo] $2"; ATLANAN=$((ATLANAN + 1)); return; fi
    if [ "$1" != 1 ]; then echo "KALDI  [sudo] $2  (on kosul: bu kimlikle olumlu komut calismadi)"; KALAN=$((KALAN + 1)); return; fi
    olmamali "[sudo] $2" "${@:3}"
}
izin() { [ "$(stat -c '%a %U %G' -- "$1" 2>/dev/null)" = "$2" ]; }
K() { sudo -u kirmizi -- "$@"; }                          # kirmizi olarak
KS() { sudo -u kirmizi -- sudo -n -u sef -- "$@"; }       # kirmizi -> sudoers -> sef

# ------------------------------------------------------------------ sudo'suz
adim "Sudo gerektirmeyen kontroller"
kontrol "ev klasorum $EV 700 ($BEN)" izin "$EV" "700 $BEN $BEN"
kontrol "kirmizi kullanicisi var" id kirmizi
kontrol "kirmizi'nin ev klasoru 700, sahibi kirmizi" izin "$(getent passwd kirmizi | cut -d: -f6)" "700 kirmizi kirmizi"
kontrol "kirmizi'nin ek grubu yok (sef, wheel vb. degil)" eval '[ "$(id -nG kirmizi)" = kirmizi ]'
kontrol "sef kullanicisi var, kabugu nologin, ek grubu yok" \
    eval '[ "$(getent passwd sef | cut -d: -f7)" = /usr/sbin/nologin ] && [ "$(id -nG sef)" = sef ]'
kontrol "$SEF_KOK: root:sef 750" izin "$SEF_KOK" "750 root sef"
kontrol "ben ($BEN) $SEF_KOK'u okuyamiyorum (var, ama sef grubunda degilim)" eval '[ -d "$SEF_KOK" ] && ! ls "$SEF_KOK"' 
for b in sef-tara sef-toplu; do
    kontrol "$BIN/$b: root:root 755 ve repodakiyle birebir" eval 'izin "$BIN/$b" "755 root root" && cmp -s "$BIN/$b" "$BURASI/$b"'
done

# ------------------------------------------------------------------ sudo'lu
adim "Sudo gerektiren kontroller [sudo]"
K_OK=0; S_OK=0; KS_OK=0
if [ "$SUDOSUZ" -eq 0 ]; then
    sudo -v || dur "sudo yetkisi alinamadi"
    K /usr/bin/true >/dev/null 2>&1 && K_OK=1                               # kirmizi olarak komut calisiyor
    sudo -u sef -- /usr/bin/true >/dev/null 2>&1 && S_OK=1                  # sef olarak komut calisiyor
    KS "$BIN/sef-tara" --surum >/dev/null 2>&1 && KS_OK=1                    # kirmizi -> sef sudoers yolu calisiyor
fi
skontrol "on kosul: kirmizi olarak komut calisiyor" eval '[ "$K_OK" = 1 ]'
skontrol "on kosul: sef olarak komut calisiyor" eval '[ "$S_OK" = 1 ]'
skontrol "on kosul: kirmizi sudoers ile sef-tara'yi sef olarak calistirabiliyor" eval '[ "$KS_OK" = 1 ]'

skontrol "visudo -c" sudo visudo -c
skontrol "$SUDOERS: root:root 440 ve repodaki sudoers.sef-kirmizi ile birebir" \
    eval '[ "$(sudo stat -c "%a %U %G" "$SUDOERS")" = "440 root root" ] && sudo cat "$SUDOERS" | cmp -s - "$BURASI/sudoers.sef-kirmizi"'
skontrol "sudo -l -U kirmizi: yalniz (sef) NOPASSWD sef-tara, sef-toplu; baska kural yok" \
    eval 'L=$(sudo sudo -l -U kirmizi | sed -n "/may run the following/,\$p" | tail -n +2 | sed "s/^ *//" | grep -v "^$"); [ "$L" = "(sef) NOPASSWD: /usr/local/bin/sef-tara, /usr/local/bin/sef-toplu" ]'

solmamali "$K_OK" "kirmizi $EV'i listeleyemez" K ls "$EV"
solmamali "$K_OK" "kirmizi ~/Chief-Sef'i okuyamaz (CLAUDE.md)" K cat "$EV/Chief-Sef/CLAUDE.md"
solmamali "$K_OK" "kirmizi ~/ember2024 modelini okuyamaz" K test -r "$EV/ember2024/model/model_native.joblib"
solmamali "$K_OK" "kirmizi ~/sef_yedek'i listeleyemez" K ls "$EV/sef_yedek"
solmamali "$K_OK" "kirmizi $SEF_KOK'u listeleyemez" K ls "$SEF_KOK"
solmamali "$K_OK" "kirmizi $SEF_KOK/SURUM.txt'yi dogrudan okuyamaz" K cat "$SEF_KOK/SURUM.txt"
solmamali "$K_OK" "kirmizi $SEF_KOK modelini okuyamaz" K test -r "$SEF_KOK/model/model_native.joblib"
solmamali "$KS_OK" "kirmizi sef olarak baska komut calistiramaz (id)" KS /usr/bin/id
solmamali "$KS_OK" "kirmizi sef olarak kabuk acamaz" KS /bin/bash -c true
solmamali "$K_OK" "kirmizi root olarak calistiramaz" K sudo -n /usr/bin/id
solmamali "$S_OK" "sef $SEF_KOK'a yazamaz (kod ve model degistirilemez)" sudo -u sef -- test -w "$SEF_KOK/kod/gumruk_memuru"
skontrol "$SEF_KOK altinda hepsi root:sef, dizin 750, dosya 640/750, 'digerleri' izni yok" \
    eval '[ -z "$(sudo find "$SEF_KOK" ! -type l \( ! -user root -o ! -group sef -o -perm /007 -o \( -type d ! -perm 750 \) -o \( -type f ! -perm 640 ! -perm 750 \) \) -print -quit)" ]'
skontrol "$SEF_KOK modelinin sha256'si beklenen ($SEF_BEKLENEN_MODEL_SHA)" \
    eval '[ "$(sudo sha256sum "$SEF_KOK/model/model_native.joblib" | cut -d" " -f1)" = "$SEF_BEKLENEN_MODEL_SHA" ]'
skontrol "$SEF_KOK/kod, SURUM.txt'deki commit ile ve kod.commit ile tutarli" \
    eval 'C=$(sudo cat "$SEF_KOK/kod.commit"); sudo grep -q "^kod_commit: $C " "$SEF_KOK/SURUM.txt"'

# Kara kutu kullanimi: kirmizi -> sudo -> sef -> sarmalayici.
skontrol "sef-tara --surum (kirmizi): sinirlar ve model sha256 yazili" \
    eval 'KS "$BIN/sef-tara" --surum >"$GECICI/surum" && grep -q "300 sn" "$GECICI/surum" && grep -q "model_sha256: $SEF_BEKLENEN_MODEL_SHA" "$GECICI/surum"'
if [ -f "$ORNEK" ]; then
    skontrol "sef-tara ornek DLL ile (kirmizi): cikis 0-4, skor satiri var" \
        eval 'KS "$BIN/sef-tara" <"$ORNEK" >"$GECICI/tara"; R=$?; [ "$R" -le 4 ] && grep -q "^Zararli olasiligi" "$GECICI/tara"'
    skontrol "sef-tara --ozet: sef'e ulasan girdinin sha256'si dosyaninkiyle ayni (ikili veri sudo'dan bozulmadan gecti)" \
        eval 'KS "$BIN/sef-tara" --ozet <"$ORNEK" 2>&1 >/dev/null | grep -q "sha256 $(sef_sha "$ORNEK")"'
else
    echo "KALDI  ornek DLL yok ($ORNEK; mingw64-gcc paketi): sef-tara ornekle sinanamadi"; KALAN=$((KALAN + 1))
fi
"$PY_ARAC" -I - "$GECICI" "$ORNEK" <<'EOF' >/dev/null 2>&1
import io, os, sys, tarfile
g, ornek = sys.argv[1:3]
with tarfile.open(f"{g}/noktanokta.tar", "w") as t:
    ti = tarfile.TarInfo("../x"); ti.size = 1; t.addfile(ti, io.BytesIO(b"x"))
if os.path.exists(ornek):
    with tarfile.open(f"{g}/ornek.tar", "w") as t:
        t.add(ornek, arcname="ornek.dll")
EOF
skontrol "sef-toplu '../x' iceren arsivi 64 ile reddeder (kirmizi)" \
    eval 'KS "$BIN/sef-toplu" <"$GECICI/noktanokta.tar" 2>"$GECICI/nn.err"; [ $? -eq 64 ] && grep -q "ARŞİV REDDEDİLDİ" "$GECICI/nn.err"'
if [ -f "$GECICI/ornek.tar" ]; then
    skontrol "sef-toplu ornek arsivle (kirmizi): cikis 0-4" eval 'KS "$BIN/sef-toplu" <"$GECICI/ornek.tar"; [ $? -le 4 ]'
fi
skontrol "bilinmeyen arguman 64 (kirmizi)" eval 'KS "$BIN/sef-tara" --baska </dev/null; [ $? -eq 64 ]'
skontrol "calismalardan sonra /var/tmp'de sef-tara.* / sef-toplu.* kalmadi" \
    eval '[ -z "$(sudo find /var/tmp -maxdepth 1 \( -name "sef-tara.*" -o -name "sef-toplu.*" \) -print -quit)" ]'

echo
echo "SONUC: $GECEN GEÇTİ, $KALAN KALDI, $ATLANAN ATLANDI"
[ "$KALAN" -eq 0 ]
