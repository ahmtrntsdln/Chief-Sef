#!/bin/bash
# kurulum.sh - Sef kara kutu kirmizi takim altyapisi. Calistirma (Ahmet, inceledikten sonra):
#   cd ~/Chief-Sef/araclar/kirmizi_takim && sudo ./kurulum.sh
#
# Yapar (idempotent; var olani atlar ya da ayni sonuca getirir, her adimi yazar):
#   1. sef (sistem kullanicisi, nologin) ve kirmizi (ev klasoru 700, ek grup YOK) kullanicilari
#   2. /opt/sef: origin/main'in kodu (git archive, degistirilmeden), kullanicinin uv
#      ortamindaki CPython 3.13.7'nin kopyasi, venv (gereksinimler.lock ile birebir; PyPI'den),
#      model_native.joblib (sha256 beklenenle tutmazsa DURUR), calistir.py, arsiv_ac.py,
#      SURUM.txt. Sahibi root, grup sef; dizinler 750, dosyalar 640 (calistirilabilirler 750).
#   3. /usr/local/bin/sef-tara, sef-toplu (root:root 755)
#   4. /etc/sudoers.d/sef-kirmizi (root:root 440; once visudo -cf, sonra visudo -c)
#   5. SELinux varsa restorecon
# Baslamadan once (yalniz okuyarak) her seyi denetler, ozet yazar ve onay ister.
# Geri alma: kaldir.sh. Dogrulama: dogrula.sh.
set -euo pipefail
umask 027
BURASI=$(cd "$(dirname "$0")" && pwd)
# shellcheck source=ortak.sh
source "$BURASI/ortak.sh"

readonly SEF_KOK=/opt/sef
readonly BIN=/usr/local/bin
readonly SUDOERS=/etc/sudoers.d/sef-kirmizi
readonly LOCK="$BURASI/gereksinimler.lock"

[ "$EUID" -eq 0 ] || dur "root gerekir: sudo $0"
KAYNAK_KULLANICI=${SUDO_USER:-}
[ -n "$KAYNAK_KULLANICI" ] && [ "$KAYNAK_KULLANICI" != root ] \
    || dur "kendi kullanicinizdan sudo ile calistirin (SUDO_USER: repo, model ve uv onun ev klasorunde)"
EV=$(getent passwd "$KAYNAK_KULLANICI" | cut -d: -f6)
REPO="$EV/Chief-Sef"
MODEL_KAYNAK="$EV/ember2024/model/model_native.joblib"
UV="$EV/.local/bin/uv"
KULLANICI_VENV="$REPO/.venv"
# git ve uv'nin kullanici tarafindaki okumalari o kullanici olarak (root, kullanicinin
# .git'ine ya da onbellegine dosya yazmasin).
SEF_GIT_ONEK=(runuser -u "$KAYNAK_KULLANICI" --)
kullanici_olarak() { runuser -u "$KAYNAK_KULLANICI" -- "$@"; }

# ------------------------------------------------------------------ on denetim (yalniz okur)
adim "On denetim (degisiklik yok)"
for arac in git runuser prlimit timeout visudo useradd groupadd install sha256sum tar; do
    command -v "$arac" >/dev/null || dur "'$arac' bulunamadi"
done
[ -x "$UV" ] || dur "uv yok: $UV"
[ -f "$MODEL_KAYNAK" ] || dur "model yok: $MODEL_KAYNAK"
[ -f "$KULLANICI_VENV/pyvenv.cfg" ] || dur "uv ortami yok: $KULLANICI_VENV"
bilgi "kaynak kullanici: $KAYNAK_KULLANICI, repo: $REPO"

bilgi "git fetch origin ($KAYNAK_KULLANICI olarak)"
kullanici_olarak git -C "$REPO" fetch -q origin || dur "git fetch basarisiz"
COMMIT=$(kullanici_olarak git -C "$REPO" rev-parse origin/main)
KONU=$(kullanici_olarak git -C "$REPO" log -1 --format='%cs %s' "$COMMIT")
bilgi "kurulacak kod: origin/main = $COMMIT ($KONU)"

META_SHA=$(sef_meta_model_sha "$REPO" "$COMMIT") || dur "meta veride model_sha256 okunamadi"
[ "$META_SHA" = "$SEF_BEKLENEN_MODEL_SHA" ] \
    || dur "main'deki model_native_meta.json model_sha256 ($META_SHA) beklenenden farkli"
