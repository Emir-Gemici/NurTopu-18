"""NEDEN: TASK_QUEUE.md yollarinda Python kacislarinin bozdugu satirlari mekanik onarir."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


KOK = Path(__file__).resolve().parents[2]
VARSAYILAN_KUYRUK = KOK / "TASK_QUEUE.md"
VARSAYILAN_RAPOR = Path(__file__).with_name("t115_rapor.json")
BOZUK_BASLANGIC = "avitas"
YOL_ONEKI = "avitas-local-train"
YOL_KOKU = "\\navitas-local-train\\"
NUMARALI_PYTHON_DOSYASI = re.compile(r"^(?P<ad>[0-9]+_[A-Za-z0-9_]+\.py)(?=$|[:`\"')\s;,])")
GOREV_KILIDI = re.compile(r"\[IN_PROGRESS:\s*(?P<sahip>[^\]]+)\]")
BU_AJAN = "Codex-1"


def _satir_ve_son(satir: str) -> tuple[str, str]:
    """Satir icerigini satir sonundan ayir; CRLF/LF baytlarini koru."""
    if satir.endswith("\r\n"):
        return satir[:-2], "\r\n"
    if satir.endswith(("\r", "\n")):
        return satir[:-1], satir[-1]
    return satir, ""


def onar(metin: str) -> tuple[str, dict[str, Any]]:
    """Yalniz olculen iki-satir desenini onar ve ayrintili rapor dondur."""
    satirlar = metin.splitlines(keepends=True)
    cikti: list[str] = []
    cozulenler: list[dict[str, Any]] = []
    cozulemeyenler: list[dict[str, Any]] = []

    for indis, ham_satir in enumerate(satirlar):
        ikinci, ikinci_son = _satir_ve_son(ham_satir)
        if not ikinci.startswith(BOZUK_BASLANGIC):
            cikti.append(ham_satir)
            continue

        birinci = ""
        if indis > 0:
            birinci, _ = _satir_ve_son(satirlar[indis - 1])
        ortak = {
            "satir_no": indis + 1,
            "once_1": birinci,
            "once_2": ikinci,
        }

        if indis == 0 or not birinci.endswith("O:"):
            cozulemeyenler.append({**ortak, "neden": "onceki_satir_O_ile_bitmiyor"})
            cikti.append(ham_satir)
            continue
        if not ikinci.startswith(YOL_ONEKI):
            cozulemeyenler.append({**ortak, "neden": "satir_avitas_local_train_ile_baslamiyor"})
            cikti.append(ham_satir)
            continue

        kilit = GOREV_KILIDI.search(birinci)
        if kilit is not None and kilit.group("sahip").strip() != BU_AJAN:
            cozulemeyenler.append(
                {
                    **ortak,
                    "neden": "baska_ajan_in_progress",
                    "kilit_sahibi": kilit.group("sahip").strip(),
                }
            )
            cikti.append(ham_satir)
            continue

        kalan = ikinci[len(YOL_ONEKI):]
        if not kalan:
            cozulemeyenler.append({**ortak, "neden": "oktal_tersi_icin_ilk_karakter_yok"})
            cikti.append(ham_satir)
            continue

        ilk_karakter = kalan[0]
        oktal_tersi = oct(ord(ilk_karakter))[2:]
        ek = oktal_tersi + kalan[1:]
        dosya_eslesmesi = NUMARALI_PYTHON_DOSYASI.match(ek)
        if dosya_eslesmesi is None:
            cozulemeyenler.append(
                {
                    **ortak,
                    "neden": "oktal_tersi_numarali_python_dosyasi_uretmiyor",
                    "ilk_karakter_kod_noktasi": ord(ilk_karakter),
                    "oktal_tersi": oktal_tersi,
                    "aday_ek": ek,
                }
            )
            cikti.append(ham_satir)
            continue
        sonra = birinci + YOL_KOKU + ek

        # Onceki satir ciktiya az once aynen eklenmisti; yalniz o iki satiri
        # mekanik olarak tek satira indir. Baska hicbir satira dokunma.
        if not cikti:
            raise RuntimeError("Ic tutarsizlik: birlestirilecek onceki satir yok")
        cikti[-1] = sonra + ikinci_son
        cozulenler.append(
            {
                **ortak,
                "sonra": sonra,
                "cozulen_dosya_adi": dosya_eslesmesi.group("ad"),
                "ilk_karakter_kod_noktasi": ord(ilk_karakter),
                "oktal_tersi": oktal_tersi,
            }
        )

    rapor = {
        "cozulenler": cozulenler,
        "cozulemeyenler": cozulemeyenler,
        "ozet": {
            "bulunan": len(cozulenler) + len(cozulemeyenler),
            "cozulen": len(cozulenler),
            "cozulemeyen": len(cozulemeyenler),
        },
    }
    return "".join(cikti), rapor


def _argumanlar() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T115 TASK_QUEUE oktal kacis onarimi")
    parser.add_argument("--kuyruk", type=Path, default=VARSAYILAN_KUYRUK)
    parser.add_argument("--rapor", type=Path, default=VARSAYILAN_RAPOR)
    parser.add_argument("--uygula", action="store_true", help="onarimi kuyruk dosyasina yaz")
    return parser.parse_args()


def main() -> int:
    args = _argumanlar()
    kaynak_bayt = args.kuyruk.read_bytes()
    try:
        kaynak = kaynak_bayt.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"HATA: kuyruk UTF-8 degil: {args.kuyruk}") from exc

    onarilmis, rapor = onar(kaynak)
    if args.uygula:
        args.kuyruk.write_bytes(onarilmis.encode("utf-8"))

    rapor_metni = json.dumps(rapor, ensure_ascii=False, indent=2) + "\n"
    args.rapor.parent.mkdir(parents=True, exist_ok=True)
    args.rapor.write_text(rapor_metni, encoding="utf-8", newline="\n")
    print(rapor_metni, end="")
    return 0 if rapor["ozet"]["cozulemeyen"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
