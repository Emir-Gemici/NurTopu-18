"""T236 — FDA görev provası, ArduCopter SITL (ön kayıt: `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` §4).

ÖN KAYITLI KAPI (10 Eylül'de, bu ölçümden ÖNCE yazıldı — burada AYNEN uygulanır):
  bekleme süresince (**ilk 10 s hariç**)
    · yatay konum merkezden        ≤ 2,0 m
    · yaw β'dan                    ≤ ±5°   → zamanın **≥ %90**'ında
    · irtifa hedeften              ± 1,0 m
  SITL koşulamazsa **ÖLÇÜLEMEDİ** (GEÇTİ değil).

NEDEN bu betik: `config/pixhawk/README.md` §6.6'da SITL yoklaması **Windows**ta
yapılmış ve "yerel ikili yok" çıkmıştı; ArduPilot SITL ikilisini **yalnız Linux
x86_64** için yayınlıyor. Bu depo bir Linux x86_64 makinesinde de açılabildiği
için prova burada koşulabilir — "Windows" bir gereklilik değil, o günkü makinenin
kısıtıydı.

Görev dosyası `scripts/fda_gorev_uret.py` ile üretilir (elle yazılmaz):
`LOITER_TIME` merkezde (D-451) ve `CONDITION_YAW` LOITER'dan ÖNCE (D-457).

Kullanım:
  .venv/bin/python -B scripts/t236_sitl_fda_provasi.py --sitl <arducopter_yolu> \
      --defaults <copter.parm> --cikti results/t236_sitl/olcum.json
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "scripts", KOK / "codes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import fda_gorev_uret as ug  # noqa: E402
from karar_sozlesmesi import DUNYA_YARICAPI_M  # noqa: E402

# Ön kayıt §4 eşikleri — DEĞİŞTİRİLMEZ.
ESIK_YATAY_M = 2.0
ESIK_YAW_DERECE = 5.0
ESIK_IRTIFA_M = 1.0
ESIK_ORAN = 0.90
ISINMA_S = 10.0          # beklemenin ilk 10 s'i ölçüme girmez

# SITL home: ArduPilot'un standart CMAC sahası.
HOME_LAT, HOME_LON, HOME_ALT, HOME_YAW = -35.363261, 149.165230, 584.0, 353.0
IRTIFA_M = 32.0
LOITER_S = 60.0
KENAR_M = 20.0           # şartname FDA alanı 20×20 m


def kare_koseler(lat, lon, kenar_m):
    """Home'un biraz kuzeyinde `kenar_m` × `kenar_m` kare (saat yönünde)."""
    d_lat = math.degrees(kenar_m / DUNYA_YARICAPI_M)
    d_lon = math.degrees(kenar_m / (DUNYA_YARICAPI_M * math.cos(math.radians(lat))))
    lat0 = lat + math.degrees(40.0 / DUNYA_YARICAPI_M)   # 40 m kuzeye kaydır
    return [(lat0, lon), (lat0 + d_lat, lon),
            (lat0 + d_lat, lon + d_lon), (lat0, lon + d_lon)]


def yerel_metre(ref_lat, ref_lon, lat, lon):
    ort = math.radians((ref_lat + lat) / 2.0)
    return (math.radians(lon - ref_lon) * DUNYA_YARICAPI_M * math.cos(ort),
            math.radians(lat - ref_lat) * DUNYA_YARICAPI_M)


def aci_farki(a, b):
    """(a − b) farkını −180..180 aralığına indir."""
    return (a - b + 180.0) % 360.0 - 180.0


def gorev_yukle(usta, satirlar):
    """MISSION_ITEM_INT ile görevi yükle (pymavlink)."""
    from pymavlink import mavutil  # noqa: F401

    usta.mav.mission_count_send(usta.target_system, usta.target_component,
                                len(satirlar))
    for _ in range(len(satirlar)):
        istek = usta.recv_match(type=["MISSION_REQUEST", "MISSION_REQUEST_INT"],
                                blocking=True, timeout=10)
        if istek is None:
            raise RuntimeError("görev isteği gelmedi")
        i = istek.seq
        frame, cmd, p1, p2, p3, p4, lat, lon, alt = satirlar[i]
        usta.mav.mission_item_int_send(
            usta.target_system, usta.target_component, i, frame, cmd,
            1 if i == 0 else 0, 1, float(p1), float(p2), float(p3), float(p4),
            int(round(lat * 1e7)), int(round(lon * 1e7)), float(alt))
    onay = usta.recv_match(type="MISSION_ACK", blocking=True, timeout=10)
    if onay is None:
        raise RuntimeError("MISSION_ACK gelmedi")
    return onay.type


