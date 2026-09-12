"""T226-D / T226-D2 — akış d düğümlerinin KAPSAM + DEYİM + KENAR denetimi
(D-448 §6, AKIS-D, D-454).

NEDEN: `scripts/akis_satir_tazele.py` düğüm etiketini dosyada eski satıra EN
YAKIN yerde arar; büyük eklemede düğümü BAŞKA fonksiyondaki aynı metne
bağlayabiliyor (T227'de 12 düğüm). `akis_diyagram_dogrula` yalnız metnin İLK
satırını denetler.

T226-D sürümü yalnız qualname karşılaştırıyordu ve bir kaymayı KAÇIRDI (D-454,
AKIS-D2 yan bulgusu): d78, `onayla`da ilk satırı AYNI üç
`self._kanit_yaz("HAKEM_ONAYI_REDDI", seq=…,` çağrısından birine bağlı; tazeleme
onu AYNI fonksiyondaki `sebep="ANKOR_YOK"` çağrısına kaydırdı (qualname aynı →
"AYNI" dendi).

T226-D2: HER düğüm için taban (eski .mmd → taban kaynağı) ve çalışma ağacı
(yeni .mmd → ağaç kaynağı) tarafında:
  KAPSAM  satırı kapsayan en içteki def/class nitelikli adı (qualname, AST)
  DEYİM   o satırda BAŞLAYAN deyimin TAM metni (`ast.unparse`: çok satırlı
          çağrının bütün argümanları dahil; biçim/yorum duyarsız). Bileşik
          deyimde yalnız başlık (`if <koşul>:`, `while …:`, `with …:`),
          `except` işleyicisinde `except T as e:`, def/class'ta yalnız
          `def ad`/`class ad` (imza değişimi — ör. yeni parametre — kayma değil)
  SIRA    aynı kapsamda aynı deyim metninin kaçıncı geçişi (satır sırası)
  KENAR   `dX -->|"evet: BELIRTEC"| dY` kenarında BELIRTEC (BÜYÜK_HARF), dY'nin
          deyimindeki dizgi sabitlerinden biri olmalı (ör. `sebep="…"`) —
          düğümün diyagramdaki ANLAMI; taban da bu denetimden geçirilir
Durum: AYNI · DUZELTILDI (tabanın bağı KENAR'dan düşüyor, yenisi geçiyor, aynı
kapsam — taban anlamca yanlıştı) · HATA (neden sütunuyla). Satırda başlayan
deyim yoksa (devam satırı/yorum) DEYIM_YOK → HATA.

T226-D3 (D-460 karar 3) — ALTGRAFIK: TABANDAN BAĞIMSIZ denetim.
NEDEN: yukarıdaki KAPSAM/DEYIM/SIRA/KENAR denetimlerinin HEPSİ taban .mmd ile
ağaç .mmd'yi kıyaslar; tanım gereği TABANDA ZATEN VAR OLAN bir yanlışı
göremezler, üstelik yanlışı düzeltmeyi "KAPSAM değişti" diye HATA sayarlar.
Bağımsız mimar denetimi bunu ölçtü (D-460): akis_d'de d71 `onayla` alt
grafiğindeyken `_ankor_yok_onayini_kapat`ın 2182'sine, d112 `ika_baslat` alt
grafiğindeyken `iha_indi`nin 3931'ine bağlıydı; betik bu qualname'leri KENDİ
ÇIKTISINDA basıp yine "kapsam HATASI 0" dedi, doğru satıra çekme denemesini
ise HATA saydı.

KURAL (ALTGRAFIK): her DEYİM düğümünün atıf satırının AST qualname'i, içinde
durduğu subgraph başlığının atıf satırının qualname'i ile AYNI ya da ONUN
ALTINDA (`uq` ya da `uq.` öneki) olmalı; dosya da aynı olmalı. Uymayan →
ALTGRAFIK hatası, çıkış 1. Denetim YALNIZ çalışma ağacını okur — taban
gerekmez, bu yüzden tabandaki eski yanlışı da görür.

İSTİSNA — ÇAĞRI GÖVDESİ (gerekçe): diyagram kuralı, çağrılan fonksiyonun
gövdesinden bir deyimi ÇAĞRI düğümünün hemen ardına koyar; o deyim doğal
olarak çağıranın değil ÇAĞRILANIN kapsamındadır. Bu kayma değil çizim
kuralıdır — bağımsız denetim de akis_d'nin d11 ve d96'sını kusur SAYMADI
(d11 = `fda_kipini_uygula` gövdesi, hemen önünde d10 = "def
YksArayuz.fda_kipini_uygula()"; d96 = `_kanit_kilidi_var` gövdesi, hemen
önünde d95 = "def YksArayuz._kanit_kilidi_var()"). Bu yüzden:
  * ilk etiket satırı `def ad()` biçiminde olan ÇAĞRI düğümleri denetlenmez
    (zaten bir TANIM satırı gösterirler; kapsam kıyası anlamsızdır),
  * bir deyim düğümü, aynı alt grafikte KENDİSİNDEN HEMEN ÖNCE gelen `def
    ad()` çağrı düğümünün kapsamına düşüyorsa kabul edilir (CAGRI_GOVDESI).
    "Hemen önce" kuralı bilerek dardır: alt grafikte bir kez görülmüş bir def
    düğümü, ardından gelen İLGİSİZ düğümleri bağışlamaz.
Alt grafik dışındaki düğümlerin kapsayanı yoktur; denetlenmezler.

SIRA: ALTGRAFIK denetimi ÖNCE koşar — bugünkü taban-ağaç kıyası kalır ama tek
başına yeterli DEĞİLDİR. ALTGRAFIK hatası varsa özet yine basılır, çıkış 1.

ALTGRAFIK_DUZELTILDI (taban-ağaç kıyasının kaçınılmaz sonucu): taban .mmd'de
bir düğüm YANLIŞ kapsama bağlıysa, onu DOĞRU kapsama çekmek taban kıyasında
"KAPSAM değişti" diye HATA görünür — ölçüldü: d71/d112 düzeltilince kapı
KAPSAM 2 verdi. Bu, tabanı ÇİMENTOLAMAK olurdu. Kural: bir düğümün KAPSAM
(ve SIRA) farkı, YALNIZ şu ÜÇ koşul birlikte ölçülürse düzeltme sayılır —
  (a) düğüm TABANDA ALTGRAFIK denetiminden DÜŞÜYOR (taban .mmd, taban kaynağı),
  (b) düğüm AĞAÇTA ALTGRAFIK denetiminden GEÇİYOR,
  (c) başka neden yok (DEYIM/DOSYA/KENAR/DEYIM_YOK farkı varsa HATA'dır).
Gevşetme değildir: kanıtı ölçümün kendisi üretir, ve düğümü YANLIŞ kapsama
taşıyan her mutasyon (b)'den düşer → çıkış 1.

KOSUM (depo kökünden):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py [--taban master]
  ... --rapor --mmd FDR/sekiller/akis_b.mmd --mmd FDR/sekiller/akis_e.mmd
      RAPOR kipi: YALNIZ ALTGRAFIK denetimi, taban kıyası yok, çıkış DAİMA 0
      — başka diyagramları DÜZELTMEDEN ölçmek için (T241).
Çıkış: 0 HATA yok · 1 en az bir HATA
"""
import argparse
import ast
import copy
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
DUGUM = re.compile(r'^\s*(?:subgraph\s+)?([A-Za-z][A-Za-z0-9_]*)\s*(?:\["|\{")'
                   r'.*<br/>([A-Za-z0-9_./-]+\.py):(\d+)"(?:\]|\})\s*$')
