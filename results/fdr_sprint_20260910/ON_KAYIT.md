# ÖN KAYIT — FDR YAZILIM SPRİNTİ (10 → 21 Eylül 2026)

> **Amaç (kullanıcı, 10 Eylül 00:3x):** FDR teslimine (21 Eylül 17:00) kadar İHA ve İKA
> **yazılımını** yönergeye uygun, ölçülmüş kanıtla **yazılabilir** hâle getirmek. İKA donanımı
> FDR'den önce **olmayacak**; İKA yalnız simülasyonda koşar. Kullanıcı "beklemeden, onay
> almadan, aralıksız" çalışma yetkisi verdi (10 Eylül 00:3x). Mimar: bu oturum (Claude 2).
>
> **Kural (değişmez):** ÖLÇÜLEMEDİ ≠ GEÇTİ. Eşikler aşağıda önceden yazılır; ölçüm eşiği
> tutmazsa **eşik gevşetilmez**, sonuç olduğu gibi rapora girer. Her hat: ön kayıt → amele
> (worktree) → çürütücü (kapıyı kendisi koşar, mutasyon) → mimar birleştirme → `push_kapisi`.

## 0. Ölçülen başlangıç durumu (10 Eylül 00:40–01:20, iş akışı `fdr-sprint-harita`, 6/8 ajan)

| alan | durum | kaynak |
|---|---|---|
| Simülasyon | Gazebo Classic 11 + Podman zinciri tasarlanmış, **hiç koşmamış**; mesh 0/4; `recordings/` yok; bu makinede gz/podman/docker/WSL **yok** (ölçüldü) | harita `simulation` |
| Ortam kararı | **MuJoCo 3.13.0** venv'e kuruldu; ekransız render 1280×720 **17 ms/kare**; drone STL yüklendi | `ortam/mujoco_duman_cikti.txt`, `ortam/mujoco_duman.png` |
| İKA yazılımı | alıcı → kilit → waypoint takibi → sürücü soyutlaması **86 test yeşil**; fizik simde sürülemez (vel_cmd dinleyicisi yok); kinematik sabitler üç kopya, CONTRACTS'ta yok | harita `ika-otonomi` |
| İKA tasarımı | DDR'de **tam mekanik tasarım var** (488×440×310 mm, 9,40 kg, 4×Ø125 mm, skid-steer, 1,3 m/s, RPi5+STM32, 5 FEA, 50 satır BOM); FDR "yapısal tasarım yoktur" diyor — **çelişki, FDR'ye taşınabilir** | harita `ika-ddr`, `rapor/NAVITAS_IKA_DDR.docx` |
| Haberleşme | paket yapısı tam; UDP loopback p95 113 ms; **RF RTT/kayıp ve veri hızı ölçülmedi**, veri hızı sayacı yok | harita `comms-yks` |
| Yönerge boşluğu | Y-3.3.3-M01/M02/M03 + Y-4-M07 (iki bölümde puanlanan simülasyon) en yüksek etkili; Y-4-M06/M10/M12 belge güncellemesiyle kapanır; Y-3.2.1-T06 fonksiyonel sütun koddan yazılır | harita `fdr-yazilim-bosluk` |
| CAD | Quad STL'leri var; sabit kanat yalnız SLDPRT (zip); İKA CAD dosyası **yok** (SolidWorks montajı ekipte) | `dronesolid/` |

Ölçülen kod kusurları (okuyucular, D-438): `simulation/score.py:141` ve `iha_perceive.py --help`
cp1254 konsolda `UnicodeEncodeError`; `iha_detect_send.py` peer'siz `TypeError`; `arena.route_waypoints`
3,3 m segment > `MAX_SEGMENT_M` 2,10; `world_generator.py` iniş alanı 8×8 (yönerge 30×30) ve H beyaz
(yönerge kırmızı); `mission_demo.py` sabit üretim portlarına bağlanıyor; `ika_nav.MAX_SPEED` 2,0 > DDR 1,3.

## 1. Hatlar, kapılar, eşikler

### H1 — 3B görev icra simülasyonu (KRİTİK YOL) · Y-3.3.3-M01/M02/M03 · Y-4-M07
Ortam: **MuJoCo** (karar D-438). Zincir: mancınık fırlatma → İHA kinematik uçuş (sabit kanat
mesh'i) → 30 m nadir kamera taraması (MuJoCo render, `scan_N.jpg` + `poses.csv`, mevcut
`navitas_scan_cam.cc` sözleşmesi) → `iha_haritala.py` (ortomozaik → **üretim modeli v36** →
costmap A* → `rota.json`) → `comms` OPEN_ROUTE (UDP, mevcut protokol) → YKS/hakem onayı
(sim hakem, **SİM** etiketli) → IKA_GO → `ika_nav.navigate` + **MuJoCoSurucu** (`IkaSurucu`
arayüzü; DDR geometrili fizik İKA, skid-steer, teker hız komutu) → HB'ye varış → paraşütle iniş.

