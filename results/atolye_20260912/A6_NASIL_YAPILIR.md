# A6 — SiK 433 MHz RTT / KAYIP / VERİ HIZI · AYRINTILI YORDAM
**Süre: 25 dk · Kamera/uçuş gerekmez · Bugün yapılabilir**

## 0. Neden bu ölçüm?
Kodumuz "ACK gelmezse komutu tekrar gönder" mantığıyla çalışır. Tekrar aralıkları:
`IKA_GO_TEKRAR_ARALIGI_S = 0,25 s` ve `PARASUT_TEKRAR_ARALIGI_S = 0,20 s`
(`codes/karar_sozlesmesi.py`). **Gidiş-dönüş süresi (RTT) bu aralıktan büyükse** komut,
ACK daha yoldayken yeniden gönderilir → hat şişer → ACK daha da gecikir → kendini
besleyen tıkanma. Yani bu ölçüm "telsiz çalışıyor mu" değil, **"tekrar tasarımımız
geçerli mi"** sorusunu yanıtlar. Şimdiye kadarki ölçüm **radyosuzdu** (TCP köprüsü).

## 1. Donanım kurulumu (5 dk)
- İki SiK telsizi Pixhawk'tan **ayır**; ikisini de PC'ye USB ile tak.
- **Antenleri tak** (antensiz verici bozulur), ikisi de **dik**, aralarında **2–5 m**.
- Aygıt Yöneticisi → `Bağlantı Noktaları (COM ve LPT)` → iki numarayı not et (ör. COM7, COM9).
- **Mission Planner KAPALI olacak** — portu tutar, betik açamaz.

## 2. Telsiz ayarlarını oku ve kaydet (5 dk) — *ECC burada*
MP → `Setup → Optional Hardware → SiK Radio` → **`Load Settings`**.
Sol sütun **Local**, sağ sütun **Remote**. Bu satırlar FDR'ye gidiyor:

| Alan | Ne işe yarar |
|---|---|
| **Baud** | Pixhawk↔telsiz seri hızı (57600 olmalı, hava hızı değil) |
| **Air Speed** | Gerçek RF hızı (kbps). **Düşürmek menzili artırır, gecikmeyi büyütür.** |
| **Net ID** | İki telsiz **aynı** olmalı, başka takımlarla **farklı** |
| **Tx Power** | dBm. BTK sınırı için önemli |
| **ECC** | ⬅ **Golay hata düzeltme.** İşaretli = açık |
| **Mavlink** | Çerçeve farkındalığı (MAVLink seçili olsun) |
| **Op Resend** | Telsiz seviyesinde tekrar |
| **Min/Max Freq · Num Channels · Duty Cycle · LBT RSSI** | Frekans atlama düzeni |

→ Ekran görüntüsü: `A6_sik_mp_ekrani.png` ✅ *(kaydettin)*
→ Değerleri metne de yaz: `A6_sik_ayar.txt`

**ECC yorumu:** ECC her veri baytına düzeltme kodu ekler, **etkin hızı yaklaşık yarıya
indirir** ama bozuk paketleri düzeltir. Bizde yük düşük — misyon veri hızı ölçüldü
**~400 B/s**, hat 5760 B/s → ECC açıkken bile doluluk **%14**. **Açık bırak**: kaybettiğin
hız zaten kullanılmıyor, kazandığın şey menzil ve dayanıklılık.

## 3. Referans ölçüm — ÖNCE bunu yap (3 dk)
Radyo olmadan, aynı betikle yazılımın kendi gecikmesini ölç. Böylece sonraki sayıdan
**radyonun payını ayırabilirsin**. İki PowerShell penceresi:

```powershell
# Pencere 1 (yankı)
& $PY -B scripts/sik_rf_olc.py --rol yanki --tasiyici udp --bind 127.0.0.1:14650

# Pencere 2 (ölç)
& $PY -B scripts/sik_rf_olc.py --rol olc --tasiyici udp --peer 127.0.0.1:14650 `
    --n 200 --aralik 0.25 --cikti results/atolye_20260912/A6_udp_referans.json
```
Beklenen: RTT p95 **birkaç ms**. Bu, "yazılım sıfır gecikme sayılır" tabanıdır.

## 4. Gerçek RF ölçümü (10 dk)
```powershell
# Pencere 1 (yankı ucu) — açık kalır
& $PY -B scripts/sik_rf_olc.py --rol yanki --port COM9 --baud 57600

# Pencere 2 — İKA_GO kadansı (0,25 s)
& $PY -B scripts/sik_rf_olc.py --rol olc --port COM7 --baud 57600 `
    --n 200 --aralik 0.25 --cikti results/atolye_20260912/A6_sik_ikago.json

# Pencere 2 — PARAŞÜT kadansı (0,20 s)
& $PY -B scripts/sik_rf_olc.py --rol olc --port COM7 --baud 57600 `
    --n 200 --aralik 0.2 --cikti results/atolye_20260912/A6_sik_parasut.json
```
Her koşum ~50 sn sürer (200 × 0,25 s).

## 5. Ekranda ne göreceksin
```
gonderilen : 200
ACK alinan : 200
kayip      : 0  (%0,0)
RTT        : p50=... ms  p95=... ms  maks=... ms
veri hizi  : ... B/s   ... bit/s   ... paket/s
VERDIKT    : tekrar tasarimiyla UYUMLU
```
**Çıkış kodu:** `0` = UYUMLU · `1` = UYARI (p95 eşiği aşıyor) · `2` = ÖLÇÜLEMEDİ (hiç ACK yok / port açılmadı).
Kontrol: `echo $LASTEXITCODE`

## 6. Geçme ölçütü (ön kayıt — şimdi yazıldı, ölçümden önce)
**RTT p95 < 200 ms** (iki eşiğin küçüğü) **her iki kadansta**. Kayıp ve veri hızı için eşik **yok**,
yalnız raporlanır (ilk ölçüm).

## 7. BEKLENTİ (HESAP — ölçüm değil)
57600 baud 8N1 → 10 bit/bayt → 0,174 ms/bayt. Çerçeve ≈ 80 B → her uçta seri süre 13,9 ms.
Hava 64 kbps → 80 × 8 / 64000 = 10 ms (**ECC açıksa ≈ 2×**).
RTT alt sınırı = 2 × (13,9 + 10 + 13,9) = **75,6 ms**; ECC ile **95,6 ms**. Üstüne SiK TDM dilim
beklemesi biner (BİLİNMİYOR). → **Beklenti 76–160 ms, eşik 200 ms: geçmeli.**

## 8. Sorun çıkarsa
| Belirti | Sebep | Çözüm |
|---|---|---|
| `port acilamadi` | MP açık ya da COM yanlış | MP'yi kapat, Aygıt Yöneticisi'nden numarayı doğrula |
| `hic ACK yok` (çıkış 2) | Net ID farklı / anten yok / telsiz eşleşmemiş | İki telsizin **yeşil sabit** ışığı yanmalı; MP'den Net ID'leri eşitle |
| p95 > 200 ms | Air Speed çok düşük ya da ECC + düşük hız birlikte | Air Speed'i yükselt (menzilden feda et) ya da tekrar aralığını sözleşmede büyüt |
| Kayıp > %5 | Antenler yakın/paralel, parazit | Antenleri dik ve 2 m ayır, USB uzatma kullan |

## 9. Çıktılar (FDR'ye gidecek)
`A6_udp_referans.json` · `A6_sik_ikago.json` · `A6_sik_parasut.json` · `A6_sik_ayar.txt` · `A6_sik_mp_ekrani.png` ✅
