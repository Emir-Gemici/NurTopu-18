"""
İHA ALAN HARİTALAMA — tarama karelerinden ORTOMOZAİK + model kararı + İKA rotası.

Dürüst haritalandırma zincirinin HOST tarafı (torch/ultralytics .venv'de):

  Gazebo (konteyner)                           Bu betik (host .venv)
  ──────────────────                           ─────────────────────
  İHA 30 m'de serpantin uçar                   kareler + poz logu senkronlanır
  scan_camera 1 Hz kare kaydeder     ──────►   1) ORTOMOZAİK: her kare, çekildiği
  plugin İHA pozunu 1 Hz loglar                   andaki İHA pozuna göre döndürülüp
  (t,x,y,z,yaw → iha_scan_poses.csv)              kuzey-yukarı saha haritasına oturtulur
  tarama bitince SCAN_DONE işareti   ──────►   2) MODEL: iha_perceive._infer mozaikte
                                                  koşar → açık yol + waypoint (piksel)
  İKA rotayı BEKLER                  ◄──────   3) KOORDİNAT: piksel → HTAB-yerel metre
  (plugin /tmp/navitas_route okur)                → dünya (x,y) → route.txt
  İKA MODELİN haritasını sürer                 4) Çıktılar: ortomozaik.jpg, algi.jpg,
                                                  detection.json, route.txt

Model yanılırsa İKA yanlış/kapalı yola gider ve fizik onu durdurur — SONUÇ DÜRÜSTTÜR.
(Eski akış: model sabit fotoğrafa bakar, dünya modelin dediğine göre kurulurdu = sahte.)

KOORDİNAT SÖZLEŞMESİ
  Mozaik: MOZ_PX×MOZ_PX piksel = HTAB + kenar payı, KUZEY YUKARI (dünya +Y = görüntü yukarı,
  dünya +X = görüntü sağı). Piksel↔metre: mpp = MOZ_M / MOZ_PX.
    dünya_x = cx + (px − MOZ_PX/2)·mpp        dünya_y = cy + (MOZ_PX/2 − py)·mpp

KARE↔POZ EŞLEME (kalibrasyon knob'ları — ilk gerçek koşuda doğrulanır):
  kamera 1 Hz kare çeker, plugin 1 Hz poz yazar → k. kare ↔ t = k + --kare-ofset satırı.
  Görüntünün "yukarısı" İHA yaw'ına bağlı döner; kuzey-yukarı için kare CCW yönünde
  yaw·(--rot-isaret) kadar döndürülür (işaret ilk koşuda H/bariyer konumundan doğrulanır).

Kullanım:
  # record.sh arka planda başlatır (canlı izleme, tüm seviyeler):
  .venv/bin/python simulation/scripts/iha_haritala.py --watch simulation/recordings/v15 \
      --levels "kolay orta zor"
  # offline analiz / kalibrasyon (kaydedilmiş tarama klasörüyle):
  .venv/bin/python simulation/scripts/iha_haritala.py --once simulation/recordings/v15/iha_scan_kolay
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "codes"))

from iha_perceive import _infer, _overlay, DEFAULT_MODEL, LABEL   # noqa: E402
from costmap_path_finder import rota_bul                          # noqa: E402
from arac_maskesi import ARAC_SINIFLERI, obb_arac_maskesi         # noqa: E402
from sinif_semasi import (COSTMAP_ENGEL_KATMANLARI,               # noqa: E402
                          COSTMAP_YOL_KATMANLARI, costmap_katmanlari)

# ── Mozaik sabitleri ──────────────────────────────────────────────────────────
MOZ_PX   = 1024            # mozaik kenarı (px) — iha_perceive CANON ile aynı → ölçeksiz infer
MOZ_M    = 56.0            # mozaiğin kapladığı alan (m) — HTAB 50 + 3 m kenar payı
MPP      = MOZ_M / MOZ_PX  # metre/piksel (~0.055)
HFOV     = 1.3             # scan_camera horizontal_fov (models/iha/model.sdf ile AYNI)
SCAN_Z   = 30.0            # tarama irtifası (world_generator.SCAN_Z ile AYNI)
BG_GRI   = 114             # boş mozaik zemini (YOLO letterbox nötr grisi)
DEFAULT_ARAC_MODEL = ROOT / "yolov8m-obb.pt"
# ARAC_SINIFLERI artik `codes/arac_maskesi.py`'den import ediliyor (S1).
# Buradaki yerel kopya import'u GOLGELIYORDU: iki kaynak, sessiz sapma riski.

# Kare filtresi: sadece DÜZ tarama bacakları (kuzey/güney uçuş, yatay kanat).
# Dönüşlerde İHA 40°'ye dek yatar → kare eğik, mozaiğe koyma.
Z_TOL    = 0.6             # |z − 30| < 0.6 m
YAW_TOL  = 0.15            # |beklenen ±90°'den sapma| < ~8.6°
HTAB_HALF_MARJ = 26.0      # İHA bu sınırın dışındayken kare mozaiğe alınmaz


def poz_oku(csv_path):
    """poses.csv → {kare_no: (x, y, z, yaw)}.

    Yeni format (navitas_scan_cam, KARE İLE AYNI OLAYDA yazılır → birebir senkron):
        n,t,x,y,z,yaw
    Eski format (navitas_anim 1 Hz, v15 — senkron kayması vardı, geriye-uyum):
        t,x,y,z,yaw   (anahtar = t ≈ kare sırası)"""
    pozlar = {}
    for line in Path(csv_path).read_text().splitlines():
        parts = line.strip().split(",")
        try:
            if len(parts) == 6:                    # yeni: n,t,x,y,z,yaw
                pozlar[int(float(parts[0]))] = tuple(float(v) for v in parts[2:])
            elif len(parts) == 5:                  # eski: t,x,y,z,yaw
                pozlar[int(float(parts[0]))] = tuple(float(v) for v in parts[1:])
        except ValueError:
            continue
    return pozlar


def mozaik_kur(kare_dir, pozlar, htab_cx, htab_cy, kare_ofset=0, rot_isaret=1.0,
               debug=False):
    """Tarama karelerini kuzey-yukarı saha haritasına diz → (mozaik BGR, kullanılan_n).

    Her karenin yer kapsama genişliği: 2·z·tan(hfov/2)  (z=30, hfov=1.3 → ~45.6 m).
    Kare önce bu genişliğe ölçeklenir, İHA yaw'ına göre kuzey-yukarı döndürülür,
    İHA'nın o anki (x,y) konumu merkez olacak şekilde tuvale yapıştırılır.
    Sonra gelen kare öncekinin üstüne yazar (serpantin bindirmeli tarar → boşluk kalmaz)."""
    import cv2
    import numpy as np

    import re
    canvas = np.full((MOZ_PX, MOZ_PX, 3), BG_GRI, dtype=np.uint8)
    kareler = sorted(kare_dir.glob("*.jpg"))
    kullanilan = 0
    for sira, kf in enumerate(kareler):
        # kare no DOSYA ADINDAN (scan_00042.jpg → 42): senkron plugin poses.csv'nin
        # n sütunuyla birebir. Numara yoksa (eski kayıt) sıra kullanılır.
        m = re.search(r"(\d+)\.jpg$", kf.name)
        k = int(m.group(1)) if m else sira
        poz = pozlar.get(k + kare_ofset)
        if poz is None:
            continue
        x, y, z, yaw = poz
        # Sadece düz tarama bacakları: irtifa 30 m ve yaw ≈ ±90° (kuzey/güney uçuş)
        if abs(z - SCAN_Z) > Z_TOL or abs(abs(yaw) - math.pi / 2) > YAW_TOL:
            continue
        # İHA HTAB dışındayken çekilen kare mozaiğe girmez (v15: İHA-İB'ye sokulma
        # bacağının karesi sağ üstte 'hayalet' yama bırakmıştı)
        if abs(x - htab_cx) > HTAB_HALF_MARJ or abs(y - htab_cy) > HTAB_HALF_MARJ:
            continue
        img = cv2.imread(str(kf))
        if img is None:
            continue

        ayak_m = 2.0 * z * math.tan(HFOV / 2.0)          # karenin yerdeki genişliği (m)
        ayak_px = max(8, int(round(ayak_m / MPP)))
        img = cv2.resize(img, (ayak_px, ayak_px), interpolation=cv2.INTER_AREA)

        # Kuzey-yukarı döndür: görüntü "yukarısı" İHA burnunun azimutuna bağlı.
        # (rot_isaret ilk koşuda kalibre edilir: H kuzeyde, bariyerler güneyde olmalı.)
        aci_deg = math.degrees(yaw) * rot_isaret
        M = cv2.getRotationMatrix2D((ayak_px / 2, ayak_px / 2), aci_deg, 1.0)
        img = cv2.warpAffine(img, M, (ayak_px, ayak_px),
                             flags=cv2.INTER_LINEAR, borderValue=(BG_GRI,) * 3)

        # HTAB-yerel konum → tuval pikseli (kuzey yukarı: +y → −py)
        px = int(round((x - htab_cx) / MPP + MOZ_PX / 2))
        py = int(round(MOZ_PX / 2 - (y - htab_cy) / MPP))
        x0, y0 = px - ayak_px // 2, py - ayak_px // 2
        # tuval sınırlarına kırp
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        w = min(ayak_px - sx0, MOZ_PX - dx0)
        h = min(ayak_px - sy0, MOZ_PX - dy0)
        if w <= 0 or h <= 0:
            continue
        canvas[dy0:dy0 + h, dx0:dx0 + w] = img[sy0:sy0 + h, sx0:sx0 + w]
        kullanilan += 1
        if debug:
            print(f"  kare {k:3d} t={k + kare_ofset:3d}  poz=({x:6.1f},{y:6.1f},{z:4.1f}) "
                  f"yaw={math.degrees(yaw):6.1f}° → tuval({px},{py})")
    return canvas, kullanilan


def piksel_to_dunya(wps_px, htab_cx, htab_cy):
    """Model waypoint'leri (mozaik pikseli, alt→üst) → dünya (x,y) listesi (güney→kuzey)."""
    out = []
    for (px, py) in wps_px:
        wx = htab_cx + (px - MOZ_PX / 2) * MPP
        wy = htab_cy + (MOZ_PX / 2 - py) * MPP
        out.append((round(wx, 2), round(wy, 2)))
    return out


