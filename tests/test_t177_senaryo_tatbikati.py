"""T177/T178/T179 KAPISI (REVIEW_LOG D-323): acil durum tatbikatinin ekranda
YALAN SOYLEMEMESI ve demo beslemesinin sunum ortasinda olmemesi.

UC KUSUR (calisan GUI acilarak / gercek besleme dinlenerek olculdu):

  T177 — F4 "Batarya KRITIK (<%15)" ve F5 "GNSS fix KAYBI" yalnizca GUNLUGE
         yaziliyordu. Ayni anda telemetri paneli "12.6 V · 14 uydu" gostermeye
         DEVAM ediyordu. Ekran kendi kendisiyle celisiyordu; tatbikati izleyen
         kisi senaryoyu degil SISTEMI supheli bulur.

  T178 — Her senaryo kendi geri-donus zamanlayicisini kuruyor, hicbiri
         digerini iptal etmiyordu. F1'e basip 1 sn sonra F2'ye basilinca,
         F1'in 6 sn'lik zamanlayicisi F2 HALA YURURLUKTEYKEN bandi yesil
         "OTONOM GOREV"e ceviriyordu: baglanti kesikken ekran "her sey yolunda"
         diyordu.

  T179 — `demo_besle` icindeki iki dongu de `while time.time() - t0 < 600`
         yaziyordu: besleme 10 DAKIKADA SESSIZCE oluyordu. Sunum 10 dakikayi
         asarsa heartbeat kesilir, ekran "baglanti yok"a duser, sistem BOZULMUS
         gibi gorunur.

BOS KAPI YASAGI (TEST_SPECS SS4.1): her iddia mutasyonla sinanir — jeton
kaldirilirsa, anahtar geri acilmazsa, sure siniri geri konursa kapi DUSER.
"""

from __future__ import annotations

import re
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import yks_gui                                                    # noqa: E402
from link import UDPLink                                          # noqa: E402
from protocol import FrameReader                                  # noqa: E402

KAYNAK = (KOK / "comms" / "yks_gui.py").read_text(encoding="utf-8")


def _ekran():
    """Tk'siz YksArayuz ornegi: senaryo yolunun MANTIGI aynen kosulur."""
    o = object.__new__(yks_gui.YksArayuz)
    o.demo = True
    o.demo_durum = {"iha_hb": True, "ika_hb": True,
                    "iha_bat": True, "iha_gnss": True}
    o.gunluk = []
    o.band = []
    o.normale_donus = 0
    o._logla = lambda metin, renk=None: o.gunluk.append(metin)
    o._ucus = lambda metin, renk=None: o.band.append(metin)

    def _normal():
        o.normale_donus += 1
        o.band.append("OTONOM GOREV (AUTO)")

    o._ucus_normal = _normal
    o.zamanlayici = []
    o.kok = mock.Mock()
    o.kok.after = lambda ms, islev: o.zamanlayici.append((ms, islev))
    return o


class T178JetonUstuOrtuleniIptalEder(unittest.TestCase):

    def test_ustu_ortulen_senaryo_bandi_DEGISTIRMEZ(self):
        o = _ekran()
        o.senaryo("rc")                       # F1 · 6 sn sonra normale doner
        o.senaryo("yks")                      # F2 · baglanti kesik, 7 sn
        f1 = o.zamanlayici[0][1]
        f1()                                  # F1'in zamanlayicisi ONCE patlar
        self.assertEqual(0, o.normale_donus,
                         "ustu ortulen senaryo bandi normale cevirdi — "
                         "baglanti kesikken ekran 'her sey yolunda' diyor")
        self.assertIn("LOITER", o.band[-1])

    def test_MUTASYON_tek_basina_senaryo_normale_DONER(self):
        """Jeton geri donusu HEP engelliyor olsaydi kapi bos olurdu."""
        o = _ekran()
        o.senaryo("rc")
        o.zamanlayici[0][1]()
        self.assertEqual(1, o.normale_donus,
                         "tek senaryo bile normale donmuyor — bant kalici kirli")

    def test_guncel_senaryo_kendi_geri_donusunu_YAPAR(self):
        o = _ekran()
        o.senaryo("rc")
        o.senaryo("yks")
        o.zamanlayici[0][1]()                 # F1 (bastirilir)
        o.zamanlayici[1][1]()                 # F2 (gunceldir)
        self.assertEqual(1, o.normale_donus)
        self.assertTrue(o.demo_durum["iha_hb"])


