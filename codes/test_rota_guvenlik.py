"""NEDEN: Ekibin kendi cikti gorselleri
(WhatsApp Image 2026-08-02 at 14.53.52*.jpeg)
rotanin park halindeki arabalarin USTUNDEN gectigini gosteriyor. test_rota_sentetik.py
bunu OLCEMEZ (sentetik arenada arac yok). Bu betik gercek otopark drone goruntulerinde
"rota hicbir arabaya deginiyor mu" sorusunu OLCULEBILIR hale getirir.

ENGELDEN KACINMA DOGRULAMASI — gercek goruntu, bagimsiz arac kahini.

YONTEM — IKI KIP, teshis degeri buradan gelir:
  (a) HAM      : planlayiciya SADECE navitas modelinin {0,1} maskeleri verilir.
                 Bu, BUGUNKU sistemin arabalarin ustunden gecip gecmedigini olcer.
  (b) ENJEKTE  : navitas {0,1} + arac kahini maskeleri EK ENGEL sinifi olarak
                  planlayiciya verilir.
  Arac maskesi HER IKI kipte de SONRADAN, SADECE PUANLAMAK icin hesaplanir.
  (a)'da planlayiciya ASLA verilmez — verilseydi test DONGUSEL olurdu ve hicbir
  sey kanitlamazdi.

  (a) ihlal ederken (b) temizse -> kusur ALGIDA (navitas modeli arac gormuyor,
      egitim/veri gerekir — tam olarak sartname Faz 4.1'deki 3-sinifli gecis).
  (b) de ihlal ediyorsa -> kusur GEOMETRIDE (costmap_path_finder hatali).

OTOPARKTA 3 AYRI KORIDOR YOK — costmap_path_finder.rota_bul()'un kapi mantigi
(koridor_adaylari) burada UYGUN DEGIL (n_kapi=3 beklentisi acik alanda tutmaz).
Bu yuzden dusuk seviyeli ilkeller (serbest_alan, astar, yol_duzelt, rota_dogrula)
DOGRUDAN kullanilir: baslangic=alt %8 serit, hedef=ust %8 serit (rota_bul'un
kendi varsayilan tohum kurali ile ayni) — "sahne icinden gec" testi.

OLCEK (mpp) BILINMIYOR — bu klipler icin irtifa/FOV kayitli degil. DOTA OBB
araclarinin tekil kisa eksen maskelerinden turetilir (binek arac ~1.8 m genislik).
Uretim hatti ile ayni ``yolov8m-obb.pt`` varsayilandir. Eski COCO-seg modeli ve
``--coco-model`` bayragi geriye uyumluluk icin desteklenir; hava goruntusu kapisi
DOTA small/large vehicle siniflariyla kosulur.

Kullanim:
  venv/Scripts/python.exe codes/test_rota_guvenlik.py --girdi "WhatsApp Image 2026-07-30 at 11.44.48.jpeg"
  venv/Scripts/python.exe codes/test_rota_guvenlik.py --girdi "WhatsApp Video 2026-07-30 at 11.44.03.mp4" --adim 24
  venv/Scripts/python.exe codes/test_rota_guvenlik.py --hepsi     # tum 4 video + 6 foto
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))

from costmap_path_finder import (
    serbest_alan, plan_izgarasi, astar, yol_duzelt, rota_dogrula,
    mpp_arac_maskesinden, olcek_px, DOYUM_CARPANI_M,
)
from rpi_inference import get_masks

REPO = Path(__file__).parent.parent
ARAC_SINIF_ADLARI = frozenset({
    "car", "motorcycle", "bus", "truck",
    "small vehicle", "large vehicle",
})
VARSAYILAN_ARAC_MODEL = REPO / "yolov8m-obb.pt"
VARSAYILAN_GORSELLER = [
    "WhatsApp Image 2026-07-30 at 11.44.48.jpeg",
    "WhatsApp Image 2026-07-30 at 11.44.50.jpeg",
    "WhatsApp Image 2026-07-30 at 11.44.50 (1).jpeg",
    "WhatsApp Image 2026-07-30 at 11.44.50 (2).jpeg",
    "WhatsApp Image 2026-07-30 at 11.44.51.jpeg",
    "WhatsApp Image 2026-07-30 at 11.44.51 (1).jpeg",
]
VARSAYILAN_VIDEOLAR = [
    "WhatsApp Video 2026-07-30 at 11.44.03.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.23.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.39.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.46.mp4",
]


def _letterbox_kare(img, boyut=896):
    """simulation/scripts/iha_perceive._letterbox_square ile ayni fikir:
    CROP degil PAD — kenarlar korunur. (icerik_x0,icerik_y0,icerik_w,icerik_h) da doner."""
    h, w = img.shape[:2]
    olcek = boyut / max(h, w)
    nh, nw = int(round(h * olcek)), int(round(w * olcek))
    kucuk = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
    tuval = np.full((boyut, boyut, 3), 114, np.uint8)
    x0, y0 = (boyut - nw) // 2, (boyut - nh) // 2
    tuval[y0:y0 + nh, x0:x0 + nw] = kucuk
    return tuval, (x0, y0, nw, nh)


def _tensor_numpy(veri):
    """Torch-benzeri model ciktisini NumPy dizisine indir (test doubles dahil)."""
    if hasattr(veri, "detach"):
        veri = veri.detach()
    if hasattr(veri, "cpu"):
        veri = veri.cpu()
    if hasattr(veri, "numpy"):
        veri = veri.numpy()
    return np.asarray(veri)


def _sinif_adi(adlar, sinif_id):
    """Ultralytics ``names`` dict/list bicimlerini tek metne cevir."""
    if isinstance(adlar, dict):
        return str(adlar.get(int(sinif_id), sinif_id)).lower()
    try:
        return str(adlar[int(sinif_id)]).lower()
    except (IndexError, KeyError, TypeError):
        return str(sinif_id)


def _arac_ornek_maskeleri(sonuclar, adlar, h, w):
    """OBB veya segmentasyon sonucundan TEKIL arac maskeleri cikar.

    DOTA OBB poligonlari hava goruntusundeki small/large vehicle siniflarini
    yakalar. Segmentasyon dali eski COCO modelini yalniz geriye uyumluluk icin
    destekler. Maskeler birlestirilmeden tutulur; mpp tek bir dev sinif-birlesim
    kutusundan degil, tekil araclarin kisa eksenlerinden hesaplanir.
    """
    maskeler = []
    for kare in sonuclar:
        obb = getattr(kare, "obb", None)
        if (obb is not None and getattr(obb, "cls", None) is not None
                and getattr(obb, "xyxyxyxy", None) is not None):
            siniflar = _tensor_numpy(obb.cls).astype(int)
            poligonlar = _tensor_numpy(obb.xyxyxyxy)
            for sinif_id, poligon in zip(siniflar, poligonlar):
                if _sinif_adi(adlar, sinif_id) not in ARAC_SINIF_ADLARI:
                    continue
                maske = np.zeros((h, w), np.uint8)
                pts = np.rint(poligon).astype(np.int32).reshape(-1, 1, 2)
                cv2.fillPoly(maske, [pts], 1, lineType=cv2.LINE_8)
                if maske.any():
                    maskeler.append(maske)
            continue

        ornekler = getattr(kare, "masks", None)
        kutular = getattr(kare, "boxes", None)
        if (ornekler is None or getattr(ornekler, "data", None) is None
                or kutular is None or getattr(kutular, "cls", None) is None):
            continue
        siniflar = _tensor_numpy(kutular.cls).astype(int)
        ham_maskeler = _tensor_numpy(ornekler.data)
        for sinif_id, ham_maske in zip(siniflar, ham_maskeler):
            if _sinif_adi(adlar, sinif_id) not in ARAC_SINIF_ADLARI:
                continue
            maske = (cv2.resize(ham_maske.astype(np.float32), (w, h),
                                interpolation=cv2.INTER_LINEAR) > 0.5).astype(np.uint8)
            if maske.any():
                maskeler.append(maske)
    return maskeler


def _merkez_tohumu(gecilebilir, taraf, yaricap_px, *, icerik):
    """Goruntunun merkezine en yakin gecerli giris/cikis tohumunu sec.

    Tum alt/ust bandi cok-kaynak yapmak A*'in gercek IKA-hedef hattindan
    kopup kenardan kacmasina izin verir. Gercek KB/H koordinati bu test
    girdilerinde olmadigi icin, merkez-yakin tek bir temsilci tohum kullanilir.
    Bantlar kare letterbox tuvalinden degil, gercek goruntunun ``icerik``
    dikdortgeninden turetilir; dolgu pikselleri asla tohum adayi olamaz.
    """
    h, w = gecilebilir.shape
    tohum = np.zeros((h, w), np.uint8)
    x0, y0, icerik_w, icerik_h = (int(v) for v in icerik)
    x0 = max(0, min(w, x0))
    y0 = max(0, min(h, y0))
    x1 = max(x0, min(w, x0 + max(0, icerik_w)))
    icerik_y1 = max(y0, min(h, y0 + max(0, icerik_h)))
    if x1 <= x0 or icerik_y1 <= y0:
        return tohum

    pay = max(1, int((icerik_y1 - y0) * 0.08))
    bant_y0, bant_y1 = (
        (icerik_y1 - pay, icerik_y1) if taraf == "alt"
        else (y0, min(icerik_y1, y0 + pay))
    )
    ys, xs = np.nonzero(gecilebilir[bant_y0:bant_y1, x0:x1])
    if xs.size == 0:
        return tohum
    ys = ys + bant_y0
    xs = xs + x0
    merkez_x = (x0 + x1 - 1) / 2.0
    kenar_y = icerik_y1 - 1 if taraf == "alt" else y0
    # X merkezi asil onceliktir; ayni koridorda dis sinira yakin nokta secilir.
    skor = 1000.0 * np.abs(xs - merkez_x) + np.abs(ys - kenar_y)
    i = int(np.argmin(skor))
    cv2.circle(tohum, (int(xs[i]), int(ys[i])), max(1, int(yaricap_px)), 1, -1)
    # Disk, bant/content sinirinda dolguya tasarsa yalniz gercek gecilebilir
    # pikselleri koru.
    icerik_maskesi = np.zeros_like(tohum)
    icerik_maskesi[y0:icerik_y1, x0:x1] = 1
    tohum &= (gecilebilir > 0).astype(np.uint8)
    tohum &= icerik_maskesi
    return tohum


def _rota_uret(maskeler, mpp, *, icerik):
    """serbest_alan + astar + yol_duzelt + rota_dogrula — DUSUK SEVIYE,
    3-koridor kapi mantigi (rota_bul/koridor_adaylari) BURADA KULLANILMAZ
    (acik otoparkta 3 ayrik koridor varsayimi tutmuyor)."""
    sonuc = serbest_alan(maskeler, mpp=mpp)
    olc = sonuc["olcek"]
    h, w = sonuc["sekil"]

    ds = max(1, int(round(olc["plan_m_hucre"] / olc["mpp"])))
    gecilebilir_tam = sonuc["dt_px"] >= olc["r_gerekli_px"]
    tohum_a = _merkez_tohumu(gecilebilir_tam, "alt", ds, icerik=icerik)
    tohum_b = _merkez_tohumu(gecilebilir_tam, "ust", ds, icerik=icerik)
    eksik_tohumlar = []
    if not tohum_a.any():
        eksik_tohumlar.append("alt")
    if not tohum_b.any():
        eksik_tohumlar.append("ust")
    if eksik_tohumlar:
        return {
            "durum": "TOHUM_YOK",
            "tohum_yok_taraflar": eksik_tohumlar,
            "waypoints_px": [],
            "sonuc": sonuc,
        }
    dt_plan, _ = plan_izgarasi(sonuc["dt_px"], None, ds)
    if dt_plan.size == 0:
        return {"durum": "MASKE_YOK", "waypoints_px": [], "sonuc": sonuc}

    gecilebilir_plan = dt_plan >= olc["r_gerekli_px"]
    aciklik_m = np.minimum(dt_plan * olc["mpp"], DOYUM_CARPANI_M)
    h2, w2 = gecilebilir_plan.shape
    ta = cv2.resize(tohum_a.astype(np.float32), (w2, h2), interpolation=cv2.INTER_AREA) > 0
    tb = cv2.resize(tohum_b.astype(np.float32), (w2, h2), interpolation=cv2.INTER_AREA) > 0
    # Yeniden ornekleme tohumu engelli bir plan hucresine yayabilir veya tamamen
    # silebilir. Bu da tohum eksikligidir; A*'in genel KAPALI sonucuna yutulmasin.
    ta &= gecilebilir_plan
    tb &= gecilebilir_plan
    eksik_plan_tohumlari = []
    if not ta.any():
        eksik_plan_tohumlari.append("alt")
    if not tb.any():
        eksik_plan_tohumlari.append("ust")
    if eksik_plan_tohumlari:
        return {
            "durum": "TOHUM_YOK",
            "tohum_yok_taraflar": eksik_plan_tohumlari,
            "waypoints_px": [],
            "sonuc": sonuc,
        }

    yol_izgara = astar(gecilebilir_plan, aciklik_m, tb, ta,
                       adim_m=ds * olc["mpp"], r_gerekli_m=olc["r_gerekli_m"])
    if yol_izgara is None:
        return {"durum": "KAPALI", "waypoints_px": [], "sonuc": sonuc}

    yol_px = [(int((c + 0.5) * ds), int((r + 0.5) * ds)) for r, c in yol_izgara]
    waypoints = yol_duzelt(yol_px, gecilebilir_tam, wp_aralik_px=olc["wp_aralik_px"])
    ok, ihlaller = rota_dogrula(waypoints, sonuc["engel_ham"], sonuc["dt_px"],
                                olc["r_gerekli_px"], katı=False)
    return {"durum": "ACIK" if ok else "DOGRULAMA_BASARISIZ", "waypoints_px": waypoints,
           "sonuc": sonuc, "olcek": olc}


def _min_aciklik_araca_px(waypoints_px, arac_maskesi_dt):
    if not waypoints_px or arac_maskesi_dt is None:
        return None
    h, w = arac_maskesi_dt.shape
    rota = np.zeros((h, w), np.uint8)
    pts = np.asarray(waypoints_px, np.int32).reshape(-1, 1, 2)
    if len(pts) == 1:
        cv2.circle(rota, tuple(pts[0, 0]), 0, 1, -1)
    else:
        cv2.polylines(rota, [pts], False, 1, thickness=1)
    return float(arac_maskesi_dt[rota > 0].min()) if rota.any() else None


def bir_kare_isle(bgr, navitas_model, arac_model, *, imgsz=896, conf=0.25,
                  arac_conf=0.25, cikti_dir=None, ad="kare"):
    """Tek karede (a) ham ve (b) enjekte kiplerini kosar, ihlal olcer.
    Donen: dict — bkz. modul basi metrikler."""
    tuval, icerik = _letterbox_kare(bgr, boyut=imgsz)

    r_nav = navitas_model.predict(tuval, imgsz=imgsz, conf=conf, verbose=False)
    maskeler_nav = get_masks(r_nav, imgsz, imgsz, sinif_idler=(0, 1))

    r_arac = arac_model.predict(tuval, imgsz=imgsz, conf=arac_conf, verbose=False)
    arac_ornekleri = _arac_ornek_maskeleri(
        r_arac, getattr(arac_model, "names", {}), imgsz, imgsz)
    arac_maskesi = np.zeros((imgsz, imgsz), np.uint8)
    for maske in arac_ornekleri:
        arac_maskesi = np.maximum(arac_maskesi, maske)

    mpp = mpp_arac_maskesinden(arac_ornekleri)
    if mpp is None:
        # olcek_px(None), sentetik testler icin metre sabitlerini sayisal olarak
        # piksel kabul eder. Gercek-goruntu guvenlik olcumunde bu 1.10 px'lik
        # sahte bir esik olur; plan ve ihlal karari uretilmez.
        sonuc_ham = {"durum": "OLCEK_YOK", "waypoints_px": []}
        sonuc_enj = {"durum": "OLCEK_YOK", "waypoints_px": []}
        arac_dt = None
        olc = None
    else:
        arac_dt = cv2.distanceTransform(
            1 - arac_maskesi, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        olc = olcek_px(mpp)
        sonuc_ham = _rota_uret(
            {0: maskeler_nav[0], 1: maskeler_nav[1]}, mpp, icerik=icerik)
        sonuc_enj = _rota_uret(
            {0: maskeler_nav[0], 1: np.maximum(maskeler_nav[1], arac_maskesi)},
            mpp,
            icerik=icerik,
        )

    def olc_ihlal(sonuc_r):
        if mpp is None:
            return {
                "karar_var": False,
                "ihlal": None,
                "min_aciklik_px": None,
                "durum": "OLCEK_YOK",
                "tohum_yok_taraflar": [],
                "olculebilir": False,
                "olcum_disi_neden": "MPP_YOK",
            }
        wp = sonuc_r["waypoints_px"]
        if not wp:
            return {
                "karar_var": False,
                "ihlal": False,
                "min_aciklik_px": None,
                "durum": sonuc_r["durum"],
                "tohum_yok_taraflar": sonuc_r.get("tohum_yok_taraflar", []),
                "olculebilir": True,
                "olcum_disi_neden": None,
            }
        min_ac = _min_aciklik_araca_px(wp, arac_dt)
        return {"karar_var": True,
               "ihlal": bool(min_ac is not None and min_ac < olc["r_gerekli_px"]),
               "min_aciklik_px": min_ac,
               "durum": sonuc_r["durum"],
               "tohum_yok_taraflar": [],
               "olculebilir": True,
               "olcum_disi_neden": None}

    m_ham = olc_ihlal(sonuc_ham)
    m_enj = olc_ihlal(sonuc_enj)

    if cikti_dir is not None:
        vis = tuval.copy()
        katman = np.zeros_like(vis)
        katman[arac_maskesi > 0] = (255, 0, 255)
        katman[maskeler_nav[1] > 0] = (0, 0, 220)
        var_maske = (arac_maskesi > 0) | (maskeler_nav[1] > 0)
        if var_maske.any():
            harman = cv2.addWeighted(vis, 0.6, katman, 0.4, 0)
            vis[var_maske] = harman[var_maske]
        for sonuc_r, renk in ((sonuc_ham, (0, 165, 255)), (sonuc_enj, (0, 255, 255))):
            wp = sonuc_r["waypoints_px"]
            for i in range(len(wp) - 1):
                cv2.line(vis, wp[i], wp[i + 1], renk, 2)
        cv2.putText(vis, f"ham:ihlal={m_ham['ihlal']} enj:ihlal={m_enj['ihlal']}",
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.imwrite(str(Path(cikti_dir) / f"{ad}.jpg"), vis)

    return {
        "ham": m_ham,
        "enj": m_enj,
        "mpp": mpp,
        "r_gerekli_px": None if olc is None else olc["r_gerekli_px"],
        "arac_sayisi": len(arac_ornekleri),
    }


def _ozet_hesapla(tum_sonuclar):
    """Yalniz fiziksel olcegi bilinen karelerden guvenlik oranlari uret."""
    n = len(tum_sonuclar)
    if n == 0:
        raise ValueError("Ozet icin en az bir kare gerekli")
    olcekli = [s for s in tum_sonuclar if s.get("mpp") is not None]
    n_olcekli = len(olcekli)
    n_olceksiz = n - n_olcekli
    ham_ihlal = sum(1 for s in olcekli if s["ham"]["ihlal"] is True)
    enj_ihlal = sum(1 for s in olcekli if s["enj"]["ihlal"] is True)
    ham_karar = sum(1 for s in olcekli if s["ham"]["karar_var"])
    enj_karar = sum(1 for s in olcekli if s["enj"]["karar_var"])
    ham_tohum_yok = sum(1 for s in olcekli
                        if s["ham"].get("durum") == "TOHUM_YOK")
    enj_tohum_yok = sum(1 for s in olcekli
                        if s["enj"].get("durum") == "TOHUM_YOK")
    oran_ham = round(ham_ihlal / n_olcekli, 3) if n_olcekli else None
    oran_enj = round(enj_ihlal / n_olcekli, 3) if n_olcekli else None
    cekimserlik_ham = round(1 - ham_karar / n_olcekli, 3) if n_olcekli else None
    cekimserlik_enj = round(1 - enj_karar / n_olcekli, 3) if n_olcekli else None
    return {
        "n_kare": n,
        "olcekli_kare": n_olcekli,
        "olceksiz_kare": n_olceksiz,
        "olcek_kapsama_orani": round(n_olcekli / n, 3),
        "olcum_durumu": (
            "OLCUM_YOK" if n_olcekli == 0
            else "KISMI_OLCUM" if n_olceksiz else "TAM_OLCUM"
        ),
        "ihlal_sayisi_ham": ham_ihlal,
        "ihlal_sayisi_enjekte": enj_ihlal,
        "karar_sayisi_ham": ham_karar,
        "karar_sayisi_enjekte": enj_karar,
        "tohum_yok_ham": ham_tohum_yok,
        "tohum_yok_enjekte": enj_tohum_yok,
        "ihlal_orani_ham": oran_ham,
        "ihlal_orani_enjekte": oran_enj,
        "cekimserlik_ham": cekimserlik_ham,
        "cekimserlik_enjekte": cekimserlik_enj,
    }


def _ozet_cikis_kodu(ozet):
    """Yalniz tam olcek kapsamasinda guclu ham olcumu basarili say."""
    ham_oran = ozet["ihlal_orani_ham"]
    return 0 if (ozet["olcum_durumu"] == "TAM_OLCUM"
                 and ham_oran is not None and ham_oran > 0.10) else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--girdi", help="tek video/gorsel dosyasi")
    ap.add_argument("--hepsi", action="store_true", help="tum varsayilan video+foto kumesi")
    ap.add_argument("--adim", type=int, default=24, help="videoda kac karede bir islensin")
    ap.add_argument("--navitas-model", default=str(REPO / "models" / "navitas_seg_v20_best.pt"))
    ap.add_argument("--arac-model", "--coco-model", dest="arac_model",
                    default=str(VARSAYILAN_ARAC_MODEL),
                    help="DOTA OBB arac kahini; --coco-model eski uyumluluk adidir")
    ap.add_argument("--arac-conf", type=float, default=0.25)
    ap.add_argument("--imgsz", type=int, default=896)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    navitas_model = YOLO(args.navitas_model)
    arac_model = YOLO(args.arac_model)

    cikti_dir = Path(args.out) if args.out else (
        REPO / "results" / f"rota_guvenlik_{time.strftime('%Y%m%d')}")
    cikti_dir.mkdir(parents=True, exist_ok=True)

    kaynaklar = []
    if args.girdi:
        kaynaklar = [Path(args.girdi)]
    elif args.hepsi:
        kaynaklar = [REPO / g for g in VARSAYILAN_GORSELLER] + \
                    [REPO / v for v in VARSAYILAN_VIDEOLAR]
    else:
        raise SystemExit("--girdi veya --hepsi verilmeli")

    tum_sonuclar = []
    for kaynak in kaynaklar:
        if not kaynak.exists():
            print(f"UYARI: bulunamadi, atlaniyor: {kaynak}")
            continue
        print(f"\n=== {kaynak.name} ===")
        if kaynak.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv"):
            cap = cv2.VideoCapture(str(kaynak))
            i = 0
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                if i % args.adim == 0:
                    sonuc = bir_kare_isle(frame, navitas_model, arac_model,
                                         imgsz=args.imgsz, conf=args.conf,
                                         arac_conf=args.arac_conf,
                                         cikti_dir=cikti_dir, ad=f"{kaynak.stem}_{i:05d}")
                    sonuc["kaynak"] = kaynak.name
                    sonuc["kare"] = i
                    tum_sonuclar.append(sonuc)
                    print(f"  kare {i:5}  ham:{sonuc['ham']['durum']:<10} "
                         f"ihlal={sonuc['ham']['ihlal']!s:5} "
                         f"enj:{sonuc['enj']['durum']:<10} "
                         f"ihlal={sonuc['enj']['ihlal']!s:5}  mpp={sonuc['mpp']}")
                i += 1
            cap.release()
        else:
            bgr = cv2.imread(str(kaynak))
            if bgr is None:
                print(f"  okunamadi: {kaynak}")
                continue
            sonuc = bir_kare_isle(bgr, navitas_model, arac_model, imgsz=args.imgsz,
                                 conf=args.conf, arac_conf=args.arac_conf,
                                 cikti_dir=cikti_dir, ad=kaynak.stem)
            sonuc["kaynak"] = kaynak.name
            sonuc["kare"] = 0
            tum_sonuclar.append(sonuc)
            esik = ("YOK" if sonuc["r_gerekli_px"] is None
                    else f"{sonuc['r_gerekli_px']:.1f}")
            print(f"  ham:{sonuc['ham']['durum']} ihlal={sonuc['ham']['ihlal']}  "
                  f"enj:{sonuc['enj']['durum']} ihlal={sonuc['enj']['ihlal']}  "
                  f"mpp={sonuc['mpp']}  r_gerekli_px={esik}")

    n = len(tum_sonuclar)
    if n == 0:
        print("\nHICBIR kare islenemedi.")
        return 1

    ozet = _ozet_hesapla(tum_sonuclar)
    ham_ihlal = ozet["ihlal_sayisi_ham"]
    enj_ihlal = ozet["ihlal_sayisi_enjekte"]
    n_olcekli = ozet["olcekli_kare"]
    n_olceksiz = ozet["olceksiz_kare"]
    ham_oran = ozet["ihlal_orani_ham"]
    enj_oran = ozet["ihlal_orani_enjekte"]

    print("\n" + "=" * 70)
    print("OZET")
    print("=" * 70)
    print(f"islenen kare          : {n}")
    print(f"olcekli / olceksiz    : {n_olcekli} / {n_olceksiz}  "
          f"({ozet['olcum_durumu']})")
    if n_olcekli == 0:
        print("ihlal orani (ham)     : OLCUM_YOK (0 olcekli kare)")
        print("ihlal orani (enjekte) : OLCUM_YOK (0 olcekli kare)")
        print("cekimserlik (ham)     : OLCUM_YOK")
        print("cekimserlik (enjekte) : OLCUM_YOK")
    else:
        print(f"ihlal orani (ham)     : {ham_oran:.3f}  "
              f"({ham_ihlal}/{n_olcekli}) — BEKLENEN: >0.10 "
              "(aksi halde testin gucu yok)")
        print(f"ihlal orani (enjekte) : {enj_oran:.3f}  "
              f"({enj_ihlal}/{n_olcekli}) — GECME SARTI: tam 0.0")
        print(f"cekimserlik (ham)     : {ozet['cekimserlik_ham']:.3f}")
        print(f"cekimserlik (enjekte) : {ozet['cekimserlik_enjekte']:.3f}  "
              f"— GECME SARTI: <0.60 (asiri temkinliyse sahada kullanilamaz)")
    if n_olcekli == 0:
        print("TOHUM_YOK (ham)       : OLCUM_YOK")
        print("TOHUM_YOK (enjekte)   : OLCUM_YOK")
    else:
        print(f"TOHUM_YOK (ham)       : {ozet['tohum_yok_ham']}/{n_olcekli}")
        print(f"TOHUM_YOK (enjekte)   : {ozet['tohum_yok_enjekte']}/{n_olcekli}")

    if n_olceksiz:
        etiket = "KISMI OLCUM" if n_olcekli else "OLCEKSIZ"
        print(f"\n[{etiket}] {n_olceksiz} karede mpp yok; bu karelerde rota ve ihlal")
        print("               karari uretilmedi, guvenlik paydalarina katilmadi.")
    if n_olcekli == 0:
        print("\n[OLCUM_YOK] Fiziksel olcegi bilinen kare yok; guvenlik sonucu uretilemez.")
    elif ham_oran <= 0.10:
        print("\n[UYARI] ihlal_orani_ham <= 0.10 — bu goruntu kumesi bildirilen hatayi")
        print("        YETERINCE tetiklemiyor olabilir; sonuc 'temiz' degil 'gucsuz'.")
    if ozet["olcum_durumu"] == "TAM_OLCUM" and enj_oran == 0.0:
        print("\n[GECTI] Enjekte kipte SIFIR ihlal — geometri (costmap_path_finder)")
        print("        gercek engel bilgisi verildiginde arabaya DEGMIYOR.")
    elif n_olcekli > 0:
        if enj_oran != 0.0:
            print("\n[KALDI] Enjekte kipte hala ihlal var — kusur GEOMETRIDE, algida degil.")
    if (ozet["olcum_durumu"] == "TAM_OLCUM"
            and ham_oran > 0.10 and enj_oran == 0.0):
        print("[TESHIS] Kusur ALGIDA: navitas modeli araclari engel olarak tanimiyor.")
        print("         Sartname Faz 4.1 (3 sinifli zemin/engel/hedef gecisi) bunu cozer.")

    with open(cikti_dir / "ozet.json", "w", encoding="utf-8") as f:
        json.dump({"ozet": ozet, "kareler": [
            {k: v for k, v in s.items() if k != "sonuc"} for s in tum_sonuclar]},
            f, ensure_ascii=False, indent=2, default=str)
    print(f"\nCikti: {cikti_dir}")
    return _ozet_cikis_kodu(ozet)


if __name__ == "__main__":
    sys.exit(main())
