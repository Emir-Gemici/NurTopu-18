"""T220 / G4 — URETIM MODELI (v36) PC REFERANS KARARLARI: `test_goruntuleri/` serit karari listesi.

NEDEN (JETSON_OTURUM_DURUMU_20260909 SS3 G4, SS5.2; jetson_paket/GUN1_KONTROL_LISTESI SS4):
Gun-1 SS4 kapisi "`test_goruntuleri/` uzerinde `.engine` ciktisi <-> PC referans KARARI
(serit no) birebir ayni mi?" diye sorar. Pakette v36 icin PC referans karari dosyasi YOKTU
(`results/pc_referans_v17_20260805` yalniz v17, o da `jetson_fps` zinciri) — kapi 6 ve 9 Eylul'de
hic olculemedi. Bu betik referansi PC'de `.pt` ile uretir ve AYNI betik Jetson'da `.engine` ile
kosulup `--karsilastir` ile fark sayilir (tek zincir, iki kart).

ZINCIR (uretim karar halkasi, 164/170 ile AYNI):
    kare -> `_preprocess` (letterbox + isik) -> predict(imgsz=INFER_SIZE, conf=0.30)
         -> `get_masks` -> `_maskeleri_icerige_kirp`
         -> URETIM KARARI: `analyze_path(..., mpp)` + `rota_olcek_reddi` + `_rota_kararini_esikle`
            -> (`uretim_yol` = serit no | None, `uretim_red` = NO_ROUTE sebebi)
         -> KATMAN-A (bilgi): `rota_bul(mpp=None, plan=False, icerik)` -> durum, yol_no
            (jetson_fps.py'nin olceksiz zinciri; v17 referansinin bicimi — KARAR DEGIL, teshis)

OLCEK (mpp) KURALI — sonuc gorulmeden yazildi:
  · `sentetik_arena` (30 kare, 640x640, sentetik kadraj ureteci): T66/T60 manifestlerindeki
    "kontrollu sentetik varsayimi" ile AYNI: mpp = HTAB 50 m / goruntu genisligi (= 0,078125).
    Bu kareler hicbir manifestte yok (sha ile bakildi: T66 0/30, T60 0/30) — mpp BEYANDIR, olcum degil.
  · `drone_kareleri` (19 kare, 1024x576, `data/raw_frames`): irtifa telemetrisi YOK -> mpp None ->
    uretim karari CONTRACTS SS11.3 Halka 5 geregi OLCEK_YOK (rota yayinlanmaz). Bu SATIR
    "trivial esitlik"tir; drone karelerinde engine<->pt farki KATMAN-A satirindan ve maske
    oranlarindan okunur (bilgi), hukme girmez.

HUKUM (`--karsilastir`): GUN1 SS4 "birebir ayni" -> `uretim_yol` uyusmazligi 0 ise GECTI, degilse
DUSTU (sayi yazilir); kare kumesi farkliysa (sha/eksik) OLCULEMEDI. Esik gevsetilmez.
CUDA yoksa OLCULEMEDI (`--cihaz cpu` acikca verilirse CPU'da kosar ve JSON'a yazilir).
GPU isi TEK surectir (BSOD kurali, ON_KAYIT SS5.6).

KULLANIM:
  PC (referans):   venv python scripts/olcum/177_pc_referans_v36.py
                   -> results/fdr_sprint_20260910/H8/pc_referans_v36.json
  Jetson (engine): python scripts/olcum/177_pc_referans_v36.py --model jetson_paket/models/<v36>.engine \
                   --karsilastir results/fdr_sprint_20260910/H8/pc_referans_v36.json \
                   --cikti results/jetson_log_<tarih>/jetson_referans_engine.json \
                   --fark-cikti results/jetson_log_<tarih>/jetson_pc_fark.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))
from costmap_path_finder import rota_bul  # noqa: E402
from karar_sozlesmesi import (OLCEK_KAYNAK_TELEMETRI, SENARYO_BOYUTLARI_M,  # noqa: E402
                              rota_olcek_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp, _preprocess,  # noqa: E402
                           _rota_kararini_esikle, analyze_path, get_masks,
                           model_kayit_dogrula)

CONF = 0.30                                    # 164/170 ile ayni uretim esigi
KUMELER = ("sentetik_arena", "drone_kareleri")  # JETSON_KILAVUZ SS2 agaci: 30 + 19 kare
VARSAYILAN_KOK = REPO / "jetson_paket" / "test_goruntuleri"
VARSAYILAN_CIKTI = REPO / "results" / "fdr_sprint_20260910" / "H8" / "pc_referans_v36.json"
SENTETIK_OLCEK_KAYNAGI = ("SENTETIK VARSAYIM (BEYAN): HTAB 50 m / goruntu genisligi — T66/T60 manifest "
                          "kalibi; gercek kamera mpp olcumu DEGIL")
DRONE_OLCEK_KAYNAGI = ("YOK: irtifa telemetrisi yok -> mpp None -> uretim karari OLCEK_YOK "
                       "(CONTRACTS SS11.3 Halka 5); fark KATMAN-A satirindan okunur")
GORUNTU_UZANTILARI = (".jpg", ".jpeg", ".png")


def _sha(yol: Path) -> str:
    h = hashlib.sha256()
    with yol.open("rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def mpp_kurali(kume: str, genislik: int):
    """(mpp, kaynak_notu) — kume basina ONCEDEN yazilmis kural (docstring)."""
    if kume == "sentetik_arena":
        return SENARYO_BOYUTLARI_M["HTAB"] / float(genislik), SENTETIK_OLCEK_KAYNAGI
    return None, DRONE_OLCEK_KAYNAGI


def _karar(masks, icerik, mpp):
    """170_engine_karar_denkligi._karar ile AYNI uretim karar halkasi."""
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
                                        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, (red[0] if isinstance(red, tuple) else red)


def kare_isle(model, img: np.ndarray, mpp, cihaz):
    """Tek kare: maskeler + uretim karari + katman-A (bilgi) + maske oranlari."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    tahmin = {"imgsz": INFER_SIZE, "conf": CONF, "verbose": False}
    if cihaz:
        tahmin["device"] = cihaz
    sonuc = model.predict(small, **tahmin)
    maskeler = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    x0, y0, cw, ch = icerik
    alan = float(cw * ch)
    oran = {int(k): round(float(v[y0:y0 + ch, x0:x0 + cw].astype(bool).sum()) / alan, 5)
            for k, v in maskeler.items()}
    yol, red = _karar({k: v.copy() for k, v in maskeler.items()}, icerik, mpp)
    ka = rota_bul({k: v.copy() for k, v in maskeler.items()}, mpp=None, plan=False,
                  gorsel_cikti=False, icerik=icerik)
    return {"uretim_yol": yol, "uretim_red": red,
            "katman_a_durum": ka.get("durum"), "katman_a_yol_no": ka.get("yol_no"),
            "gecilebilir_orani": oran.get(0), "engel_orani": oran.get(1)}


