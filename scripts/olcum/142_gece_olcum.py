"""142 — GECE ADAY OLCUMU: ON_KAYIT §4 kapilarini TEK komutla kosar ve hukmu yazar.

  python 142_gece_olcum.py --agirlik <best.pt> --ad gece_v2_v35taban

Adimlar (hepsi mevcut olcum betiklerini cagirir / ice aktarir; yeni olcut UYDURULMAZ):
  1. 65_kabul_denetcisi  -> K0..K5, VERDIKT, K1 sayisi
  2. 109 model_olc       -> cati_kacak_ort, kaplama67_icerik_medyan, zemin_maskesi_reddi (67'de red), figur_zemin_orani
  3. 126 gece_kumesi     -> 29 TEST karesi (dataset/dji_kirsal_0038_bolum/images/test): ROTA / MASKE_YOK / UC_BANT
  4. Kapi degerlendirmesi ON_KAYIT §4 (a)+(b) sabitleriyle — sabitler BURADA yazilidir, sonuca gore degismez.
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
    a = ap.parse_args()
    CIKTI.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sonuc = {"agirlik": str(a.agirlik), "ad": a.ad, "kapi_sabitleri": KAPI, "taban_v35": TABAN_V35}
    if not a.atla_kabul:
        sonuc["kabul"] = adim1_kabul(a.agirlik, a.ad)
        print("[1] kabul", json.dumps({k: v for k, v in sonuc["kabul"].items() if k != "json"}), flush=True)
    sonuc["k109"] = adim2_109(a.agirlik)
    print("[2] 109", json.dumps({k: v for k, v in sonuc["k109"].items() if k != "yol"}), flush=True)
    sonuc["test29"] = adim3_test29(a.agirlik, a.ad)
    print("[3] test29", json.dumps({k: v for k, v in sonuc["test29"].items() if k != "json"}), flush=True)

    # (b-ek) ON_KAYIT §4(b-ek): elle etiket tavanina gore TP / FP (yalniz SIKILASTIRIR)
    tavan_yolu = CIKTI / "test29_etiket_tavani.json"
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
