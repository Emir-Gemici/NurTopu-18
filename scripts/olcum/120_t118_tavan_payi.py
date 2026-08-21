"""T118 — URETIM TAVANININ (0,67) URETIMDEKI MODELE OLAN PAYI.

NEDEN: T118'in olcum kismi BITTI (D-208 §1/§2 + D-214: esik bozulmasi SIFIR).
Ama D-208'in "67/67 ret" dayanagi **v34 donemine** aittir; 2026-08-21'de
uretim **v35**'e gecti (T130/D-256). Olculmemis olan sey redlerin PAYIdir:
`red 0` ikili bir sonuctur, kareler tavanin 1 punto altinda da olabilir
30 punto altinda da — saha riski (Jetson 30 Eylul, cihaz-oncesi pencere YOK)
bu ikisinde taban tabana zittir.

🔴 KAPI DEGIL, ESIK DEGISTIRMEZ. Gorev metni: "ONCE TARA VE OLC. ESIK
DEGISTIRME." Esikler OKUNUR; `codes/` altina dokunulmaz.

⚠ RET IKI KOSULUN VE'sidir (`karar_sozlesmesi:577-582`):
    kaplama > ZEMIN_KAPLAMA_TAVANI  VE  kenar_dayanmasi > ZEMIN_KENAR_DAYANMA_TAVANI
Yalniz kaplamaya bakmak D-208'i YANLIS okumak olurdu; ikisi de olculur.

ON KAYIT: results/t118/on_kayit.md (bu betik KOSULMADAN ONCE yazildi).
"""
from __future__ import annotations

import importlib.util
import io
import json
import statistics
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t118"


def denetciyi_yukle():
    """65'i ICE AKTAR — maske uretim yolu T131'de BAYT-ES oldugu olculen yoldur."""
    sys.path.insert(0, str(KOK / "codes"))
    spec = importlib.util.spec_from_file_location(
        "kabul_denetcisi", KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def olc(model, kareler, d, ks):
    """Her karede URETIM olcusu. Uretim fonksiyonlari ICE AKTARILDI, kopya YOK."""
    import cv2
    satirlar = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        sq, small, icerik = d._preprocess(img)
        h, w = sq.shape[:2]
        sonuc = model.predict(small, imgsz=d.INFER_SIZE, conf=d.CONF, verbose=False)
        mk = d._maskeleri_icerige_kirp(d.get_masks(sonuc, h, w), icerik)
        trav = mk[0] > 0
        kaplama = ks.zemin_kaplamasi(trav, icerik)      # ICERIK paydasi
        kenar = ks.zemin_kenar_dayanmasi(trav, icerik)
        red = ks.zemin_maskesi_reddi(trav, icerik)      # URETIMIN KENDI KARARI
        satirlar.append({
            "kare": p.name,
            "kaplama_icerik": kaplama,
            "kaplama_tuval": float(trav.mean()),        # denetcinin bastigi sayi
            "kenar_dayanmasi": kenar,
            "red": red is not None,
            "red_sebebi": (red[0] if red else None),
        })
    return satirlar


def ozet(satirlar, ks):
    k = [s["kaplama_icerik"] for s in satirlar]
    e = [s["kenar_dayanmasi"] for s in satirlar]
    red = [s for s in satirlar if s["red"]]
    tavani_asan = [s for s in satirlar if s["kaplama_icerik"] > ks.ZEMIN_KAPLAMA_TAVANI]
    return {
        "n": len(satirlar),
        "red": len(red),
        "kaplama_icerik": {"min": min(k), "medyan": statistics.median(k), "maks": max(k)},
        "kenar": {"min": min(e), "medyan": statistics.median(e), "maks": max(e)},
        "kaplama_tavani_asan": len(tavani_asan),
        "en_yakin_kare": max(satirlar, key=lambda s: s["kaplama_icerik"])["kare"],
        "tavana_pay": ks.ZEMIN_KAPLAMA_TAVANI - max(k),
    }


def main() -> int:
    d = denetciyi_yukle()
    import karar_sozlesmesi as ks
    from ultralytics import YOLO

    kareler = sorted((KOK / "data" / "raw_frames").rglob("*.jpg"))
    print(f"gercek kare : {len(kareler)}")
    print(f"tavanlar    : kaplama {ks.ZEMIN_KAPLAMA_TAVANI} · "
          f"kenar {ks.ZEMIN_KENAR_DAYANMA_TAVANI}   (OKUNDU, degistirilmedi)")
    print(f"alet        : 65'in maske yolu · CONF {d.CONF} · imgsz {d.INFER_SIZE}\n")

    # v35 = URETIM (defterin gosterdigi yerden) · v34 = YEDEK ve ALET DOGRULAMASI
    from model_registry import resolve_model
    uretim_yolu, spec = resolve_model()
    hedefler = [("v35 (URETIM)", uretim_yolu),
                ("v34 (yedek)", KOK / "models" / "navitas_seg_v34_best.pt")]

    cikti = {"_ne": "T118 · uretim tavaninin payi. KAPI DEGIL, ESIK DEGISTIRMEZ.",
             "_tavanlar": {"kaplama": ks.ZEMIN_KAPLAMA_TAVANI,
                            "kenar": ks.ZEMIN_KENAR_DAYANMA_TAVANI},
             "_uretim_modeli": spec["model_id"], "modeller": {}}
    for ad, yol in hedefler:
        if not Path(yol).exists():
            print(f"{ad}: AGIRLIK YOK -> atlandi")
            continue
        satirlar = olc(YOLO(str(yol)), kareler, d, ks)
        o = ozet(satirlar, ks)
        cikti["modeller"][ad] = {"yol": str(yol), "ozet": o, "kareler": satirlar}
        print(f"── {ad}")
        print(f"   RED           : {o['red']}/{o['n']}")
        print(f"   kaplama ICERIK: min {o['kaplama_icerik']['min']:.4f} · "
              f"medyan {o['kaplama_icerik']['medyan']:.4f} · "
              f"maks {o['kaplama_icerik']['maks']:.4f}")
        print(f"   kenar dayanma : min {o['kenar']['min']:.4f} · "
              f"medyan {o['kenar']['medyan']:.4f} · maks {o['kenar']['maks']:.4f}")
        print(f"   tavani ASAN   : {o['kaplama_tavani_asan']}/{o['n']} kare "
              f"(kaplama > {ks.ZEMIN_KAPLAMA_TAVANI})")
        print(f"   TAVANA PAY    : {o['tavana_pay']:+.4f}  "
              f"(en yakin kare: {o['en_yakin_kare']})\n")

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "tavan_payi.json", "w", encoding="utf-8").write(
        json.dumps(cikti, ensure_ascii=False, indent=1))
    print(f"yazildi: {CIKTI / 'tavan_payi.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