KENAR = re.compile(r'^\s*([A-Za-z][A-Za-z0-9_]*)\s*-->\|"evet: ([A-Z][A-Z0-9_]+)"\|'
                   r'\s*([A-Za-z][A-Za-z0-9_]*)\s*$')
# ALTGRAFIK denetimi (T226-D3): DUGUM'dan farkı — `subgraph` önekini ve etiket
# metnini de yakalar (yığın kurmak ve `def ad()` çağrı düğümünü ayırmak için).
DUGUM_TAM = re.compile(r'^\s*(subgraph\s+)?([A-Za-z][A-Za-z0-9_]*)\s*(?:\["|\{")'
                       r'(.*)<br/>([A-Za-z0-9_./-]+\.py):(\d+)"(?:\]|\})\s*$')
CAGRI = re.compile(r'^def [A-Za-z_][A-Za-z0-9_.]*\(\)$')
SON = re.compile(r'^\s*end\s*$')
TANIM = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
DONGU_KOSUL = (ast.If, ast.While, ast.For, ast.AsyncFor)
BAGLAM = (ast.With, ast.AsyncWith)
DENE = tuple(t for t in (getattr(ast, "Try", None), getattr(ast, "TryStar", None)) if t)


def satirlar(metin):
    return metin.replace("\r\n", "\n").split("\n")


