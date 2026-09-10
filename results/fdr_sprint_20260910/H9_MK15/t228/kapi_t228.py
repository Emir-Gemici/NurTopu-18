"""T228 KAPI KOSUCUSU — gorev kapisinin HAM ciktisini `t228/kapi_ciktisi.txt`'ye yazar.

Kapi (gorev tanimi): yeni test + test_faz_b_jetson_baslat*.py + test_jetson_comms_paketi +
test_t135 + jetson_paket aynasi (+ ilgili paket/kilavuz kapilari) + bash -n jetson_baslat.sh +
genel kapi codes/test_rota_sentetik.py (15/15) + akis diyagrami dogrulayici.
Her kalem icin komut, cikis kodu ve son satirlar yazilir; hic bir kalem atlanmaz.

KOSUM (depo kokunden): O:/navitas-local-train/venv/Scripts/python.exe -B \
    results/fdr_sprint_20260910/H9_MK15/t228/kapi_t228.py
"""
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = sys.executable
CIKTI = Path(__file__).resolve().parent / "kapi_ciktisi.txt"
TEST_KALIPLARI = (
    "test_isaretli_gosterici.py",
    "test_faz_b_jetson_baslat*.py",
    "test_jetson_comms_paketi.py",
    "test_t135_kamera_dogrula_icerik.py",
    "test_faz_b_kamera_koprusu*.py",
    "test_faz_b_kamera_lan.py",
    "test_jetson_paket_defteri.py",
    "test_t202_jetson_paket_butunlugu.py",
    "test_kilavuz_kurulum_yordami.py",
    "test_kilavuz_gecis_yordami.py",
    "test_faz_b_surum_dondurma.py",
    "test_t120_sahte_kapi_yasagi.py",
    "test_t220_jetson_istekleri.py",
)


def bash_bul():
    for aday in (Path(r"C:\Program Files\Git\bin\bash.exe"), Path(r"C:\Program Files\Git\usr\bin\bash.exe")):
        if aday.is_file():
            return str(aday)
    return shutil.which("bash")


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
    print("\n".join(kayit), flush=True)
    return kayit, p.returncode, p.stdout + p.stderr


def t202_ortam_denetimi():
    """t202 DUSERSE: dusen kalemler yalniz git-ignore'lu model agirliklari mi (worktree'de yok)?

    Olcum: ayni kapi (t202 `_kullanilan() - _kurulan()`) GECICI bir paket kopyasinda yeniden
    kosulur; kopyanin models/ dizinine ANA DEPODAKI model dosyalarinin ADLARI bos yer tutucu olarak
    konur (t202 icerik okumaz, yalniz adlari sayar). Ana depo `tests/depo_yollari.ana_depo_adaylari`
    ile TURETILIR (ciplak yol yok). Gecici dizin silinir; depoya hicbir sey yazilmaz.
    """
    sys.path.insert(0, str(KOK / "tests"))
    import test_t202_jetson_paket_butunlugu as t202
    from depo_yollari import ana_depo_adaylari
    satir = []
    once = sorted(t202._kullanilan() - t202._kurulan())
    satir.append("  t202 eksik (bu agac): {}".format(once))
    ana = next((a / "jetson_paket" / "models" for a in ana_depo_adaylari(KOK)[1:]
                if (a / "jetson_paket" / "models").is_dir()), None)
    if ana is None:
        satir.append("  ana depo jetson_paket/models bulunamadi — ortam denetimi YAPILAMADI")
        return satir, False
    d = Path(tempfile.mkdtemp(prefix="navitas_t228_t202_"))
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
        t228_kurulu = "scripts/isaretli_gosterici.py" in t202._kurulan()
    finally:
        t202.PAKET, t202.KILAVUZ = eski
        shutil.rmtree(d, ignore_errors=True)
    yalniz_model = all(y.startswith("models/") for y in once)
    satir.append("  ana depo models/ adlari ({} dosya) ile ayni kapi: eksik = {}".format(len(adlar), sonra))
    satir.append("  bu agacta dusenlerin hepsi models/: {} · T228 satiri kuruluyor "
                 "(scripts/isaretli_gosterici.py): {}".format(yalniz_model, t228_kurulu))
    return satir, (yalniz_model and sonra == [] and t228_kurulu)


