"""NEDEN: IHA_LANDED yalnız Pixhawk'ın yerde durumunu ve düşük bağıl
irtifayı art arda doğruladığı zaman üretilmelidir. Tek bir telemetri alanı,
operatör düğmesi veya okuma hatası sürüş izni latch'ini açamaz.

``GLOBAL_POSITION_INT.relative_alt`` yerden yükseklik değil, home noktasına
göre bağıl irtifadır. Bu nedenle yalnız ek makullük kapısıdır; birincil kanıt
``EXTENDED_SYS_STATE.landed_state`` alanıdır.
"""

import importlib
import math
import time
from numbers import Real


MESAJ_EXTENDED_SYS_STATE = "EXTENDED_SYS_STATE"
MESAJ_GLOBAL_POSITION_INT = "GLOBAL_POSITION_INT"
MAVLINK_INIS_MESAJLARI = [MESAJ_EXTENDED_SYS_STATE,
                          MESAJ_GLOBAL_POSITION_INT]
MILIMETRE_BIR_METRE = 1000.0


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


def yerde_mi(mav, ardisik=3, tavan_m=1.0) -> bool:
    """Pixhawk yerde + düşük bağıl irtifa kanıtını art arda doğrula.

    Her ON_GROUND mesajı ancak ardından gelen ilk taze
    GLOBAL_POSITION_INT mesajı da eşik altındaysa bir örnek sayılır. İki mesaj
    tipi tek ``recv_match`` akışından okunur; böylece irtifa beklenirken gelen
    IN_AIR durumu filtre tarafından sessizce tüketilemez. Çağıran,
    ``mav.inis_kaniti_deadline_monotonic`` alanına mutlak ve sonlu bir çalışma
    son tarihi koymalıdır; alan yoksa fonksiyon okumadan fail-closed döner.
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

    dogrulanan = 0
    irtifa_bekleniyor = False
    kanit_kaynagi = None
    beklenen_irtifa_kaynagi = None
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
                return False
            if kanit_kaynagi is None:
                kanit_kaynagi = kaynak
            elif kaynak != kanit_kaynagi:
                return False
            try:
                durum = getattr(mesaj, "landed_state", None)
            except Exception:
                return False
            if (isinstance(durum, bool) or not isinstance(durum, int)
                    or durum != yerde_degeri):
                return False
            irtifa_bekleniyor = True
            beklenen_irtifa_kaynagi = kaynak
            continue

        if tip == MESAJ_GLOBAL_POSITION_INT:
            if not irtifa_bekleniyor:
                continue
            kaynak = _mesaj_kaynagi(mesaj)
            if (kaynak is None or kaynak != beklenen_irtifa_kaynagi
                    or kaynak != kanit_kaynagi):
                return False
            try:
                bagil_mm = getattr(mesaj, "relative_alt", None)
            except Exception:
                return False
            if (isinstance(bagil_mm, bool) or not isinstance(bagil_mm, Real)
                    or not math.isfinite(float(bagil_mm))):
                return False
            if float(bagil_mm) / MILIMETRE_BIR_METRE >= tavan:
                return False
            dogrulanan += 1
            irtifa_bekleniyor = False
            beklenen_irtifa_kaynagi = None
            continue

        return False

    return True
