"""T74 · DARBOGAZI NE DARALTIYOR: MOLOZ ADASI mi, KORIDOR SINIRI mi?

NEDEN (REVIEW_LOG D-126). T74 olculdu ama yalniz DAGILIM olarak: kusursuz
algiyla (yer gercegi maskesi) 260 karenin 46'sinda pay < 3 px, en dusuk pay
0,10 px. D-126 ayrica darligin `dar_orani` parametresinden GELMEDIGINI gosterdi
— dar paylarin %37'si "acik" seritlerden cikiyor. Yani darlik uretecin
geometrisinin geneline yayilmis.

AMA D-126 DARBOGAZIN NEREDE OLDUGUNU BULMADI. Gorevin YAP maddesi "koridor
genisligine alt sinir koy" diyor; hangi genisligin alt siniri oldugu ise
olculmeden bilinemez. Ilk bakista suclu `moloz_adalari()` icindeki
`gecit_yari = gen * rng.uniform(0.24, 0.36)` gorunuyor — ama `gen` (serit
genisligi) ~200 tuval pikseldir, yani gecit yarigenisligi ~48-94 tuval px =
38-75 son piksel. Olculen darbogaz medyani ise 14,31 son piksel. **Demek ki
darbogazi gecit belirlemiyor.** Bu betik gercek daraltaniyi bulur.

AYIRT EDILEN IKI DARALTAN (yer gercegi maskesi uzerinde, MODEL YOK):

  MOLOZ  : darbogaz noktasina en yakin sinir bir `blocked` pikseli.
           -> care: ada yogunlugu/yerlesimi (moloz_adalari)
  SINIR  : en yakin sinir ETIKETSIZ bolge (ne traversable ne blocked), yani
           koridorun/serit poligonunun kenari.
           -> care: serit poligonunun genisligi (serit(), ic_serit())

Ikisi ayni carede DEGILDIR; hangisinin baskin oldugu olculmeden kod
degistirilirse yanlis yer duzeltilir.

Etiket->maske donusumu `61_rota_moloza_basma.py`den ITHAL edilir (iki yerde iki
farkli yer gercegi tanimi olmasin — madde 16).
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

from karar_sozlesmesi import serit_no                             # noqa: E402
from rpi_inference import analyze_path                            # noqa: E402

etiket_maskesi = import_module("61_rota_moloza_basma").etiket_maskesi

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# D-126'nin "dar" esigi; ciplak sabit degil, o kayittan gelir.
DAR_ESIK_PX = 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))

    kayitlar = []
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
        h, w = img.shape[:2]
        txt = (args.kume / "labels" /
               Path(ornek["cikti"]).relative_to("images")).with_suffix(".txt")
        gt = etiket_maskesi(txt, h, w)
        if not gt[0].any():
            continue

        # KUSURSUZ ALGI: model yok, girdi dogrudan yer gercegi.
        # Goruntu zaten kare oldugu icin icerik kutusu tum tuvaldir.
        _y, _guven, _wps, _temiz, red, olcum = analyze_path(
            gt[0], icerik=(0, 0, w, h), engel_mask=gt[1], mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)
        if red is not None or not olcum:
            kayitlar.append({"kare": p.name, "red": str(red), "pay_px": None})
            continue

        bx, by = olcum["darbogaz_xy"]
        darbogaz = float(olcum["darbogaz_px"])
        r_ger = float(olcum["r_gerekli_px"])

        # DARALTANI BUL: darbogaz noktasindan iki ayri sinira uzaklik.
        #   engel  = blocked pikselleri
        #   disari = ETIKETSIZ bolge (ne traversable ne blocked)
        engel = (gt[1] > 0)
        disari = (gt[0] == 0) & (gt[1] == 0)
        d_engel = cv2.distanceTransform((~engel).astype(np.uint8),
                                        cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        d_disari = cv2.distanceTransform((~disari).astype(np.uint8),
                                         cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
        de = float(d_engel[by, bx])
        dd = float(d_disari[by, bx])
        daraltan = "MOLOZ" if de <= dd else "SINIR"

        ser = int(serit_no(bx, 0, w))
        # 🔴 URETEC SERIDI, GORUNTU UCTE BIRI DEGILDIR. Seritler ~110 px,
        # `serit_no` ucte birleri ~213 px'tir; `durumlar[ser-1]` yazmak durumu
        # YANLIS seride atar (ilk denememde tam bu hata vardi). Darbogaz
        # noktasinin x'i hangi `serit_kutusu` icine dusuyorsa O serit alinir.
        durumlar = [d for d in (ornek["arena"].get("uretec_seritleri") or [])
                    if isinstance(d, dict)]
        kayit_serit = {}
        for d in durumlar:
            kutu = d.get("serit_kutusu") or []
            if len(kutu) >= 3 and float(kutu[0]) <= bx <= float(kutu[0]) + float(kutu[2]):
                kayit_serit = d
                break
        durum = kayit_serit.get("durum")
        kutu = kayit_serit.get("serit_kutusu") or []
        serit_gen = float(kutu[2]) if len(kutu) >= 3 else None

        kayitlar.append({
            "kare": p.name, "pay_px": darbogaz - r_ger,
            "darbogaz_px": darbogaz, "r_gerekli_px": r_ger,
            "xy": [int(bx), int(by)], "d_engel": de, "d_disari": dd,
            "daraltan": daraltan, "darbogaz_serit": ser,
            "serit_durumu": durum, "serit_gen_px": serit_gen, "acik_serit": ornek["arena"].get("acik_serit"),
        })

    rotali = [k for k in kayitlar if k["pay_px"] is not None]
    dar = [k for k in rotali if k["pay_px"] < DAR_ESIK_PX]

    c = "=" * 76
    print(f"\n{c}\nT74 · DARBOGAZI NE DARALTIYOR (yer gercegi, MODEL YOK)\n"
          f"  kume {args.kume.name} · rota uretilen {len(rotali)}/{len(kayitlar)}\n{c}")
    pay = np.array([k["pay_px"] for k in rotali])
    print(f"  pay (darbogaz - r_gerekli): medyan {np.median(pay):.2f} px · "
          f"min {pay.min():.2f} px · <{DAR_ESIK_PX:.0f}px olan {len(dar)}/{len(rotali)}")

    print(f"\n  DARALTAN DAGILIMI:")
    for kume_ad, kume_v in (("TUM KARELER", rotali), (f"pay < {DAR_ESIK_PX:.0f} px", dar)):
        n = len(kume_v)
        if not n:
            continue
        moloz = sum(1 for k in kume_v if k["daraltan"] == "MOLOZ")
        print(f"    {kume_ad:<18} MOLOZ {moloz:>4}/{n:<4} (%{100*moloz/n:4.1f})"
              f"   SINIR {n-moloz:>4}/{n:<4} (%{100*(n-moloz)/n:4.1f})")

    print(f"\n  DAR KARELERDE serit durumu (uretec):")
    sayac = {}
    for k in dar:
        anahtar = (k["serit_durumu"], k["daraltan"])
        sayac[anahtar] = sayac.get(anahtar, 0) + 1
    for (durum, dar_alt), n in sorted(sayac.items(), key=lambda x: -x[1]):
        print(f"    durum={str(durum):<12} daraltan={dar_alt:<6} {n:>3} kare")

    print(f"\n  EN DAR 12 KARE:")
    for k in sorted(rotali, key=lambda k: k["pay_px"])[:12]:
        print(f"    {k['kare']:<16} pay={k['pay_px']:6.2f} px  daraltan={k['daraltan']:<6}"
              f"  d_engel={k['d_engel']:6.2f}  d_disari={k['d_disari']:6.2f}"
              f"  serit={k['darbogaz_serit']} durum={k['serit_durumu']}")

    print(f"\n{c}")
    print("OKUMA: 'MOLOZ' baskinsa care `moloz_adalari()` icindedir (ada")
    print("yerlesimi/yogunlugu). 'SINIR' baskinsa care SERIT POLIGONUNUN")
    print("genisligindedir (`serit()` / `ic_serit()`); gecit genisligini")
    print("buyutmek o durumda HICBIR SEY degistirmez.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(kayitlar, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        print(f"json -> {args.json}")


if __name__ == "__main__":
    main()
