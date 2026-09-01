"""B2/T15 — FDA 10 DAKIKA BUTCESI: algi+karar+telsiz zincirinin SURE olcumu.

ON KAYIT: `results/fda_butce/ON_KAYIT.md` — esikler (B2-G1: ucta uca p95 <=
YKS_TESPIT_TAZELIK_S) ve cerceve SONUC GORULMEDEN donduruldu. Butce sabiti
sozlesmeden okunur (SARTNAME_FDA_OPERASYON_SURESI_S) — ciplak 600 yazilmaz
(madde 16).

Zincir uretimle birebir (D-351); telsiz halkasi GERCEK KararYayinci +
UDP loopback'te ACK veren sahte IKA/YKS ile olculur. OLCULEMEDI kalemler
(ucus, hakem, seri hat, gercek kamera) toplama 0 OLARAK GIRMEZ — ayri
listelenir (OLCULEMEDI != GECTI).
"""
import argparse
import io
import json
import socket
import statistics
import sys
import threading
import time
from pathlib import Path

import cv2

from ayarlar import REPO, uretim_pt

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "codes"))
sys.path.insert(0, str(REPO / "comms"))

from karar_sozlesmesi import (OLCEK_KAYNAK_TELEMETRI,  # noqa: E402
                              SARTNAME_FDA_OPERASYON_SURESI_S,
                              YKS_TESPIT_TAZELIK_S, IHA_HEARTBEAT_ARALIK_S,
                              rota_olcek_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)
import iha_sender  # noqa: E402
from protocol import FrameReader, encode, ack  # noqa: E402

CONF = 0.30
MPP_SABIT = 0.078125     # t66 sozlesme degeri — SURE olcumu; geometri iddiasi YOK
ISINMA = 3               # ON_KAYIT §1: ilk 3 kare olcume girmez
GIRDI = REPO / "data" / "dji_gunduz_1280"
CIKTI = REPO / "results" / "fda_butce"


class LoopbackIka(threading.Thread):
    """UDP'de ACK veren sahte IKA/YKS — telsiz halkasinin karsi ucu."""

    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.settimeout(0.2)
        self.port = self.sock.getsockname()[1]
        self.dur = threading.Event()
        self.okuyucu = FrameReader()

    def run(self):
        while not self.dur.is_set():
            try:
                d, adr = self.sock.recvfrom(65535)
            except socket.timeout:
                continue
            for m in self.okuyucu.feed(d):
                if m.get("type") in ("OPEN_ROUTE", "NO_ROUTE", "IHA_LANDED"):
                    self.sock.sendto(
                        encode(ack(m["seq"], "ika", m.get("type"))), adr)


