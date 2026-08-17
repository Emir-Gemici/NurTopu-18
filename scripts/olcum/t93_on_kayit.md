# T93 — K5 SIKI KAPI · ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-17 · SONUC GORULMEDEN yazildi (D-107)
# Bu dosya olcum KOSULMADAN once yazilmistir. Kural sonuca gore DEGISTIRILMEZ.

## NEDEN

D-149: `sa_000131` IKI MODLUDUR. Kesen kosularin darbogazi {14,80}, kesmeyenlerin
{15,98 · 16,00 · 17,60} — 40 eslestirilmis kosuda tek istisna yok. v30 kotu moda
gurultulu cekilislerin 3/20'sinde dusuyor, temiz cekiliste dusmedi. Yani
`65`/`66`nin kare basina TEK temiz cikarimla verdigi `K5 = 0/173` SAGLAM BIR
OZELLIK DEGIL, o cekilise ait bir sonuctur.

K5'in olcum kusuruyla UCUNCU karsilasmasi (D-114 tek kare · D-115 noktasal rota
· D-149 tek cekilis).

## DUZELTILEN IKINCI KUSUR (D-149'da vardi, burada YOK)

D-149'un gurultu dongusu bariyer maskesini de GURULTULU goruntuden turetiyordu.
Bariyer YER GERCEGIDIR (LAB a* esigi, modelden bagimsiz); sensor gurultusuyle
yerinden oynamamalidir. T93'te bariyer maskesi TEMIZ goruntuden BIR KEZ
hesaplanir, gurultu YALNIZ modelin girdisine binlenir.

⚠ Bu duzeltme D-149'un sonucunu degistirebilir. Degisirse OYLE YAZILIR;
D-149 append-only oldugu icin duzeltme yeni kayda gecer.

## OLCUM TASARIMI

  - kume        : sentetik_arena_kadraj_t66, bariyerli + olcekli kareler (173)
  - cekilis     : 1 temiz + 20 gurultulu = 21
  - gurultu     : Gauss sigma = 2/255 (68_karar_kararliligi.py recetesi)
  - ESLESTIRME  : ayni gurultu ornegi IKI modele de verilir; aksi halde fark
                  modelden mi cekilisten mi gelir ayirt edilemez
  - bariyer     : TEMIZ goruntuden BIR KEZ (yer gercegi)
  - kesisim     : (r_gerekli_px ile kalin rota) ∩ bariyer  [66 ile ayni tanim]

  TEKRAR SAYISI GEREKCESI: bilinen tek iki modlu karede kotu mod olasiligi
  ~0,15 olculdu. 20 cekilis onu 1-(0,85)^20 = **%96,1** ihtimalle yakalar.
  Daha az tekrar kapiyi yine SANSA birakirdi.

  POZITIF KONTROL: temiz cekilisin sonucu `66`nin yayimlanmis sayilarini
  BIREBIR vermelidir (v30: 0/173 · v33: 1/173). Vermezse olcum 66'dan
  IRAKSAMIS demektir; DUR ve baska hicbir sonucu rapor etme.

## KAPI TANIMI — SIKILASTIRILAN OLCUM, GEVSETILMEYEN ESIK

  K5-SIKI GECER  : hicbir karede, hicbir cekiliste kesisim YOK  (0 px)
  K5-SIKI DUSER  : herhangi bir karede herhangi bir cekiliste kesisim VAR

Esik (0 px) D-107'dedir ve DEGISMEDI. Degisen yalnizca kac cekiliste
bakildigidir.

## ONCEDEN YAZILAN KABUL

Bu olcum bir MODEL SECIMI degil, KAPI TANIMI isidir. Sonuc ne cikarsa ciksin:

  1. Iki model de DUSERSE -> K5 hicbir modelde saglanmiyor demektir; bu, model
     kusuru degil KORIDOR kusurudur (T74 sinifi) ve oyle yazilir. Terfi
     karari kullanicinindir.
  2. Yalniz v33 DUSERSE -> D-148'in terfi reddi AYAKTA kalir.
  3. Yalniz v30 DUSERSE -> v30'un uretimde olusu YENIDEN DEGERLENDIRILMELIDIR;
     mimar bunu KENDILIGINDEN degistirmez, kullaniciya bildirir.
  4. Ikisi de GECERSE -> `sa_000131` bulgusu bariyer maskesinin gurultulu
     turetilmesinden gelmis demektir ve D-149 duzeltilir.

⚠ Hicbir dalda esik gevsetilmez, hicbir dalda "neredeyse gecti" yazilmaz.

## RAPORLANACAKLAR

  - model basina: kesen KARE sayisi · kesen (kare, cekilis) cifti sayisi
  - kare basina kesme ORANI (kac/21) — IKI MODLU kareleri gorunur kilar
  - kesen kosularin darbogaz dagilimi (D-149'un ayrimi tekrar ediyor mu)
  - DOGRULANAMADI listesi
