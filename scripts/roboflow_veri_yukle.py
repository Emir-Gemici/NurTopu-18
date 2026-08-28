"""Etiketli veri kumesini ROBOFLOW'a yukle (goruntu + YOLO-seg poligon etiketi).

Mevcut `roboflow_yukle.py` MODEL yukler; bu betik VERI yukler.

⚠ API ANAHTARI DEPOYA YAZILMAZ. Yalniz ortam degiskeninden okunur:
      set ROBOFLOW_API_KEY=...        (Windows)
      export ROBOFLOW_API_KEY=...     (bash)
  Anahtar argumana ALINMAZ — komut satiri gecmise ve surec listesine dusebilir.

⚠ DISA DONUK ISLEM: bu betik veriyi ucuncu taraf bir servise GONDERIR.
  Gonderilen sey silinse bile onbelleklenmis/indekslenmis olabilir. Bu yuzden
  varsayilan `--kuru` (hicbir sey gondermez) ve gercek yukleme ACIKCA
  `--uygula` ister.

Kullanim:
  # 1) once KURU kosu — ne gonderilecegini gorursun, hicbir sey gitmez
  <venv> scripts/roboflow_veri_yukle.py --kume dataset/sentetik_arena_bariyer_acili

  # 2) gercek yukleme
  <venv> scripts/roboflow_veri_yukle.py --kume ... --uygula --sinir 50
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

WORKSPACE = "yunuss-workspace-nsfb3"
PROJE = "n4-ozyy8"


def _ciftler(kume: Path):
    """(goruntu, etiket) ciftleri. Etiketi olmayan goruntu GONDERILMEZ."""
    ciftler, oksuz = [], []
    for img in sorted(kume.glob("images/*/*.jpg")) + sorted(kume.glob("images/*.jpg")):
        p = str(img).replace("\\", "/")
        lbl = Path(p.replace("/images/", "/labels/")).with_suffix(".txt")
        if lbl.is_file() and lbl.stat().st_size > 0:
            ciftler.append((img, lbl))
        else:
            oksuz.append(img)
    return ciftler, oksuz


def _sozlesme_siniflari():
    """Sinif adlarini CONTRACTS.md'den oku — CIPLAK SABIT YAZILMAZ (madde 16).

    Gercek DJI kumelerinde (`dataset/dji_*`, `dataset/gercek_*`) `data.yaml`
    YOKTUR; yalniz images/ + labels/ vardir. Adlari koda gomsek sozlesme
    degistiginde burasi BAYAT kalirdi. Bu yuzden tek kaynak CONTRACTS.md'nin
    sinif tablosudur:  | `0` | `zemin` / `traversable` | ...
    """
    import re
    m = KOK / "CONTRACTS.md"
    if not m.is_file():
        return None
    adlar = {}
    for satir in m.read_text(encoding="utf-8").splitlines():
        e = re.match(r"\|\s*`(\d+)`\s*\|\s*`[^`]+`\s*/\s*`([^`]+)`", satir)
        if e:
            adlar[int(e.group(1))] = e.group(2)
        if len(adlar) >= 2 and 0 in adlar and 1 in adlar:
            break
    if 0 not in adlar or 1 not in adlar:
        return None
    return [adlar[i] for i in sorted(adlar)]


def _sinif_adlari(kume: Path):
    y = kume / "data.yaml"
    if not y.is_file():
        return _sozlesme_siniflari()          # gercek kumelerde data.yaml YOK
    import yaml
    d = yaml.safe_load(y.read_text(encoding="utf-8"))
    n = d.get("names")
    return list(n.values()) if isinstance(n, dict) else n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--kume", type=Path, required=True, action="append",
                    help="YOLO duzeninde kume koku (images/ + labels/). "
                         "BIRDEN COK kez verilebilir; ayni dosya adi iki "
                         "kumede varsa ONCE VERILEN kazanir — bu yuzden "
                         "GUNCEL etiketi tasiyan kume ONCE yazilir.")
    ap.add_argument("--workspace", default=WORKSPACE)
    ap.add_argument("--proje", default=PROJE)
    ap.add_argument("--parti", default=None,
                    help="Roboflow batch adi (varsayilan: kume adi)")
    ap.add_argument("--sinir", type=int, default=None,
                    help="yalniz ilk N cifti gonder (once kucuk parti dene)")
    ap.add_argument("--bekle", type=float, default=0.0,
                    help="her yukleme arasi saniye (hiz siniri icin)")
    ap.add_argument("--uygula", action="store_true",
                    help="GERCEKTEN gonder. Verilmezse KURU kosu.")
    a = ap.parse_args()

    kumeler = [(k if k.is_absolute() else (KOK / k)) for k in a.kume]
    for k in kumeler:
        if not k.is_dir():
            raise SystemExit(f"kume yok: {k}")

    # TEKILLESTIRME: ayni kare birden cok kumede olabilir (v2/v3 YENIDEN
    # ETIKETLEMEDIR). Once verilen kazanir; cagiran GUNCEL etiketi tasiyan
    # kumeyi ONCE yazar. Hangi karenin hangi kumeden geldigi RAPORLANIR —
    # sessiz atlama YOK.
    ciftler, oksuz, gorulen, koken = [], [], set(), {}
    for k in kumeler:
        c, o = _ciftler(k)
        yeni_sayi = 0
        for img, lbl in c:
            if img.name in gorulen:
                continue
            gorulen.add(img.name)
            ciftler.append((img, lbl))
            yeni_sayi += 1
        oksuz.extend(o)
        koken[k.name] = (len(c), yeni_sayi, len(o))

    siniflar = None
    for k in kumeler:
        sn = _sinif_adlari(k)
        if sn is None:
            continue
        if siniflar is not None and list(sn) != list(siniflar):
            raise SystemExit(f"SINIF ADLARI CELISIYOR: {siniflar} vs {sn} ({k})")
        siniflar = sn
    if not siniflar:
        raise SystemExit("sinif adlari cozulemedi (data.yaml yok, CONTRACTS.md "
                         "sinif tablosu okunamadi) — indisle yuklemeyiz")

    parti = a.parti or (kumeler[0].name if len(kumeler) == 1 else "gercek_kareler")

    for ad_k, (t, y, ok) in koken.items():
        print(f"kume      : {ad_k:32s} cift={t:5d} YENI={y:5d} etiketsiz={ok}")
    print(f"siniflar  : {siniflar}")
    print(f"cift      : {len(ciftler)}  (etiketsiz atlanan: {len(oksuz)})")
    print(f"hedef     : {a.workspace}/{a.proje}  · batch '{parti}'")
    if a.sinir:
        ciftler = ciftler[:a.sinir]
        print(f"SINIR     : yalniz ilk {len(ciftler)} cift")

    if not ciftler:
        raise SystemExit("gonderilecek cift YOK — etiketler bulunamadi")

    if not a.uygula:
        print("\nKURU KOSU — hicbir sey gonderilmedi.")
        print("ilk uc cift:")
        for img, lbl in ciftler[:3]:
            print(f"  {img.name}  <-  {lbl.name} "
                  f"({sum(1 for _ in lbl.open(encoding='utf-8'))} poligon)")
        print("\nGercekten gondermek icin --uygula ekleyin.")
        return 0

    anahtar = os.environ.get("ROBOFLOW_API_KEY", "").strip()
    if not anahtar:
        raise SystemExit(
            "ROBOFLOW_API_KEY tanimli degil. Anahtari ARGUMAN OLARAK VERMEYIN "
            "(komut gecmisine duser); ortam degiskeni kullanin.")

    # 🔴 `roboflow` PAKETI KULLANILMIYOR — bilerek. Paket bagimlilik olarak
    # `opencv-python-headless` cekiyor ve bu, uretimde kullanilan
    # `opencv-python`i DEGISTIRIYOR (kurulum denendi: cv2.pyd kilitli, WinError 5).
    # Calisan bir CUDA/OpenCV ortamini bir yukleme betigi icin riske atmayiz.
    # REST API `requests` ile dogrudan kullanilir; ORTAM DEGISMEZ.
    #
    # 🔴 ETIKET BICIMI: YOLO .txt DEGIL, COCO JSON. Sebep OLCULDU (2026-08-28):
    # YOLO .txt ham govdeyle gonderildiginde sunucu 200/success doner ve
    # poligonlar dogru iner, ama `labelmap` sorgu parametresi UYGULANMAZ —
    # sinif adi ham indis olarak kalir ("0", "1") ve proje sinif listesi BOS
    # gorunur. `labelmap`i multipart alan ya da .json dosyasi olarak gondermek
    # 400 InvalidAnnotationFormat verir. COCO JSON sinif ADLARINI kendi
    # icinde tasidigi icin bu sorun ortadan kalkar; poligon tipi de korunur.
    #   dogrulama: GET /{ws}/{proje}/images/{id} -> etiketler
    #     YOLO .txt  -> ['0', '1']                  (KUSURLU)
    #     COCO JSON  -> ['blocked', 'traversable']  (DOGRU)
    import json as _json

    import cv2
    import requests

    UC = f"https://api.roboflow.com/dataset/{a.proje}"
    adlar = {i: ad for i, ad in enumerate(siniflar or [])}

    def _coco(img: Path, lbl: Path) -> bytes:
        """YOLO-seg poligonlarini tek goruntuluk COCO JSON'a cevir."""
        im = cv2.imread(str(img))
        if im is None:
            raise RuntimeError("goruntu okunamadi")
        h, w = im.shape[:2]
        anns = []
        for satir in lbl.read_text(encoding="utf-8").splitlines():
            par = satir.split()
            if len(par) < 7:            # sinif + en az 3 nokta
                continue
            c = int(par[0])
            v = [float(x) for x in par[1:]]
            xs = [v[i] * w for i in range(0, len(v) - 1, 2)]
            ys = [v[i] * h for i in range(1, len(v), 2)]
            if len(xs) < 3:
                continue
            seg = [k for xy in zip(xs, ys) for k in xy]
            x0, y0 = min(xs), min(ys)
            anns.append({"id": len(anns) + 1, "image_id": 1,
                         "category_id": c + 1, "segmentation": [seg],
                         "bbox": [x0, y0, max(xs) - x0, max(ys) - y0],
                         "area": (max(xs) - x0) * (max(ys) - y0), "iscrowd": 0})
        if not anns:
            raise RuntimeError("gecerli poligon yok")
        return _json.dumps({
            "images": [{"id": 1, "file_name": img.name, "width": w, "height": h}],
            "categories": [{"id": i + 1, "name": n, "supercategory": "none"}
                           for i, n in adlar.items()],
            "annotations": anns}).encode()

    basarili = hatali = 0
    hatalar = []
    for i, (img, lbl) in enumerate(ciftler, 1):
        try:
            govde = _coco(img, lbl)          # ONCE cevir: bozuksa hic gonderme
            with open(img, "rb") as fh:
                r = requests.post(
                    f"{UC}/upload",
                    params={"api_key": anahtar, "name": img.name,
                            "split": "train", "batch": parti},
                    files={"file": (img.name, fh, "image/jpeg")}, timeout=120)
            r.raise_for_status()
            d = r.json()
            gid = d.get("id") or (d.get("image") or {}).get("id")
            if not gid:
                raise RuntimeError(f"goruntu id donmedi: {str(d)[:160]}")
            r2 = requests.post(
                f"{UC}/annotate/{gid}",
                params={"api_key": anahtar, "name": img.stem + "_coco.json",
                        "overwrite": "true"},
                data=govde, headers={"Content-Type": "application/json"},
                timeout=120)
            r2.raise_for_status()
            if not r2.json().get("success"):
                raise RuntimeError(f"etiket reddedildi: {str(r2.json())[:160]}")
            basarili += 1
        except Exception as exc:                      # sessiz dusme YOK
            hatali += 1
            hatalar.append(f"{img.name}: {type(exc).__name__}: {str(exc)[:140]}")
        if i % 25 == 0 or i == len(ciftler):
            print(f"  {i}/{len(ciftler)} · basarili {basarili} · hatali {hatali}",
                  flush=True)
        if a.bekle:
            time.sleep(a.bekle)

    print(f"\nBITTI · basarili {basarili} · hatali {hatali}")
    for h in hatalar[:10]:
        print(f"  HATA {h}")
    if len(hatalar) > 10:
        print(f"  ... {len(hatalar)-10} hata daha")
    return 0 if hatali == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
