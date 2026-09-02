"""FAZ B — PIXHAWK ON-UCUS DOGRULAYICISI: "Pixhawk konusuyor mu?" MEKANIK verdikt.

NEDEN: Faz B'de (5 Eylul) gercek Pixhawk ilk kez baglanacak. Uretim
(`comms/inis_kaniti.BagilIrtifaOkuyucu` ve `yerde_mi`) iki MAVLink akisina
bagli: GLOBAL_POSITION_INT (relative_alt/lat/lon) ve EXTENDED_SYS_STATE
(landed_state). ArduPilot EXTENDED_SYS_STATE'i VARSAYILAN akitmaz; istenmesi
gerekir. Goz karariyla "veri geliyor" demek yeterli degildir: irtifa penceresi
TELEMETRI_IRTIFA_TAZELIK_S (0,5 s) icinde dolu kalmazsa rota OLCEK_YOK'a
duser, EXTENDED_SYS_STATE gelmezse inis kaniti hic olusmaz.

Bu arac uc soruyu OLCUMLE cevaplar (esikler codes/karar_sozlesmesi.py'den):
  1) Pixhawk konusuyor mu, beklenen sysid mi?     HEARTBEAT (tavan 15 s)
  2) Akislar istenebiliyor mu?                    MAV_CMD_SET_MESSAGE_INTERVAL
                                                  (ACK gelmezse "en iyi caba",
                                                  DUSURMEZ — hakem olcumdur)
  3) Akislar sozlesmedeki asgari hizda mi?        MAVLINK_*_ASGARI_HZ

Verdikt FAIL-CLOSED: beklenen sysid'den HEARTBEAT gelmezse, herhangi bir akis
esigin altindaysa ya da baglanti hata verirse DUSTU (exit 1). Yalniz beklenen
sysid'den gelen mesajlar sayilir; yabanci kaynaklar ayrica raporlanir.

Kullanim:
  mavlink_dogrula.py --mavlink udpin:0.0.0.0:14550 --sysid 1
  mavlink_dogrula.py --mavlink COM5 --sysid 1 --sure 10 --json rapor.json
  Prova (gercek Pixhawk olmadan):
    sahte_pixhawk.py --adres udpout:127.0.0.1:14550   (ayri terminalde)
    mavlink_dogrula.py --mavlink udpin:127.0.0.1:14550 --sysid 1

⚠ SahtePixhawk SET_MESSAGE_INTERVAL'a cevap vermez; ACK yoklugu bu yuzden
tek basina dusurme nedeni DEGILDIR. Gercek ArduPilot'ta ACK beklenir ve
raporlanir, ama verdikt yine olculen hiza baglidir.
"""
import argparse
import json
import math
import sys
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "codes") not in sys.path:
    sys.path.insert(0, str(KOK / "codes"))

from pymavlink import mavutil  # noqa: E402

from karar_sozlesmesi import (MAVLINK_DOGRULAMA_SURESI_S,  # noqa: E402
                              MAVLINK_DURUM_ASGARI_HZ,
                              MAVLINK_HEARTBEAT_ASGARI_HZ,
                              MAVLINK_KONUM_ASGARI_HZ)

# --- arac parametreleri (sozlesme degil, olcum aracinin kendi ayarlari) ---
# ArduPilot SYSID_THISMAV varsayilani 1'dir; sahte_pixhawk.VARSAYILAN_SYSID
# ile ayni. Sahada farkliysa --sysid ile beyan edilir (yabanci kaynak
# sessizce otorite olamaz — inis_kaniti ile ayni ilke).
VARSAYILAN_BEKLENEN_SYSID = 1
HEARTBEAT_TAVAN_S = 15.0     # ilk HEARTBEAT icin bekleme tavani
ACK_TAVAN_S = 1.0            # COMMAND_ACK icin bekleme (en iyi caba)
DINLEME_ADIMI_S = 0.2        # tek recv_match blok suresi (kalan sureyi asmaz)
BIRIKINTI_BOSALTMA_S = 0.2   # olcum penceresi oncesi soket birikintisi tavani
# Istenen hiz = asgari x 2 -> aralik = 1e6 / asgari_hz * 0,5 us. Asgarinin
# tam kendisini istemek jitter'da esigin hemen altina dusurur.
ISTEK_HIZ_CARPANI = 2.0
MIKROSANIYE = 1e6

