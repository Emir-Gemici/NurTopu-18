"""ARAC REFERANS OLCEGI NEREDE ATESLENMEMELI? — gecerlilik olcutu ariyoruz.

NEDEN (REVIEW_LOG D-142, yan bulgu 2). T86 arac referans olcegini uretime
bagladi ve `drone` 0/12 -> 11/12 oldu. Ama olcek ALAN DISINDA DA atesleniyor:
`gemini` (yer seviyesinden cekilmis yol fotograflari) 3 karede olcek turetti
ve 1 karede ROTA URETTI. `val` kumesinde de 1 kare.

Bu EMNIYETSIZ yondedir: yandan/egik bakista bir aracin YONLU KUTU KISA KENARI
govde genisligi DEGILDIR (perspektif). Uydurma olcek -> uydurma r_gerekli ->
gecilemeyecek koridor gecilebilir sayilir.

ARANAN SEY BIR YASAK LISTESI DEGIL, OLCULEBILIR BIR GECERLILIK OLCUTUDUR.
Yasak liste bayatlar (yeni bir kaynak eklendiginde kimse hatirlamaz); olcut
kaynaktan BAGIMSIZ calisir.

HIPOTEZ (mimar · OLCULMEDI):
    TEPEDEN bakista butun araclar KAMERAYA AYNI UZAKLIKTADIR; kisa kenarlari
    birbirine yakin cikar. EGIK/YANDAN bakista uzaklik degisir ve gorunen
    boyut SACILIR.
    Olculebilir sonuc: kisa kenarin IQR/medyan orani, tepeden bakista KUCUK
    (D-124: gercek drone karelerinde 0,138), egik bakista BUYUK olmali.

Ayrica ikinci bir isaret: tepeden bakista araclar BENZER YONELIMDEDIR
(park sirasi); yol fotografinda yonelim dagilir. Yonelim dagilimi da olculur.

BU BIR IDDIA DEGILDIR. Ayirmazsa oyle yazilir ve baska olcut aranir.
"""
import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))
from arac_maskesi import ARAC_SINIFLERI                        # noqa: E402

ARAC_CONF = 0.25
ASGARI_ARAC = 3          # bu sayidan az aracla olcut anlamsiz


def kaynaklar():
    return {
        "drone (TEPEDEN, dogru)":   REPO / "data" / "raw_frames",
        "kompozit (TEPEDEN)":       REPO / "data" / "arena_kompozit" / "images",
        "gemini (YER SEVIYESI)":    REPO / "test_images" / "gemini",
        "val (YER SEVIYESI)":       REPO / "dataset" / "rescuenet_yolo" / "images" / "val",
        "test (KARISIK)":           REPO / "test_images" / "test" / "images",
    }


def kareler(yol, azami):
    uz = (".png", ".jpg", ".jpeg")
    if not yol.is_dir():
        return []
    hepsi = sorted(p for p in yol.rglob("*") if p.suffix.lower() in uz)
    adim = max(1, len(hepsi) // azami)
    return hepsi[::adim][:azami]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--azami", type=int, default=20)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    defter = json.loads(
        (REPO / "config" / "model_registry.json").read_text(encoding="utf-8"))
    obb_yolu = REPO / defter["profiles"]["arac_referansi"]["path"]
    obb = YOLO(str(obb_yolu), task="obb")
    print(f"arac kahini: {obb_yolu.name}")

    ozet = defaultdict(dict)
    print(f"\n{'=' * 84}\nARAC REFERANS OLCEGI · GECERLILIK OLCUTU\n{'=' * 84}")
    print(f"{'kaynak':<26}{'kare':>6}{'>=3 arac':>10}"
          f"{'IQR/med medyan':>16}{'IQR/med maks':>14}{'yonelim sd':>12}")

    for ad, yol in kaynaklar().items():
        kar = kareler(yol, args.azami)
        if not kar:
            print(f"{ad:<26}  KARE YOK")
            continue
        oranlar, yonelimler, arac_var = [], [], 0
        for p in kar:
            r = obb.predict(str(p), conf=ARAC_CONF, verbose=False)[0]
            if r.obb is None or len(r.obb) == 0:
                continue
            adlar = r.names
            cls = r.obb.cls.cpu().numpy().astype(int)
            xywhr = r.obb.xywhr.cpu().numpy()
            sec = np.array([adlar.get(int(c), str(c)) in ARAC_SINIFLERI
                            for c in cls])
            if sec.sum() < ASGARI_ARAC:
                continue
            arac_var += 1
            wh = xywhr[sec][:, 2:4]
            kisa = np.minimum(wh[:, 0], wh[:, 1])
            med = float(np.median(kisa))
            if med <= 0:
                continue
            iqr = float(np.percentile(kisa, 75) - np.percentile(kisa, 25))
            oranlar.append(iqr / med)
            # Yonelim: radyan -> [0, pi) katlanir (arac yonu 180 simetrik)
            aci = np.mod(xywhr[sec][:, 4], np.pi)
            # Dairesel standart sapma (2*aci ile, cunku pi periyodik)
            c, s = np.cos(2 * aci).mean(), np.sin(2 * aci).mean()
            R = float(np.hypot(c, s))
            yonelimler.append(float(np.sqrt(max(0.0, -2.0 * np.log(max(R, 1e-9))))))
        if not oranlar:
            print(f"{ad:<26}{len(kar):>6}{arac_var:>10}   olcut uretilemedi")
            continue
        o = np.array(oranlar)
        y = np.array(yonelimler)
        print(f"{ad:<26}{len(kar):>6}{arac_var:>10}"
              f"{np.median(o):>16.3f}{o.max():>14.3f}{np.median(y):>12.3f}")
        ozet[ad] = {"kare": len(kar), "arac_var": arac_var,
                    "iqr_med_medyan": float(np.median(o)),
                    "iqr_med_maks": float(o.max()),
                    "iqr_med_min": float(o.min()),
                    "yonelim_sd_medyan": float(np.median(y))}

    print(f"\n{'=' * 84}")
    print("OKUMA: IQR/medyan = arac kisa kenarlarinin SACILIMI.")
    print("  TEPEDEN bakis -> tum araclar ayni uzaklikta -> SACILIM KUCUK.")
    print("  EGIK bakis    -> uzaklik degisir -> SACILIM BUYUK.")
    print("  D-124'te gercek drone karelerinde olculen deger: 0,138.")
    print("  Ayirici bir esik varsa, `drone`un maksimumu ile yer-seviyesi")
    print("  kumelerinin minimumu arasinda BOSLUK olmali. Yoksa bu olcut")
    print("  AYIRMIYOR demektir ve boyle yazilir.")
    print(f"{'=' * 84}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(dict(ozet), ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
