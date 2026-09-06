"""GUN-1 §4 — TensorRT FP16 .engine <-> PyTorch FP32 .pt KARAR DENKLIGI (Jetson'da kosar).

KOKEN: 6 Eylul 2026 Jetson Orin Nano oturumunda `results/jetson_log_20260906/engine_karar_denkligi.py`
adiyla yazildi ve kosuldu (paket GELISTIRICIYE_20260906, REVIEW_LOG D-431; ham cikti
`results/jetson_20260906/jetson_log_20260906/engine_karar_denkligi.json`). Paket bunu
`scripts/olcum/165_engine_karar_denkligi.py` olarak oneriyordu; 165 numarasi depoda
`165_trt_pc_provasi.py` ile CAKISIYORDU -> 170. 7 Eylul degisiklikleri (mimar birlestirmesi):
  · ciplak model yollari KALDIRILDI — .pt kayit defterinden (`ayarlar.uretim_pt`, madde 16),
    .engine defterin `turevler` sozlugundeki kayitli tensorrt turevinden cozulur (`--engine` ile
    acik yol verilebilir; her iki kol da `model_kayit_dogrula`dan gecmeden OLCULMEZ);
  · `--json` varsayilani betik dizinine yazmiyor (164 kalibi: verilmezse yalniz basar);
  · S kumesi secilebilir: `--s-kume kompozit` (6 Eylul'de olculen `data/arena_kompozit_v2`,
    T66 KABUL KUMESI DEGILDIR) ya da `--s-kume kabul` (profilin `kabul_kumesi` = T66, D-303'un
    yazildigi kume; K2 nihai karari bununla verilir — kume Jetson'a kopyalanmis olmali).
Olcum mantigi 6 Eylul'de kosulanla AYNI; hukum kurallari degismedi.

Yontem `scripts/olcum/164_fp16_karar_denkligi.py` ile AYNI uretim karar halkasi;
tek fark ikinci kol `half=True` .pt DEGIL, Jetson'da derlenmis .engine'dir.
Esikler ON_KAYIT_FP16 §2'den alinir, SONUC GORULMEDEN:
  F1 (S, zarar yonu): FP32 DOGRUYKEN engine'in yanlis serit vermesi = 0 tolerans.
  F2 (R >=30 m katmani): yayinlanan karar uyusmasi >= 0,98.
  D-303 kurali (FAZ_B_GUN_PLANI §2 11:15 satiri): uyusmazlik <= 5/260 -> S'te oranla uygulanir.
R kumesi: `results/dji_20260822/kareler_irtifa.json` >= 30 m katmani (633 kare), FOV 67,3 (EK-1).
`--r-genislik 1280`: 4K kareler CPU costmap'te dakikalar suruyor (D-431 K7); uretimde kopru
1280 genislik verir, mpp yeni genislikten turetilir.
CUDA yoksa OLCULEMEDI.
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
from karar_sozlesmesi import (OLCEK_KAYNAK_TELEMETRI, SARTNAME_ASGARI_IRTIFA_M,  # noqa: E402
                              mpp_irtifadan, rota_olcek_reddi)
from model_registry import (TUREV_BACKEND, load_registry,  # noqa: E402
                            sha256_dogrulanmis_mi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp, _preprocess,  # noqa: E402
                           _rota_kararini_esikle, analyze_path, get_masks,
                           model_kayit_dogrula)

CONF = 0.30
FOV_ESAS = 67.3            # EK-1 §E1.4'te donduruldu (164 ile ayni)
F2_UYUSMA_ASGARI = 0.98    # ON_KAYIT_FP16 §2'de donduruldu (164 ile ayni)
D303_ORAN = 5 / 260        # FAZ_B_GUN_PLANI §2 11:15 satiri (T66 n=260 icin yazildi)
S_KOMPOZIT = REPO / "data" / "arena_kompozit_v2"
R_KOK = REPO / "results" / "dji_20260822"
ENGINE_UZANTISI = ".engine"
PAKET_MODEL_DIZINI = REPO / "jetson_paket" / "models"
KANONIK_MODEL_DIZINI = REPO / "models"


def s_kumesi(secim: str) -> Path:
    """S kumesi: 'kompozit' (6 Eylul olcumu) ya da 'kabul' (defterin `kabul_kumesi`, T66)."""
    if secim == "kompozit":
        return S_KOMPOZIT
    reg = load_registry()
    profil = reg["profiles"][reg["default_profile"]]
    yol = Path(profil["kabul_kumesi"])
    if not yol.is_absolute():
        yol = REPO / yol
    return yol


def kayitli_engine() -> Path:
    """Defterde sha256'si DOGRULANMIS tensorrt turevini diskte bul (ciplak yol yok, madde 16)."""
    reg = load_registry()
    profil = reg["profiles"][reg["default_profile"]]
    turevler = profil.get("turevler") or {}
    adaylar = sorted(ad for ad, k in turevler.items()
                     if isinstance(k, dict) and k.get("backend") == TUREV_BACKEND[ENGINE_UZANTISI]
                     and sha256_dogrulanmis_mi(k.get("sha256")))
    if not adaylar:
        raise RuntimeError("defterde sha256'si kayitli tensorrt turevi yok (once Jetson'da derle + "
                           "`codes/model_registry.py --turev-kaydet`)")
    for ad in adaylar:
        for dizin in (PAKET_MODEL_DIZINI, KANONIK_MODEL_DIZINI):
            if (dizin / ad).is_file():
                return dizin / ad
    raise RuntimeError(f"kayitli tensorrt turevi diskte yok: {adaylar} "
                       f"({PAKET_MODEL_DIZINI.relative_to(REPO).as_posix()} / models)")


