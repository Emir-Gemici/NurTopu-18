# SAHA KARTI — 19 Eylül 2026 (tünel düzeni, D-494)

**Sürüm:** PC YKİ = worktree `tunel-saha-20260918` (aef6ccb8 ya da üstü) · Jetson = e33b592a paketi (`~/navitas`) · yedek: `~/yedek_arkadas_ikili_20260918.tar.gz` + `~/GERI_DON_ARKADAS_IKILI.txt`
**Roller (isim yazın):** Pilot ____ · MP operatörü (parametre yazan TEK kişi) ____ · YKİ operatörü ____ · Jetson sorumlusu ____ · Pilot ≠ YKİ operatörü.

## 1. Malzeme
4S 13 Ah pil ×__ (uçuşa çıkış ≥ 16,6 V multimetre) · iMAX B6 + 12 V kaynak · multimetre · **Ethernet kablosu** (Jetson ↔ laptop, sahada şart) · RFD900A yer modülü + USB + 2 anten · Pixhawk USB kablosu (.bin) · yedek 1045 CW/CCW + somun anahtarı · FS-i6 + piller · laptop + şarj · ip/kayış (ilk askı) · aydınlatma.

## 2. Açılış sırası (her seferinde aynı)
1. Pil tak → Jetson açılır (1–2 dk). Ethernet takılıysa: `ssh n4vitas@fe80::991b:7948:5cff:884f%8` (parola ekipte).
2. RFD yer modülünü USB'ye tak (COM7). **Mission Planner COM7'ye BAĞLANMAZ.**
3. PC'de **`SAHA_YKI_BASLAT.cmd`** çalıştır → iki pencere: yönlendirici (COM7'nin tek sahibi) + YKİ (`--tunel 127.0.0.1:14590 --fda`). Eski kısayollar (`saha_baslat.py`, `--ika/--iha`) **kullanılmaz**.
4. Mission Planner: bağlantı türü **UDP**, port **14550**, Connect. HUD hareket etmeli. MP'nin Ctrl+F aynası **kapalı** kalır.
5. YKİ: İHA noktası **yeşil**, HAM GNSS satırında koordinat/uydu, alt çubukta "MAVLink TUNNEL". Günlükte `NO_ROUTE`/heartbeat akıyor.
6. Jetson (Ethernet varsa): `sudo -E … --kapi` yerine hızlı kontrol: `bash ~/navitas_tunel_staging/jetson_paket/jetson_baslat.sh --durum` → 6 birim active, restart 0.
7. **Pil değişimi = Jetson yeniden açılış:** 1–2 dk bekle, YKİ yeşile dönmeden kalkma. Ölçülen süre: __ dk.

**Yedek yol:** yönlendirici penceresi çökerse: pencereyi kapat → MP'yi **COM7 57600** ile doğrudan bağla (acil LAND/RTL MP'den her zaman verilebilir) → YKİ o an rota görmez.

## 3. Sabah pervanesiz zorunlu sıra
1. Görsel muayene + kolları elle burma (önce M1/M4); vida/somun; kablolar pervane alanı dışında.
2. Accel kalibrasyonu + Level (gövde yeniden yapıldı).
3. **Pusula kalibrasyonu dışarıda, Jetson AÇIK, pil takılı, metalden ≥ 5 m** → reboot.
4. GPS: 3D fix, uydu ≥ 12, HDop < 1,0; MP Messages'ta **PreArm satırı yok**.
5. Parametre teyidi (Refresh Params): `BATT_CAPACITY 13000 · BATT_LOW_VOLT 14.0 · BATT_CRT_VOLT 13.2 · BATT_ARM_VOLT 14.4 · BATT_FS_VOLTSRC 1 · ATC_RAT_RLL/PIT P 0,07 I 0,07 D 0,002 · FENCE_ENABLE 1 (50 m / 60 m)`. **Tam dökümü kaydet:** `results\saha_20260919\param_<saat>.param`.
6. Motor testi A/B/C/D %10 (A=M1 sağ-ön CCW, B=M4 sağ-arka CW, C=M2 sol-arka CCW, D=M3 sol-ön CW), videolu; ESC sinyalleri AUX1–4'te, MAIN1–4 boş.
7. Failsafe: A4 CH6 disarm 3/3 · A1 kumanda kapat → ≤ 2 s Radio Failsafe + LAND.
8. **YKİ'den ARM (iki basış) → motorlar döner → DISARM; ACİL LAND iki basış → mod LAND.** Bu, komut yolunun kanıtıdır.
9. **Yerde armlı gaz testi YAPILMAZ:** yazılım bunu kalkış sayar ve uçuştan önce YKİ'ye SAHTE bir iniş kanıtı yazar (kırmızı "İHLAL RİSKİ" satırıyla). KALKIŞ düğmesinden ÖNCE olursa kronometreye dokunmaz; SONRA olursa kronometreyi yanlış durdurur ve geri alınamaz. Gerçek inişin kanıtı yine gelir (yeni seq). Yapıldıysa tutanağa yaz.

