# EMİR İÇİN REHBER — 12 Eylül 2026

> Bu rehber, **yazılım kolunun tıkandığı ve senin açabileceğin** işleri anlatır.
> Her komut bu depoda **gerçekten koşuldu** ya da koşulamadıysa nedeni yazıldı —
> "çalışması lazım" diye yazılmış hiçbir satır yok.
>
> Kaynak: soru-cevap oturumu transkripti (`results/soru_cevap_20260912/`),
> `REVIEW_LOG.md` D-475, `TASK_QUEUE.md` T258–T260.

---

## 0. 🔴 ÖNCE BUNU OKU — takvim değişmiş olabilir

Soru-cevap oturumunda organizasyon şunu söylüyor (otomatik transkript,
`results/soru_cevap_20260912/transkript_otomatik.txt`):

| dakika | söylenen |
|---|---|
| `[01:32]` | "Biliyorsunuz **14'ünde** normalde raporlar teslim edilecekti." |
| `[01:57]` | "**14'ünde**… **sunumlarınızla raporlarınızla birlikte** sisteme yüklemeniz bizim için çok önemli." |
| `[10:01]` | "**14'ünün ertelenme ihtimali maalesef yok.**" |
| `[26:41]` | "Buradaki **bir haftalık erkene çekilme**…" |

Depodaki bütün belgeler (ve `tests/test_fdr_takvim_kapisi.py` adlı bir kapı testi)
**21.09.2026** diyor. İkisi aynı anda doğru olamaz.

**Senden istenen (T258):**
1. Organizasyonun duyurusunu/e-postasını bul → **14 mü 21 mi, yazılı kaynakla** teyit et.
2. Sonucu bana/ekibe bildir. Yazılım tarafı tarihi ancak yazılı kaynakla değiştirir
   (eski tarih silinmez, üstü çizilir — bu deponun kuralı).

**Ayrıca (T259): rapordan AYRI bir SUNUM isteniyor** — depoda hiç izi yok.
`[09:28]` "teknik ve ayrıntılı", `[11:17]` **şablon** kullanılacak, `[22:17]` **15 dakika**,
salı günü yüz yüze, sıra **kura** ile. `[04:16]` değerlendirme **gönderdiğiniz sunum**
üzerinden yapılacak. → **Şablonu indir**, kimin sunacağına karar ver.

---

## 1. T236 — FDA görev provası (SITL). "Windows gerekiyor" DOĞRU DEĞİL

### Neden bu iş önemli
FDA'da drone, alanın **merkezinde** belirli bir yöne dönük bekleyip görüntü almalı.
Bugünkü görev dosyasında **iki ölçülmüş kusur** vardı:

- `NAV_LOITER_TIME` satırı lat/lon **0,0** → "bulunduğun yerde bekle" demek; son
  waypoint bir **köşe** olduğu için drone **köşede** bekliyordu (D-451).
- `CONDITION_YAW` **hiç yoktu**; eklenmesi ve **LOITER'dan ÖNCE** konması gerektiği
  SITL'de ölçüldü: sonra konunca yaw **0/499** tuttu, önce konunca **500/500** (D-457).

**İkisi de artık yapısal olarak kapalı** — görev dosyası elle yazılmıyor, üreteçten
çıkıyor: `scripts/fda_gorev_uret.py`. Nöbetçi test bunu kilitliyor
(`tests/test_t235e_fda_gorev_ureteci.py`, **7/7 OK**; iki mutasyon denendi, ikisi de
test tarafından yakalandı).

### Windows meselesi — düzeltme
`config/pixhawk/README.md` §6.6'da "Windows'ta SITL ikilisi yok" yazıyor ve bu **doğru**:
ArduPilot SITL ikilisini **yalnız Linux x86_64** için yayınlıyor. Yani sorun "Windows
makinesi lazım" değil, tam tersi — **Linux lazım**. Üç yolun biri:

