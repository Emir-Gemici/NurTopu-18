# 02 — Kalan işler (ön kayıtlı geçme ölçütleriyle)

> **Ön kayıt kuralı (D-225):** her görevin geçme ölçütü **koşudan önce** yazılıdır ve
> koşu sonrası **gevşetilmez**. Eşik tutmazsa görev düşer; eşik değiştirilmez.
> **Kanıtsız bulgu yazılmaz** (anayasa md. 6). Koşulan komut + gerçek çıktı `REVIEW_LOG.md`'ye.

🔴 **GÜNCELLEME (20 Eyl akşamı, kullanıcı kararı).** Öncelik değişti:

> *"Emir zaten YKS testini yapmış... artık Jetson'a bağlantı kurmadan düz gerçek pratik
> bir şekilde test edelim."*

**Yeni öncelik: `03_PRATIK_SAHA_TESTI.md` → T-C → T-E → T-A.**
**T-B DÜŞTÜ** (aşağıda gerekçesi). T-D fırsat bulunursa. T-F ve sonrası uçuş sonrası.

⚠ **Jetson'a SSH ile bağlanmak artık akış dışıdır.** Saha testi terminal açmadan,
yalnız yönlendirici penceresi + YKİ + Mission Planner ekranlarından yürür.
SSH yalnız uçuş sonrası kanıt toplamada kullanılır.

---

## T-A · Bugünün işini commit + push et  🔴 İLK İŞ

**Neden acil:** `SAHA_20260920/` tamamı **takip edilmiyor** (`?? SAHA_20260920/`).
Plan, uygunluk ölçümü, kanıt defteri (D-517…D-521), montaj açısı belgesi, test aracı ve
kanıtlar **yalnız bu diskte**. Makineye bir şey olursa günün tamamı gider.

**Kapsam:** `SAHA_20260920/` + `master`'daki itilmemiş `e4f4edc5`.

**Yapılacak:**
1. `git add SAHA_20260920/` → `git diff --cached --stat` ile **üretim kodu dokunulmadığını** göster.
2. Commit, yazar **`trs-1342 <socialmediaoftrs1342@gmail.com>`**, **AI atfı YOK**.
3. `git push`.

**Geçme ölçütü:**
- `git diff --cached --name-only` çıktısında `codes/`, `comms/`, `scripts/` altında **hiçbir dosya olmamalı**
  (yalnız `SAHA_20260920/` altı). Varsa commit edilmez, önce incelenir.
- Commit mesajında hiçbir atıf satırı olmayacak (`git log -1 --format=%B` ile doğrula).