bilgi "meta model_sha256 = beklenen"
bilgi "kaynak modelin sha256'si hesaplaniyor (~414 MB)..."
KAYNAK_SHA=$(sef_sha "$MODEL_KAYNAK")
[ "$KAYNAK_SHA" = "$SEF_BEKLENEN_MODEL_SHA" ] \
    || dur "kaynak model sha256 ($KAYNAK_SHA) beklenenden ($SEF_BEKLENEN_MODEL_SHA) farkli"
bilgi "kaynak model sha256 = $SEF_BEKLENEN_MODEL_SHA"

kullanici_olarak "$UV" pip freeze --no-config --python "$KULLANICI_VENV/bin/python" 2>/dev/null \
    | diff <(grep -v '^#' "$LOCK") - >/dev/null \
    || dur "gereksinimler.lock, uv ortaminin ($KULLANICI_VENV) paket listesiyle ayni degil"
bilgi "gereksinimler.lock = uv ortaminin paketleri ($(grep -vc '^#' "$LOCK") paket)"
PY_KAYNAK=$(dirname "$(sed -n 's/^home = //p' "$KULLANICI_VENV/pyvenv.cfg")")
[ "$(grep -c "^version_info = $SEF_PYTHON_SURUM\$" "$KULLANICI_VENV/pyvenv.cfg")" -eq 1 ] \
    || dur "uv ortaminin python'u $SEF_PYTHON_SURUM degil"
[ -x "$PY_KAYNAK/bin/python3.13" ] || dur "python yok: $PY_KAYNAK/bin/python3.13"
bilgi "python kaynagi: $PY_KAYNAK"

if [ -e "$SEF_KOK" ] && [ ! -f "$SEF_KOK/SURUM.txt" ] && [ -n "$(ls -A "$SEF_KOK" 2>/dev/null)" ]; then
    dur "$SEF_KOK var, bos degil ve bu kurulumun degil (SURUM.txt yok); elle inceleyin"
fi
[ ! -L "$SEF_KOK" ] || dur "$SEF_KOK bir sembolik baglanti; elle inceleyin"
if id kirmizi >/dev/null 2>&1; then
    [ "$(id -nG kirmizi)" = kirmizi ] || dur "kirmizi zaten var ve ek gruplari var: $(id -nG kirmizi)"
fi
if id sef >/dev/null 2>&1; then
    [ "$(id -nG sef)" = sef ] || dur "sef zaten var ve ek gruplari var: $(id -nG sef)"
fi

# ------------------------------------------------------------------ ozet + onay
cat <<OZET

