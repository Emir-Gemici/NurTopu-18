"""
Navitas — Gorsel Test & Dogruluk
Kullanim:
  # Dogruluk testi — P001..P030 gorsel + etiket karsilastirma + gorsel cikti
  python3 test_accuracy.py --test test_images/ [--conf 0.30]

  # Gorsel inference — dogruluk karsilastirmasi yok
  python3 test_accuracy.py --image resim.jpg
  python3 test_accuracy.py --image gorseller/
  python3 test_accuracy.py --video video.mp4 [--no-save]
  python3 test_accuracy.py --camera

Cikti:
  test_results/<ad>_result.jpg   — annotated gorsel (orijinal cozunurluk)
  test_results/<ad>_ika_map.jpg  — IKA rota haritasi + koordinatlar
  test_results/accuracy_results.json — (sadece --test modunda)
"""

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from rpi_inference import _maskeleri_icerige_kirp, _preprocess

_here = Path(__file__).parent
MODEL_DIR = next(
    (p for p in [
        _here / "rescuenet_seg_v1_ncnn_model",
        _here.parent / "models" / "rescuenet_seg_v1_ncnn_model",
        _here / "rescuenet_seg_v1_ncnn",
        _here.parent / "models" / "rescuenet_seg_v1_ncnn",
    ] if p.exists()),
    _here / "rescuenet_seg_v1_ncnn_model",
)
LABELS_FILE = next(
    (p for p in [
        _here.parent / "dataset" / "test_labels.json",
        _here / "test_labels.json",
    ] if p.exists()),
    _here.parent / "dataset" / "test_labels.json",
)
RESULTS_DIR = _here / "test_results"
INFER_SIZE = 512
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

CLASS_COLORS = {
    0: (0, 200, 0),   # traversable — yesil
    1: (0, 0, 200),   # blocked     — kirmizi
}


# ─── Model ──────────────────────────────────────────────────────────────────

def load_model(model_dir=None):
    model_dir = Path(model_dir) if model_dir else MODEL_DIR
    if not model_dir.exists():
        print(f"HATA: Model bulunamadi: {model_dir}")
        print("rescuenet_seg_v1_ncnn_model/ klasorunu ayni dizine veya models/ altina koy.")
        sys.exit(1)
    print(f"Model yukleniyor: {model_dir}")
    return YOLO(str(model_dir), task="segment")


# ─── Inference Temel Fonksiyonlari ──────────────────────────────────────────

def get_masks(results, h, w):
    """Her sinif icin (h, w) boyutunda binary mask doner."""
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


