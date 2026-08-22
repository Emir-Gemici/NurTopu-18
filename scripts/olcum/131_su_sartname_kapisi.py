"""F3 — SARTNAME KAPISI. On kayittaki bantlari MEKANIK uygular.

On kayit: `results/dji_20260822/su_on_kayit.md` §2 (etiketleme baslamadan yazildi)

BANTLAR (buraya ELLE kopyalanmaz, on kayittan ALINIR ve degistirilmez):
    U1 ameleler arasi IoU medyani  >= 0,75
    U2 referansa gore IoU medyani  >= 0,70
    U3 sinif-1 IoU (ayni sey, ayri raporlanir) >= 0,65

🔴 KARAR KURALI (D-273'un dersi):
    U1 GECTI + U2 GECTI -> sartname saglam, F4 pilot BASLAR
    U1 GECTI + U2 DUSTU -> "tutarli ama yanlis": sartname HALA BELIRSIZ.
                           Cumle duzeltilir, pilot BASLAMAZ.
    U1 DUSTU            -> sartname okunamiyor, pilot BASLAMAZ.
D-273'te tam olarak ikinci hal cikmisti (ajanlar 0,88 / referans 0,55) ve
ameleler HAKLIYDI; o yuzden U2 duserse once REFERANS sorgulanir, amele degil.

⚠ BOS MASKE bir DEGER DEGILDIR (D-180 sinifi): iki maske de bossa IoU
  TANIMSIZDIR ve ortalamaya KATILMAZ; ayrica sayilir ve raporlanir. Bos
  maskeyi 1,0 saymak sahte uyum uretir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
TABAN = KOK / "results" / "dji_20260822"
ATAMA = TABAN / "su_pilot_atama.json"
REFERANS = TABAN / "referans"
AMELE_KOK = TABAN / "ameleler"
AMELELER = ("A", "B", "C")

U1_BANT, U2_BANT, U3_BANT = 0.75, 0.70, 0.65


def iou(a: np.ndarray, b: np.ndarray):
    """-> (deger, durum). Iki maske de bossa OLCULEMEDI doner (None)."""
    kesisim = int(np.logical_and(a, b).sum())
    birlesim = int(np.logical_or(a, b).sum())
    if birlesim == 0:
        return None, "OLCULEMEDI (iki maske de BOS)"
    return kesisim / birlesim, "OLCULDU"


def maske_oku(yol: Path, bicim: tuple[int, int]) -> np.ndarray | None:
    if not yol.is_file():
        return None
    m = cv2.imread(str(yol), cv2.IMREAD_GRAYSCALE)
    if m is None:
        return None
    if (m.shape[1], m.shape[0]) != bicim:
        m = cv2.resize(m, bicim, interpolation=cv2.INTER_NEAREST)
    return m > 127


def maske_coz(dizin: Path, dosya: str, stem_tekil: bool,
              bicim: tuple[int, int]) -> tuple[np.ndarray | None, str]:
    """Maskeyi CAKISMAYA DAYANIKLI coz. -> (maske, aciklama)

    🔴 NEDEN (amele C buldu, 2026-08-23): atamadaki 8 karenin IKISI ayni
    `stem`'e sahip (0038_d ve 0039_d'nin `frame_000000_000000000`'i). Duz
    `<stem>_sinif1.png` adlandirmasinda ikinci maske birincini SESSIZCE ezer.
    Ustabasinin referansi tam bu kusurla uretilmisti: 8 kare icin 7 PNG.
    Bu kapi kosulsaydi 0038'in amele maskesi 0039'un referansiyla
    kiyaslanacakti — olcumun tamami gecersiz olurdu.

    Kural: once GUVENLI ad (`<kaynak_dizin>__<stem>`) aranir. Yoksa duz ad
    yalniz stem BENZERSIZSE kabul edilir. Stem cakisiyorsa duz ad HANGI kareye
    ait belli DEGILDIR -> OLCULEMEDI (sessizce yanlis okumaktansa gurultulu
    eksik; D-180 sinifi).
    """
    govde = dosya.rsplit(".", 1)[0]
    guvenli = govde.replace("/", "__").replace("\\", "__")
    p = dizin / f"{guvenli}_sinif1.png"
    if p.is_file():
        return maske_oku(p, bicim), "guvenli ad"
    duz = Path(dosya).stem
    p2 = dizin / f"{duz}_sinif1.png"
    if p2.is_file():
        if stem_tekil:
            return maske_oku(p2, bicim), "duz ad (stem benzersiz)"
        return None, "🔴 duz ad AMA stem CAKISIYOR -> hangi kare oldugu belirsiz"
    return None, "dosya YOK"


def medyan(dizi):
    d = sorted(dizi)
    n = len(d)
    if n == 0:
        return None
    return d[n // 2] if n % 2 else (d[n // 2 - 1] + d[n // 2]) / 2


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    at = json.load(open(ATAMA, encoding="utf-8"))
    bicim = (960, 540)

    from collections import Counter
    stem_sayaci = Counter(Path(k["dosya"]).stem for k in at["kareler"])
    cakisan = [s for s, n in stem_sayaci.items() if n > 1]
    if cakisan:
        print(f"⚠ CAKISAN STEM ({len(cakisan)}): {cakisan} -> guvenli ad ZORUNLU\n")

    satirlar, eksik, bos = [], [], []
    for a in at["kareler"]:
        stem = Path(a["dosya"]).stem
        tekil = stem_sayaci[stem] == 1
        ref, nasil = maske_coz(REFERANS, a["dosya"], tekil, bicim)
        if ref is None:
            eksik.append(f"REFERANS {a['dosya']} ({nasil})")
            continue
        maskeler = {}
        for ad in AMELELER:
            m, nasil = maske_coz(AMELE_KOK / ad, a["dosya"], tekil, bicim)
            if m is None:
                eksik.append(f"{ad} {a['dosya']} ({nasil})")
            else:
                maskeler[ad] = m
                if not m.any():
                    bos.append(f"{ad} {stem}")
        satir = {"kare": stem, "kapsam": a["kapsam"],
                 "ref_oran": round(float(ref.mean()), 4)}
        # ameleler arasi
        ikili = []
        adlar = sorted(maskeler)
        for i in range(len(adlar)):
            for j in range(i + 1, len(adlar)):
                v, d = iou(maskeler[adlar[i]], maskeler[adlar[j]])
                satir[f"IoU_{adlar[i]}{adlar[j]}"] = None if v is None else round(v, 4)
                if v is not None:
                    ikili.append(v)
        # referansa gore
        refe = []
        for ad in adlar:
            v, d = iou(maskeler[ad], ref)
            satir[f"IoU_{ad}_ref"] = None if v is None else round(v, 4)
            satir[f"oran_{ad}"] = round(float(maskeler[ad].mean()), 4)
            if v is not None:
                refe.append(v)
        satir["amele_arasi_medyan"] = None if not ikili else round(medyan(ikili), 4)
        satir["referansa_medyan"] = None if not refe else round(medyan(refe), 4)
        satirlar.append(satir)

    u1 = medyan([s["amele_arasi_medyan"] for s in satirlar
                 if s["amele_arasi_medyan"] is not None])
    u2 = medyan([s["referansa_medyan"] for s in satirlar
                 if s["referansa_medyan"] is not None])

    print("=" * 78)
    print(f"{'kare':22s} {'ref%':>6s} {'A%':>6s} {'B%':>6s} {'C%':>6s} "
          f"{'amele':>7s} {'ref':>7s}")
    for s in satirlar:
        def g(k):
            v = s.get(k)
            return f"{100*v:5.1f}" if isinstance(v, (int, float)) else "    -"
        aa = s["amele_arasi_medyan"]; rr = s["referansa_medyan"]
        print(f"{s['kare'][-13:]:22s} {100*s['ref_oran']:5.1f} {g('oran_A')} "
              f"{g('oran_B')} {g('oran_C')} "
              f"{(f'{aa:6.3f}' if aa is not None else '     -')} "
              f"{(f'{rr:6.3f}' if rr is not None else '     -')}")
    print("=" * 78)

    def huk(ad, deger, bant):
        if deger is None:
            return f"{ad} OLCULEMEDI (bant {bant})"
        return f"{ad} {deger:.3f} (bant {bant}) -> {'GECTI' if deger >= bant else 'DUSTU'}"

    print(huk("U1 ameleler arasi", u1, U1_BANT))
    print(huk("U2 referansa gore ", u2, U2_BANT))
    print(huk("U3 sinif-1        ", u2, U3_BANT))

    if u1 is None or u2 is None:
        karar = "OLCULEMEDI — pilot BASLAMAZ"
    elif u1 >= U1_BANT and u2 >= U2_BANT:
        karar = "SARTNAME SAGLAM -> F4 PILOT BASLAR"
    elif u1 >= U1_BANT and u2 < U2_BANT:
        karar = ("🔴 TUTARLI AMA YANLIS — sartname HALA BELIRSIZ. "
                 "Once REFERANS sorgulanir (D-273: ameleler hakli cikmisti). "
                 "Cumle duzeltilir, PILOT BASLAMAZ.")
    else:
        karar = "🔴 SARTNAME OKUNAMIYOR (U1 dustu) — cumle duzeltilir, PILOT BASLAMAZ"
    print(f"\nKARAR: {karar}")

    if eksik:
        print(f"\n⚠ EKSIK MASKE ({len(eksik)}): {eksik[:10]}")
    if bos:
        print(f"⚠ BOS MASKE ({len(bos)}): {bos[:10]} — 'su yok' mu 'cizilmedi' mi, "
              f"amele raporundan DOGRULA")
    if u1 is not None and u1 > 0.97:
        print("⚠ U1 > 0,97 — ameleler BAGIMSIZ calismamis olabilir (on kayit §5). "
              "Prompt'larin ayri oldugu dogrulanmali.")

    cikti = TABAN / "sartname_kapisi.json"
    json.dump({"_ne": "F3 sartname kapisi", "_on_kayit": "results/dji_20260822/su_on_kayit.md",
               "_bantlar": {"U1": U1_BANT, "U2": U2_BANT, "U3": U3_BANT},
               "U1": u1, "U2": u2, "karar": karar,
               "eksik_maske": eksik, "bos_maske": bos, "kareler": satirlar},
              open(cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nyazildi: {cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
