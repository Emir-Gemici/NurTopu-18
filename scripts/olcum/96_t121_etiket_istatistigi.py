"""T121 adim 3 — ETIKET ISTATISTIGI: 4 secenegin ONCE/SONRA sinif piksel paylari.

NEDEN (mimar T121 emri): secenekler (a)-(d) uygulanmadan once her birinin
etiket dagilimina etkisi sayiyla bilinmeli. Bu betik EGITIM YAPMAZ; yalniz
etiket dosyalarini rasterize eder ve kahin maskeleriyle IZDUSUM hesaplar.

BOLUMLER:
  A (GPU yok) : dataset/copy_paste_gercek 448 etiketinin bugunku paylari
                (zemin tam-kare mi, engel/hedef paylari, zemin∧engel bindirmesi
                — manifest "zemin_alti_engeller": true'nun piksel karsiligi).
  B (GPU, kucuk): 56 kaynak karede aday_v5c zemin maskesi (secenek a kahini,
                conf=0.05 — manifest'in kendi degeri) ve v30 engel maskesi
                (secenek c kahin ADAYI, conf=0.05; kiremitte zayif oldugu
                95_t121_kahin_sondasi.json ile olculdu). Maskeler npz'e yazilir
                — adim 4 hazirligi ve gorsel dogrulama ayni maskeleri kullanir.
  C (GPU yok) : secenek bazinda SONRA paylari (izdusum):
                (a) zemin=kahin zemini · (b) zemin etiketi YOK (yalniz
                engel/hedef) · (c) zemin=tam-kare−catı, engel+=cati (v30
                vekiliyle; elle etiket adim 4'te) · (d) etiket degismez —
                karisim kutle tablosu ayrica 97'de.

Rasterizasyon 256x144'te yapilir (paylar olceksiz; dogrulama:
yolo_sinif_maskesi ayni poligonu geri rasterize eder — uretecin kendi
denetim fonksiyonu import edilir, yeniden yazilmaz).
CIKTI: results/t121/etiket_istatistigi.json + results/t121/kahin_maskeleri.npz
"""
from __future__ import annotations

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

from copy_paste_augmentation import (  # noqa: E402
    yolo_sinif_maskesi, zemin_ve_mevcut_engel)

VERI = KOK / "dataset" / "copy_paste_gercek"
KARE_KOKU = KOK / "data" / "raw_frames"
CIKTI_JSON = KOK / "results" / "t121" / "etiket_istatistigi.json"
CIKTI_NPZ = KOK / "results" / "t121" / "kahin_maskeleri.npz"
W, H = 256, 144          # pay olcumu icin kucuk izgara (oran korunur)
ZEMIN, ENGEL, HEDEF = 0, 1, 2
TAM_KARE_SATIR_ONEKI = "0 0.000000 0.000000 1.000000"


def etiket_paylari(etiket_metni: str) -> dict:
    z = yolo_sinif_maskesi(etiket_metni, (H, W), ZEMIN)
    e = yolo_sinif_maskesi(etiket_metni, (H, W), ENGEL)
    h = yolo_sinif_maskesi(etiket_metni, (H, W), HEDEF)
    return {
        "zemin": float(z.mean()), "engel": float(e.mean()),
        "hedef": float(h.mean()),
        "zemin_ve_engel_bindirme": float((z & e).mean()),
        "tam_kare_zemin_satiri": etiket_metni.startswith(TAM_KARE_SATIR_ONEKI),
    }