class AnahtarGeriAcmaJetondanBAGIMSIZ(unittest.TestCase):
    """En sinsi hata: jeton, anahtarin geri acilmasini da bastirirsa telemetri
    KALICI kesik kalir — ekran sonsuza dek 'baglanti yok' der."""

    def test_ustu_ortulen_YKS_senaryosu_anahtari_GERI_ACAR(self):
        o = _ekran()
        o.senaryo("yks")                      # iha_hb -> False
        o.senaryo("ika")                      # ustunu orter
        self.assertFalse(o.demo_durum["iha_hb"])
        o.zamanlayici[0][1]()                 # YKS geri donusu
        self.assertTrue(o.demo_durum["iha_hb"],
                        "ustu ortulen senaryonun kestigi telemetri KALICI "
                        "kesik kaldi")

    def test_ustu_ortulen_BATARYA_senaryosu_anahtari_GERI_ACAR(self):
        o = _ekran()
        o.senaryo("bat")
        o.senaryo("gnss")
        self.assertFalse(o.demo_durum["iha_bat"])
        o.zamanlayici[0][1]()
        self.assertTrue(o.demo_durum["iha_bat"])


class T177SenaryolarTelemetriyiKESER(unittest.TestCase):

    def test_F4_bataryayi_dusurur(self):
        o = _ekran()
        o.senaryo("bat")
        self.assertFalse(o.demo_durum["iha_bat"],
                         "F4 yalniz gunluge yaziyor — panel hala saglikli "
                         "batarya gosterir (D-323 T177)")

    def test_F5_GNSS_fixini_dusurur(self):
        o = _ekran()
        o.senaryo("gnss")
        self.assertFalse(o.demo_durum["iha_gnss"])

    def test_geri_donus_anahtarlari_TAZELER(self):
        for kod, anahtar in (("bat", "iha_bat"), ("gnss", "iha_gnss")):
            with self.subTest(kod=kod):
                o = _ekran()
                o.senaryo(kod)
                o.zamanlayici[0][1]()
                self.assertTrue(o.demo_durum[anahtar])

    def test_demo_DISI_hicbir_sey_yapmaz(self):
        o = _ekran()
        o.demo = False
        o.senaryo("bat")
        self.assertTrue(o.demo_durum["iha_bat"])
        self.assertEqual([], o.gunluk)


class T177GercekBeslemeSayiyiDEGISTIRIR(unittest.TestCase):
    """Kaynak taramasi degil: besleme GERCEKTEN dinlenir, panele giden
    sayilarin degistigi UDP'den okunur."""

    @classmethod
    def setUpClass(cls):
        cls.link = UDPLink(bind=("127.0.0.1", 0))
        cls.durum = {"iha_hb": True, "ika_hb": True,
                     "iha_bat": True, "iha_gnss": True}
        yks_gui.demo_besle(cls.link.port, cls.durum)

    @classmethod
    def _topla(cls, saniye):
        reader = FrameReader()
        hb = []
        bitis = time.time() + saniye
        while time.time() < bitis:
            d, _ = cls.link.recv()
            for m in (reader.feed(d) if d else []):
                if m.get("type") == "HEARTBEAT" and m.get("node") == "iha":
                    hb.append(m)
            time.sleep(0.05)
        return hb

    @classmethod
    def _yerles(cls):
        """Anahtar cevrildikten sonra YOLDAKI eski cerceveleri at.

        🔴 Bu kapinin ILK kosusu KARARSIZDI: anahtar `False` yapildigi anda
        besleme zaten hesaplanmis bir heartbeat'i gonderme asamasinda
        olabiliyor; o cerceve HALA saglikli degerleri tasir ve 2 sn'lik
        pencerenin ilk karesi olarak yakalanip `all(...)` iddiasini
        dusuruyordu. Kusur URUNDE degil OLCU ALETINDEYDI — besleme araligi
        0.5 sn, bu yuzden 1.5 sn boyunca gelen atilir.
        """
        cls._topla(1.5)

    def test_saglikli_sonra_KRITIK_sonra_geri(self):
        saglikli = self._topla(2.0)
        self.assertTrue(saglikli, "besleme hic heartbeat vermedi")
        self.assertTrue(all(h["bat"] > 11.0 for h in saglikli),
                        [h["bat"] for h in saglikli])
        self.assertTrue(all(h["uydu"] >= 12 for h in saglikli))

        self.durum["iha_bat"] = False
        self.durum["iha_gnss"] = False
        self._yerles()
        kritik = self._topla(2.0)
        self.assertTrue(kritik, "senaryo sonrasi heartbeat kesildi")
        self.assertTrue(all(h["bat"] < 11.0 for h in kritik),
                        "F4 sonrasi panel hala saglikli batarya gosteriyor: "
                        + repr([h["bat"] for h in kritik]))
        self.assertTrue(all(h["uydu"] == 0 for h in kritik),
                        "F5 sonrasi uydu sayisi dusmedi: "
                        + repr([h["uydu"] for h in kritik]))
        # GNSS yoksa konum DONAR (fix olmadan konum guncellenemez).
        xy = {(h["x"], h["y"]) for h in kritik}
        self.assertEqual(1, len(xy), "fix yokken konum guncellendi: " + repr(xy))

        self.durum["iha_bat"] = True
        self.durum["iha_gnss"] = True
        self._yerles()
        geri = self._topla(2.0)
        self.assertTrue(all(h["uydu"] >= 12 for h in geri),
                        "anahtar geri acildi ama telemetri toparlamadi")


