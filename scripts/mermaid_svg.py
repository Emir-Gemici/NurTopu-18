#!/usr/bin/env python3
"""Mermaid .mmd → .svg, Chrome headless ile (mermaid-cli / pandoc YOK).

NEDEN: FDR §3.3.4.1.17 akış diyagramları 5 Eylül'de "SVG render ÖLÇÜLEMEDİ
(mmdc/pandoc yok)" kaldı. Makinede Chrome var; mermaid.js CDN'den yüklenir,
diyagram tarayıcıda çizilir, DOM `--dump-dom` ile alınır, `<svg>` parçası
dosyaya yazılır. SVG'ler `scripts/fdr_pdf_uret.py` ile PDF'e `<img>` olarak
girer (Chrome, SVG'yi vektör basar).

Yöntem (her .mmd için):
  1. Geçici HTML: mermaid.min.js (CDN) + .mmd metni JSON olarak gömülü;
     `mermaid.render` sonucu `XMLSerializer` ile `<pre id="svgout">`'a yazılır,
     hata olursa `<div id="err">Syntax error: …</div>` dolar.
  2. chrome.exe --headless=new --disable-gpu --user-data-dir=<geçici>
     --virtual-time-budget=20000 --dump-dom <html>
  3. DOM'dan `<pre id="svgout">` içeriği HTML-çözülür → `<svg …>…</svg>`.
     Boş / hatalı ("Syntax error") / < 2 KB / XML olarak ayrıştırılamayan
     çıktı HATA sayılır ve dosya YAZILMAZ (bayat SVG kalmasın diye eski
     dosya silinir).

Etiketler SVG `<text>` olarak çizilir (htmlLabels=false): `<img>` içinde
foreignObject/HTML'e bağımlılık kalmaz, düğüm metni SVG'de düz metin olarak
aranabilir (nöbetçi test bunu kullanır).

Kullanım:
  python scripts/mermaid_svg.py --hepsi                 # FDR/sekiller/akis_*.mmd
  python scripts/mermaid_svg.py FDR/sekiller/akis_a.mmd [cikti.svg]
Çıkış: 0 hepsi üretildi · 1 en az biri düştü · 2 Chrome yok / çağrı hatası
"""

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
CHROME = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]
MERMAID_JS = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"
SANAL_ZAMAN_BUTCESI_MS = 20000
CHROME_ZAMAN_ASIMI_S = 120
ASGARI_SVG_BAYT = 2048          # nöbetçi test ile aynı eşik
# Yerleşim sıkılığı: Mermaid varsayılanı 50/50 px; 50–86 düğümlü diyagramlarda
# sayfa genişliğine ölçeklenince metin küçülür. Boşluk azaltılır, yazı tipi
# sabit tutulur (okunurluk PDF'te vektörden gelir; yakınlaştırılabilir).
YAZI_PX = 14
DUGUM_ARALIGI_PX = 20
# Kademe aralığı: küme kutusu başlık payı kadar (32 px) + iç boşluk (16 px)
# yukarı büyür; 44 px'te kümenin DIŞINDAKİ önceki düğüm kutunun içine giriyordu
# (akis_a a01, 7 Eylül ölçüldü). 76 px dış düğümü kutunun dışında tutar.
KADEME_ARALIGI_PX = 76
# Alt-grafik iç boşluğu ve başlık payı: başlık (2 satır: "def main()" +
# dosya:satır) ilk düğümün tepesine biniyordu (7 Eylül, akis_a ölçüldü; `padding`
# tek başına çözmedi — Mermaid başlığı kümenin üst kenarına çizer, düğümleri
# kaydırmaz). `subGraphTitleMargin` (Mermaid ≥ 10.9) başlık için üstte yer açar.
# Mermaid 10.9 düğümleri (top+bottom)/2 kadar aşağı, başlığı `top` kadar aşağı
# kaydırır ve küme kutusunu toplam kadar büyütür; başlık kümenin üst kenarında
# kalsın diye `top: 0`, pay `bottom`da. 64 = kayma 32 px; iki satırlık başlık
# ~30 px olduğundan ilk düğümün tepesi başlığın altına düşer. Kutunun yukarı
# büyümesi `KADEME_ARALIGI_PX` ile telafi edilir (yukarıdaki not).
ALT_GRAFIK_BOSLUGU_PX = 16
ALT_GRAFIK_BASLIK_USTU_PX = 64

