"""CURUTME 5 — "daha iyi ETIKET bunu cozemez" iddiasi.

Elle cizilen maskelerin ~%38'i (medyan) ETIKETSIZ (deger 0). ETIKETSIZ,
"surulemez" DEGILDIR; "insan cizmemis"tir. Bant testi ETIKETSIZ'i sessizce
"zemin degil" saydigi icin YAPISAL hukmu bu bosluktan gelmis olabilir.

SINAMA: ETIKETSIZ pikselleri, AYNI KAREDEKI insan etiketlerinden turetilen
iki merkeze (SINIF0 ortalama Lab · SINIF1 ortalama Lab) EN YAKIN olana ata.
Hicbir dis bilgi, hicbir model, hicbir el ayari yok — yalniz insanin o karede
zaten verdigi iki ornek kume. Sonra URETIM `analyze_path` kosulur.

Iki degisken:
  TAM   : tum ETIKETSIZ pikseller nearest-centroid ile atanir
  BAGLI : ayni atama, ama yeni SINIF0 yalniz mevcut SINIF0'a BAGLI oldugu
          yerde kabul edilir (muhafazakar)

KONTROL: bos bandi %100 SINIF1 olan kareler (insan ACIKCA engel demis)
kurtarilmamalidir. Kurtariliyorsa yontem 'her yeri yesile boya'dir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
from rpi_inference import _preprocess, analyze_path  # noqa: E402

KARE_DIZIN = KOK / "dataset" / "dji_kirsal" / "images" / "val"
ETIKET_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
CIK = KOK / "results" / "dji_kirsal" / "curut_yapisal"


def etiket_bul(stem):
    for alt in ("A", "B", "C", "D"):
        p = ETIKET_KOK / alt / (stem + "_uc.png")
        if p.exists():
            return p
    return None


def tamamla(img, lab_big):
    """ETIKETSIZ pikselleri kare-ici iki merkeze en yakin sinifa ata."""
    lab_uzay = cv2.cvtColor(cv2.GaussianBlur(img, (0, 0), 3),
                            cv2.COLOR_BGR2LAB).astype(np.float32)
    s0 = (lab_big == 1)
    s1 = (lab_big == 2)
    bos = (lab_big == 0)
    if not s0.any() or not s1.any() or not bos.any():
        return None, None, {"atlandi": True}
    m0 = lab_uzay[s0].mean(axis=0)
    m1 = lab_uzay[s1].mean(axis=0)
    d0 = ((lab_uzay - m0) ** 2).sum(axis=2)
    d1 = ((lab_uzay - m1) ** 2).sum(axis=2)
    yeni0 = bos & (d0 < d1)
    tam = lab_big.copy()
    tam[yeni0] = 1
    tam[bos & ~yeni0] = 2
    # BAGLI degisken: yeni SINIF0 yalniz mevcut SINIF0'la ayni bilesende ise
    aday = (s0 | yeni0).astype(np.uint8)
    n, etk = cv2.connectedComponents(aday, 8)
    tutulan = np.unique(etk[s0])
    tutulan = tutulan[tutulan > 0]
    bagli_s0 = np.isin(etk, tutulan)
    bagli = lab_big.copy()
    bagli[bos & bagli_s0] = 1
    bagli[bos & ~bagli_s0] = 2
    ist = {"bos_oran": round(float(bos.mean()), 4),
           "yeni_s0_oran": round(float(yeni0.mean()), 4),
           "s0_once": round(float(s0.mean()), 4),
           "s0_tam": round(float((tam == 1).mean()), 4),
           "s0_bagli": round(float((bagli == 1).mean()), 4)}
    return tam, bagli, ist


def kosum(img, lab_big, icerik, tuval_sekli):
    x0, y0, w, h = icerik
    zemin = np.zeros(tuval_sekli, np.uint8)
    engel = np.zeros(tuval_sekli, np.uint8)
    zemin[y0:y0 + h, x0:x0 + w] = (lab_big == 1).astype(np.uint8)
    engel[y0:y0 + h, x0:x0 + w] = (lab_big == 2).astype(np.uint8)
    serit, guven, wps, temiz, sebep = analyze_path(
        zemin, return_clean=True, return_reason=True,
        icerik=icerik, engel_mask=engel)
    return {"serit": serit, "guven": round(float(guven), 4), "wp": len(wps),
            "sebep": None if sebep is None else sebep[0]}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    e = json.loads((KOK / "results" / "dji_kirsal" /
                    "bant_tanisi_etiket.json").read_text(encoding="utf-8"))
    kapsam = {r["kare"]: r for r in json.loads(
        (CIK / "c1_etiket_kapsam.json").read_text(encoding="utf-8"))["kareler"]}
    hedefler = [r["kare"] for r in e["kareler"] if r["durum"] == "YAPISAL"]
    sonuc = []
    print("%-30s %-13s | %-16s | %-16s | %-16s"
          % ("kare", "BOS BANT", "HAM ETIKET", "TAMAMLANMIS", "BAGLI"))
    for ad in hedefler:
        p = KARE_DIZIN / ad
        img = cv2.imread(str(p))
        lp = etiket_bul(p.stem)
        lab = cv2.imread(str(lp), cv2.IMREAD_UNCHANGED)
        if lab.ndim == 3:
            lab = lab[:, :, 0]
        tuval, _, icerik = _preprocess(img)
        x0, y0, w, h = icerik
        big = cv2.resize(lab, (w, h), interpolation=cv2.INTER_NEAREST)
        ham = kosum(img, big, icerik, tuval.shape[:2])
        tam, bagli, ist = tamamla(img, big)
        if tam is None:
            print("%-30s ATLANDI" % ad[-26:])
            continue
        r_tam = kosum(img, tam, icerik, tuval.shape[:2])
        r_bag = kosum(img, bagli, icerik, tuval.shape[:2])
        k = kapsam[ad]
        # hangi bant bos ve o bandin bilesimi
        er = e["kareler"]
        rec = next(r for r in er if r["kare"] == ad)
        taraf = "alt" if rec["tam_alt"] < rec["gereken"] else "ust"
        if rec["tam_alt"] < rec["gereken"] and rec["tam_ust"] < rec["gereken"]:
            taraf = "ikisi"
        bos_ozet = ("%s ets%.2f s1%.2f"
                    % (taraf, k.get("%s_etiketsiz_oran" % (
                        taraf if taraf != "ikisi" else "ust"), -1),
                       k.get("%s_sinif1_oran" % (
                        taraf if taraf != "ikisi" else "ust"), -1)))

        def özet(d):
            return ("ROTA g=%.3f" % d["guven"]) if d["serit"] is not None \
                else ("RED %s" % (d["sebep"] or "?")[:12])
        print("%-30s %-13s | %-16s | %-16s | %-16s"
              % (ad[-26:], bos_ozet, özet(ham), özet(r_tam), özet(r_bag)))
        sys.stdout.flush()
        sonuc.append({"kare": ad, "bos_taraf": taraf, "kapsam": {
            kk: k[kk] for kk in k if "oran" in kk},
            "ham": ham, "tamamlanmis": r_tam, "bagli": r_bag, "ist": ist})
    n = lambda key: sum(1 for s in sonuc if s[key]["serit"] is not None)
    print("\nHAM %d/%d · TAMAMLANMIS %d/%d · BAGLI %d/%d"
          % (n("ham"), len(sonuc), n("tamamlanmis"), len(sonuc),
             n("bagli"), len(sonuc)))
    (CIK / "c5_etiket_tamamlama.json").write_text(
        json.dumps({"_ne": "ETIKETSIZ bosluk kare-ici nearest-centroid ile "
                           "dolduruldu, uretim analyze_path kosuldu",
                    "kareler": sonuc}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
