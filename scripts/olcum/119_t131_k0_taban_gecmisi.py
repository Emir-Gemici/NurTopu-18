"""T131 — K0 figur tabaninin URETIM SOYAGACI boyunca TEK ALETLE olculmesi.

NEDEN: kayma defteri (118) gosterdi ki `figur_zemin_orani` SAYISAL alani ancak
2026-08-19'da (v34 terfisinden SONRA) dogdu; v30'un degeri yalnizca
`k0_korluk.olculen` DUZ METNINDE var ("figur zemin %8,0"). Bicimli metinden
sayi ayiklamak D-180'in kusur sinifidir — bu yuzden metne guvenmiyoruz,
AYNI FIGURU AYNI FONKSIYONLA BUGUN YENIDEN OLCUYORUZ.

🔴 KAPI DEGIL, ESIK KOYMAZ (T131 kisiti). Hicbir esik okumaz/yazmaz; yalnizca
denetcinin KENDI `kaplama()` fonksiyonunu ICE AKTARIR (kopyalamaz — kopya,
aletin surumler arasi ayni oldugu iddiasini bozar) ve olcum basar.

ON KAYIT: results/t131/on_kayit.md (bu betik KOSULMADAN ONCE yazildi).
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t131"

# Uretim soyagaci (JETSON_KILAVUZ: v35 <- v34 <- v30 <- v27 <- v24 <- v21 <- v17/v20)
# `donem_512`: model KENDI URETIM DONEMINDE 512 ile mi kosuyordu? False ise
# sayi ALET-TUTARLI ama DONEM-TUTARLI DEGILDIR (on kayit SS3).
# 🔴 ILK YAZIMDA v24'e True demistim — DOGRULAMADAN. Yanlis: cozunurluk
# 640 -> 512 gecisi v27 ILE oldu (JETSON_KILAVUZ SS0-T76; REVIEW_LOG:7455
# "v24 640'ta EGITILDI"). v27 de 640'ta EGITILDI ama URETIMDE 512 kostu —
# bayrak "egitim boyutu" degil "donemin cikarim boyutu" demektir.
SOYAGACI = [
    ("v17", "navitas_seg_v17_best.pt", False),
    ("v20", "navitas_seg_v20_best.pt", False),
    ("v21", "navitas_seg_v21_best.pt", False),
    ("v24", "navitas_seg_v24_best.pt", False),
    ("v27", "navitas_seg_v27_best.pt", True),
    ("v30", "navitas_seg_v30_best.pt", True),
    ("v34", "navitas_seg_v34_best.pt", True),
    ("v35", "navitas_seg_v35_best.pt", True),
]


def denetciyi_yukle():
    """65'i ICE AKTAR (adi rakamla basladigi icin importlib gerekir)."""
    yol = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
    sys.path.insert(0, str(KOK / "codes"))
    spec = importlib.util.spec_from_file_location("kabul_denetcisi", yol)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    d = denetciyi_yukle()
    from ultralytics import YOLO  # noqa: E402  (denetciyle ayni kaynak)

    print(f"figur   : {d.FIGUR.relative_to(KOK)}")
    print(f"alet    : 65_kabul_denetcisi.kaplama() (ICE AKTARILDI) · "
          f"CONF={d.CONF} · INFER_SIZE={d.INFER_SIZE}")
    print(f"band    : {d.K0_ORAN_ALT} <= oran <= {d.K0_ORAN_UST} "
          f"(OKUNDU, degistirilmedi)\n")

    olcumler = []
    for ad, dosya, donem_512 in SOYAGACI:
        p = KOK / "models" / dosya
        if not p.exists():
            print(f"{ad:5s} AGIRLIK YOK -> atlandi ({dosya})")
            continue
        figur = d.kaplama(YOLO(str(p)), d.FIGUR)
        olcumler.append({"surum": ad, "agirlik": dosya, "figur": figur,
                         "donem_512": donem_512})
        isaret = "" if donem_512 else "  ⚠ donem-tutarli DEGIL"
        print(f"{ad:5s} figur zemin = {100*figur:6.2f}%{isaret}")

    # Terfi zinciri: her uretim modeli, KENDINDEN ONCEKI uretim modeline gore
    URETIM = ["v27", "v30", "v34", "v35"]  # 118'in git gecmisinden: ayni kabul kumesi
    harita = {o["surum"]: o["figur"] for o in olcumler}
    zincir = []
    for i in range(1, len(URETIM)):
        onceki, simdiki = URETIM[i - 1], URETIM[i]
        if onceki not in harita or simdiki not in harita:
            continue
        taban, deger = harita[onceki], harita[simdiki]
        oran = (deger / taban) if taban > 0 else None
        uyari = d.k0_dikkat_satiri(oran)
        zincir.append({
            "terfi": f"{onceki} -> {simdiki}", "taban": taban, "figur": deger,
            "oran": oran,
            "band_disi": uyari is not None,
            "yon": (None if uyari is None
                    else ("YETENEK (< 0,5 · daha az zemin)" if oran < d.K0_ORAN_ALT
                          else "TEHLIKELI (> 2,0 · daha cok zemin)")),
        })

    print("\n== TERFI ZINCIRI (her terfi, KENDINDEN ONCEKI uretim modeline gore)")
    for z in zincir:
        durum = z["yon"] if z["band_disi"] else "band icinde — uyari YOK"
        print(f"  {z['terfi']:12s} taban {100*z['taban']:6.2f}% -> "
              f"figur {100*z['figur']:6.2f}%  oran {z['oran']:6.2f}x   {durum}")

    io.open(CIKTI / "k0_taban_gecmisi.json", "w", encoding="utf-8").write(
        json.dumps({
            "_ne": "T131 · K0 figur tabani, uretim soyagaci, TEK ALET. KAPI DEGIL.",
            "_alet": {"fonksiyon": "65_kabul_denetcisi.kaplama (ice aktarildi)",
                       "CONF": d.CONF, "INFER_SIZE": d.INFER_SIZE,
                       "figur": str(d.FIGUR.relative_to(KOK)),
                       "band": [d.K0_ORAN_ALT, d.K0_ORAN_UST]},
            "olcumler": olcumler, "terfi_zinciri": zincir,
        }, ensure_ascii=False, indent=1))
    print(f"\nyazildi: {CIKTI / 'k0_taban_gecmisi.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
