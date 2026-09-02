"""FAZ B — PIXHAWK ON-UCUS DOGRULAYICISI KAPILARI (scripts/mavlink_dogrula.py).

NEDEN: Faz B'de gercek Pixhawk ilk kez baglanacak; "akislar yeterli hizda mi"
sorusunu goz karariyla degil MEKANIK verdiktle cevaplayan aracin kendisi
sinanmadan sahaya cikamaz (`KOD_VAR != KOSUYOR`). Testler GERCEK bilesenlerle
kosar: SahtePixhawk gercek MAVLink cerceveleri basar (UDP loopback), arac
gercek `udpin` dinleyicisiyle olcer; mock yok.

Kapilar (her biri neyi kilitledigini adiyla soyler):
  B1 varsayilan hizlar (5/2/1 Hz)  -> GECTI, exit 0, JSON rapor tam
  B2 konum 1 Hz                    -> GLOBAL_POSITION_INT DUSTU, exit 1
  B3 beklenen sysid 7, sahte 1     -> sysid uyusmazligi DUSTU, olcum YAPILMAZ
  B4 hic yayin yok                 -> HEARTBEAT zaman asimi DUSTU (kisa tavan)
  B5 yabanci sysid trafigi         -> sayilmaz, ayrica raporlanir; verdikt bozulmaz
  B6 sozlesme baglantisi           -> esikler/mesaj id'leri sozlesme ve pymavlink
                                      sabitlerinden; konum esigi tazelikten turetili
  B7 gecersiz --sysid              -> argparse hatasi (exit 2), olcum yok

Olcum penceresi: SahtePixhawk'in `Event.wait(0.02)` adimi Windows'ta ~31 ms
surer (olculdu), etkin konum hizi ~4,6 Hz'dir (nominal 5). 2 s pencerede sayim
8-9 -> 4,0-4,5 Hz, 4,0 esigine DEGER; 4 s pencerede 18-19 -> 4,5-4,75 Hz.
Bu yuzden GECTI beklenen kapilar 4 s pencereyle kosar (esik gevsetilmedi).
"""
import contextlib
import io
import json
import socket
import sys
import tempfile
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "scripts", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

try:
    from pymavlink import mavutil
except ImportError:  # pragma: no cover - kurulum kapisi
    mavutil = None

from karar_sozlesmesi import (MAVLINK_DOGRULAMA_SURESI_S,  # noqa: E402
                              MAVLINK_DURUM_ASGARI_HZ,
                              MAVLINK_HEARTBEAT_ASGARI_HZ,
                              MAVLINK_KONUM_ASGARI_HZ,
                              TELEMETRI_IRTIFA_TAZELIK_S)

if mavutil is not None:
    import mavlink_dogrula as md  # noqa: E402
    from sahte_pixhawk import YABANCI_SYSID, SahtePixhawk  # noqa: E402

SYSID = 1
YANLIS_SYSID = 7
OLCUM_SURESI_S = 4.0        # gerekce: modul dokstringi
KISA_OLCUM_S = 3.0          # DUSTU beklenen kapida pay gerekmez
ACK_TAVAN_S = 0.3           # sahte ACK vermez; bekleme kisaltilir
HEARTBEAT_TAVAN_S = 2.0


