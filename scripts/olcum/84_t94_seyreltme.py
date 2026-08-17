"""T94 · SON ADAY: `yol_duzelt` string-pulling'i acikligi ne kadar yiyor?

NEDEN (REVIEW_LOG D-152 + D-153). Elenen adaylar: ceza parametreleri (lam/us),
arama izgarasinin C-uzayina kisitlanmasi, `r_gerekli_m` gecirilmesi, plan
izgarasi cozunurlugu. Kalan tek aday waypoint duzeltme/seyreltmesi.

⚠ D-153'TE BIR OLCUM KUSURU VARDI, BURADA DUZELTILIYOR. Orada "son islem
kaybi" diye raporlanan sayi `ham` (MIN-HAVUZLANMIS plan izgarasi birimi) ile
`darbogaz` (TAM COZUNURLUK) farkiydi — iki AYRI buyukluk. Mevcut izgarada
-1,00 px cikmasi (negatif!) bunun isaretiydi. Burada ikisi de TAM
COZUNURLUKTE olculur.

HANGI ASAMA? `analyze_path` olcumu KANONIK yol uzerinde yapar
(`rpi_inference.py:1224`), yani `n_waypoints` karara GIRMEZ (CONTRACTS SS6.4/5).
Dolayisiyla suclu aday `_rotayi_ornekle` DEGIL, `yol_duzelt`in gorus-hatti
string-pulling'idir: A*'in girintili yolunu uzun KIRISLERLE degistirir ve
kirisler kose keser.

OLCULEN UC BUYUKLUK (hepsi TAM COZUNURLUK dt'si uzerinde):
    ham_tam   : A*'in ham yolunun (yol_px) darbogazi
    kanonik   : `yol_duzelt` ciktisinin darbogazi   (= uretimin `darbogaz_px`i)
    maximin   : alttan uste giden yollarin en iyi darbogazi

    STRING-PULLING KAYBI = ham_tam - kanonik

TAVAN DENEMESI (B modu): `yol_duzelt` KIMLIK yapilir (ham yol aynen gecer).
Bu DAGITILABILIR BIR COZUM DEGILDIR (waypoint sayisi patlar); yalnizca
string-pulling'i duzeltmenin EN COK ne kazandirabilecegini SINIRLAR.

⚠ Madde 15: kimlik yapmak rotayi UZATIR/dugum sayisini artirir, serbest alani
BUYUTMEZ. Olcum guvenlik yonunu bozmaz.

ON KAYIT (olcum KOSULMADAN once yazildi):
  (a) string-pulling kaybi medyani <= 1 px  -> ADAY ELENIR; T94'un tanimli
      hicbir nedeni kalmaz ve bu ACIKCA yazilir.
  (b) >= 3 px                               -> ADAY DOGRULANDI.
  (c) 1-3 px arasi                          -> KISMI; tek basina yetmez.
  Ayrica B modu T94 kapisini (kayip <= 2 px · pay<3px <= 5/260) tutturmuyorsa,
  string-pulling duzeltilse BILE gorev kapanmaz — oyle yazilir.
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

etiket_maskesi = import_module("61_rota_moloza_basma").etiket_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
DAR_ESIK_PX = 3.0

_GERCEK_YOL_DUZELT = RI.yol_duzelt
YAKALA = {"giris": None, "cikis": None}


def _sarmal_duzelt(yol_px, gecilebilir_tam, **kw):
    YAKALA["giris"] = list(yol_px)
    cikis = _GERCEK_YOL_DUZELT(yol_px, gecilebilir_tam, **kw)
    YAKALA["cikis"] = list(cikis)
    return cikis


def _kimlik_duzelt(yol_px, gecilebilir_tam, **kw):
    """TAVAN denemesi: string-pulling YOK, ham yol aynen gecer."""
    YAKALA["giris"] = list(yol_px)
    YAKALA["cikis"] = list(yol_px)
    return list(yol_px)


def _polyline_darbogazi(nokta, dist):
    """Polyline'in LINE_8 pikselleri uzerinde min dt — uretimle AYNI kaynak."""
    if not nokta or len(nokta) < 2:
        return None
    pikseller = RI._rota_pikselleri(nokta)
    h, w = dist.shape
    en_kucuk = float("inf")
    for px, py in pikseller:
        xx = min(w - 1, max(0, int(px)))
        yy = min(h - 1, max(0, int(py)))
        en_kucuk = min(en_kucuk, float(dist[yy, xx]))
    return None if en_kucuk == float("inf") else en_kucuk


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

    mm = {}
    sonuc = {}
    for ad, fn in (("A mevcut (string-pulling VAR)", _sarmal_duzelt),
                   ("B TAVAN (string-pulling YOK)", _kimlik_duzelt)):
        RI.yol_duzelt = fn
        satir = []
        for i, (kare, gt, mpp, h, w) in enumerate(kareler):
            YAKALA.update({"giris": None, "cikis": None})
            _y, _g, wps, temiz, red, ol = RI.analyze_path(
                gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            if kare not in mm:
                mm[kare] = maximin_tam(temiz, h, w) if temiz is not None else None
            if red is not None or not ol:
                satir.append({"kare": kare, "rota": False})
                continue
            dist = cv2.distanceTransform((temiz > 0).astype(np.uint8),
                                         cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
            ham = _polyline_darbogazi(YAKALA["giris"], dist)
            kan = _polyline_darbogazi(YAKALA["cikis"], dist)
            satir.append({
                "kare": kare, "rota": True,
                "ham_tam": ham, "kanonik": kan,
                "darbogaz": float(ol["darbogaz_px"]),
                "pay": float(ol["darbogaz_px"]) - float(ol["r_gerekli_px"]),
                "maximin": mm[kare],
                "dugum_giris": len(YAKALA["giris"] or []),
                "dugum_cikis": len(YAKALA["cikis"] or []),
                "wp": len(wps or [])})
            if (i + 1) % 40 == 0:
                print(f"  {ad}: {i+1}/{len(kareler)}", flush=True)
        sonuc[ad] = satir
    RI.yol_duzelt = _GERCEK_YOL_DUZELT

    c = "=" * 86
    print(f"\n{c}\nT94 · SEYRELTME (yol_duzelt string-pulling) — TAM COZUNURLUK\n"
          f"  kume {args.kume.name} · kare {len(kareler)}\n{c}")
    ozet = {}
    for ad in sonuc:
        r = [k for k in sonuc[ad] if k["rota"] and k.get("ham_tam") is not None]
        if not r:
            print(f"{ad}: olculebilir kare yok")
            continue
        g = lambda a: np.array([k[a] for k in r], dtype=float)
        ham, kan, dar, pay, mmv = g("ham_tam"), g("kanonik"), g("darbogaz"), g("pay"), g("maximin")
        sp_kayip = ham - kan
        ozet[ad] = {
            "kare": len(r),
            "string_pulling_kayip_med": float(np.median(sp_kayip)),
            "string_pulling_kayip_maks": float(sp_kayip.max()),
            "sp_kayip_2px_ustu": int((sp_kayip > 2).sum()),
            "toplam_kayip_med": float(np.median(mmv - dar)),
            "pay_med": float(np.median(pay)), "pay_min": float(pay.min()),
            "dar": int((pay < DAR_ESIK_PX).sum()),
            "dugum_giris_med": float(np.median(g("dugum_giris"))),
            "dugum_cikis_med": float(np.median(g("dugum_cikis"))),
            "wp_med": float(np.median(g("wp")))}
        print(f"\n  {ad}   (n={len(r)})")
        print(f"    ham A* yolu darbogazi (TAM COZ.)   medyan {np.median(ham):6.2f} px")
        print(f"    kanonik yol darbogazi (TAM COZ.)   medyan {np.median(kan):6.2f} px")
        print(f"    STRING-PULLING KAYBI               medyan {np.median(sp_kayip):6.2f} px"
              f"  · maks {sp_kayip.max():6.2f}  · >2px olan {int((sp_kayip>2).sum())}/{len(r)}")
        print(f"    maximin {np.median(mmv):6.2f}  ->  TOPLAM KAYIP medyan {np.median(mmv-dar):6.2f} px")
        print(f"    pay medyan {np.median(pay):6.2f} · pay<3px {int((pay<DAR_ESIK_PX).sum())} · pay min {pay.min():.2f}")
        print(f"    dugum: giris {np.median(g('dugum_giris')):.0f} -> cikis "
              f"{np.median(g('dugum_cikis')):.0f} · yayinlanan wp {np.median(g('wp')):.0f}")

    print(f"\n{c}")
    print("ON KAYIT: sp kaybi <= 1 px -> ADAY ELENIR · >= 3 px -> DOGRULANDI")
    print("T94 kapisi: toplam kayip <= 2 px · pay<3px <= 5/260")
    print("B modu DAGITILABILIR DEGILDIR (dugum sayisi patlar); TAVAN olcer.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"ozet": ozet, "kayitlar": sonuc},
                                        ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
