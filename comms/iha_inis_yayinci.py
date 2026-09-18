#!/usr/bin/env python3
"""NEDEN: Saha görevinde IHA_LANDED mesajı ancak Pixhawk iniş kanıtı
doğrulandıktan sonra, İKA/YKS haberleşme protokolünün ACK'li yayın yoluyla
üretilmelidir. Simülasyon pozu ve operatör düğmesi saha kanıtı sayılmaz.

T207 (D-406 A): ArduCopter EXTENDED_SYS_STATE'i hiçbir `SR*` akışında vermez;
yalnız MAV_CMD_SET_MESSAGE_INTERVAL ile akar, istek bağlantıya özeldir ve
Pixhawk yeniden başlayınca (pil değişimi) silinir. Bu süreç iniş kanıtının
TEK üreticisidir; isteği kendisi yapmazsa reboot sonrası kanıt SESSİZCE ölür.
Bu yüzden başta ve her MAVLINK_AKIS_ISTEK_ARALIGI_S'de EXTENDED_SYS_STATE,
GLOBAL_POSITION_INT ve YKİ GNSS göstergesi için GPS_RAW_INT isteği gönderir;
EXTENDED
MAVLINK_AKIS_SESSIZLIK_TAVANI_S boyunca gelmezse KIRMIZI loglar ve anında
yeniden ister (fail-visible). Kanıt kararı (`inis_kaniti.yerde_mi`) DEĞİŞMEZ.

⚠ JETSON'DA SERI PIXHAWK TEK SAHIPLIDIR (CONTRACTS §7.4 · D-403). Bu surec
`rpi_inference` (bagil irtifa) ve `iha_komut_alici` (PARACHUTE/ARM) ile AYNI
`/dev/ttyACM0`'i acamaz — acarsa cerceveler bolunur ve her iki taraf da
SESSIZCE kor olur. Seri portu yalniz cogullayici acar (mavlink-router ya da
`MAVProxy --out udp:127.0.0.1:1455N`); bu surecin ucu **14551**'dir.
Kilit artik BELGE DEGIL KOD: `--mavlink` seri cihaz yolu alirsa cikis 2
(FDR/ACIK_KALEMLER §4b #23); bilerek asmak icin `--seri-pixhawk-bilerek`.
🔴 Buradaki ornek eskiden `/dev/ttyACM0` gosteriyordu — kilavuzun kendisi
sozlesmeyi ihlal ediyordu; DEGISTIRILDI, geri konmaz.

Örnekler:
  python3 iha_inis_yayinci.py --mavlink udp:127.0.0.1:14551 --kanit-timeout 5 --ika 10.0.0.2:5006
  python3 iha_inis_yayinci.py --mavlink udp:127.0.0.1:14551 --kanit-timeout 5 --serial /dev/ttyUSB0
"""

import argparse
import math
import sys
import threading
import time
from numbers import Real
from pathlib import Path


_BU_DIZIN = Path(__file__).resolve().parent
if str(_BU_DIZIN) not in sys.path:
    sys.path.insert(0, str(_BU_DIZIN))

from iha_komut_alici import (  # noqa: E402
    MAVLINK_ONAY_ILK_GONDERIM, MAVLINK_PARAM_KULLANILMIYOR,
    mav_hedefi_biliniyor_mu)
from iha_sender import IhaSender, _addr as udp_adres  # noqa: E402
from inis_kaniti import (  # noqa: E402
    MESAJ_EXTENDED_SYS_STATE, MESAJ_GLOBAL_POSITION_INT, MESAJ_GPS_RAW_INT,
    _mavutil_al, _mesaj_kaynagi, _mesaj_tipi, mavlink_baglantisi_ac,
    seri_pixhawk_bayragini_ekle, seri_pixhawk_kilidini_uygula, yerde_mi)
from link import SerialLink, UDPLink  # noqa: E402

_KOK = _BU_DIZIN.parent
for _aday in (_BU_DIZIN, _KOK / "codes"):
    if str(_aday) not in sys.path:
        sys.path.insert(0, str(_aday))
