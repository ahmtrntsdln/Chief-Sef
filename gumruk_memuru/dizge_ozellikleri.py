"""
Sef Projesi - Dizge (string) ozellikleri, EMBER2024 / thrember ile BIREBIR

EMBER2024'un `strings` grubunu bu makinedeki dosyalar icin AYNI sekilde
hesaplar (Kritik Kural 1). Kural ve regex'ler thrember'dan birebir alindi:
  https://github.com/FutureComputing4AI/EMBER2024  src/thrember/features.py
  (StringExtractor), Apache License 2.0.
Regex'ler kaynak dosyadan programla kopyalandi; elle duzeltme YAPILMADI.
thrember'daki tuhafliklar bilerek korunuyor (ornek: "email_addr" deseni
"mac_addr" ile ayni), yoksa iki taraf farkli olcer.

.NET'te tip/metod/P/Invoke adlari metadata'da ASCII durdugu icin bu sayimlar
.NET'in icinden kismi bir sinyal verir (ornek: "keyboard", "clipboard").
"""

import re

import numpy as np

DIZGE_DESENI = re.compile(b"[\x20-\x7f]{5,}")

REGEXLER = {
    # IOC strings, from:
    # https://www.stackzero.net/python-string-analysis/
    # https://engineering.avast.io/yara-in-search-of-regular-expressions/
    "url": re.compile("\\b(?:http|https|ftp):\\/\\/[a-zA-Z0-9-._~:?#[\\]@!$&'()*+,;=]+"),
    "ipv4_addr": re.compile("\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b"),
    "ipv6_addr": re.compile("\\b(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}\\b|\\b(?:[A-Fa-f0-9]{1,4}:){1,7}:\\b|\\b:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4}){1,6}\\b"),
    "mac_addr": re.compile("\\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\\b"),
    "email_addr": re.compile("\\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\\b"),
    "btc_wallet": re.compile("[13][a-km-zA-HJ-NP-Z1-9]{25,34}"),

    # Windows strings
    "file_path": re.compile("\\bC:/"),
    "dos_msg": re.compile("!This program "),
    "registry_key": re.compile("\\b(?:KHEY_|KHLM|HKCU)"),

    # Linux strings
    "/dev/": re.compile("/dev/"),
    "/proc/": re.compile("/proc/"),
    "/bin/": re.compile("/bin/"),
    "/usr/": re.compile("/usr/"),
    "/tmp/": re.compile("/tmp/"),

    # PDF strings
    "/URI": re.compile("/URI"),
    "/FlateDecode": re.compile("/FlateDecode"),
    "/EmbeddedFile": re.compile("/EmbeddedFile"),

    # HTML and JS strings
    "html": re.compile("html", re.IGNORECASE),
    "javascript": re.compile("javascript", re.IGNORECASE),
    "<script": re.compile("<script", re.IGNORECASE),
    ".click(": re.compile(".click", re.IGNORECASE),
    "onlick": re.compile("onclick", re.IGNORECASE),

    # Powershell strings
    "powershell": re.compile("powershell", re.IGNORECASE),
    "Invoke-Expression": re.compile("Invoke-Expression"),
    "Invoke-Command": re.compile("Invoke-Command"),
    "Start-process": re.compile("Start-process"),

    # Network strings
    "get": re.compile("GET /", re.IGNORECASE),
    "post": re.compile("POST /", re.IGNORECASE),
    "http": re.compile("HTTP/", re.IGNORECASE),
    "http://": re.compile("http://", re.IGNORECASE),
    "https://": re.compile("https://", re.IGNORECASE),
    "ftp": re.compile("ftp:", re.IGNORECASE),
    "useragent": re.compile("User-Agent", re.IGNORECASE),
    "cookie": re.compile("cookie", re.IGNORECASE),
    "internet": re.compile("internet", re.IGNORECASE),
    "download": re.compile("download", re.IGNORECASE),
    "connect": re.compile("connect", re.IGNORECASE),

    # Cryptography and encoding strings
    "base64": re.compile("base64", re.IGNORECASE),
    "base64string": re.compile("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
    "crypt": re.compile("crypt"),
    "encode": re.compile("encode", re.IGNORECASE),
    "decode": re.compile("decode", re.IGNORECASE),

    # Miscellaneous strings
    "cache": re.compile("cache", re.IGNORECASE),
    "certificate": re.compile("certificate", re.IGNORECASE),
    "clipboard": re.compile("clipboard", re.IGNORECASE),
    "command": re.compile("command", re.IGNORECASE),
    "create": re.compile("create", re.IGNORECASE),
    "debug": re.compile("debug", re.IGNORECASE),
    "delete": re.compile("delete", re.IGNORECASE),
    "desktop": re.compile("desktop", re.IGNORECASE),
    "directory": re.compile("directory", re.IGNORECASE),
    "disk": re.compile("disk", re.IGNORECASE),
    "environment": re.compile("environment", re.IGNORECASE),
    "enum": re.compile("enum", re.IGNORECASE),
    "exit": re.compile("exit", re.IGNORECASE),
    "file": re.compile("file", re.IGNORECASE),
    "hostname": re.compile("hostname", re.IGNORECASE),
    "install": re.compile("install", re.IGNORECASE),
    "hidden": re.compile("hidden", re.IGNORECASE),
    "keyboard": re.compile("keyboard", re.IGNORECASE),
    "memory": re.compile("memory", re.IGNORECASE),
    "module": re.compile("module", re.IGNORECASE),
    "mutex": re.compile("mutex", re.IGNORECASE),
    "password": re.compile("password", re.IGNORECASE),
    "privilege": re.compile("privilege", re.IGNORECASE),
    "process": re.compile("process", re.IGNORECASE),
    "remote": re.compile("remote", re.IGNORECASE),
    "resource": re.compile("resource", re.IGNORECASE),
    "security": re.compile("security", re.IGNORECASE),
    "service": re.compile("service", re.IGNORECASE),
    "shell": re.compile("shell", re.IGNORECASE),
    "snapshot": re.compile("snapshot", re.IGNORECASE),
    "system": re.compile("system", re.IGNORECASE),
    "thread": re.compile("thread", re.IGNORECASE),
    "token": re.compile("token", re.IGNORECASE),
    "wallet": re.compile("wallet", re.IGNORECASE),
    "window": re.compile("window", re.IGNORECASE),
}


def _sutun_adi(ad: str) -> str:
    # "http" ve "http://" ayri regex'ler; "://" korunmazsa ayni sutuna duserler
    return "DZ_" + re.sub(r"[^0-9A-Za-z]+", "_", ad.replace("://", "_url")).strip("_")


SAYIM_SUTUNLARI = {ad: _sutun_adi(ad) for ad in sorted(REGEXLER)}
assert len(set(SAYIM_SUTUNLARI.values())) == len(SAYIM_SUTUNLARI), "sutun adi cakismasi"
DIZGE_SUTUNLARI = ["DZ_sayi", "DZ_ort_uzunluk", "DZ_entropi"] + list(SAYIM_SUTUNLARI.values())


def _sutunlara(numstrings, avlength, entropi, string_counts) -> dict:
    satir = {"DZ_sayi": numstrings, "DZ_ort_uzunluk": round(avlength, 4),
             "DZ_entropi": round(entropi, 4)}
    for ad, sutun in SAYIM_SUTUNLARI.items():
        satir[sutun] = string_counts.get(ad, 0)
    return satir


def ham_dizge_ozellikleri(bytez: bytes) -> dict:
    """thrember StringExtractor.raw_features'in bu projede kullanilan alanlari,
    ayni algoritmayla (dizge kurali, entropi, regex basina 'eslesen dizge' sayisi)."""
    dizgeler = DIZGE_DESENI.findall(bytez)
    if dizgeler:
        avlength = sum(len(s) for s in dizgeler) / len(dizgeler)
        c = np.bincount(np.frombuffer(b"".join(dizgeler), dtype=np.uint8) - 0x20, minlength=96)
        p = c.astype(np.float32) / c.sum()
        wh = np.where(c)[0]
        entropi = float(np.sum(-p[wh] * np.log2(p[wh])))
    else:
        avlength, entropi = 0, 0.0
    string_counts = {}
    for s in (d.decode() for d in dizgeler):
        for ad, desen in REGEXLER.items():
            if re.search(desen, s):
                string_counts[ad] = string_counts.get(ad, 0) + 1
    return {"numstrings": len(dizgeler), "avlength": avlength,
            "entropy": entropi, "string_counts": string_counts}


def dosyadan_dizge_ozellikleri(bytez: bytes) -> dict:
    h = ham_dizge_ozellikleri(bytez)
    return _sutunlara(h["numstrings"], h["avlength"], h["entropy"], h["string_counts"])


def kayittan_dizge_ozellikleri(kayit: dict) -> dict:
    """EMBER2024 ham JSON kaydindan ayni sutunlar (EMBER 2018'de bu alan yok)."""
    s = kayit["strings"]
    return _sutunlara(s["numstrings"], s["avlength"], s["entropy"], s.get("string_counts", {}))
