# ÖN KISIM — Kapak · Versiyonlar · Tanımlar ve Kısaltmalar

> Yönergenin **puanlanan bölümlerden önce** gelen zorunlu kısmı
> (`FDR_2_qNiVF.pdf` s. 1–6). Haritadaki kimlikler: `Y-0-M01…M05`.
>
> ⚠ **Metin çıkarımı uyarısı.** `results/fdr_sablon/fdr_yonerge_metin.txt`
> dosyasında yazı tipi bağ-imi (ligature) yüzünden bazı `i` harfleri `g`
> olarak çıkmıştır ("Değerlendgrme", "glgşkgn"). Aşağıdaki kısaltma listesi
> **PDF sayfalarının kendisinden** okunmuştur, çıkarılmış metinden değil.
> Bu satırları çıkarılmış metinden kopyalamayın.

---

## Y-0-M01 · Kapak sayfası

```
              İLERİ OTONOM SİSTEMLER TASARIM VE
                    OPERASYON YARIŞMASI

            FİNAL DEĞERLENDİRME RAPORU (FDR)


   TAKIM ADI   : Navitas Autonomous Systems
   TAKIM ID    : 997827
   BAŞVURU ID  : 5329027
   RAPOR TARİHİ: 14.09.2026

                                                             2026
```

**Kapak tarihi ve yıl — kaynak ve kanıt sınıfı (13.09.2026 eklendi).**
Künye alanlarının ardından gelen **yıl** yönergenin kendi kapak düzeninden
gelir: `results/fdr_sablon/fdr_yonerge_metin.txt:7` kapak satırı
"TAKIM ADI:  TAKIM ID: BAŞVURU ID:                    2026"
(kaynak `FDR_2_qNiVF.pdf` s. 1).

**RAPOR TARİHİ = 14.09.2026** — **güncel FDR son teslim tarihi.** Organizasyon takvimi
**erkene çekmiştir**; kaynak: kaptan beyanı (13.09.2026, D-477) — etiketi **BEYAN**.
**Uçuş tarihi: 21.09.2026** (kaptan beyanı, D-471 ve D-477).

⚠ **Eski takvim geçersiz.** Repodaki şartname metni ilk yayımlanan takvimi taşır:
~~FDR son teslim 21.09.2026 – 17.00~~ · ~~Görev Test Uçuşu 30.09–03.10.2026~~
(`results/sartname_bosluk/sartname_metin.txt:355, :362`). Değişiklik duyurusu repoya
eklendiğinde (T269) `tests/test_fdr_takvim_kapisi.py` yeni takvime bağlanacaktır.

⚠ **DOĞRULANACAK (kaptan):** Bu üç alan `navitas-teknofest/references/
ddr_requirements.md` içinden, **DDR döneminde** alınmıştır. KYS (Kayıt Yönetim
Sistemi) kaydıyla teyit edilmeden nihai sayılmaz. ~~Yönerge kapağında alan adı
**"BAŞVURU ID"**dir; bizim DDR belgemizde "başvuru no" yazıyor — teyitte bu da
kontrol edilecek.~~ → **Alan adı alt kalemi KAPANDI (13.09.2026):** kapakta
yönergenin kendi yazdığı ad kullanılır —
`results/fdr_sablon/fdr_yonerge_metin.txt:7` kapak satırı
"TAKIM ADI:  TAKIM ID: BAŞVURU ID:" (kaynak `FDR_2_qNiVF.pdf` s. 1). DDR
belgemizdeki "başvuru no" yalnızca bir **adlandırma farkıdır**, sayı değerini
değiştirmez.

**Kanıt sınıfı: BEYAN (ölçüm değil).** Üç alan da repodaki **tek kayıtlı
kaynaktan** alınmıştır: `navitas-teknofest/references/ddr_requirements.md:10`
("ID: 997827 | Başvuru: 5329027") ve `navitas-teknofest/SKILL.md:20`. Kayıt
**DDR dönemine** aittir. Ölçüm (13.09.2026): `grep -rn '997827\|5329027'`
repoda **KYS ekranından alınmış hiçbir kanıt dosyası bulmadı** — dönen her
satır bu tek kayıttan türeyen belgelerdir (ana ağaçta `BOLUM_2:10`,
`ACIK_KALEMLER_HAM.md`, worktree kopyaları). Künye **ölçümle veya hesapla
türetilemez**; harici bir kayıt sorgusudur. Bu nedenle sayılar yukarıdaki
haliyle rapora girer; açık olan kalem değerin kendisi değil, dış kayıtla
**teyididir**.

