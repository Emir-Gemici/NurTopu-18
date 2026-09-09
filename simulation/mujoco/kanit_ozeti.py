"""T212 kanıt özeti — H1 dizinindeki ölçüm JSON'larını tek dosyada toplar.

Girdi (hepsi ölçümden yazılır, elle düzenlenmez):
  arena_ozeti_15.json      (arena_mjcf --hepsi --kanit-kok)   → H1-K1
  tarama_ozeti_15.json     (iha_ucus --hepsi)                  → H1-K2 ön-ölçümü (kapsama)
  on_olcum_K3.json         (on_olcum_k3, 3 harita)             → H1-K3 ön-ölçümü
  on_olcum_K3_15harita.json, on_olcum_K3_asfalt_varyant.json  → ek ölçümler
Çıktı: ozet_T212.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[2]
H1 = KOK / "results" / "fdr_sprint_20260910" / "H1"


def _oku(ad):
    p = H1 / ad
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def main():
    arena = _oku("arena_ozeti_15.json")
    tarama = _oku("tarama_ozeti_15.json")
    k3 = _oku("on_olcum_K3.json")
    k3_15 = _oku("on_olcum_K3_15harita.json")
    k3_asf = _oku("on_olcum_K3_asfalt_varyant.json")
    out = {"gorev": "T212 SIM-1 (MuJoCo arena + araçlar + İHA uçuşu + tarama)",
           "tarih": time.strftime("%Y-%m-%d %H:%M"),
           "sinir": "İHA uçuşu KİNEMATİK (mocap, aerodinamik yok); modeller basitleştirilmiş (D-438 ek); "
                    "OBB araç maskesi sim'de KAPALI; hakem onayı bu görevde yok."}
    if arena:
        out["H1_K1"] = {"kapi": "arena MJCF deterministik, 15 harita, yönerge geometrisi",
                        "harita_n": arena["harita_n"], "yonerge_hepsi_ok": arena["yonerge_hepsi_ok"],
                        "mjcf_uretim_ms_ort": arena["mjcf_uretim_ms_ort"],
                        "mjcf_yukleme_ms_ort": arena["mjcf_yukleme_ms_ort"],
                        "ngeom_min_maks": arena["ngeom_min_maks"],
                        "sonuc": "GEÇTİ 15/15" if arena["yonerge_hepsi_ok"] and arena["harita_n"] == 15 else "DÜŞTÜ"}
    if tarama:
        kaps = [r["htab_kapsama_orani"] for r in tarama]
        rms = [r["render_ms_kare_ort"] for r in tarama]
        out["H1_K2_on_olcum"] = {
            "kapi": "kamera taraması gerçek renderdan; mozaik kurulur; kapsama ≥ HTAB",
            "harita_n": len(tarama), "kare_n_her_harita": sorted({r["kare_n"] for r in tarama}),
            "kabul_edilen_kare": sorted({r["kabul_edilen_kare"] for r in tarama}),
            "htab_kapsama_min": min(kaps), "htab_kapsama_maks": max(kaps),
            "render_ms_kare_ort": round(sum(rms) / len(rms), 1), "render_ms_kare_maks": max(r["render_ms_kare_maks"] for r in tarama),
            "res": sorted({r["res"] for r in tarama}), "sim_sure_s": sorted({r["sim_sure_s"] for r in tarama}),
            "duvar_saati_s_toplam": round(sum(r["duvar_saati_s"] for r in tarama), 1),
            "mozaik_kurulan_harita": (sum(1 for r in k3_15["haritalar"] if r["mozaik_kare_n"]) if k3_15 else None),
            "sonuc": ("GEÇTİ 15/15 (kapsama)" if len(tarama) == 15 and min(kaps) >= 0.99 else "DÜŞTÜ")}
    if k3:
        out["H1_K3_on_olcum"] = {
            "kapi": "üretim modeli v36 mozaikte açık yolu doğru etiketler (asıl eşik ≥ 12/15)",
            "model": k3["model"]["model_id"], "model_sha_eslesti": k3["model"]["eslesti"],
            "gpu": k3["gpu"]["cihaz"], "yol_dokusu": k3.get("yol_dokusu"),
            "ozet": k3["ozet"],
            "haritalar": [{"harita": r["harita"], "senaryo": r["senaryo"], "gercek": r["gercek_etiket"],
                           "model": r["model_etiket"], "rota_durum": r["rota_durum"], "dogru": r["dogru"],
                           "htab_gecilebilir": r["teshis"].get("htab_gecilebilir_orani"),
                           "htab_engel": r["teshis"].get("htab_engel_orani"),
                           "acik_yol_seridinde_gecilebilir": r["teshis"].get("acik_yol_seridinde_gecilebilir"),
                           "yol_disi_gecilebilir": r["teshis"].get("yol_disi_zeminde_gecilebilir")}
                          for r in k3["haritalar"]],
            "sonuc": f"DÜŞTÜ {k3['ozet']['dogru_etiket']}/{k3['ozet']['harita_n']}" if k3["ozet"]["dogru_etiket"] < k3["ozet"]["harita_n"]
                     else f"GEÇTİ {k3['ozet']['dogru_etiket']}/{k3['ozet']['harita_n']}"}
    if k3_15:
        out["H1_K3_15harita"] = {"ozet": k3_15["ozet"], "yol_dokusu": k3_15.get("yol_dokusu"),
                                 "rota_durumlari": sorted({r["rota_durum"] for r in k3_15["haritalar"]}),
                                 "sonuc": f"{k3_15['ozet']['dogru_etiket']}/{k3_15['ozet']['harita_n']} (eşik ≥ 12/15)"}
    if k3_asf:
        out["H1_K3_teshis_asfalt"] = {"not": "TEŞHİS varyantı — asıl ölçüm değil", "ozet": k3_asf["ozet"],
                                      "htab_gecilebilir": [r["teshis"].get("htab_gecilebilir_orani") for r in k3_asf["haritalar"]]}
    (H1 / "ozet_T212.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
