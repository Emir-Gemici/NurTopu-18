"""TEZGAH: Jetson monitorunde canli CSI onizleme + keskinlik + orta kare mesafe TAHMINI (ONARIM-04/05).

Uretim kodu DEGIL. Lens odagi ve 20-30 m gorus testi icin.

MESAFE — ONEMLI SINIR: tek kamera mesafeyi OLCEMEZ. Burada gosterilen deger
  mesafe ≈ fx · W / w_px   (pinhole; fx = (genislik/2) / tan(FOV/2))
TAHMINDIR ve iki BEYANA dayanir: (1) yatay FOV (varsayilan 63°, FDR B3 "55–63°",
OLCULMEDI), (2) orta karedeki nesnenin GERCEK genisligi W (+/- tuslariyla girilir).
Nesnenin piksel genisligi w_px orta karenin icinde, merkeze dokunan en buyuk kenar
konturundan otomatik bulunur — arka plan karmasiksa yanlis olabilir; ekranda cizilen
yesil kutuya bak. Ayrica orta karenin 10/20/30 m'de kac metreyi kapladigi gosterilir.

KAYIT: her ~1 s bir JSONL satiri + her 15 s bir kare (jpg):
  ~/navitas/results/jetson_log/odak_testi/<tarih>_<boot8>/  (kosum.jsonl, kare_*.jpg)
  s tusu: o anki kareyi hemen kaydeder.

Kullanim (SSH'tan, Jetson masaustu oturumuna):
  DISPLAY=:1 XAUTHORITY=/run/user/1000/gdm/Xauthority /usr/bin/python3 scripts/tezgah/odak_onizleme.py
Tuslar: + / - nesne genisligi (0,1 m) · [ / ] orta kare boyutu · r en iyi sifirla · s kare kaydet · q/Esc cik
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "codes"))
from kare_keskinligi import (KESKIN_BULANIK, KESKIN_NET, kare_keskinligi,  # noqa: E402
                             keskinlik_bandi)

RENK = {KESKIN_NET: (0, 200, 0), KESKIN_BULANIK: (0, 0, 255)}


def boru_hatti(sensor, gen, yuk, fps):
    return (f"nvarguscamerasrc sensor-id={sensor} ! video/x-raw(memory:NVMM),width={gen},"
            f"height={yuk},framerate={fps}/1 ! nvvidconv ! video/x-raw,format=BGRx ! "
            "videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1")


def odak_px(genislik_px, fov_derece):
    return (genislik_px / 2.0) / math.tan(math.radians(fov_derece) / 2.0)


def roi_nesne_genisligi(roi):
    """Orta karede merkeze dokunan/en yakin buyuk kenar konturunun (x,y,w,h) kutusu ya da None."""
    gri = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    gri = cv2.GaussianBlur(gri, (5, 5), 0)
    kenar = cv2.Canny(gri, 40, 120)
    kenar = cv2.dilate(kenar, np.ones((5, 5), np.uint8), iterations=2)
    konturlar, _ = cv2.findContours(kenar, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not konturlar:
        return None
    h, w = gri.shape
    merkez = (w / 2.0, h / 2.0)
    en_iyi, en_iyi_puan = None, None
    for k in konturlar:
        x, y, kw, kh = cv2.boundingRect(k)
        # sol ve sag kenara birden degen kutu: nesne kareden genis -> genislik OLCULEMEZ
        if kw < 8 or kh < 8 or (x <= 1 and x + kw >= w - 1):
            continue
        icinde = x <= merkez[0] <= x + kw and y <= merkez[1] <= y + kh
        uzak = math.hypot(x + kw / 2 - merkez[0], y + kh / 2 - merkez[1])
        puan = (0 if icinde else 1, uzak, -kw * kh)
        if en_iyi_puan is None or puan < en_iyi_puan:
            en_iyi, en_iyi_puan = (x, y, kw, kh), puan
    return en_iyi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sensor", type=int, default=0)
    ap.add_argument("--genislik", type=int, default=1920)
    ap.add_argument("--yukseklik", type=int, default=1080)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--fov", type=float, default=63.0, help="yatay FOV derece — BEYAN (olculmedi)")
    ap.add_argument("--nesne-m", type=float, default=1.0, help="orta karedeki nesnenin gercek genisligi m")
    ap.add_argument("--kare-oran", type=float, default=0.12, help="orta kare kenari / kare genisligi")
    ap.add_argument("--pencere-genislik", type=int, default=1600)
    ap.add_argument("--kayit-dizin", type=Path,
                    default=Path.home() / "navitas" / "results" / "jetson_log" / "odak_testi")
    a = ap.parse_args()

    try:
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip().replace("-", "")[:8]
    except OSError:
        boot = "bootyok"
    kayit = a.kayit_dizin / f"{time.strftime('%Y%m%d_%H%M%S')}_{boot}"
    kayit.mkdir(parents=True, exist_ok=True)
    jsonl = (kayit / "kosum.jsonl").open("a", encoding="utf-8")

    cap = cv2.VideoCapture(boru_hatti(a.sensor, a.genislik, a.yukseklik, a.fps), cv2.CAP_GSTREAMER)
    if not cap.isOpened():
        print("KAMERA ACILAMADI (nvargus). Kopru/baska surec kamerayi tutuyor olabilir.")
        return 2
    en_iyi = en_iyi_roi = 0.0
    nesne_m, kare_oran = a.nesne_m, a.kare_oran
    son_satir = son_jpg = 0.0
    cv2.namedWindow("NAVITAS odak", cv2.WINDOW_NORMAL)
    print(f"kayit: {kayit}", flush=True)
    try:
        while True:
            ok, kare = cap.read()
            if not ok or kare is None:
                continue
            H, W = kare.shape[:2]
            fx = odak_px(W, a.fov)
            d = kare_keskinligi(kare)
            en_iyi = max(en_iyi, d)
            kenar = max(40, int(W * kare_oran))
            x0, y0 = W // 2 - kenar // 2, H // 2 - kenar // 2
            roi = kare[y0:y0 + kenar, x0:x0 + kenar]
            d_roi = kare_keskinligi(roi)
            en_iyi_roi = max(en_iyi_roi, d_roi)
            kutu = roi_nesne_genisligi(roi)
            mesafe = (fx * nesne_m / kutu[2]) if kutu else None
            kapsam = {m: kenar * m / fx for m in (10, 20, 30)}

            s = a.pencere_genislik / W
            goster = cv2.resize(kare, (a.pencere_genislik, round(H * s)))
            gh, gw = goster.shape[:2]
            gx0, gy0, gk = round(x0 * s), round(y0 * s), round(kenar * s)
            cv2.rectangle(goster, (gx0, gy0), (gx0 + gk, gy0 + gk), (0, 255, 255), 2)
            if kutu:
                bx, by, bw, bh = kutu
                cv2.rectangle(goster, (gx0 + round(bx * s), gy0 + round(by * s)),
                              (gx0 + round((bx + bw) * s), gy0 + round((by + bh) * s)), (0, 255, 0), 2)
            cv2.rectangle(goster, (0, 0), (gw, 200), (0, 0, 0), -1)
            bant = keskinlik_bandi(d)
            cv2.putText(goster, f"KESKINLIK {d:7.1f} {bant}  (en iyi {en_iyi:.0f})", (15, 48),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.4, RENK.get(bant, (0, 200, 255)), 3)
            bant_roi = keskinlik_bandi(d_roi)
            cv2.putText(goster, f"ORTA KARE keskinlik {d_roi:7.1f} {bant_roi}  (en iyi {en_iyi_roi:.0f})",
                        (15, 92), cv2.FONT_HERSHEY_SIMPLEX, 1.0, RENK.get(bant_roi, (0, 200, 255)), 2)
            if mesafe is not None:
                mtxt = (f"MESAFE TAHMINI ~{mesafe:5.1f} m  (nesne {nesne_m:.1f} m = {kutu[2]} px"
                        f" · FOV {a.fov:.0f} BEYAN)")
            else:
                mtxt = f"MESAFE: orta karede nesne bulunamadi  (nesne {nesne_m:.1f} m)"
            cv2.putText(goster, mtxt, (15, 136), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 0), 2)
            cv2.putText(goster, f"orta kare {kenar}px kapsar: 10m={kapsam[10]:.2f}m 20m={kapsam[20]:.2f}m "
                        f"30m={kapsam[30]:.2f}m | 1px@30m={100 * 30 / fx:.1f}cm | +/- [ ] r s q",
                        (15, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("NAVITAS odak", goster)

            simdi = time.time()
            if simdi - son_satir >= 1.0:
                son_satir = simdi
                jsonl.write(json.dumps({
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "monotonic_s": round(time.monotonic(), 3),
                    "keskinlik": round(d, 1), "roi_keskinlik": round(d_roi, 1),
                    "roi_px": kenar, "nesne_kutu_px": list(kutu) if kutu else None,
                    "nesne_m_beyan": nesne_m, "fov_beyan": a.fov, "fx_px": round(fx, 1),
                    "mesafe_tahmini_m": round(mesafe, 2) if mesafe else None,
                    "kare_hw": [H, W]}) + "\n")
                jsonl.flush()
            tus = cv2.waitKey(1) & 0xFF
            kaydet = tus == ord("s") or simdi - son_jpg >= 15.0
            if kaydet:
                son_jpg = simdi
                cv2.imwrite(str(kayit / f"kare_{time.strftime('%H%M%S')}.jpg"), kare,
                            [cv2.IMWRITE_JPEG_QUALITY, 90])
            if tus in (ord("q"), 27):
                break
            if tus == ord("r"):
                en_iyi = en_iyi_roi = 0.0
            elif tus in (ord("+"), ord("=")):
                nesne_m = round(nesne_m + 0.1, 2)
            elif tus == ord("-"):
                nesne_m = max(0.1, round(nesne_m - 0.1, 2))
            elif tus == ord("]"):
                kare_oran = min(0.6, kare_oran + 0.02)
            elif tus == ord("["):
                kare_oran = max(0.04, kare_oran - 0.02)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        jsonl.close()
        cv2.destroyAllWindows()
    print(f"son en iyi keskinlik: {en_iyi:.1f} · orta kare: {en_iyi_roi:.1f} · kayit {kayit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
