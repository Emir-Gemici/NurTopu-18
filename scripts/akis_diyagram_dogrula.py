#!/usr/bin/env python3
"""Akış diyagramı (Mermaid .mmd) düğümlerini KODA karşı doğrular (Y-3.3.4-M01).

NEDEN: 6 Eylül gecesi çizilen diyagramlar çürütücüde düştü — bazı düğümler
dosya:satır taşımıyordu ("Cx0 yok sayılır" gibi sözde düğümler). Bu betik
KURALI koda bağlar: bir .mmd içindeki HER düğüm (alt-grafik başlıkları dâhil)
şu iki biçimden biridir, başka düğüm tipi YOKTUR:

  ID["metin<br/>dosya.py:SATIR"]   fonksiyon ya da blok
  ID{"kosul<br/>dosya.py:SATIR"}   karar (koşul metni koddan birebir)

  * Son satır `dosya:satır` (depo köküne göre yol).
  * Önceki her satır kodda o satırın ±SATIR_TOLERANSI penceresinde
    BİREBİR bulunmalıdır (boşluk sıkıştırılarak). `def ad()` biçimi
    fonksiyon düğümüdür: pencerede `def ad(` aranır; tam satırda ise
    "tam" sayılır.
  * Kenarlarda yalnız tanımlı ID'ler geçer: tanımsız bir ID Mermaid'de
    kendiliğinden düğüm olur — bu da sözde düğümdür, HATA sayılır.
  * Tanınmayan satır (alıntısız düğüm, tırnaksız etiket) HATA sayılır.

Mermaid varlık kodları çözülür: #quot; #lt; #gt; #amp; #35; ve #NN;.

KAPSAM DENETİMİ (--taban, AKIS-D / D-448 (6)): metin denetimi, düğüm BAŞKA
fonksiyondaki aynı metne kaydığında da "tuttu" der (T227: 12 düğüm). `--taban
<git-ref>` verilince her düğüm için tabandaki .mmd'nin gösterdiği satırın
(git show <ref>:<yol>) ast ile en içteki def/class nitelikli adı (qualname),
çalışma ağacındaki satırın qualname'i ile karşılaştırılır; farklıysa
"KAPSAM DEGISTI" → çıkış 1. Tabandaki .mmd'de olmayan düğüm "yeni" sayılır
(karşılaştırılamaz, sayısı basılır). Seçenek verilmezse davranış ve çıktı
değişmez.

Kullanım:
  python scripts/akis_diyagram_dogrula.py            # 5 diyagramı doğrula
  python scripts/akis_diyagram_dogrula.py --tablo    # + akis_<x>_dugumler.md yaz
  python scripts/akis_diyagram_dogrula.py --mmd FDR/sekiller/akis_a.mmd
  python scripts/akis_diyagram_dogrula.py --taban HEAD   # + kapsam denetimi
Çıkış: 0 tüm düğümler tuttu · 1 en az bir hata · 2 dosya yok / taban geçersiz
"""

import argparse
import ast
import html
import re
import subprocess
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
SEKILLER = KOK / "FDR" / "sekiller"
DIYAGRAMLAR = ("a", "b", "c", "d", "e")
SATIR_TOLERANSI = 3

RE_DUGUM = re.compile(
    r'^\s*(?:(subgraph)\s+)?([A-Za-z][A-Za-z0-9_]*)\s*(\["|\{")(.*?)("\]|"\})\s*$')
RE_YOL = re.compile(r'^([A-Za-z0-9_][A-Za-z0-9_./-]*\.py):(\d+)$')
RE_DEF = re.compile(
    r'^def ([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\(\)$')
RE_BASLIK = re.compile(
    r'^%% koddan turetildi ([0-9a-f]{7,40}) (\d{4}-\d{2}-\d{2})\b')
RE_TANINAN = re.compile(
    r'^\s*(flowchart\s+(?:TD|TB|LR|RL|BT)|end|direction\s+(?:TD|TB|LR|RL|BT)'
    r'|classDef\b.*|class\b.*|style\b.*|linkStyle\b.*)\s*$')
RE_OK = re.compile(r'\s*(?:-->|-\.->|==>|---|-\.-)\s*')
RE_ID = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
RE_BR = re.compile(r'<br\s*/?>')


