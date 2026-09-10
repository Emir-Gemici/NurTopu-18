"""TLOG / DATAFLASH AKIM OZETI — guc modulu (PM06) akim/gerilimini motor PWM'iyle YAN YANA koyar.

NEDEN (T219, saha kosum kagidi adim 6): FDR itki butcesi (BOLUM_3 §3.2.1.1.1) ve
ACIK_KALEMLER kalem 12 "asili kalma akimi, tepe akim" ister; kaynak PM06 telemetrisi
(BATTERY_STATUS) ya da DataFlash BAT mesajidir. Mission Planner grafiginden gozle
okunan sayi tutanak degildir; bu betik dosyadan okur ve pencere basina yazar.

NEDEN PWM yan yana: akim tek basina yalan soyleyebilir. 6 Eylul tlog'unda
(results/ucus_loglari/20260906/2026-09-06 19-52-44.tlog) motorlar pervaneli 1949 PWM'e
cikarken BATTERY_STATUS.current_battery en fazla 0,44 A okudu (bu betikle olculdu;
results/fdr_sprint_20260910/saha_kosum/tlog_akim_ozet_20260906.txt). Yani PM06 akim
hatti o gun ya bagli degildi ya da olcek yanlisti. Betik bu durumu KENDISI isaretler:
bir pencerede AUX PWM tepe >= PWM_YUK_ESIGI iken akim tepe < AKIM_SUPHE_ESIGI_A ise
UYARI basar — "olcum var" ile "olcum anlamli" ayrilir.

Girdi: Mission Planner .tlog (BATTERY_STATUS / SYS_STATUS / SERVO_OUTPUT_RAW) ya da
DataFlash .bin (BAT / RCOU). Pencere: --pencere s (varsayilan 60). Kanallar: AUX1-4 =
SERVO9-12 (D-428 §5d, config/pixhawk/arducopter_fda_20260906.param) — --kanallar ile ezilir.

Cikis kodlari: 0 ozet yazildi (UYARI olsa da; hukmu okuyan verir) · 2 dosya yok ya da
hic akim mesaji yok (OLCULEMEDI — sessiz bos tablo basilmaz).

Kullanim:
  tlog_akim_ozet.py "results/ucus_loglari/20260906/2026-09-06 19-52-44.tlog"
  tlog_akim_ozet.py 00000012.BIN --pencere 30 --json results/.../akim.json
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

#: AUX1-4 = SERVO9-12 (D-428 §5d): ESC'ler bu cikislarda; tlog SERVO_OUTPUT_RAW servoN_raw,
#: DataFlash RCOU.CN alanlari.
VARSAYILAN_KANALLAR = (9, 10, 11, 12)
VARSAYILAN_PENCERE_S = 60.0
#: Turkiye saati (UTC+3) — tlog zaman damgasi UTC epoch'tur; tablo yerel saatle okunur.
VARSAYILAN_SAAT_OFSETI = 3
#: PWM tepe bu degerin ustundeyse motorlar yuk altindadir (~%40 gaz; 6 Eylul'de ilk egilme
#: 1446'da basladi, D-434 olcum 4). Pervaneli dort motor bu gazda onlarca amper ceker.
PWM_YUK_ESIGI = 1400
#: Yuk altinda akim tepe bunun altindaysa akim hatti/olcek supheli (aviyonik bosta ~0,3-0,5 A;
#: 6 Eylul'de olculen 0,44 A tam bu banttadir).
AKIM_SUPHE_ESIGI_A = 1.0

CIKIS_TAMAM, CIKIS_OLCULEMEDI = 0, 2

# tlog ve DataFlash mesaj adlari — iki bicim de ayni tabloya duser
AKIM_TIPLERI = ("BATTERY_STATUS", "SYS_STATUS", "BAT")
PWM_TIPLERI = ("SERVO_OUTPUT_RAW", "RCOU")


def _akim_gerilim(msg):
    """(akim_A, gerilim_V) ya da None — mesaj tipine gore birim donusumu."""
    tp = msg.get_type()
    try:
        if tp == "BATTERY_STATUS":
            i = msg.current_battery          # cA (10 mA); -1 = olculmuyor
            v = msg.voltages[0]              # mV; 65535 = yok
            if i < 0 or v == 65535:
                return None
            return i / 100.0, v / 1000.0
        if tp == "SYS_STATUS":
            i = msg.current_battery          # cA; -1 = olculmuyor
            v = msg.voltage_battery          # mV
            if i < 0:
                return None
            return i / 100.0, v / 1000.0
        if tp == "BAT":                      # DataFlash: Curr (A), Volt (V)
            return float(msg.Curr), float(msg.Volt)
    except (AttributeError, IndexError, TypeError, ValueError):
        return None
    return None


def _pwm_tepe(msg, kanallar):
    """Verilen kanallardaki en yuksek PWM (us) ya da None."""
    tp = msg.get_type()
    degerler = []
    for k in kanallar:
        ad = f"servo{k}_raw" if tp == "SERVO_OUTPUT_RAW" else f"C{k}"
        d = getattr(msg, ad, None)
        if isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0:
            degerler.append(int(d))
    return max(degerler) if degerler else None


def _yuzdelik(degerler, p):
    if not degerler:
        return None
    s = sorted(degerler)
    k = max(1, min(len(s), math.ceil(p / 100.0 * len(s))))
    return s[k - 1]


def pencereleri_hesapla(mesajlar, pencere_s, kanallar):
    """(mesaj) akisindan pencere sozlukleri (t_bas'a gore sirali). Saf: dosya acmaz."""
    if not (pencere_s > 0):
        raise ValueError("pencere > 0 olmali")
    kutular = {}
    t0 = None
    for msg in mesajlar:
        t = getattr(msg, "_timestamp", None)
        if t is None:                 # 0.0 gecerli damgadir; `not t` onu da atlardi (test yakaladi)
            continue
        if t0 is None:
            t0 = t
        anahtar = int((t - t0) // pencere_s)
        k = kutular.setdefault(anahtar, {"akim": [], "gerilim": [], "pwm": []})
        tp = msg.get_type()
        if tp in AKIM_TIPLERI:
            ag = _akim_gerilim(msg)
            if ag is not None:
                k["akim"].append(ag[0])
                k["gerilim"].append(ag[1])
        elif tp in PWM_TIPLERI:
            p = _pwm_tepe(msg, kanallar)
            if p is not None:
                k["pwm"].append(p)
    satirlar = []
    for anahtar in sorted(kutular):
        k = kutular[anahtar]
        if not k["akim"] and not k["pwm"]:
            continue
        pwm_max = max(k["pwm"]) if k["pwm"] else None
        i_max = max(k["akim"]) if k["akim"] else None
        supheli = (pwm_max is not None and pwm_max >= PWM_YUK_ESIGI
                   and i_max is not None and i_max < AKIM_SUPHE_ESIGI_A)
        satirlar.append({
            "t_bas_s": anahtar * pencere_s,
            "t_bas_epoch": (t0 + anahtar * pencere_s) if t0 else None,
            "n_akim": len(k["akim"]),
            "akim_p50_A": _yuzdelik(k["akim"], 50),
            "akim_maks_A": i_max,
            "gerilim_min_V": min(k["gerilim"]) if k["gerilim"] else None,
            "pwm_maks": pwm_max,
            "supheli": supheli,
        })
    return satirlar


def dosyadan_mesajlar(yol):
    """pymavlink ile tlog/bin oku; yalniz ilgili tipleri uret."""
    from pymavlink import mavutil  # tembel: --help pymavlink istemez
    m = mavutil.mavlink_connection(str(yol))
    tipler = list(AKIM_TIPLERI + PWM_TIPLERI)
    try:
        while True:
            msg = m.recv_match(type=tipler, blocking=False)
            if msg is None:
                return
            yield msg
    finally:
        # Dosya tutamaci acik kalirsa Windows'ta tlog silinemez/tasinamaz (test yakaladi).
        for kapat in (getattr(m, "close", None), getattr(getattr(m, "f", None), "close", None)):
            try:
                if kapat:
                    kapat()
            except Exception:
                pass


def _saat(epoch, ofset_saat):
    if epoch is None:
        return "-"
    return time.strftime("%H:%M:%S", time.gmtime(epoch + ofset_saat * 3600))


def tablo_metni(satirlar, ofset_saat, kanallar):
    s = [f"{'pencere':>8} {'n':>5} {'I_p50 A':>8} {'I_maks A':>9} {'V_min V':>8} "
         f"{'PWM_maks':>8}  not   (kanallar {','.join(map(str, kanallar))})"]
    for r in satirlar:
        f = lambda x, b: "-" if x is None else f"{x:{b}}"  # noqa: E731
        s.append(f"{_saat(r['t_bas_epoch'], ofset_saat):>8} {r['n_akim']:>5} "
                 f"{f(r['akim_p50_A'], '8.2f')} {f(r['akim_maks_A'], '9.2f')} "
                 f"{f(r['gerilim_min_V'], '8.2f')} {f(r['pwm_maks'], '8d')}  "
                 f"{'UYARI' if r['supheli'] else ''}")
    tum_akim = [r["akim_maks_A"] for r in satirlar if r["akim_maks_A"] is not None]
    tum_pwm = [r["pwm_maks"] for r in satirlar if r["pwm_maks"] is not None]
    s.append(f"TOPLAM: akim tepe {max(tum_akim):.2f} A" if tum_akim else "TOPLAM: akim mesaji YOK")
    if tum_pwm:
        s[-1] += f" · PWM tepe {max(tum_pwm)}"
    if any(r["supheli"] for r in satirlar):
        s.append(f"UYARI: PWM >= {PWM_YUK_ESIGI} iken akim tepe < {AKIM_SUPHE_ESIGI_A:g} A olan "
                 "pencere var — PM06 akim hatti bagli degil ya da BATT_AMP_PERVLT yanlis; "
                 "pens ampermetreyle karsilastir (bu dosyadaki akim OLCUM SAYILMAZ)")
    return "\n".join(s)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dosya", help="Mission Planner .tlog ya da DataFlash .bin")
    ap.add_argument("--pencere", type=float, default=VARSAYILAN_PENCERE_S,
                    help="pencere suresi s (varsayilan %(default)s)")
    ap.add_argument("--kanallar", default=",".join(map(str, VARSAYILAN_KANALLAR)),
                    help="PWM tepe icin servo kanallari (varsayilan AUX1-4 = %(default)s)")
    ap.add_argument("--saat-ofseti", type=int, default=VARSAYILAN_SAAT_OFSETI,
                    help="tabloda yerel saat icin UTC ofseti (varsayilan %(default)s)")
    ap.add_argument("--json", default=None, metavar="DOSYA", help="pencereleri JSON yaz")
    a = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    if not (a.pencere > 0):
        ap.error("--pencere > 0 olmali")
    try:
        kanallar = tuple(int(k) for k in a.kanallar.split(",") if k.strip())
    except ValueError:
        ap.error("--kanallar virgulle ayrilmis tamsayi olmali")
    if not kanallar or any(k < 1 or k > 16 for k in kanallar):
        ap.error("--kanallar 1..16 arasinda en az bir kanal")
    yol = Path(a.dosya)
    if not yol.is_file():
        print(f"OLCULEMEDI: dosya yok: {yol}", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    satirlar = pencereleri_hesapla(dosyadan_mesajlar(yol), a.pencere, kanallar)
    if not any(r["n_akim"] for r in satirlar):
        print(f"OLCULEMEDI: {yol.name} icinde akim mesaji yok "
              f"({'/'.join(AKIM_TIPLERI)})", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    print(f"AKIM OZETI  {yol.name}  pencere {a.pencere:g} s  "
          f"(PM06 telemetrisi; pens ampermetre karsilastirmasi ayrica yapilir)")
    print(tablo_metni(satirlar, a.saat_ofseti, kanallar))
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"dosya": yol.name, "pencere_s": a.pencere, "kanallar": list(kanallar),
             "pwm_yuk_esigi": PWM_YUK_ESIGI, "akim_suphe_esigi_A": AKIM_SUPHE_ESIGI_A,
             "pencereler": satirlar}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"JSON: {a.json}")
    return CIKIS_TAMAM


if __name__ == "__main__":
    sys.exit(main())
