"""T94 · PLANLAYICI TARAMASI — rota neden ulasabilecegi en iyi darbogazin altinda kaliyor?

NEDEN (REVIEW_LOG D-151). Yer gercegiyle olculdu: alttan uste giden yollarin
EN IYI darbogazi (maximin) medyan 36,0 px iken rota 28,4 px'i seciyor; dar
karelerde maximin 24,67, rota 15,09 (medyan 9 px kayip) ve dar karelerin
45/46'sinda rahat gecilebilir bir yol ZATEN VARDI.

D-151 kokeni "LAMBDA_ACIKLIK=3,0 kucuk" diye HIPOTEZ etmisti. Kod okunca daha
kesin iki aday cikti (`rpi_inference._bagli_koridor_yolu` -> `astar` cagrisi):

  (1) ARAMA IZGARASI C-UZAYI DEGIL. `gecilebilir_plan = dt_plan > 0` — yani
      HAM serbest alan. C-uzayi (`dist >= r_gerekli_px`) yalnizca BAGLANTI
      testinde kullaniliyor; arama, govde acikligini saglamayan hucreleri de
      degerlendiriyor ve guvenlik ancak sonradan `rota_dogrula` ile
      uygulaniyor. Fail-late; rotayi sinira yasliyor.
  (2) `r_gerekli_m=0.0` GECILIYOR. `astar`in cezasi
      `u = (doyum - aciklik) / (doyum - r_gerekli)`; r_gerekli 0 verilince
      govde sinirina YAKLASMANIN artan bir cezasi KALMIYOR.

⚠ Madde 15 yonu: (1)'in duzeltilmesi arama uzayini yalniz DARALTIR
({dt>=r} ⊆ {dt>0}), yani serbest alani BUYUTMEZ.

BU BETIK URETIM KODUNA DOKUNMAZ. `rpi_inference.astar` bir sarmalayiciyla
degistirilir; sarmalayici yalnizca izgarayi ve ceza parametrelerini yeniden
yazip GERCEK `astar`i cagirir. Boylece tek kaynak korunur.

On kayit TASK_QUEUE T94'te, bu tarama KOSULMADAN once yazildi:
  kayip medyani <= 2 px · pay<3px kare <= 5/260 · K1 >= 258/260 ·
  test_rota_sentetik 15/15 · K2/K3 kotulesmeyecek ·
  rota UZUNLUGU artisi olculup kayda gececek.
"""
import argparse
import json
import sys
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

_GERCEK_ASTAR = C.astar
# Kare basina degisen baglam; sarmalayici buradan okur.
AKTIF = {"r_px": None, "mod": None}


def _sarmalayici(gecilebilir_h, aciklik_m_h, hedef_h, baslangic_h, *,
                 adim_m, r_gerekli_m, doyum_m=C.DOYUM_CARPANI_M,
                 lam=C.LAMBDA_ACIKLIK, us=C.US_ACIKLIK):
    """Izgarayi/cezayi moda gore yeniden yaz, sonra GERCEK astar'i cagir."""
    mod = AKTIF["mod"] or {}
    r_px = AKTIF["r_px"]
    g, rg = gecilebilir_h, r_gerekli_m
    if mod.get("cuzay") and r_px:
        # C-UZAYI IZGARASI: yalnizca govde acikligini saglayan hucreler.
        # `aciklik_m_h` bu cagri yerinde PIKSEL cinsindendir (dt_plan).
        g = np.asarray(gecilebilir_h) & (np.asarray(aciklik_m_h) >= float(r_px))
    if mod.get("r_gercek") and r_px:
        rg = float(r_px)
    yol = _GERCEK_ASTAR(g, aciklik_m_h, hedef_h, baslangic_h,
                        adim_m=adim_m, r_gerekli_m=rg, doyum_m=doyum_m,
                        lam=mod.get("lam", lam), us=mod.get("us", us))
    # HAM A* YOLUNUN darbogazi: duzeltme/seyreltme ONCESI. Nihai 
    # duzeltilmis waypointlerden olculur; ikisi ayrisiyorsa kayip PLANLAYICIDA
    # degil SON ISLEMDE demektir.
    if yol:
        a = np.asarray(aciklik_m_h)
        AKTIF["ham"] = float(min(a[r, c] for r, c in yol))
    return yol


MODLAR = [
    ("A mevcut",              {}),
    ("B C-uzayi izgarasi",    {"cuzay": True}),
    ("C B + r_gercek",        {"cuzay": True, "r_gercek": True}),
    ("D C + lam=6",           {"cuzay": True, "r_gercek": True, "lam": 6.0}),
    ("E C + lam=12",          {"cuzay": True, "r_gercek": True, "lam": 12.0}),
    ("F C + us=1",            {"cuzay": True, "r_gercek": True, "us": 1.0}),
]


