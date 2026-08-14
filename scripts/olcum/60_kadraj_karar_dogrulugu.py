"""T63 — KADRAJ kumesinde MODEL TABANLI karar dogrulugu.

NEDEN BU OLCUM YOKTU. Bugune kadar iki ayri sey olculuyordu:
  * `57_t51_kadraj_kapilari.py` — YER GERCEGI etiketleriyle; URETECIN geometrisini
    sinar, modelin basarimini DEGIL.
  * `56_uc_kapili_model_secimi.py` K3 — `data/arena_kompozit` uzerinde; o kumenin
    arka plani OTOPARKTIR (D-53/D-89) ve modelleri AYIRT EDEMIYOR.

Yani "model, sartnameye sadik bir arenada dogru serit buluyor mu" sorusu HIC
olculmedi. Bu betik onu olcer: URETIM zinciri + kadraj kumesi + manifest
yer gercegi + MANIFESTTEN gelen mpp (olcek uydurulmaz).

OLCUT SIRALAMASI — gorev guvenligi sirasi, dogruluk degil:
  1. TEHLIKELI  : sistem KAPALI bir seridi ACIK ilan etti. Sartname SS5.3.2/SS6.2
                  uyarinca yanlis guzergah = 0 puan; ustelik IKA molozla carpisir.
                  BU SAYI SIFIR OLMALIDIR. Diger her sey ikincildir.
  2. DOGRU      : acik serit(ler)den birini verdi.
  3. RET        : karar vermedi (sebep koduyla). Guvenlidir ama gorev ilerlemez.

Uretim fonksiyonlari KOPYALANMAZ, cagrilir (CONTRACTS SS11 sahiplik).

Kullanim:
  venv\\Scripts\\python.exe 60_kadraj_karar_dogrulugu.py --model models/navitas_seg_v24_best.pt \
      --kume calisma/sentetik_arena_kadraj_t60 --json results/t63/v24.json
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import cv2

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import (rota_olcek_reddi,  # noqa: E402
                              zemin_maskesi_reddi)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, analyze_path, get_masks)

CONF = 0.30


def kume_oku(kok):
    """Manifestten (goruntu yolu, arena bilgisi) ciftlerini uret."""
    man = json.loads((kok / "manifest.json").read_text(encoding="utf-8"))
    for ornek in man["ornekler"]:
        if ornek.get("durum") != "YAZILDI":
            continue
        p = kok / ornek["cikti"]
        if p.is_file() and ornek.get("arena"):
            yield p, ornek["arena"]


def kareyi_karara_cevir(model, img):
    """URETIM zinciri — `comms/yks_gui.py` algi blogunun birebir sirasi."""
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    maskeler = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    return maskeler[0], maskeler[1], icerik


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--kume", type=Path, required=True)
    ap.add_argument("--json", type=Path, default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--arena-icerik", action="store_true",
                    help="KAHIN DENEYI: `icerik`i tum kare yerine manifestteki "
                         "ARENA kutusuna daralt. Uretimde boyle bir bilgi YOKTUR; "
                         "bu yalniz kok neden sinamasidir (D-90).")
    args = ap.parse_args()

    kok = args.kume if args.kume.is_absolute() else REPO.parent / args.kume
    model_yolu = (args.model if args.model.is_absolute()
                  else REPO / args.model)
    if not (kok / "manifest.json").is_file():
        raise SystemExit(f"manifest yok: {kok}")
    if not model_yolu.is_file():
        raise SystemExit(f"model yok: {model_yolu}")

    from ultralytics import YOLO
    model = YOLO(str(model_yolu), task="segment")

    kayitlar = []
    sayac = Counter()
    sebepler = Counter()
    for i, (p, arena) in enumerate(kume_oku(kok)):
        if args.limit and i >= args.limit:
            break
        img = cv2.imread(str(p))
        if img is None:
            sayac["OKUNAMADI"] += 1
            continue
        mpp = arena.get("mpp")
        kapali = set(arena.get("kapali_seritler") or [])
        acik = arena.get("acik_serit")
        adaylar = set(arena.get("acik_serit_adaylari") or [])
        if acik is not None:
            adaylar.add(acik)

        trav, blok, icerik = kareyi_karara_cevir(model, img)
        if args.arena_icerik and arena.get("arena_x_araligi"):
            ax0, ax1 = arena["arena_x_araligi"]
            x0, y0, cw, ch = icerik
            nx0 = max(x0, int(round(ax0)))
            nx1 = min(x0 + cw, int(round(ax1)))
            if nx1 - nx0 > 8:
                icerik = (nx0, y0, nx1 - nx0, ch)

        # Kapi sirasi URETIMDEKI ile ayni: olcek -> zemin maskesi -> rota.
        olcek_red = rota_olcek_reddi(mpp)
        zemin_red = zemin_maskesi_reddi(trav, icerik)
        yol, guven, wps, _kor, karar_red, olcum = analyze_path(
            trav, icerik=icerik, engel_mask=blok, mpp=mpp,
            return_clean=True, return_reason=True, return_olcum=True)

        red = olcek_red or zemin_red or karar_red
        if red is not None:
            sinif = "RET"
            sebepler[red[0] if isinstance(red, tuple) else str(red)] += 1
        elif yol is None:
            sinif = "RET"
            sebepler["ROTA_YOK"] += 1
        elif yol in kapali:
            sinif = "TEHLIKELI"
        elif not adaylar or yol in adaylar:
            sinif = "DOGRU"
        else:
            sinif = "YANLIS"
        sayac[sinif] += 1
        kayitlar.append({
            "kare": p.name, "serit": yol, "guven": guven,
            "beklenen": arena.get("beklenen_durum"), "acik": acik,
            "adaylar": sorted(adaylar), "kapali": sorted(kapali),
            "sinif": sinif,
            "red": (red[0] if isinstance(red, tuple) else red),
            "darbogaz_px": (olcum or {}).get("darbogaz_px"),
            "r_gerekli_px": (olcum or {}).get("r_gerekli_px"),
            "mpp": mpp,
        })

    n = len(kayitlar)
    print(f"\nmodel : {model_yolu.name}")
    print(f"kume  : {kok.name}   n = {n}")
    print("-" * 62)
    for ad in ("TEHLIKELI", "DOGRU", "YANLIS", "RET"):
        v = sayac.get(ad, 0)
        pay = (100.0 * v / n) if n else 0.0
        isaret = "  <-- SIFIR OLMALI" if ad == "TEHLIKELI" and v else ""
        print(f"  {ad:<10} {v:>4} / {n}   %{pay:5.1f}{isaret}")
    if sebepler:
        print("\n  RET sebepleri:")
        for s, v in sebepler.most_common():
            print(f"    {s:<28} {v:>4}")
    print("-" * 62)

    if args.json:
        cikti = args.json if args.json.is_absolute() else REPO.parent / args.json
        cikti.parent.mkdir(parents=True, exist_ok=True)
        cikti.write_text(json.dumps({
            "model": str(model_yolu), "kume": str(kok), "n": n,
            "conf": CONF, "ozet": dict(sayac), "ret_sebepleri": dict(sebepler),
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"json -> {cikti}")


if __name__ == "__main__":
    main()
