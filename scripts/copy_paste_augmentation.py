"""NEDEN: Gercek otopark zemini uzerine etiket maskesi bilinen moloz eklemek,
uretkenden piksel alip etiketsiz engel uretme hatasini onler. Yapistirma yalniz
zemin uzerinde yapilir; arac, mevcut engel ve hedef pikselleri korunur.

Etiket semantigi `codes/sinif_semasi.py`'den gelir: 0=zemin, 1=engel, 2=hedef.
Zemin satiri tam cercevedir; engeller ve hedefler onun ustunde ayri poligonlar
olarak yazilir. Boylece zemin poligonu engellerin altinda delik acmaz.

⚠ Ilan edilen SINIF SAYISI veriye baglidir: rastgele kipte
`--hedef-maske-dizini` verilmezse sinif 2 olusmaz. T40 `--arena` kipi ise
CONTRACTS.md 1.1'deki 2 m x 2 m kirmizi H'yi kontrollu olcekte kendisi uretir.

ARAC KAHINI (S1): araclar DOTA OBB ile bulunur, COCO segmentasyonu ile DEGIL.
Olculdu: ayni nadir fotografta COCO 2 arac / DOTA OBB 93 arac. Zemin satiri tam
cerceve oldugu icin, ENGEL maskesine girmeyen her arac ZEMIN etiketi alir --
yani kahin hatasi sessiz degil, YANLIS ETIKET uretir.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
import shutil
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import cv2
import numpy as np
from ultralytics import YOLO


KOK = Path(__file__).resolve().parents[1]
KODLAR = KOK / "codes"
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))
if str(KODLAR) not in sys.path:
    sys.path.insert(0, str(KODLAR))

from arac_maskesi import coco_arac_maskesi, obb_arac_maskesi, obb_modeli_mi
from costmap_path_finder import olcek_px, rota_bul
from karar_sozlesmesi import hedef_bant_yuksekligi, serit_no
from rpi_inference import _maskeleri_icerige_kirp, _preprocess, get_masks
from sinif_semasi import (COSTMAP_ENGEL_KATMANLARI, COSTMAP_YOL_KATMANLARI,
                          EGITIM_SINIF_ADLARI, ENGEL, HEDEF,
                          IKI_SINIF_ADLARI, ZEMIN, costmap_katmanlari)
from simulation.scripts.arena import HTAB


GORUNTU_UZANTILARI = {".jpg", ".jpeg", ".png"}
MASKE_UZANTILARI = (".png", ".jpg", ".jpeg", ".bmp")

# CONTRACTS.md 1.1: hedef, 2 m x 2 m kirmizi H brandasidir. Bu sabit yalniz
# kontrollu kompozit olcege cevrilir; gercek kameranin mpp olcumu diye sunulmaz.
ARENA_HEDEF_KENAR_M = 2.0
# T40 kabul kapisi: yazilan YOLO class-1 poligonlari, DOTA arac piksellerinin en
# az bu oranini tasimalidir. Bellek ici union bu olcumu kanitlamaz.
ARENA_ARAC_KAPSAMA_ESIGI = 0.95
ARENA_OLCEK_KAYNAGI = (
    "kontrollu kompozit varsayimi: simulation.scripts.arena.HTAB / "
    "kaynak karenin GENISLIGI; gercek kamera mpp olcumu degildir"
)


@dataclass
class UretimOzeti:
    """Bir kaynak/cesit icin denetlenebilir uretim sonucu."""

    kaynak: str
    cikti: str | None
    bolum: str | None
    durum: str
    moloz_sayisi: int = 0
    arac_px: int = 0
    mevcut_engel_px: int = 0
    hedef_px: int = 0
    sebep: str | None = None
    arena: dict | None = None


@dataclass
class ArenaGeometrisi:
    """Kontrollu uc-koridor yer gercegi ve kabul kapisi girdileri."""

    zemin: np.ndarray
    bariyer: np.ndarray
    pozitif_bariyer: np.ndarray
    hedef: np.ndarray
    acik_serit: int
    kapali_seritler: list[int]
    bariyerler: list[dict]
    icerik: tuple[int, int, int, int]
    mpp: float
    hedef_kutu: tuple[int, int, int, int]


@dataclass
class ArenaBariyerSonucu:
    """Goruntude gercekten bulunan ve yerel koridoru kesen moloz kaniti."""

    maske: np.ndarray
    kutu: tuple[int, int, int, int]
    pencere: tuple[int, int, int, int]
    parca_sayisi: int


def modulu_yukle(yol: Path, ad: str):
    """Rakamla baslayan mevcut betigi kopyalamadan yuklemek icin yardimci."""
    if not yol.is_file():
        raise FileNotFoundError(f"Kaynak betik bulunamadi: {yol}")
    spec = importlib.util.spec_from_file_location(ad, yol)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Kaynak betik yuklenemedi: {yol}")
    modul = importlib.util.module_from_spec(spec)
    # T173 (D-322): yuklenen betik KENDI klasorundeki modulleri (ornegin
    # `ayarlar`) import edebilmeli. Yalnizca yoldan yuklemek `sys.path`i
    # kurmuyordu ve `51_sentetik_arena.py` "No module named 'ayarlar'" ile
    # dusuyordu — arena kipi bu yuzden hic kosulamiyordu.
    _dizin = str(Path(yol).resolve().parent)
    _eklendi = _dizin not in sys.path
    if _eklendi:
        sys.path.insert(0, _dizin)
    try:
        spec.loader.exec_module(modul)
    finally:
        if _eklendi and sys.path and sys.path[0] == _dizin:
            sys.path.pop(0)
    return modul


def yapistir_yukle(kaynak: Path) -> Callable:
    """51_sentetik_arena.py icindeki golgeli/alfa-yumusatmali yapistir'i al."""
    yapistir = getattr(modulu_yukle(kaynak, "navitas_sentetik_yapistir"), "yapistir", None)
    if not callable(yapistir):
        raise RuntimeError(f"yapistir() bulunamadi: {kaynak}")
    return yapistir


def guvenli_cikti_kok(cikti: Path, temizle: bool) -> Path:
    """Temizleme isini proje icindeki acik dataset diziniyle sinirla."""
    kok = KOK.resolve()
    hedef = cikti.resolve()
    try:
        hedef.relative_to(kok)
    except ValueError as exc:
        raise ValueError(f"Cikti proje disinda olamaz: {hedef}") from exc
    if hedef in {kok, (kok / "dataset").resolve(), (kok / "data").resolve()}:
        raise ValueError("--temizle proje, dataset/ veya data/ kokunu silemez")
    if temizle and hedef.exists():
        shutil.rmtree(hedef)
    for bolum in ("train", "val"):
        (hedef / "images" / bolum).mkdir(parents=True, exist_ok=True)
        (hedef / "labels" / bolum).mkdir(parents=True, exist_ok=True)
    return hedef


def atomik_bytes_yaz(hedef: Path, veri: bytes) -> None:
    """Goruntu/etiket yazimini yarim dosya gorunmeden tamamla."""
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    try:
        gecici.write_bytes(veri)
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()


def atomik_jpeg_yaz(hedef: Path, bgr: np.ndarray, kalite: int) -> None:
    """BGR resmi atomik JPEG olarak yaz."""
    basarili, kodlu = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, int(kalite)])
    if not basarili:
        raise OSError(f"JPEG kodlanamadi: {hedef}")
    atomik_bytes_yaz(hedef, kodlu.tobytes())


def atomik_png_yaz(hedef: Path, maske: np.ndarray) -> None:
    """Ikili yer gercegi maskesini kayipsiz ve atomik yaz."""
    basarili, kodlu = cv2.imencode(".png", ((maske > 0).astype(np.uint8) * 255))
    if not basarili:
        raise OSError(f"PNG kodlanamadi: {hedef}")
    atomik_bytes_yaz(hedef, kodlu.tobytes())


def goruntuleri_bul(kaynak: Path) -> list[Path]:
    """Ham kare klasorundeki goruntuleri kararlı sirada bul."""
    if not kaynak.is_dir():
        raise FileNotFoundError(f"Ham kare klasoru bulunamadi: {kaynak}")
    return sorted(p for p in kaynak.rglob("*") if p.is_file() and p.suffix.lower() in GORUNTU_UZANTILARI)


def asetleri_bul(aset_dizini: Path) -> list[Path]:
    """RGBA enkaz kesitlerini bul; BGR dosyalar sonradan reddedilir."""
    if not aset_dizini.is_dir():
        raise FileNotFoundError(f"Enkaz doku bankasi bulunamadi: {aset_dizini}")
    sonuc = sorted(p for p in aset_dizini.iterdir() if p.is_file() and p.suffix.lower() == ".png")
    if not sonuc:
        raise FileNotFoundError(f"Enkaz PNG bulunamadi: {aset_dizini}")
    return sonuc


def alani_kirp(maske: np.ndarray, icerik: tuple[int, int, int, int]) -> np.ndarray:
    """Kare letterbox tuvalindeki maskeyi orijinal kare koordinatina geri getir."""
    x0, y0, genislik, yukseklik = icerik
    return maske[y0:y0 + yukseklik, x0:x0 + genislik].copy()


