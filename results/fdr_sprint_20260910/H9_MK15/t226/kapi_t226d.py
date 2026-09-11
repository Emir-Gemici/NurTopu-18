"""T226-D KAPI KOSUCUSU — gorev kapisinin HAM ciktisini `t226/kapi_ciktisi_t226d.txt`'ye yazar.

Kapi (D-448 T226-D gorev tanimi): test_yks_mk15_hakem_ekrani (yeni testlerle, 3 ARDISIK
kosu) + test_yks_*.py + comms/test_comms.py + test_faz_b_kamera_koprusu* + jetson aynasi
(jetson_paket_hazirla + kamera_koprusu bayt-es + test_jetson_comms_paketi +
test_t135_kamera_dogrula_icerik + test_olcum_ayna_senkronu + test_t202) + genel kapi
codes/test_rota_sentetik.py (15/15) + akis_diyagram_dogrula + test_gece_akis_diyagramlari +
akis d KAPSAM (qualname) denetimi (tazelenen her dugumun eski/yeni satiri ayni fonksiyonda mi).
Her kalem icin komut, cikis kodu ve son satirlar yazilir; hic bir kalem atlanmaz.

ORTAM KAYNAKLI DUSUS (worktree): git-ignore'lu varliklar worktree'de yoktur. Dusen kalem
YALNIZ bunlarsa ayrica OLCULUR (kanit), "gecti" sayilmaz — ozet satiri ayri yazilir:
  * test_t202: dusen kalemler yalniz models/ agirliklari mi (t228 kosucusunun yordami)
  * test_yks_*.py: dusen test yalniz `test_kompozit_dizini_listeleniyor` mu; worktree'de
    data/arena_kompozit/images yok, ana depoda var, git-ignore'lu ve izlenmiyor mu

KOSUM (depo kokunden): O:/navitas-local-train/venv/Scripts/python.exe -B \
    results/fdr_sprint_20260910/H9_MK15/t226/kapi_t226d.py
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = sys.executable
CIKTI = Path(__file__).resolve().parent / "kapi_ciktisi_t226d.txt"
#: T226-D'nin taban commit'i: T226 (77853afb) + master (362197e0) birlesmesi, WIP'ten ONCE.
#: akis d tazelemesi bu tabana gore denetlenir.
AKIS_TABAN = "76df4dcb"
HAKEM_KOSU = 3
TEST_KALIPLARI = (
    "test_yks_*.py",
    "test_faz_b_kamera_koprusu*.py",
    "test_jetson_comms_paketi.py",
    "test_t135_kamera_dogrula_icerik.py",
    "test_olcum_ayna_senkronu.py",
    "test_t202_jetson_paket_butunlugu.py",
    "test_gece_akis_diyagramlari.py",
)
#: worktree'de git-ignore'lu varlik yuzunden dusebilecegi BILINEN testler (gorev tanimi).
ORTAM_KAYNAKLI_YKS = frozenset(("test_kompozit_dizini_listeleniyor",))

#: Ham ciktiya yerel kullanici/worktree yolu girmesin: depo koku <depo>, gecici dizin <gecici>.
YER_TUTUCU = []
for _yol, _ad in ((KOK, "<depo>"), (Path(tempfile.gettempdir()), "<gecici>")):
    _s = str(_yol)
    for _b in (_s, _s.replace("\\", "/"), _s.replace("\\", "\\\\")):
        YER_TUTUCU.append((_b, _ad))
    if len(_s) > 2 and _s[1] == ":":      # MSYS bicimi: O:\x -> /o/x
        YER_TUTUCU.append(("/" + _s[0].lower() + _s[2:].replace("\\", "/"), _ad))


def temizle(metin):
    m = str(metin)
    for eski, yeni in YER_TUTUCU:
        m = m.replace(eski, yeni)
    return m


def kos(ad, argv, son=4):
    t0 = time.monotonic()
    p = subprocess.run(argv, cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    satirlar = [s for s in (p.stdout + p.stderr).splitlines() if s.strip()]
    kayit = ["== {} (cikis {}, {:.1f} s)".format(ad, p.returncode, time.monotonic() - t0),
             temizle("$ " + " ".join(argv[1:] if argv[0] == PY else argv))]
    kayit += ["  " + temizle(s) for s in satirlar[-son:]]
    with CIKTI.with_suffix(".raw.txt").open("a", encoding="utf-8") as ham:
        ham.write("\n".join(kayit[:2]) + "\n" + temizle(p.stdout + p.stderr)
                  + f"\nEXIT={p.returncode}\n\n")
    print("\n".join(kayit), flush=True)
    return kayit, p.returncode, p.stdout + p.stderr


def dusenler(cikti):
    """unittest ciktisindaki FAIL/ERROR satirlarindan test adlari."""
    return sorted({m.group(1) for m in re.finditer(r"^(?:FAIL|ERROR): (\S+)", cikti, re.M)})


def ana_depo():
    sys.path.insert(0, str(KOK / "tests"))
    from depo_yollari import ana_depo_adaylari
    return ana_depo_adaylari(KOK)[1:]


def t202_ortam_denetimi():
    """t202 DUSERSE: dusen kalemler yalniz git-ignore'lu model agirliklari mi (worktree'de yok)?

    Yordam t228 kosucusununkiyle ayni: ayni kapi (t202 `_kullanilan() - _kurulan()`) GECICI bir
    paket kopyasinda, models/ dizinine ANA DEPODAKI model dosyalarinin ADLARI bos yer tutucu
    olarak konarak yeniden kosulur (t202 icerik okumaz, yalniz adlari sayar). Ana depo
    `tests/depo_yollari.ana_depo_adaylari` ile TURETILIR. Gecici dizin silinir.
    """
    sys.path.insert(0, str(KOK / "tests"))
    import test_t202_jetson_paket_butunlugu as t202
    satir = []
    once = sorted(t202._kullanilan() - t202._kurulan())
    satir.append("  t202 eksik (bu agac): {}".format(once))
    ana = next((a / "jetson_paket" / "models" for a in ana_depo()
                if (a / "jetson_paket" / "models").is_dir()), None)
    if ana is None:
        satir.append("  ana depo jetson_paket/models bulunamadi — ortam denetimi YAPILAMADI")
        return satir, False
    d = Path(tempfile.mkdtemp(prefix="navitas_t226d_t202_"))
    paket = d / "jetson_paket"
    shutil.copytree(KOK / "jetson_paket", paket, ignore=shutil.ignore_patterns("models"))
    (paket / "models").mkdir()
    adlar = sorted(p.name for p in ana.iterdir() if p.is_file())
    for ad in adlar:
        (paket / "models" / ad).write_bytes(b"")
    eski = (t202.PAKET, t202.KILAVUZ)
    t202.PAKET, t202.KILAVUZ = paket, paket / "JETSON_KILAVUZ.md"
    try:
        sonra = sorted(t202._kullanilan() - t202._kurulan())
        kopru_kurulu = "scripts/kamera_koprusu.py" in t202._kurulan()
    finally:
        t202.PAKET, t202.KILAVUZ = eski
        shutil.rmtree(d, ignore_errors=True)
    yalniz_model = all(y.startswith("models/") for y in once)
    satir.append("  ana depo models/ adlari ({} dosya) ile ayni kapi: eksik = {}".format(len(adlar), sonra))
    satir.append("  bu agacta dusenlerin hepsi models/: {} · kamera_koprusu satiri kuruluyor "
                 "(scripts/kamera_koprusu.py): {}".format(yalniz_model, kopru_kurulu))
    return satir, (yalniz_model and sonra == [] and kopru_kurulu)


def kompozit_ortam_denetimi(dusen):
    """test_yks_*.py DUSERSE: dusen test YALNIZ `test_kompozit_dizini_listeleniyor` mu ve nedeni
    worktree'de olmayan git-ignore'lu `data/arena_kompozit/images` mi? Olculen: (1) dusen kume
    bilinen kumenin alt kumesi; (2) bu agacta dizin YOK; (3) ana depoda goruntu VAR; (4) ornek
    goruntu `git check-ignore` ile ignore'lu; (5) `git ls-files` dizinde izlenen dosya yok.
    """
    rel = Path("data", "arena_kompozit", "images")
    satir = ["  dusen testler: {}".format(dusen)]
    kume_ok = bool(dusen) and set(dusen) <= ORTAM_KAYNAKLI_YKS
    satir.append("  dusenlerin hepsi bilinen ortam-kaynakli kume {}: {}".format(
        sorted(ORTAM_KAYNAKLI_YKS), kume_ok))
    bu_yok = not (KOK / rel).is_dir()
    satir.append("  bu agacta {} YOK: {}".format(rel.as_posix(), bu_yok))
    ana = next((a / rel for a in ana_depo() if (a / rel).is_dir()), None)
    if ana is None:
        satir.append("  ana depoda {} bulunamadi — ortam denetimi YAPILAMADI".format(rel.as_posix()))
        return satir, False
    goruntu = sorted(p for p in ana.rglob("*") if p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    satir.append("  ana depoda goruntu: {} dosya".format(len(goruntu)))
    ignore_ok = False
    if goruntu:
        ornek = goruntu[0].relative_to(ana.parents[2]).as_posix()
        p = subprocess.run(["git", "-C", str(KOK), "check-ignore", "-v", ornek],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        ignore_ok = p.returncode == 0
        satir.append("  git check-ignore -v {}: {}".format(ornek, temizle(p.stdout.strip()) or "(eslesme yok)"))
    p = subprocess.run(["git", "-C", str(KOK), "ls-files", rel.as_posix()],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    izlenen = [s for s in p.stdout.splitlines() if s.strip()]
    satir.append("  git ls-files {}: {} izlenen dosya".format(rel.as_posix(), len(izlenen)))
    return satir, (kume_ok and bu_yok and bool(goruntu) and ignore_ok and not izlenen)


def main():
    global CIKTI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cikti", type=Path, default=CIKTI)
    ap.add_argument("--ayna-denetle", action="store_true",
                    help="Paketi yenilemeden mevcut kamera koprusu aynasini denetle.")
    args = ap.parse_args()
    CIKTI = args.cikti.resolve()
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    os.environ["PYTHONUTF8"] = "1"
    log = ["# T226-D kapi ciktisi · {} · {}".format(time.strftime("%Y-%m-%d %H:%M:%S"), temizle(PY))]
    head = subprocess.run(["git", "-C", str(KOK), "rev-parse", "--short=8", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    log.append("# HEAD {} (kapi calisma agacinda kosuldu)".format(head))
    ozet = []
    # 1) paket aynasi: paketleyici kosulur, sonra kod/ kopyasi kanonikle bayt-es mi
    rc = 0
    if not args.ayna_denetle:
        k, rc, _ = kos("jetson_paket_hazirla (ayna tazele)", [PY, "-B", "scripts/jetson_paket_hazirla.py"], 2)
        log += k
    ayna_es = (KOK / "scripts" / "kamera_koprusu.py").read_bytes() == \
        (KOK / "jetson_paket" / "kod" / "kamera_koprusu.py").read_bytes()
    log.append("  ayna bayt-es (scripts/ <-> jetson_paket/kod/ kamera_koprusu.py): {}".format(ayna_es))
    ozet.append(("mevcut kamera_koprusu aynasi" if args.ayna_denetle else
                 "jetson_paket_hazirla + kamera_koprusu aynasi", rc == 0 and ayna_es))
    # 2) hakem ekrani testi: 3 ARDISIK kosu (gorunur pencere, gercek Tk)
    for i in range(1, HAKEM_KOSU + 1):
        ad = "test_yks_mk15_hakem_ekrani.py kosu {}/{}".format(i, HAKEM_KOSU)
        k, rc, cikti = kos(ad, [PY, "-B", "-m", "unittest", "discover", "-s", "tests",
                               "-p", "test_yks_mk15_hakem_ekrani.py"], 3)
        log += k
        if rc != 0:
            log += ["  DUSEN: " + s for s in cikti.splitlines() if s.startswith(("FAIL:", "ERROR:"))]
        ozet.append((ad, rc == 0))
    # 3) test kaliplari
    for kalip in TEST_KALIPLARI:
        k, rc, cikti = kos(kalip, [PY, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", kalip])
        log += k
        if rc != 0:
            log += ["  DUSEN: " + s for s in cikti.splitlines() if s.startswith(("FAIL:", "ERROR:"))]
        ozet.append((kalip, rc == 0))
        if kalip == "test_t202_jetson_paket_butunlugu.py" and rc != 0:
            satir, ok = t202_ortam_denetimi()
            log.append("== t202 ortam denetimi (dusen kalemler yalniz git-ignore'lu modeller mi?)")
            log += satir
            print("\n".join(log[-(len(satir) + 1):]), flush=True)
            ozet.append(("t202 ORTAM KAYNAKLI: dusus YALNIZ worktree'de olmayan models/ agirliklari, "
                         "kamera_koprusu satiri kuruluyor", ok))
        if kalip == "test_yks_*.py" and rc != 0:
            satir, ok = kompozit_ortam_denetimi(dusenler(cikti))
            log.append("== test_yks_*.py ortam denetimi (dusus yalniz git-ignore'lu kompozit kareler mi?)")
            log += satir
            print("\n".join(log[-(len(satir) + 1):]), flush=True)
            ozet.append(("test_yks_*.py ORTAM KAYNAKLI: dusus YALNIZ worktree'de olmayan "
                         "data/arena_kompozit/images", ok))
    # 4) comms loopback
    k, rc, cikti = kos("comms/test_comms.py", [PY, "-B", "comms/test_comms.py"], 2)
    log += k
    ozet.append(("comms/test_comms.py", rc == 0 and "TEST GEÇTİ" in cikti))
    # 5) genel kapi + akis diyagrami + akis d kapsam
    k, rc, cikti = kos("genel kapi codes/test_rota_sentetik.py", [PY, "-B", "codes/test_rota_sentetik.py"], 3)
    log += k
    ozet.append(("test_rota_sentetik 15/15", rc == 0 and "15/15" in cikti))
    k, rc, _ = kos("akis_diyagram_dogrula", [PY, "-B", "scripts/akis_diyagram_dogrula.py"], 7)
    log += k
    ozet.append(("akis_diyagram_dogrula", rc == 0))
    k, rc, cikti = kos("akis d KAPSAM denetimi (taban {})".format(AKIS_TABAN),
                       [PY, "-B", "results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py",
                        "--taban", AKIS_TABAN], 1)
    log += k
    hata = [s for s in cikti.splitlines() if s.strip().startswith(("HATA", "YENI DUGUM"))]
    log += ["  " + temizle(s) for s in hata]
    ozet.append(("akis d kapsam: tazelenen her dugum ayni fonksiyonda (HATA 0)",
                 rc == 0 and "kapsam HATASI 0" in cikti and not hata))
    log.append("")
    log.append("## OZET")
    log += ["{} {}".format("GECTI" if ok else "DUSTU", ad) for ad, ok in ozet]
    CIKTI.write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log[-(len(ozet) + 1):]))
    return 0 if all(ok for _ad, ok in ozet) else 1


if __name__ == "__main__":
    raise SystemExit(main())
