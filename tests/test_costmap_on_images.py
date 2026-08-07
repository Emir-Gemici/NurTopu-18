"""NEDEN: Kirmizi bindirmeli 2026-08-02 ekran goruntuleri ham girdi degildir;
onlarda model calistirmak olcum dongusunu kirletir. Bu test yalniz alti ham
1600x900 foto ve dort drone videosundan seyrek ham karelerle costmap guvenligini
olcer; uc bindirmeli gorseli sadece ONCE referans sayfasinda gosterir.

Iki kip, codes/test_rota_guvenlik.py'ndeki uretim-uyumlu DOTA OBB kahin yolunu
dogrudan kullanir: HAM kipte kahin planlayiciya verilmez; ENJEKTE kipte geometri
deneyi icin ek engel olur. Her iki kipin araba yakinligi sonradan ayni kahinle
puanlanir.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from ultralytics import YOLO


KOK = Path(__file__).resolve().parents[1]
KODLAR = KOK / "codes"
if str(KODLAR) not in sys.path:
    sys.path.insert(0, str(KODLAR))

# Mevcut iki-kipli kâhin testi kaynak tek dogruluk otoritesidir. _rota_uret ve
# _min_aciklik_araca_px, bir_kare_isle'nin kullandigi dusuk seviye kanittir;
# burada kopyalanmaz veya yeni bir rota algoritmasi yazilmaz.
from test_rota_guvenlik import (
    VARSAYILAN_GORSELLER,
    VARSAYILAN_VIDEOLAR,
    _min_aciklik_araca_px,
    _rota_uret,
    bir_kare_isle,
)


ONCE_BINDIRMELER = (
    "WhatsApp Image 2026-08-02 at 14.53.52.jpeg",
    "WhatsApp Image 2026-08-02 at 14.53.52 (1).jpeg",
    "WhatsApp Image 2026-08-02 at 14.53.52 (2).jpeg",
)


@dataclass
class KareSonucu:
    """Bir ham karede iki kipin tekrarlanabilir guvenlik ozeti."""

    kaynak: str
    tur: str
    kare_no: int
    ham_karar_var: bool
    ham_ihlal: bool | None
    ham_min_aciklik_px: float | None
    enjekte_karar_var: bool
    enjekte_ihlal: bool | None
    enjekte_min_aciklik_px: float | None
    r_gerekli_px: float | None
    mpp: float | None


def atomik_json_yaz(hedef: Path, veri: dict) -> None:
    """Ozeti yarim JSON birakmadan yaz."""
    gecici = hedef.with_name(f".{hedef.stem}.{uuid.uuid4().hex}.tmp{hedef.suffix}")
    try:
        gecici.write_text(json.dumps(veri, ensure_ascii=False, indent=2), encoding="utf-8")
        gecici.replace(hedef)
    finally:
        if gecici.exists():
            gecici.unlink()


def guvenli_ad(metin: str) -> str:
    """Gorsel cikti adini Windows-guvenli yap."""
    sonuc = re.sub(r"[^a-zA-Z0-9_-]+", "_", metin).strip("_")
    return sonuc or "kare"


def video_kareleri(video: Path, adet: int) -> Iterable[tuple[int, np.ndarray]]:
    """Videonun bas/orta/sonuna dagilmis seyrek HAM kareleri oku."""
    cap = cv2.VideoCapture(str(video))
    if not cap.isOpened():
        raise OSError(f"Video acilamadi: {video}")
    try:
        toplam = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if toplam <= 0:
            return
        indisler = sorted({int(round(i * (toplam - 1) / max(1, adet - 1))) for i in range(adet)})
        for indis in indisler:
            cap.set(cv2.CAP_PROP_POS_FRAMES, indis)
            ok, kare = cap.read()
            if ok and kare is not None:
                yield indis, kare
    finally:
        cap.release()


def etiketli_kucult(gorsel: np.ndarray, baslik: str, boyut: tuple[int, int] = (480, 270)) -> np.ndarray:
    """Kontakt sayfasi icin orani koruyarak bir kutucuk ve baslik uret."""
    w, h = boyut
    tuval = np.full((h + 32, w, 3), 30, dtype=np.uint8)
    oran = min(w / gorsel.shape[1], h / gorsel.shape[0])
    nw, nh = max(1, int(gorsel.shape[1] * oran)), max(1, int(gorsel.shape[0] * oran))
    kucuk = cv2.resize(gorsel, (nw, nh), interpolation=cv2.INTER_AREA)
    x0, y0 = (w - nw) // 2, (h - nh) // 2
    tuval[y0:y0 + nh, x0:x0 + nw] = kucuk
    cv2.putText(tuval, baslik[:62], (8, h + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (255, 255, 255), 1)
    return tuval


def kontakt_sayfasi(ogeler: list[tuple[str, np.ndarray]], hedef: Path, sutun: int = 3) -> None:
    """Gorselleri ayni boyutta sayfalayip yaz."""
    kutular = [etiketli_kucult(gorsel, baslik) for baslik, gorsel in ogeler if gorsel is not None]
    if not kutular:
        return
    bos = np.full_like(kutular[0], 30)
    satirlar = []
    for baslangic in range(0, len(kutular), sutun):
        satir = kutular[baslangic:baslangic + sutun]
        satir += [bos.copy()] * (sutun - len(satir))
        satirlar.append(np.hstack(satir))
    cv2.imwrite(str(hedef), np.vstack(satirlar))


def once_referans_sayfasi(cikti: Path) -> None:
    """Kirlenmis uc ekran goruntusunu model calistirmadan ONCE referansi yap."""
    ogeler = []
    for ad in ONCE_BINDIRMELER:
        yol = KOK / ad
        gorsel = cv2.imread(str(yol))
        if gorsel is not None:
            ogeler.append((f"ONCE referansi - INFERENCE YOK: {ad}", gorsel))
    kontakt_sayfasi(ogeler, cikti / "once_bindirmeli_referans.jpg", sutun=3)


def sonuc_donustur(kaynak: str, tur: str, kare_no: int, sonuc: dict) -> KareSonucu:
    """Mevcut testin dict'ini kalici ozet semasina indir."""
    ham, enj = sonuc["ham"], sonuc["enj"]
    return KareSonucu(
        kaynak=kaynak, tur=tur, kare_no=kare_no,
        ham_karar_var=bool(ham["karar_var"]), ham_ihlal=ham["ihlal"],
        ham_min_aciklik_px=ham["min_aciklik_px"],
        enjekte_karar_var=bool(enj["karar_var"]), enjekte_ihlal=enj["ihlal"],
        enjekte_min_aciklik_px=enj["min_aciklik_px"],
        r_gerekli_px=sonuc["r_gerekli_px"], mpp=sonuc["mpp"],
    )


