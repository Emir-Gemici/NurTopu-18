"""T94 · V1 KURALINI PROJENIN KENDI KAPILARIYLA SINA (model ile, GPU).

NEDEN (REVIEW_LOG D-155). "Aciklik koruyan kiris" kurali on kayit kapisindan
RED aldi — ama dusen tek olcut (`kayip` = maximin - rota) carenin HEDEFLEDIGI
seyi olcmuyordu. Carenin hedefi kil payi koridorlardir ve orada etki buyuktu:

    pay < 3 px : 46 -> 5   ·   pay min : 0,10 -> 0,92 px
    bedel      : 1 kare rota · waypoint AYNI · uzunluk AYNI · sure AYNI

⚠ Olcutu SONUCU GORDUKTEN SONRA degistirmek yasaktir. Bu yuzden `kayip`
metrigi TERK EDILMIYOR ve D-155'in REDDI GERI ALINMIYOR. Bunun yerine karar,
projenin ZATEN YURURLUKTE olan kapilarina dayandirilir: K5-SIKI (T93/D-150),
karar kararliligi (A) ve kabul denetimi (K0..K4). Bu kapilar D-107/D-132'de
sonuc gorulmeden yazilmisti ve bu turda DEGISTIRILMIYOR.

KURAL (V1): `yol_duzelt`in string-pulling'i bir kirisi ancak kiris uzerindeki
en kucuk aciklik `r_gerekli + MASKE_HATA` esiginin ustundeyse kabul eder.
Yalnizca KISALTMAYI reddeder; serbest alana/maskeye/C-uzayina DOKUNMAZ.

⚠ KAPSAM: esik YALNIZCA `yol_duzelt` suresince aciktir. D-155'te `_gorus_hatti`
global yamalanmisti ve `_ankoru_ekle` + `rpi_inference`in 606/622/636
dogrulamalarini da sikilastirip rota uretimini DUSURMUSTU; o bir DUZENEK
kusuruydu.

`dist` (tam cozunurluk mesafe donusumu) `_bagli_koridor_yolu`ya gecirilir;
sarmalayici onu yakalar, boylece kare basina TEK cikarim yeter.

────────────────────────────────────────────────────────────────────────────
ON KAYIT — KOSUM YAPILMADAN ONCE YAZILDI (D-107)

Taban (v30, kayitli): K5-SIKI kesen kare 1/173 (4/3633 cift · D-150) ·
kararlilik A 8/260 (D-142/D-145) · K1 258/260 · K2 22/258 · K3 0/258 ·
K4 1/258 (D-133).

V1 KABUL EDILIR ancak SU UCU BIRDEN saglanirsa:
  1. K5-SIKI kesen kare  **0/173**   (yani `sa_000131` hicbir cekiliste
                                      kesmeyecek — kapinin kendi olcutu 0'dir)
  2. kararlilik A        **<= 8/260** (kotulesmeyecek)
  3. K1 >= 258/260 · K2 <= 22/258 · K3 == 0/258 · K4 <= 1/258

RED:
  · K5-SIKI 0'a inmiyorsa -> kural K5'i COZMUYOR, uygulanmaz.
  · A > 8/260 ise         -> kararliligi bozuyor, uygulanmaz.
  · Kabul denetiminde herhangi bir kotulesme -> uygulanmaz.
"Neredeyse" kabul edilmez. Uc sart tutarsa kod degisikligi ONERILIR; yazim ve
AYRI DENETIM ondan sonra gelir (madde 7).
────────────────────────────────────────────────────────────────────────────
"""
import sys
from pathlib import Path

import numpy as np

from ayarlar import REPO

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(BURASI))

import costmap_path_finder as C                                   # noqa: E402
import rpi_inference as RI                                        # noqa: E402
from karar_sozlesmesi import r_gerekli_piksel                     # noqa: E402

_GERCEK_GORUS = C._gorus_hatti
_GERCEK_YOL_DUZELT = C.yol_duzelt
_GERCEK_BAGLI = RI._bagli_koridor_yolu

DURUM = {"dist": None, "mpp": None, "icerde": False, "acik": False}


def _esik():
    mpp = DURUM["mpp"]
    if not mpp:
        return None
    r = r_gerekli_piksel(mpp, C.R_GEREKLI_M)
    if not r:
        return None
    return float(r) + float(C.MASKE_HATA_M) / float(mpp)


def _gorus(p1, p2, gecilebilir_tam):
    if not _GERCEK_GORUS(p1, p2, gecilebilir_tam):
        return False
    if not (DURUM["acik"] and DURUM["icerde"]):
        return True
    dist = DURUM["dist"]
    esik = _esik()
    if dist is None or esik is None:
        return True
    h, w = dist.shape
    for x, y in C._bresenham_noktalari(p1, p2):
        xx = min(w - 1, max(0, int(x)))
        yy = min(h - 1, max(0, int(y)))
        if float(dist[yy, xx]) < esik:
            return False
    return True


def _duzelt(yol_px, gecilebilir_tam, **kw):
    DURUM["icerde"] = True
    try:
        return _GERCEK_YOL_DUZELT(yol_px, gecilebilir_tam, **kw)
    finally:
        DURUM["icerde"] = False


def _bagli(koridor, icerik, dist, ilk_plan_adimi, hedef_tohumu=None):
    DURUM["dist"] = dist          # tam cozunurluk dt — guard bunu kullanir
    return _GERCEK_BAGLI(koridor, icerik, dist, ilk_plan_adimi,
                         hedef_tohumu=hedef_tohumu)


_GERCEK_ANALYZE = RI.analyze_path


def _analyze(trav_mask, *a, **kw):
    DURUM["mpp"] = kw.get("mpp")
    return _GERCEK_ANALYZE(trav_mask, *a, **kw)


def ac():
    """V1 kuralini devreye al."""
    C._gorus_hatti = _gorus
    RI._gorus_hatti = _gorus
    C.yol_duzelt = _duzelt
    RI.yol_duzelt = _duzelt
    RI._bagli_koridor_yolu = _bagli
    RI.analyze_path = _analyze
    DURUM["acik"] = True
    print("[V1] aciklik koruyan kiris DEVREDE "
          "(esik = r_gerekli + MASKE_HATA, yalniz yol_duzelt icinde)",
          flush=True)


def kapat():
    C._gorus_hatti = _GERCEK_GORUS
    RI._gorus_hatti = _GERCEK_GORUS
    C.yol_duzelt = _GERCEK_YOL_DUZELT
    RI.yol_duzelt = _GERCEK_YOL_DUZELT
    RI._bagli_koridor_yolu = _GERCEK_BAGLI
    RI.analyze_path = _GERCEK_ANALYZE
    DURUM["acik"] = False


def kosut(betik_adi, argv):
    """Hedef olcum betigini V1 ACIKKEN kostur (betik DOSYASI degismez)."""
    import importlib.util
    yol = BURASI / betik_adi
    spec = importlib.util.spec_from_file_location(f"olcum_{betik_adi[:2]}", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    # Betik kendi `analyze_path`ini ice aktarmis olabilir — yamayi ona da uygula.
    for ad in ("analyze_path",):
        if hasattr(mod, ad):
            setattr(mod, ad, _analyze)
    eski = sys.argv
    sys.argv = [betik_adi] + list(argv)
    try:
        mod.main()
    finally:
        sys.argv = eski


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("kullanim: 86_...py <betik.py> [argumanlar]")
    hedef, argv = sys.argv[1], sys.argv[2:]
    ac()
    try:
        kosut(hedef, argv)
    finally:
        kapat()
