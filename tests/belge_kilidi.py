# -*- coding: utf-8 -*-
"""Ortak belge kilidi yardimcisi — T240 (D-460 karar 2).

NEDEN VAR: bagimsiz mimar denetimi (D-460) uc isi (T226-D2 / T228-D2 / T221-D3)
REDDETTI. Ortak kusur tekti: her test dosyasi CIZIK ayiklamasini KENDI yazmisti ve
ucu de yalniz `~~...~~` biciminde ayikliyordu. Denetimde kurulan 19 gercek dosya
mutasyonunun 19'u da kacti (T226: 4, T228: 7, T221: 8). Kural tek yerden gelsin
diye butun belge kilitleri artik bu moduldeki yordamlardan gecer.

TASARIM KARARLARI (hepsi olculmus kacislara dayanir):
  1. KARA LISTE DEGIL BEYAZ LISTE — ama SINIRLI bir iddia ile. Cizme sozdizimi
     bitmez (`~~`, `~`, `<del>`, `<s>`, `<strike>`,
     `<span style=...line-through>`, birlesen U+0336 ...).
     `beyaz_liste_disi_cizik` metinde KALAN her cizme adayini bulur; tarihli-
     gerekceli beyaz listede olmayan her aday HATADIR.
     OLCULEN KAPSAM (fazlasi DEGIL): duz metin ve HTML VARLIK bicimindeki
     (`&#822;`, `&#x336;`) cizme isaretleri, tilde kosulari, tilde benzeri
     isaretler ve ZARARSIZ_ETIKETLER disindaki HER etiket. Bu kapsamdaki yeni
     bir sozdizimi buraya kalip eklenmeden yakalanir; kapsam DISINDA kalan bir
     bicim icin iddia YOKTUR (D-460 kacani Y4: varlik bicimi kapsam disiydi ve
     kacmisti — ÖLCULEMEDI != GECTI, bu docstring icin de gecerli).
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
  6. ESITLIK > YOKLUK (D-465, mimar karari, 12 Eylul — YONTEM DEGISIKLIGI).
     T240 ailesi uc turdur ayni bicimde RED aldi: "su sozdizimiyle yasak metin
     geri kondu / hukum gizlendi" (Y4 `&#822;`, sonra `&#96;~~...~~&#96;`, ayrica
     anahtar sozcuksuz cumle ve birim kaydirmasi). YOKLUK denetiminin kacis
     yuzeyi SONSUZDUR; ESITLIK denetiminin kacis yuzeyi YOKTUR. Bu yuzden olcum
     HUKMU tasiyan yuzeyler `bloklar` ile ON KAYITLI METIN ESITLIGINE baglanir:
     bolumun HAM metni testteki sabite esit olmak zorundadir, hangi sozdiziminin
     kullanildigi ONEMSIZDIR. Bu yuzeylerde normallestirme YALNIZ
     bosluk/satir sonu icindir — cizik/varlik/vurgu AYIKLAMASI KULLANILMAZ
     (ayiklama, saklama yuzeyini acan seyin ta kendisidir).
     Ayiklamali kilitler (cizikleri_ayikla + `in`) yalniz DUSUK DEGERLI
     yuzeylerde (uzun anlati paragraflari) kalir ve orada YOKLUK degil VARLIK
     denetimi yapar.

Yalnizca standart kutuphane (CLAUDE.md madde 4).

KESIF MUAFIYETI: test DEGIL, ORTAK yardimci modul — kendi basina kapi degildir
(T120 kurali: `test_` onekli olmayan dosya test tasimaz). `cizikleri_ayikla`,
`beyaz_liste_disi_cizik`, `bloklar`, `normalize`, `olumlu_hukum_var` ve
`HUKUM_SOZCUKLERI` su testler tarafindan ice alinir: test_belge_kilidi,
test_yks_mk15_hakem_ekrani, test_isaretli_gosterici, test_faz_b_arduplane_sablon,
test_t235_alan_etiketi ve test_t243_paket_boyutu. Kendi kapisi
`tests/test_belge_kilidi.py`dir (74 test).
KOSUM: O:\\navitas-local-train\\venv\\Scripts\\python.exe -X utf8 -B -m unittest discover -s tests -p "test_belge_kilidi.py"  (tests/belge_kilidi.py bu kosumda ice alinir)
"""

import html
import re
import unicodedata

__all__ = ["cizikleri_ayikla", "beyaz_liste_disi_cizik", "normalize",
           "olumlu_hukum_var", "on_kayitli_metin_esit", "bloklar",
           "hukum_cumleleri", "kabul_olcutu_tekligi", "HARF",
           "ZARARSIZ_ETIKETLER", "HUKUM_SOZCUKLERI", "KABUL_CELISKI_SOZCUKLERI"]

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


