"""YKİ UDP dinleme ucu tek süreç tarafından sahiplenmelidir."""

import ast
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
GUI_YOLU = KOK / "comms" / "yks_gui.py"
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


class YksUdpTekSahipTests(unittest.TestCase):
    def test_ikinci_yks_ayni_portu_sessizce_acamaz(self):
        ilk = yks_gui.yks_udp_linki_ac(("127.0.0.1", 0))
        try:
            port = ilk.port
            with self.assertRaises(OSError):
                ikinci = yks_gui.yks_udp_linki_ac(("127.0.0.1", port))
                ikinci.close()
        finally:
            ilk.close()

    def test_main_udp_yolunda_tek_sahip_yardimcisini_kullanir(self):
        agac = ast.parse(GUI_YOLU.read_text(encoding="utf-8"),
                         filename=str(GUI_YOLU))
        main = next(n for n in agac.body
                    if isinstance(n, ast.FunctionDef) and n.name == "main")
        cagrilar = [n for n in ast.walk(main) if isinstance(n, ast.Call)]
        self.assertTrue(any(
            isinstance(c.func, ast.Name) and c.func.id == "yks_udp_linki_ac"
            for c in cagrilar),
            "mutasyon: main UDPLink varsayılan reuse=True yoluna geri döndü")

    def test_dolu_port_operatora_acik_nedenle_reddedilir(self):
        ilk = yks_gui.yks_udp_linki_ac(("127.0.0.1", 0))
        hata = io.StringIO()
        try:
            argv = ["yks_gui.py", "--demo", "--bind",
                    f"127.0.0.1:{ilk.port}"]
            with (mock.patch.object(sys, "argv", argv),
                  contextlib.redirect_stderr(hata),
                  self.assertRaises(SystemExit) as cikis):
                yks_gui.main()
        finally:
            ilk.close()
        self.assertEqual(2, cikis.exception.code)
        self.assertIn("YKİ UDP dinleme ucu açılamadı", hata.getvalue())
        self.assertIn("Başka bir YKİ", hata.getvalue())

    def test_serial_ile_iha_udp_hedefi_sessizce_yok_sayilmaz(self):
        hata = io.StringIO()
        argv = ["yks_gui.py", "--serial", "COM5", "--iha",
                "10.0.0.4:5007"]
        with (mock.patch.object(sys, "argv", argv),
              contextlib.redirect_stderr(hata),
              self.assertRaises(SystemExit) as cikis):
            yks_gui.main()
        self.assertEqual(2, cikis.exception.code)
        self.assertIn("--serial ile --iha birlikte kullanılamaz", hata.getvalue())
        self.assertIn("UDP hedefi uygulanmaz", hata.getvalue())


if __name__ == "__main__":
    unittest.main()
