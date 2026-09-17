# -*- coding: utf-8 -*-
"""
NAVITAS — 17 Eylül 2026 02:53 düşüşü: Pixhawk logundan canlandırma videosu (2. sürüm, denetim düzeltmeli).

Yorumlayıcı: O:\\navitas-local-train\\venv\\Scripts\\python.exe

Kullanım:
  log_video.py                 video (dusus_0253.mp4) + örnek kareler + işaret testleri
                               + mp4'ten kare doğrulaması + yerleşim denetimi + OKUBENI.md
  log_video.py --test-isaret   yalnız 3 işaret test karesi (kareler/test_*.png)

Kural: çizilen ve yazılan TÜM log verisi bu betikte .bin logundan (telemetri son
paketi MP tlog'undan) okunur. Elle yazılmış sayı yalnız şunlardır: video düzeni
(süreler, eksenler, piksel yerleşimi), 3B çizimin temsili ölçüleri, görev tanımının
motor eşlemesi (SERVOx_FUNCTION ile doğrulanır), değerlendirme metinleri (paylar,
eşikler) ve OKUBENI karşılaştırması için rapor değerleri (REFERANS; çizimde kullanılmaz).
"""
import argparse
import datetime
import math
import multiprocessing as mp
import os
import subprocess
import sys
import time
import json

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from pymavlink import mavutil

# ----------------------------------------------------------------------------
# Yollar
# ----------------------------------------------------------------------------
KLASOR = os.path.dirname(os.path.abspath(__file__))
KARELER = os.path.join(KLASOR, "kareler")
BIN = r"O:\navitas\results\ucus_20260917b\2026-09-17 02-50-38.bin"
TLOG = r"C:\Users\yunus\OneDrive\Belgeler\Mission Planner\logs\2026-09-17 02-31-36.tlog"
FFMPEG = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\ffmpeg\bin\ffprobe.exe"
FONT_R = r"C:\Windows\Fonts\DejaVuSans.ttf"
FONT_B = r"C:\Windows\Fonts\DejaVuSans-Bold.ttf"
MP4 = os.path.join(KLASOR, "dusus_0253.mp4")
OKUBENI = os.path.join(KLASOR, "OKUBENI.md")

# ----------------------------------------------------------------------------
# Video düzeni (tasarım sabitleri — log verisi değil)
# ----------------------------------------------------------------------------
W, H, FPS = 1920, 1080, 30
BASLIK_S, OZET_S, SONUC_S = 3.0, 6.0, 7.0
CANLI = (186.0, 202.2)
AGIR = (202.2, 203.4)
AGIR_HIZ = 0.1
SONRA = (203.4, 206.6)
EKSEN_TAM = (186.0, 207.0)
EKSEN_YAKIN = (202.0, 203.4)
ZAMAN_COZ = 0.0005  # örnekle-tut ve olay erişimi: HUD'daki 1 ms çözünürlüğe yuvarlanmış zaman (t + 0,5 ms)
ORNEK_T = [186.5, 190.0, 195.0, 200.2, 202.30, 202.43, 202.52, 202.62, 202.77, 202.97, 204.5]

# Görev tanımındaki KESİN motor eşlemesi (SERVOx_FUNCTION ile doğrulanır)
MOTOR_KANAL = {1: "C11", 2: "C10", 3: "C12", 4: "C9"}
MOTOR_YER = {1: ("ön-sağ", "CCW"), 2: ("arka-sol", "CCW"), 3: ("ön-sol", "CW"), 4: ("arka-sağ", "CW")}
MOTOR_ISARET = {1: (1, 1), 2: (-1, -1), 3: (1, -1), 4: (-1, 1)}  # FRD (x ileri, y sağ)
MOD_AD = {0: "Stabilize", 5: "Loiter", 9: "Land"}
GPS_DURUM = {0: "GPS yok", 1: "fix yok", 2: "2B fix", 3: "3B fix", 4: "3B DGPS", 5: "RTK float", 6: "RTK fixed"}
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
G0 = 9.80665
GPS_UTC_ARTIK_SANIYE = 18  # GPS−UTC (2017'den beri)

# DUSUS_ANALIZI.md / görev tanımındaki değerler — YALNIZ OKUBENI karşılaştırması; çizimde KULLANILMAZ
REFERANS = {
    "W1 başlangıç": 49.6, "W1 bitiş": 61.5, "W2 başlangıç": 66.0, "W2 bitiş": 80.2, "W2 sert iniş": 79.45,
    "W5 başlangıç": 134.2, "W5 bitiş": 150.7, "W6 başlangıç": 181.7, "W6 bitiş": 204.0,
    "kalkis": 188.3, "basamak1": 189.5, "basamak2": 194.4, "sag": 199.8, "telemetri": 202.18,
    "baslangic": 202.41, "pervane": 202.45, "pervane_bitis": 202.49, "kopma": 202.47, "kopma_bitis": 202.57,
    "ters": 202.77, "carpma": 202.97, "disarm": 203.97,
}

# Renkler (RGB)
ZEMIN = (11, 14, 20)
PANEL = (20, 25, 34)
CERCEVE = (46, 54, 70)
IZGARA = (40, 47, 60)
YAZI = (236, 239, 244)
SOLUK = (156, 165, 181)
KIRMIZI = (255, 86, 86)
SARI = (255, 204, 64)
YESIL = (96, 214, 124)
MAVI = (90, 160, 255)
TURUNCU = (255, 160, 64)
NOTR = (214, 219, 228)  # yaw hatası: motor paletinde olmayan nötr renk
MOTOR_RENK = {1: (255, 95, 200), 2: (120, 225, 110), 3: (176, 140, 255), 4: (60, 210, 230)}
PWM_MAVI, PWM_SARI, PWM_KIRMIZI = np.array((40, 110, 255.)), np.array((255, 215, 40.)), np.array((255, 40, 40.))

# Ekran bölgeleri (x0, y0, x1, y1)
UST_H = 60
R3 = (16, 68, 920, 760)
RUST = (936, 68, 1904, 244)
RORTA = (936, 252, 1904, 600)
RALT = (936, 608, 1904, 760)
SERIT = (16, 768, 1904, 1072)
R3_ALT_REZERV = 88  # 3B panelin altındaki dipnot bandı (etiketler buraya girmez)
# sağ üst
MB_X0, MB_X1 = 1136, 1346  # motor çubuğu 1000..2000 µs
MB_Y = [114, 142, 170, 198]
GX_T, GX0, GX1 = 1428, 1436, 1888
# sağ orta (grafikler)
PX0, PX1 = 1014, 1856
PLOT_Y = {"motor": (282, 338), "fark": (366, 408), "vibe": (436, 474), "amag": (502, 568)}
PLOT_ARA = {"motor": (1000, 2000), "fark": (-300, 700), "vibe": (0, 100), "amag": (0, 60)}
X_ETIKET_Y = 573
# sağ alt (HUD)
HUD_Y = [627, 655, 683, 711, 739]
HUD_A_ETIKET, HUD_A_DEGER = 952, 1072
HUD_B_ETIKET, HUD_B_DEGER = 1298, 1410
CUBUK_KUTU = [(1668, "Sol: gaz/yaw"), (1788, "Sağ: pitch/roll")]
CUBUK_Y0, CUBUK_Y1 = 634, 700
# şerit
TX0, TX1 = 80, 1840
SATIR_Y = [774, 797, 820, 843]
EKSEN_Y = 882
# yazı boyu alt sınırları
MIN_VERI_BOY, MIN_YARDIMCI_BOY = 18, 16


# ----------------------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------------------
def tr(x, nd=1, isaret=False):
    """Türkçe sayı: ondalık virgül, gerçek eksi işareti."""
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    x = round(float(x), nd) + 0.0  # −0 yazılmasın
    if x == 0:
        x = 0.0
    s = f"{x:+.{nd}f}" if isaret else f"{x:.{nd}f}"
    return s.replace("-", "−").replace(".", ",")


def son_i(tarr, t):
    return int(np.searchsorted(tarr, t, side="right")) - 1


def orta1s(t, x, pencere=1.0):
    """Her örnek için son N örneğin ortalaması; N = pencere / medyan örnek aralığı (10 Hz'de 10 örnek = 1 s)."""
    N = max(int(round(pencere / float(np.median(np.diff(t))))), 1)
    cs = np.concatenate([[0.0], np.cumsum(x)])
    i = np.arange(len(t)) + 1
    j = np.maximum(i - N, 0)
    return (cs[i] - cs[j]) / (i - j)


def seg_kutu(p0, p1, b):
    """Doğru parçası (p0-p1) ile eksen hizalı kutu kesişiyor mu (Liang–Barsky)."""
    if b[2] <= b[0] or b[3] <= b[1]:
        return False
    x0, y0 = p0
    dx, dy = p1[0] - x0, p1[1] - y0
    u0, u1 = 0.0, 1.0
    for p, q in ((-dx, x0 - b[0]), (dx, b[2] - x0), (-dy, y0 - b[1]), (dy, b[3] - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return False
        else:
            r = q / p
            if p < 0:
                if r > u1:
                    return False
                u0 = max(u0, r)
            else:
                if r < u0:
                    return False
                u1 = min(u1, r)
    return u0 <= u1


def genislet(b, p):
    return (b[0] - p, b[1] - p, b[2] + p, b[3] + p)


def kutu_kes(a, b, pad=0.0):
    return a[0] < b[2] + pad and a[2] > b[0] - pad and a[1] < b[3] + pad and a[3] > b[1] - pad


S8 = 8


def _p(pts):
    return np.round(np.asarray(pts, float) * S8).astype(np.int32)


def dolu(img, pts, renk):
    cv2.fillPoly(img, [_p(pts)], renk, cv2.LINE_AA, 3)


def cizgi(img, pts, renk, k=1, kapali=False):
    cv2.polylines(img, [_p(pts)], kapali, renk, k, cv2.LINE_AA, 3)


def kesikli(img, p0, p1, renk, k=1, parca=8, bosluk=6):
    p0, p1 = np.array(p0, float), np.array(p1, float)
    L = np.linalg.norm(p1 - p0)
    if L < 1:
        return
    u = (p1 - p0) / L
    s = 0.0
    while s < L:
        e = min(s + parca, L)
        cizgi(img, [p0 + u * s, p0 + u * e], renk, k)
        s = e + bosluk


def alfa_dolu(img, pts, renk, alfa):
    pts = np.asarray(pts, float)
    x0 = max(int(pts[:, 0].min()) - 2, 0)
    y0 = max(int(pts[:, 1].min()) - 2, 0)
    x1 = min(int(pts[:, 0].max()) + 3, img.shape[1])
    y1 = min(int(pts[:, 1].max()) + 3, img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    roi = img[y0:y1, x0:x1]
    ust = roi.copy()
    cv2.fillPoly(ust, [_p(pts - [x0, y0])], renk, cv2.LINE_AA, 3)
    roi[:] = cv2.addWeighted(ust, alfa, roi, 1 - alfa, 0)


def alfa_kutu(img, x0, y0, x1, y1, renk, alfa):
    x0, y0 = max(int(x0), 0), max(int(y0), 0)
    x1, y1 = min(int(x1), img.shape[1]), min(int(y1), img.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    roi = img[y0:y1, x0:x1]
    roi[:] = (roi * (1 - alfa) + np.array(renk, float) * alfa).astype(np.uint8)


def rot(roll, pitch, yaw):
    """ArduPilot 321 Euler: gövde FRD → (kuzey/ileri, doğu/sağ, aşağı)."""
    r, p, y = math.radians(roll), math.radians(pitch), math.radians(yaw)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Ry = np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
    Rx = np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])
    return Rz @ Ry @ Rx


class Kamera:
    """Ekran dünyası: x = sağ (referans yönün sağı), y = ileri (referans yön), z = yukarı."""

    def __init__(self, hedef, az, el, mesafe, odak, merkez):
        T = np.array(hedef, float)
        a, e = math.radians(az), math.radians(el)
        yon = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])
        self.C = T + mesafe * yon
        k = T - self.C
        k /= np.linalg.norm(k)
        i = np.cross(k, [0, 0, 1.0])
        i /= np.linalg.norm(i)
        j = np.cross(k, i)
        self.M = np.stack([i, j, k])
        self.f = odak
        self.cx, self.cy = merkez

    def izdus(self, P):
        q = (np.asarray(P, float) - self.C) @ self.M.T
        z = np.maximum(q[..., 2], 1e-3)
        return np.stack([self.cx + self.f * q[..., 0] / z, self.cy + self.f * q[..., 1] / z], -1), q[..., 2]


# ----------------------------------------------------------------------------
# Veri okuma
# ----------------------------------------------------------------------------
def veri_oku():
    tipler = ["ATT", "RCOU", "RCIN", "CTUN", "BAT", "VIBE", "IMU", "GPS", "MAG", "MODE", "EV", "ERR", "ARM", "PARM", "MSG"]
    m = mavutil.mavlink_connection(BIN)
    ham = {k: [] for k in tipler}
    while True:
        x = m.recv_match(type=tipler)
        if x is None:
            break
        ham[x.get_type()].append(x.to_dict())

    def t_(L):
        return np.array([x["TimeUS"] for x in L], float) / 1e6

    def a_(L, k):
        return np.array([x[k] for x in L], float)

    V = {}
    P = {}
    for x in ham["PARM"]:
        P[x["Name"]] = x["Value"]
    V["P"] = P
    V["msg"] = [(x["TimeUS"] / 1e6, x["Message"]) for x in ham["MSG"]]
    V["sayim"] = {k: len(v) for k, v in ham.items()}

    for k, ch in MOTOR_KANAL.items():
        fn = int(P[f"SERVO{ch[1:]}_FUNCTION"])
        if fn != 32 + k:
            raise SystemExit(f"Motor eşlemesi logla uyuşmuyor: {ch} SERVO_FUNCTION={fn}, beklenen Motor{k}")

    L = ham["ATT"]
    V["att_t"] = t_(L)
    for k in ("Roll", "Pitch", "Yaw", "DesRoll", "DesPitch", "DesYaw"):
        V["att_" + k] = a_(L, k)
    for k in ("Roll", "Pitch", "Yaw"):
        V["att_u" + k] = np.unwrap(V["att_" + k], period=360.0)
    V["att_yawhata"] = (V["att_DesYaw"] - V["att_Yaw"] + 180.0) % 360.0 - 180.0

    L = ham["RCOU"]
    V["rcou_t"] = t_(L)
    for k, ch in MOTOR_KANAL.items():
        V[f"M{k}"] = a_(L, ch)
    V["fark"] = (V["M1"] + V["M2"]) - (V["M3"] + V["M4"])
    V["fark1s"] = orta1s(V["rcou_t"], V["fark"])

    L = ham["RCIN"]
    V["rcin_t"] = t_(L)
    for i in range(1, 7):
        V[f"C{i}"] = a_(L, f"C{i}")

    L = ham["CTUN"]
    V["ctun_t"] = t_(L)
    V["alt"] = a_(L, "Alt")
    V["tho"] = a_(L, "ThO")
    V["dcrt"] = a_(L, "DCRt")

    L = ham["BAT"]
    V["bat_t"] = t_(L)
    V["volt"] = a_(L, "Volt")
    V["akim"] = a_(L, "Curr")

    for I in (0, 1):
        L = [x for x in ham["VIBE"] if x["IMU"] == I]
        V[f"vibe{I}_t"] = t_(L)
        for k in ("VibeX", "VibeY", "VibeZ", "Clip"):
            V[f"vibe{I}_{k}"] = a_(L, k)

    L = [x for x in ham["IMU"] if x["I"] == 0]
    V["imu_t"] = t_(L)
    ax, ay, az = a_(L, "AccX"), a_(L, "AccY"), a_(L, "AccZ")
    V["amag"] = np.sqrt(ax * ax + ay * ay + az * az)
    for k in ("GyrX", "GyrY", "GyrZ"):
        V[k] = np.degrees(a_(L, k))

    L = ham["GPS"]
    V["gps_t"] = t_(L)
    for k in ("Status", "NSats", "GWk", "GMS"):
        V["gps_" + k] = a_(L, k)

    L = [x for x in ham["MAG"] if x["I"] == 0]
    V["mag_t"] = t_(L)
    V["mag_S"] = a_(L, "S") / 1e6

    V["mode"] = [(x["TimeUS"] / 1e6, int(x["Mode"])) for x in ham["MODE"]]
    V["ev"] = [(x["TimeUS"] / 1e6, int(x["Id"])) for x in ham["EV"]]
    V["err"] = [(x["TimeUS"] / 1e6, int(x["Subsys"]), int(x["ECode"])) for x in ham["ERR"]]
    V["arm"] = [(x["TimeUS"] / 1e6, int(x["ArmState"]), int(x["Method"])) for x in ham["ARM"]]

    # GPS saati → UTC; açılış anının UTC'si
    gps_epoch = datetime.datetime(1980, 1, 6, tzinfo=datetime.timezone.utc).timestamp()
    g = (V["gps_Status"] >= 3) & (V["gps_GWk"] > 0)
    utc = gps_epoch + V["gps_GWk"] * 604800 + V["gps_GMS"] / 1000.0 - GPS_UTC_ARTIK_SANIYE
    V["boot_utc"] = float(np.median(utc[g] - V["gps_t"][g]))
    V["fw"] = next((s for _, s in V["msg"] if s.startswith("ArduCopter")), "?")
    V["kart"] = next((s.split()[0] for _, s in V["msg"] if s.startswith("Pixhawk")), "?")
    return V


def tlog_oku(V):
    """Araçtan (SYSID_THISMAV) gelen, time_boot_ms taşıyan son paket; yalnız bu .bin açılışına ait paketler."""
    sysid = int(V["P"]["SYSID_THISMAV"])
    m = mavutil.mavlink_connection(TLOG, dialect="ardupilotmega")
    ilk_pc = None
    son = None
    n_eslesen = 0
    diger_acilis = set()
    att_tb = []
    while True:
        x = m.recv_match()
        if x is None:
            break
        pc = getattr(x, "_timestamp", None)
        if ilk_pc is None and pc:
            ilk_pc = pc
        if x.get_type() == "BAD_DATA" or x.get_srcSystem() != sysid:
            continue
        tb = getattr(x, "time_boot_ms", None)
        if tb is None:
            continue
        be = pc - tb / 1000.0
        if abs(be - V["boot_utc"]) < 30.0:
            n_eslesen += 1
            son = {"tb": tb / 1000.0, "tip": x.get_type(), "pc": pc}
            if x.get_type() == "ATTITUDE":
                att_tb.append(tb / 1000.0)
        else:
            diger_acilis.add(round(be / 60.0))
    # Saat dilimi: tlog dosya adındaki yerel saat ile ilk paketin UTC zaman damgası
    ad = os.path.splitext(os.path.basename(TLOG))[0]
    yerel = datetime.datetime.strptime(ad, "%Y-%m-%d %H-%M-%S")
    utc = datetime.datetime.fromtimestamp(ilk_pc, datetime.timezone.utc).replace(tzinfo=None)
    tz = round((yerel - utc).total_seconds() / 900.0) * 900
    V["tz_s"] = tz
    V["tlog"] = {"son_tb": son["tb"], "son_tip": son["tip"], "son_pc": son["pc"], "n": n_eslesen,
                 "diger_acilis_sayisi": len(diger_acilis), "tz_s": tz,
                 "att_periyot": float(np.median(np.diff(att_tb))), "att_son": att_tb[-1]}
    return V


def yerel_saat(V, epoch, nd=2):
    e = epoch + V["tz_s"]
    d = datetime.datetime.fromtimestamp(math.floor(e), datetime.timezone.utc)
    frac = int((e - math.floor(e)) * 10 ** nd)
    return d.strftime("%H:%M:%S") + ("," + str(frac).zfill(nd) if nd else "")


def log_saat(V, t, nd=2):
    return yerel_saat(V, V["boot_utc"] + t, nd)


