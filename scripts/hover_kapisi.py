"""HOVER KAPISI — kisa hover sonrasi VibeZ ve motor cikis farki esigini otomatik denetler.

NEDEN (2026-09-17): 17 Eylul 02:53 dusuşünden once, motor cikis farki 13 saniye boyunca
+16 us'den +520 us'ye BUYUDU ve titresim oturumun basindan beri onceki uçuşlarin 2,5-3
katiydi (Windows PC'de Pixhawk logunun ELLE, goz karariyla okunmasiyla fark edildi —
LOG-DURUMU.md §3). O log kontrolunden gecemeyecek onceki kisa hover de ayni sekilde
goz kararindan kacmisti. Takim bu yuzden kural koydu: "her ilk kisa hover'dan sonra log
kontrol edilecek (VibeZ <= 16, motor cikis farki <= 60 us); gecmezse uçulmayacak." Bu
betik o kontrolu otomatiklestirir — proje kulturu "OLCULEMEDI != GECTI"dir, goz karari
kapi sayilmaz.

NE OLCER (tum dosya + --pencere ile zaman-ici egilim tablosu):
  - VibeZ tepe: DataFlash VIBE.VibeZ ya da tlog VIBRATION.vibration_z (m/s/s). Ikisi de
    ArduPilot'un ayni get_vibration_levels() hesabindan gelir — DEGERLER ESDEGER
    varsayilir, format farki yalniz DataFlash/canli-telemetri arasindadir.
  - Motor cikis farki tepe: yapilandirilmis kanallar arasinda (varsayilan AUX1-4 =
    SERVO9-12, D-428 §5d, config/pixhawk/arducopter_fda_20260906.param — tlog_akim_ozet.py
    ile AYNI kanallar) her ornekte max-min, dosya genelinde tepe deger (us).

Girdi: DataFlash .bin (VIBE / RCOU) ya da Mission Planner .tlog (VIBRATION /
SERVO_OUTPUT_RAW) — tlog_akim_ozet.py'deki gibi ikisi de mavutil ile okunur, format
ayrimi mesaj adindan gelir, dosya uzantisina bakilmaz.

ESIKLER (VIBEZ_ESIK=16, MOTOR_FARK_ESIK_US=60) takimin 2026-09-17 karari — ON KAYITLIDIR,
--vibez-esik/--motor-fark-esik-us yalniz kesif/teshis icindir; asil KAPI hukmu icin
esikleri GEVSETMEK bu betigin amacini bozar (ÖLÇÜLEMEDİ ≠ GEÇTİ kulturu).

Kapi: KAPI: TAMAM (ikisi de esigin altinda) · KAPI: BASARISIZ (biri esigi astiysa) ·
OLCULEMEDI (dosyada VIBE/VIBRATION ya da PWM mesaji yok — sessiz "gecti" basilmaz).

Cikis kodlari: 0 TAMAM (tum dosyalar) · 1 en az bir dosya BASARISIZ · 2 en az bir dosya
OLCULEMEDI (ve hicbiri BASARISIZ degilse).

Kullanim:
  hover_kapisi.py results/ucus_loglari/20260917/00000099.BIN
  hover_kapisi.py "results/.../ilk_hover.tlog" --pencere 2 --json results/.../hover_kapi.json
  hover_kapisi.py log1.bin log2.bin        # birden fazla dosya; en kotu sonuc dondurulur
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

#: AUX1-4 = SERVO9-12 (D-428 §5d): motorlar bu ciktilarda — tlog_akim_ozet.py ile ayni
#: varsayilan, ayni gerekce.
VARSAYILAN_KANALLAR = (9, 10, 11, 12)
VARSAYILAN_PENCERE_S = 2.0
#: Turkiye saati (UTC+3) — tlog zaman damgasi UTC epoch'tur.
VARSAYILAN_SAAT_OFSETI = 3

#: Takimin 2026-09-17 karari (17 Eylul dusuşü sonrasi) — ON KAYITLI, gevsetilmez.
VIBEZ_ESIK = 16.0
MOTOR_FARK_ESIK_US = 60.0

CIKIS_TAMAM, CIKIS_BASARISIZ, CIKIS_OLCULEMEDI = 0, 1, 2

VIBE_TIPLERI = ("VIBRATION", "VIBE")
PWM_TIPLERI = ("SERVO_OUTPUT_RAW", "RCOU")


def _vibez(msg):
    """VibeZ (m/s/s) ya da None — mesaj tipine gore alan adi degisir."""
    tp = msg.get_type()
    try:
        if tp == "VIBRATION":
            return float(msg.vibration_z)
        if tp == "VIBE":
            return float(msg.VibeZ)
    except (AttributeError, TypeError, ValueError):
        return None
    return None


def _motor_degerleri(msg, kanallar):
    """Verilen kanallardaki PWM degerleri (us), en az 2 kanal yoksa None."""
    tp = msg.get_type()
    degerler = []
    for k in kanallar:
        ad = f"servo{k}_raw" if tp == "SERVO_OUTPUT_RAW" else f"C{k}"
        d = getattr(msg, ad, None)
        if isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0:
            degerler.append(int(d))
    return degerler if len(degerler) >= 2 else None


def pencereleri_hesapla(mesajlar, pencere_s, kanallar, vibez_esik=VIBEZ_ESIK,
                         motor_fark_esik_us=MOTOR_FARK_ESIK_US):
    """(mesaj) akisindan pencere sozlukleri (t_bas'a gore sirali). Saf: dosya acmaz."""
    if not (pencere_s > 0):
        raise ValueError("pencere > 0 olmali")
    kutular = {}
    t0 = None
    for msg in mesajlar:
        t = getattr(msg, "_timestamp", None)
        if t is None:                 # 0.0 gecerli damgadir; `not t` onu da atlardi
            continue
        if t0 is None:
            t0 = t
        anahtar = int((t - t0) // pencere_s)
        k = kutular.setdefault(anahtar, {"vibez": [], "motor_fark": []})
        tp = msg.get_type()
        if tp in VIBE_TIPLERI:
            vz = _vibez(msg)
            if vz is not None:
                k["vibez"].append(vz)
        elif tp in PWM_TIPLERI:
            d = _motor_degerleri(msg, kanallar)
            if d is not None:
                k["motor_fark"].append(max(d) - min(d))
    satirlar = []
    for anahtar in sorted(kutular):
        k = kutular[anahtar]
        if not k["vibez"] and not k["motor_fark"]:
            continue
        vz_max = max(k["vibez"]) if k["vibez"] else None
        mf_max = max(k["motor_fark"]) if k["motor_fark"] else None
        satirlar.append({
            "t_bas_s": anahtar * pencere_s,
            "t_bas_epoch": (t0 + anahtar * pencere_s) if t0 else None,
            "n_vibe": len(k["vibez"]),
            "vibez_maks": vz_max,
            "n_pwm": len(k["motor_fark"]),
            "motor_fark_maks_us": mf_max,
            "esik_asildi": (vz_max is not None and vz_max > vibez_esik)
                           or (mf_max is not None and mf_max > motor_fark_esik_us),
        })
    return satirlar


def dosyadan_mesajlar(yol):
    """pymavlink ile tlog/bin oku; yalniz ilgili tipleri uret."""
    from pymavlink import mavutil  # tembel: --help pymavlink istemez
    m = mavutil.mavlink_connection(str(yol))
    tipler = list(VIBE_TIPLERI + PWM_TIPLERI)
    try:
        while True:
            msg = m.recv_match(type=tipler, blocking=False)
            if msg is None:
                return
            yield msg
    finally:
        # Dosya tutamaci acik kalirsa Windows'ta tlog silinemez/tasinamaz.
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
    s = [f"{'pencere':>8} {'n_v':>4} {'VibeZ maks':>10} {'n_p':>4} {'motor fark maks us':>18}  not   "
         f"(kanallar {','.join(map(str, kanallar))})"]
    for r in satirlar:
        f = lambda x, b: "-" if x is None else f"{x:{b}}"  # noqa: E731
        s.append(f"{_saat(r['t_bas_epoch'], ofset_saat):>8} {r['n_vibe']:>4} "
                  f"{f(r['vibez_maks'], '10.2f')} {r['n_pwm']:>4} {f(r['motor_fark_maks_us'], '18.0f')}  "
                  f"{'ESIK ASILDI' if r['esik_asildi'] else ''}")
    return "\n".join(s)


def hukum(satirlar, vibez_esik=VIBEZ_ESIK, motor_fark_esik_us=MOTOR_FARK_ESIK_US):
    """(tamam_mi, vibez_tepe, motor_fark_tepe) — dosya genelindeki tepe degerlere gore."""
    tum_vz = [r["vibez_maks"] for r in satirlar if r["vibez_maks"] is not None]
    tum_mf = [r["motor_fark_maks_us"] for r in satirlar if r["motor_fark_maks_us"] is not None]
    vz_tepe = max(tum_vz) if tum_vz else None
    mf_tepe = max(tum_mf) if tum_mf else None
    tamam = (vz_tepe is not None and vz_tepe <= vibez_esik) and \
            (mf_tepe is not None and mf_tepe <= motor_fark_esik_us)
    return tamam, vz_tepe, mf_tepe


def tek_dosya(yol, pencere_s, kanallar, ofset_saat, json_yol,
              vibez_esik=VIBEZ_ESIK, motor_fark_esik_us=MOTOR_FARK_ESIK_US):
    if not yol.is_file():
        print(f"OLCULEMEDI: dosya yok: {yol}", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    satirlar = pencereleri_hesapla(dosyadan_mesajlar(yol), pencere_s, kanallar,
                                    vibez_esik, motor_fark_esik_us)
    vibe_var = any(r["n_vibe"] for r in satirlar)
    pwm_var = any(r["n_pwm"] for r in satirlar)
    if not vibe_var and not pwm_var:
        print(f"OLCULEMEDI: {yol.name} icinde VIBE/VIBRATION ve PWM mesaji yok", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    if not vibe_var:
        print(f"OLCULEMEDI: {yol.name} icinde VIBE/VIBRATION mesaji yok "
              f"({'/'.join(VIBE_TIPLERI)}) — motor farki olculdu ama VibeZ olculemedi", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    if not pwm_var:
        print(f"OLCULEMEDI: {yol.name} icinde PWM mesaji yok ({'/'.join(PWM_TIPLERI)}, "
              f"kanallar {','.join(map(str, kanallar))}) — VibeZ olculdu ama motor farki olculemedi",
              file=sys.stderr)
        return CIKIS_OLCULEMEDI

    tamam, vz_tepe, mf_tepe = hukum(satirlar, vibez_esik, motor_fark_esik_us)
    print(f"HOVER KAPISI  {yol.name}  pencere {pencere_s:g} s  "
          f"(esik: VibeZ<={vibez_esik:g} m/s/s, motor farki<={motor_fark_esik_us:g} us)")
    print(tablo_metni(satirlar, ofset_saat, kanallar))
    print(f"TOPLAM: VibeZ tepe {vz_tepe:.2f} m/s/s · motor fark tepe {mf_tepe:.0f} us")
    if tamam:
        print("KAPI: TAMAM")
    else:
        neden = []
        if vz_tepe > vibez_esik:
            neden.append(f"VibeZ tepe {vz_tepe:.2f} > esik {vibez_esik:g}")
        if mf_tepe > motor_fark_esik_us:
            neden.append(f"motor fark tepe {mf_tepe:.0f} us > esik {motor_fark_esik_us:g} us")
        print(f"KAPI: BASARISIZ — {' · '.join(neden)} — UCULMAYACAK (takim karari 2026-09-17)")

    if json_yol:
        Path(json_yol).parent.mkdir(parents=True, exist_ok=True)
        Path(json_yol).write_text(json.dumps({
            "dosya": yol.name, "pencere_s": pencere_s, "kanallar": list(kanallar),
            "vibez_esik": vibez_esik, "motor_fark_esik_us": motor_fark_esik_us,
            "vibez_tepe": vz_tepe, "motor_fark_tepe_us": mf_tepe, "kapi_tamam": tamam,
            "pencereler": satirlar,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"JSON: {json_yol}")

    return CIKIS_TAMAM if tamam else CIKIS_BASARISIZ


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("dosyalar", nargs="+", help="DataFlash .bin ve/veya Mission Planner .tlog (birden fazla olabilir)")
    ap.add_argument("--pencere", type=float, default=VARSAYILAN_PENCERE_S,
                     help="egilim tablosu pencere suresi s (varsayilan %(default)s) — kapi hukmu tum dosyanin tepe degerine bakar, pencere yalniz teshis icindir")
    ap.add_argument("--kanallar", default=",".join(map(str, VARSAYILAN_KANALLAR)),
                     help="motor cikis kanallari (varsayilan AUX1-4 = %(default)s)")
    ap.add_argument("--vibez-esik", type=float, default=VIBEZ_ESIK,
                     help="KESIF/TESHIS icindir — asil kapi karari icin gevsetmeyin (varsayilan %(default)s m/s/s)")
    ap.add_argument("--motor-fark-esik-us", type=float, default=MOTOR_FARK_ESIK_US,
                     help="KESIF/TESHIS icindir — asil kapi karari icin gevsetmeyin (varsayilan %(default)s us)")
    ap.add_argument("--saat-ofseti", type=int, default=VARSAYILAN_SAAT_OFSETI,
                     help="tabloda yerel saat icin UTC ofseti (varsayilan %(default)s)")
    ap.add_argument("--json", default=None, metavar="DOSYA",
                     help="tek dosya verildiginde pencereleri+hukmu JSON yaz")
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

    if a.json and len(a.dosyalar) > 1:
        ap.error("--json yalniz tek dosyayla kullanilir")

    kodlar = []
    for i, d in enumerate(a.dosyalar):
        if i:
            print()
        kodlar.append(tek_dosya(Path(d), a.pencere, kanallar, a.saat_ofseti, a.json,
                                 a.vibez_esik, a.motor_fark_esik_us))
    if CIKIS_BASARISIZ in kodlar:
        return CIKIS_BASARISIZ
    if CIKIS_OLCULEMEDI in kodlar:
        return CIKIS_OLCULEMEDI
    return CIKIS_TAMAM


if __name__ == "__main__":
    sys.exit(main())
