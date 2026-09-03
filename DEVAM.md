# DEVAM NOKTASI — 3 Eylül 2026, 20:40

> "devam" dendiğinde buradan sürülür. Son commit: `95a5710`.
> ⚠ **42 dosya commit'lenmemiş** + **iki worktree birleştirilmeyi bekliyor**.
> Commit atılmadı çünkü süit kırmızıydı; düzeltmeler geldi ama **ana ağaca
> alınmadı** (kullanıcı çıkarken tur bitti).

## İLK İŞ — iki worktree'yi birleştir

Her ikisi de **bitti, çürütücüden geçti, ana ağaca ALINMADI.**
⚠ Worktree'ler bayat tabandan açılıyor; ajanlar ana ağacın kirli dosyalarını
kopyaladı. **Bütün worktree'yi ALMA** — `cmp` ile gerçek deltayı bul.

### 1. `wf_b62ddbf3-986` — uçuş komut hattı (EN ÖNEMLİ)
Worktree: `.claude/worktrees/wf_b62ddbf3-986-1`
Delta: `comms/iha_komut_alici.py` · `jetson_paket/kod/iha_komut_alici.py` ·
`tests/test_iha_komut_saat_ve_tekrar.py` (YENİ, 18 test)

**Düşen 2 uçtan uca testin kökü ikili aramayla ölçüldü: K-3, tek başına.**
Deney A (K-3 kapalı) → 23 test OK · Deney B (K-2 kapalı) → hâlâ 2 düşük ·
Deney C (K-1 kapalı) → hâlâ 2 düşük. Kök neden logdan:
`COMMAND_ACK yabancı component=1 (beklenen 3)` — test alıcısı
`HEDEF_COMPONENT = 3` ile açılıyor, sahte Pixhawk gerçek ArduPilot gibi
component **1** basıyor; eski kod `srcComponent`i (kim cevapladı)
`target_component` ile (kime gönderdim) eşitliyordu.

Onarımlar:
- **K-3:** kapı kaldırılmadı, ölçtüğü küme düzeltildi. `_ack_basabilen_bilesenler(m)`
  yetkili kümeyi açıkça yazıyor: `0` (belirtilmemiş), `MAV_COMP_ID_AUTOPILOT1`,
  `target_component`. Gimbal/kamera/companion **hâlâ reddediliyor**.
- **K-2:** `_komut_sonuclari[anahtar] = False` aktarımdan önceki yerinden alındı,
  `_komut_ack_bekle` **döndükten sonraya** taşındı (`= bool(kabul)`). Terminal
  olan şey artık **MAVLink'e ulaşmış** denemedir; ulaşmamış teşebbüs anahtarı
  zehirlemiyor → D-02/K4 tekrar merdiveni yaşıyor.
  ⚠ ACK timeout'u **bilerek terminal bırakıldı** (COMMAND_LONG tele çıkmıştır);
  bunu kilitleyen mevcut test **değiştirilmedi**.
- **K-1:** kapı kaldırılmadı, doğru büyüklüğü ölçer oldu. Saat ofseti kayan
  pencerede **minimum-ham-fark** (NTP min filtresi) ile kestiriliyor;
  `yas = ham − ofset`. Yeni adlandırılmış sabitler (çıplak sayı yok):
  `KOMUT_SAAT_OFSETI_EN_AZ_ORNEK=2`, `KOMUT_SAAT_OFSETI_PENCERESI_S=60.0`,
  `KOMUT_SAAT_SAPMA_TAVANI_S=30*60`. Üç güvenlik şartı koda yazıldı: çerçeve
  kendi örneğini kestirime katamaz · ofset biliniyorken **reddedilen** çerçeve
  kestirimi kaydıramaz · bant dışı çılgın damga örnek alınmaz.
  🔴 **Ajan kendi ilk uygulamasında kusur buldu ve ölçtü**: ısrarlı ileri damgalı
  bir kaynak ofseti kendi üzerine çekip kapıdan geçiyordu; 1. ve 2. şart eklendi.
