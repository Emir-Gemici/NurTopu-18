#!/usr/bin/env python3
"""IKA SURUCU KABUL HARNESSI — surucu CONTRACTS.md §7.2 sozlesmesine uyuyor mu?

NEDEN (D-390 · T149 · CONTRACTS §7.2 · Faz B): D-390, motor/konum erisimini
`simulation/scripts/ika_surucu.py` arayuzune tasidi (hiz_ver/konum_al/durdur/
saglikli). GercekSurucu bugun ISKELETTIR: arka ucsuz kurulum DONANIM_YOK ile
duser (§7.2 kural 3). Cumartesi (5 Eylul) arka uc dolacak; o an "surucu
sozlesmeye uyuyor mu" sorusu GOZ KARARIYLA degil, MEKANIK bir kabul turuyla
cevaplanmali. Bu betik o turdur. Bugun SahteSurucu ile sinanir; sahada
`--surucu gercek --arka-uc modul:Sinif` ile AYNI adimlar kosulur.

Kabul adimlari (her biri GECTI / DUSTU / ATLANDI + olculen deger):
  K1 durdur() -> True.
  K2 konum_al() -> 4'lu demet. Hepsi None ise "KONUM YOK" UYARISI ile kabul
     (GNSS/odometri baglanana dek); sayisal ise HEPSI sonlu olmali.
  K3 hiz rampasi 0 -> RAMPA_HEDEF_MS, RAMPA_ADIM adim, her adimda
     hiz_ver(v, v) True; adimlar arasi RAMPA_ADIM_SURESI_S. Ilk False'ta
     rampa KESILIR (guvenilmez surucuye hizlanma komutu basilmaz).
     Gercek/gazebo: aracin hareketi insan gozuyle teyit edilir —
     "GOZLE TEYIT ET" satiri basilir (yazilim bunu OLCEMEZ).
  K4 durdur() -> True ve sonrasinda saglikli() True (ika_nav.surucu_saglikli()
     ile de ayni goruse varilmali).
  K5 fail-closed (YALNIZ sahte): ARDISIK_HATA_TAVANI ardisik ariza enjekte
     -> saglikli() False; tavanin bir altinda ise hala True (tek gecici
     aksama gorevi durdurmasin — §7.2 kural 1).
  K6 saglik sifirlama: basarili hiz_ver sonrasi ardisik_hata == 0.

Cikis kodu:
  0  tum ZORUNLU adimlar GECTI
  1  en az bir zorunlu adim DUSTU (ya da tur cokme ile kesildi — fail-closed)
  2  surucu KURULAMADI: gercek + arka uc yok (DONANIM_YOK — Faz B oncesi
     BEKLENEN durum) ya da --arka-uc yuklenemedi. Tur hic baslamadi.

Fail-closed: hangi adimda dusulurse dusulsun, tur sonunda SON BIR durdur()
her zaman denenir; istisna yakalanir, sessiz basari YALANI yoktur.

Sabitler: ARDISIK_HATA_TAVANI ika_surucu'dan IMPORT edilir (madde 16 — ciplak
sayi yazilmaz); rampa hedefi ika_nav.MAX_SPEED'i asamaz.

Kullanim:
    O:\\navitas-local-train\\venv\\Scripts\\python.exe -B scripts/ika_surucu_kabul.py \\
        --surucu sahte|gazebo|gercek [--arka-uc modul:Sinif] [--json] \\
        [--json-dosya YOL] [--arizali-cagrilar 3,4] [--sahte-konum-yok]
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "simulation" / "scripts", KOK / "comms", KOK / "codes"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

import ika_nav  # noqa: E402
from ika_surucu import (  # noqa: E402
    ARDISIK_HATA_TAVANI,
    VARSAYILAN_MODEL,
    VARSAYILAN_TOPIC,
    GazeboSurucu,
    GercekSurucu,
    IkaSurucuHatasi,
    SahteSurucu,
)

GECTI, DUSTU, ATLANDI = "GECTI", "DUSTU", "ATLANDI"

# Kabul turu parametreleri (gorev tanimi: 0 -> 0,30 m/s, 5 adim, 0,2 s).
RAMPA_HEDEF_MS = 0.30
RAMPA_ADIM = 5
RAMPA_ADIM_SURESI_S = 0.2

# Cikis kodlari — ayirt edilebilir olmalari SOZLESMEDIR (testler kilitler).
CIKIS_GECTI = 0
CIKIS_DUSTU = 1
CIKIS_SURUCU_KURULAMADI = 2

SURUCULER = ("sahte", "gazebo", "gercek")

JSON_AYRAC = "--- JSON ---"


class ArkaUcYuklenemedi(RuntimeError):
    """--arka-uc modul:Sinif cozumlenemedi (kullanici/yapilandirma hatasi)."""


@dataclass
class Adim:
    ad: str
    baslik: str
    zorunlu: bool = True
    durum: str = DUSTU          # varsayilan DUSTU: adim kosulmadiysa GECTI sayilmaz
    olculen: str = ""
    sebep: str | None = None
    uyari: str | None = None
    veri: dict = field(default_factory=dict)

    def gecti(self, olculen, uyari=None, **veri):
        self.durum, self.olculen, self.uyari = GECTI, olculen, uyari
        self.veri.update(veri)
        return self

    def dustu(self, olculen, sebep, **veri):
        self.durum, self.olculen, self.sebep = DUSTU, olculen, sebep
        self.veri.update(veri)
        return self

    def atlandi(self, sebep):
        self.durum, self.zorunlu, self.sebep = ATLANDI, False, sebep
        return self

    def sozluk(self):
        return {
            "ad": self.ad, "baslik": self.baslik, "zorunlu": self.zorunlu,
            "durum": self.durum, "olculen": self.olculen,
            "sebep": self.sebep, "uyari": self.uyari, "veri": self.veri,
        }


# ── Surucu kurulumu ─────────────────────────────────────────────────────────

def _arka_uc_yukle(belirtec):
    """'modul:Sinif' -> ornek. Bulunamazsa ArkaUcYuklenemedi (sessiz None yok)."""
    if not belirtec or ":" not in belirtec:
        raise ArkaUcYuklenemedi(
            f"--arka-uc 'modul:Sinif' bicimini bekler, alinan: {belirtec!r}")
    modul_adi, sinif_adi = belirtec.rsplit(":", 1)
    try:
        modul = importlib.import_module(modul_adi)
    except ImportError as hata:
        raise ArkaUcYuklenemedi(
            f"arka uc modulu yuklenemedi: {modul_adi!r} ({hata})") from hata
    sinif = getattr(modul, sinif_adi, None)
    if sinif is None:
        raise ArkaUcYuklenemedi(
            f"{modul_adi!r} icinde {sinif_adi!r} yok")
    try:
        return sinif()
    except Exception as hata:  # arka uc kurucusu ne firlatirsa firlatsin
        raise ArkaUcYuklenemedi(
            f"arka uc {belirtec!r} kurulamadi: {type(hata).__name__}: {hata}"
        ) from hata


def _cagri_kumesi(metin):
    """'3,4' -> {3, 4}; 1 tabanli cagri numaralari (SahteSurucu sozlesmesi)."""
    if not metin:
        return set()
    kume = set()
    for parca in metin.split(","):
        parca = parca.strip()
        if not parca:
            continue
        n = int(parca)
        if n < 1:
            raise ValueError(f"cagri numarasi 1 tabanlidir, alinan: {n}")
        kume.add(n)
    return kume


def surucu_kur(args):
    """Secilen surucuyu kur. gercek + arka uc yok -> IkaSurucuHatasi SIZAR
    (cagiran DONANIM_YOK olarak raporlar); --arka-uc bozuksa ArkaUcYuklenemedi."""
    if args.surucu == "sahte":
        pozlar = None if args.sahte_konum_yok else [(0.0, 0.0, 0.0, 0.0)]
        return SahteSurucu(pozlar=pozlar,
                           arizali_cagrilar=_cagri_kumesi(args.arizali_cagrilar))
    if args.surucu == "gazebo":
        return GazeboSurucu(topic=args.gz_topic, model=args.gz_model)
    if args.surucu == "gercek":
        arka_uc = _arka_uc_yukle(args.arka_uc) if args.arka_uc else None
        return GercekSurucu(arka_uc=arka_uc)   # arka_uc None -> DONANIM_YOK
    raise ArkaUcYuklenemedi(f"bilinmeyen surucu: {args.surucu!r}")


# ── Kabul turu ──────────────────────────────────────────────────────────────

def _hiz_ver_dustu_sebebi(surucu_adi):
    """hiz_ver False dondugunde insanin okuyacagi sebep (istisna sizmadigi icin
    surucu sebep vermez; ortamdan cikarilir)."""
    if surucu_adi == "gazebo" and shutil.which("gz") is None:
        return "gz komutu yok (PATH'te bulunamadi)"
    return "hiz_ver False dondu (surucu iletemedi)"


def _sayisal_sonlu(deger):
    return (isinstance(deger, (int, float)) and not isinstance(deger, bool)
            and math.isfinite(deger))


def _k2_konum(surucu):
    adim = Adim("K2", "konum_al() -> 4'lu demet")
    try:
        konum = surucu.konum_al()
    except Exception as hata:
        return adim.dustu("istisna", f"konum_al istisna firlatti: "
                                     f"{type(hata).__name__}: {hata}")
    if not isinstance(konum, (tuple, list)) or len(konum) != 4:
        return adim.dustu(repr(konum), "4'lu demet degil")
    konum = tuple(konum)
    if all(k is None for k in konum):
        return adim.gecti("(None, None, None, None)",
                          uyari="KONUM YOK — GNSS/odometri baglanana dek kabul",
                          konum=None)
    if not all(_sayisal_sonlu(k) for k in konum):
        return adim.dustu(repr(konum),
                          "karisik None ya da sonlu olmayan deger "
                          "(sozlesme: ya 4 sayi ya 4 None)")
    return adim.gecti(repr(konum), konum=list(float(k) for k in konum))


def _k3_rampa(surucu, surucu_adi, uyku):
    adim = Adim("K3", f"hiz rampasi 0 -> {RAMPA_HEDEF_MS:.2f} m/s, "
                      f"{RAMPA_ADIM} adim")
    if RAMPA_HEDEF_MS > ika_nav.MAX_SPEED:
        return adim.dustu(f"hedef={RAMPA_HEDEF_MS} MAX_SPEED={ika_nav.MAX_SPEED}",
                          "rampa hedefi ika_nav.MAX_SPEED ustunde — rampa "
                          "KOSULMADI")
    hizlar = [RAMPA_HEDEF_MS * i / RAMPA_ADIM for i in range(1, RAMPA_ADIM + 1)]
    basarili = []
    for i, v in enumerate(hizlar, start=1):
        if not surucu.hiz_ver(v, v):
            return adim.dustu(
                f"{i - 1}/{RAMPA_ADIM} adim; adim {i} (v={v:.2f} m/s) iletilemedi",
                _hiz_ver_dustu_sebebi(surucu_adi),
                basarili_adim=len(basarili), dusen_adim=i, dusen_hiz=v)
        basarili.append(v)
        if i < RAMPA_ADIM:
            uyku(RAMPA_ADIM_SURESI_S)
    return adim.gecti(f"{RAMPA_ADIM}/{RAMPA_ADIM} adim; son v={hizlar[-1]:.2f} m/s",
                      basarili_adim=len(basarili), hizlar=basarili)


def _k4_durdur_saglik(surucu):
    adim = Adim("K4", "durdur() -> True ve saglikli() True")
    durdu = surucu.durdur()
    saglik = surucu.saglikli()
    nav_saglik = ika_nav.surucu_saglikli()
    olculen = (f"durdur()={durdu} saglikli()={saglik} "
               f"ika_nav.surucu_saglikli()={nav_saglik}")
    if not durdu:
        return adim.dustu(olculen, "durdur() False dondu — arac durmamis olabilir",
                          durdur=durdu, saglikli=saglik, nav_saglikli=nav_saglik)
    if not saglik:
        return adim.dustu(olculen, "durdurma basarili ama saglikli() False",
                          durdur=durdu, saglikli=saglik, nav_saglikli=nav_saglik)
    if not nav_saglik:
        return adim.dustu(olculen, "surucu saglikli ama ika_nav.surucu_saglikli() "
                                   "False — surucu ika_nav'a takili degil",
                          durdur=durdu, saglikli=saglik, nav_saglikli=nav_saglik)
    return adim.gecti(olculen, durdur=durdu, saglikli=saglik,
                      nav_saglikli=nav_saglik)


def _k5_fail_closed(surucu_adi):
    """YALNIZ sahte: tavan kadar ardisik ariza -> sagliksiz; tavanin bir
    altinda -> hala saglikli. Ayri bir SahteSurucu orneginde kosulur (ana
    surucunun ozel cagri sayacina dokunulmaz); sozlesme sinifa aittir."""
    adim = Adim("K5", f"fail-closed: {ARDISIK_HATA_TAVANI} ardisik ariza "
                      f"-> saglikli() False")
    if surucu_adi != "sahte":
        return adim.atlandi("ariza enjeksiyonu yalniz SahteSurucu'da mumkun")
    ariza_surucu = SahteSurucu(arizali_cagrilar=range(1, ARDISIK_HATA_TAVANI + 1))
    v = RAMPA_HEDEF_MS / RAMPA_ADIM
    for i in range(1, ARDISIK_HATA_TAVANI + 1):
        iletildi = ariza_surucu.hiz_ver(v, v)
        if iletildi:
            return adim.dustu(f"ariza {i} enjekte edilemedi (hiz_ver True)",
                              "SahteSurucu ariza enjeksiyonu calismadi")
        if i < ARDISIK_HATA_TAVANI and not ariza_surucu.saglikli():
            return adim.dustu(
                f"{i} arizada saglikli()=False (tavan {ARDISIK_HATA_TAVANI})",
                "tavanin altinda sagliksiz — erken tetikleme, tek gecici "
                "aksama gorevi durdurur", ardisik_hata=ariza_surucu.ardisik_hata)
    saglik = ariza_surucu.saglikli()
    olculen = (f"ardisik_hata={ariza_surucu.ardisik_hata} saglikli()={saglik}; "
               f"tavan-1'de saglikli()=True")
    if saglik:
        return adim.dustu(olculen, "tavana varildi ama saglikli() hala True",
                          ardisik_hata=ariza_surucu.ardisik_hata)
    adim.veri["ariza_surucu"] = ariza_surucu   # K6 toparlanma olcumu icin
    return adim.gecti(olculen, ardisik_hata=ariza_surucu.ardisik_hata,
                      saglikli=saglik)


def _k6_saglik_sifirlama(surucu, k4, k5):
    adim = Adim("K6", "basarili hiz_ver sonrasi ardisik_hata == 0")
    if k4.durum != GECTI:
        return adim.dustu(f"ardisik_hata={surucu.ardisik_hata}",
                          "K4 durdur() basarisiz; sifirlama OLCULEMEDI "
                          "(OLCULEMEDI != GECTI)")
    sayac = surucu.ardisik_hata
    if sayac != 0:
        return adim.dustu(f"ardisik_hata={sayac}",
                          "basarili durdur() sonrasi sayac sifirlanmadi",
                          ardisik_hata=sayac)
    olculen = f"ana surucu ardisik_hata={sayac}"
    ariza_surucu = k5.veri.pop("ariza_surucu", None)
    if ariza_surucu is not None:
        toparlandi = ariza_surucu.hiz_ver(0.0, 0.0)
        olculen += (f"; ariza sonrasi hiz_ver={toparlandi} "
                    f"ardisik_hata={ariza_surucu.ardisik_hata} "
                    f"saglikli()={ariza_surucu.saglikli()}")
        if not (toparlandi and ariza_surucu.ardisik_hata == 0
                and ariza_surucu.saglikli()):
            return adim.dustu(olculen, "tavan sonrasi basarili komut sayaci "
                                       "sifirlamadi / sagligi geri getirmedi",
                              ardisik_hata=sayac,
                              toparlanma_ardisik_hata=ariza_surucu.ardisik_hata)
        return adim.gecti(olculen, ardisik_hata=sayac,
                          toparlanma_ardisik_hata=ariza_surucu.ardisik_hata)
    return adim.gecti(olculen, ardisik_hata=sayac)


def kabul_turu(surucu, surucu_adi, uyku=time.sleep):
    """Tum adimlari kosar; dusen adimda DURMAZ (amac tabloyu tek koşuda gormek),
    ama K3'te ilk iletilemeyen hizda rampa kesilir. Sonda HER ZAMAN durdur().

    Doner: (adimlar, son_durdur) — son_durdur: turdan bagimsiz guvenli durus
    denemesinin sonucu (bool ya da istisna metni)."""
    adimlar = []
    ika_nav.surucu_ayarla(surucu)
    son_durdur = None
    try:
        k1 = Adim("K1", "durdur() -> True")
        durdu = surucu.durdur()
        adimlar.append(k1.gecti(f"durdur()={durdu}", durdur=durdu) if durdu
                       else k1.dustu(f"durdur()={durdu}",
                                     _hiz_ver_dustu_sebebi(surucu_adi),
                                     durdur=durdu))
        adimlar.append(_k2_konum(surucu))
        adimlar.append(_k3_rampa(surucu, surucu_adi, uyku))
        k4 = _k4_durdur_saglik(surucu)
        adimlar.append(k4)
        k5 = _k5_fail_closed(surucu_adi)
        adimlar.append(k5)
        adimlar.append(_k6_saglik_sifirlama(surucu, k4, k5))
    finally:
        # Fail-closed: tur nasil biterse bitsin arac durdurulur; istisna
        # sizmaz ama SAKLANMAZ da — rapora yazilir.
        try:
            son_durdur = bool(surucu.durdur())
        except Exception as hata:  # surucu sozlesmeyi bozup firlatirsa bile
            son_durdur = f"istisna: {type(hata).__name__}: {hata}"
        ika_nav.surucu_ayarla(None)
    return adimlar, son_durdur


def cikis_kodu(adimlar):
    return (CIKIS_GECTI if all(a.durum == GECTI for a in adimlar if a.zorunlu)
            else CIKIS_DUSTU)


# ── Rapor ───────────────────────────────────────────────────────────────────

def rapor_sozlugu(args, adimlar, son_durdur, kod, gozle_teyit):
    return {
        "surucu": args.surucu,
        "arka_uc": args.arka_uc,
        "tavan": ARDISIK_HATA_TAVANI,
        "rampa": {"hedef_ms": RAMPA_HEDEF_MS, "adim": RAMPA_ADIM,
                  "adim_suresi_s": RAMPA_ADIM_SURESI_S,
                  "max_speed_ms": ika_nav.MAX_SPEED},
        "adimlar": [a.sozluk() for a in adimlar],
        "son_durdur": son_durdur,
        "gozle_teyit_gerekli": gozle_teyit,
        "sonuc": GECTI if kod == CIKIS_GECTI else DUSTU,
        "cikis_kodu": kod,
    }


def tablo_yaz(args, adimlar, son_durdur, kod, gozle_teyit, akim=None):
    akim = akim or sys.stdout
    yaz = lambda s="": print(s, file=akim)  # noqa: E731
    yaz(f"IKA SURUCU KABUL TURU — surucu={args.surucu}"
        f"{' arka_uc=' + args.arka_uc if args.arka_uc else ''}"
        f"  tavan={ARDISIK_HATA_TAVANI}  rampa=0->{RAMPA_HEDEF_MS:.2f} m/s "
        f"/ {RAMPA_ADIM} adim / {RAMPA_ADIM_SURESI_S} s  (MAX_SPEED="
        f"{ika_nav.MAX_SPEED} m/s)")
    yaz(f"{'adim':<5} {'durum':<8} {'zorunlu':<8} olculen")
    for a in adimlar:
        yaz(f"{a.ad:<5} {a.durum:<8} {'evet' if a.zorunlu else 'hayir':<8} "
            f"{a.baslik}: {a.olculen}")
        if a.uyari:
            yaz(f"{'':<5} UYARI    {a.uyari}")
        if a.sebep:
            yaz(f"{'':<5} SEBEP    {a.sebep}")
    yaz(f"SON DURDUR (fail-closed): durdur()={son_durdur}")
    if gozle_teyit:
        yaz("GOZLE TEYIT ET: rampa sirasinda arac GERCEKTEN hareket etti mi ve "
            "K4'te durdu mu? Yazilim bunu OLCEMEZ; insan teyidi olmadan kabul "
            "TAMAMLANMIS sayilmaz.")
    yaz(f"SONUC: {GECTI if kod == CIKIS_GECTI else DUSTU} (exit {kod})")


def arg_ayristirici():
    p = argparse.ArgumentParser(
        description="IKA surucu kabul turu (CONTRACTS §7.2 sozlesmesi)")
    p.add_argument("--surucu", choices=SURUCULER, required=True)
    p.add_argument("--arka-uc", default=None,
                   help="gercek icin 'modul:Sinif' (hiz_ver/konum_al sunan nesne)")
    p.add_argument("--json", action="store_true",
                   help=f"tablodan sonra '{JSON_AYRAC}' ayraci ve JSON bas")
    p.add_argument("--json-dosya", default=None, help="JSON raporu bu dosyaya yaz")
    p.add_argument("--arizali-cagrilar", default="",
                   help="sahte: 1 tabanli hiz_ver cagri numaralari, virgullu "
                        "(ariza enjeksiyonu; K1 = cagri 1, K3 = 2..%d)"
                        % (RAMPA_ADIM + 1))
    p.add_argument("--sahte-konum-yok", action="store_true",
                   help="sahte: konum_al hep None dortlusu (KONUM YOK yolu)")
    p.add_argument("--gz-topic", default=VARSAYILAN_TOPIC)
    p.add_argument("--gz-model", default=VARSAYILAN_MODEL)
    return p


def main(argv=None):
    args = arg_ayristirici().parse_args(argv)
    try:
        surucu = surucu_kur(args)
    except IkaSurucuHatasi as hata:
        print(f"DONANIM_YOK — beklenen (Faz B oncesi): GercekSurucu arka ucu yok; "
              f"kabul turu BASLAMADI. Arka uc dolunca --arka-uc modul:Sinif ile "
              f"kos. Ayrinti: {hata}")
        print(f"SONUC: SURUCU_KURULAMADI (exit {CIKIS_SURUCU_KURULAMADI})")
        return CIKIS_SURUCU_KURULAMADI
    except (ArkaUcYuklenemedi, ValueError) as hata:
        print(f"SURUCU_KURULAMADI: {hata}")
        print(f"SONUC: SURUCU_KURULAMADI (exit {CIKIS_SURUCU_KURULAMADI})")
        return CIKIS_SURUCU_KURULAMADI

    gozle_teyit = args.surucu != "sahte"
    try:
        adimlar, son_durdur = kabul_turu(surucu, args.surucu)
        kod = cikis_kodu(adimlar)
    except Exception as hata:  # tur cokerse: fail-closed, DUSTU
        print(f"COKME: kabul turu istisnayla kesildi — "
              f"{type(hata).__name__}: {hata}")
        print(f"SONUC: {DUSTU} (exit {CIKIS_DUSTU})")
        return CIKIS_DUSTU

    tablo_yaz(args, adimlar, son_durdur, kod, gozle_teyit)
    rapor = rapor_sozlugu(args, adimlar, son_durdur, kod, gozle_teyit)
    if args.json_dosya:
        Path(args.json_dosya).write_text(
            json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json:
        print(JSON_AYRAC)
        print(json.dumps(rapor, ensure_ascii=False, indent=2))
    return kod


if __name__ == "__main__":
    sys.exit(main())
