"""
Navitas — Model Doğruluk Testi
Kullanim:
  python3 test_accuracy.py --images test_images/
  python3 test_accuracy.py --images test_images/ --conf 0.25

Görsel isimlendirme: P001.jpg, P002.jpg, ... P030.jpg
Label dosyasi     : dataset/test_labels.json (otomatik bulunur)
"""

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

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
LABELS_FILE = _here.parent / "dataset" / "test_labels.json"
RESULTS_DIR = _here / "test_results"
INFER_SIZE = 512
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}


def load_model():
    if not MODEL_DIR.exists():
        print(f"HATA: Model bulunamadi: {MODEL_DIR}")
        sys.exit(1)
    return YOLO(str(MODEL_DIR), task="segment")


def get_masks(results, h, w):
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


def predict_open_road(trav_mask):
    h, w = trav_mask.shape
    k1 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    k2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(7, w // 30), max(7, h // 30)))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN, k1)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k2)

    if clean.sum() == 0:
        return None, 0.0

    top = clean[:int(h * 0.4), :]
    thirds = [
        int(top[:, :w // 3].sum()),
        int(top[:, w // 3:2 * w // 3].sum()),
        int(top[:, 2 * w // 3:].sum()),
    ]
    total = sum(thirds)
    if total == 0:
        all_t = [int(clean[:, :w//3].sum()), int(clean[:, w//3:2*w//3].sum()), int(clean[:, 2*w//3:].sum())]
        total = sum(all_t)
        thirds = all_t

    if total == 0:
        return None, 0.0

    pred = int(np.argmax(thirds)) + 1
    conf = round(thirds[pred - 1] / total, 3)
    return pred, conf


def run_test(model, images_dir, conf_thresh):
    images_dir = Path(images_dir)
    if not images_dir.exists():
        print(f"HATA: Klasor bulunamadi: {images_dir}")
        sys.exit(1)

    if not LABELS_FILE.exists():
        print(f"HATA: Label dosyasi bulunamadi: {LABELS_FILE}")
        sys.exit(1)

    with open(LABELS_FILE) as f:
        labels = json.load(f)

    RESULTS_DIR.mkdir(exist_ok=True)

    files = sorted(f for f in images_dir.iterdir() if f.suffix.lower() in SUPPORTED_EXT)
    if not files:
        print(f"Klasorde gorsel bulunamadi: {images_dir}")
        return

    results_log = []
    correct_total = 0
    correct_easy = 0
    correct_tricky = 0
    count_easy = 0
    count_tricky = 0

    print(f"\n{'ID':6} {'TÜR':8} {'BEKLENEN':10} {'TAHMİN':10} {'GÜVEN':8} {'SONUÇ':8} {'HİLE'}")
    print("-" * 75)

    for img_path in files:
        prompt_id = img_path.stem.upper()
        if prompt_id not in labels:
            print(f"{prompt_id:6}  label yok — atlandi")
            continue

        label = labels[prompt_id]
        expected = label["open_road"]
        img_type = label["type"]
        trick = label.get("trick") or "-"

        img = cv2.imread(str(img_path))
        if img is None:
            print(f"{prompt_id:6}  okunamadi")
            continue

        h, w = img.shape[:2]
        side = min(h, w)
        y0, x0 = (h - side) // 2, (w - side) // 2
        sq = img[y0:y0 + side, x0:x0 + side]
        small = cv2.resize(sq, (INFER_SIZE, INFER_SIZE))

        res = model.predict(small, imgsz=INFER_SIZE, conf=conf_thresh, verbose=False)
        masks = get_masks(res, side, side)
        pred, conf = predict_open_road(masks[0])

        is_correct = pred == expected
        symbol = "✓" if is_correct else "✗"

        if img_type == "correct":
            count_easy += 1
            if is_correct:
                correct_easy += 1
                correct_total += 1
        else:
            count_tricky += 1
            if is_correct:
                correct_tricky += 1
                correct_total += 1

        pred_str = str(pred) if pred else "?"
        print(f"{prompt_id:6} {img_type:8} {expected:<10} {pred_str:<10} {conf:<8.2f} {symbol:<8} {trick}")

        results_log.append({
            "id": prompt_id,
            "type": img_type,
            "expected": expected,
            "predicted": pred,
            "confidence": conf,
            "correct": is_correct,
            "trick": trick,
        })

    total = len(results_log)
    if total == 0:
        print("Sonuc yok.")
        return

    print("\n" + "=" * 75)
    print(f"GENEL DOĞRULUK   : {correct_total}/{total}  ({100*correct_total/total:.1f}%)")
    if count_easy > 0:
        print(f"KOLAY (correct)  : {correct_easy}/{count_easy}  ({100*correct_easy/count_easy:.1f}%)")
    if count_tricky > 0:
        print(f"KANDIRMACA(tricky): {correct_tricky}/{count_tricky}  ({100*correct_tricky/count_tricky:.1f}%)")

    # Hile tipine göre breakdown
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
        print("\nHİLE TIPI BAZINDA:")
        for trick, (ok, tot) in sorted(trick_stats.items()):
            bar = "█" * ok + "░" * (tot - ok)
            print(f"  {trick:30s} {bar} {ok}/{tot}")

    # Sonuçları kaydet
    out_json = RESULTS_DIR / "accuracy_results.json"
    with open(out_json, "w") as f:
        json.dump({
            "total": total,
            "correct": correct_total,
            "accuracy": round(correct_total / total, 3),
            "easy_accuracy": round(correct_easy / count_easy, 3) if count_easy else None,
            "tricky_accuracy": round(correct_tricky / count_tricky, 3) if count_tricky else None,
            "details": results_log,
        }, f, indent=2, ensure_ascii=False)
    print(f"\nDetaylar kaydedildi: {out_json}")


def main():
    parser = argparse.ArgumentParser(description="Navitas Model Dogruluk Testi")
    parser.add_argument("--images", required=True, help="Test gorsellerinin klasoru")
    parser.add_argument("--conf", type=float, default=0.30, help="Guven esigi (varsayilan: 0.30)")
    args = parser.parse_args()

    model = load_model()
    run_test(model, args.images, args.conf)


if __name__ == "__main__":
    main()
