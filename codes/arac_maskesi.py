"""NEDEN: Arac tespiti iki ayri yerde, iki ayri kahinle yapiliyordu.

OLCULDU (S1 / ARCHITECT_PLAN K-6): ayni hava fotografinda
    COCO  yolov8m-seg.pt  ->   2 arac
    DOTA  yolov8m-obb.pt  ->  93 arac
COCO guven esigi 0,35 -> 0,02'ye indirildi; 18 karede yine SIFIR kesisim.
Esik ayari cozum degil -- domain uyumsuzlugu. COCO yer seviyesi fotograflarla
egitildi; sartname §5.3.2 asgari 30 m irtifadan NADIR bakis istiyor.

Bunun bedeli olculdu: `copy_paste_augmentation.py` etiket yazarken sinif 0
(zemin) daima TAM KARE dikdortgen cizer, engel/hedef poligonlari ustune biner.
`engel` maskesine girmeyen her arac bu dikdortgenin altinda kalir ve "surulebilir
zemin" olarak etiketlenir. COCO 93 aracin 2'sini buldugu icin uretilen egitim
verisinde araclarin ~%98'i ZEMIN ogretiliyordu. Bu, v16'yi moloza basmada
%2,7 -> %31,6'ya cokerten *etiketsiz engel* hatasinin birebir aynisidir.

Bu modul tek kaynaktir: hem sentetik veri ureteci hem calisma zamani
haritalama ayni fonksiyonu cagirir (CLAUDE.md madde 16 -- sozlesme tek yerde).
"""

from __future__ import annotations

import cv2
import numpy as np

#: DOTA-v1 sinif adlari. Ad ile eslesir, id ile DEGIL: DOTA surumleri arasinda
#: id'ler kayar, adlar kaymaz.
ARAC_SINIFLERI: frozenset[str] = frozenset({"small vehicle", "large vehicle"})

#: COCO segmentasyon id'leri (car, motorcycle, bus, truck).
#: YALNIZ geriye uyum icin durur -- yeni cagri yerlerinde kullanilmaz.
COCO_ARAC_SINIFLARI: tuple[int, ...] = (2, 3, 5, 7)


def obb_arac_maskesi(bgr, arac_model, conf: float = 0.25, imgsz: int | None = None):
    """DOTA OBB poligonlarindan ikili arac maskesi uret.

    bgr        : (h, w, 3) BGR goruntu
    arac_model : ultralytics YOLO (OBB gorevi) ya da None
    conf       : guven esigi
    imgsz      : cikarim boyutu; None ise goruntunun uzun kenari kullanilir

    Model None ise BOS maske doner. Bos maske, serbest alani BUYUTMEZ --
    yalnizca ek cikarma yapilmaz (CLAUDE.md madde 15 monotonluk sozlesmesi).
    Cagirici bu durumu ciktisinda gorunur kilmalidir.
    """
    maske = np.zeros(bgr.shape[:2], np.uint8)
    if arac_model is None:
        return maske

    olcu = imgsz if imgsz else max(bgr.shape[:2])
    sonuc = arac_model.predict(bgr, imgsz=olcu, conf=conf, verbose=False)
    adlar = getattr(arac_model, "names", {}) or {}

    for kare in sonuc:
        obb = getattr(kare, "obb", None)
        if obb is None or obb.cls is None or obb.xyxyxyxy is None:
            continue
        sinifler = obb.cls.cpu().numpy().astype(int)
        poligonlar = obb.xyxyxyxy.cpu().numpy()
        for sinif, poligon in zip(sinifler, poligonlar):
            if adlar.get(int(sinif), str(sinif)) not in ARAC_SINIFLERI:
                continue
            pts = np.rint(poligon).astype(np.int32).reshape(-1, 1, 2)
            cv2.fillPoly(maske, [pts], 1, lineType=cv2.LINE_8)
    return maske


#: Ayni araci iki SINIFTA birden sayan kutu ciftini eleme esigi (T89 · denetim
#: bulgusu 4). Ultralytics NMS'i varsayilan olarak SINIF FARKINDADIR
#: (`agnostic_nms=False`), bu yuzden `small vehicle` + `large vehicle` olarak
#: IKI kutu birden hayatta kalabilir. Olculdu: drone 1137 kutuda 3 cift,
#: kompozit 685'te 2 cift (%0,26) — ve BESININ DE sinifi farkli, yani mekanizma
#: dogrulandi. Oran kucuk ama TEHLIKELI DURUM esik civaridir: 2 gercek arac +
#: 1 mukerrer = 3 ile esik HAKSIZ gecilir. Eleme yalnizca sayiyi AZALTIR,
#: yani fail-safe yondedir (madde 15 ile uyumlu).
MUKERRER_IOU: float = 0.5


