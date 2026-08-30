"""D-279..D-282 icin ham artefaktlardan bagimsiz, salt-okunur sayim.

Yalniz denetim ciktilarini ``results/codex_denetim`` altina yazar.
"""
from __future__ import annotations

import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[2]
CIKTI = Path(__file__).resolve().parent


def oku(yol: Path):
    return json.loads(yol.read_text(encoding="utf-8"))


def d279_say() -> dict:
    gruplar = {}
    tum = []
    for grup in "ABC":
        yol = KOK / "results" / "dji_20260822" / "f4" / grup / "rapor.json"
        veri = oku(yol)
        kareler = veri["kareler"]
        sureler = [k.get("saniye") for k in kareler]
        olculen = [float(s) for s in sureler if s is not None]
        tum.extend(sureler)
        gruplar[grup] = {
            "kare": len(kareler),
            "olculen": len(olculen),
            "null": sum(s is None for s in sureler),
            "hesaplanan_toplam_saniye": round(sum(olculen), 3),
            "rapordaki_toplam_saniye": veri.get("toplam_saniye"),
        }
    olculen = [float(s) for s in tum if s is not None]
    toplam = sum(olculen)
    return {
        "gruplar": gruplar,
        "toplam_kare": len(tum),
        "olculen": len(olculen),
        "null": sum(s is None for s in tum),
        "toplam_saniye": round(toplam, 3),
        "min_saniye": min(olculen),
        "medyan_saniye": float(np.median(olculen)),
        "maks_saniye": max(olculen),
        "olculen_kare_basina_saniye": toplam / len(olculen),
        "olculen_kare_saat": 3600.0 / (toplam / len(olculen)),
        "null_sifir_varsayilirsa_kare_basina_saniye": toplam / len(tum),
        "null_sifir_varsayilirsa_kare_saat": 3600.0 / (toplam / len(tum)),
        "null_notu": "Null, sifir sure degil eksik olcumdur; sifir senaryosu yalniz karsi-olgusaldir.",
    }


def tek_model(veri: dict) -> dict:
    modeller = veri["modeller"]
    assert len(modeller) == 1, list(modeller)
    return next(iter(modeller.values()))


def d280_say() -> dict:
    kabul = oku(KOK / "scripts" / "olcum" / "results" / "t63" /
                "dji_kirsal_v1_kabul_verdikt.json")
    aday = tek_model(oku(KOK / "results" / "dji_kirsal" / "bakir_0038.json"))
    tabanlar = oku(KOK / "results" / "dji_kirsal" / "bakir_0038_taban.json")["modeller"]
    v35 = tabanlar["navitas_seg_v35_best.pt"]
    aday_kare = {k["kare"]: (k["olceksiz_sebep"] or "ROTA")
                 for k in aday["kareler"]}
    v35_kare = {k["kare"]: (k["olceksiz_sebep"] or "ROTA")
                for k in v35["kareler"]}
    gecis = Counter((v35_kare[k], aday_kare[k]) for k in aday_kare)

    satirlar = {}
    with (KOK / "codes" / "runs" / "segment" / "dji_kirsal_v1" /
          "results.csv").open(encoding="utf-8-sig", newline="") as fh:
        for satir in csv.DictReader(fh):
            temiz = {k.strip(): v.strip() for k, v in satir.items()}
            ep = int(float(temiz["epoch"]))
            satirlar[ep] = temiz
    m5095 = "metrics/mAP50-95(M)"
    m50 = "metrics/mAP50(M)"
    en_5095 = max(satirlar, key=lambda e: float(satirlar[e][m5095]))
    en_50 = max(satirlar, key=lambda e: float(satirlar[e][m50]))

    kiyas = {}
    for satir in (KOK / "results" / "dji_kirsal" / "kiyas_109.txt").read_text(
            encoding="utf-8").splitlines():
        if satir.startswith("t127_temiz ") or satir.startswith("dji_kirsal_v1 "):
            ad, govde = satir.split(" ", 1)
            kiyas[ad] = json.loads(govde)
    figur_oran = (kiyas["dji_kirsal_v1"]["figur_zemin_orani"] /
                  kiyas["t127_temiz"]["figur_zemin_orani"])

    return {
        "kabul": {
            "verdikt": kabul["verdikt"],
            "gecti": kabul["gecti"],
            "K0_figur_tuval": kabul["olcum"]["K0"]["figur"],
            "K0_uretim_tabanina_oran": kabul["olcum"]["K0"].get("figur_orani"),
            "K1": kabul["olcum"]["K1_rota"],
            "K2": kabul["olcum"]["K2_basma"],
            "K3": kabul["olcum"]["K3_agir"],
            "K4": kabul["olcum"]["K4_arena_disi"],
            "K5_durum": kabul["olcum"]["K5_durum"],
            "K5_olculebilir": kabul["olcum"]["K5_olculebilir_kare"],
            "K5_kesen": kabul["olcum"]["K5_kesen_kare"],
        },
        "bakir": {
            "aday": {k: aday[k] for k in
                     ("n", "rota_olceksiz", "sebep_olceksiz")},
            "v35": {k: v35[k] for k in
                   ("n", "rota_olceksiz", "sebep_olceksiz")},
            "v35ten_adaya_gecis": {
                f"{eski} -> {yeni}": n for (eski, yeni), n in sorted(gecis.items())
            },
            "v35_MASKE_YOK_iken_adayda_maske_var": sum(
                v35_kare[k] == "MASKE_YOK" and aday_kare[k] != "MASKE_YOK"
                for k in aday_kare),
            "bu_karelerden_ROTA_olan": sum(
                v35_kare[k] == "MASKE_YOK" and aday_kare[k] == "ROTA"
                for k in aday_kare),
            "adayda_MASKE_YOKa_gerileyen": sum(
                v35_kare[k] != "MASKE_YOK" and aday_kare[k] == "MASKE_YOK"
                for k in aday_kare),
        },
        "csv": {
            "satir": len(satirlar),
            "mAP50_95_M_en_iyi_epoch": en_5095,
            "mAP50_95_M_en_iyi": float(satirlar[en_5095][m5095]),
            "mAP50_M_en_iyi_epoch": en_50,
            "mAP50_M_en_iyi": float(satirlar[en_50][m50]),
            "epoch1_mAP50_M": float(satirlar[1][m50]),
            "epoch10_mAP50_M": float(satirlar[10][m50]),
            "epoch16_mAP50_M": float(satirlar[16][m50]),
            "epoch1_mAP50_95_M": float(satirlar[1][m5095]),
        },
        "kiyas_109": {
            "v35_figur_zemin": kiyas["t127_temiz"]["figur_zemin_orani"],
            "dji_figur_zemin": kiyas["dji_kirsal_v1"]["figur_zemin_orani"],
            "dji_bolu_v35": figur_oran,
            "v35_kaplama67_icerik_medyan": kiyas["t127_temiz"]["kaplama67_icerik_medyan"],
            "dji_kaplama67_icerik_medyan": kiyas["dji_kirsal_v1"]["kaplama67_icerik_medyan"],
        },
    }


