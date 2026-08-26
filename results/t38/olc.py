"""T38 olcumu (ON_KAYIT §23): kuru kosunun halka 7'si hangi karede MESRU gecebilir?

Uretim zinciri, kuru kosunun KENDI `halka_rota` cagrisiyla (kopya yok) uc kaynakta:
  a) otopark        : bugunku varsayilan (data/raw_frames ilk kare)
  b1) kabul_kumesi  : registry kabul_kumesi (DEPO DISI) — referans
  b2) depo_ici_arena: dataset/sentetik_arena/images/val — varsayilan adayi
"""
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
for y in (KOK / "scripts", KOK / "codes", KOK / "comms"):
    sys.path.insert(0, str(y))

import cv2  # noqa: E402

# Kuru kosunun SAHTE TELEMETRIDEN turettigi mpp (results/saha_zinciri_20260827/
# kosu_t160/ozet.json -> olcek.detay.mpp). Uydurulmaz, olculen degerdir.
KURU_KOSU_MPP = 0.03382911733532963
import rpi_inference as ri  # noqa: E402
import saha_kuru_kosu as sk  # noqa: E402

_MODEL = None


def kareler(kaynak, n=12):
    if kaynak == "otopark":
        ps = sorted(p for p in (KOK / "data" / "raw_frames").rglob("*")
                    if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        return ps[:1]
    if kaynak == "kabul_kumesi":
        defter = json.load(open(KOK / "config" / "model_registry.json", encoding="utf-8"))
        kok = Path(defter["profiles"]["competition"]["kabul_kumesi"])
        ps = (sorted((kok / "images" / "val").glob("*.jpg"))
              or sorted((kok / "images" / "train").glob("*.jpg"))
              or sorted((kok / "images").glob("*.jpg")))
    else:
        ps = sorted((KOK / "dataset" / "sentetik_arena" / "images" / "val").glob("*.jpg"))
    if not ps:
        return []
    adim = max(1, len(ps) // n)
    return ps[::adim][:n]


def kos(kaynak):
    global _MODEL
    if _MODEL is None:
        print("model yukleniyor...", flush=True)
        _MODEL = ri.load_model(kayit_zorunlu=False)
    ks = kareler(kaynak)
    print(f"  {kaynak}: {len(ks)} kare", flush=True)
    cikti = []
    for i, yol in enumerate(ks, 1):
        kare = cv2.imread(str(yol))
        if kare is None:
            print(f"    [{i}] {yol.name} OKUNAMADI", flush=True)
            continue
        sq, small, icerik = ri._preprocess(kare)
        sonuc = _MODEL.predict(small, imgsz=ri.INFER_SIZE, conf=0.25, verbose=False)
        maskeler = ri._maskeleri_icerige_kirp(
            ri.get_masks(sonuc, sq.shape[0], sq.shape[1]), icerik)
        rapor = sk.Rapor()
        durum, _s = sk.halka_rota(rapor, maskeler, icerik, sk.GECTI,
                                  mpp=KURU_KOSU_MPP)
        satir = next(s for s in rapor.satirlar if s["halka"] == "rota")
        kayit = {"kare": yol.name, "durum": durum,
                 "uretim_durum": satir["detay"].get("durum"),
                 "yol_no": satir["detay"].get("yol_no"),
                 "tanisal": satir["detay"].get("tanisal_rota_bul", {}).get("durum")}
        cikti.append(kayit)
        print(f"    [{i}/{len(ks)}] {yol.name[:38]:38s} {durum:6s} {kayit['uretim_durum']}",
              flush=True)
    return cikti


if __name__ == "__main__":
    rapor = {}
    for k in ("otopark", "kabul_kumesi", "depo_ici_arena"):
        r = kos(k)
        gecti = sum(1 for x in r if x["durum"] == sk.GECTI)
        rapor[k] = {"n": len(r), "GECTI": gecti, "kareler": r}
        print(f"{k:16s} GECTI {gecti}/{len(r)}", flush=True)
    p = KOK / "results" / "t38" / "olcum.json"
    p.write_text(json.dumps(rapor, indent=1, ensure_ascii=False), encoding="utf-8")
    print("yazildi:", p, flush=True)
