"""Single source of truth for Navitas runtime model selection and identity.

T143 (D-284, T18 curutucusu): `.engine` / `.onnx` TUREVLERI ayni soydan
tanitilir. Profilin `turevler` sozlugu dosya ADIYLA anahtarlanir; her turevin
KENDI `sha256`si vardir ve `kaynak`/`kaynak_sha256` alanlari onu uretim `.pt`
kaydina baglar. Fail-closed KALIR:
  * kayitsiz/yabanci dosya         -> RED (kayitli ad yok)
  * sha256 yer tutucu              -> RED (derlenmemis = dogrulanmamis)
  * sha256 diskteki dosyaya uymuyor -> RED
  * kaynak_sha256 uretim .pt'ye uymuyor -> RED (yetim turev)
Dogrulanmis turev eklemek icin:  python codes/model_registry.py --turev-kaydet <dosya>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "config" / "model_registry.json"
PAKET_REGISTRY = ROOT / "jetson_paket" / "config" / "model_registry.json"

if str(ROOT / "codes") not in sys.path:      # `python codes/model_registry.py` kipi
    sys.path.insert(0, str(ROOT / "codes"))
from karar_sozlesmesi import MODEL_TUREV_SHA_YER_TUTUCU  # noqa: E402

TUREV_UZANTILARI = {".engine", ".onnx"}
TUREV_BACKEND = {".engine": "tensorrt", ".onnx": "onnx"}


class ModelRegistryError(RuntimeError):
    pass


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict:
    registry_path = Path(path)
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ModelRegistryError(f"model registry okunamadı: {registry_path}: {exc}") from exc
    if data.get("schema_version") != 1 or not isinstance(data.get("profiles"), dict):
        raise ModelRegistryError("desteklenmeyen/bozuk model registry şeması")
    return data


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_dogrulanmis_mi(ozet) -> bool:
    """Yer tutucu / bos / bicimsiz ozet DOGRULANMAMIS sayilir (fail-closed)."""
    if not isinstance(ozet, str) or ozet == MODEL_TUREV_SHA_YER_TUTUCU:
        return False
    if len(ozet) != 64:
        return False
    try:
        int(ozet, 16)
    except ValueError:
        return False
    return True


def turev_dogrula(profil: dict, dosya: str | Path, *, calisan_imgsz=None,
                  ozet_hesapla=True) -> tuple[bool, dict]:
    """Bir dosyayi profilin `turevler` sozlugune gore dogrula.

    -> (uyumlu, detay). Karar VERMEZ; `resolve_model`/`load_model` verir.
    Kural: ad kayitli + sha256 yer tutucu DEGIL + diskteki ozet BIREBIR +
    kaynak_sha256 == profil sha256 + imgsz eslesiyor. Eksik olan RED'dir.
    """
    yol = Path(dosya)
    ad = yol.name
    detay = {"turev": ad}
    turevler = profil.get("turevler")
    if not isinstance(turevler, dict) or ad not in turevler:
        detay["durum"] = "ESLESMIYOR"          # kayitsiz/yabanci turev
        return False, detay
    kayit = turevler[ad]
    detay.update({"beklenen_sha256": kayit.get("sha256"),
                  "kaynak": kayit.get("kaynak"),
                  "beklenen_imgsz": kayit.get("imgsz")})
    if kayit.get("kaynak") != profil.get("path") or \
            kayit.get("kaynak_sha256") != profil.get("sha256"):
        detay["durum"] = "TUREV KAYNAGI ESLESMIYOR"   # yetim turev
        return False, detay
    if not sha256_dogrulanmis_mi(kayit.get("sha256")):
        detay["durum"] = "TUREV SHA YER TUTUCU (dogrulanmamis)"
        return False, detay
    if calisan_imgsz is not None:
        try:
            if int(kayit.get("imgsz")) != int(calisan_imgsz):
                detay["durum"] = "IMGSZ ESLESMIYOR"
                return False, detay
        except (TypeError, ValueError):
            detay["durum"] = "turevde `imgsz` gecersiz"
            return False, detay
    if ozet_hesapla:
        if not yol.is_file():
            detay["durum"] = "turev dosyasi yok"
            return False, detay
        gercek = _sha256(yol)
        detay["gercek_sha256"] = gercek
        if gercek != kayit["sha256"]:
            detay["durum"] = "TUREV SHA ESLESMIYOR"
            return False, detay
    detay["durum"] = "turev_eslesti"
    return True, detay


def resolve_model(profile: str | None = None, *, registry_path: str | Path = DEFAULT_REGISTRY,
                  verify: bool = True, turev: str | Path | None = None) -> tuple[Path, dict]:
    """Etkin profilin artefaktini coz. `turev` verilirse o dosya profilin
    `turevler` kaydiyla dogrulanir (T143); .pt yolu DEGISMEZ."""
    registry = load_registry(registry_path)
    name = profile or registry.get("default_profile")
    try:
        spec = dict(registry["profiles"][name])
    except KeyError as exc:
        choices = ", ".join(sorted(registry["profiles"]))
        raise ModelRegistryError(f"bilinmeyen model profili {name!r}; seçenekler: {choices}") from exc
    if turev is not None:
        uyumlu, detay = turev_dogrula(spec, turev, ozet_hesapla=verify)
        if not uyumlu:
            raise ModelRegistryError(f"{name}: turev {Path(turev).name} RED — {detay['durum']}")
        spec["profile"] = name
        spec["resolved_artifact"] = str(Path(turev))
        spec["turev_detay"] = detay
        return Path(turev), spec
    model_path = ROOT / spec["path"]
    artifact = model_path / spec.get("artifact", "") if model_path.is_dir() else model_path
    if not model_path.exists() or not artifact.exists():
        raise ModelRegistryError(f"model artefaktı yok: {artifact}")
    if int(spec.get("imgsz", 0)) <= 0:
        raise ModelRegistryError(f"{name}: geçersiz imgsz")
    if verify:
        actual = _sha256(artifact)
        if actual != spec.get("sha256"):
            raise ModelRegistryError(
                f"{name}: SHA-256 uyuşmuyor; beklenen={spec.get('sha256')} gerçek={actual}"
            )
    spec["profile"] = name
    spec["resolved_artifact"] = str(artifact)
    return model_path, spec


def describe(spec: dict) -> str:
    metrics = spec.get("metrics") or {}
    score = f" mAP50={metrics['mask_map50']:.4f}" if "mask_map50" in metrics else ""
    return (f"{spec['model_id']} [{spec['backend']}, imgsz={spec['imgsz']}, "
            f"sha256={spec['sha256'][:12]}…{score}]")


# ── T143 · turev kaydi (CLI) ─────────────────────────────────────────────────

def _defteri_yaz(path: Path, data: dict) -> None:
    """Defteri ayni bicimde (indent=1, satir sonu korunur) geri yaz — paket
    aynasi bayt-es kalmali (tests/test_jetson_paket_defteri)."""
    ham = path.read_bytes() if path.is_file() else b"\n"
    metin = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if b"\r\n" in ham:
        metin = metin.replace("\n", "\r\n")
    path.write_bytes(metin.encode("utf-8"))


def turev_kaydet(dosya: str | Path, *, registry_path: str | Path = DEFAULT_REGISTRY,
                 profile: str | None = None, kaynak_pt: str | Path | None = None,
                 ayna_yollari: tuple = ()) -> dict:
    """Derlenmis turevin GERCEK sha256'sini deftere yaz.

    Guvenlik: (1) dosya var ve uzantisi turev uzantisi; (2) turev ad olarak
    profilde ZATEN kayitli olmali — bu CLI yabanci dosyayi soya SOKMAZ, yalniz
    yer tutucuyu doldurur / ozeti tazeler; (3) `kaynak_pt` verilirse diskteki
    .pt ozeti profilin sha256'siyla birebir olmali (yanlis soydan derleme RED);
    (4) competition.path ve .pt sha256 DEGISMEZ.
    """
    yol = Path(dosya)
    if not yol.is_file():
        raise ModelRegistryError(f"turev dosyasi yok: {yol}")
    if yol.suffix.lower() not in TUREV_UZANTILARI:
        raise ModelRegistryError(f"turev uzantisi degil: {yol.suffix!r} (izinli: {sorted(TUREV_UZANTILARI)})")
    registry = load_registry(registry_path)
    name = profile or registry.get("default_profile")
    profil = registry["profiles"][name]
    turevler = profil.get("turevler")
    if not isinstance(turevler, dict) or yol.name not in turevler:
        raise ModelRegistryError(
            f"{yol.name} profil {name!r} turevlerinde KAYITLI DEGIL — bu CLI yabanci dosyayi "
            "soya sokmaz; once defterde (kaynak baglantisiyla) tanimlanmali.")
    if kaynak_pt is not None:
        kaynak_yol = Path(kaynak_pt)
        if not kaynak_yol.is_file():
            raise ModelRegistryError(f"kaynak .pt yok: {kaynak_yol}")
        kaynak_ozet = _sha256(kaynak_yol)
        if kaynak_ozet != profil.get("sha256"):
            raise ModelRegistryError(
                f"kaynak .pt ozeti profil sha256 ile uyusmuyor: {kaynak_ozet} != {profil.get('sha256')}")
    kayit = turevler[yol.name]
    if kayit.get("kaynak") != profil.get("path") or kayit.get("kaynak_sha256") != profil.get("sha256"):
        raise ModelRegistryError(f"{yol.name}: turev kaynagi profilin .pt kaydiyla uyusmuyor (yetim)")
    eski = kayit.get("sha256")
    kayit["sha256"] = _sha256(yol)
    kayit["backend"] = TUREV_BACKEND[yol.suffix.lower()]
    _defteri_yaz(Path(registry_path), registry)
    for ayna in ayna_yollari:                       # ayna = ana defterin BAYT-ES kopyasi
        Path(ayna).write_bytes(Path(registry_path).read_bytes())
    return {"turev": yol.name, "eski_sha256": eski, "yeni_sha256": kayit["sha256"],
            "profil": name, "defter": str(registry_path)}


def _cli(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Navitas model kayit defteri araclari (T143)")
    parser.add_argument("--turev-kaydet", metavar="DOSYA",
                        help="derlenmis .engine/.onnx turevinin sha256'sini deftere yaz")
    parser.add_argument("--kaynak-pt", metavar="PT", default=None,
                        help="turevin derlendigi .pt; verilirse ozeti profil sha256 ile kiyaslanir")
    parser.add_argument("--defter", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--profil", default=None)
    parser.add_argument("--ayna-yok", action="store_true",
                        help="jetson_paket/config aynasini guncelleme")
    args = parser.parse_args(argv)
    if not args.turev_kaydet:
        parser.print_help()
        return 2
    aynalar = () if args.ayna_yok or Path(args.defter).resolve() != DEFAULT_REGISTRY.resolve() \
        else (PAKET_REGISTRY,)
    try:
        sonuc = turev_kaydet(args.turev_kaydet, registry_path=args.defter, profile=args.profil,
                             kaynak_pt=args.kaynak_pt, ayna_yollari=aynalar)
    except ModelRegistryError as exc:
        print(f"RED: {exc}")
        return 1
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