def analyze_path(trav_mask, n_waypoints=8):
    """
    Traversable maskinden:
      - open_path  : 1=sol  2=orta  3=sag  (None=tespit yok)
      - confidence : [0,1]
      - waypoints  : [(x,y), ...] alt→ust, goruntu koordinatlari
    """
    h, w = trav_mask.shape

    k_open  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN,  k_open)
    clean = cv2.morphologyEx(clean,     cv2.MORPH_CLOSE, k_close)

    if clean.sum() == 0:
        return None, 0.0, []

    top = clean[:int(h * 0.4), :]
    thirds = [
        int(top[:, :w // 3].sum()),
        int(top[:, w // 3:2 * w // 3].sum()),
        int(top[:, 2 * w // 3:].sum()),
    ]
    total = sum(thirds)
    if total == 0:
        thirds = [
            int(clean[:, :w // 3].sum()),
            int(clean[:, w // 3:2 * w // 3].sum()),
            int(clean[:, 2 * w // 3:].sum()),
        ]
        total = sum(thirds)

    if total == 0:
        return None, 0.0, []

    open_path  = int(np.argmax(thirds)) + 1
    confidence = round(thirds[open_path - 1] / total, 3)

    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)
    waypoints = []
    for i in range(n_waypoints - 1, -1, -1):
        y0 = i * h // n_waypoints
        y1 = (i + 1) * h // n_waypoints
        band = dist[y0:y1, :]
        if band.max() > 0.5:
            ly, lx = np.unravel_index(band.argmax(), band.shape)
            waypoints.append((int(lx), int(y0 + ly)))

    return open_path, confidence, waypoints


# ─── Gorsel Cizim ───────────────────────────────────────────────────────────

def draw_masks(image_bgr, masks):
    """Traversable=yesil, blocked=kirmizi overlay."""
    vis = image_bgr.copy()
    overlay = vis.copy()
    for cls_id, mask in masks.items():
        if mask.sum() == 0:
            continue
        color = CLASS_COLORS.get(cls_id, (128, 128, 128))
        overlay[mask > 0] = color
    return cv2.addWeighted(vis, 0.5, overlay, 0.5, 0)


def draw_waypoints(vis, waypoints):
    """Centerline + hedef noktasi."""
    if not waypoints:
        return vis
    for j in range(len(waypoints) - 1):
        cv2.line(vis, waypoints[j], waypoints[j + 1], (0, 255, 255), 2)
    for wp in waypoints[:-1]:
        cv2.circle(vis, wp, 4, (0, 255, 255), -1)
    cv2.circle(vis, waypoints[-1], 9, (0, 255, 255), -1)
    cv2.circle(vis, waypoints[-1], 12, (0, 0, 0), 2)
    return vis


def generate_ika_map(waypoints, open_path, confidence, src_h, src_w, map_size=512):
    """IKA icin navigasyon haritasi — centerline, waypoint koordinatlari, hedef."""
    canvas = np.full((map_size, map_size, 3), 22, dtype=np.uint8)

    step = map_size // 8
    for i in range(0, map_size + 1, step):
        cv2.line(canvas, (i, 0), (i, map_size), (42, 42, 42), 1)
        cv2.line(canvas, (0, i), (map_size, i), (42, 42, 42), 1)

    for x in [map_size // 3, 2 * map_size // 3]:
        cv2.line(canvas, (x, 0), (x, map_size), (60, 60, 60), 1)
    for j, label in enumerate(["SOL", "ORTA", "SAG"]):
        lx    = j * map_size // 3 + map_size // 12
        color = (0, 220, 0) if (j + 1 == open_path) else (60, 60, 60)
        cv2.putText(canvas, label, (lx, map_size - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)

    start = (map_size // 2, map_size - 20)
    cv2.circle(canvas, start, 7, (0, 200, 255), -1)
    cv2.putText(canvas, "IKA", (start[0] + 10, start[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)

    if waypoints:
        sx = map_size / src_w
        sy = map_size / src_h
        scaled = [(int(x * sx), int(y * sy)) for x, y in waypoints]

        pts = np.array(scaled, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts], False, (0, 210, 0), 3)

        for j, ((px, py), (ox, oy)) in enumerate(zip(scaled, waypoints)):
            cv2.circle(canvas, (px, py), 4, (80, 255, 80), -1)
            if j % 2 == 0:
                cv2.putText(canvas, f"({ox},{oy})", (px + 5, py - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.26, (150, 150, 150), 1)

        tx, ty = scaled[-1]
        cv2.circle(canvas, (tx, ty), 10, (0, 255, 255), 2)
        cv2.circle(canvas, (tx, ty), 4,  (0, 255, 255), -1)
        cv2.putText(canvas, "HEDEF", (tx + 12, ty + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 255), 1)

        if len(scaled) >= 2:
            cv2.arrowedLine(canvas, scaled[-2], scaled[-1],
                            (0, 255, 120), 2, tipLength=0.4)

        cv2.line(canvas, start, scaled[0], (80, 80, 200), 1)

    direction = {1: "SOL", 2: "ORTA", 3: "SAG"}.get(open_path, "?")
    cv2.putText(canvas, f"ACIK YOL: {open_path} ({direction})  GUVEN: {confidence:.2f}",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(canvas, f"WP: {len(waypoints)}  KAYNAK: {src_w}x{src_h}px",
                (8, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.37, (140, 140, 140), 1)

    return canvas


def _infer_frame(model, img, conf):
    """
    Tek kare icin tam pipeline.
    Returns: (vis, ika_map_or_None, open_path, path_conf, waypoints, orig_h, orig_w)
    """
    # Uretim hatti ile birebir ayni: merkez crop yok, tam goruntu letterbox
    # ile kare tuvale konur ve dolgu bolgesindeki maskeler sonradan temizlenir.
    tuval, small, icerik = _preprocess(img)
    orig_h, orig_w = tuval.shape[:2]

    results    = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
    masks      = _maskeleri_icerige_kirp(get_masks(results, orig_h, orig_w), icerik)
    open_path, path_conf, waypoints = analyze_path(masks[0])

    vis = draw_masks(tuval, masks)

    direction = {1: "SOL", 2: "ORTA", 3: "SAG"}.get(open_path, "?")
    if open_path:
        vis = draw_waypoints(vis, waypoints)
        label  = f"YOL: {open_path} ({direction})  guven: {path_conf:.2f}"
        ika_map = generate_ika_map(waypoints, open_path, path_conf, orig_h, orig_w)
    else:
        label   = "TESPIT YOK"
        ika_map = None

    cv2.putText(vis, label, (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    cv2.putText(vis, f"{orig_w}x{orig_h}px", (10, orig_h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    return vis, ika_map, open_path, path_conf, waypoints, orig_h, orig_w


def _save_pair(stem, vis, ika_map, out_dir):
    """_result.jpg ve (varsa) _ika_map.jpg kaydet."""
    out_dir.mkdir(parents=True, exist_ok=True)
    res_path = out_dir / f"{stem}_result.jpg"
    cv2.imwrite(str(res_path), vis)
    if ika_map is not None:
        map_path = out_dir / f"{stem}_ika_map.jpg"
        cv2.imwrite(str(map_path), ika_map)
        return res_path, map_path
    return res_path, None


# ─── Modlar ─────────────────────────────────────────────────────────────────

def run_image(model, path_str, conf):
    path = Path(path_str)
    if path.is_dir():
        files = sorted(f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXT)
        if not files:
            print(f"HATA: Klasorde gorsel bulunamadi: {path}")
            return
        print(f"{len(files)} gorsel islenecek -> {RESULTS_DIR}/")
    elif path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXT:
            print(f"HATA: Desteklenmeyen format: {path.suffix}")
            return
        files = [path]
    else:
        print(f"HATA: Dosya/klasor bulunamadi: {path}")
        return

    for img_path in files:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"  okunamadi: {img_path.name}")
            continue

        vis, ika_map, open_path, path_conf, waypoints, oh, ow = _infer_frame(model, img, conf)
        res_path, map_path = _save_pair(img_path.stem, vis, ika_map, RESULTS_DIR)

        direction = {1: "SOL", 2: "ORTA", 3: "SAG"}.get(open_path, "?")
        status = f"yol={open_path}({direction}) guven={path_conf:.2f}" if open_path else "tespit yok"
        print(f"  {img_path.name:30s}  {ow}x{oh}  {status}")
        print(f"    -> {res_path.name}")
        if map_path:
            print(f"    -> {map_path.name}  wp:{len(waypoints)}")
            ika_data = {"open_path": open_path, "confidence": path_conf,
                        "waypoints": waypoints, "timestamp": int(time.time())}
            print(f"    payload: {json.dumps(ika_data)}")


def run_video(model, path_str, conf, save=True):
    path = Path(path_str)
    if not path.is_file():
        print(f"HATA: Dosya bulunamadi: {path}")
        return
    if path.suffix.lower() not in SUPPORTED_VIDEO_EXT:
        print(f"HATA: Desteklenmeyen format: {path.suffix}")
        return

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"HATA: Video acilamadi: {path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps  = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w    = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h    = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    yan      = max(src_w, src_h)

    writer = None
    out_path = None
    if save:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        out_path = RESULTS_DIR / f"{path.stem}_result.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, src_fps, (yan, yan))

    print(f"Video: {path.name}  {src_w}x{src_h}  {src_fps:.1f}fps  {total_frames} kare")
    if save:
        print(f"Cikti: {out_path}")

    fps_buf   = []
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1

        t0 = time.perf_counter()
        vis, ika_map, open_path, path_conf, waypoints, oh, ow = _infer_frame(model, frame, conf)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
        progress = f"{frame_idx}/{total_frames}" if total_frames > 0 else str(frame_idx)
        cv2.putText(vis, f"FPS: {live_fps:.1f}  Kare: {progress}  {ow}x{oh}px",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        if writer:
            writer.write(vis)

        cv2.imshow("Navitas — Video", vis)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("Durduruldu.")
            break

    cap.release()
    if writer:
        writer.release()
    cv2.destroyAllWindows()

    avg_fps = 1.0 / (sum(fps_buf) / len(fps_buf)) if fps_buf else 0
    print(f"\n{frame_idx} kare islendi — ortalama {avg_fps:.1f} FPS")
    if save and out_path:
        print(f"Kaydedildi: {out_path}")


def run_camera(model, conf):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("HATA: Kamera acilamadi.")
        return

    print("Kamera acik — cikmak icin 'q'")
    fps_buf = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        t0 = time.perf_counter()
        vis, _, open_path, path_conf, _, oh, ow = _infer_frame(model, frame, conf)
        fps_buf.append(time.perf_counter() - t0)
        if len(fps_buf) > 30:
            fps_buf.pop(0)

        live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
        cv2.putText(vis, f"FPS: {live_fps:.1f}  {ow}x{oh}px",
                    (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        cv2.imshow("Navitas — Kamera", vis)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def run_test(model, images_dir, conf, labels_file=None):
    """Dogruluk testi: P001-P030 gorsel + etiket karsilastirma + gorsel cikti."""
    images_dir = Path(images_dir)
    if not images_dir.exists():
        print(f"HATA: Klasor bulunamadi: {images_dir}")
        sys.exit(1)

    labels_file = Path(labels_file) if labels_file else LABELS_FILE
    if not labels_file.exists():
        print(f"HATA: Label dosyasi bulunamadi: {labels_file}")
        sys.exit(1)

    with open(labels_file) as f:
        labels = json.load(f)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    files = sorted(f for f in images_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXT)
    if not files:
        print(f"HATA: Klasorde gorsel bulunamadi: {images_dir}")
        return

    results_log     = []
    correct_total   = 0
    correct_easy    = 0
    correct_tricky  = 0
    count_easy      = 0
    count_tricky    = 0

    print(f"\n{'ID':6} {'TUR':8} {'BEKLENEN':10} {'TAHMIN':10} {'GUVEN':8} {'SONUC':6} {'BOYUT':12} {'HILE'}")
    print("-" * 85)

    for img_path in files:
        prompt_id = img_path.stem.upper()
        if prompt_id not in labels:
            print(f"{prompt_id:6}  label yok — atlandi")
            continue

        label    = labels[prompt_id]
        expected = label["open_road"]
        img_type = label["type"]
        trick    = label.get("trick") or "-"

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"{prompt_id:6}  okunamadi: {img_path.name}")
            continue

        vis, ika_map, open_path, path_conf, waypoints, oh, ow = _infer_frame(model, img, conf)
        res_path, map_path = _save_pair(prompt_id.lower(), vis, ika_map, RESULTS_DIR)

        is_correct = (open_path == expected)
        symbol     = "✓" if is_correct else "✗"

        if img_type == "correct":
            count_easy += 1
            if is_correct:
                correct_easy  += 1
                correct_total += 1
        else:
            count_tricky += 1
            if is_correct:
                correct_tricky += 1
                correct_total  += 1

        pred_str = str(open_path) if open_path else "?"
        dim_str  = f"{ow}x{oh}"
        print(f"{prompt_id:6} {img_type:8} {expected:<10} {pred_str:<10} {path_conf:<8.2f} {symbol:<6} {dim_str:<12} {trick}")

    total = len(results_log) if results_log else (correct_easy + correct_tricky +
            (count_easy - correct_easy) + (count_tricky - correct_tricky))
    total = count_easy + count_tricky

    if total == 0:
        print("Sonuc yok.")
        return

    print("\n" + "=" * 85)
    print(f"GENEL DOGRULUK    : {correct_total}/{total}  ({100 * correct_total / total:.1f}%)")
    if count_easy:
        print(f"KOLAY  (correct)  : {correct_easy}/{count_easy}  ({100 * correct_easy / count_easy:.1f}%)")
    if count_tricky:
        print(f"KANDIRMACA(tricky): {correct_tricky}/{count_tricky}  ({100 * correct_tricky / count_tricky:.1f}%)")
    print(f"\nGorsel ciktilar   : {RESULTS_DIR}/")

    # Hile tipine gore breakdown
    for img_path in files:
        prompt_id = img_path.stem.upper()
        if prompt_id not in labels:
            continue
        label      = labels[prompt_id]
        img        = cv2.imread(str(img_path))
        if img is None:
            continue
        _, _, open_path, path_conf, waypoints, oh, ow = _infer_frame(model, img, conf)
        is_correct = (open_path == labels[prompt_id]["open_road"])
        results_log.append({
            "id": prompt_id, "type": label["type"],
            "expected": label["open_road"], "predicted": open_path,
            "confidence": path_conf, "correct": is_correct,
            "trick": label.get("trick") or "-",
            "resolution": f"{ow}x{oh}",
        })

    trick_stats: dict = {}
    for r in results_log:
        if r["type"] == "tricky":
            t = r["trick"]
            if t not in trick_stats:
                trick_stats[t] = [0, 0]
            trick_stats[t][1] += 1
            if r["correct"]:
                trick_stats[t][0] += 1

    if trick_stats:
        print("\nHILE TIPI BAZINDA:")
        for trick, (ok, tot) in sorted(trick_stats.items()):
            bar = "█" * ok + "░" * (tot - ok)
            print(f"  {trick:30s} {bar} {ok}/{tot}")

    out_json = RESULTS_DIR / "accuracy_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "total": total,
            "correct": correct_total,
            "accuracy": round(correct_total / total, 3) if total else 0,
            "easy_accuracy": round(correct_easy / count_easy, 3) if count_easy else None,
            "tricky_accuracy": round(correct_tricky / count_tricky, 3) if count_tricky else None,
            "details": results_log,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetaylar kaydedildi: {out_json}")


# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Navitas Gorsel Test & Dogruluk")
    grp = parser.add_mutually_exclusive_group(required=True)
    grp.add_argument("--test",   metavar="DIR",  help="Dogruluk testi — P001-P030 gorsel klasoru")
    grp.add_argument("--image",  metavar="PATH", help="Gorsel dosya veya klasor")
    grp.add_argument("--video",  metavar="FILE", help="Video dosyasi")
    grp.add_argument("--camera", action="store_true", help="Canli kamera")
    parser.add_argument("--conf",    type=float, default=0.30, help="Guven esigi (varsayilan: 0.30)")
    parser.add_argument("--no-save", action="store_true",      help="Video modunda kaydetme")
    parser.add_argument("--model",   metavar="PATH", help="Model yolu (.pt veya ncnn klasoru). Varsayilan: models/rescuenet_seg_v1")
    parser.add_argument("--labels",  metavar="JSON", help="Etiket dosyasi (--test ile). Varsayilan: dataset/test_labels.json")
    args = parser.parse_args()

    model = load_model(args.model)

    if args.test:
        run_test(model, args.test, args.conf, args.labels)
    elif args.image:
        run_image(model, args.image, args.conf)
    elif args.video:
        run_video(model, args.video, args.conf, save=not args.no_save)
    elif args.camera:
        run_camera(model, args.conf)


if __name__ == "__main__":
    main()