| # | kapı | eşik (önceden) | kanıt |
|---|---|---|---|
| H1-K1 | Arena MJCF üreteci `arena.py`'den, 15 harita deterministik (aynı seed → bayt-eş) | 15/15, yönerge geometrisi: İHA-İB 30×30 mavi, HB kırmızı H, bariyerli kapalı yol, moloz | `sim_mujoco/kanit/arena_*.json`, test |
| H1-K2 | Kamera taraması gerçek renderdan; mozaik kurulur | 15/15 haritada mozaik boyutu ≥ HTAB kapsaması | `kanit/mozaik_*.png` |
| H1-K3 | **Görüntü işleme ile rota tespiti — üretim modeli** (v36 `.pt`, sim'e özel eğitim YOK) | açık yol etiketi doğru ≥ **12/15**; sonuç ne çıkarsa yazılır | `kanit/rota_*.json`, `karar` |
| H1-K4 | Aktarım: OPEN_ROUTE ACK `['ika','yks']`, IKA_GO ACK | 15/15 | hakem_log.jsonl |
| H1-K5 | İKA otonom sürüş fizikte: HB'ye ≤ FINAL_WP_RADIUS, moloza çarpma yok, ≤ 600 s sim | ≥ **12/15** harita × 3 tohum = 45 koşum; oran rapora | `kanit/kosum_*.json` |
| H1-K6 | Sanal görev süresi ölçümü (sim saati) ve başarı oranı grafikleri | 45 koşum tablo + 4 grafik | `FDR/sekiller/sim_*.svg/png` |
| H1-K7 | Video: ≥ 90 s, HUD'lu, üç kamera (İHA nadir, üçüncü şahıs, İKA takip) | mp4 yazıldı, ≥ 24 FPS | `results/fdr_sprint_20260910/video/*.mp4` (link **insan**) |
| H1-K8 | Nöbetçi testler + mutasyon (arena determinizmi, sürücü arayüzü, metrik şeması, video varlığı) | hepsi OK, ≥ 3 mutasyon yakalanır | `tests/test_sim_mujoco_*.py` |
| H1-K9 | FDR §3.3.3 (M01–M03) ve §4.7 metni ölçümle; YONERGE_HARITASI satırları | çürütücü onayı | FDR diff |

Sınırlar (rapora yazılır): fizik İHA uçuşu kinematiktir (aerodinamik yok); hakem onayı sim'de
otomatiktir; OBB araç maskesi sim'de kapalıdır (sim'de araç yok); ışık/gölge çeşitliliği sentetik.

### H2 — Haberleşme ölçümü · Y-3.3.4-M03 · Y-4-M09
`scripts/sik_rf_olc.py`'a bayt/s ve paket/s sayacı; UDP loopback + TCP-seri köprüsünde gecikme ve
veri hızı ölçümü (yazılım); RF satırları **ÖLÇÜLEMEDİ** kalır, ekip radyoları taktığında aynı
betikle kapanır. `mission_demo.py` ephemeral port; T208 mesaj tipi sabitleri; README bayat notlar;
FDR §3.3.4.3 tarih düzeltmesi. Kapı: test dosyaları OK + ölçüm JSON'u.

### H3 — İKA yazılım/entegrasyon belgeleri · Y-3.3.1-M03 · Y-3.2.1-T06 · Y-3.3.1-M01(İKA)
CONTRACTS §4'e İKA kinematik sabitleri (tek kaynak; DDR: Ø125 mm teker, 1,3 m/s, iz genişliği
**TAHMİN 0,39 m** insan teyidine kadar); `ika_nav.MAX_SPEED` 1,3; İKA entegrasyon planı (yazılım
kolu: alıcı→kilit→navigate→sürücü, kabul turu K1–K6 GEÇTİ); İHA–İKA–Mancınık **fonksiyonel**
arayüz tablosu koddan (fiziksel sütun BEYAN GEREKLİ); İKA renk kodlu şeması **DDR tasarımından**
("DDR tasarımı, tedarik yok" etiketli; kaynak DDR BOM/mimari). Kapı: nöbetçi testler.

