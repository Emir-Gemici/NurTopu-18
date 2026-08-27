# ŞARTNAME UYUM BOŞLUK DENETİMİ — salt okuma (2026-08-26)

Kaynak: `Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf` (30 sayfa; metin PyMuPDF ile çıkarıldı, 56 919 karakter).
Kapsam: §2.1, §2.2.2–2.2.6, §5.3.2, §6, §6.2, §6.4, §7. Yazılıma düşmeyen hükümler (mancınık, ağırlık, rapor, takım) atlandı.
Kod DEĞİŞTİRİLMEDİ. Her satırın kanıtı grep/okuma ile alındı; ölçülemeyen "ÖLÇÜLEMEDİ" yazıldı.

Kanıt durumu sözlüğü: **KANITLI_TEST** = kod var ve `tests/` altında koşan test var · **KOD_VAR_TEST_YOK** = kod var, o davranışı sınayan test yok ya da entegrasyon sınanmıyor · **YOK** = karşılayan kod yok · **BELİRSİZ** = kod var ama sahada hangi yolun koştuğu / davranış tek başına belirlenemiyor · **ÖLÇÜLEMEDİ** = repo dışı (uçuş kontrolcüsü, donanım).

---

# TAZELEME - 2026-08-26 aksami (olcum; kod DEGISMEDI)

> Asagidaki §0-§4 **sabah cekilmis fotograftir ve SILINMEDI** (kanit zinciri korunur).
> Bu bolum o fotografin **hangi satirlarinin bayatladigini** bugunku olcumle soyler.
> Nerede celisirlerse **bu bolum gecerlidir**.

## T0 - Bugun gercekten kosulan kapilar

```
> <venv> -B codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI                       (RC=0)

> <venv> -B -m unittest discover -s tests -q
Ran 1002 tests in 82.606s
OK (skipped=2)                                              (RC=0)
```
(Sabahki kosumda 855 testti; brifingde "master 988" deniyordu - bugun **1002**.
Fark bugun kapanan T146/T147/T148/T155 testleridir, gevsetme degil.)

```
> CUDA_VISIBLE_DEVICES=-1 <venv> -B scripts/saha_kuru_kosu.py --cikti results/saha_zinciri_20260826/kosu_cpu
  kamera         GECTI      kaynak parametrik ve VideoCapture'a BESLENIYOR
  model_yukleme  GECTI      agirlik manifestten turetiliyor (navitas_seg_v36_best.pt)
  cikarim        GECTI      tek kare cikarimi tamamlandi                      [1621 ms]
  maske          GECTI      {0,1} anahtarli maskeler uretildi
  olcek          GECTI      canli telemetri bu kare icin gecerli mpp uretti   (mpp=0,0338)
  hedef_konumu   SAHIPSIZ   HB'nin tek kaynagi Gazebo meta.txt; --hb girisi yok
  rota           DUSTU      rota uretilemedi: durum=BELIRSIZ_TEK_KAPI
  aktarim        GECTI      uretim yolu run_camera karari loopback IKA'ya OPEN_ROUTE yazdi
  telsiz halkasi GECTI      {'open_route_alindi': True, 'heartbeat': 1, 'ack': ['ika']}
  surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor
  motor          SAHIPSIZ   gercek motor surucusu yok
GECTI 7 · DUSTU 1 · SAHIPSIZ 2 · ATLANDI 0
```
**GPU KOSULMADI** - `torch.cuda.is_available()` -> `False`, `nvidia-smi` -> `14 MiB, 0 %`
(PC bugun BSOD verdi: `results/pc_cokme_20260826/rapor.md`).
Sabahki kosum `--atla-cikarim` ile yapildigi icin `olcek DUSTU` gorunuyordu; **o bir
zincir kopuklugu degil, atlanan cikarimin yan etkisiydi.** Bugun tam zincirde GECTI.

**Halka 7 IKI kusur tasiyordu, IKISI DE KAPANDI (2026-08-27):** (T160) kuru kosu `rota_bul` cagiriyordu; (T38/D-301) ve OTOPARK karesiyle, kareyle ilgisiz sahte bir olcekle sinaniyordu — artik kabul dagilimindan kare + o karenin olcegiyle kosuyor ve halka GECIYOR
(`scripts/saha_kuru_kosu.py:709`), oysa D-295/T151 ile **uretim yolu `analyze_path`**
ilan edildi. Yani tek `DUSTU` satiri **tanisal** yolun sonucudur; uretim karar yolu
kuru kosuda **hic olculmuyor** (D-297 §1, T156).

## T1 - Hukum satirlarinin BUGUNKU durumu

Sabahki tablo **21 satirdir (R1-R21)**; gorev metni "18 hukum" diyordu - sayi
tutmuyor, duzeltildi. Taramada **bir hukum daha atlanmis** cikti -> **R22**.

