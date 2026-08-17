"""T94 · ACIKLIK KORUYAN STRING-PULLING — kirisi dar bogazdan gecirme.

NEDEN (REVIEW_LOG D-154). Olculdu: `yol_duzelt`in gorus-hatti string-pulling'i
A*'in orta-eksene sarilan yolunu TEK DUZ KIRISLE degistiriyor (260 karenin
213'unde sonuc TAM 2 dugum) ve emniyet payini medyan 4,00 px yiyor. Dar
karelerin 39/46'si SADECE bundan dar gorunuyor; K5'i dusuren `sa_000131`de
kayip 10,47 px (pay 12,52 -> 2,31).

FIKIR: kirisin GECILEBILIR olmasi yetmiyor; kiris DAR BIR BOGAZDAN gecmemeli.
`_gorus_hatti` bir kirisi yalnizca C-uzayinda kaldigi icin kabul ediyor. Buraya
bir ACIKLIK ESIGI eklenir: kiris uzerindeki en kucuk aciklik esigin altina
duserse kiris REDDEDILIR ve yol o noktada dugum tutar.

⚠ YON: bu kural yalnizca KISALTMAYI REDDEDER. Rota UZAR / dugum ARTAR; serbest
alana, maskeye veya C-uzayina DOKUNMAZ. Madde 15 acisindan notrdur ve karar
yalnizca daha MUHAFAZAKAR olur.

⚠ URETIM KODU DEGISMEZ: `_gorus_hatti` surec icinde sarmalanir; string-pulling
algoritmasi URETIMIN KENDISIDIR, yalnizca KABUL OLCUTU sikilastirilir. Boylece
algoritma iki yerde iki turlu yazilmaz (madde 16).

────────────────────────────────────────────────────────────────────────────
ON KAYIT — OLCUM KOSULMADAN ONCE YAZILDI (D-107)

⚠ ORIJINAL T94 KAPISI (kayip <= 2 px · pay<3px <= 5/260) **GEVSETILMIYOR** ve
SAGLANMADIGI da gizlenmiyor: D-154 tavan modda bile 2,33 px / 7 kare olctu,
yani string-pulling tamamen kaldirilsa dahi o kapi tutmuyor.

Kullanici bu turda "kismi kazanc kabul edilir" dedi. Bu yuzden AYRI ve ACIKCA
DAHA ZAYIF bir kapi tanimlanir. Orijinal kapi kayitta DURUR; bu onun yerine
gecmez, yanina yazilir.

KISMI KABUL (hepsi birden):
    1. toplam kayip medyani   <= 4,00 px      (taban 6,61)
    2. pay < 3 px olan kare   <= 20/260       (taban 46)
    3. pay min                >= 0,50 px      (taban 0,10)
    4. yayinlanan waypoint    <= 16           (taban 8; mesaj + IKA maliyeti)
    5. rota uretilen kare     >= 258/260      (taban 258)
    6. sure artisi            <= 2 kat

RED: yukaridakilerden biri bile tutmazsa o esik REDDEDILIR. "Neredeyse tuttu"
diye kabul edilmez. Hicbir esik tutmazsa T94 kod degisikligi YAPILMAZ.
────────────────────────────────────────────────────────────────────────────
"""
import argparse
import json
import sys
import time
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(BURASI))

import costmap_path_finder as C                                   # noqa: E402
import rpi_inference as RI                                        # noqa: E402
from karar_sozlesmesi import r_gerekli_piksel                     # noqa: E402

etiket_maskesi = import_module("61_rota_moloza_basma").etiket_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
DAR_ESIK_PX = 3.0

_GERCEK_GORUS = C._gorus_hatti
_GERCEK_YOL_DUZELT = C.yol_duzelt
# 🔴 KAPSAM: esik YALNIZCA  icindeyken uygulanir.
# Ilk denememde  GLOBAL yamalanmisti; oysa ayni yordam
#  (costmap:340) ve in 606/622/636 satirlarindaki
# DOGRULAMA kontrollerinde de kullaniliyor. Global yama onlari da
# sikilastirdigi icin rota uretimi 260 -> 256/247/231 dusmustu; bu, FIKRIN
# degil OLCUM DUZENEGININ kusuruydu. Kapsam daraltildi.
AKTIF = {"dist": None, "esik": None, "icerde": False}


