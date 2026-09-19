# 01 — Telsiz zinciri, ölçümler ve K8

Kanıtlar: `results/telsiz_20260919/` (özet tablo `SONUC.md`), defter D-508, D-509 (+ekler), D-511, D-513, D-514.

## Zincir (tek RFD900A çifti, 16 Eyl kararı)

```
Jetson içi:  rpi_inference ──► seri_hub (127.0.0.1:5100) ──► MAVProxy --out udp:127.0.0.1:14553
             MAVLink2 TUNNEL (id 385, payload_type 0xCE56, parça 128 B = 123 B yük)
Havada:      Jetson ──TELEM2 (kablo)──► Pixhawk 6C ──TELEM1──► RFD900A (hava)
Yerde:       RFD900A (yer, USB = COM7, 57600) ──► scripts/yer_yonlendirici.py
                 ├─► Mission Planner: UDP 14550  (MP'de "UDP" seç, port 14550, Connect)
                 └─► YKİ: --tunel 127.0.0.1:14590
```

- COM7'nin **tek sahibi yönlendiricidir**. MP'yi COM7'ye doğrudan bağlamaya çalışmak "Bağlantı başarısız" verir, bu beklenen davranış.
- Ethernet yalnız kurulum ve SSH içindir. Uçuşta telsiz dışında yol yok; D-513 kanıtı bu düzende alındı.

## Bugün ne kanıtlandı

| Test | Sonuç | Kanıt |
|---|---|---|
| Telsiz iki yönlü (Halil'in isteği) | Jetson'dan işaretli çerçeve YKİ'ye, YKİ'nin ACK'i Jetson'a: **gidiş-dönüş 474 ms** | D-513, `betikler/telsiz_kanit.py` |
| GPS koordinatı telsizle | lat 40.9595434, lon 29.1337843, 22 uydu, fix 4 YKİ'de | D-511, `prova2_hakem_log.jsonl` |
| USB çek-tak (Test 3) | "SERI YENIDEN BAGLANDI COM7 (kopukluk 8.0 s)", hiçbir program yeniden açılmadı | D-514, `prova5_yonlendirici.log` |
| Gerçek boyda rota (Test 4) | 414 B / 4 parça, **ilk gönderimde 0,40 s**; hakem 2. adım → ACK Jetson'da **0,22 s** | D-514, `betikler/rota_testi.py` |
| GCS failsafe, Jetson açık | PC heartbeat'i 25 s kesildi → "GCS Failsafe" **yok** (MAVProxy sysid 255 heartbeat'i sayılıyor) | D-508 ölçüm 4 |

GCS failsafe: Jetson ya da MAVProxy ölürse `FS_GCS_ENABLE 5` devreye girer ve araç LAND'a geçer. İstenen davranış budur.
Jetson kapalıyken MP telsizden 5 s koparsa da LAND'a geçer. 12:59 logunda GUIDED'da bu yaşandı (D-505 ek 2).

## K8 — hız kapısı (p95 gidiş-dönüş < 200 ms)

| Ölçüm | Düzen | p50 | p95 | kayıp | Hüküm |
|---|---|---|---|---|---|
| K8a | tünel, hub durduruldu | 168,6 ms | **212,4 ms** | %3 | DÜŞTÜ |
| K8b | üretim yolu, tüm servisler açık | 205 ms | **278 ms** | %13 | DÜŞTÜ |
| dün K8a / K8b | MAX_WINDOW 131 | 184 / 249 | 268 / 360 | | |
| param yolu | Jetson YOK, yalnız telsiz+Pixhawk | 128,5 | **204,9** | 1/120 | tek başına > 200 |

- **Ne değişti:** telsizlerde `MAX_WINDOW` yerde 33, havada 131 bulundu, yani eşleşmiyordu. İkisi 33 yapıldı ve yeniden başlatıldı. p95 %21–23 düştü. Ayar **33/33'te kaldı**.
- **Neden kapanmıyor:** Jetson hiç yokken de p95 205 ms. Darboğaz telsiz ve TELEM1 turu (TDM), Jetson değil.
  Dağılım basamaklı (77 / 128 / 205 / 231 ms); bu, telsiz zaman diliminin imzası.
