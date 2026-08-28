"""NEDEN: Onceki FPS sayilari tahmindi. Bu betik Jetson'da kare okuma,
cikarim, rpi_inference maskesi ve costmap Katman-A kararini AYNI dongude
olcer; .pt, ONNX ve Jetson'da derlenmis TensorRT FP16 sonuclarini ayri p50/p95
ile raporlar.

TensorRT .engine dosyasi bu PC'de uretilmez. ``scripts/export_tensorrt.py``
ile ONNX'i PC'de uretin, engine'i Jetson Orin NX'te derleyin, sonra bu betigi
Jetson'da calistirin.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import sys
import time
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO


KOK = Path(__file__).resolve().parents[1]
KODLAR = KOK / "codes"
if str(KODLAR) not in sys.path:
    sys.path.insert(0, str(KODLAR))

from costmap_path_finder import rota_bul
from rpi_inference import (
    INFER_SIZE,
    _arguman_ayristirici,
    _maskeleri_icerige_kirp,
    _preprocess,
    get_masks,
    model_kayit_dogrula,          # T203/D-354: defter kapisi
)


GORUNTU_UZANTILARI = {".jpg", ".jpeg", ".png", ".bmp"}
VIDEO_UZANTILARI = {".mp4", ".mov", ".avi", ".mkv", ".m4v"}
JETSON_MANIFEST_ADI = "jetson_derleme_manifest.json"


def _manifest_ve_model_dizini(kok: Path = KOK) -> tuple[dict[str, Any], Path]:
    """Repo ve Jetson paket topolojisinde ayni uretim manifestini oku."""
    adaylar = (
        kok / "models" / JETSON_MANIFEST_ADI,
        kok / "jetson_paket" / "models" / JETSON_MANIFEST_ADI,
    )
    bulunan = [yol for yol in adaylar if yol.is_file()]
    if len(bulunan) != 1:
        raise RuntimeError(
            "Jetson uretim manifesti tekil olmali: "
            + ", ".join(str(yol) for yol in bulunan)
        )
    try:
        veri = json.loads(bulunan[0].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Jetson uretim manifesti okunamadi: {bulunan[0]}") from exc
    if not isinstance(veri, dict):
        raise RuntimeError("Jetson uretim manifesti JSON nesnesi olmali")
    return veri, bulunan[0].parent


def _manifest_model_adi(veri: dict[str, Any], alan: str, uzanti: str) -> str:
    """Manifest model adini yol kacisina izin vermeden dogrula."""
    deger = veri.get(alan)
    if not isinstance(deger, str) or not deger.strip():
        raise RuntimeError(f"Jetson uretim manifestinde `{alan}` yok/gecersiz")
    ad = deger.strip()
    if Path(ad).name != ad or Path(ad).suffix.lower() != uzanti:
        raise RuntimeError(f"Jetson uretim manifestinde `{alan}` guvensiz/gecersiz: {ad!r}")
    return ad


def _uretim_varsayilanlari(kok: Path = KOK) -> dict[str, Any]:
    """FPS varsayilanlarini manifest ve uretim yorumlayicisindan turet."""
    veri, model_dizini = _manifest_ve_model_dizini(kok)
    pt = model_dizini / _manifest_model_adi(veri, "asil_model_pt", ".pt")
    onnx = model_dizini / _manifest_model_adi(veri, "asil_model", ".onnx")

    engine_adayi = onnx.with_suffix(".engine")
    engine = engine_adayi if engine_adayi.is_file() else None

    manifest_boyutlari = veri.get("imgsz")
    if (
        not isinstance(manifest_boyutlari, list)
        or not manifest_boyutlari
        or any(isinstance(x, bool) or not isinstance(x, int) or x < 32 or x % 32
               for x in manifest_boyutlari)
    ):
        raise RuntimeError("Jetson uretim manifestinde `imgsz` yok/gecersiz")
    imgsz = list(dict.fromkeys([*manifest_boyutlari, INFER_SIZE]))

    conf = _arguman_ayristirici().get_default("conf")
    if isinstance(conf, bool) or not isinstance(conf, (int, float)) or not 0.0 < float(conf) <= 1.0:
        raise RuntimeError("rpi_inference uretim `conf` varsayilani yok/gecersiz")
    return {"pt": pt, "onnx": onnx, "engine": engine, "imgsz": imgsz, "conf": float(conf)}


class KareAkisi:
    """Disk goruntusu veya videodan kare okur; EOF'ta basa sarar."""

    def __init__(self, kaynak: Path, video_adim: int = 1):
        self.kaynak = kaynak
        self.video_adim = max(1, int(video_adim))
        self.gorseller: list[Path] = []
        self.indis = 0
        self.cap: cv2.VideoCapture | None = None
        if kaynak.is_dir():
            self.gorseller = sorted(
                p for p in kaynak.rglob("*") if p.is_file() and p.suffix.lower() in GORUNTU_UZANTILARI
            )
        elif kaynak.is_file() and kaynak.suffix.lower() in GORUNTU_UZANTILARI:
            self.gorseller = [kaynak]
        elif kaynak.is_file() and kaynak.suffix.lower() in VIDEO_UZANTILARI:
            self.cap = cv2.VideoCapture(str(kaynak))
            if not self.cap.isOpened():
                raise OSError(f"Video acilamadi: {kaynak}")
        else:
            raise FileNotFoundError(f"Kare kaynagi bulunamadi/desteklenmiyor: {kaynak}")
        if not self.gorseller and self.cap is None:
            raise FileNotFoundError(f"Kare kaynaginda gorsel yok: {kaynak}")

    def sifirla(self) -> None:
        """Her model/kare boyutu ayni kaynak sirasiyla olculsun."""
        self.indis = 0
        if self.cap is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def al(self) -> tuple[np.ndarray, float, str]:
        """Bir BGR kare, disk okuma suresi ve kaynak adi don."""
        t0 = time.perf_counter()
        if self.cap is None:
            for _ in range(len(self.gorseller)):
                yol = self.gorseller[self.indis % len(self.gorseller)]
                self.indis += 1
                kare = cv2.imread(str(yol))
                if kare is not None:
                    return kare, (time.perf_counter() - t0) * 1000, yol.name
            raise OSError("Kare kaynagindaki hicbir gorsel okunamadi")

        for _ in range(2):
            kare = None
            for _ in range(self.video_adim):
                ok, kare = self.cap.read()
                if not ok:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    break
            if kare is not None:
                return kare, (time.perf_counter() - t0) * 1000, self.kaynak.name
        raise OSError(f"Videodan kare okunamadi: {self.kaynak}")

    def kapat(self) -> None:
        """Video yakalamasini serbest birak."""
        if self.cap is not None:
            self.cap.release()


