"""TEZGAH: Jetson monitorunde canli CSI onizleme + buyuk keskinlik gostergesi (ONARIM-04/05).

Lens odak halkasini elle ayarlamak icin. Uretim kodu DEGIL. Kamerayi >= 10 m uzaga
cevir, halkayi yavasca dondur; "EN IYI" degerine en yakin noktada vidayi sik.
Kullanim (Jetson masaustu oturumu, SSH'tan):
  DISPLAY=:1 XAUTHORITY=/run/user/1000/gdm/Xauthority /usr/bin/python3 scripts/tezgah/odak_onizleme.py
Cikis: pencerede q / Esc, ya da SIGINT.
"""
import argparse
import sys
from pathlib import Path

import cv2

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "codes"))
from kare_keskinligi import (KESKIN_BULANIK, KESKIN_NET, kare_keskinligi,  # noqa: E402
                             keskinlik_bandi)

RENK = {KESKIN_NET: (0, 200, 0), KESKIN_BULANIK: (0, 0, 255)}


def boru_hatti(sensor, gen, yuk, fps):
    return (f"nvarguscamerasrc sensor-id={sensor} ! video/x-raw(memory:NVMM),width={gen},"
            f"height={yuk},framerate={fps}/1 ! nvvidconv ! video/x-raw,format=BGRx ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensor", type=int, default=0)
    ap.add_argument("--genislik", type=int, default=1920)
    ap.add_argument("--yukseklik", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--pencere-genislik", type=int, default=1600)
    a = ap.parse_args()
    cap = cv2.VideoCapture(boru_hatti(a.sensor, a.genislik, a.yukseklik, a.fps), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("KAMERA ACILAMADI (nvargus). Kopru/baska surec kamerayi tutuyor olabilir.")
        return 2
    en_iyi = 0.0
    cv2.namedWindow("NAVITAS odak", cv2.WINDOW_NORMAL)
    try:
        while True:
            ok, kare = cap.read()
            if not ok or kare is None:
                continue
            d = kare_keskinligi(kare)
            en_iyi = max(en_iyi, d)
            bant = keskinlik_bandi(d)
            renk = RENK.get(bant, (0, 200, 255))
            s = a.pencere_genislik / kare.shape[1]
            goster = cv2.resize(kare, (a.pencere_genislik, round(kare.shape[0] * s)))
            h, w = goster.shape[:2]
            cv2.rectangle(goster, (0, 0), (w, 150), (0, 0, 0), -1)
            cv2.putText(goster, f"KESKINLIK {d:7.1f}  {bant}", (20, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 2.0, renk, 4)
            cv2.putText(goster, f"EN IYI {en_iyi:7.1f}   (r: sifirla, q: cik)  NET>=100 BULANIK<20",
                        (20, 125), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.line(goster, (w // 2 - 40, h // 2), (w // 2 + 40, h // 2), (0, 255, 255), 2)
            cv2.line(goster, (w // 2, h // 2 - 40), (w // 2, h // 2 + 40), (0, 255, 255), 2)
            cv2.imshow("NAVITAS odak", goster)
            tus = cv2.waitKey(1) & 0xFF
            if tus in (ord("q"), 27):
                break
            if tus == ord("r"):
                en_iyi = 0.0
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()
    print(f"son en iyi keskinlik: {en_iyi:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
