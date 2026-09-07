# CUMA AKŞAMI KONTROL KARTI — 4 Eylül (yazdırılacak)
> **7 Eylül 2026 notu (D-435 · T211):** bu kart 5008 340KV / 12×10 dönemine aittir (satır «Yedek pervane seti (12×10, CW+CCW)»); 7 Eylül beyanıyla motor ~~5008 340KV~~ → SunnySky X2220 980KV V3 ×4 (BEYAN, etiket fotoğrafı yok), pervane ~~12×10~~ → 10×4,5 (1045) — yedek set de 1045 olmalı; itki bütçesi ÖLÇÜLEMEDİ (`FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` §3.2.1.1.1). Kartın geri kalanı tarihli kayıttır, değiştirilmedi.

> Cumartesi sabahı kutu açılmadan önce bu kartın **tamamı** işaretli olmalı.
> Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §1 · ölçüm çıktıları:
> `results/faz_b_oncesi/cuma_kontrol/`

## A. Yazılım kapıları — **4 Eylül 02:30, TAMAMI YEŞİL**

> ⚠ 4 Eylül'de ~2200 satır kod değişti (Codex + altı worktree birleştirmesi);
> 3 Eylül ölçümleri **geçersizdi** ve bu tablo baştan üretildi. Artefaktlar:
> `results/faz_b_oncesi/cuma_kontrol/*_0904.txt`

