# 15 · SÖZLÜK — terimler, kısaltmalar, projeye özgü adlar

> Yönerge kısaltmaları FDR Bölüm 0'dan; takım terimleri CONTRACTS ve koddan. Alfabetik değil, **konuya göre** gruplanmış.

## Yarışma
- **DDK** Danışma ve Değerlendirme Kurulu (TUSAŞ mühendisleri; jüri). **TUSAŞ** Türk Havacılık ve Uzay Sanayii (düzenleyici).
- **ÖDR / DDR / FDR / UHDR** Ön / Detay / Final Değerlendirme Raporu / Uçuşa Hazırlık Değerlendirme Raporu. **FDA** Final Değerlendirme Aşaması (FDS sunumu + drone görev test uçuşu, 30 Eyl–3 Eki). **FDS** Final Değerlendirme Sunumu. **SGGS** Sistem Gözden Geçirme Sunumu (Şubat 2027; üretim tutarlılığı kontrolü).
- **HTAB** Hedef Tespit Alan Bölgesi 50×50 m. **İHA-FB / İHA-UB / İHA-İB** fırlatma / uçuş (300×300) / iniş (30×30) bölgeleri. **İKA-KB** İKA başlangıç 1×1 m. **HB** Hedef Bölge 2×2 m, kırmızı H.
- **K_zorluk** 1,0/1,5/2,0 (Kolay/Orta/Zor; açık güzergâhın zorluğu). **P_görev** 600. **P_TI / P_uçuş / P_centilmenlik** teknik muayene / uçuş / centilmenlik. **C_ceza** −5/m, −100, −50.
- **Görev test uçuşu (§5.3.2)** quad, 20×20 m, ≥30 m, ≤10 dk, İKA yok. **Yarışma görevi (§2.2)** sabit kanat + mancınık + paraşüt + İKA, 2027.

## Sistem birimleri
- **İHA** hava aracı (FDA: 3B baskı quad; final: sabit kanat). **İKA** kara aracı (donanımı henüz yok). **YKS/YKİ** yer kontrol istasyonu (dizüstü, `yks_gui.py`, hakem ekranı).
- **Pixhawk 6C** uçuş kontrolcüsü; **ArduCopter 4.5.7** üstündeki yazılım; **Mission Planner** PC yer istasyonu programı; **parametre** `AD,DEGER`; **failsafe** kopma tepkisi (RTL eve dön, Land yerinde in); **geofence/çit** irtifa/yarıçap sınırı; **PM06** güç modülü; **ESC** motor sürücü (Skywalker 60A); **iBUS** FlySky alıcı protokolü; **SiK** 433 MHz telemetri telsizi.
- **Jetson Orin Nano DevKit 4 GB** görev bilgisayarı (JetPack 7.2.1); **CSI** kamera arayüzü (IMX477); **çoğullayıcı** MAVProxy, seri Pixhawk'ı UDP'ye çoğaltır; **seri hub** SiK'i UDP'ye çoğaltır; **systemd birimi** otomatik başlayan servis.

