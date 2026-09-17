"""TEZGAH: Pixhawk dataflash (.bin) loglarini MAVLink LOG_REQUEST ile indirir (ONARIM-14).

Mission Planner "Kayitlari Indir" ile ayni protokol (LOG_REQUEST_LIST / LOG_REQUEST_DATA /
LOG_DATA). Eksik parcalar yeniden istenir; boyut tutmazsa dosya `.eksik` uzantisiyla kalir.
Dosya adi: <id>_<YYYY-MM-DD_HH-MM-SS yerel ya da 1980>.bin + md5 listesi (indirme.jsonl).
En yeni log ONCE (--ilk-yeni). Arac ARM'liysa hicbir sey yapmaz. Log SILMEZ.

Kullanim: .venv/bin/python scripts/tezgah/pixhawk_log_indir.py --hedef DIZIN [--idler 81 78] [--son N]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

from pymavlink import mavutil

VARSAYILAN_PORT = "/dev/serial/by-id/usb-Holybro_Pixhawk6C_220044001451333531363238-if00"
PARCA = 90  # LOG_DATA yuku


def liste(m):
    m.mav.log_request_list_send(m.target_system, m.target_component, 0, 0xFFFF)
    girdiler, toplam, bas = {}, None, time.time()
    while time.time() - bas < 30:
        x = m.recv_match(type="LOG_ENTRY", blocking=True, timeout=2)
        if x is None:
            if toplam is not None and len(girdiler) >= toplam:
                break
            continue
        toplam = x.num_logs
        if x.id and x.size:
            girdiler[x.id] = (x.size, x.time_utc)
    return girdiler


def indir(m, log_id, boyut, zaman_asimi_s=900):
    tampon = bytearray(boyut)
    alinan = [False] * ((boyut + PARCA - 1) // PARCA)
    m.mav.log_request_data_send(m.target_system, m.target_component, log_id, 0, 0xFFFFFFFF)
    bas = son_veri = time.time()
    while time.time() - bas < zaman_asimi_s:
        x = m.recv_match(type="LOG_DATA", blocking=True, timeout=0.5)
        if x is not None and x.id == log_id:
            son_veri = time.time()
            if x.count:
                tampon[x.ofs:x.ofs + x.count] = bytes(x.data[:x.count])
                alinan[x.ofs // PARCA] = True
        eksik = [i for i, v in enumerate(alinan) if not v]
        if not eksik:
            break
        if time.time() - son_veri > 1.0:   # akis durdu: ilk eksik bolgeyi yeniden iste
            i0 = eksik[0]
            j = i0
            while j < len(alinan) and not alinan[j] and j - i0 < 2000:
                j += 1
            m.mav.log_request_data_send(m.target_system, m.target_component, log_id,
                                        i0 * PARCA, (j - i0) * PARCA)
            son_veri = time.time()
    m.mav.log_request_end_send(m.target_system, m.target_component)
    return bytes(tampon), all(alinan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=VARSAYILAN_PORT)
    ap.add_argument("--hedef", type=Path, required=True)
    ap.add_argument("--idler", type=int, nargs="*")
    ap.add_argument("--son", type=int, default=None, help="yalniz en yeni N log")
    a = ap.parse_args()
    m = mavutil.mavlink_connection(a.port, baud=115200)
    hb = m.wait_heartbeat(timeout=15)
    if hb is None:
        print("BAGLANTI YOK")
        return 2
    if hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        print("ARAC ARM'LI — indirme yapilmadi")
        return 1
    # telemetri akislarini sustur: USB hattini log verisine birak
    m.mav.request_data_stream_send(m.target_system, m.target_component,
                                   mavutil.mavlink.MAV_DATA_STREAM_ALL, 0, 0)
    girdiler = liste(m)
    idler = sorted(a.idler or girdiler, reverse=True)
    if a.son:
        idler = idler[:a.son]
    a.hedef.mkdir(parents=True, exist_ok=True)
    kayit = (a.hedef / "indirme.jsonl").open("a", encoding="utf-8")
    print(f"log sayisi {len(girdiler)} · indirilecek {len(idler)}", flush=True)
    kod = 0
    for i in idler:
        if i not in girdiler:
            print(f"{i}: listede yok")
            continue
        boyut, tu = girdiler[i]
        damga = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(tu)) if tu > 0 else "1980"
        ad = f"{i:03d}_{damga}.bin"
        if (a.hedef / ad).exists() and (a.hedef / ad).stat().st_size == boyut:
            print(f"{ad}: zaten var")
            continue
        t0 = time.time()
        veri, tam = indir(m, i, boyut)
        yol = a.hedef / (ad if tam else ad + ".eksik")
        yol.write_bytes(veri)
        sure = time.time() - t0
        md5 = hashlib.md5(veri).hexdigest()
        print(f"{yol.name}: {boyut} B · {sure:.0f} s · {boyut / max(sure, 1e-3) / 1024:.0f} KB/s · "
              f"{'TAM' if tam else 'EKSIK'} · md5 {md5}", flush=True)
        kayit.write(json.dumps({"id": i, "dosya": yol.name, "boyut": boyut, "time_utc": tu,
                                "tam": tam, "md5": md5, "sure_s": round(sure, 1)}) + "\n")
        kayit.flush()
        if not tam:
            kod = 1
    return kod


if __name__ == "__main__":
    sys.exit(main())
