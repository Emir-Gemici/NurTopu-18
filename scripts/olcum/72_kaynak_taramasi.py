"""HAKEM EKRANININ HER KAYNAGINDA NE OLUYOR? — kaynak kaynak ret dokumu.

NEDEN. Kullanici bildirdi: "`arena_kadraj` dogru calisiyor ama digerlerinde
duzgun yol bulmuyor." Bu ifadeyi TAHMINLE degil OLCUMLE karsilamak gerekir:
her kaynakta rota neden cikmiyor, ayni sebep mi, farkli mi?

Ekranin kaynak listesi `comms/yks_gui.py:_algi_gorseller` ile BIREBIR ayni
tutulur; burada ayri bir liste TANIMLANMAZ (madde 16 ruhu).

Her kaynak icin ornek kareler kosulur ve `analyze_path`in RET SEBEBI sayilir.
Olcek, kaynagin kendi manifestinden gelir; manifest yoksa OLCEK YOKTUR ve
bu, ret sebebi olarak AYRICA raporlanir — cunku olceksizken C-uzayi kosamaz
ve bu, modelin degil VERININ eksigidir.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import rota_olcek_reddi                # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

CONF = 0.30
KADRAJ_KOKU = Path(r"O:\navitas-local-train\calisma\sentetik_arena_kadraj_t66")


def kaynaklar():
    """`yks_gui._algi_gorseller` ile AYNI eslesme."""
    return {
        "kompozit":     REPO / "data" / "arena_kompozit" / "images",
        "arena_kadraj": KADRAJ_KOKU / "images",
        "arena_gercek": REPO / "data" / "arena_referans" / "sartname_s9_arena.png",
        "gemini":       REPO / "test_images" / "gemini",
        "test":         REPO / "test_images" / "test" / "images",
        "val":          REPO / "dataset" / "rescuenet_yolo" / "images" / "val",
        "drone":        REPO / "data" / "raw_frames",
    }


def kareler(yol, azami):
    uz = (".png", ".jpg", ".jpeg")
    if yol.is_file():
        return [yol] if yol.suffix.lower() in uz else []
    if not yol.is_dir():
        return []
    hepsi = sorted(p for p in yol.rglob("*") if p.suffix.lower() in uz)
    adim = max(1, len(hepsi) // azami)
    return hepsi[::adim][:azami]


def manifest_mpp(kok):
    """Kumenin manifestinden {dosya_adi: mpp}. Manifest yoksa bos."""
    for aday in (kok / "manifest.json", kok.parent / "manifest.json"):
        if aday.is_file():
            try:
                man = json.loads(aday.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                return {}
            d = {}
            for o in man.get("ornekler", []):
                a = o.get("arena") or {}
                if o.get("cikti") and a.get("mpp"):
                    d[Path(o["cikti"]).name] = a["mpp"]
            return d
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--azami", type=int, default=12, help="kaynak basina kare")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    ozet = {}
    print(f"\n{'=' * 76}\nKAYNAK TARAMASI · {args.model.name}\n{'=' * 76}")
    for ad, yol in kaynaklar().items():
        kar = kareler(yol, args.azami)
        if not kar:
            print(f"\n### {ad:<14} — KARE YOK ({yol})")
            ozet[ad] = {"n": 0}
            continue
        mpp_ile = manifest_mpp(yol if yol.is_dir() else yol.parent)
        sebep = Counter()
        rota = 0
        kaplamalar = []
        for p in kar:
            img = cv2.imread(str(p))
            if img is None:
                continue
            mpp = mpp_ile.get(p.name)
            sq, small, ic = _preprocess(img)
            r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), ic)
            x0, y0, cw, ch = ic
            kaplamalar.append(float((mk[0][y0:y0+ch, x0:x0+cw] > 0).mean()))
            _y, _g, wps, _k, red, _o = analyze_path(
                mk[0], icerik=ic, engel_mask=mk[1], mpp=mpp,
                return_clean=True, return_reason=True, return_olcum=True)
            s = red[0] if isinstance(red, tuple) else red
            # ⚠ OLCEK KAPISI AYRI BIR HALKADIR (CONTRACTS SS11.3 Halka 5) ve
            # `analyze_path`in ICINDE degildir. Ilk surumde cagrilmadi ve
            # olceksiz kareler "ROTA VAR" sayildi — oysa hakem ekrani onlari
            # OLCEK_YOK ile REDDEDIYOR (gorsel olarak dogrulandi). Uretimin
            # yaptigi kontrolu atlayan bir olcum, uretimi olcmez.
            olcek_red = rota_olcek_reddi(mpp)
            if olcek_red is not None:
                s = olcek_red[0] if isinstance(olcek_red, tuple) else olcek_red
                sebep[s] += 1
                continue
            if red is None and wps:
                rota += 1
                sebep["ROTA VAR"] += 1
            else:
                sebep[s or "SEBEPSIZ"] += 1
        n = sum(sebep.values())
        km = sorted(kaplamalar)[len(kaplamalar)//2] if kaplamalar else 0.0
        olcekli = sum(1 for p in kar if p.name in mpp_ile)
        print(f"\n### {ad:<14} n={n:<4} ROTA {rota}/{n}   "
              f"olcek MANIFESTTE {olcekli}/{n}   zemin kaplamasi ~%{100*km:.0f}")
        for s, c in sebep.most_common():
            print(f"      {c:4d}  {s}")
        ozet[ad] = {"n": n, "rota": rota, "olcekli": olcekli,
                    "kaplama_medyan": km, "sebepler": dict(sebep)}
    print(f"\n{'=' * 76}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"model": str(args.model), "kaynaklar": ozet},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
