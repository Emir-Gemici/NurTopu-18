"""İHA renk kodlu bağlantı şeması (Y-3.3.1-M01) — ÖLÇÜLEN topolojiden.

Tek doğruluk kaynağı bu dosyadaki `HATLAR` tablosudur: her hat için nereden →
nereye, tür (renk), düz/kesik ve KAYNAK burada yazılıdır. Aynı tablodan iki
çıktı üretilir:

  FDR/sekiller/iha_baglanti.svg            — 1100 px genişlik, elle yerleşim
  FDR/sekiller/iha_baglanti_kaynaklar.md   — hat başına kaynak tablosu

Kural (gece ön kaydı G6, results/gece_20260907/ON_KAYIT.md): kaynaksız hat
ÇİZİLMEZ; ölçülmemiş hat "DOĞRULANACAK" etiketiyle KESİK çizilir. Düz çizgi
yalnız bir D-kaydı (saha ölçümü) ya da 20260906 parametre dökümüyle desteklenen
hatlar içindir. İKA şeması çizilmez: İKA aviyoniği tedarik edilmemiştir.

Kaynaklar:
  REVIEW_LOG.md D-426 (5 Eylül saha), D-428 (6 Eylül akşam), D-429 §4 (döküm)
  config/pixhawk/arducopter_fda_20260906.param (20:22 dökümü)
  config/pixhawk/arducopter_fda.param (şablon; SERIAL↔TELEM eşlemesi yorumları)
  SAHA_HAZIRLIK_PLANI_20260903.md §2.3 · FDR/BOLUM_5 §5.2.4 · FDR/BOLUM_3 §3.2.1.1
  jetson_paket/JETSON_NANO_KURULUM.md §2.1, §2.4

Kullanım:
  python scripts/fdr_iha_baglanti_svg.py            # iki dosyayı yazar
  python scripts/fdr_iha_baglanti_svg.py --dogrula  # diskteki dosya üretimle aynı mı (0/1)
"""

from __future__ import annotations

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
SVG_YOLU = SEKILLER / "iha_baglanti.svg"
MD_YOLU = SEKILLER / "iha_baglanti_kaynaklar.md"

CIZIM_TARIHI = "2026-09-07"
DOKUM = "config/pixhawk/arducopter_fda_20260906.param"

GENISLIK = 1100
YUKSEKLIK = 900

# ── Renk sözlüğü — legend ile hatlar aynı sözlükten okur ─────────────────────
RENK = {
    "guc": "#c62828",      # güç + (kırmızı)
    "guc_gnd": "#212121",  # güç − / GND (siyah)
    "pwm": "#ef6c00",      # PWM sinyal (turuncu)
    "uart": "#1565c0",     # UART (mavi)
    "i2c": "#6a1b9a",      # I2C (mor)
    "csi": "#2e7d32",      # CSI şerit (yeşil)
    "rc": "#f9a825",       # RC iBUS (sarı)
    "gpio": "#616161",     # emniyet düğmesi GPIO (gri)
}
RENK_ADI = {
    "guc": "güç + (kırmızı)",
    "guc_gnd": "güç − / GND (siyah)",
    "pwm": "PWM sinyal (turuncu)",
    "uart": "UART (mavi)",
    "i2c": "I2C (mor)",
    "csi": "CSI şerit (yeşil)",
    "rc": "RC iBUS (sarı)",
    "gpio": "emniyet düğmesi GPIO (gri)",
}
KESIK_DESEN = "8,5"
DOGRULANACAK = "DOĞRULANACAK"

