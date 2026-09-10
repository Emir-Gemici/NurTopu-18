"""İKA renk kodlu bağlantı şeması (Y-3.3.1-M01) — DDR TASARIMINDAN, tedarik yok.

Tek doğruluk kaynağı bu dosyadaki `HATLAR` tablosudur: her hat için nereden →
nereye, tür (renk), durum ve KAYNAK burada yazılıdır. Aynı tablodan iki çıktı
üretilir (İHA şemasıyla aynı kalıp: scripts/fdr_iha_baglanti_svg.py):

  FDR/sekiller/ika_baglanti.svg            — 1100 px genişlik, elle yerleşim
  FDR/sekiller/ika_baglanti_kaynaklar.md   — hat başına kaynak tablosu

Kural (FDR sprinti ön kaydı H3, results/fdr_sprint_20260910/ON_KAYIT.md; D-439 §3):
İKA aviyoniği TEDARİK EDİLMEDİ; ölçülmüş İKA topolojisi YOKTUR. Bu şema DDR
belgelerindeki TASARIMI çizer. Bu yüzden:
  * her hat "DDR tasarımı, tedarik yok" etiketi taşır ve KESİK çizilir;
  * ölçülmüş hat sayısı 0'dır (düz çizgi yoktur) — ÖLÇÜLEMEDİ ≠ GEÇTİ;
  * kaynaksız hat çizilmez: her hat en az bir DDR şekil/tablo atfı taşır;
  * DDR belgelerinin KENDİ İÇİNDEKİ çelişkiler gizlenmez, hatta yazılır.

Kaynaklar (kullanıcının belgeleri, salt okunur; python-docx ile 10 Eylül 2026 okundu):
  rapor/NAVITAS_IKA_DDR.docx              — İKA mekanik DDR: Tablo 3.2.2.14 BOM (NVT-ELK-*),
                                            §"Master Geometri" yerleşim maddeleri (kamera podu,
                                            ultrasonik pod, ön kapak acil stop + şalter, enkoder)
  rapor/3.3.1-2-3-4_SON.docx              — DDR aviyonik: Şekil 3.3.1.5 "İKA Bağlantı Şeması"
                                            (pin düzeyi), Şekil 3.3.2.10 kart tam şematiği,
                                            Şekil 3.3.3.2 güç dağıtım akışı, Tablo 3.3.2.18 BOM,
                                            Tablo 3.3.3.3 kablo/gerilim düşümü, Tablo 3.3.4.4 güç
  rapor/3.3.5_Yazilim_Mimarisi_MERGED_duzeltmeler.docx
                                          — DDR yazılım: Tablo 3.3.5.9 haberleşme hatları (Hat-3
                                            PA9/PA10 ↔ GPIO14/15, 115200), Tablo 3.3.5.13 UART v2
                                            çerçevesi, Tablo 3.3.5.16 FreeRTOS görevleri (ADC1_IN5,
                                            I2C1), Tablo 3.3.5.19 açık maddeler (Vet36/Vet06,
                                            IMX477/IMX708, PA2/PA3 USART2)

Kullanım:
  python scripts/fdr_ika_baglanti_svg.py            # iki dosyayı yazar
  python scripts/fdr_ika_baglanti_svg.py --dogrula  # diskteki dosya üretimle aynı mı (0/1)
"""

from __future__ import annotations

import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):      # cp1254 konsolda Türkçe çıktı (D-438 §2a sınıfı)
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
SVG_YOLU = SEKILLER / "ika_baglanti.svg"
MD_YOLU = SEKILLER / "ika_baglanti_kaynaklar.md"

CIZIM_TARIHI = "2026-09-10"
DDR_ETIKETI = "DDR tasarımı, tedarik yok"
SEMA_KAYNAGI = "DDR aviyonik Şekil 3.3.1.5 (İKA Bağlantı Şeması)"

GENISLIK = 1100
YUKSEKLIK = 1000

# ── Renk sözlüğü — legend ile hatlar aynı sözlükten okur ─────────────────────
RENK = {
    "guc_hv": "#7f0000",   # ana güç 22,2 V (bordo)
    "guc": "#e53935",      # 5 V / 5,1 V regüle güç (kırmızı)
    "guc_gnd": "#212121",  # güç − / GND (siyah)
    "motor": "#ad1457",    # H-köprü (BTS7960S) motor çıkışı, PWM'li DC (magenta)
    "uart": "#1565c0",     # UART (mavi)
    "i2c": "#6a1b9a",      # I2C (mor)
    "csi": "#2e7d32",      # MIPI CSI-2 şerit (yeşil)
    "enk": "#00838f",      # enkoder kuadratür A/B faz (turkuaz)
    "gpio": "#f9a825",     # GPIO: ultrasonik Trig/Echo, IMU INT (sarı)
    "analog": "#ef6c00",   # analog sensör: ACS758 akım çıkışı → ADC (turuncu)
}
RENK_ADI = {
    "guc_hv": "ana güç 22,2 V (bordo)",
    "guc": "5 V / 5,1 V regüle güç (kırmızı)",
    "guc_gnd": "güç − / GND (siyah)",
    "motor": "H-köprü motor çıkışı, PWM'li DC (magenta)",
    "uart": "UART (mavi)",
    "i2c": "I2C (mor)",
    "csi": "MIPI CSI-2 şerit (yeşil)",
    "enk": "enkoder kuadratür A/B (turkuaz)",
    "gpio": "GPIO: Trig/Echo, INT (sarı)",
    "analog": "analog sensör → ADC (turuncu)",
}
LEGEND_SIRASI = ["guc_hv", "guc", "guc_gnd", "motor", "uart", "i2c", "csi", "enk", "gpio", "analog"]
KESIK_DESEN = "8,5"