def guvenlik_ozeti(sonuclar: list[KareSonucu]) -> dict:
    """Iki-kip sonucunu guc, geometri ve olcum-varligi kapilarindan gecir."""
    if not sonuclar:
        raise ValueError("Guvenlik ozeti icin en az bir kare gerekli")
    n = len(sonuclar)
    olcekli = [kayit for kayit in sonuclar if kayit.mpp is not None]
    n_olcekli = len(olcekli)
    n_olceksiz = n - n_olcekli
    ham_ihlal = sum(kayit.ham_ihlal is True for kayit in olcekli)
    enj_ihlal = sum(kayit.enjekte_ihlal is True for kayit in olcekli)
    enj_karar = sum(kayit.enjekte_karar_var for kayit in olcekli)
    ham_oran = ham_ihlal / n_olcekli if n_olcekli else None
    enj_tam_sifir = (enj_ihlal == 0) if n_olcekli else None
    ham_guclu = (ham_oran > 0.10) if ham_oran is not None else False

    if n_olcekli == 0:
        durum = "OLCUM_YOK"
    elif not enj_tam_sifir:
        durum = "GEOMETRI_HATASI"
    elif n_olceksiz:
        durum = "KISMI_OLCUM"
    elif enj_karar == 0:
        durum = "OLCUM_YOK"
    elif not ham_guclu:
        durum = "GUCSUZ"
    else:
        durum = "GECTI"

    return {
        "n_kare": n,
        "olcekli_kare": n_olcekli,
        "olceksiz_kare": n_olceksiz,
        "olcek_kapsama_orani": round(n_olcekli / n, 4),
        "ham_ihlal": ham_ihlal,
        "ham_ihlal_orani": round(ham_oran, 4) if ham_oran is not None else None,
        "enjekte_ihlal": enj_ihlal,
        "enjekte_karar_var": enj_karar,
        "enjekte_cekimserlik_orani": (
            round(1 - enj_karar / n_olcekli, 4) if n_olcekli else None
        ),
        "enjekte_kesisim_dilate_arac_r_gerekli_tam_sifir": enj_tam_sifir,
        "ham_test_guclu": ham_guclu,
        "durum": durum,
        "not": "ihlal, mevcut _min_aciklik_araca_px < r_gerekli_px kanitidir; bu rota ile dilate(arac, r_gerekli) kesisiminin esdegeridir.",
    }


