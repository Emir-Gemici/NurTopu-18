"""T127 — BAKIR (egitime hic girmemis) gercek karelerde aday kiyasi.

NEDEN (mimar D-242 SS3): "secim kaniti ALAN-ICI" terfi kararinin eksenidir.
Elimizde alan-DISI etiketli kume yok (T111/D-198). Ama olculdu: 67 gercek
karenin 11'i copy_paste uretimine HIC girmemistir (`manifest.json`,
sebep "yeterli_guvenli_zemin_yok"). Bu 11 kare EGITIM DISIDIR.

⚠ IKI SINIR BAS TARAFTA YAZILIR, sonuc bunlarla okunur:
  1. YANLI ORNEKLEM: kareler rastgele ayrilmadi; ureteci "yeterli guvenli
     zemin yok" diye ELEDI. Yani sistematik olarak DAHA ZOR kareler.
  2. AYNI SAHA/OTURUM: ayni videolarin komsu kareleri. Olculdu (pHash, en
     yakin egitim karesine): medyan 0,281 · 11'in 1'i 0,094 (neredeyse ayni;
     `frame_000003` <-> egitimdeki `frame_000004`). O kare AYRICA isaretlenir.
  Dolayisiyla bu kume ALAN-DISI degil EGITIM-DISIdir; genelleme kaniti
  SAYILMAZ, yalniz "ezber mi" sorusuna kismi cevap verir.

CATI YER GERCEGI: T121'in elle cizilmis ve UC gorsel turda dogrulanmis
anahtar poligonlarindan ORB+RANSAC homografisiyle tasinir (99'un yontemi
AYNEN; kopya kod yok — 99'daki fonksiyonlar ITHAL edilir). Tasinan her maske
GORSEL olarak dogrulanir (D-80).

CIKTI: results/t127/bakir_cati_maskeleri/*.png · results/t127/ozet.json
       results/t127/dogrulama_sayfa_*.png
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
OLCUM = KOK / "scripts" / "olcum"
KARE_KOK = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "t127"
POLIGONLAR = KOK / "results" / "t121" / "cati_anahtar_poligonlari.json"
MANIFEST = KOK / "dataset" / "copy_paste_gercek" / "manifest.json"
EN_AZ_ESLESME = 40


def _yukle(ad: str, dosya: str):
    spec = importlib.util.spec_from_file_location(ad, OLCUM / dosya)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


Y99 = _yukle("yayilim99", "99_t121_cati_yayilimi.py")


def bakir_kareler() -> list[str]:
    man = json.load(io.open(MANIFEST, encoding="utf-8"))
    uretilen = {o["kaynak"] for o in man["ornekler"] if o.get("cikti")}
    tum = {p.relative_to(KARE_KOK).as_posix()
           for p in KARE_KOK.rglob("*.jpg")}
    return sorted(tum - uretilen)


def capa_havuzu() -> dict[str, Path]:
    """CAPA HAVUZU = T121'in 56 DOGRULANMIS maskesi (yalniz 23 elle cizim degil).

    🔴 NEDEN (olcumle bulundu): ilk surumde capa olarak yalniz elle cizilen
    anahtar kareler kullanildi; `11_44_23/09` ve `/10` icin en yakin anahtar
    IKI kare uzaktaydi ve homografi maskeyi ~50 px KAYDIRDI (gorsel
    dogrulamada goruldu — maske catidan tasip asfalta biniyordu). Kaymis bir
    yer gercegi, modelin dogru cevabini "kacak" diye sayar ve olcumu KIRLETIR.
    Cozum: capa havuzu T121'in TUM dogrulanmis maskeleridir; komsuluk mesafesi
    boylece 1'e duser.
    """
    havuz = {}
    for p in sorted((KOK / "results" / "t121" / "cati_maskeleri").glob("*.png")):
        video, kare = p.stem.split("__")
        havuz[f"{video}/{kare}.jpg"] = p
    return havuz


def main() -> int:
    cfg = json.load(io.open(POLIGONLAR, encoding="utf-8"))["kareler"]
    havuz = capa_havuzu()
    hedefler = bakir_kareler()
    (CIKTI / "bakir_cati_maskeleri").mkdir(parents=True, exist_ok=True)

    kayitlar, hucreler = [], []
    for ad in hedefler:
        bgr = cv2.imread(str(KARE_KOK / ad))
        if bgr is None:
            kayitlar.append({"kare": ad, "yontem": "OKUNAMADI"})
            continue
        sekil = bgr.shape[:2]
        video = ad.split("/")[0]
        no = int(ad.split("/")[1].split("_")[1])
        adaylar = sorted((abs(int(k.split("/")[1].split("_")[1]) - no), k)
                         for k in havuz if k.split("/")[0] == video)
        if not adaylar:
            kayitlar.append({"kare": ad, "yontem": "ANAHTAR_YOK"})
            continue
        mesafe, anahtar = adaylar[0]
        a_bgr = cv2.imread(str(KARE_KOK / anahtar))
        H, inlier = Y99.homografi(cv2.cvtColor(a_bgr, cv2.COLOR_BGR2GRAY),
                                  cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY))
        if H is None or inlier < EN_AZ_ESLESME:
            maske = np.zeros(sekil, np.uint8)
            kayit = {"kare": ad, "yontem": "BASARISIZ", "anahtar": anahtar,
                     "mesafe": mesafe, "inlier": inlier}
        else:
            ham = cv2.imread(str(havuz[anahtar]), 0)
            a_maske = ((ham[:, :, 0] if ham.ndim == 3 else ham) > 127).astype("uint8")
            maske = cv2.warpPerspective(a_maske, H, (sekil[1], sekil[0]),
                                        flags=cv2.INTER_NEAREST)
            kayit = {"kare": ad, "yontem": "HOMOGRAFI", "anahtar": anahtar,
                     "mesafe": mesafe, "inlier": inlier}
        kayit["cati_pay"] = round(float(maske.mean()), 4)
        kayitlar.append(kayit)
        cv2.imwrite(str(CIKTI / "bakir_cati_maskeleri" /
                        (ad.replace("/", "__").replace(".jpg", "") + ".png")),
                    maske * 255)
        gorsel = bgr.copy()
        gorsel[maske > 0] = (gorsel[maske > 0] * 0.45
                             + np.array([0, 0, 255]) * 0.55).astype(np.uint8)
        cv2.putText(gorsel, f"{video[-8:]}/{no:02d} {kayit['yontem'][:4]}"
                    f" pay={kayit['cati_pay']}", (8, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        hucreler.append(cv2.resize(gorsel, (640, 360)))

    for s in range((len(hucreler) + 3) // 4):
        grup = hucreler[s * 4:(s + 1) * 4]
        while len(grup) % 2:
            grup.append(np.zeros_like(grup[0]))
        satir = [np.hstack(grup[i:i + 2]) for i in range(0, len(grup), 2)]
        cv2.imwrite(str(CIKTI / f"dogrulama_sayfa_{s}.png"), np.vstack(satir))

    ozet = {"n_bakir": len(hedefler),
            "yontem_dagilimi": {y: sum(1 for k in kayitlar if k.get("yontem") == y)
                                 for y in {k.get("yontem") for k in kayitlar}},
            "sinirlar": ["YANLI ORNEKLEM: ureteci 'yeterli guvenli zemin yok' "
                          "diye eledi — sistematik olarak daha ZOR kareler",
                          "AYNI SAHA/OTURUM: alan-DISI degil EGITIM-DISI"],
            "kayitlar": kayitlar}
    io.open(CIKTI / "ozet.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in ozet.items() if k != "kayitlar"},
                     ensure_ascii=False, indent=1))
    print(f"sayfa: {(len(hucreler) + 3) // 4} · maske: {CIKTI / 'bakir_cati_maskeleri'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
