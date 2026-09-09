#!/usr/bin/env python3
"""NEDEN: Sartname §2.2.4 (parasut "yer istasyonundan manuel tetikleme ile de
gerceklestirilebilir") ve §6.4; CONTRACTS §6.6 PARACHUTE maddesi; D-393.
YKS parasut komutunu ACK gelene dek tekrarliyor ama IHA tarafinda CMD dinleyen
uc YOKTU ("AVIYONIK-BLOKLU"). Bu surec o boslugun YAZILIM yarisini kapatir:
Jetson'da kosar, YKS'nin CMD mesajlarini (UDP ya da SiK seri) alir, Pixhawk'a
MAVLink COMMAND_LONG ile aktarir ve YALNIZ aktarim basariliysa ACK doner.

ACK "aldim VE Pixhawk KABUL ETTI" demektir (D-393 durustluk sozlesmesi;
D-403 curutucu ONEMLI-3 ile sikilastirildi):
  * COMMAND_LONG gonderilir, ardindan Pixhawk'in MAVLink COMMAND_ACK cevabi
    MAVLINK_KOMUT_ACK_TAVANI_S icinde beklenir; yalniz MAV_RESULT_ACCEPTED
    gelirse YKS'ye ACK doner. Ret/zaman asimi -> ACK YOK, KIRMIZI log.
  * command_long_send istisna firlatirsa ACK YOK, KIRMIZI log;
  * MAVLink baglantisi yoksa aktarim yok, ACK YOK, log;
  * bilinmeyen komut aktarilmaz ve ACK'lanmaz.
Boylece YKS tekrarlamaya devam eder ve hakem ekraninda "ACK YOK" gorunur —
sessiz basari yalani yoktur.

Idempotentlik BILEREK YOK (D-403 curutucu KRITIK-2): ilk tasarim (cmd, seq)
hafizasiyla tekrari baskiliyordu; YKS her acilista seq'i 1'den baslattigi
icin yeniden acilan YKS'nin PARACHUTE'u "mukerrer" sayilip MAVLink'e HIC
gitmeden ACK'laniyordu — yesil "IHA ALDI", parasut kapali. DO_PARACHUTE ve
ARM/DISARM/RTL/LAND Pixhawk tarafinda idempotenttir; her gecerli komut YENIDEN
aktarilir ve yeniden COMMAND_ACK beklenir. (IKA_GO'daki hafiza IKA latch
semantigi icindir; burada karsiligi yoktur.)

⚠ JETSON'DA SERI PIXHAWK TEK SAHIPLIDIR. Bu surec, `rpi_inference` (bagil
irtifa okuyucu) ve `iha_inis_yayinci` (inis kaniti) ile AYNI ANDA seri portu
ACAMAZ — ayni /dev/ttyACM0'i iki surec acarsa cerceveler bolunur ve her iki
taraf da sessizce kor olur. MAVLink cogullayici (mavlink-router ya da
`MAVProxy --out udp:127.0.0.1:145xx`) SART; her surec kendi UDP ucundan
konusur. Kurulum: runbook (`Jetson runbook`, P4).

⚠ `udp:` (sunucu) ucunda pymavlink, Pixhawk/cogullayicidan HIC paket almadan
`write()` cagrilirsa SESSIZCE hicbir sey gondermez ve socket hatasini da yutar
(pymavlink 2.4.49 `mavudp.write`). Bu yuzden her turda MAVLink gelen kutusu
bosaltilir (akran adresi ogrenilir) ve akran gorulmeden gelen komut
"aktarilmadi, ACK YOK" sayilir (`mav_hedefi_biliniyor_mu`).

Kullanim (dev/UDP, cogullayici ucu):
  python3 iha_komut_alici.py --mavlink udp:127.0.0.1:14560 --bind 0.0.0.0:5007
Saha (SiK telsiz + cogullayici):
  python3 iha_komut_alici.py --mavlink udp:127.0.0.1:14560 --serial /dev/ttyUSB0
"""
import argparse
import importlib
import math
import socket
import sys
import threading
import time
from numbers import Real
from pathlib import Path

_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

_KODLAR = _BU_DIZIN.parent / "codes"
if str(_KODLAR) not in sys.path:
    sys.path.insert(0, str(_KODLAR))

from inis_kaniti import (  # noqa: E402
    mavlink_baglantisi_ac, seri_pixhawk_bayragini_ekle,
    seri_pixhawk_kilidini_uygula)
from karar_sozlesmesi import (ARM_TEKRAR_ARALIGI_S,  # noqa: E402
                              ARM_TEKRAR_UST_SINIRI,
                              MAVLINK_KOMUT_ACK_TAVANI_S,
                              PARASUT_TEKRAR_ARALIGI_S,
                              PARASUT_TEKRAR_UST_SINIRI)
from link import SerialLink, UDPLink  # noqa: E402
from protocol import (ACK_SONUC_KABUL, FrameReader, ack, encode,  # noqa: E402
                      oturum_dogrula, MESAJ_CMD)

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


# ── Protokol adlari (CONTRACTS §6 mesaj tablosu + §6.6) ──────────────────────
MESAJ_TIPI_CMD = MESAJ_CMD        # T208: ad protocol.py'de tek yerde
CMD_PARACHUTE = "PARACHUTE"       # CONTRACTS §6.6 · D-393 · sartname §2.2.4
CMD_ARM = "ARM"                   # CONTRACTS §6 tablo: "IKA_GO, ARM, ..."
CMD_DISARM = "DISARM"
CMD_RTL = "RTL"                   # güvenli uçuş sonlandırma: eve dönüş
CMD_LAND = "LAND"                 # güvenli uçuş sonlandırma: bulunduğu yere iniş
KOMUT_ADLARI = (CMD_PARACHUTE, CMD_ARM, CMD_DISARM, CMD_RTL, CMD_LAND)
VARSAYILAN_DUGUM = "iha"          # protocol.iha_landed ile ayni dugum adi
VARSAYILAN_BIND = "0.0.0.0:5007"  # YKS bunu `yks_gui --iha HOST:5007` ile PINLER
                                  # (D-403: heartbeat'ten ogrenilen adres
                                  # rpi_inference'in efemer portudur, bu degil)
VARSAYILAN_BAUD = 57600           # ika_receiver ile ayni SiK varsayilani

# ── MAVLink alan anlamlari (common.xml; pymavlink'te adli sabiti yok) ─────────
# MAV_CMD_COMPONENT_ARM_DISARM param1: 0 = disarm, 1 = arm.
ARM_DISARM_PARAM1_ARM = 1
ARM_DISARM_PARAM1_DISARM = 0
# COMMAND_LONG.confirmation: 0 = komutun ilk gonderimi; 1..255 teyit tekrari.
MAVLINK_ONAY_ILK_GONDERIM = 0
# Komutun kullanmadigi param2..param7 alanlari ("0 / kullanilmiyor").
MAVLINK_PARAM_KULLANILMIYOR = 0
# ArduPilot varsayilan arac kimligi ve MAV_COMP_ID_AUTOPILOT1.
VARSAYILAN_HEDEF_SYSID = 1
VARSAYILAN_HEDEF_COMPONENT = 1
# MAV_COMP_ID_ALL (0): COMMAND_ACK'te kaynak bilesenin BELIRTILMEDIGI geriye
# uyumlu bicim (eski pymavlink, sahte uc). Adli sabiti common.xml'de vardir
# ama eski pymavlink surumlerinde her zaman disari verilmez.
MAVLINK_BELIRTILMEMIS_COMPONENT = 0

