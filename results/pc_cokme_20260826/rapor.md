# PC ÇÖKMESİ — 2026-08-26 11:20:45 · ön inceleme (yönetici yetkisi olmadan)

## 1. Olay zinciri (Windows olay günlüğü, ölçüldü)
| saat | olay |
|---|---|
| 11:10:24 | Temiz yeniden başlatma (Kernel API — kullanıcı/Windows Update) |
| 11:12:03 | **İkinci** temiz yeniden başlatma (21 sn sonra) |
| 11:12:55 | **Intel Dynamic Tuning (DTT/DptfPolicy) kullanıcı-modu sürücüsü çöktü** (10111/10120, c0000005) — ısı/güç ayar bileşeni çevrimdışı |
| 11:15:44 → 11:25 | **`llama-server.exe` çökme döngüsü** (BEX64, `ucrtbase.dll`, c0000409 = stack buffer overrun / fail-fast), her ~90 sn; yeniden başlatmadan sonra da sürüyor. Başlatan: **LM Studio `--run-as-service`** (Win32_StartupCommand). |
| ~11:05–11:20 | Aynı anda bu oturumun GPU işleri: `65_kabul_denetcisi` (K6 ajanı, 3 model) + sızıntı ölçümü (3 model × 111 kare) — **iki ayrı YOLO süreci** |
| **11:20:45** | **BSOD 0x0000003B** (SYSTEM_SERVICE_EXCEPTION, c0000005, adres fffff802bdba22a0) → `C:\WINDOWS\Minidumps\082626-19828-01.dmp` |
| 11:21:30 | Yeniden açılış (Kernel-Power 41) |

## 2. Örüntü — tek olay DEĞİL: 5 haftada 8 mavi ekran
```
26.08 0x3B c0000005   20.08 0x3B c0000005   14.08 0x1E c0000005
03.08 0x10E 2d        31.07 0x10E 17        24.07 0x3B c0000005
21.07 0x10E 17 (+WHEA 1)                    20.07 0xC2 99 (BAD_POOL_CALLER)
```
**0x10E = VIDEO_MEMORY_MANAGEMENT_INTERNAL** (3 kez) doğrudan GPU sürücüsü / VRAM yöneticisidir;
0x3B ve 0x1E (c0000005) de en sık sürücü kaynaklıdır. Ekran kartı: RTX 5080 Laptop,
NVIDIA sürücü **32.0.16.1088 (22.07.2026)** — 0x10E'lerin ikisi bu sürücüden **sonra**.
Donanım hatası (WHEA) yalnız 21.07'de 1 kayıt. Şu an: GPU 48 °C, 0 MiB kullanımda, 100 GB RAM (83 GB boş).

## 3. En olası neden (kanıt ağırlığıyla)
1. **GPU sürücüsü / VRAM baskısı** — 16 GB VRAM'e aynı anda: (a) LM Studio'nun servis olarak
   yüklemeye çalışıp çöktüğü yerel LLM, (b) iki YOLO süreci. 0x10E tarihçesi bu yönü gösteriyor.
   ⚠ `CLAUDE.md` madde 11: *"yerel iki model asla aynı anda yüklenmez"* — LM Studio servisi bu
   kuralı **otomatik** ihlal ediyor (kullanıcı elle başlatmıyor, açılışta kendisi kalkıyor).
2. **Intel DTT sürücüsü** kararsız (çöken bileşen güç/ısı politikasını yönetiyor).
3. Gece 01:00–05:30 arasında aynı GPU yüküyle (eğitim 5 GB + çıkarım) **hiç çökme olmadı**;
   çökme, 11:10–11:12 çift yeniden başlatma + DTT çökmesi + llama-server döngüsünden **sonra** geldi.

## 4. Kesin teşhis için gereken (yönetici yetkisi — kullanıcı)
Minidump ve WER klasörleri yönetici olmadan okunamıyor. **Yönetici PowerShell'de** şunu koş, sonra bana söyle:
```powershell
New-Item -ItemType Directory -Force O:\navitas\results\pc_cokme_20260826\dump | Out-Null
Copy-Item C:\WINDOWS\Minidumps\*.dmp O:\navitas\results\pc_cokme_20260826\dump\
Get-ChildItem C:\ProgramData\Microsoft\Windows\WER\ReportQueue -Directory | ? Name -match '^Kernel_' | % { Copy-Item $_.FullName O:\navitas\results\pc_cokme_20260826\dump\ -Recurse -Force }
```
Dökümlerden suçlu modülü (nvlddmkm / dxgmms2 / DTT) çıkarırım.

## 5. Hemen alınabilecek önlemler (öneri)
- **LM Studio → Ayarlar → "Run LLM server on login / as service" KAPAT** (llama-server döngüsü ve VRAM çakışması biter).
- NVIDIA sürücüsünü **Studio** dalına ya da bir önceki kararlı sürüme al; 0x10E tekrarı sürerse
  DDU ile temiz kurulum.
- Intel DTT (Dynamic Tuning) sürücüsünü ASUS/Intel'den güncelle ya da MyASUS'ta devre dışı bırak.
- Bu oturumda **GPU işleri artık sıralı** koşulacak (aynı anda tek YOLO süreci); iş akışlarında
  paralel GPU ajanı yok.
