"""T54 — 11 sinifli RescueNet etiketlerini 2 sinifa YENI eslemeyle indir.

NEDEN (REVIEW_LOG D-67, kodda dogrulandi):
`dataset/download_and_convert.py:72-83` yalniz road-clear(7)->0 ve
road-blocked(8)->1 aliyor; bina, agac, su, havuz ETIKETSIZ ARKA PLANA dusuyor.
Segmentasyonda etiketsiz arka plan DENETIM ALMAZ — modele hicbir yerde "cati
zemin DEGILDIR" denmiyor. Model "road-clear = zemin" ogrenip karsi ornek
olmadigi icin "genis duz yuzey = zemin" diye genelliyor. Otoparkta bina catisi
tam olarak bu yuzden yesil.

BU BETIK ham veriyi YENIDEN INDIRMEZ. `dataset/rescuenet_11sinif` diskte hazir;
etiketleri okuyup yeni eslemeyle 2 sinifa indirir.

ESLEME (11 sinif -> 2 sinif):
    0 traversable                -> 0   (zemin — DEGISMEDI)
    1 blocked                    -> 1   (engel — DEGISMEDI)
    2 water                      -> 1   YENI
    3 building_no_damage         -> 1   YENI
    4 building_minor             -> 1   YENI
    5 building_major             -> 1   YENI
    6 building_total_destruction -> 1   YENI
    7 vehicle                    -> 1   YENI  (bkz. not)
    8 tree                       -> 1   YENI
    9 pool                       -> 1   YENI

ARAC NOTU: DOTA OBB katmani zaten araclari serbest alandan CIKARIYOR (madde 15
"yalniz cikarir"). Segmentasyonda da engel saymak CIFT SAYIM degil, ayni yonde
ikinci bir cikarmadir; madde 15 acisindan guvenlidir (serbest alani buyutmez).
Sinif dagilimi once/sonra basiliyor ki etki gorulebilsin.
"""
import argparse
import collections
import shutil
import sys
from pathlib import Path

BURASI = Path(__file__).parent
sys.path.insert(0, str(BURASI))
from ayarlar import REPO  # noqa: E402

KAYNAK = REPO / "dataset" / "rescuenet_11sinif"
HEDEF = REPO / "dataset" / "rescuenet_2sinif_engelli"

ESLEME = {0: 0, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1, 9: 1}

DATA_YAML = """# T54 — 2 SINIF, YENI ENGEL ESLEMESI (REVIEW_LOG D-67)
#
# Onceki 2 sinifli kume yalniz road-clear/road-blocked aliyordu; bina, agac, su
# ve havuz ETIKETSIZ ARKA PLANA dusuyordu. Etiketsiz arka plan denetim almaz,
# bu yuzden model "cati zemin degildir" bilgisini HIC ogrenmedi ve otoparkta
# bina catisini geciilebilir sandi (%80,6 kaplama, gozle dogrulandi).
#
# Burada 11 sinifli RescueNet etiketleri 2 sinifa su eslemeyle indirildi:
#   0 traversable -> 0 ;  DIGER HER SINIF -> 1 blocked
# Boylece "zemin degil -> engel" (anayasa madde 15) EGITIM VERISINDE de gecerli.
path: {hedef}
train: images/train
val: images/val
test: images/test

nc: 2
names:
  0: traversable
  1: blocked
"""


def etiket_donustur(satirlar, sayac_once, sayac_sonra):
    cikti = []
    for s in satirlar:
        p = s.split()
        if not p:
            continue
        try:
            eski = int(p[0])
        except ValueError:
            continue
        sayac_once[eski] += 1
        yeni = ESLEME.get(eski)
        if yeni is None:
            continue
        sayac_sonra[yeni] += 1
        cikti.append(" ".join([str(yeni)] + p[1:]))
    return cikti


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--temizle", action="store_true")
    a = ap.parse_args()

    if not (KAYNAK / "labels").is_dir():
        raise SystemExit(f"11 sinifli kume yok: {KAYNAK}")
    if HEDEF.exists() and a.temizle:
        shutil.rmtree(HEDEF)

    once = collections.Counter()
    sonra = collections.Counter()
    n_kare = 0
    for bolum in ("train", "val", "test"):
        k_et = KAYNAK / "labels" / bolum
        k_im = KAYNAK / "images" / bolum
        if not k_et.is_dir():
            continue
        h_et = HEDEF / "labels" / bolum
        h_im = HEDEF / "images" / bolum
        h_et.mkdir(parents=True, exist_ok=True)
        h_im.mkdir(parents=True, exist_ok=True)
        for et in sorted(k_et.glob("*.txt")):
            satirlar = et.read_text(encoding="utf-8").splitlines()
            yeni = etiket_donustur(satirlar, once, sonra)
            (h_et / et.name).write_text("\n".join(yeni) + ("\n" if yeni else ""),
                                        encoding="utf-8")
            for uzanti in (".jpg", ".png", ".jpeg"):
                kaynak_im = k_im / (et.stem + uzanti)
                if kaynak_im.is_file():
                    hedef_im = h_im / kaynak_im.name
                    if not hedef_im.exists():
                        try:
                            hedef_im.symlink_to(kaynak_im)
                        except OSError:
                            shutil.copy2(kaynak_im, hedef_im)
                    break
            n_kare += 1
        print(f"[{bolum}] {len(list(h_et.glob('*.txt')))} etiket", flush=True)

    (HEDEF / "data.yaml").write_text(
        DATA_YAML.format(hedef=str(HEDEF)), encoding="utf-8")

    print(f"\n{n_kare} kare islendi -> {HEDEF}")
    print("\nSINIF DAGILIMI (poligon sayisi)")
    print(f"{'11 sinif ONCE':>28s}    {'2 sinif SONRA':>18s}")
    adlar = {0: "traversable", 1: "blocked", 2: "water", 3: "bina_hasarsiz",
             4: "bina_hafif", 5: "bina_agir", 6: "bina_yikik", 7: "arac",
             8: "agac", 9: "havuz"}
    for k in sorted(once):
        print(f"  {k} {adlar.get(k, '?'):24s} {once[k]:>8d}"
              f"   ->  {ESLEME.get(k, '-')}")
    print(f"\n  yeni 0 traversable : {sonra[0]:>8d}")
    print(f"  yeni 1 blocked     : {sonra[1]:>8d}")
    eski_engel = once[1]
    print(f"\n  ENGEL POLIGONU: {eski_engel} -> {sonra[1]}  "
          f"({sonra[1] / max(1, eski_engel):.1f}x)")


if __name__ == "__main__":
    main()