MESAJ_HEARTBEAT = "HEARTBEAT"
MESAJ_KONUM = "GLOBAL_POSITION_INT"
MESAJ_DURUM = "EXTENDED_SYS_STATE"
MESAJ_COMMAND_ACK = "COMMAND_ACK"


def akis_tanimlari():
    """Olculecek akislar: ad, MAVLink mesaj id'si, asgari Hz, istensin mi.

    Mesaj id'leri pymavlink sabitlerinden okunur (madde 16: ciplak sayi yok).
    HEARTBEAT istenmez (ArduPilot zaten 1 Hz basar; standart).
    """
    m = mavutil.mavlink
    return [
        {"ad": MESAJ_HEARTBEAT, "id": m.MAVLINK_MSG_ID_HEARTBEAT,
         "asgari_hz": MAVLINK_HEARTBEAT_ASGARI_HZ, "istenir": False},
        {"ad": MESAJ_KONUM, "id": m.MAVLINK_MSG_ID_GLOBAL_POSITION_INT,
         "asgari_hz": MAVLINK_KONUM_ASGARI_HZ, "istenir": True},
        {"ad": MESAJ_DURUM, "id": m.MAVLINK_MSG_ID_EXTENDED_SYS_STATE,
         "asgari_hz": MAVLINK_DURUM_ASGARI_HZ, "istenir": True},
    ]


def _enum_adi(enum_adi, deger):
    """MAVLink enum degerinin adini dondur; bilinmiyorsa None (uydurma yok)."""
    try:
        return mavutil.mavlink.enums[enum_adi][int(deger)].name
    except Exception:
        return None


def _hata_metni(exc):
    return f"{type(exc).__name__}: {exc}"


def _kaynak(mesaj):
    """(sysid, compid) ya da None — pymavlink disi nesnelere karsi savunma."""
    try:
        return int(mesaj.get_srcSystem()), int(mesaj.get_srcComponent())
    except Exception:
        return None


# ---------------------------------------------------------------- 1) HEARTBEAT

def heartbeat_bekle(mav, beklenen_sysid, tavan_s):
    """Beklenen sysid'den ilk HEARTBEAT'i bekle; gorulen tum kaynaklari kaydet.

    Yalniz ilk gelen paketi beklenenle karsilastirmak yerine tavan boyunca
    beklenen kaynak aranir: ayni hatta bir YKS heartbeat'i (sysid 255) ya da
    yabanci arac gorulmesi tek basina dusurmez, ama beklenen sysid tavan
    icinde hic konusmadiysa DUSTU ve gorulen kaynaklar raporlanir.
    """
    gorulen = []
    sonuc = {
        "alindi": False, "beklenen_sysid": beklenen_sysid,
        "sysid": None, "compid": None,
        "autopilot": None, "autopilot_ad": None,
        "type": None, "type_ad": None,
        "bekleme_s": None, "tavan_s": tavan_s,
        "gorulen_kaynaklar": gorulen, "hata": None,
    }
    baslangic = time.monotonic()
    bitis = baslangic + tavan_s
    while True:
        kalan = bitis - time.monotonic()
        if kalan <= 0.0:
            break
        try:
            mesaj = mav.recv_match(type=MESAJ_HEARTBEAT, blocking=True,
                                   timeout=min(kalan, DINLEME_ADIMI_S))
        except Exception as exc:
            sonuc["hata"] = _hata_metni(exc)
            break
        if mesaj is None:
            continue
        kaynak = _kaynak(mesaj)
        if kaynak is None:
            continue
        sysid, compid = kaynak
        if [sysid, compid] not in gorulen:
            gorulen.append([sysid, compid])
        if sysid != beklenen_sysid:
            continue
        try:
            autopilot = int(mesaj.autopilot)
            tip = int(mesaj.type)
        except Exception as exc:
            sonuc["hata"] = f"HEARTBEAT alanlari okunamadi ({_hata_metni(exc)})"
            break
        sonuc.update({
            "alindi": True, "sysid": sysid, "compid": compid,
            "autopilot": autopilot,
            "autopilot_ad": _enum_adi("MAV_AUTOPILOT", autopilot),
            "type": tip, "type_ad": _enum_adi("MAV_TYPE", tip),
            "bekleme_s": round(time.monotonic() - baslangic, 3),
        })
        break
    return sonuc


