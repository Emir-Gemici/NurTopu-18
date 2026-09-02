"""T95-C · `rota_bul` ACIKLIK KORUMASI — GURULTU ALTINDA KARARLILIK (FAZ 1).

⚠ D-402 (2026-09-03) — taban kolu hala calisir (satir 100 `dt_px` pop) ama
cagri imzasi ANKORSUZ ve sayilar v30 donemi (D-399: ankor yanlis seritlerin
%91,7'sini eler). Buradaki kararlilik sayilari URETIM IMZASINA AIT DEGILDIR;
guncel imza: scripts/olcum/173_t99_uretim_imzasi.py

NEDEN UCUNCU TUR (on kayit: `scripts/olcum/t95c_on_kayit.md`; dayanak D-156 ·
D-159 · D-162 · D-163). T95-B'de olculebilir her sey tuttu, ama bu kuralin
SABIT ESIKLI bicimi (V1) daha once TAM BU EKSENDE olduruldu:

    D-156: V1 K5'i cozdu ama kararliligi 8 -> 11/260 BOZDU -> RED.

W1 bicimi KATMAN A'da kararliligi korudu (8/260, D-158) — ama `rota_bul`
FARKLI parametrelerle kosar ve BU YOLDA hicbir gurultu olcumu YOKTUR:

    rpi_inference:  aci_esigi_derece = 0,0   · gecilebilir = koridor > 0
    rota_bul     :  aci_esigi_derece = 15,0  · gecilebilir = dt_px >= r_gerekli

D-158 bulgu 1 asama 2'nin (aci esigi) korumayi SILEBILDIGINI zaten gostermisti.

────────────────────────────────────────────────────────────────────────────
GURULTU RECETESI — 68_karar_kararliligi.py / 75_koridor_envanteri.py ile
BIREBIR, DEGISTIRILMEZ (sayilar D-142/D-145 ile kiyaslanabilsin diye):

    sigma = 2.0/255 · tekrar = 3 · tohum = 7
    RNG akisi: TEMIZ kosu cekilis YAPMAZ, ardindan kare basina 3 cekilis.

OLCUM SOZLESMESI (D-139 dersi):
  · Kare + cekilis basina model YALNIZ BIR KEZ kosar. Cikan AYNI `mk` HEM
    taban HEM koruma `rota_bul` cagrisina verilir. Iki ayri cikarim YASAK.
  · Taban ve koruma AYNI kosumda; uretim kodu DEGISMEZ, maymun-yamayla
    sarmalanir (90_t95b_butce.py iskeleti).
  · Aciklik probu KAPALI — bu tur SURE olcmez; kayip sayilari D-159'dan gelir.

KARARSIZLIK OLCUSU: bir karenin 4 kosumunda (1 temiz + 3 cekilis)
`(durum, yol_no)` demeti AYNI degilse o kare CEVIRMIS sayilir.

POZITIF KONTROLLER (D-15/K-04 — 90'dakilerin aynisi):
  1. TABAN modunda `dt_px` yol_duzelt'e HIC gecirilmemeli (sizinti 0).
  2. KORUMA modunda enjeksiyon sayisi cagri sayisina ESIT olmali.
  3. `mk` maskeleri iki kosum arasinda BOZULMAMALI.
  4. RNG cekilis sayisi = kare sayisi x tekrar (akis 68/75 ile ayni).
────────────────────────────────────────────────────────────────────────────
"""
import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

import costmap_path_finder as C                                      # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,      # noqa: E402
                           _preprocess, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# Surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
MODEL = uretim_pt()
CONF = 0.30

_GERCEK_SERBEST = C.serbest_alan
_GERCEK_DUZELT = C.yol_duzelt

DURUM = {
    "dt_px": None,
    "koru": False,
    "cagri": 0,
    "enjekte": 0,
    "taban_sizintisi": 0,
    "uretim_dt_px": 0,     # URETIMIN KENDI gecirdigi dt_px cagrisi (T95 sonrasi)
    "dugum": None,
}


# ── maymun-yamalar (uretim kodu DEGISMEZ) ───────────────────────────────────
def _serbest(maskeler, **kw):
    s = _GERCEK_SERBEST(maskeler, **kw)
    DURUM["dt_px"] = s["dt_px"]
    return s


