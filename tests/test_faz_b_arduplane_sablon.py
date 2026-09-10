"""FAZ B · T221 — ARDUPLANE FINAL PARAMETRE SETI + SITL PROVA GOREVI KAPILARI (config/pixhawk/).

NEDEN (T221 / K11; JETSON_OTURUM_DURUMU_20260909.md SS5 madde 4; D-431 SS4(10) "ArduPlane parametre
seti ve provasi yok"): yarisma final araci (sabit kanat + mancinik + parasut) icin parametre dosyasi
yoktu. Bu test dosyayi Mission Planner ayirmasiyla okur (test_faz_b_pixhawk_sablon.param_oku - TEK
ayristirici) ve degerleri uc kaynaga baglar: (1) ArduPilot Plane-4.5.7 KAYNAGI - scripts/
ardupilot_param_kaynak.py'nin urettigi kanit JSON'u uzerinden, CEVRIMDISI; (2) DDR tasarim sayilari
(BEYAN, burada TEK yerde); (3) depo sozlesmeleri (karar_sozlesmesi, iha_komut_alici, mavlink_dogrula,
arducopter_fda.param). Mock yok; ArduPilot tablolari kaynak dosya adiyla asagida TEK yerde.

Kapilar:
  A1  .param ayrisir, NEDEN'siz parametre yok; betigin ayristiricisi ayni ad/degerleri gorur
  A2  zorunlu anahtarlar VAR (servo, TKOFF, CHUTE, FS, ARMING, SERIAL2, RC_PROTOCOLS, LOG)
  A3  servo: 16 cikisin hepsi yazili, yalniz izinli fonksiyonlar, aileron 2 / elevator 1 / rudder 1 /
      gaz 2 / parasut 1 (DDR), Copter motor fonksiyonu YOK (servo cakismasi yok)
  A4  CHUTE tutarliligi: acik, servo tipi + TAM BIR parasut cikisi, ON != OFF ve servo MIN/MAX icinde,
      SITL esigi arasinda, gecikme > 0, kritik alcalma kapali, pil kritik eylemi parasut -> acik
  A5  TKOFF (mancinik) tutarliligi: ivme kapisi acik ve DDR ivmesinin yarisinin altinda; gecikme ray
      suresinden uzun, ray + itkisiz stall suresinden kisa; GPS hiz kapisi 0; TDRAG/ROTATE 0; tek ivme
      olayi; zaman asimi 0; ray acisi "Bad launch" kapisinin icinde; yorumdaki sayilar hesapla ayni
  A6  failsafe: RC acik, AUTO'da kisa/uzun kayipta devam, zaman asimlari DDR ile ayni, uzun >= kisa,
      GCS heartbeat acik ve ARMING_REQUIRE ile
  A7  pil: analog V+I, LOW > CRT = DDR 14,0 V, dusukte RTL (Plane tablosu 1), kritikte parasut (5)
  A8  hava hizi: MIN >= 1,2 x DDR stall, CRUISE = DDR seyir, MIN < CRUISE < MAX, MAX >= 1,5 x MIN, MAX < VH
  A9  Jetson/YKS sozlesmesi + arducopter_fda.param ile ortak anahtarlar ESIT
  A10 ARMING_CHECK 1, ARMING_REQUIRE 1 · A11 RC_PROTOCOLS 1 iken BEYAN · A12 LOG_BITMASK tanimli bitler
  A13 Q_ENABLE 0
  A14 kaynak kaniti: etiket Plane-4.5.7 + commit; ad/deger kumesi .param ile BIREBIR (bayat kanit duser);
      her kayit bulundu, tanim satiri eslesti, deger @Values/@Bitmask/@Range icinde
  A15 her parametrenin yorum blogu, kanittaki tanim dosyasinin ADINI anar
  A16 README SS6: TEYIT listesi == .param TEYIT, BEYAN listesi == .param BEYAN; dosya/surum atiflari
  A17 SITL prova gorevi: QGC WPL 110; home CMAC; ilk NAV_TAKEOFF (pitch 5..20); TAM BIR DO_PARACHUTE
      (RELEASE) son WAYPOINT'ten sonra, birakma irtifasi > CHUTE_ALT_MIN; son satir LOITER_UNLIM
  A18 SITL yoklama kaniti "HUKUM: OLCULEMEDI" ve README SS6.6 bunu yazar, GECTI yazmaz; SS6.6 kabul
      olcutu 1 (T221-D, D-449): beklenen-yok listesi onceden yazilan kumeyle AYNI ve .param'da; yuklu
      ad sayisi .param'dan HESAPLANIR (N - |beklenen-yok|); her beklenen-yok adinin var_info adi SITL
      ikilisinde 0 kez, pozitif kontrolu >= 1 (sitl_yoklama.txt SS6.1); README sha'si = yoklama
      sha'si; features.txt satir atfi yoklamayla ayni; DUSER kurali + CHUTE_* on hukmu yazili.
      T221-D2 (curutucu C2/C3/C4/C7): D-449 oncesi olcut 1 ("dosyadaki N adin N'si") yururlukteki
      metinde YOK, ham metinde TAM 1 kez ~~cizili~~ ve hemen ardinda tarih damgasi; olcut 1 maddesinde
      acilis surumu ve `param show CHUTE_ENABLED` 1 TAM 1 kez; CHUTE_* on hukmu paragrafi TAM 1 kez,
      basliginda tarih damgasi, hukum cumleleri ("Olcut 1 DUSER (... eklenmez, esik gevsetilmez)",
      "olcut 3 yine olculur") paragrafin ICINDE, paragrafta her olcut en cok 1 kez anilir
  A19 ardupilot_param_kaynak.py saf fonksiyonlari (cevrimdisi sentetik kaynak)
  M1..M17 mutasyonlar: bozulmus kopyada ilgili denetleyici DUSER
"""
import json
import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "comms", KOK / "scripts", KOK / "tests"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from pymavlink import mavutil  # noqa: E402

import ardupilot_param_kaynak as apk  # noqa: E402
import iha_komut_alici  # noqa: E402
import mavlink_dogrula  # noqa: E402
from karar_sozlesmesi import (MAVLINK_DURUM_ASGARI_HZ,  # noqa: E402
                              MAVLINK_KONUM_ASGARI_HZ,
                              SARTNAME_IHA_UB_KENAR_M, yerel_konum_m)
from test_faz_b_pixhawk_sablon import (ARMING_CHECK_ALL,  # noqa: E402
                                       BATT_MONITOR_ANALOG_V_I,
                                       BRD_SER_RTSCTS_DISABLED,
                                       SERIAL_BAUD_57600,
                                       SERIAL_PROTOCOL_MAVLINK2, param_oku,
                                       waypoint_oku)
from test_faz_b_pixhawk_sablon import \
    PARAM_DOSYASI as COPTER_PARAM_DOSYASI  # noqa: E402

DIZIN = KOK / "config" / "pixhawk"
PARAM_DOSYASI = DIZIN / "arduplane_final.param"
GOREV_DOSYASI = DIZIN / "arduplane_sitl_prova.waypoints"
README = DIZIN / "README.md"
KANIT_DIZINI = KOK / "results" / "fdr_sprint_20260910" / "H8" / "T221"
KANIT_JSON = KANIT_DIZINI / "plane457_param_kaynak.json"
SITL_YOKLAMA = KANIT_DIZINI / "sitl_yoklama.txt"
PARAM_GORELI = "config/pixhawk/arduplane_final.param"

# ── surum (D-425: dosya TEK surume baglidir) ─────────────────────────────────
ETIKET = "Plane-4.5.7"
FIRMWARE_DIZINI = "stable-4.5.7"
# firmware.ardupilot.org/Plane/stable-4.5.7/Pixhawk6C/git-version.txt (10 Eyl okundu) = etiket commit'i
ETIKET_COMMIT = "0358a9c210bc6c965006f5d6029239b7033616df"

# ── ArduPilot Plane-4.5.7 tablolari (kaynak dosya adiyla, TEK yer) ─────────────
# libraries/SRV_Channel/SRV_Channel.cpp FUNCTION @Values{Plane}
SERVO_KAPALI = 0
SERVO_AILERON = 4
SERVO_ELEVATOR = 19
SERVO_RUDDER = 21
SERVO_PARASUT = 27
SERVO_GAZ = 70
SERVO_COPTER_MOTOR = (*range(33, 41), 82, 83, 84, 85)       # Motor1..8, Motor9..12
IZINLI_SERVO = frozenset((SERVO_KAPALI, SERVO_AILERON, SERVO_ELEVATOR, SERVO_RUDDER,
                          SERVO_PARASUT, SERVO_GAZ))
