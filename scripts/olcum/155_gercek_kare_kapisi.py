"""155 — GERCEK KARE KAPISI (K8) · T195 · REVIEW_LOG D-332 SS5.

NEDEN VAR (bir kez PAHALIYA MAL OLDU):
  Kabul zinciri TAMAMEN SENTETIKTIR — denetci bunu her kosuda kendisi yazar
  ("Bu olcumlerin tamami SENTETIKTIR"). 2026-08-28'de bunun bedeli olculdu:
  v37 adayi K0'dan K7'ye ZINCIRIN TAMAMINI gecti (K1 258/260, K7 87/87 =
  %100,0, K2/K4/K6 hepsi v36'dan iyi) ve "URETIME ALINIR" verdikti aldi.
  Ama elimizdeki TEK gercekci karede zemin kaplamasi %4,4'ten %56,1'e ciktI
  ve uretim karar yolu `ZEMIN_MASKESI_SUPHELI` ile REDDETTI — yani model o
  karede HIC ROTA URETEMIYORDU.

  Bunu yakalayan tek sey `tests/test_gercek_arena_kapisi.py` idi (T59/D-84)
  ve o ZINCIRIN ICINDE DEGILDI. Yani zincirden gecen bir model, suit
  kosulmasaydi sessizce terfi edebilirdi.

BU KAPI YENI BIR ESIK UYDURMAZ. Uretim yolunda ZATEN VAR OLAN zemin
saglamlik kapisini (`karar_sozlesmesi.zemin_maskesi_reddi`) gercek kare
uzerinde kosar ve sonucu zincire tasir. Olcut: uretim karar yolu bu karede
`ZEMIN_MASKESI_SUPHELI` DONDURMEMELIDIR.

⚠ NE IDDIA ETMEZ: bu kare, sartnamenin kendi ifadesiyle "tamamen yapay zeka
ile olusturulmustur, gercek alani dogrudan yansitmamaktadir" (D-99). Bu kapi
"model sahada calisir" DEMEZ. Yalnizca sunu der: elimizdeki tek gercekci
karede uretim yolu KIRILMIYOR. n = 1'dir ve bu ACIKCA yazilidir (D-186 bu
figur uzerinde MODEL TAVANI koymayi zaten reddetmisti — burada tavan yok,
yalnizca "kirilmasin" sarti var).

Kullanim:
  <venv> 155_gercek_kare_kapisi.py --agirlik models/navitas_seg_v36_best.pt \
                                   --json results/t63/x_k8.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

import cv2                                                          # noqa: E402

from karar_sozlesmesi import (ZEMIN_MASKESI_SUPHELI_SEBEBI,         # noqa: E402
                              zemin_kaplamasi, zemin_kenar_dayanmasi,
                              zemin_maskesi_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,     # noqa: E402
                           _preprocess, analyze_path, get_masks)

KARE = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"


def olc(agirlik: Path) -> dict:
    """Uretim cagri sirasiyla gercek kareyi kos. OLCULEMEDI != GECTI."""
    if not KARE.is_file():
        return {"durum": "OLCULEMEDI", "sebep": f"gercek kare yok: {KARE}"}
    im = cv2.imread(str(KARE))
    if im is None:
        return {"durum": "OLCULEMEDI", "sebep": "kare okunamadi"}
    if not Path(agirlik).is_file():
        return {"durum": "OLCULEMEDI", "sebep": f"agirlik yok: {agirlik}"}

    from ultralytics import YOLO
    model = YOLO(str(agirlik), task="segment")
    sq, small, icerik = _preprocess(im)
    res = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
    maskeler = _maskeleri_icerige_kirp(
        get_masks(res, sq.shape[0], sq.shape[1]), icerik)
    zemin = maskeler[0]

    kaplama = float(zemin_kaplamasi(zemin, icerik))
    kenar = float(zemin_kenar_dayanmasi(zemin, icerik))
    zemin_red = zemin_maskesi_reddi(zemin, icerik)

    # Karar yolunun KENDISI de sinanir: kapi `analyze_path` icinden de susmali.
    _yol, _guven, _wps, karar_reddi = analyze_path(
        zemin, icerik=icerik, engel_mask=maskeler.get(1),
        mpp=50.0 / im.shape[1], return_reason=True)
    karar_kodu = (karar_reddi[0] if isinstance(karar_reddi, (tuple, list))
                  else karar_reddi)

    suphe = (zemin_red is not None
             and (zemin_red[0] if isinstance(zemin_red, (tuple, list))
                  else zemin_red) == ZEMIN_MASKESI_SUPHELI_SEBEBI)
    suphe = suphe or (karar_kodu == ZEMIN_MASKESI_SUPHELI_SEBEBI)

    return {
        "durum": "DUSTU" if suphe else "GECTI",
        "kare": str(KARE.relative_to(KOK)).replace("\\", "/"),
        "zemin_kaplamasi": round(kaplama, 4),
        "zemin_kenar_dayanmasi": round(kenar, 4),
        "zemin_kapisi": (zemin_red[0] if isinstance(zemin_red, (tuple, list))
                         else zemin_red),
        "karar_yolu_reddi": karar_kodu,
        "_olcut": ("uretim karar yolu bu karede ZEMIN_MASKESI_SUPHELI "
                   "DONDURMEMELIDIR (yeni esik YOK; uretimde zaten var olan "
                   "zemin saglamlik kapisi kosuluyor)"),
        "_n": 1,
        "_uyari": ("n = 1 ve bu kare sartnamenin kendi ifadesiyle YAPAY ZEKA "
                   "urunudur (D-99). Bu kapi 'sahada calisir' DEMEZ; yalnizca "
                   "'elimizdeki tek gercekci karede uretim yolu KIRILMIYOR' der."),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--agirlik", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    a = ap.parse_args()

    d = olc(a.agirlik)
    print(f"K8 · GERCEK KARE: {d['durum']}")
    if d["durum"] == "OLCULEMEDI":
        print(f"   sebep: {d['sebep']}")
    else:
        print(f"   zemin kaplamasi {d['zemin_kaplamasi']:.4f} · "
              f"kenar {d['zemin_kenar_dayanmasi']:.4f}")
        print(f"   zemin kapisi: {d['zemin_kapisi']} · "
              f"karar yolu: {d['karar_yolu_reddi']}")
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(d, indent=1, ensure_ascii=False),
                          encoding="utf-8")
        print(f"json -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