def varlik_coz(metin):
    """Mermaid varlık kodları (#quot; #35; …) → düz metin."""
    metin = re.sub(r'#(\d+);', lambda m: chr(int(m.group(1))), metin)
    metin = re.sub(r'#([A-Za-z]+);', r'&\1;', metin)
    return html.unescape(metin)


def _sikistir(s):
    return " ".join(s.split())


class Dugum:
    __slots__ = ("kimlik", "tur", "parcalar", "dosya", "satir", "mmd_satiri",
                 "dogrulama", "alt_grafik")

    def __init__(self, kimlik, sekil, etiket, mmd_satiri, alt_grafik):
        self.kimlik = kimlik
        self.alt_grafik = alt_grafik
        parcalar = [p.strip() for p in RE_BR.split(etiket)]
        self.parcalar = [varlik_coz(p) for p in parcalar]
        self.mmd_satiri = mmd_satiri
        self.dosya = self.satir = None
        self.dogrulama = None
        m = RE_YOL.match(self.parcalar[-1]) if self.parcalar else None
        if m:
            self.dosya, self.satir = m.group(1), int(m.group(2))
        metin = self.parcalar[0] if self.parcalar else ""
        if sekil == '{"':
            self.tur = "karar"
        elif RE_DEF.match(metin):
            self.tur = "fonksiyon"
        else:
            self.tur = "blok"

    @property
    def metin(self):
        return " ⏎ ".join(self.parcalar[:-1])


def ayristir(metin):
    """.mmd metni → (düğümler, kenar id'leri, hatalar, başlık)."""
    dugumler, kenar_idler, hatalar = [], [], []
    baslik = None
    alt_grafik = None
    satirlar = metin.replace("\r\n", "\n").split("\n")
    if not satirlar or not RE_BASLIK.match(satirlar[0]):
        hatalar.append("1. satır '%% koddan turetildi <commit> <tarih>' değil")
    else:
        m = RE_BASLIK.match(satirlar[0])
        baslik = (m.group(1), m.group(2))
    for no, ham in enumerate(satirlar, 1):
        s = ham.strip()
        if not s or s.startswith("%%"):
            continue
        m = RE_DUGUM.match(ham)
        if m:
            alt_mi, kimlik, sekil, etiket, kapanis = m.groups()
            if (sekil == '["' and kapanis != '"]') or (sekil == '{"' and kapanis != '"}'):
                hatalar.append(f"satır {no}: açılış/kapanış uyuşmuyor ({kimlik})")
                continue
            d = Dugum(kimlik, sekil, etiket, no, alt_grafik)
            dugumler.append(d)
            if alt_mi:
                alt_grafik = kimlik
            continue
        if RE_TANINAN.match(ham):
            if s == "end":
                alt_grafik = None
            continue
        if s.startswith("subgraph"):
            hatalar.append(f"satır {no}: alt-grafik başlığı alıntısız/dosya:satırsız: {s}")
            continue
        # Kenar satırı: |etiket| kaldır, oklardan böl, kalan her parça ID olmalı
        temiz = re.sub(r'\|[^|]*\|', '', ham)
        parcalar = [p.strip() for p in RE_OK.split(temiz) if p.strip()]
        if len(parcalar) < 2 or not RE_OK.search(temiz):
            hatalar.append(f"satır {no}: tanınmayan satır: {s}")
            continue
        for p in parcalar:
            for kimlik in (k.strip() for k in p.split("&")):
                if not RE_ID.match(kimlik):
                    hatalar.append(f"satır {no}: kenar parçası ID değil (satır-içi "
                                   f"düğüm ya da tırnaksız etiket?): {kimlik!r}")
                else:
                    kenar_idler.append((no, kimlik))
    return dugumler, kenar_idler, hatalar, baslik