Yapilacaklar:
  1. Kullanicilar: sef (sistem, nologin, grup sef)$(id sef >/dev/null 2>&1 && echo ' [var, atlanir]')
                   kirmizi (ev /home/kirmizi 700, bash, parolasiz/kilitli)$(id kirmizi >/dev/null 2>&1 && echo ' [var, atlanir]')
  2. $SEF_KOK (root:sef, dizin 750, dosya 640, calistirilabilir 750):
       kod/    origin/main $COMMIT
       python/ $(basename "$PY_KAYNAK") (kopya)
       venv/   $(grep -vc '^#' "$LOCK") paket, gereksinimler.lock ile birebir (PyPI'den indirilir)
       model/  model_native.joblib sha256 $SEF_BEKLENEN_MODEL_SHA
       calistir.py, arsiv_ac.py, SURUM.txt
  3. $BIN/sef-tara, $BIN/sef-toplu (root:root 755)
  4. $SUDOERS (root:root 440):
       $(grep -v '^#' "$BURASI/sudoers.sef-kirmizi")
  5. restorecon (SELinux etiketleri)
Dokunulmayanlar: sistem Python'u, Windows diski, $REPO (yalniz okunur; fetch kullanici olarak).

OZET
[ -r /dev/tty ] || dur "onay icin terminal gerekli"
read -r -p "Devam edilsin mi? [e/H] " CEVAP </dev/tty
[ "$CEVAP" = e ] || [ "$CEVAP" = E ] || dur "iptal edildi (degisiklik yapilmadi)"

# ------------------------------------------------------------------ 1. kullanicilar
adim "1. Kullanicilar"
if getent group sef >/dev/null; then bilgi "grup sef var, atlandi"; else groupadd --system sef; bilgi "grup sef acildi"; fi
if id sef >/dev/null 2>&1; then
    bilgi "sef var, atlandi"
else
    useradd --system --gid sef --no-create-home --home-dir / --shell /usr/sbin/nologin \
        --comment "Sef tarayici (kirmizi takim)" sef
    bilgi "sef acildi"
fi
if id kirmizi >/dev/null 2>&1; then
    bilgi "kirmizi var, atlandi"
else
    useradd --create-home --user-group --shell /bin/bash --comment "Sef kirmizi takim" kirmizi
    bilgi "kirmizi acildi (parola yok = kilitli)"
fi
KIRMIZI_EV=$(getent passwd kirmizi | cut -d: -f6)
chmod 700 -- "$KIRMIZI_EV"
bilgi "$KIRMIZI_EV 700"

# ------------------------------------------------------------------ 2. /opt/sef
adim "2. $SEF_KOK"
mkdir -p -- "$SEF_KOK"
chown root:sef -- "$SEF_KOK"
chmod 750 -- "$SEF_KOK"
UV_CACHE_DIR=$(mktemp -d /var/tmp/sef-kurulum-uv.XXXXXXXX)
export UV_CACHE_DIR UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1
trap 'rm -rf -- "$UV_CACHE_DIR"' EXIT
sef_kod_kur "$SEF_KOK" "$REPO" "$COMMIT"
sef_python_kur "$SEF_KOK" "$PY_KAYNAK"
sef_venv_kur "$SEF_KOK" "$UV" "$SEF_PYTHON" "$LOCK"
sef_model_kur "$SEF_KOK" "$MODEL_KAYNAK"
sef_yardimci_kur "$SEF_KOK" "$BURASI"
sef_surum_yaz "$SEF_KOK" "$UV"
grep -q "^model_sha256: $SEF_BEKLENEN_MODEL_SHA\$" "$SEF_KOK/SURUM.txt" || dur "SURUM.txt'deki model sha256 beklenen degil"

adim "   izinler: root:sef, dizin 750, dosya 640, calistirilabilir 750"
chown -R root:sef -- "$SEF_KOK"
find "$SEF_KOK" -type d -exec chmod 750 {} +
find "$SEF_KOK" -type f -perm /111 -exec chmod 750 {} +
find "$SEF_KOK" -type f ! -perm /111 -exec chmod 640 {} +
[ -z "$(find "$SEF_KOK" ! -type l -perm /007 -print -quit)" ] || dur "$SEF_KOK altinda 'digerleri' izni kaldi"
bilgi "tamam"

# ------------------------------------------------------------------ 3. sarmalayicilar
adim "3. $BIN/sef-tara, $BIN/sef-toplu"
install -o root -g root -m 755 -- "$BURASI/sef-tara" "$BIN/sef-tara"
install -o root -g root -m 755 -- "$BURASI/sef-toplu" "$BIN/sef-toplu"
bilgi "yerlestirildi"

# ------------------------------------------------------------------ 4. sudoers
adim "4. $SUDOERS"
GECICI_SUDOERS=$(mktemp)
cp -- "$BURASI/sudoers.sef-kirmizi" "$GECICI_SUDOERS"
visudo -cf "$GECICI_SUDOERS" || { rm -f -- "$GECICI_SUDOERS"; dur "visudo -cf basarisiz; sudoers yerlestirilmedi"; }
install -o root -g root -m 440 -- "$GECICI_SUDOERS" "$SUDOERS"
rm -f -- "$GECICI_SUDOERS"
visudo -c || dur "visudo -c basarisiz: $SUDOERS'i hemen inceleyin (sudo -i ile)"
bilgi "yerlestirildi, visudo -c tamam"

# ------------------------------------------------------------------ 5. SELinux
adim "5. SELinux etiketleri"
if command -v restorecon >/dev/null; then
    restorecon -RF -- "$SEF_KOK" "$BIN/sef-tara" "$BIN/sef-toplu" "$SUDOERS"
    bilgi "restorecon tamam"
else
    bilgi "restorecon yok, atlandi"
fi

adim "Kurulum bitti"
sed 's/^/    /' "$SEF_KOK/SURUM.txt"
cat <<SON

Dogrulama:   ./dogrula.sh            (sudo gerektiren kontroller sudo ister)
kirmizi'ya gecis (ornek):  sudo machinectl shell kirmizi@   ya da   sudo -iu kirmizi
kirmizi'nin kullanimi:     sudo -u sef /usr/local/bin/sef-tara < dosya
                           sudo -u sef /usr/local/bin/sef-toplu < arsiv.tar
SON