- **A)** Windows'ta **WSL2 + Ubuntu** (en kolay; `wsl --install` sonra aşağıdaki adımlar)
- **B)** Herhangi bir Linux makinesi (bu depo zaten bir Linux makinesinde açık)
- **C)** Mission Planner'ın kendi SIM'i (ölçüm otomatik olmaz, gözle bakarsın — son çare)

### Bu makinede benim DOĞRULADIĞIM adımlar (senin tekrarlayacağın)

```bash
# 1) SITL ikilisi (ArduCopter 4.5.7, Linux x86_64) — indirildi ve ÇALIŞTIĞI görüldü
mkdir -p ~/sitl && cd ~/sitl
curl -O https://firmware.ardupilot.org/Copter/stable-4.5.7/SITL_x86_64_linux_gnu/arducopter
chmod +x arducopter
curl -O https://raw.githubusercontent.com/ArduPilot/ardupilot/Copter-4.5.7/Tools/autotest/default_params/copter.parm

# 2) pymavlink (depo venv'ine kuruldu)
<DEPO>/.venv/bin/python -m pip install pymavlink

# 3) Provayı koş (görev dosyasını kendi üretir, ölçer, JSON yazar)
cd <DEPO>
.venv/bin/python -u -B scripts/t236_sitl_fda_provasi.py \
    --sitl ~/sitl/arducopter --defaults ~/sitl/copter.parm \
    --hiz 10 --ucus-tavan 150 \
    --cikti results/t236_sitl/olcum.json
```

**Beklenen çıktı:** ekrana sırayla `SITL bağlandı` → `GPS fix hazır` → `görev
yükleniyor (9 satır)` → `MISSION_ACK: 0` → `ARM edildi` → `AUTO + MISSION_START` →
waypoint sırası → sonunda JSON özeti. `durum` alanı **GEÇTİ / DÜŞTÜ / ÖLÇÜLEMEDİ**
olur.

