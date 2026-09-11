"""T226 uçtan uca (f): web kamerası → kamera_koprusu (indeks, 1280×720) →
YKS (gerçek Tk, GÖRÜNÜR pencere, main() ile aynı DPI kuralı) kamera görünümü:
video + küçük harita + onay paneli AYNI ANDA; köprü kapanınca KARE_BAYAT;
video koptuktan SONRA 2/2 onay ACK'i gerçek UDP ile İHA ucuna ulaşır.

Veri hattı sahte İHA/İKA UDP uçlarıyla (efemer port) sürülür: OPEN_ROUTE
(road=2 · orta) + İKA OPEN_ROUTE ACK. 5005/5006/5007'ye bind YOK.

KOSUM (depo kökünden; web kamerası takılı olmalı):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/uctan_uca_t226.py [--arka-uc auto] [--kaynak 0]
Çıktılar (bu dizin, --onek ile): <onek>_1_canli.png, <onek>_2_bayat.png,
<onek>_3_onay_video_kopuk.png, <onek>_olcum.json, <onek>_hakem_log.jsonl,
<onek>_kopru_log.txt
"""
import argparse
import ctypes
import json
import re
import statistics
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[3]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

ROTA = {"v": 1, "type": "OPEN_ROUTE", "seq": 41, "road": 2, "label": "orta",
        "conf": 0.91, "ref_xy": [0.0, 0.0],
        "waypoints": [[0.5, 4.0], [1.0, 9.0], [1.5, 14.0]]}
