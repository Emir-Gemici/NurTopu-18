# 03 — PRATİK SAHA TESTİ (terminal yok, SSH yok)

> **Kullanıcı kararı, 20 Eyl akşamı:** *"artık Jetson'a bağlantı kurmadan düz gerçek pratik
> bir şekilde test edelim."*
>
> Bu belge **sahada, ekran başında, kabuk açmadan** uygulanır. Her adımın ne anlama geldiği
> ve **nereden okunacağı** yazılıdır. Bilgisayarda yalnız iki şey çalışır: **yönlendirici
> penceresi** ve **YKİ**. Üçüncüsü Mission Planner.
>
> ⚠ Bu **prova değil, gerçek**: yarışma programı **21–25 Eylül, Adıyaman Üniv. Stadyumu**.

---

## 0. ÖN ŞART — bunlar olmadan başlama

| ✔ | Madde | Neden |
|---|---|---|
| ☐ | **Dört pervane somunu elle kontrol** | İki düşüş, iki farklı köşe, aynı imza (D-491 ön-sağ, D-506 ön-sol). **Ortak şüpheli pervane tutma sistemi** |
| ☐ | Pervanelerde çatlak yok, motorlar elle serbest dönüyor | |
| ☐ | **Kamera şeridi ve bandı yerinde**, şerit gövdeye 3–4 cm ötede ayrıca sabit | Konnektörün ZIF mandalı **kırık**, bantla duruyor (D-520). Titreşim doğrudan bandına binmemeli |
| ☐ | **Lens odağı yapıldı** | 20 Eyl'de kare **düz gri**ydi. Odaksız görüntüden şerit çıkmaz → rota yok → puan yok |
| ☐ | Jetson güç fişi sallanınca oynamıyor. Pil **4S** ve dolu | 3S pille Jetson uçmaz (D-512) |
| ☐ | GPS1 kablosu iki ucundan oturmuş, gerilimsiz sabit | Harici pusula **aralıklı** geliyor (D-515) |

⚠ **CSI sıcak takılmaz.** Kameraya dokunulduysa Jetson'ın gücü **tamamen kesilip** yeniden açılır.

---

## 1. AÇILIŞ SIRASI (bu sırayla, atlamadan)

1. **Jetson'ı aç.** Ethernet yok, SSH yok, kimse bilgisayardan bağlanmıyor.
   Servisler `enabled` — kendiliğinden gelir. Bekleme: ~60 s.
2. **Pixhawk'ı aç** (pervanesiz, güvenlik anahtarı basılı değil).
3. **Yer telsizini** bilgisayarın USB'sine tak.
4. Mission Planner açıksa **COM portundan AYIR**. Portun tek sahibi yönlendiricidir.
5. **Yönlendirici + YKİ**'yi aç:
   - Windows: dal kökünde `SAHA_YKI_BASLAT.cmd` çift tık (port vermek için `SAHA_YKI_BASLAT.cmd COM7`)
   - Linux (yedek): `python3 -B scripts/yer_yonlendirici.py --port /dev/ttyUSB0 --baud 57600 --tunel 127.0.0.1:14590`
     ardından `python3 -B comms/yks_gui.py --tunel 127.0.0.1:14590 --fda`
   ⚠ **YKİ `bilgilendirme-he` dalından açılır.** `master`'daki YKİ'de `--tunel` **yoktur**.
   ⚠ Eskiden açık kalmış bir YKİ penceresi **eski kodu taşır** — kapat, yeniden aç.
6. **Mission Planner**: bağlantı türü **UDP**, port **14550**, Connect.

---

## 2. YERDE OKUNACAKLAR — hepsi ekrandan, terminal yok

### 2.1 Yönlendirici penceresi

| Görülen | Anlamı | Ne yap |
|---|---|---|
| `seri->udp` **2–3 kB/s** akıyor, `seri_hata` artmıyor | ✅ telsiz zinciri sağlam | devam |
| `seri->udp 0 B/s` ya da `seri_hata` artıyor | 🔴 sorun **yer telsizi ya da USB**'de | kabloyu kontrol et. Yeni kod portu kendisi yeniden açar (8 s) |
| `SERI YENIDEN BAGLANDI` | USB çıkıp takıldı, kendini toparladı | not al, kabloyu sabitle |

