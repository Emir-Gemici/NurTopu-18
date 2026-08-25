"""KARE UYGUNLUK DENETIMI — "gurultu olmasin" (kullanici talimati 2026-08-25).

Etiketlenen 160 karenin her biri BIZIM MODELIMIZE uygun mu? Uygun olmayan
kare egitimde GURULTUDUR: modele ogretilecek bir sey tasimaz ama kayip
fonksiyonunda yer kaplar.

🔴 ILK SURUM YANLISTI — DUZELTILDI (2026-08-25, gozle yakalandi).
Ilk surum esikleri `data/raw_frames`ten (otopark) turetti ve IKI YANLIS BAYRAK
uretti; ikisini de GOZLE (D-80) yakaladim:
  · POZLAMA 61 kare  -> kirpma tamamen BEYAZ SILAJ BALYALARINDAN geliyordu.
                        Kareler kusursuz; plastik ortu doyuyor, o kadar.
  · NADIR_SUPHELI 23 -> altisi da KUSURSUZ NADIR. "Gok puani" dedigim sey
                        ust seridin alttan parlak/duzgun olmasini olcuyordu;
                        kirsalda ustte ciplak toprak altta bitki olunca bu
                        DOGAL olarak cikiyor. Olcut iddia ettigim seyi
                        OLCMUYORDU.
DERS: farkli domenden turetilen esik KALITE degil DOMEN FARKI olcer. T136'nin
parlaklik kapisi calisiyordu cunku gece/gunduz icin "ortusme" DOGRU soruydu;
kirpma ve ust/alt gradyani TASINABILIR DEGIL.
Bu surumde olcutler MUTLAK ve alan-bagimsiz tanimlandi; referans yalniz
KESKINLIK icin (alt sinir) kullanilir.
Referans: `data/raw_frames` (67 otopark karesi) — bugunku uretim modellerini
URETEN veri. Bir olcut icin "kabul araligi", referansin kendi dagilimindan
alinir. Bu, T136'nin parlaklik kapisinda kurulan kalibin aynisidir:
"yeni cekimin en aydinlik karesi referansin en karanligina ulasmiyorsa DUR".

OLCUTLER (hepsi tek kareden, ek veri gerektirmez):
  1. KESKINLIK   — Laplacian varyansi. Hareket bulanikligi.
  2. POZLAMA     — kirpilmis piksel orani (0 veya 255). Yanmis/kararmis kare.
  3. NADIR       — ust seritte GOK belirtisi: parlak + dokusuz + yatay sinir.
                   (rel_alt filtresi kalkis/inisi eledi ama gimbal egik
                    olabilir; bu OLCUM onu yakalar.)
  4. ETIKET BILGISI — etiketsiz orani. Cok yuksekse kare egitime az sey katar.
  5. IKIZLIK     — algisal hash ile kume ICI yakinlik. Tekrar = gurultu degil
                   ama BILGI TASIMAZ ve dengeyi bozar.

⚠ HICBIR KARE OTOMATIK SILINMEZ. Betik yalniz OLCER ve isaretler; eleme
  karari insanin/mimarindir (D-133 ruhu). Cikti bir IS LISTESIDIR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[2]
MASKE_KOK = KOK / "results" / "dji_20260822" / "f5_olcek"
KARE_KOK = KOK / "results" / "dji_20260822" / "kareler_1fps"
REFERANS = KOK / "data" / "raw_frames"
CIKTI = KOK / "results" / "dji_kirsal" / "kare_uygunluk.json"


def olcutler(img):
    """Tek kareden olculen ham sayilar."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kucuk = cv2.resize(g, (960, 540), interpolation=cv2.INTER_AREA)
    keskinlik = float(cv2.Laplacian(kucuk, cv2.CV_64F).var())
    kirpik = float(((kucuk <= 2) | (kucuk >= 253)).mean())
    # 🔴 GOK/UFUK TESTI — MUTLAK, gradyan DEGIL.
    # Ilk surum "ust serit alttan parlak/duzgun mu" diye soruyordu ve KUSURSUZ
    # NADIR kareleri bayrakliyordu: kirsalda ustte ciplak toprak altta bitki
    # olunca o fark DOGAL olarak cikiyor (gozle dogrulandi, 6/6 yanlis alarm).
    # Gok'un AYIRT EDICI imzasi: COK parlak (>200) VE neredeyse dokusuz (<6)
    # VE UST KENARA DEGEN GENIS bir bolge. Ucu birden aranir.
    h = kucuk.shape[0]
    f = kucuk.astype(np.float32)
    o = cv2.blur(f, (9, 9))
    sd = np.sqrt(np.maximum(cv2.blur(f * f, (9, 9)) - o * o, 0))
    aday = ((kucuk > 200) & (sd < 6)).astype(np.uint8)
    gok_puani = 0.0
    if aday.any():
        n_l, lab, st, _ = cv2.connectedComponentsWithStats(aday, 8)
        ust_serit = lab[:max(1, int(h * 0.05))]
        for i in range(1, n_l):
            if (ust_serit == i).any():          # ust kenara DEGIYOR mu
                gok_puani = max(gok_puani,
                                st[i, cv2.CC_STAT_AREA] / float(kucuk.size))
    return {"keskinlik": round(keskinlik, 2),
            "kirpik_oran": round(kirpik, 5),
            "gok_puani": round(gok_puani, 4),
            "parlaklik": round(float(kucuk.mean()), 2)}