def dunya_to_piksel(xy, htab_cx, htab_cy):
    """Dunya ``(x, y)`` koordinatini kuzey-yukari mozaik pikseline cevir."""
    if xy is None:
        return None
    wx, wy = float(xy[0]), float(xy[1])
    if not math.isfinite(wx) or not math.isfinite(wy):
        return None
    return (int(round((wx - htab_cx) / MPP + MOZ_PX / 2)),
            int(round(MOZ_PX / 2 - (wy - htab_cy) / MPP)))


def _tohum_maskesi(xy, htab_cx, htab_cy, sekil, yaricap_m=0.0):
    """KB/HB dunya konumundan costmap icin tohum maskesi uret.

    Varsayilan tek piksel, rotanin gercek baslangic/hedefe sabitlenmesini
    saglar. Daha genis bir tolerans ancak cagirici acikca isterse kullanilir.
    """
    import cv2
    import numpy as np

    maske = np.zeros(sekil, np.uint8)
    nokta = dunya_to_piksel(xy, htab_cx, htab_cy)
    if nokta is None:
        return maske
    x, y = nokta
    h, w = sekil
    if not (0 <= x < w and 0 <= y < h):
        return maske
    if yaricap_m <= 0:
        maske[y, x] = 1
    else:
        yaricap_px = max(1, int(round(yaricap_m / MPP)))
        cv2.circle(maske, (x, y), yaricap_px, 1, -1)
    return maske


