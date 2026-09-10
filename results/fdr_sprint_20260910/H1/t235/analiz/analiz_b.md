# ANALİZ B: Şartname ve arena geometrisi, tek kare uygunluk hesabı

**Sonuç:**
- **KB–HB mesafesi hiçbir yerde tanımlı değil.** Şartname koordinat vermiyor, yol genişliği ve aralığı yazmıyor, "sol/orta/sağ" diye bir tanımı yok. Güzergâhları yalnız zorluğa göre adlandırıyor (Kolay/Orta/Zor).
- **Ana görev:** KB ile HB'yi tek karede görmek için HQ 6 mm ile ≥ ~59–66 m, köşegen durumda ~92 m irtifa gerekiyor. Bu irtifalarda ölçek 12–19 cm/px; modelin kanıtı olan ölçeğin 1,5–2,4 katı ve bu ölçekte hiç ölçülmedi.
- **Doğru irtifada bile garanti yok.** Üretim rotayı karenin alt %8 bandından başlatıyor. KB'nin o bantta olacağı pencere (≤ 6,3 m) kareler arası mesafeden (7,4–10 m) kısa.
- **FDA (30 Eylül):** 20×20 m alan 32 m'de, alanın merkezindeki bekleme noktasında tek kareye sığıyor. Tek koşul, kamera kipinin sensörü kırpmaması; bu henüz ölçülmedi.

Kaynak: `O:\navitas\results\sartname_bosluk\sartname_metin.txt`. Bu metin `Ileri_Otonom_Sistemler_..._Ltktw.pdf` (V2, 13.04.2026) dosyasından çıkarılmış; kendi çıkarımımla sayfa sayfa eş çıktı, yalnız sayfa işaretleri farklı. `2026_TEKNOFEST_TYDA_..._Ucuncu_Senaryo...pdf` başka bir yarışmaya ait ("YAPAY ZEKA DİL AJANLARI", sayfa 1), konu dışı.

## 1. Kaynaklı geometri tablosu (şartname satır numaraları)

| Öğe | Şartnamenin söylediği | Satır |
|---|---|---|
| HTAB | 50 × 50 m, içinde moloz ve engel | 239-241 |
| İHA-UB | 300 × 300 m; dışına çıkmak "Alan İhlali", uçuş başarısız | 249-251, 971-972, 1009-1010 |
| İKA-KB | 1 × 1 m; İKA'yı KB'ye takım yerleştirir (hazırlık süresinde) | 252-253, 940-942 |
| HB | 2 × 2 m, üzerinde kırmızı H, HTAB içinde | 254-256 |
| İHA-İB | 30 × 30 m mavi alan | 257-258 |
| Güzergâhlar | KB ile HB arasında 3 yol, 1'i açık, açık olan gizli | 259-270 |
| Yol sınıfı | "Kolay", "Orta", "Zor"; her birinin zorluk katsayısı var; her 2 günlük periyotta 1'i açık | 830-844 |
| Zorluk katsayısı | Senaryo 1/2/3 → 1,0 / 1,5 / 2,0 | 1042-1045 |
| Yol genişliği, aralığı, yönü | **Şartnamede yok.** "genişli", "sol", "sağ", "kuzey/güney" araması boş (`geometri_hesap_cikti.txt`) | — |
| KB–HB mesafesi | **Şartnamede yok.** İkisi de HTAB içindeyse üst sınır 70,7 m (köşegen, HESAP); KB'nin HTAB içinde olduğu metinden çıkarım (TAHMIN) | 254, 259 |
| Şekil 1 | Yapay zekâyla üretilmiş, "Gerçek alanı doğrudan yansıtmamaktadır" | 273-274 |
| Saha yerleşimi | Resmi kanaldan sonra duyurulacak | 821-822 |
| İHA irtifası | **Ana görevde alt/üst sınır yok.** Tek irtifa ifadesi FDA test uçuşunda "asgari 30 metre" | 733 |
| Koordinat / GPS | **Organizasyon vermiyor** ("koordinat", "GPS" araması boş). FDA planında HOME (0,0) yer tutucu, "Koordinatlar Adıyaman'da girilir" | `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:770`, `config/pixhawk/README.md:97` |
| Hakemin doğruladığı | Güzergâh YKS'ye canlı aktarılır, hakem monitörden izler ve **sözlü** onaylar; İKA'ya aktarımı da onaylar; aktarım İHA havadayken biter. Doğruluk teyit edilemezse uçuş geçersiz. **Mesaj biçimi tanımsız** | 297-303, 967-970, 1005-1008 |
| FDA test uçuşu | Çoklu rotor, 20×20 m alan, "Başlangıç Alanı" ile "Hedef Alanı" arası, ≥ 30 m, ≤ 10 dk; yanlış güzergâh 0 puan | 726-745 |
| İKA'nın hareketi | İHA inince, YKS'deki üye elle tetikler, İKA otonom izler; HB'ye girmek başarı sayılır, Pgörev ise brandaya temas ister; süre 600 s | 313-320, 327-328, 980, 1131-1142 |