### H4 — FDR §3.2.2 İKA (T01–T11, A01–A03) DDR'den · Bölüm 3 (40 puan)
DDR docx içeriği (master geometri, BOM, kütle dağılımı, malzeme, FEA, yerleşim, parça numaraları)
FDR'ye "DDR'den; FDR'de üretim yok" etiketiyle taşınır; görseller `word/media` → `FDR/sekiller/ika_ddr_*.png`.
T08 tedarikçi, T10 tartı **BEYAN GEREKLİ** kalır. Kapı: her tablo DDR sayfa/tablo atfı taşır; çürütücü
rastgele 10 sayıyı docx'ten yeniden okur.

### H5 — Bölüm 4 belge güncellemeleri (yazılımla kapananlar)
Y-4-M06 (6 Eylül dökümü INS/COMPASS ofsetleri → §4.6), Y-4-M10 (D-429 tlog analizi → BOLUM_4),
Y-4-M12 tablosu (RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ), Y-4-M03 takvim (ölçülen olaylarla), bayat satırlar
(score.py yolu, YONERGE :150/:171, README :135). Kapı: FDR testleri + çürütücü.

### H6 — Saha koşum kâğıdı (ekip için, tek sayfa)
Jetson+Pixhawk `mavlink_dogrula` 3/3, CSI kamera köprüsü, SiK çifti `sik_rf_olc` (+ veri hızı),
PM06 pervaneli akım kaydı, tartı. Her komutun beklenen çıktısı ve eşiği. (İnsan bunları koşar;
sonuçlar ÖLÇÜLEMEDİ satırlarını kapatır.)

### H7 — (zaman kalırsa) ışık/gölge sentetik kesiti · Y-3.3.4-M02
Sentetik aydınlatma artırımıyla karışıklık matrisi; **SENTETİK** etiketiyle.

## 2. Kritik yol ve sıra
H1.0 ortam ✅ → H1.1 arena+mesh → H1.2 İHA uçuş+kamera → H1.3 mozaik+model → H1.4 aktarım →
H1.5 İKA fizik sürüş → H1.6 45 koşum + grafik → H1.7 video → H1.8 test → H1.9 FDR. H2/H3/H4/H5
paralel hatlarda koşar; H6 hemen (ekibe verilir). GPU işleri sıralı (BSOD kuralı).

## 3. İnsan girdileri (sorulur; cevap gelmezse varsayılanla ilerlenir, etiketlenir)
1. Sabit kanat İHA STL dışa aktarımı (SolidWorks `Fuselage+Wing+Tail`, kontrol yüzeyleriyle). **Varsayılan:** DDR ölçülerinden basitleştirilmiş mesh, "basitleştirilmiş CAD" etiketi.
2. İKA STL dışa aktarımı (`Montaj6v2v20` gövde + tek teker). **Varsayılan:** DDR ölçülü primitif mesh.
3. İKA iz genişliği / dingil mesafesi / kamera yüksekliği-eğimi. **Varsayılan:** 0,39 m / 0,36 m / 0,25 m, 15°.
4. FDR'de İKA hattı beyanı: repo protokolü (NAVITAS çerçeve, UDP sim) mi, DDR MAVLink iki-atlamalı mı. **Varsayılan:** repo protokolü; DDR→FDR değişikliği gerekçesiyle yazılır.
5. Video barındırma (YouTube liste dışı / Drive) — **insan**; mp4 mimar üretir.
6. Ekip FDR `.md` dosyalarını doğrudan düzenliyor mu? **Varsayılan:** hayır (düzenliyorsa ayrı dalda).
7. Tezgâh ölçümleri (H6 kâğıdı): ne zaman yapılabilir? (engellemez)

## 4. Kapanış kapısı (mimar)
Her hat: tam süit OK + genel kapı 15/15 · 15/15 + FDR testleri + `push_kapisi`. Sprint sonu:
YONERGE_HARITASI yeniden sayım; ACIK_KALEMLER güncel; PDF üretimi; pano.

### H8 — Jetson geliştirici istekleri (eklendi 10 Eylül 01:5x; kaynak `JETSON_OTURUM_DURUMU_20260909.md` §5)
T220 (K2 T66 kabul kümesi + göreli defter yolları, G4 v36 PC referans kararları, K10 çıplak `O:\` yolları,
K1 kalan bant) ve T221 (K11 ArduPlane parametre seti + SITL). Kapı: PC tam süit yeşil; Jetson koşumu İNSAN.
Uzak push'lar 10 Eylül 01:29'da birleştirildi (`0e788eb`: OGREN_ADIYAMAN dizisi, Jetson oturum notu).