def dugumler(metin):
    sonuc = {}
    for s in satirlar(metin):
        m = DUGUM.match(s)
        if m:
            if m.group(1) in sonuc:
                raise ValueError(f"Tekrarlanan dugum: {m.group(1)}")
            sonuc[m.group(1)] = (m.group(2), int(m.group(3)))
    return sonuc


def kenarlar(metin):
    return [m.groups() for m in map(KENAR.match, satirlar(metin)) if m]


def kapsamlar(agac):
    """[(bas, son, qualname)] — dekoratör satırları dahil."""
    cikti = []

    def gez(dugum, yigin):
        for alt in ast.iter_child_nodes(dugum):
            if isinstance(alt, TANIM):
                bas = min([alt.lineno] + [d.lineno for d in alt.decorator_list])
                ad = ".".join(yigin + [alt.name])
                cikti.append((bas, alt.end_lineno, ad))
                gez(alt, yigin + [alt.name])
            else:
                gez(alt, yigin)

    gez(agac, [])
    return cikti


def kapsam(tablo, satir):
    icerenler = [(son - bas, ad) for bas, son, ad in tablo if bas <= satir <= son]
    return min(icerenler)[1] if icerenler else "<modul>"


def imza(d):
    """Deyimin karşılaştırma metni (bkz. modül belgesi, DEYİM)."""
    if isinstance(d, TANIM):
        return f"{'class' if isinstance(d, ast.ClassDef) else 'def'} {d.name}"
    if isinstance(d, ast.ExceptHandler):
        metin = "except"
        if d.type is not None:
            metin += " " + ast.unparse(d.type)
        if d.name:
            metin += " as " + d.name
        return metin + ":"
    if isinstance(d, DENE):
        return "try:"
    if isinstance(d, DONGU_KOSUL + BAGLAM):
        k = copy.copy(d)
        k.body = [ast.Pass()]
        if hasattr(k, "orelse"):
            k.orelse = []
        return " ".join(ast.unparse(k).rsplit("pass", 1)[0].split())
    return " ".join(ast.unparse(d).split())


def dizgiler(d):
    """Deyimin dizgi sabitleri; bileşik deyimde yalnız başlık (gövde hariç)."""
    if isinstance(d, TANIM + DENE):
        return set()
    if isinstance(d, DONGU_KOSUL + BAGLAM):
        d = copy.copy(d)
        d.body, d.orelse = [], []
    return {c.value for c in ast.walk(d)
            if isinstance(c, ast.Constant) and isinstance(c.value, str)}


class Kaynak:
    """Bir kaynak dosyanın deyim dizini: satır → (kapsam, imza, sıra)."""

    def __init__(self, metin):
        agac = ast.parse(metin)
        self.tablo = kapsamlar(agac)
        derinlik = {}

        def gez(dugum, d):
            for alt in ast.iter_child_nodes(dugum):
                if isinstance(alt, (ast.stmt, ast.excepthandler)):
                    derinlik[alt] = d
                gez(alt, d + 1)

        gez(agac, 0)
        self.satirda = {}                # satır → en DIŞTAKİ, o satırda başlayan deyim
        for n, d in derinlik.items():
            onceki = self.satirda.get(n.lineno)
            if onceki is None or d < derinlik[onceki]:
                self.satirda[n.lineno] = n
        gruplar = {}
        for n in sorted(derinlik, key=lambda x: (x.lineno, derinlik[x])):
            anahtar = (kapsam(self.tablo, n.lineno), imza(n))
            gruplar.setdefault(anahtar, []).append(n.lineno)
        self.sira = {}
        for anahtar, satirlar_ in gruplar.items():
            for i, s in enumerate(satirlar_):
                self.sira.setdefault((anahtar, s), i + 1)

    def kunye(self, satir):
        n = self.satirda.get(satir)
        kp = kapsam(self.tablo, satir)
        if n is None:
            return kp, None, None
        im = imza(n)
        return kp, im, self.sira[((kp, im), satir)]

    def dizgi(self, satir):
        n = self.satirda.get(satir)
        return set() if n is None else dizgiler(n)