def atomik_yaz(hedef: Path, metin: str) -> None:
    """JSON ve raporu yarim dosya gorunmeden yaz."""
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    try:
        gecici.write_text(metin, encoding="utf-8")
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()


def yuzdelik(degerler: list[float], oran: float) -> float | None:
    """Bos listeyi bozmayacak sekilde p50/p95 hesapla."""
    return round(float(np.percentile(degerler, oran)), 3) if degerler else None


def model_turu(yol: Path) -> str:
    """Dosya uzantisindan rapor etiketi uret."""
    return {".pt": "PyTorch", ".onnx": "ONNX", ".engine": "TensorRT FP16"}.get(
        yol.suffix.lower(), yol.suffix.lstrip(".").upper() or "BILINMEYEN"
    )


def ortam_bilgisi() -> dict[str, Any]:
    """Olcumu calistiran Jetson/PC baglamini kaydet."""
    bilgi: dict[str, Any] = {
        "zaman": datetime.now().isoformat(timespec="seconds"),
        "platform": platform.platform(), "python": sys.version.split()[0],
    }
    try:
        import torch

        bilgi["torch"] = torch.__version__
        bilgi["cuda_var"] = bool(torch.cuda.is_available())
        bilgi["cuda_adi"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception as exc:
        bilgi["torch_hata"] = str(exc)
    return bilgi


def tek_kare_isle(model: YOLO, bgr: np.ndarray, imgsz: int, conf: float, cihaz: str | None) -> dict[str, Any]:
    """Kare -> cikarim -> get_masks -> rota_bul(plan=False) gercek zinciri."""
    t0 = time.perf_counter()
    tuval, kucuk_512, icerik = _preprocess(bgr)
    giris = kucuk_512 if imgsz == kucuk_512.shape[0] else cv2.resize(
        tuval, (imgsz, imgsz), interpolation=cv2.INTER_AREA
    )
    tahmin = {"imgsz": imgsz, "conf": conf, "verbose": False}
    if cihaz:
        tahmin["device"] = cihaz
    sonuc = model.predict(giris, **tahmin)
    cikarim_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    yan = tuval.shape[0]
    maskeler = get_masks(sonuc, yan, yan, sinif_idler=(0, 1))
    maskeler = _maskeleri_icerige_kirp(maskeler, icerik)
    maske_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    rota = rota_bul(
        maskeler, mpp=None, plan=False, gorsel_cikti=False, icerik=icerik)
    katman_a_ms = (time.perf_counter() - t0) * 1000
    return {"cikarim_ms": cikarim_ms, "maske_ms": maske_ms,
            "katman_a_ms": katman_a_ms, "rota_durumu": rota["durum"],
            "yol_no": rota["yol_no"]}


def vaka_calistir(ad: str, yol: Path, imgsz: int, akis: KareAkisi, isinma: int,
                  tekrar: int, conf: float, cihaz: str | None,
                  kayit_dogrulamasiz: bool = False) -> dict[str, Any]:
    """Bir model+cozunurluk kombinasyonunu isitir ve p50/p95 olcer."""
    temel = {"ad": ad, "tur": model_turu(yol), "model": str(yol), "imgsz": imgsz}
    if not yol.is_file():
        return temel | {"durum": "ATLANDI", "sebep": "model_dosyasi_yok"}
    # Ultralytics eksik backend gorunce pip'i otomatik calistirmayi dener. FPS
    # olcumu ag bagimliligina donusmesin; Jetson hazir degilse acikca atla.
    if yol.suffix.lower() == ".onnx" and importlib.util.find_spec("onnxruntime") is None:
        return temel | {"durum": "ATLANDI", "sebep": "onnxruntime_yok"}
    if yol.suffix.lower() == ".engine" and importlib.util.find_spec("tensorrt") is None:
        return temel | {"durum": "ATLANDI", "sebep": "tensorrt_yok"}
    # 🔴 T203 · D-354: KAYIT DEFTERI KAPISI. Bu betik defter zincirini HIC
    # cagirmiyordu (grep = 0) ama kilavuz SS6C/G6-1 "load_model +
    # model_kayit_dogrula zincirinden gecer" DIYORDU. Yani saha defterine
    # "dogrulandi" yaziliyor, dogrulama KOSMUYORDU: kayitsiz ya da YANLIS bir
    # agirlik "OK" damgasiyla raporlanabiliyordu. 30 Eylul testi TEK ATIS
    # oldugu icin bu, dogrulanmamis bir modelle sahaya cikmak demektir.
    # FAIL-CLOSED: uyusmazlikta OLCUM YAPILMAZ. Bilerek gecmek icin
    # `--kayit-dogrulamasiz` gerekir ve verdikt ozete YAZILIR.
    kayit_detay = None
    if not kayit_dogrulamasiz:
        try:
            uyumlu, kayit_detay = model_kayit_dogrula(yol, calisan_imgsz=imgsz)
        except Exception as exc:                 # defter okunamadi = DOGRULANMADI
            return temel | {"durum": "HATA",
                            "sebep": f"kayit_defteri_okunamadi: {exc}",
                            "kayit": {"durum": "OKUNAMADI"}}
        if not uyumlu:
            return temel | {"durum": "HATA",
                            "sebep": "kayit_defteri_uyusmazligi (fail-closed; "
                                     "bilerek gecmek icin --kayit-dogrulamasiz)",
                            "kayit": kayit_detay}

    try:
        akis.sifirla()
        t0 = time.perf_counter()
        model = YOLO(str(yol), task="segment")
        yukleme_ms = (time.perf_counter() - t0) * 1000
        for _ in range(isinma):
            kare, _, _ = akis.al()
            tek_kare_isle(model, kare, imgsz, conf, cihaz)
    except Exception as exc:
        return temel | {"durum": "HATA", "sebep": f"isinma/yukleme: {exc}"}

    temel = temel | {"kayit": (kayit_detay if kayit_detay is not None
                               else {"durum": "DOGRULANMADI",
                                     "sebep": "--kayit-dogrulamasiz verildi"})}

    olcumler: list[dict[str, Any]] = []
    rota_durumlari: Counter[str] = Counter()
    try:
        for _ in range(tekrar):
            t_toplam = time.perf_counter()
            kare, okuma_ms, kaynak_ad = akis.al()
            parca = tek_kare_isle(model, kare, imgsz, conf, cihaz)
            toplam_ms = (time.perf_counter() - t_toplam) * 1000
            rota_durumlari[parca["rota_durumu"]] += 1
            olcumler.append({"kaynak": kaynak_ad, "okuma_ms": round(okuma_ms, 3),
                             "cikarim_ms": round(parca["cikarim_ms"], 3),
                             "maske_ms": round(parca["maske_ms"], 3),
                             "katman_a_ms": round(parca["katman_a_ms"], 3),
                             "toplam_ms": round(toplam_ms, 3),
                             "rota_durumu": parca["rota_durumu"], "yol_no": parca["yol_no"]})
    except Exception as exc:
        return temel | {"durum": "HATA", "sebep": f"olcum: {exc}",
                         "yukleme_ms": round(yukleme_ms, 3)}

    metrikler: dict[str, dict[str, float | None]] = {}
    for adim in ("okuma_ms", "cikarim_ms", "maske_ms", "katman_a_ms", "toplam_ms"):
        degerler = [float(ornek[adim]) for ornek in olcumler]
        metrikler[adim] = {"p50": yuzdelik(degerler, 50), "p95": yuzdelik(degerler, 95),
                            "ortalama": round(float(np.mean(degerler)), 3)}
    toplam = metrikler["toplam_ms"]
    return temel | {"durum": "OK", "yukleme_ms": round(yukleme_ms, 3),
                     "ornek": len(olcumler), "rota_durumlari": dict(rota_durumlari),
                     "metrikler_ms": metrikler, "olcumler": olcumler,
                     "fps_p50_tabanli": round(1000 / toplam["p50"], 3) if toplam["p50"] else None,
                     "fps_ortalama_tabanli": round(1000 / toplam["ortalama"], 3) if toplam["ortalama"] else None}


def markdown_raporu(
    vakalar: list[dict[str, Any]],
    ortam: dict[str, Any],
    atlanan_vakalar: list[dict[str, Any]] | None = None,
) -> str:
    """p50/p95'i ayri tutan insan-okunur ozet olustur."""
    satirlar = ["# Jetson Uctan Uca FPS Olcumu", "",
                "NEDEN: Sayilar kare okuma + cikarim + get_masks + costmap Katman A yolunun gercek olcumudur.", "",
                f"Ortam: `{ortam.get('platform')}`; Python `{ortam.get('python')}`; CUDA `{ortam.get('cuda_adi')}`.", "",
                "| Model | imgsz | Ornek | Toplam p50 ms | Toplam p95 ms | Ortalama FPS | Durum |",
                "|---|---:|---:|---:|---:|---:|---|"]
    for vaka in vakalar:
        if vaka["durum"] == "OK":
            toplam = vaka["metrikler_ms"]["toplam_ms"]
            satirlar.append(f"| {vaka['tur']} | {vaka['imgsz']} | {vaka['ornek']} | {toplam['p50']:.3f} | {toplam['p95']:.3f} | {vaka['fps_ortalama_tabanli']:.3f} | OK |")
        else:
            satirlar.append(f"| {vaka['tur']} | {vaka['imgsz']} | - | - | - | - | {vaka['durum']}: {vaka.get('sebep')} |")
    for vaka in atlanan_vakalar or []:
        satirlar.append(
            f"| {vaka['tur']} | - | - | - | - | - | ATLANDI: {vaka.get('sebep')} |"
        )
    satirlar.extend(["", "Not: mpp=None olceksiz Katman-A performans kipidir; gercek mpp rota geometrisini degistirir.",
                     "TensorRT satiri yalniz Jetson'da derlenmis FP16 .engine ile gecerlidir."])
    return "\n".join(satirlar) + "\n"


def argumanlar(argv: list[str] | None = None) -> argparse.Namespace:
    """Jetson benchmark komut satiri arayuzunu olustur."""
    varsayilan = _uretim_varsayilanlari()
    tarih = datetime.now().strftime("%Y%m%d_%H%M%S")
    ayrac = argparse.ArgumentParser(description="Gercek Navitas algi + Katman-A FPS olcumu")
    ayrac.add_argument("--girdi", type=Path, default=KOK / "data" / "raw_frames")
    ayrac.add_argument(
        "--kayit-dogrulamasiz", action="store_true",
        help="Kayit defteri dogrulamasini ATLA. VARSAYILAN FAIL-CLOSED'dir "
             "(T203/D-354): uyusmazlikta olcum YAPILMAZ. Bu bayrak T73'te "
             "BILEREK kurulan yanlis-model korumasini kapatir; verildiginde "
             "ozete `kayit.durum=DOGRULANMADI` yazilir.")
    ayrac.add_argument("--pt", type=Path, default=varsayilan["pt"])
    ayrac.add_argument("--onnx", type=Path, default=varsayilan["onnx"])
    ayrac.add_argument(
        "--engine",
        type=Path,
        default=varsayilan["engine"],
        help="Jetson'da derlenmis TensorRT engine; yoksa bu vaka acikca atlanir",
    )
    ayrac.add_argument("--imgsz", type=int, nargs="+", default=varsayilan["imgsz"])
    ayrac.add_argument("--isinma", type=int, default=15)
    ayrac.add_argument("--tekrar", type=int, default=120)
    ayrac.add_argument("--conf", type=float, default=varsayilan["conf"])
    ayrac.add_argument("--cihaz", help="Ultralytics device, ornek: 0")
    ayrac.add_argument("--video-adim", type=int, default=1)
    ayrac.add_argument("--cikti", type=Path, default=KOK / "results" / f"jetson_fps_{tarih}")
    return ayrac.parse_args(argv)


def main() -> int:
    """Tum model/size kombinasyonlarini olc ve JSON + Markdown sonuclari yaz."""
    args = argumanlar()
    if args.isinma < 0 or args.tekrar < 1 or any(x < 32 or x % 32 for x in args.imgsz):
        print("HATA: --isinma >= 0, --tekrar >= 1 ve imgsz 32 kati olmali", file=sys.stderr)
        return 2
    try:
        akis = KareAkisi(args.girdi, args.video_adim)
    except (OSError, ValueError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2
    cikti = args.cikti.resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    vakalar: list[dict[str, Any]] = []
    atlanan_vakalar: list[dict[str, Any]] = []
    modeller = [("pt", args.pt), ("onnx", args.onnx)]
    if args.engine is None:
        sebep = "T16: Jetson'da derlenmis TensorRT .engine henuz yok"
        print(f"ATLANDI: tensorrt_fp16 - {sebep}")
        atlanan_vakalar.append({"tur": "tensorrt_fp16", "sebep": sebep})
    else:
        modeller.append(("tensorrt_fp16", args.engine))
    try:
        for ad, yol in modeller:
            for imgsz in args.imgsz:
                print(f"Olculuyor: {ad} / imgsz={imgsz}")
                vakalar.append(vaka_calistir(
                    ad, yol, imgsz, akis, args.isinma, args.tekrar,
                    args.conf, args.cihaz,
                    kayit_dogrulamasiz=args.kayit_dogrulamasiz))
    finally:
        akis.kapat()

    ortam = ortam_bilgisi()
    veri = {"ortam": ortam,
            "zincir": "kare_oku -> letterbox/cikarim -> rpi_inference.get_masks -> costmap_path_finder.rota_bul(plan=False)",
            "parametreler": {"girdi": str(args.girdi), "isinma": args.isinma, "tekrar": args.tekrar,
                              "conf": args.conf, "imgsz": args.imgsz, "cihaz": args.cihaz, "mpp": None},
            "atlanan_vakalar": atlanan_vakalar,
            "vakalar": vakalar}
    atomik_yaz(cikti / "ozet.json", json.dumps(veri, ensure_ascii=False, indent=2))
    atomik_yaz(cikti / "rapor.md", markdown_raporu(vakalar, ortam, atlanan_vakalar))
    basarili = sum(vaka["durum"] == "OK" for vaka in vakalar)
    print(f"SONUC: {basarili}/{len(vakalar)} vaka olculdu; "
          f"{len(atlanan_vakalar)} vaka acikca atlandi -> {cikti}")
    return 0 if basarili else 1


if __name__ == "__main__":
    raise SystemExit(main())