# ----------------------------------------------------------------------------
# Olaylar (hepsi logdan)
# ----------------------------------------------------------------------------
def olaylari_hesapla(V):
    P = V["P"]
    E = {}
    # --- arm pencereleri
    pen = []
    acik = None
    for t, st, yontem in V["arm"]:
        if st == 1:
            acik = t
        else:
            if acik is None:
                at = V["att_t"][V["att_t"] < t]
                bosluk = np.where(np.diff(at) > 2.0)[0]
                bas = float(at[bosluk[-1] + 1]) if len(bosluk) else float(at[0])
                pen.append({"bas": bas, "son": t, "bas_kaynak": "log bloğu başı (ARM kaydı yok)"})
            else:
                pen.append({"bas": acik, "son": t, "bas_kaynak": "ARM"})
                acik = None
    E["pencereler"] = pen
    w6 = pen[-1]
    w6b, w6s = w6["bas"], w6["son"]
    ev = V["ev"]
    E["kalkis"] = kalkis = next(t for t, i in ev if i == 28 and w6b < t < w6s)
    E["ref_a"], E["ref_b"] = kalkis - 2.0, kalkis - 0.05
    ct = V["ctun_t"]
    wref = (ct >= E["ref_a"] - 1e-6) & (ct <= E["ref_b"] + 1e-6)
    E["zemin"] = float(V["alt"][wref].mean())
    E["zemin_n"] = int(wref.sum())
    V["agl"] = V["alt"] - E["zemin"]
    at = V["att_t"]
    wy = (at >= E["ref_a"] - 1e-6) & (at <= E["ref_b"] + 1e-6)
    E["yaw_ref"] = float(V["att_uYaw"][wy].mean())

    # --- başlangıç: kalkıştan sonra ilk |GyrX| ya da |GyrY| > 100 °/s (IMU0)
    it = V["imu_t"]
    gxy = np.maximum(np.abs(V["GyrX"]), np.abs(V["GyrY"]))
    ib = int(np.where((it > kalkis) & (it < w6s) & (gxy > 100.0))[0][0])
    E["baslangic"] = bas = float(it[ib])
    E["bas_once_gyro_max"] = float(gxy[(it > kalkis) & (it < bas)].max())
    E["bas_a_once"], E["bas_a"] = float(V["amag"][ib - 1]), float(V["amag"][ib])
    E["bas_gx"], E["bas_gy"] = float(V["GyrX"][ib]), float(V["GyrY"][ib])
    E["bas_dgz"] = float(V["GyrZ"][ib] - V["GyrZ"][ib - 1])
    ia = son_i(at, bas - 1e-6)
    E["son_normal"] = float(at[ia])
    E["son_normal_roll"], E["son_normal_pitch"] = float(V["att_Roll"][ia]), float(V["att_Pitch"][ia])
    ic = son_i(ct, bas - 1e-6)
    E["hover_agl_son"] = float(V["agl"][ic])
    wh = (ct >= kalkis + 3.0) & (ct < bas)
    E["hover_agl_medyan"] = float(np.median(V["agl"][wh]))
    E["agl_kalkis3"] = float(V["agl"][son_i(ct, kalkis + 3.0)])

    # --- ters: ilk |Roll| > 90°
    i = int(np.where((at > bas) & (np.abs(V["att_Roll"]) > 90.0))[0][0])
    E["ters"], E["ters_roll"], E["ters_pitch"] = float(at[i]), float(V["att_Roll"][i]), float(V["att_Pitch"][i])

    # --- pervane darbesi: ilk |a| > 2 g → başlangıç ile ters arası |a| tepesi
    am = V["amag"]
    j = int(np.where((it > bas) & (am > 2 * G0))[0][0])
    w = np.where((it > bas) & (it < E["ters"]))[0]
    k = int(w[np.argmax(am[w])])
    E["pervane"], E["pervane_a1"] = float(it[j]), float(am[j])
    E["pervane_bitis"], E["pervane_a2"] = float(it[k]), float(am[k])
    for I in (0, 1):
        vt, vc = V[f"vibe{I}_t"], V[f"vibe{I}_Clip"]
        E[f"clip{I}_once"] = float(vc[son_i(vt, bas)])
        E[f"clip{I}_sonra"] = float(vc[int(np.searchsorted(vt, E["pervane"]))])
    vt0 = V["vibe0_t"]
    wv = (vt0 > bas) & (vt0 < E["ters"])
    E["vibe_max_xyz"] = float(max(V["vibe0_VibeX"][wv].max(), V["vibe0_VibeY"][wv].max(), V["vibe0_VibeZ"][wv].max()))

    # --- çarpma: ters ile disarm arası IMU0 |a| tepesi
    w = np.where((it >= E["ters"]) & (it <= w6s))[0]
    k = int(w[np.argmax(am[w])])
    E["carpma"], E["carpma_a"] = float(it[k]), float(am[k])
    E["clip0_carpma"] = float(V["vibe0_Clip"][int(np.searchsorted(vt0, E["carpma"] - 1e-3))])
    E["clip0_ters"] = float(V["vibe0_Clip"][son_i(vt0, E["ters"])])
    E["err_pusula"] = next(((t, s, c) for t, s, c in V["err"] if s == 3 and bas <= t <= w6s), None)

    # --- harici pusula (MAG I=0): S (son güncelleme) donması
    mt, S = V["mag_t"], V["mag_S"]
    idx = [q for q in np.where((mt > kalkis) & (mt <= w6s))[0] if S[q] == S[q - 1]]
    E["kopma_bitis"] = float(mt[idx[0]])
    E["kopma"] = float(S[idx[0]])
    # --- GPS
    gt = V["gps_t"]
    wg = np.where((gt > kalkis) & (gt <= E["carpma"]))[0]
    E["gps_son"] = float(gt[wg[-1]])
    dts = np.diff(gt[wg])
    E["gps_periyot"] = float(np.median(dts))
    E["gps_max_dt"] = float(dts.max())
    E["gps_son_ns"], E["gps_son_st"] = int(V["gps_NSats"][wg[-1]]), int(V["gps_Status"][wg[-1]])
    q = wg[-1] + 1
    E["gps0"], E["gps0_st"], E["gps0_ns"] = float(gt[q]), int(V["gps_Status"][q]), int(V["gps_NSats"][q])

    # --- disarm ve anahtarlar
    E["disarm"] = w6s
    rt = V["rcin_t"]
    orta6 = (P["RC6_MIN"] + P["RC6_MAX"]) / 2.0
    i6 = int(np.where((rt > E["carpma"]) & (V["C6"] < orta6))[0][0])
    E["c6_dusuk"] = float(rt[i6])
    E["c6_once"], E["c6_sonra"] = float(V["C6"][i6 - 1]), float(V["C6"][i6])
    c5b = V["C5"][son_i(rt, bas)]
    i5 = int(np.where((rt > bas) & (np.abs(V["C5"] - c5b) > 200))[0][0])
    E["c5_degisim"] = float(rt[i5])
    E["land_mod"] = next(t for t, mo in V["mode"] if mo == 9 and bas < t <= w6s)

    # --- roll/pitch/yaw çubukları ortada: kalkıştan sonra C1/C2/C4 ilk ölü bölge dışı (gaz AYRI hesaplanır)
    dis = np.zeros(len(rt), bool)
    for c in (1, 2, 4):
        dis |= np.abs(V[f"C{c}"] - P[f"RC{c}_TRIM"]) > P[f"RC{c}_DZ"]
    E["cubuk_cikis"] = float(rt[np.where((rt > kalkis) & dis)[0][0]])

    # --- gaz çubuğu: ArduCopter Loiter/AltHold ölü bandı
    #     get_pilot_desired_climb_rate(): bant = get_throttle_mid() ± THR_DZ (0..1000 ölçeğinde)
    #     RC_Channel::pwm_to_range_dz(): control_in = 1000·(pwm − (RC3_MIN+RC3_DZ)) / (RC3_MAX − (RC3_MIN+RC3_DZ)), tamsayı
    #     RC_Channel::get_control_mid(): r_in = (RC3_MIN+RC3_MAX)/2 aynı dönüşümle
    trim_low = P["RC3_MIN"] + P["RC3_DZ"]
    aralik = P["RC3_MAX"] - trim_low

    def gaz_cin(pwm):
        pwm = np.clip(np.asarray(pwm, float), P["RC3_MIN"], P["RC3_MAX"])
        return np.where(pwm > trim_low, np.floor(1000.0 * (pwm - trim_low) / aralik), 0.0)

    orta = math.floor(1000.0 * (math.floor((P["RC3_MIN"] + P["RC3_MAX"]) / 2) - trim_low) / aralik)
    dz = min(max(P["THR_DZ"], 0), 400)
    E["gaz_orta"], E["gaz_dz"] = int(orta), int(dz)
    pwm_s = np.arange(int(P["RC3_MIN"]), int(P["RC3_MAX"]) + 1)
    E["gaz_ust_pwm"] = int(pwm_s[gaz_cin(pwm_s) > orta + dz][0])
    E["gaz_alt_pwm"] = int(pwm_s[gaz_cin(pwm_s) >= orta - dz][0])
    cin = gaz_cin(V["C3"])
    durum = np.where(cin > orta + dz, 1, np.where(cin < orta - dz, -1, 0))
    dcrt = V["dcrt"]

    def diziler(maske):
        idx_ = np.where(maske & (rt >= w6b) & (rt <= bas))[0]
        out = []
        if len(idx_):
            a0 = p0 = idx_[0]
            for q_ in idx_[1:]:
                if q_ != p0 + 1:
                    out.append((a0, p0))
                    a0 = q_
                p0 = q_
            out.append((a0, p0))
        return [(i_, j_) for i_, j_ in out if rt[j_] >= kalkis]

    E["gaz_ust"] = []
    for i_, j_ in diziler(durum == 1):
        wc = (ct >= rt[i_]) & (ct <= rt[j_] + 0.1)
        E["gaz_ust"].append(dict(bas=float(rt[i_]), son=float(rt[j_]), c3_max=float(V["C3"][i_:j_ + 1].max()),
                                 dcrt_max=float(dcrt[wc].max()) if wc.any() else float("nan")))
    E["gaz_alt"] = [dict(bas=float(rt[i_]), son=float(rt[j_]), c3_min=float(V["C3"][i_:j_ + 1].min()))
                    for i_, j_ in diziler(durum == -1)]
    wd = (ct > kalkis) & (ct < bas)
    E["dcrt_max_ucus"] = float(dcrt[wd].max())

    # --- sağ düzeltme: kalkış–başlangıç arası en büyük C1'i içeren, C1 > TRIM+DZ bitişik dizi
    c1 = V["C1"]
    wi = np.where((rt > kalkis) & (rt < bas))[0]
    imax = int(wi[np.argmax(c1[wi])])
    esik = P["RC1_TRIM"] + P["RC1_DZ"]
    a_, b_ = imax, imax
    while c1[a_ - 1] > esik:
        a_ -= 1
    while c1[b_ + 1] > esik:
        b_ += 1
    E["sag"], E["sag_son"], E["sag_c1"] = float(rt[a_]), float(rt[b_]), float(c1[imax])
    wr = np.where((at >= E["sag"]) & (at <= E["sag_son"] + 0.5))[0]
    kr = int(wr[np.argmax(V["att_Roll"][wr])])
    E["sag_roll"], E["sag_roll_t"] = float(V["att_Roll"][kr]), float(at[kr])

    # --- basamaklar: CCW−CW adım istatistiği (1 s sonrası ort. − 1 s öncesi ort.), en büyük 2 tepe (≥ 2 s arayla)
    rct, fk = V["rcou_t"], V["fark"]
    N = int(round(1.0 / float(np.median(np.diff(rct[(rct > kalkis) & (rct < bas)])))))
    s = np.full(len(rct), np.nan)
    for i in np.where((rct >= kalkis + 1.0) & (rct <= E["cubuk_cikis"] - 1.0))[0]:
        s[i] = fk[i:i + N].mean() - fk[i - N:i].mean()
    secilen = []
    for i in np.argsort(-np.nan_to_num(s, nan=-1e9)):
        if np.isnan(s[i]):
            break
        if all(abs(rct[i] - rct[j]) >= 2.0 for j in secilen):
            secilen.append(int(i))
        if len(secilen) == 2:
            break
    secilen.sort()
    for n, i in enumerate(secilen, 1):
        E[f"basamak{n}"] = float(rct[i])
        E[f"basamak{n}_once"] = float(fk[i - N:i].mean())
        E[f"basamak{n}_sonra"] = float(fk[i:i + N].mean())
        E[f"basamak{n}_gaz"] = int(durum[son_i(rt, rct[i])])
        E[f"basamak{n}_dcrt"] = float(dcrt[son_i(ct, rct[i])])
    E["fark_ilk1s"] = float(fk[(rct >= kalkis) & (rct < kalkis + 1.0)].mean())
    isn = son_i(rct, bas - 1e-6)
    E["fark_son1s"], E["fark_son_t"] = float(V["fark1s"][isn]), float(rct[isn])
    E["fark_son_anlik"] = float(fk[isn])
    E["m4_son"] = float(V["M4"][isn])

    # --- telemetri: son paket ve kesilmenin belli olduğu an (sıradaki beklenen ATTITUDE)
    tl = V["tlog"]
    E["telemetri"] = tl["son_tb"]
    E["telemetri_kesik"] = max(tl["att_son"] + tl["att_periyot"], tl["son_tb"])

    # --- pencere ayrıntıları (özet kartı)
    for n, p in enumerate(pen, 1):
        a, b = p["bas"], p["son"]
        wa = (at >= a) & (at <= b)
        k = int(np.argmax(np.abs(V["att_Roll"][wa])))
        p["roll_max"], p["roll_max_t"] = float(V["att_Roll"][wa][k]), float(at[wa][k])
        wi2 = np.where((it >= a) & (it <= b))[0]
        k = int(wi2[np.argmax(am[wi2])])
        p["a_max"], p["a_max_t"] = float(am[k]), float(it[k])
        p["kalkis"] = [t for t, i in ev if i == 28 and a <= t <= b]
        p["modlar"] = [(t, mo) for t, mo in V["mode"] if a - 0.05 <= t <= b]
        wv0 = (vt0 >= a) & (vt0 <= b)
        p["clip_ilk"], p["clip_son"] = float(V["vibe0_Clip"][wv0][0]), float(V["vibe0_Clip"][wv0][-1])
        p["clip_once_amax"] = float(V["vibe0_Clip"][son_i(vt0, p["a_max_t"] - 1e-3)])
        p["clip_sonra_amax"] = float(V["vibe0_Clip"][int(np.searchsorted(vt0, p["a_max_t"] - 1e-3))])
        if p["kalkis"]:
            land = [t for t, mo in p["modlar"] if mo == 9]
            son_ = land[0] if land else b
            wv1 = (vt0 >= p["kalkis"][0] + 1.0) & (vt0 <= son_)
            p["vibez_ort"] = float(V["vibe0_VibeZ"][wv1].mean()) if wv1.any() else float("nan")
            p["land"] = land[0] if land else None
    return E


def gaz_metni(E):
    t2 = lambda x: tr(x, 2)
    p = []
    for g in E["gaz_ust"]:
        p.append(f"gaz {t2(g['bas'])}–{t2(g['son'])} s ölü bandın üstünde (C3 en çok {g['c3_max']:.0f} µs, bant üstü ≥{E['gaz_ust_pwm']} µs; "
                 f"istenen tırmanma DCRt en çok {tr(g['dcrt_max'], 0, True)} cm/s)")
    for g in E["gaz_alt"]:
        p.append(f"gaz {t2(g['bas'])}–{t2(g['son'])} s ölü bandın altında (C3 en az {g['c3_min']:.0f} µs)")
    return " · ".join(p) if p else "gaz ölü bantta"


def olay_listesi(V, E):
    """Açıklama şeridi ve zaman çizgisi olayları; metindeki tüm sayılar E'den.
    Başlık kuralı: ölçülen olgu önce, yorum sonra; yorum '(çıkarım)' / '(çıkarım + beyan)' etiketi taşır."""
    t2 = lambda x: tr(x, 2)
    tl = V["tlog"]
    w6b = E["pencereler"][-1]["bas"]
    mod6 = [mo for t, mo in V["mode"] if t <= w6b + 0.05][-1]
    gaz_durum_ad = {1: "ölü bandın üstünde (yavaş tırmanış isteği)", 0: "ölü bantta", -1: "ölü bandın altında"}
    kesik_sira = "sonra" if E["telemetri_kesik"] > E["baslangic"] else "önce"
    O = [
        dict(k="hazirlik", t=w6b, renk=SOLUK, kisa=None,
             baslik=f"Son uçuş (W6): arm {t2(w6b)} s, mod {MOD_AD.get(mod6, mod6)} — kalkış bekleniyor",
             detay=f"Yer referansı: CTUN Alt ortalaması {t2(E['ref_a'])}–{t2(E['ref_b'])} s = {t2(E['zemin'])} m "
                   f"({E['zemin_n']} örnek); yükseklik bu değere göre"),
        dict(k="kalkis", t=E["kalkis"], renk=SARI, kisa="Kalkış",
             baslik=f"Kalkış — yavaş tırmanışla ~{tr(E['hover_agl_medyan'], 1)} m askı (olay öncesi {tr(E['hover_agl_son'], 2, True)} m)",
             detay=f"ÖLÇÜM: EV 28 {t2(E['kalkis'])} s · roll/pitch/yaw çubukları {t2(E['kalkis'])}–{t2(E['cubuk_cikis'])} s ortada · "
                   f"{gaz_metni(E)} · yükseklik 3 s sonra {tr(E['agl_kalkis3'], 2, True)} m, olay öncesi {tr(E['hover_agl_son'], 2, True)} m (CTUN)"),
    ]
    for n in (1, 2):
        O.append(dict(k=f"basamak{n}", t=E[f"basamak{n}"], renk=SARI, kisa=f"Basamak {n}",
                      baslik="Motor dengesizliği basamakla büyüyor (ölçüm) — gövde esniyor (çıkarım)",
                      detay=f"ÖLÇÜM: CCW−CW 1 s ort. {tr(E[f'basamak{n}_once'], 0, True)} → {tr(E[f'basamak{n}_sonra'], 0, True)} µs "
                            f"({t2(E[f'basamak{n}'])} s) · roll/pitch/yaw çubukları ortada · gaz {gaz_durum_ad[E[f'basamak{n}_gaz']]}, "
                            f"DCRt {tr(E[f'basamak{n}_dcrt'], 0, True)} cm/s"))
    O += [
        dict(k="sag", t=E["sag"], renk=SARI, kisa="Sağ düzeltme",
             baslik=f"Kısa sağ düzeltme (roll {tr(E['sag_roll'], 0)}°)",
             detay=f"ÖLÇÜM: RCIN C1 en çok {E['sag_c1']:.0f} µs ({t2(E['sag'])}–{t2(E['sag_son'])} s) · "
                   f"roll en çok {tr(E['sag_roll'], 1, True)}° ({t2(E['sag_roll_t'])} s)"),
        dict(k="telemetri", t=E["telemetri"], renk=MAVI, kisa="Telemetri son",
             baslik="Telemetri: yer istasyonuna ulaşan son paket",
             detay=f"ÖLÇÜM (MP tlog): {tl['son_tip']}, time_boot_ms {tr(tl['son_tb'], 3)} s (PC {yerel_saat(V, tl['son_pc'])}) · "
                   f"ATTITUDE periyodu {tr(tl['att_periyot'], 2)} s → sıradaki paket ~{t2(E['telemetri_kesik'])} s'de gelmedi; "
                   f"kesilme bu anda, yani başlangıçtan ({t2(E['baslangic'])} s) {kesik_sira} belli olur"),
        dict(k="baslangic", t=E["baslangic"], renk=KIRMIZI, kisa="Başlangıç",
             baslik="Başlangıç: ön-sağ köşe düştü (ölçüm: GyrX/GyrY) — itki kaybı (çıkarım)",
             detay=f"ÖLÇÜM: |a| {tr(E['bas_a_once'], 1)} → {tr(E['bas_a'], 1)} m/s² · GyrX {tr(E['bas_gx'], 0, True)} °/s (sağ aşağı) · "
                   f"GyrY {tr(E['bas_gy'], 0, True)} °/s (burun aşağı)"),
        dict(k="pervane", t=E["pervane"], t2=E["pervane_bitis"], renk=KIRMIZI, kisa="Pervane/clip",
             baslik="Titreşim/clip patlaması (ölçüm) — pervaneler birbirine girdi (çıkarım + kullanıcı beyanı)",
             detay=f"ÖLÇÜM: |a| {tr(E['pervane_a1'], 1)} → {tr(E['pervane_a2'], 1)} m/s² · Clip IMU0 {E['clip0_once']:.0f} → "
                   f"{E['clip0_sonra']:.0f}, IMU1 {E['clip1_once']:.0f} → {E['clip1_sonra']:.0f} · VIBE en çok {tr(E['vibe_max_xyz'], 0)}"),
        dict(k="kopma", t=E["kopma"], t2=E["kopma_bitis"], renk=KIRMIZI, kisa="GPS·pusula",
             baslik="GPS ve pusula verisi HAVADA kesildi (ölçüm) — kablo kopması (çıkarım + beyan)",
             detay=f"ÖLÇÜM: GPS son örnek {t2(E['gps_son'])} s (sıradaki ~{t2(E['gps_son'] + E['gps_periyot'])} gelmedi) · "
                   f"harici pusula son güncelleme {t2(E['kopma'])}, {t2(E['kopma_bitis'])} s'den itibaren donuk · "
                   f"çarpmadan {tr(E['carpma'] - E['kopma_bitis'], 1)}–{tr(E['carpma'] - E['kopma'], 1)} s önce"),
        dict(k="ters", t=E["ters"], renk=KIRMIZI, kisa=f"Ters {tr(E['ters_roll'], 0)}°",
             baslik=f"Ters döndü (roll {tr(E['ters_roll'], 0)}°)",
             detay=f"ÖLÇÜM: ATT roll {tr(E['ters_roll'], 1, True)}°, pitch {tr(E['ters_pitch'], 1, True)}° · "
                   f"pilot LAND anahtarı C5 {t2(E['c5_degisim'])} s → mod Land {t2(E['land_mod'])} s (etkisi yok)"),
        dict(k="carpma", t=E["carpma"], renk=KIRMIZI, kisa="Çarpma",
             baslik="Yere çarpma",
             detay=f"ÖLÇÜM: |a| {tr(E['carpma_a'], 1)} m/s² (IMU0) · Clip IMU0 {E['clip0_ters']:.0f} → {E['clip0_carpma']:.0f}"
                   + (f" · ERR pusula (Subsys {E['err_pusula'][1]}, ECode {E['err_pusula'][2]}) {t2(E['err_pusula'][0])} s"
                      if E["err_pusula"] else "")),
        dict(k="disarm", t=E["disarm"], renk=SOLUK, kisa="CH6 disarm",
             baslik="CH6 disarm",
             detay=f"ÖLÇÜM: RCIN C6 {E['c6_once']:.0f} → {E['c6_sonra']:.0f} µs {t2(E['c6_dusuk'])} s · ARM disarm "
                   f"{t2(E['disarm'])} s (çarpmadan {tr(E['disarm'] - E['carpma'], 1)} s sonra)"),
        dict(k="gps0", t=E["gps0"], renk=SOLUK, kisa="GPS durum 0",
             baslik=f"GPS kaydı: durum {E['gps0_st']}, {E['gps0_ns']} uydu",
             detay=f"ÖLÇÜM: {t2(E['gps_son'])} s'den sonraki ilk GPS kaydı {t2(E['gps0'])} s — durum {E['gps0_st']} "
                   f"({GPS_DURUM.get(E['gps0_st'], '?')}), {E['gps0_ns']} uydu"),
    ]
    O.sort(key=lambda o: o["t"])
    return O