def _eksen_kutulari(xywh: np.ndarray) -> np.ndarray:
    """(x, y, w, h) -> (x0, y0, x1, y1). Aci YOK SAYILIR: mukerrer kutu ayni
    araci gosterdigi icin eksen hizali kaba ortusme yeterlidir."""
    x, y, w, h = xywh.T
    return np.stack([x - w / 2, y - h / 2, x + w / 2, y + h / 2], axis=1)


def _mukerrerleri_ele(kenarlar: np.ndarray, kutular: np.ndarray) -> np.ndarray:
    """IoU > MUKERRER_IOU olan ciftlerden BIRINI birak. Sira korunur."""
    n = len(kenarlar)
    if n < 2:
        return kenarlar
    kt = _eksen_kutulari(kutular)
    alan = np.clip(kt[:, 2] - kt[:, 0], 0, None) * np.clip(kt[:, 3] - kt[:, 1], 0, None)
    tut = np.ones(n, dtype=bool)
    for i in range(n):
        if not tut[i]:
            continue
        for j in range(i + 1, n):
            if not tut[j]:
                continue
            ix0 = max(kt[i, 0], kt[j, 0]); iy0 = max(kt[i, 1], kt[j, 1])
            ix1 = min(kt[i, 2], kt[j, 2]); iy1 = min(kt[i, 3], kt[j, 3])
            kes = max(0.0, ix1 - ix0) * max(0.0, iy1 - iy0)
            bir = alan[i] + alan[j] - kes
            if bir > 0 and kes / bir > MUKERRER_IOU:
                tut[j] = False
    return kenarlar[tut]


def arac_kisa_kenarlari(bgr, arac_model, conf: float = 0.25,
                        imgsz: int | None = None,
                        mukerrer_ele: bool = False) -> np.ndarray:
    """DOTA OBB arac kutularinin KISA KENARLARI (px). Arac yoksa bos dizi.

    NEDEN BURADA (T86): olcek kahininin 3. katmani "arac genisligi ~1,80 m"
    referansiyla mpp uretir (D-124/D-126). Bu olcum `69_arac_referans_olcegi.py`
    ve `70_gercek_kare_rota_denemesi.py` icinde IKI KEZ kopyalanmisti; uretim
    yoluna baglanirken UCUNCU kopya cikarmak yerine tek kaynaga alindi
    (CLAUDE.md madde 16).

    ⚠ Kisa kenar ORIJINAL goruntu pikselindedir. `_preprocess` letterbox
    tuvaline goruntuyu 1:1 yerlestirir (olcekleme YOK), bu yuzden bu deger
    dogrudan tuval pikseli olarak kullanilabilir. Tuval olceklenmeye
    baslarsa BU VARSAYIM COKER.
    """
    bos = np.empty(0, dtype=np.float32)
    if arac_model is None:
        return bos

    olcu = imgsz if imgsz else max(bgr.shape[:2])
    sonuc = arac_model.predict(bgr, imgsz=olcu, conf=conf, verbose=False)
    adlar = getattr(arac_model, "names", {}) or {}

    kenarlar, kutular = [], []
    for kare in sonuc:
        obb = getattr(kare, "obb", None)
        if obb is None or obb.cls is None or getattr(obb, "xywhr", None) is None:
            continue
        sinifler = obb.cls.cpu().numpy().astype(int)
        xywhr = obb.xywhr.cpu().numpy()
        for sinif, satir in zip(sinifler, xywhr):
            if adlar.get(int(sinif), str(sinif)) not in ARAC_SINIFLERI:
                continue
            kg, ky = float(satir[2]), float(satir[3])
            kenarlar.append(min(kg, ky))
            kutular.append((float(satir[0]), float(satir[1]), kg, ky))
    if not kenarlar:
        return bos
    dizi = np.array(kenarlar, dtype=np.float32)
    if mukerrer_ele:
        dizi = _mukerrerleri_ele(dizi, np.array(kutular, dtype=np.float32))
    return dizi


