"""
İHA algısı (TÜM seviyeler) — GERÇEK model (best.pt) ile her seviyenin aerial
görselinde açık yolu tespit eder, detections.json'a yazar. record.sh host'ta
(.venv) bunu çağırır; container bu tespitleri kullanır (sim modelin kararını izler).

IHA_VIEW: İHA'nın her seviyede gördüğü görsel. Kendi sol/orta/sag üretilmiş
görsellerinle DEĞİŞTİR (model onları okuyup karar verecek).

Kullanım (.venv ile):
  .venv/bin/python simulation/scripts/iha_perceive_all.py --levels "kolay orta zor" --out det.json
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from iha_perceive import perceive, LABEL

# İHA'nın her seviyede gördüğü aerial görsel (← kendi görsellerinle değiştir)
IHA_VIEW = {
    "kolay": ROOT / "test_images" / "gemini" / "3.png",
    "orta":  ROOT / "test_images" / "gemini" / "4.png",
    "zor":   ROOT / "test_images" / "gemini" / "6.png",
}


def main():
    ap = argparse.ArgumentParser(description="İHA algısı — tüm seviyeler (gerçek model)")
    ap.add_argument("--levels", default="kolay orta zor")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    det = {}
    for lv in args.levels.split():
        img = IHA_VIEW.get(lv)
        try:
            road, conf, trav = perceive(img)
        except Exception as e:
            print(f"[İHA-ALGI] {lv}: HATA {e}", file=sys.stderr)
            road, conf, trav = None, 0.0, 0
        det[lv] = {"road": road, "label": LABEL.get(road, "yok"),
                   "conf": conf, "image": Path(img).name if img else None}
        name = Path(img).name if img else "?"
        print(f"[İHA-ALGI] {lv}: {name} → {LABEL.get(road, 'YOK').upper()} "
              f"(yol {road}, güven {conf})  [GERÇEK best.pt]")

    Path(args.out).write_text(json.dumps(det, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[İHA-ALGI] tespitler yazıldı: {args.out}")


if __name__ == "__main__":
    main()
