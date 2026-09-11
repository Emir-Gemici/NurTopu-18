#!/usr/bin/env python3
"""NEDEN: T221-D/D2/D3 · GERCEK DOSYADA mutasyon: A18 bozuk depoda DUSUYOR mu?

Kilitler: README SS6.6 kabul olcutu 1 (sayi .param'dan, beklenen-yok listesi, eski olcut 1'in cizili
durusu, acilis ve CHUTE_ENABLED kosulu), CHUTE_* on hukmu, sitl_yoklama.txt SS6.1 ek taramasi.

T221-D2 (10 Eyl, curutucu RED): curutucunun KACAN dort mutanti AYNI metinle eklendi -
C2 (eski olcut 1'in ~~cizgisi~~ kaldirildi), C3 (on hukum "Olcut 1 DUSER" -> "OLCULEMEDI"),
C4 (olcut 1'den `param show CHUTE_ENABLED` 1 silindi), C7 ("eklenmez, esik gevsetilmez" parantezi
silindi). E1..E6: T221-D2'nin her yeni kilidi icin ayri mutant (kilitsiz A18 bunlari da gecirir).
T221-D3: D-454 curutucusunun N1..N8 ve N3b/N5b/N4c mutasyonlari birebir; olumlu hukum,
HTML cizgisi, paragraf disi celiski ve DDR komutlari icin ek kontroller.

Her mutant icin:
  1. calisma kopyasi git'in kayitli haliyle BAYT-ES mi: `git cat-file --filters <ref>:<yol>`
     (core.autocrlf=true -> checkout'un urettigi CRLF'in aynisi; `git show <ref>:<yol>` ham LF blob
     verir, calisma kopyasiyla bayt-es DEGILDIR). Degilse mutant KOSULMAZ.
  2. mutant yazilir (satir sonu dosyanin kendi bicimiyle; yalniz desen degisir),
  3. kapi (tests/test_faz_b_arduplane_sablon.py) alt surecte TAM kosulur; ayrica A18 denetleyicisi
     (sitl_kabul_hatalari) bu surecte diskteki mutant dosyalarla cagrilir: hangi kilidin tuttugu gorulur,
  4. dosya HER DURUMDA (finally) git'ten alinan baytlarla geri yazilir ve sha256'si ilk haliyle
     karsilastirilir.
YAKALANDI = cikis != 0 VE test_a18 FAIL VE beklenen hata alt-dizgesi A18 hata listesinde.
Geri yuklemeden sonra kapi OK ve 3 dosya git ile bayt-es olmali.

REF: varsayilan "index" (git add'lenmis, commit'e girecek hal). Commit sonrasi: --ref HEAD.
KULLANIM: python -B results/fdr_sprint_20260910/H8/T221/mutasyon_kos_d.py [--ref HEAD] \\
              > results/fdr_sprint_20260910/H8/T221/mutasyon_cikti_d.txt
"""
import argparse
import contextlib
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[4]
PARAM = "config/pixhawk/arduplane_final.param"
README = "config/pixhawk/README.md"
YOKLAMA = "results/fdr_sprint_20260910/H8/T221/sitl_yoklama.txt"
TEST = "tests/test_faz_b_arduplane_sablon.py"
A18 = "test_a18_sitl_olculemedi_yazili_gecti_yazilmaz"
SHA = "639a8381c1d8805a2e252a679f22d72473232ac813c810216d99aaba55e160e9"
ESKI_OLCUT1 = ("Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1 ve dosyadaki 62 adın 62'si "
               "yüklü.")
YENI_OLCUT1_BASI = "Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1; dosyadaki"

