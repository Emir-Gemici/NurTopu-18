"""SAHA BELLEĞİ HAZIRLAYICI — cumartesi götürülecek her şeyi TEK klasöre toplar.

NEDEN (SAHA_HAZIRLIK_PLANI_20260903 §1.10): 5 Eylül'de Jetson Nano kutudan
çıkacak ve **internet olmayabilir**. Kurulumun gerektirdiği her parça (paket,
tekerlekler, uçuş kontrolcüsü şablonları, basılacak kontrol listeleri) elle
toplanırsa biri unutulur ve sahada telafisi yoktur. Bu betik toplamayı
mekanikleştirir ve **eksik olanı sayar** — "hazır" demek için eksik sıfır olmalı.

Fail-closed: zorunlu bir parça yoksa çıkış **3** ve eksik listesi basılır
(`--eksige-ragmen` ile bilerek aşılır, MANIFEST'e yazılır).

Kullanım:
    <venv> scripts/bellek_hazirla.py --hedef E:/navitas_bellek
    <venv> scripts/bellek_hazirla.py --kuru          # kopyalamaz, ne yapacağını yazar

Çıktı: hedef klasör + `MANIFEST.txt` (her dosyanın sha256'sı, üretim zamanı,
git HEAD) + `EKSIKLER.txt` (varsa).
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]

# Windows konsolu cp1254'tur; kutu/ok imleri UnicodeEncodeError verir. Cikti
# metni RAPORDUR — imle takilip raporu kaybetmek kabul edilemez (fail-visible
# yerine fail-silent olurdu).
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# (kaynak, hedef_alt_klasor, zorunlu_mu, neden)
KOPYA_KURALLARI = (
    ("jetson_paket", "jetson_paket", True,
     "Jetson kurulumu: kod aynası, modeller, kılavuzlar, systemd birimleri"),
    ("config/pixhawk", "config_pixhawk", True,
     "ArduCopter parametreleri + görev planı (Mission Planner'a yüklenir)"),
    ("SAHA_HAZIRLIK_PLANI_20260903.md", "belgeler", True,
     "sıfırdan uçuşa adım listesi (basılacak)"),
    ("FAZ_B_GUN_PLANI.md", "belgeler", True,
     "cumartesi saat planı ve kapıları (basılacak)"),
    ("SAHA_RUNBOOK.md", "belgeler", True,
     "saha yordamı: açılış kartı, operatör kartı, İHA/Jetson blokları"),
    ("jetson_paket/JETSON_NANO_KURULUM.md", "belgeler", True,
     "Nano 4GB kurulumu (JetPack, Python 3.8, tekerlekler, kamera)"),
    ("jetson_paket/JETSON_BASLAT.md", "belgeler", True,
     "tek komut açılış ve systemd birimleri"),
    ("jetson_paket/GUN1_KONTROL_LISTESI.md", "belgeler", True,
     "Jetson Gün-1 kapıları (.engine, FPS, denklik)"),
    ("config/pixhawk/README.md", "belgeler", True,
     "parametre yükleme + sahada değişecek tek şeyler + TEYİT listesi"),
    ("results/faz_b_oncesi/CUMA_KONTROL_KARTI.md", "belgeler", True,
     "cuma akşamı kontrol kartı: koşulmuş kapılar, alışveriş, cumartesi ilk üç iş"),
    ("wheels", "wheels", False,
     "Nano için çevrimdışı aarch64/cp38 tekerlekler (scripts/nano_tekerlek_indir.py)"),
)

# Betiğin ÜRETEMEYECEĞİ, insanın koyması gereken parçalar (MANIFEST'e yazılır).
INSAN_PARCALARI = (
    ("JetPack 4.6.x SD imajı", "microSD'ye balenaEtcher ile yazılır; belleğe imaj "
     "dosyası KONMAZ, kart hazır gelir (JETSON_NANO_KURULUM §1)"),
    ("GPU torch wheel'i (JetPack 4.6 / Python 3.8)", "Qengineering deposundan elle "
     "indirilir; CPU torch zaten wheels/ içinde, GPU olursa FPS kapısı rahatlar"),
    ("Mission Planner kurulu dizüstü", "parametre + görev planı yükleme"),
)


def _sha256(yol: Path) -> str:
    h = hashlib.sha256()
    with open(yol, "rb") as f:
        for parca in iter(lambda: f.read(1 << 20), b""):
            h.update(parca)
    return h.hexdigest()


def _git_head() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=KOK,
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip() if r.returncode == 0 else "BILINMIYOR"
    except (OSError, subprocess.SubprocessError):
        return "BILINMIYOR"


def _dosyalari_topla(kaynak: Path):
    if kaynak.is_file():
        return [kaynak]
    return [p for p in sorted(kaynak.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts]


def hazirla(hedef: Path, *, kuru: bool, eksige_ragmen: bool) -> int:
    eksikler, kopyalanan, toplam_bayt = [], [], 0
    satirlar = []
    for gore, alt, zorunlu, neden in KOPYA_KURALLARI:
        kaynak = KOK / gore
        if not kaynak.exists():
            (eksikler if zorunlu else satirlar).append(
                f"{'EKSIK (ZORUNLU)' if zorunlu else 'yok (istege bagli)'}: {gore} — {neden}")
            continue
        dosyalar = _dosyalari_topla(kaynak)
        boyut = sum(p.stat().st_size for p in dosyalar)
        toplam_bayt += boyut
        satirlar.append(f"[{len(dosyalar):4d} dosya · {boyut/1e6:8.1f} MB] {gore} -> {alt}/")
        if kuru:
            continue
        for p in dosyalar:
            goreli = p.relative_to(kaynak if kaynak.is_dir() else kaynak.parent)
            varis = hedef / alt / goreli
            varis.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, varis)
            kopyalanan.append((f"{alt}/{goreli.as_posix()}", p))

    print(f"KAYNAK: {KOK}  (git {_git_head()})")
    print(f"HEDEF : {hedef}" + ("   [KURU — kopyalanmadı]" if kuru else ""))
    for s in satirlar:
        print("  " + s)
    print(f"  TOPLAM ~{toplam_bayt/1e6:.1f} MB")

    if eksikler:
        print("\n🔴 EKSİK ZORUNLU PARÇALAR:")
        for e in eksikler:
            print("  " + e)

    print("\nİNSANIN KOYACAĞI (bu betik üretemez):")
    for ad, aciklama in INSAN_PARCALARI:
        print(f"  ☐ {ad} — {aciklama}")

    if kuru:
        return 3 if eksikler else 0
    if eksikler and not eksige_ragmen:
        (hedef / "EKSIKLER.txt").parent.mkdir(parents=True, exist_ok=True)
        (hedef / "EKSIKLER.txt").write_text("\n".join(eksikler) + "\n",
                                            encoding="utf-8")
        print("\nRED: zorunlu parça eksik — bellek EKSİK hazırlandı. "
              "`--eksige-ragmen` ile bilerek geçilir (MANIFEST'e yazılır).")
        return 3

    manifest = [
        "NAVITAS SAHA BELLEĞİ — MANIFEST",
        f"üretim: {time.strftime('%Y-%m-%d %H:%M:%S')}  ·  git HEAD: {_git_head()}",
        f"dosya: {len(kopyalanan)}  ·  boyut: {toplam_bayt/1e6:.1f} MB",
        f"eksik zorunlu: {len(eksikler)}"
        + ("  (BİLEREK GEÇİLDİ --eksige-ragmen)" if eksikler and eksige_ragmen else ""),
        "",
        "İNSANIN KOYACAĞI:",
    ]
    manifest += [f"  ☐ {ad} — {a}" for ad, a in INSAN_PARCALARI]
    manifest += ["", "SHA256:"]
    manifest += [f"  {_sha256(p)}  {ad}" for ad, p in kopyalanan]
    (hedef / "MANIFEST.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    print(f"\nMANIFEST: {hedef / 'MANIFEST.txt'}  ({len(kopyalanan)} dosya)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # Varsayilan DEPO DISIDIR: ~1,3 GB'lik kopya depoya girmemeli (results/
    # izleniyor). USB takiliysa dogrudan onun kokunu ver.
    ap.add_argument("--hedef", type=Path, default=KOK.parent / "navitas_bellek",
                    help="bellek klasörü (USB kök dizini olabilir)")
    ap.add_argument("--kuru", action="store_true",
                    help="kopyalama; ne alınacağını ve eksikleri yaz")
    ap.add_argument("--eksige-ragmen", action="store_true",
                    help="zorunlu parça eksikken de hazırla (MANIFEST'e yazılır)")
    a = ap.parse_args(argv)
    return hazirla(a.hedef.resolve(), kuru=a.kuru, eksige_ragmen=a.eksige_ragmen)


if __name__ == "__main__":
    sys.exit(main())