# ── Hatlar: tek doğruluk kaynağı ─────────────────────────────────────────────
# id · ad · nereden · nereye · olculdu (bool) · durum · kaynak · cizgiler
# Kesik çizgi = olculdu False (üretici bundan türetir). Bu şemada HEPSİ False.
HATLAR = [
    dict(
        id="K01", ad="Ana güç: pil → XT90-S anti-spark",
        nereden="Leopard Power 6S 22,2 V 5200 mAh 40C LiPo (NVT-ELK-003)",
        nereye="XT90-S anti-spark konnektör + akü kesici şalter 100 A (NVT-ELK-014)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — 12 AWG, 13,21 A tepe hesabı, ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI}; DDR aviyonik Şekil 3.3.3.2 (güç dağıtım akışı: 6S → XT90-S → 30 A sigorta → kart); "
               "DDR aviyonik Tablo 3.3.3.3 satır '6S batarya → özel kontrol/güç kartı' (12 AWG, 13,21 A tepe / 30 A koruma, "
               "0,80 m, ΔV 0,055 V, XT90-S + 30 A ATO); İKA DDR Tablo 3.2.2.14 NVT-ELK-003 (755 g), NVT-ELK-014",
        cizgiler=[("guc_hv", [(110, 250), (110, 280)], 3),
                  ("guc_gnd", [(140, 250), (140, 262), (24, 262), (24, 620), (400, 620)], 3)],
    ),
    dict(
        id="K02", ad="XT90-S / şalter → 30 A blade sigorta",
        nereden="XT90-S anti-spark + akü kesici şalter (ön kapak üstünde)",
        nereye="30 A ATO blade sigorta + yuva (NVT-ELK-013)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — acil kesme ≤ 2 s (şartname 32–34) test edilmedi",
        kaynak=f"{SEMA_KAYNAGI}; DDR aviyonik Şekil 3.3.3.2; İKA DDR Tablo 3.2.2.14 NVT-ELK-013 (30 A blade, +1 yedek); "
               "İKA DDR 'Master Geometri' ön kapak maddesi (acil stop butonu ve akü kesici şalter ön kapakta); "
               "DDR aviyonik Tablo 3.3.2.18 satır 14 (XT90-S 100 A anti-spark ayırıcı)",
        cizgiler=[("guc_hv", [(110, 332), (110, 362)], 3)],
    ),
    dict(
        id="K03", ad="30 A sigorta → ACS758 (seri) → özel kart + / pil − → kart −",
        nereden="30 A sigorta çıkışı",
        nereye="ACS758LCB-050B Hall akım sensörü (IP+ → IP−) → STM32F407 özel kart `+ 22,2 V`; pil − doğrudan kart `−`",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — akım yolu ACS758 üzerinden (şemada seri), ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI} (sigorta → ACS758 → kart +); DDR aviyonik Şekil 3.3.2.10 'POWER INPUT CONNECTOR' "
               "(6S_LIPO_22VIN / GND, P10); İKA DDR Tablo 3.2.2.14 NVT-ELK-009 (ACS758LCB-050B, gerilim bölücü ile), "
               "NVT-ELK-012 (özel kart STM32F407VET6 + BTS7960)",
        cizgiler=[("guc_hv", [(110, 406), (110, 436)], 3),
                  ("guc_hv", [(210, 456), (290, 456), (290, 300), (400, 300)], 3)],
    ),
    dict(
        id="K04", ad="ACS758 akım çıkışı → STM32 PA5 (ADC1_IN5)",
        nereden="ACS758 `I` (analog çıkış; besleme 5 V/GND kart üzerinden)",
        nereye="STM32F407 `PA5` = `ADC1_IN5`",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — akım izleme görevi 100 ms, aşırı akım failsafe; ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI} (ACS758 I → PA5 ADC1_IN5, 'Sensör' rengi); DDR yazılım Tablo 3.3.5.16 "
               "'Akım İzleme Görevi — ADC1_IN5 okuma, 100 ms, aşırı akım eşiğinde failsafe'; DDR yazılım Tablo 3.3.5.15 "
               "(STM32 sorumluluğu: akım izleme ACS758)",
        cizgiler=[("analog", [(210, 480), (330, 480), (330, 380), (400, 380)], 2.5)],
    ),
    dict(
        id="K05", ad="Özel kart H-köprü (BTS7960S ×4) → 4× KGX38 redüktörlü DC motor",
        nereden="Kart motor soketleri (KF301-2P ×4: LMA/LMB, RMA/RMB, qLMA/qLMB, qRMA/qRMB)",
        nereye="4× Keskinler KGX38 24 V 200 RPM 1 N·m (NVT-ELK-004): M1 sol arka · M2 sağ arka · M3 sol ön · M4 sağ ön (skid-steer)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — 18 AWG, 3,75 A/motor tasarım; PID yalnız arka aks enkoderinden, ön motor ayna komut (tasarım varsayımı)",
        kaynak=f"{SEMA_KAYNAGI} ('Motor Pinleri' ×4, yüksek voltaj rengi); DDR aviyonik Şekil 3.3.2.10 'MOTOR DRIVEN WITH ENCODER' "
               "(4× bts7960S, motor soketleri P1–P4 KF301-2P); DDR aviyonik Tablo 3.3.3.3 satır 'Kart → motor kolu (her motor)' "
               "(18 AWG, 3,75 A, 1,20 m, ΔV 0,094 V, kilitli terminal + yüksük); İKA DDR Tablo 3.2.2.14 NVT-ELK-004 (4 × 480 g); "
               "DDR yazılım §'Motor döngüsü' (arka aks enkoderli PID, ön motora ayna simetrik PWM — ekip onayına açık)",
        cizgiler=[("motor", [(520, 650), (520, 766)], 3), ("motor", [(580, 650), (580, 766)], 3),
                  ("motor", [(640, 650), (640, 766)], 3), ("motor", [(700, 650), (700, 766)], 3)],
    ),
    dict(
        id="K06", ad="2× artımlı optik enkoder ↔ kart (A/B faz + 5 V/GND)",
        nereden="2× artımlı optik döner enkoder 5–24 V / 400 darbe (NVT-ELK-010), GT2 kayışla arka aks motor millerinden",
        nereye="Kart 'Encoder Destekli Sürücü Devresi' (şematik: ENCAL/ENCBL, ENCAR/ENCBR, 4k7 pull-up 3,3 V, B4B-XH soket)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — ⚠ etiket tutarsızlığı: bağlantı şeması 'Ön/Arka A-B faz' yazar, kart şematiği L/R (sol/sağ), "
              "mekanik DDR 'enkoder yalnız ARKA aks' der",
        kaynak=f"{SEMA_KAYNAGI} ('Ön - A/B Faz', 'Arka - A/B Faz', Encoder A/B faz renkleri; Vcc/GND 5 V); DDR aviyonik "
               "Şekil 3.3.2.10 (ENCAL/ENCBL/ENCAR/ENCBR, 'INTERFACING PINS' H1/H7); İKA DDR 'Tahrik Sistemi' maddesi "
               "(arka aks motorlarında enkoder, GT2 kasnak + kayış); İKA DDR Tablo 3.2.2.14 NVT-ELK-010, NVT-MEK-008/009/010; "
               "DDR aviyonik Tablo 3.3.3.3 satır 'Enkoder besleme ve sinyal demeti' (22 AWG, ≤ 1 A, JST-XH)",
        cizgiler=[("enk", [(430, 650), (430, 718), (210, 718)], 2.5),
                  ("enk", [(450, 650), (450, 798), (210, 798)], 2.5),
                  ("guc", [(438, 650), (438, 726), (210, 726)], 1.5),
                  ("guc", [(458, 650), (458, 806), (210, 806)], 1.5)],
    ),
    dict(
        id="K07", ad="Kart 5 V buck → Raspberry Pi 5 besleme (5,1 V / 5 A)",
        nereden="Özel kart 5 V çıkışı (XL4015E1 buck 22,2 V → 5 V; şemada 'USB Type-C Vout')",
        nereye="Raspberry Pi 5 8 GB (NVT-ELK-001) `5V` / `GND` pinleri (kablo tablosu: USB-C + mekanik kelepçe)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — 18 AWG, 5 A, ΔV 0,063 V hesabı; ⚠ şema 5 V pin, kablo tablosu USB-C — bağlantı biçimi belirsiz",
        kaynak=f"{SEMA_KAYNAGI} (kart 5V/GND → RPi5 5V GND); DDR aviyonik Şekil 3.3.2.10 '22.2V (6S) -> 5V BUCK: SYSTEM LOGIC SUPPLY' "
               "(XL4015E1, H11 5 V; AMS1117 3,3 V lojik); DDR aviyonik Şekil 3.3.3.2 '5.1 V / 5 A Raspberry Pi 5 hattı'; "
               "DDR aviyonik Tablo 3.3.3.3 satır '5,1 V Raspberry Pi çıkışı' (5 A, 18 AWG, 0,60 m, USB-C + mekanik kelepçe); "
               "DDR aviyonik Tablo 3.3.2.18 satır 12 (kart: STM32F407VET6 + motor sürücü + 5,1V/5A)",
        cizgiler=[("guc", [(720, 222), (760, 222)], 3), ("guc_gnd", [(720, 232), (760, 232)], 2)],
    ),
    dict(
        id="K08", ad="Hat-3: STM32 UART1 ↔ RPi5 UART (Navitas UART v2, 115200)",
        nereden="STM32 `PA9` (UART1_TX) → RPi5 `GPIO15 RX` (pin 10); RPi5 `GPIO14 TX` (pin 8) → STM32 `PA10` (UART1_RX)",
        nereye="çerçeve: `0xAA 0x55` · ID · LEN · PAYLOAD · CRC8 (enkoder, ultrasonik, IMU passthrough, motor komutu, failsafe bayrağı)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — 'STM32 ↔ RPi5 donanım entegrasyon testi, paket kaybı %0' DDR'de planlı, yapılmadı; "
              "kodda bu hattın uygulaması yok (`GercekSurucu` arka ucu DONANIM_YOK)",
        kaynak=f"{SEMA_KAYNAGI} (PA9/UART1 TX → P10/GPIO15 RX; P8/GPIO14 TX → PA10/UART1 RX); DDR yazılım Tablo 3.3.5.9 "
               "Hat-3 ('RPi5 ↔ STM32, Navitas UART v2, kablolu UART PA9/PA10 ↔ GPIO14/15, 115200 baud'); DDR yazılım "
               "Tablo 3.3.5.13 (çerçeve alanları: Header 0xAA 0x55, ID, LEN, PAYLOAD, CRC8); DDR yazılım Tablo 3.3.5.16 "
               "('UART İletişim Görevi 20 ms'); DDR aviyonik Tablo 3.3.3.3 satır 'UART ve I²C haberleşme' (24 AWG, bükümlü çift)",
        cizgiler=[("uart", [(720, 262), (760, 262)], 2.5), ("uart", [(760, 272), (720, 272)], 2.5)],
    ),
    dict(
        id="K09", ad="RPi5 UART ↔ M8N GPS (NMEA/UBX)",
        nereden="RPi5 `GPIO4 TX` (pin 7) → M8N `RX`; M8N `TX` → RPi5 `GPIO5 RX` (pin 29)",
        nereye="M8N GPS + dahili pusula modülü (NVT-ELK-006), üst kapak sacında",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — GPS doğrudan RPi5'e (STM32 üzerinden geçmez), EKF girdisi; ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI} (P29/GPIO5 RX ← M8N TX; P7/GPIO4 TX → M8N RX); DDR yazılım §3.3.5.3 metni "
               "('GPS ve telemetri modülleri STM32 üzerinden geçmemekte, doğrudan RPi5'e bağlanmaktadır'); DDR aviyonik "
               "'İKA Sistem Mimarisi Açıklaması' ('GPS konum verileri UART hattı ile'); İKA DDR 'GPS Modülü ve Pusula Yerleşimi' "
               "maddesi (üst kapak sacı, manyetik sapma); İKA DDR Tablo 3.2.2.14 NVT-ELK-006",
        cizgiler=[("uart", [(960, 310), (960, 330)], 2.5), ("uart", [(975, 330), (975, 310)], 2.5)],
    ),
    dict(
        id="K10", ad="RPi5 I2C ↔ M8N pusula",
        nereden="RPi5 `GPIO2 SDA` (pin 3) / `GPIO3 SCL` (pin 5)",
        nereye="M8N modülü üstündeki pusula `SDA` / `SCL`",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — EMI/pusula sapma testi (±5°) DDR'de planlı, yapılmadı",
        kaynak=f"{SEMA_KAYNAGI} (P3/GPIO2 SDA, P5/GPIO3 SCL → M8N SDA/SCL, I2C renkleri); DDR aviyonik 'İKA Sistem Mimarisi "
               "Açıklaması' ('pusula ve IMU sensör verileri I²C hattı üzerinden'); İKA DDR Tablo 3.2.2.16 "
               "('EMI/EMC Manyetik Sapma Testi — pusula sapması ±5°'yi geçmemeli', planlı)",
        cizgiler=[("i2c", [(1000, 310), (1000, 330)], 2.5), ("i2c", [(1015, 310), (1015, 330)], 2.5)],
    ),
    dict(
        id="K11", ad="Kart 5 V / GND rayı → sensör ve haberleşme kolları",
        nereden="Özel kart 5 V çıkışı (regüle, filtreli kollar)",
        nereye="M8N `5V/GND` · SiK V3 `Vcc/GND` · MPU6050 `Vcc/GND` · 2× HC-SR04 `Vcc/GND` (enkoder 5 V K06'da)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — 22 AWG ≤ 2 A hesabı; DDR: sensör beslemeleri ayrı filtrelenmiş 5 V/3,3 V kollarından",
        kaynak=f"{SEMA_KAYNAGI} (5V-5.3V rengi: kart 5V → M8N 5V, SiK Vcc, MPU6050 Vcc, HC-SR04 Vcc ×2); DDR aviyonik "
               "Şekil 3.3.3.2 ('REGÜLE / DÜŞÜK AKIM ÇIKIŞLARI': telemetri, GNSS/pusula, HC-SR04 ×2, enkoder, IMU hatları); "
               "DDR aviyonik Tablo 3.3.3.3 satır 'GNSS, IMU, ultrasonik sensörler' (≤ 2 A, 22 AWG, JST-GH/JST-XH); "
               "DDR aviyonik 'Kablo düzenlemesi — İKA' maddeleri (sensör beslemeleri ayrı filtrelenmiş 5 V/3,3 V kollarından)",
        cizgiler=[("guc", [(720, 200), (740, 200), (740, 168), (1094, 168), (1094, 606)], 2),
                  ("guc", [(1094, 358), (1080, 358)], 2), ("guc", [(1094, 438), (1080, 438)], 2),
                  ("guc", [(1094, 518), (1080, 518)], 2), ("guc", [(1094, 598), (1080, 598)], 2)],
    ),
    dict(
        id="K12", ad="Raspberry Pi Camera Module 3 Wide → RPi5 CSI",
        nereden="Camera Module 3 Wide (IMX708, 120°; NVT-ELK-002), ön kapak kamera podunda aşağı eğimli",
        nereye="RPi5 MIPI CSI-2 konnektörü (FFC şerit)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — ⚠ DDR içi tutarsızlık: yazılım bölümü Tablo 3.3.5.19 'elektronik şemada Arducam IMX477 yazıyor' der; "
              "bu şema IMX708 yazar (BOM ile uyumlu)",
        kaynak=f"{SEMA_KAYNAGI} (Raspberry Pi Camera Module 3 Wide IMX708, MIPI CSI-2 rengi); İKA DDR Tablo 3.2.2.14 NVT-ELK-002; "
               "DDR aviyonik Tablo 3.3.3.4 satır 'Kamera CSI hattı — MIPI CSI-2 FFC, FFC mandalı + kablo kıskacı'; "
               "İKA DDR 'Ön Kapak' maddesi (kamera podu 120°, aşağı eğim); DDR yazılım Tablo 3.3.5.19 'Kamera sensör etiketi' açık maddesi",
        cizgiler=[("csi", [(790, 310), (790, 330)], 2.5)],
    ),
    dict(
        id="K13", ad="SiK V3 433 MHz (Hat-2) ↔ STM32 USART2 — DDR İÇİ ÇELİŞKİ",
        nereden="Holybro SiK Telemetry Radio V3 (NVT-ELK-005) `Tx` → STM32 `PA3` (USART2_RX); STM32 `PA2` (USART2_TX) → SiK `Rx`",
        nereye="⚠ DDR yazılım bölümü aynı radyoyu 'doğrudan RPi5'e' bağlar ve PA2/PA3'ü 'fonksiyonu belirtilmemiş' sayar; "
               "kodun İKA alıcısı (`comms/ika_receiver.py --serial`) RPi5'te Python'dur — bu hat kodla uyumsuz",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — ⚠ KARAR BEYAN GEREKLİ: SiK RPi5'e (USB/UART) mi, STM32 USART2'ye köprü mü? Bugün ikisi de ölçülmedi",
        kaynak=f"{SEMA_KAYNAGI} (SiK Tx → PA3 USART2_RX, PA2 USART2_TX → SiK Rx; Vcc/GND 5 V); DDR yazılım Tablo 3.3.5.9 Hat-2 "
               "('İKA ↔ YKİ, MAVLink v2, SiK V3, 433 MHz NetID 26'); DDR yazılım §3.3.5.3 metni ('telemetri modülleri STM32 "
               "üzerinden geçmemekte, doğrudan RPi5'e'); DDR yazılım Tablo 3.3.5.19 satır 'PA2/PA3 (USART2) — fonksiyonu "
               "belirtilmemiş ikinci UART hattı'; İKA DDR Tablo 3.2.2.14 NVT-ELK-005; kod: `comms/ika_receiver.py` `--serial` "
               "(SerialLink, RPi5'te) — FDR BOLUM_3 §3.3.1.3.3 (4) beyan tablosu",
        cizgiler=[("uart", [(760, 428), (720, 428)], 2.5), ("uart", [(720, 440), (760, 440)], 2.5)],
    ),
    dict(
        id="K14", ad="MPU6050 GY-521 IMU ↔ STM32 I2C1 + INT",
        nereden="MPU6050 `SDA`/`SCL` ↔ STM32 `PB7` (I2C1_SDA) / `PB6` (I2C1_SCL); `INT` → `PC5`; Vcc/GND 5 V (K11)",
        nereye="STM32 'IMU Okuma Görevi' 20 ms → RPi5'e passthrough (Hat-3), tank dönüşü telafisi",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — IMU verisi STM32 I2C1'den okunup RPi5'e aktarılır; ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI} (PB7 I2C1_SDA, PB6 I2C1_SCL, PC5 INT → MPU6050 GY-521); DDR yazılım Tablo 3.3.5.16 "
               "('IMU Okuma Görevi — I2C1 üzerinden ham veri okuma ve RPi5'e passthrough, 20 ms'); İKA DDR 'Sensör Füzyonu "
               "(Tank Dönüşü Telafisi)' maddesi; İKA DDR Tablo 3.2.2.14 NVT-ELK-011 (MPU6050 GY-521, I2C)",
        cizgiler=[("i2c", [(720, 505), (760, 505)], 2.5), ("i2c", [(720, 517), (760, 517)], 2.5),
                  ("gpio", [(760, 530), (720, 530)], 2)],
    ),
    dict(
        id="K15", ad="HC-SR04 ön ultrasonik ↔ STM32 PC2 (Trig) / PC3 (Echo, 5 V→3,3 V bölücü)",
        nereden="HC-SR04 ön (NVT-ELK-008, açılandırılmış pod: zemin tarama 65 cm)",
        nereye="STM32 `PC2` → Trig; Echo → `PC3` (kart üstü 1k/2k direnç bölücü 'ECHO1'); Vcc/GND 5 V (K11)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — FSM eşikleri (SLOW 65 cm + fren mesafesi, STOP ≤ 65 cm) fren testi yapılmadan sayısal değil",
        kaynak=f"{SEMA_KAYNAGI} (PC2 → ön Trig, ön Echo → PC3, Trig-Echo rengi); DDR aviyonik Şekil 3.3.2.10 "
               "'ULTRASONIC SENSOR 5V-3.3V SIGNAL CONVERTING' (ECHO1 → PC3, 1k/2k); İKA DDR 'Ön Alt Ultrasonik Sensör Podu' "
               "maddesi (7,5° → açılı pod, 65 cm); DDR yazılım Tablo 3.3.5.17 (NORMAL/SLOW/STOP) ve Tablo 3.3.5.19 'SLOW eşiği'; "
               "İKA DDR Tablo 3.2.2.14 NVT-ELK-008",
        cizgiler=[("gpio", [(720, 584), (760, 584)], 2), ("gpio", [(760, 598), (720, 598)], 2)],
    ),
    dict(
        id="K16", ad="HC-SR04 arka ultrasonik ↔ STM32 PC0 (Trig) / PC1 (Echo, 5 V→3,3 V bölücü)",
        nereden="HC-SR04 arka (NVT-ELK-008)",
        nereye="STM32 `PC0` → Trig; Echo → `PC1` (kart üstü bölücü 'ECHO2'); Vcc/GND 5 V (K11)",
        olculdu=False,
        durum=f"{DDR_ETIKETI} — geri sürüşte kullanım DDR'de yazılı değil; ölçüm yok",
        kaynak=f"{SEMA_KAYNAGI} (PC0 → arka Trig, arka Echo → PC1); DDR aviyonik Şekil 3.3.2.10 (ECHO2 → PC1, 1k/2k); "
               "DDR yazılım §3.3.5.3 metni ('ultrasonik mesafe (ön+arka)' Hat-3 üzerinden); İKA DDR Tablo 3.2.2.14 NVT-ELK-008 (2 adet)",
        cizgiler=[("gpio", [(720, 612), (745, 612), (745, 640), (960, 640), (960, 626)], 2),
                  ("gpio", [(985, 626), (985, 648), (738, 648), (738, 622), (720, 622)], 2)],
    ),
]

