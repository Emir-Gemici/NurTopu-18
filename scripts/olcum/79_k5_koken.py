"""K5 NEDEN DUSTU? — v30 <-> v33 kare kare KOKEN TESHISI.

NEDEN (REVIEW_LOG D-148, "DOGRULANAMADI #1"). v33 gurultu dayanikliligi
egitimi kararliligi 8/260'tan 3/260'a indirdi ama K5'ten dustu: `sa_000131`
karesinde IKA govdesi bariyerle **2 px** kesisiyor (v30: 0 px). D-148'de bunun
kokeni icin "gurultu augmentasyonunun maskeyi bir yerde genislettigi TAHMIN
ediliyor" yazildi — TAHMIN, olcum degil. Bu betik tahmini olcumle degistirir.

K5'in tanimi `66_k5_bariyer_populasyon.py`den AYNEN alinir (yeniden yazilmaz):
    kesisim = (r_gerekli_px ile kalinlastirilmis rota) ∩ (bariyer kolu)
Bariyer dedektoru MODELDEN BAGIMSIZDIR (`63_bariyer_kesisimi.bariyer_maskesi`,
LAB a* esigi). Yani iki model arasindaki TEK fark SEGMENTASYON MASKELERIDIR.

AYIRT EDILEN HIPOTEZLER (kare basina, ikisi de dogrudan olculur):

  H1 · ROTA TASINDI. v33 rotayi BASKA bir koridordan gecirdi; yeni koridor
       bariyere daha yakin. Isaret: serit / waypoint geometrisi farkli.

  H2 · BARIYER DUYARLILIGI DUSTU. Model bariyerin bir kismini `blocked`
       saymayi birakti; engel cikarilmayinca serbest alan bariyerin USTUNE
       tasti ve rota oradan siyirdi. Isaret: `blocked` maskesinin bariyer
       pikselleri uzerindeki kapsamasi v33'te DUSUK, ve/veya `traversable`
       maskesi bariyer uzerinde v33'te DAHA GENIS.

Ikisi ayni anda da olabilir; olcum ikisini de sayar ve HANGISININ kesisim
bolgesinde gecerli oldugunu gosterir.

⚠ Bu betik KARAR VERMEZ, olcer. K5 esigi (0 px) D-107'dedir ve gevsetilmez.
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

from costmap_path_finder import R_GEREKLI_M                     # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

bariyer_maskesi = import_module("63_bariyer_kesisimi").bariyer_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
CONF = 0.30


def olc(model, img, mpp):
    """66'nin K5 hesabinin BIREBIR aynisi + koken icin ek alanlar."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    trav, blok = mk[0], mk[1]

    kol, kutular = bariyer_maskesi(img)
    x0, y0, cw, ch = icerik
    kol_t = np.zeros((h, w), np.uint8)
    kol_t[y0:y0 + ch, x0:x0 + cw] = cv2.resize(
        kol, (cw, ch), interpolation=cv2.INTER_NEAREST)
    ust = kol_t > 0

    yol, guven, wps, temiz, red, olcum = analyze_path(
        trav, icerik=icerik, engel_mask=blok, mpp=mpp,
        return_clean=True, return_reason=True, return_olcum=True)
    olcum = olcum or {}

    d = {
        "serit": yol, "red": red[0] if isinstance(red, tuple) else red,
        "guven": guven, "wps": [(int(a), int(b)) for a, b in (wps or [])],
        "darbogaz_px": olcum.get("darbogaz_px"),
        "r_gerekli_px": olcum.get("r_gerekli_px"),
        "bariyer_px": int(ust.sum()),
        # H2 olcutleri — hepsi BARIYER PIKSELLERI uzerinde:
        "duyarlilik": float((blok[ust] > 0).mean()) if ust.any() else None,
        "trav_bariyer_uzerinde": int((trav[ust] > 0).sum()) if ust.any() else 0,
        "serbest_bariyer_uzerinde": int((temiz[ust] > 0).sum())
        if (temiz is not None and ust.any()) else None,
        "kesisim_px": 0, "kesisim_merkezi": None,
    }

    if red is None and wps:
        r_px = max(1, int(round(R_GEREKLI_M / mpp)))
        iz = np.zeros((h, w), np.uint8)
        pts = [(int(round(x)), int(round(y))) for x, y in wps]
        for a, b in zip(pts, pts[1:]):
            cv2.line(iz, a, b, 1, 2)
        iz = cv2.dilate(iz, cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (2 * r_px + 1, 2 * r_px + 1)))
        kes = (iz > 0) & ust
        d["r_px"] = r_px
        d["kesisim_px"] = int(kes.sum())
        if kes.any():
            ys, xs = np.nonzero(kes)
            d["kesisim_merkezi"] = (int(xs.mean()), int(ys.mean()))
            d["kesisim_kutusu"] = (int(xs.min()), int(ys.min()),
                                   int(xs.max()), int(ys.max()))
    d["_temiz"] = temiz
    d["_ust"] = ust
    d["_trav"] = trav
    d["_blok"] = blok
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", type=Path, required=True, help="taban model (v30)")
    ap.add_argument("--b", type=Path, required=True, help="sinanan model (v33)")
    ap.add_argument("--kare", action="append", default=None,
                    help="incelenecek kare adi; verilmezse TUM bariyerli kareler")
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    # K5 = 0 px bir SINIR olcutudur; taban modelin 0 cikmasi o karenin GUVENLI
    # oldugu anlamina gelmez, yalnizca O CEKIMDE kesismedigi anlamina gelir.
    # Ayni gurultuyu (68'in recetesi) bindirip iki modelin de K5'ini tekrar
    # tekrar olcmek, esigin PAYLA mi yoksa SANSLA mi gecildigini gosterir.
    ap.add_argument("--tekrar", type=int, default=0,
                    help="kare basina gurultulu tekrar (0 = yalniz temiz kosu)")
    ap.add_argument("--sigma", type=float, default=2.0,
                    help="Gauss gurultu sigmasi 0-255 olceginde (68 ile ayni)")
    ap.add_argument("--tohum", type=int, default=7)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    ma = YOLO(str(args.a), task="segment")
    mb = YOLO(str(args.b), task="segment")

    hedefler = set(args.kare) if args.kare else None
    kayitlar = []
    rng = np.random.default_rng(args.tohum)
    gurultu_ozeti = []
    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        if not p.is_file():
            continue
        if hedefler and p.name not in hedefler:
            continue
        mpp = ornek["arena"].get("mpp")
        if not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        kol, kutular = bariyer_maskesi(img)
        if not kutular:
            continue

        A = olc(ma, img, mpp)
        B = olc(mb, img, mpp)
        # ⚠ `--tekrar` verildiginde bu atlama YAPILMAZ: temiz kosuda 0 px veren
        # kare tam da gurultu altinda sinanmasi gereken karedir (sa_000131'de
        # v30 temiz kosuda 0, gurultulu kosularin 3/20'sinde 2 px verdi).
        if (args.tekrar == 0 and hedefler is None
                and A["kesisim_px"] == 0 and B["kesisim_px"] == 0):
            continue                       # ilginc olmayan kareyi basma

        ust = A["_ust"]
        # H2'nin KESISIM BOLGESINDE gecerli olup olmadigi: kesisim kutusunun
        # civarinda iki modelin bariyer uzerindeki serbest alani.
        yerel = {}
        kutu = B.get("kesisim_kutusu") or A.get("kesisim_kutusu")
        if kutu:
            x0, y0, x1, y1 = kutu
            pay = 40
            dilim = (slice(max(0, y0 - pay), y1 + pay + 1),
                     slice(max(0, x0 - pay), x1 + pay + 1))
            u = ust[dilim]
            for ad, M in (("v30", A), ("v33", B)):
                yerel[ad] = {
                    "bariyer_px": int(u.sum()),
                    "blocked_kapsama": float((M["_blok"][dilim][u] > 0).mean())
                    if u.any() else None,
                    "trav_bariyer_uzerinde": int((M["_trav"][dilim][u] > 0).sum()),
                    "serbest_bariyer_uzerinde": int((M["_temiz"][dilim][u] > 0).sum())
                    if M["_temiz"] is not None else None,
                }

        kayit = {"kare": p.name, "mpp": mpp,
                 "v30": {k: v for k, v in A.items() if not k.startswith("_")},
                 "v33": {k: v for k, v in B.items() if not k.startswith("_")},
                 "yerel": yerel}

        # ── GURULTU ALTINDA K5 ──────────────────────────────────────────────
        # AYNI gurultu ornegi IKI modele de verilir (eslestirilmis olcum);
        # aksi halde fark modelden mi cekilisten mi gelir ayirt edilemez.
        if args.tekrar > 0:
            tur = {"v30": [], "v33": []}
            for _ in range(args.tekrar):
                g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
                gimg = np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)
                for ad, mm in (("v30", ma), ("v33", mb)):
                    r = olc(mm, gimg, mpp)
                    tur[ad].append({"kesisim_px": r["kesisim_px"],
                                    "darbogaz_px": r["darbogaz_px"],
                                    "serit": r["serit"], "red": r["red"]})
            kayit["gurultu"] = tur
            gurultu_ozeti.append((p.name, tur))

        kayitlar.append(kayit)

        c = "=" * 76
        print(f"\n{c}\n{p.name}   mpp={mpp:.5f}\n{c}")
        print(f"{'olcut':<34}{'v30':>20}{'v33':>20}")
        for etiket, anahtar in (
                ("serit (road)", "serit"), ("red sebebi", "red"),
                ("darbogaz_px", "darbogaz_px"), ("r_gerekli_px", "r_gerekli_px"),
                ("bariyer piksel sayisi", "bariyer_px"),
                ("bariyer DUYARLILIGI (blocked)", "duyarlilik"),
                ("trav maskesi bariyer USTUNDE", "trav_bariyer_uzerinde"),
                ("SERBEST alan bariyer USTUNDE", "serbest_bariyer_uzerinde"),
                ("KESISIM px", "kesisim_px"),
                ("kesisim merkezi", "kesisim_merkezi")):
            va, vb = A.get(anahtar), B.get(anahtar)
            f = (lambda v: f"{v:.4f}" if isinstance(v, float) else str(v))
            print(f"{etiket:<34}{f(va):>20}{f(vb):>20}")

        # ROTA TASINDI MI (H1)?
        wa, wb = A["wps"], B["wps"]
        if wa and wb:
            n = min(len(wa), len(wb))
            sapma = [abs(wa[i][0] - wb[i][0]) + abs(wa[i][1] - wb[i][1])
                     for i in range(n)]
            print(f"\n  H1 ROTA TASINMASI: waypoint {len(wa)} vs {len(wb)} · "
                  f"ortak {n} · L1 sapma medyan {np.median(sapma):.1f} px · "
                  f"maks {max(sapma)} px")
        else:
            print(f"\n  H1 ROTA TASINMASI: waypoint v30={len(wa)} v33={len(wb)}")

        if yerel:
            print(f"  H2 KESISIM CIVARI (kutu ± 40 px):")
            print(f"     {'olcut':<32}{'v30':>16}{'v33':>16}")
            for k in ("bariyer_px", "blocked_kapsama",
                      "trav_bariyer_uzerinde", "serbest_bariyer_uzerinde"):
                va = yerel["v30"].get(k)
                vb = yerel["v33"].get(k)
                f = (lambda v: f"{v:.4f}" if isinstance(v, float) else str(v))
                print(f"     {k:<32}{f(va):>16}{f(vb):>16}")

    if gurultu_ozeti:
        print(f"\n{'=' * 76}\nGURULTU ALTINDA K5 "
              f"(sigma={args.sigma}/255 · {args.tekrar} tekrar · ESLESTIRILMIS)"
              f"\n{'=' * 76}")
        for kare, tur in gurultu_ozeti:
            print(f"  {kare}")
            for ad in ("v30", "v33"):
                kesenler = [r["kesisim_px"] for r in tur[ad]]
                kac = sum(1 for v in kesenler if v > 0)
                bog = [r["darbogaz_px"] for r in tur[ad]
                       if r["darbogaz_px"] is not None]
                print(f"     {ad}: KESEN kosu {kac}/{len(kesenler)} · "
                      f"kesisim px {kesenler} · "
                      f"darbogaz min/maks "
                      f"{min(bog):.2f}/{max(bog):.2f}" if bog else
                      f"     {ad}: KESEN kosu {kac}/{len(kesenler)}")
        print("  OKUMA: taban modelin temiz kosuda 0 px vermesi, o karenin")
        print("  GUVENLI oldugu anlamina GELMEZ. Gurultu altinda o da kesiyorsa")
        print("  K5 esigi PAYLA degil SANSLA geciliyor demektir.")

    print(f"\n{'=' * 76}")
    print("OKUMA:")
    print("  H1 gecerliyse rota GEOMETRISI ayrisir (waypoint sapmasi buyuk).")
    print("  H2 gecerliyse v33'un `blocked` kapsamasi bariyer uzerinde DUSUK")
    print("  ve/veya SERBEST alani bariyer uzerinde GENIS olur.")
    print("  Ikisi de kucukse koken BASKA yerdedir ve oyle yazilir.")
    print("=" * 76)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(kayitlar, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