# ------------------------------------------------------ 2) AKIS ISTEGI (best-effort)

def akislari_iste(mav, hedef_sysid, hedef_compid, akislar, ack_tavan_s):
    """MAV_CMD_SET_MESSAGE_INTERVAL ile akislari iste; ACK'leri topla.

    EN IYI CABA: gonderim hatasi ya da ACK yoklugu DUSURMEZ — akis olcumle
    yargilanir. COMMAND_ACK hangi mesaj id'si icin oldugunu tasimaz;
    ArduPilot komutlari sirayla isledigi icin ACK'ler gonderim sirasina
    eslenir (raporda belirtilir).
    """
    m = mavutil.mavlink
    istekler = []
    for akis in akislar:
        if not akis["istenir"]:
            continue
        istenen_hz = float(akis["asgari_hz"]) * ISTEK_HIZ_CARPANI
        aralik_us = int(round(MIKROSANIYE / istenen_hz))
        kayit = {
            "mesaj": akis["ad"], "mesaj_id": int(akis["id"]),
            "istenen_hz": istenen_hz, "aralik_us": aralik_us,
            "gonderildi": False, "ack": None, "ack_ad": None, "not": None,
        }
        try:
            mav.mav.command_long_send(
                hedef_sysid, hedef_compid,
                m.MAV_CMD_SET_MESSAGE_INTERVAL, 0,
                float(akis["id"]), float(aralik_us),
                0.0, 0.0, 0.0, 0.0, 0.0)
            kayit["gonderildi"] = True
        except Exception as exc:
            kayit["not"] = (f"istek gonderilemedi ({_hata_metni(exc)}); "
                            "en iyi caba — akis olcumle yargilanir")
        istekler.append(kayit)

    bekleyen = [k for k in istekler if k["gonderildi"]]
    bitis = time.monotonic() + ack_tavan_s
    while bekleyen:
        kalan = bitis - time.monotonic()
        if kalan <= 0.0:
            break
        try:
            mesaj = mav.recv_match(type=MESAJ_COMMAND_ACK, blocking=True,
                                   timeout=min(kalan, DINLEME_ADIMI_S))
        except Exception as exc:
            for k in bekleyen:
                k["not"] = (f"ACK beklenirken hata ({_hata_metni(exc)}); "
                            "en iyi caba")
            bekleyen = []
            break
        if mesaj is None:
            continue
        kaynak = _kaynak(mesaj)
        if kaynak is None or kaynak[0] != hedef_sysid:
            continue
        try:
            komut = int(mesaj.command)
            sonuc = int(mesaj.result)
        except Exception:
            continue
        if komut != m.MAV_CMD_SET_MESSAGE_INTERVAL:
            continue
        k = bekleyen.pop(0)
        k["ack"] = sonuc
        k["ack_ad"] = _enum_adi("MAV_RESULT", sonuc)
        if sonuc != m.MAV_RESULT_ACCEPTED:
            k["not"] = "ACK kabul degil; akis olcumle yargilanir"
    for k in bekleyen:
        if k["not"] is None:
            k["not"] = (f"ACK gelmedi ({ack_tavan_s:g} s); en iyi caba — "
                        "akis olcumle yargilanir")
    return istekler


# --------------------------------------------------------------- 3) HIZ OLCUMU

