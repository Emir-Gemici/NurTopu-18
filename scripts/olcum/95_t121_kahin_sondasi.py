"""T121 adim 2 — KAHIN SONDASI: hangi model bu alanda CATIYI ZEMINDEN ayirir?

NEDEN (mimar T121 emri + D-210): copy_paste ureteci gercek karelerde zemini
TAM KARE etiketliyor (`yolo_etiketi()`, copy_paste_augmentation.py:817-829).
Secenek (a) "dogrulanmis zemine daralt" bir ZEMIN KAHINI ister; secenek (c)
"cati ayri kahinle sinif 1" bir CATI KAHINI ister. Bu betik ADAY modellerin
bu alandaki (otopark, 1024x576 WhatsApp kareleri) davranisini OLCER — secim
yapmaz, secim MIMARINDIR.

YONTEM: 6 sonda karesi x cati-ici / zemin-referans diskleri
(`results/t121/diskler.json`; yerlesim gozle, D-80; REV1 duzeltmeleri dahil).
Diskler bolge SINIRLARINDAN uzak tutuldu ki kahin kiyasi sinir hatasina degil
GOVDE davranisina baksin. Maske zinciri uretecin KENDISINDEN import edilir
(`zemin_ve_mevcut_engel` — secenek (a) tam bu zincirle kosacagi icin);
yeniden uygulama yok.

GUVEN ESIKLERI (ciplak sayi degil, ikisi de kayitli kaynaktan):
  0.05 = uretec `zemin_conf` varsayilani (dataset/copy_paste_gercek/
         manifest.json "zemin_conf": 0.05 — kosulmus uretimin kendi degeri)
  0.30 = uretim karar zinciri CONF (65_kabul_denetcisi.py CONF, D-139 zinciri)

DAIRESELLIK UYARISI (emirden): v34 URETIMDIR (duzeltilmeye calisilan model),
v21/v30 ayni karisim soyundandir. Olcume dahiller cunku "mevcut hicbir model
bu alanda cati gormuyor" iddiasi ancak olcumle yazilabilir; ama (a) icin
KAHIN olarak secilmeleri dairesel olur ve rapor bunu ayrica soyler.

CIKTI: results/t121/kahin_sondasi.json (ham disk-bazli degerler + ozet).
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

from copy_paste_augmentation import zemin_ve_mevcut_engel  # noqa: E402
from ultralytics import YOLO  # noqa: E402

DISKLER = KOK / "results" / "t121" / "diskler.json"
CIKTI = KOK / "results" / "t121" / "kahin_sondasi.json"
KARE_KOKU = KOK / "data" / "raw_frames"

# Adaylar: (etiket, agirlik yolu, dairesellik notu)
ADAYLAR = [
    ("aday_v5c_m640", "models/aday_v5c_m640.pt",
     "URETEC KAHINI - kosulmus uretimde zemin_model buydu (manifest.json)"),
    ("v17", "models/navitas_seg_v17_best.pt",
     "eski soy; karisim yorumunda 'cokmuyor ama kor' (karisim_t54_engelli.yaml)"),
    ("v20", "models/navitas_seg_v20_best.pt",
     "eski soy; ayni yorum"),
    ("v21", "models/navitas_seg_v21_best.pt",
     "DAIRESEL-ADAY: copy_paste tam-kare etiketiyle egitildi"),
    ("v30", "models/navitas_seg_v30_best.pt",
     "DAIRESEL-ADAY: ayni soy"),
    ("v34", "models/navitas_seg_v34_best.pt",
     "DAIRESEL-URETIM: duzeltilmeye calisilan modelin kendisi"),
]
CONFLAR = (0.05, 0.30)


def disk_maskesi(sekil: tuple[int, int], x: int, y: int, r: int) -> np.ndarray:
    m = np.zeros(sekil, np.uint8)
    cv2.circle(m, (int(x), int(y)), int(r), 1, -1)
    return m


def main() -> int:
    cfg = json.load(io.open(DISKLER, encoding="utf-8"))
    kareler = {ad: cv2.imread(str(KARE_KOKU / ad)) for ad in cfg["kareler"]}
    for ad, img in kareler.items():
        if img is None:
            print(f"KARE OKUNAMADI: {ad}", file=sys.stderr)
            return 2

    sonuc = {"diskler_rev": cfg["aciklama"], "conflar": list(CONFLAR),
             "adaylar": [], "olcumler": []}
    for etiket, yol, not_ in ADAYLAR:
        model = YOLO(str(KOK / yol), task="segment")
        sonuc["adaylar"].append({"etiket": etiket, "yol": yol, "not": not_})
        for conf in CONFLAR:
            for ad, k in cfg["kareler"].items():
                bgr = kareler[ad]
                zemin, engel = zemin_ve_mevcut_engel(model, bgr, conf)
                if zemin.shape != bgr.shape[:2]:
                    print(f"SEKIL UYUSMAZ: {ad} {zemin.shape} != {bgr.shape[:2]}",
                          file=sys.stderr)
                    return 3
                for tur, diskler in (("cati", k["cati"]), ("zemin", k["zemin"])):
                    for x, y, r in diskler:
                        dm = disk_maskesi(zemin.shape, x, y, r).astype(bool)
                        sonuc["olcumler"].append({
                            "model": etiket, "conf": conf, "kare": ad,
                            "cati_turu": k["cati_turu"], "disk_turu": tur,
                            "disk": [x, y, r],
                            "zemin_orani": round(float(zemin[dm].mean()), 4),
                            "engel_orani": round(float(engel[dm].mean()), 4),
                        })
        del model

    # Ozet: model x conf -> cati disklerinde ort. zemin orani (kucuk iyi),
    # zemin disklerinde ort. zemin orani (buyuk iyi).
    ozet = {}
    for o in sonuc["olcumler"]:
        anahtar = f"{o['model']}@{o['conf']}"
        alan = ozet.setdefault(anahtar, {"cati_zemin": [], "zemin_zemin": [],
                                         "cati_engel": []})
        if o["disk_turu"] == "cati":
            alan["cati_zemin"].append(o["zemin_orani"])
            alan["cati_engel"].append(o["engel_orani"])
        else:
            alan["zemin_zemin"].append(o["zemin_orani"])
    sonuc["ozet"] = {
        k: {"cati_disklerinde_ort_zemin": round(float(np.mean(v["cati_zemin"])), 4),
            "cati_disklerinde_ort_engel": round(float(np.mean(v["cati_engel"])), 4),
            "zemin_disklerinde_ort_zemin": round(float(np.mean(v["zemin_zemin"])), 4)}
        for k, v in ozet.items()}

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI, "w", encoding="utf-8").write(
        json.dumps(sonuc, ensure_ascii=False, indent=1))
    print(f"{'model@conf':24s} {'cati->zemin':>11s} {'cati->engel':>11s} {'zemin->zemin':>12s}")
    for k, v in sonuc["ozet"].items():
        print(f"{k:24s} {v['cati_disklerinde_ort_zemin']:11.3f} "
              f"{v['cati_disklerinde_ort_engel']:11.3f} "
              f"{v['zemin_disklerinde_ort_zemin']:12.3f}")
    print(f"yazildi: {CIKTI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