def _atomik_yaz(path, metin):
    """Tam yazilmamis bir rota dosyasinin tuketicilerce gorulmesini engelle."""
    path = Path(path)
    gecici = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        gecici.write_text(metin, encoding="utf-8")
        gecici.replace(path)
    finally:
        if gecici.exists():
            gecici.unlink()


def _rota_artiklarini_sil(level_dir):
    """Basarisiz yeni algi sonucunun onceki rota artefaktini kullanmasini onle."""
    for ad in ("route.txt", "rota.json"):
        yol = Path(level_dir) / ad
        if yol.is_file():
            yol.unlink()


def _arac_maskesi(bgr, arac_model, conf=0.25):
    """Ayni mozaik koordinatinda OBB arac maskesi uret.

    S1: govde `codes/arac_maskesi.py`'ye TASINDI ve sentetik veri ureteciyle
    PAYLASILIYOR. Eskiden iki ayri kopya vardi ve ureteci COCO seg kullaniyordu
    (olculdu: COCO 2 arac / DOTA OBB 93 arac ayni fotografta). Tek kaynak,
    kahin sapmasini yapisal olarak imkansiz kilar.

    Bu sarmalayici cagri yerlerini bozmamak icin durur.
    """
    return obb_arac_maskesi(bgr, arac_model, conf=conf)


