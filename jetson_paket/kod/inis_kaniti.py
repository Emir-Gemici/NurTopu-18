"""NEDEN: IHA_LANDED yalnız Pixhawk'ın yerde durumunu ve düşük bağıl
irtifayı art arda doğruladığı zaman üretilmelidir. Tek bir telemetri alanı,
operatör düğmesi veya okuma hatası sürüş izni latch'ini açamaz.

``GLOBAL_POSITION_INT.relative_alt`` yerden yükseklik değil, home noktasına
göre bağıl irtifadır. Bu nedenle yalnız ek makullük kapısıdır; birincil kanıt
``EXTENDED_SYS_STATE.landed_state`` alanıdır.
"""

import importlib
import math
import threading
import time
from numbers import Real


MESAJ_EXTENDED_SYS_STATE = "EXTENDED_SYS_STATE"
MESAJ_GLOBAL_POSITION_INT = "GLOBAL_POSITION_INT"
MESAJ_GPS_RAW_INT = "GPS_RAW_INT"
MESAJ_HEARTBEAT = "HEARTBEAT"
MAVLINK_INIS_MESAJLARI = [MESAJ_EXTENDED_SYS_STATE,
                          MESAJ_GLOBAL_POSITION_INT]
MAVLINK_TELEMETRI_MESAJLARI = [MESAJ_GLOBAL_POSITION_INT,
                               MESAJ_GPS_RAW_INT,
                               MESAJ_HEARTBEAT]
MILIMETRE_BIR_METRE = 1000.0
MAVLINK_TIME_BOOT_MS_AZAMI = (1 << 32) - 1
MAVLINK_TIME_USEC_AZAMI = (1 << 64) - 1
MAVLINK_UINT8_AZAMI = (1 << 8) - 1
# MAVLink GPS_RAW_INT: 255, uydu sayisinin bilinmedigini belirtir.
GPS_UYDU_BILINMIYOR = MAVLINK_UINT8_AZAMI


_MAV_SAHIPLIK_KILIDI = threading.Lock()
_MAV_SAHIPLERI = {}


def _mav_sahiplen(mav, sahip):
    """Bir bağlantının tek telemetri tüketicisi olmasını atomik olarak sağla."""
    anahtar = id(mav)
    with _MAV_SAHIPLIK_KILIDI:
        mevcut = _MAV_SAHIPLERI.get(anahtar)
        if mevcut is not None and mevcut is not sahip:
            return False
        _MAV_SAHIPLERI[anahtar] = sahip
        return True


def _mav_sahipligini_birak(mav, sahip):
    anahtar = id(mav)
    with _MAV_SAHIPLIK_KILIDI:
        if _MAV_SAHIPLERI.get(anahtar) is sahip:
            del _MAV_SAHIPLERI[anahtar]


def _mavutil_al():
    """pymavlink'i tembel yükle; eksik saha bağımlılığını görünür kıl."""
    try:
        return importlib.import_module("pymavlink.mavutil")
    except (ImportError, ModuleNotFoundError) as exc:
        raise ImportError(
            "pymavlink gerekli; Pixhawk iniş kanıtı okunamadı"
        ) from exc


def mavlink_baglantisi_ac(adres):
    """Verilen pymavlink bağlantı dizesini aç; bağımlılık hatasını gizleme."""
    mavutil = _mavutil_al()
    try:
        return mavutil.mavlink_connection(adres)
    except Exception as exc:
        raise ConnectionError(
            f"MAVLink bağlantısı açılamadı: {adres!r}"
        ) from exc


def _mesaj_tipi(mesaj):
    try:
        tip_al = getattr(mesaj, "get_type")
        tip = tip_al()
    except Exception:
        return None
    return tip if isinstance(tip, str) else None