| # | Sabahki durum | BUGUN | Ne degisti · kanit |
|---|---|---|---|
| R1 | BELIRSIZ (iki karar yolu) | **BEYAN EDILDI, KAPI YOK** | T151 kapandi (D-295): `analyze_path` **URETIM**, `rota_bul` **TANISAL** - CONTRACTS §11.2-EK. Davranis degismedi (Secenek C). Actigi iki bosluk **T155/T156**. T155 kapandi (D-296: yayinlanan `road` 6/15 -> **15/15**, `results/t155/`). **T156 ACIK**: genel kapi hala yalniz `rota_bul`u zorluyor. |
| R2 | OLCULEMEDI | **OLCULEMEDI** (degismedi) | Ucus kontrolcusu repo disi. |
| R3 | KANITLI_TEST | **KANITLI_TEST + kuru kosuda GECTI** | Olcek halkasi bugun tam zincirde `mpp=0,0338` uretti (sabah `--atla-cikarim` yuzunden DUSTU gorunuyordu). Gercek Pixhawk **hala OLCULMEDI**. |
| R4 | **KOD_VAR_TEST_YOK · KRITIK** | **KAPANDI** | **T146** (K1 telsiz halkasi): `run_camera` -> `iha_sender.KararYayinci`; CONTRACTS §6.5. Kanit: `results/K1_telsiz_halkasi/rapor.md` + `tests/test_rpi_telsiz_yayin.py` (11 test); kuru kosuda `uretim_yolu_telsiz.open_route_alindi=True`. SiK seri **OLCULMEDI** (D-287 §2). |
| R5 | KANITLI_TEST | degismedi | - |
| R6 | **BELIRSIZ · ONEMLI** | **KAPANDI** | **T147** (K8): IKA ACK'i YKS'ye de gidiyor (`ika_nav --yks`); "IKA ALDI" gelmeden 2. onay acilmiyor. Kanit: `results/k4_k8_ika_go_ack/rapor.md`, `tests/test_ika_go_ackli_tekrar.py` (11 test), CONTRACTS §6.6. |
| R7 | KANITLI_TEST | degismedi | - |
| R8 | **KOD_VAR_TEST_YOK · KRITIK** (D-02) | **KAPANDI** | **T147** (K4): `IKA_GO` ayni-seq ACK'li tekrar, ust sinir, idempotent latch, ACK yoksa dugme yeniden acik. CONTRACTS §6.6 baglayici. Kanit: `results/k4_k8_ika_go_ack/` (5 mutasyonun 5'i yakalandi). |
| R9 | OLCULEMEDI / BELIRSIZ | degismedi | Otonom parasut repo disi; manuel tetigin IHA'da alicisi yok. -50 ceza kaydi `yks_gui.py:2024`. |
| R10 | KANITLI_TEST · "runbook yok" | **KAPANDI (kod) · runbook hala EKSIK** | **T148** (K6): inis sonrasi heartbeat suruyor (`--heartbeat-sure`, varsayilan §6.2 IKA suresi 600 s) -> 3 s'de `link_lost` bitti. Kanit: `tests/test_k5_k6_sure_limitleri.py` (9 test). **Ama `JETSON_KILAVUZ.md`'de `iha_inis_yayinci.py` icin hala CALISTIRMA KOMUTU YOK** - yalniz `cp` satiri (`:301`). Bu bosluk `results/saha_zinciri_20260826/saha_gunu.md` adim 6'da EKSIK isaretlendi. |
| R11 | KANITLI_TEST | degismedi | R8 ile birlikte guclendi. |
| R12 | **YOK · KRITIK** | **ACIK - INSAN/DONANIM** | **T149**. Kuru kosu `motor SAHIPSIZ`; saha surucu importu **0**. Donanim karari gelmeden kapanmaz. |
| R13 | KOD_VAR_TEST_YOK · ONEMLI | **ACIK - ve artik OLCULDU: baglanmamali** | **T150**. D-295 §2: `hb_konumu` gercek inis pedinde **%0**, kirmizi arabada %100 -> bugun `goruntu=` baglanirsa her kare `HEDEF_YOK`'a dusme riski. Karar **insanda**; "olcmeden baglama" hukmu artik olcumle destekli. |
| R14 | KANITLI_TEST · kararlilik acik | **KOTULESTI (olculdu, gizlenmiyor)** | D-295 §3: v36 karar kararliliginda **v35'ten kotu**; fazlaligin tamami "rota VAR/YOK cevrilmesi" (v36 6, v35 0-1), yon fail-closed ama saha elverisliligini dusurur. Terfi geri alinmadi (on kayit §16; geri alma **kullanici karari**). |
| R15 | BELIRSIZ | degismedi | T14/T15 acik. |
| R16 | KOD_VAR_TEST_YOK | **KAPANDI** | **T148** (K5): `SARTNAME_IHA_GOREV_SURESI_S=900`, `SARTNAME_IKA_GOREV_SURESI_S=600` `codes/karar_sozlesmesi.py:1539-1542`; `ika_nav` TEK deadline yerine **iki ayri bayrak** (`--bekleme-suresi` / `--surus-suresi`); cikis kodu 4 testle kilitli. CONTRACTS §7.1. |
| R17 | OLCULEMEDI | **KAPANDI (yazilim tarafi) — T162 / D-307** | Sartname SS6.2/SS6.4 ALAN IHLALI denetimi GUI'de VARDI ama uretimde `x,y` ureten yol YOKTU: kapi sahada OLUYDU. Artik `--ub-referans LAT,LON` ile her HEARTBEAT yerel `x,y` tasiyor (konum ayni telemetri okuyucusundan, ikinci yol acilmadi) ve GUI denetimi sozlesme sabitiyle (`SARTNAME_IHA_UB_KENAR_M`) yapiliyor. Kapi 19/19 (uretim dongusu gercekten kosuluyor). ⚠ Gercek Pixhawk hâlâ YOK — uctan uca sahte GLOBAL_POSITION_INT ile olculdu; geofence'in KENDISI (Pixhawk parametresi) hâlâ repo disi. |
| R18 | **YOK · KRITIK** | **YARISI KAPANDI** | Aktarim otonom oldu (R4/T146). **Surus hala YOK** (R12/T149). |
| R19 | KANITLI_TEST | guclendi | T148 heartbeat suresi §6.2'ye baglandi. |
| R20 | KOD_VAR_TEST_YOK | **hala OLCULMEDI** | Gercek SiK cifti yok. Kuru kosu yalniz UDP loopback. DDR'deki ">%98, 300 m" iddiasinin kaniti **hala yok**. |
| R21 | BELIRSIZ | degismedi | - |
| **R22** | *(tabloda YOKTU)* | **YENI - INSAN/DONANIM** | §2.2.6: *"IKA'nin belirlenen yukleri tasiyarak hedef bolgeye intikal etmesi esastir... yapisal butunlugunu koruyor olmasi ve tasidigi yuku/yukleri eksiksiz muhafaza etmesi zorunludur; aksi takdirde ilgili gorev basarisiz sayilir."* Yazilima dusmez ama **"gorev basarisiz"** yaptirimli ve tabloda hic yoktu (D-297 §3). |

