# ÖĞREN — ADIYAMAN HAZIRLIĞI · Buradan başla

> **Kim için:** Halil (görüntü işleme / uçuş yazılımı / sistem mimarisi sorumlusu, DDR referansına göre).
> **Ne için:** 20–27 Eylül 2026 aralığında Adıyaman'da FDR üzerinden sorulacak sorulara **yazılımcı olarak** hazır olmak
> ve projeye yeniden hâkim olmak. Biçim bilinmediği için hem belge-jürisi hem saha-hakemi soruları hedeflendi.
> **Yazan:** Jetson'daki Claude oturumu (Fable 5.1), 9–10 Eylül 2026, Halil'in isteğiyle. Depo: `yazilim-takimi/navitas`
> master `181c310` (7 Eyl) + `jetson/oturum-20260909`. Her sayı bir dosyaya bağlıdır; bağlanamayan sayı **yazılmadı**.
> Projenin kendi kuralı burada da geçerli: **ÖLÇÜLEMEDİ ≠ GEÇTİ.** Jüriye de böyle söylenir.

---

## 1. Bu klasör nasıl okunur

Dosyalar **projenin gelişim sırasında** dizildi (Mayıs'tan Eylül'e) ve her dosya **genelden ayrıntıya** iner:

```
Seviye 1 — BİR CÜMLE + BÜYÜK RESİM     (2 dakika; jüriye söyleyeceğin şey)
Seviye 2 — NASIL ÇALIŞIR                (10 dakika; mekanizma, akış, neden böyle)
Seviye 3 — AYRINTI VE SAYILAR           (30 dakika; sabitler, eşikler, ölçümler, dosya:satır)
Jüriye 30 saniyede                       (ezber kalıbı)
Kendini sına                             (5–10 soru; cevaplar dosyanın sonunda)
Kaynaklar                                (hangi dosyaya bakılır)
```

Her dosyayı ilk turda **yalnız Seviye 1 ve "Jüriye 30 saniyede"** kısımlarıyla oku (toplam ~40 dk). İkinci turda
Seviye 2'leri, üçüncü turda Seviye 3'leri ve sınamaları yap. Soru bankasına (14) en son gel.

## 2. Okuma sırası ve zaman planı

| # | dosya | konu | 1. tur | 2.+3. tur |
|---|---|---|---|---|
| 01 | `01_YARISMA_VE_GOREV.md` | Şartname: görev, puan, takvim, iki ayrı araç | 5 dk | 30 dk |
| 02 | `02_BASLANGIC_VERI_VE_ILK_MODEL.md` | Mayıs–Temmuz: veri kaynakları, YOLOv8-seg nedir, ilk hat | 5 dk | 40 dk |
| 03 | `03_MIMARI_KARAR_SERBEST_ALAN.md` | 3–4 Ağustos: A/B/C kararı, üç katman, değişmez kural | 5 dk | 40 dk |
| 04 | `04_ROTA_COSTMAP_VE_KARAR.md` | Maske → costmap → A* → şerit kararı → ret sebepleri | 5 dk | 60 dk |
| 05 | `05_SOZLESMELER_VE_KAPILAR.md` | CONTRACTS, sınıf id, çerçeveler, genel kapı, ön kayıt, mutasyon | 5 dk | 45 dk |
| 06 | `06_MODEL_SURUMLERI_VE_KABUL.md` | v3→v36 tarihçesi, T66 kabul kümesi, K0–K8, terfi kararı, export | 5 dk | 60 dk |
| 07 | `07_HABERLESME_YKS_IKA.md` | Protokol, ACK, IKA_GO, iniş kanıtı, hakem ekranı, FDA kipi | 5 dk | 60 dk |
| 08 | `08_IKA_VE_SIMULASYON.md` | İKA sürüş, sürücü soyutlaması, Gazebo, puan hesaplayıcı | 3 dk | 30 dk |
| 09 | `09_SAHA_FAZ_B_PIXHAWK.md` | Eylül: Pixhawk/ArduCopter, failsafe, çoğullayıcı, saha günleri | 5 dk | 45 dk |
| 10 | `10_JETSON_VE_URETIM_PAKETI.md` | Jetson paketi, tek komut açılış, engine, FPS, 6 ve 9 Eylül | 5 dk | 45 dk |
| 11 | `11_GELISTIRME_SURECI_VE_AJANLAR.md` | Anayasa, çok-ajanlı düzen, kanıt defteri, push kapısı | 5 dk | 30 dk |
| 12 | `12_KUSUR_TARIHCESI_VE_DERSLER.md` | D-kayıtlarından dönüm noktaları ve dersler | 5 dk | 45 dk |
| 13 | `13_FDR_HARITASI.md` | FDR'nin 7 bölümü, puanlar, ne var/ne yok, kanıt dizinleri | 5 dk | 45 dk |
| 14 | `14_ADIYAMAN_SORU_BANKASI.md` | Olası sorular + model cevap + kanıt yolu | — | 120 dk |
| 15 | `15_SOZLUK.md` | Terimler ve kısaltmalar | başvuru | — |
| 16 | `16_KENDINI_SINA_TOPLU.md` | Karışık final sınaması | — | 60 dk |
| 17 | `17_ACIK_KALEMLER_VE_DURUST_CEVAP.md` | "Bilmiyoruz / ölçmedik" nasıl söylenir; açık kalemler listesi | 5 dk | 20 dk |

