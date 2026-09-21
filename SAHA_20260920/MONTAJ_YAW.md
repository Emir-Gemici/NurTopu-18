# Kamera montaj açısı — ÖLÇÜLDÜ (20 Eylül 2026)

> 🔴 **REVİZYON 3 — 21 Eylül 2026 (mimar). Aşağıdaki `+90` artık GEÇERSİZ SAYILIR.**
>
> 1. **Çelişki:** 20 Eyl ölçümü "burun görüntüde **4** (sol)" → `+90`. 21 Eyl kullanıcı:
>    "**sağdaymış**, solda değilmiş" → `−90`. İki insan gözlemi çelişiyor; ikisi de burna
>    göre yönü bilinen bir referansla kaydedilmedi. Bu fark **180°'dir**: yanlış işaretle
>    üretilen görevde görüntünün üstü rotanın tersine bakar → şeritler aynalanır (1↔3) → 0 puan.
> 2. **Görüntü döndürmesi eklendi:** kullanıcı canlı videoda "soldaki yazı üstte olmalı"
>    dedi → kamera köprüsüne `--dondur 90` (saat yönü) eklendi (`scripts/kamera_koprusu.py`).
>    Döndürme uygulanınca görüntünün üstü **eski solu** olur ve montaj açısı değişir:
>    `yeni = eski − 90`. Eski +90 idiyse **yeni 0** (burun üstte); eski −90 idiyse **yeni 180**
>    (burun altta). **İki durumda da `+90` yanlıştır.**
> 3. **Döndürme ile BİRLİKTE zorunlu:** `rpi_inference --fov 54` → **`--fov 31.99`**. Döndürülmüş
>    karenin yatay ekseni (720 px) sensörün DİKEY FOV'unu görür; 54'te bırakılırsa ölçek
>    **%77,8** kayar (ölçüldü). `arena_kare_teshis.py` de döndürülmüş karede `--fov 31.99` ister.
> 4. **Uçuştan önce ZORUNLU ölçüm (ok testi, döndürülmüş videoda):** burnun baktığı yöne
>    uzun bir cisim koy, `http://127.0.0.1:8080/video`'da ucuna bak.
>    **Yukarı → `--montaj-yaw 0`** · **Aşağı → `--montaj-yaw 180`** · sola → +90 · sağa → −90.
>    Ölçülmeden görev dosyası üretilmez. Ayrıntı: `REVIEW_LOG.md` D-524 ek 7.

> A9 ölçümü bugüne kadar hiç yapılmamıştı (`BILGILENDIRME_HE/05`), bu yüzden `montaj_yaw`
> varsayılan **0** kalıyordu ve yanlış şerit → **0 puan** riski açıktı. Bugün kapatıldı.
>
> ⚠ **Sürüm notu:** bu belgenin ilk hâli hatalıydı (−90 yazıyordu). Kullanıcı ölçümü
> düzeltti: burun **4**'te (sol), 6'da (sağ) değil. İşaret düzeltildi. **Geçerli değer aşağıdadır.**

## Ölçüm

Ok testi (belge 05 §Ok testi). Kullanıcı gözlemi, 3×3 ızgara ile:

```
1 2 3        2 = burun (ön) yönü — DOĞRU montajda görüntünün ÜSTÜ olmalıydı
4 5 6        ÖLÇÜLEN: burun görüntüde 4'te, yani SOLDA
7 8 9
```

Belge 05 tablosu:

| Görüntüde burun/ok | Görüntü üstü nedir | montaj_yaw |
|---|---|---|
| yukarı (2) | burun | 0 |
| **sola (4)** | aracın **sağı** | **+90** |
| sağa (6) | aracın solu | −90 (= 270) |
| aşağı (8) | kuyruk | 180 |

### 🔒 **montaj_yaw = +90°**

Tutarlılık kontrolü: burun görüntüde soldaysa, görüntünün üstü buruna göre 90° **sağa**
düşer = aracın **sağ** yanı. Tablo ile birebir.

## Sonuç: burun nereye bakacak

