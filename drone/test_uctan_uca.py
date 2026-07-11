"""
Navitas dron yayini — otomatik uctan uca test (donanimsiz, localhost)

rpi_yayin.py'yi --sim modunda baslatir, izleyici protokolunun tamamini dogrular:
  1. HELLO el sikismasi (ACK + RTT/saat-ofseti alanlari)
  2. HAM H.264/MPEG-TS akisi (ffprobe ile codec + cozunurluk)
  3. AI overlay akisi (parca birlestirme, JPEG cozme, kare boyutu, kare_no artisi)
  4. TELEMETRI akisi (JSON alanlari)
  5. Kalp atisi kesilince yayinin durmasi, geri gelince surmesi

Kullanim (repo kokunden, model gerektirir → .venv):
  .venv/bin/python drone/test_uctan_uca.py
  .venv/bin/python drone/test_uctan_uca.py --hizli    # 5. adimi atla (~15 sn kisalir)
"""

import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

_kok = Path(__file__).resolve().parent
sys.path.insert(0, str(_kok))
import cv2  # noqa: E402

from ortak import (AI_BASLIK, AI_PORT, HEDEF_ZAMANASIMI, HELLO_PORT,  # noqa: E402
                   RAW_PORT, TLM_PORT, ack_coz, hello_yap, udp_soket)

REPO = _kok.parent
SIM_KAYNAK = REPO / "test_images" / "ai"

SONUCLAR = []


def kontrol(ad, kosul, detay=""):
    SONUCLAR.append((ad, bool(kosul), detay))
    print(f"  {'✓' if kosul else '✗'} {ad}" + (f"  — {detay}" if detay else ""))
    return bool(kosul)


def hello_at(sock, deadline=10):
    """ACK gelene kadar hello atar; (rtt, ofset) ya da None."""
    sock.settimeout(1.0)
    son = time.time() + deadline
    while time.time() < son:
        try:
            sock.sendto(hello_yap(), ("127.0.0.1", HELLO_PORT))
            sonuc = ack_coz(sock.recv(256))
            if sonuc:
                return sonuc
        except socket.timeout:
            pass
    return None