# ── Hatlar: tek doğruluk kaynağı ─────────────────────────────────────────────
# id · ad · nereden · nereye · durum · kaynak · cizgiler: [(tür, [(x,y),...], kalınlık)]
# Kesik çizgi = durum "DOĞRULANACAK" ile başlar (üretici bundan türetir).
HATLAR = [
    dict(
        id="H01", ad="Ana güç: pil → PM06",
        nereden="4S LiPo 10 Ah (fiş XT60/XT90 — hangisi olduğu BEYAN GEREKLİ)",
        nereye="PM06 güç modülü girişi",
        durum="ÖLÇÜLDÜ (pil takılı; PreArm pil uyarısı kayboldu)",
        kaynak="D-426 §1 (18:03 pil takıldı, `PreArm: Battery 1 low voltage failsafe` listeden kayboldu); "
               "fiş tipi: FDR BOLUM_5 §5.2.4 ve BOLUM_3 §3.2.1.1 'XT60/XT90' — tek tip beyan edilmedi",
        cizgiler=[("guc", [(110, 260), (110, 300)], 3), ("guc_gnd", [(140, 260), (140, 300)], 3)],
    ),
    dict(
        id="H02", ad="PM06 → Pixhawk POWER1 (6-pin: 5 V · GND · V/I sens)",
        nereden="PM06", nereye="Pixhawk 6C `POWER1`",
        durum="ÖLÇÜLDÜ (6 pinli kablo; pil gerilimi MP ↔ multimetre 15,8 V)",
        kaynak="D-426 §1 (18:03 satırı: pil takıldı, PM06 → POWER1 çalışıyor), D-426 §2 (8 pinli kablo uymadı, 6 pinli takıldı, "
               "uydurma adaptör yapılmadı); D-428 §1 (MP 15,8 ↔ multimetre 15,8 V); "
               "param:BATT_MONITOR,4 · param:BATT_VOLT_PIN,8 · param:BATT_CURR_PIN,4",
        cizgiler=[("guc", [(210, 331), (400, 331)], 3), ("guc_gnd", [(210, 341), (400, 341)], 3)],
    ),
    dict(
        id="H03", ad="PM06 çıkışı → FCHUB-12S V2 (PDB)",
        nereden="PM06 çıkış", nereye="FCHUB-12S V2 pil pad'leri",
        durum=f"{DOGRULANACAK} — D-426/428/429'da FCHUB anılmıyor; PM06 çıkışının ESC'lere yolu ölçülmedi",
        kaynak="SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Ana güç' satırı; FDR BOLUM_5 §5.2.4 'Ana güç' satırı "
               "(plan, ölçüm değil)",
        cizgiler=[("guc", [(110, 370), (110, 410)], 3)],
    ),
    dict(
        id="H04", ad="FCHUB → ESC ×4 güç (+/−)",
        nereden="FCHUB-12S V2", nereye="4× ESC güç girişi",
        durum=f"{DOGRULANACAK} — motor testi koştu (D-426 §1 18:06) ama ESC'lerin hangi noktadan beslendiği tutanakta yok",
        kaynak="SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Ana güç' satırı; FDR BOLUM_5 §5.2.4; "
               "BOLUM_3 §3.3.2.1 'doğrulanacak bağlantılar' (künyeden, ölçüm değil)",
        cizgiler=[("guc", [(210, 445), (390, 445), (390, 705), (405, 705)], 3)],
    ),
    dict(
        id="H05", ad="FCHUB pil pad'i → UBEC 5 V / 5 A",
        nereden="FCHUB-12S V2 pad", nereye="UBEC girişi",
        durum=f"{DOGRULANACAK} — Jetson ve UBEC sahada takılı değil (D-426 §4 'Jetson takılı DEĞİL')",
        kaynak="SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson güç' satırı; FDR BOLUM_3 §3.2.1.1 'Jetson beslemesi'; "
               "D-426 §4 (Jetson takılı değil)",
        cizgiler=[("guc", [(110, 480), (110, 500), (22, 500), (22, 885), (900, 885), (900, 756)], 3)],
    ),
    dict(
        id="H06", ad="UBEC → Jetson Nano J25 barrel (+ J48 jumper)",
        nereden="UBEC 5 V / 5 A çıkışı", nereye="Nano `J25` barrel jack; `J48` jumper takılı; ortak GND",
        durum=f"{DOGRULANACAK} — Nano kurulumu ve güç ölçümü yok",
        kaynak="jetson_paket/JETSON_NANO_KURULUM.md §2.1 (barrel 5 V/≥ 4 A + J48); FDR BOLUM_3 §3.2.1.1; "
               "SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson güç' (5,0–5,2 V yük altında — ÖLÇÜLEMEDİ)",
        cizgiler=[("guc", [(900, 708), (900, 540)], 3)],
    ),
    dict(
        id="H07", ad="ESC sinyal ×4 → Pixhawk AUX1–4 (adaptör kartı üzerinden)",
        nereden="4× ESC sinyal teli", nereye="Pixhawk 6C FMU PWM OUT `AUX1..AUX4` = `SERVO9..12`",
        durum="ÖLÇÜLDÜ (döküm + pervanesiz motor testi + tlog)",
        kaynak="D-428 §1 ESC künyesi (3 telli fiş, Pixhawk ile gelen 'PWM IN / PWM OUT' adaptörü üzerinden AUX); "
               "D-428 §5d (AUX 1–4 = M4, M2, M1, M3); D-429 §1 (tlog: AUX1=M4 sağ arka · AUX2=M2 sol arka · "
               "AUX3=M1 sağ ön · AUX4=M3 sol ön); "
               "param:SERVO9_FUNCTION,36 · param:SERVO10_FUNCTION,34 · param:SERVO11_FUNCTION,33 · "
               "param:SERVO12_FUNCTION,35 · param:MOT_PWM_TYPE,0 · param:RC_SPEED,490 (D-429 §4: 400 yazılacak)",
        cizgiler=[("pwm", [(440, 650), (440, 540)], 2.5), ("pwm", [(520, 650), (520, 540)], 2.5),
                  ("pwm", [(600, 650), (600, 540)], 2.5), ("pwm", [(680, 650), (680, 540)], 2.5)],
    ),
    dict(
        id="H08", ad="ESC BEC 5 V ×4 → Pixhawk servo rayı (paralel)",
        nereden="4× ESC kırmızı tel (BEC 5 V / 5 A)", nereye="Pixhawk AUX servo rayı (+5 V)",
        durum="ÖLÇÜLDÜ (4 kırmızı tel rayda paralel) — karar: 3'ü çıkarılacak, yapılmadı",
        kaynak="D-428 §1 (3 telli fiş, BEC 5 V/5 A); D-428 §5f (4 BEC paralel, ertelendi); "
               "D-429 §4 'ESC BEC: 4 kırmızı tel rayda paralel — 3'ü çıkar'",
        cizgiler=[("guc", [(708, 650), (708, 540)], 1.5)],
    ),
    dict(
        id="H09", ad="ESC → motor 3 faz ×4 (5008 340 KV)",
        nereden="4× ESC", nereye="M1 sağ ön · M2 sol arka · M3 sol ön · M4 sağ arka (quad-X)",
        durum="ÖLÇÜLDÜ (motor testi koştu); sıra/yön 4/4 BEYAN — video yok; M1 hasarlı",
        kaynak="D-426 §1 (18:06 `starting motor test` → `finished motor test`; ~18:30 sıra/yön 4/4 BEYAN, video BEYAN GEREKLİ); "
               "D-429 §2 madde 4 (M1 sağ ön hasarlı) ve §6 madde 2 (motor yönü videosuz doğru sayılmaz); "
               "yerleşim: FDR BOLUM_5 §5.2.3 (1 sağ ön CCW, 2 sol arka CCW, 3 sol ön CW, 4 sağ arka CW); "
               "param:FRAME_CLASS,1 · param:FRAME_TYPE,1",
        cizgiler=[("guc", [(440, 710), (440, 749)], 3), ("guc", [(520, 710), (520, 749)], 3),
                  ("guc", [(600, 710), (600, 749)], 3), ("guc", [(680, 710), (680, 749)], 3)],
    ),
    dict(
        id="H10", ad="M9N GPS → Pixhawk GPS1 (UART)",
        nereden="Holybro M9N u-blox", nereye="Pixhawk 6C `GPS1` seri hattı",
        durum="ÖLÇÜLDÜ (modül tanındı; 18 uydu, EKF GPS kullanıyor)",
        kaynak="D-426 §1 (15:38 `u-blox 1 HW: 000A0000 SW: ROM SPG 5.10`); D-428 §1 GPS/EKF satırı "
               "(18 uydu, `EKF3 IMU0/IMU1 is using GPS`); param:GPS_TYPE,1 · param:SERIAL3_PROTOCOL,5",
        cizgiler=[("uart", [(545, 145), (545, 200)], 2.5)],
    ),
    dict(
        id="H11", ad="M9N pusula → Pixhawk GPS1 (I2C, harici)",
        nereden="M9N üstündeki pusula", nereye="Pixhawk 6C `GPS1` I2C hattı",
        durum="ÖLÇÜLDÜ (harici pusula dökümde; iki kalibrasyon, ofset < 300)",
        kaynak="param:COMPASS_EXTERNAL,1 · param:COMPASS_DEV_ID,658953 (dev-id 0xA0E09, düşük 3 bit = 1 = I2C "
               "veri yolu — ArduPilot DeviceId kodlaması, hesap); D-428 §1 pusula satırı (OFS/OFS2 < 300, "
               "ikinci kalibrasyon PreArm temiz); D-429 §4 (`COMPASS_ORIENT` 6, direkte 90° dönük)",
        cizgiler=[("i2c", [(575, 145), (575, 200)], 2.5)],
    ),
    dict(
        id="H12", ad="Emniyet düğmesi (M9N üstü) → Pixhawk GPS1 (GPIO)",
        nereden="M9N üstündeki emniyet düğmesi", nereye="Pixhawk 6C `GPS1` düğme/LED hattı",
        durum="ÖLÇÜLDÜ (düğme fiziksel olarak çözüldü; PreArm satırı kayboldu)",
        kaynak="D-426 §1 (18:05 `PreArm: Hardware safety switch` kayboldu; öncesinde 12× `Motor Test: Safety switch`); "
               "D-426 §2 (düğme M9N üstünde, `BRD_SAFETY_DEFOFF` değiştirilmedi); param:BRD_SAFETY_DEFLT,1",
        cizgiler=[("gpio", [(605, 145), (605, 200)], 2.5)],
    ),
    dict(
        id="H13", ad="Pixhawk GPS1 → M9N besleme (5 V)",
        nereden="Pixhawk 6C `GPS1` 5 V", nereye="M9N",
        durum="ÖLÇÜLDÜ dolaylı: modül yalnız GPS1 kablosuyla bağlıyken tanındı; ayrı besleme yok",
        kaynak="D-426 §1 (15:38 modül tanındı); SAHA_HAZIRLIK_PLANI_20260903.md §2.3 ve FDR BOLUM_3 §3.3.1.1.7 "
               "(M9N için ayrı güç satırı yok)",
        cizgiler=[("guc", [(515, 200), (515, 145)], 2)],
    ),
    dict(
        id="H14", ad="Pixhawk TELEM1 → SiK 433 MHz (UART, MAVLink2 57600)",
        nereden="Pixhawk 6C `TELEM1` (= SERIAL1)", nereye="SiK telemetri modülü (RF ↔ YKS SiK, USB)",
        durum="DÖKÜM (SERIAL1) · fiziksel bağlantı BEYAN — RTT / paket kaybı ÖLÇÜLEMEDİ",
        kaynak="param:SERIAL1_PROTOCOL,2 · param:SERIAL1_BAUD,57; şablon config/pixhawk/arducopter_fda.param "
               "yorumu 'SERIAL1 = UART7 = TELEM1'; D-426 §1 (~18:45 SiK bağlandı, BEYAN); "
               "SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Telemetri' (JST-GH 6 pin, TX↔RX çapraz)",
        cizgiler=[("uart", [(720, 280), (760, 280)], 2.5)],
    ),
    dict(
        id="H15", ad="Pixhawk TELEM2 → Jetson Nano UART (3 tel, 3,3 V; 5 V BAĞLI DEĞİL)",
        nereden="Pixhawk 6C `TELEM2` (= SERIAL2) TX/RX/GND",
        nereye="Nano 40-pin `/dev/ttyTHS1`: pin 8 TX · pin 10 RX · pin 6 GND",
        durum=f"{DOGRULANACAK} — parametre dökümde hazır; Jetson sahada takılmadı",
        kaynak="param:SERIAL2_PROTOCOL,2 · param:SERIAL2_BAUD,57 · param:BRD_SER2_RTSCTS,0; şablon "
               "config/pixhawk/arducopter_fda.param yorumu 'SERIAL2 = UART5 = TELEM2'; FDR BOLUM_3 §3.2.1.1 "
               "'Pixhawk ↔ Jetson bağlantısı'; SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Jetson ↔ Pixhawk'; "
               "D-426 §4 (Jetson takılı DEĞİL)",
        cizgiler=[("uart", [(720, 470), (760, 470)], 2.5)],
    ),
    dict(
        id="H16", ad="FS-iA6B `i-BUS SERVO` → Pixhawk `PPM/SBUS RC` (iBUS)",
        nereden="FS-iA6B alıcı `i-BUS SERVO` portu (CH1–CH6 DEĞİL)", nereye="Pixhawk 6C `PPM/SBUS RC`",
        durum="ÖLÇÜLDÜ (`RCInput: decoding IBUS(1)`) — ⚠ RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ",
        kaynak="D-426 §1 (18:03 `RCInput: decoding IBUS(1)`); D-426 §2 (alıcı önce `CH6`'daydı, `i-BUS SERVO`'ya alındı); "
               "SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'RC' satırı (5-pin JST-GH, `PPM/SBUS RC`); "
               "param:RC_PROTOCOLS,1; D-428 §2 (kumanda kapatılınca `Radio Failsafe` gelmedi)",
        cizgiler=[("rc", [(760, 370), (720, 370)], 2.5)],
    ),
    dict(
        id="H17", ad="RPi HQ kamera → Jetson Nano CSI (IMX477 şerit)",
        nereden="Raspberry Pi HQ kamera (IMX477)", nereye="Nano CSI konnektörü (mavi taraf dışa, kilit kapalı)",
        durum=f"{DOGRULANACAK} — Nano kurulumu ve `jetson-io` overlay'i yapılmadı",
        kaynak="jetson_paket/JETSON_NANO_KURULUM.md §2.4 (IMX477 overlay, şerit yönü); "
               "SAHA_HAZIRLIK_PLANI_20260903.md §2.3 'Kamera' satırı; FDR BOLUM_3 §3.2.1.1 kamera satırı",
        cizgiler=[("csi", [(930, 480), (960, 480)], 2.5)],
    ),
]

