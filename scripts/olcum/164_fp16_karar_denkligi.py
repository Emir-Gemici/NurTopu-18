"""B4 — FP16 <-> FP32 KARAR DENKLIGI (D-371'in Jetson'siz kapanan ayagi).

ON KAYIT: `results/b4_fps/ON_KAYIT_FP16.md` — esikler F1/F2 sonuc gorulmeden
donduruldu. Olculen sey maske IoU'su DEGIL, YAYINLANAN KARARDIR (serit no ya
da None + ret sebebi). D-74'un dersi: IoU 2,2x artti, karar duzeyinde hicbir
sey degismedi — kiyas karar duzeyinde yapilir.

- F1 (S, zarar yonu): FP32 DOGRUYKEN FP16'nin yanlis serit vermesi = 0 tolerans.
- F2 (R >=30 m katmani): karar uyusmasi >= 0,98.
- CUDA yoksa OLCULEMEDI — CPU half emulasyonuyla "gecti" URETILMEZ.

⚡ Maskeler bit-es ise karar BIR KEZ hesaplanir (analyze_path deterministik);
bit-es olmayan karede iki kol ayri kosulur.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import (OLCEK_KAYNAK_TELEMETRI,  # noqa: E402
                              SARTNAME_ASGARI_IRTIFA_M, mpp_irtifadan,
                              rota_olcek_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

CONF = 0.30
FOV_ESAS = 67.3            # EK-1 §E1.4'te donduruldu
F2_UYUSMA_ASGARI = 0.98    # ON_KAYIT_FP16 §2'de donduruldu

R_KOK = REPO / "results" / "dji_20260822"
S_KOK = Path("O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66")


def _karar(masks, icerik, mpp):
    """163 ile AYNI uretim karar halkasi (rpi_inference.py:2088-2101)."""
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(
        masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, (red[0] if isinstance(red, tuple) else red)


def _dtype_dogrula(model, beklenen, ad):
    """🔴 OLCEN ARACIN KENDISI OLCULUR (D-370/D-375).

    Ilk kosum ayni model nesnesine once half=False sonra half=True verdi;
    ultralytics predictor'i ILK cagrida kurar ve ikinci cagrinin half'ini
    SESSIZCE YOK SAYAR — iki kol da FP32 kostu, bit_es=1,0 cikti ve 'GECTI'
    hukmu hicligin olcumuydu. Bu yuzden her kolun dtype'i KOD icinde
    dogrulanir; tutmuyorsa sonuc OLCULEMEDI'dir, 'gecti' uretilmez.
    """
    d = str(next(model.predictor.model.model.parameters()).dtype)
    if d != beklenen:
        print(f"OLCULEMEDI: {ad} kolu {d} kosuyor (beklenen {beklenen}) — "
              f"half uygulanmadi; olcum VAKUM olurdu (D-375)")
        raise SystemExit(1)


def _iki_kol(model32, model16, img, mpp):
    """Ayni kare, iki AYRI model ornegi. -> (fp32, fp16, maskeler_bit_es)."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    s32 = model32.predict(small, imgsz=INFER_SIZE, conf=CONF,
                          verbose=False, half=False, device=0)
    m32 = _maskeleri_icerige_kirp(get_masks(s32, h, w), icerik)
    s16 = model16.predict(small, imgsz=INFER_SIZE, conf=CONF,
                          verbose=False, half=True, device=0)
    m16 = _maskeleri_icerige_kirp(get_masks(s16, h, w), icerik)
    _dtype_dogrula(model32, "torch.float32", "FP32")
    _dtype_dogrula(model16, "torch.float16", "FP16")

    bit_es = (set(m32) == set(m16) and
              all(np.array_equal(m32[k], m16[k]) for k in m32))
    k32 = _karar(m32, icerik, mpp)
    k16 = k32 if bit_es else _karar(m16, icerik, mpp)
    return k32, k16, bit_es


def _kayit(ad, mpp, k32, k16, bit_es, ek=None):
    r = {"kare": ad, "mpp": mpp, "bit_es": bit_es,
         "fp32_yol": k32[0], "fp32_red": k32[1],
         "fp16_yol": k16[0], "fp16_red": k16[1],
         "uyusma": k32[0] == k16[0]}
    if ek:
        r.update(ek)
    return r


def olc_S(model32, model16, sinir=None):
    man = json.loads((S_KOK / "manifest.json").read_text(encoding="utf-8"))
    kayitlar = []
    for ornek in man["ornekler"]:
        if sinir and len(kayitlar) >= sinir:
            break
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = S_KOK / ornek["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        k32, k16, bit_es = _iki_kol(model32, model16, img,
                                    ornek["arena"].get("mpp"))
        kayitlar.append(_kayit(p.name, ornek["arena"].get("mpp"), k32, k16,
                               bit_es,
                               {"acik_serit": ornek["arena"].get("acik_serit")}))
    return kayitlar


