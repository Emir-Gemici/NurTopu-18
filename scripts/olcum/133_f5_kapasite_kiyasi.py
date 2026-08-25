"""F5 OLCUM TURU — sinif 0'in EK MALIYETI, eslestirmeli kiyas.

On kayit: `results/dji_20260822/f5_on_kayit.md` (etiketleme baslamadan yazildi)

SORU: F4'te olculen 708 sn/kare YALNIZ sinif 1'in maliyetiydi (amelelere
"sinif 0 cizme" denmisti). Uc durumlu bicimde amele artik UC karar veriyor:
sinif 1 · sinif 0 · etiketsiz. Bunun ek maliyeti NEDIR?

YONTEM: AYNI 12 kare yeniden etiketlendi -> kare zorlugu DEGISKEN OLMAKTAN
CIKAR. Fark yalniz sartnameden gelir.

BANTLAR (on kayit §3, sonuca gore DEGISTIRILMEZ):
    medyan oran <= 1,30  -> sinif 0 ucuz, 14 Eylul yaklasik gecerli
    1,30 - 2,00          -> anlamli ek maliyet, tarih YENIDEN HESAPLANIR
    > 2,00               -> is belirgin buyudu, F5 olcegi YENIDEN TARTISILIR

⚠ ORTALAMA DEGIL MEDYAN: F4'te tek kare 3152 sn ile 26,9 kat yayilim
  uretmisti; ortalama o tek kareye esir olur.
⚠ GECERSIZLIK KAPISI (on kayit §4): sinif 0'i FIILEN cizmemis bir amele
  dusuk oran uretir ve yaniltir. Sinif 0 orani ~0 olan kare ORTALAMAYA
  KATILMAZ, ayrica raporlanir.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
TABAN = KOK / "results" / "dji_20260822"
SINIF0_ASGARI = 0.01     # sinif 0 orani bunun altindaysa "cizilmemis" sayilir


def rapor_oku(dizin: Path) -> dict:
    """-> {dosya: kayit}"""
    out = {}
    for grup in "ABC":
        p = dizin / grup / "rapor.json"
        if not p.is_file():
            continue
        d = json.load(open(p, encoding="utf-8"))
        kayit = d.get("kareler") or []
        if isinstance(kayit, dict):
            kayit = list(kayit.values())
        for k in kayit:
            if isinstance(k, dict) and k.get("dosya"):
                out[k["dosya"]] = {**k, "_grup": grup}
    return out


def medyan(d):
    d = sorted(d)
    n = len(d)
    if not n:
        return None
    return d[n // 2] if n % 2 else (d[n // 2 - 1] + d[n // 2]) / 2


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    f4 = rapor_oku(TABAN / "f4")
    f5 = rapor_oku(TABAN / "f5")
    print(f"F4 kayit {len(f4)} · F5 kayit {len(f5)}")

    oranlar, disarida, satirlar = [], [], []
    for dosya, k5 in sorted(f5.items()):
        k4 = f4.get(dosya)
        s5 = k5.get("saniye")
        s4 = k4.get("saniye") if k4 else None
        s0 = k5.get("sinif0_oran")
        s1 = k5.get("sinif1_oran")
        se = k5.get("etiketsiz_oran")
        neden = None
        if k4 is None:
            neden = "F4'te YOK"
        elif not isinstance(s4, (int, float)) or not isinstance(s5, (int, float)):
            neden = "sure OLCULEMEDI"
        elif isinstance(s0, (int, float)) and s0 < SINIF0_ASGARI:
            neden = f"sinif0 orani {s0:.4f} < {SINIF0_ASGARI} — CIZILMEMIS sayildi"
        oran = None
        if neden is None:
            oran = s5 / s4
            oranlar.append(oran)
        else:
            disarida.append((dosya, neden))
        satirlar.append({"dosya": dosya, "f4_sn": s4, "f5_sn": s5, "oran": oran,
                         "sinif0": s0, "sinif1": s1, "etiketsiz": se,
                         "disarida": neden})

    print(f"\n{'kare':46s} {'F4 sn':>7s} {'F5 sn':>7s} {'oran':>6s} "
          f"{'sinif0':>7s} {'sinif1':>7s} {'etiketsiz':>9s}")
    for s in satirlar:
        def f(v, k=".4f"):
            return format(v, k) if isinstance(v, (int, float)) else "-"
        print(f"{s['dosya'][-46:]:46s} {f(s['f4_sn'],'.0f'):>7s} {f(s['f5_sn'],'.0f'):>7s} "
              f"{f(s['oran'],'.2f'):>6s} {f(s['sinif0']):>7s} {f(s['sinif1']):>7s} "
              f"{f(s['etiketsiz']):>9s}" + (f"   ⚠ {s['disarida']}" if s['disarida'] else ""))

    med = medyan(oranlar)
    print(f"\nEslestirilen kare: {len(oranlar)} · disarida {len(disarida)}")
    for d, n in disarida:
        print(f"  ⚠ {d[-46:]}: {n}")
    if med is None:
        print("\n🔴 MEDYAN OLCULEMEDI — hukum YOK (D-180: olculemeyen deger degildir)")
        karar = "OLCULEMEDI"
    else:
        print(f"MEDYAN ORAN: {med:.2f}  (ortalama {sum(oranlar)/len(oranlar):.2f} — "
              f"kullanilMAZ, on kayit §3)")
        if med <= 1.30:
            karar = "SINIF 0 UCUZ -> 14 Eylul yaklasik gecerli"
        elif med <= 2.00:
            karar = "ANLAMLI EK MALIYET -> tarih YENIDEN HESAPLANIR"
        else:
            karar = "IS BELIRGIN BUYUDU -> F5 olcegi YENIDEN TARTISILIR"
    print(f"\nKARAR (on kayit bantlari, mekanik): {karar}")

    cikti = TABAN / "f5_kapasite_kiyasi.json"
    json.dump({"_ne": "F5 olcum turu — sinif 0'in ek maliyeti, eslestirmeli",
               "_on_kayit": "results/dji_20260822/f5_on_kayit.md",
               "_bantlar": {"ucuz": 1.30, "anlamli": 2.00},
               "medyan_oran": med, "karar": karar,
               "eslestirilen": len(oranlar), "disarida": disarida,
               "kareler": satirlar},
              open(cikti, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"yazildi: {cikti}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
