"""P1 (plan v2) — SAHTE PIXHAWK: GERCEK MAVLink cerceveleri uretir.

NEDEN: `comms/inis_kaniti.py` ve `rpi_inference` irtifa saglayicisi bugune dek
YALNIZ sahte nesnelerle sinandi; venv'de pymavlink kurulu bile degildi. Sahte
nesne, pymavlink'in cerceve/CRC/`recv_match` davranisini TAKLIT ETMEZ —
kabul zincirimizin diliyle `KOD_VAR != KOSUYOR`. Bu betik uretimin okudugu
akisin AYNISINI (gercek serilestirme, gercek CRC) UDP'ye basar.

⚠ BU GERCEK PIXHAWK DEGILDIR (ON_KAYIT §4): zamanlama duzensizligi, paket
kaybi ve ArduPilot alan aliskanliklari burada yoktur. Cerceve+sozlesme
katmanini kapatir; gercek akis Faz B'de (5 Eylul) olculur.

Kullanim:
  sahte_pixhawk.py --adres udpout:127.0.0.1:14550 --senaryo ucus --irtifa 30
  sahte_pixhawk.py --senaryo inis --irtifa 30 --inis-suresi 20
  sahte_pixhawk.py --senaryo yabanci      # sysid 99'dan da basar (G5 vekili)
  sahte_pixhawk.py --senaryo donuk-saat   # time_boot_ms ilerlemez (G6 vekili)

Kutuphane olarak: `with SahtePixhawk(adres) as sp: ...` — kendi thread'inde
yayin yapar, `dur()` ile kapanir.
"""
import argparse
import math
import sys
import threading
import time

from pymavlink import mavutil

# --- yayin hizlari (gercek ArduPilot varsayilanlarina yakin) ---
HEARTBEAT_HZ = 1.0
KONUM_HZ = 5.0
DURUM_HZ = 2.0
DONGU_ADIMI_S = 0.02

# --- varsayilan arac kunyesi ---
VARSAYILAN_SYSID = 1
YABANCI_SYSID = 99
VARSAYILAN_LAT = 39.925533
VARSAYILAN_LON = 32.866287
VARSAYILAN_ADRES = "udpout:127.0.0.1:14550"

# MAVLink olcek sabitleri (madde 16: ciplak sabit degil, adlandirildi)
DERECE_E7 = 1e7
METRE_MM = 1000.0

SENARYOLAR = ("ucus", "inis", "yerde", "yabanci", "donuk-saat")