**⚠ ÇELİŞKİ ÇÖZÜLDÜ (20 Eyl, Codex'in bulgusu).** `AGENTS.md:62` *"push 2026-08-21'den beri
DONDURULDU"* diyordu; atıf verdiği `CLAUDE.md §5` ise dondurmayı **2026-08-28'de kaldırmıştı**.
AGENTS.md **23 gün bayat** kalmış. 2026-09-20'de anayasayla hizalandı. **Push yasak değildir.**
Codex'in "push yetkisi varsaymıyorum" demesi **doğru davranıştı** — çelişkide durup sormak esastır.

**⚠ Dürüstlük notu (mimar):** anayasa §5 "itilen şey kapıdan geçmiş olmalı" der ve
**bu makinede genel kapı koşamaz** (numpy/opencv yok). Değişen hiçbir dosya kapının konusu
değildir — bu, kuralın sağlandığı anlamına gelmez, **sağlanamadığı** anlamına gelir.
Bu istisna commit mesajına ya da deftere **yazılacak**, sessizce geçilmeyecek.
**Kullanıcı onayı alınmadan push YAPILMAZ.**

---

## T-B · Canlı hakem onay testi — ⛔ **DÜŞTÜ / DEVREDİLDİ** (20 Eyl akşamı)

**Kullanıcı beyanı:** *"Emir zaten YKS testini yapmış, gerek yoktu."*

⚠ **Kanıt bu pakette YOK.** Emir'in koşusunun hakem günlüğü (`hakem_log.jsonl`), çıktısı ve
geçme/düşme hükmü elimizde değil. Anayasa md. 6 gereği **kanıtsız bulgu deftere yazılmaz**;
bu yüzden `UYGUNLUK_OLCUMU.md`'deki **L5 satırı kapatılmadı**, "kullanıcı beyanı — kanıtı
Emir'de" olarak işaretlendi.

**Yapılacak (küçük iş):** Emir'den koşunun `hakem_log.jsonl`'ını ve çıktısını iste.
Geçme ölçütü sağlanmışsa L5 kapanır. Sağlanmamışsa aşağıdaki kurulum hazır bekliyor.

**Pratik yedek:** `03_PRATIK_SAHA_TESTI.md` §3'teki pervanesiz hakem provası **aynı şeyi
ölçer** ve terminal istemez: iki adıma bas, **elini çek, 30–60 s bekle**, düğme
"ONAYLANDI ✓✓" kalıyor mu. Onay duruyorsa D-516 düzeltmesi sahada çalışıyordur.

<details><summary>Araçlı kurulum (gerekirse) — bugün koşuldu, tekrarlanabilir</summary>

**Durum:** araç hazır ve **kendini kanıtladı** (3/3 mutant, D-518). Bugün iki kez koşuldu:

**Durum:** araç hazır ve **kendini kanıtladı** (3/3 mutant, D-518). Bugün iki kez koşuldu:
1. `OSError 22` — aracın kendi kusuru, düzeltildi (`--dinle-adres`), gerileme testi temiz.
2. **Hakem düğmeye basmadı** → hüküm **GEÇERSİZ** (düştü değil). Hakem günlüğünde
   `ONAY/DOGRULA/GORULDU` olayı **sıfır**; `ROTA_ALINDI` 171, `ROTA_YOK` 9.

**Koşu boşa gitmedi, üçünü kanıtladı:** 171 OPEN_ROUTE YKİ'ye ulaştı ve hepsi `ankor:true`
(geometri kapısı **açık**, düğme basılabilirdi) · 9 NO_ROUTE → **9 otomatik ACK Jetson'a döndü**
(dönüş yolu çalışıyor) · Jetson'ın yeni kurulan sürümü sorunsuz çerçeve üretiyor.

**Kurulum (bugün çalıştı, aynen tekrarlanabilir):**

```bash
# 1) YKI — bu laptopta, saha dalindan
cd /home/trs/projects/navitas-wt-bilgilendirme
python3 -B comms/yks_gui.py --fda --bind 0.0.0.0:5005 \
    --ika 127.0.0.1:5006 --iha 192.168.55.1:5193 \
    --hakem-log <kayit_yolu>/hakem_log.jsonl

# 2) Test araci — JETSON'da (once scp ile kopyala)
ssh jetson 'cd /home/n4vitas && python3 -u rota_testi_yeniseq.py \
    --hub 192.168.55.100:5005 --dinle-adres 0.0.0.0 --dinle-port 5193 \
    --sure 100 --no-route-her 20 --serit 2 --seq-basla 9000 \
    --kayit /home/n4vitas/onay_testi.json'
```

⚠ `--ika` **zorunlu** (UDP kipinde). `--dinle-adres 0.0.0.0` **zorunlu** — 127.0.0.1'e bağlı
soket loopback dışına yazamaz.

**İNSAN adımı (atlanamaz):** rota görünür görünmez **"1) TESPİTİ DOĞRULA"** → ardından
**"2) YKS'DE GÖRÜLDÜ — ONAYLA"** → **sonra elini çek**. İkinci basıştan sonra tekrar basmak
**testi geçersiz kılar** — ölçülen şey onayın kendiliğinden kalıcı olup olmadığıdır.

**Geçme ölçütü (ön kayıt, değiştirilemez):**
1. İlk ACK'ten sonra **her 10 s'lik pencerede en az bir yeni-seq ACK**.
2. Her NO_ROUTE'tan sonra **10 s içinde** yeniden OPEN_ROUTE ACK.
3. **Hiçbir ACK gönderilmemiş bir seq'e ait olmayacak.**

Araç `--pencere` ile gevşetilebilir ama o zaman ekrana **"OLCUT GEVSETILDI — bu koşu saha
kanıtı değildir"** basar ve kayda `gevsetildi: true` yazar. **Saha kanıtı 10 s ile alınır.**

**Geçerlilik ön şartı:** hakem günlüğünde onay olayı **görülmeli**. Görülmüyorsa sonuç
"DÜŞTÜ" değil **GEÇERSİZ**'dir; tekrar koşulur.

**Sınır — abartılmayacak:** bu kurulumda **telsiz devrede değil** (USB ağı üzerinden).
Gerçek `yks_gui` + gerçek protokol + gerçek Jetson'ı sınar, **taşıma katmanını sınamaz**.
Telsizli tekrar ayrı bir görevdir.

**Düşerse:** uçuşta hakem her karede yeniden basmak zorunda kalır → görev akışı yürümez.
Karar kullanıcıya gider: kod düzeltmesi mi, elle prosedür mü. **Kendi başına kod yazma.**

</details>

---

## T-C · Kamera lens odağı  🔴 ZİNCİR KOPUK

**Durum:** elektriksel zincir **tamam** (fps 10, 0 düşen kare), **görüntü kullanılamaz**.
İndirilen kare: `../kanit/kare_20260920.jpg` — düz gri, detay yok, köşelerde macenta.

**Sebepler (ucuzdan pahalıya):** lens koruma filmi/kapağı · odak halkası ayarsız
(IMX477 + ~6 mm lens elle odaklanır) · ISP lens gölgeleme kalibrasyonunun lense uymaması (macenta köşeler).

**İNSAN adımı:** film/kapak varsa çıkar; kamerayı 3–5 m uzağa doğrult; lens halkasını
yavaşça çevirerek odakla.

**Codex'in işi — ölçümü sağla:**
```bash
ssh jetson 'curl -s -o /tmp/kare.jpg http://127.0.0.1:8080/kare.jpg && ls -l /tmp/kare.jpg'
scp jetson:/tmp/kare.jpg <yerel>/kare_<zaman>.jpg
```

**Geçme ölçütü:** kare üzerinde **kenar keskinliği ölçülebilir olmalı** — gözle "net"
demek yeterli değil. Basit ölçüt: gri tonlu karenin **Laplacian varyansı**, odaklama
öncesi/sonrası **aynı sahnede** karşılaştırılır ve belirgin şekilde artmalıdır.
⚠ Bu ölçüm `numpy`/`opencv` ister; bu makinede **yok**. Ya Jetson'da koş (orada var),
ya kullanıcı onayıyla kur. **Ölçmeden "odak tamam" yazma.**

---

## T-D · Modeli GERÇEK zeminde ölç (L1)  🔴 Hiç yapılmadı

**Neden:** genel kapı 15/15 geçiyor ama **sentetik ve kusursuz maskeyle**. Kullanıcı beyanı
(20 Eyl): model **gerçek arena zemininde hiç denenmedi**. Gazebo'da düz/dokusuz zeminde
model karelerin **%93'ünü "blocked"** saymıştı. Uçuşa gerek yok, arenaya bile gerek yok.

**Yapılacak:** T-C bittikten sonra kamerayı gerçek zemine doğrult, ham kareler al, üretim
karar yolunu (`rpi_inference`, `analyze_path`) **çevrimdışı** o kareler üzerinde koştur.

**Geçme ölçütü:** yok — bu bir **keşif ölçümüdür**, eşiği yoktur. Çıktı: kaç karede rota
üretildi, kaçında NO_ROUTE, hangi şerit. Ham kareler + çıktı repoya konur.
**Sonuç kötüyse bu bir başarısızlık değil, zamanında öğrenilmiş bir gerçektir.**

---

## T-E · Görev dosyası üret (arena köşeleri bilinince)

**Ön şart:** arena dört köşesinin GPS'i. Ekip alana girmeden **bilinmiyor**.

```bash
cd /home/trs/projects/navitas-unified-20260822     # master — betik burada
python3 scripts/fda_gorev_uret.py \
    --kose <lat1> <lon1> --kose <lat2> <lon2> \
    --kose <lat3> <lon3> --kose <lat4> <lon4> \
    --baslangic-kenari <i> --montaj-yaw 90 --irtifa 32 \
    --cikti config/pixhawk/fda_gorev_saha_20260921.waypoints
```

🔒 **`--montaj-yaw 90`** — bugün ölçüldü (D-521). Köşeler **saat yönünde**.

**Geçme ölçütü:**
- Çıktıda `CONDITION_YAW komutu` = `(β − 90) mod 360` olmalı, betiğin bastığı β ile tutarlı.
- `CONDITION_YAW` satırı `NAV_LOITER_TIME`'dan **ÖNCE** gelmeli (betik garanti eder, nöbetçi
  test `tests/test_t235e_fda_gorev_ureteci.py`); üretilen dosyada **gözle de doğrula**.
