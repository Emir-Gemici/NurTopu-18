"""v21 egitimi bitince: IKI KAPI + ONNX export + Jetson paketi guncelleme.

NEDEN tek betik: v21'in pakete girmesi otomatik degildir. ARCHITECT_PLAN K-8
bir modelin sevk edilmeden once IKI kapidan gecmesini sart kosuyor:

  1. arena basarimi
  2. GERCEK nadir karede zemin cikarabilme  (v17 burada 10/67 ile kaldi)

Ikincisini gecemeyen model, birincisi ne olursa olsun aday DEGILDIR. Bu betik
kapilari kosar, gecmezse paketi DEGISTIRMEZ ve nedenini yazar.

Kullanim:
  venv\\Scripts\\python.exe scripts/v21_degerlendir_ve_paketle.py
  venv\\Scripts\\python.exe scripts/v21_degerlendir_ve_paketle.py --zorla   # kapi dusse de paketle
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from costmap_path_finder import rota_bul
from rpi_inference import _maskeleri_icerige_kirp, _preprocess, get_masks
from sinif_semasi import ALGI_SINIF_IDLERI

from ultralytics import YOLO

VARSAYILAN_AGIRLIK = KOK / "codes" / "runs" / "segment" / "v21_gercek_doku" / "weights" / "best.pt"
GERCEK_KARE = KOK / "data" / "raw_frames"
ARENA_KARE = KOK / "jetson_paket" / "test_goruntuleri" / "sentetik_arena"
PAKET = KOK / "jetson_paket"

# K-8 kapisi: kare alaninin en az %5'i zemin sayilmali
ASGARI_ZEMIN_ORANI = 0.05
# v17'nin olculmus referansi (conf 0,25) — v21 bunu ACIK ARA gecmeli
V17_REFERANS = 10


def orneklem(kok: Path, n: int | None = None) -> list[Path]:
    hepsi = sorted(p for p in kok.rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
    if n is None or len(hepsi) <= n:
        return hepsi
    return hepsi[::max(1, len(hepsi) // n)][:n]


def zincir(model: YOLO, bgr: np.ndarray, imgsz: int, conf: float, cihaz: str | None):
    """kare -> cikarim -> get_masks -> rota_bul  (uretim yolunun aynisi)"""
    tuval, kucuk, icerik = _preprocess(bgr)
    yan = tuval.shape[0]
    giris = cv2.resize(tuval, (imgsz, imgsz), interpolation=cv2.INTER_AREA)
    kw = {"imgsz": imgsz, "conf": conf, "verbose": False}
    if cihaz:
        kw["device"] = cihaz
    r = model.predict(giris, **kw)
    mk = _maskeleri_icerige_kirp(get_masks(r, yan, yan, sinif_idler=ALGI_SINIF_IDLERI), icerik)
    x0, y0, gen, yuk = icerik
    zemin_orani = float(mk[0][y0:y0 + yuk, x0:x0 + gen].sum()) / (gen * yuk)
    rota = rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False)
    return zemin_orani, rota["durum"]


def kapi_gercek_kare(model: YOLO, conf: float, imgsz: int, cihaz: str | None) -> dict:
    """K-8 ikinci kapisi: gercek nadir karede zemin cikarabiliyor mu?"""
    kareler = orneklem(GERCEK_KARE)
    iyi = 0
    oranlar: list[float] = []
    durumlar: dict[str, int] = {}
    for p in kareler:
        bgr = cv2.imread(str(p))
        if bgr is None:
            continue
        oran, durum = zincir(model, bgr, imgsz, conf, cihaz)
        oranlar.append(oran)
        durumlar[durum] = durumlar.get(durum, 0) + 1
        if oran >= ASGARI_ZEMIN_ORANI:
            iyi += 1
    return {"kare": len(oranlar), "kullanilabilir": iyi,
            "ort_zemin_yuzde": round(float(np.mean(oranlar)) * 100, 2) if oranlar else 0.0,
            "rota_durumlari": durumlar,
            "v17_referans": V17_REFERANS,
            "gecti": iyi > V17_REFERANS}


def kapi_arena(model: YOLO, conf: float, imgsz: int, cihaz: str | None) -> dict:
    """Arena karelerinde karar uretebiliyor mu (MASKE_YOK orani dusuk mu)?"""
    kareler = orneklem(ARENA_KARE)
    if not kareler:
        return {"durum": "ATLANDI", "sebep": f"arena karesi yok: {ARENA_KARE}"}
    durumlar: dict[str, int] = {}
    oranlar: list[float] = []
    for p in kareler:
        bgr = cv2.imread(str(p))
        if bgr is None:
            continue
        oran, durum = zincir(model, bgr, imgsz, conf, cihaz)
        oranlar.append(oran)
        durumlar[durum] = durumlar.get(durum, 0) + 1
    n = sum(durumlar.values()) or 1
    maske_yok = durumlar.get("MASKE_YOK", 0)
    return {"kare": n, "rota_durumlari": durumlar,
            "maske_yok_yuzde": round(maske_yok / n * 100, 1),
            "ort_zemin_yuzde": round(float(np.mean(oranlar)) * 100, 2) if oranlar else 0.0,
            "gecti": maske_yok / n <= 0.25}


def onnx_uret(agirlik: Path, cikti: Path, imgsz: int) -> Path | None:
    """Mevcut export betigini YENIDEN KULLAN (yeniden yazma)."""
    komut = [sys.executable, str(KOK / "scripts" / "export_tensorrt.py"),
             "--model", str(agirlik), "--imgsz", str(imgsz), "--cihaz", "0",
             "--cikti", str(cikti)]
    print("  " + " ".join(komut[-8:]))
    p = subprocess.run(komut, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        print("  HATA: ONNX export basarisiz", file=sys.stderr)
        print("  " + (p.stderr or "")[-600:], file=sys.stderr)
        return None
    uretilen = sorted(cikti.glob(f"*_{imgsz}_fp16.onnx"))
    return uretilen[0] if uretilen else None


def parite(agirlik: Path, onnx: Path, imgsz: int, conf: float) -> dict:
    """PT ve ONNX AYNI rota kararini mi veriyor?

    Bos-dogru tuzagina karsi: karar CESITLILIGI de raporlanir. Tum kareler
    MASKE_YOK ise eslesme anlamsizdir.
    """
    kareler = orneklem(ARENA_KARE, 30) or orneklem(GERCEK_KARE, 30)
    m_pt = YOLO(str(agirlik), task="segment")
    m_ox = YOLO(str(onnx), task="segment")
    pt_d: dict[str, int] = {}
    ox_d: dict[str, int] = {}
    ayni = 0
    n = 0
    for p in kareler:
        bgr = cv2.imread(str(p))
        if bgr is None:
            continue
        _, d1 = zincir(m_pt, bgr, imgsz, conf, "0")
        _, d2 = zincir(m_ox, bgr, imgsz, conf, None)
        pt_d[d1] = pt_d.get(d1, 0) + 1
        ox_d[d2] = ox_d.get(d2, 0) + 1
        ayni += int(d1 == d2)
        n += 1
    cesit = len([k for k, v in pt_d.items() if v > 0])
    return {"kare": n, "ayni_karar": ayni, "pt_dagilim": pt_d, "onnx_dagilim": ox_d,
            "karar_cesidi": cesit,
            "gecti": n > 0 and ayni == n and cesit >= 2,
            "not": "karar_cesidi < 2 ise parite BOS-DOGRU olabilir"}


def main() -> int:
    a = argparse.ArgumentParser(description="v21 kapilari + ONNX + Jetson paketi")
    a.add_argument("--agirlik", type=Path, default=VARSAYILAN_AGIRLIK)
    a.add_argument("--ad", default="navitas_seg_v21_best")
    a.add_argument("--imgsz", type=int, default=640)
    a.add_argument("--conf", type=float, default=0.25)
    a.add_argument("--cihaz", default="0")
    a.add_argument("--zorla", action="store_true", help="kapi dusse de paketle")
    args = a.parse_args()

    if not args.agirlik.is_file():
        print(f"HATA: agirlik yok: {args.agirlik}", file=sys.stderr)
        print("Egitim bitmemis olabilir.", file=sys.stderr)
        return 2

    damga = datetime.now().strftime("%Y%m%d_%H%M%S")
    cikti = KOK / "results" / f"v21_degerlendirme_{damga}"
    cikti.mkdir(parents=True, exist_ok=True)
    print(f"Agirlik : {args.agirlik}")
    print(f"Cikti   : {cikti}\n")

    model = YOLO(str(args.agirlik), task="segment")

    print("KAPI 1/2 — GERCEK NADIR KARE (ARCHITECT_PLAN K-8)")
    k1 = kapi_gercek_kare(model, args.conf, args.imgsz, args.cihaz)
    print(f"  kullanilabilir : {k1['kullanilabilir']}/{k1['kare']}  "
          f"(v17 referansi: {V17_REFERANS})")
    print(f"  ort zemin      : %{k1['ort_zemin_yuzde']}")
    print(f"  rota durumlari : {k1['rota_durumlari']}")
    print(f"  KAPI: {'GECTI' if k1['gecti'] else 'DUSTU'}\n")

    print("KAPI 2/2 — ARENA")
    k2 = kapi_arena(model, args.conf, args.imgsz, args.cihaz)
    if k2.get("durum") == "ATLANDI":
        print(f"  ATLANDI: {k2['sebep']}\n")
    else:
        print(f"  MASKE_YOK      : %{k2['maske_yok_yuzde']}")
        print(f"  ort zemin      : %{k2['ort_zemin_yuzde']}")
        print(f"  rota durumlari : {k2['rota_durumlari']}")
        print(f"  KAPI: {'GECTI' if k2['gecti'] else 'DUSTU'}\n")

    kapilar_gecti = k1["gecti"] and k2.get("gecti", False)
    rapor = {"agirlik": str(args.agirlik), "zaman": damga,
             "kapi_gercek_kare": k1, "kapi_arena": k2,
             "kapilar_gecti": bool(kapilar_gecti)}

    if not kapilar_gecti and not args.zorla:
        (cikti / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        print("=" * 64)
        print("PAKET GUNCELLENMEDI — kapi dustu.")
        print("v21 pakete girmiyor; v17/v20 paketteki haliyle kaliyor.")
        print(f"Rapor: {cikti / 'rapor.json'}")
        print("Yine de paketlemek istersen: --zorla")
        return 1

    print("ONNX export")
    onnx = onnx_uret(args.agirlik, cikti, args.imgsz)
    if onnx is None:
        rapor["onnx"] = "BASARISIZ"
        (cikti / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        return 1
    print(f"  -> {onnx.name}\n")

    print("PARITE — PT vs ONNX ayni karar mi")
    par = parite(args.agirlik, onnx, args.imgsz, args.conf)
    print(f"  ayni karar   : {par['ayni_karar']}/{par['kare']}")
    print(f"  karar cesidi : {par['karar_cesidi']}  ({par['not']})")
    print(f"  PT   : {par['pt_dagilim']}")
    print(f"  ONNX : {par['onnx_dagilim']}")
    print(f"  KAPI: {'GECTI' if par['gecti'] else 'DUSTU'}\n")
    rapor["parite"] = par

    if not par["gecti"] and not args.zorla:
        (cikti / "rapor.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=2),
                                          encoding="utf-8")
        print("PAKET GUNCELLENMEDI — ONNX paritesi dustu.")
        return 1

    print("JETSON PAKETI GUNCELLENIYOR")
    hedef_onnx = PAKET / "models" / f"{args.ad}_{args.imgsz}_fp16.onnx"
    hedef_pt = PAKET / "models" / f"{args.ad}.pt"
    shutil.copy2(onnx, hedef_onnx)
    shutil.copy2(args.agirlik, hedef_pt)
    print(f"  + {hedef_onnx.name}")
    print(f"  + {hedef_pt.name}")

    (PAKET / "V21_KAPI_RAPORU.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    (cikti / "rapor.json").write_text(
        json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  + V21_KAPI_RAPORU.json")
    print("\n" + "=" * 64)
    print("TAMAM. Jetson'da derleme komutu:")
    print(f"  yolo export model={hedef_onnx.name} format=engine imgsz={args.imgsz} half=True")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
