"""T236-B kilit mutasyon gosterisi: her kilit GERCEK dosya mutasyonuyla dusuyor mu?

Her adim: dosyayi boz -> testleri kos -> hangi testler dustu -> `git checkout` ile
BAYT ESI geri yukle ve sha256 dogrula.
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

KOK = Path(r"O:\navitas\.claude\worktrees\wf_d450cb9f-ba7-9")
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"
T235 = "results/fdr_sprint_20260910/H1/t235"

MUTASYONLAR = [
    # (ad, dosya, eski, yeni, beklenen test)
    ("M1 cizgi kaldirildi (eski yaw yeri ham metinde geri geliyor)",
     f"{T235}/ON_KAYIT.md",
     "~~`CONDITION_YAW(\u03b2 \u2212 montaj_yaw)` `LOITER_TIME`'dan **SONRA**",
     "`CONDITION_YAW(\u03b2 \u2212 montaj_yaw)` `LOITER_TIME`'dan **SONRA**",
     "K1"),
    ("M2 yasakli kural ES ANLAMLI sozcukle geri konuyor",
     f"{T235}/ON_KAYIT.md",
     "\u0130rtifa (kip, h) se\u00e7imine g\u00f6re",
     "`CONDITION_YAW` `LOITER_TIME`'\u0131n hemen arkas\u0131nda yaz\u0131l\u0131r. "
     "\u0130rtifa (kip, h) se\u00e7imine g\u00f6re",
     "K1"),
    ("M3 on kayitli esik gevsetildi (2,0 m -> 3,0 m)",
     f"{T235}/ON_KAYIT.md",
     "yatay konum merkezden **\u2264 2,0 m**",
     "yatay konum merkezden **\u2264 3,0 m**",
     "K1"),
    ("M4 olcum hukmu gevsetildi (OLCULEMEDI -> dogrulandi)",
     f"{T235}/ON_KAYIT.md",
     "SITL ko\u015fulamazsa **\u00d6L\u00c7\u00dcLEMED\u0130** (GE\u00c7T\u0130 de\u011fil)",
     "SITL ko\u015fulamazsa ~~**\u00d6L\u00c7\u00dcLEMED\u0130** (GE\u00c7T\u0130 de\u011fil)~~ **do\u011fruland\u0131** say\u0131l\u0131r",
     "K1"),
    ("M5 §6 mutasyon hedefi eski haline donduruldu",
     f"{T235}/ON_KAYIT.md",
     "**`CONDITION_YAW`'\u0131n `LOITER_TIME` SONRASINA ta\u015f\u0131nmas\u0131**",
     "**`CONDITION_YAW`'\u0131n `LOITER_TIME` \u00f6ncesine ta\u015f\u0131nmas\u0131**",
     "K1"),
    ("M6 README'ye celiskili ikinci hukum eklendi",
     f"{T235}/sitl/README.md",
     "### 5.5 A\u00e7\u0131k insan kalemi",
     "4.5.7 kap\u0131s\u0131 da GE\u00c7T\u0130 say\u0131l\u0131r.\n\n### 5.5 A\u00e7\u0131k insan kalemi",
     "K2"),
    ("M7 README tablosundaki oran kanittan koparildi",
     f"{T235}/sitl/README.md",
     "**0/499 = %0**",
     "**450/499 = %90**",
     "K2"),
    ("M8 README surum sayisi kanittan koparildi (8/24 -> 9/24)",
     f"{T235}/sitl/README.md",
     "(4.5.7 \u2194 4.7.1-sitl) \u2014 8/24",
     "(4.5.7 \u2194 4.7.1-sitl) \u2014 9/24",
     "K2"),
    ("M9 sablonda yaw yeniden LOITER arkasina alindi",
     "config/pixhawk/fda_gorev.waypoints",
     "7\t0\t3\t115\t90\t0\t0\t0\t0\t0\t0\t1\n8\t0\t3\t19\t60\t0\t0\t0\t0.000179663\t0.000179663\t32\t1",
     "7\t0\t3\t19\t60\t0\t0\t0\t0.000179663\t0.000179663\t32\t1\n8\t0\t3\t115\t90\t0\t0\t0\t0\t0\t0\t1",
     "K4/P6"),
    ("M10 kanit ozetinde esik gevsetildi (yaw 5 -> 8 derece)",
     f"{T235}/sitl/ozet.json",
     '"yaw_derece": 5.0',
     '"yaw_derece": 8.0',
     "K3"),
]

TESTLER = ["test_t236_fda_sitl.py", "test_fda_gorev_uret.py", "test_faz_b_pixhawk_sablon.py"]


def kos():
    dusen = []
    for t in TESTLER:
        s = subprocess.run([PY, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                            "-p", t], cwd=KOK, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        for m in re.finditer(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", s.stderr, re.M):
            dusen.append(m.group(2))
    return dusen


def sha(yol):
    return hashlib.sha256((KOK / yol).read_bytes()).hexdigest()


def main():
    temiz = kos()
    print(f"TEMIZ AGAC: dusen test = {temiz or 'YOK'}")
    if temiz:
        return 1
    tamam = True
    for ad, yol, eski, yeni, beklenen in MUTASYONLAR:
        p = KOK / yol
        once_sha = sha(yol)
        metin = p.read_bytes().decode("utf-8")
        if '\r\n' in metin:
            eski = eski.replace('\n', '\r\n')
            yeni = yeni.replace('\n', '\r\n')
        if eski not in metin:
            print(f"[ATLANDI] {ad}: hedef metin bulunamadi ({yol})")
            tamam = False
            continue
        p.write_bytes(metin.replace(eski, yeni, 1).encode("utf-8"))
        dusen = kos()
        subprocess.run(["git", "checkout", "--", yol], cwd=KOK, check=True,
                       capture_output=True)
        sonra_sha = sha(yol)
        geri = "BAYT ESI" if sonra_sha == once_sha else f"BOZUK {once_sha}!={sonra_sha}"
        durum = "YAKALANDI" if dusen else "YAKALANMADI"
        if not dusen:
            tamam = False
        print(f"[{durum}] {ad}\n    beklenen kilit: {beklenen}\n"
              f"    dusen testler ({len(dusen)}): {sorted(set(dusen))[:6]}\n"
              f"    geri yukleme: {geri} (sha256 {once_sha[:16]})")
    son = kos()
    print(f"MUTASYONLARDAN SONRA AGAC: dusen test = {son or 'YOK'}")
    return 0 if tamam and not son else 1


if __name__ == "__main__":
    sys.exit(main())
