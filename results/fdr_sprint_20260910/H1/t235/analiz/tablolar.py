"""analiz_c_sonuc.json -> CSV tablolar + ek sayimlar (salt okuma)."""
import sys, os, json, math, csv
sys.dont_write_bytecode = True
WT = r"O:\navitas\.claude\worktrees\wf_2c28e623-233-7"
for p in ("simulation/scripts", "simulation/mujoco", "codes"):
    sys.path.insert(0, os.path.join(WT, p))
import arena, arena_mjcf

OUT = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(OUT, "analiz_c_sonuc.json"), encoding="utf-8"))


def yaz(ad, satirlar):
    with open(os.path.join(OUT, ad), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(satirlar[0].keys()))
        w.writeheader()
        for s in satirlar:
            w.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in s.items()})


yaz("etiket_k3_8kare.csv", [{k: e[k] for k in ("harita", "kare", "kare_xc", "yaw", "artik_aci", "ucte_bir_sinirlari_dunya_x",
                                                "yayinlanan", "yeniden_uretilen", "piksel_sayim_kare", "dunya_yolu",
                                                "L_merkez_ortalanmis_kare", "sayim_ortalanmis", "L_htab_ucte_bir",
                                                "rota_x_araligi", "rota_x_medyan", "yol_bu_karede_ucte_bir",
                                                "yol_gorunurluk_orani", "neden")} for e in d["etiket_k3"]])
yaz("etiket_uretim_20kare.csv", [{k: e[k] for k in ("harita", "tohum", "kare", "kare_xc", "artik_aci", "yayinlanan",
                                                     "dunya_yolu", "L_merkez_ortalanmis_kare", "L_htab_ucte_bir", "neden")}
                                  for e in d["etiket_uretim"]])
yaz("ankor_uretim_20kare.csv", d["ankor_uretim"])
yaz("surus_karsi_olgu_12.csv", [{"kosum": s["kosum"], "ankor_m": s["ankor_m"], "olculen_temas": s["olculen"]["temas"],
                                 "olculen_varis_m": s["olculen"]["varis_m"],
                                 "A_temas_ongoru": s["A_saf_oteleme"]["temas_ongoru"],
                                 "A_acik_hatta_maks_m": s["A_saf_oteleme"]["acik_hatta_maks_m"],
                                 "A_son_hb_m": s["A_saf_oteleme"]["son_hb_m"],
                                 "B_temas_ongoru": s["B_baglanti_bacagi"]["temas_ongoru"],
                                 "B_engel_acikligi_m": s["B_baglanti_bacagi"]["engel_acikligi_m"],
                                 "B_acik_hatta_maks_m": s["B_baglanti_bacagi"]["acik_hatta_maks_m"],
                                 "B_son_hb_m": s["B_baglanti_bacagi"]["son_hb_m"],
                                 "B_hb_2x2_icinde": s["B_baglanti_bacagi"]["hb_2x2_icinde"],
                                 "bacak_uzunluk_m": s["B_bacak"]["uzunluk_m"],
                                 "bacak_acik_hatta_maks_m": s["B_bacak"]["acik_hatta_maks_m"],
                                 "bacak_engel_acikligi_m": s["B_bacak"]["engel_acikligi_m"]} for s in d["surus_geometri"]])
yaz("hfov_k3_8kare.csv", d["hfov_k3"])

# ek sayimlar
son = {(a["harita"], a["tohum"]): a for a in d["ankor_uretim"]}   # son OR = listede son yazilan (sirali kareler)
son_or = []
for s in d["surus_geometri"]:
    h, lv, t = s["kosum"].split("_")
    son_or.append(next(a for a in d["ankor_uretim"] if a["harita"] == f"{h}_{lv}" and a["tohum"] == int(t) and a["kare"] == s["son_or_kare"]))
ek = {
    "son_or_model55_gt_model74": sum(a["model55_ankor_m"] > a["model74_ankor_m"] for a in son_or), "son_or_n": len(son_or),
    "tum_or_model55_gt_model74": sum(a["model55_ankor_m"] > a["model74_ankor_m"] for a in d["ankor_uretim"]),
    "tum_or_n": len(d["ankor_uretim"]),
    "A_temas_ongoru_n": sum(s["A_saf_oteleme"]["temas_ongoru"] for s in d["surus_geometri"]),
    "olculen_temas_n": sum(s["olculen"]["temas"] > 0 for s in d["surus_geometri"]),
    "B_temas_ongoru_n": sum(s["B_baglanti_bacagi"]["temas_ongoru"] for s in d["surus_geometri"]),
    "B_engel_acikligi_ozet": sorted(s["B_baglanti_bacagi"]["engel_acikligi_m"] for s in d["surus_geometri"]),
    "B_hb_icinde_n": sum(s["B_baglanti_bacagi"]["hb_2x2_icinde"] for s in d["surus_geometri"]),
    "A_hb_icinde_n": sum(s["A_saf_oteleme"]["hb_2x2_icinde"] for s in d["surus_geometri"]),
    "A_en_yakin_yol_ort": sorted({s["A_saf_oteleme"]["en_yakin_yol_ort"] for s in d["surus_geometri"]}),
}
# 4:3 sensor (IMX477 6.287 x 4.712 mm, 6 mm) TAHMIN
hf_h = 2 * math.atan(6.287 / 12.0)
hf_v = 2 * math.atan(4.712 / 12.0)
ek["iz_4_3_30m_TAHMIN"] = [round(2 * 30 * math.tan(hf_h / 2), 2), round(2 * 30 * math.tan(hf_v / 2), 2)]
ek["hfov_vfov_TAHMIN_derece"] = [round(math.degrees(hf_h), 2), round(math.degrees(hf_v), 2)]
ek["z_gerekli_Dy44_uzun_kenar_boyuna"] = round(44.0 / (2 * math.tan(hf_h / 2)), 1)
ek["z_gerekli_Dy44_kisa_kenar_boyuna"] = round(44.0 / (2 * math.tan(hf_v / 2)), 1)
ek["z_gerekli_Dy44_sim"] = round(44.0 / (2 * math.tan(arena_mjcf.HFOV_RAD / 2)), 1)
# xc=-18 karelerinde yol 3'un gorunen noktalarinin y araligi (KB/HB yakinsamasi mi)
fw = 2 * 30 * math.tan(arena_mjcf.HFOV_RAD / 2)
g = {}
for e in d["etiket_k3"]:
    if e["kare_xc"] != -18.0:
        continue
    h, lv = e["harita"].split("_")
    Hm = arena.harita(int(h), lv)
    P = arena_mjcf._yol_ornekle(Hm["paths"][3], 0.25)
    ys = [y for x, y in P if abs(x - e["kare_xc"]) <= fw / 2 and abs(y - e["kare_yc"]) <= fw / 2]
    g[f'{e["harita"]}_k{e["kare"]}'] = [round(min(ys), 2), round(max(ys), 2)] if ys else None
ek["xc_-18_yol3_gorunen_y_araligi"] = g
json.dump(ek, open(os.path.join(OUT, "ek_sayimlar.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(ek, ensure_ascii=False, indent=1))