# ── Çizilmeyenler (bilerek) ──────────────────────────────────────────────────
CIZILMEYENLER = [
    "**Kart üstü devreler** — XL4015E1 5 V buck, AMS1117 3,3 V, CH340C USB-UART (programlama/log, USB-C), durum LED'leri, "
    "BOOT/NRST anahtarları: DDR aviyonik Şekil 3.3.2.10'da var; araç kablosu değil, kart içi iz.",
    "**Acil stop butonu** — İKA DDR ön kapak maddesinde 'acil stop butonu ve akü kesici şalter' yazar; şalter K02'dir, "
    "butonun hangi hatta olduğu DDR şemasında yok → BEYAN GEREKLİ.",
    "**RPi5 microSD, aktif soğutucu, kart üstü fan** — kart/kutu içi; hat değil.",
    "**Kablo kesitleri gerçek ölçüsü, konnektör tipleri** — DDR Tablo 3.3.3.3 tasarım değerleridir; ölçülmedi.",
    "**RC alıcı** — DDR: 'İKA'da RC alıcısı bulunmadığından' (failsafe bölümü); İKA'da RC hattı YOK.",
    "**MAVLink / Pixhawk** — İKA'da uçuş kontrolcüsü yok; DDR'nin 'MAVLink v2 Hat-2' beyanı kodla değişti "
    "(FDR BOLUM_3 §3.3.1.3.3 madde 4, D-439 §2).",
]