# ── Çizilmeyenler (bilerek) ──────────────────────────────────────────────────
CIZILMEYENLER = [
    "**İKA bağlantı şeması** — İKA aviyoniği tedarik edilmedi (FDR BOLUM_3 §3.2.2); çizilecek ölçülmüş topoloji yok.",
    "**Pixhawk USB** (SERIAL0) — yalnız tezgâh/ESC kalibrasyonu (D-428 §3), uçuş bağlantısı değil.",
    "**Kablo kesitleri, uzunlukları, konnektör tipleri** — ÖLÇÜLMEDİ (FDR BOLUM_5 §5.2.5, BEYAN GEREKLİ).",
    "**Pixhawk MAIN 1–8 ve AUX 5–8** — fiziksel bağlantı yok; dökümde başıboş motor fonksiyonları var, "
    "0'lanacak (D-428 §5d, D-429 §4).",
    "**GPS1 kablosundaki LED / buzzer telleri** — tutanakta ölçüm yok.",
]

TUTARSIZLIKLAR = [
    "FDR BOLUM_3 §3.3.1.1.7 ASCII topolojisi ve BOLUM_5 §5.2.4 'ESC sinyal' satırı **`MAIN 1..4`** yazar; "
    "döküm ve D-428 §5d **AUX 1–4 (`SERVO9–12`)** diyor. Bu şema dökümü esas alır; metinler düzeltilmelidir.",
    "SAHA_HAZIRLIK_PLANI_20260903.md §2.3 ve §0.2 hâlâ **PM02** ve **`MAIN OUT 1–4`** yazar (D-426 §3: PM06; D-428 §5d: AUX).",
    "Şablon config/pixhawk/arducopter_fda.param `RC_SPEED` yorumu 'PWM 400 Hz (MAIN 1-4)' — döküm 490, karar 400 (D-429 §4).",
]


