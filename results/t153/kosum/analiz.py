"""T153 ANALIZ — ACIK vs KAPALI 142 ciktilarindan (results/t153/olcum) tablo + benimseme kurali.

Kural ON_KAYIT §13 (sonuc gorulmeden yazildi; burada yalniz UYGULANIR):
  v35'te 111 karede YANLIS GUZERGAH >= %50 azalir VE mesru rota kaybi <= 1 VE yeni FP 0
  VE sentetik K1-K6 birebir VE 67'de red <= 5.
Tanimlar:
  mesru rota kaybi = KAPALI'da TP (model rota VE tavan rota) olup ACIK'ta rota uretmeyen kare
  (bilgi: 'TP ve yol ustunde' daraltilmis sayim da yazilir)
  yeni FP = ACIK'ta tavana gore FP olup KAPALI'da FP olmayan kare
Cikti: results/t153/analiz.json + stdout tablo (rapora yapistirilir).
"""
import io
import json
import sys
from pathlib import Path

T153 = Path(__file__).resolve().parents[1]
OLCUM = T153 / "olcum"
KABUL = T153 / "kabul"
ANA_T63 = Path(r"O:\navitas\scripts\olcum\results\t63")


def yukle(ad):
    p = OLCUM / f"{ad}_olcum.json"
    if not p.is_file():
        return None
    d = json.load(io.open(p, encoding="utf-8"))
    d126 = json.load(io.open(d["test29"]["json"], encoding="utf-8"))
    v = list(d126["modeller"].values())[0]
    kareler = {}
    tavan = json.load(io.open(d["tavan"], encoding="utf-8"))
    tav = {s["kare"]: s["rota"] for s in tavan["kareler"]}
    ry = {r["kare"]: r for r in d.get("rota_yol", {}).get("rota_yol", [])}
    for s in v["kareler"]:
        k = s["kare"]
        rota = s["olceksiz_sebep"] is None
        yanlis = bool(ry[k]["yanlis_guzergah"]) if (rota and k in ry) else None
        kareler[k] = {"rota": rota, "sebep": s["olceksiz_sebep"], "tavan": tav.get(k),
                      "yanlis": yanlis, "wps": s.get("olceksiz_wps", []),
                      "yol_payi": ry[k]["yol_payi"] if k in ry else None,
                      "engel_wp": ry[k]["engel_wp"] if k in ry else None}
    return {"ozet": d, "kareler": kareler}


def ozet(k):
    rota = [a for a, s in k.items() if s["rota"]]
    return {"n": len(k), "rota": len(rota),
            "yanlis": sum(1 for a in rota if k[a]["yanlis"]),
            "yol_ustunde": sum(1 for a in rota if k[a]["yanlis"] is False),
            "TP": sum(1 for a in rota if k[a]["tavan"]),
            "FP": sum(1 for a in rota if k[a]["tavan"] is False),
            "FN": sum(1 for a, s in k.items() if (not s["rota"]) and s["tavan"]),
            "TP_yol_ustunde": sum(1 for a in rota if k[a]["tavan"] and k[a]["yanlis"] is False),
            "maske_yok": sum(1 for s in k.values() if s["sebep"] == "MASKE_YOK"),
            "uc_bant": sum(1 for s in k.values() if s["sebep"] == "UC_BANT_TEMAS_YOK")}


