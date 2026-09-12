#!/usr/bin/env python3
"""T235-B/D mutasyon kosucusu — her mutasyon TEK TEK uygulanir, hedef testler kosulur,
dosya once `git checkout --` ile kanonik bicime dondurulur, sonra icerigin `git show HEAD:<yol>`
ciktisiyla ve mutasyondan ONCEKI baytlarla (satir sonu disinda) ortustugu DOGRULANIR.
Ayrica `git status --porcelain <yol>` bos olmali. Ham cikti: `mutasyon_ciktisi.txt`.

Depo KOKU `__file__`'dan turetilir — betik hangi calisma agacindan kosulursa O agaci sinar
(baska bir agaci yanlislikla mutasyona ugratmaz).

🔴 `__pycache__` tuzagi: bir mutasyon ayni BOYUTTA metin yaziyorsa ve ayni saniye icinde
kosuluyorsa, `.pyc` gecerlilik olcutu (kaynak mtime + boyut) degismedigi icin Python
ONBELLEKTEN kosar ve mutasyon "kacmis" gorunur. Bu tuzak bu iste bir kez gerceklesti
(M3 "A1 x aynasi" ilk turda KACTI gorundu, elle kosunca 7 test dusuyordu). Her test
kosumundan once codes/tests/simulation/jetson_paket altindaki `.pyc`'ler silinir.
Depoda IZLENEN .pyc dosyalari vardir (models/...) — temizlik yalniz bu dort agaci tarar.

Kullanim (ciktiyi AGAC DISINA yaz; dogrudan `mutasyon_ciktisi.txt`'ye yonlendirmek calisma
agacini kirletir ve betigin kendi temizlik denetimini dusurur):
    O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 \\
        results/fdr_sprint_20260910/H1/t235/mutasyon/mutasyon_t235bd.py > %TEMP%\\mut.txt 2>&1
    copy %TEMP%\\mut.txt results\\fdr_sprint_20260910\\H1\\t235\\mutasyon\\mutasyon_ciktisi.txt
"""
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[5]
PY = r"O:\navitas-local-train\venv\Scripts\python.exe"

KS = "codes/karar_sozlesmesi.py"
TZ = "simulation/mujoco/t235_etiket_tezgahi.py"
OK = "results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md"
RM = "results/fdr_sprint_20260910/H1/t235/olcum/README.md"
DJ = "results/fdr_sprint_20260910/H1/t235/olcum/kapi_duyarliligi.json"

