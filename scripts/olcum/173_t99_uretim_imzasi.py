"""T99 (D-399) — 89/90/91 olcumleri URETIM cagri imzasiyla yeniden.

ON KAYIT: results/t99_uretim_imzasi/ON_KAYIT.md (kollar + gecerlilik kapilari
sonuc gorulmeden yazildi).

Eski olcum imzasi (89:160, 90:276, 91:130 — ucu de ayni):
    rota_bul(mk, mpp=mpp, icerik=icerik)
Uretim (simulation/scripts/iha_haritala.py:324):
    rota_bul(costmap_maskeleri, mpp=MPP, baslangic=.., hedef=.., plan=True,
             yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
             engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI, gorsel_cikti=True)
    (`icerik` GECIRILMEZ)

Dort kol ayni maskelerle kosar (89'un sozlesmesi: kare basina TEK cikarim):
  A eski olcum · B +ankor · C +arac katmani · D tam uretim bicimi

🔴 VAKUM KORUMASI (D-375 sinifi): arac modeli yuklenmezse `obb_arac_maskesi`
BOS maske doner ve `engel_sinif_idler=(1,10)` fiilen (1,) olur — o zaman C
kolu HICBIR SEY olcmez. Bos-olmayan arac maskesi sayisi raporlanir; sifirsa
kol "VAKUMDA OLCULDU" damgalanir.
"""
import argparse
import json
import sys
import time
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from arac_maskesi import obb_arac_maskesi  # noqa: E402
from costmap_path_finder import olcek_px, rota_bul, serbest_alan  # noqa: E402
from karar_sozlesmesi import serit_no  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)
from sinif_semasi import (COSTMAP_ENGEL_KATMANLARI,  # noqa: E402
                          COSTMAP_YOL_KATMANLARI, KATMAN_ARAC)

kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu

CONF = 0.30
ARAC_CONF = 0.25
ARAC_MODEL_YOLU = REPO / "yolov8m-obb.pt"

# ON_KAYIT §1 — kollarin kwargs'i TEK yerde; cikti bunlari aynen yazar (V2).
KOLLAR = {
    "A_eski_olcum": dict(),
    "B_ankor_kor": dict(ankor=True),
    "B2_ankor_acik_serit": dict(ankor=True, ankor_kaynagi="acik_serit"),
    "C_arac": dict(ankor=True, arac=True,
                   engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI),
    "D_tam_uretim": dict(ankor=True, arac=True,
                         engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,
                         gorsel_cikti=True, icerik_yok=True),
}


def _en_yakin_gecilebilir(zemin, x, y, azami_yaricap=320):
    """(x,y)'ye EN YAKIN gecilebilir pikseli bul; yoksa None.

    NEDEN (EK-1 · EK-2): ilk vekil tohum icerik kutusunun alt-orta pikseliydi
    ve olculdu ki 6 karenin 4'unde orasi ZEMIN DEGIL. Zemine oturtmak da
    yetmedi: `koridor_adaylari` baglantiyi **C-UZAYINDA** (`dt_px >=
    r_gerekli_px`) test eder ve duvar dibindeki tek piksel C-uzayinda
    gecersizdir -> KAPALI_DAR. Uretimde `baslangic` IKA'nin GERCEKTEN
    durdugu yerdir; bir arac ancak kendi yaricapi kadar acikligi olan bir
    noktada durabilir. Bu yuzden tohum C-UZAYINA oturtulur (`z` olarak
    C-uzayi maskesi verilir). Esik gevsetmesi DEGIL; vekilin uretim
    semantigine hizalanmasidir.
    """
    z = np.asarray(zemin)
    h, w = z.shape
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < w and 0 <= yi < h and z[yi, xi]:
        return xi, yi, 0.0
    for r in range(8, azami_yaricap + 1, 8):
        y0, y1 = max(0, yi - r), min(h, yi + r + 1)
        x0, x1 = max(0, xi - r), min(w, xi + r + 1)
        pencere = z[y0:y1, x0:x1]
        noktalar = np.argwhere(pencere)
        if noktalar.size == 0:
            continue
        mutlak = noktalar + (y0, x0)
        uzak = np.hypot(mutlak[:, 0] - yi, mutlak[:, 1] - xi)
        i = int(np.argmin(uzak))
        return int(mutlak[i, 1]), int(mutlak[i, 0]), float(uzak[i])
    return None


