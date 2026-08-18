# T96 — `road` HANGI ISTATISTIK OLMALI? · ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-18 · OLCUM KOSULMADAN once yazildi (D-107)
# Dayanak: D-41 · D-146 · D-158 (bulgu 5) · D-166 (oncul duzeltmesi)

## SORU

`rpi_inference.py:1255` -> `open_path = olcum["darbogaz_serit"]` (rotanin EN
DAR noktasinin seridi). `baskin_serit` (en cok rota pikseli tasiyan serit)
hesaplanir ama YAYINLANMAZ.

`road` PUANLANAN cevaptir (D-166: IKA onunla SURMEZ, waypoint ile surer).
Sorulan sey "hangi koridor acik"tir. Sorulmayan sey "en dar nokta nerede"dir.

    HANGI ISTATISTIK YER GERCEGINE DAHA YAKIN?

## OLCULECEKLER (kume yer gercegi TASIR)

Kume `sentetik_arena_kadraj_t66` (n=260), TEMIZ kare, cekilis YOK.
Yer gercegi: manifest `arena.acik_serit` · `uretec_seritleri` ·
`arena_x_araligi` · `kapali_seritler`.

Rotasi olan HER karede uc aday:
    A = darbogaz_serit   (yayinlanan, mevcut)
    B = baskin_serit     (en cok rota pikseli)
    C = cikis_serit      (rotanin UST ucunun seridi)
karsilastirilir: her birinin YER GERCEGINE UYUM sayisi.

🔴 **ESLEME TUZAGI — ONCEDEN ISARETLENIYOR.** `acik_serit` URETECIN serit
numarasidir; `serit_no()` LETTERBOX ICERIK KUTUSUNU uce boler. Bu tuzaga bu
oturumda BIR KEZ DUSULDU (`81_t74_darbogaz_yeri.py`: "kapali 13 / acik 13"
yanlis sonucu; dogrusu "46'sinin hepsi acikta" idi). Esleme
`uretec_seritleri` / `arena_x_araligi` X ARALIKLARIYLA yapilacak, INDISLE
DEGIL. Betik eslemenin kendi POZITIF KONTROLUNU basacak (or. yer gercegi
serit sayisi 3 mu, araliklar ortusmuyor mu).

## KABUL — HANGI ISTATISTIK YAYINLANIR

    (T1) uyum sayisi: kazanan aday, digerlerinden EN AZ 5 kare ONDE olmali
    (T2) kazanan A (mevcut) degilse: degisiklik yalniz `open_path` atamasinda
         olmali; `_rota_serit_olcumu` ciktisi ve diger alanlar DEGISMEZ
    (T3) `codes/test_rota_sentetik.py` 15/15
    (T4) `unittest discover -s tests` >= 589 OK, HIC dusme yok
    (T5) kararlilik: yeni istatistigin ceviren kare sayisi (sigma 2/255,
         tekrar 3, tohum 7) mevcut A'nin sayisindan BUYUK OLMAYACAK

⚠ 5 KARE nereden: D-146 ayrisma sayisini 5/258 olctu. Fark 5'ten kucukse
iki istatistik AYNI kumede AYNI seyi soyluyor demektir ve degisiklik
GEREKCESIZDIR — "biraz daha iyi" bir sayi icin puanlanan bir sozlesme alani
degistirilmez.

⚠ HICBIR MUTLAK ESIK YOK. (T1) bir FARK esigidir, (T5) tabana baglidir.
Bu oturumda mutlak esikler DORT kez patladi (D-146 · D-157 · D-159 · D-163).

## RED KURALI

- (T1) tutmazsa: **DEGISIKLIK YAPILMAZ.** Mevcut `darbogaz_serit` kalir,
  olcum kayda gecer. Bu bir basarisizlik DEGIL, gecerli bir sonuctur.
- (T5) duserse: kazanan aday daha dogru olsa bile YAYINLANMAZ; kararsiz bir
  dogru cevap, kararli bir yaklasik cevaptan iyi degildir (D-156 dersi).
- Olcut sonuca gore GEVSETILMEZ.

## ⚠ KAPSAM DISI

- T90 fail-closed korumasinin maliyeti (34 -> 31 ACIK) YENI GEREKCE altinda
  yeniden tartilmayacak (D-166 SS3). Ayri karar, ayri on kayit.
- Sartname SS5.3.2/SS6.2 metni okunmadi; puanlama iddiasi CONTRACTS SS6.3
  ozetine dayaniyor. Bu tur onu DEGISTIRMIYOR.
