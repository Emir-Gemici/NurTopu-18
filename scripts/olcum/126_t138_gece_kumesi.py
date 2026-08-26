"""T138 — DJI GECE KARELERI: egitime uygun mu, ve baska bir ise yariyor mu?

ON KAYIT: results/t138/on_kayit.md (bu betik KOSULMADAN ONCE yazildi, D-107).

IKI SORU, IKISI DE OLCULUR:
  A) EGITIME UYGUNLUK (on kayit SS2): kare kare zemin orani (ICERIK paydasi).
     U2 bandi: 0,05 < oran < 0,95. Alt sinir KORLUGU, ust sinir D-210'un
     tam-kare zemin kusurunu eler. TEK YONLU esik bu projede iki kez patladi.
  B) BASKA BIR ISE YARAR MI (mimarin eki): uretim yolunun bu karelerdeki
     davranisi. Kac kare REDDEDILDI, hangi SEBEPLE, kac karede ROTA URETILDI.
     🔴 ON KAYITTA YAZILI HUKUM: rota uretilen kare sayisi SIFIR DEGILSE bu
     CIDDI BIR BULGUDUR — sistem gormesi mumkun olmayan goruntude karar
     uretiyor demektir. Sifirsa fail-closed tasarimin ILK GERCEK VERI
     uzerindeki kanitidir.

IKI OLCEK KIPI (ikisi de kosulur — biri digerini gizler):
  · mpp=None : GERCEK uretim yolu. Olcek turetilemezse zaten reddeder;
               tek basina olculurse "olcek yoktu" tum sebepleri gizler.
  · mpp VERILDI : olcek BEDAVA. Maske tabanli kapilarin AYRICA tutup
               tutmadigini sinar — asil soru budur.

🔴 REGISTRY'YE YAZMAZ, ESIK DEGISTIRMEZ, dataset/ altina kume YAZMAZ.
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t138"
U2_ALT, U2_UST = 0.05, 0.95      # on kayit SS2 · SONUCA GORE DEGISTIRILMEZ

# URETIM GUVEN ESIGI. Bu deger URETIM zincirinin degeridir; ciplak sayi olarak
# degil, uretimdeki kardeslerine BAGLI durur: `rpi_inference` CLI varsayilani,
# `61_rota_moloza_basma.CONF` ve `65_kabul_denetcisi.CONF` ile ayni olmak
# ZORUNDADIR — kilit: tests/test_conf_esigi_supurmesi.py. `--conf` YALNIZ
# OLCUM icindir (ON_KAYIT SS18-A esik supurmesi); varsayilansiz kosum
# davranisi ve JSON ciktisi BAYT-ES ayni kalir.
CONF = 0.30


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--kareler", type=Path,
                    default=KOK / "data" / "dji_prova_kareler")
    ap.add_argument("--modeller", nargs="*",
                    default=["navitas_seg_v35_best.pt", "navitas_seg_v34_best.pt",
                             "navitas_seg_v30_best.pt"])
    ap.add_argument("--mpp", type=float, default=0.01,
                    help="olcek BEDAVA kipi icin mpp")
    ap.add_argument("--en-fazla", type=int, default=0, help="0 = TUMU")
    # 🔴 CIKTI PARAMETRELESTIRILDI (2026-08-22): betik BASKA bir kare kumesine
    #    de kosuluyor (yeni gunduz DJI cekimleri). Varsayilanlar DEGISMEDI, yani
    #    argumansiz kosum T138'in ciktisini AYNEN uretir; T138'in kaniti
    #    (results/t138/gece_kumesi.json) UZERINE YAZILMAZ.
    ap.add_argument("--cikti", type=Path, default=CIKTI,
                    help="Cikti dizini (varsayilan: results/t138)")
    ap.add_argument("--dosya", default="gece_kumesi.json",
                    help="Cikti dosya adi")
    ap.add_argument("--etiket", default="T138 · DJI gece kareleri, "
                                        "uretim yolu davranisi",
                    help="Ciktinin `_ne` alani")
    # 🔴 OLCUM PARAMETRESI (2026-08-26, ON_KAYIT SS18-A): guven esigi supurmesi
    #    icin. VARSAYILAN URETIM DEGERIDIR (CONF); argumansiz kosum ONCEKI
    #    davranisin ve JSON ciktisinin BAYT-ESIDIR. Bu bayrak esigi DEGISTIRMEZ,
    #    yalnizca baska bir esikte OLCMEYI mumkun kilar.
    ap.add_argument("--conf", type=float, default=CONF,
                    help=f"Guven esigi (varsayilan: uretim degeri {CONF})")
    args = ap.parse_args()

    sys.path.insert(0, str(KOK / "codes"))
    import numpy as np                                        # noqa: E402
    import cv2                                                # noqa: E402
    from rpi_inference import (_preprocess, _maskeleri_icerige_kirp,  # noqa: E402
                               get_masks, analyze_path, INFER_SIZE, )
    from karar_sozlesmesi import zemin_kaplamasi              # noqa: E402
    from ultralytics import YOLO                              # noqa: E402

    kareler = sorted(args.kareler.rglob("*.jpg"))
    if args.en_fazla:
        kareler = kareler[:args.en_fazla]
    print(f"kare: {len(kareler)} · model: {len(args.modeller)} · "
          f"imgsz {INFER_SIZE}\n")

    tum = {}
    for model_ad in args.modeller:
        yol = KOK / "models" / model_ad
        if not yol.exists():
            print(f"{model_ad}: AGIRLIK YOK -> atlandi")
            continue
        model = YOLO(str(yol), task="segment")
        t0 = time.perf_counter()
        satirlar = []
        for p in kareler:
            img = cv2.imread(str(p))
            if img is None:
                continue
            sq, small, icerik = _preprocess(img)
            h, w = sq.shape[:2]
            sonuc = model.predict(small, imgsz=INFER_SIZE, conf=args.conf, verbose=False)
            mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
            trav = mk[0] > 0
            oran = zemin_kaplamasi(trav, icerik)
            # (1) GERCEK uretim yolu: olcek YOK
            # 🔴 CAGRI URETIMDEKININ AYNISI (61_rota_moloza_basma.py:96).
            # Onceki surumde yalniz `return_reason=True` verilmisti ve demet
            # KISALDIGI icin sebep yanlis indeksten okunuyordu: 12/12 kare
            # "None" gorunuyordu. Kendi aletimin kusuruydu, olcum degil.
            y1 = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1], mpp=None,
                              return_clean=True, return_reason=True,
                              return_olcum=True)
            # (2) olcek BEDAVA
            y2 = analyze_path(mk[0], icerik=icerik, engel_mask=mk[1],
                              mpp=args.mpp, return_clean=True,
                              return_reason=True, return_olcum=True)
            def coz(y):
                yol, _guven, wps, _clean, red, _olcum = y
                sebep = red[0] if isinstance(red, tuple) else red
                # T152 (ON_KAYIT §11(2)): waypoint LISTESI de yazilir — tuval
                # (kare letterbox) koordinati, tam sayi. "Rota yol ustunde mi"
                # kapisi (142, b-ek2) rotanin NEREDEN gectigini bununla olcer;
                # D-288'de 3 rota cim/tarladan gecerken TP sayilmisti.
                liste = [[int(x), int(y)] for x, y in wps] if wps else []
                return (sebep, len(wps) if wps else 0, yol, liste)
            s1, n1, yol1, w1 = coz(y1)
            s2, n2, yol2, w2 = coz(y2)
            satirlar.append({
                "kare": p.name, "klip": p.parent.name[:38],
                "zemin_orani": round(float(oran), 5),
                "U2": bool(U2_ALT < oran < U2_UST),
                "olceksiz_sebep": s1, "olceksiz_wp": n1, "olceksiz_yol": yol1,
                "olcekli_sebep": s2, "olcekli_wp": n2, "olcekli_yol": yol2,
                "olceksiz_wps": w1, "olcekli_wps": w2,
            })
        sure = time.perf_counter() - t0
        u2 = sum(1 for s in satirlar if s["U2"])
        rota1 = sum(1 for s in satirlar if s["olceksiz_wp"] > 0)
        rota2 = sum(1 for s in satirlar if s["olcekli_wp"] > 0)
        sb1 = collections.Counter(s["olceksiz_sebep"] for s in satirlar)
        sb2 = collections.Counter(s["olcekli_sebep"] for s in satirlar)
        klipler = sorted({s["klip"] for s in satirlar if s["U2"]})
        print(f"── {model_ad}  ({sure:.0f} sn)")
        print(f"   U2 bandinda ({U2_ALT}<oran<{U2_UST}): {u2}/{len(satirlar)} "
              f"kare · {len(klipler)} ayri klip")
        print(f"   ROTA URETILEN  olceksiz {rota1}  ·  olcek BEDAVA {rota2}")
        print(f"   sebep (olceksiz)   : {dict(sb1.most_common(5))}")
        print(f"   sebep (olcek bedava): {dict(sb2.most_common(5))}\n")
        tum[model_ad] = {"sure_sn": round(sure, 1), "n": len(satirlar),
                         "U2_gecen": u2, "U2_klip": klipler,
                         "rota_olceksiz": rota1, "rota_olcekli": rota2,
                         "sebep_olceksiz": dict(sb1), "sebep_olcekli": dict(sb2),
                         "kareler": satirlar}

    args.cikti.mkdir(parents=True, exist_ok=True)
    govde = {"_ne": args.etiket,
             "_on_kayit": "results/t138/on_kayit.md",
             "_kareler": str(args.kareler),
             "_U2_bandi": [U2_ALT, U2_UST], "_mpp_bedava": args.mpp}
    # Uretim disi esikle kosuldugunda esik CIKTIYA yazilir (kanit izlenebilir
    # olsun). Uretim esiginde anahtar YOKTUR — JSON bayt-es kalir.
    if args.conf != CONF:
        govde["_conf"] = args.conf
    io.open(args.cikti / args.dosya, "w", encoding="utf-8").write(
        json.dumps({**govde, "modeller": tum}, ensure_ascii=False, indent=1))
    print(f"yazildi: {args.cikti / args.dosya}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
