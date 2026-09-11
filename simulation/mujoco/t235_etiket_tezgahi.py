#!/usr/bin/env python3
"""T235-D · FDA yol etiketi tezgahi — ON_KAYIT SS2 (T235-K3, K3n, alan sigma) + SS3 (T235-K1).

⚠ BENZETIM (sentetik maske), SAHA OLCUMU DEGIL. Render YOK, GPU YOK, MuJoCo kosusu YOK.
On kayit (olcumden ONCE yazildi; esik/izgara/cekilis/tohum DEGISMEZ):
    results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md

Ne olcer (SS2):
  Sentetik maske: 20x20 m FDA alaninda Baslangic -> Hedef dogrultusunda uzanan uc DUZ yol
  (x = -s, 0, +s; y = -10..+10 m). Acik yolun merkez hatti rota sayilir, icerik kutusundaki
  LINE_8 pikselleri (uretim cikarim tuvali, letterbox) rasterlanir. Uc yontem AYNI cekilislerle:
    KARE : karar_sozlesmesi.rota_serit_karari   (bugunku yayin tanimi)
    A0   : karar_sozlesmesi.alan_serit_karari   (icerik merkezinden ±(W/6)/mpp)
    A1   : karar_sozlesmesi.kbh_serit_karari    (GPS + hdg + montaj yaw ile KBH izdusumu)
  Hata modeli (bagimsiz, tohum 20260910, hucre basina 2000 cekilis):
    e_c ~ N(0, s_c^2) her eksende (bekleme konum hatasi) · psi ~ N(0, s_psi^2) (yaw) ·
    egim ~ U[2, 3] derece, yon ~ U[0, 2pi) -> yer kaymasi h*tan(egim) ·
    yalniz A1: GPS kestirim hatasi e_g ~ N(0, s_g^2) her eksende.
Ne olcer (SS3, K1 — uygulama testi, bagimsiz kanit DEGIL):
  A1 saf fonksiyonu yer gercegi pozla kosum_tur3 (20) + kerteriz (8) OPEN_ROUTE karesinde dunya
  yoluyla eslesir mi (28/28 beklenir); KARE ayni tezgahta 3/8 ve 6/20'yi yeniden uretir mi.

Uygulama secimleri (on kayitta yazili DEGIL; README'de gerekcesiyle yazilir):
  * Ortak rastgele sayilar: tum hucreler AYNI standart cekilisleri olcekler -> hucre sonucu
    izgaranin geri kalanindan bagimsizdir (alt izgara bayt-es yeniden uretilir).
  * Acik yol "esit": her cekilis uc acik yol icin de degerlendirilir (hucre = 2000 x 3 sahne).
  * psi pusula kaynakli yon hatasidir: otopilot olculen basi (kerteriz - montaj) tutar, A1 ayni
    pusulayi okur -> A1'in yaw artigi da psi'dir. A1 egimi bilmez (ATTITUDE yok). e_c'yi A1
    bilir (poz izdusumu), yerine e_g hatasini tasir.
  * A1 donusumunu sinamak icin alan kerterizi 37 derece, montaj yaw 90 derece alinir
    (KARE/A0 goruntu koordinatinda calisir, bu secimden bagimsizdir).

Kullanim:
  venv python simulation/mujoco/t235_etiket_tezgahi.py            # K3 izgarasi + K1 -> H1/t235/olcum/
  venv python simulation/mujoco/t235_etiket_tezgahi.py --yalniz-k1
  venv python simulation/mujoco/t235_etiket_tezgahi.py --turetme  # tezgahi KOSMADAN: kayitli
      # JSON'lardan kapi duyarliligi + D-457 kosullu hukmu + README (yeni cekilis YOK)
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from fractions import Fraction
from pathlib import Path

import cv2
import numpy as np

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

import karar_sozlesmesi as ks  # noqa: E402

ETIKET = "benzetim (sentetik maske), saha ölçümü değil"
K1_ETIKET = "benzetim (MuJoCo sentetik kareler, yer gerçeği poz), saha ölçümü değil"
DUY_ETIKET = ("TÜRETME — kayıtlı hücre tablosundan hesaplandı; yeni çekiliş, yeni koşum YOK. "
              "Sayıların kendisi: benzetim (sentetik maske), saha ölçümü değil")
ON_KAYIT_YOLU = "results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md"
D457_YOLU = "REVIEW_LOG.md D-457 (12 Eylül; kamera kipi ÖLÇÜLMEDEN ÖNCE yazıldı)"
H1 = KOK / "results" / "fdr_sprint_20260910" / "H1"
CIKTI_DIZIN = H1 / "t235" / "olcum"
K3_JSON = "k3_hucre_tablosu.json"
K1_JSON = "k1_uygulama.json"
DUY_JSON = "kapi_duyarliligi.json"

# ── ON KAYIT SS2 (DEGISMEZ) ─────────────────────────────────────────────────
TOHUM = 20260910
CEKILIS_N = 2000
S_DEGERLERI_M = (5.0, 6.67, 8.0)
KIP_H = (("4:3", 32.0), ("16:9", 40.0), ("16:9", 32.0))
BILGI_KIP_H = (("16:9", 32.0),)                 # "bilgi hucresi": raporlanir, kapiya girmez
SIGMA_C_M = (0.5, 1.0)
SIGMA_PSI_DERECE = (2.0, 5.0)
SIGMA_G_M = (1.0, 2.0)
EGIM_ARALIGI_DERECE = (2.0, 3.0)
SENSOR_GENISLIK_MM = 6.287                      # HQ (IMX477) aktif genislik
ODAK_MM = 6.0                                   # HQ 6 mm lens
HFOV_DERECE = 2.0 * math.degrees(math.atan(SENSOR_GENISLIK_MM / (2.0 * ODAK_MM)))   # 55,30
NOMINAL_S_M = (6.67, 8.0)
NOMINAL_SIGMA_C_M = 1.0
NOMINAL_SIGMA_PSI_DERECE = 5.0
NOMINAL_KIP_H = (("4:3", 32.0), ("16:9", 40.0))
NOMINAL_SIGMA_G_M = 2.0
KAPI_DISI_S_M = (5.0,)                          # raporlanir, kapiya girmez
KAPI_ORAN_YUZDE = 99.0                          # nominal hucrede dogru orani >= %99,0
KAPI_KARE_FARK_PUAN = 0.5                       # hicbir hucrede KARE'den > 0,5 puan kotu degil
ALAN_SIGMA_ASGARI_PAY_M = 1.0                   # pay < 1,0 m -> yapilandirma FDA'da kullanilmaz
K3N_S_M = 5.0
K3N_KARE_BEKLENEN = [2, 2, 2]
# ── ON KAYIT SS3 (K1) ───────────────────────────────────────────────────────
K1_BEKLENEN_A1 = (28, 28)
K1_BEKLENEN_KARE = {"kerteriz": (3, 8), "kosum_tur3_uretim": (6, 20)}

# ── Tezgah uygulama secimleri (on kayitta yok; README'de yazili) ────────────
ALAN_GENISLIK_M = ks.FDA_ALAN_GENISLIK_M        # 20 m (sartname :726-745)
ALAN_BOY_M = ks.FDA_ALAN_GENISLIK_M             # 20x20 alan: Baslangic -> Hedef boyu
TEZGAH_KERTERIZ_DERECE = 37.0
TEZGAH_MONTAJ_YAW_DERECE = 90.0
KIP_ORAN = {"4:3": (4, 3), "16:9": (16, 9)}


def tuval_px(kok: Path = KOK) -> int:
    """Uretim cikarim tuvali (letterbox kare): kayit defterinin etkin profilindeki imgsz."""
    veri = json.loads((kok / "config" / "model_registry.json").read_text(encoding="utf-8"))
    return int(veri["profiles"][veri["default_profile"]]["imgsz"])


def icerik_kutusu(kip: str, tuval: int | None = None) -> tuple[int, int, int, int]:
    """Yatay goruntunun kare tuvaldeki letterbox icerik kutusu (x0, y0, w, h)."""
    t = tuval_px() if tuval is None else int(tuval)
    a, b = KIP_ORAN[kip]
    h = int(round(t * b / a))
    return 0, (t - h) // 2, t, h


def kare_mpp(kip: str, h_m: float, tuval: int | None = None) -> float:
    """Nadir kare olcegi — uretimdeki `mpp_irtifadan` (FOV yolu), icerik genisligiyle."""
    _x0, _y0, w, _h = icerik_kutusu(kip, tuval)
    return float(ks.mpp_irtifadan(h_m, w, yatay_fov_derece=HFOV_DERECE))


def taban_cekilisler(tohum: int = TOHUM, n: int = CEKILIS_N) -> dict:
    """Standart cekilisler (siralama SABIT: z_c, z_psi, egim, yon, z_g). Hucreler olcekler."""
    rng = np.random.default_rng(tohum)
    z_c = rng.standard_normal((n, 2))
    z_psi = rng.standard_normal(n)
    egim = rng.uniform(EGIM_ARALIGI_DERECE[0], EGIM_ARALIGI_DERECE[1], n)
    yon = rng.uniform(0.0, 2.0 * math.pi, n)
    z_g = rng.standard_normal((n, 2))
    return {"z_c": z_c, "z_psi": z_psi, "egim_derece": egim, "yon_rad": yon, "z_g": z_g}


def alan_to_enu(x: float, y: float, kerteriz_derece: float) -> tuple[float, float]:
    """KBH (x sag, y Baslangic->Hedef) -> ENU (dogu, kuzey). `kbh_donustur` 5. adiminin TERSI."""
    k = math.radians(kerteriz_derece)
    return x * math.cos(k) + y * math.sin(k), -x * math.sin(k) + y * math.cos(k)


def alan_piksel(noktalar_xy: np.ndarray, merkez_xy: np.ndarray, psi_derece: float, mpp: float,
                icerik: tuple) -> np.ndarray:
    """FIZIKSEL kamera: alan noktasi -> tuval pikseli (float). Goruntu merkezi yerde `merkez_xy`,
    goruntu-yukari alanin +y'sinden saat yonunde psi donuk (nadir, duz zemin)."""
    x0, y0, w, h = icerik
    cx, cy = x0 + w / 2.0, y0 + h / 2.0
    p = math.radians(psi_derece)
    rel = np.asarray(noktalar_xy, dtype=float) - np.asarray(merkez_xy, dtype=float)
    du = (rel[:, 0] * math.cos(p) - rel[:, 1] * math.sin(p)) / mpp
    dv = (rel[:, 0] * math.sin(p) + rel[:, 1] * math.cos(p)) / mpp
    return np.column_stack([cx + du, cy - dv])


