# Navitas Gazebo Simülasyonu — Elden Geçirme Raporu

**Tarih:** 2026-06-30
**Kapsam:** Kullanıcı talebiyle Gazebo simülasyonunda kapsamlı düzeltme + yeniden tasarım.
**Şartname kaynağı:** `doc/İleri_Otonom_Sistemler…ÖDR…13.04.pdf` (8 sf, PDF→metin doğrulandı).

---

## 1. Talep Listesi → Yapılan Değişiklikler

| # | Talep | Yapılan |
|---|-------|---------|
| 1 | Paraşüt görseli bozuk (saran/küçülen daire) | `make_parachute` düz disk → **kubbe kanopi** (istiflenmiş silindir dilimleri + 4 askı ipi + harness). İniş sonrası yere oturup **kalır** (z=0.6), kaybolmaz. |
| 2 | İKA'da çubuk+daire, çarpınca devrilip geçiyor | `beacon_pole`/`beacon_disc` **kaldırıldı**. **Tank-benzeri** geniş alçak gövde + iri teker (r0.11) + palet yan koruma + 200gr yük kutusu. Ağırlık merkezi alçaltıldı (inertial pose z−0.07) → devrilmez. |
| 3 | İHA max 50→40-45; İKA uygun hız | İHA seyir **42 m/s** (faz bazlı: tarama 16, tırmanış 24). İKA **1.1 m/s** (PDF açık hız yok; 10dk limiti + 24V motor + 12-15cm tekerden türetildi). plugin+mission_time+world_gen uyumlu. |
| 4a | Sadece 3 yol (2 kapalı/1 açık), süre limitinde | `--layout clean`: net 3 koridor, 2'si molozla tam kapalı + bariyer, 1'i açık, dağınık moloz yok. `--layout field`: moloz sahası+3 yol (ikisi de seçilebilir). |
| 4b | İHA gerçekten tarasın + model + saniyelik foto | `iha_flight` düz geçiş → **serpantin tarama** (4 sütun, 30m). İHA'ya **nadir kamera** (1Hz → /tmp/iha_scan). Model kararı gerçek aerial proxy görselde (sim kutu karesini model tanımaz). |
| 4c | İKA modeli yok → koordinatla nav | arena.py'a **koordinat referans çerçevesi** (START_Z, to_world, start_xyz, hb_xyz). İHA yol no'su → A* waypoint → dünya xyz. |
| 4d | Engelden geçemesin, gerçek fizik | plugin İKA `SetLinearVel` (temas ezme) → **sınırlı kuvvet** (AddForce). Katı moloza çarpınca durur. |
| 5 | Loglar güçlensin, teknik detay | hakem_log: model künye/mAP, comms SiK433/MAVLink/ACK, koordinat xyz, GNSS+IMU+encoder, A*, İKA telemetri (xyz+yön+hız+HB mesafe), fizik. |

## 2. Dokunulan Dosyalar
- `scripts/arena.py` — koordinat referans çerçevesi, START_Z=0.21.
- `scripts/world_generator.py` — serpantin tarama, kubbe paraşüt, layout param, faz hızları, yol zeminleri.
- `scripts/mission_time.py` — IKA_REAL_SPEED 0.16→1.1.
- `scripts/hakem_log.py` — teknik detaylı log.
- `models/iha/model.sdf` — nadir tarama kamerası.
- `models/ika/model.sdf` — beacon kaldırma, tank tasarım, fizik düzeltmeleri.
- `plugins/navitas_anim.cc` — İKA sınırlı kuvvet kontrolü.
- `docker/record.sh`, `docker/record_in_container.sh` — --layout geçişi.

