"""ANALIZ C - SIM KANITI (salt okuma; GPU yok; surus benzetimi YOK; yalniz JSON + geometri).
Girdi: worktree-wf_2c28e623-233-7 calisma agaci (degistirilmez). Cikti: bu betigin klasoru.
"""
import sys, os, json, math, glob, statistics as st
sys.dont_write_bytecode = True
WT = r"O:\navitas\.claude\worktrees\wf_2c28e623-233-7"
for p in ("simulation/scripts", "simulation/mujoco", "codes", "comms"):
    sys.path.insert(0, os.path.join(WT, p))
import numpy as np, cv2
import arena, arena_mjcf
import sim_karar_toplayici as skt
from karar_sozlesmesi import rota_serit_karari, HEDEF_BANT_ORANI

OUT = os.path.dirname(os.path.abspath(__file__))
H1 = os.path.join(WT, "results/fdr_sprint_20260910/H1")
W = HH = 1280
HFOV_SIM = arena_mjcf.HFOV_RAD
HFOV_GERCEK = 2 * math.atan(6.287 / (2 * 6.0))   # IMX477 aktif genislik 6.287 mm + 6 mm lens: TAHMIN
Z = 30.0


def iz(hfov, z=Z):
    return 2 * z * math.tan(hfov / 2)