def _birikintiyi_bosalt(mav):
    """Onceki asamalarda sokette biriken paketleri at: pencere temiz baslasin.

    Zaman tavanli: hizli bir kaynakta sonsuz dongu olmaz.
    """
    bitis = time.monotonic() + BIRIKINTI_BOSALTMA_S
    while time.monotonic() < bitis:
        if mav.recv_match(blocking=False) is None:
            return


def hizlari_olc(mav, beklenen_sysid, akislar, sure_s):
    """`sure_s` boyunca her akisin Hz'ini olc (yalniz beklenen sysid'den).

    Hz = sayi / gercek pencere suresi. Zaman damgasi farkindan (ilk-son)
    hesaplanmaz: patlamali (burst) akislar o yontemde sahte yuksek Hz verir.
    Baglanti hatasi fail-closed: tum akislar DUSTU sayilir.
    """
    tipler = [a["ad"] for a in akislar]
    sayim = {ad: 0 for ad in tipler}
    yabanci = {ad: 0 for ad in tipler}
    hata = None
    try:
        _birikintiyi_bosalt(mav)
    except Exception as exc:
        hata = f"birikinti bosaltilamadi ({_hata_metni(exc)})"

    baslangic = time.monotonic()
    bitis = baslangic + sure_s
    while hata is None:
        kalan = bitis - time.monotonic()
        if kalan <= 0.0:
            break
        try:
            mesaj = mav.recv_match(type=tipler, blocking=True,
                                   timeout=min(kalan, DINLEME_ADIMI_S))
        except Exception as exc:
            hata = f"olcum sirasinda baglanti hatasi ({_hata_metni(exc)})"
            break
        if mesaj is None:
            continue
        try:
            tip = mesaj.get_type()
        except Exception:
            continue
        if tip not in sayim:
            continue
        kaynak = _kaynak(mesaj)
        if kaynak is not None and kaynak[0] == beklenen_sysid:
            sayim[tip] += 1
        else:
            yabanci[tip] += 1
    gercek_sure = time.monotonic() - baslangic

    satirlar = []
    for akis in akislar:
        ad = akis["ad"]
        hz = (sayim[ad] / gercek_sure) if gercek_sure > 0.0 else 0.0
        esik = float(akis["asgari_hz"])
        satirlar.append({
            "mesaj": ad, "mesaj_id": int(akis["id"]),
            "sayi": sayim[ad], "hz": round(hz, 3), "esik_hz": esik,
            "gecti": bool(hata is None and math.isfinite(hz) and hz >= esik),
        })
    olcum = {
        "sure_s": float(sure_s), "gercek_sure_s": round(gercek_sure, 3),
        "hata": hata, "yabanci_kaynak_mesaj": yabanci,
    }
    return satirlar, olcum


# ------------------------------------------------------------------- VERDIKT

def _nedenler(rapor):
    nedenler = []
    hb = rapor["heartbeat"]
    if hb["hata"]:
        nedenler.append(f"HEARTBEAT beklenirken hata: {hb['hata']}")
    if not hb["alindi"]:
        gorulen = ", ".join(f"sysid {s}/comp {c}"
                            for s, c in hb["gorulen_kaynaklar"]) or "hicbiri"
        if hb["gorulen_kaynaklar"]:
            nedenler.append(
                f"sysid uyusmazligi: beklenen {hb['beklenen_sysid']} "
                f"{hb['tavan_s']:g} s icinde konusmadi; gorulen: {gorulen}")
        else:
            nedenler.append(
                f"HEARTBEAT zaman asimi: {hb['tavan_s']:g} s icinde hicbir "
                "kaynak konusmadi")
    olcum = rapor.get("olcum")
    if olcum and olcum.get("hata"):
        nedenler.append(olcum["hata"])
    for akis in rapor.get("akislar", []):
        if not akis["gecti"]:
            nedenler.append(
                f"{akis['mesaj']}: {akis['hz']:.2f} Hz < esik "
                f"{akis['esik_hz']:g} Hz ({akis['sayi']} mesaj)")
    return nedenler


