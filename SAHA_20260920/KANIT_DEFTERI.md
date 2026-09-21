# 20 Eylül 2026 · Adıyaman — kanıt defteri

⚠ **D-numara uyarısı.** İki çizgi ayrı numara veriyor: `origin/master`'da en yüksek **D-505**,
`bilgilendirme-he` çizgisinde **D-516**. Aşağıdaki numara **geçicidir**, birleştirmede doğrulanacak
(`BILGILENDIRME_HE/07` bu çakışmayı zaten açık iş olarak yazmıştı).

---

## D-517 (geçici) · Takvim varsayımı çürütüldü: 21 Eylül prova değil

**İddia (FDR Bölüm 1, 3–4 Eylül hâli):** *"30 Eylül – 3 Ekim'de uçacak olan budur;
provası 21 Eylül Adıyaman."*

**Ölçüm (20 Eyl, dış kaynak):**
- teknofest.org · İleri Otonom Sistemler Tasarım ve Operasyon Yarışması → **"FDR Sunumları: 21 Eylül – 3 Ekim 2026"**
- Yerel basın, iki bağımsız gazete, aynı bilgi → *"21–25 Eylül'de **Adıyaman Üniversitesi Stadyumu**'nda"*,
  **23–25 Eylül** ziyarete açık günler.

**Hüküm:** 21 Eylül **Adıyaman programının birinci günüdür**, prova günü değil.
FDR'deki satır bayattır. **"Yarın puan alınmıyor" varsayımı DÜŞTÜ.**

**Hâlâ bilinmeyen:** takımın kendi slotu (hangi gün sunum, hangi gün uçuş). Dış kaynaktan
çıkarılamaz; KYS kaydında ve ekiptedir. **İnsan teyidi bekliyor.**

**Ders:** rapor içindeki tarih satırları, yazıldıkları günün resmî sayfasından türetilir ve
**sessizce bayatlar**. Saha kararı bir rapor satırına değil, o günkü kaynağa dayanmalıdır.

---

## D-518 (geçici) · Canlı hakem onay testi aracı yazıldı ve KENDİNİ KANITLADI

**Neden gerekti.** D-516'daki hata (her yeni seq hakemin onay adımlarını siliyor) 19 Eyl akşamı
bulundu ve düzeltildi (`a2e69b9b`, `db692109`), ama **canlı denenmedi**. Eldeki
`results/telsiz_20260919/betikler/rota_testi.py` hep **aynı** seq'i yolladığı için hatayı
zaten görememişti — bu bir **test tasarımı açığıdır**, kod hatası değil.

**Yazılan.** `SAHA_20260920/rota_testi_yeniseq.py` — üretim taklidi: aynı şerit, **her saniye
yeni seq**, her N tıkta bir NO_ROUTE, 1 Hz heartbeat. Gelen her ACK zaman + ref ile kaydedilir.

**Ön kayıt (koşudan ÖNCE yazıldı, değiştirilmeyecek):**
1. İlk ACK'ten sonra her **10 s**'lik pencerede en az bir **yeni-seq** ACK'i.
2. Her NO_ROUTE'tan sonra **10 s** içinde yeniden OPEN_ROUTE ACK'i.
3. **Hiçbir ACK gönderilmemiş bir seq'e ait olmamalı.**

Pencere CLI'dan değiştirilebilir ama araç o zaman ekrana **"OLCUT GEVSETILDI — bu koşu saha
kanıtı değildir"** basar ve kayda `gevsetildi: true` yazar (D-225 dersi).

**Kendi kanıtı.** `SAHA_20260920/test_rota_testi_yeniseq.py` — sahte hub + sahte YKİ, ağ/donanım yok.
Ham çıktı: `SAHA_20260920/kanit/b2_kendi_testi_20260920.txt`. **5 test OK, 65,6 s.**

