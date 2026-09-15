#!/usr/bin/env python3
"""Satranc tahtasi ile kamera ic parametre kalibrasyonu (tezgah araci, uretim kodu degil).

Neden: FOV'u elle mesafe olcumuyle bulmak hataya acik. calibrateCamera odak uzunlugunu
piksel cinsinden verir; kare boyutu ve mesafe gerekmez (ic parametreler olcekten bagimsiz).
Bukulme katsayilari da cikar: genis acili lenste pinhole mpp formulunun kenar hatasini gosterir.

Kullanim:
  python kalibrasyon_satranc.py --sentetik            # boru hattini bilinen kamerayla sinar
  python kalibrasyon_satranc.py --url http://10.21.8.7:8080/kare.jpg --sure 120
Yalniz OpenCV + NumPy + standart kutuphane.
"""
import argparse
import json
import math
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

IC_KOSE = (9, 6)
BAYRAK = cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_FAST_CHECK
ALT_PIKSEL = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 40, 1e-3)


def nesne_noktalari():
    p = np.zeros((IC_KOSE[0] * IC_KOSE[1], 3), np.float32)
    p[:, :2] = np.mgrid[0:IC_KOSE[0], 0:IC_KOSE[1]].T.reshape(-1, 2)
    return p


def kose_bul(gri):
    ok, k = cv2.findChessboardCorners(gri, IC_KOSE, BAYRAK)
    if not ok:
        return None
    return cv2.cornerSubPix(gri, k, (11, 11), (-1, -1), ALT_PIKSEL)


def poz_imzasi(k, w, h):
    """Kaydedilen kareler birbirinin kopyasi olmasin: merkez, olcek, egim."""
    xy = k.reshape(-1, 2)
    merkez = xy.mean(0) / (w, h)
    olcek = np.linalg.norm(xy.max(0) - xy.min(0)) / math.hypot(w, h)
    ust = xy[IC_KOSE[0] - 1] - xy[0]
    sol = xy[-IC_KOSE[0]] - xy[0]
    egim = np.linalg.norm(ust) / max(np.linalg.norm(sol), 1e-6)
    return np.array([merkez[0], merkez[1], olcek, egim / 2.0])


def farkli_mi(imza, imzalar, esik=0.05):
    return all(np.abs(imza - o).max() > esik for o in imzalar)


def kalibre_et(koseler, w, h):
    obj = [nesne_noktalari()] * len(koseler)
    rms, K, D, rv, tv = cv2.calibrateCamera(obj, koseler, (w, h), None, None)
    hatalar = []
    for o, k, r, t in zip(obj, koseler, rv, tv):
        p, _ = cv2.projectPoints(o, r, t, K, D)
        hatalar.append(float(np.sqrt(((p - k) ** 2).sum(-1).mean())))
    fx, fy, cx, cy = K[0, 0], K[1, 1], K[0, 2], K[1, 2]
    return {
        "kare_sayisi": len(koseler), "goruntu": [w, h], "rms_px": round(float(rms), 4),
        "kare_hatalari_px": [round(e, 3) for e in hatalar],
        "fx": round(float(fx), 2), "fy": round(float(fy), 2), "cx": round(float(cx), 2), "cy": round(float(cy), 2),
        "bukulme_k1_k2_p1_p2_k3": [round(float(v), 5) for v in D.ravel()[:5]],
        "fov_yatay_derece_pinhole": round(math.degrees(2 * math.atan(w / (2 * fx))), 2),
        "fov_dikey_derece_pinhole": round(math.degrees(2 * math.atan(h / (2 * fy))), 2),
    }