- **AYNA GÜNCELLENDİ** — `jetson_paket/kod/iha_komut_alici.py`. Kritik: Jetson'da
  koşan dosya paket kopyasıdır; yalnız `comms/` düzeltilseydi **düzeltme sahaya
  hiç ulaşmazdı**.

Kanıt: `test_faz_b_iha_komut_alici` **23 OK** (önce 2 düşük) · `test_iha_rtl_land`
6 OK · `test_iha_komut_guvenligi` 10 OK · `test_p1_canli_mavlink` 17 OK ·
`test_faz_b_seri_hub` 31 OK · `test_jetson_comms_paketi` 7 OK ·
`test_faz_b_jetson_baslat` 42 OK · genel kapı **15/15 · 15/15** ·
yeni kilit testleri **18 OK** · 3 mutant, hepsi yakalandı, `cmp` bayt-eş.

⚠ Ajan **ön-varolan** bir düşük bildirdi (kendisinin değil, ölçtü):
`test_t202_jetson_paket_butunlugu::test_KULLANILAN_HER_YOL_KURULUYOR` —
`models/navitas_seg_v17/v35/v36*` dosyaları kurulum bloğunda yok (D-352).
Düzeltmeyi geri alıp aynı kapıyı koşmuş, **birebir aynı** düşmüş.

### 2. `wf_dce95c66-485` — YKS kanıt kilidi + olay kümesi + CONTRACTS §6.8
Worktree: `.claude/worktrees/wf_dce95c66-485-1`
Delta: `comms/yks_gui.py` · `CONTRACTS.md` · `tests/test_yks_hakem_kanit_olaylari.py`

- **Kanıt kilidi fail-open kapandı.** `_kanit_kilidi_var()` tek gerçek;
  `_firlat_dugmesini_ciz` / `_onay_dugmesini_ciz` `btn_firlat`/`btn_onay`
  state'inin **tek yazarları** (AST kapısıyla bağlandı). Eylem düzeyinde de
  reddediliyor: `firlatma()` kronometre başlatmaz, `onayla()` link'e ACK yazmaz.
  **Niyet korundu:** ARM/RTL/LAND kanıt kaydı bozukken de kullanılabilir —
  M3 mutasyonu bunu **ters yönde** ölçtü.
- **Mükerrer iş birleştirildi.** wt-2 tasarımı Codex sürümünün üzerine taşındı:
  `KANIT_OLAYLARI` 16 olay, `KANIT_TEKRAR_ARALIGI_S = 30.0`. Codex'in
  `KAMERA_DURUMU`/`TELEMETRI_ORNEGI` yolları **silinmedi**, taşındı.
  "Üç ayrı `_kanit_yaz`" uyarısı kontrol edildi → **1 tanım**.
- **CONTRACTS §6.8** — 16 satırlık olay tablosu + üç yönlü küme eşitliği
  (CONTRACTS ↔ sabit ↔ AST ile koddan toplanan adlar).
- ⚠ **fsync sorunu da kapandı**: kenar + 30 s aralık sınırlaması (önce 185 fsync/dk).
- wt-2'nin **başlık çakışması** düzeltmesi bilerek taşınmadı — **açık kusur**.

Kanıt: yeni kapı **22 test OK** · regresyon 8 modül OK · 6 mutasyon yakalandı ·
uçtan uca `--demo --fda` exit 0, üretilen `hakem_log.jsonl` **18 satır, 9 farklı
olay adı** (önce yalnız `YKS_ARAYUZ_HAZIR` vardı).

