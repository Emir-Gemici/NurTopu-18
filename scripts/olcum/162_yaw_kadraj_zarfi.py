"""B3 — uretim kararinin kontrollu yaw/kadraj bozulma zarfini olcer.

NEDEN: kabul kumesi merkezlenmis `kip=kadraj` karelerinden olusur; bu nedenle
mevcut kabul kapilari dronun yonelim veya kadraj hatasinda rotanin ne zaman
koptugunu olcemez. Bu betik model secmez/egitmez. Dondurulmus bir orneklemin
goruntusunu ve YOLO-segment etiketini AYNI affine matrisle bozar, sonra her
goruntuyu uretim cagri sirasindan gecirir:

    _preprocess -> model.predict -> get_masks (results LISTESI)
    -> _maskeleri_icerige_kirp -> analyze_path

Kabul olcutu ve gerekli saha araligi sonuc gorulmeden once
`results/yaw_zarfi/ON_KAYIT.md` dosyasinda sabitlenmistir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[2]
for _yol in (KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from karar_sozlesmesi import rota_olcek_reddi  # noqa: E402
from model_registry import load_registry, resolve_model  # noqa: E402
from rpi_inference import (  # noqa: E402
    INFER_SIZE,
    _maskeleri_icerige_kirp,
    _preprocess,
    _rota_kararini_esikle,
    analyze_path,
    get_masks,
)
from sinif_semasi import EGITIM_SINIF_ADLARI, ENGEL, ZEMIN  # noqa: E402


ON_KAYIT_YOLU = KOK / "results" / "yaw_zarfi" / "ON_KAYIT.md"
# Ilk olcumden once ana oturum tarafindan kaydedilen on-kayit ozeti. Bu kontrol
# sonuc goruldukten sonra olcut metninin sessizce degistirilmesini engeller.
ON_KAYIT_SHA256 = "e7ad76fffb69922913c6bc51dbcb50362c5b9a280f8f8ed56085db82a83a192a"

ON_KAYIT_N = 12
AZAMI_N = 40
CONF = 0.30
YAW_DEGERLERI = tuple(range(-30, 31, 5))
KAYMA_YUZDELERI = (5, 10, 15, 20)
ROTA_KABUL_ORANI = 0.90
SERIT_KABUL_ORANI = 0.95
KIRILMA_ORANI = 0.90
GEREKLI_YAW = 10
GEREKLI_KAYMA = 10
# `_preprocess` letterbox dolgusuyla ayni deger. FOV disini yansitmak gercek
# doku UYDURUP dayanimi yapay yukseltirdi; sabit dolgu bu nedenle fail-closed.
GORUNTU_DOLGU_DEGERI = 114


def kadraj_durumlari() -> tuple[dict, ...]:
    """On kayittaki merkez + dort yonlu kadraj izgara hucreleri."""
    durumlar = [{"ad": "merkez", "x_pct": 0, "y_pct": 0,
                 "buyukluk_pct": 0}]
    for yuzde in KAYMA_YUZDELERI:
        durumlar.extend((
            {"ad": f"x-{yuzde:02d}", "x_pct": -yuzde, "y_pct": 0,
             "buyukluk_pct": yuzde},
            {"ad": f"x+{yuzde:02d}", "x_pct": yuzde, "y_pct": 0,
             "buyukluk_pct": yuzde},
            {"ad": f"y-{yuzde:02d}", "x_pct": 0, "y_pct": -yuzde,
             "buyukluk_pct": yuzde},
            {"ad": f"y+{yuzde:02d}", "x_pct": 0, "y_pct": yuzde,
             "buyukluk_pct": yuzde},
        ))
    return tuple(durumlar)


KADRAJ_DURUMLARI = kadraj_durumlari()


def on_kayit_dogrula(yol: Path = ON_KAYIT_YOLU) -> str:
    """On kaydin olcum oncesinde dondurulmus metin oldugunu dogrula."""
    if not yol.is_file():
        raise RuntimeError(f"on kayit yok: {yol}")
    # Git `core.autocrlf=true` ile ayni metni Windows'ta CRLF, depoda LF
    # saklayabilir. Icerigi kanonik LF olarak ozetle; satir-sonu donusumu
    # "olcumden sonra degisti" diye yanlis alarm uretmesin.
    metin = yol.read_bytes().decode("utf-8")
    kanonik = metin.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    ozet = hashlib.sha256(kanonik).hexdigest()
    if ozet != ON_KAYIT_SHA256:
        raise RuntimeError(
            "on kayit olcumden sonra degismis olabilir: "
            f"beklenen={ON_KAYIT_SHA256} gercek={ozet}"
        )
    return ozet


def affine_matrisi(sekil: tuple[int, ...], yaw_derece: float,
                   x_pct: float, y_pct: float) -> np.ndarray:
    """Yaw + kadraj merkezi kaymasini tek bir 2x3 matriste birlestirir.

    `x_pct > 0`, kadraj merkezinin saga kaymasidir; gorulen icerik bu nedenle
    sola tasinir. `y_pct > 0` da merkez asagi kayarken icerigi yukari tasir.
    """
    if len(sekil) < 2 or int(sekil[0]) <= 0 or int(sekil[1]) <= 0:
        raise ValueError(f"gecersiz goruntu sekli: {sekil}")
    h, w = int(sekil[0]), int(sekil[1])
    merkez = ((w - 1) / 2.0, (h - 1) / 2.0)
    matris = cv2.getRotationMatrix2D(merkez, float(yaw_derece), 1.0)
    matris[0, 2] -= float(x_pct) * w / 100.0
    matris[1, 2] -= float(y_pct) * h / 100.0
    return matris.astype(np.float64, copy=False)


def _maskeleri_affine_donustur(etiketler: dict[int, np.ndarray],
                               matris: np.ndarray,
                               boyut: tuple[int, int]) -> dict[int, np.ndarray]:
    """Tum etiket kanallarini goruntuyle ayni matrisle, fail-closed dondurur."""
    return {
        int(sinif): cv2.warpAffine(
            np.asarray(maske, dtype=np.uint8), matris, boyut,
            flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT,
            borderValue=0,
        )
        for sinif, maske in etiketler.items()
    }


def goruntu_ve_etiketi_donustur(
        goruntu: np.ndarray, etiketler: dict[int, np.ndarray],
        yaw_derece: float, x_pct: float, y_pct: float,
) -> tuple[np.ndarray, dict[int, np.ndarray], np.ndarray]:
    """Goruntu ve etikete AYNI affine matrisi uygular (test edilebilir saf cekirdek)."""
    h, w = goruntu.shape[:2]
    boyut = (w, h)
    matris = affine_matrisi(goruntu.shape, yaw_derece, x_pct, y_pct)
    donusmus_goruntu = cv2.warpAffine(
        goruntu, matris, boyut, flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(GORUNTU_DOLGU_DEGERI,) * 3,
    )
    donusmus_etiketler = _maskeleri_affine_donustur(etiketler, matris, boyut)
    return donusmus_goruntu, donusmus_etiketler, matris


def yolo_etiket_maskeleri(yol: Path, h: int, w: int) -> dict[int, np.ndarray]:
    """YOLO-segment poligonlarini sinif basina ikili raster maskeye cevirir."""
    maskeler = {int(c): np.zeros((h, w), dtype=np.uint8)
                for c in EGITIM_SINIF_ADLARI}
    if not yol.is_file():
        raise FileNotFoundError(f"etiket yok: {yol}")
    for satir_no, satir in enumerate(yol.read_text(encoding="utf-8").splitlines(), 1):
        parca = satir.split()
        if not parca:
            continue
        if len(parca) < 7 or len(parca[1:]) % 2:
            raise ValueError(f"bozuk YOLO poligonu: {yol}:{satir_no}")
        sinif = int(parca[0])
        if sinif not in maskeler:
            raise ValueError(f"bilinmeyen sinif {sinif}: {yol}:{satir_no}")
        koord = np.asarray([float(v) for v in parca[1:]], dtype=np.float64)
        koord = koord.reshape(-1, 2)
        if not np.isfinite(koord).all():
            raise ValueError(f"sonlu olmayan koordinat: {yol}:{satir_no}")
        koord[:, 0] = np.clip(koord[:, 0] * w, 0, w - 1)
        koord[:, 1] = np.clip(koord[:, 1] * h, 0, h - 1)
        cv2.fillPoly(maskeler[sinif], [np.rint(koord).astype(np.int32)], 1)
    return maskeler


def _etiket_yolu(kume: Path, goruntu_goreli: Path) -> Path:
    """`images/<bolum>/x.jpg` yolunun YOLO etiket ikizini verir."""
    parcalar = goruntu_goreli.parts
    if len(parcalar) < 3 or parcalar[0] != "images":
        raise ValueError(f"beklenmeyen manifest goruntu yolu: {goruntu_goreli}")
    return kume / "labels" / parcalar[1] / f"{goruntu_goreli.stem}.txt"


def ornekleri_sec(kume: Path, n: int) -> list[dict]:
    """Model sonucuna bakmadan manifest sirasindaki ilk N uygun kareyi secer."""
    if n < 0 or n > AZAMI_N:
        raise ValueError(f"N 0..{AZAMI_N} araliginda olmali: {n}")
    if n == 0:
        return []
    manifest_yolu = kume / "manifest.json"
    manifest = json.loads(manifest_yolu.read_text(encoding="utf-8"))
    secilen = []
    for indis, ornek in enumerate(manifest.get("ornekler") or []):
        arena = ornek.get("arena")
        if ornek.get("durum") != "YAZILDI" or not isinstance(arena, dict):
            continue
        if arena.get("acik_serit") is None:
            continue
        goreli = Path(ornek.get("cikti") or "")
        goruntu = kume / goreli
        etiket = _etiket_yolu(kume, goreli)
        if not goruntu.is_file() or not etiket.is_file():
            continue
        secilen.append({
            "manifest_indisi": indis,
            "kare": goruntu.name,
            "goruntu": goruntu,
            "etiket": etiket,
            "mpp": arena.get("mpp"),
            "manifest_acik_serit": arena.get("acik_serit"),
        })
        if len(secilen) == n:
            break
    return secilen


def uretim_karari(model, goruntu: np.ndarray, mpp: float | None,
                  conf: float = CONF) -> dict:
    """Bir kareyi uretimin birebir cagri sirasindan gecirir."""
    sq, small, icerik = _preprocess(goruntu)
    h, w = sq.shape[:2]
    results = model.predict(
        small, imgsz=INFER_SIZE, conf=conf, verbose=False,
    )
    if not isinstance(results, list):
        raise TypeError(
            "model.predict sonucu LISTE olmali; get_masks'e results[0] verilmez"
        )
    maskeler = get_masks(results, h, w)
    maskeler = _maskeleri_icerige_kirp(maskeler, icerik)
    ham_yol, guven, ham_wps, karar_reddi = analyze_path(
        maskeler[ZEMIN], icerik=icerik, engel_mask=maskeler.get(ENGEL),
        mpp=mpp, return_reason=True,
    )
    olcek_reddi = rota_olcek_reddi(mpp)
    if olcek_reddi is not None and karar_reddi is None:
        ham_yol, guven, ham_wps = None, 0.0, []
        karar_reddi = olcek_reddi
    yol, guven, wps, karar_reddi = _rota_kararini_esikle(
        ham_yol, guven, ham_wps, karar_reddi,
    )
    red = (karar_reddi[0] if isinstance(karar_reddi, (tuple, list))
           else karar_reddi)
    return {
        "yol": int(yol) if yol is not None else None,
        "guven": float(guven),
        "waypoint_n": len(wps or []),
        "red": red,
        "icerik": [int(v) for v in icerik],
    }


def _etiket_ozeti(maskeler: dict[int, np.ndarray]) -> dict:
    """Donusturulmus etiketin kullanildigini ham raporda gorunur kilar."""
    return {
        str(sinif): {
            "piksel": int(np.count_nonzero(maske)),
            "sha256": hashlib.sha256(np.ascontiguousarray(maske).tobytes()).hexdigest(),
        }
        for sinif, maske in sorted(maskeler.items())
    }


def hucresi_ozetle(kayitlar: list[dict], beklenen_n: int) -> dict:
    """Paydalari fail-closed kurar; N=0 asla sessiz gecmez."""
    n = len(kayitlar)
    karsilastirilabilir = sum(1 for k in kayitlar
                             if k.get("temel_yol") is not None)
    rota = sum(1 for k in kayitlar if k.get("yol") is not None)
    ayni = sum(1 for k in kayitlar
               if k.get("temel_yol") is not None
               and k.get("yol") == k.get("temel_yol"))
    rota_orani = rota / n if n else None
    serit_orani = ayni / karsilastirilabilir if karsilastirilabilir else None
    olculebilir = bool(n and n == beklenen_n and karsilastirilabilir)
    if not olculebilir:
        durum = "OLCULEMEDI"
        gecti = False
    else:
        gecti = bool(rota_orani >= ROTA_KABUL_ORANI
                     and serit_orani >= SERIT_KABUL_ORANI)
        durum = "GECTI" if gecti else "DUSTU"
    return {
        "durum": durum,
        "gecti": gecti,
        "n": n,
        "beklenen_n": beklenen_n,
        "rota": rota,
        "rota_orani": rota_orani,
        "temel_serit_karsilastirilabilir": karsilastirilabilir,
        "ayni_serit": ayni,
        "ayni_serit_orani": serit_orani,
    }


def _hucreleri_birlestir(hucreler: list[dict]) -> dict:
    """Kirilma icin yonlerin EN KOTU oranini dondurur; iyi yon kotuyu gizlemez."""
    if not hucreler or any(h["ozet"]["durum"] == "OLCULEMEDI" for h in hucreler):
        return {"durum": "OLCULEMEDI", "rota_orani": None,
                "ayni_serit_orani": None}
    yonler = [{"yaw": h["yaw_derece"], "kadraj": h["kadraj"]["ad"],
               "rota_orani": h["ozet"]["rota_orani"],
               "ayni_serit_orani": h["ozet"]["ayni_serit_orani"]}
              for h in hucreler]
    return {
        "durum": "OLCUM",
        "rota_orani": min(y["rota_orani"] for y in yonler),
        "ayni_serit_orani": min(y["ayni_serit_orani"] for y in yonler),
        "birlesim": "EN_KOTU_YON",
        "yonler": yonler,
    }


def kirilmalari_bul(hucreler: list[dict]) -> dict:
    """On kayittaki <%90 kirilma tanimini yaw ve kadraj ekseninde uygular."""
    indeks = {(h["yaw_derece"], h["kadraj"]["ad"]): h for h in hucreler}
    yaw_gruplari = []
    yaw_kirilma = None
    for aci in range(0, 31, 5):
        isaretler = (0,) if aci == 0 else (-aci, aci)
        grup = _hucreleri_birlestir([indeks[(y, "merkez")] for y in isaretler])
        grup["mutlak_yaw"] = aci
        yaw_gruplari.append(grup)
        if (yaw_kirilma is None and grup["durum"] != "OLCULEMEDI"
                and (grup["rota_orani"] < KIRILMA_ORANI
                     or grup["ayni_serit_orani"] < KIRILMA_ORANI)):
            yaw_kirilma = aci

    kadraj_gruplari = []
    kadraj_kirilma = None
    for yuzde in (0,) + KAYMA_YUZDELERI:
        adlar = (["merkez"] if yuzde == 0 else
                 [f"x-{yuzde:02d}", f"x+{yuzde:02d}",
                  f"y-{yuzde:02d}", f"y+{yuzde:02d}"])
        grup = _hucreleri_birlestir([indeks[(0, ad)] for ad in adlar])
        grup["kayma_yuzde"] = yuzde
        kadraj_gruplari.append(grup)
        if (kadraj_kirilma is None and grup["durum"] != "OLCULEMEDI"
                and (grup["rota_orani"] < KIRILMA_ORANI
                     or grup["ayni_serit_orani"] < KIRILMA_ORANI)):
            kadraj_kirilma = yuzde
    return {
        "yaw": {"ilk_kirilma_derece": yaw_kirilma,
                "rapor": (f"{yaw_kirilma} derece" if yaw_kirilma is not None
                           else ">30 derece"),
                "gruplar": yaw_gruplari},
        "kadraj": {"ilk_kirilma_yuzde": kadraj_kirilma,
                   "rapor": (f"%{kadraj_kirilma}" if kadraj_kirilma is not None
                              else ">%20"),
                   "gruplar": kadraj_gruplari},
    }


def gerekli_zarfi_degerlendir(hucreler: list[dict]) -> dict:
    """On kayitli ±10 derece / her eksende ±10% dikdortgenini AND ile sinar."""
    gerekli_kadraj = {"merkez"}
    for yuzde in KAYMA_YUZDELERI:
        if yuzde <= GEREKLI_KAYMA:
            gerekli_kadraj.update((f"x-{yuzde:02d}", f"x+{yuzde:02d}",
                                    f"y-{yuzde:02d}", f"y+{yuzde:02d}"))
    gereken = [h for h in hucreler
               if abs(h["yaw_derece"]) <= GEREKLI_YAW
               and h["kadraj"]["ad"] in gerekli_kadraj]
    dusen = [{"yaw": h["yaw_derece"], "kadraj": h["kadraj"]["ad"],
              "durum": h["ozet"]["durum"],
              "rota_orani": h["ozet"]["rota_orani"],
              "ayni_serit_orani": h["ozet"]["ayni_serit_orani"]}
             for h in gereken if not h["ozet"]["gecti"]]
    durum = "GECTI" if gereken and not dusen else "DUSTU"
    if any(h["ozet"]["durum"] == "OLCULEMEDI" for h in gereken):
        durum = "OLCULEMEDI"
    # Merkezden baslayan her aday dikdortgenin BUTUN alt hucrelerini denetle.
    # Sonradan tek bir iyi hucre secilmez; arada dusen varsa daha genis zarf
    # guvenli sayilmaz. Birden cok Pareto ucu varsa koordinat bazinda ortak ic
    # sinir alinir; bu sinir her ucun alt kumesidir ve olcumle kanitlidir.
    adaylar = []
    yaw_adaylari = tuple(range(0, 31, 5))
    kayma_adaylari = (0,) + KAYMA_YUZDELERI
    for yaw_sinir in yaw_adaylari:
        for kayma_sinir in kayma_adaylari:
            dikdortgen = [h for h in hucreler
                           if abs(h["yaw_derece"]) <= yaw_sinir
                           and h["kadraj"]["buyukluk_pct"] <= kayma_sinir]
            if dikdortgen and all(h["ozet"]["gecti"] for h in dikdortgen):
                adaylar.append((yaw_sinir, kayma_sinir))
    pareto = [a for a in adaylar if not any(
        b[0] >= a[0] and b[1] >= a[1] and b != a for b in adaylar
    )]
    if pareto:
        guvenli_yaw = min(a[0] for a in pareto)
        guvenli_kayma = min(a[1] for a in pareto)
        oneri = (f"Dronu su yaw araliginda konumlandirin: "
                 f"-{guvenli_yaw}..+{guvenli_yaw} derece · kadraj kaymasi "
                 f"yatay/dikey eksende en fazla %{guvenli_kayma}.")
    else:
        guvenli_yaw = None
        guvenli_kayma = None
        oneri = ("ONERI URETILEMEDI: merkez hucre bile on kayitli kapiyi "
                 "gecmedi; esik gevsetilmeden duzeltme gerekir.")
    return {"durum": durum, "hucre_n": len(gereken), "dusen_hucreler": dusen,
            "olculen_guvenli_ic_sinir": {
                "yaw_derece": guvenli_yaw,
                "kadraj_yuzde": guvenli_kayma,
                "pareto_ust_sinirlar": [list(a) for a in sorted(pareto)],
            },
            "saha_kontrol_listesi_onerisi": oneri}


def _oran_metni(deger: float | None) -> str:
    return "OLC" if deger is None else f"{100.0 * deger:05.1f}"


def tablo_yaz(hucreler: list[dict]) -> None:
    """Tum yaw x kadraj hucrelerini `rota%/ayni-serit%` biciminde basar."""
    indeks = {(h["yaw_derece"], h["kadraj"]["ad"]): h for h in hucreler}
    adlar = [k["ad"] for k in KADRAJ_DURUMLARI]
    print("\nHAM TABLO · hucre = rota%/ayni-serit%")
    print("yaw\t" + "\t".join(adlar))
    for yaw in YAW_DEGERLERI:
        hucre_metinleri = []
        for ad in adlar:
            ozet = indeks[(yaw, ad)]["ozet"]
            hucre_metinleri.append(
                f"{_oran_metni(ozet['rota_orani'])}/{_oran_metni(ozet['ayni_serit_orani'])}"
            )
        print(f"{yaw:+03d}\t" + "\t".join(hucre_metinleri))


def bos_rapor(neden: str, istenen_n: int, on_kayit_sha: str) -> dict:
    """N=0/eksik ornek capasi: GECTI demeyen yapisal sonuc."""
    return {
        "durum": "OLCULEMEDI",
        "neden": neden,
        "istenen_n": istenen_n,
        "on_kayit_sha256": on_kayit_sha,
        "hucreler": [],
    }


def raporu_yaz(rapor: dict, yol: Path) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(rapor, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")


def olc(model, model_yolu: Path, kume: Path, ornekler: list[dict],
        on_kayit_sha: str) -> dict:
    """Dondurulmus orneklemin temel kararlarini ve tam bozma izgarasini olcer."""
    baslangic = time.perf_counter()
    temeller = []
    for sira, ornek in enumerate(ornekler, 1):
        goruntu = cv2.imread(str(ornek["goruntu"]), cv2.IMREAD_COLOR)
        if goruntu is None:
            raise RuntimeError(f"goruntu okunamadi: {ornek['goruntu']}")
        h, w = goruntu.shape[:2]
        etiketler = yolo_etiket_maskeleri(ornek["etiket"], h, w)
        temel = uretim_karari(model, goruntu, ornek["mpp"])
        temeller.append({**ornek, "goruntu_verisi": goruntu,
                         "etiket_maskeleri": etiketler, "temel_karar": temel})
        print(f"temel {sira:02d}/{len(ornekler)} {ornek['kare']} "
              f"yol={temel['yol']} red={temel['red']}", flush=True)

    hucreler = []
    toplam_hucre = len(YAW_DEGERLERI) * len(KADRAJ_DURUMLARI)
    hucre_sira = 0
    for yaw in YAW_DEGERLERI:
        for kadraj in KADRAJ_DURUMLARI:
            hucre_sira += 1
            kayitlar = []
            for temel in temeller:
                bozuk, bozuk_etiket, matris = goruntu_ve_etiketi_donustur(
                    temel["goruntu_verisi"], temel["etiket_maskeleri"], yaw,
                    kadraj["x_pct"], kadraj["y_pct"],
                )
                karar = uretim_karari(model, bozuk, temel["mpp"])
                kayitlar.append({
                    "kare": temel["kare"],
                    "manifest_indisi": temel["manifest_indisi"],
                    "manifest_acik_serit": temel["manifest_acik_serit"],
                    "temel_yol": temel["temel_karar"]["yol"],
                    "temel_red": temel["temel_karar"]["red"],
                    "yol": karar["yol"],
                    "guven": karar["guven"],
                    "red": karar["red"],
                    "rota_uretildi": karar["yol"] is not None,
                    "ayni_serit": (temel["temel_karar"]["yol"] is not None
                                    and karar["yol"] == temel["temel_karar"]["yol"]),
                    "affine": [[round(float(v), 8) for v in satir]
                               for satir in matris],
                    "etiket": _etiket_ozeti(bozuk_etiket),
                })
            ozet = hucresi_ozetle(kayitlar, len(temeller))
            hucreler.append({"yaw_derece": yaw, "kadraj": dict(kadraj),
                             "ozet": ozet, "kareler": kayitlar})
            print(f"hucre {hucre_sira:03d}/{toplam_hucre} yaw={yaw:+d} "
                  f"kadraj={kadraj['ad']} rota={_oran_metni(ozet['rota_orani'])}% "
                  f"ayni={_oran_metni(ozet['ayni_serit_orani'])}% "
                  f"{ozet['durum']}", flush=True)

    kirilma = kirilmalari_bul(hucreler)
    gerekli = gerekli_zarfi_degerlendir(hucreler)
    return {
        "durum": "OLCUM",
        "model": str(model_yolu),
        "model_adi": model_yolu.name,
        "kume": str(kume),
        "n": len(temeller),
        "conf": CONF,
        "imgsz": INFER_SIZE,
        "on_kayit_sha256": on_kayit_sha,
        "izgara": {"yaw": list(YAW_DEGERLERI),
                   "kadraj": [dict(k) for k in KADRAJ_DURUMLARI]},
        "esikler": {"rota_kabul": ROTA_KABUL_ORANI,
                    "ayni_serit_kabul": SERIT_KABUL_ORANI,
                    "kirilma": KIRILMA_ORANI},
        "temel_kararlar": [
            {"kare": t["kare"], "manifest_indisi": t["manifest_indisi"],
             "manifest_acik_serit": t["manifest_acik_serit"],
             **t["temel_karar"]}
            for t in temeller
        ],
        "gerekli_zarf": gerekli,
        "kirilma": kirilma,
        "sure_s": round(time.perf_counter() - baslangic, 3),
        "hucreler": hucreler,
        "sinir": ("Sentetik kabul kumesinde geometri dayanimi; gercek ucus, "
                  "mercek/perspektif veya arena domain basarimi kaniti degildir."),
    }


def _varsayilan_kume() -> Path:
    defter = load_registry()
    profil = defter["profiles"][defter["default_profile"]]
    return Path(profil["kabul_kumesi"])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", type=Path, default=None,
                    help="varsayilan: model defterindeki etkin uretim modeli")
    ap.add_argument("--kume", type=Path, default=None,
                    help="varsayilan: model defterindeki kabul_kumesi")
    ap.add_argument("--n", type=int, default=ON_KAYIT_N,
                    help=f"temel kare sayisi (0..{AZAMI_N}; on kayit={ON_KAYIT_N})")
    ap.add_argument("--cikti", type=Path,
                    default=KOK / "results" / "yaw_zarfi" / "b3_yaw_kadraj_zarfi.json")
    a = ap.parse_args(argv)

    if a.n < 0 or a.n > AZAMI_N:
        ap.error(f"--n 0..{AZAMI_N} araliginda olmali")
    on_kayit_sha = on_kayit_dogrula()
    kume = a.kume or _varsayilan_kume()
    if not kume.is_absolute():
        kume = (KOK / kume).resolve()
    cikti = a.cikti if a.cikti.is_absolute() else (KOK / a.cikti).resolve()

    ornekler = ornekleri_sec(kume, a.n)
    if a.n == 0:
        rapor = bos_rapor("N=0; olcum paydasi yok", a.n, on_kayit_sha)
        raporu_yaz(rapor, cikti)
        print("OLCULEMEDI: N=0; olcum paydasi yok")
        print(f"json -> {cikti}")
        return 2
    if len(ornekler) != a.n:
        rapor = bos_rapor(
            f"istenen {a.n} uygun karenin yalniz {len(ornekler)} tanesi bulundu",
            a.n, on_kayit_sha,
        )
        raporu_yaz(rapor, cikti)
        print(f"OLCULEMEDI: {rapor['neden']}")
        print(f"json -> {cikti}")
        return 2

    if a.model is None:
        model_yolu, _profil = resolve_model(calisan_imgsz=INFER_SIZE)
    else:
        model_yolu = a.model if a.model.is_absolute() else (KOK / a.model).resolve()
        if not model_yolu.is_file():
            raise SystemExit(f"model yok: {model_yolu}")

    from ultralytics import YOLO
    model = YOLO(str(model_yolu), task="segment")
    print(f"B3 yaw/kadraj · model={model_yolu.name} · n={a.n} · "
          f"hucre={len(YAW_DEGERLERI)}x{len(KADRAJ_DURUMLARI)} · conf={CONF}")
    rapor = olc(model, model_yolu, kume, ornekler, on_kayit_sha)
    raporu_yaz(rapor, cikti)
    tablo_yaz(rapor["hucreler"])
    print("\nKIRILMA:")
    print("  yaw   :", rapor["kirilma"]["yaw"]["rapor"])
    print("  kadraj:", rapor["kirilma"]["kadraj"]["rapor"])
    print("GEREKLI ZARF:", rapor["gerekli_zarf"]["durum"])
    print("SAHA ONERISI:",
          rapor["gerekli_zarf"]["saha_kontrol_listesi_onerisi"])
    print(f"json -> {cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
