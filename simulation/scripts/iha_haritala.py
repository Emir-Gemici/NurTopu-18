"""
İHA ALAN HARİTALAMA — tarama karelerinden ORTOMOZAİK + model kararı + İKA rotası.

Dürüst haritalandırma zincirinin HOST tarafı (torch/ultralytics .venv'de):

  Gazebo (konteyner)                           Bu betik (host .venv)
  ──────────────────                           ─────────────────────
  İHA profil irtifasında serpantin uçar          kareler + poz logu senkronlanır
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
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "codes"))

from iha_perceive import _infer, _overlay, DEFAULT_MODEL, LABEL   # noqa: E402

# ── Mozaik sabitleri ──────────────────────────────────────────────────────────
MOZ_PX   = 1024            # mozaik kenarı (px) — iha_perceive CANON ile aynı → ölçeksiz infer
MOZ_M    = 56.0            # mozaiğin kapladığı alan (m) — HTAB 50 + 3 m kenar payı
MPP      = MOZ_M / MOZ_PX  # metre/piksel (~0.055)
HFOV     = 1.3             # scan_camera horizontal_fov (models/iha/model.sdf ile AYNI)
DEFAULT_SCAN_Z = 30.0      # eski kayıt/meta yokluğu için geriye uyumlu varsayılan
BG_GRI   = 114             # boş mozaik zemini (YOLO letterbox nötr grisi)

# Kare filtresi: sadece DÜZ tarama bacakları (kuzey/güney uçuş, yatay kanat).
# Dönüşlerde İHA 40°'ye dek yatar → kare eğik, mozaiğe koyma.
Z_TOL    = 0.6             # |z − profil tarama irtifası| < 0.6 m
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


def mozaik_kur(kare_dir, pozlar, htab_cx, htab_cy, scan_z=DEFAULT_SCAN_Z,
               kare_ofset=0, rot_isaret=1.0, debug=False):
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
        # Sadece düz tarama bacakları: profil irtifası ve yaw ≈ ±90°.
        if abs(z - scan_z) > Z_TOL or abs(abs(yaw) - math.pi / 2) > YAW_TOL:
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


def _seyrekle(wps, min_m=1.5):
    """1.5 m'den yakın ardışık noktaları at (İKA WP_RADIUS 1.2 — sıkışık wp titretir)."""
    if not wps:
        return wps
    out = [wps[0]]
    for p in wps[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) >= min_m:
            out.append(p)
    return out


def _rota_saglamlik(rota, htab_cx, htab_cy, kb_xy):
    """ROTA SAĞLAMLIK SÜZGECİ — v15 dersi: model 2 noktalık, HTAB DIŞINA işaret eden
    rota üretti; İKA kestirmeden moloz duvarına sürdü. Kurallar:
      1) HTAB sınırı dışındaki noktalar ATILIR (saha 50×50 + 0.5 m tolerans).
      2) İKA başlangıcının (KB) gerisindeki (güneyindeki) noktalar ATILIR.
      3) Rota KUZEYE akmalı: o ana dek ulaşılan en kuzey noktadan 3 m'den fazla
         GERİYE giden nokta atılır (model maskesindeki gürültü zikzakları).
    Döner: temizlenmiş rota (yetersizse boş liste → rota YAZILMAZ, dürüst fallback)."""
    S = 25.5
    temiz, en_kuzey = [], -1e9
    kb_y = kb_xy[1] if kb_xy else htab_cy - 23.0
    for (x, y) in rota:
        if abs(x - htab_cx) > S or abs(y - htab_cy) > S:
            continue                                   # 1) saha dışı
        if y < kb_y + 0.5:
            continue                                   # 2) başlangıcın gerisi
        if y < en_kuzey - 3.0:
            continue                                   # 3) güneye zikzak
        en_kuzey = max(en_kuzey, y)
        temiz.append((x, y))
    return temiz if len(temiz) >= 3 else []