def main() -> int:
    from ultralytics import YOLO

    # ── A: bugunku 448 etiket ────────────────────────────────────────────────
    etiketler = sorted(VERI.glob("labels/*/*.txt"))
    if not etiketler:
        print("etiket bulunamadi", file=sys.stderr)
        return 2
    once = [etiket_paylari(io.open(p, encoding="utf-8").read()) for p in etiketler]
    A = {
        "dosya_sayisi": len(etiketler),
        "tam_kare_zemin_sayisi": sum(o["tam_kare_zemin_satiri"] for o in once),
        "ort_zemin": round(float(np.mean([o["zemin"] for o in once])), 4),
        "ort_engel": round(float(np.mean([o["engel"] for o in once])), 4),
        "ort_hedef": round(float(np.mean([o["hedef"] for o in once])), 4),
        "ort_zemin_engel_bindirme": round(
            float(np.mean([o["zemin_ve_engel_bindirme"] for o in once])), 4),
    }

    # ── B: 56 kaynakta kahin maskeleri ──────────────────────────────────────
    manifest = json.load(io.open(VERI / "manifest.json", encoding="utf-8"))
    kaynaklar = sorted({o["kaynak"] for o in manifest["ornekler"] if o.get("cikti")})
    v5c = YOLO(str(KOK / "models" / "aday_v5c_m640.pt"), task="segment")
    v30 = YOLO(str(KOK / "models" / "navitas_seg_v30_best.pt"), task="segment")
    npz: dict[str, np.ndarray] = {}
    b_kayitlari = []
    for ad in kaynaklar:
        bgr = cv2.imread(str(KARE_KOKU / ad))
        if bgr is None:
            print(f"KARE OKUNAMADI: {ad}", file=sys.stderr)
            return 3
        z5c, _ = zemin_ve_mevcut_engel(v5c, bgr, 0.05)
        _, e30 = zemin_ve_mevcut_engel(v30, bgr, 0.05)
        kz = cv2.resize(z5c, (W, H), interpolation=cv2.INTER_NEAREST)
        ke = cv2.resize(e30, (W, H), interpolation=cv2.INTER_NEAREST)
        anahtar = ad.replace("/", "__").replace(".jpg", "")
        npz[anahtar + "__v5c_zemin"] = kz.astype(bool)
        npz[anahtar + "__v30_engel"] = ke.astype(bool)
        b_kayitlari.append({
            "kaynak": ad,
            "v5c_zemin_payi": round(float(kz.mean()), 4),
            "v30_engel_payi": round(float(ke.mean()), 4),
            "kesisim_v5czemin_v30engel": round(float((kz.astype(bool) & ke.astype(bool)).mean()), 4),
        })
    np.savez_compressed(CIKTI_NPZ, **npz)

    v5c_ort = float(np.mean([b["v5c_zemin_payi"] for b in b_kayitlari]))
    v30_ort = float(np.mean([b["v30_engel_payi"] for b in b_kayitlari]))

    # ── C: secenek izdusumleri (448 kompozite, kaynak maskesi vekaletiyle) ──
    C = {
        "ONCE_bugunku": {"zemin": A["ort_zemin"], "engel": A["ort_engel"],
                          "etiketsiz": round(1 - A["ort_zemin"], 4),
                          "not": "zemin tam-kare: engel/hedef ZEMIN ETIKETININ ALTINDA da etiketli (bindirme A'da)"},
        "a_kahin_zeminine_daralt": {
            "zemin": round(v5c_ort, 4),
            "etiketsiz": round(1 - v5c_ort, 4),
            "not": "zemin=aday_v5c(conf 0.05) maskesi; engel/hedef degismez. "
                   "Kahin zayifligi: acik_oluklu catida 0.50 sizinti "
                   "(95_t121_kahin_sondasi.json)"},
        "b_zemin_etiketi_yok": {
            "zemin": 0.0, "etiketsiz": 1.0,
            "not": "zemin satiri hic yazilmaz; yalniz engel/hedef kalir. "
                   "Gercek-doku ZEMIN denetimi tamamen kaybolur (D-12/D-18 riski). "
                   "'Etiketsiz=negatif mi' sorusu ultralytics kaynagindan ayrica raporlanir."},
        "c_cati_sinif1": {
            "zemin": round(A["ort_zemin"] - v30_ort, 4),
            "engel_eki": round(v30_ort, 4),
            "not": "v30 vekiliyle izdusum (kiremitte 0.53 — EKSIK sayim); "
                   "elle etiket olcumu adim 4'te"},
        "d_karisim_orani": {
            "not": "etiket degismez; kutle tablosu 97_t121_karisim_kutlesi.py"},
    }

    sonuc = {"A_bugunku_448": A, "B_kaynak_kahinleri": b_kayitlari,
             "B_ozet": {"v5c_zemin_ort": round(v5c_ort, 4),
                         "v30_engel_ort": round(v30_ort, 4)},
             "C_secenek_izdusumleri": C}
    CIKTI_JSON.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI_JSON, "w", encoding="utf-8").write(
        json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(json.dumps({"A": A, "B_ozet": sonuc["B_ozet"]}, ensure_ascii=False, indent=1))
    print(f"yazildi: {CIKTI_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
