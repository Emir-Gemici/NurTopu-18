"""T106 · GUVEN BANDI SIKISMASI KABUL KUMESINDE DE VAR MI? (YALNIZ OLCUM)

SORU (D-183'un acik biraktigi tek soru). v34, sartname figurunde zemini
%7,96 -> %0,49'a dusuruyordu; sebebi olculdu: KORLUK DEGIL, GUVEN COKUSU.
Tahminler kaybolmuyor, uretim esiginin (0,30) ALTINDA duruyor:

    model  conf    ZEMIN    ENGEL   toplam
    v30    0,30    7,96%    1,61%    9,56%
    v30    0,10   10,62%    4,84%   15,46%
    v34    0,30    0,49%    3,74%    4,24%
    v34    0,10   13,29%   27,34%   40,63%

D-183 §DOGRULANAMADI bunu acikca birakti: **bu sikisma yalniz o figure mi
ozgu, yoksa KABUL KUMESINDE de var mi?** Bu betik onu olcer.

    BAND_ORANI = toplam_kaplama(conf=0,10) / toplam_kaplama(conf=0,30)

Figurde v34 icin ~9,6 · v30 icin ~1,6 (yukaridaki tablodan dogrudan cikar:
40,63/4,24 = 9,58 ve 15,46/9,56 = 1,62 — yani olcut TOPLAM kaplama uzerinden
tanimlidir, zemin uzerinden degil).

────────────────────────────────────────────────────────────────────────────
🔴 OLCUM SOZLESMESI (D-139). Kaplama, `65_kabul_denetcisi.kaplama()` ile AYNI
yoldan hesaplanir: `_preprocess` -> `predict(imgsz=INFER_SIZE, conf=...)` ->
`get_masks` -> `_maskeleri_icerige_kirp`. Metrik YENIDEN YAZILMADI; 65 modulu
ICE AKTARILIR ve onun `kaplama`si bir POZITIF KONTROL olarak kullanilir:

    benim zemin(conf=0,30)  ==  65_kabul_denetcisi.kaplama(model, kare)

Esitlik her kosuda sinanir; tutmazsa OLCUM GECERSIZ sayilir. Iki farkim var
ve ikisi de gereklidir: (1) `conf` parametreli, (2) ZEMIN ve ENGEL ayri ayri.

⚠ Her esik icin AYRI `predict` kosulur. `get_masks(min_conf=...)` ile tek
cikarimdan suzmek mumkundur ama NMS'e giren kutu kumesi degisir; `kaplama()`
her cagrida kendi `conf`uyla `predict` eder ve olcum ONA denk olmalidir.
────────────────────────────────────────────────────────────────────────────

KUMELER — yollar `65_kabul_denetcisi.py`den alinir, CIPLAK YAZILMAZ:
  · FIGUR       : modulun `FIGUR` sabiti (pozitif kontrol)
  · kadraj_t66  : modulun `KADRAJ` sabiti — KABUL KUMESI (n=260)
  · raw_frames  : `REPO/data/raw_frames` · `*.jpg`   (65:73)
  · copy_paste  : `REPO/dataset/copy_paste_gercek/images/train` · `*.jpg` (65:74)

⚠ 65 K0 kontrolunde bu iki kumeden 8'er kare ORNEKLER; bu betik VARSAYILAN
OLARAK HEPSINI kullanir (67 ve 393) — ayni kaynak, daha cok kare. Fark
bilerektir ve raporda yazilidir.

⚠ YORUM SINIRI (emir): "v34 iyi/kotu" HUKMU VERILMEZ · esik degisikligi
ONERILMEZ (T110 mimarda) · gercek arena karesi YOK, "sahada soyle olur"
DENMEZ (D-88/D-99 kalici kisiti).
"""
import argparse
import importlib.util
import json
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

# `65_kabul_denetcisi` rakamla basladigi icin normal `import` ile alinamaz.
_spec = importlib.util.spec_from_file_location(
    "kabul_denetcisi", BURASI / "65_kabul_denetcisi.py")
K65 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K65)

ESIKLER = [0.30, 0.20, 0.10, 0.05]

# ⚠ Uretim modeli CIPLAK SABIT DEGILDIR (madde 16) — kayit defterinden cozulur.
# v30 TARIHSEL kiyas agirligidir; adi 48_arena_iou.py'deki KISAYOL kalibiyla
# acikca yazilir (o bir surum kaydidir, uretim bildirimi degil).
MODELLER = {
    "uretim": uretim_pt(),
    "v30": REPO / "models" / "navitas_seg_v30_best.pt",
}


