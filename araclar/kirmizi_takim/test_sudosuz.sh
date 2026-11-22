#!/bin/bash
# test_sudosuz.sh - kirmizi takim altyapisinin sudo GEREKTIRMEYEN kisimlarini sinar.
#
# Ne yapar: ortak.sh'nin AYNI islevleriyle (kurulum.sh'nin kullandiklari) gecici bir klasore
# /opt/sef'in bir kopyasini kurar (kod = origin/main, python, venv, model, SURUM.txt) ve
# sarmalayicilarin kopyalarini o klasore yonlendirerek calistirir. Kopyalarda YALNIZ su
# satirlar degisir (her biri tam bir kez bulunmali, yoksa test durur):
#   readonly SEF_KOK=/opt/sef, readonly GECICI_TABAN=/var/tmp, ve bazi testlerde
#   readonly SURE_SN=300 / readonly GIRDI_SINIR_BAYT=... (siniri kucultup sinamak icin).
# Kullanicilar, sahiplik/izinler, sudoers ve kirmizi'nin erisemedigi: dogrula.sh (sudo).
#
# Kullanim: ./test_sudosuz.sh [calisma_klasoru]   (varsayilan: mktemp -d; sonunda silinir)
# Ag gerekir (venv icin PyPI). Ornek dosyalar: mingw (native DLL) ve dotnet (.NET DLL).
set -uo pipefail
BURASI=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$BURASI/../.." && pwd)
# shellcheck source=ortak.sh
source "$BURASI/ortak.sh"

