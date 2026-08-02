"""
Navitas Toplu Test Scripti
Kullanim:
  python3 test_batch.py --all
  python3 test_batch.py --source roboflow
  python3 test_batch.py --source floodnet
  python3 test_batch.py --source rescuenet
"""

import argparse
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

from rpi_inference import _maskeleri_icerige_kirp, _preprocess

# ── Yollar ──────────────────────────────────────────────────────────────────
_root = Path(__file__).parent.parent

MODEL_DIR = next(
    (p for p in [
        _root / "models" / "best_ncnn_model",
        Path(__file__).parent / "best_ncnn_model",
    ] if p.exists()),
    _root / "models" / "best_ncnn_model",
)

TEST_SOURCES = {
    "roboflow":  _root / "test_images" / "roboflow",
    "floodnet":  Path("~/trs/github/navitas/FloodNet/FloodNet-Supervised_v1.0").expanduser(),
    "rescuenet": _root / "dataset" / "rescuenet_yolo" / "images" / "test",
}

RESULTS_DIR = Path(__file__).parent / "results"
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
INFER_SIZE = 512
CLASS_COLORS = {0: (0, 200, 0), 1: (0, 0, 200)}


# ── Model ────────────────────────────────────────────────────────────────────
def load_model():
    if not MODEL_DIR.exists():
        raise FileNotFoundError(f"Model bulunamadı: {MODEL_DIR}")
    print(f"Model yükleniyor: {MODEL_DIR}")
    return YOLO(str(MODEL_DIR), task="segment")


# ── Görsel toplama ───────────────────────────────────────────────────────────
def collect_images(source_name, source_path):
    images = {}

    if not source_path.exists():
        print(f"  UYARI: {source_name} yolu bulunamadı: {source_path}")
        return images

    if source_name == "floodnet":
        for split in ["train", "val", "test"]:
            org_dir = source_path / split / f"{split}-org-img"
            if org_dir.exists():
                files = [f for f in org_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXT]
                if files:
                    images[f"floodnet_{split}"] = sorted(files)

    elif source_name == "roboflow":
        for sub in sorted(source_path.iterdir()):
            if sub.is_dir():
                files = [f for f in sub.rglob("*") if f.suffix.lower() in SUPPORTED_EXT]
                if files:
                    images[f"roboflow_{sub.name}"] = sorted(files)

    elif source_name == "rescuenet":
        files = [f for f in source_path.rglob("*") if f.suffix.lower() in SUPPORTED_EXT]
        if files:
            images["rescuenet_test"] = sorted(files)

    return images


# ── Inference ─────────────────────────────────────────────────────────────────
def get_masks(results, h, w):
    masks = {0: np.zeros((h, w), np.uint8), 1: np.zeros((h, w), np.uint8)}
    r = results[0]
    if r.masks is None:
        return masks
    for i, cls in enumerate(r.boxes.cls):
        cid = int(cls)
        if cid not in masks:
            continue
        m = cv2.resize(r.masks.data[i].cpu().numpy(), (w, h))
        masks[cid] = np.maximum(masks[cid], (m > 0.5).astype(np.uint8))
    return masks


def draw_masks(img, masks):
    vis = img.copy()
    overlay = vis.copy()
    for cid, mask in masks.items():
        if mask.sum() == 0:
            continue
        overlay[mask > 0] = CLASS_COLORS.get(cid, (128, 128, 128))
    return cv2.addWeighted(vis, 0.5, overlay, 0.5, 0)


