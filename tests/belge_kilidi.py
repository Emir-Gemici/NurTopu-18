# -*- coding: utf-8 -*-
"""Ortak belge kilidi yardimcisi — T240 (D-460 karar 2).

NEDEN VAR: bagimsiz mimar denetimi (D-460) uc isi (T226-D2 / T228-D2 / T221-D3)
REDDETTI. Ortak kusur tekti: her test dosyasi CIZIK ayiklamasini KENDI yazmisti ve
ucu de yalniz `~~...~~` biciminde ayikliyordu. Denetimde kurulan 19 gercek dosya
mutasyonunun 19'u da kacti (T226: 4, T228: 7, T221: 8). Kural tek yerden gelsin
diye butun belge kilitleri artik bu moduldeki yordamlardan gecer.

TASARIM KARARLARI (hepsi olculmus kacislara dayanir):
  1. KARA LISTE DEGIL BEYAZ LISTE. Cizme sozdizimi bitmez (`~~`, `~`, `<del>`,
     `<s>`, `<strike>`, `<span style=...line-through>`, birlesen U+0336 ...).
     `beyaz_liste_disi_cizik` metinde KALAN her cizme adayini bulur; tarihli-
     gerekceli beyaz listede olmayan her aday HATADIR. Boylece gelecekte cikacak
     yeni sozdizimi, buraya kalip eklenmeden yakalanir.
  2. KOD ICI METIN HARFI HARFINEDIR. Markdown'da ` ... ` ve ```...``` icindeki
     `~` ya da `<s>` cizgi degildir; kod araliklari once maskelenir.
  3. "~<rakam>" YAKLASIK ISARETIDIR, cizgi degil. Uc belgede (CONTRACTS.md,
     GOSTERICI_KURULUM.md, config/pixhawk/README.md) kod disinda kalan TEK tilde
     ornekleri olculdu: hepsi "~3 s", "~8 Hz", "~1,4 px" gibi yaklasik
     isaretleridir. Belgelenen tek istisna budur.
  4. OLCULEMEDI != GECTI. `olumlu_hukum_var` olumlu hukum ailesini
     NORMALLESTIRILMIS metinde arar; harf sinirlari `\\w` DEGILDIR (altcizgi `\\w`
     oldugu icin `_dogrulandi_` T221'de kilidi delmisti).
  5. ON KAYIT > KARA LISTE. `on_kayitli_metin_esit` bosluk-normalize tam
     esitliktir: bir hukum cumlesi ancak testteki sabitle BIRLIKTE, gorunur bir
     test degisikligiyle degisebilir.

Yalnizca standart kutuphane (CLAUDE.md madde 4).
"""

import re
import unicodedata

__all__ = ["cizikleri_ayikla", "beyaz_liste_disi_cizik", "normalize",
           "olumlu_hukum_var", "on_kayitli_metin_esit", "hukum_cumleleri",
           "HARF", "ZARARSIZ_ETIKETLER"]

# Turkce harfleri kapsayan, ALTCIZGIYI DISLAYAN harf sinifi.
# NEDEN: T221 kacani W3/W4 — `SITL_OLUMLU_HUKUM` sinirlari `(?<!\w)` idi; `_`
# Python'da `\w` oldugu icin `_dogrulandi_` ve `__kosuldu__` hic gorulmedi.
HARF = "0-9A-Za-zÀ-ɏĞğİıŞş"
_SINIR_ONCE = r"(?<![" + HARF + r"])"
_SINIR_SONRA = r"(?![" + HARF + r"])"

# Uzeri cizili RENDER EDEMEYEN, bu yuzden zararsiz sayilan HTML etiketleri.
# Listede olmayan HER etiket (ornegin uydurma bir `<sil>`, ya da stil tasiyabilen
# `<span>`) cizik adayidir — gelecekteki sozdizimi kalip eklemeden yakalanir.
ZARARSIZ_ETIKETLER = frozenset({"br", "sub", "sup", "kbd", "details", "summary",
                                "img", "hr", "wbr"})

# ── kod araliklari ────────────────────────────────────────────────────────────
_CIT = re.compile(r"(?ms)^[ \t]*```.*?^[ \t]*```[ \t]*$")
_SATIRICI_KOD = re.compile(r"`+[^`\n]*`+")


