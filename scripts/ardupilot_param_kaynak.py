#!/usr/bin/env python3
"""ArduPilot .param dosyasini SABIT bir surum etiketinin KAYNAK KODUNA baglar (T221 · K11).

NEDEN (D-425, 5 Eylul sahada olculdu): Copter parametre dosyasi Mission Planner'in
onerdigi 4.7.1'e yuklendi ve MP "Missing 9 params" dedi - dosya baska bir surumun
anlambilimiyle eslesmiyordu. Bir .param dosyasindaki her AD'in, secilen etiketin
(or. Plane-4.5.7) kaynaginda bir `@Param` tanimi olmali; DEGER'i de o tanimin
`@Values` / `@Bitmask` / `@Range` alanina uymali. Bu betik ikisini ArduPilot
KAYNAGINDAN okur ve kanit JSON'u yazar. Test (tests/test_faz_b_arduplane_sablon.py)
kaniti cevrimdisi denetler; ag yalniz bu betik kosarken gerekir.

KULLANIM (PC, depo venv'i):
  python scripts/ardupilot_param_kaynak.py \\
      --param config/pixhawk/arduplane_final.param --etiket Plane-4.5.7 \\
      --cikti results/fdr_sprint_20260910/H8/T221/plane457_param_kaynak.json
  --onbellek DIZIN   indirilen kaynak dosyalari DIZIN'e yazilir / oradan okunur

CIKIS KODLARI: 0 her ad bulundu, her deger tanima uyuyor | 1 hatali cagri |
2 kaynak indirilemedi | 3 en az bir ad kaynakta YOK ya da deger tanim disinda
(kanit dosyasi 3'te de yazilir - neyin dustugu gorunur olsun).

SINIR: ad cozumlemesi asagidaki onek tablosuyla yapilir (ArduPilot grup onekleri);
tabloda olmayan bir grup ust duzey (<arac>/Parameters.cpp) sanilir ve bulunamazsa
"YOK" yazilir - sessizce gecmez.
"""

import argparse
import hashlib
import json
import math
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
HAM_URL = "https://raw.githubusercontent.com/ArduPilot/ardupilot/{etiket}/{yol}"
ETIKET_URL = "https://api.github.com/repos/ArduPilot/ardupilot/git/ref/tags/{etiket}"
# etiket oneki -> (arac adi @Values{...} icin, arac kaynak dizini)
ARACLAR = {"Plane": ("Plane", "ArduPlane"), "Copter": ("Copter", "ArduCopter"),
           "Rover": ("Rover", "Rover"), "Sub": ("Sub", "ArduSub")}

BLOK_BASI = re.compile(r"^//\s*@Param(?:\{([^}]*)\})?:\s*(\S+)\s*$")
ALAN = re.compile(r"^//\s*@(\w+)(?:\{([^}]*)\})?:\s*(.*)$")


def _kume(metin):
    return {x.strip() for x in metin.split(",") if x.strip()} if metin else None


def aday_kaynaklar(ad, arac_dizini):
    """AD -> [(kaynak yolu, @Param goreli adi)]; ilk bulunan kazanir.

    Onekler ArduPilot grup kayitlaridir (Plane-4.5.7: ArduPlane/Parameters.cpp
    GOBJECT/AP_SUBGROUPINFO satirlari; ARSPD: AP_Vehicle.cpp + AP_Airspeed.cpp).
    """
    kurallar = (
        (r"SERVO(\d{1,2})_(\w+)", "libraries/SRV_Channel/SRV_Channel.cpp", lambda m: m[2]),
        (r"SR(\d)_(\w+)", f"{arac_dizini}/GCS_Mavlink.cpp", lambda m: m[2]),
        (r"SERIAL(\d)_(\w+)", "libraries/AP_SerialManager/AP_SerialManager.cpp",
         lambda m: f"{m[1]}_{m[2]}"),
        (r"BRD_(\w+)", "libraries/AP_BoardConfig/AP_BoardConfig.cpp", lambda m: m[1]),
        (r"BATT_(\w+)", "libraries/AP_BattMonitor/AP_BattMonitor_Params.cpp", lambda m: m[1]),
        (r"RC_(\w+)", "libraries/RC_Channel/RC_Channels_VarInfo.h", lambda m: "_" + m[1]),
        (r"ARMING_(\w+)", "libraries/AP_Arming/AP_Arming.cpp", lambda m: m[1]),
        (r"CHUTE_(\w+)", "libraries/AP_Parachute/AP_Parachute.cpp", lambda m: m[1]),
        (r"ARSPD_(\w+)", "libraries/AP_Airspeed/AP_Airspeed_Params.cpp", lambda m: m[1]),
        (r"Q_(\w+)", f"{arac_dizini}/quadplane.cpp", lambda m: m[1]),
        (r"LOG_(?!BITMASK$)(\w+)", "libraries/AP_Logger/AP_Logger.cpp", lambda m: "_" + m[1]),
    )
    adaylar = []
    for desen, yol, goreli in kurallar:
        m = re.fullmatch(desen, ad)
        if m:
            adaylar.append((yol, goreli(m)))
            break
    adaylar.append((f"{arac_dizini}/Parameters.cpp", ad))
    return adaylar


