"""Akis diyagrami (.mmd) dugumlerindeki dosya:satir atiflarini koda gore tazeler.

KAPSAM KORUMASI (AKIS-D, D-448 (6)). Eski surum etiket metnini eski satira EN
YAKIN yerde ariyordu; buyuk bir ekleme fonksiyonlari kaydirinca dugum BASKA
fonksiyondaki ayni metne baglaniyordu (T227: a06/a15/a17/... 12 dugum) ve
dogrulayici yalniz metni denetledigi icin "TUM DUGUMLER TUTTU" diyordu. Simdi:

  1. Dugumun ESKI satiri taban surumdeki dosyada (git show <taban>:<yol>) metni
     tasimali: tam satir; degilse +-SATIR_TOLERANSI icinde en yakin (esitlikte
     hata). Tasimiyorsa "TABANDA TUTMUYOR" — .mmd bu tabana gore turetilmemis;
     dogru --taban'i verin (tahmin edilmez).
  2. O satirin ast ile en icteki def/class nitelikli adi (qualname) bulunur
     (scripts/akis_diyagram_dogrula.py KapsamHaritasi — iki arac tek kural).
  3. Yeni eslesme YALNIZ calisma agacindaki AYNI qualname'in kendi satirlarinda
     (ic ice tanimlar haric) aranir. Kapsam yoksa ya da metin kapsamda yoksa
     "KAPSAM ICINDE BULUNAMADI" (baska fonksiyona bakilmaz). Kapsamda birden cok
     aday → kapsam basina gore goreli konumu eski konuma en yakin olan; esitlikte
     "ESITLIK" hatasi. Ayni ad birden cok tanimliysa (property setter) kacinci
     tanim oldugu korunur; tanim sayisi degistiyse "KAPSAM BELIRSIZ".
  4. Hata veren dugum DEGISTIRILMEZ; cozulen dugumler yazilir. Basliktaki
     "koddan turetildi <commit> <tarih>" yalniz dosyada hata yoksa guncellenir.

Alt-grafik basliklari (subgraph ID["..."]) de dugumdur ve ayni kuralla tazelenir.

Kullanim:
  python scripts/akis_satir_tazele.py <depo_koku> <mmd...> [--taban REF] [--kuru]
    --taban  eski satirlarin ait oldugu git-ref (varsayilan HEAD). Kod degisikligi
             commit'lenmemisken HEAD dogrudur; commit'lendiyse .mmd'nin
             turetildigi commit'i verin.
    --kuru   hicbir dosya yazilmaz, yalniz rapor.
Cikis: 0 tum dugumler cozuldu · 1 en az bir dugum cozulemedi · 2 kullanim/taban hatasi
"""
import argparse
import datetime
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

_sp = importlib.util.spec_from_file_location(
    "_akis_dogrula_kapsam", Path(__file__).resolve().parent / "akis_diyagram_dogrula.py")
D = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(D)

SATIR_TOLERANSI = D.SATIR_TOLERANSI
DUGUM = re.compile(
    r'^(\s*(?:subgraph\s+)?[a-zA-Z0-9_]+)([\[{(])"(.*)<br/>([^"<]+?):(\d+)(?:-(\d+))?"([\]})])\s*$')


def parcalar_coz(etiket):
    """Etiket (dosya:satir haric) → varliklari cozulmus metin parcalari."""
    return [D.varlik_coz(p).strip() for p in D.RE_BR.split(etiket)]


def _satir_eslesir(satir, parca, def_kipi):
    if def_kipi:
        ad = D.RE_DEF.match(parca).group(1).split(".")[-1]
        return re.match(r"\s*(?:async\s+)?def\s+" + re.escape(ad) + r"\(", satir) is not None
    hedef = D._sikistir(parca)
    return bool(hedef) and hedef in D._sikistir(satir)


def blok_eslesir(satirlar, n, parcalar, def_kipi=False):
    """n. satirdan (1-tabanli) baslayan ARDISIK satirlar parcalari tasiyor mu."""
    if n < 1 or n + len(parcalar) - 1 > len(satirlar):
        return False
    return all(_satir_eslesir(satirlar[n - 1 + k], p, def_kipi and k == 0)
               for k, p in enumerate(parcalar))


def adaylari_bul(satirlar, aday_satirlari, parcalar):
    """Metin eslesmesi; hic yoksa ve etiket `def ad()` ise tanim satiri (eski oncelik)."""
    adaylar = [n for n in aday_satirlari if blok_eslesir(satirlar, n, parcalar)]
    if not adaylar and len(parcalar) == 1 and D.RE_DEF.match(parcalar[0]):
        adaylar = [n for n in aday_satirlari if blok_eslesir(satirlar, n, parcalar, True)]
    return adaylar


def tabanda_bul(satirlar, parcalar, eski, tolerans=SATIR_TOLERANSI):
    """Eski satirin tabandaki karsiligi → (satir, None) ya da (None, hata)."""
    pencere = range(max(1, eski - tolerans), min(len(satirlar), eski + tolerans) + 1)
    adaylar = adaylari_bul(satirlar, pencere, parcalar)
    if eski in adaylar:
        return eski, None
    if not adaylar:
        return None, (f"TABANDA TUTMUYOR: satir {eski}+-{tolerans} metni tasimiyor "
                      "(.mmd bu tabandan turetilmemis — dogru --taban'i verin)")
    sirali = sorted(adaylar, key=lambda n: (abs(n - eski), n))
    if len(sirali) > 1 and abs(sirali[0] - eski) == abs(sirali[1] - eski):
        return None, f"TABANDA ESITLIK: {sirali[0]} ve {sirali[1]} eski satira esit uzak"
    return sirali[0], None