**"Sol/orta/sağ" nereden geliyor:**
- Etiket tamamen projeye ait: `CONTRACTS.md:361`, `:586`; `simulation/scripts/arena.py:33` (`ROAD_LABEL`).
- Üretimde etiketi içerik genişliğinin üçte birlerine göre `karar_sozlesmesi.py:42-54` (`serit_no`) belirliyor, yani **kareye göreli**.
- Şartnamede ne dünyaya ne kareye göre bir tanım var.

**İKA'nın yönlendirilmesi (GPS):**
- DDR tasarımında İKA'da M8N GPS ve pusula RPi5 UART/I2C'ye bağlı (`FDR/sekiller/ika_baglanti_kaynaklar.md:36-37`). MPU6050 (`:41`) ve 2 enkoder (`:33`) de var. Hepsi "DDR tasarımı, tedarik yok"; İKA donanımı hiç alınmadı (`FDR/BOLUM_3...:417-418`).
- Rota sözleşmesi GPS kullanmıyor: `ref_xy` daima [0,0], "sahada dünya çerçevesi yoktur", İKA saf öteleme yapıyor (`CONTRACTS.md:187-188`, `:1048`).
- TAHMIN: İKA'yı takım yerleştirdiğine göre (940-942), karedeki "yukarı" yönü İKA'nın ilk burun yönüne elle hizalanmak zorunda.

## 2. HESAP: Tek kare uygunluğu

Betik ve çıktı: `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\geometri_hesap.py` ve `geometri_hesap_cikti.txt`.