def bloklar(metin):
    """Kaynak metnindeki `@Param` bloklari (satir numarasi 1 tabanli)."""
    satirlar = metin.splitlines()
    sonuc = []
    i = 0
    while i < len(satirlar):
        m = BLOK_BASI.match(satirlar[i].strip())
        if not m:
            i += 1
            continue
        alanlar = []
        j = i + 1
        while j < len(satirlar):
            t = satirlar[j].strip()
            if not t or t.startswith("#"):
                j += 1
                continue
            if not t.startswith("//") or BLOK_BASI.match(t):
                break
            a = ALAN.match(t)
            if a:
                alanlar.append((a.group(1), _kume(a.group(2)), a.group(3).strip()))
            j += 1
        sonuc.append({"satir": i + 1, "ad": m.group(2), "araclar": _kume(m.group(1)),
                      "alanlar": alanlar, "tanim_satiri": j + 1,
                      "tanim": satirlar[j].strip() if j < len(satirlar) else ""})
        i = j if j > i else i + 1
    return sonuc


def alan_sec(alanlar, alan_adi, arac):
    """Araca ozel satirlar varsa onlar, yoksa genel satirlar (birden cok satir birlesir)."""
    ozel = [d for a, ar, d in alanlar if a == alan_adi and ar and arac in ar]
    if ozel:
        return ozel
    return [d for a, ar, d in alanlar if a == alan_adi and ar is None]


def sayi_anahtarlari(satirlar):
    """'@Values' / '@Bitmask' satirlarindaki 'anahtar:ad' anahtarlari (float)."""
    anahtarlar = set()
    for satir in satirlar:
        for parca in satir.split(","):
            if ":" not in parca:
                continue
            anahtar = parca.split(":", 1)[0].strip()
            try:
                anahtarlar.add(float(anahtar))
            except ValueError:
                continue
    return anahtarlar


def deger_denetle(deger, values, bitmask, aralik):
    """(gecerli, neden). Tanimda kisit yoksa gecerli ama nedeni soyler."""
    if values:
        izinli = sayi_anahtarlari(values)
        if not any(math.isclose(deger, k) for k in izinli):
            return False, f"deger {deger:g} @Values disinda"
    if bitmask:
        if deger < 0 or deger != int(deger):
            return False, f"deger {deger:g} bitmask icin negatif/kesirli"
        bitler = {int(b) for b in sayi_anahtarlari(bitmask)}
        disari = [b for b in range(64) if (int(deger) >> b) & 1 and b not in bitler]
        if disari:
            return False, f"@Bitmask disi bitler {disari}"
    if aralik:
        try:
            alt, ust = (float(x) for x in aralik[0].split()[:2])
        except ValueError:
            return False, f"@Range okunamadi: {aralik[0]!r}"
        if not alt <= deger <= ust:
            return False, f"deger {deger:g} @Range {alt:g}..{ust:g} disinda"
    if not (values or bitmask or aralik):
        return True, "tanimda deger kisiti yok (yalniz ad dogrulandi)"
    return True, "gecerli"


class Kaynak:
    """Etiketli ArduPilot kaynak dosyalarini indirir/onbellekler."""

    def __init__(self, etiket, onbellek=None):
        self.etiket = etiket
        self.onbellek = Path(onbellek) if onbellek else None
        self._metin = {}
        self.dosyalar = {}

    def oku(self, yol):
        if yol in self._metin:
            return self._metin[yol]
        veri = None
        yerel = None
        if self.onbellek:
            yerel = self.onbellek / self.etiket / yol
            if yerel.exists():
                veri = yerel.read_bytes()
        if veri is None:
            try:
                with urllib.request.urlopen(HAM_URL.format(etiket=self.etiket, yol=yol),
                                            timeout=60) as y:
                    veri = y.read()
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self._metin[yol] = None
                    return None
                raise
            if yerel is not None:
                yerel.parent.mkdir(parents=True, exist_ok=True)
                yerel.write_bytes(veri)
        self.dosyalar[yol] = {"bayt": len(veri), "sha256": hashlib.sha256(veri).hexdigest()}
        self._metin[yol] = veri.decode("utf-8", errors="replace")
        return self._metin[yol]