def _karar(masks, icerik, mpp):
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
                                        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, (red[0] if isinstance(red, tuple) else red)


def _iki_kol(m32, meng, img, mpp):
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    s32 = m32.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False, half=False, device=0)
    a = _maskeleri_icerige_kirp(get_masks(s32, h, w), icerik)
    se = meng.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False, device=0)
    b = _maskeleri_icerige_kirp(get_masks(se, h, w), icerik)
    bit_es = set(a) == set(b) and all(np.array_equal(a[k], b[k]) for k in a)
    ka = _karar(a, icerik, mpp)
    kb = ka if bit_es else _karar(b, icerik, mpp)
    return ka, kb, bit_es


def _kayit(ad, mpp, ka, kb, bit_es, ek=None):
    r = {"kare": ad, "mpp": mpp, "bit_es": bit_es, "fp32_yol": ka[0], "fp32_red": ka[1],
         "engine_yol": kb[0], "engine_red": kb[1], "uyusma": ka[0] == kb[0]}
    if ek:
        r.update(ek)
    return r


def olc_S(m32, meng, s_kok, sinir=None):
    man = json.loads((s_kok / "manifest.json").read_text(encoding="utf-8"))
    out = []
    for o in man["ornekler"]:
        if sinir and len(out) >= sinir:
            break
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = s_kok / o["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        ka, kb, be = _iki_kol(m32, meng, img, o["arena"].get("mpp"))
        out.append(_kayit(p.name, o["arena"].get("mpp"), ka, kb, be,
                          {"acik_serit": o["arena"].get("acik_serit")}))
    return out


def olc_R(m32, meng, sinir=None, genislik=None):
    irt = json.loads((R_KOK / "kareler_irtifa.json").read_text(encoding="utf-8"))
    out = []
    for k in sorted(irt, key=lambda x: (x["kaynak"], x["zaman_sn"])):
        if sinir and len(out) >= sinir:
            break
        if (k.get("rel_alt") or 0.0) < SARTNAME_ASGARI_IRTIFA_M:
            continue
        p = R_KOK / "kareler_1fps" / k["dosya"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        if genislik and img.shape[1] > genislik:
            # uretim kosulu: kopru 1280 genislikte verir (4K costmap CPU'da dakikalar suruyor, D-431 K7)
            olcek = genislik / img.shape[1]
            img = cv2.resize(img, (genislik, int(round(img.shape[0] * olcek))),
                             interpolation=cv2.INTER_AREA)
        mpp = mpp_irtifadan(k["rel_alt"], img.shape[1], yatay_fov_derece=FOV_ESAS)
        ka, kb, be = _iki_kol(m32, meng, img, mpp)
        out.append(_kayit(k["dosya"], mpp, ka, kb, be, {"rel_alt": k["rel_alt"]}))
    return out


def hukum(s, r, s_adi):
    h = {}
    zarar = [k for k in s if k["fp32_yol"] == k["acik_serit"] and k["engine_yol"] is not None
             and k["engine_yol"] != k["acik_serit"]]
    h["F1"] = {"zarar_veren": [k["kare"] for k in zarar], "sayi": len(zarar), "tolerans": 0,
               "durum": "OLCULEMEDI" if not s else ("GECTI" if not zarar else "DUSTU"),
               "_not": f"S = {s_adi}" + ("" if s_adi == "kabul" else
                                          " (GT'li kompozit kume; T66 KABUL kumesi DEGILDIR)")}
    if s:
        uyusan = sum(1 for k in s if k["uyusma"])
        h["D303_S"] = {"uyusmazlik": len(s) - uyusan, "n": len(s), "esik_oran": D303_ORAN,
                       "durum": "GECTI" if (1 - uyusan / len(s)) <= D303_ORAN else "DUSTU"}
    if r:
        uy = sum(1 for k in r if k["uyusma"]) / len(r)
        h["F2"] = {"uyusma": round(uy, 5), "n": len(r), "esik": F2_UYUSMA_ASGARI,
                   "durum": "GECTI" if uy >= F2_UYUSMA_ASGARI else "DUSTU"}
    else:
        h["F2"] = {"durum": "OLCULEMEDI", "sebep": "katman karesi yok"}
    yon = {"None->serit": 0, "serit->None": 0, "serit->serit": 0}
    for k in list(s) + list(r):
        if k["uyusma"]:
            continue
        if k["fp32_yol"] is None:
            yon["None->serit"] += 1
        elif k["engine_yol"] is None:
            yon["serit->None"] += 1
        else:
            yon["serit->serit"] += 1
    h["F3_bilgi"] = yon
    h["bit_es_orani"] = {"S": (sum(1 for k in s if k["bit_es"]) / len(s)) if s else None,
                         "R": (sum(1 for k in r if k["bit_es"]) / len(r)) if r else None}
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinir", type=int, default=None)
    ap.add_argument("--r-sinir", type=int, default=None)
    ap.add_argument("--r-genislik", type=int, default=None,
                    help="R karelerini bu genislige kucult (uretim: 1280); mpp yeni genislikten turetilir")
    ap.add_argument("--s-kume", choices=("kompozit", "kabul"), default="kompozit",
                    help="S kumesi: kompozit = data/arena_kompozit_v2 (6 Eylul olcumu); "
                         "kabul = defterin kabul_kumesi (T66, D-303'un kumesi)")
    ap.add_argument("--engine", default=None,
                    help="acik .engine yolu; verilmezse defterin kayitli tensorrt turevi diskte aranir")
    ap.add_argument("--json", default=None, help="verilmezse yalniz basilir (164 kalibi)")
    a = ap.parse_args()
    import torch
    if not torch.cuda.is_available():
        print("OLCULEMEDI: CUDA yok")
        return 1
    pt = uretim_pt()
    engine = Path(a.engine) if a.engine else kayitli_engine()
    s_kok = s_kumesi(a.s_kume)
    if not (s_kok / "manifest.json").is_file():
        print(f"OLCULEMEDI: S kumesi yok: {s_kok}")
        return 1
    for y in (pt, engine):
        ok, d = model_kayit_dogrula(y)
        print(("GECTI " if ok else "RED   ") + f"defter: {y.name} -> {d.get('durum')}")
        if not ok:
            print("OLCULEMEDI: kayit defteri reddi")
            return 1
    from ultralytics import YOLO
    m32 = YOLO(str(pt), task="segment")
    meng = YOLO(str(engine), task="segment")
    t0 = time.time()
    s = olc_S(m32, meng, s_kok, a.sinir)
    print(f"S ({a.s_kume}: {s_kok}): {len(s)} kare ({time.time() - t0:.0f} s)")
    d32 = str(next(m32.predictor.model.model.parameters()).dtype)
    arka = type(meng.predictor.model).__name__ + "/" + (
        "engine" if getattr(meng.predictor.model, "engine", False) else "?")
    print(f"kol A dtype {d32} · kol B arka uc {arka}")
    if d32 != "torch.float32":
        print("OLCULEMEDI: FP32 kolu float32 degil")
        return 1
    t0 = time.time()
    r = olc_R(m32, meng, a.r_sinir or a.sinir, a.r_genislik)
    print(f"R>=30m: {len(r)} kare ({time.time() - t0:.0f} s) · r_genislik={a.r_genislik}")
    h = hukum(s, r, a.s_kume)
    print(json.dumps(h, indent=1, ensure_ascii=False))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"_on_kayit": "results/b4_fps/ON_KAYIT_FP16.md §2 + FAZ_B_GUN_PLANI §2 D-303",
             "_model": {"pt": str(pt), "engine": str(engine)}, "_s_kume": a.s_kume, "_s_kok": str(s_kok),
             "_conf": CONF, "_infer_size": INFER_SIZE, "_fov_esas": FOV_ESAS,
             "_r_genislik": a.r_genislik, "_r_sinir": a.r_sinir, "hukum": h, "S": s, "R_katman": r},
            indent=1, ensure_ascii=False), encoding="utf-8")
        print("yazildi:", a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
