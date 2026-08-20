"""NEDEN: T40'in agir model kosusunu kaydedilmis yer gerceginden tekrar olcer.

KESIF MUAFIYETI: agir model kosusu gerektiren ELLE kapi; unittest kesfinde
  kosulamaz (takim kapisini dakikalarca bloklar ve GPU ister).
KOSUM: O:\\navitas-local-train\\venv\\Scripts\\python.exe -B tests/arena_kompozit_kapisi.py

Bu betik unittest kesfine girmez. Kompozit kare karar mantigini sinar; modelin
gercek arenadaki basarimini veya arena domain boslugunun kapandigini iddia etmez.
Ureticinin kendi rota sonucuyla ornek elemesine izin vermez: rota ve pozitif
kontrol, yazimdan sonra bu bagimsiz kapida yeniden hesaplanir.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
for yol in (KOK / "scripts", KOK / "codes", KOK):
    if str(yol) not in sys.path:
        sys.path.insert(0, str(yol))

from copy_paste_augmentation import (  # noqa: E402
    ARENA_ARAC_KAPSAMA_ESIGI,
    ARENA_HEDEF_KENAR_M,
    _pencerede_ust_alt_bileseni,
    arena_hedefini_ciz,
    arena_rotasi,
    arena_serit_haritasi,
    yolo_sinif_maskesi,
)
from costmap_path_finder import serbest_alan  # noqa: E402
from karar_sozlesmesi import hedef_bant_yuksekligi, serit_no  # noqa: E402
from sinif_semasi import ENGEL, HEDEF, ZEMIN  # noqa: E402


ROTA_ELEME_ONEKLERI = (
    "arena_rota_uyusmazligi",
    "pozitif_kontrol_acik_kaldi",
)


def agac_sha256(kok: Path) -> str:
    """Goreli adlari ve dosya baytlarini tek deterministik SHA'da birlestir."""
    ozet = hashlib.sha256()
    for yol in sorted(p for p in kok.rglob("*") if p.is_file()):
        ozet.update(yol.relative_to(kok).as_posix().encode("utf-8"))
        ozet.update(b"\0")
        ozet.update(yol.read_bytes())
        ozet.update(b"\0")
    return ozet.hexdigest()


def maske_oku(yol: Path) -> np.ndarray:
    """Kayipsiz ikili maskeyi ac; eksigi sessiz bos kabul etme."""
    maske = cv2.imread(str(yol), cv2.IMREAD_GRAYSCALE)
    if maske is None:
        raise OSError(f"Maske okunamadi: {yol}")
    maske = np.squeeze(maske)
    if maske.ndim != 2:
        raise ValueError(f"Maske iki boyutlu degil: {yol} {maske.shape}")
    return (maske > 0).astype(np.uint8)


def renk_kaniti(
    resim: np.ndarray,
    hedef_kutu: tuple[int, int, int, int],
) -> tuple[bool, bool]:
    """Uretim yordamindan turetilen bolgelerde salt kanal siralamasini olc."""
    beklenen = np.zeros_like(resim)
    arena_hedefini_ciz(beklenen, hedef_kutu)
    h_bolgesi = (np.all(beklenen == beklenen[:, :, :1], axis=2) &
                 np.any(beklenen > 0, axis=2))
    kirmizi_bolge = ((beklenen[:, :, 2] > 0) & ~h_bolgesi)
    if not h_bolgesi.any() or not kirmizi_bolge.any():
        return False, False
    kirmizi = resim[kirmizi_bolge].astype(np.float64)
    h = resim[h_bolgesi].astype(np.float64)
    kirmizi_var = bool(
        kirmizi[:, 2].mean() > kirmizi[:, 1].mean() and
        kirmizi[:, 2].mean() > kirmizi[:, 0].mean()
    )
    # Beyaz H'nin en dusuk kanali bile kirmizi branda bolgesinin en dusuk
    # kanalindan parlak olmali. Sayisal esik yoktur; cizim geometrisi dogrudan
    # uretimde kullanilan yordamdan gelir.
    h_var = bool(h.min(axis=1).mean() > kirmizi.min(axis=1).mean())
    return kirmizi_var, h_var