def _duzelt(yol_px, gecilebilir_tam, **kw):
    """KORUMA modunda `dt_px` enjekte eder. Aciklik PROBU YOKTUR (bu tur sure
    olcmez); yalniz dugum sayisi kaydedilir."""
    # 🔴 T95 UYGULANDIKTAN SONRA URETIM `dt_px`i KENDISI gecirir. O halde
    # TABAN kolu artik "hicbir sey eklememek" ile kurulamaz — eklenmis olani
    # CIKARMAK gerekir; yoksa taban ile koruma AYNI SEY olur ve olcum
    # sessizce ANLAMSIZLASIR. Sayac hangi durumda oldugumuzu da raporlar.
    if "dt_px" in kw and kw["dt_px"] is not None:
        DURUM["uretim_dt_px"] += 1
    if DURUM["koru"]:
        if DURUM["dt_px"] is None:
            raise RuntimeError("KORUMA modunda dt_px yakalanamadi — olcum gecersiz")
        kw["dt_px"] = DURUM["dt_px"]
        DURUM["enjekte"] += 1
    else:
        kw.pop("dt_px", None)
        if "dt_px" in kw:                      # olamaz — kontrol olarak durur
            DURUM["taban_sizintisi"] += 1
    DURUM["cagri"] += 1
    sonuc = _GERCEK_DUZELT(yol_px, gecilebilir_tam, **kw)
    DURUM["dugum"] = (len(list(yol_px)), len(list(sonuc)))
    return sonuc


def ac():
    C.serbest_alan = _serbest
    C.yol_duzelt = _duzelt


def kapat():
    C.serbest_alan = _GERCEK_SERBEST
    C.yol_duzelt = _GERCEK_DUZELT


def cikarim(model, img):
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    return mk, icerik


def _kosum(mk, icerik, mpp, koru):
    DURUM["koru"] = koru
    DURUM["dt_px"] = None
    DURUM["dugum"] = None
    r = C.rota_bul(mk, mpp=mpp, icerik=icerik)
    return {
        "durum": r["durum"],
        "yol_no": r["yol_no"],
        "guven": r["guven"],
        "wp": len(r.get("waypoints_px") or []),
        "dugum": DURUM["dugum"],
    }


def _anahtar(k):
    """Kararsizlik olcusu: (durum, yol_no)."""
    return (k["durum"], k["yol_no"])