class SahtePixhawk:
    """Gercek MAVLink cerceveleri basan sahte ucus kontrolcusu.

    HEARTBEAT + GLOBAL_POSITION_INT + EXTENDED_SYS_STATE uretir. Irtifa
    profili senaryoya gore sabit ya da alcalandir; `inis` senaryosunda irtifa
    `inis_tavani_m` altina indikten sonra landed_state ON_GROUND'a doner —
    yani uretimin `yerde_mi` kaniti ancak GERCEK bir alcalma sonrasi olusur.
    """

    def __init__(self, adres=VARSAYILAN_ADRES, *, sysid=VARSAYILAN_SYSID,
                 senaryo="ucus", irtifa_m=30.0, inis_suresi_s=20.0,
                 inis_tavani_m=0.4, lat=VARSAYILAN_LAT, lon=VARSAYILAN_LON,
                 konum_hz=KONUM_HZ, durum_hz=DURUM_HZ,
                 heartbeat_hz=HEARTBEAT_HZ):
        if senaryo not in SENARYOLAR:
            raise ValueError(f"senaryo {SENARYOLAR} icinden olmali")
        if not (isinstance(sysid, int) and not isinstance(sysid, bool)
                and 1 <= sysid <= 255):
            raise ValueError("sysid 1..255 tamsayi olmali")
        for ad, deger in (("irtifa_m", irtifa_m), ("inis_suresi_s", inis_suresi_s),
                          ("inis_tavani_m", inis_tavani_m)):
            if not math.isfinite(float(deger)) or float(deger) <= 0.0:
                raise ValueError(f"{ad} pozitif ve sonlu olmali")

        self.adres = adres
        self.sysid = sysid
        self.senaryo = senaryo
        self.irtifa_m = float(irtifa_m)
        self.inis_suresi_s = float(inis_suresi_s)
        self.inis_tavani_m = float(inis_tavani_m)
        self.lat = float(lat)
        self.lon = float(lon)
        self.konum_periyodu = 1.0 / float(konum_hz)
        self.durum_periyodu = 1.0 / float(durum_hz)
        self.heartbeat_periyodu = 1.0 / float(heartbeat_hz)

        self._mav = None
        self._thread = None
        self._dur_olayi = threading.Event()
        self._baslangic = None
        self._donuk_ms = 1000
        self.gonderilen = {"heartbeat": 0, "konum": 0, "durum": 0,
                           "yabanci_konum": 0}

    # --- profil ---

    def _gecen_s(self):
        return time.monotonic() - self._baslangic

    def anlik_irtifa_m(self):
        """Senaryonun bu andaki bagil irtifasi (m)."""
        if self.senaryo == "yerde":
            # Temas etmis arac: bagil irtifa inis tavaninin ALTINDA sabit.
            return self.inis_tavani_m * 0.5
        if self.senaryo != "inis":
            return self.irtifa_m
        oran = min(1.0, max(0.0, self._gecen_s() / self.inis_suresi_s))
        # Dogrusal alcalma; sonunda inis tavaninin altina iner.
        return max(self.inis_tavani_m * 0.5,
                   self.irtifa_m * (1.0 - oran) + self.inis_tavani_m * 0.5 * oran)

    def _yerde_mi(self):
        if self.senaryo == "yerde":
            return True
        return (self.senaryo == "inis"
                and self.anlik_irtifa_m() < self.inis_tavani_m)

    def _time_boot_ms(self):
        """Ilerleyen boot zamani; `donuk-saat` senaryosunda SABIT (G6 vekili)."""
        if self.senaryo == "donuk-saat":
            return self._donuk_ms
        return int(self._gecen_s() * 1000.0) + 1

    # --- yayin ---

    def _konum_bas(self, sysid=None):
        onceki = self._mav.mav.srcSystem
        if sysid is not None:
            self._mav.mav.srcSystem = sysid
        try:
            irtifa = self.anlik_irtifa_m()
            self._mav.mav.global_position_int_send(
                self._time_boot_ms(),
                int(round(self.lat * DERECE_E7)),
                int(round(self.lon * DERECE_E7)),
                int(round((900.0 + irtifa) * METRE_MM)),   # AMSL (kullanilmaz)
                int(round(irtifa * METRE_MM)),             # relative_alt
                0, 0, 0, 0)
        finally:
            self._mav.mav.srcSystem = onceki

    def _durum_bas(self):
        mav = mavutil.mavlink
        self._mav.mav.extended_sys_state_send(
            mav.MAV_VTOL_STATE_UNDEFINED,
            mav.MAV_LANDED_STATE_ON_GROUND if self._yerde_mi()
            else mav.MAV_LANDED_STATE_IN_AIR)

    def _heartbeat_bas(self):
        mav = mavutil.mavlink
        self._mav.mav.heartbeat_send(
            mav.MAV_TYPE_FIXED_WING,          # sartname §6: sabit kanat
            mav.MAV_AUTOPILOT_ARDUPILOTMEGA,
            mav.MAV_MODE_FLAG_SAFETY_ARMED | mav.MAV_MODE_FLAG_AUTO_ENABLED,
            0, mav.MAV_STATE_ACTIVE)

    def _dongu(self):
        sonraki_hb = sonraki_konum = sonraki_durum = 0.0
        while not self._dur_olayi.is_set():
            simdi = self._gecen_s()
            if simdi >= sonraki_hb:
                self._heartbeat_bas()
                self.gonderilen["heartbeat"] += 1
                sonraki_hb = simdi + self.heartbeat_periyodu
            if simdi >= sonraki_konum:
                self._konum_bas()
                self.gonderilen["konum"] += 1
                if self.senaryo == "yabanci":
                    # Ayni porta YABANCI aracin paketi: uretim bunu kaynak
                    # kimligiyle elemeli (G5). Yabancinin irtifasi kasten FARKLI.
                    onceki = self.irtifa_m
                    self.irtifa_m = onceki + 100.0
                    try:
                        self._konum_bas(sysid=YABANCI_SYSID)
                    finally:
                        self.irtifa_m = onceki
                    self.gonderilen["yabanci_konum"] += 1
                sonraki_konum = simdi + self.konum_periyodu
            if simdi >= sonraki_durum:
                self._durum_bas()
                self.gonderilen["durum"] += 1
                sonraki_durum = simdi + self.durum_periyodu
            self._dur_olayi.wait(DONGU_ADIMI_S)

    # --- yasam dongusu ---

    def baslat(self):
        if self._thread is not None and self._thread.is_alive():
            return self
        self._mav = mavutil.mavlink_connection(self.adres,
                                               source_system=self.sysid)
        self._baslangic = time.monotonic()
        self._dur_olayi.clear()
        self._thread = threading.Thread(target=self._dongu,
                                        name="sahte-pixhawk", daemon=True)
        self._thread.start()
        return self

    def dur(self):
        self._dur_olayi.set()
        thread, self._thread = self._thread, None
        if thread is not None:
            thread.join(timeout=2.0)
        if self._mav is not None:
            try:
                self._mav.close()
            finally:
                self._mav = None

    def __enter__(self):
        return self.baslat()

    def __exit__(self, *_):
        self.dur()
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--adres", default=VARSAYILAN_ADRES,
                    help="pymavlink baglanti dizesi (varsayilan: %(default)s)")
    ap.add_argument("--sysid", type=int, default=VARSAYILAN_SYSID)
    ap.add_argument("--senaryo", choices=SENARYOLAR, default="ucus")
    ap.add_argument("--irtifa", type=float, default=30.0,
                    help="bagil irtifa (m) — inis senaryosunda baslangic")
    ap.add_argument("--inis-suresi", type=float, default=20.0)
    ap.add_argument("--sure", type=float, default=0.0,
                    help="0 = Ctrl+C'ye kadar")
    args = ap.parse_args(argv)

    sp = SahtePixhawk(args.adres, sysid=args.sysid, senaryo=args.senaryo,
                      irtifa_m=args.irtifa, inis_suresi_s=args.inis_suresi)
    print(f"sahte pixhawk -> {args.adres} · senaryo={args.senaryo} "
          f"sysid={args.sysid} irtifa={args.irtifa} m")
    with sp:
        try:
            bitis = time.monotonic() + args.sure if args.sure > 0 else None
            while bitis is None or time.monotonic() < bitis:
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
    print("gonderilen:", sp.gonderilen)
    return 0


if __name__ == "__main__":
    sys.exit(main())