- **Üretimde neden daha kötü (278):** Jetson'ın karar trafiği telsizi dolduruyor. Her karede ACK'siz NO_ROUTE ×4 tekrar gidiyor.
  Uçuş sonrası iş: aynı kararı yalnız değişince ya da 1 Hz'de göndermek. Bu değişiklik kod ister.
- **Gürültü:** n=120'de p95 ±12 ms oynuyor. "12 ms kala geçti sayılır" okuması yapılmaz.
- **Eşik gevşetilmedi.** Pratikte komut ve onay tekrarla güvenilir gidiyor, rota gecikmeli gelebilir.
- SR1 akış denemesi geçersiz. ArduPilot 4.5, SRn değişikliğini canlı akışa uygulamıyor (D-509 ek 3).
- `RADIO_STATUS` akmıyor, bu yüzden RSSI ve TxBuf ölçülemiyor. Kök neden açık.

## MAX_WINDOW yeniden yazılacaksa (DİKKAT)

Halil'in `scripts/tezgah/sik_ayar.py` betiği uzak telsize yazdıktan sonra geri okumadan yeniden başlatıyor (D-507).
Yazım tutmazsa telsizler eşleşmez; uzak telsiz araçta olduğu için düzeltme fiziksel.
Doğru sıra: yaz (yeniden başlatma yok) → iki tarafı `RTI5`/`ATI5` ile oku, ikisi de 33 → ancak sonra `RTZ` + `ATZ`.
Bu sırayı uygulayan betik `results/telsiz_20260919/betikler/mw_uzak_yaz_dogrula.py`.
RT okuması aralıklı gelir: boş döküm "fark yok" demek değildir, 8 s bekleyip tekrarla.

## Video

- Telsiz birkaç kB/s taşıyor. Tek kare ~28 kB. **Telsizden video geçmez.**
- Yerde ethernet ve SSH ile video ölçüldü: 10,2 fps, 2,28 Mbit/s (`betikler/ssh_yonlendir.py`). Bu yalnız yer doğrulamasıdır.
- Uçuşta video için ayrı bir görüntü bağlantısı gerekir. Kullanıcı kararı: şimdilik yalnız telsiz.

## Arıza okuma kuralı (bugün öğrenildi)

YKİ "BAĞLANTI KAYBI" gösterirse **önce yönlendirici penceresine bak**:

- `seri->udp 0 B/s` ya da `seri_hata` artıyorsa sorun yer telsizi ya da USB'dedir. Yeni kod portu kendisi yeniden açar; kabloyu kontrol et.
- `seri->udp` 2–3 kB/s akıyor ama YKİ kayıp diyorsa sorun Jetson tarafındadır (servis, güç).

18:40'ta bu sıra atlandığı için yanlış teşhis konuldu: "Jetson heartbeat'i durdu" denildi, gerçekte USB kopmuştu (D-513 ek). Yaklaşık 30 dakika kaybedildi.

## Betikler (`results/telsiz_20260919/betikler/`)

| Betik | İş |
|---|---|
| `jetson_ssh.py` | Jetson'da komut (parola `NAVITAS_SIFRE` ortam değişkeninden) |
| `ssh_yonlendir.py` | SSH port yönlendirme (kamera köprüsü 8080 → PC 18080) |
| `telsiz_kanit.py` | işaretli tek çerçeve + ACK yakalama (iki yönlü kanıt) |
| `rota_testi.py` | gerçek boyda rota + hakem ACK testi (üretim rpi_inference'ı STOP/CONT ile duraklatır) |
| `k8b_yanki.py` | K8b yankı ucu |
| `mw_uzak_yaz_dogrula.py` | MAX_WINDOW güvenli yazım |
| `sr1_ab.py`, `pixhawk_ayar_20260919.py` | Pixhawk parametre deneyleri ve onaylı yazım |
| `prova_baslat.py` | COM7'yi bekler, yönlendirici + YKİ açar (prova günlükleri) |
| `panel_kaydet.ps1` | YKİ ekran görüntüsü |
