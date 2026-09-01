# K1 — HAKEM EKRANINDA TAZELİK DAMGASI · ön kayıt

Tarih: **2026-09-01** — kullanıcı onayı (K1a, "tüm onayları veriyorum")
alındıktan sonra, **kod yazılmadan önce** donduruldu.

## 0. Düzeltme — kartdaki bir ifade yanlıştı

K1 kartı *"karar kutusu 5 saniye sonra boşalıyor"* diyordu. Kod okununca
görüldü: kutu **boşalmıyor** — bayatlıkta yalnız SARI'ya boyanıyor
(`_kutu_yaz("protokol", renk=SARI)`), rota metni ve güven ekranda kalıyor.
Gerçek eksik: **yaş damgası yok** — hakem tespitin NE KADAR eski olduğunu
ve NEDEN bayat sayıldığını göremiyor. Uygulama bu gerçeğe göre daraltıldı.

## 1. Dondurulan davranış

1. Tespit **BAYAT** işaretliyken (ve onaylanmamışken) karar kutusunun
   `detay` satırı şunu gösterir ve **her tazeleme tikinde güncellenir**:
   `⏱ son ALGI kararı N sn önce — <kaynak>`; kaynak üç değerden biridir:
   *hat kesik* · *algı sustu (hat canlı)* · *tespit yaşı bilinmiyor*.
2. Kutunun `karar` metni ve güven çubuğu **SİLİNMEZ** (bugünkü davranış).
3. **Onay kilidi DEĞİŞMEZ**: bayat tespite ACK üretilemez (T169/T176
   mevcut kapıları aynen bağlayıcı).
4. Tazelik dönünce (T176 simetrisi) damga satırı diğer akışa bırakılır;
   bir sonraki OPEN_ROUTE/karar `detay`ı olağan yolla yazar.
5. Günlük **bir kez** yazılır (mevcut davranış) — damga güncellenir,
   günlük tekrarı ÜRETİLMEZ.

## 2. Kapılar (kod yazılmadan dondu)

- Bayatken iki ardışık tikte damga **artar** (canlı güncelleme kanıtı).
- `karar` metni bayatlıkta korunur (boşalma yok).
- Üç kaynak metni üçü de üretilebilir (hat/algı/bilinmiyor).
- `onayla()` bayatken yine ACK üretmez (mevcut kapı, yeniden koşulur).
- Günlük tekrar sayısı artmaz.
- Tatbikat F6: bant "ALGI ZAMAN AŞIMI" derken kutu damgası aynı hikâyeyi
  anlatır (D-383'ün kapattığı çelişki geri gelmez).
