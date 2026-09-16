"""NEDEN: Kuru koşu yalnız üç dosya adı ve birkaç AST sembolü görerek halka
8'i geçirebilir. Jetson paketinin gerçek yayıncı bağımlılıklarını taşıdığını,
kanonik kaynaklardan ayrışmadığını ve izole dizinden import edildiğini kanıtlar.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PAKET = KOK / "jetson_paket" / "kod"
BETIKLER = KOK / "scripts"
if str(BETIKLER) not in sys.path:
    sys.path.insert(0, str(BETIKLER))

from jetson_paket_hazirla import KOPYALAR


class JetsonCommsPaketiTests(unittest.TestCase):
    def test_paket_kopyalari_kanonik_kaynaklarla_birebir(self):
        # ⚠ SAYI BILEREK CIVILIDIR: pakete dosya eklemek/cikarmak SESSIZ
        # olmamalidir. T103'te 9 -> 10 oldu; eklenen
        # `config/model_registry.json`dur (REVIEW_LOG D-178). Bu kapi
        # degisikligi YAKALADI ve dogru davrandi — gevsetilmedi, GUNCELLENDI.
        # T83 onariminda 10 -> 11: eklenen `codes/arac_maskesi.py`dir (olcek
        # kahininin 3. katmani; pakette yokken kahin SESSIZCE None donuyordu).
        # T202/D-352'de 11 -> 14. Ucu de kilavuzun KULLANDIGI ama kurulum
        # blogunun TASIMADIGI dosyalardi; 30 Agustos Jetson Q8 testinde saha
        # gunu cokerlerdi:
        #   · codes/model_registry.py    -> derlenen .engine KAYDEDILEMEZ,
        #     model_kayit_dogrula fail-closed doner, MODEL YUKLENMEZ
        #     (T103/D-177 ile birebir ayni sinif kusur)
        #   · dataset/karisim_arena.yaml -> INT8/Q8 KALIBRASYON dosyasi;
        #     `int8=True data=...` derlemesi bunsuz kosmaz
        #   · codes/kamera_dogrula.py    -> DEPODA HIC YOKTU, yalniz pakette
        #     duruyordu (oksuz); kanonik kaynak artik codes/ altindadir
        #   · comms/iha_komut_alici.py  -> Faz B (D-403): YKS'nin PARACHUTE/ARM
        #     komutlarini Pixhawk'a aktaran Jetson sureci (D-393'un IHA yarisi);
        #     pakette yoksa sahada parasut yedegi ACK'siz kalir
        # D-404'te 15 -> 17 (Faz B, donanim-oncesi kapanis):
        #   · comms/seri_hub.py         -> SiK 433 MHz kipinde /dev/ttyUSB0 tek
        #     sahipli; hub olmadan uc surec ayni portu acamaz (CONTRACTS 7.5),
        #     navitas-seri-hub.service ExecStart'i bu dosyayi bekler
        #   · scripts/mavlink_dogrula.py -> jetson_baslat.sh --kapi on-ucus
        #     kapisi; paket tasimayinca --kapi HATA ile durur (FAZ_B §1)
        # Gorev K'da 17 -> 18 (SAHA_HAZIRLIK_PLANI_20260903 §1.4):
        #   · scripts/kamera_koprusu.py -> Jetson Nano'da RPi HQ (IMX477, CSI)
        #     yalniz GStreamer nvarguscamerasrc ile okunur, o da yalniz SISTEM
        #     Python 3.6 + sistem OpenCV'de var; rpi_inference (Py>=3.8 venv)
        #     kamerayi dogrudan acamaz. navitas-kamera-koprusu.service bu
        #     dosyayi bekler; paket tasimayinca CSI kameradan kare GELMEZ.
        # D-431'de 18 -> 21 (7 Eylul 2026, Jetson paketi birlestirme): kart Jetson
        # NANO degil ORIN NANO 4GB (JetPack 7.2.1, Py 3.12) cikti; Nano kurulum
        # belgesi/betikleri bu kartta gecersiz. Pakete alinanlar (jetson_paket/ KOKU):
        #   · JETSON_ORIN_NANO_KURULUM.md  -> kapi kapi kurulum tutanagi (olculdu)
        #   · orin_nano_root_kurulum.sh    -> apt nvidia-jetpack, swap, gruplar, nvpmodel
        #   · orin_nano_venv_kurulum.sh    -> ~/venv312 + torch cu130 + ultralytics
        # Kapi yine GEVSETILMEDI, gerekceyle GUNCELLENDI.
        # T228'de 21 -> 22 (10 Eylul 2026, D-443 MK15 video hatti):
        #   · scripts/isaretli_gosterici.py -> T227 isaretli yayinini tam ekran
        #     DP->HDMI->SIYI donusturucuye (x11/drm) ya da yedek RTSP'ye verir;
        #     kamera_koprusu'nu import eder (ikisi de ~/navitas/scripts/). Pakette
        #     yoksa GOSTERICI_KIP=x11 autostart'i `No such file` ile olurdu.
        # Tunel on kaydinda 22 -> 24 (16 Eylul 2026, CONTRACTS §7.6):
        #   · comms/mavlink_tunel.py -> KIP=tunel'de navitas-seri-hub `--tunel` onu
        #     IMPORT eder; pakette yoksa hub ImportError + Restart=always dongusu
        #   · scripts/sik_rf_olc.py  -> K8a/K8b gercek donanim olcumunun hava yanki
        #     ucu (~/navitas/scripts/); pakette yoksa K8 sahada KOSULAMAZ
        # Kapi yine GEVSETILMEDI, gerekceyle GUNCELLENDI.
        self.assertEqual(24, len(KOPYALAR),
                         "paket kopya sozlesmesi 24 dosya olmali "
                         "(19 .py + karisim_arena.yaml + config/model_registry.json + "
                         "Orin Nano belgesi + 2 kurulum betigi · "
                         "T103/T83/T202/D-403/D-404/Gorev K/D-431/T228/§7.6)")
        for kaynak, hedef in KOPYALAR.items():
            with self.subTest(hedef=hedef.name):
                self.assertTrue(hedef.is_file(), f"paket dosyasi yok: {hedef}")
                self.assertEqual(kaynak.read_bytes(), hedef.read_bytes(),
                                 f"paket kopyasi bayat: {hedef.name}")

    def test_jetson_fps_kanonigi_scripts_altindadir(self):
        """Calistirilabilir repo betigi kanonik, paket dosyasi turetilmis aynadir."""
        self.assertEqual(
            PAKET / "jetson_fps.py",
            KOPYALAR.get(KOK / "scripts" / "jetson_fps.py"),
        )

    def test_pymavlink_ve_pyserial_paket_bagimliligi(self):
        satirlar = {
            satir.strip().lower()
            for satir in (PAKET / "requirements_rpi.txt").read_text(
                encoding="utf-8").splitlines()
            if satir.strip() and not satir.lstrip().startswith("#")
        }
        self.assertIn("pyserial", satirlar)
        self.assertIn("pymavlink", satirlar)

    def test_uretim_yayincisi_pymavlink_olmadan_izole_import_edilir(self):
        kod = (
            "import pathlib,sys; "
            f"p=pathlib.Path({str(PAKET)!r}).resolve(); "
            "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
            "import iha_inis_yayinci as y; "
            "assert pathlib.Path(y.__file__).resolve().parent == p; "
            "assert callable(y.iha_inisini_yayinla); "
            "print('JETSON_COMMS_IMPORT=OK')"
        )
        sonuc = subprocess.run(
            [sys.executable, "-B", "-c", kod], cwd=PAKET,
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, sonuc.returncode,
                         f"stdout={sonuc.stdout}\nstderr={sonuc.stderr}")
        self.assertIn("JETSON_COMMS_IMPORT=OK", sonuc.stdout)

    def test_mavlink_tunel_pymavlink_yuklenmeden_izole_import_edilir(self):
        """§7.6: paket dizininden TEK BASINA `import mavlink_tunel` (ve onu import
        eden seri_hub / sik_rf_olc) pymavlink'i YUKLEMEZ — tembel import
        TunelLink kurucusundadir; KIP=sik/udp hub'i pymavlink'e baglanmaz."""
        kod = (
            "import pathlib,sys; "
            f"p=pathlib.Path({str(PAKET)!r}).resolve(); "
            "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
            "import mavlink_tunel as m, seri_hub as h, sik_rf_olc as s; "
            "assert pathlib.Path(m.__file__).resolve().parent == p; "
            "assert pathlib.Path(h.__file__).resolve().parent == p; "
            "assert pathlib.Path(s.__file__).resolve().parent == p; "
            # duzeltme turu 1: seri_hub tunel modulunu TEMBEL yukler (KIP=sik
            # mavlink_tunel.py'siz calisir; kilit test_seri_hub_tunel T8).
            "assert callable(m.TunelLink) and h._tunel_modulu() is m; "
            "yuklu=[x for x in sys.modules if x.startswith('pymavlink')]; "
            "assert not yuklu, yuklu; "
            "print('JETSON_TUNEL_IMPORT=OK')"
        )
        sonuc = subprocess.run(
            [sys.executable, "-B", "-c", kod], cwd=PAKET,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(0, sonuc.returncode,
                         f"stdout={sonuc.stdout}\nstderr={sonuc.stderr}")
        self.assertIn("JETSON_TUNEL_IMPORT=OK", sonuc.stdout)

    def test_rpi_canli_olcek_pymavlink_olmadan_izole_import_edilir(self):
        """T70: duz Jetson yerlesimi ortak irtifa okuyucusunu bulabilmeli."""
        kod = (
            "import pathlib,sys; "
            f"p=pathlib.Path({str(PAKET)!r}).resolve(); "
            "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
            "import rpi_inference as r; "
            "k=r._inis_kaniti_modulu(); "
            "assert pathlib.Path(r.__file__).resolve().parent == p; "
            "assert pathlib.Path(k.__file__).resolve().parent == p; "
            "assert callable(r.CanliOlcekSaglayici); "
            "assert callable(k.BagilIrtifaOkuyucu); "
            "print('JETSON_RPI_CANLI_OLCEK_IMPORT=OK')"
        )
        sonuc = subprocess.run(
            [sys.executable, "-B", "-c", kod], cwd=PAKET,
            capture_output=True, text=True, timeout=15)
        self.assertEqual(0, sonuc.returncode,
                         f"stdout={sonuc.stdout}\nstderr={sonuc.stderr}")
        self.assertIn("JETSON_RPI_CANLI_OLCEK_IMPORT=OK", sonuc.stdout)

    # ── T83 · OLCEK KATMANI PAKETTE CANLI MI? ────────────────────────────
    # KUSUR: `rpi_inference._arac_kisa_kenari` `arac_maskesi`yi gecikmeli +
    # try/except ile import eder; dosya pakette YOKSA ImportError yutulur ve
    # kahin "arac_maskesi modulu yok" notuyla None doner. Hicbir kapi dusmez,
    # hicbir sey cokmez — muhurlu pakette 3. katman (arac govdesinden mpp)
    # OLU gider. Iki kilit: (a) kopya kanonikle bayt-es, (b) izole paket
    # dizininden kosulunca import GERCEKTEN basarili.
    def test_arac_maskesi_paket_kopyasi_kanonikle_bayt_es(self):
        kaynak = KOK / "codes" / "arac_maskesi.py"
        hedef = PAKET / "arac_maskesi.py"
        self.assertEqual(hedef, KOPYALAR.get(kaynak),
                         "arac_maskesi.py KOPYALAR sozlesmesinde yok — paket "
                         "yenilenince tasinmaz, olcek katmani sahada olur")
        self.assertTrue(hedef.is_file(), f"paket dosyasi yok: {hedef}")
        self.assertEqual(kaynak.read_bytes(), hedef.read_bytes(),
                         "paket kopyasi bayat: arac_maskesi.py")

    def test_olcek_kahini_arac_katmani_izole_pakette_IMPORT_EDILIYOR(self):
        """Paket dizininden TEK BASINA: 'arac_maskesi modulu yok' DONMEMELI.

        Sahte OBB dedektoru hicbir kutu dondurmez; boylece beklenen not
        `arac_maskesi.arac_olcek_kenari`nin KENDI metni olur ("sahnede
        olculebilir arac YOK"). Not oradan geldiyse import basarilmistir.
        """
        kod = (
            "import pathlib,sys; "
            f"p=pathlib.Path({str(PAKET)!r}).resolve(); "
            "sys.path[:]=[str(p)]+[x for x in sys.path if x not in ('',str(p))]; "
            "import numpy as np; "
            "import rpi_inference as r; "
            "assert pathlib.Path(r.__file__).resolve().parent == p\n"
            "class M:\n"
            "    task='obb'; names={0:'small vehicle',1:'large vehicle'}\n"
            "    def predict(self,*a,**k): return []\n"
            "bgr=np.zeros((96,128,3),np.uint8); "
            "kenar,notu=r._arac_kisa_kenari(bgr, M(), 0.25); "
            "print('ARAC_NOTU='+notu); "
            "assert kenar is None; "
            "assert 'modulu yok' not in notu, notu; "
            "assert notu == 'sahnede olculebilir arac YOK', notu; "
            "import arac_maskesi as a; "
            "assert pathlib.Path(a.__file__).resolve().parent == p; "
            "k=r.kare_olcek_kahini(None, None, (None,None,None), bgr=bgr, arac_modeli=M()); "
            "d=dict(k['denenen']); "
            "assert r.OLCEK_KAYNAK_ARAC in d, d; "
            "assert 'modulu yok' not in d[r.OLCEK_KAYNAK_ARAC], d; "
            "print('JETSON_ARAC_OLCEK_IMPORT=OK')"
        )
        sonuc = subprocess.run(
            [sys.executable, "-B", "-c", kod], cwd=PAKET,
            capture_output=True, text=True, timeout=30)
        self.assertEqual(0, sonuc.returncode,
                         f"stdout={sonuc.stdout}\nstderr={sonuc.stderr}")
        self.assertIn("ARAC_NOTU=sahnede olculebilir arac YOK", sonuc.stdout)
        self.assertNotIn("modulu yok", sonuc.stdout)
        self.assertIn("JETSON_ARAC_OLCEK_IMPORT=OK", sonuc.stdout)


if __name__ == "__main__":
    unittest.main()
