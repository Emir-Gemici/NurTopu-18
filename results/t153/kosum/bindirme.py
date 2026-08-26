"""T153 bindirme: en iyi / en kotu 5 kare (ACIK vs KAPALI) — results/t153/bindirme/<model>_<iyi|kotu>_<i>_<kare>.jpg

Ust: kare (960x540). Alt: model zemin YESIL, dedektor maskesi MOR, GT sinif1 KIRMIZI kenar,
rota KAPALI CAMGOBEGI, rota ACIK SARI. Cikarim uretim yolu (ACIK: get_masks ince_beton_serit=True).
Secim analiz.json'dan: iyi = yanlis->yol_ustunde, yanlis->rota_yok; kotu = mesru rota kaybi,
yol_ustunde->yanlis, yeni FP, sonra dedektor pikseli en cok olan TP kareler.
Kullanim: bindirme.py <model> [kare_govdesi ...]
"""
import io
import json
import sys
from pathlib import Path

import cv2
import numpy as np

WT = Path(r"O:\navitas\.claude\worktrees\wf_2d1c9d5e-54f-1")
sys.path.insert(0, str(WT / "codes"))
from rpi_inference import _preprocess, _maskeleri_icerige_kirp, get_masks, INFER_SIZE  # noqa: E402
from karar_sozlesmesi import ince_beton_serit_maskesi  # noqa: E402
from ultralytics import YOLO  # noqa: E402

ANA = Path(r"O:\navitas")
T153 = WT / "results" / "t153"
V3 = ANA / "dataset" / "dji_kirsal_0038_bolum_v3" / "images"
UZ = ANA / "results" / "gece_20260826" / "t152_uzlasi"
AGIRLIK = {
    "v35": ANA / "models" / "navitas_seg_v35_best.pt",
    "v3": ANA / "codes" / "runs" / "segment" / "gece_v3_v35taban" / "weights" / "best.pt",
    "v6": ANA / "codes" / "runs" / "segment" / "gece_v6_v35taban" / "weights" / "best.pt",
}
W, H = 960, 540


def kare_yolu(ad):
    for b in ("test", "val"):
        p = V3 / b / ad
        if p.is_file():
            return p
    raise FileNotFoundError(ad)


def wps_126(ad, model, kip):
    for b in ("test29", "val82"):
        p = T153 / "olcum" / f"t153_{kip}_{model}_{b}_test29.json"
        if not p.is_file():
            continue
        v = list(json.load(io.open(p, encoding="utf-8"))["modeller"].values())[0]
        for s in v["kareler"]:
            if s["kare"] == ad:
                return s.get("olceksiz_wps") or [], s["olceksiz_sebep"]
    return [], None


def secim(model):
    A = json.load(io.open(T153 / "analiz.json", encoding="utf-8"))["modeller"][model]
    g = A["bolum"]["111"]["gecis"]
    iyi = g["yanlis->yol_ustunde"] + g["yanlis->rota_yok"]
    # yanlis kalan ama engel ustundeki waypoint sayisi AZALAN kareler (kismi etki)
    for b in ("test29", "val82"):
        K, A_ = A["bolum"][b]["kapali_kareler"], A["bolum"][b]["acik_kareler"]
        for ad, s in K.items():
            t = A_[ad]
            if s["yanlis"] and t["yanlis"] and (t["engel_wp"] or 0) < (s["engel_wp"] or 0) and ad not in iyi:
                iyi.append(ad)
    if len(iyi) < 5:   # dedektorun en cok piksel yazdigi (hala) YANLIS kareler — etkisiz kalanlar
        adaylar = []
        for b in ("test29", "val82"):
            for ad, s in A["bolum"][b]["acik_kareler"].items():
                if s["rota"] and s["yanlis"] and ad not in iyi:
                    _sq, small, _ic = _preprocess(cv2.imread(str(kare_yolu(ad))))
                    m = ince_beton_serit_maskesi(small)
                    adaylar.append((int(m.sum()) if m is not None else 0, ad))
        for _n, ad in sorted(adaylar, reverse=True):
            if len(iyi) >= 5:
                break
            iyi.append(ad)
    kotu = g["mesru_rota_kaybi"] + g["yol_ustunde->yanlis"] + g["yeni_FP"]
    kotu = list(dict.fromkeys(kotu))
    if len(kotu) < 5:
        # dedektorun en cok piksel yazdigi TP (yol ustunde) kareler — "en riskli"
        adaylar = []
        for b in ("test29", "val82"):
            for ad, s in A["bolum"][b]["acik_kareler"].items():
                if s["rota"] and s["tavan"] and ad not in kotu:
                    img = cv2.imread(str(kare_yolu(ad)))
                    _sq, small, _ic = _preprocess(img)
                    m = ince_beton_serit_maskesi(small)
                    adaylar.append((int(m.sum()) if m is not None else 0, ad))
        for _n, ad in sorted(adaylar, reverse=True):
            if len(kotu) >= 5:
                break
            kotu.append(ad)
    return iyi[:5], kotu[:5]