def git_goster(rev, yol):
    return subprocess.run(["git", "-C", str(KOK), "show", f"{rev}:{yol}"],
                          capture_output=True, check=True).stdout.decode("utf-8")


def kisalt(metin, n=70):
    return metin if metin is None or len(metin) <= n else metin[:n - 1] + "…"


def kenar_denetimi(ad, mmd_metni, okuyucu):
    """{hedef: (belirteç, kaynak, tutar_mi)} + rapor satırları."""
    dug = dugumler(mmd_metni)
    sonuc, rapor = {}, []
    for kaynak, belirtec, hedef in kenarlar(mmd_metni):
        if hedef not in dug:
            sonuc[hedef] = (belirtec, kaynak, False)
            rapor.append(f"  KENAR {ad} {kaynak} -evet: {belirtec}-> {hedef}: HEDEF YOK")
            continue
        dosya, satir = dug[hedef]
        tutar = belirtec in okuyucu(dosya).dizgi(satir)
        sonuc[hedef] = (belirtec, kaynak, tutar)
        rapor.append(f"  KENAR {ad} {kaynak} -evet: {belirtec}-> {hedef} "
                     f"({dosya}:{satir}): {'TUTAR' if tutar else 'TUTMAZ'}")
    return sonuc, rapor


def altgrafik_denetimi(mmd_metni, okuyucu):
    """ALTGRAFIK — TABANDAN BAĞIMSIZ: deyim düğümü kendi alt grafiğinin
    kapsamında mı? (bkz. modül belgesi, KURAL ve İSTİSNA)

    Döner: (hata, rapor, denetlenen, bagisik, hatali) — `hatali` denetimden
    düşen düğüm kimlikleri kümesidir (taban/ağaç kıyasında kanıt olarak
    kullanılır, bkz. modül belgesi ALTGRAFIK_DUZELTILDI).
    """
    yigin = []            # [(kimlik, dosya, satir, qualname)] — açık alt grafikler
    onceki_cagri = []     # her açık alt grafik için: HEMEN önceki `def ad()` düğümü
    hata = denetlenen = bagisik = 0
    rapor, hatali = [], set()
    for s in satirlar(mmd_metni):
        if SON.match(s):
            if yigin:
                yigin.pop()
                onceki_cagri.pop()
            continue
        m = DUGUM_TAM.match(s)
        if not m:
            continue
        alt, kimlik, etiket, dosya, satir = (m.group(1), m.group(2), m.group(3),
                                             m.group(4), int(m.group(5)))
        qn = kapsam(okuyucu(dosya).tablo, satir)
        if alt:
            yigin.append((kimlik, dosya, satir, qn))
            onceki_cagri.append(None)
            continue
        ilk = etiket.split("<br/>")[0].strip()
        if CAGRI.match(ilk):
            # ÇAĞRI düğümü: kendisi denetlenmez, ardından gelen TEK düğüm için
            # alternatif kapsam olur (çağrılan fonksiyonun gövdesi).
            if onceki_cagri:
                onceki_cagri[-1] = (kimlik, dosya, qn)
            continue
        if not yigin:
            continue          # alt grafik dışı düğümün kapsayanı yok
        cagri = onceki_cagri[-1]
        onceki_cagri[-1] = None       # "hemen önce" YALNIZ bir düğüm için geçerli
        denetlenen += 1
        u_kimlik, u_dosya, u_satir, uq = yigin[-1]

        def icinde(hedef_dosya, hedef_qn):
            return dosya == hedef_dosya and (qn == hedef_qn
                                             or qn.startswith(hedef_qn + "."))

        if icinde(u_dosya, uq):
            continue
        if cagri is not None and icinde(cagri[1], cagri[2]):
            bagisik += 1
            rapor.append(f"  CAGRI_GOVDESI {kimlik} ({dosya}:{satir} [{qn}]): "
                         f"altgrafik {u_kimlik} [{uq}] disinda ama HEMEN onceki "
                         f"cagri dugumu {cagri[0]} [{cagri[2]}] bu kapsami gosteriyor")
            continue
        hata += 1
        hatali.add(kimlik)
        rapor.append(f"  HATA {kimlik} [ALTGRAFIK]: {dosya}:{satir} [{qn}] "
                     f"{kisalt(ilk, 60)!r}\n       altgrafik {u_kimlik} "
                     f"{u_dosya}:{u_satir} [{uq}] KAPSAMINDA DEGIL")
    return hata, rapor, denetlenen, bagisik, hatali


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--taban", default="76df4dcb")
    ap.add_argument("--mmd", action="append", default=None,
                    help="denetlenecek .mmd (birden cok kez verilebilir; "
                         "varsayilan FDR/sekiller/akis_d.mmd)")
    ap.add_argument("--rapor", action="store_true",
                    help="RAPOR kipi: YALNIZ ALTGRAFIK denetimi, taban kiyasi "
                         "yok, cikis DAIMA 0 (duzeltilmemis diyagramlari olcmek icin)")
    a = ap.parse_args(argv)
    toplam = 0
    for yol in (a.mmd or ["FDR/sekiller/akis_d.mmd"]):
        toplam += diyagram_denetle(a, yol)
    return 0 if a.rapor else (1 if toplam else 0)


