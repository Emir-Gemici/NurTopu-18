#!/usr/bin/env python3
"""Jetson Nano 4GB icin Python 3.8 / aarch64 tekerleklerini PC'de CEVRIMDISI indirir.

NEDEN (SAHA_HAZIRLIK_PLANI_20260903.md §1.3 "Jetson Nano 4GB yigini — EN KRITIK"):
  * Nano'nun sistem Python'u 3.6; repo `ultralytics` ister (Python >= 3.8).
    Karar: Nano'da `python3.8 -m venv ~/venv38` + tekerlekler PC'de indirilip
    tasinabilir bellekle goturulur (sahada internet VARSAYILMAZ).
  * Nano = aarch64 (arm64), Ubuntu 18.04, **glibc 2.27**. Bu yuzden
    `manylinux_2_28_aarch64` tekerlekleri Nano'da ACILMAZ; yalniz
    manylinux2014 (= manylinux_2_17) ... manylinux_2_27 kabul edilir
    (`HEDEF_PLATFORMLAR`). PC x86_64 oldugu icin `pip download` platform/
    surum bayraklariyla HEDEF makine icin cozumleme yapar.
  * Wheel'i olmayan (yalniz sdist) paketler `kaynak_paketler.txt`'ye yazilir ve
    Nano'da `pip install` ile derlenir (fail-visible: sessizce atlanmaz, raporda
    gorunur). 3 Eylul gercek kosumunda bu liste BOS cikti — pymavlink 2.4.49
    dahil hepsi cp38/aarch64 wheel tasiyor; kademe yine de durur.

KULLANIM (PC, depo venv'i):
  python scripts/nano_tekerlek_indir.py --kuru        kosulacak pip komutlarini basar, INDIRMEZ
  python scripts/nano_tekerlek_indir.py               wheels/ altina indirir, rapor yazar
  python scripts/nano_tekerlek_indir.py --dest E:/wheels   dogrudan bellege

CIKIS KODLARI: 0 her paket wheel ya da kaynak olarak indi | 1 gereksinim
dosyasi yok / hatali cagri (fail-closed) | 2 en az bir paket HIC indirilemedi
ya da yanlis platformda tekerlek bulundu (fail-visible).

`wheels/` deposu repoya GIRMEZ (.gitignore). Paket listesinin TEK KAYNAGI
`jetson_paket/kod/requirements_nano.txt`; bu betik listeyi oradan okur.
Test: tests/test_faz_b_nano_kurulum.py (--kuru ciktisindaki bayraklar kilitli).
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

# ── Hedef makine kimligi — SAHA_HAZIRLIK_PLANI_20260903.md §0.2 / §1.3 ────────
# Ciplak sabit yazilmaz: JETSON_NANO_KURULUM.md ve test bu adlari okur.
HEDEF_PYTHON_SURUMU = "3.8"          # ~/venv38 (apt python3.8, bionic deposu)
HEDEF_UYGULAMA = "cp"                # CPython
HEDEF_ABI = "cp38"                   # cp38 wheel'leri; abi3/none pip tarafindan otomatik eklenir
NANO_GLIBC = "2.27"                  # Ubuntu 18.04 — manylinux_2_28 ve ustu KABUL EDILMEZ
HEDEF_PLATFORMLAR = (
    "manylinux2014_aarch64",         # = manylinux_2_17; torch/numpy/opencv bu etiketle gelir
    "manylinux_2_17_aarch64",        # yalniz PEP 600 adiyla etiketlenmis wheel'ler icin
    "manylinux_2_24_aarch64",
    "manylinux_2_26_aarch64",
    "manylinux_2_27_aarch64",        # onnxruntime aarch64 bu etiketi kullanir; glibc 2.27 = Nano
)
# Yanlis platform yakalayici (fail-visible): bir wheel'in platform etiketlerinden
# HICBIRI HEDEF_PLATFORMLAR'da (ya da "any") degilse Nano'da acilmaz; indirme
# BASARISIZ sayilir. Sikistirilmis etiket kumesi (orn.
# `manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64`) "bunlardan
# HERHANGI biri" demektir — gercek indirmede pymavlink/PyYAML/psutil boyle geldi;
# icinde 2_28 gecen boyle bir wheel YANLIS DEGILDIR. Yorumlayici etiketi de
# denetlenir: cp39+ / py39+ wheel'i venv38'de acilmaz. Mantik: `wheel_uyumlu_mu`.
HEDEF_PYTHON_KUCUK = int(HEDEF_PYTHON_SURUMU.split(".")[1])   # 8

GEREKSINIM_VARSAYILAN = KOK / "jetson_paket" / "kod" / "requirements_nano.txt"
WHEELS_VARSAYILAN = KOK / "wheels"
KAYNAK_LISTESI_ADI = "kaynak_paketler.txt"
RAPOR_ADI = "INDIRME_RAPORU.txt"

# Durum etiketleri (rapor + test bunlari okur)
DURUM_WHEEL = "WHEEL"                # wheel + bagimliliklari indi
DURUM_WHEEL_BAGIMSIZ = "WHEEL_BAGIMSIZ"   # paketin wheel'i var ama bir bagimliligi wheel'siz; bagimliliklar listede AYRICA olmali
DURUM_KAYNAK = "KAYNAK"              # sdist indi; Nano'da derlenir
DURUM_BASARISIZ = "BASARISIZ"        # hicbir sekilde indirilemedi

CIKIS_TAMAM = 0
CIKIS_HATALI_CAGRI = 1
CIKIS_EKSIK = 2


def gereksinimleri_oku(yol: Path):
    """requirements satirlarini (yorum ve bos satirlar haric) sirayla dondurur."""
    satirlar = []
    for ham in yol.read_text(encoding="utf-8").splitlines():
        satir = ham.split("#", 1)[0].strip()
        if satir:
            satirlar.append(satir)
    return satirlar


def paket_adi(spec: str) -> str:
    """'opencv-python-headless>=4.8' -> 'opencv-python-headless' (PEP 503 normalize)."""
    ad = re.split(r"[<>=!~\[; ]", spec, maxsplit=1)[0].strip()
    return re.sub(r"[-_.]+", "-", ad).lower()


def platform_bayraklari():
    bayraklar = []
    for p in HEDEF_PLATFORMLAR:
        bayraklar += ["--platform", p]
    return bayraklar


def tekerlek_komutu(python: str, spec: str, dest: Path, bagimliliksiz: bool = False):
    """Hedef makine icin YALNIZ wheel indiren pip komutu (PC'de derleme YOK)."""
    komut = [python, "-m", "pip", "download",
             "--only-binary=:all:",
             "--python-version", HEDEF_PYTHON_SURUMU,
             "--implementation", HEDEF_UYGULAMA,
             "--abi", HEDEF_ABI,
             *platform_bayraklari(),
             "--dest", str(dest)]
    if bagimliliksiz:
        komut.append("--no-deps")
    komut.append(spec)
    return komut


def kaynak_komutu(python: str, spec: str, dest: Path):
    """Wheel'i olmayan paketin kaynak dagitimini (sdist) indirir; Nano'da derlenir."""
    return [python, "-m", "pip", "download", "--no-deps", "--no-binary=:all:",
            "--dest", str(dest), spec]


def komut_metni(komut) -> str:
    return " ".join(komut)


def _dosyalar(dest: Path):
    return {p.name for p in dest.iterdir() if p.is_file()} if dest.is_dir() else set()


def _kos(komut, zaman_asimi_s: int):
    try:
        sonuc = subprocess.run(komut, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=zaman_asimi_s)
    except subprocess.TimeoutExpired:
        return 124, f"zaman asimi ({zaman_asimi_s} s)"
    cikti = (sonuc.stdout or "") + (sonuc.stderr or "")
    return sonuc.returncode, cikti


def _son_satirlar(cikti: str, n: int = 4) -> str:
    satirlar = [s.strip() for s in cikti.splitlines() if s.strip()]
    return " | ".join(satirlar[-n:])


def paketi_indir(python: str, spec: str, dest: Path, zaman_asimi_s: int):
    """Uc kademe: wheel+bagimlilik -> wheel (bagimsiz) -> kaynak. Sonuc sozlugu."""
    ad = paket_adi(spec)
    onceki = _dosyalar(dest)
    kademeler = (
        (DURUM_WHEEL, tekerlek_komutu(python, spec, dest)),
        (DURUM_WHEEL_BAGIMSIZ, tekerlek_komutu(python, spec, dest, bagimliliksiz=True)),
        (DURUM_KAYNAK, kaynak_komutu(python, spec, dest)),
    )
    hatalar = []
    for durum, komut in kademeler:
        kod, cikti = _kos(komut, zaman_asimi_s)
        if kod == 0:
            yeni = sorted(_dosyalar(dest) - onceki)
            return {"paket": ad, "spec": spec, "durum": durum, "yeni_dosyalar": yeni,
                    "komut": komut_metni(komut), "not": ""}
        hatalar.append(f"{durum}: pip cikis {kod}: {_son_satirlar(cikti)}")
    return {"paket": ad, "spec": spec, "durum": DURUM_BASARISIZ, "yeni_dosyalar": [],
            "komut": komut_metni(kademeler[0][1]), "not": " || ".join(hatalar)}


def _yorumlayici_uyumlu(etiket: str) -> bool:
    """py3 / py2 / py3X (X<=8) / cp3X (X<=8) kabul; cp39+, py39+ RED."""
    if etiket in ("py2", "py3"):
        return True
    m = re.fullmatch(r"(cp|py)3(\d+)", etiket)
    return bool(m) and int(m.group(2)) <= HEDEF_PYTHON_KUCUK


def wheel_uyumlu_mu(dosya_adi: str) -> bool:
    """Wheel adi (PEP 427) Nano hedefiyle uyumlu mu: yorumlayici VE platform."""
    govde = dosya_adi[:-4] if dosya_adi.endswith(".whl") else dosya_adi
    parcalar = govde.split("-")
    if len(parcalar) < 5:
        return False
    py_etiketleri, platform_etiketleri = parcalar[-3].split("."), parcalar[-1].split(".")
    if not any(_yorumlayici_uyumlu(e) for e in py_etiketleri):
        return False
    return any(e == "any" or e in HEDEF_PLATFORMLAR for e in platform_etiketleri)


def yanlis_platform_dosyalari(dest: Path):
    """wheels/ icinde Nano'da ACILMAYACAK wheel'ler (fail-visible). sdist'ler denetlenmez."""
    return [ad for ad in sorted(_dosyalar(dest))
            if ad.endswith(".whl") and not wheel_uyumlu_mu(ad)]


def rapor_yaz(dest: Path, sonuclar, kotu_dosyalar, python: str, gereksinim: Path):
    dest.mkdir(parents=True, exist_ok=True)
    # Gereksinim listesi bellege wheel'lerle BIRLIKTE gider: Nano'da
    # `pip install --no-index --find-links . -r requirements_nano.txt` tek komut.
    shutil.copy2(gereksinim, dest / gereksinim.name)
    kaynak = [s["spec"] for s in sonuclar if s["durum"] == DURUM_KAYNAK]
    (dest / KAYNAK_LISTESI_ADI).write_text(
        "# Nano'da KAYNAKTAN derlenecek paketler (wheel'i yok) — "
        "`pip install --no-index --find-links . <paket>` derler\n"
        + "".join(f"{s}\n" for s in kaynak), encoding="utf-8")
    satirlar = [
        "# JETSON NANO 4GB — tekerlek indirme raporu (scripts/nano_tekerlek_indir.py)",
        f"# hedef: python {HEDEF_PYTHON_SURUMU} / {HEDEF_UYGULAMA} {HEDEF_ABI} / "
        f"{', '.join(HEDEF_PLATFORMLAR)} (glibc <= {NANO_GLIBC})",
        f"# gereksinim: {gereksinim}",
        f"# pip: {python}",
        "",
    ]
    for s in sonuclar:
        satirlar.append(f"[{s['durum']:<15}] {s['paket']:<26} {len(s['yeni_dosyalar']):>3} yeni dosya"
                        + (f"  ({s['not']})" if s["not"] else ""))
        for d in s["yeni_dosyalar"]:
            satirlar.append(f"    + {d}")
    if kotu_dosyalar:
        satirlar.append("")
        satirlar.append("[YANLIS_PLATFORM] Nano'da acilmayacak dosyalar — SILINMELI:")
        satirlar += [f"    - {d}" for d in kotu_dosyalar]
    (dest / RAPOR_ADI).write_text("\n".join(satirlar) + "\n", encoding="utf-8")


def _ayristirici():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--kuru", action="store_true",
                   help="Kosulacak pip komutlarini basar; HICBIR SEY indirmez, dizin acmaz")
    p.add_argument("--gereksinim", type=Path, default=GEREKSINIM_VARSAYILAN,
                   help=f"paket listesi (varsayilan {GEREKSINIM_VARSAYILAN.relative_to(KOK)})")
    p.add_argument("--dest", type=Path, default=WHEELS_VARSAYILAN,
                   help="tekerleklerin yazilacagi dizin (varsayilan wheels/ — repoya girmez)")
    p.add_argument("--python", default=sys.executable,
                   help="pip'i kosacak yorumlayici (varsayilan: bu betigi kosan)")
    p.add_argument("--zaman-asimi", type=int, default=1800,
                   help="paket basina pip zaman asimi (s)")
    return p


