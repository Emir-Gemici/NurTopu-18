"""FDA görev planı üreteci (T235-E) — 4 köşe + Başlangıç kenarı + montaj yaw → `.waypoints`.

NEDEN: Bugünkü `config/pixhawk/fda_gorev.waypoints` elle yazılmış bir ŞABLONDUR ve
iki ÖLÇÜLMÜŞ kusuru vardır:

  1. `NAV_LOITER_TIME` satırı lat/lon **0,0** taşıyor = "bulunduğun yerde bekle".
     Son NAV waypoint'i bir KÖŞE olduğu için İHA **köşede** bekliyor, alanın
     merkezinde değil (D-451 olgu 3). 32 m'de köşe merkezli kare alanın ancak
     ~16,8×12,6 m'lik çeyreğini görür.
  2. `CONDITION_YAW` **hiç yok**. Eklenmesi gerektiği ve **`LOITER_TIME`'dan ÖNCE**
     konması gerektiği SITL'de ölçüldü (D-457): sonra konunca yaw **0/499**
     tuttu (hata p50 134,8°), önce konunca **500/500** (hata p50 0,18–0,37°,
     rüzgârlı koşuda da). `WP_YAW_BEHAVIOR=2` yeni NAV komutunda yaw'ı sıfırlar.

Bu betik o iki kusuru yapısal olarak ORTADAN KALDIRIR: merkez 4 köşeden
hesaplanır ve `LOITER_TIME` satırına AÇIKÇA yazılır; `CONDITION_YAW` her zaman
`LOITER_TIME`'dan ÖNCE üretilir (sıra kodda sabittir, elle bozulamaz — nöbetçi
`tests/test_t235e_fda_gorev_ureteci.py` bunu kilitler).

Koordinat dönüşümü `codes/karar_sozlesmesi.py`'deki `DUNYA_YARICAPI_M` /
eşdikdörtgen yaklaşımıyla AYNIDIR (madde 16: ikinci bir tanım yazılmaz).

Kullanım (köşeler saat yönünde, ondalık derece):

  python scripts/fda_gorev_uret.py \\
      --kose 37.1234567 38.7654321 --kose 37.1236000 38.7654321 \\
      --kose 37.1236000 38.7656000 --kose 37.1234567 38.7656000 \\
      --baslangic-kenari 0 --montaj-yaw 0 --irtifa 32 \\
      --cikti config/pixhawk/fda_gorev_saha.waypoints

  `--baslangic-kenari i` : i. köşe ile (i+1). köşe arasındaki kenar Başlangıç
                           kenarıdır; β bu kenarın ortasından KARŞI kenarın
                           ortasına olan kerterizdir.
  `--montaj-yaw d`       : kameranın burna göre montaj açısı (A9 ölçümü).
                           Komut açısı = β − montaj_yaw.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from karar_sozlesmesi import DUNYA_YARICAPI_M  # noqa: E402

# MAVLink komut numaraları (MAV_CMD) — çıplak sayı yazılmaz, adıyla durur.
CMD_NAV_WAYPOINT = 16
CMD_NAV_LOITER_TIME = 19
CMD_NAV_LAND = 21
CMD_NAV_TAKEOFF = 22
CMD_CONDITION_YAW = 115

FRAME_GLOBAL = 0            # home satırı (mutlak)
FRAME_GLOBAL_REL_ALT = 3    # kalkış sonrası göreli irtifa

# `config/pixhawk/arducopter_fda.param`: FENCE_ALT_MAX 50 → görev irtifası altında kalmalı.
FENCE_ALT_MAX_M = 50.0


def kose_ortalamasi(koseler):
    """4 köşenin ORTALAMASI = alan merkezi (eşdikdörtgen ölçekte yeterli)."""
    return (sum(k[0] for k in koseler) / len(koseler),
            sum(k[1] for k in koseler) / len(koseler))


def kenar_ortasi(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def kerteriz_derece(bas, son):
    """`bas` → `son` kerterizi (derece, kuzey=0, saat yönü +).

    Eşdikdörtgen izdüşüm: `karar_sozlesmesi.yerel_konum_m` ile aynı yaklaşım
    (x doğu, y kuzey), ikinci bir tanım eklenmez.
    """
    ortalama_enlem = math.radians((bas[0] + son[0]) / 2.0)
    x = math.radians(son[1] - bas[1]) * DUNYA_YARICAPI_M * math.cos(ortalama_enlem)
    y = math.radians(son[0] - bas[0]) * DUNYA_YARICAPI_M
    return math.degrees(math.atan2(x, y)) % 360.0


def gorev_satirlari(koseler, baslangic_kenari, montaj_yaw, irtifa_m,
                    loiter_s, yaw_hizi_ds=25.0):
    """QGC WPL 110 satırlarını (liste of tuple) üret.

    SIRA SABİTTİR ve bozulamaz: … köşeler → **CONDITION_YAW** → **LOITER_TIME** → iniş.
    """
    if len(koseler) != 4:
        raise ValueError(f"tam 4 köşe gerekir, gelen: {len(koseler)}")
    if not 0 <= baslangic_kenari <= 3:
        raise ValueError("--baslangic-kenari 0..3 olmalı")
    if not 0 < irtifa_m < FENCE_ALT_MAX_M:
        raise ValueError(
            f"irtifa 0 ile FENCE_ALT_MAX ({FENCE_ALT_MAX_M:.0f} m) arasında olmalı, "
            f"gelen: {irtifa_m}")

    merkez = kose_ortalamasi(koseler)
    bas_kenar = kenar_ortasi(koseler[baslangic_kenari], koseler[(baslangic_kenari + 1) % 4])
    karsi_kenar = kenar_ortasi(koseler[(baslangic_kenari + 2) % 4],
                               koseler[(baslangic_kenari + 3) % 4])
    beta = kerteriz_derece(bas_kenar, karsi_kenar)
    komut_yaw = (beta - montaj_yaw) % 360.0

    s = []
    # 0: home (mutlak çerçeve; Mission Planner yüklerken kendi home'unu koyar)
    s.append((FRAME_GLOBAL, CMD_NAV_WAYPOINT, 0, 0, 0, 0, merkez[0], merkez[1], 0))
    # 1: kalkış
    s.append((FRAME_GLOBAL_REL_ALT, CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, irtifa_m))
    # 2..5: dört köşe (tek pas)
    for k in koseler:
        s.append((FRAME_GLOBAL_REL_ALT, CMD_NAV_WAYPOINT, 0, 0, 0, 0, k[0], k[1], irtifa_m))
    # 6: 🔴 CONDITION_YAW — LOITER'dan ÖNCE (D-457: sonra konunca 0/499 DÜŞTÜ)
    #    param1 açı, param2 hız (°/s), param3 yön (0 = en kısa), param4 0 = MUTLAK
    s.append((FRAME_GLOBAL_REL_ALT, CMD_CONDITION_YAW,
              komut_yaw, yaw_hizi_ds, 0, 0, 0, 0, 0))
    # 7: 🔴 LOITER_TIME — MERKEZDE (D-451: şablonda 0,0 idi = köşede bekliyordu)
    s.append((FRAME_GLOBAL_REL_ALT, CMD_NAV_LOITER_TIME,
              loiter_s, 0, 0, 0, merkez[0], merkez[1], irtifa_m))
    # 8: iniş
    s.append((FRAME_GLOBAL_REL_ALT, CMD_NAV_LAND, 0, 0, 0, 0, 0, 0, 0))
    return s, {"merkez": merkez, "beta": beta, "komut_yaw": komut_yaw,
               "baslangic_kenar_ortasi": bas_kenar, "karsi_kenar_ortasi": karsi_kenar}


def wpl_metni(satirlar):
    """QGC WPL 110 biçimi: sekmeyle ayrılmış 12 sütun."""
    cikti = ["QGC WPL 110"]
    for i, (frame, cmd, p1, p2, p3, p4, lat, lon, alt) in enumerate(satirlar):
        akim = 1 if i == 0 else 0
        cikti.append(
            f"{i}\t{akim}\t{frame}\t{cmd}\t{p1:g}\t{p2:g}\t{p3:g}\t{p4:g}\t"
            f"{lat:.7f}\t{lon:.7f}\t{alt:g}\t1")
    return "\n".join(cikti) + "\n"


def _ana(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kose", nargs=2, type=float, action="append", metavar=("LAT", "LON"),
                    required=True, help="köşe (4 kez verilir, saat yönünde)")
    ap.add_argument("--baslangic-kenari", type=int, default=0,
                    help="Başlangıç kenarı = i. ve (i+1). köşe arası (varsayılan 0)")
    ap.add_argument("--montaj-yaw", type=float, default=0.0,
                    help="kamera montaj açısı (derece, A9 ölçümü); komut açısı = β − bu")
    ap.add_argument("--irtifa", type=float, default=32.0, help="görev irtifası (m)")
    ap.add_argument("--loiter", type=float, default=60.0, help="merkezde bekleme (s)")
    ap.add_argument("--cikti", type=Path, default=None, help="yazılacak .waypoints")
    a = ap.parse_args(argv)

    satirlar, bilgi = gorev_satirlari([tuple(k) for k in a.kose], a.baslangic_kenari,
                                      a.montaj_yaw, a.irtifa, a.loiter)
    metin = wpl_metni(satirlar)

    print(f"merkez              : {bilgi['merkez'][0]:.7f}, {bilgi['merkez'][1]:.7f}")
    print(f"Başlangıç kenar ort.: {bilgi['baslangic_kenar_ortasi'][0]:.7f}, "
          f"{bilgi['baslangic_kenar_ortasi'][1]:.7f}")
    print(f"β (kerteriz)        : {bilgi['beta']:.2f}°")
    print(f"montaj yaw          : {a.montaj_yaw:.2f}°")
    print(f"CONDITION_YAW komutu: {bilgi['komut_yaw']:.2f}°  (β − montaj_yaw)")
    print(f"irtifa              : {a.irtifa:g} m  (FENCE_ALT_MAX {FENCE_ALT_MAX_M:g} m altında)")
    print()
    if a.cikti:
        a.cikti.parent.mkdir(parents=True, exist_ok=True)
        a.cikti.write_text(metin, encoding="utf-8")
        print(f"yazıldı: {a.cikti}")
    else:
        print(metin)
    return 0


if __name__ == "__main__":
    sys.exit(_ana())
