"""T122 — DORT/BES MODELIN TEK TABLODA KIYASI (on kayittaki olcutlerle).

ON KAYIT: results/t122_on_kayit.md (D-107). Bu betik OLCUT KOYMAZ, on kayitta
yazili olanlari uygular ve sonuclari tek tabloda toplar. Esik yorumu yoktur;
"cati dondu mu" gibi ikili kararlar on kaydin metnindeki kuralla hesaplanir.

OLCULENLER (her model icin, hepsi AYNI zincir):
  1. CATI KACAGI (55 kare, TAM MASKE) — yer gercegi: T121 elle+homografi
     cati maskeleri. `108_t122_kahin_kiyasi` ile AYNI olcut.
  2. CATI DISKLERI (6 kare) — T121 on kaydinin karar kurali burada tanimli:
     engel >= 0,50 VE zemin <= 0,30.
  3. 67 KARE KAPLAMA — IKI PAYDAYLA (ICERIK: karar_sozlesmesi zinciri /
     LETTERBOX: 65 denetcisi tanimi) + zemin_maskesi_reddi sayisi.
  4. FIGUR (K0 girdisi) — figur zemin orani + ⚠ v34 ILE ORTUSME (IoU):
     D-229 olctu ki K0 sinyali bu figurde iki modeli ayni bolge uzerinden
     kiyaslamayabiliyor; ortusme sutunu o kararsizligi gorunur kilar.
CIKTI: results/t122/kiyas.json + kiyas.md (mimara sunulacak tablo)
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
for p in (KOK / "scripts", KOK / "codes"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from karar_sozlesmesi import zemin_kaplamasi, zemin_maskesi_reddi  # noqa: E402
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)
from ultralytics import YOLO  # noqa: E402

CATI_KOK = KOK / "results" / "t121" / "cati_maskeleri"
DISKLER = KOK / "results" / "t121" / "diskler.json"
KARE_KOK = KOK / "data" / "raw_frames"
FIGUR = KOK / "data" / "arena_referans" / "sartname_s9_arena.png"
CIKTI = KOK / "results" / "t122"
CONF = 0.30
RUNS = KOK / "codes" / "runs" / "segment"

VARSAYILAN = [
    ("v30", KOK / "models" / "navitas_seg_v30_best.pt"),
    ("v34_URETIM", KOK / "models" / "navitas_seg_v34_best.pt"),
    ("t121_ft_(c)", RUNS / "t121_etiket_ft" / "weights" / "best.pt"),
    ("t122a_(a)", RUNS / "t122a_daralt" / "weights" / "best.pt"),
    ("t122ac_(a+c)", RUNS / "t122ac_daralt_cati" / "weights" / "best.pt"),
    # T127: TEMIZ bolumle egitilmis ayni recete (D-233 duzeltmesi sonrasi).
    ("t127_temiz", RUNS / "t127_temiz" / "weights" / "best.pt"),
    # 2026-08-25: DJI kirsal veriyle egitilen aday (D-107 on kayitli tur).
    ("dji_kirsal_v1", RUNS / "dji_kirsal_v1" / "weights" / "best.pt"),
]


def cati_kareleri():
    cikti = []
    for cp in sorted(CATI_KOK.glob("*.png")):
        ham = cv2.imread(str(cp), 0)
        m = (ham[:, :, 0] if ham.ndim == 3 else ham) > 127
        if m.any():
            video, kare = cp.stem.split("__")
            cikti.append((f"{video}/{kare}.jpg", m))
    return cikti


def disk_kurali(engel_ort: float, zemin_ort: float) -> bool:
    """T121/T122 on kaydinin karar kurali — DEGISMEZ."""
    return bool(engel_ort >= 0.50 and zemin_ort <= 0.30)


def model_olc(model, catilar, diskler, kareler67, figur_bgr) -> dict:
    # 1) tam maske cati kacagi
    kacaklar = []
    for ad, cati in catilar:
        z, _ = zemin_ve_mevcut_engel(model, kareler67[ad], CONF)
        kacaklar.append(float((z.astype(bool) & cati).sum() / max(1, cati.sum())))
    # 2) diskler
    ce, cz, zz = [], [], []
    for ad, k in diskler.items():
        z, e = zemin_ve_mevcut_engel(model, kareler67[ad], CONF)
        for x, y, r in k["cati"]:
            dm = np.zeros(z.shape, np.uint8)
            cv2.circle(dm, (x, y), r, 1, -1)
            dm = dm.astype(bool)
            ce.append(float(e[dm].mean()))
            cz.append(float(z[dm].mean()))
        for x, y, r in k["zemin"]:
            dm = np.zeros(z.shape, np.uint8)
            cv2.circle(dm, (x, y), r, 1, -1)
            zz.append(float(z[dm.astype(bool)].mean()))
    # 3) 67 kare kaplama
    icerik_p, tuval_p, red = [], [], 0
    for ad, bgr in kareler67.items():
        sq, small, icerik = _preprocess(bgr)
        h, w = sq.shape[:2]
        s = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
        mk = _maskeleri_icerige_kirp(get_masks(s, h, w), icerik)
        trav = (mk[0] > 0).astype(np.uint8)
        icerik_p.append(float(zemin_kaplamasi(trav, icerik)))
        tuval_p.append(float(trav.mean()))
        red += zemin_maskesi_reddi(trav, icerik) is not None
    # 4) figur
    zf, ef = zemin_ve_mevcut_engel(model, figur_bgr, CONF)
    return {
        "cati_kacak_ort": round(float(np.mean(kacaklar)), 4),
        "cati_kacak_medyan": round(float(np.median(kacaklar)), 4),
        "disk_cati_engel": round(float(np.mean(ce)), 4),
        "disk_cati_zemin": round(float(np.mean(cz)), 4),
        "disk_zemin_zemin": round(float(np.mean(zz)), 4),
        "cati_dondu": disk_kurali(float(np.mean(ce)), float(np.mean(cz))),
        "kaplama67_icerik_medyan": round(float(np.median(icerik_p)), 4),
        "kaplama67_tuval_medyan": round(float(np.median(tuval_p)), 4),
        "zemin_maskesi_reddi": int(red),
        "figur_zemin_orani": round(float(zf.mean()), 5),
        "figur_engel_orani": round(float(ef.mean()), 5),
        "_figur_maske": zf.astype(bool),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--atla-eksik", action="store_true",
                    help="agirligi olmayan modeli ATLA (egitim bitmemisse)")
    args = ap.parse_args()

    catilar = cati_kareleri()
    diskler = json.load(io.open(DISKLER, encoding="utf-8"))["kareler"]
    gerekli = {ad for ad, _ in catilar} | set(diskler)
    kareler67 = {p.relative_to(KARE_KOK).as_posix(): cv2.imread(str(p))
                 for p in sorted(KARE_KOK.rglob("*.jpg"))}
    eksik = gerekli - set(kareler67)
    if eksik:
        print(f"EKSIK KARE: {sorted(eksik)[:3]}", file=sys.stderr)
        return 2
    figur = cv2.imread(str(FIGUR))

    sonuc, figur_maskeleri = {}, {}
    for ad, yol in VARSAYILAN:
        if not yol.is_file():
            if args.atla_eksik:
                print(f"ATLANDI (agirlik yok): {ad}", flush=True)
                continue
            print(f"AGIRLIK YOK: {yol}", file=sys.stderr)
            return 3
        model = YOLO(str(yol), task="segment")
        olcum = model_olc(model, catilar, diskler, kareler67, figur)
        del model
        figur_maskeleri[ad] = olcum.pop("_figur_maske")
        olcum["yol"] = str(yol)
        sonuc[ad] = olcum
        print(ad, json.dumps({k: v for k, v in olcum.items() if k != "yol"},
                             ensure_ascii=False), flush=True)

    # Figurde v34 ile ORTUSME (D-229: K0 sinyalinin kararliligi)
    if "v34_URETIM" in figur_maskeleri:
        taban = figur_maskeleri["v34_URETIM"]
        for ad, m in figur_maskeleri.items():
            birlesim = int((m | taban).sum())
            sonuc[ad]["figur_v34_ile_IoU"] = round(
                float((m & taban).sum() / birlesim) if birlesim else 0.0, 4)

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "kiyas.json", "w", encoding="utf-8").write(
        json.dumps({"conf": CONF, "n_cati_kare": len(catilar),
                    "n_kare67": len(kareler67), "modeller": sonuc},
                   ensure_ascii=False, indent=1))

    basliklar = [("cati_kacak_ort", "çatı kaçağı (55 kare)"),
                 ("disk_cati_engel", "disk çatı→engel"),
                 ("disk_cati_zemin", "disk çatı→zemin"),
                 ("cati_dondu", "ÇATI DÖNDÜ?"),
                 ("disk_zemin_zemin", "disk zemin→zemin"),
                 ("kaplama67_icerik_medyan", "kaplama İÇERİK"),
                 ("kaplama67_tuval_medyan", "kaplama TUVAL"),
                 ("zemin_maskesi_reddi", "67'de red"),
                 ("figur_zemin_orani", "figür zemin (K0)"),
                 ("figur_v34_ile_IoU", "figür v34-IoU ⚠")]
    satirlar = ["| ölçüt | " + " | ".join(sonuc) + " |",
                "|---|" + "---|" * len(sonuc)]
    for anahtar, baslik in basliklar:
        satirlar.append(f"| {baslik} | " + " | ".join(
            str(sonuc[m].get(anahtar, "-")) for m in sonuc) + " |")
    io.open(CIKTI / "kiyas.md", "w", encoding="utf-8").write(
        "# T122 · MODEL KIYASI (ön kayıt ölçütleriyle)\n\n"
        + "\n".join(satirlar) + "\n")
    print("\n".join(satirlar))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
