"""Direct RFD/MAVLink mode for the Windows YKI.

The old implementation intentionally exposed telemetry only. This module
keeps the YKI safety gates, but translates verified IHA CMD messages to raw
MAVLink COMMAND_LONG frames and translates the matching COMMAND_ACK back to
the NAVITAS ACK protocol. IKA commands are not sent over this Pixhawk-only
link.
"""
from __future__ import annotations

import math
import time
from numbers import Real

from mavlink_tunel import TunelLink, TUNEL_AKRAN_SESSIZLIK_S
from karar_sozlesmesi import ARM_DURUM_TAZELIK_S
from protocol import ACK_SONUC_KABUL, MESAJ_CMD, ack, decode, encode, heartbeat, oturum_dogrula
from iha_komut_alici import (
    ARM_DISARM_PARAM2_FORCE,
    CMD_FORCE_ARM,
    KOMUT_ADLARI, KOMUT_YAS_TAVANI_S, UCUS_MODLARI, CMD_MOD_PREFIX,
    mavlink_komut_tablosu, ucus_modu_komutu_mu,
)


class RadioTelemetry:
    def __init__(self, sysid=1, clock=time.monotonic):
        self.sysid, self.clock = sysid, clock
        self.messages = {}
        self.sequence = 0

    def accept(self, message):
        from pymavlink.dialects.v20 import ardupilotmega as mav
        if (message.get_srcSystem() != self.sysid
                or message.get_srcComponent() != mav.MAV_COMP_ID_AUTOPILOT1):
            return None
        kind = message.get_type()
        if kind == "BAD_DATA":
            return None
        if kind == "HEARTBEAT" and (
                message.type == mav.MAV_TYPE_GCS
                or message.autopilot == mav.MAV_AUTOPILOT_INVALID):
            return None
        self.messages[kind] = (message, self.clock())
        if kind != "HEARTBEAT":
            return None
        self.sequence += 1
        from pymavlink import mavutil
        fields = {
            "armed": bool(message.base_mode & mav.MAV_MODE_FLAG_SAFETY_ARMED),
            "pixhawk_canli": True,
        }
        mode = mavutil.mode_string_v10(message)
        if mode and all(c.isalnum() or c in "_-" for c in mode):
            fields["mod"] = mode

        def recent(kind):
            record = self.messages.get(kind)
            return (record[0] if record and
                    0 <= self.clock() - record[1] <= ARM_DURUM_TAZELIK_S
                    else None)

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
    """RFD900A byte link with a guarded ground-side Pixhawk command bridge."""

    TASIYICI_ADI = "mavlink_radyo"
    MISSION_PLANNER_FORCE_ARM = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.telemetry = RadioTelemetry(self.beklenen_arac_sysid, self.saat)
        self._son_heartbeat_t = None
        # One latest request per MAVLink command. Retries use the same NAVITAS
        # sequence, while a newer request replaces an old unacknowledged one.
        self._bekleyen_ack = {}

    def _komut_cevir(self, cmd):
        from pymavlink import mavutil
        m = self._m
        if cmd in KOMUT_ADLARI and not ucus_modu_komutu_mu(cmd):
            try:
                mav_cmd, param1 = mavlink_komut_tablosu()[cmd]
            except KeyError as exc:
                raise OSError(f"Pixhawk komutu desteklenmiyor: {cmd}") from exc
            param2 = (ARM_DISARM_PARAM2_FORCE
                      if cmd == CMD_FORCE_ARM else 0.0)
            return int(mav_cmd), float(param1), float(param2)
        if not ucus_modu_komutu_mu(cmd):
            raise OSError(
                f"Doğrudan radyo yalnız İHA uçuş komutlarını destekler: {cmd!r}")
        mode = cmd[len(CMD_MOD_PREFIX):]
        if mode not in UCUS_MODLARI:
            raise OSError(f"İzinli Pixhawk uçuş modu değil: {mode}")
        reverse = {str(name): int(number)
                   for number, name in mavutil.mode_mapping_acm.items()}
        if mode not in reverse:
            raise OSError(f"Pixhawk uçuş modu desteklenmiyor: {mode}")
        return (int(m.MAV_CMD_DO_SET_MODE),
                float(m.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED),
                float(reverse[mode]))

    def _komut_dogrula(self, data):
        try:
            message = decode(bytes(data))
        except (TypeError, ValueError, UnicodeDecodeError) as exc:
            raise OSError("Doğrudan radyo geçerli NAVITAS JSON CMD bekliyor") from exc
        if (not isinstance(message, dict)
                or message.get("type") != MESAJ_CMD
                or message.get("hedef") != "iha"):
            raise OSError(
                "Bu radyo bağlantısı yalnız hedef=iha CMD kabul eder; "
                "IKA komutları için ayrı IKA bağlantısı gerekir")
        cmd = message.get("cmd")
        if not isinstance(cmd, str):
            raise OSError("CMD adı geçersiz")
        seq = message.get("seq")
        if isinstance(seq, bool) or not isinstance(seq, int):
            raise OSError("CMD seq geçersiz")
        try:
            oturum = oturum_dogrula(message.get("oturum"))
        except (TypeError, ValueError) as exc:
            raise OSError("İHA komutu geçerli oturum kimliği taşımıyor") from exc
        damga = message.get("t")
        if (isinstance(damga, bool) or not isinstance(damga, Real)
                or not math.isfinite(float(damga))):
            raise OSError("İHA komutu geçerli zaman damgası taşımıyor")
        tavan = KOMUT_YAS_TAVANI_S.get(cmd)
        if tavan is None:
            self._komut_cevir(cmd)
            raise OSError(f"İHA komutu desteklenmiyor: {cmd}")
        yas = time.time() - float(damga)
        if yas < -0.5 or yas > float(tavan):
            raise OSError(f"İHA komutu bayat/gelecek zamanlı (yaş={yas:.3f}s)")
        mav_cmd, param1, param2 = self._komut_cevir(cmd)
        return message, cmd, seq, oturum, mav_cmd, param1, param2

    def _send_verified_command(self, verified, peer=None):
        message, cmd, seq, oturum, mav_cmd, param1, param2 = verified
        now = self.saat()
        with self._kilit:
            akran = self.akran
            if peer is not None:
                requested = (str(peer[0]), int(peer[1]))
                if akran is None or requested != akran:
                    raise OSError("MAVLink akranı doğrulanmadı")
            if akran is None:
                self._link_sayac["akran_yok"] += 1
                raise OSError("Pixhawk HEARTBEAT bekleniyor; komut gönderilmedi")
            if (self._son_heartbeat_t is None
                    or now - self._son_heartbeat_t > ARM_DURUM_TAZELIK_S):
                raise OSError("Pixhawk HEARTBEAT bayat; komut gönderilmedi")
            if (self._son_akran_t is not None
                    and now - self._son_akran_t > TUNEL_AKRAN_SESSIZLIK_S):
                raise OSError("MAVLink akranı sessiz; komut gönderilmedi")
            self._bekleyen_ack[mav_cmd] = {
                "seq": seq, "cmd": cmd, "oturum": oturum, "t": now,
            }
            paket = self._kodlayici.command_long_encode(
                self.beklenen_arac_sysid, 1, mav_cmd, 0,
                param1, param2, 0.0, 0.0, 0.0, 0.0, 0.0,
            ).pack(self._kodlayici)
            try:
                self.sock.sendto(paket, akran)
            except (ConnectionResetError, ConnectionRefusedError, OSError):
                self._bekleyen_ack.pop(mav_cmd, None)
                self._link_sayac["gonderim_hatasi"] += 1
                raise

    def send_mission_planner_force_arm(self, data, peer=None):
        """Send the Mission Planner-equivalent ArduPilot force-arm command."""
        self._kapali_mi()
        verified = self._komut_dogrula(data)
        if verified[1] != CMD_FORCE_ARM:
            raise OSError("Doğrudan force-arm yolu yalnız FORCE_ARM kabul eder")
        self._send_verified_command(verified, peer)

    def send(self, data, peer=None):
        """Translate one verified NAVITAS IHA CMD to MAVLink COMMAND_LONG."""
        self._kapali_mi()
        verified = self._komut_dogrula(data)
        if verified[1] == CMD_FORCE_ARM:
            self.send_mission_planner_force_arm(data, peer)
            return
        self._send_verified_command(verified, peer)

    def _ack_isle(self, message):
        from pymavlink import mavutil
        if (message.get_srcSystem() != self.beklenen_arac_sysid
                or message.get_srcComponent() not in (
                    0, int(self._m.MAV_COMP_ID_AUTOPILOT1), 1)):
            self._link_sayac["yabanci_mesaj"] += 1
            return
        try:
            mav_cmd = int(message.command)
            result = int(message.result)
        except (AttributeError, TypeError, ValueError):
            return
        pending = self._bekleyen_ack.pop(mav_cmd, None)
        if pending is None:
            self._link_sayac["yabanci_mesaj"] += 1
            return
        accepted = result == int(mavutil.mavlink.MAV_RESULT_ACCEPTED)
        response = ack(
            pending["seq"], "iha", MESAJ_CMD,
            ref_cmd=pending["cmd"],
            sonuc=ACK_SONUC_KABUL if accepted else "REJECTED",
        )
        response["oturum"] = pending["oturum"]
        if not accepted:
            response["neden"] = f"MAV_RESULT_{result}"
            response["aciklama"] = "Pixhawk COMMAND_ACK ACCEPTED dönmedi"
        self._teslim.append(encode(response))
        self._link_sayac["teslim_cerceve"] += 1

    def _datagram_isle(self, data, address):
        self._link_sayac["alinan_datagram"] += 1
        address = (str(address[0]), int(address[1]))
        if self.akran is not None and address != self.akran:
            if (self._son_akran_t is not None
                    and self.saat() - self._son_akran_t <= TUNEL_AKRAN_SESSIZLIK_S):
                self._link_sayac["akrandisi_datagram"] += 1
                return
            self._kalici = self._yeni_ayristirici()
            self.telemetry.messages.clear()
            self.akran = None
            self._son_heartbeat_t = None
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
            if msg.get_type() == "COMMAND_ACK":
                self._ack_isle(msg)
                continue
            if self.akran is None and msg.get_type() != "HEARTBEAT":
                continue
            snapshot = self.telemetry.accept(msg)
            if snapshot is not None:
                self.akran = address
                self._son_akran_t = self.saat()
                self._son_heartbeat_t = self.saat()
                self._teslim.append(encode(snapshot))
                self._link_sayac["teslim_cerceve"] += 1


