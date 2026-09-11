"""T226-D uçtan uca (D-448): SENTETİK video → kamera_koprusu (dosya kaynağı) →
YKS (gerçek Tk, GÖRÜNÜR pencere, main() ile AYNI DPI kuralı) kamera görünümü.

Küçük harita road 1 / 2 / 3 OPEN_ROUTE ve NO_ROUTE (kısa + uzun detay) için
ÖLÇÜLÜR (bütün metin kutuları, ikişer ikişer kesişim, tuval dışına taşma) ve
görüntülenir; ana harita ROTA YOK'ta (inset dahil) ölçülür; harita → kamera →
harita dönüşünde harita çerçevesinin sırası/konumu kaydedilir.

Kamera yerine SENTETİK kare kaynağı: bu betik 1280×720 MJPG bir test deseni
(ızgara + hareketli disk + "SENTETİK KAYNAK" yazısı) üretir, köprü onu dosya
kaynağı olarak döngüde yayınlar — görüntüde kişi/oda YOKTUR.

Veri hattı sahte İHA/İKA UDP uçlarıyla (efemer port); 5005/5006/5007'ye bind YOK.
GPU KULLANILMAZ (algı görünümü açılmaz, model yüklenmez).

KOSUM (depo kökünden):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/uctan_uca_t226d.py [--onek t226d]
Çıktılar (bu dizin): <onek>_mini_road1.png, <onek>_mini_road2.png,
<onek>_mini_road3.png, <onek>_mini_no_route.png, <onek>_mini_no_route_uzun.png,
<onek>_ana_no_route.png, <onek>_pencere_road1.png, <onek>_pencere_road3.png,
<onek>_olcum.json, <onek>_kopru_log.txt, <onek>_hakem_log.jsonl
"""
import argparse
import ctypes
import json
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[3]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

ROTA = {"v": 1, "type": "OPEN_ROUTE", "seq": 41, "road": 2, "label": "orta",
        "conf": 0.91, "ref_xy": [0.0, 0.0],
        "waypoints": [[0.5, 4.0], [1.0, 9.0], [1.5, 14.0]]}
YOK = {"v": 1, "type": "NO_ROUTE", "seq": 60, "sebep": "KORIDOR_DEGIL",
       "detay": "koridor genişlik tavanı aşıldı"}
UZUN_DETAY = ("koridor genişlik tavanı aşıldı · şerit 1 moloz · şerit 3 kapalı"
              " · costmap güvenli rota üretmedi · İKA başlangıçta bekler")
ETIKET = "SENTETIK KAYNAK · kamera_koprusu (dosya) · T226-D"
H_HB = frozenset(("H", "HB (hedef)"))


