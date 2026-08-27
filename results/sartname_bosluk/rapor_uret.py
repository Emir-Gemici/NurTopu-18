# -*- coding: utf-8 -*-
"""Sartname uyum bosluk denetimi — rapor.md + rapor.json ureteci (salt okuma denetimi)."""
import json
from pathlib import Path

KOK = Path(__file__).resolve().parent
TARIH = "2026-08-26"

SATIRLAR = [
 {
  "no": 1, "madde": "§2.2.2",
  "gereksinim": "İHA, üzerindeki algılayıcılar ve görüntü işleme algoritmaları vasıtasıyla HTAB içerisindeki açık olan güzergâhı tespit edecektir.",
  "kod": ["codes/rpi_inference.py:1080 analyze_path", "codes/costmap_path_finder.py:951 rota_bul", "codes/costmap_path_finder.py:366 koridor_adaylari"],
  "test": ["codes/test_rota_sentetik.py → 15/15 (bu koşu)", "tests/test_t119_yayinlanan_road_kapisi.py (4)", "tests/test_koridor_etiketi.py (13)"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "Kanıt SENTETİK arenadır. Gerçek arena karesi tek (sartname_s9_arena.png, CONTRACTS §6.4 T59). Saha kuru koşusu 2026-08-26 00:14 `rota` halkası DÜŞTÜ: durum=BELIRSIZ_TEK_KAPI (results/saha_kuru_kosu_20260826_001414/ozet.json).",
  "is": "Gerçek arena/DJI karelerinde (T136 hattı) açık güzergâh isabetini ölçüp raporla; tek kapı belirsizliğinin gerçek karede sıklığı."
 },
 {
  "no": 2, "madde": "§2.1 / §6",
  "gereksinim": "Üç yoldan yalnızca bir tanesi açık bırakılacak, diğer iki yol fiziki engellerle kapatılacaktır. (3 güzergâhtan açık olanın seçimi)",
  "kod": ["codes/costmap_path_finder.py:366-505 koridor_adaylari (kapı bandında ayrık geçitler; her aday için yalnız o kapı açıkken başlangıç↔hedef bağlantısı)", "codes/karar_sozlesmesi.py:42 serit_no (tek etiket kaynağı)", "codes/rpi_inference.py:1255 road = olcum['darbogaz_serit']"],
  "test": ["tests/test_koridor_etiketi.py (13)", "tests/test_koridor_genisligi.py", "tests/test_koridor_kararliligi.py"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "İki karar yolu var: saha üretim yolu `analyze_path` (uç-bant + A*), Gazebo yolu `rota_bul`+`koridor_adaylari`. `koridor_adaylari` yalnız `rota_bul`dan çağrılır (costmap_path_finder.py:1025); `rpi_inference.analyze_path` onu ÇAĞIRMAZ — saha yolunda 3-koridor kapı mantığı yok, şerit etiketi darboğaz şeridinden türer (CONTRACTS §6.2, 'daha iyi olduğu gösterilmemiştir'). Kararsızlık gerçek ölçüm: %3,46 (D-122).",
  "is": "Saha yolunda (analyze_path) seçilen koridorun 3 fiziksel güzergâhtan hangisi olduğunu yer gerçekli gerçek karede ölçmek; koridor_adaylari'nın saha yoluna bağlanıp bağlanmayacağına mimar kararı."
 },
 {
  "no": 3, "madde": "§5.3.2 / §6.2",
  "gereksinim": "Yanlış güzergah tespiti yapan takımlar 0 puan alarak görevden başarısız sayılacaktır. Hakem onayı alınmayan tespitler geçersiz sayılır.",
  "kod": ["codes/karar_sozlesmesi.py:76-88 ret sebepleri; :224 rota_guven_reddi (bool/NaN/aralık dışı fail-closed)", "codes/rpi_inference.py:1127 _don / :1362 _rota_kararini_esikle", "comms/iha_sender.py:131-137 send_open_route son savunma (eşik altı → NO_ROUTE)", "comms/yks_gui.py:813-816 eşik altı OPEN_ROUTE onaya açılmaz, ACK üretilmez", "simulation/scripts/ika_nav.py:226-252 receiver_rota_gecerli (NO_ROUTE → sürmez)"],
  "test": ["tests/test_rota_ret_nedenleri.py (10)", "tests/test_rota_guven_esigi.py", "tests/test_t141_rota_yoksa_surme.py (7) → '[KAPI T141] rota kapisi KAPALI · komut=5 · sifir-olmayan=0'", "tests/test_t120_sahte_kapi_yasagi.py"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "Fail-closed her katmanda var. Ama çekimserlik de 0 puandır; K-B ölçekli kipte hiç ateşlemez (CONTRACTS §6.3 T43) — seçici kapı yalnız K-A + KORIDOR_DEGIL + ZEMIN_MASKESI_SUPHELI.",
  "is": "Yok (kod). Saha günü: NO_ROUTE sebebi hakem günlüğüne düşüyor; operatör kontrol listesinde 'rota yoksa İKA sürülmez' (T141) var."
 },
 {
  "no": 4, "madde": "§2.2.3",
  "gereksinim": "İHA, tespit ettiği güzergâh bilgisini kablosuz haberleşme sistemleri üzerinden yerdeki yer istasyonuna ve İKA'ya aktaracaktır.",
  "kod": ["comms/protocol.py:33 open_route / :67 rota_yok", "comms/iha_sender.py:93-121 _tekrarli_gonder (repeat=8 × interval=0,25 s = 2 s ACK penceresi)", "ÜRETİCİ: simulation/scripts/iha_detect_send.py:132-137 (girdi: iha_haritala rota.json = Gazebo mozaik)"],
  "test": ["comms/test_comms.py", "tests/test_iha_sender_cli.py", "tests/test_jetson_comms_paketi.py (paket API'yi taşıyor)"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "KRİTİK",
  "not": "GREP KANITI: `codes/` altında IhaSender/send_open_route çağrısı YOK (grep -rn 'IhaSender|send_open_route' codes → 0). `rpi_inference.run_camera` (:1735) kararı ekrana basar, hiçbir mesaj göndermez; `run_image` payload'ı yalnız print eder (:1626). Sahada rota üreten yol (rpi_inference/analyze_path) ile telsize yazan yol (iha_sender) BİRBİRİNE BAĞLI DEĞİL. Saha kuru koşu `aktarim=GECTI` yalnız 'paket iha_sender.py taşıyor' ölçüyor (ozet.json sebep alanı), uçtan uca değil. `iha_detect_send.py` tek atış: bir OPEN_ROUTE gönderir, 2 s ACK bekler, çıkar.",
  "is": "Bu gece yapılabilir: `rpi_inference.run_camera` içine (veya ayrı `codes/iha_yayin.py`) her geçerli karar için IhaSender.send_open_route / send_no_route çağrısı + kalıcı HEARTBEAT döngüsü; loopback UDP ile YKS+İKA'ya ulaştığını test et."
 },
 {
  "no": 5, "madde": "§2.2.3 / §6.2",
  "gereksinim": "Yer istasyonunda bulunan alan hakemi, canlı olarak güzergâh bilgisinin tespit edildiğini onaylamalıdır. (...) Alan Hakemi tarafından monitör üzerinden izlenmelidir.",
  "kod": ["comms/yks_gui.py:625-707 _harita_ciz — 3 şerit ŞEMATİK (x=12,5/25/37,5 m sabit), açık şerit YEŞİL / kapalı KIRMIZI '✕ KAPALI', rota = ref_xy + waypoint oklu çizgi (:686-696), NO_ROUTE → kırmızı bant 'ROTA YOK — <sebep>' + detay (:697-707)", "comms/yks_gui.py:1053 _rota_analiz segment tablosu", "comms/yks_gui.py:964-999 onayla — 2 aşamalı (1) tespit (2) İKA'ya aktarım → ACK", "comms/yks_gui.py:187 otomatik_onay=False (varsayılan; CLI'da açılamıyor :2099)", "algı görünümü (V/K tuşu) gerçek kare + maske + waypoint (:1135-1330)"],
  "test": ["tests/t64_hakem_ekrani_kapisi.py", "tests/test_yks_gui_rota_engel.py (6)", "tests/test_yks_gui_uretim_hizasi.py", "tests/test_hakem_kunye_algi_hizasi.py", "tests/test_yks_gui_dayaniklilik.py"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "Ret sebebi görünür (CONTRACTS §6.4 kural 2: üç ret üç farklı metin). Rota görünür ama harita ŞEMATİKTİR: HB (25,48) ve şerit merkezleri sabit; gerçek arenanın geometrisini değil protokolün `road` etiketini gösterir. Hakemin 'gerçek zamanlı' istediği canlı kare, algı görünümünde vardır; ikisi aynı anda görünmez (görünüm anahtarı).",
  "is": "Saha günü provası: hakeme hangi görünümün gösterileceği (harita mı algı mı) karar verilmeli; ideal: algı karesi + rota üstte, şematik altta."
 },
 {
  "no": 6, "madde": "§2.2.3",
  "gereksinim": "Yer istasyonunda bulunan alan hakemi tespit edilen güzergâh bilgisinin İKA'ya aktarıldığını onaylayacaktır.",
  "kod": ["comms/yks_gui.py:976-999 onayla 2. adım (ACK gönderir)", "comms/ika_receiver.py:264-270 İKA ACK'ı İHA'ya döner", "comms/yks_gui.py:_mesaj_isle (:810-930) — 'ACK' tipi DALI YOK; ACK yalnız demo iş parçacığında (:2022) okunuyor"],
  "test": ["tests/test_yks_gui_aktarim_zamani.py (3)"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "ÖNEMLİ",
  "not": "Hakem 'İKA'ya aktarıldı'yı EKRANDA KANITLA göremez: İKA'nın ACK'ı İHA'ya gider, YKS o ACK'ı almaz/işlemez. Hakem 2. onayı ekranda görünen bilgiye değil, operatörün sözüne verir. Ayrıca IhaSender ACK penceresi 2 s: hakem onayı 2 s içinde gelmezse İHA 'ACK alınamadı' yazar; hakem ACK'ı İHA tarafında hiç kaydedilmez.",
  "is": "Bu gece yapılabilir: İKA, OPEN_ROUTE ACK'ını YKS'ye de göndersin (peer listesi) veya İHA HEARTBEAT'ine `acked` alanı; YKS ekranında 'İKA ALDI ✓ (seq)' satırı. Test: loopback üçlü."
 },
 {
  "no": 7, "madde": "§2.2.3 / §6.4",
  "gereksinim": "Bu aktarımın İHA havada iken tamamlanması gerekmektedir.",
  "kod": ["comms/yks_gui.py:829-832 OPEN_ROUTE iniş sonrası gelirse uyarı", "comms/yks_gui.py:983-987 onayda 'aktarım İHA inişinden SONRA' / 'AKTARIM ZAMANI BİLİNMİYOR'", "comms/yks_gui.py:1813-1815 iha_indi: onay yoksa §6.4 uyarısı"],
  "test": ["tests/test_yks_gui_aktarim_zamani.py (3)"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "Yalnız UYARI üretir, zorlamaz (zorlayamaz da — hakem kararı). Havadayken tamamlama, aktarım halkasının hiç bağlı olmamasına (satır 4) bağımlıdır.",
  "is": "Satır 4 kapanınca: uçuş provasında OPEN_ROUTE → ACK → IHA_LANDED zaman damgalarını günlükten ölç."
 },
 {
  "no": 8, "madde": "§2.2.5",
  "gereksinim": "İKA, harekete geçmek için İHA'nın inişini tamamlamasını beklemek zorundadır. İHA yere temas etmeden İKA hareket edemez. İHA iniş yapmadan harekete geçen takımların görevi başarısız sayılacaktır.",
  "kod": ["ÜRETİCİ: comms/iha_inis_yayinci.py:44 send_iha_landed (ACK'li, 8 tekrar) ← comms/inis_kaniti.py:307-420 yerde_mi (Pixhawk EXTENDED_SYS_STATE=ON_GROUND + ardından GLOBAL_POSITION_INT relative_alt<1 m, ×3 ardışık, tek sysid, deadline)", "comms/protocol.py:96 iha_landed (node='iha')", "comms/ika_receiver.py:236-244 iha_inisini_bildir latch; :62-72 run_if_route_valid (motor komutu kilit altında)", "simulation/scripts/ika_nav.py:232-234 receiver_rota_gecerli; :283-300 receiver_surus_izni_bekle", "comms/yks_gui.py:1822-1830 ika_baslat: iha_landed_seq yoksa IKA_GO REDDEDİLİR; manuel 'İHA İNDİ' düğmesi (:1807) yalnız kronometre, latch açmaz"],
  "test": ["tests/test_iha_landed_gate.py (12)", "tests/test_inis_kaniti.py (23)", "tests/test_iha_inis_yayinci.py (12)", "tests/test_ika_surus_no_route.py (3)", "saha kuru koşu 2026-08-26: surus_izni=GECTI 'IHA_LANDED saha kod yolunda uretiliyor' comms/iha_inis_yayinci.py:44"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "CONTRACTS §7'deki 'üretim zincirinde iniş sinyalini üreten yok' notu BAYAT — üretici comms/iha_inis_yayinci.py (Pixhawk kanıtlı) var, kılavuzda komut var (jetson_paket/JETSON_KILAVUZ.md:387). Kalan boşluk: (a) gerçek Pixhawk/MAVLink ile hiç koşulmadı (ÖLÇÜLEMEDİ — sahte mav nesneleriyle test); (b) yayıncı OPERATÖR tarafından elle başlatılır, --kanit-timeout 5 s: iniş 5 s içinde doğrulanmazsa exit 3 ve yeniden başlatmak gerekir; (c) İKA `deadline` (satır 12) aşılırsa latch gelse de sürmez.",
  "is": "CONTRACTS §7 notunu güncelle (öneri). Pixhawk SITL (ArduPlane) ile iha_inis_yayinci'yi bir kez gerçek MAVLink akışında koştur — bu gece SITL kuruluysa yapılabilir."
 },
 {
  "no": 9, "madde": "§2.2.5",
  "gereksinim": "İHA'nın iniş operasyonunun tamamlanmasını müteakip, İKA'nın intikal süreci yer kontrol istasyonunda (YKS) görevli takım üyesi tarafından manuel olarak tetiklenir.",
  "kod": ["comms/yks_gui.py:1822-1843 ika_baslat → _cmd_gonder('IKA_GO','ika') :1762-1782 — TEK UDP paketi, ACK BEKLEMEZ, TEKRAR YOK; ardından düğme disabled (:1842) ve t_ika0 set → ikinci basış yok (:1834)", "comms/ika_receiver.py:290-303 IKA_GO latch + ACK (yalnız hedef='ika')"],
  "test": ["tests/test_ika_go_gate.py (9) — alıcı tarafı", "tests/test_yks_gui_komut_durustlugu.py (6) — gönderim hatası ekrana yansır"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "KRİTİK",
  "not": "REVIEW_LOG D-02 'IKA_GO tek atışlık ve ACK'siz' HÂLÂ GEÇERLİ (yks_gui.py:1762-1782 okundu). İKA ACK döner ama YKS onu işlemez (satır 6). SiK 433 MHz'de tek paket kaybı → İKA hiç kalkmaz, operatör düğmeye tekrar basamaz → P_görev=0. Ayrıca `son_adr['ika']` yalnız İKA'dan daha önce bir çerçeve geldiyse doludur (_dugum_adresini_ogren); İKA YKS'ye hiç paket göndermediyse 'UDP adresi yok' ile komut hiç çıkmaz (UDP kipi; seri kipte broadcast).",
  "is": "BU GECE YAPILABİLİR: _cmd_gonder(IKA_GO) → ACK gelene dek 0,25 s aralıkla tekrar (IhaSender._tekrarli_gonder kalıbı), YKS'de ACK dalı, düğme ACK gelene kadar aktif; test: loopback'te ilk paket düşürülünce ikinci paketle latch açılıyor."
 },
 {
  "no": 10, "madde": "§2.2.5 / §6.2",
  "gereksinim": "İHA'dan aldığı güzergâh verisini doğrultusunda İKA; otonom olarak açık olan güzergâhı takip ederek HB'ye ilerleyecektir. Otonom hareket etmeyen İKA'nın görevi başarısız sayılacaktır.",
  "kod": ["simulation/scripts/ika_nav.py:295-400 navigate (waypoint takip, heading konum geçmişinden)", "simulation/scripts/ika_nav.py:90-99 send_vel = subprocess `gz topic` (Gazebo)", "simulation/scripts/ika_nav.py:41-88 get_pose = subprocess `gz model` (Gazebo)"],
  "test": ["tests/test_ika_go_gate.py / test_iha_landed_gate.py (motor komutu = send_vel sayacı, gz yok)", "saha kuru koşu 2026-08-26: motor=SAHIPSIZ 'gercek motor surucusu yok; send_vel yalnizca gz subprocess'i'"],
  "kanit": "YOK",
  "risk": "KRİTİK",
  "not": "Gerçek İKA için ne motor sürücüsü ne konum kaynağı (GNSS/odometri) var. grep pigpio/RPi.GPIO/roboclaw/sabertooth → 0. Sahada `gz` yok → subprocess FileNotFoundError capture_output ile YUTULUR, uyarı basılmaz (CONTRACTS §11.3 Halka 10). Kapı (rota∧IKA_GO∧IHA_LANDED) doğru ama tekerlek dönmez.",
  "is": "Bu gece YAPILAMAZ (donanım kararı: İKA sürücü kartı/protokolü bilinmiyor — insan girdisi gerekli). Yapılabilir kısmı: send_vel/get_pose'u soyut arayüz (`IkaSurucu`) arkasına al; gz yoksa fail-closed HATA bassın, sessiz yutmasın."
 },
 {
  "no": 11, "madde": "§2.2.6 / §2.1",
  "gereksinim": "İKA'nın, İHA tarafından bildirilen güzergâhı takip ederek HB sınırları içerisine girmesi ile görev başarılı şekilde icra edilmiş kabul edilecektir. HB: 2 m × 2 m, üzerinde kırmızı H.",
  "kod": ["codes/karar_sozlesmesi.py:754 hb_maskesi / :811 hb_konumu (T72 · kırmızı-kare dedektörü, bariyer tümleyeni)", "codes/rpi_inference.py:1279-1289 analyze_path: HB yalnız `goruntu` VERİLİRSE aranır; yoksa hedef = üst bant", "ÇAĞRI YERLERİ: codes/rpi_inference.py:1586, :1689, :1781 ve comms/yks_gui.py:1491 — HİÇBİRİ `goruntu=` GEÇMİYOR (grep 'goruntu=' → yalnız imza :1083)", "HB varış tespiti: simulation/scripts/ika_nav.py:31 FINAL_WP_RADIUS=0.3 m son waypoint'e varış = 'HB ULAŞILDI' (:405); comms/yks_gui.py:1845 hb_temas = manuel kronometre düğmesi"],
  "test": ["tests/test_hb_dedektoru.py (25) — dedektör izole, sentetik n=260", "saha kuru koşu 2026-08-26: hedef_konumu=SAHIPSIZ"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "KRİTİK",
  "not": "T72 'KAPANDI' ama bağlantı 'geriye uyumlu, goruntu=None' bırakıldı ve hiçbir üretim çağrısı görüntüyü geçmiyor → sahada rota HB'ye değil karenin ÜST BANDINA gider. HB dedektörü gerçek karede hiç ölçülmedi (sentetik 260/260). Ayrıca `hb_konumu` ölçek kahinine de bağlı değil (rpi_inference'ta yalnız :1285). ika_nav HB'ye 'girdiğini' bilmez; son waypoint'i HB sayar.",
  "is": "BU GECE KISMEN: analyze_path çağrılarına `goruntu=bgr` geçir (4 satır) + saha kuru koşusunun hedef_konumu halkasını yeni sahibe bağla; ardından gerçek DJI/arena karelerinde HEDEF_YOK oranını ÖLÇ (HB görünmeyen karede her karede NO_ROUTE olur — bu bir ürün kararıdır, mimar onayı gerekir)."
 },
 {
  "no": 12, "madde": "§6.2 / §6.4 / §7",
  "gereksinim": "İHA görev süresi ≤15 dk (fırlatma→paraşütle iniş); İKA HB'ye ≤10 dk; FDA tüm operasyon ≤10 dk; süre aşımı görevi geçersiz kılar.",
  "kod": ["comms/yks_gui.py:183-184 IHA_LIMIT=900, IKA_LIMIT=600 kronometre + günlük uyarısı", "simulation/scripts/ika_nav.py:545 --timeout varsayılan 60 s: tek `deadline` rota + IKA_GO + IHA_LANDED ÜÇÜNÜ birden kapsar (:551-566); aşılırsa exit(3) 'İKA hareket etmez'", "simulation/scripts/navitas_sim.py:154 --route-timeout 60"],
  "test": ["tests/test_yks_gui_*", "uçtan uca süre bütçesi: YOK (ARCHITECT_PLAN §8 T15 'tahmin')"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "KRİTİK",
  "not": "Sahada rota aktarımı ile iniş arasında dakikalar geçer; ika_nav varsayılan 60 s deadline ile İKA, IHA_LANDED gelmeden zaman aşımına düşer ve bir daha dinlemez. Kılavuzlarda ika_nav saha komutu/timeout YOK (grep jetson_paket/JETSON_KILAVUZ.md, results/t123/saha_gunu_kontrol_listesi.md → ika_nav komutu yok).",
  "is": "BU GECE YAPILABİLİR: saha kontrol listesine `ika_nav --timeout 1500` (≥ 15 dk uçuş + pay) yazılmalı; daha iyisi deadline'ı rota için ayrı, iniş için ayrı tutan iki parametre."
 },
 {
  "no": 13, "madde": "§6.4",
  "gereksinim": "Veri akışının sağlanamadığı durumlarda uçuş geçersiz sayılacaktır. (bağlantı kaybı davranışı)",
  "kod": ["comms/ika_receiver.py:309-321 poll: hb_timeout=3 s → link_lost → on_link_lost; latest KORUNUR", "simulation/scripts/ika_nav.py:341-351 link_ok yoksa GÜVENLİ DURMA, dönünce aynı waypoint'ten devam", "comms/iha_sender.py:151 send_heartbeat; iha_inis_yayinci.py:55-56 iniş sonrası heartbeat sürdürür"],
  "test": ["tests/test_ika_no_route_recovery.py", "tests/test_ika_surus_no_route.py (3)", "comms/test_comms.py"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "Gerçek SiK 433 MHz RF üzerinde hiç ölçülmedi (10_PDF_SARTNAME_DDR_UYUMU.md: '915 MHz / 300 m / <100 ms saha kanıtı yok'). İniş sonrası HEARTBEAT'i sürdüren tek üretim yolu iha_inis_yayinci'nin `heartbeat_until` parametresidir; CLI (`main`) bunu GEÇMİYOR (:131-134 → iha_inisini_yayinla(peers) heartbeat_until=None) → yayıncı çıkınca 3 s sonra İKA link_lost → GÜVENLİ DURMA, İKA hiç sürmez.",
  "is": "BU GECE YAPILABİLİR: iha_inis_yayinci CLI'ye `--heartbeat-sure` ekleyip iniş sonrası heartbeat'i 10 dk sürdür; test: yayıncı çıkışından 3 s sonra link_lost olmadığı."
 },
 {
  "no": 14, "madde": "§2.2.4",
  "gereksinim": "Paraşüt açma komutu otonom sistem tarafından verilebileceği gibi yer istasyonundan manuel tetikleme ile de gerçekleştirilebilir (ceza puanı).",
  "kod": ["comms/yks_gui.py:1904 parasut → CMD PARACHUTE hedef=iha (+ −50 ceza sayacı)", "Tüketici: grep -rn PARACHUTE comms codes simulation (yks_gui hariç) → 0"],
  "test": ["tests/test_yks_gui_komut_durustlugu.py (6) — yalnız gönderim"],
  "kanit": "BELİRSİZ",
  "risk": "KÜÇÜK",
  "not": "Uçuş kontrolü (Pixhawk) repo dışı; PARACHUTE komutunu İHA tarafında alan kod yok. Yarışmada emniyet pilotu/RC ile tetiklenmesi muhtemel — yazılıma düşmüyor olabilir.",
  "is": "Mimar kararı: bu komut YKS'de kalacaksa MAVLink köprüsü gerekir; kalmayacaksa düğme kaldırılsın (yanıltmasın)."
 },
 {
  "no": 15, "madde": "§5.3.2",
  "gereksinim": "FDA: 20×20 m test alanı, asgari 30 m irtifa.",
  "kod": ["codes/karar_sozlesmesi.py:263 SARTNAME_ASGARI_IRTIFA_M=30.0; :953 SENARYO_BOYUTLARI_M FDA=20.0", "codes/karar_sozlesmesi.py asgari_irtifa_notu (T171/D-319: RET DEĞİL GÖSTERİM; hakem günlüğüne düşer). ⚠ DÜZELTME (D-319): bu satır önce ölçek reddi fonksiyonunun irtifayı denetlediğini iddia ediyordu — YANLIŞTI. O daldaki İKİ KOL DA `return None` yapıyordu ve hiçbir çağıran irtifa geçmiyordu, yani şart HİÇ uygulanmıyordu. Tam alıntı ve kanıt: REVIEW_LOG D-319."],
  "test": ["tests/test_olcek_kahini.py", "tests/test_rpi_canli_olcek.py", "tests/test_saha_parametrik.py"],
  "kanit": "KOD_VAR_TEST_YOK",
  "risk": "ÖNEMLİ",
  "not": "🔴 D-319: asgari 30 m şartı 2026-08-27'ye kadar HİÇ uygulanmıyordu ve bu rapor uygulandığını İDDİA EDİYORDU. Artık `asgari_irtifa_notu` var (ret değil gösterim) ve üretim heartbeat'e `alt` yayınlıyor; saha ölçümü H-A'ya bağlı. Sentetik üreteç FDA profilini (20×20, ≥30 m) taşımıyor (ARCHITECT_PLAN §8 T14 / S8) — model o ölçekte ölçülmedi.",
  "is": "FDA drone'u geldiğinde 30 m'den gerçek kare; sentetik FDA profili ayrı görev."
 },
 {
  "no": 16, "madde": "§2.2.2 / §6.2",
  "gereksinim": "Fırlatma sonrası İHA tam otonom uçuş moduna geçecek; tüm süreçler (seyrüsefer, tespit, veri aktarımı, sürüş) tam otonom.",
  "kod": ["Uçuş otonomisi: repo dışı (Pixhawk/ArduPilot). Repoda yalnız telemetri OKUMA: comms/inis_kaniti.py BagilIrtifaOkuyucu; codes/rpi_inference.py:233 CanliOlcekSaglayici"],
  "test": ["—"],
  "kanit": "BELİRSİZ",
  "risk": "ÖNEMLİ",
  "not": "ÖLÇÜLEMEDİ: uçuş planı, görev waypoint'leri, otonom iniş tetiği bu depoda yok. YKS 'ARM'/'FIRLATMA' düğmeleri yalnız CMD gönderir/kronometre başlatır; İHA tarafında tüketici yok (grep 'ARM' iha tarafı → yok).",
  "is": "Kapsam kararı (mimar): uçuş otonomisi hangi depoda/kimde? DDR'de 'tam otonom' iddiası için kanıt (10_PDF_..: 'desteklenmiyor')."
 },
 {
  "no": 17, "madde": "§2.2.3 (ölçek zorunluluğu — dolaylı)",
  "gereksinim": "Rota metrik olarak İKA'ya aktarılır (waypoints metre, ref_xy) → ölçek (m/px) gerekli.",
  "kod": ["codes/karar_sozlesmesi.py:272 mpp_irtifadan, :1000 olcek_kahini (telemetri > arena > araç), :316 rota_olcek_reddi", "codes/rpi_inference.py:1257 OLCEK_YOK fail-closed"],
  "test": ["tests/test_olcek_ve_c_uzayi.py", "tests/test_olcek_uretim_baglantisi.py", "tests/test_rpi_canli_olcek.py", "saha kuru koşu 2026-08-26: olcek=GECTI 'canli telemetri bu kare icin gecerli mpp uretti'"],
  "kanit": "KANITLI_TEST",
  "risk": "ÖNEMLİ",
  "not": "GLOBAL_POSITION_INT.relative_alt home'a göredir, yerden yükseklik değil (inis_kaniti.py docstring). Arena kotu ile home farklıysa mpp sistematik sapar; HB çapraz kontrolü (§5.4) bunu yakalar ama HB dedektörü üretime bağlı değil (satır 11).",
  "is": "Satır 11 ile birlikte: HB çapraz kontrolünü canlı yola bağla."
 },
 {
  "no": 18, "madde": "§6.2",
  "gereksinim": "Hakem, tespitin başarılı olduğunu sözlü olarak onaylamalıdır. Hakem onayı alınmayan tespitler geçersiz sayılır. (otomatik onay yok)",
  "kod": ["comms/yks_gui.py:187 otomatik_onay=False; :2099 CLI'da True yapılamıyor; :14 'yks_monitor otomatik onay kaldırıldı'", "comms/yks_gui.py:1828-1830 hakem ACK'ı olmadan IKA_GO reddedilir"],
  "test": ["tests/test_yks_gui_demo_kaynak.py", "tests/test_yks_gui_komut_durustlugu.py"],
  "kanit": "KANITLI_TEST",
  "risk": "KÜÇÜK",
  "not": "Demo kipinde (`--demo`) `onayla` 2,5 s sonra otomatik çağrılabilir (:851-852) — yalnız otomatik_onay True iken; CLI bunu açmıyor.",
  "is": "Yok."
 },
]

KRITIK = [
 ("K1", "Üretim algı yolu (rpi_inference) telsize HİÇ yazmıyor — OPEN_ROUTE/NO_ROUTE üreticisi yalnız Gazebo betiği (iha_detect_send + iha_haritala rota.json).", "codes/ altında IhaSender çağrısı 0; run_camera yalnız ekrana basar (rpi_inference.py:1735-1812)", "EVET — run_camera'ya IhaSender bağlamak ve loopback testi bir gecelik iş; SiK üzerinde ölçüm ayrı."),
 ("K2", "Gerçek İKA için motor sürücüsü ve konum kaynağı yok; send_vel/get_pose Gazebo `gz` subprocess'i, sahada sessizce yutulur.", "ika_nav.py:41-99; saha kuru koşu 2026-08-26 motor=SAHIPSIZ", "HAYIR — İKA donanım kararı (sürücü kartı/protokol) insana bağlı; bu gece yalnız soyutlama + 'gz yok → yüksek sesle hata' yapılabilir."),
 ("K3", "HB dedektörü üretime BAĞLI DEĞİL: analyze_path'in 4 üretim çağrısı da `goruntu=` geçmiyor → rota HB'ye değil karenin üst bandına gider; saha kuru koşu hedef_konumu=SAHIPSIZ.", "rpi_inference.py:1586/1689/1781, yks_gui.py:1491; grep 'goruntu=' → yalnız imza", "KISMEN — çağrılara `goruntu=bgr` eklemek küçük; ama HB görünmeyen karede HEDEF_YOK=NO_ROUTE ürün kararıdır ve gerçek karede HB isabeti ÖLÇÜLMEDİ."),
 ("K4", "IKA_GO tek UDP paketi, ACK beklemez, tekrar yok, düğme kilitlenir (D-02 hâlâ geçerli); YKS İKA ACK'ını hiç işlemiyor.", "yks_gui.py:1762-1782, :1834-1842; _mesaj_isle'de 'ACK' dalı yok", "EVET — _tekrarli_gonder kalıbı + YKS'de ACK dalı + loopback paket-düşürme testi."),
 ("K5", "İKA `--timeout` varsayılan 60 s tek deadline rota+IKA_GO+IHA_LANDED'ı kapsıyor; sahada iniş dakikalar sonra → İKA zaman aşımıyla çıkar. Kılavuzlarda ika_nav saha komutu yok.", "ika_nav.py:545-566; jetson_paket/JETSON_KILAVUZ.md ve saha_gunu_kontrol_listesi.md'de ika_nav yok", "EVET — kontrol listesine komut + timeout; iki ayrı deadline küçük kod değişikliği."),
 ("K6", "iha_inis_yayinci CLI iniş sonrası HEARTBEAT sürdürmüyor (heartbeat_until=None) → yayıncı çıkınca 3 s sonra İKA link_lost → sürmez.", "iha_inis_yayinci.py:131-134 vs :55-56; ika_receiver.py:309-316 hb_timeout=3", "EVET — CLI'ye `--heartbeat-sure` (varsayılan 600 s) + test."),
 ("K7", "Saha rota yolu (analyze_path) 3-koridor kapı mantığını (koridor_adaylari) kullanmıyor; saha kuru koşu 2026-08-26 `rota` halkası BELIRSIZ_TEK_KAPI ile DÜŞTÜ; gerçek arena isabeti tek kareyle ölçülü.", "costmap_path_finder.py:1025 (yalnız rota_bul çağırır); ozet.json rota=DUSTU", "HAYIR (ölçüm işi) — DJI/arena karelerinde yer gerçekli isabet ölçümü gerekli; bu gece yalnız ölçüm betiği hazırlanabilir."),
 ("K8", "Hakem 'İKA'ya aktarıldı' onayını ekranda kanıtsız veriyor; İHA'nın ACK penceresi 2 s olduğundan hakem ACK'ı İHA'ya hiç ulaşmayabilir.", "yks_gui.py:964-999; iha_sender.py:93-121", "EVET — K4 ile aynı değişiklik paketinde (ACK yansıtma)."),
]

OLCULEMEDI = [
 "Gerçek Pixhawk/MAVLink akışında iha_inis_yayinci — yalnız sahte mav nesneleriyle test edildi.",
 "SiK 433 MHz gerçek RF üzerinde paket kaybı / gecikme / ACK süresi.",
 "HB dedektörünün (hb_konumu) GERÇEK arena/DJI karesinde isabeti — yalnız sentetik n=260.",
 "Saha yolunda (analyze_path) seçilen şeridin 3 fiziksel güzergâhtan hangisi olduğunun gerçek karede isabeti.",
 "Uçtan uca süre bütçesi (fırlatma→iniş, İKA teker→HB) — hiç ölçülmedi (T15).",
 "İKA donanımı (sürücü, konum kaynağı) — repoda yok, ölçülecek şey yok.",
 "Uçuş otonomisi (ARM/FIRLATMA/PARACHUTE tüketicisi) — repo dışı.",
]

def md():
    L = []
    L.append(f"# ŞARTNAME UYUM BOŞLUK DENETİMİ — {TARIH}\n")
    L.append("Salt okuma denetimi; kod DEĞİŞTİRİLMEDİ. Kaynak: `Ileri_Otonom_Sistemler_..._Sartname_TR_Ltktw.pdf` (30 sayfa, PyMuPDF ile `sartname_metin.txt`). "
             "Kanıt: dosya:satır okuması, grep, `results/saha_kuru_kosu_20260826_001414/ozet.json`, bu koşuda `unittest` 819 OK (2 skip) ve `test_rota_sentetik.py` 15/15.\n")
    L.append("Kanıt durumu sözlüğü: **KANITLI_TEST** = kod + koşan test; **KOD_VAR_TEST_YOK** = kod var, hüküm uçtan uca sınanmıyor; **YOK** = kod yok; **BELİRSİZ** = repo dışı / kapsam belirsiz.\n")
    L.append("## 1. Hüküm tablosu\n")
    L.append("| # | § | Gereksinim (alıntı) | Karşılayan kod | Test / kanıt | Kanıt durumu | Saha riski | Önerilen iş |")
    L.append("|---|---|---|---|---|---|---|---|")
    for s in SATIRLAR:
        L.append("| {no} | {madde} | {g} | {k} | {t} | **{kd}** | **{r}** | {i} |".format(
            no=s["no"], madde=s["madde"], g=s["gereksinim"].replace("|", "¦"),
            k="<br>".join(s["kod"]).replace("|", "¦"), t="<br>".join(s["test"]).replace("|", "¦"),
            kd=s["kanit"], r=s["risk"], i=s["is"].replace("|", "¦")))
    L.append("\n## 2. Satır notları (kanıt ayrıntısı)\n")
    for s in SATIRLAR:
        L.append(f"**{s['no']} · {s['madde']}** — {s['not']}\n")
    L.append("## 3. Görevde özellikle sorulanlar\n")
    L.append("- **§2.2.3 hakem canlı onay** — ekran: 3 şerit şematiği (yeşil açık / kırmızı kapalı), ref_xy+waypoint oklu rota, segment tablosu, güven çubuğu, NO_ROUTE kırmızı bant **sebep+detay ile**, 2 aşamalı onay düğmesi; otomatik onay kapalı. Ret sebebi GÖRÜNÜR (satır 5). Eksik: İKA'nın aldığına dair ekran kanıtı (satır 6).")
    L.append("- **Aktarım havadayken** — YKS uyarır ama zorlamaz (satır 7). Asıl boşluk: üretim algı yolu telsize yazmıyor (satır 4). IKA_GO ACK'siz (D-02) hâlâ geçerli (satır 9).")
    L.append("- **§2.2.5 iniş sinyali** — üretici VAR: `comms/iha_inis_yayinci.py:44` ← `inis_kaniti.yerde_mi` (Pixhawk ON_GROUND + relative_alt<1 m ×3). CONTRACTS §7'deki 'üretim zincirinde üreten yok' notu **BAYAT** (öneri: güncellensin). Kalan: gerçek MAVLink ile koşulmadı; CLI iniş sonrası heartbeat sürdürmüyor (K6); İKA deadline (K5).")
    L.append("- **HB'ye varış / hb_maskesi** — `hb_konumu` yalnız `analyze_path(goruntu=...)` verilirse çağrılır (rpi_inference.py:1283-1289); üretim çağrılarının HİÇBİRİ `goruntu` geçmiyor → sahada HB aranmaz, hedef üst banttır. Saha kuru koşu 2026-08-26 `hedef_konumu=SAHIPSIZ`. İKA'nın HB'ye girdiğini bilen kod yok; son waypoint'e 0,3 m yaklaşmak 'HB ULAŞILDI' sayılıyor.")
    L.append("- **3 güzergâhtan seçim (koridor_adaylari)** — yalnız `rota_bul` (Gazebo yolu) çağırır; saha yolu `analyze_path` şeridi darboğaz pikselinden etiketler. Saha kuru koşu `rota` halkası BELIRSIZ_TEK_KAPI ile düştü.")
    L.append("- **Yanlış güzergâh = 0 puan, fail-closed nerede** — karar_sozlesmesi ret sebepleri (:76-88), analyze_path `_don` (:1127), `_rota_kararini_esikle` (:1362), `IhaSender.send_open_route` son savunma (iha_sender.py:131-137), YKS eşik altı OPEN_ROUTE'a ACK vermez (:813-816), İKA `run_if_route_valid` kilit altında motor (ika_receiver.py:62-72), T141 kapısı. Hepsi test kilitli.\n")
    L.append("## 4. KRİTİK boşluklar — önem sırasıyla\n")
    L.append("| # | Boşluk | Kanıt | Bu gece yapılabilir mi? |")
    L.append("|---|---|---|---|")
    for k, b, kanit, gece in KRITIK:
        L.append(f"| {k} | {b} | {kanit} | {gece} |")
    L.append("\n## 5. ÖLÇÜLEMEDİ\n")
    for o in OLCULEMEDI:
        L.append(f"- {o}")
    L.append("\n## 6. Koşulan komutlar ve ham çıktı\n")
    L.append("```text\n<venv> -m unittest discover -s tests -q   → Ran 819 tests in 116.405s / OK (skipped=2) / EXIT=0   (unittest_cikti.txt)\n<venv> codes/test_rota_sentetik.py         → SONUC: 15/15 dogru / [OK] TUM DETERMINISTIK SAHNELER GECTI / EXIT=0   (rota_sentetik_cikti.txt)\ngrep -rn 'IhaSender|send_open_route' codes → 0 eşleşme (üretim algı yolu telsize yazmıyor)\ngrep -n 'goruntu=' codes/rpi_inference.py comms/yks_gui.py simulation/scripts/*.py → yalnız codes/rpi_inference.py:1083 (imza)\ngrep -rn PARACHUTE comms codes simulation (yks_gui hariç) → 0\ngrep -rli 'pigpio|RPi.GPIO|roboclaw|sabertooth' codes comms simulation → 0\nresults/saha_kuru_kosu_20260826_001414/ozet.json → kamera GECTI · model_yukleme GECTI · cikarim GECTI · maske GECTI · olcek GECTI · hedef_konumu SAHIPSIZ · rota DUSTU (BELIRSIZ_TEK_KAPI) · aktarim GECTI · surus_izni GECTI · motor SAHIPSIZ\n```\n")
    L.append("## 7. Sözleşme ÖNERİLERİ (değiştirilmedi)\n")
    L.append("- CONTRACTS §7 'üretim zincirinde iniş sinyalini üreten yok' notu → `comms/iha_inis_yayinci.py` sahip olarak yazılsın; 'IKA_GO ACK'siz' notu ise hâlâ doğrudur, korunmalı.")
    L.append("- CONTRACTS §11.2 halka tablosu 2026-08-26 kuru koşuyla uyumsuz (kamera/model/olcek/aktarim/surus_izni artık GEÇTİ; hedef_konumu ve motor hâlâ SAHİPSİZ) — tablo koşucu çıktısından yenilensin.")
    L.append("- CONTRACTS §6.4 `HEDEF_YOK` satırı 'T72' der; üretim çağrılarının `goruntu` geçmediği not edilsin (aksi hâlde sözleşme var olmayan davranışı vaat eder — D-193 sınıfı).")
    return "\n".join(L) + "\n"

def main():
    (KOK / "rapor.md").write_text(md(), encoding="utf-8")
    (KOK / "rapor.json").write_text(json.dumps({
        "tarih": TARIH, "kaynak_pdf": "Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf",
        "kapi": {"unittest": "Ran 819 tests / OK (skipped=2)", "test_rota_sentetik": "15/15"},
        "saha_kuru_kosu": "results/saha_kuru_kosu_20260826_001414/ozet.json",
        "satirlar": SATIRLAR,
        "kritik": [{"id": k, "bosluk": b, "kanit": c, "bu_gece": g} for k, b, c, g in KRITIK],
        "olculemedi": OLCULEMEDI,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("yazildi:", KOK / "rapor.md", KOK / "rapor.json")

if __name__ == "__main__":
    main()
