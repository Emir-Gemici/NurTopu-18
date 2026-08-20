"""T122 — MODEL-FREE cati kahini icin IKINCI deneme: kenar-gudumlu buyutme.

🔴 71'i DEGISTIRMEZ (olcum; kural karari mimarin, SS9.2).

GECMIS: D-234'te "golge istisnasi" hipotezim KURULDU ve DUSTU. Kacan cati
pikselleri olculdu: L medyan 134 · yerel varyans 336 · akromatik — yani
oluklu sac cati, 71'in parlaklik/duzluk/kroma olcutlerine ASFALT gorunuyor.
Ayni kayitta "geometri kullanilabilir" demistim; burada O DA OLCULUYOR.

DENEME: cati TEK PARCADIR ve parlak yamaci 71 zaten buluyor (YAPI). Karanlik
yamac o parlak parcaya BITISIKTIR ve asfalttan GUCLU BIR KENARLA ayrilir
(bina siniri). Bu yuzden:
  tohum(on plan) = YAPI maskesi (asindirilmis)
  tohum(arka plan) = YAPI'dan UZAK bolge
  sinir            = Sobel gradyan siddeti uzerinde watershed
Watershed, ayrimi renk/parlaklik yerine KENAR uzerinden kurar — iki yuzeyin
istatistigi ayni olsa bile aralarindaki bina kenari keskindir.

IKI YONLU OLCUM (D-234 dersi): KAZANC = cati kacaginin dususu ·
RISK = cati DISINDA yeni engel isaretlenen alan (asfalt kaybi).
Tek yonlu rapor kabul edilmez.

CIKTI: results/t122/cati_buyutme.json + cati_buyutme.png
"""
from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t122"

spec = importlib.util.spec_from_file_location(
    "d110", KOK / "scripts" / "olcum" / "110_t122_golge_kurali_denemesi.py")
D110 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(D110)

TOHUM_ASINDIRMA = 9       # on plan tohumu: YAPI'nin ic kismi
ARKA_UZAKLIK = 61         # arka plan tohumu: YAPI'dan bu kadar uzak
BUYUME_TAVANI = 6.0       # buyuyen alan / tohum alani; ustunde SISME sayilir


def watershed_buyut(img: np.ndarray, yapi: np.ndarray) -> np.ndarray:
    """YAPI tohumundan kenar-gudumlu buyume. Sismeyi TAVANLA sinirlar."""
    if not yapi.any():
        return np.zeros(yapi.shape, np.uint8)
    on = cv2.erode(yapi, np.ones((TOHUM_ASINDIRMA, TOHUM_ASINDIRMA), np.uint8))
    if not on.any():
        on = yapi.copy()
    uzak = cv2.dilate(yapi, np.ones((ARKA_UZAKLIK, ARKA_UZAKLIK), np.uint8))
    arka = (uzak == 0).astype(np.uint8)
    if not arka.any():
        return yapi.copy()

    isaret = np.zeros(yapi.shape, np.int32)
    isaret[arka > 0] = 1
    isaret[on > 0] = 2
    cv2.watershed(img, isaret)
    buyuyen = (isaret == 2).astype(np.uint8)
    # SISME KORKULUGU: kenar zayifsa watershed asfalta tasar. Tohumun
    # BUYUME_TAVANI katini asan sonuc kabul edilmez (olcum bunu da raporlar).
    if buyuyen.sum() > BUYUME_TAVANI * max(1, yapi.sum()):
        return yapi.copy()
    return np.maximum(buyuyen, yapi)


def main() -> int:
    kayitlar, hucreler, sisen = [], [], 0
    for cp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(cp), 0)
        cati = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127)
        if not cati.any():
            continue
        video, kare = cp.stem.split("__")
        img = cv2.imread(str(KARE_KOK / f"{video}/{kare}.jpg"))
        if img is None:
            continue
        bitki, yapi, _golge = D110.bitki_ve_yapi(img)
        temel = ((bitki | yapi) > 0)
        buyuk = watershed_buyut(img, yapi)
        sisen += int(buyuk.sum() > BUYUME_TAVANI * max(1, yapi.sum()))
        duzeltilmis = temel | (buyuk > 0)

        cati_px = int(cati.sum())
        dis = ~cati
        kayit = {
            "kare": f"{video}/{kare}",
            "TEMEL_cati_kacak": round(float((~temel & cati).sum() / cati_px), 4),
            "BUYUTULMUS_cati_kacak": round(
                float((~duzeltilmis & cati).sum() / cati_px), 4),
            "TEMEL_cati_disi_engel": round(float((temel & dis).sum() / dis.sum()), 4),
            "BUYUTULMUS_cati_disi_engel": round(
                float((duzeltilmis & dis).sum() / dis.sum()), 4),
            "yapi_px": int(yapi.sum()), "buyuyen_px": int(buyuk.sum()),
        }
        kayit["cati_disi_YENI_engel"] = round(
            kayit["BUYUTULMUS_cati_disi_engel"] - kayit["TEMEL_cati_disi_engel"], 4)
        kayitlar.append(kayit)

        if len(hucreler) < 4:
            g = img.copy()
            yeni = (buyuk > 0) & ~temel
            g[temel] = (g[temel] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
            g[yeni] = (0, 255, 255)
            g[cati & ~duzeltilmis] = (255, 0, 255)
            cv2.putText(g, f"{kare[6:12]} {kayit['TEMEL_cati_kacak']:.2f}->"
                        f"{kayit['BUYUTULMUS_cati_kacak']:.2f} "
                        f"disi+{kayit['cati_disi_YENI_engel']:.3f}", (8, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            hucreler.append(cv2.resize(g, (640, 360)))

    def ort(k):
        return round(float(np.mean([r[k] for r in kayitlar])), 4)

    ozet = {
        "n_kare": len(kayitlar), "sisme_korkulugu_devreye_giren_kare": sisen,
        "parametreler": {"tohum_asindirma": TOHUM_ASINDIRMA,
                          "arka_uzaklik": ARKA_UZAKLIK,
                          "buyume_tavani": BUYUME_TAVANI},
        "KAZANC": {"temel_cati_kacak_ort": ort("TEMEL_cati_kacak"),
                    "buyutulmus_cati_kacak_ort": ort("BUYUTULMUS_cati_kacak")},
        "RISK": {"temel_cati_disi_engel_ort": ort("TEMEL_cati_disi_engel"),
                  "buyutulmus_cati_disi_engel_ort": ort("BUYUTULMUS_cati_disi_engel"),
                  "cati_disi_YENI_engel_ort": ort("cati_disi_YENI_engel")},
        "kiyas_kahin_v5c": "D-232: aday_v5c cati kacagi 0,121 (ogrenilmis kahin)",
        "kayitlar": kayitlar,
    }
    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "cati_buyutme.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    if hucreler:
        while len(hucreler) % 2:
            hucreler.append(np.zeros_like(hucreler[0]))
        satir = [np.hstack(hucreler[i:i + 2]) for i in range(0, len(hucreler), 2)]
        cv2.imwrite(str(CIKTI / "cati_buyutme.png"), np.vstack(satir))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
