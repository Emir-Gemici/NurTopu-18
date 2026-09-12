# -*- coding: utf-8 -*-
"""T240-C (D-465) — ESITLIK yuzeyi ile YOKLUK/AYIKLAMA yuzeyini YAN YANA olcer.

NEDEN VAR: D-465'in mimar gerekcesi "YOKLUK denetiminin kacis yuzeyi SONSUZDUR,
ESITLIK denetiminin kacis yuzeyi YOKTUR" hukmudur. Bu hukum bir IDDIA olarak
degil, OLCUM olarak durmalidir: ayni hukum ALTI ayri sozdizimiyle gizlenir ve
her iki yuzeyin ne yaptigi tek tabloda basilir.

Ayrica D-465 (4) SINIR LISTESI'nin sayilari buradan gelir: hangi gizleme
biciminin cizik taramasinca GORULDUGU, hangisinin YALNIZ esitlikce goruldugu.

Kullanim (depo kokunden):
  O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B \\
      results/fdr_sprint_20260910/T240/sinir_olcumu.py
Cikis 0 = her gizleme bicimini ESITLIK yakaladi (beklenen hukum).
"""

import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(KOK / "tests"))
import belge_kilidi as bk  # noqa: E402

#: Taban: kucuk ama GERCEK yapiyi tasiyan bir kabul yuzeyi (baslik + madde + tablo).
TABAN = ("## 4. Kabul\n"
         "\n"
         "- **T236 kapısı:** yatay **≤ 2,0 m**, zamanın **≥ %90**'ında.\n"
         "\n"
         "| alan | kural |\n"
         "|---|---|\n"
         "| kaynak | zorunlu |\n")
HEDEF = "| kaynak | zorunlu |"

#: (ad, yerine konan metin) — ayni hukmun ALTI ayri gizleme bicimi.
GIZLEMELER = (
    ("~~ cift tilde", "| kaynak | ~~zorunlu~~ |"),
    ("<s> etiketi", "| kaynak | <s>zorunlu</s> |"),
    ("&#822; varlik cizgisi", "| kaynak | z&#822;o&#822;runlu |"),
    ("&#96; sarmali sahte kod araligi", "| kaynak | &#96;~~zorunlu~~&#96; |"),
    ("&amp;#96; cift kacisli varlik", "| kaynak | &amp;#96;~~zorunlu~~&amp;#96; |"),
    ("HTML yorumu", "| kaynak | <!-- zorunlu --> |"),
    ("markdown baglantisi", "| kaynak | [zorunlu](#) |"),
    ("sifir genislikli karakter", "| kaynak | zorun\u200blu |"),
    ("U+0333 birlesen cift alt cizgi", "| kaynak | " + "".join(
        h + "\u0333" for h in "zorunlu") + " |"),
)

#: MESRU duzenleme: bosluk/satir sonu hukmun anlami DEGILDIR — esitligi BOZMAMALI.
MESRU = (
    ("satir sarmasi", TABAN.replace("yatay **≤ 2,0 m**, zamanın",
                                    "yatay **≤ 2,0 m**,\n  zamanın", 1)),
    ("cift bosluk", TABAN.replace("| kaynak | zorunlu |", "|  kaynak  |  zorunlu  |", 1)),
)


#: K1'in ikinci yarisinin OLCUMU: bu dort belgede kod ARALIKLARI DISINDA mesru
#: HTML varligi var mi? (A) yolunun bedeli — yapi ureten varliklari dogrudan HATA
#: saymak — ancak bu sayi SIFIRSA yanlis pozitif uretmez.
KILITLI_BELGELER = (
    "CONTRACTS.md",
    "jetson_paket/gosterici/GOSTERICI_KURULUM.md",
    "config/pixhawk/README.md",
    "results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md",
)


def varlik_olcumu():
    """Her belgede kod DISINDAKI varlik adaylarini, cozulenleri ve YAPI URETENLERI sayar."""
    import html as _html
    print("## K1 OLCUMU — kod ARALIKLARI DISINDA HTML varligi")
    print()
    print("| belge | kod disi varlik | cozulen | YAPI ureten |")
    print("|---|---|---|---|")
    temiz = True
    for goreli in KILITLI_BELGELER:
        metin = KOK.joinpath(goreli).read_text(encoding="utf-8")
        kod = bk._kod_araliklari(metin)
        dis = [m.group(0) for m in bk._VARLIK.finditer(metin)
               if not any(kb <= m.start() and m.end() <= ks for kb, ks in kod)]
        coz = [v for v in dis if _html.unescape(v) != v]
        yapi = [v for v in coz if set(_html.unescape(v)) & bk._COZULMEZ]
        temiz &= not yapi
        print("| `{}` | {} | {} | {} |".format(
            goreli, len(dis), len(coz), len(yapi)))
    print()
    return temiz


def main():
    taban_blok = bk.bloklar(TABAN)
    print("# T240-C — ESITLIK vs YOKLUK/AYIKLAMA (D-465 gerekcesinin OLCUMU)")
    print("# taban blok sayisi: {}".format(len(taban_blok)))
    print()
    print("| gizleme bicimi | beyaz_liste_disi_cizik hata | ayiklama hukmu DUSURDU |"
          " ESITLIK DUSURDU |")
    print("|---|---|---|---|")
    tamam = True
    for ad, yeni in GIZLEMELER:
        metin = TABAN.replace(HEDEF, yeni, 1)
        cizik = len(bk.beyaz_liste_disi_cizik(metin))
        ayiklama_dusurdu = "zorunlu" not in bk.cizikleri_ayikla(metin)
        esitlik_dusurdu = bk.bloklar(metin) != taban_blok
        tamam &= esitlik_dusurdu
        print("| {} | {} | {} | {} |".format(
            ad, cizik, "EVET" if ayiklama_dusurdu else "hayir",
            "**EVET**" if esitlik_dusurdu else "HAYIR"))
    print()
    print("## MESRU duzenleme (esitligi BOZMAMALI — bosluk hukmun anlami degildir)")
    print()
    for ad, metin in MESRU:
        ayni = bk.bloklar(metin) == taban_blok
        tamam &= ayni
        print("  {:<22} esitlik KORUNDU={}".format(ad, ayni))
    print()
    tamam &= varlik_olcumu()
    print("HUKUM: {}".format(
        "her gizleme ESITLIKCE yakalandi, mesru duzenleme yanlis pozitif uretmedi, "
        "kilitli belgelerde kod disi YAPI VARLIGI yok"
        if tamam else "BOZUK"))
    return 0 if tamam else 1


if __name__ == "__main__":
    sys.exit(main())
