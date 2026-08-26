"""142 — GECE ADAY OLCUMU: ON_KAYIT §4 kapilarini TEK komutla kosar ve hukmu yazar.

  python 142_gece_olcum.py --agirlik <best.pt> --ad gece_v2_v35taban

Adimlar (hepsi mevcut olcum betiklerini cagirir / ice aktarir; yeni olcut UYDURULMAZ):
  1. 65_kabul_denetcisi  -> K0..K5, VERDIKT, K1 sayisi
  2. 109 model_olc       -> cati_kacak_ort, kaplama67_icerik_medyan, zemin_maskesi_reddi (67'de red), figur_zemin_orani
  3. 126 gece_kumesi     -> 29 TEST karesi (dataset/dji_kirsal_0038_bolum/images/test): ROTA / MASKE_YOK / UC_BANT
  4. Kapi degerlendirmesi ON_KAYIT §4 (a)+(b) sabitleriyle — sabitler BURADA yazilidir, sonuca gore degismez.
  5. (b-ek2, T152 · ON_KAYIT §11(2)) --etiket-dizin verilirse: her ROTA karesinde rota CIZGISI
     (ardisik waypoint'leri birlestiren 1 px polylines, tuval koordinati) elle etiketin uc durumlu
     maskesiyle kesistirilir: sinif 0 ustundeki pay >= 0,90 VE sinif 1 ustunde 0 waypoint; aksi
     hâlde kare YANLIS GUZERGAH. Kapi: YANLIS GUZERGAH == 0. Etiketsiz pay yalniz raporlanir.
     --etiket-dizin verilmezse davranis ve JSON ciktisi BAYT-ES aynidir.
"""
from __future__ import annotations

import argparse
import importlib.util
import io
import json
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
PY = sys.executable
OLCUM = KOK / "scripts" / "olcum"
CIKTI = KOK / "results" / "gece_20260826"
TEST29 = KOK / "dataset" / "dji_kirsal_0038_bolum" / "images" / "test"

# ON_KAYIT §4 — sonuc gorulmeden yazildi (2026-08-26 01:0x)
KAPI = {
    "verdikt": True, "K1_min": 230, "red67_maks": 5, "cati_kacagi_maks": 0.10,   # (a)
    "rota_test29_min": 10, "maske_yok_test29_maks": 10,                           # (b)  v35 tabani ROTA 6 · MASKE_YOK 16
}
TABAN_V35 = {"rota": 6, "maske_yok": 16, "uc_bant": 7, "figur_zemin": 0.1508, "kaplama67": 0.5076, "cati": 0.043}
# ON_KAYIT §11(2) — T152 "rota yol ustunde mi" (b-ek2). TANIM `rota_yol_olcumu.py`de TEK yerde
# durur (K6 / 61-65 zinciri de ayni tanimi kullanir); burada yalniz ad baglanir — davranis ve
# JSON ciktisi bayt-es aynidir (test_t152 ve K6 rapor kaniti).


