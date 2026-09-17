"""T227 / ONARIM-06: Jetson isaretli yayin — YAYINLANMIS karar bindirmeli kare, yerel HTTP.

NEDEN (D-443 kusur b, results/fdr_sprint_20260910/H9_MK15/TASARIM.md §1.1, §4 T227):
hakem ekranina giden video yalniz ham kameraydi; modelin hangi rotayi SECTIGI goruntude
gorunmuyordu. Onceki uygulama (D-448) birlesmedi. Bu modul:
  * bindirmeyi YAYINLANAN karardan cizer (KararYumusatici'dan gecen son karar; esik-alti /
    teyitsiz aday kare yayinlanmis etiketi DEGISTIRMEZ),
  * kamera goruntusu + gecilebilir (yesil) / engel (kirmizi) maske + rota noktalari +
    buyuk etiket "SECILEN ROTA: 2 - ORTA" ya da "ROTA YOK - <sebep>" + guven + seq + UTC,
  * 1280x720, <= 2 Hz, cizim + JPEG AYRI iplikte (cikarim dongusu yalniz referans birakir),
  * HTTP: scripts/kamera_koprusu.py KopruSunucusu/KareUretici YENIDEN kullanilir
    (/kare.jpg, /video, /durum) — yeni sunucu yazilmaz; isaretli_gosterici buradan okur.
KARAR URETMEZ, karar yolunu DEGISTIRMEZ (tests/test_onarim06_isaretli_yayin.py).
"""
import importlib
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np

YAYIN_GENISLIK, YAYIN_YUKSEKLIK = 1280, 720
YAYIN_AZAMI_HZ = 2.0
YAYIN_JPEG_KALITE = 80
SERIT_ADI = {1: "SOL", 2: "ORTA", 3: "SAG"}
RENK_ZEMIN = (0, 200, 0)
RENK_ENGEL = (0, 0, 230)
RENK_ROTA = (0, 255, 255)


def kamera_koprusu_modulu():
    """scripts/kamera_koprusu.py (repo) ya da duz Jetson paketi kopyasi."""
    kok = Path(__file__).resolve().parent
    for aday in (kok.parent / "scripts", kok):
        if (aday / "kamera_koprusu.py").is_file():
            yol = str(aday)
            if yol not in sys.path:
                sys.path.insert(0, yol)
            break
    return importlib.import_module("kamera_koprusu")


def etiket_metni(yol, red):
    if yol in SERIT_ADI:
        return "SECILEN ROTA: {} - {}".format(yol, SERIT_ADI[yol])
    if red:
        return "ROTA YOK - {}".format(red)
    return "ROTA YOK"


