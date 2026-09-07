#!/usr/bin/env python3
"""FDR bölümlerinden PDF üretir (taslak dizgisi — nihai dizgi 18–20 Eylül).

NEDEN: Takım üyeleri bölümleri okuyup üstünde çalışacak; Markdown herkeste aynı
görünmez. Bu betik `FDR/BOLUM_*.md` dosyalarını sırayla HTML'e çevirir ve Chrome
headless ile PDF'e basar. Kaynak dosyalara DOKUNMAZ; PDF türev üründür.

İki kip:
  --kip tam       Bölüm 0–7 tamamı                 → FDR/pdf/FDR_TAM_TASLAK_<tarih>.pdf
  --kip yazilim   Bölüm 3 (§3.3'ten sona), 4, 6    → FDR/pdf/FDR_YAZILIM_KOLU_<tarih>.pdf
                  + "bu taslak nasıl kullanılır" ön sayfası

Yönerge Y-0-M05 ("her sayfada TASNİF DIŞI + sayfa numarası"): TASNİF DIŞI üst ve alt
şerit her sayfada basılır (CSS fixed). Sayfa numarası bu taslakta YOKTUR — Chrome'un
kendi altlığı kapatıldı; nihai dizgide eklenir. Bu bilinerek kabul edildi.

Kullanım:
  python scripts/fdr_pdf_uret.py --kip tam
  python scripts/fdr_pdf_uret.py --kip yazilim
Çıkış: 0 üretildi ve sayfa sayısı > 10 · 1 hatalı çağrı · 2 Chrome/çıktı hatası
"""

import argparse
import datetime as dt
import html
import re
import subprocess
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

import markdown  # noqa: E402

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
CIKTI = FDR / "pdf"
CHROME = [
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]
BOLUMLER = [
    "BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md",
    "BOLUM_1_OZET.md",
    "BOLUM_2_ORGANIZASYON_VE_TAKVIM.md",
    "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md",
    "BOLUM_4_TEST_FAALIYETLERI.md",
    "BOLUM_5_URETIM_FAALIYETLERI.md",
    "BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md",
    "BOLUM_7_BUTCE_GERCEKLEME.md",
]
YAZILIM = ["BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", "BOLUM_4_TEST_FAALIYETLERI.md",
           "BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md"]

CSS = """
@page { size: A4; margin: 22mm 16mm 20mm 16mm; }
html { font-size: 10.5pt; }
body { font-family: "Segoe UI", "Noto Sans", Arial, sans-serif; line-height: 1.42; color: #111;
       margin: 0; }
.tasnif { position: fixed; left: 0; right: 0; text-align: center; font-size: 8.5pt;
          letter-spacing: .18em; color: #444; }
.tasnif.ust { top: -14mm; }  .tasnif.alt { bottom: -12mm; }
.bolum { page-break-before: always; }
.bolum:first-of-type { page-break-before: auto; }
h1 { font-size: 20pt; margin: 0 0 12pt; border-bottom: 2px solid #222; padding-bottom: 4pt; }
h2 { font-size: 15pt; margin: 18pt 0 8pt; border-bottom: 1px solid #999; padding-bottom: 2pt; page-break-after: avoid; }
h3 { font-size: 12.5pt; margin: 14pt 0 6pt; page-break-after: avoid; }
h4 { font-size: 11pt; margin: 12pt 0 4pt; page-break-after: avoid; }
h5, h6 { font-size: 10.5pt; margin: 10pt 0 4pt; }
p { margin: 0 0 7pt; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; border-left: 3px solid #888; background: #f4f4f4; }
table { border-collapse: collapse; width: 100%; margin: 6pt 0 10pt; font-size: 9pt;
        page-break-inside: auto; table-layout: fixed; }
th, td { border: 1px solid #999; padding: 3pt 5pt; vertical-align: top; text-align: left;
         word-wrap: break-word; overflow-wrap: anywhere; }
th { background: #e8e8e8; }
tr { page-break-inside: avoid; }
code { font-family: Consolas, "Courier New", monospace; font-size: 8.8pt; background: #f1f1f1;
       padding: 0 2pt; overflow-wrap: anywhere; }
pre { background: #f1f1f1; padding: 6pt 8pt; font-size: 8.5pt; white-space: pre-wrap;
      overflow-wrap: anywhere; border: 1px solid #ccc; page-break-inside: avoid; }
pre code { background: none; padding: 0; }
ul, ol { margin: 0 0 7pt 18pt; padding: 0; }
li { margin: 0 0 2pt; }
hr { border: 0; border-top: 1px solid #aaa; margin: 12pt 0; }
img { max-width: 100%; max-height: 235mm; display: block; margin: 6pt auto;
      page-break-inside: avoid; }
.onsoz { border: 2px solid #222; padding: 12pt 14pt; margin-bottom: 14pt; }
.onsoz h2 { border: 0; margin-top: 0; }
.damga { font-size: 9pt; color: #555; }
"""

