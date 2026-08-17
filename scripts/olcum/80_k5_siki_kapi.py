"""T93 — K5 SIKI KAPI: populasyon x GURULTULU TEKRAR (tek cekilis YETMEZ).

NEDEN (REVIEW_LOG D-149). `65`/`66` K5'i kare basina TEK temiz cikarimla
olcer. `sa_000131` ise IKI MODLUDUR: kesen kosularin darbogazi {14,80},
kesmeyenlerin {15,98 · 16,00 · 17,60}. v30 kotu moda gurultulu cekilislerin
3/20'sinde duser ama temiz cekiliste dusmedi — yani kayitli `K5 = 0/173`
SAGLAM BIR OZELLIK DEGIL, o cekilise ait bir sonuctur.

Bu, K5'in olcum kusuruyla UCUNCU karsilasmasidir:
    D-114  tek kare olculuyordu
    D-115  rota 3 px'lik NOKTASAL iz olarak kalinlastiriliyordu
    D-149  tek CEKILISTE olculuyor            <- bu betik bunu kapatir

🔴 ESIK GEVSETILMIYOR. D-107'nin olcutu (kesisim = 0 px) aynen durur; degisen
yalnizca KAC CEKILISTE bakildigidir.

── D-149'DA VAR OLAN, BURADA OLMAYAN IKINCI KUSUR ──────────────────────────
D-149'un gurultu dongusu bariyer maskesini de GURULTULU goruntuden turetiyordu.
Bariyer YER GERCEGIDIR (LAB a* esigi, `63`ten ithal, MODELDEN BAGIMSIZ) ve
sensor gurultusuyle yerinden oynamamalidir. Burada bariyer TEMIZ goruntuden
BIR KEZ hesaplanir; gurultu YALNIZ modelin girdisine biner.

⚠ Bu duzeltme D-149'un sayisini degistirebilir. Degisirse oyle yazilir.

── ESLESTIRME ──────────────────────────────────────────────────────────────
Ayni gurultu ornegi IKI modele de verilir. Aksi halde iki model arasindaki
fark modelden mi cekilisten mi gelir, ayirt edilemez.

── POZITIF KONTROL ─────────────────────────────────────────────────────────
Temiz cekilisin sonucu `66_k5_bariyer_populasyon.py`nin yayimlanmis sayilarini
BIREBIR vermelidir (v30: 0/173 · v33: 1/173). Vermiyorsa olcum 66'dan
iraksamistir; betik bunu EKRANA BASAR ve sonuc "KIYASLANAMAZ" diye isaretlenir.
Olcum sozlesmesi D-139'un dersidir: uretimin/kapinin yaptigi islemi atlayan bir
olcum onu olcmez.

On kayit: `calisma/olcum/t93_on_kayit.md` (olcum kosulmadan once yazildi).
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(BURASI))

from costmap_path_finder import R_GEREKLI_M                      # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,   # noqa: E402
                           _preprocess, analyze_path, get_masks)

bariyer_maskesi = import_module("63_bariyer_kesisimi").bariyer_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
CONF = 0.30

# 66'nin yayimlanmis temiz-cekilis sayilari (pozitif kontrol icin).
BEKLENEN_TEMIZ = {"v30": 0, "v33": 1}


def bariyer_tuvalde(img, icerik, sekil):
    """Bariyeri TEMIZ goruntuden turet ve letterbox tuvaline tasi.

    `_preprocess` icerigi OLCEKLEMEDEN yerlestirir; tuval = ozgun + kaydirma.
    """
    kol, kutular = bariyer_maskesi(img)
    if not kutular:
        return None
    h, w = sekil
    x0, y0, cw, ch = icerik
    kol_t = np.zeros((h, w), np.uint8)
    kol_t[y0:y0 + ch, x0:x0 + cw] = cv2.resize(
        kol, (cw, ch), interpolation=cv2.INTER_NEAREST)
    return kol_t > 0


def k5_cekilis(model, girdi, mpp, ust, icerik, sekil):
    """TEK cekilisin K5'i. `ust` DISARIDAN gelir (temiz goruntunun bariyeri).

    Hesap `66_k5_bariyer_populasyon.py` ile AYNI: rota `r_gerekli_px` yaricapli
    elips cekirdekle kalinlastirilir ve bariyerle kesistirilir.
    """
    h, w = sekil
    _sq, small, _ic = _preprocess(girdi)
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    trav, blok = mk[0], mk[1]

    _y, guven, wps, _temiz, red, olcum = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)
    olcum = olcum or {}
    d = {"rota_var": bool(red is None and wps),
         "darbogaz_px": olcum.get("darbogaz_px"),
         "duyarlilik": float((blok[ust] > 0).mean()) if ust.any() else None,
         "kesisim_px": 0}
    if not d["rota_var"]:
        return d                       # rota yok -> kesisim TANIMSIZ (66 ile ayni)

    r_px = max(1, int(round(R_GEREKLI_M / mpp)))
    iz = np.zeros((h, w), np.uint8)
    pts = [(int(round(x)), int(round(y))) for x, y in wps]
    for a, b in zip(pts, pts[1:]):
        cv2.line(iz, a, b, 1, 2)
    iz = cv2.dilate(iz, cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * r_px + 1, 2 * r_px + 1)))
    d["kesisim_px"] = int(((iz > 0) & ust).sum())
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", action="append", required=True,
                    metavar="AD=YOL", help="or. v30=O:\\...\\best.pt (>=1 kez)")
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--tekrar", type=int, default=20)
    ap.add_argument("--sigma", type=float, default=2.0)
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    modeller = {}
    from ultralytics import YOLO
    for m in args.model:
        ad, _, yol = m.partition("=")
        if not yol:
            raise SystemExit(f"--model AD=YOL bekleniyor, gelen: {m}")
        modeller[ad] = YOLO(yol, task="segment")
    adlar = list(modeller)

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    rng = np.random.default_rng(args.tohum)

    kayitlar = []
    olculen = 0
    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        mpp = ornek["arena"].get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        _sq, _small, icerik = _preprocess(img)
        sekil = _sq.shape[:2]
        ust = bariyer_tuvalde(img, icerik, sekil)
        if ust is None or not ust.any():
            continue                   # bariyersiz kare K5'e girmez
        olculen += 1

        # Cekilisler ONCE uretilir; ayni ornek TUM modellere verilir.
        girdiler = [img]
        for _ in range(args.tekrar):
            g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
            girdiler.append(
                np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8))

        kare = {"kare": p.name, "mpp": mpp, "bariyer_px": int(ust.sum()),
                "modeller": {}}
        for ad in adlar:
            kare["modeller"][ad] = [
                k5_cekilis(modeller[ad], gi, mpp, ust, icerik, sekil)
                for gi in girdiler]
        kayitlar.append(kare)
        if olculen % 20 == 0:
            print(f"  ... {olculen} kare", flush=True)

    # ── COZUMLEME ──────────────────────────────────────────────────────────
    c = "=" * 78
    print(f"\n{c}\nK5 SIKI KAPI (T93) · populasyon x gurultulu tekrar\n"
          f"  kume {args.kume.name} · kare {olculen} · "
          f"cekilis 1 temiz + {args.tekrar} gurultulu · sigma={args.sigma}/255\n"
          f"  bariyer TEMIZ goruntuden (yer gercegi) · cekilisler ESLESTIRILMIS\n{c}")

    ozet = {}
    for ad in adlar:
        temiz_kesen = sum(1 for k in kayitlar
                          if k["modeller"][ad][0]["kesisim_px"] > 0)
        kare_kesen = sum(1 for k in kayitlar
                         if any(r["kesisim_px"] > 0 for r in k["modeller"][ad]))
        cift_kesen = sum(1 for k in kayitlar for r in k["modeller"][ad]
                         if r["kesisim_px"] > 0)
        cift_top = sum(len(k["modeller"][ad]) for k in kayitlar)
        ozet[ad] = {"temiz_kesen": temiz_kesen, "kare_kesen": kare_kesen,
                    "cift_kesen": cift_kesen, "cift_toplam": cift_top}

    print(f"{'model':<8}{'TEMIZ cekilis':>16}{'HERHANGI cekilis':>20}"
          f"{'(kare,cekilis) cifti':>24}{'K5-SIKI':>10}")
    for ad in adlar:
        o = ozet[ad]
        print(f"{ad:<8}{o['temiz_kesen']:>10}/{olculen:<5}"
              f"{o['kare_kesen']:>14}/{olculen:<5}"
              f"{o['cift_kesen']:>17}/{o['cift_toplam']:<6}"
              f"{'GECER' if o['kare_kesen'] == 0 else 'DUSER':>10}")

    # POZITIF KONTROL — temiz cekilis 66 ile ayni mi?
    print(f"\n{'-' * 78}\nPOZITIF KONTROL (temiz cekilis, 66'nin yayimlanmis sayisi):")
    kiyaslanabilir = True
    for ad in adlar:
        bek = BEKLENEN_TEMIZ.get(ad)
        got = ozet[ad]["temiz_kesen"]
        if bek is None:
            print(f"  {ad}: beklenen sayi kayitli DEGIL — kontrol edilemedi")
            continue
        ok = (got == bek)
        kiyaslanabilir &= ok
        print(f"  {ad}: beklenen {bek} · olculen {got} · "
              f"{'TUTTU' if ok else 'IRAKSADI'}")
    if not kiyaslanabilir:
        print("  🔴 IRAKSAMA VAR — bu kosu 66 ile KIYASLANAMAZ. Once sebebi bulun.")

    # IKI MODLU KARELER
    print(f"\n{'-' * 78}\nKESEN KARELER — cekilis basina oran (IKI MODLU olanlar gorunur olsun):")
    for k in kayitlar:
        satir = []
        for ad in adlar:
            n = sum(1 for r in k["modeller"][ad] if r["kesisim_px"] > 0)
            if n:
                satir.append(f"{ad} {n}/{len(k['modeller'][ad])}")
        if satir:
            bog_kes, bog_temiz = set(), set()
            for ad in adlar:
                for r in k["modeller"][ad]:
                    if r["darbogaz_px"] is None:
                        continue
                    (bog_kes if r["kesisim_px"] > 0 else bog_temiz).add(
                        round(float(r["darbogaz_px"]), 2))
            print(f"  {k['kare']:<18}{' · '.join(satir)}")
            print(f"      darbogaz  KESEN={sorted(bog_kes)}  "
                  f"KESMEYEN={sorted(bog_temiz)}")

    print(f"\n{c}")
    print("OKUMA: 'HERHANGI cekilis' sutunu SIKI kapidir. Tek temiz cekiliste")
    print("0 cikan bir model burada duserse, eski K5 sonucu SANSLA gecmistir.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"kume": str(args.kume), "kare": olculen, "tekrar": args.tekrar,
             "sigma": args.sigma, "tohum": args.tohum,
             "modeller": {a: str(m.ckpt_path) if hasattr(m, "ckpt_path") else a
                          for a, m in modeller.items()},
             "ozet": ozet, "kayitlar": kayitlar},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
