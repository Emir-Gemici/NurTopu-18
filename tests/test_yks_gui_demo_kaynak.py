"""NEDEN: Demo açılışındaki ilk algı isteği, v21'in ölçülmüş saha domainine
daha yakın drone karelerinden gelmeli; tanısal gemini/val kümeleri kaybolmamalıdır.
"""

import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


class DemoAlgiKaynagiTests(unittest.TestCase):
    def test_demo_ilk_algi_istegi_drone_kumesinden_gelir(self):
        sahte_kok = (KOK / "temiz_klon_t29").resolve()
        sahte_modul = sahte_kok / "comms" / "yks_gui.py"
        drone_koku = sahte_kok / "data" / "raw_frames"
        sahte_gorseller = [
            drone_koku / "b.jpg",
            drone_koku / "not.txt",
            drone_koku / "a.jpg",
        ]
        yol_sinifi = type(drone_koku)

        with mock.patch.object(yks_gui, "__file__", str(sahte_modul)), \
             mock.patch.object(
                 yol_sinifi, "is_dir", autospec=True, return_value=True) as is_dir, \
             mock.patch.object(
                 yol_sinifi, "rglob", autospec=True,
                 return_value=sahte_gorseller) as rglob, \
             mock.patch.object(yks_gui.YksArayuz, "_arayuz_kur"), \
             mock.patch.object(yks_gui.YksArayuz, "_tik"), \
             mock.patch.object(yks_gui.threading, "Thread") as thread_sinifi:
            arayuz = yks_gui.YksArayuz(mock.Mock(), mock.Mock(), demo=True)
            thread_sinifi.reset_mock()
            arayuz.lbl_algi_bilgi = mock.Mock()

            self.assertTrue(arayuz.demo)
            self.assertEqual("drone", arayuz.algi_kaynak)
            self.assertIn("gemini", arayuz.ALGI_KAYNAKLAR)
            self.assertIn("val", arayuz.ALGI_KAYNAKLAR)
            gorseller = arayuz._algi_gorseller()
            self.assertEqual([drone_koku / "a.jpg", drone_koku / "b.jpg"],
                             gorseller)

            arayuz._algi_iste()

        is_dir.assert_called_with(drone_koku)
        rglob.assert_called_with(drone_koku, "*")
        thread_sinifi.assert_called_once()
        ilk_worker_yolu = thread_sinifi.call_args.kwargs["args"][0]
        self.assertEqual(gorseller[0], ilk_worker_yolu)
        goreli_yol = ilk_worker_yolu.relative_to(sahte_kok)
        print(f"[T29_KAPI] demo=1 kaynak=drone "
              f"ilk_kare={goreli_yol.as_posix()} exit=0")


if __name__ == "__main__":
    unittest.main()
