"""H1-K3 ÖN-ÖLÇÜMÜ — sim taraması → iha_haritala mozaik → ÜRETİM MODELİ v36 → rota.

Sonuç ne çıkarsa yazılır (ÖLÇÜLEMEDİ ≠ GEÇTİ; eşik gevşetilmez). Zincir:
  iha_ucus.tara (MuJoCo render, 1 Hz)  →  iha_haritala.haritala(level_dir, model, ...)
      mozaik_kur → _infer (v36 .pt, sim'e özel eğitim YOK) → costmap → rota_bul → rota.json
Ek teşhis (K3'ün "neden"i için): mozaik üstünde sınıf piksel oranları, yer-gerçeği yol
şeridinde geçilebilir oranı (açık/kapalı yollar ayrı), yol dışı zeminde geçilebilir oranı.

OBB araç maskesi sim'de KAPALI (arac_model=None → boş maske; sim'de araç yok).
Model yolu `config/model_registry.json` etkin profilinden; sha256 kayıtla karşılaştırılır.

Kullanım:
  venv python simulation/mujoco/on_olcum_k3.py --haritalar 1:kolay,1:orta,1:zor
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
for _p in (str(BURASI.parent / "scripts"), str(KOK / "codes"), str(BURASI)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import arena                                        # noqa: E402
import arena_mjcf                                   # noqa: E402
import iha_ucus                                     # noqa: E402
import iha_haritala as ih                           # noqa: E402
from iha_perceive import _infer                     # noqa: E402
from model_registry import DEFAULT_REGISTRY, load_registry   # noqa: E402
from world_generator import DIFF                    # noqa: E402

H1_KOK = KOK / "results" / "fdr_sprint_20260910" / "H1"
ANA_DEPO = Path("O:/navitas")       # .pt git dışı; worktree'de yoksa ana ağaçtan


def _sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def model_coz(kayit=None) -> dict:
    """Etkin profil → {path, sha256_kayit, sha256_dosya, eslesti, model_id}."""
    veri = load_registry(Path(kayit) if kayit else DEFAULT_REGISTRY)
    profil = veri["profiles"][veri["default_profile"]]
    rel = profil["path"]
    aday = [KOK / rel, ANA_DEPO / rel]
    yol = next((p for p in aday if p.is_file()), None)
    if yol is None:
        raise FileNotFoundError(f"üretim modeli yok: {aday}")
    sha = _sha256(yol)
    return {"model_id": profil.get("model_id"), "path": str(yol), "kayit_path": rel,
            "sha256_dosya": sha, "sha256_kayit": profil.get("sha256"),
            "eslesti": bool(sha == profil.get("sha256")), "imgsz_kayit": profil.get("imgsz")}


def yol_maskeleri(H: dict, lv: str):
    """Mozaik pikselinde (MOZ_PX², kuzey-yukarı) yer-gerçeği: açık yol, kapalı yollar, tüm yol."""
    import cv2
    N = ih.MOZ_PX
    kal = max(1, int(round(DIFF[lv]["lane_w"] / ih.MPP)))
    acik = np.zeros((N, N), np.uint8)
    kapali = np.zeros((N, N), np.uint8)
    for road in (1, 2, 3):
        pts = np.array([ih.dunya_to_piksel((x, y), 0.0, 0.0) for (x, y) in H["paths"][road]], np.int32)
        hedef = acik if road == H["open"] else kapali
        cv2.polylines(hedef, [pts], False, 1, thickness=kal)
    return acik.astype(bool), kapali.astype(bool)


def htab_penceresi():
    N = ih.MOZ_PX
    k = int(round(arena.HTAB_HALF / ih.MPP))
    c = N // 2
    pen = np.zeros((N, N), bool)
    pen[c - k:c + k, c - k:c + k] = True
    return pen


def teshis(mozaik_bgr, model, conf, H, lv) -> dict:
    """Model maskeleri üstünde piksel oranları (sınıf 0 geçilebilir, 1 moloz/engel)."""
    _content, masks, _road, _conf, _wps, _k = _infer(mozaik_bgr, model, conf, ih.MOZ_PX)
    trav = masks[0].astype(bool); eng = masks[1].astype(bool)
    pen = htab_penceresi()
    acik, kapali = yol_maskeleri(H, lv)
    yol_disi = pen & ~acik & ~kapali
    def oran(a, b):
        return round(float(a[b].mean()), 4) if b.any() else None
    return {
        "mozaik_gecilebilir_orani": round(float(trav.mean()), 4),
        "mozaik_engel_orani": round(float(eng.mean()), 4),
        "htab_gecilebilir_orani": oran(trav, pen),
        "htab_engel_orani": oran(eng, pen),
        "acik_yol_seridinde_gecilebilir": oran(trav, acik),
        "acik_yol_seridinde_engel": oran(eng, acik),
        "kapali_yol_seridinde_gecilebilir": oran(trav, kapali),
        "kapali_yol_seridinde_engel": oran(eng, kapali),
        "yol_disi_zeminde_gecilebilir": oran(trav, yol_disi),
        "yol_disi_zeminde_engel": oran(eng, yol_disi),
    }


def harita_olc(h: int, lv: str, model, conf: float, res: int, yeniden: bool, fizik: bool,
               kok: Path = H1_KOK, yol_dokusu: str = arena_mjcf.YOL_DOKUSU_VARSAYILAN) -> dict:
    import cv2
    H = arena.harita(h, lv)
    hdir = Path(kok).resolve() / f"harita_{h}_{lv}"
    ldir = hdir / "iha_scan"
    if yeniden or not (ldir / "poses.csv").is_file():
        tarama = iha_ucus.tara(h, lv, out=ldir, res=res, fizik=fizik, yol_dokusu=yol_dokusu)
    else:
        tarama = json.loads((ldir / "tarama_ozeti.json").read_text(encoding="utf-8"))
    if tarama.get("yol_dokusu", arena_mjcf.YOL_DOKUSU_VARSAYILAN) != yol_dokusu:
        raise SystemExit(f"{ldir}: tarama yol dokusu {tarama.get('yol_dokusu')} ≠ istenen {yol_dokusu} "
                         "(--yeniden-tara ya da ayrı --kok kullan)")
    meta = ih._meta_oku(ldir)
    cx, cy = ih._htab_merkez(meta, None)
    kb, hb = ih._meta_xy(meta, "KB_XY"), ih._meta_xy(meta, "HB_XY")
    t0 = time.perf_counter()
    det = ih.haritala(ldir, model, cx, cy, conf=conf, kb_xy=kb, hb_xy=hb, arac_model=None)
    t_harita = time.perf_counter() - t0
    moz = cv2.imread(str(ldir / "ortomozaik.jpg"))
    th = teshis(moz, model, conf, H, lv) if moz is not None else {}
    truth = H["open"]
    return {
        "harita": h, "senaryo": lv, "yol_dokusu": yol_dokusu,
        "tarama": {"kare_n": tarama["kare_n"], "kabul": tarama["kabul_edilen_kare"],
                   "htab_kapsama_orani": tarama["htab_kapsama_orani"], "res": tarama["res"]},
        "mozaik_kare_n": det.get("kare_n"),
        "gercek_acik_yol": truth, "gercek_etiket": arena.ROAD_LABEL[truth],
        "model_yol": det.get("road"), "model_etiket": det.get("label"), "model_guven": det.get("conf"),
        "rota_durum": det.get("rota_durum"), "rota_sebep": det.get("rota_sebep"),
        "wp_n": det.get("wp_n"), "darbogaz_m": det.get("darbogaz_m"),
        "rota_bulundu": bool(det.get("rota_durum") == "ACIK" and det.get("road")),
        "dogru": bool(det.get("road") == truth),
        "trav_px": det.get("trav_px"), "moloz_px": det.get("moloz_px"), "arac_px": det.get("arac_px"),
        "arac_model": det.get("arac_model"),
        "teshis": th,
        "haritala_sure_s": round(t_harita, 2),
        "dosyalar": {k: (str((ldir / k).relative_to(KOK)) if ldir.is_relative_to(KOK) else str(ldir / k))
                     for k in ("ortomozaik.jpg", "algi.jpg", "detection.json") if (ldir / k).is_file()},
    }


def main():
    ap = argparse.ArgumentParser(description="H1-K3 ön-ölçümü: sim mozaik → v36 → rota")
    ap.add_argument("--haritalar", default="1:kolay,1:orta,1:zor")
    ap.add_argument("--conf", type=float, default=0.15)
    ap.add_argument("--res", type=int, default=arena_mjcf.KAM_RES_VARSAYILAN)
    ap.add_argument("--yeniden-tara", action="store_true")
    ap.add_argument("--hizli", action="store_true")
    ap.add_argument("--cikti", default=str(H1_KOK / "on_olcum_K3.json"))
    ap.add_argument("--kok", default=str(H1_KOK), help="harita_<h>_<lv>/ dizinlerinin kökü")
    ap.add_argument("--yol-dokusu", default=arena_mjcf.YOL_DOKUSU_VARSAYILAN, choices=arena_mjcf.YOL_DOKULARI,
                    help="TEŞHİS varyantı: yol yüzeyi dokusu (varsayılan stabilize = asıl ölçüm)")
    a = ap.parse_args()

    import torch
    from ultralytics import YOLO
    mk = model_coz()
    print(f"[K3] model {mk['model_id']} {mk['path']} sha eşleşti={mk['eslesti']}")
    model = YOLO(mk["path"], task="segment")
    gpu = {"cuda": bool(torch.cuda.is_available()),
           "cihaz": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
           "torch": torch.__version__}
    sonuclar = []
    for parca in a.haritalar.split(","):
        h, lv = parca.split(":")
        r = harita_olc(int(h), lv, model, a.conf, a.res, a.yeniden_tara, not a.hizli,
                       kok=Path(a.kok), yol_dokusu=a.yol_dokusu)
        print(f"[K3] harita {h} {lv}: gerçek={r['gercek_etiket']} model={r['model_etiket']} "
              f"rota={r['rota_durum']} doğru={r['dogru']} trav={r['teshis'].get('htab_gecilebilir_orani')} "
              f"engel={r['teshis'].get('htab_engel_orani')}")
        sonuclar.append(r)
    dogru = sum(r["dogru"] for r in sonuclar)
    rota = sum(r["rota_bulundu"] for r in sonuclar)
    cikti = {
        "kapi": "H1-K3 ÖN-ÖLÇÜM (3 harita; asıl kapı 15 harita ≥ 12/15)",
        "tarih": time.strftime("%Y-%m-%d %H:%M"),
        "model": mk, "gpu": gpu, "conf": a.conf, "obb_arac_maskesi": "KAPALI (sim'de araç yok)",
        "yol_dokusu": a.yol_dokusu, "kok": str(a.kok),
        "sim_sinir": "İHA uçuşu kinematik; render MuJoCo; dokular gerçek kare kırpması (dokular/KAYNAK.md)",
        "ozet": {"harita_n": len(sonuclar), "rota_bulunan": rota, "dogru_etiket": dogru,
                 "dogru_orani": round(dogru / max(1, len(sonuclar)), 3)},
        "haritalar": sonuclar,
    }
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    Path(a.cikti).write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[K3] ÖZET: rota bulunan {rota}/{len(sonuclar)}, doğru etiket {dogru}/{len(sonuclar)} → {a.cikti}")


if __name__ == "__main__":
    main()
