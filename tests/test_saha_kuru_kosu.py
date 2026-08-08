"""T23 KAPISI: saha kuru kosusunun GERCEKTEN olctugunu kanitla.

NEDEN ayri gorev: T22 tek basina "bos kapi" riski tasir. D-15'te anayasa madde 4
kapisinin hicbir zaman calismadigi (sahte gecis) ortaya cikti; ayni hata burada
tekrarlanmamali. Bir kosucunun "4 halka dustu" demesi yetmez — HANGI halkanin,
HANGI sebeple dustugu ve o halka onarilinca sonucun DEGISTIGI gosterilmelidir.

Iki bolum:
  1. Pozitif kontrol — D-22'nin dort kopuklugu ISIM ISIM yakalaniyor mu?
  2. Mutasyon kanidi — her kopukluk sahte bir kok agacinda tatmin edilince o
     halka GECTI'ye doner ve DIGER UCU DEGISMEZ. Bu, halkalarin birbirine
     sizmadigini kanitlar; tek bir "her seye GECTI diyen" kod yolu olsaydi
     mutasyon testi dortunu birden cevirirdi.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "scripts", KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import saha_kuru_kosu as sk


# D-22'nin dort kopuklugu: halka adi -> (beklenen durum, kanit kaydi)
DORT_KOPUKLUK = {
    "aktarim": (sk.SAHIPSIZ, "jetson_paket'te haberlesme kodu yok"),
    "hedef_konumu": (sk.SAHIPSIZ, "HB yalniz Gazebo meta.txt'ten"),
    "surus_izni": (sk.DUSTU, "IHA_LANDED uretici yalniz simulation/"),
    "motor": (sk.SAHIPSIZ, "gercek motor surucusu yok"),
}


def _sahte_kok(tmp: Path) -> Path:
    """Dort kopuklugun HICBIRINI tatmin etmeyen, en kucuk gecerli agac."""
    (tmp / "jetson_paket" / "kod").mkdir(parents=True)
    (tmp / "jetson_paket" / "kod" / "requirements_rpi.txt").write_text(
        "ultralytics\nopencv-python\nnumpy\n", encoding="utf-8")
    (tmp / "simulation" / "scripts").mkdir(parents=True)
    (tmp / "simulation" / "scripts" / "ika_nav.py").write_text(
        'import subprocess\n'
        'def send_vel(r, l):\n'
        '    subprocess.run(["gz", "topic", "-p", "x"], capture_output=True)\n',
        encoding="utf-8")
    (tmp / "simulation" / "scripts" / "iha_haritala.py").write_text(
        'import argparse\n'
        'def main():\n'
        '    ap = argparse.ArgumentParser()\n'
        '    ap.add_argument("--htab", type=float)\n',
        encoding="utf-8")
    (tmp / "simulation" / "scripts" / "navitas_sim.py").write_text(
        'def yayinla(sender):\n'
        '    seq, acked = sender.send_iha_landed(repeat=8)\n',
        encoding="utf-8")
    (tmp / "config").mkdir()
    (tmp / "config" / "model_registry.json").write_text(json.dumps({
        "schema_version": 1, "default_profile": "competition",
        "profiles": {"competition": {"path": "models/x.pt",
                                     "classes": {"0": "traversable", "1": "blocked"}}},
    }), encoding="utf-8")
    (tmp / "codes").mkdir()
    return tmp


def _saha_paketini_doldur(kok: Path) -> None:
    """aktarim halkasinin MESRU onarimi: moduller gerekli API'yi GERCEKTEN tanimlar.

    Bos stub yazmak yetmez — denetim, dosya adi varliginin halkayi gecirdigini
    gosterdi; simdi sembol denetimi var.
    """
    kod = kok / "jetson_paket" / "kod"
    (kod / "protocol.py").write_text(
        "def open_route(road, conf, waypoints=None, ref_xy=None, seq=None):\n"
        "    return {}\n"
        "def rota_yok(sebep, detay=None, seq=None):\n"
        "    return {}\n"
        "def iha_landed(seq=None):\n"
        "    return {}\n"
        "def encode(msg):\n"
        "    return b''\n"
        "def decode(line):\n"
        "    return {}\n",
        encoding="utf-8")
    (kod / "iha_sender.py").write_text(
        "class IhaSender:\n"
        "    def __init__(self, link, peers=None):\n"
        "        self.link = link\n"
        "    def send_open_route(self, *a, **k):\n"
        "        return 1, set()\n"
        "    def send_no_route(self, *a, **k):\n"
        "        return 1, set()\n",
        encoding="utf-8")
    (kod / "link.py").write_text(
        "class UDPLink:\n"
        "    def send(self, veri, adr=None):\n"
        "        pass\n"
        "class SerialLink:\n"
        "    def send(self, veri, adr=None):\n"
        "        pass\n",
        encoding="utf-8")
    (kod / "requirements_rpi.txt").write_text(
        "ultralytics\nopencv-python\nnumpy\npyserial\n", encoding="utf-8")


def _dort_halkayi_kos(kok: Path) -> dict[str, str]:
    """Dort kopukluk halkasini verilen kok agacinda kos, durumlarini dondur."""
    rapor = sk.Rapor()
    sk.halka_hedef(rapor, kok)
    sk.halka_aktarim(rapor, kok)
    sk.halka_surus_izni(rapor, kok)
    sk.halka_motor(rapor, kok)
    return {s["halka"]: s["durum"] for s in rapor.satirlar}


class PozitifKontrolTests(unittest.TestCase):
    """Gercek depoda dort kopukluk ISIM ISIM yakalaniyor mu?"""

    @classmethod
    def setUpClass(cls):
        cls.rapor = sk.kosuyu_yap(kare_yolu=None, atla_cikarim=True)
        cls.durumlar = {s["halka"]: s for s in cls.rapor.satirlar}

    def test_sozlesmedeki_on_halkanin_hepsi_raporlaniyor(self):
        self.assertEqual(list(sk.HALKALAR), [s["halka"] for s in self.rapor.satirlar])

    def test_dort_kopukluk_isim_isim_yakalaniyor(self):
        for halka, (beklenen, aciklama) in DORT_KOPUKLUK.items():
            with self.subTest(halka=halka):
                self.assertIn(halka, self.durumlar, f"{halka} raporlanmadi")
                self.assertEqual(
                    beklenen, self.durumlar[halka]["durum"],
                    f"{halka} ({aciklama}) beklenen {beklenen} degil")

    def test_iha_landed_ureticisi_yalniz_simulasyonda(self):
        detay = self.durumlar["surus_izni"]["detay"]
        self.assertEqual([], detay["saha_ureticileri"],
                         "saha yolunda IHA_LANDED uretici cikti — D-22 kapanmis olabilir")
        self.assertTrue(any(u.startswith("simulation/") for u in detay["tum_ureticiler"]))

    def test_aktarim_kutuphanesi_calisiyor_ama_paket_eksik(self):
        """Kopukluk PAKETLEMEDE; comms kutuphanesi loopback'te gercekten calisiyor."""
        detay = self.durumlar["aktarim"]["detay"]
        self.assertEqual(["iha_sender.py", "link.py", "protocol.py"],
                         detay["eksik_moduller"])
        dogrulama = detay["depo_comms_loopback"]
        self.assertIsInstance(dogrulama, dict,
                              f"loopback probu kosmadi: {dogrulama}")
        self.assertEqual(["ika"], dogrulama["ack"])
        self.assertTrue(dogrulama["alindi"])

    def test_kosu_dusen_halkada_durmuyor(self):
        """Dusen halkadan SONRAKI halkalar da raporlanmali (ATLANDI degil, kosulmus)."""
        sonrakiler = [s["durum"] for s in self.rapor.satirlar
                      if s["halka"] in ("aktarim", "surus_izni", "motor")]
        self.assertNotIn(sk.ATLANDI, sonrakiler,
                         "ilk dususten sonra halkalar atlanmis — tam tablo uretilmiyor")

    def test_cikis_kodu_kopuk_varken_sifir_degil(self):
        kopuk = [s for s in self.rapor.satirlar
                 if s["durum"] in (sk.DUSTU, sk.SAHIPSIZ)]
        self.assertGreaterEqual(len(kopuk), 4)


