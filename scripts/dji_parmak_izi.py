# -*- coding: utf-8 -*-
"""DJI cekiminin parmak izini (sha256) uretir — yedegin BAGIMSIZ ikinci kaniti.

NEDEN AYRI BIR KANIT: rclone kendi hash'iyle aktarimi dogrular, ama o dogrulama
"yerel dosya bozulmadiysa" varsayimina dayanir. Bu betik yerel tarafi KENDI
basina olcer; iki kanit birbirinden bagimsiz olur.

⚠ CEKIM BITMEDEN URETILEN PARMAK IZI KISMIDIR. Cekim surdukce `dji/` buyur ve
eski kayit BAYAT olur — bu projede elle/anlik listeler dort kez bayatladi.
Bu yuzden kayit, uretildigi andaki dosya sayisini ve toplam boyutu da yazar;
dogrulama betigi sayilar tutmazsa UYARIR.

Kullanim:
  O:\\navitas-local-train\\venv\\Scripts\\python.exe scripts/dji_parmak_izi.py
  O:\\navitas-local-train\\venv\\Scripts\\python.exe scripts/dji_parmak_izi.py --dogrula
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KAYNAK = KOK / "dji"
CIKTI = KOK / "results" / "dji_parmak_izi.json"
UZANTILAR = (".mp4", ".jpg", ".jpeg", ".dng", ".mov", ".srt")


def _sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as fh:
        for blok in iter(lambda: fh.read(1 << 22), b""):
            h.update(blok)
    return h.hexdigest()


def _dosyalar():
    return sorted(p for p in KAYNAK.iterdir()
                  if p.is_file() and p.suffix.lower() in UZANTILAR)


def uret():
    kayit = []
    for f in _dosyalar():
        kayit.append({"ad": f.name, "bayt": f.stat().st_size, "sha256": _sha256(f)})
        print("%-58s %9.1f MB  %s" % (f.name[:58], f.stat().st_size / 1e6,
                                      kayit[-1]["sha256"][:16]))
    belge = {
        "_not": "KISMI OLABILIR — cekim bitmediyse bu kayit yalniz o ANIN durumudur.",
        "dosya_sayisi": len(kayit),
        "toplam_bayt": sum(k["bayt"] for k in kayit),
        "dosyalar": kayit,
    }
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(belge, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n%d dosya · %.2f GB\nyazildi: %s"
          % (len(kayit), belge["toplam_bayt"] / 1e9, CIKTI))
    return 0


def dogrula():
    if not CIKTI.is_file():
        print("parmak izi YOK — once uret.", file=sys.stderr)
        return 2
    belge = json.loads(CIKTI.read_text(encoding="utf-8"))
    simdiki = _dosyalar()

    # 🔴 BAYATLIK KAPISI: kayit uretildikten sonra cekim buyudu mu?
    if len(simdiki) != belge["dosya_sayisi"]:
        print("⚠ BAYAT KAYIT: kayitta %d dosya, diskte %d. Cekim degismis — "
              "parmak izini YENIDEN URET." % (belge["dosya_sayisi"], len(simdiki)))
        return 3

    tut = bozuk = 0
    for k in belge["dosyalar"]:
        f = KAYNAK / k["ad"]
        if not f.is_file():
            print("EKSIK   :", k["ad"]); bozuk += 1; continue
        if _sha256(f) == k["sha256"]:
            tut += 1
        else:
            print("DEGISMIS:", k["ad"]); bozuk += 1
    print("parmak izi: %d tuttu · %d sorunlu · toplam %d" % (tut, bozuk, len(belge["dosyalar"])))
    return 0 if bozuk == 0 else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dogrula", action="store_true")
    raise SystemExit(dogrula() if ap.parse_args().dogrula else uret())