def diyagram_denetle(a, mmd_yolu):
    """Tek bir .mmd'yi denetle; HATA sayısını döndür."""
    k_yeni = {}

    def okur_yeni(dosya):
        if dosya not in k_yeni:
            k_yeni[dosya] = Kaynak((KOK / dosya).read_text(encoding="utf-8"))
        return k_yeni[dosya]

    yeni_mmd = (KOK / mmd_yolu).read_text(encoding="utf-8")
    # ÖNCE ve TABANDAN BAĞIMSIZ: alt grafik kapsam denetimi (T226-D3, D-460).
    (alt_hata, alt_rapor, alt_denetlenen, alt_bagisik,
     alt_yeni_hatali) = altgrafik_denetimi(yeni_mmd, okur_yeni)
    if alt_rapor:
        print("\n".join(alt_rapor))
    print(f"{mmd_yolu}: ALTGRAFIK {alt_hata} "
          f"({alt_denetlenen} deyim dugumu denetlendi, {alt_bagisik} CAGRI_GOVDESI "
          f"bagisik){' [RAPOR kipi: cikis 0]' if a.rapor else ''}")
    if a.rapor:
        return alt_hata
    eski_mmd = git_goster(a.taban, mmd_yolu)
    eski, yeni = dugumler(eski_mmd), dugumler(yeni_mmd)
    k_eski = {}

    def okur_eski(dosya):
        if dosya not in k_eski:
            k_eski[dosya] = Kaynak(git_goster(a.taban, dosya))
        return k_eski[dosya]

    # TABANIN ALTGRAFIK ölçümü — yalnız KANIT için (tabanı düzeltmeyiz):
    # tabanda düşen + ağaçta geçen düğümün KAPSAM farkı düzeltmedir.
    alt_eski_hatali = altgrafik_denetimi(eski_mmd, okur_eski)[4]
    kenar_eski, rapor_eski = kenar_denetimi("taban", eski_mmd, okur_eski)
    kenar_yeni, rapor_yeni = kenar_denetimi("yeni ", yeni_mmd, okur_yeni)
    degisen = ayni = duzeltildi = 0
    hatalar = {k: 0 for k in ("ALTGRAFIK", "KAPSAM", "DEYIM", "SIRA", "DOSYA",
                              "DEYIM_YOK", "KENAR", "YENI", "SILINEN",
                              "KENAR_KUMESI")}
    hatalar["ALTGRAFIK"] = alt_hata
    hata = alt_hata
    for kimlik in sorted(eski.keys() - yeni.keys()):
        hata += 1
        hatalar["SILINEN"] += 1
        print(f"  HATA {kimlik} [SILINEN]: tabandaki dugum yeni diyagramda yok")
    if Counter(kenarlar(eski_mmd)) != Counter(kenarlar(yeni_mmd)):
        hata += 1
        hatalar["KENAR_KUMESI"] += 1
        print("  HATA [KENAR_KUMESI]: kaynak/hedef/ret belirteci tabandan degisti")
    for kimlik, (dosya, satir) in sorted(yeni.items(), key=lambda x: (len(x[0]), x[0])):
        if kimlik not in eski:
            hatalar["YENI"] += 1
            hata += 1
            print(f"  HATA {kimlik} [YENI]: tabanda yok -> {dosya}:{satir}")
            continue
        e_dosya, e_satir = eski[kimlik]
        degisen += (e_dosya, e_satir) != (dosya, satir)
        ek, ei, es = okur_eski(e_dosya).kunye(e_satir)
        yk, yi, ys = okur_yeni(dosya).kunye(satir)
        neden = []
        if e_dosya != dosya:
            neden.append("DOSYA")
        if ei is None or yi is None:
            neden.append("DEYIM_YOK")
        if ek != yk:
            neden.append("KAPSAM")
        if ei is not None and yi is not None and ei != yi:
            neden.append("DEYIM")
        if not neden and es != ys:
            neden.append("SIRA")
        k_e, k_y = kenar_eski.get(kimlik), kenar_yeni.get(kimlik)
        if k_y is not None and not k_y[2]:
            neden.append("KENAR")
        duzeltme = (neden and set(neden) <= {"DEYIM", "SIRA"} and k_y is not None
                    and k_y[2] and k_e is not None and not k_e[2]
                    and k_y[:2] == k_e[:2])
        alt_duzeltme = (neden and set(neden) <= {"KAPSAM", "SIRA"}
                        and kimlik in alt_eski_hatali
                        and kimlik not in alt_yeni_hatali)
        satir_metni = (f"{e_dosya}:{e_satir} [{ek}] #{es} {kisalt(ei)!r}\n"
                       f"       -> {dosya}:{satir} [{yk}] #{ys} {kisalt(yi)!r}")
        if duzeltme:
            duzeltildi += 1
            print(f"  DUZELTILDI {kimlik} [{'+'.join(neden)}; KENAR 'evet: {k_y[0]}' "
                  f"taban TUTMAZ -> yeni TUTAR]: {satir_metni}")
        elif alt_duzeltme:
            duzeltildi += 1
            print(f"  DUZELTILDI {kimlik} [{'+'.join(neden)}; ALTGRAFIK taban "
                  f"DUSER -> yeni GECER]: {satir_metni}")
        elif neden:
            hata += 1
            for n in neden:
                hatalar[n] += 1
            print(f"  HATA {kimlik} [{'+'.join(neden)}]: {satir_metni}")
        else:
            ayni += 1
            print(f"  AYNI {kimlik}: {e_dosya}:{e_satir} -> {satir} [{yk}] #{ys} "
                  f"{kisalt(yi, 60)!r}")
    print("\n".join(rapor_eski + rapor_yeni))
    ke = sum(1 for v in kenar_eski.values() if v[2])
    ky = sum(1 for v in kenar_yeni.values() if v[2])
    print(f"{mmd_yolu}: taban {a.taban} · {len(yeni)} dugum · satiri degisen {degisen} · "
          f"AYNI {ayni} · DUZELTILDI {duzeltildi} · kapsam HATASI {hata} "
          f"({', '.join(f'{k} {v}' for k, v in hatalar.items())}) · KENAR taban "
          f"{ke}/{len(kenar_eski)} tutar, yeni {ky}/{len(kenar_yeni)} tutar")
    return hata


if __name__ == "__main__":
    raise SystemExit(main())
