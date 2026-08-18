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

## YER GERCEGI — ESLEME DOGRULANDI (mimar, olcum ONCESI)

Manifest `uretec_seritleri` KADRAJA gore 2-5 serit tasir (dagilim: 2->39,
3->116, 4->54, 5->51). Ama her serit girdisinde `karar_seridi` alani vardir ve
ACIK seritte doludur — bu, URETECIN KARAR UZAYINDAKI KENDI ETIKETIDIR.

Mimar 260 karede dogruladi:

    karar_seridi != serit_no(serit_kutusu merkezi) olan kare : 0 / 260
    acik_serit = None olan kare                              : 49 / 260
      -> 49'unun HEPSI belirsiz=True ve beklenen_durum='BELIRSIZ'

⚠ Yani D-166'da isaretledigim ESLEME TUZAGI BU KUMEDE ISIRMIYOR: `karar_seridi`
zaten karar uzayindadir ve `serit_no` ile 260/260 ortusur. Fazladan esleme
makinesi KURMA. Ama POZITIF KONTROLU yine de bas (0 degilse olcum gecersiz).

**KARSILASTIRILABILIR KUME:** `acik_serit` None OLMAYAN 211 kare, VE uretimin
rota urettigi kareler. 49 BELIRSIZ kare DISLANIR (uretecin kendisi tek cevap
ilan etmiyor).

## KABUL — HANGI ISTATISTIK YAYINLANIR

🔴 **ILK YAZDIGIM OLCUT GECERSIZ, OLCUMDEN ONCE GERI ALINDI.** "Kazanan aday
digerlerinden EN AZ 5 KARE onde olmali" yazmistim; dayanagi D-146'nin
"5/258 karede A != B" olcumuydu. Ama ayrisan kare sayisi ZATEN ~5 ise, "5 kare
onde" ancak 5-0'lik bir supurme ile olusur ve ustelik o 5 karenin hepsinde yer
gercegi bulunmasi gerekir (49 kare BELIRSIZ olarak dislaniyor). Yani esik
BUYUK OLASILIKLA ULASILAMAZDI ve T96 daha kosmadan "degisiklik yok"a
kilitlenirdi. **Bu, bu oturumda DORT kez yasanan kusurun (D-146 · D-157 ·
D-159 · D-163) BESINCISIDIR; farki: bu kez OLCUMDEN ONCE yakalandi.**

Olcut TAMAMEN GORELI ve DOMINANS bicimine cevrildi:

    (T1a) TAM KUME: kazananin yer gercegine uyum sayisi, digerlerinin
          uyum sayisindan KUCUK OLMAYACAK
    (T1b) AYRISAN ALT KUME: kazanan, digerinin YANILDIGI her karede DOGRU
          olacak VE digerinin DOGRU oldugu hicbir karede YANILMAYACAK
          (yani KESIN DOMINANS; takas varsa degisiklik YOK)
    (T1c) ayrisan + yer gercegi olan alt kume BOS ISE -> bu kumede
          KARAR VERILEMEZ, degisiklik YOK, sonuc oyle kaydedilir
    (T2)  kazanan A (mevcut) degilse degisiklik yalniz `open_path`
          atamasinda olacak; `_rota_serit_olcumu` ciktisi DEGISMEZ
    (T3)  `codes/test_rota_sentetik.py` 15/15
    (T4)  `unittest discover -s tests` >= 589 OK, HIC dusme yok
    (T5)  kararlilik: kazananin ceviren kare sayisi (sigma 2/255, tekrar 3,
          tohum 7) mevcut A'nin sayisindan BUYUK OLMAYACAK

⚠ NEDEN KESIN DOMINANS: `road` PUANLANAN bir sozlesme alanidir. Iki istatistik
takas yapiyorsa (her biri bazi karelerde hakli) net kazanc yoktur ve puanlanan
bir alani calkalamak bedava degildir. Takas = DEGISIKLIK YOK.

⚠ HICBIR MUTLAK ESIK YOK. Hepsi ya karsilastirma ya tabandir.

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