## 4. Uçuş kuralları
- **İlk askı (U1):** ipli/alçak, Stabilize/AltHold, ≥ 2 s gaz rampası, 1–2 m, ≥ 30 s. **Yerde Loiter'a geçilmez.** Salınım → hemen indir. `.bin` USB ile → `ucus_bin_analiz.py`: VibeZ p95 ≤ 16, motor yayılımı ≤ 40 µs, CCW−CW ≤ 60 µs, tutum ≤ 1,5°. **Geçmeden U2 yok.**
- Drone yerden kesilince YKİ'de **KALKIŞ**.
- Görev noktaları: `fda_gorev.waypoints` şablonu **yer tutucudur**; gerçek koordinatlar girilir, `Read WPs` ile doğrulanır; home–köşe < 60 m.
- Otonom kalkış (KARAR 1): A) `AUTO_OPTIONS=3`, mod AUTO, YKİ'den ARM · B) pilot Loiter'da kaldırır, MP'den AUTO. Seçim: ____
- Hakem onayı: ilk rota gelince `1) TESPİTİ DOĞRULA` → `2) YKS'DE GÖRÜLDÜ — ONAYLA → ACK (FDA)`; hakem sözlü onay. İnişten **önce**.
- Uçuşta rota gelmiyorsa: kamera/model (gün ışığı, odak) ilk şüpheli; YKİ'de `NO_ROUTE MASKE_YOK` sürekli → tutanağa "algı kanıtı yok".
- İnişte kırmızı "İHLAL RİSKİ: İKA ACK yok" satırı FDA'da **yok sayılır**.

## 5. Acil sıra (ezber)
1. Pilot: mod anahtarı → Loiter/Land, kontrolü al. 2. MP operatörü: Actions → **LAND** (ya da RTL). 3. YKİ: ACİL LAND (iki basış). 4. Yere çok yakın ve kontrolsüz: **CH6 disarm** (düşer).
Yalnız telsiz koparsa drone göreve devam eder (GCS failsafe tetiklenmez); Jetson çökerse uçuş sürer, rota gelmez.

## 6. Bilinen sınırlar (D-494)
- Tünel gecikmesi p95 268–360 ms (eşik 200 **DÜŞTÜ**); tek parçalı komut/onay 20 tekrarla güvenilir. **4 parçalı uzun rota (≥ ~25 nokta) %43 kayıp** — rota gecikebilir. Çare (kullanıcı kararı): MP hızlarını kısmak / RFD Max Window küçültmek.
- TELEM2 doygunluğu Pixhawk reboot'unda tekrarlamaz (eski istek silindi); şüphede: Jetson'da `journalctl -u navitas-seri-hub -n 2 --no-pager` — `mavlink_paket` 10 s'de ≈ 500–650 artmalı (1750 = doygun).
- Jetson RTC pilsiz: her açılışta saat yanlış; Ethernet varsa `sudo date -u -s "<UTC>"`.

## 7. Uçuş sonrası kanıt
`uptime` (sıfırlandıysa güç sorunu → sonraki uçuş YOK) · hub sayaç satırı · `.bin` USB ile · YKİ `results\prova\<klasör>` adı · MP Messages ekran görüntüsü · tutanak (pilot, saat, pil V, sonuç).