def haritala(level_dir, model, htab_cx, htab_cy, conf=0.15,
             kare_ofset=0, rot_isaret=1.0, debug=False, kb_xy=None, hb_xy=None,
             arac_model=None, arac_conf=0.25):
    """Bir seviyenin tarama klasörünü işle: mozaik → algı → costmap → rota.
    kb_xy = İKA başlangıç REFERANS noktası (dünya), hb_xy = HB (dünya, önceden bilinir).
    Çıktılar level_dir'e: ortomozaik/algi jpg + route.txt (plugin) + rota.json (İKA'ya
    JSON aktarım formatı: referans + yerel koordinatlar). Döner: detection dict."""
    import cv2

    level_dir = Path(level_dir)
    kare_dir = level_dir / "kareler"
    poses = level_dir / "poses.csv"
    det = {"road": None, "label": "yok", "conf": 0.0, "image": "ortomozaik.jpg",
           "kaynak": "sim-tarama", "kare_n": 0}

    if not kare_dir.is_dir() or not poses.is_file():
        _rota_artiklarini_sil(level_dir)
        print(f"[İHA-HARİTA] eksik girdi: {kare_dir} / {poses}", file=sys.stderr)
        return det

    pozlar = poz_oku(poses)
    mozaik, n = mozaik_kur(kare_dir, pozlar, htab_cx, htab_cy,
                           kare_ofset=kare_ofset, rot_isaret=rot_isaret, debug=debug)
    det["kare_n"] = n
    cv2.imwrite(str(level_dir / "ortomozaik.jpg"), mozaik)
    print(f"[İHA-HARİTA] mozaik: {n} tarama karesi → {level_dir / 'ortomozaik.jpg'}")
    if n == 0:
        _rota_artiklarini_sil(level_dir)
        print("[İHA-HARİTA] hiç kare oturtulamadı (poz eşleşmesi?) — rota YOK", file=sys.stderr)
        (level_dir / "detection.json").write_text(json.dumps(det, ensure_ascii=False, indent=2))
        return det

    # ── MODEL: gerçek best.pt mozaikte (İHA'nın kendi taramasında!) karar verir ──
    # Model maskeleri tek basina rota degildir. Kalibre mozaik olceginde
    # serbest alan = zemin - (arac|moloz|engel) kurulur; A* KB'den HB'ye
    # sadece bu C-uzayinda rota uretirse IKA'ya rota verilir.
    content, masks, _model_road, _model_conf, _old_wps, _ = _infer(
        mozaik, model, conf, MOZ_PX)
    # Free_Space = Road - (Rubble/blocked | Car).  Segmentasyonun blocked
    # sinifi molozu tasir; OBB arac poligonlari ayni mozaik piksel sisteminde
    # ek bir engel kanali olur. Costmap bu iki kanali OR'layarak C-uzayini kurar.
    arac = _arac_maskesi(content, arac_model, arac_conf)
    # S2: katman kimlikleri EGITIM sinif id'lerinden AYRI bir ad alanindadir.
    # Eskiden burada `{0:.., 1:.., 2: arac}` yaziliyordu; 3 sinifli bir model bu
    # yola verildiginde 2 = HEDEF ile 2 = ARAC cakisir ve hedef ENGEL sayilirdi.
    costmap_maskeleri = costmap_katmanlari(masks[0], masks[1], arac)
    # Dinamik rota, fiziksel hedefe (HB) kadar dogrulanmis olmalidir. HB meta
    # verisi yokken costmap'in varsayilan ust bant tohumuna plan yapmak, IKA'yi
    # gercek hedefe gitmeyen ama geometri olarak gecerli gorunen bir rotaya
    # baslatabilirdi. Bu durumda algiyi kaydet, onceki rota artefaktlarini sil
    # ve IKA'nin guvenli durmasini sagla.
    if hb_xy is None:
        det.update({
            "trav_px": int(masks[0].sum()),
            "moloz_px": int(masks[1].sum()),
            "arac_px": int(arac.sum()),
            "engel_px": int((masks[1] | arac).sum()),
            "arac_model": (str(getattr(arac_model, "ckpt_path", DEFAULT_ARAC_MODEL))
                           if arac_model is not None else None),
            "wp_n": 0,
            "rota_durum": "HEDEF_YOK",
            "rota_sebep": "HB koordinati bulunamadi; dinamik rota yayinlanmadi.",
            "darbogaz_m": None,
            "rota_ihlalleri": [],
        })
        vis = _overlay(content, costmap_maskeleri, None, 0.0, [],
                       extra="  [SIM TARAMA MOZAIK]")
        cv2.imwrite(str(level_dir / "algi.jpg"), vis)
        _rota_artiklarini_sil(level_dir)
        print("[IHA-HARITA] HB koordinati yok — IKA guvenli durur")
        (level_dir / "detection.json").write_text(
            json.dumps(det, ensure_ascii=False, indent=2), encoding="utf-8")
        return det

    baslangic_xy = kb_xy or (htab_cx, htab_cy - 23.0)
    baslangic = _tohum_maskesi(baslangic_xy, htab_cx, htab_cy,
                               costmap_maskeleri[0].shape)
    hedef = _tohum_maskesi(hb_xy, htab_cx, htab_cy,
                            costmap_maskeleri[0].shape)
    plan_sonucu = rota_bul(costmap_maskeleri, mpp=MPP,
                           baslangic=baslangic, hedef=hedef, plan=True,
                           yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
                           engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,
                           gorsel_cikti=True)
    road = plan_sonucu["yol_no"]
    confidence = plan_sonucu["guven"]
    wps_px = plan_sonucu["waypoints_px"]
    det.update({
        "road": road,
        "label": LABEL.get(road, "yok"),
        "conf": confidence,
        "trav_px": int(masks[0].sum()),
        "moloz_px": int(masks[1].sum()),
        "arac_px": int(arac.sum()),
        "engel_px": int((masks[1] | arac).sum()),
        "arac_model": (str(getattr(arac_model, "ckpt_path", DEFAULT_ARAC_MODEL))
                       if arac_model is not None else None),
        "wp_n": len(wps_px),
        "rota_durum": plan_sonucu["durum"],
        "rota_sebep": plan_sonucu["sebep"],
        "darbogaz_m": plan_sonucu["darbogaz_m"],
        "rota_ihlalleri": plan_sonucu["ihlaller"],
    })

    vis = _overlay(content, costmap_maskeleri, road, confidence, wps_px,
                   extra="  [SIM TARAMA MOZAIK]")
    cv2.imwrite(str(level_dir / "algi.jpg"), vis)

    # ── ROTA: costmap'in DOGRULADIGI waypoint dizisini degistirmeden aktar ──
    # Waypoint silmek, yeniden etiketlemek veya dogrudan HB eklemek yeni ve
    # dogrulanmamis segmentler uretir. KB/HB ankorlari rota_bul() icinde
    # C-uzayinda dogrulanmistir; burada yalniz koordinat sistemi cevrilir.
    rota = []
    if plan_sonucu["durum"] == "ACIK" and road and len(wps_px) >= 2:
        rota = piksel_to_dunya(wps_px, htab_cx, htab_cy)
    if rota:
        # Referans, costmap'in dogruladigi ilk fiziksel ankor noktadir. Ilk
        # yerel waypoint daima [0,0] olur; IKA sahte bir KB->rota segmenti
        # eklemeden bu diziyi aynen takip eder.
        ref = rota[0]
        rota_json = json.dumps({
            "referans_xy": [round(ref[0], 2), round(ref[1], 2)],
            "kb_xy": [round(baslangic_xy[0], 2), round(baslangic_xy[1], 2)],
            "acik_yol": det["label"], "yol_no": road, "guven": confidence,
            "hb_xy": [round(hb_xy[0], 2), round(hb_xy[1], 2)] if hb_xy else None,
            "rota_dunya": [[round(x, 2), round(y, 2)] for x, y in rota],
            "rota_yerel": [[round(x - ref[0], 2), round(y - ref[1], 2)]
                           for x, y in rota],
        }, ensure_ascii=False, indent=2)
        # Tuketici route.txt gorur gormez okumaya baslar; once JSON'u, sonra
        # route.txt'yi atomik olarak yayinla ki hicbir zaman yarim rota tasinmasin.
        _atomik_yaz(level_dir / "rota.json", rota_json)
        _atomik_yaz(level_dir / "route.txt", "".join(f"{x:.2f} {y:.2f}\n" for x, y in rota))
        det["rota"] = rota
        print(f"[İHA-HARİTA] MODEL KARARI: AÇIK YOL {det['label'].upper()} ({road}) "
              f"güven={confidence}  rota {len(rota)} nokta → route.txt + rota.json")
    else:
        # Yeniden calistirilan bir seviyede eski rota dosyasi kalirsa IKA'nin
        # yeni, basarisiz algi sonucuna ragmen onu surmesi tehlikelidir.
        _rota_artiklarini_sil(level_dir)
        det.update({"road": None, "label": "yok"})
        print("[İHA-HARİTA] GÜVENİLİR COSTMAP ROTASI YOK — İKA güvenli durur")

    (level_dir / "detection.json").write_text(
        json.dumps(det, ensure_ascii=False, indent=2), encoding="utf-8")
    return det