def main(argv=None) -> int:
    args = _ayristirici().parse_args(argv)
    if not args.gereksinim.is_file():
        print(f"HATA: gereksinim dosyasi yok: {args.gereksinim}", file=sys.stderr)
        return CIKIS_HATALI_CAGRI
    specler = gereksinimleri_oku(args.gereksinim)
    if not specler:
        print(f"HATA: gereksinim dosyasi bos: {args.gereksinim}", file=sys.stderr)
        return CIKIS_HATALI_CAGRI

    print(f"hedef: python {HEDEF_PYTHON_SURUMU} {HEDEF_UYGULAMA}/{HEDEF_ABI} | "
          f"platform {', '.join(HEDEF_PLATFORMLAR)} | glibc <= {NANO_GLIBC}")
    print(f"gereksinim: {args.gereksinim} ({len(specler)} paket) | dest: {args.dest}")

    if args.kuru:
        for spec in specler:
            print("KURU: " + komut_metni(tekerlek_komutu(args.python, spec, args.dest)))
        print("KURU: wheel bulunamazsa sirayla -> "
              + komut_metni(tekerlek_komutu(args.python, "<paket>", args.dest, bagimliliksiz=True))
              + "  ->  " + komut_metni(kaynak_komutu(args.python, "<paket>", args.dest)))
        return CIKIS_TAMAM

    args.dest.mkdir(parents=True, exist_ok=True)
    sonuclar = []
    for spec in specler:
        print(f"... {spec}", flush=True)
        s = paketi_indir(args.python, spec, args.dest, args.zaman_asimi)
        sonuclar.append(s)
        ek = f"  ({s['not']})" if s["not"] else ""
        print(f"[{s['durum']:<15}] {s['paket']:<26} {len(s['yeni_dosyalar']):>3} yeni dosya{ek}",
              flush=True)

    kotu = yanlis_platform_dosyalari(args.dest)
    rapor_yaz(args.dest, sonuclar, kotu, args.python, args.gereksinim)

    sayim = {d: sum(1 for s in sonuclar if s["durum"] == d)
             for d in (DURUM_WHEEL, DURUM_WHEEL_BAGIMSIZ, DURUM_KAYNAK, DURUM_BASARISIZ)}
    toplam_dosya = len(_dosyalar(args.dest))
    print(f"OZET: {sayim} | {toplam_dosya} dosya | rapor {args.dest / RAPOR_ADI} | "
          f"kaynak listesi {args.dest / KAYNAK_LISTESI_ADI}")
    if kotu:
        print("YANLIS PLATFORM (Nano'da acilmaz): " + ", ".join(kotu), file=sys.stderr)
    if sayim[DURUM_BASARISIZ] or kotu:
        return CIKIS_EKSIK
    return CIKIS_TAMAM


if __name__ == "__main__":
    raise SystemExit(main())