def main():
    log = ["# T228 kapi ciktisi · {} · {}".format(time.strftime("%Y-%m-%d %H:%M:%S"), PY)]
    ozet = []
    # 1) paket aynasi: paketleyici kosulur, sonra kod/ kopyasi kanonikle bayt-es mi
    k, rc, _ = kos("jetson_paket_hazirla (ayna tazele)", [PY, "-B", "scripts/jetson_paket_hazirla.py"], 2)
    log += k
    ayna_es = (KOK / "scripts" / "isaretli_gosterici.py").read_bytes() == \
        (KOK / "jetson_paket" / "kod" / "isaretli_gosterici.py").read_bytes()
    log.append("  ayna bayt-es (scripts/ <-> jetson_paket/kod/ isaretli_gosterici.py): {}".format(ayna_es))
    ozet.append(("jetson_paket_hazirla + ayna", rc == 0 and ayna_es))
    # 2) bash -n (LF kopya + calisma kopyasi)
    bash = bash_bul()
    if bash is None:
        log.append("== bash -n: YAPILAMADI (bash yok)")
        ozet.append(("bash -n", False))
    else:
        d = Path(tempfile.mkdtemp(prefix="navitas_t228_kapi_"))
        lf = d / "jetson_baslat.sh"
        lf.write_bytes((KOK / "jetson_paket" / "jetson_baslat.sh").read_bytes().replace(b"\r\n", b"\n"))
        for ad, yol in (("bash -n jetson_baslat.sh (LF kopya)", lf),
                        ("bash -n jetson_baslat.sh (calisma kopyasi)", KOK / "jetson_paket" / "jetson_baslat.sh")):
            k, rc, _ = kos(ad, [bash, "-n", str(yol).replace("\\", "/")], 2)
            log += k
            ozet.append((ad, rc == 0))
        shutil.rmtree(d, ignore_errors=True)
    # 3) testler
    for kalip in TEST_KALIPLARI:
        k, rc, cikti = kos(kalip, [PY, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", kalip])
        log += k
        if rc != 0:
            # dusen testlerin adlarini da yaz (ham)
            log += ["  DUSEN: " + s for s in cikti.splitlines() if s.startswith(("FAIL:", "ERROR:"))]
        ozet.append((kalip, rc == 0))
        if kalip == "test_t202_jetson_paket_butunlugu.py" and rc != 0:
            satir, ok = t202_ortam_denetimi()
            log.append("== t202 ortam denetimi (dusen kalemler yalniz git-ignore'lu modeller mi?)")
            log += satir
            print("\n".join(log[-(len(satir) + 1):]), flush=True)
            ozet.append(("t202 ortam denetimi: dusus YALNIZ worktree'de olmayan models/ agirliklari, "
                         "T228 satiri kuruluyor", ok))
    # 4) genel kapi + akis diyagrami
    k, rc, cikti = kos("genel kapi codes/test_rota_sentetik.py", [PY, "-B", "codes/test_rota_sentetik.py"], 3)
    log += k
    ozet.append(("test_rota_sentetik 15/15", rc == 0 and "15/15" in cikti))
    k, rc, _ = kos("akis_diyagram_dogrula", [PY, "-B", "scripts/akis_diyagram_dogrula.py"], 2)
    log += k
    ozet.append(("akis_diyagram_dogrula", rc == 0))
    log.append("")
    log.append("## OZET")
    log += ["{} {}".format("GECTI" if ok else "DUSTU", ad) for ad, ok in ozet]
    CIKTI.write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log[-(len(ozet) + 1):]))


if __name__ == "__main__":
    main()
