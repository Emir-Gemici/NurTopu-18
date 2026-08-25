"""UC DURUMLU MASKE — bicim, goc ve YOLO'ya cevrim.

KARAR: kullanici, 2026-08-25. Gerekce `SU_ETIKETLEME_PLANI.md §4b-EK-2 (B)`.

🔴 NEDEN (amele B buldu, F4): eski cikti `{0,255}` idi ve sartnamenin urettigi
"ETIKETSIZ" hukmu diske **0** yaziliyordu — yani egitimde SERBEST ALANLA AYNI.
   "Her belirsizlik guvensiz yone dusuyor."
Bu, madde 15'in (serbest alani buyuten islem yasak) ve D-210'un (bilinmeyen
zemin ilan edilmez) TERSIDIR.

BICIM:
    PNG degeri   anlam                     YOLO'ya cevrilirken
        0        ETIKETSIZ / bilinmiyor    HICBIR poligon uretilmez
        1        SINIF 0 — surulebilir     class 0 poligonu
        2        SINIF 1 — gecilemez       class 1 poligonu

⚠ 0'in ETIKETSIZ olmasi TASARIMDIR: maske yarim yazilir, yanlis okunur ya da
  bir arac bicimi bilmezse sonuc "anotasyon yok" olur — "burasi surulebilir"
  DEGIL. Bicim FAIL-SAFE'tir. Eski semada ayni kaza "her yer surulebilir"
  uretirdi.
⚠ `CONTRACTS.md` DEGISMEZ: sinif id sozlesmesi hala {0: traversable,
  1: blocked}. Degisen sey ETIKET DOSYASI BICIMI, sinif sozlesmesi degil.

KULLANIM:
  python 132_uc_durumlu_maske.py goc      # eski {0,255} -> {0,2}
  python 132_uc_durumlu_maske.py dogrula  # bicim denetimi
  python 132_uc_durumlu_maske.py yolo     # -> YOLO segment etiketleri
"""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
TABAN = KOK / "results" / "dji_20260822"
ETIKETSIZ, SINIF0, SINIF1 = 0, 1, 2
GECERLI = {ETIKETSIZ, SINIF0, SINIF1}

# Eski maskelerin bulundugu dizinler (F3 + F4 + ustabasi referansi)
ESKI_DIZINLER = [TABAN / "ameleler" / g for g in "ABC"] + \
                [TABAN / "f4" / g for g in "ABC"] + [TABAN / "referans"]


def goc() -> int:
    """Eski {0,255} maskeleri {0,2}'ye cevir.

    🔴 SINIF 0 BILGISI YOKTUR: F3/F4'te ameleler YALNIZ sinif 1 cizdi;
    "burayi surulebilir diye DOGRULADIM" ile "buraya BAKMADIM" ayrimi
    YAPILMADI. Bu yuzden 0 -> ETIKETSIZ'e cevrilir, SINIF0'a DEGIL.
    Sinif 0 icin bu kareler F5'te YENIDEN gecilmelidir.
    """
    cevrilen = atlanan = 0
    for d in ESKI_DIZINLER:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*_sinif1.png")):
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if m is None:
                print(f"  [!] OKUNAMADI: {p}")
                continue
            deg = set(np.unique(m).tolist())
            hedef = p.with_name(p.name.replace("_sinif1.png", "_uc.png"))
            # 🔴 ATLAMA OLCUTU DOSYA VARLIGI, DEGER KUMESI DEGIL.
            #    Ilk surumde "deg <= {0,1,2} ise zaten uc durumlu" deniyordu;
            #    TAMAMEN BOS bir binary maske ({0}) bu kosula UYUYOR ve
            #    atlaniyordu -> `_uc.png` HIC YAZILMIYORDU. 56 maskenin 4'u
            #    (kare 133'un bos maskeleri) boyle SESSIZCE disarida kaldi.
            #    Sayim tutmayinca yakalandi.
            if hedef.is_file():
                atlanan += 1
                continue
            if not deg <= ({0, 255} | GECERLI):
                print(f"  [!] BEKLENMEDIK DEGERLER {sorted(deg)}: {p}")
                continue
            yeni = np.where(m > 127, SINIF1, ETIKETSIZ).astype(np.uint8)
            cv2.imwrite(str(hedef), yeni)
            cevrilen += 1
    print(f"goc: {cevrilen} maske cevrildi · {atlanan} zaten uc durumlu")
    print("⚠ Cevrilen maskelerde SINIF 0 BILGISI YOK (yalniz sinif 1 cizilmisti).")
    return 0


def dogrula() -> int:
    """Her `*_uc.png` yalniz {0,1,2} icermeli."""
    hata = 0
    toplam = 0
    for d in ESKI_DIZINLER:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*_uc.png")):
            toplam += 1
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            deg = set(np.unique(m).tolist()) if m is not None else {"OKUNAMADI"}
            if m is None or not deg <= GECERLI:
                print(f"  🔴 GECERSIZ {sorted(deg)}: {p}")
                hata += 1
    print(f"dogrula: {toplam} maske · gecersiz {hata}")
    return 1 if hata else 0


def maske_to_yolo(maske: np.ndarray, min_alan: int = 40) -> list[str]:
    """Uc durumlu maskeyi YOLO segment satirlarina cevir.

    🔴 CEKIRDEK KURAL: ETIKETSIZ (0) icin HICBIR SATIR URETILMEZ.
    Yani belirsizlik egitimde ne "zemin" ne "engel" olarak gorunur —
    hic gorunmez. Eski binary semada 0 sinif 0 demekti ve belirsizlik
    SERBEST ALAN olarak ogreniliyordu.
    """
    h, w = maske.shape
    satirlar = []
    for deger, sinif_id in ((SINIF0, 0), (SINIF1, 1)):
        ikili = (maske == deger).astype(np.uint8)
        if not ikili.any():
            continue
        konturlar, _ = cv2.findContours(ikili, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        for k in konturlar:
            if cv2.contourArea(k) < min_alan:
                continue
            yak = cv2.approxPolyDP(k, 0.002 * cv2.arcLength(k, True), True)
            if len(yak) < 3:
                continue
            nokta = " ".join(f"{x/w:.6f} {y/h:.6f}" for x, y in yak.reshape(-1, 2))
            satirlar.append(f"{sinif_id} {nokta}")
    return satirlar


def yolo() -> int:
    cikti = TABAN / "yolo_etiket"
    cikti.mkdir(parents=True, exist_ok=True)
    n = bos = 0
    for d in ESKI_DIZINLER:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*_uc.png")):
            m = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
            if m is None:
                continue
            satirlar = maske_to_yolo(m)
            hedef = cikti / (d.name + "__" + p.stem + ".txt")
            hedef.write_text("\n".join(satirlar) + ("\n" if satirlar else ""),
                             encoding="utf-8")
            n += 1
            if not satirlar:
                bos += 1
    print(f"yolo: {n} etiket dosyasi -> {cikti}  (bos {bos})")
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    kip = sys.argv[1] if len(sys.argv) > 1 else "dogrula"
    return {"goc": goc, "dogrula": dogrula, "yolo": yolo}[kip]()


if __name__ == "__main__":
    raise SystemExit(main())
