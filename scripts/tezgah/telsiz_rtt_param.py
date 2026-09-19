#!/usr/bin/env python3
"""TEZGAH: Telsiz hattinin gidis-donus gecikmesini JETSON OLMADAN olc (PARAM_REQUEST_READ).

NEDEN: K8'in tam zinciri (Jetson->Pixhawk->telsiz->PC) Jetson'a erisim ister. Ama gecikmenin
baskin kismi TELSIZ katmanindadir ve bu, Jetson devrede olmadan da olculebilir — Pixhawk'in
kendisi yanki gorevi gorur:

    PC --USB-- RFD(yer) )))RF((( RFD(hava) --TELEM1-- Pixhawk
                                                       (PARAM_VALUE ile cevaplar)

Bu, REVIEW_LOG D-494 madde 3'teki "AYRIM 1" olcumunun (120 prob, p95 231 ms) tekrarlanabilir
halidir. MAX_WINDOW degisikliginin etkisi burada da gorunur.

URETIM KODU DEGILDIR. Yalniz okur; hicbir parametre YAZMAZ, komut gondermez.

Kullanim:
  python scripts/tezgah/telsiz_rtt_param.py --port /dev/ttyUSB0 --n 120 \
      --json --cikti results/telsiz_20260919/referans.json --etiket "referans_MW131"
"""
import argparse
import json
import statistics
import sys
import time

VARSAYILAN_PARAM = "SYSID_THISMAV"     # her ArduPilot kurulumunda vardir, kucuk ve zararsiz


def yuzdelik(dizi, p):
    if not dizi:
        return None
    d = sorted(dizi)
    k = (len(d) - 1) * p
    alt = int(k)
    ust = min(alt + 1, len(d) - 1)
    return d[alt] + (d[ust] - d[alt]) * (k - alt)


def olc(baglanti, param, n, aralik_s, zaman_asimi_s, log=print):
    rtt, zaman_asimi, gec = [], 0, 0
    for i in range(n):
        t0 = time.monotonic()
        baglanti.mav.param_request_read_send(
            baglanti.target_system, baglanti.target_component,
            param.encode("ascii"), -1)
        cevap = None
        while time.monotonic() - t0 < zaman_asimi_s:
            m = baglanti.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.05)
            if m is None:
                continue
            ad = m.param_id.rstrip("\x00") if isinstance(m.param_id, str) else \
                 m.param_id.decode("ascii", "replace").rstrip("\x00")
            if ad == param:
                cevap = m
                break
        dt = (time.monotonic() - t0) * 1000.0
        if cevap is None:
            zaman_asimi += 1
            log("prob %d/%d: ZAMAN ASIMI (%.0f ms)" % (i + 1, n, dt))
        else:
            rtt.append(dt)
            if dt > zaman_asimi_s * 1000.0 * 0.8:
                gec += 1
            log("prob %d/%d: rtt=%.1f ms" % (i + 1, n, dt))
        kalan = aralik_s - (time.monotonic() - t0)
        if kalan > 0:
            time.sleep(kalan)
    return rtt, zaman_asimi, gec


def main(argv=None):
    ap = argparse.ArgumentParser(description="Telsiz RTT olcumu (Jetson gerekmez)")
    ap.add_argument("--port", required=True, help="yer telsizi seri portu (or. /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--n", type=int, default=120)
    ap.add_argument("--aralik", type=float, default=0.25)
    ap.add_argument("--zaman-asimi", type=float, default=0.5)
    ap.add_argument("--param", default=VARSAYILAN_PARAM)
    ap.add_argument("--etiket", default="", help="kayda yazilacak test adi (or. referans_MW131)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--cikti", help="JSON cikti dosyasi")
    ap.add_argument("--sessiz", action="store_true")
    a = ap.parse_args(argv)

    try:
        from pymavlink import mavutil
    except ImportError:
        raise SystemExit("pymavlink yok")

    log = (lambda *x: None) if a.sessiz else print
    print("baglaniyor: %s @ %d ..." % (a.port, a.baud))
    m = mavutil.mavlink_connection(a.port, baud=a.baud)
    hb = m.wait_heartbeat(timeout=15)
    if hb is None:
        print("HEARTBEAT YOK — Pixhawk gorunmuyor. Kontrol: telsiz TELEM1'de mi, "
              "Pixhawk'a guc var mi, iki telsiz eslesmis mi (LED), baud dogru mu.")
        return 2
    print("Pixhawk GORULDU: sysid=%d compid=%d tip=%s" %
          (m.target_system, m.target_component, hb.type))

    rtt, zaman_asimi, gec = olc(m, a.param, a.n, a.aralik, a.zaman_asimi, log)
    sonuc = {
        "etiket": a.etiket, "t": time.time(), "port": a.port, "baud": a.baud,
        "param": a.param, "n": a.n, "aralik_s": a.aralik, "zaman_asimi_s": a.zaman_asimi,
        "cevap": len(rtt), "zaman_asimi_sayisi": zaman_asimi,
        "kayip_yuzde": round(zaman_asimi / a.n * 100.0, 2) if a.n else None,
        "gec_cevap": gec,
        "rtt_ms": {
            "ornek": len(rtt),
            "min": round(min(rtt), 1) if rtt else None,
            "p50": round(yuzdelik(rtt, 0.50), 1) if rtt else None,
            "p90": round(yuzdelik(rtt, 0.90), 1) if rtt else None,
            "p95": round(yuzdelik(rtt, 0.95), 1) if rtt else None,
            "p99": round(yuzdelik(rtt, 0.99), 1) if rtt else None,
            "maks": round(max(rtt), 1) if rtt else None,
            "ortalama": round(statistics.fmean(rtt), 1) if rtt else None,
        },
        "esik_ms": 200.0,
        "verdikt": ("GECTI" if rtt and yuzdelik(rtt, 0.95) < 200.0 else "DUSTU") if rtt else "OLCULEMEDI",
        "not": "PARAM_REQUEST_READ yanki; Jetson ve TELEM2 zincirde YOK. K8'in tam zinciri DEGIL.",
    }
    print("\n" + json.dumps(sonuc, ensure_ascii=False) if a.json else "")
    print("p50=%s p90=%s p95=%s p99=%s maks=%s ms | kayip %s%% | verdikt %s" % (
        sonuc["rtt_ms"]["p50"], sonuc["rtt_ms"]["p90"], sonuc["rtt_ms"]["p95"],
        sonuc["rtt_ms"]["p99"], sonuc["rtt_ms"]["maks"], sonuc["kayip_yuzde"], sonuc["verdikt"]))
    if a.cikti:
        from pathlib import Path
        Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
        with open(a.cikti, "w", encoding="utf-8") as f:
            json.dump(sonuc, f, ensure_ascii=False, indent=2)
        print("yazildi: %s" % a.cikti)
    return 0 if sonuc["verdikt"] == "GECTI" else 1


if __name__ == "__main__":
    sys.exit(main())
