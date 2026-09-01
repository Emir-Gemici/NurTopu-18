"""D-374 kaldirac 1 — INFER_SIZE 512 vs 640 (KOR ARALIGI cozunurluk kapatir mi?).

ON KAYIT: `results/b4_fps/ON_KAYIT_INFER_SIZE.md` — I1/I2/I3/I4 esikleri sonuc
gorulmeden donduruldu. Bu bir OLCUMDUR, karar degil: 640'a gecmek kayit
defterini ve kabul zincirini degistirir -> MIMAR KARARI.

🔴 D-375 DERSI BASTAN UYGULANDI: iki AYRI model ornegi + her kolun gercek
`imgsz`'i kod icinde dogrulanir. Tek nesneye iki farkli predict argumani
verilirse ultralytics predictor'i ILK cagrida kurar ve ikincisini SESSIZCE
yok sayabilir; oyle bir kosum FARKSIZLIK uretir ve "denk" sanilir.

Kume K (kor kareler) R'nin ALT KUMESIDIR: R bir kez kosulur, K ondan turetilir
(ayni maskeler — hem hizli hem daha dogru kiyas).
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
                              SARTNAME_ASGARI_IRTIFA_M, mpp_irtifadan,
                              rota_olcek_reddi)
from rpi_inference import (_maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, _rota_kararini_esikle, analyze_path,
                           get_masks)

CONF = 0.30
FOV_ESAS = 67.3              # EK-1'de donduruldu
TABAN, ADAY = 512, 640       # ON_KAYIT_INFER_SIZE §2
I2_GERILEME_TAVANI = 0.02    # §3-I2
# ⚠ Tam sinirda kayan nokta gurultusu kapiyi belirlemesin: 0,98-1,0 =
# -0,020000000000000018 cikar ve ON KAYIT'in "≥ -0,02" metnine ragmen DUSER.
# Esik bir HUKUMDUR; 1e-17'lik gosterim artigi onu cevirmemeli.
I2_EPSILON = 1e-9
I3_KOSU_ESIGI_S = 5.0        # sozlesme: YKS_TESPIT_TAZELIK_S
I4_GEREKLI_FPS = 0.41        # D-374 R katmani
I4_BAND_ALT = 0.9            # plan bandinin alt ucu

R_KOK = REPO / "results" / "dji_20260822"
S_KOK = Path("O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66")
KOR = REPO / "results" / "b4_fps" / "kor_kareler.json"


def _imgsz_dogrula(model, beklenen, ad):
    """🔴 OLCEN ARACIN KENDISI OLCULUR (D-375). Tutmazsa OLCULEMEDI + exit 1."""
    try:
        g = model.predictor.args.imgsz
    except Exception as e:
        print(f"OLCULEMEDI: {ad} kolunun imgsz'i okunamadi ({type(e).__name__})")
        raise SystemExit(1)
    g = g[0] if isinstance(g, (list, tuple)) else g
    if int(g) != int(beklenen):
        print(f"OLCULEMEDI: {ad} kolu imgsz={g} kosuyor (beklenen {beklenen}) "
              f"— arguman yok sayildi; olcum FARKSIZLIK uretirdi (D-375)")
        raise SystemExit(1)


def _karar(masks, icerik, mpp):
    """163/164 ile AYNI uretim karar halkasi."""
    olcek_reddi = rota_olcek_reddi(mpp)
    yol, guven, wps, red = analyze_path(
        masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=mpp,
        return_reason=True, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI)
    if olcek_reddi is not None and red is None:
        yol, guven, wps = None, 0.0, []
        red = olcek_reddi
    yol, guven, wps, red = _rota_kararini_esikle(yol, guven, wps, red)
    return yol, (red[0] if isinstance(red, tuple) else red)


def _iki_kol(m512, m640, img, mpp):
    """Ayni kare, iki cozunurluk. On-isleme ve tuval PAYLASILIR."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    cikti = {}
    ham_sekil = {}
    for ad, model, boy in (("512", m512, TABAN), ("640", m640, ADAY)):
        t0 = time.perf_counter()
        son = model.predict(small, imgsz=boy, conf=CONF, verbose=False,
                            device=0)
        ms = (time.perf_counter() - t0) * 1000.0
        _imgsz_dogrula(model, boy, ad)
        r0 = son[0]
        ham_sekil[ad] = (list(r0.masks.data.shape[-2:])
                         if r0.masks is not None else None)
        mk = _maskeleri_icerige_kirp(get_masks(son, h, w), icerik)
        yol, red = _karar(mk, icerik, mpp)
        cikti[ad] = {"yol": yol, "red": red, "cikarim_ms": ms}
    cikti["_ham_maske_sekli"] = ham_sekil
    return cikti


def _kosular(bayraklar):
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