| ✓ | kapı | sonuç (4 Eylül) |
|---|---|---|
| ✅ | Genel kapı `codes/test_rota_sentetik.py` | **15/15 · 15/15**. ⚠ Bu kapı `tests/` altında **değildir**, tam süit onu **kapsamaz**; ayrı koşulur (D-415) |
| ✅ | Tam test paketi | **2104 test OK** (skipped 3, 393,1 s, çıkış 0) · artefakt `cuma_kontrol/tam_suit.txt`. Sabah 1896'ydı; gece boyunca 208 test eklendi (uçuş komut hattı, hakem kanıt olay kümesi, saat kilidi, runbook kapısı) |
| ✅ | Kuru koşu `scripts/saha_kuru_kosu.py` | **9 GEÇTİ · 0 DÜŞTÜ · 1 SAHİPSİZ** · `kuru_kosu_0904.txt`. Sahipsiz halka `motor`: gerçek İKA motor sürücüsü yok — **FDA uçuşunda gerekmez**, final aracında gerekir (T149). Çıkış 1 (kopuk halka nedeniyle, beklenen) |
| ✅ | `saha_baslat.py --komutlar` | `--iha <JETSON_IP>:5007` yerinde (D-403) · `saha_baslat_0904.txt` |
| ✅ | Jetson açılış `jetson_baslat.sh --kuru` **udp** | exit 3 (PC'de beklenen) · `--izinli-kaynak 192.168.1.10:5005` · `--streamrate 8` · uçlar 14550/14551/14552 · `jetson_udp_0904.txt` |
| ✅ | Jetson açılış **sik** | exit 3 · `--izinli-kaynak 127.0.0.1:5100` (seri hub ucu) · `jetson_sik_0904.txt` |
| ✅ | Paket aynası `scripts/jetson_paket_hazirla.py` | 18 dosya · `paket_0904.txt` |
| ✅ | Model dosyaları pakette | `navitas_seg_v36_best.pt` **52,3 MB** + `_512_fp16.onnx` **52,0 MB** *(kartın önceki hâli 54,8 / 54,6 diyordu — yanlıştı, ölçüldü ve düzeltildi)* |
| ✅ | Mühür `scripts/surum_dondur.py --dogrula` | exit 3 "DONDURULMADI" — mühür **17 Eylül**, bugün beklenen değer · `muhur_0904.txt` |
| ✅ | Çevrimdışı tekerlekler `wheels/` | **51 dosya · 246 MiB** = **48 `.whl`** + 3 metin (`INDIRME_RAPORU.txt`, `kaynak_paketler.txt`, `requirements_nano.txt`). ⚠ Saha kapısı **`.whl` sayar**: `ls ~/wheels/*.whl | wc -l` = **48**. Süzgeçsiz `ls` **51** basar — 4 Eylül'de kapı yanlış sayıyla yazılmıştı, doğru kopyada düşerdi (D-423) |
| ✅ | Saha belleği `scripts/bellek_hazirla.py` | **YENİDEN ÜRETİLDİ** — 405 dosya → `O:\navitas_bellek` · `bellek_0904.txt`, çıkış 0. Bayat işareti kalktı; **USB'ye artık kopyalanabilir** |

**Cuma akşamı tekrar koşulacak:** tam süit (yukarıdaki ⏳ satırı) + genel kapı.
Gün içinde kod değişmediyse geri kalanı geçerlidir.

## B. İnsanın yapacakları — cuma akşamına kadar

| ✓ | ne | neden / not |
|---|---|---|
| ~~☐~~ | ~~microSD ≥ 64 GB + kart okuyucu~~ **GEREKMİYOR** (3 Eylül beyanı: kartta microSD yuvası yok — eMMC modül; 6 Eylül ölçümü: Orin Nano DevKit, kök NVMe — D-431) | **satın alma listesinden ÇIKTI** |
| ✅ | ~~**CUMARTESİ İLK İŞ: Nano'yu aç ve bak** — eMMC'de JetPack kurulu geliyor mu?~~ **AÇILDI (6 Eylül, D-431): kart Jetson Orin Nano Developer Kit 4 GB, JetPack 7.2.1 kurulu, kök NVMe** | GEÇERSİZ: ~~`JETSON_NANO_KURULUM.md` §1.1~~ → `JETSON_ORIN_NANO_KURULUM.md` §0 |
| ✅ | ~~5 V / 5 A UBEC~~ **ALINDI (4 Eylül akşamı, kullanıcı beyanı)** — kargo riski KALKTI. ⚠ Kutu açılınca **etiketi oku**: çıkış **5 V**, akım **≥ 5 A**, giriş **4S'i (16,8 V) kaldırmalı**. 3 A'lik bir BEC Nano'nun MAXN kipini besleyemez | Jetson beslemesi; FCHUB'ın 2 A BEC'i yetmez. **J48 jumper takılı olmalı** (`JETSON_NANO_KURULUM.md` §2.1) — ⚠ GEÇERSİZ (D-431): Orin Nano DevKit'te **J48 yok**; Jetson beslemesi Orin için **DOĞRULANACAK** |
| 🛒 | JST-GH 6-pin kablo + dişi-dişi jumper — **SİPARİŞ EDİLDİ (4 Eylül); elde olduğu BEYAN EDİLMEDİ** | TELEM1 (SiK) ve TELEM2 → Nano UART. ⚠ UBEC geldi ama bu kablo gelmezse Pixhawk↔Nano hattı yine kurulamaz — **ayrı kalemdir, ayrı sorulur** |
| ☐ | **USB webcam** (yedek kamera) | CSI yolu ilk gün açılmazsa `--kaynak 0` |
| ✅ | ~~XT60/XT90 fiş, kablo bağı, ısı makaronu, damper bant~~ **HAZIR (4 Eylül)** | kablolama |
| ☐ | **Yedek pervane seti (12×10, CW+CCW)** | ilk uçuşlarda en sık kırılan parça |
| ☐ | (öneri) **2. pil 4S 10 Ah + ≥150 W şarj** | tek pil → günde 2 uçuş |
| ✅ | ~~YEDEK PLAN: Ubuntu'lu x86_64 bilgisayar~~ **AYARLANDI (4 Eylül)** — yalnız eMMC boş çıkarsa kullanılır → **GEREKMEDİ (D-431): JetPack 7.2.1 kurulu geldi, kök NVMe** | GEÇERSİZ (D-431): ~~eMMC BOŞ çıkarsa SDK Manager ile flash gerekir; **Windows'ta yapılamaz** · `JETSON_NANO_KURULUM.md` §1.2~~ |
| 🛒 | ~~Taşıyıcı kartın kurtarma (FC REC) pini — üretici kılavuzu~~ **TEMİN EDİLDİ (4 Eylül)** | flash gerekirse pin adı tahmin edilemez |
| ✅ | **NANO'YA İNTERNET — ETHERNET seçildi (4 Eylül, kullanıcı beyanı).** Doğru seçim: Nano'da yerleşik Wi-Fi **yoktur** (`JETSON_NANO_KURULUM.md` §2.1). 🔴 **Kapı — apt'ye dokunmadan önce:** `ping -c 2 archive.ubuntu.com && sudo apt update`. Kablo takılı olması internet demek değildir (WAN'sız modem / switch / ICS kapalı) | GEÇERSİZ (D-431): ~~`python3.8` **apt ile** kurulur ve çevrimdışı yedeği YOKTUR. İnternet yoksa venv38 kurulamaz → `ultralytics` yok → **algı zinciri hiç çalışmaz**. Yordam: `JETSON_NANO_KURULUM.md` §3.1~~ → Orin Nano'da (6 Eylül) internet **yine gerekti ve vardı**: `apt install nvidia-jetpack …` + çevrimiçi pip (`~/venv312`), `JETSON_ORIN_NANO_KURULUM.md` §1–2 |
| 🔴 | **KÜNYE FARKLARI (5 Eylül, kutu açıldı — BEYAN):** ESC **"60 A V2"** (plan 80 A) · güç modülü **PM06** (plan PM02) · FS-iA6B teyit. ESC ve PM06'nın **tam etiketi** fotoğraflanıp yazılacak; FDR Bölüm 3/5/7 düzeltilecek (D-426) | BEYAN GEREKLİ (insan) |
| ✅ | **Taşıyıcı kartın MODELİ** — **ÖLÇÜLDÜ (6 Eylül, D-431):** NVIDIA Jetson Orin Nano Developer Kit (`ORTAM_KUNYESI.txt`), modül p3767-0004 (tutanak §0 `/proc/device-tree/compatible`) | GEÇERSİZ: ~~eMMC boş çıkarsa FC REC pini ve flash yordamı modele bağlıdır · **BEYAN GEREKLİ (insan)**~~ flash gerekmedi |
| ✅ | ~~*(yalnız eMMC boş çıkarsa)* NVIDIA developer hesabı · ~20 GB SDK Manager indirmesi · **micro-USB kablo**~~ **GEREKMEDİ (D-431): JetPack kurulu geldi** | "Ubuntu'lu makine ayarlandı" bunları kapsamıyor; üçü de ayrı kalem · `JETSON_NANO_KURULUM.md` §1.2 |
| ✅ | ~~(öneri) GPU torch wheel'i (JetPack 4.6 / Py3.8) indir, belleğe koy~~ **GEÇERSİZ (D-431):** Orin Nano'da torch 2.11.0+cu130 jetson-ai-lab'den çevrimiçi kuruldu, CUDA **çalışıyor** | FPS **ölçüldü**: pt p50/p95 1,35/1,06 · engine 1,58/1,33 ≥ 0,61 GEÇTİ |
| ✅ | ~~Küçük ekran + klavye, ethernet kablosu~~ **HAZIR (4 Eylül)** | Nano ilk açılış |
| ✅ | ~~Multimetre, tartı, baret/yelek~~ **HAZIR (4 Eylül)** | kablolama kontrolü, UHDR kütle, saha |
| ⏳ | `O:\navitas_bellek` → **USB'ye kopyala** — klasör **HAZIR** ve depoyla **bayt-eş doğrulandı**. **USB bir takım arkadaşında (4 Eylül beyanı)** — kopyalama bu PC'de yapılır, yani USB **kaynağın yanına gelmeli**. ⚠ Ethernet geldiği için USB artık **TEK YOL DEĞİL**: dosyalar `scp`/`http` ile de geçirilebilir (`JETSON_NANO_KURULUM.md` §3.4) — bu kalem **tıkayıcı olmaktan çıktı, yedeği var** | kopyalayınca `MANIFEST.txt` ile doğrula; hangi yolla gelirse gelsin Nano'da `ls ~/wheels \| wc -l` = **48**. ⚠ D-431: tekerlekler Orin Nano'da **kullanılmadı** (cp38); paket 6 Eylül'de NTFS HDD ile taşındı (`DEVAM.md` §1) |
| 🔴 | **YKS dizüstüne SABİT IP ver** (yönlendiricide DHCP rezervasyonu ya da adaptöre statik adres) — *ethernet kararının açtığı yeni kalem* | `YKS_IP` `/etc/navitas.env`'e **elle** yazılır. DHCP adresi değiştirirse alıcı **tüm** ARM/DISARM/RTL/LAND/PARAŞÜT komutlarını reddeder ve bunu **yalnız Jetson tarafında** loglar — YKS ekranında hiçbir uyarı çıkmaz (D-421 §8). Yordam: `SAHA_RUNBOOK.md` §3 |
| ☐ | Bu kartı + **`SAHA_RUNBOOK.md`** + `FAZ_B_GUN_PLANI.md` + ~~`JETSON_NANO_KURULUM.md`~~ `JETSON_ORIN_NANO_KURULUM.md` (D-431) **yazdır** | sahada ekran olmayabilir. 🔴 RUNBOOK ATLANMAZ: tüm başlatma komutları, YKS operatör kartı ve SiK hub yordamı §2–3'tedir |

