# FILO1 TARAMA LANE 7/15 — T118 payda sozlesmesi
# Girdi: filo1_adaylar.json grup indeksi 7 (0-indeksli)
# Dosyalar: scripts/olcum/54_arena_cozunurluk.py · scripts/olcum/67_onnx_karar_denkligi.py
# Yontem: statik kod okumasi (54, 67, codes/rpi_inference.py:1475-1509, codes/karar_sozlesmesi.py:400-480). Kosum YOK — payda tayini kod izinden.
# Referans payda: ZEMIN_KAPLAMA_TAVANI=0.67 (codes/karar_sozlesmesi.py:423) `zemin_kaplamasi()` ile ICERIK kutusu paydasinda kalibre (karar_sozlesmesi.py:426-443, v24 kalibrasyon yorumu :405-417).

dosya:satir | PAYDA NE | ESIGE/KAPIYA KARSI KULLANIM | ESIK HANGI PAYDADA KALIBRE
--- | --- | --- | ---
scripts/olcum/54_arena_cozunurluk.py:109 | HAM GORUNTU (tam kare h*w; GT maskesi g.mean(), betik model.predict(im) ile ham goruntude calisir, ICERIK/letterbox yok) | HAYIR — tanisal print (yol alani %) | esik yok
scripts/olcum/54_arena_cozunurluk.py:133 | HAM GORUNTU (p.mean(); p=maske(r,h,w) ham goruntu boyutunda) | HAYIR — print sutunu, karar analyze_path serit secimidir, kaplama esigi uygulanmaz | esik yok
scripts/olcum/54_arena_cozunurluk.py:142 | kaplama-degil: moloza_basma_orani, payda GT MOLOZ MASKE TOPLAMI (mzt) | dosya icinde esik yok; JSON kaydi (S7, "asil olcut" BULGULAR_20260720.md 13d) — asagi akista kapi var mi BELIRSIZ | BELIRSIZ
scripts/olcum/54_arena_cozunurluk.py:143 | HAM GORUNTU (float(p.mean()) JSON "kaplama" alani) | dosya icinde ESIK YOK; ancak alan adi uretimdeki "kaplama" ile ayni, uretim tavani 0.67 ICERIK paydasinda — bu JSON'u 0.67'ye kiyaslayan olursa payda kaymasi olur (potansiyel, bu dosyada gerceklesmiyor) | 0.67 ICERIK paydasinda (karar_sozlesmesi.py:423); bu satirin sayisi HAM paydada — dogrudan kapi kullanimi yok, [UYUSMAZLIK] degil, RISK NOTU
scripts/olcum/54_arena_cozunurluk.py:144 | HAM GORUNTU (g.mean(), GT kaplamasi, betimleyici JSON alani) | HAYIR | esik yok
scripts/olcum/67_onnx_karar_denkligi.py:18 | kaplama-degil (docstring; "kaplama farki" baglam metrigi ilani) | HAYIR | esik yok
scripts/olcum/67_onnx_karar_denkligi.py:93 | kaplama-degil (liste tanimi) | HAYIR | esik yok
scripts/olcum/67_onnx_karar_denkligi.py:113 | LETTERBOX KARESI (t1,t2 = _maskeleri_icerige_kirp sonrasi trav; dizi kare tuval yan*yan boyutunda kalir — rpi_inference.py:1502-1509 dolguyu sifirlar ama KESMEZ; .mean() paydasi dolgu dahil kare) | HAYIR — kaplama_fark = onnx-pt farki, yalniz print+JSON; esige vurulmaz. Karar kapisi ayni fonksiyondaki analyze_path zinciridir ve o zincir ICERIK'i dogru gecirir (:54-56) | esik yok; NOT: bu satirdaki mutlak kaplama degerleri uretim ICERIK-payda kaplamasindan sistematik KUCUKTUR (carpan = icerik_alani/kare_alani), fakat FARK oldugu ve iki taraf ayni tuvalde olculdugu icin kiyas ic tutarlidir
scripts/olcum/67_onnx_karar_denkligi.py:149 | LETTERBOX KARESI (113'teki kaplama_fark'in print'i) | HAYIR — rapor satiri | esik yok
scripts/olcum/67_onnx_karar_denkligi.py:150 | LETTERBOX KARESI (ayni dizinin azami mutlak farki) | HAYIR — rapor satiri | esik yok

# UYUSMAZLIK OZETI: [UYUSMAZLIK] YOK — bu grupta hicbir kaplama degeri bir esige/kapiya karsi kullanilmiyor.
# Iki payda notu: (1) 54:143 JSON "kaplama" alani HAM paydada, uretim tavani 0.67 ICERIK paydasinda — ad cakismasi asagi akis riski.
# (2) 67:113 kaplama_fark LETTERBOX paydasinda — mutlak deger ICERIK paydasiyla kiyaslanamaz, fark olcumu olarak gecerli.