# ── 0. HTML varlik cozumlemesi ────────────────────────────────────────────────
# NEDEN (D-460 kacani Y4): CONTRACTS §6.8'de `maliyeti` yerine
# `m&#822;a&#822;l&#822;i&#822;...` yazildiginda hukum markdown okuyucuda USTU
# CIZILI gorunuyor, testte ise YURURLUKTE sayiliyordu: `&#822;`, U+0336'nin
# (birlesen uzeri cizgi) HTML varlik bicimidir ve tarayici onu HIC gormuyordu.
# Ayni karakterin ciplak hali DUSUYORDU — kacis yolu yalniz YAZIM bicimiydi.
_VARLIK = re.compile(r"&(?:#[0-9]{1,7}|#[xX][0-9a-fA-F]{1,6}|[A-Za-z][A-Za-z0-9]{1,31});?")
#: Cozulmesi YASAK varliklar: cozulmus degeri MARKDOWN YAPISI belirten bir simge
#: olanlar.
#:
#: NEDEN (D-465 · T240-B curutucusunun KUSUR 1'i, GERILEME): CommonMark/GFM'de
#: varlik ve sayisal karakter referanslari YAPI belirten simgelerin yerine
#: KULLANILAMAZ. Okuyucu once satiri yapiya ayirir, varliklari ANCAK ondan sonra
#: metin icerigi olarak cozer. Yani COZULMUS bir backtick KOD ARALIGI ACAMAZ,
#: cozulmus bir tilde CIZGI ACAMAZ, cozulmus bir `<` ETIKET ACAMAZ: `&#96;` metinde
#: duz bir backtick KARAKTERI olarak gorunur, kod araligi baslatmaz.
#:
#: OLCULEN KACIS (curutucu X15/X16/X17, gercek dosya + gercek suit, cikis 0):
#: `&#96;~~Donusturucunun canli kodeki~~&#96;` — T240-B'nin ilk surumu `&#96;`'i
#: cozuyordu, `_kod_araliklari` COZULMUS kopyada bir kod araligi "goruyordu" ve
#: icindeki `~~...~~` taramadan tamamen gizleniyordu. Okuyucuda USTU CIZILI duran
#: hukum testte YURURLUKTE sayiliyordu. Ayni girdi T240-B ONCESI surumde (64b60ae5)
#: DUSUYORDU: gerileme.
#:
#: SECILEN COZUM ve GEREKCESI: iki yol vardi.
#:   (A) yapi ureten karakterlere cozen varliklari HIC cozmemek (bu),
#:   (B) `_kod_araliklari`'ni HAM metinde hesaplayip haritayla tarama kopyasina
#:       tasimak.
#: (A) secildi, cunku (B) yalniz KOD ARALIGI yanilgisini kapatir; `&#126;` ile
#: yazilmis bir tilde, `&#42;` ile yazilmis bir yildiz ya da `&#124;` ile yazilmis
#: bir tablo cubugu (B)'de HALA cozulur ve tarama kopyasinda OLMAYAN bir yapi
#: uretir. (A) sinifin tamamini tek kuralla kapatir: cozulmus metin yapi ureten
#: HICBIR simge KAZANMAZ, cozum yalniz KARAKTER tespiti icindir (`&#822;`
#: birlesen uzeri cizgi, `&#8212;` uzun tire ...).
#: (A)'nin bedeli: `&#96;` gibi bir varlik cozulmedigi icin "gorunmez" kalabilirdi
#: — bu yuzden `beyaz_liste_disi_cizik` onlari DOGRUDAN beyaz liste disi aday
#: sayar (asagida). OLCUM (bu kilidin bagladigi dort belgede, kod araliklari
#: DISINDA): CONTRACTS.md 0, GOSTERICI_KURULUM.md 0 (tek aday `&PWR`, cozulmuyor),
#: config/pixhawk/README.md 0, t235/ON_KAYIT.md 0 mesru varlik — yani bu adaylarin
#: kod DISINDA hicbir mesru kullanimi YOKTUR.
_COZULMEZ = frozenset("<>`~*_[]|#" + chr(92))


def _varlik_cozumle(metin):
    """(cozulmus, bas_haritasi, son_haritasi) — kod DISINDA HTML varliklari cozulur.

    `bas[i]` / `son[i]`: cozulmus metnin i. karakterinin HAM metindeki baslangic
    ve bitis indeksidir. Tarama cozulmus KOPYA uzerinde yapilir; hata metnindeki
    satir ve baglam bu haritayla HAM metinden okunur — konum KAYMAZ.

    Kod araliklari (` ... `, ```...```) cozulmez: kod icinde `&amp;` harfi
    harfinedir (karar 2'nin varlik ikizi).
    """
    kod = _kod_araliklari(metin)
    cikti, bas, son, onceki = [], [], [], 0

    def aynen(b, s):
        cikti.append(metin[b:s])
        bas.extend(range(b, s))
        son.extend(range(b + 1, s + 1))

    for m in _VARLIK.finditer(metin):
        b, s = m.span()
        if b < onceki or any(kb <= b and s <= ks for kb, ks in kod):
            continue
        cozulmus = html.unescape(m.group(0))
        if cozulmus == m.group(0) or set(cozulmus) & _COZULMEZ:
            continue
        aynen(onceki, b)
        cikti.append(cozulmus)
        bas.extend([b] * len(cozulmus))
        son.extend([s] * len(cozulmus))
        onceki = s
    aynen(onceki, len(metin))
    return "".join(cikti), bas, son


