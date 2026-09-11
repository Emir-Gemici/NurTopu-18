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
     aday → def/class satirina (capa; dekoratorler HARIC) gore goreli konumu eski
     konuma en yakin olan; esitlikte "ESITLIK" hatasi. Ayni ad birden cok
     tanimliysa (property setter) kacinci tanim oldugu korunur; tanim sayisi
     degistiyse "KAPSAM BELIRSIZ".
  4. Hata veren dugum DEGISTIRILMEZ; cozulen dugumler yazilir. Basliktaki
     "koddan turetildi <commit> <tarih>" yalniz dosyada hata ve taban uyarisi
     yoksa guncellenir.

TABAN SUPHESI (AKIS-D2, curutucu KUSUR-1 ve KUSUR-A). .mmd satirlari her zaman
secilen tabana gore DEGILDIR: kod commit'lenip .mmd tazelenmediyse bir dugumun
satiri O SATIRI YAZAN commit'e (L_n) gore; .mmd onceki bir tazelemeyle (ya da
elle) degistiyse o dugumun satiri calisma agacina gore olabilir. fd65b427 bu
durumda varsayilan HEAD ile dugumu SESSIZCE baska fonksiyonda birakiyordu
(cikis 0, baslik yeniden damgali). Simdi her dugum icin ikinci bir makul taban
alinir: satiri tabandaki .mmd'de AYNEN duran dugum icin L_n (L_n != taban ise),
duruyor olmayan dugum icin calisma agaci.
🔴 L_n dosya duzeyinde DEGIL, `git blame` ile DUGUM BASINA alinir (AKIS-D2 2.
RED, KUSUR-A): .mmd kod commit'inden SONRA baska bir nedenle (yorum satiri, elle
eklenen baska dugum) commit'lenirse "dosyaya dokunan son commit" tabanin kendisi
olur, ikinci taban dusuyor ve kayma yine sessiz kaliyordu — karsi-ornek A (dugum
f1:8) → C (basa f3, kod commit'i) → D (.mmd'ye yalniz '%% not'): varsayilan
tazele cikis 0 verip n1'i f3'te birakiyor, basligi yeniden damgaliyordu.
Dugumun dosyasi iki tabanda ayniysa sonuc ozdestir (satir kaydirmayan kod
degisikligi supheli DEGIL); degilse iki tabanda sonuc (yeni satir / cozulemedi)
hesaplanir ve farkliysa:
  --taban VERILMEDIYSE  "TABAN SUPHELI": hicbir dosya yazilmaz, cikis 2
                        (tahmin edilmez; tabani acikca verin);
  --taban VERILDIYSE    "TABAN UYARISI" basilir, tazeleme surer, o .mmd'nin
                        basligi guncellenmez.
(AKIS-D2 2026-09-10: onceki surumun beyani "kod commit'lendiyse TABANDA
TUTMUYOR ile guvenli tarafta durur" diyordu — olculmemisti ve YANLISTI; curutucu
karsi-ornekte cikis 0 ve sessiz f3 baglantisi olctu.)

Alt-grafik basliklari (subgraph ID["..."]) de dugumdur ve ayni kuralla tazelenir.
TEK DESEN (AKIS-D2 EK, T226-D amelesi bulgusu): eski surumun kendi dugum deseni
`subgraph …["def …<br/>dosya:N"]` basliklarini yakalamiyordu (T226-D'de 5 baslik elle
AST ile tazelendi); fd65b427 `subgraph` onekini ekledi ama desen hala dogrulayicininkinden
dardi (`ID ["` bosluklu bicim, `<br>` / `<br />` ayraci). Simdi dugum TANIMI
akis_diyagram_dogrula.RE_DUGUM ile yapilir — iki arac yapi geregi AYNI dugum kumesini
gorur; yalniz etiketin sonundaki dosya:satir[-satir] parcasi yerinde degistirilir, satirin
geri kalani (bicim, bosluk, ayrac) BAYT-ES korunur.

Kullanim:
  python scripts/akis_satir_tazele.py <depo_koku> <mmd...> [--taban REF] [--kuru]
    --taban  eski satirlarin ait oldugu git-ref. Verilmezse HEAD + taban suphesi
             ENGELI (supheli → cikis 2); verilirse yalniz uyari.
    --kuru   hicbir dosya yazilmaz, yalniz rapor.
Cikis: 0 tum dugumler cozuldu · 1 en az bir dugum cozulemedi · 2 kullanim/taban
hatasi ya da TABAN SUPHELI
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
# Etiketin son parcasi: <br…>dosya:satir[-satir] (dosya:satir etiketin sonunda olmali).
RE_ATIF = re.compile(r'(<br\s*/?>)([^"<]+?):(\d+)(?:-(\d+))?$')


