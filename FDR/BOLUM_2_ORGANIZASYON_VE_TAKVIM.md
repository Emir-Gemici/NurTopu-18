# Bölüm 2. Organizasyonel Yapı ve Proje Takvimi (5 PUAN)

> **Yönerge (birebir):** *"Programın kurumsal işleyişini ve uygulama evrelerini
> netleştirmek adına bu bölümde; rollerin tanımlandığı organizasyonel hiyerarşi ile
> tasarım döngüsünün aşamalarını kapsayan proje takvimi incelenmektedir. Mühendislik
> döngüsünün sistematik bir düzende ilerlemesini sağlayan bu iki temel unsur, aşağıda
> iki müstakil başlık altında ayrıntılı olarak sunulmaktadır."*
> (Kaynak: `results/fdr_sablon/fdr_yonerge_metin.txt`, Bölüm 2 girişi.)

> **Takım:** Navitas Autonomous Systems · **Takım ID:** 997827 · **Başvuru no:** 5329027
> *(Kaynak: `navitas-teknofest/references/ddr_requirements.md:9-10` — DDR döneminde yazıldı.
> **Kanıt sınıfı: BEYAN (DDR dönemi, 2026-07).** Üç alanın tek bağımsız kaynağı KYS takım
> kaydıdır. Depo ölçümü (13 Eylül 2026):
> `grep -rl "997827\|5329027" --include=*.md . | grep -v "^\./\.claude/"` → **8 dosya**
> (ham çıktı: `FDR/ACIK_KALEMLER_HAM.md` · `FDR/BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` ·
> `FDR/BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` · `navitas-teknofest/references/ddr_requirements.md` ·
> `navitas-teknofest/SKILL.md` · `OGREN_ADIYAMAN/13_FDR_HARITASI.md` ·
> `OGREN_ADIYAMAN/ozet/C_fdr_spec.md` · `OGREN_ADIYAMAN/ozet/D_fdr_test_izlenebilirlik.md`).
> ⚠ `.claude/worktrees/` **hariç tutulmuştur** (çalışma ağacı kopyaları); filtresiz komut 236 satır
> döner — filtre olmadan sayı yeniden üretilemez. Sekiz dosyanın hepsi tek köke,
> `ddr_requirements.md`'ye çıkar; bağımsız KYS artefaktı depoda **yok**, bu yüzden depodan
> **türetilemez**. **Planlanan teyit:** KYS takım sayfası ekran dökümü, **14 Eylül 2026**
> (FDR teslimi) öncesi; geldiğinde kanıt sınıfı BEYAN → ÖLÇÜM olur ve bu not düşer.)*
>
> **Bu bölümün yazım kuralı.** Aşağıdaki her tarih ve her sayı bir artefakttan gelir;
> satırın sonunda hangi dosyadan ve hangi komutla çıkarıldığı yazılıdır (bölüm sonundaki
> Kanıt dizini). Ölçülmemiş bir şey "ölçülemedi" diye yazılır, tahmin edilmez. Geçmeyen
> bir kapı "geçmedi" diye yazılır (§2.2.5.4). Henüz kapanmamış insan girdileri
> **BEYAN GEREKLİ (insan)** etiketiyle boş bırakılmıştır; doldurulmadan bu bölüm
> tamamlanmış sayılmaz.

> **Numara eşlemesi (eski taslak → bu sürüm).** Bu bölüm, resmî yönergenin iskeletine
> taşınırken yeniden numaralandı. Tablo satırlarının içindeki eski çapraz atıflar
> **kaynağındaki hâliyle bırakılmıştır** (kanıt satırı değiştirilmez, §2.1.6 kural 4);
> karşılıkları şunlardır:
>
> | eski numara | bu sürümdeki karşılığı |
> |---|---|
> | 1 (İki ayrı sistem) | **Bölüm 2 — kapsam notu** |
> | 2.1 / 2.2 / 2.3 | §2.1.3 / §2.1.4 / §2.1.6 |
> | 3.1 / 3.2 / 3.3 | §2.2.2.a / §2.2.3 / §2.2.4 |
> | 4 · 4.1 · 4.2 · 4.3 · 4.4 | §2.2.5 · §2.2.5.1 · §2.2.5.2 · §2.2.5.3 · §2.2.5.4 |
> | 5 (Planlanan takvim) | §2.2.6 |
> | 6 (Takvim riskleri) | §2.2.7 |
> | 7 (Kanıt dizini) | **Kanıt dizini (Bölüm 2)** — bölüm sonu |

---

## Bölüm 2 — kapsam notu: iki ayrı sistem

Şartname bu yarışmada takımdan **iki farklı fiziksel araçla** iş ister ve bunlar aynı araç değildir.
Hem organizasyon (kim neyi icra eder) hem takvim (ne ne zaman yapılır) bu ayrım üzerine kurulur;
rapordaki her takvim satırı hangi araca ait olduğu belirtilerek yazılmıştır.

