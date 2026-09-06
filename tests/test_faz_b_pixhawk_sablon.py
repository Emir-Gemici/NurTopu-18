"""FAZ B · GOREV P — PIXHAWK PARAMETRE + GOREV SABLONU KAPILARI (config/pixhawk/).

NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.6, §1.7, §2.4): Pixhawk 6C 5 Eylul'de ilk
kez yapilandirilacak; Mission Planner'a yuklenecek parametre dosyasi ve gorev plani
repoda durur ama "dosya var" != "dosya dogru". Bu test dosyalari GERCEK bicim
kurallariyla (MP ParamFile.loadParamFile ayirmasi, QGC WPL 110 sutunlari) ayristirir
ve degerleri sozlesme sabitlerine (codes/karar_sozlesmesi.py, comms/iha_komut_alici.py,
scripts/mavlink_dogrula.py) baglar. Mock yok; ArduPilot enum degerleri pymavlink'ten
(MAV_CMD_*, MAV_FRAME_*), ArduPilot parametre tablolarindan gelenler ise kaynak
dosya adiyla burada TEK yerde tanimlidir (madde 16: ciplak sayi dagitilmaz).

Kapilar (adlari ne kilitledigini soyler):
  P1 .param ayrisir: yorum disi her satir AD,DEGER; AD ArduPilot adi (<=16 kr), DEGER sayi,
     mukerrer yok; MP ayirmasiyla (bosluk/virgul/sekme) ayni sonuc
  P2 zorunlu anahtarlar VAR (§1.6 listesi)
  P3 degerler sozlesmeyle tutarli: SYSID_THISMAV == iha_komut_alici.VARSAYILAN_HEDEF_SYSID
     (== mavlink_dogrula.VARSAYILAN_BEKLENEN_SYSID); SR*_POSITION >= MAVLINK_KONUM_ASGARI_HZ;
     SR*_EXTRA3 >= MAVLINK_DURUM_ASGARI_HZ; FENCE_ALT_MAX > SARTNAME_ASGARI_IRTIFA_M ve
     > RTL_ALT; BATT_LOW > BATT_CRT; failsafe/fence/arming acik; MAVLink2 + 57600 iki hatta
  P4 her parametre satirinin USTUNDE NEDEN yorumu var (yorumsuz parametre yok)
  P5 README TEYIT listesi == .param "# TEYIT" isaretli adlar (metin kilidi, kume esitligi)
  P6 .waypoints: "QGC WPL 110" basligi; 8 satir (0..7); indeks sirali; 12 sutun; home
     satiri current=1 frame GLOBAL; TAKEOFF var, irtifa >= SARTNAME_ASGARI_IRTIFA_M ve
     < FENCE_ALT_MAX; koseler 20x20 m kare (SENARYO_BOYUTLARI_M["FDA"], yerel_konum_m);
     LOITER_TIME var, param1 = 60 s ve <= butce/5; LAND var ve SON satir
  P7 sure butcesi (.param hizlariyla hesaplanir) <= SARTNAME_FDA_OPERASYON_SURESI_S
  P8 denetleyici gercekten duser: bozulmus kopyalar (SR2_POSITION dusuk, TAKEOFF 20 m,
     TEYIT listesi eksik, RC_SPEED silinmis, SERVO10 Motor1'e cekilmis) ilgili kapida
     DUSER — kapinin kendisi sinanir
  P9 RC_SPEED == plan degeri (400 Hz, §0.2) ve <= ESC spec ust siniri (Skywalker 60A V2
     432 Hz) ve ArduPilot @Range 50..490 icinde — 6 Eylul dokumunde 490 (varsayilan) idi,
     D-429 §4
  P10 motor cikislari: OLCULEN AUX eslemesi SERVO9..12 = 36,34,33,35 birebir (D-428 §5d;
     dort satir TEYIT isaretli), bos cikislar SERVO1-8/13-16 == 0, her motor fonksiyonu
     33..36 tum SERVOn_FUNCTION'lar arasinda TAM BIR KEZ
"""
import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "comms", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from pymavlink import mavutil  # noqa: E402

import iha_komut_alici  # noqa: E402
import mavlink_dogrula  # noqa: E402
from karar_sozlesmesi import (MAVLINK_DURUM_ASGARI_HZ,  # noqa: E402
                              MAVLINK_KONUM_ASGARI_HZ,
                              SARTNAME_ASGARI_IRTIFA_M,
                              SARTNAME_FDA_OPERASYON_SURESI_S,
                              SENARYO_BOYUTLARI_M, yerel_konum_m)

DIZIN = KOK / "config" / "pixhawk"
PARAM_DOSYASI = DIZIN / "arducopter_fda.param"
WP_DOSYASI = DIZIN / "fda_gorev.waypoints"
README = DIZIN / "README.md"

