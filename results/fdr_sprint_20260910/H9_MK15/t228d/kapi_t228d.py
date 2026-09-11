"""T228-D KAPI KOSUCUSU — gorev kapisinin HAM ciktisini `t228d/kapi_ciktisi.txt`'ye yazar.

Kapi (gorev tanimi T228-D): test_isaretli_gosterici (yeni testlerle) + test_faz_b_jetson_baslat* +
test_jetson_comms_paketi + test_t135 + test_olcum_ayna_senkronu + test_faz_b_kamera_koprusu* +
jetson_paket aynasi (G9 bayt-es) + genel kapi codes/test_rota_sentetik.py (15/15) +
akis_diyagram_dogrula. T228 kapisinin ek paket/kilavuz kalemleri ve t202 (worktree'de git-ignore'lu
models/ yuzunden dusebilir -> ortam denetimi) de kosulur. `--kip drm --kuru` ciktisi kanit olarak
eklenir. Yardimcilar (kos, temizle, t202 ortam denetimi) T228 kosucusundan (t228/kapi_t228.py)
alinir — o dosyanin ciktisina DOKUNULMAZ.

--ayna-denetle mevcut gosterici aynasini denetler, paket dosyalarini yenilemez. --cikti eski
kaniti koruyarak ayri dosya secer; yanindaki .raw.txt tam stdout/stderr'i tutar. Herhangi bir
kalem duserse cikis 1'dir; t202 ortam aciklamasi orijinal dususu GECTI'ye cevirmez.

KOSUM (depo kokunden): O:/navitas-local-train/venv/Scripts/python.exe -B \
    results/fdr_sprint_20260910/H9_MK15/t228d/kapi_t228d.py
"""
import argparse
import importlib.util
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BURASI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("kapi_t228", BURASI.parent / "t228" / "kapi_t228.py")
k228 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(k228)

KOK, PY = k228.KOK, k228.PY
CIKTI = BURASI / "kapi_ciktisi.txt"
TEST_KALIPLARI = (
    "test_isaretli_gosterici.py",
    "test_faz_b_jetson_baslat*.py",
    "test_jetson_comms_paketi.py",
    "test_t135_kamera_dogrula_icerik.py",
    "test_olcum_ayna_senkronu.py",
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


def kos(ad, argv, son=4):
    kayit, rc, cikti = k228.kos(ad, argv, son)
    with CIKTI.with_suffix(".raw.txt").open("a", encoding="utf-8") as ham:
        ham.write("\n".join(kayit[:2]) + "\n" + k228.temizle(cikti) + "\nEXIT={}\n\n".format(rc))
    return kayit, rc, cikti


def main():
    global CIKTI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cikti", type=Path, default=CIKTI)
    ap.add_argument("--ayna-denetle", action="store_true",
                    help="Paketi yenilemeden mevcut gosterici aynasinin bayt-esligini denetle.")
    args = ap.parse_args()
    CIKTI = args.cikti.resolve()
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    os.environ["PYTHONUTF8"] = "1"  # Alt sureclerin Turkce kaniti Windows kod sayfasina takilmaz.
    log = ["# T228-D + T228-D2 kapi ciktisi · {} · {}".format(time.strftime("%Y-%m-%d %H:%M:%S"),
                                                             Path(PY).name)]
    ozet = []
    rc = 0
    if not args.ayna_denetle:
        k, rc, _ = kos("jetson_paket_hazirla (ayna tazele)",
                       [PY, "-B", "scripts/jetson_paket_hazirla.py"], 2)
        log += k
    ayna_es = (KOK / "scripts" / "isaretli_gosterici.py").read_bytes() == \
        (KOK / "jetson_paket" / "kod" / "isaretli_gosterici.py").read_bytes()
    log.append("  ayna bayt-es (scripts/ <-> jetson_paket/kod/ isaretli_gosterici.py): {}".format(
        ayna_es))
    ozet.append(("mevcut ayna bayt-es" if args.ayna_denetle else "jetson_paket_hazirla + ayna bayt-es",
                 rc == 0 and ayna_es))
    k, rc, cikti = kos("isaretli_gosterici --kip drm --kuru (kanit)",
                            [PY, "-B", "scripts/isaretli_gosterici.py", "--kip", "drm", "--kuru"], 14)
    log += k
    ozet.append(("--kip drm --kuru cikis 0 ve -v/identity/DOGRULANACAK basar",
                 rc == 0 and "gst-launch-1.0 -v -e" in cikti and "identity name=nabiz silent=false"
                 in cikti and "[DOGRULANACAK]" in cikti))
    for kalip in TEST_KALIPLARI:
        k, rc, cikti = kos(kalip, [PY, "-B", "-m", "unittest", "discover", "-s", "tests",
                                        "-p", kalip])
        log += k
        if rc != 0:
            log += ["  DUSEN: " + s for s in cikti.splitlines() if s.startswith(("FAIL:", "ERROR:"))]
        ozet.append((kalip, rc == 0))
        if kalip == "test_t202_jetson_paket_butunlugu.py" and rc != 0:
            satir, ok = k228.t202_ortam_denetimi()
            log.append("== t202 ortam denetimi (dusen kalemler yalniz git-ignore'lu modeller mi?)")
            log += satir
            print("\n".join(log[-(len(satir) + 1):]), flush=True)
            ozet.append(("t202 ortam denetimi: dusus YALNIZ worktree'de olmayan models/ agirliklari, "
                         "T228 satiri kuruluyor", ok))
        CIKTI.write_text("\n".join(log) + "\n", encoding="utf-8")
    k, rc, cikti = kos("genel kapi codes/test_rota_sentetik.py",
                            [PY, "-B", "codes/test_rota_sentetik.py"], 3)
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
    return 0 if all(ok for _ad, ok in ozet) else 1


if __name__ == "__main__":
    raise SystemExit(main())
