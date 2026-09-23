"""NEDEN: Yalniz yerde hazirlanan FDA plani Pixhawk ACK ve geri okumayla kabul edilir."""

import math
import time
import uuid

from fda_gorev import (
    COPTER_AUTO_MODU, GOREV_YUKLEME_TAVANI_S, HAZIRLIK_TAZELIK_S,
    KALKIS_KONUM_TOLERANSI_M, KALKIS_YON_TOLERANSI_DERECE,
    PLAN_SURUMU, atomik_json_yaz, ayar_dogrula, ayar_ozeti,
    drone_test_kare_noktalari, hazirlik_oku, hedef_konumu, mesafe_m,
    sonlu_sayi,
)


class GorevYuklemeHatasi(RuntimeError):
    pass


GELEN_KUTU_BOSALTMA_TAVANI = 8192
GELEN_KUTU_BOSALTMA_SURE_S = 0.50
# ArduPilot MissionItemInt geri okuması koordinatı yaklaşık 0,2 m oynatabilir;
# daha büyük farklar planın gerçekten değiştirildiğini gösterir.
KOORDINAT_GERI_OKUMA_TOLERANSI_1E7 = 100


class FdaPlanYukleyici:
    def __init__(self, mav, yol, target_system=1, target_component=1,
                 saat=time.monotonic, mavlink=None, require_algi_hazir=True):
        if mavlink is None:
            from pymavlink import mavutil
            mavlink = mavutil.mavlink
        self.mav = mav
        self.yol = yol
        self.target_system = target_system
        self.target_component = target_component
        self.saat = saat
        self.kod = mavlink
        self.require_algi_hazir = bool(require_algi_hazir)
        self.son = None
        self.hb = None
        self.hb_zamani = None
        self.yazmaya_baslandi = False
        self.kutu_bosaltma_sayisi = 0
        self.kutu_bosaltma_tavani_asildi = False

    def _gelen_kutusunu_bosalt(self):
        """Eski MAVLink paketlerini süre ve tavan sınırıyla temizle.

        Telemetri akışı sürekli olduğunda ``recv_match(blocking=False)`` hiçbir
        zaman ``None`` dönmeyebilir. Fiziksel olarak tamamen boş kuyruğu şart
        koşmak, sağlıklı bağlantıyı plan reddine dönüştürür; görev aktarımı
        sonrasında kaynak/hedef ve ACK doğrulamalarıyla devam eder.
        """
        baslangic = time.monotonic()
        sayi = 0
        while (sayi < GELEN_KUTU_BOSALTMA_TAVANI and
               time.monotonic() - baslangic < GELEN_KUTU_BOSALTMA_SURE_S):
            if self.mav.recv_match(blocking=False) is None:
                break
            sayi += 1
        self.kutu_bosaltma_sayisi = sayi
        self.kutu_bosaltma_tavani_asildi = sayi >= GELEN_KUTU_BOSALTMA_TAVANI
        return sayi
    def _kaynak(self, mesaj):
        return (mesaj.get_srcSystem() == self.target_system
                and mesaj.get_srcComponent() == self.target_component)

    def _sure(self):
        if self.saat() >= self.son:
            raise GorevYuklemeHatasi("Gorev hazirlama zaman asimi; yuklendi sayilmaz")

    def _yerde(self):
        self._sure()
        if (self.hb is None or self.hb_zamani is None
                or not 0 <= self.saat() - self.hb_zamani <= HAZIRLIK_TAZELIK_S):
            raise GorevYuklemeHatasi("Taze Pixhawk HEARTBEAT yok")
        if self.hb.base_mode & self.kod.MAV_MODE_FLAG_SAFETY_ARMED:
            raise GorevYuklemeHatasi("ARM arac uzerinde gorev degistirilemez")
        if self.hb.custom_mode == COPTER_AUTO_MODU:
            raise GorevYuklemeHatasi("Hazirlik icin AUTO disinda bir mod gerekli")
        if (self.hb.autopilot != self.kod.MAV_AUTOPILOT_ARDUPILOTMEGA
                or self.hb.type != self.kod.MAV_TYPE_QUADROTOR):
            raise GorevYuklemeHatasi("Bu gorev yalniz ArduCopter quad test araci icindir")

    def _oku(self, turler, bekleme=2.0, yerde=True):
        bitis = min(self.son, self.saat() + bekleme)
        while self.saat() < bitis:
            self._sure()
            mesaj = self.mav.recv_match(blocking=True, timeout=min(0.1, bitis - self.saat()))
            if mesaj is None or mesaj.get_type() == "BAD_DATA" or not self._kaynak(mesaj):
                continue
            if mesaj.get_type() == "HEARTBEAT":
                self.hb = mesaj
                self.hb_zamani = self.saat()
            if yerde:
                self._yerde()
            if mesaj.get_type() in turler:
                return mesaj
        return None

    def _istek_mesaji(self, mesaj_id):
        self.mav.mav.command_long_send(
            self.target_system, self.target_component,
            self.kod.MAV_CMD_REQUEST_MESSAGE, 0, mesaj_id, 0, 0, 0, 0, 0, 0)

    def _parametre(self, ad):
        for deneme in range(3):
            self._yerde()
            self.mav.mav.param_request_read_send(
                self.target_system, self.target_component, ad.encode("ascii"), -1)
            bitis = min(self.son, self.saat() + 1.5)
            while self.saat() < bitis:
                mesaj = self._oku({"PARAM_VALUE"}, bitis - self.saat())
                if mesaj is None:
                    break
                kimlik = mesaj.param_id
                if isinstance(kimlik, bytes):
                    kimlik = kimlik.decode("ascii")
                if kimlik.rstrip("\0") == ad:
                    return sonlu_sayi(mesaj.param_value, ad)
        raise GorevYuklemeHatasi(f"{ad} geri okunamadi; parametre degistirilmedi")

    def _telemetri(self):
        self.hb = self._oku({"HEARTBEAT"}, 3.0, yerde=False)
        self._yerde()
        gerekli = {
            "GPS_RAW_INT": self.kod.MAVLINK_MSG_ID_GPS_RAW_INT,
            "GLOBAL_POSITION_INT": self.kod.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
            "HOME_POSITION": self.kod.MAVLINK_MSG_ID_HOME_POSITION,
            "EXTENDED_SYS_STATE": self.kod.MAVLINK_MSG_ID_EXTENDED_SYS_STATE,
        }
        for mesaj_id in gerekli.values():
            self._istek_mesaji(mesaj_id)
        gelen = {}
        bitis = min(self.son, self.saat() + 4.0)
        while set(gelen) != set(gerekli) and self.saat() < bitis:
            mesaj = self._oku(set(gerekli), bitis - self.saat())
            if mesaj is not None:
                gelen[mesaj.get_type()] = mesaj
        if set(gelen) != set(gerekli):
            raise GorevYuklemeHatasi("GPS, konum, HOME veya yerde olma kaniti eksik")
        if gelen["GPS_RAW_INT"].fix_type < 3:
            raise GorevYuklemeHatasi("3D GPS fix gerekli")
        if gelen["EXTENDED_SYS_STATE"].landed_state != self.kod.MAV_LANDED_STATE_ON_GROUND:
            raise GorevYuklemeHatasi("Arac yerde olarak dogrulanmadi")
        return gelen

    def _on_kontrol(self, ayar, veri):
        konum = veri["GLOBAL_POSITION_INT"]
        home = veri["HOME_POSITION"]
        canli_konum = (konum.lat / 1e7, konum.lon / 1e7)
        home_konum = (home.latitude / 1e7, home.longitude / 1e7)
        kalkis = (ayar["lat"], ayar["lon"])
        if (mesafe_m(kalkis, canli_konum) > KALKIS_KONUM_TOLERANSI_M
                or mesafe_m(kalkis, home_konum) > KALKIS_KONUM_TOLERANSI_M):
            raise GorevYuklemeHatasi("Kalkis, HOME ve canli konum uyusmuyor; yeniden hazirlayin")
        if not 0 <= konum.hdg < 36000:
            raise GorevYuklemeHatasi("Burun yonu bilinmiyor")
        yon_hatasi = abs((konum.hdg / 100.0 - ayar["yon"] + 180.0) % 360.0 - 180.0)
        if yon_hatasi > KALKIS_YON_TOLERANSI_DERECE:
            raise GorevYuklemeHatasi("Hazirliktan sonra burun yonu degismis")
        if math.hypot(konum.vx, konum.vy) / 100.0 > 0.5:
            raise GorevYuklemeHatasi("Gorev hazirlarken arac hareketsiz olmali")
        parametreler = {ad: self._parametre(ad) for ad in (
            "AUTO_OPTIONS", "FENCE_ENABLE", "FENCE_TYPE", "FENCE_ALT_MAX",
            "FENCE_RADIUS", "FENCE_MARGIN", "ARMING_CHECK")}
        for ad in ("AUTO_OPTIONS", "FENCE_ENABLE", "FENCE_TYPE", "ARMING_CHECK"):
            if parametreler[ad] != int(parametreler[ad]):
                raise GorevYuklemeHatasi(f"{ad} tam sayi olmali")
        if not int(parametreler["AUTO_OPTIONS"]) & 2:
            raise GorevYuklemeHatasi(
                "AUTO_OPTIONS kalkisin gaz hareketi olmadan baslamasina izin vermiyor; "
                "parametre otomatik degistirilmedi")
        if parametreler["FENCE_ENABLE"] != 1 or int(parametreler["FENCE_TYPE"]) != 3:
            raise GorevYuklemeHatasi("Bu hazirlayici etkin irtifa+dairesel cit gerektirir (tip 3)")
        if parametreler["ARMING_CHECK"] != 1:
            raise GorevYuklemeHatasi("Tum arming denetimleri acik olmali; ayar degistirilmedi")
        if abs(konum.relative_alt / 1000.0) > 1.0:
            raise GorevYuklemeHatasi("Yerdeki HOME irtifa referansi uyusmuyor")
        hedef_irtifa = ayar["yukseklik_m"]
        pay = parametreler["FENCE_MARGIN"]
        if pay < 0 or not 0 < hedef_irtifa < parametreler["FENCE_ALT_MAX"] - pay:
            raise GorevYuklemeHatasi("Istenen yukseklik mevcut irtifa citini/payini asiyor")
        if mesafe_m(home_konum, hedef_konumu(ayar)) >= parametreler["FENCE_RADIUS"] - pay:
            raise GorevYuklemeHatasi("Istenen hedef mevcut dairesel citin/payinin disinda")
        return hedef_irtifa, parametreler

    def _satirlar(self, ayar, irtifa, home):
        hedef_enlem, hedef_boylam = hedef_konumu(ayar)
        satirlar = [
            (self.kod.MAV_FRAME_GLOBAL, self.kod.MAV_CMD_NAV_WAYPOINT,
             home.latitude / 1e7, home.longitude / 1e7, home.altitude / 1000.0),
            (self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT, self.kod.MAV_CMD_NAV_TAKEOFF,
             0.0, 0.0, irtifa),
            (self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT, self.kod.MAV_CMD_NAV_WAYPOINT,
             hedef_enlem, hedef_boylam, irtifa),
        ]
        if "arama_kare_m" in ayar:
            for enlem, boylam in drone_test_kare_noktalari(ayar):
                satirlar.append((
                    self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                    self.kod.MAV_CMD_NAV_WAYPOINT,
                    enlem, boylam, irtifa))
        satirlar.append((
            self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            self.kod.MAV_CMD_NAV_LOITER_UNLIM,
            hedef_enlem, hedef_boylam, irtifa))
        return satirlar

    def _bizim_islem(self, mesaj):
        return (getattr(mesaj, "mission_type", self.kod.MAV_MISSION_TYPE_MISSION)
                == self.kod.MAV_MISSION_TYPE_MISSION
                and getattr(mesaj, "target_system", None) == self.mav.mav.srcSystem
                and getattr(mesaj, "target_component", None) in (0, self.mav.mav.srcComponent))

    def _satir_gonder(self, sira, satir, tam_sayi):
        self._yerde()
        cerceve, komut, enlem, boylam, irtifa = satir
        if tam_sayi:
            cerceve = {
                self.kod.MAV_FRAME_GLOBAL: self.kod.MAV_FRAME_GLOBAL_INT,
                self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT: self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT,
            }[cerceve]
        gonder = self.mav.mav.mission_item_int_send if tam_sayi else self.mav.mav.mission_item_send
        gonder(self.target_system, self.target_component, sira, cerceve,
               komut, 0, 1, 0, 0, 0, 0,
               int(round(enlem * 1e7)) if tam_sayi else enlem,
               int(round(boylam * 1e7)) if tam_sayi else boylam,
               irtifa)

    def _yukle(self, satirlar):
        self._yerde()
        self.yazmaya_baslandi = True
        self.mav.mav.mission_count_send(
            self.target_system, self.target_component, len(satirlar))
        gonderilen = set()
        beklenen_sira = 0
        son_tam_sayi = True
        tekrar = 0
        while True:
            mesaj = self._oku({"MISSION_REQUEST_INT", "MISSION_REQUEST", "MISSION_ACK"})
            if mesaj is None:
                tekrar += 1
                if tekrar > 3:
                    raise GorevYuklemeHatasi("Gorev aktarimi cevap vermedi")
                self._yerde()
                if not gonderilen:
                    self.mav.mav.mission_count_send(
                        self.target_system, self.target_component, len(satirlar))
                else:
                    self._satir_gonder(beklenen_sira, satirlar[beklenen_sira], son_tam_sayi)
                continue
            if not self._bizim_islem(mesaj):
                continue
            tekrar = 0
            if mesaj.get_type() == "MISSION_ACK":
                if mesaj.type != self.kod.MAV_MISSION_ACCEPTED or len(gonderilen) != len(satirlar):
                    raise GorevYuklemeHatasi("Eksik veya reddedilmis MISSION_ACK")
                return
            sira = mesaj.seq
            if isinstance(sira, bool) or not isinstance(sira, int) or not 0 <= sira < len(satirlar):
                raise GorevYuklemeHatasi("Gecersiz gorev sira istegi")
            if sira > len(gonderilen):
                raise GorevYuklemeHatasi("Sirasiz gorev istegi")
            beklenen_sira = sira
            son_tam_sayi = mesaj.get_type() == "MISSION_REQUEST_INT"
            self._satir_gonder(sira, satirlar[sira], son_tam_sayi)
            gonderilen.add(sira)

    def _geri_oku(self, satirlar):
        self._yerde()
        self.mav.mav.mission_request_list_send(
            self.target_system, self.target_component)
        sayim = self._oku({"MISSION_COUNT"})
        if sayim is None or not self._bizim_islem(sayim) or sayim.count != len(satirlar):
            raise GorevYuklemeHatasi("Gorev geri okuma sayisi uyusmadi")
        for sira, satir in enumerate(satirlar):
            alinan = None
            for deneme in range(3):
                self._yerde()
                self.mav.mav.mission_request_int_send(
                    self.target_system, self.target_component, sira)
                aday = self._oku({"MISSION_ITEM_INT"})
                if aday is not None and self._bizim_islem(aday) and aday.seq == sira:
                    alinan = aday
                    break
            if alinan is None:
                raise GorevYuklemeHatasi(f"Gorev satiri {sira} geri okunamadi")
            cerceve, komut, enlem, boylam, irtifa = satir
            esdeger_cerceve = {
                self.kod.MAV_FRAME_GLOBAL_INT: self.kod.MAV_FRAME_GLOBAL,
                self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT_INT: self.kod.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            }.get(alinan.frame, alinan.frame)
            uyusmazliklar = []
            beklenen_x = round(enlem * 1e7)
            beklenen_y = round(boylam * 1e7)
            if alinan.command != komut:
                uyusmazliklar.append(f"command beklenen={komut} gelen={alinan.command}")
            if esdeger_cerceve != cerceve:
                uyusmazliklar.append(
                    f"frame beklenen={cerceve} gelen={alinan.frame} normalize={esdeger_cerceve}")
            if abs(alinan.x - beklenen_x) > KOORDINAT_GERI_OKUMA_TOLERANSI_1E7:
                uyusmazliklar.append(f"x beklenen={beklenen_x} gelen={alinan.x}")
            if abs(alinan.y - beklenen_y) > KOORDINAT_GERI_OKUMA_TOLERANSI_1E7:
                uyusmazliklar.append(f"y beklenen={beklenen_y} gelen={alinan.y}")
            if not math.isclose(alinan.z, irtifa, abs_tol=0.05):
                uyusmazliklar.append(f"z beklenen={irtifa} gelen={alinan.z}")
            if alinan.autocontinue != 1:
                uyusmazliklar.append(f"autocontinue beklenen=1 gelen={alinan.autocontinue}")
            for alan in range(1, 5):
                parametre = getattr(alinan, f"param{alan}")
                if not math.isclose(parametre, 0.0, abs_tol=1e-6):
                    uyusmazliklar.append(f"param{alan} beklenen=0 gelen={parametre}")
            if uyusmazliklar:
                raise GorevYuklemeHatasi(
                    f"Gorev satiri {sira} geri okuma ile uyusmuyor: "
                    + "; ".join(uyusmazliklar))
        self._yerde()
        self.mav.mav.mission_ack_send(
            self.target_system, self.target_component, self.kod.MAV_MISSION_ACCEPTED)

    def hazirla(self, ayar):
        self.son = self.saat() + GOREV_YUKLEME_TAVANI_S
        self.hb = None
        self.hb_zamani = None
        self.yazmaya_baslandi = False
        ayar = ayar_dogrula(ayar)
        hazirlik = (hazirlik_oku(self.yol, self.saat())
                    if self.require_algi_hazir else
                    {"oturum": uuid.uuid4().hex})
        self._gelen_kutusunu_bosalt()
        veri = self._telemetri()
        irtifa, parametreler = self._on_kontrol(ayar, veri)
        satirlar = self._satirlar(ayar, irtifa, veri["HOME_POSITION"])
        atomik_json_yaz(self.yol, {"v": PLAN_SURUMU, "dogrulandi": False})
        self._yukle(satirlar)
        self._geri_oku(satirlar)
        self._yerde()
        self.mav.mav.mission_set_current_send(self.target_system, self.target_component, 1)
        gecerli = self._oku({"MISSION_CURRENT"})
        if gecerli is None or gecerli.seq != 1:
            raise GorevYuklemeHatasi("Gorev TAKEOFF satirina alinamadi")
        if self.require_algi_hazir:
            son_hazirlik = hazirlik_oku(self.yol, self.saat())
            if son_hazirlik["oturum"] != hazirlik["oturum"]:
                raise GorevYuklemeHatasi("Gorev sirasinda algi sureci yeniden basladi")
        self._yerde()
        atomik_json_yaz(self.yol, {
            "v": PLAN_SURUMU, "dogrulandi": True, "ayar": ayar,
            "ozet": ayar_ozeti(ayar), "hedef_irtifa_m": irtifa,
            "algi_oturumu": hazirlik["oturum"], "parametreler": parametreler,
            "hazirlandi_monotonik": self.saat(),
        })
        return True
