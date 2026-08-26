"""148 — YKS GUI KAYNAK-OZEL ROTA TESHISI (ON_KAYIT §19).

Kullanicinin gozlemi: "arena_kadraj klasoru haric tum klasorleri kaynak olarak
secince guiden yol uretemiyor".

Bu betik GUI'yi ACMADAN, `comms/yks_gui.py`nin `_algi_kos` govdesindeki AYNI
uretim zincirini kaynak basina koşar ve rota uretilmeme sebebini
  (a) OLCEK_YOK  (GUI/olcek yapilandirmasi)   vs
  (b) MASKE_YOK / UC_BANT... (model)
olarak ayristirir. Kopya algoritma yoktur; GUI sinifinin kendi metodlari ve
`codes/rpi_inference.py` fonksiyonlari cagrilir.

Kullanim:
  python scripts/olcum/148_gui_kaynak_teshis.py [--kare-sayisi 12]
"""
from __future__ import annotations

import argparse
import json
import queue
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "comms"))
sys.path.insert(0, str(KOK / "codes"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402


def _kod(red):
    """Ret sebebinin KODU (tuple ise ilk oge)."""
    if red is None:
        return None
    return red[0] if isinstance(red, (tuple, list)) else str(red)


def _metin(red):
    if red is None:
        return None
    if isinstance(red, (tuple, list)):
        return " | ".join(str(x) for x in red)
    return str(red)


def _gui_ornegi(kaynak):
    """Tk penceresi ACMADAN GUI sinifinin bir ornegi (yalniz algi alanlari)."""
    import yks_gui
    o = object.__new__(yks_gui.YksArayuz)
    o.algi_kaynak = kaynak
    o.algi_model = None
    o.algi_kuyruk = queue.Queue()
    o._arac_modeli_durumu = None
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kare-sayisi", type=int, default=12)
    ap.add_argument("--kaynak", default=None, help="yalniz bu kaynak")
    ap.add_argument("--model", default=None, help="agirlik yolu (varsayilan: uretim)")
    ap.add_argument("--cikti", default="results/gece_20260826/gui_kaynak_teshis.json")
    a = ap.parse_args()

    from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp, _preprocess,
                               _rota_kararini_esikle, analyze_path, get_masks,
                               kare_olcek_kahini)
    from karar_sozlesmesi import olcek_gecerli_mi, rota_olcek_reddi
    try:
        from karar_sozlesmesi import OLCEK_KAYNAK_ARAC  # noqa: F401
    except ImportError:
        OLCEK_KAYNAK_ARAC = None
    import yks_gui
    from ultralytics import YOLO

    model_yolu = (Path(a.model).resolve() if a.model
                  else KOK / "models" / yks_gui.YksArayuz.ALGI_MODEL_DOSYA)
    model = YOLO(str(model_yolu))
    print(f"model: {model_yolu.name}", flush=True)

    rapor = {"model": model_yolu.name, "conf": yks_gui.YksArayuz.ALGI_PREDICT_CONF,
             "kare_sayisi_ust": a.kare_sayisi, "kaynaklar": {}}

    kaynaklar = ([a.kaynak] if a.kaynak else list(yks_gui.YksArayuz.ALGI_KAYNAKLAR))
    for kaynak in kaynaklar:
        o = _gui_ornegi(kaynak)
        o.algi_model = model
        try:
            gorseller = o._algi_gorseller()
        except Exception as exc:
            rapor["kaynaklar"][kaynak] = {"hata": f"{type(exc).__name__}: {exc}"}
            print(f"{kaynak}: LISTE HATASI {exc}", flush=True)
            continue
        if not gorseller:
            rapor["kaynaklar"][kaynak] = {"gorsel": 0, "not": "dizin bos/yok"}
            print(f"{kaynak}: gorsel YOK", flush=True)
            continue
        # esit araliklarla ornekle (ilk N degil — dizin basi tek sahne olabilir)
        n = min(a.kare_sayisi, len(gorseller))
        idx = [round(i * (len(gorseller) - 1) / max(1, n - 1)) for i in range(n)] if n > 1 else [0]
        secilen = [gorseller[i] for i in sorted(set(idx))]
        kareler = []
        for yol in secilen:
            img = cv2.imread(str(yol))
            if img is None:
                kareler.append({"kare": yol.name, "hata": "okunamadi"})
                continue
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            sonuc = model.predict(small, imgsz=INFER_SIZE,
                                  conf=yks_gui.YksArayuz.ALGI_PREDICT_CONF,
                                  verbose=False)
            maskeler = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
            trav, blok = maskeler[0], maskeler[1]
            try:
                beyan, olcek_notu = o._kaynak_olcegi(yol)
            except Exception as exc:
                beyan, olcek_notu = None, f"{type(exc).__name__}: {exc}"
            katman3_yasak = kaynak in yks_gui.YksArayuz.ALGI_SKALER_OLCEK_GECERSIZ
            kahin = kare_olcek_kahini(
                beyan, None, icerik, bgr=img,
                arac_modeli=(None if (olcek_gecerli_mi(beyan) or katman3_yasak)
                             else o._arac_modeli()))
            mpp = kahin["mpp"]
            olcek_reddi = rota_olcek_reddi(mpp)
            (ham_yol, guven, ham_wps, koridor, karar_reddi,
             rota_olcumu) = analyze_path(trav, icerik=icerik, engel_mask=blok,
                                         mpp=mpp, return_clean=True,
                                         return_reason=True, return_olcum=True,
                                         olcek_kaynagi=kahin["kaynak"])
            yapisal_red = karar_reddi
            if olcek_reddi is not None and karar_reddi is None:
                ham_yol, guven, ham_wps = None, 0.0, []
                karar_reddi = olcek_reddi
            yol_no, guven, wps, karar_reddi = _rota_kararini_esikle(
                ham_yol, guven, ham_wps, karar_reddi)
            kareler.append({
                "kare": yol.name,
                "yapisal_red_kod": _kod(yapisal_red),
                "karar_reddi_kod": _kod(karar_reddi),
                "beyan_mpp": beyan,
                "beyan_not": olcek_notu,
                "kahin_kaynak": kahin["kaynak"],
                "mpp": mpp,
                "zemin_px": int(np.count_nonzero(trav)),
                "engel_px": int(np.count_nonzero(blok)),
                "yapisal_red": _metin(yapisal_red),
                "olcek_reddi": _metin(olcek_reddi),
                "karar_reddi": _metin(karar_reddi),
                "yol_no": yol_no,
            })
        say = {}
        for k in kareler:
            if "hata" in k:
                s = "OKUNAMADI"
            elif k["yol_no"] is not None:
                s = "ROTA"
            else:
                s = k["karar_reddi_kod"] or "RET(sebepsiz)"
            say[s] = say.get(s, 0) + 1
        # ayristirma: olcek mi model mi
        olcek_sucu = sum(1 for k in kareler if "hata" not in k
                         and k["yol_no"] is None and k["yapisal_red"] is None
                         and k["olcek_reddi"] is not None)
        model_sucu = sum(1 for k in kareler if "hata" not in k
                         and k["yol_no"] is None and k["yapisal_red"] is not None)
        rapor["kaynaklar"][kaynak] = {
            "gorsel_toplam": len(gorseller), "olculen": len(kareler),
            "dagilim": say, "olcek_sucu": olcek_sucu, "model_sucu": model_sucu,
            "kareler": kareler,
        }
        print(f"{kaynak}: n={len(kareler)}/{len(gorseller)} {say} "
              f"| olcek_sucu={olcek_sucu} model_sucu={model_sucu}", flush=True)

    cikti = KOK / a.cikti
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(rapor, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"\nyazildi: {cikti}")


if __name__ == "__main__":
    main()