# ── SVG yardımcıları ─────────────────────────────────────────────────────────
def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def _kutu(x, y, w, h, satirlar, kesik=False, dolgu="#ffffff", kenar="#37474f", r=6, boyut=12.5):
    dash = f' stroke-dasharray="{KESIK_DESEN}"' if kesik else ""
    out = [f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{dolgu}" '
           f'stroke="{kenar}" stroke-width="1.6"{dash}/>']
    cx = x + w / 2
    n = len(satirlar)
    adim = boyut + 3.5
    y0 = y + h / 2 - (n - 1) * adim / 2 + boyut * 0.35
    for i, s in enumerate(satirlar):
        agirlik = ' font-weight="bold"' if i == 0 else ""
        b = boyut if i == 0 else boyut - 1.5
        out.append(f'  <text x="{cx:.0f}" y="{y0 + i * adim:.1f}" text-anchor="middle" '
                   f'font-size="{b}"{agirlik}>{_esc(s)}</text>')
    return "\n".join(out)


def _metin(x, y, s, boyut=11, anchor="start", renk="#263238", agirlik=None, ek=""):
    a = f' font-weight="{agirlik}"' if agirlik else ""
    return (f'  <text x="{x}" y="{y}" text-anchor="{anchor}" font-size="{boyut}" '
            f'fill="{renk}"{a}{ek}>{_esc(s)}</text>')


