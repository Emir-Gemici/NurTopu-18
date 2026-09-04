"""YKİ'nin puanlanan süreleri ve kritik teyidi duvar saatine bağlı kalamaz."""

import ast
import inspect
import sys
import textwrap
import unittest
from pathlib import Path
from unittest import mock


KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


class _Widget:
    def __init__(self):
        self.ayarlar = {}

    def config(self, **kwargs):
        self.ayarlar.update(kwargs)


class YksMonotonikKronometreTests(unittest.TestCase):
    SURE_METOTLARI = (
        "firlatma", "iha_indi", "ika_baslat", "hb_temas",
        "alan_girisi", "takim_hazir", "mudahale", "_kron_metin", "parasut",
    )

    def test_sure_metotlarinda_duvar_saati_cagrisi_YOK(self):
        """Mutasyon: yöntemlerden biri ``time.time``a dönerse kapı düşer."""
        for ad in self.SURE_METOTLARI:
            with self.subTest(metot=ad):
                kaynak = textwrap.dedent(
                    inspect.getsource(getattr(yks_gui.YksArayuz, ad)))
                agac = ast.parse(kaynak)
                nitelikler = [n for n in ast.walk(agac)
                              if isinstance(n, ast.Attribute)
                              and isinstance(n.value, ast.Name)
                              and n.value.id == "time"]
                self.assertNotIn(
                    "time", [n.attr for n in nitelikler],
                    f"{ad}: duvar saati puanlanan/teyit süresine geri döndü")
                self.assertIn(
                    "monotonic", [n.attr for n in nitelikler],
                    f"{ad}: monotonik süre kaynağı yok")

    def test_duvar_saati_sicramasi_canli_sayaci_degistirmez(self):
        g = object.__new__(yks_gui.YksArayuz)
        g.t_iha0 = 100.0
        g.t_iha1 = None
        with (mock.patch.object(yks_gui.time, "monotonic", return_value=130.0),
              mock.patch.object(yks_gui.time, "time", return_value=-9_999_999.0)):
            metin, _renk = g._kron_metin(g.t_iha0, g.t_iha1, 600.0)
        self.assertEqual("09:30", metin)

    def test_iha_baslangic_bitis_suresi_duvar_saatinden_bagimsizdir(self):
        g = object.__new__(yks_gui.YksArayuz)
        g.t_iha0 = g.t_iha1 = None
        g.arm_bekleyen_komut = None
        g.arm_acik = True
        g.IHA_LIMIT = 600.0
        g.onaylandi = True
        g._kanit_kilidi_var = mock.Mock(return_value=False)
        g._arm_durumu_taze_mi = mock.Mock(return_value=True)
        g._kanit_yaz = mock.Mock()
        g._logla = mock.Mock()
        g._firlat_dugmesini_ciz = mock.Mock()
        g._ucus = mock.Mock()
        g.btn_iha_indi = _Widget()

        with (mock.patch.object(yks_gui.time, "monotonic",
                               side_effect=(1_000.0, 1_045.0)),
              mock.patch.object(yks_gui.time, "time",
                               side_effect=(99_000.0, -99_000.0))):
            g.firlatma()
            g.iha_indi()

        self.assertEqual(1_000.0, g.t_iha0)
        self.assertEqual(1_045.0, g.t_iha1)
        bitis = [c for c in g._kanit_yaz.call_args_list
                 if c.args and c.args[0] == "KRONOMETRE_BITTI"]
        self.assertEqual(1, len(bitis))
        self.assertEqual(45.0, bitis[0].kwargs["sure_s"])


if __name__ == "__main__":
    unittest.main()