class SenaryoBayragiKANIT_URETIR(unittest.TestCase):
    """`--senaryo`: tatbikatin EKRANDAKI etkisi tekrar uretilebilir olmali
    (bu kapinin gorsel kaniti results/demo_hazirlik/07_f4_batarya.png ile
    boyle uretildi). Demo disinda SESSIZCE yoksayilmaz."""

    def test_bayrak_tanimli_ve_secenekler_senaryo_kodlariyla_AYNI(self):
        self.assertIn('"--senaryo"', KAYNAK)
        bas = KAYNAK.index('"--senaryo"')
        pencere = KAYNAK[bas: bas + 400]
        for kod in ("rc", "yks", "ika", "bat", "gnss", "algi"):
            self.assertIn('"' + kod + '"', pencere,
                          "senaryo kodu " + kod + " CLI'da yok — bayrak ile "
                          "dugmeler ayrisir")

    def test_demo_DISINDA_sessiz_kalmaz(self):
        bas = KAYNAK.index("if args.senaryo:")
        pencere = KAYNAK[bas: bas + 600]
        self.assertIn("if not args.demo:", pencere)
        self.assertIn("YOKSAYILDI", pencere,
                      "demo disinda bayrak SESSIZCE dusuyor")


class T182YardimMetniYALAN_SOYLEMEZ(unittest.TestCase):
    """`--help` varsayilani `ALGI_KAYNAKLAR[0]`dan (= "kompozit") turetiyordu;
    oysa T161'den beri gercek varsayilan `ALGI_VARSAYILAN_KAYNAK`
    (= "arena_kadraj"). Kullaniciya soylenen ile yapilan AYRISMISTI."""

    def test_yardim_GERCEK_varsayilani_soyler(self):
        bas = KAYNAK.index('"--kaynak"')
        pencere = KAYNAK[bas: bas + 400]
        self.assertIn("ALGI_VARSAYILAN_KAYNAK", pencere)
        self.assertNotIn("ALGI_KAYNAKLAR[0]", pencere,
                         "yardim metni varsayilani YANLIS sabitten turetiyor")

    def test_MUTASYON_iki_sabit_GERCEKTEN_farkli(self):
        """Ikisi ayni olsaydi kapi hicbir seyi olcmuyor olurdu."""
        self.assertNotEqual(yks_gui.YksArayuz.ALGI_KAYNAKLAR[0],
                            yks_gui.YksArayuz.ALGI_VARSAYILAN_KAYNAK)

    def test_varsayilan_ORNEKTE_de_ayni(self):
        o = object.__new__(yks_gui.YksArayuz)
        self.assertEqual("arena_kadraj", o.ALGI_VARSAYILAN_KAYNAK)
        self.assertIn(o.ALGI_VARSAYILAN_KAYNAK, yks_gui.YksArayuz.ALGI_KAYNAKLAR)