def _etiket_orta_bant(rota, htab_cx):
    """sol/orta/sag etiketini rotanın ORTA bandındaki (|y-cy|≤10) ortalama x'inden türet
    — 3 yol HB'de birleştiği için üst-bant kararı ayırt edici değil; orta bant ayırt eder."""
    if not rota:
        return None
    xs = [x - htab_cx for (x, y) in rota]
    orta = xs[len(xs) // 3: max(len(xs) // 3 + 1, 2 * len(xs) // 3)] or xs
    m = sum(orta) / len(orta)
    return 1 if m < -8 else (3 if m > 8 else 2)


def haritala(level_dir, model, htab_cx, htab_cy, conf=0.15, scan_z=DEFAULT_SCAN_Z,
             kare_ofset=0, rot_isaret=1.0, debug=False, kb_xy=None, hb_xy=None):
    """Bir seviyenin tarama klasörünü işle: mozaik → model → sağlamlık süzgeci → rota.
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
        print(f"[İHA-HARİTA] eksik girdi: {kare_dir} / {poses}", file=sys.stderr)
        return det

    pozlar = poz_oku(poses)
    mozaik, n = mozaik_kur(kare_dir, pozlar, htab_cx, htab_cy, scan_z=scan_z,
                           kare_ofset=kare_ofset, rot_isaret=rot_isaret, debug=debug)
    det["kare_n"] = n
    cv2.imwrite(str(level_dir / "ortomozaik.jpg"), mozaik)
    print(f"[İHA-HARİTA] mozaik: {n} tarama karesi → {level_dir / 'ortomozaik.jpg'}")
    if n == 0:
        print("[İHA-HARİTA] hiç kare oturtulamadı (poz eşleşmesi?) — rota YOK", file=sys.stderr)
        (level_dir / "detection.json").write_text(json.dumps(det, ensure_ascii=False, indent=2))
        return det

    # ── MODEL: gerçek best.pt mozaikte (İHA'nın kendi taramasında!) karar verir ──
    content, masks, road, confidence, wps_px, _ = _infer(mozaik, model, conf, MOZ_PX)
    det.update({"road": road, "label": LABEL.get(road, "yok"), "conf": confidence,
                "trav_px": int(masks[0].sum()), "wp_n": len(wps_px)})

    vis = _overlay(content, masks, road, confidence, wps_px, extra="  [SIM TARAMA MOZAIK]")
    cv2.imwrite(str(level_dir / "algi.jpg"), vis)

    # ── ROTA: piksel→dünya → SAĞLAMLIK SÜZGECİ (v15 dersi) → İKA'ya aktarım ──
    rota = []
    if road:
        rota = _rota_saglamlik(
            _seyrekle(piksel_to_dunya(wps_px, htab_cx, htab_cy)), htab_cx, htab_cy, kb_xy)
    if rota:
        # Etiketi ORTA banttan yeniden türet (3 yol HB'de birleşir; üst bant yanıltır)
        r2 = _etiket_orta_bant(rota, htab_cx)
        if r2 and r2 != road:
            road = r2
            det.update({"road": road, "label": LABEL.get(road, "yok"),
                        "etiket_kaynak": "orta-bant"})
        # HB yarışmada ÖNCEDEN bilinir (işaretli pad); bilinmeyen HANGİ yol açık.
        # Son hedef olarak HB'yi ekle (meta'dan; yoksa rota son noktası kalır).
        if hb_xy and math.hypot(rota[-1][0] - hb_xy[0], rota[-1][1] - hb_xy[1]) > 2.0:
            rota.append((round(hb_xy[0], 2), round(hb_xy[1], 2)))
        (level_dir / "route.txt").write_text(
            "".join(f"{x} {y}\n" for x, y in rota), encoding="utf-8")
        # İHA→İKA JSON aktarımı: İHA'nın BAŞLANGIÇ REFERANS noktası (KB, dünya xy) +
        # rotanın hem dünya hem REFERANSA GÖRE yerel koordinatları (İKA yerel farkları
        # kendi konumuna ekleyerek sürer — gerçek sistemdeki comms.open_route içeriği).
        ref = kb_xy or (htab_cx, htab_cy - 23.0)
        (level_dir / "rota.json").write_text(json.dumps({
            "referans_xy": [round(ref[0], 2), round(ref[1], 2)],
            "acik_yol": det["label"], "yol_no": road, "guven": confidence,
            "hb_xy": [round(hb_xy[0], 2), round(hb_xy[1], 2)] if hb_xy else None,
            "rota_dunya": [[round(x, 2), round(y, 2)] for x, y in rota],
            "rota_yerel": [[round(x - ref[0], 2), round(y - ref[1], 2)] for x, y in rota],
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        det["rota"] = rota
        print(f"[İHA-HARİTA] MODEL KARARI: AÇIK YOL {det['label'].upper()} ({road}) "
              f"güven={confidence}  rota {len(rota)} nokta → route.txt + rota.json")
    else:
        det.update({"road": None, "label": "yok"})
        print("[İHA-HARİTA] GÜVENİLİR ROTA YOK (sağlamlık süzgeci geçilemedi) — "
              "rota yazılmadı, İKA hareket etmeyecek (fail-safe)")

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


def _tarama_irtifasi(meta, cli_scan_z=None):
    """Gerçek profil irtifasını kullan; yalnız eski kayıtlarda 30 m'ye dön."""
    if cli_scan_z is not None:
        return float(cli_scan_z)
    try:
        return float(meta.get("SCAN_ALTITUDE_M", DEFAULT_SCAN_Z))
    except (TypeError, ValueError):
        raise SystemExit("Geçersiz SCAN_ALTITUDE_M meta değeri")


def watch(vdir, levels, model_path, conf, kare_ofset, rot_isaret, bekle_sn=1800):
    """record.sh akışı: her seviyenin SCAN_DONE işaretini bekle → haritala → rota yaz.
    Konteyner route.txt'yi /tmp/navitas_route'a kopyalar, İKA sürmeye başlar."""
    from ultralytics import YOLO
    model = YOLO(str(model_path), task="segment")     # BİR KEZ yükle (seviyeler arası)
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
                       scan_z=_tarama_irtifasi(meta),
                       kare_ofset=kare_ofset, rot_isaret=rot_isaret,
                       kb_xy=_meta_xy(meta, "KB_XY"), hb_xy=_meta_xy(meta, "HB_XY"))
        _detections_birlestir(vdir, level, det)
    print("[İHA-HARİTA] izleme bitti.")


