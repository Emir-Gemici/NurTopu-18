"""ÇOK SINIFLI VERİ SETİ — RescueNet'in 11 sınıfını YOLO-seg formatına çevir.

NEDEN: şu an RescueNet'in 11 sınıfından yalnız 2'sini (road-clear=7, road-blocked=8)
kullanıp 9'unu ATIYORUZ. Özellikle Building-Total-Destruction(6) ve Tree(9) sınıfları
MOLOZU tarif ediyor — bizim 'blocked' sınıfımızın tanımı tam olarak bu. Model bu
sınıfları da öğrenirse yol/moloz ayrımı için daha zengin bir temsil kurabilir.

KULLANIM PLANI (iki aşamalı):
  1) 11 sınıflı veriyle ön-eğit (yardımcı görev — zengin temsil)
  2) 2 sınıfa (traversable/blocked) fine-tune → SON MODEL YİNE 2 SINIFLI
     => Segment head nc=2 olur, çıkarım maliyeti değişmez, FPS KORUNUR.

Kaynak: dataset/rescuenet_ham (orijinal 3000x4000 + tam çözünürlüklü maskeler)
Çıktı : dataset/rescuenet_11sinif (1024 tam sahne, 31_kirpma.py ile aynı hat)

Kesintiye dayanıklı: manifest ile tamamlananlar atlanır.

Kullanım:
  venv\\Scripts\\python.exe 41_cok_sinifli_veri.py
  venv\\Scripts\\python.exe 41_cok_sinifli_veri.py --durum
"""
import argparse
import json
import os
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO

KAYNAK = REPO / "dataset" / "rescuenet_ham"
CIKTI = REPO / "dataset" / "rescuenet_11sinif"
MANIFEST = CIKTI / "_manifest.json"

UZUN_KENAR = 1024          # tam sahne, 31_kirpma.py ile aynı
MIN_ALAN = 200
EPSILON_ORANI = 0.003
MAX_POLIGON = 30

# RescueNet piksel değeri -> (YOLO sınıf indeksi, ad)
# Kaynak: indirmeyle gelen RescueNet-Segmentation-Dataset-Note.txt (RESMİ):
#   Background:0, Water:1, Building_No_Damage:2, Building_Minor_Damage:3,
#   Building_Major_Damage:4, Building_Total_Destruction:5, Vehicle:6,
#   Road-Clear:7, Road-Blocked:8, Tree:9, Pool:10
# Yol sınıfları BAŞA alındı ki 2 sınıfa fine-tune'da indeksler korunsun:
#   YOLO 0 = traversable (Road-Clear), YOLO 1 = blocked (Road-Blocked)
# Background(0) etiketlenmez — YOLO'da arka plan örtük.
SINIF_ESLEME = {
    7: (0, "traversable"),                 # Road-Clear
    8: (1, "blocked"),                     # Road-Blocked
    1: (2, "water"),
    2: (3, "building_no_damage"),
    3: (4, "building_minor"),
    4: (5, "building_major"),
    5: (6, "building_total_destruction"),  # MOLOZ — blocked ile doğrudan ilişkili
    6: (7, "vehicle"),
    9: (8, "tree"),                        # MOLOZ kaynağı (devrilmiş ağaç)
    10: (9, "pool"),
}