TUTARSIZLIKLAR = [
    "**SiK radyosu nereye bağlı?** DDR aviyonik Şekil 3.3.1.5: STM32 `PA2/PA3` (USART2). DDR yazılım §3.3.5.3: 'telemetri "
    "doğrudan RPi5'e'; Tablo 3.3.5.19: 'PA2/PA3 fonksiyonu belirtilmemiş'. Kod: alıcı RPi5'te Python (`comms/ika_receiver.py`). "
    "→ K13, BEYAN GEREKLİ.",
    "**Kart adı:** bağlantı şeması 'Vet36 Mikroişlemci Devresi', yazılım metni 'Vet06' (DDR yazılım Tablo 3.3.5.19 ilk satır).",
    "**Kamera sensörü:** DDR yazılım Tablo 3.3.5.19 'elektronik şemada Arducam IMX477' der; Şekil 3.3.1.5 ve BOM IMX708 (Camera Module 3 Wide).",
    "**Enkoder etiketi:** Şekil 3.3.1.5 'Ön/Arka A-B faz'; kart şematiği ENCAL/ENCAR (sol/sağ); mekanik DDR 'yalnız arka aks' → K06.",
    "**RPi5 besleme biçimi:** Şekil 3.3.1.5 5V/GND pin; DDR aviyonik Tablo 3.3.3.3 'USB-C + mekanik kelepçe' → K07.",
    "**İKA hattı protokolü:** DDR 'MAVLink v2 iki-atlamalı (İHA → YKİ → İKA)'; kod NAVITAS çerçeve protokolü, İHA → İKA doğrudan "
    "+ K8 ACK kanıtı — FDR beyanı BOLUM_3 §3.3.1.3.3 (4) (D-439 §2).",
    "**Heartbeat kaybı eşiği:** DDR 'SiK bağlantısı 5 s kesilirse güvenli duruş' (aviyonik failsafe metni); kod `IkaReceiver.hb_timeout` "
    "= 3 s (`comms/ika_receiver.py`).",
]


