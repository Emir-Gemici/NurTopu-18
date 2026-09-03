# CUMA AKŞAMI KONTROL KARTI — 4 Eylül (yazdırılacak)

> Cumartesi sabahı kutu açılmadan önce bu kartın **tamamı** işaretli olmalı.
> Kaynak: `SAHA_HAZIRLIK_PLANI_20260903.md` §1 · ölçüm çıktıları:
> `results/faz_b_oncesi/cuma_kontrol/`

## A. Yazılım kapıları — **4 Eylül 01:00'de baştan koşuldu**

> ⚠ 4 Eylül'de ~2200 satır kod değişti (Codex + altı worktree birleştirmesi);
> 3 Eylül ölçümleri **geçersizdi** ve bu tablo baştan üretildi. Artefaktlar:
> `results/faz_b_oncesi/cuma_kontrol/*_0904.txt`

| ✓ | kapı | sonuç (4 Eylül) |
|---|---|---|
| ✅ | Genel kapı `codes/test_rota_sentetik.py` | **15/15 · 15/15**. ⚠ Bu kapı `tests/` altında **değildir**, tam süit onu **kapsamaz**; ayrı koşulur (D-415) |
| ⏳ | Tam test paketi | **2059 test · 1 düşük** — düşen tek şey ayna ikizi (`rpi_inference.py`), çünkü **başka bir ajan ağaca canlı yazıyordu**. Kod kusuru değil; ajan durunca ayna senkronlanıp süit yeniden koşulacak. **Cuma akşamı tekrar koşulacak tek kalem budur.** |
| ✅ | Kuru koşu `scripts/saha_kuru_kosu.py` | **9 GEÇTİ · 0 DÜŞTÜ · 1 SAHİPSİZ** · `kuru_kosu_0904.txt`. Sahipsiz halka `motor`: gerçek İKA motor sürücüsü yok — **FDA uçuşunda gerekmez**, final aracında gerekir (T149). Çıkış 1 (kopuk halka nedeniyle, beklenen) |
| ✅ | `saha_baslat.py --komutlar` | `--iha <JETSON_IP>:5007` yerinde (D-403) · `saha_baslat_0904.txt` |
| ✅ | Jetson açılış `jetson_baslat.sh --kuru` **udp** | exit 3 (PC'de beklenen) · `--izinli-kaynak 192.168.1.10:5005` · `--streamrate 8` · uçlar 14550/14551/14552 · `jetson_udp_0904.txt` |
| ✅ | Jetson açılış **sik** | exit 3 · `--izinli-kaynak 127.0.0.1:5100` (seri hub ucu) · `jetson_sik_0904.txt` |
| ✅ | Paket aynası `scripts/jetson_paket_hazirla.py` | 18 dosya · `paket_0904.txt` |
| ✅ | Model dosyaları pakette | `navitas_seg_v36_best.pt` **52,3 MB** + `_512_fp16.onnx` **52,0 MB** *(kartın önceki hâli 54,8 / 54,6 diyordu — yanlıştı, ölçüldü ve düzeltildi)* |
| ✅ | Mühür `scripts/surum_dondur.py --dogrula` | exit 3 "DONDURULMADI" — mühür **17 Eylül**, bugün beklenen değer · `muhur_0904.txt` |
| ✅ | Çevrimdışı tekerlekler `wheels/` | **48 dosya · 246 MB** *(kart 51 diyordu — ölçüldü ve düzeltildi)* |
| ✅ | Saha belleği `scripts/bellek_hazirla.py` | **YENİDEN ÜRETİLDİ** — 405 dosya → `O:\navitas_bellek` · `bellek_0904.txt`, çıkış 0. Bayat işareti kalktı; **USB'ye artık kopyalanabilir** |

**Cuma akşamı tekrar koşulacak:** tam süit (yukarıdaki ⏳ satırı) + genel kapı.
Gün içinde kod değişmediyse geri kalanı geçerlidir.

## B. İnsanın yapacakları — cuma akşamına kadar

| ✓ | ne | neden / not |
|---|---|---|
| ~~☐~~ | ~~microSD ≥ 64 GB + kart okuyucu~~ **GEREKMİYOR** (3 Eylül: kartta microSD yuvası yok — eMMC modül) | **satın alma listesinden ÇIKTI** |
| ☐ | **CUMARTESİ İLK İŞ: Nano'yu aç ve bak** — eMMC'de JetPack kurulu geliyor mu? (üçüncü parti kitlerin çoğu kurulu gelir) | `JETSON_NANO_KURULUM.md` §1.1 · 5 dakika · flash'lamadan ÖNCE |
| 🛒 | ~~5 V / 5 A UBEC al~~ **SİPARİŞ EDİLDİ (4 Eylül)** — kargo cumartesi sabahına yetişmeli; yetişmezse 11:00 kablolama bloğu yarım kalır | Jetson beslemesi; FCHUB'ın küçük BEC'i yetmez |
| 🛒 | ~~JST-GH 6-pin kablo + dişi-dişi jumper~~ **SİPARİŞ EDİLDİ (4 Eylül)** | TELEM1 (SiK) ve TELEM2 → Nano UART |
| ☐ | **USB webcam** (yedek kamera) | CSI yolu ilk gün açılmazsa `--kaynak 0` |
| ☐ | XT60/XT90 fiş, kablo bağı, ısı makaronu, damper bant | kablolama |
| ☐ | **Yedek pervane seti (12×10, CW+CCW)** | ilk uçuşlarda en sık kırılan parça |
| ☐ | (öneri) **2. pil 4S 10 Ah + ≥150 W şarj** | tek pil → günde 2 uçuş |
| 🛒 | ~~YEDEK PLAN: Ubuntu'lu x86_64 bilgisayar~~ **AYARLANDI (4 Eylül)** — yalnız eMMC boş çıkarsa kullanılır | eMMC BOŞ çıkarsa SDK Manager ile flash gerekir; **Windows'ta yapılamaz** · `JETSON_NANO_KURULUM.md` §1.2 |
| 🛒 | ~~Taşıyıcı kartın kurtarma (FC REC) pini — üretici kılavuzu~~ **TEMİN EDİLDİ (4 Eylül)** | flash gerekirse pin adı tahmin edilemez |
| ☐ | (öneri) GPU torch wheel'i (JetPack 4.6 / Py3.8) indir, belleğe koy | v36 YOLOv8m; CPU'da FPS kapısı düşebilir |
| ☐ | Küçük ekran + klavye, ethernet kablosu | Nano ilk açılış |
| ☐ | Multimetre, tartı, baret/yelek | kablolama kontrolü, UHDR kütle, saha |
| ☐ | `O:\navitas_bellek` klasörünü **USB'ye kopyala** | 1,27 GB; `MANIFEST.txt` içindedir |
| ☐ | Bu kartı + `FAZ_B_GUN_PLANI.md` + `JETSON_NANO_KURULUM.md` **yazdır** | sahada ekran olmayabilir |

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

### 4 Eylül'de gelen ve sahada BİLİNMESİ gereken üç yeni davranış

- 🔴 **Komut alıcı artık `--izinli-kaynak HOST:PORT` İSTER.** Verilmezse
  **çıkış 2** ile açılmaz. `jetson_baslat.sh` bunu kendisi veriyor (kuru koşuda
  görünüyor), ama süreci **elle** başlatan olursa bayrağı yazmalı. Ayrıca
  `--serial` artık **tümden reddediliyor**: seri Pixhawk'ı yalnız `seri_hub` açar.
- 🔴 **ARM / DISARM / RTL / LAND artık İKİ TIK ister.** İlk tık hiçbir şey
  göndermez, düğme "…? TEKRAR BAS" olur ve sarı uyarı düşer; ikinci tık gerçek
  komutu yollar. Komut iletilemezse düğme **gerçeğe döner** ve kırmızı hata
  görünür — "TEKRAR BAS" ekranda asılı kalmaz.
- ⚠ **Komut yaşı artık saat sapmasına dayanıklı.** İHA ile YKS'nin duvar saatleri
  farklıysa (Jetson'da RTC pili yok) komut **artık reddedilmiyor**: ofset
  kayan pencerede kestiriliyor. Yine de ilk kritik komutta kestirim henüz
  oluşmamış olabilir — **ARM ilk denemede geçmezse ikinci kez dene**, bu
  beklenen davranıştır.