# (ad, dosya, eski, yeni, beklenen eslesme adedi, A18 hata listesinde beklenen alt-dizge)
MUTANTLAR = (
    ("R1 README beklenen-yok listesi bosaltildi", README,
     "listesi = {`BRD_SER2_RTSCTS`}", "listesi = {}", 1, "onceden yazilan"),
    ("R2 README olcut 1: SITL'de 61 yerine 62 (SITL'de tutamayan eski sayi)", README,
     "SITL'de **61**'i", "SITL'de **62**'si", 1, "olcut 1: SITL'de yuklu"),
    ("R3 .param'dan TKOFF_ACCEL_CNT satiri silindi (N .param'dan hesaplanir)", PARAM,
     "\nTKOFF_ACCEL_CNT,1\n", "\n", 1, "olcut 1: dosyadaki ad"),
    ("R4 yoklama SS6.1: SER2_RTSCTS 0 -> 1 (beklenen-yok olcumle celisir)", YOKLAMA,
     f"  {'SER2_RTSCTS':22s} 0\n", f"  {'SER2_RTSCTS':22s} 1\n", 1, "olcumle celisir"),
    ("R5 README olcut 1 ikili sha'sinin son hanesi degisti", README,
     f"(sha256 `{SHA}`)", f"(sha256 `{SHA[:-1]}8`)", 1, "ikili sha"),
    ("R6 yoklama SS6.1: pozitif kontrol SAFETY_DEFLT 1 -> 0", YOKLAMA,
     f"  {'SAFETY_DEFLT':22s} 1\n", f"  {'SAFETY_DEFLT':22s} 0\n", 1, "pozitif kontrol"),
    ("R7 README 'her eksik ad DUSER' kurali yumusatildi", README,
     "listenin dışındaki her eksik ad **DÜŞER**", "listenin dışındaki her eksik ad not edilir", 1,
     "on kayit cumlesi eksik"),
    ("R8 README CHUTE_* on hukmunun kayit cumlesi kisaltildi", README,
     "SITL paraşütsüz derlenmiş — paraşüt zinciri ÖLÇÜLEMEDİ", "SITL paraşütsüz derlenmiş", 1,
     "on kayit cumlesi eksik"),
    ("R9 README 'olcumden once, D-449' damgasi (2 yer) silindi", README,
     "ölçümden önce, D-449", "D-449", 2, "on kayit cumlesi eksik"),
    ("R10 README SITL features.txt:139 -> :138", README,
     "SITL_x86_64_linux_gnu/features.txt:139", "SITL_x86_64_linux_gnu/features.txt:138", 1,
     "yoklamadaki satirla uyusmuyor"),
    # ── T221-D2: curutucunun KACAN mutantlari (journal wf_b9bb9db5-4d7, mut_curutucu.py ile AYNI metin)
    ("C2 eski olcut 1'in ~~cizgisi~~ kaldirildi (62 adin 62'si yeniden yururlukte)", README,
     f"1. ~~{ESKI_OLCUT1}~~", f"1. {ESKI_OLCUT1}", 1, "eski olcut 1 yururlukteki metinde"),
    ("C3 on hukum gevsetildi: Olcut 1 DUSER -> OLCULEMEDI", README,
     "Ölçüt 1 **DÜŞER** (`CHUTE_*`", "Ölçüt 1 **ÖLÇÜLEMEDİ** (`CHUTE_*`", 1,
     "on kayit cumlesi eksik: 'Ölçüt 1 **DÜŞER**"),
    ("C4 yeni olcut 1'den `param show CHUTE_ENABLED` 1 silindi", README,
     YENI_OLCUT1_BASI, "Açılış `ArduPlane V4.5.7`; dosyadaki", 1,
     "olcut 1 maddesinde '`param show CHUTE_ENABLED` 1' 0 kez"),
    ("C7 on hukmun 'eklenmez, esik gevsetilmez' parantezi silindi", README,
     " (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez)", "", 1,
     "on kayit cumlesi eksik: 'Ölçüt 1 **DÜŞER**"),
    # ── T221-D2 ek: her yeni kilidin kendi mutanti
    ("E1 eski olcut 1 tamamen silindi (FDR: eski metin silinmez, cizilir)", README,
     f"~~{ESKI_OLCUT1}~~", "", 1, "~~cizili~~ 0 kez"),
    ("E2 cizgi notundaki tarih damgasi silindi (on hukum basliginda duruyor)", README,
     "*(10 Eylül, ölçümden önce, D-449:", "*(D-449:", 1, "ardinda tarih damgasi yok"),
    ("E3 olcut 1'den acilis surumu `ArduPlane V4.5.7` silindi", README,
     YENI_OLCUT1_BASI, "`param show CHUTE_ENABLED` 1; dosyadaki", 1,
     "olcut 1 maddesinde 'Açılış `ArduPlane V4.5.7`' 0 kez"),
    ("E4 on hukme celiskili ikinci olcut 1 hukmu eklendi (DUSER cumlesi yerinde)", README,
     "yine ölçülür.", "yine ölçülür. Ölçüt 1 bu durumda ÖLÇÜLEMEDİ sayılır.", 1,
     "birden cok kez anilmis"),
    ("E5 on hukum paragrafi bolundu (Olcut 1 DUSER cumlesi kosul paragrafindan cikti)", README,
     "kaydedilir. Ölçüt 1 **DÜŞER**", "kaydedilir.\n\nÖlçüt 1 **DÜŞER**", 1,
     "on hukum paragrafinda yok"),
    ("E6 on hukum basligindaki tarih damgasi silindi (cizgi notunda duruyor)", README,
     "yoksa (10 Eylül, ölçümden önce, D-449):**", "yoksa (D-449):**", 1,
     "basliginda tarih damgasi yok"),
    # ── D-454: scratchpad/t221d2_curut/mut_d2.py'deki AYNI desen ve yerine koymalar.
    ("N1 cizili olcut 4/5 OLCULEMEDI + dogrulandi", README,
     "ölçüt 4 ve 5\nÖLÇÜLEMEDİ; ölçüt 3", "ölçüt 4 ve 5\n~~ÖLÇÜLEMEDİ~~ (doğrulandı: tutar); ölçüt 3",
     1, "on kayitli metin degisti"),
    ("N2 on hukum olcut 2 OLCULEMEDI yerine tutar", README,
     "kendiliğinden sağlanır → ÖLÇÜLEMEDİ;", "kendiliğinden sağlanır → tutar;", 1,
     "on kayitli metin degisti"),
    ("N3 olcut 4 ve 5 arkasina ikinci olcut 5 hukmu", README,
     "yine ölçülür. Yukarıdaki", "yine ölçülür; ölçüt 5 ise tutar sayılır. Yukarıdaki", 1,
     "birden cok kez anilmis"),
    ("N4 eski olcut tipografik kesme ile geri gelir", README,
     "yüklü (N − |beklenen-yok|;", "yüklü ve dosyadaki 62 adın 62’si de yüklü (N − |beklenen-yok|;",
     1, "eski olcut 1 yururlukteki metinde"),
    ("N4b eski olcut 62 adin tamami olarak geri gelir", README,
     "yüklü (N − |beklenen-yok|;", "yüklü ve dosyadaki 62 adın tamamı da yüklü (N − |beklenen-yok|;",
     1, "eski olcut 1 yururlukteki metinde"),
    ("N5 CHUTE_ENABLED 1 ya da bos", README,
     YENI_OLCUT1_BASI, "Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1 (ya da boş); dosyadaki",
     1, "kabul blogu on kayitli"),
    ("N6 sonuc KOSULMADI cizildi ve kosuldu yazildi", README,
     "**Sonuç: ArduPlane SITL provası KOŞULMADI.**",
     "~~**Sonuç: ArduPlane SITL provası KOŞULMADI.**~~ **Sonuç: prova koşuldu (doğrulandı).**", 1,
     "sonuc cumlesi yururlukte"),
    ("N7 Olcut 1 DUSER gerekcesi cizildi ve OLCULEMEDI yazildi", README,
     "Ölçüt 1 **DÜŞER** (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez);",
     "Ölçüt 1 ~~**DÜŞER** (`CHUTE_*` beklenen-yok listesine sonradan eklenmez, eşik gevşetilmez)~~ ÖLÇÜLEMEDİ;",
     1, "on kayit cumlesi eksik"),
    ("N8 kalin sayilar ve tipografik kesmeyle ikinci eski olcut", README,
     "   Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1; dosyadaki **62**",
     "   Ayrıca dosyadaki **62** adın **62**’si yüklü. Açılış `ArduPlane V4.5.7`; `param show CHUTE_ENABLED` 1; dosyadaki **62**",
     1, "eski olcut 1 yururlukteki metinde"),
    ("N3b ikinci Olcut 5 hukmu M16 on kosuluna dokunmadan", README,
     "yine ölçülür. Yukarıdaki", "yine ölçülür. Ölçüt 5 ise tutar sayılır. Yukarıdaki", 1,
     "birden cok kez anilmis"),
    ("N5b CHUTE_ENABLED bos donerse tutar M17 on kosuluna dokunmadan", README,
     "listesi = {`BRD_SER2_RTSCTS`}. Gerekçe",
     "listesi = {`BRD_SER2_RTSCTS`}; `CHUTE_ENABLED` boş dönerse de bu ölçüt tutar. Gerekçe", 1,
     "kabul blogu on kayitli"),
    ("N4c kontrol eski olcut duz kesmeyle geri gelir", README,
     "yüklü (N − |beklenen-yok|;", "yüklü ve dosyadaki 62 adın 62'si de yüklü (N − |beklenen-yok|;",
     1, "eski olcut 1 yururlukteki metinde"),
    ("D3a olumlu hukum ikinci paragrafta", README,
     "kaydı değiştirmez.", "kaydı değiştirmez.\n\nSITL sonucu: DOĞRULANDI.", 1, "olumlu hukum"),
    ("D3b paragraf disinda olcut 5 muaf", README,
     "kaydı değiştirmez.", "kaydı değiştirmez.\n\n5. ölçüt bu durumda muaftır.", 1,
     "ek/celiskili olcut atfi"),
    ("D3c HTML ile KOSULMADI cizildi", README,
     "KOŞULMADI.", "<del>KOŞULMADI.</del>", 1, "HTML cizgisi"),
    ("D3d parasut servosu yerine gaz cikisi", README,
     "param set SIM_PARA_PIN 7", "param set SIM_PARA_PIN 3", 1, "SIM_PARA_PIN komutu"),
    ("D3e mancininik ivmesi degisti", README,
     "param set SIM_SHOVE_X 46", "param set SIM_SHOVE_X 4", 1, "SIM_SHOVE_X komutu"),
    ("D3f mancininik suresi degisti", README,
     "param set SIM_SHOVE_TIME 390", "param set SIM_SHOVE_TIME 39", 1, "SIM_SHOVE_TIME komutu"),
)


