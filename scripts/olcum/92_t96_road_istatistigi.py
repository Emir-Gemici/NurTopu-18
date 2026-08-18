"""T96 · YAYINLANAN `road` HANGI ISTATISTIK OLMALI? (FAZ 1 — YALNIZ OLCUM)

SORU (on kayit: `scripts/olcum/t96_on_kayit.md`). `rpi_inference.py:1255`
`open_path = olcum["darbogaz_serit"]` — rotanin EN DAR noktasinin seridi.
`baskin_serit` hesaplanir ama YAYINLANMAZ. Sorulan sey "hangi koridor acik";
sorulmayan sey "en dar nokta nerede".

    A = darbogaz_serit   (yayinlanan, mevcut)
    B = baskin_serit     (en cok rota pikseli tasiyan serit)
    C = cikis_serit      (rotanin UST ucunun seridi — burada hesaplanir)

`road` PUANLANAN cevaptir; IKA onunla SURMEZ (D-166: `ika_nav.py:179-182`
sayisal `road`u geometri saymayi ACIKCA reddeder, `waypoints`+`ref_xy` ile
surer). Onem bundandir: yanlis numara IKA'yi yanlis koridora surmez, YANLIS
CEVAP YAYINLAR (sartname SS5.3.2/SS6.2 -> yanlis guzergah 0 puan).

────────────────────────────────────────────────────────────────────────────
OLCUM SOZLESMESI (D-139): kare basina model YALNIZ BIR KEZ kosar; A, B ve C
AYNI `_rota_serit_olcumu`/`analyze_path` ciktisindan turetilir. Kume
`sentetik_arena_kadraj_t66` (n=260), TEMIZ kare, CEKILIS YOK.

YER GERCEGI: manifest `arena.acik_serit` — URETECIN KARAR UZAYINDAKI etiketi.
Mimar 260 karede dogruladi: `karar_seridi != serit_no(serit_kutusu merkezi)`
olan kare 0/260, `acik_serit is None` olan 49 karenin HEPSI `belirsiz=True`.
⚠ D-166'daki ESLEME TUZAGI bu kumede ISIRMIYOR; fazladan esleme makinesi
KURULMAZ — ama POZITIF KONTROL yine de basilir (0 degilse OLCUM GECERSIZ).

KARSILASTIRILABILIR KUME: `acik_serit` None OLMAYAN kareler VE uretimin rota
urettigi kareler. `belirsiz` kareler DISLANIR (uretecin kendisi tek cevap
ilan etmiyor) ve sayilir.

⚠ C ROTANIN UST UCUNDAN, Y'YE GORE secilir — indise GUVENILMEZ. `analyze_path`
docstring'i "alt->ust sirali" der ama sira bir SOZLESME DEGILDIR; en kucuk y
aranir.
────────────────────────────────────────────────────────────────────────────
"""
import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import serit_no                            # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
MODEL = uretim_pt()          # surum adi CIPLAK SABIT degil (madde 16)
CONF = 0.30

ADAYLAR = ("A_darbogaz", "B_baskin", "C_cikis")


def cikis_seridi(waypoints, icerik):
    """Rotanin UST ucunun seridi. Y'ye gore secilir, indise gore DEGIL."""
    if not waypoints:
        return None
    ust = min(waypoints, key=lambda w: w[1])
    ix0, _iy0, iw, _ih = icerik
    return int(serit_no(float(ust[0]), ix0, iw))


def yer_gercegi_kontrolu(arena, icerik):
    """POZITIF KONTROL: `karar_seridi` ile `serit_no(kutu merkezi)` ortusuyor mu?

    🔴 KUTU SECIMI OLCULEREK BULUNDU — ilk denememde `serit_kutusu` kullandim
    ve kontrol ATESLEDI (527 seridin 21'i uyusmuyor). Sebep D-166'nin isaret
    ettigi esleme tuzagidir: `serit_kutusu` URETECIN tam serit kutusudur ve
    kadraj onu KIRPAR; kirpilmis bir seridin TAM kutu merkezi baska bir ucte
    bire dusebilir. Karar uzayinin gordugu sey seridin KARE ICINDE KALAN
    gecilebilir parcasidir -> `gecilebilir_kutu`. Olculen:

        gecilebilir_kutu (varsa) -> serit_kutusu :   0 / 527 uyusmaz
        yalniz serit_kutusu                      :  21 / 527 uyusmaz
        arena_x_araligi ile bolme                : 133 / 527 uyusmaz

    Yani kontrol GERCEKTEN ayirt edicidir; 0 cikmasi tesadufi degildir.
    """
    ix0, _iy0, iw, _ih = icerik
    uyusmaz = 0
    for s in (arena.get("uretec_seritleri") or []):
        ks = s.get("karar_seridi")
        kutu = s.get("gecilebilir_kutu") or s.get("serit_kutusu")
        if ks is None or not kutu:
            continue
        merkez_x = float(kutu[0]) + float(kutu[2]) / 2.0
        if int(serit_no(merkez_x, ix0, iw)) != int(ks):
            uyusmaz += 1
    return uyusmaz


