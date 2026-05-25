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


def get_masks(results, h, w):
    """Her sinif icin (h, w) cozunurlugunde binary mask doner."""
    masks = {0: np.zeros((h, w), dtype=np.uint8),
             1: np.zeros((h, w), dtype=np.uint8)}
    r = results[0]
    if r.masks is None:
        return masks
    for i, cls in enumerate(r.boxes.cls):
        cls_id = int(cls)
        if cls_id not in masks:
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


def analyze_path(trav_mask, n_waypoints=8):
    """
    Algoritma:
      1. Morfolojik temizleme (gurultu, kucuk blob)
      2. Distance transform → centerline (medial axis approximation)
      3. Yatay bantlarda alt→ust waypoint ornekleme
      4. Ust %40'a bakarak hangi ucte birden cikildigi → open_path

    Returns:
      open_path  : 1=sol, 2=orta, 3=sag (None = tespit yok)
      confidence : acik yol piksel orani (0.0-1.0)
      waypoints  : [(x, y), ...] alt→ust sirali, goruntu koordinatlari
    """
    h, w = trav_mask.shape

    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)

    if clean.sum() == 0:
        return None, 0.0, []

    # Ust %40: cikmak istenen yonu belirle
    top = clean[:int(h * 0.4), :]
    thirds = [
        int(top[:, :w // 3].sum()),
        int(top[:, w // 3:2 * w // 3].sum()),
        int(top[:, 2 * w // 3:].sum()),
    ]
    total_top = sum(thirds)

    if total_top == 0:
        thirds = [
            int(clean[:, :w // 3].sum()),
            int(clean[:, w // 3:2 * w // 3].sum()),
            int(clean[:, 2 * w // 3:].sum()),
        ]
        total_top = sum(thirds)

    open_path = int(np.argmax(thirds)) + 1
    confidence = round(thirds[open_path - 1] / total_top, 3) if total_top > 0 else 0.0

    # Distance transform centerline
    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)

    waypoints = []
    for i in range(n_waypoints - 1, -1, -1):  # alt → ust
        y0 = i * h // n_waypoints
        y1 = (i + 1) * h // n_waypoints
        band = dist[y0:y1, :]
        if band.max() > 0.5:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            waypoints.append((int(lx), int(y0 + ly)))

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


def _preprocess(img):
    """Merkezi kare crop. (orijinal_kare, 512x512_infer) doner."""
    h, w = img.shape[:2]
    side = min(h, w)
    y0, x0 = (h - side) // 2, (w - side) // 2
    sq = img[y0:y0 + side, x0:x0 + side]
    small = cv2.resize(sq, (INFER_SIZE, INFER_SIZE))
    return sq, small


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

        sq, small = _preprocess(img)
        orig_h, orig_w = sq.shape[:2]

        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        masks = get_masks(results, orig_h, orig_w)

        open_path, path_conf, waypoints = analyze_path(masks[0])
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
    side = min(src_w, src_h)

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
        sq, small = _preprocess(frame)
        orig_h, orig_w = sq.shape[:2]

        t0 = time.perf_counter()
        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        masks = get_masks(results, orig_h, orig_w)
        open_path, path_conf, waypoints = analyze_path(masks[0])
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
        sq, small = _preprocess(frame)
        orig_h, orig_w = sq.shape[:2]

        t0 = time.perf_counter()
        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        masks = get_masks(results, orig_h, orig_w)
        open_path, path_conf, waypoints = analyze_path(masks[0])
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