def dugumu_coz(kaynak, taban, dosya, eski, parcalar):
    """→ (yeni_satir, kapsam, None) ya da (None, kapsam|None, hata metni)."""
    ds_c = kaynak.satirlar(dosya)
    if ds_c is None:
        return None, None, "DOSYA YOK (calisma agaci)"
    ds_t = kaynak.satirlar(dosya, taban)
    if ds_t is None:
        return None, None, "TABANDA DOSYA YOK"
    t_satir, hata = tabanda_bul(ds_t, parcalar, eski)
    if hata:
        return None, None, hata
    try:
        ht, hc = kaynak.harita(dosya, taban), kaynak.harita(dosya)
    except (SyntaxError, ValueError) as e:
        return None, None, f"AST HATASI ({e.__class__.__name__}: {e})"
    kt = ht.kapsam(t_satir)
    q, adi = kt[0], D.kapsam_metni(kt)
    if hc.sayi(q) == 0:
        return None, kt, f"KAPSAM ICINDE BULUNAMADI: kapsam [{adi}] calisma agacinda yok"
    if hc.sayi(q) != ht.sayi(q):
        return None, kt, (f"KAPSAM BELIRSIZ: [{q}] adli tanim sayisi degisti "
                          f"(taban {ht.sayi(q)}, calisma {hc.sayi(q)})")
    adaylar = adaylari_bul(ds_c, hc.satirlari(kt), parcalar)
    if not adaylar:
        return None, kt, f"KAPSAM ICINDE BULUNAMADI: metin [{adi}] icinde yok"
    beklenen = hc.baslangic(kt) + (t_satir - ht.baslangic(kt))
    sirali = sorted(adaylar, key=lambda n: (abs(n - beklenen), n))
    if len(sirali) > 1 and abs(sirali[0] - beklenen) == abs(sirali[1] - beklenen):
        return None, kt, (f"ESITLIK: [{adi}] icinde {sirali[0]} ve {sirali[1]} "
                          f"beklenen {beklenen} satirina esit uzak")
    return sirali[0], kt, None


def mmd_tazele(mmd, kaynak, taban, kuru, head, tarih):
    """Bir .mmd → (degisen, hatalar). kuru degilse dosya yazilir."""
    ham = mmd.read_bytes()
    crlf = b"\r\n" in ham
    satirlar = ham.decode("utf-8").replace("\r\n", "\n").split("\n")
    degisen, hatalar = [], []
    for k, s in enumerate(satirlar):
        m = DUGUM.match(s)
        if not m:
            continue
        on, ac, etiket, dosya, sat, sat2, kapa = m.groups()
        kimlik, eski = on.split()[-1], int(sat)
        parcalar = parcalar_coz(etiket)
        yeni, kt, hata = dugumu_coz(kaynak, taban, dosya, eski, parcalar)
        if hata:
            hatalar.append(f"{kimlik}: {dosya}:{sat} '{' / '.join(parcalar)[:60]}' — {hata}")
            continue
        if yeni != eski:
            yeni_sat2 = f"-{int(sat2) + yeni - eski}" if sat2 else ""
            satirlar[k] = f'{on}{ac}"{etiket}<br/>{dosya}:{yeni}{yeni_sat2}"{kapa}'
            degisen.append(f"{kimlik}: {dosya}:{eski} -> {yeni}  [{D.kapsam_metni(kt)}]")
    if not kuru:
        if not hatalar and satirlar and satirlar[0].startswith("%% koddan turetildi"):
            satirlar[0] = f"%% koddan turetildi {head} {tarih}"
        mmd.write_bytes(("\r\n" if crlf else "\n").join(satirlar).encode("utf-8"))
    return degisen, hatalar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("kok", type=Path, help="depo koku")
    ap.add_argument("mmd", type=Path, nargs="+", help="tazelenecek .mmd dosyalari")
    ap.add_argument("--taban", default="HEAD", metavar="GIT_REF",
                    help="eski satirlarin ait oldugu git-ref (varsayilan HEAD)")
    ap.add_argument("--kuru", action="store_true", help="dosya yazma, yalniz rapor")
    args = ap.parse_args(argv)
    kok = args.kok.resolve()
    sha = D.taban_ref_coz(args.taban, kok)
    if sha is None:
        print(f"TABAN GECERSIZ: {args.taban!r} bir commit degil ({kok})")
        return 2
    eksik = [p for p in args.mmd if not p.is_file()]
    if eksik:
        for p in eksik:
            print(f"DOSYA YOK: {p}")
        return 2
    head = subprocess.run(["git", "-C", str(kok), "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True).stdout.strip()
    tarih = datetime.date.today().isoformat()
    kaynak = D.KapsamKaynagi(kok)
    fiil = "tazelenecek (KURU — dosya yazilmadi)" if args.kuru else "tazelendi"
    print(f"taban: {args.taban} = {sha[:12]}")
    toplam_degisen = toplam_hata = 0
    for p in args.mmd:
        degisen, hatalar = mmd_tazele(p, kaynak, sha, args.kuru, head, tarih)
        toplam_degisen += len(degisen)
        toplam_hata += len(hatalar)
        print(f"{p.name}: {len(degisen)} dugum {fiil}; cozulemeyen {len(hatalar)}")
        for d in degisen:
            print(f"   {d}")
        for h in hatalar:
            print(f"   HATA {h}")
    print(f"SONUC: {toplam_degisen} dugum {fiil} · {toplam_hata} hata")
    return 1 if toplam_hata else 0


if __name__ == "__main__":
    raise SystemExit(main())
