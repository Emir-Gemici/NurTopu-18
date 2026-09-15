#!/usr/bin/env python3
"""FDR final sunumunu resmî TEKNOFEST şablonundan üretir (T259).

NEDEN: Sunumun teknik içeriği FDR'nin ölçülmüş çekirdeğinden gelir; elle
PowerPoint'te yazılan slaytın kaynağı yoktur, sayısı denetlenemez ve
ÖLÇÜLDÜ/ÖLÇÜLEMEDİ etiketi sessizce düşer. Bu betik içeriği tek bir veri
dosyasından (`results/sunum_20260913/icerik.json`) okur, resmî şablonu
(`FDR/sablon/TEKNOFEST_2026_IOS_Final_Sunum_Sablonu.pptx`) BOZMADAN doldurur
ve yanına düz metin dökümü basar. Nöbetçi `tests/test_sunum_kanit.py` o düz
metin üzerinden her sayıyı kaynağına bağlar.

Şablon kuralları (şablonun kendi notları):
  * Kapak sayfası düzeni değiştirilmez — yalnız metin alanları doldurulur.
    Kapaktaki "(Bu açıklama silinmelidir.)" kutusu şablonun kendi talimatıdır;
    `--aciklamayi-koru` verilmedikçe SİLİNİR.
  * İçerik slaytları şablonun 3. slaydı (boş içerik düzeni) çoğaltılarak üretilir;
    altlıktaki "... SEVİYESİ FİNAL SUNUMU" şeridi korunur. `meta.seviye` verilirse
    noktalı alan doldurulur, verilmezse ELLE doldurulmak üzere aynen bırakılır.
  * TEŞEKKÜRLER slaydı her zaman en sona taşınır.

Kaynak (`kaynak` alanı) slayta BASILMAZ, konuşmacı notuna yazılır: jüri slaytta
dosya:satır görmemeli, ama iddia kaynaksız kalmamalı.

Kullanım:
  python scripts/sunum_uret.py                     # icerik.json -> pptx + metin
  python scripts/sunum_uret.py --kontrol           # yalnız şema denetimi, yazma yok
  python scripts/sunum_uret.py --icerik <yol> --cikti-dizin <yol>
Çıkış: 0 üretildi · 1 hatalı çağrı/eksik dosya/şema hatası · 2 python-pptx yok
"""

import argparse
import copy
import datetime as dt
import json
import re
import sys
from pathlib import Path

for _a in (sys.stdout, sys.stderr):
    try:
        _a.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
VARSAYILAN_ICERIK = KOK / "results" / "sunum_20260913" / "icerik.json"
SABLON = KOK / "FDR" / "sablon" / "TEKNOFEST_2026_IOS_Final_Sunum_Sablonu.pptx"
VARSAYILAN_CIKTI = KOK / "FDR" / "sunum"

VENV_ONERISI = ("/tmp/claude-1000/-home-trs-projects-navitas-unified-20260822/"
                "0082bcda-c2f1-4e69-8683-8439e9578f36/scratchpad/sunumvenv/bin/python")

# Şablondaki yazı tipleri. Bu adlar makinede yoksa görüntüleyici kendi yedeğine
# düşer — dosya yine geçerlidir, yalnız görünüm değişir.
YAZI_BASLIK = "Active Heart"
YAZI_GOVDE = "Aileron"

ETIKET_ADI = {"OLCULDU": "ÖLÇÜLDÜ", "OLCULEMEDI": "ÖLÇÜLEMEDİ", "BEYAN": "BEYAN"}
GECERLI_TIPLER = {"kapak", "takim", "icerik", "tesekkur"}

# Kapak slaydındaki etiketler (şablon metniyle birebir; \xa0 dahil).
KAPAK_ALANLARI = [
    ("PROJE ADI:", "proje_adi"),
    ("KONU BAŞLIĞI:", "konu_basligi"),
    ("TAKIM ADI:", "takim_adi"),
    ("TAKIM ID:", "takim_id"),
    ("BAŞVURU ID:", "basvuru_id"),
]
KAPAK_ACIKLAMA_IZI = "açıklama"          # silinecek kutunun tanınma izi
KAPAK_ACIKLAMA_IZI2 = "kapak"