def zemin_ve_mevcut_engel(model: YOLO, bgr: np.ndarray, conf: float) -> tuple[np.ndarray, np.ndarray]:
    """Uretim letterbox yoluyla Navitas zemin ve mevcut engel maskelerini al."""
    tuval, kucuk, icerik = _preprocess(bgr)
    yan = tuval.shape[0]
    sonuc = model.predict(kucuk, imgsz=kucuk.shape[0], conf=conf, verbose=False)
    maskeler = get_masks(sonuc, yan, yan, sinif_idler=(0, 1))
    maskeler = _maskeleri_icerige_kirp(maskeler, icerik)
    return alani_kirp(maskeler[0], icerik), alani_kirp(maskeler[1], icerik)


def arac_maskesi(model: YOLO, bgr: np.ndarray, conf: float, imgsz: int) -> np.ndarray:
    """Araclari ENGEL maskesine ekle. Kahin: DOTA OBB (COCO seg DEGIL).

    S1 / ARCHITECT_PLAN K-6 olcumu: ayni hava fotografinda COCO 2 arac, DOTA OBB
    93 arac buluyor. Bulunamayan her arac, `yolo_etiketi()`'nin tam-kare zemin
    dikdortgeni altinda kalip ZEMIN etiketi aliyordu -- yani model araclarin
    ustunden gecmeyi ogreniyordu.

    OBB olmayan bir model verilirse eski COCO yolu kullanilir (geriye uyum) ama
    cagirici UYARILIR: sessizce kotu veri uretmektense gurultulu olmak yeglenir.
    """
    if obb_modeli_mi(model):
        return obb_arac_maskesi(bgr, model, conf=conf, imgsz=max(bgr.shape[:2]))
    # Uyari kare basina degil, model YUKLENIRKEN bir kez basilir (main icinde).
    return coco_arac_maskesi(bgr, model, conf, imgsz, get_masks)


def hedef_maskesi_yukle(hedef_dizini: Path | None, kaynak: Path, sekil: tuple[int, int]) -> np.ndarray:
    """Istege bagli hedef maskesini ayni kare boyutunda yukle.

    Hedef kaynagi verilmezse bos maske doner. Bu kanca class-2'yi uretim
    verisinden uydurmadan, disaridan dogrulanmis bir maske ile eklemek icindir.
    """
    yukseklik, genislik = sekil
    bos = np.zeros((yukseklik, genislik), dtype=np.uint8)
    if hedef_dizini is None:
        return bos
    for uzanti in MASKE_UZANTILARI:
        aday = hedef_dizini / f"{kaynak.stem}{uzanti}"
        if aday.is_file():
            gri = cv2.imread(str(aday), cv2.IMREAD_GRAYSCALE)
            if gri is None:
                raise OSError(f"Hedef maskesi okunamadi: {aday}")
            if gri.shape != (yukseklik, genislik):
                raise ValueError(f"Hedef maskesi boyutu farkli: {aday} ({gri.shape} != {sekil})")
            return (gri > 127).astype(np.uint8)
    return bos


def eliptik_cekirdek(yaricap: int) -> np.ndarray:
    """Piksel yaricapi sifir olsa bile geceli bir morfoloji cekirdegi ver."""
    yaricap = max(0, int(yaricap))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * yaricap + 1, 2 * yaricap + 1))


def uygun_zemin(zemin: np.ndarray, korunan: np.ndarray, kenar_pay: int, golge_pay: int) -> np.ndarray:
    """Yapistirma merkezlerini sadece zeminin ve engelden uzak golge alaninin icinde tut."""
    zemin = (zemin > 0).astype(np.uint8)
    if kenar_pay:
        zemin = cv2.erode(zemin, eliptik_cekirdek(kenar_pay))
    korunan = (korunan > 0).astype(np.uint8)
    if golge_pay:
        korunan = cv2.dilate(korunan, eliptik_cekirdek(golge_pay))
    return (zemin & (1 - korunan)).astype(np.uint8)


def rastgele_nokta(maske: np.ndarray, rng: random.Random) -> tuple[int, int] | None:
    """Ikili maskeden esit olasilikli bir (x,y) merkezi sec."""
    ys, xs = np.nonzero(maske)
    if len(xs) == 0:
        return None
    i = rng.randrange(len(xs))
    return int(xs[i]), int(ys[i])


def rgba_oku(yol: Path) -> np.ndarray | None:
    """Doku bankasindan yalniz alfa kanalli, gorunur bir enkaz kesiti oku."""
    rgba = cv2.imread(str(yol), cv2.IMREAD_UNCHANGED)
    if rgba is None or rgba.ndim != 3 or rgba.shape[2] != 4:
        return None
    if int((rgba[:, :, 3] > 0).sum()) < 12:
        return None
    return rgba


def moloz_yapistir(
    tuval: np.ndarray,
    kimlik: np.ndarray,
    zemin: np.ndarray,
    korunan: np.ndarray,
    asetler: list[Path],
    yapistir: Callable,
    rng: random.Random,
    adet: int,
    olcek_min: float,
    olcek_max: float,
    kenar_pay: int,
    golge_pay: int,
    min_alan: int,
) -> tuple[np.ndarray, int]:
    """Her molozu arac/engel disindaki zemine etiketli olarak yapistir.

    ``yapistir`` hem goruntu hem kimlik haritasini yerinde degistirdigi icin her
    deneme once kopyada yapilir. Cok kucuk/etiketlenemeyen bir parca varsa
    goruntuye de alinmaz; etiketsiz moloz olusmaz.
    """
    sonraki_kimlik = int(kimlik.max()) + 1
    basarili = 0
    etkin_korunan = (korunan > 0).astype(np.uint8)

    for _ in range(adet):
        izin = uygun_zemin(zemin, etkin_korunan, kenar_pay, golge_pay)
        merkez = rastgele_nokta(izin, rng)
        if merkez is None:
            break
        rgba = None
        for _deneme in range(12):
            rgba = rgba_oku(rng.choice(asetler))
            if rgba is not None:
                break
        if rgba is None:
            break

        deneme_tuval = tuval.copy()
        deneme_kimlik = kimlik.copy()
        yapistir(
            deneme_tuval, deneme_kimlik, rgba, merkez[0], merkez[1],
            rng.uniform(olcek_min, olcek_max), rng.uniform(0.0, 360.0), rng,
            kimlik_no=sonraki_kimlik, isik=(0.09, 0.07), sinir=izin,
        )
        yeni = (deneme_kimlik == sonraki_kimlik).astype(np.uint8)
        if int(yeni.sum()) < min_alan:
            continue
        if np.any(yeni & korunan):
            raise RuntimeError("Moloz korunan piksele tasacak sekilde etiketlendi")

        tuval[:] = deneme_tuval
        kimlik[:] = deneme_kimlik
        etkin_korunan = np.maximum(etkin_korunan, yeni)
        sonraki_kimlik += 1
        basarili += 1
    return etkin_korunan, basarili


def arena_icerik_ve_mpp(sekil: tuple[int, int]) -> tuple[tuple[int, int, int, int], float]:
    """Arena kutusunu KARAR YOLUNUN icerik kutusuyla ayni tanimla kur.

    NEDEN TAM KARE, ICTEGET KARE DEGIL (T45): karar yolu icerik kutusunu
    ARENA sanar — `serit_no()` seritleri icerik GENISLIGINI ucе bolerek uretir
    ve `_preprocess` icerik olarak GORUNTUNUN TAMAMINI dondurur. Onceki surum
    arenayi ictegs kareye kuruyordu; 1024x576 bir karede iki tanim asla
    ortusmuyordu ve kompozit kareler `UC_BANT_TEMAS_YOK` ile reddediliyordu:

        _preprocess icerik : (0, 224, 1024, 576) -> serit sinirlari [341, 682]
        eski arena ROI     : (224, 0,  576, 576) -> serit sinirlari [416, 608]

    Kompozit kumenin isi karar mantigini SINAMAKTIR; bu yuzden karar yolunun
    varsayimina uymak zorundadir. Arenanin gercekte kare olmasi, kameranin onu
    16:9 kadraja tam oturtamayacagi anlamina gelir — bu ayri ve daha buyuk bir
    acik sorudur (TASK_QUEUE T50), burada kapatilmaz.

    Ham karelerde irtifa/FOV yoktur; dolayisiyla mpp bir kamera olcumu DEGILDIR.
    `arena.HTAB` kare GENISLIGINE eslenir ve bu varsayim manifeste yazilir.
    """
    yukseklik, genislik = map(int, sekil)
    if yukseklik < 1 or genislik < 1:
        raise ValueError("Arena icerigi icin bos goruntu boyutu")
    return (0, 0, genislik, yukseklik), float(HTAB / genislik)


def arena_serit_haritasi(
    sekil: tuple[int, int], icerik: tuple[int, int, int, int]
) -> np.ndarray:
    """Her pikselin seridini yalniz `serit_no()` otoritesinden turet."""
    yukseklik, genislik = map(int, sekil)
    x0, y0, icerik_w, icerik_h = map(int, icerik)
    harita = np.zeros((yukseklik, genislik), dtype=np.uint8)
    if icerik_w <= 0 or icerik_h <= 0:
        return harita
    x_etiketleri = np.array(
        [serit_no(x, x0, icerik_w) for x in range(x0, x0 + icerik_w)],
        dtype=np.uint8,
    )
    harita[y0:y0 + icerik_h, x0:x0 + icerik_w] = x_etiketleri[None, :]
    return harita