def _yuzdelik(v, q):
    s = sorted(v)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def olc(model, yayinci, yollar):
    kayitlar = []
    for p in yollar:
        img = cv2.imread(str(p))
        if img is None:
            continue
        t = {}
        t0 = time.perf_counter()
        sq, small, icerik = _preprocess(img)
        h, w = sq.shape[:2]
        t["onisleme"] = time.perf_counter() - t0

        t1 = time.perf_counter()
        son = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        t["cikarim"] = time.perf_counter() - t1

        t2 = time.perf_counter()
        masks = _maskeleri_icerige_kirp(get_masks(son, h, w), icerik)
        t["maske"] = time.perf_counter() - t2

        t3 = time.perf_counter()
        olcek_reddi = rota_olcek_reddi(MPP_SABIT)
        yol, guven, wps, red = analyze_path(
            masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=MPP_SABIT,
            return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
        if olcek_reddi is not None and red is None:
            yol, guven, wps = None, 0.0, []
            red = olcek_reddi
        yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
        t["karar"] = time.perf_counter() - t3

        t4 = time.perf_counter()
        onceki = len(yayinci.gonderilen)
        yayinci.karar(yol, guven, wps, MPP_SABIT,
                      red if isinstance(red, tuple) else
                      ((red, None) if red else None))
        bekleme_siniri = time.perf_counter() + 10.0
        while (len(yayinci.gonderilen) <= onceki
               and time.perf_counter() < bekleme_siniri):
            time.sleep(0.002)
        t["telsiz_ack"] = time.perf_counter() - t4
        t["ack_alindi"] = len(yayinci.gonderilen) > onceki and \
            bool(yayinci.gonderilen[-1][3])

        t["toplam"] = time.perf_counter() - t0
        t["kare"] = p.name
        t["yol"] = yol
        kayitlar.append(t)
    return kayitlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=str(CIKTI / "olcum_20260901.json"))
    a = ap.parse_args()

    yollar = sorted(GIRDI.glob("*.jpg"))
    if len(yollar) < ISINMA + 10:
        print(f"OLCULEMEDI: girdi karesi yetersiz ({len(yollar)})")
        return 1

    from ultralytics import YOLO
    mp = uretim_pt()
    t_yuk0 = time.perf_counter()
    model = YOLO(str(mp), task="segment")
    model.predict(cv2.imread(str(yollar[0])), imgsz=INFER_SIZE, conf=CONF,
                  verbose=False)          # soguk baslangic dahil
    model_yukleme_s = time.perf_counter() - t_yuk0

    ika = LoopbackIka()
    ika.start()
    yayinci = iha_sender.yayinci_kur(ika=f"127.0.0.1:{ika.port}",
                                     wait_ack=True, repeat=2, interval=0.05)
    yayinci.start()

    try:
        hepsi = olc(model, yayinci, yollar)
    finally:
        yayinci.stop()
        ika.dur.set()

    isinma, olcum = hepsi[:ISINMA], hepsi[ISINMA:]
    adimlar = ("onisleme", "cikarim", "maske", "karar", "telsiz_ack", "toplam")
    ozet = {}
    print(f"MODEL: {mp}\nmodel yukleme + soguk baslangic: {model_yukleme_s:.2f} s"
          f"  [BUTCE DISI — ucus oncesi]\n")
    print(f"n = {len(olcum)} (isinma {ISINMA} kare olcum disi)")
    print(f"{'adim':12s} {'p50 ms':>10s} {'p95 ms':>10s}")
    for ad in adimlar:
        v = [k[ad] * 1000 for k in olcum]
        ozet[ad] = {"p50_ms": _yuzdelik(v, 0.50), "p95_ms": _yuzdelik(v, 0.95)}
        print(f"{ad:12s} {ozet[ad]['p50_ms']:10.1f} {ozet[ad]['p95_ms']:10.1f}")

    ack_orani = sum(1 for k in olcum if k["ack_alindi"]) / len(olcum)
    p95_s = ozet["toplam"]["p95_ms"] / 1000.0
    g1 = p95_s <= YKS_TESPIT_TAZELIK_S
    g2 = p95_s <= IHA_HEARTBEAT_ARALIK_S
    print(f"\nACK alinan kare orani: {ack_orani:.3f} (UDP loopback)")
    print(f"B2-G1: ucta uca p95 {p95_s:.3f} s <= tazelik "
          f"{YKS_TESPIT_TAZELIK_S:.0f} s -> {'GECTI' if g1 else 'DUSTU'}")
    print(f"B2-G2: p95 <= heartbeat {IHA_HEARTBEAT_ARALIK_S:.0f} s -> "
          f"{'GECTI' if g2 else 'GECMEDI (bilgi)'}")

    print(f"\nBUTCE CIZELGESI (sozlesme: "
          f"{SARTNAME_FDA_OPERASYON_SURESI_S:.0f} s):")
    print("  olculen (bu PC): kare gecikmesi yukarida — BIRIKMEZ, akis halinde")
    print("  VARSAYIM-ONERI : hakem sozlu onayi 30 s (kaynak YOK; mimar secer)")
    print("  OLCULEMEDI     : kalkis/intikal/inis ucusu · IKA intikali · "
          "seri telsiz hatti · gercek kamera yakalama")
    print("  ⚠ 'sigar/sigmaz' hukmu ucus kalemleri olculmeden VERILMEZ; "
          "OLCULEMEDI toplama 0 olarak GIRMEDI.")

    Path(a.json).parent.mkdir(parents=True, exist_ok=True)
    Path(a.json).write_text(json.dumps({
        "_on_kayit": "results/fda_butce/ON_KAYIT.md",
        "_model": str(mp), "_mpp_sabit": MPP_SABIT,
        "_butce_s": SARTNAME_FDA_OPERASYON_SURESI_S,
        "model_yukleme_s_butce_disi": model_yukleme_s,
        "n": len(olcum), "isinma": ISINMA, "ozet": ozet,
        "ack_orani": ack_orani,
        "hukum": {"B2_G1": "GECTI" if g1 else "DUSTU",
                  "B2_G2": "GECTI" if g2 else "GECMEDI",
                  "p95_s": p95_s},
        "olculemedi": ["ucus_kalemleri", "hakem_onayi(VARSAYIM-ONERI 30 s)",
                       "seri_telsiz", "gercek_kamera"],
        "kareler": olcum, "isinma_kareler": isinma,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\njson -> {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