def _sarmal_gorus(p1, p2, gecilebilir_tam):
    """URETIMIN gorus-hatti testi + ACIKLIK ESIGI. Yalnizca REDDEDER."""
    if not _GERCEK_GORUS(p1, p2, gecilebilir_tam):
        return False
    esik = AKTIF["esik"]
    dist = AKTIF["dist"]
    if not AKTIF["icerde"] or esik is None or dist is None:
        return True
    h, w = dist.shape
    # Rasterizasyon URETIMLE AYNI kaynaktan; ikinci bir yuvarlama uretilmez.
    for x, y in C._bresenham_noktalari(p1, p2):
        xx = min(w - 1, max(0, int(x)))
        yy = min(h - 1, max(0, int(y)))
        if float(dist[yy, xx]) < esik:
            return False
    return True


def _sarmal_yol_duzelt(yol_px, gecilebilir_tam, **kw):
    """Esigi YALNIZCA string-pulling suresince ac."""
    AKTIF["icerde"] = True
    try:
        return _GERCEK_YOL_DUZELT(yol_px, gecilebilir_tam, **kw)
    finally:
        AKTIF["icerde"] = False


def maximin_tam(dist, h, w):
    ta = C._tohum_maske(None, h, w, "alt", icerik=(0, 0, w, h))
    tb = C._tohum_maske(None, h, w, "ust", icerik=(0, 0, w, h))
    lo, hi = 0.0, float(dist.max())
    for _ in range(18):
        mid = (lo + hi) / 2.0
        if C._bagli_mi((dist >= mid).astype(np.uint8), ta, tb):
            lo = mid
        else:
            hi = mid
    return lo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    kareler = []
    for o in man["ornekler"]:
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = args.kume / o["cikti"]
        mpp = o["arena"].get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        if args.sinir and len(kareler) >= args.sinir:
            break
        h, w = img.shape[:2]
        txt = (args.kume / "labels" /
               Path(o["cikti"]).relative_to("images")).with_suffix(".txt")
        gt = etiket_maskesi(txt, h, w)
        if not gt[0].any():
            continue
        kareler.append((p.name, gt, mpp, h, w))
    print(f"olculecek kare: {len(kareler)}", flush=True)

    # ESIKLER: hepsi r_gerekli ve MASKE_HATA'dan TURETILIR, ciplak sayi yok.
    def esikler(mpp):
        r = float(r_gerekli_piksel(mpp, C.R_GEREKLI_M) or 0.0)
        mh = float(C.MASKE_HATA_M) / float(mpp)
        return {
            "V0 mevcut": None,
            "V1 r + maske_hata": r + mh,
            "V2 r + 2x maske_hata": r + 2.0 * mh,
            "V3 r + 3x maske_hata": r + 3.0 * mh,
        }

    adlar = list(esikler(0.078).keys())
    sonuc = {ad: [] for ad in adlar}
    mm = {}
    C._gorus_hatti = _sarmal_gorus
    RI._gorus_hatti = _sarmal_gorus
    RI.yol_duzelt = _sarmal_yol_duzelt
    try:
        for ad in adlar:
            for i, (kare, gt, mpp, h, w) in enumerate(kareler):
                AKTIF["esik"] = esikler(mpp)[ad]
                AKTIF["dist"] = None
                t0 = time.perf_counter()
                # `dist` analyze_path icinde uretilir; ilk cagride yok. Iki
                # asamali kosum yerine dt'yi BURADA temiz maskeden uretiriz —
                # analyze_path'in kullandigi `clean` ile ayni kaynak.
                _y0, _g0, _w0, temiz0, red0, _o0 = RI.analyze_path(
                    gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
                    return_clean=True, return_reason=True, return_olcum=True)
                if temiz0 is None:
                    sonuc[ad].append({"kare": kare, "rota": False})
                    continue
                AKTIF["dist"] = cv2.distanceTransform(
                    (temiz0 > 0).astype(np.uint8), cv2.DIST_L2,
                    cv2.DIST_MASK_PRECISE)
                _y, _g, wps, temiz, red, ol = RI.analyze_path(
                    gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
                    return_clean=True, return_reason=True, return_olcum=True)
                sure = (time.perf_counter() - t0) * 1000.0 / 2.0
                if kare not in mm:
                    mm[kare] = maximin_tam(AKTIF["dist"], h, w)
                if red is not None or not ol:
                    sonuc[ad].append({"kare": kare, "rota": False})
                    continue
                p_ = np.asarray(wps, dtype=float)
                uz = float(np.sum(np.hypot(*(p_[1:] - p_[:-1]).T))) if len(wps) > 1 else 0.0
                sonuc[ad].append({
                    "kare": kare, "rota": True, "sure_ms": sure,
                    "darbogaz": float(ol["darbogaz_px"]),
                    "pay": float(ol["darbogaz_px"]) - float(ol["r_gerekli_px"]),
                    "maximin": mm[kare], "wp": len(wps or []), "uzunluk": uz})
                if (i + 1) % 60 == 0:
                    print(f"  {ad}: {i+1}/{len(kareler)}", flush=True)
    finally:
        C._gorus_hatti = _GERCEK_GORUS
        RI._gorus_hatti = _GERCEK_GORUS
        RI.yol_duzelt = _GERCEK_YOL_DUZELT

    c = "=" * 92
    print(f"\n{c}\nT94 · ACIKLIK KORUYAN STRING-PULLING (yer gercegi, MODEL YOK)\n"
          f"  kume {args.kume.name} · kare {len(kareler)}\n{c}")
    print(f"{'esik':<24}{'rota':>6}{'kayip med':>11}{'pay med':>9}"
          f"{'pay<3px':>9}{'pay min':>9}{'wp med':>8}{'uzunluk':>10}{'sure ms':>9}")
    ozet = {}
    taban_sure = None
    for ad in adlar:
        r = [k for k in sonuc[ad] if k["rota"]]
        if not r:
            print(f"{ad:<24}{'0':>6}   rota yok")
            continue
        g = lambda a: np.array([k[a] for k in r], dtype=float)
        kayip = g("maximin") - g("darbogaz")
        pay, wp, uz, sr = g("pay"), g("wp"), g("uzunluk"), g("sure_ms")
        if taban_sure is None:
            taban_sure = float(np.median(sr))
        ozet[ad] = {"rota": len(r), "kayip_med": float(np.median(kayip)),
                    "pay_med": float(np.median(pay)),
                    "dar": int((pay < DAR_ESIK_PX).sum()),
                    "pay_min": float(pay.min()), "wp_med": float(np.median(wp)),
                    "wp_maks": float(wp.max()),
                    "uzunluk_med": float(np.median(uz)),
                    "sure_med": float(np.median(sr)),
                    "sure_kat": float(np.median(sr) / max(1e-9, taban_sure))}
        print(f"{ad:<24}{len(r):>6}{np.median(kayip):>11.2f}{np.median(pay):>9.2f}"
              f"{int((pay < DAR_ESIK_PX).sum()):>9}{pay.min():>9.2f}"
              f"{np.median(wp):>8.0f}{np.median(uz):>10.1f}{np.median(sr):>9.1f}")

    print(f"\n{c}\nKISMI KABUL (on kayit, olcumden ONCE yazildi):")
    print("  kayip <= 4,00 · pay<3px <= 20 · pay min >= 0,50 · wp <= 16 ·"
          " rota >= 258 · sure <= 2 kat")
    for ad in adlar[1:]:
        o = ozet.get(ad)
        if not o:
            continue
        kos = [("kayip", o["kayip_med"] <= 4.0), ("dar", o["dar"] <= 20),
               ("pay_min", o["pay_min"] >= 0.5), ("wp", o["wp_med"] <= 16),
               ("rota", o["rota"] >= 258),
               ("sure", o["sure_kat"] <= 2.0)]
        dusen = [k for k, v in kos if not v]
        print(f"  {ad:<24} {'KABUL' if not dusen else 'RED — dusen: ' + ', '.join(dusen)}")
    print("⚠ ORIJINAL T94 kapisi (kayip <= 2 · pay<3px <= 5) AYRICA durur ve")
    print("  D-154'e gore TAVAN modda bile saglanmiyor.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"ozet": ozet, "kayitlar": sonuc},
                                        ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