def isaretli_kare_ciz(tuval, icerik, masks, karar, seq, zaman_s,
                      boyut=(YAYIN_GENISLIK, YAYIN_YUKSEKLIK)):
    """Saf cizim: (tuval, icerik=(x0,y0,w,h), masks{0,1}, karar) -> boyut BGR kare.

    karar = {"yol": int|None, "guven": float, "waypoints": [(x,y) tuval], "red": str|None,
             "yayin_seq": int|None}  — YAYINLANMIS karar.
    """
    x0, y0, w, h = [int(v) for v in icerik]
    kare = tuval[y0:y0 + h, x0:x0 + w].copy()
    renkli = kare.copy()
    for sinif, renk in ((0, RENK_ZEMIN), (1, RENK_ENGEL)):
        m = masks.get(sinif) if masks else None
        if m is not None:
            if m.shape[:2] != tuval.shape[:2]:   # maske tuvalle ayni olcekte olmali; degilse olcekle
                m = cv2.resize(m, (tuval.shape[1], tuval.shape[0]), interpolation=cv2.INTER_NEAREST)
            parca = m[y0:y0 + h, x0:x0 + w] > 0
            renkli[parca] = renk
    kare = cv2.addWeighted(kare, 0.62, renkli, 0.38, 0)
    wps = [(int(px) - x0, int(py) - y0) for px, py in (karar.get("waypoints") or [])]
    for a, b in zip(wps, wps[1:]):
        cv2.line(kare, a, b, RENK_ROTA, max(2, w // 320))
    if wps:
        cv2.circle(kare, wps[-1], max(6, w // 120), RENK_ROTA, -1)
    # icerigi en-boy koruyarak hedef boyuta sigdir (dolgu siyah)
    hg, hy = boyut
    s = min(hg / w, hy / h)
    yeni = cv2.resize(kare, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)
    cikti = np.zeros((hy, hg, 3), np.uint8)
    ox, oy = (hg - yeni.shape[1]) // 2, (hy - yeni.shape[0]) // 2
    cikti[oy:oy + yeni.shape[0], ox:ox + yeni.shape[1]] = yeni
    yol = karar.get("yol")
    renk = (0, 220, 0) if yol in SERIT_ADI else (0, 0, 255)
    cv2.rectangle(cikti, (0, 0), (hg, 92), (0, 0, 0), -1)
    cv2.putText(cikti, etiket_metni(yol, karar.get("red")), (16, 52),
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, renk, 4)
    utc = datetime.fromtimestamp(zaman_s, timezone.utc).strftime("%H:%M:%S UTC")
    alt = "guven {:.2f} | kare {} | yayin {} | {} | KARAR URETMEZ (gorsel kanit)".format(
        float(karar.get("guven") or 0.0), seq,
        "-" if karar.get("yayin_seq") is None else karar["yayin_seq"], utc)
    cv2.putText(cikti, alt, (16, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return cikti


class IsaretliYayin:
    """Cikarim dongusunden `kare_bildir` alir; ayri iplikte <= azami_hz cizer ve yayinlar."""

    def __init__(self, host, port, *, azami_hz=YAYIN_AZAMI_HZ, kalite=YAYIN_JPEG_KALITE,
                 saat=time.monotonic, duvar=time.time, koprusu=None, log=print):
        self.koprusu = koprusu or kamera_koprusu_modulu()
        self.azami_hz = float(azami_hz)
        self.saat = saat
        self.duvar = duvar
        self.log = log
        self.uretici = self.koprusu.KareUretici("isaretli-yayin", kalite=kalite,
                                                fps_tavani=self.azami_hz, log=lambda *a, **k: None)
        with self.uretici.kilit:
            self.uretici.kaynak_acik = True
        self.sunucu = self.koprusu.KopruSunucusu((host, int(port)), self.uretici)
        self._kilit = threading.Lock()
        self._olay = threading.Event()
        self._dur = threading.Event()
        self._bekleyen = None
        self._son_teslim = None
        self._yayin = {"yol": None, "guven": 0.0, "waypoints": [], "red": "KARAR_YOK", "yayin_seq": None}
        self.cizilen = 0
        self.atlanan = 0
        self._cizici = threading.Thread(target=self._dongu, name="isaretli-cizici", daemon=True)
        self._http = threading.Thread(target=self.sunucu.serve_forever, name="isaretli-http", daemon=True)

    @property
    def adres(self):
        return self.sunucu.server_address

    def baslat(self):
        self._cizici.start()
        self._http.start()
        self.log("isaretli yayin: http://{}:{}/video (<= {:g} Hz, KARAR URETMEZ)".format(
            self.adres[0], self.adres[1], self.azami_hz))
        return self

    def karar_yayinlandi(self, yol, guven, waypoints, red, seq):
        """Yalniz KararYumusatici'dan GECEN karar icin cagrilir."""
        with self._kilit:
            self._yayin = {"yol": yol, "guven": float(guven or 0.0),
                           "waypoints": list(waypoints or []),
                           "red": (str(red[0]) if red else None), "yayin_seq": int(seq)}

    def kare_bildir(self, tuval, icerik, masks, seq):
        """Hizli: <= azami_hz'de son kareyi birakir, digerlerini sayar. Kopya YAPMAZ
        (tuval ve masks her karede yeni nesnedir, cikarim dongusu onlari degistirmez)."""
        simdi = self.saat()
        with self._kilit:
            if self._son_teslim is not None and simdi - self._son_teslim < 1.0 / self.azami_hz:
                self.atlanan += 1
                return False
            self._son_teslim = simdi
            self._bekleyen = (tuval, icerik, masks, int(seq), dict(self._yayin))
        self._olay.set()
        return True

    def _dongu(self):
        while not self._dur.is_set():
            if not self._olay.wait(timeout=0.5):
                continue
            self._olay.clear()
            with self._kilit:
                is_ = self._bekleyen
                self._bekleyen = None
            if is_ is None:
                continue
            tuval, icerik, masks, seq, karar = is_
            try:
                kare = isaretli_kare_ciz(tuval, icerik, masks, karar, seq, self.duvar())
                self.uretici._kare_yayinla(kare)
                self.cizilen += 1
            except Exception as exc:          # gorsel kanit karari etkilemez
                self.log("UYARI: isaretli kare cizilemedi: {!r}".format(exc))

    def durdur(self):
        self._dur.set()
        self._olay.set()
        self.uretici._dur.set()
        with self.uretici.kosul:
            self.uretici.kosul.notify_all()
        self.sunucu.shutdown()
        self.sunucu.server_close()
        self._cizici.join(timeout=2.0)
