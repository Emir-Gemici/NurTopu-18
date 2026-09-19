# 02 — YKİ (hakem ekranı) ve iki adımlı hakem onayı

Kanıtlar: defter D-514, D-516 (+ek 1–4). Kod: `comms/yks_gui.py` ve `scripts/yer_yonlendirici.py` (bu dal).

## Açılış (saha düzeni, ethernetsiz)

1. Mission Planner açıksa COM7'den **ayır**. COM7'yi yönlendirici alacak.
2. Bu dalın kökünde `SAHA_YKI_BASLAT.cmd` çift tık. İsterseniz port verin: `SAHA_YKI_BASLAT.cmd COM7`.
   İki pencere açılır: "NAVITAS yer yonlendiricisi (KAPATMA)" ve "NAVITAS YKI".
3. MP'de bağlantı türünü **UDP**, portu **14550** seçip Connect'e basın.
4. YKİ'de İHA satırı yeşil olmalı ("TAZE").

Elle açmak için komut:

```
cd /d O:\navitas\.claude\worktrees\bilgilendirme-he
O:\navitas-local-train\venv\Scripts\python.exe -u -B scripts\yer_yonlendirici.py --port COM7 --baud 57600 --tunel 127.0.0.1:14590
O:\navitas-local-train\venv\Scripts\python.exe -B comms\yks_gui.py --tunel 127.0.0.1:14590 --fda
```

- ⚠ **Bu akşam 20:15'ten önce açılmış YKİ penceresi eski kodu taşır.** Kapatıp yeniden açın.
- ⚠ `origin/master` üzerindeki `yks_gui`'de `--tunel` seçeneği **yok**. Tünel için YKİ bu daldan (ya da `tunel-saha-20260918`'den) açılmalı.
- ⚠ **.exe paketi bayat.** `dist/YKS_20260919.zip` 19 Eyl 11:52'de paketlendi. Bu akşamki onay düzeltmelerini ve yönlendiriciyi içermez.
  İçindeki OKUBENI eski "MP aynası" düzenini anlatır. Arkadaş paketi kullanacaksa paket bu daldan yeniden üretilmeli:
  dal kökünde `tools\yki_paket\paketle.bat` çalıştırılır. Yönlendirici pakette yok, ayrıca Python ile çalıştırılmalı.
  Bu iş YAPILMADI.
- Başka bir PC'de `SAHA_YKI_BASLAT.cmd` içindeki `PY=` satırı o PC'nin Python yoluna çevrilir.
- Hakem kanıt günlüğü şuraya yazılır: `results/prova/<tarih_saat_pid>/hakem_log.jsonl`.

## İki adımlı onay (FDA §5.3.2)

1. İHA rotayı gönderir. YKİ rotayı haritada çizer, düğme **"1) TESPİTİ DOĞRULA"** olur.
2. Hakem 1. adıma basar. Düğme **"2) YKS'DE GÖRÜLDÜ — ONAYLA → ACK (FDA)"** olur.
3. Hakem 2. adıma basar. **ACK yalnız bu anda Jetson'a gider** (Test 4'te 0,22 s).
   İki adım arasında İHA rotayı saniyede bir yeniden gönderir.

YKİ'nin bilerek reddettiği durumlar. Bunlar hata değil, güvenlik kapısıdır:

| Ekranda | Anlamı |
|---|---|
| `GEOMETRİ YOK` / `ANKOR YOK` | rotanın ilk noktası [0,0] değil |
| `BAYAT TESPİT — ONAY KAPALI` | İHA kararının yaşı > 5 s (`YKS_TESPIT_TAZELIK_S`) |
| `ROTA YOK — ACK OTOMATİK GÖNDERİLDİ` | İHA "rota yok" dedi. Güvenlik bildirimi, otomatik ACK'lenir |
| `SERIT DEGISTI — yeni onay gerekir` | İHA başka şerit seçti, onay baştan |
| `ONAY ASKIDA — ACK YOK` | arada "rota yok" ya da düşük güven karesi geldi. 5 s içinde aynı şerit dönerse onay geri gelir |