def _hat_cizgileri(h) -> str:
    kesik = h["durum"].startswith(DOGRULANACAK)
    dash = f' stroke-dasharray="{KESIK_DESEN}"' if kesik else ""
    out = []
    for tur, noktalar, kalinlik in h["cizgiler"]:
        pts = " ".join(f"{x},{y}" for x, y in noktalar)
        out.append(f'  <polyline class="hat" data-hat="{h["id"]}" data-tur="{tur}" points="{pts}" '
                   f'fill="none" stroke="{RENK[tur]}" stroke-width="{kalinlik}" '
                   f'stroke-linejoin="round" stroke-linecap="round"{dash}/>')
    return "\n".join(out)


def _legend(x, y):
    out = [f'  <g id="legend">',
           f'  <rect x="{x}" y="{y}" width="330" height="262" rx="6" fill="#fafafa" stroke="#90a4ae" stroke-width="1"/>',
           _metin(x + 12, y + 20, "Açıklama", 13, agirlik="bold")]
    yy = y + 40
    for tur in ["guc", "guc_gnd", "pwm", "uart", "i2c", "csi", "rc", "gpio"]:
        out.append(f'  <line data-hat="{tur}" x1="{x + 14}" y1="{yy - 4}" x2="{x + 54}" y2="{yy - 4}" '
                   f'stroke="{RENK[tur]}" stroke-width="3.5" stroke-linecap="round"/>')
        out.append(_metin(x + 64, yy, RENK_ADI[tur], 11))
        yy += 22
    yy += 4
    out.append(f'  <line x1="{x + 14}" y1="{yy - 4}" x2="{x + 54}" y2="{yy - 4}" stroke="#263238" stroke-width="2.5"/>')
    out.append(_metin(x + 64, yy, "düz: ölçüm (D-kaydı) ya da 20260906 dökümü", 10))
    yy += 22
    out.append(f'  <line x1="{x + 14}" y1="{yy - 4}" x2="{x + 54}" y2="{yy - 4}" stroke="#263238" '
               f'stroke-width="2.5" stroke-dasharray="{KESIK_DESEN}"/>')
    out.append(_metin(x + 64, yy, f"kesik: {DOGRULANACAK} (plan/künye, ölçüm yok)", 10))
    out.append("  </g>")
    return "\n".join(out)


