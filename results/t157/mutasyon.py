"""T157 mutasyon kaniti: kok satiri boz -> test DUSER -> bayt-es geri al.

Kullanim: mutasyon.py <a|b|c|d|e> <uygula|geri>
Yedek bayt-es olarak scratchpad'e alinir ve geri alma SHA ile dogrulanir.
"""
import hashlib
import shutil
import sys
from pathlib import Path

KOK = Path(r"O:\navitas\.claude\worktrees\wf_a3528b62-8d1-2")
YEDEK = Path(r"C:\Users\yunus\AppData\Local\Temp\claude\O--navitas"
             r"\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\scratchpad\mut_yedek")
YEDEK.mkdir(parents=True, exist_ok=True)

KILAVUZ = "JETSON_KILAVUZ.md"
KILAVUZ_P = "jetson_paket/JETSON_KILAVUZ.md"

MUTASYONLAR = {
    # (a) --imgsz denetlenmiyordu: SS5 ASIL FPS blogunda 512 -> 640
    "a": (KILAVUZ, "  --imgsz 512 \\\r\n  --isinma 15 --tekrar 120",
          "  --imgsz 640 \\\r\n  --isinma 15 --tekrar 120"),
    # (b) uzantisiz model yolu: SS5 --engine satirindan uzantiyi at + eskit
    "b": (KILAVUZ, "  --engine models/navitas_seg_v36_best_512_fp16.engine \\",
          "  --engine models/navitas_seg_v30_best_512_fp16 \\"),
    # (c) baslik metnindeki ciplak vNN: canli SS0-T85 basligindan uretimi sil
    "c": (KILAVUZ, " *(zincir SÜRDÜ — bugünün asıl modeli **v36**, D-293)*", ""),
    # (d) agac istisnasi bolume bagli degildi: SS9'a etiketli agac satiri koy
    "d": (KILAVUZ, "## 9. Bugün YAPILMAYACAKLAR\r\n",
          "## 9. Bugün YAPILMAYACAKLAR\r\n"
          "├── navitas_seg_v17_best.pt              ← yedek model\r\n"),
    # (e) taban k109 sayisi ham JSON'a bagli mi
    "e": ("results/gece_20260826/v35_ref2_olcum.json",
          '"figur_zemin_orani": 0.15084', '"figur_zemin_orani": 0.11'),
}


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    ad, eylem = sys.argv[1], sys.argv[2]
    dosya, eski, yeni = MUTASYONLAR[ad]
    hedef = KOK / dosya
    yedek = YEDEK / f"{ad}_{Path(dosya).name}"

    if eylem == "uygula":
        shutil.copy2(hedef, yedek)
        print(f"YEDEK sha256 = {_sha(yedek)}  ({yedek})")
        ham = hedef.read_bytes()
        e, y = eski.encode("utf-8"), yeni.encode("utf-8")
        if ham.count(e) != 1:
            return print(f"HATA: kok satiri {ham.count(e)} kez gecti") or 2
        hedef.write_bytes(ham.replace(e, y))
        print(f"MUTASYON uygulandi: {dosya}")
        print(f"  - {eski!r}\n  + {yeni!r}")
        print(f"BOZUK  sha256 = {_sha(hedef)}")
        return 0

    if eylem == "geri":
        shutil.copy2(yedek, hedef)
        print(f"GERI ALINDI: {dosya}")
        print(f"BAYT-ES? {_sha(hedef) == _sha(yedek)}  sha256 = {_sha(hedef)}")
        return 0
    return 2


sys.exit(main())
