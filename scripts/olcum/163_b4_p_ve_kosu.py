"""B4 — `p` (kare basina gecerli rota olasiligi) ve BASARISIZ KOSU dagilimi.

ON KAYIT: `results/b4_fps/ON_KAYIT.md` (+ EK-1). Esikler G1/G2/G3 ve FOV
degerleri SONUC GORULMEDEN donduruldu; bu betik onlari OKUR, secmez.

NICIN: `FDA_PLANI_20260829.md` §B4 "0,9-2,6 FPS" diyor ama bu esigin nereden
geldigi yaziliydi degil. Turetme (ON_KAYIT §1):

    GEREKLI_FPS >= 1 / (YKS_TESPIT_TAZELIK_S * p)

Karar KARE BASINADIR (`_karari_yayinla` her karede; kareler arasi uzlasma
YOK) ve tazelik 5 s gecince hakem onay dugmesi duser -> ucus gecersiz.

🔴 OLCEK TUZAGI (ON_KAYIT EK-1): `rota_olcek_reddi(kare_mpp)` olcek yoksa
rotayi BLOKLAR. mpp verilmezse HER karede rota cikmaz ve p=0 olculur — bu
modelin kusuru degil OLCUM ARTEFAKTIDIR.

⚡ Cikarim kare basina BIR KEZ kosulur: maskeler mpp'den BAGIMSIZDIR, yalniz
`analyze_path` mpp'ye baglidir. Boylece FOV duyarliligi ayni maskeler uzerinde
olculur (hem 3 kat hizli hem DAHA DOGRU kiyas).
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import cv2

from ayarlar import REPO, uretim_pt

sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import (OLCEK_KAYNAK_TELEMETRI,  # noqa: E402
                              SARTNAME_ASGARI_IRTIFA_M,
                              YKS_TESPIT_TAZELIK_S, mpp_irtifadan,
                              rota_olcek_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

CONF = 0.30

# ── ON KAYIT EK-1 §E1.4'te DONDURULDU — sonuca bakilarak secilmez ──────────
FOV_ESAS = 67.3
FOV_DUYARLILIK = (62.4, 67.3, 69.9)
DUYARLILIK_ORANI = 0.20          # p bagil %20'den fazla oynarsa OLCEK_DUYARLI

# ── ON KAYIT §4'te DONDURULDU ─────────────────────────────────────────────
G1_KOSU_MAKS_S = YKS_TESPIT_TAZELIK_S    # en uzun kosu bunun ALTINDA olmali
G2_P_ASGARI = 0.22                       # plandaki 0,9 FPS alt ucunun sarti

R_KOK = REPO / "results" / "dji_20260822"
R_KARELER = R_KOK / "kareler_1fps"
S_KOK = Path("O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66")


def _karar(masks, icerik, mpp):
    """URETIM zincirinin karar halkasi (rpi_inference.py:2088-2101 birebir)."""
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(
        masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, guven, red


def _cikarim(model, img):
    """URETIM on-isleme + cikarim (61_rota_moloza_basma.py:94-96 birebir)."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    return _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik), icerik


def _kosular(bayraklar):
    """Ardisik BASARISIZ kare kosularinin uzunluklari."""
    ck, n = [], 0
    for b in bayraklar:
        if b:
            if n:
                ck.append(n)
            n = 0
        else:
            n += 1
    if n:
        ck.append(n)
    return ck


def _ozet(kosular):
    if not kosular:
        return {"kosu_sayisi": 0, "maks": 0, "p50": 0, "p95": 0}
    s = sorted(kosular)
    return {"kosu_sayisi": len(s), "maks": max(s),
            "p50": statistics.median(s),
            "p95": s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]}


