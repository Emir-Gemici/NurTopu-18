"""
Navitas Autonomous Systems — RPi 5 Inference
Kullanim:
  python3 rpi_inference.py --fps
  python3 rpi_inference.py --image test.jpg
  python3 rpi_inference.py --image gorseller/
  python3 rpi_inference.py --video video.mp4
  python3 rpi_inference.py --video video.mp4 --no-save   (sadece izle, kaydetme)
  python3 rpi_inference.py --camera

Cikti (--image): results/<ad>_result.jpg  (orijinal cozunurluk)
                 results/<ad>_ika_map.jpg  (IKA navigasyon haritasi)
Cikti (--video): results/<ad>_result.mp4  (annotated video)

Dizin yapisi:
  navitas/
    rpi_inference.py
    best_ncnn_model/
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# Gorus hatti rasterizasyonu TEK KAYNAKTAN alinir. Kopyalamak, rota_dogrula ile
# farkli yuvarlama uretip "burada guvenli, orada ihlal" celiskisine yol acardi;
# ayni kopyala-yapistir kusuru bu depoda zaten kayitli (test_rota_sentetik'in
# _tohum_merkezi kopyasi). costmap_path_finder yalniz cv2/numpy/heapq kullanir,
# dairesel import yoktur.
from costmap_path_finder import _gorus_hatti

_here = Path(__file__).parent
MODEL_DIR = next(
    (p for p in [
        _here / "best_ncnn_model",
        _here.parent / "models" / "best_ncnn_model",
        _here / "rescuenet_seg_v1_ncnn",
        _here.parent / "models" / "rescuenet_seg_v1_ncnn",
    ] if p.exists()),
    _here / "best_ncnn_model",
)
RESULTS_DIR = _here / "results"
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
INFER_SIZE = 512

CLASS_COLORS = {
    0: (0, 200, 0),    # traversable — yesil
    1: (0, 0, 200),    # blocked     — kirmizi
}


def load_model():
    if not MODEL_DIR.exists():
        print(f"HATA: Model klasoru bulunamadi: {MODEL_DIR}")
        print("best_ncnn_model/ klasorunu bu scriptle ayni dizine koy.")
        sys.exit(1)
    return YOLO(str(MODEL_DIR), task="segment")


def get_masks(results, h, w, min_conf=None, sinif_idler=(0, 1)):
    """Her sinif icin (h, w) cozunurlugunde binary mask doner.
    min_conf verilirse yalniz guveni >= min_conf tespitler dahil edilir → model DUSUK
    esikle BIR KEZ kosturulup ayni sonuctan farkli esikler suzulebilir (2. predict yok).

    sinif_idler: maskesi uretilecek sinif idleri. Varsayilan (0, 1) ESKI DAVRANISIN
    BIREBIR AYNISIDIR — hicbir mevcut cagri yeri degismez. Costmap hatti ek engel
    siniflari icin genisletir (or. COCO araba/kamyon: sinif_idler=(0,1,2,5,7)).
    Eskiden {0,1} sabit kodluydu ve id >= 2 olan her maske SESSIZCE atiliyordu."""
    masks = {int(c): np.zeros((h, w), dtype=np.uint8) for c in sinif_idler}
    r = results[0]
    if r.masks is None:
        return masks
    confs = r.boxes.conf
    for i, cls in enumerate(r.boxes.cls):
        cls_id = int(cls)
        if cls_id not in masks:
            continue
        if min_conf is not None and float(confs[i]) < min_conf:
            continue
        m = r.masks.data[i].cpu().numpy()
        m_up = cv2.resize(m, (w, h))
        masks[cls_id] = np.maximum(masks[cls_id], (m_up > 0.5).astype(np.uint8))
    return masks


def draw_masks(image_bgr, masks):
    """Traversable=yesil, blocked=kirmizi renkli maske overlay."""
    vis = image_bgr.copy()
    overlay = vis.copy()
    for cls_id, mask in masks.items():
        if mask.sum() == 0:
            continue
        color = CLASS_COLORS.get(cls_id, (128, 128, 128))
        overlay[mask > 0] = color
    return cv2.addWeighted(vis, 0.5, overlay, 0.5, 0)


def _bandda_gorunur_en_genis(band, y0, onceki, gecilebilir, k=64):
    """Bantta, ONCEKI waypoint'ten GORUNEN en genis noktayi sec.

    NEDEN (REVIEW_LOG D-28): eski kod her bandin distance-transform argmax'ini
    korlemesine waypoint yapiyordu. Ardisik iki bandin maksimumu iki AYRI
    koridora dusebiliyor ve aralarindaki dogru engelin ustunden geciyordu —
    olculdu: waypoint 3 (122,399) sol koridorda, waypoint 4 (520,240) sag
    koridorda, aradaki kenar 119 engel pikselinin uzerinden geciyordu.

    Adaylar aciklik sirasina gore denenir; ilk GORUNEN secilir. Hicbiri gorunmuyorsa
    None doner — bu bant onceki waypoint'e bagli degildir.
    """
    duz = band.ravel()
    n = min(int(k), duz.size)
    if n <= 0:
        return None
    idx = np.argpartition(duz, -n)[-n:]
    idx = idx[np.argsort(duz[idx])[::-1]]      # aciklik: buyukten kucuge
    genislik = band.shape[1]
    for j in idx:
        if duz[j] <= 0.5:
            break                               # kalanlar zaten koridor disi
        ly, lx = divmod(int(j), genislik)
        aday = (int(lx), int(y0 + ly))
        if _gorus_hatti(onceki, aday, gecilebilir):
            return aday

    # top-K YANLIS NEGATIF olabilir: bandin en genis k pikseli uzak bir koridorda
    # toplanmissa, onceki waypoint'in tam ustundeki gecerli nokta kacirilir ve
    # halka gereksiz yere "karar yok" der. Duz devam eden koridor icin ucuz bir
    # ikinci sans: onceki waypoint'e x'te EN YAKIN koridor pikselini dene.
    satir = int(np.argmax(band.max(axis=1) > 0.5)) if (band > 0.5).any() else None
    if satir is None:
        return None
    for satir_no in (satir, band.shape[0] // 2, band.shape[0] - 1):
        sutunlar = np.flatnonzero(band[satir_no] > 0.5)
        if sutunlar.size == 0:
            continue
        en_yakin = int(sutunlar[np.argmin(np.abs(sutunlar - onceki[0]))])
        aday = (en_yakin, int(y0 + satir_no))
        if _gorus_hatti(onceki, aday, gecilebilir):
            return aday
    return None


def _kenarlar_guvenli(waypoints, gecilebilir, engel_ham=None):
    """Her ARDISIK waypoint cifti gercekten baglantili mi?

    D-28'in son kapisi: iki ucu serbest olan bir kenar yine de engelin ustunden
    gecebilir. `_gorus_hatti` cizgideki HER pikselin serbest oldugunu dogrular;
    engel maskesi verilmisse ayrica HAM engele temas denetlenir (rota_dogrula
    ile ayni olcut).
    """
    for a, b in zip(waypoints, waypoints[1:]):
        if not _gorus_hatti(a, b, gecilebilir):
            return False
        if engel_ham is None:
            continue
        h, w = engel_ham.shape
        sol, sag = min(a[0], b[0]), max(a[0], b[0])
        ust, alt = min(a[1], b[1]), max(a[1], b[1])
        if not (0 <= sol and sag < w and 0 <= ust and alt < h):
            return False
        cizgi = np.zeros((alt - ust + 1, sag - sol + 1), np.uint8)
        cv2.line(cizgi, (a[0] - sol, a[1] - ust), (b[0] - sol, b[1] - ust),
                 1, thickness=1, lineType=cv2.LINE_8)
        if bool((engel_ham[ust:alt + 1, sol:sag + 1][cizgi > 0] > 0).any()):
            return False
    return True


def analyze_path(trav_mask, n_waypoints=8, return_clean=False,
                 min_area_ratio=0.01, *, icerik=None, engel_mask=None):
    """
    Algoritma:
      1. Morfolojik temizleme (gurultu, kucuk blob)
      1b. engel_mask verilmisse CIKARMA — kapama sonrasi, EN SON (madde 15)
      2. Distance transform → centerline (medial axis approximation)
      3. Yatay bantlarda alt→ust waypoint ornekleme, her adimda GORUS HATTI ile
      4. Ust %40'a bakarak hangi ucte birden cikildigi → open_path
      5. Kenar guvenligi: ardisik waypoint'ler baglantili degilse KARAR YOK

    engel_mask: engel sinifi maskesi (opsiyonel, geriye uyumlu). Verilirse
      morfolojiden SONRA cikarilir — cikarma en son islemdir, sonrasinda serbest
      alani buyuten hicbir sey yapilmaz (CLAUDE.md madde 15). Verilmezse eski
      davranis korunur; kenar denetimi yine de kosar (D-28 kusuru engel zaten
      zeminden dusulmus olsa bile olusabiliyordu).

    min_area_ratio: ana koridor letterbox'taki gercek icerik alaninin bu
      oranindan KUCUKse karar VERME (None doner). Dusuk-esik fallback'te
      gurultuden yol uydurmayi onler — yanlis yonlendirmektense "tespit yok"
      demek gorev guvenligi geregi.

    icerik: letterbox tuvalindeki gercek goruntu dikdortgeni ``(x0,y0,w,h)``.
      Sol/orta/sag sinirlari kare tuvalden degil bu yatay icerik araligindan
      hesaplanir. ``None`` geriye uyumlu olarak tum maskeyi icerik sayar.

    Returns:
      open_path  : 1=sol, 2=orta, 3=sag (None = tespit yok / alan yetersiz)
      confidence : acik yol piksel orani (0.0-1.0)
      waypoints  : [(x, y), ...] alt→ust sirali, goruntu koordinatlari
      (return_clean=True ise 4. eleman: kararin kullandigi TEMIZ koridor
       maskesi — gorsellestirme ham maske yerine bunu basmali)
    """
    h, w = trav_mask.shape
    if icerik is None:
        icerik_x0, icerik_y0, icerik_w, icerik_h = 0, 0, w, h
    else:
        icerik_x0 = max(0, min(w, int(icerik[0])))
        icerik_y0 = max(0, min(h, int(icerik[1])))
        icerik_w = max(0, min(w - icerik_x0, int(icerik[2])))
        icerik_h = max(0, min(h - icerik_y0, int(icerik[3])))
        if icerik_w == 0 or icerik_h == 0:
            if return_clean:
                return None, 0.0, [], np.zeros_like(trav_mask)
            return None, 0.0, []

    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)

    # CIKARMA EN SON (CLAUDE.md madde 15). MORPH_CLOSE extensive'dir ve oyulmus
    # engelin ustunu geri kapatir (REVIEW_LOG D-24: 7 px engelin %99'u geri
    # doldu). Bu yuzden engel maskesi kapamadan SONRA dusulur; bundan sonra
    # serbest alani buyuten hicbir islem yapilmaz.
    if engel_mask is not None:
        engel_mask = (np.asarray(engel_mask) > 0)
        if engel_mask.shape != clean.shape:
            raise ValueError(
                f"engel_mask sekli {engel_mask.shape} trav_mask {clean.shape} ile uyusmuyor")
        # Dogrudan sifirlama: maskenin DEGER ALANINI korur. bitwise_not(...)//255
        # kalibi 0/255 bir girdiyi sessizce 0/1'e indiriyordu.
        clean = clean.copy()
        clean[engel_mask] = 0

    if clean.sum() == 0:
        if return_clean:
            return None, 0.0, [], clean
        return None, 0.0, []

    # EN BUYUK bagli bileseni ANA KORIDOR say → kopuk gurultu bloblari lane kararini
    # ceviremez (girdi cozunurlugu degisince sol/orta/sag ziplamasini onler).
    n_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    if n_lbl > 2:  # >1 gercek bilesen (0=arkaplan)
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        clean = (labels == largest).astype(np.uint8)

    # ALAN DENETIMI: dolgu degil, gercek letterbox icerigi paydaya girer.
    if clean.sum() < min_area_ratio * icerik_w * icerik_h:
        if return_clean:
            return None, 0.0, [], np.zeros_like(clean)
        return None, 0.0, []

    # Acik yol = koridorun HEDEFE (ust) ulastigi taraf. Ust banttaki YATAY MERKEZ
    # (centroid) -> lane. Piksel-argmax yerine centroid: girdi cozunurlugu/kalitesi
    # degisince sol/orta/sag ziplamasini onler (kararli, boyuttan bagimsiz).
    ys, xs = np.nonzero(clean)
    ymin, ymax = int(ys.min()), int(ys.max())
    band = ys <= ymin + 0.30 * (ymax - ymin + 1)   # koridorun ust %30'u
    bx = xs[band] if band.any() else xs
    cx = float(bx.mean())
    sinir_1 = icerik_x0 + icerik_w / 3.0
    sinir_2 = icerik_x0 + 2.0 * icerik_w / 3.0
    open_path = 1 if cx < sinir_1 else (2 if cx < sinir_2 else 3)
    # Guven: ust banttaki piksellerin secilen ucte-bire dusen orani (netlik olcusu).
    lo = icerik_x0 + (open_path - 1) * icerik_w / 3.0
    hi = icerik_x0 + open_path * icerik_w / 3.0
    in_third = int(((bx >= lo) & (bx < hi)).sum())
    confidence = round(in_third / max(1, bx.size), 3)

    # Distance transform centerline
    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)

    # Bantlar ICERIK kutusu uzerinden bolunur; letterbox dolgusundaki bantlar
    # zaten bos olurdu ve denetlenmemis atlamayi uzatirdi (D-25 ailesi).
    bant_ust, bant_alt = icerik_y0, icerik_y0 + icerik_h
    waypoints = []
    for i in range(n_waypoints - 1, -1, -1):  # alt → ust
        y0 = bant_ust + i * (bant_alt - bant_ust) // n_waypoints
        y1 = bant_ust + (i + 1) * (bant_alt - bant_ust) // n_waypoints
        if y1 <= y0:
            continue
        band = dist[y0:y1, :]
        if band.size == 0 or band.max() <= 0.5:
            continue
        if not waypoints:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            waypoints.append((int(lx), int(y0 + ly)))
            continue
        aday = _bandda_gorunur_en_genis(band, y0, waypoints[-1], clean)
        if aday is None:
            # Bu bant onceki waypoint'ten GORUNMUYOR. Koridor tek parca degil;
            # bant-argmax sezgisi burada gecersizdir. Yanlis guzergah uretmektense
            # "tespit yok" demek gorev guvenligi geregidir (sartname §5.3.2).
            if return_clean:
                return None, 0.0, [], clean
            return None, 0.0, []
        waypoints.append(aday)

    # SON KAPI: iki ucu serbest olan bir kenar yine de engelin ustunden gecebilir.
    if len(waypoints) >= 2 and not _kenarlar_guvenli(waypoints, clean, engel_mask):
        if return_clean:
            return None, 0.0, [], clean
        return None, 0.0, []

    if return_clean:
        return open_path, confidence, waypoints, clean
    return open_path, confidence, waypoints


def generate_ika_map(waypoints, open_path, confidence, src_h, src_w, map_size=512):
    """
    IKA icin navigasyon haritasi. Gercek goruntu yok.
    Sadece centerline, waypoint koordinatlari, hedef noktasi.

    IKA bu haritayi alir + kendi kamerasini kullanarak eslestirir.
    """
    canvas = np.full((map_size, map_size, 3), 22, dtype=np.uint8)

    # Grid
    step = map_size // 8
    for i in range(0, map_size + 1, step):
        cv2.line(canvas, (i, 0), (i, map_size), (42, 42, 42), 1)
        cv2.line(canvas, (0, i), (map_size, i), (42, 42, 42), 1)

    # Uc bolge siniri (sol/orta/sag)
    for x in [map_size // 3, 2 * map_size // 3]:
        cv2.line(canvas, (x, 0), (x, map_size), (60, 60, 60), 1)
    for j, label in enumerate(["SOL", "ORTA", "SAG"]):
        lx = j * map_size // 3 + map_size // 12
        color = (0, 220, 0) if (j + 1 == open_path) else (60, 60, 60)
        cv2.putText(canvas, label, (lx, map_size - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)

    # IKA baslangic
    start = (map_size // 2, map_size - 20)
    cv2.circle(canvas, start, 7, (0, 200, 255), -1)
    cv2.putText(canvas, "IKA", (start[0] + 10, start[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)

    if waypoints:
        sx = map_size / src_w
        sy = map_size / src_h
        scaled = [(int(x * sx), int(y * sy)) for x, y in waypoints]

        # Yol cizgisi
        pts = np.array(scaled, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts], False, (0, 210, 0), 3)

        # Waypoint noktalar + seyrek koordinat etiketi
        for j, ((px, py), (ox, oy)) in enumerate(zip(scaled, waypoints)):
            cv2.circle(canvas, (px, py), 4, (80, 255, 80), -1)
            if j % 2 == 0:
                cv2.putText(canvas, f"({ox},{oy})", (px + 5, py - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.26, (150, 150, 150), 1)

        # Hedef
        tx, ty = scaled[-1]
        cv2.circle(canvas, (tx, ty), 10, (0, 255, 255), 2)
        cv2.circle(canvas, (tx, ty), 4, (0, 255, 255), -1)
        cv2.putText(canvas, "HEDEF", (tx + 12, ty + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 255), 1)

        # Ok yonu (son segment)
        if len(scaled) >= 2:
            cv2.arrowedLine(canvas, scaled[-2], scaled[-1],
                            (0, 255, 120), 2, tipLength=0.4)

        # Baslangictan ilk waypoint'e kesikli bag
        cv2.line(canvas, start, scaled[0], (80, 80, 200), 1)

    direction = {1: "SOL", 2: "ORTA", 3: "SAG"}.get(open_path, "?")
    cv2.putText(canvas, f"ACIK YOL: {open_path} ({direction})  GUVEN: {confidence:.2f}",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(canvas, f"WP: {len(waypoints)}  KAYNAK: {src_w}x{src_h}px",
                (8, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.37, (140, 140, 140), 1)

    return canvas


DARK_L_MEAN = 80.0   # LAB L ortalamasi bunun altindaysa goruntu KARANLIK sayilir


def is_dark(img):
    """Goruntu los/golgeli mi? (LAB L ortalamasina gore)"""
    return float(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].mean()) < DARK_L_MEAN


def normalize_light(img):
    """Isik normalizasyonu — model golge/los isikta cokuyor (bilinen zayiflik).
    Karanlik goruntuyu acar: gamma (ortalamayi ~125'e ceker) + CLAHE (LAB L —
    golge altindaki dokuyu lokal esitler). Normal pozlanmis goruntu AYNEN doner.
    NOT: tek basina kullanma — normalizasyon bazi goruntulerde tespiti BOZAR;
    dogru kullanim orijinalle YARISTIRMAK (bkz. iha_perceive._infer)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    mean = float(lab[:, :, 0].mean())
    if mean >= DARK_L_MEAN:
        return img
    # gamma = log(hedef)/log(mevcut) → ortalamayi ~125'e tasi (asiri patlatmaz)
    gamma = max(0.35, min(1.0, np.log(125.0 / 255.0) / np.log(max(mean, 1.0) / 255.0)))
    lut = ((np.arange(256) / 255.0) ** gamma * 255.0).clip(0, 255).astype(np.uint8)
    out = cv2.LUT(img, lut)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _preprocess(img):
    """Kare LETTERBOX (dolgu) + isik normalizasyonu.
    (kare_tuval, 512x512_infer, icerik_dikdortgeni) doner.

    NEDEN CROP DEGIL PAD: onceki surum MERKEZI KARE CROP yapiyordu. 1024x576 bir
    drone karesinde bu x=[224,800] araligini birakip genisligin %56'sini ATIYORDU
    → soldaki ve sagdaki guzergah, karar verilmeden once yok oluyordu. Sartname
    HTAB icinde 3 guzergah tanimliyor ve gunun birinde SOL veya SAG acik olabilir;
    o yuzden kenarlari atmak gorevi dogrudan kaybettirir.
    Ayni cozumu simulation/scripts/iha_perceive.py:52 zaten uyguluyordu.

    icerik_dikdortgeni = (x0, y0, w, h): gercek goruntunun tuval icindeki yeri.
    Dolgu bolgesinden gelen sahte tespitleri elemek icin
    _maskeleri_icerige_kirp() ile birlikte kullanilir.
    """
    h, w = img.shape[:2]
    # Isik normalizasyonu DOLGUDAN ONCE: gri dolgu LAB ortalamasini kaydirip
    # is_dark() kararini bozardi.
    norm = normalize_light(img)
    yan = max(h, w)
    tuval = np.full((yan, yan, 3), 114, dtype=np.uint8)
    x0, y0 = (yan - w) // 2, (yan - h) // 2
    tuval[y0:y0 + h, x0:x0 + w] = norm
    small = cv2.resize(tuval, (INFER_SIZE, INFER_SIZE))
    return tuval, small, (x0, y0, w, h)