def dugum_ayikla(satir):
    """.mmd satiri → (kimlik, etiket, dosya, satir, satir2|None, (bas, son)) ya da None.

    Dugum tanimi akis_diyagram_dogrula.RE_DUGUM ile (TEK DESEN — AKIS-D2 EK): alt-grafik
    basliklari, `ID ["` bosluklu bicim, `<br>`/`<br/>`/`<br />`. Acilis/kapanis uyusmayan
    satir dogrulayicida hata, burada dugum DEGIL. etiket: dosya:satir'dan onceki metin;
    (bas, son): satir numarasi metninin satir icindeki yeri (yerinde degisim icin).
    """
    m = D.RE_DUGUM.match(satir)
    if not m:
        return None
    _, kimlik, sekil, etiket, kapanis = m.groups()
    if (sekil == '["') != (kapanis == '"]'):
        return None
    a = RE_ATIF.search(etiket)
    if not a:
        return None
    ofs = m.start(4)
    return (kimlik, etiket[:a.start()], a.group(2), int(a.group(3)), a.group(4),
            (ofs + a.start(3), ofs + a.end()))


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
    """taban: git-ref ya da None (calisma agaci; taban suphesi icin)
    → (yeni_satir, kapsam, None) ya da (None, kapsam|None, hata metni)."""
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
    beklenen = hc.capa(kt) + (t_satir - ht.capa(kt))
    sirali = sorted(adaylar, key=lambda n: (abs(n - beklenen), n))
    if len(sirali) > 1 and abs(sirali[0] - beklenen) == abs(sirali[1] - beklenen):
        return None, kt, (f"ESITLIK: [{adi}] icinde {sirali[0]} ve {sirali[1]} "
                          f"beklenen {beklenen} satirina esit uzak")
    return sirali[0], kt, None


def dugum_satirlari(satirlar):
    """.mmd satirlari → (indeks, satir, dugum_ayikla sonucu): yalniz dosya:satir tasiyan
    dugumler (alt-grafik basliklari dahil)."""
    for k, s in enumerate(satirlar):
        a = dugum_ayikla(s)
        if a:
            yield k, s, a


def _sonuc_metni(sonuc):
    yeni, kt, hata = sonuc
    if hata:
        return "cozulemedi (" + hata.split(":")[0] + ")"
    return f"{yeni} [{D.kapsam_metni(kt)}]"


def taban_suphesi(mmd, kok, kaynak, sha):
    """Sonucu secilen tabana BAGLI dugumler → [rapor]; bos liste = suphe yok (AKIS-D2).

    Dugum satiri tabandaki .mmd'de AYNEN varsa satir O SATIRI YAZAN commit'e (L_n,
    `git blame`) gore yazilmistir → ikinci makul taban L_n (L_n != sha ise). Yoksa
    (onceki tazeleme, elle duzeltme, .mmd tabanda yok) → ikinci makul taban calisma
    agaci. 🔴 L_n dosya duzeyinde alinmaz (KUSUR-A): .mmd kod commit'inden sonra
    baska bir nedenle commit'lenince dosya duzeyi taban sha'ya esitlenip dusuyordu.
    Dugumun dosyasi ikinci tabanda sha'dakiyle ayniysa sonuc ozdestir; degilse iki
    tabanda dugumu_coz sonucu (yeni satir ya da cozulemedi) karsilastirilir.
    """
    try:
        goreli = Path(mmd).resolve().relative_to(kok).as_posix()
    except ValueError:
        goreli = None
    mmd_taban = D.taban_icerigi(kok, sha, goreli) if goreli else None
    kokenler = D.satir_kokenleri(kok, sha, goreli) if mmd_taban is not None else {}
    W = (None, "calisma agaci (dugum satiri tabandaki .mmd'de yok)")
    taban_dugum = {}
    if mmd_taban is not None:
        for k, s, a in dugum_satirlari(D.satirlara_bol(mmd_taban)):
            taban_dugum.setdefault((a[0], s.strip()), k + 1)
    ham = Path(mmd).read_bytes().decode("utf-8-sig")
    supheler = []
    for _, s, (kimlik, etiket, dosya, eski, _, _) in dugum_satirlari(D.satirlara_bol(ham)):
        taban_no = taban_dugum.get((kimlik, s.strip()))
        koken = kokenler.get(taban_no) if taban_no is not None else None
        if taban_no is None:
            aday = W
        elif koken is not None and koken != sha:
            aday = (koken, f"{koken[:7]} (dugum satirinin koken commit'i)")
        else:
            aday = None
        if aday is None:
            continue
        ref, ad = aday
        if kaynak.satirlar(dosya, ref) == kaynak.satirlar(dosya, sha):
            continue                                      # ayni kod → ayni sonuc
        parcalar = parcalar_coz(etiket)
        secilen = dugumu_coz(kaynak, sha, dosya, eski, parcalar)
        diger = dugumu_coz(kaynak, ref, dosya, eski, parcalar)
        if diger[0] != secilen[0]:
            supheler.append(f"{Path(mmd).name}: {kimlik}: {dosya}:{eski} — sonuc tabana bagli: "
                            f"secilen taban {sha[:7]} → {_sonuc_metni(secilen)} · {ad} → "
                            f"{_sonuc_metni(diger)}")
    return supheler