# (etiket, yol, eski, yeni, testleri secen -k anahtarlari)
MUTASYONLAR = [
    # ── ON_KAYIT SS6 mutasyon hedefleri (uretim kodu) ─────────────────────────
    ("M1  W/6 -> W/3", KS, "return w / (2.0 * SERIT_SAYISI)", "return w / (1.0 * SERIT_SAYISI)",
     "A0AlanSeritKarari A1KbhSeritKarari OnKayitKilitleri Sabitler"),
    ("M2  A0 x aynasi", KS, "_np.where(xs < sol, 1, _np.where(xs <= sag, 2, 3))",
     "_np.where(xs < sol, 3, _np.where(xs <= sag, 2, 1))", "A0AlanSeritKarari"),
    ("M3  A1 x aynasi (kbh sag)", KS, "sag = (_np.asarray(px, dtype=float) - cx) * m",
     "sag = (cx - _np.asarray(px, dtype=float)) * m", "A1KbhDonustur TezgahKameraModeli"),
    ("M4  kerteriz (beta) isareti", KS, "k = math.radians(kerteriz)",
     "k = math.radians(-kerteriz)", "A1KbhDonustur TezgahKameraModeli"),
    ("M5  montaj yaw isareti", KS, "t = math.radians(hdg + montaj)",
     "t = math.radians(hdg - montaj)", "A1KbhDonustur TezgahKameraModeli"),
    ("M6  hiz kapisi kaldirildi", KS,
     "return v <= ALAN_ETIKETI_HIZ_ESIGI_M_S and yas <= ALAN_ETIKETI_TAZELIK_S",
     "return True", "HizKapisi"),
    ("M7  hiz esigi 1,0 -> 2,0 m/s", KS, "ALAN_ETIKETI_HIZ_ESIGI_M_S = 1.0",
     "ALAN_ETIKETI_HIZ_ESIGI_M_S = 2.0", "HizKapisi Sabitler OnKayitKilitleri"),
    # ── tezgah: on kayitli esik/tohum/karar kurali ────────────────────────────
    ("M8  tezgah kapi esigi %99 -> %98", TZ, "KAPI_ORAN_YUZDE = 99.0", "KAPI_ORAN_YUZDE = 98.0",
     "OnKayitKilitleri KapiVeHukumMantigi TezgahYenidenUretim"),
    ("M9  KARE fark payi 0,5 -> 5,0 puan", TZ, "KAPI_KARE_FARK_PUAN = 0.5",
     "KAPI_KARE_FARK_PUAN = 5.0", "OnKayitKilitleri KapiVeHukumMantigi TezgahYenidenUretim"),
    ("M10 tohum 20260910 -> 20260911", TZ, "TOHUM = 20260910", "TOHUM = 20260911",
     "OnKayitKilitleri TezgahYenidenUretim"),
    ("M11 kosul1 bos nominal kumesi GECER (fail-open)", TZ,
     'k1 = bool(k1_sat) and all(s["gecti"] for s in k1_sat)',
     'k1 = all(s["gecti"] for s in k1_sat)', "KapiVeHukumMantigi"),
    ("M12 karar kurali: A1 gecmeden T235-C acilir", TZ,
     '"t235c_poz_kolu_acilir": bool((not t_a0) and t_a1),',
     '"t235c_poz_kolu_acilir": bool(not t_a0),', "TezgahYenidenUretim"),
    # NOT: "bugunku_hukum" kaynagini TAM tablodan alt kumeye cevirmek bir mutasyon olarak
    # LISTELENMEDI: bu veriyle iki kapi ayni ciktigi icin (tam_tablo_kapisiyla_ayni = true,
    # test bunu ONERMEYLE dogruluyor) fark GOZLENEMEZ. Veriyle yakalanamayan bir degisikligi
    # "yakalandi" diye yazmak da, kacti diye saymak da yaniltici olurdu.
    # ── belge kilitleri: cizili/varyant/celiski ile delme denemeleri (D-453) ──
    ("M13 ON_KAYIT esigi cizilip gevsetildi (~~ ~~)", OK, "**\u2265 %99,0**",
     "~~**\u2265 %99,0**~~ **\u2265 %98,0**", "OnKayitKilitleri"),
    ("M14 ON_KAYIT esigi <del> ile gevsetildi", OK, "**\u2265 %99,0**",
     "<del>**\u2265 %99,0**</del> **\u2265 %98,0**", "OnKayitKilitleri"),
    ("M15 ON_KAYIT tohumu tek tilde ile degistirildi", OK, "tohum 20260910",
     "tohum ~20260910~ 20260911", "OnKayitKilitleri"),
    ("M16 ON_KAYIT'a celisen ikinci SS2 bolumu eklendi", OK,
     "## 3. Uygulama testi T235-K1",
     "## 2. Ek \u00f6l\u00e7\u00fct\n- **Kap\u0131:** do\u011fru oran\u0131 **\u2265 %95,0** yeterlidir.\n\n"
     "## 3. Uygulama testi T235-K1", "OnKayitKilitleri"),
    ("M17 ON_KAYIT karar kurali: A1 kosulsuz acilir", OK,
     "A0 d\u00fc\u015fer A1 ge\u00e7erse A1 yaln\u0131z T235-C poz kolu",
     "A0 d\u00fc\u015fer A1 ge\u00e7erse A1 ko\u015fulsuz a\u00e7\u0131l\u0131r; T235-C poz kolu", "OnKayitKilitleri"),
    ("M18 README hukmu cizilip GECTI yazildi", RM, "**A0: DUSTU**",
     "~~**A0: DUSTU**~~ **A0: GECTI**", "TezgahYenidenUretim"),
    ("M19 README'de T235-C ACILIR yapildi", RM,
     "ba\u011flanmas\u0131) A\u00c7ILMAZ**", "ba\u011flanmas\u0131) A\u00c7ILIR**", "TezgahYenidenUretim"),
    ("M20 README D-457 satiri elle 16:9 -> A0", RM,
     "| 16:9 | 16:9@40m | \u2717 | \u2713 | **DUSTU** | **KARE** |",
     "| 16:9 | 16:9@40m | \u2717 | \u2713 | **GECTI** | **A0** |", "TezgahYenidenUretim"),
    ("M21 duyarlilik JSON'unda 16:9 elle A0 yapildi", DJ,
     '"yapilandirma": "16:9@40m",\n    "A0": "DUSTU",',
     '"yapilandirma": "16:9@40m",\n    "A0": "GECTI",', "TezgahYenidenUretim"),
    ("M22 duyarlilik JSON'unda kapi disi hucre hukmu tasidi denildi", DJ,
     '"tam_tablo_kapisiyla_ayni": true', '"tam_tablo_kapisiyla_ayni": false',
     "TezgahYenidenUretim"),
]


