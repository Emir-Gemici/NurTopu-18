"""T244 mutasyon kosucusu — GERCEK DOSYA MUTASYONU.

Her mutasyonu FDR belgelerine gercekten uygular, `tests/test_fdr_t244_ic_celiski.py`
kapisini kosar, sonra dosyalari BAYT-ES geri yukler (sha256 ile dogrulanir).
Ham cikti: `T244/mutasyon_ciktisi.txt` (+ tam stdout/stderr `.raw.txt`).

Kapsam (gorev tanimi: "en az 6 — her maddeden biri + celiskili ikinci hukum + cizili
varyant"). 11 mutant:

  M1  madde 1 — §3.3.1.1.8 "acik kalemdir" cizgisi kaldirilir (eski hukum CANLI doner)
  M2  madde 2 — §3.3.4.1.7 H1c "damgalanmadi" cizgisi kaldirilir
  M3  madde 3 — kunye satirinda `.engine` sha'si bir karakter degistirilir (defterle
      artik birebir degil)
  M4  madde 4 — §4.4 ekipman tablosunda ESC kalibrasyonu hucresi 5 Eylul haline doner
  M5  madde 5 — §4.8.3'te "Jetson'da .engine ile olculecektir" cumlesi CANLI doner
  M6  madde 6 — §4.0 Y-4-M04 durumu "YOK"a geri alinir (YONERGE ile celisir)
  M7  madde 7 — durustluk cumlesi §4.7'den silinir (yalniz Bolum 3'te kalir)
  M8  madde 8 — §3.3.4.2.8 isik/golge alt tablosunda v2 engel orani degistirilir
  MC  CELISKILI IKINCI HUKUM — §4.8.3 D-303 kabul olcutunun yanina gevsetilmis
      ikinci esik yazilir ("gozden gecirilmis kapi: <= 5/126")
  MZ1 CIZILI VARYANT (tek tilde) — madde 7 cumlesi §3.3.3.2'de TEK TILDE ile cizilir
  MZ2 CIZILI VARYANT (<del>) + OLUMLUYA CEVIRME — §4.8.3'te D-303 DUSTU hukmu
      <del>…</del> ile cizilip yerine "dogrulandı" yazilir

"YAKALANDI" yalniz kapi DUSTUYSE (ERROR degil, assert ile) ve secilen hedef testlerin
hepsi dustuyse yazilir. Kacis / uygulanamayan mutant / bozuk temiz kosum / geri yukleme
uyusmazligi cikis 1'dir.

KOSUM (depo kokunden; baska surec bu dosyalari duzenlerken KOSMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B -X utf8 \
      results/fdr_sprint_20260910/T244/mutasyon_t244.py
"""
import argparse
import hashlib
import re
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[3]
PY = sys.executable
TEST = "test_fdr_t244_ic_celiski.py"
CIKTI = Path(__file__).resolve().parent / "mutasyon_ciktisi.txt"