def _varliklari_coz(metin):
    """Kod araliklari korunarak HTML varliklari cozulmus TARAMA kopyasi."""
    return _varlik_cozumle(metin)[0]


def _yapi_varliklari(metin):
    """YAPI ureten bir simgeye cozen (bu yuzden COZULMEYEN) varliklarin (bas, son, ham).

    `_COZULMEZ` gerekcesinin ikinci yarisi: bu varliklar cozulmedigi icin tarama
    kopyasinda yapi URETMEZLER, ama gorunmez de kalmamalidirlar. Uc belgede kod
    DISINDA mesru kullanimlari OLCULDU ve SIFIRDIR; dolayisiyla kod disinda
    gorunen her biri dogrudan beyaz liste disi ADAYDIR (`&#96;~~X~~&#96;` sarmali
    ancak boyle GORUNUR olur).
    """
    bulunan = []
    for m in _VARLIK.finditer(metin):
        cozulmus = html.unescape(m.group(0))
        if cozulmus != m.group(0) and set(cozulmus) & _COZULMEZ:
            bulunan.append((m.start(), m.end(), m.group(0)))
    return bulunan


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

    Metin ONCE HTML varlik cozumlemesinden gecer (D-460 kacani Y4): `&#822;` ile
    harf harf cizilmis bir hukum, ciplak U+0336 ile cizilmis olani gibi DUSER.
    """
    m, parcalar = _maskele(_varliklari_coz(metin))
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
      · YUKARIDAKILERIN HTML VARLIK BICIMI (`&#822;`, `&#x336;`) — D-460 kacani Y4
      · MARKDOWN YAPISI ureten simgelerin varlik bicimi (`&#96;`, `&#126;`, `&#42;`,
        `&#124;`, `&grave;` ...) — D-465, curutucu kacanlari X15/X16/X17. Bunlar
        `_COZULMEZ` geregi COZULMEZ (gerekcesi orada); kod DISINDA mesru
        kullanimlari OLCULDU ve sifirdir, bu yuzden dogrudan ADAYDIR. `&#96;` ile
        sarilan bir `~~...~~` boylece hem tilde olarak hem varlik olarak gorunur.
      · tilde benzeri isaretler — kopyala-yapistir varyantlari
      · ZARARSIZ_ETIKETLER disindaki HER HTML etiketi — uydurma `<sil>` ya da
        stil tasiyan `<span style="text-decoration:line-through">` dahil
      · icinde `line-through` / `text-decoration` gecen her etiket
    Kod araliklari (` ... `, ```...```) taranmaz: oradaki `~` harfi harfinedir.
    Ayni nedenle varlik cozumlemesi de kod DISINDA yapilir.

    Tarama varlik-cozumlu KOPYA uzerindedir; hata metnindeki satir ve baglam HAM
    metinden okunur (`_varlik_cozumle` haritasi) — konum kaymaz.

    Doner: hata metinleri listesi (bos liste = temiz).
    """
    tarama, bas, son = _varlik_cozumle(metin)
    izinli_araliklar = []
    for parca in izinli:
        if not parca:
            continue
        cozulmus = _varliklari_coz(parca)
        i = tarama.find(cozulmus)
        while i >= 0:
            izinli_araliklar.append((i, i + len(cozulmus)))
            i = tarama.find(cozulmus, i + 1)
    kod = _kod_araliklari(tarama)

    def mesru(b, s):
        return (any(kb <= b and s <= ks for kb, ks in izinli_araliklar)
                or any(kb <= b and s <= ks for kb, ks in kod))

    hatalar = []

    def ekle(b, s, tur):
        if not mesru(b, s):
            hb = bas[b] if b < len(bas) else len(metin)
            hs = son[s - 1] if 0 < s <= len(son) else hb
            hatalar.append("{}: beyaz liste disi cizik ({}) — {!r}".format(
                _konum(metin, hb), tur, _baglam(metin, hb, hs)))

    for m in _TILDE_KOSUSU.finditer(tarama):
        b, s = m.span()
        if len(m.group(0)) == 1 and s < len(tarama) and tarama[s].isdigit():
            continue                      # "~3 s" = yaklasik (belgelenen istisna)
        ekle(b, s, "tilde")
    for b, s, ham in _yapi_varliklari(tarama):
        ekle(b, s, "yapi ureten varlik bicimi {}".format(ham))
    for m in _BIRLESEN_CIZGI.finditer(tarama):
        ekle(m.start(), m.end(), "birlesen uzeri cizgi")
    for m in _TILDE_BENZERI.finditer(tarama):
        ekle(m.start(), m.end(), "tilde benzeri isaret")
    for m in _ETIKET.finditer(tarama):
        ad = m.group(1).lower()
        if ad in ZARARSIZ_ETIKETLER and not _CSS_CIZGI.search(m.group(0)):
            continue
        ekle(m.start(), m.end(), "html etiketi <{}>".format(ad))
    return hatalar


