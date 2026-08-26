"""T161 olcumu (ON_KAYIT §22): worktree/kopya agacta `ayarlar.REPO` hangi depoyu gosteriyor?

Sahte bir agac kurar:  <tmp>/CLAUDE.md · <tmp>/codes/rpi_inference.py (SENTINEL) ·
                       <tmp>/scripts/olcum/ayarlar.py  (ANA DEPODAN kopya)
Sonra o agactan bir alt surec kosar: ayarlar'i import eder, REPO'yu ve
sys.path'e eklenen kod dizininden yuklenen `rpi_inference`in SENTINEL'ini yazar.

DUZELTMEDEN ONCE beklenen: REPO = O:\navitas ve SENTINEL = YOK (ana depo yuklendi).
DUZELTMEDEN SONRA beklenen: REPO = <tmp> ve SENTINEL = TMP.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ANA = Path(__file__).resolve().parents[2]


def olc():
    with tempfile.TemporaryDirectory() as td:
        kok = Path(td) / "sahte_depo"
        (kok / "codes").mkdir(parents=True)
        (kok / "scripts" / "olcum").mkdir(parents=True)
        (kok / "CLAUDE.md").write_text("# sahte depo koku\n", encoding="utf-8")
        (kok / "codes" / "rpi_inference.py").write_text(
            'SENTINEL = "TMP"\n', encoding="utf-8")
        shutil.copy2(ANA / "scripts" / "olcum" / "ayarlar.py",
                     kok / "scripts" / "olcum" / "ayarlar.py")
        prob = kok / "scripts" / "olcum" / "prob.py"
        prob.write_text(
            "import json, sys\n"
            "from pathlib import Path\n"
            "sys.path.insert(0, str(Path(__file__).parent))\n"
            "from ayarlar import REPO\n"
            "sys.path.insert(0, str(REPO / 'codes'))\n"
            "try:\n"
            "    import rpi_inference\n"
            "    s = getattr(rpi_inference, 'SENTINEL', 'YOK')\n"
            "    kaynak = rpi_inference.__file__\n"
            "except Exception as exc:\n"
            "    s, kaynak = f'HATA: {type(exc).__name__}', None\n"
            "print(json.dumps({'REPO': str(REPO), 'SENTINEL': s, 'kaynak': kaynak}))\n",
            encoding="utf-8")
        cp = subprocess.run([sys.executable, str(prob)], capture_output=True,
                            text=True, cwd=str(kok))
        satir = [l for l in cp.stdout.splitlines() if l.startswith("{")]
        return json.loads(satir[-1]) if satir else {"hata": cp.stderr[-500:]}


if __name__ == "__main__":
    sonuc = olc()
    sonuc["hukum"] = ("KUSURLU: kopya agac ANA DEPOYU yukluyor"
                      if sonuc.get("SENTINEL") != "TMP"
                      else "SAGLAM: kopya agac KENDI kodunu yukluyor")
    print(json.dumps(sonuc, indent=1, ensure_ascii=False))