def kiyas(kap, ac):
    """KAPALI -> ACIK gecisleri."""
    g = {"yanlis->yol_ustunde": [], "yanlis->rota_yok": [], "yanlis->yanlis": [],
         "yol_ustunde->rota_yok": [], "yol_ustunde->yanlis": [], "rota_yok->rota": [],
         "mesru_rota_kaybi": [], "mesru_rota_kaybi_yol_ustunde": [], "yeni_FP": [], "kaybolan_FP": []}
    for a, s in kap.items():
        t = ac[a]
        if s["rota"] and s["yanlis"]:
            if not t["rota"]:
                g["yanlis->rota_yok"].append(a)
            elif t["yanlis"]:
                g["yanlis->yanlis"].append(a)
            else:
                g["yanlis->yol_ustunde"].append(a)
        elif s["rota"] and s["yanlis"] is False:
            if not t["rota"]:
                g["yol_ustunde->rota_yok"].append(a)
            elif t["yanlis"]:
                g["yol_ustunde->yanlis"].append(a)
        elif not s["rota"] and t["rota"]:
            g["rota_yok->rota"].append(a)
        if s["rota"] and s["tavan"] and not t["rota"]:
            g["mesru_rota_kaybi"].append(a)
            if s["yanlis"] is False:
                g["mesru_rota_kaybi_yol_ustunde"].append(a)
        if t["rota"] and t["tavan"] is False and not (s["rota"] and s["tavan"] is False):
            g["yeni_FP"].append(a)
        if s["rota"] and s["tavan"] is False and not (t["rota"] and t["tavan"] is False):
            g["kaybolan_FP"].append(a)
    return g


