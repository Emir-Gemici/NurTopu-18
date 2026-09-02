"""SiK 433 MHz RF OLCUM ARACI — ACK gidis-donusu (RTT) ve kayip.

NEDEN: D-388 seri hatti GERCEK bayt akisinda (TCP koprusu, `socket://`)
dogruladi; gercek 433 MHz RF olcumu Faz B'ye kaldi. Bu arac o olcumu yapar:
iki SiK telsiz, bir ucta `--rol yanki`, diger ucta `--rol olc`. Olcum
`comms/protocol.py`'nin GERCEK cerceveleriyle (CMD -> ACK) yapilir; yani
sahadaki IKA_GO / PARASUT tekrar dongusunun bire bir ayni yolu olculur.

NEDEN esik tekrar araliklaridir: `codes/karar_sozlesmesi.py` icindeki
`IKA_GO_TEKRAR_ARALIGI_S` (0,25 s) ve `PARASUT_TEKRAR_ARALIGI_S` (0,20 s)
"ACK gelmezse tekrar gonder" araliklaridir. RTT p95 bu araliklarin ALTINDA
degilse tekrar tasarimi anlamsizlasir: ACK yolda iken komut yeniden gider,
hat bogulur, ACK'ler gecikir (kendi kendini besleyen tikanma). Esikler
sozlesmeden IMPORT edilir (anayasa m.16), burada yeniden yazilmaz.

NEDEN `SerialLink.recv` ile ZAMANLAMA yapilmaz: pyserial `read(256)`, 256 bayt
gelene YA DA zaman asimi dolana kadar bloklar. ~70 baytlik bir ACK icin bu,
"ACK geldi" aninin okuma zaman asimina (0,3 s) YUVARLANMASI demektir — RTT
hep ~zaman asimi cikar, olcum yalan olur. Ayni sebeple YANKI tarafi da hizli
okumak zorundadir; yoksa cevabi 0,3 s geciktirir. Bu yuzden her iki rol
`_hizli_oku` kullanir: ilk bayta kadar bekle (`read(1)`), sonra birikeni
bosalt. Acma/gonderme/kapama yine `SerialLink` uzerindendir (uretim yolu).

VERDIKT (fail-closed):
  UYUMLU     (cikis 0) — RTT p95 < IKA_GO_TEKRAR_ARALIGI_S ve < PARASUT_TEKRAR_ARALIGI_S
  UYARI      (cikis 1) — p95 esiklerden en az birini asiyor
  OLCULEMEDI (cikis 2) — hic ACK yok (RTT ornegi yok) ya da port acilamadi;
                         "UYUMLU" DENEMEZ, sessiz basari yalani yok.
Kayip icin esik YOK (ilk olcum): yalniz raporlanir. RTT yuzdelikleri YALNIZ
ACK alinan problar uzerindendir; yuksek kayipta p95 iyimserdir — kayip
alanina birlikte bakilir.

Kullanim (iki telsiz, iki makine ya da iki port):
    venv\\Scripts\\python.exe -B scripts/sik_rf_olc.py --rol yanki --port COM7
    venv\\Scripts\\python.exe -B scripts/sik_rf_olc.py --rol olc --port COM8 \\
        --n 50 --aralik 0.25 --json --cikti results/faz_b/sik_rtt.json
Port `serial_for_url` uyumludur: `COM7`, `/dev/ttyUSB0`, `socket://h:p`,
`loop://` (loop:// ile olc rolu kendi CMD'sini gorur, ACK gelmez: kayip %100).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import threading
import time
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S)
from link import SerialLink  # noqa: E402
from protocol import FrameReader, ack, command, encode  # noqa: E402

# SiK varsayilan air-rate'inde yaygin seri hiz (`comms/link.py` varsayilaniyla
# ayni; sozlesmede baud sabiti YOK — D-388 / link.py dokstringi).
VARSAYILAN_BAUD = 57600
VARSAYILAN_N = 50
#: Prob kadansi varsayilani = IKA_GO tekrar kadansi (olculen sey o dongudur).
VARSAYILAN_ARALIK_S = IKA_GO_TEKRAR_ARALIGI_S
#: Yanki ucunun okuma zaman asimi: yalniz KeyboardInterrupt tepkisini belirler
#: (RTT'ye etkisi yok — ilk bayt gelince okuma hemen doner).
YANKI_OKUMA_ZAMAN_ASIMI_S = 0.3
#: Olc ucunun okuma zaman asimi tavani: prob son tarihine bu kadar kaba
#: yaklasilir (kayip probda en fazla bu kadar tasma). RTT'ye etkisi YOK;
#: test bunu kilitler (p50 bu degerin yarisinin altinda kalmali).
OLC_OKUMA_ZAMAN_ASIMI_S = 0.05
#: Tek `_hizli_oku` cagrisinda bosaltilacak en fazla bayt (sel korumasi).
OKUMA_TAVANI = 4096

PROB_KOMUTU = "RF_PROBE"       # protocol.command(cmd=...) — alicilar bilmedigini yok sayar
PROB_HEDEF = "ika"             # command(hedef=...) — yanki ucu IKA rolunu oynar
YANKI_DUGUMU = "ika"           # ack(node=...)
ACK_REF_TIPI = "CMD"           # ack(ref_tip=...) — CONTRACTS §6.6

CIKIS_UYUMLU, CIKIS_UYARI, CIKIS_OLCULEMEDI = 0, 1, 2
VERDIKT_UYUMLU = "tekrar tasarimiyla UYUMLU"
VERDIKT_UYARI = "UYARI: RTT p95 tekrar araligini asiyor"
VERDIKT_OLCULEMEDI = "OLCULEMEDI: hic ACK alinmadi (RTT ornegi yok)"


# ── Seri uc ──────────────────────────────────────────────────────────────────

def uc_ac(port, baud=VARSAYILAN_BAUD, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S):
    """Uretim tasiyicisi `SerialLink` ile ucu ac (serial_for_url uyumlu)."""
    return SerialLink(port, baud, timeout=timeout)


def _hizli_oku(link):
    """Ilk bayta kadar bekle (en fazla link zaman asimi), sonra birikeni bosalt.

    Donus: gelen baytlar (bos ise zaman asimi). Bir cerceve parcali gelebilir;
    cagiran `FrameReader` ile birlestirir — zamanlama cerceve TAMAMLANINCA alinir.
    """
    ser = link.ser
    ilk = ser.read(1)
    if not ilk:
        return b""
    parcalar = [ilk]
    toplam = 1
    while toplam < OKUMA_TAVANI:
        bekleyen = ser.in_waiting          # socket:// icin 0/1 doner; dongu yeter
        if bekleyen <= 0:
            break
        parca = ser.read(bekleyen)
        if not parca:
            break
        parcalar.append(parca)
        toplam += len(parca)
    return b"".join(parcalar)


def _seri_hatasi():
    import serial  # tembel: link.py de oyle yapar
    return serial.SerialException


# ── Rol: yanki ───────────────────────────────────────────────────────────────

def _prob_mu(mesaj):
    return (isinstance(mesaj, dict) and mesaj.get("type") == "CMD"
            and mesaj.get("cmd") == PROB_KOMUTU
            and isinstance(mesaj.get("seq"), int)
            and not isinstance(mesaj.get("seq"), bool))


def yanki_kos(link, dur=None, ilerleme=None):
    """Gelen her CMD(RF_PROBE) icin ack(seq, "ika", "CMD") yaz.

    `dur` (threading.Event) verilirse o kurulunca doner; verilmezse
    KeyboardInterrupt ya da hat kopana kadar surer. Cevaplanan sayiyi dondurur.
    """
    okuyucu = FrameReader()
    cevaplanan = 0
    hata = _seri_hatasi()
    while dur is None or not dur.is_set():
        try:
            veri = _hizli_oku(link)
        except (hata, OSError) as exc:
            if ilerleme:
                ilerleme(f"yanki: hat koptu ({exc})")
            break
        if not veri:
            continue
        for mesaj in okuyucu.feed(veri):
            if not _prob_mu(mesaj):
                continue                   # baska trafik: yok say
            link.send(encode(ack(mesaj["seq"], YANKI_DUGUMU, ref_tip=ACK_REF_TIPI)))
            cevaplanan += 1
            if ilerleme:
                ilerleme(f"yanki: seq={mesaj['seq']} -> ACK ({cevaplanan})")
    return cevaplanan


# ── Rol: olc ─────────────────────────────────────────────────────────────────

def _ack_eslesir(mesaj, seq):
    if not isinstance(mesaj, dict) or mesaj.get("type") != "ACK":
        return False
    if mesaj.get("ref") != seq:
        return False
    # ref_tip yoksa yalniz ref ile eslenir (geriye uyumlu, CONTRACTS §6.6)
    return mesaj.get("ref_tip", ACK_REF_TIPI) == ACK_REF_TIPI


def yuzdelik(degerler, p):
    """En yakin sira (nearest-rank) yuzdeligi; bos listede None."""
    if not degerler:
        return None
    sirali = sorted(degerler)
    k = max(1, min(len(sirali), math.ceil(p / 100.0 * len(sirali))))
    return sirali[k - 1]


def olc_kos(link, n, aralik, zaman_asimi=None, ilerleme=None,
            saat=time.monotonic):
    """n prob gonder, her biri icin ACK RTT olc; rapor sozlugu dondur.

    Prob i icin seq=i (1..n) — ACK `ref` ile eslenir. Zaman asimi icinde
    gelmeyen ACK KAYIP sayilir; sonradan gelen (bekleyen seq'e ait olmayan)
    ACK `gec_ack` sayacina yazilir, RTT'ye GIRMEZ.
    """
    n = int(n)
    aralik = float(aralik)
    if n < 1 or not (aralik > 0):
        raise ValueError("n >= 1 ve aralik > 0 olmali")
    zaman_asimi = 2.0 * aralik if zaman_asimi is None else float(zaman_asimi)
    if not (zaman_asimi > 0):
        raise ValueError("zaman asimi > 0 olmali")

    okuyucu = FrameReader()
    hata = _seri_hatasi()
    rtt_ms = []
    gonderilen = 0
    gec_ack = 0
    hat_koptu = None

    for seq in range(1, n + 1):
        cerceve = encode(command(PROB_KOMUTU, PROB_HEDEF, seq=seq))
        t0 = saat()
        try:
            link.send(cerceve)
        except (hata, OSError) as exc:
            hat_koptu = f"gonderim {seq}: {exc}"
            break
        gonderilen += 1
        son = t0 + zaman_asimi
        rtt = None
        while rtt is None and saat() < son:
            try:
                veri = _hizli_oku(link)
            except (hata, OSError) as exc:
                hat_koptu = f"okuma {seq}: {exc}"
                break
            for mesaj in okuyucu.feed(veri):
                if _ack_eslesir(mesaj, seq):
                    rtt = (saat() - t0) * 1000.0
                    break
                if isinstance(mesaj, dict) and mesaj.get("type") == "ACK":
                    gec_ack += 1
        if hat_koptu:
            break
        if rtt is None:
            if ilerleme:
                ilerleme(f"prob {seq}/{n}: KAYIP (> {zaman_asimi * 1000:.0f} ms)")
        else:
            rtt_ms.append(rtt)
            if ilerleme:
                ilerleme(f"prob {seq}/{n}: rtt={rtt:.1f} ms")
        kalan = (t0 + aralik) - saat()
        if kalan > 0 and seq < n:
            time.sleep(kalan)

    ack_alinan = len(rtt_ms)
    kayip = gonderilen - ack_alinan
    p50, p95 = yuzdelik(rtt_ms, 50), yuzdelik(rtt_ms, 95)
    esik_s = {"IKA_GO_TEKRAR_ARALIGI_S": IKA_GO_TEKRAR_ARALIGI_S,
              "PARASUT_TEKRAR_ARALIGI_S": PARASUT_TEKRAR_ARALIGI_S}

    if p95 is None:
        verdikt, cikis = VERDIKT_OLCULEMEDI, CIKIS_OLCULEMEDI
    elif p95 / 1000.0 < min(esik_s.values()):
        verdikt, cikis = VERDIKT_UYUMLU, CIKIS_UYUMLU
    else:
        verdikt, cikis = VERDIKT_UYARI, CIKIS_UYARI

    rapor = {
        "rol": "olc",
        "n": n, "aralik_s": aralik, "zaman_asimi_s": zaman_asimi,
        "gonderilen": gonderilen, "ack_alinan": ack_alinan,
        "kayip": kayip,
        "kayip_yuzde": (100.0 * kayip / gonderilen) if gonderilen else 100.0,
        "gec_ack": gec_ack,
        "rtt_ms": {
            "ornek": ack_alinan,
            "p50": p50, "p95": p95,
            "min": (min(rtt_ms) if rtt_ms else None),
            "maks": (max(rtt_ms) if rtt_ms else None),
        },
        "esik_s": esik_s,
        "verdikt": verdikt,
        "cikis_kodu": cikis,
        "not": ("RTT yuzdelikleri yalniz ACK alinan problar uzerindendir; "
                "kayip icin esik yok, birlikte okunur."),
    }
    if hat_koptu:
        rapor["hat_koptu"] = hat_koptu
        # Hat koparsa olcum tamamlanmamistir: UYUMLU denemez.
        if rapor["cikis_kodu"] == CIKIS_UYUMLU:
            rapor["verdikt"] = "OLCULEMEDI: hat koptu — " + hat_koptu
            rapor["cikis_kodu"] = CIKIS_OLCULEMEDI
    return rapor


def _ms(deger):
    return "-" if deger is None else f"{deger:.1f} ms"


def rapor_metni(rapor):
    r = rapor["rtt_ms"]
    satirlar = [
        f"gonderilen : {rapor['gonderilen']}",
        f"ACK alinan : {rapor['ack_alinan']}",
        f"kayip      : {rapor['kayip']} (%{rapor['kayip_yuzde']:.1f})"
        + (f"  gec ACK: {rapor['gec_ack']}" if rapor["gec_ack"] else ""),
        f"RTT p50    : {_ms(r['p50'])}",
        f"RTT p95    : {_ms(r['p95'])}",
        f"RTT maks   : {_ms(r['maks'])}",
        "esik       : p95 < IKA_GO_TEKRAR_ARALIGI_S="
        f"{rapor['esik_s']['IKA_GO_TEKRAR_ARALIGI_S'] * 1000:.0f} ms ve "
        f"< PARASUT_TEKRAR_ARALIGI_S="
        f"{rapor['esik_s']['PARASUT_TEKRAR_ARALIGI_S'] * 1000:.0f} ms",
        f"VERDIKT    : {rapor['verdikt']}",
    ]
    if rapor.get("hat_koptu"):
        satirlar.append(f"HAT KOPTU  : {rapor['hat_koptu']}")
    return "\n".join(satirlar)


# ── CLI ──────────────────────────────────────────────────────────────────────

def _ilerleme_yaz(satir):
    print(satir, file=sys.stderr, flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rol", choices=("yanki", "olc"), required=True)
    ap.add_argument("--port", required=True,
                    help="serial_for_url uyumlu: COM7, /dev/ttyUSB0, socket://, loop://")
    ap.add_argument("--baud", type=int, default=VARSAYILAN_BAUD)
    ap.add_argument("--n", type=int, default=VARSAYILAN_N, help="prob sayisi (olc)")
    ap.add_argument("--aralik", type=float, default=VARSAYILAN_ARALIK_S,
                    help="prob araligi s (olc); varsayilan IKA_GO tekrar araligi")
    ap.add_argument("--zaman-asimi", type=float, default=None,
                    help="ACK bekleme s (olc); varsayilan 2*aralik")
    ap.add_argument("--json", action="store_true", help="raporu JSON bas")
    ap.add_argument("--cikti", default=None, help="raporu bu JSON dosyasina da yaz")
    ap.add_argument("--sessiz", action="store_true", help="prob ilerlemesini basma")
    a = ap.parse_args(argv)

    ilerleme = None if a.sessiz else _ilerleme_yaz
    try:
        hata = _seri_hatasi()
    except ImportError:
        print("OLCULEMEDI: pyserial kurulu degil (venv: pip install pyserial)",
              file=sys.stderr)
        return CIKIS_OLCULEMEDI

    if a.rol == "olc":
        if a.n < 1 or not (a.aralik > 0) or (a.zaman_asimi is not None
                                             and not (a.zaman_asimi > 0)):
            ap.error("--n >= 1, --aralik > 0, --zaman-asimi > 0 olmali")
        try:
            link = uc_ac(a.port, a.baud, timeout=min(
                a.zaman_asimi if a.zaman_asimi else 2.0 * a.aralik,
                OLC_OKUMA_ZAMAN_ASIMI_S))
        except (hata, OSError, ValueError) as exc:
            print(f"OLCULEMEDI: port acilamadi ({a.port}): {exc}", file=sys.stderr)
            return CIKIS_OLCULEMEDI
        try:
            rapor = olc_kos(link, a.n, a.aralik, a.zaman_asimi, ilerleme=ilerleme)
        finally:
            link.close()
        rapor["port"], rapor["baud"] = a.port, a.baud
        if a.cikti:
            yol = Path(a.cikti)
            yol.parent.mkdir(parents=True, exist_ok=True)
            yol.write_text(json.dumps(rapor, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        if a.json:
            print(json.dumps(rapor, ensure_ascii=False))
        else:
            print(rapor_metni(rapor))
        return rapor["cikis_kodu"]

    # rol == yanki
    try:
        link = uc_ac(a.port, a.baud, timeout=YANKI_OKUMA_ZAMAN_ASIMI_S)
    except (hata, OSError, ValueError) as exc:
        print(f"yanki: port acilamadi ({a.port}): {exc}", file=sys.stderr)
        return CIKIS_OLCULEMEDI
    _ilerleme_yaz(f"yanki: {a.port} @ {a.baud} — CMD({PROB_KOMUTU}) bekleniyor "
                  "(Ctrl+C ile cik)")
    cevaplanan = 0
    try:
        cevaplanan = yanki_kos(link, ilerleme=ilerleme)
    except KeyboardInterrupt:
        pass
    finally:
        link.close()
    sonuc = {"rol": "yanki", "port": a.port, "baud": a.baud,
             "cevaplanan": cevaplanan}
    print(json.dumps(sonuc, ensure_ascii=False) if a.json
          else f"yanki: cevaplanan prob = {cevaplanan}")
    return CIKIS_UYUMLU


if __name__ == "__main__":
    sys.exit(main())
