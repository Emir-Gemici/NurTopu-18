"""T150 baglama olcumu (D-386) — HB hedeflemesi ACILIRSA ne olur?

ON KAYIT: results/t150/ON_KAYIT_BAGLAMA.md (K2a onayli; renk teyidi geldi).
Bu betik BAGLAMADAN ONCE catali olcer:

  KIP A (bugunku uretim): analyze_path'e goruntu GECMEZ — hedef ust bant.
  KIP B (tam baglama)   : goruntu + mpp gecer — hedef HB (olcek+sekil kapili,
                          rpi_inference icindeki tek noktadan).
  SONDA (kadraj-disi)   : ayni karede HB pedi ORTULUR (griyle boyanir) ve
                          KIP B cagrilir — ucusta pedin gorus disinda kaldigi
                          karelerin vekili. Beklenen: HEDEF_YOK (fail-closed).

Cikti K10 kararinin kanitidir: tam baglama pedin gorunmedigi HER karede
cekimserlik demek; oran burada olculur, karari mimar/kullanici verir.
"""
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import OLCEK_KAYNAK_TELEMETRI, rota_olcek_reddi  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

CONF = 0.30
T66 = Path("O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66")
CIKTI = REPO / "results" / "t150"


def karar(masks, icerik, mpp, goruntu=None):
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(
        masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI,
        goruntu=goruntu)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, wps, (red[0] if isinstance(red, tuple) else red)


def main():
    from ultralytics import YOLO
    mp = uretim_pt()
    model = YOLO(str(mp), task="segment")
    man = json.loads((T66 / "manifest.json").read_text(encoding="utf-8"))

    kayitlar = []
    for o in man["ornekler"]:
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = T66 / o["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        a = o["arena"]
        mpp = a.get("mpp")
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        masks = _maskeleri_icerige_kirp(get_masks(son, h, w), icerik)

        ya, _, ra = karar(masks, icerik, mpp)                      # KIP A
        yb, wb, rb = karar(masks, icerik, mpp, goruntu=sq)         # KIP B

        # hedef dogru pedde mi (KIP B rota urettiyse son waypoint ped kutusunda)
        hx, hy, hw_, hh_ = a["hedef_kutu"]
        hedef_pedde = None
        if yb is not None and wb:
            sx, sy = wb[-1]
            hedef_pedde = bool(hx - 3 <= sx <= hx + hw_ + 3
                               and hy - 3 <= sy <= hy + hh_ + 3)

        # SONDA: pedi ORT (arka planla benzer gri) -> kadraj-disi vekili
        ort = sq.copy()
        x0, y0 = max(0, int(hx)), max(0, int(hy))
        ort[y0:y0 + int(hh_) + 1, x0:x0 + int(hw_) + 1] = (128, 128, 128)
        ys, _, rs = karar(masks, icerik, mpp, goruntu=ort)

        kayitlar.append({"kare": p.name, "acik_serit": a.get("acik_serit"),
                         "A_yol": ya, "A_red": ra,
                         "B_yol": yb, "B_red": rb, "B_hedef_pedde": hedef_pedde,
                         "SONDA_yol": ys, "SONDA_red": rs})

    n = len(kayitlar)
    pa = sum(1 for k in kayitlar if k["A_yol"]) / n
    pb = sum(1 for k in kayitlar if k["B_yol"]) / n
    b_rotali = [k for k in kayitlar if k["B_yol"] is not None]
    pedde = sum(1 for k in b_rotali if k["B_hedef_pedde"])
    b_dogru = sum(1 for k in b_rotali if k["B_yol"] == k["acik_serit"])
    sonda_rota = [k for k in kayitlar if k["SONDA_yol"] is not None]
    sonda_hy = sum(1 for k in kayitlar if k["SONDA_red"] == "HEDEF_YOK")

    print(f"n = {n}")
    print(f"KIP A (bugunku)     : p = {pa:.4f}")
    print(f"KIP B (tam baglama) : p = {pb:.4f} · rota ureten {len(b_rotali)}")
    print(f"   hedef DOGRU pedde: {pedde}/{len(b_rotali)}")
    print(f"   yayinlanan serit dogru: {b_dogru}/{len(b_rotali)}")
    print(f"SONDA (ped ortulu)  : rota ureten {len(sonda_rota)}/{n} · "
          f"HEDEF_YOK {sonda_hy}/{n}")
    if sonda_rota:
        print("   🔴 ped gorunmezken rota ureten kareler (fail-closed "
              "BEKLENIYORDU):", [k["kare"] for k in sonda_rota[:6]])

    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "baglama_olcumu_20260901.json").write_text(json.dumps({
        "_on_kayit": "results/t150/ON_KAYIT_BAGLAMA.md",
        "_model": str(mp),
        "ozet": {"n": n, "p_A": pa, "p_B": pb,
                 "B_hedef_pedde": [pedde, len(b_rotali)],
                 "B_serit_dogru": [b_dogru, len(b_rotali)],
                 "SONDA_rota": len(sonda_rota), "SONDA_hedef_yok": sonda_hy},
        "kareler": kayitlar}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"json -> {CIKTI / 'baglama_olcumu_20260901.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
