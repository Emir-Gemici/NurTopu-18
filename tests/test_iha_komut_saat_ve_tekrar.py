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


# ── K-A / K-B (2026-09-04) ──────────────────────────────────────────────────
# K-1 düzeltmesi kapıyı doğru büyüklüğü ölçer hâle getirdi ama İKİ kusur kaldı;
# ikisi de saha ÖLÇÜMÜYLE yeniden üretildi (bu dosyanın altındaki sayılar):
#
#   K-A  `_ornekle` içindeki mutlak sapma tavanı ÖĞRENMEYİ kilitliyordu. Ofset
#        bilinmezken `ham` iki saatin FARKI'dır; sapma tavanı aşınca öğrenmek
#        için gereken örneğin TA KENDİSİ eleniyor -> ofset ASLA öğrenilmiyor ->
#        kritik komutlar KALICI olarak reddediliyordu.
#        ÖLÇÜM (düzeltme ÖNCESİ, 2 saat sapma, ARM merdiveni 20 basamak):
#            ARM geçti mi = HAYIR · MAVLink'e giden = 0 · zaman_red = 20
#            örnek sayısı = 0 · öğrenilen ofset = None
#        1970'e açılmış Jetson (sapma ~53 yıl) da aynı: HAYIR / 0.
#        ÖLÇÜM (düzeltme SONRASI): ikisi de 7. denemede GEÇİYOR.
#
#   K-B  Ofset öğrenildikten sonra saat BASAMAKLI düzeltilirse penceredeki
#        ESKİ örnekler kestirimi eski değerde tutuyordu.
#        ÖLÇÜM (düzeltme ÖNCESİ, ofset -600 s öğrenildi, saat +600 s adımlandı):
#            ölü pencere = 60,00 s · o sürede reddedilen komut = 241
#        ÖLÇÜM (düzeltme SONRASI): ölü süre 1,75 s (7 basamak).
#
# Kapıların hiçbiri gevşetilmedi: her yeni davranışın yanına, aynı kapının
# hâlâ REDDETTİĞİ durum ve yeniden-oynatma savunmasının hâlâ tuttuğu da yazıldı.

# Sahada ölçülen iki sapma. İkisi de eski mutlak tavanın (30 dk) DIŞINDADIR.
IKI_SAAT_SAPMASI_S = 2.0 * 60.0 * 60.0
# RTC pili olmayan Jetson 1970'e (ya da son kapanma anına) açılır: sapma YIL
# mertebesinde olur. "30 dakika makul band" varsayımı burada çöker.
JETSON_1970_IHA_SAATI = 100.0


def _sapmali_alici(mav, iha_saati, *, saat=None, **kw):
    """Alıcıyı İSTENEN İHA duvar saatiyle kur (dosya başındaki `_alici` 300 s'e
    sabitlidir; K-A senaryoları çok daha büyük sapma ister)."""
    link = _Link()
    saat = saat if saat is not None else _Saat()
    baslangic = saat.t
    kayit = []
    durum = {"iha": float(iha_saati)}
    alici = ika.IhaKomutAlici(
        link, mav, saat=saat,
        duvar_saati=lambda: durum["iha"] + (saat.t - baslangic),
        izinli_kaynak=KAYNAK, **kw)
    alici._logla = lambda metin, kirmizi=False: kayit.append((metin, kirmizi))
    return alici, link, saat, kayit, durum


def _merdiveni_yuru(alici, saat, mesaj, *, basamak=None, aralik=None):
    """D-02/K4 tekrar merdivenini yürüt; komutun GEÇTİĞİ basamağı döndür.

    Dönen: 1'den başlayan deneme sayısı, hiç geçmediyse ``None``.
    """
    basamak = ika.ARM_TEKRAR_UST_SINIRI if basamak is None else basamak
    aralik = TEKRAR_ARALIGI_S if aralik is None else aralik
    for i in range(basamak):
        if alici.isle(mesaj, KAYNAK):
            return i + 1
        saat.ilerlet(aralik)
    return None