SERVO_FUNCTION_DESENI = re.compile(r"^SERVO(\d{1,2})_FUNCTION$")
# SRV_Channel.cpp MIN / MAX varsayilanlari (dosyada yazilmazsa bunlar gecer)
SERVO_MIN_VARSAYILAN = 1100.0
SERVO_MAX_VARSAYILAN = 1900.0
# AP_HAL_ChibiOS/hwdef/Pixhawk6C/hwdef.dat: 8 IOMCU (MAIN) + PWM(1)..PWM(8) FMU (AUX)
PIXHAWK6C_CIKIS_SAYISI = 16
# libraries/AP_Parachute/AP_Parachute.cpp (+ .h)
CHUTE_TIP_SERVO = 10                 # TYPE @Values 10:Servo
CHUTE_PWM_ARALIGI = (1000.0, 2000.0)  # SERVO_ON / SERVO_OFF @Range
CHUTE_SECENEK_ACIK_TUT = 1 << 0      # OPTIONS @Bitmask 0:hold open forever after release
# libraries/SITL/SIM_Parachute.cpp Parachute::update: pwm >= 1250 -> "BANG!  Parachute deployed"
SIM_PARA_ESIK_PWM = 1250.0
# ArduPlane/defines.h + ArduPlane/Parameters.cpp
THR_FAILSAFE_ACIK = 1                # THR_FAILSAFE @Values 1:Enabled
FS_KISA_DEGISMEZ = 0                 # FS_ACTION_SHORT_BESTGUESS: AUTO'da kip degismez
FS_UZUN_DEVAM = 0                    # FS_ACTION_LONG_CONTINUE
FS_UZUN_PARASUT = 3                  # FS_ACTION_LONG_PARACHUTE
GCS_FS_HEARTBEAT = 1                 # GCS_FAILSAFE_HEARTBEAT
# libraries/AP_Arming/AP_Arming.cpp REQUIRE @Values 1:minimum PWM when disarmed
ARMING_REQUIRE_MIN_PWM = 1
# libraries/AP_BattMonitor/AP_BattMonitor_Params.cpp FS_LOW_ACT / FS_CRT_ACT @Values{Plane}
BATT_FS_PLANE_RTL = 1
BATT_FS_PLANE_PARASUT = 5
# ArduPlane/quadplane.cpp ENABLE @Values 0:Disable
Q_KAPALI = 0
# libraries/RC_Channel/RC_Channels_VarInfo.h _PROTOCOLS @Bitmask
RC_TUMU = 1
RC_ADAY_BITLERI = {2: "IBUS", 3: "SBUS", 9: "CRSF"}   # README SS6.4 adaylari
# ArduPlane/Parameters.cpp LOG_BITMASK @Bitmask (6 ve 15 TANIMSIZ: defines.h MODE "no longer used",
# ARM_DISARM yorum satiri)
LOG_TANIMLI_BITLER = frozenset((*range(0, 6), *range(7, 15), 19, 20, 21, 22))
LOG_SECILEN_BITLER = (*range(0, 6), *range(7, 15))     # config.h 0xffff'in tanimli kismi
# ArduPlane/takeoff.cpp auto_takeoff_check / takeoff_calc_pitch
TKOFF_GECIKME_BIRIMI_S = 0.1                     # TKOFF_THR_DELAY @Units ds
TKOFF_KOTU_ATIS_PITCH_DERECE = (-30.0, 45.0)     # pitch <= -3000 || >= 4500 cd -> "Bad launch AUTO"
TKOFF_MANCINIK_MIN_PITCH_DERECE = 5.0            # MAX(takeoff_pitch_cd, 500)
PITCH_MAX_VARSAYILAN_DERECE = 20.0               # ArduPlane/config.h PITCH_MAX 20
TKOFF_MINACC_ARALIK = (0.0, 30.0)                # TKOFF_THR_MINACC @Range 0 30
# ArduPlane/Parameters.cpp AIRSPEED_MIN / AIRSPEED_MAX aciklamalari
AIRSPEED_MIN_STALL_CARPANI = 1.2   # "Should be set to 20% higher than level flight stall speed."
AIRSPEED_MAX_MIN_CARPANI = 1.5     # "at least 50% above AIRSPEED_MIN"
# ArduPlane/config.h varsayilanlari (dosyaya yazilmazsa gecerli) - mutasyon M4
AIRSPEED_CONFIG_H = {"AIRSPEED_CRUISE": 12.0, "AIRSPEED_MIN": 9.0, "AIRSPEED_MAX": 22.0}

# ── DDR tasarim sayilari (BEYAN; ucusla olculmedi, arac uretilmedi) — TEK yer ──
# rapor/NAVITIAS_DDR_2026_Bolum3_Only (5) (3).docx: V-n tablosu (VS/VC/VH), gorev profili (faz 1:
# "15° rail, 3.5 m ray", "~18m/s"), "25 m/s ... toplam surukleme ~6.0 N", MTOW 8,542 kg;
# rapor/3.3.1-2-3-4_SON.docx: failsafe (RC 1,5 s, heartbeat 5 s, 4S 14,0 V), 4x MG996R, 2 motor.
DDR_STALL_MS = 15.86
DDR_SEYIR_MS = 25.0
DDR_VH_MS = 35.0
DDR_MTOW_KG = 8.542
DDR_SURUKLEME_SEYIRDE_N = 6.0
DDR_RAY_M = 3.5
DDR_CIKIS_MS = 18.0
DDR_RAY_ACI_DERECE = 15.0
DDR_KRITIK_PIL_V = 14.0
DDR_RC_FS_S = 1.5
DDR_HEARTBEAT_FS_S = 5.0
DDR_ESC = 2
YER_CEKIMI_MS2 = 9.80665

# 4x MG996R = 2 kanatcik + elevator + rudder; 2 ESC; 1 kurtarma tetik hatti
BEKLENEN_SERVO_SAYIMI = {SERVO_AILERON: 2, SERVO_ELEVATOR: 1, SERVO_RUDDER: 1,
                         SERVO_GAZ: DDR_ESC, SERVO_PARASUT: 1}

# ── SITL prova gorevi ─────────────────────────────────────────────────────────
CMAC = (-35.363261, 149.165230)    # Tools/autotest/locations.txt:4 (SITL varsayilan konumu)
WP_BASLIK = "QGC WPL 110"

ORTAK_ANAHTARLAR = ("SYSID_THISMAV", "SERIAL1_PROTOCOL", "SERIAL1_BAUD", "SERIAL2_PROTOCOL",
                    "SERIAL2_BAUD", "BRD_SER2_RTSCTS", "SR1_POSITION", "SR1_EXTRA3",
                    "SR2_POSITION", "SR2_EXTRA3")
ZORUNLU_ANAHTARLAR = (
    "Q_ENABLE", *ORTAK_ANAHTARLAR, "RC_PROTOCOLS",
    *(f"SERVO{n}_FUNCTION" for n in range(1, PIXHAWK6C_CIKIS_SAYISI + 1)),
    "TKOFF_THR_MINACC", "TKOFF_THR_DELAY", "TKOFF_THR_MINSPD", "TKOFF_TDRAG_ELEV",
    "TKOFF_TDRAG_SPD1", "TKOFF_ROTATE_SPD", "TKOFF_ACCEL_CNT", "TKOFF_TIMEOUT",
    "AIRSPEED_MIN", "AIRSPEED_CRUISE", "AIRSPEED_MAX",
    "CHUTE_ENABLED", "CHUTE_TYPE", "CHUTE_SERVO_ON", "CHUTE_SERVO_OFF", "CHUTE_ALT_MIN",
    "CHUTE_DELAY_MS", "CHUTE_CRT_SINK", "CHUTE_OPTIONS",
    "THR_FAILSAFE", "FS_SHORT_ACTN", "FS_SHORT_TIMEOUT", "FS_LONG_ACTN", "FS_LONG_TIMEOUT",
    "FS_GCS_ENABL", "BATT_MONITOR", "BATT_LOW_VOLT", "BATT_CRT_VOLT", "BATT_LOW_TIMER",
    "BATT_FS_LOW_ACT", "BATT_FS_CRT_ACT", "ARMING_CHECK", "ARMING_REQUIRE", "LOG_BITMASK",
)

README_BOLUM = "## 6. ArduPlane final"
README_TEYIT = "### 6.3"
README_BEYAN = "### 6.4"
README_SITL = "### 6.6"
# sitl_yoklama.txt'teki T221-D ek tarama blogu (sitl_yokla.py --ek)
YOKLAMA_EK = "## 6.1"

# ── SITL beklenen-yok (README SS6.6 kabul olcutu 1; D-449 · 10 Eyl, OLCUMDEN ONCE) ─────────────
# Pixhawk 6C'de VAR, Plane 4.5.7 SITL'de DERLENMEZ: libraries/AP_BoardConfig/AP_BoardConfig.cpp:124
# `#ifdef HAL_HAVE_RTSCTS_SERIAL2` (tanim :131). Makroyu ChibiOS hwdef ureteci yazar
# (hwdef/scripts/chibios_hwdef.py:1899-1903, UART'in _RTS hatti varsa); Pixhawk6C hwdef.dat:57-58
# UART5_RTS/CTS, :37 SERIAL_ORDER -> SERIAL2 = UART5. Olcum: sitl_yoklama.txt SS6.1 "SER2_RTSCTS 0".
# Liste olcumden SONRA genisletilmez: README kumesi bu sabitten farkliysa A18 DUSER. CHUTE_* eksikse
# README SS6.6 on hukmu isler (olcut 1 DUSER, parasut zinciri OLCULEMEDI) - listeye EKLENMEZ.
SITL_BEKLENEN_YOK = frozenset({"BRD_SER2_RTSCTS"})
# beklenen-yok adinin ayni var_info'daki KOSULSUZ komsusu (AP_BoardConfig.cpp:171 SAFETY_DEFLT): ikilide
# >= 1 gorulmezse "0" tarama yonteminin korlugu olabilir, kanit sayilmaz
SITL_POZITIF_KONTROL = {"BRD_SER2_RTSCTS": "SAFETY_DEFLT"}
# D-449 duzeltmesinin tarih damgasi (cizili eski olcut 1'in notu ve CHUTE_* on hukmunun basligi)
SITL_DAMGA = "10 Eylül, ölçümden önce, D-449"
# CHUTE_* on hukmunun on kayitli hukum cumleleri; on hukum paragrafinin ICINDE durur. T221-D2
# (curutucu C3/C7): hukum kelimesi (DUSER -> OLCULEMEDI gevsetmesi) ve gerekcesi ("sonradan eklenmez,
# esik gevsetilmez") da kilitli
SITL_ON_HUKUM_IFADELERI = (
    "SITL paraşütsüz derlenmiş — paraşüt zinciri ÖLÇÜLEMEDİ",
    "Ölçüt 1 **DÜŞER** (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez)",
    "ölçüt 3 (kalkış kapısı) yine ölçülür",
)
# README SS6.6'da yururlukteki (cizilmemis) metinde bulunmasi gereken on kayit cumleleri
SITL_KURAL_IFADELERI = ("listenin dışındaki her eksik ad **DÜŞER**",
                        "ölçümden önce, D-449",
                        *SITL_ON_HUKUM_IFADELERI)
