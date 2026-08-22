"""T141 KAPISI: (b) senaryosunun cevabi MODEL DEGIL PROSEDUR — ve o prosedur
METIN OLARAK DEGIL, KODDA KOSULARAK kilitlenir.

🔴 NEDEN VAR (D-277 §3-4, mimar hukmu): "birincil goremiyor / rota uretmiyor"
senaryosunun MODEL duzeyinde cevabi YOKTUR. Okunamayan bir sahnede model
degistirmek AYNI KORLUGU BASKA MODELLE denemektir. Dogru cevap bir yedek
agirlik degil, bir OPERASYON kararidir:

    "Rota uretilmiyorsa model degistirilmez; IKA surmez ve sebep kaydedilir."

Bu cumle bir DAVRANIS IDDIASIDIR. T104/D-193'un sinifi tam olarak sudur:
kilavuz VAR OLMAYAN bir davranisa isaret eder ve kimse fark etmez. T123'te
ayni sinif ikinci kez cikti: 7 testlik METIN kilidi, saha gunu cokecek bir
kodu 0/7 ile geciriyordu.

YONTEM (belge -> kod bagi):
  1. Kural, kilavuzdaki `T141-KURAL` blogundan OKUNUR (elle yazilmaz).
  2. Blokta `GECIS YASAK` isaretli senaryo BELGEDEN cikarilir.
  3. O senaryonun iddia ettigi davranis `ika_nav` uzerinde GERCEKTEN KOSULUR:
     rota kapisi kapaliyken sifir-olmayan motor komutu cikmamalidir.
Boylece iki yon de kilitlenir: belge degisirse (2) duser, kod degisirse (3).

⚠ CRLF: kilavuzlar CRLF satir sonuyla tutuluyor. T123'te mutasyonum `\\n`
aradigi icin HIC UYGULANMAMIS ve "dusmedi" gorunmustu. Burada tum ayristirma
satir sonundan BAGIMSIZ yapilir.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK / "simulation" / "scripts"))

import ika_nav  # noqa: E402

KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md",
              KOK / "jetson_paket" / "JETSON_KILAVUZ.md")
LISTE = KOK / "results" / "t123" / "saha_gunu_kontrol_listesi.md"

# Mimarin D-277 §4/2'de yazdigi cumle. Kelimesi kelimesine korunur;
# "surmez" -> "surmemesi onerilir" gibi bir yumusatma bu kapiyi dusurur.
ZORUNLU_CUMLE = ("Rota üretilmiyorsa model değiştirilmez; "
                 "İKA sürmez ve sebep kaydedilir.")


def _duz(metin: str) -> str:
    """Satir sonu ve bosluk farklarindan bagimsiz kiyas metni (CRLF-duyarli)."""
    return re.sub(r"\s+", " ", metin.replace("\r\n", "\n").replace("\r", "\n"))


def kural_blogu(belge: Path) -> dict[str, str]:
    """`T141-KURAL` blogunu ayikla -> {senaryo_harfi: 'SERBEST'|'YASAK'}."""
    metin = belge.read_text(encoding="utf-8").replace("\r\n", "\n")
    m = re.search(r"```text\nT141-KURAL\n(.*?)\n```", metin, re.S)
    if not m:
        raise AssertionError(f"T141-KURAL blogu YOK: {belge}")
    kural: dict[str, str] = {}
    for satir in m.group(1).splitlines():
        s = re.match(r"\s*SENARYO\s*\(([abc])\)\s*(.*?)\s*->\s*GECIS\s+(\w+)",
                     satir)
        if s:
            kural[s.group(1)] = s.group(3).upper()
    if not kural:
        raise AssertionError(f"T141-KURAL blogu BOS ayristirildi: {belge}")
    return kural


class KuralBelgedenOkunurTests(unittest.TestCase):
    """Kural KAYNAGI belgedir — test onu elle tekrar etmez, AYIKLAR."""

    def test_iki_kilavuzda_da_var_ve_AYNI(self):
        a, b = (kural_blogu(k) for k in KILAVUZLAR)
        self.assertEqual(a, b, "iki kilavuzun T141 kurali AYRISMIS")

    def test_uc_senaryo_da_tanimli(self):
        kural = kural_blogu(KILAVUZLAR[0])
        self.assertEqual({"a", "b", "c"}, set(kural),
                         "uc senaryonun hepsi kuralda olmali")

    def test_YASAK_senaryo_TAM_OLARAK_b(self):
        """🔴 Asil hukum: (b) yasak, (a)/(c) serbest.

        Biri (b)'yi SERBEST'e cevirirse saha gunu operator yanlis modele
        gecer — D-277 §3'un onledigi sey budur.
        """
        kural = kural_blogu(KILAVUZLAR[0])
        yasak = {h for h, k in kural.items() if k == "YASAK"}
        self.assertEqual({"b"}, yasak,
                         f"YASAK senaryo kumesi beklenenden farkli: {yasak}")
        self.assertEqual("SERBEST", kural["a"])
        self.assertEqual("SERBEST", kural["c"])

    def test_ZORUNLU_CUMLE_uc_belgede_de_var(self):
        hedef = _duz(ZORUNLU_CUMLE)
        for belge in (*KILAVUZLAR, LISTE):
            self.assertIn(hedef, _duz(belge.read_text(encoding="utf-8")),
                          f"D-277 §4/2 cumlesi YOK: {belge.name}")

    def test_liste_b_senaryosunda_MODEL_DEGISTIR_demiyor(self):
        """Liste (b) satirinda gecise KAPI ACMAMALI."""
        metin = _duz(LISTE.read_text(encoding="utf-8"))
        i = metin.find("rota çizmiyor")
        self.assertGreater(i, -1, "listede (b) satiri bulunamadi")
        satir = metin[i:i + 200]
        self.assertIn("MODEL DEĞİŞTİRİLMEZ", satir,
                      f"(b) satiri gecisi yasaklamiyor: {satir[:120]}")


class DavranisKODDA_KOSULUYORTests(unittest.TestCase):
    """Belgedeki iddia `ika_nav` uzerinde GERCEKTEN kosulur."""

    def _surus_kos(self, kapali_tur: int) -> list[tuple[float, float]]:
        """Rota kapisi ilk `kapali_tur` turda KAPALI; komutlari dondur.

        Kapi kapaliyken IKA'nin surmemesi gerekir. Sonra kapi acilir ki
        dongu sonlansin — saha gerceginin aynisi (NO_ROUTE gecicidir,
        `CONTRACTS.md §6`).
        """
        komutlar: list[tuple[float, float]] = []
        konum = {"x": 0.0}
        cagri = {"n": 0}

        def get_pose(_model="ika"):
            return konum["x"], 0.0, 0.0, 0.0

        def send_vel(right, left, _topic="~/ika/vel_cmd"):
            komutlar.append((right, left))
            if len(komutlar) > 60:
                raise AssertionError("test watchdog: 60 komut asildi")
            if abs(right) > 1e-9 or abs(left) > 1e-9:
                konum["x"] += 0.4

        def rota_gecerli():
            cagri["n"] += 1
            return cagri["n"] > kapali_tur

        with (
            mock.patch.object(ika_nav, "get_pose", side_effect=get_pose),
            mock.patch.object(ika_nav, "send_vel", side_effect=send_vel),
            mock.patch.object(ika_nav, "time",
                              SimpleNamespace(sleep=lambda _s: None)),
        ):
            ika_nav.navigate([(0.0, 0.0), (1.0, 0.0)], verbose=False,
                             rota_gecerli=rota_gecerli)
        return komutlar[:kapali_tur]

    def test_YASAK_senaryoda_IKA_SURMEZ_kosuldu(self):
        """🔴 Belgedeki (b) hukmunun KOD karsiligi burada ICRA edilir."""
        kural = kural_blogu(KILAVUZLAR[0])
        self.assertEqual("YASAK", kural["b"],
                         "belge (b)'yi yasaklamiyor — kod kiyasi anlamsiz")

        kapali = self._surus_kos(kapali_tur=5)
        self.assertGreaterEqual(len(kapali), 5,
                                "rota kapisi kapaliyken hic komut uretilmedi")
        sifir_olmayan = [k for k in kapali
                         if abs(k[0]) > 1e-9 or abs(k[1]) > 1e-9]
        self.assertEqual([], sifir_olmayan,
                         "🔴 rota YOKKEN sifir-olmayan motor komutu cikti — "
                         "kilavuzun 'IKA surmez' iddiasi YANLIS")
        print(f"[KAPI T141] rota kapisi KAPALI · komut={len(kapali)} · "
              f"sifir-olmayan={len(sifir_olmayan)}")

    def test_NO_ROUTE_alicida_rota_kapisini_ACMAZ(self):
        """`receiver_rota_gecerli` NO_ROUTE'u yok sayarsa kapi bosalir."""
        rota = {"type": "OPEN_ROUTE", "waypoints": [[0.0, 0.0], [1.0, 0.0]],
                "ref_xy": [0.0, 0.0], "seq": 9001}

        class _Alici:
            def __init__(self, no_route):
                self.ika_go = True
                self.iha_landed = True
                self._no_route = no_route

            def decision_snapshot(self):
                return rota, self._no_route, 1, 0.0

        self.assertTrue(ika_nav.receiver_rota_gecerli(_Alici(None)),
                        "gecerli OPEN_ROUTE kapiyi acmali (pozitif kontrol)")
        self.assertFalse(
            ika_nav.receiver_rota_gecerli(_Alici({"sebep": "KAPALI_DAR"})),
            "🔴 NO_ROUTE varken kapi ACIK kaldi")


if __name__ == "__main__":
    unittest.main(verbosity=2)