# ════════════════════════════════════════════════════════════════════════════
# T89 · ASGARI ARAC SAYISI — olcek kahininin 3. katmanini ALAN DISINDA SUSTURUR
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (REVIEW_LOG D-142 yan bulgu 2, D-143'te sayiya doküldü): T86 arac
# referans olcegini uretime bagladi ve `drone` 0/12 -> 11/12 oldu. Ama katman
# ALAN DISINDA DA atesleniyordu: `gemini` (yer seviyesinden cekilmis yol
# fotograflari) 3 karede olcek turetti ve 1 karede ROTA URETTI.
#
# Bu EMNIYETSIZ yondedir: yandan/egik bakista yonlu kutunun kisa kenari govde
# genisligi DEGILDIR (perspektif). Uydurma olcek -> uydurma r_gerekli ->
# gecilemeyecek koridor gecilebilir sayilir.
#
# 🔴 ONCE BASKA BIR OLCUT DENENDI VE CURUDU (D-143): "tepeden bakista araclar
# ayni uzakliktadir, kisa kenarlarin SACILIMI kucuk olur" hipotezi olculdu —
# gemini'nin nitelikli tek karesi IQR/medyan 0,101 verdi ve bu deger drone'un
# bandinin (0,084-0,117) TAM ICINDEDIR. Sacilim AYIRMIYOR, esik cekilemez.
#
# AYIRAN sey SAYIM oldu (kaynak basina 20 kare):
#     >= 3 arac bulunan kare
#       drone     20/20      kompozit  9/9
#       gemini     1/20      val       0/20      test  0/20
# `3` esigi `drone`u 20/20 KORUR, yer-seviyesi kumelerinin 39/40'ini ELER.
#
# Esik AYNI ZAMANDA olcegin kendisini iyilestirir: medyan, ornek sayisi
# arttikca saglamlasir. Tek aracla hesaplanan "medyan" bir medyan degildir.
#
# ⚠ Yonelim dagilimi da ayiriyordu (dairesel sd: drone 0,813 · gemini 0,271)
# ama KURAL YAPILMADI — ILKESEL DEGIL: tepeden cekilmis bir OTOYOL
# goruntusunde araclar da hizali olurdu ve olcut yanlis elerdi (D-143).
ARAC_ASGARI_SAYI: int = 3

# ⚠ OLCEK YOLUNUN CIKARIM COZUNURLUGU SABITTIR (T89 · bagimsiz denetim bulgusu).
# KUSUR: kalibrasyonlarin TAMAMI (D-124 · D-126 · D-143) `obb.predict(yol, ...)`
# ile, yani Ultralytics'in VARSAYILAN imgsz=640'iyla kosuldu. Uretim yolu ise
# `olcu = max(bgr.shape[:2])`, yani DOGAL uzun kenar kullaniyordu. Kucuk nesne
# duyarliligi cozunurlukle degisir; kalibre edilmemis bir serbestlik derecesi
# olcegin HEM sayimini HEM degerini kaydiriyordu. Olculdu (drone, n=20,
# 1024x576):
#     imgsz=640 (kalibre)  mpp medyan 0,07037  ->  r_gerekli 15,6 px
#     DOGAL     (uretim)   mpp medyan 0,07392  ->  r_gerekli 14,9 px
#     bagil fark +%5,1 · r_gerekli 0,75 px KUCUK = EMNIYETSIZ yon
# T86 olcumunde bazi drone karelerinin payi +0,006 px idi; 0,75 px orada
# belirleyicidir. Cozunurluk, KALIBRE EDILDIGI degere sabitlenir.
# ⚠ SABITLEMEK TEK BASINA YETMEDI (olculdu, ayni denetim turu): 640'a
# sabitlenince 512x512'lik ALAN DISI kareler BUYUTULUYOR, olmayan ayrinti
# uretiliyor ve orada 3 arac bulunup rota cikti (`test/road_233.jpg`,
# 0 -> 1 rota). Kalibrasyonda HIC BUYUTME YOKTU: drone kareleri 1024x576'dir
# ve 640'a KUCULTULEREK olculdu. Bu yuzden deger bir TAVANDIR, hedef degil:
#     olcu = min(ARAC_OLCEK_IMGSZ, goruntunun uzun kenari)
# Boylece 1024'luk kareler kalibre edilen 640'ta kosar, 512'lik kareler
# kendi cozunurlugunde kalir ve hicbir kare BUYUTULMEZ.
ARAC_OLCEK_IMGSZ: int = 640


def _olcek_cikarim_boyu(bgr) -> int:
    """Olcek yolunun cikarim boyu: kalibre edilen TAVAN, asla BUYUTME."""
    uzun = int(max(np.asarray(bgr).shape[:2])) if bgr is not None else 0
    return max(32, min(ARAC_OLCEK_IMGSZ, uzun)) if uzun else ARAC_OLCEK_IMGSZ


def arac_kisa_kenar_medyani(bgr, arac_model, conf: float = 0.25,
                            imgsz: int | None = None,
                            asgari: int = ARAC_ASGARI_SAYI):
    """Sahnedeki araclarin kisa kenar MEDYANI (px); olcut saglanmazsa None.

    Medyan secildi cunku tek bir yanlis kutu (kamyon, golge, kismen gorunen
    arac) ortalamayi kaydirir; D-124 olcumu de medyanla yapildi ve kareler
    arasi bagil aralik 0,138 olarak KAYITLIDIR — olcek kahininin 0,86 guven
    carpani tam bu sayidan gelir.

    ⚠ `asgari` altinda kalan sahnelerde None doner (T89 · D-143). Gerekcesi
    ve olculmus esik yukarida `ARAC_ASGARI_SAYI` icin yazilidir.
    """
    kenar, _sayi, _sebep = arac_olcek_kenari(bgr, arac_model, conf=conf,
                                             imgsz=imgsz, asgari=asgari)
    return kenar


def arac_olcek_kenari(bgr, arac_model, conf: float = 0.25,
                      imgsz: int | None = None,
                      asgari: int = ARAC_ASGARI_SAYI):
    """Olcek katmaninin TEK KAYNAGI. -> (medyan|None, sayi, sebep_metni).

    NEDEN AYRI BIR FONKSIYON (T89 · bagimsiz denetim bulgusu 2): uretim yolu
    hakemin "arac YOK" ile "arac AZ"i ayirt edebilmesi icin SAYIYA ihtiyac
    duyar. Ilk surumde `rpi_inference` diziyi kendisi cekip medyani ORADA
    yeniden hesapladi; boylece `arac_kisa_kenar_medyani` uretimde
    KULLANILMAZ hale geldi ve toplama kuralinin ileride degismesi uretime
    HIC ULASMAYACAKTI. Toplama kurali burada, TEK yerde durur; hem medyan
    hem sayi hem sebep buradan doner ve dedektor YALNIZ BIR KEZ kosar.
    """
    olcu = imgsz if imgsz else _olcek_cikarim_boyu(bgr)
    kenarlar = arac_kisa_kenarlari(bgr, arac_model, conf=conf, imgsz=olcu,
                                   mukerrer_ele=True)
    n = int(np.asarray(kenarlar).size)
    esik = max(1, int(asgari))
    if n == 0:
        return None, 0, "sahnede olculebilir arac YOK"
    if n < esik:
        return None, n, (f"yalnizca {n} arac bulundu; olcek icin asgari "
                         f"{esik} gerekir (D-143)")
    medyan = float(np.median(kenarlar))
    if not (medyan > 0.0):
        return None, n, f"{n} arac bulundu ama kisa kenar medyani gecersiz"
    return medyan, n, f"arac kisa kenar medyani {medyan:.1f} px ({n} arac)"


def obb_modeli_mi(model) -> bool:
    """Verilen modelin OBB gorevi olup olmadigini soyle.

    Cagri yerleri, kullanicinin yanlislikla bir segmentasyon modeli vermesi
    durumunda SESSIZCE bos maske uretmek yerine acik uyari verebilsin diye.
    """
    if model is None:
        return False
    gorev = getattr(model, "task", None)
    if gorev == "obb":
        return True
    adlar = getattr(model, "names", {}) or {}
    return bool(ARAC_SINIFLERI & {str(a) for a in adlar.values()})


def coco_arac_maskesi(bgr, arac_model, conf: float, imgsz: int, get_masks):
    """ESKI COCO segmentasyon yolu -- yalniz geriye uyum icin.

    Yeni kod bunu cagirmaz. `get_masks` disaridan verilir ki bu modul
    `rpi_inference`'a bagimli olmasin.
    """
    yukseklik, genislik = bgr.shape[:2]
    sonuc = arac_model.predict(bgr, imgsz=imgsz, conf=conf, verbose=False)
    maskeler = get_masks(sonuc, yukseklik, genislik, sinif_idler=COCO_ARAC_SINIFLARI)
    birlesik = np.zeros((yukseklik, genislik), dtype=np.uint8)
    for maske in maskeler.values():
        birlesik = np.maximum(birlesik, maske)
    return birlesik