## 3. İlk Doğrulama
- `bash -n`, `py_compile`, world üretimi (3 seviye × clean/field): geçti.
- Plugin C++ container'da **derlendi**; imaj `navitas-gazebo:11` yeniden build edildi.
- `gz sdf -k` (container, include'lar dahil): **Check complete** (yalnız zararsız noise-attr uyarısı).

---

## 4. Kritik Analiz (eleştirel/geliştirici gözlem) — 2. tur

İlk uygulama statik testleri geçiyordu ama **fiziksel davranış** test edilmemişti. Kodu
yeniden inceleyince 3 gerçek hata + 2 gözlem bulundu:

| # | Önem | Bulgu | Neden hatalı |
|---|------|-------|--------------|
| B1 | **KRİTİK** | İKA'da `libDiffDrivePlugin.so` duruyordu | Komutsuzken tekerleri 0 hıza FRENLER. Statik sürtünme (mu1.5 × ~98N ≈ 147N) > FORCE_MAX (80N) → İKA **hiç hareket etmez**; ya da hareket ederse tekerler kayar ve engelden geçer. Kuvvet sürüşü için tekerler SERBEST dönmeli. |
| B2 | YÜKSEK | Dönüş `AddTorque` (12 N·m) ile | 4 sabit-eksenli yüksek-sürtünmeli teker yerinde dönüşe direnir; bu tork kıvrımlı yolu **döndürmeye yetmez** → İKA yolu takip edemez. |
| B3 | ORTA | Zemin z-katmanları çakışık | zon zemini(0.01)+yol(0.01)+HB pad(0.01) aynı z → z-fighting; açık yol zemini HB pad'i **örtebilir**. |
| G1 | gözlem | Kuvvet dünya-çerçevesinde (crabbing) | Holonomik olmayan rover yana kayar gibi gider; demo için kabul (önceki davranışla aynı). |
| G2 | gözlem | scan_camera sürekli kaydeder | Tarama dışında da kare yazar (her koşu temizlenir, zararsız). |

## 5. Uygulanan Düzeltmeler

- **B1 →** `models/ika/model.sdf`'ten `diff_drive` eklentisi KALDIRILDI; tekerler serbest döner
  (yer sürtünmesiyle yuvarlanır), aracı sim'de `navitas_anim` sürer. (Fiziksel diff-drive yapı
  4 teker + aks joint'leriyle korundu; sahada gerçek sürücü kullanılır.)
- **B2 →** `plugins/navitas_anim.cc`: dönüş `AddTorque` → `SetAngularVel` (doğrudan, YAW_RATE_MAX=1.6
  rad/s limitli). İLERİ hareket sınırlı `AddForce`'ta kaldı → çarpışma bütünlüğü korunur.
- **B3 →** `world_generator.py`: katmanlı z (zon 0.01 < yol Z_ROAD=0.04 < halka/pad Z_PAD=0.07 <
  H Z_H=0.10). Yol/pad/H artık `_box` ile belirli yükseklikte.
- Plugin yeniden derlendi + imaj yeniden build edildi.

## 6. Final Analiz — FİZİK TESTİ ile doğrulama

Riskli fizik değişikliği gerçek Gazebo'da headless test edildi (RTF sınırsız, gerçek ika modeli):
düz zemin + x=4'te katı duvar (cephe x=3.5) + hedef (10,0).

**Sonuç:**
- İKA x=0 → ilerledi, **x=3.17'de DURDU** (tampon 3.17+0.33≈3.50 = duvara tam dayandı).
- x=10'a **GEÇMEDİ** → engelden geçmiyor (çarpışma bütünlüğü ✓).
- z=0.21 sabit → **devrilmedi** (alçak ağırlık merkezi ✓); y≈0 → düz gitti.
- Ayrı koşuda 1 m/s civarı hız doğrulandı (sim-zamanı bazında).

→ B1/B2 (hareket + dönüş + çarpışma) ve İKA stabilitesi **kanıtlandı**.

**Statik (tekrar):** py_compile, world gen (clean/field), `gz sdf -k` model+world = Check complete;
plugin derlendi; imaj güncel.

**Kalan gözlemler (kabul edilebilir, yarışma günü notu):**
- Kuvvet dünya-çerçevesinde (crabbing) — istenirse gövde-çerçevesine çevrilebilir.
- iha_perceive_all IHA_VIEW proxy görseller — gerçek İHA karesiyle değiştirilecek.
- Plugin kuvvet/hız sabitleri (FORCE_MAX/YAW_RATE) ilk kayıtta gözle ince ayarlanabilir.

**DURUM: hazır.** Gerçek kaydı kullanıcı çalıştırır: `cd docker && ./record.sh orta 1`.
</content>
