# -*- coding: utf-8 -*-
"""DEPO DENETIMI — hangi belge kilitleri ORTAK yardimcidan gecmiyor? (T240, D-460 karar 2)

NEDEN: D-460 denetimi uc test dosyasinda AYNI kusuru buldu — her biri cizik
ayiklamasini kendi yazmisti ve ucu de yalniz `~~...~~` biliyordu. Ayni kacis
sinifinin baska testlerde de acik durup durmadigi OLCULMEDEN bilinemez.

Bu betik `tests/` altinda markdown okuyup DIZGE arayan (yani belge kilidi olan)
her test dosyasini bulur ve `tests/belge_kilidi.py` yardimcisini KULLANMAYANLARI
raporlar. KAPI DEGILDIR: cikis her zaman 0'dir, cunku her markdown dizgesi bir
HUKUM kilidi degildir (yol adi, komut ornegi, baslik navigasyonu olabilir).
Rapor, hangi kilitlerin hala delinebilir oldugunu GORUNUR kilar.

Yontem (AST, salt okuma):
  1. Dosyada `.md` gecen bir yol sabiti / dizge var mi (markdown okuyor mu)?
  2. `read_text` / `open(...).read()` cagrisi var mi?
  3. `assertIn` / `assertNotIn` / `in` karsilastirmasi / `re.search|findall|match`
     ile metin taraniyor mu?
  4. `import belge_kilidi` (ya da `from belge_kilidi import ...`) var mi?
Dortten ilk uc tutup dorduncu tutmuyorsa: ACIK KILIT.

Kullanim (depo kokunden):
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B scripts/belge_kilidi_denetle.py
  [--rapor results/fdr_sprint_20260910/T240/acik_kilitler.md]
"""

import argparse
import ast
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
TESTLER = KOK / "tests"
YARDIMCI = "belge_kilidi"

OKUMA = {"read_text", "read", "readlines"}
TARAMA_CAGRI = {"assertIn", "assertNotIn", "assertRegex", "assertNotRegex",
                "search", "findall", "match", "finditer", "count", "index", "find"}
#: cizik ayiklamasini KENDI yazan testin izi — yardimci kullanilmiyorsa agir uyari
KENDI_CIZIK_IZI = ("~~", "<del", "<s>", "<strike", "strikethrough")

#: D-465 (3): YONTEM SINIFLANDIRMASI. Mimar karari 12 Eylul — olcum HUKMU tasiyan
#: yuzeyler ON KAYITLI METIN ESITLIGINE cevrilir (kacis yuzeyi YOKTUR); ayiklamali
#: kilitler yalniz DUSUK DEGERLI yuzeylerde (uzun anlati) kalir ve orada YOKLUK degil
#: VARLIK denetimi yapar. Bu rapor hangi dosyanin hangi sinifta oldugunu OLCER.
ESITLIK_YORDAMLARI = ("bloklar", "on_kayitli_metin_esit")
AYIKLAMA_YORDAMLARI = ("cizikleri_ayikla",)
DIGER_YORDAMLAR = ("beyaz_liste_disi_cizik", "normalize", "olumlu_hukum_var",
                   "hukum_cumleleri", "kabul_olcutu_tekligi")
YORDAMLAR = ESITLIK_YORDAMLARI + AYIKLAMA_YORDAMLARI + DIGER_YORDAMLAR


class Tarayici(ast.NodeVisitor):
    def __init__(self):
        self.md = False
        self.okuma = False
        self.tarama = set()
        self.yardimci = False
        self.kendi_cizik = set()
        self.yordam = set()

    def visit_Import(self, d):
        for a in d.names:
            if a.name.split(".")[0] == YARDIMCI:
                self.yardimci = True
        self.generic_visit(d)

    def visit_ImportFrom(self, d):
        if (d.module or "").split(".")[0] == YARDIMCI:
            self.yardimci = True
            for a in d.names:
                if a.name in YORDAMLAR:
                    self.yordam.add(a.name)
        self.generic_visit(d)

    def visit_Name(self, d):
        if d.id in YORDAMLAR:
            self.yordam.add(d.id)
        self.generic_visit(d)

    def visit_Constant(self, d):
        if isinstance(d.value, str):
            if d.value.endswith(".md") or ".md" in d.value:
                self.md = True
            for iz in KENDI_CIZIK_IZI:
                if iz in d.value:
                    self.kendi_cizik.add(iz)
        self.generic_visit(d)

    def visit_Attribute(self, d):
        if d.attr in OKUMA:
            self.okuma = True
        if d.attr in YORDAMLAR:
            self.yordam.add(d.attr)
        self.generic_visit(d)

    def visit_Call(self, d):
        ad = getattr(d.func, "attr", None) or getattr(d.func, "id", None)
        if ad in OKUMA:
            self.okuma = True
        if ad in TARAMA_CAGRI:
            self.tarama.add(ad)
        self.generic_visit(d)

    def visit_Compare(self, d):
        for op in d.ops:
            if isinstance(op, (ast.In, ast.NotIn)):
                self.tarama.add("in")
        self.generic_visit(d)


def denetle(yol):
    kaynak = yol.read_text(encoding="utf-8")
    try:
        agac = ast.parse(kaynak, filename=str(yol))
    except SyntaxError as e:                       # pragma: no cover (olmamali)
        return {"ad": yol.name, "hata": str(e)}
    t = Tarayici()
    t.visit(agac)
    return {"ad": yol.name, "md": t.md, "okuma": t.okuma, "tarama": sorted(t.tarama),
            "yardimci": t.yardimci, "kendi_cizik": sorted(t.kendi_cizik),
            "yordam": sorted(t.yordam)}


