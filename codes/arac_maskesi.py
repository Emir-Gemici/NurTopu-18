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


def arac_kisa_kenarlari(bgr, arac_model, conf: float = 0.25,
                        imgsz: int | None = None) -> np.ndarray:
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

    kenarlar = []
    for kare in sonuc:
        obb = getattr(kare, "obb", None)
        if obb is None or obb.cls is None or getattr(obb, "xywhr", None) is None:
            continue
        sinifler = obb.cls.cpu().numpy().astype(int)
        wh = obb.xywhr.cpu().numpy()[:, 2:4]
        for sinif, (kg, ky) in zip(sinifler, wh):
            if adlar.get(int(sinif), str(sinif)) not in ARAC_SINIFLERI:
                continue
            kenarlar.append(float(min(kg, ky)))
    return np.array(kenarlar, dtype=np.float32) if kenarlar else bos


def arac_kisa_kenar_medyani(bgr, arac_model, conf: float = 0.25,
                            imgsz: int | None = None):
    """Sahnedeki araclarin kisa kenar MEDYANI (px); olculebilir arac yoksa None.

    Medyan secildi cunku tek bir yanlis kutu (kamyon, golge, kismen gorunen
    arac) ortalamayi kaydirir; D-124 olcumu de medyanla yapildi ve kareler
    arasi bagil aralik 0,138 olarak KAYITLIDIR — olcek kahininin 0,86 guven
    carpani tam bu sayidan gelir.
    """
    kenarlar = arac_kisa_kenarlari(bgr, arac_model, conf=conf, imgsz=imgsz)
    if kenarlar.size == 0:
        return None
    medyan = float(np.median(kenarlar))
    return medyan if medyan > 0 else None


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
