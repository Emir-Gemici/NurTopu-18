#!/usr/bin/env python3
"""NEDEN: ARM/DISARM/RTL/LAND/PARACHUTE uçuş komut hattındaki ÜÇ kapı, sahada
komutun İHA'ya hiç ulaşmamasına yol açacak biçimde YANLIŞ BÜYÜKLÜĞÜ ölçüyordu.
Bu dosya üç düzeltmeyi de davranışla kilitler (mimar kararları K-1/K-2/K-3):

  K-1  Yaş kapısı `simdi - damga` ile İKİ AYRI MAKİNENİN saat farkını ölçüyordu
       (damgayı YKS dizüstü basar, `simdi`yi Jetson okur; Jetson NANO'da RTC
       pili YOKTUR). Kapı kaldırılmadı: yaş artık trafikten kestirilen saat
       ofsetine GÖRE ölçülür. Burada X = 300 s (5 dakika) sapmayla ÖLÇÜLÜR.
  K-2  Sonuç önbelleği anahtarı aktarımdan ÖNCE zehirleniyordu; MAVLink'e hiç
       ulaşmamış bir teşebbüs aynı `(oturum, seq, cmd)`i kalıcı olarak
       öldürüyor ve D-02/K4 tekrar merdivenini bitiriyordu. Terminal olan şey
       artık MAVLink'e ULAŞMIŞ denemedir.
  K-3  COMMAND_ACK'in `srcComponent`i (kim cevapladı) `target_component` ile
       (kime gönderdim) eşitleniyordu; ArduPilot komutu her zaman OTOPİLOT
       bileşeni olarak cevaplar. Kapı kalır, yalnız doğru kümeyi ölçer.

Kapıların hiçbiri gevşetilmedi: her düzeltmenin yanına, aynı kapının hâlâ
REDDETTİĞİ durum da yazıldı.
"""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from pymavlink import mavutil  # noqa: E402

import iha_komut_alici as ika  # noqa: E402
from protocol import command, decode  # noqa: E402

# ── Sahanın ölçüldüğü sayılar (hepsi AÇIKÇA yazılı) ─────────────────────────
YKS_SAATI = 1_700_000_000.0     # YKS dizüstünün duvar saati (damgayı o basar)
# X = 300 s: İHA'nın (Jetson) saati YKS'den BEŞ DAKİKA GERİDE. Yön bilerek
# seçildi — RTC pilsiz Jetson açılışta bayat bir ana düşer, yani `simdi`
# damganın GERİSİNDE kalır ve eski kapı `yas < 0` deyip komutu REDDEDERDİ.
SAAT_SAPMASI_S = 300.0
IHA_SAATI = YKS_SAATI - SAAT_SAPMASI_S
# Saha tekrar merdiveni (D-02/K4, comms/komut_tekrar.py): AYNI mesaj, AYNI seq.
TEKRAR_ARALIGI_S = ika.ARM_TEKRAR_ARALIGI_S
OTURUM = "saha-oturumu-21eylul"
KAYNAK = ("10.20.30.40", 5005)
# MAV_COMP_ID_GIMBAL benzeri, otopilot OLMAYAN bir bileşen: ACK basamaz.
YABANCI_COMPONENT = 154


class _Link:
    def __init__(self):
        self.gonderilen = []

    def send(self, veri, adr=None):
        self.gonderilen.append((decode(veri), adr))


class _Saat:
    """Enjekte edilen monotonik alış-tarafı saati (elle ilerletilir)."""

    def __init__(self, t=5_000.0):
        self.t = float(t)

    def __call__(self):
        return self.t

    def ilerlet(self, dt):
        self.t += float(dt)