def _bos_port():
    """Loopback'te bos bir UDP portu sec (arac udpin, sahte udpout kullanir)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]
    finally:
        s.close()


@unittest.skipIf(mavutil is None, "pymavlink kurulu degil")
class OnUcusDogrulayici(unittest.TestCase):
    """Arac gercek UDP MAVLink akisiyla dogru verdikti veriyor mu."""

    def _sahte(self, port, **kw):
        sp = SahtePixhawk(f"udpout:127.0.0.1:{port}", **kw)
        self.addCleanup(sp.dur)
        return sp

    def _kos(self, port, *ek_arg):
        """main() ile CLI yolunu kos; (exit kodu, JSON rapor, stdout) dondur."""
        with tempfile.TemporaryDirectory() as d:
            json_yolu = Path(d) / "rapor.json"
            argv = ["--mavlink", f"udpin:127.0.0.1:{port}",
                    "--ack-tavan", str(ACK_TAVAN_S),
                    "--json", str(json_yolu)] + list(ek_arg)
            cikti = io.StringIO()
            with contextlib.redirect_stdout(cikti):
                kod = md.main(argv)
            rapor = json.loads(json_yolu.read_text(encoding="utf-8"))
        return kod, rapor, cikti.getvalue()

    # --- B1 ---
    def test_B1_varsayilan_hizlarda_GECTI_exit_0(self):
        port = _bos_port()
        with self._sahte(port):
            kod, rapor, cikti = self._kos(port, "--sysid", str(SYSID),
                                          "--sure", str(OLCUM_SURESI_S))
        self.assertEqual(kod, 0, f"exit 0 bekleniyordu:\n{cikti}")
        self.assertTrue(rapor["gecti"])
        self.assertEqual(rapor["dusme_nedenleri"], [])
        self.assertIn("VERDIKT: GECTI", cikti)

        hb = rapor["heartbeat"]
        self.assertTrue(hb["alindi"])
        self.assertEqual(hb["sysid"], SYSID)
        self.assertEqual(hb["autopilot"],
                         mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA)
        self.assertEqual(hb["type"], mavutil.mavlink.MAV_TYPE_FIXED_WING)
        self.assertEqual(hb["autopilot_ad"], "MAV_AUTOPILOT_ARDUPILOTMEGA")

        akislar = {a["mesaj"]: a for a in rapor["akislar"]}
        beklenen = {md.MESAJ_HEARTBEAT: MAVLINK_HEARTBEAT_ASGARI_HZ,
                    md.MESAJ_KONUM: MAVLINK_KONUM_ASGARI_HZ,
                    md.MESAJ_DURUM: MAVLINK_DURUM_ASGARI_HZ}
        self.assertEqual(set(akislar), set(beklenen), "uc akis da olculmeli")
        for ad, esik in beklenen.items():
            self.assertEqual(akislar[ad]["esik_hz"], esik)
            self.assertTrue(akislar[ad]["gecti"], f"{ad}: {akislar[ad]}")
            self.assertGreaterEqual(akislar[ad]["hz"], esik)
            self.assertGreater(akislar[ad]["sayi"], 0)

        # Istekler: iki akis SET_MESSAGE_INTERVAL ile istendi. D-403'ten beri
        # sahte Pixhawk her COMMAND_LONG'a gercek Pixhawk gibi COMMAND_ACK
        # ACCEPTED doner (parasut kapisi icin gerekti); arac bunu kaydeder.
        # Ilk surumde sahte cevap vermiyordu ve "ack None + en iyi caba"
        # kilitlenmisti — o kilit sahtenin eksigini olcuyordu, aracin degil.
        from pymavlink import mavutil as _mu
        istekler = {k["mesaj"]: k for k in rapor["istekler"]}
        self.assertEqual(set(istekler), {md.MESAJ_KONUM, md.MESAJ_DURUM})
        for k in istekler.values():
            self.assertTrue(k["gonderildi"])
            self.assertEqual(k["ack"], _mu.mavlink.MAV_RESULT_ACCEPTED,
                             "sahte Pixhawk COMMAND_ACK ACCEPTED dondurmeli")
        self.assertEqual(istekler[md.MESAJ_KONUM]["mesaj_id"],
                         mavutil.mavlink.MAVLINK_MSG_ID_GLOBAL_POSITION_INT)
        self.assertEqual(istekler[md.MESAJ_DURUM]["mesaj_id"],
                         mavutil.mavlink.MAVLINK_MSG_ID_EXTENDED_SYS_STATE)
        self.assertEqual(istekler[md.MESAJ_KONUM]["aralik_us"],
                         int(round(1e6 / MAVLINK_KONUM_ASGARI_HZ * 0.5)))
        self.assertEqual(istekler[md.MESAJ_DURUM]["aralik_us"],
                         int(round(1e6 / MAVLINK_DURUM_ASGARI_HZ * 0.5)))

    # --- B2 ---
    def test_B2_konum_1Hz_GLOBAL_POSITION_INT_DUSTU_exit_1(self):
        port = _bos_port()
        with self._sahte(port, konum_hz=1.0):
            kod, rapor, cikti = self._kos(port, "--sysid", str(SYSID),
                                          "--sure", str(KISA_OLCUM_S))
        self.assertEqual(kod, 1, f"exit 1 bekleniyordu:\n{cikti}")
        self.assertFalse(rapor["gecti"])
        self.assertIn("VERDIKT: DUSTU", cikti)
        akislar = {a["mesaj"]: a for a in rapor["akislar"]}
        self.assertFalse(akislar[md.MESAJ_KONUM]["gecti"])
        self.assertLess(akislar[md.MESAJ_KONUM]["hz"], MAVLINK_KONUM_ASGARI_HZ)
        # Yalniz konum dustu; diger akislar sozlesme ustunde (hata izole).
        self.assertTrue(akislar[md.MESAJ_HEARTBEAT]["gecti"])
        self.assertTrue(akislar[md.MESAJ_DURUM]["gecti"])
        self.assertEqual(len(rapor["dusme_nedenleri"]), 1)
        self.assertIn(md.MESAJ_KONUM, rapor["dusme_nedenleri"][0])

    # --- B3 ---
    def test_B3_beklenen_sysid_7_sahte_1_yayinlarsa_DUSTU(self):
        port = _bos_port()
        with self._sahte(port, sysid=SYSID):
            kod, rapor, cikti = self._kos(
                port, "--sysid", str(YANLIS_SYSID),
                "--sure", str(KISA_OLCUM_S),
                "--heartbeat-tavan", str(HEARTBEAT_TAVAN_S))
        self.assertEqual(kod, 1, f"exit 1 bekleniyordu:\n{cikti}")
        self.assertFalse(rapor["gecti"])
        hb = rapor["heartbeat"]
        self.assertFalse(hb["alindi"])
        self.assertEqual(hb["beklenen_sysid"], YANLIS_SYSID)
        self.assertIn(SYSID, [s for s, _c in hb["gorulen_kaynaklar"]],
                      "gorulen yanlis sysid raporlanmali (tani icin)")
        # Yanlis arac icin istek gonderilmez, olcum yapilmaz (fail-closed).
        self.assertEqual(rapor["istekler"], [])
        self.assertEqual(rapor["akislar"], [])
        self.assertIsNone(rapor["olcum"])
        self.assertTrue(any("sysid" in n for n in rapor["dusme_nedenleri"]),
                        rapor["dusme_nedenleri"])

    # --- B4 ---
    def test_B4_hic_yayin_yoksa_heartbeat_zaman_asimi_DUSTU(self):
        port = _bos_port()
        tavan = 1.0
        t0 = time.monotonic()
        kod, rapor, cikti = self._kos(port, "--sysid", str(SYSID),
                                      "--sure", str(KISA_OLCUM_S),
                                      "--heartbeat-tavan", str(tavan))
        gecen = time.monotonic() - t0
        self.assertEqual(kod, 1, f"exit 1 bekleniyordu:\n{cikti}")
        self.assertFalse(rapor["gecti"])
        self.assertFalse(rapor["heartbeat"]["alindi"])
        self.assertEqual(rapor["heartbeat"]["gorulen_kaynaklar"], [])
        self.assertEqual(rapor["akislar"], [])
        self.assertTrue(any("zaman asimi" in n
                            for n in rapor["dusme_nedenleri"]),
                        rapor["dusme_nedenleri"])
        # Arac tavanda vazgecer; olcum penceresine hic girmez (asilmaz).
        self.assertGreaterEqual(gecen, tavan * 0.9)
        self.assertLess(gecen, tavan + KISA_OLCUM_S,
                        "heartbeat yokken olcum penceresi beklenmemeli")

    # --- B5 ---
    def test_B5_yabanci_sysid_trafigi_sayilmaz_ama_raporlanir(self):
        """`yabanci` senaryosu sysid 99'dan da konum basar (G5 vekili)."""
        port = _bos_port()
        with self._sahte(port, senaryo="yabanci") as sp:
            kod, rapor, cikti = self._kos(port, "--sysid", str(SYSID),
                                          "--sure", str(OLCUM_SURESI_S))
            self.assertGreater(sp.gonderilen["yabanci_konum"], 0,
                               "on kosul: yabanci paket hic gonderilmedi")
        self.assertEqual(kod, 0, f"yabanci trafik verdikti bozmamali:\n{cikti}")
        self.assertNotIn(YABANCI_SYSID,
                         [s for s, _c in rapor["heartbeat"]["gorulen_kaynaklar"]],
                         "yabanci konum basar, heartbeat basmaz")
        yabanci = rapor["olcum"]["yabanci_kaynak_mesaj"]
        self.assertGreater(yabanci[md.MESAJ_KONUM], 0,
                           "yabanci kaynak mesajlari raporda gorunmeli")
        # Sayim yalniz beklenen sysid'den: yabanci dahil olsaydi konum hizi
        # ~2x olurdu (sahte her konumda bir de yabanci basar).
        akislar = {a["mesaj"]: a for a in rapor["akislar"]}
        konum_hz = akislar[md.MESAJ_KONUM]["hz"]
        toplam_hz = ((akislar[md.MESAJ_KONUM]["sayi"] + yabanci[md.MESAJ_KONUM])
                     / rapor["olcum"]["gercek_sure_s"])
        self.assertLess(konum_hz, toplam_hz * 0.75,
                        "yabanci konum paketleri sayima SIZDI")

    # --- B6 ---
    def test_B6_esikler_sozlesmeden_mesaj_idleri_pymavlinkten(self):
        akislar = {a["ad"]: a for a in md.akis_tanimlari()}
        m = mavutil.mavlink
        self.assertEqual(akislar[md.MESAJ_HEARTBEAT]["id"],
                         m.MAVLINK_MSG_ID_HEARTBEAT)
        self.assertEqual(akislar[md.MESAJ_KONUM]["id"],
                         m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT)
        self.assertEqual(akislar[md.MESAJ_DURUM]["id"],
                         m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE)
        self.assertEqual(akislar[md.MESAJ_HEARTBEAT]["asgari_hz"],
                         MAVLINK_HEARTBEAT_ASGARI_HZ)
        self.assertEqual(akislar[md.MESAJ_KONUM]["asgari_hz"],
                         MAVLINK_KONUM_ASGARI_HZ)
        self.assertEqual(akislar[md.MESAJ_DURUM]["asgari_hz"],
                         MAVLINK_DURUM_ASGARI_HZ)
        self.assertFalse(akislar[md.MESAJ_HEARTBEAT]["istenir"],
                         "HEARTBEAT istenmez (standart 1 Hz)")
        # Turetme: konum esigi = tazelik penceresinin Nyquist'i x 2 payi.
        nyquist_hz = 2.0 / TELEMETRI_IRTIFA_TAZELIK_S
        self.assertGreaterEqual(MAVLINK_KONUM_ASGARI_HZ, nyquist_hz,
                                "konum esigi tazelik penceresini dolduramaz")
        self.assertGreater(MAVLINK_DOGRULAMA_SURESI_S,
                           2.0 / MAVLINK_HEARTBEAT_ASGARI_HZ,
                           "pencere en yavas akistan en az 2 mesaj gormeli")

    # --- B7 ---
    def test_B7_gecersiz_sysid_argparse_hatasi(self):
        for kotu in ("0", "256"):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    md.main(["--mavlink", "udpin:127.0.0.1:0",
                             "--sysid", kotu])
            self.assertEqual(cm.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