> ℹ️ **🛒 ve ✅ işaretli satırlar KULLANICI BEYANIDIR** (4 Eylül), depoda
> artefaktı yoktur. Planın kuralı "her iddia bir artefakta bağlanır" der;
> bu satırlar ölçüm değil beyandır ve öyle okunmalıdır. Kutu açılınca
> envanterle **teyit edilecektir** (§C adım 1).

## C. Cumartesi sabahı ilk üç iş (kutu açılınca)

1. **Envanter + tartı** — künye tablosuyla karşılaştır, farkları tutanağa (UHDR ister).
2. **Mekanik yerleşim** — Pixhawk ok ileri + damper, GPS direkte, kamera nadir.
3. **Kablolama pervanesiz, pil en son** — `SAHA_HAZIRLIK_PLANI` §2.3 tablosu.

⚠ **Pervaneler ilk uçuşa kadar takılmaz.** Motor testi ve tüm yer provaları pervanesiz.

## D. Sahada kural olarak hatırlanacak üç şey

- **Pil değişimi = Pixhawk yeniden başlar = akış isteği silinir** → `jetson_baslat.sh --kapi`
  yeniden koşulur (iniş kanıtı bu akışa bağlı, D-406).
- **`--fda` bayrağı** 21 Eylül uçuşunda YKS'yi doğru kipe alır: bütçe 10 dk, paraşüt ve
  İKA kapalı, hakem onayı İKA kanıtı beklemez (D-408).