from karar_sozlesmesi import (  # noqa: E402
    IHA_INIS_HEARTBEAT_ARALIGI_S, IHA_INIS_HEARTBEAT_SURESI_S,
    MAVLINK_AKIS_ISTEK_ARALIGI_S, MAVLINK_AKIS_ISTEK_HIZ_CARPANI,
    MAVLINK_AKIS_SESSIZLIK_TAVANI_S, MAVLINK_DURUM_ASGARI_HZ,
    MAVLINK_KONUM_ASGARI_HZ)

LOG_ONEKI = "[İHA]"
# KIRMIZI log metni sabittir: saha günlüğünde grep ile aranır (D-406 A).
SESSIZLIK_UYARISI = "EXTENDED_SYS_STATE gelmiyor — akis yeniden isteniyor"
MIKROSANIYE_BIR_SANIYE = 1e6
# `recv_match` bekleme dilimi: bakım (istek yenileme, sessizlik denetimi) en
# geç bu sıklıkla koşar. Sözleşme değil iç çözünürlük; sessizlik tavanının
# onda biri -> tespit gecikmesi <= 0,5 s. Toplam bekleme süresi DEĞİŞMEZ.
AKIS_BAKIM_DILIMI_S = MAVLINK_AKIS_SESSIZLIK_TAVANI_S / 10.0


def istek_araligi_us(asgari_hz, carpan=MAVLINK_AKIS_ISTEK_HIZ_CARPANI):
    """SET_MESSAGE_INTERVAL aralığı (us) = 1e6 / (asgari_hz x carpan)."""
    return int(round(MIKROSANIYE_BIR_SANIYE / (float(asgari_hz) * float(carpan))))


def akis_istek_tanimlari(carpan=MAVLINK_AKIS_ISTEK_HIZ_CARPANI):
    """İstenecek akışlar: ad, MAVLink mesaj id'si (pymavlink'ten), aralık.

    İniş kanıtının iki akışı ile YKİ'nin GNSS durum akışı. GPS_RAW_INT,
    GLOBAL_POSITION_INT ile aynı sözleşme hızını kullanır; ikinci bir çıplak
    frekans tanımlanmaz.
    pymavlink yoksa ImportError, sabit adı yoksa AttributeError yükselir;
    çağıran (`AkisIstekcisi`) bunu görünür kılar, yutmaz.
    """
    m = _mavutil_al().mavlink
    return [
        {"ad": MESAJ_EXTENDED_SYS_STATE,
         "id": int(m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE),
         "asgari_hz": MAVLINK_DURUM_ASGARI_HZ,
         "aralik_us": istek_araligi_us(MAVLINK_DURUM_ASGARI_HZ, carpan)},
        {"ad": MESAJ_GLOBAL_POSITION_INT,
         "id": int(m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT),
         "asgari_hz": MAVLINK_KONUM_ASGARI_HZ,
         "aralik_us": istek_araligi_us(MAVLINK_KONUM_ASGARI_HZ, carpan)},
        {"ad": MESAJ_GPS_RAW_INT,
         "id": int(m.MAVLINK_MSG_ID_GPS_RAW_INT),
         "asgari_hz": MAVLINK_KONUM_ASGARI_HZ,
         "aralik_us": istek_araligi_us(MAVLINK_KONUM_ASGARI_HZ, carpan)},
    ]


def _pozitif_sonlu(deger, ad):
    if isinstance(deger, bool) or not isinstance(deger, Real):
        raise ValueError(f"{ad} pozitif ve sonlu olmalı")
    d = float(deger)
    if not math.isfinite(d) or d <= 0.0:
        raise ValueError(f"{ad} pozitif ve sonlu olmalı")
    return d


def _kimlik_1_255(deger):
    return (not isinstance(deger, bool) and isinstance(deger, int)
            and 1 <= deger <= 255)