# Takım slaydındaki kutu etiketleri → içerik maddesinin anahtar kelimesi.
TAKIM_KUTULARI = [
    ("TAKIM DANIŞMANI", ("danışman", "danisman")),
    ("TAKIM KAPTANI", ("kaptan",)),
    ("ÜYE 1", ("üye 1", "uye 1")),
    ("ÜYE 2", ("üye 2", "uye 2")),
    ("ÜYE 3", ("üye 3", "uye 3")),
    ("ÜYE 4", ("üye 4", "uye 4")),
    ("ÜYE 5", ("üye 5", "uye 5")),
]

ZORUNLU_META = ["proje_adi", "konu_basligi", "takim_adi", "takim_id",
                "basvuru_id", "tarih", "sure_dk"]


class SemaHatasi(Exception):
    """icerik.json sözleşmeye uymuyor."""


# ─────────────────────────── şema ───────────────────────────

def sema_dogrula(veri):
    """icerik.json'u denetler; hata listesi döndürür (boş liste = geçerli)."""
    hatalar = []
    if not isinstance(veri, dict):
        return ["kök nesne bir sözlük değil"]

    meta = veri.get("meta")
    if not isinstance(meta, dict):
        hatalar.append("meta yok ya da sözlük değil")
    else:
        for alan in ZORUNLU_META:
            if alan not in meta:
                hatalar.append(f"meta.{alan} yok")
            elif alan != "sure_dk" and not isinstance(meta[alan], str):
                hatalar.append(f"meta.{alan} metin değil")
        if "sure_dk" in meta and not isinstance(meta["sure_dk"], (int, float)):
            hatalar.append("meta.sure_dk sayı değil")

    slaytlar = veri.get("slaytlar")
    if not isinstance(slaytlar, list) or not slaytlar:
        hatalar.append("slaytlar yok ya da boş liste")
        return hatalar

    gorulen_no = set()
    for i, s in enumerate(slaytlar):
        yer = f"slaytlar[{i}]"
        if not isinstance(s, dict):
            hatalar.append(f"{yer} sözlük değil")
            continue
        no = s.get("no")
        if not isinstance(no, int):
            hatalar.append(f"{yer}.no tamsayı değil")
        elif no in gorulen_no:
            hatalar.append(f"{yer}.no yinelenmiş: {no}")
        else:
            gorulen_no.add(no)
        tip = s.get("tip")
        if tip not in GECERLI_TIPLER:
            hatalar.append(f"{yer}.tip geçersiz: {tip!r} (geçerli: {sorted(GECERLI_TIPLER)})")
        if not isinstance(s.get("baslik", ""), str):
            hatalar.append(f"{yer}.baslik metin değil")
        if not isinstance(s.get("not", ""), str):
            hatalar.append(f"{yer}.not metin değil")

        maddeler = s.get("maddeler", [])
        if not isinstance(maddeler, list):
            hatalar.append(f"{yer}.maddeler liste değil")
        else:
            for j, m in enumerate(maddeler):
                myer = f"{yer}.maddeler[{j}]"
                if not isinstance(m, dict):
                    hatalar.append(f"{myer} sözlük değil")
                    continue
                if not isinstance(m.get("metin"), str) or not m.get("metin").strip():
                    hatalar.append(f"{myer}.metin boş ya da metin değil")
                et = m.get("etiket")
                if et is not None and et not in ETIKET_ADI:
                    hatalar.append(f"{myer}.etiket geçersiz: {et!r}")
                kay = m.get("kaynak")
                if kay is not None:
                    if not isinstance(kay, str):
                        hatalar.append(f"{myer}.kaynak metin değil")
                    elif not re.match(r"^[^:]+:\d+$", kay):
                        hatalar.append(f"{myer}.kaynak 'dosya:satır' biçiminde değil: {kay!r}")

        tablo = s.get("tablo")
        if tablo is not None:
            if not isinstance(tablo, dict):
                hatalar.append(f"{yer}.tablo sözlük değil")
            else:
                bas = tablo.get("basliklar")
                sat = tablo.get("satirlar")
                if not isinstance(bas, list) or not bas or not all(isinstance(b, str) for b in bas):
                    hatalar.append(f"{yer}.tablo.basliklar metin listesi değil")
                if not isinstance(sat, list) or not sat:
                    hatalar.append(f"{yer}.tablo.satirlar liste değil ya da boş")
                elif isinstance(bas, list):
                    for k, satir in enumerate(sat):
                        if not isinstance(satir, list) or len(satir) != len(bas):
                            hatalar.append(
                                f"{yer}.tablo.satirlar[{k}] sütun sayısı başlıklarla uyuşmuyor")
    return hatalar