class _Mav:
    """Pixhawk ucu: COMMAND_LONG'u kaydeder, ardından COMMAND_ACK döner.

    sonuc     : "kabul" | "ret" | "sessiz"
    component : COMMAND_ACK'i basan bileşen (get_srcComponent)
    hedef_bilinir / gonderim_hatasi : K-2'nin "MAVLink'e HİÇ ULAŞMADI" yolları.
    """

    def __init__(self, *, sonuc="kabul", component=ika.VARSAYILAN_HEDEF_COMPONENT,
                 sysid=ika.VARSAYILAN_HEDEF_SYSID, hedef_bilinir=True,
                 gonderim_hatasi=None):
        self.sonuc = sonuc
        self.component = component
        self.sysid = sysid
        self.gonderim_hatasi = gonderim_hatasi
        self.komutlar = []
        self._bekleyen = []
        # `mav_hedefi_biliniyor_mu` yalnız `udp_server is True` iken kapanır.
        self.udp_server = True
        self.clients = set() if not hedef_bilinir else {("127.0.0.1", 14550)}
        self.mav = SimpleNamespace(command_long_send=self._gonder)

    def hedefi_ogren(self):
        self.clients.add(("127.0.0.1", 14550))

    def _gonder(self, _sys, _comp, mav_cmd, *_param):
        if self.gonderim_hatasi is not None:
            hata, self.gonderim_hatasi = self.gonderim_hatasi, None
            raise hata
        self.komutlar.append(mav_cmd)
        self._bekleyen.append(mav_cmd)

    def recv_match(self, type=None, **_kw):
        if type != "COMMAND_ACK" or not self._bekleyen or self.sonuc == "sessiz":
            return None
        mav_cmd = self._bekleyen.pop(0)
        m = mavutil.mavlink
        return SimpleNamespace(
            command=mav_cmd,
            result=(m.MAV_RESULT_ACCEPTED if self.sonuc == "kabul"
                    else m.MAV_RESULT_DENIED),
            get_srcSystem=lambda: self.sysid,
            get_srcComponent=lambda: self.component,
        )


def _alici(mav, *, saat=None, **kw):
    """Alıcıyı SAPMIŞ İHA saatiyle kur; log görünür kalsın diye toplanır.

    İHA'nın duvar saati monotonik saatle BİRLİKTE ilerler (gerçek makine gibi),
    ama YKS'nin saatinden kalıcı olarak ``SAAT_SAPMASI_S`` geridedir.
    """
    link = _Link()
    saat = saat if saat is not None else _Saat()
    baslangic = saat.t
    kayit = []
    alici = ika.IhaKomutAlici(
        link, mav, saat=saat,
        duvar_saati=lambda: IHA_SAATI + (saat.t - baslangic),
        izinli_kaynak=KAYNAK, **kw)
    alici._logla = lambda metin, kirmizi=False: kayit.append((metin, kirmizi))
    return alici, link, saat, kayit


def _sapmayi_ogret(alici, saat, *, seq=1):
    """Tekrar merdiveninin ilk basamaklarını yürüt: saat ofsetini kestirt.

    Bu basamaklar kapıdan GEÇMEZ (henüz yeterli örnek yok) ve MAVLink'e
    ulaşmadıkları için sonuç önbelleğini de zehirlemezler — K-2'nin ta kendisi.
    """
    mesaj = _cmd(seq=seq)
    for _ in range(ika.KOMUT_SAAT_OFSETI_EN_AZ_ORNEK):
        assert alici.isle(mesaj, KAYNAK) is False
        saat.ilerlet(TEKRAR_ARALIGI_S)


def _cmd(ad=ika.CMD_ARM, *, seq=11, t=YKS_SAATI, oturum=OTURUM):
    """YKS'nin telde ürettiği komut — damga YKS'nin duvar saatindendir."""
    mesaj = command(ad, "iha", seq=seq, oturum=oturum)
    mesaj["t"] = t
    return mesaj


