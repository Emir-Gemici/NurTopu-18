"""176 — SINIF BAZLI KARISIKLIK MATRISI (Y-3.3.4-M02 / Y-4-M08 · gece 7 Eylul 2026 · ON_KAYIT G3).

FDR §3.3.4.2 ve §4.8.4'te "OLCULEMEDI: sinif bazli karisiklik matrisi" yaziyordu.
Uretim yolu vardi (`65_kabul_denetcisi.py` yer gercegi maskeleriyle calisir) ama
matris cikarimi yazilmamisti. Bu betik o bosluğu OLCUMLE kapatir:

  (1) PIKSEL DUZEYI 3x3 matris — DOGRULAMA kumesi test29 (CONTRACTS §12, kor
      etiket uzlasisi v3) uzerinde, URETIM ALGI YOLUYLA (`rpi_inference._preprocess`
      -> `model.predict(conf=CONF, imgsz=INFER_SIZE)` -> `get_masks` ->
      `_maskeleri_icerige_kirp`; 65_kabul_denetcisi.kaplama() ile AYNI zincir).
      Satir = tahmin {zemin, engel, YOK}, sutun = yer gercegi {zemin, engel, ETIKETSIZ}.
      🔴 ETIKETSIZ AYRI SUTUNDUR, ENGELE KATILMAZ (D-315 / §4.8.4'un itirazi:
      etiket kapsami eksikligi model hatasi gibi gosterilmez). Bu yuzden IoU iki
      paydayla verilir: `etiketli` (etiketsiz sutun FP sayilmaz) ve `tum` (sayilir).
  (2) ORNEK DUZEYI (nesne) matris — `ultralytics` `model.val(...)` yan urunu;
      ayni CONF, ayni imgsz, CPU. Ultralytics'in KENDI on islemesiyle kosar
      (isik normalizasyonu YOK, rect letterbox) — uretim yolu DEGILDIR, ek kanittir.

KURALLAR
  * GPU KULLANILMAZ: device='cpu' ve CUDA_VISIBLE_DEVICES bos (gece GPU surucusu
    BSOD uretiyor; ON_KAYIT G3). 29 kare CPU'da dakikalar surer, sorun degil.
  * CIPLAK SABIT YOK: CONF `65_kabul_denetcisi.CONF`'tan, imgsz `rpi_inference.INFER_SIZE`
    (kayit defterinden), sinif idleri `sinif_semasi`'den, model `model_registry.resolve_model`.
  * ONCELIK KURALI (etiket VE tahmin icin AYNI): bir piksel hem zemin hem engel ise
    ENGEL sayilir — uretimin `serbest = zemin AND NOT engel` semantigi (madde 15).
    Etiket uzlasisi (sinif 0 = A∧B, sinif 1 = A∨B) cakisan piksel URETEBILIR; sayisi
    JSON'da (`cakisan_etiket_px`) raporlanir, gizlenmez.
  * SINIR: bu kume DOGRULAMA kumesidir (kirsal yol, 0038), ARENA DEGILDIR; "farkli
    isik/golge" sorusunu kapatmaz (o kesit bu kumede yok).

Kullanim:
  venv\\Scripts\\python.exe scripts/olcum/176_piksel_karisiklik_matrisi.py
  venv\\Scripts\\python.exe scripts/olcum/176_piksel_karisiklik_matrisi.py --ornek-duzeyi-atla
"""
from __future__ import annotations

import os

# GPU YASAK — torch import edilmeden ONCE, ortam degiskeniyle (fail-safe).
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import argparse  # noqa: E402
import datetime as _dt  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
from pathlib import Path  # noqa: E402

import cv2  # noqa: E402
import numpy as np  # noqa: E402