def kos(sitl_yolu, defaults, cikti_yolu, hiz=10, ucus_tavan_s=240.0):
    from pymavlink import mavutil

    koseler = kare_koseler(HOME_LAT, HOME_LON, KENAR_M)
    satirlar, bilgi = ug.gorev_satirlari(koseler, baslangic_kenari=0,
                                         montaj_yaw=0.0, irtifa_m=IRTIFA_M,
                                         loiter_s=LOITER_S)
    merkez = bilgi["merkez"]
    beta = bilgi["komut_yaw"]

    kayit_dir = cikti_yolu.parent
    kayit_dir.mkdir(parents=True, exist_ok=True)
    gorev_dosyasi = kayit_dir / "fda_gorev_sitl.waypoints"
    gorev_dosyasi.write_text(ug.wpl_metni(satirlar), encoding="utf-8")

    surec = subprocess.Popen(
        [str(sitl_yolu), "--model", "quad", "--speedup", str(hiz),
         "--home", f"{HOME_LAT},{HOME_LON},{HOME_ALT},{HOME_YAW}",
         "--defaults", str(defaults), "-I0"],
        cwd=str(sitl_yolu.parent), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        usta = mavutil.mavlink_connection("tcp:127.0.0.1:5760")
        usta.wait_heartbeat(timeout=60)
        print(f"SITL bağlandı (sys {usta.target_system})", flush=True)

        # 🔴 YALNIZ gereken akışlar. `MAV_DATA_STREAM_ALL` 10 Hz + speedup ile
        # saniyede yüzlerce mesaj üretiyor ve alıcıyı boğuyordu (ölçüldü: süreç
        # yanıt vermeden düştü). Konum 4 Hz + durum 2 Hz yeterli.
        for _sid, _hz in ((mavutil.mavlink.MAV_DATA_STREAM_POSITION, 4),
                          (mavutil.mavlink.MAV_DATA_STREAM_EXTENDED_STATUS, 2)):
            usta.mav.request_data_stream_send(usta.target_system,
                                              usta.target_component, _sid, _hz, 1)
        t0 = time.time()
        while time.time() - t0 < 120:
            m = usta.recv_match(type="GPS_RAW_INT", blocking=True, timeout=5)
            if m and m.fix_type >= 3:
                break
        print(f"GPS fix hazır ({time.time()-t0:.0f} s)", flush=True)
        time.sleep(3)

        print(f"görev yükleniyor ({len(satirlar)} satır)…", flush=True)
        print("MISSION_ACK:", gorev_yukle(usta, satirlar), flush=True)

        usta.set_mode("GUIDED")
        time.sleep(1)
        usta.arducopter_arm()
        # `motors_armed_wait()` SÜRESİZ bloklar: ön-arm denetimi düşerse betik
        # hiç dönmez ve SITL öksüz kalır. Sınırlı bekleme + açık hata.
        arm_bitis = time.time() + 60
        while time.time() < arm_bitis and not usta.motors_armed():
            usta.recv_match(type=["HEARTBEAT", "STATUSTEXT"], blocking=True, timeout=2)
        if not usta.motors_armed():
            raise RuntimeError("ARM olmadı (ön-arm denetimi düşmüş olabilir)")
        print("ARM edildi", flush=True)
        usta.set_mode("AUTO")
        usta.mav.command_long_send(usta.target_system, usta.target_component,
                                   mavutil.mavlink.MAV_CMD_MISSION_START,
                                   0, 0, 0, 0, 0, 0, 0, 0)
        print("AUTO + MISSION_START", flush=True)

        ornekler, loiter_seq = [], None
        son_seq, bitis = -1, time.time() + ucus_tavan_s
        while time.time() < bitis:
            m = usta.recv_match(
                type=["GLOBAL_POSITION_INT", "MISSION_CURRENT", "STATUSTEXT"],
                blocking=True, timeout=10)
            if m is None:
                continue
            tip = m.get_type()
            if tip == "MISSION_CURRENT":
                if m.seq != son_seq:
                    son_seq = m.seq
                    print(f"  waypoint {m.seq} ({satirlar[m.seq][1] if m.seq < len(satirlar) else '?'})",
                          flush=True)
                    if satirlar[m.seq][1] == ug.CMD_NAV_LOITER_TIME and loiter_seq is None:
                        loiter_seq = m.seq
                        loiter_basi = time.time()
            elif tip == "GLOBAL_POSITION_INT":
                if loiter_seq is not None and son_seq == loiter_seq:
                    x, y = yerel_metre(merkez[0], merkez[1],
                                       m.lat / 1e7, m.lon / 1e7)
                    ornekler.append({
                        "t": round(time.time() - loiter_basi, 2),
                        "yatay_m": round(math.hypot(x, y), 3),
                        "yaw_hata": round(aci_farki(m.hdg / 100.0, beta), 2),
                        "irtifa_hata_m": round(m.relative_alt / 1000.0 - IRTIFA_M, 3),
                    })
                if loiter_seq is not None and son_seq > loiter_seq:
                    break
        print(f"loiter örnekleri: {len(ornekler)}", flush=True)
    finally:
        surec.terminate()
        try:
            surec.wait(timeout=10)
        except subprocess.TimeoutExpired:
            surec.kill()

    olculen = [o for o in ornekler if o["t"] >= ISINMA_S]
    sonuc = {
        "on_kayit": "results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md §4",
        "esikler": {"yatay_m": ESIK_YATAY_M, "yaw_derece": ESIK_YAW_DERECE,
                    "irtifa_m": ESIK_IRTIFA_M, "oran": ESIK_ORAN,
                    "isinma_s": ISINMA_S},
        "gorev": {"merkez": merkez, "beta_komut": round(beta, 2),
                  "irtifa_m": IRTIFA_M, "loiter_s": LOITER_S,
                  "dosya": str(gorev_dosyasi.relative_to(KOK))},
        "ornek_toplam": len(ornekler), "ornek_olculen": len(olculen),
    }
    if not olculen:
        sonuc["durum"] = "ÖLÇÜLEMEDİ"
        sonuc["sebep"] = "bekleme evresinde ısınma sonrası örnek toplanamadı"
    else:
        n = len(olculen)
        yatay_ok = sum(1 for o in olculen if o["yatay_m"] <= ESIK_YATAY_M) / n
        yaw_ok = sum(1 for o in olculen if abs(o["yaw_hata"]) <= ESIK_YAW_DERECE) / n
        irtifa_ok = sum(1 for o in olculen if abs(o["irtifa_hata_m"]) <= ESIK_IRTIFA_M) / n
        sonuc["olcum"] = {
            "yatay_oran": round(yatay_ok, 4),
            "yaw_oran": round(yaw_ok, 4),
            "irtifa_oran": round(irtifa_ok, 4),
            "yatay_max_m": round(max(o["yatay_m"] for o in olculen), 3),
            "yaw_mutlak_max": round(max(abs(o["yaw_hata"]) for o in olculen), 2),
            "irtifa_mutlak_max_m": round(max(abs(o["irtifa_hata_m"]) for o in olculen), 3),
        }
        gecti = (yatay_ok >= ESIK_ORAN and yaw_ok >= ESIK_ORAN and irtifa_ok >= ESIK_ORAN)
        sonuc["durum"] = "GEÇTİ" if gecti else "DÜŞTÜ"
    sonuc["ornekler"] = ornekler
    cikti_yolu.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in sonuc.items() if k != "ornekler"},
                     ensure_ascii=False, indent=2))
    return 0 if sonuc["durum"] == "GEÇTİ" else 1


def _ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sitl", type=Path, required=True, help="arducopter SITL ikilisi")
    ap.add_argument("--defaults", type=Path, required=True, help="copter.parm")
    ap.add_argument("--cikti", type=Path,
                    default=KOK / "results" / "t236_sitl" / "olcum.json")
    ap.add_argument("--hiz", type=int, default=10, help="SITL speedup")
    ap.add_argument("--ucus-tavan", type=float, default=240.0,
                    help="uçuş izleme üst sınırı (s) — aşılırsa ÖLÇÜLEMEDİ")
    a = ap.parse_args(argv)
    return kos(a.sitl.resolve(), a.defaults.resolve(), a.cikti, a.hiz,
               a.ucus_tavan)


if __name__ == "__main__":
    sys.exit(_ana())
