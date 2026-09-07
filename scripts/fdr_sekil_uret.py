"""FDR Bölüm 6 §6.6 dağılım grafiklerini SVG olarak üretir (Y-6-M06).

NEDEN: Yönerge `Y-6-M06` genel uygunluk durumunun **görsel** sunumunu ister;
markdown kaynağında yalnız veri tablosu ve metin bar vardır. Bu betik
`FDR/BOLUM_6_*.md` §6.6.2 ve §6.6.3 tablolarını **okur** (sayı elle yazılmaz)
ve iki statik SVG basar:

  FDR/sekiller/uygunluk_pasta.svg   §6.6.2 — 45 satırın durum dağılımı (halka)
  FDR/sekiller/uygunluk_yontem.svg  §6.6.3 — doğrulama yöntemi dağılımı (yatay çubuk;
                                     bir satır birden çok yöntem taşıdığı için halka
                                     YANILTICI olurdu: oranlar 45 satıra göredir,
                                     toplamı %100'ü aşar)

Yalnız standart kütüphane; harici çizim kütüphanesi yok. SVG işaretlemesi
burada açık yazılıdır (viewBox, explicit fill, sans-serif); betik yalnız yay
uç noktalarını ve çubuk genişliklerini hesaplar. Her dilim/çubuk `data-satir`
ve `data-oran` taşır ki `tests/test_gece_sekiller.py` tabloyla birebir
karşılaştırabilsin — geometri de sınanır (yay açısı, çubuk genişliği).

Kullanım:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -B scripts/fdr_sekil_uret.py
  (isteğe bağlı --tarih 2026-09-07; varsayılan sabittir ki çıktı deterministik kalsın)
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):        # konsol cp1254 → Türkçe/ok karakterleri
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
BOLUM_6 = KOK / "FDR" / "BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md"
SEKILLER = KOK / "FDR" / "sekiller"

# Tablodaki sayım tarihi: §6.6.2 "Yeniden sayım 5 Eylül sonrası" — bu betik
# 7 Eylül 2026 gecesi yazıldı. `date.today()` bilerek KULLANILMAZ: aynı tablo
# aynı SVG'yi üretmeli (git diff gürültüsü yok).
VARSAYILAN_TARIH = "7 Eylül 2026"

# Renk anlamı (durum → renk). Dört durum etiketi §6.3.1'de tanımlıdır; renkler
# durum renkleridir, seri rengi değil: yeşil = kanıtlı, sarı = kısmen (kod var
# test yok), kırmızı = açık (ölçülemedi), gri = yazılım kapsamı dışı
# (insan/donanım hükmü — §6.6.6/3). Her dilim etiket + sayı + yüzde taşır;
# kimlik yalnız renge bırakılmaz (gri bilerek renksizdir).
RENK = {
    "KANITLI_TEST": "#0ca30c",
    "KOD_VAR_TEST_YOK": "#d99a00",
    "ÖLÇÜLEMEDİ": "#d03b3b",
    "İNSAN-DONANIM": "#8a8a86",
}
RENK_ACIKLAMA = {                       # lejant sütunu ≈ 330 px: ≤ 30 karakter
    "KANITLI_TEST": "kanıtlı (kapı koştu, ayırt edici)",
    "İNSAN-DONANIM": "kapsam dışı (insan/donanım)",
    "KOD_VAR_TEST_YOK": "kısmen (kod var, test yok)",
    "ÖLÇÜLEMEDİ": "açık (ölçülemedi)",
}
CUBUK_RENK = "#4a6fa5"   # tek seri → tek renk
METIN = "#111111"
METIN_IKINCIL = "#444444"
IZGARA = "#d9d9d6"
ARKA = "#ffffff"
FONT = "font-family=\"'Segoe UI', 'Noto Sans', Arial, sans-serif\""

SATIR_662 = re.compile(r"^\|\s*\*\*([^*|]+?)\*\*\s*\|\s*(\d+)\s*\|\s*(%[\d,]+)\s*\|")
SATIR_663 = re.compile(r"^\|\s*([^*|]+?)\s*\|\s*(\d+)\s*\|\s*(%[\d,]+)\s*\|")


def _kesit(metin: str, bas: str, son: str) -> str:
    i = metin.index(bas)
    j = metin.index(son, i)
    return metin[i:j]


def tablo_662(metin: str) -> tuple[list[tuple[str, int, str]], int]:
    """§6.6.2 satırları [(durum, satır, oran)] ve tablonun kendi 'toplam' hücresi."""
    kesit = _kesit(metin, "### 6.6.2", "### 6.6.3")
    satirlar, toplam = [], None
    for s in kesit.splitlines():
        m = SATIR_662.match(s)
        if not m:
            continue
        ad = m.group(1).strip()
        if ad == "toplam":
            continue
        satirlar.append((ad, int(m.group(2)), m.group(3)))
    mt = re.search(r"^\|\s*\*\*toplam\*\*\s*\|\s*\*\*(\d+)\*\*", kesit, re.M)
    if mt:
        toplam = int(mt.group(1))
    if not satirlar or toplam is None:
        raise SystemExit("§6.6.2 tablosu okunamadı")
    return satirlar, toplam


def tablo_663(metin: str) -> tuple[list[tuple[str, int, str]], int]:
    """§6.6.3 satırları [(yöntem, satır, oran)] ve oranın paydası (45 satır)."""
    kesit = _kesit(metin, "### 6.6.3", "### 6.6.4")
    satirlar = []
    for s in kesit.splitlines():
        m = SATIR_663.match(s)
        if not m or m.group(1).strip() in ("yöntem",):
            continue
        satirlar.append((m.group(1).strip(), int(m.group(2)), m.group(3)))
    mp = re.search(r"\|\s*(\d+)\s+satırın oranı\s*\|", kesit)
    if not satirlar or not mp:
        raise SystemExit("§6.6.3 tablosu okunamadı")
    return satirlar, int(mp.group(1))


def _nokta(cx: float, cy: float, r: float, aci_derece: float) -> tuple[float, float]:
    a = math.radians(aci_derece)
    return cx + r * math.cos(a), cy + r * math.sin(a)


def _f(x: float) -> str:
    return f"{x:.3f}"


def pasta_svg(satirlar, toplam, tarih: str) -> str:
    W, H = 900, 560
    cx, cy, R, r = 270.0, 318.0, 165.0, 100.0
    aci = -90.0  # 12'den başla, saat yönü
    dilimler, etiketler, lejant = [], [], []
    ly = 214
    for ad, n, oran in satirlar:
        span = 360.0 * n / toplam
        a0, a1 = aci, aci + span
        x0, y0 = _nokta(cx, cy, R, a0)
        x1, y1 = _nokta(cx, cy, R, a1)
        xi1, yi1 = _nokta(cx, cy, r, a1)
        xi0, yi0 = _nokta(cx, cy, r, a0)
        buyuk = 1 if span > 180 else 0
        d = (f"M {_f(x0)} {_f(y0)} A {_f(R)} {_f(R)} 0 {buyuk} 1 {_f(x1)} {_f(y1)} "
             f"L {_f(xi1)} {_f(yi1)} A {_f(r)} {_f(r)} 0 {buyuk} 0 {_f(xi0)} {_f(yi0)} Z")
        dilimler.append(
            f'    <path class="dilim" data-durum="{ad}" data-satir="{n}" data-oran="{oran}" '
            f'd="{d}" fill="{RENK[ad]}" stroke="{ARKA}" stroke-width="2"/>')
        # dilimin dışına doğrudan değer etiketi
        orta = a0 + span / 2
        tx, ty = _nokta(cx, cy, R + 26, orta)
        ank = "start" if math.cos(math.radians(orta)) >= 0 else "end"
        etiketler.append(
            f'    <text x="{_f(tx)}" y="{_f(ty + 5)}" text-anchor="{ank}" font-size="13" '
            f'fill="{METIN}">{n} ({oran})</text>')
        lejant.append(
            f'    <rect x="540" y="{ly - 15}" width="18" height="18" fill="{RENK[ad]}"/>\n'
            f'    <text x="570" y="{ly}" font-size="15" font-weight="bold" fill="{METIN}">{ad}</text>\n'
            f'    <text x="570" y="{ly + 20}" font-size="13" fill="{METIN_IKINCIL}">'
            f'{n} satır · {oran} — {RENK_ACIKLAMA[ad]}</text>')
        ly += 60
        aci = a1
    govde = "\n".join(dilimler)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" {FONT}>
  <title>Genel uygunluk dağılımı — {toplam} gereksinim satırı (FDR §6.6.2)</title>
  <rect x="0" y="0" width="{W}" height="{H}" fill="{ARKA}"/>
  <text x="24" y="38" font-size="20" font-weight="bold" fill="{METIN}">Genel uygunluk dağılımı — {toplam} gereksinim satırı</text>
  <text x="24" y="62" font-size="13" fill="{METIN_IKINCIL}">Sayım kuralı: her satırın baskın durumu (§6.3.1); döküm §6.6.1. "Kanıtlı" = kapı koştu ve ayırt edici, "sahada çalıştı" değil (§6.6.6).</text>
  <g id="dilimler" data-toplam="{toplam}" data-cx="{_f(cx)}" data-cy="{_f(cy)}" data-r-dis="{_f(R)}" data-r-ic="{_f(r)}">
{govde}
  </g>
  <g id="degerler">
{chr(10).join(etiketler)}
  </g>
  <text x="{_f(cx)}" y="{_f(cy - 2)}" text-anchor="middle" font-size="40" font-weight="bold" fill="{METIN}">{toplam}</text>
  <text x="{_f(cx)}" y="{_f(cy + 24)}" text-anchor="middle" font-size="14" fill="{METIN_IKINCIL}">gereksinim satırı</text>
  <g id="lejant">
{chr(10).join(lejant)}
  </g>
  <text x="24" y="{H - 34}" font-size="12" fill="{METIN_IKINCIL}">Renk anlamı: yeşil = kanıtlı · gri = yazılım kapsamı dışı · sarı = kısmen · kırmızı = açık. Her dilim etiket + sayı + yüzde taşır.</text>
  <text x="24" y="{H - 14}" font-size="12" fill="{METIN_IKINCIL}">kaynak: FDR Bölüm 6 §6.6.2 (yeniden sayım 5 Eylül sonrası) · {tarih} · üretici: scripts/fdr_sekil_uret.py</text>
</svg>
'''


def yontem_svg(satirlar, payda, tarih: str) -> str:
    W, H = 900, 440
    x0, px = 230.0, 13.0          # çubuk başlangıcı; satır başına piksel
    y0, yuk, adim = 112, 30, 50
    toplam_atama = sum(n for _, n, _ in satirlar)
    izgara, cubuklar = [], []
    for k in range(0, 101, 20):
        x = x0 + px * payda * k / 100
        izgara.append(
            f'    <line x1="{_f(x)}" y1="{y0 - 8}" x2="{_f(x)}" y2="{y0 + adim * len(satirlar) - 12}" stroke="{IZGARA}" stroke-width="1"/>\n'
            f'    <text x="{_f(x)}" y="{y0 - 14}" text-anchor="middle" font-size="11" fill="{METIN_IKINCIL}">%{k}</text>')
    for i, (ad, n, oran) in enumerate(satirlar):
        y = y0 + i * adim
        w = px * n
        cubuklar.append(
            f'    <text x="{_f(x0 - 14)}" y="{y + 20}" text-anchor="end" font-size="14" fill="{METIN}">{ad}</text>\n'
            f'    <rect class="cubuk" data-yontem="{ad}" data-satir="{n}" data-oran="{oran}" '
            f'x="{_f(x0)}" y="{y}" width="{_f(w)}" height="{yuk}" rx="3" fill="{CUBUK_RENK}"/>\n'
            f'    <text x="{_f(x0 + w + 10)}" y="{y + 20}" font-size="13" fill="{METIN}">{n} satır · {oran}</text>')
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" {FONT}>
  <title>Doğrulama yöntemi dağılımı — {payda} satır, {toplam_atama} atama (FDR §6.6.3)</title>
  <rect x="0" y="0" width="{W}" height="{H}" fill="{ARKA}"/>
  <text x="24" y="38" font-size="20" font-weight="bold" fill="{METIN}">Doğrulama yöntemi dağılımı — {payda} satır, {toplam_atama} yöntem ataması</text>
  <text x="24" y="62" font-size="13" fill="{METIN_IKINCIL}">Bir satır birden çok yöntem taşır; oranlar {payda} satıra göredir ve toplamı %100'ü aşar (bu yüzden pasta değil çubuk). Kural: §6.2.3.</text>
  <g id="izgara">
{chr(10).join(izgara)}
  </g>
  <g id="cubuklar" data-satir-toplam="{payda}" data-px-per-satir="{_f(px)}" data-x0="{_f(x0)}">
{chr(10).join(cubuklar)}
  </g>
  <line x1="{_f(x0)}" y1="{y0 - 8}" x2="{_f(x0)}" y2="{y0 + adim * len(satirlar) - 12}" stroke="#888888" stroke-width="1"/>
  <text x="{_f(x0 + px * payda)}" y="{y0 + adim * len(satirlar) + 6}" text-anchor="end" font-size="11" fill="{METIN_IKINCIL}">%100 = {payda} satır</text>
  <text x="24" y="{H - 14}" font-size="12" fill="{METIN_IKINCIL}">kaynak: FDR Bölüm 6 §6.6.3 (yeniden sayım 5 Eylül sonrası: {toplam_atama} atama) · {tarih} · üretici: scripts/fdr_sekil_uret.py</text>
</svg>
'''


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tarih", default=VARSAYILAN_TARIH)
    a = ap.parse_args(argv)
    metin = BOLUM_6.read_text(encoding="utf-8").replace("\r\n", "\n")
    s662, toplam = tablo_662(metin)
    s663, payda = tablo_663(metin)
    if sum(n for _, n, _ in s662) != toplam:
        print(f"§6.6.2 satır toplamı {sum(n for _, n, _ in s662)} ≠ tablo toplamı {toplam}")
        return 1
    SEKILLER.mkdir(parents=True, exist_ok=True)
    (SEKILLER / "uygunluk_pasta.svg").write_text(pasta_svg(s662, toplam, a.tarih), encoding="utf-8", newline="\n")
    (SEKILLER / "uygunluk_yontem.svg").write_text(yontem_svg(s663, payda, a.tarih), encoding="utf-8", newline="\n")
    print("§6.6.2:", ", ".join(f"{ad} {n} {o}" for ad, n, o in s662), f"→ toplam {toplam}")
    print("§6.6.3:", ", ".join(f"{ad} {n} {o}" for ad, n, o in s663), f"→ payda {payda}")
    print(f"yazıldı: {SEKILLER.relative_to(KOK)}/uygunluk_pasta.svg, uygunluk_yontem.svg")
    return 0


if __name__ == "__main__":
    sys.exit(main())