# Bir poll turunda MAVLink gelen kutusundan bosaltilacak en cok mesaj sayisi:
# Pixhawk ~10-50 mesaj/s, tur <= link zaman asimi (0,3 s) -> 64 yeterli.
MAVLINK_BOSALTMA_TAVANI = 64
LOG_ONEKI = "[IHA_KOMUT]"

# Bir CMD'nin meşru ömrü onu üreten YKS tekrar penceresidir; ikinci, bağımsız
# bir sayı yazılmaz. DISARM/RTL/LAND ve ARM aynı tekrar sözleşmesini paylaşır.
KOMUT_YAS_TAVANI_S = {
    CMD_ARM: ARM_TEKRAR_ARALIGI_S * ARM_TEKRAR_UST_SINIRI,
    CMD_DISARM: ARM_TEKRAR_ARALIGI_S * ARM_TEKRAR_UST_SINIRI,
    CMD_RTL: ARM_TEKRAR_ARALIGI_S * ARM_TEKRAR_UST_SINIRI,
    CMD_LAND: ARM_TEKRAR_ARALIGI_S * ARM_TEKRAR_UST_SINIRI,
    CMD_PARACHUTE: PARASUT_TEKRAR_ARALIGI_S * PARASUT_TEKRAR_UST_SINIRI,
}
# protocol.command zaman damgasını milisaniyeye yuvarlar. En yakın milisaniyeye
# yukarı yuvarlama çok küçük negatif yaş üretebilir; OFSETE GÖRE düzeltilmiş
# yaş bundan daha ileriyse damga bozuktur ve reddedilir.
KOMUT_ZAMAN_YUVARLAMA_TOLERANSI_S = 1.0 / 1000.0

# ── K-1 · ÇAPRAZ-MAKİNE SAAT SAPMASI ────────────────────────────────────────
# `t` damgasını YKS DİZÜSTÜ basar (`protocol.command`: `round(time.time(), 3)`),
# `simdi`yi İHA (Jetson) okur — İKİ AYRI MAKİNE. Dolayısıyla ham fark
#     ham = simdi - damga = ofset_gercek + gecikme      (gecikme >= 0)
# iki SAATİN farkı artı taşıma gecikmesidir; komutun YAŞI DEĞİLDİR. Jetson
# NANO'da RTC pili YOKTUR: açılışta saat bayat bir değere düşer ve NTP kurulana
# kadar sapma saniyeler–dakikalar mertebesindedir. Ham farkı doğrudan yaş sayan
# kapı sahada ARM/DISARM/RTL/LAND/PARACHUTE'un TAMAMINI reddeder.
#
# KAPI KALDIRILMAZ — DOĞRU BÜYÜKLÜĞÜ ÖLÇER HALE GETİRİLİR: aynı (pinlenmiş)
# kaynaktan gelen ham farkların kayan penceredeki EN KÜÇÜĞÜ saat ofsetinin
# kestirimidir (gecikme negatif olamayacağı için en küçük ham fark, gecikmesi
# en düşük çerçevedir — NTP'nin "minimum filtresi" ile aynı akıl). Yaş bu
# ofsete göre hesaplanır:
#     yas = ham - ofset = gecikme - min(gecikme)
# yani sapma sadeleşir ve GERÇEKTEN yaş ölçülür. Eşik gevşemez: bayat/ileri
# damga ofsete göre de bayat/ileridir.
KOMUT_SAAT_OFSETI_EN_AZ_ORNEK = 2
# Değerlendirilen çerçevenin KENDİ örneği kestirime GİRMEZ; en az bu kadar
# ÖNCEKİ örnek gerekir. Aksi hâlde her çerçeve kendi damgasıyla kendini aklar
# ve kapı anlamsızlaşırdı. Kestirim yokken kapı bugünkü SIKI davranışını aynen
# korur (ofset = 0). Sahada bedeli: sapma varken tekrar merdiveninin ilk iki
# basamağı reddedilir, komut 3. basamakta (2 × 0,25 s sonra) geçer.
KOMUT_SAAT_OFSETI_PENCERESI_S = 60.0
# Örnekler ALIŞ TARAFININ monotonik saatiyle kayan pencerede tutulur; eskiyen
# bir örnek ofseti kilitlemesin (saatler NTP ile yerine oturduğunda kestirim
# de kendini düzeltebilsin). Pencere en uzun tekrar merdiveninden (PARAŞÜT:
# 0,20 s × 40 = 8 s) belirgin biçimde uzundur, birkaç operatör basışını kapsar.
KOMUT_SAAT_SAPMA_TAVANI_S = 30.0 * 60.0
# ⚠ 2026-09-04 · K-A: bu sabit ARTIK "şu kadar sapmış damgayı HİÇ görme"
# filtresi DEĞİLDİR. Öyleyken ÖLÜMCÜLDÜ: ofset bilinmezken `ham` iki saatin
# FARKI'dır; sapma bu tavanı aşınca öğrenmek için gereken örneğin TA KENDİSİ
# eleniyordu -> ofset ASLA öğrenilemiyor -> ARM/DISARM/RTL/LAND/PARACHUTE
# KALICI olarak reddediliyordu. ÖLÇÜLDÜ (2 saat sapma, ARM merdiveni 20/20):
# MAVLink'e giden 0, zaman_red 20, örnek sayısı 0, ofset None.
# "NTP'siz Jetson'ın makul bandı 30 dk" varsayımı da YANLIŞTI: RTC pili olmayan
# bir Jetson sabit bir epoch'a açılır (1970 ya da son kapanma anı) — sapma
# saatler, günler, YILLAR olabilir.
#
# YENİ ANLAMI (KARAR-1): tavan ÖĞRENMEYİ değil KAYMAYI engeller. Bandın
# İÇİNDEKİ bir kestirim UCUZDUR (iki örnek yeter, bugünkü davranış aynen);
# bandın DIŞINDAKİ bir kestirim PAHALIDIR — aşağıdaki geniş kanıt eşiğini
# ister. Yani büyük sapma öğrenilebilir hâle gelir ama TEK bir çılgın çerçeve
# (ya da bir avuç tekrarı) kestirimi kuramaz.
KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK = 6
# Bant DIŞI (|ofset| > KOMUT_SAAT_SAPMA_TAVANI_S) bir kestirim için gereken
# BİRBİRİNİ DESTEKLEYEN örnek sayısı. Bant içi eşiğin (2) üç katıdır: saldırgan
# tek/az sayıda uydurma damgayla ofseti kendi üzerine çekemesin, ama RTC'siz
# Jetson'ın gerçek sapması saha tekrar merdiveninin İLK SANİYESİNDE öğrenilsin
# (ARM merdiveni 20 basamak × 0,25 s = 5 s; 6. basamak = 1,5 s).
# ⚠ Bu bir GEVŞETME değildir: saat kapısı kimlik doğrulaması DEĞİL tazelik
# kapısıdır. Yeniden-oynatma savunması `(oturum, seq, cmd)` anahtarıdır
# (CONTRACTS/`protocol.py`) ve `izinli_kaynak` adres pinidir; ikisi de yerinde
# durur. Saldırganın eski bir komutu oynatabilmesi için hâlâ geçerli bir
# `oturum` + GÖRÜLMEMİŞ bir `seq` üretmesi gerekir.
KOMUT_SAAT_DESTEK_BANDI_S = max(KOMUT_YAS_TAVANI_S.values())
# "Birbirini destekleyen" örnek: aday ofsete GÖRE yaşı meşru olan örnek. Üst
# sınır en uzun komut ömrüdür (PARAŞÜT: 0,20 s × 40 = 8 s) — aynı çerçeve
# merdiven boyunca yeniden gönderilirken `ham` gerçekten bu kadar büyür.
# Bandın dışındaki bir örnek aday ofseti DESTEKLEMEZ; sayılmaz.

