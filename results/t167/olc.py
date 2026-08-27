"""T167 olcumu (ON_KAYIT SS32): kabul kumesinin ETIKET maskeleri gercekten kac
guzergah birakiyor?

D-311'de kaba bir yontem ("ucte bir dilimi + alt<->ust baglanti") ~%45 karede
IKI serit acik demisti. Ama `koridor_adaylari` docstring'i aynen soyle der:
"3 guzergah baslangicta ayrilip hedefte BIRLESIYOR — kapali bir yol AYRI bir
bilesen degil, ayni bilesene bagli bir CIKMAZ. Duz baglanti testi hangi
guzergahin acik oldugunu SOYLEYEMEZ."

Bu betik kodun KENDI OTORITESINI kullanir: yer gercegi maskesiyle `rota_bul`
kosulur ve donen `adaylar` listesindeki GECILEBILIR aday sayisi sayilir.
Model KULLANILMAZ — bu bir KUME olcumudur.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(_y))

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import rpi_inference as ri  # noqa: E402
from costmap_path_finder import rota_bul  # noqa: E402


def _etiket(lbl: Path, w: int, h: int):
    m0 = np.zeros((h, w), np.uint8)
    m1 = np.zeros((h, w), np.uint8)
    if not lbl.is_file():
        return m0, m1
    for satir in lbl.read_text(encoding="utf-8").splitlines():
        p = satir.split()
        if len(p) < 7:
            continue
        c = int(float(p[0]))
        k = np.array([float(x) for x in p[1:]], np.float32).reshape(-1, 2)
        k[:, 0] *= w
        k[:, 1] *= h
        cv2.fillPoly(m0 if c == 0 else m1, [k.astype(np.int32)], 255)
    return m0, m1


def main():
    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    kume = Path(defter["profiles"]["competition"]["kabul_kumesi"])
    mf = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    arena = {Path(o["cikti"]).name: o["arena"] for o in mf["ornekler"]
             if isinstance(o.get("arena"), dict)}

    kareler = []
    for alt in ("val", "train"):
        kareler += [(p, kume / "labels" / alt / (p.stem + ".txt"))
                    for p in sorted((kume / "images" / alt).glob("*.jpg"))]
    kareler = [(g, l) for g, l in kareler if g.name in arena]
    print(f"kare {len(kareler)}", flush=True)

    satirlar = []
    for i, (gorsel, lbl) in enumerate(kareler, 1):
        a = arena[gorsel.name]
        img = cv2.imread(str(gorsel))
        sq, small, icerik = ri._preprocess(img)
        yan = sq.shape[0]
        x0, y0, w, h = icerik
        g0, g1 = _etiket(lbl, img.shape[1], img.shape[0])
        trav = np.zeros((yan, yan), np.uint8)
        blok = np.zeros((yan, yan), np.uint8)
        trav[y0:y0 + h, x0:x0 + w] = g0
        blok[y0:y0 + h, x0:x0 + w] = g1
        try:
            sonuc = rota_bul({0: trav, 1: blok}, mpp=a.get("mpp"), icerik=icerik)
        except Exception as exc:
            satirlar.append({"kare": gorsel.name, "hata": f"{type(exc).__name__}: {exc}"})
            continue
        adaylar = sonuc.get("adaylar") or []
        gecilebilir = [ad for ad in adaylar if ad.get("gecilebilir")]
        etiketler = sorted({ad.get("etiket") for ad in gecilebilir})
        satirlar.append({
            "kare": gorsel.name,
            "acik_serit": a.get("acik_serit"),
            "aday_toplam": len(adaylar),
            "gecilebilir_n": len(gecilebilir),
            "gecilebilir_etiketler": etiketler,
            "durum": sonuc.get("durum"),
            "yol_no": sonuc.get("yol_no"),
            "tekil_uyusuyor": bool(len(gecilebilir) == 1
                                   and etiketler[:1] == [a.get("acik_serit")]),
            # T101 imzasi: kapi bir NOKTA degil ACIKLIKTIR ve iki seride
            # yayilabilir (koridor_adaylari docstring'i). Yayilim iki serit
            # gosteriyorsa etiket TANIM GEREGI belirsizdir.
            "gecilebilir_ayrinti": [
                {"etiket": ad.get("etiket"),
                 "kapi_merkez_x": ad.get("kapi_merkez_x"),
                 "kapi_genislik_px": ad.get("kapi_genislik_px"),
                 "serit_yayilimi": ad.get("serit_yayilimi")}
                for ad in gecilebilir],
            "icerik": [x0, y0, w, h],
        })
        if i % 50 == 0:
            print(f"  {i}/{len(kareler)}", flush=True)

    olculen = [s for s in satirlar if "hata" not in s]
    dagilim = collections.Counter(s["gecilebilir_n"] for s in olculen)
    tekil = [s for s in olculen if s["gecilebilir_n"] == 1]
    coklu = [s for s in olculen if s["gecilebilir_n"] >= 2]
    tekil_uyusan = sum(1 for s in tekil if s["tekil_uyusuyor"])
    n = len(olculen)
    tekil_pay = len(tekil) / n if n else None
    coklu_pay = len(coklu) / n if n else None

    hukum = ("ETIKETLER SAGLAM — onceki %45 YONTEM ARTEFAKTI"
             if tekil_pay is not None and tekil_pay >= 0.90 else
             ("ETIKETLER GERCEKTEN BIRDEN COK GUZERGAH BIRAKIYOR"
              if coklu_pay is not None and coklu_pay > 0.10 else
              "ARADA — on kayitli iki dal da tutmadi, sayilar yazilir"))

    ozet = {"n": n, "gecilebilir_dagilimi": dict(sorted(dagilim.items())),
            "tekil_n": len(tekil), "tekil_pay": round(tekil_pay, 4) if tekil_pay else None,
            "coklu_n": len(coklu), "coklu_pay": round(coklu_pay, 4) if coklu_pay else None,
            "tekil_acik_seritle_uyusan": tekil_uyusan,
            "tekil_ayrisan": len(tekil) - tekil_uyusan,
            "hukum": hukum,
            "coklu_kareler": sorted(s["kare"] for s in coklu)[:40]}
    print(json.dumps({k: v for k, v in ozet.items() if k != "coklu_kareler"},
                     indent=1, ensure_ascii=False))
    print("HUKUM:", hukum)

    p = KOK / "results" / "t167" / "olcum.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"ozet": ozet, "kareler": satirlar}, indent=1,
                            ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p)


if __name__ == "__main__":
    main()