def main(argv=None):
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("--rapor", default=None, help="markdown rapor dosyasi")
    n = a.parse_args(argv)

    kayitlar = [denetle(y) for y in sorted(TESTLER.glob("*.py"))
                if y.name != "belge_kilidi.py"]
    kilitli = [k for k in kayitlar if k.get("md") and k.get("okuma") and k.get("tarama")]
    gecen = [k for k in kilitli if k["yardimci"]]
    acik = [k for k in kilitli if not k["yardimci"]]
    riskli = [k for k in acik if k["kendi_cizik"]]

    satirlar = []

    def yaz(s=""):
        satirlar.append(s)

    yaz("# Belge kilidi denetimi — ACIK KILITLER (T240, D-460 karar 2)")
    yaz()
    yaz("Uretici: `scripts/belge_kilidi_denetle.py` (salt okuma, AST). **KAPI DEGILDIR** —")
    yaz("cikis her zaman 0. Her markdown dizgesi bir HUKUM kilidi degildir; liste,")
    yaz("`tests/belge_kilidi.py` ortak yardimcisindan GECMEYEN belge taramalarini gorunur kilar.")
    yaz()
    yaz("| olcum | deger |")
    yaz("|---|---|")
    yaz("| taranan test dosyasi | {} |".format(len(kayitlar)))
    yaz("| markdown okuyup dizge arayan | {} |".format(len(kilitli)))
    yaz("| ortak yardimcidan GECEN | {} |".format(len(gecen)))
    yaz("| ACIK (yardimci kullanmayan) | {} |".format(len(acik)))
    yaz("| ACIK **ve** kendi cizik kalibi olan (agir) | {} |".format(len(riskli)))
    esitlikli = [k for k in gecen if set(k["yordam"]) & set(ESITLIK_YORDAMLARI)]
    blokcu = [k for k in gecen if "bloklar" in k["yordam"]]
    yaz("| GECENLERDEN on kayitli METIN ESITLIGI kullanan (D-465) | {} |".format(len(esitlikli)))
    yaz("| GECENLERDEN BLOK esitligi (`bloklar`) kullanan (D-465 (1)) | {} |".format(len(blokcu)))
    yaz()
    yaz("## 1. Ortak yardimcidan gecenler — YONTEM SINIFI (D-465 (3))")
    yaz()
    yaz("D-465 (mimar karari, 12 Eylul): olcum HUKMU tasiyan yuzeyler ON KAYITLI METIN")
    yaz("ESITLIGINE cevrilir — YOKLUK denetiminin kacis yuzeyi SONSUZ, ESITLIGIN kacis")
    yaz("yuzeyi YOKTUR. Ayiklamali kilitler yalniz DUSUK DEGERLI yuzeylerde kalir ve")
    yaz("orada YOKLUK degil VARLIK denetimi yapar.")
    yaz()
    yaz("| test | ESITLIK | ayiklama | diger yordamlar |")
    yaz("|---|---|---|---|")
    for k in gecen:
        es = [y for y in k["yordam"] if y in ESITLIK_YORDAMLARI]
        ay = [y for y in k["yordam"] if y in AYIKLAMA_YORDAMLARI]
        dg = [y for y in k["yordam"] if y in DIGER_YORDAMLAR]
        yaz("| `tests/{}` | {} | {} | {} |".format(
            k["ad"],
            ", ".join("`{}`".format(x) for x in es) or "—",
            ", ".join("`{}`".format(x) for x in ay) or "—",
            ", ".join("`{}`".format(x) for x in dg) or "—"))
    if not gecen:
        yaz("| (yok) | | | |")
    yaz()
    yaz("## 2. ACIK kilitler — kendi cizik/hukum kalibini tasiyanlar (once bunlar)")
    yaz()
    yaz("Bu dosyalar markdown okuyup dizge ariyor **ve** kaynaginda cizme sozdizimi gecen bir")
    yaz("sabit var: D-460'ta olculen kacis sinifina (`~~` disindaki cizikler) acik olabilirler.")
    yaz()
    if riskli:
        yaz("| test | kendi cizik izi | tarama |")
        yaz("|---|---|---|")
        for k in riskli:
            yaz("| `tests/{}` | {} | {} |".format(
                k["ad"], ", ".join("`{}`".format(x) for x in k["kendi_cizik"]),
                ", ".join("`{}`".format(x) for x in k["tarama"][:5])))
    else:
        yaz("- (yok)")
    yaz()
    yaz("## 3. ACIK kilitler — digerleri")
    yaz()
    yaz("Cogu yol adi / komut ornegi / baslik navigasyonu olabilir; hukum kilidi olanlar")
    yaz("ayri ayri incelenip yardimciya gecirilmelidir.")
    yaz()
    yaz("| test | tarama cagrilari |")
    yaz("|---|---|")
    for k in acik:
        if k in riskli:
            continue
        yaz("| `tests/{}` | {} |".format(
            k["ad"], ", ".join("`{}`".format(x) for x in k["tarama"][:6])))
    yaz()

    metin = "\n".join(satirlar) + "\n"
    print(metin)
    if n.rapor:
        y = Path(n.rapor)
        if not y.is_absolute():
            y = KOK / y
        y.parent.mkdir(parents=True, exist_ok=True)
        y.write_text(metin, encoding="utf-8")
        print("rapor yazildi: {}".format(y))
    return 0


if __name__ == "__main__":
    sys.exit(main())