def kume_isle(model, kok: Path, kume: str, cihaz, sinir=None):
    dizin = kok / kume
    kareler = sorted(p for p in dizin.iterdir() if p.suffix.lower() in GORUNTU_UZANTILARI)
    if sinir:
        kareler = kareler[:sinir]
    out = []
    for p in kareler:
        img = cv2.imread(str(p))
        if img is None:
            out.append({"kare": p.name, "sha256": _sha(p), "hata": "okunamadi"})
            continue
        mpp, kaynak = mpp_kurali(kume, img.shape[1])
        t0 = time.perf_counter()
        k = kare_isle(model, img, mpp, cihaz)
        k.update({"kare": p.name, "sha256": _sha(p), "boyut": [int(img.shape[1]), int(img.shape[0])],
                  "mpp": mpp, "mpp_kaynagi": kaynak, "sure_ms": round((time.perf_counter() - t0) * 1000, 1)})
        out.append(k)
    return out


def ozetle(kayitlar):
    """Kume ozeti: uretim serit dagilimi, red sebepleri, katman-A durumlari."""
    def say(anahtar):
        d = {}
        for k in kayitlar:
            v = k.get(anahtar)
            d[str(v)] = d.get(str(v), 0) + 1
        return dict(sorted(d.items()))
    return {"n": len(kayitlar), "uretim_yol": say("uretim_yol"), "uretim_red": say("uretim_red"),
            "katman_a_durum": say("katman_a_durum"), "katman_a_yol_no": say("katman_a_yol_no")}


