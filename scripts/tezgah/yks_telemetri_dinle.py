"""TEZGAH: YKS yerine basit dinleyici — eslesme duyurusu yapar, 5005'te Jetson cercevelerini sayar,
HEARTBEAT telemetrisini (konum/irtifa/mod/arm/pixhawk) ozetler (ONARIM-18). Uretim kodu DEGIL.

JSON satiri: her saniye {t, hb_iha, konum_var, lat, lon, alt, gps_fix, uydu, mod, armed, pixhawk_canli, yas_s}.
Kullanim: .venv/bin/python scripts/tezgah/yks_telemetri_dinle.py --sure 40 --jetson 10.21.8.7 [--komut RTL@20]
"""
import argparse
import json
import socket
import sys
import time
import uuid
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KOK / "comms"))
import yks_kesif as yk  # noqa: E402
from protocol import FrameReader, command, encode  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sure", type=float, default=40.0)
    ap.add_argument("--jetson", default="10.21.8.7")
    ap.add_argument("--eslesme", default=str(Path.home() / ".config/navitas/yks_eslesme.json"))
    ap.add_argument("--komut", action="append", default=[], metavar="CMD@SANIYE",
                    help="or. GUIDED@... degil: yalniz iha_komut_alici komutlari (RTL, LAND, ARM, DISARM)")
    ap.add_argument("--jsonl", default=None)
    ap.add_argument("--duyuru-yok", action="store_true", help="eslesme duyurusu YAPMA (YKS kaybi testi)")
    a = ap.parse_args(argv)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(("0.0.0.0", 5005))
    s.settimeout(0.2)
    yay = None
    if not a.duyuru_yok:
        es = yk.eslesme_oku(a.eslesme)
        yay = yk.DuyuruYayinci(es, 5005, hedefler=[("255.255.255.255", yk.DUYURU_PORT), (a.jetson, yk.DUYURU_PORT)],
                               log=lambda *_: None)
        yay.start()
    oturum = uuid.uuid4().hex
    komutlar = sorted(((float(k.split("@")[1]), k.split("@")[0]) for k in a.komut))
    bas = time.monotonic()
    tipler, son_hb, son_hb_t, acklar = {}, {}, None, []
    cikti = open(a.jsonl, "w") if a.jsonl else None
    son_satir = bas
    seq = 7000
    while time.monotonic() - bas < a.sure:
        simdi = time.monotonic() - bas
        while komutlar and komutlar[0][0] <= simdi:
            _, cmd = komutlar.pop(0)
            seq += 1
            s.sendto(encode(command(cmd, "iha", seq=seq, oturum=oturum)), (a.jetson, 5009))
            print(f"t={simdi:.1f} CMD {cmd} seq={seq} -> {a.jetson}:5009", flush=True)
        try:
            veri, adr = s.recvfrom(65536)
            for m in FrameReader().feed(veri):
                tipler[m.get("type")] = tipler.get(m.get("type"), 0) + 1
                if m.get("type") == "HEARTBEAT" and m.get("node") == "iha":
                    son_hb, son_hb_t = m, time.monotonic()
                if m.get("type") == "ACK":
                    acklar.append((round(simdi, 1), m.get("ref"), m.get("node"), m.get("ref_tip")))
        except socket.timeout:
            pass
        if time.monotonic() - son_satir >= 1.0:
            son_satir = time.monotonic()
            h = son_hb
            satir = {"t": round(simdi, 1), "hb_iha": bool(h), "yas_s": None if son_hb_t is None else round(time.monotonic() - son_hb_t, 2),
                     "konum_var": "lat" in h, **{k: h.get(k) for k in ("lat", "lon", "alt", "hiz", "gps_fix", "uydu", "mod", "armed", "pixhawk_canli", "bat")}}
            if cikti:
                cikti.write(json.dumps(satir) + "\n")
                cikti.flush()
    if yay:
        yay.durdur()
    print(json.dumps({"tipler": tipler, "son_hb": son_hb, "acklar": acklar}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