def _kod_araliklari(metin):
    """Markdown kod citleri ve satirici kod araliklarinin (bas, son) listesi.

    NEDEN: kod icindeki `~` (ornegin `~/navitas`) ya da `<s>` cizgi DEGILDIR;
    ayiklanirsa belge bozulur, cizik aranirsa yalanci alarm uretir.
    """
    araliklar = [m.span() for m in _CIT.finditer(metin)]
    for m in _SATIRICI_KOD.finditer(metin):
        if not any(b <= m.start() < s for b, s in araliklar):
            araliklar.append(m.span())
    return sorted(araliklar)


def _maskele(metin):
    """(maskelenmis_metin, parcalar): kod araliklari \\x00<n>\\x00 ile degistirilir."""
    parcalar, cikti, son = [], [], 0
    for b, s in _kod_araliklari(metin):
        parcalar.append(metin[b:s])
        cikti.append(metin[son:b])
        cikti.append("\x00{}\x00".format(len(parcalar) - 1))
        son = s
    cikti.append(metin[son:])
    return "".join(cikti), parcalar


def _coz(metin, parcalar):
    return re.sub(r"\x00(\d+)\x00", lambda m: parcalar[int(m.group(1))], metin)


# ── 1. cizik ayiklama ─────────────────────────────────────────────────────────
_CIFT_TILDE = re.compile(r"~~.*?~~", re.S)
# Tek tilde: GFM'de `~x~` de uzeri cizili uretir (T228 kacani A3, T221 kacani W1).
# Acilis tildesi rakamla BASLAYAMAZ (karar 3: "~3 s" yaklasiktir), bosluk ile
# baslayamaz/bitemez (GFM flanking kurali), aralik BOS SATIR asamaz (satir ici).
_TEK_TILDE = re.compile(
    r"(?<!~)~(?![~\d\s])(?:(?!\n[ \t]*\n)(?!~).)*?(?<![\s~])~(?![~\d])", re.S)
# HTML cizgisi (T226 kacanlari D1b/D1d, T228 kacanlari A4/A5).
_HTML_CIZGI = re.compile(r"<(del|s|strike)\b[^>]*>.*?</\1\s*>", re.S | re.I)


def cizikleri_ayikla(metin):
    """~~cizili~~ / ~cizili~ / <del|s|strike>cizili</...> araliklarini DUSURUR.

    NEDEN: kacan mutantlar — T226 D1b (<del>), D1c (tek tilde), D1d (<s>);
    T228 A3 (tek tilde), A4 (<del>), A5 (<s>); T221 W1/W6 (baslikta ~OLCULEMEDI~).
    Ucunde de eski ayiklayici yalniz `~~...~~` biliyordu, yani belge okuyucuda
    USTU CIZILI gorunen hukum testte YURURLUKTE sayiliyordu.

    Cikti YURURLUKTEKI metindir: yeni icerik BURADA aranir. Eski metnin cizili
    DURDUGUNU denetleyen kilitler HAM metinde kalir (FDR kurali: eski metin
    silinmez, cizilir + tarih).
    """
    m, parcalar = _maskele(metin)
    m = _CIFT_TILDE.sub("", m)
    m = _TEK_TILDE.sub("", m)
    m = _HTML_CIZGI.sub("", m)
    return _coz(m, parcalar)


# ── 2. beyaz liste disi cizik ─────────────────────────────────────────────────
_TILDE_KOSUSU = re.compile(r"~+")
_BIRLESEN_CIZGI = re.compile(r"[̵̶̷̸]")          # birlesen uzeri cizgi
_TILDE_BENZERI = re.compile(r"[˜∼∽⁓～]")      # tilde benzerleri
_ETIKET = re.compile(r"</?([A-Za-z][A-Za-z0-9-]*)\b[^>]*>")
_CSS_CIZGI = re.compile(r"line-through|text-decoration", re.I)


def _konum(metin, indeks):
    return "satir {}".format(metin.count("\n", 0, indeks) + 1)


def _baglam(metin, b, s):
    return " ".join(metin[max(0, b - 35):s + 35].split())


