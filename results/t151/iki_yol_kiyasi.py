"""T151 OLCUM — IKI KARAR YOLU, AYNI MASKE, YER GERCEKLI 15 SENTETIK SAHNE.

NEDEN. T151 sorusu "hangi yol dogru" degil "iki yol ayni maskede ayni seyi mi
soyluyor" sorusudur. Repoda ikisini AYNI karede kiyaslayan tek kayit D-145'tir
(n=260, sentetik_arena_kadraj_t66) ve orada YER GERCEGI YOKTUR — yalnizca
cevrilme sayilir. `codes/test_rota_sentetik.py` ise yer gercekli 15 sahne
uretir (arena.harita -> H["open"] GIZLI cevap) ve YALNIZ `rota_bul`u sinar.

BU BETIK MODEL KOSMAZ (GPU yok). Sahneleri `test_rota_sentetik.sahne_uret` ile
BIREBIR ayni sekilde uretir, AYNI maske sozlugunu HEM `rota_bul`a HEM
`analyze_path`e verir ve ikisinin cevabini yer gercegiyle kiyaslar.

⚠ SINIR — RAPORDA AYNEN YAZILIR:
  1. Sahneler SENTETIK ve maske KUSURSUZDUR. Bu bir ALGI olcumu degil MANTIK
     olcumudur; gercek karelerde iki yolun ayrisma orani BU DEGILDIR.
  2. `rota_bul` KB/HB tohumunu ARGUMAN olarak alir (`baslangic`, `hedef`);
     `analyze_path` tohum ARGUMANI KABUL ETMEZ — alt/ust bantlari icerik
     kutusundan kendi kurar. Yani ikisi ayni girdiyi almiyor: bu esitsizlik
     olcumun kusuru degil, olculen SOZLESME FARKININ ta kendisidir.
  3. `analyze_path` bu sahnede `icerik=None` (tuval = icerik) ile kosar; sahne
     letterbox degildir, bu yuzden T135 letterbox suphesi devrede degildir.
"""
import json
import sys
from pathlib import Path

import numpy as np

KOK = Path(r"O:\navitas")
sys.path.insert(0, str(KOK / "codes"))
sys.path.insert(0, str(KOK / "simulation" / "scripts"))

import arena  # noqa: E402
from costmap_path_finder import rota_bul  # noqa: E402
from rpi_inference import analyze_path  # noqa: E402
from karar_sozlesmesi import ZEMIN_KAPLAMA_TAVANI  # noqa: E402

sys.path.insert(0, str(KOK / "codes"))
import test_rota_sentetik as TRS  # noqa: E402


def _guzergah_maskesi(H, road, sekil, yaricap_m=2.0):
    """Yer gercegi guzergah poligonunu KALIN cizgi olarak rasterlestir.

    T152'nin `--etiket-dizin` yol_payi kapisiyla AYNI fikir: bir waypoint'in
    hangi guzergahin uzerinde oldugu, o guzergahin ekseninden `yaricap_m`
    icinde olup olmadigiyla belirlenir. Yaricap arena yol yariciapindan
    (`world_generator.DIFF` yol genisligi) DEGIL, olcumun kendi toleransindan
    gelir ve raporda ACIKCA yazilir.
    """
    import cv2
    m = np.zeros(sekil, np.uint8)
    pts = np.array([TRS._px(p) for p in H["paths"][road]], np.int32)
    kal = max(1, int(round(2 * yaricap_m / TRS.MPP)))
    cv2.polylines(m, [pts], False, 1, kal)
    return m


def _rota_hangi_guzergahta(H, wps, sekil, yaricap_m=2.0):
    """Her guzergah icin: waypointlerin yuzde kaci o guzergahin bandinda."""
    if not wps:
        return {}
    paylar = {}
    for road in (1, 2, 3):
        m = _guzergah_maskesi(H, road, sekil, yaricap_m)
        icinde = sum(1 for (x, y) in wps
                     if 0 <= int(y) < sekil[0] and 0 <= int(x) < sekil[1]
                     and m[int(y), int(x)] > 0)
        paylar[road] = round(icinde / len(wps), 3)
    return paylar


def olc():
    satirlar = []
    for harita_id in range(1, arena.HARITA_N + 1):
        for senaryo in arena.SCENARIOS:
            H, zemin, engel, baslangic, hedef = TRS.sahne_uret(harita_id, senaryo)
            maskeler = {0: zemin, 1: engel}

            rb = rota_bul(maskeler, mpp=TRS.MPP, baslangic=baslangic,
                          hedef=hedef, plan=True)

            ap = analyze_path(zemin, icerik=None, engel_mask=engel,
                              mpp=TRS.MPP, return_reason=True,
                              return_olcum=True)
            ap_yol, ap_guven, ap_wps, ap_red, ap_olcum = ap

            kaplama = float((zemin > 0).sum()) / float(zemin.size)

            satirlar.append({
                "harita": harita_id,
                "senaryo": senaryo,
                "yer_gercegi": int(H["open"]),
                "zemin_kaplama": round(kaplama, 4),
                "rota_bul": {
                    "durum": rb["durum"],
                    "yol_no": rb["yol_no"],
                    "guven": round(float(rb["guven"]), 4),
                    "n_waypoint": len(rb["waypoints_px"]),
                    "n_aday": len(rb["adaylar"]),
                },
                "analyze_path": {
                    "yol": ap_yol,
                    "guven": round(float(ap_guven), 4),
                    "n_waypoint": len(ap_wps),
                    "red": (list(ap_red) if isinstance(ap_red, tuple) else ap_red),
                    "darbogaz_px": (ap_olcum or {}).get("darbogaz_px"),
                    "baskin_serit": (ap_olcum or {}).get("baskin_serit"),
                    "seritler": list((ap_olcum or {}).get("seritler") or []),
                },
                "rota_guzergah_payi": {
                    "analyze_path": _rota_hangi_guzergahta(H, ap_wps, zemin.shape),
                    "rota_bul": _rota_hangi_guzergahta(
                        H, rb["waypoints_px"], zemin.shape),
                },
            })
    return satirlar


