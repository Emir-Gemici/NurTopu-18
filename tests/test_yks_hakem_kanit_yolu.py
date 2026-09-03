"""D-412 — YKS hakem kanıt yolu: `_kanit_yaz` gerçekten VARDIR ve yazar.

NEDEN (ölçülen kusur): `comms/yks_gui.py` içinde `self._kanit_yaz(...)`
**çağrısı** commit'lendi ama **tanımı** commit'lenmedi. Sonuç: `YksArayuz`
her gerçek kurulumda `AttributeError: 'YksArayuz' object has no attribute
'_kanit_yaz'` ile öldü — tam suitte **6 test** bu yüzden hata verdi
(`test_iha_landed_gate` 3, `test_ika_go_gate` 1, `test_p9abc_yks` 1,
`test_yks_gui_demo_kaynak` 1). Sahada bunun anlamı YKS'nin **hiç açılmaması**dır.

Kusur bir "çağrılan ama tanımlanmayan metot" sınıfıdır ve statik olarak
yakalanabilir; bu kapı hem sınıfı hem davranışı kilitler:

  T1  `_kanit_yaz` sınıfta TANIMLI (kusurun kendisi)
  T2  `hakem_kaydi=None` iken çağrı sessizce geçer (test/demo fikstürü yolu)
  T3  gerçek dosya verilince satır JSONL olarak diske yazılır
  T4  yazma hatası arayüzü ÖLDÜRMEZ ama `kanit_kaydi_hatasi`ya DÜŞER (fail-visible)
  T5  ilk hata saklanır, sonraki hata üzerine yazmaz (kök neden kaybolmaz)
  T6  `comms/` içinde başka "çağrılıyor ama tanımlı değil" self-metodu yok
      (aynı kusur sınıfının nüksü — sözdizim ağacından ölçülür)
"""

import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402


def _arayuz(hakem_kaydi):
    """Kurucuyu (tk gerektirir) atlayarak yalnız kanıt yolunu kurar."""
    a = yks_gui.YksArayuz.__new__(yks_gui.YksArayuz)
    a.hakem_kaydi = hakem_kaydi
    a.kanit_kaydi_hatasi = None
    return a


class KanitYolu(unittest.TestCase):
    def test_T1_metot_tanimli(self):
        self.assertTrue(
            callable(getattr(yks_gui.YksArayuz, "_kanit_yaz", None)),
            "_kanit_yaz tanımsız — kurucu AttributeError ile ölür")

    def test_T2_kayit_yokken_sessiz_gecer(self):
        a = _arayuz(None)
        self.assertIsNone(a._kanit_yaz("YKS_ARAYUZ_HAZIR", demo=True))
        self.assertIsNone(a.kanit_kaydi_hatasi)

    def test_T3_gercek_dosyaya_jsonl_yazar(self):
        from hakem_kaydi import HakemKaydi
        with tempfile.TemporaryDirectory() as d:
            yol = Path(d) / "hakem.jsonl"
            kayit = HakemKaydi(yol)
            try:
                a = _arayuz(kayit)
                donen = a._kanit_yaz("YKS_ARAYUZ_HAZIR", demo=False,
                                     tasiyici="udp")
            finally:
                kayit.kapat()
            # HakemKaydi kendi OTURUM_BASLADI / OTURUM_BITTI satirlarini
            # yazar; aradigimiz bizim yazdirdigimizdir.
            kayitlar = [json.loads(x) for x in
                        yol.read_text(encoding="utf-8").strip().splitlines()]
            self.assertEqual(["OTURUM_BASLADI", "YKS_ARAYUZ_HAZIR",
                              "OTURUM_BITTI"], [k["olay"] for k in kayitlar])
            obj = kayitlar[1]
            self.assertEqual("YKS_ARAYUZ_HAZIR", obj["olay"])
            self.assertEqual("udp", obj["tasiyici"])
            self.assertIs(False, obj["demo"])
            self.assertEqual(obj["olay"], donen["olay"])
            self.assertIsNone(a.kanit_kaydi_hatasi)

    def test_T4_yazma_hatasi_oldurmez_ama_gorunur(self):
        kayit = mock.Mock()
        kayit.yaz.side_effect = OSError("disk dolu")
        a = _arayuz(kayit)
        a.gunluk = None                      # arayüz henüz kurulmamış olabilir
        self.assertIsNone(a._kanit_yaz("YKS_ARAYUZ_HAZIR"))   # yükseltmez
        self.assertIsNotNone(a.kanit_kaydi_hatasi)
        self.assertIn("disk dolu", a.kanit_kaydi_hatasi)
        self.assertIn("YKS_ARAYUZ_HAZIR", a.kanit_kaydi_hatasi)

    def test_T5_ilk_hata_saklanir(self):
        kayit = mock.Mock()
        kayit.yaz.side_effect = [OSError("ilk"), OSError("ikinci")]
        a = _arayuz(kayit)
        a.gunluk = None
        a._kanit_yaz("OLAY_A")
        a._kanit_yaz("OLAY_B")
        self.assertIn("ilk", a.kanit_kaydi_hatasi)
        self.assertNotIn("ikinci", a.kanit_kaydi_hatasi)


class TanimsizSelfMetoduYok(unittest.TestCase):
    """Kusur SINIFININ nüksü: `self.X(...)` çağrılıp `def X` yazılmaması."""

    def test_T6_comms_icinde_cagrilan_her_self_metodu_tanimli(self):
        eksikler = []
        for py in sorted((KOK / "comms").glob("*.py")):
            agac = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            for sinif in [d for d in ast.walk(agac)
                          if isinstance(d, ast.ClassDef)]:
                tanimli = {f.name for f in ast.walk(sinif)
                           if isinstance(f, (ast.FunctionDef,
                                             ast.AsyncFunctionDef))}
                # `self._fsync = os.fsync` gibi ENJEKTE EDILEN cagrilabilirler
                # metot degildir ama `self._fsync(...)` diye cagrilir; bunlar
                # tanimli sayilir yoksa kapi yanlis alarm verir.
                for atama in ast.walk(sinif):
                    hedefler = []
                    if isinstance(atama, ast.Assign):
                        hedefler = atama.targets
                    elif isinstance(atama, (ast.AnnAssign, ast.AugAssign)):
                        hedefler = [atama.target]
                    for h in hedefler:
                        if (isinstance(h, ast.Attribute)
                                and isinstance(h.value, ast.Name)
                                and h.value.id == "self"):
                            tanimli.add(h.attr)
                # miras alan sınıflarda taban sınıfın metotları görünmez;
                # yalnız SADE (object) sınıflar denetlenir — yanlış alarm olmasın
                if sinif.bases:
                    continue
                for dugum in ast.walk(sinif):
                    if (isinstance(dugum, ast.Call)
                            and isinstance(dugum.func, ast.Attribute)
                            and isinstance(dugum.func.value, ast.Name)
                            and dugum.func.value.id == "self"
                            and dugum.func.attr not in tanimli):
                        ad = dugum.func.attr
                        # sınıf gövdesinde atanan alanlar (self.x = fonksiyon)
                        # ve dışarıdan enjekte edilenler bu testin dışında;
                        # yalnız `_` ile başlayan İÇ metotlar aranır.
                        if ad.startswith("_") and not ad.startswith("__"):
                            eksikler.append(
                                f"{py.name}:{sinif.name}.{ad}() çağrılıyor, "
                                f"`def {ad}` yok")
        self.assertEqual([], sorted(set(eksikler)))


if __name__ == "__main__":
    unittest.main()