class MutasyonKanitiTests(unittest.TestCase):
    """Her kopukluk tek tek tatmin edilince YALNIZ o halka GECTI'ye donmeli."""

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.kok = _sahte_kok(Path(self._tmp.name))
        self.taban = _dort_halkayi_kos(self.kok)

    def tearDown(self):
        self._tmp.cleanup()

    def test_taban_agacinda_dort_kopukluk_da_var(self):
        for halka, (beklenen, _) in DORT_KOPUKLUK.items():
            with self.subTest(halka=halka):
                self.assertEqual(beklenen, self.taban[halka])

    def _mutasyonu_dogrula(self, onarilan: str):
        yeni = _dort_halkayi_kos(self.kok)
        self.assertEqual(sk.GECTI, yeni[onarilan],
                         f"{onarilan} onarildi ama hala {yeni[onarilan]}")
        for halka in DORT_KOPUKLUK:
            if halka == onarilan:
                continue
            with self.subTest(degismemeli=halka):
                self.assertEqual(
                    self.taban[halka], yeni[halka],
                    f"{onarilan} onarilinca {halka} de degisti — halkalar sizisiyor")

    def test_aktarim_onarilinca_yalniz_aktarim_gecer(self):
        """Onarim = modullerin GERCEKTEN API tanimlamasi; bos stub yetmez."""
        _saha_paketini_doldur(self.kok)
        self._mutasyonu_dogrula("aktarim")

    def test_hedef_konumu_onarilinca_yalniz_o_gecer(self):
        """Onarim SAHA dizininde olmali — simulation/ sahip olamaz (§11.1/1)."""
        (self.kok / "codes" / "saha_giris.py").write_text(
            'import argparse\n'
            'def main():\n'
            '    ap = argparse.ArgumentParser()\n'
            '    ap.add_argument("--hb", type=str)\n',
            encoding="utf-8")
        self._mutasyonu_dogrula("hedef_konumu")

    def test_surus_izni_onarilinca_yalniz_o_gecer(self):
        (self.kok / "drone").mkdir(exist_ok=True)
        (self.kok / "drone" / "rpi_yayin.py").write_text(
            'def inis_bildir(sender):\n'
            '    sender.send_iha_landed(repeat=8)\n',
            encoding="utf-8")
        self._mutasyonu_dogrula("surus_izni")

    def test_motor_onarilinca_yalniz_o_gecer(self):
        """Onarim SAHA dizininde, surucu import'u + motor fonksiyonu birlikte."""
        (self.kok / "drone").mkdir(exist_ok=True)
        (self.kok / "drone" / "motor_surucu.py").write_text(
            'import serial\n'
            'def send_vel(sag, sol):\n'
            '    serial.Serial("/dev/ttyACM0").write(b"v")\n',
            encoding="utf-8")
        self._mutasyonu_dogrula("motor")