def kaynak_resmi(manifest: dict, ornek: dict) -> np.ndarray | None:
    """Manifestteki kaynak kareyi, gorunur moloz kaniti icin geri ac."""
    girdi = Path(manifest["parametreler"]["girdi"])
    if not girdi.is_absolute():
        girdi = KOK / girdi
    return cv2.imread(str(girdi / ornek["kaynak"]), cv2.IMREAD_COLOR)


def jpeg_yeniden_kodla(resim: np.ndarray, kalite: int) -> np.ndarray:
    """Kaynak kareyi ureticiyle ayni JPEG kalitesinde karsilastirma tabanina cevir."""
    tamam, kodlu = cv2.imencode(".jpg", resim, [cv2.IMWRITE_JPEG_QUALITY, kalite])
    if not tamam:
        raise OSError("Kaynak JPEG yeniden kodlanamadi")
    sonuc = cv2.imdecode(kodlu, cv2.IMREAD_COLOR)
    if sonuc is None:
        raise OSError("Kaynak JPEG yeniden acilamadi")
    return sonuc


def maske_kutusu(maske: np.ndarray) -> list[int] | None:
    """Bos olmayan ikili maskenin kayipsiz x/y/w/h kutusunu dondur."""
    ys, xs = np.nonzero(maske)
    if xs.size == 0:
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1),
            int(ys.max() - ys.min() + 1)]


def pencere_kapsar(
    pencere: object,
    ic_kutu: list[int] | None,
    sekil: tuple[int, int],
) -> bool:
    """Manifest penceresinin tuval icinde olup exact maskeyi kapsadigini denetle."""
    if not isinstance(pencere, list) or len(pencere) != 4 or ic_kutu is None:
        return False
    try:
        x, y, w, h = map(int, pencere)
    except (TypeError, ValueError):
        return False
    ix, iy, iw, ih = ic_kutu
    return (
        x >= 0 and y >= 0 and w > 0 and h > 0 and
        x + w <= sekil[1] and y + h <= sekil[0] and
        x <= ix and y <= iy and x + w >= ix + iw and y + h >= iy + ih
    )