def _ozet(kayitlar, mod):
    temiz_dagilim = {}
    ceviren, acik_temiz = [], 0
    dogr_bas_kare, dogr_bas_toplam, dogr_bas_temiz = [], 0, 0
    gecisler = {}
    for kayit in kayitlar:
        ks = kayit[mod]
        temiz = ks[0]
        temiz_dagilim[temiz["durum"]] = temiz_dagilim.get(temiz["durum"], 0) + 1
        if temiz["durum"] == "ACIK":
            acik_temiz += 1
        if temiz["durum"] == "DOGRULAMA_BASARISIZ":
            dogr_bas_temiz += 1
        n_db = sum(1 for k in ks if k["durum"] == "DOGRULAMA_BASARISIZ")
        dogr_bas_toplam += n_db
        if n_db:
            dogr_bas_kare.append(kayit["kare"])
        if len({_anahtar(k) for k in ks}) > 1:
            ceviren.append(kayit["kare"])
            for k in ks[1:]:
                if _anahtar(k) != _anahtar(temiz):
                    g = f"{temiz['durum']}/{temiz['yol_no']} -> {k['durum']}/{k['yol_no']}"
                    gecisler[g] = gecisler.get(g, 0) + 1
    return {
        "ceviren": len(ceviren), "ceviren_kareler": ceviren,
        "acik_temiz": acik_temiz, "temiz_durum_dagilimi": temiz_dagilim,
        "dogrulama_basarisiz_kare": len(dogr_bas_kare),
        "dogrulama_basarisiz_kareler": dogr_bas_kare,
        "dogrulama_basarisiz_kosum": dogr_bas_toplam,
        "dogrulama_basarisiz_temiz": dogr_bas_temiz,
        "gecisler": gecisler,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sigma", type=float, default=2.0)
    ap.add_argument("--tekrar", type=int, default=3)
    ap.add_argument("--tohum", type=int, default=7)
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    rng = np.random.default_rng(args.tohum)

    kayitlar, maske_bozuldu = [], []
    sayac = {"taban": {"cagri": 0, "enjekte": 0},
             "koruma": {"cagri": 0, "enjekte": 0}}
    n = cekilis = 0
    t0 = time.perf_counter()
    ac()
    try:
        for ornek in man["ornekler"]:
            if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
                continue
            p = args.kume / ornek["cikti"]
            mpp = ornek["arena"].get("mpp")
            if not p.is_file() or not mpp:
                continue
            img = cv2.imread(str(p))
            if img is None:
                continue
            if args.sinir and n >= args.sinir:
                break
            n += 1

            tabanlar, korumalar = [], []
            for i in range(args.tekrar + 1):
                if i == 0:
                    girdi = img          # TEMIZ kosu cekilis YAPMAZ (68/75)
                else:
                    g = rng.normal(0.0, args.sigma, img.shape).astype(np.float32)
                    girdi = np.clip(img.astype(np.float32) + g,
                                    0, 255).astype(np.uint8)
                    cekilis += 1

                mk, icerik = cikarim(model, girdi)
                imza_once = (int(mk[0].sum()), int(mk[1].sum()))

                DURUM["cagri"] = DURUM["enjekte"] = 0
                tabanlar.append(_kosum(mk, icerik, mpp, koru=False))
                sayac["taban"]["cagri"] += DURUM["cagri"]
                sayac["taban"]["enjekte"] += DURUM["enjekte"]

                DURUM["cagri"] = DURUM["enjekte"] = 0
                korumalar.append(_kosum(mk, icerik, mpp, koru=True))
                sayac["koruma"]["cagri"] += DURUM["cagri"]
                sayac["koruma"]["enjekte"] += DURUM["enjekte"]

                if (int(mk[0].sum()), int(mk[1].sum())) != imza_once:
                    maske_bozuldu.append(f"{p.name}#{i}")

            kayitlar.append({"kare": p.name, "taban": tabanlar,
                             "koruma": korumalar})
            if n % 20 == 0:
                print(f"  ... {n} kare  ({time.perf_counter() - t0:.0f} s)",
                      flush=True)
    finally:
        kapat()

    t = _ozet(kayitlar, "taban")
    k = _ozet(kayitlar, "koruma")
    yalniz_koruma = [x for x in k["ceviren_kareler"] if x not in t["ceviren_kareler"]]
    yalniz_taban = [x for x in t["ceviren_kareler"] if x not in k["ceviren_kareler"]]

    c = "=" * 78
    print(f"\n{c}\nT95-C · rota_bul ACIKLIK KORUMASI — GURULTU ALTINDA KARARLILIK")
    print(f"  model {args.model.name} · kume {args.kume.name} · n={n}")
    print(f"  gurultu Gauss sigma={args.sigma}/255 · kare basina {args.tekrar} "
          f"cekilis · tohum {args.tohum}\n{c}")
    print(f"{'olcum':44s}{'TABAN':>10s}{'KORUMA':>10s}")
    for ad, key in [
            ("(durum, yol_no) CEVIREN kare", "ceviren"),
            ("temiz kosuda durum == ACIK", "acik_temiz"),
            ("DOGRULAMA_BASARISIZ kare (4 kosumun biri)",
             "dogrulama_basarisiz_kare"),
            ("  ayni, temiz kosuda", "dogrulama_basarisiz_temiz"),
            ("  ayni, TOPLAM kosum (1040 icinde)", "dogrulama_basarisiz_kosum"),
    ]:
        print(f"{ad:44s}{str(t[key]):>10s}{str(k[key]):>10s}")

    print("\n  temiz kosuda durum dagilimi")
    for mod, o in (("TABAN ", t), ("KORUMA", k)):
        print(f"    {mod}: " + " · ".join(
            f"{a}={b}" for a, b in sorted(o["temiz_durum_dagilimi"].items(),
                                          key=lambda x: -x[1])))

    print(f"\n{c}\nCEVIREN KARELER\n{c}")
    print(f"  TABAN  ({t['ceviren']}): {', '.join(t['ceviren_kareler']) or '(yok)'}")
    print(f"  KORUMA ({k['ceviren']}): {', '.join(k['ceviren_kareler']) or '(yok)'}")
    print(f"  yalniz KORUMADA ceviren ({len(yalniz_koruma)}): "
          f"{', '.join(yalniz_koruma) or '(yok)'}")
    print(f"  yalniz TABANDA  ceviren ({len(yalniz_taban)}): "
          f"{', '.join(yalniz_taban) or '(yok)'}")
    for mod, o in (("TABAN", t), ("KORUMA", k)):
        if o["gecisler"]:
            print(f"  {mod} gecisleri:")
            for g, sayi in sorted(o["gecisler"].items(), key=lambda x: -x[1]):
                print(f"      {sayi}x  {g}")

    print(f"\n{c}\nPOZITIF KONTROLLER\n{c}")
    gecerli = True
    bekleniyor = n * args.tekrar
    kontroller = [
        ("TABAN modunda dt_px sizintisi", DURUM["taban_sizintisi"], 0),
        ("TABAN yol_duzelt enjekte (0 olmali)", sayac["taban"]["enjekte"], 0),
        ("mk maskesi bozulan kosum", len(maske_bozuldu), 0),
        ("RNG cekilis sayisi (kare x tekrar)", cekilis, bekleniyor),
    ]
    for ad, olculen, beklenen in kontroller:
        ok = olculen == beklenen
        gecerli &= ok
        print(f"  {'OK ' if ok else 'HATA'}  {ad:42s}{olculen} (beklenen {beklenen})")
    ok = sayac["koruma"]["cagri"] == sayac["koruma"]["enjekte"]
    gecerli &= ok
    print(f"  {'OK ' if ok else 'HATA'}  {'KORUMA cagri == enjekte':42s}"
          f"{sayac['koruma']['cagri']}/{sayac['koruma']['enjekte']}")
    print(f"  URETIMIN KENDI gecirdigi dt_px cagrisi: {DURUM['uretim_dt_px']}"
          f" / {sayac['taban']['cagri'] + sayac['koruma']['cagri']}"
          f"   (T95 ONCESI 0 · SONRASI hepsi)")
    print(f"  -> OLCUM {'GECERLI' if gecerli else 'GECERSIZ'}")

    print(f"\n{c}\nON KAYIT OLCUTLERI (scripts/olcum/t95c_on_kayit.md)\n{c}")
    K1 = k["ceviren"] <= t["ceviren"]
    K2 = k["acik_temiz"] >= t["acik_temiz"]
    K3 = k["dogrulama_basarisiz_kare"] <= t["dogrulama_basarisiz_kare"]
    for ad, tamam, deger in [
            ("(K1) ceviren kare <= taban", K1,
             f"{k['ceviren']} <= {t['ceviren']}"),
            ("(K2) temiz ACIK >= taban", K2,
             f"{k['acik_temiz']} >= {t['acik_temiz']}"),
            ("(K3) DOGRULAMA_BASARISIZ kare <= taban", K3,
             f"{k['dogrulama_basarisiz_kare']} <= "
             f"{t['dogrulama_basarisiz_kare']}")]:
        print(f"  {'TUTTU ' if tamam else 'DUSTU '} {ad:40s} {deger}")
    print("  (6) test_rota_sentetik.py ve (7) unittest AYRI kosulur.")
    print(f"\n  HEPSI TUTTU MU: {'EVET' if (K1 and K2 and K3 and gecerli) else 'HAYIR'}")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume), "n": n,
            "sigma": args.sigma, "tekrar": args.tekrar, "tohum": args.tohum,
            "conf": CONF, "taban": t, "koruma": k,
            "yalniz_koruma_ceviren": yalniz_koruma,
            "yalniz_taban_ceviren": yalniz_taban,
            "kontrol": {"taban_sizintisi": DURUM["taban_sizintisi"],
                        "sayac": sayac, "maske_bozuldu": maske_bozuldu,
                        "cekilis": cekilis, "cekilis_beklenen": bekleniyor,
                        "gecerli": bool(gecerli)},
            "olcutler": {"K1": bool(K1), "K2": bool(K2), "K3": bool(K3)},
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