def d281_say() -> dict:
    m4 = oku(KOK / "results" / "dji_kirsal" / "curut_hat" /
             "m4_kural_kaldirilirsa.json")
    kareler = m4["kareler"] if isinstance(m4, dict) else m4
    kazanan = [k["kare"] for k in kareler
               if k.get("kural_var_yol") is None and k.get("kural_yok_yol") is not None]
    parcali = [k for k in kareler if k.get("durum_ustabasi") == "PARCALILIK"]
    parcali_kopuk = [k["kare"] for k in parcali
                     if k.get("kural_yok_sebep") == "GORUS_HATTI_KOPUK"]

    kontrol = oku(KOK / "results" / "dji_kirsal" / "curut_ucus" /
                  "kontrol_kuculme.json")
    acilar = []
    for aci, gen, yuk, donuk, yalniz_kucuk in kontrol:
        dg = int(donuk.get("GECER", 0))
        kg = int(yalniz_kucuk.get("GECER", 0))
        acilar.append({"aci": aci, "genislik": gen, "yukseklik": yuk,
                       "donuk_gecer": dg, "kontrol_gecer": kg,
                       "fark": dg - kg})
    return {
        "m4_n": len(kareler),
        "kural_kalkinca_rota_kazanan": len(kazanan),
        "kazananlar": kazanan,
        "parcalilik": len(parcali),
        "parcalilik_kural_yokken_kopuk": len(parcali_kopuk),
        "acilar": acilar,
        "kayitta_secili_acilar": [a for a in acilar if a["aci"] in (10, 30, 40, 90, 120, 160)],
    }