def dogrula_baglanti(mav, adres, beklenen_sysid, sure_s,
                     heartbeat_tavan_s=HEARTBEAT_TAVAN_S,
                     ack_tavan_s=ACK_TAVAN_S):
    """Acik bir pymavlink baglantisinda tam dogrulamayi kos; rapor dict doner."""
    akislar = akis_tanimlari()
    rapor = {
        "arac": "mavlink_dogrula", "mavlink": adres,
        "beklenen_sysid": beklenen_sysid,
        "esikler": {
            "konum_asgari_hz": MAVLINK_KONUM_ASGARI_HZ,
            "durum_asgari_hz": MAVLINK_DURUM_ASGARI_HZ,
            "heartbeat_asgari_hz": MAVLINK_HEARTBEAT_ASGARI_HZ,
            "dogrulama_suresi_s": MAVLINK_DOGRULAMA_SURESI_S,
        },
        "heartbeat": None, "istekler": [], "akislar": [], "olcum": None,
        "gecti": False, "dusme_nedenleri": [],
    }
    rapor["heartbeat"] = heartbeat_bekle(mav, beklenen_sysid, heartbeat_tavan_s)
    if rapor["heartbeat"]["alindi"]:
        rapor["istekler"] = akislari_iste(
            mav, rapor["heartbeat"]["sysid"], rapor["heartbeat"]["compid"],
            akislar, ack_tavan_s)
        rapor["akislar"], rapor["olcum"] = hizlari_olc(
            mav, beklenen_sysid, akislar, sure_s)
    rapor["dusme_nedenleri"] = _nedenler(rapor)
    rapor["gecti"] = (not rapor["dusme_nedenleri"]
                      and rapor["heartbeat"]["alindi"]
                      and bool(rapor["akislar"])
                      and all(a["gecti"] for a in rapor["akislar"]))
    return rapor


def dogrula(adres, beklenen_sysid=VARSAYILAN_BEKLENEN_SYSID,
            sure_s=MAVLINK_DOGRULAMA_SURESI_S,
            heartbeat_tavan_s=HEARTBEAT_TAVAN_S, ack_tavan_s=ACK_TAVAN_S):
    """Baglantiyi ac, dogrula, kapat. Acilamazsa fail-closed DUSTU raporu."""
    try:
        mav = mavutil.mavlink_connection(adres)
    except Exception as exc:
        return {
            "arac": "mavlink_dogrula", "mavlink": adres,
            "beklenen_sysid": beklenen_sysid, "heartbeat": {
                "alindi": False, "beklenen_sysid": beklenen_sysid,
                "gorulen_kaynaklar": [], "tavan_s": heartbeat_tavan_s,
                "hata": f"baglanti acilamadi ({_hata_metni(exc)})"},
            "istekler": [], "akislar": [], "olcum": None, "gecti": False,
            "dusme_nedenleri": [f"baglanti acilamadi: {_hata_metni(exc)}"],
        }
    try:
        return dogrula_baglanti(mav, adres, beklenen_sysid, sure_s,
                                heartbeat_tavan_s, ack_tavan_s)
    finally:
        try:
            mav.close()
        except Exception:
            pass


# --------------------------------------------------------------------- CIKTI

