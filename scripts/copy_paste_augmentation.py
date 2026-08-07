"""NEDEN: Gercek otopark zemini uzerine etiket maskesi bilinen moloz eklemek,
uretkenden piksel alip etiketsiz engel uretme hatasini onler. Yapistirma yalniz
zemin uzerinde yapilir; arac, mevcut engel ve hedef pikselleri korunur.

Etiket semantigi `codes/sinif_semasi.py`'den gelir: 0=zemin, 1=engel, 2=hedef.
Zemin satiri tam cercevedir; engeller ve hedefler onun ustunde ayri poligonlar
olarak yazilir. Boylece zemin poligonu engellerin altinda delik acmaz.

⚠ Ilan edilen SINIF SAYISI veriye baglidir: `--hedef-maske-dizini` verilmezse
hicbir etikette sinif 2 olusmaz ve `data.yaml` iki sinifli (traversable/blocked)
yazilir. Aksi halde bu veri seti 2 sinifli bir karisimla birlikte egitilemezdi.

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
if str(KODLAR) not in sys.path:
    sys.path.insert(0, str(KODLAR))

from arac_maskesi import coco_arac_maskesi, obb_arac_maskesi, obb_modeli_mi
from rpi_inference import _maskeleri_icerige_kirp, _preprocess, get_masks
from sinif_semasi import (EGITIM_SINIF_ADLARI, ENGEL, HEDEF, IKI_SINIF_ADLARI,
                          ZEMIN)


GORUNTU_UZANTILARI = {".jpg", ".jpeg", ".png"}
MASKE_UZANTILARI = (".png", ".jpg", ".jpeg", ".bmp")


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


def modulu_yukle(yol: Path, ad: str):
    """Rakamla baslayan mevcut betigi kopyalamadan yuklemek icin yardimci."""
    if not yol.is_file():
        raise FileNotFoundError(f"Kaynak betik bulunamadi: {yol}")
    spec = importlib.util.spec_from_file_location(ad, yol)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Kaynak betik yuklenemedi: {yol}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
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


def bolum_sec(kaynak: Path, cesit: int, tohum: int, val_oran: float) -> str:
    """Calismalar arasinda degismeyen train/val secimi yap."""
    anahtar = f"{kaynak.as_posix()}:{cesit}:{tohum}".encode("utf-8")
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

    ⚠ Sinif SAYISI veriye baglidir, sabit degildir. `--hedef-maske-dizini`
    verilmediginde hicbir etikette sinif 2 bulunmaz; yine de `nc=3` ilan etmek
    bu veri setini 2 sinifli bir karisimla (ornegin `karisim_arena.yaml`) BIRLIKTE
    EGITILEMEZ hale getirir -- YOLO nc uyusmazligi verir. Bu yuzden ilan edilen
    sinif kumesi, gercekten uretilen etiketlerle ayni olmak zorundadir.

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
    ayrac.add_argument("--girdi", type=Path, default=KOK / "data" / "raw_frames")
    ayrac.add_argument("--cikti", type=Path, default=KOK / "dataset" / "copy_paste_moloz")
    ayrac.add_argument("--aset-dizini", type=Path,
                        default=Path(r"O:\navitas-local-train\doku_bankasi\enkaz"))
    ayrac.add_argument("--yapistir-kaynak", type=Path,
                        default=Path(r"O:\navitas-local-train\51_sentetik_arena.py"))
    ayrac.add_argument("--zemin-model", type=Path, default=KOK / "models" / "navitas_seg_v20_best.pt")
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


def main() -> int:
    """Moloz sentezini calistir; arac ustune yazma sozlesmesini uygula."""
    args = argumanlar()
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
        "zemin_tam_cerceve": True,
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
        "hedef_sinifi_uretildi": hedef_uretildi,
        "girdi": str(args.girdi), "tohum": args.tohum,
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