def olc_R(model, sinir=None):
    """GERCEK DJI — zaman ekseni VAR (1 fps => 1 kare = 1 s), olcek rel_alt'tan."""
    irt = json.loads((R_KOK / "kareler_irtifa.json").read_text(encoding="utf-8"))
    ucuslar = {}
    for k in irt:
        ucuslar.setdefault(k["kaynak"], []).append(k)
    for v in ucuslar.values():
        v.sort(key=lambda x: x["zaman_sn"])       # ZAMAN SIRASI sart

    cikti = {"kume": "R", "n": 0, "fov": {}, "ucuslar": {}, "kareler": []}
    say = 0
    for ucus, kayitlar in sorted(ucuslar.items()):
        if sinir and say >= sinir:
            break
        for kayit in kayitlar:
            if sinir and say >= sinir:
                break
            p = R_KARELER / kayit["dosya"]
            if not p.is_file():
                continue
            img = cv2.imread(str(p))
            if img is None:
                continue
            masks, icerik = _cikarim(model, img)
            icerik_w = icerik[2]
            satir = {"ucus": ucus, "dosya": kayit["dosya"],
                     "zaman_sn": kayit["zaman_sn"],
                     "rel_alt": kayit.get("rel_alt"), "fov": {}}
            for fov in FOV_DUYARLILIK:
                h_m = kayit.get("rel_alt")
                mpp = (mpp_irtifadan(h_m, icerik_w, yatay_fov_derece=fov)
                       if h_m else None)
                yol, guven, red = _karar(masks, icerik, mpp)
                satir["fov"][str(fov)] = {
                    "mpp": mpp, "yol": yol, "guven": float(guven),
                    "red": (red[0] if isinstance(red, tuple) else red),
                    "yayinlandi": bool(yol)}
            cikti["kareler"].append(satir)
            say += 1
    cikti["n"] = say

    for fov in FOV_DUYARLILIK:
        f = str(fov)
        # Tam kume: yalniz BAGLAM (ON_KAYIT EK-2 kural 1) — hukme katilmaz.
        bayrak = [k["fov"][f]["yayinlandi"] for k in cikti["kareler"]]
        p_tam = (sum(bayrak) / len(bayrak)) if bayrak else None

        # >=30 m KATMANI (SARTNAME_ASGARI_IRTIFA_M): hukum burada verilir.
        # 🔴 KOSU, BITISIK segment ICINDE olculur (EK-2 kural 2): iki
        # segmentin/ucusun ucu birlestirilirse olmayan bir kosu uydurulur.
        per_ucus = {}
        kat_bayrak, kat_kosular = [], []
        for ucus in sorted({k["ucus"] for k in cikti["kareler"]}):
            sira = [k for k in cikti["kareler"] if k["ucus"] == ucus]
            segmentler, cur = [], []
            for k in sira:
                if (k["rel_alt"] or 0.0) >= SARTNAME_ASGARI_IRTIFA_M:
                    cur.append(k["fov"][f]["yayinlandi"])
                elif cur:
                    segmentler.append(cur)
                    cur = []
            if cur:
                segmentler.append(cur)
            b_kat = [x for seg in segmentler for x in seg]
            kosu = [u for seg in segmentler for u in _kosular(seg)]
            b_tam = [k["fov"][f]["yayinlandi"] for k in sira]
            per_ucus[ucus] = {
                "n_tam": len(b_tam),
                "p_tam": (sum(b_tam) / len(b_tam)) if b_tam else None,
                "n_katman": len(b_kat),
                "p_katman": (sum(b_kat) / len(b_kat)) if b_kat else None,
                "segment_sayisi": len(segmentler),
                "segment_uzunluklari": [len(s) for s in segmentler],
                "kosu_katman": _ozet(kosu)}
            kat_bayrak += b_kat
            kat_kosular += kosu
        cikti["fov"][f] = {
            "p_tam": p_tam,
            "p_katman": (sum(kat_bayrak) / len(kat_bayrak))
                        if kat_bayrak else None,
            "n_katman": len(kat_bayrak),
            "ucus": per_ucus,
            "kosu_maks_s": max(kat_kosular) if kat_kosular else 0,
            "kosu_katman": _ozet(kat_kosular)}
    return cikti


def olc_S(model, sinir=None):
    """SENTETIK ARENA — olcek manifestte; ZAMAN EKSENI YOK (kosu OLCULEMEZ)."""
    man = json.loads((S_KOK / "manifest.json").read_text(encoding="utf-8"))
    cikti = {"kume": "S", "n": 0, "kareler": [],
             "kosu": "OLCULEMEDI (zaman ekseni yok — ON_KAYIT EK-1 §E1.2)"}
    for ornek in man["ornekler"]:
        if sinir and cikti["n"] >= sinir:
            break
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = S_KOK / ornek["cikti"]
        if not p.is_file():
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        masks, icerik = _cikarim(model, img)
        mpp = ornek["arena"].get("mpp")
        yol, guven, red = _karar(masks, icerik, mpp)
        cikti["kareler"].append({
            "kare": p.name, "mpp": mpp, "yol": yol, "guven": float(guven),
            "red": (red[0] if isinstance(red, tuple) else red),
            "yayinlandi": bool(yol),
            "acik_serit": ornek["arena"].get("acik_serit")})
        cikti["n"] += 1
    b = [k["yayinlandi"] for k in cikti["kareler"]]
    cikti["p"] = (sum(b) / len(b)) if b else None
    return cikti