def beyaz_liste_disi_cizik(metin, izinli=()):
    """Metinde KALAN her cizme adayini bulur; `izinli` disindaki her cizik HATA.

    `izinli`: tarihli-gerekceli, CAGIRAN TESTIN bildirdigi cizili araliklarin tam
    metinleri (ornegin GOSTERICI_KURULUM §5'teki `~~10 Eylul (T228): ...~~` eski
    komut satiri). Bir aday bu metinlerden birinin ICINDE duruyorsa mesrudur.

    NEDEN BEYAZ LISTE: cizme sozdizimi kara listeyle kapanmaz. Kalip eklemeden
    yakalanmasi gereken aday siniflari:
      · tilde kosusu (`~~x~~`, `~x~`, `~~~x~~~`) — "~<rakam>" yaklasik istisnasi disinda
      · birlesen uzeri cizgi U+0335..U+0338 (gorunurde cizili, sozdizimi yok)
      · tilde benzeri isaretler — kopyala-yapistir varyantlari
      · ZARARSIZ_ETIKETLER disindaki HER HTML etiketi — uydurma `<sil>` ya da
        stil tasiyan `<span style="text-decoration:line-through">` dahil
      · icinde `line-through` / `text-decoration` gecen her etiket
    Kod araliklari (` ... `, ```...```) taranmaz: oradaki `~` harfi harfinedir.

    Doner: hata metinleri listesi (bos liste = temiz).
    """
    izinli_araliklar = []
    for parca in izinli:
        if not parca:
            continue
        i = metin.find(parca)
        while i >= 0:
            izinli_araliklar.append((i, i + len(parca)))
            i = metin.find(parca, i + 1)
    kod = _kod_araliklari(metin)

    def mesru(b, s):
        return (any(kb <= b and s <= ks for kb, ks in izinli_araliklar)
                or any(kb <= b and s <= ks for kb, ks in kod))

    hatalar = []

    def ekle(b, s, tur):
        if not mesru(b, s):
            hatalar.append("{}: beyaz liste disi cizik ({}) — {!r}".format(
                _konum(metin, b), tur, _baglam(metin, b, s)))

    for m in _TILDE_KOSUSU.finditer(metin):
        b, s = m.span()
        if len(m.group(0)) == 1 and s < len(metin) and metin[s].isdigit():
            continue                      # "~3 s" = yaklasik (belgelenen istisna)
        ekle(b, s, "tilde")
    for m in _BIRLESEN_CIZGI.finditer(metin):
        ekle(m.start(), m.end(), "birlesen uzeri cizgi")
    for m in _TILDE_BENZERI.finditer(metin):
        ekle(m.start(), m.end(), "tilde benzeri isaret")
    for m in _ETIKET.finditer(metin):
        ad = m.group(1).lower()
        if ad in ZARARSIZ_ETIKETLER and not _CSS_CIZGI.search(m.group(0)):
            continue
        ekle(m.start(), m.end(), "html etiketi <{}>".format(ad))
    return hatalar


# ── 3. normallestirme ─────────────────────────────────────────────────────────
_SIFIR_GENISLIK = dict.fromkeys(
    map(ord, "­​‌‍‎‏⁠﻿"))
_TIPOGRAFI = str.maketrans({
    **{c: "'" for c in "‘’‚‛´ʼʹ′`"},
    **{c: '"' for c in "“”„‟″"},
    **{c: "-" for c in "‐‑‒–—―−"},
    "*": None, "_": None})
_TR_KUCUK = str.maketrans({"I": "ı", "İ": "i"})
_AKSANSIZ = str.maketrans({"ı": "i"})

# Turkce sayi sozcukleri -> rakam. NEDEN: T228 kacani A6 — kod DRM_CANLI_ARDISIK=2
# iken belgeye "**bir** ardisik" yazildi; kilit yalniz RAKAM aradigi icin gormedi.
# DIKKAT: bu adim AKSANLAR DURURKEN kosar — aksan katlandiktan sonra "ön" (on ek)
# ile "on" (10) ayirt edilemez ve "ön hüküm" sessizce "10 hüküm" olurdu. Ayni
# celiski "uç" (tip) ile "üç" (3) arasindadir.
_SAYI_SOZCUKLERI = {"sıfır": "0", "bir": "1", "iki": "2", "üç": "3", "dört": "4",
                    "beş": "5", "altı": "6", "yedi": "7", "sekiz": "8",
                    "dokuz": "9", "on": "10", "tek": "1", "yarım": "0,5"}
_SAYI_DESENI = re.compile(_SINIR_ONCE + r"(" + "|".join(
    sorted(_SAYI_SOZCUKLERI, key=len, reverse=True)) + r")" + _SINIR_SONRA)

# Birim es anlamlilari — TEK YON: SOZCUK -> SEMBOL (milisaniye->ms, saniye->s,
# derece->°). Ek harfleri ([a-z]*) yutulur: "saniyeyi" -> "s".
# NEDEN: T228 kacani A7/A9 — kilit "s" ariyordu, belgeye "saniye" yazildi.
_BIRIM_DESENI = re.compile(
    _SINIR_ONCE + r"(milisaniye|saniye|derece)[a-z]*" + _SINIR_SONRA)