def mmd_tazele(mmd, kaynak, taban, kuru, head, tarih, damga=True):
    """Bir .mmd → (degisen, hatalar). kuru degilse dosya yazilir; baslik yalniz hata
    yoksa ve damga (taban uyarisi yok) ise guncellenir."""
    ham = mmd.read_bytes()
    crlf = b"\r\n" in ham
    satirlar = ham.decode("utf-8").replace("\r\n", "\n").split("\n")
    degisen, hatalar = [], []
    for k, s, (kimlik, etiket, dosya, eski, sat2, (bas, son)) in list(dugum_satirlari(satirlar)):
        parcalar = parcalar_coz(etiket)
        yeni, kt, hata = dugumu_coz(kaynak, taban, dosya, eski, parcalar)
        if hata:
            hatalar.append(f"{kimlik}: {dosya}:{eski} '{' / '.join(parcalar)[:60]}' — {hata}")
            continue
        if yeni != eski:
            yeni_sat2 = f"-{int(sat2) + yeni - eski}" if sat2 else ""
            satirlar[k] = s[:bas] + f"{yeni}{yeni_sat2}" + s[son:]     # yalniz sayi; bicim ayni
            degisen.append(f"{kimlik}: {dosya}:{eski} -> {yeni}  [{D.kapsam_metni(kt)}]")
    if not kuru:
        if not hatalar and damga and satirlar and satirlar[0].startswith("%% koddan turetildi"):
            satirlar[0] = f"%% koddan turetildi {head} {tarih}"
        mmd.write_bytes(("\r\n" if crlf else "\n").join(satirlar).encode("utf-8"))
    return degisen, hatalar


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("kok", type=Path, help="depo koku")
    ap.add_argument("mmd", type=Path, nargs="+", help="tazelenecek .mmd dosyalari")
    ap.add_argument("--taban", default=None, metavar="GIT_REF",
                    help="eski satirlarin ait oldugu git-ref; verilmezse HEAD + taban suphesi "
                         "engeli (supheli → cikis 2, hicbir dosya yazilmaz)")
    ap.add_argument("--kuru", action="store_true", help="dosya yazma, yalniz rapor")
    args = ap.parse_args(argv)
    kok = args.kok.resolve()
    varsayilan = args.taban is None
    ref = "HEAD" if varsayilan else args.taban
    sha = D.taban_ref_coz(ref, kok)
    if sha is None:
        print(f"TABAN GECERSIZ: {ref!r} bir commit degil ({kok})")
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
    print(f"taban: {ref} = {sha[:12]} ("
          + ("varsayilan — taban suphesi engeller)" if varsayilan
             else "elle verildi — taban suphesi yalniz uyarir)"))
    supheler = {p: taban_suphesi(p, kok, kaynak, sha) for p in args.mmd}
    tum = [s for ss in supheler.values() for s in ss]
    if tum and varsayilan:
        for s in tum:
            print(f"TABAN SUPHELI: {s}")
        print(f"SONUC: TABAN SUPHELI ({len(tum)} dugum) — hicbir dosya yazilmadi. Sonuc tabana "
              "bagli: .mmd satirlarinin ait oldugu tabani --taban ile acikca verin (.mmd "
              "degismediyse son commit'i; onceki bir tazelemeyle degistiyse .mmd'yi git "
              "checkout ile geri alip yeniden kosun).")
        return 2
    for s in tum:
        print(f"TABAN UYARISI: {s}")
    toplam_degisen = toplam_hata = 0
    for p in args.mmd:
        degisen, hatalar = mmd_tazele(p, kaynak, sha, args.kuru, head, tarih,
                                      damga=not supheler[p])
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