def acik_serit_tutarli_mi(arena):
    """IKINCI POZITIF KONTROL: `acik_serit`, ACIK seridin `karar_seridi`si mi?

    Yer gercegini `acik_serit`ten okuyorum; o degerin uretecin serit
    dokumuyle CELISMEDIGI ayrica sinanir (celisirse hangi otoriteye
    baktigim belirsizlesir).

    🔴 ILK KURDUGUM DEGISMEZ YANLISTI, kayda geciyor. "acik_serit doluysa TAM
    BIR acik serit olmali" yazmistim; kontrol 25 karede atesledi. Ayristirinca
    veri degil VARSAYIMIM yanlis cikti:

        acik_serit VAR + karar_seridi CELISEN serit :  0 / 260   <- asil sey
        acik_serit VAR + birden cok "acik" serit    :  5   (hepsi AYNI
                                                     karar_seridi, or. [2,2,2])
        acik_serit YOK (BELIRSIZ)                   : 49   (29 tek + 20 coklu)

    Kadraj birden cok URETEC seridini TEK karar seridine katlayabiliyor
    (`sa_000020`: uc serit de karar_seridi=2). Bu bir celiski degildir. Gercek
    degismez: **acik_serit doluysa HICBIR acik serit onunla CELISMEYECEK**;
    bosaa ise kare `belirsiz` olacak.
    """
    a = arena.get("acik_serit")
    acik = [s for s in (arena.get("uretec_seritleri") or [])
            if s.get("durum") == "acik" and s.get("karar_seridi") is not None]
    if a is None:
        return not bool(arena.get("belirsiz"))     # yer gercegi yoksa BELIRSIZ olmali
    return not (acik and all(int(s["karar_seridi"]) == int(a) for s in acik))