def dugumu_dogrula(d, kok=KOK, tolerans=SATIR_TOLERANSI, _onbellek=None):
    """None = tuttu; aksi hâlde hata metni. d.dogrulama doldurulur."""
    if d.dosya is None:
        return f"{d.kimlik} (satır {d.mmd_satiri}): son satır dosya:satır değil: {d.parcalar[-1]!r}"
    if len(d.parcalar) < 2:
        return f"{d.kimlik}: metin yok (yalnız dosya:satır)"
    yol = kok / d.dosya
    if not yol.is_file():
        return f"{d.kimlik}: dosya yok: {d.dosya}"
    if _onbellek is not None and d.dosya in _onbellek:
        satirlar = _onbellek[d.dosya]
    else:
        satirlar = yol.read_text(encoding="utf-8", errors="replace").splitlines()
        if _onbellek is not None:
            _onbellek[d.dosya] = satirlar
    if not 1 <= d.satir <= len(satirlar):
        return f"{d.kimlik}: {d.dosya}:{d.satir} aralık dışı (dosya {len(satirlar)} satır)"
    lo, hi = max(1, d.satir - tolerans), min(len(satirlar), d.satir + tolerans)
    pencere = {i: _sikistir(satirlar[i - 1]) for i in range(lo, hi + 1)}
    en_uzak = 0
    for k, parca in enumerate(d.parcalar[:-1]):
        m = RE_DEF.match(parca)
        hedef = f"def {m.group(1).split('.')[-1]}(" if m else _sikistir(parca)
        if not hedef:
            return f"{d.kimlik}: boş metin parçası"
        bulunan = [i for i, s in pencere.items() if hedef in s]
        if not bulunan:
            return (f"{d.kimlik}: {parca!r} {d.dosya}:{d.satir}±{tolerans} "
                    f"içinde YOK")
        # Çok satırlı blok: k. parçanın beklenen yeri satır+k (ardışık satırlar).
        # "tam" = blok başı tam satırda ve devam parçaları ardışık.
        en_uzak = max(en_uzak, min(abs(i - (d.satir + k)) for i in bulunan))
    d.dogrulama = "tam" if en_uzak == 0 else f"±{en_uzak}"
    return None


def dogrula_metin(metin, kok=KOK, tolerans=SATIR_TOLERANSI):
    """Bir .mmd metnini uçtan uca doğrula → (düğümler, hatalar, başlık)."""
    dugumler, kenar_idler, hatalar, baslik = ayristir(metin)
    tanimli = {}
    for d in dugumler:
        if d.kimlik in tanimli:
            hatalar.append(f"{d.kimlik}: iki kez tanımlı (satır {tanimli[d.kimlik]} ve {d.mmd_satiri})")
        tanimli[d.kimlik] = d.mmd_satiri
    for no, kimlik in kenar_idler:
        if kimlik not in tanimli:
            hatalar.append(f"satır {no}: kenarda tanımsız ID {kimlik!r} — Mermaid bunu "
                           "sözde düğüm yapar")
    onbellek = {}
    for d in dugumler:
        h = dugumu_dogrula(d, kok, tolerans, onbellek)
        if h:
            hatalar.append(h)
    return dugumler, hatalar, baslik


# ── Kapsam (qualname) katmanı — AKIS-D ───────────────────────────────────
# Metin denetimi düğümün HANGİ fonksiyonda durduğunu görmez; bu katman her
# satırı ast ile en içteki def/class'a bağlar. akis_satir_tazele.py da
# buradan içe aktarır (tek tanım: iki araç aynı kapsam kuralını kullanır).
MODUL_KAPSAMI = "<modul>"
_KAPSAM_TIPLERI = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def satirlara_bol(metin):
    """ast satır numaralarıyla uyumlu bölme (yalnız \\n, \\r\\n, \\r)."""
    return metin.replace("\r\n", "\n").replace("\r", "\n").split("\n")