def olc_R(m512, m640, sinir=None):
    irt = json.loads((R_KOK / "kareler_irtifa.json").read_text(encoding="utf-8"))
    kayitlar = []
    for k in sorted(irt, key=lambda x: (x["kaynak"], x["zaman_sn"])):
        if sinir and len(kayitlar) >= sinir:
            break
        if (k.get("rel_alt") or 0.0) < SARTNAME_ASGARI_IRTIFA_M:
            continue
        p = R_KOK / "kareler_1fps" / k["dosya"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        mpp = mpp_irtifadan(k["rel_alt"], img.shape[1],
                            yatay_fov_derece=FOV_ESAS)
        d = _iki_kol(m512, m640, img, mpp)
        d.update({"dosya": k["dosya"], "ucus": k["kaynak"],
                  "zaman_sn": k["zaman_sn"], "rel_alt": k["rel_alt"]})
        kayitlar.append(d)
    return kayitlar


def olc_S(m512, m640, sinir=None):
    man = json.loads((S_KOK / "manifest.json").read_text(encoding="utf-8"))
    kayitlar = []
    for o in man["ornekler"]:
        if sinir and len(kayitlar) >= sinir:
            break
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = S_KOK / o["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        d = _iki_kol(m512, m640, img, o["arena"].get("mpp"))
        d.update({"kare": p.name, "acik_serit": o["arena"].get("acik_serit")})
        kayitlar.append(d)
    return kayitlar


def hukum(r, s, kor_adlari):
    h = {}
    if not r or not s:
        return {"durum": "OLCULEMEDI", "sebep": "kume bos"}

    # I1 — AYIRT EDICI TANI: kor karelerde 640 ne yapiyor (512'de hepsi 0).
    kor = [k for k in r if k["dosya"] in kor_adlari]
    p_k = (sum(1 for k in kor if k["640"]["yol"]) / len(kor)) if kor else None
    h["I1_tani"] = {
        "n_kor": len(kor), "p_512": 0.0, "p_640": p_k,
        "hukum": ("OLCULEMEDI" if p_k is None
                  else "COZUNURLUK_KALDIRAC_DEGIL" if p_k == 0
                  else "KISMEN_CALISIYOR"),
        "_kapsam": "512'nin dustugu SECILMIS alt kume; genel p yerine gecmez"}

    # I2 — GERILEME YASAGI (S): p dusmemeli + dogru->yanlis sayilir.
    p512 = sum(1 for k in s if k["512"]["yol"]) / len(s)
    p640 = sum(1 for k in s if k["640"]["yol"]) / len(s)
    zarar = [k["kare"] for k in s
             if k["512"]["yol"] == k["acik_serit"]
             and k["640"]["yol"] is not None
             and k["640"]["yol"] != k["acik_serit"]]
    h["I2_gerileme"] = {
        "p_S_512": p512, "p_S_640": p640, "fark": p640 - p512,
        "tavan": -I2_GERILEME_TAVANI, "dogru_yanlisa_donen": len(zarar),
        "kareler": zarar[:20],
        "durum": ("GECTI" if (p640 - p512) >= -I2_GERILEME_TAVANI - I2_EPSILON
                  else "DUSTU")}

    # I3 — ASIL KAPI: R katmaninda en uzun kosu (BITISIK segment icinde).
    kosu = {}
    for ad in ("512", "640"):
        hepsi = []
        for u in sorted({k["ucus"] for k in r}):
            sira = [k for k in r if k["ucus"] == u]
            hepsi += _kosular([bool(k[ad]["yol"]) for k in sira])
        kosu[ad] = {"maks": max(hepsi) if hepsi else 0,
                    "p50": statistics.median(hepsi) if hepsi else 0,
                    "kosu_sayisi": len(hepsi)}
    p_r = {ad: sum(1 for k in r if k[ad]["yol"]) / len(r) for ad in ("512", "640")}
    h["I3_kapi"] = {
        "p_R_512": p_r["512"], "p_R_640": p_r["640"],
        "kosu_512": kosu["512"], "kosu_640": kosu["640"],
        "esik_s": I3_KOSU_ESIGI_S,
        "durum": "GECTI" if kosu["640"]["maks"] < I3_KOSU_ESIGI_S else "DUSTU"}

    # I4 — FPS BUTCESI (gosterge; Jetson'da ayni olacagi VARSAYILMAZ).
    t = {ad: statistics.median([k[ad]["cikarim_ms"] for k in r])
         for ad in ("512", "640")}
    c = t["640"] / t["512"] if t["512"] else None
    etkin = (I4_BAND_ALT / c) if c else None
    h["I4_fps"] = {
        "cikarim_ms_p50_512": t["512"], "cikarim_ms_p50_640": t["640"],
        "maliyet_orani": c, "band_alt_640_etkin": etkin,
        "gerekli": I4_GEREKLI_FPS,
        "durum": ("OLCULEMEDI" if etkin is None
                  else "GECTI" if etkin >= I4_GEREKLI_FPS
                  else "FPS_BUTCESI_YETMEZ"),
        "_not": "PC oraninin Jetson'da ayni olacagi varsayilmaz — gosterge."}
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sinir", type=int, default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    from ultralytics import YOLO
    mp = uretim_pt()
    print(f"MODEL: {mp} · TABAN {TABAN} · ADAY {ADAY}")
    # 🔴 IKI AYRI ORNEK (D-375).
    m512 = YOLO(str(mp), task="segment")
    m640 = YOLO(str(mp), task="segment")

    kor_adlari = {k["dosya"] for k in
                  json.loads(KOR.read_text(encoding="utf-8"))}
    print(f"KOR kume: {len(kor_adlari)} kare")

    t0 = time.time()
    r = olc_R(m512, m640, a.sinir)
    t1 = time.time()
    s = olc_S(m512, m640, a.sinir)
    t2 = time.time()
    print(f"R: n={len(r)} ({t1 - t0:.0f} sn) · S: n={len(s)} ({t2 - t1:.0f} sn)")

    h = hukum(r, s, kor_adlari)
    print(json.dumps(h, ensure_ascii=False, indent=1))

    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"_on_kayit": "results/b4_fps/ON_KAYIT_INFER_SIZE.md",
             "_model": str(mp), "_taban": TABAN, "_aday": ADAY,
             "_conf": CONF, "_fov": FOV_ESAS, "hukum": h, "R": r, "S": s},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"JSON: {a.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
