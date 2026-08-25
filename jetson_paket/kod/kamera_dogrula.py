"""NEDEN: H3 "DroidCam video dugumunu dogrula, cozunurluk ve FPS bildir" diyor.
rpi_inference.py:505 kamerayi ``cv2.VideoCapture(0)`` ile SABIT acar; DroidCam
URL'si ya da farkli /dev/video dugumu verilemez. Bu betik kaynagi parametrik
alir, akisi olcer ve istege bagli olarak gercek algi zincirini de kosar.

Kaynak ornekleri:
  0                                  -> /dev/video0
  /dev/video2                        -> belirli v4l2 dugumu
  http://127.0.0.1:4747/video        -> DroidCam USB (adb forward sonrasi)
  http://192.168.1.42:4747/video     -> DroidCam WiFi

Yalniz OpenCV + NumPy kullanir (anayasa madde 4).
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2
import numpy as np


def zincir_durumu(bgr, tahmin_maskeleri, *, rota_bul, preprocess, kirp):
    """Tek kare icin algi zinciri: letterbox -> maske -> kirp -> rota_bul -> durum.

    T135 (D-268 §6, results/t142/olcum.md §3): `icerik` kutusu `rota_bul`a
    GECIRILIR. Gecirilmezse 16:9 karede kirpilmis maske + tam tuval paydasi
    zemin saglamlik kapisinin iki kolunu da oldurur (kaplama <= 0,5625,
    kenar <= 0,2815) — kapi hic ateslemez. `tahmin_maskeleri(tuval)` model
    cagrisini sarar; test sahte maske verir.
    """
    tuval, _, icerik = preprocess(bgr)
    mk = kirp(tahmin_maskeleri(tuval), icerik)
    return rota_bul(mk, mpp=None, plan=False, gorsel_cikti=False, icerik=icerik)["durum"]


def kaynagi_coz(metin: str):
    """Sayi ise kamera indeksi, degilse yol/URL olarak birak."""
    try:
        return int(metin)
    except ValueError:
        return metin


def dugumleri_listele() -> None:
    """Linux'ta hangi video dugumleri var, hangileri gercekten aciliyor."""
    kok = Path("/dev")
    if not kok.exists():
        print("(/dev yok — Linux disi sistem, dugum listesi atlandi)")
        return
    dugumler = sorted(kok.glob("video*"))
    if not dugumler:
        print("UYARI: /dev/video* bulunamadi — kamera surucusu yuklu degil")
        return
    print("Bulunan video dugumleri:")
    for d in dugumler:
        cap = cv2.VideoCapture(str(d))
        acildi = cap.isOpened()
        bilgi = ""
        if acildi:
            ok, kare = cap.read()
            bilgi = f"{kare.shape[1]}x{kare.shape[0]}" if ok and kare is not None else "acildi ama kare YOK"
        cap.release()
        print(f"  {str(d):16s} {'ACILDI' if acildi else 'acilmadi':10s} {bilgi}")