def _dikey_en_guvenli_yol(
    dt_px: np.ndarray,
    gecilebilir: np.ndarray,
    icerik: tuple[int, int, int, int],
) -> list[tuple[int, int]] | None:
    """Ust ve alt uc bantlari arasinda asagi-yukari donmeyen bir omurga bul.

    Dinamik programlama her satirda en fazla bir piksel yana gider. Boylece bir
    koridor yatay karar bandini iki kez kesip sahte dorduncu kapi uretemez.
    Skor, yolun en dar noktasindaki acikligi maksimize eder.
    """
    x0, y0, genislik, yukseklik = map(int, icerik)
    pay = hedef_bant_yuksekligi(yukseklik)
    ust_satirlar = range(y0, min(y0 + pay, y0 + yukseklik))
    alt_satirlar = range(max(y0, y0 + yukseklik - pay), y0 + yukseklik)
    ust = max(ust_satirlar, key=lambda y: (int(gecilebilir[y].sum()), -y))
    alt = max(alt_satirlar, key=lambda y: (int(gecilebilir[y].sum()), y))
    if ust >= alt or not gecilebilir[ust].any() or not gecilebilir[alt].any():
        return None

    genislik_tam = dt_px.shape[1]
    gecersiz = np.float32(-1.0e20)
    onceki = np.full(genislik_tam, gecersiz, dtype=np.float32)
    onceki[gecilebilir[alt] > 0] = dt_px[alt, gecilebilir[alt] > 0]
    ebeveyn = np.full((alt - ust + 1, genislik_tam), -1, dtype=np.int32)
    kaymalar = np.array([1, 0, -1], dtype=np.int32)

    for y in range(alt - 1, ust - 1, -1):
        adaylar = np.stack((
            np.r_[onceki[1:], gecersiz],
            onceki,
            np.r_[gecersiz, onceki[:-1]],
        ))
        secim = np.argmax(adaylar, axis=0)
        en_iyi = adaylar[secim, np.arange(genislik_tam)]
        simdiki = np.minimum(en_iyi, dt_px[y])
        simdiki[gecilebilir[y] == 0] = gecersiz
        ebeveyn[y - ust] = np.arange(genislik_tam, dtype=np.int32) + kaymalar[secim]
        onceki = simdiki

    if float(onceki.max()) < 0.0:
        return None
    x = int(np.argmax(onceki))
    yol: list[tuple[int, int]] = []
    for y in range(ust, alt + 1):
        yol.append((x, y))
        if y < alt:
            x = int(ebeveyn[y - ust, x])
            if not (x0 <= x < x0 + genislik):
                return None
    return yol