def tablo_metni(rapor):
    s = []
    s.append(f"PIXHAWK ON-UCUS DOGRULAMASI  ({rapor['mavlink']}, "
             f"beklenen sysid {rapor['beklenen_sysid']})")
    hb = rapor["heartbeat"]
    if hb.get("alindi"):
        s.append(f"HEARTBEAT: sysid={hb['sysid']} compid={hb['compid']} "
                 f"autopilot={hb['autopilot']} ({hb['autopilot_ad']}) "
                 f"type={hb['type']} ({hb['type_ad']})  "
                 f"bekleme={hb['bekleme_s']:.2f} s")
    else:
        gorulen = ", ".join(f"{a}/{b}" for a, b in hb.get("gorulen_kaynaklar", []))
        s.append(f"HEARTBEAT: beklenen sysid'den ALINAMADI "
                 f"(gorulen sysid/comp: {gorulen or 'hicbiri'})")
    for k in rapor["istekler"]:
        ack = (f"ACK {k['ack']} ({k['ack_ad']})" if k["ack"] is not None
               else "ACK yok")
        notu = f" — {k['not']}" if k["not"] else ""
        s.append(f"ISTEK: {k['mesaj']:<20} @{k['istenen_hz']:.1f} Hz "
                 f"({k['aralik_us']} us) -> {ack}{notu}")
    olcum = rapor.get("olcum")
    if olcum:
        s.append(f"OLCUM: {olcum['gercek_sure_s']:.2f} s "
                 f"(istenen {olcum['sure_s']:g} s), yalniz sysid "
                 f"{rapor['beklenen_sysid']}; yabanci kaynak mesaj: "
                 f"{sum(olcum['yabanci_kaynak_mesaj'].values())}")
        s.append(f"  {'akis':<20} {'sayi':>5} {'olculen Hz':>11} "
                 f"{'esik Hz':>8}   sonuc")
        for a in rapor["akislar"]:
            s.append(f"  {a['mesaj']:<20} {a['sayi']:>5} {a['hz']:>11.2f} "
                     f"{a['esik_hz']:>8.2f}   "
                     f"{'GECTI' if a['gecti'] else 'DUSTU'}")
    for n in rapor["dusme_nedenleri"]:
        s.append(f"NEDEN: {n}")
    s.append(f"VERDIKT: {'GECTI' if rapor['gecti'] else 'DUSTU'}")
    return "\n".join(s)


def _pozitif_sonlu(deger, ad, parser):
    try:
        d = float(deger)
    except (TypeError, ValueError):
        parser.error(f"{ad} sayi olmali")
    if not math.isfinite(d) or d <= 0.0:
        parser.error(f"{ad} pozitif ve sonlu olmali")
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--mavlink", required=True,
                    help="pymavlink baglanti dizesi (udpin:..., COM5, "
                         "/dev/ttyACM0, tcp:...)")
    ap.add_argument("--sysid", type=int, default=VARSAYILAN_BEKLENEN_SYSID,
                    help="beklenen Pixhawk sysid (varsayilan %(default)s)")
    ap.add_argument("--sure", type=float, default=MAVLINK_DOGRULAMA_SURESI_S,
                    help="olcum penceresi s (varsayilan sozlesme: %(default)s)")
    ap.add_argument("--heartbeat-tavan", type=float, default=HEARTBEAT_TAVAN_S,
                    help="ilk HEARTBEAT bekleme tavani s (varsayilan "
                         "%(default)s)")
    ap.add_argument("--ack-tavan", type=float, default=ACK_TAVAN_S,
                    help="SET_MESSAGE_INTERVAL ACK bekleme s (en iyi caba; "
                         "varsayilan %(default)s)")
    ap.add_argument("--json", default=None, metavar="DOSYA",
                    help="JSON raporu bu dosyaya yaz ('-' = stdout; tablo o "
                         "zaman stderr'e gider)")
    args = ap.parse_args(argv)

    if not 1 <= args.sysid <= 255:
        ap.error("--sysid 1..255 tamsayi olmali")
    sure = _pozitif_sonlu(args.sure, "--sure", ap)
    hb_tavan = _pozitif_sonlu(args.heartbeat_tavan, "--heartbeat-tavan", ap)
    ack_tavan = _pozitif_sonlu(args.ack_tavan, "--ack-tavan", ap)

    rapor = dogrula(args.mavlink, args.sysid, sure, hb_tavan, ack_tavan)
    tablo = tablo_metni(rapor)
    json_metni = json.dumps(rapor, ensure_ascii=False, indent=2)
    if args.json == "-":
        print(tablo, file=sys.stderr)
        print(json_metni)
    else:
        print(tablo)
        if args.json:
            Path(args.json).write_text(json_metni + "\n", encoding="utf-8")
            print(f"JSON: {args.json}")
    sys.stdout.flush()
    return 0 if rapor["gecti"] else 1


if __name__ == "__main__":
    sys.exit(main())