def svg_uret() -> str:
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{GENISLIK}" height="{YUKSEKLIK}" '
             f'viewBox="0 0 {GENISLIK} {YUKSEKLIK}" font-family="Segoe UI, DejaVu Sans, Arial, sans-serif" '
             f'fill="#263238">')
    p.append("  <title>İHA bağlantı şeması — ölçülen topoloji (D-426/428/429, döküm 20260906)</title>")
    p.append(f"  <desc>Üreten: scripts/fdr_iha_baglanti_svg.py · çizim {CIZIM_TARIHI} · her hat için kaynak: "
             f"FDR/sekiller/iha_baglanti_kaynaklar.md</desc>")
    p.append(f'  <rect x="0" y="0" width="{GENISLIK}" height="{YUKSEKLIK}" fill="#ffffff"/>')

    # Başlık
    p.append(_metin(40, 32, "İHA bağlantı şeması — ölçülen topoloji (çizim 7 Eylül 2026)", 18, agirlik="bold"))
    p.append(_metin(40, 52, "Kaynak: REVIEW_LOG D-426 / D-428 / D-429 · parametre dökümü "
                    "config/pixhawk/arducopter_fda_20260906.param · hat başına kaynak: "
                    "FDR/sekiller/iha_baglanti_kaynaklar.md", 10.5, renk="#455a64"))

    # Okuma kılavuzu (sağ üst)
    p.append('  <rect x="760" y="75" width="320" height="150" rx="6" fill="#fff8e1" stroke="#ffb300" stroke-width="1"/>')
    p.append(_metin(772, 95, "Okuma kılavuzu", 12.5, agirlik="bold"))
    notlar = [
        "• Düz çizgi: ölçüm (D-kaydı) ya da 20260906 dökümü",
        f"• Kesik çizgi: {DOGRULANACAK} — yalnız plan/künye",
        "• ESC çıkışları AUX1–4 (SERVO9–12); MAIN 1–8 boş —",
        "  başıboş motor fonksiyonları 0'lanacak (D-428 §5d)",
        "• ⚠ RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ (D-428 §2)",
        "• İKA şeması yok: İKA aviyoniği tedarik edilmedi",
        "• Kablo kesiti / konnektör tipi ÖLÇÜLMEDİ (§5.2.5)",
    ]
    for i, s in enumerate(notlar):
        p.append(_metin(772, 113 + i * 15.5, s, 10.5))

    # ── Bileşen kutuları ──
    p.append(_kutu(40, 190, 170, 70, ["4S LiPo 10 Ah", "fiş XT60/XT90 —", "BEYAN GEREKLİ"]))
    p.append(_kutu(40, 300, 170, 70, ["PM06 güç modülü", "V/I sensör → POWER1", "(plan PM02; D-426 §3)"]))
    p.append(_kutu(40, 410, 170, 70, ["FCHUB-12S V2 (PDB)", DOGRULANACAK, "(D-426'da anılmıyor)"], kesik=True, dolgu="#fafafa"))
    p.append(_kutu(430, 75, 260, 70, ["Holybro M9N (direk üstü)", "GPS u-blox · pusula (harici, I2C)", "emniyet düğmesi üstünde"]))
    p.append('  <circle cx="672" cy="88" r="6" fill="#616161" stroke="#263238" stroke-width="1"/>')
    p.append(_kutu(400, 200, 320, 340, [], dolgu="#e3f2fd", kenar="#1565c0"))
    p.append(_metin(560, 242, "Pixhawk 6C — ArduCopter 4.5.7 (D-425)", 13, anchor="middle", agirlik="bold"))
    p.append(_metin(560, 259, "QUAD/X (FRAME_CLASS=1, FRAME_TYPE=1)", 11, anchor="middle"))
    # Pixhawk port etiketleri
    p.append(_metin(408, 325, "POWER1", 11, agirlik="bold"))
    p.append(_metin(625, 213, "GPS1", 11, agirlik="bold"))
    p.append(_metin(712, 274, "TELEM1", 11, anchor="end", agirlik="bold"))
    p.append(_metin(712, 364, "PPM/SBUS RC", 11, anchor="end", agirlik="bold"))
    p.append(_metin(712, 464, "TELEM2", 11, anchor="end", agirlik="bold"))
    p.append(_metin(560, 505, "FMU PWM OUT (AUX) — 4 çıkış kullanımda", 10.5, anchor="middle"))
    for i, x in enumerate([440, 520, 600, 680], start=1):
        p.append(_metin(x, 530, f"AUX{i}", 11, anchor="middle", agirlik="bold"))
    # GPS1 demeti etiketi
    p.append(_metin(618, 168, "GPS1 demeti: 5 V · UART (GPS) ·", 10))
    p.append(_metin(618, 181, "I2C (pusula) · düğme GPIO", 10))
    p.append(_metin(618, 194, "(D-426 §1 15:38 · 18:05)", 9.5, renk="#455a64"))
    # PM06→POWER1 etiketi
    p.append(_metin(305, 322, "6-pin: 5 V · GND · V/I sens (D-426 §2)", 10, anchor="middle"))
    p.append(_metin(305, 356, "15,8 V MP ↔ multimetre (D-428 §1)", 9.5, anchor="middle", renk="#455a64"))
    # Pil→PM06 etiketleri
    p.append(_metin(158, 285, "+ / −", 10))
    # FCHUB→ESC etiketi
    p.append(_metin(225, 437, f"ESC güç ×4 ({DOGRULANACAK})", 10))
    # UBEC hattı etiketi
    p.append(_metin(40, 877, f"FCHUB pad → UBEC girişi ({DOGRULANACAK}; plan §2.3)", 9.5, renk="#455a64"))

    # Adaptör kartı
    p.append('  <rect x="415" y="580" width="290" height="26" rx="4" fill="#eceff1" stroke="#78909c" stroke-width="1"/>')
    p.append(_metin(560, 597, "PWM adaptör kartı — Pixhawk ile gelen \"PWM IN / PWM OUT\" (D-428 §1)", 9.5, anchor="middle"))
    # SERVO fonksiyon etiketleri
    for x, s, m in [(440, "SERVO9=36", "M4"), (520, "SERVO10=34", "M2"),
                    (600, "SERVO11=33", "M1"), (680, "SERVO12=35", "M3")]:
        p.append(_metin(x, 622, s, 9.5, anchor="middle"))
        p.append(_metin(x, 634, f"→ {m}", 9.5, anchor="middle"))
    # BEC etiketi
    p.append(_metin(714, 556, "BEC 5 V ×4 paralel (servo rayı)", 9.5, renk=RENK["guc"]))
    p.append(_metin(714, 568, "D-429 §4: 3'ü çıkarılacak", 9.5, renk=RENK["guc"]))
    # ESC kutuları
    for x in [405, 485, 565, 645]:
        p.append(_kutu(x, 650, 70, 60, ["ESC", "60A V2"], boyut=11.5))
    p.append(_metin(728, 660, "ESC ×4: Hobbywing", 10))
    p.append(_metin(728, 673, "Skywalker 60A V2", 10))
    p.append(_metin(728, 686, "3 telli: sinyal · BEC · GND", 9.5))
    p.append(_metin(728, 699, "(D-428 §1)", 9.5, renk="#455a64"))
    # Motorlar
    for x, ad, konum in [(440, "M4", "sağ arka · CW"), (520, "M2", "sol arka · CCW"),
                         (600, "M1", "sağ ön · CCW"), (680, "M3", "sol ön · CW")]:
        p.append(f'  <circle cx="{x}" cy="775" r="26" fill="#ffffff" stroke="#37474f" stroke-width="1.6"/>')
        p.append(_metin(x, 780, ad, 12.5, anchor="middle", agirlik="bold"))
        p.append(_metin(x, 818, konum, 10, anchor="middle"))
    p.append(_metin(560, 833, "5008 340 KV ×4 · yerleşim plan (BOLUM_5 §5.2.3) · yön BEYAN, video yok (D-429 §6) · M1 hasarlı (D-429 §2)",
                    9.5, anchor="middle", renk="#455a64"))
    p.append(_metin(692, 735, "3 faz ×4", 10))

    # Sağ sütun
    p.append(_kutu(760, 250, 320, 60, ["SiK 433 MHz telemetri", "TELEM1 · MAVLink2 57600 (SERIAL1) · RF ↔ YKS SiK (USB)"], boyut=12))
    p.append(_kutu(760, 340, 320, 60, ["FS-iA6B alıcı (iBUS) ← kumanda FS-i6 (RF)", "i-BUS SERVO → PPM/SBUS RC · RC_PROTOCOLS=1"], boyut=12))
    p.append(_kutu(760, 420, 170, 120, ["Jetson Nano 4GB", "UART /dev/ttyTHS1", "pin 8 TX · 10 RX · 6 GND", "3,3 V — 5 V BAĞLI DEĞİL", "J25 barrel · J48 jumper"], boyut=11.5))
    p.append(_kutu(960, 420, 120, 120, ["RPi HQ kamera", "IMX477", "CSI şerit", DOGRULANACAK], kesik=True, dolgu="#fafafa", boyut=11.5))
    p.append(_kutu(760, 708, 170, 48, ["UBEC 5 V / 5 A", DOGRULANACAK], kesik=True, dolgu="#fafafa", boyut=11.5))
    p.append(_metin(740, 262, "UART", 9, anchor="middle", renk=RENK["uart"]))
    p.append(_metin(740, 386, "iBUS", 9, anchor="middle", renk="#8d6e00"))
    p.append(_metin(740, 452, "UART", 9, anchor="middle", renk=RENK["uart"]))
    p.append(_metin(740, 492, DOGRULANACAK, 8.5, anchor="middle", renk=RENK["uart"]))
    p.append(_metin(945, 470, "CSI", 9, anchor="middle", renk=RENK["csi"]))
    p.append(_metin(912, 610, "J25 + J48", 9.5, renk=RENK["guc"]))
    p.append(_metin(912, 623, DOGRULANACAK, 8.5, renk=RENK["guc"]))

    # ── Hatlar ──
    p.append("  <!-- Hatlar: her polyline data-hat ile iha_baglanti_kaynaklar.md tablosuna bağlıdır -->")
    for h in HATLAR:
        p.append(f"  <!-- {h['id']} {h['ad']} -->")
        p.append(_hat_cizgileri(h))

    p.append(_legend(50, 530))
    p.append("</svg>")
    return "\n".join(p) + "\n"


