# ANALİZ C — T214-A üretim hattının sim kanıtı (SENTETİK, salt okuma)

Kaynak `worktree-wf_2c28e623-233-7` çalışma ağacı, dosyalar doğrudan okundu. Koşumdan önce ve sonra `git status` aynı çıktı: yalnız zaten var olan iki untracked `FDR/pdf` dosyası. GPU kullanılmadı, sürüş benzetimi koşulmadı. Hesabın tamamı JSON ve arena geometrisinden.

## (1) Etiket uyuşmazlığı: 5 vakanın 5'i kare merkezinin HTAB'dan kaymasından

- **Etiket kareye göre okunuyor.** Etiket, rota piksellerinin kare genişliğinin hangi üçte birinde çoğunlukta olduğundan okunuyor (`codes/karar_sozlesmesi.py:42-54`, `:57-98`). Tarama bacakları x = −18/−6/+6/+18 m'de (`simulation/mujoco/iha_ucus.py:80`), yollar ise x ≈ −16/0/+16'da (`simulation/scripts/arena.py:36`). Kare 45,61 m genişliğinde, yani üçte biri 15,2 m.
- **Yeniden üretim.** Her karede `rota_dunya` noktalarını piksele çevirdim (`sim_karar_toplayici.dunya_piksel`) ve üretim fonksiyonuna (`rota_serit_karari`) verdim. Yayınlanan etiket 8/8 kez aynen çıktı. Geri dönüş hatası 0,000 m.
- **Yaw katkısı sıfır.** Sekiz karenin hepsinde artık açı 0,0°. Pozlarda yaw tam ±1,570796 (`poses.csv`) ve kerteriz döndürmesi bunu tam hizalıyor (`sim_karar_toplayici.py:113-119`, `:179-185`).
- **Kamera eğimi yok.** Kamera montajında dönme özniteliği yok (`simulation/mujoco/araclar.py:170`), tarama bacağında yatış 0 (README_T214A §7).

| harita | kare | kare merkezi x | üçte-bir sınırları (dünya x) | rota x medyanı [aralık] | yayınlanan (yeniden üretilen) | dünya yolu | HTAB'a ortalanmış kare | neden |
|---|---|---|---|---|---|---|---|---|
| 1_kolay | k9 | −18 | −40,8 / −25,6 / −10,4 / 4,8 | −16,3 [−17,6; −13,3] | 2 (2) | 1 | 1 | kayma |
| 1_kolay | k15 | −6 | −28,8 / −13,6 / 1,6 / 16,8 | −16,4 | 1 (1) | 1 | 1 | eşleşiyor |
| 2_kolay | k9 | −18 | aynı | −15,7 [−16,7; −9,6] | 2 (2) | 1 | 1 | kayma |
| 2_orta | k15 | −6 | aynı | −14,4 | 1 (1) | 1 | 1 | eşleşiyor |
| 4_zor | k9 | −18 | aynı | −14,5 [−17,2; −11,2] | 2 (2) | 1 | 1 | kayma |
| 5_zor | k9 | −18 | aynı | −3,6 [−11,0; 4,3] | 3 (3) | 2 | 2 | kayma |
| 5_zor | k15 | −6 | aynı | −3,3 | 2 (2) | 2 | 2 | eşleşiyor |
| 5_zor | k20 | +6 | −16,8 / −1,6 / 13,6 / 28,8 | −3,5 [−10,8; 3,8] | 1 (1) | 2 | 2 | kayma + kıvrım |