def kos(args):
    return subprocess.run(args, cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def duz(b: bytes) -> bytes:
    """Satir sonu farkini yok sayan bayt karsilastirmasi (calisma kopyasi autocrlf ile CRLF)."""
    return b.replace(b"\r\n", b"\n")


def temiz_mi(yol=None):
    """IZLENEN dosyalarda hicbir fark kalmamali (satir sonu dahil). Izlenmeyen kosum
    artifaktlari (results/prova/...) mutasyon degildir, sayilmaz."""
    r = kos(["git", "status", "--porcelain", "--untracked-files=no"]
            + (["--", yol] if yol else []))
    return r.stdout.strip()


def geri_yukle(yol, once_bayt):
    r = kos(["git", "checkout", "--", yol])
    assert r.returncode == 0, r.stderr
    blob = subprocess.run(["git", "show", "HEAD:" + yol], cwd=KOK, capture_output=True)
    assert blob.returncode == 0, blob.stderr
    simdi = (KOK / yol).read_bytes()
    assert duz(simdi) == duz(blob.stdout), f"{yol}: HEAD ile ayrisik"
    assert duz(simdi) == duz(once_bayt), f"{yol}: mutasyon oncesi baytlarla ayrisik"


def pycache_temizle():
    for alt in ("codes", "tests", "simulation", "jetson_paket"):
        for d in (KOK / alt).rglob("__pycache__"):
            for f in d.glob("*.pyc"):
                f.unlink()


def testi_kos(secici):
    pycache_temizle()
    args = [PY, "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
            "-p", "test_t235_alan_etiketi.py"]
    for k in secici.split():
        args += ["-k", k]
    return kos(args)


def main():
    print("DEPO KOKU:", KOK)
    kacan = []
    kirli = temiz_mi()
    assert not kirli, "calisma agaci temiz degil:\n" + kirli
    for etiket, yol, eski, yeni, secici in MUTASYONLAR:
        once_bayt = (KOK / yol).read_bytes()
        s = (KOK / yol).read_text(encoding="utf-8")
        if s.count(eski) != 1:
            print(f"[ATLANDI  ] {etiket}: hedef metin {s.count(eski)} kez bulundu")
            kacan.append(etiket + " (hedef bulunamadi)")
            continue
        (KOK / yol).write_text(s.replace(eski, yeni), encoding="utf-8", newline="\n")
        r = testi_kos(secici)
        dusen = r.returncode != 0
        son = (r.stderr or "").strip().splitlines()
        print(f"[{'YAKALANDI' if dusen else 'KACTI    '}] {etiket}  -> {son[-1] if son else ''}",
              flush=True)
        if not dusen:
            kacan.append(etiket)
        geri_yukle(yol, once_bayt)
        kirli = temiz_mi(yol)
        assert not kirli, f"geri yukleme basarisiz ({etiket}): {kirli}"
    print()
    print("TOPLAM", len(MUTASYONLAR), "mutasyon; KACAN", len(kacan))
    for k in kacan:
        print("  KACTI:", k)
    kirli = temiz_mi()
    print("KOSUM SONU calisma agaci:", kirli if kirli else "TEMIZ")
    return 1 if kacan else 0


if __name__ == "__main__":
    sys.exit(main())