def ozet_cikis_kodu(ozet: dict) -> int:
    """Yalniz tum kapilardan gecen olcumu basarili surec say."""
    return 0 if ozet["durum"] == "GECTI" else 1


def argumanlar() -> argparse.Namespace:
    """Ham kaynak tabanli costmap gorsel dogrulama arayuzu."""
    varsayilan = KOK / "results" / f"costmap_gorsel_dogrulama_{time.strftime('%Y%m%d_%H%M%S')}"
    ayrac = argparse.ArgumentParser(description="Ham foto/video karelerinde iki-kipli costmap guvenlik kaniti")
    ayrac.add_argument("--navitas-model", type=Path, default=KOK / "models" / "navitas_seg_v20_best.pt")
    ayrac.add_argument("--arac-model", "--coco-model", dest="arac_model", type=Path,
                        default=KOK / "yolov8m-obb.pt",
                        help="DOTA OBB arac kahini; --coco-model eski uyumluluk adidir")
    ayrac.add_argument("--arac-conf", type=float, default=0.25)
    ayrac.add_argument("--imgsz", type=int, default=896)
    ayrac.add_argument("--conf", type=float, default=0.25)
    ayrac.add_argument("--video-basina", type=int, default=3,
                        help="Her ham videodan bas/orta/son seyrek kare (varsayilan: 3)")
    ayrac.add_argument("--sinir", type=int, help="Yalniz ilk N aday kareyi isle (smoke test)")
    ayrac.add_argument("--beklenen-kare", type=int,
                        help="Kapida islenmesi zorunlu kesin kare sayisi")
    ayrac.add_argument("--cikti", type=Path, default=varsayilan)
    return ayrac.parse_args()