| Senaryo (sahte YKİ kipi) | Araç hükmü | Kanıt satırı |
|---|---|---|
| **saglam** (a2e69b9b + db692109 davranışı) | **GEÇTİ** | 8 yeni-seq ACK, en uzun boşluk 2,0 s, hayalet yok |
| **MUTANT yeni_seq** (= D-516'daki gerçek hata) | **DÜŞTÜ** | `open_route_ack: 0`, "ÖLÇÜT 1 DÜŞTÜ" |
| **MUTANT no_route** (db692109 öncesi) | **DÜŞTÜ** | "ÖLÇÜT 2 DÜŞTÜ", 8,0 s boşluk |
| **MUTANT hayalet** (gönderilmemiş seq'e ACK) | **DÜŞTÜ** | "ÖLÇÜT 3 DÜŞTÜ", 8 hayalet seq |

**Hüküm: 3/3 mutant yakalandı.** Araç, ölçmesi gereken hatayı yakalayabildiğini kanıtladı;
saha koşusuna (B3) hazırdır. **Bu koşu bir SAHA kanıtı değildir** — sahte YKİ'ye karşı alındı,
gerçek `yks_gui` + telsiz + Jetson ile tekrarlanacak.

**Bağımsızlık notu (anayasa §19).** Bu aracı mimar oturumu yazdı. Kendi yazdığını kendi
onaylamaz; ama burada onaylayan **ölçümdür**: mutant yakalama, anlaşma değil kanıttır.
Yine de B3'ün ham çıktısı ayrı bir gözle okunmalıdır.

---

## D-519 (geçici) · Linux laptop YEDEK YER İSTASYONU olarak doğrulandı

**Neden arandı.** 20 Eyl'de yer istasyonu tek makineye bağlıydı (Emir'in Windows O: makinesi).
Tek nokta arızası: o makine düşerse sahada YKİ yok. Jetson da bugün erişilemez durumda
(yurtta ethernet prizi yok, USB-C kablo/ekran/klavye yok) — bu yüzden masa başı dayanıklılık
işine geçildi.

**Ölçüm (bu Linux PC, Fedora 44, Python 3.14.7, Wayland):**

| Bileşen | Sonuç |
|---|---|
| `pyserial` | `pip install --user pyserial` → **3.5 kuruldu** (0,3 MB; numpy/opencv GEREKMEDİ) |
| `tkinter` | zaten kurulu |
| `scripts/yer_yonlendirici.py --help` | **çalıştı** — platform bağımsız, `--port` alıyor (Linux'ta `/dev/ttyUSB0`, Windows'ta `COM7`) |
| `comms/yks_gui.py --help` | **çalıştı** — `--tunel`, `--fda`, `--gorunum` seçenekleri yerinde |
| `yks_gui --demo --fda --otokaydet 8 --kapat` | **pencere açıldı ve çizildi**, exit 0. Kanıt: `kanit/yki_linux_20260920.png` |

Çalışma kopyası: `git worktree` → `/home/trs/projects/navitas-wt-bilgilendirme` (dal `bilgilendirme-he`,
324ce42b). master çalışma klasörüne dokunulmadı.

**Hüküm:** yer istasyonu zinciri (yönlendirici + YKİ) bu Linux PC'de **koşar**. Yedek vardır.
Windows'tan tek fark seri port adıdır.

**Yan bulgu (kayda geçti).** `--demo` beslemesi ekranda **"GEOMETRİ YOK — ilk yerel waypoint
costmap başlangıç ankuru [0,0] olmalı"** verdi ve hakem onay düğmesi **KAPALI** kaldı.
Bu güvenlik kapısının doğru çalışmasıdır (`BILGILENDIRME_HE/02` bu reddi bilerek listeliyor),
ama sonucu şudur: **`--demo` kipi hakem onay akışını sınayamaz.** Onay yolunu yalnız gerçek
OPEN_ROUTE (ankoru [0,0] olan) zorlayabilir → D-518'deki araç bu yüzden gereklidir.

**Sınır — abartılmayacak:** bu, GUI'nin Linux'ta çizildiğinin kanıtıdır.
**Telsiz + seri + tünel uçtan ucu bu makinede HENÜZ ölçülmedi.**

---

## D-520 (geçici) · Jetson'a erişim kuruldu; KAMERA YOK — kök neden mekanik

**Erişim (çözüldü).** Yurtta ethernet prizi yok, Jetson'da wifi yok. Çözüm `l4tbr0` oldu:
USB **veri** kablosu, **A ucu laptopta, C ucu Jetson'da**. Önceki denemelerin sıfır olay
vermesinin sebebi kablonun A ucunun **Jetson'a** takılmasıydı — Jetson'ın Type-A portları
**host**'tur, cihaz sunmaz. İki host birbirine bağlanınca çekirdek hiçbir şey görmez.

```
Bus 003 Device 122: ID 0955:7020 NVIDIA Corp. L4T (Linux for Tegra) running on Tegra
enp0s20f0u6   192.168.55.100/24      (Jetson: 192.168.55.1, ping 0,24 ms, ttyACM0 da açıldı)
```
Anahtar yetkilendirildi (`~/.ssh/navitas_jetson`, `ssh jetson`); parola artık gerekmiyor.

**Servisler — dünkü düzeltme TUTMUŞ.** Altı servis `active`, **hepsinde `NRestarts=0`**.
19 Eyl'deki 32'lik çökme döngüsü bitti. `67467c4f` amacına ulaşmış: servis çökmüyor,
bekliyor ve **kök nedeni kendisi raporluyor**.

**🔴 Ama kamera YOK.** 1 sa 23 dk'dır bekliyor:
```
[KAMERA_BEKLIYOR] neden=KAMERA_ACILAMADI deneme=795 bekleme_s=5011.5
/dev/video*: YOK | acma_denemesi=2125 dusen_kare=63750
```
`i2cdetect -y -r 9` ve `-r 10` (her iki CSI bus'ı): **tamamen boş, hiçbir adreste cihaz yok.**
Sensör elektriksel olarak cevap vermiyor.

**Kök neden (kullanıcı beyanı + ölçümle uyumlu):** CSI/FFC konnektörünün **ZIF kilit mandalı kırık**.
Boş I2C bu beyanla birebir uyumludur.

**sha'lar tutuyor:** `rpi_inference 6fe5819b`, `karar_sozlesmesi 3bc18e5d` → bekleyen
`kurulum2/uygula.py` ön şartı sağlanıyor, koşulabilir.

### İkinci, bağımsız hata: boot overlay uyuşmazlığı

```
MENU LABEL  Custom Header Config: <CSI Camera IMX219 Dual>
OVERLAYS    /boot/tegra234-p3767-camera-p3768-imx477-dual.dtbo
```

`extlinux.conf` mtime **2026-09-15 20:06** → **dün DEĞİL**. Yedeklerden çıkan sıra:

| yedek | içindeki hâl | tutarlı mı |
|---|---|---|
| `jetson-io-backup` 13 Eyl 15:05 | kamera overlay'i yok | — |
| `before-imx477-` 15:09 | IMX219-C | ✅ |
| `before-cam0-` 16:17 | IMX477-C | ✅ |
| `before-imx219-cam0-` 16:22 | IMX477-A | ✅ |
| `before-imx477-dual-` 18:10 | IMX219-dual | ✅ |
| **mevcut** 15 Eyl 20:06 | IMX219 etiketi + **imx477** overlay | 🔴 **hayır** |

Son adımda **yalnız `OVERLAYS` satırı elle değiştirilmiş**; Jetson-IO ikisini birden yazardı.
13–15 Eyl'de **beş farklı overlay** denenmiş.

**Yorum (MUHTEMEL, kanıtlanmadı):** konnektör kırıkken hiçbir overlay çalışmazdı.
Beş overlay denemesi, **mekanik bir arızanın yazılımda aranmasıdır**. Bu örüntü tekrarlıyor:
19 Eyl 18:40'ta USB kopmuşken "Jetson heartbeat'i durdu" denildi ve ~30 dk kaybedildi (D-513 ek).

**KARAR: overlay'e dokunulmayacak.** Altıncı tahmin yürütülmez. Sıra kilitli:
1. fiziksel temas (shim + Kapton + **gerginlik azaltma**; CSI sıcak takılmaz → güç tamamen kesilip açılacak)
2. `i2cdetect` → **0x10 = IMX219** · **0x1a = IMX477**
3. ancak o zaman eşleşen overlay

Geri dönüş hazır: IMX219 çıkarsa
`sudo cp /boot/extlinux/extlinux.conf.before-imx477-dual-20260915 /boot/extlinux/extlinux.conf`.

**USB kamera yedeği KAPALI.** `kamera_koprusu.py --kaynak 0` USB (UVC) kamerayı destekliyor ve
`KAMERA_KOPRU_ARGS` tek satırla değişirdi (kod değişikliği gerekmez), ama kullanıcı beyanı:
**elde USB kamera yok, yalnız Jetson uyumlu CSI kamera var.** Bu yol açılırsa `--fov` yeniden
ölçülmelidir (ölçek → rota geometrisi).

**Uygunluk tablosuna etkisi: L1 artık "ölçülmedi" değil, ZİNCİR KOPUK.**
Kamera yoksa şerit kararı yok, rota yok. Günün en yüksek öncelikli işi budur.

---

## D-521 (geçici) · montaj_yaw ÖLÇÜLDÜ: **+90°** (A9 nihayet yapıldı)

**Neden önemli.** `BILGILENDIRME_HE/05`: *"Montaj açısı daha önce hiç ölçülmedi (A9 yapılmadı),
varsayılan 0'dır."* Kamera montaja 90° çevrilerek sığdığı için bu, **yanlış şerit → 0 puan**
riskiydi ve uygunluk tablosunda **L3** olarak açık duruyordu.

**Ölçüm (ok testi, kullanıcı, 20 Eyl).** 3×3 ızgara ile bildirildi: burun (ön) görüntünün
**üstünde (2)** olmalıyken **solda (4)** görülüyor.

⚠ İlk bildirimde "6" (sağ) denmiş, kullanıcı hemen düzeltti: **4 (sol)**. İlk türetmem bu yüzden
−90 çıkmıştı ve **yanlıştı**; düzeltildi. Bu, sol/sağ şeridi takas eden işaretin ta kendisidir —
tek harflik bir bildirim farkı 0 puan demekti. Ekrandan bağımsız doğrulama bu yüzden zorunludur.

Belge 05 tablosu → *görüntüde sola = görüntü üstü aracın SAĞI* → **montaj_yaw = +90**.
Tutarlılık: burun soldaysa görüntü üstü buruna göre 90° sağda kalır = aracın sağı. ✓

**Zincir doğrulandı (türetmeye güvenilmedi, koşuldu):** β = 0° olan sentetik arena verildi,
`fda_gorev_uret.py` çıktısı **CONDITION_YAW 270.00°** — `(β − montaj_yaw)` kuralının beklenen
değeri (düzeltilmiş işaretle yeniden koşuldu). Komut satırı ve tam çıktı `SAHA_20260920/MONTAJ_YAW.md` §Zincir doğrulaması'nda.

**Sonuç:** komut açısı **β − 90**; burun rotanın 90° **soluna**, aracın **SAĞ yanı** hedefe.
Pilot kartı cümlesi ve görev üretme komutu `MONTAJ_YAW.md`'de.

**Kapanmayan kısım — bilerek.** Bu bir *türetmedir*, uçuş kanıtı değildir. Her uçuşta,
hakem onayından önce ekrandan doğrulanacak: **YKİ haritasında rota aşağıdan yukarı akmalı.**
Yatay akıyorsa açı uygulanmamış; tersten akıyorsa işaret yanlış. Sol/sağ takası 0 puandır.

**L3 hükmü:** ÖLÇÜLMEDİ → **ÖLÇÜLDÜ (uçuşta ekrandan teyit edilecek)**.

---

## D-522 (geçici) · `AGENTS.md` push kuralı 23 gündür bayatmış — bulan: Codex

**Bulgu.** Codex, devir paketini okurken çelişki bildirdi:
> *"T-A push istiyor; verdiğin AGENTS.md ise push'u donduruyor. Bu nedenle push yetkisi
> varsaymıyorum. Yalnızca okudum; dosya değiştirmedim, commit veya push yapmadım."*

**Doğrulama (ölçüm, iddia değil).**
```
AGENTS.md:62  🔴 **`git push` — 2026-08-21'den beri DONDURULDU** (kullanıcı emri, ikinci emre kadar).
              Ayrıntı: `CLAUDE.md §5`.
```
Atıf verdiği `CLAUDE.md §5` ise şunu diyor: **"✅ PUSH DONDURMASI KALKTI — 2026-08-28, kullanıcı emri"**
(*"push artık istediğin zaman yapabilirsin"*). Yani "ikinci emir" **23 gün önce gelmiş**,
AGENTS.md o gün güncellenmemiş. Belge, **kendi atıf verdiği maddeyle** çelişiyordu.

**Düzeltme (2026-09-20).** `AGENTS.md:62` anayasayla hizalandı: push serbest; **kapı
kırmızıyken push yok** (D-360); kapı koşulamıyorsa bu **eksiklik olarak yazılır** ve push
**kullanıcı onayına** bağlanır.

**İki ders.**
1. **Codex doğru davrandı.** Çelişki görünce durdu, tahmin yürütmedi, sordu. Yetki belirsizken
   yazmamak doğrudur; bu davranış korunmalı.
2. **Mimarın kusuru.** Devir paketi T-A'da push istiyordu ama bilinen belge çelişkilerini
   listelemiyordu. Kullanıcı haklı olarak *"eksik bilgi vermişsin"* dedi. Pakete
   **Ç1…Ç8 çelişki tablosu** ve **asıl amaç + proje okuma sırası** eklendi.
   Bir devir paketi, devralanın **hangi belgeye güveneceğini** söylemeden tamam sayılmaz.

**Genel kural (bu depoda tekrarlıyor):** birden çok belge aynı konuyu farklı tarihlerde yazıyor.
**Çelişkide `CLAUDE.md` üstündür**; bayat olanı düzeltmek, üstünü örtmek değil, deftere yazmaktır.

---

## D-523 (geçici) · Yön değişikliği: SSH'siz pratik saha testi

**Kullanıcı kararı (20 Eyl akşamı):** *"Emir zaten YKS testini yapmış, gerek yoktu.
Artık Jetson'a bağlantı kurmadan düz gerçek pratik bir şekilde test edelim."*

**Uygulanan.** `SAHA_20260920/CODEX_DEVIR/03_PRATIK_SAHA_TESTI.md` yazıldı: sahada
**terminal açmadan**, yalnız yönlendirici penceresi + YKİ + Mission Planner ekranlarından
yürüyen altı bölümlü yordam — ön şart, açılış sırası, ekrandan okunacaklar, pervanesiz
hakem provası, uçuş, durdurma ölçütleri, kanıt toplama.
SSH yalnız **uçuş sonrası** kanıt toplamaya bırakıldı. T-B (araçlı onay testi) **düştü**.

**Kapanmayan kayıt — bilerek.** Emir'in YKS testinin `hakem_log.jsonl`'ı ve hükmü bu pakette
**yok**. Anayasa md. 6: *kanıtsız bulgu yazılmaz*. Bu yüzden `UYGUNLUK_OLCUMU.md` **L5**
kapatılmadı, "kullanıcı beyanı — kanıtı Emir'de" diye işaretlendi. İki yoldan biriyle kapanır:
(a) Emir'in günlüğü gelir, (b) `03` §3'teki pervanesiz prova geçer (**iki adıma bas, elini çek,
30–60 s düğme "ONAYLANDI ✓✓" kalıyor mu**) — aynı şeyi terminalsiz ölçer.

**Not.** Bu bir güvensizlik değil **yordamdır**: aynı disiplin bugün mimarın kendi
`montaj_yaw` türetmesini de çürüttü (D-521). Beyan hızlıdır, kanıt kalıcıdır.