class AkisIstekcisi:
    """MAVLink akış isteğini başta ve periyodik yeniler; sessizliği görünür kılar.

    * ``iste()``: üç akış için MAV_CMD_SET_MESSAGE_INTERVAL gönderir
      (``mav.mav.command_long_send``). Gönderim hatası (OSError) YUTULMAZ:
      sayaç + KIRMIZI log, çağıranın döngüsü sürer. pymavlink ``udp:``
      sunucusu akranı görmeden yazamaz (sessizce düşürür); o durumda istek
      ERTELENİR ve akran görülür görülmez ``bakim()`` gönderir.
    * ``gozle(mesaj)``: beklenen kaynaktan EXTENDED_SYS_STATE görünce "son
      EXTENDED zamanı"nı günceller (salt gözlem; kanıt kararına dokunmaz).
    * ``bakim()``: son EXTENDED'den (hiç yoksa ilk istekten) bu yana
      ``sessizlik_tavani_s`` aşıldıysa KIRMIZI log + anında yeniden istek
      (yalnız duruma girerken; her turda spam yok); ``istek_araligi_s``
      dolduysa periyodik yenileme.

    ``saat`` enjekte edilebilir; yalnız bu sınıfın zamanlaması içindir.
    """

    def __init__(self, mav, *, beklenen_sysid=None, saat=time.monotonic,
                 istek_araligi_s=MAVLINK_AKIS_ISTEK_ARALIGI_S,
                 sessizlik_tavani_s=MAVLINK_AKIS_SESSIZLIK_TAVANI_S,
                 hiz_carpani=MAVLINK_AKIS_ISTEK_HIZ_CARPANI):
        if not callable(saat):
            raise TypeError("saat çağrılabilir olmalı")
        if beklenen_sysid is not None and not _kimlik_1_255(beklenen_sysid):
            raise ValueError("beklenen_sysid 1..255 tamsayı olmalı")
        self._mav = mav
        self._beklenen_sysid = beklenen_sysid
        self._saat = saat
        self._istek_araligi_s = _pozitif_sonlu(istek_araligi_s,
                                               "istek_araligi_s")
        self._sessizlik_tavani_s = _pozitif_sonlu(sessizlik_tavani_s,
                                                  "sessizlik_tavani_s")
        self._hiz_carpani = _pozitif_sonlu(hiz_carpani, "hiz_carpani")
        self._tanimlar = None
        self._destek_hatasi = None       # pymavlink/arayüz yok: bir kez loglanır
        self._baslangic = None           # ilk istek zamanı (sessizlik referansı)
        self._son_istek = None
        self._son_extended = None
        self._sessiz = False             # sessizlik alarmı (durum makinesi)
        self._bekleyen = False           # akran görülmediği için ertelendi
        self.sayac = {"tur": 0, "gonderilen": 0, "gonderim_hatasi": 0,
                      "ertelenen": 0, "sessizlik_uyarisi": 0}

    # ── salt-okunur gözlem alanları ─────────────────────────────────────
    @property
    def son_extended_monotonic(self):
        """Beklenen kaynaktan son EXTENDED_SYS_STATE'in ``saat`` damgası."""
        return self._son_extended

    @property
    def sessiz(self):
        return self._sessiz

    @property
    def son_istek_monotonic(self):
        return self._son_istek

    # ── log ─────────────────────────────────────────────────────────────
    def _logla(self, metin, kirmizi=False):
        seviye = "KIRMIZI " if kirmizi else ""
        print(f"{LOG_ONEKI} {seviye}{metin}",
              file=sys.stderr if kirmizi else sys.stdout, flush=True)

    def _tanimlari_al(self):
        if self._tanimlar is None:
            self._tanimlar = akis_istek_tanimlari(self._hiz_carpani)
        return self._tanimlar

    def _hedef(self):
        """(target_system, target_component); bilinmiyorsa 0 (= tümü)."""
        sistem = self._beklenen_sysid
        if sistem is None:
            aday = getattr(self._mav, "target_system", None)
            sistem = aday if _kimlik_1_255(aday) else 0
        bilesen = getattr(self._mav, "target_component", None)
        if not _kimlik_1_255(bilesen):
            bilesen = 0
        return sistem, bilesen

    # ── istek ───────────────────────────────────────────────────────────
    def iste(self):
        """Üç akış için SET_MESSAGE_INTERVAL gönder; True = hepsi gitti."""
        simdi = float(self._saat())
        if self._baslangic is None:
            self._baslangic = simdi
        self._son_istek = simdi
        self.sayac["tur"] += 1
        try:
            tanimlar = self._tanimlari_al()
        except (ImportError, AttributeError) as exc:
            self._destek_yok(f"pymavlink sabitleri okunamadı: {exc}")
            return False
        gonderici = getattr(getattr(self._mav, "mav", None),
                            "command_long_send", None)
        if not callable(gonderici):
            self._destek_yok("MAVLink gönderim arayüzü yok "
                             "(mav.mav.command_long_send)")
            return False
        if not mav_hedefi_biliniyor_mu(self._mav):
            # pymavlink udp sunucusu akranı görmeden yazmaz ve hatayı yutar:
            # "gönderildi" yalanı yerine ertele; akran görülünce bakim() yollar.
            self._bekleyen = True
            self.sayac["ertelenen"] += 1
            self._logla("akış isteği ertelendi: MAVLink akranı henüz "
                        "görülmedi (udp sunucu kipi)")
            return False
        self._bekleyen = False
        hedef_sys, hedef_comp = self._hedef()
        try:
            komut = int(_mavutil_al().mavlink.MAV_CMD_SET_MESSAGE_INTERVAL)
        except (ImportError, AttributeError) as exc:
            self._destek_yok(f"MAV_CMD_SET_MESSAGE_INTERVAL okunamadı: {exc}")
            return False
        hepsi = True
        for t in tanimlar:
            try:
                gonderici(
                    hedef_sys, hedef_comp, komut, MAVLINK_ONAY_ILK_GONDERIM,
                    float(t["id"]), float(t["aralik_us"]),
                    float(MAVLINK_PARAM_KULLANILMIYOR),
                    float(MAVLINK_PARAM_KULLANILMIYOR),
                    float(MAVLINK_PARAM_KULLANILMIYOR),
                    float(MAVLINK_PARAM_KULLANILMIYOR),
                    float(MAVLINK_PARAM_KULLANILMIYOR))
                self.sayac["gonderilen"] += 1
            except OSError as exc:
                self.sayac["gonderim_hatasi"] += 1
                self._logla(f"akış isteği gönderilemedi ({t['ad']}, "
                            f"{type(exc).__name__}: {exc}); döngü sürüyor",
                            kirmizi=True)
                hepsi = False
        return hepsi

    def _destek_yok(self, neden):
        self.sayac["gonderim_hatasi"] += 1
        if self._destek_hatasi != neden:
            self._destek_hatasi = neden
            self._logla(f"akış isteği gönderilemiyor: {neden}", kirmizi=True)

    # ── gözlem ──────────────────────────────────────────────────────────
    def gozle(self, mesaj):
        """`recv_match` çıktısını gör; beklenen kaynaktan EXTENDED ise damgala."""
        if mesaj is None or _mesaj_tipi(mesaj) != MESAJ_EXTENDED_SYS_STATE:
            return False
        kaynak = _mesaj_kaynagi(mesaj)
        if kaynak is None:
            return False
        if self._beklenen_sysid is not None and kaynak != self._beklenen_sysid:
            return False
        simdi = float(self._saat())
        if self._sessiz:
            ref = (self._son_extended if self._son_extended is not None
                   else self._baslangic)
            gecen = (simdi - ref) if ref is not None else float("nan")
            self._sessiz = False
            self._logla(f"EXTENDED_SYS_STATE yeniden akıyor "
                        f"({gecen:.1f} s sessizlikten sonra)")
        self._son_extended = simdi
        return True

    # ── bakım ───────────────────────────────────────────────────────────
    def bakim(self):
        """Sessizlik denetimi + periyodik yenileme. Dönüş: istek gönderildi mi."""
        if self._son_istek is None:
            return self.iste()
        simdi = float(self._saat())
        if self._bekleyen and mav_hedefi_biliniyor_mu(self._mav):
            return self.iste()
        ref = (self._son_extended if self._son_extended is not None
               else self._baslangic)
        sessizlik = simdi - ref
        if not self._sessiz and sessizlik > self._sessizlik_tavani_s:
            self._sessiz = True
            self.sayac["sessizlik_uyarisi"] += 1
            self._logla(f"{SESSIZLIK_UYARISI} (son {sessizlik:.1f} s; "
                        f"tavan {self._sessizlik_tavani_s:g} s)",
                        kirmizi=True)
            return self.iste()
        if simdi - self._son_istek >= self._istek_araligi_s:
            return self.iste()
        return False

    def ozet(self):
        s = self.sayac
        if self._son_extended is None:
            son = "hiç gelmedi"
        else:
            son = f"{float(self._saat()) - self._son_extended:.1f} s önce"
        return (f"akış isteği özeti: tur={s['tur']} gönderilen={s['gonderilen']} "
                f"gonderim_hatasi={s['gonderim_hatasi']} "
                f"ertelenen={s['ertelenen']} "
                f"sessizlik_uyarisi={s['sessizlik_uyarisi']} "
                f"son_EXTENDED={son}")