def main() -> int:
    """Ham kaynaklari iki kipte degerlendir; bindirmelere asla model calistirma."""
    args = argumanlar()
    if args.imgsz < 32 or args.imgsz % 32 or args.video_basina < 1:
        print("HATA: --imgsz 32 kati, --video-basina >= 1 olmali", file=sys.stderr)
        return 2
    for yol in (args.navitas_model, args.arac_model):
        if not yol.is_file():
            print(f"HATA: Model bulunamadi: {yol}", file=sys.stderr)
            return 2
    cikti = args.cikti.resolve()
    cikti.mkdir(parents=True, exist_ok=True)
    once_referans_sayfasi(cikti)

    # Bu iki isim, kopyalama olmadigini calisma aninda da gorunur kilar.
    assert callable(bir_kare_isle) and callable(_rota_uret) and callable(_min_aciklik_araca_px)
    navitas_model = YOLO(str(args.navitas_model), task="segment")
    arac_model = YOLO(str(args.arac_model))

    adaylar: list[tuple[str, str, int, np.ndarray]] = []
    for ad in VARSAYILAN_GORSELLER:
        yol = KOK / ad
        gorsel = cv2.imread(str(yol))
        if gorsel is None:
            print(f"UYARI: ham foto okunamadi/eksik: {yol}")
            continue
        if gorsel.shape[:2] != (900, 1600):
            print(f"UYARI: beklenen ham 1600x900 degil, atlandi: {yol.name} {gorsel.shape[1]}x{gorsel.shape[0]}")
            continue
        adaylar.append((ad, "foto", 0, gorsel))
    for ad in VARSAYILAN_VIDEOLAR:
        yol = KOK / ad
        if not yol.is_file():
            print(f"UYARI: ham video eksik: {yol}")
            continue
        try:
            adaylar.extend((ad, "video", kare_no, kare) for kare_no, kare in video_kareleri(yol, args.video_basina))
        except OSError as exc:
            print(f"UYARI: {exc}")
    if args.sinir is not None:
        adaylar = adaylar[:max(0, args.sinir)]
    if not adaylar:
        print("HATA: Islenecek ham kaynak yok", file=sys.stderr)
        return 1
    if args.beklenen_kare is not None and len(adaylar) != args.beklenen_kare:
        print(f"HATA: Beklenen {args.beklenen_kare} kare yerine {len(adaylar)} kare hazirlandi",
              file=sys.stderr)
        return 1

    sonuclar: list[KareSonucu] = []
    sonra_ogeler: list[tuple[str, np.ndarray]] = []
    for sira, (kaynak, tur, kare_no, bgr) in enumerate(adaylar, start=1):
        ad = guvenli_ad(f"{Path(kaynak).stem}_{kare_no:06d}")
        sonuc = bir_kare_isle(
            bgr, navitas_model, arac_model, imgsz=args.imgsz, conf=args.conf,
            arac_conf=args.arac_conf,
            cikti_dir=cikti, ad=ad,
        )
        kayit = sonuc_donustur(kaynak, tur, kare_no, sonuc)
        sonuclar.append(kayit)
        gorsel = cv2.imread(str(cikti / f"{ad}.jpg"))
        if gorsel is not None:
            sonra_ogeler.append((f"SONRA ham={kayit.ham_ihlal} enjekte={kayit.enjekte_ihlal}: {ad}", gorsel))
        print(f"[{sira}/{len(adaylar)}] {tur} {Path(kaynak).name}#{kare_no}: "
              f"ham_ihlal={kayit.ham_ihlal} enjekte_ihlal={kayit.enjekte_ihlal}")

    kontakt_sayfasi(sonra_ogeler, cikti / "sonra_iki_kip_costmap.jpg", sutun=3)
    ozet = guvenlik_ozeti(sonuclar)
    n_olcekli = ozet["olcekli_kare"]
    n_olceksiz = ozet["olceksiz_kare"]
    ham_ihlal = ozet["ham_ihlal"]
    ham_oran = ozet["ham_ihlal_orani"]
    enj_ihlal = ozet["enjekte_ihlal"]
    enj_tam_sifir = ozet["enjekte_kesisim_dilate_arac_r_gerekli_tam_sifir"]
    ham_guclu = ozet["ham_test_guclu"]
    atomik_json_yaz(cikti / "ozet.json", {"ozet": ozet, "kareler": [asdict(kayit) for kayit in sonuclar]})
    print("=" * 72)
    print(f"OLCEKLI / OLCEKSIZ: {n_olcekli} / {n_olceksiz}")
    if n_olcekli == 0:
        print("HAM ihlal orani: OLCUM_YOK")
        print("ENJEKTE rota kesisimi: OLCUM_YOK")
    else:
        print(f"HAM ihlal orani: {ham_oran:.3f} ({ham_ihlal}/{n_olcekli}) — BEKLENEN > 0.10")
        print(f"ENJEKTE rota ∩ dilate(arac, r_gerekli): {'TAM 0' if enj_tam_sifir else f'IHLAL {enj_ihlal}'}")
    if n_olcekli == 0:
        print("[OLCUM_YOK] Fiziksel olcegi bilinen kare yok; guvenlik karari uretilmedi.")
    elif not ham_guclu:
        print("[GUCSUZ] Ham ihlal orani <= 0.10. Bu veri kumesi bildirilen kusuru yeterince tetiklemiyor;")
        print("         sonuc TEMIZ degil, GUCSUZ kabul edilmelidir.")
    if ozet["durum"] == "KISMI_OLCUM":
        print("[KISMI_OLCUM] Olceksiz kareler guvenlik paydasina alinmadi; tam gecis yok.")
    elif n_olcekli > 0:
        if not enj_tam_sifir:
            print("[KALDI] Enjekte kipte ihlal var: kusur algi degil costmap geometrisindedir.")
        elif ozet["enjekte_karar_var"] == 0:
            print("[OLCUM_YOK] Enjekte kipte 0 rota karari var; sifir ihlal sonucu vakumdur.")
        elif ham_guclu:
            print("[GECTI] Enjekte kipte her rota, genisletilmis arac alanindan tam uzakta.")
    print(f"CIKTI: {cikti}")
    # Gucsuz test sessiz basari sayilmaz; ama uretim kodunu degil test verisini isaret eder.
    return ozet_cikis_kodu(ozet)


if __name__ == "__main__":
    raise SystemExit(main())
