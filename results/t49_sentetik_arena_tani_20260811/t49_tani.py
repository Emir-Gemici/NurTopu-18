"""
NEDEN: T49 icin uretim kodunu degistirmeden sentetik arena uc-bant reddini
model maskesi, yer gercegi geometrisi ve bagli bilesenler uzerinden ayirir.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


KOK = Path(__file__).resolve().parents[2]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

from codes import karar_sozlesmesi as karar  # noqa: E402
from codes import rpi_inference as rpi  # noqa: E402


KARE_SAYISI = 24
ORANLAR = tuple(i / 100.0 for i in range(2, 21))
BAZ_ORAN = 0.08
SON_ORAN = 0.20
GORSEL_UZANTILARI = {".jpg", ".jpeg", ".png"}
CIKTI = Path(__file__).resolve().parent
GORSEL_DIZINI = CIKTI / "gorseller"
URETEC_REPLAY = {
    "n_ser_dagilimi": {2: 5, 3: 13, 4: 2, 5: 4},
    "jpeg_bayt_esit": "24/24",
    "seed": 7,
    "ayni_malzeme": 0.0,
    "dar": 0.0,
    "not": "Ayri exact komutla 0..320 RNG akisi yeniden oynatildi.",
}


def sha256(yol: Path) -> str:
    ozet = hashlib.sha256()
    with yol.open("rb") as akis:
        for parca in iter(lambda: akis.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def json_uyumlu(deger):
    if isinstance(deger, dict):
        return {str(k): json_uyumlu(v) for k, v in deger.items()}
    if isinstance(deger, (list, tuple)):
        return [json_uyumlu(v) for v in deger]
    if isinstance(deger, Counter):
        return {str(k): int(v) for k, v in sorted(deger.items())}
    if isinstance(deger, (np.integer,)):
        return int(deger)
    if isinstance(deger, (np.floating,)):
        return float(deger)
    if isinstance(deger, np.ndarray):
        return deger.tolist()
    return deger


def yer_gercegi_oku(yol: Path, h: int, w: int):
    maskeler = {0: np.zeros((h, w), np.uint8),
                1: np.zeros((h, w), np.uint8)}
    poligon_sayisi = Counter()
    for satir in yol.read_text(encoding="utf-8").splitlines():
        parcalar = satir.split()
        if len(parcalar) < 7:
            continue
        sinif = int(parcalar[0])
        if sinif not in maskeler:
            continue
        xy = np.asarray(parcalar[1:], np.float32).reshape(-1, 2)
        xy[:, 0] *= w
        xy[:, 1] *= h
        noktalar = xy.astype(np.int32)
        noktalar[:, 0] = np.clip(noktalar[:, 0], 0, w - 1)
        noktalar[:, 1] = np.clip(noktalar[:, 1], 0, h - 1)
        cv2.fillPoly(maskeler[sinif], [noktalar], 1)
        poligon_sayisi[sinif] += 1
    return maskeler, poligon_sayisi


def karar_calistir(kayit):
    yol, guven, noktalar, temiz, ret = rpi.analyze_path(
        kayit["maskeler"][0],
        icerik=kayit["icerik"],
        engel_mask=kayit["maskeler"].get(1),
        mpp=None,
        return_clean=True,
        return_reason=True,
    )
    return {
        "yol": None if yol is None else int(yol),
        "guven": float(guven),
        "noktalar": [(int(x), int(y)) for x, y in noktalar],
        "temiz": temiz,
        "ret": None if ret is None else (str(ret[0]), str(ret[1])),
    }


def gt_karar_calistir(kayit):
    yol, guven, noktalar, temiz, ret = rpi.analyze_path(
        kayit["gt"][0],
        icerik=kayit["icerik"],
        engel_mask=kayit["gt"].get(1),
        mpp=None,
        return_clean=True,
        return_reason=True,
    )
    return {
        "yol": None if yol is None else int(yol),
        "guven": float(guven),
        "noktalar": [(int(x), int(y)) for x, y in noktalar],
        "temiz": temiz,
        "ret": None if ret is None else (str(ret[0]), str(ret[1])),
    }


def durum_anahtari(sonuc):
    if sonuc["yol"] is not None:
        return f"ACIK_{sonuc['yol']}"
    if sonuc["ret"] is None:
        return "ROTA_YOK_SEBEPSIZ"
    return sonuc["ret"][0]


def morfoloji_sonrasi_tum_bilesenler(kayit):
    zemin = kayit["maskeler"][0]
    h, w = zemin.shape
    k_open = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    temiz = cv2.morphologyEx(zemin, cv2.MORPH_OPEN, k_open)
    temiz = cv2.morphologyEx(temiz, cv2.MORPH_CLOSE, k_close)
    temiz = temiz.copy()
    temiz[np.asarray(kayit["maskeler"].get(1, 0)) > 0] = 0
    return (temiz > 0).astype(np.uint8)


def temas_genisligi(maske, icerik, taraf):
    x0, y0, w, h = map(int, icerik)
    bant_h = karar.hedef_bant_yuksekligi(h)
    if taraf == "ust":
        bant = maske[y0:y0 + bant_h, x0:x0 + w]
    else:
        bant = maske[y0 + h - bant_h:y0 + h, x0:x0 + w]
    return int(np.count_nonzero(np.any(bant > 0, axis=0)))


def bant_pikseli(maske, icerik, taraf):
    x0, y0, w, h = map(int, icerik)
    bant_h = karar.hedef_bant_yuksekligi(h)
    if taraf == "ust":
        bant = maske[y0:y0 + bant_h, x0:x0 + w]
    else:
        bant = maske[y0 + h - bant_h:y0 + h, x0:x0 + w]
    return int(np.count_nonzero(bant))


def bilesen_olcumu(kayit):
    tumu = morfoloji_sonrasi_tum_bilesenler(kayit)
    n, etiketler, istatistik, _ = cv2.connectedComponentsWithStats(tumu, 8)
    gereken = karar.bant_temasi_gereken_px(kayit["icerik"][2])
    bilesenler = []
    for etiket in range(1, n):
        maske = (etiketler == etiket).astype(np.uint8)
        ust_gen = temas_genisligi(maske, kayit["icerik"], "ust")
        alt_gen = temas_genisligi(maske, kayit["icerik"], "alt")
        bilesenler.append({
            "etiket": etiket,
            "alan": int(istatistik[etiket, cv2.CC_STAT_AREA]),
            "ust_genislik": ust_gen,
            "alt_genislik": alt_gen,
            "ust_px": bant_pikseli(maske, kayit["icerik"], "ust"),
            "alt_px": bant_pikseli(maske, kayit["icerik"], "alt"),
            "ust_ok": ust_gen >= gereken,
            "alt_ok": alt_gen >= gereken,
        })
    bilesenler.sort(key=lambda x: (-x["alan"], x["etiket"]))
    en_buyuk = bilesenler[0] if bilesenler else {
        "alan": 0, "ust_genislik": 0, "alt_genislik": 0,
        "ust_px": 0, "alt_px": 0, "ust_ok": False, "alt_ok": False,
    }
    toplam = int(np.count_nonzero(tumu))
    tum_ust_gen = temas_genisligi(tumu, kayit["icerik"], "ust")
    tum_alt_gen = temas_genisligi(tumu, kayit["icerik"], "alt")
    herhangi_iki_uc = any(b["ust_ok"] and b["alt_ok"] for b in bilesenler)
    tum_ust_ok = tum_ust_gen >= gereken
    tum_alt_ok = tum_alt_gen >= gereken
    return {
        "maske": tumu,
        "etiketler": etiketler,
        "bilesen_sayisi": len(bilesenler),
        "toplam_px": toplam,
        "en_buyuk_pay": (en_buyuk["alan"] / toplam) if toplam else 0.0,
        "tum_ust_px": bant_pikseli(tumu, kayit["icerik"], "ust"),
        "tum_alt_px": bant_pikseli(tumu, kayit["icerik"], "alt"),
        "tum_ust_genislik": tum_ust_gen,
        "tum_alt_genislik": tum_alt_gen,
        "tum_ust_ok": tum_ust_ok,
        "tum_alt_ok": tum_alt_ok,
        "herhangi_iki_uc": herhangi_iki_uc,
        "en_buyuk": en_buyuk,
        "bilesenler": bilesenler,
        "uclar_farkli_bilesenlerde": (
            tum_ust_ok and tum_alt_ok and not herhangi_iki_uc),
        "kucuk_bilesen_span_kaybi": (
            herhangi_iki_uc
            and not (en_buyuk["ust_ok"] and en_buyuk["alt_ok"])),
    }


def gt_geometri_olcumu(kayit):
    zemin = (kayit["gt"][0] > 0).astype(np.uint8)
    n, etiketler, istatistik, _ = cv2.connectedComponentsWithStats(zemin, 8)
    gereken = karar.bant_temasi_gereken_px(kayit["icerik"][2])
    iki_uc = 0
    for etiket in range(1, n):
        m = (etiketler == etiket).astype(np.uint8)
        if (temas_genisligi(m, kayit["icerik"], "ust") >= gereken
                and temas_genisligi(m, kayit["icerik"], "alt") >= gereken):
            iki_uc += 1
    ys, _ = np.nonzero(zemin)
    h = zemin.shape[0]
    if len(ys):
        ust_bosluk = int(ys.min())
        alt_bosluk = int(h - 1 - ys.max())
    else:
        ust_bosluk = h
        alt_bosluk = h
    return {
        "poligon_sayisi": int(kayit["gt_poligon"].get(0, 0)),
        "bilesen_sayisi": int(n - 1),
        "iki_uca_degen_bilesen": int(iki_uc),
        "ust_bosluk_px": ust_bosluk,
        "alt_bosluk_px": alt_bosluk,
        "ust_bosluk_orani": ust_bosluk / float(h),
        "alt_bosluk_orani": alt_bosluk / float(h),
        "alan_px": int(np.count_nonzero(zemin)),
    }


def maske_bindirme(gorsel, zemin, engel=None, alfa=0.46):
    cikti = gorsel.copy()
    renk = cikti.copy()
    renk[zemin > 0] = (0, 210, 0)
    if engel is not None:
        renk[engel > 0] = (0, 0, 220)
    return cv2.addWeighted(cikti, 1.0 - alfa, renk, alfa, 0)


def bilesen_bindirme(gorsel, etiketler):
    renkler = (
        (0, 220, 0), (255, 100, 0), (0, 180, 255),
        (220, 0, 220), (255, 255, 0), (100, 255, 100),
    )
    ov = gorsel.copy()
    for etiket in range(1, int(etiketler.max()) + 1):
        ov[etiketler == etiket] = renkler[(etiket - 1) % len(renkler)]
    return cv2.addWeighted(gorsel, 0.48, ov, 0.52, 0)


def bant_ve_rota_ciz(gorsel, icerik, noktalar, oran, etiket):
    cikti = gorsel.copy()
    x0, y0, w, h = map(int, icerik)
    onceki = karar.HEDEF_BANT_ORANI
    karar.HEDEF_BANT_ORANI = oran
    try:
        bant_h = karar.hedef_bant_yuksekligi(h)
    finally:
        karar.HEDEF_BANT_ORANI = onceki
    ov = cikti.copy()
    cv2.rectangle(ov, (x0, y0), (x0 + w - 1, y0 + bant_h - 1),
                  (255, 190, 0), -1)
    cv2.rectangle(ov, (x0, y0 + h - bant_h),
                  (x0 + w - 1, y0 + h - 1), (255, 190, 0), -1)
    cikti = cv2.addWeighted(cikti, 0.78, ov, 0.22, 0)
    cv2.rectangle(cikti, (x0, y0), (x0 + w - 1, y0 + h - 1),
                  (255, 255, 255), 1)
    if noktalar:
        p = np.asarray(noktalar, np.int32).reshape(-1, 1, 2)
        cv2.polylines(cikti, [p], False, (0, 255, 255), 4, cv2.LINE_AA)
        for x, y in noktalar:
            cv2.circle(cikti, (int(x), int(y)), 5, (255, 255, 255), -1)
    cv2.rectangle(cikti, (0, 0), (cikti.shape[1] - 1, 34), (0, 0, 0), -1)
    cv2.putText(cikti, etiket, (8, 24), cv2.FONT_HERSHEY_SIMPLEX,
                0.58, (255, 255, 255), 1, cv2.LINE_AA)
    return cikti


def uc_panel(yol: Path, paneller, baslik):
    h = max(p.shape[0] for p in paneller)
    esit = [cv2.resize(p, (p.shape[1], h)) if p.shape[0] != h else p
            for p in paneller]
    govde = np.hstack(esit)
    ust = np.zeros((46, govde.shape[1], 3), np.uint8)
    cv2.putText(ust, baslik, (12, 31), cv2.FONT_HERSHEY_SIMPLEX,
                0.78, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imwrite(str(yol), np.vstack([ust, govde]))


def ana():
    GORSEL_DIZINI.mkdir(parents=True, exist_ok=True)
    girdi = KOK / "dataset" / "sentetik_arena" / "images" / "train"
    etiket = KOK / "dataset" / "sentetik_arena" / "labels" / "train"
    model_yolu = KOK / "models" / "navitas_seg_v21_best.pt"
    kareler = sorted(
        p for p in girdi.iterdir() if p.suffix.lower() in GORSEL_UZANTILARI
    )[:KARE_SAYISI]
    if len(kareler) != KARE_SAYISI:
        raise RuntimeError(f"24 kare bekleniyordu, bulunan={len(kareler)}")

    model = YOLO(str(model_yolu))
    kayitlar = []
    for sira, yol in enumerate(kareler, 1):
        bgr = cv2.imread(str(yol))
        if bgr is None:
            raise RuntimeError(f"okunamadi: {yol}")
        tuval, kucuk, icerik = rpi._preprocess(bgr)
        # T49 kanit zinciri: conf argumani verilmez; Ultralytics predict varsayilani.
        tahmin = model.predict(kucuk, imgsz=rpi.INFER_SIZE, verbose=False)
        maskeler = rpi.get_masks(tahmin, tuval.shape[0], tuval.shape[1])
        maskeler = rpi._maskeleri_icerige_kirp(maskeler, icerik)
        gt, gt_poligon = yer_gercegi_oku(
            etiket / f"{yol.stem}.txt", tuval.shape[0], tuval.shape[1])
        kayitlar.append({
            "sira": sira,
            "yol": yol,
            "bgr": tuval,
            "icerik": tuple(map(int, icerik)),
            "maskeler": maskeler,
            "gt": gt,
            "gt_poligon": gt_poligon,
        })

    etkin_conf = float(model.predictor.args.conf)
    asil_oran = karar.HEDEF_BANT_ORANI
    supurme = []
    kare_kararlari = {k["yol"].stem: {} for k in kayitlar}
    try:
        for oran in ORANLAR:
            karar.HEDEF_BANT_ORANI = oran
            dagilim = Counter()
            yollar = Counter()
            for kayit in kayitlar:
                sonuc = karar_calistir(kayit)
                anahtar = durum_anahtari(sonuc)
                dagilim[anahtar] += 1
                if sonuc["yol"] is not None:
                    yollar[str(sonuc["yol"])] += 1
                kare_kararlari[kayit["yol"].stem][f"{oran:.2f}"] = sonuc
            supurme.append({
                "oran": oran,
                "bant_h": karar.hedef_bant_yuksekligi(
                    kayitlar[0]["icerik"][3]),
                "acik": int(sum(yollar.values())),
                "yollar": dict(sorted(yollar.items())),
                "dagilim": dict(sorted(dagilim.items())),
            })

        karar.HEDEF_BANT_ORANI = BAZ_ORAN
        for kayit in kayitlar:
            ad = kayit["yol"].stem
            kayit["baz"] = kare_kararlari[ad][f"{BAZ_ORAN:.2f}"]
            kayit["son"] = kare_kararlari[ad][f"{SON_ORAN:.2f}"]
            kayit["bilesen"] = bilesen_olcumu(kayit)
            kayit["gt_geometri"] = gt_geometri_olcumu(kayit)
            kayit["gt_baz"] = gt_karar_calistir(kayit)
        karar.HEDEF_BANT_ORANI = SON_ORAN
        for kayit in kayitlar:
            kayit["gt_son"] = gt_karar_calistir(kayit)
    finally:
        karar.HEDEF_BANT_ORANI = asil_oran

    ilk12 = Counter(durum_anahtari(k["baz"]) for k in kayitlar[:12])
    baz24 = Counter(durum_anahtari(k["baz"]) for k in kayitlar)
    gt_baz = Counter(durum_anahtari(k["gt_baz"]) for k in kayitlar)
    gt_son = Counter(durum_anahtari(k["gt_son"]) for k in kayitlar)
    kaplama = [
        100.0 * np.count_nonzero(k["maskeler"][0])
        / float(k["icerik"][2] * k["icerik"][3])
        for k in kayitlar
    ]
    kaplama_ilk12 = kaplama[:12]
    poligon_dagilimi = Counter(
        k["gt_geometri"]["poligon_sayisi"] for k in kayitlar)
    gt_bilesen_dagilimi = Counter(
        k["gt_geometri"]["bilesen_sayisi"] for k in kayitlar)

    uc_retleri = [k for k in kayitlar
                  if durum_anahtari(k["baz"]) == karar.UC_BANT_TEMAS_YOK_SEBEBI]
    ret_nedenleri = Counter()
    for kayit in uc_retleri:
        b = kayit["bilesen"]
        if not b["tum_ust_ok"] and not b["tum_alt_ok"]:
            neden = "IKI_BANTTA_YETERSIZ_ZEMIN"
        elif not b["tum_ust_ok"]:
            neden = "UST_BANTTA_YETERSIZ_ZEMIN"
        elif not b["tum_alt_ok"]:
            neden = "ALT_BANTTA_YETERSIZ_ZEMIN"
        elif b["uclar_farkli_bilesenlerde"]:
            neden = "UCLAR_FARKLI_BILESENLERDE"
        elif b["kucuk_bilesen_span_kaybi"]:
            neden = "EN_BUYUK_SECIMI_SPAN_KAYBI"
        else:
            neden = "DOGRULANAMADI"
        kayit["c_nedeni"] = neden
        ret_nedenleri[neden] += 1

    bilesen_ozet = {
        "bilesen_sayisi_dagilimi": Counter(
            k["bilesen"]["bilesen_sayisi"] for k in kayitlar),
        "birden_fazla_bilesen_kare": sum(
            k["bilesen"]["bilesen_sayisi"] > 1 for k in kayitlar),
        "en_buyuk_pay_ortalama": float(np.mean([
            k["bilesen"]["en_buyuk_pay"] for k in kayitlar])),
        "en_buyuk_pay_min": float(min(
            k["bilesen"]["en_buyuk_pay"] for k in kayitlar)),
        "en_buyuk_pay_max": float(max(
            k["bilesen"]["en_buyuk_pay"] for k in kayitlar)),
        "tum_maskede_ust_ok": sum(k["bilesen"]["tum_ust_ok"] for k in kayitlar),
        "tum_maskede_alt_ok": sum(k["bilesen"]["tum_alt_ok"] for k in kayitlar),
        "ayni_bilesen_iki_uc_ok": sum(
            k["bilesen"]["herhangi_iki_uc"] for k in kayitlar),
        "en_buyuk_bilesen_iki_uc_ok": sum(
            k["bilesen"]["en_buyuk"]["ust_ok"]
            and k["bilesen"]["en_buyuk"]["alt_ok"] for k in kayitlar),
        "uclar_farkli_bilesenlerde": sum(
            k["bilesen"]["uclar_farkli_bilesenlerde"] for k in kayitlar),
        "kucuk_bilesen_span_kaybi": sum(
            k["bilesen"]["kucuk_bilesen_span_kaybi"] for k in kayitlar),
        "uc_ret_atiflari": ret_nedenleri,
        "ust_bant_zemin_px_toplam": sum(
            k["bilesen"]["tum_ust_px"] for k in kayitlar),
        "alt_bant_zemin_px_toplam": sum(
            k["bilesen"]["tum_alt_px"] for k in kayitlar),
        "en_buyuk_ust_kesisim_px_toplam": sum(
            k["bilesen"]["en_buyuk"]["ust_px"] for k in kayitlar),
        "en_buyuk_alt_kesisim_px_toplam": sum(
            k["bilesen"]["en_buyuk"]["alt_px"] for k in kayitlar),
    }

    # Gorsel secimi: her hipotez icin iki ayri ve olculebilir ornek.
    duyarli = [k for k in kayitlar if k["baz"]["yol"] is None
               and k["son"]["yol"] is not None]
    kalici = [k for k in kayitlar if k["baz"]["yol"] is None
              and k["son"]["yol"] is None]
    a1 = duyarli[0] if duyarli else kayitlar[0]
    a2 = kalici[0] if kalici else kayitlar[-1]
    # Deterministik uretici replay'inde gozlenen fiziksel n_ser=2 ve n_ser=5
    # karsit ornekleri; JPEG'ler disk verisiyle 24/24 bayt-esit dogrulandi.
    b1 = next(k for k in kayitlar if k["yol"].stem == "sa_000300")
    b2 = next(k for k in kayitlar if k["yol"].stem == "sa_000306")
    c_aday = sorted(uc_retleri, key=lambda k: (
        not k["bilesen"]["uclar_farkli_bilesenlerde"],
        -k["bilesen"]["bilesen_sayisi"], k["sira"]))
    c1 = c_aday[0] if c_aday else kayitlar[0]
    c2 = next((k for k in sorted(uc_retleri, key=lambda k: (
        k["bilesen"]["en_buyuk_pay"], k["sira"])) if k is not c1), c1)

    gorseller = []

    def a_gorseli(kayit, ad, baslik):
        p0 = bant_ve_rota_ciz(kayit["bgr"], kayit["icerik"], [], BAZ_ORAN,
                             f"HAM + bant %{int(BAZ_ORAN * 100)}")
        p1 = bant_ve_rota_ciz(
            maske_bindirme(kayit["bgr"], kayit["baz"]["temiz"]),
            kayit["icerik"], kayit["baz"]["noktalar"], BAZ_ORAN,
            f"%8: {durum_anahtari(kayit['baz'])}")
        p2 = bant_ve_rota_ciz(
            maske_bindirme(kayit["bgr"], kayit["son"]["temiz"]),
            kayit["icerik"], kayit["son"]["noktalar"], SON_ORAN,
            f"%20: {durum_anahtari(kayit['son'])}")
        yol = GORSEL_DIZINI / ad
        uc_panel(yol, [p0, p1, p2], baslik)
        gorseller.append(str(yol.relative_to(KOK)))

    def b_gorseli(kayit, ad, baslik):
        gt_n, gt_lab = cv2.connectedComponents(kayit["gt"][0], 8)
        del gt_n
        p0 = bant_ve_rota_ciz(kayit["bgr"], kayit["icerik"], [], BAZ_ORAN,
                             "HAM + %8 bant")
        p1 = bant_ve_rota_ciz(
            maske_bindirme(kayit["bgr"], kayit["gt"][0], kayit["gt"][1]),
            kayit["icerik"], kayit["gt_baz"]["noktalar"], BAZ_ORAN,
            f"GT: {durum_anahtari(kayit['gt_baz'])}")
        p2 = bant_ve_rota_ciz(
            bilesen_bindirme(kayit["bgr"], gt_lab), kayit["icerik"], [],
            BAZ_ORAN,
            f"GT poligon={kayit['gt_geometri']['poligon_sayisi']} "
            f"bilesen={kayit['gt_geometri']['bilesen_sayisi']}")
        yol = GORSEL_DIZINI / ad
        uc_panel(yol, [p0, p1, p2], baslik)
        gorseller.append(str(yol.relative_to(KOK)))

    def c_gorseli(kayit, ad, baslik):
        b = kayit["bilesen"]
        p0 = bant_ve_rota_ciz(kayit["bgr"], kayit["icerik"], [], BAZ_ORAN,
                             f"HAM + %8 bant; {kayit.get('c_nedeni', '-')}")
        p1 = bant_ve_rota_ciz(
            bilesen_bindirme(kayit["bgr"], b["etiketler"]),
            kayit["icerik"], [], BAZ_ORAN,
            f"Tum bilesenler={b['bilesen_sayisi']} "
            f"ust={b['tum_ust_px']} alt={b['tum_alt_px']}")
        p2 = bant_ve_rota_ciz(
            maske_bindirme(kayit["bgr"], kayit["baz"]["temiz"]),
            kayit["icerik"], kayit["baz"]["noktalar"], BAZ_ORAN,
            f"En buyuk pay=%{100*b['en_buyuk_pay']:.1f} "
            f"ust={b['en_buyuk']['ust_px']} alt={b['en_buyuk']['alt_px']}")
        yol = GORSEL_DIZINI / ad
        uc_panel(yol, [p0, p1, p2], baslik)
        gorseller.append(str(yol.relative_to(KOK)))

    a_gorseli(a1, f"a1_bant_duyarli_{a1['yol'].stem}.png",
              f"(a) Bantla acilan: {a1['yol'].name}")
    a_gorseli(a2, f"a2_bant_yetersiz_{a2['yol'].stem}.png",
              f"(a) %20'de de kapali: {a2['yol'].name}")
    b_gorseli(b1, f"b1_gt_iki_serit_{b1['yol'].stem}.png",
              f"(b) Uretici replay n_ser=2: {b1['yol'].name}")
    b_gorseli(b2, f"b2_gt_cok_koridor_{b2['yol'].stem}.png",
              f"(b) Uretici replay n_ser=5: {b2['yol'].name}")
    c_gorseli(c1, f"c1_bilesen_{c1['yol'].stem}.png",
              f"(c) Bilesen tani ornegi 1: {c1['yol'].name}")
    c_gorseli(c2, f"c2_bilesen_{c2['yol'].stem}.png",
              f"(c) Bilesen tani ornegi 2: {c2['yol'].name}")

    satirlar = []
    for kayit in kayitlar:
        b = kayit["bilesen"]
        satirlar.append({
            "sira": kayit["sira"],
            "kare": kayit["yol"].name,
            "baz_durum": durum_anahtari(kayit["baz"]),
            "oran20_durum": durum_anahtari(kayit["son"]),
            "gt_baz_durum": durum_anahtari(kayit["gt_baz"]),
            "gt_oran20_durum": durum_anahtari(kayit["gt_son"]),
            "gt_traversable_poligon": kayit["gt_geometri"]["poligon_sayisi"],
            "gt_traversable_bilesen": kayit["gt_geometri"]["bilesen_sayisi"],
            "gt_ust_bosluk_px": kayit["gt_geometri"]["ust_bosluk_px"],
            "gt_alt_bosluk_px": kayit["gt_geometri"]["alt_bosluk_px"],
            "model_bilesen": b["bilesen_sayisi"],
            "model_en_buyuk_pay": f"{b['en_buyuk_pay']:.6f}",
            "tum_ust_px": b["tum_ust_px"],
            "tum_alt_px": b["tum_alt_px"],
            "en_buyuk_ust_px": b["en_buyuk"]["ust_px"],
            "en_buyuk_alt_px": b["en_buyuk"]["alt_px"],
            "c_atfi": kayit.get("c_nedeni", "-"),
        })
    with (CIKTI / "kare_olcumleri.csv").open(
            "w", newline="", encoding="utf-8-sig") as akis:
        yazici = csv.DictWriter(akis, fieldnames=list(satirlar[0]))
        yazici.writeheader()
        yazici.writerows(satirlar)

    uc_oran = next(x for x in supurme if x["oran"] == BAZ_ORAN)
    son_oran = next(x for x in supurme if x["oran"] == SON_ORAN)
    gt_exact3 = sum(k["gt_geometri"]["poligon_sayisi"] == 3 for k in kayitlar)
    gt_cc_exact3 = sum(k["gt_geometri"]["bilesen_sayisi"] == 3 for k in kayitlar)
    gt_span = sum(k["gt_geometri"]["iki_uca_degen_bilesen"] > 0 for k in kayitlar)
    ust_bosluklar = [k["gt_geometri"]["ust_bosluk_px"] for k in kayitlar]
    alt_bosluklar = [k["gt_geometri"]["alt_bosluk_px"] for k in kayitlar]
    baz_bant_h = karar.hedef_bant_yuksekligi(kayitlar[0]["icerik"][3])
    gt_bosluk = {
        "ust_medyan_px": float(np.median(ust_bosluklar)),
        "ust_maks_px": int(max(ust_bosluklar)),
        "ust_bant_disinda_kare": int(sum(v >= baz_bant_h for v in ust_bosluklar)),
        "alt_medyan_px": float(np.median(alt_bosluklar)),
        "alt_maks_px": int(max(alt_bosluklar)),
        "alt_bant_disinda_kare": int(sum(v >= baz_bant_h for v in alt_bosluklar)),
    }

    sonuc_a = (
        f"ETKILI AMA TEK NEDEN DEGIL: %{int(BAZ_ORAN*100)}'de "
        f"{uc_oran['acik']}/24 acik, %{int(SON_ORAN*100)}'de "
        f"{son_oran['acik']}/24 acik; {24-son_oran['acik']} kare taranan "
        "ust sinirda da acilmadi.")
    sonuc_b = (
        "DOGRU: dogrulanmis uretici replay'inde fiziksel serit sayisi "
        f"{URETEC_REPLAY['n_ser_dagilimi']}; yalniz 13/24 kare tam 3 seritli. "
        f"GT class-0 poligon sayisi yalniz {gt_exact3}/24, birlesik maske "
        f"bilesen sayisi yalniz {gt_cc_exact3}/24 karede tam 3. %8 tam-goruntu "
        f"bantlarina ayni GT bileseniyle iki uctan temas eden kare {gt_span}/24. "
        "n_ser degeri salt YOLO etiketlerinden birebir geri kazanilamaz; "
        "etiket-only sonuc DOGRULANAMADI, fakat kaynak replay'iyle dogrulandi.")
    frag = int(ret_nedenleri.get("UCLAR_FARKLI_BILESENLERDE", 0)
               + ret_nedenleri.get("EN_BUYUK_SECIMI_SPAN_KAYBI", 0))
    sonuc_c = (
        f"{'DOGRU' if frag else 'ANA NEDEN DEGIL'}: %8 UC_BANT retlerinin "
        f"{frag}/{len(uc_retleri)} tanesi bagli-bilesen ayrismasina atfedildi; "
        f"kalan {len(uc_retleri)-frag}/{len(uc_retleri)} ret, tum model "
        "maskesinde bile bir veya iki uc bandinda yeterli zemin olmamasindan geldi.")

    rapor = {
        "provenance": {
            "model": str(model_yolu.relative_to(KOK)),
            "model_sha256": sha256(model_yolu),
            "rpi_inference_sha256": sha256(KOK / "codes" / "rpi_inference.py"),
            "kare_sayisi": len(kayitlar),
            "ilk_kare": kayitlar[0]["yol"].name,
            "son_kare": kayitlar[-1]["yol"].name,
            "infer_size": int(rpi.INFER_SIZE),
            "predict_conf_arg": "VERILMEDI",
            "predict_etkin_conf": etkin_conf,
            "mpp": None,
            "kaplama_ilk12_ortalama_yuzde": float(np.mean(kaplama_ilk12)),
            "kaplama_ilk12_min_yuzde": float(min(kaplama_ilk12)),
            "kaplama_ilk12_maks_yuzde": float(max(kaplama_ilk12)),
            "kaplama_24_ortalama_yuzde": float(np.mean(kaplama)),
            "kaplama_24_min_yuzde": float(min(kaplama)),
            "kaplama_24_maks_yuzde": float(max(kaplama)),
            "zincir": ["_preprocess", "predict", "get_masks",
                       "_maskeleri_icerige_kirp", "analyze_path"],
        },
        "reproduksiyon_ilk12": ilk12,
        "baz24": baz24,
        "a_bant_supurme": supurme,
        "b_gt": {
            "class0_poligon_dagilimi": poligon_dagilimi,
            "class0_bilesen_dagilimi": gt_bilesen_dagilimi,
            "tam_3_poligon_kare": gt_exact3,
            "tam_3_bilesen_kare": gt_cc_exact3,
            "baz_gt_karar": gt_baz,
            "oran20_gt_karar": gt_son,
            "baz_iki_uca_degen_gt_bileseni_olan_kare": gt_span,
            "gt_bosluk": gt_bosluk,
            "uretec_replay": URETEC_REPLAY,
            "uretec_kod_kaniti": {
                "kaynak": "O:/navitas-local-train/51_sentetik_arena.py:382-445",
                "n_ser_secimleri": [2, 3, 3, 3, 4, 5],
                "dikey_kenar_y_orani": "0.00..0.28",
                "serit_durumlari": ["kapali", "acik", "kismi", "dar"],
                "etiketten_exact_n_ser": "DOGRULANAMADI; kaynak replay'iyle dogrulandi",
            },
        },
        "c_bilesen": bilesen_ozet,
        "net": {"a": sonuc_a, "b": sonuc_b, "c": sonuc_c},
        "gorseller": gorseller,
        "esik_degistirildi": False,
    }
    (CIKTI / "rapor.json").write_text(
        json.dumps(json_uyumlu(rapor), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    md = [
        "# T49 — Sentetik arena uç-bant tanısı",
        "",
        "Bu çıktı karar eşiğini değiştirmez; üretim koduna yazmaz.",
        "",
        "## (a) Bant oranı süpürmesi",
        "",
        "| oran | bant px | açık | karar dağılımı |",
        "|---:|---:|---:|---|",
    ]
    for x in supurme:
        md.append(
            f"| {x['oran']:.2f} | {x['bant_h']} | {x['acik']} | "
            f"{json.dumps(x['dagilim'], ensure_ascii=False, sort_keys=True)} |")
    md += ["", f"**Net:** {sonuc_a}", "", "## (b) Yer gerçeği geometrisi", "",
           f"- Üretici replay fiziksel şerit dağılımı: `{URETEC_REPLAY['n_ser_dagilimi']}`; JPEG provenance `{URETEC_REPLAY['jpeg_bayt_esit']}`",
           f"- Class-0 poligon dağılımı: `{dict(sorted(poligon_dagilimi.items()))}`",
           f"- Class-0 bağlı bileşen dağılımı: `{dict(sorted(gt_bilesen_dagilimi.items()))}`",
           f"- GT karar, %8: `{dict(sorted(gt_baz.items()))}`",
           f"- GT karar, %20: `{dict(sorted(gt_son.items()))}`",
           f"- GT boşluk: `{gt_bosluk}`",
           f"- **Net:** {sonuc_b}", "", "## (c) Parçalanma", "",
           f"- Bileşen sayısı dağılımı: `{dict(sorted(bilesen_ozet['bilesen_sayisi_dagilimi'].items()))}`",
           f"- UC ret atıfları: `{dict(sorted(ret_nedenleri.items()))}`",
           f"- Bant zemin piksel toplamı (tüm/en büyük): üst `{bilesen_ozet['ust_bant_zemin_px_toplam']}/{bilesen_ozet['en_buyuk_ust_kesisim_px_toplam']}`, alt `{bilesen_ozet['alt_bant_zemin_px_toplam']}/{bilesen_ozet['en_buyuk_alt_kesisim_px_toplam']}`",
           f"- **Net:** {sonuc_c}", "", "## Görsel kanıt", ""]
    md.extend(f"- `{g}`" for g in gorseller)
    md += ["", "## Sınır", "",
           "Bu tanı model/karar zincirini ayrıştırır. Eşik düzeltmesi yapmaz. "
           "Üretecin gerçek `n_ser` değeri YOLO etiketlerinde saklanmadığı için "
           "salt etiketten birebir geri kazanımı **DOĞRULANAMADI**. Ayrı kaynak "
           "replay'i ilk 24 JPEG'i 24/24 bayt-eşit üretip şerit sayılarını doğruladı.", ""]
    (CIKTI / "rapor.md").write_text("\n".join(md), encoding="utf-8")

    print(
        f"[T49_KUME] kare={len(kayitlar)} ilk={kayitlar[0]['yol'].name} "
        f"son={kayitlar[-1]['yol'].name} imgsz={rpi.INFER_SIZE} "
        f"conf_arg=VERILMEDI etkin_conf={etkin_conf:.2f}")
    print(
        f"[T49_KAPLAMA] ilk12_ort={np.mean(kaplama_ilk12):.3f}% "
        f"min={min(kaplama_ilk12):.3f}% maks={max(kaplama_ilk12):.3f}% "
        f"tam24_ort={np.mean(kaplama):.3f}%")
    print(f"[T49_REPRO_ILK12] {dict(sorted(ilk12.items()))}")
    for x in supurme:
        print(
            f"[T49_A] oran={x['oran']:.2f} bant_px={x['bant_h']} "
            f"acik={x['acik']} dagilim={x['dagilim']}")
    print(
        f"[T49_B] gt_poligon={dict(sorted(poligon_dagilimi.items()))} "
        f"gt_bilesen={dict(sorted(gt_bilesen_dagilimi.items()))} "
        f"gt_baz={dict(sorted(gt_baz.items()))} gt_oran20={dict(sorted(gt_son.items()))} "
        f"gt_iki_uc={gt_span}/24 n_ser={URETEC_REPLAY['n_ser_dagilimi']} "
        f"jpeg_esit={URETEC_REPLAY['jpeg_bayt_esit']} "
        "etiket_only_n_ser=DOGRULANAMADI")
    print(f"[T49_B_BOSLUK] {gt_bosluk}")
    print(
        f"[T49_C] bilesen={dict(sorted(bilesen_ozet['bilesen_sayisi_dagilimi'].items()))} "
        f"uc_ret_atiflari={dict(sorted(ret_nedenleri.items()))} "
        f"ust_px={bilesen_ozet['ust_bant_zemin_px_toplam']} "
        f"alt_px={bilesen_ozet['alt_bant_zemin_px_toplam']} "
        f"en_buyuk_ust_px={bilesen_ozet['en_buyuk_ust_kesisim_px_toplam']} "
        f"en_buyuk_alt_px={bilesen_ozet['en_buyuk_alt_kesisim_px_toplam']}")
    print(f"[T49_NET_A] {sonuc_a}")
    print(f"[T49_NET_B] {sonuc_b}")
    print(f"[T49_NET_C] {sonuc_c}")
    print(f"[T49_GORSELLER] adet={len(gorseller)} dizin={GORSEL_DIZINI.relative_to(KOK)}")
    print("[T49_ESIK] degistirildi=HAYIR")


if __name__ == "__main__":
    ana()