def git(*arg):
    return subprocess.run(["git", *arg], cwd=KOK, capture_output=True, check=True).stdout


def git_bayt(ref, yol):
    """Dosyanin git'teki kayitli hali, checkout filtreleriyle (autocrlf) = beklenen calisma baytlari."""
    nesne = f":{yol}" if ref == "index" else f"{ref}:{yol}"
    return git("cat-file", "--filters", nesne)


def kapi():
    r = subprocess.run([sys.executable, "-X", "utf8", "-B", "-m", "unittest", "discover", "-s", "tests",
                        "-p", "test_faz_b_arduplane_sablon.py"],
                       cwd=KOK, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def a18_hatalari(tfb):
    """A18 denetleyicisi (sitl_kabul_hatalari) diskteki GUNCEL dosyalarla: hangi kilit tuttu?"""
    try:
        p, _, _, _ = tfb.param_oku(tfb.PARAM_DOSYASI)
        sitl = tfb.readme_bolumu(tfb._readme(), tfb.README_SITL)
        if sitl is None:
            return [f"README'de {tfb.README_SITL!r} yok"]
        return tfb.sitl_kabul_hatalari(sitl, p, tfb._kanit(),
                                       tfb.SITL_YOKLAMA.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001 - mutant ayristiriciyi da bozabilir; hata listeye yazilir
        return [f"{type(e).__name__}: {e}"]


def kos(a):
    sys.path.insert(0, str(KOK / "tests"))
    import test_faz_b_arduplane_sablon as tfb  # noqa: E402 - sabitler bir kez; dosyalar her cagrida okunur
    head = git("rev-parse", "HEAD").decode().strip()
    test_bayt = (KOK / TEST).read_bytes()
    print(f"# T221-D/T221-D2/T221-D3 gercek dosya mutasyonu · "
          f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    print(f"ref={a.ref} · HEAD={head} · core.autocrlf={git('config', 'core.autocrlf').decode().strip()}")
    print(f"kapi dosyasi {TEST} sha256={hashlib.sha256(test_bayt).hexdigest()[:16]} · git {a.ref} ile "
          f"bayt-es={git_bayt(a.ref, TEST) == test_bayt} · git HEAD ile bayt-es="
          f"{git_bayt('HEAD', TEST) == test_bayt}")
    temel = a18_hatalari(tfb)
    print(f"[mutasyonsuz] A18 hatalari (surecte): {json.dumps(temel, ensure_ascii=False)}")
    sonuc = 0 if temel == [] else 1
    yakalanan = 0
    for ad, goreli, eski, yeni, adet, beklenen_hata in MUTANTLAR:
        dosya = KOK / goreli
        asil = dosya.read_bytes()
        ozet = hashlib.sha256(asil).hexdigest()
        kayitli = git_bayt(a.ref, goreli)
        if kayitli != asil:
            print(f"[{ad}] KOSULMADI: calisma kopyasi git {a.ref} ile bayt-es DEGIL ({goreli})")
            sonuc = 1
            continue
        crlf = b"\r\n" in asil
        metin = asil.decode("utf-8").replace("\r\n", "\n")
        if metin.count(eski) != adet:
            print(f"[{ad}] UYGULANAMADI (eslesme {metin.count(eski)} != {adet})")
            sonuc = 1
            continue
        mutant = metin.replace(eski, yeni)
        try:
            dosya.write_bytes((mutant.replace("\n", "\r\n") if crlf else mutant).encode("utf-8"))
            kod, cikti = kapi()
            a18 = a18_hatalari(tfb)
        finally:
            dosya.write_bytes(kayitli)
        geri = hashlib.sha256(dosya.read_bytes()).hexdigest() == ozet
        dusenler = sorted({s.split(" ")[1] for s in cikti.splitlines()
                           if s.startswith(("FAIL: ", "ERROR: "))})
        isabet = any(beklenen_hata in h for h in a18)
        yakalandi = kod != 0 and A18 in dusenler and isabet
        yakalanan += yakalandi
        print(f"[{ad}] {goreli} · cikis={kod} dusen={dusenler} -> "
              f"{'YAKALANDI' if yakalandi else 'KACTI'} · geri_yukleme(git cat-file --filters {a.ref}) "
              f"bayt_es={geri} sha256={ozet[:12]}")
        print(f"    beklenen A18 hatasi {beklenen_hata!r}: {'VAR' if isabet else 'YOK'}")
        print(f"    A18 hatalari (surecte, {len(a18)}): {json.dumps(a18, ensure_ascii=False)[:700]}")
        print("    son satir: " + (cikti.strip().splitlines() or [''])[-1])
        if not (yakalandi and geri):
            sonuc = 1
    kod, cikti = kapi()
    temiz = all(git_bayt(a.ref, y) == (KOK / y).read_bytes() for y in (PARAM, README, YOKLAMA))
    print(f"[OZET] {yakalanan}/{len(MUTANTLAR)} YAKALANDI")
    print(f"[geri yukleme sonrasi] cikis={kod} · 3 dosya git {a.ref} ile bayt-es={temiz} · "
          f"son satir: {(cikti.strip().splitlines() or [''])[-1]}")
    return sonuc or (0 if kod == 0 and temiz else 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ref", default="index", help="'index' (varsayilan) ya da bir rev (HEAD)")
    ap.add_argument("--cikti", type=Path, help="UTF-8 ham kanit dosyasi (mevcut dosyayi ezmez)")
    a = ap.parse_args(argv)
    if a.cikti is None:
        return kos(a)
    with a.cikti.open("x", encoding="utf-8", newline="\n") as akim:
        with contextlib.redirect_stdout(akim):
            kod = kos(a)
            print(f"cikis={kod}")
    print(f"Kanit: {a.cikti} · cikis={kod}")
    return kod


if __name__ == "__main__":
    sys.exit(main())
