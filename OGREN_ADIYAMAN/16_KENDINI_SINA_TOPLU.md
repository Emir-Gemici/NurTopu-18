# 16 · KENDİNİ SINA — toplu final sınaması (karışık, 60 soru)

> Kapalı kitap, 60 dakika. Her soru için **tek cümle cevap + bir sayı ya da kanıt yolu**. Cevap anahtarı en altta. 45/60 altındaysan ilgili dosyaya dön.
> Bölüm kodu: (01) yarışma · (02) veri · (03) mimari · (04) rota · (05) sözleşme/kapı · (06) model · (07) haberleşme · (08) İKA · (09) saha · (10) Jetson · (11) süreç · (12) kusur · (13) FDR · (17) dürüst cevap.

## Bölüm 1 — Boşluk doldurma (20)
1. Yanlış güzergâh tespiti ____ puandır; tespit yapamamak yalnız ____ terimini kaybettirir. (01)
2. Serbest alan = ____ AND NOT ____; çıkarma ____ yapılır. (03)
3. `R_GEREKLI_M` = ____ + ____ + ____ = ____ m. (04)
4. Güven eşiği ____; kaplama tavanı ____ / kenar ____. (04)
5. Genel kapı ____ sahne; KOL 1 ____, KOL 2 ≥ ____. (05)
6. Üretim modeli ____ (mimari ____, imgsz ____); yedekler ____ ve ____. (06)
7. v36 gerçek kare kapısında ROTA ____ (eşik ≥ 10), MASKE_YOK ____ (eşik ≤ 10). (06)
8. İKA hareket kilidi: ____ ∧ ____ ∧ ____. (07)
9. İniş kanıtı: `landed_state` ____ + `relative_alt` < ____ m, ____ ardışık çift. (07)
10. Portlar: YKS ____, İKA ____, İHA komut ____, hub ____, MAVLink ____–____. (07)
11. Jetson kartı ____ ; FPS pt ____/____, engine ____/____; eşik ____. (10)
12. Engine denkliği D-303: ____/126 > ____/260 → uçuş ____ ile. (10)
13. ArduCopter sürümü ____; neden 4.7 değil: ____ parametre kırılıyor. (09)
14. Görev planı: TAKEOFF ____ m → 20×20 m tek pas → LOITER ____ s → LAND; bütçe ____ s ≤ 600. (09)
15. RC failsafe 6 Eylül'de ____ ; sebep: alıcı ____. (09)
16. Kusur defterinde ____ kayıt; en pahalı kusur ____ (D-____). (12)
17. FDR 45 yükümlülük: ____ KANITLI_TEST (%____), ____ ÖLÇÜLEMEDİ, ____ İNSAN-DONANIM. (13)
18. FDA = FDR × ____ + uçuş × ____. (01)
19. Test süiti 9 Eylül Jetson'da ____ test, ____ ortam kırmızısı. (10)
20. Dürüst cevabın dört adımı: ne ____, ne ____, ne ____, ne ____. (17)

## Bölüm 2 — Doğru/yanlış, gerekçeyle (15)
21. Sentetik kabul kapıları saha başarımını kanıtlar. (05)
22. mAP model seçiminde birincil ölçüttür. (03)
23. NO_ROUTE İKA'daki son geçerli rotayı ezer. (07)
24. YKS'deki "İHA İNDİ" düğmesi İKA kilidini açar. (07)
25. Kamera köprüsü venv'de koşar. (10)
26. `road` İKA'nın sürüş girdisidir. (04)
27. K7 kabul kümesinin tamamında ölçülür. (05)
28. Ultralytics'te `seed` değiştirmek farklı model üretir. (06)
29. Jetson'da süit kırmızıları kod hatasıdır. (10)
30. `FS_GCS_ENABLE` SiK kopunca RTL tetikler. (09)
31. v37 kabul zincirini geçti ve üretime alındı. (06)
32. Mimar üretim kodu yazabilir. (11)
33. FDR'ye takım üyelerinin adı yazılır. (13)
34. `EXTENDED_SYS_STATE` ArduCopter'da kendiliğinden akar. (07)
35. Şartname 433 MHz'i zorunlu kılar. (01)

## Bölüm 3 — Kısa açıklama (15)
36. "vb." kelimesi mimari kararı nasıl belirledi? (03)
37. Üç koordinat çerçevesi ve tek kural. (04)
38. Ön kayıt nedir; işe yaradığı bir olay. (05)
39. D-99 nedir? (12)
40. Neden `analyze_path` üretim, `rota_bul` tanısal? (04)
41. `ref_tip` neyi çözer? (07)
42. Saat kilidi D-422 kusuru ve çözümü. (07)
43. Seri port neden çoğullanır? (10)
44. Motor künyesi olayı ve açık kapı. (09)
45. Kol reçete farkı neden risk? (13)
46. "Kutusu açılmamış donanım" örüntüsü ve kuralı. (12)
47. Korelasyonlu kör nokta nedir? (11)
48. K2 (D-431) neden hâlâ açık? (10)
49. 51 saniyelik kör aralık ne, neden hız sorunu değil? (06)
50. Kanıt kaydı yazılamazsa hangi düğmeler kilitlenir, neden? (07)