⚠ Ajan geniş taramada 9 düşük gördü ve **kendisine ait olmadığını kanıtladı**
(dosyaları ana ağaç tabanına koyup aynı 9 düşüğü aldı; sebep worktree bayatlığı,
`data/arena_kompozit/images` worktree'de yok). Birleştirmeden sonra ana ağaçta
bunlar **çıkmamalı** — çıkarsa dur.

## Birleştirme sırası

1. `wf_b62ddbf3-986-1` → 3 dosya (`cmp` ile doğrula)
2. `wf_dce95c66-485-1` → 3 dosya (`cmp` ile doğrula)
3. **wt-1** (`.claude/worktrees/wf_b0f33806-4ba-1`) — tek-yazar kilidi + T204/T205.
   Tek çatışma `iha_komut_alici.py` **import bloğu** (Codex 5 sabit, wt-1 3 ad —
   birleşimi aşikâr). Artık komut hattı işi bittiği için sıra bunda.
4. `scripts/jetson_paket_hazirla.py` koş (aynalar **3 yollu birleştirilmez**)
5. Tam süit → yeşil olmalı → **commit + push**

## Ağacın son ölçülen hâli

| ölçüm | değer |
|---|---|
| Genel kapı | ✅ 15/15 · 15/15 |
| Tam süit (birleştirme ÖNCESİ) | 🔴 1954 test, 2 düşük — bu ikisi yukarıda kapatıldı |
| Defter | D-417, D-418 yazıldı · bütünlük 13/13 · ad kapısı 3/3 |

## ✅ Bu oturumda kapananlar

**Codex'in ~2200 satırlık işi korundu**, 12 düşüğü mimar kapattı (8 ayna
bayatlığı + 4 canlı MAVLink; ikincisinde kusur süzgeçte değil **test
sahtesindeydi** — `sahte_pixhawk.py` `source_component` vermiyordu).
Amelelere verilip kapanan 2: ARM/DISARM teyit metni takılı kalması (ajan aynı
sınıftan **ikinci kusur** buldu: `parasut()` zamanlayıcısı uçuştaki PARACHUTE
metnini eziyordu) ve K6 `KeyError: 'YKS_IP'`.

**Çatışmasız iki kazanç ana ağaca ALINDI:**
- **wt-4 H1c** → `h1c_siniflandirilamayan = 0`; `main()` çıkış kodu artık H1c'yi
  de şart koşuyor (kapı **sıkıldı**). 23 test OK. **Açık kalem #24 kapanabilir.**
- **wt-3 Python 3.6 beyaz listesi** → 3 yollu birleştirme 0 çatışma, 12 test OK.

**FDR yönergeye taşındı (temel)** — D-417.

## Sonraki adımlar (birleştirmeden sonra)

6. FDR bölümlerinin yönerge iskeletine taşınması (`wf_5016c26d-8b5`) — betiğe
   kanıt koruma yordamı eklendi, **temiz yeniden koşulacak** (önceki tur
   BOLUM_7'den 13, BOLUM_1'den 3 kanıt satırı düşürmüştü)
7. `YONERGE_HARITASI.md` DURUM sütununu yeniden ölç
8. D-419 defter kaydı: bu iki onarım turu

## Kullanıcının beklediği

- **`FDR/` klasörünü ortak sürücüye yükleyecek.** Bölümler hâlâ eski iskelette;
  yükleme öncesi taşıma bitmeli. Kapak/harita/prompt hazır.
- Cumartesi 5 Eylül montaj. Yazılımdan tıkayan iş yok.

## Açık uyarılar

- ⚠ **Codex her an yazabilir.** Ölçüm penceresinde ağaç hareket etti (21 → 27).
  Birleştirmeden önce `git status` ve mtime kontrol et.
- ⚠ Ön-varolan düşük: `test_t202_jetson_paket_butunlugu` (model dosyaları kurulum
  bloğunda yok, D-352) — komut hattıyla ilgisiz, ölçüldü.
- ⚠ YKS başlık çakışması (`HAZIRLIK` etiketi) hâlâ **açık**.
- 🔴 Saha belleği bayat — cuma `bellek_hazirla.py` koşulmadan USB'ye kopyalanmaz
- 🔴 Jetson: microSD YOK, eMMC modül + M.2. Cumartesi ilk iş **aç ve bak**;
  eMMC boşsa **Ubuntu x86_64 host** gerekir (D-413)
- 🔴 Kol 1–2 / kol 3–4 farklı reçetelerle basıldı, gerekçesi kayıtta yok;
  yönerge "gerekliliği ispatlanmamış değişiklikler diskalifiye sebebi" diyor