def maske_poligon(maske, sinif_id, h, w):
    """İkili maske → YOLO-seg satırları (31_kirpma.py ile aynı mantık, alan sıralı)."""
    ikili = (maske > 0).astype(np.uint8)
    konturlar, _ = cv2.findContours(ikili, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cikti = []
    for c in konturlar:
        alan = cv2.contourArea(c)
        if alan < MIN_ALAN:
            continue
        eps = EPSILON_ORANI * cv2.arcLength(c, True)
        yak = cv2.approxPolyDP(c, eps, True)
        if len(yak) < 3:
            continue
        p = yak.reshape(-1, 2).astype(float)
        p[:, 0] /= w
        p[:, 1] /= h
        p = np.clip(p, 0.0, 1.0)
        koord = " ".join(f"{x:.6f} {y:.6f}" for x, y in p)
        cikti.append((alan, f"{sinif_id} {koord}"))
    cikti.sort(key=lambda t: -t[0])
    return [s for _, s in cikti[:MAX_POLIGON]]


def atomik_yaz(yol: Path, yaz_fn):
    tmp = yol.with_name(f".{yol.stem}.tmp{yol.suffix}")
    yaz_fn(tmp)
    os.replace(tmp, yol)


def ciftleri_bul():
    """rescuenet_ham klasör düzeni: <split>set/<split>-org-img + <split>-label-img"""
    esleme = {"trainset": "train", "validationset": "val", "testset": "test"}
    sonuc = {}
    for klasor in sorted(KAYNAK.glob("segmentation-*")):
        ad = klasor.name.replace("segmentation-", "")
        split = esleme.get(ad)
        if not split:
            continue
        img_dir = next((d for d in klasor.iterdir()
                        if d.is_dir() and "org" in d.name), None)
        lbl_dir = next((d for d in klasor.iterdir()
                        if d.is_dir() and "label" in d.name), None)
        if not img_dir or not lbl_dir:
            continue
        ciftler = []
        for g in sorted(img_dir.glob("*.jpg")):
            m = lbl_dir / f"{g.stem}_lab.png"
            if m.exists():
                ciftler.append((g, m))
        if ciftler:
            sonuc[split] = ciftler
    return sonuc


def isle(gorsel: Path, maske: Path, split: str, ist):
    im = cv2.imread(str(gorsel))
    mk = cv2.imread(str(maske), cv2.IMREAD_UNCHANGED)
    if im is None or mk is None:
        return 0
    if mk.ndim == 3:
        mk = mk[:, :, 0]
    if mk.shape[:2] != im.shape[:2]:
        mk = cv2.resize(mk, (im.shape[1], im.shape[0]), interpolation=cv2.INTER_NEAREST)

    h0, w0 = im.shape[:2]
    olcek = UZUN_KENAR / max(h0, w0)
    h, w = int(round(h0 * olcek)), int(round(w0 * olcek))
    im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
    mk = cv2.resize(mk, (w, h), interpolation=cv2.INTER_NEAREST)

    satir = []
    for ham_deger, (sinif_id, ad) in SINIF_ESLEME.items():
        s = maske_poligon(mk == ham_deger, sinif_id, h, w)
        satir += s
        if s:
            ist[ad] = ist.get(ad, 0) + len(s)
    if not satir:
        ist["etiketsiz"] = ist.get("etiketsiz", 0) + 1
        return 0

    ims = CIKTI / "images" / split
    lbs = CIKTI / "labels" / split
    ims.mkdir(parents=True, exist_ok=True)
    lbs.mkdir(parents=True, exist_ok=True)
    ad_ = gorsel.stem
    atomik_yaz(ims / f"{ad_}.jpg",
               lambda p: cv2.imwrite(str(p), im, [cv2.IMWRITE_JPEG_QUALITY, 95]))
    atomik_yaz(lbs / f"{ad_}.txt",
               lambda p: p.write_text("\n".join(satir), encoding="utf-8"))
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--durum", action="store_true")
    args = ap.parse_args()

    CIKTI.mkdir(parents=True, exist_ok=True)
    m = {"tamamlanan": {}, "istatistik": {}}
    if MANIFEST.exists():
        try:
            m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            pass

    if args.durum:
        for s in ("train", "val", "test"):
            d = CIKTI / "images" / s
            n = len(list(d.glob("*.jpg"))) if d.exists() else 0
            print(f"  {s}: {n} görüntü")
        print(f"  istatistik: {m.get('istatistik')}")
        return

    if not KAYNAK.exists():
        raise SystemExit(f"kaynak yok: {KAYNAK}")

    ciftler = ciftleri_bul()
    if not ciftler:
        raise SystemExit("görüntü/maske çifti bulunamadı")
    print(f"Kaynak: {KAYNAK}\nÇıktı : {CIKTI}\nUzun kenar: {UZUN_KENAR}\n")
    for s, c in ciftler.items():
        print(f"  {s}: {len(c)} kaynak görüntü")

    ist = m.get("istatistik") or {}
    t0 = time.time()
    yeni = 0
    for split, liste in ciftler.items():
        for i, (g, mk) in enumerate(liste, 1):
            anahtar = f"{split}/{g.name}"
            if anahtar in m["tamamlanan"]:
                continue
            n = isle(g, mk, split, ist)
            m["tamamlanan"][anahtar] = n
            yeni += n
            if i % 200 == 0:
                m["istatistik"] = ist
                atomik_yaz(MANIFEST, lambda p: p.write_text(
                    json.dumps(m, ensure_ascii=False), encoding="utf-8"))
                print(f"  {split} {i}/{len(liste)} · {yeni} görüntü · "
                      f"{(time.time() - t0) / 60:.1f} dk")
        m["istatistik"] = ist
        atomik_yaz(MANIFEST, lambda p: p.write_text(
            json.dumps(m, ensure_ascii=False), encoding="utf-8"))

    adlar = sorted({v[0]: v[1] for v in SINIF_ESLEME.values()}.items())
    yaml = CIKTI / "data.yaml"
    yaml.write_text(
        f"# RescueNet 11 SINIF — yardımcı görev ön eğitimi için\n"
        f"# Sınıf 0/1 = traversable/blocked (2 sınıfa fine-tune'da indeks korunur)\n"
        f"path: {CIKTI}\ntrain: images/train\nval: images/val\ntest: images/test\n\n"
        f"nc: {len(adlar)}\nnames:\n" +
        "".join(f"  {i}: {ad}\n" for i, ad in adlar), encoding="utf-8")

    print(f"\n{'=' * 56}\nÇOK SINIFLI VERİ TAMAM · {yeni} yeni görüntü · "
          f"{(time.time() - t0) / 60:.1f} dk")
    for s in ("train", "val", "test"):
        d = CIKTI / "images" / s
        if d.exists():
            print(f"  {s}: {len(list(d.glob('*.jpg')))} görüntü")
    print("\n  sınıf başına instance:")
    for k, v in sorted(ist.items(), key=lambda x: -x[1] if isinstance(x[1], int) else 0):
        print(f"    {k:30} {v}")
    print(f"\ndata.yaml: {yaml}")


if __name__ == "__main__":
    main()