`fda_gorev_uret.py` içindeki kural (kodda sabit): `komut_yaw = (β − montaj_yaw) % 360`

    montaj_yaw = +90  →  **komut_yaw = β − 90**

- **β** = Başlangıç kenarının ortasından Hedef (karşı) kenarın ortasına kerteriz.
- Burun, rotanın **90° SOLUNA** bakar. Aracın **SAĞ yanı** hedefe döner.

```
        HEDEF kenar
            ↑  β
            |
          [İHA] ——→     burun bu yöne (β − 90)
            |           SAĞ yan hedefe bakar
        BAŞLANGIÇ kenarı
```

## Zincir doğrulaması (bugün koşuldu, kanıt)

β'nın **0°** olduğu sentetik arena verildi; `(β − montaj_yaw)` kuralına göre beklenen 270°:

```
$ python3 scripts/fda_gorev_uret.py --kose 37.7660 38.2810 --kose 37.7660 38.2815 \
    --kose 37.7665 38.2815 --kose 37.7665 38.2810 \
    --baslangic-kenari 0 --montaj-yaw 90 --irtifa 32 --cikti <dosya>

β (kerteriz)        : 0.00°
montaj yaw          : 90.00°
CONDITION_YAW komutu: 270.00°  (β − montaj_yaw)      ← BEKLENEN DEĞER, TUTTU
irtifa              : 32 m  (FENCE_ALT_MAX 50 m altında)
```

## Sahada kullanım

### A) Otonom görev dosyası (GUIDED/AUTO)

Arena köşeleri **saat yönünde**, ondalık derece; `--baslangic-kenari i` = i. köşe ile
(i+1). köşe arasındaki kenar Başlangıç kenarıdır.

```
python3 scripts/fda_gorev_uret.py \
    --kose <lat1> <lon1> --kose <lat2> <lon2> \
    --kose <lat3> <lon3> --kose <lat4> <lon4> \
    --baslangic-kenari <i> \
    --montaj-yaw 90 \
    --irtifa 32 \
    --cikti config/pixhawk/fda_gorev_saha_20260921.waypoints
```

⚠ `--montaj-yaw 90` **atlanmayacak**. Verilmezse varsayılan 0'dır ve görüntü 90° yan gelir:
rota yatay görünür, şerit araması anlamsızlaşır.

⚠ İşareti **eksi** yazmak (`-90`) görüntüyü 180° ters çevirir: **sol ile sağ şerit yer değiştirir → 0 puan.**

Betik iki kusuru yapısal olarak engelliyor (D-451, D-457): merkez dört köşeden hesaplanıp
`LOITER_TIME` satırına açıkça yazılır, ve `CONDITION_YAW` **her zaman** `LOITER_TIME`'dan
**önce** üretilir (sıra kodda sabit, nöbetçi test `test_t235e_fda_gorev_ureteci.py`).

### B) Pilot elle konumlandırıyorsa (Loiter)

> **Burnu, Başlangıç→Hedef yönünün 90° SOLUNA çevir. Aracın SAĞ yanı hedefe baksın.**

Pilot kartına bu tek cümle yazılır.

## 🔴 Bağımsız doğrulama — onaydan ÖNCE, her uçuşta

Yukarıdaki işaret türetmesine **güvenilmeyecek** (bir kez zaten ters türetildi); ekrandan
doğrulanacak:

> **YKİ haritasında rota AŞAĞIDAN YUKARI akmalı.**

- Rota **yatay** akıyorsa → açı uygulanmamış (`--montaj-yaw` unutulmuş ya da pilot çevirmemiş)
- Rota **yukarıdan aşağı** akıyorsa → işaret **ters** (−90 yazılmış)
- **Sol/sağ şeritler takas olursa 0 puandır.** Emin olunmadan hakem onayı verilmez.

Ek kontrol (belge 05 §4): ok testindeki **"ÖN" yazısı düz okunmalı**. Ayna gibi ters
okunuyorsa görüntü aynalanıyor demektir — bu olmamalı, olursa **uçulmaz**, önce incelenir
(eski `cv2.flip` hatası 16 karenin 15'inde şeritleri takas ediyordu, D-349).
