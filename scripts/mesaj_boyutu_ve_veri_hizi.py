"""T243 (D-462 C; Y-3.3.4-M03): mesaj paket boyutu tablosu + gerçek görev veri hızı.

Ön kayıt: results/t243_mesaj_boyutu/ON_KAYIT.md (ölçümden ÖNCE yazıldı).

İki bölüm:
  A) Boyut tablosu — her mesaj tipi için WORST-CASE gövde, `comms/protocol.py`
     `encode()` ile GERÇEK çağrı üzerinden ölçülür (elle sayı yazılmaz).
     Worst-case seçimleri kaynaklıdır (MAKS_WP, en uzun gerçek sabitler) —
     rastgele/uydurma değer yoktur.
  B) Gerçek görev veri hızı — `tests/test_rpi_telsiz_yayin.py`'deki
     `_Alicilar`/`KararYayinci` altyapısı yeniden kullanılıp GERÇEK 127.0.0.1
     UDP loopback üzerinden N saniye trafik üretilir; gönderilen bayt sayaçla
     sayılır (mock/sahte değer yok). SiK 57600 8N1 doluluk oranı bu gerçek
     sayıdan hesaplanır.

Bu betik bir KAPI değildir (eşik yok); yalnız FDR §3.3.4 için veri üretir.

Kullanım:
  .venv/bin/python -B scripts/mesaj_boyutu_ve_veri_hizi.py
"""
from __future__ import annotations

import contextlib
import io
import json
import socket
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "comms"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

import protocol as proto  # noqa: E402
import iha_sender  # noqa: E402
import rpi_inference as ri  # noqa: E402
from ika_receiver import IkaReceiver  # noqa: E402
from link import UDPLink  # noqa: E402
from protocol import FrameReader  # noqa: E402
from karar_sozlesmesi import IHA_HEARTBEAT_ARALIK_S  # noqa: E402
from costmap_path_finder import MAKS_WP  # noqa: E402
import karar_sozlesmesi as ks  # noqa: E402

CIKTI = KOK / "results" / "t243_mesaj_boyutu" / "olcum.json"
SURE_S = 10.0
SIK_BAUD = 57600
SIK_BIT_PER_BAYT = 10  # 8N1: 1 baslangic + 8 veri + 1 durma biti


# ── A) Boyut tablosu ──────────────────────────────────────────────────────

def _en_uzun_sabit(modul, en_az_uzunluk=6) -> str:
    """Modüldeki BUYUK_HARF sabitlerinden en uzun dizgeyi bul (kaynaklı worst-case)."""
    adaylar = [v for k, v in vars(modul).items()
              if k.isupper() and isinstance(v, str) and len(v) >= en_az_uzunluk]
    return max(adaylar, key=len) if adaylar else "BILINMEYEN_SEBEP"


def boyut_tablosu() -> dict:
    en_uzun_sebep = _en_uzun_sabit(ks)
    ub_sinir = 150.0  # CONTRACTS.md İHA-UB 300x300 m -> yarı-genişlik sınırı
    worst_wp = [[-ub_sinir + 0.001, ub_sinir - 0.001]] * MAKS_WP

    tam_telemetri = {
        "x": -ub_sinir, "y": ub_sinir, "alt": 999.9, "hiz": 99.99,
        "yon": 359.9, "bat": 25.19, "bat_yuzde": 100.0, "uydu": 32,
        "karar_yas": 9999.999, "lat": -89.9999999, "lon": 179.9999999,
        "gps_fix": 6, "armed": True, "mod": "YAPILANDIRILMADI",
        "pixhawk_canli": True,
    }

    mesajlar = {
        "OPEN_ROUTE (0 wp)": proto.open_route(3, 0.999, [], ref_xy=[-ub_sinir, ub_sinir]),
        f"OPEN_ROUTE ({MAKS_WP} wp, MAKS_WP)": proto.open_route(
            3, 0.999, worst_wp, ref_xy=[-ub_sinir, ub_sinir]),
        "NO_ROUTE (en uzun sebep)": proto.rota_yok(en_uzun_sebep, detay=en_uzun_sebep),
        "HEARTBEAT (tam telemetri)": proto.heartbeat("iha", **tam_telemetri),
        "ACK (ref_tip+ref_cmd+sonuc dolu)": proto.ack(
            999999, "ika", ref_tip="OPEN_ROUTE", ref_cmd="PARACHUTE", sonuc="ACCEPTED"),
        "CMD (en uzun cmd/hedef + oturum)": proto.command(
            "PARACHUTE", "iha", oturum="a" * 64),
        "IHA_LANDED": proto.iha_landed(),
    }
    return {ad: {"bayt": len(proto.encode(msg)), "ornek": msg}
           for ad, msg in mesajlar.items()}


# ── B) Gerçek UDP loopback veri hızı ──────────────────────────────────────