def maximin(temiz, h, w):
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


def yol_uzunlugu(wps):
    if not wps or len(wps) < 2:
        return 0.0
    p = np.asarray(wps, dtype=float)
    return float(np.sum(np.hypot(*(p[1:] - p[:-1]).T)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    RI.astar = _sarmalayici          # URETIM DOSYASI DEGISMEZ, yalniz bu surec

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
    mm_onbellek = {}
    for ad, mod in MODLAR:
        AKTIF["mod"] = mod
        satir = []
        for i, (kare, gt, mpp, h, w) in enumerate(kareler):
            AKTIF["r_px"] = r_gerekli_piksel(mpp, C.R_GEREKLI_M)
            AKTIF["ham"] = None
            _y, _g, wps, temiz, red, ol = RI.analyze_path(
                gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            if kare not in mm_onbellek:
                mm_onbellek[kare] = maximin(temiz, h, w) if temiz is not None else None
            mm = mm_onbellek[kare]
            if red is not None or not ol:
                satir.append({"kare": kare, "rota": False})
                continue
            satir.append({
                "kare": kare, "rota": True,
                "darbogaz": float(ol["darbogaz_px"]),
                "r_px": float(ol["r_gerekli_px"]),
                "pay": float(ol["darbogaz_px"]) - float(ol["r_gerekli_px"]),
                "maximin": mm,
                "kayip": (mm - float(ol["darbogaz_px"])) if mm else None,
                "ham_darbogaz": AKTIF.get("ham"),
                "uzunluk": yol_uzunlugu(wps)})
            if (i + 1) % 60 == 0:
                print(f"  {ad}: {i+1}/{len(kareler)}", flush=True)
        sonuc[ad] = satir

    taban_uz = None
    c = "=" * 84
    print(f"\n{c}\nT94 · PLANLAYICI TARAMASI (yer gercegi, MODEL YOK)\n"
          f"  kume {args.kume.name} · kare {len(kareler)}\n{c}")
    print(f"{'mod':<22}{'rota':>7}{'kayip med':>11}{'kayip min':>11}"
          f"{'pay med':>9}{'pay<3px':>9}{'pay min':>9}{'uzunluk':>10}{'uz.%':>8}")
    ozet = {}
    for ad, _m in MODLAR:
        r = [k for k in sonuc[ad] if k["rota"]]
        if not r:
            print(f"{ad:<22}{'0':>7}   (rota uretilemedi)")
            continue
        kayip = np.array([k["kayip"] for k in r if k["kayip"] is not None])
        pay = np.array([k["pay"] for k in r])
        uz = np.array([k["uzunluk"] for k in r])
        if taban_uz is None:
            taban_uz = float(np.median(uz))
        artis = 100.0 * (float(np.median(uz)) / taban_uz - 1.0)
        ozet[ad] = {"rota": len(r), "kayip_med": float(np.median(kayip)),
                    "kayip_min": float(kayip.min()),
                    "pay_med": float(np.median(pay)), "pay_min": float(pay.min()),
                    "dar": int((pay < DAR_ESIK_PX).sum()),
                    "uzunluk_med": float(np.median(uz)), "uzunluk_artis_yuzde": artis}
        ham = np.array([k["ham_darbogaz"] for k in r if k.get("ham_darbogaz")])
        if ham.size:
            print(f"   [{ad}] HAM A* darbogazi medyan {np.median(ham):.2f} px "
                  f"· nihai medyan {np.median([k['darbogaz'] for k in r]):.2f} px "
                  f"· SON ISLEM KAYBI {np.median(ham)-np.median([k['darbogaz'] for k in r]):.2f} px")
        print(f"{ad:<22}{len(r):>7}{np.median(kayip):>11.2f}{kayip.min():>11.2f}"
              f"{np.median(pay):>9.2f}{int((pay < DAR_ESIK_PX).sum()):>9}"
              f"{pay.min():>9.2f}{np.median(uz):>10.1f}{artis:>+8.1f}")

    print(f"\n{c}")
    print("ON KAYIT (TASK_QUEUE T94, tarama KOSULMADAN once yazildi):")
    print("  kayip medyani <= 2 px · pay<3px kare <= 5 · rota >= 258")
    print("  ROTA UZUNLUGU ARTISI kayda gececek (sartname sureye bakar).")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"ozet": ozet, "kayitlar": sonuc},
                                        ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
