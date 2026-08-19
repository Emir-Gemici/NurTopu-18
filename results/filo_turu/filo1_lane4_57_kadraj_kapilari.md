# FILO1 LANE 4/15 — scripts/olcum/57_t51_kadraj_kapilari.py (T118 payda sozlesmesi)
# Kosum: statik kod incelemesi (dosya okuma + karar_sozlesmesi.py esik izi), 2026-08-20.
# Kod CALISTIRILMADI; tum bulgular kaynak koddan.

dosya:satir | PAYDA NE | ESIGE KARSI KULLANIM | ESIK HANGI PAYDADA KALIBRE
57_t51_kadraj_kapilari.py:6 | kaplama-degil (docstring; KAPI 5 niyet beyani) | ZEMIN_KAPLAMA_TAVANI'na atif (tanim: codes/karar_sozlesmesi.py:423) | ICERIK kutusu, v24 uretim zinciri (T59, D-84/D-85; karar_sozlesmesi.py:355,383)
57_t51_kadraj_kapilari.py:23 | kaplama-degil (import satiri) | - | -
57_t51_kadraj_kapilari.py:63 | kaplama-degil (xs.mean() = serit merkezi x, oran degil) | - | -
57_t51_kadraj_kapilari.py:78 | kaplama-degil (sayac tanimi kaplama_reddi=0) | ZEMIN_MASKESI_SUPHELI_SEBEBI sayimi icin | (bkz. :98)
57_t51_kadraj_kapilari.py:81 | kaplama-degil (bos liste) | - | -
57_t51_kadraj_kapilari.py:82 | kaplama-degil (tablo basligi print) | - | -
57_t51_kadraj_kapilari.py:88 | ICERIK kutusu = TAM HAM KARE (icerik=(0,0,w,h), satir 87; letterbox YOK cunku _preprocess cagirilmiyor, maske YER GERCEGI poligonu) | dogrudan esikle kiyaslanmiyor; :89'da listeye, :135-137'de tavana KARSI raporlaniyor | ZEMIN_KAPLAMA_TAVANI=0.67 ICERIK kutusunda, v24 MODEL ciktisi + uretim zinciri (_preprocess+get_masks+kirp, conf=0.30) ile kalibre (karar_sozlesmesi.py:355-357, 383-396; T59/D-84/D-85)
57_t51_kadraj_kapilari.py:89 | :88'deki degerin listeye eklenmesi (ayni payda) | :135'te toplulastiriliyor | ayni
57_t51_kadraj_kapilari.py:98 | kaplama-degil (sayac artisi) | analyze_path icindeki zemin_maskesi_reddi(trav,icerik) ZEMIN_KAPLAMA_TAVANI'ni GT maskeye uyguluyor (karar_sozlesmesi.py:556,577); girdi maskesi YER GERCEGI, payda ICERIK=tam kare | esik ICERIK paydasinda ama v24 MODEL ciktisi uzerinde kalibre — burada GT maskeye uygulaniyor; script bunu bilerek yapiyor (KAPI 5 = "tavan bu kumede YANLIS ateslıyor mu" tanisi)
57_t51_kadraj_kapilari.py:135 | np.mean(kaplamalar) — :88 paydasi (ICERIK=tam kare, GT maske) | ZEMIN_KAPLAMA_TAVANI ile YAN YANA raporlaniyor (gecti/dustu karari yok, tanisal) | ICERIK kutusu, v24 model ciktisi (T59)
57_t51_kadraj_kapilari.py:136 | max(kaplamalar) + tavanin kendisi yazdiriliyor | ayni | ayni
57_t51_kadraj_kapilari.py:137 | kaplama-degil (tavan reddi sayaci raporu) | ayni | ayni

## DEGERLENDIRME
1. PAYDA UYUMU: Deger ICERIK kutusunda (icerik = tam ham sentetik kare, letterbox
   uygulanmadigi icin ICERIK == tam kare gecerli). Esik de ICERIK paydasinda
   kalibre. PAYDA UYUSMAZLIGI YOK.
2. KAYNAK FARKI (payda degil): esik v24 MODEL ciktisi uzerinde kalibre
   (karar_sozlesmesi.py:383), bu script YER GERCEGI maskesini ayni esikten
   geciriyor. Bu bilincli bir tani (KAPI 5, D-62 yan bulgusu): "GT bile tavani
   asiyorsa tavan yanlis ateslıyor" sorusu. Kalibrasyon tablosundaki GT satiri
   (karar_sozlesmesi.py:360: sentetik arena GT maks %39,0) bu kullanim icin
   emsal olusturuyor. UYUSMAZLIK sayilmadi.