class KapsamHaritasi:
    """Python kaynağı → her satırın en içteki def/class kapsamı (ast).

    Kapsam kimliği (qualname, sıra): `Sinif.metot` biçiminde nitelikli ad ve
    aynı ad birden çok kez tanımlıysa (property setter, if/else içinde iki
    def) kaynak sırasındaki kaçıncı tanım olduğu. Dekoratör satırları tanıma
    aittir. Hiçbir def/class içinde olmayan satır MODUL_KAPSAMI'dır.
    Sözdizimi hatası → SyntaxError (ya da NUL bayt → ValueError).
    """

    def __init__(self, kaynak):
        if kaynak.startswith("\ufeff"):
            kaynak = kaynak[1:]
        agac = ast.parse(kaynak)
        self.satir_sayisi = len(satirlara_bol(kaynak))
        self.kapsamlar = [(MODUL_KAPSAMI, 0, 1, self.satir_sayisi)]
        self._say = {MODUL_KAPSAMI: 1}
        self._en_ic = [0] * (self.satir_sayisi + 2)
        self._gez(agac, "")
        self._dizin = {(q, s): i for i, (q, s, _, _) in enumerate(self.kapsamlar)}

    def _gez(self, dugum, on):
        # Ön-sıra: önce tanımın tüm aralığı, sonra iç tanımlar üzerine yazar.
        for c in ast.iter_child_nodes(dugum):
            if isinstance(c, _KAPSAM_TIPLERI):
                q = on + c.name
                sira = self._say.get(q, 0)
                self._say[q] = sira + 1
                bas = min([c.lineno] + [d.lineno for d in c.decorator_list])
                i = len(self.kapsamlar)
                self.kapsamlar.append((q, sira, bas, c.end_lineno))
                for n in range(bas, c.end_lineno + 1):
                    self._en_ic[n] = i
                self._gez(c, q + ".")
            else:
                self._gez(c, on)

    def kapsam(self, satir):
        """1-tabanlı satır → (qualname, sıra); aralık dışı → None."""
        if not 1 <= satir <= self.satir_sayisi:
            return None
        q, s, _, _ = self.kapsamlar[self._en_ic[satir]]
        return q, s

    def sayi(self, qualname):
        """Bu nitelikli adla kaç tanım var (MODUL_KAPSAMI için 1)."""
        return self._say.get(qualname, 0)

    def baslangic(self, kimlik):
        """(qualname, sıra) → tanımın ilk satırı (dekoratör dâhil); yoksa None."""
        i = self._dizin.get(kimlik)
        return None if i is None else self.kapsamlar[i][2]

    def satirlari(self, kimlik):
        """En içteki kapsamı TAM OLARAK `kimlik` olan satırlar (iç tanımlar hariç)."""
        i = self._dizin.get(kimlik)
        if i is None:
            return []
        _, _, bas, son = self.kapsamlar[i]
        return [n for n in range(bas, son + 1) if self._en_ic[n] == i]


def kapsam_metni(kimlik):
    """(qualname, sıra) → okunur metin; aynı adlı 2. tanım 'ad#2' olur."""
    q, s = kimlik
    return q if s == 0 else f"{q}#{s + 1}"


def taban_ref_coz(ref, kok=KOK):
    """git-ref → tam commit sha; commit değilse None."""
    r = subprocess.run(["git", "-C", str(kok), "rev-parse", "--verify", "--quiet",
                        f"{ref}^{{commit}}"], capture_output=True, text=True)
    sha = r.stdout.strip()
    return sha if r.returncode == 0 and sha else None


def taban_icerigi(kok, ref, yol):
    """`git show <ref>:./<yol>` (yol köke göre, '/' ayraçlı) → metin; yoksa None."""
    r = subprocess.run(["git", "-C", str(kok), "show", f"{ref}:./{yol}"],
                       capture_output=True)
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8-sig", errors="replace")


class KapsamKaynagi:
    """(ref, dosya) → metin / KapsamHaritasi önbelleği; ref None = çalışma ağacı."""

    def __init__(self, kok):
        self.kok = Path(kok)
        self._metin = {}
        self._harita = {}

    def metin(self, dosya, ref=None):
        a = (ref, dosya)
        if a not in self._metin:
            if ref is None:
                yol = self.kok / dosya
                self._metin[a] = (yol.read_bytes().decode("utf-8-sig", errors="replace")
                                  if yol.is_file() else None)
            else:
                self._metin[a] = taban_icerigi(self.kok, ref, dosya)
        return self._metin[a]

    def satirlar(self, dosya, ref=None):
        m = self.metin(dosya, ref)
        return None if m is None else satirlara_bol(m)

    def harita(self, dosya, ref=None):
        """KapsamHaritasi; dosya yoksa None; ast hatası SyntaxError/ValueError yükseltir."""
        a = (ref, dosya)
        if a not in self._harita:
            m = self.metin(dosya, ref)
            self._harita[a] = None if m is None else KapsamHaritasi(m)
        return self._harita[a]