class DenetimRegresyonTests(unittest.TestCase):
    """2026-08-07 bagimsiz denetiminin bulduğu ALTI kusuru kalici olarak kilitle.

    Hepsi ayni sinifin ornegiydi: bir halkanin "onarildi" gorunmesi icin GERCEK
    bir saha yetenegi degil, ucuz bir yan etki (yorum satiri, bos dosya, config
    kaydi, simulation/ altinda bir bayrak) yetiyordu.
    """

    def setUp(self):
        self._tmp = TemporaryDirectory()
        self.kok = _sahte_kok(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def _durum(self, halka: str, fn) -> str:
        rapor = sk.Rapor()
        fn(rapor, self.kok)
        return rapor.durum(halka)

    # ── motor ────────────────────────────────────────────────────────────
    def test_motor_yorum_satiri_halkayi_gecirmez(self):
        """Kusuru ITIRAF eden bir yorum, kusuru onarilmis gosteremez."""
        (self.kok / "drone").mkdir(exist_ok=True)
        (self.kok / "drone" / "not.py").write_text(
            '# TODO FAZ 6: gercek surucu (serial / PWM / mavlink) buraya gelecek, henuz YOK\n'
            'def send_vel(r, l):\n'
            '    raise NotImplementedError\n',
            encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("motor", sk.halka_motor))

    def test_motor_can_altdizgisi_masum_kelimede_eslesmez(self):
        """'CAN' tokeni 'scan'/'canli' gibi kelimelerde eslesmemeli."""
        (self.kok / "drone").mkdir(exist_ok=True)
        (self.kok / "drone" / "tarama.py").write_text(
            '# alani scan ederiz, canli yayin surer, significant fark yok\n'
            'def motor_durumu():\n'
            '    return "bos"\n',
            encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("motor", sk.halka_motor))

    def test_motor_surucu_importu_tek_basina_yetmez(self):
        """comms/link.py `import serial` yapar ama TELSIZ tasiyicisidir, motor degil."""
        (self.kok / "comms").mkdir(exist_ok=True)
        (self.kok / "comms" / "link.py").write_text(
            'import serial\n'
            'class SerialLink:\n'
            '    def send(self, veri, adr=None):\n'
            '        pass\n',
            encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("motor", sk.halka_motor))

    def test_motor_simulation_altindaki_surucu_sahip_sayilmaz(self):
        (self.kok / "simulation" / "scripts" / "ika_nav.py").write_text(
            'import serial\n'
            'def send_vel(r, l):\n'
            '    serial.Serial("/dev/ttyACM0").write(b"v")\n',
            encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("motor", sk.halka_motor))

    # ── aktarim ──────────────────────────────────────────────────────────
    def test_aktarim_bos_stub_dosyalar_halkayi_gecirmez(self):
        kod = self.kok / "jetson_paket" / "kod"
        for ad in ("protocol.py", "iha_sender.py", "link.py"):
            (kod / ad).write_text("# saha paketine tasindi\n", encoding="utf-8")
        (kod / "requirements_rpi.txt").write_text(
            "ultralytics\nopencv-python\nnumpy\npyserial\n", encoding="utf-8")
        rapor = sk.Rapor()
        sk.halka_aktarim(rapor, self.kok)
        self.assertEqual(sk.SAHIPSIZ, rapor.durum("aktarim"))
        eksik = rapor.satirlar[0]["detay"]["eksik_semboller"]
        self.assertIn("protocol.py", eksik)
        self.assertIn("iha_sender.py", eksik)

    def test_aktarim_loopback_alani_saha_paketini_olcmedigini_soyluyor(self):
        """Loopback DEPO comms/'u olcer; alan adi bunu gizlememeli."""
        rapor = sk.Rapor()
        sk.halka_aktarim(rapor, self.kok)
        detay = rapor.satirlar[0]["detay"]
        self.assertIn("depo_comms_loopback", detay)
        self.assertNotIn("loopback_dogrulamasi", detay)

    # ── hedef_konumu ─────────────────────────────────────────────────────
    def test_hedef_atil_3_sinifli_profil_halkayi_gecirmez(self):
        """Etkin olmayan deneysel bir profil uretimde hedefi gorunur kilmaz."""
        kayit = self.kok / "config" / "model_registry.json"
        veri = json.loads(kayit.read_text(encoding="utf-8"))
        veri["profiles"]["deney_v99"] = {
            "path": "models/deney.pt",
            "classes": {"0": "traversable", "1": "blocked", "2": "hedef"},
        }
        kayit.write_text(json.dumps(veri), encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("hedef_konumu", sk.halka_hedef))

    def test_hedef_simulation_altindaki_hb_bayragi_gecirmez(self):
        yol = self.kok / "simulation" / "scripts" / "iha_haritala.py"
        yol.write_text(
            'import argparse\n'
            'def main():\n'
            '    ap = argparse.ArgumentParser()\n'
            '    ap.add_argument("--hb", type=str)\n',
            encoding="utf-8")
        self.assertEqual(sk.SAHIPSIZ, self._durum("hedef_konumu", sk.halka_hedef))

    def test_hedef_etkin_profil_3_sinifliysa_gecer(self):
        kayit = self.kok / "config" / "model_registry.json"
        veri = json.loads(kayit.read_text(encoding="utf-8"))
        veri["profiles"]["competition"]["classes"] = {
            "0": "traversable", "1": "blocked", "2": "hedef"}
        kayit.write_text(json.dumps(veri), encoding="utf-8")
        self.assertEqual(sk.GECTI, self._durum("hedef_konumu", sk.halka_hedef))

    # ── kamera ───────────────────────────────────────────────────────────
    def test_depo_disi_kare_yolu_kosuyu_cokertmez(self):
        """--kare ile depo disi/goreli yol verilince ValueError atmamali."""
        with TemporaryDirectory() as disarisi:
            kare = Path(disarisi) / "kare.jpg"
            import numpy as np
            cv2 = __import__("cv2")
            cv2.imwrite(str(kare), np.zeros((32, 32, 3), np.uint8))
            rapor = sk.Rapor()
            durum, okunan = sk.halka_kamera(rapor, kare)   # istisna ATMAMALI
            self.assertIsNotNone(okunan)
            self.assertEqual(str(kare), rapor.satirlar[0]["detay"]["kare"])

    # ── surus izni probu ─────────────────────────────────────────────────
    def test_surus_kapisi_probu_gercekten_olcuyor(self):
        """Prob uc gozlemi de yapmali: bos kapali · yalniz IKA_GO kapali · ikisi acik."""
        gozlem = sk._surus_kapisi_probu()
        self.assertNotIn("hata", gozlem, f"prob kosamadi: {gozlem}")
        self.assertTrue(gozlem["bos_kapali"])
        self.assertTrue(gozlem["ika_go_alindi"],
                        "IKA_GO alicida islenmedi — prob hicbir sey olcmuyor")
        self.assertTrue(gozlem["yalniz_ika_go_kapali"],
                        "tek latch ile kapi acildi — surus kapisi gevsemis")
        self.assertTrue(gozlem["iha_landed_alindi"])
        self.assertTrue(gozlem["iki_latch_ile_acik"])
        self.assertTrue(gozlem["prob_gecerli"])


class OlcekHalkasiTests(unittest.TestCase):
    """olcek halkasi METIN aramasiyla degil, FONKSIYON imzasiyla karar vermeli.

    Bu, gelistirme sirasinda gercekten yasanan bir yanlis pozitiftir: duz grep
    "irtifa"/"fov"/"mpp" kelimelerini costmap_path_finder.py'nin YORUMLARINDA
    bulup halkayi GECTI isaretliyordu.
    """

    def test_yorumda_gecen_kelimeler_halkayi_gecirmez(self):
        with TemporaryDirectory() as t:
            kok = Path(t)
            (kok / "codes").mkdir()
            (kok / "codes" / "sahte.py").write_text(
                '"""irtifa ve FOV bilgisinden mpp turetilmelidir (yapilmadi)."""\n'
                '# mpp = irtifa * fov  <- TODO\n'
                'def bir_sey():\n'
                '    return 1\n',
                encoding="utf-8")
            self.assertIsNone(sk._irtifadan_mpp_ureticisi_bul(kok))

    def test_gercek_fonksiyon_halkayi_gecirir(self):
        with TemporaryDirectory() as t:
            kok = Path(t)
            (kok / "codes").mkdir()
            (kok / "codes" / "olcek.py").write_text(
                'def mpp_irtifadan(irtifa_m, fov_deg, genislik_px):\n'
                '    import math\n'
                '    return 2 * irtifa_m * math.tan(math.radians(fov_deg / 2)) / genislik_px\n',
                encoding="utf-8")
            bulunan = sk._irtifadan_mpp_ureticisi_bul(kok)
            self.assertIsNotNone(bulunan)
            self.assertIn("olcek.py", bulunan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
