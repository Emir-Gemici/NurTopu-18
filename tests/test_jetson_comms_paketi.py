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
        self.assertEqual(11, len(KOPYALAR),
                         "paket kopya sozlesmesi 11 dosya olmali "
                         "(10 .py + config/model_registry.json · T103/T83)")
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
