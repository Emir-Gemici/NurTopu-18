"""T228 PC DUMANI — GERCEK `scripts/kamera_koprusu.py` CLI (dosya kaynagi) + GERCEK
`scripts/isaretli_gosterici.py --kip x11` CLI (Windows'ta cv2 TAM EKRAN penceresi acilir).

KAYNAK: depodaki resim dizini `data/kabul/sentetik_arena_kadraj_t66/images/train` (640x640
sentetik arena, sirali ilk 40 kare) -> 5 fps MJPG AVI, NATIVE 640x640 (gosterici 16:9 tuvale
kendisi bantlar — letterbox yolu da sinanir). AVI'ler gecici dizine yazilir, depoya YAZILMAZ.
NEDEN bu dizin (OLCULDU, 10 Eylul): `data/dji_prova_kareler/*` aksam ucusu; kare ortalama
parlakligi 8-41 (dizin ortalamasi 15-23) -> CANLI/BAYAT tuvalleri kapkara cikti, kanit
okunamadi. Arena kareleri 82-167 (ort. 126).
T227 (rpi_inference --isaretli-yayin) henuz master'da degil: gosterici yalniz HTTP sozlesmesine
baglidir ve T227 sunucusu kamera_koprusu'nun sunucusudur -> kopru bu sozlesmenin GERCEK ornegidir.
Isaretli bindirme (rota/etiket) BU dumanda YOK — kare ham resimdir.

SENARYOLAR (her birinde gosterici --tuval-kaydi <t228/duman/Sx>: durum degisiminde + son tuval):
  S1 CANLI  : kopru --fps 2            -> gosterici --sure 4
  S2 BAYAT  : kopru --fps 0.25 (4 s'de bir yeni kare; /kare.jpg 5 s'ye kadar 200) -> --sure 9
  S3 503    : kopru --kaynak yok/olmayan_kaynak.avi (/kare.jpg 503 + son_hata) -> --sure 3
  S4 YOK    : kopru yok (bos port)     -> --sure 3
  X264      : ffmpeg libx264 (GStreamer x264enc ile ayni ayar: ultrafast, zerolatency, 2000 kbit/s,
              GOP 10) 1280x720 tuval AVI'sini (ayni kareler isaretli_gosterici.sigdir ile 16:9
              bantli — rtsp 'tuval' borusunun kodladigi yerlesim) 5 fps GERCEK ZAMANLI (-re) kodlar;
              -benchmark utime/stime/rtime -> tek cekirdek yuzdesi. Taban: ayni girdi kodlamasiz.
              PC olcumudur; Jetson (Cortex-A78AE) OLCULEMEDI.
CIKTI: t228/duman_ciktisi.txt, t228/x264_cpu_olcumu.txt, t228/duman/S*/*.jpg
Loglarda depo koku `<depo>`, gecici dizin `<gecici>` ile yazilir (yerel kullanici yolu depoya girmez).
KOSUM (depo kokunden): O:/navitas-local-train/venv/Scripts/python.exe -B \
    results/fdr_sprint_20260910/H9_MK15/t228/duman_t228.py
"""
import json
import platform
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import cv2

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
BURASI = Path(__file__).resolve().parent
if str(KOK / "scripts") not in sys.path:
    sys.path.insert(0, str(KOK / "scripts"))
import isaretli_gosterici as g  # noqa: E402  (sigdir: x264 girdisi rtsp tuvaliyle ayni yerlesim)

PY = sys.executable
KOPRU = KOK / "scripts" / "kamera_koprusu.py"
GOSTERICI = KOK / "scripts" / "isaretli_gosterici.py"
KAYNAK_DIZIN = KOK / "data" / "kabul" / "sentetik_arena_kadraj_t66" / "images" / "train"
KARE_SAYISI = 40
FPS = 5
X264_SURE_S = 20
#: S3: goreli, var OLMAYAN kaynak (kopru repr'i yerel mutlak yol tasimasin)
OLMAYAN_KAYNAK = "yok/olmayan_kaynak.avi"
DUMAN = BURASI / "duman"
LOG = []
YER_TUTUCU = []


def _yer_tutucu_ekle(yol, ad):
    s = str(yol)
    for bicim in (s.replace("\\", "\\\\\\\\"), s.replace("\\", "\\\\"), s, s.replace("\\", "/")):
        YER_TUTUCU.append((bicim, ad))


_yer_tutucu_ekle(KOK, "<depo>")


def temizle(metin):
    m = str(metin)
    for eski, yeni in YER_TUTUCU:
        m = m.replace(eski, yeni)
    return m


def yaz(metin=""):
    m = temizle(metin)
    print(m, flush=True)
    LOG.append(m)


def _avi_yaz(yol, kareler):
    h, w = kareler[0].shape[:2]
    vw = cv2.VideoWriter(str(yol), cv2.VideoWriter_fourcc(*"MJPG"), float(FPS), (w, h))
    if not vw.isOpened():
        raise SystemExit("VideoWriter MJPG acilamadi: {}".format(yol))
    for k in kareler:
        vw.write(k)
    vw.release()