def _mesaj_kaynagi(mesaj):
    """MAVLink sistem kimliğini al; adsız/rezerv kaynakları reddet."""
    try:
        kaynak = mesaj.get_srcSystem()
    except Exception:
        return None
    if isinstance(kaynak, bool) or not isinstance(kaynak, int) or kaynak <= 0:
        return None
    return kaynak


def _bagil_irtifa_m(mesaj):
    """GLOBAL_POSITION_INT bağıl irtifasını doğrulayıp metreye çevir."""
    try:
        bagil_mm = getattr(mesaj, "relative_alt", None)
    except Exception:
        return None
    if isinstance(bagil_mm, bool) or not isinstance(bagil_mm, Real):
        return None
    try:
        bagil_mm = float(bagil_mm)
    except (OverflowError, TypeError, ValueError):
        return None
    if not math.isfinite(bagil_mm):
        return None
    return bagil_mm / MILIMETRE_BIR_METRE


def _konum_derece(mesaj):
    """GLOBAL_POSITION_INT `lat`/`lon` (1e7 derece) -> (lat_d, lon_d) ya da None.

    T162 (ON_KAYIT SS28): sartname SS6.2/SS6.4 ALAN IHLALI denetimi IHA'nin
    konumunu ister; YKS bunu heartbeat'teki x,y'den okuyor ama URETIMDE o alani
    ureten hicbir yol yoktu — kapi sahada OLUYDU. Konum, IKINCI bir telemetri
    yolu acilmadan AYNI mesajdan alinir.

    🔴 BU FONKSIYON INIS KANITINI ETKILEMEZ: lat/lon bozuk olsa bile
    `_bagil_irtifa_m` yolu ve surus izni latch'i DEGISMEZ (bkz. `_mesaj_isle`).
    FAIL-CLOSED: gecersiz/bool/NaN/sonsuz ya da bant disi deger -> None.
    """
    try:
        lat_e7 = getattr(mesaj, "lat", None)
        lon_e7 = getattr(mesaj, "lon", None)
    except Exception:
        return None
    cikti = []
    for ham, sinir in ((lat_e7, 90.0), (lon_e7, 180.0)):
        if isinstance(ham, bool) or not isinstance(ham, Real):
            return None
        try:
            d = float(ham) / 1e7
        except (OverflowError, TypeError, ValueError):
            return None
        if not math.isfinite(d) or abs(d) > sinir:
            return None
        cikti.append(d)
    return (cikti[0], cikti[1])


def _uzak_zaman_ms(mesaj):
    """MAVLink boot zamanını sıra denetimi için doğrula.

    Bu alan tazelik saati değildir: farklı araç saatleri ve yeniden başlatmalar
    nedeniyle yaş daima yerel ``monotonic`` saatten hesaplanır.
    """
    try:
        uzak_ms = getattr(mesaj, "time_boot_ms", None)
    except Exception:
        return None
    if (isinstance(uzak_ms, bool) or not isinstance(uzak_ms, int)
            or uzak_ms < 0 or uzak_ms > MAVLINK_TIME_BOOT_MS_AZAMI):
        return None
    return uzak_ms


def _gps_uzak_zaman_us(mesaj):
    """GPS_RAW_INT zaman alanını yalnız sıra/tekrar denetimi için doğrula."""
    try:
        uzak_us = getattr(mesaj, "time_usec", None)
    except Exception:
        return None
    if (isinstance(uzak_us, bool) or not isinstance(uzak_us, int)
            or uzak_us < 0 or uzak_us > MAVLINK_TIME_USEC_AZAMI):
        return None
    return uzak_us


def _gps_raw_alanlari(mesaj):
    """GPS fix ve uydu sayısını doğrula; bilinmeyen uyduyu ``None`` yap."""
    try:
        fix = getattr(mesaj, "fix_type", None)
        uydu = getattr(mesaj, "satellites_visible", None)
    except Exception:
        return None
    if (isinstance(fix, bool) or not isinstance(fix, int)
            or not 0 <= fix <= MAVLINK_UINT8_AZAMI):
        return None
    if (isinstance(uydu, bool) or not isinstance(uydu, int)
            or not 0 <= uydu <= MAVLINK_UINT8_AZAMI):
        uydu = None
    elif uydu == GPS_UYDU_BILINMIYOR:
        uydu = None
    return fix, uydu