class K1SaatSapmasiTests(unittest.TestCase):
    """Yaş kapısı çapraz-makine sapmasına karşı bağışık; ama hâlâ kapı."""

    def test_bes_dakika_sapmada_kritik_komut_tekrar_merdiveniyle_GECER(self):
        """X = 300 s sapma: saha tekrar merdiveni komutu Pixhawk'a ULAŞTIRIR.

        Eski kapı `yas = simdi - damga = -300 s` deyip ARM/DISARM/RTL/LAND/
        PARACHUTE'un HEPSİNİ reddediyordu — araç indirilemezdi.
        """
        for ad in (ika.CMD_ARM, ika.CMD_DISARM, ika.CMD_RTL, ika.CMD_LAND,
                   ika.CMD_PARACHUTE):
            with self.subTest(komut=ad):
                mav = _Mav()
                alici, link, saat, _ = _alici(mav)
                mesaj = _cmd(ad, seq=31)
                # Merdivenin ilk basamakları: ofset henüz kestirilemedi, kapı
                # SIKI davranır ve bilinmeyen sapmayı KABUL ETMEZ.
                for basamak in range(ika.KOMUT_SAAT_OFSETI_EN_AZ_ORNEK):
                    self.assertFalse(alici.isle(mesaj, KAYNAK),
                                     f"{ad} basamak {basamak} erken gecti")
                    self.assertEqual([], mav.komutlar)
                    saat.ilerlet(TEKRAR_ARALIGI_S)
                # Sonraki basamak (D-02/K4: AYNI mesaj, AYNI seq): önceki
                # örnekler sapmayı ele verir, yaş ofsete göre ölçülür ve komut
                # Pixhawk'a GİDER. Sahadaki bedel yalnız 2 × 0,25 s gecikmedir.
                self.assertTrue(alici.isle(mesaj, KAYNAK),
                                f"{ad} 5 dk saat sapmasinda GECEMEDI")
                self.assertEqual(1, len(mav.komutlar))
                self.assertEqual(1, len(link.gonderilen))
                self.assertEqual(-SAAT_SAPMASI_S, alici._son_ofset)

    def test_tek_cerceve_kendi_damgasiyla_kendini_AKLAYAMAZ(self):
        """Kestirim en az iki örnek ister: tek çerçeve kapıyı açamaz."""
        mav = _Mav()
        alici, link, _saat, _ = _alici(mav)
        self.assertFalse(alici.isle(_cmd(seq=32), KAYNAK))
        self.assertIsNone(alici._son_ofset)
        self.assertEqual([], mav.komutlar)
        self.assertEqual(1, alici.sayac["zaman_red"])

    def test_sapma_ogrenildikten_SONRA_da_bayat_damga_REDDEDILIR(self):
        """Kapı gevşemedi: ofset bilinirken bile tavanı aşan yaş RED."""
        mav = _Mav()
        alici, link, saat, _ = _alici(mav)
        tavan = ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM]
        _sapmayi_ogret(alici, saat, seq=33)
        # Aynı sapmayla ama tavanı aşacak kadar ESKİ damga: yine RED.
        bayat = _cmd(seq=34, t=YKS_SAATI - tavan - 0.01)
        self.assertFalse(alici.isle(bayat, KAYNAK))
        self.assertEqual(-SAAT_SAPMASI_S, alici._son_ofset,
                         "sapma kestirimi bayat cerceveyle kaydi")
        self.assertEqual([], mav.komutlar, "bayat komut eyleyiciye ulasti")
        self.assertEqual([], link.gonderilen)
        # Israr etse de geçemez: reddedilen çerçeve kestirimi kaydıramaz.
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertFalse(alici.isle(bayat, KAYNAK))
        self.assertEqual([], mav.komutlar)

    def test_sapma_ogrenildikten_SONRA_da_ileri_damga_REDDEDILIR(self):
        """Ofsetin İLERİSİNDE bir damga (uydurma taze) hâlâ kabul edilmez.

        Bu, kestirimin çerçevenin KENDİ örneğini içermemesinin sebebidir:
        içerseydi ileri damga ofseti kendine çeker ve kapıdan geçerdi.
        """
        mav = _Mav()
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat, seq=35)
        ileri = _cmd(seq=36, t=YKS_SAATI + 1.0)
        self.assertFalse(alici.isle(ileri, KAYNAK))
        self.assertEqual([], mav.komutlar)
        # Ve ileri damga ısrar ederse de geçemez (kendi örneğiyle aklanamaz).
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertFalse(alici.isle(ileri, KAYNAK))
        self.assertEqual([], mav.komutlar)

    def test_cilgin_damga_ofset_kestirimini_KAYDIRAMAZ(self):
        """Sapma bandı dışındaki damga örnek olarak alınmaz (fail-closed)."""
        mav = _Mav()
        alici, link, saat, _ = _alici(mav)
        cilgin = _cmd(seq=37, t=YKS_SAATI + 10.0 * ika.KOMUT_SAAT_SAPMA_TAVANI_S)
        for _ in range(ika.KOMUT_SAAT_OFSETI_EN_AZ_ORNEK + 1):
            self.assertFalse(alici.isle(cilgin, KAYNAK))
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertIsNone(alici._son_ofset, "cilgin damga ofseti kaydirdi")
        self.assertEqual([], mav.komutlar)

    def test_yas_kapisi_hala_sayac_ve_KIRMIZI_log_birakiyor(self):
        """fail-VISIBLE: reddedilen komut görünür kayıt bırakır."""
        mav = _Mav()
        alici, _link, _saat, kayit = _alici(mav)
        self.assertFalse(alici.isle(_cmd(seq=38), KAYNAK))
        self.assertEqual(1, alici.sayac["zaman_red"])
        self.assertTrue(any(kirmizi and "zaman RED" in metin
                            for metin, kirmizi in kayit), kayit)