# T221-D2 (curutucu C2): D-449 ONCESI olcut 1 bicimi ("dosyadaki 62 adın 62'si yüklü" - SITL'de hic
# tutamaz). Yururlukteki metinde BULUNMAZ; ham metinde TAM 1 kez ~~cizili~~ durur ve hemen ardinda
# "(<SITL_DAMGA>" gelir (FDR kurali: eski metin silinmez, cizilir + tarih). "addan" bicimi de yakalanir;
# yururlukteki yeni cumle ("addan SITL'de **61**'i") bu desene UYMAZ.
SITL_ESKI_OLCUT1 = r"dosyadaki\s+\**\d+\**\s+ad(?:ın|dan)\s+\**\d+\**'\w+"
# T221-D2 (curutucu C4): olcut 1 maddesinin yururlukteki metninde TAM 1 kez gecmesi gereken kosullar
SITL_OLCUT1_KOSULLARI = ("Açılış `ArduPlane V4.5.7`", "`param show CHUTE_ENABLED` 1")
SITL_KABUL_BASLIGI = "**Kabul ölçütleri"
# CHUTE_* on hukmu paragrafinin basi: yururlukteki metinde TAM 1 kez, ardindan "(<SITL_DAMGA>):**"
SITL_ON_HUKUM = "**Ön hüküm — SITL'de `CHUTE_*` yoksa"


# ════════════════════════════════════════════════════════════════════════════
# Yardimcilar
# ════════════════════════════════════════════════════════════════════════════

def mancinik_kinematigi():
    """DDR sayilarindan (sabit ivme varsayimi): (ort. ivme m/s2, ray suresi s, itkisiz stall'a sure s).

    Stall suresi: 15 derece tirmanista itkisiz yavaslama g.sin(aci) + D/m; surukleme V^2 ile
    olceklenir ve CIKIS hizindaki deger kullanilir (en buyuk surukleme -> en kisa sure, ihtiyatli).
    """
    ort_ivme = DDR_CIKIS_MS ** 2 / (2.0 * DDR_RAY_M)
    ray_s = 2.0 * DDR_RAY_M / DDR_CIKIS_MS
    surukleme_n = DDR_SURUKLEME_SEYIRDE_N * (DDR_CIKIS_MS / DDR_SEYIR_MS) ** 2
    yavaslama = (YER_CEKIMI_MS2 * math.sin(math.radians(DDR_RAY_ACI_DERECE))
                 + surukleme_n / DDR_MTOW_KG)
    stall_s = (DDR_CIKIS_MS - DDR_STALL_MS) / yavaslama
    return ort_ivme, ray_s, stall_s


def yorum_bloklari(yol):
    """Her parametrenin HEMEN ustundeki ardisik '#' satirlari (bos satir blogu keser)."""
    bloklar, blok = {}, []
    for ham in yol.read_text(encoding="utf-8").splitlines():
        satir = ham.strip()
        if not satir:
            blok = []
            continue
        if satir.startswith("#"):
            blok.append(satir)
            continue
        bloklar[re.split(r"[ ,\t]+", satir)[0]] = blok
        blok = []
    return bloklar


def isaretli_adlar(bloklar, isaret):
    """Yorum blogunda '# <ISARET>' ile baslayan satir bulunan parametreler."""
    return {ad for ad, blok in bloklar.items()
            if any(s[1:].strip().upper().startswith(isaret) for s in blok)}


def readme_bolumu(metin, baslik):
    """'baslik' ile baslayan bolum; ayni ya da ust duzey bir sonraki basliga kadar.
    Kod citlerinin (```) icindeki '#' satirlari baslik sayilmaz."""
    duzey = len(baslik) - len(baslik.lstrip("#"))
    icinde, cit, secilen = False, False, []
    for s in metin.splitlines():
        if s.startswith("```"):
            cit = not cit
        elif not cit:
            m = re.match(r"^(#{1,6}) ", s)
            if m:
                if icinde and len(m.group(1)) <= duzey:
                    break
                if s.startswith(baslik):
                    icinde = True
        if icinde:
            secilen.append(s)
    return "\n".join(secilen) if secilen else None


def readme_listesi(bolum):
    """Bolumdeki '- `PARAM`' maddeleri."""
    return set(re.findall(r"^- `([A-Z][A-Z0-9_]{0,15})`", bolum, flags=re.M))


def servo_fonksiyonlari(p):
    return {ad: int(v) for ad, v in p.items() if SERVO_FUNCTION_DESENI.match(ad)}


def ondalik(x, basamak):
    """README/yorum yazimi: Turkce ondalik virgul."""
    return f"{x:.{basamak}f}".replace(".", ",")


# ════════════════════════════════════════════════════════════════════════════
# Denetleyiciler (saf fonksiyon; bos liste = gecti). Mutasyon testleri ayni
# fonksiyonlari bozuk kopyada kosar: kapilar "her zaman gecen" degildir.
# ════════════════════════════════════════════════════════════════════════════

def servo_hatalari(p):
    """A3: 16 cikis acik, izinli fonksiyonlar, DDR sayimi, Copter motoru yok."""
    hatalar = []
    for n in range(1, PIXHAWK6C_CIKIS_SAYISI + 1):
        if f"SERVO{n}_FUNCTION" not in p:
            hatalar.append(f"SERVO{n}_FUNCTION yok (her cikis acikca yazilir)")
    fonk = servo_fonksiyonlari(p)
    for ad, f in sorted(fonk.items()):
        if f in SERVO_COPTER_MOTOR:
            hatalar.append(f"{ad} = {f}: Copter motor fonksiyonu")
        elif f not in IZINLI_SERVO:
            hatalar.append(f"{ad} = {f}: izinli kume {sorted(IZINLI_SERVO)} disinda")
    for f, beklenen in BEKLENEN_SERVO_SAYIMI.items():
        adlar = sorted(ad for ad, v in fonk.items() if v == f)
        if len(adlar) != beklenen:
            hatalar.append(f"fonksiyon {f}: {len(adlar)} cikis {adlar} (beklenen {beklenen})")
    return hatalar


def parasut_hatalari(p):
    """A4: CHUTE_* kendi icinde ve servo/pil/SITL ile tutarli."""
    hatalar = []
    if int(p.get("CHUTE_ENABLED", 0)) != 1:
        hatalar.append("CHUTE_ENABLED != 1 (sartname SS2.2.4: parasutle inis zorunlu)")
    kanallar = sorted(ad for ad, v in servo_fonksiyonlari(p).items() if v == SERVO_PARASUT)
    if int(p.get("CHUTE_TYPE", -1)) != CHUTE_TIP_SERVO:
        hatalar.append(f"CHUTE_TYPE != {CHUTE_TIP_SERVO} (servo)")
    elif len(kanallar) != 1:
        hatalar.append(f"CHUTE_TYPE servo iken {SERVO_PARASUT} atanmis cikis sayisi {len(kanallar)} "
                       "(AP_Parachute arming_checks: 'Chute has no channel')")
    on, off = p.get("CHUTE_SERVO_ON"), p.get("CHUTE_SERVO_OFF")
    if on is None or off is None or on == off:
        hatalar.append("CHUTE_SERVO_ON/OFF eksik ya da esit")
    else:
        for ad, v in (("CHUTE_SERVO_ON", on), ("CHUTE_SERVO_OFF", off)):
            if not CHUTE_PWM_ARALIGI[0] <= v <= CHUTE_PWM_ARALIGI[1]:
                hatalar.append(f"{ad} {v:g} @Range {CHUTE_PWM_ARALIGI} disinda")
        if len(kanallar) == 1:
            n = SERVO_FUNCTION_DESENI.match(kanallar[0]).group(1)
            lo = p.get(f"SERVO{n}_MIN", SERVO_MIN_VARSAYILAN)
            hi = p.get(f"SERVO{n}_MAX", SERVO_MAX_VARSAYILAN)
            for ad, v in (("CHUTE_SERVO_ON", on), ("CHUTE_SERVO_OFF", off)):
                if not lo <= v <= hi:
                    hatalar.append(f"{ad} {v:g} SERVO{n} MIN/MAX {lo:g}..{hi:g} disinda")
        if not off < SIM_PARA_ESIK_PWM <= on:
            hatalar.append(f"SITL SIM_PARA esigi {SIM_PARA_ESIK_PWM:g} OFF({off:g})..ON({on:g}) "
                           "arasinda degil: prova birakmayi goremez")
    if p.get("CHUTE_DELAY_MS", 0) <= 0:
        hatalar.append("CHUTE_DELAY_MS <= 0: gaz bastirilmadan parasut acilir")
    if p.get("CHUTE_CRT_SINK", -1) != 0:
        hatalar.append("CHUTE_CRT_SINK != 0: otomatik birakma esigi ucus verisi olmadan secilemez "
                       "(README SS6.7 karari)")
    if int(p.get("CHUTE_OPTIONS", 0)) & ~CHUTE_SECENEK_ACIK_TUT:
        hatalar.append("CHUTE_OPTIONS tanimsiz bit")
    parasut_eylemi = (int(p.get("BATT_FS_CRT_ACT", 0)) == BATT_FS_PLANE_PARASUT
                      or int(p.get("FS_LONG_ACTN", 0)) == FS_UZUN_PARASUT)
    if parasut_eylemi and int(p.get("CHUTE_ENABLED", 0)) != 1:
        hatalar.append("failsafe eylemi parasut ama CHUTE_ENABLED kapali")
    return hatalar