# Ölçülen ve KİLİTLENEN deneme sayısı: bant dışı (büyük) bir sapmanın kestirimi
# `KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK` adet BİRBİRİNİ DESTEKLEYEN örnek ister.
# Bu örnekler merdivenin ilk basamaklarında toplanır; komut BİR SONRAKİ
# basamakta geçer. ARM merdiveni 20 basamak olduğu için bu, merdivenin ilk
# üçte birinden de kısadır.
BEKLENEN_DENEME = ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK + 1


class KASapmaTavaniOgrenmeyiKilitlemezTests(unittest.TestCase):
    """KARAR-1: tavan ÖĞRENMEYİ değil KAYMAYI engeller."""

    def test_IKI_SAAT_sapmada_kritik_komutlarin_HEPSI_gecer(self):
        """Düzeltme öncesi ÖLÇÜM: 20/20 red, MAVLink 0. Şimdi 7. denemede geçer."""
        for ad in (ika.CMD_ARM, ika.CMD_DISARM, ika.CMD_RTL, ika.CMD_LAND,
                   ika.CMD_PARACHUTE):
            with self.subTest(komut=ad):
                mav = _Mav()
                alici, link, saat, _kayit, _d = _sapmali_alici(
                    mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
                deneme = _merdiveni_yuru(alici, saat, _cmd(ad, seq=61))
                self.assertEqual(BEKLENEN_DENEME, deneme,
                                 f"{ad} 2 saat sapmada beklenen basamakta gecmedi")
                self.assertEqual(1, len(mav.komutlar))
                self.assertEqual(1, len(link.gonderilen))
                self.assertEqual(-IKI_SAAT_SAPMASI_S, alici._son_ofset)
                # Bedel merdivenin İLK saniyesidir; merdiven 5 s sürer.
                self.assertLess(
                    (deneme - 1) * TEKRAR_ARALIGI_S,
                    ika.ARM_TEKRAR_ARALIGI_S * ika.ARM_TEKRAR_UST_SINIRI)

    def test_1970e_acilmis_JETSON_senaryosu_da_gecer(self):
        """RTC pilsiz Jetson: sapma YIL mertebesinde. Eski tavan bunu ÖLDÜRDÜ."""
        mav = _Mav()
        alici, link, saat, _kayit, _d = _sapmali_alici(mav, JETSON_1970_IHA_SAATI)
        beklenen_ofset = JETSON_1970_IHA_SAATI - YKS_SAATI
        self.assertGreater(abs(beklenen_ofset), 365.0 * 24.0 * 3600.0,
                           "senaryo yil mertebesinde sapma olmali")
        deneme = _merdiveni_yuru(alici, saat, _cmd(seq=62))
        self.assertEqual(BEKLENEN_DENEME, deneme)
        self.assertEqual(1, len(mav.komutlar))
        self.assertEqual(beklenen_ofset, alici._son_ofset)

    def test_TEK_cilgin_cerceve_bant_disi_ofset_KURAMAZ(self):
        """Bant dışı kestirim GENİŞ kanıt ister; tek çerçeve (ve azı) yetmez."""
        mav = _Mav()
        alici, link, saat, _kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        mesaj = _cmd(seq=63)
        for basamak in range(ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK - 1):
            self.assertFalse(alici.isle(mesaj, KAYNAK),
                             f"basamak {basamak} erken gecti")
            self.assertIsNone(alici._son_ofset,
                              f"basamak {basamak}: yetersiz kanitla ofset kuruldu")
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual([], mav.komutlar)
        self.assertEqual(ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK - 1,
                         alici.sayac["zaman_red"])

    def test_TEK_cilgin_cerceve_ogrenilmis_ofseti_KAYDIRAMAZ(self):
        """Ofset bilinirken bant dışı TEK çerçeve ne geçer ne kestirimi bozar."""
        mav = _Mav()
        alici, link, saat, _kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        self.assertEqual(BEKLENEN_DENEME,
                         _merdiveni_yuru(alici, saat, _cmd(seq=64)))
        saat.ilerlet(TEKRAR_ARALIGI_S)
        cilgin = _cmd(seq=65, t=YKS_SAATI + 10.0 * ika.KOMUT_SAAT_SAPMA_TAVANI_S)
        self.assertFalse(alici.isle(cilgin, KAYNAK))
        self.assertEqual(-IKI_SAAT_SAPMASI_S, alici._son_ofset,
                         "tek cilgin cerceve ofseti KAYDIRDI")
        self.assertEqual(1, len(mav.komutlar))

    def test_bant_disi_ogrenmede_de_bayat_ve_ileri_damga_REDDEDILIR(self):
        """Kapı gevşemedi: büyük sapma öğrenilse bile tazelik ölçülmeye devam."""
        tavan = ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM]
        for etiket, damga in (("bayat", YKS_SAATI - tavan - 0.01),
                              ("ileri", YKS_SAATI + 1.0)):
            with self.subTest(damga=etiket):
                mav = _Mav()
                alici, link, saat, _kayit, _d = _sapmali_alici(
                    mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
                self.assertEqual(BEKLENEN_DENEME,
                                 _merdiveni_yuru(alici, saat, _cmd(seq=66)))
                saat.ilerlet(TEKRAR_ARALIGI_S)
                # Damga YKS'nin O ANKİ saatine göre kurulur: merdiven boyunca
                # geçen süre "bayat/ileri" niteliğini bozmasın.
                simdi_yks = YKS_SAATI + (saat.t - 5_000.0)
                kotu = _cmd(seq=67, t=simdi_yks + (damga - YKS_SAATI))
                self.assertFalse(alici.isle(kotu, KAYNAK))
                saat.ilerlet(TEKRAR_ARALIGI_S)
                self.assertFalse(alici.isle(kotu, KAYNAK))
                self.assertEqual(1, len(mav.komutlar),
                                 f"{etiket} damga eyleyiciye ULASTI")
                self.assertEqual(-IKI_SAAT_SAPMASI_S, alici._son_ofset)

    def test_acikca_BOZUK_damgalar_hala_REDDEDILIR(self):
        """NaN / bool / sonsuz / eksik damga: fail-closed, fail-visible."""
        for etiket, damga in (("nan", float("nan")), ("bool", True),
                              ("sonsuz", float("inf")),
                              ("eksi_sonsuz", float("-inf")),
                              ("metin", "1700000000")):
            with self.subTest(damga=etiket):
                mav = _Mav()
                alici, link, saat, kayit, _d = _sapmali_alici(
                    mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
                bozuk = _cmd(seq=68, t=damga)
                for _ in range(ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK + 3):
                    self.assertFalse(alici.isle(bozuk, KAYNAK))
                    saat.ilerlet(TEKRAR_ARALIGI_S)
                self.assertEqual([], mav.komutlar, f"{etiket} damga GECTI")
                self.assertEqual([], link.gonderilen)
                self.assertIsNone(alici._son_ofset,
                                  f"{etiket} damga ofset kurdu")
                self.assertTrue(any(kirmizi and "zaman RED" in metin
                                    for metin, kirmizi in kayit), kayit)

    def test_damgasiz_CMD_de_REDDEDILIR(self):
        mav = _Mav()
        alici, link, saat, _kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        damgasiz = _cmd(seq=69)
        damgasiz.pop("t")
        for _ in range(ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK + 3):
            self.assertFalse(alici.isle(damgasiz, KAYNAK))
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual([], mav.komutlar)
        self.assertIsNone(alici._son_ofset)

    def test_ofset_OGRENILINCE_gorunur_kayit_birakir(self):
        """KARAR-3: sahada 'ARM neden gecmedi' sorusunun cevabi logda olmali."""
        mav = _Mav()
        alici, _link, saat, kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        self.assertEqual(BEKLENEN_DENEME,
                         _merdiveni_yuru(alici, saat, _cmd(seq=70)))
        ogrenme = [metin for metin, _k in kayit if "saat ofseti OGRENILDI" in metin]
        self.assertEqual(1, len(ogrenme), kayit)
        self.assertIn("-7200.000", ogrenme[0])


# Adım YEREL ölçülür (duvar saati monotonik saate göre zıpladı mı), trafikten
# çıkarılmaz. Bu yüzden adımdan SONRAKİ İLK çerçeve zaten geçer: kestirim
# adımın kendisi kadar düzeltilir, beklenecek örnek yoktur.
BEKLENEN_ADIM_DENEME = 1


class KBSaatAdimindaOluPencereYokTests(unittest.TestCase):
    """KARAR-2: yerel saat adımı algılanır, kestirim adım kadar düzeltilir."""

    def _ogren_ve_adimla(self, *, ilk_sapma, adim):
        """Ofseti öğret, sonra İHA DUVAR saatini BASAMAKLI kaydır.

        `saat` (monotonik) adımdan ETKİLENMEZ — gerçek makinede de öyledir;
        kusurun ve düzeltmenin bütün ayrımı buradadır.
        """
        mav = _Mav()
        alici, link, saat, kayit, durum = _sapmali_alici(
            mav, YKS_SAATI + ilk_sapma)
        deneme = _merdiveni_yuru(alici, saat, _cmd(seq=71))
        self.assertIsNotNone(deneme, "on kosul: ofset ogrenilemedi")
        self.assertEqual(ilk_sapma, alici._son_ofset)
        durum["iha"] += adim                     # NTP step / timedatectl
        return mav, alici, link, saat, kayit

    def _adimdan_sonra_taze_komut(self, saat, seq):
        """YKS'nin O AN bastığı taze damga (YKS saati sapmadan bağımsızdır)."""
        return _cmd(seq=seq, t=YKS_SAATI + (saat.t - 5_000.0))

    def _adimdan_sonra_yuru(self, alici, saat, ilk_seq, *, basamak=400):
        for i in range(basamak):
            saat.ilerlet(TEKRAR_ARALIGI_S)
            if alici.isle(self._adimdan_sonra_taze_komut(saat, ilk_seq + i),
                          KAYNAK):
                return i + 1
        return None

    def test_ILERI_saat_adiminda_olu_pencere_YOK(self):
        """ÖLÇÜM: düzeltme öncesi 60,00 s ölü / 241 red. Şimdi 1 basamak."""
        mav, alici, link, saat, _kayit = self._ogren_ve_adimla(
            ilk_sapma=-600.0, adim=+600.0)
        redler = alici.sayac["zaman_red"]
        gecen = self._adimdan_sonra_yuru(alici, saat, 200)
        self.assertEqual(BEKLENEN_ADIM_DENEME, gecen, "adim algilanmadi")
        olu_sure = gecen * TEKRAR_ARALIGI_S
        self.assertLess(olu_sure, ika.KOMUT_SAAT_OFSETI_PENCERESI_S / 10.0,
                        f"olu pencere hala uzun: {olu_sure} s")
        self.assertEqual(redler, alici.sayac["zaman_red"],
                         "adimdan sonra komut yine de reddedildi")
        self.assertAlmostEqual(0.0, alici._son_ofset, places=6)
        self.assertEqual(2, len(mav.komutlar))

    def test_GERI_saat_adiminda_da_olu_pencere_YOK(self):
        """Operatör saati GERİ alırsa da kestirim düzelir (simetrik)."""
        mav, alici, _link, saat, _kayit = self._ogren_ve_adimla(
            ilk_sapma=-600.0, adim=-600.0)
        self.assertEqual(BEKLENEN_ADIM_DENEME,
                         self._adimdan_sonra_yuru(alici, saat, 250))
        self.assertAlmostEqual(-1200.0, alici._son_ofset, places=6)
        self.assertEqual(2, len(mav.komutlar))

    def test_saat_adimi_gorunur_kayit_birakir(self):
        """KARAR-3: adım algılandığında sıçrama ve yeni kestirim logda."""
        _mav, alici, _link, saat, kayit = self._ogren_ve_adimla(
            ilk_sapma=-600.0, adim=+600.0)
        self.assertEqual(BEKLENEN_ADIM_DENEME,
                         self._adimdan_sonra_yuru(alici, saat, 300))
        adimlar = [metin for metin, _k in kayit
                   if "YEREL saat ADIMI algilandi" in metin]
        self.assertEqual(1, len(adimlar), kayit)
        self.assertIn("+600.000", adimlar[0])
        self.assertIn("-600.0", adimlar[0])          # duzeltilen eski kestirim

    def test_NTP_JETSONU_1970ten_duzeltince_de_olu_pencere_YOK(self):
        """5 Eylul senaryosu: Jetson aga ilk baglanir, NTP saati duzeltir."""
        mav = _Mav()
        alici, _link, saat, _kayit, durum = _sapmali_alici(
            mav, JETSON_1970_IHA_SAATI)
        self.assertEqual(BEKLENEN_DENEME,
                         _merdiveni_yuru(alici, saat, _cmd(seq=72)))
        durum["iha"] = YKS_SAATI              # NTP: saat YERİNE oturdu (sapma 0)
        self.assertEqual(BEKLENEN_ADIM_DENEME,
                         self._adimdan_sonra_yuru(alici, saat, 400))
        self.assertAlmostEqual(0.0, alici._son_ofset, delta=1e-3)
        self.assertEqual(2, len(mav.komutlar))

    def test_adim_kaniti_TRAFIKTEN_cikarilmaz_israrli_BAYAT_gonderici_yuruyemez(self):
        """🔴 4 Eylul'de OLCULEN delik: trafik-tabanli adim kaniti kullanilirsa
        israrli bayat bir gonderici, reddedilen cerceveleriyle kestirimi kendi
        uzerine YURUTUYOR ve 10. israrda MAVLink'e ULASIYORDU. Adim kaniti
        YALNIZ yerel oldugu icin bu yol kapali."""
        mav = _Mav()
        alici, link, saat, _kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        self.assertEqual(BEKLENEN_DENEME,
                         _merdiveni_yuru(alici, saat, _cmd(seq=73)))
        self.assertEqual(1, len(mav.komutlar))
        saat.ilerlet(ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM] + 1.0)
        bayat = _cmd(seq=74, t=YKS_SAATI)      # BAYAT damga, GORULMEMIS seq
        for israr in range(60):                # 15 s boyunca israr
            self.assertFalse(alici.isle(bayat, KAYNAK),
                             f"bayat cerceve {israr + 1}. israrda GECTI")
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual(1, len(mav.komutlar),
                         "israrli bayat gonderici eyleyiciye ULASTI")
        self.assertEqual(-IKI_SAAT_SAPMASI_S, alici._son_ofset,
                         "israrli bayat gonderici kestirimi YURUTTU")

    def test_esikten_KUCUK_saat_kaymasi_adim_SAYILMAZ(self):
        """NTP yavaşlatma (slew) mertebesindeki kayma kestirimi DÜŞÜRMEZ."""
        _mav, alici, _link, saat, kayit = self._ogren_ve_adimla(
            ilk_sapma=-600.0, adim=+ika.KOMUT_SAAT_ADIMI_ESIGI_S)
        for basamak in range(8):
            saat.ilerlet(TEKRAR_ARALIGI_S)
            alici.isle(self._adimdan_sonra_taze_komut(saat, 600 + basamak),
                       KAYNAK)
        self.assertEqual(-600.0, alici._son_ofset,
                         "esikten kucuk kayma kestirimi bozdu")
        self.assertEqual([], [m for m, _k in kayit if "ADIMI" in m], kayit)


class KAKBYenidenOynatmaKorunduTests(unittest.TestCase):
    """🔴 Saat kapısı GEVŞEMEDİ demek yetmez: replay savunması ÖLÇÜLÜR.

    Yeniden-oynatma savunması `(oturum, seq, cmd)` anahtarıdır. Saat kapısının
    işi TAZELİKtir; ikisi birbirinin yerine geçmez. Aşağıdaki testler saldırgan
    rolünü GERÇEKTEN oynar: geçmiş bir çerçeveyi yakalayıp yeniden gönderir.
    """

    def _gecmis_arm(self, iha_saati=None):
        """Bir ARM'ı gerçekten geçir; sonra o çerçeveyi 'yakalanmış' say."""
        iha_saati = (YKS_SAATI - IKI_SAAT_SAPMASI_S if iha_saati is None
                     else iha_saati)
        mav = _Mav()
        alici, link, saat, kayit, durum = _sapmali_alici(mav, iha_saati)
        mesaj = _cmd(seq=81)
        self.assertEqual(BEKLENEN_DENEME, _merdiveni_yuru(alici, saat, mesaj))
        self.assertEqual(1, len(mav.komutlar))
        return mav, alici, link, saat, kayit, durum, mesaj

    def test_ayni_oturum_seq_cmd_eyleyiciyi_BIR_DAHA_calistirmaz(self):
        mav, alici, link, saat, _kayit, _d, mesaj = self._gecmis_arm()
        for _ in range(5):
            saat.ilerlet(TEKRAR_ARALIGI_S)
            alici.isle(mesaj, KAYNAK)
        self.assertEqual(1, len(mav.komutlar),
                         "yakalanan cerceve eyleyiciyi YENIDEN calistirdi")
        self.assertGreaterEqual(alici.sayac["tekrar"], 5)

    def test_ESKI_cerceve_dakikalar_sonra_oynatilinca_CALISMAZ(self):
        """Saldırgan çerçeveyi kaydedip 5 dakika sonra tele basıyor.

        ÖNEMLİ: ölçülen şey EYLEYİCİdir. Saat kapısı çerçeveyi elese de
        elemese de, `(oturum, seq, cmd)` anahtarı COMMAND_LONG'un bir daha
        çıkmasını engeller — yineleyen ACK idempotenttir (D-02/K4 merdiveni
        böyle durur), eyleyici YENİDEN ÇALIŞMAZ.
        """
        mav, alici, link, saat, _kayit, _d, mesaj = self._gecmis_arm()
        saat.ilerlet(5.0 * 60.0)
        tekrar_oncesi = alici.sayac["tekrar"]
        for _ in range(3 * ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK):
            alici.isle(mesaj, KAYNAK)
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual(1, len(mav.komutlar),
                         "eski cerceve eyleyiciyi YENIDEN calistirdi")
        self.assertGreater(alici.sayac["tekrar"], tekrar_oncesi,
                           "eski cerceve TEKRAR olarak taninmadi")

    def test_saat_ADIMINDAN_sonra_da_eski_cerceve_CALISMAZ(self):
        """Adım kestirimi düzeltir — ama replay anahtarına DOKUNMAZ."""
        mav, alici, link, saat, _kayit, durum, mesaj = self._gecmis_arm()
        durum["iha"] += IKI_SAAT_SAPMASI_S          # NTP saati YERİNE oturttu
        for i in range(BEKLENEN_ADIM_DENEME + 2):
            saat.ilerlet(TEKRAR_ARALIGI_S)
            alici.isle(_cmd(seq=900 + i, t=YKS_SAATI + (saat.t - 5_000.0)),
                       KAYNAK)                      # adımı algılat
        self.assertAlmostEqual(0.0, alici._son_ofset, places=6,
                               msg="on kosul: adim algilanmadi")
        oncesi = len(mav.komutlar)
        for _ in range(2 * ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK):
            alici.isle(mesaj, KAYNAK)               # yakalanan ESKİ çerçeve
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual(oncesi, len(mav.komutlar),
                         "adimdan sonra ESKI cerceve eyleyiciyi calistirdi")

    def test_GORULMEMIS_seq_hala_gerekli_ayni_damga_yeni_seq_ile_gecmez(self):
        """Saldırgan yakalanan damgayı YENİ bir seq'e takıyor: tazelik tutar."""
        mav, alici, link, saat, _kayit, _d, _mesaj = self._gecmis_arm()
        saat.ilerlet(ika.KOMUT_YAS_TAVANI_S[ika.CMD_ARM] + 1.0)
        sahte = _cmd(seq=82, t=YKS_SAATI)           # ESKİ damga, YENİ seq
        for _ in range(3 * ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK):
            self.assertFalse(alici.isle(sahte, KAYNAK))
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertEqual(1, len(mav.komutlar),
                         "bayat damga yeni seq ile eyleyiciyi calistirdi")

    def test_replay_anahtari_1970_senaryosunda_da_tutar(self):
        mav, alici, link, saat, _kayit, _d, mesaj = self._gecmis_arm(
            iha_saati=JETSON_1970_IHA_SAATI)
        for _ in range(5):
            saat.ilerlet(TEKRAR_ARALIGI_S)
            alici.isle(mesaj, KAYNAK)
        self.assertEqual(1, len(mav.komutlar))


# ── K-C · TEK AYKIRI ÖRNEK UÇUŞ KOMUT HATTINI KİLİTLEYEMEZ ──────────────────
# 2026-09-04, SAHA mercekli çürütme ÖLÇÜMÜ. K-A/K-B onarımı `_kestir` adayını
# KÜRESEL `min` ile seçiyordu; `min` kırılma noktası SIFIR olan bir özettir.
# Meşru sapma -600 s iken TEK bir "10 gün İLERİ damgalı" çerçeve aday olur,
# bant dışıdır, 6 destekçi bulamaz ve kestirim `None` döner — meşru -600 s
# KÜMESİ hiç denenmeden elenir. ÖLÇÜLDÜ: 20 basamaklık RTL merdiveninden
# MAVLink'e giden 0, zaman_red 243, uçuş komut hattı 60,75 s ÖLÜ (aykırı örnek
# pencerede durduğu sürece; kaynak ısrar ederse KALICI). ESKİ kodda (HEAD
# bb832a2) aynı senaryoda 18/20 basamak geçiyordu — yani onarım, K-B'nin
# kapattığı 60 s ölü pencereyi BAŞKA BİR KAPIDAN geri getiriyordu.
# Aday artık artan sırada taranır: kendi kanıt eşiğini karşılayan İLK (en
# küçük) aday kazanır. İki kademeli eşik AYNEN durur.
BANT_ICI_SAPMA_S = 600.0          # eski mutlak tavanın (30 dk) İÇİNDE
AYKIRI_ILERI_DAMGA_S = 10.0 * 24.0 * 3600.0   # 10 gün İLERİ damga


class KCTekAykiriOrnekKilitlemezTests(unittest.TestCase):
    """Bir aykırı örnek, geri kalan tutarlı kümeyi SUSTURAMAZ."""

    def _kurulum(self, mav):
        alici, link, saat, kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - BANT_ICI_SAPMA_S)
        return alici, link, saat, kayit

    def _aykiri(self, seq=71):
        return _cmd(ika.CMD_ARM, seq=seq, t=YKS_SAATI + AYKIRI_ILERI_DAMGA_S)

    def test_tek_aykiri_ILERI_damga_mesru_komutu_OLDURMEZ(self):
        """Ölçüm: yamadan önce 0/20 basamak geçiyordu (60,75 s ölü)."""
        for ad in (ika.CMD_ARM, ika.CMD_RTL, ika.CMD_LAND, ika.CMD_PARACHUTE):
            with self.subTest(komut=ad):
                mav = _Mav()
                alici, link, saat, _kayit = self._kurulum(mav)
                self.assertFalse(alici.isle(self._aykiri(), KAYNAK))
                saat.ilerlet(TEKRAR_ARALIGI_S)
                deneme = _merdiveni_yuru(alici, saat, _cmd(ad, seq=72))
                self.assertIsNotNone(
                    deneme, f"{ad} tek aykiri ornek yuzunden HIC gecmedi")
                self.assertEqual(1, len(mav.komutlar))

    def test_aykiri_ornek_kestirime_ADAY_olamaz(self):
        """Kestirim MEŞRU kümenin değeridir; aykırı örneğinki DEĞİL.

        `KOMUT_SAAT_DESTEK_BANDI_S` genişletilirse aykırı örnek destek
        toplayıp adayı kaparaks bu assert düşer — sabiti davranışla kilitler.
        """
        mav = _Mav()
        alici, _link, saat, _kayit = self._kurulum(mav)
        alici.isle(self._aykiri(seq=73), KAYNAK)
        saat.ilerlet(TEKRAR_ARALIGI_S)
        _merdiveni_yuru(alici, saat, _cmd(seq=74))
        # Merdiven basamakları İHA saatini ilerletir; kestirim meşru kümenin
        # EN KÜÇÜK ham farkıdır — sapmaya bir merdiven boyu kadar yakındır.
        self.assertAlmostEqual(-BANT_ICI_SAPMA_S, alici._son_ofset,
                               delta=ika.KOMUT_SAAT_DESTEK_BANDI_S)
        # Aykırı örneğin kendi değeri (-BANT_ICI - 10 gün) bandın ÇOK
        # dışındadır: kestirim ona kaymışsa bu assert düşer.
        self.assertLessEqual(abs(alici._son_ofset),
                             ika.KOMUT_SAAT_SAPMA_TAVANI_S)

    def test_aykiri_ornek_TEK_BASINA_kestirim_KURAMAZ(self):
        """Kapı gevşemedi: bant dışı aday hâlâ geniş kanıt eşiği ister."""
        mav = _Mav()
        alici, _link, saat, _kayit = self._kurulum(mav)
        for i in range(ika.KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK - 1):
            self.assertFalse(alici.isle(self._aykiri(seq=75 + i), KAYNAK))
            saat.ilerlet(TEKRAR_ARALIGI_S)
        self.assertIsNone(alici._son_ofset)
        self.assertEqual(0, len(mav.komutlar))

    def test_BANT_DISI_sapmada_aykiri_ornek_destek_TOPLAYAMAZ(self):
        """Aykırı örnek `KOMUT_SAAT_DESTEK_BANDI_S` dışındadır; destekçi sayamaz.

        Sapma bant DIŞI (2 saat) olduğu için kestirim 6 destekçi ister ve
        örnekler gerçekten birikir — bandın davranışa dokunduğu tek yer burası.
        Bant genişletilirse aykırı örnek 6 destekçiyi toplayıp adayı kapar,
        meşru küme susar ve merdiven HİÇ geçmez; bu assert onu yakalar.
        """
        mav = _Mav()
        alici, _link, saat, _kayit, _d = _sapmali_alici(
            mav, YKS_SAATI - IKI_SAAT_SAPMASI_S)
        self.assertFalse(alici.isle(self._aykiri(seq=91), KAYNAK))
        saat.ilerlet(TEKRAR_ARALIGI_S)
        deneme = _merdiveni_yuru(alici, saat, _cmd(ika.CMD_ARM, seq=92))
        self.assertEqual(BEKLENEN_DENEME, deneme,
                         "aykiri ornek bant disi kestirimi de bozmamali")
        self.assertEqual(1, len(mav.komutlar))
        self.assertAlmostEqual(-IKI_SAAT_SAPMASI_S, alici._son_ofset,
                               delta=ika.KOMUT_SAAT_DESTEK_BANDI_S)

    def test_aykiri_ornekten_sonra_OLU_PENCERE_YOK(self):
        """Ölçüm: yamadan önce ilk meşru komut 60,75 s sonra geçiyordu."""
        mav = _Mav()
        alici, _link, saat, _kayit = self._kurulum(mav)
        alici.isle(self._aykiri(seq=81), KAYNAK)
        saat.ilerlet(TEKRAR_ARALIGI_S)
        t0 = saat.t
        deneme = _merdiveni_yuru(alici, saat, _cmd(ika.CMD_RTL, seq=82))
        self.assertIsNotNone(deneme)
        olu_s = (deneme - 1) * TEKRAR_ARALIGI_S
        self.assertLess(olu_s, ika.KOMUT_SAAT_OFSETI_PENCERESI_S / 10.0,
                        f"aykiri ornekten sonra olu pencere {olu_s} s")
        self.assertGreaterEqual(saat.t, t0)

if __name__ == "__main__":
    unittest.main()
