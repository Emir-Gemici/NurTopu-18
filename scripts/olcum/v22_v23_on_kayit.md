# v22 (T53) ve v23 (T54) KABUL ON KAYDI
# Yazan: Claude 1 (mimar) · 2026-08-19 · OLCUMLER KOSULMADAN once yazildi (D-107)
# ⚠ Bu metin yazilirken egitim loglarindaki fitness/mAP degerlerine BAKILMADI.

## NE SINANIYOR

Iki TIKAYICI gorev ayni gece kosuldu (kullanici karari):

  v22_on10_gercek  (T53) — 11-sinif on-egitim + GERCEK DOKU karisimi AYNI kosuda.
      Hipotez: on-egitim alan-ici dogrulugu ve ASIRI-TESPIT FRENINI verir
      (v15: IoU 0,425 · otopark %24,1); gercek doku KORLUGU acar (v21: duyar
      0,890). Ikisi HIC birlestirilmemisti.
  v23_t54_engelli  (T54) — bina/agac/su/havuz -> `blocked` eslemesi.
      Hipotez: 2 sinifli donusum modele "cati zemin DEGILDIR" demiyordu
      (etiketsiz arka plan DENETIM ALMAZ); esleme bunu ogretir.

## VARSAYILAN: **v30 KALIR**

Bu, D-132'nin kalibidir. Aday ancak asagidakilerin HEPSINI saglarsa uretime
alinir. "Neredeyse" kabul edilmez.

## KABUL OLCUTLERI — HEPSI BIRDEN

    (1) `65_kabul_denetcisi.py` verdikti = "URETIME ALINIR"
        (D-107'nin ALTI olcutu: K0..K5; esikler betige GOMULU, ben
         DEGISTIRMIYORUM — kod tek kaynak)

    (2) K5-SIKI POPULASYON KAPISI = 0/173 kare
        (`66_k5_bariyer_populasyon.py`, 173 kare x 21 cekilis)
        ⚠ TEK TEMIZ CEKILIS YETMEZ: D-150 v30'un `K5=0`inin SANSLI CEKILIS
        oldugunu olctu. Bu sart PAZARLIGA KAPALIDIR (D-132'nin 2. sarti).

    (3) K3 = %0,0 TAM — agir basma BELIRMEYECEK
        D-132'nin 3. sarti: esik %3'tur ama v27/v28/v30 SIFIR verir; sifirdan
        cikmak bir GERILEMEDIR ve esigin altinda kalmasi onu kabul edilebilir
        yapmaz.

    (4) K2 (moloza basma) <= **%8,53** — v30'un OLCULEN degeri
        (kayit defteri `metrics.k2_moloza_basma_yuzde.olculen`)
        ⚠ Mutlak esik (%15) DEGIL, URETIMIN KENDI degeri. Bu oturumda mutlak
        esikleri baska baglamdan kopyalamak DORT kez patladi (D-146 · D-157 ·
        D-159 · D-163); her esik ayni yolda olculmus tabana baglanir.

    (5) KARARLILIK (`68_karar_kararliligi.py`) ceviren kare <= **8/260**
        — v30'un olculen degeri (kayit defteri `metrics.karar_cevrilmesi`).
        🔴 BU YENI BIR KAPIDIR ve sonucu gormeden ekleniyor. Gerekce: D-133'te
        mimar bu olcutu eksik birakip sonucu GORDUKTEN SONRA eklememisti
        (dogru davranis). Bu tur ONCEDEN ekliyorum, cunku D-156 tam bu eksende
        bir degisikligi (8 -> 11/260) REDDETTI: emniyeti iyilestiren ama
        kararliligi bozan bir sey KABUL EDILMEZ.

    (6) `codes/test_rota_sentetik.py` 15/15 · `unittest discover -s tests`
        >= 620 OK (model degisikligi kod kapilarini dusurmemeli)

## KISMI GECIS — KARAR INSANINDIR

Bir aday (1)(2)(3) saglayip yalniz (4) veya (5)'te URETIMDEN 1-2 birim geride
kalirsa: **OTOMATIK TERFI YOKTUR**, ama RED de ilan edilmez. Sonuc sayilariyla
raporlanir ve karar kullaniciya birakilir. Dayanak D-133: *"iki KABUL
EDILEBILIR model arasindaki sevk karari on-kayitlarda cozulmez ve INSANA
aittir"*. 3 birim ve uzeri gerileme REDDIR (D-156 emsali: 8 -> 11).

## YASAKLAR

  · **fitness / mAP KARAR OLCUTU DEGILDIR** (K-3). Egitim loglarindaki hicbir
    sayi terfi gerekcesi olamaz. Arena siralamasini TERSINE cevirdigi olculdu.
  · **"Gercek arenada calisir" DENMEZ.** Gercek 30 m arena karesi YOKTUR
    (D-88/D-99, kalici sinir). Butun sayilar SENTETIKTIR.
  · **`gercek_kare_gecen` BASARI OLARAK SUNULMAZ** (D-133/D-134): gecis sebebi
    dogru gormek degil AZ ZEMIN GORMEK olabilir. Olculurse kaplama ile birlikte
    raporlanir, tek basina DEGIL.
  · Olcut sonuca gore GEVSETILMEZ.

## OLCUM SOZLESMESI

Kume `sentetik_arena_kadraj_t66` (n=260). Her aday icin AYNI betikler, AYNI
argumanlar, AYNI kume. v30'un sayilari kayit defterinden okunur — YENIDEN
KOSULMAZ (aynilik icin gerekirse kosulur ve fark bildirilir).
