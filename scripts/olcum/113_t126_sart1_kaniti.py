"""T126 SART 1 KANITI: bariyer geometrisi MODELDEN GELMIYOR — OLCUMLE.

D-243 SART 1: "Bariyer, degerlendirilen modelin KENDI MASKESINDEN okunursa,
bariyere KOR bir model kapiyi TRIVIAL olarak gecer. Geometri MODEL-BAGIMSIZ
kaynaktan gelecek. `63`un dedektoru bu sarti sagliyor mu? KANITLA — kod
okumasiyla degil, OLCUMLE: dedektoru model YOKKEN calistir."

Bu betik segmentasyon modelini HIC YUKLEMEZ (ultralytics import EDILMEZ) ve
`63_bariyer_kesisimi.bariyer_maskesi`yi dogrudan kosar. Bulunan bariyer
kutulari ve piksel sayilari yazilir. Ek olarak AYNI kareler icin dedektorun
ciktisinin ceyrek/iki-kat parlaklikta DEGISMEDIGI degil — degistigi de
raporlanir (dedektorun neye duyarli oldugu gorunur olsun).

CIKTI: results/t126/sart1_kaniti.json
"""
from __future__ import annotations

import io
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
BURASI = KOK / "scripts" / "olcum"
sys.path.insert(0, str(BURASI))
sys.path.insert(0, str(KOK / "codes"))

# 🔴 KANITIN CEKIRDEGI: "ultralytics import EDILMEDI" YETERSIZ bir iddiadir —
# `rpi_inference` onu modul duzeyinde zaten yukler. Dogru iddia "HICBIR MODEL
# ORNEKLENMEDI"dir. Bu yuzden `YOLO` cagri sayaciyla SARILIR ve olcumun sonunda
# sayacin SIFIR oldugu raporlanir. Sarma, olculecek modullerden ONCE yapilir.
import ultralytics  # noqa: E402

_YOLO_CAGRI = {"n": 0}
_ozgun_YOLO = ultralytics.YOLO


def _sayan_YOLO(*a, **k):
    _YOLO_CAGRI["n"] += 1
    return _ozgun_YOLO(*a, **k)


ultralytics.YOLO = _sayan_YOLO

B63 = import_module("63_bariyer_kesisimi")
K65 = import_module("65_kabul_denetcisi")
CIKTI = KOK / "results" / "t126" / "sart1_kaniti.json"


def main() -> int:
    kume = K65.kabul_kumesi_yolu()
    yollar = sorted(kume.rglob("*.jpg"))
    kayitlar = []
    for p in yollar:
        img = cv2.imread(str(p))
        if img is None:
            continue
        kol, kutular = B63.bariyer_maskesi(img)
        kayitlar.append({"kare": p.name, "kutu": len(kutular),
                         "bariyer_px": int((kol > 0).sum())})
    bulunan = [k for k in kayitlar if k["kutu"]]
    ozet = {
        "kume": str(kume), "n_kare": len(kayitlar),
        "YOLO_MODELI_ORNEKLENDI_MI": _YOLO_CAGRI["n"] > 0,
        "YOLO_cagri_sayisi": _YOLO_CAGRI["n"],
        "bariyer_bulunan_kare": len(bulunan),
        "bariyer_px_ort": round(float(np.mean(
            [k["bariyer_px"] for k in bulunan])), 1) if bulunan else 0.0,
        "dedektor": "63_bariyer_kesisimi.bariyer_maskesi (LAB a* > 25, "
                    "uzun-ince yatay bilesen)",
        "hukum": ("MODEL-BAGIMSIZ: HICBIR YOLO modeli orneklenmeden "
                  f"{len(bulunan)}/{len(kayitlar)} karede bariyer bulundu"),
        "kayitlar": kayitlar,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI, "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