_BIRIMLER = {"milisaniye": "ms", "saniye": "s", "derece": "°"}

# Karsilastirma es anlamlilari -> tek bicim. NEDEN: T228 kacani A7 ("en az 1
# saniye") ve A9 ("6 saniyeyi asan").
_ONEK_KARSILASTIRMA = [
    (r"en\s+az|asgari|en\s+erken|en\s+dusuk", "≥"),
    (r"en\s+cok|en\s+fazla|azami|en\s+gec|en\s+yuksek", "≤"),
    (r">=", "≥"),
    (r"<=", "≤"),
]
_ONEK_DESENI = re.compile(_SINIR_ONCE + "(?:" + "|".join(
    "(?P<g{}>{})".format(i, k) for i, (k, _) in enumerate(_ONEK_KARSILASTIRMA)) + ")")
_ONEK_KARSILIK = {"g{}".format(i): d for i, (_, d) in enumerate(_ONEK_KARSILASTIRMA)}

_BIRIM_SINIFI = r"(?:ms|s|°|hz|m|km|px|fps|v|a)"
_SONEK_DESENI = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(" + _BIRIM_SINIFI + r")?\s*(?:'[a-z]*)?\s*"
    r"(ve\s+uzeri|uzerinde|uzeri|asan|gecen|fazla)" + _SINIR_SONRA)
_SONEK_ISARET = {"ve uzeri": "≥", "uzerinde": "≥", "uzeri": "≥",
                 "asan": ">", "gecen": ">", "fazla": ">"}


def _sonek(m):
    isaret = _SONEK_ISARET[" ".join(m.group(3).split())]
    birim = " " + m.group(2) if m.group(2) else ""
    return "{} {}{}".format(isaret, m.group(1), birim)


def normalize(metin):
    """Hukum karsilastirmalari icin tek bicime indirger.

    Sirayla: (1) cizikler DUSER; (2) sifir genislikli karakterler atilir, '≠'
    korunur ('!=' olur — NFKD'de '=' + U+0338'e ayrisip anlami TERSINE donerdi);
    (3) tipografik kesme/tirnak/tire duz karsiliklarina iner ve vurgu isaretleri
    (** * __ _ backtick) SOZCUK ICI DAHIL sokulur; (4) Turkce kucuk harf (I->ı,
    İ->i) — AKSANLAR HENUZ DURUR; (5) Turkce sayi sozcukleri rakama iner;
    (6) NFKD + birlesen isaretler atilir (g-breve -> g, s-cedilla -> s), noktasiz
    i -> i; (7) birim es anlamlilari katlanir (saniye->s, milisaniye->ms,
    derece->derece isareti); (8) karsilastirma es anlamlilari tek bicime iner
    (>= / "en az" / "asgari" / "ve uzeri" -> ≥ ; > / "asan" / "gecen" / "fazla"
    -> > ; <= / "en cok" / "azami" -> ≤), sonek bicimi ("6 saniyeyi asan") ONEK
    bicimine ("> 6 s") cevrilir.

    (5)'in (6)'dan ONCE kosmasi zorunludur: aksan katlandiktan sonra "ön" ile
    "on" ayni dizedir ve "ön hüküm" sessizce "10 hüküm" olurdu.

    NEDEN her adim: (3) T221 kacanlari W3 `_dogrulandi_`, W4 `__kosuldu__` ve
    T226 kacani D1f (tipografik tirnak); (5) T228 kacani A6 "bir ardisik";
    (7)+(8) T228 kacanlari A7 "en az 1 saniye" ve A9 "6 saniyeyi asan".
    """
    s = cizikleri_ayikla(metin)
    s = s.translate(_SIFIR_GENISLIK).replace("≠", "!=")
    s = s.translate(_TIPOGRAFI)
    s = s.translate(_TR_KUCUK).lower()
    s = _SAYI_DESENI.sub(lambda m: _SAYI_SOZCUKLERI[m.group(1)], s)
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    s = s.translate(_AKSANSIZ)
    s = _BIRIM_DESENI.sub(lambda m: _BIRIMLER[m.group(1)], s)
    s = _ONEK_DESENI.sub(lambda m: _ONEK_KARSILIK[m.lastgroup], s)
    s = _SONEK_DESENI.sub(_sonek, s)
    return s