def _detections_birlestir(vdir, level, det):
    """$VDIR/detections.json'ı (hakem_log formatı: {seviye:{...}}) güncelle."""
    p = Path(vdir) / "detections.json"
    d = {}
    if p.is_file():
        try:
            d = json.loads(p.read_text())
        except json.JSONDecodeError:
            d = {}
    d[level] = det
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")


def _meta_oku(level_dir):
    """record_in_container'ın yazdığı meta.txt → dict (HTAB_CENTER vs.)."""
    meta = {}
    mp = Path(level_dir) / "meta.txt"
    if mp.is_file():
        for line in mp.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                meta[k.strip()] = v.strip()
    return meta


def _htab_merkez(meta, cli_htab):
    if cli_htab:
        cx, cy = (float(v) for v in cli_htab.split(","))
        return cx, cy
    if "HTAB_CENTER" in meta:
        cx, cy = (float(v) for v in meta["HTAB_CENTER"].split(","))
        return cx, cy
    raise SystemExit("HTAB merkezi bilinmiyor: --htab cx,cy verin (meta.txt de yok)")


def _meta_xy(meta, anahtar):
    """meta.txt'ten 'x,y' çifti oku (KB_XY / HB_XY) — yoksa None."""
    if anahtar in meta and "," in meta[anahtar]:
        try:
            x, y = (float(v) for v in meta[anahtar].split(","))
            return (x, y)
        except ValueError:
            pass
    return None


