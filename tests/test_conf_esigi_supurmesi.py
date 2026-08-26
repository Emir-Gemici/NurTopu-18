"""ON_KAYIT §18-A · `126_t138_gece_kumesi.py --conf` KILIDI.

NE KILITLENIYOR (iki ayri iddia, ikisi de tek basina kapiyi dusurur):

  (1) URETIM ESIGI TEK DEGERDIR. `126`nin `--conf` VARSAYILANI uretim
      zincirinin degeridir; `61_rota_moloza_basma.CONF`, `65_kabul_denetcisi.CONF`
      ve `codes/rpi_inference.py` CLI `--conf` varsayilani ile AYNI olmak
      zorundadir. Esik supurmesi bir OLCUMDUR; bayragin varlıgi uretim esigini
      degistirmemelidir (ON_KAYIT §18-A: "kod/sozlesme esigi bu turda degismez").

  (2) ARGUMANSIZ KOSUM BAYT-ESTIR. `--conf` eklenmeden onceki cikti ile
      argumansiz (ve `--conf 0.30` ile) kosumun JSON'u BAYT-ES aynidir; yalniz
      URETIM DISI bir esikle kosulunca ciktiya `_conf` anahtari eklenir (kanit
      izlenebilirligi). Bu, GPU'suz kosulur: `--modeller` var olmayan bir
      agirliga isaret eder, betik "AGIRLIK YOK -> atlandi" yolundan gecer ve
      JSON govdesini yine de yazar — sinanan sey zaten GOVDEDIR.

MUTASYON (bu dosyanin acilis kaniti, results/conf_supurme/rapor.md'de ham
ciktisiyla): `126`da `if args.conf != CONF:` satiri bozulunca (2) duser;
`--conf` varsayilani 0.30 disina alininca (1) duser.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
OLCUM = KOK / "scripts" / "olcum"
BETIK126 = OLCUM / "126_t138_gece_kumesi.py"


def _modul(ad: str, yol: Path):
    for p in (str(OLCUM), str(KOK / "codes")):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class ConfEsigiTekDeger(unittest.TestCase):
    """(1) Uretim guven esigi tek degerdir — dort yerde de AYNI."""

    def test_dort_kaynak_ayni_esik(self):
        m126 = _modul("m126", BETIK126)
        m61 = _modul("m61", OLCUM / "61_rota_moloza_basma.py")
        m65 = _modul("m65", OLCUM / "65_kabul_denetcisi.py")
        import rpi_inference

        cli = {a.dest: a.default
               for a in rpi_inference._arguman_ayristirici()._actions}
        self.assertEqual(m126.CONF, 0.30, "126 uretim esigi degismis")
        self.assertEqual(m61.CONF, m126.CONF,
                         f"61 CONF {m61.CONF} != 126 CONF {m126.CONF}")
        self.assertEqual(m65.CONF, m126.CONF,
                         f"65 CONF {m65.CONF} != 126 CONF {m126.CONF}")
        self.assertEqual(cli["conf"], m126.CONF,
                         f"rpi_inference CLI conf {cli['conf']} != {m126.CONF}")

    def test_cli_varsayilani_uretim_degeri(self):
        """`--conf` bayragi VARSAYILAN olarak uretim esigini kullanir."""
        m126 = _modul("m126b", BETIK126)
        with tempfile.TemporaryDirectory() as td:
            d = self._kos(Path(td), [])
        self.assertNotIn("_conf", d,
                         "argumansiz kosumda `_conf` YAZILMAMALI (bayt-eslik)")
        self.assertEqual(m126.CONF, 0.30)

    # ── (2) bayt-eslik ──────────────────────────────────────────────────────
    @staticmethod
    def _kos(td: Path, ek: list) -> dict:
        """126'yi GPU'suz kos (agirlik yok yolundan) ve JSON govdesini dondur."""
        kare_dizin = td / "kareler"          # AYNI dizin: `_kareler` alani da bayt-es olsun
        kare_dizin.mkdir(parents=True, exist_ok=True)
        cikti = td / f"cikti{'_'.join(ek).replace('.', '_') or 'yok'}"
        r = subprocess.run(
            [sys.executable, str(BETIK126),
             "--kareler", str(kare_dizin),
             "--modeller", "OLMAYAN_AGIRLIK_test_conf.pt",
             "--cikti", str(cikti), "--dosya", "k.json"] + ek,
            cwd=str(KOK), text=True, encoding="utf-8", errors="replace",
            capture_output=True)
        if r.returncode != 0:
            raise AssertionError(f"126 cokti (exit {r.returncode}):\n{r.stdout}\n{r.stderr}")
        return json.loads((cikti / "k.json").read_text(encoding="utf-8"))

    def test_argumansiz_ve_uretim_esigi_bayt_es(self):
        with tempfile.TemporaryDirectory() as td:
            yok = self._kos(Path(td), [])
            acik = self._kos(Path(td), ["--conf", "0.30"])
        self.assertEqual(yok, acik,
                         "--conf 0.30 ile argumansiz kosum AYNI govdeyi vermeli")
        self.assertNotIn("_conf", acik)

    def test_uretim_disi_esik_ciktiya_yazilir(self):
        with tempfile.TemporaryDirectory() as td:
            d = self._kos(Path(td), ["--conf", "0.15"])
        self.assertIn("_conf", d,
                      "uretim disi esikle kosumda esik CIKTIYA yazilmali")
        self.assertEqual(d["_conf"], 0.15)

    def test_esik_predict_cagrisina_gecirilir(self):
        """Bayrak yalniz ayristirilmiyor, GERCEKTEN predict'e gidiyor."""
        kaynak = BETIK126.read_text(encoding="utf-8")
        self.assertIn("conf=args.conf", kaynak,
                      "predict() cagrisi args.conf kullanmiyor")
        self.assertNotIn("conf=0.30", kaynak,
                         "predict() cagrisinda CIPLAK esik kalmis")


if __name__ == "__main__":
    unittest.main()