# ── ArduPilot parametre tablolari (Copter-4.5 kaynagi; TEK yer) ────────────────
# ArduCopter/Parameters.cpp
FRAME_CLASS_QUAD = 1            # @Values 1:Quad
FRAME_TYPE_X = 1                # @Values 1:X
FS_THR_ENABLED_ALWAYS_RTL = 1   # @Values 1:Enabled always RTL
FS_GCS_RTL = 1                  # @Values 1:RTL
# AP_Motors/AP_MotorsMulticopter.cpp
MOT_PWM_TYPE_NORMAL = 0         # @Values 0:Normal
# AP_SerialManager/AP_SerialManager.cpp
SERIAL_PROTOCOL_MAVLINK2 = 2    # @Values 2:MAVLink2
SERIAL_BAUD_57600 = 57          # @Values 57:57600
# AP_BoardConfig/AP_BoardConfig.cpp
BRD_SER_RTSCTS_DISABLED = 0     # @Values 0:Disabled
# AP_BattMonitor/AP_BattMonitor_Params.cpp
BATT_MONITOR_ANALOG_V_I = 4     # @Values 4:Analog Voltage and Current
BATT_FS_ACT_LAND = 1            # @Values{Copter} 1:Land
BATT_FS_ACT_RTL = 2             # @Values{Copter} 2:RTL
# AC_Fence/AC_Fence.cpp
FENCE_TYPE_BIT_ALT_MAX = 1 << 0   # @Bitmask{Copter} 0:Max altitude
FENCE_TYPE_BIT_CIRCLE = 1 << 1    # 1:Circle Centered on Home
FENCE_ACTION_RTL_OR_LAND = 1      # @Values{Copter} 1:RTL or Land
FENCE_RADIUS_ALT_SINIRI_M = 30.0  # @Range 30 10000
# AP_Arming/AP_Arming.cpp
ARMING_CHECK_ALL = 1            # @Bitmask 0:All
# RC_Channel/RC_Channels_VarInfo.h @Bitmask 2:IBUS
RC_PROTOCOLS_BIT_IBUS = 1 << 2
# ArduCopter/defines.h MASK_LOG_* bitleri; config.h DEFAULT_LOG_BITMASK bilesimi
LOG_BITMASK_VARSAYILAN = sum(1 << b for b in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17))
# AC_WPNav/AC_WPNav.cpp WPNAV_SPEED_UP varsayilani (dosyada yok; butce hesabi icin)
WPNAV_SPEED_UP_VARSAYILAN_CMS = 250.0
# ArduCopter/Parameters.cpp RC_SPEED: "@Units: Hz @Range: 50 490" (Copter-4.5 dali,
# 2026-09-07 okundu); ArduCopter/config.h RC_FAST_SPEED 490 = varsayilan (6 Eylul dokumu)
RC_SPEED_ARALIK_HZ = (50, 490)
# SAHA_HAZIRLIK_PLANI_20260903.md §0.2 "ilk ucuslarda PWM 400 Hz"
RC_SPEED_PLAN_HZ = 400
# Hobbywing Skywalker 60A V2 gaz sinyali 50-432 Hz (D-429 §4; ESC etiketi D-428 §1, beyan)
ESC_PWM_UST_HZ = 432
# libraries/SRV_Channel/SRV_Channel.cpp SERVOn_FUNCTION @Values (Copter-4.5)
SERVO_FUNCTION_DISABLED = 0             # 0:Disabled
SERVO_FUNCTION_MOTOR = (33, 34, 35, 36)  # 33:Motor1,34:Motor2,35:Motor3,36:Motor4
# OLCULEN AUX eslemesi (D-428 §5d; config/pixhawk/arducopter_fda_20260906.param satir
# 918/848/853/858): AUX1..4 = SERVO9..12 = Motor4, Motor2, Motor1, Motor3. Motor testi bu
# eslemeyle gecti; degistirmek = motor testini bastan almak.
ESC_CIKIS_ESLEMESI = {
    "SERVO9_FUNCTION": 36, "SERVO10_FUNCTION": 34,
    "SERVO11_FUNCTION": 33, "SERVO12_FUNCTION": 35,
}
# Bos cikislar: MAIN 1-8 (SERVO1-8) ve AUX 5-8 (SERVO13-16). Dokumde motor fonksiyonu
# tasiyordu (basibos); D-429 §4 karari: 0.
BOS_CIKISLAR = tuple(f"SERVO{n}_FUNCTION" for n in (*range(1, 9), *range(13, 17)))
SERVO_FUNCTION_DESENI = re.compile(r"^SERVO\d{1,2}_FUNCTION$")
# ArduPilot parametre adi: buyuk harf/rakam/alt cizgi, en fazla 16 karakter
PARAM_AD_DESENI = re.compile(r"^[A-Z][A-Z0-9_]{0,15}$")
CM_PER_M = 100.0