def hukum(r, s):
    """ON KAYIT §4 + EK-2 esikleri — BURADA SECILMEZ, OKUNUR.

    G1 ve G2_R >=30 m KATMANINDA verilir (EK-2 kural 1); tam kume baglamdir.
    """
    h = {}
    ps = [r["fov"][str(f)]["p_katman"] for f in FOV_DUYARLILIK
          if r["fov"][str(f)]["p_katman"] is not None]
    if ps and max(ps) > 0:
        oyn = (max(ps) - min(ps)) / max(ps)
        h["olcek_duyarliligi"] = {
            "p_min": min(ps), "p_maks": max(ps), "bagil_oynama": oyn,
            "damga": "OLCEK_DUYARLI" if oyn > DUYARLILIK_ORANI else "KARARLI"}
    else:
        h["olcek_duyarliligi"] = {"damga": "OLCULEMEDI"}

    esas = r["fov"][str(FOV_ESAS)]
    kosu = esas["kosu_maks_s"]
    olculdu = esas.get("n_katman", 0) > 0
    h["G1"] = {"olculen_en_uzun_kosu_s": kosu, "esik_s": G1_KOSU_MAKS_S,
               "durum": ("OLCULEMEDI" if not olculdu
                         else "GECTI" if kosu < G1_KOSU_MAKS_S else "DUSTU")}
    pr = esas["p_katman"]
    h["G2_R"] = {"p": pr, "p_tam_baglam": esas["p_tam"], "esik": G2_P_ASGARI,
                 "durum": ("OLCULEMEDI" if pr is None
                           else "GECTI" if pr >= G2_P_ASGARI else "DUSTU")}
    h["G2_S"] = {"p": s["p"], "esik": G2_P_ASGARI,
                 "durum": ("OLCULEMEDI" if s["p"] is None
                           else "GECTI" if s["p"] >= G2_P_ASGARI else "DUSTU")}
    for ad, pd in (("R", pr), ("S", s["p"])):
        h[f"gerekli_fps_{ad}"] = (
            None if not pd else 1.0 / (YKS_TESPIT_TAZELIK_S * pd))
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinir", type=int, default=None,
                    help="her kumeden en fazla N kare (yoklama icin)")
    ap.add_argument("--json", default=None)
    ap.add_argument("--kume", choices=("R", "S", "ikisi"), default="ikisi")
    a = ap.parse_args()

    from ultralytics import YOLO
    mp = uretim_pt()
    print(f"MODEL: {mp}")
    model = YOLO(str(mp), task="segment")

    t0 = time.time()
    r = olc_R(model, a.sinir) if a.kume in ("R", "ikisi") else {
        "kume": "R", "n": 0, "fov": {}, "kareler": []}
    t1 = time.time()
    s = olc_S(model, a.sinir) if a.kume in ("S", "ikisi") else {
        "kume": "S", "n": 0, "p": None, "kareler": []}
    t2 = time.time()

    def _f(x):
        return "-" if x is None else f"{x:.4f}"

    print(f"\nR: n={r['n']}  ({t1 - t0:.1f} sn)")
    for f in FOV_DUYARLILIK:
        d = r["fov"].get(str(f))
        if d:
            print(f"   FOV {f}: p_katman={_f(d['p_katman'])} "
                  f"(n={d['n_katman']}) · p_tam={_f(d['p_tam'])} · "
                  f"en uzun kosu={d['kosu_maks_s']} s")
    print(f"S: n={s['n']}  ({t2 - t1:.1f} sn)  p={_f(s['p'])}")

    if r["n"] and s["n"] is not None and r["fov"]:
        hk = hukum(r, s)
        print("\nHUKUM (ON_KAYIT §4 esikleri):")
        print(json.dumps(hk, ensure_ascii=False, indent=1))
    else:
        hk = {"durum": "OLCULEMEDI"}

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"_on_kayit": "results/b4_fps/ON_KAYIT.md",
             "_model": str(mp), "_conf": CONF, "_infer_size": INFER_SIZE,
             "_fov_dondurulan": list(FOV_DUYARLILIK),
             "R": r, "S": s, "hukum": hk},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\nJSON: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
