# F5 ÖLÇÜM TURU — ÖN KAYIT (D-107)

> **Yazıldığı an:** 2026-08-25, **hiçbir maske çizilmeden önce.**
> **Yazan:** Claude 2 (başamele) · **Karar:** kullanıcı, *"ölçüm turunu başlat"*.
> ⛔ Bantlar **sonuca göre değiştirilmez.**

## 1. NE ÖLÇÜLÜYOR

**Sınıf 0'ın ve "etiketsiz" ayrımının ek maliyeti.**

F4'te amelelere açıkça *"Sınıf 0 çizme, bu turda istenmiyor"* dendi. Ölçülen
**708 sn/kare** bu yüzden işin **yarısıdır**. Yeni üç durumlu biçimde amele
her piksel için **üç karar** veriyor: sınıf 1 · sınıf 0 · etiketsiz.
14 Eylül tarihi bu eksik maliyetle hesaplandı ve **üst sınırdır**.

## 2. YÖNTEM — EŞLEŞTİRMELİ (kare zorluğu değişken olmaktan çıkar)

Aynı **12 kare** yeniden etiketlenir. Bunlar F4'te süresi **fiilen ölçülen**
14 karenin, süre ekseninde eşit aralıklı 12'sidir (117–3152 sn yelpazesi).
Aynı kare → fark **yalnız şartnameden** gelir.

⚠ Ameleler taze örneklerdir, F4'teki işi **hatırlamazlar**; tanışıklık yanlılığı
yoktur. Kendi F4 maskelerini de **görmeyecekler**.

## 3. BANTLAR — önceden yazılı

Ölçüt: **eşleştirilmiş oran** = `F5_saniye / F4_saniye`, kare başına; **medyan**.

| medyan oran | hüküm | sonuç |
|---|---|---|
| ≤ 1,30 | sınıf 0 ucuz | 14 Eylül **yaklaşık geçerli** |
| 1,30 – 2,00 | anlamlı ek maliyet | tarih **yeniden hesaplanır** |
| > 2,00 | iş belirgin büyüdü | F5 ölçeği **yeniden tartışılır** |

⚠ **Ortalama değil MEDYAN** kullanılır: F4'te tek kare 3152 sn ile 26,9 kat
yayılım üretmişti; ortalama o tek kareye esir olur.

## 4. ÖLÇÜMÜ GEÇERSİZ KILACAK DURUMLAR

- **Amele sınıf 0'ı fiilen çizmemişse** ölçüm oranı düşük çıkar ve yanıltır.
  Denetim: her maskede **sınıf 0 alanı** ve **etiketsiz alanı** ayrıca ölçülür;
  sınıf 0 oranı ~0 olan kare **ortalamaya katılmaz**, ayrıca soruşturulur.
- **Süre `null`** dönen kare orana katılmaz (D-180: ölçülemeyen değer değildir).
- Ameleler arası uyum bu turda **ölçülmez** — kareler ayrık; bu bir
  **kapasite** turudur, şartname turu değil.

## 5. ALTYAPI DÜZELTMESİ (D-279 §5)

F4'te ameleler **scratchpad'i paylaşıyordu** ve amele B'nin dosyası C'nin
sürümüyle **ezildi**. Bu turda her amele **kendi alt dizinini** alır.

## 6. BU TURDA YAPILMAYACAKLAR

`dataset/` altına kalıcı küme **yazılmaz** · eğitim **yok** · registry'ye
**dokunulmaz** · `CONTRACTS.md` **değişmez** · terfi **yok** · **push YOK**.
