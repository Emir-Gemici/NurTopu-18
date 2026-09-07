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

Kullanım:
  python scripts/akis_diyagram_dogrula.py            # 5 diyagramı doğrula
  python scripts/akis_diyagram_dogrula.py --tablo    # + akis_<x>_dugumler.md yaz
  python scripts/akis_diyagram_dogrula.py --mmd FDR/sekiller/akis_a.mmd
Çıkış: 0 tüm düğümler tuttu · 1 en az bir hata · 2 dosya yok
"""

import argparse
import html
import re
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


def dosyayi_dogrula(mmd_yolu, kok=KOK, tablo=False):
    metin = mmd_yolu.read_text(encoding="utf-8")
    dugumler, hatalar, baslik = dogrula_metin(metin, kok)
    harf = mmd_yolu.stem.replace("akis_", "")
    tam = sum(1 for d in dugumler if d.dogrulama == "tam")
    print(f"{mmd_yolu.relative_to(kok)}: {len(dugumler)} düğüm · "
          f"{len(dugumler) - sum(1 for d in dugumler if d.dogrulama is None)} tuttu · "
          f"tam satır {tam} · hata {len(hatalar)}")
    for h in hatalar:
        print(f"  HATA: {h}")
    if tablo and not hatalar:
        cikti = mmd_yolu.with_name(f"akis_{harf}_dugumler.md")
        cikti.write_text(tablo_uret(harf, dugumler, baslik), encoding="utf-8")
        print(f"  tablo: {cikti.relative_to(kok)}")
    return len(hatalar) == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--mmd", type=Path, action="append",
                    help="yalnız bu .mmd (tekrarlanabilir); verilmezse 5 diyagram")
    ap.add_argument("--tablo", action="store_true",
                    help="hatasız diyagramlar için akis_<x>_dugumler.md yaz")
    args = ap.parse_args(argv)
    yollar = args.mmd or [SEKILLER / f"akis_{h}.mmd" for h in DIYAGRAMLAR]
    eksik = [y for y in yollar if not y.is_file()]
    if eksik:
        for y in eksik:
            print(f"DOSYA YOK: {y}")
        return 2
    sonuc = [dosyayi_dogrula(y, KOK, args.tablo) for y in yollar]
    print("SONUÇ:", "TÜM DÜĞÜMLER TUTTU" if all(sonuc) else "HATA VAR")
    return 0 if all(sonuc) else 1


if __name__ == "__main__":
    raise SystemExit(main())