| | **FDA görev test uçuşu aracı** | **Yarışma (final) aracı** |
|---|---|---|
| Şartname dayanağı | §5.3.2 — *"çoklu rotorlu ve dikey iniş-kalkış yapabilen bir insansız hava aracı (Drone)"* | §6 — *"sabit kanatlı insansız hava aracı (İHA) konfigürasyonunda olması zorunludur"* |
| Konfigürasyon | Quadcopter, 3B baskı gövde | Sabit kanat + mancınık fırlatma + paraşütle iniş + İKA |
| Görev | 20×20 m simüle alanda ≥ 30 m irtifadan açık güzergâh tespiti, YKS'ye canlı aktarım, ≤ 10 dk | Tam görev zinciri (fırlatma → tespit → aktarım → paraşüt → İKA → hedef bölge) |
| Bu raporda durumu | **Gövde basıldı, aviyonik monte edildi, kalibre edildi ve araç havalandı.** ~~aviyonik montajı 5 Eylül 2026'da yapılacak~~ → montaj 5–6 Eylül'de yapıldı (D-426), ilk askı **12 Eylül 2026** (A12: ~3 m'de ~15 s askı + **kodla** LAND — **BEYAN**, ham dosya yok). 🔴 **A12 kabul kapısı AÇIK, geçilmedi:** ön kayıt 1–2 m'de **≥ 30 s** askı istiyordu (`ATOLYE_TEST_GUNU_20260912.md:193`), fiilen 3 m'de 15 s; `MOT_THST_HOVER` hâlâ **0,35 fabrika** (`emir.param:580`, `MOT_HOVER_LEARN=2` açık olmasına rağmen öğrenmemiş) ⇒ **itki payı ÖLÇÜLMEDİ** (D-474 §4); VIBE ve askı akımı **ÖLÇÜLMEDİ** (`.bin` çekilmedi, T257); bağlayıcı ön koşul **A13 yapılmadı** (D-473). **ÖLÇÜM (kümülatif — tek güne atfedilemez):** `config/pixhawk/emir.param:980` `STAT_FLTTIME` = **273 s** (4 dk 33 sn); önceki sıfır okuması `config/pixhawk/mevcut.param:980` (6 Eyl **20:22**). Bu pencere 6 Eylül **20:45–21:34**'teki 26 arm / 3 devrilmeyi (D-429) **de** içerir ⇒ 273 s **6 ve 12 Eylül'ün toplamıdır**; 12 Eylül'e düşen pay **ÖLÇÜLEMEDİ**. `STAT_BOOTCNT` 48 → 96. Dökümün kanıtladığı tek şey: 6 Eyl 20:22'den sonra kartta 4 dk 33 sn uçuş/arm süresi **birikmiştir** — A12'nin süresi, irtifası ve başarısı bu sayıdan çıkarılamaz ve **BEYAN** kalır (T257). ✅ Kalibrasyon kanıtlı: `COMPASS_OFS/DIA/ODI`, `INS_ACC*`, `INS_GYR*` 6 Eylül dökümüne göre değişmiş | **Üretilmedi.** Tasarım DDR'de sunuldu; üretim dalgası 21 Eylül sonrası (bkz. Bölüm 5 §5.2.10) |
| Ağırlık limiti | — (§5.3.2 limit koymuyor) | İHA ≤ 25 kg (yükler dâhil), İKA ≤ 10 kg (yük hariç) — §6 |

⚠ **Bu ayrım raporun her yerinde korunur.** FDA uçuşunda paraşüt ve İKA **yoktur**; yer kontrol
istasyonu yazılımı bunun için ayrı bir görev kipiyle (`--fda`) çalıştırılır ve o kipte paraşüt
ile İKA düğmeleri fiilen kapalıdır (sözleşme: `CONTRACTS.md` §6.7, karar kaydı `REVIEW_LOG.md`
D-408, 2026-09-02).

---

## Bölüm 2.1. Organizasyonel Yapı

> **Yönerge (birebir):** *"Takımın güncel organizasyonel yapılanması ve üyelerin/birimlerin
> icra yetkileri bu bölümde şematize edilmelidir. Raporun objektif değerlendirme kriterleri
> uyarınca, üyelerin kişisel verilerinden (isim, görsel vb.) arındırılmış, tamamen rol bazlı
> ve profesyonel bir anlatım tercih edilmelidir."*

### 2.1.1 Kişisel veriden arındırma — `Y-2.1-M02` (karşılanmıştır)

Bu bölümde **ad-soyad, fotoğraf ve kişiye bağlanabilir hiçbir veri yoktur ve olmayacaktır.**
Yapı tamamen **rol kodları (R1…R8)** üzerinden tanımlıdır.

Bu, doldurulmayı bekleyen bir boşluk **değildir**: yönerge isim istemediği gibi açıkça
*"üyelerin kişisel verilerinden (isim, görsel vb.) arındırılmış, tamamen rol bazlı"* bir anlatım
şart koşar. Dolayısıyla **rol bazlı anlatım, gereksinimin karşılanmış hâlidir**; isim eklemek
gereksinimi kapatmaz, **ihlal eder**.

⚠ Raporun önceki sürümünde "rol → isim ataması" bir insan beyanı borcu olarak işaretliydi.
Bu **yanlış okumaydı** ve yönerge okunduktan sonra kaldırılmıştır (dayanak: `REVIEW_LOG.md`
D-417 — *"resmî FDR yönergesi okundu: rapor yanlış iskeletteydi ve isim yasağını bilmiyorduk"*).
Rol → kişi eşlemesi takım içi bir kayıttır ve **rapora girmez**; bu yüzden §2.1.7'deki açık
kalem listesinde de yer almaz.

Kapsam sınırı: takımın **üye sayısı** ve **öğrenim düzeyi oranı** şartname §4 kontenjan
kuralıyla ilgilidir, kişisel veri değildir; o iki sayı §2.1.7'de açık kalem olarak durur.

### 2.1.2 Organizasyon şeması — icra yetkileri (`Y-2.1-M01`)

Şema iki hattı ayırır: **icra hattı** (görev emri yukarıdan aşağı akar) ve **denetim hattı**
(kanıt aşağıdan yukarı akar, hüküm kaptana döner). R8 bilerek icra hattının **dışındadır**.

![Organizasyon şeması — icra yetkileri, rol bazlı, isimsiz](sekiller/organizasyon.svg)

*Şema rol bazlıdır, isim içermez (Y-2.1-M02). `sekiller/organizasyon.svg`, 7 Eylül 2026; kutular §2.1.3
tablosundan (rol kodu + rol adı + icra yetkisi), hatlar ve kurallar §2.1.2'den, R2/R5 uçuş anı
eşzamanlılığı §2.1.4–§2.1.5'ten (sarı şerit + not kutusu). Düz ok icra hattı, kesikli ok denetim hattı;
R8'in hükmü R1'e döner. Nöbetçi: `tests/test_gece_sekiller.py` (isim taraması, R1–R8 tamlığı,
eşzamanlılık notu). Aşağıdaki metin şeması aynı içeriğin düz-metin karşılığıdır ve korunur.*

```text
                      ┌───────────────────────────────────────────────┐
                      │             R1 · TAKIM KAPTANI                │
                      │  İCRA YETKİSİ: "Takım Hazır" ilanı · uçuş/    │
                      │  uçmama kararı · rol ataması · tedarik onayı  │
                      │  · koordinat girişi onayı                     │
                      └──────────────────────┬────────────────────────┘
                                             │  görev emri  ──►  (icra hattı: tek yön)
       ┌──────────────┬──────────────┬───────┴──────┬──────────────┬──────────────┐
       ▼              ▼              ▼              ▼              ▼              ▼
 ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
 │ R2  PİLOT  │ │ R3 AVİYONİK│ │ R4 GÖREV   │ │ R5   YKS   │ │ R6   İKA   │ │ R7 YAZILIM │
 │            │ │            │ │ BİLGİSAYARI│ │ OPERATÖRÜ  │ │ (final     │ │ /GÖRÜNTÜ   │
 │ İCRA:      │ │ İCRA:      │ │ İCRA:      │ │ İCRA:      │ │  dalgası)  │ │ İCRA:      │
 │ uçuşu      │ │ parametre  │ │ sürüm ve   │ │ ACK'siz    │ │ İCRA:      │ │ kod değ.   │
 │ KESME      │ │ yükleme ·  │ │ paket      │ │ onayı      │ │ İKA sürücü │ │ (mühre     │
 │ mod anaht. │ │ kablo hattı│ │ kurulumu · │ │ REDDETME · │ │ seçimi     │ │  kadar)    │
 │            │ │ kabulü     │ │ kamera     │ │ ekran      │ │            │ │ EŞİK DEĞ.  │
 │            │ │            │ │ kaynağı    │ │ düzeni     │ │            │ │ YETKİSİ YOK│
 └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
       │              │              │              │              │              │
       └──────────────┴──────────────┴───────┬──────┴──────────────┴──────────────┘
                                             │  ürettiği kanıt (log · ölçüm · suit çıktısı)
                      ╔══════════════════════╦════════════════════════╗
                      ║          R8 · KANIT-KALİTE (DENETİM)          ║
                      ║  İCRA YETKİSİ: kapıyı GEÇERSİZ sayma ·        ║
                      ║  bulguyu deftere yazma · ön kayıt tutma       ║
                      ║                                               ║
                      ║  ! İCRA HATTININ DIŞINDADIR: kanıt üreten     ║
                      ║    rolün onayına bağlı DEĞİLDİR (§2.1.6 / 3)  ║
                      ╚══════════════════════╩════════════════════════╝
                                             │
                                             └──►  bulgu / kapı hükmü R1'e döner
                                                   (icra birimlerine DEĞİL) — döngü kapanır
```

**Şemanın okunuşu — üç bağlayıcı kural:**

1. **Tek karar mercii.** Uçuş/uçmama, "Takım Hazır" ilanı ve tedarik onayı yalnız R1'dedir.
   Hiçbir icra birimi kendi başına uçuş kararı veremez. R2'nin yetkisi **uçuşu kesmedir**
   (tek yönlü emniyet yetkisi), başlatma değil.
2. **Yetki devri karar devri değildir.** R7 kod değiştirebilir; **eşik değiştiremez** —
   eşikler ön kayıtta donmuştur (§2.1.6 / 1) ve `CONTRACTS.md` §12 sonraki terfileri bağlar.
3. **Denetim ayrı hattadır.** R8 icra emri almaz; kanıtı çürütür ve hükmü R1'e verir.
   Bu ayrım uygulanmıştır: `REVIEW_LOG.md` D-405 ve D-407 çürütme turları, kanıtı üreten
   rolün onayına bakılmadan kapatılmıştır.

⚠ Şema **rolleri** gösterir, kişileri değil. Bir kişi birden çok kutuyu üstlenebilir; bunun
uçuş anındaki tek ölçülmüş sonucu §2.1.5'te açık kalem olarak durur.

### 2.1.3 Rol tanımları, icra yetkileri ve üretilen kanıt

Şartname §4, takımın **kaptan dâhil en az 6, en fazla 10 kişiden** oluşmasını zorunlu kılar.
Aşağıdaki yapı **rol** üzerinden tanımlıdır; bir kişi birden çok rolü üstlenebilir, ancak
**kanıt üreten rol ile o kanıtı onaylayan rol aynı kişi olamaz** (bağımsızlık kuralı, §2.1.6).

| # | Rol | Sorumluluk | Yetkisi olan kararlar | Ürettiği kanıt |
|---|---|---|---|---|
| R1 | **Takım Kaptanı** | Görev günü tutanağı, saha kararları, kişi ataması, alışveriş/tedarik onayı | "Takım Hazır" ilanı; uçuş/uçmama kararı; koordinat girişi onayı | Saha tutanağı, karar kaydı |
| R2 | **Pilot** | RC kumanda, arm/disarm ön kontrolü, manuel kurtarma (yalnız emniyet) | Uçuşu kesme; mod anahtarı kullanımı | Uçuş logu (`.bin`), hover/loiter kayıtları |
| R3 | **Aviyonik sorumlusu** | Pixhawk 6C + güç dağıtımı + kablolama + kalibrasyon; failsafe/geofence | Parametre yükleme; kablo hattı kabulü | **`config/pixhawk/emir.param`** (12 Eylül 2026 23:55, 18 148 B) — karttan alınan **üçüncü döküm** (D-474). Önceki iki kart dökümü: `mevcut.param` (18 139 B, **6 Eyl 20:22**) ve `arducopter_fda_20260906.param` (18 139 B, **7 Eyl 01:18** — içerik `mevcut.param` ile aynı, sonradan kopyalandığı için damgası farklı) (D-428 §5g). Aynı dizinde ayrıca iki **şablon** durur, bunlar kart dökümü **değildir**: `arducopter_fda.param` (14 345 B, 7 Eyl 12:10) ve `arduplane_final.param` (24 258 B, 12 Eyl 01:17). Yordam: `ls -la config/pixhawk/*.param` → **5 satır** (13 Eylül 2026). Karşılaştırma: `config/pixhawk/PARAMETRE_KILAVUZU_1SAYFA.md` |
| R4 | **Görev bilgisayarı / kamera** | Jetson (Orin Nano Developer Kit 4 GB — D-431) kurulumu, kamera köprüsü, FPS kapısı, model yükleme | Sürüm/paket kurulumu; kamera kaynağı seçimi | `jetson_fps.py` çıktısı, `jetson_baslat.sh --kapi` çıktısı |
| R5 | **YKS operatörü** | Yer kontrol istasyonu, hakem ekranı, aktarım/ACK, kronometreler | Ekran düzeni; ACK'siz onayı reddetme | `hakem_log`, YKS ekran kaydı |
| R6 | **İKA sorumlusu** | İKA hattı (final dalgası); sürücü entegrasyonu, yük ve temas | İKA sürücü seçimi (donanım kararı) | `scripts/ika_surucu_kabul.py` kabul turu çıktısı |
| R7 | **Yazılım / görüntü işleme** | Algı zinciri, rota kararı, sözleşmeler, testler | Kod değişikliği (mühre kadar); eşik **değiştirme yetkisi YOKTUR** | `tests/` suit çıktısı, `REVIEW_LOG.md` D-kayıtları |
| R8 | **Kanıt-kalite (denetim)** | Bağımsız çürütme turu; ön kayıt tutma; kapı denetimi | Bulguyu deftere yazma; kapıyı geçersiz sayma | `REVIEW_LOG.md` çürütücü kayıtları |

Bugün itibarıyla kullanıcı beyanıyla atanmış roller: **R2 Pilot** ve **R5 YKS
operatörü** (`SAHA_HAZIRLIK_PLANI_20260903.md` §3 ve §1.8; beyan 3 Eylül 2026).
R5 rolünün üstlenilmesi ve PC'de uçtan uca koşturulması `REVIEW_LOG.md` D-414'te
ölçümüyle kayıtlıdır (ekran görüntüsü: `results/yks_kurulum/yks_acilis_20260903.png`).

### 2.1.4 Saha günü rol dağılımı (5 Eylül montaj günü ve 21 Eylül prova günü)

| an | R1 Kaptan | R2 Pilot | R3 Aviyonik | R4 Jetson/kamera | R5 YKS |
|---|---|---|---|---|---|
| Kutu/envanter | tutanak, eksik listesi | — | tartı + fotoğraf | — | — |
| Mekanik + kablolama | denetim | yapılandırmada | **yürütür** | kamera/Jetson yerleşimi | — |
| Pixhawk yapılandırma | tutanak | radyo kalibrasyonu | **yürütür** | — | HEARTBEAT teyidi |
| Jetson kurulumu | — | — | UART hattı | **yürütür** | — |
| Yer zinciri | kronometre | — | — | uçlar | **yürütür** |
| Uçuş | "Takım Hazır" | kumanda | pil/CG | canlı izleme | hakem ekranı |

Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §2 (montaj günü tablosu) ve §6 (21 Eylül akışı).

### 2.1.5 🔴 Ölçülmüş rol çakışması — R2 Pilot + R5 YKS operatörü

**Bu iki rol uçuş anında ÇAKIŞIR ve çakışma bilerek kayda geçirilmiştir.**
§2.1.4 tablosunun "Uçuş" satırında R2 kumandayı tutar (gözü araçta), R5 hakem
ekranını sürer (gözü ekranda, hakemle birlikte onay basar). Görev ≤ 10 dk
boyunca ikisi **eşzamanlıdır**; tek kişi ikisini birden yapamaz. Montaj günü
(5 Eylül) ve yer provalarında çakışma yoktur — orada aynı kişi ikisini de
yürütebilir. **Kapanışı ölçüm değil kişi atamasıdır** — çakışmanın kendisi §2.1.4 tablosundan
ölçülmüştür, çözümü R1'in (kaptan) atama kararıdır ve depodan türetilemez.
**Planlanan beyan: kaptan, R2 veya R5 rolüne ikinci kişiyi atar — son tarih 14 Eylül 2026**
(FDR teslimi), uygulama 21 Eylül 2026 uçuş günü. Atama yapılmazsa raporun hükmü şudur:
**tek kişi ≤ 10 dk görev boyunca iki rolü birden yürütemez ve bu bir ölçülmüş eksikliktir**,
gizlenmiş bir varsayım değil.

Dayanak: `SAHA_HAZIRLIK_PLANI_20260903.md` §3 uyarı kutusu (3 Eylül beyanı) ve
`REVIEW_LOG.md` D-414 ("çakışma kayda geçirildi … uçuş günü için ikinci kişi **açık kalemdir**").

### 2.1.6 Karar ve kanıt yordamı — icra yetkisinin sınırı

Bu projenin organizasyonu, kim ne yapar tablosundan ibaret değildir; **bir işin bittiğine kimin,
neye bakarak karar verdiğini** de tanımlar. Dört kural bağlayıcıdır:

1. **Ön kayıt.** Bir ölçümün eşiği, sonuç görülmeden yazılır ve sonradan gevşetilmez
   (`REVIEW_LOG.md` D-107). Bu kural somut iş görmüştür: 2026-09-01'de umut verici bir ara
   sonuç, önceden yazılmış bir RED kuralıyla karşılaşıp reddedilmiştir (D-377).
2. **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Ölçülemeyen şey geçmiş sayılmaz; paydası olmayan oran rapora girmez.
3. **Bağımsızlık.** Bir iş, onu yapanın onayıyla kapanmaz. Kod yazan rol kendi kodunun kapısını
   onaylayamaz; ayrı bir çürütme turu koşulur (`AGENTS.md` §8; uygulanmış örnekler: D-405, D-407).
4. **Kanıt silinmez.** Yanlış çıkan iddia defterden çıkarılmaz; üstü çizilip düzeltmesine işaret
   verilir (D-373). Bu bölümdeki §4.4 bu kuralın uygulanmasıdır.
   *(Numara eşlemesi: bölüm yönerge iskeletine taşınırken eski **§4.4** başlığı **§2.2.5.4**
   olmuştur; aynı kuralın ikinci uygulaması **§2.2.2.b**'dir. Eski numaralar, çapraz atıfları
   bozmamak için satırlarda olduğu gibi bırakılmıştır.)*

Kanıt defteri: `REVIEW_LOG.md` — ~~420 kayıt başlığı / 414 benzersiz kayıt no (2026-09-03)~~
→ **13 Eylül 2026 itibarıyla 481 kayıt başlığı / 475 benzersiz kayıt no.**
Ölçüm (üreten commit'le birlikte, §2.1.6 kural 4 uyarınca eski okuma silinmedi):
`grep -cE "^### D-[0-9]+" REVIEW_LOG.md` → **481**;
`grep -oE "^### D-[0-9]+" REVIEW_LOG.md | sort -u | wc -l` → **475**
(fark 6 = aynı kayıt numarasının ek/düzeltme başlığıyla tekrarlanması).
Üreten commit: `d5bf2af5` (**2026-09-13 02:20:19 +0300**) — çalışma kopyası bu commit'le aynıdır,
dolayısıyla okuma `git show d5bf2af5:REVIEW_LOG.md | grep -cE '^### D-[0-9]+'` ile yeniden üretilir.

🔴 **Aynı defterin üç okuması birbirini tutmuyor — üçü de silinmedi (kural 4).**

| okuma | başlık | benzersiz | ~~kayıtlı saat~~ → **git'ten daraltılan alınma aralığı** | üreten commit | nerede yazılı |
|---|---|---|---|---|---|
| A | 414 | 408 | 2026-09-03 (saat kayıtlı değil) — **git'ten daraltıldı:** bu içerik `6c70dd70` (2026-09-02 23:56:28) ile yazıldı, `2705b4eb` (2026-09-03 11:15:50) ile 418'e değişti ⇒ okuma **2026-09-02 23:56 – 2026-09-03 11:15** aralığında alınmıştır; "3 Eylül" etiketi **yanlış değil**, yalnız saatsizdir | `6c70dd70`..`2705b4eb` | Kanıt dizini satır 11 |
| B | 420 | 414 | 2026-09-03 (saat kayıtlı değil) — **daraltıldı:** `59e1acc2` (2026-09-03 11:42:50) ile yazıldı ⇒ okuma bu andan sonradır | `59e1acc2` | hemen yukarıdaki paragraf |
| C | **424** | **418** | **2026-09-04 00:06** (yazım anı); üreten commit anı `bb832a2b` **2026-09-04 00:14:18** | `bb832a2b` | §2.1.6, yeniden ölçüm |
| **D** | **481** | **475** | **2026-09-13 02:20:19** | `d5bf2af5` | bu satır |

Ölçüm komutları (C okuması): `grep -cE "^### D-[0-9]+" REVIEW_LOG.md` → 424;
`grep -oE "^### D-[0-9]+" REVIEW_LOG.md | sort -u | wc -l` → 418.
✅ **KAPANDI — 13 Eylül 2026, bir depo ölçümüyle (insan beyanıyla değil).** ~~ÖLÇÜLEMEDİ: A ve B
okumalarının hangi saatte alındığı kayıtlı değil~~ hükmü fazla karamsardı: defter git'te izlenen
bir dosyadır, dolayısıyla **her okuma bir commit aralığına daraltılabilir**. Yordam ve ham çıktı:

```text
$ git log --date=iso --pretty=format:"%h|%ad" -- REVIEW_LOG.md   # dosyaya dokunan commit'ler
$ git show <sha>:REVIEW_LOG.md | grep -cE '^### D-[0-9]+'        # o andaki başlık sayısı
$ git show <sha>:REVIEW_LOG.md | grep -oE '^### D-[0-9]+' | sort -u | wc -l

6c70dd70  2026-09-02 23:56:28 +0300   ->  414 / 408      (= A okumasının içeriği yazıldı)
2705b4eb  2026-09-03 11:15:50 +0300   ->  418 / 412      (= A içeriği burada değişti)
59e1acc2  2026-09-03 11:42:50 +0300   ->  420 / 414      (= B okuması)
bb832a2b  2026-09-04 00:14:18 +0300   ->  424 / 418      (= C okuması)
```

Üç okuma da **birebir** yeniden üretildi; **hiçbiri yanlış değildi** ve hiçbir tarih etiketi
hatalı çıkmadı. A okumasının içeriği 2 Eylül 23:56'da yazılmış olmakla birlikte **3 Eylül 11:15'e
kadar HEAD'de aynen durmuştur**; dolayısıyla "2026-09-03" etiketi tutarlıdır — eksik olan yalnız
**saattir**, ve o eksik artık bir **aralıkla** kapatılmıştır (aralık kapalı değil, açıktır:
bir commit'in yazılma anı, okumanın alınma anı **değildir**).
**Kalıcı kapanış:** bundan sonra her defter okuması saat damgası **ve** üreten commit sha'sı ile
yazılır; yukarıdaki D satırı o biçimin ilk uygulamasıdır.

### 2.1.7 Bölüm 2.1'in açık kalemleri

1. **Takım üye sayısı ve şartname §4 oran kontrolü** (kaptan dâhil 6–10 kişi; lisansüstü üye
   oranının şartname sınırını aşmadığı). Bu bir sayı beyanıdır, kişisel veri değildir.
   **Depodan türetilemez** (üye listesi repoda yok; `git shortlog -sn` yalnız tek commit yazarını
   gösterir ve takım üyeliğinin kanıtı değildir). **Bugünkü hüküm:** rapordaki organizasyon
   **8 rol** (R1–R8) tanımlar ve *"bir kişi birden çok rolü üstlenebilir"* (§2.1.3) → rol sayısı
   üye sayısının **üst sınırını değil yalnız iş kalemini** verir; §2.1.5'te ölçülmüş R2/R5
   çakışması **en az 2 kişi** gerektiğini kanıtlar. Şartname §4 tabanı (6 kişi) bağlayıcıdır.
   **Planlanan beyan: KYS üye listesi sayımı (toplam sayı + lisansüstü sayısı), 14 Eylül 2026.**
2. **Danışman öğretim üyesi** bilgisi (unvan/kurum düzeyinde, isimsiz). Depo ölçümü
   (13 Eylül 2026): `grep -ril "danışman\|danisman" --include=*.md . | grep -v "^\./\.claude/"`
   → **5 dosya** (`FDR/ACIK_KALEMLER_HAM.md` · `FDR/BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` ·
   `OGREN_ADIYAMAN/01_YARISMA_VE_GOREV.md` · `OGREN_ADIYAMAN/ozet/D_fdr_test_izlenebilirlik.md` ·
   `OGREN_ADIYAMAN/ozet/H_sartname.md`); hepsi **açık-kalem ya da şartname özeti** satırıdır,
   bir künye kaydı olarak **hiçbir yerde yok** → türetilemez. ⚠ `.claude/worktrees/` hariç
   tutulmuştur; filtresiz komut 138 satır döner.
   **Bugünkü hüküm: danışman alanı BOŞ ve bu bir eksikliktir** ("ölçülemedi" değil — kayıt
   hiç oluşturulmamış). **Planlanan beyan: unvan + kurum (isimsiz), 14 Eylül 2026.**
3. **Takım künyesinin KYS teyidi** (ID 997827 / başvuru 5329027) — bölüm başındaki künye
   kalemiyle **aynı kalemdir, iki kez sayılmaz**. Kanıt sınıfı bugün **BEYAN**: iki sayı depoda
   (filtreli ölçümle) **8 belgede** geçiyor ama hepsi tek kaynağa
   (`navitas-teknofest/references/ddr_requirements.md:9-10`, 2026-07) çıkıyor; bağımsız doğrulama
   yalnız KYS kaydıdır. **Planlanan teyit: KYS takım sayfası ekran dökümü, 14 Eylül 2026.**
4. **Uçuş günü için R2/R5 çakışmasının çözümü** — bu iki rolden birine ikinci bir kişi
   (§2.1.5 ile **aynı kalem**). Çakışmanın kendisi **ölçülmüştür** (§2.1.4 "Uçuş" satırı:
   R2 kumandada, R5 hakem ekranında, ≤ 10 dk boyunca eşzamanlı); çözümü kaptanın atama
   kararıdır, ölçüm ya da türetme değildir. **Planlanan beyan: kaptan ataması, son tarih
   14 Eylül 2026; uygulama 21 Eylül 2026 uçuş günü** (D-471 ile takvim yeniden kuruldu).
5. **R6 İKA rolünün final dalgasında kime/hangi birime verileceği.** **Bugünkü hüküm: rol
   boştadır ve bu 21 Eylül'e kadar bir eksiklik değildir** — FDA görev test uçuşu aracında
   İKA **yoktur** (Bölüm 2 kapsam notu; `CONTRACTS.md` §6.7: `--fda` kipinde İKA düğmeleri
   fiilen kapalı), rol ilk kez **final (sabit kanat + İKA) dalgasında** yüklenir ve o dalga
   21 Eylül 2026 sonrasıdır (Bölüm 5 §5.2.10). Rolün yazılım tarafı boş beklemiyor: İKA iz
   genişliği **459,5 mm ÖLÇÜLDÜ** (12 Eylül, şerit metre, D-472 — sözleşmedeki 0,39 m TAHMİN'i
   ve URDF'teki 0,319 m'nin ikisi de yanlıştı), teker çapı Ø125 mm teyit edildi (D-471).
   **Planlanan atama: final dalgası açılışında, 30 Eylül 2026 (FDA penceresi) sonrası.**

---

## Bölüm 2.2. Proje Takvimi

> **Yönerge (birebir):** *"Bu bölüm kapsamında daha önce Detay Değerlendirme Raporu'nda
> hazırlanmış olan proje takviminde yer alan termin planına uygunluk teyit edilmeli, iş
> takvimine eklenen yeni iş akışları mevcut ise planlama analitik bir yaklaşımla yeniden
> değerlendirilerek güncellenmelidir."*

Bu başlık üç soruya sırayla cevap verir:
**(1)** DDR termin planı tutuyor mu (§2.2.1) · **(2)** gerçekte ne oldu (§2.2.2–2.2.4) ·
**(3)** takvime hangi yeni iş akışları girdi ve plan buna göre nasıl güncellendi (§2.2.5–2.2.9).

### 2.2.1 DDR termin planına uygunluk teyidi (`Y-2.2-M01`)

DDR döneminin termin planı depoda `navitas-teknofest/references/ddr_requirements.md` içindedir
ve **"Kritik Takvim" başlığı altında üç tarihten ibarettir** (satır 3–6). Aynı dosyanın
"DDR Gap Analizi" bölümü, DDR'ye taşınacak kalemler arasında *"Organizasyon şeması"* (satır 90),
*"Proje takvimi (güncelleme gerekli)"* (satır 91) ve *"Planlanan test takvimi"* (satır 124)
satırlarını taşır. Aşağıdaki tablo bu beş kalemin bugünkü durumudur.

| # | DDR termin planı kalemi (kaynak satır) | DDR'de yazılı | Bugünkü gerçekleşme | Durum |
|---|---|---|---|---|
| 1 | **DDR Son Teslim** (`ddr_requirements.md:4`) | 15 Temmuz 2026 | Depoda ölçülen: DDR belgesinin son iz bırakan sürümü **v4.3**, 2026-07-12 (`f4d1583`); belge 2026-07-12'de depo dışına alındı (`38798f2` — *"DDR dokümanları repoda taşınmıyor"*). 15.07.2026'da iki teknik commit var (`cb10e0e`, `bcfab0f`) | **ÖLÇÜLEMEDİ ve ÖLÇÜLEMEZ — kaynağı yapısaldır, eksiklik değil.** DDR belgesi **bilerek** depo dışındadır (`38798f2`, 2026-07-12: *"doc/ repo dışı tutuluyor — DDR dokümanları repoda taşınmıyor"* — anayasa madde 18); teslim **anı** git'ten görülmez ve türetilemez. Depodan görülebilen en yakın iz: son sürüm v4.3 `f4d1583` (2026-07-12) + 15.07'de iki teknik commit (`cb10e0e`, `bcfab0f`) → **teslim tarihiyle çelişen hiçbir kanıt yok**, ama bu teyit değildir. **Planlanan beyan: KYS teslim kaydının ekran dökümü (tarih + saat), 14 Eylül 2026** |
| 2 | **DDR Sonuçları** (`ddr_requirements.md:5`) | 29 Temmuz 2026 | Şartname resmî tarihi ile birebir aynı (`results/sartname_bosluk/sartname_metin.txt` s.11). Depoda sonuç/puan artefaktı yok | **Depoda sonuç/puan artefaktı YOK ve türetilemez** — puan KYS'de bildirilir, git geçmişinde iz bırakmaz. **Bugünkü hüküm: DDR geçildi** (aksi hâlde FDR aşamasına geçilemezdi; takım ID 997827 FDR sürecinde etkindir) — **puan bilinmiyor, sıfır ya da tahmin yazılmıyor**. **Planlanan beyan: KYS sonuç bildirimi ekran dökümü (puan dâhil), 14 Eylül 2026** |
| 3 | **FDR** (`ddr_requirements.md:6`) | 21 Eylül 2026 | Şartname s.11 ile birebir aynı (**21.09.2026 – 17.00**). Takım planı bu tarihe kilitli (§2.2.8) ve tarih artık **kapı testiyle** korunuyor: `tests/test_fdr_takvim_kapisi.py` **4 test, 4/4 OK** (koşum 2026-09-04) | **UYGUN — termin planı tutuyor** |
| 4 | *"Proje takvimi (güncelleme gerekli)"* (`:91`) | DDR'de güncelleme borcu olarak işaretlenmiş | Güncellendi: §2.2.2 (ölçülmüş gerçekleşme), §2.2.5 (yeni iş akışları), §2.2.8 (3 → 30 Eylül planı) | **KAPANDI** |
| 5 | *"Organizasyon şeması"* (`:90`) | DDR'de ÖDR'den taşınacak kalem | §2.1.2'de **isimsiz, rol bazlı** olarak yeniden üretildi (`Y-2.1-M02`) | **KAPANDI** |
| 6 | *"Planlanan test takvimi"* (`:124`) | DDR'de "yeni gerekli" kalem | §2.2.8 satır satır kapılıdır; test içeriği Bölüm 4'tedir | **KISMEN — koşulan/koşulmayan ayrımıyla, 13 Eylül 2026 itibarıyla.** ~~saha testleri 5–19 Eylül'de koşulacak~~ → Kabul kâğıdı (`ATOLYE_TEST_GUNU_20260912.md`) **14 adım** içerir. **GEÇTİ (4, kanıt sınıfı BEYAN — ham dosya yok):** A1 RC failsafe (`:58`) · A3 pil failsafe (`:82`) · A4 anahtarla LAND (`:93`) · A5 bağlantı kaybı, gerçek SiK (`:105`). **KISMİ (1):** A2 GCS failsafe (`:69`) — tetikleme çalıştı, kodla uçurulamadı (MP bağlantısı yoktu). ⚠ Aynı satırdaki *"`FS_GCS_ENABLE` geçici 0 yapıldı, uçuştan önce 1'e döner"* borcu **ölçümle çürüdü:** `emir.param:408` = **5** ("Enabled always Land"), 6 Eylül dökümünde 1'di (`mevcut.param:408`) ⇒ failsafe kartta **açık ve LAND'e ayarlı**, `FS_THR_ENABLE=3` ile tutarlı, **geri alma borcu YOK** (D-474 §2). **ÖLÇÜLDÜ ve DÜŞTÜ (1):** A6 SiK RTT — 13 Eylül, gerçek RF çifti (`:116`, D-476); ayrıntı §2.2.7. **UÇUŞ OLDU ama KABUL KAPISI AÇIK (1):** A12 askı — 3 m'de ~15 s + kodla LAND (BEYAN); ön kayıtlı 4 kabul kaleminin **4'ü de açık** (bkz. kapsam notu tablosu). **YAPILMADI (7):** A7, A8, A9, A9-ek, A10, A11 (kamera 14 Eylül'e yetişmiyor — A11 yerine **HESAP** yazıldı, `results/atolye_20260912/A11_gecikme_HESAP.md`), A13 (pens ampermetre yok). **Sayı: 14 adımın 4'ü tam geçti, 1'i kısmi, 1'i ölçülüp DÜŞTÜ, 1'i kapısı açık, 7'si yapılmadı** = **%28,6 tam geçiş** |

⚠ **Kapsam uyarısı — abartılmıyor.** Depodaki DDR referans dosyasının termin planı **üç tarihtir**;
iş paketi kırılımı, Gantt çizelgesi veya kaynak atama tablosu **depoda yoktur**.
**ÖLÇÜLEMEDİ ve depodan türetilemez: DDR'nin rapora giren tam termin çizelgesi.** Depodaki
referans dosyası (`ddr_requirements.md`) yalnız **3 tarih** taşır (satır 3–6); Gantt, iş paketi
kırılımı ve kaynak atama tablosu **depo dışı yerel yedektedir** — belgenin depoda tutulmaması
bilinçli bir karardır (`38798f2`, anayasa madde 18), dolayısıyla bu bir kayıt kusuru değil,
**kapsam sınırıdır**. **Bugünkü hüküm: yukarıdaki tablo, termin uygunluğunun depodan
görülebilen tam kısmıdır ve o kısımda 6 kalemin 2'si KAPANDI (4, 5), 1'i UYGUN (3), 1'i KISMEN
(6), 2'si depodan türetilemez ve KYS beyanı bekler (1, 2).** **Planlanan beyan: DDR proje
takvimi sayfasının (Gantt + iş paketleri) rapora alınması, 14 Eylül 2026.**

### 2.2.2 Gerçekleşen proje takvimi — depo geçmişinden ölçüldü

Aşağıdaki tablo tahmin değildir: `O:\navitas` git deposunun tamamı taranarak
`git log --date=short --pretty=format:"%ad|%h|%s"` ile çıkarılmıştır. ~~Depoda **551 commit**
(3 Eylül 2026 gecesi) vardır~~ → **13 Eylül 2026 ölçümü: HEAD'de 846 commit**
(`git log --oneline | wc -l` → **846**), tüm dallar dâhil **1019**
(`git log --all --oneline | wc -l` → **1019**); üreten commit `d5bf2af5`
(**2026-09-13 02:20:19 +0300**). İlk commit **2026-05-06** (`17258f8`, "start project") —
değişmedi. Eski okuma §2.1.6 kural 4 uyarınca silinmedi; ayrıca artık **yeniden üretilebilir**:
551, `0ac3a35a` (2026-09-03 10:42:48) commit'inde HEAD'in tam sayısıdır (§2.2.2.b).

#### 2.2.2.a Faaliyet yoğunluğu — gün başına commit (ölçüm, 2026-09-03)

| ay | commit'li gün | toplam commit | en yoğun gün |
|---|---|---|---|
| Mayıs 2026 | 3 | 4 | 07.05 (2) |
| Haziran 2026 | 2 | 4 | 24.06 (3) |
| Temmuz 2026 | 5 | 27 | 11.07 (16) |
| Ağustos 2026 | 27 | 425 | 26.08 (**89**) |
| Eylül 2026 (1–2) | 2 | 93 | 02.09 (**72**) |

Ölçüm komutu: `git log --date=short --pretty=format:"%ad|%s" | awk -F'|' '{print $1}' | sort | uniq -c`.
Yorum: proje ağırlığı Ağustos'ta yoğunlaşmıştır; bu, DDR sonrası (29.07) açılan doğrulama
borçlarının kapatıldığı dönemdir ve §2.2.5'teki revizyonların çoğu bu pencerede alınmıştır.

#### 2.2.2.b 🔴 Yeniden ölçüm (2026-09-04 00:05) — bir satır yeniden üretilemedi

Yukarıdaki tablo **silinmemiştir** (§2.1.6 kural 4). Aynı komut bugün yeniden koşuldu:

| ay | commit'li gün | toplam commit | en yoğun gün | 2026-09-03 okumasıyla farkı |
|---|---|---|---|---|
| Mayıs 2026 | 3 | 4 | 07.05 (2) | aynı |
| Haziran 2026 | 2 | 4 | 24.06 (3) | aynı |
| Temmuz 2026 | 5 | 27 | 11.07 (16) | aynı |
| Ağustos 2026 | **26** | **418** | 26.08 (**89**) | 🔴 **tutmuyor** (27 gün / 425 idi) |
| Eylül 2026 (1–3) | 3 | 107 | 02.09 (**72**) | büyüme (yeni gün eklendi) |
| **Toplam (HEAD)** | 39 | **560** | — | 551 → 560 (büyüme) |

Ek ölçüm: `git log --all --oneline | wc -l` → **607** (tüm dallar dâhil; Ağustos 465).

#### 2.2.2.c Üçüncü ölçüm (2026-09-13, `d5bf2af5`) — 4 Eylül okuması eskidi, Ağustos donmuş durumda

Önceki iki tablo **silinmedi** (§2.1.6 kural 4). Aynı komutlar bugün yeniden koşuldu:

| ay | commit'li gün | toplam commit | 2026-09-04 okumasıyla farkı |
|---|---|---|---|
| Mayıs 2026 | 3 | 4 | aynı |
| Haziran 2026 | 2 | 4 | aynı |
| Temmuz 2026 | 5 | 27 | aynı |
| Ağustos 2026 | **26** | **418** | **aynı** — ay kapandığı için artık dondu; 4 Eylül okumasını **doğruluyor**, 3 Eylül'ün 27/425'ini **yine yanlışlıyor** |
| Eylül 2026 (1–13) | **12** | **393** | 3 gün / 107 → 12 gün / 393 (büyüme) |
| **Toplam (HEAD)** | **48** | **846** | 560 → 846 |
| **Toplam (`--all`)** | — | **1019** | 607 → 1019 (Ağustos `--all` bugün **464**, 4 Eylül'de 465 yazılmıştı) |

Ölçüm komutları (13 Eylül 2026, HEAD = `d5bf2af5`, 02:20:19 +0300):
`git log --oneline | wc -l` → **846** · `git log --all --oneline | wc -l` → **1019** ·
`git log --date=short --pretty=format:"%ad" | cut -c1-7 | sort | uniq -c` → ay dağılımı ·
Ağustos günü: `... | grep "^2026-08" | sort -u | wc -l` → **26**; Eylül günü → **12**.
Ay toplamları ile HEAD toplamı **birebir tutuyor**: 4 + 4 + 27 + 418 + 393 = **846**.

**İç tutarsızlık, gizlenmeden yazılır.** 2026-09-03 tablosunun ay toplamları
4 + 4 + 27 + 425 + 93 = **553** eder, ama aynı paragrafta toplam **551** yazılıdır; iki sayı
kendi içinde de uyuşmuyor. Bugünkü ölçümde toplam ile ayların toplamı birebir tutuyor
(4 + 4 + 27 + 418 + 107 = 560 = `git log --oneline | wc -l`).
**Bu hükmün YARISI 13 Eylül 2026'da kapandı, yarısı kayıt olarak kalıyor** — ikisi de silinmedi.

- ✅ **551 KAPANDI — yeniden üretildi.** `git log --oneline | wc -l` bugün 846 verir; 551'inci
  commit `0ac3a35a`'dır (**2026-09-03 10:42:48 +0300**) ve `git log --oneline 0ac3a35a | wc -l`
  → **551**. Yani "551 commit" uydurma değildi: 3 Eylül **sabahı** HEAD'in tam sayısıdır; kayıp
  olan yalnız **saat damgasıydı** ve o damga artık yazılıdır.
- 🔴 **425 / 27 gün YENİDEN ÜRETİLEMİYOR ve kalıcı olarak kaynaksızdır.** Aynı `0ac3a35a`
  noktasında Ağustos **418 commit / 26 gün**dür (ölçüldü); bugünkü HEAD'de de **418 / 26**,
  `--all` okumasında **464 / 26**. Hiçbir dal, hiçbir an 425 ya da 27 gün vermiyor. Komut
  çıktısı dosyaya yazılmadığı için kaynağı **kalıcı olarak kayıp**tır.

**Hüküm:** Doğru sayılması gereken, yeniden üretilebilen okumadır (bugün **846 / Ağustos 418**);
3 Eylül'ün 425/27 satırı **kayıt olarak yerinde bırakılmıştır** ve hiçbir yerde hesaba katılmaz.
**Kalıcı önlem:** her depo ölçümü bundan sonra saat damgası **ve** üreten commit sha'sı ile
yazılır (§2.1.6 kural 4'ün bu bölümdeki ikinci uygulaması).

### 2.2.3 Kilometre taşları

| tarih | kilometre taşı | kanıt |
|---|---|---|
| 2026-05-06 | Depo açıldı | `17258f8` "start project" |
| 2026-06-24 | **Model v2** — RescueNet + FloodNet, 100 epoch (Colab) | `594e1b0` |
| 2026-07-11 | Haberleşme çekirdeği: İHA→İKA/YKS açık yol aktarımı (UDP/seri, ACK+seq, heartbeat failsafe) | `d2227ef` |
| 2026-07-11 | Dürüst simülasyon zinciri (tarama → ortomozaik → model → rota → İKA) + hakem logu | `516041b` |
| 2026-07-12 | **Model v3** (yolov8s-seg): mask mAP50 **0,627**; `blocked` 0,322 → 0,403 | `4b386ce`, `results/v3_test_20260712` |
| **2026-07-15** | **DDR son teslim tarihi (şartname)** | şartname s.11 takvim tablosu |
| 2026-07-15 | Model v4 (imgsz 512 → 640; v3 reçetesi birebir) | git log 15.07 |
| **2026-07-29** | **DDR sonuçlarının açıklanması (şartname)** | şartname s.11 |
| 2026-08-05 | Jetson saha paketi ilk hâli; v17 / v20 paket modelleri | `jetson_paket/models/` dosya damgaları |
| 2026-08-13 → 08-19 | v24 → v27 → v30 → v34 model dizisi; kabul kapıları K0–K6 kuruldu | `jetson_paket/models/`, `REVIEW_LOG.md` |
| 2026-08-16 | 🔴 **Kusur ölçüldü:** `seed` eğitimi hiç etkilemiyor — v31, v30'un bit-bit aynısı (D-140); **6,4 saat GPU** karşılıksız harcandı | `REVIEW_LOG.md` D-140, D-252 |
| 2026-08-19 | Saha paketi kayıt defterini taşıyor — kılavuza göre kurulan Jetson model yükleyebiliyor (D-178/D-179) | `results/`, T103 |
| 2026-08-21 | **Model v35** üretime alındı | `jetson_paket/models/navitas_seg_v35_best.pt` |
| **2026-08-26** | **Model v36 üretime alındı — ön kayıtlı iki eşik GEÇİLMEDEN** (§4.4) | D-293, D-294, `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 |
| 2026-08-26 | Üretim karar yolu ilan edildi: `analyze_path` **üretim**, `rota_bul` **tanısal** (D-295, `CONTRACTS.md` §11.2-EK) | D-295 |
| 2026-08-27 | K7 (yayınlanan şerit doğruluğu) kabul zincirine bağlandı; v36 bozulmadan geçti | D-316 |
| 2026-08-28 | **v37 denendi ve GERİ ALINDI**: kabul zinciri geçti, gerçek arena karesi reddetti | D-332 |
| 2026-08-28 | v8 adayı: 124 epoch / **6,19 saat** eğitim → kabul zinciri **RED**; v36 üretimde kaldı | D-331 |
| 2026-09-01 | FDR görüntü işleme kanıt paketi artefakttan üretilir hâle geldi (elle sayı yazımı kaldırıldı) | `scripts/olcum/167_fdr_kanit_paketi.py` |
| 2026-09-01 | Uçtan uca kare gecikmesi ölçüldü: p95 **0,113 s** (D-382/D-383) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b |
| 2026-09-02 | Faz B araç seti: `iha_komut_alici`, `mavlink_dogrula`, `sik_rf_olc`, `ika_surucu_kabul` | D-403 |
| 2026-09-02 | **MAVLink çoğullayıcı zorunlu kılındı** — seri port tek sahipli, üç tüketici (`CONTRACTS.md` §7.4) | D-403, `FAZ_B_GUN_PLANI.md` §1 |
| 2026-09-02 | Jetson tek komutla kalkar (`jetson_baslat.sh` + 6 systemd birimi); sürüm dondurma mührü | D-404, D-405 |
| 2026-09-02 | Tam test suiti **1827 test** ile kapandı | D-407 §3, `REVIEW_LOG.md`:28298 |
| 2026-09-03 | Cuma öncesi kapı koşumu: genel kapı **15/15 · 15/15**, tam suit **1875 test OK** (skipped 3), kuru koşu **9 GEÇTİ / 1 SAHİPSİZ** (yalnız `motor`) | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` |
| 2026-09-03 | Saha belleği üretildi: **405 dosya · 1,27 GB** (`MANIFEST.txt` sha256 + git HEAD) | `scripts/bellek_hazirla.py`, `results/faz_b_oncesi/CUMA_KONTROL_KARTI.md` §A |
| 2026-09-02 | **YKS FDA görev kipi** (`--fda`) — 21 Eylül'de hakem onayını imkânsız kılan kilit kaldırıldı | D-408, `CONTRACTS.md` §6.7 |
| 2026-09-03 | Jetson **Nano 4GB** yığını (14/14 aarch64 çevrimdışı tekerlek), kamera köprüsü, ArduCopter parametre + görev şablonu | D-406, D-407 |
| 2026-09-03 | 🔴 **Takvim kusuru bulundu ve kapıyla kilitlendi:** 21 Eylül FDR **teslim** günüdür, uçuş günü değildir; hata plan/runbook/CONTRACTS/FDR bölümlerine yayılmıştı | D-410, `tests/test_fdr_takvim_kapisi.py` (4 test) |
| 2026-09-03 | **Donanım beyanı değişti:** Nano taşıyıcı kartta microSD yuvası **yok**, M.2 **var** → planın bir adımı geçersiz oldu | D-413, `SAHA_HAZIRLIK_PLANI_20260903.md` §4 |
| 2026-09-03 | **YKS PC kurulumu R5 tarafından üstlenildi ve uçtan uca koşturuldu** (`yks_gui --demo --fda --otokaydet 14 --kapat` → exit 0) | D-414, `results/yks_kurulum/yks_acilis_20260903.png` |

⚠ Tablodaki *(§4.4)* çapraz atfı, bölümün yönerge iskeletine taşınmasından önceki
numaralandırmadandır; bu raporda karşılığı **§2.2.5.4 "Geçmeyen kapı"** başlığıdır. Satır,
kaynağındaki hâliyle korunmuştur.

### 2.2.4 Model sürüm soyağacı (üretim hattı)

| sürüm | paket dosyası damgası | durum | not |
|---|---|---|---|
| v2 | 2026-06-24 (git) | tarihsel | ilk Colab eğitimi |
| v3 / v4 | 2026-07-12 / 07-15 (git) | tarihsel | mask mAP50 0,627 (v3) |
| v17, v20 | 2026-08-05 | tarihsel | saha paketinin ilk modelleri |
| v21 | 2026-08-05 | tarihsel | — |
| v24 | 2026-08-13 | tarihsel | zemin kapısı eşiklerinin kalibre edildiği sürüm (D-283) |
| v27, v30 | 2026-08-14 / 08-15 | tarihsel | v31, v30'un bit-bit kopyası çıktı (D-140) |
| v34 | 2026-08-19 | **yedek aday** | tam sha `config/model_registry.json` `_yedek_surumler` |
| v35 | 2026-08-21 | **yedek aday** | v36'dan farklı hata yapar: arena K3/K4/K6'da daha iyi |
| **v36** | **2026-08-26** | **ÜRETİM** | `navitas-seg-v36-512`, sha256 `1d1caca6…c46911` |
| v37 | 2026-08-28 | **geri alındı** | gerçek arena karesi reddetti (D-332) |
| v8 (gece_v8) | 2026-08-28 | **reddedildi** | kabul zinciri RED (D-331) |

⚠ **DOĞRULANDI ve sınırı çizildi (13 Eylül 2026).** v17–v36 satırlarındaki damgalar
`jetson_paket/models/` içindeki dosya değiştirme zamanlarıdır; bunlar **saha paketine
kopyalanma / dışa aktarım** anıdır, eğitimin bittiği an değildir — bu okuma **doğrudur** ve
depo ölçümüyle desteklenir. Yordam ve ham çıktı: `ls -d results/*export*` → **8 dizin**
(`onnx_export_smoke` · `_v17_20260805` · `_v24_20260813` · `_v27_20260814` · `_v30_20260815` ·
`_v34_20260819` · `_v35_20260821` · `_v36_20260826`); bu damgalar `ls -la jetson_paket/models/`
çıktısındaki `.pt` değiştirme zamanlarıyla **gün gününe eşleşiyor**.

🔴 **Sınır — eşleşme yalnız 7 sürüm içindir** (v17, v24, v27, v30, v34, v35, v36). Tabloda geçen
**v20 ve v21** için `results/` altında **dışa aktarım klasörü YOKTUR**; o iki satırın 2026-08-05
damgası yalnız `.pt` dosya `mtime`'ına dayanır (v20: 07:48, v21: 17:48) ve bağımsız kaydı yoktur.

🔴 **Eğitim bitiş zamanları bu depodan TÜRETİLEMEZ ve bu kalıcıdır.** Arama yordamı:
`ls -d results/*train* results/*egit* results/*runs* results/terfi*` → yalnızca
`results/etiket_denetimi_train` (etiket denetimi, eğitim koşumu değil) ve `results/terfi_v36`
(terfi/değerlendirme). **Epoch/metrik logu taşıyan bir eğitim koşum klasörü depoda yoktur** —
eğitimler Colab'de koşmuştur ve koşum logları depoya hiç girmemiştir; "ayrıca çıkarılmalıdır"
borcunun karşılığı yoktur. **Hüküm: tablodaki damgalar paketleme anlarıdır ve rapor boyunca öyle
okunur; eğitim bitiş anı ÖLÇÜLEMEDİ (kaynak depo dışı) — tahmin edilmez.** Elde olan tek eğitim
süresi ölçümleri ayrı kanıtlardır: v8 adayı 124 epoch / **6,19 saat** (D-331) ve v31 = v30
bit-bit kopyasında karşılıksız harcanan **6,4 saat GPU** (D-140).

### 2.2.5 Revizyonlar ve takvime eklenen yeni iş akışları (`Y-2.2-M02`)

Şartname §5.3.1: *"Süreç boyunca meydana gelen bütün revizyonlar FDR kapsamında sunulmalıdır."*
Bu alt başlık o hükmün karşılığıdır **ve aynı zamanda yönergenin 2.2 maddesinin ikinci
yarısıdır**: aşağıdaki revizyonların her biri takvime **yeni bir iş akışı** eklemiştir; §2.2.5.5
bu iş akışlarını planın hangi gününe oturduğuyla birlikte analitik olarak yeniden değerlendirir.
Revizyonlar gizlenmemiş, gerekçeleriyle listelenmiştir.

#### 2.2.5.1 Donanım revizyonları — DDR BOM'u ile bugünkü gerçek künye

DDR aviyonik BOM'u `navitas-teknofest/references/ddr_requirements.md` içindedir (**26 satır**; numaralandırma 1…24, 26, 27 diye gider, **25 atlanmıştır** — DDR metnindeki "27" en büyük numaradır, satır sayısı değil;
beyan edilen toplam **2293 g**). Bugünkü gerçek künye kullanıcı beyanıdır
(`SAHA_HAZIRLIK_PLANI_20260903.md` §0.2, 3 Eylül 2026).

| kalem | DDR BOM (15.07.2026) | **FDR — gerçek (03.09.2026)** | revizyon gerekçesi |
|---|---|---|---|
| Uçuş kontrolcüsü | Pixhawk 6C (BOM) / **Pixhawk 6X** (DDR mimari şeması) | **Pixhawk 6C** + PM02 güç modülü | DDR'nin iki belgesi çelişiyordu (BOM 6C, `avionics_software.md` şeması 6X); gerçek donanım **6C**'dir, çelişki bu raporla kapanır |
| Görev bilgisayarı | Jetson **Orin NX** + carrier + soğutucu (180 g) | ~~**Jetson Nano 4GB** (JetPack 4.6.x, sistem Python 3.6) — 3 Eylül beyanı~~ → **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1, Ubuntu 24.04, Python 3.12; 3 Eylül beyanı 'Nano 4GB' 6 Eylül'de kartla YANLIŞLANDI — D-431) | Tedarik. 3 Eylül'de sonucu ağır sanıldı (`ultralytics` Py ≥ 3.8 → ayrı Python 3.8 venv + çevrimdışı tekerlek zinciri, Bölüm 5 §5.2.7); 6 Eylül'de kart Python 3.12 ve apt'te TensorRT 10.16 ile geldi, cp38 zinciri kullanılmadı, `~/venv312` + GPU torch 2.11 kuruldu |
| GNSS | Holybro **M10** GPS + pusula (32 g) | **Holybro M9N** | Tedarik |
| Kamera | **Arducam** IMX477 12MP (50 g) | **Raspberry Pi HQ** (IMX477, CSI) + standart lens | Aynı sensör (IMX477), farklı kart. **FOV — HESAP (lens + sensör geometrisi), ölçüm DEĞİL; girdisi de BEYAN.** Girdiler: IMX477 aktif alan **6,287 × 4,712 mm** (veri sayfası) ve **f = 6 mm** — bu odak uzaklığı **kullanıcı beyanıdır ve koşulludur** (`SAHA_HAZIRLIK_PLANI_20260903.md:46`: *"RPi'nin standart 6 mm geniş açı lensi **ise**"*); kamera 13 Eylül itibarıyla **elde yok** (D-471) ⇒ lens **doğrulanmadı**. Türetme: yatay `2·atan(6,287/12)` = **55,3°**, dikey `2·atan(4,712/12)` = **42,9°**, köşegen **66,4°**; 30 m'de nadir (90°) kare **31,4 × 23,6 m**. ⚠ **Depodaki eski hesap 55–63° / 31–37 m** (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:284`, `FDR/BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md:84`, `FDR/BOLUM_1_OZET.md:499`, `FDR/ACIK_KALEMLER.md:29`) — bu satır **aralığın en dar ucunu** (en kötü durum) kullanır; **aksi hâlde raporda iki farklı FOV kalır** → açık kalem: dört yerdeki aralık bu türetmeyle hizalanacak. Hüküm: 20 × 20 m **hesaben sığar**, ama boyuna pay yalnız **3,6 m**'dir ve bu pay merkezleme/eğim/irtifa hatasına tolerans bırakmaz. ⚠ ~~5 Eylül'de `kamera_dogrula` ile ölçülecek~~ → **5 Eylül'de ölçülmedi** (D-426 §4: Jetson araca takılmadı) → **planlanan ölçüm: `codes/kamera_dogrula.py --fov`, kamera geldiğinde, 21 Eylül 2026 uçuşu öncesi** |
| Güç dağıtımı / sensör | **Mauch PL-100** + Mauch PL 4-6S BEC + ayrı PDB | **Matek XCLASS FCHUB-12S V2** (PDB + akım sensörü) + **PM02** | Tedarik + sadeleştirme; akım ölçümü PM02'ye taşındı (`BATT_MONITOR=4`) |
| RC alıcı | TBS **Crossfire** Nano RX | **FlySky FS-i6** + FS-iA6B (**iBUS**) | Tedarik. Yazılım etkisi: `RC_PROTOCOLS` iBUS'a alındı (parametre dosyası, TEYİT listesinde) |
| Motor | SunnySky X2216 V3 1100KV ×2 (sabit kanat) | ~~**5008 340KV ×4** + 12×10 pervane~~ → **SunnySky X2220 980KV V3 ×4** (BEYAN, etiket fotoğrafı yok) + **10×4,5 (1045)** pervane (7 Eylül beyanı, D-435) (çoklu rotor) | **Araç sınıfı farkı** — FDA aracı çoklu rotordur (§1). 7 Eylül: 5008'ler iade edildi; X2220'ler 2 yıl önce kullanılmış eski motorlar (BEYAN, D-435). **İtki bütçesi HESAP olarak türetildi — 13 Eylül, Bölüm 3 §3.2.1.1.1'in 4S satırlarından ölçeklenerek; §3.2.1.1.1'in kendisi hâlâ 4S'tir ve orası da güncellenecek (açık kalem).** Girdi: üreticinin **APC1047 (10×4,7)** satırı, 4S 14,8 V, motor başına **2130 g @ 38,4 A** (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:313`). ⚠ Araçtaki pervane **10×4,5**'tir; bu satır 10×4,5 için **DOĞRULANMADI** (`BOLUM_3:305-306`) ⇒ girdi üreticinin **farklı pervanesine** aittir. Ölçekleme (HESAP, ölçüm değil): sabit pervanede `T ∝ (V₂/V₁)²`, `(12,6/16,8)² = 0,5625` ⇒ **1198 g/motor**, 4 × = **4793 g**, %50 eşiğine denk kütle = **2396 g** (4S'teki 4260 g değil — `BOLUM_3:321`). ⚠ Bu model ESC/motor akım sınırını ve yük altında gerilim düşüşünü hesaba katmaz. 🔴 **KAPI HÂLÂ AÇIK** (`BOLUM_3:325` = **ÖLÇÜLEMEDİ**): kalkış kütlesi **ÖLÇÜLMEDİ** (T10, tartı yok) ⇒ askı itki oranı hesaplanamaz; `MOT_THST_HOVER` öğrenmedi (`emir.param:580` = 0,35 fabrika) ⇒ itki payı **ÖLÇÜLMEDİ** (D-474 §4). **Planlanan ölçüm: pilli tam araç tartısı (T10) + PM06 telemetrisinden askı akımı, 21 Eylül 2026 öncesi** |
| ESC | Hobbywing FlyFun 40A V5 ×2 | **80 A DShot destekli ×4** (ilk uçuşlarda PWM 400 Hz) | Araç sınıfı farkı |
| Pil | 4S 14000–15000 mAh Li-ion (1000 g) | ~~**1× 4S 10 Ah 25C**~~ → **1× 3S 8000 mAh** (kullanıcı kararı, gerekçe: **stabilite**), şarj iMAX B6 (50 W — BEYAN) | **Tedarik + stabilite kararı.** Kart dökümü kararı doğruluyor: `emir.param:138` `BATT_LOW_VOLT = 10` (3S × 3,33 V) ve `:131` `BATT_CRT_VOLT = 9` (3S × 3,00 V) — 4S eşikleri değil (`mevcut.param`: 14,4 / 14). 🔴 **12 Eylül dökümünde `BATT_CAPACITY = 3300` HATALI kalmıştı** (pil 6000 mAh; sayaç %45 yanılır — D-474 §3); ⚠ **13 Eylül'de kullanıcı `BATT_CAPACITY = 6000` ve `BATT_CRT_VOLT = 10,5 V` yazdı — BEYAN, yeni döküm alınmadı**, kartla teyidi T258'de (13 Eylül dökümü) kapanır. ⚠ `BATT_AMP_PERVLT = 36,36` ve `BATT_VOLT_MULT = 18,18` **PM06 fabrika değerleridir, doğrulanmadı** → akım/gerilim telemetrisi kalibre edilmeden askı akımı ölçümü geçerli sayılmaz. **Operasyonel sonucu ~~günde en fazla 2 uçuş~~ → dolum ≈ 1,5 saat, günde ≈ 4 uçuş (HESAP, açılımı ve çekinceleri §2.2.5.5)**; buna karşılık enerji **66,6 Wh** = 11,1 V × 6,0 Ah (4S 10 Ah'in 148 Wh'sinin **%45'i**) → askı süresi **≈ 8 dk (HESAP)**, 10 dk görev bütçesinin **altında** — yeni ve **ölçülmemiş** risk |
| Paraşüt zinciri (kalem 12–16) | Opale Rescue 2,5 m² + pod + servo + mekanizma + tether | **FDA aracında YOK** | §5.3.2 çoklu rotor uçuşunda paraşüt zorunlu değil; final aracında kalır |
| Servolar (kanat/kuyruk) | EMAX ES08MA II ×4 | **FDA aracında YOK** | Araç sınıfı farkı |
| Pitot + airspeed | Pitot + Holybro MS5525DSO | **FDA aracında YOK** | Çoklu rotorda hava hızı sensörü kullanılmaz |
| Telemetri | Holybro ~~SiK 433 MHz~~ RFD900A 915–928 MHz ×2 (uçak + YKS) | **2× ~~SiK 433 MHz~~ RFD900A 915–928 MHz** — değişmedi | — |
| Acil güç kesme | Anahtarlı stop + röle | **Anahtar yok — pil fişi çekilir (XT60/XT90)** | 🔴 **DDR gereksinimi** REQ-25…31 — *takımın kendi* gereksinim kimliğidir (`references/ddr_requirements.md:76`); şartname metninde "REQ-" **hiç geçmez** (çift acil güç kesme) FDA aracında **karşılanmıyor**; final aracı için **açık madde** (Bölüm 6'ya taşınır). **Bugünkü sayısal hüküm: FDA aracında fiziksel acil güç kesme donanımı sayısı = 0**; tek yol pil fişinin (XT60/XT90) elle çekilmesidir ve bu **araç yerdeyken** işler. ⚠ **Karıştırılmaması gereken ayrım:** `emir.param:735` `RC6_OPTION = 153` (**ArmDisarm**, `config/pixhawk/PARAMETRE_KILAVUZU_1SAYFA.md` §2) vardır — bu **yazılımsal disarm anahtarıdır**, güç kesme değildir; havada disarm'ı ArduPilot zaten reddeder. REQ-25…31'in istediği **çift** fiziksel kesme yolu bununla karşılanmaz. Bu bir tedarik/tasarım borcudur; ölçülemez, türetilemez. **Planlanan tasarım: final aracı acil güç kesme (röle + anahtar) şeması, sabit kanat üretim dalgasıyla — 30 Eylül 2026 sonrası** |
| Gövde | (DDR: sabit kanat yapısal malzeme dağılımı) | **3B baskı quadcopter** (ABS + ABS-CF) | Araç sınıfı farkı; ayrıntı Bölüm 5 |

#### 2.2.5.2 Yazılım ve mimari revizyonları

| konu | DDR'de beyan / plan | **FDR — bugünkü gerçek** | kanıt |
|---|---|---|---|
| Model | YOLOv8-seg **nano**, NCNN, conf > 0,40 (DDR akış şeması) | **YOLOv8m-seg**, `navitas-seg-v36-512`, PyTorch; conf 0,30 | `config/model_registry.json`, `navitas-teknofest/references/avionics_software.md` |
| Hızlandırma | TensorRT `.engine` (Jetson'da derlenir) | ~~**Nano'da ÖLÇÜLEMEDİ** — venv38'de `tensorrt` modülü yok (JetPack 4.6 bağı Py3.6). PT/ONNX ile uçulur~~ **6 Eylül (D-431, Orin Nano, TensorRT 10.16.2):** `.engine` `.pt`'den **derlendi** (57 283 989 B, sha256 `bb9bd868…0300`, deftere yazıldı); FPS engine 1,58/1,33 · pt 1,35/1,06 GEÇTİ; engine↔pt **D-303 oransal 3/126 DÜŞTÜ** → **uçuş `.pt`**, engine üretime alınmadı | `jetson_paket/JETSON_ORIN_NANO_KURULUM.md` §4–§5, §8 |
| Rota karar yolu | tek yol varsayımı | **İki yol ayrıldı:** `analyze_path` üretim, `rota_bul` tanısal | D-295, `CONTRACTS.md` §11.2-EK |
| Pixhawk erişimi | doğrudan seri | 🔴 **Çoğullayıcı zorunlu** — seri port tek sahipli, üç tüketici ayrı UDP ucundan okur | D-403, `CONTRACTS.md` §7.4 |
| Kamera yolu | doğrudan `VideoCapture` | **Kamera köprüsü** (sistem Python + GStreamer `nvarguscamerasrc` → MJPEG/HTTP; 3 Eylül'de 'Python 3.6' sanılıyordu, kartın sistem Python'u 3.12 — 6 Eylül'de köprü sistem Python 3.12 + cv2 4.6 ile **dosya kaynağında açıldı** — köprünün kendisi **çalıştığı ölçüldü** (`results/jetson_20260906/jetson_log_20260906/kamera_koprusu_dosya.log`); CSI kamera bağlı değildi → `nvarguscamerasrc` yolu **ÖLÇÜLEMEDİ**, D-431. **13 Eylül 2026 durumu: kamera (RPi HQ IMX477 + 6 mm lens, 90° nadir) elde YOK ve 14 Eylül'e yetişmiyor** (D-471) → CSI yolu bugün de ölçülemez ve türetilebilir bir sayısı yoktur. **Ölçülmüş kısmın hükmü: köprü zinciri dosya kaynağıyla uçtan uca GEÇTİ; ölçülmeyen tek halka `nvarguscamerasrc` sürücü yoludur.** **Planlanan ölçüm: `scripts/kamera_koprusu.py` CSI kaynağıyla, kamera geldiğinde — 21 Eylül 2026 uçuşu öncesi**) | D-406, `scripts/kamera_koprusu.py`; `results/jetson_20260906/jetson_log_20260906/kamera_koprusu_dosya.log` |
| Hedef Bölge (HB) dedektörü | DDR: üretime bağlanacak | **BAĞLANDI (1 Eylül 2026, D-386)** — kullanıcı renk teyidi + ölçek/şekil çifti kapısıyla; hedef **253/256** doğru pedde, ped örtülüyken **259/260 `HEDEF_YOK`** (fail-closed), karar maliyeti **sıfır**. Ara dönemdeki bağlanmama gerekçesi (gerçek pedde %0 isabet, kırmızı arabada yanlış pozitif) D-295 §2'de durur | D-295 §2 → **D-386** |
| YKS görev kipi | tek kip | **`--fda` kipi eklendi** — paraşüt/İKA kapalı, bütçe tek 10 dk | D-408, `CONTRACTS.md` §6.7 |
| Süre limitleri | belgede | **Sözleşme sabiti**: İHA 900 s, İKA 600 s, FDA operasyon 600 s | `codes/karar_sozlesmesi.py`, D-318 |

#### 2.2.5.3 Şartname resmî takvimi ile takım takvimi

| olay | şartname resmî tarihi | takım planı |
|---|---|---|
| FDR son teslim | **21.09.2026 – 17.00** | ~~rapor bu tarihe yetiştirilir~~ → **14 Eylül 2026** (takım kendi terminini **7 gün öne çekti**, D-471, 12 Eylül kullanıcı kararı). Şartname tarihi değişmedi; takım payı **7 gün**dür. 21 Eylül böylece teslim günü olmaktan çıkıp **uçuş / genel prova günü** oldu |
| FDA (FDS + Drone ile Görev Test Uçuşu) | **30.09 – 03.10.2026** | **tek atış** — `SAHA_RUNBOOK.md` başlık satırı |
| FDR sonuçları | 04.10.2026 | — |
| SGGS son teslim | 05.02.2027 | Bölüm 7'deki BOM bu sunumun temelidir |
| UHDR son teslim | 16.04.2027 | — |
| Uçuş testleri | 21.05.2027 | — |
| Yarışma | Ağustos–Eylül 2027 | — |

🔴 **Düzeltilen iç tutarsızlık.** `SAHA_HAZIRLIK_PLANI_20260903.md` §0.1, 21 Eylül Adıyaman
uçuşunu *"şartname §5.3.2"* diye etiketler. Bu **yanlıştır ve burada düzeltilir**: şartnamenin
resmî FDA penceresi 30.09–03.10.2026'dır (şartname s.11 takvim tablosu); 21 Eylül'deki Adıyaman
uçuşu takımın **kendi genel provasıdır** ve aynı zamanda FDR teslim günüdür. `SAHA_RUNBOOK.md`
başlık satırı bu doğru okumayı zaten taşır (*"kesin hazır 21 Eylül, tek atış 30 Eylül"*).
Plan belgesindeki etiket kaynağında düzeltilmemiştir (belge kaydı bozulmasın diye); rapor için
geçerli olan bu paragraftır.

**Kusurun ağırlığı ve kapatılışı (D-410).** Bu yalnızca bir etiket hatası değildi: hata
plan, runbook, `CONTRACTS.md` ve FDR bölümlerine **yayılmıştı**; yanlış kalsaydı takım 21 Eylül'e
uçuş hazırlığı yapıp **rapor teslimini kaçırabilirdi** — FDA puanının %85'i rapordur
(`FDA = FDR × 0,85 + test uçuşu × 0,15`). Tekrarı artık bir kapıyla engellenir:

```text
$ python -B -m unittest discover -s tests -p "test_fdr_takvim_kapisi.py" -v
test_T2_hicbir_belge_ucusu_21_eylule_baglamiyor ... ok
test_T3_resmi_takvim_tablosu_belgelerde ... ok
test_T4_ucus_penceresi_kaybolmadi ... ok
test_T1_sartname_iki_tarihi_soyluyor ... ok
----------------------------------------------------------------------
Ran 4 tests in 0.012s
OK
```
(Koşum: 2026-09-04, yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe`.)

#### 2.2.5.4 🔴 Geçmeyen kapı — gizlenmez

Üretim modeli **v36**, kendi **ön kayıtlı iki eşiğini geçmeden** terfi etmiştir. Ham kayıt:

```text
ON KAYITLI ESIKLER GECILMEDI: ROTA >= 10 istendi, olculen 8;
MASKE_YOK <= 10 istendi, olculen 16.
GECILEN: FP <= 1 (1) ve YANLIS GUZERGAH = 0 (0).
Terfi bu esikleri GECEREK degil, KULLANICI KARARIYLA yapildi.
ESIKLER DEGISMEDI ve sonraki terfileri baglar.
```

- **Terfi tarihi:** 2026-08-26 · **Karar mercii:** kullanıcı (takım kararı), mimar değil.
- **Gerekçe:** gerçek karede yanlış güzergâh 15/21 → 7/38; engel üstü waypoint 79 → 3.
- **Bedeli açık yazıldı:** K3 0→1, K4 1→4, K6 5→7 (kapı içinde kaldı); kaplama67 0,51→0,42.
- **Eşikler gevşetilmedi** ve sonraki terfileri bağlamaya devam ediyor (`CONTRACTS.md` §12).
- Ayrıca aynı dönemde ölçülen bir karşı kalem: `karar_cevrilmesi` ekseninde v36, v35'ten
  **kötüdür** (14/260 vs 9/260, eşli koşum). Terfi geri alınmamış, ölçüm kayda geçmiştir (D-295 §3).

Bu satır, projenin kanıt yordamının kendi aleyhine de işlediğinin göstergesidir ve raporda
bilerek öne alınmıştır.

#### 2.2.5.5 Yeni iş akışlarının analitik yeniden değerlendirilmesi

Yukarıdaki revizyonların her biri takvime **yeni bir iş kalemi** doğurmuştur. Aşağıdaki tablo,
"hangi revizyon → hangi yeni iş akışı → planın hangi gününe oturdu → kanıtı ne" zincirini kurar.

| # | tetikleyen revizyon | doğan yeni iş akışı | plandaki yeri | kanıt |
|---|---|---|---|---|
| 1 | Jetson Orin NX → ~~**Nano 4GB**~~ **Orin Nano Developer Kit 4 GB** (6 Eylül'de kartla ölçüldü, D-431) | JetPack 4.6.x + ayrı Python 3.8 venv + **çevrimdışı aarch64 tekerlek zinciri** (14/14) hazırlandı → **6 Eylül'de kartla geçersiz**: JetPack 7.2.1 / Python 3.12; kurulum kartta apt + `~/venv312` ile yeniden yapıldı, kapılar geçti | Per 3 Eyl (hazırlık) → Cmt 5 Eyl (kurulum planı) → **Paz 6 Eyl (gerçek kurulum)** | D-406, D-407; `jetson_paket/JETSON_NANO_KURULUM.md` (GEÇERSİZ bandı alacak) → D-431 |
| 2 | Arducam → **RPi HQ (CSI)** | **Kamera köprüsü** (sistem Py3.6 + GStreamer `nvarguscamerasrc` → MJPEG/HTTP) | Per 3 Eyl | D-406, `scripts/kamera_koprusu.py` |
| 3 | Seri porta tek erişim → **üç tüketici** | **MAVLink çoğullayıcı** + doğrulama aracı | Çar 2 – Per 3 Eyl | D-403, `CONTRACTS.md` §7.4, `scripts/mavlink_dogrula.py` |
| 4 | Tek görev kipi → **FDA kipi** | YKS `--fda` kipi; paraşüt/İKA düğmeleri kapalı; tek 10 dk bütçe | Çar 2 Eyl | D-408, `CONTRACTS.md` §6.7, `tests/test_faz_b_yks_fda_kipi.py` |
| 5 | microSD varsayımı → **M.2 / eMMC** (donanım beyanı düzeldi) | "microSD flash" adımı **geçersiz** oldu; yerine Ubuntu'lu host ile yazım | **Cum 4 Eyl satırı yeniden yazıldı** | D-413, `SAHA_HAZIRLIK_PLANI_20260903.md` §4 |
| 6 | 21 Eylül "uçuş günü" sanılıyordu → **FDR teslim günü** | Takvim iddiaları belge belge düzeltildi + **kapı testi** eklendi | 21 Eyl satırı + tüm belgeler | D-410, `tests/test_fdr_takvim_kapisi.py` (4/4, 2026-09-04) |
| 7 | R5 YKS rolü üstlenildi | YKS PC kurulumu + uçtan uca koşum | §1.8 (Cum 4 Eyl) → **3 Eylül'e çekildi** | D-414, `results/yks_kurulum/yks_acilis_20260903.png` |

**Analitik sonuç — 1: plan kaydırılmadı, bir satır yeniden yazıldı.** Yedi yeni iş akışından
altısı 2–3 Eylül penceresine sığdırılmış, ileri tarihli hiçbir satır ertelenmemiştir; yalnız
**5 numaralı kalem** planın bir gününü (Cum 4 Eylül) içerik olarak değiştirmiştir. Kaydırma
gerekmediğinin ölçülmüş göstergesi 3 Eylül kapı koşumudur: genel kapı **15/15 · 15/15**,
tam suit **1875 test OK** (skipped 3), kuru koşu **9 GEÇTİ / 1 SAHİPSİZ**
(`results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt`).

**Analitik sonuç — 2: uçuş bütçesi, takvimin bağlayıcı kısıtıdır.** Plan §3'ün gerektirdiği
en az uçuş sayısı, kontrol listesinden sayılabilir: 3.1 ilk hover (1) + 3.2 Loiter/Auto + iniş
kanıtı (1) + 3.3 algı canlı (1) + 3.4 tam prova ×3 (3) + 3.5 sıkı provada tekrar kalkış (≥1)
= **≥ 7 uçuş**. 🔴 **Bu hesabın pil varsayımı 12 Eylül'de değişti** (~~4S 10 Ah~~ → **3S 8000 mAh**,
stabilite gerekçesiyle, kullanıcı kararı); aşağıdaki sayılar **yeniden türetilmiştir**.

**Dolum süresi — HESAP, ölçüm değil; girdilerinin ikisi BEYAN, ikisi varsayım.** Girdiler:
(a) şarj cihazı çıkış gücü **50 W** — kaynağı `SAHA_HAZIRLIK_PLANI_20260903.md:47`,
**kullanıcı beyanı**, cihaz künyesi (B6'nın hangi varyantı) doğrulanmadı; (b) pil 3S 8000 mAh
(D-474); (c) CC evresi kapasitenin **~%80'i**; (d) CV kuyruğu **~0,3 saat** — (c) ve (d) tipik
LiPo dolum profili **VARSAYIMIDIR**, ölçüm değildir.
Türetme: 50 W sabit güçte akım gerilimle ters orantılıdır ⇒ dolumun **başında** (boşalmış 3S
≈ 10,0 V) `I = 50/10,0 =` **5,0 A**, **sonunda** (12,6 V) `I = 50/12,6 =` **3,97 A**.
⚠ Cihazın **5 A akım sınırı dolumun başında devrededir**; ortalama akım bu yüzden ≈ 4,0–4,5 A
bandında kalır. Süreyi uzatan (yani güvenli taraftaki) 3,97 A ile:
CC `0,8 × 6,0 Ah / 3,97 A =` **1,21 saat** + CV ≈ 0,3 saat ⇒ **dolum ≈ 1,5 saat** (band 1,3–1,6).
*Yöntem doğrulaması:* aynı hesap eski pile uygulandığında `50/16,8 = 2,98 A`,
`0,8 × 10 / 2,98 = 2,68 sa` + kuyruk ≈ **3,0 saat** verir ve raporun eski **~3 saat** satırını
yeniden üretir → yöntem **kalibrelidir**. Bu sayı **ÖLÇÜLMEDİ**; kapanış yolu: bir dolumun
kronometreyle ölçülmesi (açık kalem).

**Günlük uçuş sayısı — HESAP.** 8 saatlik saha günü, çevrim = uçuş ≈ 8 dk + soğuma ≈ 20 dk +
dolum 1,5 saat ≈ **2,0 saat** → `8 / 2,0 =` **günde ≈ 4 uçuş** (eskiden 2).

**Gereken en az uçuş günü.** 12 Eylül'de 1 uçuş fiilen yapıldı (A12, BEYAN), **6 uçuş kaldı**;
`⌈6 / 4⌉ =` **≥ 2 gün**. Yeni takvimde (D-471: FDR 14 Eylül, uçuş 21 Eylül) 13–20 Eylül
aralığında **8 gün** vardır. **Pay: 6 gün** (eskiden 2). İkinci pil + ≥ 150 W şarj cihazı bu payı
daha da büyütür; karar kaptandadır (`SAHA_HAZIRLIK_PLANI_20260903.md` §4 "Pil kuralı").

🔴 **Ama aynı geçiş yeni bir kısıt doğurdu ve gizlenmiyor — askı süresi.** 3S 8000 mAh enerjisi
`11,1 V × 8,0 Ah =` **88,8 Wh**, 4S 10 Ah'in (148 Wh) **%60'ı**. Veri sayfası ÖRNEK satırından
(`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md:319`) 2,5 kg için 4S'te 26 A → 3S'te
`26 × (14,8/11,1) ≈` **35 A**, güç ≈ **388 W** (+ aviyonik ≈ 25 W);
`0,8 × 66,6 Wh / 413 W ≈` **0,13 saat = ≈ 8 dk askı (HESAP)**. Şartname bütçesi **10 dk**'dır
(`codes/karar_sozlesmesi.py:2009` `SARTNAME_FDA_OPERASYON_SURESI_S = 10 * 60.0`) →
**hesaplanan askı süresi görev bütçesinin ALTINDA kalıyor.** Bu bir ölçüm değildir ve eşik
**gevşetilmez**; sonucu şudur: **ya kütle 2,5 kg'ın altına iner, ya ikinci pil / daha büyük
kapasite gerekir.** Kapanışı: pilli tartı (T10) + PM06 telemetrisinden **gerçek askı akımı**,
21 Eylül 2026 öncesi.
⚠ **HESAP (sayım) — ÖLÇÜM değil.** ~~Kaybedilen uçuş günü sayısı öngörülmemiştir~~ →
artık öngörü değil, ama bir ölçüm aleti çıktısı da değil: aşağıdaki sayı depodaki
artefaktlardan **türetilmiş bir sayımdır**, etiketi bu yüzden **HESAP**'tır.

**Sayım yordamı (açıkça).** Planlanan uçuş penceresi **5–13 Eylül = 9 takvim günü** (§2.2.6):

| planlanan gün | ne oldu | kanıt |
|---|---|---|
| Cmt 5 Eyl | **boş** — Jetson araca takılmadı, tartı ve kamera satırları alınmadı, uçuş yok | D-426 §4; `results/ucus_loglari/20260905/` **boş** |
| Paz 6 Eyl | **hedefine ulaşmadı** — 20:45–21:34 arasında 26 arm, pervaneli **3 devrilme**; FC doğru yönde düzeltti ama **ön itki yetmedi**, **M1 (sağ ön) hasarlı** | D-429 (tlog ölçümü, `results/ucus_loglari/20260906/2026-09-06 19-52-44.tlog`) |
| Pzt 7 – Cum 11 Eyl | **boş** (5 gün) — motor onarımı/teşhisi | `ls results/ucus_loglari/` → yalnız `20260905`, `20260906` |
| Cmt 12 Eyl | ✅ **hedefine ulaştı** — A12: ~3 m'de ~15 s askı + kodla LAND (BEYAN) | D-473; `ATOLYE_TEST_GUNU_20260912.md:199` |
| Paz 13 Eyl | **tamamlanmadı** — sayıma girmiyor (A6 ölçümü yapıldı, uçuş değil) | D-476 |

**Hüküm: 9 günün 6'sı tamamen boş geçti (5, 7, 8, 9, 10, 11 Eylül), 1'i hedefine ulaşmadı
(6 Eylül), 1'i ulaştı (12 Eylül), 1'i tamamlanmadı (13 Eylül) ⇒ planlanan 3 temiz provanın
0'ı koşuldu.** Plandaki ilk askı 6 Eylül'e yazılmıştı, gerçekleşen 12 Eylül → **gecikme 6 gün**.
Hava değil, **donanım arızası** (M1) baskın nedendir; §2.2.7 risk tablosunun "arıza/onarım payı"
satırı bu sayımla beslenir.
⚠ **Sayımın kendi sınırı:** boş klasör *"uçuş olmadı"*nın değil **"kayıt yok"**un kanıtıdır —
nitekim 12 Eylül uçuşunun da `results/ucus_loglari/` altında klasörü **yoktur** (`.bin` çekilmedi,
T257). Bu yüzden 6 rakamı, kanıt düzeyinde bir **kayıt yokluğu** sayımıdır.
⚠ Yukarıdaki §2.2.5.5 payı (6 gün) bu kaybı **zaten karşılıyor**, çünkü kayıp gerçekleşmiş ve
geride kalan 13–20 Eylül penceresi hesaba öyle girmiştir.

### 2.2.6 Planlanan takvim — 3 → 30 Eylül 2026

Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §4. Her satırın bir **kapısı** vardır; kapı geçilmeden
sonraki güne geçilmiş sayılmaz.

| gün | ne yapılır | rol | kapı |
|---|---|---|---|
| Per 3 Eyl | Jetson Nano yığını, kamera köprüsü, ArduCopter parametre + görev şablonu, çürütücü turu | R7, R8 | suit yeşil; dosyalar depoda ✅ |
| Cum 4 Eyl | microSD'ye JetPack 4.6.x yazımı; tekerlek + paket belleğe; YKS PC; alışveriş; **kargo teslim** | R1, R4, R5 | `results/faz_b_oncesi/` dolu; bellek hazır |
| **Cmt 5 Eyl** | **MONTAJ GÜNÜ** — kutu → mekanik → kablolama → Pixhawk → Nano kurulumu → yer zinciri (pervanesiz) | herkes | `mavlink_dogrula` 3/3; YKS'de HEARTBEAT; FPS ölçüldü |
| Paz 6 Eyl | Pusula kalibrasyonu (dışarıda); **ilk hover**; Loiter/Auto + iniş kanıtı — 2 uçuş | R2, R3, R5 | uçuş logu + `IHA_LANDED` |
| Pzt 7 – Cum 11 | Canlı algı (30 m'de OPEN_ROUTE); ilk tam prova | R2, R4, R5 | 1 tam prova ≤ 10 dk |
| Cmt 12 – Paz 13 | Tam prova ×2 | herkes | toplam 3 temiz prova |
| Pzt 14 – Çar 16 | Sıkı prova: kapalı kutudan başla, kronometre, sıfır müdahale | herkes | 0 müdahale |
| Per 17 Eyl | **Sürüm dondurma (mühür)** — bundan sonra kod değişmez | R7, R1 | künye depoda, `--dogrula` 0 |
| Cum 18 Eyl | "KESİN HAZIR" listesi baştan sona; yedek parça; taşıma kutusu | herkes | tutanak |
| Cmt 19 Eyl | Yedek gün; pil tam şarj | R2, R1 | — |
| Paz 20 Eyl | Adıyaman'a yolculuk; otelde kuru koşu | herkes | — |
| **Pzt 21 Eyl** | **Genel prova uçuşu — Adıyaman** · aynı gün **FDR son teslim (17.00)** | herkes | `results/gorev_20260921/` |
| 22–29 Eyl | Tutanak, düzeltmeler (mühür kapsamı dışında değişiklik yok) | — | — |
| **30.09–03.10** | **FDA — FDS + Drone ile Görev Test Uçuşu (şartname §5.3.2)** | herkes | **tek atış** |

⚠ **"Cum 4 Eyl" satırının güncellenmiş hâli (D-413).** Yukarıdaki satır microSD'ye yazımdan söz
eder; donanım beyanı 3 Eylül'de değişmiştir (taşıyıcı kartta microSD yuvası **yok**, M.2 **var**).
Plan belgesindeki karşılığı üstü çizilerek düzeltilmiştir: *"~~microSD flash~~ → Ubuntu'lu host
ayarla (eMMC boş çıkarsa gerekecek, D-413)"* (`SAHA_HAZIRLIK_PLANI_20260903.md` §4).
Satır kaynağında silinmemiş, düzeltilmiştir (§2.1.6 kural 4).

⚠ **Jetson satırlarının güncellenmiş hâli (D-431).** "Per 3 Eyl — Jetson Nano yığını", "Cum 4 Eyl — microSD'ye JetPack 4.6.x yazımı" ve "Cmt 5 Eyl — Nano kurulumu" satırları 3 Eylül beyanına göre yazılmıştı. 5 Eylül'de Jetson araca takılmadı (D-426 §4); **6 Eylül'de** kart açıldı ve **Jetson Orin Nano Developer Kit 4 GB** (JetPack 7.2.1 kurulu, NVMe kök, Python 3.12) çıktı — imaj yazımı gerekmedi, cp38 tekerlek zinciri kullanılmadı, kurulum kartta yapıldı; genel kapı 15/15 · 15/15 ve FPS kapısı (pt 1,35/1,06 · engine 1,58/1,33 ≥ 0,61) o gün **GEÇTİ** (`results/jetson_20260906/`). Satırlar silinmedi; kapı sütunundaki "FPS ölçüldü" 6 Eylül'e aittir.

**Takvimin ölçülmüş kısıtı:** tek pil ve iMAX B6 (~50 W → ~3 A → ~3 saat dolum) uçuş gününü
**en fazla 2 uçuşa** kilitler. İkinci pil + ≥150 W şarj cihazı prova sayısını ikiye katlar;
karar kaptandadır (`SAHA_HAZIRLIK_PLANI_20260903.md` §4 "Pil kuralı"). Bu kısıtın takvime
etkisinin hesabı §2.2.5.5'tedir.

### 2.2.7 Takvim riskleri ve karşı önlemler (ölçülmüş olanlar)

| risk | neden gerçek | önlem | durumu |
|---|---|---|---|
| **Nano yığını kurulamaz** | v36 YOLOv8m-seg'dir; Nano **CPU**'da 512'de FPS kapısı (**0,61**) düşebilir — ölçülmedi | Çevrimdışı 14/14 aarch64 tekerlek hazır; sıra: CUDA topluluk wheel → ONNX Runtime → CPU torch | açık; 5 Eylül'de ölçülecek. **Eşik gevşetilmez** |
| **Yanlış güzergâh = 0 puan** | Şartname §5.3.2 mutlak | Histerezis, tek pas tarama, hakem ekranında güven + sebep | kod hazır (D-396) |
| **10 dk aşımı** | Şartname §5.3.2 mutlak | Görev planı kötü-durum bütçesi ~3–3,5 dk (hesaplandı, `config/pixhawk/README.md`) | test ile kilitli |
| **Tek pil** | Ölçülü (10 Ah, iMAX B6) | Günde 2 uçuş planı; 2. pil kararı kaptanda | açık |
| **Gerçek arena görüntüsü yok** | Ölçüm: arena benzeri saha kanıtı **yoktur** (T111/D-198) | Sentetik + gerçek kırsal iki ayrı çerçeve olarak raporlanır; arası tahmin edilmez | **kapanmadı** |
| **Acil güç kesme anahtarı yok** | Kullanıcı beyanı §0.2 | FDA aracında pil fişi; final aracı için tasarım borcu | **açık madde** |

### 2.2.8 Bölüm 2.2'nin açık kalemleri

1. **BEYAN GEREKLİ (insan): DDR teslim tarihi/saati teyidi** — KYS teslim kaydı (§2.2.1 satır 1).
2. **BEYAN GEREKLİ (insan): DDR sonuç bildirimi ve alınan puan** (§2.2.1 satır 2).
3. **BEYAN GEREKLİ (insan): DDR proje takvimi sayfası** — depo dışı yerel yedekten; termin
   çizelgesinin tam hâli olmadan §2.2.1 yalnız üç tarih üzerinden teyit edilebiliyor.
4. **BEYAN GEREKLİ (insan): 5 Eylül kutu açılış teyidi** — §2.2.5.1'deki gerçek künye satırlarının
   her biri fiziksel parça ile karşılaştırılıp imzalanacaktır.
5. **BEYAN GEREKLİ (insan): 21 Eylül Adıyaman uçuş alanı izni** ve alan koordinatları.
6. **ÖLÇÜLEMEDİ: 2026-09-03 tarihli 551 commit / Ağustos 425 okumalarının kaynağı** — bugünkü
   depodan yeniden üretilemiyor (§2.2.2.b); kapanışı, ölçüm satırlarına saat damgası ve komut
   çıktısının dosyaya yazılmasıdır.
7. **ÖLÇÜLEMEDİ: kanıt defteri okumalarının saati** (§2.1.6, A/B okumaları); aynı kapanış.
8. **ÖLÇÜLEMEDİ: Nano'da FPS** (kapı 0,61) — 5 Eylül montaj gününde ölçülecek (§2.2.7).

---

## Kanıt dizini (Bölüm 2)

| # | sayı / iddia | dosya yolu | üreten betik / komut | ölçüm tarihi |
|---|---|---|---|---|
| 1 | 551 commit (3 Eylül gecesi), ilk commit 2026-05-06 `17258f8` | `O:\navitas\.git` | `git log --date=short --pretty=format:"%ad\|%h\|%s"` | 2026-09-03 |
| 2 | Gün başına commit dağılımı (26.08 → 89, 02.09 → 72) | `O:\navitas\.git` | `git log … \| awk -F'\|' '{print $1}' \| sort \| uniq -c` | 2026-09-03 |
| 3 | Model dosyası damgaları v17…v36 | `jetson_paket/models/` | `ls -la jetson_paket/models/` | 2026-09-03 |
| 4 | Üretim modeli künyesi (`navitas-seg-v36-512`, imgsz 512, sha256 `1d1caca6…`) | `config/model_registry.json` → `profiles.competition` | `scripts/olcum/167_fdr_kanit_paketi.py` | 2026-09-01 |
| 5 | v36 ön kayıtlı eşiklerin geçilmediği ham metin (ROTA 8 < 10; MASKE_YOK 16 > 10) | `results/fdr/GORUNTU_ISLEME_KANIT.md` §3 | `scripts/olcum/167_fdr_kanit_paketi.py`; dayanak D-293/D-294 | 2026-08-26 (karar) / 2026-09-01 (paket) |
| 6 | `karar_cevrilmesi` v36 14/260 vs v35 9/260 | `REVIEW_LOG.md` D-295 §3 | eşli koşum, ON_KAYIT §16 | 2026-08-26 |
| 7 | v37 geri alındı; v8 adayı RED (124 epoch / 6,19 saat) | `REVIEW_LOG.md` D-332, D-331 | kabul zinciri `scripts/olcum/65_kabul_denetcisi.py` | 2026-08-28 |
| 8 | v31 = v30 bit-bit aynısı; 6,4 saat GPU karşılıksız | `REVIEW_LOG.md` D-140 (alıntı D-252:19148) | eğitim koşumu kıyası | 2026-08-16 |
| 9 | Uçtan uca kare gecikmesi p95 0,113 s | `results/fdr/GORUNTU_ISLEME_KANIT.md` §4.1b | D-382/D-383 ölçümü, 33 ölçülen gerçek kare (+3 ısınma) | 2026-09-01 |
| 10 | Tam suit 1827 test | `REVIEW_LOG.md`:28298 (D-407 §3) | `python -B -m unittest discover -s tests -q` | 2026-09-02 |
| 10b | Genel kapı 15/15 · 15/15; tam suit 1875 OK (skipped 3); kuru koşu 9 GEÇTİ / 1 SAHİPSİZ | `results/faz_b_oncesi/cuma_kontrol/cuma_kontrol.txt` | `codes/test_rota_sentetik.py`, `unittest discover`, `scripts/saha_kuru_kosu.py` | 2026-09-03 |
| 11 | Kanıt defteri 414 başlık / 408 benzersiz kayıt | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+"` ve `\| sort -u \| wc -l` | 2026-09-03 |
| 12 | Şartname resmî takvimi (ÖDR/DDR/FDR/FDA/SGGS/UHDR tarihleri) | `results/sartname_bosluk/sartname_metin.txt` s.11 | PyMuPDF metin çıkarımı (`rapor_uret.py`) | 2026-08-26 |
| 13 | FDR puan tablosu (Tablo 4) ve FDA formülü (FDR×0,85 + uçuş×0,15) | `results/sartname_bosluk/sartname_metin.txt` §5.3.1–5.3.2 | aynı çıkarım | 2026-08-26 |
| 14 | DDR aviyonik BOM'u (**26 satır**, en büyük numara 27, toplam 2293 g) | `navitas-teknofest/references/ddr_requirements.md` | DDR dönemi Excel aktarımı — **DOĞRULANACAK** | 2026-07 (tarih damgası yok) |
| 15 | DDR mimari şemasında "Pixhawk 6X" / "Jetson Orin NX" / "M10" | `navitas-teknofest/references/avionics_software.md` | — | 2026-07 |
| 16 | Gerçek donanım künyesi (Pixhawk 6C, M9N, ~~Nano 4GB~~, FCHUB-12S, 5008 340KV, RPi HQ, 4S 10 Ah) | `SAHA_HAZIRLIK_PLANI_20260903.md` §0.2 | **kullanıcı beyanı**, 3 Eylül 2026 — ~~kutu 5 Eylül'de açılıp teyit edilecek~~ → 5–6 Eylül'de kutu açıldı: Jetson **Orin Nano Developer Kit 4 GB** (beyan yanlışlandı, D-431), ESC Skywalker 60A V2, PM06 (D-426); motor ~~5008 340KV~~ → SunnySky X2220 980KV V3 + 10×4,5 (BEYAN, etiket yok — 7 Eylül, D-435) | 2026-09-03 → 2026-09-07 |
| 17 | Planlanan 3–21 Eylül takvimi | `SAHA_HAZIRLIK_PLANI_20260903.md` §4 | — | 2026-09-03 |
| 18 | FDA görev kipi sözleşmesi (`--fda`) | `CONTRACTS.md` §6.7 · `REVIEW_LOG.md` D-408 | `tests/test_faz_b_yks_fda_kipi.py` (9 test, 4/4 mutant) | 2026-09-02 |
| 19 | MAVLink çoğullayıcı zorunluluğu | `CONTRACTS.md` §7.4 · `FAZ_B_GUN_PLANI.md` §1 | `scripts/mavlink_dogrula.py` | 2026-09-02 |
| 20 | Süre sözleşme sabitleri (900 / 600 / 600 s) | `codes/karar_sozlesmesi.py` · `CONTRACTS.md` §7.1 | `REVIEW_LOG.md` D-318 | 2026-08-27 |
| 21 | DDR termin planı: DDR teslim 15.07.2026 · DDR sonuç 29.07.2026 · FDR 21.09.2026 | `navitas-teknofest/references/ddr_requirements.md:3–6` | doğrudan okuma (`grep -n "Kritik Takvim" -A 6`) | 2026-09-04 |
| 22 | DDR'nin depoya bakan izi: son sürüm v4.3 (`f4d1583`, 12.07) ve belgenin depo dışına alınışı (`38798f2`, 12.07) | `O:\navitas\.git` | `git log --date=short --since=2026-07-10 --until=2026-07-31` | 2026-09-04 |
| 23 | Takvim kapısı **4 test / 4 OK** (21 Eylül = FDR teslim, uçuş değil) | `tests/test_fdr_takvim_kapisi.py` · `REVIEW_LOG.md` D-410 | `python -B -m unittest discover -s tests -p "test_fdr_takvim_kapisi.py" -v` | 2026-09-04 |
| 24 | Depo yeniden ölçümü: **560 commit** (HEAD) · 607 (`--all`) · Ağustos 26 gün / 418 commit | `O:\navitas\.git` | `git log --oneline \| wc -l`; `git log --date=short --pretty=format:"%ad" \| sort \| uniq -c` | 2026-09-04 00:05 |
| 25 | Kanıt defteri yeniden ölçümü: **424 başlık / 418 benzersiz** | `REVIEW_LOG.md` | `grep -cE "^### D-[0-9]+"`; `grep -oE "^### D-[0-9]+" \| sort -u \| wc -l` | 2026-09-04 00:06 |
| 26 | YKS PC kurulumu uçtan uca koştu (exit 0); R5 rolü üstlenildi; R2/R5 çakışması açık kalem | `REVIEW_LOG.md` D-414 · `results/yks_kurulum/yks_acilis_20260903.png` | `yks_gui --demo --fda --otokaydet 14 --kapat` | 2026-09-03 |
| 27 | Donanım beyanı düzeltmesi: Nano taşıyıcıda microSD **yok**, M.2 **var** → plan adımı geçersiz | `REVIEW_LOG.md` D-413 · `SAHA_HAZIRLIK_PLANI_20260903.md` §4 | kullanıcı beyanı + plan düzeltmesi | 2026-09-03 |
| 28 | İsim yasağının bulunuşu ve raporun yönerge iskeletine alınışı | `REVIEW_LOG.md` D-417 · `FDR/YONERGE_HARITASI.md` | resmî yönerge metni `results/fdr_sablon/fdr_yonerge_metin.txt` | 2026-09-03 |
| 29 | Yönergenin Bölüm 2 / 2.1 / 2.2 metni (birebir alıntılar) | `results/fdr_sablon/fdr_yonerge_metin.txt` | pypdf metin çıkarımı | 2026-09-03 |
