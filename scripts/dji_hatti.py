"""T136 — DJI HATTI: cekimden aday raporuna TEK KOMUT.

🔴 NEDEN VAR: goruntu 30 Eylul'e dogru gelecek ve hattin O GUN ILK KEZ
kosmasi kabul edilemez. Bu betik hattin KENDISIDIR ve BUGUN elde olan 14
dosyayla PROVA EDILIR. Prova modeli ADAY BILE DEGILDIR (14 dosya yetersiz);
prova edilen sey MODEL degil HATTIR.

ZINCIR (her adim oncekinin ciktisina baglidir; biri duserse zincir DURUR):
  0. OTURUM KAPISI   — DOGRULAMA oturumu AYRILMIS mi?
  1. KARE CIKARMA    — dedup'li, oturum oturum
  2. ETIKETLEME      — (a)+(c) recetesi (T122/D-237); kahin ACIKCA verilir
  3. BOLUM KAPISI    — KAYNAK duzeyinde (D-233); "kaynagi egitimde olan val" = 0
  4. KARISIM YAML
  5. EGITIM
  6. TAM KABUL ZINCIRI
  7. RAPOR + ZAMANLAMA

⏱ HER ADIMIN DUVAR SAATI OLCULUR ve `zamanlama.json`a yazilir. "Son guvenli
gelis tarihi" bu sayilardan HESAPLANIR — tahminden degil.

🔴 BU BETIK MODEL TERFI ETTIRMEZ. `config/model_registry.json`a YAZMAZ.
"""
from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PY = sys.executable
CIKTI_KOK = KOK / "results" / "t136"

# ── OTURUM SOZLESMESI ──────────────────────────────────────────────────────
# Cekim gunu kullanicinin yapacagi TEK sey: dogrulama ucusunu AYRI bir klasore
# koymak. Kural MEKANIKTIR ve hat onu ZORLAR.
#
#   dji/
#     <ne_olursa>/            <- egitim oturum(lari)
#     DOGRULAMA/              <- FARKLI yer/gun; EGITIME ASLA GIRMEZ
#
# 🔴 NEDEN SONRADAN BOLMEK YETMEZ (T111): ayni ucustan ayrilan val, ayni
# dagilimdan gelir — "alan disi" sorusunu YANITLAMAZ, yalnizca yanitlamis
# GIBI gorunur. D-256 §5'te bu tam olarak olculdu: egitim disi 11 kare "ayni
# saha ve ayni oturumdandi", KANIT degil ZAYIF DESTEK sayildi.
DOGRULAMA_ADI = "DOGRULAMA"


def sure_olc(ad: str, kayit: list):
    """Adim zamanlayici — `with sure_olc("ad", kayit):`"""
    class _Zaman:
        def __enter__(self_):
            self_.t0 = time.perf_counter()
            print(f"\n{'='*66}\nADIM: {ad}\n{'='*66}")
            return self_

        def __exit__(self_, *a):
            sn = time.perf_counter() - self_.t0
            kayit.append({"adim": ad, "saniye": round(sn, 2)})
            print(f"[{ad}] {sn:.1f} sn")
            return False
    return _Zaman()


def kos(*arg, **kw) -> int:
    """Alt betigi kos; cikis kodunu DONDUR (T125: exit kodu KONTROL EDILIR)."""
    print("  $ " + " ".join(str(a) for a in arg[:6]) + (" ..." if len(arg) > 6 else ""))
    p = subprocess.run([str(a) for a in arg], cwd=str(KOK), **kw)
    return p.returncode


