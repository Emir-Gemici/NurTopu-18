"""153 — v8 ADAY MODEL DEGERLENDIRMESI (on kayit: results/gece_20260828/ON_KAYIT.md).

Egitim bitince tek komutla TUM on kayitli kapilari kosar ve TEK bir hukum
uretir. Amac: model gelince hukmun HIZLI ve EKSIKSIZ verilmesi; aksi halde
insan "iyi gorunuyor" deyip gecer.

KOSULAN KAPILAR (hepsi ON KAYITTA, olcumden ONCE yazildi):
  G4 · bariyeri HER ACIDA goruyor mu — sartname karesi 15 derecelik adimlarla
       0-165 arasi dondurulur; bariyer bolgesinde ENGEL orani >= %60 olan aci
       sayisi >= 10/12 olmali. v36 TABANI: 7/12 (60/105/120/135'te %0,0).
  G5 · BOZULMAMA: K7 kabul kumesinde dogruluk >= %95 VE rota ureten >= 80/88.
       v36 TABANI: %98,8 · 85/88.
  G11· kompozit kumede rota >= 45/88. v36 TABANI: 49/88.
  EK · GUI kaynak dagilimi (bilgi; kapi DEGIL).

YAYIMLAMA KURALI (on kayit SS4): yeni model uretime YALNIZ G4 ∧ G5 ∧ G6
birlikte gecerse alinir. G6 (genel kapi + suit) bu betikte KOSULMAZ — ayri
komuttur ve insan tarafindan gorulmelidir.

Kullanim:
  <venv> 153_v8_degerlendirme.py --agirlik codes/runs/segment/bariyer_v8_v36taban/weights/best.pt
  <venv> 153_v8_degerlendirme.py --agirlik ... --kiyas models/navitas_seg_v36_best.pt
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "codes"))

import cv2                                                        # noqa: E402
import numpy as np                                                # noqa: E402

from karar_sozlesmesi import ince_bariyer_maskesi                 # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,   # noqa: E402
                           _preprocess, analyze_path, get_masks)

SARTNAME = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
K7_KUME = KOK / "config" / "k7_iyi_kosullu_kume.json"
T66 = Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66\images")
KOMPOZIT = KOK / "data" / "arena_kompozit"

# ── ON KAYITLI ESIKLER — sonuca gore DEGISTIRILMEZ ─────────────────────────
G4_ACI_ESIGI = 60.0          # bariyer bolgesinde ENGEL orani (%)
G4_GECEN_ACI_ASGARI = 10     # 12 acidan kaci gecmeli
G5_DOGRULUK_ASGARI = 0.95
G5_ROTA_ASGARI = 80
G11_KOMPOZIT_ASGARI = 45

# Taban degerleri (v36, 2026-08-28 olculdu) — kiyas icin, kapi icin DEGIL.
TABAN = {"G4": 7, "G5_dogruluk": 0.9882, "G5_rota": 85, "G11": 49}


def _dondur(g, aci):
    h, w = g.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), aci, 1.0)
    kos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * kos), int(h * kos + w * sin)
    M[0, 2] += nw / 2.0 - w / 2.0
    M[1, 2] += nh / 2.0 - h / 2.0
    return cv2.warpAffine(g, M, (nw, nh), flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_REPLICATE)


def _engel_maskesi(model, g):
    """Modelin ENGEL(1) maskesi — URETIM cagri sirasiyla."""
    h, w = g.shape[:2]
    res = model.predict(g, imgsz=INFER_SIZE, conf=0.30, verbose=False)
    o = np.zeros((h, w), np.uint8)
    r = res[0]
    if r.masks is None:
        return o
    for msk, c in zip(r.masks.data.cpu().numpy(),
                      r.boxes.cls.cpu().numpy().astype(int)):
        if int(c) == 1:
            o = np.maximum(o, cv2.resize(msk.astype(np.uint8), (w, h),
                                         interpolation=cv2.INTER_NEAREST))
    return o


def g4_aci_taramasi(model):
    """Bariyeri HER ACIDA goruyor mu (D-324 §4)."""
    if not SARTNAME.is_file():
        return {"hata": "sartname karesi yok"}
    im = cv2.imread(str(SARTNAME))
    bar0 = ince_bariyer_maskesi(im)
    acilar = {}
    gecen = 0
    for aci in range(0, 180, 15):
        g = _dondur(im, aci)
        b = _dondur(bar0 * 255, aci) > 127
        e = _engel_maskesi(model, g)
        n = int(b.sum())
        oran = 100.0 * int((b & (e > 0)).sum()) / max(1, n)
        ok = oran >= G4_ACI_ESIGI
        gecen += ok
        acilar[str(aci)] = {"oran": round(oran, 1), "gecti": bool(ok)}
    return {"acilar": acilar, "gecen_aci": gecen, "toplam": 12,
            "esik": G4_GECEN_ACI_ASGARI,
            "gecti": gecen >= G4_GECEN_ACI_ASGARI,
            "taban_v36": TABAN["G4"]}


def _kume_rota(model, yollar, mpp_f):
    rota = 0
    sebepler = {}
    seritler = {}
    for p in yollar:
        im = cv2.imread(p)
        if im is None:
            continue
        sq, small, icerik = _preprocess(im)
        res = model.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
        m = _maskeleri_icerige_kirp(get_masks(res, sq.shape[0], sq.shape[1]),
                                    icerik)
        yol, _g, _w, red = analyze_path(m[0], icerik=icerik,
                                        engel_mask=m.get(1), mpp=mpp_f(im),
                                        return_reason=True)
        if yol:
            rota += 1
            seritler[str(yol)] = seritler.get(str(yol), 0) + 1
        else:
            kod = red[0] if isinstance(red, (tuple, list)) else str(red)
            sebepler[kod] = sebepler.get(kod, 0) + 1
    return rota, sebepler, seritler


def g5_k7(model_yolu):
    """K7 kabul kumesi — mevcut olcum betigini KOSAR (kopya mantik yok)."""
    import subprocess
    cikti = KOK / "results" / "gece_20260828" / "k7_aday.json"
    komut = [sys.executable, str(KOK / "scripts" / "olcum" /
                                 "151_k7_serit_dogrulugu.py"),
             "--agirlik", str(model_yolu), "--cikti", str(cikti)]
    p = subprocess.run(komut, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if not cikti.is_file():
        return {"hata": "K7 olcumu uretilmedi", "stdout": p.stdout[-500:]}
    ham = json.loads(cikti.read_text(encoding="utf-8"))
    # 🔴 Betigin YAZDIGI json ile EKRANA BASTIGI ozet ayni sey degil:
    # dosyada olculer "ozet" anahtari altinda durur. Ilk surumde ust duzeyde
    # aradim ve KeyError aldim — bu betigi v36 tabaninda ONCEDEN kosmak
    # tam da bunun icindi.
    d = dict(ham.get("ozet") or ham)
    gecti = (d["dogruluk"] >= G5_DOGRULUK_ASGARI
             and d["rota_uretilen"] >= G5_ROTA_ASGARI)
    d.update({"esik_dogruluk": G5_DOGRULUK_ASGARI,
              "esik_rota": G5_ROTA_ASGARI, "gecti": bool(gecti),
              "taban_v36_dogruluk": TABAN["G5_dogruluk"],
              "taban_v36_rota": TABAN["G5_rota"]})
    return d


def g11_kompozit(model):
    yollar = sorted(glob.glob(str(KOMPOZIT / "images" / "*" / "*.jpg")))
    rota, sebepler, seritler = _kume_rota(
        model, yollar, lambda im: 50.0 / im.shape[1])
    return {"n": len(yollar), "rota": rota, "esik": G11_KOMPOZIT_ASGARI,
            "gecti": rota >= G11_KOMPOZIT_ASGARI, "sebepler": sebepler,
            "seritler": seritler, "taban_v36": TABAN["G11"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--agirlik", type=Path, required=True)
    ap.add_argument("--cikti", type=Path,
                    default=KOK / "results" / "gece_20260828" / "v8_hukum.json")
    a = ap.parse_args()
    if not a.agirlik.is_file():
        raise SystemExit(f"agirlik yok: {a.agirlik}")

    from ultralytics import YOLO
    model = YOLO(str(a.agirlik), task="segment")
    print(f"model: {a.agirlik}")

    sonuc = {"model": str(a.agirlik)}
    print("\n[1/3] G4 · bariyer aci taramasi ...", flush=True)
    sonuc["G4"] = g4_aci_taramasi(model)
    print("[2/3] G5 · K7 kabul kumesi ...", flush=True)
    sonuc["G5"] = g5_k7(a.agirlik)
    print("[3/3] G11 · kompozit ...", flush=True)
    sonuc["G11"] = g11_kompozit(model)

    print("\n" + "=" * 66)
    g4, g5, g11 = sonuc["G4"], sonuc["G5"], sonuc["G11"]
    if "acilar" in g4:
        print(f"  G4  bariyer aci    {g4['gecen_aci']}/12 aci >= %{G4_ACI_ESIGI:.0f}"
              f"   (esik {G4_GECEN_ACI_ASGARI}/12 · v36 tabani {g4['taban_v36']}/12)"
              f"   {'GECTI' if g4['gecti'] else 'DUSTU'}")
        kor = [k for k, v in g4["acilar"].items() if not v["gecti"]]
        if kor:
            print(f"      gecemeyen acilar: {', '.join(kor)}")
    if "dogruluk" in g5:
        print(f"  G5  K7 dogruluk    %{100*g5['dogruluk']:.1f} · rota "
              f"{g5['rota_uretilen']}/88   (esik %95 · >=80)   "
              f"{'GECTI' if g5['gecti'] else 'DUSTU'}")
    print(f"  G11 kompozit rota  {g11['rota']}/{g11['n']}   "
          f"(esik >={G11_KOMPOZIT_ASGARI} · v36 tabani {g11['taban_v36']})   "
          f"{'GECTI' if g11['gecti'] else 'DUSTU'}")
    hepsi = all(x.get("gecti") for x in (g4, g5, g11))
    print("-" * 66)
    print(f"  HUKUM: {'UC KAPI DA GECTI' if hepsi else 'EN AZ BIR KAPI DUSTU'}")
    print("  ⚠ Yayimlama icin G6 (genel kapi 15/15 + `discover -s tests`) AYRICA")
    print("    kosulmalidir; bu betik onu KOSMAZ.")
    print("=" * 66)
    sonuc["uc_kapi_gecti"] = bool(hepsi)
    a.cikti.parent.mkdir(parents=True, exist_ok=True)
    a.cikti.write_text(json.dumps(sonuc, indent=1, ensure_ascii=False),
                       encoding="utf-8")
    print(f"\njson -> {a.cikti}")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