def _rota_yol_modulu():
    spec = importlib.util.spec_from_file_location("rota_yol_olcumu", OLCUM / "rota_yol_olcumu.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_RYO = _rota_yol_modulu()
KAPI_B_EK2 = _RYO.KAPI_B_EK2
ETIKETSIZ, SINIF0, SINIF1 = _RYO.ETIKETSIZ, _RYO.SINIF0, _RYO.SINIF1
uc_durum_maske = _RYO.uc_durum_maske
rota_yol_olc = _RYO.rota_yol_olc
yanlis_guzergah_mi = _RYO.yanlis_guzergah_mi


def rota_yol_kapisi(kareler126: list, etiket_dizin: Path, kare_dizin: Path, kapi: dict = KAPI_B_EK2) -> dict:
    """126 ciktisindaki her ROTA karesi (olceksiz_sebep None) icin rota_yol_olc + hukum."""
    import cv2
    satirlar = []
    for s in kareler126:
        if s.get("olceksiz_sebep") is not None:
            continue
        wps = s.get("olceksiz_wps")
        if wps is None:
            raise SystemExit(f"{s['kare']}: 126 ciktisinda 'olceksiz_wps' yok — 126'yi (T152 sonrasi) yeniden kos")
        img = cv2.imread(str(kare_dizin / s["kare"]))
        if img is None:
            raise SystemExit(f"kare okunamadi: {kare_dizin / s['kare']}")
        h, w = img.shape[:2]
        uc = uc_durum_maske(etiket_dizin / (Path(s["kare"]).stem + ".txt"), h, w)
        o = rota_yol_olc(wps, uc)
        o["etiket_var"] = bool((uc > 0).any())
        o["yanlis_guzergah"] = yanlis_guzergah_mi(o, kapi)
        satirlar.append({"kare": s["kare"], **o})
    n_y = sum(1 for r in satirlar if r["yanlis_guzergah"])
    return {"kapi": dict(kapi), "etiket_dizin": str(etiket_dizin), "rota_kare": len(satirlar),
            "yanlis_guzergah": n_y, "yanlis_kareler": [r["kare"] for r in satirlar if r["yanlis_guzergah"]],
            "rota_yol": satirlar}


def _modul(ad: str):
    spec = importlib.util.spec_from_file_location(ad, OLCUM / f"{ad}.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def adim1_kabul(agirlik: Path, ad: str) -> dict:
    r = subprocess.run([PY, str(OLCUM / "65_kabul_denetcisi.py"), "--model", str(agirlik), "--ad", ad],
                       cwd=str(KOK), text=True, encoding="utf-8", errors="replace", capture_output=True)
    (CIKTI / f"{ad}_65.log").write_text(r.stdout + "\n--stderr--\n" + r.stderr, encoding="utf-8")
    cj = OLCUM / "results" / "t63" / f"{ad}_kabul_verdikt.json"
    d = json.load(io.open(cj, encoding="utf-8"))
    k1 = int(str(d["olcum"]["K1_rota"]).split("/")[0])
    return {"verdikt": bool(d["verdikt"]), "K1": k1, "gecti": d["gecti"], "K0_figur_orani": d["olcum"]["K0"].get("figur_orani"),
            "json": str(cj), "exit": r.returncode}


def adim2_109(agirlik: Path) -> dict:
    m = _modul("109_t122_kiyas")
    import cv2
    from ultralytics import YOLO
    catilar = m.cati_kareleri()
    diskler = json.load(io.open(m.DISKLER, encoding="utf-8"))["kareler"]
    kareler67 = {p.relative_to(m.KARE_KOK).as_posix(): cv2.imread(str(p)) for p in sorted(m.KARE_KOK.rglob("*.jpg"))}
    figur = cv2.imread(str(m.FIGUR))
    model = YOLO(str(agirlik), task="segment")
    o = m.model_olc(model, catilar, diskler, kareler67, figur)
    o.pop("_figur_maske", None)
    return o


def adim3_test29(agirlik: Path, ad: str) -> dict:
    dosya = f"{ad}_test29.json"
    r = subprocess.run([PY, str(OLCUM / "126_t138_gece_kumesi.py"), "--kareler", str(TEST29), "--modeller", str(Path(agirlik).resolve()),
                        "--cikti", str(CIKTI), "--dosya", dosya,
                        "--etiket", f"GECE {ad} · 0038 TEK-konum TEST (29 kare) — ON_KAYIT §2"],
                       cwd=str(KOK), text=True, encoding="utf-8", errors="replace", capture_output=True)
    (CIKTI / f"{ad}_126.log").write_text(r.stdout + "\n--stderr--\n" + r.stderr, encoding="utf-8")
    d = json.load(io.open(CIKTI / dosya, encoding="utf-8"))
    v = list(d["modeller"].values())[0]
    seb = v["sebep_olceksiz"]
    return {"n": v["n"], "rota": int(v["rota_olceksiz"]), "maske_yok": int(seb.get("MASKE_YOK", 0)),
            "uc_bant": int(seb.get("UC_BANT_TEMAS_YOK", 0)), "sebep": seb, "json": str(CIKTI / dosya), "exit": r.returncode}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agirlik", type=Path, required=True)
    ap.add_argument("--ad", required=True)
    ap.add_argument("--atla-kabul", action="store_true")
    ap.add_argument("--test-dizin", type=Path, default=None, help="TEST29 yerine (ON_KAYIT §10 v2 referansi)")
    ap.add_argument("--tavan", type=Path, default=None, help="etiket tavani JSON (varsayilan test29_etiket_tavani.json)")
    ap.add_argument("--etiket-dizin", type=Path, default=None,
                    help="(b-ek2, ON_KAYIT §11) YOLO etiket dizini (labels/test); verilirse 'rota yol ustunde' kapisi kosar")
    ap.add_argument("--cikti", type=Path, default=None, help="cikti dizini (varsayilan results/gece_20260826)")
    a = ap.parse_args()
    global TEST29, CIKTI
    if a.test_dizin is not None:
        TEST29 = a.test_dizin
    if a.cikti is not None:
        CIKTI = a.cikti
    CIKTI.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sonuc = {"agirlik": str(a.agirlik), "ad": a.ad, "kapi_sabitleri": KAPI, "taban_v35": TABAN_V35,
             "test_dizin": str(TEST29), "tavan": str(a.tavan) if a.tavan else "varsayilan"}
    if not a.atla_kabul:
        sonuc["kabul"] = adim1_kabul(a.agirlik, a.ad)
        print("[1] kabul", json.dumps({k: v for k, v in sonuc["kabul"].items() if k != "json"}), flush=True)
    sonuc["k109"] = adim2_109(a.agirlik)
    print("[2] 109", json.dumps({k: v for k, v in sonuc["k109"].items() if k != "yol"}), flush=True)
    sonuc["test29"] = adim3_test29(a.agirlik, a.ad)
    print("[3] test29", json.dumps({k: v for k, v in sonuc["test29"].items() if k != "json"}), flush=True)

    # (b-ek) ON_KAYIT §4(b-ek): elle etiket tavanina gore TP / FP (yalniz SIKILASTIRIR)
    tavan_yolu = a.tavan if a.tavan is not None else CIKTI / "test29_etiket_tavani.json"
    if tavan_yolu.is_file():
        tavan = {s["kare"]: s["rota"] for s in json.load(io.open(tavan_yolu, encoding="utf-8"))["kareler"]}
        d126 = json.load(io.open(sonuc["test29"]["json"], encoding="utf-8"))
        v = list(d126["modeller"].values())[0]
        tp = fp = fn = 0
        fp_kareler = []
        for s in v["kareler"]:
            model_rota = s["olceksiz_sebep"] is None
            etiket_rota = tavan.get(s["kare"])
            if model_rota and etiket_rota:
                tp += 1
            elif model_rota and etiket_rota is False:
                fp += 1
                fp_kareler.append(s["kare"])
            elif (not model_rota) and etiket_rota:
                fn += 1
        sonuc["test29_tavan"] = {"tavan_rota": sum(1 for x in tavan.values() if x), "TP": tp, "FP": fp, "FN": fn,
                                 "fp_kareler": fp_kareler}
        print("[3-ek] tavan", json.dumps(sonuc["test29_tavan"]), flush=True)

    # (b-ek2) ON_KAYIT §11(2): rota YOL USTUNDE mi (T152) — yalniz --etiket-dizin verilince
    if a.etiket_dizin is not None:
        d126 = json.load(io.open(sonuc["test29"]["json"], encoding="utf-8"))
        v = list(d126["modeller"].values())[0]
        sonuc["kapi_sabitleri_b_ek2"] = KAPI_B_EK2
        sonuc["rota_yol"] = rota_yol_kapisi(v["kareler"], a.etiket_dizin, TEST29)
        print("[3-ek2] rota_yol", json.dumps({k: vv for k, vv in sonuc["rota_yol"].items() if k != "rota_yol"},
                                             ensure_ascii=False), flush=True)
        for r in sonuc["rota_yol"]["rota_yol"]:
            print(f"        {r['kare']}: yol {r['yol_payi']:.2f} etiketsiz {r['etiketsiz_payi']:.2f} "
                  f"engel_wp {r['engel_wp']}/{r['wp']} -> {'YANLIS GUZERGAH' if r['yanlis_guzergah'] else 'yol ustunde'}")

    k = sonuc.get("kabul", {})
    a_kapi = {
        "verdikt": (k.get("verdikt") is True) if k else None,
        "K1>=230": (k.get("K1", 0) >= KAPI["K1_min"]) if k else None,
        "red67<=5": sonuc["k109"]["zemin_maskesi_reddi"] <= KAPI["red67_maks"],
        "cati<=0,10": sonuc["k109"]["cati_kacak_ort"] <= KAPI["cati_kacagi_maks"],
    }
    b_kapi = {
        "rota_test29>=10": sonuc["test29"]["rota"] >= KAPI["rota_test29_min"],
        "maske_yok_test29<=10": sonuc["test29"]["maske_yok"] <= KAPI["maske_yok_test29_maks"],
    }
    if "test29_tavan" in sonuc:
        b_kapi["FP_test29<=1"] = sonuc["test29_tavan"]["FP"] <= 1
    if "rota_yol" in sonuc:
        b_kapi["yanlis_guzergah==0"] = sonuc["rota_yol"]["yanlis_guzergah"] == 0
    sonuc["kapi_a"] = a_kapi
    sonuc["kapi_b"] = b_kapi
    sonuc["a_gecti"] = all(v is True for v in a_kapi.values())
    sonuc["b_gecti"] = all(b_kapi.values())
    sonuc["terfi_adayi"] = sonuc["a_gecti"] and sonuc["b_gecti"]
    sonuc["saniye"] = round(time.time() - t0)
    (CIKTI / f"{a.ad}_olcum.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("\n=== HUKUM (ON_KAYIT §4) ===")
    for kk, vv in {**a_kapi, **b_kapi}.items():
        print(f"  {kk:24s} {'GECTI' if vv else ('OLCULMEDI' if vv is None else 'DUSTU')}")
    print(f"  (a) {'GECTI' if sonuc['a_gecti'] else 'DUSTU'} · (b) {'GECTI' if sonuc['b_gecti'] else 'DUSTU'} · "
          f"TERFI ADAYI: {sonuc['terfi_adayi']}")
    print(f"  bilgi: figur_zemin {sonuc['k109']['figur_zemin_orani']} (v35 0,1508) · kaplama67 "
          f"{sonuc['k109']['kaplama67_icerik_medyan']} (v35 0,5076) · test29 sebep {sonuc['test29']['sebep']}")


if __name__ == "__main__":
    main()