def ai_kare_topla(ai_sock, n_hedef, deadline):
    """AI portundan n_hedef TAM kare toplar → [(kare_no, cekim, jpg_bytes)]."""
    tampon, kareler = {}, []
    ai_sock.settimeout(1.0)
    son = time.time() + deadline
    while len(kareler) < n_hedef and time.time() < son:
        try:
            data = ai_sock.recv(AI_BASLIK.size + 1500)
        except socket.timeout:
            continue
        kare_no, cekim, idx, toplam = AI_BASLIK.unpack(data[:AI_BASLIK.size])
        g = tampon.setdefault(kare_no, {})
        g[idx] = data[AI_BASLIK.size:]
        if len(g) == toplam:
            kareler.append((kare_no, cekim, b"".join(g[i] for i in range(toplam))))
            del tampon[kare_no]
    return kareler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hizli", action="store_true", help="kalp atisi zaman asimi testini atla")
    args = ap.parse_args()

    if not SIM_KAYNAK.exists():
        print(f"HATA: sim kaynagi yok: {SIM_KAYNAK}")
        return 2

    log_dosya = Path("/tmp/navitas_yayin_test.log")
    print(f"[1/6] rpi_yayin --sim baslatiliyor (log: {log_dosya})")
    proc = subprocess.Popen(
        [sys.executable, str(_kok / "rpi_yayin.py"), "--sim", str(SIM_KAYNAK),
         "--debug", "--log-file", str(log_dosya)],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )

    hb_sock = udp_soket()          # kalp atisi buradan atilir (izleyici benzeri)
    ai_sock = udp_soket(alici_port=AI_PORT)
    tlm_sock = udp_soket(alici_port=TLM_PORT)
    tlm_sock.settimeout(1.0)

    hb_dur = [False]

    def kalp_at():
        # arka planda duzenli kalp atisi (yayinin acik kalmasi icin)
        while not hb_dur[0]:
            try:
                hb_sock.sendto(hello_yap(), ("127.0.0.1", HELLO_PORT))
                hb_sock.settimeout(1.0)
                hb_sock.recv(256)
            except OSError:
                pass
            time.sleep(1.0)

    import threading
    hb_thread = None
    try:
        print("[2/6] HELLO el sikismasi")
        sonuc = hello_at(hb_sock, deadline=15)
        if not kontrol("ACK alindi", sonuc is not None):
            raise SystemExit(1)
        rtt, ofset = sonuc
        kontrol("RTT makul (<200 ms yerel)", rtt < 0.2, f"rtt={rtt*1000:.1f} ms")
        kontrol("saat ofseti makul (<1 sn yerel)", abs(ofset) < 1.0, f"ofset={ofset*1000:.1f} ms")

        hb_thread = threading.Thread(target=kalp_at, daemon=True)
        hb_thread.start()

        print("[3/6] HAM H.264 akisi (ffprobe)")
        if shutil.which("ffprobe"):
            fp = subprocess.run(
                ["ffprobe", "-v", "error", "-show_streams", "-of", "json",
                 f"udp://127.0.0.1:{RAW_PORT}?timeout=15000000"],
                capture_output=True, text=True, timeout=30)
            akislar = json.loads(fp.stdout or "{}").get("streams", [])
            video = next((s for s in akislar if s.get("codec_type") == "video"), None)
            kontrol("MPEG-TS video akisi var", video is not None)
            if video:
                kontrol("codec h264", video.get("codec_name") == "h264",
                        video.get("codec_name"))
                kontrol("cozunurluk 1280x720",
                        (video.get("width"), video.get("height")) == (1280, 720),
                        f"{video.get('width')}x{video.get('height')}")
        else:
            kontrol("ffprobe var", False, "ffprobe bulunamadi, ham akis dogrulanamadi")

        print("[4/6] AI overlay akisi (model yuklemesi surebilir...)")
        # ffprobe adimi boyunca sokette biriken eski kareleri at (tazelik olcumu
        # icin TAZE kare gerekir; gercek izleyici de ayni sekilde drain yapar)
        ai_sock.settimeout(0.2)
        try:
            while True:
                ai_sock.recv(65536)
        except socket.timeout:
            pass
        kareler = ai_kare_topla(ai_sock, n_hedef=5, deadline=90)
        if kontrol("≥5 tam kare alindi", len(kareler) >= 5, f"{len(kareler)} kare"):
            nolar = [k for k, _, _ in kareler]
            kontrol("kare_no artiyor", all(b > a for a, b in zip(nolar, nolar[1:])),
                    f"nolar={nolar}")
            img = cv2.imdecode(np.frombuffer(kareler[-1][2], np.uint8), cv2.IMREAD_COLOR)
            kontrol("JPEG cozuluyor", img is not None)
            if img is not None:
                kontrol("boyut 640x360", img.shape[:2] == (360, 640), str(img.shape))
            yas = time.time() - (kareler[-1][1] + ofset)
            kontrol("cekim zamani taze (<5 sn)", 0 <= yas < 5, f"yas={yas*1000:.0f} ms")

        print("[5/6] TELEMETRI")
        tlm = None
        son = time.time() + 10
        while tlm is None and time.time() < son:
            try:
                tlm = json.loads(tlm_sock.recv(2048).decode())
            except socket.timeout:
                pass
        if kontrol("telemetri paketi geldi", tlm is not None):
            eksik = {"t", "calisma_sn", "ai_fps", "cikarim_ms", "karar", "kare_no"} - set(tlm)
            kontrol("alanlar tam", not eksik, f"eksik={eksik or '-'}  ornek: karar={tlm.get('karar')}")

        if args.hizli:
            print("[6/6] kalp atisi zaman asimi — ATLANDI (--hizli)")
        else:
            print(f"[6/6] kalp atisi kesilince yayin durmali ({HEDEF_ZAMANASIMI:.0f} sn bekleniyor)")
            hb_dur[0] = True
            hb_thread.join(timeout=3)
            time.sleep(HEDEF_ZAMANASIMI + 3)
            # AI portunu bosalt, sonra 3 sn icinde YENI paket gelmemeli
            ai_sock.settimeout(0.1)
            try:
                while True:
                    ai_sock.recv(65536)
            except socket.timeout:
                pass
            ai_sock.settimeout(3.0)
            durdu = False
            try:
                ai_sock.recv(65536)
            except socket.timeout:
                durdu = True
            kontrol("AI yayini durdu", durdu)
            # geri don: tekrar hello → yayin surmeli
            sonuc = hello_at(hb_sock, deadline=10)
            kontrol("yeniden baglanti ACK", sonuc is not None)
            hb_dur[0] = False
            hb_thread = threading.Thread(target=kalp_at, daemon=True)
            hb_thread.start()
            kareler2 = ai_kare_topla(ai_sock, n_hedef=2, deadline=20)
            kontrol("yayin kaldigi yerden surdu", len(kareler2) >= 2, f"{len(kareler2)} kare")

    finally:
        hb_dur[0] = True
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()

    basarili = sum(1 for _, ok, _ in SONUCLAR if ok)
    print(f"\nSONUC: {basarili}/{len(SONUCLAR)} kontrol gecti")
    for ad, ok, detay in SONUCLAR:
        if not ok:
            print(f"  BASARISIZ: {ad}  {detay}")
    print(f"(yayin loglari: {log_dosya})")
    return 0 if basarili == len(SONUCLAR) else 1


if __name__ == "__main__":
    sys.exit(main())
