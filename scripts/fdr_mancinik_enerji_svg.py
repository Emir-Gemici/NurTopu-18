"""Mancınık enerji-denklemi şematiği (Y-3.2.3-A02) — SEMBOLİK ÇERÇEVE, veri DEĞİL.

NEDEN: Yönerge `Y-3.2.3-A02` "mekanizmanın İHA'yı ne kadar uzağa fırlatabileceğinin
enerji denklemleriyle açıklanması + şematik gösterim" ister. Mancınık bugün
ÜRETİLMEDİ (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` §3.2.3): yay sabiti (k),
kızak uzunluğu (x), fırlatma açısı (θ) hiçbiri ÖLÇÜLMEDİ/BEYAN edilmedi. Bu betik
sayı UYDURMAZ — yalnız yönergenin istediği ANALİTİK ÇERÇEVEYİ (enerji zinciri:
depolanan enerji → çıkış hızı → menzil) sembolik değişkenlerle çizer. Her değişken
etiketinin yanında "BEYAN GEREKLİ" durur; SVG'de tek bir sayısal değer YOKTUR.

Gerçek veri (k, x, m, θ) geldiğinde bu betiğe `--k --x --m --theta` eklenip
sayısal bir ikinci şekil (`mancinik_enerji_hesap.svg`) üretilebilir — O GÜNE
KADAR bu dosya yalnız çerçevedir, sonuç değildir.

Çıktı: FDR/sekiller/mancinik_enerji.svg

Kullanım:
  python scripts/fdr_mancinik_enerji_svg.py            # yazar
  python scripts/fdr_mancinik_enerji_svg.py --dogrula  # diskteki dosya üretimle aynı mı (0/1)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
SVG_YOLU = SEKILLER / "mancinik_enerji.svg"

GENISLIK = 900
YUKSEKLIK = 545

RENK_CIZGI = "#1f2933"
RENK_YAY = "#b91c1c"
RENK_IHA = "#1d4ed8"
RENK_YORUNGE = "#6b7280"
RENK_BEYAN = "#b45309"
RENK_ZEMIN = "#374151"


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _metin(x, y, icerik, *, boyut=15, renk=RENK_CIZGI, agirlik="normal",
           hiza="start", aile="sans-serif"):
    return (f'<text x="{x}" y="{y}" font-family="{aile}" font-size="{boyut}" '
            f'font-weight="{agirlik}" fill="{renk}" text-anchor="{hiza}">'
            f'{_esc(icerik)}</text>')


def _beyan_etiketi(x, y, ad):
    """Sembolik değişken etiketi — hep AYNI turuncu 'BEYAN GEREKLİ' rozetiyle."""
    return (_metin(x, y, ad, boyut=16, renk=RENK_BEYAN, agirlik="bold")
            + _metin(x, y + 16, "(BEYAN GEREKLİ)", boyut=10, renk=RENK_BEYAN))


def uret_svg() -> str:
    parcalar = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {GENISLIK} {YUKSEKLIK}" '
        f'font-family="sans-serif">',
        f'<rect width="{GENISLIK}" height="{YUKSEKLIK}" fill="#ffffff"/>',
        _metin(20, 30, "Mancınık enerji zinciri — SEMBOLİK ÇERÇEVE (sayısal veri yok)",
               boyut=18, agirlik="bold"),
        _metin(20, 50, "Y-3.2.3-A02 · gerçek k, x, m, θ değerleri BEYAN GEREKLİ (bkz. §3.2.3 T04/A01)",
               boyut=12, renk=RENK_YORUNGE),
    ]

    # Zemin çizgisi
    zemin_y = 340
    parcalar.append(f'<line x1="30" y1="{zemin_y}" x2="{GENISLIK-30}" y2="{zemin_y}" '
                     f'stroke="{RENK_ZEMIN}" stroke-width="2"/>')

    # Kızak (rail) — yatay dikdörtgen
    ray_x0, ray_x1, ray_y = 60, 340, zemin_y - 20
    parcalar.append(f'<rect x="{ray_x0}" y="{ray_y-6}" width="{ray_x1-ray_x0}" height="10" '
                     f'fill="none" stroke="{RENK_CIZGI}" stroke-width="2"/>')
    parcalar.append(_metin((ray_x0+ray_x1)//2, ray_y+28, "kızak uzunluğu",
                            hiza="middle", boyut=12))
    parcalar.append(_beyan_etiketi((ray_x0+ray_x1)//2 - 10, ray_y + 50, "x"))

    # Yay (zigzag) — sıkışmış durumda, kızağın sol ucunda
    yay_x0, yay_x1, yay_y = ray_x0 + 15, ray_x0 + 120, ray_y - 1
    n_dis = 7
    pts = [f"{yay_x0},{yay_y}"]
    for i in range(1, n_dis):
        x = yay_x0 + (yay_x1 - yay_x0) * i / n_dis
        y = yay_y + (-10 if i % 2 else 10)
        pts.append(f"{x:.1f},{y}")
    pts.append(f"{yay_x1},{yay_y}")
    parcalar.append(f'<polyline points="{" ".join(pts)}" fill="none" '
                     f'stroke="{RENK_YAY}" stroke-width="3"/>')
    parcalar.append(_beyan_etiketi(yay_x0 - 5, ray_y - 45, "k (yay sabiti)"))

    # İHA (basit üçgen + gövde) kızağın üstünde


    iha_x = yay_x1 + 55
    iha_y = ray_y - 12
    parcalar.append(f'<polygon points="{iha_x-35},{iha_y} {iha_x+35},{iha_y} '
                     f'{iha_x+35},{iha_y-14} {iha_x-20},{iha_y-14}" '
                     f'fill="{RENK_IHA}" opacity="0.85"/>')
    parcalar.append(_metin(iha_x, iha_y - 20, "İHA (kütle m)", hiza="middle",
                            boyut=12, renk=RENK_IHA, agirlik="bold"))
    parcalar.append(_beyan_etiketi(iha_x - 45, iha_y - 55, "m"))

    # Çıkış hızı vektörü + açı
    cikis_x, cikis_y = ray_x1, ray_y - 12
    ok_x, ok_y = cikis_x + 140, cikis_y - 90
    parcalar.append(f'<line x1="{cikis_x}" y1="{cikis_y}" x2="{ok_x}" y2="{ok_y}" '
                     f'stroke="{RENK_CIZGI}" stroke-width="2.5" '
                     f'marker-end="url(#ok)"/>')
    parcalar.append(_beyan_etiketi(ok_x - 20, ok_y - 10, "v0 (çıkış hızı)"))
    parcalar.append(f'<path d="M {cikis_x+40},{cikis_y} A 40 40 0 0 0 {cikis_x+28},{cikis_y-33}" '
                     f'fill="none" stroke="{RENK_ZEMIN}" stroke-width="1.5"/>')
    parcalar.append(_beyan_etiketi(cikis_x + 46, cikis_y - 12, "θ (fırlatma açısı)"))

    # Yörünge (kesikli eğri) + menzil oku
    yor_pts = []
    import math
    for i in range(21):
        t = i / 20
        x = cikis_x + t * 420
        y = cikis_y - (4 * 130 * t * (1 - t))
        yor_pts.append(f"{x:.1f},{y:.1f}")
    parcalar.append(f'<polyline points="{" ".join(yor_pts)}" fill="none" '
                     f'stroke="{RENK_YORUNGE}" stroke-width="2" stroke-dasharray="6,5"/>')
    inis_x = cikis_x + 420
    parcalar.append(f'<line x1="{cikis_x}" y1="{zemin_y+18}" x2="{inis_x}" y2="{zemin_y+18}" '
                     f'stroke="{RENK_ZEMIN}" stroke-width="1.5" marker-end="url(#ok)"/>')
    parcalar.append(_beyan_etiketi((cikis_x+inis_x)//2 - 15, zemin_y + 32, "R (menzil)"))

    # Ok başı tanımı
    parcalar.append('<defs><marker id="ok" markerWidth="8" markerHeight="8" '
                     'refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 z" '
                     f'fill="{RENK_ZEMIN}"/></marker></defs>')

    # Denklem kutusu (sağ alt) — sembolik, sayı yok
    kutu_x, kutu_y = 20, 430
    denklemler = [
        "Enerji zinciri (sembolik, sayı yok — BEYAN GEREKLİ değişkenler yukarıda):",
        "1) Depolanan enerji:      E = ½ · k · x²",
        "2) Çıkış hızı (m kütleye aktarım, kayıpsız üst sınır):   v0 = √(2E / m)",
        "3) İdeal menzil (düz zemin, hava direnci ihmal):   R = v0² · sin(2θ) / g",
    ]
    parcalar.append(f'<rect x="{kutu_x}" y="{kutu_y-24}" width="{GENISLIK-2*kutu_x}" '
                     f'height="{4*22+16}" fill="#f9fafb" stroke="{RENK_ZEMIN}" '
                     f'stroke-width="1"/>')
    for i, satir in enumerate(denklemler):
        parcalar.append(_metin(kutu_x + 14, kutu_y + i*22, satir,
                                boyut=13.5 if i == 0 else 14,
                                agirlik="bold" if i == 0 else "normal",
                                aile="monospace" if i > 0 else "sans-serif"))

    parcalar.append('</svg>')
    return "\n".join(parcalar) + "\n"


def yaz(dogrula: bool) -> int:
    icerik = uret_svg()
    if dogrula:
        if not SVG_YOLU.is_file():
            print(f"BAYAT: {SVG_YOLU} yok")
            return 1
        if SVG_YOLU.read_text(encoding="utf-8") != icerik:
            print(f"BAYAT: {SVG_YOLU} üretimle aynı değil")
            return 1
        print("GÜNCEL")
        return 0
    SEKILLER.mkdir(parents=True, exist_ok=True)
    SVG_YOLU.write_text(icerik, encoding="utf-8")
    print(f"yazıldı: {SVG_YOLU}")
    return 0


def _ana(argv=None) -> int:
    ayristirici = argparse.ArgumentParser(description=__doc__)
    ayristirici.add_argument("--dogrula", action="store_true",
                              help="yazmaz, diskteki dosyanın güncel olup olmadığını söyler")
    args = ayristirici.parse_args(argv)
    return yaz(args.dogrula)


if __name__ == "__main__":
    sys.exit(_ana())