class AkisGozcusu:
    """`yerde_mi`'ye verilen mav sargısı: okumayı DEĞİŞTİRMEZ, gözler.

    ``recv_match(blocking=True, timeout=T)`` toplam T boyunca bekler ama
    beklemeyi ``AKIS_BAKIM_DILIMI_S`` dilimlerine böler; her dilimde dönen
    mesaj ``istekci.gozle`` ile görülür ve ``istekci.bakim`` koşar. Böylece
    Pixhawk tamamen sessizken bile (hiç mesaj yok) istek yenilenir. Mesaj
    gelince hemen döner; süre dolunca None döner — ``yerde_mi``'nin gördüğü
    sözleşme aynıdır. Diğer öznitelikler (``inis_kaniti_deadline_monotonic``,
    ``target_system``, ``close``) gerçek bağlantıya devredilir.
    """

    def __init__(self, mav, istekci, *, dilim_s=AKIS_BAKIM_DILIMI_S,
                 monotonic=time.monotonic):
        self._mav = mav
        self._istekci = istekci
        self._dilim_s = _pozitif_sonlu(dilim_s, "dilim_s")
        self._monotonic = monotonic

    def __getattr__(self, ad):
        return getattr(self._mav, ad)

    def recv_match(self, condition=None, type=None, blocking=False,
                   timeout=None):
        ek = {} if condition is None else {"condition": condition}
        if not blocking or timeout is None:
            mesaj = self._mav.recv_match(type=type, blocking=blocking,
                                         timeout=timeout, **ek)
            self._istekci.gozle(mesaj)
            self._istekci.bakim()
            return mesaj
        bitis = self._monotonic() + float(timeout)
        while True:
            kalan = bitis - self._monotonic()
            if kalan <= 0.0:
                self._istekci.bakim()
                return None
            mesaj = self._mav.recv_match(
                type=type, blocking=True,
                timeout=min(kalan, self._dilim_s), **ek)
            self._istekci.gozle(mesaj)
            self._istekci.bakim()
            if mesaj is not None:
                return mesaj