def avi_uret(dizin):
    """-> (kopru AVI'si: native boyut, x264 AVI'si: 1280x720 sigdir tuvali)."""
    tum = sorted(KAYNAK_DIZIN.glob("*.jpg")) + sorted(KAYNAK_DIZIN.glob("*.png"))
    kareler = [k for k in (cv2.imread(str(p)) for p in tum[:KARE_SAYISI]) if k is not None]
    if len(kareler) < KARE_SAYISI:
        raise SystemExit("kaynak kareleri eksik: {} ({} kare)".format(KAYNAK_DIZIN, len(kareler)))
    kopru_avi = dizin / "t228_arena_native.avi"
    x264_avi = dizin / "t228_arena_tuval_1280x720.avi"
    _avi_yaz(kopru_avi, kareler)
    _avi_yaz(x264_avi, [g.sigdir(k) for k in kareler])
    parlaklik = [float(k.mean()) for k in kareler]
    yaz("AVI: <gecici>/{} ({} kare, kaynak {} [{} dosya], boyut {}, parlaklik min/ort/maks "
        "{:.0f}/{:.0f}/{:.0f}, {} fps MJPG, {:.1f} MB)".format(
            kopru_avi.name, len(kareler), KAYNAK_DIZIN.relative_to(KOK).as_posix(), len(tum),
            kareler[0].shape, min(parlaklik), sum(parlaklik) / len(parlaklik), max(parlaklik), FPS,
            kopru_avi.stat().st_size / 1e6))
    yaz("AVI (x264 girdisi): <gecici>/{} (ayni kareler sigdir ile 1280x720, {:.1f} MB)".format(
        x264_avi.name, x264_avi.stat().st_size / 1e6))
    return kopru_avi, x264_avi


class Kopru:
    """kamera_koprusu CLI'si (--port 0); 'dinliyor' satirindan portu okur."""

    def __init__(self, kaynak, fps):
        self.argv = [PY, "-B", str(KOPRU), "--kaynak", str(kaynak), "--port", "0", "--fps",
                     str(fps), "--log-aralik", "0"]
        self.p = subprocess.Popen(self.argv, cwd=KOK, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                  errors="replace")
        self.satirlar = []
        self.port = None
        hazir = threading.Event()

        def oku():
            for s in self.p.stdout:
                self.satirlar.append(s.rstrip("\n"))
                m = re.search(r"dinliyor http://127\.0\.0\.1:(\d+)/video", s)
                if m:
                    self.port = int(m.group(1))
                    hazir.set()
            hazir.set()

        threading.Thread(target=oku, daemon=True).start()
        if not hazir.wait(20) or self.port is None:
            raise SystemExit("kopru 'dinliyor' satiri gelmedi: {}".format(self.satirlar))

    @property
    def kok(self):
        return "http://127.0.0.1:{}".format(self.port)

    def durum(self):
        acici = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with acici.open(self.kok + "/durum", timeout=2) as r:
            return json.loads(r.read().decode("utf-8"))

    def kapat(self):
        self.p.terminate()
        try:
            self.p.wait(5)
        except subprocess.TimeoutExpired:
            self.p.kill()
            self.p.wait(5)


def bos_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _goreli(argv):
    return " ".join(a.replace(str(KOK) + "\\", "").replace(str(KOK) + "/", "") for a in argv[1:])


def gosterici(kaynak, sure, dizin):
    if dizin.exists():
        shutil.rmtree(dizin)
    argv = [PY, "-B", str(GOSTERICI), "--kip", "x11", "--kaynak", kaynak, "--sure", str(sure),
            "--tuval-kaydi", str(dizin)]
    yaz("$ " + _goreli(argv))
    t0 = time.monotonic()
    p = subprocess.run(argv, cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=sure + 60)
    yaz("cikis={} duvar={:.1f} s".format(p.returncode, time.monotonic() - t0))
    for s in (p.stdout + p.stderr).splitlines():
        yaz("  | " + s)
    kayit = sorted(x.name for x in dizin.glob("*.jpg")) if dizin.exists() else []
    yaz("tuval kaydi: {}".format(kayit))
    return p.returncode, p.stdout + p.stderr, kayit


def senaryo(ad, kopru_kaynak, kopru_fps, sure):
    yaz()
    yaz("=== {} ===".format(ad))
    k = None
    if kopru_kaynak is not None:
        k = Kopru(kopru_kaynak, kopru_fps)
        yaz("$ " + _goreli(k.argv))
        son = time.monotonic() + 10
        d = {}
        while time.monotonic() < son:
            d = k.durum()
            if d.get("kare_sayaci") or d.get("acma_denemesi", 0) >= 2:
                break
            time.sleep(0.2)
        yaz("kopru /durum: {}".format({a: d.get(a) for a in (
            "kaynak_acik", "kare_sayaci", "fps_tavani", "son_hata", "acma_denemesi", "port")}))
        kaynak = k.kok
    else:
        kaynak = "http://127.0.0.1:{}".format(bos_port())
        yaz("kopru YOK — bos port {}".format(kaynak))
    try:
        return gosterici(kaynak, sure, DUMAN / ad.split()[0])
    finally:
        if k is not None:
            k.kapat()
            yaz("kopru logu (son 3): {}".format(k.satirlar[-3:]))