def ozetle(satirlar):
    n = len(satirlar)
    rb_dogru = sum(1 for s in satirlar if s["rota_bul"]["yol_no"] == s["yer_gercegi"])
    ap_dogru = sum(1 for s in satirlar if s["analyze_path"]["yol"] == s["yer_gercegi"])
    rb_karar = sum(1 for s in satirlar if s["rota_bul"]["yol_no"] is not None)
    ap_karar = sum(1 for s in satirlar if s["analyze_path"]["yol"] is not None)
    ikisi_karar = [s for s in satirlar
                   if s["rota_bul"]["yol_no"] is not None
                   and s["analyze_path"]["yol"] is not None]
    uyusan = sum(1 for s in ikisi_karar
                 if s["rota_bul"]["yol_no"] == s["analyze_path"]["yol"])
    rb_yanlis = sum(1 for s in satirlar
                    if s["rota_bul"]["yol_no"] is not None
                    and s["rota_bul"]["yol_no"] != s["yer_gercegi"])
    ap_yanlis = sum(1 for s in satirlar
                    if s["analyze_path"]["yol"] is not None
                    and s["analyze_path"]["yol"] != s["yer_gercegi"])
    redler = {}
    for s in satirlar:
        r = s["analyze_path"]["red"]
        kod = r[0] if isinstance(r, list) else (r if r else "-")
        redler[kod] = redler.get(kod, 0) + 1
    durumlar = {}
    for s in satirlar:
        d = s["rota_bul"]["durum"]
        durumlar[d] = durumlar.get(d, 0) + 1
    # ROTA GEOMETRISI: yayinlanan etiket degil, waypointlerin FIZIKSEL yeri.
    ap_gercek_guzergahta = 0
    rb_gercek_guzergahta = 0
    for s in satirlar:
        g = str(s["yer_gercegi"])
        pa = s["rota_guzergah_payi"]["analyze_path"]
        pb = s["rota_guzergah_payi"]["rota_bul"]
        if pa and max(pa, key=pa.get) == s["yer_gercegi"] and pa[s["yer_gercegi"]] >= 0.5:
            ap_gercek_guzergahta += 1
        if pb and max(pb, key=pb.get) == s["yer_gercegi"] and pb[s["yer_gercegi"]] >= 0.5:
            rb_gercek_guzergahta += 1
        del g
    return {
        "n_sahne": n,
        "analyze_path_rotasi_ACIK_guzergahta": ap_gercek_guzergahta,
        "rota_bul_rotasi_ACIK_guzergahta": rb_gercek_guzergahta,
        "zemin_kaplama_tavani": ZEMIN_KAPLAMA_TAVANI,
        "zemin_kaplama_min": min(s["zemin_kaplama"] for s in satirlar),
        "zemin_kaplama_max": max(s["zemin_kaplama"] for s in satirlar),
        "rota_bul_karar_verdi": rb_karar,
        "rota_bul_dogru": rb_dogru,
        "rota_bul_yanlis_guzergah": rb_yanlis,
        "analyze_path_karar_verdi": ap_karar,
        "analyze_path_dogru": ap_dogru,
        "analyze_path_yanlis_guzergah": ap_yanlis,
        "ikisi_de_karar_verdi": len(ikisi_karar),
        "ikisi_karar_verdiginde_uyusan": uyusan,
        "rota_bul_durum_dagilimi": durumlar,
        "analyze_path_ret_dagilimi": redler,
    }


def main():
    satirlar = olc()
    ozet = ozetle(satirlar)
    cikti = {"olcum": "T151 iki karar yolu, ayni maske, yer gercekli sentetik arena",
             "kume": "simulation/scripts/arena.py — 5 harita x 3 senaryo",
             "mpp": TRS.MPP, "tuval": TRS.N,
             "ozet": ozet, "satirlar": satirlar}
    yol = Path(__file__).parent / "iki_yol_kiyasi.json"
    yol.write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'har':>3} {'senaryo':>8} {'gercek':>6} | "
          f"{'rota_bul':>9} {'durum':>18} | {'analyze':>7} {'ret':>22}")
    for s in satirlar:
        r = s["analyze_path"]["red"]
        kod = r[0] if isinstance(r, list) else "-"
        print(f"{s['harita']:>3} {s['senaryo']:>8} {s['yer_gercegi']:>6} | "
              f"{str(s['rota_bul']['yol_no']):>9} {s['rota_bul']['durum']:>18} | "
              f"{str(s['analyze_path']['yol']):>7} {kod:>22}")
    print("-" * 90)
    print(json.dumps(ozet, ensure_ascii=False, indent=1))
    print(f"\nyazildi: {yol}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