def _maskeleri_icerige_kirp(masks, icerik):
    """Letterbox dolgusuna dusen maske pikselleri sifirlanir (sahte tespit onlemi)."""
    x0, y0, w, h = icerik
    for k in list(masks):
        kirpik = np.zeros_like(masks[k])
        kirpik[y0:y0 + h, x0:x0 + w] = masks[k][y0:y0 + h, x0:x0 + w]
        masks[k] = kirpik
    return masks


def _draw_waypoints(vis, waypoints):
    if len(waypoints) < 1:
        return vis
    for j in range(len(waypoints) - 1):
        cv2.line(vis, waypoints[j], waypoints[j + 1], (0, 255, 255), 2)
    for wp in waypoints[:-1]:
        cv2.circle(vis, wp, 4, (0, 255, 255), -1)
    # Hedef noktasi
    cv2.circle(vis, waypoints[-1], 9, (0, 255, 255), -1)
    cv2.circle(vis, waypoints[-1], 12, (0, 0, 0), 2)
    return vis


def run_fps(model, n=30):
    dummy = np.zeros((INFER_SIZE, INFER_SIZE, 3), dtype=np.uint8)
    model.predict(dummy, imgsz=INFER_SIZE, verbose=False)

    start = time.perf_counter()
    for _ in range(n):
        model.predict(dummy, imgsz=INFER_SIZE, verbose=False)
    elapsed = time.perf_counter() - start

    fps = n / elapsed
    ms = elapsed / n * 1000
    print(f"\n=== FPS Olcumu ({n} kare) ===")
    print(f"FPS      : {fps:.1f}")
    print(f"ms/kare  : {ms:.0f}")
    print(f"Hedef    : >=10 FPS")
    print("Sonuc    :", "BASARILI" if fps >= 10 else "YETERSIZ — imgsz=256 ile tekrar dene")