Toplam: 1. tur ≈ 1,5 saat · 2.+3. tur ≈ 12 saat · soru bankası + sınama ≈ 3 saat.

## 3. Projeyi bir paragrafta

NAVITAS, TEKNOFEST **İleri Otonom Sistemler Tasarım ve Operasyon Yarışması** için bir İHA + İKA + yer istasyonu
sistemidir. İHA moloz alanının (HTAB) üstünden geçerken kamera görüntüsünde **üç güzergâhtan hangisinin açık olduğunu**
bulur, kararını canlı olarak yer istasyonuna (YKS) ve kara aracına (İKA) yollar; hakem YKS ekranında onaylar; İHA iner;
İKA açık güzergâhtan hedef bölgeye (kırmızı H brandası) otonom gider. Yazılımın omurgası: kamera karesi → YOLOv8-seg
"zemin/engel" maskesi → uçuş kontrolcüsünden gelen irtifayla ölçek → serbest alan üzerinde A* tanık yol → şerit kararı →
her karede tam bir mesaj (`OPEN_ROUTE` ya da `NO_ROUTE`). Mimarinin değişmez kuralı: **serbest alan otoritedir, nesne
katmanı yalnızca çıkarır**; şüphede sistem susmaz, **`NO_ROUTE` der ve sebebini yazar** (fail-closed), çünkü şartname
yanlış güzergâha **0 puan** verir.

## 4. Bugünkü durum — tek bakışta (10 Eylül 2026)

| ne | durum | kanıt |
|---|---|---|
| Üretim modeli | `navitas-seg-v36-512` (YOLOv8m-seg, 512 px, PyTorch `.pt`) | `config/model_registry.json` |
| Genel kapı | 15/15 · 15/15 (PC 7 Eyl, Jetson 9 Eyl) | `results/push_kapisi/20260907_015733/`, `results/jetson_log_20260909/` |
| Tam süit | PC: 2138 OK (7 Eyl) · Jetson: 2204, 32 ortam kırmızısı | aynı dizinler |
| Kabul kapıları (sentetik, n=260) | K0–K8 + K5A **10/10 GEÇTİ** (1 Eyl) | `results/fdr/GORUNTU_ISLEME_KANIT.md` |
| Gerçek kare kapısı | v36 iki ön kayıtlı eşiği **GEÇMEDEN** terfi etti (insan kararı, D-293) | `CONTRACTS.md` §12 |
| Jetson | Orin Nano 4 GB kuruldu; FPS pt 1,35/1,06 · engine 1,58/1,33 (eşik 0,61) GEÇTİ; uçuş `.pt` ile | `results/jetson_20260906/` (D-431) |
| Kamera / Pixhawk / SiK gerçek hat | **ÖLÇÜLEMEDİ** (donanım bağlı değildi) | D-431, D-428 |
| İKA gerçek motor sürücüsü | **YOK** (arayüz + kabul turu hazır, arka uç seçilmedi) | CONTRACTS §7.2, T149 |
| Saha (5–6 Eyl) | Pixhawk 7 kalem kapandı; RC failsafe **DÜŞTÜ**; uçuş yapılmadı; devrilme | D-426, D-428, D-429, D-434 |
| Motor künyesi | 5008 iade, X2220 980KV **BEYAN** (etiket/tartı bekliyor, T211) | D-435, D-436 |
| FDR | taslak v1, 3.3/4/6 güçlü; 3.1/3.2 (uçuş bilimleri, yapısal) **YOK** | `FDR/YONERGE_HARITASI.md` |

