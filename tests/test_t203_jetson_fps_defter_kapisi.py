"""T203 — `jetson_fps.py` KAYIT DEFTERI KAPISI. Kanit: REVIEW_LOG D-354.

🔴 NEDEN VAR. Kilavuz SS6C/G6-1 "load_model + model_kayit_dogrula zincirinden
gecer" DIYORDU; `jetson_fps.py` bu zinciri HIC cagirmiyordu (grep = 0),
`YOLO(str(yol))` ile dogrudan yukluyordu. Yani saha defterine "dogrulandi"
yaziliyor, dogrulama KOSMUYORDU: kayitsiz ya da YANLIS bir agirlik "OK"
damgasiyla raporlanabiliyordu.

OLCULDU (2026-08-28, duzeltmeden ONCE ve SONRA):
    v37 (defterde KAYITLI DEGIL) -> once: OK · sonra: HATA
        "kayit_defteri_uyusmazligi (fail-closed; ...)"
    v36 (uretim) -> uyumlu=True, durum="eslesti"
    kayitli .onnx -> OK
Yani kapi AYIRT EDIYOR: hem reddediyor hem gecirmesi gerekeni geciriyor.

30 Eylul testi TEK ATIS oldugu icin "dogrulanmamis modelle olcum" secenegi
YOKTUR.
"""
import ast
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "jetson_fps.py"
PAKET = KOK / "jetson_paket" / "kod" / "jetson_fps.py"
KAYNAK = BETIK.read_text(encoding="utf-8")


def _vaka_govdesi(metin: str) -> str:
    i = metin.index("def vaka_calistir(")
    j = metin.find("\ndef ", i + 10)
    return metin[i:j if j > 0 else len(metin)]


def _kodu(metin: str) -> str:
    """Yorum satirlarini AT.

    🔴 T196'nin dersi burada TEKRARLANDI ve bu kez BEN dustum: ilk yazimda
    mutasyon `model_kayit_dogrula` metninin ILK gecisini degistiriyordu ve o
    gecis YORUMDAYDI — gercek cagri sag kaliyor, test kendini kandiriyordu.
    Denetim ve mutasyon artik YALNIZ KOD uzerinde yapilir.
    """
    return "\n".join(s for s in metin.splitlines()
                     if not s.lstrip().startswith("#"))


class DefterKapisi(unittest.TestCase):
    def test_capa_GOVDE_AYRISTIRILIYOR(self):
        self.assertIn("def vaka_calistir(", KAYNAK)
        self.assertGreater(len(_vaka_govdesi(KAYNAK)), 500)

    def test_DEFTER_ZINCIRI_CAGRILIYOR(self):
        self.assertIn("model_kayit_dogrula(", _kodu(_vaka_govdesi(KAYNAK)),
                      "jetson_fps defter zincirini cagirmiyor — kayitsiz model "
                      "'OK' damgasi alabilir (D-354)")

    def test_FAIL_CLOSED_VARSAYILAN(self):
        """Bayrak verilmezse denetim KOSAR; varsayilan `False` olmali."""
        agac = ast.parse(KAYNAK)
        fn = next(d for d in ast.walk(agac)
                  if isinstance(d, ast.FunctionDef) and d.name == "vaka_calistir")
        adlar = [a.arg for a in fn.args.args]
        self.assertIn("kayit_dogrulamasiz", adlar)
        # son varsayilan, son argumana aittir
        self.assertIsInstance(fn.args.defaults[-1], ast.Constant)
        self.assertIs(fn.args.defaults[-1].value, False,
                      "varsayilan fail-OPEN — kayitsiz model sessizce olculur")

    def test_UYUSMAZLIKTA_OLCUM_YAPILMIYOR(self):
        """Ret, model YUKLENMEDEN once donmeli (GPU'ya bile gitmemeli)."""
        g = _vaka_govdesi(KAYNAK)
        i_ret = g.index("kayit_defteri_uyusmazligi")
        i_yolo = g.index("YOLO(str(yol)")
        self.assertLess(i_ret, i_yolo,
                        "defter reddi model yuklendikten SONRA geliyor — "
                        "uyusmazlikta model yine de yukleniyor")

    def test_MUTASYON_kapi_kaldirilinca_DUSER(self):
        g = _kodu(_vaka_govdesi(KAYNAK))
        self.assertIn("model_kayit_dogrula(yol", g, "on kosul: cagri KODDA olmali")
        mutant = g.replace("model_kayit_dogrula(yol", "_kaldirildi(yol", 1)
        self.assertNotEqual(g, mutant, "mutasyon uygulanamadi")
        self.assertNotIn("model_kayit_dogrula(", mutant,
                         "cagri kaldirildigi hâlde kapi gormuyor — BOS KAPI")

    def test_MUTASYON_YORUMDAKI_metin_KIRLETMEZ(self):
        """T196 kalibi: yorumda gecen ad, kapiyi 'ayakta' gostermemeli."""
        g = _vaka_govdesi(KAYNAK)
        self.assertIn("model_kayit_dogrula", g)          # yorumda da geciyor
        kod = _kodu(g)
        mutant = kod.replace("model_kayit_dogrula(yol", "_kaldirildi(yol", 1)
        self.assertNotIn("model_kayit_dogrula(", mutant,
                         "yorumdaki metin kod denetimini KIRLETIYOR")

    def test_VERDIKT_OZETE_YAZILIYOR(self):
        """Atlandiginda bile ozette iz kalmali — sessiz atlama YOK."""
        g = _vaka_govdesi(KAYNAK)
        self.assertIn('"kayit"', g)
        self.assertIn("DOGRULANMADI", g,
                      "--kayit-dogrulamasiz verildiginde ozette iz kalmiyor")

    def test_PAKET_KOPYASI_da_kapiyi_TASIYOR(self):
        if not PAKET.is_file():
            self.skipTest("paket kopyasi yok")
        self.assertIn("model_kayit_dogrula(",
                      _kodu(_vaka_govdesi(PAKET.read_text(encoding="utf-8"))),
                      "PAKET kopyasi defter kapisini tasimiyor (D-304 kalibi)")


if __name__ == "__main__":
    unittest.main()