# ── K-B · YEREL SAAT ADIMI (basamaklı düzeltme) ─────────────────────────────
# Ofset öğrenildikten SONRA İHA'nın DUVAR saati BASAMAKLI düzeltilirse
# (systemd-timesyncd / chrony step, ya da operatörün `timedatectl set-time`i)
# penceredeki ESKİ örnekler kestirimi eski değerde tutar ve kritik komutlar o
# süre boyunca reddedilir. ÖLÇÜLDÜ (ofset -600 s öğrenildi, saat +600 s ileri
# adımlandı): ARM yeniden geçene kadar 60,00 s ÖLÜ pencere, 241 komut reddi.
# 5 Eylül'de Jetson ilk kez ağa bağlanıp NTP saati düzelttiğinde tam olarak bu
# olur — kabul edilemez.
#
# KARAR-2 · ADIM YEREL OLARAK ÖLÇÜLÜR, TRAFİKTEN ÇIKARILMAZ.
# `time.monotonic` saat adımından ETKİLENMEZ, `time.time` ADIMLA ZIPLAR. İki
# ardışık ölçüm arasında
#     adim = (duvar_farki) - (monotonik_farki)
# sıfırdan belirgin biçimde farklıysa YEREL duvar saati basamaklanmıştır. Bu
# ölçüm YKS'den gelen hiçbir alana bakmaz; saldırgan giremez.
# Adım bulununca pencere atılmaz, DÜZELTİLİR: her örneğin `ham` değeri eski
# duvar saatiyle hesaplanmıştı ve ofset tam olarak `adim` kadar değişmiştir
# (`ofset = C_iha - C_yks`). Örnekler `adim` kadar kaydırılınca gecikme bilgisi
# KORUNUR ve ölü pencere SIFIRLANIR.
#
# ⛔ REDDEDİLEN ALTERNATİF (ölçümle çürütüldü, 2026-09-04): adımı TRAFİKTEN
# çıkarmak — reddedilen çerçevelerin ham farklarını bir halkada toplayıp "ofset
# ani değişti" demek. Uygulandı ve DELİK ÖLÇÜLDÜ: ısrarlı BAYAT bir gönderici
# kendi reddedilen çerçeveleriyle kestirimi kendi üzerine YÜRÜTÜYOR —
# 2 saat sapmalı kurulumda bayat damgalı yeni bir `seq` 10. ısrarda kapıdan
# GEÇTİ ve MAVLink'e ULAŞTI (ofset -7200,000 -> -7191,750). Bu, D-02'nin
# "gecikmiş komut" savunmasını öldürürdü. Adım kanıtı bu yüzden YALNIZ yereldir.
KOMUT_SAAT_ADIMI_ESIGI_S = max(KOMUT_YAS_TAVANI_S.values())
# Bundan KÜÇÜK bir duvar/monotonik ayrışması adım SAYILMAZ. Alt sınır iki
# gerçek etkiden gelir: (a) NTP'nin ADIM yerine YAVAŞLATMA (slew) düzeltmesi en
# çok 500 ppm'dir — iki komut arasında saatler geçse bile birkaç saniyeyi
# aşmaz; (b) en uzun meşru komut ömründen (PARAŞÜT: 8 s) küçük bir kayma zaten
# kapıyı kilitlemez. Gerçek saat adımı (NTP step / operatör) mertebe olarak
# bunun çok üstündedir.


def _mavutil_al():
    """pymavlink'i tembel yukle; eksik saha bagimliligini gorunur kil."""
    try:
        return importlib.import_module("pymavlink.mavutil")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ImportError(
            "pymavlink gerekli; komut Pixhawk'a aktarilamaz") from exc


def mavlink_komut_tablosu():
    """YKS komut adi -> (MAV_CMD, param1). Sabitler pymavlink'ten (madde 16)."""
    m = _mavutil_al().mavlink
    return {
        CMD_PARACHUTE: (m.MAV_CMD_DO_PARACHUTE, m.PARACHUTE_RELEASE),
        CMD_ARM: (m.MAV_CMD_COMPONENT_ARM_DISARM, ARM_DISARM_PARAM1_ARM),
        CMD_DISARM: (m.MAV_CMD_COMPONENT_ARM_DISARM, ARM_DISARM_PARAM1_DISARM),
        CMD_RTL: (m.MAV_CMD_NAV_RETURN_TO_LAUNCH,
                  MAVLINK_PARAM_KULLANILMIYOR),
        CMD_LAND: (m.MAV_CMD_NAV_LAND, MAVLINK_PARAM_KULLANILMIYOR),
    }


def mav_hedefi_biliniyor_mu(mav):
    """`udp:` (sunucu) pymavlink baglantisinda akran adresi ogrenildi mi?

    pymavlink `mavudp.write` sunucu kipinde yalniz `clients` kumesindeki
    adreslere yazar; kume bossa HICBIR SEY gondermez ve socket hatasini yutar.
    Boyle bir baglantida `command_long_send` istisnasiz "basarili" gorunur —
    sessiz basari yalani. Bu kapi onu ACK oncesinde yakalar.
    `udpout:`/seri/tcp baglantilarinda ve sahte nesnelerde (oznitelik `True`
    degil) daima True: kapi yalniz bilinen sessiz-dusurme durumunda kapanir.
    """
    if getattr(mav, "udp_server", None) is not True:
        return True
    istemciler = getattr(mav, "clients", None)
    if istemciler is None:                      # eski pymavlink: last_address
        return getattr(mav, "last_address", None) is not None
    try:
        return len(istemciler) > 0
    except TypeError:
        return True


def _kimlik_dogrula(deger, ad, alt):
    if (isinstance(deger, bool) or not isinstance(deger, int)
            or not alt <= deger <= 255):
        raise ValueError(f"{ad} {alt}..255 tamsayi olmali, gelen: {deger!r}")
    return deger


def _kaynak_adresi_dogrula(adres):
    """Opsiyonel tam UDP kaynak pinini doğrula; ``None`` sınıf geriye uyumudur."""
    if adres is None:
        return None
    if (not isinstance(adres, (tuple, list)) or len(adres) != 2
            or not isinstance(adres[0], str) or not adres[0].strip()
            or isinstance(adres[1], bool) or not isinstance(adres[1], int)
            or not 1 <= adres[1] <= 65535):
        raise ValueError("izinli_kaynak (host, 1..65535 port) olmalidir")
    return adres[0].strip(), adres[1]


def _cli_kaynak_adresi(metin):
    """CLI ``HOST:PORT`` kaynağını alıcının göreceği IPv4 adresine çöz."""
    try:
        host, port_metin = metin.rsplit(":", 1)
        port = int(port_metin)
        host = socket.gethostbyname(host)
        return _kaynak_adresi_dogrula((host, port))
    except (OSError, TypeError, ValueError) as exc:
        raise argparse.ArgumentTypeError(
            f"izinli kaynak HOST:PORT olmalidir: {metin!r} ({exc})") from exc


