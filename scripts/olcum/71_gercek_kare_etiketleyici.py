"""T84 · GERCEK KARE ETIKETLEYICI — yari otomatik, GORSEL ONAYLI.

NEDEN. Elimizdeki tek gercek goruntu 67 otopark karesidir ve ETIKETSIZDIR.
Etiketsiz veri egitime giremez; giremeyince model gercek dokuyu ogrenemez ve
cati/asfalt ayrimini yapamaz (D-118 gorseli: cati YESIL boyaniyor).

TASARIM KURALI — SENTETIK URETECIN EN KRITIK KURALI BURADA DA GECERLIDIR:
**GECILEMEZ NESNE ASLA ETIKETSIZ BIRAKILMAZ.** v16 bu kural ihlal edildigi
icin moloza basmada %2,7'den %31,6'ya cokmustu. Bu yuzden sinif atamasi
"geriye kalan zemindir" mantigiyla YAPILMAZ; her sinif KENDI kaniti ile
isaretlenir ve KANITSIZ kalan piksel `blocked` olur (fail-safe).

UC KANIT (hepsi modelden BAGIMSIZ, klasik):
  1. ARAC   — DOTA OBB yonlu kutulari. K-6'da olculdu: ayni fotografta
              COCO 2 arac, DOTA OBB 93 arac. Kahin budur.
  2. BITKI  — LAB kromasi. Kuru ot ve agac renklidir; asfalt AKROMATIKTIR.
  3. YAPI   — parlak + duz (dusuk yerel varyans) + genis bilesen. Cati asfalttan
              PARLAKLIK ve DOKUSUZLUKLA ayrilir.
Geriye kalan AKROMATIK, ORTA PARLAKLIKTA, DOKULU alan asfalttir -> traversable.

⚠ Bu betik ETIKET ONERIR, ETIKET KESINLESTIRMEZ. Cikti gorsellestirilir ve
GOZLE dogrulanir (D-80: gorsel kazanir). Onaylanmayan kare egitime GIRMEZ.
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(r"O:\navitas")
sys.path.insert(0, str(REPO / "codes"))
from arac_maskesi import ARAC_SINIFLERI                     # noqa: E402

# ── Esikler: hepsi bu dosyada TEK YERDE, gorsel denetimle ayarlanir ─────────
BITKI_KROMA = 12          # LAB kroma sapmasi; gri-dunya notrune gore
# ⚠ YAPI kurali OLCUMLE ayarlandi (dorduncu gecis). Ilk hali "parlak + duz +
# genis" diyordu ve GUNES ALAN ACIK ASFALTI bina saniyordu — tam cozunurlukte
# bakildiginda otoparkin ortasinda kocaman kirmizi lekeler cikti. Aday
# bilesenler tek tek olculdu (ayni kare):
#     cati          alan 31794  L 222,3  DIKDORTGENLIK 0,853
#     asfalt lekesi alan 54250  L 180,0  DIKDORTGENLIK 0,324
#     asfalt lekesi alan 15527  L 212,7  DIKDORTGENLIK 0,339
#     asfalt lekesi alan  3881  L 182,3  DIKDORTGENLIK 0,355
# Cati DIKDORTGENDIR (dogal yapi), gunes lekesi PACAVRADIR. Ayrim keskin.
YAPI_PARLAKLIK = 205      # L ortalamasi (175 -> 205; asfalt lekesi 180-213)
YAPI_DOKU_VAR = 90        # yerel varyans TAVANI — cati DUZDUR
YAPI_DIKDORTGENLIK = 0.45  # alan / minAreaRect alani; cati 0,47-0,85 · leke 0,32-0,36
YAPI_ASGARI_ALAN = 4000   # px; kucuk parlak lekeler yapi degildir
YAPI_KAPAMA = 9           # 15 -> 9: buyuk cekirdek catiyi komsu asfalta YAPISTIRIYORDU
ARAC_CONF = 0.25


def yerel_varyans(gri, k=9):
    g = gri.astype(np.float32)
    ort = cv2.blur(g, (k, k))
    return cv2.blur(g * g, (k, k)) - ort * ort


def etiket_onerisi(img, obb_sonuc):
    """(engel_maskesi, zemin_maskesi, ayrinti) — ikisi ORTUSMEZ, birlesimi TAM."""
    h, w = img.shape[:2]
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    a = lab[:, :, 1].astype(np.int16) - 128
    b = lab[:, :, 2].astype(np.int16) - 128

    # 1) ARAC — OBB poligonlari
    arac = np.zeros((h, w), np.uint8)
    n_arac = 0
    if obb_sonuc.obb is not None and len(obb_sonuc.obb):
        adlar = obb_sonuc.names
        cls = obb_sonuc.obb.cls.cpu().numpy().astype(int)
        poly = obb_sonuc.obb.xyxyxyxy.cpu().numpy()
        for c, p in zip(cls, poly):
            if adlar.get(int(c), str(c)) not in ARAC_SINIFLERI:
                continue
            cv2.fillPoly(arac, [p.reshape(-1, 2).astype(np.int32)], 1)
            n_arac += 1

    # 2) BITKI — kromatik alan.
    # ⚠ MUTLAK kroma KULLANILAMAZ (olculdu, ilk gecis): bu kareler drone
    # kaydidir ve GLOBAL MAVI YATKINLIGI tasir. LAB'de mavi, `b`yi notrden
    # uzaklastirir; mutlak esik asfalti "bitki" sanip ZEMINI ENGEL yapti
    # (zemin orani 0,17 cikti, gorselde asfalt kirmizi bitki yesildi).
    # Cozum GRI-DUNYA: karenin KENDI medyan a/b'si notr kabul edilir. Asfalt
    # baskin yuzey oldugu icin medyan onu temsil eder; bitki ondan SAPAR.
    a0, b0 = float(np.median(a)), float(np.median(b))
    # ⚠ YONSUZ kroma da YETMEZ (olculdu, ikinci gecis): golge de notrden sapar
    # ve arac siralarinin kenarindaki golgeler ENGEL isaretlendi. "Koyu asfalt
    # engeldir" ogretmek golgeli koridorlari kapatir — kabul edilemez.
    # Bitki ile golge FARKLI YONE sapar:
    #     kuru ot / toprak -> SARI  (b - b0 > 0)
    #     agac / cim       -> YESIL (a - a0 < 0)
    #     golge            -> MAVI  (b - b0 < 0)   <- disarida birakilir
    # ⚠ SADECE bitki yonlerini saymak da YETMEZ (olculdu, ucuncu gecis):
    # KIREMIT CATILI bina ne parlak (yapi kurali kacirdi) ne sari/yesil
    # (bitki kurali kacirdi) — ZEMIN isaretlendi. Gecilemez bir yapiyi
    # etiketsiz birakmak uretecin EN KRITIK kural ihlalidir (v16: %2,7 -> %31,6).
    #
    # Kural TERSINE cevrildi: artik "zemin nedir" degil, "NOTR GRI ASFALT
    # DEGILSE ENGELDIR" tanimlanir (fail-safe, madde 15 yonunde).
    #   a ekseninde HER IKI yon  -> yesil (agac) VE kirmizi (kiremit) yakalanir
    #   b ekseninde YALNIZ sari  -> kuru ot yakalanir
    #   b ekseninde MAVI HARIC   -> golge asfalt olarak KALIR (tek istisna)
    bitki = ((np.abs(a - a0) > BITKI_KROMA) |
             ((b - b0) > BITKI_KROMA)).astype(np.uint8)
    bitki = cv2.morphologyEx(bitki, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    # 3) YAPI — parlak VE duz VE genis
    duz = yerel_varyans(L) < YAPI_DOKU_VAR
    aday = ((L > YAPI_PARLAKLIK) & duz).astype(np.uint8)
    aday = cv2.morphologyEx(aday, cv2.MORPH_CLOSE,
                            np.ones((YAPI_KAPAMA, YAPI_KAPAMA), np.uint8))
    n, lbl, st, _ = cv2.connectedComponentsWithStats(aday, 8)
    yapi = np.zeros((h, w), np.uint8)
    n_yapi = 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < YAPI_ASGARI_ALAN:
            continue
        m = (lbl == i).astype(np.uint8)
        kon, _h = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not kon:
            continue
        rect = cv2.minAreaRect(max(kon, key=cv2.contourArea))
        ra = rect[1][0] * rect[1][1]
        # DIKDORTGENLIK: yapi dogal olarak dikdortgendir; gunes alan asfalt
        # lekesi degildir. Bu olcut olmadan asfalt "bina" isaretleniyordu.
        if ra <= 0 or st[i, cv2.CC_STAT_AREA] / ra < YAPI_DIKDORTGENLIK:
            continue
        yapi[lbl == i] = 1
        n_yapi += 1

    engel = ((arac | bitki | yapi) > 0).astype(np.uint8)
    zemin = 1 - engel
    return engel, zemin, {"arac": n_arac, "yapi_bileseni": n_yapi,
                          "engel_orani": float(engel.mean()),
                          "zemin_orani": float(zemin.mean())}


def gorsellestir(img, engel, zemin):
    g = img.copy()
    g[engel > 0] = (0.45 * g[engel > 0] + 0.55 * np.array([0, 0, 255])).astype(np.uint8)
    g[zemin > 0] = (0.65 * g[zemin > 0] + 0.35 * np.array([0, 255, 0])).astype(np.uint8)
    return g


def poligonlar(maske, asgari=250):
    """Maskeyi YOLO-seg poligonlarina cevir. Delikler ic konturla YOK EDILMEZ —
    delik varsa parca ayri poligon olur; kucuk parcalar ATILMAZ, ENGEL tarafina
    birakilir (fail-safe)."""
    kon, _ = cv2.findContours(maske, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cikti = []
    for c in kon:
        if cv2.contourArea(c) < asgari:
            continue
        eps = 0.002 * cv2.arcLength(c, True)
        p = cv2.approxPolyDP(c, eps, True).reshape(-1, 2)
        if len(p) >= 3:
            cikti.append(p)
    return cikti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", type=Path, default=REPO / "data" / "raw_frames")
    ap.add_argument("--cikti", type=Path, required=True)
    ap.add_argument("--obb", type=Path, default=REPO / "yolov8m-obb.pt")
    ap.add_argument("--adim", type=int, default=1, help="her N. kare")
    ap.add_argument("--azami", type=int, default=0, help="0 = sinirsiz")
    ap.add_argument("--yaz-etiket", action="store_true",
                    help="YOLO-seg .txt yaz (varsayilan: yalniz onizleme)")
    args = ap.parse_args()

    from ultralytics import YOLO
    obb = YOLO(str(args.obb), task="obb")

    kareler = sorted(args.kok.rglob("*.jpg"))[::args.adim]
    if args.azami:
        kareler = kareler[:args.azami]
    (args.cikti / "onizleme").mkdir(parents=True, exist_ok=True)
    if args.yaz_etiket:
        (args.cikti / "images").mkdir(parents=True, exist_ok=True)
        (args.cikti / "labels").mkdir(parents=True, exist_ok=True)

    ozet = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            continue
        r = obb.predict(str(p), conf=ARAC_CONF, verbose=False)[0]
        engel, zemin, d = etiket_onerisi(img, r)
        ad = f"{p.parent.name[-8:]}_{p.stem}"
        cv2.imwrite(str(args.cikti / "onizleme" / f"{ad}.jpg"),
                    gorsellestir(img, engel, zemin))
        d["kare"] = ad
        ozet.append(d)

        if args.yaz_etiket:
            h, w = img.shape[:2]
            satirlar = []
            for sinif, mask in ((0, zemin), (1, engel)):
                for poly in poligonlar(mask):
                    xy = poly.astype(np.float32)
                    xy[:, 0] /= w
                    xy[:, 1] /= h
                    satirlar.append(str(sinif) + " " +
                                    " ".join(f"{v:.6f}" for v in xy.reshape(-1)))
            cv2.imwrite(str(args.cikti / "images" / f"{ad}.jpg"), img)
            (args.cikti / "labels" / f"{ad}.txt").write_text(
                "\n".join(satirlar), encoding="utf-8")

    zo = np.array([o["zemin_orani"] for o in ozet])
    print(f"\n{'=' * 62}\nETIKET ONERISI · {len(ozet)} kare\n{'=' * 62}")
    print(f"  arac (kare basina)  ort {np.mean([o['arac'] for o in ozet]):.1f}")
    print(f"  yapi bileseni       ort {np.mean([o['yapi_bileseni'] for o in ozet]):.1f}")
    print(f"  ZEMIN orani         medyan {np.median(zo):.3f} · "
          f"min {zo.min():.3f} · maks {zo.max():.3f}")
    print(f"  (v27'nin ayni karelerdeki zemin kaplamasi: ~0,81 — kapi tavani 0,67)")
    print("=" * 62)
    print(f"onizleme -> {args.cikti / 'onizleme'}")
    (args.cikti / "ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