def hash64(img):
    k = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), (9, 8),
                   interpolation=cv2.INTER_AREA)
    return (k[:, 1:] > k[:, :-1]).flatten()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # ── REFERANSTAN BANT TURET ────────────────────────────────────────────
    ref = sorted(REFERANS.rglob("*.jpg"))[:400]
    if not ref:
        print("🔴 REFERANS OKUNAMADI — esik turetilemez, hukum YOK (D-180)")
        return 1
    ref_olcum = []
    for p in ref:
        im = cv2.imread(str(p))
        if im is not None:
            ref_olcum.append(olcutler(im))
    def dagilim(ad):
        v = sorted(o[ad] for o in ref_olcum)
        n = len(v)
        return {"min": v[0], "p05": v[max(0, n // 20)], "p50": v[n // 2],
                "p95": v[min(n - 1, 19 * n // 20)], "maks": v[-1]}
    ref_d = {a: dagilim(a) for a in ("keskinlik", "kirpik_oran", "gok_puani")}
    print("REFERANS `data/raw_frames` (n=%d) — esikler BURADAN turetiliyor" % len(ref_olcum))
    for a, d in ref_d.items():
        print("  %-12s min %.4f · p05 %.4f · p50 %.4f · p95 %.4f · maks %.4f"
              % (a, d["min"], d["p05"], d["p50"], d["p95"], d["maks"]))

    # BANTLAR: referansin kendi p05/p95'i. Disari tasan kare ISARETLENIR.
    # KESKINLIK: referanstan (alt sinir) — bulaniklik alan-bagimsizdir.
    kes_alt = ref_d["keskinlik"]["p05"]
    # POZLAMA ve GOK: MUTLAK esikler. Referanstan TURETILMEZ (domen farki
    # olcerlerdi — ilk surumun kusuru). Gerekce:
    #  · kirpik %20: bir karenin BESTE BIRI doymussa sahne okunamaz. Beyaz
    #    balyanin %1-3 kirpmasi MESRUDUR ve elenmemelidir.
    #  · gok %5: ust kenara degen, parlak (>200) ve dokusuz (<6) bir bolge
    #    karenin %5'ini asiyorsa orada GOK/UFUK vardir.
    kirp_ust = 0.20
    gok_ust = 0.05

    # ── KARELERI OLC ──────────────────────────────────────────────────────
    maskeler = {p.name[:-len("_uc.png")]: p
                for g in "ABCD" for p in (MASKE_KOK / g).glob("*_uc.png")}
    satirlar, hashler = [], {}
    for govde, mp in sorted(maskeler.items()):
        kaynak_dizin, stem = govde.split("__", 1)
        kare = KARE_KOK / kaynak_dizin / (stem + ".jpg")
        if not kare.is_file():
            continue
        img = cv2.imread(str(kare))
        o = olcutler(img)
        m = cv2.imread(str(mp), cv2.IMREAD_GRAYSCALE)
        o["etiketsiz_oran"] = round(float((m == 0).mean()), 4)
        o["sinif0_oran"] = round(float((m == 1).mean()), 4)
        o["sinif1_oran"] = round(float((m == 2).mean()), 4)
        bayrak = []
        if o["keskinlik"] < kes_alt:
            bayrak.append("BULANIK")
        if o["kirpik_oran"] > kirp_ust:
            bayrak.append("POZLAMA")
        if o["gok_puani"] > gok_ust:
            bayrak.append("NADIR_SUPHELI")
        if o["etiketsiz_oran"] > 0.85:
            bayrak.append("ETIKET_COK_SEYREK")
        o["kare"] = govde
        o["bayrak"] = bayrak
        satirlar.append(o)
        hashler[govde] = hash64(img)

    # ── IKIZLIK (kume ICI) ────────────────────────────────────────────────
    adlar = list(hashler)
    ikiz = []
    for i in range(len(adlar)):
        for j in range(i + 1, len(adlar)):
            d = int(np.count_nonzero(hashler[adlar[i]] != hashler[adlar[j]]))
            if d <= 5:
                ikiz.append({"a": adlar[i], "b": adlar[j], "hamming": d})
    for z in ikiz:
        for s in satirlar:
            if s["kare"] in (z["a"], z["b"]) and "IKIZ" not in s["bayrak"]:
                s["bayrak"].append("IKIZ")

    say = {}
    for s in satirlar:
        for b in s["bayrak"]:
            say[b] = say.get(b, 0) + 1
    temiz = [s for s in satirlar if not s["bayrak"]]
    print("\nSONUC (%d kare)" % len(satirlar))
    print("  BAYRAKSIZ (temiz): %d" % len(temiz))
    for b, n in sorted(say.items(), key=lambda t: -t[1]):
        print("  %-20s %3d" % (b, n))
    if ikiz:
        print("  ikiz cift: %d (hamming <= 5)" % len(ikiz))

    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    CIKTI.write_text(json.dumps(
        {"_ne": "Kare uygunluk denetimi — esikler data/raw_frames'ten TURETILDI",
         "_referans_n": len(ref_olcum), "_referans_dagilim": ref_d,
         "_bantlar": {"keskinlik_alt": kes_alt, "kirpik_ust": kirp_ust,
                      "gok_ust": gok_ust, "etiketsiz_ust": 0.85},
         "_uyari": "HICBIR KARE OTOMATIK SILINMEZ; bu bir IS LISTESIDIR.",
         "sayim": say, "temiz": len(temiz), "ikiz_ciftler": ikiz,
         "kareler": satirlar}, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nyazildi: %s" % CIKTI)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