# ─────────────────────────── düz metin dökümü ───────────────────────────

def metin_dokumu(veri):
    """sunum_metin.txt içeriğini üretir (nöbetçi testin girdisi)."""
    meta = veri["meta"]
    sat = [
        "# NAVITAS — FDR FİNAL SUNUMU (metin dökümü)",
        f"# üreten: scripts/sunum_uret.py · tarih: {meta.get('tarih', '')}"
        f" · süre: {meta.get('sure_dk', '')} dk",
        "# Bu dosya türev üründür; kaynak results/sunum_20260913/icerik.json",
        "",
    ]
    for s in veri["slaytlar"]:
        sat.append(f"## {s['no']} {s.get('baslik', '')}".rstrip())
        for m in s.get("maddeler", []):
            parca = f"- {m['metin']}"
            if m.get("etiket"):
                parca += f" [{ETIKET_ADI[m['etiket']]}]"
            if m.get("kaynak"):
                parca += f" ({m['kaynak']})"
            sat.append(parca)
        tablo = s.get("tablo")
        if tablo:
            sat.append("| " + " | ".join(tablo["basliklar"]) + " |")
            for satir in tablo["satirlar"]:
                sat.append("| " + " | ".join(str(h) for h in satir) + " |")
        if s.get("not"):
            sat.append(f"NOT: {s['not']}")
        sat.append("")
    return "\n".join(sat).rstrip() + "\n"


# ─────────────────────────── pptx yardımcıları ───────────────────────────

def _metin_kutulari(slayt):
    return [sh for sh in slayt.shapes if sh.has_text_frame]


def _kutu_bul(slayt, iz):
    """Metni `iz` ile başlayan/`iz` içeren ilk kutuyu döndürür."""
    iz_k = iz.casefold()
    for sh in _metin_kutulari(slayt):
        if iz_k in sh.text_frame.text.casefold():
            return sh
    return None


def _kapak_doldur(slayt, meta, aciklamayi_koru):
    """Kapakta yalnız metin alanlarını doldurur; düzen değişmez."""
    yazilan = []
    for sh in _metin_kutulari(slayt):
        for para in sh.text_frame.paragraphs:
            if not para.runs:
                continue
            ham = "".join(r.text for r in para.runs)
            for etiket, anahtar in KAPAK_ALANLARI:
                if ham.strip().startswith(etiket):
                    deger = str(meta.get(anahtar, "")).strip()
                    # İlk run'a yaz, kalan run'ları boşalt (biçim ilk run'dan gelir).
                    para.runs[0].text = f"{etiket} {deger}".rstrip()
                    for r in para.runs[1:]:
                        r.text = ""
                    yazilan.append(etiket)
                    break
    if not aciklamayi_koru:
        # Şablonun kendi talimatı: "(Bu açıklama silinmelidir.)"
        for sh in list(_metin_kutulari(slayt)):
            t = sh.text_frame.text.casefold()
            if KAPAK_ACIKLAMA_IZI in t and KAPAK_ACIKLAMA_IZI2 in t and "silinmelidir" in t:
                sh._element.getparent().remove(sh._element)
                yazilan.append("(açıklama kutusu silindi)")
    return yazilan


