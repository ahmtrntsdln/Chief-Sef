# ortak.sh - kurulum.sh ile test_sudosuz.sh'nin ORTAK kurma adimlari (source ile yuklenir).
# Neden ortak: sudo'suz test, kurulumun /opt/sef'e yaptigini ayni islevlerle gecici bir
# klasore yapar; iki ayri kopya olsaydi test baska bir seyi sinardi.
# Bu dosyadaki islevler root gerektirmez; sahiplik/izin, kullanici ve sudoers kurulum.sh'de.

# Kurulum ancak bu modelle yapilir (Kural 10; meta veri ile de karsilastirilir).
readonly SEF_BEKLENEN_MODEL_SHA=f6b74df812f02d75a28a003b33d22294b799a94f12cf0e4ec2d5d6c9569ba536
readonly SEF_PYTHON_SURUM=3.13.7

# git'i baska kullanici olarak calistirmak icin onek (kurulum.sh: runuser -u <kullanici> --).
SEF_GIT_ONEK=()

adim() { printf '\n==> %s\n' "$*"; }
bilgi() { printf '    %s\n' "$*"; }
dur() { printf '\nDURDU: %s\n' "$*" >&2; exit 1; }

sef_sha() { sha256sum -- "$1" | cut -d' ' -f1; }

# Bir commit'teki model_native_meta.json'un model_sha256 degeri.
sef_meta_model_sha() {
    local repo=$1 commit=$2
    "${SEF_GIT_ONEK[@]}" git -C "$repo" show "$commit:gumruk_memuru/model_native_meta.json" \
        | grep -o '"model_sha256": *"[0-9a-f]*"' | grep -o '[0-9a-f]\{64\}'
}

# lock dosyasindaki paket listesi (yorumsuz) ile bir ortamin uv pip freeze'i ayni mi.
sef_freeze_ayni() {
    local uv=$1 python=$2 lock=$3
    diff <(grep -v '^#' "$lock") <("$uv" pip freeze --no-config --python "$python" 2>/dev/null) >/dev/null
}

# sef_kod_kur KOK REPO COMMIT: commit'in agacini (git archive) KOK/kod'a koyar.
sef_kod_kur() {
    local kok=$1 repo=$2 commit=$3
    if [ -f "$kok/kod.commit" ] && [ "$(cat "$kok/kod.commit")" = "$commit" ] && [ -d "$kok/kod" ]; then
        bilgi "kod zaten $commit, atlandi"; return 0
    fi
    rm -rf -- "$kok/kod.yeni"
    mkdir -p -- "$kok/kod.yeni"
    "${SEF_GIT_ONEK[@]}" git -C "$repo" archive --format=tar "$commit" \
        | tar -x --no-same-owner -C "$kok/kod.yeni"
    local d=("${PIPESTATUS[@]}")
    [ "${d[0]}" -eq 0 ] && [ "${d[1]}" -eq 0 ] || dur "git archive | tar basarisiz (${d[*]})"
    [ -f "$kok/kod.yeni/gumruk_memuru/tahmin_et.py" ] || dur "kod.yeni'de tahmin_et.py yok"
    rm -rf -- "$kok/kod"
    mv -- "$kok/kod.yeni" "$kok/kod"
    echo "$commit" >"$kok/kod.commit"
    bilgi "kod: $commit -> $kok/kod"
}

# sef_python_kur KOK KAYNAK: uv'nin kurdugu CPython klasorunu (kullanicinin uv ortaminin
# yorumlayicisi) KOK/python/ altina kopyalar. Sonuc yolu: SEF_PYTHON degiskeni.
sef_python_kur() {
    local kok=$1 kaynak=$2 ad hedef
    ad=$(basename -- "$kaynak")
    hedef="$kok/python/$ad"
    SEF_PYTHON="$hedef/bin/python3.13"
    if [ -x "$SEF_PYTHON" ] && [ "$("$SEF_PYTHON" -I -c 'import platform; print(platform.python_version())')" = "$SEF_PYTHON_SURUM" ]; then
        bilgi "python zaten $SEF_PYTHON_SURUM ($hedef), atlandi"; return 0
    fi
    rm -rf -- "$hedef.yeni" "$hedef"
    mkdir -p -- "$kok/python"
    cp -r --no-preserve=ownership -- "$kaynak" "$hedef.yeni"
    mv -- "$hedef.yeni" "$hedef"
    local s
    s=$("$SEF_PYTHON" -I -c 'import platform; print(platform.python_version())') || dur "kopyalanan python calismiyor"
    [ "$s" = "$SEF_PYTHON_SURUM" ] || dur "python surumu $s, beklenen $SEF_PYTHON_SURUM"
    bilgi "python $s -> $hedef"
}

