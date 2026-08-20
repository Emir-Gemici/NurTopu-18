# T128-B ON KAYIT — kosum BASLAMADAN once yazildi (D-107)
# Yazan: Claude 2 / Opus 5 (basamele) · 2026-08-21

## NEDEN
D-251 olctu: `--tohum` bu recetede ETKISIZ (tohum 0 ile 42 bit-es agirlik).
Sebep kaynaktan okundu: DataLoader karistirma ureteci SABIT sayiya tohumlu
(`ultralytics/data/build.py:359`), epoch karistirmasi epoch numarasindan.
Dolayisiyla D-135'in "kararlar tek kosuyla verildi" sorusu tohum koluyla
OLCULEMEZ. Gercek kosum-ici degiskenligi olcmek icin DataLoader'in
TUKETTIGI bir seyin degismesi gerekir.

## KOSUM
`105_t122_ft_kosumu.py --kip ac --belirsiz` -> ad `t122ac_belirsiz`
Recete t122ac ile AYNI; degisen TEK sey `deterministic=False`.
⚠ Bu bir OLCUM kosumudur; URETIM RECETESI DEGISMEZ (D-107/SS9.2).

## KARAR KURALLARI (SONUC GORULMEDEN)
1. DEGISKENLIK BANDI := |t122ac(deterministic) - t122ac_belirsiz| , her olcut icin
   (cati kacagi · kaplama ICERIK · K1 · K2 · K3 · K4 · K5 · figur K0).
2. Bir olcutte v34 ile t122ac arasindaki fark BANTTAN KUCUK ya da esitse:
   o fark "kosum-ici degiskenlikten AYIRT EDILEMEZ" diye yazilir.
3. Fark banttan BUYUKSE: "bant ALT SINIRIDIR" notuyla fark ayakta kalir.
   n=2 bir DAGILIM DEGILDIR; kesin hüküm YAZILMAZ.
4. Bant SIFIR cikarsa: "bu kolla da olculemedi" yazilir; kolun neyi degistirdigi
   (ya da degistirmedigi) kaynaktan gosterilir. Sifir bant "gurultu yok"
   DEMEK DEGILDIR.
5. Bu kosum bir TERFI ONERISI DEGILDIR ve secim degistirme gerekcesi DEGILDIR.

## SIMDIDEN BILINEN SINIRLAR
· n=2 (tek cekilis). Gercek dagilim icin daha fazla kosum gerekir.
· `deterministic=False` iki seyi AYNI ANDA degistirir: (a) cudnn algoritma
  secimi (sayisal belirsizlik), (b) belirlenimci cekirdek zorunlulugunun
  kalkmasi. Bant bu ikisini AYIRMAZ; "kosum-ici degiskenlik" toplamidir.
· Veri sirasi HALA sabit olabilir (build.py:359 sabit tohum) — o durumda
  bant yalniz sayisal belirsizligi olcer ve bu RAPORDA yazilir.