class _SayacSoket:
    """Ham UDP dinleyici — YKS ham soketi taklidi, yalnız TOPLAM bayt sayar."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.1)
        self.adres = f"127.0.0.1:{self.sock.getsockname()[1]}"
        self.toplam_bayt = 0
        self.n_mesaj = 0
        self._dur = threading.Event()
        self._thr = threading.Thread(target=self._dongu, daemon=True)
        self._thr.start()

    def _dongu(self):
        okuyucu = FrameReader()
        while not self._dur.is_set():
            try:
                veri, _ = self.sock.recvfrom(4096)
            except (socket.timeout, ConnectionResetError):
                continue
            self.toplam_bayt += len(veri)
            self.n_mesaj += len(list(okuyucu.feed(veri)))

    def kapat(self):
        self._dur.set()
        self._thr.join(2)
        self.sock.close()


def _kamera_karari_kos(analyze, yayinci):
    kamera = SimpleNamespace(kalan=1)

    class _Kam:
        def isOpened(self_):
            return True

        def read(self_):
            if kamera.kalan <= 0:
                return False, None
            kamera.kalan -= 1
            return True, np.full((360, 640, 3), 127, np.uint8)

        def release(self_):
            pass

    maskeler = {0: np.ones((640, 640), np.uint8), 1: np.zeros((640, 640), np.uint8)}
    with mock.patch.object(cv2, "VideoCapture", return_value=_Kam()), \
            mock.patch.object(cv2, "imshow"), \
            mock.patch.object(cv2, "waitKey", return_value=ord("q")), \
            mock.patch.object(cv2, "destroyAllWindows"), \
            mock.patch.object(ri, "get_masks", return_value=maskeler), \
            mock.patch.object(ri, "analyze_path", analyze), \
            mock.patch.object(ri, "_draw_waypoints", side_effect=lambda v, _w: v), \
            contextlib.redirect_stdout(io.StringIO()):
        ri.run_camera(SimpleNamespace(predict=lambda *a, **k: [object()]), 0.30,
                      canli_olcek=(lambda _w: 0.05), yayinci=yayinci)


def gercek_veri_hizi_olc(sure_s=SURE_S) -> dict:
    """GERÇEK 127.0.0.1 UDP: KararYayinci (repeat=4, gerçek HEARTBEAT aralığı)
    + gerçek IkaReceiver ACK'i. `sure_s` boyunca karar akışı sürdürülür,
    gönderilen TOPLAM bayt/ n_mesaj ölçülür."""
    ika_link = UDPLink(bind=("127.0.0.1", 0))
    ika = IkaReceiver(ika_link).start()
    ika_adres = f"127.0.0.1:{ika_link.port}"
    yks = _SayacSoket()

    yayinci = iha_sender.yayinci_kur(
        yks=yks.adres, ika=ika_adres, repeat=4, interval=0.1,
        heartbeat_aralik=IHA_HEARTBEAT_ARALIK_S)
    y = yayinci.start()

    analyze_acik = mock.Mock(return_value=(2, 0.9, [(320, 600), (320, 300), (320, 40)], None))
    analyze_kapali = mock.Mock(return_value=(None, 0.0, [], ("KAPALI_DAR", "olcum")))

    baslangic = time.monotonic()
    donusum = 0
    try:
        while time.monotonic() - baslangic < sure_s:
            # Gerçek görev karışımı: kararlar zaman zaman değişir (yalnız
            # sabit OPEN_ROUTE değil), ACK/HEARTBEAT sürekli akar.
            _kamera_karari_kos(analyze_acik if donusum % 2 == 0 else analyze_kapali, y)
            donusum += 1
            time.sleep(0.2)
    finally:
        bitis = time.monotonic() - baslangic
        y.stop()
        y.sender.link.close()
        time.sleep(0.3)  # ucan son ACK/HEARTBEAT'leri de say
        ika.stop()
        ika_link.close()
        yks.kapat()

    toplam_bayt = yks.toplam_bayt
    toplam_mesaj = yks.n_mesaj
    bayt_s = toplam_bayt / bitis if bitis > 0 else 0.0
    sik_kapasite_bayt_s = SIK_BAUD / SIK_BIT_PER_BAYT
    return {
        "sure_s": round(bitis, 3),
        "yks_alinan_toplam_bayt": toplam_bayt,
        "yks_alinan_mesaj_sayisi": toplam_mesaj,
        "bayt_s": round(bayt_s, 2),
        "sik_57600_8n1_kapasite_bayt_s": round(sik_kapasite_bayt_s, 2),
        "sik_doluluk_orani": round(bayt_s / sik_kapasite_bayt_s, 4) if sik_kapasite_bayt_s else None,
        "not": ("Bu YALNIZ YKS ucuna giden trafiktir (bir dinleyici); sahada "
                "İKA da aynı yayından ACK'li mesaj alır — gerçek saha doluluğu "
                "ölçülen değerin üstünde olabilir, bu ölçüm ALT SINIRDIR."),
    }


def main() -> int:
    sonuc = {"olcum_tarihi": "2026-09-12", "on_kayit": "results/t243_mesaj_boyutu/ON_KAYIT.md"}
    sonuc["boyut_tablosu"] = boyut_tablosu()
    print("=== A) Boyut tablosu (worst-case, gerçek encode()) ===")
    for ad, veri in sonuc["boyut_tablosu"].items():
        print(f"  {ad:<38} {veri['bayt']:>4} bayt")

    print(f"\n=== B) Gerçek UDP loopback veri hızı ({SURE_S:.0f} s) ===")
    sonuc["veri_hizi"] = gercek_veri_hizi_olc()
    for k, v in sonuc["veri_hizi"].items():
        print(f"  {k}: {v}")

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nyazıldı: {CIKTI}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