def run_image(model, path_str, conf):
    path = Path(path_str)
    RESULTS_DIR.mkdir(exist_ok=True)

    if path.is_dir():
        files = sorted(f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXT)
        if not files:
            print(f"Klasorde gorsel bulunamadi: {path}")
            return
        print(f"{len(files)} gorsel isleniyor -> {RESULTS_DIR}/")
    elif path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXT:
            print(f"Desteklenmeyen format: {path.suffix}  (desteklenen: jpg png bmp)")
            return
        files = [path]
    else:
        print(f"Dosya/klasor bulunamadi: {path}")
        return

    for img_path in files:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"Okunamadi: {img_path}")
            continue

        sq, small, icerik = _preprocess(img)
        orig_h, orig_w = sq.shape[:2]

        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        masks = get_masks(results, orig_h, orig_w)
        masks = _maskeleri_icerige_kirp(masks, icerik)

        open_path, path_conf, waypoints = analyze_path(
            masks[0], icerik=icerik, engel_mask=masks.get(1))
        vis = draw_masks(sq, masks)

        if open_path:
            vis = _draw_waypoints(vis, waypoints)
            info = f"Acik yol: {open_path}  guven: {path_conf:.2f}"
            ika_data = {
                "open_path": open_path,
                "confidence": path_conf,
                "waypoints": waypoints,
                "timestamp": int(time.time()),
            }
        else:
            info = "Tespit yok"
            ika_data = None

        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        out_path = RESULTS_DIR / f"{img_path.stem}_result.jpg"
        cv2.imwrite(str(out_path), vis)
        print(f"{img_path.name:30s}  {info}  ({orig_w}x{orig_h}) -> {out_path.name}")

        if ika_data:
            ika_map = generate_ika_map(waypoints, open_path, path_conf, orig_h, orig_w)
            ika_map_path = RESULTS_DIR / f"{img_path.stem}_ika_map.jpg"
            cv2.imwrite(str(ika_map_path), ika_map)
            print(f"{'':30s}  IKA harita -> {ika_map_path.name}")
            print(f"{'':30s}  payload: {json.dumps(ika_data)}")