def kaplamalar(model, p, conf):
    """`65_kabul_denetcisi.kaplama()` ile AYNI yol; farki: `conf` parametreli
    ve ZEMIN/ENGEL ayri doner. -> (zemin, engel) ya da None."""
    img = cv2.imread(str(p))
    if img is None:
        return None
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    return float((mk[0] > 0).mean()), float((mk[1] > 0).mean())


def kume_kareleri(args):
    """Kume adi -> kare yollari. Yollar 65'ten TURETILIR."""
    kumeler = {}

    # KABUL KUMESI — manifestten (diger olcum betikleriyle ayni suzgec)
    man_yolu = K65.KADRAJ / "manifest.json"
    kareler = []
    if man_yolu.is_file():
        man = json.loads(man_yolu.read_text(encoding="utf-8"))
        for o in man["ornekler"]:
            if o.get("durum") != "YAZILDI" or not o.get("arena"):
                continue
            p = K65.KADRAJ / o["cikti"]
            if p.is_file():
                kareler.append(p)
    kumeler["kadraj_t66"] = kareler[:args.sinir] if args.sinir else kareler

    # 65:73-74 ile AYNI kokler ve desenler
    for ad, kok, desen in (
            ("raw_frames", REPO / "data" / "raw_frames", "*.jpg"),
            ("copy_paste",
             REPO / "dataset" / "copy_paste_gercek" / "images" / "train",
             "*.jpg")):
        ys = sorted(kok.rglob(desen))
        if args.ornek:                      # 65'in K0 ornekleme kalibi
            ys = ys[::max(1, len(ys) // args.ornek)][:args.ornek]
        kumeler[ad] = ys[:args.sinir] if args.sinir else ys
    return kumeler


def med(xs):
    xs = [x for x in xs if x is not None]
    return float(statistics.median(xs)) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modeller", nargs="+", default=["v30", "uretim"])
    ap.add_argument("--ornek", type=int, default=0,
                    help="raw_frames/copy_paste'ten N kare ornekle (65 K0 "
                         "kalibi 8'dir); 0 = HEPSI")
    ap.add_argument("--sinir", type=int, default=0, help="kume basina ilk N kare")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    kumeler = kume_kareleri(args)

    kayit = {
        "betik": Path(__file__).name, "esikler": ESIKLER,
        "olcut": "BAND_ORANI = toplam_kaplama(0.10) / toplam_kaplama(0.30); "
                 "toplam = zemin + engel (D-183 tablosunun kendi toplami)",
        "kume": {ad: {"n": len(ys),
                      "kaynak": str(ys[0].parent) if ys else None}
                 for ad, ys in kumeler.items()},
        "kapsam_notu": ("TUM KUMELER SENTETIK ya da OTOPARK/FIGUR kaynaklidir; "
                        "GERCEK ARENA KARESI YOKTUR (D-88/D-99)."),
        "figur": {}, "kumeler": {}, "kontrol": {},
    }

    print(f"\n{'=' * 78}\nT106 · GUVEN BANDI SIKISMASI — kabul kumesinde de var mi?")
    print(f"  esikler {ESIKLER} · toplam = zemin + engel\n{'=' * 78}")
    for ad, ys in kumeler.items():
        print(f"  {ad:12s} n={len(ys)}")

    kontrol_sapma = []
    for m_ad in args.modeller:
        yol = MODELLER.get(m_ad, Path(m_ad))
        if not Path(yol).exists():
            print(f"\n{m_ad}: agirlik yok ({yol}) — ATLANIYOR")
            continue
        model = YOLO(str(yol), task="segment")

        # ── POZITIF KONTROL: FIGUR, D-183 sayilarini yeniden uretiyor mu ──
        figur = {}
        for e in ESIKLER:
            z, g = kaplamalar(model, K65.FIGUR, e)
            figur[f"{e:.2f}"] = {"zemin": z, "engel": g, "toplam": z + g}
        kayit["figur"][m_ad] = figur

        # 65'in KENDI `kaplama`si ile esitlik (conf 0,30, zemin)
        ref = K65.kaplama(model, K65.FIGUR)
        benim = figur["0.30"]["zemin"]
        if ref is None or abs(ref - benim) > 1e-9:
            kontrol_sapma.append(f"{m_ad}/figur ref={ref} benim={benim}")

        print(f"\n{'=' * 78}\n{m_ad}  ({Path(yol).name})\n{'=' * 78}")
        print("  POZITIF KONTROL — sartname figuru (D-183 ile kiyaslanabilir)")
        print(f"    {'conf':>6}{'ZEMIN':>10}{'ENGEL':>10}{'toplam':>10}")
        for e in ESIKLER:
            f = figur[f"{e:.2f}"]
            print(f"    {e:>6.2f}{100 * f['zemin']:>9.2f}%"
                  f"{100 * f['engel']:>9.2f}%{100 * f['toplam']:>9.2f}%")
        fb = (figur["0.10"]["toplam"] / figur["0.30"]["toplam"]
              if figur["0.30"]["toplam"] > 0 else None)
        print(f"    BAND_ORANI (figur) = {fb:.2f}" if fb else
              "    BAND_ORANI (figur) = TANIMSIZ (payda 0)")

        # ── KUMELER ───────────────────────────────────────────────────────
        kayit["kumeler"].setdefault(m_ad, {})
        print(f"\n  {'kume':12s}{'conf':>6}{'zemin_ort':>11}{'engel_ort':>11}"
              f"{'toplam_ort':>12}{'zemin<%1':>10}")
        for k_ad, ys in kumeler.items():
            if not ys:
                continue
            satirlar, ozet = [], {}
            for e in ESIKLER:
                zs, gs = [], []
                for p in ys:
                    r = kaplamalar(model, p, e)
                    if r is None:
                        continue
                    zs.append(r[0])
                    gs.append(r[1])
                    satirlar.append({"goruntu_adi": p.name, "model": m_ad,
                                     "kume": k_ad, "conf": e,
                                     "zemin": r[0], "engel": r[1],
                                     "toplam": r[0] + r[1]})
                z_ort = float(np.mean(zs)) if zs else 0.0
                g_ort = float(np.mean(gs)) if gs else 0.0
                ozet[f"{e:.2f}"] = {
                    "n": len(zs), "zemin_ort": z_ort, "engel_ort": g_ort,
                    "toplam_ort": z_ort + g_ort,
                    "zemin_medyan": med(zs), "engel_medyan": med(gs),
                    "zemin_altinda_yuzde1": sum(1 for z in zs if z < 0.01),
                }
                o = ozet[f"{e:.2f}"]
                print(f"  {k_ad:12s}{e:>6.2f}{100 * o['zemin_ort']:>10.2f}%"
                      f"{100 * o['engel_ort']:>10.2f}%"
                      f"{100 * o['toplam_ort']:>11.2f}%"
                      f"{o['zemin_altinda_yuzde1']:>7d}/{len(zs)}")
            payda = ozet["0.30"]["toplam_ort"]
            band = (ozet["0.10"]["toplam_ort"] / payda) if payda > 0 else None
            z_payda = ozet["0.30"]["zemin_ort"]
            z_band = (ozet["0.10"]["zemin_ort"] / z_payda) if z_payda > 0 else None
            ozet["BAND_ORANI"] = band
            ozet["BAND_ORANI_zemin"] = z_band
            kayit["kumeler"][m_ad][k_ad] = {"ozet": ozet, "goruntu": satirlar}
            print(f"  {'':12s}{'-> BAND_ORANI':>6s} = "
                  f"{('%.2f' % band) if band else 'TANIMSIZ'}"
                  f"   (yalniz zemin: "
                  f"{('%.2f' % z_band) if z_band else 'TANIMSIZ'})")

    # ── OZET TABLO ────────────────────────────────────────────────────────
    c = "=" * 78
    print(f"\n{c}\nBAND_ORANI OZETI  (>= 3 ise sikisma GENEL · ~1 ise FIGURE OZGU)\n{c}")
    print(f"  {'model':10s}{'figur':>9s}" +
          "".join(f"{k:>14s}" for k in kumeler))
    for m_ad in kayit["kumeler"]:
        f = kayit["figur"].get(m_ad, {})
        fb = (f["0.10"]["toplam"] / f["0.30"]["toplam"]
              if f and f["0.30"]["toplam"] > 0 else None)
        hucre = "".join(
            f"{(('%.2f' % kayit['kumeler'][m_ad][k]['ozet']['BAND_ORANI']) if kayit['kumeler'][m_ad].get(k) and kayit['kumeler'][m_ad][k]['ozet']['BAND_ORANI'] else '—'):>14s}"
            for k in kumeler)
        print(f"  {m_ad:10s}{(('%.2f' % fb) if fb else '—'):>9s}{hucre}")

    print(f"\n{c}\nPOZITIF KONTROL\n{c}")
    print(f"  65_kabul_denetcisi.kaplama() ile sapma: {len(kontrol_sapma)}"
          f"   (0 OLMALI)")
    for s in kontrol_sapma:
        print(f"    SAPMA: {s}")
    print(f"  -> OLCUM {'GECERLI' if not kontrol_sapma else 'GECERSIZ'}")
    kayit["kontrol"]["kaplama_sapmasi"] = kontrol_sapma
    kayit["kontrol"]["gecerli"] = not kontrol_sapma
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