def cozumle(ad, kaynak, arac, arac_dizini, _derinlik=0):
    """AD -> kanit kaydi (bulunamazsa 'kaynak' None)."""
    for yol, goreli in aday_kaynaklar(ad, arac_dizini):
        metin = kaynak.oku(yol)
        if metin is None:
            continue
        adaylar = [b for b in bloklar(metin) if b["ad"] == goreli
                   and (b["araclar"] is None or arac in b["araclar"])]
        if not adaylar:
            continue
        b = adaylar[0]
        kayit = {"kaynak": yol, "satir": b["satir"], "goreli_ad": goreli,
                 "tanim_satiri": b["tanim_satiri"], "tanim": b["tanim"],
                 "tanim_eslesti": f'"{goreli}"' in b["tanim"],
                 "values": alan_sec(b["alanlar"], "Values", arac),
                 "bitmask": alan_sec(b["alanlar"], "Bitmask", arac),
                 "range": alan_sec(b["alanlar"], "Range", arac),
                 "copy_from": None}
        kopya = (alan_sec(b["alanlar"], "CopyFieldsFrom", arac)
                 or alan_sec(b["alanlar"], "CopyValuesFrom", arac))
        if kopya and _derinlik < 3:
            kayit["copy_from"] = kopya[0]
            ust = cozumle(kopya[0], kaynak, arac, arac_dizini, _derinlik + 1)
            for alan in ("values", "bitmask", "range"):
                if not kayit[alan] and ust.get(alan):
                    kayit[alan] = ust[alan]
        return kayit
    return {"kaynak": None, "satir": None, "goreli_ad": None, "tanim_satiri": None,
            "tanim": "", "tanim_eslesti": False, "values": [], "bitmask": [],
            "range": [], "copy_from": None}


def param_dosyasi_oku(yol):
    """Mission Planner ayirmasi: '#' atlanir, bosluk/virgul/sekme ile [0] ad, [1] deger."""
    cift = []
    for ham in Path(yol).read_text(encoding="utf-8").splitlines():
        satir = ham.strip()
        if not satir or satir.startswith("#"):
            continue
        parcalar = [p for p in re.split(r"[ ,\t]+", satir) if p]
        cift.append((parcalar[0], float(parcalar[1])))
    return cift


def etiket_commit(etiket):
    """Etiketin gosterdigi commit (hafif etiket -> dogrudan; nesne etiket -> bir kat)."""
    with urllib.request.urlopen(ETIKET_URL.format(etiket=etiket), timeout=60) as y:
        d = json.loads(y.read())
    nesne = d["object"]
    if nesne.get("type") == "tag":
        with urllib.request.urlopen(nesne["url"], timeout=60) as y:
            nesne = json.loads(y.read())["object"]
    return nesne["sha"]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--param", required=True, help=".param dosyasi")
    ap.add_argument("--etiket", required=True, help="ArduPilot git etiketi, or. Plane-4.5.7")
    ap.add_argument("--cikti", required=True, help="kanit JSON yolu")
    ap.add_argument("--onbellek", default=None, help="kaynak dosya onbellegi (istege bagli)")
    a = ap.parse_args(argv)

    onek = a.etiket.split("-", 1)[0]
    if onek not in ARACLAR or not Path(a.param).exists():
        print(f"HATA: etiket oneki {onek!r} bilinmiyor ya da {a.param} yok", file=sys.stderr)
        return 1
    arac, arac_dizini = ARACLAR[onek]
    kaynak = Kaynak(a.etiket, a.onbellek)
    try:
        commit = etiket_commit(a.etiket)
        cift = param_dosyasi_oku(a.param)
        kayitlar = []
        for ad, deger in cift:
            k = cozumle(ad, kaynak, arac, arac_dizini)
            if k["kaynak"] is None:
                gecerli, neden = False, "ad kaynakta YOK"
            else:
                gecerli, neden = deger_denetle(deger, k["values"], k["bitmask"], k["range"])
            kayitlar.append({"ad": ad, "deger": deger, **k, "gecerli": gecerli, "neden": neden})
    except (urllib.error.URLError, OSError) as e:
        print(f"HATA: kaynak indirilemedi: {e}", file=sys.stderr)
        return 2

    try:
        param_goreli = Path(a.param).resolve().relative_to(KOK).as_posix()
    except ValueError:
        param_goreli = str(a.param)
    kanit = {
        "etiket": a.etiket, "commit": commit, "arac": arac,
        "commit_kaynagi": ETIKET_URL.format(etiket=a.etiket),
        "param_dosyasi": param_goreli,
        "uretici": "scripts/ardupilot_param_kaynak.py",
        "uretim_zamani": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kaynak_dosyalari": dict(sorted(kaynak.dosyalar.items())),
        "parametreler": kayitlar,
        "ozet": {"toplam": len(kayitlar),
                 "bulunamayan": [k["ad"] for k in kayitlar if k["kaynak"] is None],
                 "gecersiz": [k["ad"] for k in kayitlar if not k["gecerli"]]},
    }
    cikti = Path(a.cikti)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    cikti.write_text(json.dumps(kanit, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    oz = kanit["ozet"]
    print(f"{a.etiket} ({commit[:10]}) · {oz['toplam']} parametre · "
          f"bulunamayan {len(oz['bulunamayan'])} · gecersiz {len(oz['gecersiz'])} -> {cikti}")
    for k in kayitlar:
        if not k["gecerli"]:
            print(f"  DUSTU {k['ad']}={k['deger']:g}: {k['neden']}")
    return 0 if not oz["gecersiz"] else 3


if __name__ == "__main__":
    sys.exit(main())
