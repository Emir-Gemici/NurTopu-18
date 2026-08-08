"""NEDEN: Sinif kimlikleri iki ayri ad alaninda yasiyor ve ikisi de sayi 2'yi
kullaniyordu. Bu, olculmus ve KRITIK bir kusurdur (REVIEW_LOG D-17 oncesi S2,
red team K3 pozitif kontrolu):

    scripts/copy_paste_augmentation.py  ->  2 = HEDEF   (H brandasi, egitim sinifi)
    simulation/scripts/iha_haritala.py  ->  2 = ARAC    (costmap runtime katmani)

Uc sinifli (0,1,2) veriyle egitilmis bir model `iha_haritala` yoluna verilirse
`engel_sinif_idler=(1, 2)` HEDEF'i engel sayar; IKA hedefe hicbir zaman ulasamaz
ve gorev puani sifirlanir.

COZUM: iki ad alani AYRILIR ve sayilari CAKISMAZ.

  * EGITIM SINIFLARI  — veri setinde ve model ciktisinda gecerli id'ler.
                        Bunlar YOLO etiket dosyalarina yazilir; degistirilemez.
  * COSTMAP KATMANLARI — calisma zamaninda birlestirilen kanallar. Bunlar model
                        ciktisi DEGILDIR: arac maskesi ayri bir DOTA OBB
                        modelinden gelir. `serbest_alan()` sozluk anahtarlarini
                        kullanir (`if c in maskeler`), id'nin sayisal degeri
                        onemli degildir -- yalnizca CAKISMAMASI onemlidir.

MIMARI DEGISMEZ (CLAUDE.md madde 15): "Serbest alan OTORITEDIR; nesne katmani
yalniz CIKARIR." Bu dosya yeni bir engel kaynagi TANIMLAMAZ, yalnizca mevcut
kanallara cakismayan kimlik verir. `serbest(K1 ^ !K2) subset serbest(K1)`
degismeden korunur.

Bu modul disinda hicbir yerde ciplak sinif sayisi yazilmaz (CLAUDE.md madde 16).
"""

from __future__ import annotations

# --------------------------------------------------------------------------
# EGITIM SINIFLARI — veri seti / model ciktisi ad alani
# --------------------------------------------------------------------------
ZEMIN = 0
ENGEL = 1
HEDEF = 2

EGITIM_SINIF_ADLARI: dict[int, str] = {
    ZEMIN: "zemin",
    ENGEL: "engel",
    HEDEF: "hedef",
}

#: `data.yaml` icin 2 sinifli (zemin/engel) egitim sozlesmesi
IKI_SINIF_ADLARI: dict[int, str] = {ZEMIN: "traversable", ENGEL: "blocked"}

#: Model ciktisindan maske uretilirken kullanilan varsayilan sinif kumesi.
#: `rpi_inference.get_masks(..., sinif_idler=...)` bunu bekler.
ALGI_SINIF_IDLERI: tuple[int, ...] = (ZEMIN, ENGEL)


# --------------------------------------------------------------------------
# COSTMAP RUNTIME KATMANLARI — ayri ad alani, egitim id'leriyle CAKISMAZ
# --------------------------------------------------------------------------
# 10'dan baslar: egitim sinif uzayi (0..9) ile carpismayacak sekilde secildi.
# Boylece 3 sinifli bir model bu yola verilse bile HEDEF (2) hicbir zaman bir
# costmap engel katmanina denk gelmez.
KATMAN_ZEMIN = 0    # segmentasyon: traversable
KATMAN_MOLOZ = 1    # segmentasyon: blocked
KATMAN_ARAC = 10    # DOTA OBB arac poligonlari (ayri model)

#: `rota_bul(yol_sinif_idler=...)` icin gecilebilir kanallar
COSTMAP_YOL_KATMANLARI: tuple[int, ...] = (KATMAN_ZEMIN,)

#: `rota_bul(engel_sinif_idler=...)` icin engel kanallari.
#: Yeni bir engel kaynagi eklenirse BURAYA eklenir -- cagri yerlerine sayi yazilmaz.
COSTMAP_ENGEL_KATMANLARI: tuple[int, ...] = (KATMAN_MOLOZ, KATMAN_ARAC)


def costmap_katmanlari(zemin, moloz, arac=None) -> dict[int, object]:
    """Algi maskelerinden costmap katman sozlugunu kur.

    Cagri yerlerinin `{0: ..., 1: ..., 2: ...}` gibi ciplak sayilarla sozluk
    kurmasini engeller. `arac` verilmezse arac kanali hic eklenmez; bu, arac
    modeli yokken serbest alanin YANLISLIKLA BUYUMESINI degil, yalnizca ek
    cikarmanin yapilmamasini saglar.
    """
    katmanlar: dict[int, object] = {KATMAN_ZEMIN: zemin, KATMAN_MOLOZ: moloz}
    if arac is not None:
        katmanlar[KATMAN_ARAC] = arac
    return katmanlar


def dogrula() -> None:
    """Iki ad alaninin cakismadigini calisma zamaninda kanitla.

    Bu bir test degil, bir SOZLESME KAPISIDIR: birisi ileride KATMAN_ARAC'i
    2 yaparsa import aninda patlar, sessizce hatali rota uretilmez.
    """
    egitim = set(EGITIM_SINIF_ADLARI)
    katman_engelleri = set(COSTMAP_ENGEL_KATMANLARI)
    cakisma = egitim & katman_engelleri - {ENGEL}
    if cakisma:
        raise AssertionError(
            f"Sinif-id cakismasi: {sorted(cakisma)} hem egitim sinifi hem costmap "
            f"engel katmani. HEDEF={HEDEF} bir engel katmanina denk gelemez."
        )
    if HEDEF in katman_engelleri:
        raise AssertionError(
            f"HEDEF ({HEDEF}) costmap engel katmanlari icinde: "
            f"{sorted(katman_engelleri)} -- IKA hedefe ulasamaz."
        )


dogrula()
