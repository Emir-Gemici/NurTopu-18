# NAVITAS — SİSTEM NASIL ÇALIŞIYOR (sade anlatım)

**Kim için:** bu projeyi kullanan ama koda bakmak zorunda olmayan biri için.
**Tarih:** 18 Eylül 2026. Kullanıcı isteği: *"sonra bana eğit öğret"*.

---

## 1. Tek cümlelik özet

Drone'un üstündeki küçük bilgisayar kameradan gördüğünü yorumlayıp **"rota şurada"** der;
bu karar telsizle yere iner; yerdeki program (YKİ) onu hakem ekranında gösterir ve
operatörün komutlarını aynı telsizden yukarı yollar.

## 2. Parçalar — kim ne yapar

| Parça | Nerede | İşi | Olmazsa ne olur |
|---|---|---|---|
| **Pixhawk** | Drone | Uçuşun **tek** otoritesi: motorlar, mod, failsafe | Uçuş yok |
| **Jetson** | Drone | Kamera + model: rotayı **bulan** taraf | Uçuş sürer, **görev verisi gelmez** |
| **Kamera (IMX477)** | Drone, aşağı bakar | Görüntü kaynağı | Jetson karar veremez |
| **Telsiz** | Drone + yer | Tek yer↔hava veri yolu | YKİ kör kalır, uçuş sürer |
| **Kumanda (pilot)** | Yerde | Elle uçuş, mod, acil DISARM | — |
| **YKİ (`yks_gui`)** | Yer bilgisayarı | Hakem ekranı: rota, telemetri, ARM/LAND/RTL | Görev gösterilemez |

**Altın kural:** *Serbest alan otoritedir; nesne katmanı yalnızca çıkarır.* Yani sistem
"burası boş" demeyi hak etmeden rota çizmez. Şüphe varsa **rota yok** der — bu bir arıza değil,
tasarım. Yanlış rota, rota yokluğundan daha kötüdür.

## 3. Havada ne oluyor (sırayla)

```
Kamera ──► Jetson (model) ──► "rota var / yok" kararı
                               │
                               ├─► HEARTBEAT (her saniye: konum, irtifa, pil, mod)
                               ├─► OPEN_ROUTE (rota bulundu, yol noktalarıyla)
                               └─► NO_ROUTE   (bulunamadı + sebep)
                                       │
                            Pixhawk ───┴──► TELSİZ ))) ((( TELSİZ ──USB──► YKİ
```

Jetson'da bunları yapan **beş ayrı program** var, her biri systemd servisi:

| Servis | İşi |
|---|---|
| `navitas-cogullayici` | Pixhawk'ın seri portunu **tek başına** açar, veriyi diğerlerine dağıtır |
| `navitas-kamera-koprusu` | Kamerayı okur, görüntüyü yerel bir adreste sunar |
| `navitas-rpi-inference` | Modeli çalıştırır, rota kararını ve telemetriyi üretir |
| `navitas-iha-inis-yayinci` | İniş kanıtını üretir (`IHA_LANDED`) |
| `navitas-iha-komut-alici` | Yerden gelen komutu Pixhawk'a çevirir |

**Neden bu kadar parça?** Seri port tek sahiplidir — üç program aynı anda Pixhawk'a bağlanamaz.
Bu yüzden portu yalnız çoğullayıcı açar, diğerleri ondan besleneir. Biri çökerse **diğerleri
ayakta kalır** ve systemd çökeni geri kaldırır.

## 4. Uçarken kimse Jetson'a bağlanamaz — ve bu normal

Jetson'da WiFi kartı yok, havada kablo da yok. Yani uçuşta SSH, ekran, klavye **yoktur**.
Bunun üç sonucu var, üçü de çözülmüş durumda:

1. **Her şey açılışta kendi kendine başlar** (servisler `enabled`). Kimse "başlat" demek zorunda değil.
2. **Bir program çökerse systemd onu geri kaldırır**, üstelik art arda çökmesin diye bekleme süresi büyüyerek.
3. **Yerle tek bağ telsizdir.** Rota, konum, iniş bildirimi, komut — hepsi oradan.