def _takim_doldur(slayt, maddeler):
    """Takım kutularını maddelerle doldurur; eşleşme anahtar kelimeyle, yoksa sırayla."""
    kalan = list(maddeler)
    yazilan = []
    for etiket, anahtarlar in TAKIM_KUTULARI:
        kutu = _kutu_bul(slayt, etiket)
        if kutu is None:
            continue
        secilen = None
        for m in kalan:
            dusuk = m["metin"].casefold()
            if any(a in dusuk for a in anahtarlar):
                secilen = m
                break
        if secilen is None:
            continue
        kalan.remove(secilen)
        para = kutu.text_frame.paragraphs[0]
        if para.runs:
            para.runs[0].text = secilen["metin"]
            for r in para.runs[1:]:
                r.text = ""
        else:
            kutu.text_frame.text = secilen["metin"]
        yazilan.append(etiket)
    # Eşleşmeyen maddeler kaybolmasın: slayt notuna düşer (çağıran ekler).
    return yazilan, kalan


def _altlik_doldur(slayt, seviye, yarisma_adi):
    """'.......... SEVİYESİ' ve 'YARIŞMASI' şeridini doldurur (verilmişse)."""
    if not seviye and not yarisma_adi:
        return
    for sh in _metin_kutulari(slayt):
        for para in sh.text_frame.paragraphs:
            if not para.runs:
                continue
            for r in para.runs:
                if seviye and "........" in r.text:
                    r.text = re.sub(r"\.{3,}", seviye, r.text)
                if yarisma_adi and r.text.strip() == "YARIŞMASI":
                    r.text = f"{yarisma_adi} YARIŞMASI "


def _slayt_kopyala(prs, kaynak):
    """Şablon slaydının şekil ağacını yeni bir slayda kopyalar."""
    yeni = prs.slides.add_slide(kaynak.slide_layout)
    for sh in list(yeni.shapes):
        sh._element.getparent().remove(sh._element)
    for sh in kaynak.shapes:
        yeni.shapes._spTree.append(copy.deepcopy(sh._element))
    return yeni


def _slayt_tasi(prs, eski_idx, yeni_idx):
    lst = prs.slides._sldIdLst
    ogeler = list(lst)
    oge = ogeler[eski_idx]
    lst.remove(oge)
    lst.insert(yeni_idx, oge)


def _not_yaz(slayt, metin):
    if not metin:
        return
    slayt.notes_slide.notes_text_frame.text = metin


def _icerik_doldur(slayt, s, Inches, Pt):
    """Başlık + madde listesi (+ tablo) ekler. Şablonun altlığı yerinde kalır."""
    # Başlık
    kutu = slayt.shapes.add_textbox(Inches(1.10), Inches(0.45), Inches(17.8), Inches(1.15))
    tf = kutu.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = s.get("baslik", "")
    r.font.size = Pt(34)
    r.font.bold = True
    r.font.name = YAZI_BASLIK

    ust = 1.85
    maddeler = s.get("maddeler", [])
    if maddeler:
        yuk = 6.9 if not s.get("tablo") else 3.0
        gkutu = slayt.shapes.add_textbox(Inches(1.10), Inches(ust), Inches(17.8), Inches(yuk))
        gtf = gkutu.text_frame
        gtf.word_wrap = True
        for i, m in enumerate(maddeler):
            para = gtf.paragraphs[0] if i == 0 else gtf.add_paragraph()
            para.space_after = Pt(10)
            run = para.add_run()
            run.text = "• " + m["metin"]
            run.font.size = Pt(19)
            run.font.name = YAZI_GOVDE
            if m.get("etiket"):
                rozet = para.add_run()
                rozet.text = f"  [{ETIKET_ADI[m['etiket']]}]"
                rozet.font.size = Pt(16)
                rozet.font.bold = True
                rozet.font.name = YAZI_GOVDE
        ust += yuk + 0.15

    tablo = s.get("tablo")
    if tablo:
        sutun = len(tablo["basliklar"])
        satir = len(tablo["satirlar"]) + 1
        yuk = min(0.5 * satir, 10.4 - ust)
        gt = slayt.shapes.add_table(satir, sutun, Inches(1.10), Inches(ust),
                                    Inches(17.8), Inches(max(yuk, 0.8))).table
        for j, b in enumerate(tablo["basliklar"]):
            hucre = gt.cell(0, j)
            hucre.text = str(b)
            for para in hucre.text_frame.paragraphs:
                for r2 in para.runs:
                    r2.font.size = Pt(15)
                    r2.font.bold = True
                    r2.font.name = YAZI_GOVDE
        for i, sat in enumerate(tablo["satirlar"], start=1):
            for j, h in enumerate(sat):
                hucre = gt.cell(i, j)
                hucre.text = str(h)
                for para in hucre.text_frame.paragraphs:
                    for r2 in para.runs:
                        r2.font.size = Pt(14)
                        r2.font.name = YAZI_GOVDE