- **x = −18 kareleri.** 18 m'lik kayma 1,18 üçte-bir eder. Bu yüzden yol 1 üçte-bir 2'ye, yol 2 üçte-bir 3'e düşüyor. Bu 15 haritanın hepsinde 45/45 geçerli (algı mükemmel sayılarak yapılan geometri sayımı).
- **5_zor k20.** Kayma yalnız 0,39 üçte-bir. Ama yol 2 bu y aralığında x ≈ −3,5'e kıvrılıyor ve sınırın (−1,6) 1,9 m soluna düşüyor.
- **Görünürlük neden değil, ama durumu ağırlaştırıyor.** x = −18 karelerinde yol 3'ün yalnız %20–21'i görünüyor, o da yolların birleştiği uçlarda (y 16,4–21,0). Yani üçte birler zaten ancak iki yolu kapsıyor.
- **Bacak başına genelleme (74,5°).** Kareye göre üçte-bir dünya yoluna şu oranlarda eşit: x = −6'da 172/180, +6'da 163/180, −18'de 30/120, +18'de 46/166. Toplam 411/646.
- **Kosum_tur3 üretim koşumları.** 20 OPEN_ROUTE karesi var; yayınlanan etiket dünya yoluyla 6/20 eşleşiyor. 14 uyuşmazlığın 14'ü de kayma (11'i x = −18, 3'ü x = +6). HTAB'a ortalanmış kare etiketi 20/20 doğru.
- **Ham besleme.** Tek OPEN_ROUTE karesi 4_zor k19. Rota yalnız 1,7 m (HB yanında), dünya yolları arası ayrım 1,27 m. Bu beslemede görüntünün x ekseni gövde ileri yönü, yani üçte birler yolun boyunca bölüyor. Tek bir vaka ve zayıf kanıt.

## (2) Rota başlangıcı ile KB arasındaki kayma: dağılım ve neden

Ölçülen `ankor_kb_uzakligi_m`:
- **Sürülen 12 koşumdaki son OPEN_ROUTE karesi:** en az 6,9 · medyan 17,84 · ortalama 15,35 · en çok 20,19 m. README_T214A.md:161 ile aynı.
- **20 OPEN_ROUTE karesinin tamamı:** 6,18 / 15,72 / 13,16 / 20,19 m.

Kayma iki bileşene ayrılıyor:
- **Dikey bileşen (Δy), medyan 6,53 m (6,1–9,15):**
  - KB, kare alt kenarının 2,89–5,51 m altında kalıyor.
  - Rota alt kenardan 3,0–3,64 m yukarıda başlıyor. Bu, alt tohum bandının yüksekliği: `HEDEF_BANT_ORANI` 0,08 × 45,6 m = 3,65 m (`karar_sozlesmesi.py:13`, `:287`; `rpi_inference.py:972-984`).
- **Yatay bileşen (Δx), medyan −14,3 m (−18,31 ile +1,3 arası):**
  - Rota başlangıcı açık yolun üzerinde: merkez hattına uzaklığı medyan −0,41 m (−1,93 ile +1,9 arası).
  - Kaymayı yolun kendisi yaratıyor: başlangıç yüksekliğinde açık yol KB'den medyan −13,19 m ayrışmış.
  - Yol 1 KB'den hızla batıya ayrılıyor (`arena.py` `harita`: ikinci kontrol noktası y = −19,5'te yol eksenine doğru %45 kayıyor). Bu yüzden 1/2/4 haritalarında kayma 15–20 m.
  - Yol 2 KB'den yalnız ~1 m ayrışıyor. Bu yüzden 5_zor'da kayma 6,2–9,2 m.
- **İrtifa ve eğim değişken değil.** 20 karenin hepsinde z = 30,0 ve eğim 0. Belirleyen, kare izi (irtifa × FOV) ile bant oranı.
- **Geometri modeli ölçümü açıklıyor.** Model: "başlangıç = açık yol merkez hattı ∩ (alt kenar + bant)". Ölçümden mutlak farkı medyan 0,23 m, en çok 1,83 m (n = 20).
- **KB ile HB neden hiç aynı karede değil.** KB–HB arası Dy = 44,0 m, kare 45,61 m. İkisinin birden karede olması için kare merkezi y'si [−1,81; −0,19] aralığında olmalı; bu 1,6 m'lik bir pencere. Tarama kareleri 1 Hz'de, bacak boyunca 10–14 m arayla alınıyor; en yakın y'ler −2,3 ve 2,7. En iyi kare bile her haritada 0,49–2,87 m ıskalıyor. Yani 0/225 algı değil geometri sonucu. 74,5°'de gereken irtifa 28,9 m; sim'in 30 m'si sınırın yalnız 1,1 m üstünde.