**HQ 6 mm (6,287 × 4,712 mm):** yatay 55,30°, dikey 42,88°. Yer izi genişlik = 1,0478·h, yükseklik = 0,7853·h. (Simülasyon kamerası 74,485°, 30 m'de 45,61 m kare iz.)

**T214-A kare verisi (15 harita, dalın `k3_uretim_boru/kerteriz/*.json`):**
- KB–HB mesafesi 44,53–45,77 m (medyan 45,16).
- 225 tarama karesinin KB içereni 105, HB içereni 90, **ikisini birden içereni 0**. README ile aynı.
- Varsayımsal: aynı x/y/yaw izi HQ ile uçulsa, ikisini aynı karede görmek için gereken en düşük irtifa 46,4–50,9 m (medyan 50,0). Bu hesap her karede iki kamera yönünden iyi olanı alıyor.

**Analitik alt sınır** (en iyi hizalama; KB ±0,5 m, HB ±1,0 m pay):

| KB–HB (D) | Kısa eksen boyunca h ≥ (üretim ALT→ÜST, yatay montaj) | Uzun eksen boyunca h ≥ |
|---|---|---|
| sim 44,5–45,8 m | 58,6–60,2 m | 43,9–45,1 m |
| HTAB kenarı 50 m | 65,6 m | 49,1 m |
| HTAB köşegeni 70,7 m | 91,9 m | 68,9 m |
| FDA kenarı 20 m / köşegen 28,3 m | 27,4 / 37,9 m | 20,5 / 28,4 m |

**Üretimdeki ek kısıt:**
- Başlangıç tohumu içeriğin alt `HEDEF_BANT_ORANI = 0.08` bandında (`codes/rpi_inference.py:972-984`, `karar_sozlesmesi.py:13`). HB bulunursa hedef tohumu HB olur (`rpi_inference.py:1065-1068`).
- Rotanın KB'den başlaması için KB'nin alt bantta olması gerekiyor. Uçuş yönünde bunun sağlandığı pencere = min(0,08·V, V−D−1,5).
- D=45 için pencere: 60 m'de 0,6 m, 64 m'de 3,8 m, 80 m'de 5,0 m, 100 m'de 6,3 m.
- Kareler arası mesafe:
  - Simülasyon taraması 10 m/s ve 1 Hz'de 10 m (dalda `world_generator.py:48-49`).
  - Jetson'da `.pt` ile kare başına 770/922 ms ölçüldü (`FDR/BOLUM_3...:938`); bu ~1,1–1,3 FPS demek, 10 m/s'de ~7,7–9 m.
- Pencere her irtifada kareler arası mesafeden kısa, yani o kareyi yakalamak şansa kalıyor.
- Ayrıca `run_camera` eksen parametresi geçmiyor. `rota_ekseni_derece` 1480. satırdan sonra hiç geçmiyor, CLI argümanı da yok (`rpi_inference.py:1356-1370`'teki seçenek kullanılmıyor). Uçuş yönü KB→HB'ye hizalı değilse ALT→ÜST varsayımı bozuluyor.
- Ana İHA sabit kanat olmak zorunda, dikey kalkış yasak (805-807, 289-290); havada durup bekleyemiyor.

## 3. HESAP: Çözünürlük

| h (m) | İz (m) | GSD@512 cm/px | GSD@640 | İKA 0,70 m (px@512) | R_GEREKLI 1,10 m (px) | HB 2 m (px) |
|---|---|---|---|---|---|---|
| 30 | 31,4×23,6 | 6,14 | 4,91 | 11,4 | 17,9 | 32,6 |
| 32 | 33,5×25,1 | 6,55 | 5,24 | 10,7 | 16,8 | 30,5 |
| 50 | 52,4×39,3 | 10,23 | 8,19 | 6,8 | 10,7 | 19,5 |
| 60 | 62,9×47,1 | 12,28 | 9,82 | 5,7 | 9,0 | 16,3 |
| 70 | 73,3×55,0 | 14,33 | 11,46 | 4,9 | 7,7 | 14,0 |
| 90 | 94,3×70,7 | 18,42 | 14,74 | 3,8 | 6,0 | 10,9 |

**Modelin kanıtı olan ölçek:**
- Kabul kümesi manifesti 7,81 cm/px (`REVIEW_LOG.md:8291`, v27 dönemi).
- DJI saha verisinin medyanı 4,389 cm/px@960 (`results/dji_20260822/gsd_olcumu.json`); 512'ye çevrilince 8,23 cm/px (HESAP).
- Simülasyon 30 m'de 8,91 cm/px; ama bu ölçekte bile K3 1/15. Yani ölçek tek başına yetmiyor.

**Değerlendirme:**
- Tek kare için gereken 59–92 m, 12–19 cm/px veriyor. **v36'nın bu ölçekteki başarımı ÖLÇÜLMEDİ.**
- Piksel sayısı sınırda ama yeterli: 70 m'de İKA 4,9 px, R_GEREKLI 7,7 px.
- K-B çözünürlük koruyucusu mpp > 1,10/(0,20·0,035·w) ise devreye giriyor (`REVIEW_LOG.md:3353-3360`). w=512 için 0,307 m/px, bu da ≈150 m'ye kadar tetiklenmiyor.
- HB alan tabanı `HB_ASGARI_ALAN_ORANI` (`karar_sozlesmesi.py:1156`) ≈111 m'de aşılıyor (TAHMIN: HB maskesi tam 2×2 m dolarsa).

## 4. FDA (30 Eylül, tek gerçek test)

- **Plan:** 32 m'ye kalkış, 4 köşe, HOME'da 60 s bekleme (`config/pixhawk/fda_gorev.waypoints` satır 1-6). HOME alan merkezine konursa (TAHMIN; koordinatı kaptan girer) beklemedeki kare 33,5×25,1 m olur.
- **Sığma payı (HESAP):** eksene hizalı 20×20 alan sığıyor, pay kısa eksende 2,57 m, uzun eksende 6,77 m. 45° dönükse köşegen 28,3 m > 25,1 m, **sığmıyor**. Ölçek 6,55 cm/px, kanıt bandına yakın.
- **Kamera kipi riski:**
  - Köprü varsayılanı 1280×720 (16:9) (`scripts/kamera_koprusu.py:84-85`). Kip "Cumartesi ölçülür" notuyla bırakılmış (`:81`).
  - CSI kamera hiç bağlanmadı (`FDR/BOLUM_3...:868`). Yatay FOV ölçümü 12 Eylül'e planlı (`ATOLYE_TEST_GUNU_20260912.md:136-147`).
  - Kip sensörü dikeyde kırpıyorsa (TAHMIN; 3840×2160 ya da tam genişlikte 16:9 kırpma), 32 m'de dikey iz 17,9–18,9 m olur. Bu durumda **20 m'lik alan tek kareye sığmaz**; h ≥ 36,5–38,5 m gerekir.
- FDA'da İKA yok (`CONTRACTS.md:440-444`). Bu yüzden risk (b), yani İKA'nın KB'ye oturtulması, orada geçerli değil. Kareye göreli etiket riski (a) ise sürüyor.
- **Waypoint ofseti (TAHMIN):** köşeler enlem ve boylamda aynı ±0,0000898315° ofseti kullanıyor, bu ekvatorda ±10 m. Kaptan köşeleri gerçek değerlerle girmez de yalnız kaydırırsa, 37,8° enleminde boylam ofseti 7,9 m'ye düşer ve alan 20×15,8 m olur.

## 5. Kanıtlı tutarsızlıklar

1. **FDR hangi alanın modellendiğini yanlış yazıyor.** `FDR/BOLUM_3...:32` "sentetik arenamız bu 20 × 20 m alanı modeller" diyor. Oysa `simulation/scripts/arena.py:27` HTAB=50 ve `:44-45` KB_Y=-23 / HB_Y=21 tanımlıyor; ölçülen KB–HB 44,5–45,8 m. FDR'nin kendi `:1277` satırı da "HTAB 50×50 m" diyor.
2. **Simülasyondaki "şartname" yorumlarının kaynağı yok.** Dalda `world_generator.py:46-50`: "Şartname seyir 40-45 m/s", "20-30 s tarama", "şartname: 30 m tarama irtifası". Şartnamede "m/s" ve "40-45" hiç geçmiyor. "tarama" yalnız 847. satırda ("engelleri taraması"), "irtifa" yalnız 733'te (FDA). Yani ana görevin 30 m tarama irtifası şartnameden gelmiyor; `OGREN_ADIYAMAN/ozet/H_sartname.md:83` de "irtifa sınırı PDF'de bulunamadı" diyor.
3. **İrtifa tavanını proje koymuş.** `FENCE_ENABLE=1 (irtifa 50 m)` (`FDR/BOLUM_3...:789`). Bu tavanla, KB–HB kısa eksen boyunca hizalı ana görev geometrisinde (≥ 58,6 m) KB ve HB tek kareye giremiyor.