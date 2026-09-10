"""T213-A (K3-b) özet — `results/fdr_sprint_20260910/H1/k3b/*.json` ölçümlerinden tablo.

Elle sayı yazılmaz: RAPOR_K3B.md'deki varyant tablosu bu betiğin çıktısıdır.
Çıktı: `k3b/ozet_k3b.json` + stdout'ta Markdown tablo.

Kullanım:
  venv python simulation/mujoco/k3b_ozet.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[2]
K3B = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3b"
# (etiket, dosya kökü): <dosya>.json üretim (hb 0), <dosya>_hb2.5.json TEŞHİS (ayrı --kok, tarama_kaynak)
VARYANTLAR = (("taban", "taban_15harita"), ("v1", "v1_15harita"), ("v2", "v2_15harita"), ("v3", "v3_15harita"),
              ("v1 · yerleşim D-441 (açık yol koridoru engelsiz)", "v1_15harita_yerlesim_d441"))


def _oku(ad: str):
    p = K3B / ad
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def _ort(rows, anahtar):
    v = [r["teshis"].get(anahtar) for r in rows if r["teshis"].get(anahtar) is not None]
    return round(sum(v) / len(v), 4) if v else None


def _satir(v: str, d: dict, hb: dict | None) -> dict:
    rows = d["haritalar"]
    n = len(rows)
    ti = d.get("teshis_imgsz_ozet") or {}
    out = {
        "varyant": v, "harita_n": n,
        "rota_bulunan": d["ozet"]["rota_bulunan"], "dogru_etiket": d["ozet"]["dogru_etiket"],
        "rota_durumlari": sorted({r["rota_durum"] for r in rows}),
        "htab_gecilebilir_ort": _ort(rows, "htab_gecilebilir_orani"),
        "htab_engel_ort": _ort(rows, "htab_engel_orani"),
        "acik_yol_gecilebilir_ort": _ort(rows, "acik_yol_seridinde_gecilebilir"),
        "kapali_yol_gecilebilir_ort": _ort(rows, "kapali_yol_seridinde_gecilebilir"),
        "yol_disi_gecilebilir_ort": _ort(rows, "yol_disi_zeminde_gecilebilir"),
        "yol_disi_engel_ort": _ort(rows, "yol_disi_zeminde_engel"),
        "teshis_imgsz512": {"rota_bulunan": ti.get("rota_bulunan"), "dogru_etiket": ti.get("dogru_etiket")} if ti else None,
        "teshis_hb2_5": None,
        "mozaik": d.get("mozaik"), "zemin_dokusu": d.get("zemin_dokusu"), "tarih": d.get("tarih"),
        "kok": d.get("kok"), "kapi": d.get("kapi"),
    }
    if hb:
        out["teshis_hb2_5"] = {"rota_bulunan": hb["ozet"]["rota_bulunan"], "dogru_etiket": hb["ozet"]["dogru_etiket"],
                               "rota_durumlari": sorted({r["rota_durum"] for r in hb["haritalar"]}),
                               "hb_yaricap_m": hb.get("hb_yaricap_m"),
                               "kok": hb.get("kok"), "tarama_kaynak": hb.get("tarama_kaynak")}
    return out


def main():
    satirlar = []
    for v, dosya in VARYANTLAR:
        d = _oku(f"{dosya}.json")
        if d is None:
            continue
        satirlar.append(_satir(v, d, _oku(f"{dosya}_hb2.5.json")))
    ek = {}
    for ad in ("v1_asfalt_3harita.json", "v1_15harita_nadir_yakin.json", "v2_15harita_nadir_yakin.json",
               "v1_zemin_toprak_3harita.json"):
        d = _oku(ad)
        if d:
            ek[ad] = {"ozet": d["ozet"], "rota_durumlari": sorted({r["rota_durum"] for r in d["haritalar"]}),
                      "acik_yol_gecilebilir_ort": _ort(d["haritalar"], "acik_yol_seridinde_gecilebilir"),
                      "hb_yaricap_m": d.get("hb_yaricap_m"), "mozaik": d.get("mozaik"),
                      "yol_dokusu": d.get("yol_dokusu"), "zemin_dokusu": d.get("zemin_dokusu")}
    t212 = KOK / "results" / "fdr_sprint_20260910" / "H1" / "on_olcum_K3_15harita.json"
    t212_oz = json.loads(t212.read_text(encoding="utf-8"))["ozet"] if t212.is_file() else None
    out = {"gorev": "T213-A K3-b render varyantları (üretim modeli v36 DEĞİŞMEDİ)",
           "esik": "H1-K3 doğru etiket ≥ 12/15 (ON_KAYIT) — değişmedi",
           "T212_kaydi_15harita": t212_oz, "varyantlar": satirlar, "ek_olcumler": ek}
    (K3B / "ozet_k3b.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print("| varyant | rota bulunan | doğru etiket | rota durumları | HTAB geçilebilir (ort) | HTAB engel (ort) | "
          "açık yol şeridinde geçilebilir (ort) | kapalı yol şeridinde geçilebilir (ort) | yol dışı geçilebilir (ort) | "
          "TEŞHİS imgsz512 rota/doğru | TEŞHİS HB tohumu 2,5 m rota/doğru |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for s in satirlar:
        ti = s["teshis_imgsz512"] or {}
        hb = s["teshis_hb2_5"] or {}
        print(f"| {s['varyant']} | {s['rota_bulunan']}/{s['harita_n']} | {s['dogru_etiket']}/{s['harita_n']} | "
              f"{', '.join(s['rota_durumlari'])} | {s['htab_gecilebilir_ort']} | {s['htab_engel_ort']} | "
              f"{s['acik_yol_gecilebilir_ort']} | {s['kapali_yol_gecilebilir_ort']} | {s['yol_disi_gecilebilir_ort']} | "
              f"{ti.get('rota_bulunan', '—')}/{ti.get('dogru_etiket', '—')} | "
              f"{hb.get('rota_bulunan', '—')}/{hb.get('dogru_etiket', '—')} ({', '.join(hb.get('rota_durumlari', []))}) |")
    for ad, e in ek.items():
        print(f"| ek: {ad} | {e['ozet']['rota_bulunan']}/{e['ozet']['harita_n']} | {e['ozet']['dogru_etiket']}/{e['ozet']['harita_n']} | "
              f"{', '.join(e['rota_durumlari'])} | | | {e['acik_yol_gecilebilir_ort']} | | | | hb={e['hb_yaricap_m']} mozaik={e['mozaik']} |")
    print(f"\n[k3b_ozet] → {K3B / 'ozet_k3b.json'}")


if __name__ == "__main__":
    main()