# ── 3. normallestirme ─────────────────────────────────────────────────────────
_SIFIR_GENISLIK = dict.fromkeys(
    map(ord, "­​‌‍‎‏⁠﻿"))
_TIPOGRAFI = str.maketrans({
    **{c: "'" for c in "‘’‚‛´ʼʹ′"},
    **{c: '"' for c in "“”„‟″"},
    **{c: "-" for c in "‐‑‒–—―−"},
    # Vurgu isaretleri SOZCUK ICI DAHIL sokulur (backtick markdown kod vurgusudur,
    # kesme isareti degil): `dogrulandi`, _dogrulandi_, d*ogrulandi* tek bicime iner.
    "*": None, "_": None, "`": None})
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
# Birim SAYIYA BAGLIDIR (onunde rakam olmali): esik ancak sayiyla anlamlidir ve
# bu cita "derecelendirme"/"saniyelerce" gibi sozcukleri birime cevirmeyi onler.
#
# D-465 / K3 (curutucu KUSUR 2): uzunluk birimleri de katlanir. OLCULEN KACIS —
# t235 ON_KAYIT §4'e "sahada kabul yatay en cok 4 metre ve zamanin en az yuzde
# 70'i olarak alinir" eklenince `kabul_olcutu_tekligi`'nin DORT kurali birden
# temiz donuyordu (X13); "≤ 400 cm" ayni sekilde kaciyordu (X14). "metre" ve
# "yuzde" katlanmadigi icin rakip esik HIC gorulmuyordu.
# SIRA ONEMLI: "santimetre"/"kilometre"/"milimetre" "metre"den ONCE denenir,
# yoksa "santi" + "metre" diye bolunur.
_BIRIM_DESENI = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(milisaniye|santimetre|milimetre|kilometre|saniye|metre|derece)"
    r"[a-z]*" + _SINIR_SONRA)
_BIRIMLER = {"milisaniye": "ms", "saniye": "s", "derece": "°",
             "santimetre": "cm", "milimetre": "mm", "kilometre": "km", "metre": "m"}