🔴 **Arıza okuma kuralı (19 Eyl'de ihlal edildi, ~30 dk kaybedildi):**
YKİ "BAĞLANTI KAYBI" derse **ÖNCE yönlendirici penceresine bak.**
`seri->udp` akıyorsa sorun Jetson'da; akmıyorsa sorun yer telsizinde/USB'de.
Bu sıra atlanırsa yanlış yerde aranır.

### 2.2 YKİ ekranı

| ✔ | Görülmesi gereken | Görülmezse |
|---|---|---|
| ☐ | İHA satırı **yeşil "TAZE"**, Pixhawk ✓ | sarı "bağlantı ZAYIF" (3–5 s) kısa sürerse normal; kırmızı (>5 s) ise §2.1 |
| ☐ | Konum **makul**: "3B FIX ✓" ya da koordinatla "fix BİLİNMİYOR" | "konum BİLİNMİYOR" görünüyorsa GPS'i bekle, dışarı çık |
| ☐ | Karar geliyor (rota ya da **ROTA YOK**) | hiç gelmiyorsa algı yolu ölü — kamera odağı/şeridi |

### 2.3 Mission Planner — Mesajlar sekmesi

| ✔ | Aranan satır | Anlamı |
|---|---|---|
| ☐ | **"EKF3 IMU0/1 MAG0 initial yaw alignment complete"** | ✅ harici pusula var |
| ☐ | "MAG2" ya da "switching to compass 2" | 🔴 **harici pusula YOK** → GPS1 kablosunu oturt, Pixhawk'ı yeniden başlat |
| ☐ | "RC Protocol: IBUS" | kumanda görülüyor |
| ☐ | PreArm temiz | kapalı alanda "GPS bad fix" normaldir |

---

## 3. PERVANESİZ HAKEM PROVASI (5 dk) — uçmadan önce

Amaç: görev akışının tamamını **uçmadan** bir kez geçmek.

| ✔ | Adım | Geçme ölçütü |
|---|---|---|
| ☐ | Kamera zemine baksın, YKİ'ye rota gelsin | Haritada rota çizilmeli |
| ☐ | 🔴 **Rota AŞAĞIDAN YUKARI mı akıyor?** | Yatay akıyorsa montaj açısı uygulanmamış. Tersse işaret yanlış. **Sol/sağ takası = 0 puan.** Emin olunmadan onay verilmez |
| ☐ | **"1) TESPİTİ DOĞRULA"**ya bas | Düğme "2) YKS'DE GÖRÜLDÜ — ONAYLA" olmalı |
| ☐ | **"2) YKS'DE GÖRÜLDÜ — ONAYLA"**ya bas | ACK gitmeli |
| ☐ | **Elini çek, 30–60 s bekle. HİÇBİR ŞEYE BASMA** | Düğme **"ONAYLANDI ✓✓"** kalmalı; günlükte yeni seq'lere "ACK ref=… gönderildi" görünmeli |

🔴 **Bu son satır testin kalbidir.** 19 Eyl'de bulunan hata (D-516) hakemin onayını ~1 saniyede
siliyordu. Düzeltildi. **Onay 60 saniye boyunca duruyorsa düzeltme sahada çalışıyor demektir.**
Duruyorsa: geçti. Silinirse: uçuşta hakem her karede basmak zorunda — **durdur ve bildir.**

Ekranda beklenen, hata olmayan durumlar:

| Yazı | Anlamı | Ne yap |
|---|---|---|
| `ONAY ASKIDA — ACK YOK` | arada "rota yok" ya da düşük güven karesi geldi | **basma**, 5 s içinde kendiliğinden döner |
| `ROTA YOK — ACK OTOMATİK GÖNDERİLDİ` | İHA rota bulamadı, güvenli bildirim | normal |
| `SERIT DEGISTI — yeni onay gerekir` | İHA başka şerit seçti | onay baştan |
| `BAYAT TESPİT — ONAY KAPALI` | karar yaşı > 5 s | telemetriyi bekle |
| `GEOMETRİ YOK` / `ANKOR YOK` | rotanın ilk noktası [0,0] değil | güvenlik kapısı; algı tarafında sorun var |

---

## 4. UÇUŞ

🔴 **Yazılımla uçuş (GUIDED/AUTO) yalnız Jetson AÇIKKEN.**
Yalnız MP bağlıyken telsiz 5 s koparsa `FS_GCS_ENABLE 5` devreye girer ve araç **LAND**'a düşer.
19 Eyl'de bu **iki kez** yaşandı (12:59 logunda 456 s'de, 14:09 logunda 125,8 s'de).
Jetson açıkken olmaz: MAVProxy sysid 255 ile heartbeat gönderir.

Uçuş sırasında ekrandan izlenecekler:

| Görülen | Anlamı |
|---|---|
| sarı **"bağlantı ZAYIF"** (3–5 s) | kısa sürerse normal |
| kırmızı **"BAĞLANTI KAYBI"** (>5 s) | **önce yönlendirici penceresine bak** (§2.1) |
| **"kimlik SICRAMASI"** | Jetson yeniden başladı → 1–2 dk rota gelmez |
| MP'de **"switching to compass 2"** | harici pusula koptu → yaw hatası, kayma riski → **iniş düşün** |

**Bilinen ve kabul edilmiş sınır:** K8 hız kapısı **düştü** (p95 212 / 278 ms, eşik 200).
Darboğaz telsizin TDM turudur, Jetson değil (Jetson hiç yokken bile p95 205 ms).
Pratikte rota 0,40 s'de, ACK 0,22 s'de ulaştı. **Rota gecikmeli gelebilir, tekrar mekanizması var.**
Eşik gevşetilmedi; bu bir hüküm değil, bilinen bir sınırdır.

---

## 5. DURDURMA ÖLÇÜTLERİ — şunlardan biri olursa uçma / indir

- Pervane somunlarından biri **gevşek**
- MP Mesajlarında **"MAG0"** yerine **"MAG2"** / "switching to compass 2"
- YKİ haritasında rota **yatay** ya da **tersten** akıyor (sol/sağ takası riski)
- Ok testindeki **"ÖN" yazısı ayna gibi ters okunuyor** (görüntü aynalanıyor — D-349'daki `cv2.flip` hatası 16 karenin 15'inde şeritleri takas etmişti)
- Pil dinlenik gerilimi düşük (19 Eyl'de 14,0 V'la kalkılan uçuşta 72 A çekişte 12,1 V'a düştü)
- Jetson uçuş öncesi **kendiliğinden kapandı** (D-512: iki kez oldu, güç kesintisi imzası)

---

## 6. KANIT TOPLA (uçuş sonrası, atlanmaz)

| ✔ | Ne | Nereden |
|---|---|---|
| ☐ | Pixhawk `.bin` + MP `tlog` | → `results/ucus_20260921/` |
| ☐ | Hakem günlüğü `hakem_log.jsonl` | YKİ'nin yazdığı `results/prova/<zaman>/` |
| ☐ | Yönlendirici penceresinin **son satırları** | ekran görüntüsü yeter |
| ☐ | YKİ ekran görüntüsü (onay anı) | |
| ☐ | Jetson `~/kara_kutu/*.csv` + `journalctl -u navitas-rpi-inference` | **sonradan**, bilgisayar bağlanabildiğinde |

Son madde SSH ister ve **uçuş sonrasına** bırakılır — teste engel değildir.

---

## Bu belgenin sınırı

Burada yazan her madde **20 Eyl'e kadar ölçülmüş** bir olaya ya da kayda dayanır; kaynaklar
`../KANIT_DEFTERI.md` (D-517…D-522), `../UYGUNLUK_OLCUMU.md` ve `BILGILENDIRME_HE/01…08`.
**Ölçülmemiş hiçbir şey "tamam" diye yazılmadı.** Sahada yeni bir şey ölçülürse deftere
kanıtıyla eklenir; bu belge ona göre güncellenir.
