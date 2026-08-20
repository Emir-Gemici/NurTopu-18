# T128 ON KAYIT — ikinci tohum kosumu BASLAMADAN once yazildi (D-107)
# Yazan: Claude 2 / Opus 5 (basamele) · 2026-08-21

## NEDEN
D-135: "her karar bugune kadar TEK KOSUYLA verildi; K2/K5/kararlilik
farklarinin ne kadari TOHUM GURULTUSU, olculmedi." T122 kiyasinin da
yazili sinirlarindan biri buydu (D-237 §6.2). Bekleyen secim karari
(v34 vs t122ac) kucuk arena farklarina dayaniyor:
    K2  v34 12/258  ·  t122ac 16/257
    K3  v34  0/258  ·  t122ac  1/257
Bu farklar TOHUM kaynakli olabilir. Olculmeden "geri gitti" denemez.

## KOSUM
`105_t122_ft_kosumu.py --kip ac --tohum 42` — RECETE ve veri AYNEN AYNI
(karisim_t122ac.yaml, taban v34, epochs 40, patience 15, imgsz 512).
DEGISEN TEK SEY: seed 0 -> 42. Kosum adi `t122ac_tohum42`.

## KARAR KURALLARI (SONUC GORULMEDEN)
1. TOHUM GURULTUSU BANDI := iki tohumun ayni olcutteki farkinin mutlak
   degeri. Bu bant, v34 ile t122ac arasindaki farktan BUYUKSE, o olcutteki
   fark "tohum gurultusunden ayirt EDILEMEZ" diye yazilir.
2. Cati kacagi ve kaplama icin de ayni kural uygulanir.
3. Iki tohum arasindaki fark, v34-t122ac farkindan KUCUKSE fark GERCEKTIR
   (ama n=2 tohum bir DAGILIM degildir — "gurultu tabani ALT SINIRI" diye
   yazilir, kesin hüküm degil).
4. 🔴 Bu kosum bir SECIM DEGISIKLIGI GEREKCESI DEGILDIR. Amac yalnizca
   mevcut sayilarin ne kadarinin gurultu oldugunu OLCMEK. Esik yazma ve
   terfi yetkim yok (SS9.2 / D-133).
5. Ikinci tohum daha iyi cikarsa bile "yeni aday" ilan EDILMEZ; iki tohum
   ayni recetenin iki cekilisidir.

## SIMDIDEN BILINEN SINIR
n=2 tohum. Gercek bir gurultu dagilimi icin daha fazla cekilis gerekir;
bu kosum yalnizca "fark gurultuden buyuk mu" sorusuna ALT SINIR verir.
