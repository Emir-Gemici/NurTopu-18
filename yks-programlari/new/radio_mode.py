"""NEDEN: Jetson olmadan Pixhawk MAVLink telemetrisini YKI'de gostermek.

Bu uyarlayici sadece alir; ucus komutu, rota, algi kaniti veya ACK uretmez.
HEARTBEAT ic kaydi yalniz gercek otopilot heartbeat'i alindiginda olusur.
"""
from __future__ import annotations

import math
import time
from mavlink_tunel import TunelLink, TUNEL_AKRAN_SESSIZLIK_S
from karar_sozlesmesi import ARM_DURUM_TAZELIK_S
from protocol import encode, heartbeat


class RadioTelemetry:
    def __init__(self, sysid=1, clock=time.monotonic):
        self.sysid, self.clock = sysid, clock
        self.messages = {}
        self.sequence = 0

    def accept(self, message):
        from pymavlink.dialects.v20 import ardupilotmega as mav
        if message.get_srcSystem() != self.sysid or message.get_srcComponent() != mav.MAV_COMP_ID_AUTOPILOT1:
            return None
        kind = message.get_type()
        if kind == "BAD_DATA":
            return None
        if kind == "HEARTBEAT" and (message.type == mav.MAV_TYPE_GCS or message.autopilot == mav.MAV_AUTOPILOT_INVALID):
            return None
        self.messages[kind] = (message, self.clock())
        if kind != "HEARTBEAT":
            return None
        self.sequence += 1
        from pymavlink import mavutil
        fields = {"armed": bool(message.base_mode & mav.MAV_MODE_FLAG_SAFETY_ARMED), "pixhawk_canli": True}
        mode = mavutil.mode_string_v10(message)
        if mode and all(c.isalnum() or c in "_-" for c in mode):
            fields["mod"] = mode

        def recent(kind):
            record = self.messages.get(kind)
            return record[0] if record and 0 <= self.clock() - record[1] <= ARM_DURUM_TAZELIK_S else None

        position = recent("GLOBAL_POSITION_INT")
        gps = recent("GPS_RAW_INT")
        if position is not None:
            fields["alt"] = position.relative_alt / 1000.0
            fields["hiz"] = math.hypot(position.vx, position.vy) / 100.0
            if position.hdg != 65535:
                fields["yon"] = position.hdg / 100.0
        if gps is not None:
            fields["gps_fix"] = int(gps.fix_type)
            if gps.satellites_visible != 255:
                fields["uydu"] = int(gps.satellites_visible)
            if gps.fix_type >= 3:
                source = position if position is not None else gps
                fields["lat"], fields["lon"] = source.lat / 1e7, source.lon / 1e7
        power = recent("SYS_STATUS")
        if power is not None:
            if 0 < power.voltage_battery < 65535:
                fields["bat"] = power.voltage_battery / 1000.0
            if 0 <= power.battery_remaining <= 100:
                fields["bat_yuzde"] = int(power.battery_remaining)
        result = heartbeat("iha", seq=self.sequence, **fields)
        result["kaynak"] = "PIXHAWK_MAVLINK_RADYO"
        return result


class NativeRadioLink(TunelLink):
    TASIYICI_ADI = "mavlink_radyo"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telemetry = RadioTelemetry(self.beklenen_arac_sysid, self.saat)

    def send(self, data, peer=None):
        raise OSError("Radyo izleme kipi: uçuş komutları Mission Planner'dan verilir")

    def _datagram_isle(self, data, address):
        self._link_sayac["alinan_datagram"] += 1
        address = (str(address[0]), int(address[1]))
        # A second sender cannot contaminate the current parser/state.
        if self.akran is not None and address != self.akran:
            if self._son_akran_t is not None and self.saat() - self._son_akran_t <= TUNEL_AKRAN_SESSIZLIK_S:
                self._link_sayac["akrandisi_datagram"] += 1
                return
            self._kalici = self._yeni_ayristirici()
            self.telemetry.messages.clear()
            self.akran = None
        try:
            messages = self._kalici.parse_buffer(data) or []
        except Exception:
            self._link_sayac["cozum_hatasi"] += 1
            self._kalici = self._yeni_ayristirici()
            return
        for msg in messages:
            if msg.get_type() == "BAD_DATA":
                self._link_sayac["cozum_hatasi"] += 1
                continue
            self._link_sayac["mavlink_paket"] += 1
            if self.akran is None and msg.get_type() != "HEARTBEAT":
                continue
            snapshot = self.telemetry.accept(msg)
            if snapshot is not None:
                self.akran = address
                self._son_akran_t = self.saat()
                self._teslim.append(encode(snapshot))
                self._link_sayac["teslim_cerceve"] += 1


def install(gui):
    """Paketin acik radyo kipine uygula; kaynak GUI veya eski kipler degismez."""
    gui.TunelLink = NativeRadioLink
    base = gui.YksArayuz

    class RadioYki(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.kok.title("NAVITAS YKİ — RADYO TELEMETRİ / PC VİDEO")
            self._logla("DOĞRUDAN RADYO: Pixhawk MAVLink → PC. Jetson gerekmiyor. Video ayrıca açılır.", "yesil")
            self._logla("Bu sürüm telemetriyi izler. Uçuş komutları Mission Planner'dan verilir.", "mavi")
            for widget in self.kok.winfo_children():
                self._transport_label(widget)
            self._disable_flight_controls()

        def _transport_label(self, widget):
            try:
                text = str(widget.cget("text"))
                if "Taşıyıcı:" in text:
                    widget.config(text="  RADYO MAVLink · Pixhawk → PC · Video: ayrı bağlantı · Uçuş kumandası: Mission Planner")
            except Exception:
                pass
            for child in widget.winfo_children():
                self._transport_label(child)

        def _disable_flight_controls(self):
            for name in ("btn_arm", "btn_firlat", "btn_iha_indi", "btn_parasut", "btn_ika_go", "btn_hb", "btn_rtl", "btn_land", "btn_mod", "btn_fda_gorev", "btn_onay"):
                button = getattr(self, name, None)
                if button is not None:
                    button.config(state="disabled")

        def _durum_tazele(self):
            super()._durum_tazele()
            self._disable_flight_controls()

        def _ham_gonder(self, message):
            self._logla("Bu sürümde uçuş komutunu Mission Planner'dan verin.", "sari")
            return False

        def _mesaj_isle(self, message, address):
            super()._mesaj_isle(message, address)
            if message.get("kaynak") == "PIXHAWK_MAVLINK_RADYO":
                self._kanit_yaz("PIXHAWK_RADYO", telemetri=message)

    gui.YksArayuz = RadioYki
