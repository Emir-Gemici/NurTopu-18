"""T122 — 71'in GOLGE ISTISNASI icin duzeltme adayinin OLCUMU (uygulama DEGIL).

🔴 71'i DEGISTIRMEZ. Etiket kuralini degistirmek veri sozlesmesi degisikligidir
ve mimarin kararidir (AGENTS SS9.2). Bu betik yalnizca "onerilen kural ne
kazandirir, ne kaybettirir" sorusunu OLCER.

KUSUR (D-232, olculdu): 71 catinin %49,4'unu ZEMIN sayiyor. Gorsel doğrulama
kaçağın CATININ GOLGELI YAMACI oldugunu gosterdi. Mekanizma 71'in kendi
yorumlarindan okunuyor:
  · YAPI kurali parlak+duz+dikdortgen ister (L > 205) — golgeli yamac PARLAK DEGIL;
  · BITKI kurali "mavi yon" sapmasini BILEREK disarida birakir (D-127 ikinci
    gecis: golgeli asfalti engel yapmak koridorlari kapatiyordu).
Yamac iki agin ARASINDAN dusuyor.

DUZELTME ADAYI: golge kurtarmasi YALNIZ acik alanda gecerli olsun; bir YAPI
bilesenine BITISIK (genisletilmis maskeyle kesisen) koyu/mavi bolge, o yapinin
KENDI golgeli yuzeyidir ve ENGEL sayilsin.

IKI YONLU OLCUM (tek yonlu olcum bu projede kabul edilmez):
  KAZANC : cati alanindaki kacak ne kadar duser (yer gercegi: T121'in uc
           gorsel turda dogrulanmis cati maskeleri, 55 kare)
  RISK   : cati DISINDA yeni engel isaretlenen alan ne kadar artar — yani
           D-127'nin korumaya calistigi "golgeli asfalt" ne kadar kapaniyor.
Kazanci raporlayip riski raporlamamak, D-127'nin dustugu tuzagin aynisidir.

CIKTI: results/t122/golge_kurali.json + golge_kurali.png
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t122"

spec = importlib.util.spec_from_file_location(
    "etiketleyici71", KOK / "scripts" / "olcum" / "71_gercek_kare_etiketleyici.py")
E71 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E71)

GOLGE_BITISIKLIK = 25      # px; yapinin golgesi ona BITISIKTIR (kernel yaricapi)


def bitki_ve_yapi(img) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """71'in BITKI ve YAPI kurallarini AYNEN uygular (sabitler 71'den).

    Arac katmani DISARIDA birakilir: olcum cati bolgesine bakiyor ve iki
    varyant da ayni sekilde araciz kuruluyor — kural degisikligi YALITILIR.
    """
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0].astype(np.int16)
    a = lab[:, :, 1].astype(np.int16)
    b = lab[:, :, 2].astype(np.int16)
    a0, b0 = float(np.median(a)), float(np.median(b))
    h, w = L.shape

    bitki = ((np.abs(a - a0) > E71.BITKI_KROMA) |
             ((b - b0) > E71.BITKI_KROMA)).astype(np.uint8)
    bitki = cv2.morphologyEx(bitki, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

    duz = E71.yerel_varyans(L) < E71.YAPI_DOKU_VAR
    aday = ((L > E71.YAPI_PARLAKLIK) & duz).astype(np.uint8)
    aday = cv2.morphologyEx(aday, cv2.MORPH_CLOSE,
                            np.ones((E71.YAPI_KAPAMA, E71.YAPI_KAPAMA), np.uint8))
    n, lbl, st, _ = cv2.connectedComponentsWithStats(aday, 8)
    yapi = np.zeros((h, w), np.uint8)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < E71.YAPI_ASGARI_ALAN:
            continue
        m = (lbl == i).astype(np.uint8)
        kon, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not kon:
            continue
        rect = cv2.minAreaRect(max(kon, key=cv2.contourArea))
        ra = rect[1][0] * rect[1][1]
        if ra <= 0 or st[i, cv2.CC_STAT_AREA] / ra < E71.YAPI_DIKDORTGENLIK:
            continue
        yapi[lbl == i] = 1

    golge = ((b - b0) < -E71.BITKI_KROMA).astype(np.uint8)   # MAVI yon = golge
    return bitki, yapi, golge


def yapiya_bitisik_golge(yapi: np.ndarray, golge: np.ndarray) -> np.ndarray:
    """Golge bileseni genisletilmis YAPI ile kesisiyorsa -> yapinin kendi golgesi."""
    if not yapi.any() or not golge.any():
        return np.zeros_like(golge)
    genis = cv2.dilate(yapi, np.ones((GOLGE_BITISIKLIK, GOLGE_BITISIKLIK), np.uint8))
    n, lbl, _st, _ = cv2.connectedComponentsWithStats(golge, 8)
    sonuc = np.zeros_like(golge)
    for i in range(1, n):
        m = lbl == i
        if (genis[m] > 0).any():
            sonuc[m] = 1
    return sonuc


def main() -> int:
    kayitlar, hucreler = [], []
    for cp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(cp), 0)
        cati = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        if not cati.any():
            continue
        video, kare = cp.stem.split("__")
        img = cv2.imread(str(KARE_KOK / f"{video}/{kare}.jpg"))
        if img is None:
            continue
        bitki, yapi, golge = bitki_ve_yapi(img)
        temel = ((bitki | yapi) > 0)
        ek = yapiya_bitisik_golge(yapi, golge) > 0
        duzeltilmis = temel | ek

        cati_px = int(cati.sum())
        dis = ~cati
        kayit = {
            "kare": f"{video}/{kare}",
            "cati_px": cati_px,
            "TEMEL_cati_kacak": round(float((~temel & cati).sum() / cati_px), 4),
            "DUZELTILMIS_cati_kacak": round(
                float((~duzeltilmis & cati).sum() / cati_px), 4),
            "TEMEL_cati_disi_engel_pay": round(float((temel & dis).sum() / dis.sum()), 4),
            "DUZELTILMIS_cati_disi_engel_pay": round(
                float((duzeltilmis & dis).sum() / dis.sum()), 4),
        }
        kayit["cati_disi_YENI_engel_pay"] = round(
            kayit["DUZELTILMIS_cati_disi_engel_pay"]
            - kayit["TEMEL_cati_disi_engel_pay"], 4)
        kayitlar.append(kayit)

        if len(hucreler) < 4:
            g = img.copy()
            yeni = ek & ~temel
            g[temel] = (g[temel] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
            g[yeni] = (0, 255, 255)          # sari: kuralin YENI ekledigi
            g[cati & ~duzeltilmis] = (255, 0, 255)   # mor: HALA kacan cati
            cv2.putText(g, f"{kare[6:12]} kacak {kayit['TEMEL_cati_kacak']:.2f}"
                        f"->{kayit['DUZELTILMIS_cati_kacak']:.2f}", (8, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
            hucreler.append(cv2.resize(g, (640, 360)))

    def ort(k):
        return round(float(np.mean([r[k] for r in kayitlar])), 4)

    ozet = {
        "n_kare": len(kayitlar),
        "golge_bitisiklik_px": GOLGE_BITISIKLIK,
        "KAZANC": {"temel_cati_kacak_ort": ort("TEMEL_cati_kacak"),
                    "duzeltilmis_cati_kacak_ort": ort("DUZELTILMIS_cati_kacak")},
        "RISK": {"temel_cati_disi_engel_ort": ort("TEMEL_cati_disi_engel_pay"),
                  "duzeltilmis_cati_disi_engel_ort": ort("DUZELTILMIS_cati_disi_engel_pay"),
                  "cati_disi_YENI_engel_ort": ort("cati_disi_YENI_engel_pay")},
        "not": ("cati disi YENI engel, D-127'nin korumaya calistigi 'golgeli "
                "asfalt' kaybidir; kazanc bu maliyetle birlikte okunur."),
        "kayitlar": kayitlar,
    }
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "golge_kurali.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    if hucreler:
        while len(hucreler) % 2:
            hucreler.append(np.zeros_like(hucreler[0]))
        satir = [np.hstack(hucreler[i:i + 2]) for i in range(0, len(hucreler), 2)]
        cv2.imwrite(str(CIKTI / "golge_kurali.png"), np.vstack(satir))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    print("⚠ 71 DEGISTIRILMEDI — bu bir OLCUM, uygulama karari mimarin.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