def watch(vdir, levels, model_path, arac_model_path, conf, arac_conf,
          kare_ofset, rot_isaret, bekle_sn=1800):
    """record.sh akışı: her seviyenin SCAN_DONE işaretini bekle → haritala → rota yaz.
    Konteyner route.txt'yi /tmp/navitas_route'a kopyalar, İKA sürmeye başlar."""
    from ultralytics import YOLO
    model = YOLO(str(model_path), task="segment")     # BİR KEZ yükle (seviyeler arası)
    arac_model = YOLO(str(arac_model_path), task="obb")
    print(f"[İHA-HARİTA] izleme: {vdir}  seviyeler: {levels}")

    for level in levels.split():
        ldir = Path(vdir) / f"iha_scan_{level}"
        marker = ldir / "SCAN_DONE"
        print(f"[İHA-HARİTA] {level}: tarama bekleniyor ({marker})...")
        t0 = time.time()
        while not marker.is_file():
            if time.time() - t0 > bekle_sn:
                print(f"[İHA-HARİTA] {level}: {bekle_sn}s doldu, atlanıyor", file=sys.stderr)
                break
            time.sleep(2)
        if not marker.is_file():
            continue
        time.sleep(2)   # son karelerin senkronu otursun
        meta = _meta_oku(ldir)
        cx, cy = _htab_merkez(meta, None)
        det = haritala(ldir, model, cx, cy, conf=conf,
                       kare_ofset=kare_ofset, rot_isaret=rot_isaret,
                       kb_xy=_meta_xy(meta, "KB_XY"), hb_xy=_meta_xy(meta, "HB_XY"),
                       arac_model=arac_model, arac_conf=arac_conf)
        _detections_birlestir(vdir, level, det)
    print("[İHA-HARİTA] izleme bitti.")