def karsilastir(ref: dict, yeni: dict) -> dict:
    """SAF FONKSIYON: referans (PC .pt) ile yeni kosum (Jetson .engine) kare adina gore kiyas.

    Hukum GUN1 SS4: `uretim_yol` (serit no) birebir ayni -> GECTI; uyusmazlik > 0 -> DUSTU;
    kare kumesi farkli (eksik kare / sha farki) -> OLCULEMEDI. Katman-A ve sebep farklari BILGIdir.
    """
    sonuc = {"kumeler": {}, "hukum": {}}
    toplam = uyusmazlik = eksik = kare_farkli = 0
    for kume in KUMELER:
        r = {k["kare"]: k for k in ref.get("kumeler", {}).get(kume, [])}
        y = {k["kare"]: k for k in yeni.get("kumeler", {}).get(kume, [])}
        farklar, ka_fark, red_fark, n = [], 0, 0, 0
        for ad in sorted(r):
            a = r[ad]
            b = y.get(ad)
            if b is None:
                eksik += 1
                farklar.append({"kare": ad, "tur": "EKSIK"})
                continue
            if a.get("sha256") != b.get("sha256"):
                kare_farkli += 1
                farklar.append({"kare": ad, "tur": "KARE_FARKLI", "ref_sha": a.get("sha256"),
                                "yeni_sha": b.get("sha256")})
                continue
            n += 1
            if a.get("uretim_yol") != b.get("uretim_yol"):
                uyusmazlik += 1
                farklar.append({"kare": ad, "tur": "URETIM_KARARI", "ref": a.get("uretim_yol"),
                                "yeni": b.get("uretim_yol"), "ref_red": a.get("uretim_red"),
                                "yeni_red": b.get("uretim_red")})
            elif a.get("uretim_red") != b.get("uretim_red"):
                red_fark += 1
            if (a.get("katman_a_durum"), a.get("katman_a_yol_no")) != (
                    b.get("katman_a_durum"), b.get("katman_a_yol_no")):
                ka_fark += 1
        toplam += n
        sonuc["kumeler"][kume] = {"n_kiyaslanan": n, "farklar": farklar,
                                  "uretim_uyusmazlik": sum(1 for f in farklar if f["tur"] == "URETIM_KARARI"),
                                  "sebep_farki_bilgi": red_fark, "katman_a_farki_bilgi": ka_fark}
    if eksik or kare_farkli or toplam == 0:
        durum = "OLCULEMEDI"
        sebep = f"kare kumesi farkli: eksik={eksik} sha_farki={kare_farkli} kiyaslanan={toplam}"
    else:
        durum = "GECTI" if uyusmazlik == 0 else "DUSTU"
        sebep = f"uretim serit karari uyusmazligi {uyusmazlik}/{toplam} (esik: 0, GUN1 SS4 birebir)"
    sonuc["hukum"] = {"durum": durum, "uyusmazlik": uyusmazlik, "n": toplam, "eksik": eksik,
                      "kare_farkli": kare_farkli, "esik": 0, "sebep": sebep,
                      "_kaynak": "jetson_paket/GUN1_KONTROL_LISTESI.md SS4 (rota karari birebir; maske IoU degil)"}
    return sonuc