def md_uret() -> str:
    o = []
    o.append("# İHA bağlantı şeması — hat başına kaynak")
    o.append("")
    o.append(f"Şema: `iha_baglanti.svg` (çizim {CIZIM_TARIHI}; üreten `scripts/fdr_iha_baglanti_svg.py`, "
             "iki dosya aynı tablodan çıkar). Yönerge Y-3.3.1-M01.")
    o.append("")
    o.append("**Kural:** kaynaksız hat çizilmez. **Düz çizgi** = bir D-kaydındaki saha ölçümü ya da "
             f"`{DOKUM}` dökümü. **Kesik çizgi** = `{DOGRULANACAK}`: yalnız plan/künyeden bilinen, "
             "sahada ölçülmemiş hat. `param:AD,DEĞER` atıfları dökümdeki satırın birebir kopyasıdır.")
    o.append("")
    o.append("**Kaynak belgeler:** `REVIEW_LOG.md` D-426 (5 Eylül saha tutanağı), D-428 (6 Eylül akşam tutanağı), "
             "D-429 §4 (dökümden plan dışı değerler); `config/pixhawk/arducopter_fda_20260906.param` (6 Eylül 20:22 dökümü); "
             "`config/pixhawk/arducopter_fda.param` (şablon, SERIAL↔TELEM eşleme yorumları); "
             "`SAHA_HAZIRLIK_PLANI_20260903.md` §2.3; `FDR/BOLUM_5_URETIM_FAALIYETLERI.md` §5.2.3–§5.2.5; "
             "`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` §3.2.1.1; `jetson_paket/JETSON_NANO_KURULUM.md` §2.1, §2.4.")
    o.append("")
    o.append("## Renk sözlüğü")
    o.append("")
    o.append("| tür | renk | hex |")
    o.append("|---|---|---|")
    for tur in ["guc", "guc_gnd", "pwm", "uart", "i2c", "csi", "rc", "gpio"]:
        o.append(f"| `{tur}` | {RENK_ADI[tur]} | `{RENK[tur]}` |")
    o.append("")
    o.append("## Hatlar")
    o.append("")
    o.append("| hat | ad | nereden → nereye | tür | durum | kaynak |")
    o.append("|---|---|---|---|---|---|")
    for h in HATLAR:
        turler = " + ".join(dict.fromkeys(t for t, _, _ in h["cizgiler"]))
        o.append(f"| {h['id']} | {h['ad']} | {h['nereden']} → {h['nereye']} | `{turler}` | {h['durum']} | {h['kaynak']} |")
    o.append("")
    o.append("## Çizilmeyenler (bilerek)")
    o.append("")
    for s in CIZILMEYENLER:
        o.append(f"- {s}")
    o.append("")
    o.append("## Bilinen metin tutarsızlıkları (şema dökümü esas alır)")
    o.append("")
    for s in TUTARSIZLIKLAR:
        o.append(f"- {s}")
    o.append("")
    o.append("## Sayım")
    o.append("")
    n_kesik = sum(1 for h in HATLAR if h["durum"].startswith(DOGRULANACAK))
    o.append(f"- Hat: **{len(HATLAR)}** · düz (ölçüm/döküm): **{len(HATLAR) - n_kesik}** · kesik ({DOGRULANACAK}): **{n_kesik}**")
    o.append("- İKA şeması: **çizilmedi** (aviyonik yok).")
    o.append("")
    return "\n".join(o)


def uret() -> tuple[str, str]:
    return svg_uret(), md_uret()


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    svg, md = uret()
    if "--dogrula" in argv:
        farkli = []
        for yol, icerik in [(SVG_YOLU, svg), (MD_YOLU, md)]:
            if not yol.is_file() or yol.read_text(encoding="utf-8").replace("\r\n", "\n") != icerik:
                farkli.append(str(yol.relative_to(KOK)))
        if farkli:
            print("FARKLI:", ", ".join(farkli))
            return 1
        print("AYNI:", SVG_YOLU.relative_to(KOK), MD_YOLU.relative_to(KOK))
        return 0
    SEKILLER.mkdir(parents=True, exist_ok=True)
    SVG_YOLU.write_text(svg, encoding="utf-8", newline="\n")
    MD_YOLU.write_text(md, encoding="utf-8", newline="\n")
    print(f"YAZILDI {SVG_YOLU.relative_to(KOK)} ({len(svg)} B) · {MD_YOLU.relative_to(KOK)} ({len(md)} B) · "
          f"hat {len(HATLAR)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
