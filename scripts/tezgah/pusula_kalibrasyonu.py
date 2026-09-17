"""TEZGAH: Pixhawk onboard pusula kalibrasyonu (MAVLink) + ilerleme/sonuc kaydi (ONARIM-15).

Mission Planner "Onboard Mag Calibration" ile ayni komut: MAV_CMD_DO_START_MAG_CAL
(tum pusulalar, otomatik kayit, otomatik reboot YOK). COMPASS_AUTO_ROT=2 ise ArduPilot
harici pusulanin yonunu (COMPASS_ORIENT) kalibrasyonda kendisi dogrular/duzeltir.

KOSUL: harici GPS/pusula modulu ve Pixhawk govdeye UCUSTAKI GIBI sabit olmali; metal,
sarj cihazi, laptop ve kablolardan uzakta (tercihen disarida). Kalibrasyon suresince arac
her eksende yavasca dondurulur (her yuz bir kez yere/goge baksin). Pervaneler TAKILI DEGIL.
ARM komutu GONDERMEZ. Degisen parametreler (COMPASS_OFS*/DIA*/ODI*/ORIENT*) oncesi yedek:
results/onarim/pixhawk_20260917/pixhawk_param_yedek_20260917.param

Kullanim: .venv/bin/python scripts/tezgah/pusula_kalibrasyonu.py [--sure 300] [--kayit DOSYA]
Cikis: 0 tum pusulalar SUCCESS · 1 basarisiz/iptal · 2 baglanti yok
"""
import argparse
import json
import sys
import time
from pathlib import Path

from pymavlink import mavutil

VARSAYILAN_PORT = "/dev/serial/by-id/usb-Holybro_Pixhawk6C_220044001451333531363238-if00"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=VARSAYILAN_PORT)
    ap.add_argument("--sure", type=float, default=300.0, help="azami sure s; asilirsa kalibrasyon IPTAL")
    ap.add_argument("--kayit", type=Path,
                    default=Path("results/onarim/pixhawk_20260917") / f"pusula_kal_{time.strftime('%H%M%S')}.jsonl")
    a = ap.parse_args()
    m = mavutil.mavlink_connection(a.port, baud=115200)
    hb = m.wait_heartbeat(timeout=15)
    if hb is None:
        print("BAGLANTI YOK")
        return 2
    if hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
        print("ARAC ARM'LI — kalibrasyon baslatilmadi")
        return 1
    a.kayit.parent.mkdir(parents=True, exist_ok=True)
    kayit = a.kayit.open("a", encoding="utf-8")

    def yaz(olay, **k):
        kayit.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "olay": olay, **k},
                               default=str) + "\n")
        kayit.flush()

    m.mav.command_long_send(m.target_system, m.target_component,
                            mavutil.mavlink.MAV_CMD_DO_START_MAG_CAL, 0,
                            0, 0, 1, 0, 0, 0, 0)   # tum pusulalar, retry yok, autosave, gecikme yok, reboot yok
    yaz("BASLAT_GONDERILDI")
    print("KALIBRASYON BASLADI — araci her eksende YAVASCA dondur", flush=True)
    raporlar, son_yuzde, bas = {}, {}, time.time()
    while time.time() - bas < a.sure:
        x = m.recv_match(type=["COMMAND_ACK", "MAG_CAL_PROGRESS", "MAG_CAL_REPORT", "STATUSTEXT"],
                         blocking=True, timeout=1)
        if x is None:
            continue
        tp = x.get_type()
        if tp == "COMMAND_ACK" and x.command == mavutil.mavlink.MAV_CMD_DO_START_MAG_CAL:
            print(f"ACK sonuc={x.result}", flush=True)
            yaz("ACK", result=x.result)
            if x.result not in (0, 5):
                return 1
        elif tp == "MAG_CAL_PROGRESS":
            y = int(x.completion_pct)
            if son_yuzde.get(x.compass_id) != y and y % 5 == 0:
                son_yuzde[x.compass_id] = y
                print(f"pusula {x.compass_id}: %{y}", flush=True)
                yaz("ILERLEME", pusula=x.compass_id, yuzde=y)
        elif tp == "MAG_CAL_REPORT":
            d = x.to_dict()
            raporlar[x.compass_id] = d
            durum = mavutil.mavlink.enums["MAG_CAL_STATUS"][x.cal_status].name
            print(f"RAPOR pusula {x.compass_id}: {durum} fitness={x.fitness:.1f} "
                  f"ofs=({x.ofs_x:.0f},{x.ofs_y:.0f},{x.ofs_z:.0f}) "
                  f"yon {x.old_orientation}->{x.new_orientation} kayit={x.autosaved}", flush=True)
            yaz("RAPOR", durum=durum, **d)
        elif tp == "STATUSTEXT":
            print(f"FC: {x.text}", flush=True)
            yaz("STATUSTEXT", text=x.text)
        if raporlar and len(raporlar) >= max(len(son_yuzde), 1) and all(
                r["cal_status"] >= 4 for r in raporlar.values()):
            break
    else:
        m.mav.command_long_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_CMD_DO_CANCEL_MAG_CAL, 0, 0, 0, 0, 0, 0, 0, 0)
        print("SURE DOLDU — kalibrasyon IPTAL edildi", flush=True)
        yaz("IPTAL_SURE")
        return 1
    basari = all(r["cal_status"] == mavutil.mavlink.MAG_CAL_SUCCESS for r in raporlar.values())
    yaz("BITTI", basari=basari)
    print("SONUC:", "BASARILI — Pixhawk'i yeniden baslat (guc kes/ver)" if basari else "BASARISIZ", flush=True)
    return 0 if basari else 1


if __name__ == "__main__":
    sys.exit(main())