ONSOZ_YAZILIM = """
<div class="onsoz">
<h2>Bu taslak nasıl kullanılır — yazılım kolu (Bölüm 3.3–3.4, 4, 6)</h2>
<p><b>Ne bu:</b> FDR'nin yazılım/aviyonik-yazılım, test ve izlenebilirlik bölümlerinin
<b>{tarih}</b> tarihli taslağı. Kaynak: <code>FDR/BOLUM_3_*.md</code>, <code>BOLUM_4_*.md</code>,
<code>BOLUM_6_*.md</code> (ortak sürücüdeki klasör). PDF <b>okumak</b> içindir; değişiklik
Markdown kaynağında yapılır ya da yama olarak koordinatöre gönderilir.</p>
<p><b>Üç kural (tartışmaya kapalı):</b></p>
<ol>
<li><b>İsim yazılmaz.</b> Anlatım rol bazlıdır (R1 Kaptan … R8 Kanıt-kalite). Yönerge Bölüm 2.1.</li>
<li><b>Bilmediğin sayıyı yazma.</b> Ölçülmemiş şey <code>ÖLÇÜLEMEDİ</code>, insan girdisi bekleyen şey
<code>BEYAN GEREKLİ (insan)</code> olarak kalır. Açık kalması kusur değil, <b>uydurulmuş olması</b> kusur.</li>
<li><b>Başlık icat etme.</b> Başlık adları ve numaraları yönergeden birebir gelir (<code>YONERGE_HARITASI.md</code>, <code>Y-…</code> kimlikleri).</li>
</ol>
<p><b>Her sayı bir artefakttan gelir:</b> bölüm sonundaki <i>Kanıt dizini</i> dosya yolunu ve
üreten betiği verir. Yeni bir sayı eklerken kaynağını da yaz; kaynağı yoksa ekleme.</p>
<p><b>Bu taslakta bilerek eksik:</b> sayfa numarası (nihai dizgide), gerçek arena karesi,
simülasyon videosu, SiK RF menzil/RTT, Jetson gerçek FPS — bunlar ölçümle kapanır, yazıyla değil.</p>
<p class="damga">Kaynak depo sürümü: {commit} · üretici: <code>scripts/fdr_pdf_uret.py</code></p>
</div>
"""


def _md(metin: str) -> str:
    govde = markdown.markdown(
        metin,
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
        extension_configs={"toc": {"toc_depth": "1-3"}},
        output_format="html5",
    )
    return _sekil_yollarini_coz(govde)