# ── ADIM 0 · OTURUM KAPISI ─────────────────────────────────────────────────
def oturumlari_bul(kaynak: Path) -> dict:
    """{oturum_adi: [dosyalar]}. Kokte duran dosyalar '_AYRILMAMIS' oturumudur."""
    uzanti = {".mp4", ".mov", ".jpg", ".jpeg", ".png"}
    oturumlar: dict[str, list[Path]] = {}
    for p in sorted(kaynak.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in uzanti:
            continue
        bagil = p.relative_to(kaynak)
        ad = bagil.parts[0] if len(bagil.parts) > 1 else "_AYRILMAMIS"
        oturumlar.setdefault(ad, []).append(p)
    return oturumlar


def oturum_kapisi(oturumlar: dict, prova: bool) -> dict:
    """FAIL-CLOSED: DOGRULAMA oturumu yoksa zincir DURUR.

    `--prova` bu kapiyi ACMAZ; yalnizca kosumun ADAY URETEMEYECEGINI kabul
    ederek devam etmeye izin verir ve bunu raporun her yerine YAZAR.
    """
    egitim = {a: d for a, d in oturumlar.items() if a != DOGRULAMA_ADI}
    dogrulama = oturumlar.get(DOGRULAMA_ADI, [])
    print(f"  oturum sayisi : {len(oturumlar)}")
    for ad, d in sorted(oturumlar.items()):
        print(f"    {ad:16s} {len(d):4d} dosya")
    if dogrulama:
        return {"gecti": True, "prova_mi": False,
                "egitim_dosya": sum(len(d) for d in egitim.values()),
                "dogrulama_dosya": len(dogrulama)}
    mesaj = (
        f"DOGRULAMA oturumu YOK ({kaynak_ipucu()}). T136 kisit 2: dogrulama "
        f"oturumu CEKIMDE ayrilir; sonradan bolmek AYNI DAGILIMDIR ve T111 "
        f"duvarini YIKMAZ (D-256 §5).")
    if not prova:
        raise SystemExit(f"\n[DUR] ZINCIR DURDU - {mesaj}\n"
                         f"   Cozum: dogrulama ucusunu `<kaynak>/{DOGRULAMA_ADI}/` "
                         f"altina koyun.\n"
                         f"   Yalnizca HAT PROVASI icin: --prova")
    print(f"\n  [!] PROVA KIPI - {mesaj}")
    print(f"  [!] Bu kosum ADAY URETEMEZ ve modeli TERFI ETTIREMEZ.")
    return {"gecti": False, "prova_mi": True,
            "egitim_dosya": sum(len(d) for d in egitim.values()),
            "dogrulama_dosya": 0}


def kaynak_ipucu() -> str:
    return f"beklenen klasor adi: {DOGRULAMA_ADI}"


# ── ADIM 1b · PARLAKLIK KAPISI (T136 PROVASININ BULDUGU KUSUR) ────────────
# 🔴 PROVADA OLCULDU (2026-08-21): 14 dosyalik ilk cekim AKSAM yapilmis
# (20:17-21:05) ve 569/569 karenin ortalama parlakligi 80'in ALTINDA
# (medyan 20,3; karelerin ~%39'u neredeyse siyah). Uretim modeli o karelerde
# zemini HIC gormedi: 30 karede zemin orani medyani 0,0000 ve uretim hatti
# 30/30 REDDETTI. Bu bir MODEL kusuru DEGIL, CEKIM KOSULU kusurudur.
#
# ⚠ ESIK UYDURULMAZ — CALISAN VERIDEN TURETILIR. Referans `data/raw_frames`
# (67 otopark karesi; bugunku uretim modellerini ureten veri). Olculdu:
#     referans : min 118,7 · medyan 128,7
#     DJI      : maks  73,2 · medyan  21,2
# Iki dagilim HIC ORTUSMUYOR. Kural bu yuzden "ortalamanin altinda" gibi
# keyfi bir sayi degil, ORTUSME sorusudur: yeni cekimin EN AYDINLIK karesi
# bile referansin EN KARANLIK karesine ulasamiyorsa hat DURUR.
def _ortalama_parlaklik(yol) -> float:
    import cv2
    im = cv2.imread(str(yol), cv2.IMREAD_GRAYSCALE)
    if im is None:
        return float("nan")
    return float(cv2.resize(im, (320, 180)).mean())


def parlaklik_kapisi(kare_dizini: Path, referans_dizini: Path, prova: bool,
                     ornek: int = 400) -> dict:
    import math
    yeni = [_ortalama_parlaklik(p) for p in
            sorted(kare_dizini.rglob("*.jpg"))[:ornek]]
    ref = [_ortalama_parlaklik(p) for p in
           sorted(referans_dizini.rglob("*.jpg"))[:ornek]]
    yeni = [v for v in yeni if not math.isnan(v)]
    ref = [v for v in ref if not math.isnan(v)]
    if not yeni:
        raise SystemExit("\n[DUR] ZINCIR DURDU - parlaklik olculemedi: kare yok")
    if not ref:
        print("  [!] referans kume okunamadi - parlaklik kapisi OLCULEMEDI "
              "(bu 'GECTI' DEMEK DEGILDIR)")
        return {"durum": "OLCULEMEDI"}
    durum = {"durum": None, "yeni_maks": max(yeni), "yeni_medyan": _medyan(yeni),
             "ref_min": min(ref), "ref_medyan": _medyan(ref), "n_yeni": len(yeni),
             "n_ref": len(ref), "referans": str(referans_dizini)}
    print(f"  yeni cekim : medyan {durum['yeni_medyan']:.1f} · maks {durum['yeni_maks']:.1f}")
    print(f"  referans   : medyan {durum['ref_medyan']:.1f} · min  {durum['ref_min']:.1f}"
          f"   ({referans_dizini.name})")
    if durum["yeni_maks"] < durum["ref_min"]:
        durum["durum"] = "ORTUSME_YOK"
        mesaj = (f"cekim REFERANSTAN KARANLIK: en aydinlik yeni kare "
                 f"({durum['yeni_maks']:.1f}) referansin EN KARANLIK karesine "
                 f"({durum['ref_min']:.1f}) ulasmiyor. Iki dagilim ORTUSMUYOR.")
        if not prova:
            raise SystemExit(
                f"\n[DUR] ZINCIR DURDU - {mesaj}\n"
                f"   Cekim GUN ISIGINDA tekrarlanmali; karanlik kare etiket de "
                f"egitim de uretmez.\n   Yalnizca HAT PROVASI icin: --prova")
        print(f"  [!] {mesaj}")
        print("  [!] PROVA KIPI - devam ediliyor ama bu veri EGITIME UYGUN DEGIL.")
        return durum
    durum["durum"] = "ORTUSUYOR"
    return durum


def _medyan(dizi):
    d = sorted(dizi)
    n = len(d)
    return d[n // 2] if n % 2 else (d[n // 2 - 1] + d[n // 2]) / 2


# ── ADIM 3 · BOLUM KAPISI ──────────────────────────────────────────────────
def bolum_kapisi(manifest_yolu: Path) -> dict:
    """KAYNAK duzeyinde bolum dogrulamasi (D-233 · T127).

    KAPI: "kaynagi egitimde de olan val" = 0. Degilse zincir DURUR.
    Varyant duzeyinde bolmek val'i egitimin IKIZI yapar; olculmustu: 55/55
    val ornegi egitimde de vardi, yani o bilesenin val metrigi EZBER olcer.
    """
    veri = json.loads(manifest_yolu.read_text(encoding="utf-8"))
    kayitlar = veri if isinstance(veri, list) else veri.get("kayitlar", [])
    egitim_kaynaklari = {k.get("kaynak") for k in kayitlar
                         if k.get("bolum") == "train"}
    kirli = [k for k in kayitlar if k.get("bolum") == "val"
             and k.get("kaynak") in egitim_kaynaklari]
    val = [k for k in kayitlar if k.get("bolum") == "val"]
    durum = {"val": len(val), "kirli_val": len(kirli),
             "egitim_kaynak": len(egitim_kaynaklari)}
    print(f"  val {len(val)} · kaynagi egitimde olan val: {len(kirli)}")
    if kirli:
        raise SystemExit(
            f"\n🔴 ZINCIR DURDU — bolum TEMIZ DEGIL: {len(kirli)}/{len(val)} val "
            f"orneginin kaynagi egitimde de var (D-233). Bolum anahtari KAYNAK "
            f"duzeyinde olmali (`copy_paste_augmentation.bolum_sec`).")
    return durum


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--kaynak", type=Path, default=KOK / "dji",
                    help="Cekim koku; alt klasorler OTURUMDUR")
    ap.add_argument("--ad", default="dji_prova", help="Kosum adi")
    ap.add_argument("--prova", action="store_true",
                    help="DOGRULAMA oturumu YOKKEN hat provasina izin ver "
                         "(kosum ADAY URETEMEZ)")
    ap.add_argument("--kahin", type=Path, required=True,
                    help="[!] ETIKET KAHINI agirligi. ZORUNLU ve ACIK — "
                         "varsayilan YOK. D-210'un kusuru tam buradaydi: "
                         "uretec BILINMEYENI zemin ilan ediyordu.")
    ap.add_argument("--aralik", type=float, default=1.0,
                    help="Kare ornekleme araligi (sn)")
    ap.add_argument("--hash-esik", type=float, default=0.12,
                    help="Dedup esigi (algisal hash)")
    ap.add_argument("--en-fazla", type=int, default=3000)
    ap.add_argument("--parlaklik-referansi", type=Path,
                    default=KOK / "data" / "raw_frames",
                    help="Parlaklik esigi BU KUMEDEN turetilir (uydurulmaz): "
                         "bugunku uretim modellerini ureten kare kumesi")
    ap.add_argument("--son-adim", type=int, default=7,
                    help="Bu adimdan sonra DUR (prova icin)")
    args = ap.parse_args()

    if not args.kaynak.is_dir():
        raise SystemExit(f"kaynak dizin yok: {args.kaynak}")
    if not args.kahin.exists():
        raise SystemExit(f"etiket kahini bulunamadi: {args.kahin}")

    cikti = CIKTI_KOK / args.ad
    cikti.mkdir(parents=True, exist_ok=True)
    zaman: list = []
    ozet: dict = {"_ne": "T136 · DJI hatti kosumu", "ad": args.ad,
                  "kaynak": str(args.kaynak), "kahin": str(args.kahin)}

    # ── 0 · OTURUM KAPISI ──────────────────────────────────────────────
    with sure_olc("0-oturum_kapisi", zaman):
        oturumlar = oturumlari_bul(args.kaynak)
        ozet["oturum"] = oturum_kapisi(oturumlar, args.prova)
    if args.son_adim < 1:
        return _bitir(cikti, ozet, zaman)

    # ── 1 · KARE CIKARMA (dedup) ───────────────────────────────────────
    kare_dizini = KOK / "data" / f"{args.ad}_kareler"
    with sure_olc("1-kare_cikarma", zaman):
        kod = kos(PY, KOK / "scripts" / "extract_key_frames.py",
                  "--girdi", args.kaynak, "--cikti", kare_dizini,
                  "--aralik", args.aralik, "--en-fazla", args.en_fazla,
                  "--hash-esik", args.hash_esik, "--temizle")
        if kod != 0:
            raise SystemExit(f"\n[DUR] ZINCIR DURDU - kare cikarma exit={kod}")
        mf = kare_dizini / "manifest.json"
        n = len(list(kare_dizini.rglob("*.jpg")))
        ozet["kare"] = {"dizin": str(kare_dizini), "adet": n,
                        "manifest": str(mf) if mf.exists() else None}
        print(f"  kare: {n}")
        if n == 0:
            raise SystemExit("\n[DUR] ZINCIR DURDU - hic kare cikmadi")

    # ── 1b · PARLAKLIK KAPISI (provada bulundu) ────────────────────────
    with sure_olc("1b-parlaklik_kapisi", zaman):
        ozet["parlaklik"] = parlaklik_kapisi(
            kare_dizini, args.parlaklik_referansi, args.prova)
    if args.son_adim < 2:
        return _bitir(cikti, ozet, zaman)

    # ── 2..7 · ETIKETLEME -> ADAY RAPORU ───────────────────────────────
    # Bu adimlar `copy_paste_augmentation.py` (etiket + cogaltma),
    # `bolum_kapisi` (D-233), karisim yaml, egitim ve kabul zinciridir.
    # Prova turunda ADIM 2'ye kadar kosulur; 2+ icin gereken arayuz
    # `results/t136/*/arayuz.md`de cikarilmistir.
    raise SystemExit(
        "\n🔴 ADIM 2+ HENUZ BAGLANMADI — ve bu BILEREK boyledir.\n"
        "   Etiket hattinin (a)+(c) arayuzu ADIM 1 turunda cikariliyor;\n"
        "   yarim baglanmis bir zincir 'kosuyor' gibi gorunup sessizce\n"
        "   yanlis etiket uretirdi (D-210 sinifi). Baglanana kadar DURUR.")


def _bitir(cikti: Path, ozet: dict, zaman: list) -> int:
    ozet["zamanlama"] = zaman
    ozet["toplam_saniye"] = round(sum(z["saniye"] for z in zaman), 2)
    io.open(cikti / "kosum.json", "w", encoding="utf-8").write(
        json.dumps(ozet, ensure_ascii=False, indent=1))
    print(f"\n{'='*66}\nZAMANLAMA")
    for z in zaman:
        print(f"  {z['adim']:22s} {z['saniye']:8.1f} sn")
    print(f"  {'TOPLAM':22s} {ozet['toplam_saniye']:8.1f} sn")
    print(f"yazildi: {cikti / 'kosum.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