def yol_pikselleri(x_yol: float, merkez_xy, psi_derece: float, mpp: float, icerik: tuple) -> np.ndarray:
    """Sentetik maske: x = x_yol'daki duz yol merkez hatti (y in [-L/2, L/2]) -> icerik kutusundaki
    LINE_8 pikselleri (tuval koordinati, N x 2 int). Kutu disi kirpilir (kamera gormez)."""
    x0, y0, w, h = icerik
    uc = alan_piksel(np.array([[x_yol, -ALAN_BOY_M / 2.0], [x_yol, ALAN_BOY_M / 2.0]]),
                     merkez_xy, psi_derece, mpp, icerik)
    tuval = np.zeros((h, w), np.uint8)
    p1 = (int(round(uc[0, 0] - x0)), int(round(uc[0, 1] - y0)))
    p2 = (int(round(uc[1, 0] - x0)), int(round(uc[1, 1] - y0)))
    cv2.line(tuval, p1, p2, 255, 1, cv2.LINE_8)
    ys, xs = np.nonzero(tuval)
    return np.column_stack([xs + x0, ys + y0]).astype(np.int64)


def alan_tam_karede_mi(merkez_xy, psi_derece: float, mpp: float, icerik: tuple) -> bool:
    """TESHIS: 20x20 alanin dort kosesi icerik kutusunda mi."""
    x0, y0, w, h = icerik
    ya = ALAN_GENISLIK_M / 2.0
    yb = ALAN_BOY_M / 2.0
    k = alan_piksel(np.array([[-ya, -yb], [ya, -yb], [ya, yb], [-ya, yb]]), merkez_xy, psi_derece, mpp, icerik)
    return bool(np.all((k[:, 0] >= x0) & (k[:, 0] <= x0 + w) & (k[:, 1] >= y0) & (k[:, 1] <= y0 + h)))


def sahne_etiketleri(s_m: float, kip: str, h_m: float, acik_yol: int, e_c, psi_derece: float,
                     d_egim, e_g_listesi, tuval: int | None = None) -> dict:
    """Bir sahne: fiziksel goruntu merkezi = e_c + d_egim, yaw psi. Uc yontemin etiketi.

    A1 IHA konumunu e_c + e_g sanir, egimi bilmez, basi komut edilen (kerteriz - montaj) okur."""
    icerik = icerik_kutusu(kip, tuval)
    x0, y0, w, h = icerik
    mpp = kare_mpp(kip, h_m, tuval)
    e_c = np.asarray(e_c, dtype=float)
    merkez = e_c + np.asarray(d_egim, dtype=float)
    x_yol = {1: -s_m, 2: 0.0, 3: s_m}[acik_yol]
    pix = yol_pikselleri(x_yol, merkez, psi_derece, mpp, icerik)
    kare, _ = ks.rota_serit_karari(pix.tolist(), x0, w)
    a0, _say, pay = ks.alan_serit_karari(pix, x0, w, mpp, ALAN_GENISLIK_M)
    a1 = []
    for e_g in e_g_listesi:
        ph = e_c + np.asarray(e_g, dtype=float)
        dogu, kuzey = alan_to_enu(float(ph[0]), float(ph[1]), TEZGAH_KERTERIZ_DERECE)
        k, _ = ks.kbh_serit_karari(pix, merkez_px=(x0 + w / 2.0, y0 + h / 2.0), mpp=mpp,
                                   iha_dogu_m=dogu, iha_kuzey_m=kuzey,
                                   hdg_derece=TEZGAH_KERTERIZ_DERECE - TEZGAH_MONTAJ_YAW_DERECE,
                                   montaj_yaw_derece=TEZGAH_MONTAJ_YAW_DERECE,
                                   kerteriz_derece=TEZGAH_KERTERIZ_DERECE,
                                   alan_genislik_m=ALAN_GENISLIK_M)
        a1.append(k)
    return {"KARE": kare, "A0": a0, "A0_pay_m": None if pay is None else pay["pay_m"], "A1": a1,
            "piksel_n": int(len(pix)), "alan_tam_karede": alan_tam_karede_mi(merkez, psi_derece, mpp, icerik)}


def hucre_anahtari(s_m: float, kip: str, h_m: float, sigma_c: float, sigma_psi: float) -> str:
    return f"s={s_m:g}|{kip}@{h_m:g}m|sc={sigma_c:g}|spsi={sigma_psi:g}"


def hucre_bayraklari(s_m: float, kip: str, h_m: float, sigma_c: float, sigma_psi: float) -> dict:
    """ON_KAYIT SS2 hucre sinifi — TEK tanim (hucre_kos, duyarlilik ve testler buradan okur).

      bilgi_hucresi : (kip, h) = (16:9, 32 m) — raporlanir, kapiya girmez
      kapiya_girer  : bilgi hucresi degil VE s = 5 m degil ("s = 5 m hucreleri raporlanir,
                      kapiya girmez") — kosul 2 (KARE - 0,5 puan) bu hucrelerde denetlenir
      nominal       : kapiya girer VE s in {6,67; 8}, s_c = 1,0 m, s_psi = 5 derece,
                      (kip, h) in {(4:3, 32), (16:9, 40)} — kosul 1 (>= %99,0) burada denetlenir
    """
    bilgi = (kip, h_m) in BILGI_KIP_H
    kapiya_girer = (not bilgi) and (s_m not in KAPI_DISI_S_M)
    nominal = (kapiya_girer and s_m in NOMINAL_S_M and sigma_c == NOMINAL_SIGMA_C_M
               and sigma_psi == NOMINAL_SIGMA_PSI_DERECE and (kip, h_m) in NOMINAL_KIP_H)
    return {"bilgi_hucresi": bool(bilgi), "kapiya_girer": bool(kapiya_girer), "nominal": bool(nominal)}