# ── SVG yardımcıları (İHA üreteciyle aynı kalıp) ─────────────────────────────
def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def _kutu(x, y, w, h, satirlar, kesik=True, dolgu="#fafafa", kenar="#37474f", r=6, boyut=12.5):
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
    kesik = not h["olculdu"]
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
           f'  <rect x="{x}" y="{y}" width="320" height="296" rx="6" fill="#fafafa" stroke="#90a4ae" stroke-width="1"/>',
           _metin(x + 12, y + 20, "Açıklama", 13, agirlik="bold")]
    yy = y + 40
    for tur in LEGEND_SIRASI:
        out.append(f'  <line data-hat="{tur}" x1="{x + 14}" y1="{yy - 4}" x2="{x + 54}" y2="{yy - 4}" '
                   f'stroke="{RENK[tur]}" stroke-width="3.5" stroke-linecap="round"/>')
        out.append(_metin(x + 64, yy, RENK_ADI[tur], 11))
        yy += 21
    yy += 4
    out.append(f'  <line x1="{x + 14}" y1="{yy - 4}" x2="{x + 54}" y2="{yy - 4}" stroke="#263238" '
               f'stroke-width="2.5" stroke-dasharray="{KESIK_DESEN}"/>')
    out.append(_metin(x + 64, yy, f"kesik: {DDR_ETIKETI} (ölçüm yok)", 10))
    yy += 18
    out.append(_metin(x + 14, yy, "düz çizgi bu şemada YOK: ölçülmüş İKA hattı 0 / 16", 10, renk="#b71c1c"))
    out.append("  </g>")
    return "\n".join(out)