**Kapı (10 Eylül'de, ölçümden ÖNCE yazıldı — değiştirme):** bekleme süresince
(ilk 10 s hariç) yatay konum merkezden **≤ 2,0 m**, yaw hedeften **≤ ±5°**, irtifa
**± 1,0 m** — üçü de zamanın **≥ %90**'ında.
Kaynak: `results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md` §4.

### ⚠ Ben neyi koşamadım ve neden
Bu oturumun güvenlik kısıtı, bir uçuş kontrolcüsüne **görev yükleme / ARM / AUTO**
komutu göndermeyi engelliyor (simülatörle gerçek aracı ayırt edemiyor). Bu yüzden:

| adım | durum |
|---|---|
| SITL ikilisi indi, açıldı | ✅ **doğrulandı** (sha256 `b9035c08f003ab29…`) |
| pymavlink bağlandı, HEARTBEAT geldi | ✅ **doğrulandı** |
| GPS 3D fix (fix_type 6) ~2 s'de | ✅ **doğrulandı** |
| Görev üreteci doğru dosya üretiyor | ✅ **doğrulandı** (7/7 test + 2 mutasyon) |
| **Görev yükleme + ARM + AUTO + ölçüm** | ❌ **KOŞULMADI** — bu oturumda engelli; **sen koşacaksın** |

Yani sonuç `ÖLÇÜLEMEDİ` olarak duruyor; senin koşumun onu **GEÇTİ ya da DÜŞTÜ** yapar.
Ne çıkarsa yazılır — düşerse de yazılır, eşik gevşetilmez.

---

## 2. Saha günü: gerçek köşelerle görev dosyası üretme

Organizasyon koordinatları **önceden vermiyor** (`[19:04]` "alana girdikten sonra
paylaşabiliriz"). O yüzden üreteç parametrik: köşeleri **o gün** girersin.

```bash
cd <DEPO>
.venv/bin/python -B scripts/fda_gorev_uret.py \
    --kose <LAT1> <LON1> --kose <LAT2> <LON2> \
    --kose <LAT3> <LON3> --kose <LAT4> <LON4> \
    --baslangic-kenari 0 \
    --montaj-yaw <A9_OLCUMU_DERECE> \
    --irtifa 32 \
    --cikti config/pixhawk/fda_gorev_saha.waypoints
```

- **Köşeler saat yönünde** girilir (4 tane).
- `--baslangic-kenari 0` → 1. ve 2. köşe arasındaki kenar **Başlangıç** kenarıdır;
  yön (β) bu kenarın ortasından **karşı** kenarın ortasına bakar.
- `--montaj-yaw` → **A9 ölçümü**: İHA burnu bilinen bir çizgiye bakarken görüntünün
  yukarısının burna göre açısı. Ölçülmediyse `0` girme — **önce ölç**, yoksa yaw komutu
  yanlış yöne döner.
- `--irtifa 32` → 4:3 kamera kipinde 32 m yeter; **16:9 kırpma** varsa **40** gir
  (`FENCE_ALT_MAX` 50 m'nin altında kalmalı, betik zaten reddediyor).

Çıktıyı Mission Planner'da `Flight Plan → Load WP File` ile yükle
(`config/pixhawk/README.md` §1).

---

## 3. Bugünkü atölye (A1–A13) — sonuçlar nereye

Kâğıt zaten hazır: **`ATOLYE_TEST_GUNU_20260912.md`** (sırayla uygulanır).
Sonuçlar: **`results/atolye_20260912/`** altına, `SONUC_SABLONU.md` biçiminde.
Her maddede **ÖLÇÜLDÜ / ÖLÇÜLEMEDİ** kutusu var — boş bırakma, "ölçemedik" de bir
sonuçtur ve rapora öyle geçer.

**Yazılımı doğrudan açan iki madde:**

| madde | neyi açar |
|---|---|
| **A9-ek — kamera kipi (4:3 mü 16:9 mu) + montaj yaw'ı** | FDA irtifası (32 vs 40 m) ve `--montaj-yaw` girdisi. Bu ölçülmeden görev dosyası doğru üretilemez. T235'in koşullu kolu da buna bağlı. |
| **A6-ek — telsizde ECC açık mı kapalı mı** | T250: rota uzayınca bant genişliği yetip yetmeyeceği. Ölçülen gerçek veri hızı **871,96 B/s = SiK'in %15,1'i** (12 Eylül, `results/t243_mesaj_boyutu/`), ama 64 waypoint + ECC senaryosunda bütçe aşılıyor. |

⚠ **Kamera hâlâ elimizde yok** — A9/A10 bu yüzden koşulamıyor; bu bir "eksik" değil
**tedarik** sorunu, raporda öyle duruyor.

---

## 4. Senden/ekipten bekleyen diğer maddeler

| iş | ne lazım | neyi açar |
|---|---|---|
| **T211** | Motor etiketi **fotoğrafı** + veri sayfası (4S, 10×4,5 satırı: itki g, akım A, sürekli akım) + pilli araç **tartısı** | İtki bütçesi kapısı. **TIKAYICI**: bütçe kapanmadan bir sonraki güç verme yok. |
| **T239** | İKA **iz genişliği** ve tekerlek çapı: şerit metreyle iki ölçüm + fotoğraf (ya da SolidWorks ölçüsü) | `CONTRACTS.md` 0,39 m **TAHMİN** diyor, takım arkadaşının modeli 0,319 m — çelişki. Sürüş/dönüş doğruluğu buna bağlı. |
| **T223** | **Hover logu** (.bin) + video → `results/ucus_loglari/<tarih>/` | "Başarıyla hover yapabiliyoruz" beyanını kanıta bağlar (D-439). |
| **T222** | Simülasyon videosunu YouTube (liste dışı) + Drive'a yükle, **iki linki** bildir | FDR §3.3.3.3 / §4.7 — video hazır, yalnız link eksik. |
| **T230** | MK15 saha maddeleri (kumanda HDMI portu, Air Unit gerilim aralığı, camdan cama gecikme 5 ölçüm) | FDR §3.3.1.1.13 video zinciri. |
| **T237** | Organizasyona: FDA **tarihi** (şartname 30.09–03.10 mu, 21 Eylül Adıyaman mı) | Takvimin tamamı. |

**T237'nin diğer soruları soru-cevap oturumunda CEVAPLANDI** (D-475), tekrar sormaya gerek yok:
- `[40:38]` Şartnamede **kırmızı olan H harfinin kendisi**, içindeki 2×2 m kutu değil.
- `[19:04]` Enkaz alanı koordinatları **önceden verilmiyor**, alanda paylaşılacak.
- `[33:00]` "**Bir başlangıç noktası belirteceğiz**, başlayacağınız yer belli olacak."
- `[34:23]` YKS'de açık yolu **nasıl gösterdiğin serbest** ("şartımız yok, yaratıcılığınız").

---

## 5. Adıyaman'da (21 Eylül) ne bekleniyor — transkriptten

| konu | organizasyonun sözü |
|---|---|
| Ne getirilecek | `[21:38]` "**Lütfen İKA'larınızı yükleyip getirmeyin. Sadece drone'unuzu bekliyoruz.**" |
| Neden | `[14:25]` "Bir **algoritma doğrulama** aşaması." |
| Kaç yol | `[29:12]` "**Sadece bir tane yol aktif olacak.**" `[30:20]` "Tek bir açık yol var ve bunu tespit etmenizi istiyoruz." |
| Kalkış/iniş | `[15:31]` "İniş-kalkış alanınız **farklı bir yer** olacak"; `[45:21]` özel **işaret yok**, "belli bir alan" olacak. |
| Otonomi | `[05:28]` **kalkış ve iniş dâhil tam otonom**; `[35:53]` yalnız acil durumda manuele izin. |
| Paraşüt | `[16:18]` Adıyaman'da **paraşüt şartı yok**. |
| Süre | `[35:20]` uçuş **10 dakika** içinde bitmeli. |
| **Puanlama** | `[18:52]` "Bunu yaptığınızda **bütün puanı** alırsınız, yapamazsanız **0**." — yani **hep ya da hiç**: otonom uçarken **real-time** olarak yolu bulduğunu YKS'de göstermek. |

🔴 **Bir uyarı da bize çıktı** (`[28:42]`–`[29:18]`): "Sisteminizi **sınırlı olarak 3 yolu**
tespit etmek üzerine kurguladıysanız **bizim beklentimiz bu değil**… beklentimiz **açık
olan bir yolu** tespit edebilmesi… o zaman tasarımınızda **bir yanlışlık var** demektir."
Bizim mesaj sözleşmemizde `road` alanı bugün `1=sol, 2=orta, 3=sağ` ile sınırlı — tam
olarak o kilit. Kararı mimar verecek (**T260**), ölçüm olmadan koda dokunulmadı.

---

## 6. Bu rehberdeki her iddianın kaynağı

| iddia | kaynak |
|---|---|
| Görev dosyasının iki kusuru | `REVIEW_LOG.md` D-451 (loiter köşede), D-457 (yaw sırası, SITL 0/499 vs 500/500) |
| Üretecin doğruluğu | `tests/test_t235e_fda_gorev_ureteci.py` 7/7 + 2 mutasyon (bu oturumda koşuldu) |
| SITL'in Linux-only olduğu | `config/pixhawk/README.md` §6.6 + firmware sunucusunda yalnız `SITL_x86_64_linux_gnu` |
| SITL'in bu makinede açıldığı | bu oturumda koşuldu (heartbeat + GPS fix 6) |
| Veri hızı %15,1 | `results/t243_mesaj_boyutu/olcum.json` (gerçek UDP loopback, 10 s) |
| Organizasyonun sözleri | `results/soru_cevap_20260912/transkript_otomatik.txt` — ⚠ **otomatik transkript, hata içerir**, kritik kararlar önce videodan teyit edilmeli (`OKUBENI.md`) |