def _armed_durumu(mesaj):
    """Pixhawk HEARTBEAT ``base_mode`` bitinden ARM durumunu doğrula."""
    try:
        base_mode = getattr(mesaj, "base_mode", None)
    except Exception:
        return None
    if (isinstance(base_mode, bool) or not isinstance(base_mode, int)
            or not 0 <= base_mode <= MAVLINK_UINT8_AZAMI):
        return None
    try:
        bayrak = int(_mavutil_al().mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
    except (AttributeError, ImportError, TypeError, ValueError):
        return None
    if bayrak <= 0:
        return None
    return bool(base_mode & bayrak)


class BagilIrtifaOkuyucu:
    """Kare ölçeği için taze ``relative_alt`` örneğini fail-closed sun.

    ``oku`` yalnız belirtilen MAVLink sisteminden gelen, boot zamanı ilerleyen
    örnekleri kabul eder. Aynı/eski ``time_boot_ms`` bir önceki örneğin yerel
    geliş zamanını yenileyemez. Son geçerli örnek yalnız ``tazelik_s`` içinde
    kullanılabilir; bağlantı/alan/kaynak hatası cache'i geçersiz kılar.

    Üretimde ``baslat`` tek arka-plan tüketicisini açar; mesaj yerel kuyruğa
    geldiğinde değil, ``recv_match`` tarafından teslim edildiği anda monotonic
    damga alır. ``irtifa_m`` yalnız bu snapshot'ı okur ve bağlantıyı tüketmez.
    Thread kullanılmayan deterministik testlerde ``oku`` tek seferlik nonblocking
    tüketim yapabilir.

    ``beklenen_sysid`` verilmezse bağlantının pozitif ``target_system`` alanı
    zorunludur. Kaynağı ilk pakete göre seçmek, yabancı bir aracın ilk mesajını
    sessizce otorite yapacağı için kabul edilmez.
    """

    def __init__(self, mav, tazelik_s, beklenen_sysid=None, *,
                 durum_tazelik_s=None, monotonic=time.monotonic):
        if isinstance(tazelik_s, bool) or not isinstance(tazelik_s, Real):
            raise ValueError("tazelik_s pozitif ve sonlu olmalıdır")
        try:
            tazelik = float(tazelik_s)
        except (OverflowError, TypeError, ValueError) as exc:
            raise ValueError("tazelik_s pozitif ve sonlu olmalıdır") from exc
        if not math.isfinite(tazelik) or tazelik <= 0.0:
            raise ValueError("tazelik_s pozitif ve sonlu olmalıdır")
        if durum_tazelik_s is None:
            durum_tazelik = None
        else:
            if (isinstance(durum_tazelik_s, bool)
                    or not isinstance(durum_tazelik_s, Real)):
                raise ValueError(
                    "durum_tazelik_s pozitif ve sonlu olmalıdır")
            try:
                durum_tazelik = float(durum_tazelik_s)
            except (OverflowError, TypeError, ValueError) as exc:
                raise ValueError(
                    "durum_tazelik_s pozitif ve sonlu olmalıdır") from exc
            if not math.isfinite(durum_tazelik) or durum_tazelik <= 0.0:
                raise ValueError(
                    "durum_tazelik_s pozitif ve sonlu olmalıdır")
        if not callable(monotonic):
            raise TypeError("monotonic çağrılabilir olmalıdır")

        if beklenen_sysid is None:
            try:
                baglanti_sysid = getattr(mav, "target_system", None)
            except Exception:
                baglanti_sysid = None
            if (not isinstance(baglanti_sysid, bool)
                    and isinstance(baglanti_sysid, int)
                    and 1 <= baglanti_sysid <= 255):
                beklenen_sysid = baglanti_sysid
            else:
                raise ValueError(
                    "beklenen_sysid veya pozitif mav.target_system gereklidir")
        elif (isinstance(beklenen_sysid, bool)
              or not isinstance(beklenen_sysid, int)
              or not 1 <= beklenen_sysid <= 255):
            raise ValueError("beklenen_sysid 1..255 tamsayı olmalıdır")

        self._mav = mav
        self._tazelik_s = tazelik
        # HEARTBEAT standartta 1 Hz'dir; 0,50 s irtifa eşiği ona uygulanmaz.
        # None, bu bilgi için sözleşme eşiği verilmediğini ve alanın fail-closed
        # biçimde hiç sunulmayacağını ifade eder.
        self._durum_tazelik_s = durum_tazelik
        self._beklenen_sysid = beklenen_sysid
        self._monotonic = monotonic
        self._snapshot_kilidi = threading.Lock()
        self._yasam_kilidi = threading.Lock()
        self._dur_olayi = threading.Event()
        self._poller = None
        self._son_uzak_ms = None
        self._son_irtifa_m = None
        self._son_telemetri_alt_m = None
        self._son_konum = None            # T162: (lat, lon) — irtifadan BAGIMSIZ
        self._son_gelis_monotonic = None
        self._son_gps_uzak_us = None
        self._son_gps_fix = None
        self._son_uydu = None
        self._son_gps_gelis_monotonic = None
        self._son_armed = None
        self._son_heartbeat_gelis_monotonic = None

    def _gecersiz_kil(self):
        with self._snapshot_kilidi:
            self._son_irtifa_m = None
            self._son_telemetri_alt_m = None
            self._son_konum = None
            self._son_gelis_monotonic = None
            self._son_gps_fix = None
            self._son_uydu = None
            self._son_gps_gelis_monotonic = None
            self._son_armed = None
            self._son_heartbeat_gelis_monotonic = None

    def _konumu_gecersiz_kil(self):
        with self._snapshot_kilidi:
            self._son_irtifa_m = None
            self._son_telemetri_alt_m = None
            self._son_konum = None
            self._son_gelis_monotonic = None

    def _gps_gecersiz_kil(self):
        with self._snapshot_kilidi:
            self._son_gps_fix = None
            self._son_uydu = None
            self._son_gps_gelis_monotonic = None

    def _heartbeat_gecersiz_kil(self):
        with self._snapshot_kilidi:
            self._son_armed = None
            self._son_heartbeat_gelis_monotonic = None

    def _mesaj_isle(self, mesaj, gelis):
        tip = _mesaj_tipi(mesaj)
        if tip not in MAVLINK_TELEMETRI_MESAJLARI:
            self._gecersiz_kil()
            return False

        kaynak = _mesaj_kaynagi(mesaj)
        if kaynak != self._beklenen_sysid:
            # D-389 (B1): yabanci/adsiz kaynagin paketi bizim aracimiz
            # hakkinda KANIT TASIMAZ — cache'e dokunmaz, atlanir. Eski
            # davranis (gecersiz kil) ucuncu bir tarafa bizi kor etme yetkisi
            # veriyordu (D-387: erisilebilirlik 0/193). Sizinti kapisi
            # degismedi: deger ASLA yabanci kaynaktan yazilmaz.
            return False
        if not math.isfinite(gelis):
            self._gecersiz_kil()
            return False

        if tip == MESAJ_GLOBAL_POSITION_INT:
            uzak_ms = _uzak_zaman_ms(mesaj)
            irtifa_m = _bagil_irtifa_m(mesaj)
            konum = _konum_derece(mesaj)
            if uzak_ms is None or (irtifa_m is None and konum is None):
                # BEKLENEN kaynaktan bozuk alan: kendi hattimizdaki bozulma
                # gercek kotu haberdir — yalniz bu akış temizlenir.
                self._konumu_gecersiz_kil()
                return False

            with self._snapshot_kilidi:
                # Tekrarlanan veya sıra dışı paket eski örneğin yaşını yenilemez.
                if (self._son_uzak_ms is not None
                        and uzak_ms <= self._son_uzak_ms):
                    return False
                self._son_uzak_ms = uzak_ms
                # relative_alt=0 yerde geçerli bir YKİ telemetrisidir, fakat
                # pozitif irtifa gerektiren ölçek kaynağı değildir. İki anlamı
                # tek alanda birleştirip GPS'i yerde kör bırakma.
                self._son_telemetri_alt_m = irtifa_m
                self._son_irtifa_m = (
                    irtifa_m if irtifa_m is not None and irtifa_m > 0.0
                    else None)
                # Konum EK bilgidir. Gecersizse `None`; irtifa ve inis kaniti
                # bundan ETKILENMEZ.
                self._son_konum = konum
                self._son_gelis_monotonic = gelis
            return True

        if tip == MESAJ_GPS_RAW_INT:
            uzak_us = _gps_uzak_zaman_us(mesaj)
            alanlar = _gps_raw_alanlari(mesaj)
            if uzak_us is None or alanlar is None:
                self._gps_gecersiz_kil()
                return False
            with self._snapshot_kilidi:
                if (self._son_gps_uzak_us is not None
                        and uzak_us <= self._son_gps_uzak_us):
                    return False
                self._son_gps_uzak_us = uzak_us
                self._son_gps_fix, self._son_uydu = alanlar
                self._son_gps_gelis_monotonic = gelis
            return True

        armed = _armed_durumu(mesaj)
        if armed is None:
            self._heartbeat_gecersiz_kil()
            return False
        with self._snapshot_kilidi:
            self._son_armed = armed
            self._son_heartbeat_gelis_monotonic = gelis
        return True

    def _gelis_zamani(self):
        try:
            gelis = float(self._monotonic())
        except (OverflowError, TypeError, ValueError):
            return None
        return gelis if math.isfinite(gelis) else None

    def _arka_plan_dongusu(self):
        try:
            while not self._dur_olayi.is_set():
                try:
                    mesaj = self._mav.recv_match(
                        type=MAVLINK_TELEMETRI_MESAJLARI,
                        blocking=True,
                        timeout=self._tazelik_s,
                    )
                except Exception:
                    self._gecersiz_kil()
                    return
                if mesaj is None:
                    continue
                # Damga recv_match tesliminin hemen ardından, doğrulamadan önce.
                gelis = self._gelis_zamani()
                if gelis is None:
                    self._gecersiz_kil()
                    return
                self._mesaj_isle(mesaj, gelis)
        finally:
            _mav_sahipligini_birak(self._mav, self)

    def baslat(self):
        """Tek sahipli production poller'ını başlat; çakışmada False dön."""
        with self._yasam_kilidi:
            if self._poller is not None and self._poller.is_alive():
                return True
            if not _mav_sahiplen(self._mav, self):
                return False
            self._dur_olayi.clear()
            self._poller = threading.Thread(
                target=self._arka_plan_dongusu,
                name="navitas-bagil-irtifa",
                daemon=True,
            )
            try:
                self._poller.start()
            except Exception:
                self._poller = None
                _mav_sahipligini_birak(self._mav, self)
                return False
            return True

    def durdur(self):
        """Poller'ı durdur ve bağlantı sahipliğinin bırakıldığını doğrula."""
        with self._yasam_kilidi:
            poller = self._poller
            if poller is None:
                self._dur_olayi.set()
                self._gecersiz_kil()
                return True
            self._dur_olayi.set()
        poller.join(timeout=self._tazelik_s * 2.0)
        if poller.is_alive():
            self._gecersiz_kil()
            return False
        with self._yasam_kilidi:
            if self._poller is poller:
                self._poller = None
        self._gecersiz_kil()
        return True

    def oku(self):
        """Thread kapalı test/manual kullanımda akışı anlık tüket."""
        with self._yasam_kilidi:
            if self._poller is not None and self._poller.is_alive():
                return self.irtifa_m()
        if not _mav_sahiplen(self._mav, self):
            return None
        try:
            while True:
                try:
                    mesaj = self._mav.recv_match(
                        type=MESAJ_GLOBAL_POSITION_INT,
                        blocking=False,
                    )
                except Exception:
                    self._gecersiz_kil()
                    return None
                if mesaj is None:
                    break
                gelis = self._gelis_zamani()
                if gelis is None:
                    self._gecersiz_kil()
                    return None
                self._mesaj_isle(mesaj, gelis)
        finally:
            _mav_sahipligini_birak(self._mav, self)
        return self.irtifa_m()

    def telemetri_oku(self):
        """Thread kapalı tanı/test kullanımında üç akışı tek tüketiciden çek."""
        with self._yasam_kilidi:
            if self._poller is not None and self._poller.is_alive():
                return self.telemetri_snapshot()
        if not _mav_sahiplen(self._mav, self):
            return {}
        try:
            while True:
                try:
                    mesaj = self._mav.recv_match(
                        type=MAVLINK_TELEMETRI_MESAJLARI,
                        blocking=False,
                    )
                except Exception:
                    self._gecersiz_kil()
                    return {}
                if mesaj is None:
                    break
                gelis = self._gelis_zamani()
                if gelis is None:
                    self._gecersiz_kil()
                    return {}
                self._mesaj_isle(mesaj, gelis)
        finally:
            _mav_sahipligini_birak(self._mav, self)
        return self.telemetri_snapshot()

    @staticmethod
    def _taze_mi(simdi, gelis, tavan):
        if gelis is None or tavan is None:
            return False
        yas = simdi - gelis
        return math.isfinite(yas) and 0.0 <= yas < tavan

    def telemetri_snapshot(self):
        """Taze telemetriyi tek kilit altında kopyala; bayat alanı dışarı verme.

        Dönüş alanları: ``lat``, ``lon``, ``alt`` (GLOBAL_POSITION_INT),
        ``gps_fix``/``uydu`` (GPS_RAW_INT) ve ``armed`` (HEARTBEAT). Her akışın
        yaşı kendi son geliş damgasından ölçülür. Eksik, bozuk veya bayat alan
        sözlükte hiç yer almaz; son bilinen değer tekrar kullanılmaz.
        """
        try:
            simdi = float(self._monotonic())
        except (OverflowError, TypeError, ValueError):
            self._gecersiz_kil()
            return {}
        if not math.isfinite(simdi):
            self._gecersiz_kil()
            return {}
        with self._snapshot_kilidi:
            if self._dur_olayi.is_set():
                self._son_irtifa_m = None
                self._son_telemetri_alt_m = None
                self._son_konum = None
                self._son_gelis_monotonic = None
                self._son_gps_fix = None
                self._son_uydu = None
                self._son_gps_gelis_monotonic = None
                self._son_armed = None
                self._son_heartbeat_gelis_monotonic = None
                return {}

            cikti = {}
            if self._taze_mi(
                    simdi, self._son_gelis_monotonic, self._tazelik_s):
                if self._son_telemetri_alt_m is not None:
                    cikti["alt"] = self._son_telemetri_alt_m
                if self._son_konum is not None:
                    cikti["lat"], cikti["lon"] = self._son_konum
            else:
                self._son_irtifa_m = None
                self._son_telemetri_alt_m = None
                self._son_konum = None
                self._son_gelis_monotonic = None

            if self._taze_mi(
                    simdi, self._son_gps_gelis_monotonic, self._tazelik_s):
                if self._son_gps_fix is not None:
                    cikti["gps_fix"] = self._son_gps_fix
                if self._son_uydu is not None:
                    cikti["uydu"] = self._son_uydu
            else:
                self._son_gps_fix = None
                self._son_uydu = None
                self._son_gps_gelis_monotonic = None

            if self._taze_mi(simdi, self._son_heartbeat_gelis_monotonic,
                             self._durum_tazelik_s):
                if self._son_armed is not None:
                    cikti["armed"] = self._son_armed
            else:
                self._son_armed = None
                self._son_heartbeat_gelis_monotonic = None
            return cikti

    def irtifa_m(self):
        """Bağlantıya dokunmadan taze snapshot'ı döndür; bayatta cache'i sil."""
        self.telemetri_snapshot()
        with self._snapshot_kilidi:
            return self._son_irtifa_m

    def konum_derece(self):
        """Taze ``(lat, lon)`` ya da ``None`` (T162 · ON_KAYIT SS28).

        🔴 TAZELIK KURALI KOPYALANMAZ: once `irtifa_m()` cagrilir; o metot
        bayat ornegi zaten temizler ve `None` doner. Yani konumun tazelik
        sozlesmesi irtifanınkiyle TANIM GEREGI aynidir — ikisi ayrisamaz.
        Konum gecersizse (lat/lon bozuk) irtifa yine gelir, yalniz burasi
        `None` doner: inis kaniti yolu ETKILENMEZ.
        """
        snapshot = self.telemetri_snapshot()
        if "lat" not in snapshot or "lon" not in snapshot:
            return None
        return snapshot["lat"], snapshot["lon"]


def yerde_mi(mav, ardisik=3, tavan_m=1.0, beklenen_sysid=None) -> bool:
    """Bağlantıyı tek sahiplenerek iniş kanıtını doğrula."""
    sahip = object()
    if not _mav_sahiplen(mav, sahip):
        return False
    try:
        return _yerde_mi_sahipli(mav, ardisik=ardisik, tavan_m=tavan_m,
                                 beklenen_sysid=beklenen_sysid)
    finally:
        _mav_sahipligini_birak(mav, sahip)


def _yerde_mi_sahipli(mav, ardisik=3, tavan_m=1.0,
                      beklenen_sysid=None) -> bool:
    """Pixhawk yerde + düşük bağıl irtifa kanıtını art arda doğrula.

    Her ON_GROUND mesajı ancak ardından gelen ilk taze
    GLOBAL_POSITION_INT mesajı da eşik altındaysa bir örnek sayılır. İki mesaj
    tipi tek ``recv_match`` akışından okunur; böylece irtifa beklenirken gelen
    IN_AIR durumu filtre tarafından sessizce tüketilemez. Çağıran,
    ``mav.inis_kaniti_deadline_monotonic`` alanına mutlak ve sonlu bir çalışma
    son tarihi koymalıdır; alan yoksa fonksiyon okumadan fail-closed döner.

    D-389 (A2): ON_GROUND dışı meşru ``landed_state`` artık terminal DEĞİLDİR;
    ilerlemeyi sıfırlar ve okuma son tarihe kadar sürer. Böylece alçalma
    sırasında (ya da soket birikintisinde eski IN_AIR varken) başlatılan
    doğrulama, gerçek temastan sonra kanıtı üretebilir. "Art arda ``ardisik``
    temiz çift" şartı ve süre dolunca False (fail-closed) AYNEN korunur;
    beklenen kaynaktan BOZUK alan yine terminaldir.

    D-389 (B1 kardeşi): kaynak pinine uymayan mesaj terminal değil, ATLANIR —
    yabancı bir araç iniş kanıtımızı düşüremez. ``beklenen_sysid`` verilirse
    pin beyana dayanır; verilmezse ilk görülen EXTENDED_SYS_STATE kaynağı
    pinlenir (kalıntı risk: ilk paket yabancıysa pin yanlış olur ve süre
    dolar — sahada ``--sysid`` beyanı önerilir).
    """
    if (isinstance(ardisik, bool) or not isinstance(ardisik, int)
            or ardisik <= 0):
        return False
    if isinstance(tavan_m, bool) or not isinstance(tavan_m, Real):
        return False
    try:
        tavan = float(tavan_m)
    except (OverflowError, TypeError, ValueError):
        return False
    if not math.isfinite(tavan) or tavan <= 0.0:
        return False

    mavutil = _mavutil_al()
    try:
        yerde_degeri = mavutil.mavlink.MAV_LANDED_STATE_ON_GROUND
    except Exception:
        return False
    try:
        deadline = float(mav.inis_kaniti_deadline_monotonic)
    except (AttributeError, OverflowError, TypeError, ValueError):
        return False
    if not math.isfinite(deadline):
        return False

    if beklenen_sysid is not None and (
            isinstance(beklenen_sysid, bool)
            or not isinstance(beklenen_sysid, int)
            or not 1 <= beklenen_sysid <= 255):
        return False

    dogrulanan = 0
    irtifa_bekleniyor = False
    kanit_kaynagi = beklenen_sysid
    while dogrulanan < ardisik:
        kalan = deadline - time.monotonic()
        if kalan <= 0:
            return False
        try:
            mesaj = mav.recv_match(
                type=MAVLINK_INIS_MESAJLARI,
                blocking=True,
                timeout=kalan,
            )
        except Exception:
            return False
        if mesaj is None:
            return False
        if time.monotonic() >= deadline:
            return False

        tip = _mesaj_tipi(mesaj)
        if tip == MESAJ_EXTENDED_SYS_STATE:
            kaynak = _mesaj_kaynagi(mesaj)
            if kaynak is None:
                # Adsiz kaynak kanit degildir; D-389: atla, dusurme.
                continue
            if kanit_kaynagi is None:
                kanit_kaynagi = kaynak
            elif kaynak != kanit_kaynagi:
                # D-389 (B1 kardesi): pine uymayan kaynak ATLANIR — yabanci
                # arac inis kanitimizi teker paketle dusuremez.
                continue
            try:
                durum = getattr(mesaj, "landed_state", None)
            except Exception:
                return False
            if isinstance(durum, bool) or not isinstance(durum, int):
                # Beklenen kaynaktan BOZUK alan: terminal (fail-closed).
                return False
            if durum != yerde_degeri:
                # D-389 (A2): ON_GROUND disi mesru durum terminal degil —
                # ilerleme sifirlanir, okuma son tarihe kadar surer. Boylece
                # alcalma/birikinti sirasinda baslatilan dogrulama gercek
                # temastan sonra kaniti uretebilir.
                dogrulanan = 0
                irtifa_bekleniyor = False
                continue
            irtifa_bekleniyor = True
            continue

        if tip == MESAJ_GLOBAL_POSITION_INT:
            if not irtifa_bekleniyor:
                continue
            kaynak = _mesaj_kaynagi(mesaj)
            if kaynak is None or kaynak != kanit_kaynagi:
                # D-389: pin disi konum kanit degil — cift bozulmaz, atlanir;
                # bizim kaynaktan gelecek ilk konum cifti tamamlar.
                continue
            bagil_irtifa = _bagil_irtifa_m(mesaj)
            if bagil_irtifa is None:
                # Beklenen kaynaktan bozuk irtifa: terminal (fail-closed).
                return False
            if bagil_irtifa >= tavan:
                # Yerde diyen araca yuksek irtifa: celiski — ilerleme sifirla
                # (D-389: terminal degil; inis sonu salinimlarinda toparlanir).
                dogrulanan = 0
                irtifa_bekleniyor = False
                continue
            dogrulanan += 1
            irtifa_bekleniyor = False
            continue

        return False

    return True
