"""
Is 7 (a) yardimci - belgelerden aday sayilari cikarir (siniflama envanter.py'de).
Aday: binlik ayracli (959.738 / 959,738), 1000 ve ustu tam sayi, K / M / bin / milyon ekli, k/n kesri.
Kullanim: python envanter_aday.py   -> stdout (deger, adet, kaynaklar)
"""

import os
import re
import sys
from collections import defaultdict

DEPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
SITE = os.path.join(os.path.expanduser("~"), "CLionProjects", "ahmtrntsdln.github.io")
KAYNAKLAR = [os.path.join(DEPO, a) for a in ("README.md", "README.tr.md", "CLAUDE.md", "GELISIM_SURECI.md")] + \
    [os.path.join(SITE, a) for a in ("projects/chief-sef.html", "en/projects/chief-sef.html", "notes/net-kor-nokta.html",
                                     "en/notes/dotnet-blind-spot.html", "notes/zaman-ekseni.html", "en/notes/temporal-split.html",
                                     "index.html", "en/index.html", "notes/index.html", "en/notes/index.html")]

DESEN = re.compile(r"(?<![\d.,/])(\d{1,3}(?:[.,]\d{3})+|\d{4,})(?![\d]|[.,]\d)([\s-]*(?:K|M|bin(?:den|de|i|in|lik)?|milyon(?:dan|da|u|un|luk)?|thousand|million)\b)?"
                   r"|(?<![\d.,])(\d+(?:[.,]\d+)?)[\s-]*(K|M|bin(?:den|de|i|in|lik)?|milyon(?:dan|da|u|un|luk)?|thousand|million)\b"
                   r"|(?<![\d.,])(\d[\d.,]*)\s*/\s*(\d[\d.,]*)(?![\d])")


def adaylar(satir):
    for m in DESEN.finditer(satir):
        yield m.group(0)


if __name__ == "__main__":
    sayac = defaultdict(list)
    for yol in KAYNAKLAR:
        with open(yol, encoding="utf-8") as f:
            for i, s in enumerate(f, 1):
                for a in adaylar(s):
                    sayac[a.strip()].append(f"{os.path.basename(os.path.dirname(yol)) or ''}/{os.path.basename(yol)}:{i}")
    for a, yerler in sorted(sayac.items(), key=lambda x: -len(x[1])):
        print(f"{a!r:>22} {len(yerler):>3}  {', '.join(yerler[:3])}")
    print(len(sayac), "farkli aday", sum(len(v) for v in sayac.values()), "gecis", file=sys.stderr)