**Doğrulama sahibi ve zamanı — kalem AÇIK.** KYS künye teyidi **kaptana**
zimmetlidir (`FDR/ACIK_KALEMLER.md:121`, kalem 43); en geç **14.09.2026 teslim
dizgi koşumundan önce** yapılır (güncel FDR son teslim 14.09.2026, D-477). Teyit bir sapma gösterirse yapılacak tek işlem bu üç
satırın güncellenmesidir; künye raporun başka hiçbir yerinde hesaba girmez, bu
yüzden dizgi bu kalem beklenerek geciktirilmez.

**BEYAN GEREKLİ (insan):** Kapakta kullanılacak takım logosu / görseli (varsa).

**ÖLÇÜLDÜ (13.09.2026) — repoda takım logosu YOK.**
`find . -iname "*logo*" -not -path "./.git/*"` (derinlik **sınırsız**) tek
eşleşme döndürdü: `.venv/Lib/site-packages/matplotlib/mpl-data/sample_data/logo2.png`
— üçüncü parti örnek dosyasıdır, takım logosu değildir. `FDR/sekiller/`
altındaki **30 dosyanın** (14 SVG · 5 `.mmd` · 4 PNG · 7 açıklama `.md`)
tamamı akış, bağlantı, organizasyon ve simülasyon çizimidir (`akis_a…e.svg`,
`iha_baglanti.svg`, `ika_baglanti.svg`, `organizasyon.svg`, `sim_*.svg/png`,
`uygunluk_pasta.svg`, `uygunluk_yontem.svg`). Yönerge kapağı logo **zorunlu
kılmaz**: kapak satırında yalnız TAKIM ADI / TAKIM ID / BAŞVURU ID ve yıl
vardır (`results/fdr_sablon/fdr_yonerge_metin.txt:7`).

⚠ **Ölçüm karar değildir.** "Logo dosyası repoda yok" bir **ölçümdür**;
"kapak logosuz basılır" bir **karardır** ve CLAUDE.md md. 9 uyarınca insana
aittir — kaptanın beyanı beklenmektedir (`FDR/YONERGE_HARITASI.md:216`,
`FDR/ACIK_KALEMLER.md:121`). Beyan gelmezse dizgi bu kalem yüzünden
**bekletilmez**; logo teslim edilirse dosya `FDR/sekiller/logo.svg` olarak
eklenir ve kapağın üst ortasına basılır.

---

## Y-0-M02 · Versiyonlar

| VERSİYON | TARİH | AÇIKLAMA |
|---|---|---|
| V 1 | 03.09.2026 | İlk taslak — yönerge iskeletine taşındı, ölçülmüş içerik bağlandı |
| V 1.1 | 07.09.2026 | İlk tam dizgi koşuldu — `FDR/pdf/FDR_TAM_TASLAK_20260907.pdf` **271 sayfa**; yazılım kolu ayrı çıktı **166 sayfa** |
| V 1.2 | 10.09.2026 | Yazılım kolu genişletildi — `FDR/pdf/FDR_YAZILIM_KOLU_20260910.pdf` **198 sayfa** (07.09 sürümünde 166 idi) |
| V 1.3 | 12–13.09.2026 | Atölye test günü sonuçları işlendi — **A1/A3/A4/A5 GEÇTİ · A12 hover (GUIDED, kodla, 15 s / 3 m) + kodla LAND başarılı · A2 kısmi · A6 ÖLÇÜLDÜ ve DÜŞTÜ (13.09, D-476) · A9/A9-ek/A10/A11/A13 ÖLÇÜLMEDİ**; `config/pixhawk/emir.param` kart dökümü içeriğe bağlandı |
| V n | **BEYAN GEREKLİ (insan)** | teslim sürümünün numarası ve tarihi — kaptan beyanı bekleniyor |

**BEYAN GEREKLİ (insan) — AÇIK kalem.** Teslim edilecek sürümün numarası ve
tarihi (14.09.2026 teslimi `V n` olarak buraya eklenecek). Bu kalem **yalnız
kaptan beyanıyla** kapanır; bir AI'ın ara sürüm satırı eklemesi onu kapatmaz
(CLAUDE.md md. 9). Ara sürümler bu tabloya satır olarak eklenir; **satır
silinmez**.

