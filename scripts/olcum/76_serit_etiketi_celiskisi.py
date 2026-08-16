"""IKI ETIKETLEME OTORITESI AYNI KORIDORA FARKLI NUMARA MI VERIYOR? (T79-B olcum)

NEDEN (75_koridor_envanteri olcumunden cikti). Ayni maskeler uzerinde iki karar
yolu KORIDOR NUMARASINDA celisiyor:
  - `analyze_path` (uretim)  : rotanin gectigi seriti `serit_no()` ile okur
  - `rota_bul` (envanter)    : `koridor_adaylari()` kapiya kendi numarasini verir
Olculdu (75, temiz kosu): envanterin ACIK verdigi 34 karenin 8'inde iki yol
FARKLI serit soyluyor; envanterde en az bir gecilebilir aday olan 247 karenin
55'inde uretimin seridi o kumede HIC YOK.

BU SAYI TEK BASINA IKI SEYE BIRDEN UYAR ve ikisi COK FARKLI agirliktadir:
  (H1) ETIKETLEME CERCEVESI FARKI. `serit_no()` sinirlari LETTERBOX ICERIK
       KUTUSUNU uce boler (karar_sozlesmesi.py:42-54, CONTRACTS SS8).
       `koridor_adaylari()` ise n_kapi != 3 iken kapiyi SERBEST ALAN BBOX'ina
       gore uce boler (costmap_path_finder.py:446-448), n_kapi == 3 iken de
       soldan saga SIRA NUMARASI verir (i+1). Kadraj alinmis bir karede serbest
       alan icerik kutusunun tamamini doldurmaz; ayni fiziksel koridor iki
       semada FARKLI numara alir. Bu bir ETIKET kusurudur.
  (H2) GERCEK ROTA UYUSMAZLIGI. Iki yol farkli AMAC FONKSIYONU optimize eder:
       `_guven_hesapla` EN GENIS darbogazi secer; A* ise aciklik agirlikli EN
       UCUZ yolu secer. En genis koridor en ucuz koridor olmak zorunda degildir.

BU BETIK IKISINI AYIRIR. Her aday kapi icin `etiket` ile
`serit_no(kapi_merkez_x, ...)` yan yana konur. Etiketler `serit_no` ile YENIDEN
yazildiginda celiski KAPANIYORSA fark H1'dir; KAPANMIYORSA kalan H2'dir.

NEDEN ONEMLI: `comms/ika_receiver.py:11` -> `plan_path(route["road"])`. IKA
WAYPOINT ile degil SERIT NUMARASI ile plan yapar. Yanlis numara, IHA'nin
dogruladigi koridordan BASKA bir koridora surer.

Gurultu YOKTUR — bu bir kararlilik olcumu degil, TUTARLILIK olcumudur.
Yer gercegi KULLANILMAZ; sorulan "hangisi dogru" degil, "ayni seyi mi
soyluyorlar".
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

from costmap_path_finder import koridor_adaylari, serbest_alan   # noqa: E402
from karar_sozlesmesi import serit_no                            # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
MODEL = uretim_pt()          # surum adi CIPLAK SABIT degil (madde 16)
CONF = 0.30


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

    n = 0
    kayitlar = []
    aday_top = aday_celiski = 0
    celiski_by_nkapi = {}
    aday_by_nkapi = {}
    icerik_farkli = 0

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

        # TEK cikarim, iki tuketici (D-139 dersi).
        sq, small, icerik = _preprocess(img)
        r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)

        yol, guven, _wps, _k, red, olcum = analyze_path(
            mk[0], icerik=icerik, engel_mask=mk[1], mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)
        olcum = olcum or {}

        s = serbest_alan(mk, mpp=mpp, icerik=icerik)
        adaylar, tani = koridor_adaylari(
            s["dt_px"], s["olcek"]["r_gerekli_px"], None, None,
            icerik=s["icerik"])

        # `serit_no` uretimde `analyze_path`e verilen `icerik` ile cagrilir.
        # `serbest_alan` kutuyu dogrulayip degistirmisse KIYAS GECERSIZ olur —
        # bu yuzden sayilir, sessizce gecilmez.
        if tuple(int(v) for v in s["icerik"]) != tuple(int(v) for v in icerik):
            icerik_farkli += 1
        ix0, _iy0, iw, _ih = icerik

        nk = tani.get("n_kapi")
        satirlar = []
        for a in adaylar:
            cx = int(a["kapi_merkez_x"])
            sn = int(serit_no(cx, ix0, iw))
            uyum = (int(a["etiket"]) == sn)
            # KAPI BIR NOKTA DEGIL, BIR ACIKLIKTIR. `etiket`/`serit_no` ikisi de
            # AGIRLIK MERKEZINDEN turer; genis bir kapinin merkezi serit 1'de
            # olup rota serit 2 kismindan gecebilir. Kapinin YAYILIMI bu yuzden
            # kaydedilir. YAKLASIKTIR: uretim x0/x1 dondurmez, yalniz merkez ve
            # GENISLIK doner (costmap_path_finder.py:452-453), yayilim
            # cx ± genislik/2 ile kestirilir.
            gw = int(a["kapi_genislik_px"])
            sn_sol = int(serit_no(cx - gw / 2.0, ix0, iw))
            sn_sag = int(serit_no(cx + gw / 2.0, ix0, iw))
            aday_top += 1
            aday_by_nkapi[str(nk)] = aday_by_nkapi.get(str(nk), 0) + 1
            if not uyum:
                aday_celiski += 1
                celiski_by_nkapi[str(nk)] = celiski_by_nkapi.get(str(nk), 0) + 1
            satirlar.append({"etiket": int(a["etiket"]), "serit_no": sn,
                             "cx": cx, "gecilebilir": bool(a["gecilebilir"]),
                             "darbogaz_px": round(float(a["darbogaz_px"]), 2),
                             "genislik_px": gw,
                             "yayilim": [min(sn_sol, sn_sag), max(sn_sol, sn_sag)]})

        kayitlar.append({
            "kare": p.name, "n_kapi": nk, "durum_belirsiz": tani.get("belirsiz"),
            "uretim_serit": yol, "uretim_red": red[0] if isinstance(red, tuple) else red,
            "uretim_darbogaz_px": olcum.get("darbogaz_px"),
            "r_gerekli_px": olcum.get("r_gerekli_px"),
            # Yayinlanan `road` = `darbogaz_serit` (rpi_inference.py:1255).
            # `baskin_serit` HESAPLANIR ama YAYINLANMAZ; ikisi ayrilirsa IKA
            # rotanin cogunlukla gectigi seridi DEGIL, en dar noktasinin
            # dustugu ucte birlik dilimi alir.
            "darbogaz_serit": olcum.get("darbogaz_serit"),
            "baskin_serit": olcum.get("baskin_serit"),
            "seritler": list(olcum.get("seritler") or ()),
            "serit_min_px": [None if v is None else round(float(v), 2)
                             for v in (olcum.get("serit_min_px") or ())],
            "cok_seritli": olcum.get("cok_seritli"),
            "icerik": [int(v) for v in icerik],
            "adaylar": satirlar})
        if n % 40 == 0:
            print(f"  ... {n} kare", flush=True)

    # ── COZUMLEME ──────────────────────────────────────────────────────────
    # ESKI etiketle vs YENIDEN ETIKETLENMIS (serit_no) kume kiyasi.
    gec_var = eski_icinde = yeni_icinde = yayilim_icinde = 0
    kapandi, yayilimla_kapandi, kapanmadi, hic_sorun_yok = [], [], [], 0
    for k in kayitlar:
        if k["uretim_serit"] is None:
            continue
        gec = [a for a in k["adaylar"] if a["gecilebilir"]]
        if not gec:
            continue
        gec_var += 1
        eski = {a["etiket"] for a in gec}
        yeni = {a["serit_no"] for a in gec}
        e_ok = k["uretim_serit"] in eski
        y_ok = k["uretim_serit"] in yeni
        # Kapinin YAYILIMI: uretim seridi gecilebilir bir kapinin genisligi
        # icine dusuyorsa iki yol AYNI acikligi gosteriyor, numara farkli.
        yay_ok = any(a["yayilim"][0] <= k["uretim_serit"] <= a["yayilim"][1]
                     for a in gec)
        eski_icinde += int(e_ok)
        yeni_icinde += int(y_ok)
        yayilim_icinde += int(yay_ok)
        if e_ok:
            hic_sorun_yok += 1
        elif y_ok:
            kapandi.append(k["kare"])
        elif yay_ok:
            yayilimla_kapandi.append(k)
        else:
            kapanmadi.append(k)

    # YAYINLANAN SAYI, ROTANIN KULLANDIGI SERIT MI?
    # `road` = darbogaz_serit (en dar noktanin seridi). `baskin_serit` (en cok
    # rota pikseli tasiyan serit) hesaplanir ama yayinlanmaz. Ikisi ayrilan
    # karede IKA `plan_path(road)` ile rotanin ana govdesinden BASKA bir seride
    # yonlendirilir. Bu bir KARARLILIK degil TANIM sorunudur; gurultu gerekmez.
    rotali = [k for k in kayitlar if k["darbogaz_serit"] is not None]
    ayrilan = [k for k in rotali if k["darbogaz_serit"] != k["baskin_serit"]]
    cok_seritli = [k for k in rotali if k["cok_seritli"]]
    ayrilan_cok = [k for k in ayrilan if k["cok_seritli"]]

    c = "=" * 76
    print(f"\n{c}\nSERIT ETIKETI CELISKISI · {args.model.name}\n"
          f"  kume {args.kume.name} · n={n} · gurultu YOK\n{c}")
    print(f"  toplam aday kapi                 : {aday_top}")
    print(f"  etiket != serit_no(kapi_merkez_x): {aday_celiski} "
          f"(%{100*aday_celiski/max(1,aday_top):.1f})")
    print(f"  serbest_alan icerik kutusunu degistirdi: {icerik_farkli}/{n}")
    print(f"\n  n_kapi kirilimi (celiskili aday / toplam aday):")
    for key in sorted(set(aday_by_nkapi) | set(celiski_by_nkapi), key=lambda x: int(x)):
        print(f"    n_kapi={key:>2} : {celiski_by_nkapi.get(key,0):>4} / "
              f"{aday_by_nkapi.get(key,0):>4}")

    print(f"\n{c}\nURETIM SERIDI, GECILEBILIR ADAY KUMESINDE MI?\n{c}")
    print(f"  olculebilen kare (rota var + >=1 gecilebilir aday): {gec_var}")
    print(f"    ESKI etiketle  (koridor_adaylari)  icinde: {eski_icinde}  "
          f"disinda: {gec_var - eski_icinde}")
    print(f"    YENI etiketle  (serit_no ile)      icinde: {yeni_icinde}  "
          f"disinda: {gec_var - yeni_icinde}")
    print(f"    KAPI YAYILIMIYLA (yaklasik)        icinde: {yayilim_icinde}  "
          f"disinda: {gec_var - yayilim_icinde}")
    print(f"\n  zaten celiskisiz                      : {hic_sorun_yok}")
    print(f"  YENIDEN ETIKETLEMEYLE kapanan         : {len(kapandi)}  -> H1a (ETIKET CERCEVESI)")
    print(f"  KAPI YAYILIMIYLA kapanan              : {len(yayilimla_kapandi)}  -> H1b (KAPI GENIS, MERKEZ YANILTIYOR)")
    print(f"  HALA KAPANMAYAN                       : {len(kapanmadi)} -> H2 (GERCEKTEN FARKLI KORIDOR)")

    print(f"\n{c}\nYAYINLANAN `road` ROTANIN KULLANDIGI SERIT MI?\n{c}")
    print(f"  rota uretilen kare                    : {len(rotali)}")
    print(f"  rota BIRDEN FAZLA seride giriyor       : {len(cok_seritli)}")
    print(f"  darbogaz_serit != baskin_serit (YAYIN != GOVDE): {len(ayrilan)}"
          f"  (%{100*len(ayrilan)/max(1,len(rotali)):.1f})")
    print(f"    bunlarin cok seritli olani           : {len(ayrilan_cok)}")
    for k in ayrilan[:15]:
        print(f"     {k['kare']}  yayin={k['darbogaz_serit']} "
              f"govde={k['baskin_serit']} piksel={k['seritler']} "
              f"serit_min={k['serit_min_px']}")

    print(f"\n{c}\nKAPANMAYAN KARELER (H2 adaylari)\n{c}")
    for k in (kapanmadi+yayilimla_kapandi)[:20]:
        print(f"  {k['kare']}  uretim serit={k['uretim_serit']} "
              f"darbogaz={k['uretim_darbogaz_px']} r_ger={k['r_gerekli_px']} "
              f"n_kapi={k['n_kapi']}")
        for a in k["adaylar"]:
            print(f"     etiket={a['etiket']} serit_no={a['serit_no']} "
                  f"cx={a['cx']} gec={a['gecilebilir']} db={a['darbogaz_px']}")
    print(c)
    print("  OKUMA: kapanan celiski ETIKETLEME CERCEVESI farkidir (H1) —")
    print("  koridor ayni, numara farkli. Kapanmayan celiski iki yolun FARKLI")
    print("  KORIDOR sectigi anlamina gelir (H2) ve amac fonksiyonu farkindan")
    print("  gelir: envanter EN GENIS darbogazi, A* EN UCUZ yolu secer.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume), "n": n,
            "conf": CONF,
            "aday_toplam": aday_top, "aday_celiski": aday_celiski,
            "celiski_by_nkapi": celiski_by_nkapi, "aday_by_nkapi": aday_by_nkapi,
            "icerik_farkli": icerik_farkli,
            "gec_var": gec_var, "eski_icinde": eski_icinde,
            "yeni_icinde": yeni_icinde,
            "H1_kapanan": kapandi,
            "H2_kapanmayan": [k["kare"] for k in kapanmadi], "H1b_yayilimla_kapanan": [k["kare"] for k in yayilimla_kapandi],
            "rota_uretilen": len(rotali), "cok_seritli": len(cok_seritli),
            "yayin_govde_ayrilan": len(ayrilan),
            "yayin_govde_ayrilan_cok_seritli": len(ayrilan_cok),
            "yayin_govde_ayrilan_kareler": [k["kare"] for k in ayrilan],
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