def install(gui):
    """Install direct-radio transport while retaining the base safety gates."""
    gui.TunelLink = NativeRadioLink
    base = gui.YksArayuz

    class RadioYki(base):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.kok.title("NAVITAS YKI — RADYO MAVLINK / PC VIDEO")
            self._logla(
                "DOĞRUDAN RADYO: Pixhawk MAVLink → PC. Jetson gerekmiyor.",
                "yesil")
            self._logla(
                "İHA uçuş komutları COMMAND_LONG + Pixhawk ACK ile açık; "
                "taze heartbeat ve GUI güvenlik kilitleri korunuyor.",
                "mavi")
            self._logla(
                "IKA komutları bu Pixhawk-only radyo yolundan gönderilmez; "
                "IKA linki ayrıca bağlanmalıdır.",
                "sari")
            for widget in self.kok.winfo_children():
                self._transport_label(widget)

        def _transport_label(self, widget):
            try:
                text = str(widget.cget("text"))
                if "Taşıyıcı:" in text or "TASIYICI:" in text:
                    widget.config(
                        text="  RADYO MAVLink · Pixhawk ↔ YKI · "
                             "İHA komutları ACK'li · IKA ayrı link")
            except Exception:
                pass
            for child in widget.winfo_children():
                self._transport_label(child)

        def _mesaj_isle(self, message, address):
            super()._mesaj_isle(message, address)
            if message.get("kaynak") == "PIXHAWK_MAVLINK_RADYO":
                self._kanit_yaz("PIXHAWK_RADYO", telemetri=message)

    gui.YksArayuz = RadioYki