SSH yalnız **yerde**, kalkıştan önce kullanılır: Ethernet kablosu takılır, ayar/test yapılır,
kablo çıkar, drone kalkar. İnternet gerekmez — iki makine arasında kablo yeterlidir.

## 5. YKİ (hakem ekranı) ne yapar

- Gelen `OPEN_ROUTE`/`NO_ROUTE`/`HEARTBEAT`/`IHA_LANDED` mesajlarını gösterir ve **kalıcı olarak kaydeder**.
- Operatörün ARM / DISARM / LAND / RTL komutlarını yukarı yollar. **Her komut iki kez basılır**
  (yanlışlıkla basmayı önlemek için) ve düğme ancak İHA'dan onay + taze `armed` bilgisi gelince değişir.
- **Bayat veri asla taze gibi gösterilmez.** Veri eskiyse gri/kırmızı olur. "Bilmiyorum" demek,
  yanlış söylemekten iyidir.
- YKİ'nin hangi bilgisayarda çalıştığı önemli değil: telsizin USB'si hangi laptoptaysa YKİ orada açılır.

## 6. Adresler nereden biliniyor (kablo takınca IP değişiyor)

Eskiden Jetson'a YKİ'nin IP'si elle yazılıyordu; ağ değişince bağlantı kopuyordu. Artık
**Bluetooth mantığı** var: YKİ kendini imzalı olarak duyurur, karşı taraf onu bulur ve adresini öğrenir.
Sahada ölçüldü: IP değiştikten **0,2 saniye** sonra yeniden bulundu.

Aynı şey video için de yapıldı (18 Eylül): YKİ video kaynağını **tarayarak** bulur, bulamazsa
video kapalı kalır ve **görev hattına dokunmaz.**

## 7. Sık kullanılan komutlar

```bash
# YKİ'yi aç (yer bilgisayarı)
python comms/yks_gui.py --bind 0.0.0.0:5005 --eslesme ~/.config/navitas/yks_eslesme.json

# video kaynağını ara (bağlanmadan önce ne var, bak)
python comms/video_kaynagi.py --tam

# Jetson'da servisler ayakta mı
systemctl status 'navitas-*' --no-pager

# genel kapı (her değişiklikten sonra, 15/15 olmalı)
python codes/test_rota_sentetik.py
```

## 8. Bir şey ters giderse nereye bakılır

| Belirti | İlk bakılacak yer |
|---|---|
| YKİ'de İHA kırmızı | Jetson açık mı, telsiz bağlı mı, `systemctl status 'navitas-*'` |
| Rota hiç gelmiyor, hep `NO_ROUTE` | Kamera odağı ve ışık — bulanık görüntüde model her yeri engel sayar (ölçüldü) |
| Konum/pil görünmüyor | Heartbeat akışı (ONARIM-18) ve telsiz hattı |
| Video yok | `video_kaynagi.py --tam` çıktısı; video yokluğu görevi **etkilemez** |
| Bir şey "çalışıyor" deniyor ama kanıt yok | `REVIEW_LOG.md` — her hüküm ölçümle yazılır |

## 9. Bu projenin çalışma kuralı (en önemli kısım)

**Ölçülmeyen şey "çalışıyor" sayılmaz.** Bir iddia ya koşulmuş bir komutun gerçek çıktısıyla
gelir ya da "ÖLÇÜLEMEDİ" yazılır. Testin geçmesi yetmez: test yanlış yazılmış olabilir, bu yüzden
testin kendisi de bozularak (mutasyon) sınanır. Ve **bir iş, onu yapanın onayıyla kapanmaz.**

Bu kurallar bugüne kadar en az üç kez yanlış karar verilmesini engelledi — ham çıktının repoda
durması, ölçümden önce yazılan ön kayıt, ve beş maddelik itiraz kalıbı sayesinde.