ETIKET = "MK15 · HDMI · yakalama"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arka-uc", default="auto")
    ap.add_argument("--kaynak", default="0")
    ap.add_argument("--onek", default="e2e")
    a = ap.parse_args()

    import yks_gui
    # main() ile AYNI DPI kuralı: winfo koordinatları fiziksel piksel olur,
    # ImageGrab kutusu pencereyle örtüşür.
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        yks_gui.OLCEK = max(1.0, ctypes.windll.user32.GetDpiForSystem() / 96.0)
    except Exception:
        pass
    import tkinter as tk
    from link import UDPLink
    from protocol import FrameReader, ack, encode, heartbeat

    olcum = {"arka_uc": a.arka_uc, "kaynak": a.kaynak, "olcek": yks_gui.OLCEK,
             "baslangic": time.strftime("%Y-%m-%d %H:%M:%S")}
    kopru_log = []
    p = subprocess.Popen(
        [sys.executable, "-u", str(KOK / "scripts" / "kamera_koprusu.py"),
         "--kaynak", a.kaynak, "--genislik", "1280", "--yukseklik", "720",
         "--kamera-fps", "30", "--port", "0", "--log-aralik", "0",
         "--arka-uc", a.arka_uc],
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

    t_ilk = time.monotonic()
    while time.monotonic() - t_ilk < 20 and durum()["kare_sayaci"] < 5:
        time.sleep(0.1)
    olcum["kopru_ilk_kare_s"] = round(time.monotonic() - t0, 2)
    time.sleep(1.5)                           # fps penceresi dolsun
    olcum["kopru_durum"] = durum()

    kok = tk.Tk()
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
    app.gorunum("kamera")
    hedef = ("127.0.0.1", link.port)

    hb = {"seq": 0, "son": 0.0}

    def hb_gonder():
        # Veri hattı (SiK yerine UDP) CANLI: gerçek İHA gibi 2 Hz heartbeat +
        # `karar_yas` (A2/D-381; alan yoksa tespit taze sayılmaz, onay kapalı).
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

    def ss(ad):
        from PIL import ImageGrab
        kok.lift()
        kok.update()
        x, y = kok.winfo_rootx(), kok.winfo_rooty()
        w, h = kok.winfo_width(), kok.winfo_height()
        yol = BURASI / f"{a.onek}_{ad}.png"
        ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(yol)
        return str(yol.relative_to(KOK)).replace("\\", "/")

    def al(uc, tavan_s=2.0):
        okuyucu = FrameReader()
        mesajlar = []
        bitis = time.monotonic() + tavan_s
        while time.monotonic() < bitis:
            veri, _adr = uc.recv()
            if veri is None:
                if mesajlar:
                    break
                continue
            mesajlar.extend(okuyucu.feed(veri))
        return mesajlar

    pompala(lambda: app.karar_yas_rx is not None, 3)
    iha.send(encode(ROTA), hedef)
    olcum["rota_islendi"] = pompala(lambda: app.rota is not None, 5)
    ika.send(encode(ack(ROTA["seq"], "ika", "OPEN_ROUTE")), hedef)
    olcum["ika_kaniti"] = pompala(app.ika_aktarim_kaniti_var, 5)
    olcum["yks_canli_oldu"] = pompala(
        lambda: app.kamera_istemci.snapshot()["durum"] == "CANLI"
        and app._kamera_foto is not None, 20)
    app.btn_onay.invoke()                         # 1/2 tespit doğrulandı
    pompala(lambda: False, 1.5)
    snap = app.kamera_istemci.snapshot()
    olcum["yks_canli"] = {
        "durum": snap["durum"], "kare_yasi_s": snap["kare_yasi_s"],
        "kare_sira": snap["kare_sira"], "degisen_kare": snap["degisen_kare"],
        "gosterilen_resim_px": ([app._kamera_foto.width(), app._kamera_foto.height()]
                                if app._kamera_foto is not None else None),
        "mini_harita_ismapped": bool(app.mini_harita.winfo_ismapped()),
        "video_ismapped": bool(app.lbl_kamera_img.winfo_ismapped()),
        "onay_dugmesi_ismapped": bool(app.btn_onay.winfo_ismapped()),
        "karar_kutusu": app.lbl_karar.cget("text"),
        "onay_dugmesi": app.btn_onay.cget("text"),
        "baslik": app.lbl_kamera_baslik.cget("text"),
        "mini_x": app.mini_harita.winfo_rootx(),
        "video_x_sag": app.lbl_kamera_img.winfo_rootx() + app.lbl_kamera_img.winfo_width(),
        "onay_panel_w": app.p_karar.winfo_width(),
        "pencere": [kok.winfo_width(), kok.winfo_height()],
        "tespit_onayli_1_2": app.tespit_onayli,
    }
    olcum["ss_canli"] = ss("1_canli")
    yaslar = []
    for _ in range(30):                           # ~6 s kare yaşı örnekleri
        pompala(lambda: False, 0.2)
        y = app.kamera_istemci.snapshot()["kare_yasi_s"]
        if y is not None:
            yaslar.append(y)
    olcum["kare_yasi_ornek"] = {
        "n": len(yaslar), "p50_s": round(statistics.median(yaslar), 3) if yaslar else None,
        "maks_s": round(max(yaslar), 3) if yaslar else None,
        "not": "YKS istemcisinin son DEĞİŞEN kareyi aldığı andan beri geçen süre "
               "(köprü→YKS HTTP; camdan cama gecikme DEĞİL)"}
    olcum["kopru_durum_son"] = durum()

    t_kapat = time.monotonic()
    p.terminate()
    p.wait(timeout=10)
    # İki ayrı geçiş: istemci (işçi iş parçacığı) ve EKRAN (bir sonraki `_tik`,
    # ≤ 120 ms). Görüntü EKRAN geçişinden SONRA alınır — ilk koşumda istemci
    # geçişine bağlıydı ve görüntü son kareyi yakaladı (betik kusuru).
    olcum["yks_bayat_oldu"] = pompala(
        lambda: app.kamera_istemci.snapshot()["durum"] == "KARE_BAYAT", 15)
    olcum["bayat_istemci_gecis_s"] = round(time.monotonic() - t_kapat, 3)
    olcum["yks_bayat_ekranda"] = pompala(
        lambda: app._kamera_foto is None
        and app.lbl_kamera_bilgi.cget("text").startswith("KARE_BAYAT"), 5)
    olcum["bayat_ekran_gecis_s"] = round(time.monotonic() - t_kapat, 3)
    snap = app.kamera_istemci.snapshot()
    olcum["yks_bayat"] = {"durum": snap["durum"], "hata": snap["hata"],
                          "jpeg_yok": snap["jpeg"] is None,
                          "foto_temizlendi": app._kamera_foto is None,
                          "bilgi": app.lbl_kamera_bilgi.cget("text")}
    olcum["ss_bayat"] = ss("2_bayat")

    app.btn_onay.invoke()                         # 2/2 — video KOPUK iken
    olcum["onay_2_2"] = pompala(lambda: app.onaylandi, 3)
    acklar = [m for m in al(iha) if m.get("type") == "ACK"]
    olcum["iha_ucuna_gelen_ack"] = [
        {"ref": m.get("ref"), "node": m.get("node"), "ref_tip": m.get("ref_tip")}
        for m in acklar]
    pompala(lambda: False, 0.5)
    olcum["ss_onay"] = ss("3_onay_video_kopuk")

    app.kamera_istemci.durdur()
    app.hakem_kaydi.kapat()
    for uc in (link, iha, ika):
        uc.close()
    kok.destroy()

    satirlar = [json.loads(s) for s in
                log_yolu.read_text(encoding="utf-8").strip().splitlines()]
    olcum["kamera_kanit"] = [
        {"durum": k["durum"], "degisim": k["degisim"], "kaynak": k["kaynak"],
         "kare_yasi_s": k["kare_yasi_s"], "hata": k["hata"]}
        for k in satirlar if k["olay"] == "KAMERA_KANIT"]
    olcum["hakem_olaylari"] = [k["olay"] for k in satirlar
                               if k["olay"].startswith("HAKEM_ONAYI")]
    olcum["log"] = str(log_yolu.relative_to(KOK)).replace("\\", "/")
    (BURASI / f"{a.onek}_kopru_log.txt").write_text("\n".join(kopru_log) + "\n",
                                                   encoding="utf-8")
    (BURASI / f"{a.onek}_olcum.json").write_text(
        json.dumps(olcum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(olcum, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
