"""Akis diyagrami (.mmd) dugumlerindeki dosya:satir atiflarini koda gore tazeler.
Etiket metni (kod satiri) dosyada eski satira EN YAKIN yerde aranir; bulunursa satir yenilenir.
Kullanim: python akis_satir_tazele.py <depo_koku> <mmd...>
"""
import re, sys, subprocess
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(sys.argv[1])
DUGUM = re.compile(r'^(\s*[a-zA-Z0-9_]+)([\[{(])"(.*)<br/>([^"<]+?):(\d+)(?:-(\d+))?"([\]})])\s*$')

def cozumle(etiket):
    return etiket.replace("#quot;", '"').replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&").strip()

def satir_bul(dosya_satirlari, metin, eski):
    adaylar = [i + 1 for i, l in enumerate(dosya_satirlari) if metin and metin in l.strip()]
    if not adaylar:
        # 'def X()' etiketi: def adi ile ara
        m = re.match(r"def\s+([\w.]+)\(\)", metin)
        if m:
            ad = m.group(1).split(".")[-1]
            adaylar = [i + 1 for i, l in enumerate(dosya_satirlari) if re.match(r"\s*def\s+" + re.escape(ad) + r"\(", l)]
    if not adaylar:
        return None
    return min(adaylar, key=lambda n: abs(n - eski))

head = subprocess.run(["git", "-C", str(KOK), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
import datetime
tarih = datetime.date.today().isoformat()
onbellek = {}
for mmd in sys.argv[2:]:
    p = Path(mmd); ham = p.read_bytes(); crlf = b"\r\n" in ham
    satirlar = ham.decode("utf-8").replace("\r\n", "\n").split("\n")
    degisti = 0; bulunamadi = []
    for k, s in enumerate(satirlar):
        m = DUGUM.match(s)
        if not m:
            continue
        on, ac, etiket, dosya, sat, sat2, kapa = m.groups()
        yol = KOK / dosya
        if yol not in onbellek:
            onbellek[yol] = yol.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").split("\n") if yol.is_file() else None
        ds = onbellek[yol]
        if ds is None:
            bulunamadi.append((on.strip(), dosya, "DOSYA YOK")); continue
        eski = int(sat)
        yeni = satir_bul(ds, cozumle(etiket), eski)
        if yeni is None:
            bulunamadi.append((on.strip(), dosya + ":" + sat, cozumle(etiket)[:60])); continue
        if yeni != eski:
            fark = yeni - eski
            yeni_sat2 = f"-{int(sat2) + fark}" if sat2 else ""
            satirlar[k] = f'{on}{ac}"{etiket}<br/>{dosya}:{yeni}{yeni_sat2}"{kapa}'
            degisti += 1
    # baslik kunyesi
    if satirlar and satirlar[0].startswith("%% koddan turetildi"):
        satirlar[0] = f"%% koddan turetildi {head} {tarih}"
    p.write_bytes(("\r\n" if crlf else "\n").join(satirlar).encode("utf-8"))
    print(f"{p.name}: {degisti} dugum tazelendi; bulunamayan {len(bulunamadi)}")
    for b in bulunamadi[:8]:
        print("   ?", b)