ZORUNLU_ANAHTARLAR = (
    "FRAME_CLASS", "FRAME_TYPE", "MOT_PWM_TYPE", "SYSID_THISMAV",
    "SERIAL1_PROTOCOL", "SERIAL1_BAUD", "SERIAL2_PROTOCOL", "SERIAL2_BAUD",
    "SR1_POSITION", "SR1_EXTRA3", "SR2_POSITION", "SR2_EXTRA3",
    "RC_PROTOCOLS", "BATT_MONITOR", "BATT_LOW_VOLT", "BATT_CRT_VOLT",
    "BATT_FS_LOW_ACT", "BATT_FS_CRT_ACT", "FS_THR_ENABLE", "FS_GCS_ENABLE",
    "FENCE_ENABLE", "FENCE_TYPE", "FENCE_ALT_MAX", "FENCE_RADIUS", "FENCE_ACTION",
    "RTL_ALT", "LAND_SPEED", "WPNAV_SPEED", "ARMING_CHECK", "LOG_BITMASK",
)

# ── gorev sablonu beklentileri ─────────────────────────────────────────────────
WP_BASLIK = "QGC WPL 110"
WP_SUTUN_SAYISI = 12
WP_SATIR_SAYISI = 8               # 0 home, 1 takeoff, 2-5 koseler, 6 loiter, 7 land
KOSE_INDEKSLERI = (2, 3, 4, 5)
# ACK bekleme loiter suresi. karar_sozlesmesi'nde birebir sabit YOK (IKA_GO tekrar
# penceresi 5 s, parasut 8 s, FDA butcesi 600 s); 60 s = YKS iki asamali onay + hakem
# ACK penceresi (README §1). Ust sinir butceye baglidir: butcenin 1/5'ini asamaz.
LOITER_ACK_BEKLEME_S = 60.0
LOITER_BUTCE_PAYI = 5.0
KARE_TOLERANSI_M = 0.5
# Butce hesabi: arm + motor donusu + kalkis oncesi bekleme payi (kaba, README §1)
HAZIRLIK_PAYI_S = 60.0
HOME_ADI = "HOME"
README_TEYIT_BASLIGI = "## 3. TEYİT listesi"


# ════════════════════════════════════════════════════════════════════════════
# Ayristiricilar (dosyayi Mission Planner / QGC gibi okur)
# ════════════════════════════════════════════════════════════════════════════

def param_oku(yol):
    """Mission Planner ParamFile.loadParamFile davranisi: '#' satiri atlanir, satir
    bosluk/virgul/sekme ile bolunur, [0] ad, [1] deger (double, invariant).

    Doner: (parametreler{ad: float}, teyit_adlari{ad}, hatalar[str], neden_siz[ad]).
    Ek kural (bu deponun sozlesmesi): parametre satiri tam olarak "AD,DEGER"dir
    (fazladan belirtec yok) ve ustunde en az bir '#' satiri (NEDEN) vardir.
    """
    parametreler, teyit, hatalar, neden_siz = {}, set(), [], []
    onceki_yorum = False
    teyit_bekliyor = False
    for no, ham in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
        satir = ham.strip()
        if not satir:
            onceki_yorum = False
            teyit_bekliyor = False
            continue
        if satir.startswith("#"):
            onceki_yorum = True
            if satir[1:].strip().upper().startswith("TEYIT"):
                teyit_bekliyor = True
            continue
        parcalar = [p for p in re.split(r"[ ,\t]+", satir) if p]
        if len(parcalar) != 2:
            hatalar.append(f"satir {no}: 'AD,DEGER' degil: {ham!r}")
            onceki_yorum = False
            teyit_bekliyor = False
            continue
        ad, deger_metni = parcalar
        if not PARAM_AD_DESENI.match(ad):
            hatalar.append(f"satir {no}: gecersiz parametre adi {ad!r}")
        try:
            deger = float(deger_metni)
        except ValueError:
            hatalar.append(f"satir {no}: deger sayi degil {deger_metni!r}")
            deger = float("nan")
        if not math.isfinite(deger):
            hatalar.append(f"satir {no}: deger sonlu degil {deger_metni!r}")
        if ad in parametreler:
            hatalar.append(f"satir {no}: mukerrer parametre {ad}")
        parametreler[ad] = deger
        if not onceki_yorum:
            neden_siz.append(ad)
        if teyit_bekliyor:
            teyit.add(ad)
        onceki_yorum = False
        teyit_bekliyor = False
    return parametreler, teyit, hatalar, neden_siz


