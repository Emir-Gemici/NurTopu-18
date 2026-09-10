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


def yol_maskeleri(H: dict, lv: str, serit_w: float | None = None):
    """Mozaik pikselinde (MOZ_PX², kuzey-yukarı) yer-gerçeği: açık yol, kapalı yollar, tüm yol.
    `serit_w` (m): şerit genişliği; None → DIFF lane_w (taban). v1+ görsel şerit YOL_GENISLIK_M."""
    import cv2
    N = ih.MOZ_PX
    kal = max(1, int(round((serit_w or DIFF[lv]["lane_w"]) / ih.MPP)))
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


def teshis(mozaik_bgr, model, conf, H, lv, serit_w: float | None = None, imgsz: int | None = None,
           rota: bool = False, hb_yaricap_m: float = 0.0) -> dict:
    """Model maskeleri üstünde piksel oranları (sınıf 0 geçilebilir, 1 moloz/engel).
    `imgsz` (TEŞHİS): üretim zinciri MOZ_PX=1024'te çıkarım yapar; verilirse aynı mozaik bu
    çözünürlükte de koşulur (kayıt imgsz 512, CONTRACTS §8) ve maskeler 1024'e büyütülür.
    `rota=True`: aynı costmap/rota_bul zinciri bu maskelerle koşulur (durum + yol no)."""
    import cv2
    _content, masks, _road, _conf, _wps, _k = _infer(mozaik_bgr, model, conf, imgsz or ih.MOZ_PX)
    if imgsz and imgsz != ih.MOZ_PX:
        masks = {k: cv2.resize(v.astype(np.uint8), (ih.MOZ_PX, ih.MOZ_PX), interpolation=cv2.INTER_NEAREST)
                 for k, v in masks.items()}
    trav = masks[0].astype(bool); eng = masks[1].astype(bool)
    pen = htab_penceresi()
    acik, kapali = yol_maskeleri(H, lv, serit_w)
    yol_disi = pen & ~acik & ~kapali
    def oran(a, b):
        return round(float(a[b].mean()), 4) if b.any() else None
    out = {
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
    if rota:
        from costmap_path_finder import rota_bul
        from sinif_semasi import (COSTMAP_ENGEL_KATMANLARI, COSTMAP_YOL_KATMANLARI,
                                  costmap_katmanlari)
        katman = costmap_katmanlari(masks[0].astype(np.uint8), masks[1].astype(np.uint8), None)
        bas = ih._tohum_maskesi(H["kb"], 0.0, 0.0, (ih.MOZ_PX, ih.MOZ_PX))
        hed = ih._tohum_maskesi(H["hb"], 0.0, 0.0, (ih.MOZ_PX, ih.MOZ_PX), yaricap_m=hb_yaricap_m)
        ps = rota_bul(katman, mpp=ih.MPP, baslangic=bas, hedef=hed, plan=True,
                      yol_sinif_idler=COSTMAP_YOL_KATMANLARI, engel_sinif_idler=COSTMAP_ENGEL_KATMANLARI,
                      gorsel_cikti=False)
        out.update({"rota_durum": ps["durum"], "model_yol": ps["yol_no"], "wp_n": len(ps["waypoints_px"]),
                    "dogru": bool(ps["yol_no"] == H["open"] and ps["durum"] == "ACIK")})
    return out


def harita_olc(h: int, lv: str, model, conf: float, res: int, yeniden: bool, fizik: bool,
               kok: Path = H1_KOK, yol_dokusu: str = arena_mjcf.YOL_DOKUSU_VARSAYILAN,
               varyant: str = arena_mjcf.VARYANT_VARSAYILAN,
               zemin_dokusu: str = arena_mjcf.ZEMIN_DOKUSU_VARSAYILAN,
               teshis_imgsz: int | None = None, mozaik: str = "son_yazar",
               hb_yaricap_m: float = 0.0, tarama_kaynak: Path | None = None) -> dict:
    """`tarama_kaynak` (TEŞHİS geçişleri): tarama (kareler/poses/meta/tarama_ozeti) o kökün
    harita_<h>_<lv>/iha_scan/ dizininden okunur; mozaik/algı/detection.json `kok` altına yazılır.
    Üretim (hb 0) kanıtı teşhis geçişiyle ÜZERİNE YAZILMAZ (T213-A çürütücü bulgusu)."""
    import cv2
    H = arena.harita(h, lv)
    hdir = Path(kok).resolve() / f"harita_{h}_{lv}"
    ldir = hdir / "iha_scan"
    girdi = ldir
    if tarama_kaynak is not None:
        girdi = Path(tarama_kaynak).resolve() / f"harita_{h}_{lv}" / "iha_scan"
        if yeniden or not (girdi / "poses.csv").is_file():
            raise SystemExit(f"--tarama-kaynak {girdi}: poses.csv yok ya da --yeniden-tara ile birlikte "
                             "verildi (kaynak önce üretim geçişiyle taranır)")
        if girdi == ldir:
            raise SystemExit("--tarama-kaynak ile --kok aynı dizin: teşhis çıktısı üretim kanıtının üstüne yazılır")
        ldir.mkdir(parents=True, exist_ok=True)
        tarama = json.loads((girdi / "tarama_ozeti.json").read_text(encoding="utf-8"))
    elif yeniden or not (ldir / "poses.csv").is_file():
        tarama = iha_ucus.tara(h, lv, out=ldir, res=res, fizik=fizik, yol_dokusu=yol_dokusu,
                               varyant=varyant, zemin_dokusu=zemin_dokusu)
    else:
        tarama = json.loads((ldir / "tarama_ozeti.json").read_text(encoding="utf-8"))
    istenen = {"yol_dokusu": yol_dokusu, "varyant": varyant, "zemin_dokusu": zemin_dokusu}
    vars_ = {"yol_dokusu": arena_mjcf.YOL_DOKUSU_VARSAYILAN, "varyant": "taban",
             "zemin_dokusu": arena_mjcf.ZEMIN_DOKUSU_VARSAYILAN}
    for k, v in istenen.items():
        if tarama.get(k, vars_[k]) != v:
            raise SystemExit(f"{ldir}: tarama {k} {tarama.get(k, vars_[k])} ≠ istenen {v} "
                             "(--yeniden-tara ya da ayrı --kok kullan)")
    serit_w = None if varyant == "taban" else arena_mjcf.YOL_GENISLIK_M
    meta = ih._meta_oku(girdi)
    cx, cy = ih._htab_merkez(meta, None)
    kb, hb = ih._meta_xy(meta, "KB_XY"), ih._meta_xy(meta, "HB_XY")
    t0 = time.perf_counter()
    det = ih.haritala(ldir, model, cx, cy, conf=conf, kb_xy=kb, hb_xy=hb, arac_model=None,
                      birlestirme=mozaik, hb_yaricap_m=hb_yaricap_m,
                      girdi_dir=None if girdi == ldir else girdi)
    t_harita = time.perf_counter() - t0
    moz = cv2.imread(str(ldir / "ortomozaik.jpg"))
    th = teshis(moz, model, conf, H, lv, serit_w) if moz is not None else {}
    th_imgsz = (teshis(moz, model, conf, H, lv, serit_w, imgsz=teshis_imgsz, rota=True,
                       hb_yaricap_m=hb_yaricap_m)
                if (moz is not None and teshis_imgsz) else None)
    truth = H["open"]
    return {
        "harita": h, "senaryo": lv, "yol_dokusu": yol_dokusu, "varyant": varyant, "mozaik": mozaik,
        "hb_yaricap_m": hb_yaricap_m,
        "tarama_kaynak": ((str(girdi.relative_to(KOK)) if girdi.is_relative_to(KOK) else str(girdi))
                          if girdi != ldir else None),
        "zemin_dokusu": zemin_dokusu if varyant != "taban" else None,
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
        "teshis_imgsz": ({"imgsz": teshis_imgsz,
                          "not": "TEŞHİS — üretim zinciri değil (iha_haritala MOZ_PX=1024 kullanır)",
                          **th_imgsz} if th_imgsz else None),
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
                    help="yol yüzeyi dokusu (varsayılan stabilize = asıl ölçüm)")
    ap.add_argument("--varyant", default=arena_mjcf.VARYANT_VARSAYILAN, choices=arena_mjcf.VARYANTLAR,
                    help="T213-A render varyantı (taban | v1 doku | v2 +ışık/gölge | v3 +moloz mesh)")
    ap.add_argument("--zemin-dokusu", default=arena_mjcf.ZEMIN_DOKUSU_VARSAYILAN,
                    choices=arena_mjcf.ZEMIN_DOKULARI, help="v1+ zemin kaynağı")
    ap.add_argument("--mozaik", default="son_yazar", choices=ih.BIRLESTIRMELER,
                    help="mozaik birleştirme: son_yazar (üretim varsayılanı) | nadir_yakin (TEŞHİS: "
                         "her piksel merkeze en yakın kareden)")
    ap.add_argument("--hb-yaricap", type=float, default=0.0,
                    help="TEŞHİS: HB hedef tohumu yarıçapı (m); 0 = üretim (tek piksel HB merkezi)")
    ap.add_argument("--teshis-imgsz", type=int, default=0,
                    help="TEŞHİS: aynı mozaiği bu imgsz ile de koş (0 = kapalı); karar zinciri değişmez")
    ap.add_argument("--tarama-kaynak", default=None,
                    help="TEŞHİS geçişleri: taramayı (kareler/poses/meta) bu kökten oku, çıktıları --kok "
                         "altına yaz — üretim kanıtı (detection.json) üstüne yazılmaz")
    a = ap.parse_args()
    if a.tarama_kaynak and Path(a.tarama_kaynak).resolve() == Path(a.kok).resolve():
        raise SystemExit("--tarama-kaynak ile --kok aynı: teşhis çıktısı üretim kanıtının üstüne yazılır")

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
                       kok=Path(a.kok), yol_dokusu=a.yol_dokusu, varyant=a.varyant,
                       zemin_dokusu=a.zemin_dokusu, teshis_imgsz=a.teshis_imgsz or None, mozaik=a.mozaik,
                       hb_yaricap_m=a.hb_yaricap,
                       tarama_kaynak=Path(a.tarama_kaynak) if a.tarama_kaynak else None)
        ek = ""
        if r.get("teshis_imgsz"):
            ti = r["teshis_imgsz"]
            ek = (f" | imgsz{ti['imgsz']}: rota={ti.get('rota_durum')} yol={ti.get('model_yol')} "
                  f"doğru={ti.get('dogru')} trav={ti.get('htab_gecilebilir_orani')}")
        print(f"[K3] harita {h} {lv} [{a.varyant}/{a.mozaik}/hb{a.hb_yaricap:g}]: gerçek={r['gercek_etiket']} model={r['model_etiket']} "
              f"rota={r['rota_durum']} doğru={r['dogru']} trav={r['teshis'].get('htab_gecilebilir_orani')} "
              f"engel={r['teshis'].get('htab_engel_orani')} "
              f"açıkyol_trav={r['teshis'].get('acik_yol_seridinde_gecilebilir')}{ek}")
        sonuclar.append(r)
    dogru = sum(r["dogru"] for r in sonuclar)
    rota = sum(r["rota_bulundu"] for r in sonuclar)
    ti_ozet = None
    if a.teshis_imgsz:
        ti_ozet = {"imgsz": a.teshis_imgsz, "not": "TEŞHİS — üretim zinciri değil",
                   "rota_bulunan": sum(1 for r in sonuclar
                                       if (r.get("teshis_imgsz") or {}).get("rota_durum") == "ACIK"),
                   "dogru_etiket": sum(1 for r in sonuclar if (r.get("teshis_imgsz") or {}).get("dogru"))}

    def _t(r, k):
        return r["teshis"].get(k) or 0.0
    n_harita = len(sonuclar)
    cikti = {
        "kapi": ("H1-K3 15 harita (eşik ≥ 12/15)" if n_harita == 15
                 else f"ÖN-ÖLÇÜM {n_harita} harita (asıl kapı 15 harita ≥ 12/15)"),
        "tarih": time.strftime("%Y-%m-%d %H:%M"),
        "model": mk, "gpu": gpu, "conf": a.conf, "obb_arac_maskesi": "KAPALI (sim'de araç yok)",
        "yol_dokusu": a.yol_dokusu, "varyant": a.varyant,
        "zemin_dokusu": a.zemin_dokusu if a.varyant != "taban" else None,
        "teshis_imgsz": a.teshis_imgsz or None, "mozaik": a.mozaik, "hb_yaricap_m": a.hb_yaricap,
        "kok": str(a.kok), "tarama_kaynak": a.tarama_kaynak,
        "sim_sinir": "İHA uçuşu kinematik; render MuJoCo; dokular gerçek kare kırpması (dokular/KAYNAK.md)",
        "ozet": {"harita_n": len(sonuclar), "rota_bulunan": rota, "dogru_etiket": dogru,
                 "dogru_orani": round(dogru / max(1, len(sonuclar)), 3),
                 "htab_gecilebilir_min_maks": [min(_t(r, "htab_gecilebilir_orani") for r in sonuclar),
                                               max(_t(r, "htab_gecilebilir_orani") for r in sonuclar)],
                 "htab_engel_min_maks": [min(_t(r, "htab_engel_orani") for r in sonuclar),
                                         max(_t(r, "htab_engel_orani") for r in sonuclar)],
                 "acik_yol_seridinde_gecilebilir_ort": round(
                     sum(_t(r, "acik_yol_seridinde_gecilebilir") for r in sonuclar) / max(1, len(sonuclar)), 4),
                 "yol_disi_gecilebilir_ort": round(
                     sum(_t(r, "yol_disi_zeminde_gecilebilir") for r in sonuclar) / max(1, len(sonuclar)), 4)},
        "teshis_imgsz_ozet": ti_ozet,
        "haritalar": sonuclar,
    }
    Path(a.cikti).parent.mkdir(parents=True, exist_ok=True)
    Path(a.cikti).write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[K3] ÖZET [{a.varyant}]: rota bulunan {rota}/{len(sonuclar)}, doğru etiket {dogru}/{len(sonuclar)}"
          + (f" | TEŞHİS imgsz{a.teshis_imgsz}: rota {ti_ozet['rota_bulunan']}, doğru {ti_ozet['dogru_etiket']}"
             if ti_ozet else "")
          + f" → {a.cikti}")


if __name__ == "__main__":
    main()
