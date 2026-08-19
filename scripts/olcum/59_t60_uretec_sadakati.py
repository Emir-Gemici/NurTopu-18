"""NEDEN: T60 renk duzeltmesini duz boyayla gecmeyi engelleyen olcum kapisi.

Ilk asamada, uretici degismeden onceki LAB ve 6 px Gauss yuksek-geciren doku
olcumlerini kaydeder. Sonraki asama ayni ornekleri yeni ureticiyle karsilastirir.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import random
from pathlib import Path

import cv2
import numpy as np


SIGMA_DOKU_PX = 6.0
PROSEDUREL_ORNEK = 40
ENKAZ_DOKU_ORNEK = 40
RGBA_ORNEK = 80
ZEMIN_L_BANDI = (150.0, 159.0)
ZEMIN_A_BANDI = (-0.5, 4.5)
ZEMIN_B_BANDI = (11.0, 13.5)
MOLOZ_L_BANDI = (102.0, 114.0)
MOLOZ_A_MUTLAK_TAVAN = 1.5
MOLOZ_B_BANDI = (3.0, 5.0)
DOKU_KORUMA_ORANI = 0.75
ZEMIN_DOKU_BANDI = (8.5, 12.7)
YOL_DOKU_BANDI = (2.6, 5.1)
IC_ZEMIN_EROZYON_BOYUTU_PX = 25
HEDEF_DISLAMA_PAYI_PX = 6


def modul_yukle(yol: Path):
    """Ureteci verilen mutlak yoldan, egitim veya dosya yazimi olmadan yukle."""
    spec = importlib.util.spec_from_file_location("t60_uretec", yol)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"uretec yuklenemedi: {yol}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _maske_ve_bgr(im: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """BGR/BGRA girdiden doku olcum maskesi ve BGR goruntu dondur."""
    if im.ndim != 3 or im.shape[2] not in (3, 4):
        raise ValueError("olcum girdisi BGR veya BGRA olmali")
    if im.shape[2] == 3:
        return np.ones(im.shape[:2], bool), im
    alpha = im[:, :, 3]
    cekirdek = cv2.distanceTransform((alpha > 0).astype(np.uint8), cv2.DIST_L2, 5)
    esik = 18.0 if min(im.shape[:2]) >= 64 else 6.0
    maske = cekirdek > esik
    if not maske.any():
        maske = alpha > 0
    return maske, im[:, :, :3]


def olc(im: np.ndarray) -> dict[str, float]:
    """LAB bolge ortalamasi ve T57 6 px yuksek-geciren doku genligini olc."""
    maske, bgr = _maske_ve_bgr(im)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    hp = lab - cv2.GaussianBlur(lab, (0, 0), SIGMA_DOKU_PX)
    sec = lab[maske]
    hp_sec = hp[maske]
    return {
        "L": float(sec[:, 0].mean()),
        "a": float(sec[:, 1].mean() - 128.0),
        "b": float(sec[:, 2].mean() - 128.0),
        "doku_L": float(np.sqrt(np.mean(np.square(hp_sec[:, 0])))),
        "doku_C": float(np.sqrt(np.mean(np.square(hp_sec[:, 1])
                                              + np.square(hp_sec[:, 2])))),
    }


def ozet(ad: str, kayitlar: list[dict[str, float]]) -> dict[str, object]:
    """Bir kategorinin ortalama ve min/maks metriklerini yazdirilabilir yap."""
    sonuc: dict[str, object] = {"n": len(kayitlar)}
    for alan in ("L", "a", "b", "doku_L", "doku_C"):
        degerler = np.asarray([k[alan] for k in kayitlar], np.float64)
        sonuc[alan] = {
            "ortalama": float(degerler.mean()),
            "min": float(degerler.min()),
            "maks": float(degerler.max()),
        }
    d = sonuc["doku_L"]
    print(f"[T60_ONCE] {ad:<20} n={len(kayitlar):3d} "
          f"LAB=({sonuc['L']['ortalama']:.4f},"
          f"{sonuc['a']['ortalama']:+.4f},{sonuc['b']['ortalama']:+.4f}) "
          f"doku_L={d['ortalama']:.4f} ({d['min']:.4f}..{d['maks']:.4f})")
    return sonuc


def _ortalama(sonuc: dict[str, object], alan: str) -> float:
    return float(sonuc[alan]["ortalama"])


def _bantta(deger: float, bant: tuple[float, float]) -> bool:
    return bant[0] <= deger <= bant[1]


def once_olc(uretec_yolu: Path) -> dict[str, object]:
    """T60 oncesi dort kategori icin tekrar edilebilir doku tabani olustur."""
    m = modul_yukle(uretec_yolu)
    banka = m.banka_yukle()
    kategoriler: dict[str, list[dict[str, float]]] = {
        "prosedurel_zemin": [],
        "prosedurel_yol": [],
        "enkaz_doku": [],
        "rgba_ham": [],
        "rgba_boyali": [],
    }
    for i in range(PROSEDUREL_ORNEK):
        for kat in ("zemin", "yol"):
            seed = 7000 + i
            np.random.seed(seed)
            im = m.prosedurel_yuzey(random.Random(seed), kat)
            kategoriler[f"prosedurel_{kat}"].append(olc(im))
    for im in banka["enkaz_doku"][:ENKAZ_DOKU_ORNEK]:
        kategoriler["enkaz_doku"].append(olc(im))
    for i, yol in enumerate(banka["enkaz"][:RGBA_ORNEK]):
        ham = cv2.imread(str(yol), cv2.IMREAD_UNCHANGED)
        if ham is None or ham.ndim != 3 or ham.shape[2] != 4:
            continue
        kategoriler["rgba_ham"].append(olc(ham))
        kategoriler["rgba_boyali"].append(olc(m.moloz_rengi(ham, random.Random(9000 + i))))
    return {ad: ozet(ad, kayitlar) for ad, kayitlar in kategoriler.items()}


def sonra_olc(uretec_yolu: Path, once_json: Path) -> tuple[dict[str, object], bool]:
    """Yeni ureticinin renk+doku kapilarini oncesiyle AND ederek denetle."""
    m = modul_yukle(uretec_yolu)
    banka = m.banka_yukle()
    kategoriler: dict[str, list[dict[str, float]]] = {
        "prosedurel_zemin": [], "banka_zemin": [], "prosedurel_yol": [],
        "enkaz_doku": [], "rgba_boyali": [],
    }
    for i in range(PROSEDUREL_ORNEK):
        for kat in ("zemin", "yol"):
            seed = 7000 + i
            np.random.seed(seed)
            kategoriler[f"prosedurel_{kat}"].append(
                olc(m.prosedurel_yuzey(random.Random(seed), kat)))
    banka_zemin_ham = []
    for im in banka["zemin"][:PROSEDUREL_ORNEK]:
        banka_zemin_ham.append(olc(im))
        kategoriler["banka_zemin"].append(
            olc(m.lab_ortalamasini_tasi(im, m.LAB_ZEMIN_HEDEF,
                                        m.ZEMIN_KROMA_KORUMA)))
    for im in banka["enkaz_doku"][:ENKAZ_DOKU_ORNEK]:
        kategoriler["enkaz_doku"].append(olc(im))
    alfa_uyumsuz = 0
    for i, yol in enumerate(banka["enkaz"][:RGBA_ORNEK]):
        ham = cv2.imread(str(yol), cv2.IMREAD_UNCHANGED)
        if ham is not None and ham.ndim == 3 and ham.shape[2] == 4:
            boyali = m.moloz_rengi(ham, random.Random(9000 + i))
            alfa_uyumsuz += int(np.count_nonzero(ham[:, :, 3] != boyali[:, :, 3]))
            kategoriler["rgba_boyali"].append(olc(boyali))
    son = {ad: ozet(ad, kayitlar) for ad, kayitlar in kategoriler.items()}
    once = json.loads(once_json.read_text(encoding="utf-8"))["kategoriler"]
    esleme = {
        "prosedurel_zemin": "prosedurel_zemin",
        "prosedurel_yol": "prosedurel_yol",
        "enkaz_doku": "enkaz_doku",
        "rgba_boyali": "rgba_ham",
    }
    gecti = True
    for yeni, eski in esleme.items():
        oran = _ortalama(son[yeni], "doku_L") / _ortalama(once[eski], "doku_L")
        ok = oran >= DOKU_KORUMA_ORANI
        gecti &= ok
        print(f"[T60_DOKU] {yeni:<20} oran={oran:.4f} "
              f"esik={DOKU_KORUMA_ORANI:.2f} durum={'GECTI' if ok else 'DUSTU'}")
    banka_ham = ozet("banka_zemin_ham", banka_zemin_ham)
    banka_oran = (_ortalama(son["banka_zemin"], "doku_L")
                   / _ortalama(banka_ham, "doku_L"))
    banka_ok = banka_oran >= DOKU_KORUMA_ORANI
    gecti &= banka_ok
    print(f"[T60_DOKU] {'banka_zemin':<20} oran={banka_oran:.4f} "
          f"esik={DOKU_KORUMA_ORANI:.2f} durum={'GECTI' if banka_ok else 'DUSTU'}")
    alfa_ok = alfa_uyumsuz == 0
    gecti &= alfa_ok
    print(f"[T60_ALFA] uyumsuz_px={alfa_uyumsuz} "
          f"durum={'GECTI' if alfa_ok else 'DUSTU'}")
    for ad in ("prosedurel_zemin", "banka_zemin"):
        z = son[ad]
        ok = (_bantta(_ortalama(z, "L"), ZEMIN_L_BANDI)
              and _bantta(_ortalama(z, "a"), ZEMIN_A_BANDI)
              and _bantta(_ortalama(z, "b"), ZEMIN_B_BANDI))
        gecti &= ok
        print(f"[T60_RENK] {ad:<20} durum={'GECTI' if ok else 'DUSTU'}")
    for ad in ("enkaz_doku", "rgba_boyali"):
        z = son[ad]
        ok = (_bantta(_ortalama(z, "L"), MOLOZ_L_BANDI)
              and abs(_ortalama(z, "a")) < MOLOZ_A_MUTLAK_TAVAN
              and _bantta(_ortalama(z, "b"), MOLOZ_B_BANDI))
        gecti &= ok
        print(f"[T60_RENK] {ad:<20} durum={'GECTI' if ok else 'DUSTU'}")
    d_l = min(_ortalama(son[x], "L") for x in ("prosedurel_zemin", "banka_zemin")) \
        - max(_ortalama(son[x], "L") for x in ("enkaz_doku", "rgba_boyali"))
    d_ok = d_l >= 35.0
    gecti &= d_ok
    print(f"[T60_RENK] dL={d_l:.4f} esik=35.0 durum={'GECTI' if d_ok else 'DUSTU'}")
    zd = _ortalama(son["prosedurel_zemin"], "doku_L")
    bzd = _ortalama(son["banka_zemin"], "doku_L")
    yd = _ortalama(son["prosedurel_yol"], "doku_L")
    bant_ok = (_bantta(zd, ZEMIN_DOKU_BANDI)
               and _bantta(bzd, ZEMIN_DOKU_BANDI)
               and _bantta(yd, YOL_DOKU_BANDI))
    gecti &= bant_ok
    print(f"[T60_DOKU] T57 prosedurel_zemin={zd:.4f} banka_zemin={bzd:.4f} "
          f"yol={yd:.4f} "
          f"durum={'GECTI' if bant_ok else 'DUSTU'}")
    varyant = {"yok": 0, "figur": 0, "kirmizi": 0}
    kadraj_figur = rng_uyumsuz = 0
    for seed in range(200):
        e, k = random.Random(seed), random.Random(seed)
        var, figur = m.hb_karari(e, False)
        if not var:
            varyant["yok"] += 1
        elif figur:
            varyant["figur"] += 1
        else:
            varyant["kirmizi"] += 1
        kvar, kfigur = m.hb_karari(k, True)
        kadraj_figur += int(kvar and kfigur)
        rng_uyumsuz += int(e.random() != k.random())
    varyant_ok = (varyant["figur"] > 0 and varyant["kirmizi"] > 0
                  and kadraj_figur == 200 and rng_uyumsuz == 0)
    gecti &= varyant_ok
    print(f"[T60_HB] egitim={varyant} kadraj_figur={kadraj_figur}/200 "
          f"rng_akisi_uyumsuz={rng_uyumsuz} "
          f"durum={'GECTI' if varyant_ok else 'DUSTU'}")
    # Yardimci secimin gercek sahneye baglandigini ve iki HB'nin gercekten
    # cizildigini olc. Raw sahne kullanilir: fotometrik bozunum HB/moloz L
    # ayrimini egitim cesitliligi icin bilerek genisletir.
    gercek = {"yok": 0, "figur_siyah_beyaz": 0, "metin_kirmizi": 0}
    hb_l: dict[str, list[np.ndarray]] = {"figur_siyah_beyaz": [],
                                         "metin_kirmizi": []}
    tam_temas = hb_tasma_px = 0
    final_hb_l: dict[str, list[np.ndarray]] = {"figur_siyah_beyaz": [],
                                               "metin_kirmizi": []}
    for seed in range(40):
        bilgi = {}
        np.random.seed(16000 + seed)
        rng = random.Random(16000 + seed)
        im, kimlik, siniflar = m.sahne_uret(rng, banka, bilgi=bilgi)
        ad = bilgi.get("hedef_varyanti") or "yok"
        gercek[ad] += 1
        kutu = bilgi.get("hedef_kutusu")
        if kutu is not None:
            tam_temas += int(
                bilgi.get("hedef_onceki_gecilebilir_temas_px", 0)
                == bilgi.get("hedef_pad_alani_px", -1) > 0)
            x, y, w, h = kutu
            sinif0 = np.zeros(kimlik.shape, np.uint8)
            for kimlik_no, sinif_id in siniflar.items():
                if sinif_id == 0:
                    sinif0[kimlik == kimlik_no] = 1
            hb_gorsel = np.zeros(kimlik.shape, np.uint8)
            hb_gorsel[y:y+h, x:x+w] = 1
            hb_tasma_px += int(np.count_nonzero((hb_gorsel > 0) & (sinif0 == 0)))
            lab = cv2.cvtColor(im[y:y+h, x:x+w], cv2.COLOR_BGR2LAB)
            hb_l[ad].append(lab[:, :, 0].reshape(-1))
            hedef_m = np.zeros(kimlik.shape, np.uint8)
            cv2.rectangle(hedef_m, (x, y), (x + w - 1, y + h - 1), 1, -1)
            im_g, hedef_g = m.geometrik(rng, im, hedef_m)
            im_g = cv2.resize(im_g, (m.BOYUT, m.BOYUT), interpolation=cv2.INTER_AREA)
            hedef_g = cv2.resize(hedef_g, (m.BOYUT, m.BOYUT),
                                  interpolation=cv2.INTER_NEAREST)
            im_g = m.fotometrik_rng_tuket(rng, im_g, kadraj=False)
            lab_g = cv2.cvtColor(im_g, cv2.COLOR_BGR2LAB)
            if np.any(hedef_g):
                final_hb_l[ad].append(lab_g[:, :, 0][hedef_g > 0])
    gercek_cizili = gercek["figur_siyah_beyaz"] + gercek["metin_kirmizi"]
    gercek_ok = (gercek["figur_siyah_beyaz"] > 0
                 and gercek["metin_kirmizi"] > 0
                 and tam_temas == gercek_cizili and hb_tasma_px == 0)
    gecti &= gercek_ok
    print(f"[T60_HB_GERCEK_YOL] dagilim={gercek} tam_on_temas="
          f"{tam_temas}/{gercek_cizili} hb_class0_disi_px={hb_tasma_px} "
          f"durum={'GECTI' if gercek_ok else 'DUSTU'}")
    for ad in ("figur_siyah_beyaz", "metin_kirmizi"):
        deger = np.concatenate(hb_l[ad]) if hb_l[ad] else np.asarray([], np.uint8)
        cakisma = (float(np.mean((deger >= MOLOZ_L_BANDI[0])
                                 & (deger <= MOLOZ_L_BANDI[1])))
                    if deger.size else float("nan"))
        q = np.percentile(deger, (0, 5, 50, 95, 100))
        print(f"[T60_HB_GERCEK_L] {ad} n={gercek[ad]} "
              f"moloz_bandi_cakisma={100*cakisma:.4f}% "
              f"min={q[0]:.1f} p05={q[1]:.1f} p50={q[2]:.1f} "
              f"p95={q[3]:.1f} max={q[4]:.1f}")
        final_deger = (np.concatenate(final_hb_l[ad]) if final_hb_l[ad]
                       else np.asarray([], np.uint8))
        final_cakisma = (float(np.mean((final_deger >= MOLOZ_L_BANDI[0])
                                       & (final_deger <= MOLOZ_L_BANDI[1])))
                         if final_deger.size else float("nan"))
        print(f"[T60_HB_FINAL_L] {ad} moloz_bandi_cakisma="
              f"{100*final_cakisma:.4f}% (GIZLENMEDI; fotometrik sonrasi, JPEG oncesi)")
    return son, gecti


def _lab_ozeti(pikseller: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """BGR piksel listesi icin LAB ortalamasi ve altili baskin palet."""
    bgr = np.concatenate(pikseller, axis=0)
    if len(bgr) > 120_000:
        bgr = bgr[np.linspace(0, len(bgr) - 1, 120_000, dtype=np.int64)]
    lab = cv2.cvtColor(bgr.reshape(-1, 1, 3), cv2.COLOR_BGR2LAB).reshape(-1, 3)
    veri = lab.astype(np.float32)
    cv2.setRNGSeed(60)
    _, etiket, merkez = cv2.kmeans(
        veri, 6, None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.1),
        5, cv2.KMEANS_PP_CENTERS)
    say = np.bincount(etiket[:, 0], minlength=6)
    sira = np.argsort(-say)
    palet = np.column_stack((merkez[sira], 100.0 * say[sira] / say.sum()))
    ort = veri.mean(axis=0)
    ort[1:] -= 128.0
    palet[:, 1:3] -= 128.0
    return ort, palet


def _etiket_maskeleri(kok: Path, kayit: dict, boyut: tuple[int, int]):
    h, w = boyut
    z = np.zeros((h, w), np.uint8)
    e = np.zeros((h, w), np.uint8)
    p = kok / "labels" / kayit["bolum"] / (Path(kayit["cikti"]).stem + ".txt")
    for satir in p.read_text(encoding="utf-8").splitlines():
        q = satir.split()
        pts = np.asarray(q[1:], np.float32).reshape(-1, 2)
        pts *= np.asarray([w, h], np.float32)
        cv2.fillPoly(z if q[0] == "0" else e, [pts.astype(np.int32)], 1)
    return z, e


def _final_doku_ozeti(kume: Path) -> dict[str, object]:
    """Kalici kadraj JPEG'lerinde erozyonlu zemin/engel HP-L genligini olc."""
    veri = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    degerler = {"zemin": [], "blocked": []}
    for kayit in veri["ornekler"]:
        im = cv2.imread(str(kume / kayit["cikti"]))
        z, e = _etiket_maskeleri(kume, kayit, im.shape[:2])
        lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
        hp_l = (lab - cv2.GaussianBlur(lab, (0, 0), SIGMA_DOKU_PX))[:, :, 0]
        arena = kayit["arena"]
        x0, x1 = (int(round(v)) for v in arena["arena_x_araligi"])
        zemin = np.zeros(im.shape[:2], np.uint8)
        zemin[:, :max(0, x0)] = 1
        zemin[:, min(im.shape[1], x1):] = 1
        for ad, maske in (("zemin", zemin), ("blocked", e)):
            ic = cv2.erode(maske, np.ones((25, 25), np.uint8)) > 0
            if np.any(ic):
                degerler[ad].append(float(np.sqrt(np.mean(np.square(hp_l[ic])))))
    return {ad: {"n": len(v), "ortalama": float(np.mean(v)),
                 "min": float(np.min(v)), "maks": float(np.max(v))}
            for ad, v in degerler.items()}