def ozet(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    return {"n": len(v), "min": round(min(v), 2), "medyan": round(st.median(v), 2),
            "ort": round(sum(v) / len(v), 2), "maks": round(max(v), 2)}


def yol_x_at_y(path, yq):
    """Merkez hattinin y=yq'daki x'i (y'de ilk kesisim)."""
    for (x0, y0), (x1, y1) in zip(path, path[1:]):
        if (y0 - yq) * (y1 - yq) <= 0 and y1 != y0:
            t = (yq - y0) / (y1 - y0)
            return x0 + t * (x1 - x0)
    return None


def rasterla(px_list):
    c = np.zeros((HH, W), np.uint8)
    pts = np.round(np.array(px_list)).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(c, [pts], False, 255, 1)
    ys, xs = np.nonzero(c)
    return list(zip(xs.tolist(), ys.tolist()))


def ucte_bir_dunya(xw, xc, genislik_m):
    """Dunya x -> x_c merkezli genislik_m karenin ucte-biri (1..3); kare disi -> None."""
    u = (xw - (xc - genislik_m / 2)) / genislik_m
    if u < 0 or u >= 1:
        return None
    return 1 + min(2, int(u * 3))


def cogunluk(etiketler):
    s = [0, 0, 0]
    for e in etiketler:
        if e:
            s[e - 1] += 1
    if not any(s):
        return None, s
    return max(range(3), key=lambda i: (s[i], -i)) + 1, s


def kareler_or(d):
    return [s for s in d["kareler"] if s.get("karar") == "OPEN_ROUTE"]


def yogun(P, adim=0.25):
    return arena_mjcf._yol_ornekle(P, adim)


# ---------------------------------------------------------------- (1) etiket
def etiket_ayristir(d, s, kaynak):
    Hm = arena.harita(d["harita"], d["senaryo"])
    poz = (s["n"], s["t"], s["x"], s["y"], s["z"], math.radians(s["yaw_derece"]))
    teta = math.radians(s["teta_derece"])
    mpp = s["mpp"]
    fw = W * mpp                                  # karenin dunya genisligi (m)
    wp_px = [skt.dunya_piksel(a, b, poz, W, HH, mpp, teta) for a, b in s["rota_dunya"]]
    geri = [skt.piksel_dunya(px, py, poz, W, HH, mpp, teta) for px, py in wp_px]
    rt_hata = max(math.dist(g, r) for g, r in zip(geri, s["rota_dunya"]))
    pix = rasterla(wp_px)
    L_yeniden, say = rota_serit_karari(pix, 0, W)
    wx = [skt.piksel_dunya(px, py, poz, W, HH, mpp, teta)[0] for px, py in pix]
    L_merkez, say_m = cogunluk([ucte_bir_dunya(x, 0.0, fw) for x in wx])        # ayni kare HTAB x=0'a ortalansa
    L_htab, say_h = cogunluk([ucte_bir_dunya(x, 0.0, arena.HTAB) for x in wx])  # HTAB 50 m ucte-birleri
    y_lo = min(p[1] for p in s["rota_dunya"])
    y_hi = max(p[1] for p in s["rota_dunya"])
    yol_harita, gorunur = {}, {}
    for r in (1, 2, 3):
        P = yogun(Hm["paths"][r])
        ic = [skt.karede_mi(x, y, poz, W, HH, mpp, teta) for x, y in P]
        gorunur[r] = round(sum(ic) / len(ic), 2)
        seg = [(x, y) for (x, y), k in zip(P, ic) if k and y_lo <= y <= y_hi]
        e = cogunluk([ucte_bir_dunya(x, s["x"], fw) for x, _y in seg])[0] if seg else None
        yol_harita[r] = e
    dunya = s["rota_dunya_yolu"]
    if L_yeniden != s["yol"]:
        neden = "YENIDEN_URETILEMEDI"
    elif s["yol"] == dunya:
        neden = "ESLESIYOR"
    elif s["artik_aci_derece"] not in (0, 0.0):
        neden = "YAW/EKSEN"
    elif L_merkez == dunya:
        neden = "KARE_MERKEZI_KAYMASI"
    else:
        neden = "GORUNURLUK/KIVRIM"
    return {"kaynak": kaynak, "harita": f'{d["harita"]}_{d["senaryo"]}', "tohum": d["seed"], "kare": s["n"],
            "acik": d["acik_yol"], "kare_xc": s["x"], "kare_yc": s["y"], "yaw": s["yaw_derece"],
            "artik_aci": s["artik_aci_derece"], "kare_genislik_m": round(fw, 2),
            "ucte_bir_sinirlari_dunya_x": [round(s["x"] - fw / 2 + fw * k / 3, 2) for k in range(4)],
            "yayinlanan": s["yol"], "yeniden_uretilen": L_yeniden, "piksel_sayim_kare": list(say),
            "dunya_yolu": dunya, "dunya_ort_uzaklik": s["rota_dunya_ort_uzaklik_m"],
            "L_merkez_ortalanmis_kare": L_merkez, "sayim_ortalanmis": say_m,
            "L_htab_ucte_bir": L_htab, "sayim_htab": say_h,
            "rota_x_araligi": [round(min(wx), 2), round(max(wx), 2)],
            "rota_x_medyan": round(float(np.median(wx)), 2),
            "yol_bu_karede_ucte_bir": yol_harita, "yol_gorunurluk_orani": gorunur,
            "kayma_ucte_bir_birimi": round(s["x"] / (fw / 3), 2),
            "geri_donus_hata_m": round(rt_hata, 3), "neden": neden}


def yukle(desen, anahtar):
    out = {}
    for f in sorted(glob.glob(os.path.join(H1, desen))):
        d = json.load(open(f, encoding="utf-8"))
        out[anahtar(d)] = d
    return out


k3 = yukle("k3_uretim_boru/kerteriz/harita_*.json", lambda d: (d["harita"], d["senaryo"]))
ham = yukle("k3_uretim_boru/ham/harita_*.json", lambda d: (d["harita"], d["senaryo"]))
uret = yukle("kosum_tur3/uretim_*/karar_toplayici.json", lambda d: (d["harita"], d["senaryo"], d["seed"]))

E_k3 = [etiket_ayristir(d, s, "K3_kerteriz") for d in k3.values() for s in kareler_or(d)]
E_ur = [etiket_ayristir(d, s, "kosum_tur3_uretim") for d in uret.values() for s in kareler_or(d)]

E_ham = []
for d in ham.values():
    for s in kareler_or(d):
        poz = (s["n"], s["t"], s["x"], s["y"], s["z"], math.radians(s["yaw_derece"]))
        wp_px = [skt.dunya_piksel(a, b, poz, W, HH, s["mpp"], 0.0) for a, b in s["rota_dunya"]]
        pix = rasterla(wp_px)
        L, say = rota_serit_karari(pix, 0, W)
        E_ham.append({"harita": f'{d["harita"]}_{d["senaryo"]}', "kare": s["n"], "yaw": s["yaw_derece"],
                      "yayinlanan": s["yol"], "yeniden": L, "sayim": list(say), "dunya_yolu": s["rota_dunya_yolu"],
                      "dunya_ort_uzaklik": s["rota_dunya_ort_uzaklik_m"], "dunya_ayrim_m": s["rota_dunya_ayrim_m"],
                      "rota_ilk": s["rota_ilk_dunya"], "rota_son": s["rota_son_dunya"],
                      "rota_uzunluk_m": round(sum(math.dist(a, b) for a, b in zip(s["rota_dunya"], s["rota_dunya"][1:])), 2),
                      "px_x_araligi": [round(min(p[0] for p in wp_px), 1), round(max(p[0] for p in wp_px), 1)]})


# ---------------------------------------------------------------- (2) ankor
def ankor_ayristir(d, s):
    Hm = arena.harita(d["harita"], d["senaryo"])
    kb = Hm["kb"]
    acik = Hm["open"]
    fw = W * s["mpp"]
    ilk = s["rota_ilk_dunya"]
    y_alt = s["y"] - fw / 2                    # kerteriz kuzey-yukari: kare alt kenari = guney
    bant = HEDEF_BANT_ORANI * fw
    yx = yol_x_at_y(Hm["paths"][acik], ilk[1])

    def model(fw_):
        # GEOMETRI MODELI: rota baslangici = acik yol merkez hatti x (alt kenar + bant ust siniri)
        yb = s["y"] - fw_ / 2 + HEDEF_BANT_ORANI * fw_
        if yb < kb[1]:
            yb = kb[1]
        xb = yol_x_at_y(Hm["paths"][acik], yb)
        return None if xb is None else (math.dist((xb, yb), kb), xb, yb)

    m74 = model(fw)
    m55 = model(iz(HFOV_GERCEK))
    return {"harita": f'{d["harita"]}_{d["senaryo"]}', "tohum": d["seed"], "kare": s["n"],
            "kare_xc": s["x"], "kare_yc": s["y"], "z": s["z"], "artik_aci": s["artik_aci_derece"],
            "ankor_m": s["ankor_kb_uzakligi_m"], "dx_m": round(ilk[0] - kb[0], 2), "dy_m": round(ilk[1] - kb[1], 2),
            "kare_alt_kenar_y": round(y_alt, 2), "kb_alt_kenarin_altinda_m": round(y_alt - kb[1], 2),
            "baslangic_alt_kenardan_m": round(ilk[1] - y_alt, 2), "bant_m": round(bant, 2),
            "acik_yol_x_baslangic_y": (None if yx is None else round(yx, 2)),
            "yol_ayrismasi_dx_m": (None if yx is None else round(yx - kb[0], 2)),
            "baslangic_yol_merkezine_m": (None if yx is None else round(ilk[0] - yx, 2)),
            "model74_ankor_m": (None if m74 is None else round(m74[0], 2)),
            "model55_ankor_m": (None if m55 is None else round(m55[0], 2)),
            "model55_baslangic": (None if m55 is None else [round(m55[1], 2), round(m55[2], 2)])}


A_k3 = [ankor_ayristir(d, s) for d in k3.values() for s in kareler_or(d)]
A_ur = [ankor_ayristir(d, s) for d in uret.values() for s in kareler_or(d)]
A_ur_son = [ankor_ayristir(d, kareler_or(d)[-1]) for d in uret.values() if kareler_or(d)]

fw74 = iz(HFOV_SIM)
kbhb = []
for (h, lv), d in sorted(k3.items()):
    Hm = arena.harita(h, lv)
    kb, hb = Hm["kb"], Hm["hb"]
    D = max(abs(hb[0] - kb[0]), abs(hb[1] - kb[1]))
    tb = [s for s in d["kareler"] if s["tarama_bacagi"]]
    eksik = [max(abs(kb[0] - s["x"]), abs(kb[1] - s["y"]), abs(hb[0] - s["x"]), abs(hb[1] - s["y"])) - fw74 / 2
             for s in tb]
    kbhb.append({"harita": f"{h}_{lv}", "kb": [round(v, 2) for v in kb], "hb": [round(v, 2) for v in hb],
                 "Dy_m": round(hb[1] - kb[1], 2), "Dx_m": round(abs(hb[0] - kb[0]), 2), "D_inf_m": round(D, 2),
                 "gereken_z_74_5": round(D / (2 * math.tan(HFOV_SIM / 2)), 1),
                 "gereken_z_55": round(D / (2 * math.tan(HFOV_GERCEK / 2)), 1),
                 "tarama_kare_n": len(tb), "en_iyi_kare_eksik_m": round(min(eksik), 2),
                 "y_penceresi_74_5": [round(hb[1] - fw74 / 2, 2), round(kb[1] + fw74 / 2, 2)],
                 "tarama_y_konumlari": sorted({round(s["y"], 2) for s in tb})})


# ---------------------------------------------------------------- (3) karsi-olgu
def hukum(d, etiket_fn):
    """On kayit kurali; OR mesajlarinin etiketi etiket_fn(kare) ile degistirilir (kare<->mesaj 1:1)."""
    orl = kareler_or(d)
    if not orl:
        return False
    return all(etiket_fn(s) == d["acik_yol"] for s in orl)


ek = {(e["harita"], e["kare"]): e for e in E_k3}


def _ek(d, s, alan):
    return ek[(f'{d["harita"]}_{d["senaryo"]}', s["n"])][alan]


k3_hukum = {
    "yayinlanan": sum(hukum(d, lambda s: s["yol"]) for d in k3.values()),
    "dunya_yolu_sim_ozel": sum(hukum(d, lambda s: s["rota_dunya_yolu"]) for d in k3.values()),
    "L_merkez_kare_HTABa_ortalanmis": sum(hukum(d, lambda s, d=d: _ek(d, s, "L_merkez_ortalanmis_kare")) for d in k3.values()),
    "L_htab_50m_ucte_bir": sum(hukum(d, lambda s, d=d: _ek(d, s, "L_htab_ucte_bir")) for d in k3.values()),
    "harita_n": len(k3)}
kare_esleme = {
    "yayinlanan=dunya": sum(e["yayinlanan"] == e["dunya_yolu"] for e in E_k3),
    "L_merkez=dunya": sum(e["L_merkez_ortalanmis_kare"] == e["dunya_yolu"] for e in E_k3),
    "L_htab=dunya": sum(e["L_htab_ucte_bir"] == e["dunya_yolu"] for e in E_k3),
    "dunya=acik": sum(e["dunya_yolu"] == e["acik"] for e in E_k3),
    "yeniden_uretilen=yayinlanan": sum(e["yeniden_uretilen"] == e["yayinlanan"] for e in E_k3),
    "n": len(E_k3)}
kare_esleme_ur = {
    "yayinlanan=dunya": sum(e["yayinlanan"] == e["dunya_yolu"] for e in E_ur),
    "L_merkez=dunya": sum(e["L_merkez_ortalanmis_kare"] == e["dunya_yolu"] for e in E_ur),
    "L_htab=dunya": sum(e["L_htab_ucte_bir"] == e["dunya_yolu"] for e in E_ur),
    "dunya=acik": sum(e["dunya_yolu"] == e["acik"] for e in E_ur),
    "yeniden_uretilen=yayinlanan": sum(e["yeniden_uretilen"] == e["yayinlanan"] for e in E_ur),
    "n": len(E_ur)}


def hat_uzaklik(P, path):
    return [arena.dist_to_path(x, y, path) for x, y in P]


def engel_acikligi(P, Y):
    en, ad = math.inf, None
    for b in Y["bariyer"]:
        a = arena_mjcf._kutu_aciklik(P, b["x"], b["y"], b["w"], 0.5, b["yaw"])
        if a < en:
            en, ad = a, f"bariyer_{b['road']}"
    for g in ("tikama", "moloz", "chicane"):
        for mz in Y[g]:
            a = arena_mjcf._moloz_aciklik(P, mz)
            if a < en:
                en, ad = a, mz["ad"]
    return en, ad


def secenek_olc(P, Hm, Y, yari_g):
    Ps = yogun(P)
    u = hat_uzaklik(Ps, Hm["paths"][Hm["open"]])
    uz = {r: float(np.mean(hat_uzaklik(Ps, Hm["paths"][r]))) for r in (1, 2, 3)}
    ac, ad = engel_acikligi(Ps, Y)
    son = P[-1]
    hb = Hm["hb"]
    icinde = abs(son[0] - hb[0]) <= 1.0 and abs(son[1] - hb[1]) <= 1.0
    return {"acik_hatta_maks_m": round(max(u), 2), "acik_hatta_ort_m": round(float(np.mean(u)), 2),
            "en_yakin_yol_ort": min(uz, key=uz.get), "engel_acikligi_m": round(ac, 2), "en_yakin_engel": ad,
            "temas_ongoru": bool(ac < yari_g), "son_hb_m": round(math.dist(son, hb), 2), "hb_2x2_icinde": bool(icinde),
            "htab_disina_tasar": bool(np.any(np.abs(Ps) > arena.HTAB_HALF)),
            "uzunluk_m": round(sum(math.dist(a, b) for a, b in zip(P, P[1:])), 2)}


surus = []
for (h, lv, seed), d in sorted(uret.items()):
    kj = json.load(open(os.path.join(H1, f"kosum_tur3/uretim_{h}_{lv}_{seed}.json"), encoding="utf-8"))
    orl = kareler_or(d)
    if not orl:
        continue
    s = orl[-1]
    Hm = arena.harita(h, lv)
    kb = Hm["kb"]
    Y = arena_mjcf.yerlesim(Hm, lv, seed, "field")
    yari_g = kj.get("ika_yari_genislik_m", 0.22)
    yerel = d["son_open_route"]["waypoints"]
    P_ot = [(kb[0] + x, kb[1] + y) for x, y in yerel]                   # A: saf oteleme (ika_nav.py:203)
    rd = [tuple(p) for p in s["rota_dunya"]]
    P_bag = [tuple(kb)] + rd                                            # B: KB -> rota ilk nokta + dunya rotasi
    dn_son = (rd[-1][0] - rd[0][0], rd[-1][1] - rd[0][1])
    fark = round(math.dist(yerel[-1], dn_son), 3)
    bag = yogun([tuple(kb), rd[0]])
    bag_u = hat_uzaklik(bag, Hm["paths"][Hm["open"]])
    bag_ac, bag_ad = engel_acikligi(bag, Y)
    surus.append({"kosum": f"{h}_{lv}_{seed}", "acik": d["acik_yol"], "son_or_kare": s["n"], "son_or_etiket": s["yol"],
                  "son_or_dunya_yolu": s["rota_dunya_yolu"], "ankor_m": s["ankor_kb_uzakligi_m"],
                  "oteleme_vektoru_m": [round(kb[0] - rd[0][0], 2), round(kb[1] - rd[0][1], 2)],
                  "yerel_son_vs_dunya_farki_m": fark,
                  "olculen": {"temas": kj["temas_sayisi"], "temas_geomlari": kj["temas_geomlari"],
                              "takip_maks_m": kj["takip_hatasi_maks_m"], "varis_m": kj["varis_mesafesi_m"],
                              "son_konum": kj["son_konum"], "kod": kj["cikis_kodu"]},
                  "A_saf_oteleme": secenek_olc(P_ot, Hm, Y, yari_g),
                  "B_baglanti_bacagi": secenek_olc(P_bag, Hm, Y, yari_g),
                  "B_bacak": {"uzunluk_m": round(math.dist(kb, rd[0]), 2), "acik_hatta_maks_m": round(max(bag_u), 2),
                              "engel_acikligi_m": round(bag_ac, 2), "en_yakin_engel": bag_ad,
                              "kapali_yol_hatlarina_min_m": {r: round(min(hat_uzaklik(bag, Hm["paths"][r])), 2)
                                                             for r in (1, 2, 3) if r != Hm["open"]}},
                  "C_rota_dunya_bacaksiz": secenek_olc(rd, Hm, Y, yari_g),
                  "yari_genislik_m": yari_g})

# ---------------------------------------------------------------- (4) hfov
fw55 = iz(HFOV_GERCEK)
hf = []
for d in k3.values():
    for s in kareler_or(d):
        e = ek[(f'{d["harita"]}_{d["senaryo"]}', s["n"])]
        rd = s["rota_dunya"]
        P = yogun([tuple(p) for p in rd], 0.1)
        kirp = [(x, y) for x, y in P if abs(x - s["x"]) <= fw55 / 2 and abs(y - s["y"]) <= fw55 / 2]
        L55 = cogunluk([ucte_bir_dunya(x, s["x"], fw55) for x, _ in kirp])[0] if kirp else None
        Hm = arena.harita(d["harita"], d["senaryo"])
        gor55 = {}
        for r in (1, 2, 3):
            Pr = yogun(Hm["paths"][r])
            gor55[r] = round(sum(abs(x - s["x"]) <= fw55 / 2 and abs(y - s["y"]) <= fw55 / 2 for x, y in Pr) / len(Pr), 2)
        hf.append({"harita": e["harita"], "kare": e["kare"], "kare_xc": s["x"], "kare_yc": s["y"],
                   "yayinlanan_74": s["yol"], "dunya": e["dunya_yolu"],
                   "rota_uzunlugunun_55_karede_orani": round(len(kirp) / len(P), 2),
                   "L55_kirpik_rota_TAHMIN": L55, "yol_gorunurluk_55": gor55,
                   "yol_gorunurluk_74": e["yol_gorunurluk_orani"]})


def genel_esleme(fw):
    """Tum tarama-bacagi kareleri x 3 yol: yolun (karedeki merkez hatti) kare-goreli ucte-biri == dunya yol no?
    Algi MUKEMMEL varsayimi (yalniz geometri)."""
    n = esit = gor = 0
    for (h, lv), d in k3.items():
        Hm = arena.harita(h, lv)
        yp = {r: yogun(Hm["paths"][r]) for r in (1, 2, 3)}
        for s in d["kareler"]:
            if not s["tarama_bacagi"]:
                continue
            for r in (1, 2, 3):
                seg = [(x, y) for x, y in yp[r] if abs(x - s["x"]) <= fw / 2 and abs(y - s["y"]) <= fw / 2]
                n += 1
                if not seg:
                    continue
                gor += 1
                esit += (cogunluk([ucte_bir_dunya(x, s["x"], fw) for x, _ in seg])[0] == r)
    return {"kare_x_yol": n, "yol_karede_gorunur": gor, "ucte_bir_eq_dunya": esit}


def kare_xc_esleme(fw):
    """Kare merkez x'i basina (bacak) ayni sayim."""
    out = {}
    for (h, lv), d in k3.items():
        Hm = arena.harita(h, lv)
        yp = {r: yogun(Hm["paths"][r]) for r in (1, 2, 3)}
        for s in d["kareler"]:
            if not s["tarama_bacagi"]:
                continue
            o = out.setdefault(str(s["x"]), {"n": 0, "gorunur": 0, "esit": 0, "harita_yol_ucte_bir": {}})
            for r in (1, 2, 3):
                seg = [(x, y) for x, y in yp[r] if abs(x - s["x"]) <= fw / 2 and abs(y - s["y"]) <= fw / 2]
                o["n"] += 1
                if not seg:
                    o["harita_yol_ucte_bir"].setdefault(str(r), {}).setdefault("gorunmez", 0)
                    o["harita_yol_ucte_bir"][str(r)]["gorunmez"] += 1
                    continue
                o["gorunur"] += 1
                e = cogunluk([ucte_bir_dunya(x, s["x"], fw) for x, _ in seg])[0]
                o["esit"] += (e == r)
                o["harita_yol_ucte_bir"].setdefault(str(r), {}).setdefault(str(e), 0)
                o["harita_yol_ucte_bir"][str(r)][str(e)] += 1
    return out


sonuc = {"sabitler": {"hfov_sim_derece": round(math.degrees(HFOV_SIM), 2),
                      "hfov_gercek_TAHMIN_derece": round(math.degrees(HFOV_GERCEK), 2),
                      "iz_74_5_m": round(fw74, 2), "iz_55_m": round(fw55, 2), "bant_orani": HEDEF_BANT_ORANI,
                      "KORIDOR": arena.KORIDOR, "HTAB": arena.HTAB},
         "etiket_k3": E_k3, "etiket_uretim": E_ur, "etiket_ham": E_ham,
         "kare_esleme_k3": kare_esleme, "kare_esleme_uretim": kare_esleme_ur,
         "ankor_k3": A_k3, "ankor_uretim": A_ur,
         "ankor_ozet_uretim_tum_OR": {k: ozet([a[k] for a in A_ur]) for k in (
             "ankor_m", "dx_m", "dy_m", "yol_ayrismasi_dx_m", "baslangic_alt_kenardan_m",
             "kb_alt_kenarin_altinda_m", "baslangic_yol_merkezine_m", "model74_ankor_m", "model55_ankor_m")},
         "ankor_ozet_uretim_son_OR": {k: ozet([a[k] for a in A_ur_son]) for k in (
             "ankor_m", "dx_m", "dy_m", "model74_ankor_m", "model55_ankor_m")},
         "ankor_ozet_k3": {k: ozet([a[k] for a in A_k3]) for k in (
             "ankor_m", "dx_m", "dy_m", "model74_ankor_m", "model55_ankor_m")},
         "model74_mutlak_hata_m": ozet([abs(a["model74_ankor_m"] - a["ankor_m"]) for a in A_ur
                                         if a["model74_ankor_m"] is not None]),
         "kb_hb": kbhb, "k3_hukum_karsi_olgu": k3_hukum, "surus_geometri": surus,
         "hfov_k3": hf, "hfov_genel_esleme": {"74_5": genel_esleme(fw74), "55_TAHMIN": genel_esleme(fw55)},
         "hfov_bacak_esleme": {"74_5": kare_xc_esleme(fw74), "55_TAHMIN": kare_xc_esleme(fw55)}}
with open(os.path.join(OUT, "analiz_c_sonuc.json"), "w", encoding="utf-8") as f:
    json.dump(sonuc, f, ensure_ascii=False, indent=1)
print("yazildi", os.path.join(OUT, "analiz_c_sonuc.json"))