def waypoint_oku(yol):
    """QGC WPL 110: baslik + sekmeyle ayrilmis 12 sutun (mavlink.io/en/file_formats).

    Doner: (baslik, satirlar[dict], hatalar[str]).
    """
    metin = yol.read_text(encoding="utf-8").splitlines()
    hatalar = []
    if not metin:
        return "", [], ["dosya bos"]
    baslik = metin[0].strip()
    satirlar = []
    for no, ham in enumerate(metin[1:], 2):
        if not ham.strip():
            continue
        alanlar = ham.split("\t")
        if len(alanlar) != WP_SUTUN_SAYISI:
            hatalar.append(f"satir {no}: {len(alanlar)} sutun, {WP_SUTUN_SAYISI} bekleniyor")
            continue
        try:
            satirlar.append({
                "indeks": int(alanlar[0]), "current": int(alanlar[1]),
                "frame": int(alanlar[2]), "komut": int(alanlar[3]),
                "p1": float(alanlar[4]), "p2": float(alanlar[5]),
                "p3": float(alanlar[6]), "p4": float(alanlar[7]),
                "lat": float(alanlar[8]), "lon": float(alanlar[9]),
                "alt": float(alanlar[10]), "autocontinue": int(alanlar[11]),
            })
        except ValueError as exc:
            hatalar.append(f"satir {no}: sayi ayristirilamadi ({exc})")
    return baslik, satirlar, hatalar


def readme_teyit_adlari(metin):
    """README'nin TEYIT bolumundeki `PARAM` adlari (bolum: baslik -> sonraki '## ')."""
    bas = metin.find(README_TEYIT_BASLIGI)
    if bas < 0:
        return None
    son = metin.find("\n## ", bas + len(README_TEYIT_BASLIGI))
    bolum = metin[bas:son if son > 0 else None]
    return set(re.findall(r"^- `([A-Z][A-Z0-9_]{0,15})`", bolum, flags=re.M))


def rc_speed_hatalari(parametreler):
    """P9 kapisi (D-429 §4): RC_SPEED dosyada VAR, plan degeri, ESC spec'i ve ArduPilot
    araligi icinde. Dosyada yoksa firmware varsayilani (490) kalir = ESC spec disi."""
    if "RC_SPEED" not in parametreler:
        return [f"RC_SPEED yok: firmware varsayilani {RC_SPEED_ARALIK_HZ[1]} Hz kalir "
                f"(ESC ust siniri {ESC_PWM_UST_HZ} Hz)"]
    hatalar = []
    hz = parametreler["RC_SPEED"]
    if int(hz) != RC_SPEED_PLAN_HZ:
        hatalar.append(f"RC_SPEED {hz:g} != plan {RC_SPEED_PLAN_HZ} Hz")
    if hz > ESC_PWM_UST_HZ:
        hatalar.append(f"RC_SPEED {hz:g} > ESC spec ust siniri {ESC_PWM_UST_HZ} Hz")
    if not RC_SPEED_ARALIK_HZ[0] <= hz <= RC_SPEED_ARALIK_HZ[1]:
        hatalar.append(f"RC_SPEED {hz:g} ArduPilot @Range {RC_SPEED_ARALIK_HZ} disinda")
    return hatalar


def motor_cikis_hatalari(parametreler):
    """P10 kapisi: olculen AUX eslemesi birebir, bos cikislar Disabled, her motor
    fonksiyonu (33..36) tum SERVOn_FUNCTION'lar arasinda TAM BIR KEZ.

    Doner: hata metinleri (bos liste = gecti). Mutasyon testleri (P8f/P8g) ayni
    fonksiyonu bozuk kopyada kosar; kapi 'her zaman gecen' degildir.
    """
    hatalar = []
    for ad, beklenen in ESC_CIKIS_ESLEMESI.items():
        if ad not in parametreler:
            hatalar.append(f"{ad} yok (olculen esleme {beklenen})")
        elif int(parametreler[ad]) != beklenen:
            hatalar.append(f"{ad} = {parametreler[ad]:g} != olculen {beklenen}")
    for ad in BOS_CIKISLAR:
        if ad not in parametreler:
            hatalar.append(f"{ad} yok (bos cikis, {SERVO_FUNCTION_DISABLED} olmali)")
        elif int(parametreler[ad]) != SERVO_FUNCTION_DISABLED:
            hatalar.append(f"{ad} = {parametreler[ad]:g} != {SERVO_FUNCTION_DISABLED} (bos cikis)")
    sayim = {m: [] for m in SERVO_FUNCTION_MOTOR}
    for ad, deger in parametreler.items():
        if SERVO_FUNCTION_DESENI.match(ad) and int(deger) in sayim:
            sayim[int(deger)].append(ad)
    for m, adlar in sayim.items():
        if len(adlar) != 1:
            hatalar.append(f"motor fonksiyonu {m}: {len(adlar)} kez {adlar} (tam 1 olmali)")
    return hatalar