## 5. Üç cümlelik "jüri açılışı" (ezberle)

> "Sistemimiz havadan açık güzergâhı bulur ve bu kararı hakemin canlı doğrulayabileceği biçimde yere aktarır.
> Mimarinin kuralı serbest alan otoritesidir: zemin olmayan her şey engeldir, hiçbir işlem serbest alanı büyütemez,
> şüphede rota üretmeyiz ve sebebini yazarız. Her sayımız bir ölçüm dosyasına bağlıdır; ölçmediğimizi geçti diye yazmayız."

## 6. Nerede ne var (depo haritası — sık kullanacakların)

| yol | ne |
|---|---|
| `CLAUDE.md` | anayasa (kurallar) |
| `CONTRACTS.md` | modüller arası sözleşmeler — **tek doğruluk kaynağı** |
| `ARCHITECT_PLAN.md`, `RESEARCH_NOTES.md` | mimari kararlar ve gerekçeleri (3–4 Ağustos) |
| `REVIEW_LOG.md` | kusur/karar defteri, D-1…D-436 (yalnız eklenir) |
| `TASK_QUEUE.md` | iş kuyruğu, T1…T211 |
| `codes/` | algı + karar: `rpi_inference.py`, `karar_sozlesmesi.py`, `costmap_path_finder.py`, `model_registry.py`, `sinif_semasi.py` |
| `comms/` | haberleşme + YKS: `protocol.py`, `iha_sender.py`, `ika_receiver.py`, `iha_komut_alici.py`, `inis_kaniti.py`, `seri_hub.py`, `yks_gui.py` |
| `config/model_registry.json` | model kayıt defteri (sha, imgsz, kabul kümesi) |
| `config/pixhawk/` | ArduCopter parametreleri, görev planı |
| `jetson_paket/` | Jetson'a giden paket (kod aynası, systemd, `jetson_baslat.sh`) |
| `scripts/olcum/` | 139 numaralı ölçüm betiği (tarihsel sıra) |
| `results/` | ham ölçüm çıktıları (kanıt) |
| `FDR/` | rapor bölümleri + yönerge haritası |
| `SAHA_RUNBOOK.md`, `SAHA_HAZIRLIK_PLANI_20260903.md`, `FAZ_B_GUN_PLANI.md` | saha yordamları |
| `tests/` | 190 test dosyası, ~2200 test |

Bu klasörün kaynak özetleri `ozet/` altındadır (dokuz alan incelemesi, her sayı dosya:satır atıflı, 3–6 bin kelime):
A codes · B comms · C FDR Bölüm 1+3 · D FDR Bölüm 2/4/5/6/7 · E REVIEW_LOG tarihçesi · F model/veri/eğitim · G İKA/sim/saha/Pixhawk · H şartname PDF'leri ·
I süreç/ajanlar/TASK_QUEUE. Bir dosyada derinleşmek istersen önce ilgili özete, sonra depodaki asıl dosyaya bak. Bir sayıya güvenmeden önce
**depodaki asıl dosyayı** aç; özetler "DOĞRULANAMADI" yazdığı yerde tahmin etme.

## 7. Bu klasör nasıl üretildi (şeffaflık)
9–10 Eylül 2026, Jetson'daki Claude oturumu: tam depo klonlandı (`~/proje/navitas_tam/navitas`, 606 commit, 4 dal); dokuz paralel inceleme ajanı her alanı
kaynak dosyalardan okuyup `ozet/` dosyalarını yazdı; ana oturum anayasa, sözleşmeler, mimari plan, araştırma notları, FDR özeti/yönerge haritası,
şartname boşluk raporu ve kanıt paketini kendisi okudu; 18 öğretici dosya bunlardan yazıldı. Yazarın kendi Jetson oturumları (6 ve 9 Eylül) 10 numaralı
dosyanın birincil kaynağıdır. Uydurma sayı yoktur; emin olunamayan yerler "DOĞRULANAMADI" ya da "ÖLÇÜLEMEDİ" ile işaretlidir. Halil'in isteğiyle hazırlandı.