class IhaKomutAlici:
    """YKS CMD -> Pixhawk COMMAND_LONG; ACK yalniz aktarim basariliysa.

    ``isle(mesaj, adr)`` yalniz ``type == "CMD"`` ve ``hedef == node`` olan
    mesaji isler; digerleri sessizce yok sayilir. Donus degeri **ACK
    gonderildi mi**'dir: yok sayilan, bilinmeyen, aktarilamayan ya da ACK'i
    yazilamayan her durumda ``False``.
    """

    def __init__(self, link, mav, *, node=VARSAYILAN_DUGUM,
                  target_system=VARSAYILAN_HEDEF_SYSID,
                  target_component=VARSAYILAN_HEDEF_COMPONENT,
                  saat=time.monotonic, duvar_saati=time.time,
                  izinli_kaynak=None):
        if not callable(saat):
            raise TypeError("saat cagrilabilir olmali")
        if not callable(duvar_saati):
            raise TypeError("duvar_saati cagrilabilir olmali")
        self.link = link
        self.mav = mav                       # None: aktarim yok, ACK yok
        self.node = str(node)
        self.target_system = _kimlik_dogrula(target_system, "target_system", 1)
        self.target_component = _kimlik_dogrula(
            target_component, "target_component", 0)
        self.saat = saat
        self.duvar_saati = duvar_saati
        self.izinli_kaynak = _kaynak_adresi_dogrula(izinli_kaynak)
        self.reader = FrameReader()          # yalniz SERI (bayt akisi) icin
        self._dur = threading.Event()
        self.sayac = {"cmd": 0, "aktarilan": 0, "ack": 0,
                      "bilinmeyen": 0, "hata": 0, "kaynak_red": 0,
                      "zaman_red": 0, "tekrar": 0}
        # Yalnız oturumlu komutlarda kullanılır. Eski oturumsuz sınıf API'si
        # alan alan aynı kalır; saha YKS'si oturumla gecikmiş kuyruğu kapatır.
        # Değer True: Pixhawk ACCEPTED, False: Pixhawk'a ULAŞMIŞ ama kabul
        # ettirilememiş deneme (ret ya da ACK penceresi kapandı). MAVLink'e
        # hiç ulaşmamış teşebbüs buraya YAZILMAZ (K-2, `isle` gerekçesi).
        self._komut_sonuclari = {}
        # K-1: (monotonik_alis_ani, ham_fark) örnekleri; saat ofseti kestirimi.
        self._ofset_ornekleri = []
        self._son_ofset = None               # yürürlükteki kestirim
        # K-B: yerel saat adımı çapası — (monotonik, duvar) son ölçüm çifti.
        # İkisinin farkının farkı, YEREL duvar saatinin basamaklandığını
        # YKS'den gelen hiçbir alana bakmadan söyler (KARAR-2).
        self._saat_capasi = None

    # ── log ──────────────────────────────────────────────────────────────
    def _logla(self, metin, kirmizi=False):
        try:
            t = float(self.saat())
            damga = f"t={t:.3f}"
        except (TypeError, ValueError, OverflowError):
            damga = "t=?"
        seviye = "KIRMIZI " if kirmizi else ""
        print(f"{LOG_ONEKI} {damga} {seviye}{metin}",
              file=sys.stderr if kirmizi else sys.stdout, flush=True)

    # ── K-1: capraz-makine saat ofseti ───────────────────────────────────
    @staticmethod
    def _kestir(ornekler, en_az):
        """Örnek kümesinden dayanıklı ofset kestirimi; yetersizse ``None``.

        `ham = ofset_gercek + gecikme`, `gecikme >= 0` — bir çerçeve
        gönderilmeden ÖNCE alınamaz. Bu yüzden EN KÜÇÜK ham fark, gecikmesi en
        düşük çerçevedir ve ofsetin en iyi kestirimidir (NTP'nin "minimum
        filtresi" ile aynı akıl). Yaş bu kestirime göre ölçülünce iki makinenin
        saat farkı sadeleşir.

        KARAR-1 · KANIT EŞİĞİ İKİ KADEMELİDİR:
          * aday ofset ``KOMUT_SAAT_SAPMA_TAVANI_S`` bandının İÇİNDE ise
            ``en_az`` örnek yeter — bugünkü davranış aynen korunur;
          * bandın DIŞINDA ise ``KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK`` adet
            BİRBİRİNİ DESTEKLEYEN örnek gerekir. "Destekleyen" = aday ofsete
            göre yaşı meşru (``KOMUT_SAAT_DESTEK_BANDI_S`` içinde) olan örnek.
            Böylece RTC'siz Jetson'ın saatler/yıllar mertebesindeki gerçek
            sapması ÖĞRENİLEBİLİR olur (K-A ölümcül kilidi kalkar), ama tek
            bir çılgın çerçeve — ya da onun bir avuç tekrarı — kestirimi
            KURAMAZ.

        ⚠ ADAY, KÜRESEL ``min`` DEĞİL; KÜÇÜKTEN BÜYÜĞE TARANIR (K-C).
        Küresel `min`'e tek adayla bağlanmak bu kapıyı TEK PAKETLE
        kilitliyordu: kırılma noktası SIFIRDI. ÖLÇÜLDÜ (2026-09-04, saha
        mercekli çürütme; meşru sapma -600 s, tek çerçeve 10 gün İLERİ
        damgalı): aday o çerçeve olur, bant dışıdır, 6 destekçi bulamaz ve
        `None` döner — meşru -600 s KÜMESİ hiç denenmeden elenir. Sonuç:
        20 basamaklık RTL merdiveninden MAVLink'e giden 0, zaman_red 243,
        ARM/DISARM/RTL/LAND/PARACHUTE **60,75 s ÖLÜ** (aykırı örnek
        ``KOMUT_SAAT_OFSETI_PENCERESI_S`` boyunca durur; kaynak ısrar ederse
        KALICI). ESKİ kodda aynı senaryoda 18/20 basamak geçiyordu — yani
        K-A/K-B onarımı, K-B'nin kapattığı 60 s ölü pencereyi BAŞKA BİR
        KAPIDAN geri getiriyordu.
        Nedeni: `min` kırılma noktası 0 olan bir özettir; gerçek ofsetin
        ALTINDA tek bir örnek onu yok eder. KARAR-1 "dayanıklı bir özet"
        istiyor — dayanıklılık burada adayı TEK BAŞINA veto edilemez kılmakla
        sağlanır: adaylar artan sırada denenir ve KENDİ kanıt eşiğini
        karşılayan İLK (yani en küçük) aday kazanır. İki kademeli eşik
        AYNEN durur; gevşeyen hiçbir şey yoktur — yalnız bir aykırı örnek
        artık geri kalan kümeyi susturamaz.
        """
        if len(ornekler) < en_az:
            return None
        for aday in sorted(h for (_t, h) in ornekler):
            if abs(aday) <= KOMUT_SAAT_SAPMA_TAVANI_S:
                # Artan sırada ilk BANT İÇİ aday = bant içi örneklerin en
                # küçüğü; bant içi kanıt eşiği (ucuz kademe) bugünkü davranışın
                # ta kendisidir ve DEĞİŞMEZ. Daha büyük adaya bakmanın anlamı
                # yok: minimum filtresi en küçüğü ister.
                gerekli = max(en_az, KOMUT_SAAT_OFSETI_EN_AZ_ORNEK)
                return aday if len(ornekler) >= gerekli else None
            gerekli = max(en_az, KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK)
            destek = sum(1 for (_t, h) in ornekler
                         if -KOMUT_ZAMAN_YUVARLAMA_TOLERANSI_S
                         <= h - aday <= KOMUT_SAAT_DESTEK_BANDI_S)
            if destek >= gerekli:
                return aday
        return None

    def _yerel_saat_adimi(self, simdi_mono):
        """YEREL duvar saati basamaklandıysa sıçrama miktarını döndür (K-B).

        `time.monotonic` saat adımından etkilenmez, `time.time` adımla zıplar.
        İki ardışık ölçüm arasında ``duvar_farki - monotonik_farki`` sıfırdan
        belirgin biçimde sapıyorsa duvar saati basamaklanmıştır. Ölçüm YKS'den
        gelen HİÇBİR alana bakmaz — saldırgan bu yola giremez (modül başlığında
        çürütülen trafik-tabanlı alternatifin gerekçesi).

        Çapa HER çağrıda tazelenir; böylece NTP'nin yavaşlatma (slew)
        düzeltmesi birikip yanlışlıkla adım gibi görünmez.
        """
        try:
            duvar = float(self.duvar_saati())
        except Exception:
            duvar = None
        if duvar is None or not math.isfinite(duvar):
            self._saat_capasi = None
            return None
        capa, self._saat_capasi = self._saat_capasi, (simdi_mono, duvar)
        if capa is None:
            return None
        adim = (duvar - capa[1]) - (simdi_mono - capa[0])
        if not math.isfinite(adim) or abs(adim) <= KOMUT_SAAT_ADIMI_ESIGI_S:
            return None
        return adim

    def _saat_ofseti(self):
        """Pencere içindeki örneklerden güncel ofset kestirimi (modül başlığı).

        Dönen: ``(monotonik_an, ofset)``. Kanıt yetersizse ofset ``None``'dır
        ve kapı SIKI davranır (fail-closed). Değerlendirilen çerçevenin KENDİ
        örneği burada YOKTUR — örnekleme `_saat_ofseti_ornekle` ile SONRA
        yapılır; yoksa her çerçeve kendi damgasıyla kendini aklardı.

        KARAR-2 burada işler: YEREL duvar saati basamaklandıysa pencere ATILMAZ,
        adım kadar DÜZELTİLİR — 60 s'lik ölü pencere sıfırlanır.
        KARAR-3: ofset ilk kez öğrenildiğinde ve her adımda GÖRÜNÜR kayıt.
        """
        try:
            simdi_mono = float(self.saat())
        except (TypeError, ValueError, OverflowError):
            simdi_mono = None
        if simdi_mono is None or not math.isfinite(simdi_mono):
            self._son_ofset = None
            return None, None
        adim = self._yerel_saat_adimi(simdi_mono)
        self._ofset_ornekleri = [
            (t, h) for (t, h) in self._ofset_ornekleri
            if 0.0 <= simdi_mono - t <= KOMUT_SAAT_OFSETI_PENCERESI_S]
        if adim is not None:
            # Duvar saati `adim` kadar ziplarken ofset de tam o kadar değişti.
            # Örneklerin `ham` değerleri eski duvar saatiyle hesaplanmıştı;
            # kaydırılınca gecikme bilgisi korunur, ölü pencere kalmaz.
            self._ofset_ornekleri = [(t, h + adim)
                                     for (t, h) in self._ofset_ornekleri]
        onceki = self._son_ofset
        ofset = self._kestir(self._ofset_ornekleri,
                             KOMUT_SAAT_OFSETI_EN_AZ_ORNEK)
        self._son_ofset = ofset
        if adim is not None:
            self._logla(f"YEREL saat ADIMI algilandi: duvar saati {adim:+.3f} s "
                        f"zipladi (monotonik saate gore); ofset kestirimi "
                        f"{onceki!r} -> {ofset!r} olarak duzeltildi")
        elif ofset is not None and onceki is None:
            self._logla(f"saat ofseti OGRENILDI: {ofset:+.3f} s "
                        f"({len(self._ofset_ornekleri)} ornek); komut yasi "
                        f"bundan sonra bu ofsete GORE olculur")
        elif ofset is None and onceki is not None:
            self._logla(f"saat ofseti kestirimi DUSTU (onceki {onceki:+.3f} s); "
                        f"kapi yeniden SIKI — ofset yeniden ogrenilecek")
        return simdi_mono, ofset

    def _saat_ofseti_ornekle(self, simdi_mono, ham):
        """Ham farkı ANA kestirim örneklerine ekle (çağıran koşulu denetler).

        K-A DÜZELTMESİ: burada ARTIK mutlak bir sapma tavanı YOKTUR. Eskiden
        ``abs(ham) > KOMUT_SAAT_SAPMA_TAVANI_S`` olan örnek atılıyordu; ofset
        bilinmezken `ham` iki saatin FARKI olduğu için bu, öğrenmek için
        gereken örneğin ta kendisini eliyor ve kritik komutları KALICI olarak
        öldürüyordu. Çılgın damgaya karşı savunma artık ATMAK değil, `_kestir`
        içindeki İKİ KADEMELİ KANIT EŞİĞİdir: bant dışı bir kestirim ancak
        birbirini destekleyen ``KOMUT_SAAT_OFSETI_GENIS_EN_AZ_ORNEK`` örnekle
        kurulabilir.
        """
        if simdi_mono is None or not math.isfinite(ham):
            return
        self._ofset_ornekleri.append((simdi_mono, float(ham)))

    # ── aktarim ──────────────────────────────────────────────────────────
    def _aktar(self, cmd):
        """COMMAND_LONG gonder; her istisna cagirana cikar (ACK yok)."""
        mav_cmd, param1 = mavlink_komut_tablosu()[cmd]
        self.mav.mav.command_long_send(
            self.target_system, self.target_component, mav_cmd,
            MAVLINK_ONAY_ILK_GONDERIM, param1,
            MAVLINK_PARAM_KULLANILMIYOR, MAVLINK_PARAM_KULLANILMIYOR,
            MAVLINK_PARAM_KULLANILMIYOR, MAVLINK_PARAM_KULLANILMIYOR,
            MAVLINK_PARAM_KULLANILMIYOR, MAVLINK_PARAM_KULLANILMIYOR)
        return (f"COMMAND_LONG(cmd={mav_cmd}, param1={param1}, "
                f"sys={self.target_system}, comp={self.target_component})",
                mav_cmd)

    def _ack_basabilen_bilesenler(self, m):
        """Bu komutun COMMAND_ACK'ini basmaya YETKİLİ bileşen kimlikleri (K-3).

        VARSAYIM AÇIKÇA YAZILIR: ArduPilot bir COMMAND_LONG'u OTOPİLOT bileşeni
        (``MAV_COMP_ID_AUTOPILOT1``) olarak işler ve COMMAND_ACK'i o bileşen
        kimliğinden basar — komut başka bir ``target_component``a adreslenmiş
        olsa bile. ArduPilot varsayılanında ikisi de 1 olduğu için örtüşür;
        `--target-component` varsayılandan farklı verildiğinde AYRIŞIRLAR.
        Bu yüzden geçerli küme:
          * ``MAVLINK_BELIRTILMEMIS_COMPONENT`` — kaynak bileşen belirtilmemiş
            (eski pymavlink / sahte uç); geriye uyum.
          * ``MAV_COMP_ID_AUTOPILOT1`` — komutu gerçekten işleyen otopilot.
          * ``self.target_component`` — komutun adreslendiği bileşen, kendi
            adına cevaplarsa.
        Bunların DIŞINDA hiçbir bileşen (kamera, gimbal, companion) bu komutun
        ACK'ini veremez: kapı KAPALI kalır, yalnız doğru kümeyi ölçer.
        """
        return (MAVLINK_BELIRTILMEMIS_COMPONENT,
                int(m.MAV_COMP_ID_AUTOPILOT1),
                int(self.target_component))

    def _komut_ack_bekle(self, mav_cmd):
        """Pixhawk'in COMMAND_ACK'ini bekle -> (kabul_edildi, aciklama).

        D-403: pymavlink'in her tasiyicisi write() hatasini YUTAR (seri -1
        doner, udp socket.error'u yutar); "istisnasiz gonderildi" kanit
        degildir. ArduPlane DO_PARACHUTE'u reddedebilir (CHUTE_ENABLED=0,
        zaten acik, CHUTE_ALT_MIN alti -> MAV_RESULT_FAILED). Tek durust
        olcut COMMAND_ACK(command == mav_cmd, result == ACCEPTED).
        """
        m = _mavutil_al().mavlink
        son = self.saat() + MAVLINK_KOMUT_ACK_TAVANI_S
        while True:
            kalan = son - self.saat()
            if kalan <= 0:
                return False, (f"COMMAND_ACK {MAVLINK_KOMUT_ACK_TAVANI_S:.1f} s "
                               f"icinde GELMEDI (Pixhawk/cogullayici olu?)")
            try:
                cevap = self.mav.recv_match(type="COMMAND_ACK", blocking=True,
                                            timeout=kalan)
            except Exception as exc:
                return False, f"COMMAND_ACK okunamadi ({type(exc).__name__}: {exc})"
            if cevap is None:
                # blocking recv_match None dondu = tasiyici zaman asimi doldu.
                # `continue` DEGIL: donuk saatli testte sonsuz donguye girerdi.
                return False, (f"COMMAND_ACK {MAVLINK_KOMUT_ACK_TAVANI_S:.1f} s "
                               f"icinde GELMEDI (Pixhawk/cogullayici olu?)")
            if int(getattr(cevap, "command", -1)) != int(mav_cmd):
                continue                                  # baska komutun ACK'i
            # D-403 (curutucu ONEMLI): ACK HEDEF aracin sysid'inden gelmeli —
            # SYSID_THISMAV != --sysid ise ArduPilot komutu yerel islemez;
            # baska bir kaynagin ACK'i "kabul" sayilamaz.
            try:
                kaynak = int(cevap.get_srcSystem())
            except Exception:
                kaynak = None
            if kaynak != self.target_system:
                self._logla(f"COMMAND_ACK yabanci sysid={kaynak} "
                            f"(beklenen {self.target_system}) — yok sayildi",
                            kirmizi=True)
                continue
            # K-3: ACK'i GÖNDEREN bileşen ile komutun ADRESLENDİĞİ bileşen
            # AYRI alanlardır — `COMMAND_LONG.target_component` "kime
            # gönderdim", `COMMAND_ACK.srcComponent` "kim cevapladı" demektir.
            # Aynı MAVLink sisteminde kamera/gimbal/companion gibi başka
            # bileşenler de bulunduğu için kapı KALIR, ama ikisini EŞİTLEMEK
            # yazılı olmayan bir varsayımdı ve ölçüldü (3 Eylül): sahte Pixhawk
            # gerçek ArduPilot gibi component=1'den ACK basar, alıcı
            # `--target-component 3` ile açılınca HER ACK "yabancı" sayıldı ve
            # PARACHUTE/ARM/DISARM/RTL/LAND uçtan uca DÜŞTÜ.
            # Doğru ölçüt: ACK'i basmaya YETKİLİ bileşen kümesi.
            bilesen_al = getattr(cevap, "get_srcComponent", None)
            if callable(bilesen_al):
                try:
                    bilesen = int(bilesen_al())
                except Exception:
                    bilesen = None      # okunamayan bileşen = fail-closed
                if bilesen not in self._ack_basabilen_bilesenler(m):
                    self._logla(f"COMMAND_ACK yabanci component={bilesen} "
                                f"(gecerli {self._ack_basabilen_bilesenler(m)})"
                                f" — yok sayildi", kirmizi=True)
                    continue
            sonuc = int(getattr(cevap, "result", -1))
            if sonuc == m.MAV_RESULT_ACCEPTED:
                return True, "COMMAND_ACK ACCEPTED"
            return False, f"COMMAND_ACK REDDETTI (MAV_RESULT={sonuc})"

    def _ack_gonder(self, seq, adr, cmd):
        data = encode(ack(seq, self.node, MESAJ_TIPI_CMD,
                          ref_cmd=cmd, sonuc=ACK_SONUC_KABUL))
        try:
            if adr is None:
                self.link.send(data)              # seri (SiK): ortam yayini
            else:
                self.link.send(data, adr)         # UDP: gonderene (YKS)
        except (OSError, TypeError, ValueError) as exc:
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq}: ACK gonderilemedi "
                        f"({type(exc).__name__}: {exc}); YKS tekrarinda komut "
                        f"yeniden aktarilir ve ACK yeniden denenir", kirmizi=True)
            return False
        self.sayac["ack"] += 1
        self._logla(f"ACK(ref={seq}, node={self.node}, ref_tip={MESAJ_TIPI_CMD}, "
                    f"ref_cmd={cmd}, sonuc={ACK_SONUC_KABUL})"
                    f" -> {adr if adr is not None else 'seri yayin'}")
        return True

    def isle(self, mesaj, adr):
        """Tek mesaj: CMD+hedef==node ise isle; ACK gonderildiyse True."""
        if not isinstance(mesaj, dict) or mesaj.get("type") != MESAJ_TIPI_CMD:
            return False
        if mesaj.get("hedef") != self.node:
            return False                              # baska dugumun komutu
        if self.izinli_kaynak is not None:
            try:
                gelen = None if adr is None else (str(adr[0]), int(adr[1]))
            except (IndexError, TypeError, ValueError):
                gelen = None
            if gelen != self.izinli_kaynak:
                self.sayac["kaynak_red"] += 1
                self._logla(f"CMD kaynagi RED: gelen={gelen!r}, izinli="
                            f"{self.izinli_kaynak!r}; MAVLink yok, ACK YOK",
                            kirmizi=True)
                return False
        self.sayac["cmd"] += 1
        seq = mesaj.get("seq")
        cmd = mesaj.get("cmd")
        if (isinstance(seq, bool) or not isinstance(seq, int)
                or not isinstance(cmd, str)):
            self.sayac["hata"] += 1
            self._logla(f"bozuk CMD (cmd={cmd!r} seq={seq!r}); aktarim yok, "
                        f"ACK YOK", kirmizi=True)
            return False
        # D-403 (KRITIK-2): (cmd, seq) hafizasi YOK — her gecerli komut yeniden
        # aktarilir ve yeniden COMMAND_ACK beklenir (dokstring).
        if cmd not in KOMUT_ADLARI:
            self.sayac["bilinmeyen"] += 1
            self._logla(f"bilinmeyen CMD {cmd!r} seq={seq}; aktarim yok, "
                        f"ACK YOK", kirmizi=True)
            return False

        # Kritik uçuş komutları yalnız YKS'nin tekrar penceresi içinde yaşar.
        # bool, NaN/sonsuz, eksik ve anlamlı toleranstan ileri damga fail-closed.
        # K-1: ham fark İKİ MAKİNENİN saat farkını içerir; yaş, trafikten
        # kestirilen ofsete GÖRE hesaplanır (modül başlığındaki gerekçe).
        damga = mesaj.get("t")
        try:
            simdi = self.duvar_saati()
        except Exception:
            simdi = None
        simdi_mono, ofset = self._saat_ofseti()
        if (isinstance(damga, bool) or not isinstance(damga, Real)
                or isinstance(simdi, bool) or not isinstance(simdi, Real)
                or not math.isfinite(float(damga))
                or not math.isfinite(float(simdi))):
            ham = yas = None
        else:
            ham = float(simdi) - float(damga)
            yas = ham - (0.0 if ofset is None else ofset)
        tavan = KOMUT_YAS_TAVANI_S[cmd]
        zaman_kabul = (yas is not None
                       and -KOMUT_ZAMAN_YUVARLAMA_TOLERANSI_S <= yas <= tavan)
        if ham is not None and (zaman_kabul or ofset is None):
            # Örnek yalnız iki durumda alınır: (a) çerçeve kapıdan GEÇTİ, ya da
            # (b) ofset henüz BİLİNMİYOR — sapmayı öğrenmenin tek yolu budur.
            # Ofset BİLİNİRKEN reddedilen çerçeve kestirimi KAYDIRAMAZ; yoksa
            # ısrarlı ileri/bayat damgalı bir kaynak, kendi reddedilen
            # örnekleriyle ofseti kendi üzerine çeker ve bir sonraki adımda
            # kapıdan geçerdi (3 Eylül'de ÖLÇÜLDÜ: ikinci gönderimde geçiyordu;
            # 4 Eylül'de trafik-tabanlı adım kanıtı denendiğinde 10. ısrarda
            # yeniden ÖLÇÜLDÜ — bkz. modül başlığındaki reddedilen alternatif).
            # Saat basamaklı düzeltilirse kestirimi düzelten şey bu örnekler
            # DEĞİL, `_yerel_saat_adimi`nin yerel ölçümüdür (KARAR-2).
            self._saat_ofseti_ornekle(simdi_mono, ham)
        if not zaman_kabul:
            self.sayac["zaman_red"] += 1
            self._logla(f"CMD {cmd} seq={seq}: zaman RED (yas={yas!r}, "
                        f"ham={ham!r}, saat_ofseti={ofset!r}, "
                        f"tavan={tavan:.2f} s); MAVLink yok, ACK YOK",
                        kirmizi=True)
            return False

        oturum = mesaj.get("oturum")
        anahtar = None
        if oturum is not None:
            try:
                oturum = oturum_dogrula(oturum)
            except ValueError as exc:
                self.sayac["hata"] += 1
                self._logla(f"CMD {cmd} seq={seq}: bozuk oturum ({exc}); "
                            "MAVLink yok, ACK YOK", kirmizi=True)
                return False
            anahtar = (oturum, seq, cmd)
            if anahtar in self._komut_sonuclari:
                self.sayac["tekrar"] += 1
                if self._komut_sonuclari[anahtar]:
                    self._logla(f"CMD {cmd} seq={seq}: oturum tekrari; eyleyici "
                                "yeniden calistirilmadi, ACCEPTED ACK yineleniyor")
                    return self._ack_gonder(seq, adr, cmd)
                self._logla(f"CMD {cmd} seq={seq}: oturum tekrari; ilk sonuc "
                            "basarisizdi, gecikmis eylem RED, ACK YOK",
                            kirmizi=True)
                return False
        # ── K-2: anahtar BURADA zehirlenmez ──────────────────────────────
        # "İlk giriş terminaldir" niyeti KORUNUR, ama TERMİNAL olan şey
        # MAVLink'e ULAŞMIŞ bir denemedir. Anahtarı aktarımdan ÖNCE `False`
        # yazmak, hemen ardındaki iki fail-closed çıkışın (`mav is None`,
        # hedef bilinmiyor) anahtarı KALICI olarak zehirlemesine yol açıyordu:
        # aynı (oturum, seq, cmd) ile gelen sonraki her istek "ilk sonuç
        # başarısızdı, gecikmiş eylem RED" ile eleniyordu. Bu, D-02/K4'ün
        # ACK'li aynı-seq tekrar merdivenini (`comms/komut_tekrar.py`,
        # 8 tekrar × 0,25 s) ÖLDÜRÜR — saha açılışında ilk deneme Pixhawk'tan
        # daha paket gelmeden yapılır (SIK durum) ve o andan sonra ARM/DISARM/
        # RTL/LAND/PARACHUTE bir daha asla geçemezdi.
        # MAVLink'e HİÇ ULAŞMAMIŞ teşebbüs (bağlantı yok / hedef bilinmiyor /
        # aktarım istisnası) terminal DEĞİLDİR: araç ÇALIŞMAMIŞTIR, dolayısıyla
        # gecikmiş eylem tehlikesi de yoktur. Böyle bir teşebbüs yalnızca
        # başarısız döner ve YKS tekrarında yeniden denenebilir.
        if self.mav is None:
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq}: MAVLink baglantisi YOK; "
                        f"aktarim yapilmadi, ACK YOK", kirmizi=True)
            return False
        if not mav_hedefi_biliniyor_mu(self.mav):
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq}: Pixhawk/cogullayicidan henuz "
                        f"paket gelmedi, pymavlink sessizce dusurecekti; "
                        f"aktarim yapilmadi, ACK YOK", kirmizi=True)
            return False
        try:
            aciklama, mav_cmd = self._aktar(cmd)
        except Exception as exc:                      # fail-closed: ACK yok
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq} aktarim HATASI "
                        f"({type(exc).__name__}: {exc}); ACK YOK — YKS "
                        f"tekrarlayacak", kirmizi=True)
            return False
        # D-403: gonderim kanit degil — Pixhawk'in COMMAND_ACK'i beklenir.
        kabul, ack_aciklama = self._komut_ack_bekle(mav_cmd)
        # K-2: BURASI TERMİNAL SINIRIDIR. COMMAND_LONG tele çıktı; Pixhawk
        # komutu işlemiş OLABİLİR. Sonuç ACCEPTED, REJECTED ya da "ACK gelmedi"
        # olsun — aynı (oturum, seq, cmd) bir daha ÇALIŞTIRILMAZ; aksi hâlde
        # aynı eyleyici dakikalar sonra gecikmeli olarak tetiklenebilirdi.
        # `True`: ACK taşıması başarısız olsa da Pixhawk kabul etti; sonraki
        # tekrar yalnız güçlü ACK'i yineler, eyleyiciye dokunmaz.
        if anahtar is not None:
            self._komut_sonuclari[anahtar] = bool(kabul)
        if not kabul:
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq} -> {aciklama} gonderildi ama "
                        f"{ack_aciklama}; ACK YOK — YKS tekrarlayacak",
                        kirmizi=True)
            return False
        self.sayac["aktarilan"] += 1
        self._logla(f"CMD {cmd} seq={seq} -> Pixhawk {aciklama} "
                    f"{ack_aciklama}")
        return self._ack_gonder(seq, adr, cmd)

    # ── dongu ────────────────────────────────────────────────────────────
    def _mavlink_gelen_kutusunu_bosalt(self):
        """Akran adresini ogren (udp: sunucu) ve soket birikimini onle."""
        if self.mav is None:
            return
        recv_match = getattr(self.mav, "recv_match", None)
        if not callable(recv_match):
            return
        try:
            for _ in range(MAVLINK_BOSALTMA_TAVANI):
                if recv_match(blocking=False) is None:
                    break
        except Exception as exc:
            self._logla(f"MAVLink okuma hatasi ({type(exc).__name__}: {exc})",
                        kirmizi=True)

    def poll(self):
        """Bir tur: linkten oku, cerceveleri isle, MAVLink kutusunu bosalt.

        Donus: bu turda islenen her mesaj icin ``isle`` sonucu (liste).
        """
        sonuc = []
        d, adr = self.link.recv()
        if d:
            # D-403 (KUCUK-4): UDP'de datagram = cerceve siniri. Kalici
            # tamponda newline'siz bir artik, SONRAKI gecerli PARACHUTE
            # cercevesini bozuyordu. UDP'de her datagram taze okuyucuyla;
            # seri (adr None) bayt akisidir, kalici okuyucu kalir.
            okuyucu = FrameReader() if adr is not None else self.reader
            for m in okuyucu.feed(d):
                sonuc.append(self.isle(m, adr))
        self._mavlink_gelen_kutusunu_bosalt()
        return sonuc

    def calistir(self):
        """FrameReader ile link.recv() dongusu; KeyboardInterrupt ile cikar."""
        self._dur.clear()
        self._logla(f"dinleniyor: node={self.node} hedef sys="
                    f"{self.target_system} comp={self.target_component} "
                    f"mav={'YOK (ACK uretilmez)' if self.mav is None else 'acik'}")
        try:
            while not self._dur.is_set():
                self.poll()
        except KeyboardInterrupt:
            self._logla("kapatiliyor (KeyboardInterrupt)")

    def durdur(self):
        self._dur.set()