# ----------------------------------------------------------------------------
# Çizici
# ----------------------------------------------------------------------------
class Cizer:
    KOL = 0.25
    PERV_R = 0.115

    def __init__(self, V, E, yaw_ref=None):
        self.V, self.E = V, E
        self.fontlar = {}
        self.uyarilar = set()
        self.yaw_ref = E["yaw_ref"] if yaw_ref is None else yaw_ref
        if V is not None:
            P = V["P"]
            rng = P["MOT_PWM_MAX"] - P["MOT_PWM_MIN"]
            self.pwm_dur = P["MOT_PWM_MIN"]
            self.taban = math.floor(P["MOT_PWM_MIN"] + P["MOT_SPIN_MIN"] * rng)
            self.tavan = math.floor(P["MOT_PWM_MIN"] + P["MOT_SPIN_MAX"] * rng)
            self.olaylar = olay_listesi(V, E)
        else:
            self.pwm_dur, self.taban, self.tavan = 1000, 1150, 1949
            self.olaylar = []
        pw, ph = R3[2] - R3[0], R3[3] - R3[1]
        self.kam = Kamera((0, 0, 0.30), 30.0, 40.0, 2.35, 1080.0, (pw * 0.5, ph * 0.56))
        self._onbellek = {}
        self.kart_denetim = {}
        self.son_denetim = None
        self.kayit_sifirla()
        self._govde_hazirla()

    # --- yerleşim kaydı ve denetimi
    def kayit_sifirla(self, taban=None):
        if taban is None:
            self.K = {"yazi": [], "cizgi": [], "sekil": [], "etiket": []}
        else:
            self.K = {k: list(v) for k, v in taban.items()}

    def kayit_cizgi(self, p0, p1, ad):
        self.K["cizgi"].append(((float(p0[0]), float(p0[1])), (float(p1[0]), float(p1[1])), ad))

    def kayit_kutu(self, b, ad, tur="sekil"):
        self.K[tur].append((tuple(float(q) for q in b), ad))

    def kayit_denetle(self):
        """Yazı–yazı, çizgi–yazı, şekil–yazı ve çizgi–etiket kutusu kesişimlerini sayar (1 px içeri çekilmiş kutularla)."""
        K = self.K
        Y = [y for y in K["yazi"] if y[0][2] > y[0][0] and y[0][3] > y[0][1]]
        sorun = []
        n = {"yy": 0, "yc": 0, "ys": 0, "ce": 0}
        ic = lambda b, p: (b[0] + p, b[1] + p, b[2] - p, b[3] - p)
        sekiller = K["sekil"] + K["etiket"]
        for i, (bb, s, serbest, boy, yard) in enumerate(Y):
            bi = ic(bb, 1)
            for j in range(i + 1, len(Y)):
                if kutu_kes(bi, ic(Y[j][0], 1)):
                    n["yy"] += 1
                    sorun.append(f"yazı×yazı: ‘{s}’ × ‘{Y[j][1]}’")
            for p0, p1, ad in K["cizgi"]:
                if seg_kutu(p0, p1, bi):
                    n["yc"] += 1
                    sorun.append(f"çizgi×yazı: {ad} × ‘{s}’")
            if not serbest:
                for r, ad in sekiller:
                    if kutu_kes(bi, r):
                        n["ys"] += 1
                        sorun.append(f"şekil×yazı: {ad} × ‘{s}’")
        for p0, p1, ad in K["cizgi"]:
            for r, rad in K["etiket"]:
                if rad != ad and seg_kutu(p0, p1, ic(r, 2)):
                    n["ce"] += 1
                    sorun.append(f"çizgi×etiket kutusu: {ad} × {rad}")
        veri = [y[3] for y in Y if not y[4]]
        yard = [y[3] for y in Y if y[4]]
        n["kucuk"] = sum(1 for y in Y if y[3] < (MIN_YARDIMCI_BOY if y[4] else MIN_VERI_BOY))
        n["min_veri"] = min(veri) if veri else 99
        n["min_yard"] = min(yard) if yard else 99
        n["yazi"] = len(Y)
        n["sorun"] = sorun[:6]
        return n

    # --- yazı
    def font(self, boy, kalin=False):
        k = (boy, kalin)
        if k not in self.fontlar:
            self.fontlar[k] = ImageFont.truetype(FONT_B if kalin else FONT_R, boy)
        return self.fontlar[k]

    def genislik(self, s, boy, kalin=False):
        return self.font(boy, kalin).getlength(s)

    def yaz(self, d, x, y, s, boy, renk=YAZI, kalin=False, anchor="lt", maxw=None, sinir=None, yardimci=False, serbest=False):
        b0 = boy
        alt_sinir = MIN_YARDIMCI_BOY if yardimci else MIN_VERI_BOY
        if maxw is not None:
            while boy > min(alt_sinir, b0) and self.genislik(s, boy, kalin) > maxw:
                boy -= 1
            if self.genislik(s, boy, kalin) > maxw + 0.5:
                self.uyarilar.add(f"SIĞMADI: '{s[:40]}' ({self.genislik(s, boy, kalin):.0f} > {maxw})")
            elif b0 - boy > 4:
                self.uyarilar.add(f"küçültüldü {b0}->{boy}: '{s[:40]}'")
        f = self.font(boy, kalin)
        d.text((x, y), s, font=f, fill=tuple(int(c) for c in renk), anchor=anchor)
        bb = d.textbbox((x, y), s, font=f, anchor=anchor)
        sn = sinir if sinir is not None else (0, 0, W, H)
        if bb[0] < sn[0] - 1 or bb[1] < sn[1] - 1 or bb[2] > sn[2] + 1 or bb[3] > sn[3] + 1:
            self.uyarilar.add(f"TAŞMA: '{s[:40]}' bbox={bb} sınır={sn}")
        self.K["yazi"].append((tuple(float(q) for q in bb), s[:48], serbest, boy, yardimci))
        return bb

    def sar(self, s, boy, kalin, maxw):
        kel = s.split(" ")
        satirlar, cur = [], ""
        for w_ in kel:
            den = (cur + " " + w_).strip()
            if self.genislik(den, boy, kalin) <= maxw or not cur:
                cur = den
            else:
                satirlar.append(cur)
                cur = w_
        if cur:
            satirlar.append(cur)
        return satirlar

    def pil_yaz(self, img, yazilar):
        pil = Image.fromarray(img)
        d = ImageDraw.Draw(pil)
        for y in yazilar:
            self.yaz(d, *y[:5], **y[5] if len(y) > 5 else {})
        return np.array(pil)

    # --- renk
    def pwm_renk(self, pwm):
        if pwm <= self.pwm_dur + 1:
            return (95, 100, 112)
        u = min(max((pwm - self.taban) / (self.tavan - self.taban), 0.0), 1.0)
        if u < 0.5:
            c = PWM_MAVI * (1 - u / 0.5) + PWM_SARI * (u / 0.5)
        else:
            c = PWM_SARI * (1 - (u - 0.5) / 0.5) + PWM_KIRMIZI * ((u - 0.5) / 0.5)
        return tuple(int(v) for v in c)

    # --- 3B gövde
    def _govde_hazirla(self):
        a = self.KOL / math.sqrt(2)
        ang = np.linspace(0, 2 * math.pi, 40, endpoint=False)
        self.g_motor = {}
        for k, (sx, sy) in MOTOR_ISARET.items():
            c = np.array([sx * a, sy * a, 0.0])
            u = c / np.linalg.norm(c)
            n = np.array([-u[1], u[0], 0.0])
            w = 0.013
            kol = np.array([u * 0.05 + n * w, c + n * w, c - n * w, u * 0.05 - n * w])
            mot_alt = c + np.stack([0.024 * np.cos(ang[::2]), 0.024 * np.sin(ang[::2]), np.zeros(20)], 1)
            mot_ust = mot_alt + [0, 0, -0.035]
            disk = c + np.stack([self.PERV_R * np.cos(ang), self.PERV_R * np.sin(ang), np.full(40, -0.045)], 1)
            yon = -1 if MOTOR_YER[k][1] == "CCW" else 1  # yukarıdan CW: x→y yönünde açı artar
            th0 = math.atan2(sy, sx) + math.radians(40)
            th = th0 + yon * np.linspace(0, math.radians(110), 14)
            ok = c + np.stack([0.082 * np.cos(th), 0.082 * np.sin(th), np.full(14, -0.047)], 1)
            ta = th[-1]
            tip = c + np.array([0.082 * math.cos(ta), 0.082 * math.sin(ta), -0.047])
            teg = np.array([-math.sin(ta), math.cos(ta), 0]) * yon
            rad = np.array([math.cos(ta), math.sin(ta), 0])
            bas = np.array([tip + teg * 0.022, tip - teg * 0.004 + rad * 0.013, tip - teg * 0.004 - rad * 0.013])
            self.g_motor[k] = dict(merkez=c, kol=kol, mot_alt=mot_alt, mot_ust=mot_ust, disk=disk, ok=ok, ok_bas=bas)
        pl = np.array([[0.085, 0.035], [0.05, 0.065], [-0.05, 0.065], [-0.085, 0.035],
                       [-0.085, -0.035], [-0.05, -0.065], [0.05, -0.065], [0.085, -0.035]])
        self.g_plaka_ust = np.column_stack([pl, np.full(8, -0.016)])
        self.g_plaka_alt = np.column_stack([pl, np.full(8, 0.012)])
        on = np.array([[0.125, 0.0], [0.06, 0.035], [0.06, 0.012], [-0.03, 0.012], [-0.03, -0.012], [0.06, -0.012], [0.06, -0.035]])
        self.g_on_ust = np.column_stack([on, np.full(7, -0.018)])
        self.g_on_alt = np.column_stack([on, np.full(7, 0.014)])

    def _dunya(self, pts, R, h):
        q = np.asarray(pts, float) @ R.T  # (ileri, sağ, aşağı)
        return np.stack([q[..., 1], q[..., 0], h - q[..., 2]], -1)

    def govde_dunya(self, roll, pitch, yaw_goreli, h):
        R = rot(roll, pitch, yaw_goreli)
        mot = {k: self._dunya(g["merkez"][None], R, h)[0] for k, g in self.g_motor.items()}
        burun = self._dunya(np.array([[1.0, 0, 0]]), R, 0.0)[0]
        return R, mot, burun

    def zemin_ciz(self, img, kam, bolge, yazilar=None, etiket=None, n=6, ok_ciz=True):
        """Sabit katman: zemin ızgarası ve referans yön oku (bölge görünümüne)."""
        v = img[bolge[1]:bolge[3], bolge[0]:bolge[2]]
        ad = 0.25
        for i in range(-n, n + 1):
            for yon in (0, 1):
                s = i * ad
                if yon == 0:
                    P = np.array([[s, -n * ad, 0], [s, n * ad, 0]])
                else:
                    P = np.array([[-n * ad, s, 0], [n * ad, s, 0]])
                P = np.linspace(P[0], P[1], 25)
                uv, z = kam.izdus(P)
                if (z < 0.2).any():
                    continue
                renk = (58, 68, 86) if i % 4 == 0 else IZGARA
                cizgi(v, uv, renk, 1)
        ok = np.array([[0, 0.34, 0], [0, 0.92, 0]])
        uv, z = kam.izdus(np.linspace(ok[0], ok[1], 10))
        if ok_ciz and (z > 0.2).all():
            cizgi(v, uv, (95, 108, 132), 3)
            bas, _ = kam.izdus(np.array([[0, 1.02, 0], [0.05, 0.9, 0], [-0.05, 0.9, 0]]))
            dolu(v, bas, (95, 108, 132))
        if yazilar is not None and etiket:
            yazilar.append((bolge[0] + 14, bolge[3] - 80, etiket, 16, (140, 151, 170),
                            dict(sinir=bolge, maxw=bolge[2] - bolge[0] - 28, yardimci=True)))

    def drone_ciz(self, img, roll, pitch, yaw_goreli, h, pwms, yazilar, etiket=True, kam=None, bolge=R3,
                  engeller=None, rozet=None, alt_rezerv=0, on_metin="ÖN"):
        """img: tam kare; çizim bölge görünümüne yapılır. pwms: {1..4: µs}.
        engeller: {"kutular": [(x0,y0,x1,y1)], "cizgiler": [((x,y),(x,y))]} tam kare koordinatında; etiketler bunlardan kaçar."""
        kam = self.kam if kam is None else kam
        bx0, by0 = bolge[0], bolge[1]
        v = img[bolge[1]:bolge[3], bolge[0]:bolge[2]]
        R = rot(roll, pitch, yaw_goreli)
        # yere girmeme payı: en alçak nokta ≥ 0
        tum = np.concatenate([np.concatenate([g["disk"], g["kol"], g["mot_alt"]]) for g in self.g_motor.values()]
                             + [self.g_plaka_ust, self.g_plaka_alt])
        zmin = self._dunya(tum, R, 0.0)[:, 2].min()
        h_ciz = max(h, -zmin + 0.004)
        D = lambda p: self._dunya(p, R, h_ciz)
        merkez_d = D(np.zeros((1, 3)))[0]
        ust_d = D(np.array([[0, 0, -1.0]]))[0] - merkez_d
        ust_gorunur = float(np.dot(ust_d, kam.C - merkez_d)) > 0

        # gölge
        golge = []
        for g in self.g_motor.values():
            for parca in (g["kol"], g["disk"]):
                p = D(parca)
                p[:, 2] = 0
                golge.append(kam.izdus(p)[0])
        p = D(self.g_plaka_ust)
        p[:, 2] = 0
        golge.append(kam.izdus(p)[0])
        alfa = 0.55 * math.exp(-max(h_ciz, 0) / 1.6)
        allp = np.concatenate(golge)
        x0, y0 = max(int(allp[:, 0].min()) - 2, 0), max(int(allp[:, 1].min()) - 2, 0)
        x1, y1 = min(int(allp[:, 0].max()) + 3, v.shape[1]), min(int(allp[:, 1].max()) + 3, v.shape[0])
        if x1 > x0 and y1 > y0:
            maske = np.zeros((y1 - y0, x1 - x0), np.uint8)
            for gp in golge:
                cv2.fillPoly(maske, [_p(gp - [x0, y0])], 255, cv2.LINE_AA, 3)
            roi = v[y0:y1, x0:x1]
            m = (maske.astype(np.float32) / 255.0 * alfa)[..., None]
            roi[:] = (roi * (1 - m)).astype(np.uint8)
        # yükseklik çizgisi
        uv, _ = kam.izdus(np.array([merkez_d, [merkez_d[0], merkez_d[1], 0.0]]))
        kesikli(v, uv[0], uv[1], (120, 128, 146), 1, 6, 5)

        def derinlik(p3):
            return float(kam.izdus(p3)[1].mean())

        kollar, motorlar, diskler = [], [], []
        for k, g in self.g_motor.items():
            kp = D(g["kol"])
            kollar.append((derinlik(kp), kam.izdus(kp)[0]))
            ma, mu = kam.izdus(D(g["mot_alt"]))[0], kam.izdus(D(g["mot_ust"]))[0]
            hull = cv2.convexHull(np.concatenate([ma, mu]).astype(np.float32)).reshape(-1, 2)
            motorlar.append((derinlik(D(g["mot_ust"])), hull, mu if ust_gorunur else ma))
            dp = D(g["disk"])
            diskler.append((derinlik(dp), k, kam.izdus(dp)[0], kam.izdus(D(g["ok"]))[0], kam.izdus(D(g["ok_bas"]))[0]))
        kollar.sort(key=lambda a: -a[0])
        motorlar.sort(key=lambda a: -a[0])
        diskler.sort(key=lambda a: -a[0])

        def ciz_kollar():
            for _, p in kollar:
                dolu(v, p, (92, 100, 118))
                cizgi(v, p, (30, 34, 44), 1, True)

        plaka = kam.izdus(D(self.g_plaka_ust if ust_gorunur else self.g_plaka_alt))[0]

        def ciz_plaka():
            dolu(v, plaka, (74, 84, 104) if ust_gorunur else (52, 58, 72))
            cizgi(v, plaka, (150, 160, 182), 1, True)
            on = kam.izdus(D(self.g_on_ust if ust_gorunur else self.g_on_alt))[0]
            dolu(v, on, (245, 245, 245) if ust_gorunur else (175, 175, 175))

        def ciz_motorlar():
            for _, hull, kapak in motorlar:
                dolu(v, hull, (150, 156, 168))
                cizgi(v, hull, (40, 44, 54), 1, True)
                dolu(v, kapak, (190, 195, 205))

        def ciz_diskler():
            for _, k, dp, okp, okb in diskler:
                renk = self.pwm_renk(pwms[k])
                alfa_dolu(v, dp, renk, 0.42)
                cizgi(v, dp, renk, 2, True)
                if ust_gorunur:
                    cizgi(v, okp, (240, 242, 246), 2)
                    dolu(v, okb, (240, 242, 246))

        if ust_gorunur:
            ciz_kollar(); ciz_plaka(); ciz_motorlar(); ciz_diskler()
        else:
            ciz_diskler(); ciz_motorlar(); ciz_kollar(); ciz_plaka()

        mer_uv = kam.izdus(merkez_d[None])[0][0]
        yerlesen = []
        if etiket:
            yerlesen = self._etiketler(v, kam, D, diskler, plaka, mer_uv, bx0, by0, engeller, rozet, alt_rezerv, on_metin, yazilar, bolge)
        return dict(h_ciz=h_ciz, ust_gorunur=ust_gorunur, R=R, D=D, etiketler=yerlesen)

    def _etiketler(self, v, kam, D, diskler, plaka, mer_uv, bx0, by0, engeller, rozet, alt_rezerv, on_metin, yazilar, bolge):
        """Etiket yerleşimi. Sert koşullar: kutular birbirine, rozete, dipnot bandına ve verilen engellere değmez;
        hiçbir bağlantı çizgisi başka bir kutudan geçmez. Yumuşak cezalar: kutunun pervane diski/gövde üstüne binmesi,
        çizginin başka disk üstünden geçmesi, dıştan içe doğru yön. En kısa çizgili ve en az cezalı aday seçilir."""
        PW, PH = v.shape[1], v.shape[0]
        sert = []
        if rozet is not None:
            sert.append((0, 0, rozet[0] + 6, rozet[1] + 6))
        if alt_rezerv:
            sert.append((0, PH - alt_rezerv, PW, PH))
        ek_cizgi = []
        if engeller:
            for b in engeller.get("kutular", []):
                sert.append((b[0] - bx0, b[1] - by0, b[2] - bx0, b[3] - by0))
            for p0, p1 in engeller.get("cizgiler", []):
                ek_cizgi.append(((p0[0] - bx0, p0[1] - by0), (p1[0] - bx0, p1[1] - by0)))
        disk_kutu = {}
        for _, k, dp, _, _ in diskler:
            x0_, y0_ = dp.min(0)
            x1_, y1_ = dp.max(0)
            dx_, dy_ = (x1_ - x0_) * 0.12, (y1_ - y0_) * 0.12
            disk_kutu[k] = (x0_ + dx_, y0_ + dy_, x1_ - dx_, y1_ - dy_)
        govde = (plaka[:, 0].min(), plaka[:, 1].min(), plaka[:, 0].max(), plaka[:, 1].max())
        yerlesen = []  # (ad, kutu, çizgi)

        def yerlestir(ad, hedef, bw, bh, yon, cizgi_min, d_aralik, sahip=None):
            hedef = np.asarray(hedef, float)
            aday = []
            for ai in range(24):
                th = ai * math.pi / 12
                u = np.array([math.cos(th), math.sin(th)])
                ext = abs(u[0]) * bw / 2 + abs(u[1]) * bh / 2
                sap = 1.0 - float(np.dot(u, yon))
                for d in d_aralik:
                    aday.append((d + 40.0 * sap, d, ext, u))
            aday.sort(key=lambda a: a[0])
            en_iyi = None
            for taban_c, d, ext, u in aday:
                if en_iyi is not None and taban_c >= en_iyi[0]:
                    break
                cx, cy = hedef + u * (d + ext)
                b = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
                if b[0] < 4 or b[1] < 4 or b[2] > PW - 4 or b[3] > PH - 4:
                    continue
                if any(kutu_kes(b, q, 4) for q in sert) or any(kutu_kes(b, y[1], 6) for y in yerlesen):
                    continue
                qx, qy = min(max(hedef[0], b[0]), b[2]), min(max(hedef[1], b[1]), b[3])
                seg = ((hedef[0], hedef[1]), (qx, qy)) if math.hypot(qx - hedef[0], qy - hedef[1]) > cizgi_min else None
                if seg is not None and (any(seg_kutu(seg[0], seg[1], genislet(y[1], 3)) for y in yerlesen)
                                        or any(seg_kutu(seg[0], seg[1], genislet(q, 2)) for q in sert)):
                    continue
                if any(y[2] is not None and seg_kutu(y[2][0], y[2][1], genislet(b, 3)) for y in yerlesen):
                    continue
                if any(seg_kutu(s0, s1, genislet(b, 3)) for s0, s1 in ek_cizgi):
                    continue
                ceza = taban_c
                ceza += 150.0 * sum(kutu_kes(b, dk) for dk in disk_kutu.values())
                ceza += 150.0 * kutu_kes(b, govde)
                if seg is not None:
                    ceza += 30.0 * sum(seg_kutu(seg[0], seg[1], dk) for kk, dk in disk_kutu.items() if kk != sahip)
                if en_iyi is None or ceza < en_iyi[0]:
                    en_iyi = (ceza, b, seg)
            if en_iyi is None:
                self.uyarilar.add(f"3B etiket yeri bulunamadı: {ad}")
                cx = min(max(hedef[0], bw / 2 + 4), PW - bw / 2 - 4)
                cy = min(max(hedef[1] - bh, bh / 2 + 4), PH - bh / 2 - 4)
                en_iyi = (0.0, (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2), None)
            yerlesen.append((ad, en_iyi[1], en_iyi[2]))

        # ÖN etiketi önce (burun ucunda)
        tip = kam.izdus(D(np.array([[0.215, 0, -0.02]])))[0][0]
        on_bw, on_bh = self.genislik(on_metin, 18, True) + 14, 28
        yon_on = tip - mer_uv
        yon_on = yon_on / np.linalg.norm(yon_on) if np.linalg.norm(yon_on) > 1 else np.array([0, -1.0])
        yerlestir("ÖN", tip, on_bw, on_bh, yon_on, 18.0, [2, 8, 16, 26, 38, 52, 68, 86, 110])
        s2_boy = 18
        for _, k, dp, _, _ in sorted(diskler, key=lambda a: a[0]):
            c_uv = dp.mean(0)
            r_ekr = float(np.max(np.linalg.norm(dp - c_uv, axis=1)))
            yon = c_uv - mer_uv
            nrm = np.linalg.norm(yon)
            yon = yon / nrm if nrm > 1 else np.array([0, -1.0])
            s1, s2 = f"M{k}", f"{MOTOR_YER[k][0]} · {MOTOR_YER[k][1]}"
            bw = max(self.genislik(s1, 20, True), self.genislik(s2, s2_boy)) + 18
            bh = 54
            d0 = 0.85 * r_ekr
            yerlestir(f"M{k}", c_uv, bw, bh, yon, 0.0, [d0 + e for e in (0, 10, 22, 36, 52, 70, 90, 115, 145, 180, 220, 270)], sahip=k)

        # önce çizgiler, sonra opak kutular ve yazılar
        for ad, b, seg in yerlesen:
            if seg is None:
                continue
            renk = (235, 235, 235) if ad == "ÖN" else MOTOR_RENK[int(ad[1])]
            cizgi(v, [seg[0], seg[1]], renk, 2)
            self.kayit_cizgi((seg[0][0] + bx0, seg[0][1] + by0), (seg[1][0] + bx0, seg[1][1] + by0), ad)
        for ad, b, seg in yerlesen:
            x0_, y0_, x1_, y1_ = (int(round(q)) for q in b)
            cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
            if ad == "ÖN":
                cv2.rectangle(v, (x0_, y0_), (x1_, y1_), (245, 245, 245), -1)
                yazilar.append((bx0 + cx, by0 + cy, on_metin, 18, (10, 12, 16), dict(kalin=True, anchor="mm", sinir=bolge, serbest=True)))
            else:
                k = int(ad[1])
                cv2.rectangle(v, (x0_, y0_), (x1_, y1_), (8, 10, 14), -1)
                cv2.rectangle(v, (x0_, y0_), (x1_, y1_), MOTOR_RENK[k], 2, cv2.LINE_AA)
                yazilar.append((bx0 + cx, by0 + b[1] + 5, f"M{k}", 20, MOTOR_RENK[k], dict(kalin=True, anchor="mt", sinir=bolge, serbest=True)))
                yazilar.append((bx0 + cx, by0 + b[1] + 29, f"{MOTOR_YER[k][0]} · {MOTOR_YER[k][1]}", s2_boy, (210, 215, 225),
                                dict(anchor="mt", sinir=bolge, serbest=True)))
            self.kayit_kutu((b[0] + bx0, b[1] + by0, b[2] + bx0, b[3] + by0), ad, "etiket")
        return [(ad, (b[0] + bx0, b[1] + by0, b[2] + bx0, b[3] + by0)) for ad, b, _ in yerlesen]

    # --- sabit katmanlar
    def panel(self, img, r):
        cv2.rectangle(img, (r[0], r[1]), (r[2] - 1, r[3] - 1), PANEL, -1)
        cv2.rectangle(img, (r[0], r[1]), (r[2] - 1, r[3] - 1), CERCEVE, 1)

    def plot_y(self, ad, val):
        y0, y1 = PLOT_Y[ad]
        lo, hi = PLOT_ARA[ad]
        return y1 - (val - lo) / (hi - lo) * (y1 - y0)

    def taban_goruntu(self, gor):
        if gor in self._onbellek:
            return self._onbellek[gor]
        V, E = self.V, self.E
        self.kayit_sifirla()
        img = np.full((H, W, 3), ZEMIN, np.uint8)
        cv2.rectangle(img, (0, 0), (W, UST_H), (16, 20, 28), -1)
        cv2.line(img, (0, UST_H), (W, UST_H), CERCEVE, 1)
        yz = []
        for r in (R3, RUST, RORTA, RALT, SERIT):
            self.panel(img, r)
        yz.append((24, 15, f"NAVITAS — {self.tarih_baslik()} düşüşü · log canlandırması", 28, YAZI, dict(kalin=True)))

        # 3B zemin + dipnot bandı
        self.zemin_ciz(img, self.kam, R3, yz, f"Zemindeki gri ok: kalkış öncesi burun yönü (yaw {tr(self.yaw_ref % 360, 0)}°)")
        alfa_kutu(img, R3[0] + 1, R3[3] - R3_ALT_REZERV + 2, R3[2] - 1, R3[3] - 1, PANEL, 0.82)
        yz.append((R3[0] + 14, R3[3] - 58, "Kamera sabit, eğik üstten · 3B çizim temsili (ölçüler gerçek değil) · "
                   "tutum: ATT 10 Hz, doğrusal ara değer", 16, SOLUK, dict(sinir=R3, maxw=R3[2] - R3[0] - 28, yardimci=True)))

        # --- sağ üst: motor çubukları (yatay)
        yz.append((952, 76, "Motor çıkışları — RCOU (µs)", 18, YAZI, dict(kalin=True, sinir=RUST)))
        for n, k in enumerate((1, 2, 3, 4)):
            yc = MB_Y[n]
            yz.append((952, yc, f"M{k}", 18, MOTOR_RENK[k], dict(kalin=True, anchor="lm", sinir=RUST)))
            yz.append((990, yc, f"{MOTOR_YER[k][0]} · {MOTOR_YER[k][1]}", 18, SOLUK, dict(anchor="lm", sinir=RUST)))
            cv2.rectangle(img, (MB_X0, yc - 9), (MB_X1, yc + 9), (32, 38, 50), -1)
            cv2.rectangle(img, (MB_X0, yc - 9), (MB_X1, yc + 9), CERCEVE, 1)
            self.kayit_kutu((MB_X0, yc - 9, MB_X1, yc + 9), f"motor çubuğu M{k}")
        for pwm, metin in ((self.taban, f"taban {self.taban}"), (self.tavan, f"{self.tavan} tavan")):
            x = self.mb_x(pwm)
            self.kayit_cizgi((x, MB_Y[0] - 14), (x, MB_Y[-1] + 14), f"{pwm} µs çizgisi")
            yz.append((x, MB_Y[-1] + 19, metin, 18, SOLUK, dict(anchor="mt", sinir=RUST)))
        cv2.line(img, (1417, 80), (1417, 232), CERCEVE, 1)
        # CCW−CW göstergesi
        yz.append((GX_T, 74, "CCW − CW = (M1+M2) − (M3+M4)", 18, YAZI, dict(kalin=True, sinir=RUST)))
        cv2.rectangle(img, (GX0, 129), (GX1, 147), (32, 38, 50), -1)
        self.kayit_kutu((GX0, 129, GX1, 147), "CCW−CW göstergesi")
        for d_ in (-60, 60):
            kesikli(img, (self.fx(d_), 125), (self.fx(d_), 151), KIRMIZI, 1, 4, 3)
            self.kayit_cizgi((self.fx(d_), 125), (self.fx(d_), 151), f"eşik {d_}")
        cv2.line(img, (int(self.fx(0)), 123), (int(self.fx(0)), 151), (200, 205, 215), 1)
        self.kayit_cizgi((self.fx(0), 123), (self.fx(0), 151), "CCW−CW sıfır")
        yz.append((GX0, 155, tr(-300, 0), 18, SOLUK, dict(anchor="lt", sinir=RUST)))
        yz.append((self.fx(0), 155, "0", 18, SOLUK, dict(anchor="mt", sinir=RUST)))
        yz.append((self.fx(60) + 9, 155, "eşik ±60 µs", 18, KIRMIZI, dict(anchor="lt", sinir=RUST)))
        yz.append((GX1, 155, tr(700, 0, True), 18, SOLUK, dict(anchor="rt", sinir=RUST)))
        # yaw hatası
        yz.append((GX_T, 181, "Yaw hatası = DesYaw − Yaw", 18, YAZI, dict(kalin=True, sinir=RUST)))
        cv2.rectangle(img, (GX0, 203), (GX1, 219), (32, 38, 50), -1)
        self.kayit_kutu((GX0, 203, GX1, 219), "yaw göstergesi")
        cv2.line(img, (int(self.yx(0)), 200), (int(self.yx(0)), 222), (200, 205, 215), 1)
        self.kayit_cizgi((self.yx(0), 200), (self.yx(0), 222), "yaw sıfır")
        yz.append((GX0, 225, tr(-45, 0) + "°", 18, SOLUK, dict(anchor="lt", sinir=RUST)))
        yz.append((self.yx(0), 225, "0°", 18, SOLUK, dict(anchor="mt", sinir=RUST)))
        yz.append((GX1, 225, tr(45, 0, True) + "°", 18, SOLUK, dict(anchor="rt", sinir=RUST)))

        # --- sağ orta: grafikler
        t0, t1 = EKSEN_TAM if gor == "tam" else EKSEN_YAKIN
        ek = f"tam eksen {tr(t0, 0)}–{tr(t1, 0)} s" if gor == "tam" else f"yakın eksen {tr(t0, 1)}–{tr(t1, 1)} s"
        basliklar = {"motor": (f"Motor çıkışları (µs) · {ek}", YAZI, True),
                     "fark": ("CCW − CW (µs) · ince: anlık · kalın sarı: 1 s ort. · kesik kırmızı: ±60", (205, 211, 222), False),
                     "vibe": ("VibeZ (IMU0 titreşimi), m/s²", TURUNCU, False),
                     "amag": ("|a| (IMU0 toplam ivme), m/s² · kesik: 1 g", MAVI, False)}
        for ad, (y0, y1) in PLOT_Y.items():
            cv2.rectangle(img, (PX0, y0), (PX1, y1), (16, 20, 28), -1)
            cv2.rectangle(img, (PX0, y0), (PX1, y1), CERCEVE, 1)
            self.kayit_kutu((PX0, y0, PX1, y1), f"grafik {ad}")
            s, renk, kalin = basliklar[ad]
            yz.append((PX0, y0 - 8, s, 18, renk, dict(kalin=kalin, anchor="ls", sinir=RORTA)))
            yv = lambda val, ad=ad: self.plot_y(ad, val)
            if ad == "motor":
                for pwm in (self.tavan, self.taban):
                    kesikli(img, (PX0, yv(pwm)), (PX1, yv(pwm)), (95, 100, 115), 1, 5, 4)
                    yz.append((PX0 - 6, yv(pwm), str(pwm), 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
            elif ad == "fark":
                for d_ in (-60, 60):
                    kesikli(img, (PX0, yv(d_)), (PX1, yv(d_)), (150, 60, 60), 1, 5, 4)
                cv2.line(img, (PX0, int(yv(0))), (PX1, int(yv(0))), (80, 86, 100), 1)
                yz.append((PX0 - 6, yv(0), "0", 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
                yz.append((PX0 - 6, yv(600), tr(600, 0, True), 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
            elif ad == "vibe":
                yz.append((PX0 - 6, yv(100), "100", 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
                yz.append((PX0 - 6, yv(0), "0", 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
            else:
                kesikli(img, (PX0, yv(G0)), (PX1, yv(G0)), (110, 140, 190), 1, 6, 4)
                kesikli(img, (PX0, yv(30)), (PX1, yv(30)), (60, 66, 80), 1, 3, 5)
                for val in (60, 30, 0):
                    yz.append((PX0 - 6, yv(val), str(val), 18, SOLUK, dict(anchor="rm", sinir=RORTA)))
                yz.append((PX1 + 6, yv(G0), "1 g", 18, MAVI, dict(anchor="lm", sinir=RORTA)))
        # motor lejantı (sağa yaslı, başlık satırında)
        x = PX1
        ly = PLOT_Y["motor"][0] - 8
        for k in (4, 3, 2, 1):
            s = f"M{k}"
            w_ = self.genislik(s, 18, True)
            yz.append((x - w_, ly, s, 18, MOTOR_RENK[k], dict(kalin=True, anchor="ls", sinir=RORTA)))
            cv2.line(img, (int(x - w_ - 24), ly - 6), (int(x - w_ - 6), ly - 6), MOTOR_RENK[k], 3, cv2.LINE_AA)
            x -= w_ + 24 + 18
        # x ekseni
        adim = 2.0 if gor == "tam" else 0.2
        tt = np.arange(math.ceil(t0 / adim - 1e-9) * adim, t1 + 1e-9, adim)
        for tv in tt:
            xx = PX0 + (tv - t0) / (t1 - t0) * (PX1 - PX0)
            for (y0, y1) in PLOT_Y.values():
                cv2.line(img, (int(xx), y1 - 3), (int(xx), y1), (90, 96, 110), 1)
            an = "lt" if abs(xx - PX0) < 1 else ("rt" if abs(xx - PX1) < 1 else "mt")
            yz.append((xx, X_ETIKET_Y, tr(tv, 0 if gor == "tam" else 1), 18, SOLUK, dict(anchor=an, sinir=RORTA)))
        # olay çizgileri (başlangıç, çarpma)
        for tv in (E["baslangic"], E["carpma"]):
            xx = PX0 + (tv - t0) / (t1 - t0) * (PX1 - PX0)
            for (y0, y1) in PLOT_Y.values():
                kesikli(img, (xx, y0 + 1), (xx, y1 - 1), (170, 70, 70), 1, 3, 3)

        parlak = img.copy()
        self._egriler(img, gor, soluk=True)
        self._egriler(parlak, gor, soluk=False)

        # --- HUD sabitleri
        for i, s in enumerate(["Log zamanı", "Yerel saat", "Uçuş modu", "Yükseklik", "Pil"]):
            yz.append((HUD_A_ETIKET, HUD_Y[i], s, 18, SOLUK, dict(anchor="lm", sinir=RALT)))
        for i, s in enumerate(["GPS", "Pusula", "Telemetri", "Titreşim", "RC anahtar"]):
            yz.append((HUD_B_ETIKET, HUD_Y[i], s, 18, SOLUK, dict(anchor="lm", sinir=RALT)))
        for bx, ad in CUBUK_KUTU:
            yz.append((bx + 52, 613, ad, 16, SOLUK, dict(anchor="mt", sinir=RALT, yardimci=True)))
            cv2.rectangle(img, (bx, CUBUK_Y0), (bx + 104, CUBUK_Y1), (30, 36, 48), -1)
            cv2.rectangle(img, (bx, CUBUK_Y0), (bx + 104, CUBUK_Y1), CERCEVE, 1)
            cm = (CUBUK_Y0 + CUBUK_Y1) // 2
            cv2.line(img, (bx + 52, CUBUK_Y0 + 2), (bx + 52, CUBUK_Y1 - 2), (52, 60, 76), 1)
            cv2.line(img, (bx + 2, cm), (bx + 102, cm), (52, 60, 76), 1)
            self.kayit_kutu((bx, CUBUK_Y0, bx + 104, CUBUK_Y1), f"çubuk kutusu {ad}")

        # --- şerit (zaman çizgisi)
        self._serit_statik(img, gor, yz)
        img = self.pil_yaz(img, yz)
        self._onbellek[gor] = (img, parlak, {k: list(v) for k, v in self.K.items()})
        return self._onbellek[gor]

    def mb_x(self, pwm):
        return MB_X0 + (min(max(pwm, 1000), 2000) - 1000) / 1000.0 * (MB_X1 - MB_X0)

    def fx(self, d):
        return GX0 + (min(max(d, -300), 700) + 300) / 1000.0 * (GX1 - GX0)

    def yx(self, d):
        return GX0 + (min(max(d, -45), 45) + 45) / 90.0 * (GX1 - GX0)

    def _egriler(self, img, gor, soluk):
        V, E = self.V, self.E
        t0, t1 = EKSEN_TAM if gor == "tam" else EKSEN_YAKIN
        f = 0.33 if soluk else 1.0
        kr = lambda c: tuple(int(v * f + 16 * (1 - f)) for v in c)
        nokta = gor != "tam"

        def ciz(ad, t, y, renk, k=1, nokta_ciz=False):
            y0, y1 = PLOT_Y[ad]
            lo, hi = PLOT_ARA[ad]
            w = (t >= t0 - 0.5) & (t <= t1 + 0.5)
            if not w.any():
                return
            xs = (t[w] - t0) / (t1 - t0) * (PX1 - PX0)
            ys = (y1 - y0) - (y[w] - lo) / (hi - lo) * (y1 - y0)
            vw = img[y0 + 1:y1, PX0:PX1 + 1]
            pts = np.stack([xs, ys - 1], 1)
            cizgi(vw, pts, kr(renk), k)
            if nokta_ciz:
                for p in pts:
                    if 0 <= p[0] <= PX1 - PX0:
                        cv2.circle(vw, (int(round(p[0])), int(round(p[1]))), 2, kr(renk), -1, cv2.LINE_AA)

        rt = V["rcou_t"]
        for k in (1, 2, 3, 4):
            ciz("motor", rt, V[f"M{k}"], MOTOR_RENK[k], 1, nokta)
        ciz("fark", rt, V["fark"], (190, 196, 210), 1, nokta)
        ciz("fark", rt, V["fark1s"], SARI, 2)
        ciz("vibe", V["vibe0_t"], V["vibe0_VibeZ"], TURUNCU, 2, nokta)
        ciz("amag", V["imu_t"], V["amag"], MAVI, 1, nokta)

    def _serit_statik(self, img, gor, yz):
        t0, t1 = EKSEN_TAM if gor == "tam" else EKSEN_YAKIN
        X = lambda t: TX0 + (t - t0) / (t1 - t0) * (TX1 - TX0)
        cv2.line(img, (TX0, EKSEN_Y), (TX1, EKSEN_Y), (120, 128, 146), 2)
        adim = 1.0 if gor == "tam" else 0.1
        tt = np.arange(math.ceil(t0 / adim - 1e-9) * adim, t1 + 1e-9, adim)
        for tv in tt:
            xx = int(round(X(tv)))
            buyuk = abs(tv / (2 * adim) - round(tv / (2 * adim))) < 1e-6
            cv2.line(img, (xx, EKSEN_Y - (6 if buyuk else 3)), (xx, EKSEN_Y + (6 if buyuk else 3)), (120, 128, 146), 1)
            if buyuk:
                son = tv >= t1 - 1e-9
                yz.append((xx, EKSEN_Y + 10, tr(tv, 0 if gor == "tam" else 1) + (" s" if son else ""), 18, SOLUK,
                           dict(anchor="rt" if son else "mt", sinir=SERIT)))
        # işaretler
        kume = ("baslangic", "pervane", "kopma", "ters", "carpma")
        etiketler = []
        for o in self.olaylar:
            if o["kisa"] is None or not (t0 <= o["t"] <= t1):
                continue
            xx = X(o["t"])
            if "t2" in o:
                cv2.line(img, (int(xx), EKSEN_Y), (int(X(min(o["t2"], t1))), EKSEN_Y), o["renk"], 6)
            cv2.line(img, (int(xx), EKSEN_Y - 8), (int(xx), EKSEN_Y + 2), o["renk"], 2)
            if gor == "tam" and o["k"] in kume:
                continue
            etiketler.append((xx, o["kisa"], o["renk"]))
        if gor == "tam":
            ob = [o for o in self.olaylar if o["k"] in kume]
            etiketler.append((X(ob[0]["t"]), f"Olay {tr(ob[0]['t'], 2)}–{tr(ob[-1]['t'], 2)} s", KIRMIZI))
        etiketler.sort(key=lambda e: e[0])
        # satır yerleşimi: aynı satırda yazı çakışmaz; hiçbir bağlantı çizgisi başka bir yazının içinden geçmez
        n_sat = len(SATIR_Y)
        satir_kutular = [[] for _ in range(n_sat)]
        cizgiler = []  # (x, başladığı satır)
        for xx, s, renk in etiketler:
            w_ = self.genislik(s, 18, True)
            yer = None
            for r in range(n_sat):
                for an in ("lt", "rt"):
                    x0, x1 = (xx + 5, xx + 5 + w_) if an == "lt" else (xx - 5 - w_, xx - 5)
                    if x1 > TX1 + 50 or x0 < SERIT[0] + 8:
                        continue
                    if any(x0 < b1 + 10 and x1 > b0 - 10 for b0, b1 in satir_kutular[r]):
                        continue
                    if any(r > rs and x0 - 4 <= cx <= x1 + 4 for cx, rs in cizgiler):
                        continue
                    if any(b0 - 4 <= xx <= b1 + 4 for rr in range(r + 1, n_sat) for b0, b1 in satir_kutular[rr]):
                        continue
                    yer = (r, x0, x1, an)
                    break
                if yer:
                    break
            if yer is None:
                self.uyarilar.add(f"ÇİZGİ ETİKETİ YER YOK: {s}")
                continue
            r, x0, x1, an = yer
            satir_kutular[r].append((x0, x1))
            cizgiler.append((xx, r))
            y_ust = SATIR_Y[r] + 2
            cv2.line(img, (int(xx), y_ust), (int(xx), EKSEN_Y - 8), tuple(int(c * 0.6) for c in renk), 1)
            self.kayit_cizgi((int(xx), y_ust), (int(xx), EKSEN_Y - 8), f"şerit çizgisi {s}")
            yz.append((x0 if an == "lt" else x1, SATIR_Y[r], s, 18, renk, dict(kalin=True, anchor=an, sinir=SERIT)))

    def tarih_baslik(self):
        V, E = self.V, self.E
        e = V["boot_utc"] + E["baslangic"] + V["tz_s"]
        d = datetime.datetime.fromtimestamp(e, datetime.timezone.utc)
        return f"{d.day} {AYLAR[d.month - 1]} {d.year} {d.strftime('%H:%M')}"

    # --- veri karesi
    def veri_karesi(self, t, bolum):
        V, E = self.V, self.E
        gor = "yakin" if bolum == "agir" else "tam"
        base, parlak, K0 = self.taban_goruntu(gor)
        self.kayit_sifirla(K0)
        t0, t1 = EKSEN_TAM if gor == "tam" else EKSEN_YAKIN
        img = base.copy()
        xc = PX0 + (t - t0) / (t1 - t0) * (PX1 - PX0)
        xi = int(min(max(round(xc), PX0), PX1 + 1))
        for (ya, yb) in PLOT_Y.values():  # imlecin solu parlak, sağı soluk (yalnız grafik iç bölgesi)
            img[ya + 1:yb, PX0:xi + 1] = parlak[ya + 1:yb, PX0:xi + 1]
        yz = []

        # başlık bölümü
        bas = {"canli": f"3/6 · Son uçuş — gerçek hız ×1 ({tr(CANLI[0], 1)}–{tr(CANLI[1], 1)} s)",
               "agir": f"4/6 · Olay — ağır çekim ×{tr(AGIR_HIZ, 1)} ({tr(AGIR[0], 1)}–{tr(AGIR[1], 1)} s)",
               "sonra": f"5/6 · Sonrası — gerçek hız ×1 ({tr(SONRA[0], 1)}–{tr(SONRA[1], 1)} s)"}[bolum]
        yz.append((1896, 18, bas, 22, SARI if bolum == "agir" else YAZI, dict(kalin=True, anchor="rt")))

        # tutum (doğrusal ara değer, açı sarmalama düzeltilmiş dizilerden)
        at = V["att_t"]
        i = min(max(son_i(at, t), 0), len(at) - 2)
        a = (t - at[i]) / (at[i + 1] - at[i])
        a = min(max(a, 0.0), 1.0) if at[i + 1] - at[i] < 0.5 else 0.0
        ic = lambda arr: float(arr[i] + a * (arr[i + 1] - arr[i]))
        roll, pitch, yaw = ic(V["att_uRoll"]), ic(V["att_uPitch"]), ic(V["att_uYaw"])
        ct = V["ctun_t"]
        j = min(max(son_i(ct, t), 0), len(ct) - 2)
        b = min(max((t - ct[j]) / (ct[j + 1] - ct[j]), 0.0), 1.0)
        agl = float(V["agl"][j] + b * (V["agl"][j + 1] - V["agl"][j]))
        ir = son_i(V["rcou_t"], t + ZAMAN_COZ)
        pw = {k: float(V[f"M{k}"][ir]) for k in (1, 2, 3, 4)}
        if bolum == "agir":
            rs, rboy, rh, rrenk, ryazi = f"AĞIR ÇEKİM ×{tr(AGIR_HIZ, 1)}", 44, 64, (190, 36, 44), (255, 255, 255)
        else:
            rs, rboy, rh, rrenk, ryazi = "GERÇEK HIZ ×1", 22, 36, (44, 52, 68), YAZI
        rbw = self.genislik(rs, rboy, True) + (32 if bolum == "agir" else 24)
        self.drone_ciz(img, roll, pitch, yaw - self.yaw_ref, max(agl, 0.0), pw, yz,
                       rozet=(14 + rbw, 14 + rh), alt_rezerv=R3_ALT_REZERV)
        cv2.rectangle(img, (R3[0] + 14, R3[1] + 14), (int(R3[0] + 14 + rbw), R3[1] + 14 + rh), rrenk, -1)
        self.kayit_kutu((R3[0] + 14, R3[1] + 14, R3[0] + 14 + rbw, R3[1] + 14 + rh), "hız rozeti")
        yz.append((R3[0] + 14 + rbw / 2, R3[1] + 14 + rh / 2, rs, rboy, ryazi, dict(kalin=True, anchor="mm", sinir=R3, serbest=True)))
        ia = son_i(at, t + ZAMAN_COZ)
        yz.append((R3[0] + 14, R3[3] - 34,
                   f"ATT örneği {tr(at[ia], 2)} s: roll {tr(V['att_Roll'][ia], 1, True)}° · pitch {tr(V['att_Pitch'][ia], 1, True)}° · "
                   f"yaw {tr(V['att_Yaw'][ia], 1)}° (istenen {tr(V['att_DesYaw'][ia], 1)}°)", 18, YAZI,
                   dict(sinir=R3, maxw=R3[2] - R3[0] - 28)))

        # motor çubukları
        for n, k in enumerate((1, 2, 3, 4)):
            yc = MB_Y[n]
            if pw[k] > 1000:
                cv2.rectangle(img, (MB_X0 + 1, yc - 8), (int(self.mb_x(pw[k])), yc + 8), self.pwm_renk(pw[k]), -1)
            yz.append((MB_X1 + 8, yc, f"{pw[k]:.0f}", 18, YAZI, dict(kalin=True, anchor="lm", sinir=RUST)))
        for pwm in (self.taban, self.tavan):
            x = self.mb_x(pwm)
            kesikli(img, (x, MB_Y[0] - 14), (x, MB_Y[-1] + 14), (200, 205, 216), 1, 4, 3)
        # CCW−CW
        fk, f1 = float(V["fark"][ir]), float(V["fark1s"][ir])
        renk = KIRMIZI if abs(f1) > 60 else YESIL
        x0, x1 = sorted((self.fx(0), self.fx(f1)))
        cv2.rectangle(img, (int(x0), 131), (int(max(x1, x0 + 1)), 145), renk, -1)
        xa = self.fx(fk)
        dolu(img, [(xa, 128), (xa - 6, 121), (xa + 6, 121)], (240, 240, 240))
        for deger in (f1, fk):
            if deger > 700:
                dolu(img, [(GX1 - 1, 138), (GX1 - 9, 131), (GX1 - 9, 145)], (255, 255, 255))
            if deger < -300:
                dolu(img, [(GX0 + 1, 138), (GX0 + 9, 131), (GX0 + 9, 145)], (255, 255, 255))
        yz.append((GX_T, 97, f"1 s ort. {tr(f1, 0, True)} µs", 20, renk, dict(kalin=True, sinir=RUST)))
        yz.append((GX1, 98, f"anlık {tr(fk, 0, True)} µs (▼)", 18, (220, 224, 232), dict(anchor="rt", sinir=RUST)))
        # yaw hatası (nötr renk)
        yh = float(V["att_yawhata"][ia])
        x0, x1 = sorted((self.yx(0), self.yx(yh)))
        cv2.rectangle(img, (int(x0), 205), (int(max(x1, x0 + 1)), 217), NOTR, -1)
        if yh > 45:
            dolu(img, [(GX1 - 1, 211), (GX1 - 9, 204), (GX1 - 9, 218)], (255, 255, 255))
        if yh < -45:
            dolu(img, [(GX0 + 1, 211), (GX0 + 9, 204), (GX0 + 9, 218)], (255, 255, 255))
        yz.append((GX1, 179, f"{tr(yh, 1, True)}°", 20, NOTR, dict(kalin=True, anchor="rt", sinir=RUST)))

        # grafik imleci
        if PX0 <= xc <= PX1:
            for (y0, y1) in PLOT_Y.values():
                cv2.line(img, (int(round(xc)), y0 - 2), (int(round(xc)), y1 + 2), (255, 255, 255), 2)
                self.kayit_cizgi((round(xc), y0 - 2), (round(xc), y1 + 2), "grafik imleci")

        self._hud(img, t, yz, agl)
        self._serit_dinamik(img, t, gor, yz)
        img = self.pil_yaz(img, yz)
        self.son_denetim = self.kayit_denetle()
        return img

    def _hud(self, img, t, yz, agl):
        V, E = self.V, self.E
        va, vb = HUD_A_DEGER, HUD_B_DEGER
        mwa, mwb = HUD_B_ETIKET - 12 - va, CUBUK_KUTU[0][0] - 8 - vb
        yz.append((va, HUD_Y[0], f"{tr(t, 3)} s", 22, YAZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwa)))
        yz.append((va, HUD_Y[1], log_saat(V, t, 2), 20, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwa)))
        t = t + ZAMAN_COZ
        mo = [m for tt, m in V["mode"] if tt <= t]
        mo = mo[-1] if mo else None
        yz.append((va, HUD_Y[2], f"{MOD_AD.get(mo, 'mod')} ({mo})", 20, SARI if mo == 9 else YAZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwa)))
        if t >= E["pervane"]:
            yz.append((va, HUD_Y[3], f"{tr(agl, 2, True)} m (güvenilmez)", 18, TURUNCU, dict(anchor="lm", sinir=RALT, maxw=mwa)))
        else:
            yz.append((va, HUD_Y[3], f"{tr(agl, 2, True)} m (yerden)", 20, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwa)))
        ib = son_i(V["bat_t"], t)
        yz.append((va, HUD_Y[4], f"{tr(V['volt'][ib], 2)} V · {tr(V['akim'][ib], 1)} A", 20, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwa)))
        gt = V["gps_t"]
        ig = son_i(gt, t)
        if t >= E["gps0"]:
            yz.append((vb, HUD_Y[0], f"{int(V['gps_NSats'][ig])} uydu · durum {int(V['gps_Status'][ig])}", 18, KIRMIZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwb)))
        elif t > E["gps_son"] + E["gps_max_dt"]:
            yz.append((vb, HUD_Y[0], f"VERİ YOK (son {tr(E['gps_son'], 2)} s)", 18, KIRMIZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwb)))
        else:
            st = int(V["gps_Status"][ig])
            yz.append((vb, HUD_Y[0], f"{int(V['gps_NSats'][ig])} uydu · {GPS_DURUM.get(st, '?')} ({st})", 18, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        if t >= E["kopma_bitis"]:
            yz.append((vb, HUD_Y[1], f"DONDU (son {tr(E['kopma'], 2)} s)", 18, KIRMIZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwb)))
        else:
            yz.append((vb, HUD_Y[1], "güncelleniyor", 18, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        # telemetri: son paketten sonra, sıradaki beklenen paket gelene dek nötr; ancak o an geçince KOPTU
        if t > E["telemetri_kesik"]:
            yz.append((vb, HUD_Y[2], f"KOPTU (son {tr(E['telemetri'], 2)} s)", 18, KIRMIZI, dict(kalin=True, anchor="lm", sinir=RALT, maxw=mwb)))
        elif t > E["telemetri"]:
            yz.append((vb, HUD_Y[2], f"son {tr(E['telemetri'], 2)} s · bekleniyor", 18, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        else:
            yz.append((vb, HUD_Y[2], "alınıyor", 18, YESIL, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        iv = son_i(V["vibe0_t"], t)
        yz.append((vb, HUD_Y[3], f"VibeZ {tr(V['vibe0_VibeZ'][iv], 1)} · Clip {V['vibe0_Clip'][iv]:.0f}", 18,
                   KIRMIZI if V["vibe0_VibeZ"][iv] > 30 else YAZI, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        ir = son_i(V["rcin_t"], t)
        C = {c: float(V[f"C{c}"][ir]) for c in range(1, 7)}
        yz.append((vb, HUD_Y[4], f"CH5 {C[5]:.0f} · CH6 {C[6]:.0f}", 18, YAZI, dict(anchor="lm", sinir=RALT, maxw=mwb)))
        P = V["P"]

        def nrm(c, val):
            tr_, mn, mx = P[f"RC{c}_TRIM"], P[f"RC{c}_MIN"], P[f"RC{c}_MAX"]
            return (val - tr_) / (mx - tr_) if val >= tr_ else (val - tr_) / (tr_ - mn)

        gaz = (C[3] - P["RC3_MIN"]) / (P["RC3_MAX"] - P["RC3_MIN"])
        cm = (CUBUK_Y0 + CUBUK_Y1) / 2
        for (bx, _), xn, yn, s1, s2 in ((CUBUK_KUTU[0], nrm(4, C[4]), 1 - 2 * gaz, f"C3 {C[3]:.0f}", f"C4 {C[4]:.0f}"),
                                        (CUBUK_KUTU[1], nrm(1, C[1]), nrm(2, C[2]), f"C2 {C[2]:.0f}", f"C1 {C[1]:.0f}")):
            px = bx + 52 + max(min(xn, 1), -1) * 46
            py = cm + max(min(yn, 1), -1) * 28
            cv2.line(img, (bx + 52, int(cm)), (int(px), int(py)), (120, 130, 150), 1, cv2.LINE_AA)
            cv2.circle(img, (int(px), int(py)), 6, SARI, -1, cv2.LINE_AA)
            yz.append((bx + 52, CUBUK_Y1 + 4, s1, 18, SOLUK, dict(anchor="mt", sinir=RALT, maxw=110)))
            yz.append((bx + 52, CUBUK_Y1 + 26, s2, 18, SOLUK, dict(anchor="mt", sinir=RALT, maxw=110)))

    def _serit_dinamik(self, img, t, gor, yz):
        t0, t1 = EKSEN_TAM if gor == "tam" else EKSEN_YAKIN
        xx = TX0 + (t - t0) / (t1 - t0) * (TX1 - TX0)
        if TX0 - 1 <= xx <= TX1 + 1:
            y_ust = EKSEN_Y - 16
            cv2.line(img, (int(xx), y_ust), (int(xx), EKSEN_Y + 6), (255, 255, 255), 2)
            dolu(img, [(xx, EKSEN_Y - 1), (xx - 7, y_ust), (xx + 7, y_ust)], (255, 255, 255))
            self.kayit_kutu((xx - 7, y_ust, xx + 7, EKSEN_Y + 6), "şerit imleci")
        gecmis = [o for o in self.olaylar if o["t"] <= t + ZAMAN_COZ]
        if not gecmis:
            return
        son = gecmis[-1]
        cv2.rectangle(img, (40, 922), (52, 950), son["renk"], -1)
        yz.append((64, 918, son["baslik"], 32, YAZI, dict(kalin=True, sinir=SERIT, maxw=1810)))
        satirlar = self.sar(son["detay"], 20, False, 1810)
        if len(satirlar) > 2:
            self.uyarilar.add(f"AÇIKLAMA 2 SATIRA SIĞMADI: '{son['detay'][:40]}'")
            satirlar = [satirlar[0], " ".join(satirlar[1:])]
        y = 962
        for s in satirlar:
            yz.append((64, y, s, 20, (205, 212, 224), dict(sinir=SERIT, maxw=1810)))
            y += 26
        y += 4
        for o in reversed(gecmis[:-1]):
            if y + 22 > SERIT[3] - 4:
                break
            cv2.rectangle(img, (44, y + 4), (52, y + 18), o["renk"], -1)
            yz.append((64, y, f"{tr(o['t'], 2)} s — {o['baslik']}", 18, SOLUK, dict(sinir=SERIT, maxw=1810)))
            y += 25

    # --- kartlar
    def kart_baslik(self):
        V, E = self.V, self.E
        self.kayit_sifirla()
        img = np.full((H, W, 3), ZEMIN, np.uint8)
        cv2.rectangle(img, (0, 470), (W, 474), (190, 36, 44), -1)
        yz = [(W / 2, 330, f"NAVITAS — {self.tarih_baslik()} düşüşü", 76, YAZI, dict(kalin=True, anchor="mm", maxw=1800)),
              (W / 2, 420, "Log canlandırması — veriler Pixhawk logundan; 3B çizim temsili", 40, (210, 216, 228), dict(anchor="mm", maxw=1800)),
              (W / 2, 560, f"Log: {os.path.basename(BIN)} · {V['fw']} · {V['kart']}", 26, SOLUK, dict(anchor="mm", maxw=1800)),
              (W / 2, 606, f"Telemetri: Mission Planner tlog {os.path.basename(TLOG)}", 26, SOLUK, dict(anchor="mm", maxw=1800)),
              (W / 2, 652, "Sayılar Türkçe ondalık virgülle · ÖLÇÜM ile (çıkarım)/(beyan) ayrı etiketlenir", 24, SOLUK, dict(anchor="mm", maxw=1800))]
        return self.pil_yaz(img, yz)

    def kart_ozet(self):
        V, E = self.V, self.E
        self.kayit_sifirla()
        img = np.full((H, W, 3), ZEMIN, np.uint8)
        yz = [(80, 30, "2/6 · Oturum özeti — tüm arm pencereleri", 42, YAZI, dict(kalin=True)),
              (80, 86, f"Log {os.path.basename(BIN)} · üst sıra: log zamanı (s) · alt sıra: yerel saat · "
                       f"bu videonun konusu W6", 22, SOLUK, dict(maxw=1760))]
        at = V["att_t"]
        a0 = math.floor(at[0] / 10) * 10
        a1 = math.ceil(at[-1] / 10) * 10
        AX0, AX1 = 130, 1840
        X = lambda t: AX0 + (t - a0) / (a1 - a0) * (AX1 - AX0)
        renkler = [TURUNCU, (255, 120, 110), (130, 138, 156), (130, 138, 156), MAVI, KIRMIZI]
        cv2.rectangle(img, (AX0, 156), (AX1, 192), PANEL, -1)
        pen = E["pencereler"]
        for n, p in enumerate(pen):
            cv2.rectangle(img, (int(X(p["bas"])), 156), (int(max(X(p["son"]), X(p["bas"]) + 2)), 192), renkler[n], -1)
            yz.append(((X(p["bas"]) + X(p["son"])) / 2, 128, f"W{n + 1}", 20, renkler[n], dict(kalin=True, anchor="mt")))
        for tv in range(int(a0), int(a1) + 1, 10):
            cv2.line(img, (int(X(tv)), 192), (int(X(tv)), 198 if tv % 20 else 202), SOLUK, 1)
            if tv % 20 == 0:
                yz.append((X(tv), 206, f"{tv}", 18, SOLUK, dict(anchor="mt")))
            if tv % 40 == 0:
                yz.append((X(tv), 230, log_saat(V, tv, 0), 18, (135, 144, 162), dict(anchor="mt")))
        # VibeZ grafiği
        GY0, GY1 = 300, 640
        yz.append((AX0, 264, "VibeZ — IMU0 titreşimi (m/s²), tüm oturum", 20, YAZI, dict(kalin=True)))
        cv2.rectangle(img, (AX0, GY0), (AX1, GY1), (16, 20, 28), -1)
        cv2.rectangle(img, (AX0, GY0), (AX1, GY1), CERCEVE, 1)
        self.kayit_kutu((AX0, GY0, AX1, GY1), "VibeZ grafiği")
        Y = lambda val: GY1 - val / 100.0 * (GY1 - GY0)
        for n, p in enumerate(pen):
            alfa_kutu(img, X(p["bas"]), GY0 + 1, max(X(p["son"]), X(p["bas"]) + 2), GY1 - 1, renkler[n], 0.10)
        for val in (0, 20, 40, 60, 80, 100):
            if 0 < val < 100:
                kesikli(img, (AX0, Y(val)), (AX1, Y(val)), (50, 56, 70), 1, 3, 5)
            yz.append((AX0 - 8, Y(val), str(val), 18, SOLUK, dict(anchor="rm")))
        vt, vz = V["vibe0_t"], V["vibe0_VibeZ"]
        kes = np.where(np.diff(vt) > 1.0)[0]
        for seg in np.split(np.arange(len(vt)), kes + 1):
            if len(seg) > 1:
                cizgi(img, np.stack([X(vt[seg]), Y(np.minimum(vz[seg], 100))], 1), TURUNCU, 2)
        kesikli(img, (AX0, Y(16)), (AX1, Y(16)), SARI, 1, 8, 6)
        # eşik yazısı: W2 bitişi ile W3 başı arasındaki boşluğa (veri yokken)
        s16 = "kabul eşiği VibeZ ≤16 (§7)"
        x16 = X(pen[1]["son"]) + 14
        if x16 + self.genislik(s16, 18) > X(pen[2]["bas"]) - 8:
            self.uyarilar.add("özet: eşik yazısı W2–W3 boşluğuna sığmadı")
        yz.append((x16, Y(16) - 6, s16, 18, SARI, dict(anchor="ls", serbest=True)))
        isaretler = [(pen[1]["a_max_t"], f"W2 sert iniş {tr(pen[1]['a_max_t'], 2)} s · |a| {tr(pen[1]['a_max'], 1)} m/s²", (255, 120, 110)),
                     (E["baslangic"], f"W6 başlangıç {tr(E['baslangic'], 2)} s", KIRMIZI)]
        for n, (tv, s, renk) in enumerate(isaretler):
            cv2.line(img, (int(X(tv)), GY0 + 2), (int(X(tv)), GY1 - 2), renk, 1)
            self.kayit_cizgi((int(X(tv)), GY0 + 2), (int(X(tv)), GY1 - 2), s)
            yz.append((X(tv) - 6, GY0 + 10 + n * 28, s, 18, renk, dict(kalin=True, anchor="rt", serbest=True)))
        # tablo
        ty = 664
        for n, p in enumerate(pen):
            y = ty + n * 64
            cv2.rectangle(img, (80, y + 10), (104, y + 42), renkler[n], -1)
            yz.append((120, y + 6, f"W{n + 1}", 26, renkler[n], dict(kalin=True)))
            yz.append((200, y + 6, f"{tr(p['bas'], 1)}–{tr(p['son'], 1)} s", 22, YAZI, dict()))
            yz.append((200, y + 36, f"{log_saat(V, p['bas'], 0)}–{log_saat(V, p['son'], 0)}", 18, SOLUK, dict()))
            modlar = " → ".join(f"{MOD_AD.get(mo, mo)}" for _, mo in p["modlar"])
            if n == 0:
                d1 = f"Yerde yatma — roll en çok {tr(p['roll_max'], 1, True)}° (sağ taraf aşağı), {tr(p['roll_max_t'], 2)} s"
                d2 = f"Modlar: {modlar} · başlangıç zamanı: {p['bas_kaynak']}"
            elif n == 1:
                d1 = f"Kısa sıçrama, sert iniş {tr(p['a_max_t'], 2)} s — |a| {tr(p['a_max'], 1)} m/s²"
                d2 = f"Clip IMU0 {p['clip_once_amax']:.0f} → {p['clip_sonra_amax']:.0f} · kalkış (EV 28) {tr(p['kalkis'][0], 2)} s" if p["kalkis"] else ""
            elif n in (2, 3):
                d1 = "Kısa arm — kalkış yok" + (" (EV 28 kaydı yok)" if not p["kalkis"] else "")
                d2 = f"Modlar: {modlar} · roll en çok {tr(p['roll_max'], 1, True)}°"
            elif n == 4:
                d1 = f"Kısa askı — kalkış {tr(p['kalkis'][0], 2)} s, LAND {tr(p['land'], 2)} s" if p["kalkis"] else "Kısa askı"
                d2 = f"VibeZ ortalaması askıda {tr(p['vibez_ort'], 1)} (eşik 16)"
            else:
                d1 = f"Son uçuş — kalkış {tr(E['kalkis'], 2)} s, düşüş başlangıcı {tr(E['baslangic'], 2)} s, çarpma {tr(E['carpma'], 2)} s"
                d2 = "Sonraki bölümlerde gerçek hız ve ağır çekimle gösteriliyor"
            yz.append((470, y + 6, d1, 22, YAZI, dict(kalin=True, maxw=1370)))
            if d2:
                yz.append((470, y + 36, d2, 18, SOLUK, dict(maxw=1370)))
        return self.pil_yaz(img, yz)

    def kart_sonuc(self):
        V, E = self.V, self.E
        self.kayit_sifirla()
        img = np.full((H, W, 3), ZEMIN, np.uint8)
        yz = [(80, 36, "6/6 · Sonuç", 52, YAZI, dict(kalin=True)),
              (80, 104, "Kaynak: DUSUS_ANALIZI.md §2 ve §8 · tarih/saat ve sayılar bu logdan yeniden hesaplandı", 22, SOLUK, dict(maxw=1760))]
        t2 = lambda x: tr(x, 2)
        gaz = ", ".join(f"{t2(g['bas'])}–{t2(g['son'])} s" for g in E["gaz_ust"])
        gaz_s = (f"gaz yalnız {gaz} bandın hafif üstünde (yavaş tırmanış)" if E["gaz_ust"] else "gaz ölü bantta")
        maddeler = [
            f"Başlatıcı: uçuşta yapısal çöküş — gövde/kol {t2(E['baslangic'])} s'de katlandı, ön-sağ köşe itkisini kaybetti "
            f"(çıkarım + kullanıcı beyanı; güven orta–yüksek)",
            f"Öncül: ~{E['baslangic'] - E['basamak1']:.0f} s boyunca motor dengesizliği büyüdü — CCW−CW (1 s ort.) "
            f"{tr(E['fark_ilk1s'], 0, True)} → {tr(E['fark_son1s'], 0, True)} µs; roll/pitch/yaw çubukları {t2(E['cubuk_cikis'])} s'ye dek ortada; "
            f"{gaz_s} (ölçüm)",
            f"Havada veri kesilmesi: telemetri son paketi {t2(E['telemetri'])} s, GPS son örneği {t2(E['gps_son'])} s, "
            f"harici pusula son güncellemesi {t2(E['kopma'])} s — hepsi çarpmadan ({t2(E['carpma'])} s) önce (ölçüm)",
            f"Ters dönüş {t2(E['ters'])} s (roll {tr(E['ters_roll'], 0)}°) → yere çarpma {t2(E['carpma'])} s → "
            f"CH6 disarm {t2(E['disarm'])} s (ölçüm)",
            "Dış temas izi yok; elektrik, sensör ve ayar kaynaklı başlatıcı bulunmadı (DUSUS_ANALIZI §3 + kullanıcı beyanı)",
        ]
        y = 160
        for n, m in enumerate(maddeler, 1):
            satirlar = self.sar(m, 30, False, 1690)
            cv2.circle(img, (104, y + 18), 8, SARI, -1, cv2.LINE_AA)
            for s in satirlar:
                yz.append((130, y, s, 30, YAZI, dict(maxw=1720)))
                y += 42
            y += 14
        y = y + 26
        cv2.rectangle(img, (80, y), (1840, y + 92), (58, 44, 18), -1)
        cv2.rectangle(img, (80, y), (1840, y + 92), SARI, 2)
        yz.append((110, y + 12, "Katkı payları", 22, SARI, dict(kalin=True)))
        yz.append((110, y + 44, "Gövde/tasarım %70–85 · Pilotaj+operasyon %10–25 (değerlendirme, ölçüm değil)", 32, YAZI, dict(kalin=True, maxw=1700)))
        y2 = y + 108
        s = "düşüş yaşamış baskı parça değişir; ilk kısa askıdan sonra log kontrolü (VibeZ ≤16, motor farkı ≤60 µs)"
        sat_l = self.sar(s, 28, True, 1700)
        yuk = 44 + 38 * len(sat_l) + 10
        cv2.rectangle(img, (80, y2), (1840, y2 + yuk), (18, 50, 32), -1)
        cv2.rectangle(img, (80, y2), (1840, y2 + yuk), YESIL, 2)
        yz.append((110, y2 + 12, "Bundan sonra", 22, YESIL, dict(kalin=True)))
        for n, sat in enumerate(sat_l):
            yz.append((110, y2 + 44 + n * 38, sat, 28, YAZI, dict(kalin=True, maxw=1700)))
        if y2 + yuk > H - 8:
            self.uyarilar.add(f"sonuç kartı taşıyor: {y2 + yuk}")
        return self.pil_yaz(img, yz)

    def kart(self, ad):
        if ad not in self._onbellek:
            self._onbellek[ad] = {"baslik": self.kart_baslik, "ozet": self.kart_ozet, "sonuc": self.kart_sonuc}[ad]()
            self.kart_denetim[ad] = self.kayit_denetle()
        return self._onbellek[ad]

    def kare(self, oge):
        bolum, i, n, t = oge
        if bolum in ("baslik", "ozet", "sonuc"):
            img = self.kart(bolum)
            self.son_denetim = self.kart_denetim[bolum]
            f = 1.0
            if i < 10:
                f = (i + 1) / 10.0
            if bolum == "sonuc" and i >= n - 15:
                f = min(f, (n - i) / 15.0)
            return img if f >= 1.0 else (img.astype(np.float32) * f).astype(np.uint8)
        return self.veri_karesi(t, bolum)


# ----------------------------------------------------------------------------
# İşaret testi
# ----------------------------------------------------------------------------
def isaret_testi(V=None, E=None):
    os.makedirs(KARELER, exist_ok=True)
    cz = Cizer(V, E if E is not None else {"yaw_ref": 0.0}, yaw_ref=0.0)
    cz.olaylar = []
    testler = [("test_roll+30.png", 30.0, 0.0, 0.0), ("test_pitch-30.png", 0.0, -30.0, 0.0), ("test_yaw+45.png", 0.0, 0.0, 45.0)]
    SAG = (936, 68, 1904, 1072)
    ALT = (16, 768, 920, 1072)
    EK = (952, 540, 1888, 1056)
    h = 0.5
    sonuc = []
    denetim = {}
    for dosya, r, p, y in testler:
        cz.kayit_sifirla()
        img = np.full((H, W, 3), ZEMIN, np.uint8)
        cv2.rectangle(img, (0, 0), (W, UST_H), (16, 20, 28), -1)
        for pnl in (R3, SAG, ALT):
            cz.panel(img, pnl)
        yz = [(24, 15, f"İşaret testi — roll {tr(r, 0, True)}°, pitch {tr(p, 0, True)}°, yaw {tr(y, 0, True)}°", 28, YAZI, dict(kalin=True))]
        cz.zemin_ciz(img, cz.kam, R3, yz, "Zemindeki gri ok: yaw 0° referans yönü")
        pw = {k: 1550.0 for k in (1, 2, 3, 4)}
        _, mot0, _ = cz.govde_dunya(0, 0, 0, h)
        R, mot, burun = cz.govde_dunya(r, p, y, h)
        kam = cz.kam
        ekr = lambda P3: kam.izdus(np.asarray(P3, float)[None])[0][0]
        z = {k: mot[k][2] for k in mot}
        PW, PH = R3[2] - R3[0], R3[3] - R3[1]

        # çağrı kutuları (AŞAĞI/YUKARI): önce konum ve çizgi hesaplanır, 3B etiketler bunlardan kaçar
        cagri = []
        if r != 0:
            cagri = [("AŞAĞI (sağ taraf)", (190, 36, 44), ekr((mot[1] + mot[4]) / 2), "sağ-alt"),
                     ("YUKARI (sol taraf)", (30, 120, 60), ekr((mot[2] + mot[3]) / 2), "sol-üst")]
        elif p != 0:
            cagri = [("BURUN AŞAĞI", (190, 36, 44), ekr((mot[1] + mot[3]) / 2), "sağ-alt"),
                     ("KUYRUK YUKARI", (30, 120, 60), ekr((mot[2] + mot[4]) / 2), "sol-üst")]
        on_metin = "ÖN" if (r != 0 or p != 0) else f"ÖN = BURUN (yaw {tr(y, 0, True)}°)"
        engel = {"kutular": [], "cizgiler": []}
        cizilecek = []
        for metin, renk, hedef, yer in cagri:
            bw, bh = cz.genislik(metin, 22, True) + 22, 38
            x0, y0 = (30, 24) if yer == "sol-üst" else (PW - bw - 30, PH - R3_ALT_REZERV - bh - 18)
            qx, qy = min(max(hedef[0], x0), x0 + bw), min(max(hedef[1], y0), y0 + bh)
            kutu = (R3[0] + x0, R3[1] + y0, R3[0] + x0 + bw, R3[1] + y0 + bh)
            cz_ = ((R3[0] + qx, R3[1] + qy), (R3[0] + hedef[0], R3[1] + hedef[1]))
            engel["kutular"].append(kutu)
            engel["cizgiler"].append(cz_)
            cizilecek.append((metin, renk, kutu, cz_))
        bilgi = cz.drone_ciz(img, r, p, y, h, pw, yz, engeller=engel, alt_rezerv=R3_ALT_REZERV, on_metin=on_metin)
        for metin, renk, kutu, cz_ in cizilecek:
            cv2.line(img, tuple(int(round(q)) for q in cz_[0]), tuple(int(round(q)) for q in cz_[1]), renk, 2, cv2.LINE_AA)
            cz.kayit_cizgi(cz_[0], cz_[1], metin)
        for metin, renk, kutu, cz_ in cizilecek:
            cv2.rectangle(img, (int(kutu[0]), int(kutu[1])), (int(kutu[2]), int(kutu[3])), renk, -1)
            cz.kayit_kutu(kutu, metin, "etiket")
            yz.append(((kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2, metin, 22, (255, 255, 255),
                       dict(kalin=True, anchor="mm", sinir=R3, serbest=True)))

        satirlar = ["ArduPilot gövde FRD işaretleri:", "  Roll + = sağ taraf aşağı", "  Pitch + = burun yukarı",
                    "  Yaw + = yukarıdan bakınca saat yönü", ""]
        dy_ekran = lambda ks: float(np.mean([ekr(mot[k])[1] - ekr(mot0[k])[1] for k in ks]))
        if r != 0:
            sag, sol = (z[1] + z[4]) / 2, (z[2] + z[3]) / 2
            hukum = "SAĞ TARAF AŞAĞI" if sag < sol else "SOL TARAF AŞAĞI"
            satirlar += [f"Sağ motorlar (M1, M4) ort. yükseklik: {tr(sag, 3)} m",
                         f"Sol motorlar (M2, M3) ort. yükseklik: {tr(sol, 3)} m",
                         f"Hüküm (dünya geometrisinden): {hukum}",
                         f"Ekranda sağ motorlar {tr(dy_ekran((1, 4)), 0, True)} px, sol {tr(dy_ekran((2, 3)), 0, True)} px kaydı (+ = aşağı)"]
            dogru = (sag < sol) == (r > 0)
        elif p != 0:
            on, arka = (z[1] + z[3]) / 2, (z[2] + z[4]) / 2
            hukum = "BURUN AŞAĞI" if on < arka else "BURUN YUKARI"
            satirlar += [f"Ön motorlar (M1, M3) ort. yükseklik: {tr(on, 3)} m",
                         f"Arka motorlar (M2, M4) ort. yükseklik: {tr(arka, 3)} m",
                         f"Hüküm (dünya geometrisinden): {hukum}",
                         f"Ekranda ön motorlar {tr(dy_ekran((1, 3)), 0, True)} px, arka {tr(dy_ekran((2, 4)), 0, True)} px kaydı (+ = aşağı)"]
            dogru = (on > arka) == (p > 0)
        else:
            yon = math.degrees(math.atan2(burun[0], burun[1]))  # sağa (x) doğru + → yukarıdan saat yönü
            hukum = "SAAT YÖNÜ (yukarıdan)" if yon > 0 else "SAAT YÖNÜNÜN TERSİ"
            satirlar += [f"Burun vektörü (sağ, ileri) = ({tr(burun[0], 3)}; {tr(burun[1], 3)})",
                         f"Referanstan dönüş açısı: {tr(yon, 1, True)}° (+ = ileriden sağa)",
                         f"Hüküm (dünya geometrisinden): {hukum}"]
            dogru = yon > 0
        satirlar += ["", f"Beklenen ile uyum: {'EVET' if dogru else 'HAYIR'}"]
        paragraf = ("Bu kare, videodaki 3B çizimin aynı fonksiyonu (Cizer.drone_ciz), aynı sabit kamera ve aynı dönüşüm "
                    "(ArduPilot 321 Euler, gövde FRD) ile çizildi; yalnız yaw referansı 0°. "
                    f"Yükseklik {tr(h, 2)} m, motor komutları eşit (renk nötr). AŞAĞI/YUKARI/BURUN hükmü girilen açıdan değil, "
                    "çizilen noktaların dünya koordinatlarından hesaplandı. Sağ alttaki ek görünüş aynı fonksiyonla, ikinci bir "
                    "sabit kameradan çizildi.")
        for n, s in enumerate(cz.sar(paragraf, 18, False, ALT[2] - ALT[0] - 44)):
            yz.append((ALT[0] + 20, ALT[1] + 18 + n * 30, s, 18, YAZI if n == 0 else SOLUK, dict(sinir=ALT)))
        for n, s in enumerate(satirlar):
            renk = (YESIL if dogru else KIRMIZI) if s.startswith("Beklenen") else (SARI if s.startswith("Hüküm") else YAZI)
            yz.append((952, 82 + n * 34, s, 22, renk, dict(kalin=s.startswith(("Hüküm", "Beklenen", "ArduPilot")), maxw=930, sinir=SAG)))

        # ek görünüş: aynı çizim fonksiyonu, ikinci kamera
        IW, IH = EK[2] - EK[0], EK[3] - EK[1]
        cv2.rectangle(img, (EK[0], EK[1]), (EK[2], EK[3]), (16, 20, 28), -1)
        cv2.rectangle(img, (EK[0], EK[1]), (EK[2], EK[3]), CERCEVE, 1)
        cz.kayit_kutu(EK, "ek görünüş")
        if r != 0:
            az2, el2, b2 = 0.0, 6.0, "Ek görünüş — arkadan (sağ taraf ekranda sağda)"
        elif p != 0:
            az2, el2, b2 = 90.0, 6.0, "Ek görünüş — sağdan (burun ekranda sağda)"
        else:
            az2, el2, b2 = 0.0, 84.0, "Ek görünüş — yukarıdan (yaw 0° ekranda yukarı)"
        kam2 = Kamera((0, 0, h), az2, el2, 1.6, 900.0, (IW * 0.5, IH * 0.54))
        yz.append((EK[0], EK[1] - 12, b2, 20, SOLUK, dict(anchor="ls", sinir=SAG)))
        cz.zemin_ciz(img, kam2, EK, n=4, ok_ciz=False)
        cz.drone_ciz(img, r, p, y, h, pw, yz, etiket=False, kam=kam2, bolge=EK)
        e2 = lambda P3: kam2.izdus(np.asarray(P3, float)[None])[0][0] + np.array([EK[0], EK[1]], float)
        m0 = np.array([0.0, 0.0, h])
        if r != 0 or p != 0:
            if r != 0:
                eks, ad_a, ad_b = np.array([1.0, 0, 0]), "sağ taraf", "sol taraf"
                zA, zB, PA, PB = (z[1] + z[4]) / 2, (z[2] + z[3]) / 2, (mot[1] + mot[4]) / 2, (mot[2] + mot[3]) / 2
            else:
                eks, ad_a, ad_b = np.array([0, 1.0, 0]), "burun", "kuyruk"
                zA, zB, PA, PB = (z[1] + z[3]) / 2, (z[2] + z[4]) / 2, (mot[1] + mot[3]) / 2, (mot[2] + mot[4]) / 2
            r0, r1 = e2(m0 - 0.36 * eks), e2(m0 + 0.36 * eks)
            kesikli(img, r0, r1, (150, 158, 176), 1, 8, 6)
            cz.kayit_cizgi(r0, r1, "yatay referans")
            yz.append((r0[0], r0[1] + 10, "yatay referans", 16, SOLUK, dict(anchor="lt", sinir=EK, yardimci=True, serbest=True)))
            pa, pb = e2(PA), e2(PB)
            yz.append((r1[0] + 12, pa[1], f"{ad_a} ({'aşağıda' if zA < zB else 'yukarıda'})", 20, YAZI,
                       dict(kalin=True, anchor="lm", sinir=EK, serbest=True)))
            yz.append((r0[0] - 12, pb[1], f"{ad_b} ({'aşağıda' if zB < zA else 'yukarıda'})", 20, YAZI,
                       dict(kalin=True, anchor="rm", sinir=EK, serbest=True)))
        else:
            c0, ref = e2(m0), e2(m0 + [0, 0.40, 0])
            bu = e2(m0 + np.array([burun[0], burun[1], 0.0]) / max(np.hypot(burun[0], burun[1]), 1e-9) * 0.40)
            cizgi(img, [c0, ref], (150, 158, 176), 2)
            cz.kayit_cizgi(c0, ref, "yaw 0° çizgisi")
            cizgi(img, [c0, bu], (255, 110, 110), 3)
            cz.kayit_cizgi(c0, bu, "burun çizgisi")
            aci_son = math.atan2(burun[0], burun[1])
            arc = [e2(m0 + 0.33 * np.array([math.sin(a_), math.cos(a_), 0.0])) for a_ in np.linspace(0, aci_son, 20)]
            cizgi(img, arc, SARI, 2)
            for q0, q1 in zip(arc[:-1], arc[1:]):
                cz.kayit_cizgi(q0, q1, "saat yönü yayı")
            yz.append((ref[0], ref[1] - 8, "yaw 0°", 20, SOLUK, dict(anchor="ms", sinir=EK, serbest=True)))
            yz.append((bu[0] + 10, bu[1] - 10, f"burun (yaw {tr(y, 0, True)}°)", 20, (255, 130, 130), dict(kalin=True, anchor="ls", sinir=EK, serbest=True)))
            am_ = aci_son / 2
            ms = e2(m0 + 0.50 * np.array([math.sin(am_), math.cos(am_), 0.0]))
            yz.append((ms[0], ms[1], "saat yönü", 20, SARI, dict(kalin=True, anchor="mm", sinir=EK, serbest=True)))
        img = cz.pil_yaz(img, yz)
        denetim[dosya] = cz.kayit_denetle()
        Image.fromarray(img).save(os.path.join(KARELER, dosya))
        sonuc.append({"dosya": dosya, "roll": r, "pitch": p, "yaw": y, "hukum": hukum, "uyum": bool(dogru)})
        print(f"  {dosya}: {hukum} · beklenenle uyum={dogru} · denetim {json.dumps({k: v for k, v in denetim[dosya].items() if k != 'sorun'})}")
        for s in denetim[dosya]["sorun"]:
            print("     ", s)
    return sonuc, sorted(cz.uyarilar), denetim


# ----------------------------------------------------------------------------
# Paralel işleme
# ----------------------------------------------------------------------------
_CZ = None


def _isci_baslat(V, E):
    global _CZ
    _CZ = Cizer(V, E)


def _isci_kare(oge):
    img = _CZ.kare(oge)
    u = sorted(_CZ.uyarilar)
    _CZ.uyarilar.clear()
    return img.tobytes(), u, _CZ.son_denetim


def plan_kur():
    plan = []

    def ekle(bolum, n, t0=None, hiz=1.0):
        for i in range(n):
            plan.append((bolum, i, n, None if t0 is None else t0 + i * hiz / FPS))

    ekle("baslik", round(BASLIK_S * FPS))
    ekle("ozet", round(OZET_S * FPS))
    ekle("canli", round((CANLI[1] - CANLI[0]) * FPS), CANLI[0])
    ekle("agir", round((AGIR[1] - AGIR[0]) / AGIR_HIZ * FPS), AGIR[0], AGIR_HIZ)
    ekle("sonra", round((SONRA[1] - SONRA[0]) * FPS), SONRA[0])
    ekle("sonuc", round(SONUC_S * FPS))
    return plan


def ornek_indeksleri(plan):
    ornek = {}
    for bolum, dosya in (("baslik", "kare_00_baslik.png"), ("ozet", "kare_01_oturum_ozeti.png")):
        idx = [i for i, o in enumerate(plan) if o[0] == bolum]
        ornek[idx[len(idx) // 2]] = dosya
    for n, T in enumerate(ORNEK_T, 2):
        idx = [i for i, o in enumerate(plan) if o[3] is not None and abs(o[3] - T) < 1e-6]
        if not idx:
            raise SystemExit(f"örnek zamanı {T} bir kareye denk gelmiyor")
        ornek[idx[0]] = f"kare_{n:02d}_t{T:.2f}".replace(".", "_") + f"s_{plan[idx[0]][0]}.png"
    idx = [i for i, o in enumerate(plan) if o[0] == "sonuc"]
    ornek[idx[len(idx) // 2 - 20]] = f"kare_{len(ORNEK_T) + 2:02d}_sonuc.png"
    return ornek


def ffmpeg_kodlayici():
    out = subprocess.run([FFMPEG, "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    return "libx264" if " libx264 " in out else "mpeg4"


def ffprobe_olc(yol):
    out = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-count_frames",
                          "-show_entries", "stream=codec_name,profile,width,height,r_frame_rate,avg_frame_rate,pix_fmt,nb_read_frames:format=duration,size",
                          "-of", "json", yol], capture_output=True, text=True).stdout
    return json.loads(out)


def dogrula(ornek, toplam):
    """mp4'ten her örnek karenin kendisini ve komşularını (N−1, N+1) çözüp PNG ile karşılaştırır.
    Ölçüler: ortalama mutlak fark (0–255) ve büyük fark oranı (herhangi bir kanalda |fark| > 48 olan piksel %)."""
    idxs = sorted(ornek)
    istek = sorted({j for i in idxs for j in (i - 1, i, i + 1) if 0 <= j < toplam})
    secim = "+".join(f"eq(n\\,{i})" for i in istek)
    cmd = [FFMPEG, "-v", "error", "-i", MP4, "-vf", f"select={secim}", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    ham = subprocess.run(cmd, capture_output=True).stdout
    n = len(ham) // (W * H * 3)
    kareler = {j: np.frombuffer(ham[q * W * H * 3:(q + 1) * W * H * 3], np.uint8).reshape(H, W, 3).astype(np.int16)
               for q, j in enumerate(istek[:n])}
    sonuc = []
    for i in idxs:
        png = np.array(Image.open(os.path.join(KARELER, ornek[i])).convert("RGB")).astype(np.int16)
        olc = {}
        for d in (-1, 0, 1):
            if i + d in kareler:
                fk = np.abs(kareler[i + d] - png)
                olc[d] = (float(fk.mean()), float((fk.max(axis=2) > 48).mean() * 100))
        sonuc.append((ornek[i], i, olc))
    return sonuc, n


# ----------------------------------------------------------------------------
# OKUBENI
# ----------------------------------------------------------------------------
def okubeni_yaz(V, E, plan, ornek, kodlayici, probe, sure_s, uyarilar, test_sonuc, dog, komut, den, test_den):
    t2 = lambda x: tr(x, 2)
    bolumler = []
    i = 0
    while i < len(plan):
        b = plan[i][0]
        j = i
        while j < len(plan) and plan[j][0] == b:
            j += 1
        bolumler.append((b, i, j))
        i = j
    ad = {"baslik": "1 · Başlık kartı", "ozet": "2 · Oturum özeti", "canli": "3 · Son uçuş (gerçek hız)",
          "agir": "4 · Olay (ağır çekim ×0,1)", "sonra": "5 · Sonrası (gerçek hız)", "sonuc": "6 · Sonuç kartı"}
    P_ = V["P"]
    tl = V["tlog"]
    L = []
    L.append("# dusus_0253.mp4 — 17 Eylül 2026 02:53 düşüşü, log canlandırması (2. sürüm)\n")
    L.append("Bu klasördeki her şey `log_video.py` ile üretilir; elle düzenlenmiş kare ya da elle girilmiş log sayısı yoktur. "
             "Bu dosya da betik tarafından yazılır. (`denetim/` klasörü betiğin değil, dış denetimin çıktısıdır.)\n")
    L.append("## Üretim\n")
    L.append(f"- Komut: `{komut}`")
    L.append(f"- Üretim süresi (veri okuma + işleme + kodlama + doğrulama): **{tr(sure_s, 1)} s**")
    L.append(f"- Kodlayıcı: **{kodlayici}**" + ("" if kodlayici == "libx264" else " (libx264 bulunamadı; mpeg4 kullanıldı)"))
    st = probe["streams"][0]
    L.append(f"- ffprobe: codec **{st.get('codec_name')}** ({st.get('profile')}), **{st.get('width')}×{st.get('height')}**, "
             f"r_frame_rate **{st.get('r_frame_rate')}**, pix_fmt **{st.get('pix_fmt')}**, kare **{st.get('nb_read_frames')}**, "
             f"süre **{tr(float(probe['format']['duration']), 3)} s**, boyut {tr(int(probe['format']['size']) / 1e6, 1)} MB")
    L.append(f"- Yeniden üretim: `O:\\navitas-local-train\\venv\\Scripts\\python.exe log_video.py` (bu klasörde); "
             f"yalnız işaret testleri için `--test-isaret`.\n")

    L.append("## 2. sürüm: denetim bulguları ve yapılan düzeltmeler\n")
    L.append(f"1. **Telemetri durumu:** HUD artık son paketten ({tr(E['telemetri'], 3)} s) hemen sonra ‘KOPTU’ yazmıyor. "
             f"Son paket ile sıradaki beklenen ATTITUDE (son ATTITUDE {tr(tl['att_son'], 3)} + periyot {tr(tl['att_periyot'], 2)} = "
             f"{tr(E['telemetri_kesik'], 3)} s) arasında nötr ‘son {t2(E['telemetri'])} s · bekleniyor’ yazıyor. ‘KOPTU’ ancak bu andan sonra, "
             f"yani başlangıçtan ({tr(E['baslangic'], 3)} s) sonra görünüyor. GPS'teki zaman aşımı kuralıyla aynı mantık.")
    gu = E["gaz_ust"]
    L.append(f"2. **Çubuklar ‘ortada’ ifadesi:** ölçüm yalnız roll/pitch/yaw (C1/C2/C4) için geçerli. Gaz ayrı hesaplanıyor: "
             f"ArduCopter Loiter ölü bandı THR_DZ={int(P_['THR_DZ'])}, RC3_DZ={int(P_['RC3_DZ'])}, RC3_MIN/MAX={int(P_['RC3_MIN'])}/{int(P_['RC3_MAX'])} "
             f"ile 0–1000 ölçeğinde {E['gaz_orta']}±{E['gaz_dz']} → bandın üstü **C3 ≥ {E['gaz_ust_pwm']} µs**. "
             + (" ".join(f"Gaz {t2(g['bas'])}–{t2(g['son'])} s bandın üstünde (C3 en çok {g['c3_max']:.0f} µs; CTUN DCRt en çok "
                         f"{tr(g['dcrt_max'], 0, True)} cm/s)." for g in gu) if gu else "Gaz uçuş boyunca bantta.")
             + f" Kalkış başlığı ‘yavaş tırmanışla ~{tr(E['hover_agl_medyan'], 1)} m askı (olay öncesi {tr(E['hover_agl_son'], 2, True)} m)’ oldu. "
             "Basamak açıklamaları o andaki gaz durumunu ve DCRt'yi yazıyor. Sonuç kartındaki madde de buna göre düzeltildi.")
    L.append("3. **Olay şeridi çakışması:** etiket satırı seçimi bağlantı çizgilerini de engel sayıyor. Bir etiketin çizgisi alt satırlardaki "
             "yazıları kesemez; üst satırlardan inen çizgi de yeni etiketin içinden geçemez. ‘CH6 disarm’ artık ‘Olay …’ etiketini bölmüyor.")
    L.append("4. **3B motor etiketleri:** yerleşim, aday konumları 24 yön × 12 mesafede tarayıp en kısa çizgili ve en az cezalı konumu seçiyor. "
             "Sert koşullar: kutu–kutu çakışması yok; hiçbir bağlantı çizgisi başka bir kutudan (ÖN dahil) geçmez; kutular rozet ve dipnot bandına girmez. "
             "Yumuşak cezalar: kutunun disk/gövde üstüne binmesi, dıştan içe ters yön, çizginin başka disk üstünden geçmesi. "
             "Önce tüm çizgiler, sonra opak kutular çiziliyor.")
    L.append(f"5. **Yazı boyu:** veri taşıyan yazılar en az {MIN_VERI_BOY} px, yardımcı dipnotlar en az {MIN_YARDIMCI_BOY} px. "
             "`maxw` küçültmesi bu sınırların altına inmiyor; sığmayan yazı uyarı üretiyor. Yer açmak için düzen değişti: "
             "motor çubukları yatay, grafikler 4 ayrı eksen, HUD iki sütun + çubuk kutuları, şeritte 2 satırlık açıklama.")
    L.append("6. **|a| grafiği:** VibeZ'den ayrıldı; kendi ekseni 0–60 m/s² (66 px), 1 g kesik referans çizgisi ve sağda ‘1 g’ etiketi var. "
             "Eksen etiketleri kırpılmıyor, gerçek değerin hizasında yazılıyor.")
    L.append("7–8. **Çıkarım etiketleri:** başlıklar ‘ölçülen olgu (ölçüm) — yorum (çıkarım[+ beyan])’ biçiminde. "
             "‘Başlangıç: ön-sağ köşe düştü (ölçüm: GyrX/GyrY) — itki kaybı (çıkarım)’, "
             "‘GPS ve pusula verisi HAVADA kesildi (ölçüm) — kablo kopması (çıkarım + beyan)’, "
             "‘Titreşim/clip patlaması (ölçüm) — pervaneler birbirine girdi (çıkarım + kullanıcı beyanı)’, "
             "‘Motor dengesizliği basamakla büyüyor (ölçüm) — gövde esniyor (çıkarım)’. Geçmiş satırları da aynı başlıkları taşıyor.")
    L.append("9. **Yerleşim denetimi ifadesi:** eski ‘uyarı 0’ yalnız panel sınırına bakıyordu. Betik artık her karede yazı–yazı, çizgi–yazı, "
             "şekil–yazı ve çizgi–etiket kutusu kesişimlerini sayıyor; sonuç aşağıdaki bölümde. Kapsam dışı olanlar orada yazılı.")
    L.append("10. **Şerit imleci:** yalnız eksen bandında çiziliyor (etiket satırlarının altında); yazıları bölmüyor.")
    L.append("11. **İşaret testi kareleri:** çağrı kutularının (AŞAĞI/YUKARI) konumu ve çizgisi önce hesaplanıp 3B etiketlere engel olarak veriliyor. "
             "Yaw testinde ayrı ‘BURUN’ çağrısı kaldırıldı; burun, ÖN etiketinin kendisi (‘ÖN = BURUN (yaw +45°)’). "
             "Sağ alttaki 2B çizgi şemasının yerine aynı `drone_ciz` fonksiyonu ikinci bir kameradan (pitch: sağdan, roll: arkadan, "
             "yaw: yukarıdan) çiziliyor.")
    L.append("12. **Yaw hatası rengi:** mor (M3'e çok yakındı) yerine nötr açık gri (214, 219, 228).\n")

    L.append("## Bölümler\n")
    L.append("| Bölüm | Video (s) | Log zamanı (s) | Kare |")
    L.append("|---|---|---|---|")
    for b, i, j in bolumler:
        lt = f"{t2(plan[i][3])} → {t2(plan[j - 1][3] + (AGIR_HIZ if b == 'agir' else 1.0) / FPS)}" if plan[i][3] is not None else "—"
        L.append(f"| {ad[b]} | {tr(i / FPS, 2)}–{tr(j / FPS, 2)} | {lt} | {j - i} |")
    L.append("")
    L.append("Ekran: sol 3B tutum (temsili) ve dipnot bandı; sağ üst motor çubukları (yatay, 1150/1949 çizgili), CCW−CW ve yaw hatası; "
             f"sağ orta 4 zaman grafiği: motorlar, CCW−CW, VibeZ, |a|. Grafik ekseni 3. ve 5. bölümde {tr(EKSEN_TAM[0], 0)}–{tr(EKSEN_TAM[1], 0)} s, "
             f"4. bölümde {tr(EKSEN_YAKIN[0], 1)}–{tr(EKSEN_YAKIN[1], 1)} s; imlecin sağı soluk. Sağ alt HUD ve pilot çubukları (Mode 2). "
             "Alt şerit: olay çizgisi, en yeni olayın büyük başlığı, en çok 2 satır ölçüm açıklaması ve önceki olaylar.\n")
    L.append("## Veri kaynakları\n")
    L.append(f"- Log: `{BIN}` — {V['fw']}, {V['kart']}. Okunan mesaj sayıları: "
             + ", ".join(f"{k} {n}" for k, n in V["sayim"].items()) + ".")
    n1s = max(int(round(1.0 / float(np.median(np.diff(V["rcou_t"]))))), 1)
    fonk = ", ".join(str(int(P_[f"SERVO{ch[1:]}_FUNCTION"])) for ch in ("C9", "C10", "C11", "C12"))
    L.append("- **ATT** Roll/Pitch/Yaw/DesYaw: 3B tutum. Açılar `np.unwrap(period=360)` ile sarmalamadan arındırılıp "
             "kareye doğrusal ara değerlenir; yazılan ATT sayıları ara değer değil, son örnektir. Yaw hatası = (DesYaw − Yaw) ±180'e sarılır.")
    L.append(f"- **RCOU** C9..C12: M1=C11, M2=C10, M3=C12, M4=C9; `SERVO9..12_FUNCTION` ({fonk}; 33+k−1 = Motor k) ile doğrulandı. "
             f"Çubuk/disk rengi son örnektir (örnekle-tut). CCW−CW = (M1+M2) − (M3+M4); ‘1 s ort.’ = son {n1s} örneğin (1 s) ortalaması.")
    L.append(f"- PWM taban/tavan parametrelerden: MOT_PWM_MIN + MOT_SPIN_MIN/MAX × aralık → **{math.floor(P_['MOT_PWM_MIN'] + P_['MOT_SPIN_MIN'] * (P_['MOT_PWM_MAX'] - P_['MOT_PWM_MIN']))} / "
             f"{math.floor(P_['MOT_PWM_MIN'] + P_['MOT_SPIN_MAX'] * (P_['MOT_PWM_MAX'] - P_['MOT_PWM_MIN']))} µs**.")
    L.append("- **RCIN** C1..C6: pilot çubukları (Mode 2; normalizasyon RCx_MIN/TRIM/MAX parametrelerinden) ve CH5/CH6 anahtarları. "
             "Roll/pitch/yaw ‘ortada’ = |Cx − RCx_TRIM| ≤ RCx_DZ. Gaz ölü bandı ArduCopter `get_pilot_desired_climb_rate()` ile hesaplanır: "
             "`RC_Channel::pwm_to_range_dz()` → control_in = ⌊1000·(C3 − (RC3_MIN+RC3_DZ)) / (RC3_MAX − (RC3_MIN+RC3_DZ))⌋; "
             "bant = `get_control_mid()` ± THR_DZ. Doğrulama olarak CTUN **DCRt** (istenen tırmanma hızı) okunur.")
    L.append(f"- **CTUN** Alt: yerden yükseklik = Alt − kalkış öncesi ortalama ({t2(E['ref_a'])}–{t2(E['ref_b'])} s, "
             f"{E['zemin_n']} örnek, {t2(E['zemin'])} m). Pencere EV 28 zamanından türetilir: [kalkış − 2,00; kalkış − 0,05]. **DCRt**: gaz isteği doğrulaması.")
    L.append("- **BAT** Volt/Curr, **VIBE** (IMU 0) VibeZ/Clip, **IMU** (I=0) Gyr/Acc (|a| = √(Ax²+Ay²+Az²)), "
             f"**GPS** NSats/Status, **MAG** (I=0, harici pusula; COMPASS_EXTERNAL={int(P_.get('COMPASS_EXTERNAL', -1))}) `S` son güncelleme alanı "
             "(HUD'da ‘Pusula’), **MODE**, **EV**, **ERR**, **ARM**.")
    L.append(f"- Telemetri: `{TLOG}` — SYSID_THISMAV={int(P_['SYSID_THISMAV'])} kaynaklı, time_boot_ms taşıyan paketler; "
             f"**yalnız bu .bin açılışına ait olanlar** (PC zamanı − time_boot_ms ile GPS'ten hesaplanan açılış anı farkı < 30 s). "
             f"Eşleşen {tl['n']} paket; son paket **{tl['son_tip']}**, time_boot_ms **{tr(tl['son_tb'], 3)} s**, PC {yerel_saat(V, tl['son_pc'])}. "
             f"ATTITUDE periyodu (medyan) {tr(tl['att_periyot'], 3)} s. "
             f"Filtresiz ‘son paket’ yanlış olurdu: tlog'da {tl['diger_acilis_sayisi']} başka açılışın paketleri de var.")
    L.append(f"- Yerel saat: GPS haftası/ms − {GPS_UTC_ARTIK_SANIYE} artık saniye → UTC. Saat dilimi, tlog dosya adındaki yerel saat ile "
             f"ilk paketin UTC damgasından: **UTC{V['tz_s'] / 3600:+.0f}**.\n")
    L.append("## Logdan hesaplanan olay zamanları ve rapor karşılaştırması\n")
    L.append("| Olay | Yöntem | Logdan (s) | Rapor/görev (s) | Fark (s) | >0,05 s |")
    L.append("|---|---|---|---|---|---|")
    yontem = {
        "kalkis": "W6 içindeki EV 28 (NOT_LANDED)",
        "basamak1": "CCW−CW adım istatistiği (1 s sonra ort. − 1 s önce ort.), kalkış+1 s … roll/pitch/yaw çubuk çıkışı−1 s aralığında en büyük 2 tepe (≥2 s arayla)",
        "basamak2": "aynı yöntem, ikinci tepe",
        "sag": "kalkış–başlangıç arası en büyük C1'i içeren C1 > RC1_TRIM+RC1_DZ bitişik dizisinin başı",
        "telemetri": "tlog: bu açılışa ait son paketin time_boot_ms'i",
        "baslangic": "kalkıştan sonra ilk IMU0 örneği, max(|GyrX|,|GyrY|) > 100 °/s",
        "pervane": "başlangıçtan sonra ilk IMU0 |a| > 2 g",
        "pervane_bitis": "başlangıç–ters arası IMU0 |a| tepesi",
        "kopma": "MAG I=0 `S` alanının donduğu değer (son güncelleme)",
        "kopma_bitis": "MAG I=0 `S`'nin ilk tekrarlandığı örnek (donuk)",
        "ters": "başlangıçtan sonra ilk ATT |Roll| > 90°",
        "carpma": "ters–disarm arası IMU0 |a| tepesi",
        "disarm": "W6'yı kapatan ARM (ArmState 0)",
    }
    for k, y in yontem.items():
        fark = E[k] - REFERANS[k]
        y = y.replace("|", "\\|")
        L.append(f"| {k} | {y} | **{tr(E[k], 3)}** | {t2(REFERANS[k])} | {tr(fark, 3, True)} | {'**EVET**' if abs(fark) > 0.05 else 'hayır'} |")
    for n, p in enumerate(E["pencereler"], 1):
        for alan, anahtar in (("bas", f"W{n} başlangıç"), ("son", f"W{n} bitiş")):
            if anahtar in REFERANS:
                fark = p[alan] - REFERANS[anahtar]
                L.append(f"| {anahtar} | {'ARM kaydı' if (alan == 'son' or p['bas_kaynak'] == 'ARM') else p['bas_kaynak']} | **{tr(p[alan], 3)}** | "
                         f"{t2(REFERANS[anahtar])} | {tr(fark, 3, True)} | {'**EVET**' if abs(fark) > 0.05 else 'hayır'} |")
    p2 = E["pencereler"][1]
    fark = p2["a_max_t"] - REFERANS["W2 sert iniş"]
    L.append(f"| W2 sert iniş | W2 içinde IMU0 \\|a\\| tepesi | **{tr(p2['a_max_t'], 3)}** | {t2(REFERANS['W2 sert iniş'])} | {tr(fark, 3, True)} | "
             f"{'**EVET**' if abs(fark) > 0.05 else 'hayır'} |")
    L.append(f"| telemetri kesilmesi belli | son ATTITUDE + medyan periyot (HUD ‘KOPTU’ bundan sonra) | **{tr(E['telemetri_kesik'], 3)}** | "
             f"≤ ~0,25 s içinde (§8) | — | — |")
    L.append("")
    L.append("Değer karşılaştırması:\n")
    L.append("| Büyüklük | Logdan | Rapor/görev | Not |")
    L.append("|---|---|---|---|")
    L.append(f"| W1 en büyük roll | {tr(E['pencereler'][0]['roll_max'], 1, True)}° ({t2(E['pencereler'][0]['roll_max_t'])} s) | 27° | "
             f"pencere içi \\|Roll\\| tepesi; rapor §5 27,2° diyor |")
    L.append(f"| Sağ düzeltme roll | {tr(E['sag_roll'], 1, True)}° ({t2(E['sag_roll_t'])} s) | 13° | C1 girişi + 0,5 s içinde ATT Roll tepesi; videoda logdaki değer yazılır |")
    L.append(f"| Ters roll | {tr(E['ters_roll'], 1, True)}° | 124° | |")
    L.append(f"| Askı yüksekliği | medyan (kalkış+3 s … başlangıç) {tr(E['hover_agl_medyan'], 2, True)} m; olay öncesi son örnek {tr(E['hover_agl_son'], 2, True)} m; "
             f"kalkış+3 s {tr(E['agl_kalkis3'], 2, True)} m | ~0,7 m, ‘düz hover’ | ‘~0,7 m’ olay anındaki değer; yükseklik pilotun gaz isteğiyle yavaşça arttı, "
             f"başlık bu yüzden ‘yavaş tırmanışla ~{tr(E['hover_agl_medyan'], 1)} m askı’ |")
    for g in E["gaz_ust"]:
        L.append(f"| Gaz ölü bandın üstünde | {tr(g['bas'], 2)}–{tr(g['son'], 2)} s; C3 en çok {g['c3_max']:.0f} µs (bant üstü ≥{E['gaz_ust_pwm']}); "
                 f"DCRt en çok {tr(g['dcrt_max'], 0, True)} cm/s | ‘çubuklar ortada’ | rapor §8 ‘büyük ölçüde ortada’ |")
    L.append(f"| Roll/pitch/yaw çubuk çıkışı | {tr(E['cubuk_cikis'], 2)} s | — | kalkıştan sonra ilk \\|Cx − TRIM\\| > DZ (C1, C2, C4) |")
    L.append(f"| CCW−CW 1 s ort. | {tr(E['fark_ilk1s'], 0, True)} (kalkış+1 s) → {tr(E['fark_son1s'], 0, True)} µs ({t2(E['fark_son_t'])} s) | +16 → +520 µs | "
             f"ilk değerin penceresi raporda belirtilmemiş |")
    L.append(f"| Basamaklar | {tr(E['basamak1_once'], 0, True)} → {tr(E['basamak1_sonra'], 0, True)} µs; {tr(E['basamak2_once'], 0, True)} → {tr(E['basamak2_sonra'], 0, True)} µs | "
             f"+144 (189,4), +271 (194,4) | rapor anlık/farklı pencere değerleri |")
    L.append(f"| Başlangıç öncesi uçuştaki en büyük max(\\|GyrX\\|,\\|GyrY\\|) | {tr(E['bas_once_gyro_max'], 1)} °/s | — | 100 °/s eşiğinin payı |")
    L.append(f"| GPS | son örnek {t2(E['gps_son'])} s, periyot {tr(E['gps_periyot'], 2)} s, sonraki kayıt {t2(E['gps0'])} s durum {E['gps0_st']} | 202,41 / 206,41 | |")
    L.append(f"| CH6 düşük / CH5 değişimi / mod Land | {t2(E['c6_dusuk'])} / {t2(E['c5_degisim'])} / {t2(E['land_mod'])} s | 203,77 / — / — | |")
    L.append("")
    L.append("## Örnek kareler (`kareler/`)\n")
    L.append("Her PNG, ffmpeg'e giden kare tamponunun kendisinden yazılır. Doğrulama: mp4 çözülüp aynı kare numarası (ve komşuları) PNG ile "
             "karşılaştırıldı; N'deki küçük ortalama fark H.264/yuv420p kaybıdır.\n")
    L.append("| Dosya | Kare no | Video anı (s) | Log zamanı (s) | mp4 kare N ↔ PNG: ort. fark / büyük fark % | N−1 | N+1 |")
    L.append("|---|---|---|---|---|---|---|")
    dmap = {d[0]: d[2] for d in dog[0]}

    def hucre(o, k):
        return f"{tr(o[k][0], 2)} / %{tr(o[k][1], 3)}" if k in o else "—"

    for i in sorted(ornek):
        o = plan[i]
        dm = dmap.get(ornek[i], {})
        L.append(f"| {ornek[i]} | {i} | {tr(i / FPS, 3)} | {tr(o[3], 3) if o[3] is not None else '—'} | **{hucre(dm, 0)}** | {hucre(dm, -1)} | {hucre(dm, 1)} |")
    L.append("")
    L.append("Büyük fark oranı: herhangi bir renk kanalında fark > 48 olan piksellerin yüzdesi. Doğru eşleşmede N sütunu ≈ 0; "
             "komşu karelerdeki değer, o anda görüntünün ne kadar değiştiğini gösterir (kartlarda komşu kareler aynıdır).\n")
    L.append("İşaret testleri (video dışı; `--test-isaret` ile ayrıca üretilebilir; hüküm çizim fonksiyonunun dünya geometrisinden hesaplanır):\n")
    for ts in test_sonuc:
        d = test_den.get(ts["dosya"], {})
        L.append(f"- `{ts['dosya']}`: roll {tr(ts['roll'], 0, True)}°, pitch {tr(ts['pitch'], 0, True)}°, yaw {tr(ts['yaw'], 0, True)}° → "
                 f"**{ts['hukum']}**; beklenenle uyum: **{'EVET' if ts['uyum'] else 'HAYIR'}**; yerleşim denetimi: yazı×yazı {d.get('yy')}, "
                 f"çizgi×yazı {d.get('yc')}, şekil×yazı {d.get('ys')}, çizgi×etiket kutusu {d.get('ce')}")
    L.append("")

    L.append("## Yerleşim denetimi (betiğin kendi ölçümü)\n")
    L.append(f"Denetlenen kare: **{den['kare']}** (videonun tamamı; kartlar dahil). Karelerdeki yazı sayısı {den['yazi_min']}–{den['yazi_max']}.\n")
    L.append("| Ölçüt | Toplam kesişim | Etkilenen kare |")
    L.append("|---|---|---|")
    for k, ad_ in (("yy", "yazı × yazı"), ("yc", "çizgi × yazı (bağlantı/imleç/eşik/ölçek çizgileri)"),
                   ("ys", "şekil × yazı (grafik, gösterge, çubuk, rozet, etiket kutusu)"), ("ce", "bağlantı çizgisi × başka etiket kutusu")):
        L.append(f"| {ad_} | **{den[k]}** | {den[k + '_kare']} |")
    L.append(f"| alt sınırın altındaki yazı (veri <{MIN_VERI_BOY} px, yardımcı <{MIN_YARDIMCI_BOY} px) | **{den['kucuk']}** | {den['kucuk_kare']} |")
    L.append("")
    L.append(f"- En küçük yazı boyu: veri taşıyan **{den['min_veri']} px**, yardımcı dipnot **{den['min_yard']} px**.")
    L.append(f"- Panel sınırı taşması / sığmama / küçültme uyarısı: **{len(uyarilar)}**" + (":" if uyarilar else "."))
    for u in uyarilar:
        L.append(f"  - {u}")
    if den["ornekler"]:
        L.append("- Kesişim örnekleri (ilk birkaç):")
        for s in den["ornekler"]:
            L.append(f"  - {s}")
    L.append("- Kapsam: yazıların sınır kutuları (PIL `textbbox`, 1 px içeri), kayıtlı çizgiler (3B bağlantı çizgileri, şerit etiket çizgileri, "
             "grafik imleci, 1150/1949 çizgileri, gösterge sıfır/eşik çizgileri, işaret testindeki çağrı ve referans çizgileri), kayıtlı şekiller. "
             "**Kapsam dışı:** veri eğrileri, 3B sahnenin kendisi (ızgara, gövde, disk, gölge; etiket kutuları opak olduğu için yazının altında kalır) "
             "ve renk kontrastı. Bu yüzden ‘0’ bir kanıt değil, yalnız bu ölçütlerin sonucudur.\n")

    L.append("## Sınırlar\n")
    hz = lambda tt: 1.0 / float(np.median(np.diff(tt)))
    at = V["att_t"]
    n_ara = int(np.sum((at > E["son_normal"] - 1e-6) & (at <= E["ters"] + 1e-6))) - 1
    ct = V["ctun_t"]
    agl_min = float(V["agl"][(ct >= E["carpma"]) & (ct <= SONRA[1])].min())
    gt = V["gps_t"]
    L.append("- **3B çizim temsilidir.** Gövde ölçüleri (kol 0,25 m, pervane yarıçapı 0,115 m) gerçek değildir. "
             "Katlanma, kopan parça ve yatay kayma çizilmez; araç yatayda sabittir, yalnız tutum ve yükseklik değişir.")
    L.append(f"- Tutum ATT'den {hz(at):.0f} Hz: iki örnek arası doğrusal ara değer. {t2(E['son_normal'])} → {t2(E['ters'])} s arasında roll "
             f"{tr(E['son_normal_roll'], 1, True)}° → {tr(E['ters_roll'], 1, True)}° yalnız {n_ara} örnek aralığıdır; aradaki hareketin biçimi bilinmez. "
             "Ağır çekimde bu, dönüşü olduğundan düzgün gösterir.")
    L.append(f"- ATT bir EKF/AHRS kestirimidir; clip başladıktan sonra ({t2(E['pervane'])} s) ve çarpmadan sonra tutumun güvenilirliği düşer.")
    L.append(f"- Yükseklik (CTUN Alt) de EKF kestirimidir. Clip başladıktan sonra bozulur ve çarpmadan sonra {tr(agl_min, 1, True)} m'ye kadar iner "
             f"({t2(E['carpma'])}–{t2(SONRA[1])} s aralığının en küçüğü). HUD bu aralıkta değeri ‘(güvenilmez)’ etiketiyle yazar. 3B çizimde yükseklik 0'da kırpılır "
             "ve en alçak nokta zemine gömülmesin diye çizim kaldırılır.")
    L.append("- Motor çubukları, sayılar ve disk renkleri RCOU komutudur (µs); gerçek itki ya da devir değildir. "
             "Olaydan sonraki tavan değerleri de komuttur, pervanenin döndüğünü göstermez.")
    L.append(f"- Log hızları (medyan örnek aralığından): IMU {hz(V['imu_t']):.0f} Hz, ATT {hz(at):.0f} Hz, RCOU {hz(V['rcou_t']):.0f} Hz, "
             f"VIBE {hz(V['vibe0_t']):.0f} Hz, CTUN {hz(ct):.0f} Hz, GPS {hz(gt[(gt > E['kalkis']) & (gt <= E['gps_son'])]):.0f} Hz. "
             f"{t2(E['baslangic'])}–{t2(E['pervane'])} s arasındaki sıralama bu örnek aralıkları kadar belirsizdir.")
    L.append(f"- Örnekle-tut değerleri ve olay metinleri, kare zamanı HUD'daki 1 ms çözünürlüğe yuvarlanarak seçilir (t + {tr(ZAMAN_COZ * 1000, 1)} ms). "
             f"Örneğin {t2(E['ters'])} s karesi, {tr(E['ters'], 6)} s damgalı ATT örneğini gösterir.")
    L.append(f"- Telemetri: HUD son paketten ({tr(E['telemetri'], 3)} s) sonra ‘son … · bekleniyor’, sıradaki beklenen ATTITUDE anından "
             f"({tr(E['telemetri_kesik'], 3)} s) sonra ‘KOPTU’ yazar. Gerçek kesilme anı bu iki zaman arasındadır ve logdan daha kesin belirlenemez. "
             f"GPS ‘VERİ YOK’ ise son örnekten sonra en büyük normal GPS aralığı ({tr(E['gps_max_dt'], 2)} s) geçince yazılır.")
    L.append(f"- Gaz ölü bandı ArduCopter kaynak formülüyle parametrelerden hesaplandı (ölçüm değil, türetme); CTUN DCRt'nin aynı aralıkta pozitif olması "
             f"(en çok {tr(E['dcrt_max_ucus'], 0, True)} cm/s) bunu doğruluyor.")
    L.append("- ‘Pervaneler birbirine girdi’ ve ‘kablo kopması’ nedensellik yorumları kullanıcı beyanı + çıkarımdır; logdaki ölçüm "
             "|a|/clip patlaması ve veri kesilmesidir. Başlıklarda ölçüm ve (çıkarım)/(beyan) ayrı yazılır.")
    L.append("- Katkı payları (Gövde/tasarım %70–85 · Pilotaj+operasyon %10–25) DUSUS_ANALIZI §8 değerlendirmesidir, ölçüm değildir. "
             "Sonuç kartındaki ‘elektrik/sensör/ayar başlatıcı yok’ maddesi §3'e dayanır; bu betikte yeniden hesaplanmadı.")
    L.append("- Kamera sabittir; referans yön kalkış öncesi yaw ortalamasıdır "
             f"({tr(E['yaw_ref'] % 360, 1)}°). Çizimdeki yaw dönüşü bu referansa göredir.")
    L.append(f"- Zaman ekseni tam görünümde {tr(EKSEN_TAM[0], 0)}–{tr(EKSEN_TAM[1], 0)} s'dir (görevdeki 186–206 yerine). "
             f"Nedeni: 5. bölüm {tr(SONRA[1], 1)} s'ye kadar sürüyor ve imlecin eksende kalması gerekiyor.")
    L.append("- Olay çizgisinin tam görünümünde başlangıç…çarpma işaretleri tek etikette (‘Olay …’) toplanır; ayrı etiketler ağır çekimdeki yakın eksende görünür.")
    L.append("- 3B etiketler her kare için bağımsız yerleştirilir; tutum hızla değişirken bir etiket kareler arasında yer değiştirebilir.")
    L.append("- W1'in başlangıcında ARM kaydı yoktur (log disarm iken kapalı); başlangıç, disarm öncesindeki son log boşluğunun sonu alınır.")
    with open(OKUBENI, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# ----------------------------------------------------------------------------
def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-isaret", action="store_true")
    ap.add_argument("--isci", type=int, default=max(2, min(16, (os.cpu_count() or 4) - 4)))
    args = ap.parse_args()
    os.makedirs(KARELER, exist_ok=True)
    t_bas = time.time()
    if args.test_isaret:
        print("İşaret testleri:")
        sonuc, uy, _ = isaret_testi()
        for u in uy:
            print("  UYARI", u)
        return

    V = veri_oku()
    V = tlog_oku(V)
    E = olaylari_hesapla(V)
    print(f"veri okundu {time.time() - t_bas:.1f} s")
    for k in ("kalkis", "basamak1", "basamak2", "sag", "telemetri", "baslangic", "pervane", "pervane_bitis", "kopma",
              "kopma_bitis", "ters", "carpma", "disarm"):
        print(f"  {k:14s} {E[k]:9.3f}  (rapor {REFERANS[k]:.2f}, fark {E[k] - REFERANS[k]:+.3f})")
    print(f"  telemetri_kesik {E['telemetri_kesik']:.3f} · gaz bandı üstü ≥{E['gaz_ust_pwm']} µs · gaz_ust {E['gaz_ust']} · gaz_alt {E['gaz_alt']}")
    plan = plan_kur()
    ornek = ornek_indeksleri(plan)
    kod = ffmpeg_kodlayici()
    enc = (["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-profile:v", "high"] if kod == "libx264"
           else ["-c:v", "mpeg4", "-q:v", "2"])
    cmd = [FFMPEG, "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           *enc, "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", MP4]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    uyarilar = set()
    den = {"kare": 0, "yy": 0, "yc": 0, "ys": 0, "ce": 0, "kucuk": 0, "yy_kare": 0, "yc_kare": 0, "ys_kare": 0, "ce_kare": 0,
           "kucuk_kare": 0, "min_veri": 99, "min_yard": 99, "yazi_min": 10 ** 6, "yazi_max": 0, "ornekler": []}
    t_r = time.time()
    with mp.get_context("spawn").Pool(args.isci, initializer=_isci_baslat, initargs=(V, E)) as havuz:
        for i, (bayt, uy, d) in enumerate(havuz.imap(_isci_kare, plan, chunksize=4)):
            proc.stdin.write(bayt)
            uyarilar.update(uy)
            den["kare"] += 1
            for k in ("yy", "yc", "ys", "ce", "kucuk"):
                den[k] += d[k]
                den[k + "_kare"] += 1 if d[k] else 0
            den["min_veri"] = min(den["min_veri"], d["min_veri"])
            den["min_yard"] = min(den["min_yard"], d["min_yard"])
            den["yazi_min"] = min(den["yazi_min"], d["yazi"])
            den["yazi_max"] = max(den["yazi_max"], d["yazi"])
            for s in d["sorun"]:
                if len(den["ornekler"]) < 12:
                    den["ornekler"].append(f"kare {i} ({plan[i][0]}{'' if plan[i][3] is None else ', log ' + tr(plan[i][3], 3) + ' s'}): {s}")
            if i in ornek:
                Image.frombytes("RGB", (W, H), bayt).save(os.path.join(KARELER, ornek[i]))
            if i % 150 == 0:
                print(f"  kare {i}/{len(plan)}  {time.time() - t_r:.1f} s")
    proc.stdin.close()
    rc = proc.wait()
    if rc != 0:
        raise SystemExit(f"ffmpeg hata kodu {rc}")
    print(f"video yazıldı {time.time() - t_r:.1f} s ({kod})")
    print("yerleşim denetimi:", json.dumps({k: v for k, v in den.items() if k != "ornekler"}, ensure_ascii=False))
    for s in den["ornekler"]:
        print("   ", s)
    print("İşaret testleri:")
    test_sonuc, uy, test_den = isaret_testi(V, E)
    uyarilar.update(uy)
    probe = ffprobe_olc(MP4)
    dog = dogrula(ornek, len(plan))
    for d in dog[0]:
        print(f"  doğrulama {d[0]} kare {d[1]}: " + " · ".join(f"N{k:+d}: ort {v[0]:.2f}, büyük %{v[1]:.3f}" for k, v in sorted(d[2].items())))
    sure = time.time() - t_bas
    komut = "O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 " + os.path.join(KLASOR, "log_video.py")
    okubeni_yaz(V, E, plan, ornek, kod, probe, sure, sorted(uyarilar), test_sonuc, dog, komut, den, test_den)
    print(json.dumps(probe, ensure_ascii=False))
    print(f"uyarılar ({len(uyarilar)}):")
    for u in sorted(uyarilar):
        print("  ", u)
    print(f"TOPLAM {sure:.1f} s")


if __name__ == "__main__":
    mp.freeze_support()
    main()