def ciz(model, yolo, ad, etiket, cikti):
    img = cv2.imread(str(kare_yolu(ad)))
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    son = yolo.predict(small, imgsz=INFER_SIZE, conf=0.30, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(son, h, w, ince_beton_serit=True), icerik)
    x0, y0, cw, ch = icerik
    ded = ince_beton_serit_maskesi(small)
    ded = cv2.resize(ded, (w, h), interpolation=cv2.INTER_NEAREST)
    ded[:y0, :] = 0; ded[y0 + ch:, :] = 0; ded[:, :x0] = 0; ded[:, x0 + cw:] = 0

    def kes(m):
        return cv2.resize(m[y0:y0 + ch, x0:x0 + cw].astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    zem, ded960 = kes(mk[0] > 0), kes(ded)
    kucuk = cv2.resize(img, (W, H), interpolation=cv2.INTER_AREA)
    ov = kucuk.copy()
    ov[zem] = (0, 200, 0)
    ov[ded960] = (255, 0, 255)
    bind = cv2.addWeighted(kucuk, 0.5, ov, 0.5, 0)
    govde = ad[:-4]
    uc = UZ / f"{govde}_uc.png"
    if uc.is_file():
        u = np.squeeze(cv2.imread(str(uc), cv2.IMREAD_GRAYSCALE))
        kont, _ = cv2.findContours((u == 2).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.drawContours(bind, kont, -1, (0, 0, 255), 1)
    sx, sy = W / cw, H / ch

    def rota(wps, renk, kal):
        pts = [(int((x - x0) * sx), int((y - y0) * sy)) for x, y in wps]
        for i in range(len(pts) - 1):
            cv2.line(bind, pts[i], pts[i + 1], renk, kal)
        for p in pts:
            cv2.circle(bind, p, 4, renk, -1)
    wk, sk = wps_126(ad, model, "kapali")
    wa, sa = wps_126(ad, model, "acik")
    rota(wk, (255, 255, 0), 2)
    rota(wa, (0, 255, 255), 2)
    cv2.putText(bind, f"{model} {etiket} {govde[-16:]} | KAPALI: {'ROTA' if sk is None else sk} (camgobegi) | ACIK: {'ROTA' if sa is None else sa} (sari) | dedektor {int(ded960.sum())} px (mor)",
                (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)
    cv2.imwrite(str(cikti), np.vstack([kucuk, bind]))


def main():
    model = sys.argv[1]
    cik = T153 / "bindirme"
    cik.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2:
        iyi, kotu = [], sys.argv[2:]
    else:
        iyi, kotu = secim(model)
    print("iyi:", iyi); print("kotu:", kotu)
    yolo = YOLO(str(AGIRLIK[model]), task="segment")
    for etiket, liste in (("iyi", iyi), ("kotu", kotu)):
        for i, ad in enumerate(liste, 1):
            ciz(model, yolo, ad, etiket, cik / f"{model}_{etiket}_{i}_{ad[:-4]}.jpg")
    json.dump({"iyi": iyi, "kotu": kotu}, io.open(cik / f"{model}_secim.json", "w", encoding="utf-8"), indent=1)
    print("yazildi:", cik)


if __name__ == "__main__":
    main()