def kapsam_denetle(dugumler, taban_mmd_metni, taban, kaynak):
    """Çalışma .mmd düğümleri ↔ tabandaki .mmd'nin AYNI ID'li düğümü.

    Tabandaki düğümün satırının taban kodundaki kapsamı ile çalışma düğümünün
    satırının çalışma kodundaki kapsamı karşılaştırılır.
    → (karşılaştırılan, tabanda_yok, hatalar); hatalar "KAPSAM DEGISTI",
    "KAPSAM BELIRSIZ" ya da "KAPSAM OLCULEMEDI" ile başlar (hepsi çıkış 1).
    """
    taban_dugum = {}
    if taban_mmd_metni is not None:
        for t in ayristir(taban_mmd_metni)[0]:
            taban_dugum.setdefault(t.kimlik, t)
    karsilastirilan, yeni, hatalar = 0, 0, []
    for d in dugumler:
        t = taban_dugum.get(d.kimlik)
        if t is None:
            yeni += 1
            continue
        if t.dosya is None or d.dosya is None:
            hatalar.append(f"KAPSAM OLCULEMEDI: {d.kimlik}: dosya:satır yok "
                           f"(taban {t.dosya is not None}, çalışma {d.dosya is not None})")
            continue
        yer_t, yer_c = f"{t.dosya}:{t.satir}", f"{d.dosya}:{d.satir}"
        if t.dosya != d.dosya:
            hatalar.append(f"KAPSAM DEGISTI: {d.kimlik}: dosya değişti — "
                           f"taban {yer_t} → çalışma {yer_c}")
            continue
        try:
            ht, hc = kaynak.harita(t.dosya, taban), kaynak.harita(d.dosya)
        except (SyntaxError, ValueError) as e:
            hatalar.append(f"KAPSAM OLCULEMEDI: {d.kimlik}: {d.dosya} ast ile "
                           f"ayrıştırılamadı ({e.__class__.__name__})")
            continue
        if ht is None or hc is None:
            hatalar.append(f"KAPSAM OLCULEMEDI: {d.kimlik}: {d.dosya} "
                           + ("tabanda yok" if ht is None else "çalışma ağacında yok"))
            continue
        kt, kc = ht.kapsam(t.satir), hc.kapsam(d.satir)
        if kt is None or kc is None:
            hatalar.append(f"KAPSAM OLCULEMEDI: {d.kimlik}: satır aralık dışı "
                           f"(taban {yer_t}, çalışma {yer_c})")
            continue
        karsilastirilan += 1
        if kt[0] != kc[0]:
            hatalar.append(f"KAPSAM DEGISTI: {d.kimlik}: taban {yer_t} [{kapsam_metni(kt)}]"
                           f" → çalışma {yer_c} [{kapsam_metni(kc)}]")
        elif ht.sayi(kt[0]) != hc.sayi(kt[0]):
            hatalar.append(f"KAPSAM BELIRSIZ: {d.kimlik}: {kt[0]} adlı tanım sayısı "
                           f"değişti (taban {ht.sayi(kt[0])}, çalışma {hc.sayi(kt[0])}) — "
                           f"taban {yer_t} → çalışma {yer_c}")
        elif kt[1] != kc[1]:
            hatalar.append(f"KAPSAM DEGISTI: {d.kimlik}: aynı adlı başka tanım — taban "
                           f"{yer_t} [{kapsam_metni(kt)}] → çalışma {yer_c} [{kapsam_metni(kc)}]")
    return karsilastirilan, yeni, hatalar


def mmd_kapsam_denetle(mmd_yolu, dugumler, kok, taban, kaynak=None):
    """Bir .mmd için kapsam denetimi → (karşılaştırılan, tabanda_yok, hatalar, taban_mmd_var)."""
    kok = Path(kok).resolve()
    kaynak = kaynak if kaynak is not None else KapsamKaynagi(kok)
    try:
        goreli = Path(mmd_yolu).resolve().relative_to(kok).as_posix()
    except ValueError:
        return 0, 0, [f"KAPSAM OLCULEMEDI: {mmd_yolu} depo kökü dışında"], False
    taban_mmd = taban_icerigi(kok, taban, goreli)
    k, y, h = kapsam_denetle(dugumler, taban_mmd, taban, kaynak)
    return k, y, h, taban_mmd is not None