def sure_butcesi_s(parametreler, satirlar):
    """Kotu-durum gorev suresi: hazirlik + tirmanis + yol (WPNAV_SPEED) + loiter +
    inis (tamami LAND_SPEED ile). Yol uzunlugu satirlarin yerel konumlarindan olculur
    (home = satir 0 referansi; lat/lon 0,0 olan loiter/land 'bulundugu yer' sayilir)."""
    home = satirlar[0]
    takeoff = next(s for s in satirlar if s["komut"] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)
    tirmanis_s = takeoff["alt"] / (WPNAV_SPEED_UP_VARSAYILAN_CMS / CM_PER_M)
    hiz_ms = parametreler["WPNAV_SPEED"] / CM_PER_M
    inis_ms = parametreler["LAND_SPEED"] / CM_PER_M
    yol_m = 0.0
    onceki = (0.0, 0.0)
    loiter_s = 0.0
    en_yuksek_alt = takeoff["alt"]
    for s in satirlar[1:]:
        if s["komut"] == mavutil.mavlink.MAV_CMD_NAV_LOITER_TIME:
            loiter_s += s["p1"]
        if s["komut"] == mavutil.mavlink.MAV_CMD_NAV_WAYPOINT:
            konum = yerel_konum_m(home["lat"], home["lon"], s["lat"], s["lon"])
            yol_m += math.dist(onceki, konum)
            onceki = konum
            en_yuksek_alt = max(en_yuksek_alt, s["alt"])
    return (HAZIRLIK_PAYI_S + tirmanis_s + yol_m / hiz_ms + loiter_s
            + en_yuksek_alt / inis_ms)


# ════════════════════════════════════════════════════════════════════════════