def iha_inisini_yayinla(
        peers, heartbeat_until=None, repeat=8, interval=0.25, *, tasiyici=None,
        heartbeat_suresi=None, heartbeat_araligi=IHA_INIS_HEARTBEAT_ARALIGI_S,
        saat=time.monotonic):
    """IHA_LANDED olayını ACK'li yayınla, görev bitene dek heartbeat sürdür.

    Heartbeat iki koşuldan biri sağlanana dek sürer (K6):
      * ``heartbeat_until`` (Event) set edilene dek — simülasyon İKA bitti der;
      * ``heartbeat_suresi`` saniye dolana dek — saha CLI, sözleşmeden.
    İkisi de None ise heartbeat gönderilmez (eski davranış, yalnız test/araç).
    Alıcıdaki ``link_lost`` ancak heartbeat GERÇEKTEN kesilince oluşur.

    ``tasiyici`` verilirse de bu fonksiyon onun yaşam döngüsünü sahiplenir ve
    çıkışta kapatır. Bu, UDP ve saha SerialLink yolunun aynı kanonik gövdeyi
    kullanmasını sağlar.
    """
    if not peers:
        if tasiyici is not None:
            tasiyici.close()
        return True
    link = tasiyici
    if link is None:
        link = UDPLink(bind=("0.0.0.0", 0), timeout=min(0.05, interval))
    sender = IhaSender(link, peers=peers)
    try:
        seq, acked = sender.send_iha_landed(
            repeat=repeat, interval=interval, wait_ack=True)
        beklenen = set(peers)
        aktarim_tam = acked >= beklenen
        if not aktarim_tam:
            print(f"[İHA] IHA_LANDED ACK eksik: seq={seq} "
                  f"beklenen={sorted(beklenen)} gelen={sorted(acked)}")
        else:
            print(f"[İHA] IHA_LANDED yayınlandı: seq={seq} ACK={sorted(acked)}")
        # İKA landed latch'ini açmış olsa bile ikinci bir akran ACK'i kayıp
        # olabilir. Görev sonucunu False tutarken İKA bitene dek canlılığı
        # kesmemek, alıcının link-timeout ile kilitlenmesini önler.
        hb_deadline = None
        if heartbeat_suresi is not None:
            hb_deadline = saat() + max(0.0, float(heartbeat_suresi))
        if heartbeat_until is None and hb_deadline is None:
            return aktarim_tam
        durdur = (heartbeat_until if heartbeat_until is not None
                  else threading.Event())
        araligi = max(0.0, float(heartbeat_araligi))
        while True:
            if hb_deadline is not None:
                kalan = hb_deadline - saat()
                if kalan <= 0.0:
                    break
                bekle = min(araligi, kalan)
            else:
                bekle = araligi
            if durdur.wait(bekle):
                break
            sender.send_heartbeat("iha")
        return aktarim_tam
    finally:
        link.close()


