# 08 — Sahada uçuş öncesi kontrol listesi

Yazdırıp işaretleyin. Her madde bugünkü bir ölçüme ya da olaya dayanır; köşeli parantezde kaynak var.

## A. Mekanik (pervaneler takılmadan ve takıldıktan sonra)

- [ ] Dört pervane somunu elle sıkı. Adaptör halkasında kayma izi yok. [D-491, D-506: iki düşüş iki köşede]
- [ ] Pervanelerde çatlak yok. Motorlar elle serbest dönüyor. ESC kablolarında yanık ya da koku yok.
- [ ] GPS1 kablosu iki ucundan oturmuş ve gerilimsiz sabitlenmiş. [D-515]
- [ ] Jetson güç fişi sallanınca oynamıyor. Pil **4S** ve dolu. 3S pille Jetson uçmaz. [D-512]
- [ ] Kamera montajı sabit, lens temiz. Montaj açısı biliniyor (C bölümü).

## B. Yer istasyonu (PC)

- [ ] Yer telsizi USB'de. Aygıt Yöneticisi'nde COM7 görünüyor.
- [ ] Mission Planner COM7'ye **bağlı değil**.
- [ ] Bu dalın kökünde `SAHA_YKI_BASLAT.cmd`. İki pencere açıldı: yönlendirici ve YKİ. [02]
- [ ] MP'de UDP, port 14550, Connect.
- [ ] Yönlendirici penceresinde `seri->udp` 2–3 kB/s akıyor, `seri_hata` artmıyor.

## C. Açılış kontrolleri

- [ ] MP Mesajlar'da son açılışta **"MAG0 initial yaw alignment complete"** var. "MAG2" ya da "switching to compass 2" varsa GPS1 kablosunu oturt ve yeniden başlat. [D-515]
- [ ] Kumanda açık. Mesajlar'da "RC Protocol: IBUS" var. [D-510]
- [ ] PreArm temiz. Dışarıda GPS fix var.
- [ ] YKİ'de İHA satırı yeşil "TAZE", Pixhawk ✓.
- [ ] YKİ'de konum makul: "3B FIX ✓" ya da koordinatla birlikte "fix BİLİNMİYOR". "konum BİLİNMİYOR" görünüyorsa GPS'i bekle.
- [ ] Kamera montaj açısı (ok testi) ölçüldü. Görev dosyası `--montaj-yaw` ile üretildi ya da pilot burun kuralını biliyor. [05]

## D. Jetson (ethernet takılıyken; uçuştan önce ethernet ÇIKARILIR)

- [ ] İlk gün bir kez: `jetson_manifest.py` ve telemetri kapısı kurulumu (`uygula.py`). Çıktıda Traceback yok. [03]
- [ ] Servisler aktif. `rpi_inference` günlüğünde kamera açık, Traceback yok.
- [ ] Kara kutu çalışıyor: `~/kara_kutu/` altında bugünün CSV'si büyüyor.

## E. Pervanesiz hakem provası (5 dk)

- [ ] YKİ'ye İHA'dan karar geliyor (ROTA YOK ya da rota).
- [ ] Rota gelince "1) TESPİTİ DOĞRULA" ve ardından "2) YKS'DE GÖRÜLDÜ — ONAYLA". ACK gidiyor.
- [ ] **Onay kalıcı:** 2. adımdan sonra 30–60 s bekle. Düğme "ONAYLANDI ✓✓" kalmalı, günlükte yeni seq'lere "ACK ref=… gönderildi" görünmeli. [02 §Açık test]
- [ ] YKİ haritasında rota **aşağıdan yukarı** akıyor. Kamera yönü doğru. [05]

## F. Uçuşta

- Yazılımla uçuş (GUIDED/AUTO) **yalnız Jetson açıkken**. Yalnız MP bağlıyken 5 s kopma LAND'a düşürür. [D-505 ek 2]
- YKİ'de **sarı "bağlantı ZAYIF"** (3–5 s) kısa sürerse normal. **Kırmızı** (> 5 s) görülürse önce yönlendirici penceresine bak. [01]
- "switching to compass 2" = harici pusula koptu. İniş düşün.
- YKİ'de "kimlik SICRAMASI" = Jetson yeniden başladı. 1–2 dk rota gelmez.
- "ONAY ASKIDA — ACK YOK" = arada "rota yok" karesi geldi. 5 s içinde kendiliğinden döner, basma.

## G. Sonra (kanıt topla)

- [ ] Pixhawk .bin ve MP tlog → `results/ucus_20260921/`.
- [ ] YKİ `results/prova/<zaman>/hakem_log.jsonl` ve yönlendirici penceresinin son satırları.
- [ ] Jetson `~/kara_kutu/*.csv` ve `journalctl -u navitas-rpi-inference` çıktısı.
