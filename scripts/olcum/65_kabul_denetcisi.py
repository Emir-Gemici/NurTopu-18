"""D-107 KABUL DENETCISI — onceden yazilmis olcutleri MEKANIK olarak kosar.

Esikler `REVIEW_LOG.md` D-107'de sonuc GORULMEDEN yazildi ve burada CIPLAK
SABIT olarak degil, tek bir yerde tanimli olarak durur. Sabah tartisma olmasin
diye karar kurali da koda gomulu: her olcut GECTI/DUSTU doner ve nihai verdikt
AND birlesimidir.

Kullanim:
  venv\\Scripts\\python.exe 65_kabul_denetcisi.py --model <yol> [--ad v27]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

BURASI = Path(__file__).parent
KADRAJ = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
FIGUR = REPO / "data" / "arena_referans" / "sartname_s9_arena.png"
CONF = 0.30

# ── D-107 esikleri · SONUC GORULMEDEN yazildi, sabah DEGISTIRILMEYECEK ──────
ESIK = {
    "K1_rota_min": 230,          # / 260   (v24: 196 · yer gercegi: 260)
    "K2_basma_maks": 0.15,       #         (v24: %31,1 · taban: %9,2)
    "K3_agir_maks": 0.03,        #         (v24: %20,4 · taban: %0)
    "K4_arena_disi_maks": 0.05,  #         (v24: %13,3)
}


def kaplama(model, p):
    img = cv2.imread(str(p))
    if img is None:
        return None
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    return float((mk[0] > 0).mean())


def kos(betik, ek):
    p = subprocess.run([sys.executable, "-B", str(BURASI / betik)] + ek,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    return p.stdout or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--ad", default=None)
    args = ap.parse_args()
    ad = args.ad or args.model.parent.parent.name

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    sonuc, gecti = {}, {}

    # ── K0 · KORLUK YOK (v25'in olum sebebi) ────────────────────────────────
    k0 = {}
    k0["figur"] = kaplama(model, FIGUR)
    for ad_k, kok, desen in (
            ("raw_frames", REPO / "data" / "raw_frames", "*.jpg"),
            ("copy_paste", REPO / "dataset" / "copy_paste_gercek" / "images" / "train", "*.jpg")):
        yollar = sorted(kok.rglob(desen))[::max(1, len(sorted(kok.rglob(desen))) // 8)][:8]
        oranlar = [kaplama(model, p) for p in yollar]
        oranlar = [o for o in oranlar if o is not None]
        k0[ad_k] = {"n": len(oranlar), "bos": sum(1 for o in oranlar if o <= 0.0),
                    "ort": float(np.mean(oranlar)) if oranlar else 0.0}
    gecti["K0"] = (k0["figur"] is not None and k0["figur"] > 0.0
                   and k0["raw_frames"]["bos"] == 0 and k0["copy_paste"]["bos"] == 0)
    sonuc["K0"] = k0

    # ── K1..K4 · rota / basma / arena disi ──────────────────────────────────
    jj = BURASI / "results" / "t63" / f"{ad}_kabul.json"
    kos("61_rota_moloza_basma.py", ["--model", str(args.model),
                                    "--kume", str(KADRAJ), "--json", str(jj)])
    d = json.loads(jj.read_text(encoding="utf-8")) if jj.is_file() else {}
    n, r = d.get("n", 0), d.get("rota_uretilen", 0)
    basan, agir, disi = d.get("basan", 0), d.get("agir", 0), d.get("arena_disi", 0)
    sonuc["K1_rota"] = f"{r}/{n}"
    sonuc["K2_basma"] = f"{basan}/{r}" if r else "-"
    sonuc["K3_agir"] = f"{agir}/{r}" if r else "-"
    sonuc["K4_arena_disi"] = f"{disi}/{r}" if r else "-"
    gecti["K1"] = r >= ESIK["K1_rota_min"]
    gecti["K2"] = bool(r) and basan / r <= ESIK["K2_basma_maks"]
    gecti["K3"] = bool(r) and agir / r <= ESIK["K3_agir_maks"]
    gecti["K4"] = bool(r) and disi / r <= ESIK["K4_arena_disi_maks"]

    # ── K5 · bariyer kesisimi ───────────────────────────────────────────────
    c = kos("63_bariyer_kesisimi.py", ["--model", str(args.model)])
    kes = None
    for s in c.splitlines():
        if "ROTA x BARIYER kesisimi" in s:
            try:
                kes = int(s.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    sonuc["K5_bariyer_px"] = kes
    gecti["K5"] = kes == 0

    # ── RAPOR ───────────────────────────────────────────────────────────────
    print(f"\n{'='*66}\nKABUL DENETIMI · {ad}\n  esikler: REVIEW_LOG D-107 "
          f"(sonuc gorulmeden yazildi)\n{'='*66}")
    f = sonuc["K0"]["figur"]
    print(f"  K0 KORLUK YOK        {'GECTI' if gecti['K0'] else 'DUSTU':<6} "
          f"figur zemin %{100*f:.1f} · raw bos {k0['raw_frames']['bos']}/{k0['raw_frames']['n']} "
          f"· cp bos {k0['copy_paste']['bos']}/{k0['copy_paste']['n']}")
    print(f"  K1 ROTA >= {ESIK['K1_rota_min']}       {'GECTI' if gecti['K1'] else 'DUSTU':<6} "
          f"{sonuc['K1_rota']}")
    print(f"  K2 BASMA <= %{100*ESIK['K2_basma_maks']:.0f}      {'GECTI' if gecti['K2'] else 'DUSTU':<6} "
          f"{sonuc['K2_basma']}   (taban %9,2)")
    print(f"  K3 AGIR  <= %{100*ESIK['K3_agir_maks']:.0f}       {'GECTI' if gecti['K3'] else 'DUSTU':<6} "
          f"{sonuc['K3_agir']}   (taban %0)")
    print(f"  K4 ARENA DISI <= %{100*ESIK['K4_arena_disi_maks']:.0f}  {'GECTI' if gecti['K4'] else 'DUSTU':<6} "
          f"{sonuc['K4_arena_disi']}")
    print(f"  K5 BARIYER = 0 px    {'GECTI' if gecti['K5'] else 'DUSTU':<6} {kes} px")
    print("-" * 66)
    if not gecti["K0"]:
        print("  VERDIKT: RED — K0 dustu. v25 ile AYNI sebep, tartisma yok.")
    elif all(gecti.values()):
        print("  VERDIKT: URETIME ALINIR — D-107'nin alti olcutu de saglandi.")
    else:
        d_ = [k for k, v in gecti.items() if not v]
        print(f"  VERDIKT: URETIME ALINMAZ — dusen: {', '.join(d_)}")
        print("           kok nedene baglanip TEK duzeltme turu kosulur.")
    print("=" * 66)
    print("\n⚠ Bu olcumlerin tamami SENTETIKTIR. Hicbiri 'sahada calisir'")
    print("  anlamina gelmez (D-88 + D-99, kalici kisit).")

    cj = BURASI / "results" / "t63" / f"{ad}_kabul_verdikt.json"
    cj.parent.mkdir(parents=True, exist_ok=True)
    cj.write_text(json.dumps({"model": str(args.model), "esikler": ESIK,
                              "olcum": sonuc, "gecti": gecti,
                              "verdikt": all(gecti.values())},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\njson -> {cj}")


if __name__ == "__main__":
    main()
