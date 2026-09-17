# NAVITAS — LOG ENVANTERİ VE LOG SİSTEMİ GEREKSİNİM ANALİZİ

> Derleme tarihi: 2026-09-17. Kapsam: repoda şu ana kadar tutulan tüm log/kanıt
> kayıtları (tarih aralıklarıyla) + bunlardan çıkan drone (uçuş) ve yazılım log
> sistemi gereksinimleri. Kaynak: repo taraması (`Glob`/`Grep`/dosya okuma),
> tarihler dosya adı damgası veya belge içi kayıttan alındı.

---

## 1. Log envanteri (tarih sırasıyla)

| # | Log türü | Konum | Tarih aralığı | Hacim | İçerik / üretim yolu |
|---|---|---|---|---|---|
| 1 | Donanım/LLM ölçüm günlüğü | `LOCAL_LLM.md` | 2026-08-04 → 2026-08-07 | çok bölümlü belge | Yerel LLM donanım, RAM, `mmap`, context bütçesi, commit limiti ölçüm koşumları |
| 2 | Denetim kaydı (K-serisi) | `REVIEW_LOG.md` §1 | 2026-08-03 | 11 madde (K-01…K-11) | Çekişmeli denetim, kanıt zorunlu (komut + gerçek çıktı) |
| 3 | Denetim kaydı (D-serisi) | `REVIEW_LOG.md` (~31.700 satır) | 2026-08-04 → 2026-09-17 (son: D-492) | 497 madde | Anayasa madde 6 gereği kanıtlı kusur/mantık riski kaydı |
| 4 | Eğitim konsol logu | `results/t121/ft_kosum_log.txt` | 2026-08-20 | 1 dosya, 4,1 MB | YOLO (`t121_etiket_ft`) eğitim konsol çıktısı |
| 5 | Gece etiketleme/tarama oturumları | `results/gece_20260826`, `gece_20260828`, `gece_20260907` | 2026-08-26, 2026-08-28, 2026-09-07 | 3 oturum, çok dosyalı | Gece verisi etiketleme + tarama kanıtı (`rapor.json`, kare bazlı `_ops.json`) |
| 6 | Mutasyon/denetim raporları | `results/codex_denetim/d280`, `d282` | 2026-08-30, 2026-09-01 | 2 klasör | Bağımsız mutasyon testi kanıtı (`rapor.json`) |
| 7 | Hakem/prova JSONL kaydı | `results/prova/<YYYYMMDD_HHMMSS>_<pid>/hakem_log.jsonl` | 2026-09-03 → 2026-09-15 | 34 oturum | `comms/hakem_kaydi.py` ile üretilen, thread-safe + `fsync`'li saha kanıtı |
| 8 | FDR sprint saha koşumu | `results/fdr_sprint_20260910/H9_MK15/t226/*hakem_log.jsonl` | 2026-09-10 | 2 dosya | Saha sprint koşum kanıtı |
| 9 | Uçuş dataflash logu (Pixhawk, `.bin`) | `results/ucus_20260912…20260917b/` | 2026-09-12 → 2026-09-17 | 27 dosya | ArduCopter 4.5.7 ham uçuş kaydı |
| 9b | Uçuş dataflash logu — RTC senkronsuz (tarihsiz) | `results/ucus_zaman_senkronsuz/` | belirsiz (FC saati 1980'e dönmüş) | 4 dosya, 10,5 MB | 17 Eylül'de Mission Planner önbelleğinden (`OneDrive\Belgeler\Mission Planner\logs\QUADROTOR\1\`) hash ile doğrulanarak çıkarılan, hiçbir yerde arşivi olmayan 4 tekil log |
| 10 | Uçuş telemetri logu (MAVLink, `.tlog`) | `results/ucus_20260917/` | 2026-09-17 | 4 dosya | Mission Planner telemetri akışı |
| 11 | Düşüş adli analiz raporu | `results/ucus_20260917/DUSUS_ANALIZI.md`, `ucus_20260917b/DUSUS_ANALIZI.md` | 2026-09-17 | 2 belge | Ham log kanıtından üretilen olay analizi; `REVIEW_LOG.md` D-490/491/492 ile eşleşir |
| 12 | Olay sonrası muayene prosedürü | `SAHA_OLAY_SONRASI_MUAYENE.md` | oluşturuldu 2026-09-07 (D-429 sonrası) | 1 belge | Madde 0 fiziksel sökümden ÖNCE dataflash log indirmeyi zorunlu kılıyor |
| 13 | Oturum devir kayıtları | `HANDOFF.md`, `HANDOFF_20260913.md` | 2026-09-13, 2026-09-14 | 2 dosya | Kota/oturum bitişinde devir protokolü kaydı |
| 14 | Görev kuyruğu durum kaydı | `TASK_QUEUE.md` | sürekli güncellenen | 9.757 satır | `[IN_PROGRESS]/[READY_FOR_REVIEW]/[HUMAN_COMPLETED]` durum geçmişi |

---

## 2. Drone (uçuş) log sistemi — gereksinim analizi

- **Format:** Pixhawk 6C dataflash (`.bin`, ArduCopter 4.5.7) + Mission Planner MAVLink telemetri (`.tlog`). Tek doğrulanabilir uçuş kanıtı bu ikisi; `DUSUS_ANALIZI.md` raporları tamamen bunlara dayanıyor.
- **Zaman senkronu kırılgan:** `results/ucus_20260917/1980-01-09 23-09-53.bin` dosya adı, Mission Planner'ın GPS zamanı olmadan açtığı varsayılan tarih — olay saati dosya adından değil, log içi GPS zaman damgasından geri çıkarılmak zorunda kalınmış (`DUSUS_ANALIZI.md`). Gereksinim: uçuş öncesi GPS/RTC senkronu doğrulanmalı, aksi halde adli analiz log içeriğine muhtaç kalıyor.
- **`.tlog` kapsamı dar:** repoda yalnız 4 `.tlog`, hepsi 17 Eylül'e ait; 12-15 Eylül uçuşlarında yalnız `.bin` var. D-492'nin dayandığı kritik `2026-09-17 02-31-36.tlog` (son paket 202,18 s) repoda değil, "OneDrive MP logs" olarak dış kaynaktan alınmış — tek kopya repo dışında.
- **FC'nin "82 log" listesi büyük ölçüde yanıltıcı (17 Eylül, hash ile doğrulandı):** Mission Planner'ın "Kayıtları İndir" penceresi FC üzerinde 82 kayıt gösteriyor; yerel önbellekte (`OneDrive\Belgeler\Mission Planner\logs\QUADROTOR\1\`) 41 `.bin` var. Bunları içerik (`md5`) bazında repodaki 27 dosyayla karşılaştırdığımda **10 tanesi zaten repoda, sadece farklı isim/tarih damgası altında** çıktı (Mission Planner aynı fiziksel logu farklı oturumlarda farklı görünen zaman damgasıyla kaydediyor — ör. yerel `58 13.09.2026 08-57-10.bin` ile repodaki `2026-09-13 08-34-30.bin` bayt-bayt aynı). Gerçekten arşivsiz olan içerik sadece **4 tekil dosya** (`results/ucus_zaman_senkronsuz/`) — hepsi RTC senkronsuz. Sadece dosya adına bakarak "eksik" saymak (ilk taramamdaki hata) yanlış sonuç veriyordu; kanıt her zaman içerik hash'i olmalı.
- **Canlı indirmede kalıcı boşluk:** aynı oturumda "8.09.2026 12:35:18" damgalı kayıt `GetLog` zaman aşımıyla hiç inmedi; önbellekte de (41 dosyanın hiçbirinde) hiçbir kopyası yok — bu içerik şu an hiçbir yerde mevcut değil, yalnız FC'den tekrar canlı çekilerek kurtarılabilir.
- **Olay sonrası prosedür yeni ve geriye dönük:** `SAHA_OLAY_SONRASI_MUAYENE.md`, D-429'a göre 6 Eylül'e kadar hiç yoktu ("grep: … → 0 satır"). Madde 0 artık fiziksel müdahaleden önce dataflash log indirmeyi zorunlu kılıyor; bu disiplin şu ana kadar yalnız 17 Eylül olayında (D-490/491/492) uygulanmış durumda.
- **Analiz iş akışı standartlaşıyor:** D-491, log analizini "3 mercek (itki/mekanik, temas/pilot, sensör/elektrik) → sentez → 3 çürütücü" kalıbına bağladı (Workflow `dusus-log-analizi-0250`) — gereksinim, her düşüşte bu kalıbın tekrarlanması.

## 3. Yazılım log sistemi — gereksinim analizi

- **İki ayrı kanal:** (1) `REVIEW_LOG.md` — insan/AI'ın elle yazdığı, kanıt (komut + gerçek çıktı) zorunlu denetim kaydı (Anayasa madde 6); (2) `hakem_log.jsonl` — `comms/hakem_kaydi.py` ile programatik üretilen, thread-safe + `flush`+`fsync` korumalı JSONL saha kaydı.
- **`hakem_log.jsonl` şeması:** `v` (kayıt sürümü=1), `ts` (ISO 8601, tz'li), `monotonic_s`, `oturum` (UUID, çoklu oturum ayrımı), `olay` + serbest alanlar. Kural: `UI_OLAYI` — ekranda görünen HER satır kayda da düşmek zorunda (ekran/kayıt ayrışmasını önlemek için).
- **Ayrı bir önem-seviyesi kanalı var:** `CONTRACTS.md`, `comms/seri_hub.py` için "KIRMIZI log" seviyesini tanımlıyor (öğrenilen tüketici düşürme, seri arıza, fan-out hatası). Bu seviyenin `hakem_log.jsonl` ile aynı dosyaya mı yazıldığı yoksa ayrı bir hedefe mi gittiği `CONTRACTS.md`'de belirtilmemiş — doğrulanmadı.
- **Hacim:** 34 prova oturumu 12 günde (03-15 Eylül) üretildi; sıklık artışı FDR sprint ve saha koşum takvimiyle örtüşüyor.

## 4. Saptanan boşluklar

1. `.tlog` arşivi sistematik değil — yalnız kriz sonrası (17 Eylül) toplanmış, rutin uçuşlarda yok.
2. Kritik bir `.tlog` (D-492 kanıtı) repo dışında (OneDrive), tek kopya riski.
3. GPS/RTC zaman senkronu uçuş öncesi doğrulanmıyor — FC saati tekrarlayan biçimde 1980'e dönüyor; bu durum tek seferlik değil, en az 2 ayrı boot oturumunda (4 dosya) tekrarlanmış.
4. "KIRMIZI log" hedefi (dosya/konsol/uzak) `CONTRACTS.md`'de tanımsız.
5. `REVIEW_LOG.md` tek dosyada ~31.700 satır — fiilen yalnız `grep` ile gezilebilir durumda.
6. Mission Planner'ın log listesi tek başına güvenilir envanter kaynağı değil — aynı log farklı oturumlarda farklı ad/tarihle görünüyor; arşiv eksiği/fazlası yalnız içerik hash'i ile doğru ölçülebilir (bu belge madde 2'de düzeltildi).
7. FC'de canlı `GetLog` ile inmeyen en az 1 kayıt (8.09.2026 12:35:18) hiçbir yerde arşivlenmemiş; kurtarma yalnız FC'ye yeniden bağlanıp canlı çekmekle mümkün.