## Bölüm 4 — 30 saniyelik anlatım (10; sesli, süre tut)
51. Sistemi bir cümlede anlat. 52. Mimari kararı anlat. 53. Maskeden karara anlat. 54. Kalite güvencesini anlat. 55. Model seçimini anlat. 56. Haberleşme güvenliğini anlat.
57. Jetson durumunu anlat. 58. Saha günlerini anlat. 59. FDR'nin güçlü/zayıf yanlarını anlat. 60. "Sahada çalışıyor mu?" sorusuna cevap ver.

---

<details><summary>Cevap anahtarı</summary>

**1** 0; P_görev. **2** zemin; engel; en son. **3** 0,35 + 0,25 + 0,50 = 1,10. **4** 0,20; 0,55 / 0,40. **5** 15; 15/15; 14/15 (rota ve şerit). **6** navitas-seg-v36-512; YOLOv8m-seg; 512; v35, v34. **7** 8; 16. **8** OPEN_ROUTE ∧ IHA_LANDED ∧ IKA_GO. **9** ON_GROUND; 1,0; 3. **10** 5005, 5006, 5007, 5100, 14550–14552. **11** Orin Nano DevKit 4 GB; 1,35/1,06; 1,58/1,33; 0,61. **12** 3; 5; `.pt`. **13** 4.5.7; 9. **14** 32; 60; 221,5. **15** DÜŞTÜ; son değerleri tutuyor (iBUS). **16** 441 (435 benzersiz); kamera aynalama; 349. **17** 32 (%71,1); 2; 7. **18** 0,85; 0,15. **19** 2204; 32. **20** ölçtük, ölçmedik, yaptık, zaman.

**21** Y — registry'nin kendi cümlesi: "K0..K6 saha başarımı iddia etmez". **22** Y — reddedildi; arena sıralamasını tersine çevirir. **23** Y — `last_no_route`'a yazılır, latest kalır. **24** Y — yalnız Pixhawk kanıtı açar. **25** Y — sistem Python'unda (GStreamer'lı OpenCV). **26** Y — sürüş waypoints + ref_xy ile; road yayınlanan etiket. **27** Y — dondurulmuş 88 iyi koşullu karede (%54'ü belirsiz). **28** Y — sabit tohum, v31 = v30 bit-bit. **29** Y — ortam (Windows yolları, PC kümesi, git yok, Py3.12). **30** Y — Jetson MAVProxy heartbeat bastığı için tetiklenmez; "Jetson-bağlantı failsafe'i". **31** Y — geçti ama figürde çöktü, geri alındı, K8 doğdu. **32** Y — madde 7; istisna 20 Ağu kapandı. **33** Y — yönerge 2.1 isim yasağı, rol bazlı. **34** Y — SET_MESSAGE_INTERVAL ile istenir, reboot'ta silinir. **35** Y — şartnamede frekans yok.

**36** Engel listesi açık küme → nesne tespiti bilinmeyeni geçilebilir sayar → serbest alan otoritesi (bilinmeyen engel). **37** Kaynak / tuval / içerik; her oran içeriğe göre. **38** Eşik sonuç görülmeden yazılır, gevşetilmez; 640 denemesi umut verici ara sayıya rağmen RED (D-377). **39** Şartname arena figürünün YZ ürünü olduğunun bulunması; beş kaydın alanı daraltıldı, silinmedi. **40** Saha `run_camera` → `analyze_path`; `rota_bul` yalnız kamera_dogrula/jetson_fps/kuru koşuda; genel kapı iki kol. **41** seq düğüm başına; farklı tipteki aynı seq'li ACK'in çapraz kabulünü önler. **42** Sapma tavanı ofset örneğini eliyordu → kalıcı red; NTP min-filtresi ile ofset öğrenme, adım algılama. **43** Seri port tek sahipli; üç süreç ister; MAVProxy/hub UDP'ye çoğaltır. **44** 5008 iade, X2220 980KV beyan, 38,4 A sınırda, tartı/akım yok → itki bütçesi kapısı ÖLÇÜLEMEDİ, T211 insan. **45** Kol 1–2 ve 3–4 farklı reçete, gerekçe yok → SGGS "gerekliliği ispatlanmamış değişiklik" diskalifiye. **46** microSD, PX4, künye, Orin Nano (motor); "beyan ≠ ölçüm", ilk komut künyeyi ölçer. **47** Aynı modelin iki örneği aynı kör noktaları taşır; birbirini onaylaması zayıf kanıt; hakem ölçüm. **48** T66 kabul kümesi PC'de, Jetson'a taşınmadı; engine kararı onunla verilecek. **49** Gerçek uçuşta 51 kare (46'sı MASKE_YOK) model karar üretemedi; daha hızlı örneklemek aynı köre daha çok bakmaktır; heartbeat karar_yas taşır. **50** FIRLATMA ve ONAY; ARM/DISARM/RTL/LAND açık kalır — aracı indirebilmek emniyettir.

**51–60** İlgili dosyaların "Jüriye 30 saniyede" kutuları; 60 için 17 §3.
</details>
