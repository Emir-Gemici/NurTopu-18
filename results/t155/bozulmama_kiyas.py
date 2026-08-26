"""T155 BOZULMAMA KIYASI (ON_KAYIT SS17 ek sart) — BAYT-ES denetim.

`serit_kapisi.py` iki KOK icin kosulur (once=master, sonra=T155). Bu betik
yalniz DEGISMESI YASAK alanlari kiyaslar ve kiyasi BAYT duzeyinde yapar:

    waypointler · ret · guven · tani_darbogaz_serit · tani_seritler
    · tani_darbogaz_xy · tani_darbogaz_px

DEGISMESI BEKLENEN tek alan `yayinlanan_road`tur; o ayrica raporlanir.

Cikis kodu KANIT DEGILDIR (CLAUDE.md): ham fark listesi basilir.
"""
import argparse
import json
import sys
from pathlib import Path

DEGISMEZ = ("waypointler", "ret", "guven", "tani_darbogaz_serit",
            "tani_seritler", "tani_darbogaz_xy", "tani_darbogaz_px")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", required=True)
    ap.add_argument("--sonra", required=True)
    args = ap.parse_args()

    a = json.loads(Path(args.once).read_text(encoding="utf-8"))["satirlar"]
    b = json.loads(Path(args.sonra).read_text(encoding="utf-8"))["satirlar"]
    if len(a) != len(b):
        print(f"SAHNE SAYISI FARKLI: {len(a)} vs {len(b)}")
        return 1

    bozulan = []
    degisen_road = []
    for x, y in zip(a, b):
        ad = f"{x['harita']}/{x['senaryo']}"
        assert (x["harita"], x["senaryo"]) == (y["harita"], y["senaryo"])
        for alan in DEGISMEZ:
            # BAYT-ES: kanonik JSON serilestirmesi uzerinden karsilastir.
            sa = json.dumps(x[alan], ensure_ascii=False, sort_keys=True)
            sb = json.dumps(y[alan], ensure_ascii=False, sort_keys=True)
            if sa.encode("utf-8") != sb.encode("utf-8"):
                bozulan.append((ad, alan, sa, sb))
        if x["yayinlanan_road"] != y["yayinlanan_road"]:
            degisen_road.append(
                (ad, x["yer_gercegi"], x["yayinlanan_road"],
                 y["yayinlanan_road"]))

    n_wp = sum(len(s["waypointler"]) for s in b)
    print(f"sahne              : {len(b)}")
    print(f"kiyaslanan waypoint: {n_wp}")
    print(f"degismez alanlar   : {', '.join(DEGISMEZ)}")
    print()
    print(f"BOZULAN ALAN       : {len(bozulan)}")
    for ad, alan, sa, sb in bozulan:
        print(f"  {ad:>10} {alan}: {sa}  ->  {sb}")
    print()
    print(f"yayinlanan_road DEGISEN sahne: {len(degisen_road)}")
    print(f"  {'sahne':>10} {'gercek':>6} {'once':>5} {'sonra':>5}  sonuc")
    for ad, gt, o, s in degisen_road:
        durum = ("DUZELDI" if s == gt else
                 ("BOZULDU" if o == gt else "HALA YANLIS"))
        print(f"  {ad:>10} {gt:>6} {o:>5} {s:>5}  {durum}")

    o_dogru = sum(1 for s in a if s["yayinlanan_road"] == s["yer_gercegi"])
    s_dogru = sum(1 for s in b if s["yayinlanan_road"] == s["yer_gercegi"])
    print()
    print(f"yayinlanan road dogrulugu: ONCE {o_dogru}/{len(a)}  "
          f"SONRA {s_dogru}/{len(b)}")
    print(f"KAPI (>= 14/15)          : "
          f"{'GECTI' if s_dogru >= 14 else 'KALDI'}")
    print(f"BOZULMAMA                : "
          f"{'GECTI (bayt-es)' if not bozulan else 'KALDI'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