def sentetik_video(yol, n=45, w=1280, h=720, fps=15):
    """Kişisiz test deseni: gradyan zemin, ızgara, hareketli disk, yazı."""
    yazici = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    if not yazici.isOpened():
        raise SystemExit("VideoWriter acilamadi (MJPG)")
    yy, xx = np.mgrid[0:h, 0:w]
    zemin = np.dstack([(40 + 60 * xx / w), (30 + 50 * yy / h),
                       (50 + 30 * (1 - xx / w))]).astype(np.uint8)
    for i in range(n):
        kare = zemin.copy()
        for x in range(0, w, 80):
            cv2.line(kare, (x, 0), (x, h), (70, 80, 90), 1)
        for y in range(0, h, 80):
            cv2.line(kare, (0, y), (w, y), (70, 80, 90), 1)
        cx = int(160 + (w - 320) * (i / max(1, n - 1)))
        cv2.circle(kare, (cx, h // 2), 60, (60, 200, 240), -1)
        cv2.putText(kare, "SENTETIK KAYNAK - kamera yerine test deseni",
                    (60, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (255, 255, 255), 3)
        cv2.putText(kare, f"T226-D  kare {i:02d}", (60, h - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (230, 230, 230), 2)
        yazici.write(kare)
    yazici.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--onek", default="t226d")
    a = ap.parse_args()

    import yks_gui
    # main() ile AYNI DPI kuralı: winfo koordinatları fiziksel piksel olur,
    # ImageGrab kutusu pencereyle örtüşür; OLCEK = sistem DPI / 96.
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    yks_gui.OLCEK = max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    import tkinter as tk
    from PIL import ImageGrab
    from link import UDPLink
    from protocol import encode, heartbeat

    gecici = tempfile.TemporaryDirectory()
    video = Path(gecici.name) / "sentetik_t226d.avi"
    sentetik_video(video)
    olcum = {"olcek": yks_gui.OLCEK, "baslangic": time.strftime("%Y-%m-%d %H:%M:%S"),
             "kaynak": "sentetik MJPG 1280x720 (kisi yok), dosya kaynagi dongude"}
    kopru_log = []
    p = subprocess.Popen(
        [sys.executable, "-u", str(KOK / "scripts" / "kamera_koprusu.py"),
         "--kaynak", str(video), "--port", "0", "--log-aralik", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        encoding="utf-8", errors="replace")

    def oku():
        for s in p.stdout:
            kopru_log.append(s.rstrip("\r\n"))

    threading.Thread(target=oku, daemon=True).start()
    port = None
    t0 = time.monotonic()
    while time.monotonic() - t0 < 30 and port is None:
        for s in list(kopru_log):
            m = re.search(r"dinliyor http://127\.0\.0\.1:(\d+)/video", s)
            if m:
                port = int(m.group(1))
        time.sleep(0.05)
    if port is None:
        p.kill()
        raise SystemExit("kopru dinlemedi:\n" + "\n".join(kopru_log))

    def durum():
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/durum", timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))

    while time.monotonic() - t0 < 30 and durum()["kare_sayaci"] < 5:
        time.sleep(0.1)
    olcum["kopru_durum"] = durum()

    kok = tk.Tk()
    olcum["tk_scaling"] = float(kok.tk.call("tk", "scaling"))
    link = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
    iha = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
    ika = UDPLink(bind=("127.0.0.1", 0), timeout=0.05)
    log_yolu = BURASI / f"{a.onek}_hakem_log.jsonl"
    if log_yolu.exists():
        log_yolu.unlink()
    app = yks_gui.YksArayuz(
        kok, link, demo=False, ika_peer=("127.0.0.1", ika.port),
        iha_peer=("127.0.0.1", iha.port), kamera_url=f"http://127.0.0.1:{port}",
        kamera_etiket=ETIKET, hakem_log_yolu=log_yolu)
    kok.attributes("-topmost", True)
    kok.lift()
    hedef = ("127.0.0.1", link.port)
    hb = {"seq": 0, "son": 0.0}

    def hb_gonder():
        if time.monotonic() - hb["son"] >= 0.5:
            hb["seq"] += 1
            hb["son"] = time.monotonic()
            iha.send(encode(heartbeat("iha", seq=hb["seq"], karar_yas=0.3)), hedef)

    def pompala(kosul, tavan_s):
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            hb_gonder()
            kok.update()
            if kosul():
                return True
            time.sleep(0.02)
        kok.update()
        return bool(kosul())

    def ss(ad, w=None):
        kok.lift()
        pompala(lambda: False, 0.3)
        hedef_w = kok if w is None else w
        x, y = hedef_w.winfo_rootx(), hedef_w.winfo_rooty()
        yol = BURASI / f"{a.onek}_{ad}.png"
        ImageGrab.grab(bbox=(x, y, x + hedef_w.winfo_width(),
                             y + hedef_w.winfo_height())).save(yol)
        return str(yol.relative_to(KOK)).replace("\\", "/")

    def kutular(c):
        return [(c.itemcget(i, "text"), list(c.bbox(i)), list(c.gettags(i)))
                for i in c.find_all()
                if c.type(i) == "text" and c.itemcget(i, "text")]

    def denetle(c):
        k = kutular(c)
        kes = []
        for i, (ta, ba, _e) in enumerate(k):
            for tb, bb, _f in k[i + 1:]:
                if frozenset((ta, tb)) == H_HB:
                    continue
                if ba[0] < bb[2] and bb[0] < ba[2] and ba[1] < bb[3] and bb[1] < ba[3]:
                    kes.append([ta, ba, tb, bb])
        w, h = c.winfo_width(), c.winfo_height()
        tas = [[t, b] for t, b, _e in k
               if b[0] < 0 or b[1] < 0 or b[2] > w or b[3] > h]
        return {"tuval": [w, h], "kesisen": kes, "tasan": tas, "metinler": k}

    def harita_durumu():
        bilgi = dict(app.harita.pack_info())
        bilgi.pop("in", None)
        return {"sira": [str(w) for w in app.harita.master.pack_slaves()],
                "y": app.harita.winfo_y(), "h": app.harita.winfo_height(),
                "pack": {k: str(v) for k, v in bilgi.items()}}

    # 1) açılış HARİTA görünümünde; dönüş sırası ölçümü
    pompala(lambda: app.harita.winfo_ismapped() and app.harita.winfo_height() > 1, 5)
    ilk = harita_durumu()
    app.gorunum("kamera")
    pompala(app.kamera_cerceve.winfo_ismapped, 3)
    app.gorunum("harita")
    pompala(app.harita.winfo_ismapped, 3)
    pompala(lambda: False, 0.3)
    olcum["gorunum_donusu"] = {"ilk": ilk, "donus": harita_durumu(),
                               "ayni": ilk == harita_durumu()}

    # 2) kamera görünümü + canlı sentetik video
    app.gorunum("kamera")
    olcum["kamera_canli"] = pompala(
        lambda: app.kamera_istemci.snapshot()["durum"] == "CANLI"
        and app._kamera_foto is not None, 20)
    mini = app.mini_harita
    olcum["mini_tuval"] = [mini.winfo_width(), mini.winfo_height()]
    olcum["pencere"] = [kok.winfo_width(), kok.winfo_height()]
    durumlar = {}
    seq = 100
    for yol in (1, 2, 3):
        seq += 1
        iha.send(encode(dict(ROTA, seq=seq, road=yol,
                             label=yks_gui.ROAD_LABEL[yol])), hedef)
        pompala(lambda: (app.rota or {}).get("seq") == seq, 5)
        pompala(lambda: False, 0.4)
        d = denetle(mini)
        d["ss_mini"] = ss(f"mini_road{yol}", mini)
        if yol in (1, 3):
            d["ss_pencere"] = ss(f"pencere_road{yol}")
        durumlar[f"road{yol}"] = d
    for ad, detay in (("no_route", YOK["detay"]), ("no_route_uzun", UZUN_DETAY)):
        seq += 1
        iha.send(encode(dict(YOK, seq=seq, detay=detay)), hedef)
        pompala(lambda: (app.rota_yok or {}).get("seq") == seq, 5)
        pompala(lambda: False, 0.4)
        d = denetle(mini)
        d["ss_mini"] = ss(f"mini_{ad}", mini)
        durumlar[ad] = d
    olcum["mini"] = durumlar
    # 3) ana harita ROTA YOK (kısa detay yeniden; inset _tik ile çizilir)
    seq += 1
    iha.send(encode(dict(YOK, seq=seq)), hedef)
    pompala(lambda: (app.rota_yok or {}).get("seq") == seq, 5)
    app.gorunum("harita")
    pompala(lambda: any("inset" in app.harita.gettags(i)
                        for i in app.harita.find_all()), 3)
    pompala(lambda: False, 0.4)
    d = denetle(app.harita)
    d["ss"] = ss("ana_no_route", app.harita)
    olcum["ana_no_route"] = d
    olcum["kopru_durum_son"] = durum()
    olcum["ozet"] = {
        "mini_kesisen_toplam": sum(len(v["kesisen"]) for v in durumlar.values()),
        "mini_tasan_toplam": sum(len(v["tasan"]) for v in durumlar.values()),
        "ana_no_route_kesisen": len(d["kesisen"]),
        "ana_no_route_tasan": len(d["tasan"]),
        "gorunum_donusu_ayni": olcum["gorunum_donusu"]["ayni"],
        "kamera_canli": olcum["kamera_canli"]}

    p.terminate()
    p.wait(timeout=10)
    app.kamera_istemci.durdur()
    app.hakem_kaydi.kapat()
    for uc in (link, iha, ika):
        uc.close()
    kok.destroy()
    gecici.cleanup()
    (BURASI / f"{a.onek}_kopru_log.txt").write_text("\n".join(kopru_log) + "\n",
                                                   encoding="utf-8")
    (BURASI / f"{a.onek}_olcum.json").write_text(
        json.dumps(olcum, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(olcum["ozet"], ensure_ascii=False, indent=1))
    print("mini tuval", olcum["mini_tuval"], "pencere", olcum["pencere"],
          "olcek", olcum["olcek"], "tk_scaling", olcum["tk_scaling"])


if __name__ == "__main__":
    main()
