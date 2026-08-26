"""ON_KAYIT §18-A — GUVEN ESIGI (conf) SUPURMESI · SADECE OLCUM.

🔴 BU BETIK KOD/SOZLESME ESIGI DEGISTIRMEZ, defter yazmaz, model terfi ettirmez.
   Uretim esigi 0,30'dur ve bu turda OYLE KALIR (ON_KAYIT §18-A). Burada yalniz
   "baska esiklerde ne olurdu" OLCULUR; oneri kurali ON KAYITTA yazilidir ve
   sonuca gore degistirilmez.

ZINCIR — 126'nin AYNISI (kendi kopyasi DEGIL, 126 dogrudan cagrilir):
    _preprocess -> predict(imgsz=INFER_SIZE, conf=E) -> get_masks
    -> _maskeleri_icerige_kirp -> analyze_path(mpp=None, return_reason,
       return_olcum) + olceksiz_wps
Analiz kismi da kopyalanmaz: TP/FP/FN tanimi 142'nin tavan blogunun aynisi,
"YANLIS GUZERGAH" tanimi `142_gece_olcum.rota_yol_kapisi` (dolayisiyla
`rota_yol_olcumu.py`) — tanim tek yerde yasar (D-90 dersi).

GERCEK KAYIP (ON_KAYIT §18 basligi): model rota URETMEZ ama ELLE ETIKET TAVANI
uretir. Iki bilesene ayrilir: model MASKE_YOK (MODEL KORLUGU) ve model
UC_BANT_TEMAS_YOK (bant kapisi). Ust sinir tavandir; tavan da uretmiyorsa kayip
DEGILDIR.

GPU: tek surec, SIRALI. (PC bugun BSOD verdi — results/pc_cokme_20260826/rapor.md)
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
OLCUM = KOK / "scripts" / "olcum"
BURASI = Path(__file__).resolve().parent
HAM = BURASI / "ham"

# ON_KAYIT §18-A · SONUC GORULMEDEN yazildi. TABAN = 0,30 (uretim).
ESIKLER = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
TABAN_ESIK = 0.30

# ON_KAYIT §18-A oneri kurali — SONUCA GORE DEGISTIRILMEZ.
ONERI = {
    "gercek_kayip_azalma_min": 5,   # (i)  taban 0,30'a gore >= 5 kare azalma
    "fp_test29_maks": 1,            # (iii)
    "fp_val82_maks": 2,             # (iii)
    # (ii) yanlis guzergah ARTMAZ (her iki kumede de) — sayisal esik degil, kiyas
    # (iv) sentetik kabul K0..K6 VERDIKT True — ayri kosum
}

KUMELER = {
    "test29": {
        "kareler": KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "images" / "test",
        "etiket": KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "labels" / "test",
        "tavan": KOK / "results" / "gece_20260826" / "test29_etiket_tavani_v3.json",
    },
    "val82": {
        "kareler": KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "images" / "val",
        "etiket": KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "labels" / "val",
        "tavan": KOK / "results" / "gece_20260826" / "sizinti" / "val82_etiket_tavani.json",
    },
}


def _modul(ad: str, yol: Path):
    for p in (str(OLCUM), str(KOK / "codes")):
        if p not in sys.path:
            sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def kos126(agirlik: Path, kareler: Path, conf: float, dosya: str, log: Path) -> dict:
    """126'yi ALT SUREC olarak kosar (uretim zinciri birebir) ve JSON'unu doner."""
    hedef = HAM / dosya
    if hedef.is_file():
        print(f"    (var) {hedef.name}")
        return json.load(io.open(hedef, encoding="utf-8"))
    r = subprocess.run(
        [sys.executable, str(OLCUM / "126_t138_gece_kumesi.py"),
         "--kareler", str(kareler), "--modeller", str(agirlik),
         "--cikti", str(HAM), "--dosya", dosya, "--conf", str(conf),
         "--etiket", f"ON_KAYIT §18-A conf supurmesi · conf={conf} · {kareler.name}"],
        cwd=str(KOK), text=True, encoding="utf-8", errors="replace",
        capture_output=True)
    log.write_text(r.stdout + "\n--stderr--\n" + r.stderr, encoding="utf-8")
    if r.returncode != 0 or not hedef.is_file():
        raise SystemExit(f"126 cokti (exit {r.returncode}) — bkz {log}")
    return json.load(io.open(hedef, encoding="utf-8"))


def olc(d126: dict, tavan_yolu: Path, etiket_dizin: Path, kare_dizin: Path,
        m142) -> dict:
    v = list(d126["modeller"].values())[0]
    seb = v["sebep_olceksiz"]
    tavan = {s["kare"]: s["rota"]
             for s in json.load(io.open(tavan_yolu, encoding="utf-8"))["kareler"]}

    # TP/FP/FN — 142'nin (b-ek) blogunun AYNI tanimi
    tp = fp = fn = 0
    fp_kareler, kayip_maske_yok, kayip_uc_bant, kayip_diger = [], [], [], []
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
            # GERCEK KAYIP ayristirmasi (tavan uretiyor, model uretmiyor)
            if s["olceksiz_sebep"] == "MASKE_YOK":
                kayip_maske_yok.append(s["kare"])
            elif s["olceksiz_sebep"] == "UC_BANT_TEMAS_YOK":
                kayip_uc_bant.append(s["kare"])
            else:
                kayip_diger.append(s["kare"])

    ry = m142.rota_yol_kapisi(v["kareler"], etiket_dizin, kare_dizin)
    return {
        "n": v["n"], "rota": int(v["rota_olceksiz"]),
        "maske_yok": int(seb.get("MASKE_YOK", 0)),
        "uc_bant": int(seb.get("UC_BANT_TEMAS_YOK", 0)),
        "sebep": seb,
        "tavan_rota": sum(1 for x in tavan.values() if x),
        "TP": tp, "FP": fp, "FN": fn, "fp_kareler": fp_kareler,
        "yanlis_guzergah": ry["yanlis_guzergah"],
        "yanlis_kareler": ry["yanlis_kareler"],
        "rota_kare_olculen": ry["rota_kare"],
        "gercek_kayip": len(kayip_maske_yok) + len(kayip_uc_bant) + len(kayip_diger),
        "kayip_maske_yok": len(kayip_maske_yok),
        "kayip_uc_bant": len(kayip_uc_bant),
        "kayip_diger": len(kayip_diger),
        "kayip_maske_yok_kareler": kayip_maske_yok,
        "kayip_uc_bant_kareler": kayip_uc_bant,
        "kayip_diger_kareler": kayip_diger,
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--esikler", type=float, nargs="*", default=list(ESIKLER))
    ap.add_argument("--kumeler", nargs="*", default=list(KUMELER))
    a = ap.parse_args()

    sys.path.insert(0, str(KOK / "codes"))
    from model_registry import resolve_model            # noqa: E402
    agirlik = Path(resolve_model()[0])                  # 🔴 CIPLAK YOL YOK
    m142 = _modul("m142", OLCUM / "142_gece_olcum.py")

    HAM.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    sonuc = {
        "_ne": "ON_KAYIT §18-A · guven esigi (conf) supurmesi — OLCUM, kapi degil",
        "_on_kayit": "results/gece_20260826/ON_KAYIT.md §18-A",
        "_agirlik": str(agirlik), "_taban_esik": TABAN_ESIK,
        "_oneri_kurali": ONERI, "_esikler": a.esikler,
        "_zincir": "126_t138_gece_kumesi.py --conf E (uretim zinciri birebir)",
        "olcumler": {},
    }
    for e in a.esikler:
        sonuc["olcumler"][f"{e:.2f}"] = {}
        for ad in a.kumeler:
            k = KUMELER[ad]
            print(f"[conf {e:.2f} · {ad}] kosuluyor...", flush=True)
            ts = time.time()
            d = kos126(agirlik, k["kareler"], e,
                       f"{ad}_conf{int(round(e * 100)):03d}.json",
                       BURASI / f"log_{ad}_conf{int(round(e * 100)):03d}.log")
            o = olc(d, k["tavan"], k["etiket"], k["kareler"], m142)
            o["saniye"] = round(time.time() - ts)
            sonuc["olcumler"][f"{e:.2f}"][ad] = o
            print(f"    ROTA {o['rota']}/{o['n']} · MASKE_YOK {o['maske_yok']} · "
                  f"UC_BANT {o['uc_bant']} · TP {o['TP']} FP {o['FP']} FN {o['FN']} · "
                  f"YANLIS {o['yanlis_guzergah']}/{o['rota_kare_olculen']} · "
                  f"GERCEK KAYIP {o['gercek_kayip']} "
                  f"(korluk {o['kayip_maske_yok']} · bant {o['kayip_uc_bant']} · "
                  f"diger {o['kayip_diger']}) · {o['saniye']} sn", flush=True)
            (BURASI / "olcum.json").write_text(
                json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── ON KAYITLI ONERI KURALI — sonuca gore DEGISTIRILMEZ ────────────────
    tb = sonuc["olcumler"].get(f"{TABAN_ESIK:.2f}")
    hukum = {}
    if tb:
        taban_kayip = sum(tb[ad]["gercek_kayip"] for ad in tb)
        taban_yanlis = {ad: tb[ad]["yanlis_guzergah"] for ad in tb}
        for e, kume in sonuc["olcumler"].items():
            if float(e) == TABAN_ESIK:
                continue
            kayip = sum(kume[ad]["gercek_kayip"] for ad in kume)
            i = (taban_kayip - kayip) >= ONERI["gercek_kayip_azalma_min"]
            ii = all(kume[ad]["yanlis_guzergah"] <= taban_yanlis.get(ad, 0)
                     for ad in kume)
            iii = all(kume[ad]["FP"] <= ONERI[f"fp_{ad}_maks"] for ad in kume
                      if f"fp_{ad}_maks" in ONERI)
            hukum[e] = {"gercek_kayip": kayip, "taban_kayip": taban_kayip,
                        "azalma": taban_kayip - kayip,
                        "i_kayip_azaldi": bool(i), "ii_yanlis_artmadi": bool(ii),
                        "iii_fp_icinde": bool(iii),
                        "aday": bool(i and ii and iii),
                        "iv_sentetik_K0_K6": "AYRI KOSUM (yalniz aday esikte)"}
    sonuc["hukum"] = hukum
    adaylar = [e for e, h in hukum.items() if h["aday"]]
    sonuc["adaylar"] = adaylar
    (BURASI / "olcum.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nADAY ESIK(LER): {adaylar or 'YOK'}   ({round(time.time() - t0)} sn)")
    print(f"yazildi: {BURASI / 'olcum.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
