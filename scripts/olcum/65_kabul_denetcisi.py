"""D-107 KABUL DENETCISI — onceden yazilmis olcutleri MEKANIK olarak kosar.

Esikler `REVIEW_LOG.md` D-107'de sonuc GORULMEDEN yazildi ve burada CIPLAK
SABIT olarak degil, tek bir yerde tanimli olarak durur. Sabah tartisma olmasin
diye karar kurali da koda gomulu: her olcut GECTI/DUSTU doner ve nihai verdikt
AND birlesimidir.

Kullanim:
  venv\\Scripts\\python.exe 65_kabul_denetcisi.py --model <yol> [--ad v27]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

BURASI = Path(__file__).parent
FIGUR = REPO / "data" / "arena_referans" / "sartname_s9_arena.png"


def kabul_kumesi_yolu(kok=None):
    """KADRAJ'in TEK KAYNAGI: registry `profiles[default_profile].kabul_kumesi`.

    🔴 T125 (D-225 §5): eskiden `KADRAJ = BURASI / "calisma" / ...` idi —
    betigin KENDI KONUMUNDAN turetiliyordu. Ayna kopyasinda (scripts/olcum)
    o dizin YOK; denetci BOS kume uzerinden K1..K4'u "DUSTU" raporladi ve
    mimar az kalsin "model her kapida dustu" hukmu veriyordu. Registry'deki
    `_kabul_kumesi_notu` alanin neden orada durdugunu zaten anlatiyordu;
    denetci onu OKUMUYORDU ("iki kopya, biri zorlanmiyor" sinifi).

    Fail-closed: alan yoksa ya da gosterdigi dizin yoksa RuntimeError —
    bos kume uzerinden rapor URETILMEZ. CIPLAK YEDEK YOL YOKTUR (madde 16;
    S5/INFER_SIZE kalibinin sert cesidi: orada guvenli varsayilan vardi,
    burada yanlis kume "olculemeyeni DUSTU satmak" demektir).
    """
    taban = (Path(kok) if kok is not None else REPO) / "config" / "model_registry.json"
    try:
        veri = json.loads(taban.read_text(encoding="utf-8"))
        profil = veri["default_profile"]
        deger = veri["profiles"][profil]["kabul_kumesi"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"kabul_kumesi registry'den okunamadi ({taban}): {exc}") from exc
    yol = Path(deger)
    if not yol.is_dir():
        raise RuntimeError(
            f"kabul kumesi dizini yok: {yol} "
            f"(kaynak: {taban} -> profiles.{profil}.kabul_kumesi)")
    return yol


try:
    # 93_t106 gibi ithalatcilar modul niteligi olarak okur; registry saglamsa
    # iki kosum baglaminda da AYNI mutlak yoldur. Bozuksa None kalir ve
    # main() acik hatayla durur — sessiz "bos kume raporu" yolu kapali.
    KADRAJ = kabul_kumesi_yolu()
except RuntimeError as _exc:
    print(f"UYARI: {_exc}", file=sys.stderr)
    KADRAJ = None
CONF = 0.30

# ── D-107 esikleri · SONUC GORULMEDEN yazildi, sabah DEGISTIRILMEYECEK ──────
ESIK = {
    "K1_rota_min": 230,          # / 260   (v24: 196 · yer gercegi: 260)
    "K2_basma_maks": 0.15,       #         (v24: %31,1 · taban: %9,2)
    "K3_agir_maks": 0.03,        #         (v24: %20,4 · taban: %0)
    "K4_arena_disi_maks": 0.05,  #         (v24: %13,3)
}


# ── T110 · K0 GORUNURLUGU (karar D-186) ─────────────────────────────────────
# K0'in cezalandirdigi yon (AZ zemin gormek) GUVENLI yondur — fail-closed.
# Tehlikeli yonu (COK zemin gormek) K0 olcmez; onu K2/K3 olcer (n=258).
# Yani K0 bir EMNIYET degil YETENEK kapisidir ve `> 0` olcutu DEGISMEZ.
# Asil sorun 16 kat dususun SESSIZ gecmesiydi; cozum esik degil GORUNURLUK.
#
# ⚠ ORAN BLOKLAMAZ: `gecti["K0"]`a girmez, verdikt AND birlesimini
# degistirmez. Yalnizca RAPORLAR.
K0_ORAN_ALT = 0.5     # bunun altinda YETENEK uyarisi (fail-closed yon)
K0_ORAN_UST = 2.0     # bunun ustunde TEHLIKELI yon — K2/K3'e ayrica bakilir


def k0_taban_orani(figur_kaplama, kok=None):
    """Figur kaplamasinin URETIM TABANINA orani. -> (oran|None, taban|None, not).

    🔴 TABAN SAYIDAN OKUNUR, METINDEN AYIKLANMAZ. Kayit defterindeki
    `metrics.k0_korluk.olculen` bicimli bir metindir
    ('figur zemin %0,49 · raw bos 0/8 ...'); ondan sayi cikarmak D-180'in
    kusur sinifidir (orada `None` sessizce "DUSTU" olmustu). Bu yuzden
    defterde AYRI ve SAYISAL bir alan tutulur: `figur_zemin_orani`.

    ⚠ Alan YOKSA oran `None` doner ve durum RAPORLANIR — yokluk ne BASARI
    ne BASARISIZLIK sayilir (D-180 dersi).
    """
    taban_yolu = (Path(kok) if kok is not None else REPO) / "config" / "model_registry.json"
    try:
        veri = json.loads(taban_yolu.read_text(encoding="utf-8"))
        profil = veri["profiles"][veri["default_profile"]]
        taban = profil["metrics"]["k0_korluk"]["figur_zemin_orani"]
        taban = float(taban)
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return None, None, "taban kayitli DEGIL — oran hesaplanamadi"
    if not (taban > 0.0) or figur_kaplama is None:
        return None, taban, "taban 0 ya da figur olculemedi — oran hesaplanamadi"
    return float(figur_kaplama) / taban, taban, ""


def k5_durumu(kes):
    """K5'in UC DURUMU: GECTI / DUSTU / OLCULEMEDI (T105 · D-180).

    KUSUR: K5 alt betigin stdout'undan ayristiriliyor; satir basilmazsa
    `kes = None` kaliyordu ve `gecti[\"K5\"] = (kes == 0)` bunu DUSTU sayiyordu.
    `63_bariyer_kesisimi.py` TEK karede kosar; o karede rota cikmazsa kesisim
    OLCULEMEZ — bu \"rota bariyere BASTI\" demek DEGILDIR (yanlis atif).
    Olculdu (D-180): v22/v23/v30 UCU DE None'a dusuyordu; satir hicbir modeli
    ayirt etmiyordu.

    🔴 MIMARIN KISITI — DEGISTIRILEMEZ: OLCULEMEDI != GECTI.
    OLCULEMEDI terfiyi YINE BLOKLAR (fail-closed); yalnizca raporda DUSTU'den
    AYRI gorunur. \"Olculemeyeni gecir\" seklinde bir duzeltme KABUL EDILMEZ.
    """
    if kes is None:
        return "OLCULEMEDI"
    return "GECTI" if kes == 0 else "DUSTU"


def k5_gecti(kes):
    """Verdikt girdisi. YALNIZ 'GECTI' gecer — OLCULEMEDI de DUSTU de bloklar."""
    return k5_durumu(kes) == "GECTI"


def k0_gecti(figur, raw_bos, cp_bos):
    """K0 olcutu. DEGISMEDI (D-186): `figur > 0` VE hicbir kumede bos maske yok.

    🔴 ORAN BU FONKSIYONA PARAMETRE OLARAK BILE GIRMEZ. "Oran bloklamiyor"
    iddiasi boylece bir yorum degil, IMZANIN kendisidir: oranla cagrilamaz.
    """
    return (figur is not None and figur > 0.0
            and raw_bos == 0 and cp_bos == 0)


def k0_dikkat_satiri(oran):
    """Oran bandin disindaysa UYARI metni, degilse None. BLOKLAMAZ."""
    if oran is None or K0_ORAN_ALT <= oran <= K0_ORAN_UST:
        return None
    if oran > K0_ORAN_UST:
        yon = ("     > 2,0 ise TEHLIKELI yon (daha cok zemin) — "
               "K2/K3'e AYRICA bakin.")
    else:
        yon = ("     < 0,5 ise YETENEK uyarisi (daha az zemin) — "
               "fail-closed yon.")
    return (f"  🔴 DIKKAT: figur kaplamasi uretim tabanindan {oran:.2f} kat "
            f"sapiyor.\n{yon}")


def kaplama(model, p):
    img = cv2.imread(str(p))
    if img is None:
        return None
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    return float((mk[0] > 0).mean())


def k14_durumlari(d, esik=None):
    """K1..K4'un UC DURUMU (T125 · D-225 §5) — T105'in K5 kalibinin AYNISI.

    d: `61_rota_moloza_basma.py` JSON'u (dict) ya da None (alt betik cokmus /
    JSON yok). Kural: girdi yok ya da payda 0 -> OLCULEMEDI; olculdu ve esigin
    altinda -> DUSTU. 🔴 ESIKLER DEGISMEZ — degisen yalniz OLCULEMEYENIN
    raporlanisi. OLCULEMEDI != GECTI: verdikt icin YINE bloklar (k5_gecti
    kalibi); "olculemeyeni gecir" seklinde bir okuma KABUL EDILMEZ.
    """
    e = ESIK if esik is None else esik
    if not d or int(d.get("n", 0)) == 0:
        return ({k: "OLCULEMEDI" for k in ("K1", "K2", "K3", "K4")},
                {"n": int(d.get("n", 0)) if d else 0, "rota_uretilen": 0,
                 "basan": 0, "agir": 0, "arena_disi": 0})
    n = int(d.get("n", 0))
    r = int(d.get("rota_uretilen", 0))
    basan = int(d.get("basan", 0))
    agir = int(d.get("agir", 0))
    disi = int(d.get("arena_disi", 0))
    durum = {"K1": "GECTI" if r >= e["K1_rota_min"] else "DUSTU"}
    if r == 0:
        # Rota hic uretilmemis: K1 OLCULDU ve dustu; K2..K4'un paydasi yok.
        durum.update(K2="OLCULEMEDI", K3="OLCULEMEDI", K4="OLCULEMEDI")
    else:
        durum["K2"] = "GECTI" if basan / r <= e["K2_basma_maks"] else "DUSTU"
        durum["K3"] = "GECTI" if agir / r <= e["K3_agir_maks"] else "DUSTU"
        durum["K4"] = "GECTI" if disi / r <= e["K4_arena_disi_maks"] else "DUSTU"
    return durum, {"n": n, "rota_uretilen": r, "basan": basan,
                   "agir": agir, "arena_disi": disi}


def kos(betik, ek):
    """Alt betigi kosar; (stdout, basarili_mi) dondurur.

    🔴 T125: cikis kodu artik KONTROL EDILIR. Alt betik coktuyse bu
    OLCULEMEDI'dir — "0 rota uretti" DEGILDIR. Eski hali cikis kodunu
    yutuyordu ve cokme, dort kapinin "DUSTU"su olarak raporlaniyordu.
    """
    p = subprocess.run([sys.executable, "-B", str(BURASI / betik)] + ek,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if p.returncode != 0:
        kuyruk = (p.stderr or "").strip().splitlines()[-3:]
        print(f"  UYARI: {betik} exit={p.returncode} — ciktisi OLCULEMEDI "
              "sayilacak.", file=sys.stderr)
        for s in kuyruk:
            print(f"    {s}", file=sys.stderr)
        return p.stdout or "", False
    return p.stdout or "", True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--ad", default=None)
    ap.add_argument("--kok", type=Path, default=None,
                    help="registry koku (varsayilan REPO; T125 senaryo "
                         "testleri icin)")
    args = ap.parse_args()
    ad = args.ad or args.model.parent.parent.name

    # T125: girdi kumesi MODEL YUKLENMEDEN dogrulanir — kume yoksa denetci
    # ACIK HATAYLA durur; bos kume uzerinden verdikt URETILMEZ (D-225 §5).
    kume = kabul_kumesi_yolu(args.kok)

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    sonuc, gecti = {}, {}

    # ── K0 · KORLUK YOK (v25'in olum sebebi) ────────────────────────────────
    k0 = {}
    k0["figur"] = kaplama(model, FIGUR)
    for ad_k, kok, desen in (
            ("raw_frames", REPO / "data" / "raw_frames", "*.jpg"),
            ("copy_paste", REPO / "dataset" / "copy_paste_gercek" / "images" / "train", "*.jpg")):
        # 🔴 ORNEKLEME KALDIRILDI (T110 · D-186). Eskiden 8 kare orneklenirdi:
        #     raw_frames  67 -> 8  (%11,9)   ·   copy_paste  393 -> 8  (%2,0)
        # `bos == 0` olcutu DEGISMEDI; ayni olcut artik TAM KUMEDE uygulanir.
        # (`rglob` de iki kez cagriliyordu; tek cagriya indirildi.)
        yollar = sorted(kok.rglob(desen))
        oranlar = [kaplama(model, p) for p in yollar]
        oranlar = [o for o in oranlar if o is not None]
        k0[ad_k] = {"n": len(oranlar), "bos": sum(1 for o in oranlar if o <= 0.0),
                    "ort": float(np.mean(oranlar)) if oranlar else 0.0}
    gecti["K0"] = k0_gecti(k0["figur"], k0["raw_frames"]["bos"],
                           k0["copy_paste"]["bos"])
    sonuc["K0"] = k0

    # ── K1..K4 · rota / basma / arena disi ──────────────────────────────────
    jj = BURASI / "results" / "t63" / f"{ad}_kabul.json"
    jj.parent.mkdir(parents=True, exist_ok=True)
    jj.unlink(missing_ok=True)          # T125: BAYAT json yeniden okunmasin
    _, alt_ok = kos("61_rota_moloza_basma.py",
                    ["--model", str(args.model),
                     "--kume", str(kume), "--json", str(jj)])
    d = (json.loads(jj.read_text(encoding="utf-8"))
         if alt_ok and jj.is_file() else None)
    k14, sayilar = k14_durumlari(d)
    n, r = sayilar["n"], sayilar["rota_uretilen"]
    basan, agir, disi = sayilar["basan"], sayilar["agir"], sayilar["arena_disi"]
    sonuc["K1_rota"] = f"{r}/{n}"
    sonuc["K2_basma"] = f"{basan}/{r}" if r else "-"
    sonuc["K3_agir"] = f"{agir}/{r}" if r else "-"
    sonuc["K4_arena_disi"] = f"{disi}/{r}" if r else "-"
    sonuc["K14_durum"] = k14
    gecti["K1"] = k14["K1"] == "GECTI"
    gecti["K2"] = k14["K2"] == "GECTI"      # OLCULEMEDI de bloklar (T105 kalibi)
    gecti["K3"] = k14["K3"] == "GECTI"
    gecti["K4"] = k14["K4"] == "GECTI"

    # ── K5 · bariyer kesisimi ───────────────────────────────────────────────
    c, _k5_ok = kos("63_bariyer_kesisimi.py", ["--model", str(args.model)])
    kes = None
    for s in c.splitlines():
        if "ROTA x BARIYER kesisimi" in s:
            try:
                kes = int(s.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    sonuc["K5_bariyer_px"] = kes
    sonuc["K5_durum"] = k5_durumu(kes)          # GECTI / DUSTU / OLCULEMEDI
    gecti["K5"] = k5_gecti(kes)                 # OLCULEMEDI de bloklar

    # ── RAPOR ───────────────────────────────────────────────────────────────
    print(f"\n{'='*66}\nKABUL DENETIMI · {ad}\n  esikler: REVIEW_LOG D-107 "
          f"(sonuc gorulmeden yazildi)\n{'='*66}")
    f = sonuc["K0"]["figur"]
    oran, taban, oran_notu = k0_taban_orani(f)
    taban_metni = (f"uretim tabani %{100*taban:.2f} · oran {oran:.2f}"
                   if oran is not None else (oran_notu or "oran YOK"))
    print(f"  K0 KORLUK YOK        {'GECTI' if gecti['K0'] else 'DUSTU':<6} "
          f"figur zemin %{100*f:.2f} ({taban_metni})")
    print(f"{'':23s}raw bos {k0['raw_frames']['bos']}/{k0['raw_frames']['n']} "
          f"· cp bos {k0['copy_paste']['bos']}/{k0['copy_paste']['n']}")
    # ⚠ BLOKLAMAZ — `gecti` sozlugune DOKUNMAZ, yalniz basar (D-186).
    dikkat = k0_dikkat_satiri(oran)
    if dikkat:
        print(dikkat)
    sonuc["K0"]["figur_orani"] = oran
    sonuc["K0"]["figur_tabani"] = taban
    sonuc["K0"]["oran_notu"] = oran_notu
    print(f"  K1 ROTA >= {ESIK['K1_rota_min']}       {k14['K1']:<11} "
          f"{sonuc['K1_rota']}")
    print(f"  K2 BASMA <= %{100*ESIK['K2_basma_maks']:.0f}      {k14['K2']:<11} "
          f"{sonuc['K2_basma']}   (taban %9,2)")
    print(f"  K3 AGIR  <= %{100*ESIK['K3_agir_maks']:.0f}       {k14['K3']:<11} "
          f"{sonuc['K3_agir']}   (taban %0)")
    print(f"  K4 ARENA DISI <= %{100*ESIK['K4_arena_disi_maks']:.0f}  {k14['K4']:<11} "
          f"{sonuc['K4_arena_disi']}")
    if "OLCULEMEDI" in k14.values():
        print("     (girdi kumesi / alt betik sorunu: OLCULEMEDI — bu 'DUSTU'"
              " DEGILDIR ama terfi YINE bloklanir: OLCULEMEDI != GECTI."
              " T125 · D-225 §5.)")
    k5d = sonuc["K5_durum"]
    print(f"  K5 BARIYER = 0 px    {k5d:<11} "
          f"{('%d px' % kes) if kes is not None else 'kesisim OLCULEMEDI'}")
    if k5d == "OLCULEMEDI":
        print("     (63_bariyer_kesisimi TEK karede kosar; o karede rota"
              " cikmadiysa kesisim olculemez — bu 'basti' demek DEGILDIR."
              " Terfi YINE bloklanir: OLCULEMEDI != GECTI.)")
    print("-" * 66)
    if not gecti["K0"]:
        print("  VERDIKT: RED — K0 dustu. v25 ile AYNI sebep, tartisma yok.")
    elif all(gecti.values()):
        print("  VERDIKT: URETIME ALINIR — D-107'nin alti olcutu de saglandi.")
    else:
        durumlar = dict(sonuc.get("K14_durum", {}))
        durumlar["K5"] = sonuc.get("K5_durum")
        d_ = [(k + "(OLCULEMEDI)" if durumlar.get(k) == "OLCULEMEDI" else k)
              for k, v in gecti.items() if not v]
        print(f"  VERDIKT: URETIME ALINMAZ — dusen: {', '.join(d_)}")
        print("           kok nedene baglanip TEK duzeltme turu kosulur.")
    print("=" * 66)
    print("\n⚠ Bu olcumlerin tamami SENTETIKTIR. Hicbiri 'sahada calisir'")
    print("  anlamina gelmez (D-88 + D-99, kalici kisit).")

    cj = BURASI / "results" / "t63" / f"{ad}_kabul_verdikt.json"
    cj.parent.mkdir(parents=True, exist_ok=True)
    cj.write_text(json.dumps({"model": str(args.model), "esikler": ESIK,
                              "olcum": sonuc, "gecti": gecti,
                              "verdikt": all(gecti.values())},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\njson -> {cj}")


if __name__ == "__main__":
    main()
