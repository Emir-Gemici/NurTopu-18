"""T94 · KAYBIN KAYNAGI PLAN IZGARASI MI? — adim 10 px vs ince izgara.

NEDEN (REVIEW_LOG D-152 + bu turun olcumleri). Kayip ayristirildi:

    maximin TAM COZUNURLUK   36,00 px
    maximin A* IZGARASINDA   30,00 px   -> IZGARA KAYBI  6,00 px  (~%80)
    A* yolunun darbogazi     28,50 px   -> SECIM  KAYBI  1,50 px  (~%20)

Yani genis yol tam cozunurlukte VAR, A*'in izgarasinda YOK. A* kendi
izgarasinda zaten neredeyse en iyisini buluyor; ceza parametreleriyle
oynamanin (D-152: alti yapilandirma) bir sey degistirmemesinin sebebi budur.

OLCULEN IZGARA: sekil ~64 x 40 hucre, **adim = 10 piksel**.
`plan_izgarasi` MIN-havuzlar; 10x10 blokta bir tek dar piksel tum hucreyi
dar gosterir. Hucre butcesi `ROTA_PLAN_MAKS_HUCRE = 32768` iken yalniz ~2.600
hucre kullaniliyor — **butcenin %92'si bosta**.

Adim nereden geliyor: `_bagli_koridor_yolu(..., ilk_plan_adimi=min(k_open.shape))`,
yani MORFOLOJIK ACMA CEKIRDEGINDEN. `_plan_adimlari` daha ince izgarayi ancak
kaba izgara BASARISIZ olursa dener — kaba izgara basarili oldugu icin ince
izgara HIC KOSMAZ. (Olculdu: kare basina `astar` cagrisi = 1.)

BU BETIK tek soruyu sorar: ince izgara ONCE denenirse kayip kapaniyor mu?
`_plan_adimlari` surec icinde en INCE-once siralamasiyla degistirilir; URETIM
DOSYASI DEGISMEZ.

⚠ BEDEL OLCULUR: ince izgara A*'i buyutur. Sure kare basina olculup raporlanir;
sartname sureye bakar (D-108: egitim degil ama cikarim hatti da olculmustur).

On kayit (TASK_QUEUE T94): kayip medyani <= 2 px · pay<3px <= 5/260 ·
rota >= 258/260 · uzunluk artisi kayda gececek.
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

etiket_maskesi = import_module("61_rota_moloza_basma").etiket_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
DAR_ESIK_PX = 3.0

_GERCEK_PLAN_ADIMLARI = RI._plan_adimlari
_GERCEK_ASTAR = C.astar
OLCUM = {"izgara": None, "ham": None, "maximin_izgara": None}


def _ince_once(ilk_adim, sekil, hucre_butcesi=None):
    """Butceye SIGAN EN INCE adimi ONCE dene (mevcut: kaba adim once).

    Mevcut davranis ince izgarayi yalnizca FALLBACK olarak kullanir; bu
    surumde siralama tersine cevrilir. Butce ASILMAZ — yalnizca kullanilir.
    """
    adimlar = _GERCEK_PLAN_ADIMLARI(ilk_adim, sekil, hucre_butcesi) \
        if hucre_butcesi is not None else _GERCEK_PLAN_ADIMLARI(ilk_adim, sekil)
    if not adimlar:
        return adimlar
    h, w = map(int, sekil)
    butce = int(RI.ROTA_PLAN_MAKS_HUCRE)
    aday = [a for a in range(1, max(adimlar) + 1)
            if 0 < RI._plan_hucre_sayisi((h, w), a) <= butce]
    return sorted(set(aday)) or adimlar


def _sarmal_astar(g, a, hedef, bas, **kw):
    arr = np.asarray(a)
    OLCUM["izgara"] = arr.shape
    yol = _GERCEK_ASTAR(g, a, hedef, bas, **kw)
    gb = np.asarray(g) > 0
    lo, hi = 0.0, float(arr.max()) if arr.size else 0.0
    for _ in range(18):
        mid = (lo + hi) / 2.0
        if C._bagli_mi((gb & (arr >= mid)).astype(np.uint8), bas, hedef):
            lo = mid
        else:
            hi = mid
    OLCUM["maximin_izgara"] = lo
    if yol:
        OLCUM["ham"] = float(min(arr[r, c] for r, c in yol))
    return yol


def maximin_tam(temiz, h, w):
    dt = cv2.distanceTransform((temiz > 0).astype(np.uint8),
                               cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    ta = C._tohum_maske(None, h, w, "alt", icerik=(0, 0, w, h))
    tb = C._tohum_maske(None, h, w, "ust", icerik=(0, 0, w, h))
    lo, hi = 0.0, float(dt.max())
    for _ in range(18):
        mid = (lo + hi) / 2.0
        if C._bagli_mi((dt >= mid).astype(np.uint8), ta, tb):
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
    RI.astar = _sarmal_astar

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

    sonuc = {}
    mm_tam = {}
    for ad, ince in (("A mevcut (adim=morfoloji)", False),
                     ("I ince izgara ONCE", True)):
        RI._plan_adimlari = _ince_once if ince else _GERCEK_PLAN_ADIMLARI
        satir = []
        for i, (kare, gt, mpp, h, w) in enumerate(kareler):
            OLCUM.update({"izgara": None, "ham": None, "maximin_izgara": None})
            t0 = time.perf_counter()
            _y, _g, wps, temiz, red, ol = RI.analyze_path(
                gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            sure = (time.perf_counter() - t0) * 1000.0
            if kare not in mm_tam:
                mm_tam[kare] = maximin_tam(temiz, h, w) if temiz is not None else None
            if red is not None or not ol:
                satir.append({"kare": kare, "rota": False})
                continue
            p_ = np.asarray(wps, dtype=float)
            uz = float(np.sum(np.hypot(*(p_[1:] - p_[:-1]).T))) if len(wps) > 1 else 0.0
            satir.append({
                "kare": kare, "rota": True, "sure_ms": sure,
                "darbogaz": float(ol["darbogaz_px"]),
                "pay": float(ol["darbogaz_px"]) - float(ol["r_gerekli_px"]),
                "maximin_tam": mm_tam[kare],
                "maximin_izgara": OLCUM["maximin_izgara"],
                "ham": OLCUM["ham"], "izgara": OLCUM["izgara"], "uzunluk": uz})
            if (i + 1) % 20 == 0:
                print(f"  {ad}: {i+1}/{len(kareler)}", flush=True)
        sonuc[ad] = satir
    RI._plan_adimlari = _GERCEK_PLAN_ADIMLARI

    c = "=" * 88
    print(f"\n{c}\nT94 · PLAN IZGARASI COZUNURLUGU (yer gercegi, MODEL YOK)\n"
          f"  kume {args.kume.name} · kare {len(kareler)}\n{c}")
    ozet = {}
    for ad in sonuc:
        r = [k for k in sonuc[ad] if k["rota"]]
        if not r:
            print(f"{ad}: rota uretilemedi")
            continue
        f = lambda anahtar: np.array([k[anahtar] for k in r if k.get(anahtar) is not None])
        mt, mi, ham, pay, uz, sr = (f("maximin_tam"), f("maximin_izgara"),
                                    f("ham"), f("pay"), f("uzunluk"), f("sure_ms"))
        kayip = mt - np.array([k["darbogaz"] for k in r])
        izg = sorted({tuple(k["izgara"]) for k in r if k.get("izgara")})[:3]
        ozet[ad] = {"rota": len(r), "kayip_med": float(np.median(kayip)),
                    "pay_med": float(np.median(pay)),
                    "dar": int((pay < DAR_ESIK_PX).sum()),
                    "pay_min": float(pay.min()),
                    "maximin_izgara_med": float(np.median(mi)),
                    "ham_med": float(np.median(ham)),
                    "uzunluk_med": float(np.median(uz)),
                    "sure_ms_med": float(np.median(sr))}
        print(f"\n  {ad}")
        print(f"    rota {len(r)}/{len(kareler)} · izgara sekilleri (ilk 3) {izg}")
        print(f"    maximin TAM {np.median(mt):6.2f} · IZGARADA {np.median(mi):6.2f}"
              f"  -> IZGARA KAYBI {np.median(mt)-np.median(mi):5.2f} px")
        print(f"    A* yolu     {np.median(ham):6.2f}"
              f"  -> SECIM KAYBI  {np.median(mi)-np.median(ham):5.2f} px")
        print(f"    TOPLAM KAYIP medyan {np.median(kayip):5.2f} px · "
              f"pay medyan {np.median(pay):5.2f} · pay<3px {int((pay<DAR_ESIK_PX).sum())} · "
              f"pay min {pay.min():.2f}")
        print(f"    rota uzunlugu medyan {np.median(uz):7.1f} px · "
              f"SURE medyan {np.median(sr):7.1f} ms")

    print(f"\n{c}")
    print("ON KAYIT: kayip medyani <= 2 px · pay<3px <= 5/260 · rota >= 258/260")
    print("BEDEL: sure ve rota uzunlugu yukarida; sartname sureye bakar.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"ozet": ozet, "kayitlar": sonuc},
                                        ensure_ascii=False, indent=1, default=str),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