def kalkis_hatalari(p):
    """A5: mancinik kalkisi (ArduPlane/takeoff.cpp mantigi + DDR kinematigi)."""
    hatalar = []
    ort_ivme, ray_s, stall_s = mancinik_kinematigi()
    minacc = p.get("TKOFF_THR_MINACC", 0.0)
    if not TKOFF_MINACC_ARALIK[0] < minacc <= TKOFF_MINACC_ARALIK[1]:
        hatalar.append(f"TKOFF_THR_MINACC {minacc:g}: 0 ivme kapisini kapatir (GPS sicramasi motoru "
                       "baslatabilir) ya da @Range disi")
    if minacc > ort_ivme / 2.0:
        hatalar.append(f"TKOFF_THR_MINACC {minacc:g} > DDR ort. ivmenin yarisi {ort_ivme / 2:.1f}")
    gecikme_s = p.get("TKOFF_THR_DELAY", 0.0) * TKOFF_GECIKME_BIRIMI_S
    if gecikme_s < ray_s:
        hatalar.append(f"TKOFF_THR_DELAY {gecikme_s:.2f} s < ray suresi {ray_s:.2f} s "
                       "(pervane kizaktayken doner)")
    if gecikme_s >= ray_s + stall_s:
        hatalar.append(f"TKOFF_THR_DELAY {gecikme_s:.2f} s >= ray + itkisiz stall suresi "
                       f"{ray_s + stall_s:.2f} s")
    if p.get("TKOFF_THR_MINSPD", -1) != 0:
        hatalar.append("TKOFF_THR_MINSPD != 0: GPS ~0,5 s gecikir, hiz kapisi 100 ms pencerede "
                       "sorulur -> 'Timeout AUTO', motor acilmaz")
    for ad in ("TKOFF_TDRAG_ELEV", "TKOFF_TDRAG_SPD1", "TKOFF_ROTATE_SPD"):
        if p.get(ad, -1) != 0:
            hatalar.append(f"{ad} != 0 (kaynak aciklamasi: el/mancinik atisinda sifir)")
    if int(p.get("TKOFF_ACCEL_CNT", 0)) != 1:
        hatalar.append("TKOFF_ACCEL_CNT != 1 (mancinik tek ivme olayi)")
    if p.get("TKOFF_TIMEOUT", -1) != 0:
        hatalar.append("TKOFF_TIMEOUT != 0 (tetik sonrasi disarm riski)")
    if not TKOFF_KOTU_ATIS_PITCH_DERECE[0] < DDR_RAY_ACI_DERECE < TKOFF_KOTU_ATIS_PITCH_DERECE[1]:
        hatalar.append("DDR ray acisi 'Bad launch AUTO' pitch kapisinin disinda")
    return hatalar


def failsafe_hatalari(p):
    """A6: AUTO'da failsafe gorevi bozmaz; zaman asimlari DDR; Plane arm kosulu."""
    hatalar = []
    if int(p.get("THR_FAILSAFE", 0)) != THR_FAILSAFE_ACIK:
        hatalar.append("THR_FAILSAFE != 1 (RC kaybi algilanmaz)")
    if int(p.get("FS_SHORT_ACTN", -1)) != FS_KISA_DEGISMEZ:
        hatalar.append("FS_SHORT_ACTN != 0: AUTO'da kisa RC kaybi kipi degistirir")
    if int(p.get("FS_LONG_ACTN", -1)) != FS_UZUN_DEVAM:
        hatalar.append("FS_LONG_ACTN != 0: AUTO'da uzun kayip gorevi bozar (DDR: inis bolgesine yonelir)")
    if p.get("FS_SHORT_TIMEOUT") != DDR_RC_FS_S:
        hatalar.append(f"FS_SHORT_TIMEOUT != DDR {DDR_RC_FS_S} s")
    if p.get("FS_LONG_TIMEOUT") != DDR_HEARTBEAT_FS_S:
        hatalar.append(f"FS_LONG_TIMEOUT != DDR {DDR_HEARTBEAT_FS_S} s")
    if p.get("FS_LONG_TIMEOUT", 0.0) < p.get("FS_SHORT_TIMEOUT", 0.0):
        hatalar.append("FS_LONG_TIMEOUT < FS_SHORT_TIMEOUT: ArduPlane/AP_Arming.cpp arm reddeder")
    if int(p.get("FS_GCS_ENABL", 0)) != GCS_FS_HEARTBEAT:
        hatalar.append("FS_GCS_ENABL != 1 (heartbeat)")
    if int(p.get("FS_GCS_ENABL", 0)) and int(p.get("ARMING_REQUIRE", 0)) == 0:
        hatalar.append("FS_GCS_ENABL acik ama ARMING_REQUIRE 0 (kaynak aciklamasi ister)")
    return hatalar


def pil_hatalari(p):
    """A7: pil esikleri ve Plane eylem tablosu."""
    hatalar = []
    if int(p.get("BATT_MONITOR", 0)) != BATT_MONITOR_ANALOG_V_I:
        hatalar.append("BATT_MONITOR != 4 (analog V+I)")
    low, crt = p.get("BATT_LOW_VOLT", 0.0), p.get("BATT_CRT_VOLT", 0.0)
    if not low > crt > 0:
        hatalar.append(f"BATT_LOW_VOLT {low:g} > BATT_CRT_VOLT {crt:g} > 0 degil")
    if crt != DDR_KRITIK_PIL_V:
        hatalar.append(f"BATT_CRT_VOLT != DDR {DDR_KRITIK_PIL_V} V")
    if p.get("BATT_LOW_TIMER", 0.0) <= 0:
        hatalar.append("BATT_LOW_TIMER 0: dusuk gerilim hatasi kapanir (kaynak aciklamasi)")
    if int(p.get("BATT_FS_LOW_ACT", -1)) != BATT_FS_PLANE_RTL:
        hatalar.append("BATT_FS_LOW_ACT != 1 (Plane tablosunda RTL; Copter'da 1 = Land)")
    if int(p.get("BATT_FS_CRT_ACT", -1)) != BATT_FS_PLANE_PARASUT:
        hatalar.append("BATT_FS_CRT_ACT != 5 (Plane tablosunda Parachute; DDR kritikte parasut)")
    return hatalar


def hiz_hatalari(p):
    """A8: hava hizi araligi DDR stall/seyir/VH ve kaynak aciklamalariyla."""
    mn, cr, mx = p.get("AIRSPEED_MIN"), p.get("AIRSPEED_CRUISE"), p.get("AIRSPEED_MAX")
    if None in (mn, cr, mx):
        return ["AIRSPEED_MIN/CRUISE/MAX eksik: config.h varsayilanlari (9/12/22) DDR stall'in altinda"]
    hatalar = []
    if mn < AIRSPEED_MIN_STALL_CARPANI * DDR_STALL_MS:
        hatalar.append(f"AIRSPEED_MIN {mn:g} < 1,2 x DDR stall {AIRSPEED_MIN_STALL_CARPANI * DDR_STALL_MS:.2f}")
    if cr != DDR_SEYIR_MS:
        hatalar.append(f"AIRSPEED_CRUISE {cr:g} != DDR seyir {DDR_SEYIR_MS:g}")
    if not mn < cr < mx:
        hatalar.append(f"AIRSPEED_MIN {mn:g} < CRUISE {cr:g} < MAX {mx:g} degil")
    if mx < AIRSPEED_MAX_MIN_CARPANI * mn:
        hatalar.append(f"AIRSPEED_MAX {mx:g} < 1,5 x MIN {AIRSPEED_MAX_MIN_CARPANI * mn:g} (TECS)")
    if mx >= DDR_VH_MS:
        hatalar.append(f"AIRSPEED_MAX {mx:g} >= DDR VH {DDR_VH_MS:g}")
    return hatalar


def kanit_hatalari(p, kanit):
    """A14: kaynak kaniti bu dosyanin BUGUNKU ad/degerleriyle uretilmis ve temiz mi?"""
    hatalar = []
    if kanit.get("etiket") != ETIKET:
        hatalar.append(f"kanit etiketi {kanit.get('etiket')} != {ETIKET}")
    if kanit.get("commit") != ETIKET_COMMIT:
        hatalar.append(f"kanit commit'i {kanit.get('commit')} != {ETIKET_COMMIT}")
    if kanit.get("param_dosyasi") != PARAM_GORELI:
        hatalar.append(f"kanit baska dosyanin: {kanit.get('param_dosyasi')}")
    kayit = {k["ad"]: k for k in kanit.get("parametreler", [])}
    if set(kayit) != set(p):
        hatalar.append(f"kanit adlari != .param: eksik {sorted(set(p) - set(kayit))} "
                       f"fazla {sorted(set(kayit) - set(p))} (betigi yeniden kos)")
    for ad, v in sorted(p.items()):
        k = kayit.get(ad)
        if k is None:
            continue
        if not math.isclose(k["deger"], v):
            hatalar.append(f"{ad}: kanit {k['deger']:g} != .param {v:g} (kanit bayat)")
        if not k.get("kaynak"):
            hatalar.append(f"{ad}: Plane-4.5.7 kaynaginda YOK")
        elif not k.get("tanim_eslesti"):
            hatalar.append(f"{ad}: tanim satiri adla eslesmedi ({k.get('tanim')!r})")
        if not k.get("gecerli"):
            hatalar.append(f"{ad}: {k.get('neden')}")
    oz = kanit.get("ozet", {})
    if oz.get("bulunamayan") or oz.get("gecersiz"):
        hatalar.append(f"kanit ozeti temiz degil: {oz}")
    return hatalar


def kaynak_atfi_hatalari(bloklar, kanit):
    """A15: yorum blogu, parametrenin tanimlandigi dosyanin adini anar."""
    kayit = {k["ad"]: k for k in kanit.get("parametreler", [])}
    hatalar = []
    for ad, blok in sorted(bloklar.items()):
        k = kayit.get(ad)
        if not k or not k.get("kaynak"):
            continue
        dosya = Path(k["kaynak"]).name
        if dosya not in " ".join(blok):
            hatalar.append(f"{ad}: yorum blogu tanim dosyasini ({dosya}) anmiyor")
    return hatalar