def _ortam():
    bilgi = {"platform": platform.platform(), "python": platform.python_version()}
    try:
        import torch
        bilgi["torch"] = torch.__version__
        bilgi["cuda_var"] = bool(torch.cuda.is_available())
        bilgi["cuda_adi"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception as exc:  # noqa: BLE001
        bilgi["torch_hata"] = str(exc)
    try:
        import ultralytics
        bilgi["ultralytics"] = ultralytics.__version__
    except Exception as exc:  # noqa: BLE001
        bilgi["ultralytics_hata"] = str(exc)
    bilgi["cv2"] = cv2.__version__
    return bilgi


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kok", type=Path, default=VARSAYILAN_KOK,
                    help="test_goruntuleri koku (icinde sentetik_arena/ ve drone_kareleri/)")
    ap.add_argument("--model", type=Path, default=None,
                    help="agirlik (.pt/.engine/.onnx); verilmezse defterin uretim .pt'si. Kayit defteri "
                         "dogrulamasindan gecmeyen model OLCULMEZ (fail-closed)")
    ap.add_argument("--cihaz", default="0", help="'0' (CUDA, varsayilan) ya da 'cpu' (acikca)")
    ap.add_argument("--sinir", type=int, default=None, help="kume basina en cok N kare (yalniz deneme)")
    ap.add_argument("--cikti", type=Path, default=None,
                    help=f"referans JSON (varsayilan, --karsilastir yokken: {VARSAYILAN_CIKTI.relative_to(REPO).as_posix()})")
    ap.add_argument("--karsilastir", type=Path, default=None,
                    help="PC referans JSON'u; verilirse bu kosum onunla kiyaslanir ve hukum basilir")
    ap.add_argument("--fark-cikti", type=Path, default=None, help="kiyas sonucu JSON (yalniz --karsilastir ile)")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    for kume in KUMELER:
        if not (a.kok / kume).is_dir():
            print(f"OLCULEMEDI: kume dizini yok: {a.kok / kume}")
            return 1
    import torch
    if a.cihaz != "cpu" and not torch.cuda.is_available():
        print("OLCULEMEDI: CUDA yok (CPU icin --cihaz cpu ACIKCA verilir)")
        return 1
    model_yolu = a.model if a.model else uretim_pt()
    ok, d = model_kayit_dogrula(model_yolu)
    print(("GECTI " if ok else "RED   ") + f"defter: {model_yolu.name} -> {d.get('durum')}")
    if not ok:
        print("OLCULEMEDI: kayit defteri reddi — model olculmez (madde 16 / T73 fail-closed)")
        return 1
    from ultralytics import YOLO
    model = YOLO(str(model_yolu), task="segment")
    cihaz = None if a.cihaz == "cpu" else a.cihaz

    t0 = time.time()
    kumeler = {}
    for kume in KUMELER:
        kumeler[kume] = kume_isle(model, a.kok, kume, cihaz, a.sinir)
        print(f"{kume}: {len(kumeler[kume])} kare — {json.dumps(ozetle(kumeler[kume]), ensure_ascii=False)}")
    dtype = None
    try:
        dtype = str(next(model.predictor.model.model.parameters()).dtype)
    except Exception:  # noqa: BLE001
        pass
    arka_uc = type(model.predictor.model).__name__ if getattr(model, "predictor", None) else None
    cikti = {
        "_gorev": "T220/G4 — v36 PC referans kararlari (test_goruntuleri); Jetson engine ile --karsilastir",
        "_on_kayit": "scripts/olcum/177_pc_referans_v36.py docstring (mpp kurali, hukum) + GUN1_KONTROL_LISTESI SS4",
        "_zincir": "kare -> _preprocess -> predict(INFER_SIZE, conf) -> get_masks -> _maskeleri_icerige_kirp -> "
                   "analyze_path(mpp)+rota_olcek_reddi+_rota_kararini_esikle (URETIM) | rota_bul(mpp=None, plan=False) (KATMAN-A bilgi)",
        "_model": {"yol": model_yolu.relative_to(REPO).as_posix() if model_yolu.is_relative_to(REPO) else str(model_yolu),
                   "sha256": _sha(model_yolu), "defter_durum": d.get("durum"), "dtype": dtype, "arka_uc": arka_uc},
        "_ortam": _ortam(), "_cihaz": a.cihaz, "_conf": CONF, "_infer_size": INFER_SIZE, "_sinir": a.sinir,
        "_kok": a.kok.relative_to(REPO).as_posix() if a.kok.is_relative_to(REPO) else str(a.kok),
        "_olcek_kurali": {"sentetik_arena": SENTETIK_OLCEK_KAYNAGI, "drone_kareleri": DRONE_OLCEK_KAYNAGI},
        "_tarih": time.strftime("%Y-%m-%d %H:%M"), "_sure_s": round(time.time() - t0, 1),
        "ozet": {k: ozetle(v) for k, v in kumeler.items()},
        "kumeler": kumeler,
    }
    hedef = a.cikti if a.cikti else (None if a.karsilastir else VARSAYILAN_CIKTI)
    if hedef:
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(json.dumps(cikti, indent=1, ensure_ascii=False), encoding="utf-8")
        print("yazildi:", hedef)
    if a.karsilastir:
        ref = json.loads(a.karsilastir.read_text(encoding="utf-8"))
        fark = karsilastir(ref, cikti)
        fark["_referans"] = {"dosya": str(a.karsilastir), "model": ref.get("_model")}
        fark["_yeni_model"] = cikti["_model"]
        print(json.dumps(fark["hukum"], indent=1, ensure_ascii=False))
        for kume, k in fark["kumeler"].items():
            print(f"{kume}: kiyaslanan {k['n_kiyaslanan']} · uretim uyusmazligi {k['uretim_uyusmazlik']} · "
                  f"sebep farki (bilgi) {k['sebep_farki_bilgi']} · katman-A farki (bilgi) {k['katman_a_farki_bilgi']}")
        if a.fark_cikti:
            a.fark_cikti.parent.mkdir(parents=True, exist_ok=True)
            a.fark_cikti.write_text(json.dumps(fark, indent=1, ensure_ascii=False), encoding="utf-8")
            print("yazildi:", a.fark_cikti)
        return 0 if fark["hukum"]["durum"] == "GECTI" else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
