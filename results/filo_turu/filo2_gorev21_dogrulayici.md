# FILO2 DOGRULAYICI · gorev indeksi 21 — S6
# Kosum: 2026-08-20, dogrulayici ajan, statik kod dogrulamasi (grep + kaynak okuma)

GOREV: S6 — "`hedef` sinifi hedef tohumu olarak bagli degil" · codes/costmap_path_finder.py:730 · ONEMLI

KANIT CUMLESI (gorevden): "rota_bul yalniz yol_sinif_idler ve engel_sinif_idler okuyor;
2 = hedef hicbir yerde hedef tohumu olarak kullanilmiyor. Hedef baslangic/hedef
parametreleriyle disaridan veriliyor."

YENIDEN URETIM (bugunku kod, calisma agaci master):
- Grep `hedef_sinif` @ codes/costmap_path_finder.py -> 0 eslesme (parametre hala yok).
- `rota_bul` imzasi bugun satir 951-953:
  rota_bul(maskeler, *, mpp=None, baslangic=None, hedef=None, plan=True,
           yol_sinif_idler=(0,), engel_sinif_idler=(1,), gorsel_cikti=False, icerik=None)
  -> sinif-id olarak yalniz yol_sinif_idler ve engel_sinif_idler okunuyor.
- `serbest_alan` (satir 222) da yalniz ayni iki sinif kumesini okuyor; sinif 2
  maskesinden hedef tohumu ureten hicbir kod yolu yok.
- Hedef hala dis parametre: koridor_adaylari(... baslangic, hedef ...) satir 971-972,
  A* hedef bantlari satir 1061-1070.
- CONTRACTS.md satir 21: `2 = hedef` sozlesmesi hala gecerli.

NOT (satir kaymasi, sayi degil konum): gorevdeki `:730` referansi bugun waypoint
seyreltme kodune denk geliyor; `rota_bul` bugun `:951`. Kanit CUMLESI fonksiyon
davranisina dair ve aynen gecerli; yalnizca satir numarasi kaymis.

SONUC: HALA GECERLI
SAYILAR: hedef_sinif_idler eslesmesi 0/0 (yok); rota_bul sinif parametreleri 2/2
(yol+engel), hedef-sinif parametresi 0.

ANA BULGU: S6 hala gecerli — bugunku kodda `hedef_sinif_idler` icin 0 eslesme, rota_bul (satir 951) hala yalniz yol/engel sinif kumelerini okuyor, sinif 2 hedef tohumu olarak kullanilmiyor.
ETIKET: [BILGILENDIRICI]