def gorev_hatalari(satirlar, p):
    """A17: SITL prova gorevi yapisi ve CHUTE/TKOFF ile tutarliligi."""
    m = mavutil.mavlink
    if not satirlar:
        return ["gorev bos"]
    hatalar = []
    home = satirlar[0]
    if [s["indeks"] for s in satirlar] != list(range(len(satirlar))):
        hatalar.append("indeksler 0..n-1 sirali degil")
    if (home["current"], home["frame"], home["komut"]) != (1, m.MAV_FRAME_GLOBAL,
                                                          m.MAV_CMD_NAV_WAYPOINT):
        hatalar.append("satir 0 home degil (current 1, GLOBAL, NAV_WAYPOINT)")
    if sum(s["current"] for s in satirlar) != 1:
        hatalar.append("current=1 tek satir olmali")
    if (round(home["lat"], 6), round(home["lon"], 6)) != CMAC:
        hatalar.append(f"home CMAC degil: {home['lat']}, {home['lon']}")
    for s in satirlar[1:]:
        if s["frame"] != m.MAV_FRAME_GLOBAL_RELATIVE_ALT or s["autocontinue"] != 1:
            hatalar.append(f"satir {s['indeks']}: GLOBAL_RELATIVE_ALT/autocontinue 1 degil")
    alt_min = p.get("CHUTE_ALT_MIN", 0.0)
    if len(satirlar) < 2 or satirlar[1]["komut"] != m.MAV_CMD_NAV_TAKEOFF:
        hatalar.append("ilk gorev satiri NAV_TAKEOFF degil")
    else:
        pitch = satirlar[1]["p1"]
        ust = min(PITCH_MAX_VARSAYILAN_DERECE, TKOFF_KOTU_ATIS_PITCH_DERECE[1])
        if not TKOFF_MANCINIK_MIN_PITCH_DERECE <= pitch <= ust:
            hatalar.append(f"NAV_TAKEOFF pitch {pitch:g} {TKOFF_MANCINIK_MIN_PITCH_DERECE:g}..{ust:g} disinda")
        if satirlar[1]["alt"] <= alt_min:
            hatalar.append("NAV_TAKEOFF irtifasi CHUTE_ALT_MIN altinda")
    parasut = [i for i, s in enumerate(satirlar) if s["komut"] == m.MAV_CMD_DO_PARACHUTE]
    if len(parasut) != 1:
        hatalar.append(f"DO_PARACHUTE {len(parasut)} kez (tam 1 olmali)")
    else:
        i = parasut[0]
        if satirlar[i]["p1"] != m.PARACHUTE_RELEASE:
            hatalar.append("DO_PARACHUTE param1 PARACHUTE_RELEASE degil")
        onceki = [s for s in satirlar[1:i] if s["komut"] == m.MAV_CMD_NAV_WAYPOINT]
        if not onceki:
            hatalar.append("DO_PARACHUTE'tan once NAV_WAYPOINT (birakma noktasi) yok")
        elif onceki[-1]["alt"] <= alt_min:
            hatalar.append(f"birakma noktasi {onceki[-1]['alt']:g} m <= CHUTE_ALT_MIN {alt_min:g}: "
                           "YKS manuel yedegi orada reddedilir")
        if any(s["komut"] == m.MAV_CMD_NAV_WAYPOINT for s in satirlar[i + 1:]):
            hatalar.append("DO_PARACHUTE'tan sonra NAV_WAYPOINT var (birakma son olmali)")
    if satirlar[-1]["komut"] != m.MAV_CMD_NAV_LOITER_UNLIM:
        hatalar.append("son satir NAV_LOITER_UNLIM degil (oto-gaz kipi surmeli: servos.cpp gazi bastirir)")
    # ayak izi (home dahil) IHA-UB boyutunda bir kareye sigmali: IHA-UB'de kalmanin GEREKLI kosulu
    # (home'un IHA-UB icindeki yeri bilinmedigi icin yeterli kosul yazilamaz)
    noktalar = [(0.0, 0.0)]
    for s in satirlar[1:]:
        if s["komut"] in (m.MAV_CMD_NAV_WAYPOINT, m.MAV_CMD_NAV_LOITER_UNLIM):
            konum = yerel_konum_m(home["lat"], home["lon"], s["lat"], s["lon"])
            if konum is None:
                hatalar.append(f"satir {s['indeks']}: konum hesaplanamadi")
            else:
                noktalar.append(konum)
    for eksen, ad in ((0, "dogu"), (1, "kuzey")):
        genislik = max(n[eksen] for n in noktalar) - min(n[eksen] for n in noktalar)
        if genislik > SARTNAME_IHA_UB_KENAR_M:
            hatalar.append(f"gorev {ad} ekseninde {genislik:.0f} m > IHA-UB kenari "
                           f"{SARTNAME_IHA_UB_KENAR_M:g} m")
    return hatalar


def cizilmemis(metin):
    """~~cizili~~ (geri cekilmis) metni cikarir: kilitler yalniz YURURLUKTEKI metni okur."""
    return re.sub(r"~~.*?~~", "", metin, flags=re.S)


def dizge_sayisi(blok, dizge):
    """sitl_yokla.py ikili_tara satiri '  <dizge> <sayi>' -> sayi; satir yoksa None."""
    m = re.search(rf"^  {re.escape(dizge)} +(\d+)[ \t]*$", blok, flags=re.M)
    return int(m.group(1)) if m else None


def olcut_maddesi(metin, no):
    """SS6.6 'Kabul olcutleri' listesinin <no>. maddesi; baslik ya da madde yoksa None. Madde bir
    sonraki numarali maddeye ya da bos satira kadar surer (girintili devam satirlari dahil)."""
    bas = metin.find(SITL_KABUL_BASLIGI)
    if bas < 0:
        return None
    m = re.search(rf"^{no}\. (.*?)(?=^\d+\. |^[ \t]*$|\Z)", metin[bas:], flags=re.M | re.S)
    return m.group(1) if m else None


def paragraf(metin, bas_ifade):
    """'bas_ifade' ile baslayan paragraf (ilk bos satira kadar); yoksa None."""
    i = metin.find(bas_ifade)
    if i < 0:
        return None
    son = re.search(r"\n[ \t]*\n", metin[i:])
    return metin[i:i + son.start()] if son else metin[i:]


def eski_olcut1_hatalari(ham, metin):
    """T221-D2 (curutucu C2): D-449 oncesi olcut 1 yururlukte OLAMAZ (SITL'de hic tutamaz); FDR kurali
    geregi ham metinde TAM 1 kez ~~cizili~~ durur ve hemen ardinda tarih damgasi gelir.
    ham = SS6.6 ham metni, metin = cizilmemis(ham)."""
    hatalar = []
    yururlukte = re.findall(SITL_ESKI_OLCUT1, metin)
    if yururlukte:
        hatalar.append(f"eski olcut 1 yururlukteki metinde (cizgisi kaldirilmis): {yururlukte}")
    cizili = [c for c in re.findall(r"~~(.*?)~~", ham, flags=re.S) if re.search(SITL_ESKI_OLCUT1, c)]
    if len(cizili) != 1:
        hatalar.append(f"eski olcut 1 ~~cizili~~ {len(cizili)} kez (tam 1: FDR, eski metin silinmez)")
    elif not re.search(rf"~~[^~]*?{SITL_ESKI_OLCUT1}[^~]*?~~\s*\*?\({re.escape(SITL_DAMGA)}\W", ham):
        hatalar.append(f"cizili eski olcut 1'in hemen ardinda tarih damgasi yok: '({SITL_DAMGA}'")
    return hatalar


def olcut1_hatalari(metin):
    """T221-D2 (curutucu C4): yururlukteki olcut 1 maddesi acilis surumunu ve CHUTE_ENABLED kosulunu
    TAM 1 kez tasir. metin = cizilmemis SS6.6."""
    madde = olcut_maddesi(metin, 1)
    if madde is None:
        return [f"SS6.6 {SITL_KABUL_BASLIGI!r} altinda yururlukte olcut 1 maddesi yok"]
    return [f"olcut 1 maddesinde {k!r} {madde.count(k)} kez (tam 1 olmali)"
            for k in SITL_OLCUT1_KOSULLARI if madde.count(k) != 1]


def on_hukum_hatalari(metin):
    """T221-D2 (curutucu C3/C7): CHUTE_* on hukmu paragrafi yururlukte TAM 1 kez, basliginda tarih
    damgasi; hukum cumleleri paragrafin ICINDE; paragrafta her olcut en cok 1 kez anilir (ayni olcute
    celiskili ikinci hukum eklenemez). metin = cizilmemis SS6.6."""
    adet = metin.count(SITL_ON_HUKUM)
    if adet != 1:
        return [f"CHUTE_* on hukmu paragrafi {adet} kez (tam 1 olmali)"]
    on = paragraf(metin, SITL_ON_HUKUM)
    hatalar = []
    if not on.startswith(f"{SITL_ON_HUKUM} ({SITL_DAMGA}):**"):
        hatalar.append(f"on hukum basliginda tarih damgasi yok: '({SITL_DAMGA}):**'")
    hatalar += [f"on hukum paragrafinda yok: {ifade!r}" for ifade in SITL_ON_HUKUM_IFADELERI
                if ifade not in on]
    anilan = re.findall(r"[Öö]lçüt (\d+)", on)
    cok = sorted({n for n in anilan if anilan.count(n) > 1})
    if cok:
        hatalar.append(f"on hukum paragrafinda olcut {cok} birden cok kez anilmis (celiskili hukum)")
    return hatalar


