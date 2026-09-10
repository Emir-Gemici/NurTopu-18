"""H2 (ON_KAYIT §1) — HABERLESME OLCUMU: yazilimla olculebilen duzenekler.

Iki duzenek, iki kadans; hepsi `scripts/sik_rf_olc.py`nin GERCEK CLI'siyla
(ayri surec, `--cikti` JSON'u aracin kendisi yazar):

  udp_loopback      : yanki `UdpUc` (127.0.0.1, ephemeral) bu surecte thread,
                      olc ayri surec `--tasiyici udp --peer 127.0.0.1:<port>`
  tcp_seri_koprusu  : `tests/test_p2_seri_hat.SikKoprusu` (iki GERCEK pyserial
                      `socket://` ucu, D-388 kalibi) bu surecte; yanki thread,
                      olc ayri surec `--port socket://127.0.0.1:<port>`

Kadanslar sozlesmeden okunur: IKA_GO_TEKRAR_ARALIGI_S (0,25 s) ve
PARASUT_TEKRAR_ARALIGI_S (0,20 s). n = 200 prob (~50 s / kosum).

⚠ GERCEK RF YOKTUR. Bu dosyanin urettigi sayilar 433 MHz SiK hattinin
sayilari DEGILDIR; RF satirlari FDR'de OLCULEMEDI kalir. Ekip radyolari
taktiginda ayni arac `--port COMx` ile kosulur (ON_KAYIT H6 kagidi).

Kullanim (depo kokunden):
    venv\\Scripts\\python.exe -B results/fdr_sprint_20260910/H2/olcum_kos.py
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parents[2]
for _y in (KOK / "scripts", KOK / "tests", KOK / "comms", KOK / "codes"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import sik_rf_olc  # noqa: E402
from karar_sozlesmesi import (IKA_GO_TEKRAR_ARALIGI_S,  # noqa: E402
                              PARASUT_TEKRAR_ARALIGI_S)
from test_p2_seri_hat import SikKoprusu  # noqa: E402

N_PROB = 200
ZAMAN_ASIMI_S = 0.5          # 2 * 0,25 (varsayilan kural ile ayni; kadanslar arasi sabit)
KADANSLAR = {"ikago": IKA_GO_TEKRAR_ARALIGI_S, "parasut": PARASUT_TEKRAR_ARALIGI_S}
ARAC = KOK / "scripts" / "sik_rf_olc.py"


def _olc_surec(argv, cikti):
    komut = [sys.executable, "-B", str(ARAC), "--rol", "olc", "--json", "--sessiz",
             "--n", str(N_PROB), "--zaman-asimi", str(ZAMAN_ASIMI_S),
             "--cikti", str(cikti)] + argv
    t0 = time.monotonic()
    s = subprocess.run(komut, cwd=KOK, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=600)
    sure = time.monotonic() - t0
    if s.returncode not in (0, 1):
        raise RuntimeError(f"olc surec cikis {s.returncode}: {s.stderr[-500:]}")
    return {"komut": " ".join(komut[1:]), "cikis": s.returncode,
            "duvar_saati_s": round(sure, 2)}


def _yanki_thread(uc):
    dur = threading.Event()
    sayac = {}
    sonuc = {}

    def calis():
        sonuc["cevaplanan"] = sik_rf_olc.yanki_kos(uc, dur=dur, sayac=sayac)

    t = threading.Thread(target=calis, daemon=True)
    t.start()

    def bitir():
        dur.set()
        t.join(timeout=3.0)
        uc.close()
        return {"cevaplanan": sonuc.get("cevaplanan"), "veri_hizi": sayac}

    return bitir


def udp_loopback(kadans_adi, aralik):
    uc = sik_rf_olc.udp_uc_ac("127.0.0.1:0", timeout=0.1)
    bitir = _yanki_thread(uc)
    cikti = BURASI / f"olcum_udp_loopback_{kadans_adi}.json"
    meta = _olc_surec(["--tasiyici", "udp", "--peer", f"127.0.0.1:{uc.port}",
                       "--aralik", str(aralik)], cikti)
    meta["yanki"] = bitir()
    return cikti, meta


def tcp_seri_koprusu(kadans_adi, aralik):
    kopru = SikKoprusu()
    try:
        uc = sik_rf_olc.uc_ac(f"socket://127.0.0.1:{kopru.port}",
                              sik_rf_olc.VARSAYILAN_BAUD, timeout=0.1)
        bitir = _yanki_thread(uc)
        cikti = BURASI / f"olcum_tcp_seri_koprusu_{kadans_adi}.json"
        meta = _olc_surec(["--port", f"socket://127.0.0.1:{kopru.port}",
                           "--aralik", str(aralik)], cikti)
        meta["yanki"] = bitir()
    finally:
        kopru.kapat()
    return cikti, meta


def _ozet_satiri(ad, rapor):
    r, v = rapor["rtt_ms"], rapor["veri_hizi"]
    return (f"{ad:32s} ACK {rapor['ack_alinan']}/{rapor['gonderilen']} kayip %{rapor['kayip_yuzde']:.1f} "
            f"RTT p50 {r['p50']:.2f} p95 {r['p95']:.2f} maks {r['maks']:.2f} ms | "
            f"TX {v['gonderilen_bayt_s']:.1f} B/s {v['gonderilen_paket_s']:.2f} pkt/s · "
            f"RX {v['alinan_bayt_s']:.1f} B/s {v['alinan_paket_s']:.2f} pkt/s · "
            f"sure {v['sure_s']:.1f} s · {rapor['verdikt']}")


def main():
    import serial
    ozet = {
        "tarih": datetime.now().isoformat(timespec="seconds"),
        "makine": platform.platform(),
        "python": sys.version.split()[0],
        "pyserial": serial.__version__,
        "arac": "scripts/sik_rf_olc.py",
        "n_prob": N_PROB, "zaman_asimi_s": ZAMAN_ASIMI_S,
        "kadans_s": KADANSLAR,
        "uyari": ("GERCEK RF YOK: udp_loopback = 127.0.0.1 tabani; tcp_seri_koprusu = "
                  "iki gercek pyserial socket:// ucu (D-388 kalibi). SiK 433 MHz "
                  "satirlari OLCULEMEDI."),
        "kosumlar": {},
    }
    satirlar = []
    for duzenek, fn in (("udp_loopback", udp_loopback),
                        ("tcp_seri_koprusu", tcp_seri_koprusu)):
        for kadans_adi, aralik in KADANSLAR.items():
            ad = f"{duzenek}_{kadans_adi}"
            print(f"[{ad}] n={N_PROB} aralik={aralik} s ... ", flush=True)
            cikti, meta = fn(kadans_adi, aralik)
            rapor = json.loads(cikti.read_text(encoding="utf-8"))
            meta["dosya"] = cikti.name
            meta["rtt_ms"] = rapor["rtt_ms"]
            meta["kayip_yuzde"] = rapor["kayip_yuzde"]
            meta["veri_hizi"] = rapor["veri_hizi"]
            meta["verdikt"] = rapor["verdikt"]
            ozet["kosumlar"][ad] = meta
            satir = _ozet_satiri(ad, rapor)
            satirlar.append(satir)
            print("   " + satir, flush=True)
    (BURASI / "ozet.json").write_text(
        json.dumps(ozet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n".join(["", "OZET"] + satirlar))
    print(f"yazildi: {BURASI / 'ozet.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