B3 = (KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md",)
B4 = (KOK / "FDR" / "BOLUM_4_TEST_FAALIYETLERI.md",)

T1 = "test_T1_uc_surecte_de_kodlu_yazili"
T2 = "test_T2_h1c_kosuldu_ve_gecti"
T3A = "test_T3_engine_sha_kayit_defteriyle"
T4 = "test_T4c_6_eylul_hucreleri_dosya_satirla"
T5A = "test_T5a_483_engine_olculdu_ve_dustu"
T6B = "test_T6b_durumlar_HIZALI"
T6C = "test_T6c_m04_m06_kismen_eski_deger_cizili"
T7 = "test_T7_cumle_iki_yerde_ve_CIZILMEMIS"
T8 = "test_T8_varyant_sayilari_artefakttan"
T3C = "test_T3c_d303_dustu_uc_yerde_de_olumluya_CEVRILMEMIS"
TC = "test_celiskili_ikinci_hukum_HICBIR_yuzeyde_yok"

DURUSTLUK = ("İkisi de rotanın lehinedir ve üretim kodunda karşılığı yoktur; "
             "**bu yüzden üretim sayıları sahaya göre İYİMSER ÜST SINIRDIR**")

# (ad, dosyalar, [(eski, yeni), ...], hedef testler)
MUTASYONLAR = [
    ("M1 madde1: §3.3.1.1.8 'acik kalemdir' cizgisi kaldirildi (eski hukum CANLI)", B3,
     [("**açık kalemdir** (`FDR/ACIK_KALEMLER.md`).~~",
       "**açık kalemdir** (`FDR/ACIK_KALEMLER.md`).")], (T1,)),
    ("M2 madde2: §3.3.4.1.7 H1c 'damgalanmadi' cizgisi kaldirildi", B3,
     [("H1b (kesin azalma). ~~H1c", "H1b (kesin azalma). H1c"),
      ("kendi kuralınca **açık** sayılır.~~", "kendi kuralınca **açık** sayılır.")], (T2,)),
    ("M3 madde3: kunye .engine sha'si defterden SAPTI (son hane 0 -> 1)", B3,
     [("`bb9bd8685a98a91947332c5b19b43f6c5631fb9c8ebcf611a9f75f6c05950300`",
       "`bb9bd8685a98a91947332c5b19b43f6c5631fb9c8ebcf611a9f75f6c05950301`")], (T3A,)),
    ("M4 madde4: §4.4 ESC kalibrasyonu hucresi 5 Eylul haline dondu", B4,
     [("~~ESC kalibrasyonu YAPILMADI;~~ → **6 Eylül'de yapıldı** (BEYAN; başarılı yordam "
       "D-428 §3: POWER1 çıkarılmış + USB passthrough + sonra pil → \"5'te 5\"). "
       "ESC künyesi ~~sahada **\"60 A V2\"** ×4 (plan 80 A) — BEYAN~~ → "
       "**Hobbywing Skywalker 60A V2** ×4, etiketten okundu (BEYAN, D-428 §1);",
       "ESC kalibrasyonu YAPILMADI; ESC künyesi sahada **\"60 A V2\"** ×4 (plan 80 A) — BEYAN;")],
     (T4,)),
    ("M5 madde5: §4.8.3 'Jetson'da .engine ile olculecektir' CANLI dondu", B4,
     [("~~**Jetson'da `.engine` ile ölçülecektir** (§4.13.1).~~",
       "**Jetson'da `.engine` ile ölçülecektir** (§4.13.1).")], (T5A,)),
    ("M6 madde6: §4.0 Y-4-M04 durumu YOK'a geri alindi (YONERGE ile celisir)", B4,
     [("| §4.4 | ~~YOK~~ → **KISMEN**", "| §4.4 | **YOK** ~~KISMEN~~")], (T6B, T6C)),
    ("M7 madde7: durustluk cumlesi §4.7'den SILINDI (yalniz Bolum 3'te kaldi)", B4,
     [(DURUSTLUK + " — sahada bu\n", "İkisi de rotanın lehinedir — sahada bu\n")], (T7,)),
    ("M8 madde8: §3.3.4.2.8 v2 HTAB engel orani artefakttan SAPTI (0,2380 -> 0,2400)", B3,
     [("| **v2 (alçak güneş + gölge)** | 0/15 | **0/15** | **0,2380** |",
       "| **v2 (alçak güneş + gölge)** | 0/15 | **0/15** | **0,2400** |")], (T8,)),
    ("MC CELISKILI IKINCI HUKUM: §4.8.3'e gevsetilmis ikinci D-303 esigi yazildi", B4,
     [("Eşik **gevşetilmedi**. Sonuç: **engine üretime alınmadı, uçuş `.pt` ile**",
       "Eşik **gevşetilmedi**. Gözden geçirilmiş kapı: ≤ 5/126 = **%3,97** → GEÇTİ. "
       "Sonuç: **engine üretime alınmadı, uçuş `.pt` ile**")], (T5A, TC)),
    ("MZ1 CIZILI VARYANT (tek tilde): madde7 cumlesi §3.3.3.2'de TEK TILDE ile cizildi", B3,
     [(DURUSTLUK, "~" + DURUSTLUK + "~")], (T7,)),
    ("MZ2 CIZILI VARYANT (<del>) + OLUMLUYA CEVIRME: §4.8.3 D-303 DUSTU -> dogrulandı", B4,
     [("| **3/126 = %2,38** | 🔴 **DÜŞTÜ** |",
       "| **3/126 = %2,38** | <del>🔴 **DÜŞTÜ**</del> doğrulandı |")], (T3C,)),
]

SATIRLAR = []


def yaz(metin):
    print(metin, flush=True)
    SATIRLAR.append(metin)
    CIKTI.write_text("\n".join(SATIRLAR) + "\n", encoding="utf-8")


def kos(hedefler=()):
    argv = [PY, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests", "-p", TEST]
    for hedef in hedefler:
        argv += ["-k", hedef]
    yaz("KOMUT: " + subprocess.list2cmdline(argv))
    p = subprocess.run(argv, cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1800)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    satirlar = [s for s in cikti.strip().splitlines() if s.strip()]
    son = satirlar[-1] if satirlar else "?"
    dusen = sorted(set(re.findall(r"^FAIL: (test_\w+)", cikti, re.M)))
    hatalar = re.findall(r"^ERROR: (.+)$", cikti, re.M)
    with CIKTI.with_suffix(".raw.txt").open("a", encoding="utf-8") as ham:
        ham.write("KOMUT: " + subprocess.list2cmdline(argv) + "\n" + cikti +
                  "\nEXIT={}\n\n".format(p.returncode))
    return p.returncode, (ran.group(1) if ran else "?"), son, dusen, hatalar


def uygula(dosyalar, ciftler, orijinal):
    for yol in dosyalar:
        metin = orijinal[yol].decode("utf-8")
        crlf = "\r\n" in metin
        n = metin.replace("\r\n", "\n")
        for eski, yeni in ciftler:
            sayi = n.count(eski)
            if sayi != 1:
                raise RuntimeError("{}: mutasyon metni {} kez bulundu (1 olmali): {!r}".format(
                    yol.name, sayi, eski[:70]))
            n = n.replace(eski, yeni, 1)
        yol.write_bytes((n.replace("\n", "\r\n") if crlf else n).encode("utf-8"))


def main():
    global CIKTI
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hedef-testler", action="store_true",
                    help="Her mutantta yalniz on kayitli hedef testleri kos.")
    ap.add_argument("--yalniz", action="append", default=[], help="Mutant adinin oneki.")
    ap.add_argument("--cikti", type=Path, default=CIKTI)
    args = ap.parse_args()
    CIKTI = args.cikti.resolve()
    CIKTI.parent.mkdir(parents=True, exist_ok=True)
    mutantlar = [m for m in MUTASYONLAR if not args.yalniz or
                 any(m[0].startswith(onek) for onek in args.yalniz)]
    if not mutantlar:
        ap.error("Secilen mutant yok")
    tum = sorted({y for _a, ds, _c, _h in mutantlar for y in ds})
    orijinal = {y: y.read_bytes() for y in tum}
    sha0 = {y: hashlib.sha256(b).hexdigest() for y, b in orijinal.items()}
    yaz("# T244 mutasyon ciktisi · {} · {}".format(
        time.strftime("%Y-%m-%d %H:%M:%S"), Path(PY).name))
    kod, ran, son, dusen, hatalar = kos()
    yaz("BASLANGIC TEMIZ: cikis={} ran={} son={!r} dusen={} hatalar={}".format(
        kod, ran, son, dusen, hatalar))
    if kod != 0 or ran in ("0", "?"):
        yaz("DURDU: mutasyonsuz kapi once gecmeli.")
        return 1
    yakalanan = uygulanamayan = 0
    try:
        for ad, dosyalar, ciftler, hedefler in mutantlar:
            try:
                uygula(dosyalar, ciftler, orijinal)
            except RuntimeError as exc:
                uygulanamayan += 1
                yaz("{}: UYGULANAMADI — {}".format(ad, exc))
                for y in dosyalar:
                    y.write_bytes(orijinal[y])
                continue
            try:
                kod, ran, son, dusen, hatalar = kos(hedefler if args.hedef_testler else ())
            finally:
                for y in dosyalar:
                    y.write_bytes(orijinal[y])
            durum = {h: ("DUSTU" if h in dusen else "GECTI") for h in hedefler}
            tuttu = (kod != 0 and not hatalar and all(v == "DUSTU" for v in durum.values())
                     and (not args.hedef_testler or ran == str(len(hedefler))))
            yakalanan += 1 if tuttu else 0
            yaz("{}: cikis={} ran={} son={!r} -> {}; hedef={}; dusen={}; hatalar={}".format(
                ad, kod, ran, son, "YAKALANDI" if tuttu else "KACTI", durum, dusen, hatalar))
    finally:
        for y, b in orijinal.items():
            y.write_bytes(b)
    esit = all(hashlib.sha256(y.read_bytes()).hexdigest() == sha0[y] for y in tum)
    yaz("geri yukleme sha esit: {} ({})".format(
        esit, ", ".join("{}={}".format(y.relative_to(KOK).as_posix(), sha0[y][:12]) for y in tum)))
    yaz("OZET: {}/{} mutasyon TUM hedef testleriyle yakalandi; uygulanamayan {}".format(
        yakalanan, len(mutantlar), uygulanamayan))
    kod, ran, son, dusen, hatalar = kos()
    yaz("TEMIZ KOSUM (mutasyonsuz): cikis={} ran={} son={!r} dusen={}".format(
        kod, ran, son, dusen))
    CIKTI.write_text("\n".join(SATIRLAR) + "\n", encoding="utf-8")
    return 0 if esit and yakalanan == len(mutantlar) and uygulanamayan == 0 and kod == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