def main():
    ap = argparse.ArgumentParser(description="İHA tarama → ortomozaik → model → İKA rotası")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--watch", help="kayıt dizini (v<N>) — seviyeleri canlı bekle/işle")
    g.add_argument("--once", help="tek iha_scan_<seviye> klasörünü offline işle")
    ap.add_argument("--levels", default="kolay orta zor")
    ap.add_argument("--model", default=str(DEFAULT_MODEL))
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--htab", default=None, help="HTAB merkezi 'cx,cy' (--once + meta yoksa)")
    ap.add_argument("--scan-altitude", type=float, default=None,
                    help="tarama irtifası (vars. meta.txt SCAN_ALTITUDE_M; eski kayıtta 30 m)")
    ap.add_argument("--kare-ofset", type=int, default=0,
                    help="kare index → poz t kayması (kalibrasyon, vars. 0)")
    ap.add_argument("--rot-isaret", type=float, default=1.0, choices=[1.0, -1.0],
                    help="yaw→görüntü dönüş işareti (kalibrasyon, vars. +1)")
    ap.add_argument("--debug", action="store_true", help="kare yerleşimini satır satır bas")
    args = ap.parse_args()

    if args.watch:
        watch(args.watch, args.levels, args.model, args.conf,
              args.kare_ofset, args.rot_isaret)
        return

    from ultralytics import YOLO
    ldir = Path(args.once)
    meta = _meta_oku(ldir)
    cx, cy = _htab_merkez(meta, args.htab)
    model = YOLO(str(args.model), task="segment")
    det = haritala(ldir, model, cx, cy, conf=args.conf,
                   scan_z=_tarama_irtifasi(meta, args.scan_altitude),
                   kare_ofset=args.kare_ofset, rot_isaret=args.rot_isaret, debug=args.debug,
                   kb_xy=_meta_xy(meta, "KB_XY"), hb_xy=_meta_xy(meta, "HB_XY"))
    print(json.dumps(det, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