def k6_kiyas(model):
    """65 verdikti: ACIK (results/t153/kabul) vs KAPALI referans (t63/k6_<model>_kabul_verdikt.json)."""
    ac = KABUL / f"t153_acik_{model}_kabul_verdikt.json"
    ref = ANA_T63 / f"k6_{model}_kabul_verdikt.json"
    if not ac.is_file() or not ref.is_file():
        return None
    A = json.load(io.open(ac, encoding="utf-8"))
    R = json.load(io.open(ref, encoding="utf-8"))
    alanlar = ["K1_rota", "K2_basma", "K3_agir", "K4_arena_disi", "K6_yanlis_guzergah", "K6_oran",
               "K6_yanlis_kareler", "K5_durum", "K5_kesen_kare", "K5_kesisim_px", "K5_olculebilir_kare"]
    fark = {}
    for f in alanlar:
        a, r = A["olcum"].get(f), R["olcum"].get(f)
        if a != r:
            fark[f] = {"acik": a, "kapali_ref": r}
    k0 = (round(A["olcum"]["K0"]["figur"], 6), round(R["olcum"]["K0"]["figur"], 6))
    return {"birebir": not fark and A["gecti"] == R["gecti"], "fark": fark,
            "gecti_acik": A["gecti"], "gecti_ref": R["gecti"], "verdikt_acik": A["verdikt"], "verdikt_ref": R["verdikt"],
            "K0_figur": {"acik": k0[0], "ref": k0[1]},
            "K1_acik": A["olcum"]["K1_rota"], "K1_ref": R["olcum"]["K1_rota"],
            "K6_acik": A["olcum"]["K6_yanlis_guzergah"], "K6_ref": R["olcum"]["K6_yanlis_guzergah"]}


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sonuc = {"_ne": "T153 ACIK vs KAPALI analiz (ON_KAYIT §13)", "modeller": {}}
    satirlar = []
    for m in ("v35", "v3", "v6"):
        M = {"bolum": {}, "gecis": {}, "kural": None}
        toplam = {"kapali": {}, "acik": {}}
        for b in ("test29", "val82"):
            kap, ac = yukle(f"t153_kapali_{m}_{b}"), yukle(f"t153_acik_{m}_{b}")
            if kap is None or ac is None:
                M["bolum"][b] = {"eksik": True, "kapali": kap is not None, "acik": ac is not None}
                continue
            ok, oa = ozet(kap["kareler"]), ozet(ac["kareler"])
            g = kiyas(kap["kareler"], ac["kareler"])
            red = {"kapali": kap["ozet"]["k109"]["zemin_maskesi_reddi"], "acik": ac["ozet"]["k109"]["zemin_maskesi_reddi"]}
            M["bolum"][b] = {"kapali": ok, "acik": oa, "gecis": {k: v for k, v in g.items()},
                             "gecis_n": {k: len(v) for k, v in g.items()}, "red67": red,
                             "kapali_kareler": {a: {kk: vv for kk, vv in s.items() if kk != "wps"} for a, s in kap["kareler"].items()},
                             "acik_kareler": {a: {kk: vv for kk, vv in s.items() if kk != "wps"} for a, s in ac["kareler"].items()}}
            toplam["kapali"][b], toplam["acik"][b] = kap["kareler"], ac["kareler"]
            satirlar.append((m, b, ok, oa, {k: len(v) for k, v in g.items()}, red))
        if len(toplam["kapali"]) == 2:
            K = {**toplam["kapali"]["test29"], **toplam["kapali"]["val82"]}
            A = {**toplam["acik"]["test29"], **toplam["acik"]["val82"]}
            ok, oa, g = ozet(K), ozet(A), kiyas(K, A)
            M["bolum"]["111"] = {"kapali": ok, "acik": oa, "gecis_n": {k: len(v) for k, v in g.items()}, "gecis": g}
            satirlar.append((m, "111", ok, oa, {k: len(v) for k, v in g.items()}, None))
            k6 = k6_kiyas(m)
            red_acik = max(M["bolum"][b]["red67"]["acik"] for b in ("test29", "val82"))
            azalma = (ok["yanlis"] - oa["yanlis"]) / ok["yanlis"] if ok["yanlis"] else None
            M["kural"] = {
                "yanlis_kapali": ok["yanlis"], "yanlis_acik": oa["yanlis"], "azalma_orani": None if azalma is None else round(azalma, 3),
                "yanlis_>=%50_azaldi": (azalma is not None and azalma >= 0.5),
                "mesru_rota_kaybi": len(g["mesru_rota_kaybi"]), "mesru_rota_kaybi_<=1": len(g["mesru_rota_kaybi"]) <= 1,
                "mesru_rota_kaybi_yol_ustunde_bilgi": len(g["mesru_rota_kaybi_yol_ustunde"]),
                "yeni_FP": len(g["yeni_FP"]), "yeni_FP_0": len(g["yeni_FP"]) == 0,
                "K1_K6_birebir": None if k6 is None else k6["birebir"], "k6": k6,
                "red67_acik": red_acik, "red67_<=5": red_acik <= 5,
            }
            M["kural"]["SAGLANDI"] = all(M["kural"][k] is True for k in
                                         ("yanlis_>=%50_azaldi", "mesru_rota_kaybi_<=1", "yeni_FP_0", "K1_K6_birebir", "red67_<=5"))
        M["k6"] = k6_kiyas(m)
        sonuc["modeller"][m] = M
    (T153 / "analiz.json").write_text(json.dumps(sonuc, indent=1, ensure_ascii=False), encoding="utf-8")
    print("| model | bolum | ROTA K/A | YANLIS K/A | yol ustunde K/A | TP K/A | FP K/A | FN K/A | MASKE_YOK K/A | mesru kayip (yol ust.) | yeni FP | yanlis->yol | yanlis->yok | yol->yok | red67 K/A |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for m, b, ok, oa, g, red in satirlar:
        print(f"| {m} | {b} | {ok['rota']}/{oa['rota']} | {ok['yanlis']}/{oa['yanlis']} | {ok['yol_ustunde']}/{oa['yol_ustunde']} | "
              f"{ok['TP']}/{oa['TP']} | {ok['FP']}/{oa['FP']} | {ok['FN']}/{oa['FN']} | {ok['maske_yok']}/{oa['maske_yok']} | "
              f"{g['mesru_rota_kaybi']} ({g['mesru_rota_kaybi_yol_ustunde']}) | {g['yeni_FP']} | {g['yanlis->yol_ustunde']} | {g['yanlis->rota_yok']} | "
              f"{g['yol_ustunde->rota_yok']} | {'-' if red is None else str(red['kapali']) + '/' + str(red['acik'])} |")
    for m, M in sonuc["modeller"].items():
        if M.get("kural"):
            print(f"\n{m} KURAL (ON_KAYIT §13):", json.dumps({k: v for k, v in M['kural'].items() if k != 'k6'}, ensure_ascii=False))
        if M.get("k6"):
            print(f"{m} K1-K6:", json.dumps({k: v for k, v in M['k6'].items() if k != 'fark'}, ensure_ascii=False), "fark:", json.dumps(M["k6"]["fark"], ensure_ascii=False)[:600])
    print("yazildi:", T153 / "analiz.json")


if __name__ == "__main__":
    main()