def tablo_uret(harf, dugumler, baslik):
    """akis_<harf>_dugumler.md içeriği (deterministik; commit .mmd başlığından)."""
    commit, tarih = baslik if baslik else ("?", "?")
    sat = [f"# Akış diyagramı ({harf}) — düğüm → dosya:satır tablosu", "",
           f"Kaynak: `FDR/sekiller/akis_{harf}.mmd` · koddan türetildi: commit "
           f"`{commit}`, {tarih} · üretici: `scripts/akis_diyagram_dogrula.py --tablo`", "",
           "Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; "
           "**karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. "
           f"Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans "
           f"{SATIR_TOLERANSI}). Başka düğüm tipi yoktur.", "",
           "| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |",
           "|---|---|---|---|---|---|---|"]
    for i, d in enumerate(dugumler, 1):
        metin = d.metin.replace("|", "\\|").replace("`", "'")
        sat.append(f"| {i} | `{d.kimlik}` | {d.tur} | {d.alt_grafik or '—'} | "
                   f"`{metin}` | `{d.dosya}:{d.satir}` | {d.dogrulama or 'HATA'} |")
    turler = {}
    for d in dugumler:
        turler[d.tur] = turler.get(d.tur, 0) + 1
    tam = sum(1 for d in dugumler if d.dogrulama == "tam")
    sat += ["", f"Toplam {len(dugumler)} düğüm — " +
            " · ".join(f"{k}: {v}" for k, v in sorted(turler.items())) +
            f" · tam satır: {tam}/{len(dugumler)}", ""]
    return "\n".join(sat)


def dosyayi_dogrula(mmd_yolu, kok=KOK, tablo=False, taban=None, kaynak=None):
    """taban None → eski davranış ve çıktı AYNEN; git-ref → + kapsam denetimi."""
    metin = mmd_yolu.read_text(encoding="utf-8")
    dugumler, hatalar, baslik = dogrula_metin(metin, kok)
    harf = mmd_yolu.stem.replace("akis_", "")
    tam = sum(1 for d in dugumler if d.dogrulama == "tam")
    print(f"{mmd_yolu.relative_to(kok)}: {len(dugumler)} düğüm · "
          f"{len(dugumler) - sum(1 for d in dugumler if d.dogrulama is None)} tuttu · "
          f"tam satır {tam} · hata {len(hatalar)}")
    for h in hatalar:
        print(f"  HATA: {h}")
    kapsam_hatalari = []
    if taban is not None:
        k, yeni, kapsam_hatalari, var = mmd_kapsam_denetle(mmd_yolu, dugumler, kok,
                                                           taban, kaynak)
        degisti = sum(1 for h in kapsam_hatalari if h.startswith("KAPSAM DEGISTI"))
        print(f"  kapsam (taban {taban}): {k} düğüm karşılaştırıldı · tabanda yok {yeni}"
              + ("" if var else " (tabanda .mmd YOK)")
              + f" · KAPSAM DEGISTI {degisti} · kapsam hatası {len(kapsam_hatalari)}")
        for h in kapsam_hatalari:
            print(f"  {h}")
    if tablo and not hatalar and not kapsam_hatalari:
        cikti = mmd_yolu.with_name(f"akis_{harf}_dugumler.md")
        cikti.write_text(tablo_uret(harf, dugumler, baslik), encoding="utf-8")
        print(f"  tablo: {cikti.relative_to(kok)}")
    return len(hatalar) == 0 and not kapsam_hatalari


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mmd", type=Path, action="append",
                    help="yalnız bu .mmd (tekrarlanabilir); verilmezse 5 diyagram")
    ap.add_argument("--tablo", action="store_true",
                    help="hatasız diyagramlar için akis_<x>_dugumler.md yaz")
    ap.add_argument("--taban", metavar="GIT_REF",
                    help="kapsam denetimi: her düğümün tabandaki (git show REF) "
                         "kapsamı (qualname) korunmuş mu; değişen → KAPSAM DEGISTI, çıkış 1")
    args = ap.parse_args(argv)
    yollar = args.mmd or [SEKILLER / f"akis_{h}.mmd" for h in DIYAGRAMLAR]
    eksik = [y for y in yollar if not y.is_file()]
    if eksik:
        for y in eksik:
            print(f"DOSYA YOK: {y}")
        return 2
    kaynak = None
    if args.taban is not None:
        sha = taban_ref_coz(args.taban, KOK)
        if sha is None:
            print(f"TABAN GEÇERSİZ: {args.taban!r} bir commit değil")
            return 2
        print(f"kapsam tabanı: {args.taban} = {sha[:12]}")
        kaynak = KapsamKaynagi(Path(KOK).resolve())
    sonuc = [dosyayi_dogrula(y, KOK, args.tablo, args.taban, kaynak) for y in yollar]
    print("SONUÇ:", "TÜM DÜĞÜMLER TUTTU" if all(sonuc) else "HATA VAR")
    return 0 if all(sonuc) else 1


if __name__ == "__main__":
    raise SystemExit(main())
