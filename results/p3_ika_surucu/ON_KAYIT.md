# ÖN KAYIT — P3: T149 İKA sürücü soyutlaması

**Tarih:** 2026-09-02 (gece) · **Yazan/karar:** Claude 2 — Fable 5, mimar
yetkisiyle · **Uygulama sonuçları görülmeden yazıldı** (D-107).

## 0. Neden

`ika_nav` motor komutunu doğrudan `gz topic` subprocess'ine basıyor
(`send_vel`) ve konumu `gz model -p` çıktısını ayrıştırarak alıyor
(`get_pose`). Gerçek İKA donanımı (seri/PWM) için **hiçbir katman yok**
(T149; boşluk raporu K2). Ayrıca `send_vel` içindeki `subprocess.run(...,
timeout=1)` zaman aşımında **istisna fırlatır** — navigate döngüsü bunu
yakalamıyor: donanım/simülatör takılırsa İKA "güvenli duruş" değil **çökme**
yaşar.

## 1. Mimar kararları (tasarım, uygulamadan önce)

1. **İmza tekerlek hızlarıdır:** `hiz_ver(sag, sol)` — plandaki `(v,w)`
   eskizi yerine mevcut `steer()`/DiffDrivePlugin sözleşmesi korunur;
   dönüşüm katmanı eklemek T141 bayt-eşitliğini bozardı.
2. **Delegasyon modül fonksiyonlarında kalır:** `ika_nav.send_vel/get_pose`
   imzaları değişmez, içeride aktif sürücüye delege eder. Böylece
   `mock.patch.object(ika_nav, "send_vel", ...)` kullanan mevcut test
   dosyaları (10+) davranış değiştirmez.
3. **Sağlık sözleşmesi:** sürücü ardışık `hiz_ver` hatalarını sayar;
   `ARDISIK_HATA_TAVANI = 3` (tek geçici aksama görevde İKA'yı durdurmasın,
   süreğen arıza 3 turda — 10 Hz'de ~0,3 s — güvenli duruşa çevrilsin).
   Tavan aşılınca `navigate` **son bir durdurma dener ve False döner**.
4. **GercekSurucu iskeleti fail-loud:** arka uç verilmeden kurulamaz —
   `DONANIM_YOK` metinli istisna (sessiz `NotImplementedError` değil).
   Cumartesi (Faz B) doldurulur.

## 2. Kapı ölçütleri (uygulama görülmeden yazıldı)

| # | senaryo | GEÇTİ ölçütü |
|---|---|---|
| T1 | Bayt-eşitlik | `GazeboSurucu.hiz_ver(1.234, -0.5)` **birebir** eski komutu üretir: `gz topic -p ~/ika/vel_cmd -m "position { x: 1.234 y: -0.500 z: 0 }"` |
| T2 | Poz ayrıştırma kilidi | Format A (position/orientation) ve Format B (6 sayı) örnek çıktılarında eski `get_pose` ile aynı (x,y,z,yaw); bozuk çıktıda (None,)*4 |
| T3 | Donanım sustu → İKA durdu | `SahteSurucu` 3 ardışık hata verince `navigate` **False** döner ve son komut **durdurma denemesidir**; istisna sızmaz |
| T4 | Geçici aksama tolere | 2 hata + düzelme → görev sürer (sayaç sıfırlanır) |
| T5 | Gazebo zaman aşımı çökertmez | `subprocess.run` TimeoutExpired/OSError fırlatınca `hiz_ver` **False** döner (istisna değil) |
| T6 | §2.2.5 kilidi sürücü yolundan | `SahteSurucu` + gerçek receiver: IHA_LANDED+IKA_GO gelmeden sürücüye **tek bir sıfır-dışı komut düşmez** |
| T7 | GercekSurucu fail-loud | Arka uçsuz kurulum `DONANIM_YOK` metinli istisna |
| T8 | Mevcut suit | ika_nav'ı yamalayan 10+ test dosyası DEĞİŞMEDEN geçer; genel kapı 15/15; tam suit OK |

**Reddetme kuralı:** T1–T8'den biri düşerse P3 kapanmaz; sebep deftere yazılır.
Eşikler sonuca göre gevşetilmez.

---

## 3. SONUÇ (2026-09-02 gece, ölçüm sonrası yazıldı)

| # | sonuç | kanıt |
|---|---|---|
| T1 | **GEÇTİ** | `hiz_ver(1.234, -0.5)` → `gz topic -p ~/ika/vel_cmd -m "position { x: 1.234 y: -0.500 z: 0 }"` birebir |
| T2 | **GEÇTİ** | Format A (quaternion→yaw) + Format B + bozuk çıktı → eski davranışla aynı |
| T3 | **GEÇTİ** | 3 ardışık arızada navigate False; son deneme (0,0) durdurma |
| T4 | **GEÇTİ** | 2 arıza + düzelme → sağlıklı, sayaç sıfırlandı |
| T5 | **GEÇTİ** | TimeoutExpired ve OSError → istisna değil False |
| T6 | **GEÇTİ** | Gerçek IkaReceiver + UDP: izinsiz yalnız (0,0); IHA_LANDED+IKA_GO sonrası sıfır-dışı komutlar sürücü yolundan aktı, varışta durdurma |
| T7 | **GEÇTİ** | `GercekSurucu()` → `IkaSurucuHatasi("DONANIM_YOK…")` |
| T8 | **GEÇTİ** | Mevcut ika_nav testleri DEĞİŞMEDEN yeşil; genel kapı 15/15; tam suit **1509 OK** (+14) |

CONTRACTS §7.2 eklendi. **P3 KAPANDI** (GercekSurucu arka ucu Faz B'de dolar).