def tohum(sekil, x, y):
    """Uretimdeki `_tohum_maskesi` gibi TEK PIKSEL tohum."""
    m = np.zeros(sekil, np.uint8)
    h, w = sekil
    xi, yi = int(round(x)), int(round(y))
    if 0 <= xi < w and 0 <= yi < h:
        m[yi, xi] = 1
    return m


def kol_kos(kol_adi, ayar, mk, arac_mk, mpp, icerik, ba, he, ba2=None):
    """Bir kolu kos; (sonuc, sure_ms) dondur.

    `ankor_kaynagi="acik_serit"` -> tohum ACIK seridin girisine konur (`ba2`).
    Bu, GERCEK ETIKET kullanan bir EN-IYI-DURUM kolodur ve raporda oyle anilir.
    """
    if ayar.get("ankor_kaynagi") == "acik_serit":
        ba = ba2 if ba2 is not None else ba
    maskeler = dict(mk)
    if ayar.get("arac"):
        maskeler[KATMAN_ARAC] = arac_mk
    kw = {"mpp": mpp, "plan": True,
          "yol_sinif_idler": COSTMAP_YOL_KATMANLARI,
          "engel_sinif_idler": ayar.get("engel_sinif_idler", (1,)),
          "gorsel_cikti": bool(ayar.get("gorsel_cikti", False)),
          "icerik": None if ayar.get("icerik_yok") else icerik}
    if ayar.get("ankor"):
        kw["baslangic"] = ba
        kw["hedef"] = he
    t0 = time.perf_counter()
    r = rota_bul(maskeler, **kw)
    return r, (time.perf_counter() - t0) * 1000.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", type=Path, default=None)
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--sinir", type=int, default=0, help="0 = tum kume")
    args = ap.parse_args()
    if args.kume is None:
        args.kume = kabul_kumesi_yolu()

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    arac_model = None
    if ARAC_MODEL_YOLU.is_file():
        arac_model = YOLO(str(ARAC_MODEL_YOLU))
        print(f"arac modeli: {ARAC_MODEL_YOLU.name}")
    else:
        print("🔴 arac modeli YOK — C/D kollari VAKUMDA olculecek")

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    kayitlar = []
    cikarim_sayaci = {"segmentasyon": 0, "arac": 0}
    arac_dolu_kare = 0

    ornekler = [o for o in man["ornekler"]
                if o.get("durum") == "YAZILDI" and o.get("arena")]
    if args.sinir:
        ornekler = ornekler[:args.sinir]

    for idx, o in enumerate(ornekler):
        p = args.kume / o["cikti"]
        if not p.is_file():
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        a = o["arena"]
        mpp = a.get("mpp")
        if not mpp:
            continue

        sq, small, icerik = _preprocess(img)
        # V3: kare basina TEK segmentasyon cikarimi (89'un sozlesmesi)
        son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        cikarim_sayaci["segmentasyon"] += 1
        mk = _maskeleri_icerige_kirp(get_masks(son, *sq.shape[:2]), icerik)

        # Arac maskesi de kare basina TEK kez; uretimle ayni kirpma yolundan
        arac_ham = obb_arac_maskesi(sq, arac_model, conf=ARAC_CONF)
        cikarim_sayaci["arac"] += 1
        arac_mk = _maskeleri_icerige_kirp({KATMAN_ARAC: arac_ham},
                                          icerik)[KATMAN_ARAC]
        arac_px = int(np.asarray(arac_mk).sum())
        if arac_px > 0:
            arac_dolu_kare += 1

        # Tohumlar (ON_KAYIT §1 + EK-1/EK-2: VEKIL — uretimde dunya
        # koordinatindan gelir; burada URETIMIN KENDI C-UZAYINA oturtulur.)
        sa = serbest_alan(mk, mpp=mpp, yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
                          engel_sinif_idler=(1,), icerik=icerik)
        r_gerekli = olcek_px(mpp)["r_gerekli_px"]
        c_uzayi_dt = sa["dt_px"]
        c_uzayi = (c_uzayi_dt >= r_gerekli).astype(np.uint8)
        zemin = c_uzayi
        sekil = sq.shape[:2]
        hx, hy, hw_, hh_ = a["hedef_kutu"]
        ix, iy, iw, ih = icerik
        he_n = _en_yakin_gecilebilir(zemin, hx + hw_ / 2.0, hy + hh_ / 2.0)
        ba_n = _en_yakin_gecilebilir(zemin, ix + iw / 2.0, iy + ih - 1)
        if he_n is None or ba_n is None:
            # Tohum oturtulamadi: bu karede ankorlu kollar OLCULEMEZ.
            kayitlar.append({"kare": p.name, "acik_serit": a.get("acik_serit"),
                             "arac_px": arac_px, "tohum_yok": True,
                             "kollar": {}})
            continue
        he = tohum(sekil, he_n[0], he_n[1])
        ba = tohum(sekil, ba_n[0], ba_n[1])

        # B2 (EK-3): tohum ACIK seridin alt girisine — EN IYI DURUM kolu.
        # Gercek etiket kullanir; uretimin KB'si serit ayrimindan ONCEDIR ve
        # t66 kadraji o ortak alani icermeyebilir. B (kor) ile B2 (etiketli)
        # gercek uretim davranisini ALT ve UST siniriyla kusatir.
        ba2 = ba
        acik = a.get("acik_serit")
        c_alt = np.argwhere(c_uzayi[iy + ih - max(2, ih // 8):iy + ih, :])
        if acik and c_alt.size:
            taban_y = iy + ih - max(2, ih // 8)
            adaylar = [(int(x), int(y) + taban_y) for y, x in c_alt
                       if serit_no(int(x), ix, iw) == acik]
            if adaylar:
                sx, sy = max(adaylar, key=lambda t: c_uzayi_dt[t[1], t[0]])
                ba2 = tohum(sekil, sx, sy)

        kare = {"kare": p.name, "acik_serit": a.get("acik_serit"),
                "arac_px": arac_px,
                "tohum_serit": serit_no(ba_n[0], ix, iw),
                "tohum_kaydirma_px": {"baslangic": round(ba_n[2], 1),
                                      "hedef": round(he_n[2], 1)},
                "kollar": {}}
        for kol_adi, ayar in KOLLAR.items():
            r, sure = kol_kos(kol_adi, ayar, mk, arac_mk, mpp, icerik,
                              ba, he, ba2=ba2)
            kare["kollar"][kol_adi] = {
                "durum": r.get("durum"), "yol_no": r.get("yol_no"),
                "guven": r.get("guven"),
                "wp": len(r.get("waypoints_px") or []),
                "sebep": r.get("sebep"), "sure_ms": round(sure, 2)}
        kayitlar.append(kare)

        # V4: determinizm — ilk 10 karede B kolunu iki kez kos, karsilastir
        if idx < 10:
            r2, _ = kol_kos("B_ankor_kor", KOLLAR["B_ankor_kor"], mk,
                            arac_mk, mpp, icerik, ba, he, ba2=ba2)
            kare["V4_determinizm"] = (
                r2.get("yol_no") == kare["kollar"]["B_ankor_kor"]["yol_no"]
                and r2.get("durum") == kare["kollar"]["B_ankor_kor"]["durum"])

    tohumsuz = [k for k in kayitlar if k.get("tohum_yok")]
    kayitlar = [k for k in kayitlar if not k.get("tohum_yok")]
    n = len(kayitlar)
    kaydirmalar = [k["tohum_kaydirma_px"]["baslangic"] for k in kayitlar]
    print(f"\nolculen kare: {n} · arac maskesi DOLU olan: {arac_dolu_kare} · "
          f"tohum oturtulamayan kare: {len(tohumsuz)}")
    if kaydirmalar:
        print(f"baslangic tohumu kaydirma px: p50={np.percentile(kaydirmalar,50):.1f} "
              f"p95={np.percentile(kaydirmalar,95):.1f} "
              f"maks={max(kaydirmalar):.1f} · kaydirma gereken kare: "
              f"{sum(1 for d in kaydirmalar if d > 0)}/{n}")

    ozet = {}
    taban = "A_eski_olcum"
    for kol in KOLLAR:
        rotali = [k for k in kayitlar if k["kollar"][kol]["yol_no"] is not None]
        durumlar = {}
        for k in kayitlar:
            d = k["kollar"][kol]["durum"]
            durumlar[d] = durumlar.get(d, 0) + 1
        sureler = np.array([k["kollar"][kol]["sure_ms"] for k in kayitlar])
        guvenler = [k["kollar"][kol]["guven"] for k in rotali
                    if k["kollar"][kol]["guven"] is not None]
        dogru = sum(1 for k in rotali
                    if k["kollar"][kol]["yol_no"] == k["acik_serit"])
        degisen = sum(1 for k in kayitlar
                      if (k["kollar"][kol]["yol_no"]
                          != k["kollar"][taban]["yol_no"]))
        ozet[kol] = {
            "rota_ureten": len(rotali), "kayip": n - len(rotali),
            "durumlar": durumlar,
            "serit_dogru": [dogru, len(rotali)],
            "tabana_gore_karar_degisimi": degisen,
            "guven_medyan": float(np.median(guvenler)) if guvenler else None,
            "sure_ms_p50": float(np.percentile(sureler, 50)),
            "sure_ms_p95": float(np.percentile(sureler, 95)),
        }
        print(f"{kol:16s} rota={len(rotali):3d}/{n} kayip={n-len(rotali):3d} "
              f"serit={dogru}/{len(rotali)} degisim={degisen:3d} "
              f"p50={ozet[kol]['sure_ms_p50']:6.1f}ms "
              f"p95={ozet[kol]['sure_ms_p95']:6.1f}ms")
        print(f"                 durumlar: {durumlar}")

    # Gecerlilik kapilari
    v1 = arac_dolu_kare > 0
    v3 = cikarim_sayaci["segmentasyon"] == n
    v4_liste = [k.get("V4_determinizm") for k in kayitlar
                if "V4_determinizm" in k]
    v4 = all(v4_liste) if v4_liste else None
    print(f"\nV1 vakum yok (arac dolu kare>0): {'GECTI' if v1 else '🔴 DUSTU'}")
    print(f"V3 kare basina tek cikarim      : {'GECTI' if v3 else '🔴 DUSTU'}")
    print(f"V4 determinizm (ilk 10)         : "
          f"{'GECTI' if v4 else ('OLCULEMEDI' if v4 is None else '🔴 DUSTU')}")
    if not v1:
        print("🔴 C ve D kollari VAKUMDA OLCULDU — arac katmani bos, "
              "engel_sinif_idler=(1,10) fiilen (1,)")

    cikti = {"_on_kayit": "results/t99_uretim_imzasi/ON_KAYIT.md",
             "_model": str(args.model),
             "tohum_oturtulamayan": len(tohumsuz),
             "tohum_kaydirma_p50": (float(np.percentile(kaydirmalar, 50))
                                    if kaydirmalar else None),
             "tohum_kaydirma_gereken": sum(1 for d in kaydirmalar if d > 0),
             "_arac_model": str(ARAC_MODEL_YOLU) if arac_model else None,
             "kollar_kwargs": {k: {kk: (list(vv) if isinstance(vv, tuple)
                                        else vv)
                                   for kk, vv in v.items()}
                               for k, v in KOLLAR.items()},   # V2
             "n": n, "arac_dolu_kare": arac_dolu_kare,
             "cikarim_sayaci": cikarim_sayaci,
             "V1_vakum_yok": v1, "V3_tek_cikarim": v3, "V4_determinizm": v4,
             "ozet": ozet, "kareler": kayitlar}
    hedef = args.json or (REPO / "results" / "t99_uretim_imzasi"
                          / "olcum_20260903.json")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