**Takvim (D-477).** Güncel FDR son teslim **14.09.2026**, uçuş **21.09.2026** — ikisi de
kaptan beyanı (organizasyon takvimi erkene çekti). Şartname metnindeki ilk takvim
(~~21.09.2026 – 17.00~~ / ~~30.09–03.10.2026~~) geçersizdir.

**Sürüm satırlarının kanıtı.** V 1.1–V 1.3 numaraları **geriye dönük**
verilmiştir; dayanakları ölçülmüş türev çıktılardır — sayfa sayıları
13.09.2026'da `pypdf` ile sayıldı (271 / 166 / 198), tarihler `FDR/pdf/` dosya
damgalarıdır (07.09.2026 03:31 ve 10.09.2026 17:15). V 1.3'ün dayanakları:
12.09.2026 atölye günü (**kullanıcı beyanı** — A1–A5 ve A12 için ham `.bin`
log dosyası repoda **yoktur**; A12'nin logu SD karttan silinmiştir, tek
bağımsız kanıt `config/pixhawk/emir.param:980` `STAT_FLTTIME,273`), 13.09.2026
A6 ölçüm dosyaları (`results/atolye_20260912/A6_sik_ikago.json`,
`A6_sik_parasut.json`) ve 12.09.2026 23:55 alınan `emir.param` kart dökümü.
⚠ `results/atolye_20260912/SONUC_SABLONU.md` hücreleri **doldurulmamıştır**
(A6 sat. 13, A11 sat. 18, A13 sat. 20 — "[ ] ÖLÇÜLDÜ" kutuları işaretsiz);
A6'nın ölçüldüğü şablondan değil, ölçüm dosyalarının kendisinden bilinmektedir.

---

## Y-0-M03 · Tanımlar ve Kısaltmalar

### Yönergede tanımlananlar (birebir, s. 5–6)

| kısaltma | tanım |
|---|---|
| **DDK** | Danışma ve Değerlendirme Kurulu |
| **İHA** | İnsansız Hava Aracı |
| **İKA** | İnsansız Kara Aracı |
| **HTAB** | Hedef Tespit Alan Bölgesi |
| **İHA-FB** | İHA Fırlatma Bölgesi |
| **İHA-UB** | İHA Uçuş Bölgesi |
| **İKA-KB** | İKA Konumlanma Bölgesi |
| **HB** | Hedef Bölge |
| **İHA-İB** | İHA İniş Bölgesi |
| **ÖDR** | Ön Değerlendirme Raporu |
| **DDR** | Detay Değerlendirme Raporu |
| **FDR** | Final Değerlendirme Raporu |
| **FDA** | Final Değerlendirme Aşaması |
| **FDS** | Final Değerlendirme Sunumu |
| **SGGS** | Sistem Gözden Geçirme Sunumu Teslimi |
| **UHDR** | Uçuşa Hazırlık Değerlendirme Raporu |
| **K_zorluk** | Zorluk Katsayısı |
| **m_İHA** | İHA Hafiflik Puanı |
| **t_İHA** | İHA Görev Süresi Puanı |
| **t_hazırlık** | Hazırlık Süresi Puanı |
| **m_İKA** | İKA Hafiflik Puanı |
| **m_yük** | İKA Yük Puanı |
| **t_İKA** | İKA Görev Süresi Puanı |
| **P_görev** | Görev Başarısı |
| **P** | Katılım Başarısı Puanı |
| **P_TI** | Teknik Muayene Başarı Puanı |
| **P_uçuş** | Uçuş Başarı Puanı |
| **P_centilmenlik** | Centilmenlik Başarı Puanı |
| **C_ceza** | Ceza Puanı |

### Bu raporda kullanılan ek kısaltmalar (takım tanımı)

Yönergedeki listeye ek olarak, raporun teknik bölümlerinde şu kısaltmalar
geçmektedir. Hepsi bu takımın kendi teknik terimidir; **yönergeden gelmez**
ve bir hüküm ifade etmez.