def _slayt_notu(s):
    """Konuşmacı notu: yazarın notu + kaynak listesi (slayta basılmaz)."""
    parcalar = []
    if s.get("not"):
        parcalar.append(s["not"])
    kaynaklar = [m["kaynak"] for m in s.get("maddeler", []) if m.get("kaynak")]
    if kaynaklar:
        parcalar.append("KAYNAKLAR:")
        parcalar.extend(f"  - {k}" for k in kaynaklar)
    return "\n".join(parcalar)


# ─────────────────────────── ana akış ───────────────────────────

def uret(veri, sablon_yolu, cikti_dizin, aciklamayi_koru=False):
    """pptx üretir; (pptx_yolu, metin_yolu, uyarilar) döndürür."""
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ModuleNotFoundError:
        print("HATA: python-pptx kurulu değil.", file=sys.stderr)
        print(f"  Öneri: {VENV_ONERISI} scripts/sunum_uret.py …", file=sys.stderr)
        print("  (o venv'de python-pptx 1.0.2 kurulu — ölçüldü)", file=sys.stderr)
        sys.exit(2)

    uyarilar = []
    prs = Presentation(str(sablon_yolu))
    if len(prs.slides) < 4:
        raise SemaHatasi(f"şablon beklenenden kısa: {len(prs.slides)} slayt (4 bekleniyor)")

    kapak_s, takim_s, icerik_sablon, tesekkur_s = (prs.slides[0], prs.slides[1],
                                                   prs.slides[2], prs.slides[3])
    meta = veri["meta"]

    veri_kapak = next((s for s in veri["slaytlar"] if s["tip"] == "kapak"), None)
    _kapak_doldur(kapak_s, meta, aciklamayi_koru)
    if veri_kapak:
        _not_yaz(kapak_s, _slayt_notu(veri_kapak))

    veri_takim = next((s for s in veri["slaytlar"] if s["tip"] == "takim"), None)
    if veri_takim:
        _, kalan = _takim_doldur(takim_s, veri_takim.get("maddeler", []))
        notu = _slayt_notu(veri_takim)
        if kalan:
            uyarilar.append(f"takım slaydında eşleşmeyen {len(kalan)} madde nota düştü")
            notu = (notu + "\nEŞLEŞMEYEN: "
                    + "; ".join(m["metin"] for m in kalan)).strip()
        _not_yaz(takim_s, notu)

    seviye = str(meta.get("seviye", "")).strip()
    yarisma = str(meta.get("yarisma_adi", "")).strip()
    if not seviye:
        uyarilar.append("meta.seviye yok — altlıktaki '.......... SEVİYESİ' ELLE doldurulacak")

    icerikler = [s for s in veri["slaytlar"] if s["tip"] == "icerik"]
    for s in icerikler:
        yeni = _slayt_kopyala(prs, icerik_sablon)
        _altlik_doldur(yeni, seviye, yarisma)
        _icerik_doldur(yeni, s, Inches, Pt)
        _not_yaz(yeni, _slayt_notu(s))

    for s in (kapak_s, takim_s, tesekkur_s):
        _altlik_doldur(s, seviye, yarisma)

    # Şablonun boş içerik kabuğunu (3. slayt) kaldır, TEŞEKKÜRLER'i sona taşı.
    lst = prs.slides._sldIdLst
    lst.remove(list(lst)[2])
    _slayt_tasi(prs, 2, len(list(lst)) - 1)   # eski 4. slayt artık 3. sırada

    veri_tesekkur = next((s for s in veri["slaytlar"] if s["tip"] == "tesekkur"), None)
    if veri_tesekkur:
        _not_yaz(tesekkur_s, _slayt_notu(veri_tesekkur))

    cikti_dizin.mkdir(parents=True, exist_ok=True)
    damga = dt.datetime.now().strftime("%Y%m%d")
    pptx_yolu = cikti_dizin / f"NAVITAS_FDR_SUNUM_{damga}.pptx"
    prs.save(str(pptx_yolu))

    metin_yolu = cikti_dizin / "sunum_metin.txt"
    metin_yolu.write_text(metin_dokumu(veri), encoding="utf-8")
    return pptx_yolu, metin_yolu, uyarilar