HTML_SABLON = """<!doctype html><html><head><meta charset="utf-8">
<script src="{js}"></script></head><body>
<div id="err"></div><pre id="svgout"></pre>
<script>
const KAYNAK = {kaynak_json};
(async () => {{
  try {{
    if (typeof mermaid === "undefined") throw new Error("mermaid.js yuklenemedi (CDN)");
    mermaid.initialize({{startOnLoad: false, theme: "default",
                         themeVariables: {{fontSize: "{font_px}px"}},
                         flowchart: {{htmlLabels: false, useMaxWidth: false, curve: "linear",
                                     nodeSpacing: {node_spacing}, rankSpacing: {rank_spacing},
                                     padding: {padding},
                                     subGraphTitleMargin: {{top: 0, bottom: {baslik_ust}}}}}}});
    const {{svg}} = await mermaid.render("akis", KAYNAK);
    const kap = document.createElement("div");
    kap.innerHTML = svg;
    const el = kap.querySelector("svg");
    if (!el) throw new Error("render <svg> uretmedi");
    document.getElementById("svgout").textContent = new XMLSerializer().serializeToString(el);
  }} catch (e) {{
    document.getElementById("err").textContent =
      "Syntax error: " + (e && e.message ? e.message : String(e));
  }}
}})();
</script></body></html>
"""


def chrome_bul():
    return next((c for c in CHROME if c.is_file()), None)


def dom_al(chrome, html_yolu, profil):
    cmd = [str(chrome), "--headless=new", "--disable-gpu", f"--user-data-dir={profil}",
           "--no-first-run", "--no-default-browser-check", "--hide-scrollbars",
           f"--virtual-time-budget={SANAL_ZAMAN_BUTCESI_MS}", "--dump-dom",
           html_yolu.as_uri()]
    q = subprocess.run(cmd, capture_output=True, timeout=CHROME_ZAMAN_ASIMI_S)
    return q.stdout.decode("utf-8", errors="replace"), q.stderr.decode("utf-8", errors="replace")


def svg_cikar(dom):
    """DOM metni → (svg_metni | None, hata_metni | None)."""
    # Satır-içi <script> kaynağı da DOM dökümündedir ve "Syntax error" dizgesini
    # kendisi taşır (7 Eylül'de 5/5 sahte düşüş); arama betiksiz DOM'da yapılır.
    dom_sade = re.sub(r"<script\b.*?</script>", "", dom, flags=re.S | re.I)
    m_err = re.search(r'<div id="err">(.*?)</div>', dom_sade, flags=re.S)
    err = html.unescape(m_err.group(1)).strip() if m_err else ""
    if err:
        return None, err
    if "Syntax error" in dom_sade:
        return None, "DOM 'Syntax error' iceriyor (mermaid hata cizimi)"
    m = re.search(r'<pre id="svgout">(.*?)</pre>', dom, flags=re.S)
    if not m or not m.group(1).strip():
        return None, "DOM'da <pre id=svgout> bos — mermaid.js yuklenmedi ya da render bitmedi"
    svg = html.unescape(m.group(1)).strip()
    if not svg.startswith("<svg"):
        return None, f"cikti <svg ile baslamiyor: {svg[:60]!r}"
    svg = _cift_kodlamayi_coz(svg)
    try:
        ET.fromstring(svg.encode("utf-8"))
    except ET.ParseError as exc:
        return None, f"SVG XML olarak ayristirilamadi: {exc}"
    return svg, None