def _oran(dogru: int, n: int) -> float:
    return round(100.0 * dogru / n, 3)


def hucre_kos(s_m: float, kip: str, h_m: float, sigma_c: float, sigma_psi: float,
              taban: dict | None = None, tuval: int | None = None) -> dict:
    """Bir hucre: CEKILIS_N cekilis x 3 acik yol; uc yontem ayni cekilislerle."""
    taban = taban_cekilisler() if taban is None else taban
    n = len(taban["z_psi"])
    dogru = {"KARE": [0, 0, 0], "A0": [0, 0, 0]}
    dogru_a1 = {sg: [0, 0, 0] for sg in SIGMA_G_M}
    karar_yok = {"KARE": 0, "A0": 0, "A1": {sg: 0 for sg in SIGMA_G_M}}
    paylar = []
    tam_karede = 0
    for i in range(n):
        e_c = sigma_c * taban["z_c"][i]
        psi = sigma_psi * float(taban["z_psi"][i])
        t = h_m * math.tan(math.radians(float(taban["egim_derece"][i])))
        yon = float(taban["yon_rad"][i])
        d = np.array([t * math.cos(yon), t * math.sin(yon)])
        e_g = [sg * taban["z_g"][i] for sg in SIGMA_G_M]
        for yol in (1, 2, 3):
            r = sahne_etiketleri(s_m, kip, h_m, yol, e_c, psi, d, e_g, tuval)
            for ad in ("KARE", "A0"):
                if r[ad] is None:
                    karar_yok[ad] += 1
                elif r[ad] == yol:
                    dogru[ad][yol - 1] += 1
            for sg, k in zip(SIGMA_G_M, r["A1"]):
                if k is None:
                    karar_yok["A1"][sg] += 1
                elif k == yol:
                    dogru_a1[sg][yol - 1] += 1
            if r["A0_pay_m"] is not None:
                paylar.append(r["A0_pay_m"])
            tam_karede += int(r["alan_tam_karede"])
    sahne_n = 3 * n
    bayrak = hucre_bayraklari(s_m, kip, h_m, sigma_c, sigma_psi)
    bilgi, kapiya_girer, nominal = bayrak["bilgi_hucresi"], bayrak["kapiya_girer"], bayrak["nominal"]

    def blok(say, yok):
        return {"dogru": int(sum(say)), "sahne_n": sahne_n, "oran_yuzde": _oran(sum(say), sahne_n),
                "acik_yol_basina_dogru": [int(v) for v in say], "karar_yok": int(yok)}

    pay = np.asarray(paylar, dtype=float)
    a0 = blok(dogru["A0"], karar_yok["A0"])
    a0["pay_m_p01_p05_medyan"] = ([round(float(np.percentile(pay, q)), 3) for q in (1, 5, 50)]
                                  if pay.size else None)
    return {
        "hucre": hucre_anahtari(s_m, kip, h_m, sigma_c, sigma_psi),
        "s_m": s_m, "kip": kip, "h_m": h_m, "sigma_c_m": sigma_c, "sigma_psi_derece": sigma_psi,
        "bilgi_hucresi": bilgi, "kapiya_girer": kapiya_girer, "nominal": nominal,
        "cekilis_n": n, "sahne_n": sahne_n,
        "KARE": blok(dogru["KARE"], karar_yok["KARE"]),
        "A0": a0,
        "A1": {f"sigma_g={sg:g}": blok(dogru_a1[sg], karar_yok["A1"][sg]) for sg in SIGMA_G_M},
        "alan_tam_karede_oran_yuzde": _oran(tam_karede, sahne_n),
        "etiket": ETIKET,
    }


def izgara() -> list[tuple]:
    return [(s, kip, h, sc, sp) for s in S_DEGERLERI_M for kip, h in KIP_H
            for sc in SIGMA_C_M for sp in SIGMA_PSI_DERECE]


def k3n_kos(tuval: int | None = None) -> dict:
    """Negatif kontrol K3n: KARE, s = 5 m, merkezli, hatasiz karede [2, 2, 2] uretmeli.
    A0/A1 ayni sahnede [1, 2, 3] BILGI olarak raporlanir (pozitif kontrol; kapi degil)."""
    out = {"s_m": K3N_S_M, "beklenen_KARE": K3N_KARE_BEKLENEN, "yapilandirmalar": [], "etiket": ETIKET}
    hepsi = True
    for kip, h in KIP_H:
        sat = {"kip": kip, "h_m": h, "KARE": [], "A0": [], "A1": []}
        for yol in (1, 2, 3):
            r = sahne_etiketleri(K3N_S_M, kip, h, yol, (0.0, 0.0), 0.0, (0.0, 0.0), [(0.0, 0.0)], tuval)
            sat["KARE"].append(r["KARE"])
            sat["A0"].append(r["A0"])
            sat["A1"].append(r["A1"][0])
        sat["KARE_uretti"] = sat["KARE"] == K3N_KARE_BEKLENEN
        hepsi = hepsi and sat["KARE_uretti"]
        out["yapilandirmalar"].append(sat)
    out["gecti"] = hepsi
    return out


def alan_sigma(tuval: int | None = None) -> list[dict]:
    """Her (kip, h): 20x20 alanin karede kalma payi (nominal, hatasiz; HESAP)."""
    out = []
    for kip, h in KIP_H:
        _x0, _y0, w, hh = icerik_kutusu(kip, tuval)
        mpp = kare_mpp(kip, h, tuval)
        gen, boy = w * mpp, hh * mpp
        pay = min(gen - ALAN_GENISLIK_M, boy - ALAN_BOY_M) / 2.0
        out.append({"kip": kip, "h_m": h, "mpp": round(mpp, 6), "kare_genislik_m": round(gen, 3),
                    "kare_boy_m": round(boy, 3), "pay_m": round(pay, 3),
                    "fda_kullanilir": bool(pay >= ALAN_SIGMA_ASGARI_PAY_M), "etiket": ETIKET})
    return out


