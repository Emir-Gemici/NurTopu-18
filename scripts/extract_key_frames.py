"""NEDEN: Drone videosundaki ardarda benzer kareler veri setini yapay olarak
buyutur ve gercek saha cesitliligini ezer. Bu betik tam goruntu karelerini
algisal hash ile eleyerek etiketleme icin izlenebilir ham kaynak olusturur.

Varsayilan olarak proje kokundeki dort 1024x576 drone videosunu tarar. Merkez
crop veya yeniden boyutlandirma yapmaz; her kaydedilen kare kaynak cozunurlugu
ile yazilir.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
VARSAYILAN_VIDEOLAR = (
    "WhatsApp Video 2026-07-30 at 11.44.03.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.23.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.39.mp4",
    "WhatsApp Video 2026-07-30 at 11.44.46.mp4",
)
VIDEO_UZANTILARI = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}


@dataclass
class KaynakOzeti:
    """Bir video icin tekrar uretilebilir cikarma sayilari."""

    kaynak: str
    fps: float
    taranan_kare: int = 0
    aday_kare: int = 0
    yakin_kopya: int = 0
    gecersiz_kare: int = 0
    yazilan_kare: int = 0


def hash_yardimcilari_yukle(kaynak: Path) -> tuple[Callable, Callable]:
    """53_drone_kare.py icindeki kanitlanmis ahash/farkli_mi'yi yukle.

    Dosya adi rakamla basladigi icin normal ``import`` kullanilamaz. Yardimci
    algoritmayi burada kopyalamamak, esik davranisinin doku-bankasi akisi ile
    ayni kalmasini saglar.
    """
    if not kaynak.is_file():
        raise FileNotFoundError(f"aHash kaynagi bulunamadi: {kaynak}")
    spec = importlib.util.spec_from_file_location("navitas_drone_hash", kaynak)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"aHash kaynagi yuklenemedi: {kaynak}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul.ahash, modul.farkli_mi


def guvenli_cikti_dizini(cikti: Path, temizle: bool) -> Path:
    """--temizle hedefini proje icindeki acik bir dizinle sinirla."""
    kok = KOK.resolve()
    hedef = cikti.resolve()
    try:
        hedef.relative_to(kok)
    except ValueError as exc:
        raise ValueError(f"Cikti proje disinda olamaz: {hedef}") from exc
    if hedef in {kok, (kok / "data").resolve()}:
        raise ValueError("--temizle proje koku veya data/ dizinini hedefleyemez")
    if temizle and hedef.exists():
        shutil.rmtree(hedef)
    hedef.mkdir(parents=True, exist_ok=True)
    return hedef


def temiz_ad(ad: str) -> str:
    """Kaynak adini Windows-guvenli, okunabilir bir klasor adina cevir."""
    sonuc = re.sub(r"[^a-z0-9]+", "_", ad.casefold()).strip("_")
    return sonuc or "kaynak"


def sonraki_sira(dizin: Path) -> int:
    """--temizle olmadan yeniden calismada var olan kareyi ezme."""
    en_buyuk = -1
    for yol in dizin.glob("frame_*.jpg"):
        eslesme = re.fullmatch(r"frame_(\d+)_\d+", yol.stem)
        if eslesme:
            en_buyuk = max(en_buyuk, int(eslesme.group(1)))
    return en_buyuk + 1


def atomik_jpeg_yaz(kare: np.ndarray, hedef: Path, kalite: int) -> None:
    """Kareyi gecici dosyaya yazip tek hamlede gorunur hale getir."""
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    try:
        basarili = cv2.imwrite(
            str(gecici), kare, [cv2.IMWRITE_JPEG_QUALITY, int(kalite)]
        )
        if not basarili:
            raise OSError(f"JPEG yazilamadi: {gecici}")
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()


def videolari_coz(girdiler: Iterable[str] | None) -> list[Path]:
    """Varsayilan dort videoyu veya kullanicinin verdigi dosya/dizinleri bul."""
    if not girdiler:
        return [KOK / ad for ad in VARSAYILAN_VIDEOLAR]

    videolar: list[Path] = []
    for metin in girdiler:
        yol = Path(metin).expanduser()
        if yol.is_dir():
            videolar.extend(sorted(p for p in yol.iterdir()
                                   if p.is_file() and p.suffix.lower() in VIDEO_UZANTILARI))
        else:
            videolar.append(yol)
    return videolar


def videodan_kare_cikar(
    video: Path,
    cikti_kok: Path,
    aralik: float,
    en_fazla: int,
    esik: float,
    kalite: int,
    ahash: Callable,
    farkli_mi: Callable,
    tum_gecmis: list[np.ndarray],
) -> tuple[KaynakOzeti, list[dict]]:
    """Bir videoyu tara; tam kareleri global aHash gecmisine gore yaz."""
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise OSError(f"Video acilamadi: {video}")

    fps = float(cap.get(cv2.CAP_PROP_FPS) or 24.0)
    adim = max(1, int(round(fps * aralik)))
    kaynak_dizin = cikti_kok / temiz_ad(video.stem)
    kaynak_dizin.mkdir(parents=True, exist_ok=True)
    sira = sonraki_sira(kaynak_dizin)
    ozet = KaynakOzeti(kaynak=video.name, fps=round(fps, 3))
    kayitlar: list[dict] = []
    kare_no = 0

    try:
        while ozet.yazilan_kare < en_fazla:
            if not cap.grab():
                break
            if kare_no % adim == 0:
                ozet.aday_kare += 1
                ok, kare = cap.retrieve()
                if not ok or kare is None or kare.size == 0:
                    ozet.gecersiz_kare += 1
                else:
                    karmasi = ahash(kare)
                    if not farkli_mi(karmasi, tum_gecmis, esik):
                        ozet.yakin_kopya += 1
                    else:
                        hedef = kaynak_dizin / f"frame_{sira + ozet.yazilan_kare:06d}_{kare_no:09d}.jpg"
                        atomik_jpeg_yaz(kare, hedef, kalite)
                        tum_gecmis.append(karmasi)
                        ozet.yazilan_kare += 1
                        kayitlar.append({
                            "kaynak": video.name,
                            "kare_no": kare_no,
                            "zaman_sn": round(kare_no / fps, 3),
                            "dosya": hedef.relative_to(cikti_kok).as_posix(),
                            "genislik": int(kare.shape[1]),
                            "yukseklik": int(kare.shape[0]),
                        })
            ozet.taranan_kare += 1
            kare_no += 1
    finally:
        cap.release()
    return ozet, kayitlar


def manifest_yaz(cikti_kok: Path, parametreler: dict, ozetler: list[KaynakOzeti], kayitlar: list[dict]) -> Path:
    """Cikarma kosullarini ve her tam-kare kaynagini atomik JSON ile kaydet."""
    hedef = cikti_kok / "manifest.json"
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    veri = {
        "parametreler": parametreler,
        "kaynaklar": [asdict(ozet) for ozet in ozetler],
        "kareler": kayitlar,
    }
    try:
        gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()
    return hedef


def argumanlar() -> argparse.Namespace:
    """Komut satiri arayuzunu olustur."""
    ayrac = argparse.ArgumentParser(description="Drone videosundan tam kare etiketleme kaynagi cikar")
    ayrac.add_argument("--girdi", nargs="*", help="Video dosyalari veya video dizinleri; verilmezse dort saha videosu")
    ayrac.add_argument("--cikti", type=Path, default=KOK / "data" / "raw_frames",
                        help="Karelerin yazilacagi dizin")
    ayrac.add_argument("--aralik", type=float, default=1.0,
                        help="Aday kare araligi saniye olarak (varsayilan: 1.0)")
    ayrac.add_argument("--en-fazla", type=int, default=400,
                        help="Her kaynak video icin yazilabilecek azami kare (varsayilan: 400)")
    ayrac.add_argument("--hash-esik", type=float, default=0.12,
                        help="53_drone_kare.py farkli_mi esigi (varsayilan: 0.12)")
    ayrac.add_argument("--kalite", type=int, default=95, help="JPEG kalitesi (varsayilan: 95)")
    ayrac.add_argument("--temizle", action="store_true",
                        help="Yalniz secilen cikti dizinini silip yeniden olustur")
    ayrac.add_argument("--hash-kaynak", type=Path,
                        default=Path(r"O:\navitas-local-train\53_drone_kare.py"),
                        help="ahash/farkli_mi'nin alinacagi mevcut betik")
    return ayrac.parse_args()


def main() -> int:
    """Kare cikarma isini calistir ve makine-okunur iz birak."""
    args = argumanlar()
    if args.aralik <= 0 or args.en_fazla <= 0:
        print("HATA: --aralik ve --en-fazla pozitif olmali", file=sys.stderr)
        return 2
    if not 0.0 <= args.hash_esik <= 1.0:
        print("HATA: --hash-esik 0..1 araliginda olmali", file=sys.stderr)
        return 2
    if not 1 <= args.kalite <= 100:
        print("HATA: --kalite 1..100 araliginda olmali", file=sys.stderr)
        return 2

    try:
        ahash, farkli_mi = hash_yardimcilari_yukle(args.hash_kaynak)
        cikti_kok = guvenli_cikti_dizini(args.cikti, args.temizle)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2

    videolar = videolari_coz(args.girdi)
    if not videolar:
        print("HATA: Islenecek video bulunamadi", file=sys.stderr)
        return 2

    tum_gecmis: list[np.ndarray] = []
    ozetler: list[KaynakOzeti] = []
    kayitlar: list[dict] = []
    for video in videolar:
        if not video.is_file():
            print(f"UYARI: kaynak bulunamadi, atlandi: {video}", file=sys.stderr)
            continue
        try:
            ozet, yeni_kayitlar = videodan_kare_cikar(
                video, cikti_kok, args.aralik, args.en_fazla, args.hash_esik,
                args.kalite, ahash, farkli_mi, tum_gecmis,
            )
        except OSError as exc:
            print(f"UYARI: {exc}", file=sys.stderr)
            continue
        ozetler.append(ozet)
        kayitlar.extend(yeni_kayitlar)
        print(f"{video.name}: {ozet.yazilan_kare} tam kare yazildi; "
              f"{ozet.yakin_kopya} yakin kopya elendi")

    if not ozetler:
        print("HATA: Hicbir kaynak acilamadi", file=sys.stderr)
        return 1
    manifest = manifest_yaz(
        cikti_kok,
        {"aralik_sn": args.aralik, "en_fazla_kaynak": args.en_fazla,
         "hash_esik": args.hash_esik, "jpeg_kalite": args.kalite,
         "tam_kare": True, "merkez_crop": False},
        ozetler, kayitlar,
    )
    toplam = sum(ozet.yazilan_kare for ozet in ozetler)
    print(f"TOPLAM: {toplam} tam kare -> {cikti_kok}")
    print(f"MANIFEST: {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