## (3) Karşı-olgu (HESAP, ölçüm değil)

**Etiket dünya çerçevesinde verilseydi:**
- Kare düzeyinde: `rota_dunya_yolu`, HTAB'a ortalanmış kare üçte-biri ve HTAB 50 m üçte-biri, üçü de **8/8** eşleşir. Üçünde de 8/8 açık yol.
- Harita düzeyinde, ön kayıtlı kuralla: **1/15 → 5/15**. K3 eşiği ≥ 12/15 olduğu için **yine düşer**. Kalan 10 haritada hiç OPEN_ROUTE yok (NO_ROUTE'ta `UC_BANT_TEMAS_YOK` baskın, README:81). Yani etiket düzeltmesi tek başına K3'ü geçirmez.

**Sürüş geometrisi:** yalnız statik engel kutusu (OBB) açıklığına bakıldı. Engel yerleşimi `arena_mjcf.yerlesim(H, lv, tohum, "field")`, İKA yarı genişliği 0,22 m (koşum JSON'u). Üç seçenek:
- **A — saf öteleme (mevcut hal):** rota = KB + yerel (`ika_nav.py:203`, `gorev_kosumu.py:311-315`). Yerel waypoint'ler dünya rotasının ötelenmiş hali; son noktada fark ≤ 0,014 m.
- **B — bağlantı bacağı:** KB'den rotanın ilk noktasına düz bir bacak, ardından dünya rotası.
- **C — dünya waypoint'leri:** geometrisi B ile aynı.

| koşum | kayma (m) | ölçülen temas / varış (m) | A: temas? · açık yol hattına maks (m) · son→HB (m) | B: engel açıklığı (m) · açık yol hattına maks (m) · son→HB (m) · HB 2×2 içinde |
|---|---|---|---|---|
| 1_kolay_42 | 18,11 | 5024 / 38,5 | evet · 17,70 · 17,68 | 2,66 · 1,35 · 1,37 · hayır |
| 1_kolay_43 | 17,87 | 7179 / 38,5 | evet · 17,34 · 17,47 | 2,68 · 1,53 · 1,37 · hayır |
| 1_kolay_44 | 15,82 | 7462 / 38,5 | evet · 15,63 · 15,41 | 2,71 · 1,01 · 1,26 · evet |
| 2_kolay_42 | 18,46 | 7 / 39,8 | evet · 18,69 · 18,39 | 2,47 · 1,23 · 0,86 · evet |
| 2_kolay_43 | 18,39 | 10 / 39,8 | evet · 18,47 · 18,43 | 2,55 · 1,32 · 0,93 · evet |
| 2_kolay_44 | 18,32 | 10 / 39,8 | evet · 18,37 · 17,75 | 2,33 · 1,39 · 1,32 · evet |
| 2_orta_42 | 20,19 | 12839 / 35,7 | evet · 19,74 · 19,74 | 1,64 · 2,35 · 1,08 · evet |
| 4_zor_42 | 17,80 | 3 / 40,6 | evet · 17,99 · 17,99 | 1,69 · 1,92 · 0,89 · evet |
| 4_zor_44 | 17,63 | 11 / 40,0 | evet · 17,35 · 17,34 | 1,67 · 1,66 · 1,12 · evet |
| 5_zor_42 | 6,90 | 74 / 31,4 | evet · 6,66 · 7,56 | 2,08 · 1,42 · 0,96 · evet |
| 5_zor_43 | 7,38 | 7607 / 31,7 | evet · 6,89 · 7,98 | 2,11 · 1,51 · 0,79 · evet |
| 5_zor_44 | 7,38 | 2704 / 40,2 | evet · 6,89 · 7,98 | 1,96 · 1,72 · 0,79 · evet |

- **A (mevcut):** geometri 12/12 temas öngörüyor, ölçüm de 12/12 temas. Model ölçümle tutarlı. Ötelenmiş rota 12/12 kapalı yol 2'nin üzerine düşüyor. Rota sonu 12'nin hiçbirinde HB 2×2 içinde değil.
- **B:** 12/12 koşumda engel açıklığı İKA yarı genişliğini (0,22 m) aşıyor, temas öngörüsü 0/12. En küçük açıklık 1,64 m, `R_GEREKLI` 1,10 m'nin de üstünde. Bacak uzunluğu kaymaya eşit (6,9–20,2 m); bacağın açık yol hattından en büyük sapması 0,56–1,65 m. Rota sonu 10/12 HB 2×2 içinde. Kalan ikisi (1_kolay_42/43, 1,37 m) algının HB konum hatası; bacakla ilgisi yok.
- **Uyarı:** B ile C'nin ikisi de KB→rota başlangıcı vektörünü ortak bir çerçevede bilmeyi gerektiriyor. KB hiçbir karede yok (0/225); bu yüzden kare pozu ve KB koordinatı, yani bir dünya çerçevesi şart. CONTRACTS.md:1048 ise "sahada dünya çerçevesi yoktur" diyor. Bu mimari bir karar. Dinamik, takip hatası ve arazi zemini hesaba katılmadı.

## (4) Sim FOV'u 74,5° ile gerçek ~55° arasındaki fark

Sim: `HFOV_RAD` = 1,3 → 74,48° (`arena_mjcf.py:79`), kare kare biçimli → 30 m'de 45,61 m iz. Gerçek kamera (**TAHMİN**, ölçülmedi): IMX477 (6,287 × 4,712 mm) + 6 mm lens → 55,3° × 42,9°, 30 m'de 31,4 × 23,6 m iz. Üç etkinin üçü de **kötüleşme** yönünde; yani sim iyimser.

- **KB ile HB'nin aynı karede olması:** gereken irtifa 28,9 m'den 42,0 m'ye (uzun kenar yol boyunca) ya da 56,0 m'ye (kısa kenar yol boyunca) çıkar. 30 m'de imkânsız.
- **Rota başlangıcı–KB kayması** (aynı kare merkezleri, geometri modeli): sürülen 12 son OPEN_ROUTE karesinde medyan 17,57 m'den 20,33 m'ye çıkar; 11/12'de büyür (20 karenin 19'unda). 5_zor'da 6,7–9,2 m'den 12,5–15,1 m'ye çıkar. Tek istisna 2_orta k15 (22,02 → 20,93), yol geometrisinden.
- **Kareye göre etiket:** görünen yol-kare çiftlerinde doğru oran 411/646'dan (%63,6) 276/556'ya (%49,6) düşer. 31,4 m'lik kareye 16 m arayla dizili üç yol sığmaz. 55°'de ±6 bacakları da bozulur: x = +6'da yol 2 → üçte-bir 1 (47/60), x = −6'da yol 2 → üçte-bir 3 (39/60).
- **K3'ün 8 karesi:** aynı rotanın algılandığı varsayımıyla (**TAHMİN**), kırpılmış rotanın etiketi 8/8 aynı kalır, uyuşma 3/8'de sabit. 5_zor k9'da rotanın yalnız %35'i 55° karede kalır.
- **Dünya çerçevesinde etiket** FOV'dan bağımsızdır, ama rotanın görünürlüğü düşer.
- **Ölçülmedi:** algı kalitesi. Piksel boyu 0,0356'dan 0,0246 m/px'e iner; bunun algıya etkisinin yönü belirsiz.

## Dosyalar
Hepsi `C:\Users\yunus\AppData\Local\Temp\claude\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\rota_dunya\` altında. Aynı klasördeki diğer dosyalar bu analize ait değil.
- `analiz_c.py` — ana hesap
- `tablolar.py` — tablolar ve ek sayımlar
- `analiz_c_sonuc.json` — tüm ham sonuç
- `ek_sayimlar.json`
- `etiket_k3_8kare.csv`
- `etiket_uretim_20kare.csv`
- `ankor_uretim_20kare.csv`
- `surus_karsi_olgu_12.csv`
- `hfov_k3_8kare.csv`