## Görüntü işleme
- **Segmentasyon** her pikseli sınıfa boyama; **YOLOv8-seg** kullanılan ağ (m boyutu); **imgsz** giriş kenarı (512); **maske** ikili piksel haritası; **letterbox** kareye dolgu (114 gri); **tuval / içerik** dolgulu kare / gerçek görüntü dikdörtgeni.
- **Sınıflar** 0 traversable/zemin (otorite), 1 blocked/engel, 2 hedef (yalnız etiket üreteci). **Costmap katmanları** 0 zemin, 1 moloz, 10 araç.
- **mAP50 / IoU / kaplama / kenar dayanma** doğruluk özeti / kesişim-birleşim / maskenin karedeki payı / maskenin kenara dayanma oranı.
- **Ön-eğitim, fine-tune, epoch, batch, augmentasyon, copy-paste, mozaik** — 02 §2.2.
- **Sızıntı** doğrulama görüntüsünün eğitimde olması. **Bakir küme** eğitime hiç girmemiş küme (0038). **Kör etiket** model çıktısı görülmeden etiketleme. **Üç durumlu maske** 0 etiketsiz / 1 zemin / 2 engel.
- **DOTA OBB** nadir görüntü araç dedektörü (döner kutu). **COCO** yer seviyesi genel dedektör (reddedildi).
- **Sentetik arena** kendi üretecimiz (`51_sentetik_arena.py`). **T66** kabul kümesi (260 sentetik kadraj, PC'de). **ACILI_t189** 90° bariyerli ikinci küme. **kompozit** gerçek otopark + yapıştırılmış moloz.

## Rota ve karar
- **serbest alan** zemin AND NOT engel. **distance transform (dt)** her pikselin en yakın engele uzaklığı. **C-uzayı** `dt ≥ r_gerekli` bölgesi. **`R_GEREKLI_M`** 1,10 m. **mpp** metre/piksel (ölçek). **FOV** kamera yatay görüş açısı (beyan edilir).
- **A\*** ızgarada en ucuz yol arama; **açıklık ağırlıklı** dar yerleri pahalı sayan maliyet; **tanık yol (witness)** koridorun geçilebilir olduğunun kanıtı olan yol; **string-pulling / `yol_duzelt`** yolu görüş hattıyla kısaltma; **waypoint** rota noktası (yerel metre).
- **K-A** uç-bant teması kapısı; **K-B** güven eşiği 0,20; **histerezis** şerit değişimi için K=3 kare teyit; **ret sebebi** OLCEK_YOK … KORIDOR_DEGIL (04 §2.6).
- **road / şerit** 1 sol · 2 orta · 3 sağ (içerik kutusunun üçte birleri); **`serit_karari`** rotanın gövdesinin şeridi; **darboğaz** rotanın en dar noktası.
- **`analyze_path`** üretim karar yolu; **`rota_bul`** tanısal yol (koridor envanteri: ACIK / KAPALI_DAR / KAPALI_KOPUK / BELIRSIZ_*).
- **Katman 1/2/3** otorite / emniyet ağı (yalnız çıkarır) / geometri. **Monotonluk / invariant** `serbest(K1∧¬K2) ⊆ serbest(K1)`.

## Haberleşme
- **OPEN_ROUTE / NO_ROUTE / HEARTBEAT / ACK / CMD / IHA_LANDED** mesaj tipleri; **seq** düğüm başına sayaç; **`ref_tip`** ACK'in hangi tipe ait olduğu; **`karar_yas`** son algı kararının yaşı; **node** iha/ika/yks.
- **IKA_GO** YKS'nin manuel intikal komutu; **latch** kilitli durum (ika_go, iha_landed); **üçlü kilit** OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO; **K1/K4/K8** şartname boşluk raporunun haberleşme kalemleri (yayın, IKA_GO ACK, aktarım kanıtı).
- **MAVLink** Pixhawk dili; **sysid/compid** araç/bileşen kimliği (1/1); **HEARTBEAT, GLOBAL_POSITION_INT, EXTENDED_SYS_STATE, GPS_RAW_INT, SYS_STATUS** mesajlar; **COMMAND_LONG / COMMAND_ACK** komut/cevap; **SET_MESSAGE_INTERVAL** akış isteği; **`relative_alt`** home'a göre irtifa; **`landed_state`** yerde/havada.
- **hakem kaydı** `hakem_log.jsonl` (fsync'li kanıt); **oturum künyesi** model sha + commit + argümanlar; **`--fda` kipi** görev test uçuşu ayarı.

## Süreç
- **Anayasa** `CLAUDE.md`; **mimar (Claude 1)**, **başamele (Claude 2)**, **Codex 1/2**, **red team (gpt-oss-120b)**, **Qwen** temizlik. **T-numarası** görev; **D-numarası** kusur/karar kaydı; **K-numarası** mimari karar (ARCHITECT_PLAN) ya da kabul kapısı (K0–K8) — bağlama göre; **S1–S8** serbest alan mimarisi görevleri; **P1–P9** Faz A kalemleri; **G-serisi** FDR gece görevleri; **R1–R22** şartname yükümlülük satırları; **Y-…** FDR yönerge kimlikleri; **A1–A13** FDR açık gereksinimleri; **R1–R8** roller (Kaptan … Kanıt-kalite).
- **Genel kapı** 15/15; **tam süit** unittest; **ön kayıt (ON_KAYIT)** eşik sonuç görülmeden; **mutasyon kontrolü** kusuru geri koy, test düşsün; **çürütücü turu** bağımsız ajan iddia kırar; **vakum kapı** bir şeyi kilitlemeyen yeşil test; **pozitif kontrol** kapının yakalayabildiğini gösterme; **ÖLÇÜLEMEDİ ≠ GEÇTİ**; **BEYAN / ÖLÇÜM / DOĞRULANACAK / BEYAN GEREKLİ (insan)** FDR etiketleri; **fail-closed / fail-visible / fail-dangerous** şüphede dur / hatayı göster / şüphede geç.
- **Push kapısı** `push_kapisi.py`; **HANDOFF / DEVAM** devir belgeleri; **worktree / workflow** paralel dal çalışmaları; **tek doğruluk kaynağı** CONTRACTS, registry; **ayna** `jetson_paket/` kopyası; **mühür** `surum_dondur.py` sha künyesi; **madde 16 / 17 / 18** çıplak sabit yasağı / commit kuralı / silme yasağı.
- **Faz A / B / C** 1–4 Eyl yazılım / 5–6 Eyl donanım / 7–20 Eyl prova-dondurma-FDR. **Gün-1** Jetson kontrol listesi. **K1–K11 (D-431)** Jetson oturumundan çıkan düzeltme listesi (D-431 §4).

## Sayılar (hızlı erişim)
0,61 FPS eşik · 1,35/1,06 pt · 1,58/1,33 engine · 1,10 m yarıçap · 0,20 güven · 0,55/0,40 kaplama · 5 s tazelik · 0,5 s irtifa tazeliği · 900/600/900 s süreler · 32 m kalkış ·
60 s loiter · 221,5 s bütçe · 15/15 genel kapı · 260 kabul kümesi · 88 K7 kümesi · 84/85 K7 · 8/16 gerçek kare · 3/126 engine denkliği · 2204 test (9 Eyl) · 441 D-kaydı · 606 commit ·
45 yükümlülük / 32 kanıtlı · 13 açık gereksinim · 5005/5006/5007/5100 UDP · 14550–14552 MAVLink · 8080 kamera · 57600 baud.