UV=${UV:-$HOME/.local/bin/uv}
KULLANICI_VENV=$REPO/.venv
MODEL_KAYNAK=${MODEL_KAYNAK:-$HOME/ember2024/model/model_native.joblib}
ORNEK_NATIVE=${ORNEK_NATIVE:-/usr/x86_64-w64-mingw32/sys-root/mingw/bin/libwinpthread-1.dll}
ORNEK_NET=${ORNEK_NET:-$(ls /usr/lib64/dotnet/shared/Microsoft.NETCore.App/*/System.Runtime.dll 2>/dev/null | head -1)}
PY_ARAC="$KULLANICI_VENV/bin/python"   # test arsivlerini uretmek icin (proje ortami)

if [ $# -ge 1 ]; then CALISMA=$1; SIL=0; mkdir -p -- "$CALISMA"; else CALISMA=$(mktemp -d); SIL=1; fi
KOK="$CALISMA/opt-sef"
TABAN="$CALISMA/gecici"
SARMAL="$CALISMA/sarmal"
VERI="$CALISMA/veri"
mkdir -p -- "$KOK" "$TABAN" "$SARMAL" "$VERI"
chmod 750 -- "$KOK"
cleanup() { if [ "$SIL" -eq 1 ]; then rm -rf -- "$CALISMA"; fi; }
trap cleanup EXIT

GECEN=0; KALAN=0
gecti() { echo "GEÇTİ  $1"; GECEN=$((GECEN + 1)); }
kaldi() { echo "KALDI  $1${2:+  ($2)}"; KALAN=$((KALAN + 1)); }
kontrol() { local ad=$1; shift; if "$@"; then gecti "$ad"; else kaldi "$ad"; fi; }

# ---------------------------------------------------------------- kurulum (ortak.sh)
adim "Kopya kurulum: $KOK"
COMMIT=$(git -C "$REPO" rev-parse origin/main) || dur "origin/main yok"
bilgi "origin/main = $COMMIT"
[ "$(sef_meta_model_sha "$REPO" "$COMMIT")" = "$SEF_BEKLENEN_MODEL_SHA" ] || dur "meta model_sha256 beklenenden farkli"
sef_freeze_ayni "$UV" "$KULLANICI_VENV/bin/python" "$BURASI/gereksinimler.lock" || dur "lock, uv ortaminin freeze'i ile ayni degil"
PY_KAYNAK=$(dirname "$(sed -n 's/^home = //p' "$KULLANICI_VENV/pyvenv.cfg")")
export UV_CACHE_DIR="$CALISMA/uv-onbellek" UV_PYTHON_DOWNLOADS=never UV_NO_PROGRESS=1
sef_kod_kur "$KOK" "$REPO" "$COMMIT"
sef_python_kur "$KOK" "$PY_KAYNAK"
sef_venv_kur "$KOK" "$UV" "$SEF_PYTHON" "$BURASI/gereksinimler.lock"
sef_model_kur "$KOK" "$MODEL_KAYNAK"
sef_yardimci_kur "$KOK" "$BURASI"
sef_surum_yaz "$KOK" "$UV"
rm -rf -- "$UV_CACHE_DIR"

# sarmal_kopya AD HEDEF [DEGISKEN=DEGER ...]: sarmalayicinin test kopyasi.
sarmal_kopya() {
    local ad=$1 hedef=$2; shift 2
    cp -- "$BURASI/$ad" "$hedef"
    local degisim
    for degisim in "SEF_KOK=$KOK" "GECICI_TABAN=$TABAN" "$@"; do
        local d=${degisim%%=*} v=${degisim#*=}
        [ "$(grep -c "^readonly $d=" "$hedef")" -eq 1 ] || dur "$ad: 'readonly $d=' satiri tam bir kez yok"
        sed -i "s|^readonly $d=.*|readonly $d=$v|" "$hedef"
    done
    chmod 755 -- "$hedef"
}
sarmal_kopya sef-tara "$SARMAL/sef-tara"
sarmal_kopya sef-toplu "$SARMAL/sef-toplu"
sarmal_kopya sef-tara "$SARMAL/sef-tara-kucuk" "GIRDI_SINIR_BAYT=1000"
sarmal_kopya sef-toplu "$SARMAL/sef-toplu-kucuk" "GIRDI_SINIR_BAYT=1000"
sarmal_kopya sef-tara "$SARMAL/sef-tara-kisa" "SURE_SN=3"
sarmal_kopya sef-tara "$SARMAL/sef-tara-cokkisa" "SURE_SN=1"
TARA="$SARMAL/sef-tara"; TOPLU="$SARMAL/sef-toplu"

# Test arsivleri (proje ortaminin python'u; tarfile ile, root gerekmeden aygit uyesi dahil).
[ -f "$ORNEK_NATIVE" ] || dur "native ornek yok: $ORNEK_NATIVE"
[ -f "$ORNEK_NET" ] || dur ".NET ornek yok: $ORNEK_NET"
printf 'bu bir PE degil\n' >"$VERI/metin.txt"
: >"$VERI/bos"
"$PY_ARAC" -I - "$VERI" "$ORNEK_NATIVE" "$ORNEK_NET" <<'EOF' || dur "test arsivleri uretilemedi"
import io, sys, tarfile
veri, native, net = sys.argv[1:4]
def yaz(ad, uyeler, mod="w"):
    with tarfile.open(f"{veri}/{ad}", mod) as t:
        for u in uyeler:
            ti, icerik = u
            if icerik is not None:
                ti.size = len(icerik)
                t.addfile(ti, io.BytesIO(icerik))
            else:
                t.addfile(ti)
def dosya(ad, icerik):
    return (tarfile.TarInfo(ad), icerik)
def ozel(ad, tur, hedef=""):
    ti = tarfile.TarInfo(ad); ti.type = tur; ti.linkname = hedef
    if tur == tarfile.CHRTYPE:
        ti.devmajor, ti.devminor = 1, 3
    return (ti, None)
n = open(native, "rb").read(); d = open(net, "rb").read()
yaz("native.tar", [dosya("a/native.dll", n), dosya("a/not.txt", b"metin")])
yaz("net.tar", [dosya("native.dll", n), dosya("net.dll", d)])
yaz("native.tar.gz", [dosya("native.dll", n)], "w:gz")
yaz("noktanokta.tar", [dosya("../x", b"x")])
yaz("ilk_iyi_sonra_kotu.tar", [dosya("iyi.dll", n), dosya("../x", b"x")])
yaz("mutlak.tar", [dosya("/mutlak_x", b"x")])
yaz("bag_mutlak.tar", [ozel("bag", tarfile.SYMTYPE, "/etc/passwd")])
yaz("bag_disari.tar", [ozel("bag", tarfile.SYMTYPE, "../../disari")])
yaz("aygit.tar", [ozel("null", tarfile.CHRTYPE)])
yaz("bomba.tar.gz", [dosya("sifir", bytes(5000))], "w:gz")   # sikistirilmis kucuk, acik 5000 bayt
EOF

taban_bos() { [ -z "$(ls -A -- "$TABAN")" ]; }

# calistir_kaydet AD KOMUT... < girdi: stdout/stderr/cikis kodunu $VERI/AD.{out,err,rc}'ye yazar.
calistir_kaydet() {
    local ad=$1; shift
    "$@" >"$VERI/$ad.out" 2>"$VERI/$ad.err"
    echo $? >"$VERI/$ad.rc"
}
rc() { cat "$VERI/$1.rc"; }
icerir() { grep -q -- "$2" "$VERI/$1"; }

# ---------------------------------------------------------------- sef-tara
adim "sef-tara"
calistir_kaydet surum "$TARA" --surum </dev/null
kontrol "sef-tara --surum: cikis 0, sinirlar ve SURUM.txt (model sha) yazili" \
    eval '[ "$(rc surum)" = 0 ] && icerir surum.out "300 sn" && icerir surum.out "8 GiB" && icerir surum.out "2 GiB" && icerir surum.out "model_sha256: $SEF_BEKLENEN_MODEL_SHA" && icerir surum.out "kod_commit: $COMMIT"'

# Dogrudan (sarmalayicisiz) baslatici: karsilastirma tabani.
"$KOK/venv/bin/python" -I -B "$KOK/calistir.py" tahmin_et "$ORNEK_NATIVE" >"$VERI/dogrudan.out" 2>"$VERI/dogrudan.err"
DOGRUDAN_RC=$?
calistir_kaydet native "$TARA" <"$ORNEK_NATIVE"
kontrol "sef-tara native DLL: cikis kodu ve skor satiri dogrudan calistirmayla ayni (rc $(rc native))" \
    eval '[ "$(rc native)" = "$DOGRUDAN_RC" ] && [ "$(grep "^Zararli olasiligi" "$VERI/native.out")" = "$(grep "^Zararli olasiligi" "$VERI/dogrudan.out")" ] && icerir native.out "^Zararli olasiligi"'
kontrol "sef-tara native DLL: stdout, dosya adi satiri disinda dogrudan calistirmayla birebir" \
    eval 'diff <(grep -v "^Dosya:" "$VERI/native.out") <(grep -v "^Dosya:" "$VERI/dogrudan.out") >/dev/null && diff "$VERI/native.err" "$VERI/dogrudan.err" >/dev/null'

calistir_kaydet net "$TARA" <"$ORNEK_NET"
kontrol ".NET DLL: cikis 2 (BELIRSIZ), tahmin_et mesaji gecti" eval '[ "$(rc net)" = 2 ] && icerir net.out "BELIRSIZ"'
calistir_kaydet metin "$TARA" <"$VERI/metin.txt"
kontrol "PE olmayan girdi: cikis 1, tahmin_et'in stderr mesaji gecti" eval '[ "$(rc metin)" = 1 ] && icerir metin.err "PE degil"'
calistir_kaydet bos "$TARA" <"$VERI/bos"
kontrol "bos girdi: cikis 1 (rc $(rc bos))" eval '[ "$(rc bos)" = 1 ]'
calistir_kaydet ozet "$TARA" --ozet <"$ORNEK_NATIVE"
kontrol "--ozet: stderr'deki sha256 girdi dosyasininkiyle ayni (ikili veri bozulmadan geldi)" \
    eval 'icerir ozet.err "sha256 $(sef_sha "$ORNEK_NATIVE")" && [ "$(rc ozet)" = "$DOGRUDAN_RC" ]'
calistir_kaydet arg "$TARA" --baska </dev/null
kontrol "bilinmeyen arguman: cikis 64" eval '[ "$(rc arg)" = 64 ]'
calistir_kaydet arg2 "$TARA" --ozet --ozet </dev/null
kontrol "fazla arguman: cikis 64" eval '[ "$(rc arg2)" = 64 ]'
calistir_kaydet buyuk "$SARMAL/sef-tara-kucuk" <"$ORNEK_NATIVE"
kontrol "girdi siniri (test: 1000 bayt) asildi: cikis 64, GİRDİ REDDEDİLDİ" \
    eval '[ "$(rc buyuk)" = 64 ] && icerir buyuk.err "GİRDİ REDDEDİLDİ"'
head -c 1000 "$ORNEK_NATIVE" >"$VERI/tam1000"
calistir_kaydet sinirda "$SARMAL/sef-tara-kucuk" <"$VERI/tam1000"
kontrol "girdi tam sinirda (1000 bayt): reddedilmez, tahmin_et calisir (rc $(rc sinirda))" \
    eval '[ "$(rc sinirda)" != 64 ]'
kontrol "gecici klasor her cagridan sonra silindi" taban_bos

# Zaman asimi: okuma asamasinda (stdin kapanmiyor) ve tarama asamasinda.
{ sleep 8; } | calistir_kaydet zaman_okuma "$SARMAL/sef-tara-kisa"
kontrol "zaman asimi (okuma, test: 3 sn): cikis 124, ZAMAN AŞIMI" \
    eval '[ "$(rc zaman_okuma)" = 124 ] && icerir zaman_okuma.err "ZAMAN AŞIMI"'
calistir_kaydet zaman_tarama "$SARMAL/sef-tara-cokkisa" <"$ORNEK_NATIVE"
kontrol "zaman asimi (tarama, test: 1 sn; model yuklemesi ~1,5 sn): cikis 124, ZAMAN AŞIMI" \
    eval '[ "$(rc zaman_tarama)" = 124 ] && icerir zaman_tarama.err "ZAMAN AŞIMI"'
kontrol "zaman asimindan sonra gecici klasor silindi" taban_bos

# Calisirken: gecici klasor 700, girdi 600, sahibi calistiran.
{ sleep 2; cat "$ORNEK_NATIVE"; } | "$TARA" >/dev/null 2>&1 &
ARKA=$!
sleep 1
D=$(ls -d "$TABAN"/sef-tara.* 2>/dev/null | head -1)
IZIN_D=$(stat -c '%a %u' -- "$D" 2>/dev/null); IZIN_G=$(stat -c '%a %u' -- "$D/girdi" 2>/dev/null)
wait "$ARKA"
kontrol "calisirken gecici klasor 700 ve girdi 600, sahibi calistiran kullanici ($IZIN_D / $IZIN_G)" \
    eval '[ "$IZIN_D" = "700 $(id -u)" ] && [ "$IZIN_G" = "600 $(id -u)" ]'

# Sinyal: sarmalayici TERM alinca cocugunu sonlandirir, klasoru siler.
mkfifo "$VERI/fifo"
"$TARA" <"$VERI/fifo" >/dev/null 2>"$VERI/sinyal.err" &
SARMAL_PID=$!
exec 4>"$VERI/fifo"          # yazan ucu acik tut: sarmalayici okumada bekler
sleep 1
COCUKLAR=""
for p in $(pgrep -P "$SARMAL_PID"); do COCUKLAR+="$p $(pgrep -P "$p" | tr '\n' ' ')"; done
kill -TERM "$SARMAL_PID"
wait "$SARMAL_PID"; SINYAL_RC=$?
exec 4>&-
sleep 0.5
CANLI=""
for p in $COCUKLAR; do if kill -0 "$p" 2>/dev/null; then CANLI+="$p "; fi; done
kontrol "TERM: sarmalayici 143 ile cikti ($SINYAL_RC), cocuklari [${COCUKLAR% }] kalmadi, gecici klasor silindi" \
    eval '[ "$SINYAL_RC" = 143 ] && [ -n "$COCUKLAR" ] && [ -z "$CANLI" ] && taban_bos'

# Eski kalinti temizligi: 60 dk'dan eski, ayni kullanicinin klasoru silinir.
mkdir -p "$TABAN/sef-tara.ESKIKLAS"; touch -d '2 hours ago' "$TABAN/sef-tara.ESKIKLAS"
"$TARA" <"$VERI/metin.txt" >/dev/null 2>&1
kontrol "SIGKILL kalintisi (60 dk'dan eski) sonraki cagrida silindi" taban_bos

# ---------------------------------------------------------------- sef-toplu
adim "sef-toplu"
calistir_kaydet tsurum "$TOPLU" --surum </dev/null
kontrol "sef-toplu --surum: cikis 0, sinirlar ve SURUM.txt" \
    eval '[ "$(rc tsurum)" = 0 ] && icerir tsurum.out "300 sn" && icerir tsurum.out "model_sha256: $SEF_BEKLENEN_MODEL_SHA"'
calistir_kaydet tnative "$TOPLU" <"$VERI/native.tar"
kontrol "native.tar (native DLL + metin): cikis $DOGRUDAN_RC (dogrudan tek dosyayla ayni), metin 'PE degil'" \
    eval '[ "$(rc tnative)" = "$DOGRUDAN_RC" ]'
calistir_kaydet tnet "$TOPLU" --liste <"$VERI/net.tar"
kontrol "net.tar (+ .NET DLL) --liste: cikis 2 (en kotu sonuc BELIRSIZ), dosya listede" \
    eval '[ "$(rc tnet)" = 2 ] && icerir tnet.out "net.dll"'
calistir_kaydet tgz "$TOPLU" <"$VERI/native.tar.gz"
kontrol "gzip'li tar acilir: cikis $DOGRUDAN_RC" eval '[ "$(rc tgz)" = "$DOGRUDAN_RC" ]'
# Mutlak yol: 'data' suzgeci reddetmez, bastaki '/'yi kirpip hedefin ICINE yazar (PEP 706
# belgelenmis davranis). Icerik PE degil -> toplu_tahmin "hic PE siniflanmadi" -> 1.
calistir_kaydet tmutlak "$TOPLU" <"$VERI/mutlak.tar"
kontrol "mutlak.tar: '/' kirpilir, hedefin icinde kalir (cikis $(rc tmutlak), 64 degil; /mutlak_x yok)" \
    eval '[ "$(rc tmutlak)" = 1 ] && [ ! -e /mutlak_x ]'
for a in noktanokta bag_mutlak bag_disari aygit; do
    calistir_kaydet "t$a" "$TOPLU" <"$VERI/$a.tar"
    kontrol "$a.tar reddedildi: cikis 64, ARŞİV REDDEDİLDİ" \
        eval '[ "$(rc t$a)" = 64 ] && icerir t$a.err "ARŞİV REDDEDİLDİ"'
done
kontrol "'../x' disari yazilmadi" eval '[ ! -e "$CALISMA/x" ] && [ ! -e "$TABAN/x" ] && [ ! -e /mutlak_x ]'
calistir_kaydet tmetin "$TOPLU" <"$VERI/metin.txt"
kontrol "tar olmayan girdi: cikis 64" eval '[ "$(rc tmetin)" = 64 ]'
calistir_kaydet tbos "$TOPLU" <"$VERI/bos"
kontrol "bos girdi: cikis 64" eval '[ "$(rc tbos)" = 64 ]'
calistir_kaydet tbuyuk "$SARMAL/sef-toplu-kucuk" <"$VERI/native.tar"
kontrol "arsiv siniri (test: 1000 bayt) asildi: cikis 64, GİRDİ REDDEDİLDİ" \
    eval '[ "$(rc tbuyuk)" = 64 ] && icerir tbuyuk.err "GİRDİ REDDEDİLDİ"'
calistir_kaydet tbomba "$SARMAL/sef-toplu-kucuk" <"$VERI/bomba.tar.gz"
kontrol "acik boyut siniri (5000 > 1000, arsiv kucuk): cikis 64" \
    eval '[ "$(rc tbomba)" = 64 ] && icerir tbomba.err "acik boyut"'
calistir_kaydet targ "$TOPLU" --liste --baska </dev/null
kontrol "bilinmeyen arguman: cikis 64" eval '[ "$(rc targ)" = 64 ]'
kontrol "gecici klasor her cagridan sonra silindi" taban_bos

# Hepsi ya da hic: ilk uye gecerli, ikincisi '../x' -> hedef bos kalmali.
mkdir -p "$VERI/hedef"
"$KOK/venv/bin/python" -I -B "$KOK/arsiv_ac.py" "$VERI/ilk_iyi_sonra_kotu.tar" "$VERI/hedef" 1000000 2>/dev/null
R=$?
kontrol "arsiv_ac: bir uye reddedilince hicbir sey acilmaz (cikis $R, hedef bos)" \
    eval '[ "$R" = 64 ] && [ -z "$(ls -A "$VERI/hedef")" ]'

# ---------------------------------------------------------------- kurulum idempotent mi
adim "ortak.sh islevleri ikinci kez (idempotent)"
export UV_CACHE_DIR="$CALISMA/uv-onbellek"
IKINCI=$( { sef_kod_kur "$KOK" "$REPO" "$COMMIT"; sef_python_kur "$KOK" "$PY_KAYNAK"; \
    sef_venv_kur "$KOK" "$UV" "$SEF_PYTHON" "$BURASI/gereksinimler.lock"; sef_model_kur "$KOK" "$MODEL_KAYNAK"; } 2>&1)
rm -rf -- "$UV_CACHE_DIR"
kontrol "ikinci kurulum her adimi atladi (4/4 'atlandi')" eval '[ "$(grep -c atlandi <<<"$IKINCI")" = 4 ]'

echo
echo "SONUC: $GECEN GEÇTİ, $KALAN KALDI"
[ "$KALAN" -eq 0 ]
