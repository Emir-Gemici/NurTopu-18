"""K3 üretim boru hattı — KARAR İZİ (kare başına karar) yaz / karşılaştır (T214-A devam).

İlk koşu (`kosum_tur3/kosum_tur3.sh`, 10 Eyl 12:39–12:43) ile devam koşusu (`kosum_tur3_devam.sh`)
AYNI tarama karelerini (`tarama/`, `--yeniden-tara` YOK) üretim kare döngüsünden geçirir; model,
karar zinciri ve besleme aynıdır, devam koşusu yalnız TEŞHİS alanları ekler. İz =
(besleme/harita_senaryo) → kare başına [n, karar, yol, guven, sebep]. Karşılaştırma farkları listeler
(`iki_kosu_karsilastirma.json`) — GPU çıkarımının aynı girdide aynı kararı verdiğinin ölçümüdür.

  venv python -B results/fdr_sprint_20260910/H1/k3_uretim_boru/karar_izi.py yaz kosu1_karar_izi.json
  venv python -B results/fdr_sprint_20260910/H1/k3_uretim_boru/karar_izi.py karsilastir kosu1_karar_izi.json
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BURASI = Path(__file__).resolve().parent
BESLEMELER = ("kerteriz", "ham")


def iz_kur(kok: Path) -> dict:
    iz = {}
    for bes in BESLEMELER:
        for p in sorted((kok / bes).glob("harita_*_*.json")):
            r = json.loads(p.read_text(encoding="utf-8"))
            iz[f"{bes}/{r['harita']}_{r['senaryo']}"] = [
                [s["n"], s.get("karar"), s.get("yol"), s.get("guven"), s.get("sebep")] for s in r["kareler"]]
    return iz


def karsilastir(eski: dict, yeni: dict) -> dict:
    fark = []
    for anahtar in sorted(set(eski) | set(yeni)):
        a, b = eski.get(anahtar), yeni.get(anahtar)
        if a is None or b is None:
            fark.append({"anahtar": anahtar, "neden": "bir koşuda yok"})
            continue
        if len(a) != len(b):
            fark.append({"anahtar": anahtar, "neden": f"kare sayısı {len(a)} ↔ {len(b)}"})
        for x, y in zip(a, b):
            if x != y:
                fark.append({"anahtar": anahtar, "kare": x[0], "kosu1": x, "kosu2": y})
    return {"harita_besleme_n": len(eski), "kare_n": sum(len(v) for v in eski.values()),
            "fark_n": len(fark), "karar_es": not fark, "farklar": fark}


def main(argv) -> int:
    komut, ad = argv[1], argv[2]
    dosya = BURASI / ad
    iz = iz_kur(BURASI)
    if komut == "yaz":
        dosya.write_text(json.dumps(iz, ensure_ascii=False), encoding="utf-8")
        print(f"[iz] {len(iz)} harita·besleme, {sum(len(v) for v in iz.values())} kare → {dosya.name}")
        return 0
    if komut != "karsilastir":
        raise SystemExit(f"komut {komut!r}: yaz | karsilastir")
    sonuc = {"kosu1": ad, **karsilastir(json.loads(dosya.read_text(encoding="utf-8")), iz)}
    (BURASI / "iki_kosu_karsilastirma.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[iz] {sonuc['harita_besleme_n']} harita·besleme, {sonuc['kare_n']} kare: fark {sonuc['fark_n']} "
          f"→ karar_es={sonuc['karar_es']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