def _arg_parser():
    parser = argparse.ArgumentParser(
        description="Pixhawk kanıtlı saha IHA_LANDED yayıncısı")
    parser.add_argument(
        "--mavlink", required=True,
        help="Pixhawk MAVLink bağlantısı — ÇOĞULLAYICI UCU "
             "(ör. udp:127.0.0.1:14551); seri Pixhawk tek sahiplidir, "
             "doğrudan /dev/ttyACM0 VERİLMEZ")
    # FDR/ACIK_KALEMLER §4b #23: kilit `iha_komut_alici` ile AYNI mekanizma —
    # bayrak adı, yardım ve red metni `inis_kaniti`den okunur (CONTRACTS §7.4).
    seri_pixhawk_bayragini_ekle(parser)
    parser.add_argument(
        "--kanit-timeout", required=True, type=float,
        help="Kalkış kanıtından sonra inişi bekleme süresi (saniye); "
             "kalkış öncesi bekleme süresizdir")
    parser.add_argument(
        "--sysid", type=int, default=None,
        help="Beklenen MAVLink sistem kimliği (D-389: verilirse iniş kanıtı "
             "pini beyana dayanır; ArduPilot varsayılanı 1). Verilmezse ilk "
             "görülen kaynak pinlenir.")
    parser.add_argument("--serial", help="SiK telsiz seri portu")
    parser.add_argument("--baud", type=int,
                        help="SiK seri baud değeri (verilmezse link varsayılanı)")
    parser.add_argument("--ika", help="IKA adresi host:port (UDP)")
    parser.add_argument("--yks", help="YKS adresi host:port (UDP)")
    parser.add_argument(
        "--heartbeat-sure", type=float, default=IHA_INIS_HEARTBEAT_SURESI_S,
        help="iniş sonrası heartbeat süresi (sn); İKA sürüşü boyunca link "
             "canlı kalır (K6). Varsayılan şartname §6.2 İKA görev süresi "
             f"({IHA_INIS_HEARTBEAT_SURESI_S:.0f})")
    parser.add_argument(
        "--heartbeat-aralik", type=float, default=IHA_INIS_HEARTBEAT_ARALIGI_S,
        help="heartbeat aralığı (sn); ika_receiver hb_timeout'undan küçük "
             f"olmalı (varsayılan {IHA_INIS_HEARTBEAT_ARALIGI_S})")
    return parser