def main():
    ap = argparse.ArgumentParser(description="İHA tarama → ortomozaik → model → İKA rotası")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--watch", help="kayıt dizini (v<N>) — seviyeleri canlı bekle/işle")
    g.add_argument("--once", help="tek iha_scan_<seviye> klasörünü offline işle")
    ap.add_argument("--levels", default="kolay orta zor")
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--arac-model", default=str(DEFAULT_ARAC_MODEL),
                    help="OBB araç modeli (small/large vehicle); engel costmapine OR edilir")
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--arac-conf", type=float, default=0.25)
    ap.add_argument("--htab", default=None, help="HTAB merkezi 'cx,cy' (--once + meta yoksa)")
    ap.add_argument("--kare-ofset", type=int, default=0,
                    help="kare index → poz t kayması (kalibrasyon, vars. 0)")
    ap.add_argument("--rot-isaret", type=float, default=1.0, choices=[1.0, -1.0],
                    help="yaw→görüntü dönüş işareti (kalibrasyon, vars. +1)")
    ap.add_argument("--debug", action="store_true", help="kare yerleşimini satır satır bas")
    args = ap.parse_args()

    arac_model_path = Path(args.arac_model)
    if not arac_model_path.is_file():
        ap.error(f"araç modeli bulunamadı: {arac_model_path}")

    if args.watch:
        watch(args.watch, args.levels, args.model, arac_model_path,
              args.conf, args.arac_conf, args.kare_ofset, args.rot_isaret)
        return

    from ultralytics import YOLO
    ldir = Path(args.once)
    meta = _meta_oku(ldir)
    cx, cy = _htab_merkez(meta, args.htab)
    model = YOLO(str(args.model), task="segment")
    arac_model = YOLO(str(arac_model_path), task="obb")
    det = haritala(ldir, model, cx, cy, conf=args.conf,
                   kare_ofset=args.kare_ofset, rot_isaret=args.rot_isaret, debug=args.debug,
                   kb_xy=_meta_xy(meta, "KB_XY"), hb_xy=_meta_xy(meta, "HB_XY"),
                   arac_model=arac_model, arac_conf=args.arac_conf)
    print(json.dumps(det, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