def kadraj_kapisi(uretec_yolu: Path, kume: Path, referans: Path,
                  gorsel: Path, once_kume: Path | None = None) -> bool:
    """T51/T56 geometri, HB ayrimi ve zorunlu yan-yana gorseli olc."""
    m = modul_yukle(uretec_yolu)
    veri = json.loads((kume / "manifest.json").read_text(encoding="utf-8"))
    kayitlar = veri["ornekler"]
    beklenen_adet = int(veri.get("parametreler", {}).get("adet", -1))
    goruntuler = {p.relative_to(kume).as_posix()
                  for p in (kume / "images").rglob("sa_*.jpg")}
    etiketler = {p.relative_to(kume).as_posix()
                 for p in (kume / "labels").rglob("sa_*.txt")}
    manifest_gorsel = {str(k["cikti"]).replace("\\", "/") for k in kayitlar}
    manifest_etiket = {f"labels/{k['bolum']}/{Path(k['cikti']).stem}.txt"
                       for k in kayitlar}
    goruntu_sayisi, etiket_sayisi = len(goruntuler), len(etiketler)
    butunluk_ok = (beklenen_adet > 0 and len(kayitlar) == beklenen_adet
                   and goruntu_sayisi == beklenen_adet
                   and etiket_sayisi == beklenen_adet
                   and goruntuler == manifest_gorsel
                   and etiketler == manifest_etiket)
    hedef = sapmalar = sapma_ornegi = gecilebilir_ornegi = tek = uyumsuz = temas_yok = pad_kotu = 0
    pad_engel = varyant_uyumsuz = 0
    temas_oranlari = []
    kenarlar = []
    hb_l = []
    zemin_pikselleri: list[np.ndarray] = []
    ic_zemin_pikselleri: list[np.ndarray] = []
    ic_zemin_ortalamalari: list[np.ndarray] = []
    moloz_pikselleri: list[np.ndarray] = []
    ilk_im = ilk_kutu = None
    gorsel_puan = None
    gorsel_kaynak = None
    for kayit in kayitlar:
        arena = kayit["arena"]
        for s in arena["uretec_seritleri"]:
            sapma = s.get("merkez_cizgisi_sapma_px")
            if s.get("gecilebilir"):
                gecilebilir_ornegi += 1
                if sapma is not None:
                    sapma_ornegi += 1
                    sapmalar += int(abs(sapma) > 1e-6)
        kutu = arena.get("hedef_kutu")
        if kutu is None:
            continue
        hedef += 1
        varyant_uyumsuz += int(arena.get("hedef_varyanti") != "figur_siyah_beyaz")
        kenarlar.append(float(arena["hedef_kenar_m"]))
        temas = int(arena.get("hedef_onceki_gecilebilir_temas_px", 0))
        pad_alani_tuval = int(arena.get("hedef_pad_alani_px", 0))
        if arena.get("acik_serit") is not None:
            tek += 1
        im = cv2.imread(str(kume / kayit["cikti"]))
        z, _ = _etiket_maskeleri(kume, kayit, im.shape[:2])
        _, e = _etiket_maskeleri(kume, kayit, im.shape[:2])
        kx, ky, kw, kh = (float(v) for v in kutu)
        hedef_serit_hesap = int(m.serit_no(kx + kw / 2.0, 0, im.shape[1]))
        uyumsuz += int(arena.get("hedef_serit") != hedef_serit_hesap)
        if arena.get("acik_serit") is not None:
            uyumsuz += int(hedef_serit_hesap != arena.get("acik_serit"))
        x, y, w, h = (int(round(v)) for v in kutu)
        x1, y1 = min(im.shape[1], x + w), min(im.shape[0], y + h)
        temas_oranlari.append(temas / pad_alani_tuval if pad_alani_tuval else 0.0)
        temas_yok += int(pad_alani_tuval <= 0 or temas != pad_alani_tuval)
        ic_pay = 1 if min(w, h) > 2 else 0
        pad_kotu += int(np.count_nonzero(
            z[y + ic_pay:y1 - ic_pay, x + ic_pay:x1 - ic_pay] == 0))
        pad_engel += int(np.count_nonzero(e[y:y1, x:x1] > 0))
        mpp = float(arena["mpp"])
        kenarlar[-1] = (kw * mpp, kh * mpp)
        lab = cv2.cvtColor(im[y:y1, x:x1], cv2.COLOR_BGR2LAB)
        hb_l.append(lab[:, :, 0].reshape(-1))
        arena_x0, arena_x1 = (int(round(v)) for v in arena["arena_x_araligi"])
        zemin_m = np.zeros(im.shape[:2], bool)
        zemin_m[:, :max(0, arena_x0 - 3)] = True
        zemin_m[:, min(im.shape[1], arena_x1 + 3):] = True
        zemin_pikselleri.append(im[zemin_m][::max(1, np.count_nonzero(zemin_m)//5000)])
        ic_zemin = cv2.erode(
            z, np.ones((IC_ZEMIN_EROZYON_BOYUTU_PX,
                        IC_ZEMIN_EROZYON_BOYUTU_PX), np.uint8)) > 0
        ic_zemin &= e == 0
        ic_zemin[max(0, y - HEDEF_DISLAMA_PAYI_PX):
                 min(im.shape[0], y1 + HEDEF_DISLAMA_PAYI_PX),
                 max(0, x - HEDEF_DISLAMA_PAYI_PX):
                 min(im.shape[1], x1 + HEDEF_DISLAMA_PAYI_PX)] = False
        if not np.any(ic_zemin):
            print(f"[T60_CLASS0_IC] DUSTU: ic zemin yok {kayit['cikti']}")
            return False
        ic_bgr = im[ic_zemin]
        ic_lab = cv2.cvtColor(ic_bgr.reshape(-1, 1, 3),
                              cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32)
        ic_zemin_ortalamalari.append(ic_lab.mean(axis=0))
        ic_zemin_pikselleri.append(
            ic_bgr[::max(1, len(ic_bgr) // 5000)])
        moloz_pikselleri.append(im[e > 0][::max(1, np.count_nonzero(e)//5000)])
        puan = (int(len(arena["uretec_seritleri"]) == 3), arena_x1 - arena_x0)
        if gorsel_puan is None or puan > gorsel_puan:
            ilk_im, ilk_kutu = im, (x, y, x1, y1)
            gorsel_puan = puan
            gorsel_kaynak = kayit["cikti"]
    hb = np.concatenate(hb_l) if hb_l else np.asarray([], np.uint8)
    hb_cakisma = float(np.mean((hb >= MOLOZ_L_BANDI[0]) & (hb <= MOLOZ_L_BANDI[1]))) \
        if hb.size else float("nan")
    geo_ok = (butunluk_ok and len(kayitlar) > 0 and hedef == len(kayitlar)
              and sapma_ornegi > 0 and sapma_ornegi == gecilebilir_ornegi
              and sapmalar == 0 and tek > 0
              and uyumsuz == 0 and temas_yok == 0 and pad_kotu == 0
              and pad_engel == 0 and varyant_uyumsuz == 0 and kenarlar
              and all(a == 2.0 and b == 2.0 for a, b in kenarlar))
    print(f"[T60_KADRAJ] beklenen={beklenen_adet} kayit={len(kayitlar)} "
          f"gorsel={goruntu_sayisi} etiket={etiket_sayisi} hedef={hedef} "
          f"sapma_ornegi={sapma_ornegi}/{gecilebilir_ornegi} "
          f"sapma={sapmalar} tek={tek} "
          f"hedef_serit_uyumsuz={uyumsuz} tam_on_temas_yok={temas_yok} "
          f"temas_orani={min(temas_oranlari):.4f}..{max(temas_oranlari):.4f} "
          f"pad_non_traversable_px={pad_kotu} pad_engel_px={pad_engel} "
          f"varyant_uyumsuz={varyant_uyumsuz} "
          f"kenar_m={min(min(k) for k in kenarlar):.3f}.."
          f"{max(max(k) for k in kenarlar):.3f} "
          f"durum={'GECTI' if geo_ok else 'DUSTU'}")
    print(f"[T60_HB_AYRIM] HB_L_moloz_bandi_cakisma={100*hb_cakisma:.4f}% "
          "(GIZLENMEDI; figur varyanti bimodaldir)")
    if hb.size:
        q = np.percentile(hb, (0, 5, 50, 95, 100))
        print(f"[T60_HB_L] min={q[0]:.1f} p05={q[1]:.1f} p50={q[2]:.1f} "
              f"p95={q[3]:.1f} max={q[4]:.1f}")
    z_ort, z_palet = _lab_ozeti(zemin_pikselleri)
    _, ic_zemin_palet = _lab_ozeti(ic_zemin_pikselleri)
    ic_zemin_ort = np.mean(ic_zemin_ortalamalari, axis=0)
    ic_zemin_ort[1:] -= 128.0
    m_ort, m_palet = _lab_ozeti(moloz_pikselleri)
    renk_ok = (_bantta(float(z_ort[0]), ZEMIN_L_BANDI)
               and _bantta(float(z_ort[1]), ZEMIN_A_BANDI)
               and _bantta(float(z_ort[2]), ZEMIN_B_BANDI)
               and _bantta(float(ic_zemin_ort[0]), ZEMIN_L_BANDI)
               and _bantta(float(ic_zemin_ort[1]), ZEMIN_A_BANDI)
               and _bantta(float(ic_zemin_ort[2]), ZEMIN_B_BANDI)
               and _bantta(float(m_ort[0]), MOLOZ_L_BANDI)
               and abs(float(m_ort[1])) < MOLOZ_A_MUTLAK_TAVAN
               and _bantta(float(m_ort[2]), MOLOZ_B_BANDI)
               and float(z_ort[0] - m_ort[0]) >= 35.0)
    print(f"[T60_KUME_RENK] zemin=({z_ort[0]:.3f},{z_ort[1]:+.3f},"
          f"{z_ort[2]:+.3f}) moloz=({m_ort[0]:.3f},{m_ort[1]:+.3f},"
           f"{m_ort[2]:+.3f}) dL={z_ort[0]-m_ort[0]:.3f} "
           f"durum={'GECTI' if renk_ok else 'DUSTU'}")
    print(f"[T60_CLASS0_IC] n={len(ic_zemin_ortalamalari)} "
          f"LAB=({ic_zemin_ort[0]:.3f},{ic_zemin_ort[1]:+.3f},"
          f"{ic_zemin_ort[2]:+.3f}) "
          f"durum={'GECTI' if renk_ok else 'DUSTU'}")
    final_doku = _final_doku_ozeti(kume)
    final_doku_ok = True
    if once_kume is not None:
        once_doku = _final_doku_ozeti(once_kume)
        oran_z = (final_doku["zemin"]["ortalama"]
                  / once_doku["zemin"]["ortalama"])
        oran_e = (final_doku["blocked"]["ortalama"]
                  / once_doku["blocked"]["ortalama"])
        final_doku_ok = min(oran_z, oran_e) >= DOKU_KORUMA_ORANI
        print(f"[T60_FINAL_DOKU] zemin={once_doku['zemin']['ortalama']:.4f}"
              f"->{final_doku['zemin']['ortalama']:.4f} oran={oran_z:.4f} "
              f"blocked={once_doku['blocked']['ortalama']:.4f}"
              f"->{final_doku['blocked']['ortalama']:.4f} oran={oran_e:.4f} "
              f"esik={DOKU_KORUMA_ORANI:.2f} "
              f"durum={'GECTI' if final_doku_ok else 'DUSTU'}")
    print(f"[T60_FINAL_DOKU_BANDI] zemin="
          f"{final_doku['zemin']['ortalama']:.4f} "
          "T57_nominal=8.5..12.7 durum=DOGRULANAMADI "
          "(T57 kaynak-yama bandidir; final JPEG icin sozlesme yok)")
    for ad, palet in (("zemin", z_palet), ("class0_ic", ic_zemin_palet),
                      ("moloz", m_palet)):
        metin = " | ".join(
            f"L={r[0]:.1f},a={r[1]:+.1f},b={r[2]:+.1f},%={r[3]:.1f}"
            for r in palet)
        print(f"[T60_PALET] {ad}: {metin}")
    ref = cv2.imread(str(referans))
    if ref is None or ilk_im is None:
        print("[T60_GORSEL] DUSTU: referans veya uretilen kare okunamadi")
        return False
    yuk = max(ref.shape[0], ilk_im.shape[0])
    def _uyarla(im):
        olcek = yuk / im.shape[0]
        return cv2.resize(im, (int(round(im.shape[1] * olcek)), yuk))
    r, u = _uyarla(ref), _uyarla(ilk_im)
    pano = np.full((yuk + 54, r.shape[1] + u.shape[1], 3), 245, np.uint8)
    pano[54:, :r.shape[1]] = r
    pano[54:, r.shape[1]:] = u
    cv2.putText(pano, "GERCEK SARTNAME FIGURU", (18, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
    cv2.putText(pano, "T60 URETILEN KADRAJ", (r.shape[1] + 18, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 20, 20), 2, cv2.LINE_AA)
    gorsel.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(gorsel), pano):
        print(f"[T60_GORSEL] DUSTU: yazilamadi {gorsel}")
        return False
    print(f"[T60_GORSEL] secim=uc_serit_ve_en_genis kaynak={gorsel_kaynak} "
          f"YAZILDI={gorsel}")
    return geo_ok and renk_ok and final_doku_ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--faz", choices=("once", "sonra", "kadraj"), required=True)
    ap.add_argument("--uretec", type=Path, required=True)
    ap.add_argument("--json", type=Path, required=True)
    ap.add_argument("--once-json", type=Path)
    ap.add_argument("--kume", type=Path)
    ap.add_argument("--referans", type=Path)
    ap.add_argument("--gorsel", type=Path)
    ap.add_argument("--once-kume", type=Path)
    args = ap.parse_args()
    uretec = args.uretec.resolve()
    if args.faz == "kadraj":
        if None in (args.kume, args.once_kume, args.referans, args.gorsel):
            ap.error("kadraj fazi --kume --once-kume --referans --gorsel ister")
        ok = kadraj_kapisi(uretec, args.kume, args.referans, args.gorsel,
                           args.once_kume)
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({"faz": "kadraj", "gecti": ok,
                                         "gorsel": str(args.gorsel)}, indent=2),
                             encoding="utf-8")
        return 0 if ok else 1
    if args.faz == "sonra":
        if args.once_json is None:
            ap.error("sonra fazi --once-json ister")
        kategoriler, ok = sonra_olc(uretec, args.once_json)
    else:
        kategoriler, ok = once_olc(uretec), True
    sonuc = {
        "faz": args.faz,
        "uretec": str(uretec),
        "uretec_sha256": hashlib.sha256(uretec.read_bytes()).hexdigest(),
        "sigma_doku_px": SIGMA_DOKU_PX,
        "kategoriler": kategoriler,
        "gecti": ok,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[T60_{args.faz.upper()}] SHA256={sonuc['uretec_sha256']}")
    print(f"[T60_{args.faz.upper()}] JSON={args.json}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
