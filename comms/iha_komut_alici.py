#!/usr/bin/env python3
"""NEDEN: Sartname §2.2.4 (parasut "yer istasyonundan manuel tetikleme ile de
gerceklestirilebilir") ve §6.4; CONTRACTS §6.6 PARACHUTE maddesi; D-393.
YKS parasut komutunu ACK gelene dek tekrarliyor ama IHA tarafinda CMD dinleyen
uc YOKTU ("AVIYONIK-BLOKLU"). Bu surec o boslugun YAZILIM yarisini kapatir:
Jetson'da kosar, YKS'nin CMD mesajlarini (UDP ya da SiK seri) alir, Pixhawk'a
MAVLink COMMAND_LONG ile aktarir ve YALNIZ aktarim basariliysa ACK doner.

ACK "aldim VE yaptim" demektir (D-393 durustluk sozlesmesi):
  * command_long_send istisna firlatirsa ACK YOK, KIRMIZI log;
  * MAVLink baglantisi yoksa aktarim yok, ACK YOK, log;
  * bilinmeyen komut aktarilmaz ve ACK'lanmaz.
Boylece YKS tekrarlamaya devam eder ve hakem ekraninda "ACK YOK" gorunur —
sessiz basari yalani yoktur.

Idempotentlik (IKA_GO kalibi, CONTRACTS §6.6): ayni (cmd, seq) ikinci kez
gelirse ACK yeniden gonderilir ama MAVLink komutu YENIDEN GONDERILMEZ. Hafiza
yalniz BASARILI aktarimlari tutar: basarisiz denemeden sonra gelen tekrar
yeniden aktarilir (YKS zaten ACK gelmedigi icin tekrarliyordur).

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
import collections
import importlib
import sys
import threading
import time
from pathlib import Path

_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

from inis_kaniti import mavlink_baglantisi_ac  # noqa: E402
from link import SerialLink, UDPLink  # noqa: E402
from protocol import FrameReader, ack, encode  # noqa: E402

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


# ── Protokol adlari (CONTRACTS §6 mesaj tablosu + §6.6) ──────────────────────
MESAJ_TIPI_CMD = "CMD"
CMD_PARACHUTE = "PARACHUTE"       # CONTRACTS §6.6 · D-393 · sartname §2.2.4
CMD_ARM = "ARM"                   # CONTRACTS §6 tablo: "IKA_GO, ARM, ..."
CMD_DISARM = "DISARM"
KOMUT_ADLARI = (CMD_PARACHUTE, CMD_ARM, CMD_DISARM)
VARSAYILAN_DUGUM = "iha"          # protocol.iha_landed ile ayni dugum adi
VARSAYILAN_BIND = "0.0.0.0:5007"  # yks_gui son_adr["iha"] varsayilani (5007)
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

# Idempotentlik hafizasi tavani: 15 dakikalik ucusta ayrik (cmd, seq) sayisi
# onlarla olculur; tavan yalniz sinirsiz buyumeyi keser (en eski dusurulur).
BASARILI_KOMUT_HAFIZASI = 256
# Bir poll turunda MAVLink gelen kutusundan bosaltilacak en cok mesaj sayisi:
# Pixhawk ~10-50 mesaj/s, tur <= link zaman asimi (0,3 s) -> 64 yeterli.
MAVLINK_BOSALTMA_TAVANI = 64
LOG_ONEKI = "[IHA_KOMUT]"


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
                 saat=time.monotonic):
        if not callable(saat):
            raise TypeError("saat cagrilabilir olmali")
        self.link = link
        self.mav = mav                       # None: aktarim yok, ACK yok
        self.node = str(node)
        self.target_system = _kimlik_dogrula(target_system, "target_system", 1)
        self.target_component = _kimlik_dogrula(
            target_component, "target_component", 0)
        self.saat = saat
        self.reader = FrameReader()
        self._basarili = collections.OrderedDict()   # (cmd, seq) -> t
        self._dur = threading.Event()
        self.sayac = {"cmd": 0, "aktarilan": 0, "ack": 0, "mukerrer": 0,
                      "bilinmeyen": 0, "hata": 0}

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
                f"sys={self.target_system}, comp={self.target_component})")

    def _basariyi_kaydet(self, anahtar):
        self._basarili[anahtar] = self.saat()
        while len(self._basarili) > BASARILI_KOMUT_HAFIZASI:
            self._basarili.popitem(last=False)

    def _ack_gonder(self, seq, adr, cmd):
        data = encode(ack(seq, self.node, MESAJ_TIPI_CMD))
        try:
            if adr is None:
                self.link.send(data)              # seri (SiK): ortam yayini
            else:
                self.link.send(data, adr)         # UDP: gonderene (YKS)
        except (OSError, TypeError, ValueError) as exc:
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq}: ACK gonderilemedi "
                        f"({type(exc).__name__}: {exc}); YKS tekrarinda ACK "
                        f"yinelenir, komut yeniden aktarilmaz", kirmizi=True)
            return False
        self.sayac["ack"] += 1
        self._logla(f"ACK(ref={seq}, node={self.node}, ref_tip={MESAJ_TIPI_CMD})"
                    f" -> {adr if adr is not None else 'seri yayin'}")
        return True

    def isle(self, mesaj, adr):
        """Tek mesaj: CMD+hedef==node ise isle; ACK gonderildiyse True."""
        if not isinstance(mesaj, dict) or mesaj.get("type") != MESAJ_TIPI_CMD:
            return False
        if mesaj.get("hedef") != self.node:
            return False                              # baska dugumun komutu
        self.sayac["cmd"] += 1
        seq = mesaj.get("seq")
        cmd = mesaj.get("cmd")
        if (isinstance(seq, bool) or not isinstance(seq, int)
                or not isinstance(cmd, str)):
            self.sayac["hata"] += 1
            self._logla(f"bozuk CMD (cmd={cmd!r} seq={seq!r}); aktarim yok, "
                        f"ACK YOK", kirmizi=True)
            return False
        anahtar = (cmd, seq)
        if anahtar in self._basarili:
            self.sayac["mukerrer"] += 1
            self._logla(f"CMD {cmd} seq={seq} MUKERRER: MAVLink yeniden "
                        f"GONDERILMEDI, ACK yineleniyor")
            return self._ack_gonder(seq, adr, cmd)
        if cmd not in KOMUT_ADLARI:
            self.sayac["bilinmeyen"] += 1
            self._logla(f"bilinmeyen CMD {cmd!r} seq={seq}; aktarim yok, "
                        f"ACK YOK", kirmizi=True)
            return False
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
            aciklama = self._aktar(cmd)
        except Exception as exc:                      # fail-closed: ACK yok
            self.sayac["hata"] += 1
            self._logla(f"CMD {cmd} seq={seq} aktarim HATASI "
                        f"({type(exc).__name__}: {exc}); ACK YOK — YKS "
                        f"tekrarlayacak", kirmizi=True)
            return False
        self._basariyi_kaydet(anahtar)
        self.sayac["aktarilan"] += 1
        self._logla(f"CMD {cmd} seq={seq} -> Pixhawk {aciklama} aktarildi")
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
            for m in self.reader.feed(d):
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
    ap.add_argument("--serial",
                    help="SiK telsiz seri portu (saha); verilirse --bind "
                         "kullanilmaz")
    ap.add_argument("--baud", type=int, default=VARSAYILAN_BAUD,
                    help="SiK seri baud (varsayilan %(default)s)")
    ap.add_argument("--mavlink", required=True,
                    help="Pixhawk MAVLink baglantisi — COGULLAYICI UCU "
                         "(or. udp:127.0.0.1:14560); seri Pixhawk tek "
                         "sahiplidir, dogrudan /dev/ttyACM0 VERME")
    ap.add_argument("--sysid", type=int, default=VARSAYILAN_HEDEF_SYSID,
                    help="hedef MAVLink sistem kimligi (ArduPilot varsayilani "
                         "%(default)s)")
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
                              target_component=args.target_component)
        alici.calistir()
        return 0
    finally:
        _kapat(link)
        _kapat(mav)


if __name__ == "__main__":
    raise SystemExit(main())