# ── CLI ──────────────────────────────────────────────────────────────────────

def _arg_parser():
    ap = argparse.ArgumentParser(
        description="IHA komut alicisi: YKS CMD -> Pixhawk MAVLink; ACK yalniz "
                    "aktarim basariliysa (D-393)")
    ap.add_argument("--bind", default=VARSAYILAN_BIND,
                    help="UDP dinleme host:port (varsayilan %(default)s)")
    ap.add_argument(
        "--izinli-kaynak", type=_cli_kaynak_adresi,
        help=("yalniz bu YKS UDP HOST:PORT kaynaginin kritik CMD'lerini kabul "
              "et (saha icin zorunlu; SiK'te seri_hub kaynagi "
              "127.0.0.1:5100)"))
    ap.add_argument("--serial",
                    help="SiK telsiz seri portu (saha); verilirse --bind "
                         "kullanilmaz")
    ap.add_argument("--baud", type=int, default=VARSAYILAN_BAUD,
                    help="SiK seri baud (varsayilan %(default)s)")
    ap.add_argument("--mavlink", required=True,
                    help="Pixhawk MAVLink baglantisi — COGULLAYICI UCU "
                         "(or. udp:127.0.0.1:14560); seri Pixhawk tek "
                         "sahiplidir, dogrudan /dev/ttyACM0 VERME")
    # D-403 kilidi UC surecte de ayni: bayrak adi, yardim metni ve red
    # metni `inis_kaniti`den okunur (FDR/ACIK_KALEMLER §4b #23).
    seri_pixhawk_bayragini_ekle(ap)
    ap.add_argument("--sysid", type=int, default=VARSAYILAN_HEDEF_SYSID,
                    help="hedef MAVLink sistem kimligi — Pixhawk SYSID_THISMAV "
                         "ile AYNI olmali; COMMAND_ACK yalniz bu sysid'den "
                         "kabul edilir (ArduPilot varsayilani %(default)s)")
    ap.add_argument("--target-component", type=int,
                    default=VARSAYILAN_HEDEF_COMPONENT,
                    help="hedef MAVLink bilesen kimligi (MAV_COMP_ID_AUTOPILOT1"
                         " = %(default)s)")
    ap.add_argument("--node", default=VARSAYILAN_DUGUM,
                    help="bu dugumun adi; yalniz hedef==node komutlar islenir "
                         "(varsayilan %(default)s)")
    return ap