## Bu akşam bulunan ve düzeltilen hata (D-516) 🔴

- **Hata.** Jetson her kararda yeni bir sıra numarası (seq) üretir, aynı şerit için yaklaşık saniyede bir.
  Eski YKİ her yeni seq'te iki onay adımını da sıfırlıyordu. Sonuç: hakemin 1. adımı ~1 s'de siliniyordu.
  2. adıma pratikte ulaşılamıyordu. Tamamlanmış onay bir sonraki karede geri alınıyordu.
  Şartnamede hakem onayı zorunlu olduğu için bu **0 puan riskiydi**.
- **Neden Test 4 görmedi.** Test betiği hep aynı seq'i tekrarlıyordu. Bu bir test tasarımı açığıydı.
  Hata headless (ekransız) yeniden üretilerek kanıtlandı.

Düzeltmeler (hepsi bu dalda, mimar tarafından testler koşularak ve mutasyonla denetlendi):

| Commit | Ne yapar |
|---|---|
| `a2e69b9b` | Aynı şerit + yeni seq geldiğinde onay korunur. Tamamlanmış onayda yeni seq'e ACK gider; aynı seq'e ikinci ACK gitmez. Şerit değişirse sıfırlanır. Yarışma kipi (FDA dışı) değişmedi. |
| `db692109` | Tek "rota yok" / düşük güven karesi onayı silmez, **askıya alır**. 5 s içinde aynı şerit dönerse onay geri gelir, dönmezse düşer. |
| `21ae2f5f` + `eb6a0c20` | Saçma telemetri gizlenir: 0/0 konum ya da fix < 3 → "konum BİLİNMİYOR". Fix alanı hiç gelmediyse koordinat gösterilir ama "fix BİLİNMİYOR" işaretlenir. İrtifa (−50, 200] dışıysa 30 m satırı "GEÇERSİZ". |
| `6bea6808` | İHA satırı: heartbeat 3–5 s gecikirse **SARI "bağlantı ZAYIF"**, 5 s'yi geçerse **KIRMIZI "BAĞLANTI KAYBI"**. ARM kapısı (2,5 s) değişmedi. |
| `185c2f97` | Yönlendirici: USB çıkıp takılınca port kendiliğinden yeniden açılır (canlı 8 s). |

⚠ Eski belgeler "kırmızı ≤ 4 s" diyor: `SAHA_YOL_HARITASI_20260916.md:892`, `ATOLYE_TEST_GUNU_20260912.md:101-103`. Artık 3 s'de sarı başlıyor, belgeler güncellenmedi.

## AÇIK: canlı telsiz onay testi (yarın, Jetson açıkken) — YAPILMADI

Düzeltmeler yalnız bilgisayarda test edildi, telsizle canlı denenmedi. Yarın uçuştan önce şu test yapılmalı:

- Jetson'da test betiği her saniye **yeni seq**'li aynı şerit rotası ve arada bir NO_ROUTE göndersin. Üretim böyle davranıyor.
  Mevcut `rota_testi.py` hep aynı seq'i yolluyor. Yeni seq'li sürüm **henüz yazılmadı**.
- Hakem iki adıma **birer kez** basıp bıraksın.
- **Geçme ölçütü:** ilk ACK'ten sonra her 10 s'lik pencerede en az bir yeni seq ACK'i gelmeli. Her NO_ROUTE'tan sonra 10 s içinde yeniden OPEN_ROUTE ACK'i gelmeli.
  Hiçbir ACK, gönderilmemiş bir seq'e ait olmamalı.
- Onay sıfırlanırsa ACK'ler durur ve test düşer. Bu durumda uçuşta hakemin her karede yeniden basması gerekir.

## İkinci operatör notu

Bugün 10.21.8.180'den Jetson'a ikinci bir SSH oturumu açıktı (Halil tarafı). İki ajan aynı anda
servis durdurursa ölçümler karışır. Kim ne yapıyor, önce konuşun.
