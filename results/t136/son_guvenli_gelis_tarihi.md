# T136 · SON GÜVENLİ GELİŞ TARİHİ — ölçümden hesaplandı

> ⚠ **TAHMİN DEĞİL ÖLÇÜM.** Her satırın kaynağı yazılı. Ölçeklerken kullandığım
> **varsayımlar açıkça işaretli** — yanlışsa düzeltin, hesap yeniden koşar.

## 1. ÖLÇÜLEN BİRİM MALİYETLER (bugün, 14 dosyalık provada)

| adım | ölçülen | birim maliyet | kaynak |
|---|---|---|---|
| kare çıkarma (4K, dedup) | 138,9 sn / 21,8 dk video | **6,4 sn / dk video** | `results/t136/dji_prova/kosum.json` |
| kare verimi (dedup sonrası) | 569 kare / 21,8 dk | **26,1 kare / dk video** | aynı |
| parlaklık kapısı | 9,7 sn / 569 kare | ihmal edilebilir | aynı |
| etiket + çoğaltma (4K) | **4,6 sn / kare** | 569 kare ≈ 43,6 dk | fan-out ölçümü |
| eğitim | 0,58 saat / 440 görüntü, 18 epoch | ~0,0013 saat/görüntü | `codes/runs/segment/t127_temiz` |
| kabul zinciri | ~400 sn | ~7 dk | fan-out ölçümü |
| **elle etiketleme** | **569 kare için ~230–290 poligon ≈ 15–20 saat** | **~0,03 saat/kare** | fan-out ölçümü |

🔴 **Baskın terim COMPUTE DEĞİL, İNSAN EMEĞİ.** (c) çatı maskesi elle
poligon + homografi ürünüdür; depoda hazır bina kâhini **YOK**.

⚠ 4K pahalı: etiket adımı 1024×576'da 0,41 sn/kare iken 4K'da 4,6 sn/kare —
**11 kat**.

## 2. VARSAYIMLAR (düzeltilebilir)

| # | varsayım | değer | neden |
|---|---|---|---|
| V1 | gerçek çekim uzunluğu | **60 dk** 4K video | provanın ~3 katı; DJI Neo pil ömrü ve çoklu oturum |
| V2 | elle etiketleme kapasitesi | **1 kişi × 8 saat/gün** | tek insan (siz) |
| V3 | eğitim yeniden koşumu | **1 kez** | v31/T128 örnekleri: ilk koşum tutmayabilir |
| V4 | model + paket bitiş hedefi | **27 Eylül** | 30 Eylül CİHAZ GÜNÜdür; o gün yalnız `.engine` derlemesi + geçiş provası kalır (T109/T123) |
| V5 | başarısız çekim payı | **+3 gün** | bu provanın kendisi kanıt: ilk çekim kullanılamaz çıktı |

## 3. HESAP (V1–V5 ile)

```text
60 dk video  ->  kare cikarma      6,4 x 60      =   6,4 dk
             ->  kare verimi       26,1 x 60     = 1566 kare
             ->  ELLE ETIKETLEME   0,03 x 1566   = ~47 saat  = 6 IS GUNU   <- BASKIN
             ->  etiket+cogaltma   4,6 sn x 1566 = ~2,0 saat
             ->  bolum+yaml                       = <0,5 saat
             ->  egitim (V3: 2 kosum)             = ~1 gun (yeniden kosum payiyla)
             ->  kabul zinciri + aday raporu      = ~0,5 gun
                                                   ------------------------
                                        TOPLAM   ≈ 8,5 - 9 IS GUNU
```

**Geriye doğru:**

```text
27 Eylul (V4 bitis hedefi)
  - 9 is gunu  (hat)                  -> 16 Eylul
  - 3 gun      (V5 basarisiz cekim)   -> 13 Eylul
```

## 🔴 4. SONUÇ

> **Görüntü en geç 13 Eylül'de gelmezse 30 Eylül'e yetişmez.**

Bugün **21 Ağustos** → **23 gün** var. Yani takvim **şu an için yeterli**, ama
tek şartla: **çekim gündüz tekrarlanmalı** (§5).

⚠ Bu tarih **V1'e (60 dk) çok duyarlıdır.** Çekim 120 dk olursa elle etiketleme
~94 saate (12 iş günü) çıkar ve son tarih **~6 Eylül**'e kayar. Süreyi siz
söyleyin, hesabı yeniden koşayım.

⚠ **Elle etiketleme yükünü azaltmanın tek meşru yolu daha az ama daha ÇEŞİTLİ
kare çekmektir** — dedup zaten %57 eliyor; kaynakta çeşitlilik yoksa 2 kat
uçuş 2 kat etiket demek değil, 2 kat **aynı** kare demektir.

## 5. BU HESABI GEÇERSİZ KILAN ŞEY — ilk çekim KULLANILAMAZ

Prova verisi eğitime **uygun değil** ve bu ölçüldü:

```text
parlaklik (0-255 ort):  DJI medyan 21,2 · maks 73,2
                        raw_frames (calisan veri) min 118,7 · medyan 128,7
                        -> IKI DAGILIM HIC ORTUSMUYOR (400/400 kare altinda)
etiket verimi        :  otopark 440/448 (%98,2)  ·  DJI 73/569 (%12,8)
zemin maskesi        :  569 karenin 496'sinda (%87,2) TAMAMEN BOS
uretim modeli (v35)  :  569 karenin 546'sinda (%96,0) bos maske
```

Çekim **20:17–21:05** arasında yapılmış; parlaklık klip sırasıyla düşüyor
(70 → 14), yani hava kararırken çekilmiş. **7 fotoğrafın 7'si de aynı saatte**
(20:43–20:57) — elde **tek bir gündüz karesi yok**, bu yüzden "gece mi doku mu"
sorusu **ayrılamıyor** ve bu dürüstçe böyle yazılmıştır.

**İnsan işi (yalnız siz yapabilirsiniz):** çekimi **gün ışığında** tekrarlayın
ve doğrulama uçuşunu `dji/DOGRULAMA/` altına **ayrı** koyun. Hat ikisini de
kapıyla zorluyor.