def _bagimsiz_merkez_haritalari(
    serit_maske: np.ndarray,
    korunan: np.ndarray,
    mpp: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Rota kodunu cagirmadan fiziksel merkez acikligini olc.

    Serit duvari icin robot yaricapi, gercek engel icin ayni yaricapa ek olarak
    algi payi aranir. Boylece beklenen acik serit `rota_bul` sonucundan secilmez.
    """
    olc = olcek_px(mpp)
    serit_dt = cv2.distanceTransform(
        (serit_maske > 0).astype(np.uint8), cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    engel_bos = (np.asarray(korunan) == 0).astype(np.uint8)
    engel_dt = cv2.distanceTransform(
        engel_bos, cv2.DIST_L2, cv2.DIST_MASK_PRECISE)
    uygun = (
        (serit_dt >= float(olc["r_gerekli_px"])) &
        (engel_dt >= float(olc["r_gerekli_px"] + olc["algi_payi_px"]))
    ).astype(np.uint8)
    skor = np.minimum(serit_dt, engel_dt).astype(np.float32)
    return skor, uygun


def _orta_kapi_yolu(
    skor: np.ndarray,
    uygun: np.ndarray,
    icerik: tuple[int, int, int, int],
) -> list[tuple[int, int]] | None:
    """Uc koridorun orta karar kesitinde tek ve temiz bir gecit kur."""
    x0, y0, genislik, yukseklik = map(int, icerik)
    pay = hedef_bant_yuksekligi(yukseklik)
    orta = y0 + yukseklik // 2
    ust = max(y0, orta - pay // 2)
    alt = min(y0 + yukseklik, ust + pay)
    if alt <= ust:
        return None
    return _dikey_en_guvenli_yol(
        skor, uygun, (x0, ust, genislik, alt - ust))


def _hedef_kutusunu_kur(
    yol: list[tuple[int, int]],
    acik_serit: int,
    serit_haritasi: np.ndarray,
    korunan: np.ndarray,
    bariyer: np.ndarray,
    icerik: tuple[int, int, int, int],
    mpp: float,
) -> tuple[np.ndarray, tuple[int, int, int, int]] | None:
    """Acik koridorun hedef ucuna 2 m x 2 m H brandasi maskesi koy."""
    x0, y0, genislik, yukseklik = map(int, icerik)
    kenar = max(1, int(round(ARENA_HEDEF_KENAR_M / mpp)))
    pay = hedef_bant_yuksekligi(yukseklik)
    # 🔴 T173 (D-322): pad ESKIDEN bandin ORTASINA konuyordu
    # (`merkez_y = y0 + pay // 2`). 576 px karede bant ~46 px, 2 m pad ~41 px
    # -> ust pay 3 PIKSEL. Olculdu: uretilen dokuz karenin DOKUZUNDA da
    # `hedef_kutu` y = 3, yani kirmizi H kare kenarina yapisik ve kesik
    # gorunuyordu (kullanici bunu fark etti). Pad artik bandin ALT sinirina
    # oturur: hedef ucu DEGISMEZ (rota yine bantta biter) ama branda TAMAMEN
    # gorunur ve kareden en az yarim pad kadar iceridedir.
    merkez_y = y0 + pay
    # Pad bandin ALTINA kendi boyu kadar sarkabilir; hedef ucunda olmasi
    # yeterlidir, bandin ICINE SIGMASI sart degildir.
    alt_sinir = y0 + pay + kenar
    aday_xler = [x for x, y in yol if y < y0 + pay]
    if not aday_xler:
        aday_xler = [yol[0][0]]

    # T173 (D-322): YATAY PAY. Acik koridor kenar seritteyse rotanin ucu kare
    # kenarina dayanir ve 2 m'lik branda cerceveye yapisik cikiyordu (olculdu:
    # x = 10 ve 14 px). Pad en az YARIM PAD kadar iceride durur; bu, pad'i
    # koridordan cikarmaz, yalnizca cerceveden ayirir.
    yatay_pay = kenar // 2
    for merkez_x in aday_xler:
        sol = int(merkez_x - kenar // 2)
        # Cerceveden ayir: koridor kenarda olsa bile pad iceride kalsin.
        sol = max(x0 + yatay_pay, min(sol, x0 + genislik - kenar - yatay_pay))
        ust = int(merkez_y - kenar // 2)
        sag, alt = sol + kenar, ust + kenar
        if sol < x0 or sag > x0 + genislik or ust < y0 or alt > alt_sinir:
            continue
        if alt > y0 + yukseklik:
            continue
        bolge_serit = serit_haritasi[ust:alt, sol:sag]
        if bolge_serit.size == 0 or not np.all(bolge_serit == acik_serit):
            continue
        if np.any(korunan[ust:alt, sol:sag]) or np.any(bariyer[ust:alt, sol:sag]):
            continue
        hedef = np.zeros_like(korunan, dtype=np.uint8)
        hedef[ust:alt, sol:sag] = 1
        return hedef, (sol, ust, kenar, kenar)
    return None


def arena_geometrisi_uret(
    korunan: np.ndarray,
    rng: random.Random,
    *,
    icerik: tuple[int, int, int, int],
    mpp: float,
    acik_serit: int | None = None,
    harici_hedef: np.ndarray | None = None,
) -> ArenaGeometrisi | None:
    """DOTA/v21 engellerinden kacan tek acik ve iki kapali koridor kur.

    Acik serit, `rota_bul` sonucuna bakilarak secilmez. Once C-uzayinda uc bant
    arasinda baglanti kurabilen seritler bulunur; deterministik RNG bunlardan
    birini secer. `rota_bul` daha sonra yalniz kabul kapisi olarak calisir.
    """
    korunan = (np.asarray(korunan) > 0).astype(np.uint8)
    seritler = arena_serit_haritasi(korunan.shape, icerik)
    serit_no_listesi = sorted(int(s) for s in np.unique(seritler) if int(s) > 0)
    if len(serit_no_listesi) != 3:
        return None

    olc = olcek_px(mpp)
    merkez_gerekli = float(olc["r_gerekli_px"])
    # Kapinin karar uzayinda en az 2*r genis kalmasi icin zemin tupu 4*r capli
    # kurulur. Tum degerler costmap fizik sozlesmesinden gelir.
    koridor_yaricap = int(np.ceil(2.0 * merkez_gerekli))
    zemin = np.zeros_like(korunan)
    yollar: dict[int, list[tuple[int, int]]] = {}
    guvenli_seritler: list[int] = []
    x0, y0, genislik, yukseklik = map(int, icerik)
    pay = hedef_bant_yuksekligi(yukseklik)

    for serit in serit_no_listesi:
        serit_maske = (seritler == serit).astype(np.uint8)
        # OpenCV distanceTransform goruntu disini sifir saymaz. Icerigin dis
        # kenarlarini acikca kapatmazsak dis seritlerin "en guvenli" omurgasi
        # tuval kenarina yapisir ve 2 m hedef kutusu cerceve disina tasar.
        serit_maske[:, x0] = 0
        serit_maske[:, x0 + genislik - 1] = 0
        merkez_skor, merkez_uygun = _bagimsiz_merkez_haritalari(
            serit_maske, korunan, mpp)
        tam_yol = _dikey_en_guvenli_yol(merkez_skor, merkez_uygun, icerik)
        orta_yol = _orta_kapi_yolu(merkez_skor, merkez_uygun, icerik)
        if orta_yol is None:
            return None
        if tam_yol is not None:
            guvenli_seritler.append(serit)
            yol = tam_yol
        else:
            # Kapali serit icin tam gecis gerekmez; fakat karar kesitinde temiz,
            # tek bir kapi gerekir. Orta omurga ust/alt tohumlara uzatilir ve
            # moloz daha sonra bu yerel tupu gercek alfa maskesiyle kesecektir.
            ilk_x, ilk_y = orta_yol[0]
            son_x, son_y = orta_yol[-1]
            yol = [
                (ilk_x, y0 + pay // 2),
                (ilk_x, ilk_y),
                *orta_yol[1:-1],
                (son_x, son_y),
                (son_x, y0 + yukseklik - 1 - pay // 2),
            ]
        yollar[serit] = yol
        tup = np.zeros_like(zemin)
        cv2.polylines(tup, [np.asarray(yol, dtype=np.int32)], False, 1,
                      thickness=2 * koridor_yaricap + 1, lineType=cv2.LINE_8)
        tup[seritler != serit] = 0
        zemin = np.maximum(zemin, tup)

    if harici_hedef is not None and np.any(harici_hedef):
        ys, xs = np.nonzero(harici_hedef)
        hedef_seritler = set(int(s) for s in seritler[ys, xs] if int(s) > 0)
        if (len(hedef_seritler) != 1 or int(ys.min()) < y0 or
                int(ys.max()) >= y0 + pay):
            return None
        secilen = next(iter(hedef_seritler))
        if not np.all(seritler[ys, xs] == secilen):
            return None
    elif acik_serit is not None:
        secilen = int(acik_serit)
    elif guvenli_seritler:
        secilen = int(rng.choice(guvenli_seritler))
    else:
        return None
    if secilen not in guvenli_seritler:
        return None

    kapali = [serit for serit in serit_no_listesi if serit != secilen]
    bariyer = np.zeros_like(korunan)
    bariyerler: list[dict] = []
    bariyer_y0 = y0 + 2 * pay
    bariyer_y1 = min(y0 + yukseklik, bariyer_y0 + pay)
    for serit in kapali:
        parca = (seritler == serit).astype(np.uint8)
        parca[:bariyer_y0] = 0
        parca[bariyer_y1:] = 0
        bariyer = np.maximum(bariyer, parca)
        ys, xs = np.nonzero(parca)
        bariyerler.append({
            "serit": serit,
            "kutu": [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1),
                     int(ys.max() - ys.min() + 1)],
        })

    pozitif_bariyer = (seritler == secilen).astype(np.uint8)
    pozitif_bariyer[:bariyer_y0] = 0
    pozitif_bariyer[bariyer_y1:] = 0

    if harici_hedef is not None and np.any(harici_hedef):
        hedef = (harici_hedef > 0).astype(np.uint8)
        if np.any(hedef & korunan) or np.any(hedef & bariyer):
            return None
        ys, xs = np.nonzero(hedef)
        hedef_kutu = (int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1),
                      int(ys.max() - ys.min() + 1))
    else:
        hedef_sonucu = _hedef_kutusunu_kur(
            yollar[secilen], secilen, seritler, korunan, bariyer, icerik, mpp)
        if hedef_sonucu is None:
            return None
        hedef, hedef_kutu = hedef_sonucu

    return ArenaGeometrisi(
        zemin=zemin, bariyer=bariyer, pozitif_bariyer=pozitif_bariyer,
        hedef=hedef, acik_serit=secilen, kapali_seritler=kapali,
        bariyerler=bariyerler, icerik=icerik, mpp=mpp,
        hedef_kutu=hedef_kutu,
    )


def _pencerede_ust_alt_bileseni(
    maske: np.ndarray,
    pencere: tuple[int, int, int, int],
) -> np.ndarray | None:
    """Pencerenin ust ve alt kenarina degen ortak bileseni tam tuvalde don."""
    x0, y0, genislik, yukseklik = map(int, pencere)
    yerel = (maske[y0:y0 + yukseklik, x0:x0 + genislik] > 0).astype(np.uint8)
    if yerel.size == 0 or not yerel[0].any() or not yerel[-1].any():
        return None
    _n, etiket = cv2.connectedComponents(yerel, connectivity=8)
    ust = set(int(v) for v in np.unique(etiket[0]) if int(v) > 0)
    alt = set(int(v) for v in np.unique(etiket[-1]) if int(v) > 0)
    ortak = sorted(ust & alt)
    if not ortak:
        return None
    secilen = max(ortak, key=lambda deger: int((etiket == deger).sum()))
    sonuc = np.zeros_like(maske, dtype=np.uint8)
    sonuc[y0:y0 + yukseklik, x0:x0 + genislik] = (etiket == secilen)
    return sonuc


def arena_molozunu_yapistir(
    tuval: np.ndarray,
    kimlik: np.ndarray,
    bariyer: np.ndarray,
    asetler: list[Path],
    yapistir: Callable,
    rng: random.Random,
    ilk_kimlik: int,
    *,
    koridor: np.ndarray,
    korunan: np.ndarray,
    min_poligon_alan: float,
) -> ArenaBariyerSonucu | None:
    """Gercek RGBA pikselleriyle yerel koridoru atomik olarak kes.

    Planlanan dikdortgen yalniz yapistirma siniridir. Engel yer gercegi, alfa
    esigini gecip kimlik haritasina gercekten yazilan piksellerden uretilir.
    """
    bariyer = (np.asarray(bariyer) > 0).astype(np.uint8)
    koridor = (np.asarray(koridor) > 0).astype(np.uint8)
    korunan = (np.asarray(korunan) > 0).astype(np.uint8)
    ys, xs = np.nonzero(bariyer)
    if xs.size == 0 or not asetler:
        return None
    sol, sag = int(xs.min()), int(xs.max()) + 1
    ust, alt = int(ys.min()), int(ys.max()) + 1
    bant_yuksekligi = alt - ust
    pencere_ust = max(0, ust - bant_yuksekligi)
    pencere_alt = min(bariyer.shape[0], alt + bant_yuksekligi)
    pencere = (sol, pencere_ust, sag - sol, pencere_alt - pencere_ust)
    izin = ((bariyer > 0) & (korunan == 0)).astype(np.uint8)
    baslangic_serbest = ((koridor > 0) & (korunan == 0)).astype(np.uint8)
    if _pencerede_ust_alt_bileseni(baslangic_serbest, pencere) is None:
        return None

    calisma_tuval = tuval.copy()
    calisma_kimlik = kimlik.copy()
    gercek = np.zeros_like(bariyer, dtype=np.uint8)
    parca_sayisi = 0
    merkez_adimi = max(1, bant_yuksekligi)
    merkez_sayisi = max(1, int(np.ceil((sag - sol) / merkez_adimi)))
    maks_deneme = merkez_sayisi * merkez_sayisi

    for _deneme in range(maks_deneme):
        kalan = ((baslangic_serbest > 0) & (gercek == 0)).astype(np.uint8)
        bilesen = _pencerede_ust_alt_bileseni(kalan, pencere)
        if bilesen is None:
            ys_g, xs_g = np.nonzero(gercek)
            if xs_g.size == 0:
                return None
            tuval[:] = calisma_tuval
            kimlik[:] = calisma_kimlik
            return ArenaBariyerSonucu(
                maske=gercek,
                kutu=(int(xs_g.min()), int(ys_g.min()),
                      int(xs_g.max() - xs_g.min() + 1),
                      int(ys_g.max() - ys_g.min() + 1)),
                pencere=pencere,
                parca_sayisi=parca_sayisi,
            )

        gecit = ((bilesen > 0) & (izin > 0)).astype(np.uint8)
        satirlar = [(int(gecit[y].sum()), y) for y in range(ust, alt)
                    if int(gecit[y].sum()) > 0]
        if not satirlar:
            return None
        _dar_genislik, merkez_y = min(satirlar)
        gecit_x = np.flatnonzero(gecit[merkez_y])
        merkez_x = int(np.rint(float(np.median(gecit_x))))

        rgba = None
        # Mevcut ureticinin bozuk aset toleransi korunur; sessiz bos bariyer yoktur.
        for _ in range(12):
            rgba = rgba_oku(rng.choice(asetler))
            if rgba is not None:
                break
        if rgba is None:
            continue
        olcek = bant_yuksekligi / max(1, min(rgba.shape[:2]))
        kimlik_no = ilk_kimlik + parca_sayisi
        deneme_tuval = calisma_tuval.copy()
        deneme_kimlik = calisma_kimlik.copy()
        yapistir(
            deneme_tuval, deneme_kimlik, rgba, merkez_x, merkez_y, olcek,
            rng.uniform(-10.0, 10.0), rng, kimlik_no=kimlik_no,
            isik=None, sinir=izin,
        )
        yeni = (deneme_kimlik == kimlik_no).astype(np.uint8)
        degisen = np.any(deneme_tuval != calisma_tuval, axis=2)
        if (int(yeni.sum()) < float(min_poligon_alan) or
                np.any(yeni & (1 - izin)) or np.any(degisen & (izin == 0))):
            continue
        calisma_tuval = deneme_tuval
        calisma_kimlik = deneme_kimlik
        gercek = np.maximum(gercek, yeni)
        parca_sayisi += 1

    if _pencerede_ust_alt_bileseni(
            ((baslangic_serbest > 0) & (gercek == 0)).astype(np.uint8),
            pencere) is None:
        ys_g, xs_g = np.nonzero(gercek)
        if xs_g.size:
            tuval[:] = calisma_tuval
            kimlik[:] = calisma_kimlik
            return ArenaBariyerSonucu(
                maske=gercek,
                kutu=(int(xs_g.min()), int(ys_g.min()),
                      int(xs_g.max() - xs_g.min() + 1),
                      int(ys_g.max() - ys_g.min() + 1)),
                pencere=pencere,
                parca_sayisi=parca_sayisi,
            )
    return None


def arena_hedefini_ciz(tuval: np.ndarray, hedef_kutu: tuple[int, int, int, int]) -> None:
    """Class-2 maskesiyle ayni 2 m kareye kirmizi branda ve beyaz H ciz."""
    x0, y0, genislik, yukseklik = map(int, hedef_kutu)
    cv2.rectangle(tuval, (x0, y0), (x0 + genislik - 1, y0 + yukseklik - 1),
                  (0, 0, 255), thickness=-1)
    kalinlik = max(1, min(genislik, yukseklik) // 8)
    sol = x0 + genislik // 3
    sag = x0 + (2 * genislik) // 3
    ust = y0 + yukseklik // 5
    alt = y0 + (4 * yukseklik) // 5
    orta = y0 + yukseklik // 2
    cv2.line(tuval, (sol, ust), (sol, alt), (255, 255, 255), kalinlik)
    cv2.line(tuval, (sag, ust), (sag, alt), (255, 255, 255), kalinlik)
    cv2.line(tuval, (sol, orta), (sag, orta), (255, 255, 255), kalinlik)


def poligon_satirlari(sinif: int, maske: np.ndarray, min_alan: float) -> list[str]:
    """Ikili maskeyi YOLO-seg normalize dis poligon satirlarina cevir."""
    yukseklik, genislik = maske.shape[:2]
    konturlar, _ = cv2.findContours((maske > 0).astype(np.uint8), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    satirlar: list[str] = []
    for kontur in konturlar:
        if cv2.contourArea(kontur) < min_alan:
            continue
        cevre = cv2.arcLength(kontur, True)
        sade = cv2.approxPolyDP(kontur, max(0.75, cevre * 0.002), True).reshape(-1, 2)
        if len(sade) < 3:
            continue
        sade[:, 0] = np.clip(sade[:, 0], 0, genislik - 1)
        sade[:, 1] = np.clip(sade[:, 1], 0, yukseklik - 1)
        koordinatlar = " ".join(f"{x / genislik:.6f} {y / yukseklik:.6f}" for x, y in sade)
        satirlar.append(f"{sinif} {koordinatlar}")
    return satirlar


def yolo_etiketi(engel: np.ndarray, hedef: np.ndarray, min_alan: float) -> str:
    """Zemini tum cerceve olarak, engel/hedefi ayri sinif olarak yaz.

    DIKKAT — bu fonksiyon S1'in neden tikayici oldugunu aciklar: zemin daima
    TAM KARE dikdortgendir ve engel/hedef poligonlari onun USTUNE binir. Yani
    `engel` maskesine girmeyen her nesne otomatik olarak ZEMIN etiketi alir.
    Sessiz kayip yoktur -- yanlis etiket vardir. Bu yuzden `arac_maskesi()`
    kahini dogru olmak ZORUNDADIR.
    """
    satirlar = [f"{ZEMIN} 0.000000 0.000000 1.000000 0.000000 1.000000 1.000000 0.000000 1.000000"]
    satirlar.extend(poligon_satirlari(ENGEL, engel, min_alan))
    satirlar.extend(poligon_satirlari(HEDEF, hedef, min_alan))
    return "\n".join(satirlar) + "\n"


def arena_yolo_etiketi(
    zemin: np.ndarray, engel: np.ndarray, hedef: np.ndarray, min_alan: float
) -> str:
    """Arena kipinde kontrollu zemin maskesini de gercek poligon olarak yaz.

    Rastgele kipin tam-kare zemin sozlesmesi `yolo_etiketi()` icinde aynen kalir.
    """
    satirlar: list[str] = []
    satirlar.extend(poligon_satirlari(ZEMIN, zemin, min_alan))
    satirlar.extend(poligon_satirlari(ENGEL, engel, min_alan))
    satirlar.extend(poligon_satirlari(HEDEF, hedef, min_alan))
    return "\n".join(satirlar) + "\n"


def yolo_sinif_maskesi(
    etiket: str, sekil: tuple[int, int], sinif: int
) -> np.ndarray:
    """Yazilacak YOLO poligonunu geri rasterize ederek serilestirmeyi denetle."""
    yukseklik, genislik = map(int, sekil)
    maske = np.zeros((yukseklik, genislik), dtype=np.uint8)
    for satir in etiket.splitlines():
        alanlar = satir.split()
        if not alanlar or int(alanlar[0]) != int(sinif):
            continue
        sayilar = np.asarray([float(deger) for deger in alanlar[1:]], dtype=np.float64)
        if sayilar.size < 6 or sayilar.size % 2:
            continue
        noktalar = sayilar.reshape(-1, 2)
        noktalar[:, 0] = np.clip(np.rint(noktalar[:, 0] * genislik), 0, genislik - 1)
        noktalar[:, 1] = np.clip(np.rint(noktalar[:, 1] * yukseklik), 0, yukseklik - 1)
        cv2.fillPoly(maske, [noktalar.astype(np.int32)], 1, lineType=cv2.LINE_8)
    return maske


def arena_rotasi(
    zemin: np.ndarray,
    mevcut_engel: np.ndarray,
    arac: np.ndarray,
    bariyer: np.ndarray,
    *,
    mpp: float,
    icerik: tuple[int, int, int, int],
) -> dict:
    """Egitim siniflarini costmap katman sozlesmesiyle rota kapisina ver."""
    katmanlar = costmap_katmanlari(
        zemin,
        np.maximum((mevcut_engel > 0).astype(np.uint8),
                   (bariyer > 0).astype(np.uint8)),
        (arac > 0).astype(np.uint8),
    )
    return rota_bul(
        katmanlar, mpp=mpp, plan=False, icerik=icerik,
        yol_sinif_idler=COSTMAP_YOL_KATMANLARI,
        engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,
    )


def bolum_sec(kaynak: Path, cesit: int, tohum: int, val_oran: float) -> str:
    """Calismalar arasinda degismeyen train/val secimi yap — KAYNAK BAZINDA.

    🔴 T122 (D-233) — DUZELTILEN KUSUR: anahtar eskiden `cesit`i de iceriyordu
    (`f"{kaynak}:{cesit}:{tohum}"`). Ayni kaynak karenin varyantlari boylece
    FARKLI bolumlere dusuyordu. Olculdu (`dataset/copy_paste_gercek/
    manifest.json`): 56 kaynagin 41'i HEM train HEM val'de; dogrulama
    kumesinin 55/55'inin (%100) kaynagi egitimde de var — TEMIZ dogrulama
    ornegi SIFIR. Varyantlar ayni kareden uretildigi icin piksel farki
    %0,1-0,4'tur (olculdu), yani val fiilen egitim verisinin ikizidir ve o
    bilesenin val metrigi EZBERI olcer.

    Kural: bolum YALNIZ kaynak (ve tohum) ile belirlenir — bir kaynagin TUM
    varyantlari AYNI bolume gider (grup ayrimi). Kilit:
    `tests/test_t122_bolum_ayrimi.py`.

    ⚠ MEVCUT KUMELER BU DUZELTMEDEN ONCE URETILDI ve kirliligi tasimaya devam
    eder; yeniden uretim MIMARIN karari (veri sozlesmesi degisikligi).
    """
    anahtar = f"{kaynak.as_posix()}:{tohum}".encode("utf-8")
    deger = int.from_bytes(hashlib.sha256(anahtar).digest()[:8], "big") / 2**64
    return "val" if deger < val_oran else "train"


def dosya_koku(kaynak_kok: Path, kaynak: Path, cesit: int) -> str:
    """Ayni isimli farkli alt dizin kaynaklarini carpmayan dosya adi ver."""
    goreli = kaynak.relative_to(kaynak_kok).with_suffix("").as_posix()
    temiz = "_".join(parca for parca in goreli.replace("/", "_").split() if parca)
    temiz = "".join(ch if ch.isalnum() or ch in "_-" else "_" for ch in temiz)
    return f"{temiz}_cp_{cesit:02d}"


def veri_yaml_yaz(cikti: Path, hedef_uretildi: bool) -> None:
    """YOLO veri seti sozlesmesini ciktiyla birlikte sakla.

    Sinif adlari `codes/sinif_semasi.py`'den gelir; burada ciplak sayi yazilmaz
    (CLAUDE.md madde 16).

    ⚠ Sinif SAYISI veriye baglidir, sabit degildir. Rastgele kipte harici hedef
    yoksa sinif 2 bulunmaz; arena kipi ise prosedurel H uretir. Yine de gercekte
    iki sinifli ciktiya `nc=3` demek veri karisiminda YOLO nc uyusmazligi verir.
    Bu yuzden ilan edilen sinif kumesi gercek etiketlerle ayni olmak zorundadir.

    Iki sinifli kipte `traversable/blocked` adlari kullanilir; boylece mevcut
    RescueNet + sentetik arena karisimiyla ad duzeyinde de uyumludur.
    """
    if hedef_uretildi:
        adlar = sorted(EGITIM_SINIF_ADLARI.items())
    else:
        adlar = sorted(IKI_SINIF_ADLARI.items())
    satirlar = ["path: .", "train: images/train", "val: images/val", "names:"]
    satirlar += [f"  {kimlik}: {ad}" for kimlik, ad in adlar]
    atomik_bytes_yaz(cikti / "data.yaml", ("\n".join(satirlar) + "\n").encode("utf-8"))


def manifest_yaz(cikti: Path, parametreler: dict, ozetler: list[UretimOzeti]) -> None:
    """Her sentezlenen sahnenin kaynak ve koruma istatistiklerini kaydet."""
    veri = {"parametreler": parametreler, "ornekler": [asdict(ozet) for ozet in ozetler]}
    atomik_bytes_yaz(cikti / "manifest.json", json.dumps(veri, ensure_ascii=False, indent=2).encode("utf-8"))


def argumanlar() -> argparse.Namespace:
    """Komut satiri ayarlarini tanimla."""
    ayrac = argparse.ArgumentParser(description="Gercek zemine etiketli moloz copy-paste uygula")
    ayrac.add_argument("--arena", action="store_true",
                        help="T40: kontrollu uc-koridor arena yer gercegi uret")
    ayrac.add_argument("--girdi", type=Path, default=KOK / "data" / "raw_frames")
    ayrac.add_argument("--cikti", type=Path,
                        help="Varsayilan: rastgele kipte dataset/copy_paste_moloz, arena kipinde data/arena_kompozit")
    ayrac.add_argument("--aset-dizini", type=Path,
                        default=Path(r"O:\navitas-local-train\doku_bankasi\enkaz"))
    ayrac.add_argument("--yapistir-kaynak", type=Path,
                        default=Path(r"O:\navitas-local-train\51_sentetik_arena.py"))
    ayrac.add_argument("--zemin-model", type=Path,
                        help="Varsayilan: rastgele kipte v20, arena kipinde etkin uretim modeli v21")
    # S1: varsayilan DOTA OBB. COCO seg nadir bakista araclarin ~%98'ini kaciriyor
    # ve kacan her arac ZEMIN etiketleniyordu (olculdu: COCO 2 / DOTA 93 arac).
    ayrac.add_argument("--arac-model", type=Path, default=KOK / "yolov8m-obb.pt")
    ayrac.add_argument("--hedef-maske-dizini", type=Path,
                        help="Istege bagli, kaynak stem'iyle ayni adli ikili class-2 maskeleri")
    ayrac.add_argument("--zemin-conf", type=float, default=0.25)
    ayrac.add_argument("--arac-conf", type=float, default=0.25)
    ayrac.add_argument("--arac-imgsz", type=int, default=640)
    ayrac.add_argument("--kopya", type=int, default=1, help="Her ham kare icin varyasyon sayisi")
    ayrac.add_argument("--moloz-min", type=int, default=1)
    ayrac.add_argument("--moloz-max", type=int, default=3)
    ayrac.add_argument("--olcek-min", type=float, default=0.20)
    ayrac.add_argument("--olcek-max", type=float, default=0.55)
    ayrac.add_argument("--kenar-pay", type=int, default=18,
                        help="Zemin sinirindan moloz merkezine en az piksel pay")
    ayrac.add_argument("--golge-pay", type=int, default=96,
                        help="Arac/engel cevresinde golge tasmasina karsi piksel tampon")
    ayrac.add_argument("--min-poligon-alan", type=float, default=16.0)
    ayrac.add_argument("--jpeg-kalite", type=int, default=95)
    ayrac.add_argument("--val-oran", type=float, default=0.15)
    ayrac.add_argument("--tohum", type=int, default=20260802)
    ayrac.add_argument("--sinir", type=int, help="Yalniz ilk N ham kareyi isle (smoke test icin)")
    ayrac.add_argument("--temizle", action="store_true", help="Yalniz secilen cikti veri setini silip yeniden uret")
    return ayrac.parse_args()


def kip_varsayilanlarini_uygula(args: argparse.Namespace) -> argparse.Namespace:
    """Yeni arena kipini eklerken eski rastgele kipin varsayilanlarini koru."""
    if args.cikti is None:
        args.cikti = (KOK / "data" / "arena_kompozit" if args.arena
                      else KOK / "dataset" / "copy_paste_moloz")
    if args.zemin_model is None:
        # Arena v21'i kullanir: bu etkin sistem modelidir ve ilk gercek karede
        # v20'nin 0 px urettigi olculmustur. Bu yine model basarimi kaniti DEGILDIR.
        surum = "navitas_seg_v21_best.pt" if args.arena else "navitas_seg_v20_best.pt"
        args.zemin_model = KOK / "models" / surum
    return args


def ayarlari_dogrula(args: argparse.Namespace) -> None:
    """Hatalari pahali model yuklemeden once acikca bildir."""
    if args.kopya < 1 or args.moloz_min < 1 or args.moloz_max < args.moloz_min:
        raise ValueError("--kopya >= 1 ve 1 <= --moloz-min <= --moloz-max olmali")
    if not 0 < args.olcek_min <= args.olcek_max:
        raise ValueError("0 < --olcek-min <= --olcek-max olmali")
    if not 0.0 <= args.val_oran < 1.0:
        raise ValueError("--val-oran [0,1) araliginda olmali")
    if not 1 <= args.jpeg_kalite <= 100 or args.arac_imgsz < 32:
        raise ValueError("JPEG kalitesi 1..100 ve --arac-imgsz >= 32 olmali")
    for yol in (args.zemin_model, args.arac_model):
        if not yol.is_file():
            raise FileNotFoundError(f"Model bulunamadi: {yol}")
    if args.hedef_maske_dizini is not None and not args.hedef_maske_dizini.is_dir():
        raise FileNotFoundError(f"Hedef maske dizini bulunamadi: {args.hedef_maske_dizini}")


def arena_cesidi_uret(
    args: argparse.Namespace,
    cikti: Path,
    kaynak: Path,
    bgr: np.ndarray,
    mevcut_engel: np.ndarray,
    arac: np.ndarray,
    harici_hedef: np.ndarray,
    asetler: list[Path],
    yapistir: Callable,
    cesit: int,
) -> UretimOzeti:
    """Bir kontrollu arena ornegini kapilariyla birlikte atomik olarak yaz."""
    goreli_kaynak = kaynak.relative_to(args.girdi).as_posix()
    temel = dict(
        kaynak=goreli_kaynak, cikti=None, bolum=None, durum="ATLANDI",
        arac_px=int(arac.sum()), mevcut_engel_px=int(mevcut_engel.sum()),
        hedef_px=int(harici_hedef.sum()),
    )
    rng = random.Random(f"{args.tohum}:{kaynak.as_posix()}:{cesit}")
    icerik, mpp = arena_icerik_ve_mpp(bgr.shape[:2])
    korunan = np.maximum(mevcut_engel, arac)
    geometri = arena_geometrisi_uret(
        korunan, rng, icerik=icerik, mpp=mpp,
        harici_hedef=harici_hedef if np.any(harici_hedef) else None,
    )
    if geometri is None:
        return UretimOzeti(**temel, sebep="arena_c_uzayi_veya_hedef_uygunsuz")

    tuval = bgr.copy()
    kimlik = np.zeros(bgr.shape[:2], dtype=np.int32)
    seritler = arena_serit_haritasi(bgr.shape[:2], geometri.icerik)
    moloz_sayisi = 0
    sonraki_kimlik = 1
    gercek_bariyer = np.zeros(bgr.shape[:2], dtype=np.uint8)
    bariyer_kayitlari: list[dict] = []
    yapistirma_korunani = np.maximum(korunan, geometri.hedef)
    for serit in geometri.kapali_seritler:
        parca = ((geometri.bariyer > 0) & (seritler == serit)).astype(np.uint8)
        koridor = ((geometri.zemin > 0) & (seritler == serit)).astype(np.uint8)
        sonuc = arena_molozunu_yapistir(
            tuval, kimlik, parca, asetler, yapistir, rng, sonraki_kimlik,
            koridor=koridor, korunan=yapistirma_korunani,
            min_poligon_alan=args.min_poligon_alan,
        )
        if sonuc is None:
            return UretimOzeti(
                **temel, sebep=f"arena_gercek_bariyer_kesmiyor_serit_{serit}")
        gercek_bariyer = np.maximum(gercek_bariyer, sonuc.maske)
        moloz_sayisi += sonuc.parca_sayisi
        bariyer_kayitlari.append({
            "serit": serit,
            "kutu": list(sonuc.kutu),
            "pencere": list(sonuc.pencere),
            "gercek_px": int(sonuc.maske.sum()),
            "parca_sayisi": sonuc.parca_sayisi,
            "yerel_once_bagli": True,
            "yerel_sonra_bagli": False,
        })
        sonraki_kimlik = int(kimlik.max()) + 1

    # Pozitif kontrol de hayali bir dikdortgen degil, ayni RGBA mekanizmasinin
    # acik seritte uretebildigi exact engel maskesidir. Ana JPEG'e yazilmaz.
    pozitif_tuval = bgr.copy()
    pozitif_kimlik = np.zeros(bgr.shape[:2], dtype=np.int32)
    pozitif_rng = random.Random(
        f"{args.tohum}:{kaynak.as_posix()}:{cesit}:pozitif")
    pozitif_koridor = (
        (geometri.zemin > 0) & (seritler == geometri.acik_serit)).astype(np.uint8)
    pozitif_sonuc = arena_molozunu_yapistir(
        pozitif_tuval, pozitif_kimlik, geometri.pozitif_bariyer,
        asetler, yapistir, pozitif_rng, 1,
        koridor=pozitif_koridor, korunan=yapistirma_korunani,
        min_poligon_alan=args.min_poligon_alan,
    )
    if pozitif_sonuc is None:
        return UretimOzeti(**temel, sebep="pozitif_gercek_bariyer_kesmiyor")
    pozitif_bariyer = pozitif_sonuc.maske

    if not np.any(harici_hedef):
        arena_hedefini_ciz(tuval, geometri.hedef_kutu)

    engel = np.maximum(np.maximum(mevcut_engel, arac), gercek_bariyer)
    if np.any(geometri.hedef & engel):
        return UretimOzeti(**temel, sebep="uretilen_hedef_engel_cakismasi")
    etiket = arena_yolo_etiketi(
        geometri.zemin, engel, geometri.hedef, args.min_poligon_alan)
    yazilan_engel = yolo_sinif_maskesi(etiket, bgr.shape[:2], ENGEL)
    arac_px = int((arac > 0).sum())
    kapsanan_px = int(((arac > 0) & (yazilan_engel > 0)).sum())
    if arac_px == 0:
        # 🔴 T174 (D-325): burada kare REDDEDILIYORDU. Oysa bu bir ETIKET
        # BUTUNLUGU kapisidir: "DOTA'nin gordugu her arac pikseli, yazilan
        # ENGEL etiketinin altinda mi?" ARACSIZ bir karede dogrulanacak bir
        # sey YOKTUR; kod "olculemedi"yi "dustu" sayiyor ve KIRSAL (aracsiz)
        # her kareyi eliyordu.
        #
        # OLCULDU: 36 gunduz DJI karesinin 72 denemesinden 44'u (%61) TAM BU
        # SATIRDA dustu. Kompozit kumenin otopark zeminine bagimli kalmasinin
        # sebebi buydu — otoparkta hep arac vardi.
        #
        # Kontrol ATLANIR ama SESSIZCE DEGIL: manifeste `arac_kapsama: null`
        # ve `arac_kapsama_durumu: "UYGULANAMAZ_ARAC_YOK"` yazilir. Asil
        # etiket butunlugu BARIYER kapsama kapisindan olculur (asagida) ve o
        # kapi AYNEN yururlukte kalir — yani "yokluk GECTI degildir" ilkesi
        # korunur, yalnizca UYGULANAMAZ olan ile DUSEN ayrilir.
        arac_kapsama = None
    else:
        arac_kapsama = kapsanan_px / arac_px
        if arac_kapsama < ARENA_ARAC_KAPSAMA_ESIGI:
            return UretimOzeti(
                **temel,
                sebep=f"yazilan_arac_kapsama_dusuk:{arac_kapsama:.6f}",
            )
    bariyer_px = int(gercek_bariyer.sum())
    bariyer_kapsanan_px = int(((gercek_bariyer > 0) & (yazilan_engel > 0)).sum())
    bariyer_kapsama = bariyer_kapsanan_px / bariyer_px if bariyer_px else 0.0
    if bariyer_px == 0 or bariyer_kapsama < ARENA_ARAC_KAPSAMA_ESIGI:
        return UretimOzeti(
            **temel,
            sebep=f"yazilan_bariyer_kapsama_dusuk:{bariyer_kapsama:.6f}",
        )

    bolum = bolum_sec(kaynak, cesit, args.tohum, args.val_oran)
    ad = dosya_koku(args.girdi, kaynak, cesit)
    resim_yol = cikti / "images" / bolum / f"{ad}.jpg"
    etiket_yol = cikti / "labels" / bolum / f"{ad}.txt"
    maske_dizini = cikti / "masks" / bolum
    maske_dizini.mkdir(parents=True, exist_ok=True)
    maske_yollari = {
        "zemin": maske_dizini / f"{ad}_zemin.png",
        "engel": maske_dizini / f"{ad}_engel.png",
        "hedef": maske_dizini / f"{ad}_hedef.png",
        "arac": maske_dizini / f"{ad}_arac.png",
        "bariyer": maske_dizini / f"{ad}_bariyer.png",
        "pozitif_bariyer": maske_dizini / f"{ad}_pozitif_bariyer.png",
    }
    atomik_jpeg_yaz(resim_yol, tuval, args.jpeg_kalite)
    atomik_bytes_yaz(etiket_yol, etiket.encode("utf-8"))
    atomik_png_yaz(maske_yollari["zemin"], geometri.zemin)
    atomik_png_yaz(maske_yollari["engel"], engel)
    atomik_png_yaz(maske_yollari["hedef"], geometri.hedef)
    atomik_png_yaz(maske_yollari["arac"], arac)
    atomik_png_yaz(maske_yollari["bariyer"], gercek_bariyer)
    atomik_png_yaz(maske_yollari["pozitif_bariyer"], pozitif_bariyer)

    arena_detayi = {
        "beklenen_durum": "ACIK",
        "beklenti_kaynagi": "serit_no_ve_bagimsiz_geometri",
        "acik_serit": geometri.acik_serit,
        "kapali_seritler": geometri.kapali_seritler,
        "bariyerler": bariyer_kayitlari,
        "icerik": list(geometri.icerik),
        "mpp": geometri.mpp,
        "olcek_kaynagi": ARENA_OLCEK_KAYNAGI,
        "hedef_kaynagi": ("harici_maske" if np.any(harici_hedef)
                           else "prosedurel_2m_kirmizi_H"),
        "hedef_kutu": list(geometri.hedef_kutu),
        "arac_kapsanan_px": kapsanan_px,
        "arac_kapsama": (None if arac_kapsama is None
                         else round(arac_kapsama, 6)),
        "arac_kapsama_durumu": ("UYGULANAMAZ_ARAC_YOK" if arac_kapsama is None
                                else "OLCULDU"),
        "bariyer_kapsanan_px": bariyer_kapsanan_px,
        "bariyer_kapsama": round(bariyer_kapsama, 6),
        "pozitif_bariyer": {
            "kutu": list(pozitif_sonuc.kutu),
            "pencere": list(pozitif_sonuc.pencere),
            "gercek_px": int(pozitif_bariyer.sum()),
            "parca_sayisi": pozitif_sonuc.parca_sayisi,
            "yerel_once_bagli": True,
            "yerel_sonra_bagli": False,
        },
        "maskeler": {ad: yol.relative_to(cikti).as_posix()
                     for ad, yol in maske_yollari.items()},
        "etiket": etiket_yol.relative_to(cikti).as_posix(),
    }
    return UretimOzeti(
        kaynak=goreli_kaynak,
        cikti=resim_yol.relative_to(cikti).as_posix(),
        bolum=bolum,
        durum="YAZILDI",
        moloz_sayisi=moloz_sayisi,
        arac_px=arac_px,
        mevcut_engel_px=int(mevcut_engel.sum()),
        hedef_px=int(geometri.hedef.sum()),
        arena=arena_detayi,
    )


def main() -> int:
    """Moloz sentezini calistir; arac ustune yazma sozlesmesini uygula."""
    args = kip_varsayilanlarini_uygula(argumanlar())
    try:
        ayarlari_dogrula(args)
        kaynaklar = goruntuleri_bul(args.girdi)
        asetler = asetleri_bul(args.aset_dizini)
        yapistir = yapistir_yukle(args.yapistir_kaynak)
        cikti = guvenli_cikti_kok(args.cikti, args.temizle)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    if args.sinir is not None:
        kaynaklar = kaynaklar[:max(0, args.sinir)]
    if not kaynaklar:
        print("HATA: Islenecek ham kare bulunamadi", file=sys.stderr)
        return 2

    print(f"Modeller yukleniyor: zemin={args.zemin_model.name}, arac={args.arac_model.name}")
    zemin_model = YOLO(str(args.zemin_model), task="segment")
    # S1: arac modeline gorev ZORLANMAZ. Eskiden burada task="segment" yaziliydi;
    # bir DOTA OBB modeline segment gorevi dayatmak, `obb` sonuc alanini bos
    # birakip SESSIZCE sifir arac uretebilirdi. Gorev agirlik dosyasindan okunur.
    arac_model = YOLO(str(args.arac_model))
    arac_obb_mi = obb_modeli_mi(arac_model)
    print(f"  arac kahini: {'DOTA-OBB' if arac_obb_mi else 'COCO-seg'} "
          f"(task={getattr(arac_model, 'task', '?')})")
    if not arac_obb_mi:
        print("UYARI: arac modeli OBB DEGIL. Nadir bakista COCO segmentasyonu "
              "araclarin buyuk cogunlugunu kaciriyor (olculdu: ayni fotografta "
              "COCO 2 / DOTA 93 arac) ve kacan her arac ZEMIN etiketi aliyor. "
              "Uretilen veri seti bu haliyle modele araclarin ustunden gecmeyi "
               "ogretir. yolov8m-obb.pt kullanin.", file=sys.stderr)
        if args.arena:
            print("HATA: Arena kipi DOTA-OBB arac kahini olmadan veri uretmez.",
                  file=sys.stderr)
            return 2
    ozetler: list[UretimOzeti] = []

    for kaynak_sira, kaynak in enumerate(kaynaklar, start=1):
        bgr = cv2.imread(str(kaynak))
        if bgr is None:
            ozetler.append(UretimOzeti(kaynak.name, None, None, "ATLANDI", sebep="gorsel_okunamadi"))
            continue
        try:
            zemin, mevcut_engel = zemin_ve_mevcut_engel(zemin_model, bgr, args.zemin_conf)
            arac = arac_maskesi(arac_model, bgr, args.arac_conf, args.arac_imgsz)
            hedef = hedef_maskesi_yukle(args.hedef_maske_dizini, kaynak, bgr.shape[:2])
        except (OSError, ValueError, RuntimeError) as exc:
            ozetler.append(UretimOzeti(kaynak.name, None, None, "ATLANDI", sebep=str(exc)))
            continue

        if args.arena:
            for cesit in range(args.kopya):
                try:
                    ozetler.append(arena_cesidi_uret(
                        args, cikti, kaynak, bgr, mevcut_engel, arac, hedef,
                        asetler, yapistir, cesit,
                    ))
                except (OSError, RuntimeError, ValueError) as exc:
                    ozetler.append(UretimOzeti(
                        kaynak.relative_to(args.girdi).as_posix(), None, None,
                        "ATLANDI", arac_px=int(arac.sum()),
                        mevcut_engel_px=int(mevcut_engel.sum()),
                        hedef_px=int(hedef.sum()), sebep=str(exc),
                    ))
            yazilan_kaynak = sum(
                o.durum == "YAZILDI" and o.kaynak == kaynak.relative_to(args.girdi).as_posix()
                for o in ozetler)
            print(f"[{kaynak_sira}/{len(kaynaklar)}] {kaynak.name}: "
                  f"v21_engel={int(mevcut_engel.sum())} px, "
                  f"DOTA_arac={int(arac.sum())} px, arena_yazilan={yazilan_kaynak}")
            continue

        # Hedefi engel gibi etiketlemek yerine class-2 onceligi verilir. Hedef ile
        # arac cakisiyorsa kaynak geometrisi belirsizdir; o kare uretime alinmaz.
        ham_korunan = np.maximum(mevcut_engel, arac)
        if np.any(hedef & ham_korunan):
            ozetler.append(UretimOzeti(kaynak.name, None, None, "ATLANDI",
                                        arac_px=int(arac.sum()), mevcut_engel_px=int(mevcut_engel.sum()),
                                        hedef_px=int(hedef.sum()), sebep="hedef_engel_cakismasi"))
            continue
        ham_korunan = np.maximum(ham_korunan, hedef)

        for cesit in range(args.kopya):
            rng = random.Random(f"{args.tohum}:{kaynak.as_posix()}:{cesit}")
            tuval = bgr.copy()
            kimlik = np.zeros(bgr.shape[:2], dtype=np.int32)
            istenen_moloz = rng.randint(args.moloz_min, args.moloz_max)
            try:
                tum_engel, moloz_sayisi = moloz_yapistir(
                    tuval, kimlik, zemin, ham_korunan, asetler, yapistir, rng,
                    istenen_moloz, args.olcek_min, args.olcek_max, args.kenar_pay,
                    args.golge_pay, int(args.min_poligon_alan),
                )
            except RuntimeError as exc:
                ozetler.append(UretimOzeti(kaynak.name, None, None, "ATLANDI", sebep=str(exc)))
                continue
            if moloz_sayisi < args.moloz_min:
                ozetler.append(UretimOzeti(kaynak.name, None, None, "ATLANDI",
                                            arac_px=int(arac.sum()), mevcut_engel_px=int(mevcut_engel.sum()),
                                            hedef_px=int(hedef.sum()), sebep="yeterli_guvenli_zemin_yok"))
                continue

            # Yeni molozlar, mevcut engeller ve COCO araclari class-1'dir.
            engel = np.maximum(np.maximum(mevcut_engel, arac), (kimlik > 0).astype(np.uint8))
            engel = (engel & (1 - hedef)).astype(np.uint8)
            bolum = bolum_sec(kaynak, cesit, args.tohum, args.val_oran)
            ad = dosya_koku(args.girdi, kaynak, cesit)
            resim_yol = cikti / "images" / bolum / f"{ad}.jpg"
            etiket_yol = cikti / "labels" / bolum / f"{ad}.txt"
            atomik_jpeg_yaz(resim_yol, tuval, args.jpeg_kalite)
            atomik_bytes_yaz(etiket_yol, yolo_etiketi(engel, hedef, args.min_poligon_alan).encode("utf-8"))
            ozetler.append(UretimOzeti(
                kaynak=kaynak.relative_to(args.girdi).as_posix(),
                cikti=resim_yol.relative_to(cikti).as_posix(), bolum=bolum, durum="YAZILDI",
                moloz_sayisi=moloz_sayisi, arac_px=int(arac.sum()),
                mevcut_engel_px=int(mevcut_engel.sum()), hedef_px=int(hedef.sum()),
            ))
        print(f"[{kaynak_sira}/{len(kaynaklar)}] {kaynak.name}: "
              f"zemin={int(zemin.sum())} px, arac={int(arac.sum())} px")

    # Sinif kumesi GERCEKTEN uretilen etiketlerden turetilir, varsayilmaz.
    hedef_uretildi = any(ozet.hedef_px > 0 for ozet in ozetler)
    veri_yaml_yaz(cikti, hedef_uretildi)
    manifest_yaz(cikti, {
        # Siniflar sozlesme modulunden gelir; manifest ile veri seti asla ayrisamaz.
        "siniflar": {str(k): v for k, v in sorted(EGITIM_SINIF_ADLARI.items())},
        "kip": "arena" if args.arena else "rastgele",
        "zemin_tam_cerceve": not args.arena,
        "zemin_alti_engeller": True,
        "arac_ustu_yapistirma": False,
        "yapistir_kaynagi": str(args.yapistir_kaynak),
        # S1 izlenebilirligi: hangi KAHIN ile uretildigi kayda gecer. Bu alan
        # olmadan "bu veri COCO ile mi OBB ile mi uretildi" sorusu sonradan
        # cevaplanamaz -- ki S1'in tum meselesi tam olarak buydu.
        "zemin_model": str(args.zemin_model),
        "arac_model": str(args.arac_model),
        "arac_kahini": "DOTA-OBB" if arac_obb_mi else "COCO-seg (ESKI, ONERILMEZ)",
        "arac_conf": args.arac_conf, "zemin_conf": args.zemin_conf,
        "jpeg_kalite": args.jpeg_kalite,
        "hedef_sinifi_uretildi": hedef_uretildi,
        "girdi": str(args.girdi), "tohum": args.tohum,
        "arena_karar_mantigi_kaniti": bool(args.arena),
        "arena_model_basarimi_kaniti": False,
        "arena_domain_boslugu_kapandi": False,
        "arena_olcek_kaynagi": ARENA_OLCEK_KAYNAGI if args.arena else None,
    }, ozetler)
    yazilan = sum(ozet.durum == "YAZILDI" for ozet in ozetler)
    atlanan = sum(ozet.durum != "YAZILDI" for ozet in ozetler)
    print(f"TOPLAM: {yazilan} YOLO-seg ornegi yazildi, {atlanan} atlandi -> {cikti}")
    if yazilan == 0:
        print("HATA: Guvenli zemin bulunamadigi icin veri seti uretilmedi", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