class ParamDosyasi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p, cls.teyit, cls.hatalar, cls.neden_siz = param_oku(PARAM_DOSYASI)

    def test_p1_ayrisir_ve_mp_ayirmasiyla_ayni(self):
        self.assertEqual(self.hatalar, [], "ayristirma hatalari")
        self.assertGreater(len(self.p), 0)
        # MP: line.Split(' ', ',', '\t') -> items[0], double.Parse(items[1])
        mp = {}
        for ham in PARAM_DOSYASI.read_text(encoding="utf-8").splitlines():
            if not ham.strip() or ham.startswith("#"):
                continue
            parcalar = [x for x in re.split(r"[ ,\t]", ham) if x]
            mp[parcalar[0]] = float(parcalar[1])
        self.assertEqual(mp, self.p)

    def test_p2_zorunlu_anahtarlar_var(self):
        eksik = [a for a in ZORUNLU_ANAHTARLAR if a not in self.p]
        self.assertEqual(eksik, [], f"§1.6 zorunlu anahtarlar eksik: {eksik}")

    def test_p3_degerler_sozlesmeyle_tutarli(self):
        p = self.p
        # kimlik: alicilarin pinlendigi sysid (CONTRACTS §7.4, D-403)
        self.assertEqual(int(p["SYSID_THISMAV"]), iha_komut_alici.VARSAYILAN_HEDEF_SYSID)
        self.assertEqual(int(p["SYSID_THISMAV"]), mavlink_dogrula.VARSAYILAN_BEKLENEN_SYSID)
        # akis hizlari (karar_sozlesmesi MAVLINK_*_ASGARI_HZ)
        for hat in ("SR1", "SR2"):
            self.assertGreaterEqual(p[f"{hat}_POSITION"], MAVLINK_KONUM_ASGARI_HZ, hat)
            self.assertGreaterEqual(p[f"{hat}_EXTRA3"], MAVLINK_DURUM_ASGARI_HZ, hat)
        # Jetson hatti jitter payi: mavlink_dogrula ile ayni carpan
        self.assertGreaterEqual(
            p["SR2_POSITION"], MAVLINK_KONUM_ASGARI_HZ * mavlink_dogrula.ISTEK_HIZ_CARPANI)
        # iki hat MAVLink2 + 57600 (SiK ve jetson_baslat PIXHAWK_BAUD)
        for n in ("1", "2"):
            self.assertEqual(int(p[f"SERIAL{n}_PROTOCOL"]), SERIAL_PROTOCOL_MAVLINK2)
            self.assertEqual(int(p[f"SERIAL{n}_BAUD"]), SERIAL_BAUD_57600)
        self.assertEqual(int(p["BRD_SER2_RTSCTS"]), BRD_SER_RTSCTS_DISABLED)
        # govde
        self.assertEqual(int(p["FRAME_CLASS"]), FRAME_CLASS_QUAD)
        self.assertEqual(int(p["FRAME_TYPE"]), FRAME_TYPE_X)
        self.assertEqual(int(p["MOT_PWM_TYPE"]), MOT_PWM_TYPE_NORMAL)
        # RC: iBUS biti acik
        self.assertTrue(int(p["RC_PROTOCOLS"]) & RC_PROTOCOLS_BIT_IBUS)
        # pil
        self.assertEqual(int(p["BATT_MONITOR"]), BATT_MONITOR_ANALOG_V_I)
        self.assertGreater(p["BATT_LOW_VOLT"], p["BATT_CRT_VOLT"])
        self.assertGreater(p["BATT_CRT_VOLT"], 0.0)
        self.assertEqual(int(p["BATT_FS_LOW_ACT"]), BATT_FS_ACT_RTL)
        self.assertEqual(int(p["BATT_FS_CRT_ACT"]), BATT_FS_ACT_LAND)
        # failsafe
        self.assertEqual(int(p["FS_THR_ENABLE"]), FS_THR_ENABLED_ALWAYS_RTL)
        self.assertEqual(int(p["FS_GCS_ENABLE"]), FS_GCS_RTL)
        # cit: irtifa + daire; gorev irtifasinin ve RTL irtifasinin ustunde
        self.assertEqual(int(p["FENCE_ENABLE"]), 1)
        self.assertTrue(int(p["FENCE_TYPE"]) & FENCE_TYPE_BIT_ALT_MAX)
        self.assertTrue(int(p["FENCE_TYPE"]) & FENCE_TYPE_BIT_CIRCLE)
        self.assertGreater(p["FENCE_ALT_MAX"], SARTNAME_ASGARI_IRTIFA_M)
        self.assertGreater(p["FENCE_ALT_MAX"], p["RTL_ALT"] / CM_PER_M)
        self.assertGreaterEqual(p["FENCE_RADIUS"], FENCE_RADIUS_ALT_SINIRI_M)
        self.assertGreater(p["FENCE_RADIUS"], SENARYO_BOYUTLARI_M["FDA"] * math.sqrt(2))
        self.assertEqual(int(p["FENCE_ACTION"]), FENCE_ACTION_RTL_OR_LAND)
        # RTL gorev irtifasinin altinda kalmasin (once alcalip sonra tirmanma yok)
        self.assertGreaterEqual(p["RTL_ALT"] / CM_PER_M, SARTNAME_ASGARI_IRTIFA_M)
        # arm + log
        self.assertEqual(int(p["ARMING_CHECK"]), ARMING_CHECK_ALL)
        self.assertEqual(int(p["LOG_BITMASK"]), LOG_BITMASK_VARSAYILAN)

    def test_p4_her_parametrenin_neden_yorumu_var(self):
        self.assertEqual(self.neden_siz, [], f"NEDEN yorumsuz parametreler: {self.neden_siz}")

    def test_p5_readme_teyit_listesi_param_ile_ayni(self):
        self.assertTrue(README.exists())
        readme_kume = readme_teyit_adlari(README.read_text(encoding="utf-8"))
        self.assertIsNotNone(readme_kume, f"README'de {README_TEYIT_BASLIGI!r} bolumu yok")
        self.assertGreater(len(self.teyit), 0, ".param'da hic '# TEYIT' isareti yok")
        self.assertEqual(readme_kume, self.teyit,
                         f"README TEYIT {sorted(readme_kume)} != .param TEYIT {sorted(self.teyit)}")
        # README iki dosyayi da adiyla anmali (yukleme yordami)
        metin = README.read_text(encoding="utf-8")
        for ad in (PARAM_DOSYASI.name, WP_DOSYASI.name, "Load from file", "Load WP File"):
            self.assertIn(ad, metin)

    def test_p9_rc_speed_plan_degeri_ve_esc_spec_icinde(self):
        # D-429 §4: dokumde 490 (firmware varsayilani) = Skywalker 60A V2 spec disi
        self.assertIn("RC_SPEED", self.p, "RC_SPEED dosyada yok -> kart 490'da kalir")
        self.assertEqual(int(self.p["RC_SPEED"]), RC_SPEED_PLAN_HZ)
        self.assertLessEqual(self.p["RC_SPEED"], ESC_PWM_UST_HZ)
        self.assertGreaterEqual(self.p["RC_SPEED"], RC_SPEED_ARALIK_HZ[0])
        self.assertLessEqual(self.p["RC_SPEED"], RC_SPEED_ARALIK_HZ[1])
        self.assertEqual(rc_speed_hatalari(self.p), [])

    def test_p10_motor_cikislari_olculen_aux_eslemesi_bos_cikislar_sifir(self):
        p = self.p
        # olculen esleme birebir (D-428 §5d): AUX1..4 = M4, M2, M1, M3
        for ad, beklenen in ESC_CIKIS_ESLEMESI.items():
            self.assertIn(ad, p)
            self.assertEqual(int(p[ad]), beklenen, ad)
        # bos cikislar Disabled (D-429 §4)
        for ad in BOS_CIKISLAR:
            self.assertIn(ad, p)
            self.assertEqual(int(p[ad]), SERVO_FUNCTION_DISABLED, ad)
        # her motor fonksiyonu tam bir kez
        atanan = sorted(int(v) for ad, v in p.items()
                        if SERVO_FUNCTION_DESENI.match(ad) and int(v) in SERVO_FUNCTION_MOTOR)
        self.assertEqual(atanan, sorted(SERVO_FUNCTION_MOTOR))
        self.assertEqual(motor_cikis_hatalari(p), [])
        # dort ESC cikisi TEYIT isaretli (README metin kilidi P5 ile birlikte)
        self.assertTrue(set(ESC_CIKIS_ESLEMESI) <= self.teyit,
                        f"TEYIT'siz ESC cikisi: {sorted(set(ESC_CIKIS_ESLEMESI) - self.teyit)}")


