"""T226-D (D-448) — ANA harita altın kaydı: master `_harita_ciz` çağrı listesi.

MİMAR KARARI (D-448 §4): ana haritanın çizimi YALNIZ `rota_yok` durumunda
değişebilir; OPEN_ROUTE (ve boşta) durumlarında öğe listesi + koordinatları
master ile BAYT-EŞ kalmalıdır. Bu betik master'daki `comms/yks_gui.py`'yi
(`git show <MASTER>:comms/yks_gui.py`, T226 öncesi, D-448 anı) ayrı modül
olarak yükler, kayıt tutan yalancı tuvalde (Tk'siz, font/DPI'dan bağımsız)
`_harita_ciz()`'i koşar ve çağrı listesini JSON'a yazar. Kapı:
`tests/test_yks_mk15_hakem_ekrani.py` H2d aynı senaryoları GÜNCEL kodla koşar
ve bu dosyayla birebir karşılaştırır.

KOSUM (depo kökünden):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/ana_harita_altin_uret.py
Çıktı: tests/artifacts/t226d/ana_harita_master.json
"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
MASTER = "362197e0"            # D-448 anındaki master (T226 birleşmemiş)
CIKTI = KOK / "tests" / "artifacts" / "t226d" / "ana_harita_master.json"
for _y in (KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

# Senaryolar test dosyasındakiyle AYNI tanımdan gelmek zorunda değil ama AYNI
# değerlerdir; test, JSON'daki `senaryolar` sözlüğünü okuyup yeniden koşar.
BOYUTLAR = ((1142, 725, 1.5), (742, 450, 1.0), (480, 420, 1.0), (1, 1, 1.0))
ROTA = {"v": 1, "type": "OPEN_ROUTE", "seq": 41, "conf": 0.91,
        "ref_xy": [0.0, 0.0],
        "waypoints": [[0.5, 4.0], [1.0, 9.0], [1.5, 14.0]]}
ETIKET = {1: "sol", 2: "orta", 3: "sag"}
DURUMLAR = {
    "bos": None,
    "road1": dict(ROTA, road=1, label=ETIKET[1]),
    "road2": dict(ROTA, road=2, label=ETIKET[2]),
    "road3": dict(ROTA, road=3, label=ETIKET[3]),
    "ankor_yok": dict(ROTA, road=2, label=ETIKET[2], ref_xy=None),
}


class KayitTuval:
    """`_harita_ciz`in ana haritada kullandığı yüzey — ÖLÇÜM YÜZEYİ YOK.

    `bbox`/`coords` bilerek tanımsız: ana harita OPEN_ROUTE/boşta ölçülü
    yerleşime girerse AttributeError ile düşer (font/DPI'ya bağımlı olur)."""

    def __init__(self, w, h):
        self.w, self.h, self.cagrilar = w, h, []

    def winfo_width(self):
        return self.w

    def winfo_height(self):
        return self.h

    def delete(self, *a, **k):
        self.cagrilar.append(["delete", list(a), dict(sorted(k.items()))])

    def _kayit(self, ad, a, k):
        self.cagrilar.append([ad, [list(x) if isinstance(x, tuple) else x for x in a],
                              {kk: (list(v) if isinstance(v, tuple) else v)
                               for kk, v in sorted(k.items())}])
        return len(self.cagrilar)

    def create_line(self, *a, **k):
        return self._kayit("create_line", a, k)

    def create_rectangle(self, *a, **k):
        return self._kayit("create_rectangle", a, k)

    def create_text(self, *a, **k):
        return self._kayit("create_text", a, k)

    def create_oval(self, *a, **k):
        return self._kayit("create_oval", a, k)


def ciz(modul, w, h, olcek, rota):
    modul.OLCEK = olcek
    g = modul.YksArayuz.__new__(modul.YksArayuz)
    g.harita = KayitTuval(w, h)
    g.f_kucuk, g.f_orta = "f_kucuk", "f_orta"
    g.rota, g.rota_yok = rota, None
    g.gorunum_adi = "harita"
    g._harita_ciz()
    return g.harita.cagrilar


def main():
    ham = subprocess.run(["git", "-C", str(KOK), "show", f"{MASTER}:comms/yks_gui.py"],
                         capture_output=True, check=True).stdout
    # Modül depo kökünü `Path(__file__).parents[1]`den türetir (model kayıt
    # defteri vb.): geçici kopya comms/ ALTINDA durmalı; iş bitince silinir.
    yol = KOK / "comms" / f"_yks_gui_master_{MASTER}_gecici.py"
    if yol.exists():
        raise SystemExit(f"gecici dosya zaten var: {yol}")
    try:
        yol.write_bytes(ham)
        spec = importlib.util.spec_from_file_location("yks_gui_master", yol)
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        senaryolar = {}
        for w, h, olcek in BOYUTLAR:
            for ad, rota in DURUMLAR.items():
                anahtar = f"{ad}@{w}x{h}@{olcek}"
                senaryolar[anahtar] = {
                    "w": w, "h": h, "olcek": olcek, "rota": rota,
                    "cagrilar": ciz(modul, w, h, olcek, rota)}
    finally:
        yol.unlink(missing_ok=True)
    veri = {"kaynak": f"{MASTER}:comms/yks_gui.py",
            "kaynak_sha256": hashlib.sha256(ham).hexdigest(),
            "not": "font alanlari 'f_kucuk'/'f_orta' adlariyla kayitlidir",
            "senaryolar": senaryolar}
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(veri, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    print(f"{CIKTI.relative_to(KOK)}: {len(senaryolar)} senaryo; kaynak "
          f"{veri['kaynak']} sha256={veri['kaynak_sha256'][:12]}")
    for k, v in senaryolar.items():
        print(f"  {k}: {len(v['cagrilar'])} cagri")


if __name__ == "__main__":
    main()