def bench(argv):
    p = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=X264_SURE_S + 120)
    m = re.search(r"bench: utime=([\d.]+)s stime=([\d.]+)s rtime=([\d.]+)s", p.stderr)
    if not m:
        return None, p.stderr[-800:]
    u, s, r = (float(x) for x in m.groups())
    return (u, s, r), m.group(0)


def x264_olc(avi):
    ffmpeg = shutil.which("ffmpeg")
    satir = []
    if not ffmpeg:
        return ["ffmpeg YOK — x264 CPU PC'de OLCULEMEDI"]
    enc = subprocess.run([ffmpeg, "-hide_banner", "-encoders"], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    if "libx264" not in enc:
        return ["ffmpeg'de libx264 YOK — x264 CPU PC'de OLCULEMEDI"]
    cpu = subprocess.run(["powershell", "-NoProfile", "-Command",
                          "(Get-CimInstance Win32_Processor | Select-Object -First 1 | "
                          "ForEach-Object { $_.Name + ' | cekirdek ' + $_.NumberOfCores + ' | mantiksal ' "
                          "+ $_.NumberOfLogicalProcessors })"],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    ortak = [ffmpeg, "-hide_banner", "-nostdin", "-benchmark", "-stream_loop", "-1", "-re",
             "-i", str(avi), "-t", str(X264_SURE_S), "-an"]
    taban_argv = ortak + ["-f", "null", "-"]
    x264_argv = ortak + ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
                         "-b:v", "2000k", "-g", "10", "-pix_fmt", "yuv420p", "-f", "null", "-"]
    satir.append("PC: {} · {} · {}".format(cpu or "?", platform.platform(), ffmpeg))
    satir.append("girdi: {} (1280x720 MJPG {} fps; arena kareleri 16:9 bantli tuvalde), -re ile "
                 "gercek zaman, {} s".format(avi.name, FPS, X264_SURE_S))
    sonuc = {}
    for ad, argv in (("taban (coz, kodlama yok)", taban_argv), ("x264 (coz + libx264)", x264_argv)):
        olcum, ham = bench(argv)
        satir.append("$ " + " ".join(a if a != str(avi) else avi.name for a in argv[1:]))
        satir.append("  {}".format(ham))
        if olcum:
            u, s, r = olcum
            yuzde = 100.0 * (u + s) / r
            sonuc[ad] = yuzde
            satir.append("  {}: CPU (utime+stime)/rtime = {:.1f}% tek cekirdek".format(ad, yuzde))
    if len(sonuc) == 2:
        a, b = sonuc["taban (coz, kodlama yok)"], sonuc["x264 (coz + libx264)"]
        satir.append("SONUC (PC): x264 kodlama farki = {:.1f}% tek cekirdek (5 fps 1280x720, "
                     "ultrafast/zerolatency/2000k/GOP10). Jetson Orin Nano: OLCULEMEDI.".format(b - a))
    return satir


def main():
    DUMAN.mkdir(parents=True, exist_ok=True)
    gecici = Path(tempfile.mkdtemp(prefix="navitas_t228_duman_"))
    _yer_tutucu_ekle(gecici, "<gecici>")
    yaz("# T228 PC dumani · {} · python {} · cv2 {}".format(
        time.strftime("%Y-%m-%d %H:%M:%S"), platform.python_version(), cv2.__version__))
    kopru_avi, x264_avi = avi_uret(gecici)
    sonuclar = {}
    sonuclar["S1"] = senaryo("S1 CANLI (kopru --fps 2)", kopru_avi, 2, 4)
    sonuclar["S2"] = senaryo("S2 BAYAT (kopru --fps 0.25)", kopru_avi, 0.25, 9)
    sonuclar["S3"] = senaryo("S3 503 (kopru kaynagi yok)", OLMAYAN_KAYNAK, 2, 3)
    sonuclar["S4"] = senaryo("S4 YOK (kopru yok)", None, None, 3)
    yaz()
    yaz("=== OZET ===")
    for ad, (kod, _cikti, kayit) in sonuclar.items():
        durumlar = [k.split("_", 1)[1].rsplit(".", 1)[0] for k in kayit if k != "son.jpg"]
        yaz("{}: cikis={} durum gecisleri={}".format(ad, kod, durumlar))
    (BURASI / "duman_ciktisi.txt").write_text("\n".join(LOG) + "\n", encoding="utf-8")
    x = [temizle(s) for s in x264_olc(x264_avi)]
    for s in x:
        print(s, flush=True)
    (BURASI / "x264_cpu_olcumu.txt").write_text(
        "# T228 x264 CPU olcumu (PC) · {}\n".format(time.strftime("%Y-%m-%d %H:%M:%S"))
        + "\n".join(x) + "\n", encoding="utf-8")
    shutil.rmtree(gecici, ignore_errors=True)


if __name__ == "__main__":
    main()