def main() -> int:
    a = argparse.ArgumentParser(description="Kamera/DroidCam kaynagini dogrula ve olc")
    a.add_argument("--kaynak", default="0", help="indeks, /dev/videoN ya da http://...:4747/video")
    a.add_argument("--kare", type=int, default=120, help="olculecek kare sayisi")
    a.add_argument("--isinma", type=int, default=15)
    a.add_argument("--kaydet", type=Path, help="ilk kareyi bu yola JPG yaz (gozle dogrulama)")
    a.add_argument("--listele", action="store_true", help="once /dev/video* dugumlerini tara")
    a.add_argument("--zincir", action="store_true",
                   help="algi zincirini de kos (model + get_masks + rota_bul)")
    a.add_argument("--model", type=Path, help="--zincir icin model yolu")
    a.add_argument("--imgsz", type=int, default=640)
    a.add_argument("--conf", type=float, default=0.25)
    args = a.parse_args()

    if args.listele:
        dugumleri_listele()
        print()

    kaynak = kaynagi_coz(args.kaynak)
    print(f"Aciliyor: {kaynak!r}")
    t0 = time.perf_counter()
    cap = cv2.VideoCapture(kaynak)
    acilma_s = time.perf_counter() - t0
    if not cap.isOpened():
        print(f"HATA: kaynak acilamadi: {kaynak!r}")
        print("  - DroidCam USB icin once: adb forward tcp:4747 tcp:4747")
        print("  - Telefonda DroidCam uygulamasi ACIK ve 'baslat' basili olmali")
        print("  - WiFi modunda telefon ve Jetson AYNI agda olmali")
        return 1
    print(f"Acildi ({acilma_s*1000:.0f} ms)")

    bildirilen = {
        "genislik": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "yukseklik": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "fourcc": int(cap.get(cv2.CAP_PROP_FOURCC)),
    }
    kod = bildirilen["fourcc"]
    fourcc_metin = "".join(chr((kod >> (8 * i)) & 0xFF) for i in range(4)) if kod else "?"
    print(f"Surucunun BILDIRDIGI : {bildirilen['genislik']}x{bildirilen['yukseklik']} "
          f"@ {bildirilen['fps']:.2f} FPS  fourcc={fourcc_metin!r}")
    print("  (bildirilen deger yalan olabilir — asil olculen asagida)")

    zincir_fn = None
    if args.zincir:
        if not args.model or not args.model.is_file():
            print("HATA: --zincir icin gecerli --model gerekir")
            cap.release(); return 2
        kod_dizin = Path(__file__).resolve().parent
        if str(kod_dizin) not in sys.path:
            sys.path.insert(0, str(kod_dizin))
        from costmap_path_finder import rota_bul
        from rpi_inference import _maskeleri_icerige_kirp, _preprocess, get_masks
        from ultralytics import YOLO
        model = YOLO(str(args.model), task="segment")
        print(f"Zincir acik: {args.model.name}")

        def tahmin_maskeleri(tuval):
            giris = cv2.resize(tuval, (args.imgsz, args.imgsz), interpolation=cv2.INTER_AREA)
            r = model.predict(giris, imgsz=args.imgsz, conf=args.conf, verbose=False)
            yan = tuval.shape[0]
            return get_masks(r, yan, yan, sinif_idler=(0, 1))

        def zincir_fn(bgr):
            return zincir_durumu(bgr, tahmin_maskeleri, rota_bul=rota_bul,
                                 preprocess=_preprocess, kirp=_maskeleri_icerige_kirp)

    for i in range(args.isinma):
        ok, kare = cap.read()
        if not ok:
            print(f"HATA: isinma karesi {i} okunamadi — akis kararsiz")
            cap.release(); return 1
        if i == 0 and args.kaydet:
            args.kaydet.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(args.kaydet), kare)
            print(f"Ilk kare yazildi: {args.kaydet}  ({kare.shape[1]}x{kare.shape[0]})")

    gecikmeler: list[float] = []
    durumlar: dict[str, int] = {}
    dusen = 0
    t_bas = time.perf_counter()
    for _ in range(args.kare):
        t = time.perf_counter()
        ok, kare = cap.read()
        if not ok or kare is None:
            dusen += 1
            continue
        if zincir_fn is not None:
            d = zincir_fn(kare)
            durumlar[d] = durumlar.get(d, 0) + 1
        gecikmeler.append((time.perf_counter() - t) * 1000)
    toplam_s = time.perf_counter() - t_bas
    cap.release()

    if not gecikmeler:
        print("HATA: hic kare okunamadi")
        return 1

    g = np.array(gecikmeler)
    print("\n" + "=" * 62)
    print(f"okunan kare      : {len(gecikmeler)}  (dusen: {dusen})")
    print(f"kare gecikmesi   : p50={np.percentile(g,50):.2f} ms  p95={np.percentile(g,95):.2f} ms")
    print(f"OLCULEN FPS      : {len(gecikmeler)/toplam_s:.2f}")
    print(f"cozunurluk       : {kare.shape[1]}x{kare.shape[0]}")
    if durumlar:
        print(f"rota durumlari   : {durumlar}")
    print("=" * 62)
    if dusen > len(gecikmeler) * 0.05:
        print("UYARI: kare dusme orani %5'in ustunde — baglanti kararsiz")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
