# T94 / W1 — SON TUR ON KAYIT
# Yazan: Claude 1 (mimar) · 2026-08-17 · OLCUMLER KOSULMADAN once yazildi (D-107)
# Kullanici "sen sec" dedi; karar mimarindir ve gerekcesi asagidadir.

## 3. OLCUT CELISKISININ COZUMU (D-157)

On kayitta "rota >= 259/260" yazmistim ve bunu REDDEDILMIS V1 bicimin sayisina
civilemistim; 259 ise TABANDAN (258) IYIDIR. Yani olcut, uretimin KENDISININ
saglamadigi bir esik istiyordu.

KARAR: o olcut **GECERSIZ** sayilir ve tabandan yeniden turetilir:
    rota uretilen >= 258/260   (taban v30 = 258)

⚠ "Gecti" diye YAZILMIYOR; olcut VOID edilip yeniden turetiliyor ve bu ACIKCA
kayda geciyor. Ayirt edici olgu: W1 **257** verseydi bu tartisma acilmaz,
reddedilirdi. Karar sonuca gore degil, olcutun KENDI AMACINA gore veriliyor
("rota kaybi olmasin").

## BU TURDA OLCULECEKLER (D-157 madde 4'teki eksikler)

1. K5-SIKI POPULASYON (T93 recetesi: 173 kare x 21 cekilis, sigma=2/255)
2. KABUL DENETIMI K0..K4 (65_kabul_denetcisi + gercek K5 icin 66)
3. waypoint sayisi · rota uzunlugu · sure

## KABUL — HEPSI BIRDEN (sonuc gorulmeden yazildi)

    olcut                     esik                    taban (v30)
    K5-SIKI kesen kare        == 0/173                1/173   (D-150)
    kararlilik A              <= 8/260                8/260   (olculdu: 8)
    rota uretilen             >= 258/260              258     (D-133)
    K1 rota                   >= 258/260              258
    K2 moloza basma           <= 22/258               22/258
    K3 agir basma             == 0/258                0/258
    K4 arena disi             <= 1/258                1/258
    K0 korluk                 GECER                   %8,0
    waypoint medyani          <= 16                   8
    rota uzunlugu artisi      <= %5                   —
    sure artisi               <= 2 kat                —

RED: biri bile tutmazsa W1 URETIME YAZILMAZ. "Neredeyse" kabul edilmez.
Hepsi tutarsa kod yazilir ve MADDE 7 geregi AYRI DENETIM kosulur; denetim
bulgulari islenmeden commit ATILMAZ.

⚠ Tutan bir varyant bulmak icin BASKA band degerleri ARANMAYACAK. W1 duserse
T94 kod degisikligi yapilmadan kapanir ve oyle yazilir.
