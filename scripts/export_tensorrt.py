"""NEDEN: TensorRT engine dosyalari CUDA/TensorRT surumu ve GPU mimarisine
baglidir. PC'de uretilen .engine Jetson Orin NX'te CALISMAZ; bu betik PC'de
yalniz tasinabilir ONNX (FP16 varsayilan) uretir ve Jetson derleme bilgisini
yaninda saklar.

Iki asama zorunludur:
  1. PC: ``model.export(format="onnx", imgsz=640, half=True)``
  2. Jetson: ayni ONNX'i Jetson TensorRT'siyle FP16 engine'e derle.

INT8 istenirse kalibrasyon veri YAML yolu metadata'ya baglanir. Kalibrasyon
Jetson'daki derleme adiminda uygulanir; PC'de engine derlenmez.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
import uuid
from datetime import datetime
from pathlib import Path

from ultralytics import YOLO


KOK = Path(__file__).resolve().parents[1]


def atomik_json_yaz(hedef: Path, veri: dict) -> None:
    """Jetson'a aktarilacak derleme bilgisini yarim dosya olmadan yaz."""
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    try:
        gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()


def argumanlar() -> argparse.Namespace:
    """PC ONNX disa aktarma arayuzunu olustur."""
    ayrac = argparse.ArgumentParser(description="PC'de FP16 ONNX uret; TensorRT engine Jetson'da derlenir")
    ayrac.add_argument("--model", type=Path, default=KOK / "models" / "navitas_seg_v20_best.pt")
    ayrac.add_argument("--imgsz", type=int, nargs="+", default=[640],
                        help="ONNX giris boyutu/boyutlari (varsayilan: 640)")
    ayrac.add_argument("--fp32", action="store_true", help="FP16 yerine FP32 ONNX disari aktar")
    ayrac.add_argument("--opset", type=int, default=17)
    ayrac.add_argument("--cihaz", default="0",
                        help="PC CUDA cihazi (varsayilan: 0); CPU icin cpu yazin")
    ayrac.add_argument("--dinamik", action="store_true", help="Jetson engine icin dinamik ONNX sekli iste")
    ayrac.add_argument("--basitlestir", action="store_true", help="onnxsim varsa ONNX grafigini basitlestir")
    ayrac.add_argument("--cikti", type=Path, help="ONNX kopyalari ve manifest icin dizin")
    ayrac.add_argument("--int8-kalibrasyon", type=Path,
                        help="Yalniz Jetson INT8 derlemesi icin veri YAML kancasi")
    return ayrac.parse_args()


def ayarlari_dogrula(args: argparse.Namespace) -> None:
    """Agir export baslamadan once acik hatalari bildir."""
    if not args.model.is_file():
        raise FileNotFoundError(f"Model bulunamadi: {args.model}")
    if args.model.suffix.lower() != ".pt":
        raise ValueError("PC ONNX export girdisi bir .pt segment modeli olmali")
    if any(boyut < 32 or boyut % 32 for boyut in args.imgsz):
        raise ValueError("Her --imgsz degeri 32'nin pozitif kati olmali")
    if args.int8_kalibrasyon is not None and not args.int8_kalibrasyon.exists():
        raise FileNotFoundError(f"INT8 kalibrasyon yolu bulunamadi: {args.int8_kalibrasyon}")
    if importlib.util.find_spec("onnx") is None:
        raise RuntimeError(
            "onnx paketi bu PC venv'inde yok. Once su komutu calistirin: "
            r"O:\navitas-local-train\venv\Scripts\python.exe -m pip install onnx"
        )


def fp16_dogrula(onnx_yol: Path) -> bool:
    """ONNX agirliklarinda gercek FP16 tensorlugu oldugunu denetle.

    ``half=True`` CPU exportunda bazen FP32'ye geri dusebilir. Sessizce FP32
    artefakti Jetson FP16 karsilastirmasi diye raporlanmasin diye bu kapi var.
    """
    import onnx

    model = onnx.load(str(onnx_yol), load_external_data=False)
    return any(t.data_type == onnx.TensorProto.FLOAT16 for t in model.graph.initializer)


def jetson_komutu(onnx: Path, imgsz: int, fp16: bool, int8_kalibrasyon: Path | None) -> str:
    """Engine'i yalniz Jetson'da derlemek icin kopyalanabilir komut ver."""
    bayraklar = [f"model={onnx.name}", "format=engine", f"imgsz={imgsz}"]
    if fp16:
        bayraklar.append("half=True")
    if int8_kalibrasyon is not None:
        bayraklar.extend(["int8=True", f"data={int8_kalibrasyon.name}"])
    return "yolo export " + " ".join(bayraklar)


def main() -> int:
    """PT modeli ONNX'e aktar; engine derlemeyi bilerek Jetson'a birak."""
    args = argumanlar()
    try:
        ayarlari_dogrula(args)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"HATA: {exc}", file=sys.stderr)
        return 2

    fp16 = not args.fp32
    cikti = (args.cikti or (KOK / "results" / f"onnx_export_{datetime.now():%Y%m%d_%H%M%S}")).resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(args.model), task="segment")
    onnxler: list[Path] = []

    for boyut in args.imgsz:
        print(f"ONNX uretiliyor: {args.model.name} -> imgsz={boyut}, {'FP16' if fp16 else 'FP32'}")
        try:
            uretilen = Path(model.export(
                format="onnx", imgsz=boyut, half=fp16, opset=args.opset,
                dynamic=args.dinamik, simplify=args.basitlestir, device=args.cihaz,
            ))
        except Exception as exc:
            print(f"HATA: ONNX export basarisiz (imgsz={boyut}): {exc}", file=sys.stderr)
            return 1
        if not uretilen.is_file():
            print(f"HATA: Ultralytics ONNX dosyasini vermedi: {uretilen}", file=sys.stderr)
            return 1
        hedef = cikti / f"{args.model.stem}_{boyut}_{'fp16' if fp16 else 'fp32'}.onnx"
        if uretilen.resolve() != hedef.resolve():
            shutil.copy2(uretilen, hedef)
        if fp16 and not fp16_dogrula(hedef):
            print("HATA: ONNX FP16 agirlik icermiyor. CUDA cihazini (--cihaz 0) "
                  "ve export ortamini kontrol edin; FP32 artefakti FP16 diye kullanmayin.", file=sys.stderr)
            return 1
        onnxler.append(hedef)
        print(f"  -> {hedef}")

    manifest = {
        "olusturma_zamani": datetime.now().isoformat(timespec="seconds"),
        "pc_modeli": str(args.model.resolve()),
        "format": "onnx",
        "fp16": fp16,
        "imgsz": args.imgsz,
        "dinamik": args.dinamik,
        "opset": args.opset,
        "cihaz": args.cihaz,
        "onnxler": [str(yol.resolve()) for yol in onnxler],
        "int8_kalibrasyon": str(args.int8_kalibrasyon.resolve()) if args.int8_kalibrasyon else None,
        "jetson_uyari": "PC'de uretilen TensorRT .engine Jetson Orin NX'te calismaz; engine Jetson'da derlenmelidir.",
        "jetson_komutlari": [
            jetson_komutu(yol, boyut, fp16, args.int8_kalibrasyon)
            for yol, boyut in zip(onnxler, args.imgsz)
        ],
    }
    atomik_json_yaz(cikti / "jetson_derleme_manifest.json", manifest)
    print("ONEMLI: .engine bu PC'de uretilmedi. ONNX'i Jetson'a tasiyip manifestteki komutu Jetson'da calistirin.")
    print(f"MANIFEST: {cikti / 'jetson_derleme_manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