def d282_say() -> dict:
    etki = oku(KOK / "results" / "dji_kirsal" / "bant_tamamlama_etkisi.json")
    once = Counter(etki["once"].values())
    sonra = Counter(etki["sonra"].values())

    taban_kok = KOK / "results" / "dji_20260822" / "f5_olcek"
    yeni_kok = KOK / "results" / "dji_kirsal" / "bant_tamamlama"
    tabanlar = {p.name: p for p in taban_kok.glob("*/*_uc.png")}
    yeniler = sorted(yeni_kok.glob("*/*_uc.png"))
    eksik, boyut_farki = [], []
    korunan_fark = eklenen = ek_s0 = ek_s1 = 0
    for yeni_yol in yeniler:
        eski_yol = tabanlar.get(yeni_yol.name)
        if eski_yol is None:
            eksik.append(yeni_yol.name)
            continue
        m0 = cv2.imread(str(eski_yol), cv2.IMREAD_GRAYSCALE)
        m1 = cv2.imread(str(yeni_yol), cv2.IMREAD_GRAYSCALE)
        if m0 is None or m1 is None or m0.shape != m1.shape:
            boyut_farki.append(yeni_yol.name)
            continue
        korunan_fark += int(np.count_nonzero((m0 != 0) & (m1 != m0)))
        yeni_px = (m0 == 0) & (m1 != 0)
        eklenen += int(np.count_nonzero(yeni_px))
        ek_s0 += int(np.count_nonzero(yeni_px & (m1 == 1)))
        ek_s1 += int(np.count_nonzero(yeni_px & (m1 == 2)))

    # 138'in kendi saf olcumunu aynen kullan; gercek girdiye yazilmaz.
    modul_yolu = KOK / "scripts" / "olcum" / "138_kare_uygunluk_denetimi.py"
    spec = importlib.util.spec_from_file_location("d138_denetim", modul_yolu)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ref_olcum = []
    for p in sorted((KOK / "data" / "raw_frames").rglob("*.jpg"))[:400]:
        im = cv2.imread(str(p))
        if im is not None:
            ref_olcum.append(mod.olcutler(im))
    kes = sorted(o["keskinlik"] for o in ref_olcum)
    kes_alt = kes[max(0, len(kes) // 20)]

    ilk_ad = sorted(tabanlar)[0]
    govde = ilk_ad[:-len("_uc.png")]
    kaynak, stem = govde.split("__", 1)
    kare_yolu = KOK / "results" / "dji_20260822" / "kareler_1fps" / kaynak / (stem + ".jpg")
    ham = cv2.imread(str(kare_yolu))
    assert ham is not None, kare_yolu
    temel = cv2.resize(ham, (960, 540), interpolation=cv2.INTER_AREA)
    bulanik = cv2.GaussianBlur(temel, (101, 101), 25)
    gok = temel.copy()
    gok[:int(np.ceil(gok.shape[0] * 0.08)), :] = 230
    rng = np.random.default_rng(282)
    karanlik = np.clip(temel.astype(np.float32) * 0.03 +
                       rng.normal(12.0, 8.0, temel.shape), 3, 60).astype(np.uint8)

    mutasyonlar = {}
    for ad, im in (("temel", temel), ("bulanik", bulanik),
                   ("gok", gok), ("karanlik_gurultulu", karanlik)):
        o = mod.olcutler(im)
        # Denetlenen betiğin güncel saf karar fonksiyonunu çağır.  D-282
        # sonrasında eklenen KARANLIK/GURULTULU kapılarını burada kopyalayıp
        # yeniden ıraksama yaratma.
        bayrak = mod.bayraklar(o, kes_alt)
        mutasyonlar[ad] = {**o, "bayrak": bayrak}
        cv2.imwrite(str(CIKTI / "d282" / f"mutasyon_{ad}.png"), im)

    return {
        "etki": {
            "n_once": len(etki["once"]),
            "n_sonra": len(etki["sonra"]),
            "once": dict(once),
            "sonra": dict(sonra),
            "kazanan_sayisi": len(etki["kazanan"]),
            "kazanan": etki["kazanan"],
            "kaybeden_sayisi": len(etki["kaybeden"]),
            "kaybeden": etki["kaybeden"],
        },
        "maske_korunumu": {
            "yeni_maske": len(yeniler),
            "eski_maske_eksik": eksik,
            "boyut_okuma_sorunu": boyut_farki,
            "m0_nonzero_iken_degisen": korunan_fark,
            "eklenen_toplam": eklenen,
            "eklenen_sinif0": ek_s0,
            "eklenen_sinif1": ek_s1,
        },
        "uygunluk_mutasyonlari": {
            "kaynak": str(kare_yolu),
            "keskinlik_alt": kes_alt,
            "kirpik_ust": 0.20,
            "gok_ust": 0.05,
            "sonuclar": mutasyonlar,
        },
    }


def main() -> int:
    (CIKTI / "d282").mkdir(parents=True, exist_ok=True)
    sonuc = {
        "d279": d279_say(),
        "d280": d280_say(),
        "d281": d281_say(),
        "d282": d282_say(),
    }
    yol = CIKTI / "bagimsiz_sayim.json"
    yol.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    print(f"yazildi: {yol}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
