"""T198 kalan is (D-379) — HB SEKIL PUANI olcumu ve esik turetimi.

ON KAYIT: `results/hb_sekil/ON_KAYIT.md` — puan tanimi, turetme kurali
(pozitif %0,5 dilimi x 0,85) ve kabul olcutleri (P1 >= 258/260 tutma,
N1 <= %10 otomobil gecisi) SONUC GORULMEDEN donduruldu.

Pozitif: t66'nin 260 sentetik pedi, URETIMLE AYNI aday hattindan (yer
gercegi kutusu degil — cevrimsellige ek sahtecilik katmamak icin secim de
uretimin secimi). Negatif: T150'nin 67 otopark karesi (kirmizi otomobil FP)
+ 111 kirsal kare (15 toprak FP).

⚠ Bu betik esigi TURETIR ve verdikt yazar; sozlesmeye SABIT yazmaz.
Sabiti yazmak ayri bir adimdir ve verdikt GECTI ise yapilir (D-107 zinciri).
"""
import glob
import io
import json
import statistics
import sys
from pathlib import Path

import cv2

from ayarlar import REPO

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import hb_konumu, hb_sekil_puani  # noqa: E402

T66 = Path("O:/navitas-local-train/calisma/sentetik_arena_kadraj_t66")
OTOPARK = REPO / "data" / "raw_frames"
KIRSAL = REPO / "dataset" / "dji_kirsal_0038_bolum_v3" / "images"
CIKTI = REPO / "results" / "hb_sekil"

# ON_KAYIT §3-§4'te DONDURULDU:
DILIM = 0.005
PAY = 0.85
P1_ASGARI_TUTMA = 258 / 260.0
N1_AZAMI_GECIS = 0.10