def _sekil_yollarini_coz(govde: str) -> str:
    """`![](sekiller/x.svg)` → mutlak file:// URI.

    NEDEN: HTML `FDR/pdf/` altına yazılır; Markdown'daki `sekiller/…` yolu
    oradan çözülünce `FDR/pdf/sekiller/…` olur ve görsel SESSİZCE boş kalır
    (7 Eylül, akış diyagramları). Kaynak .md'de yol `FDR/`ye göre kalır;
    yalnız üretilen HTML'de mutlaklaştırılır.
    """
    kok_uri = (FDR / "sekiller").as_uri()
    return re.sub(r'src="sekiller/', f'src="{kok_uri}/', govde)


def _oku(ad: str) -> str:
    return (FDR / ad).read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def _yazilim_kesiti(metin: str) -> str:
    """BOLUM_3: '## 3.3' başlığından dosya sonuna (§3.3, §3.4, Kanıt dizini)."""
    m = re.search(r"^## 3\.3 ", metin, flags=re.M)
    if not m:
        return metin
    baslik = metin.split("\n", 1)[0]  # '# BÖLÜM 3 — …' başlığı korunur
    not_ = ("\n\n> *(Bu taslakta §3.0–3.2 atlandı: uçuş bilimleri ve yapısal tasarım "
            "yazılım kolunun dışındadır.)*\n\n")
    return baslik + not_ + metin[m.start():]


