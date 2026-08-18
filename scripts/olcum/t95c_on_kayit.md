# T95-C — `rota_bul` ACIKLIK KORUMASI, GURULTU ALTINDA KARARLILIK · ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-18 · OLCUM KOSULMADAN once yazildi (D-107)
# Dayanak: D-156 (V1 tam bu eksende olduruldu) · D-159 · D-162 · D-163

## NEDEN UCUNCU TUR — ve neden T95 hala uygulanmiyor

T95-B'de olculebilir HER SEY tuttu (kapsami duzeltilmis (4'a') dahil). Ama
olcutu DORT kez duzelttim ve her duzeltmede sonuc "gecti"ye yaklasti.
Duzeltmelerin her biri nesnel olarak dogrulanabilir; yine de dort kez olcut
duzeltmis birinin "artik hepsi tutuyor" demesi tek basina yeterli degildir.

Bu yuzden T95, **HIC OLCULMEMIS** ve bu kurali **DAHA ONCE BIR KEZ OLDURMUS**
bir eksende sinanir:

    D-156: ayni kuralin SABIT ESIKLI bicimi (V1) K5'i cozdu ama kararliligi
           8 -> 11/260 BOZDU ve TAM BU YUZDEN REDDEDILDI.

W1 bicimi KATMAN A'da kararliligi korudu (8/260) — ama `rota_bul` FARKLI
parametrelerle kosar ve bu yolda hicbir gurultu olcumu YOKTUR:

    rpi_inference:  aci_esigi_derece = 0,0   · gecilebilir = koridor > 0
    rota_bul     :  aci_esigi_derece = 15,0  · gecilebilir = dt_px >= r_gerekli

D-158 bulgu 1 asama 2'nin (aci esigi) korumayi silebildigini zaten gostermisti.

## OLCUM SOZLESMESI

- Kume `sentetik_arena_kadraj_t66` (n=260).
- Gurultu recetesi 68/75 ile BIREBIR: `sigma=2.0/255`, `tekrar=3`, `tohum=7`.
  RNG akisi da AYNEN: temiz kosu cekilis YAPMAZ, ardindan kare basina 3 cekilis.
  Sayilar D-142/D-145 ile kiyaslanabilsin diye DEGISTIRILMEZ.
- Kare + cekilis basina model YALNIZ BIR KEZ kosar; cikan AYNI `mk` HEM taban
  HEM koruma `rota_bul` cagrisina verilir (D-139). Iki ayri cikarim YASAK.
- Kararsizlik olcusu: bir karenin 4 kosumunda (1 temiz + 3 cekilis)
  `(durum, yol_no)` demeti AYNI degilse o kare CEVIRMIS sayilir.

## KABUL — HEPSI BIRDEN

    olcut                                          esik
    (K1) koruma altinda ceviren kare  <=  ayni kosumdaki TABAN
    (K2) temiz kosuda ACIK            >=  ayni kosumdaki TABAN
    (K3) koruma altinda DOGRULAMA_BASARISIZ kare  <= TABAN
    (6)  codes/test_rota_sentetik.py  15/15
    (7)  unittest discover -s tests   >= 584 OK, HIC dusme yok

Bunlara EK olarak T95-B'de tutan olcutler gecerliligini korur; yeniden
olculmez (uretim kodu degismedi).

⚠ HICBIR MUTLAK SAYI YOK. Dort turdur mutlak esikler patliyor (D-146 taban 31,
D-157 taban 258, D-159 taban 31, D-163 kapsam hatasi). Bu turda her esik AYNI
KOSUMDA olculen tabandir.

## 🔴 BEKLENTIM VE NEDEN OLCUT YINE DE GEVSEK DEGIL

Mekanizma daralticidir: `yol_no` `koridor_adaylari`dan gelir ve `yol_duzelt`ten
ONCE belirlenir — koruma koridor SECIMINI dogrudan ceviremez. Cevirebilecegi
tek yol `durum`u `DOGRULAMA_BASARISIZ`/`KAPALI_DAR`a dusurmektir (daha cok
dugum -> daha cok dogrulanacak segment). Temiz karede `yol_no` 31/31 AYNI cikti.

Yani BEKLENTIM kararliligin BOZULMAMASI. Olcut tam da bu beklentiye karsi bir
sinamadir: beklentim yanlissa T95 OLUR. Ayirt edici olgu: (K1) tabandan BUYUK
cikarsa T95 REDDEDILIR ve daha az mudahaleci bir bicim aranir (or. korumanin
yalniz asama 1'de kosmasi, ya da onek gecisinin yalniz reddedilen kirislerde
calistirilmasi).

## RED KURALI

- Biri bile tutmazsa degisiklik URETIME YAZILMAZ, gorev `[ ]` kalir.
- Olcut sonuca gore GEVSETILMEZ. Bir olcutu duzeltmek gerekiyorsa gerekce
  NESNEL olmali (taban sayisi / kaynak kapsami) ve ACIKCA kayda gecmeli
  (D-157 · D-160 · D-163 usulu).