class K2SonucOnbellegiTests(unittest.TestCase):
    """Terminal olan şey MAVLink'e ULAŞMIŞ denemedir, teşebbüs değil."""

    def test_hedef_bilinmiyorken_ayni_seq_TEKRAR_denenip_GECER(self):
        """Saha açılışı: Pixhawk'tan daha paket gelmemiş. Merdiven ölmemeli."""
        mav = _Mav(hedef_bilinir=False)
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat)
        mesaj = _cmd(seq=41)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual([], mav.komutlar)
        self.assertNotIn((OTURUM, 41, ika.CMD_ARM), alici._komut_sonuclari,
                         "aktarilmamis tesebbus anahtari ZEHIRLEDI")
        mav.hedefi_ogren()                    # ilk MAVLink paketi geldi
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertTrue(alici.isle(mesaj, KAYNAK),
                        "ayni seq tekrari reddedildi; tekrar merdiveni oldu")
        self.assertEqual(1, len(mav.komutlar))
        self.assertEqual(1, len(link.gonderilen))

    def test_mavlink_baglantisi_yokken_ayni_seq_TEKRAR_denenip_GECER(self):
        mav = _Mav()
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat)
        alici.mav = None                       # bağlantı henüz açılmadı
        mesaj = _cmd(seq=42)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertNotIn((OTURUM, 42, ika.CMD_ARM), alici._komut_sonuclari)
        alici.mav = mav
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar))

    def test_aktarim_istisnasindan_sonra_ayni_seq_TEKRAR_denenip_GECER(self):
        mav = _Mav(gonderim_hatasi=RuntimeError("seri hat bir an kapandi"))
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat)
        mesaj = _cmd(seq=43)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual([], mav.komutlar)
        self.assertNotIn((OTURUM, 43, ika.CMD_ARM), alici._komut_sonuclari)
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar))

    def test_pixhawk_REDDEDINCE_ayni_seq_bir_daha_CALISMAZ(self):
        """Gecikmiş eylem yok: kesin RET terminaldir."""
        mav = _Mav(sonuc="ret")
        alici, link, saat, kayit = _alici(mav)
        _sapmayi_ogret(alici, saat)
        mesaj = _cmd(seq=44)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar))
        self.assertIs(False, alici._komut_sonuclari[(OTURUM, 44, ika.CMD_ARM)])
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar),
                         "REDDEDILEN komut gecikmeli olarak YENIDEN calisti")
        self.assertEqual([], link.gonderilen)
        self.assertEqual(1, alici.sayac["tekrar"])

    def test_ACK_gelmezse_de_ayni_seq_bir_daha_CALISMAZ(self):
        """COMMAND_LONG tele çıktıysa araç işlemiş OLABİLİR: terminaldir."""
        mav = _Mav(sonuc="sessiz")
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat)
        mesaj = _cmd(seq=45)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar))
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertFalse(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar))

    def test_KABUL_edilen_komut_yinelenmez_ama_ACK_yeniden_yollanir(self):
        mav = _Mav()
        alici, link, saat, _ = _alici(mav)
        _sapmayi_ogret(alici, saat)
        mesaj = _cmd(seq=46)
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertTrue(alici.isle(mesaj, KAYNAK))
        self.assertEqual(1, len(mav.komutlar), "eyleyici YINELENDI")
        self.assertEqual(2, len(link.gonderilen), "kayip ACK yinelenmedi")