def run_video(model, path_str, conf, save=True):
    path = Path(path_str)
    if not path.is_file():
        print(f"Dosya bulunamadi: {path}")
        return
    if path.suffix.lower() not in SUPPORTED_VIDEO_EXT:
        print(f"Desteklenmeyen format: {path.suffix}  (desteklenen: {', '.join(SUPPORTED_VIDEO_EXT)})")
        return

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"Video acilamadi: {path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    side = max(src_w, src_h)   # letterbox KARE tuval — crop degil, pad (bkz. _preprocess)

    writer = None
    if save:
        RESULTS_DIR.mkdir(exist_ok=True)
        out_path = RESULTS_DIR / f"{path.stem}_result.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, src_fps, (side, side))

    print(f"Video: {path.name}  {src_w}x{src_h}  {src_fps:.1f}fps  {total_frames} kare")
    print(f"Cikti: {out_path if save else 'kayit yok'}  — izlemek icin 'q'")

    fps_buf = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        sq, small, icerik = _preprocess(frame)
        orig_h, orig_w = sq.shape[:2]

        t0 = time.perf_counter()
        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        masks = get_masks(results, orig_h, orig_w)
        masks = _maskeleri_icerige_kirp(masks, icerik)
        open_path, path_conf, waypoints = analyze_path(
            masks[0], icerik=icerik, engel_mask=masks.get(1))
        vis = draw_masks(sq, masks)

        if open_path:
            vis = _draw_waypoints(vis, waypoints)
            label = f"Yol: {open_path}  guven: {path_conf:.2f}"
        else:
            label = "Tespit yok"

        live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
        progress = f"{frame_idx}/{total_frames}" if total_frames > 0 else str(frame_idx)
        cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(vis, f"FPS: {live_fps:.1f}  Kare: {progress}",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if writer:
            writer.write(vis)

        cv2.imshow("Navitas", vis)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Kullanici durdurdu.")
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    elapsed = sum(fps_buf) / len(fps_buf) * frame_idx if fps_buf else 0
    print(f"\n{frame_idx} kare islendi  —  ortalama {1/( sum(fps_buf)/len(fps_buf)):.1f} FPS")
    if save and writer:
        print(f"Kaydedildi: {out_path}")


def run_camera(model, conf):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Kamera acilamadi.")
        return

    print("Kamera acik — cikmak icin 'q'")
    fps_buf = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        sq, small, icerik = _preprocess(frame)
        orig_h, orig_w = sq.shape[:2]

        t0 = time.perf_counter()
        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        masks = get_masks(results, orig_h, orig_w)
        masks = _maskeleri_icerige_kirp(masks, icerik)
        open_path, path_conf, waypoints = analyze_path(
            masks[0], icerik=icerik, engel_mask=masks.get(1))
        vis = draw_masks(sq, masks)

        if open_path:
            vis = _draw_waypoints(vis, waypoints)
            label = f"Yol: {open_path}  guven: {path_conf:.2f}"
        else:
            label = "Tespit yok"

        live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
        cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(vis, f"FPS: {live_fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Navitas", vis)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Navitas RPi Inference")
    parser.add_argument("--fps", action="store_true", help="FPS olcumu")
    parser.add_argument("--image", type=str, help="Gorsel dosya veya klasor yolu")
    parser.add_argument("--video", type=str, help="Video dosyasi (.mp4 .avi .mov ...)")
    parser.add_argument("--camera", action="store_true", help="Canli kamera")
    parser.add_argument("--no-save", action="store_true", help="Video modunda ciktiyi kaydetme")
    parser.add_argument("--conf", type=float, default=0.30, help="Guven esigi (varsayilan: 0.30)")
    args = parser.parse_args()

    if not any([args.fps, args.image, args.video, args.camera]):
        parser.print_help()
        return

    model = load_model()

    if args.fps:
        run_fps(model)
    elif args.image:
        run_image(model, args.image, args.conf)
    elif args.video:
        run_video(model, args.video, args.conf, save=not args.no_save)
    elif args.camera:
        run_camera(model, args.conf)


if __name__ == "__main__":
    main()