def kapi_degerlendir(hucreler: list[dict]) -> dict:
    """ON_KAYIT SS2 kapisi — KESIR aritmetigi (yuvarlama/float kapiyi cevirmez); esikler
    on kayitli sabitlerden (KAPI_ORAN_YUZDE, KAPI_KARE_FARK_PUAN) okunur, burada ciplak sayi yok.
      kosul 1: nominal hucrelerde 100*dogru/n >= KAPI_ORAN_YUZDE (99,0)
      kosul 2: kapiya giren HER hucrede (s=5 ve bilgi hucresi haric; A1'de her s_g)
               100*(dM - dKARE)/n >= -KAPI_KARE_FARK_PUAN (0,5 puan); tam -0,5 puan GECER
               ("0,5 puandan FAZLA kotu degil")
    """
    esik_oran = Fraction(str(KAPI_ORAN_YUZDE))
    esik_fark = Fraction(str(KAPI_KARE_FARK_PUAN))
    sonuc = {}
    for yontem in ("A0", "A1"):
        k1_sat, k2_ihlal, k2_n = [], [], 0
        for hc in hucreler:
            bloklar = ([("A0", hc["A0"])] if yontem == "A0"
                       else [(anah, b) for anah, b in hc["A1"].items()])
            kare = hc["KARE"]
            for ad, b in bloklar:
                n = b["sahne_n"]
                if hc["nominal"] and (yontem == "A0" or ad == f"sigma_g={NOMINAL_SIGMA_G_M:g}"):
                    k1_sat.append({"hucre": hc["hucre"], "blok": ad, "oran_yuzde": b["oran_yuzde"],
                                   "gecti": Fraction(100 * b["dogru"], n) >= esik_oran})
                if hc["kapiya_girer"]:
                    k2_n += 1
                    fark = b["dogru"] - kare["dogru"]
                    if Fraction(100 * fark, n) < -esik_fark:
                        k2_ihlal.append({"hucre": hc["hucre"], "blok": ad,
                                         "fark_puan": round(100.0 * fark / n, 3)})
        k1 = bool(k1_sat) and all(s["gecti"] for s in k1_sat)
        yapilandirma = {}
        for kip, h in NOMINAL_KIP_H:
            anah = f"{kip}@{h:g}m"
            sat = [s for s in k1_sat if f"|{anah}|" in s["hucre"]]
            ihl = [v for v in k2_ihlal if f"|{anah}|" in v["hucre"]]
            yapilandirma[anah] = {"kosul1": bool(sat) and all(s["gecti"] for s in sat), "kosul2": not ihl}
        sonuc[yontem] = {"kosul1_nominal_oran": k1_sat, "kosul1_gecti": k1,
                         "kosul2_denetlenen_blok_n": k2_n, "kosul2_ihlaller": k2_ihlal,
                         "kosul2_gecti": not k2_ihlal, "gecti": bool(k1 and not k2_ihlal),
                         "yapilandirma_basina_BILGI": yapilandirma}
    return sonuc


def hukum_kur(k3n: dict, kapi: dict, sigma: list[dict]) -> dict:
    """ON_KAYIT SS2 karar kurali — onceden yazili; sonuc ne cikarsa o."""
    if not k3n["gecti"]:
        return {"tezgah_bos": True, "karar": "HUKUM YOK — K3n negatif kontrolu uretilmedi (tezgah bos)",
                "A0": None, "A1": None, "etiket": ETIKET}
    a0, a1 = kapi["A0"]["gecti"], kapi["A1"]["gecti"]
    if a0:
        karar = "A0 kapiyi GECTI -> FDA'da A0 bayrakla acilir (ON_KAYIT SS2)."
    elif a1:
        karar = ("A0 DUSTU, A1 GECTI -> A1 yalniz T235-C poz kolu + tezgah/SITL kaniti 21 Eylul'den "
                 "once hazirsa acilir; degilse KARE kalir (ON_KAYIT SS2).")
    else:
        karar = "A0 DUSTU, A1 DUSTU -> KARE kalir (ON_KAYIT SS2)."
    kullanilmaz = [f'{s["kip"]}@{s["h_m"]:g}m' for s in sigma if not s["fda_kullanilir"]]
    return {"tezgah_bos": False, "A0": "GECTI" if a0 else "DUSTU", "A1": "GECTI" if a1 else "DUSTU",
            "karar": karar, "her_durumda": "YKS etiketin cercevesini niteler (T235-A).",
            "alan_sigma_ile_fda_disi_yapilandirma": kullanilmaz, "etiket": ETIKET}


def _hukum_sozcugu(gecti: bool) -> str:
    return "GECTI" if gecti else "DUSTU"


def _yapilandirma_kapisi(hucreler: list[dict], kip: str, h_m: float) -> dict:
    """Yalniz (kip, h) yapilandirmasinin hucreleriyle ON_KAYIT SS2 kapisi — ayni esik, ayni iki
    kosul, yalniz hucre kumesi dardir. TURETME: kayitli tablodan okunur, cekilis YOK."""
    alt = [hc for hc in hucreler if f"|{kip}@{h_m:g}m|" in hc["hucre"]]
    kapi = kapi_degerlendir(alt)
    return {"yapilandirma": f"{kip}@{h_m:g}m", "hucre_n": len(alt), "kapi": kapi,
            "A0": _hukum_sozcugu(kapi["A0"]["gecti"]), "A1": _hukum_sozcugu(kapi["A1"]["gecti"])}


def kapi_duyarliligi(k3: dict) -> dict:
    """Kapinin hangi hucrelere DUYARLI oldugu + D-457 kosullu on kaydinin TURETILMESI.

    🔴 Yeni olcum YOKTUR: girdi kayitli `k3_hucre_tablosu.json` sozlugudur, cikti onun saf bir
    fonksiyonudur (cekilis, rasterleme, rastgelelik yok). Iki soruya cevap verir:

      1. **Duyarlilik:** kapiya giren 16 hucre TEK BASINA degerlendirildiginde hukum degisiyor mu?
         Degismiyorsa kapi disi 20 hucre (s = 5 m + bilgi hucresi) hukmu tasimamistir — ON_KAYIT
         SS2'nin "raporlanir, kapiya girmez" ifadesinin sayisal kaniti.
      2. **D-457 kosullu on kaydi:** 12 Eylul A9'da kamera kipi olculunce FDA tek yapilandirmaya
         iner. Her yapilandirma icin kapi AYNI esikle (%99,0 ve 0,5 puan) yeniden kurulur ve
         hangi kip olculurse hangi etiketin kalacagi SIMDIDEN yazilir. Esik gevsetilmesi degildir;
         hucre kumesi degisir, olcut degismez.
    """
    hucreler = []
    for j, c in enumerate(izgara()):
        anahtar = hucre_anahtari(*c)
        kayitli = [hc for hc in k3["hucreler"] if hc["hucre"] == anahtar]
        if len(kayitli) != 1:
            raise ValueError(f"kayitli tabloda {anahtar} tek degil ({len(kayitli)})")
        if not hucre_bayraklari(*c)["kapiya_girer"]:
            continue
        hucreler.append(dict(kayitli[0], izgara_indeksi=j))
    kapi = kapi_degerlendir(hucreler)
    a0, a1 = kapi["A0"]["gecti"], kapi["A1"]["gecti"]
    yap = {f"{kip}@{h:g}m": _yapilandirma_kapisi(k3["hucreler"], kip, h) for kip, h in NOMINAL_KIP_H}
    kosullu = {}
    for kip, h in NOMINAL_KIP_H:
        v = yap[f"{kip}@{h:g}m"]
        kosullu[kip] = {"yapilandirma": v["yapilandirma"], "A0": v["A0"], "A1": v["A1"],
                        "fda_etiketi": "A0" if v["A0"] == "GECTI" else "KARE",
                        "a0_bayrakla_acilir": v["A0"] == "GECTI"}
    return {
        "etiket": DUY_ETIKET,
        "kaynak": K3_JSON,
        "on_kayit": [ON_KAYIT_YOLU + " SS2", D457_YOLU],
        "yeni_olcum_yok": True,
        "hucreler": hucreler,
        "kapi_disi_hucre_n": len(k3["hucreler"]) - len(hucreler),
        "kapi": kapi,
        "A0": _hukum_sozcugu(a0),
        "A1": _hukum_sozcugu(a1),
        "tam_tablo_kapisiyla_ayni": k3["kapi"] == json.loads(json.dumps(kapi)),
        "bugunku_hukum": {
            "A0": k3["hukum"]["A0"], "A1": k3["hukum"]["A1"],
            "fda_etiketi": "A0" if a0 else ("A1" if a1 else "KARE"),
            # ON_KAYIT SS2 karar kurali: A1 (ve T235-C poz kolu) YALNIZ A0 duser A1 gecerse.
            "t235c_poz_kolu_acilir": bool((not a0) and a1),
        },
        "yapilandirma_basina": yap,
        "d457_kosullu": {
            "kaynak": D457_YOLU,
            "kural": ("12 Eylül A9'da ölçülen kamera kipinin yapılandırması geçerli sayılır; kapı "
                      "AYNI eşikle (%99,0 ve KARE'den 0,5 puan) yalnız o yapılandırmanın hücreleriyle "
                      "kurulur. Ölçüm yeniden koşulmaz; kayıtlı tablo okunur."),
            "kip_olculurse": kosullu,
            "kip_olculemezse": {"fda_etiketi": "KARE", "a0_bayrakla_acilir": False},
        },
    }


