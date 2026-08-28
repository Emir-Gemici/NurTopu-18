"""160 — T199 VERDIKTI · ON_KAYIT D-340'i MEKANIK uygular.

NEDEN MEKANIK: on kayit, sonuclar gorulduKTEN sonra "sayilari yorumlama"
firsatini kapatmak icin yazilir. Verdikti elle vermek o korumayi delerdi.
Bu betik D-340'in sartlarini KODA yazar ve kendisi karar verir.

ON KAYIT D-340 (egitimden ONCE yazildi):
  BIRINCIL OLCUT : aday, sartname figurunde ROTA URETMELI (ikili, esik YOK).
                   Taban (v36): rota YOK · zemin %4,4 · ret UC_BANT_TEMAS_YOK.
  IKINCIL        : ayni karede zemin kaplamasi — BILGI, kapi DEGIL (D-186).
  GERILEME KAPISI: 10 kapinin TAMAMI (K0..K8 + K5A) MEVCUT esiklerle
                   gecilmeli. Tek kapi duserse aday REDDEDILIR, v36 kalir.
  Esikler bu is icin GEVSETILMEZ.

Kullanim:
  <venv> 160_t199_verdikt.py --aday codes/runs/segment/<ad>/weights/best.pt
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
BURASI = Path(__file__).resolve().parent
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"


def kos(betik: str, ek: list[str]) -> tuple[str, bool]:
    r = subprocess.run([PY, str(BURASI / betik), *ek], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return (r.stdout or "") + (r.stderr or ""), r.returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--aday", type=Path, required=True)
    ap.add_argument("--ad", default="t199_aday")
    a = ap.parse_args()
    if not a.aday.is_file():
        raise SystemExit(f"aday agirlik yok: {a.aday}")

    print("=" * 66)
    print(f"T199 VERDIKTI · {a.aday}")
    print("ON KAYIT: REVIEW_LOG D-340 (egitimden ONCE yazildi)")
    print("=" * 66)

    # ── BIRINCIL: figurde rota uretiliyor mu ──────────────────────────────
    j1 = BURASI / "results" / "t63" / f"{a.ad}_t192.json"
    c1, _ = kos("159_t192_figur_rota.py",
                ["--agirlik", str(a.aday), "--json", str(j1)])
    print(c1.strip())
    d1 = json.loads(j1.read_text(encoding="utf-8"))[0] if j1.is_file() else None
    birincil = bool(d1 and d1.get("rota_uretildi"))

    # ── GERILEME: 10 kapili zincir ────────────────────────────────────────
    c2, _ = kos("65_kabul_denetcisi.py", ["--model", str(a.aday), "--ad", a.ad])
    for satir in c2.splitlines():
        if any(k in satir for k in ("K0 ", "K1 ", "K2 ", "K3 ", "K4 ", "K5 ",
                                    "K5A", "K6 ", "K7 ", "K8 ", "VERDIKT")):
            print("  " + satir.strip())
    zincir = "URETIME ALINIR" in c2 and "URETIME ALINMAZ" not in c2

    print("\n" + "-" * 66)
    print(f"  BIRINCIL (figurde rota)   : "
          f"{'URETILDI' if birincil else 'URETILMEDI'}"
          + (f"  · {d1.get('waypoint')} waypoint" if birincil else ""))
    if d1:
        print(f"  IKINCIL  (bilgi, kapi DEGIL): zemin %"
              f"{100*d1.get('zemin_kaplamasi', 0):.1f} "
              f"(taban v36 %4,4) · cekimser %{100*d1.get('cekimser', 0):.1f}")
    print(f"  GERILEME (10 kapi)        : {'GECTI' if zincir else 'DUSTU'}")
    print("-" * 66)

    if birincil and zincir:
        print("  VERDIKT: ADAY KABUL EDILEBILIR — D-340'in IKI sarti da tuttu.")
        print("           ⚠ Terfi AYRI bir karardir: registry, Jetson paketi ve")
        print("           tam suit ayrica kosulur (D-304 kalibi).")
        kod = 0
    elif not zincir:
        print("  VERDIKT: ADAY REDDEDILDI — gerileme kapisi DUSTU.")
        print("           v36 uretimde KALIR. Esik GEVSETILMEZ (D-340).")
        kod = 1
    else:
        print("  VERDIKT: ADAY REDDEDILDI — figurde rota URETILEMEDI.")
        print("           Zincir gecse bile birincil olcut tutmadi; T199'un")
        print("           amaci buydu. v36 uretimde KALIR.")
        kod = 1
    print("=" * 66)
    print("\n⚠ Bu olcumlerin ZINCIR kismi SENTETIKTIR; figur ise YAPAY ZEKA")
    print("  urunudur (D-99), n = 1. Hicbiri 'sahada calisir' DEMEZ.")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