def sitl_kabul_hatalari(sitl_bolumu, p, kanit, yoklama):
    """A18 (T221-D, D-449): README SS6.6 kabul olcutu 1 SITL'de tutabilir ve olcume bagli mi?

    Yuklu ad sayisi .param'dan HESAPLANIR (README'deki elle yazilmis sayiya guvenilmez); beklenen-yok
    listesi onceden yazilan kumeyle ayni olmali ve her adi SITL ikili taramasinda 0 kez gecmeli.
    T221-D2: eski olcut 1 cizili kalir (eski_olcut1_hatalari), olcut 1 kosullari tam 1 kez
    (olcut1_hatalari), CHUTE_* on hukmu gevsetilemez (on_hukum_hatalari).
    """
    metin = cizilmemis(sitl_bolumu)
    hatalar = []
    tanim = re.findall(r"beklenen-yok\**\s+listesi\s*=\s*\{([^}]*)\}", metin)
    if len(tanim) != 1:
        return [f"beklenen-yok listesi tanimi {len(tanim)} kez (tam 1 olmali)"]
    yok = frozenset(re.findall(r"`([A-Z][A-Z0-9_]*)`", tanim[0]))
    if yok != SITL_BEKLENEN_YOK:
        hatalar.append(f"README beklenen-yok {sorted(yok)} != onceden yazilan "
                       f"{sorted(SITL_BEKLENEN_YOK)} (liste olcumden sonra degistirilemez)")
    if yok - set(p):
        hatalar.append(f"beklenen-yok adi .param'da yok: {sorted(yok - set(p))}")
    sayilar = re.findall(r"dosyadaki\s+\**(\d+)\**\s+addan\s+SITL'de\s+\**(\d+)\**", metin)
    if len(sayilar) != 1:
        hatalar.append(f"olcut 1 sayi cumlesi {len(sayilar)} kez (tam 1 olmali)")
    else:
        n, m = map(int, sayilar[0])
        yuklu = len(set(p) - yok)
        if n != len(p):
            hatalar.append(f"olcut 1: dosyadaki ad README {n} != .param {len(p)}")
        if m != yuklu:
            hatalar.append(f"olcut 1: SITL'de yuklu README {m} != .param {len(p)} - beklenen-yok "
                           f"{len(yok & set(p))} = {yuklu}")
    for ifade in SITL_KURAL_IFADELERI:
        if ifade not in metin:
            hatalar.append(f"README SS6.6 on kayit cumlesi eksik: {ifade!r}")
    hatalar += (eski_olcut1_hatalari(sitl_bolumu, metin) + olcut1_hatalari(metin)
                + on_hukum_hatalari(metin))
    ek = readme_bolumu(yoklama, YOKLAMA_EK)
    if ek is None:
        return hatalar + [f"sitl_yoklama.txt'de {YOKLAMA_EK!r} ek tarama blogu yok"]
    sha = re.findall(r"^  bayt \d+ · sha256 ([0-9a-f]{64})", ek, flags=re.M)
    readme_sha = set(re.findall(r"\b[0-9a-f]{64}\b", metin))
    if len(sha) != 1 or readme_sha != {sha[0]}:
        hatalar.append(f"ikili sha: README {sorted(readme_sha)} != yoklama {sha}")
    kayit = {k["ad"]: k for k in kanit.get("parametreler", [])}
    for ad in sorted(yok):
        goreli = (kayit.get(ad) or {}).get("goreli_ad")
        if not goreli:
            hatalar.append(f"{ad}: kanitta goreli_ad yok (ikilideki adi bilinmiyor)")
            continue
        say = dizge_sayisi(ek, goreli)
        if say is None:
            hatalar.append(f"{ad}: yoklama ek taramasinda {goreli!r} satiri yok")
        elif say != 0:
            hatalar.append(f"{ad}: SITL ikilisinde {goreli!r} {say} kez (beklenen-yok olcumle celisir)")
        kontrol = SITL_POZITIF_KONTROL.get(ad)
        if not kontrol or not dizge_sayisi(ek, kontrol):
            hatalar.append(f"{ad}: pozitif kontrol {kontrol!r} ikilide gorulmedi (0 kanit sayilmaz)")
    atiflar = re.findall(r"(SITL_x86_64_linux_gnu|Pixhawk6C)/features\.txt:(\d+)", metin)
    if not any(kart.startswith("SITL") for kart, _ in atiflar):
        hatalar.append("SITL features.txt satir atfi yok (HAL_PARACHUTE_ENABLED celiskisi)")
    for kart, no in atiflar:
        if not re.search(rf"^    {kart} .*:{no} !?HAL_PARACHUTE_ENABLED\b", ek, flags=re.M):
            hatalar.append(f"{kart}/features.txt:{no} yoklamadaki satirla uyusmuyor")
    return hatalar


def _kanit():
    return json.loads(KANIT_JSON.read_text(encoding="utf-8"))


def _readme():
    return README.read_text(encoding="utf-8")


# ════════════════════════════════════════════════════════════════════════════

class ParamDosyasi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p, cls.teyit, cls.hatalar, cls.neden_siz = param_oku(PARAM_DOSYASI)
        cls.bloklar = yorum_bloklari(PARAM_DOSYASI)
        cls.kanit = _kanit()
        cls.metin = PARAM_DOSYASI.read_text(encoding="utf-8")

    def test_a1_ayrisir_ve_nedensiz_parametre_yok(self):
        self.assertEqual(self.hatalar, [])
        self.assertEqual(self.neden_siz, [], f"NEDEN yorumsuz: {self.neden_siz}")
        self.assertGreater(len(self.p), 0)
        # kanit betiginin ayristiricisi da (MP ayirmasi) ayni ad/degerleri gorur
        self.assertEqual(dict(apk.param_dosyasi_oku(PARAM_DOSYASI)), self.p)
        self.assertEqual(set(self.bloklar), set(self.p))

    def test_a2_zorunlu_anahtarlar_var(self):
        eksik = [a for a in ZORUNLU_ANAHTARLAR if a not in self.p]
        self.assertEqual(eksik, [], f"zorunlu anahtarlar eksik: {eksik}")

    def test_a3_servo_fonksiyonlari_ve_cakisma_yok(self):
        self.assertEqual(servo_hatalari(self.p), [])

    def test_a4_parasut_tutarliligi(self):
        self.assertEqual(parasut_hatalari(self.p), [])

    def test_a5_mancinik_kalkisi_tutarliligi(self):
        self.assertEqual(kalkis_hatalari(self.p), [])
        # yorumdaki sayilar hesapla ayni (DDR sabiti degisirse yorum da degismek zorunda)
        ort_ivme, ray_s, stall_s = mancinik_kinematigi()
        for sayi in (ondalik(ort_ivme, 1), ondalik(ray_s, 2), ondalik(stall_s, 2),
                     ondalik(ray_s + stall_s, 2)):
            self.assertIn(sayi, self.metin, f"{sayi} .param yorumunda yok")

    def test_a6_failsafe(self):
        self.assertEqual(failsafe_hatalari(self.p), [])

    def test_a7_pil(self):
        self.assertEqual(pil_hatalari(self.p), [])

    def test_a8_hava_hizi(self):
        self.assertEqual(hiz_hatalari(self.p), [])

    def test_a9_jetson_yks_sozlesmesi_ve_copter_ile_ortak_anahtarlar(self):
        p = self.p
        self.assertEqual(int(p["SYSID_THISMAV"]), iha_komut_alici.VARSAYILAN_HEDEF_SYSID)
        self.assertEqual(int(p["SYSID_THISMAV"]), mavlink_dogrula.VARSAYILAN_BEKLENEN_SYSID)
        for hat in ("SR1", "SR2"):
            self.assertGreaterEqual(p[f"{hat}_POSITION"], MAVLINK_KONUM_ASGARI_HZ, hat)
            self.assertGreaterEqual(p[f"{hat}_EXTRA3"], MAVLINK_DURUM_ASGARI_HZ, hat)
        self.assertGreaterEqual(
            p["SR2_POSITION"], MAVLINK_KONUM_ASGARI_HZ * mavlink_dogrula.ISTEK_HIZ_CARPANI)
        for n in ("1", "2"):
            self.assertEqual(int(p[f"SERIAL{n}_PROTOCOL"]), SERIAL_PROTOCOL_MAVLINK2)
            self.assertEqual(int(p[f"SERIAL{n}_BAUD"]), SERIAL_BAUD_57600)
        self.assertEqual(int(p["BRD_SER2_RTSCTS"]), BRD_SER_RTSCTS_DISABLED)
        copter, _, copter_hata, _ = param_oku(COPTER_PARAM_DOSYASI)
        self.assertEqual(copter_hata, [])
        fark = {a: (p[a], copter[a]) for a in ORTAK_ANAHTARLAR if p[a] != copter[a]}
        self.assertEqual(fark, {}, "ayni Jetson/YKS yazilimi: iki dosyada ayni olmali")

    def test_a10_arm(self):
        self.assertEqual(int(self.p["ARMING_CHECK"]), ARMING_CHECK_ALL)
        self.assertEqual(int(self.p["ARMING_REQUIRE"]), ARMING_REQUIRE_MIN_PWM)

    def test_a11_rc_protokolu_beyana_bagli(self):
        rc = int(self.p["RC_PROTOCOLS"])
        izinli = {RC_TUMU} | {1 << b for b in RC_ADAY_BITLERI}
        self.assertIn(rc, izinli)
        if rc == RC_TUMU:
            self.assertIn("RC_PROTOCOLS", isaretli_adlar(self.bloklar, "BEYAN"),
                          "RC_PROTOCOLS 1 (All) iken alici BEYAN isaretli olmali")

    def test_a12_log_bitmask_tanimli_bitler(self):
        deger = int(self.p["LOG_BITMASK"])
        self.assertEqual(deger, sum(1 << b for b in LOG_SECILEN_BITLER))
        bitler = {b for b in range(32) if deger >> b & 1}
        self.assertTrue(bitler <= LOG_TANIMLI_BITLER, sorted(bitler - LOG_TANIMLI_BITLER))

    def test_a13_quadplane_kapali(self):
        self.assertEqual(int(self.p["Q_ENABLE"]), Q_KAPALI)

    def test_a14_kaynak_kaniti_temiz_ve_guncel(self):
        self.assertEqual(kanit_hatalari(self.p, self.kanit), [])
        for metin in (self.metin, readme_bolumu(_readme(), README_BOLUM) or ""):
            self.assertIn(ETIKET, metin)
            self.assertIn(FIRMWARE_DIZINI, metin)
            self.assertIn(ETIKET_COMMIT[:10], metin)

    def test_a15_yorum_tanim_dosyasini_anar(self):
        self.assertEqual(kaynak_atfi_hatalari(self.bloklar, self.kanit), [])