KOK = Path(__file__).resolve().parents[2]
for _y in (KOK / "codes", KOK / "scripts" / "olcum"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import rpi_inference as ri  # noqa: E402
from model_registry import resolve_model  # noqa: E402
from sinif_semasi import ENGEL, IKI_SINIF_ADLARI, ZEMIN  # noqa: E402

DEVICE = "cpu"
KUME_KOKU = KOK / "dataset" / "dji_kirsal_0038_bolum_v3"
KARE_DIZIN = KUME_KOKU / "images" / "test"
ETIKET_DIZIN = KUME_KOKU / "labels" / "test"
YAML = KOK / "dataset" / "test29_v3.yaml"
CIKTI = KOK / "results" / "gece_20260907" / "karisiklik"
JSON_ADI = "piksel_karisiklik_test29.json"

# Uc durum eksenleri — satir (tahmin) ve sutun (yer gercegi) sirasi SABIT ve JSON'a yazilir.
TAHMIN_EKSENI = ("zemin", "engel", "yok")
GERCEK_EKSENI = ("zemin", "engel", "etiketsiz")
I_ZEMIN, I_ENGEL, I_UCUNCU = 0, 1, 2


def _kabul_denetcisi():
    """CONF'u 65_kabul_denetcisi'nden OKU (kopyalama)."""
    yol = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
    spec = importlib.util.spec_from_file_location("kabul_denetcisi_65", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def kume_parmak_izi(kok: Path) -> dict:
    """65_kabul_denetcisi.kume_parmak_izi ile ayni yontem: sorted(rglob) ad+boyut."""
    dosyalar = sorted(p for p in kok.rglob("*") if p.is_file())
    h = hashlib.sha256()
    for p in dosyalar:
        h.update(p.relative_to(kok).as_posix().encode("utf-8"))
        h.update(str(p.stat().st_size).encode("ascii"))
    return {"n": len(dosyalar), "ozet": f"sha256:{h.hexdigest()}",
            "yontem": "sorted(rglob) uzerinden ad+boyut; icerik OKUNMAZ"}


def etiket_maskeleri(txt: Path, h: int, w: int):
    """YOLO poligon etiketini (h, w) rasterine cevir. Donus: (zemin, engel, istatistik)."""
    zemin = np.zeros((h, w), np.uint8)
    engel = np.zeros((h, w), np.uint8)
    n_poli = {ZEMIN: 0, ENGEL: 0}
    bilinmeyen = 0
    if txt.is_file():
        for satir in txt.read_text(encoding="utf-8").splitlines():
            v = satir.split()
            if len(v) < 7:          # sinif + en az 3 nokta
                continue
            sinif = int(v[0])
            koord = np.array([float(x) for x in v[1:]], np.float64).reshape(-1, 2)
            pts = np.rint(koord * [w, h]).astype(np.int32).reshape(-1, 1, 2)
            if sinif == ZEMIN:
                cv2.fillPoly(zemin, [pts], 1)
            elif sinif == ENGEL:
                cv2.fillPoly(engel, [pts], 1)
            else:
                bilinmeyen += 1
                continue
            n_poli[sinif] += 1
    cakisan = int(np.count_nonzero(zemin & engel))
    return zemin, engel, {"poligon_zemin": n_poli[ZEMIN], "poligon_engel": n_poli[ENGEL],
                          "poligon_bilinmeyen_sinif": bilinmeyen, "cakisan_etiket_px": cakisan}


def uc_durum(zemin: np.ndarray, engel: np.ndarray) -> np.ndarray:
    """Iki ikili maskeden tek uc-durum haritasi: 0 zemin, 1 engel, 2 ucuncu (yok/etiketsiz).
    ONCELIK: engel > zemin (serbest = zemin AND NOT engel)."""
    u = np.full(zemin.shape, I_UCUNCU, np.uint8)
    u[zemin > 0] = I_ZEMIN
    u[engel > 0] = I_ENGEL
    return u


def karisiklik(tahmin: np.ndarray, gercek: np.ndarray) -> np.ndarray:
    """3x3 sayim: satir = tahmin, sutun = gercek."""
    idx = tahmin.astype(np.int64) * 3 + gercek.astype(np.int64)
    return np.bincount(idx.ravel(), minlength=9).reshape(3, 3)


def _oran(pay: int, payda: int):
    return (float(pay) / float(payda)) if payda > 0 else None


def iou_hesapla(M: np.ndarray) -> dict:
    """Sinif IoU'lari iki paydayla.
    tum      : FP = satirin diger IKI sutunu (etiketsiz DAHIL)      -> klasik piksel IoU
    etiketli : FP = satirin yalniz DIGER ETIKETLI sutunu (etiketsiz FP SAYILMAZ)
    FN her ikisinde ayni: sutunun diger iki satiri."""
    out = {}
    for ad, c in (("zemin", I_ZEMIN), ("engel", I_ENGEL)):
        tp = int(M[c, c])
        fn = int(M[:, c].sum() - tp)
        fp_tum = int(M[c, :].sum() - tp)
        fp_etk = int(M[c, :I_UCUNCU].sum() - tp)
        out[ad] = {
            "tp": tp, "fn": fn, "fp_tum": fp_tum, "fp_etiketli": fp_etk,
            "iou_tum": _oran(tp, tp + fp_tum + fn),
            "iou_etiketli": _oran(tp, tp + fp_etk + fn),
        }
    etiketli = int(M[:, :I_UCUNCU].sum())
    out["piksel_dogrulugu_etiketli"] = _oran(int(M[I_ZEMIN, I_ZEMIN] + M[I_ENGEL, I_ENGEL]), etiketli)
    return out


def _matris_sozlugu(M: np.ndarray) -> dict:
    return {
        "satir_ekseni_tahmin": list(TAHMIN_EKSENI),
        "sutun_ekseni_gercek": list(GERCEK_EKSENI),
        "matris": [[int(x) for x in satir] for satir in M],
        "toplam_px": int(M.sum()),
        "satir_toplam": [int(x) for x in M.sum(axis=1)],
        "sutun_toplam": [int(x) for x in M.sum(axis=0)],
        "sutun_normalize": [[_oran(int(M[r, c]), int(M[:, c].sum())) for c in range(3)] for r in range(3)],
        "satir_normalize": [[_oran(int(M[r, c]), int(M[r, :].sum())) for c in range(3)] for r in range(3)],
        **iou_hesapla(M),
    }


def ham_model_maskeleri(sonuc, yan: int) -> dict:
    """YALNIZ MODEL maskeleri (T67 ince bariyer katmani ve T153 OLMADAN).
    `rpi_inference.get_masks` ile ayni esik (>0.5) ve ayni yeniden boyutlama;
    get_masks'in kendisi katman 2'yi HER ZAMAN OR'ladigi icin burada ayrilir.
    Amac: uretim matrisinin ne kadari modelden, ne kadari T67'den — raporda ayri satir."""
    masks = {ZEMIN: np.zeros((yan, yan), np.uint8), ENGEL: np.zeros((yan, yan), np.uint8)}
    r = sonuc[0]
    if r.masks is not None:
        for i, cls in enumerate(r.boxes.cls):
            c = int(cls)
            if c not in masks:
                continue
            m = r.masks.data[i].cpu().numpy()
            m_up = cv2.resize(m, (yan, yan))
            masks[c] = np.maximum(masks[c], (m_up > 0.5).astype(np.uint8))
    return masks


def kare_olc(model, kare: Path, conf: float) -> dict:
    img = cv2.imread(str(kare))
    if img is None:
        raise RuntimeError(f"kare okunamadi: {kare}")
    h, w = img.shape[:2]
    gz, ge, ist = etiket_maskeleri(ETIKET_DIZIN / (kare.stem + ".txt"), h, w)
    gercek = uc_durum(gz, ge)

    sq, small, icerik = ri._preprocess(img)
    yan = sq.shape[0]
    sonuc = model.predict(small, imgsz=ri.INFER_SIZE, conf=conf, device=DEVICE, verbose=False)
    x0, y0, cw, ch = icerik
    assert (cw, ch) == (w, h), (icerik, w, h)

    # (a) URETIM YOLU: get_masks (model + T67 katman 2) -> icerige kirp -> icerik dikdortgeni
    uretim = ri._maskeleri_icerige_kirp(ri.get_masks(sonuc, yan, yan), icerik)
    pz = uretim[ZEMIN][y0:y0 + h, x0:x0 + w]
    pe = uretim[ENGEL][y0:y0 + h, x0:x0 + w]
    tahmin = uc_durum(pz, pe)
    M = karisiklik(tahmin, gercek)

    # (b) YALNIZ MODEL (T67'siz) — ayni kirpma
    ham = ri._maskeleri_icerige_kirp(ham_model_maskeleri(sonuc, yan), icerik)
    hz = ham[ZEMIN][y0:y0 + h, x0:x0 + w]
    he = ham[ENGEL][y0:y0 + h, x0:x0 + w]
    M_ham = karisiklik(uc_durum(hz, he), gercek)
    # Madde 15 denetimi: katman 2 engeli yalniz BUYUTUR, zemine dokunmaz.
    t67_ek = int(np.count_nonzero((pe > 0) & (he == 0)))
    assert not np.any((he > 0) & (pe == 0)), "T67 engel KUCULTTU — madde 15 ihlali"
    assert np.array_equal(hz, pz), "get_masks zemin maskesini degistirdi — beklenmiyor"

    n_tespit = int(len(sonuc[0].boxes)) if sonuc[0].boxes is not None else 0
    return {
        "kare": kare.name, "h": h, "w": w, "px": int(h * w),
        "tespit_sayisi": n_tespit,
        **ist,
        "etiketsiz_orani": _oran(int((gercek == I_UCUNCU).sum()), h * w),
        "t67_ek_engel_px": t67_ek,
        "uretim": _matris_sozlugu(M),
        "yalniz_model": _matris_sozlugu(M_ham),
    }


def ornek_duzeyi(agirlik: Path, conf: float, cikti: Path) -> dict:
    """ultralytics val: nesne (ornek) duzeyi matris. CPU, ayni CONF, ayni imgsz."""
    from ultralytics import YOLO
    from ultralytics.utils.metrics import ConfusionMatrix

    if not YAML.is_file():
        raise RuntimeError(f"yaml yok: {YAML}")
    proje = cikti / "ultralytics_val"
    model = YOLO(str(agirlik))
    metrics = model.val(data=str(YAML), device=DEVICE, imgsz=ri.INFER_SIZE, conf=conf,
                        plots=True, project=str(proje), name="test29_v36_cpu",
                        exist_ok=True, verbose=False, workers=0, batch=8)
    cm = getattr(metrics, "confusion_matrix", None)
    if cm is None:
        raise RuntimeError("ultralytics metrics.confusion_matrix yok")
    matris = np.asarray(cm.matrix)
    adlar = list(getattr(cm, "names", {}).values()) if isinstance(getattr(cm, "names", None), dict) \
        else [IKI_SINIF_ADLARI[ZEMIN], IKI_SINIF_ADLARI[ENGEL]]
    iou_thres = inspect.signature(ConfusionMatrix.process_batch).parameters["iou_thres"].default
    kayit_dizini = Path(metrics.save_dir) if getattr(metrics, "save_dir", None) else proje / "test29_v36_cpu"

    # Olcum olmayan buyuk yiginlar (val_batch*.jpg: ornek gorseller) depoya girmesin.
    silinen = []
    for p in sorted(kayit_dizini.glob("val_batch*.jpg")):
        silinen.append(p.name)
        p.unlink()
    # ultralytics'in etiket onbellegi izlenen dizine yazilir — kalinti birakma.
    for onbellek in (ETIKET_DIZIN.parent / "test.cache",):
        if onbellek.is_file():
            onbellek.unlink()

    sonuc_sozlugu = {k: float(v) for k, v in dict(metrics.results_dict).items()}
    return {
        "_ne": "ultralytics model.val yan urunu — ORNEK (nesne) duzeyi; satir = tahmin, sutun = yer gercegi; "
               "son satir/sutun = arka plan (FN satiri / FP sutunu). Ultralytics ON ISLEMESIYLE kosar "
               "(rect letterbox, isik normalizasyonu YOK) — uretim yolu DEGILDIR, ek kanittir.",
        "conf": conf, "iou_thres_kutu_eslesme": float(iou_thres),
        "iou_thres_kaynak": "ultralytics.utils.metrics.ConfusionMatrix.process_batch varsayilani (inspect ile okundu)",
        "imgsz": int(ri.INFER_SIZE), "device": DEVICE,
        "sinif_adlari": adlar + ["arka_plan"],
        "matris": [[int(x) for x in satir] for satir in matris],
        "satir_toplam": [int(x) for x in matris.sum(axis=1)],
        "sutun_toplam": [int(x) for x in matris.sum(axis=0)],
        "results_dict": sonuc_sozlugu,
        "kayit_dizini": kayit_dizini.relative_to(KOK).as_posix(),
        "silinen_gorsel_yiginlari": silinen,
        "yaml": YAML.relative_to(KOK).as_posix(),
    }


def ciz(M: np.ndarray, iou: dict, meta: dict, yol: Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sutun_norm = M / np.maximum(M.sum(axis=0, keepdims=True), 1)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
    for ax, veri, baslik, fmt in (
        (axes[0], M, "piksel sayisi", "{:,}"),
        (axes[1], sutun_norm, "sutun normalize (yer gercegi sutunu = 1,00)", "{:.3f}"),
    ):
        im = ax.imshow(veri, cmap="Blues")
        ax.set_xticks(range(3)); ax.set_xticklabels(GERCEK_EKSENI)
        ax.set_yticks(range(3)); ax.set_yticklabels(TAHMIN_EKSENI)
        ax.set_xlabel("yer gercegi (test29, kor uzlasi v3)")
        ax.set_ylabel("tahmin (uretim yolu, v36, CPU)")
        ax.set_title(baslik)
        esik = veri.max() / 2
        for r in range(3):
            for c in range(3):
                ax.text(c, r, fmt.format(veri[r, c]), ha="center", va="center",
                        color="white" if veri[r, c] > esik else "black", fontsize=10)
        fig.colorbar(im, ax=ax, fraction=0.046)
    fig.suptitle(
        f"Sinif bazli piksel karisiklik matrisi — {meta['model_id']} · CONF {meta['conf']:.2f} · "
        f"imgsz {meta['imgsz']} · {meta['n_kare']} kare · "
        f"IoU zemin {iou['zemin']['iou_etiketli']:.3f} / engel {iou['engel']['iou_etiketli']:.3f} (etiketli payda)",
        fontsize=10)
    fig.tight_layout()
    fig.savefig(yol, dpi=150)
    plt.close(fig)


def _f(x, basamak=4):
    return "OLCULEMEDI" if x is None else f"{x:.{basamak}f}"


def md_yaz(veri: dict, yol: Path):
    T = veri["toplam"]["uretim"]
    H = veri["toplam"]["yalniz_model"]
    s = []
    s.append("# Sinif bazli karisiklik matrisi — test29 DOGRULAMA kumesi (v36, CPU)\n")
    s.append(f"- tarih: {veri['tarih']}  ·  komut: `{veri['komut']}`")
    s.append(f"- model: `{veri['model']['path']}` · sha256 `{veri['model']['sha256_defter']}` · "
             f"CONF {veri['conf']} (`{veri['conf_kaynak']}`) · imgsz {veri['imgsz']} · device {veri['device']}")
    s.append(f"- kume: `{veri['kume']['kare_dizin']}` ({veri['kume']['n_kare']} kare, "
             f"{veri['kume']['cozunurluk']}) · etiket `{veri['kume']['etiket_dizin']}` · "
             f"parmak izi {veri['kume']['parmak_izi_etiket']['ozet']}")
    s.append(f"- SINIR: {veri['sinirlar'][0]}\n")
    s.append("## Piksel duzeyi — URETIM YOLU (get_masks: model + T67 katman 2)\n")
    s.append("| tahmin \\ yer gercegi | zemin | engel | ETIKETSIZ | satir toplam |")
    s.append("|---|---:|---:|---:|---:|")
    for r, ad in enumerate(TAHMIN_EKSENI):
        s.append(f"| {ad} | " + " | ".join(f"{T['matris'][r][c]:,}" for c in range(3)) + f" | {T['satir_toplam'][r]:,} |")
    s.append("| sutun toplam | " + " | ".join(f"{x:,}" for x in T["sutun_toplam"]) + f" | {T['toplam_px']:,} |")
    s.append("")
    s.append("| olcut | zemin | engel |")
    s.append("|---|---:|---:|")
    s.append(f"| IoU (etiketli payda; etiketsiz FP sayilmaz) | {_f(T['zemin']['iou_etiketli'])} | {_f(T['engel']['iou_etiketli'])} |")
    s.append(f"| IoU (tum payda; etiketsiz FP sayilir) | {_f(T['zemin']['iou_tum'])} | {_f(T['engel']['iou_tum'])} |")
    s.append(f"| sutun normalize kosegen (yer gercegi icinde dogru pay) | {_f(T['sutun_normalize'][0][0])} | {_f(T['sutun_normalize'][1][1])} |")
    s.append(f"\n- etiketli piksel dogrulugu: {_f(T['piksel_dogrulugu_etiketli'])} · "
             f"etiketsiz payi: {_f(veri['toplam']['etiketsiz_orani'])} · "
             f"cakisan etiket px (engel > zemin oncelikli): {veri['toplam']['cakisan_etiket_px']:,}")
    s.append(f"- T67 ince bariyer katmaninin ek engel pikseli: {veri['toplam']['t67_ek_engel_px']:,} "
             f"({veri['toplam']['t67_etkilenen_kare']} karede) · yalniz-model IoU: zemin {_f(H['zemin']['iou_etiketli'])} / engel {_f(H['engel']['iou_etiketli'])} (etiketli payda)\n")
    o = veri.get("ornek_duzeyi")
    if o:
        s.append("## Ornek (nesne) duzeyi — ultralytics val (CPU, ayni CONF/imgsz; uretim on islemesi DEGIL)\n")
        adlar = o["sinif_adlari"]
        s.append("| tahmin \\ yer gercegi | " + " | ".join(adlar) + " |")
        s.append("|---|" + "---:|" * len(adlar))
        for r, ad in enumerate(adlar):
            s.append(f"| {ad} | " + " | ".join(str(x) for x in o["matris"][r]) + " |")
        rd = o["results_dict"]
        s.append("\n- results_dict: " + ", ".join(f"{k} {v:.4f}" for k, v in rd.items()))
        s.append(f"- kayit: `{o['kayit_dizini']}` (confusion_matrix.png, confusion_matrix_normalized.png)\n")
    else:
        s.append("## Ornek duzeyi: KOSULMADI (--ornek-duzeyi-atla)\n")
    s.append("## Kare bazli (uretim yolu)\n")
    s.append("| kare | tespit | etiketsiz | z→z | z→e | z→∅ | e→z | e→e | e→∅ | ∅→z | ∅→e | ∅→∅ | IoU z (etk) | IoU e (etk) | T67 px |")
    s.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in veri["kareler"]:
        m = k["uretim"]["matris"]
        duz = [m[r][c] for r in range(3) for c in range(3)]
        s.append(f"| {k['kare']} | {k['tespit_sayisi']} | {_f(k['etiketsiz_orani'], 3)} | " +
                 " | ".join(f"{x:,}" for x in duz) +
                 f" | {_f(k['uretim']['zemin']['iou_etiketli'], 3)} | {_f(k['uretim']['engel']['iou_etiketli'], 3)} | {k['t67_ek_engel_px']:,} |")
    s.append("\nHucre gosterimi: tahmin→gercek (z zemin, e engel, ∅ yok/etiketsiz).")
    yol.write_text("\n".join(s) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cikti", default=str(CIKTI))
    ap.add_argument("--ornek-duzeyi-atla", action="store_true",
                    help="ultralytics val (ornek duzeyi) kosulmasin")
    a = ap.parse_args(argv)
    cikti = Path(a.cikti)
    cikti.mkdir(parents=True, exist_ok=True)

    kd = _kabul_denetcisi()
    conf = float(kd.CONF)
    agirlik, spec = resolve_model()           # verify=True: sha256 DISKTE dogrulanir
    sha_disk = _sha256(agirlik)
    if sha_disk != spec["sha256"]:
        raise RuntimeError("defter/disk sha256 uyusmuyor")

    kareler = sorted(KARE_DIZIN.glob("*.jpg"))
    if not kareler:
        raise RuntimeError(f"kare yok: {KARE_DIZIN}")
    etiketler = sorted(ETIKET_DIZIN.glob("*.txt"))
    if {p.stem for p in kareler} != {p.stem for p in etiketler}:
        raise RuntimeError("kare/etiket govde adlari birebir eslesmiyor")

    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=KOK, capture_output=True,
                                text=True, check=True).stdout.strip()
    except Exception:  # noqa: BLE001
        commit = "OLCULEMEDI"

    import torch
    import ultralytics
    from ultralytics import YOLO
    model = YOLO(str(agirlik))

    t0 = _dt.datetime.now()
    sonuclar = []
    for i, kare in enumerate(kareler, 1):
        r = kare_olc(model, kare, conf)
        sonuclar.append(r)
        print(f"[{i:2d}/{len(kareler)}] {kare.name} tespit={r['tespit_sayisi']} "
              f"IoU z={_f(r['uretim']['zemin']['iou_etiketli'], 3)} e={_f(r['uretim']['engel']['iou_etiketli'], 3)} "
              f"etiketsiz={_f(r['etiketsiz_orani'], 3)} t67+={r['t67_ek_engel_px']}", flush=True)
    sure_piksel = (_dt.datetime.now() - t0).total_seconds()

    M = np.zeros((3, 3), np.int64)
    Mh = np.zeros((3, 3), np.int64)
    for r in sonuclar:
        M += np.asarray(r["uretim"]["matris"], np.int64)
        Mh += np.asarray(r["yalniz_model"]["matris"], np.int64)
    toplam_px = int(sum(r["px"] for r in sonuclar))
    assert int(M.sum()) == toplam_px == int(Mh.sum())

    cozunurlukler = sorted({f"{r['w']}x{r['h']}" for r in sonuclar})
    toplam = {
        "n_kare": len(sonuclar), "toplam_px": toplam_px,
        "uretim": _matris_sozlugu(M), "yalniz_model": _matris_sozlugu(Mh),
        "etiketsiz_orani": _oran(int(M[:, I_UCUNCU].sum()), toplam_px),
        "cakisan_etiket_px": int(sum(r["cakisan_etiket_px"] for r in sonuclar)),
        "poligon_zemin": int(sum(r["poligon_zemin"] for r in sonuclar)),
        "poligon_engel": int(sum(r["poligon_engel"] for r in sonuclar)),
        "t67_ek_engel_px": int(sum(r["t67_ek_engel_px"] for r in sonuclar)),
        "t67_etkilenen_kare": int(sum(1 for r in sonuclar if r["t67_ek_engel_px"] > 0)),
        "sure_s": round(sure_piksel, 1),
    }

    ornek = None
    if not a.ornek_duzeyi_atla:
        t1 = _dt.datetime.now()
        ornek = ornek_duzeyi(agirlik, conf, cikti)
        ornek["sure_s"] = round((_dt.datetime.now() - t1).total_seconds(), 1)

    veri = {
        "_ne": "Y-3.3.4-M02 / Y-4-M08 sinif bazli karisiklik matrisi — DOGRULAMA kumesi test29 "
               "(CONTRACTS §12), piksel duzeyi (uretim yolu) + ornek duzeyi (ultralytics val). "
               "ON_KAYIT: results/gece_20260907/ON_KAYIT.md G3.",
        "tarih": _dt.datetime.now().isoformat(timespec="seconds"),
        "komut": " ".join([Path(sys.executable).as_posix(),
                           Path(__file__).resolve().relative_to(KOK).as_posix(), *sys.argv[1:]]),
        "git_commit": commit,
        "makine": {"platform": platform.platform(), "python": sys.version.split()[0],
                   "torch": torch.__version__, "ultralytics": ultralytics.__version__,
                   "opencv": cv2.__version__, "numpy": np.__version__,
                   "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "<yok>"),
                   "torch_cuda_kullanildi": False},
        "model": {"model_id": spec["model_id"], "profile": spec["profile"],
                  "path": Path(spec["path"]).as_posix(), "sha256_defter": spec["sha256"],
                  "sha256_disk": sha_disk, "imgsz_defter": int(spec["imgsz"]),
                  "kaynak": "config/model_registry.json -> profiles[default_profile] (model_registry.resolve_model, verify=True)"},
        "conf": conf, "conf_kaynak": "scripts/olcum/65_kabul_denetcisi.py:CONF (importlib ile okundu)",
        "imgsz": int(ri.INFER_SIZE), "imgsz_kaynak": "codes/rpi_inference.INFER_SIZE (kayit defterinden turetilir)",
        "device": DEVICE,
        "kume": {"kare_dizin": KARE_DIZIN.relative_to(KOK).as_posix(),
                 "etiket_dizin": ETIKET_DIZIN.relative_to(KOK).as_posix(),
                 "n_kare": len(kareler), "cozunurluk": ", ".join(cozunurlukler),
                 "parmak_izi_kare": kume_parmak_izi(KARE_DIZIN),
                 "parmak_izi_etiket": kume_parmak_izi(ETIKET_DIZIN),
                 "sozlesme": "CONTRACTS §12 — DOGRULAMA kumesi, kor etiket uzlasisi v3 (sinif 0 = A∧B, sinif 1 = A∨B)"},
        "sinif_sozlesmesi": {"zemin_id": int(ZEMIN), "engel_id": int(ENGEL),
                             "adlar": {str(k): v for k, v in IKI_SINIF_ADLARI.items()},
                             "kaynak": "codes/sinif_semasi.py (CONTRACTS §1.1)"},
        "yontem": {
            "tahmin": "rpi_inference._preprocess -> model.predict(conf, imgsz, cpu) -> get_masks (model + T67 ince bariyer; "
                      "T153 varsayilan KAPALI) -> _maskeleri_icerige_kirp -> icerik dikdortgeni (orijinal cozunurluk)",
            "yer_gercegi": "YOLO poligon -> cv2.fillPoly, orijinal cozunurluk; etiketsiz piksel UCUNCU sutun (engele KATILMAZ)",
            "oncelik": "hem etiket hem tahmin icin ENGEL > ZEMIN (serbest = zemin AND NOT engel; madde 15)",
            "iou_tum": "TP / (TP + FP_tum + FN); FP_tum = satirin diger iki sutunu (etiketsiz dahil)",
            "iou_etiketli": "TP / (TP + FP_etiketli + FN); FP_etiketli = satirin yalniz diger ETIKETLI sutunu",
        },
        "toplam": toplam,
        "kareler": sonuclar,
        "ornek_duzeyi": ornek,
        "sinirlar": [
            "Bu kume DOGRULAMA kumesidir (0038 kirsal yol; CONTRACTS §12) — ARENA DEGILDIR; kirmizi H, moloz yigini, "
            "fiziki bariyer icermez. Arena basarimi IDDIA EDILMEZ.",
            "Farkli isik acisi / golge kesiti bu kumede YOKTUR — o satir OLCULEMEDI kalir.",
            "Etiketsiz sutun 'model hatasi' DEGILDIR: etiket kapsami eksikligi (D-315) ayri sutunda gorunur; "
            "yorumda IoU'nun etiketli paydali sekli esas alinir, tum paydali sekil yaninda verilir.",
            "Ornek duzeyi matris ultralytics on islemesiyle kosar (isik normalizasyonu yok, rect letterbox) — uretim yolu degildir.",
        ],
    }

    json_yolu = cikti / JSON_ADI
    json_yolu.write_text(json.dumps(veri, indent=1, ensure_ascii=False), encoding="utf-8")
    md_yaz(veri, cikti / "piksel_karisiklik_test29.md")
    ciz(M, toplam["uretim"], {"model_id": spec["model_id"], "conf": conf, "imgsz": int(ri.INFER_SIZE),
                              "n_kare": len(sonuclar)}, cikti / "piksel_karisiklik_test29.png")
    T = toplam["uretim"]
    print(json.dumps({"n_kare": len(sonuclar), "toplam_px": toplam_px,
                      "matris": T["matris"],
                      "iou_zemin_etiketli": T["zemin"]["iou_etiketli"], "iou_engel_etiketli": T["engel"]["iou_etiketli"],
                      "iou_zemin_tum": T["zemin"]["iou_tum"], "iou_engel_tum": T["engel"]["iou_tum"],
                      "json": json_yolu.relative_to(KOK).as_posix()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