def sentetik():
    """Bilinen kamera (fx=fy=1700, 1920x1080) ile tahtayi farkli pozlarda cizip geri bul."""
    w, h, f = 1920, 1080, 1700.0
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]], np.float64)
    kare_px = 80
    tahta = np.full(((IC_KOSE[1] + 1) * kare_px + 160, (IC_KOSE[0] + 1) * kare_px + 160), 255, np.uint8)
    for r in range(IC_KOSE[1] + 1):
        for c in range(IC_KOSE[0] + 1):
            if (r + c) % 2 == 0:
                tahta[80 + r * kare_px:80 + (r + 1) * kare_px, 80 + c * kare_px:80 + (c + 1) * kare_px] = 0
    rng = np.random.default_rng(7)
    koseler = []
    for _ in range(40):
        rvec = rng.uniform(-0.45, 0.45, 3) * np.array([1, 1, 0.3])
        tvec = np.array([rng.uniform(-3, 3), rng.uniform(-2, 2), rng.uniform(13, 22)])
        # tahta koseleri (birim kare=1) -> resim; tahta goruntusundeki ic kose (80+80, 80+80) px
        dunya = np.array([[-2, -2, 0], [IC_KOSE[0] + 1, -2, 0], [IC_KOSE[0] + 1, IC_KOSE[1] + 1, 0], [-2, IC_KOSE[1] + 1, 0]], np.float32)
        tahta_px = np.array([[0, 0], [tahta.shape[1], 0], [tahta.shape[1], tahta.shape[0]], [0, tahta.shape[0]]], np.float32)
        resim_px, _ = cv2.projectPoints(dunya - np.array([0, 0, 0], np.float32), rvec, tvec, K, None)
        H = cv2.getPerspectiveTransform(tahta_px, resim_px.reshape(-1, 2).astype(np.float32))
        im = cv2.warpPerspective(tahta, H, (w, h), borderValue=128)
        k = kose_bul(im)
        if k is not None:
            koseler.append(k)
    sonuc = kalibre_et(koseler, w, h)
    beklenen = math.degrees(2 * math.atan(w / (2 * f)))
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    hata = abs(sonuc["fx"] - f) / f * 100
    print(f"SENTETIK: beklenen fx={f} FOV_yatay={beklenen:.2f} | bulunan fx={sonuc['fx']} (%{hata:.2f}) | kare {sonuc['kare_sayisi']}/40")
    print("SENTETIK SONUC:", "GECTI" if hata < 1.0 and sonuc["kare_sayisi"] >= 15 else "DUSTU")


def canli(url, sure, aralik, en_az, cikti):
    cikti.mkdir(parents=True, exist_ok=True)
    koseler, imzalar, boyut = [], [], None
    bitis = time.time() + sure
    deneme = 0
    while time.time() < bitis:
        deneme += 1
        try:
            veri = urllib.request.urlopen(url, timeout=5).read()
        except Exception as e:  # ag kopmasi tezgahta beklenir; sayilip gecilir
            print(f"[{deneme}] kare alinamadi: {e}")
            time.sleep(aralik)
            continue
        im = cv2.imdecode(np.frombuffer(veri, np.uint8), cv2.IMREAD_COLOR)
        gri = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        h, w = gri.shape
        if boyut and boyut != (w, h):
            print(f"[{deneme}] kare boyutu degisti {boyut}->{(w, h)}; atlandi")
            continue
        k = kose_bul(gri)
        if k is None:
            print(f"[{deneme}] tahta yok")
        else:
            imza = poz_imzasi(k, w, h)
            if farkli_mi(imza, imzalar):
                boyut = (w, h)
                koseler.append(k)
                imzalar.append(imza)
                cv2.imwrite(str(cikti / f"kalib_{len(koseler):02d}.jpg"), im)
                print(f"[{deneme}] ALINDI #{len(koseler)} merkez=({imza[0]:.2f},{imza[1]:.2f}) olcek={imza[2]:.2f}")
            else:
                print(f"[{deneme}] tahta var ama poz oncekine cok benzer — acisini/yerini degistir")
        time.sleep(aralik)
    if len(koseler) < en_az:
        print(f"YETERSIZ: {len(koseler)} farkli poz (en az {en_az}). Kalibrasyon yapilmadi.")
        return 2
    sonuc = kalibre_et(koseler, *boyut)
    (cikti / "kalibrasyon.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(sonuc, ensure_ascii=False, indent=1))
    print("UYARI: rms > 1 px ise sonuc guvenilmez" if sonuc["rms_px"] > 1.0 else "rms kabul edilebilir (<= 1 px)")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--sentetik", action="store_true")
    a.add_argument("--url", default="http://10.21.8.7:8080/kare.jpg")
    a.add_argument("--sure", type=float, default=120)
    a.add_argument("--aralik", type=float, default=1.0)
    a.add_argument("--en-az", type=int, default=15)
    a.add_argument("--cikti", type=Path, default=Path(__file__).with_name("kalibrasyon_imx477"))
    g = a.parse_args()
    raise SystemExit(sentetik() if g.sentetik else canli(g.url, g.sure, g.aralik, g.en_az, g.cikti))