class K3AckBileseniTests(unittest.TestCase):
    """ACK'i GÖNDEREN bileşen ile komutun ADRESLENDİĞİ bileşen ayrı alanlardır."""

    def _kur(self, *, ack_component, target_component):
        mav = _Mav(component=ack_component)
        alici, link, saat, kayit = _alici(
            mav, target_component=target_component)
        _sapmayi_ogret(alici, saat)             # K-1 ofsetini kestirt
        return mav, alici, link, kayit

    def test_otopilot_bileseninin_ACKi_target_component_farkli_olsa_da_KABUL(self):
        """ArduPilot komutu OTOPİLOT olarak cevaplar; hedef bileşen 3 olsa bile.

        Uçtan uca iki testi düşüren kapı buydu (3 Eylül ikili arama ölçümü).
        """
        mav, alici, link, _ = self._kur(
            ack_component=mavutil.mavlink.MAV_COMP_ID_AUTOPILOT1,
            target_component=3)
        self.assertTrue(alici.isle(_cmd(seq=51), KAYNAK))
        self.assertEqual(1, len(link.gonderilen))

    def test_adreslenen_bilesenin_kendi_ACKi_KABUL(self):
        mav, alici, link, _ = self._kur(ack_component=3, target_component=3)
        self.assertTrue(alici.isle(_cmd(seq=52), KAYNAK))
        self.assertEqual(1, len(link.gonderilen))

    def test_belirtilmemis_bilesen_geriye_uyumlu_KABUL(self):
        mav, alici, link, _ = self._kur(
            ack_component=ika.MAVLINK_BELIRTILMEMIS_COMPONENT,
            target_component=3)
        self.assertTrue(alici.isle(_cmd(seq=53), KAYNAK))

    def test_yabanci_bilesenin_ACKi_REDDEDILIR_ve_gorunur_kayit_birakir(self):
        """Gimbal/kamera/companion bu komutun ACK'ini VEREMEZ: kapı kapalı."""
        mav, alici, link, kayit = self._kur(
            ack_component=YABANCI_COMPONENT, target_component=3)
        self.assertFalse(alici.isle(_cmd(seq=54), KAYNAK))
        self.assertEqual(1, len(mav.komutlar))     # gönderildi ama kabul yok
        self.assertEqual([], link.gonderilen)
        self.assertTrue(any(kirmizi and "yabanci component" in metin
                            for metin, kirmizi in kayit), kayit)

    def test_yetkili_bilesen_kumesi_ACIKCA_yazili(self):
        """Varsayım koda yazıldı: küme otopilot + adreslenen + belirtilmemiş."""
        mav = _Mav()
        alici, _link, _saat, _ = _alici(mav, target_component=3)
        m = ika._mavutil_al().mavlink
        self.assertEqual(
            (ika.MAVLINK_BELIRTILMEMIS_COMPONENT,
             int(m.MAV_COMP_ID_AUTOPILOT1), 3),
            alici._ack_basabilen_bilesenler(m))
        self.assertNotIn(YABANCI_COMPONENT, alici._ack_basabilen_bilesenler(m))

    def test_yabanci_sysid_ACKi_hala_REDDEDILIR(self):
        """K-3 sysid kapısını GEVŞETMEDİ (D-403)."""
        mav = _Mav(sysid=ika.VARSAYILAN_HEDEF_SYSID + 1)
        alici, link, saat, kayit = _alici(mav)
        _sapmayi_ogret(alici, saat)
        self.assertFalse(alici.isle(_cmd(seq=55), KAYNAK))
        self.assertEqual([], link.gonderilen)
        self.assertTrue(any("yabanci sysid" in metin for metin, _k in kayit))


if __name__ == "__main__":
    unittest.main()
