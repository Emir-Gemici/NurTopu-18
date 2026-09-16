"""K7 — MAVLink TUNNEL sozlesme kilidi (CONTRACTS §7.6 ↔ kod ↔ kabuk ↔ birim ↔ runbook ↔ kilavuz).

NEDEN (anayasa madde 16): sabitlerin TEK kaynagi `comms/mavlink_tunel.py`dir; tabloyu
CONTRACTS §7.6 tutar, kabuk ikizleri `jetson_paket/jetson_baslat.sh`'tadir. Biri sessizce
kayarsa (ornek: hub 14553'u, MAVProxy 14554'u dinler) tunel sahada SAGIR olur ve hicbir
birim testi bunu gormez. Bu dosya metinleri birbirine esitler:
  S1 §7.6 tablosu == mavlink_tunel sabitleri (TUNEL_* hepsi tabloda; tablo satiri kodda);
  S2 kabuk sabitleri == kod (TUNEL_HAVA_UC, TUNEL_OLCUM_YANKI_UC, hub kimligi) ve
     == §7.6 tablosu (TUNEL_TELEM2_BAUD, TUNEL_STREAMRATE);
  S3 yeni portlar §7.4/§7.5 port tablolariyla ve birbirleriyle CAKISMAZ; 5190 depoda
     yalniz tunel dosyalarinda;
  S4 runbook komutlari: uclar sabitlerle ayni, cagirilan dosyalar depoda var;
  S5 JETSON_KILAVUZ kurulum blogu mavlink_tunel.py'i comms/'a, sik_rf_olc.py'i scripts/'e kopyalar;
  S6 degistirilen kod dosyalarinda CIPLAK tunel sayisi yok (ast: docstring/yorum haric);
  S7 pymavlink ile esitlik (msgid, payload dizi boyu, MAV_COMP_ID_USER1/2).
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import mavlink_tunel as mt  # noqa: E402
import seri_hub  # noqa: E402

CONTRACTS = KOK / "CONTRACTS.md"
BETIK = KOK / "jetson_paket" / "jetson_baslat.sh"
RUNBOOK = KOK / "jetson_paket" / "TUNEL_SAHA_RUNBOOK.md"
KILAVUZ = KOK / "jetson_paket" / "JETSON_KILAVUZ.md"
KABUK_SABITLERI = ("TUNEL_TELEM2_BAUD", "TUNEL_STREAMRATE")


def _bolum(metin, baslik):
    bas = metin.index(baslik)
    son = min(i for i in (metin.find("\n### ", bas + 1), metin.find("\n## ", bas + 1)) if i > 0)
    return metin[bas:son]


def _tablo():
    bolum = _bolum(CONTRACTS.read_text(encoding="utf-8"), "### 7.6")
    return dict(re.findall(r"^\|\s*`(TUNEL_[A-Z0-9_]+)`\s*\|\s*`([^`]+)`\s*\|", bolum, re.M))


def _sh(ad):
    m = re.search(rf'^{ad}="?([^"\s#]+)"?', BETIK.read_text(encoding="utf-8"), re.M)
    return None if m is None else m.group(1)


def _deger_metni(v):
    return v if isinstance(v, str) else repr(v)


class SozlesmeTablosu(unittest.TestCase):
    def test_S1_tablo_ve_kod_birebir(self):
        tablo = _tablo()
        self.assertGreater(len(tablo), 20, "tablo ayristirilamadi")
        kod = {ad: getattr(mt, ad) for ad in dir(mt) if ad.startswith("TUNEL_")}
        eksik = sorted(set(kod) - set(tablo))
        self.assertEqual([], eksik, "kod sabiti §7.6 tablosunda yok")
        for ad, metin in tablo.items():
            with self.subTest(sabit=ad):
                if ad in KABUK_SABITLERI:
                    continue
                self.assertIn(ad, kod, "tablo satiri kodda yok")
                deger = kod[ad]
                if isinstance(deger, str):
                    self.assertEqual(deger, metin)
                else:
                    self.assertEqual(deger, ast.literal_eval(metin))

    def test_S2_kabuk_ikizleri_kod_ve_tablo_ile_ayni(self):
        tablo = _tablo()
        self.assertEqual(mt.TUNEL_HAVA_UC, _sh("TUNEL_HAVA_UC"))
        self.assertEqual(mt.TUNEL_OLCUM_YANKI_UC, _sh("TUNEL_OLCUM_YANKI_UC"))
        self.assertEqual(mt.KIMLIK_HAVA, _sh("TUNEL_HUB_KIMLIGI"))
        for ad in KABUK_SABITLERI:
            with self.subTest(sabit=ad):
                self.assertIsNotNone(_sh(ad))
                self.assertEqual(int(tablo[ad]), int(_sh(ad)))
        self.assertEqual(-1, int(_sh("TUNEL_STREAMRATE")))
        self.assertEqual(57600, int(_sh("TUNEL_TELEM2_BAUD")))

    def test_S3_portlar_cakismaz_5190_yalniz_tunel_dosyalarinda(self):
        metin = CONTRACTS.read_text(encoding="utf-8")
        eski = set()
        for b in ("### 7.4", "### 7.5"):
            eski |= {int(p) for p in re.findall(r"127\.0\.0\.1:(\d+)", _bolum(metin, b))}
        self.assertTrue({14550, 14551, 14552, 5100, 5007} <= eski, eski)
        yeni = [int(mt.uc_coz(u)[1]) for u in (mt.TUNEL_HAVA_UC, mt.TUNEL_YER_UC,
                                               mt.TUNEL_OLCUM_YANKI_UC)]
        self.assertEqual(len(set(yeni)), len(yeni))
        self.assertEqual(set(), set(yeni) & eski, "tunel portu §7.4/§7.5 uclariyla cakisiyor")
        izinli = {"comms/mavlink_tunel.py", "jetson_paket/kod/mavlink_tunel.py",
                  "jetson_paket/jetson_baslat.sh"}
        port = str(mt.uc_coz(mt.TUNEL_OLCUM_YANKI_UC)[1])
        bulunan = set()
        for alt in ("comms", "codes", "scripts", "jetson_paket"):
            for yol in (KOK / alt).rglob("*"):
                if yol.suffix not in (".py", ".sh", ".service") or "__pycache__" in yol.parts:
                    continue
                if re.search(rf"\b{port}\b", yol.read_text(encoding="utf-8", errors="replace")):
                    bulunan.add(yol.relative_to(KOK).as_posix())
        self.assertEqual(izinli, bulunan)
        self.assertLess(mt.TUNEL_TAMAMLANAN_HAFIZA_S, seri_hub.SERI_YENIDEN_ACMA_ARALIGI_S)

    def test_S4_runbook_komutlari_sabitlerle_ayni_dosyalar_var(self):
        rb = RUNBOOK.read_text(encoding="utf-8")
        hava, yer, yanki = mt.TUNEL_HAVA_UC, mt.TUNEL_YER_UC, mt.TUNEL_OLCUM_YANKI_UC
        beklenen = (
            f"--rol yanki --tasiyici tunel --tunel-bind {hava} --tunel-kimlik {mt.KIMLIK_HAVA}",
            f"--rol olc --tasiyici tunel --tunel-bind {yer} --tunel-kimlik {mt.KIMLIK_YER} --n 200 --aralik 0.25",
            f"comms\\yks_gui.py --tunel {yer}",
            f"seri_hub.py --tunel {hava} --tunel-kimlik {mt.KIMLIK_HAVA} --bind {seri_hub.VARSAYILAN_BIND}",
            f"--tuketici {yanki}",
            f"--rol yanki --tasiyici udp --bind {yanki}",
            "--prob-dolgu 165", "--prob-dolgu 473",
            "K8a_tunel_rtt.json", "K8b_uretim_rtt.json",
            f"--out udp:{hava} --streamrate -1",
            # duzeltme turu 1: K8-0 (i) iki kip + datagram siniri; hava JSON'u;
            # havadan yere cok parcali ACK; SR2 kaniti ayri dinleyici
            "--tunel-ayristirma akis", "--tunel-ayristirma datagram",
            "datagram_siniri.hizasiz = 0",
            f"--tunel-kimlik {mt.KIMLIK_HAVA} --json --cikti ~/K8a_hava_yanki.json",
            f"--rol yanki --tasiyici udp --bind {yanki} --ack-dolgu 473",
            "udpin:127.0.0.1:14550", "FS_GCS_ENABLE",
        )
        for parca in beklenen:
            with self.subTest(parca=parca):
                self.assertIn(parca, rb)
        izinli = {int(mt.uc_coz(u)[1]) for u in (hava, yer, yanki)}
        izinli |= {int(seri_hub.VARSAYILAN_BIND.rsplit(":", 1)[1]), 5007, 14550}
        portlar = {int(p) for p in re.findall(r"127\.0\.0\.1:(\d+)", rb)}
        self.assertEqual(set(), portlar - izinli, "runbook'ta sozlesme disi port")
        for dosya in re.findall(r"(?:~/navitas/|\b)((?:comms|scripts)[/\\][A-Za-z0-9_]+\.py)", rb):
            with self.subTest(dosya=dosya):
                self.assertTrue((KOK / dosya.replace("\\", "/")).is_file(), dosya)
        self.assertTrue((KOK / "jetson_paket" / "jetson_baslat.sh").is_file())

    def test_S5_kilavuz_kurulum_blogu_tunel_dosyalarini_kopyalar(self):
        import test_t202_jetson_paket_butunlugu as t202
        kurulan = t202._kurulan()
        self.assertIn("comms/mavlink_tunel.py", kurulan)
        self.assertIn("scripts/sik_rf_olc.py", kurulan)
        self.assertIn("comms/seri_hub.py", kurulan, "eski kopya satiri bozulmadi")
        self.assertTrue(re.search(r"^cp kod/sik_rf_olc\.py ~/navitas/scripts/",
                                  KILAVUZ.read_text(encoding="utf-8"), re.M),
                        "sik_rf_olc ayri cp satiri")

    def test_S6_degisen_kod_dosyalarinda_ciplak_tunel_sayisi_yok(self):
        yasak_sayi = {mt.TUNEL_MAVLINK_MSG_ID, mt.TUNEL_PAYLOAD_TYPE, mt.TUNEL_SYSID,
                      *(int(mt.uc_coz(u)[1]) for u in (mt.TUNEL_HAVA_UC, mt.TUNEL_YER_UC,
                                                       mt.TUNEL_OLCUM_YANKI_UC))}
        yasak_metin = {str(int(mt.uc_coz(u)[1])) for u in (mt.TUNEL_HAVA_UC, mt.TUNEL_YER_UC,
                                                           mt.TUNEL_OLCUM_YANKI_UC)}
        for goreli in ("comms/seri_hub.py", "comms/yks_gui.py", "scripts/sik_rf_olc.py",
                       "comms/link.py", "scripts/ardupilot_yonlendirici_taklit.py"):
            with self.subTest(dosya=goreli):
                agac = ast.parse((KOK / goreli).read_text(encoding="utf-8"))
                docstringler = set()
                for dugum in ast.walk(agac):
                    if isinstance(dugum, (ast.Module, ast.FunctionDef, ast.ClassDef,
                                          ast.AsyncFunctionDef)) and dugum.body:
                        ilk = dugum.body[0]
                        if isinstance(ilk, ast.Expr) and isinstance(getattr(ilk, "value", None), ast.Constant):
                            docstringler.add(id(ilk.value))
                ihlal = []
                for dugum in ast.walk(agac):
                    if not isinstance(dugum, ast.Constant) or id(dugum) in docstringler:
                        continue
                    v = dugum.value
                    if isinstance(v, int) and not isinstance(v, bool) and v in yasak_sayi:
                        ihlal.append((dugum.lineno, v))
                    elif isinstance(v, str) and any(re.search(rf"\b{p}\b", v) for p in yasak_metin):
                        ihlal.append((dugum.lineno, v[:60]))
                self.assertEqual([], ihlal)

    def test_S7_pymavlink_ile_esit(self):
        try:
            from pymavlink.dialects.v20 import ardupilotmega as m
        except ImportError:  # pragma: no cover
            self.skipTest("pymavlink kurulu degil")
        self.assertEqual(m.MAVLINK_MSG_ID_TUNNEL, mt.TUNEL_MAVLINK_MSG_ID)
        self.assertEqual(m.MAVLink_tunnel_message.array_lengths[-1], mt.TUNEL_MAVLINK_YUK_B)
        self.assertEqual(m.MAV_COMP_ID_USER1, mt.TUNEL_HAVA_COMPID)
        self.assertEqual(m.MAV_COMP_ID_USER2, mt.TUNEL_YER_COMPID)
        self.assertGreater(mt.TUNEL_PAYLOAD_TYPE, 32767)
        self.assertNotIn(mt.TUNEL_PAYLOAD_TYPE, m.enums["MAV_TUNNEL_PAYLOAD_TYPE"])
        from iha_komut_alici import VARSAYILAN_HEDEF_SYSID
        self.assertNotIn(mt.TUNEL_SYSID, (0, VARSAYILAN_HEDEF_SYSID, 255, 51))


if __name__ == "__main__":
    unittest.main()