def _mavlink_kapat(mav):
    kapat = getattr(mav, "close", None)
    if callable(kapat):
        try:
            kapat()
        except (OSError, RuntimeError):
            pass


def kalkisi_bekle(mav, *, beklenen_sysid=None):
    """Yerde açılışı iniş sayma; aynı kaynaktan uçuş kanıtını süresiz bekle.

    AkisGozcusu kısa okuma dilimlerinde akış isteklerini yeniler. İlk geçerli
    EXTENDED kaynağı (veya --sysid) hem kalkış hem sonraki iniş için pinlenir.
    ARM tek başına kalkış değildir; eşik uydurmadan MAVLink IN_AIR/TAKEOFF
    durumları kullanılır. Süreç uçuş sırasında açılırsa IN_AIR da yeterlidir.
    """
    m = _mavutil_al().mavlink
    ucus_durumlari = (m.MAV_LANDED_STATE_IN_AIR, m.MAV_LANDED_STATE_TAKEOFF)
    mesru_durumlar = (m.MAV_LANDED_STATE_ON_GROUND,
                     m.MAV_LANDED_STATE_LANDING) + ucus_durumlari
    kaynak_pini = beklenen_sysid
    okuma_hatasi = False
    print(f"{LOG_ONEKI} Kalkış kanıtı bekleniyor; iniş süresi henüz başlamadı.",
          flush=True)
    while True:
        try:
            mesaj = mav.recv_match(type=MESAJ_EXTENDED_SYS_STATE,
                                   blocking=True, timeout=AKIS_BAKIM_DILIMI_S)
        except OSError as exc:
            if not okuma_hatasi:
                print(f"{LOG_ONEKI} Kalkış beklerken MAVLink okuma hatası: {exc}",
                      file=sys.stderr, flush=True)
            okuma_hatasi = True
            time.sleep(AKIS_BAKIM_DILIMI_S)
            continue
        okuma_hatasi = False
        if mesaj is None or _mesaj_tipi(mesaj) != MESAJ_EXTENDED_SYS_STATE:
            continue
        kaynak = _mesaj_kaynagi(mesaj)
        durum = getattr(mesaj, "landed_state", None)
        if (not _kimlik_1_255(kaynak) or type(durum) is not int
                or durum not in mesru_durumlar):
            continue
        if kaynak_pini is None:
            kaynak_pini = kaynak
        if kaynak != kaynak_pini or durum not in ucus_durumlari:
            continue
        print(f"{LOG_ONEKI} Kalkış kanıtı doğrulandı: sysid={kaynak_pini}; "
              "iniş beklemesi başlıyor.", flush=True)
        return kaynak_pini