def tezgah_kos(hucre_listesi: list[tuple] | None = None, tuval: int | None = None,
               ilerleme: bool = False) -> dict:
    taban = taban_cekilisler()
    hucreler = []
    for j, (s, kip, h, sc, sp) in enumerate(izgara() if hucre_listesi is None else hucre_listesi):
        t0 = time.perf_counter()
        hucreler.append(hucre_kos(s, kip, h, sc, sp, taban, tuval))
        if ilerleme:
            print(f"  [{j + 1}] {hucreler[-1]['hucre']}: KARE {hucreler[-1]['KARE']['oran_yuzde']} "
                  f"A0 {hucreler[-1]['A0']['oran_yuzde']} "
                  f"A1 {[b['oran_yuzde'] for b in hucreler[-1]['A1'].values()]} "
                  f"({time.perf_counter() - t0:.1f} s)", flush=True)
    k3n = k3n_kos(tuval)
    sigma = alan_sigma(tuval)
    kapi = kapi_degerlendir(hucreler)
    return {
        "etiket": ETIKET,
        "on_kayit": ON_KAYIT_YOLU,
        "parametreler": {
            "tohum": TOHUM, "cekilis_n": CEKILIS_N, "s_m": list(S_DEGERLERI_M),
            "kip_h": [[k, h] for k, h in KIP_H], "bilgi_kip_h": [[k, h] for k, h in BILGI_KIP_H],
            "sigma_c_m": list(SIGMA_C_M), "sigma_psi_derece": list(SIGMA_PSI_DERECE),
            "sigma_g_m": list(SIGMA_G_M), "egim_derece": list(EGIM_ARALIGI_DERECE),
            "hfov_derece": round(HFOV_DERECE, 4), "alan_m": [ALAN_GENISLIK_M, ALAN_BOY_M],
            "tuval_px": tuval_px() if tuval is None else int(tuval),
            "icerik_kutusu": {kip: list(icerik_kutusu(kip, tuval)) for kip in KIP_ORAN},
            "tezgah_kerteriz_derece": TEZGAH_KERTERIZ_DERECE,
            "tezgah_montaj_yaw_derece": TEZGAH_MONTAJ_YAW_DERECE,
            "kapi": {"nominal_s_m": list(NOMINAL_S_M), "nominal_sigma_c_m": NOMINAL_SIGMA_C_M,
                     "nominal_sigma_psi_derece": NOMINAL_SIGMA_PSI_DERECE,
                     "nominal_kip_h": [[k, h] for k, h in NOMINAL_KIP_H],
                     "nominal_sigma_g_m": NOMINAL_SIGMA_G_M, "oran_yuzde_esigi": KAPI_ORAN_YUZDE,
                     "kare_fark_puan_esigi": KAPI_KARE_FARK_PUAN, "kapi_disi_s_m": list(KAPI_DISI_S_M),
                     "alan_sigma_asgari_pay_m": ALAN_SIGMA_ASGARI_PAY_M},
        },
        "k3n": k3n,
        "alan_sigma": sigma,
        "hucreler": hucreler,
        "kapi": kapi,
        "hukum": hukum_kur(k3n, kapi, sigma),
    }


# ── K1 (ON_KAYIT SS3) ───────────────────────────────────────────────────────

def _rasterla(px_list, genislik: int, yukseklik: int) -> list:
    """Analiz C yontemi: waypoint pikselleri -> LINE_8 polyline pikselleri (cv2.polylines, 1 px)."""
    c = np.zeros((yukseklik, genislik), np.uint8)
    pts = np.round(np.array(px_list)).astype(np.int32).reshape(-1, 1, 2)
    cv2.polylines(c, [pts], False, 255, 1)
    ys, xs = np.nonzero(c)
    return list(zip(xs.tolist(), ys.tolist()))


def k1_kos() -> dict:
    """A1 yer gercegi pozla 28 OPEN_ROUTE karesinde dunya yoluyla; KARE 3/8 ve 6/20 yeniden uretimi."""
    for p in (KOK / "simulation" / "scripts", BURASI):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import arena                 # noqa: E402
    import arena_mjcf            # noqa: E402
    import sim_karar_toplayici as skt   # noqa: E402

    res = int(arena_mjcf.KAM_RES_VARSAYILAN)
    # Alan (HTAB) merkezi = kose ortalamasi; kerteriz = Baslangic (guney) kenari ortasi -> Hedef
    # (kuzey) kenari ortasi (TASARIM SS3, T235-E ile ayni tanim).
    y2 = arena.HTAB / 2.0
    koseler = [(-y2, -y2), (y2, -y2), (y2, y2), (-y2, y2)]
    mx = sum(k[0] for k in koseler) / 4.0
    my = sum(k[1] for k in koseler) / 4.0
    bas = ((koseler[0][0] + koseler[1][0]) / 2.0, (koseler[0][1] + koseler[1][1]) / 2.0)
    hed = ((koseler[2][0] + koseler[3][0]) / 2.0, (koseler[2][1] + koseler[3][1]) / 2.0)
    kerteriz = math.degrees(math.atan2(hed[0] - bas[0], hed[1] - bas[1])) % 360.0

    kaynaklar = (("kerteriz", sorted((H1 / "k3_uretim_boru" / "kerteriz").glob("harita_*.json"))),
                 ("kosum_tur3_uretim", sorted((H1 / "kosum_tur3").glob("uretim_*/karar_toplayici.json"))))
    kareler, ozet = [], {}
    geri_donus_maks = 0.0
    mpp_cozunurluk_tutarsiz = 0
    for kaynak, dosyalar in kaynaklar:
        say = {"n": 0, "A1=dunya": 0, "KARE=dunya": 0, "KARE_yeniden=yayinlanan": 0}
        for f in dosyalar:
            d = json.loads(f.read_text(encoding="utf-8"))
            for s in d["kareler"]:
                if s.get("karar") != "OPEN_ROUTE":
                    continue
                poz = (s["n"], s["t"], s["x"], s["y"], s["z"], math.radians(s["yaw_derece"]))
                teta = math.radians(s["teta_derece"])
                mpp = float(s["mpp"])
                iz = 2.0 * s["z"] * math.tan(arena_mjcf.HFOV_RAD / 2.0)
                mpp_cozunurluk_tutarsiz += int(round(iz / mpp) != res)
                wp_px = [skt.dunya_piksel(a, b, poz, res, res, mpp, teta) for a, b in s["rota_dunya"]]
                pix = _rasterla(wp_px, res, res)
                kare, kare_say = ks.rota_serit_karari(pix, 0, res)
                ortak = dict(merkez_px=(res / 2.0, res / 2.0), mpp=mpp, iha_dogu_m=s["x"] - mx,
                             iha_kuzey_m=s["y"] - my, hdg_derece=90.0 - s["yaw_derece"],
                             montaj_yaw_derece=s["teta_derece"] - 90.0, kerteriz_derece=kerteriz)
                a1, a1_say = ks.kbh_serit_karari(pix, alan_genislik_m=ks.HTAB_ALAN_GENISLIK_M, **ortak)
                xs = np.array([p[0] for p in pix], dtype=float)
                ys = np.array([p[1] for p in pix], dtype=float)
                kx, ky = ks.kbh_donustur(xs, ys, **ortak)
                ref = np.array([skt.piksel_dunya(px, py, poz, res, res, mpp, teta) for px, py in pix])
                hata = float(np.max(np.hypot(kx - (ref[:, 0] - mx), ky - (ref[:, 1] - my))))
                geri_donus_maks = max(geri_donus_maks, hata)
                dunya = s["rota_dunya_yolu"]
                say["n"] += 1
                say["A1=dunya"] += int(a1 == dunya)
                say["KARE=dunya"] += int(kare == dunya)
                say["KARE_yeniden=yayinlanan"] += int(kare == s["yol"])
                kareler.append({"kaynak": kaynak, "harita": f'{d["harita"]}_{d["senaryo"]}',
                                "tohum": d.get("seed"), "kare": s["n"], "acik_yol": d["acik_yol"],
                                "dunya_yolu": dunya, "yayinlanan": s["yol"], "KARE_yeniden": kare,
                                "KARE_sayim": list(kare_say), "A1": a1, "A1_sayim": list(a1_say),
                                "kbh_sim_geri_donus_maks_m": round(hata, 9)})
        ozet[kaynak] = say
    n_top = sum(o["n"] for o in ozet.values())
    a1_top = sum(o["A1=dunya"] for o in ozet.values())
    kare_uretti = all((ozet[k]["KARE=dunya"], ozet[k]["n"]) == K1_BEKLENEN_KARE[k] for k in K1_BEKLENEN_KARE)
    yeniden = all(o["KARE_yeniden=yayinlanan"] == o["n"] for o in ozet.values())
    a1_gecti = (a1_top, n_top) == K1_BEKLENEN_A1
    return {"etiket": K1_ETIKET, "on_kayit": ON_KAYIT_YOLU + " SS3",
            "not": "uygulama testi — bagimsiz kanit DEGIL (Analiz C karsi-olgusunun yeniden uretimi)",
            "sim_cozunurluk_px": res, "mpp_cozunurluk_tutarsiz_kare_n": mpp_cozunurluk_tutarsiz,
            "alan_merkezi_htab": [mx, my], "kerteriz_derece": round(kerteriz, 6),
            "alan_genislik_m": ks.HTAB_ALAN_GENISLIK_M,
            "ozet": ozet, "A1_dunya": [a1_top, n_top], "A1_beklenen": list(K1_BEKLENEN_A1),
            "KARE_beklenen": {k: list(v) for k, v in K1_BEKLENEN_KARE.items()},
            "KARE_negatif_kontrol_uretildi": kare_uretti, "KARE_yayin_yeniden_uretildi": yeniden,
            "kbh_sim_geri_donus_maks_m": round(geri_donus_maks, 9),
            "tezgah_bos": not (kare_uretti and yeniden),
            "gecti": bool(a1_gecti and kare_uretti and yeniden),
            "kareler": kareler}