### K2 ve K3 - insan/donanim karari olarak KALIR (degismedi)
- **K2 · IKA motor surucusu (R12 / T149):** yazilim tarafinda yapilacak is
  soyutlamadir; **hangi surucuye** baglanacagi donanim kararidir. Kuru kosu bugun de
  `motor SAHIPSIZ` diyor. **Mimar/AI kapatamaz.**
- **K3 · HB dedektorunun uretime baglanmasi (R13 / T150):** artik yalniz "test yok"
  degil, **olculmus bir risk**: gercek pedde %0 isabet (D-295 §2). Baglama karari
  insandadir; olcum iyilesmeden baglamak fail-closed'i her karede tetikler.

## T2 - Sartname yeniden taramasi (§2.2 ve §6, `venv` + `fitz`)

`Ileri_Otonom_Sistemler_Tasarim_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf`
**30 sayfa · 56 418 karakter** -> `results/saha_zinciri_20260826/sartname_metin_20260826.txt`.
(Sabah 56 919 karakter yazilmisti; fark **metin birlestirme** farkidir, PDF ayni dosyadir.)

| Tarama bulgusu | Durum |
|---|---|
| §2.2.6 yuk tasima + yapisal butunluk | **ATLANMIS** -> R22 (insan/donanim) |
| §6.2 hazirlik 15 dk · "Takim Hazir" · mudahale **-100 ceza** + sure hazirliga eklenir | **KARSILANIYOR** - `comms/yks_gui.py:1985, :2001-2011, :1976` (`_ceza_ekle`). Sabahki tabloda R16 "yalniz gosterge + log" diyordu; **bayat**. |
| §6.2 tekrar firlatma: "sure durdurulmaz, 15 dk'ya dahil" | **KARSILANIYOR** - `yks_gui.py:1889 firlatma()` `if self.t_iha0: return` ile kronometreyi **yeniden baslatmiyor**; dugme de kilitleniyor. Tabloda yoktu, **davranis dogru**. Dogrudan tekrar-firlatma testi **YOK**. |
| §6.2/§6.4 IHA 15 dk · IKA 10 dk | **KARSILANIYOR** - R16 (T148) |
| §6.4 kirim / inis ihlali / alan ihlali / manuel mudahale | R17/R21/R9 - repo disi, degismedi |
| §6 "uc guzergah Kolay/Orta/Zor, farkli zorluk katsayisi" | Katsayi **acik olan** guzergaha aittir, bizim yayinladigimiza degil -> yeni yazilim gereksinimi **degil**. Yine de yayinlanan `road` etiketinin dogrulugu §2.2.3 hakem onayini ilgilendirir (T155/D-296 ile 15/15 oldu). |
| §6 agirlik limitleri (IHA 25 kg / IKA 10 kg), 3 ucus hakki, muhur | Insan/idari - yazilima dusmez |

**§6.2 hazirlik suresi kodda CIPLAK.** `comms/yks_gui.py` icinde `"15:00"` bes yerde
duz metin (`:494, :519, :1893, :2090, :2094`); `SARTNAME_HAZIRLIK_SURESI_S` diye bir sabit
**yok** (`grep` -> 0). IHA limiti sabitten geliyor ama **ekran metni** ondan turemiyor.
Madde 16 (ciplak sayi yok) acisindan acik kusur - bugun kod degistirilmedigi icin
duzeltilmedi, **kayda gecti** (D-297).

## T3 - Bugun itibariyla KRITIK kalanlar (sabahki 8 maddenin yerine)

1. **Gercek IKA motor surucusu yok** (R12 · T149) - **K2, insan/donanim.**
2. **HB uretime bagli degil ve olcum baglanmamasi gerektigini soyluyor** (R13 · T150) - **K3, insan.**
3. **Uretim karar yolu `analyze_path` hicbir kapida yok** (T156) - genel kapi da
   kuru kosu `rota_bul`u zorluyordu (D-297 §1) — **T160 ile kapandi (D-298 §5b):** halka 7'nin
   hukmu artik `analyze_path`ten gelir, tanisal yol hukmu ceviremez (8/8 mutasyon).
   **T156 (genel kapi kolu) hâlâ ayri bir istir.**
4. **v36 karar kararliligi v35'ten kotu** (R14 · D-295 §3) - geri alma **kullanici karari**.
5. **SiK seri hatti hic olculmedi** (R20) - donanim gerekiyor; UDP loopback kanit sayilmaz.
6. **`iha_inis_yayinci` icin Jetson calistirma yordami kilavuzda yok** (R10 kalan) -
   belge isi; `results/saha_zinciri_20260826/saha_gunu.md` adim 6 bunu EKSIK olarak tasiyor.
7. **T153 (ince beton serit cikarici) KAPALI kalir** - on kayit §13 benimseme kurali
   **saglanmadi** (v35 15 -> 14 dustu, D-291). `INCE_BETON_SERIT_ETKIN = False`
   (`codes/karar_sozlesmesi.py:870`). Kalan is **model tarafindadir**, esik oynatmak degil.

## T4 - Belge tutarsizliklari - bugunku hali

- `CONTRACTS.md §11.2` halka tablosu -> **bugun olcumle tazelendi** (bu gorev).
- `CONTRACTS.md §7` "uretim zincirinde inis sinyalini ureten yok" -> **bayat**;
  §7.1 ve §6.6 eklendi, halka 9 artik **GECTI**.