# "yuzde 70" -> "%70". ONEKTIR, sonek degil: _BIRIM_DESENI kalibina girmez.
# NEDEN: X13 — "zamanin en az yuzde 70'i" yazildiginda % hic gorulmuyordu.
_YUZDE_DESENI = re.compile(_SINIR_ONCE + r"yuzde\s*(?=\d)")

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

    Sirayla: (1) `cizikleri_ayikla` — once HTML varliklari cozulur (D-460 kacani
    Y4: `&#822;` ile cizilmis hukum, ciplak U+0336 ile cizilmis gibi DUSER),
    sonra cizikler DUSER; (2) sifir genislikli karakterler atilir, '≠'
    korunur ('!=' olur — NFKD'de '=' + U+0338'e ayrisip anlami TERSINE donerdi);
    (3) tipografik kesme/tirnak/tire duz karsiliklarina iner ve vurgu isaretleri
    (** * __ _ backtick) SOZCUK ICI DAHIL sokulur; (4) Turkce kucuk harf (I->ı,
    İ->i) — AKSANLAR HENUZ DURUR; (5) Turkce sayi sozcukleri rakama iner;
    (6) NFKD + birlesen isaretler atilir (g-breve -> g, s-cedilla -> s), noktasiz
    i -> i; (7) "yuzde <sayi>" -> "%<sayi>" ve birim es anlamlilari katlanir
    (saniye->s, milisaniye->ms, derece->derece isareti, metre->m, santimetre->cm,
    milimetre->mm, kilometre->km); (8) karsilastirma es anlamlilari tek bicime iner
    (>= / "en az" / "asgari" / "ve uzeri" -> ≥ ; > / "asan" / "gecen" / "fazla"
    -> > ; <= / "en cok" / "azami" -> ≤), sonek bicimi ("6 saniyeyi asan") ONEK
    bicimine ("> 6 s") cevrilir.

    (5)'in (6)'dan ONCE kosmasi zorunludur: aksan katlandiktan sonra "ön" ile
    "on" ayni dizedir ve "ön hüküm" sessizce "10 hüküm" olurdu.

    NEDEN her adim: (3) T221 kacanlari W3 `_dogrulandi_`, W4 `__kosuldu__` ve
    T226 kacani D1f (tipografik tirnak); (5) T228 kacani A6 "bir ardisik";
    (7)+(8) T228 kacanlari A7 "en az 1 saniye" ve A9 "6 saniyeyi asan", ayrica
    D-465/K3 kacanlari X13 ("en cok 4 metre", "en az yuzde 70") ve X14 ("≤ 400 cm").
    """
    s = cizikleri_ayikla(metin)
    s = s.translate(_SIFIR_GENISLIK).replace("≠", "!=")
    s = s.translate(_TIPOGRAFI)
    s = s.translate(_TR_KUCUK).lower()
    s = _SAYI_DESENI.sub(lambda m: _SAYI_SOZCUKLERI[m.group(1)], s)
    s = "".join(c for c in unicodedata.normalize("NFKD", s)
                if not unicodedata.combining(c))
    s = s.translate(_AKSANSIZ)
    s = _YUZDE_DESENI.sub("%", s)
    s = _BIRIM_DESENI.sub(lambda m: "{} {}".format(m.group(1), _BIRIMLER[m.group(2)]), s)
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


# ── 5b. BLOK ESITLIGI — D-465 (1) ─────────────────────────────────────────────
#: Blok siniri: `_CUMLE_SONU` / `_MADDE_BASI` ile AYNI yapisal birimler (paragraf,
#: liste maddesi, tablo satiri) + baslik satiri. Kod citleri MASKELIYKEN bolunur:
#: bir cit icindeki bos satir blok acmaz ve citin ICI harfi harfine korunur.
_BLOK_SINIRI = re.compile(r"\n[ \t]*\n"
                          r"|\n(?=[ \t]*(?:[-*+]|\d+\.)[ \t])"
                          r"|\n(?=[ \t]*\|)"
                          r"|(?<=\|)[ \t]*\n"
                          r"|\n(?=[ \t]*#{1,6}[ \t])")


def bloklar(metin):
    """Bolumun ON KAYITLI METIN ESITLIGI birimleri: bosluk-normalize HAM bloklar.

    D-465 (mimar karari, 12 Eylul) — YONTEM DEGISIKLIGI. Uc turdur her RED ayni
    bicimde geldi: "su sozdizimiyle yasak metin geri kondu / hukum gizlendi".
    YOKLUK (absence) denetiminin kacis yuzeyi SONSUZDUR — yasaklanan her bicimin
    bir baska yazimi vardir (`~~`, `<s>`, `&#822;`, `&#96;~~...~~&#96;`, anahtar
    sozcuksuz cumle, birim kaydirmasi ...). ESITLIK denetiminin kacis yuzeyi
    YOKTUR: bolumun metni testte duran on kayitli sabite ESIT olmak zorundadir;
    bir sozcuk, bir karakter degisirse test DUSER ve hangi SOZDIZIMIYLE degistigi
    ONEMSIZDIR.

    Bu yuzden olcum hukmu tasiyan yuzeyler (kabul olcutu bloklari, "Sonuc:"
    cumleleri, on kayit bolumleri, hukum tablolari) buradan gecer.

    NORMALLESTIRME YALNIZ BOSLUK/SATIR SONU ICINDIR — bilerek. Cizik ayiklamasi,
    varlik cozumlemesi ve vurgu sokme BURADA KULLANILMAZ: ayiklama, tam da
    "saklama yuzeyi" acan seydir (ayiklanan sey testin gordugu metinden DUSER).
    Ham metin karsilastirildigi icin `~~x~~`, `<s>x</s>`, `&#96;~~x~~&#96;` ve
    `&#822;` sarmali — hepsi ayni sekilde, tek kuralla DUSURUR.

    Bloklama NEDEN: tek bir devasa dize yerine yapisal birimler karsilastirilir;
    boylece (i) hangi blogun degistigi hata metninde okunur, (ii) bir belgede
    kilitlenen blok SAYISI sayilabilir ve KANIT.md'de beyan edilebilir.

    Doner: bosluk-normallestirilmis blok demeti. Kod araliklarinin ICI (satir
    sonlari dahil) harfi harfine korunur.
    """
    maskeli, parcalar = _maskele(metin)
    return tuple(_coz(" ".join(p.split()), parcalar)
                 for p in _BLOK_SINIRI.split(maskeli) if p.strip())


# ── 6. hukum cumleleri ────────────────────────────────────────────────────────
# Cumle siniri: nokta/unlem/soru + bosluk, PARAGRAF siniri, madde (liste) basi ve
# markdown TABLO satiri sinirlari. NEDEN paragraf/madde/tablo da sinirdir: kapali
# kume ancak cumle birimleri KUCUK ve KARARLI ise okunabilir bir on kayda iner;
# tablo satirlari tek bir devasa "cumle"ye yapisinca hem on kayit okunamaz hem de
# satir eklemesi baska bir satirin metniyle gizlenebilirdi.
_CUMLE_SONU = re.compile(
    r"(?<=[.!?])[*_`)\]]*\s+"        # cumle sonu
    r"|\n[ \t]*\n"                   # paragraf siniri
    r"|\n(?=[ \t]*\|)"               # tablo satiri basi
    r"|(?<=\|)[ \t]*\n"              # tablo satiri sonu
    r"|\n(?=[ \t]*(?:[-*+]|\d+\.)[ \t])")   # madde (liste) basi

#: ON KAYITLI "hukum tasiyan sozcuk" listesi — normallestirilmis KOKLER.
#: NEDEN BU SOZCUKLER (kara liste degil, KUME SECICISI): kapali cumle kumesi bir
#: bolumun TUM cumlelerini degil, hukum tasiyanlari kilitler; secici cok dar
#: olursa hukum kacar, cok genis olursa on kayit bolumun kendisi kadar buyur ve
#: alakasiz duzenlemelerde kirilir. Liste, D-460 denetiminde OLCULEN kacan
#: mutantlarin dilinden cikarildi:
#:   · "kaynak"  — D1e: "`kaynak` alani artik zorunlu degildir" (CONTRACTS §6.8)
#:   · "zorunlu" — ayni mutant; "bagimsiz"/"serbest" ikizleri de bu cumlede
#:   · "kilit", "baglayici" — §6.8'in kendi hukum yuzeyinin adi
#:   · "gecerli"/"gecersiz"/"kaldirildi"/"uretmez" — hukmu GERI ALAN fiiller
#:   · "yasak" — yasaklayici hukum
#:   · "olcut"/"prova"/"kabul" — T221 kacanlari V1/V3 ("prova kabul edilir",
#:     "prova kapilari sorun cikarmadi"): hicbir olumlu hukum sozcugu tasimayan,
#:     numarasiz celiskili ikinci hukumler
#:   · "kural"/"hukum" — "Saha kurali (12 Eylul): ..." kalibinin tamami (T228
#:     kacanlari A6/A7/A8/A9 ve curutucunun Y5 aile disi es anlamlisi)
#: Cagiran test bu demeti BOLUME OZGU alan sozcukleriyle genisletir (ornegin
#: GOSTERICI §5 icin "nabiz", "boru", "kip"); daraltmaz.
HUKUM_SOZCUKLERI = ("kaynak", "kilit", "kural", "hukum", "yasak", "baglayici",
                    "gecerli", "gecersiz", "kaldirildi", "uretmez", "zorunlu",
                    "olcut", "prova", "kabul")


def hukum_cumleleri(metin, anahtarlar=HUKUM_SOZCUKLERI):
    """`anahtarlar`dan (normallestirilmis kok) en az birini tasiyan cumleler.

    Cumleler kod araliklari MASKELIYKEN bolunur (`4.5.7`, `AP_Param.cpp:2313`
    gibi noktalar cumle bitirmesin diye), sonra kod geri konur ve her cumle
    `normalize`'dan gecer. Cagiran test donen demeti ON KAYITLI demetle
    karsilastirir; listede olmayan her hukum cumlesi kilidi DUSURUR.

    NEDEN: T221 kacanlari V1/V3 — olumlu hukum sozcugu icermeyen, numarasiz
    celiskili ikinci hukum cumleleri. Kara liste onlari goremez, kapali cumle
    kumesi gorur. D-460 kacani Y7 ayni sinifin CONTRACTS §6.8'deki ikizidir:
    kalin baslik TASIMAYAN ve kaynak paragrafinin hemen ardina DEGIL, bolumun
    baska bir yerine konan celiskili hukum paragrafi hem kalin baslik demetinden
    hem komsuluk kilidinden kacmisti; yakalayan tek yapi budur.
    """
    maskeli, parcalar = _maskele(cizikleri_ayikla(metin))
    cumleler = []
    for ham in _CUMLE_SONU.split(maskeli):
        c = normalize(_coz(ham, parcalar)).strip()
        if c and any(a in c for a in anahtarlar):
            cumleler.append(" ".join(c.split()))
    return tuple(cumleler)


# ── 7. ON KAYIT TEKLIGI (D-461) ───────────────────────────────────────────────
# NEDEN: T236-B curutucusu olctu — `ON_KAYIT §4`'e IKINCI ve GEVSETILMIS bir
# kabul olcutu ("T236 SITL kapisi (gozden gecirilmis): ≤ 4,0 m · ±15° · ≥ %70 ·
# ±3,0 m") eklenince HICBIR test dusmuyordu. Bugunku kilitler yalniz OZGUN
# SATIRIN VARLIGINI koruyordu; olcutun TEKLIGINI korumuyordu. Ayni sinif
# ATOLYE-2'de (A10/A7) ve T229-D2'de (§7.5) ayri ayri olculdu: uc belirtinin tek
# kok nedeni budur. "On kayitli esikler gevsetilmez" kuralinin MEKANIK karsiligi.
#
# Kabul yuzeyinde celiskili IKINCI HUKUM sozcukleri — ON KAYITLI liste.
# Bunlar kara liste DEGIL, YUZEY kuralidir: kabul blogu zaten metin esitligiyle
# baglidir (kural c); bu sozcukler "kabul olcutunu baska bir yerden gecersiz
# kilma" girisiminin dilidir ve bolumun HERHANGI bir yerinde yasaktir.
KABUL_CELISKI_SOZCUKLERI = (
    r"gozden\s+gecirilmis",
    r"guncellenmis\s+kapi",
    r"yalniz\s+[^.;:\n]{1,60}?\s+ile\s+verilir",
    r"kaldirildi",
    r"gecersiz",
    r"revize",
)
_KABUL_CELISKI = re.compile("|".join(KABUL_CELISKI_SOZCUKLERI))

# Esik ifadesi: karsilastirma isareti + sayi + (birim). Sayi ZORUNLUDUR —
# karsilastirmasiz "50 m" (ornegin "FENCE 50 m altinda") esik degildir, olcum
# baglamidir; rakip esik ancak KARSILASTIRMALI ikinci ifadedir.
_OLCUT_BIRIMI = r"m/s|ms|cm|mm|b/s|km|dk|db|s|°|m|px|fps|hz|v|a"
_OLCUT_DESENI = re.compile(
    r"(?:≥|≤|>|<|±)\s*±?\s*(?P<yuzde>%)?\s*(?P<sayi>\d+(?:[.,]\d+)?)\s*"
    r"(?P<birim>%|" + _OLCUT_BIRIMI + r")?" + _SINIR_SONRA)

#: ONEK KATLAMASI (D-465 / K3, curutucu kacani X14): "≤ 400 cm" ile "≤ 4,0 m"
#: AYNI esiktir; birim adi farkli oldugu icin kural (b) ikisini ayri buyukluk
#: sayiyor ve rakip esik kaciyordu. Katlanan aile SAYILIDIR ve OLCULDU:
#: uzunluk (cm/mm/km -> m) ve sure (ms -> s). "dk" BILEREK katlanmaz: "15 dk"
#: sure butcesi, "900 s" ise esik dili degildir; ikisi bu belgelerde hic ayni
#: buyuklugu anlatmiyor (olculdu) ve katlansa yalanci alarm uretirdi.
_OLCEK = {"cm": ("m", 0.01), "mm": ("m", 0.001), "km": ("m", 1000.0),
          "ms": ("s", 0.001)}

#: Madde siniri `_CUMLE_SONU` ile AYNI yapisal birimleri kullanir (paragraf, liste
#: maddesi, tablo satiri) — kabul blogu bunlardan biridir. Tablo satiri da birimdir:
#: T229-D2 kacani kabul hukmunu bir TABLO SATIRININ parantezine koymustu.
_MADDE_BASI = re.compile(r"\n[ \t]*\n"
                         r"|\n(?=[ \t]*(?:[-*+]|\d+\.)[ \t])"
                         r"|\n(?=[ \t]*\|)"
                         r"|(?<=\|)[ \t]*\n")


def _olcek(birim, deger):
    """(birim, deger) ciftini TEMEL birime cevirir: 400 cm -> (m, 4.0); 200 ms -> (s, 0.2)."""
    if birim in _OLCEK:
        temel, kat = _OLCEK[birim]
        return temel, round(deger * kat, 9)
    return birim, round(deger, 9)


def _buyuklukler(metin):
    """{birim: {deger, ...}} — KARSILASTIRMALI esik ifadeleri (normallestirilmis metin).

    Birimler TEMEL birime katlanir (`_OLCEK`): "≤ 400 cm" ile "≤ 4,0 m" ayni
    buyukluge iner, boylece ONEK degistirerek rakip esik gizlenemez (X14).
    """
    kume = {}
    for m in _OLCUT_DESENI.finditer(metin):
        birim = "%" if m.group("yuzde") else (m.group("birim") or "")
        birim, deger = _olcek(birim, float(m.group("sayi").replace(",", ".")))
        kume.setdefault(birim, set()).add(deger)
    return kume


def _maddeler(metin):
    """Madde/paragraf birimleri: kabul blogu bir madde ya da paragraftir."""
    return [p for p in _MADDE_BASI.split(metin) if p.strip()]


def kabul_olcutu_tekligi(metin, kapi_adi, on_kayitli_olcut, mesru_buyuklukler=()):
    """ON KAYIT TEKLIGI kilidi (D-461). Doner: hata metinleri listesi (bos = temiz).

    `metin`            : kabul YUZEYI (ornegin ON_KAYIT'in ilgili bolumu).
    `kapi_adi`         : kapinin adi, belgedeki yaziliyla ("T236 SITL kapisi").
    `on_kayitli_olcut` : kabul blogunun ON KAYITLI TAM metni.
    `mesru_buyuklukler`: kural (b) icin ON KAYITLI istisna ciftleri — ((birim,
                         deger), ...). Bolumde kabul olcutu DISINDA, baska bir
                         nedenle mesruen gecen karsilastirmali buyuklukler.
                         Ornek: ATOLYE-2 A10'da "BEKLENTI (BENZER OLCUM — olcum
                         DEGIL): ... → beklenti ≤ 1,35 FPS" satiri. Bu bir KARA
                         LISTE GEVSETMESI DEGIL, bir ON KAYITTIR: yeni bir deger
                         ancak testte gorunur bir degisiklikle girer ve kalan
                         HER rakip esik yine DUSURUR (olculdu: A10'da 1,35 FPS
                         disindaki her fps degeri hata verir).

    Dort kural (hepsi D-461'de olculmus bir kacisa karsilik gelir):
      (a) TEKLIK — `kapi_adi` normallestirilmis metinde TAM BIR KEZ gecmeli.
          Ikinci bir "T236 SITL kapisi (gozden gecirilmis): ..." satiri, ozgun
          satir yerinde dururken de kabul yuzeyini ikiye boler.
      (b) RAKIP ESIK YOK — on kayitli olcutun kisitladigi her buyuklugun (m, °,
          %, s, m/s, a, fps ...) bolumde gecen KARSILASTIRMALI degerleri, on
          kayitli olcuttekilerin ALT KUMESI olmali. "≤ 4,0 m" ikinci kez,
          "±15°" ikinci kez: rakip esik.
      (c) METIN ESITLIGI — `kapi_adi`yi tasiyan madde, `on_kayitli_olcut` ile
          bosluk-normalize TAM esit olmali; alt dizge `in` YETMEZ (ATOLYE-2 A7
          kacani: olcute "∧ YKS video paneli BAYAT degil" EKLENMISTI, ozgun metin
          hala icinde duruyordu).
      (d) CELISKI SOZCUGU YOK — `KABUL_CELISKI_SOZCUKLERI` kabul yuzeyinde
          yasaktir (ATOLYE-2 A10 kacani: "kabul yalniz p50 ile verilir";
          T229-D2 kacani: parantez ICINE konan "... gecersiz" hukmu).

    Kural (b) YALNIZ on kayitli olcutteki birimlere bakar: bolumdeki baska
    buyuklukler (ornegin "FENCE 50 m altinda") kapi olcutu DEGILDIR ve zaten
    karsilastirma isareti tasimazlar.
    """
    hatalar = []
    n = normalize(metin)
    n_ad = " ".join(normalize(kapi_adi).split())
    n_olcut = normalize(on_kayitli_olcut)

    adet = n.count(n_ad)
    if adet != 1:
        hatalar.append("kabul olcutu tekligi: {!r} normallestirilmis metinde {} kez "
                       "(tam 1 olmali)".format(kapi_adi, adet))

    olcut_buyukluk = _buyuklukler(n_olcut)
    bolum_buyukluk = _buyuklukler(n)
    mesru = {}
    for birim, deger in mesru_buyuklukler:
        b, d = _olcek(birim, float(deger))
        mesru.setdefault(b, set()).add(d)
    for birim, degerler in sorted(olcut_buyukluk.items()):
        fazla = sorted(bolum_buyukluk.get(birim, set()) - degerler - mesru.get(birim, set()))
        if fazla:
            hatalar.append("rakip esik ({!r}): on kayitta {} varken bolumde ayrica {}"
                           .format(birim or "birimsiz", sorted(degerler), fazla))

    adayi = [p for p in _maddeler(metin) if n_ad in " ".join(normalize(p).split())]
    if len(adayi) != 1:
        hatalar.append("kabul blogu {} madde icinde bulundu (tam 1 olmali)".format(len(adayi)))
    elif not on_kayitli_metin_esit(adayi[0], on_kayitli_olcut):
        hatalar.append("kabul blogu on kayitli metinle ayni degil: {!r}"
                       .format(" ".join(adayi[0].split())))

    for m in _KABUL_CELISKI.finditer(n):
        hatalar.append("kabul yuzeyinde celiskili ikinci hukum sozcugu: {!r} — {!r}"
                       .format(m.group(0), " ".join(n[max(0, m.start() - 45):m.end() + 45].split())))
    return hatalar
