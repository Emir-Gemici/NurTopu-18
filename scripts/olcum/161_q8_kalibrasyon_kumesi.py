r"""161 — Q8 (INT8) KALIBRASYON KUMESI kur · ON_KAYIT REVIEW_LOG D-355.

NEDEN. 30 Agustos'ta Jetson'da INT8 derlemesi kosacak
(`yolo export ... int8=True data=<yaml>`). Bugun:
  · kalibrasyon kumesi YOK,
  · kilavuzun isaret ettigi `karisim_arena.yaml` WINDOWS MUTLAK yollari
    tasiyor (O:\navitas\...) ve Jetson'da acilmaz — kilavuz bunu KENDISI
    yaziyor ama bitirilmemis,
  · pakette kalibrasyon karesi var ama ETIKETSIZ (49 jpg, 0 txt).

BU BETIK kumeyi URETIR (elle kopyalanmaz, yeniden uretilebilir):
  · 80 sentetik arena (dagitimin hedefi) + 40 gercek DJI karesi
  · ETIKETLERIYLE birlikte (ultralytics val yukleyicisi etiket ister)
  · YAML'da `path:` anahtari YAZILMAZ — ultralytics onu YAML'in KENDI
    dizinine gore cozer; mutlak yol yazmak tam da bugunku kusurdur
  · POSIX goreli yollar (Jetson Linux)

🔴 AYRIKLIK SARTI (D-355 SS5): kalibrasyon kareleri, DOGRULUK KAPISININ
kareleriyle KESISMEZ. Ayni kareyle hem kalibre edip hem olcmek CEVRIMSELDIR.
Bu betik ayrilan kareleri `dogruluk_kapisi_kareleri.json` olarak yazar ve
kesisimi KOSUMDA denetler — belgede iddia edilmez.

Kullanim:
  <venv> 161_q8_kalibrasyon_kumesi.py --cikti jetson_paket/kalibrasyon
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]

# D-355 SS2: sayilar ON KAYITTAN gelir, burada uydurulmaz.
SENTETIK_ADET = 80
GERCEK_ADET = 40
# Dogruluk kapisi icin AYRILAN (kalibrasyona GIRMEYEN) kare sayilari.
KAPI_SENTETIK = 60
KAPI_GERCEK = 30
# Kalibrasyon karelerinin uzun kenari. Uretimde model INFER_SIZE=512 gorur;
# 4K kare gondermek hem paketi sisirir hem uretimden uzaklastirir.
UZUN_KENAR = 640


def _ciftler(kume: Path):
    """(goruntu, etiket) ciftleri — etiketsiz kare ALINMAZ."""
    out = []
    for img in sorted((kume / "images").rglob("*.jpg")):
        lbl = kume / "labels" / img.parent.name / (img.stem + ".txt")
        if lbl.is_file() and lbl.stat().st_size:
            out.append((img, lbl))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cikti", type=Path,
                    default=KOK / "jetson_paket" / "kalibrasyon")
    ap.add_argument("--sentetik", type=Path,
                    default=KOK / "dataset" / "sentetik_arena_bariyer_acili")
    ap.add_argument("--gercek", type=Path, default=KOK / "dataset" / "dji_v7")
    a = ap.parse_args()

    sen = _ciftler(a.sentetik)
    ger = _ciftler(a.gercek)
    gerek_s = SENTETIK_ADET + KAPI_SENTETIK
    gerek_g = GERCEK_ADET + KAPI_GERCEK
    if len(sen) < gerek_s or len(ger) < gerek_g:
        raise SystemExit(
            f"yeterli etiketli kare yok: sentetik {len(sen)}/{gerek_s} · "
            f"gercek {len(ger)}/{gerek_g}")

    # DETERMINIST ve AYRIK secim. 🔴 Ilk yazimda `atla` parametreli tek bir
    # ornekleyici kullandim ve adim yeniden hesaplandigi icin iki kume 17
    # karede KESISTI — ayriklik denetimi bunu KOSUMDA yakaladi (kanit: bu
    # yorum). Cozum: listeyi ONCE ikiye BOL, sonra her yaridan ayri ornekle.
    # Boylece kesisim KURGU GEREGI imkansizdir, umuda birakilmaz.
    def bol_ve_ornekle(liste, n_kal, n_kapi):
        yari = len(liste) // 2
        onculer, ardillar = liste[:yari], liste[yari:]
        def esit(l, n):
            if n <= 0 or not l:
                return []
            adim = max(1, len(l) // n)
            return l[::adim][:n]
        return esit(onculer, n_kal), esit(ardillar, n_kapi)

    kal_s, kapi_s = bol_ve_ornekle(sen, SENTETIK_ADET, KAPI_SENTETIK)
    kal_g, kapi_g = bol_ve_ornekle(ger, GERCEK_ADET, KAPI_GERCEK)
    kal, kapi = kal_s + kal_g, kapi_s + kapi_g
    for ad, alinan, istenen in (("sentetik-kal", kal_s, SENTETIK_ADET),
                                ("sentetik-kapi", kapi_s, KAPI_SENTETIK),
                                ("gercek-kal", kal_g, GERCEK_ADET),
                                ("gercek-kapi", kapi_g, KAPI_GERCEK)):
        if len(alinan) < istenen:
            raise SystemExit(f"{ad}: {len(alinan)}/{istenen} kare — kume kucuk")

    # 🔴 AYRIKLIK KOSUMDA DENETLENIR (D-355 §5)
    kal_ad = {p.name for p, _ in kal}
    kapi_ad = {p.name for p, _ in kapi}
    kesisim = kal_ad & kapi_ad
    if kesisim:
        raise SystemExit(
            f"🔴 AYRIKLIK IHLALI (D-355 §5): kalibrasyon ve kapi kareleri "
            f"{len(kesisim)} karede KESISIYOR — cevrimsel olcum. Ornek: "
            f"{sorted(kesisim)[:3]}")

    img_d = a.cikti / "images"
    lbl_d = a.cikti / "labels"
    for d in (img_d, lbl_d):
        d.mkdir(parents=True, exist_ok=True)
    # 🔴 KARELER KUCULTULEREK kopyalanir (uzun kenar UZUN_KENAR).
    # Neden: gercek DJI kareleri 4K'dir ve 40 tanesi paketi 127 MB sisiriyordu.
    # Daha onemlisi, model sahada zaten `_preprocess` ile kucultulmus kareyi
    # gorur (INFER_SIZE=512); 4K gondermek uretimden UZAKLASTIRIR.
    # 640'a kucultmek modelin gordugune DAHA YAKINDIR.
    # ⚠ Etiketler NORMALIZE poligonlardir; olcek degisimi onlari BOZMAZ,
    # bu yuzden aynen kopyalanir.
    import cv2
    for img, lbl in kal:
        im = cv2.imread(str(img))
        if im is None:
            raise SystemExit(f"kare okunamadi: {img}")
        h, w = im.shape[:2]
        k = UZUN_KENAR / float(max(h, w))
        if k < 1.0:
            im = cv2.resize(im, (int(round(w * k)), int(round(h * k))),
                            interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(img_d / img.name), im, [cv2.IMWRITE_JPEG_QUALITY, 95])
        shutil.copy2(lbl, lbl_d / lbl.name)

    # YAML — `path:` YAZILMAZ (D-355 §4). POSIX goreli.
    (a.cikti / "kalibrasyon.yaml").write_text(
        "# Q8 (INT8) KALIBRASYON KUMESI — ON_KAYIT REVIEW_LOG D-355\n"
        "#\n"
        "# ⚠ `path:` ANAHTARI BILEREK YOKTUR. Ultralytics onu bu YAML'in KENDI\n"
        "# dizinine gore cozer. Mutlak yol yazmak tam da duzeltilen kusurdur:\n"
        "# eski `karisim_arena.yaml` WINDOWS mutlak yollari tasiyor ve\n"
        "# Jetson'da ACILMIYORDU.\n"
        "#\n"
        f"# Kalibrasyon: {SENTETIK_ADET} sentetik arena + {GERCEK_ADET} gercek DJI.\n"
        "# Bu kareler DOGRULUK KAPISININ kareleriyle KESISMEZ (D-355 §5);\n"
        "# ayriklik uretimde KOSUMDA denetlendi.\n"
        "#\n"
        "# Yeniden uretme:\n"
        "#   <venv> scripts/olcum/161_q8_kalibrasyon_kumesi.py\n"
        "\n"
        "train: images\n"
        "val: images\n"
        "\n"
        "nc: 2\n"
        "names:\n"
        "  0: traversable\n"
        "  1: blocked\n",
        encoding="utf-8")

    (a.cikti / "dogruluk_kapisi_kareleri.json").write_text(
        json.dumps({
            "_neden": ("D-355 §5: bu kareler KALIBRASYONA GIRMEDI; INT8 "
                       "dogruluk kapisi BUNLARLA kosulur. Ayni kareyle hem "
                       "kalibre edip hem olcmek CEVRIMSELDIR."),
            "adet": len(kapi),
            "kareler": [str(p.relative_to(KOK)).replace("\\", "/") for p, _ in kapi],
        }, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"kalibrasyon  : {len(kal)} kare -> {a.cikti}")
    print(f"  sentetik   : {SENTETIK_ADET} · gercek: {GERCEK_ADET}")
    print(f"kapi kareleri: {len(kapi)} (kalibrasyona GIRMEDI, ayriklik dogrulandi)")
    print(f"yaml         : {a.cikti / 'kalibrasyon.yaml'}  (`path:` anahtari YOK)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
