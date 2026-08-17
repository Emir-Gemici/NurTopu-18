"""T94 · YUMUSAK KIRIS KABULU — sabit esik yerine GORELI kiyas.

NEDEN (REVIEW_LOG D-156). V1 (sabit esik: kiris acikligi >= r_gerekli +
MASKE_HATA) K5'i cozdu (sa_000131: 4/20 -> 0/20) ama kararliligi bozdu
(A: 8 -> 11/260). Teshis: V1 SUREKLI bir buyuklugu (kiris acikligi) SABIT bir
sayiyla kiyasliyor; esik civarinda kucuk bir maske degisimi kabul/red'i
ceviriyor. Proje bu kusur sinifini besinci kez goruyor (D-122 · D-145 · D-147
· D-156).

⚠ GERCEK HISTEREZIS BURADA MUMKUN DEGIL. D-126 olcup yazdi: `analyze_path`
DURUMSUZDUR, histerezis kareler-arasi bir mekanizmadir ve o gorevde uretime
BAGLANMADI. Bu yuzden "yumusatma" farkli kurulur:

    KIRIS, YERINE GECTIGI ALT YOLDAN BELIRGIN OLARAK DAHA DAR DEGILSE KABUL.

Yani kiyas SABITLE degil, kirisin YERINE GECTIGI PARCAYLA yapilir. Iki
buyukluk de AYNI maskeden turer ve gurultuyle BIRLIKTE oynar; sabit esikte
oldugu gibi bagimsiz bir esigin iki yakasinda salinmazlar.

"Belirgin" olcusu projenin OLCULMUS gurultu tabanidir:
`karar_sozlesmesi.BERABERLIK_BANDI = 0,04` (D-112/D-122; ciplak sayi degil).

DENENEN BICIMLER:
  W1  goreli    : kiris >= (1 - band) * alt_yol
  W2  gevsek    : kiris >= (1 - 3*band) * alt_yol
  W3  hedefli   : yalnizca kiris r_gerekli + MASKE_HATA'nin ALTINDAYSA
                  goreli kural uygulanir; ustundeyse hep kabul
                  (yani guvenlik sinirindan UZAKTA hic mudahale yok)

⚠ KAPSAM: kural yalnizca `yol_duzelt` suresince ve yalnizca girdi yolunun
DUGUMLERI arasindaki kirislerde uygulanir. `_maks_aralikla_bol` gibi baska
cagrilar (nokta listesi farkli) GUARD'SIZ gecer — indis bulunamazsa kabul
edilir. D-155'te global yama `_ankoru_ekle` ve dogrulama kontrollerini de
sikilastirip rota uretimini dusurmustu; o hata tekrarlanmiyor.

⚠ YON: kural yalnizca KISALTMAYI reddeder. Serbest alana, maskeye, C-uzayina
DOKUNMAZ; karar yalniz MUHAFAZAKARLASIR (madde 15 notr).

────────────────────────────────────────────────────────────────────────────
ON KAYIT — KOSUM YAPILMADAN ONCE YAZILDI (D-107)

Taban (v30): kararlilik A = 8/260 (D-142/D-145) · K5 sa_000131 kesen kosu
4/20 (D-150) · K1 258/260 (D-133).
Karsilastirma: V1 (sabit esik) A = 11/260 · K5 0/20 · 1 kare rota kaybi (D-156).

BIR BICIM KABUL EDILIR ancak SU UCU BIRDEN saglanirsa:
  1. kararlilik A     <= 8/260      (V1 burada dustu; asil sinav bu)
  2. K5 sa_000131     0/20 kesen    (V1'in cozdugu seyi KAYBETMEYECEK)
  3. rota uretilen    >= 259/260    (V1'de 259; daha kotusu kabul edilmez)

Ikincil, KAPI DEGIL, yalnizca kayda gecer: `pay < 3 px` olan kare sayisi.

RED: biri bile tutmazsa o bicim reddedilir. Hicbiri tutmazsa T94'te kod
degisikligi YAPILMAZ ve "yumusatma da cozmedi" diye yazilir.
"Neredeyse" kabul edilmez.
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
from karar_sozlesmesi import BERABERLIK_BANDI, r_gerekli_piksel   # noqa: E402

_GERCEK_GORUS = C._gorus_hatti
_GERCEK_YOL_DUZELT = C.yol_duzelt
_GERCEK_BAGLI = RI._bagli_koridor_yolu
_GERCEK_ANALYZE = RI.analyze_path

DURUM = {"dist": None, "mpp": None, "icerde": False, "bicim": None,
         "yol": None, "indis": None}

BICIMLER = {
    "W1 goreli (band)":    {"band": 1.0, "yalniz_sinirda": False},
    "W2 gevsek (3x band)": {"band": 3.0, "yalniz_sinirda": False},
    "W3 hedefli":          {"band": 1.0, "yalniz_sinirda": True},
}


def _alt_yol_darbogazi(p1, p2):
    """Kirisin YERINE GECTIGI parcanin darbogazi. Indis bulunamazsa None."""
    ind = DURUM["indis"]
    yol = DURUM["yol"]
    if not ind or not yol:
        return None
    i, j = ind.get(tuple(p1)), ind.get(tuple(p2))
    if i is None or j is None or j <= i:
        return None
    dist = DURUM["dist"]
    en_kucuk = float("inf")
    h, w = dist.shape
    for a, b in zip(yol[i:j], yol[i + 1:j + 1]):
        for x, y in C._bresenham_noktalari(a, b):
            xx = min(w - 1, max(0, int(x)))
            yy = min(h - 1, max(0, int(y)))
            en_kucuk = min(en_kucuk, float(dist[yy, xx]))
    return None if en_kucuk == float("inf") else en_kucuk


def _kiris_darbogazi(p1, p2):
    dist = DURUM["dist"]
    h, w = dist.shape
    en_kucuk = float("inf")
    for x, y in C._bresenham_noktalari(p1, p2):
        xx = min(w - 1, max(0, int(x)))
        yy = min(h - 1, max(0, int(y)))
        en_kucuk = min(en_kucuk, float(dist[yy, xx]))
    return en_kucuk


def _gorus(p1, p2, gecilebilir_tam):
    if not _GERCEK_GORUS(p1, p2, gecilebilir_tam):
        return False
    bicim = DURUM["bicim"]
    if not (DURUM["icerde"] and bicim and DURUM["dist"] is not None):
        return True
    alt = _alt_yol_darbogazi(p1, p2)
    if alt is None:            # indis yok (or. _maks_aralikla_bol) -> GUARD YOK
        return True
    kiris = _kiris_darbogazi(p1, p2)
    if bicim["yalniz_sinirda"]:
        mpp = DURUM["mpp"]
        r = r_gerekli_piksel(mpp, C.R_GEREKLI_M) if mpp else None
        if r:
            sinir = float(r) + float(C.MASKE_HATA_M) / float(mpp)
            if kiris >= sinir:
                return True    # guvenlik sinirindan UZAK -> mudahale yok
    band = float(BERABERLIK_BANDI) * float(bicim["band"])
    return kiris >= (1.0 - band) * alt


def _duzelt(yol_px, gecilebilir_tam, **kw):
    DURUM["icerde"] = True
    DURUM["yol"] = [tuple(p) for p in yol_px]
    DURUM["indis"] = {}
    for k, p in enumerate(DURUM["yol"]):
        DURUM["indis"].setdefault(p, k)
    try:
        return _GERCEK_YOL_DUZELT(yol_px, gecilebilir_tam, **kw)
    finally:
        DURUM["icerde"] = False
        DURUM["yol"] = None
        DURUM["indis"] = None


def _bagli(koridor, icerik, dist, ilk_plan_adimi, hedef_tohumu=None):
    DURUM["dist"] = dist
    return _GERCEK_BAGLI(koridor, icerik, dist, ilk_plan_adimi,
                         hedef_tohumu=hedef_tohumu)


def _analyze(trav_mask, *a, **kw):
    DURUM["mpp"] = kw.get("mpp")
    return _GERCEK_ANALYZE(trav_mask, *a, **kw)


def ac(bicim_adi):
    DURUM["bicim"] = BICIMLER[bicim_adi]
    C._gorus_hatti = _gorus
    RI._gorus_hatti = _gorus
    C.yol_duzelt = _duzelt
    RI.yol_duzelt = _duzelt
    RI._bagli_koridor_yolu = _bagli
    RI.analyze_path = _analyze
    print(f"[{bicim_adi}] DEVREDE · band={BERABERLIK_BANDI}"
          f"x{DURUM['bicim']['band']} · yalniz_sinirda="
          f"{DURUM['bicim']['yalniz_sinirda']}", flush=True)


def kapat():
    DURUM["bicim"] = None
    C._gorus_hatti = _GERCEK_GORUS
    RI._gorus_hatti = _GERCEK_GORUS
    C.yol_duzelt = _GERCEK_YOL_DUZELT
    RI.yol_duzelt = _GERCEK_YOL_DUZELT
    RI._bagli_koridor_yolu = _GERCEK_BAGLI
    RI.analyze_path = _GERCEK_ANALYZE


def kosut(betik_adi, argv):
    import importlib.util
    yol = BURASI / betik_adi
    spec = importlib.util.spec_from_file_location(f"olcum_{betik_adi[:2]}", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if hasattr(mod, "analyze_path"):
        mod.analyze_path = _analyze
    eski = sys.argv
    sys.argv = [betik_adi] + list(argv)
    try:
        mod.main()
    finally:
        sys.argv = eski


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("kullanim: 87_...py <bicim> <betik.py> [argumanlar]")
    bicim, hedef, argv = sys.argv[1], sys.argv[2], sys.argv[3:]
    eslesen = [b for b in BICIMLER if b.startswith(bicim)]
    if len(eslesen) != 1:
        raise SystemExit(f"bicim belirsiz: {bicim} -> {eslesen or list(BICIMLER)}")
    ac(eslesen[0])
    try:
        kosut(hedef, argv)
    finally:
        kapat()