def _kapat(nesne):
    kapat = getattr(nesne, "close", None)
    if callable(kapat):
        try:
            kapat()
        except (OSError, RuntimeError):
            pass


def main(argv=None):
    parser = _arg_parser()
    args = parser.parse_args(argv)
    if not 1 <= args.sysid <= 255:
        parser.error("--sysid 1..255 araliginda olmali")
    if not 0 <= args.target_component <= 255:
        parser.error("--target-component 0..255 araliginda olmali")
    if args.baud <= 0:
        parser.error("--baud pozitif olmali")
    if args.izinli_kaynak is None:
        parser.error("--izinli-kaynak HOST:PORT saha komutlari icin zorunlu; "
                     "kaynak pinsiz ARM/DISARM/PARACHUTE/RTL/LAND kabul edilmez")
    if args.serial:
        parser.error("--serial kaynagi adresle pinlenemez; seri portu tek sahipli "
                     "seri_hub acsin, bu sureci --bind 127.0.0.1:5007 "
                     "--izinli-kaynak 127.0.0.1:5100 ile calistirin")
    # D-403 (curutucu KUCUK): CONTRACTS §7.4 yalniz belgeydi, kod engellemiyordu.
    # Seri Pixhawk tek sahiplidir; dogrudan cihaz verilirse rpi_inference /
    # iha_inis_yayinci ile cakisir ve iki taraf da SESSIZCE kor olur.
    # Kalip artik `inis_kaniti`de: ayni kilit o iki surecte de KODLU.
    seri_pixhawk_kilidini_uygula(parser, args.mavlink,
                                 args.seri_pixhawk_bilerek)

    try:
        mav = mavlink_baglantisi_ac(args.mavlink)
    except (ImportError, ConnectionError) as exc:
        print(f"{LOG_ONEKI} HATA: {exc}", file=sys.stderr)
        return 2

    link = None
    try:
        try:
            if args.serial:
                link = SerialLink(args.serial, args.baud)
                print(f"{LOG_ONEKI} SiK seri hat: {args.serial} @ {args.baud}")
            else:
                h, p = args.bind.rsplit(":", 1)
                link = UDPLink(bind=(h, int(p)))
                print(f"{LOG_ONEKI} UDP dinleniyor: {args.bind}")
        except (ImportError, OSError, ValueError) as exc:
            print(f"{LOG_ONEKI} HATA: tasiyici acilamadi: {exc}",
                  file=sys.stderr)
            return 4
        alici = IhaKomutAlici(link, mav, node=args.node,
                              target_system=args.sysid,
                              target_component=args.target_component,
                              izinli_kaynak=args.izinli_kaynak)
        alici.calistir()
        return 0
    finally:
        _kapat(link)
        _kapat(mav)


if __name__ == "__main__":
    raise SystemExit(main())
