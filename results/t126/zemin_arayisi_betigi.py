"""K5 icin OLCULEBILIR ZEMIN arayisi: bariyer benzeri yapi hangi kumede var?

63_bariyer_kesisimi.py bariyeri MODELSIZ bulur (LAB a* > 25, yuksek kromali
kirmizi). Ayni dedektoru kumelerde kosarak "bariyerli kare" sayisini olceriz.
Ayrica o karelerde URETIM zinciri rota uretiyor mu (K5'in olculebilmesi icin
SART) bakilir.
"""
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
sys.path.insert(0, str(KOK / "scripts" / "olcum"))

import importlib.util
spec = importlib.util.spec_from_file_location(
    "bariyer", KOK / "scripts" / "olcum" / "63_bariyer_kesisimi.py")
B63 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(B63)

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)
from ultralytics import YOLO  # noqa: E402

KUMELER = {
    "sentetik_arena_kadraj_t66": Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66"),
    "arena_kompozit": KOK / "data" / "arena_kompozit" / "images",
    "raw_frames": KOK / "data" / "raw_frames",
}
MODEL = KOK / "models" / "navitas_seg_v34_best.pt"
ORNEK = 40

model = YOLO(str(MODEL), task="segment")
rapor = {}
for ad, kok in KUMELER.items():
    if not kok.is_dir():
        rapor[ad] = {"hata": f"dizin yok: {kok}"}
        continue
    yollar = sorted(kok.rglob("*.jpg"))[:ORNEK]
    bariyerli, rotali, ikisi = 0, 0, 0
    ornekler = []
    for p in yollar:
        img = cv2.imread(str(p))
        if img is None:
            continue
        kol, kutular = B63.bariyer_maskesi(img)
        var = bool(kutular)
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        s = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(s, h, w), icerik)
        yol, guven, wps, _c, red, _o = analyze_path(
            mk[0], icerik=icerik, engel_mask=mk[1], mpp=None,
            return_clean=True, return_reason=True, return_olcum=True)
        rota = yol is not None and bool(wps)
        bariyerli += var
        rotali += rota
        if var and rota:
            ikisi += 1
            if len(ornekler) < 5:
                ornekler.append({"kare": p.name, "kutu": len(kutular),
                                 "serit": yol, "guven": round(float(guven), 3)})
    rapor[ad] = {"n": len(yollar), "bariyerli": bariyerli, "rota_uretilen": rotali,
                 "IKISI_BIRDEN": ikisi, "ornekler": ornekler}
    print(ad, json.dumps(rapor[ad], ensure_ascii=False), flush=True)

io.open(Path(__file__).with_name("k5_zemin_arayisi.json"), "w",
        encoding="utf-8").write(json.dumps(rapor, ensure_ascii=False, indent=1))
print("yazildi")