class T181SessizSifirYOK(unittest.TestCase):
    """◀ Onceki · Sonraki ▶ · Kaynak degistir dugmeleri SOL PANELDE durur,
    yani HARITA gorunumunde de ekrandadir. Uc komut da sessizce dusuyordu:
    basilinca hicbir sey olmuyordu. Izleyen icin bu 'dugme bozuk' demektir."""

    @staticmethod
    def _ekran(gorunum):
        o = object.__new__(yks_gui.YksArayuz)
        o.gorunum_adi = gorunum
        o.gunluk = []
        o.algi_idx = 0
        o.istendi = []
        o._logla = lambda metin, renk=None: o.gunluk.append(metin)
        o._algi_iste = lambda: o.istendi.append(o.algi_idx)
        return o

    def test_HARITA_gorunumunde_neden_YAZILIR(self):
        for komut in ("algi_sonraki", "algi_onceki", "algi_kaynak_degistir"):
            with self.subTest(komut=komut):
                o = self._ekran("harita")
                getattr(o, komut)()
                self.assertTrue(o.gunluk,
                                komut + " sessizce dustu — kullanici dugmeyi "
                                "bozuk sanir")
                self.assertIn("V", o.gunluk[-1],
                              "cikis yolu (V tusu) soylenmemis")
                self.assertEqual([], o.istendi, "harita gorunumunde is yapildi")

    def test_ALGI_gorunumunde_GERCEKTEN_calisir(self):
        """MUTASYON: koruma her hâlde reddediyor olsaydi kapi bos olurdu."""
        o = self._ekran("algi")
        o.algi_sonraki()
        self.assertEqual([1], o.istendi)
        o.algi_onceki()
        self.assertEqual([1, 0], o.istendi)
        self.assertEqual([], o.gunluk, "calisan komut uyari yazdi")


class T179SureSiniriYOK(unittest.TestCase):

    DESEN = re.compile(r"while\s+time\.time\(\)\s*-\s*t0\s*<\s*\d+")

    def _demo_besle_govdesi(self, canli=True):
        bas = KAYNAK.index("def demo_besle(")
        son = KAYNAK.index("def main():", bas)
        govde = KAYNAK[bas:son]
        if not canli:
            return govde
        # Yorumlar TARIHSEL kayittir: kaldirilan sure sinirinin NE OLDUGU
        # yorumda yaziyor. Canli kod aranir, anlati degil. (Bu kapi ilk
        # kosusunda tam da kendi yorumunu yakaladi.)
        return chr(10).join(s for s in govde.splitlines()
                            if not s.strip().startswith("#"))

    def test_besleme_dongusu_SURESIZ(self):
        bulunan = self.DESEN.findall(self._demo_besle_govdesi())
        self.assertEqual([], bulunan,
                         "besleme hala sureli: " + repr(bulunan) + " — sunum bu "
                         "sureyi asarsa ekran kendiliginden 'baglanti yok'a duser")

    def test_MUTASYON_deseni_calisiyor(self):
        self.assertTrue(
            self.DESEN.findall("        while time.time() - t0 < 600:"),
            "desen sure sinirini yakalamiyor — kapi bos")

    def test_MUTASYON_yorum_suzgeci_kapiyi_KORELTMIYOR(self):
        """Yorum ayiklamasi, CANLI bir `while` satirini de yutuyor olsaydi
        kapi bos olurdu: suzgec yalnizca `#` ile baslayan satiri atmali."""
        ornek = ("        # eskiden while time.time() - t0 < 600 yaziyordu" +
                 chr(10) + "        while time.time() - t0 < 900:")
        canli = chr(10).join(s for s in ornek.splitlines()
                             if not s.strip().startswith("#"))
        self.assertEqual(1, len(self.DESEN.findall(canli)),
                         "suzgec canli satiri da yuttu — kapi hicbir seyi "
                         "olcmuyor olurdu")

    def test_SURE_SINIRI_yorumda_ANLATILIYOR(self):
        """Kaldirilan kusur, kaynakta NEDENIYLE duruyor mu (kor duzeltme yok)."""
        ham = self._demo_besle_govdesi(canli=False)
        self.assertIn("T179", ham)
        self.assertIn("10 DAKIKADA", ham.upper())

    def test_batarya_uzun_sunumda_EKSIYE_DUSMEZ(self):
        """3 saatlik bir oturumda ekran '-1.2 V' gostermemeli."""
        govde = self._demo_besle_govdesi()
        self.assertIn("max(11.1, 12.6", govde)
        self.assertIn("max(11.0, 11.9", govde)


if __name__ == "__main__":
    unittest.main()