class GorevSablonu(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baslik, cls.s, cls.hatalar = waypoint_oku(WP_DOSYASI)
        cls.p, _, _, _ = param_oku(PARAM_DOSYASI)

    def test_p6_qgc_wpl_110_yapisi_ve_gorev_sirasi(self):
        m = mavutil.mavlink
        self.assertEqual(self.baslik, WP_BASLIK)
        self.assertEqual(self.hatalar, [])
        self.assertEqual(len(self.s), WP_SATIR_SAYISI)
        self.assertEqual([x["indeks"] for x in self.s], list(range(WP_SATIR_SAYISI)))
        # home satiri
        home = self.s[0]
        self.assertEqual(home["current"], 1)
        self.assertEqual(home["frame"], m.MAV_FRAME_GLOBAL)
        self.assertEqual(home["komut"], m.MAV_CMD_NAV_WAYPOINT)
        self.assertEqual(sum(x["current"] for x in self.s), 1)
        # geri kalanlar goreli irtifa cercevesinde
        for x in self.s[1:]:
            self.assertEqual(x["frame"], m.MAV_FRAME_GLOBAL_RELATIVE_ALT, x)
            self.assertEqual(x["autocontinue"], 1, x)
        # TAKEOFF: ilk gorev satiri, irtifa sartname asgarisinin ustunde, citin altinda
        takeoff = self.s[1]
        self.assertEqual(takeoff["komut"], m.MAV_CMD_NAV_TAKEOFF)
        self.assertGreaterEqual(takeoff["alt"], SARTNAME_ASGARI_IRTIFA_M)
        self.assertLess(takeoff["alt"], self.p["FENCE_ALT_MAX"])
        # koseler: 20x20 m kare, ardisik koseler arasi = kenar, tumu gorev irtifasinda
        kenar = SENARYO_BOYUTLARI_M["FDA"]
        koseler = []
        for i in KOSE_INDEKSLERI:
            x = self.s[i]
            self.assertEqual(x["komut"], m.MAV_CMD_NAV_WAYPOINT, x)
            self.assertGreaterEqual(x["alt"], SARTNAME_ASGARI_IRTIFA_M, x)
            self.assertLess(x["alt"], self.p["FENCE_ALT_MAX"], x)
            konum = yerel_konum_m(home["lat"], home["lon"], x["lat"], x["lon"])
            self.assertIsNotNone(konum, x)
            koseler.append(konum)
        for a, b in zip(koseler, koseler[1:]):
            self.assertAlmostEqual(math.dist(a, b), kenar, delta=KARE_TOLERANSI_M)
        self.assertAlmostEqual(math.dist(koseler[0], koseler[2]), kenar * math.sqrt(2),
                               delta=KARE_TOLERANSI_M)
        self.assertAlmostEqual(math.dist(koseler[1], koseler[3]), kenar * math.sqrt(2),
                               delta=KARE_TOLERANSI_M)
        # tum koseler cit yaricapinin icinde (home merkezli daire)
        for k in koseler:
            self.assertLess(math.hypot(*k), self.p["FENCE_RADIUS"])
        # LOITER_TIME: ACK bekleme; sure sabiti ve butce payi
        loiter = self.s[6]
        self.assertEqual(loiter["komut"], m.MAV_CMD_NAV_LOITER_TIME)
        self.assertEqual(loiter["p1"], LOITER_ACK_BEKLEME_S)
        self.assertLessEqual(loiter["p1"], SARTNAME_FDA_OPERASYON_SURESI_S / LOITER_BUTCE_PAYI)
        self.assertGreaterEqual(loiter["alt"], SARTNAME_ASGARI_IRTIFA_M)
        # LAND: var ve SON satir
        self.assertEqual(self.s[-1]["komut"], m.MAV_CMD_NAV_LAND)
        self.assertEqual(sum(1 for x in self.s if x["komut"] == m.MAV_CMD_NAV_LAND), 1)

    def test_p7_sure_butcesi_sartname_icinde(self):
        toplam = sure_butcesi_s(self.p, self.s)
        self.assertLessEqual(
            toplam, SARTNAME_FDA_OPERASYON_SURESI_S,
            f"kotu-durum gorev suresi {toplam:.0f} s > {SARTNAME_FDA_OPERASYON_SURESI_S:.0f} s")
        # hakem onayi gecikirse pilotun loiter uzatma payi kalsin: butcenin yarisi
        self.assertLessEqual(toplam, SARTNAME_FDA_OPERASYON_SURESI_S / 2.0)


class DenetleyiciGercektenDuser(unittest.TestCase):
    """P8: kapilar bozulmus girdiyi yakalar — 'her zaman gecen test' degil."""

    def _kopya(self, kaynak, degistir):
        metin = kaynak.read_text(encoding="utf-8")
        yeni = degistir(metin)
        self.assertNotEqual(metin, yeni, "mutasyon uygulanamadi")
        d = tempfile.mkdtemp()
        yol = Path(d) / kaynak.name
        yol.write_text(yeni, encoding="utf-8")
        return yol

    def test_p8a_dusuk_sr2_position_yakalanir(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace("\nSR2_POSITION,8\n", "\nSR2_POSITION,1\n"))
        p, _, hatalar, _ = param_oku(yol)
        self.assertEqual(hatalar, [])
        self.assertLess(p["SR2_POSITION"], MAVLINK_KONUM_ASGARI_HZ)

    def test_p8b_nedensiz_ve_bozuk_satir_yakalanir(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t + "\nYENI_PARAM,1\nBOZUK 1 2\n")
        _, _, hatalar, neden_siz = param_oku(yol)
        self.assertIn("YENI_PARAM", neden_siz)
        self.assertTrue(any("BOZUK" in h for h in hatalar), hatalar)

    def test_p8c_teyit_isareti_readme_ile_kopar(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace("# TEYIT: Pixhawk'ta BRD_SER2_RTSCTS", "# NOT: BRD_SER2_RTSCTS"))
        _, teyit, _, _ = param_oku(yol)
        readme_kume = readme_teyit_adlari(README.read_text(encoding="utf-8"))
        self.assertNotEqual(teyit, readme_kume)

    def test_p8d_takeoff_asgari_alti_yakalanir(self):
        yol = self._kopya(WP_DOSYASI, lambda t: t.replace("\t22\t0\t0\t0\t0\t0\t0\t32\t1", "\t22\t0\t0\t0\t0\t0\t0\t20\t1"))
        _, s, hatalar = waypoint_oku(yol)
        self.assertEqual(hatalar, [])
        takeoff = next(x for x in s if x["komut"] == mavutil.mavlink.MAV_CMD_NAV_TAKEOFF)
        self.assertLess(takeoff["alt"], SARTNAME_ASGARI_IRTIFA_M)

    def test_p8e_eksik_sutun_yakalanir(self):
        yol = self._kopya(WP_DOSYASI, lambda t: t.replace("7\t0\t3\t21\t0\t0\t0\t0\t0\t0\t0\t1", "7\t0\t3\t21\t0\t0\t0\t0\t0\t0\t0"))
        _, s, hatalar = waypoint_oku(yol)
        self.assertEqual(len(hatalar), 1, hatalar)
        self.assertEqual(len(s), WP_SATIR_SAYISI - 1)

    def test_p8f_rc_speed_silinince_yakalanir(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace("\nRC_SPEED,400\n", "\n"))
        p, _, hatalar, _ = param_oku(yol)
        self.assertEqual(hatalar, [])
        self.assertNotIn("RC_SPEED", p)
        self.assertNotEqual(rc_speed_hatalari(p), [])

    def test_p8g_servo10_motor1_yapilinca_yakalanir(self):
        # SERVO10 34 -> 33: Motor1 iki cikista, Motor2 hicbir cikista
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace("\nSERVO10_FUNCTION,34\n", "\nSERVO10_FUNCTION,33\n"))
        p, _, hatalar, _ = param_oku(yol)
        self.assertEqual(hatalar, [])
        h = motor_cikis_hatalari(p)
        self.assertTrue(any(x.startswith("SERVO10_FUNCTION = 33") for x in h), h)
        self.assertTrue(any(x.startswith("motor fonksiyonu 33: 2 kez") for x in h), h)
        self.assertTrue(any(x.startswith("motor fonksiyonu 34: 0 kez") for x in h), h)


if __name__ == "__main__":
    unittest.main()