- `REVIEW_LOG D-105` "hedef_konumu SAHIPLENDI" <-> kuru kosu `SAHIPSIZ` celiskisi ->
  **hala acik**, ama artik D-295 §2 olcumuyle taraf tutuluyor: dedektor **var**,
  uretime **bagli degil**, ve bugunku isabetle baglanmamali.
- `results/t123/saha_gunu_kontrol_listesi.md` -> **BAYAT: v35/v34 diyor**, uretim **v36**
  (D-294). Bu gorevde **duzeltilmedi** (kapsam disi); `saha_gunu.md` bunu acikca uyariyor.

---

## 0. Koşulan kapılar (bu denetim için, kod değişmeden)

```
> O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -q
Ran 855 tests in 69.605s
OK (skipped=2)

> O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI

> O:\navitas-local-train\venv\Scripts\python.exe -B scripts/saha_kuru_kosu.py --atla-cikarim --cikti <scratch>
  kamera         GECTI      kaynak parametrik ve VideoCapture'a BESLENIYOR
  model_yukleme  GECTI      agirlik manifestten turetiliyor, --model besliyor
  cikarim        ATLANDI    --atla-cikarim verildi
  maske          ATLANDI    --atla-cikarim verildi
  olcek          DUSTU      OLCEK_YOK: kare icerik genisligi yok; canli olcek bu kare icin turetilemedi
  hedef_konumu   SAHIPSIZ   HB'nin tek kaynagi Gazebo meta.txt; saha kod yolunda --hb girisi yok ve etkin model profili 2 sinifli
  rota           ATLANDI    onceki halka dustu: maske
  aktarim        GECTI      saha paketi haberlesme kodunu ve gerekli API'yi tasiyor -> jetson_paket/kod/iha_sender.py
  surus_izni     GECTI      IHA_LANDED saha kod yolunda uretiliyor -> comms/iha_inis_yayinci.py:44
  motor          SAHIPSIZ   gercek motor surucusu yok; send_vel yalnizca gz subprocess'i
GECTI 4 · DUSTU 1 · SAHIPSIZ 2 · ATLANDI 3   KOPUK HALKALAR (3): olcek, hedef_konumu, motor
```
(`olcek DUSTU` kare olmadığı için beklenen sonuçtur; sahada canlı irtifa telemetrisi gerekir.)

## 1. Hüküm tablosu