- `LOITER_TIME` satırında lat/lon **0,0 OLMAYACAK** (merkez açıkça yazılı olmalı — D-451).

⚠ `--montaj-yaw` **atlanırsa** varsayılan 0'dır → görüntü 90° yan → rota yatay → şerit araması anlamsız.
⚠ İşaret **eksi** yazılırsa (`-90`) görüntü 180° ters → **sol/sağ şerit takas → 0 puan.**

**🔴 Uçuşta, hakem onayından ÖNCE, her seferinde:**
> **YKİ haritasında rota AŞAĞIDAN YUKARI akmalı.**
> Yatay akıyorsa açı uygulanmamış. Yukarıdan aşağı akıyorsa işaret ters.
> Bu bakış atlanmayacak — bugün bildirimdeki tek rakam farkı (4 mü 6 mı) işareti
> tersine çevirdi ve mimar yanlış türetti. **Türetmeye değil ekrana güvenilecek.**

---

## Uçuş sonrasına bırakılanlar (bugün YAPILMAYACAK)

| # | İş | Not |
|---|---|---|
| T-F | `--ub-referans` eksik → **YKS alan ihlali denetimi YAPILAMIYOR** (şartname SS6.2/SS6.4) | Referans noktası **sahada ölçülmeli** — insan işi. `RPI_EK_ARGS`'a eklenir |
| T-G | K8 (p95 212/278 ms, eşik 200) — kaldıraç: aynı kararı yalnız değişince ya da 1 Hz'de gönder | Kod ister. **Eşik gevşetilmez** |
| T-H | Dal birleştirme (108/92) + `REVIEW_LOG` **D-505 numara çakışması** | İki çizgide iki farklı D-505 |
| T-I | `IKA_IZ_GENISLIGI_M`: master **0.39 (bayat tahmin)** → **0.4595 (ölçüldü, D-472)** | master yanlış; kapı koşulabilen makinede düzeltilir |
| T-J | Tam süit kırmızı (3119 test, 21 failure + 11 error; tabanda 33 → bu dalda 32, **yeni gerileme yok**) | Anayasa §5 borcu |
| T-K | MAVProxy `--streamrate` iki kez geçiyor — tek yere alınmalı | Sessiz gerileme riski |
| T-L | Belgelerde "kırmızı ≤ 4 s" → "sarı 3 s, kırmızı 5 s" | `SAHA_YOL_HARITASI_20260916.md:892` vd. |
| T-M | `3f13b2e1` "WIP DENETLENMEDI" (Codex'in YKS tek-rota paneli, 14 Eyl) denetlenmeli | Defterde denetim kaydı yok |

---

## Devralana son söz

Bugün iki kez aynı hata yapıldı ve ikisi de **pahalıydı**: mekanik bir arıza yazılımda arandı.
13–15 Eyl'de beş kamera overlay'i denenmişti — konnektör kırıkken hiçbiri çalışmazdı.
19 Eyl 18:40'ta USB kopmuşken "Jetson heartbeat'i durdu" denildi, ~30 dakika gitti.
Bugün de kablonun A ucu Jetson'a takılıydı, ~1 saat gitti.

**Bir şey çalışmıyorsa, önce en alttaki fiziksel katmanı ölç.** `i2cdetect`, `lsusb`,
`ip -brief addr`, `dmesg`. Yazılım katmanına çıkmadan önce elektriğin geldiğini kanıtla.
