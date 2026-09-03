"""FDR/ACIK_KALEMLER_HAM.md üreteci — bölümlerden ham açık kalem çıkarımı.

NEDEN (D-411): rapor "her sayı artefakttan gelir" diyor; açık kalem listesi de
bir sayıdır ("188 satır"). Elle tutulan bir liste bölümler değiştikçe **sessizce
bayatlar** ve rapor kendi kuralını ihlal eder. Bu betik listeyi `FDR/BOLUM_*.md`
dosyalarından **yeniden üretir**, böylece sayı ölçüm olur.

Ne aranır: `BEYAN GEREKLİ` ya da `ÖLÇÜLEMEDİ` geçen her satır. Bu iki etiketin
sözleşmesi Bölüm 1 §-kurallarındadır:
  BEYAN GEREKLİ  → insan girdisi bekler (isim, fiyat, tartı)
  ÖLÇÜLEMEDİ     → ölçüm bekler; "geçti" sayılmaz

Kullanım:
    python -B scripts/fdr_acik_kalem_cikar.py            # yazar
    python -B scripts/fdr_acik_kalem_cikar.py --dogrula  # yazmaz, farkı söyler
                                                          # (fark varsa çıkış 3)
"""

import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
HEDEF = FDR / "ACIK_KALEMLER_HAM.md"
ETIKETLER = ("BEYAN GEREKLİ", "ÖLÇÜLEMEDİ")

BASLIK = """# FDR — AÇIK KALEMLER (ham çıkarım)

> `FDR/BOLUM_*.md` içinde **BEYAN GEREKLİ** ya da **ÖLÇÜLEMEDİ** geçen her
> satır. Bu dosya ELLE yazılmaz; `scripts/fdr_acik_kalem_cikar.py` ile
> çıkarılır ve bölümler değiştikçe yeniden üretilir.
> Derlenmiş hâli: `FDR/ACIK_KALEMLER.md`.
"""


def uret():
    """Bölümleri tarar, ham markdown metnini ve toplam kalem sayısını döner."""
    parcalar, toplam = [BASLIK], 0
    for bolum in sorted(FDR.glob("BOLUM_*.md")):
        vurgular = []
        for i, satir in enumerate(
                bolum.read_text(encoding="utf-8").splitlines(), 1):
            if any(e in satir for e in ETIKETLER):
                # satır başındaki markdown süsü atılır, içerik korunur
                temiz = satir.strip().lstrip("|*-># ").strip()
                vurgular.append(f"- `:{i}` {temiz}")
        if not vurgular:
            continue
        parcalar.append(f"\n## {bolum.name}  ({len(vurgular)} satır)\n")
        parcalar.extend(x + "\n" for x in vurgular)
        toplam += len(vurgular)
    parcalar.append(f"\n---\n\n**TOPLAM: {toplam} açık kalem satırı** "
                    f"({len(ETIKETLER)} etiket: "
                    + ", ".join(ETIKETLER) + ").\n")
    return "".join(parcalar), toplam


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dogrula", action="store_true",
                    help="yazma; dosya güncel değilse çıkış 3")
    a = ap.parse_args(argv)

    metin, toplam = uret()
    if a.dogrula:
        mevcut = HEDEF.read_text(encoding="utf-8") if HEDEF.is_file() else ""
        if mevcut == metin:
            print(f"GUNCEL — {toplam} açık kalem satırı")
            return 0
        print(f"BAYAT — yeniden üretilmeli ({toplam} satır çıkarıldı)")
        return 3
    HEDEF.write_text(metin, encoding="utf-8", newline="")
    print(f"YAZILDI {HEDEF.relative_to(KOK)} — {toplam} açık kalem satırı")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