def main(argv=None):
    ap = argparse.ArgumentParser(description="FDR final sunumunu üretir (T259)")
    ap.add_argument("--icerik", type=Path, default=VARSAYILAN_ICERIK)
    ap.add_argument("--sablon", type=Path, default=SABLON)
    ap.add_argument("--cikti-dizin", type=Path, default=VARSAYILAN_CIKTI)
    ap.add_argument("--kontrol", action="store_true",
                    help="yalnız şemayı denetle, hiçbir şey yazma")
    ap.add_argument("--aciklamayi-koru", action="store_true",
                    help="kapaktaki '(Bu açıklama silinmelidir.)' kutusunu silme")
    a = ap.parse_args(argv)

    if not a.icerik.is_file():
        print(f"HATA: içerik dosyası yok: {a.icerik}", file=sys.stderr)
        return 1
    try:
        veri = json.loads(a.icerik.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"HATA: {a.icerik} geçerli JSON değil: {e}", file=sys.stderr)
        return 1

    hatalar = sema_dogrula(veri)
    if hatalar:
        print(f"ŞEMA HATASI ({len(hatalar)}):", file=sys.stderr)
        for h in hatalar:
            print(f"  - {h}", file=sys.stderr)
        return 1

    sayim = {}
    for s in veri["slaytlar"]:
        sayim[s["tip"]] = sayim.get(s["tip"], 0) + 1
    madde = sum(len(s.get("maddeler", [])) for s in veri["slaytlar"])
    etiketli = sum(1 for s in veri["slaytlar"] for m in s.get("maddeler", []) if m.get("etiket"))
    kaynakli = sum(1 for s in veri["slaytlar"] for m in s.get("maddeler", []) if m.get("kaynak"))
    olculemedi = sum(1 for s in veri["slaytlar"] for m in s.get("maddeler", [])
                     if m.get("etiket") == "OLCULEMEDI")
    insan = sum(1 for s in veri["slaytlar"] for m in s.get("maddeler", [])
                if "[İNSAN DOLDURACAK]" in m["metin"])
    insan += sum(1 for d in veri["meta"].values() if isinstance(d, str)
                 and "[İNSAN DOLDURACAK]" in d)

    print("ŞEMA: OK")
    print(f"  slayt: {len(veri['slaytlar'])} ({sayim})")
    print(f"  madde: {madde} · etiketli: {etiketli} · kaynaklı: {kaynakli}"
          f" · ÖLÇÜLEMEDİ: {olculemedi}")
    print(f"  [İNSAN DOLDURACAK] yer tutucu: {insan}")

    if a.kontrol:
        return 0

    if not a.sablon.is_file():
        print(f"HATA: şablon yok: {a.sablon}", file=sys.stderr)
        return 1
    try:
        pptx_yolu, metin_yolu, uyarilar = uret(veri, a.sablon, a.cikti_dizin,
                                               a.aciklamayi_koru)
    except SemaHatasi as e:
        print(f"HATA: {e}", file=sys.stderr)
        return 1
    for u in uyarilar:
        print(f"UYARI: {u}")
    print(f"YAZILDI: {pptx_yolu}")
    print(f"YAZILDI: {metin_yolu}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