class ReadmeVeIsaretler(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.p, cls.teyit, _, _ = param_oku(PARAM_DOSYASI)
        cls.bloklar = yorum_bloklari(PARAM_DOSYASI)
        cls.bolum = readme_bolumu(_readme(), README_BOLUM)

    def test_a16_readme_teyit_ve_beyan_listeleri_param_ile_ayni(self):
        self.assertIsNotNone(self.bolum, f"README'de {README_BOLUM!r} yok")
        teyit_param = isaretli_adlar(self.bloklar, "TEYIT")
        beyan_param = isaretli_adlar(self.bloklar, "BEYAN")
        # iki ayristirici (Copter P5 ve bu dosya) TEYIT'i ayni gorur
        self.assertEqual(teyit_param, self.teyit)
        teyit_readme = readme_listesi(readme_bolumu(self.bolum, README_TEYIT) or "")
        beyan_readme = readme_listesi(readme_bolumu(self.bolum, README_BEYAN) or "")
        self.assertEqual(teyit_readme, teyit_param)
        self.assertEqual(beyan_readme, beyan_param)
        # aktif cikislar sahada gorulmeden yuklendi sayilmaz, kablolamalari beyandir
        aktif = {ad for ad, f in servo_fonksiyonlari(self.p).items() if f != SERVO_KAPALI}
        self.assertTrue(aktif <= teyit_param, sorted(aktif - teyit_param))
        self.assertTrue(aktif <= beyan_param, sorted(aktif - beyan_param))
        self.assertIn("CHUTE_ENABLED", teyit_param)
        for ad in (PARAM_DOSYASI.name, GOREV_DOSYASI.name, KANIT_JSON.name, SITL_YOKLAMA.name,
                   "Load from file"):
            self.assertIn(ad, self.bolum)


class SitlGorevi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.baslik, cls.s, cls.hatalar = waypoint_oku(GOREV_DOSYASI)
        cls.p, _, _, _ = param_oku(PARAM_DOSYASI)

    def test_a17_prova_gorevi_yapi_ve_parasut_tutarliligi(self):
        self.assertEqual(self.baslik, WP_BASLIK)
        self.assertEqual(self.hatalar, [])
        self.assertEqual(gorev_hatalari(self.s, self.p), [])

    def test_a18_sitl_olculemedi_yazili_gecti_yazilmaz(self):
        hukum = [s for s in SITL_YOKLAMA.read_text(encoding="utf-8").splitlines()
                 if s.startswith("HUKUM:")]
        self.assertEqual(len(hukum), 1, hukum)
        self.assertTrue(hukum[0].startswith("HUKUM: OLCULEMEDI"), hukum[0])
        sitl = readme_bolumu(_readme(), README_SITL)
        self.assertIsNotNone(sitl, f"README'de {README_SITL!r} yok")
        self.assertIn("ÖLÇÜLEMEDİ", sitl)
        self.assertNotIn("GEÇTİ", sitl)
        self.assertIn("sim_vehicle.py", sitl)
        self.assertIn("--add-param-file", sitl)
        # SITL parasut benzeticisi, parasut servosunun cikisina bakar
        n = next(SERVO_FUNCTION_DESENI.match(ad).group(1)
                 for ad, f in servo_fonksiyonlari(self.p).items() if f == SERVO_PARASUT)
        self.assertIn(f"SIM_PARA_PIN {n}", sitl)
        # T221-D (D-449): kabul olcutu 1 SITL'de tutabilir; sayi .param'dan hesaplanir
        self.assertEqual(sitl_kabul_hatalari(sitl, self.p, _kanit(),
                                             SITL_YOKLAMA.read_text(encoding="utf-8")), [])


class KaynakBetigi(unittest.TestCase):
    """A19: scripts/ardupilot_param_kaynak.py saf fonksiyonlari, cevrimdisi sentetik kaynakla."""

    SENTETIK = (
        "    // @Param: FOO\n"
        "    // @DisplayName: deneme\n"
        "    // @Values: 0:A,1:B\n"
        "    // @Values{Plane}: 0:A,1:B,5:P\n"
        "\n"
        "    // @User: Standard\n"
        "    GSCALAR(foo, \"FOO\", 0),\n"
    )
    SERI = (
        "    // @Param: 1_PROTOCOL\n"
        "    // @Values: -1:None, 1:MAVLink1, 2:MAVLink2\n"
        "    AP_GROUPINFO(\"1_PROTOCOL\",  1, AP_SerialManager, state[1].protocol, 2),\n"
        "\n"
        "    // @Param: 2_PROTOCOL\n"
        "    // @CopyFieldsFrom: SERIAL1_PROTOCOL\n"
        "    AP_GROUPINFO(\"2_PROTOCOL\",  3, AP_SerialManager, state[2].protocol, 2),\n"
    )

    def test_bloklar_arac_ozel_alan_ve_bos_satir(self):
        b = apk.bloklar(self.SENTETIK)
        self.assertEqual([x["ad"] for x in b], ["FOO"])
        self.assertIn('"FOO"', b[0]["tanim"])
        self.assertEqual(apk.alan_sec(b[0]["alanlar"], "Values", "Plane"), ["0:A,1:B,5:P"])
        self.assertEqual(apk.alan_sec(b[0]["alanlar"], "Values", "Copter"), ["0:A,1:B"])

    def test_deger_denetle_values_bitmask_range(self):
        self.assertTrue(apk.deger_denetle(5, ["0:A,1:B,5:P"], [], [])[0])
        self.assertFalse(apk.deger_denetle(2, ["0:A,1:B,5:P"], [], [])[0])
        gecerli, neden = apk.deger_denetle(65, [], ["0:All,1:X"], [])
        self.assertFalse(gecerli)
        self.assertIn("[6]", neden)
        self.assertFalse(apk.deger_denetle(31, [], [], ["0 30"])[0])
        self.assertTrue(apk.deger_denetle(15, [], [], ["0 30"])[0])

    def test_aday_kaynaklar_onekleri(self):
        self.assertEqual(apk.aday_kaynaklar("SERVO7_FUNCTION", "ArduPlane")[0],
                         ("libraries/SRV_Channel/SRV_Channel.cpp", "FUNCTION"))
        self.assertEqual(apk.aday_kaynaklar("RC_PROTOCOLS", "ArduPlane")[0],
                         ("libraries/RC_Channel/RC_Channels_VarInfo.h", "_PROTOCOLS"))
        self.assertEqual(apk.aday_kaynaklar("CHUTE_ALT_MIN", "ArduPlane")[0],
                         ("libraries/AP_Parachute/AP_Parachute.cpp", "ALT_MIN"))
        self.assertEqual(apk.aday_kaynaklar("TKOFF_THR_MINACC", "ArduPlane"),
                         [("ArduPlane/Parameters.cpp", "TKOFF_THR_MINACC")])

    def test_cozumle_copyfieldsfrom_ve_bulunamayan(self):
        class SahteKaynak:
            def __init__(self, dosyalar):
                self.dosyalar = dosyalar

            def oku(self, yol):
                return self.dosyalar.get(yol)

        kaynak = SahteKaynak({"libraries/AP_SerialManager/AP_SerialManager.cpp": self.SERI})
        k = apk.cozumle("SERIAL2_PROTOCOL", kaynak, "Plane", "ArduPlane")
        self.assertEqual(k["copy_from"], "SERIAL1_PROTOCOL")
        self.assertTrue(k["tanim_eslesti"])
        self.assertTrue(apk.deger_denetle(2, k["values"], k["bitmask"], k["range"])[0])
        self.assertFalse(apk.deger_denetle(3, k["values"], k["bitmask"], k["range"])[0])
        yok = apk.cozumle("NAVITAS_YOK", kaynak, "Plane", "ArduPlane")
        self.assertIsNone(yok["kaynak"])


class DenetleyiciGercektenDuser(unittest.TestCase):
    """Mutasyonlar: bozulmus kopyada ilgili denetleyici DUSER — 'her zaman gecen test' degil."""

    def _kopya(self, kaynak, degistir):
        metin = kaynak.read_text(encoding="utf-8")
        yeni = degistir(metin)
        self.assertNotEqual(metin, yeni, "mutasyon uygulanamadi")
        d = tempfile.mkdtemp()
        yol = Path(d) / kaynak.name
        yol.write_text(yeni, encoding="utf-8")
        return yol

    def _param(self, eski, yeni):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace(f"\n{eski}\n", f"\n{yeni}\n"))
        p, _, hatalar, _ = param_oku(yol)
        self.assertEqual(hatalar, [])
        return p, yol

    def test_m1_gps_hiz_kapisi_acilinca_yakalanir(self):
        p, _ = self._param("TKOFF_THR_MINSPD,0", "TKOFF_THR_MINSPD,4")
        self.assertTrue(any("TKOFF_THR_MINSPD" in h for h in kalkis_hatalari(p)))

    def test_m2_parasut_cikisi_silinince_yakalanir(self):
        p, _ = self._param("SERVO7_FUNCTION,27", "SERVO7_FUNCTION,0")
        self.assertTrue(any("Chute has no channel" in h for h in parasut_hatalari(p)))
        self.assertTrue(any("fonksiyon 27" in h for h in servo_hatalari(p)))

    def test_m3_gaz_cikisi_rudder_yapilinca_yakalanir(self):
        p, _ = self._param("SERVO6_FUNCTION,70", "SERVO6_FUNCTION,21")
        h = servo_hatalari(p)
        self.assertTrue(any(x.startswith("fonksiyon 70: 1 cikis") for x in h), h)
        self.assertTrue(any(x.startswith("fonksiyon 21: 2 cikis") for x in h), h)

    def test_m4_config_h_hiz_varsayilanlari_yakalanir(self):
        p, _ = self._param("AIRSPEED_CRUISE,25", "AIRSPEED_CRUISE,12")
        self.assertNotEqual(hiz_hatalari(p), [])
        varsayilan = {**p, **AIRSPEED_CONFIG_H}
        self.assertTrue(any("AIRSPEED_MIN" in h for h in hiz_hatalari(varsayilan)))

    def test_m5_uzun_failsafe_rtl_yakalanir(self):
        p, _ = self._param("FS_LONG_ACTN,0", "FS_LONG_ACTN,1")
        self.assertTrue(any(h.startswith("FS_LONG_ACTN") for h in failsafe_hatalari(p)))

    def test_m6_bungee_30_gecikmesi_stall_kapisinda_yakalanir(self):
        p, _ = self._param("TKOFF_THR_DELAY,5", "TKOFF_THR_DELAY,30")
        self.assertTrue(any("stall" in h for h in kalkis_hatalari(p)))

    def test_m7_deger_degisip_kanit_yenilenmezse_yakalanir(self):
        p, _ = self._param("CHUTE_ALT_MIN,10", "CHUTE_ALT_MIN,20")
        self.assertTrue(any("kanit bayat" in h for h in kanit_hatalari(p, _kanit())))

    def test_m8_teyit_isareti_silinince_readme_kilidi_kopar(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace(
            "# TEYIT: Pixhawk'ta CHUTE_ENABLED = 1", "# NOT: Pixhawk'ta CHUTE_ENABLED = 1"))
        teyit = isaretli_adlar(yorum_bloklari(yol), "TEYIT")
        bolum = readme_bolumu(readme_bolumu(_readme(), README_BOLUM), README_TEYIT)
        self.assertNotEqual(teyit, readme_listesi(bolum))

    def test_m9_yorumdan_kaynak_dosyasi_silinince_yakalanir(self):
        yol = self._kopya(PARAM_DOSYASI, lambda t: t.replace(
            "# AP_Parachute.cpp @Param ENABLED", "# @Param ENABLED"))
        h = kaynak_atfi_hatalari(yorum_bloklari(yol), _kanit())
        self.assertTrue(any(x.startswith("CHUTE_ENABLED") for x in h), h)

    def test_m10_pil_kritik_eylemi_copter_tablosuyla_yakalanir(self):
        p, _ = self._param("BATT_FS_LOW_ACT,1", "BATT_FS_LOW_ACT,2")
        self.assertTrue(any(h.startswith("BATT_FS_LOW_ACT") for h in pil_hatalari(p)))

    def test_m11_birakma_irtifasi_alt_min_altina_inince_yakalanir(self):
        p, _, _, _ = param_oku(PARAM_DOSYASI)
        yol = self._kopya(GOREV_DOSYASI, lambda t: t.replace(
            "4\t0\t3\t16\t0\t0\t0\t0\t-35.3628118\t149.1674331\t50\t1",
            "4\t0\t3\t16\t0\t0\t0\t0\t-35.3628118\t149.1674331\t5\t1"))
        _, s, hatalar = waypoint_oku(yol)
        self.assertEqual(hatalar, [])
        self.assertTrue(any("CHUTE_ALT_MIN" in h for h in gorev_hatalari(s, p)))

    def _sitl_girdileri(self):
        p, _, _, _ = param_oku(PARAM_DOSYASI)
        return (readme_bolumu(_readme(), README_SITL), p, _kanit(),
                SITL_YOKLAMA.read_text(encoding="utf-8"))

    def test_m12_olcut1_sayisi_elle_yazilinca_yakalanir(self):
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        self.assertEqual(sitl_kabul_hatalari(sitl, p, kanit, yoklama), [])
        # README'deki yuklu sayi bir artirilir (61 -> 62: SITL'de hic tutamayan eski olcut)
        bozuk = re.sub(r"(dosyadaki\s+\**\d+\**\s+addan\s+SITL'de\s+\**)(\d+)",
                       lambda m: f"{m.group(1)}{int(m.group(2)) + 1}", cizilmemis(sitl), count=1)
        self.assertNotEqual(bozuk, cizilmemis(sitl), "mutasyon uygulanamadi")
        self.assertTrue(any(h.startswith("olcut 1: SITL'de yuklu")
                            for h in sitl_kabul_hatalari(bozuk, p, kanit, yoklama)))
        # .param'dan bir ad dusunce README'deki sayilar tutmaz: sayi .param'dan HESAPLANIR
        eksik = {a: v for a, v in p.items() if a != "TKOFF_ACCEL_CNT"}
        self.assertTrue(any(h.startswith("olcut 1")
                            for h in sitl_kabul_hatalari(sitl, eksik, kanit, yoklama)))

    def test_m13_beklenen_yok_bosaltilinca_ya_da_genisletilince_yakalanir(self):
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        desen = r"(beklenen-yok\**\s+listesi\s*=\s*\{)[^}]*\}"
        bos = re.sub(desen, r"\1}", sitl, count=1)
        genis = re.sub(desen, r"\1`BRD_SER2_RTSCTS`, `CHUTE_ENABLED`}", sitl, count=1)
        for bozuk in (bos, genis):
            self.assertNotEqual(bozuk, sitl, "mutasyon uygulanamadi")
            self.assertTrue(any("onceden yazilan" in h
                                for h in sitl_kabul_hatalari(bozuk, p, kanit, yoklama)))

    def test_m14_ikili_taramasi_adi_gosterince_yakalanir(self):
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        goreli = {k["ad"]: k for k in kanit["parametreler"]}["BRD_SER2_RTSCTS"]["goreli_ad"]
        ek = readme_bolumu(yoklama, YOKLAMA_EK)
        self.assertIsNotNone(ek, f"sitl_yoklama.txt'de {YOKLAMA_EK!r} ek tarama blogu yok")
        ek_bozuk = re.sub(rf"^(  {re.escape(goreli)} +)0", r"\g<1>1", ek, count=1, flags=re.M)
        self.assertNotEqual(ek_bozuk, ek, "mutasyon uygulanamadi")
        bozuk = yoklama.replace(ek, ek_bozuk)
        self.assertTrue(any("olcumle celisir" in h
                            for h in sitl_kabul_hatalari(sitl, p, kanit, bozuk)))

    def test_m15_eski_olcut1_cizgisi_kalkinca_ya_da_silinince_yakalanir(self):
        """C2 (curutucu): eski olcut 1'in ~~cizgisi~~ kalkinca SITL'de tutamayan olcut yururluge doner;
        eski metnin silinmesi (FDR) ve cizgi notundaki tarih damgasinin silinmesi de DUSER."""
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        eski = re.search(rf"~~([^~]*?{SITL_ESKI_OLCUT1}[^~]*?)~~", sitl)
        self.assertIsNotNone(eski, "cizili eski olcut 1 yok")
        for bozuk, beklenen in ((sitl.replace(eski.group(0), eski.group(1), 1),
                                 "eski olcut 1 yururlukteki metinde"),
                                (sitl.replace(eski.group(0), "", 1), "~~cizili~~ 0 kez"),
                                (sitl.replace(f"*({SITL_DAMGA}:", "*(D-449:", 1),
                                 "ardinda tarih damgasi yok")):
            self.assertNotEqual(bozuk, sitl, "mutasyon uygulanamadi")
            hatalar = sitl_kabul_hatalari(bozuk, p, kanit, yoklama)
            self.assertTrue(any(beklenen in h for h in hatalar), (beklenen, hatalar))

    def test_m16_chute_on_hukmu_gevsetilince_yakalanir(self):
        """C3/C7 (curutucu): on kayitli 'Olcut 1 DUSER' hukmu gevsetilemez, gerekcesi silinemez;
        celiskili ikinci hukum eklenemez; hukum cumlesi paragraftan cikarilamaz; baslik damgasi silinemez."""
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        for eski, yeni, beklenen in (
                ("Ölçüt 1 **DÜŞER** (`CHUTE_*`", "Ölçüt 1 **ÖLÇÜLEMEDİ** (`CHUTE_*`",
                 "on kayit cumlesi eksik: 'Ölçüt 1 **DÜŞER**"),
                (" (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez)", "",
                 "on kayit cumlesi eksik: 'Ölçüt 1 **DÜŞER**"),
                ("yine ölçülür.", "yine ölçülür. Ölçüt 1 bu durumda ÖLÇÜLEMEDİ sayılır.",
                 "birden cok kez anilmis"),
                ("kaydedilir. Ölçüt 1 **DÜŞER**", "kaydedilir.\n\nÖlçüt 1 **DÜŞER**",
                 "on hukum paragrafinda yok"),
                (f"yoksa ({SITL_DAMGA}):**", "yoksa (D-449):**", "basliginda tarih damgasi yok")):
            self.assertEqual(sitl.count(eski), 1, eski)
            hatalar = sitl_kabul_hatalari(sitl.replace(eski, yeni), p, kanit, yoklama)
            self.assertTrue(any(beklenen in h for h in hatalar), (eski, hatalar))

    def test_m17_olcut1_chute_enabled_ve_acilis_kosulu_silinince_yakalanir(self):
        """C4 (curutucu): olcut 1'den `param show CHUTE_ENABLED` 1 ya da acilis surumu silinemez."""
        sitl, p, kanit, yoklama = self._sitl_girdileri()
        acilis, chute = SITL_OLCUT1_KOSULLARI
        for eski, yeni, kosul in ((f"{acilis}; {chute}; dosyadaki", f"{acilis}; dosyadaki", chute),
                                  (f"{acilis}; {chute}; dosyadaki", f"{chute}; dosyadaki", acilis)):
            self.assertEqual(sitl.count(eski), 1, eski)
            hatalar = sitl_kabul_hatalari(sitl.replace(eski, yeni), p, kanit, yoklama)
            self.assertIn(f"olcut 1 maddesinde {kosul!r} 0 kez (tam 1 olmali)", hatalar)


if __name__ == "__main__":
    unittest.main()