| # | Şartname hükmü (alıntı) | Karşılayan kod / test (dosya:satır) | Kanıt | Risk | Önerilen iş |
|---|---|---|---|---|---|
| R1 | §2.1 "üç yoldan yalnızca bir tanesi açık bırakılacak… hangi yolun açık olduğu… gizli" | Üretim yolu: `codes/rpi_inference.py:1080 analyze_path` (en büyük bağlı bileşen + K-A uç-bant + A* tanık yol; `road` = darboğaz şeridi `:1099-1106`). Envanter yolu: `codes/costmap_path_finder.py:366 koridor_adaylari` yalnız `rota_bul:1025` içinden; `rpi_inference` `costmap`'ten yalnız `_bagli_mi` alıyor (`:38`). Testler: `tests/test_analyze_path_uc_bant.py`, `test_t119_yayinlanan_road_kapisi.py`, `test_koridor_etiketi.py` (koridor_adaylari), `codes/test_rota_sentetik.py` 15/15 (rota_bul). | KANITLI_TEST — ama **iki üretim yolu** var: Jetson `run_camera` → `analyze_path`; `iha_haritala`/`jetson_fps` → `rota_bul`. Sahada hangisi yayına gidiyor: BELİRSİZ | ÖNEMLİ | Tek karar yolu ilan et (CONTRACTS §11.2 halka 7 hâlâ `rota_bul:729` diyor, Jetson kodu `analyze_path` koşuyor). T79 (D-119/D-122 %3,46 kararsızlık) açık. |
| R2 | §2.2.2 "Fırlatma sonrası İHA, tam otonom uçuş moduna geçerek" | Repo'da uçuş kontrol yazılımı yok (`drone/` yalnız video yayını: `drone/rpi_yayin.py`; `grep IhaSender drone/` → boş). | ÖLÇÜLEMEDİ (Pixhawk/ArduPlane görev planı repo dışı) | KRİTİK (repo dışı) | Uçuş planı + geofence parametre dosyasını repoya kanıt olarak koy (`config/`); YKS `mod != AUTO` uyarısı var (`comms/yks_gui.py:917-921`) ama İHA'dan `mod` alanını üreten yok. |
| R3 | §2.2.2 "görüntü işleme algoritmaları vasıtasıyla HTAB içindeki açık olan güzergâhı tespit edecektir" | `codes/rpi_inference.py:1844-1878 run_camera` → `_preprocess` → `model.predict` → `get_masks` → `kare_olcek_kahini` → `analyze_path` → `_rota_kararini_esikle`. Model kaydı fail-closed `:578`. Testler: `test_rota_guven_esigi.py:120`, `test_rota_ret_nedenleri.py`, `test_zemin_kaplama_kapisi.py`, `test_olcek_uretim_baglantisi.py`, `test_rpi_canli_olcek.py`. | KANITLI_TEST | ÖNEMLİ | Ölçek halkası canlı irtifaya bağlı (kuru koşu `olcek DUSTU`); sahada Pixhawk `GLOBAL_POSITION_INT` gelmezse her kare `OLCEK_YOK` → NO_ROUTE. Sahaya çıkmadan `--mavlink` ile bir canlı ölçek koşusu kanıtı üret. |
| R4 | §2.2.3 "tespit ettiği güzergâh bilgisini kablosuz haberleşme… yer istasyonuna ve İKA'ya aktaracaktır" · §5.3.2 "uçuş esnasında gerçek zamanlı olarak YKİ'ye aktarmak" · §6.2 "gerçek zamanlı olarak YKS'ye aktarılmalı" | Kütüphane: `comms/iha_sender.py:104-131 send_open_route/send_no_route` (ACK'li 8 tekrar), `comms/protocol.py`. **Ama** üretim çıkarım döngüsü `codes/rpi_inference.py run_camera` hiçbir gönderici çağırmıyor: `grep -n "IhaSender\|send_open_route\|rota.json" codes/rpi_inference.py` → 0 (yalnız `:1708 print(payload)`). `iha_sender.py main:191-193`: `--ika/--serial` için `--rota-json` ZORUNLU; `rota.json`'ı yalnız `simulation/scripts/iha_haritala.py` üretiyor. Testler: kütüphane için `test_rota_guven_esigi.py:106 gercek_udp`, kuru koşu `aktarim GECTI` (yalnız paket içeriği + loopback). | **KOD_VAR_TEST_YOK** (entegrasyon): canlı tespit → telsiz köprüsü YOK | **KRİTİK** | `run_camera` (veya ayrı `iha_yayin.py`) analyze_path kararını her N karede `send_open_route`/`send_no_route` ile yayınlasın; test: sahte kamera + loopback UDP'de OPEN_ROUTE alınıyor. |
| R5 | §2.2.3 "alan hakemi, canlı olarak güzergâh bilgisinin tespit edildiğini onaylamalıdır" · §6.2 "monitör üzerinden izlenmeli… sözlü olarak onaylamalı" | `comms/yks_gui.py`: onay butonu 2 aşamalı `:388-398, :964-999`; harita üzerinde ref_xy + waypoint çizimi `:685-690`; NO_ROUTE sebebi kırmızı bant `:698-703`; canlı algı görünümü (üretimle aynı `analyze_path`) `:1491-1500, :1537, :1592`; güven-altı OPEN_ROUTE reddi ekranda `:931-962`; hakem künyesi model sha `_uretim_modeli_adi:100`. Testler: `test_yks_gui_rota_engel.py` (6), `test_rota_ret_nedenleri.py:267` (üç ret → üç farklı metin), `test_rota_guven_esigi.py:199`, `test_hakem_kunye_algi_hizasi.py`, `tests/t64_hakem_ekrani_kapisi.py`. | KANITLI_TEST — ekran: rota GÖRÜNÜR, ret sebebi GÖRÜNÜR, ACK ancak 2. onayda | KÜÇÜK | Sözlü onay insan işidir; ekran yeterli. Hakem günlüğünü dosyaya yazdığı doğrulanmalı (kanıt olarak). |
| R6 | §2.2.3 "alan hakemi tespit edilen güzergâh bilgisinin İKA'ya aktarıldığını onaylayacaktır" | YKS 2. onay `:976-999` yalnız İHA'ya ACK yollar. **YKS, İKA'nın rotayı ALDIĞINA dair hiçbir sinyal görmüyor**: İKA ACK'i yalnız gönderen adrese döner (`comms/ika_receiver.py:219-221`), İKA heartbeat üretmiyor (`grep heartbeat comms/ika_receiver.py simulation/scripts/ika_nav.py` → 0), YKS'de `"ACK"` işleyen tek yer demo iş parçacığı `:2022`. | BELİRSİZ — 2. onay hakemin gözlemine değil YKS operatörünün beyanına dayanıyor | ÖNEMLİ | İKA alıcısı ACK'i YKS akranına da göndersin (ya da İKA heartbeat'i `latest.seq` taşısın); YKS "İKA seq=N aldı" satırını 2. onay düğmesinin ön koşulu yapsın. |
| R7 | §2.2.3 "Bu aktarımın İHA havada iken tamamlanması gerekmektedir" | YKS: onay anında `t_iha1`/`iha_landed_seq` ile "inişten SONRA / zaman bilinmiyor / henüz inmedi" uyarısı `:983-991`; `iha_indi():1816-1818` uyarı. Test: `test_yks_gui_aktarim_zamani.py` (3 test). | KANITLI_TEST (yalnız UYARI; zorlama yok — doğası gereği) | KÜÇÜK | — |
| R8 | §2.2.3 aktarımın tamamlanması: **IKA_GO ACK** (CONTRACTS §7 notu) | `comms/yks_gui.py:1761-1781 _cmd_gonder`: tek `link.send`, ACK beklemiyor, tekrar yok. `ika_baslat:1822-1843`: gönderim başarılıysa `t_ika0` set ve buton `disabled` → **kaybolan tek UDP paketi sonrası operatör bir daha basamaz**. Alıcı tarafı ACK üretiyor (`ika_receiver.py:260 _kontrol_mesaji_ack`) ama YKS okumuyor. `REVIEW_LOG D-02` hâlâ açık; CONTRACTS §7 notu geçerli. Test: `test_ika_go_gate.py` (9) kapıyı sınar, tekrar/ACK'i sınamaz. | KOD_VAR_TEST_YOK (ACK yarısı var, bekleyen yok) | **KRİTİK** | `_cmd_gonder("IKA_GO")` → `IhaSender._tekrarli_gonder` kalıbıyla ACK'e kadar tekrar; ACK gelmezse buton yeniden açık + kırmızı log. Test: alıcı ilk paketi düşürür, ikinci tekrarla latch açılır (mutasyon: tekrar kaldırılınca düşer). |
| R9 | §2.2.4 "Paraşüt açma komutu otonom… manuel tetikleme… ceza" | YKS manuel tetik `comms/yks_gui.py:1895 parasut` (CMD → iha, ceza −50 kaydı; `test_yks_gui_komut_durustlugu.py:127-140`). Otonom tetik: repo dışı. İHA'da CMD tüketen kod yok (`drone/` protokol kullanmıyor). | ÖLÇÜLEMEDİ (otonom) · BELİRSİZ (manuel komutun İHA'da alıcısı yok) | ÖNEMLİ | Paraşüt otonom tetiği uçuş kontrolcüsünde; YKS `PARASUT` komutunun gerçek bir alıcısı yoksa ekrandan kaldır veya MAVLink'e bağla. |
| R10 | §2.2.5 "İHA yere temas etmeden İKA hareket edemez… iniş yapmadan harekete geçen… başarısız" | Kapı: `comms/ika_receiver.py:119-121, :129 _surus_izni_gecerli_unlocked` (`ika_go ∧ iha_landed`), `run_if_route_valid:78-92`; `simulation/scripts/ika_nav.py:213-222 receiver_rota_gecerli`; YKS kilidi `yks_gui.py:1826-1834`. **Üretici (iniş sinyali): `comms/iha_inis_yayinci.py:44 iha_inisini_yayinla` ← `main:126-151` → `comms/inis_kaniti.py:329 yerde_mi`** = Pixhawk `EXTENDED_SYS_STATE.landed_state == ON_GROUND` ardından `GLOBAL_POSITION_INT.relative_alt < 1 m`, aynı sysid, ardışık 3 çift, mutlak deadline; sonra `send_iha_landed` ACK'li. Manuel "İHA İNDİ" düğmesi latch'i AÇMAZ (`test_iha_landed_gate.py:313`). Testler: `test_iha_landed_gate.py` (12), `test_inis_kaniti.py` (25), `test_iha_inis_yayinci.py` (13), `test_saha_kuru_kosu.py:150`; kuru koşu `surus_izni GECTI`. | KANITLI_TEST | ÖNEMLİ (kalan) | **CONTRACTS §7 notu ("üretim zincirinde iniş sinyalini üreten yok") BAYAT — güncelle.** Kalan boşluk: `iha_inis_yayinci.py`'yi Jetson'da KİM, NE ZAMAN başlatıyor? `JETSON_KILAVUZ.md` yalnız `cp` satırı (`:297`), çalıştırma komutu/servis yok. `pymavlink` paket gereksiniminde var (`jetson_paket/kod/requirements_rpi.txt`). |
| R11 | §2.2.5 "İKA'nın intikal süreci YKS'de görevli takım üyesi tarafından manuel olarak tetiklenir" | `yks_gui.py:1822 ika_baslat` → `CMD IKA_GO hedef=ika`; alıcı `ika_receiver.py:245-263` latch. Test: `test_ika_go_gate.py:51` gerçek UDP çiftinde IKA_GO öncesi hareket yok / sonrası var. | KANITLI_TEST | — | R8'e bağlı. |
| R12 | §2.2.5 "İKA; otonom olarak açık olan güzergâhı takip ederek HB'ye ilerleyecektir" · "Otonom hareket etmeyen İKA'nın görevi başarısız" · §2.2.6 "HB sınırları içerisine girmesi" | Navigasyon: `simulation/scripts/ika_nav.py:290 navigate` (waypoint takip, `send_vel:90` = `gz topic` subprocess). Gerçek sürücü (seri/PWM/GPIO/MAVLink): `grep -n "Serial|GPIO|pwm|pixhawk|mavlink" ika_nav.py` → 0. Kuru koşu: `motor SAHIPSIZ`. CONTRACTS §11.1/1: `simulation/` sahip olamaz. | **YOK** (gerçek sürücü) | **KRİTİK** | İKA donanım arayüzü kararı (Jetson→motor sürücü) + `send_vel` arka ucu soyutlaması + kuru koşuda "çağrı sayan sahte sürücü"nün gerçek sürücüye bağlanması. Donanım gelmeden kapanmaz. |
| R13 | §2.2.6 "HB'ye… kırmızı H… 2×2 m" — varış noktası HB | HB dedektörü var: `codes/karar_sozlesmesi.py:754 hb_maskesi`, `:811 hb_konumu`, `:1271 hedef_yok_reddi`; `analyze_path` `goruntu=` verilirse HB'yi A* hedefi yapıyor `codes/rpi_inference.py:1281-1371`. **Üretim çağrı yerlerinin HİÇBİRİ `goruntu=` geçirmiyor**: `rpi_inference.py:1668, :1771, :1862` ve `yks_gui.py:1491` → `grep -c "goruntu=" codes/rpi_inference.py` = 1 (yalnız imza `:1165`), `comms/yks_gui.py` = 0. Yani `hb_maskesi` üretimde HİÇ çağrılmıyor, `HEDEF_YOK` hiç üretilmiyor, rota hedefi hâlâ **üst bant**. Kuru koşu bunu `hedef_konumu SAHIPSIZ` diye raporluyor (ölçütü `--hb` CLI veya 3 sınıf; `hb_konumu`'nu saymıyor). D-105 "sahiplendi" ile çelişiyor. Testler: `test_hb_dedektoru.py` (25 birim), entegrasyon yok. | **KOD_VAR_TEST_YOK** (üretime bağlı değil) | ÖNEMLİ | (1) Gerçek arena/DJI karelerinde `hb_konumu` isabetini ÖLÇ (yanlış-negatif oranı bilinmeden bağlamak her kareyi HEDEF_YOK'a düşürebilir); (2) ölçüm iyiyse `run_camera`/`yks_gui` çağrılarına `goruntu=bgr` ekle; (3) `saha_kuru_kosu.halka_hedef` ölçütünü `hb_konumu` ile hizala; (4) HB dünya koordinatı İKA'ya `OPEN_ROUTE.waypoints[-1]` olarak gitsin. |
| R14 | §5.3.2 "yanlış güzergah tespiti yapan takımlar 0 puan" · §6.2/§6.4 "doğruluğu teyit edilemeyen… geçersiz" → fail-closed | `codes/karar_sozlesmesi.py rota_guven_reddi`, `rota_olcek_reddi`, `zemin_maskesi_reddi`, `rota_koridor_genisligi_reddi`; `rpi_inference.py:1360 _rota_kararini_esikle` (eşik altı → yol None, wp boş); K-A uç bant `:1305-1320`; `iha_sender.py:111-114` son savunma (eşik altı → NO_ROUTE); `yks_gui.py:931` eşik altı OPEN_ROUTE'a ACK yok; `ika_receiver` NO_ROUTE `latest`'i ezmez ama sürüşü keser `:78-92`. Testler: `test_rota_guven_esigi.py` (8), `test_rota_ret_nedenleri.py` (10), `test_koridor_genisligi.py`, `test_zemin_kaplama_kapisi.py`, `test_t141_rota_yoksa_surme.py`, `test_ika_surus_no_route.py`. | KANITLI_TEST | ÖNEMLİ (kalan: kararlılık) | T79 açık: `.pt`/`.onnx` aynı karede farklı koridor (D-119/D-122). Yayın öncesi N-kare çoğunluk/kararlılık filtresi yok (`run_camera` her kare bağımsız karar). |
| R15 | §5.3.2 "asgari 30 metre irtifadan… 20×20 metre test alanı" | `CONTRACTS §8` imgsz 640 sabit, 30 m'de kaplama ölçümü; T14 `[IN_PROGRESS: Codex-1]` (`TASK_QUEUE.md:1883`). | BELİRSİZ | ÖNEMLİ | T14/T15 kapanmadan FDA irtifasında tek kare kanıtı yok; DJI 30 m çekimleri (`data/dji_prova`) ile ölçüm. |
| R16 | §5.3.2 "tüm operasyon… maksimum 10 dakika" · §6.2 İHA 15 dk · İKA 10 dk · hazırlık 15 dk · §7 t_İHA, t_İKA, t_hazırlık | YKS kronometreleri `yks_gui.py:183-184 IHA_LIMIT=900, IKA_LIMIT=600`, hazırlık `:1867-1976` (yalnız gösterge + log). İKA 600 s kesmesi: yalnız sim `navitas_sim.py:102-119 deadline`; `ika_nav.navigate` sahada süre sınırı yok (D-05 açık). `mission_time.py` sim. | KOD_VAR_TEST_YOK (YKS kronometre testi yok; İKA kesme sim'de) | KÜÇÜK | T15 (FDA bütçesi uçtan uca ölçümü) açık. Süre aşımı zaten hakemde; yazılım kesmesi puan kurtarmaz. |
| R17 | §6.2 "İHA-UB sınırları içinde… Alan İhlali" | YKS heartbeat `x,y` ile 300×300 uyarısı `yks_gui.py:922-926` — ama İHA'dan `x,y` üreten üretim kodu yok (yalnız demo `:2013`). Geofence: Pixhawk parametresi, repo dışı. | ÖLÇÜLEMEDİ | ÖNEMLİ (repo dışı) | Uçuş kontrolcüsü geofence parametrelerini kanıt olarak repoya ekle. |
| R18 | §6.2 "fırlatma/başlangıçtan görev bitimine… tam otonom (seyrüsefer, tespit, veri aktarımı, sürüş)" | Tespit: otonom (R3). Aktarım: `iha_sender.py` CLI elle, `--rota-json` ister (R4) → otonom DEĞİL. Sürüş: R12. | YOK (aktarım ve sürüş otonom zinciri) | KRİTİK | R4 + R12. |
| R19 | §6.4 "veri akışının sağlanamadığı durumlarda uçuş geçersiz" · bağlantı kaybı | `ika_receiver.py:265-276 poll` `hb_timeout` → `link_lost` → güvenli duruş; `iha_sender.py:133 send_heartbeat`; `iha_inis_yayinci.py:58-59` iniş sonrası heartbeat sürer. Testler: `test_iha_landed_gate.py:374, :403`, `test_ika_no_route_recovery.py`. | KANITLI_TEST | KÜÇÜK | — |
| R20 | §2.2.3 "kablosuz haberleşme" — SiK seri hattı | `comms/link.py SerialLink`; `pyserial` gereksinimde; `test_iha_inis_yayinci.py:97, :190` sahte seri. Protokolde CRC/checksum yok (`navitas-derin-analiz-build/10_PDF_SARTNAME_DDR_UYUMU.md`); bozuk JSON satırı atılıyor (`protocol.py:149`). Gerçek SiK üzerinde uçtan uca ölçüm: yok. | KOD_VAR_TEST_YOK (gerçek telsiz) | ÖNEMLİ | Gerçek SiK çifti ile OPEN_ROUTE/IKA_GO/IHA_LANDED tur süresi ve kayıp oranı ölçümü (DDR'deki ">%98, 300 m" iddiasının kanıtı yok). |
| R21 | §6.4 "Güvenlik Pilotu… manuel moda alması → başarısız" | YKS `mod != AUTO` uyarısı `yks_gui.py:917-921`; üreten yok (R2). | BELİRSİZ | KÜÇÜK | — |

## 2. Görevde özellikle sorulanlar — kısa cevaplar

- **§2.2.3 hakem canlı onaylar:** ekran rota polyline + ref_xy çiziyor (`yks_gui.py:685-690`), ret sebebini kanonik kodla gösteriyor (`:698-703`, `:931-962`), ACK ancak 2. onayda (`:976-982`). KANITLI_TEST.
- **Aktarım İHA havadayken — ACK var mı?** OPEN_ROUTE/NO_ROUTE/IHA_LANDED ACK'li ve tekrarlı (`iha_sender.py:80-102`). **IKA_GO ACK'siz ve tek atış** (`yks_gui.py:1761-1781`), buton gönderim sonrası kalıcı kapanıyor (`:1838-1843`). CONTRACTS §7 "IKA_GO ACK'siz" notu **hâlâ geçerli**; D-02 açık.
- **§2.2.5 iniş sinyalini üreten kim?** `comms/iha_inis_yayinci.py` (Pixhawk kanıtı `inis_kaniti.yerde_mi`). CONTRACTS §7 "üretim zincirinde iniş sinyalini üreten yok" notu **artık geçersiz/bayat** — kuru koşu `surus_izni GECTI -> comms/iha_inis_yayinci.py:44`. Kalan: Jetson'da bu süreci başlatan runbook/servis yok.
- **HB'ye varış — `hb_maskesi` üretim yolunda çağrılıyor mu?** **HAYIR.** Yalnız `analyze_path(goruntu=...)` verilince (`rpi_inference.py:1366-1367`); üretim çağrılarının hiçbiri `goruntu` geçirmiyor (grep sayımı: rpi_inference 1 = imza, yks_gui 0). Kuru koşu `hedef_konumu SAHIPSIZ`.
- **3 güzergâhtan açık olanın seçimi:** üretim (`run_camera`) `analyze_path` = en büyük bağlı bileşen + iki uç bant teması; `koridor_adaylari` yalnız `rota_bul` içinde (sim/`jetson_fps`). İki yol arasındaki seçim BELİRSİZ; T79 kararsızlığı açık.
- **Yanlış güzergâh = 0 puan, fail-closed nerede:** `_rota_kararini_esikle` (`rpi_inference.py:1360`), K-A (`:1305`), `rota_guven_reddi`, `iha_sender.send_open_route:111`, `yks_gui._open_route_guven_reddini_goster:931`, `ika_receiver.run_if_route_valid:78`. KANITLI_TEST.

## 3. KRİTİK boşluklar — önem sırası (en fazla 8)

1. **Canlı tespit → telsiz köprüsü yok** (R4/R18). `run_camera` yayın yapmıyor; `iha_sender` CLI sim `rota.json` istiyor. Sahada hakem ekranına HİÇBİR şey gitmez → §6.4 geçersiz. *Bu gece:* **EVET** — `run_camera` karar → `IhaSender.send_open_route/send_no_route` çağrısı + loopback testi; ölçek halkası canlı irtifaya bağlı kalır.
2. **IKA_GO tek atış, ACK'siz, buton kalıcı kapanıyor** (R8, D-02). Tek UDP/SiK kaybı = İKA hiç başlamaz, P_görev=0. *Bu gece:* **EVET** — `_tekrarli_gonder` kalıbı + ACK'siz butonu yeniden aç; mevcut `test_ika_go_gate` üzerine düşürücü test.
3. **Gerçek İKA motor sürücüsü yok** (R12). `send_vel` yalnız `gz`. *Bu gece:* **HAYIR** — donanım arayüzü kararı gerekir; sürücü soyutlaması (arayüz + sahte) yazılabilir.
4. **HB dedektörü üretime bağlı değil; rota hedefi üst bant, HB konumu İKA'ya gitmiyor** (R13). *Bu gece:* **KISMEN** — önce gerçek karelerde `hb_konumu` isabet ölçümü (yarım saat), iyiyse `goruntu=bgr` bağlantısı; ölçümsüz bağlamak fail-closed'ı her karede tetikleyebilir.
5. **YKS, İKA'nın rotayı aldığını görmüyor** (R6): 2. hakem onayı kanıtsız. *Bu gece:* **EVET** — İKA ACK/heartbeat'i YKS'ye yansıt, 2. onayı buna koşulla.
6. **`iha_inis_yayinci` için Jetson başlatma yordamı yok** (R10 kalan). Kod ve test var, runbook yok; uçuş günü kimse başlatmazsa latch açılmaz. *Bu gece:* **EVET** — `JETSON_KILAVUZ.md`'ye komut + kuru koşuya "süreç tanımlı mı" probu.
7. **Ölçek (mpp) halkası sahada ölçülmedi** (R3): canlı Pixhawk irtifası olmadan her kare `OLCEK_YOK`. *Bu gece:* **HAYIR** — Pixhawk/telemetri gerekir; sahte MAVLink ile yalnız yordam sınanır.
8. **Karar kararlılığı yok** (R14, T79): kare başına bağımsız karar, `.pt`/`.onnx` %3,46 ayrışma. *Bu gece:* **KISMEN** — N-kare çoğunluk filtresi küçük iş, ama eşik/kural CONTRACTS değişikliği ister → yalnız ÖNERİ.

## 4. Belge tutarsızlıkları (kod değil, metin)

- `CONTRACTS.md §7`: "üretim zincirinde iniş sinyalini üreten yok" → bayat (R10). "IKA_GO ACK'siz" → hâlâ doğru.
- `CONTRACTS.md §11.2` halka 6 `SAHİPSİZ`/halka 9 `KUSURLU`/halka 8 `SAHİPSİZ`: kuru koşu bugün `surus_izni GECTI`, `aktarim GECTI` (paket içeriği), `hedef_konumu SAHIPSIZ`. Tablo elle güncellenmez deniyor; `ozet.json` ile hizalanmalı.
- `REVIEW_LOG D-105` "hedef_konumu halkası SAHİPLENDİ" ↔ kuru koşu `SAHIPSIZ` ↔ üretimde `goruntu=` geçilmiyor: üçü birden doğru olamaz.

## ÖLÇÜLEMEDİ

- Uçuş kontrolcüsü (otonom uçuş, geofence İHA-UB, otonom paraşüt) — repo dışı.
- Gerçek SiK 433 MHz üzerinde paket kaybı/tur süresi.
- Sahada canlı `mpp` (Pixhawk irtifası) ve 30 m'de HB tespiti isabeti.
- Gerçek İKA sürüşü (donanım yok).
- `rpi_inference` ile `rota_bul` yollarından hangisinin Jetson'da yayına bağlanacağı (bugün ikisi de bağlı değil).