- **Kamera köprüsü** `scripts/kamera_koprusu.py` içindir ve Jetson'da `~/navitas/scripts/`
  altına kopyalanır (`codes/` değil — yanlışı `--kur`'u durdurur, D-407).
- **Jetson künyesi (6 Eylül ölçümü, D-431):** kart **Orin Nano Developer Kit 4 GB / JetPack 7.2.1 /
  Ubuntu 24.04 / Python 3.12** — Nano/JetPack 4.6 varsayımı geçersiz. Kullanıcı `n4vitas`, paket kökü
  `~/navitas` (symlink), yorumlayıcı `~/venv312/bin/python` (`PYTHON3=/home/n4vitas/venv312/bin/python`),
  köprü `/usr/bin/python3`; `jetson_baslat.sh --kuru` ölçüldü: `[YOK]` yalnız `/dev/ttyACM0` (Pixhawk
  bağlı değildi). **Uçuş modeli `.pt`** (engine↔pt D-303 oransal denkliği 3/126 DÜŞTÜ). CSI kamera ve
  Pixhawk kapıları **ÖLÇÜLEMEDİ**. Tutanak: `jetson_paket/JETSON_ORIN_NANO_KURULUM.md`.

### 4 Eylül'de gelen ve sahada BİLİNMESİ gereken üç yeni davranış

- 🔴 **Komut alıcı artık `--izinli-kaynak HOST:PORT` İSTER.** Verilmezse
  **çıkış 2** ile açılmaz. `jetson_baslat.sh` bunu kendisi veriyor (kuru koşuda
  görünüyor), ama süreci **elle** başlatan olursa bayrağı yazmalı. Ayrıca
  `--serial` artık **tümden reddediliyor**: seri Pixhawk'ı yalnız `seri_hub` açar.
- 🔴 **ARM / DISARM / RTL / LAND artık İKİ TIK ister.** İlk tık hiçbir şey
  göndermez, düğme "…? TEKRAR BAS" olur ve sarı uyarı düşer; ikinci tık gerçek
  komutu yollar. Komut iletilemezse düğme **gerçeğe döner** ve kırmızı hata
  görünür — "TEKRAR BAS" ekranda asılı kalmaz.
- ⚠ **Komut yaşı artık saat sapmasına dayanıklı — ama ilk komut GECİKMELİ geçer.**
  İHA ile YKS'nin duvar saatleri farklıysa (Jetson'da RTC pili yok, 1970'e
  açılabilir) komut **artık kalıcı reddedilmiyor**: ofset kayan pencerede
  kestiriliyor. **Ölçülen davranış (4 Eylül):** soğuk açılışta kestirim
  **7. basamakta** oluşuyor. ACK'li tekrar merdiveni 8 basamak × 0,25 s
  olduğu için **operatörün tek basışı yeter** — komut ~1,75 s sonra geçer.
  Ekranda "TEKRAR BAS" değil, kısa bir gecikme görürsün.
  🔴 **Tek basış geçmezse ikinci kez bas** — merdiven 8 basamakta bitiyor ve
  kestirim tam sınırda oluşuyor; ikinci basış kesin geçer (ofset artık öğrenildi).
  Logda görünür: `saat ofseti OGRENILDI: -7200.000 s`.