| kısaltma | tanım | nerede geçer |
|---|---|---|
| **YKS** | Yer Kontrol İstasyonu — hakem ekranı yazılımı (`comms/yks_gui.py`) | 3.3, 4 |
| **ACK** | Onay çerçevesi; `ref` (sıra no) ve `ref_tip` (hangi mesaja ait) taşır | 3.3, 4 |
| **OPEN_ROUTE / NO_ROUTE** | Açık güzergâh bulundu / bulunamadı kararı | 3.3, 4 |
| **IHA_LANDED** | İniş kanıtı çerçevesi (MAVLink `EXTENDED_SYS_STATE` kaynaklı) | 3.3, 4 |
| **HEARTBEAT** | Hat canlılık çerçevesi; `karar_yas` (algı kararının yaşı) taşır | 3.3, 4 |
| **K0…K8, K5A** | Karar zinciri kabul kapıları (sentetik arena, n=260) | 3.3, 4, 6 |
| **SiK** | 433 MHz telemetri radyo bağlantısı | 3.3 |
| **HB dedektörü** | Hedef Bölge (kırmızı branda) tespit modülü | 3.3 |
| **D-NNN** | Bu projenin kanıt defteri kaydı (`REVIEW_LOG.md`) | her yerde |
| **Ön kayıt** | Ölçüm eşiğinin **sonuç görülmeden** yazıldığı belge | 4, 6 |
| **Mutasyon kontrolü** | Kodu bilerek bozup testin düştüğünü doğrulama | 4 |
| **RTSP** | *Real Time Streaming Protocol* — video akışının ağ üzerinden çekilmesi. **PLANLANAN YOL, ÖLÇÜLMEDİ (T255 AÇIK):** kumandada HDMI portu bulunmadığı için yakalama kartı yolu düşmüştür; YKS köprüsünün **yer biriminden (192.168.144.12 ağı)** doğrudan RTSP çekmesi planlanmaktadır (`TASK_QUEUE.md:9744`, T255, durum `[ ]`). ⚠ `rtsp://192.168.144.25:8554/main.264` adresi **HDMI giriş dönüştürücüsünün** varsayılanıdır, yer biriminin değil (`jetson_paket/gosterici/GOSTERICI_KURULUM.md:55`). `kamera_koprusu`nun RTSP kaynağını desteklediği ve camdan cama gecikme (A11) **ÖLÇÜLMEDİ** | 3.3, 4 |
| **NVENC** | NVIDIA donanım video kodlayıcısı. **Jetson Orin Nano'da yoktur**; RTSP akışı yazılımla (x264) kodlanır — kaynak NVIDIA Jetson Linux r36.2 "Software Encode in Orin Nano" (`results/fdr_sprint_20260910/H9_MK15/TASARIM.md:17`). Etiket: **ÜRETİCİ_VERİSİ** | 3.3 |
| **MK15** | SIYI MK15 el kumandası + hava/yer birimi seti; video ve telemetriyi `192.168.144.x` ağı üzerinden taşır (sabit IP'ler: `.11` hava, `.12` yer, `.20` Android) — `results/fdr_sprint_20260910/H9_MK15/TASARIM.md:15` | 3.3 |
| **A1…A13** | 12–13 Eylül atölye test günü adım numaraları (A1 RC failsafe → LAND … A6 SiK RTT/kayıp/veri hızı … A12 hover logu); adım tanımları `ATOLYE_TEST_GUNU_20260912.md:49–201` | 4 |
| **p50 / p95** | Ölçüm dağılımının ortancası ve %95 dilimi; FPS ve gecikme sayıları bu iki dilimle verilir (ör. Jetson Orin Nano `.pt` **1,353 FPS p50** — `results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json`, `fps_p50_tabanli`) | 3.3, 4 |
| **STAT_FLTTIME** | ArduCopter kümülatif uçuş süresi sayacı (saniye); `config/pixhawk/emir.param:980` = **273 s** — A12 uçuşunun kart üstündeki tek bağımsız kanıtı (`.bin` logu SD karttan silinmiştir) | 4 |

⚠ **Karışmasın:** yönergedeki **FDA** = *Final Değerlendirme Aşaması*. Bu raporun
teknik bölümlerinde `--fda` bir **yazılım bayrağıdır** ve şartname §5.3.2 "Drone
ile Görev Test Uçuşu" görev kipini açar. Aynı harfler, farklı şeyler.

---

## Y-0-M04 · İçindekiler

| bölüm | konu | puan | sayfa (07.09 taslak dizgisi) | dosya |
|---|---|---|---|---|
| — | Kapak · Versiyonlar · Tanımlar ve Kısaltmalar | — | 1–4 | `BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` |
| **1** | Özet | 5 | 5–17 | `BOLUM_1_OZET.md` |
| **2** | Organizasyonel Yapı ve Proje Takvimi | 5 | 18–39 | `BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` |
| **3** | Genel Sistem Spesifikasyonları | **40** | 40–116 | `BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` |
| **4** | Test Faaliyetleri | 15 | 117–167 | `BOLUM_4_TEST_FAALIYETLERI.md` |
| **5** | Üretim Faaliyetleri | 15 | 168–189 | `BOLUM_5_URETIM_FAALIYETLERI.md` |
| **6** | Gereksinim İzlenebilirliği ve Değerlendirme | 10 | 190–241 | `BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` |
| **7** | Bütçe Gerçekleme Analizi | 10 | 242–271 | `BOLUM_7_BUTCE_GERCEKLEME.md` |
| — | **TOPLAM** | **100** | **271 sayfa** | — |

**Sayfa sütunu — ÖLÇÜLDÜ (13.09.2026 · `pypdf`).** Sayılar **07.09.2026 taslak
dizgisinden** okunmuştur: `FDR/pdf/FDR_TAM_TASLAK_20260907.pdf`, **271 sayfa**.

*Koşulan yöntem (aynen).* Her sayfanın **ilk 6 satırında** `^(ÖN KISIM|BÖLÜM
[1-7]|Bölüm [1-7])` düzenli ifadesi arandı; her bölümün **ilk** eşleşme sayfası
başlangıç sayfası sayıldı → **1, 5, 18, 40, 117, 168, 190, 242**. Bitiş
sayfaları bir sonraki bölümün başlangıcından bir eksiktir; Bölüm 7'nin bitişi
belgenin son sayfasıdır.

⚠ **Yöntemin sınırı dürüstçe yazılır:** eşleşmeler **tekil değildir**. Bu
tarama Bölüm 2 için ikinci bir sayfa (s. 67 — gövde metninde "Bölüm 2
takviminde özetlenir" cümlesi) ve Bölüm 5 için ikinci bir sayfa (s. 169 — alt
başlık "Bölüm 5.1 …") daha döndürmüştür; ikisi de başlangıç sayfası değildir.
**Serbest metin araması ise büsbütün ayırt edici değildir.** Sayfa sınırları
"ilk başlık satırı" kuralıyla saptanmıştır, "tek sonuç döndü" diye değil.

⚠ Bu değerler **taslak dizgiye** aittir; sayfa sütunu **teslim sürümünün nihai
dizgi koşumunda** yeniden üretilip güncellenir (üretici `scripts/fdr_pdf_uret.py`).

**Puan sütunu doğrulandı:** 5 + 5 + 40 + 15 + 15 + 10 + 10 = **100**; yönerge
Tablo 1 ile birebir (`results/fdr_sablon/fdr_yonerge_metin.txt:37`).

Yardımcı dosyalar (rapora **girmez**, çalışma belgesidir):
`YONERGE_HARITASI.md` (zorunlu iskelet + boşluk analizi) ·
`ACIK_KALEMLER.md` (elle ayıklanmış açık kalemler) ·
`ACIK_KALEMLER_HAM.md` (üretilen ham liste) ·
`TAKIM_PROMPT.md` (takım üyeleri için bölüm doldurma prompt'u) ·
`README.md` (kapak notu ve yazım kuralları).

Üretilmiş dizinler (ölçüm: `ls FDR/`, 13.09.2026):

| dizin / dosya | içerik (sayılmış) | rapora girer mi |
|---|---|---|
| `sekiller/` | **30 dosya** — 14 SVG (`akis_a…e`, `iha_baglanti`, `ika_baglanti`, `organizasyon`, `sim_*`, `uygunluk_pasta`, `uygunluk_yontem`), 5 Mermaid kaynağı (`.mmd`), 4 PNG (`sim_*`), 7 açıklama `.md` | ✅ **çizimler girer** (dizgide gömülür); `.mmd` ve `.md` kaynakları **girmez** |
| `pdf/` | **6 dosya** — 3 PDF + 3 HTML türev çıktı (`FDR_TAM_TASLAK_20260907`, `FDR_YAZILIM_KOLU_20260907`, `FDR_YAZILIM_KOLU_20260910`) | ❌ türev üründür; teslimde yenisi üretilir |
| `A6_sik_mp_ekrani.png` | A6 adımı Mission Planner ekran görüntüsü (kök `FDR/` içinde duruyor) | ✅ Bölüm 4 kanıtı — dizgiden önce `sekiller/` altına taşınacak |

---

## Y-0-M05 · Sayfa düzeni

Yönergenin her sayfasında üstte ve altta **TASNİF DIŞI** ibaresi ve sağ altta
sayfa numarası bulunur. Bu, **PDF dizgisi** aşamasında uygulanacaktır; markdown
kaynak dosyalarında sayfa başlığı/altlığı yoktur.

~~**ÖLÇÜLEMEDİ:** Dizgi henüz yapılmadı. Dizgi 17 Eylül sürüm dondurmasından
sonra, 18–20 Eylül aralığında yapılacak; TASNİF DIŞI başlık/altlık, sayfa
numarası, kapak ve içindekiler o aşamada üretilecektir.~~

→ **ÖLÇÜLDÜ (13.09.2026 · `pypdf`).** Taslak dizgisi **koşuldu**, çıktıları
repodadır; Y-0-M05 taslak düzeyinde **karşılanmıştır**:

| dizgi çıktısı | tarih | sayfa | 4. sayfadan okunan iz |
|---|---|---|---|
| `FDR/pdf/FDR_TAM_TASLAK_20260907.pdf` | 07.09.2026 | **271** | üstte "TASNİF DIŞI", altta "TASNİF DIŞI · Sayfa 4 / 271" |
| `FDR/pdf/FDR_YAZILIM_KOLU_20260907.pdf` | 07.09.2026 | **166** | "TASNİF DIŞI · Sayfa 4 / 166" |
| `FDR/pdf/FDR_YAZILIM_KOLU_20260910.pdf` | 10.09.2026 | **198** | "TASNİF DIŞI · Sayfa 4 / 198" |

Üretici `scripts/fdr_pdf_uret.py:206–216`: paged.js `@page` kenar kutuları —
`@top-center` "TASNİF DIŞI", `@bottom-center` "TASNİF DIŞI · Sayfa "
`counter(page)` " / " `counter(pages)`; Chrome headless ile basılır. Yani
başlık/altlık **ve sayfa numarası üretilmektedir** — "üretilecek" değildir.

**Kalan iş.** Nihai dizgi **teslim sürümünde** yeniden koşulur; o koşumda kapak
(Y-0-M01) ve içindekiler sayfa numaraları (Y-0-M04) güncel sayfa sayısıyla
tazelenir. Takvim: dizgi **13.09.2026**, FDR teslim **14.09.2026**, uçuş **21.09.2026** (D-477).

⚠ **Bayat takvim ikizleri (ölçüm: `grep`, 13.09.2026).** Yukarıda üstü çizilen
"17 Eylül dondurma → 18–20 Eylül dizgi" ifadesinin **dizgiye ait** ikizi iki
yerdedir: `FDR/YONERGE_HARITASI.md:216` ("TASNİF DIŞI sayfa düzeni (dizgi
18–20 Eylül)") ve `scripts/fdr_pdf_uret.py:2` ("nihai dizgi 18–20 Eylül");
ayrıca `FDR/YONERGE_HARITASI.md:28` hâlâ "Y-0-M05 … YOK (PDF dizgisinde)"
demektedir ve yukarıdaki ölçümle çelişir. `scripts/fdr_pdf_uret.py:14`
("Sayfa numarası bu taslakta YOKTUR") **kodun kendi davranışıyla** çelişir —
kod sayfa numarasını basmaktadır, yukarıda ölçüldü. Üçü de düzeltilecektir.

⚠ **Ayrım:** `BOLUM_1_OZET.md:386`, `BOLUM_3:978`, `BOLUM_4:1831`,
`BOLUM_5:376, 441, 653` satırlarındaki **17 Eylül** tarihi *dizgi* değil
**üretim kodu sürüm dondurması**dır; bu takvim geçerlidir ve bu kalemle
birlikte değiştirilmez. `BOLUM_1_OZET.md:472`'deki resmî takvim satırı da
(21 Eylül FDR teslimi + prova → 30 Eylül–3 Ekim görev test uçuşu) şartnameyle
uyumludur, **doğrudur**.