def main(argv=None, *, saat=time.monotonic):
    """CLI gövdesi. ``saat`` yalnız akış isteği zamanlayıcısına (T207) gider;
    kanıt son tarihi `inis_kaniti` ile aynı gerçek monotonic saati kullanır."""
    parser = _arg_parser()
    args = parser.parse_args(argv)
    # CONTRACTS §7.4 (D-403): seri Pixhawk TEK SAHİPLİDİR. Denetim bağlantı
    # açılmadan ÖNCE koşar; yoksa süreç portu bir an için kapıp öbür iki
    # tüketicinin akışını çalabilir (fail-closed, argparse çıkış kodu 2).
    seri_pixhawk_kilidini_uygula(parser, args.mavlink,
                                 args.seri_pixhawk_bilerek)
    if args.serial and (args.ika or args.yks):
        parser.error("--serial ile --ika/--yks birlikte kullanılamaz")
    if not args.serial and not (args.ika or args.yks):
        parser.error("--serial veya --ika/--yks hedeflerinden biri gerekli")
    if args.baud is not None and not args.serial:
        parser.error("--baud yalnız --serial ile kullanılabilir")
    if args.baud is not None and args.baud <= 0:
        parser.error("--baud pozitif olmalı")
    if not math.isfinite(args.kanit_timeout) or args.kanit_timeout <= 0:
        parser.error("--kanit-timeout sonlu ve pozitif olmalı")
    if args.sysid is not None and not 1 <= args.sysid <= 255:
        parser.error("--sysid 1..255 aralığında olmalı")
    if not math.isfinite(args.heartbeat_sure) or args.heartbeat_sure < 0:
        parser.error("--heartbeat-sure sonlu ve negatif olmayan olmalı")
    if (not math.isfinite(args.heartbeat_aralik)
            or args.heartbeat_aralik <= 0):
        parser.error("--heartbeat-aralik sonlu ve pozitif olmalı")

    peers = None
    if not args.serial:
        try:
            peers = {}
            if args.ika:
                peers["ika"] = udp_adres(args.ika)
            if args.yks:
                peers["yks"] = udp_adres(args.yks)
        except (TypeError, ValueError) as exc:
            print(f"[İHA] HATA: UDP hedefi geçersiz: {exc}", file=sys.stderr)
            return 4

    try:
        mav = mavlink_baglantisi_ac(args.mavlink)
    except (ImportError, ConnectionError) as exc:
        print(f"[İHA] HATA: {exc}", file=sys.stderr)
        return 2

    try:
        # Kalkış beklenirken de akış istekleri ve sessizlik bakımı sürer.
        istekci = AkisIstekcisi(mav, beklenen_sysid=args.sysid, saat=saat)
        istekci.iste()
        gozcu = AkisGozcusu(mav, istekci)
        try:
            kanit_sysid = kalkisi_bekle(gozcu, beklenen_sysid=args.sysid)
            son_tarih = time.monotonic() + args.kanit_timeout
            mav.inis_kaniti_deadline_monotonic = son_tarih
        except (ImportError, AttributeError, TypeError, ValueError) as exc:
            print(f"[İHA] HATA: Kalkış/iniş beklemesi kurulamadı: {exc}",
                  file=sys.stderr)
            return 2
        # T207 (D-406 A): EXTENDED_SYS_STATE yalniz istekle akar ve istek
        # Pixhawk reboot'unda silinir. Basta iste; gozcu, yerde_mi'nin okuma
        # beklemesi icinde periyodik yenilemeyi ve sessizlik denetimini kosar.
        # D-389 (A1): yerde_mi son tarihe kadar bekler (A2); yine de erken
        # False donerse (gecici istisna / beklenen kaynaktan bozuk paket)
        # sure kaldigi surece YENIDEN denenir — tek atis gorevi olduremez.
        yerde = False
        while not yerde and time.monotonic() < son_tarih:
            istekci.bakim()
            yerde = yerde_mi(gozcu, beklenen_sysid=kanit_sysid)
            if not yerde:
                time.sleep(0.05)   # bozuk paket firtinasinda sicak dongu olmasin
        print(f"{LOG_ONEKI} {istekci.ozet()}", flush=True)
        if not yerde:
            print(f"{LOG_ONEKI} İniş kanıtı doğrulanmadı; IHA_LANDED "
                  f"yayınlanmadı. ({istekci.ozet()})", file=sys.stderr)
            return 3

        if args.serial:
            try:
                link = (SerialLink(args.serial, args.baud)
                        if args.baud is not None else SerialLink(args.serial))
            except (ImportError, OSError, ValueError) as exc:
                print(f"[İHA] HATA: SiK hattı açılamadı: {exc}", file=sys.stderr)
                return 4
            peers = {"ika": None}
            basarili = iha_inisini_yayinla(
                peers, tasiyici=link,
                heartbeat_suresi=args.heartbeat_sure,
                heartbeat_araligi=args.heartbeat_aralik)
        else:
            basarili = iha_inisini_yayinla(
                peers,
                heartbeat_suresi=args.heartbeat_sure,
                heartbeat_araligi=args.heartbeat_aralik)
        return 0 if basarili else 5
    finally:
        _mavlink_kapat(mav)


if __name__ == "__main__":
    raise SystemExit(main())
