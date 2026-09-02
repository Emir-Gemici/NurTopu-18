"""T95 · `rota_bul` (KATMAN B) ACIKLIK KORUMASI — KAYIP OLCUMU (FAZ 1).

⛔ D-402 (2026-09-03) — BU BETIK BUGUN GECERSIZ OLCUM URETIR: uretim artik
`yol_duzelt`e `dt_px` geciriyor (T95/D-164; costmap_path_finder.py:1259),
asagidaki taban kolu sizinti sayacini tetikler ve rapor "OLCUM GECERSIZ"
basar. Ustelik cagri imzasi ankorsuz ve sayilar v30 (D-399). TARIHSEL
KAYITTIR; guncel olcum: scripts/olcum/173_t99_uretim_imzasi.py

NEDEN (REVIEW_LOG D-158, bagimsiz denetim bulgusu 2). T94 `yol_duzelt`e
ACIKLIK KORUMA kurali ekledi:

    kiris_asgari >= (1 - kiris_bandi) * alt_yol_asgari

ve bunu YALNIZ `rpi_inference` (KATMAN A) yolunda devreye aldi. `rota_bul`
ayni fonksiyonu `dt_px` GECIRMEDEN cagiriyor (costmap_path_finder.py:1116),
oysa `sonuc["dt_px"]` bir satir once kapsamda (:1114). D-154'te olculen kusur
(string-pulling emniyet payini yiyor, medyan 4,00 px) bu yolda HALA CANLI.
Zincir: `rota_bul` -> simulation/scripts/iha_haritala.py:329 -> yayinlanan `road`.

KORLEMESINE TEK SATIR EKLENMEZ. Bu yolun `rpi_inference`tan IKI YAPISAL
FARKI var ve ikisi de kuralin davranisini degistirebilir:
  (a) `rota_bul` `yol_duzelt`i VARSAYILAN `aci_esigi_derece=15.0` ile cagirir;
      `rpi_inference` `0.0` kullanir. D-157'de asama 2 tam bu yuzden korumayi
      SILIYORDU; duzeltildi ama BU YOLDA hic olculmedi.
  (b) `rota_bul` `gecilebilir_tam` olarak C-UZAYINI (`dt_px >= r_gerekli_px`)
      verir; `rpi_inference` `koridor > 0` verir — kural C-uzayinda daha az
      serbestlik gorur.

────────────────────────────────────────────────────────────────────────────
OLCUM SOZLESMESI (D-139 dersi: uretimin yaptigi islemi atlayan olcum uretimi
olcmez).
  · Kume: calisma/sentetik_arena_kadraj_t66 (n=260), TEMIZ kare, CEKILIS YOK.
  · Model kare basina YALNIZ BIR KEZ kosar. Cikan AYNI `mk` maskeleri hem
    TABAN hem KORUMA kosumuna verilir. Iki ayri cikarim YASAK.
  · Taban ve koruma AYNI KOSUMDA olculur; mutlak sayi degil TABANLA kiyas.
  · Uretim kodu DEGISTIRILMEZ; `serbest_alan` ve `yol_duzelt` maymun-yamayla
    sarmalanir (87_t94_yumusak_kiris.py kalibi).

POZITIF KONTROLLER (D-15/K-04 — sifir olcum basari sayilmaz):
  1. TABAN modunda `dt_px` anahtari yol_duzelt'e HIC gecirilmemeli. Sizinti
     sayaci 0 degilse OLCUM GECERSIZDIR.
  2. KORUMA modunda enjeksiyon sayisi cagri sayisina ESIT olmali; degilse
     koruma bazi karelerde hic calismamis demektir.
  3. `mk` maskeleri iki kosum arasinda BOZULMAMALI (imza karsilastirmasi).
────────────────────────────────────────────────────────────────────────────

KABUL OLCUTLERI icin `scripts/olcum/t95_on_kayit.md` — mimar tarafindan, bu
olcum kosulmadan ONCE yazildi. Bu betik olcutu DEGERLENDIRIR, TANIMLAMAZ.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

import costmap_path_finder as C                                      # noqa: E402
from costmap_path_finder import (_polyline_asgari_aciklik,           # noqa: E402
                                 olcek_px, rota_bul)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,      # noqa: E402
                           _preprocess, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# Surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
MODEL = uretim_pt()
CONF = 0.30

_GERCEK_SERBEST = C.serbest_alan
_GERCEK_DUZELT = C.yol_duzelt

DURUM = {
    "dt_px": None,         # `serbest_alan`dan yakalanan TAM cozunurluk mesafesi
    "koru": False,         # KORUMA modu mu
    "olcum": None,         # son `yol_duzelt` cagrisinin kayip olcumu
    "cagri": 0,            # yol_duzelt cagri sayisi (mod basina sifirlanir)
    "enjekte": 0,          # dt_px enjekte edilen cagri sayisi
    "taban_sizintisi": 0,  # TABAN modunda dt_px gecen cagri — 0 OLMALI
    "olc_aciklik": True,   # False ise aciklik probu KAPALI (temiz zamanlama)
}


# ── maymun-yamalar (uretim kodu DEGISMEZ) ───────────────────────────────────
def _serbest(maskeler, **kw):
    """`rota_bul`un ic `serbest_alan` cagrisini yakala; `dt_px`i sakla."""
    s = _GERCEK_SERBEST(maskeler, **kw)
    DURUM["dt_px"] = s["dt_px"]
    return s


def _aciklik(noktalar, dt):
    """< 2 nokta icin aciklik TANIMSIZDIR — inf yerine None doner."""
    p = list(noktalar)
    if dt is None or len(p) < 2:
        return None
    return float(_polyline_asgari_aciklik(p, dt))


def _duzelt(yol_px, gecilebilir_tam, **kw):
    """`yol_duzelt` sarmalayicisi: KORUMA modunda `dt_px` enjekte eder, her
    iki modda GIRDI/CIKTI acikligini olcer."""
    dt = DURUM["dt_px"]
    DURUM["cagri"] += 1
    if DURUM["koru"]:
        if dt is None:
            raise RuntimeError("KORUMA modunda dt_px yakalanamadi — olcum gecersiz")
        kw["dt_px"] = dt
        DURUM["enjekte"] += 1
    elif "dt_px" in kw:
        # POZITIF KONTROL 1: taban modunda enjeksiyon OLMAMALI
        DURUM["taban_sizintisi"] += 1

    t0 = time.perf_counter()
    sonuc = _GERCEK_DUZELT(yol_px, gecilebilir_tam, **kw)
    t1 = time.perf_counter()

    # 🔴 ZAMANLAMA KIPI: aciklik probu `rota_bul`un `sure_ms["duzelt"]`
    # PENCERESININ ICINDE calisir ve o sayiyi KIRLETIR (her iki modda sabit ek
    # yuk -> ORANI SIKISTIRIR, yani (4) olcutunu OLDUGUNDAN IYI gosterir).
    # `--yalniz-sure` kipinde prob KAPATILIR; o kosumdaki `sure_ms["duzelt"]`
    # uretimin KENDI suresidir.
    a_giris = _aciklik(yol_px, dt) if DURUM["olc_aciklik"] else None
    a_cikis = _aciklik(sonuc, dt) if DURUM["olc_aciklik"] else None
    DURUM["olcum"] = {
        "a_giris": (None if a_giris is None else round(a_giris, 3)),
        "a_cikis": (None if a_cikis is None else round(a_cikis, 3)),
        "kayip": (None if (a_giris is None or a_cikis is None)
                  else round(a_giris - a_cikis, 3)),
        "dugum_giris": len(list(yol_px)),
        "dugum": len(list(sonuc)),
        "duzelt_ms_ic": round((t1 - t0) * 1000, 2),
    }
    return sonuc


def ac():
    C.serbest_alan = _serbest
    C.yol_duzelt = _duzelt


def kapat():
    C.serbest_alan = _GERCEK_SERBEST
    C.yol_duzelt = _GERCEK_DUZELT


# ── tek cikarim sozlesmesi (75_koridor_envanteri.py ile ayni) ───────────────
def cikarim(model, img):
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    return mk, icerik


def _kosum(mk, icerik, mpp, koru):
    """Tek bir `rota_bul` kosumu; kayip olcumu ile birlikte doner."""
    DURUM["koru"] = koru
    DURUM["olcum"] = None
    DURUM["dt_px"] = None
    r = rota_bul(mk, mpp=mpp, icerik=icerik)
    dt = DURUM["dt_px"]
    r_gerekli = float(olcek_px(mpp)["r_gerekli_px"])
    wp = r.get("waypoints_px") or []
    wp_aciklik = _aciklik(wp, dt)
    return {
        "durum": r["durum"],
        "yol_no": r["yol_no"],
        "wp": len(wp),
        "duzelt_ms": (r.get("sure_ms") or {}).get("duzelt"),
        "r_gerekli_px": round(r_gerekli, 3),
        "wp_aciklik_px": (None if wp_aciklik is None else round(wp_aciklik, 3)),
        "pay_px": (None if wp_aciklik is None
                   else round(wp_aciklik - r_gerekli, 3)),
        "olcum": DURUM["olcum"],
    }


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def _ozet(kayitlar, anahtar):
    """ACIK karelerde ozet. `anahtar` = 'taban' | 'koruma'."""
    acik = [k for k in kayitlar if k[anahtar]["durum"] == "ACIK"]
    duzelt_kosan = [k for k in kayitlar if k[anahtar]["olcum"] is not None]
    kayiplar = [k[anahtar]["olcum"]["kayip"] for k in acik
                if k[anahtar]["olcum"] is not None]
    paylar = [k[anahtar]["pay_px"] for k in acik]
    dugumler = [k[anahtar]["olcum"]["dugum"] for k in acik
                if k[anahtar]["olcum"] is not None]
    # ⚠ OLCUM KIRLILIGI (kendi duzenegimin): `rota_bul`un `sure_ms["duzelt"]`i
    # `yol_duzelt` CAGRISINI sarar; benim sarmalayicim `_polyline_asgari_aciklik`
    # olcumlerini o pencerenin ICINDE yapar. Bu sabit ek yuk her iki modda da
    # eklendigi icin ORANI SIKISTIRIR, yani (4) olcutunu OLDUGUNDAN IYI
    # gosterir. Bu yuzden (4) icin sarmalayicinin kendi IC olcumu
    # (`duzelt_ms_ic` — yalniz gercek cagriyi sarar) esas alinir; dis deger
    # seffaflik icin ayrica raporlanir.
    sureler = [k[anahtar]["olcum"]["duzelt_ms_ic"] for k in acik
               if k[anahtar]["olcum"] is not None]
    sureler_dis = [k[anahtar]["duzelt_ms"] for k in acik]
    dagilim = {}
    for k in kayitlar:
        d = k[anahtar]["durum"]
        dagilim[d] = dagilim.get(d, 0) + 1
    return {
        "acik": len(acik),
        "duzelt_kosan": len(duzelt_kosan),
        "kayip_medyan": med(kayiplar),
        "kayip_gt2": sum(1 for x in kayiplar if x is not None and x > 2.0),
        "kayip_n": len(kayiplar),
        "pay_lt3": sum(1 for x in paylar if x is not None and x < 3.0),
        "pay_medyan": med(paylar),
        "dugum_medyan": med(dugumler),
        "wp_medyan": med([k[anahtar]["wp"] for k in acik]),
        "duzelt_ms_medyan": med(sureler),
        "duzelt_ms_dis_medyan": med(sureler_dis),
        "durum_dagilimi": dagilim,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sinir", type=int, default=0, help="yalniz ilk N kare")
    ap.add_argument("--yalniz-sure", action="store_true",
                    help="aciklik probunu KAPAT — (4) icin KIRLENMEMIS zamanlama")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    DURUM["olc_aciklik"] = not args.yalniz_sure
    if args.yalniz_sure:
        print("[YALNIZ SURE] aciklik probu KAPALI — sure_ms['duzelt'] "
              "uretimin KENDI suresidir (kayip sayilari bu kosumda YOKTUR).")

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    kayitlar = []
    maske_bozuldu = []
    sayaclar = {"taban": {"cagri": 0, "enjekte": 0},
                "koruma": {"cagri": 0, "enjekte": 0}}
    n = 0
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

            mk, icerik = cikarim(model, img)
            imza_once = (int(mk[0].sum()), int(mk[1].sum()))

            DURUM["cagri"] = DURUM["enjekte"] = 0
            taban = _kosum(mk, icerik, mpp, koru=False)
            sayaclar["taban"]["cagri"] += DURUM["cagri"]
            sayaclar["taban"]["enjekte"] += DURUM["enjekte"]

            DURUM["cagri"] = DURUM["enjekte"] = 0
            koruma = _kosum(mk, icerik, mpp, koru=True)
            sayaclar["koruma"]["cagri"] += DURUM["cagri"]
            sayaclar["koruma"]["enjekte"] += DURUM["enjekte"]

            imza_sonra = (int(mk[0].sum()), int(mk[1].sum()))
            if imza_once != imza_sonra:
                maske_bozuldu.append(f"{p.name} {imza_once}->{imza_sonra}")

            kayitlar.append({"kare": p.name, "taban": taban, "koruma": koruma})
            if n % 20 == 0:
                print(f"  ... {n} kare", flush=True)
    finally:
        kapat()

    t = _ozet(kayitlar, "taban")
    k = _ozet(kayitlar, "koruma")

    # ESLESTIRILMIS ALT KUME — ikisinde de ACIK olan kareler
    ortak = [x for x in kayitlar
             if x["taban"]["durum"] == "ACIK" and x["koruma"]["durum"] == "ACIK"
             and x["taban"]["olcum"] and x["koruma"]["olcum"]]
    e_taban = med([x["taban"]["olcum"]["kayip"] for x in ortak])
    e_koruma = med([x["koruma"]["olcum"]["kayip"] for x in ortak])

    kaybeden = [x["kare"] for x in kayitlar
                if x["taban"]["durum"] == "ACIK" and x["koruma"]["durum"] != "ACIK"]
    kazanan = [x["kare"] for x in kayitlar
               if x["taban"]["durum"] != "ACIK" and x["koruma"]["durum"] == "ACIK"]

    c = "=" * 78
    print(f"\n{c}\nT95 · rota_bul ACIKLIK KORUMASI — TABAN vs KORUMA (ayni kosum)")
    print(f"  model {args.model.name} · kume {args.kume.name} · n={n} · "
          f"TEMIZ kare (cekilis yok)\n{c}")
    print(f"{'olcum':34s}{'TABAN':>14s}{'KORUMA':>14s}")
    satirlar = [
        ("durum == ACIK", "acik"),
        ("yol_duzelt kosan kare", "duzelt_kosan"),
        ("kayip medyani (px)", "kayip_medyan"),
        ("kayip > 2 px olan ACIK kare", "kayip_gt2"),
        ("pay < 3 px olan ACIK kare", "pay_lt3"),
        ("pay medyani (px)", "pay_medyan"),
        ("yol_duzelt cikti dugum medyani", "dugum_medyan"),
        ("waypoint medyani", "wp_medyan"),
        ("duzelt suresi medyani (ms, IC)", "duzelt_ms_medyan"),
        ("  ayni, DIS (olcum kirli)", "duzelt_ms_dis_medyan"),
    ]
    for ad, key in satirlar:
        print(f"{ad:34s}{str(t[key]):>14s}{str(k[key]):>14s}")
    print(f"\n  ESLESTIRILMIS (ikisinde de ACIK, n={len(ortak)}) kayip medyani:"
          f"  taban {e_taban} · koruma {e_koruma}")

    print("\n  durum dagilimi TABAN : " + " · ".join(
        f"{a}={b}" for a, b in sorted(t["durum_dagilimi"].items(),
                                      key=lambda x: -x[1])))
    print("  durum dagilimi KORUMA: " + " · ".join(
        f"{a}={b}" for a, b in sorted(k["durum_dagilimi"].items(),
                                      key=lambda x: -x[1])))

    print(f"\n{c}\nKARARI CEVIREN KARELER\n{c}")
    print(f"  ACIK -> baska durum (KAYIP) : {len(kaybeden)}"
          + (("  -> " + ", ".join(kaybeden)) if kaybeden else ""))
    print(f"  baska durum -> ACIK (KAZANC): {len(kazanan)}"
          + (("  -> " + ", ".join(kazanan)) if kazanan else ""))
    for x in kayitlar:
        if x["taban"]["durum"] != x["koruma"]["durum"]:
            print(f"    {x['kare']}: {x['taban']['durum']} -> {x['koruma']['durum']}"
                  f"  (yol_no {x['taban']['yol_no']} -> {x['koruma']['yol_no']})")

    print(f"\n{c}\nPOZITIF KONTROLLER\n{c}")
    gecerli = True
    print(f"  1. TABAN modunda dt_px sizintisi : {DURUM['taban_sizintisi']}"
          f"   (0 OLMALI)")
    if DURUM["taban_sizintisi"] != 0:
        gecerli = False
    print(f"  2. TABAN  yol_duzelt cagri/enjekte: "
          f"{sayaclar['taban']['cagri']}/{sayaclar['taban']['enjekte']}"
          f"   (enjekte 0 OLMALI)")
    if sayaclar["taban"]["enjekte"] != 0:
        gecerli = False
    print(f"     KORUMA yol_duzelt cagri/enjekte: "
          f"{sayaclar['koruma']['cagri']}/{sayaclar['koruma']['enjekte']}"
          f"   (ESIT OLMALI)")
    if sayaclar["koruma"]["cagri"] != sayaclar["koruma"]["enjekte"]:
        gecerli = False
    print(f"  3. mk maskesi bozulan kare       : {len(maske_bozuldu)}   (0 OLMALI)")
    if maske_bozuldu:
        gecerli = False
    print(f"  -> OLCUM {'GECERLI' if gecerli else 'GECERSIZ'}")

    # ── ON KAYIT OLCUTLERI (t95_on_kayit.md) — betik TANIMLAMAZ, DEGERLENDIRIR
    print(f"\n{c}\nON KAYIT OLCUTLERI (scripts/olcum/t95_on_kayit.md)\n{c}")
    o1 = k["acik"] >= t["acik"]
    kazanc = (None if (t["kayip_medyan"] is None or k["kayip_medyan"] is None)
              else round(t["kayip_medyan"] - k["kayip_medyan"], 3))
    o2 = kazanc is not None and kazanc >= 1.00
    o3 = k["pay_lt3"] <= t["pay_lt3"]
    o4 = (t["duzelt_ms_medyan"] is not None and k["duzelt_ms_medyan"] is not None
          and k["duzelt_ms_medyan"] <= 2.0 * t["duzelt_ms_medyan"])
    o5 = k["wp_medyan"] is not None and k["wp_medyan"] <= 16
    for ad, tamam, deger in [
            ("(1) ACIK >= taban", o1, f"{k['acik']} >= {t['acik']}"),
            ("(2) kayip medyani kazanci >= 1,00 px", o2, f"{kazanc}"),
            ("(3) pay<3 ACIK kare <= taban", o3, f"{k['pay_lt3']} <= {t['pay_lt3']}"),
            ("(4) duzelt suresi <= 2x taban", o4,
             f"{k['duzelt_ms_medyan']} <= 2 x {t['duzelt_ms_medyan']}"),
            ("(5) waypoint medyani <= 16", o5,
             f"{k['wp_medyan']}   (TABAN {t['wp_medyan']})")]:
        print(f"  {'TUTTU ' if tamam else 'DUSTU '} {ad:38s} {deger}")
    print("  (6) test_rota_sentetik.py ve (7) unittest AYRI kosulur — FAZ 2.")
    # MUTLAK esikli olcutler icin: TABAN da sagliyor mu? Saglamayan bir esik
    # DEGISIKLIGI AYIRT EDEMEZ (D-146/D-157 kusur sinifi) — karar mimarindir.
    if t["wp_medyan"] is not None and t["wp_medyan"] > 16:
        print(f"\n  [!] (5) MUTLAK bir esiktir ve TABAN da saglamiyor "
              f"(taban waypoint medyani {t['wp_medyan']} > 16). Bu olcut "
              f"degisikligi AYIRT ETMEZ; olcut GEVSETILMEDI, olgu bildirilir.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume), "n": n,
            "conf": CONF, "taban": t, "koruma": k,
            "eslestirilmis": {"n": len(ortak), "taban": e_taban,
                              "koruma": e_koruma},
            "acik_kaybeden": kaybeden, "acik_kazanan": kazanan,
            "kontrol": {"taban_sizintisi": DURUM["taban_sizintisi"],
                        "sayaclar": sayaclar,
                        "maske_bozuldu": maske_bozuldu,
                        "gecerli": gecerli},
            "olcutler": {"1_acik": o1, "2_kayip_kazanci": o2, "2_deger": kazanc,
                         "3_pay_lt3": o3, "4_sure": o4, "5_wp": o5},
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
