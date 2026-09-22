"""NEDEN: EXE acilisi yanlis tasiyiciya veya otomatik demo verisine dusmemeli."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

spec = importlib.util.spec_from_file_location("launcher", Path(__file__).with_name("navitas_yki_app.py"))
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        output = Path(__file__).parent / "test_outputs" / self._testMethodName
        output.mkdir(parents=True, exist_ok=True)
        self.root_patch = patch.object(app, "ROOT", output)
        self.root_patch.start(); self.addCleanup(self.root_patch.stop)
        self.argv = sys.argv[:]
        self.addCleanup(setattr, sys, "argv", self.argv)
        self.seen = []
        self.gui = types.SimpleNamespace(main=lambda: self.seen.append(sys.argv[1:]))

    def test_existing_tunnel_never_opens_serial_or_demo(self):
        with patch.dict(sys.modules, yks_gui=self.gui), patch.object(app, "start_radio") as radio:
            self.assertEqual(app.main(["--tunel", "127.0.0.1:14590", "--fda"]), 0)
        radio.assert_not_called()
        self.assertEqual(self.seen, [["--tunel", "127.0.0.1:14590", "--fda"]])

    def test_radio_and_gui_share_exact_tunnel_endpoint(self):
        router = object()
        with patch.dict(sys.modules, yks_gui=self.gui, radio_mode=types.SimpleNamespace(install=Mock())), patch.object(app, "start_radio", return_value=router) as radio, patch.object(app, "cleanup_router") as cleanup:
            self.assertEqual(app.main(["--radyo", "COM7", "--baud", "57600"]), 0)
        radio.assert_called_once_with("COM7", 57600, "127.0.0.1:14590")
        self.assertEqual(self.seen, [["--tunel", "127.0.0.1:14590", "--fda"]])
        cleanup.assert_called_once_with(router)

    def test_conflicting_transport_rejected_before_radio_open(self):
        with patch.object(app, "start_radio") as radio:
            self.assertEqual(app.main(["--radyo", "COM7", "--demo"]), 2)
        radio.assert_not_called()

    def test_serial_open_failure_releases_udp_ports(self):
        sockets = [Mock(), Mock()]
        targets = [("mp", sockets[0], ("127.0.0.1", 14550)), ("tunel", sockets[1], ("127.0.0.1", 14590))]
        router_module = types.SimpleNamespace(udp_hedefler=Mock(return_value=targets), Yonlendirici=Mock(side_effect=OSError("COM7 busy")))
        with patch.dict(sys.modules, yer_yonlendirici=router_module):
            with self.assertRaisesRegex(OSError, "COM7 busy"):
                app.start_radio("COM7", 57600, "127.0.0.1:14590")
        for sock in sockets:
            sock.close.assert_called_once()


if __name__ == "__main__":
    unittest.main(verbosity=2)