# ── 4. olumlu hukum ailesi ────────────────────────────────────────────────────
# NEDEN: T228 kacani A8 — belgeye "**teyit edildi**, saha kosumu **basarili**"
# yazildi; eski kalip yalniz dogrulandi|gecti|olculdu|tutar|onaylandi biliyordu.
# T221 kacanlari W2 (KANITLANDI) ve W7 ("sorunsuz tamamlandi; ... saglanmis").
# Harf sinirlari HARF sinifiyla yazilir — `\w` altcizgiyi de harf sayardi ve
# `_dogrulandi_` T221'de kilidi delmisti (W3).
_OLUMLU = (r"gec(?:ti|mistir)", r"olcul(?:du|mustur)",
           r"dogrulan(?:di|mis|mistir)", r"teyit\s+edil(?:di|mis|ir|iyor)",
           r"saglan(?:di|mis|ir|mistir)", r"basarili", r"basariyla",
           r"sorunsuz", r"calisti", r"uygun\s+bulun(?:du|mus)",
           r"gozlen(?:di|mis)", r"kanitlan(?:di|mis|mistir)", r"kosuldu",
           r"tut(?:ar|tu|uyor)", r"onaylan(?:di|mis)")
_OLUMLU_KALIBI = re.compile(
    _SINIR_ONCE + r"(?:" + "|".join(_OLUMLU) + r")" + _SINIR_SONRA)


def olumlu_hukum_var(metin, haric=()):
    """Olculmemis GECTI ailesinden ilk hukum sozcugu (yoksa None).

    Metin ONCE `normalize`'dan gecirilir; donen deger normallestirilmis bicimdir.
    Bos olmayan her donus "olumlu hukum VARDIR" demektir.

    `haric`: cagiran testin, o sozcugu DAHA GUCLU bir kilitle (ornegin ON KAYITLI
    sayim) zaten cakmis oldugunu bildirdigi normallestirilmis kokler. Gevsetme
    DEGILDIR: disarida birakilan sozcuk baska bir kilitle sayilir; hicbir kilidi
    olmayan sozcuk buraya yazilamaz.
    """
    n = normalize(metin)
    for m in _OLUMLU_KALIBI.finditer(n):
        if m.group(0) not in haric:
            return m.group(0)
    return None


# ── 5. on kayitli metin esitligi ──────────────────────────────────────────────
def on_kayitli_metin_esit(metin, beklenen):
    """Bosluk-normalize TAM esitlik (satir sarmasi hukmun anlami degildir).

    NEDEN: kara liste bu sinifta ilkece kapanmaz — T221 kacanlari W1 (baslikta
    `~OLCULEMEDI~`), V1 ("biri tutmasa da prova kabul edilir") ve V3 ("SITL
    zinciri yerinde; prova kapilari sorun cikarmadi") olumlu hukum sozcugu
    TASIMIYORDU. Cozum yapisaldir: hukum tasiyan yuzey ON KAYITLI metinle bire
    bir esitlenir; yeni bir hukum cumlesi eklemek, testi de gorunur bicimde
    degistirmeden IMKANSIZ olur. Bugun baslik alt dizge (`in`) ile bakildigi icin
    `~OLCULEMEDI~` gecmisti.
    """
    return " ".join(metin.split()) == " ".join(beklenen.split())


# ── 6. hukum cumleleri ────────────────────────────────────────────────────────
_CUMLE_SONU = re.compile(r"(?<=[.!?])[*_`)\]]*\s+")


def hukum_cumleleri(metin, anahtarlar):
    """`anahtarlar`dan (normallestirilmis kok) en az birini tasiyan cumleler.

    Cumleler kod araliklari MASKELIYKEN bolunur (`4.5.7`, `AP_Param.cpp:2313`
    gibi noktalar cumle bitirmesin diye), sonra kod geri konur ve her cumle
    `normalize`'dan gecer. Cagiran test donen demeti ON KAYITLI demetle
    karsilastirir; listede olmayan her hukum cumlesi kilidi DUSURUR.

    NEDEN: T221 kacanlari V1/V3 — olumlu hukum sozcugu icermeyen, numarasiz
    celiskili ikinci hukum cumleleri. Kara liste onlari goremez, kapali cumle
    kumesi gorur.
    """
    maskeli, parcalar = _maskele(cizikleri_ayikla(metin))
    cumleler = []
    for ham in _CUMLE_SONU.split(maskeli):
        c = normalize(_coz(ham, parcalar)).strip()
        if c and any(a in c for a in anahtarlar):
            cumleler.append(" ".join(c.split()))
    return tuple(cumleler)