def run_inference(model, img_path, out_dir, conf=0.30):
    img = cv2.imread(str(img_path))
    if img is None:
        return None

    # Uretimle ayni letterbox akisi: sol/sag guzergahlar crop ile atilmaz.
    tuval, small, icerik = _preprocess(img)
    h, w = tuval.shape[:2]

    t0 = time.perf_counter()
    results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
    ms = (time.perf_counter() - t0) * 1000

    masks = _maskeleri_icerige_kirp(get_masks(results, h, w), icerik)
    vis = draw_masks(tuval, masks)

    # Dolgu, maske kirpmayla sifirlanir ama paydada yer alirsa oranlari yapay
    # olarak dusurur. Olcum yalniz gercek drone icerigi uzerinden yapilir.
    icerik_alan = icerik[2] * icerik[3]
    trav_pct = round(float(masks[0].sum()) / icerik_alan * 100, 2)
    blk_pct  = round(float(masks[1].sum()) / icerik_alan * 100, 2)
    detected = bool(trav_pct > 1 or blk_pct > 1)

    label = f"T:{trav_pct}%  B:{blk_pct}%  {ms:.0f}ms"
    cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    out_path = out_dir / f"{img_path.stem}_result.jpg"
    cv2.imwrite(str(out_path), vis)

    return {
        "file": img_path.name,
        "traversable_pct": trav_pct,
        "blocked_pct": blk_pct,
        "detected": detected,
        "ms": round(ms, 1),
    }


# ── Ana döngü ────────────────────────────────────────────────────────────────
def run_batch(sources, conf=0.30):
    model = load_model()

    run_id = datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nRun ID : {run_id}")
    print(f"Çıktı  : {run_dir}\n")

    summary = {"run_id": run_id, "sources": {}}
    total_images = 0
    total_detected = 0

    for source_name in sources:
        source_path = TEST_SOURCES.get(source_name)
        if not source_path:
            print(f"Bilinmeyen kaynak: {source_name}")
            continue

        groups = collect_images(source_name, source_path)
        if not groups:
            print(f"[{source_name}] Görsel bulunamadı")
            continue

        summary["sources"][source_name] = {}

        for group_name, files in groups.items():
            out_dir = run_dir / group_name
            out_dir.mkdir(exist_ok=True)

            print(f"[{group_name}] {len(files)} görsel işleniyor...")
            group_results = []

            for i, img_path in enumerate(files):
                result = run_inference(model, img_path, out_dir, conf)
                if result:
                    group_results.append(result)
                    total_images += 1
                    if result["detected"]:
                        total_detected += 1

                if (i + 1) % 50 == 0:
                    print(f"  {i+1}/{len(files)} tamamlandı")

            detected_count = sum(1 for r in group_results if r["detected"])
            avg_ms = round(sum(r["ms"] for r in group_results) / len(group_results), 1) if group_results else 0

            summary["sources"][source_name][group_name] = {
                "total": len(group_results),
                "detected": detected_count,
                "detection_rate": round(detected_count / len(group_results) * 100, 1) if group_results else 0,
                "avg_ms": avg_ms,
                "results": group_results,
            }

            print(f"  ✓ Tespit: {detected_count}/{len(group_results)}  Ort: {avg_ms}ms")

    summary["total_images"] = total_images
    summary["total_detected"] = total_detected
    summary["overall_detection_rate"] = round(total_detected / total_images * 100, 1) if total_images else 0

    summary_path = run_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n{'='*50}")
    print(f"TOPLAM  : {total_images} görsel")
    print(f"TESPİT  : {total_detected} ({summary['overall_detection_rate']}%)")
    print(f"ÖZET    : {summary_path}")
    print(f"{'='*50}")


# ── CLI ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Navitas Toplu Test")
    parser.add_argument("--all", action="store_true", help="Tüm kaynakları test et")
    parser.add_argument("--source", type=str, help="Belirli kaynak: roboflow, floodnet, rescuenet")
    parser.add_argument("--conf", type=float, default=0.30, help="Güven eşiği")
    args = parser.parse_args()

    if args.all:
        sources = list(TEST_SOURCES.keys())
    elif args.source:
        sources = [args.source]
    else:
        parser.print_help()
        return

    run_batch(sources, conf=args.conf)


if __name__ == "__main__":
    main()