def svg_uret() -> str:
    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{GENISLIK}" height="{YUKSEKLIK}" '
             f'viewBox="0 0 {GENISLIK} {YUKSEKLIK}" font-family="Segoe UI, DejaVu Sans, Arial, sans-serif" '
             f'fill="#263238">')
    p.append(f"  <title>İKA bağlantı şeması — {DDR_ETIKETI} (DDR aviyonik Şekil 3.3.1.5 / 3.3.2.10 / 3.3.3.2; ölçülmüş hat 0)</title>")
    p.append(f"  <desc>Üreten: scripts/fdr_ika_baglanti_svg.py · çizim {CIZIM_TARIHI} · her hat için kaynak: "
             f"FDR/sekiller/ika_baglanti_kaynaklar.md · İKA aviyoniği tedarik edilmedi (D-439 §3): şema DDR tasarımıdır, "
             f"hiçbir hat ölçülmedi</desc>")
    p.append(f'  <rect x="0" y="0" width="{GENISLIK}" height="{YUKSEKLIK}" fill="#ffffff"/>')

    # Başlık
    p.append(_metin(40, 32, f"İKA bağlantı şeması — {DDR_ETIKETI} (çizim 10 Eylül 2026)", 18, agirlik="bold"))
    p.append(_metin(40, 52, "Kaynak: DDR aviyonik Şekil 3.3.1.5 (İKA Bağlantı Şeması), Şekil 3.3.2.10 (kart şematiği), "
                    "Şekil 3.3.3.2 (güç dağıtımı), Tablo 3.3.3.3 (kablo) · İKA DDR Tablo 3.2.2.14 (BOM) · "
                    "hat başına kaynak: FDR/sekiller/ika_baglanti_kaynaklar.md", 10, renk="#455a64"))

    # Okuma kılavuzu (sağ üst)
    p.append('  <rect x="760" y="58" width="320" height="92" rx="6" fill="#fff8e1" stroke="#ffb300" stroke-width="1"/>')
    p.append(_metin(772, 76, "Okuma kılavuzu", 12.5, agirlik="bold"))
    notlar = [
        f"• Bütün hatlar kesik: {DDR_ETIKETI}",
        "• Düz çizgi yok — ölçülmüş İKA hattı 0/16 (ÖLÇÜLEMEDİ ≠ GEÇTİ)",
        "• ⚠ işaretli hat: DDR belgeleri kendi içinde çelişiyor (K06, K07, K12, K13)",
        "• Kart üstü devreler (buck, CH340C, LED) çizilmedi — kaynak tablosu",
    ]
    for i, s in enumerate(notlar):
        p.append(_metin(772, 94 + i * 15, s, 10))

    # ── Sol sütun: güç zinciri ──
    p.append(_kutu(40, 180, 170, 70, ["6S 22,2 V LiPo", "5200 mAh 40C", "NVT-ELK-003 · 755 g"]))
    p.append(_kutu(40, 280, 170, 52, ["XT90-S anti-spark", "+ akü kesici şalter 100 A"]))
    p.append(_kutu(40, 362, 170, 44, ["30 A ATO blade sigorta"]))
    p.append(_kutu(40, 436, 170, 60, ["ACS758LCB-050B 50 A", "Hall akım sensörü (seri)", "I → PA5 ADC1_IN5"]))
    p.append(_metin(158, 270, "+ / −", 10))
    p.append(_metin(300, 292, "22,2 V (12 AWG, 13,21 A tepe)", 9.5, anchor="middle", renk=RENK["guc_hv"]))
    p.append(_metin(340, 372, "analog akım", 9.5, anchor="middle", renk=RENK["analog"]))
    p.append(_metin(30, 640, "pil − → kart − (GND)", 9.5, renk="#455a64"))

    # ── Merkez: özel kart ──
    p.append(_kutu(400, 180, 320, 470, [], kesik=True, dolgu="#e3f2fd", kenar="#1565c0"))
    p.append(_metin(408, 204, "Özel güç/kontrol kartı", 13, agirlik="bold"))
    p.append(_metin(408, 220, "STM32F407VET6 (NVT-ELK-012)", 11))
    p.append(_metin(408, 236, "kart adı: 'Vet36' şema / 'Vet06' metin — DDR içi fark", 9.5, renk="#b71c1c"))
    p.append(_metin(408, 318, "BTS7960S ×4 H-köprü · XL4015E1 5 V buck · AMS1117 3,3 V", 9.5))
    p.append(_metin(408, 332, "CH340C USB-UART (programlama/log) · durum LED'leri", 9.5))
    p.append(_metin(408, 346, "FreeRTOS: PID 10 ms · UART v2 20 ms · ultrasonik FSM 20 ms", 9.5))
    p.append(_metin(408, 360, "IMU 20 ms · akım izleme 100 ms (ADC1_IN5)", 9.5))
    # sol kenar portları
    p.append(_metin(408, 296, "+ 22,2 V", 10.5, agirlik="bold"))
    p.append(_metin(408, 376, "PA5 ADC1_IN5", 10.5, agirlik="bold"))
    p.append(_metin(408, 616, "− GND", 10.5, agirlik="bold"))
    # sağ kenar portları
    p.append(_metin(712, 196, "5 V rayı →", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 219, "5,1 V RPi5 →", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 258, "PA9 TX → GPIO15", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 283, "PA10 RX ← GPIO14", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 424, "PA3 RX ← SiK Tx", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 451, "PA2 TX → SiK Rx", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 501, "PB7 SDA", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 528, "PB6 SCL · PC5 INT", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 580, "PC2 Trig → ön", 10, anchor="end", agirlik="bold"))
    p.append(_metin(712, 604, "PC3 Echo ← ön", 10, anchor="end", agirlik="bold"))
    p.append(_metin(408, 470, "Hat-3 (UART1 ↔ RPi5): Navitas UART v2 · 115200 baud", 9.5))
    p.append(_metin(408, 484, "çerçeve: 0xAA 0x55 · ID · LEN · PAYLOAD · CRC8", 9.5))
    p.append(_metin(408, 496, "kodda YOK: GercekSurucu DONANIM_YOK (§3.3.1.3.3)", 9.5, renk="#b71c1c"))
    # alt kenar
    p.append(_metin(440, 636, "ENC L/R", 10, anchor="middle", agirlik="bold"))
    for x, s in [(520, "M1"), (580, "M2"), (640, "M3"), (700, "M4")]:
        p.append(_metin(x, 636, s, 10.5, anchor="middle", agirlik="bold"))
    p.append(_metin(408, 602, "BTS7960S ×4 → M1..M4 (KF301-2P, 18 AWG, 3,75 A)", 9.5))

    # ── Sağ sütun ──
    p.append(_kutu(760, 190, 320, 120, ["Raspberry Pi 5 8 GB (NVT-ELK-001)", "Raspberry Pi OS · Python · A* · EKF · comms/ika_receiver.py",
                                         "GPIO14 TX (pin 8) · GPIO15 RX (pin 10) ← Hat-3 UART1",
                                         "GPIO4 TX (pin 7) · GPIO5 RX (pin 29) → M8N GPS",
                                         "GPIO2 SDA (pin 3) · GPIO3 SCL (pin 5) → pusula · CSI"], boyut=11.5))
    p.append(_kutu(760, 330, 150, 56, ["Camera Module 3 Wide", "IMX708 · 120° · CSI-2", "(NVT-ELK-002)"], boyut=11))
    p.append(_kutu(930, 330, 150, 56, ["M8N GPS + pusula", "UART (GPS) · I2C (pusula)", "(NVT-ELK-006)"], boyut=11))
    p.append(_kutu(760, 410, 320, 56, ["Holybro SiK V3 433 MHz (Hat-2, NetID 26) — NVT-ELK-005",
                                        "⚠ şema: STM32 USART2 · metin: doğrudan RPi5 · kod: alıcı RPi5'te (K13)"], boyut=11))
    p.append(_kutu(760, 490, 320, 56, ["MPU6050 GY-521 6 eksen IMU (NVT-ELK-011)",
                                        "SDA/SCL → I2C1 (PB7/PB6) · INT → PC5 · Vcc 5 V"], boyut=11))
    p.append(_kutu(760, 570, 150, 56, ["HC-SR04 ön", "Trig ← PC2 · Echo → PC3", "açılı pod, 65 cm"], boyut=11))
    p.append(_kutu(930, 570, 150, 56, ["HC-SR04 arka", "Trig ← PC0 · Echo → PC1", "(NVT-ELK-008 ×2)"], boyut=11))
    p.append(_metin(740, 320, "CSI", 9, anchor="middle", renk=RENK["csi"]))
    p.append(_metin(940, 324, "UART", 9, anchor="end", renk=RENK["uart"]))
    p.append(_metin(1030, 324, "I2C", 9, renk=RENK["i2c"]))
    p.append(_metin(1094, 164, "5 V rayı (K11)", 9, anchor="end", renk=RENK["guc"]))
    p.append(_metin(850, 662, "PC0 Trig / PC1 Echo → HC-SR04 arka (K16)", 9, anchor="middle", renk="#8d6e00"))

    # ── Alt: enkoderler ve motorlar ──
    p.append(_kutu(40, 690, 170, 56, ["Enkoder L (arka sol)", "400 darbe · A/B faz · 5 V", "NVT-ELK-010"], boyut=11))
    p.append(_kutu(40, 770, 170, 56, ["Enkoder R (arka sağ)", "400 darbe · A/B faz · 5 V", "NVT-ELK-010"], boyut=11))
    p.append(_metin(320, 712, "A/B faz (22 AWG) + 5 V/GND", 9.5, anchor="middle", renk=RENK["enk"]))
    p.append(_metin(40, 880, "⚠ enkoder etiketi: şema 'Ön/Arka', kart şematiği L/R, mekanik DDR 'yalnız arka aks' (K06)", 9.5, renk="#b71c1c"))
    for x, ad, konum in [(520, "M1", "sol arka · enk"), (580, "M2", "sağ arka · enk"),
                         (640, "M3", "sol ön"), (700, "M4", "sağ ön")]:
        p.append(f'  <circle cx="{x}" cy="790" r="24" fill="#fafafa" stroke="#37474f" stroke-width="1.6" stroke-dasharray="{KESIK_DESEN}"/>')
        p.append(_metin(x, 795, ad, 12.5, anchor="middle", agirlik="bold"))
        p.append(_metin(x, 830, konum, 9.5, anchor="middle"))
    p.append(_metin(230, 848, "4× KGX38 24 V 200 RPM 1 N·m (NVT-ELK-004) · Ø125 mm TPU teker · skid-steer · 1,3 m/s teorik", 9.5))
    p.append(_metin(230, 864, "motor yerleşimi (sol/sağ, ön/arka) DDR'de numaralı değil — gösterim amaçlı sıralandı (BEYAN GEREKLİ)",
                    9.5, renk="#455a64"))
    p.append(_metin(40, 905, "İKA hattı FDR beyanı: kod NAVITAS çerçeve protokolü (İHA → İKA doğrudan + K8 ACK); DDR 'MAVLink v2 iki-atlamalı' — "
                    "FDR BOLUM_3 §3.3.1.3.3 (4), D-439 §2", 9.5, renk="#455a64"))
    p.append(_metin(40, 921, "Hiçbir hat ölçülmedi: İKA aviyoniği tedarik edilmedi (D-439 §3). Bu şema tasarım beyanıdır, saha topolojisi değildir.",
                    9.5, renk="#b71c1c"))

    # ── Hatlar ──
    p.append("  <!-- Hatlar: her polyline data-hat ile ika_baglanti_kaynaklar.md tablosuna bağlıdır -->")
    for h in HATLAR:
        p.append(f"  <!-- {h['id']} {h['ad']} -->")
        p.append(_hat_cizgileri(h))

    p.append(_legend(760, 690))
    p.append("</svg>")
    return "\n".join(p) + "\n"