def _ikili_dominans(kayitlar, kazanan, rakip):
    """(T1b) KESIN DOMINANS. Ayrisan alt kumede:
       · rakibin YANILDIGI her karede kazanan DOGRU olmali,
       · rakibin DOGRU oldugu hicbir karede kazanan YANILMAMALI.
    Doner: (tutuyor_mu, kazanan_kurtardi, rakip_kurtardi, ayrisan_n)."""
    ayrisan = [k for k in kayitlar if k[kazanan] != k[rakip]]
    kazanan_kurtardi = sum(1 for k in ayrisan
                           if k[kazanan] == k["yer"] and k[rakip] != k["yer"])
    rakip_kurtardi = sum(1 for k in ayrisan
                         if k[rakip] == k["yer"] and k[kazanan] != k["yer"])
    return (rakip_kurtardi == 0 and len(ayrisan) > 0 and kazanan_kurtardi >= 0,
            kazanan_kurtardi, rakip_kurtardi, len(ayrisan))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sinir", type=int, default=0)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    n = rota_var = 0
    dislanan_belirsiz = 0        # acik_serit None (uretec BELIRSIZ ilan etti)
    yer_yok_ama_rota = 0
    esleme_uyusmaz = 0
    acik_serit_celiskisi = 0
    icerik_farkli = 0
    c_hesaplanamadi = 0
    kayitlar = []                # yalniz KARSILASTIRILABILIR kareler
    hepsi = []                   # tum rota ureten kareler (dokum icin)

    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
            continue
        p = args.kume / ornek["cikti"]
        arena = ornek["arena"]
        mpp = arena.get("mpp")
        if not p.is_file() or not mpp:
            continue
        img = cv2.imread(str(p))
        if img is None:
            continue
        if args.sinir and n >= args.sinir:
            break
        n += 1

        # TEK cikarim, tek karar yolu (D-139).
        sq, small, icerik = _preprocess(img)
        r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)

        yol, _guven, wps, _k, _red, olcum = analyze_path(
            mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)

        esleme_uyusmaz += yer_gercegi_kontrolu(arena, icerik)
        if acik_serit_tutarli_mi(arena):
            acik_serit_celiskisi += 1
        man_icerik = arena.get("icerik")
        if man_icerik and tuple(int(v) for v in man_icerik) != tuple(
                int(v) for v in icerik):
            icerik_farkli += 1

        if yol is None or not olcum:
            continue
        rota_var += 1

        A = int(olcum["darbogaz_serit"])
        B = int(olcum["baskin_serit"])
        C = cikis_seridi(wps, icerik)
        if C is None:
            c_hesaplanamadi += 1

        satir = {
            "kare": p.name,
            "A_darbogaz": A, "B_baskin": B, "C_cikis": C,
            "yayinlanan_open_path": int(yol),
            "cok_seritli": bool(olcum.get("cok_seritli")),
            "seritler": list(olcum.get("seritler") or []),
            "serit_min_px": [None if v is None else round(float(v), 2)
                             for v in (olcum.get("serit_min_px") or [])],
            "darbogaz_px": round(float(olcum.get("darbogaz_px", 0.0)), 2),
            "yer": arena.get("acik_serit"),
            "belirsiz": bool(arena.get("belirsiz")),
        }
        hepsi.append(satir)

        if satir["yer"] is None:
            dislanan_belirsiz += 1
            continue
        if C is None:
            yer_yok_ama_rota += 1
            continue
        satir["yer"] = int(satir["yer"])
        kayitlar.append(satir)

    # ── COZUMLEME ──────────────────────────────────────────────────────────
    uyum = {a: sum(1 for k in kayitlar if k[a] == k["yer"]) for a in ADAYLAR}
    ayrisma = {
        "A!=B": sum(1 for k in kayitlar if k["A_darbogaz"] != k["B_baskin"]),
        "A!=C": sum(1 for k in kayitlar if k["A_darbogaz"] != k["C_cikis"]),
        "B!=C": sum(1 for k in kayitlar if k["B_baskin"] != k["C_cikis"]),
    }
    ucu_farkli = sum(1 for k in kayitlar
                     if len({k["A_darbogaz"], k["B_baskin"], k["C_cikis"]}) == 3)
    ayrisan = [k for k in kayitlar
               if len({k["A_darbogaz"], k["B_baskin"], k["C_cikis"]}) > 1]

    c = "=" * 78
    print(f"\n{c}\nT96 · YAYINLANAN `road` HANGI ISTATISTIK OLMALI?")
    print(f"  model {args.model.name} · kume {args.kume.name} · n={n} · "
          f"TEMIZ kare (cekilis yok)\n{c}")
    print(f"  olculen kare                         : {n}")
    print(f"  uretim ROTA URETEN kare              : {rota_var}")
    print(f"  DISLANAN (uretec BELIRSIZ, yer=None) : {dislanan_belirsiz}")
    print(f"  C hesaplanamadi (waypoint yok)       : {c_hesaplanamadi}")
    print(f"  KARSILASTIRILABILIR kare             : {len(kayitlar)}")

    print(f"\n{c}\nPOZITIF KONTROLLER\n{c}")
    gecerli = True
    for ad, olculen, beklenen in [
            ("karar_seridi != serit_no(merkez) olan serit", esleme_uyusmaz, 0),
            ("manifest icerik != uretim icerik olan kare", icerik_farkli, 0),
            ("acik_serit ile uretec dokumu celisen kare",
             acik_serit_celiskisi, 0)]:
        ok = olculen == beklenen
        gecerli &= ok
        print(f"  {'OK ' if ok else 'HATA'}  {ad:44s}{olculen} (beklenen {beklenen})")
    print(f"  -> ESLEME {'GECERLI' if gecerli else 'GECERSIZ'}")

    print(f"\n{c}\nAYRISMA (karsilastirilabilir kume, n={len(kayitlar)})\n{c}")
    for ad, sayi in ayrisma.items():
        print(f"  {ad:8s}{sayi}")
    print(f"  ucu birden farkli: {ucu_farkli}")
    print(f"  EN AZ IKISI farkli (ayrisan alt kume): {len(ayrisan)}")

    print(f"\n{c}\nTAM KUME UYUM (yer gercegine gore)\n{c}")
    for a in ADAYLAR:
        pay = 100.0 * uyum[a] / max(1, len(kayitlar))
        print(f"  {a:12s}{uyum[a]:4d} / {len(kayitlar)}   (%{pay:.1f})")

    print(f"\n{c}\nAYRISAN ALT KUME — KARE KARE\n{c}")
    if not ayrisan:
        print("  (BOS — hicbir karede adaylar ayrismadi)")
    else:
        print(f"  {'kare':16s}{'yer':>4s}{'A':>3s}{'B':>3s}{'C':>3s}"
              f"{'cok':>5s}  {'serit pikselleri':>18s}  serit_min_px")
        for k in ayrisan:
            print(f"  {k['kare']:16s}{k['yer']:>4d}{k['A_darbogaz']:>3d}"
                  f"{k['B_baskin']:>3d}{k['C_cikis']:>3d}"
                  f"{'E' if k['cok_seritli'] else '-':>5s}"
                  f"  {str(k['seritler']):>18s}  {k['serit_min_px']}")

    # ── ON KAYIT OLCUTLERI ────────────────────────────────────────────────
    print(f"\n{c}\nON KAYIT OLCUTLERI (scripts/olcum/t96_on_kayit.md)\n{c}")
    en_iyi = max(ADAYLAR, key=lambda a: uyum[a])
    esit = [a for a in ADAYLAR if uyum[a] == uyum[en_iyi]]
    T1a = all(uyum[en_iyi] >= uyum[a] for a in ADAYLAR)
    print(f"  (T1a) TAM KUME kazanan: {en_iyi} ({uyum[en_iyi]}) · "
          f"digerleri: " + " · ".join(f"{a}={uyum[a]}" for a in ADAYLAR
                                      if a != en_iyi))
    if len(esit) > 1:
        print(f"        BERABERLIK: {', '.join(esit)} — mevcut A varsa A KALIR")
    print(f"  {'TUTTU ' if T1a else 'DUSTU '}(T1a)")

    ayrisan_yer = ayrisan       # zaten yalniz yer gercegi olan kareler
    T1c_bos = len(ayrisan_yer) == 0
    print(f"\n  (T1c) ayrisan + yer gercegi olan alt kume: {len(ayrisan_yer)} kare"
          + ("   -> BOS: KARAR VERILEMEZ, DEGISIKLIK YOK" if T1c_bos else ""))

    print(f"\n  (T1b) KESIN DOMINANS — ikili dokum (ayrisan alt kumede):")
    dominans = {}
    for kaz in ADAYLAR:
        tut_hepsi = True
        for rak in ADAYLAR:
            if rak == kaz:
                continue
            ok, kk, rk, an = _ikili_dominans(kayitlar, kaz, rak)
            print(f"    {kaz:12s} vs {rak:12s} ayrisan={an:3d}  "
                  f"{kaz} kurtardi={kk}  {rak} kurtardi={rk}  "
                  f"-> {'DOMINANT' if ok else 'TAKAS/YOK'}")
            tut_hepsi &= ok
        dominans[kaz] = tut_hepsi

    T1b = (not T1c_bos) and dominans.get(en_iyi, False) and len(esit) == 1
    print(f"\n  {'TUTTU ' if T1b else 'DUSTU '}(T1b) kazanan {en_iyi} "
          f"digerlerinin HEPSINE kesin dominant mi")

    karar = "DEGISIKLIK YOK"
    if T1c_bos:
        karar = "KARAR VERILEMEZ (ayrisan+yer gercegi alt kume BOS) — DEGISIKLIK YOK"
    elif T1a and T1b and en_iyi != "A_darbogaz":
        karar = f"KAZANAN {en_iyi} — (T2)..(T5) kosulmali"
    elif en_iyi == "A_darbogaz":
        karar = "KAZANAN A (mevcut) — MEVCUT ISTATISTIK DOGRULANDI, degisiklik YOK"
    print(f"\n  KARAR: {karar}")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume), "n": n,
            "conf": CONF, "rota_var": rota_var,
            "dislanan_belirsiz": dislanan_belirsiz,
            "c_hesaplanamadi": c_hesaplanamadi,
            "karsilastirilabilir": len(kayitlar),
            "kontrol": {"esleme_uyusmaz": esleme_uyusmaz,
                        "icerik_farkli": icerik_farkli,
                        "acik_serit_celiskisi": acik_serit_celiskisi,
                        "gecerli": bool(gecerli)},
            "uyum": uyum, "ayrisma": ayrisma, "ucu_farkli": ucu_farkli,
            "ayrisan": ayrisan, "dominans": dominans,
            "olcutler": {"T1a": bool(T1a), "T1b": bool(T1b),
                         "T1c_bos": bool(T1c_bos)},
            "en_iyi": en_iyi, "karar": karar,
            "kayitlar": kayitlar, "tum_rota_ureten": hepsi,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