# ── Yazim ───────────────────────────────────────────────────────────────────

def json_metni(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1) + "\n"


def _yz(b: dict) -> str:
    return f'{b["oran_yuzde"]:.2f} ({b["dogru"]}/{b["sahne_n"]})'


def readme_metni(k3: dict, k1: dict | None, duy: dict) -> str:
    L = []
    E = ETIKET
    p = k3["parametreler"]
    L.append("# T235-D · FDA yol etiketi tezgâhı — ölçüm (ON_KAYIT §2 + §3)")
    L.append("")
    L.append(f"> ⚠ **{E.upper()}.** Render yok, GPU yok, MuJoCo koşusu yok. Bu klasördeki her sayı "
             f"*{E}* etiketlidir (K1 satırları: *{K1_ETIKET}*).")
    L.append(">")
    L.append(f"> Ön kayıt: `{ON_KAYIT_YOLU}` (ölçümden önce yazıldı; eşik, ızgara, çekiliş, tohum değişmedi).")
    L.append("> Üreteç: `simulation/mujoco/t235_etiket_tezgahi.py` · ham tablo: "
             f"`{K3_JSON}`, `{K1_JSON}` (bu README aynı koşumdan üretildi) · türetme: `{DUY_JSON}` "
             "(kayıtlı tablodan hesap; yeni çekiliş yok).")
    L.append("")
    h = k3["hukum"]
    L.append("## Hüküm (ON_KAYIT §2 karar kuralı — önceden yazılı; sonuç ne çıktıysa o)")
    L.append("")
    if h["tezgah_bos"]:
        L.append(f"- **{h['karar']}**")
    else:
        L.append(f"- **A0: {h['A0']}** · **A1: {h['A1']}** — {E}.")
        L.append(f"- **Karar:** {h['karar']}")
        L.append(f"- {h['her_durumda']}")
        if h["alan_sigma_ile_fda_disi_yapilandirma"]:
            L.append(f"- Alan sığma payı < {ALAN_SIGMA_ASGARI_PAY_M:g} m olduğu için FDA'da kullanılmayacak "
                     f"yapılandırma: {', '.join(h['alan_sigma_ile_fda_disi_yapilandirma'])} ({E}).")
    if k1 is not None:
        L.append(f"- **K1 (uygulama testi, bağımsız kanıt değil):** A1 dünya yoluyla "
                 f"{k1['A1_dunya'][0]}/{k1['A1_dunya'][1]} (beklenen {k1['A1_beklenen'][0]}/"
                 f"{k1['A1_beklenen'][1]}); KARE negatif kontrolü "
                 f"{'ÜRETİLDİ' if k1['KARE_negatif_kontrol_uretildi'] else 'ÜRETİLMEDİ'} "
                 f"({', '.join(f'{k}: {v[0]}/{v[1]}' for k, v in ((k, (k1['ozet'][k]['KARE=dunya'], k1['ozet'][k]['n'])) for k in k1['ozet']))}) "
                 f"→ **{'GEÇTİ' if k1['gecti'] else 'DÜŞTÜ'}** ({K1_ETIKET}).")
    bh = duy["bugunku_hukum"]
    L.append(f"- **FDA'da yayınlanan yol etiketi: {bh['fda_etiketi']}.** "
             f"**T235-C (poz kolu / A1'in üretime bağlanması) {'AÇILIR' if bh['t235c_poz_kolu_acilir'] else 'AÇILMAZ'}** "
             "— ON_KAYIT §2 karar kuralı A1'i yalnız \"A0 düşer, A1 geçerse\" açar.")
    L.append("- Eşik gevşetilmedi. \"GEÇTİ\" yalnız bu tezgâh kapısı içindir; saha doğrulaması değildir, "
             "FDR'ye \"düzeltildi\" diye yazılamaz (ON_KAYIT §7).")
    L.append("")
    L.append("## Koşullu yeniden hüküm ve duyarlılık (D-457 ön kaydı) — TÜRETME, yeni ölçüm YOK")
    L.append("")
    L.append(f"> ⚠ Bu bölümdeki her sayı `{K3_JSON}`'daki **kayıtlı** hücrelerden hesaplandı "
             f"(`{DUY_JSON}`); tezgâh yeniden koşulmadı, yeni çekiliş üretilmedi. Eşik (%"
             f"{KAPI_ORAN_YUZDE:g}) ve iki koşul aynıdır; yalnız hangi hücrelerin sayıldığı değişir.")
    L.append("")
    L.append(f"- **Duyarlılık:** kapıya giren {len(duy['hucreler'])} hücre tek başına değerlendirildiğinde "
             f"kapı {'AYNI' if duy['tam_tablo_kapisiyla_ayni'] else 'FARKLI'} çıkıyor "
             f"(A0: {duy['A0']}, A1: {duy['A1']}) → kapı dışı {duy['kapi_disi_hucre_n']} hücre "
             f"(s = {'; '.join(f'{v:g}' for v in KAPI_DISI_S_M)} m ve bilgi hücresi) hükmü "
             f"{'taşımadı' if duy['tam_tablo_kapisiyla_ayni'] else 'DEĞİŞTİRDİ'}.")
    L.append(f"- **{duy['d457_kosullu']['kural']}**")
    L.append("")
    L.append("| 12 Eylül A9'da ölçülen kip | yapılandırma | koşul 1 | koşul 2 | A0 | FDA etiketi |")
    L.append("|---|---|---|---|---|---|")
    for kip, v in duy["d457_kosullu"]["kip_olculurse"].items():
        y = duy["yapilandirma_basina"][v["yapilandirma"]]["kapi"]["A0"]
        L.append(f'| {kip} | {v["yapilandirma"]} | {"✓" if y["kosul1_gecti"] else "✗"} | '
                 f'{"✓" if y["kosul2_gecti"] else "✗"} | **{v["A0"]}** | '
                 f'**{v["fda_etiketi"]}**{" (bayrakla, varsayılan kapalı)" if v["a0_bayrakla_acilir"] else ""} |')
    ko = duy["d457_kosullu"]["kip_olculemezse"]
    L.append(f'| ölçülemezse | — | — | — | — | **{ko["fda_etiketi"]}** |')
    L.append("")
    L.append("A1 aynı ayrımda: "
             + "; ".join(f'{kip} → {v["A1"]}' for kip, v in duy["d457_kosullu"]["kip_olculurse"].items())
             + f" (hiçbir yapılandırmada geçmiyor → T235-C poz kolu bu tabloyla açılmaz). Tüm satırlar: {E}.")
    L.append("")
    L.append("## Kapı (ON_KAYIT §2)")
    L.append("")
    L.append(f"Nominal hücreler: s ∈ {{{', '.join(f'{v:g}' for v in NOMINAL_S_M)}}} m, σ_c = "
             f"{NOMINAL_SIGMA_C_M:g} m, σ_ψ = {NOMINAL_SIGMA_PSI_DERECE:g}°, "
             f"{' ve '.join(f'({k}, {v:g} m)' for k, v in NOMINAL_KIP_H)}; A1 için σ_g = {NOMINAL_SIGMA_G_M:g} m. "
             f"Koşul 1: doğru oranı ≥ %{KAPI_ORAN_YUZDE:g}. Koşul 2: kapıya giren **hiçbir** hücrede "
             f"(s = 5 m ve bilgi hücresi (16:9, 32 m) hariç; A1'de her σ_g) KARE'den {KAPI_KARE_FARK_PUAN:g} "
             "puandan fazla kötü değil. Kapı tamsayı sayımlarla değerlendirildi.")
    L.append("")
    L.append("| yöntem | koşul 1 (nominal ≥ %99) | koşul 2 (KARE − 0,5 puan) | kapı |")
    L.append("|---|---|---|---|")
    for y in ("A0", "A1"):
        k = k3["kapi"][y]
        oranlar = "; ".join(f'{s["hucre"].split("|")[0]} {s["hucre"].split("|")[1]}'
                            f'{"" if y == "A0" else " " + s["blok"]}: %{s["oran_yuzde"]:.2f}'
                            f'{" ✓" if s["gecti"] else " ✗"}' for s in k["kosul1_nominal_oran"])
        L.append(f'| {y} | {"GEÇTİ" if k["kosul1_gecti"] else "DÜŞTÜ"} — {oranlar} | '
                 f'{"GEÇTİ" if k["kosul2_gecti"] else "DÜŞTÜ"} — ihlal {len(k["kosul2_ihlaller"])}/'
                 f'{k["kosul2_denetlenen_blok_n"]} blok | **{"GEÇTİ" if k["gecti"] else "DÜŞTÜ"}** |')
    L.append("")
    L.append(f"Tüm oranlar: {E}.")
    L.append("")
    for y in ("A0", "A1"):
        ihl = k3["kapi"][y]["kosul2_ihlaller"]
        if ihl:
            L.append(f"{y} koşul 2 ihlalleri ({len(ihl)}; en kötü 5): "
                     + "; ".join(f'{v["hucre"]} {v["blok"]}: {v["fark_puan"]:+.2f} puan'
                                 for v in sorted(ihl, key=lambda v: v["fark_puan"])[:5]) + f" — {E}.")
            L.append("")
    L.append("Yapılandırma başına kapı (BİLGİ — ön kayıt iki yapılandırmayı birlikte bağlar, hükmü değiştirmez):")
    L.append("")
    for y in ("A0", "A1"):
        L.append(f"- {y}: " + "; ".join(
            f'{a}: koşul1 {"✓" if v["kosul1"] else "✗"}, koşul2 {"✓" if v["kosul2"] else "✗"}'
            for a, v in k3["kapi"][y]["yapilandirma_basina_BILGI"].items()) + f" ({E})")
    L.append("")
    L.append("## Negatif kontrol K3n")
    L.append("")
    L.append(f"KARE, s = {K3N_S_M:g} m, merkezli, hatasız karede {K3N_KARE_BEKLENEN} üretmeli "
             f"(açık yol 1/2/3 sırasıyla). A0/A1 aynı sahnede BİLGİ (pozitif kontrol).")
    L.append("")
    L.append("| (kip, h) | KARE | A0 | A1 | KARE üretti mi |")
    L.append("|---|---|---|---|---|")
    for s in k3["k3n"]["yapilandirmalar"]:
        L.append(f'| ({s["kip"]}, {s["h_m"]:g} m) | {s["KARE"]} | {s["A0"]} | {s["A1"]} | '
                 f'{"EVET" if s["KARE_uretti"] else "HAYIR"} |')
    L.append("")
    L.append(f'K3n: **{"ÜRETİLDİ — tezgâh boş değil" if k3["k3n"]["gecti"] else "ÜRETİLMEDİ — TEZGÂH BOŞ, hüküm yok"}** ({E}).')
    L.append("")
    L.append("## Alan sığma (HESAP, hatasız nominal kare)")
    L.append("")
    L.append("| (kip, h) | mpp (m/px) | kare genişlik × boy (m) | 20×20 alan payı (m) | FDA'da kullanılır mı (pay ≥ 1,0 m) |")
    L.append("|---|---|---|---|---|")
    for s in k3["alan_sigma"]:
        L.append(f'| ({s["kip"]}, {s["h_m"]:g} m) | {s["mpp"]:.5f} | {s["kare_genislik_m"]:.2f} × '
                 f'{s["kare_boy_m"]:.2f} | {s["pay_m"]:+.2f} | {"EVET" if s["fda_kullanilir"] else "HAYIR"} |')
    L.append("")
    L.append(f"Tüm satırlar: {E}.")
    L.append("")
    L.append("## Hücre tablosu (doğru oranı %, doğru/sahne; sahne = 2000 çekiliş × 3 açık yol)")
    L.append("")
    L.append(f"Her hücre: {E}. `N` = nominal hücre, `b` = bilgi hücresi, `-` = kapı dışı (s = 5 m).")
    L.append("")
    L.append("| s (m) | (kip, h) | σ_c (m) | σ_ψ (°) | | KARE | A0 | A1 σ_g=1 | A1 σ_g=2 | A0 − KARE (puan) | A0 pay p01/p05/medyan (m) | alan tam karede % |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for hc in k3["hucreler"]:
        isaret = "N" if hc["nominal"] else ("b" if hc["bilgi_hucresi"] else ("-" if not hc["kapiya_girer"] else ""))
        a1 = hc["A1"]
        fark = hc["A0"]["oran_yuzde"] - hc["KARE"]["oran_yuzde"]
        pay = hc["A0"]["pay_m_p01_p05_medyan"]
        L.append(f'| {hc["s_m"]:g} | ({hc["kip"]}, {hc["h_m"]:g}) | {hc["sigma_c_m"]:g} | {hc["sigma_psi_derece"]:g} | '
                 f'{isaret} | {_yz(hc["KARE"])} | {_yz(hc["A0"])} | {_yz(a1["sigma_g=1"])} | {_yz(a1["sigma_g=2"])} | '
                 f'{fark:+.2f} | {"/".join(f"{v:.2f}" for v in pay) if pay else "-"} | '
                 f'{hc["alan_tam_karede_oran_yuzde"]:.1f} |')
    L.append("")
    if k1 is not None:
        L.append("## T235-K1 — uygulama testi (ON_KAYIT §3; bağımsız kanıt DEĞİL)")
        L.append("")
        L.append(f"Veri: `H1/k3_uretim_boru/kerteriz/harita_*.json` (8 OPEN_ROUTE) ve "
                 f"`H1/kosum_tur3/uretim_*/karar_toplayici.json` (20 OPEN_ROUTE). Rota `rota_dunya` → "
                 f"`sim_karar_toplayici.dunya_piksel` → `cv2.polylines` LINE_8 ({k1['sim_cozunurluk_px']} px; "
                 f"Analiz C yöntemi). A1: `kbh_serit_karari`, yer gerçeği poz, alan = HTAB "
                 f"({k1['alan_genislik_m']:g} m; merkez köşe ortalaması {k1['alan_merkezi_htab']}, kerteriz "
                 f"{k1['kerteriz_derece']:g}°), hdg = 90 − yaw, montaj = θ − 90.")
        L.append("")
        L.append("| kaynak | kare | A1 = dünya yolu | KARE = dünya yolu | KARE yeniden = yayınlanan |")
        L.append("|---|---|---|---|---|")
        for k, o in k1["ozet"].items():
            L.append(f'| {k} | {o["n"]} | {o["A1=dunya"]}/{o["n"]} | {o["KARE=dunya"]}/{o["n"]} | '
                     f'{o["KARE_yeniden=yayinlanan"]}/{o["n"]} |')
        L.append("")
        L.append(f"- `kbh_donustur` ↔ `sim_karar_toplayici.piksel_dunya` geri dönüş farkı (tüm rota pikselleri): "
                 f"en çok {k1['kbh_sim_geri_donus_maks_m']:.2e} m. mpp ↔ çözünürlük tutarsız kare: "
                 f"{k1['mpp_cozunurluk_tutarsiz_kare_n']}.")
        L.append(f"- Hepsi: {K1_ETIKET}.")
        L.append("")
    L.append("## Yöntem ve uygulama seçimleri")
    L.append("")
    L.append(f"- **Sentetik maske:** 20×20 m alanda Başlangıç→Hedef doğrultusunda üç DÜZ yol, x = −s, 0, +s; "
             f"y = −10…+10 m. Açık yolun merkez hattı rota sayılır ve üretim çıkarım tuvalinde "
             f"({p['tuval_px']} px kare, letterbox; içerik kutusu 4:3 {p['icerik_kutusu']['4:3']}, 16:9 "
             f"{p['icerik_kutusu']['16:9']}) `cv2.line` LINE_8 ile rasterlanır; kutu dışı kırpılır. "
             f"mpp = `mpp_irtifadan(h, içerik genişliği, HFOV {p['hfov_derece']:.2f}°)`.")
    L.append("- **Fiziksel kamera (her çekiliş):** görüntü merkezi yerde e_c + h·tan(eğim)·(cos φ, sin φ); "
             "görüntü-yukarısı alan +y'sinden saat yönünde ψ dönük; nadir, düz zemin.")
    L.append("- **KARE** `rota_serit_karari`, **A0** `alan_serit_karari` (W = 20 m), **A1** `kbh_serit_karari` — "
             "üretim modülündeki fonksiyonların kendisi çağrılır.")
    L.append("- **A1'in bildiği:** İHA konumu e_c + e_g (GPS kestirim hatası), baş = komut edilen "
             f"(kerteriz − montaj); eğimi bilmez (ATTITUDE yok). ψ pusula kaynaklıdır: otopilot ölçülen başı tutar, "
             "A1 aynı pusulayı okur → A1'in yaw artığı da ψ'dir. A1 dönüşümünü sınamak için alan kerterizi "
             f"{p['tezgah_kerteriz_derece']:g}°, montaj yaw {p['tezgah_montaj_yaw_derece']:g}° (KARE/A0 bu seçimden bağımsızdır).")
    L.append("- **Aynı çekilişler:** tohum 20260910 ile sabit sırada (z_c, z_ψ, eğim, yön, z_g) 2000 standart "
             "çekiliş üretilir; her hücre bunları σ ile ölçekler (ortak rastgele sayılar). Üç yöntem ve iki σ_g aynı "
             "çekilişi görür; hücre sonucu ızgaranın geri kalanından bağımsızdır (alt ızgara bayt-eş yeniden üretilir, "
             "`tests/test_t235_alan_etiketi.py`).")
    L.append("- **Açık yol \"eşit\":** her çekiliş üç açık yol için de değerlendirilir (hücre = 6000 sahne; açık yol "
             "başına sayım JSON'da).")
    L.append("- **s = 6,67 m** ön kayıttaki yazımıyla (6.67) alındı, 20/3 değil.")
    L.append("- Karar üretilemeyen sahne (rota karede yok) YANLIŞ sayılır; sayısı JSON'da `karar_yok`.")
    L.append("")
    L.append("## Yeniden üretim")
    L.append("")
    L.append("```")
    L.append("REM tam kosum (tezgah yeniden kosulur — ON KAYIT tohumuyla ayni sayilari uretmelidir)")
    L.append("O:\\navitas-local-train\\venv\\Scripts\\python.exe simulation/mujoco/t235_etiket_tezgahi.py")
    L.append("REM yalniz turetme (tezgah KOSULMAZ; kayitli JSON'lardan bu README ve " + DUY_JSON + ")")
    L.append("O:\\navitas-local-train\\venv\\Scripts\\python.exe simulation/mujoco/t235_etiket_tezgahi.py --turetme")
    L.append("O:\\navitas-local-train\\venv\\Scripts\\python.exe -m unittest discover -s tests -p test_t235_alan_etiketi.py")
    L.append("```")
    L.append("")
    return "\n".join(L)


def _yaz(yol: Path, metin: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "w", encoding="utf-8", newline="\n") as f:
        f.write(metin)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--yalniz-k1", action="store_true")
    ap.add_argument("--turetme", action="store_true",
                    help="tezgahi KOSMADAN kayitli JSON'lardan tureteni (kapi duyarliligi + README) yeniden yaz")
    ap.add_argument("--cikti", default=str(CIKTI_DIZIN))
    a = ap.parse_args(argv)
    out = Path(a.cikti)
    t0 = time.perf_counter()
    if a.turetme:
        k3 = json.loads((out / K3_JSON).read_text(encoding="utf-8"))
        k1 = json.loads((out / K1_JSON).read_text(encoding="utf-8"))
        duy = kapi_duyarliligi(k3)
        _yaz(out / DUY_JSON, json_metni(duy))
        _yaz(out / "README.md", readme_metni(k3, k1, duy))
        print(f"TURETME (yeni olcum YOK): A0 {duy['A0']} · A1 {duy['A1']} · tam tablo ile ayni "
              f"{duy['tam_tablo_kapisiyla_ayni']} · D-457 "
              f"{ {k: v['fda_etiketi'] for k, v in duy['d457_kosullu']['kip_olculurse'].items()} }")
        print(f"yazildi: {out} ({time.perf_counter() - t0:.1f} s)")
        return 0
    k1 = k1_kos()
    print(f"K1: A1 {k1['A1_dunya']} · KARE {({k: (o['KARE=dunya'], o['n']) for k, o in k1['ozet'].items()})} "
          f"· yeniden {k1['KARE_yayin_yeniden_uretildi']} · geri donus {k1['kbh_sim_geri_donus_maks_m']:.2e} m "
          f"-> {'GECTI' if k1['gecti'] else 'DUSTU'} ({K1_ETIKET})")
    if a.yalniz_k1:
        return 0
    k3 = tezgah_kos(ilerleme=True)
    duy = kapi_duyarliligi(k3)
    _yaz(out / K3_JSON, json_metni(k3))
    _yaz(out / K1_JSON, json_metni(k1))
    _yaz(out / DUY_JSON, json_metni(duy))
    _yaz(out / "README.md", readme_metni(k3, k1, duy))
    print(f"K3n: {k3['k3n']['gecti']} · A0 {k3['kapi']['A0']['gecti']} · A1 {k3['kapi']['A1']['gecti']}")
    print(f"HUKUM: {k3['hukum']['karar']} ({ETIKET})")
    print(f"yazildi: {out} ({time.perf_counter() - t0:.0f} s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
