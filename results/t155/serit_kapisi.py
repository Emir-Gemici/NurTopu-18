"""T155 KAPI OLCUMU — yayinlanan `road` dogrulugu + BOZULMAMA (ON_KAYIT SS17).

NE OLCER
  Yer gercekli 15 sentetik sahnede (T151 kumesi, `results/t151/iki_yol_kiyasi.py`
  ile AYNI uretec: `codes/test_rota_sentetik.sahne_uret`) uretim yolunun
  (`rpi_inference.analyze_path`) YAYINLADIGI serit numarasini yer gercegiyle
  kiyaslar ve ayni kosumda `rota_bul` referansini yazar.

  Ayrica BOZULMAMA icin her sahnenin waypoint listesini, ret sebebini ve
  guvenini KANONIK JSON olarak doker. Iki KOK (once/sonra) icin ayri kosulur
  ve ciktilar BAYT-ES kiyaslanir; kiyasi `bozulmama_kiyas.py` yapar.

  MODEL KOSMAZ, GPU KULLANMAZ — sahneler sentetiktir, maske kusursuzdur.

KULLANIM
  python serit_kapisi.py --kok <depo koku> --json <cikti.json>

⚠ SINIR (T151'den devralinir, raporda AYNEN durur): sahneler SENTETIKtir ve
  maske KUSURSUZdur. Bu bir ALGI olcumu degil MANTIK olcumudur; gercek
  karelerde oran BU DEGILDIR.
"""
import argparse
import json
import sys
from pathlib import Path


def kur(kok):
    kok = Path(kok)
    for alt in ("codes", "simulation/scripts"):
        sys.path.insert(0, str(kok / alt))
    return kok


def olc(kok):
    import arena
    from costmap_path_finder import rota_bul
    from rpi_inference import analyze_path
    import test_rota_sentetik as TRS

    satirlar = []
    for hid in range(1, arena.HARITA_N + 1):
        for sen in arena.SCENARIOS:
            H, zemin, engel, baslangic, hedef = TRS.sahne_uret(hid, sen)
            rb = rota_bul({0: zemin, 1: engel}, mpp=TRS.MPP,
                          baslangic=baslangic, hedef=hedef, plan=True)
            yol, guven, wps, red, olcum = analyze_path(
                zemin, icerik=None, engel_mask=engel, mpp=TRS.MPP,
                return_reason=True, return_olcum=True)
            satirlar.append({
                "harita": hid,
                "senaryo": sen,
                "yer_gercegi": int(H["open"]),
                # --- KAPI 1: yayinlanan numara ---
                "yayinlanan_road": yol,
                "rota_bul_yol_no": rb["yol_no"],
                # --- KAPI 2: BOZULMAMA (bayt-es kiyaslanacak alanlar) ---
                "waypointler": [[int(x), int(y)] for x, y in wps],
                "ret": (list(red) if isinstance(red, tuple) else red),
                "guven": repr(float(guven)),
                # --- TANI (kiyasa girmez, gorunur olsun diye) ---
                "tani_darbogaz_serit": (olcum or {}).get("darbogaz_serit"),
                "tani_seritler": list((olcum or {}).get("seritler") or []),
                "tani_darbogaz_xy": list((olcum or {}).get("darbogaz_xy") or []),
                "tani_darbogaz_px": repr(float((olcum or {}).get("darbogaz_px"))
                                         if olcum else 0.0),
            })
    return satirlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", required=True)
    ap.add_argument("--json", required=True)
    args = ap.parse_args()

    kur(args.kok)
    satirlar = olc(args.kok)
    dogru = sum(1 for s in satirlar if s["yayinlanan_road"] == s["yer_gercegi"])
    rb_dogru = sum(1 for s in satirlar
                   if s["rota_bul_yol_no"] == s["yer_gercegi"])
    ozet = {"n": len(satirlar), "yayinlanan_dogru": dogru,
            "rota_bul_dogru": rb_dogru}

    print(f"KOK: {args.kok}")
    print(f"{'har':>3} {'senaryo':>8} {'gercek':>6} {'yayin':>6} {'rota_bul':>8} "
          f"{'wp':>4} {'ret':>6}  {'tani_darbogaz':>13} {'seritler':>16}")
    for s in satirlar:
        r = s["ret"]
        print(f"{s['harita']:>3} {s['senaryo']:>8} {s['yer_gercegi']:>6} "
              f"{str(s['yayinlanan_road']):>6} {str(s['rota_bul_yol_no']):>8} "
              f"{len(s['waypointler']):>4} "
              f"{(r[0] if isinstance(r, list) else '-'):>6}  "
              f"{str(s['tani_darbogaz_serit']):>13} {str(s['tani_seritler']):>16}")
    print("-" * 88)
    print(json.dumps(ozet, ensure_ascii=False))

    Path(args.json).write_text(
        json.dumps({"ozet": ozet, "satirlar": satirlar},
                   ensure_ascii=False, indent=1, sort_keys=True),
        encoding="utf-8")
    print(f"yazildi: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