def olc_pozitifler():
    man = json.loads((T66 / "manifest.json").read_text(encoding="utf-8"))
    kayitlar = []
    for o in man["ornekler"]:
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = T66 / o["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        a = o["arena"]
        hb = hb_konumu(img, mpp=a.get("mpp"))       # uretim hatti, sekil YOK
        kayit = {"kare": p.name, "tespit": hb is not None}
        if hb is not None:
            hx, hy, hw, hh = a["hedef_kutu"]
            cx, cy = hb["merkez"]
            dogru = (hx - 2 <= cx <= hx + hw + 2 and
                     hy - 2 <= cy <= hy + hh + 2)
            kayit["dogru_ped"] = bool(dogru)
            if dogru:
                kayit["puan"] = hb_sekil_puani(img, hb["kutu"])
        kayitlar.append(kayit)
    return kayitlar


def olc_negatifler(kok, esik, desen="**/*.jpg"):
    """KARE DUZEYI, URETIM SEMANTIGI: hb_konumu kapi ACIKKEN cagrilir.

    Ilk surum yalniz SECILEN adayin puanini olcuyordu; nobetci test bunun
    uretimden ayristigini yakaladi — dusme semantigiyle buyuk otomobil
    reddedilince kucuk lekeler uzerinden 59/67 kare YINE tespit uretiyordu.
    Simdi (1) sekil reddi NIHAI (hb_konumu D-379) ve (2) olcum kare duzeyinde.
    """
    kayitlar = []
    for p in sorted(glob.glob(str(kok / desen), recursive=True)):
        img = cv2.imread(p)
        if img is None:
            continue
        eski = hb_konumu(img)                        # T150 ile ayni: kapisiz
        yeni = hb_konumu(img, sekil_esigi=esik)      # uretim semantigi
        kayit = {"kare": Path(p).name, "tespit": eski is not None,
                 "kapiyla_tespit": yeni is not None}
        if eski is not None:
            kayit["puan"] = hb_sekil_puani(img, eski["kutu"])
        if yeni is not None:
            kayit["kapiyla_puan"] = yeni.get("sekil_puani")
        kayitlar.append(kayit)
    return kayitlar


def main():
    poz = olc_pozitifler()
    puanli = [k for k in poz if k.get("puan") is not None]
    puansiz = [k for k in poz if k["tespit"] and k.get("dogru_ped")
               and k.get("puan") is None]
    yanlis_aday = [k for k in poz if k["tespit"] and not k.get("dogru_ped")]
    tespitsiz = [k for k in poz if not k["tespit"]]
    print(f"POZITIF: n={len(poz)} · puanli {len(puanli)} · "
          f"puan uretilemedi {len(puansiz)} · yanlis aday {len(yanlis_aday)} · "
          f"tespitsiz {len(tespitsiz)}")

    if len(puanli) < 200:
        print("OLCULEMEDI: puanli pozitif < 200 — turetim yapilmaz")
        return 1

    puanlar = sorted(k["puan"] for k in puanli)
    idx = max(0, int(round(DILIM * (len(puanlar) - 1))))
    q = puanlar[idx]
    esik = q * PAY
    print(f"pozitif puan: min {puanlar[0]:.3f} · %0,5 {q:.3f} · "
          f"p50 {statistics.median(puanlar):.3f} · maks {puanlar[-1]:.3f}")
    print(f"TURETILEN ESIK = {q:.3f} x {PAY} = {esik:.4f}")

    # P1 KARE DUZEYI: olcek+sekil BIRLIKTE (uretim semantigi) — kapi acikken
    # dogru ped hala bulunuyor mu.
    man = json.loads((T66 / "manifest.json").read_text(encoding="utf-8"))
    tutulan = 0
    p1_n = 0
    p1_kayip = []
    for o in man["ornekler"]:
        if o.get("durum") != "YAZILDI" or not o.get("arena"):
            continue
        p = T66 / o["cikti"]
        img = cv2.imread(str(p)) if p.is_file() else None
        if img is None:
            continue
        p1_n += 1
        a = o["arena"]
        hb = hb_konumu(img, mpp=a.get("mpp"), sekil_esigi=esik)
        if hb is None:
            p1_kayip.append(p.name)
            continue
        hx, hy, hw, hh = a["hedef_kutu"]
        cx, cy = hb["merkez"]
        if hx - 2 <= cx <= hx + hw + 2 and hy - 2 <= cy <= hy + hh + 2:
            tutulan += 1
        else:
            p1_kayip.append(p.name + " (yanlis yer)")
    p1 = tutulan / p1_n if p1_n else 0.0
    p1_gecti = p1 >= P1_ASGARI_TUTMA
    print(f"P1 (kare duzeyi, olcek+sekil): {tutulan}/{p1_n} "
          f"(%{100 * p1:.1f}) · sart >= %{100 * P1_ASGARI_TUTMA:.1f} "
          f"-> {'GECTI' if p1_gecti else 'AYIRAMIYOR'}")

    oto = olc_negatifler(OTOPARK, esik)
    oto_tespit = [k for k in oto if k["tespit"]]
    oto_gecen = [k for k in oto if k["kapiyla_tespit"]]
    n1 = (len(oto_gecen) / len(oto_tespit)) if oto_tespit else None
    if n1 is not None:
        print(f"N1 OTOPARK (kare duzeyi): {len(oto)} kare · kapisiz tespit "
              f"{len(oto_tespit)} · kapiyla {len(oto_gecen)} "
              f"(%{100 * n1:.1f}) · sart <= %{100 * N1_AZAMI_GECIS:.0f} "
              f"-> {'GECTI' if n1 <= N1_AZAMI_GECIS else 'DUSTU'}")
    else:
        print("N1: OLCULEMEDI (tespit yok)")

    kir = olc_negatifler(KIRSAL, esik)
    kir_tespit = [k for k in kir if k["tespit"]]
    kir_gecen = [k for k in kir if k["kapiyla_tespit"]]
    print(f"N2 KIRSAL (bilgi, kare duzeyi): {len(kir)} kare · kapisiz "
          f"{len(kir_tespit)} · kapiyla {len(kir_gecen)}")

    n1_gecti = n1 is not None and n1 <= N1_AZAMI_GECIS
    verdikt = "GECTI" if (p1_gecti and n1_gecti) else "AYIRAMIYOR"
    print(f"\nVERDIKT: {verdikt}"
          + ("" if verdikt == "GECTI" else " — kapi BAGLANMAZ (ON_KAYIT §4)"))

    CIKTI.mkdir(parents=True, exist_ok=True)
    (CIKTI / "olcum_20260901.json").write_text(json.dumps({
        "_on_kayit": "results/hb_sekil/ON_KAYIT.md",
        "esik_turetim": {"dilim": DILIM, "pay": PAY, "q": q, "esik": esik},
        "P1": {"tutulan": tutulan, "n": p1_n, "oran": p1,
               "gecti": p1_gecti, "kayip": p1_kayip,
               "_semantik": "KARE DUZEYI: olcek+sekil birlikte, uretim gibi"},
        "N1": {"tespit": len(oto_tespit), "gecen": len(oto_gecen),
               "oran": n1, "gecti": n1_gecti,
               "gecen_kareler": [k["kare"] for k in oto_gecen]},
        "N2": {"tespit": len(kir_tespit), "gecen": len(kir_gecen),
               "gecen_kareler": [k["kare"] for k in kir_gecen]},
        "verdikt": verdikt,
        "pozitif": poz, "otopark": oto, "kirsal": kir,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"json -> {CIKTI / 'olcum_20260901.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
