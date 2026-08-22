"""F2 — SU/KORIDOR REFERANS MASKESI (ustabasi cizer, amelelerden ONCE).

On kayit: `results/dji_20260822/su_on_kayit.md`
Sartname : `results/dji_20260822/SU_ETIKETLEME_PLANI.md §4b` (kullanici onayladi)

🔴 NEDEN OTOMATIK ONERI + ELLE DUZELTME:
D-273'te olculdu ki GOZLE OKUMA guvenilmez — ameleler 100 px izgarada kenari
x=118 okuyup piksel profilinde x=170 buldu (52 px hata). Bu yuzden referans da
OLCUMLE baslar. Ama otomatik oneri SARTNAMEYI BILMEZ: menfez tabliyesi
(S4) suyun ustundedir ve GECILEBILIR; oneri onu koridora katiyor. Bu yuzden
oneri HAM MADDEDIR, hukum degil; her kare gozle denetlenir (D-80) ve
`ELLE_DUZELTME` ile duzeltilir.

YONTEM (sartname §4b'nin dogrudan karsiligi):
  su      = dusuk yerel doku (std<8) VE koyu (V<100)
  yesil   = asiri yesil indeksi (2G-R-B) > 18   -> gecilemez kiyi ortusu
  SINIF 1 = (su ∪ yesil) bilesenlerinden SUYA BITISIK olanlar
            ("suya bitisik" = bilesende >= 150 su pikseli)
            + delik doldurma (sartname: butun poligon, delik acilmaz)
  ELLE    = S4 tabliyesi gibi istisnalar poligonla CIKARILIR/EKLENIR

⚠ Bu betik SINIF 1 uretir. SINIF 0 (surulebilir zemin) AYRI turda cizilir;
  ikisini tek gecişte uretmek, hangi kusurun hangisinden geldigini ayirmayi
  imkansiz kilar.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
ATAMA = KOK / "results" / "dji_20260822" / "su_pilot_atama.json"
CIKTI = KOK / "results" / "dji_20260822" / "referans"

OLCEK = 4          # 3840x2160 -> 960x540 (maske bu olcekte tutulur)
SU_STD = 8.0       # yerel standart sapma esigi
SU_V = 100         # parlaklik esigi
YESIL_ESIK = 18    # 2G-R-B
MIN_SU_PX = 150    # bir bilesenin "suya bitisik" sayilmasi icin

# ── ELLE DUZELTME — her biri GOZLE dogrulanip gerekcesiyle yazilir ──────────
# Bicim: dosya_anahtari -> {"cikar": [poligon...], "ekle": [poligon...]}
# Poligon: 960x540 olceginde [(x, y), ...]
ELLE_DUZELTME: dict[str, dict] = {}


def su_maskesi(k: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(k, cv2.COLOR_BGR2HSV)
    gri = cv2.cvtColor(k, cv2.COLOR_BGR2GRAY).astype(np.float32)
    ort = cv2.blur(gri, (9, 9))
    std = np.sqrt(np.maximum(cv2.blur(gri * gri, (9, 9)) - ort * ort, 0))
    return ((std < SU_STD) & (hsv[:, :, 2] < SU_V)).astype(np.uint8)


def koridor(k: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    b, g, r = [x.astype(np.float32) for x in cv2.split(k)]
    yesil = ((2 * g - r - b) > YESIL_ESIK).astype(np.uint8)
    su = su_maskesi(k)
    ham = cv2.morphologyEx((su | yesil).astype(np.uint8), cv2.MORPH_CLOSE,
                           np.ones((15, 15), np.uint8))
    n, lab, _, _ = cv2.connectedComponentsWithStats(ham, 8)
    tut = np.zeros_like(ham)
    for i in range(1, n):
        bilesen = lab == i
        if int(su[bilesen].sum()) >= MIN_SU_PX:
            tut[bilesen] = 1
    tut = cv2.morphologyEx(tut, cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8))
    kontur, _ = cv2.findContours(tut, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(tut, kontur, -1, 1, -1)
    return tut, su


def duzelt(maske: np.ndarray, anahtar: str) -> tuple[np.ndarray, int]:
    d = ELLE_DUZELTME.get(anahtar)
    if not d:
        return maske, 0
    m = maske.copy()
    sayi = 0
    for poli in d.get("ekle", []):
        cv2.fillPoly(m, [np.array(poli, np.int32)], 1); sayi += 1
    for poli in d.get("cikar", []):
        cv2.fillPoly(m, [np.array(poli, np.int32)], 0); sayi += 1
    return m, sayi


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    at = json.load(open(ATAMA, encoding="utf-8"))
    CIKTI.mkdir(parents=True, exist_ok=True)
    ozet = []
    paneller, etiketler = [], []
    for a in at["kareler"]:
        p = KARE_KOK / a["dosya"]
        if not p.is_file():
            raise SystemExit(f"[DUR] kare DISKTE YOK: {p}")
        im = cv2.imread(str(p))
        h, w = im.shape[:2]
        k = cv2.resize(im, (w // OLCEK, h // OLCEK), interpolation=cv2.INTER_AREA)
        m, su = koridor(k)
        anahtar = Path(a["dosya"]).stem
        m, n_duz = duzelt(m, anahtar)
        cv2.imwrite(str(CIKTI / f"{anahtar}_sinif1.png"), (m * 255).astype(np.uint8))
        ozet.append({"dosya": a["dosya"], "kapsam": a["kapsam"],
                     "sinif1_oran": round(float(m.mean()), 4),
                     "su_oran": round(float(su.mean()), 4),
                     "elle_duzeltme": n_duz})
        bb = k.copy()
        bb[m > 0] = (0.45 * np.array([0, 0, 255]) + 0.55 * bb[m > 0]).astype(np.uint8)
        bb[(su > 0) & (m > 0)] = (
            0.55 * np.array([255, 60, 255]) + 0.45 * bb[(su > 0) & (m > 0)]).astype(np.uint8)
        paneller.append(np.hstack([k, bb]))
        etiketler.append(f"{anahtar[-13:]} %{100*m.mean():.1f}"
                         + (f" ELLE:{n_duz}" if n_duz else ""))
        print(f"  {a['dosya']:52s} sinif1 %{100*m.mean():5.1f} · su %{100*su.mean():4.1f}"
              f" · elle {n_duz}")

    hh = paneller[0].shape[0]
    sayfa = np.vstack(paneller)
    for i, e in enumerate(etiketler):
        for c, t in (((0, 0, 0), 4), ((0, 255, 255), 2)):
            cv2.putText(sayfa, e, (8, i * hh + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, c, t)
    sayfa = cv2.resize(sayfa, (sayfa.shape[1] // 2, sayfa.shape[0] // 2))
    cv2.imwrite(str(CIKTI / "dogrulama_sayfasi.jpg"), sayfa,
                [cv2.IMWRITE_JPEG_QUALITY, 82])
    json.dump({"_ne": "F2 referans SINIF 1 (su + gecilemez kiyi) — ustabasi",
               "_on_kayit": "results/dji_20260822/su_on_kayit.md",
               "_parametreler": {"olcek": OLCEK, "su_std": SU_STD, "su_v": SU_V,
                                 "yesil_esik": YESIL_ESIK, "min_su_px": MIN_SU_PX},
               "kareler": ozet},
              open(CIKTI / "referans_ozeti.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\nyazildi: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