def _cift_kodlamayi_coz(svg):
    """Mermaid 10 SVG-metin (htmlLabels=false) çift kodlamasını geri al.

    7 Eylül'de ÖLÇÜLDÜ: etiketteki `<`/`#lt;` SVG'de düz metin olarak
    `&lt;` (dosyada `&amp;lt;`) çıkıyor, `&`/`#amp;` ise `&amp;` (dosyada
    `&amp;amp;`) — ekranda "if kalan &lt;= 0:" okunuyordu. Yalnız bu dört
    çift-kodlu dizi tek kodluya indirilir; başka hiçbir şey değişmez ve
    çıktı yine XML olarak yeniden ayrıştırılır.
    """
    for cift, tek in (("&amp;lt;", "&lt;"), ("&amp;gt;", "&gt;"),
                      ("&amp;quot;", "&quot;"), ("&amp;amp;", "&amp;")):
        svg = svg.replace(cift, tek)
    return svg


def render(mmd_yolu, svg_yolu, chrome=None, log=print):
    """Bir .mmd'yi .svg'ye çevir. Dönüş: (basarili, mesaj)."""
    chrome = chrome or chrome_bul()
    if chrome is None:
        return False, "Chrome/Edge bulunamadi"
    kaynak = mmd_yolu.read_text(encoding="utf-8")
    gecici = Path(tempfile.mkdtemp(prefix="mermaid_svg_"))
    try:
        html_yolu = gecici / "diyagram.html"
        html_yolu.write_text(
            HTML_SABLON.format(js=MERMAID_JS, kaynak_json=json.dumps(kaynak),
                               font_px=YAZI_PX, node_spacing=DUGUM_ARALIGI_PX,
                               rank_spacing=KADEME_ARALIGI_PX,
                               padding=ALT_GRAFIK_BOSLUGU_PX,
                               baslik_ust=ALT_GRAFIK_BASLIK_USTU_PX),
            encoding="utf-8")
        profil = gecici / "profil"
        try:
            dom, stderr = dom_al(chrome, html_yolu, profil)
        except subprocess.TimeoutExpired:
            return False, f"Chrome {CHROME_ZAMAN_ASIMI_S} s icinde donmedi"
        svg, hata = svg_cikar(dom)
        if svg is None:
            if svg_yolu.exists():
                svg_yolu.unlink()             # bayat SVG kalmasin
            return False, f"{hata} (stderr son 200: {stderr[-200:].strip()!r})"
        veri = svg.encode("utf-8")
        if len(veri) < ASGARI_SVG_BAYT:
            if svg_yolu.exists():
                svg_yolu.unlink()
            return False, f"SVG {len(veri)} B < {ASGARI_SVG_BAYT} B (bos cizim?)"
        svg_yolu.write_bytes(veri)
        return True, f"{svg_yolu.relative_to(KOK) if svg_yolu.is_relative_to(KOK) else svg_yolu} · {len(veri)} B"
    finally:
        shutil.rmtree(gecici, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mmd", nargs="?", type=Path, help="girdi .mmd")
    ap.add_argument("svg", nargs="?", type=Path, help="cikti .svg (varsayilan: ayni ad)")
    ap.add_argument("--hepsi", action="store_true", help="FDR/sekiller/akis_*.mmd hepsini cevir")
    args = ap.parse_args(argv)
    chrome = chrome_bul()
    if chrome is None:
        print("HATA: Chrome/Edge bulunamadi", file=sys.stderr)
        return 2
    if args.hepsi:
        ciftler = [(p, p.with_suffix(".svg")) for p in sorted(SEKILLER.glob("akis_*.mmd"))]
    elif args.mmd:
        ciftler = [(args.mmd, args.svg or args.mmd.with_suffix(".svg"))]
    else:
        ap.error("bir .mmd ya da --hepsi verin")
    if not ciftler:
        print("HATA: cevrilecek .mmd yok", file=sys.stderr)
        return 2
    basarisiz = 0
    for mmd, svg in ciftler:
        ok, mesaj = render(mmd, svg, chrome)
        print(f"{'URETILDI' if ok else 'DUSTU  '} {mmd.name} -> {mesaj}")
        basarisiz += 0 if ok else 1
    print(f"SONUC: {len(ciftler) - basarisiz}/{len(ciftler)} SVG uretildi")
    return 0 if basarisiz == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
