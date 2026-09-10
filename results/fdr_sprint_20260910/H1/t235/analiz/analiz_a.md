# Analiz A: rota ve etiket zinciri (salt okuma, SENTETİK bağlam)

Depoda hiçbir dosyayı değiştirmedim. Dal dosyalarını `git show worktree-wf_2c28e623-233-7:` ile okudum. Geçici çıktılar `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\` altında: `skt_dal.py`, `gk_dal.py`, `ozet.py` ve üç `uretim_*_42.json` dosyası.

**Ana sonuç:** Kanıtlanan iki risk (a ve b) kod hatası değil, sözleşmenin kendisi. CONTRACTS.md:1048 "sahada dünya çerçevesi yoktur" diyor. CONTRACTS.md:185-188 da yalnız saf öteleme tanımlıyor; dönme yok. Ayrıca simülasyon, üretimde olmayan iki bilgiyi dışarıdan veriyor. Bu yüzden T214-A'nın üretim sayıları sahaya göre **iyimser bir üst sınır** (§1.7).

## 1. Kod zinciri, satır satır

### 1.1 Kare → karar (`codes/rpi_inference.py`, `run_camera` 2298–2419)

| adım | satır | ne yapıyor |
|---|---|---|
| kare okuma | 2335 | `for frame in kamera_kareleri(cap, ozet)` — yakalama zaman damgası tutulmuyor |
| letterbox | 2356 → `_preprocess` 1892–1918 | tuval `max(h,w)²`, içerik kutusu `(x0,y0,w,h)` |
| çıkarım | 2360 | `model.predict` |
| ölçek | 2369 → `_kare_olcegi` 398–409 → `CanliOlcekSaglayici.kare_mpp` 358–371 | irtifa **çıkarımdan SONRA** okunuyor (§2) |
| rota | 2376–2386 | `analyze_path(..., goruntu=sq)` — **`rota_ekseni_derece` geçirilmiyor.** Parametre 1356'da var, 1412–1423'te uygulanıyor. Docstring (1369–1370): "Uretimde eksen UYDURULMAZ: kaynak operatorun KB->HB kerterizi". CLI'de bu parametreye bağlanan hiçbir yol yok; grep yalnız 1356 ve 1423'ü buluyor. |
| yayın | 2399 → `_karari_yayinla` 285–294 | `KararYumusatici` (karar_sozlesmesi 2139–2195) yalnız etiket histerezisi uygular, geometriye dokunmaz |

### 1.2 Rotanın uçları

- **Başlangıç:** her zaman içerik kutusunun **alt bandı**. `_uc_tohum_maskeleri` 972–984; bant yüksekliği `HEDEF_BANT_ORANI = 0.08` (karar_sozlesmesi:13).
- **Bitiş:** HB görünürse HB kutusu (1696–1706). HB görünmezse `HEDEF_YOK` ile ret (1697–1698).
- **KB tespiti ya da beyanı üretimde hiç yok.** rpi_inference'ta "KB" yalnız docstring'lerde geçiyor (1293–1295, 1369).

### 1.3 Etiket (`road`) — kusur (a) tam burada

- Çağrı yolu: `analyze_path` 1735 → `_rota_serit_olcumu` → 1248 `rota_serit_karari(kirpilmis, icerik_x0, icerik_w)` → 1766 `open_path = olcum["serit_karari"]`.
- Tanım, `codes/karar_sozlesmesi.py`:
  - `serit_no` 42–54: `x < x0 + w/3` ise 1, `x < x0 + 2w/3` ise 2, aksi hâlde 3.
  - `rota_serit_karari` 57–98: rotanın en çok pikselinin düştüğü şerit kazanır.
- **Girdiler yalnız rota piksellerinin x değerleri ile içerik kutusunun `x0` ve `w` değeri.** Konum, yaw, HTAB sınırı ve dünya koordinatı yok.
- İki örtük varsayım var:
  1. Kare HTAB'a yatayda ortalanmış.
  2. Görüntü-yukarısı = KB→HB yönü.
- Sözleşmedeki tanım: CONTRACTS.md:588–592 (§6.2).

Ölçüm kanıtı (dal, `kosum_tur3/uretim_5_zor_42/karar_toplayici.json`, `ozet.py` çıktısı). Dünyadaki rota aynı kalıyor (orta yol), ama İHA'nın x konumu değiştikçe etiket değişiyor:

| kare | İHA x | yayınlanan etiket | dünyadaki yol |
|---|---|---|---|
| n=9 | −18 | 3 | 2 |
| n=15 | −6 | 2 | 2 |
| n=20 | +6 | 1 | 2 |

İkinci örnek, `uretim_2_kolay_42` n=9: İHA x=−18, etiket 2, dünya yolu 1. Yol merkez hatlarına ortalama uzaklık: yol 1 için 0,33 m, yol 2 için 11,89 m, yol 3 için 15,31 m.

Tarama bacakları x = −18 / −6 / +6 / +18 m'de (kare sayısı 3/4/4/4).

### 1.4 Waypoint çerçevesi

1. rpi waypoint'leri **tuval pikseli** (docstring 1402; maskeler `sq` boyutunda, 2357).
2. `KararYayinci.karar` 371–384 → `_karari_gonder` 416–449 → `piksel_rotayi_yerele_cevir` (`comms/iha_sender.py` 271–298) dönüşümü:
   - `x = (px − px0)·mpp`, `y = (py0 − py)·mpp` (284–286)
   - ilk nokta `[0, 0]`
   - `ref_xy = YAYIN_REF_XY = (0.0, 0.0)` (karar_sozlesmesi 160–162; iha_sender 298, 444)
3. `mpp` nadir kamera varsayımıyla hesaplanıyor (`mpp_irtifadan`, karar_sozlesmesi 395–429, docstring 397: "Nadir (90 derece)").

**Sonuç:** waypoint'ler **kamera gövde çerçevesinde metre** cinsinden. x = görüntünün sağı, y = görüntünün yukarısı; orijin = rotanın alt banttaki ilk pikseli. Dünya ya da kuzey çerçevesi değil; İHA konumuna da bağlı değil.

### 1.5 Protokol

`comms/protocol.py` `open_route` 54–85 şu alanları taşıyor: `road`, `label`, `conf`, `ref_xy`, `waypoints`, `seq`, `t`.

- `t = time.time()` (82) mesajın **oluşturulma anı**; kare yakalama anı değil.
- Poz alanı yok.
- Geometri denetimi yalnız `ika` ya da `broadcast` akranı varken koşuyor (iha_sender 234–235).

### 1.6 İKA tarafı (`simulation/scripts/ika_nav.py`)

Çağrı sırası: `ika_gorevi` 477–548 → `navigate_route` 455–470 → `route_to_world_waypoints` 149–205.

- İlk yerel nokta `[0,0]` olmalı, tolerans 0,15 m (48, 197–200). Kapsam ≤ 60 m (47, 201–202).
- **Saf öteleme 203. satırda:** `world_waypoints = [(ref_x + x, ref_y + y) ...]`. CONTRACTS.md:188 hâlâ `:206` diyor; bu satır kayması.
- `navigate` 311–452 hedef farkını `dx = wx − cx` ile, konumu `get_pose()` üzerinden sürücünün dünya çerçevesinden alıyor (399, 413–414). Yaw hareket geçmişinden tahmin ediliyor (333–336, 405–411). Rota döndürülmüyor.

`ref_xy=[0,0]` olduğu için rota, **sürücünün konum çerçevesinin ORİJİNİNE ve EKSENLERİNE** oturuyor; İKA'nın o anki konumuna değil. Sahada doğru sürüş için iki şart gerekiyor, ikisi de hiçbir yerde kurulmuyor:

1. Sürücü çerçevesinin orijini = rotanın alt banttaki başlangıç noktasının yerdeki karşılığı.
2. Sürücü çerçevesinin +y ekseni = kare yakalandığı andaki görüntü-yukarısı yönü.

Sahadaki İKA konum çerçevesi de **tanımsız**:
- `GercekSurucu.konum_al` → `arka_uc.konum_al` (`ika_surucu.py` 186–206). Arka uç "Faz B'de (5 Eylül) doldurulacak" iskeleti olarak duruyor.
- Repoda gerçek bir arka uç yok. `GercekSurucu(` yalnız `scripts/ika_surucu_kabul.py:186`'da geçiyor ve `--arka-uc` verilmezse `DONANIM_YOK` ile reddediliyor.

### 1.7 Simülasyon neden iyimser

- `gorev_kosumu.uretim_rota` (dal, `gk_dal.py:312–315`): `ref = H["kb"]`, yani **gerçek KB dünya koordinatı** İKA'ya veriliyor. Üretim `[0,0]` gönderir.
- Kerteriz beslemesi kareyi yaw'a göre kuzey-yukarı döndürüyor (`skt_dal.py:179–184`, `np.rot90`). Böylece yerel y = kuzey oluyor. Üretimde bu döndürme yok.
- Bu iki yardıma rağmen başlangıç noktası KB'den medyan 17,84 m kaymış sürüldü (README_T214A §4, n=12). Örnek: `uretim_2_kolay_42` rota ilk noktası dünyada (−16,36, −16,47); KB (0,9, −23,0); aradaki mesafe 18,46 m.
- Sahada bu iki yardım olmayacağı için hata en az bu kadar büyük olur (TAHMİN).

### 1.8 Belge tutarsızlıkları (kodu etkilemiyor, kayıt için)

- `rpi_inference.py:1218` ve `comms/ika_receiver.py:11` (`plan_path(route["road"])`) `road`'u İKA'nın planlama girdisi olarak anlatıyor. CONTRACTS.md:681–684 (D-166) ve ika_nav 174–177 bunun tersini söylüyor. Koddaki gerçek davranış: `road` sürüşte kullanılmıyor.
- CONTRACTS.md:682 `ika_nav.py:178-182` diyor; ilgili satırlar 174–177.

## 2. Karar anında elde olan ve olmayan bilgi

| bilgi | üretimde var mı | karara ya da rotaya giriyor mu | kanıt |
|---|---|---|---|
| Bağıl irtifa (`relative_alt`) | VAR | yalnız `mpp` hesabına | inis_kaniti 18–27, 179–194; tazelik 0,50 s (karar_sozlesmesi:345) |
| Kare ↔ irtifa zaman eşlemesi | **YOK** | — | irtifa çıkarımdan sonra okunuyor (rpi 2360 → 2369); kare damgası yok; kamera_koprusu'nda damga yok (grep yalnız `logla`) |
| lat/lon | VAR (okuyucuda) | **hayır**, yalnız HEARTBEAT'e gidiyor | inis_kaniti 196–225, 811–870; rpi `_telemetri_saglayici` 2637–2669; iha_sender 451–510 |
| İHA-UB yerel x,y | yalnız `--ub-referans` verilirse | hayır, yalnız HEARTBEAT (alan ihlali denetimi) | rpi 2599–2618, 2663–2667; `jetson_baslat.sh:101,226` (varsayılan boş) |
| Yaw / heading (`GLOBAL_POSITION_INT.hdg`) | VAR (`yon`) | **hayır**, yalnız HEARTBEAT | inis_kaniti 291–313; yks_gui 1762, 2305–2316 |
| Roll/pitch (ATTITUDE) | **YOK** | nadir varsayılıyor | `MAVLINK_TELEMETRI_MESAJLARI` ATTITUDE içermiyor (inis_kaniti 24–27); akış isteği yalnız EXTENDED_SYS_STATE / GLOBAL_POSITION_INT / GPS_RAW_INT (iha_inis_yayinci 91–99; mavlink_dogrula 80–95) |
| Kameranın gövdeye göre montaj yönü | **YOK** (sözleşmede yok) | hayır | yalnız ayna yasağı var (tests/test_t201_kamera_yonu.py) |
| KB konumu | **YOK** | hayır | rpi'de KB tespiti yok; saha_kuru_kosu halka 6 yalnız HB'yi arıyor (683–745) |
| HB | karede piksel olarak | bitiş tohumu olarak; dünya konumu yok | rpi 1696–1706 |
| Rota ekseni / kerteriz | parametre var | **geçirilmiyor** | rpi 1356, 1412–1423; run_camera 2376–2386 |
| Yayın zaman damgası | OPEN_ROUTE `t` (yayın anı); `karar_yas` (`karar()` çağrı anı) | tanı amaçlı | protocol:82; iha_sender 371–384, 489–497 |
| Sahadaki İKA konum çerçevesi | **tanımsız** | sürüşün tek konum referansı bu | ika_surucu 186–206 |

**Zaman farkı (TAHMİN):** Jetson ~1,35 FPS'te (D-431) kare ile irtifa okuması arasında ~0,7 s'e varan fark olabilir. MJPEG köprüsünün gecikmesi ölçülmedi.

**Tek kare ayak izi (TAHMİN, hesap):** 30 m irtifada sim kamerası (hfov 74,5°) 45,6 × 45,6 m görüyor. Gerçek HQ + 6 mm (~55°) 31,2 m genişlik veriyor; yükseklik 16:9'da 17,6 m, 4:3'te 23,4 m. 46 m'lik KB–HB mesafesini tek karede görmek için gereken irtifa, yol görüntü dikeyinde uzanıyorsa 4:3'te ~59 m, 16:9'da ~79 m; yatay eksende uzanıyorsa ~44 m. Hepsi gerçek kamerada ÖLÇÜLMEDİ. Simde bile KB ve HB aynı karede 0/225.

## 3. YKS hakem ekranı (`comms/yks_gui.py`)

**OPEN_ROUTE alındığında:**
- `ROTA_ALINDI` kanıtı yazılıyor: road, label, conf, waypoint sayısı, ankor (1590–1593).
- Karar kutusu yeşil `"road · LABEL"` gösteriyor (1604–1607). Detay satırı `ref=(0,0) m · N waypoint` (1611–1613).

**Harita:**
- Şeritler sabit çiziliyor: `SERIT_CIZIM_TABLOSU` x = 12,5 / 25 / 37,5 m, y 4→46 m (102–106).
- `road` şeridi yeşil, diğerleri kırmızı "✕ KAPALI" (1327–1359). KB (25,2) ve HB (25,48) sabit (1362–1368).
- Rota şöyle çiziliyor: `road` şeridinin giriş ankoru + `ref_xy` + yerel waypoint'ler (`rota_gosterim_geometrisi` 212–236; 1371–1383).
- Harita kuzey-yukarı (`_mxy` 1295–1302). Waypoint eksenleri ise görüntü eksenleri; araya döndürme girmiyor.
- Ekranda uyarı var: "SEMATIK GOSTERIM — serit tablosundan turetildi, GPS degil" (108–109, 1406–1411).

**Sonuç:**
- Hakem, kare-göreli etiketi dünya şeridi gibi boyanmış görüyor. Etiket yanlışsa (sim kerteriz OPEN_ROUTE karelerinde 5/8) yanlış şerit yeşil yanıyor ve rota o şeridin girişinden çiziliyor.
- Ankor yoksa onay kapanıyor (1614–1615), ama bu ankor şerit etiketinden türüyor; dünya ankoru değil.
- İHA yaw'ı ≠ 0 iken çizilen rota dönük görünür (TAHMİN, ölçülmedi).
- Heartbeat'teki yaw ve x,y inset'te ayrıca gösteriliyor; rotaya bağlanmıyor.

## 4. Mozaik yolu (`simulation/scripts/iha_haritala.py`, K3 mozaik 6/15)

**Dünyaya bağlanışı:**
1. Poz logu `poses.csv` (n,t,x,y,z,yaw) sim plugin'inden geliyor (96–117).
2. Her kare yaw'a göre kuzey-yukarı döndürülüp İHA'nın dünya konumuna yapıştırılıyor (`mozaik_kur` 119–197). Yalnız z≈30 m ve yaw≈±90° kareleri alınıyor (150–152).
3. `rota_bul` → `piksel_to_dunya` 200–207: `dünya = HTAB merkezi + (px − MOZ/2)·MPP`.
4. `rota.json` şunları yazıyor: `referans_xy = rota[0]` (dünya), `kb_xy`, `rota_dunya`, `rota_yerel` (412–431).
5. `iha_sender --rota-json` (78–89, 545) üzerinden `ref_xy` **dünya koordinatı** olarak gidiyor.
- Dayandığı bilgiler: sim meta'sından HTAB merkezi ve sim yer gerçeği pozları.

**Üretimde YOK:**
- `jetson_paket/kod/` altında `iha_haritala` ve `iha_perceive` yok.
- `scripts/saha_kuru_kosu.py:683–685`: "sahada Gazebo haritalayicisi zaten kosmaz"; §11.1/1 bu dosyayı sahip saymayı yasaklıyor.
- CONTRACTS §6.5 (1031–1048) üretim üreticisini `rpi_inference` + `KararYayinci` ve `ref [0,0]` olarak tanımlıyor.
- Mozaiğin ihtiyaç duyduğu kare↔poz eşlemesi ve yaw üretimde yok (§2). HTAB merkezinin dünya koordinatını sahada beyan etmenin de bir yolu yok; `UB_REFERANS` yalnız İHA-UB köşesi ve yalnız heartbeat için.

## 5. Kusurların kesin yeri

| no | kusur | kod | sözleşme |
|---|---|---|---|
| a | Etiket kare-göreli; poz ya da HTAB girdisi yok | karar_sozlesmesi.py:42–54, 57–98; rpi_inference.py:1248, 1766 | CONTRACTS.md:588–592 |
| b | Ankor = kare alt bandı, KB değil; ilk nokta [0,0]; ref sabit [0,0] | rpi_inference.py:972–984; iha_sender.py:284–286, 298, 444; karar_sozlesmesi.py:160–162; ika_nav.py:191–203 | CONTRACTS.md:185–188, 1048 |
| c | Yerel eksen = görüntü ekseni; yaw ya da kerteriz dönmesi yok | iha_sender.py:285–286; ika_nav.py:203; rpi_inference.py:2376–2386 (`rota_ekseni_derece` yok) | CONTRACTS.md:188 ("Dönme yoktur") |
| d | Kare ↔ poz zaman eşlemesi yok | rpi_inference.py:2335–2371; protocol.py:82 | — |
| e | Sahadaki İKA konum çerçevesi tanımsız | ika_surucu.py:186–206 | CONTRACTS §7.2 yalnız arayüzü tanımlıyor |
| f | Sim iyimser: ref=KB ve kuzey döndürmesi dışarıdan veriliyor | gorev_kosumu.py (dal) 312–315; sim_karar_toplayici.py (dal) 179–184 | README_T214A §7 bunu kısmen anıyor |
| g | Belge kayması | CONTRACTS.md:188 (`:206` → 203), :682 (`:178-182` → 174–177); rpi_inference.py:1218 ↔ CONTRACTS.md:681–684 | — |

Özet: sahada rotayı dünyaya bağlayacak bilgilerden (KB, kare anındaki yaw, kamera montaj yönü, kare zaman damgası, İKA konum çerçevesi) hiçbiri bugün karara girmiyor. Yaw ve lat/lon okunuyor ama yalnız HEARTBEAT'e gidiyor.