def md_uret() -> str:
    o = []
    o.append("# İKA bağlantı şeması — hat başına kaynak (DDR tasarımı, tedarik yok)")
    o.append("")
    o.append(f"Şema: `ika_baglanti.svg` (çizim {CIZIM_TARIHI}; üreten `scripts/fdr_ika_baglanti_svg.py`, "
             "iki dosya aynı tablodan çıkar). Yönerge Y-3.3.1-M01 (İKA kolu). İHA şeması ayrı: `iha_baglanti.svg`.")
    o.append("")
    o.append(f"**Kural:** kaynaksız hat çizilmez. Bu şemada **düz çizgi yoktur**: İKA aviyoniği tedarik edilmedi "
             "(FDR BOLUM_3 §3.2.2; D-439 §3), hiçbir hat ölçülmedi. Her hat **kesik** çizilir ve "
             f"`{DDR_ETIKETI}` etiketi taşır. Kaynak, kullanıcının DDR belgeleridir (python-docx ile 10 Eylül 2026 okundu); "
             "DDR belgelerinin kendi içindeki çelişkiler ⚠ ile hat satırında yazılır, gizlenmez.")
    o.append("")
    o.append("**Kaynak belgeler:** `rapor/NAVITAS_IKA_DDR.docx` (İKA mekanik DDR: Tablo 3.2.2.14 BOM `NVT-ELK-*`, "
             "'Master Geometri' yerleşim maddeleri, Tablo 3.2.2.16 gelecek testler); `rapor/3.3.1-2-3-4_SON.docx` "
             "(DDR aviyonik: **Şekil 3.3.1.5 İKA Bağlantı Şeması** — pin düzeyi tek kaynak, Şekil 3.3.2.10 kart tam şematiği, "
             "Şekil 3.3.3.2 güç dağıtım akışı, Tablo 3.3.2.18 BOM, Tablo 3.3.3.3 kablo/gerilim düşümü, Tablo 3.3.3.4 konnektörler, "
             "Tablo 3.3.4.4 güç tüketimi); `rapor/3.3.5_Yazilim_Mimarisi_MERGED_duzeltmeler.docx` (DDR yazılım: Tablo 3.3.5.9 "
             "haberleşme hatları, Tablo 3.3.5.13 UART v2 çerçevesi, Tablo 3.3.5.16 FreeRTOS görevleri, Tablo 3.3.5.19 açık maddeler). "
             "Kod tarafı: `comms/ika_receiver.py`, `simulation/scripts/ika_surucu.py` (FDR BOLUM_3 §3.3.1.3.3).")
    o.append("")
    o.append("## Renk sözlüğü")
    o.append("")
    o.append("| tür | renk | hex |")
    o.append("|---|---|---|")
    for tur in LEGEND_SIRASI:
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
    o.append("## DDR içi çelişkiler ve kod ↔ DDR farkları (şema DDR Şekil 3.3.1.5'i esas alır)")
    o.append("")
    for s in TUTARSIZLIKLAR:
        o.append(f"- {s}")
    o.append("")
    o.append("## Sayım")
    o.append("")
    n_olculdu = sum(1 for h in HATLAR if h["olculdu"])
    o.append(f"- Hat: **{len(HATLAR)}** · ölçülmüş (düz): **{n_olculdu}** · {DDR_ETIKETI} (kesik): **{len(HATLAR) - n_olculdu}**")
    o.append("- İHA şeması: ayrı dosya `iha_baglanti.svg` (ölçülen topoloji, 7 Eylül).")
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
    n_olculdu = sum(1 for h in HATLAR if h["olculdu"])
    print(f"YAZILDI {SVG_YOLU.relative_to(KOK)} ({len(svg)} B) · {MD_YOLU.relative_to(KOK)} ({len(md)} B) · "
          f"hat {len(HATLAR)} · ölçülmüş {n_olculdu} · kesik {len(HATLAR) - n_olculdu}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
