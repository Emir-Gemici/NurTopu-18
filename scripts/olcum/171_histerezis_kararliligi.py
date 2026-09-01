"""P5 (D-396) — HISTEREZIS OLCUMU: yayina sizan cevrilme ham cevrilmeye karsi.

ON KAYIT: results/p5_histerezis/ON_KAYIT.md (H1 esigi sonuc gorulmeden:
yayimlanan cevrilme <= ham cevrilmenin %40'i; ham >= 5 ise kesin azalma).

Yontem — 68'in gurultu recetesi KARE-ICI akisa cevrilir: her kare icin
[temiz, g1, g2, g3, g4] dizisi AYNI SAHNENIN pespese 5 karesinin vekilidir.
Dizi hem HAM hem `KararYumusatici`den gecirilerek oynatilir; sayilan yalniz
KARE-ICI (ayni sahne) cevrilmedir:

  ham cevrilme       : dizide karar (serit,red) degisim sayisi
  yayimlanan cevrilme : yumusatici True dedigi orneklerdeki degisim sayisi
  bastirilan NO_ROUTE : 0 OLMAK ZORUNDA (H2 — fail-closed)

⚠ ILK SURUM (ayni gece, D-396'da kayitli) 260 kareyi TEK akis saydi ve
sahne SINIRLARINDAKI mesru karar degisimlerini de "cevrilme" olarak
yumusaticiya yikti — kume ardisik ucus DEGIL, 260 bagimsiz sahnedir; 68'in
onculu "AYNI sahne, gurultu altinda"dir. Bu yuzden yumusatici kare basina
taze kurulur (sahneler arasi tasima olcumu kirletir). Esikler DEGISMEDI.
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import (KARAR_HISTEREZIS_KARE,  # noqa: E402
                              KararYumusatici)

m68 = import_module("68_karar_kararliligi")
kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu

CONF = 0.30


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--kume", type=Path, default=None)
    ap.add_argument("--sigma", type=float, default=2.0)
    ap.add_argument("--tekrar", type=int, default=4)
    ap.add_argument("--tohumlar", type=int, nargs="+", default=[7, 42])
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    if args.kume is None:
        args.kume = kabul_kumesi_yolu()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    sonuclar = {}
    for tohum in args.tohumlar:
        rng = np.random.default_rng(tohum)
        n = 0
        ham_cevrilme = yayin_cevrilme = 0
        ham_kararsiz_kare = yayin_kararsiz_kare = 0
        bastirilan = bastirilan_no_route = 0
        siniflar = {}

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
            n += 1

            dizi = [m68.karar(model, img, mpp)]
            for _ in range(args.tekrar):
                g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
                gurultulu = np.clip(img.astype(np.float32) + g,
                                    0, 255).astype(np.uint8)
                dizi.append(m68.karar(model, gurultulu, mpp))

            # AYNI sahnenin 5 ornegi = kare-ici akis; yumusatici taze kurulur
            yumusatici = KararYumusatici()
            son_ham = son_yayin = ("BASLANGIC",)
            kare_ham = kare_yayin = 0
            kimlik_sayilari = {}
            for k in dizi:
                kimlik_sayilari[k[:2]] = kimlik_sayilari.get(k[:2], 0) + 1
            for k in dizi:
                kimlik = k[:2]                     # (serit, red)
                if son_ham != ("BASLANGIC",) and kimlik != son_ham:
                    kare_ham += 1
                son_ham = kimlik

                yayimla = yumusatici.suz(k[0], k[1])
                if yayimla:
                    if son_yayin != ("BASLANGIC",) and kimlik != son_yayin:
                        kare_yayin += 1
                        # EK-1 siniflandirmasi (olcut bilesimden ONCE yazildi)
                        no_route_gecisi = (
                            k[0] is None or k[1] is not None
                            or son_yayin[0] is None or son_yayin[1] is not None)
                        if no_route_gecisi:
                            sinif = "no_route"          # (i) fail-closed
                        elif kimlik_sayilari[kimlik] >= KARAR_HISTEREZIS_KARE:
                            sinif = "cogunluk"          # (ii) kalici karar
                        elif kimlik_sayilari[kimlik] == 2:
                            sinif = "h5_tavani"         # (iii) bayatlama siniri
                        else:
                            sinif = "azinlik"           # H1a IHLALI
                        siniflar[sinif] = siniflar.get(sinif, 0) + 1
                    son_yayin = kimlik
                else:
                    bastirilan += 1
                    if k[0] is None or k[1] is not None:
                        bastirilan_no_route += 1   # H2 ihlali — 0 olmali
            ham_cevrilme += kare_ham
            yayin_cevrilme += kare_yayin
            ham_kararsiz_kare += 1 if kare_ham else 0
            yayin_kararsiz_kare += 1 if kare_yayin else 0

        sonuclar[str(tohum)] = {
            "n_kare": n, "ornek_per_kare": args.tekrar + 1,
            "ham_cevrilme": ham_cevrilme,
            "yayimlanan_cevrilme": yayin_cevrilme,
            "ham_kararsiz_kare": ham_kararsiz_kare,
            "yayin_kararsiz_kare": yayin_kararsiz_kare,
            "bastirilan": bastirilan,
            "bastirilan_no_route": bastirilan_no_route,
            "yayin_cevrilme_siniflari": siniflar,
        }
        print(f"tohum {tohum:>3}: n={n} · ham={ham_cevrilme} "
              f"({ham_kararsiz_kare} karede) · yayimlanan={yayin_cevrilme} "
              f"({yayin_kararsiz_kare} karede) · bastirilan={bastirilan} · "
              f"bastirilan_NO_ROUTE={bastirilan_no_route}")
        print(f"           siniflar: {siniflar}")

    # ON_KAYIT H1/H2 verdikti
    h1 = all(
        (s["yayimlanan_cevrilme"] <= 0.40 * s["ham_cevrilme"])
        and (s["ham_cevrilme"] < 5 or s["yayimlanan_cevrilme"] < s["ham_cevrilme"])
        for s in sonuclar.values())
    h2 = all(s["bastirilan_no_route"] == 0 for s in sonuclar.values())
    # EK-1 (bilesim gorulmeden yazildi): mekanizmanin gercek vaadi
    h1a = all(s["yayin_cevrilme_siniflari"].get("azinlik", 0) == 0
              for s in sonuclar.values())
    h1b = all(s["yayimlanan_cevrilme"] < s["ham_cevrilme"]
              for s in sonuclar.values())
    print(f"\nH1 (toplam %40 esigi — OZGUN): {'GECTI' if h1 else 'DUSTU'}")
    print(f"H1a (azinlik rota-rota sizinti = 0): {'GECTI' if h1a else 'DUSTU'}")
    print(f"H1b (kesin azalma): {'GECTI' if h1b else 'DUSTU'}")
    print(f"H2 (NO_ROUTE bastirilmadi): {'GECTI' if h2 else 'DUSTU'}")

    cikti = {"_on_kayit": "results/p5_histerezis/ON_KAYIT.md",
             "_model": str(args.model), "sigma": args.sigma,
             "esik_K": KARAR_HISTEREZIS_KARE,
             "tohumlar": sonuclar, "H1_ozgun": h1, "H1a": h1a,
             "H1b": h1b, "H2": h2}
    hedef = args.json or (REPO / "results" / "p5_histerezis"
                          / "olcum_20260903.json")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0 if (h1a and h1b and h2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