def main() -> int:
    """Persist edilen orneklerin bagimsiz T40 kapilarini olc."""
    ayrac = argparse.ArgumentParser()
    ayrac.add_argument("--veri", type=Path, default=KOK / "data" / "arena_kompozit")
    args = ayrac.parse_args()
    veri = args.veri.resolve()
    try:
        manifest = json.loads((veri / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError) as exc:
        print(f"[T40_KAPI] HATA manifest okunamadi: {exc}")
        return 1
    parametreler = manifest.get("parametreler", {})
    ornekler = manifest.get("ornekler", [])
    yazilan = [o for o in ornekler if o.get("durum") == "YAZILDI"]
    if not yazilan:
        print("[T40_KAPI] HATA yazilmis kompozit yok")
        return 1

    hatalar: Counter[str] = Counter()
    durumlar: Counter[str] = Counter()
    pozitif_durumlar: Counter[str] = Counter()
    acik_seritler: Counter[int] = Counter()
    arac_px = kapsanan_px = bariyer_px = bariyer_kapsanan_px = 0
    serbest_artan = 0

    if parametreler.get("kip") != "arena":
        hatalar["kip_arena_degil"] += 1
    if Path(str(parametreler.get("zemin_model", ""))).name != "navitas_seg_v21_best.pt":
        hatalar["zemin_model_v21_degil"] += 1
    if parametreler.get("arac_kahini") != "DOTA-OBB":
        hatalar["arac_kahini_dota_obb_degil"] += 1
    if "obb" not in Path(str(parametreler.get("arac_model", ""))).name.lower():
        hatalar["arac_model_obb_degil"] += 1
    if not parametreler.get("arena_karar_mantigi_kaniti", False):
        hatalar["karar_kaniti_bildirimi_yok"] += 1
    if parametreler.get("arena_model_basarimi_kaniti", True):
        hatalar["model_basarimi_yanlis_iddia"] += 1
    if parametreler.get("arena_domain_boslugu_kapandi", True):
        hatalar["domain_boslugu_yanlis_iddia"] += 1

    # SUT kendi yanlis kararlarini ATLANDI yaparak kapidan gizleyemez.
    rota_ile_elenen = [
        o for o in ornekler
        if any(str(o.get("sebep", "")).startswith(on) for on in ROTA_ELEME_ONEKLERI)
    ]
    hatalar["rota_sonucuyla_elenen"] += len(rota_ile_elenen)

    for ornek in yazilan:
        try:
            arena = ornek["arena"]
            yollar = {ad: veri / yol for ad, yol in arena["maskeler"].items()}
            zemin = maske_oku(yollar["zemin"])
            engel = maske_oku(yollar["engel"])
            arac = maske_oku(yollar["arac"])
            hedef = maske_oku(yollar["hedef"])
            bariyer = maske_oku(yollar["bariyer"])
            pozitif_bariyer = maske_oku(yollar["pozitif_bariyer"])
            resim = cv2.imread(str(veri / ornek["cikti"]), cv2.IMREAD_COLOR)
            if resim is None:
                raise OSError(f"Resim okunamadi: {ornek['cikti']}")
        except (KeyError, OSError, ValueError, TypeError) as exc:
            print(f"[T40_ORNEK_HATA] {ornek.get('kaynak')}: {exc}")
            hatalar["dosya_veya_manifest_eksik"] += 1
            continue

        if any(m.shape != zemin.shape for m in
               (engel, arac, hedef, bariyer, pozitif_bariyer)) or resim.shape[:2] != zemin.shape:
            hatalar["boyut_uyusmazligi"] += 1
            continue
        bos = np.zeros_like(zemin)
        icerik = tuple(arena["icerik"])
        mpp = float(arena["mpp"])
        acik_serit = int(arena["acik_serit"])
        acik_seritler[acik_serit] += 1

        sonuc = arena_rotasi(zemin, engel, bos, bos, mpp=mpp, icerik=icerik)
        durumlar[sonuc["durum"]] += 1
        if sonuc["durum"] != "ACIK" or sonuc["yol_no"] != acik_serit:
            hatalar["rota_uyumsuz"] += 1

        # Bariyerin kendisi, gercek arka plan engellerinden bagimsiz olarak iki
        # koridoru kapatabilmeli. Boylece park halindeki araclar bariyer acigini
        # tesadufen ortemez.
        yalniz_bariyer = arena_rotasi(
            zemin, bariyer, bos, bos, mpp=mpp, icerik=icerik)
        if yalniz_bariyer["durum"] != "ACIK" or yalniz_bariyer["yol_no"] != acik_serit:
            hatalar["exact_bariyer_koridoru_kesmiyor"] += 1

        pozitif = arena_rotasi(
            zemin, engel, bos, pozitif_bariyer, mpp=mpp, icerik=icerik)
        pozitif_durumlar[pozitif["durum"]] += 1
        if pozitif["durum"] == "ACIK":
            hatalar["pozitif_acik_kaldi"] += 1

        k1 = serbest_alan({ZEMIN: zemin, ENGEL: bos}, mpp=mpp, icerik=icerik)["serbest"]
        k12 = serbest_alan({ZEMIN: zemin, ENGEL: engel}, mpp=mpp, icerik=icerik)["serbest"]
        serbest_artan += int(((k12 > 0) & (k1 == 0)).sum())

        etiket = (veri / arena["etiket"]).read_text(encoding="utf-8")
        yazilan_engel = yolo_sinif_maskesi(etiket, zemin.shape, ENGEL)
        yazilan_hedef = yolo_sinif_maskesi(etiket, zemin.shape, HEDEF)
        bu_arac_px = int(arac.sum())
        bu_arac_kapsanan = int(((arac > 0) & (yazilan_engel > 0)).sum())
        bu_arac_kapsama = bu_arac_kapsanan / bu_arac_px if bu_arac_px else 0.0
        arac_px += bu_arac_px
        kapsanan_px += bu_arac_kapsanan
        if bu_arac_px == 0 or bu_arac_kapsama < ARENA_ARAC_KAPSAMA_ESIGI:
            hatalar["kare_bazli_arac_kapsama_dusuk"] += 1
        if arena.get("arac_kapsanan_px") != bu_arac_kapsanan:
            hatalar["arac_kapsama_tanisi_bayat"] += 1

        bu_bariyer_px = int(bariyer.sum())
        bu_bariyer_kapsanan = int(((bariyer > 0) & (yazilan_engel > 0)).sum())
        bariyer_px += bu_bariyer_px
        bariyer_kapsanan_px += bu_bariyer_kapsanan
        if (bu_bariyer_px == 0 or
                bu_bariyer_kapsanan / bu_bariyer_px < ARENA_ARAC_KAPSAMA_ESIGI):
            hatalar["exact_bariyer_etiket_kapsama_dusuk"] += 1
        if np.any(bariyer & hedef) or np.any(engel & hedef):
            hatalar["hedef_engel_cakismasi"] += 1
        if int(hedef.sum()) == 0 or not np.all(yazilan_hedef[hedef > 0] > 0):
            hatalar["hedef_class2_etiketinde_eksik"] += 1
        if np.any((bariyer > 0) & (engel == 0)):
            hatalar["exact_bariyer_engelde_yok"] += 1

        hedef_px = int(hedef.sum())
        ys, xs = np.nonzero(hedef)
        if hedef_px == 0:
            hatalar["hedef_bos"] += 1
        else:
            kutu = [int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1),
                    int(ys.max() - ys.min() + 1)]
            beklenen_kenar = int(round(ARENA_HEDEF_KENAR_M / mpp))
            if arena.get("hedef_kaynagi") != "prosedurel_2m_kirmizi_H":
                hatalar["hedef_kaynagi_prosedurel_degil"] += 1
            if kutu != list(arena.get("hedef_kutu", [])):
                hatalar["hedef_kutu_bayat"] += 1
            if kutu[2:] != [beklenen_kenar, beklenen_kenar] or hedef_px != beklenen_kenar ** 2:
                hatalar["hedef_2m_kare_degil"] += 1
            x0, y0, w, h = map(int, icerik)
            if kutu[1] < y0 or kutu[1] + kutu[3] > y0 + hedef_bant_yuksekligi(h):
                hatalar["hedef_ust_bantta_degil"] += 1
            hedef_seritleri = {
                serit_no(int(x), x0, w) for x in xs
                if x0 <= int(x) < x0 + w
            }
            if hedef_seritleri != {acik_serit}:
                hatalar["hedef_acik_seritte_degil"] += 1
            kirmizi_var, h_var = renk_kaniti(resim, tuple(kutu))
            if not kirmizi_var:
                hatalar["kirmizi_branda_gorunmuyor"] += 1
            if not h_var:
                hatalar["beyaz_h_gorunmuyor"] += 1

        taban = None
        kaynak = kaynak_resmi(manifest, ornek)
        if kaynak is None or kaynak.shape != resim.shape:
            hatalar["kaynak_resim_okunamadi"] += 1
        elif bu_bariyer_px:
            try:
                taban = jpeg_yeniden_kodla(kaynak, int(parametreler["jpeg_kalite"]))
            except (KeyError, OSError, TypeError, ValueError):
                hatalar["jpeg_kalite_veya_taban_gecersiz"] += 1
                taban = None
            if taban is not None and not np.any(resim[bariyer > 0] != taban[bariyer > 0]):
                hatalar["exact_bariyer_jpegde_gorunmuyor"] += 1

        seritler = arena_serit_haritasi(zemin.shape, icerik)
        bariyer_kayitlari = {
            int(b["serit"]): b for b in arena.get("bariyerler", [])
        }
        meta_seritler = set(bariyer_kayitlari)
        beklenen_kapali = set(map(int, arena.get("kapali_seritler", [])))
        if meta_seritler != beklenen_kapali or beklenen_kapali != ({1, 2, 3} - {acik_serit}):
            hatalar["bariyer_manifest_seritleri_yanlis"] += 1
        for serit in beklenen_kapali:
            serit_bariyeri = ((bariyer > 0) & (seritler == serit))
            if not np.any(serit_bariyeri):
                hatalar["kapali_seritte_exact_bariyer_yok"] += 1
            elif taban is not None and not np.any(resim[serit_bariyeri] != taban[serit_bariyeri]):
                hatalar["kapali_seritte_moloz_jpegde_yok"] += 1
            kayit = bariyer_kayitlari.get(serit, {})
            exact_kutu = maske_kutusu(serit_bariyeri)
            if (kayit.get("kutu") != exact_kutu or
                    kayit.get("gercek_px") != int(serit_bariyeri.sum()) or
                    kayit.get("yerel_once_bagli") is not True or
                    kayit.get("yerel_sonra_bagli") is not False or
                    not pencere_kapsar(kayit.get("pencere"), exact_kutu, zemin.shape)):
                hatalar["exact_bariyer_manifest_kaniti_bayat"] += 1
            taban_engel = ((engel > 0) & (bariyer == 0)).astype(np.uint8)
            once = (
                (zemin > 0) & (seritler == serit) & (taban_engel == 0)
            ).astype(np.uint8)
            sonra = (once & ~serit_bariyeri).astype(np.uint8)
            try:
                once_bagli = _pencerede_ust_alt_bileseni(
                    once, tuple(kayit.get("pencere", ()))) is not None
                sonra_bagli = _pencerede_ust_alt_bileseni(
                    sonra, tuple(kayit.get("pencere", ()))) is not None
            except (IndexError, TypeError, ValueError):
                once_bagli, sonra_bagli = False, True
            if not once_bagli or sonra_bagli:
                hatalar["exact_bariyer_yerel_kesme_kaniti_yok"] += 1

        pozitif_meta = arena.get("pozitif_bariyer", {})
        pozitif_kutu = maske_kutusu(pozitif_bariyer)
        if (pozitif_meta.get("kutu") != pozitif_kutu or
                pozitif_meta.get("gercek_px") != int(pozitif_bariyer.sum()) or
                pozitif_meta.get("yerel_once_bagli") is not True or
                pozitif_meta.get("yerel_sonra_bagli") is not False or
                not pencere_kapsar(
                    pozitif_meta.get("pencere"), pozitif_kutu, zemin.shape) or
                np.any((pozitif_bariyer > 0) & (seritler != acik_serit)) or
                np.any(pozitif_bariyer & hedef)):
            hatalar["pozitif_exact_bariyer_manifest_kaniti_bayat"] += 1
        pozitif_once = (
            (zemin > 0) & (seritler == acik_serit) & (engel == 0)
        ).astype(np.uint8)
        pozitif_sonra = (
            pozitif_once & ~(pozitif_bariyer > 0)
        ).astype(np.uint8)
        try:
            pozitif_once_bagli = _pencerede_ust_alt_bileseni(
                pozitif_once, tuple(pozitif_meta.get("pencere", ()))) is not None
            pozitif_sonra_bagli = _pencerede_ust_alt_bileseni(
                pozitif_sonra, tuple(pozitif_meta.get("pencere", ()))) is not None
        except (IndexError, TypeError, ValueError):
            pozitif_once_bagli, pozitif_sonra_bagli = False, True
        if not pozitif_once_bagli or pozitif_sonra_bagli:
            hatalar["pozitif_exact_yerel_kesme_kaniti_yok"] += 1

    kapsama = kapsanan_px / arac_px if arac_px else 0.0
    bariyer_kapsama = bariyer_kapsanan_px / bariyer_px if bariyer_px else 0.0
    print(f"[T40_KAPI] kompozit={len(yazilan)} ACIK={durumlar['ACIK']} "
          f"rota_ile_elenen={len(rota_ile_elenen)} "
          f"acik_seritler={dict(sorted(acik_seritler.items()))}")
    print(f"[T40_POZITIF] kapatilan={len(yazilan)} "
          f"durumlar={dict(sorted(pozitif_durumlar.items()))}")
    print(f"[T40_ARAC] arac_px={arac_px} kapsanan_px={kapsanan_px} "
          f"kapsama_yuzde={100.0 * kapsama:.3f} kare_bazli_dusuk="
          f"{hatalar['kare_bazli_arac_kapsama_dusuk']}")
    print(f"[T40_BARIYER] exact_px={bariyer_px} kapsanan_px={bariyer_kapsanan_px} "
          f"kapsama_yuzde={100.0 * bariyer_kapsama:.3f}")
    print(f"[T40_MADDE15] serbest_artan={serbest_artan}")
    print(f"[T40_HATALAR] {dict(sorted(hatalar.items()))}")
    print(f"[T40_SHA256] {agac_sha256(veri)}")
    print("[T40_SINIR] Kompozit kume karar mantigini sinar; model basarimini veya "
          "gercek arena domainini sinamaz.")
    return 0 if not any(hatalar.values()) and serbest_artan == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