def olc_R_katman(model32, model16, sinir=None):
    """YALNIZ >=30 m kareleri (ON_KAYIT_FP16 §1 — GPU sirali, israf yok)."""
    irt = json.loads((R_KOK / "kareler_irtifa.json").read_text(encoding="utf-8"))
    kayitlar = []
    for k in sorted(irt, key=lambda x: (x["kaynak"], x["zaman_sn"])):
        if sinir and len(kayitlar) >= sinir:
            break
        if (k.get("rel_alt") or 0.0) < SARTNAME_ASGARI_IRTIFA_M:
            continue
        p = R_KOK / "kareler_1fps" / k["dosya"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        sq_w = max(img.shape[:2])  # yalniz log icin; mpp icerik genisliginden:
        mpp = mpp_irtifadan(k["rel_alt"], img.shape[1],
                            yatay_fov_derece=FOV_ESAS)
        k32, k16, bit_es = _iki_kol(model32, model16, img, mpp)
        kayitlar.append(_kayit(k["dosya"], mpp, k32, k16, bit_es,
                               {"rel_alt": k["rel_alt"], "tuval": sq_w}))
    return kayitlar


def hukum(s_kayit, r_kayit, cuda_var):
    if not cuda_var:
        return {"F1": {"durum": "OLCULEMEDI", "sebep": "CUDA yok"},
                "F2": {"durum": "OLCULEMEDI", "sebep": "CUDA yok"}}
    h = {}
    # F1: FP32 DOGRUYKEN FP16 YANLIS serite doner — 0 tolerans (S'te GT var).
    zarar = [k for k in s_kayit
             if k["fp32_yol"] == k["acik_serit"]
             and k["fp16_yol"] is not None
             and k["fp16_yol"] != k["acik_serit"]]
    h["F1"] = {"zarar_veren": [k["kare"] for k in zarar],
               "sayi": len(zarar), "tolerans": 0,
               "durum": ("OLCULEMEDI" if not s_kayit
                         else "GECTI" if not zarar else "DUSTU")}
    # F2: R katmaninda karar uyusmasi.
    if r_kayit:
        uy = sum(1 for k in r_kayit if k["uyusma"]) / len(r_kayit)
        h["F2"] = {"uyusma": uy, "n": len(r_kayit),
                   "esik": F2_UYUSMA_ASGARI,
                   "durum": "GECTI" if uy >= F2_UYUSMA_ASGARI else "DUSTU"}
    else:
        h["F2"] = {"durum": "OLCULEMEDI", "sebep": "katman karesi yok"}
    # F3 (bilgi, kapi degil): uyusmazlik yonleri.
    yon = {"None->serit": 0, "serit->None": 0, "serit->serit": 0}
    for k in list(s_kayit) + list(r_kayit):
        if k["uyusma"]:
            continue
        if k["fp32_yol"] is None:
            yon["None->serit"] += 1
        elif k["fp16_yol"] is None:
            yon["serit->None"] += 1
        else:
            yon["serit->serit"] += 1
    h["F3_bilgi"] = yon
    h["bit_es_orani"] = {
        "S": (sum(1 for k in s_kayit if k["bit_es"]) / len(s_kayit)
              if s_kayit else None),
        "R": (sum(1 for k in r_kayit if k["bit_es"]) / len(r_kayit)
              if r_kayit else None)}
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinir", type=int, default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    import torch
    cuda_var = torch.cuda.is_available()
    if not cuda_var:
        print("CUDA YOK -> OLCULEMEDI (ON_KAYIT_FP16 §3; half emulasyonuyla "
              "'gecti' uretilmez)")
    from ultralytics import YOLO
    mp = uretim_pt()
    print(f"MODEL: {mp} · CUDA: {cuda_var}")
    # 🔴 IKI AYRI ORNEK (D-375): tek nesneye iki half degeri verilirse
    # ikincisi SESSIZCE yok sayilir — olcum vakumlasir.
    model32 = YOLO(str(mp), task="segment")
    model16 = YOLO(str(mp), task="segment")

    s_kayit, r_kayit = [], []
    if cuda_var:
        t0 = time.time()
        s_kayit = olc_S(model32, model16, a.sinir)
        t1 = time.time()
        r_kayit = olc_R_katman(model32, model16, a.sinir)
        t2 = time.time()
        print(f"S: n={len(s_kayit)} ({t1 - t0:.0f} sn) · "
              f"R katman: n={len(r_kayit)} ({t2 - t1:.0f} sn)")

    h = hukum(s_kayit, r_kayit, cuda_var)
    print(json.dumps(h, ensure_ascii=False, indent=1))

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"_on_kayit": "results/b4_fps/ON_KAYIT_FP16.md",
             "_model": str(mp), "_conf": CONF, "_infer_size": INFER_SIZE,
             "_fov_esas": FOV_ESAS, "hukum": h,
             "S": s_kayit, "R_katman": r_kayit},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"JSON: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