def uret(kip: str) -> int:
    tarih = dt.date.today().strftime("%Y%m%d")
    tarih_tr = dt.date.today().strftime("%d.%m.%Y")
    try:
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=KOK,
                                capture_output=True, text=True).stdout.strip() or "?"
    except OSError:
        commit = "?"

    parcalar = []
    if kip == "tam":
        adlar, ad_pdf = BOLUMLER, f"FDR_TAM_TASLAK_{tarih}.pdf"
    else:
        adlar, ad_pdf = YAZILIM, f"FDR_YAZILIM_KOLU_{tarih}.pdf"
        parcalar.append(ONSOZ_YAZILIM.format(tarih=tarih_tr, commit=commit))

    for ad in adlar:
        metin = _oku(ad)
        if kip == "yazilim" and ad.startswith("BOLUM_3"):
            metin = _yazilim_kesiti(metin)
        govde_html = _md(metin)
        # Bölüm dosyaları FDR/ altında, üretilen HTML FDR/pdf/ altında: `sekiller/x.svg`
        # atıfları bir üst dizine çözülmeli (G4/G5/G6 diyagramları, 7 Eylül).
        govde_html = govde_html.replace('src="sekiller/', 'src="../sekiller/')
        parcalar.append(f'<section class="bolum" id="{html.escape(ad)}">' + govde_html + "</section>")

    govde = "\n".join(parcalar)
    # Şekiller `FDR/sekiller/` altındadır; markdown'da `![](sekiller/x.svg)` FDR
    # köküne görelidir ama HTML `FDR/pdf/` içine yazılır → göreli yol PDF'te kırık
    # kalır (7 Eylül gecesi ölçüldü). Mutlak file:// URI'ye çevrilir.
    govde = govde.replace('src="sekiller/', f'src="{FDR.as_uri()}/sekiller/')
    sayfa = (
        "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
        f"<title>NAVITAS FDR taslak {tarih_tr}</title><style>{CSS}</style></head><body>"
        "<div class='tasnif ust'>TASNİF DIŞI</div>"
        f"{govde}"
        "<div class='tasnif alt'>TASNİF DIŞI</div>"
        "</body></html>"
    )
    CIKTI.mkdir(parents=True, exist_ok=True)
    pdf_yolu = CIKTI / ad_pdf
    chrome = next((c for c in CHROME if c.is_file()), None)
    if chrome is None:
        print("Chrome/Edge bulunamadı"); return 2

    # ── Yol 1: paged.js — gerçek @page kenar kutuları: üst-orta TASNİF DIŞI, alt-orta
    # "TASNİF DIŞI · Sayfa N / M" (Y-0-M05 tam karşılanır). 7 Eylül'de ölçüldü: CSS
    # `position: fixed` şerit Chrome baskısında kenar boşluğuna değil metnin ÜSTÜNE
    # biniyor (2. sayfada tabloyla çakıştı) — o yüzden şerit kaldırıldı.
    PAGED = ("<script src='https://cdnjs.cloudflare.com/ajax/libs/pagedjs/0.4.3/"
             "paged.polyfill.min.js'></script>")
    PAGED_CSS = ("@page { size: A4; margin: 22mm 16mm 20mm 16mm; "
                 "@top-center { content: 'TASNİF DIŞI'; font-size: 8.5pt; letter-spacing: .18em; color: #444; } "
                 "@bottom-center { content: 'TASNİF DIŞI · Sayfa ' counter(page) ' / ' counter(pages); "
                 "font-size: 8.5pt; color: #444; } }")
    sayfa_paged = sayfa.replace("<div class='tasnif ust'>TASNİF DIŞI</div>", "") \
                       .replace("<div class='tasnif alt'>TASNİF DIŞI</div>", "") \
                       .replace("<style>", f"<style>{PAGED_CSS}", 1) \
                       .replace("</head>", PAGED + "</head>", 1)
    # ── Yol 2 (yedek): Chrome'un kendi başlık/altlığı — başlıkta <title> (TASNİF DIŞI
    # ile başlar), altlıkta dosya URL'si + "N/M". Sayfa numarası gelir, şerit binmez.
    sayfa_yedek = sayfa.replace("<div class='tasnif ust'>TASNİF DIŞI</div>", "") \
                       .replace("<div class='tasnif alt'>TASNİF DIŞI</div>", "") \
                       .replace("<title>", "<title>TASNİF DIŞI — ", 1)

    import tempfile

    def _bas(metin_html, ad_html, ek_bayraklar):
        html_yolu = CIKTI / ad_html
        html_yolu.write_text(metin_html, encoding="utf-8")
        # Chrome açıkken --user-data-dir verilmezse çağrı MEVCUT oturuma devrolur ve
        # PDF üretilmez (7 Eylül'de ölçüldü). Geçici profil şart.
        profil = Path(tempfile.mkdtemp(prefix="fdr_pdf_"))
        cmd = [str(chrome), "--headless=new", "--disable-gpu", f"--user-data-dir={profil}",
               "--no-first-run", "--no-default-browser-check", *ek_bayraklar,
               f"--print-to-pdf={pdf_yolu}", html_yolu.as_uri()]
        if pdf_yolu.exists():
            pdf_yolu.unlink()
        q = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if not pdf_yolu.is_file():
            return -1, q.stderr[-300:]
        try:
            from pypdf import PdfReader
            r = PdfReader(str(pdf_yolu))
            ornek = (r.pages[min(3, len(r.pages) - 1)].extract_text() or "")[:160].replace("\n", " ")
            return len(r.pages), ornek
        except Exception as e:  # noqa: BLE001
            return -1, f"pypdf: {e}"

    n, ornek = _bas(sayfa_paged, ad_pdf[:-4] + ".html",
                    ["--no-pdf-header-footer", "--virtual-time-budget=120000"])
    yol = "paged.js"
    if n < 10 or "Sayfa " not in (ornek + "") and n < 10:
        n, ornek = _bas(sayfa_yedek, ad_pdf[:-4] + ".html", [])
        yol = "chrome-altlik (yedek)"
    boyut = pdf_yolu.stat().st_size if pdf_yolu.exists() else 0
    print(f"ÜRETİLDİ {pdf_yolu.relative_to(KOK)} · {n} sayfa · {boyut / 1e6:.1f} MB · kaynak {commit} · yol: {yol}")
    print(f"  4. sayfa örneği: {ornek}")
    return 0 if n > 10 else 2


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--kip", choices=("tam", "yazilim"), required=True)
    a = ap.parse_args(argv)
    return uret(a.kip)


if __name__ == "__main__":
    sys.exit(main())