# sef_venv_kur KOK UV PYTHON LOCK: KOK/venv, lock'taki paketlerle birebir (uv pip sync).
# Ag gerekir (PyPI). UV_CACHE_DIR cagiran tarafindan gecici klasore ayarlanmali.
sef_venv_kur() {
    local kok=$1 uv=$2 python=$3 lock=$4 venv="$1/venv"
    if [ -x "$venv/bin/python" ] && sef_freeze_ayni "$uv" "$venv/bin/python" "$lock"; then
        bilgi "venv zaten lock ile ayni, atlandi"; return 0
    fi
    rm -rf -- "$venv"
    "$uv" venv --no-config --python "$python" "$venv" || dur "uv venv basarisiz"
    "$uv" pip sync --no-config --strict --python "$venv/bin/python" "$lock" || dur "uv pip sync basarisiz"
    sef_freeze_ayni "$uv" "$venv/bin/python" "$lock" || dur "venv paketleri lock ile ayni degil"
    bilgi "venv: $(grep -vc '^#' "$lock") paket, lock ile birebir"
}

# sef_model_kur KOK KAYNAK: modeli KOK/model/'e kopyalar; sha256 beklenenden farkliysa DURUR.
sef_model_kur() {
    local kok=$1 kaynak=$2 hedef="$1/model/model_native.joblib"
    if [ -f "$hedef" ] && [ "$(sef_sha "$hedef")" = "$SEF_BEKLENEN_MODEL_SHA" ]; then
        bilgi "model zaten yerinde (sha256 tutuyor), atlandi"; return 0
    fi
    mkdir -p -- "$kok/model"
    rm -f -- "$hedef.yeni"
    cp --no-preserve=all -- "$kaynak" "$hedef.yeni"
    local s
    s=$(sef_sha "$hedef.yeni")
    if [ "$s" != "$SEF_BEKLENEN_MODEL_SHA" ]; then
        rm -f -- "$hedef.yeni"
        dur "kopyalanan modelin sha256'si $s, beklenen $SEF_BEKLENEN_MODEL_SHA"
    fi
    mv -- "$hedef.yeni" "$hedef"
    bilgi "model: sha256 $s -> $hedef"
}

# sef_yardimci_kur KOK BETIK_DIZINI: baslatici ve arsiv acici.
sef_yardimci_kur() {
    local kok=$1 dizin=$2
    install -m 640 -- "$dizin/calistir.py" "$kok/calistir.py"
    install -m 640 -- "$dizin/arsiv_ac.py" "$kok/arsiv_ac.py"
    bilgi "calistir.py, arsiv_ac.py -> $kok"
}

# sef_surum_yaz KOK UV: KOK/SURUM.txt (sef-tara --surum bunu gosterir).
sef_surum_yaz() {
    local kok=$1 uv=$2
    {
        echo "kod_commit: $(cat "$kok/kod.commit") (origin/main, git archive; kod degistirilmedi)"
        echo "model_sha256: $(sef_sha "$kok/model/model_native.joblib")"
        echo "python: $("$kok/venv/bin/python" -I -c 'import platform; print(platform.python_version())')"
        echo "paketler:"
        "$uv" pip freeze --no-config --python "$kok/venv/bin/python" 2>/dev/null | sed 's/^/  /'
        echo "kurulum: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    } >"$kok/SURUM.txt.yeni"
    mv -- "$kok/SURUM.txt.yeni" "$kok/SURUM.txt"
    bilgi "SURUM.txt yazildi"
}
