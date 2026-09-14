"""P9d (D-394) — SAHA TEK-KOMUT ACILIS (thazirlik, sartname §6.2).

NEDEN: §6.2 kurulum icin 15 dk verir; 900 s'den tasarruf edilen her 30 s
+1 puandir ve hands-off sonrasi fiziksel mudahale -100'dur. Sahada bayrak
hatirlamaya calismak hem sure yakar hem hata uretir. Bu betik istasyon
basina TEK komuttur: dogru bayraklarla bileseni kaldirir, acilis suresini
olcup yazar.

Kullanim (saha):
  <venv> scripts/saha_baslat.py yks --fda --ika 10.0.0.2:5006 --iha 10.0.0.3:5007 --kamera-url http://10.0.0.3:8080
  <venv> scripts/saha_baslat.py yks --fda --serial COM5 --kamera-url http://192.168.4.2:8080
  <venv> scripts/saha_baslat.py ika --yks 10.0.0.1:5005
  <venv> scripts/saha_baslat.py --komutlar                 # karti yazdir
  <venv> scripts/saha_baslat.py --reset                    # tekrar-firlatma yordami

D-403 (KRITIK-1): YKS, IHA komut alicisini (`iha_komut_alici --bind`) yalniz
`--iha HOST:PORT` ile pinler. Verilmezse PARACHUTE/ARM komutlari heartbeat'ten
ogrenilen adrese — rpi_inference'in EFEMER portuna — gider ve aliciya HIC
ulasmaz. Bu betik UDP kipinde bayragi gecirir; verilmezse gorunur uyarir.
SiK kipinde adresler anlamsizdir (yks_gui serialde --iha'yi sessizce yutar);
o birlesim burada REDDEDILIR — sessiz basari yalani yok.

Jetson tarafi bu betikle ACILMAZ — cihazda `jetson_paket/` kilavuzu gecerli
(SAHA_RUNBOOK.md §3'te tek satiri var).
"""
import argparse
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

# cp1254 konsollarda ⚠ gibi isaretler patlamasin (repo kalibi)
for _akim in (sys.stdout, sys.stderr):
    try:
        _akim.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

KOK = Path(__file__).resolve().parents[1]
VENV = sys.executable

#: Ilk cikti satiri icin bekleme tavani; GUI'ler stdout'a gec yazabilir.
ACILIS_ISARET_TAVANI_S = 30.0

#: --komutlar karti yer tutuculari. Portlar sozlesmeden gelir, burada yalniz
#: ORNEK olarak yazilir: 5005 = yks_gui --bind varsayilani, 5006 = ika_nav
#: comms dinleme ucu, 5007 = comms/iha_komut_alici.VARSAYILAN_BIND (D-403).
KART_IKA_HEDEF = "<IKA_IP>:5006"
KART_YKS_HEDEF = "<YKS_IP>:5005"
KART_IHA_HEDEF = "<JETSON_IP>:5007"
KART_KAMERA_URL = "http://<JETSON_IP>:8080"

#: UDP kipinde --iha verilmezse basilan uyari (D-403 KRITIK-1; fail-visible).
IHA_EKSIK_UYARISI = (
    "⚠ --iha verilmedi: PARAŞÜT/ARM komutları rpi_inference'ın efemer portuna "
    "gider, iha_komut_alici'ya ULAŞMAZ (D-403). Sahada `--iha "
    f"{KART_IHA_HEDEF}` ver.")

RESET_YORDAMI = """\
TEKRAR FIRLATMA / RESET YORDAMI (sartname §6.2 — sure 15 dk'dan yer)
  1. YKS: R tusu (onay_sifirla) — tespit/onay durumu sifirlanir.
  2. YKS: ARM durumunu kontrol et; gerekiyorsa A ile yeniden ARM.
  3. IKA: ika_nav zaten NO_ROUTE/izin-yok durumunda guvenli durusta bekler;
     surec OLDURULMEZ (bekleme son tarihi §6.2 icinde islemeye devam eder).
  4. Jetson: rpi_inference kosmaya devam eder — yeniden baslatma GEREKMEZ;
     yeni ucusun kararlari ayni hatta akar.
  5. Kronometreler: FIRLATMA damgasi yeni atista yeniden atilir.
  ⚠ Hicbir adimda arac donanimina fiziksel mudahale yoktur (-100 ceza)."""


def komut_uret(kip, ika=None, yks=None, serial=None, baud=None, iha=None,
               kamera_url=None, fda=False, tek_rota=False):
    """Istasyon komutunu TEK yerden uret (runbook bu ciktiyi kopyalar).

    `iha` yalniz yks kipinde ve yalniz UDP'de anlamlidir: yks_gui serial
    dalinda `--iha`yi sessizce yutar (iha_peer=None); sessiz yutmayi burada
    ValueError'a ceviririz ki operator pinledigini SANMASIN (D-403).
    """
    if fda and kip != "yks":
        raise ValueError("--fda yalnız YKS kipinde kullanılabilir")
    if tek_rota and kip != "yks":
        raise ValueError("--tek-rota yalnız YKS kipinde kullanılabilir")
    if kip == "yks":
        komut = [VENV, str(KOK / "comms" / "yks_gui.py")]
        if fda:
            komut.append("--fda")
        if tek_rota:
            komut.append("--tek-rota")
        if serial:
            if iha:
                raise ValueError(
                    "--serial (SiK) kipinde --iha gecilmez: yks_gui serialde "
                    "UDP adresi kabul etmez; komutlar seri hattan gider")
            komut += ["--serial", serial]
            if baud:
                komut += ["--baud", str(baud)]
        if ika:
            komut += ["--ika", ika]
        if iha:
            komut += ["--iha", iha]
        if kamera_url:
            komut += ["--kamera-url", kamera_url]
        return komut
    if kip == "ika":
        komut = [VENV, str(KOK / "simulation" / "scripts" / "ika_nav.py"),
                 "comms"]
        if yks:
            komut += ["--yks", yks]
        if serial:
            komut += ["--serial", serial]
            if baud:
                komut += ["--baud", str(baud)]
        return komut
    raise ValueError(f"bilinmeyen kip: {kip!r}")


def iha_eksik_uyarisi(kip, iha=None, serial=None):
    """UDP yks kipinde --iha yoksa uyari metnini dondur; aksi halde None.

    Ayri fonksiyon: main() GUI'yi acar, test edilemez; bu karar edilebilir.
    """
    if kip == "yks" and not serial and not iha:
        return IHA_EKSIK_UYARISI
    return None


def acilis_olc(komut, cikti=sys.stdout, tavan_s=ACILIS_ISARET_TAVANI_S):
    """Komutu başlat; sessiz GUI yüzünden süre ölçümünü sonsuza dek kilitleme.

    Çocuk çıktısını tek bir arka-plan okuyucusu aktarır. Ana iş parçacığı ilk
    satırı en fazla ``tavan_s`` bekler; süreç sağ ve sessizse uyarıyı basıp
    çağırana geri döner. Böylece GUI'nin stdout yazmaması açılış kartını
    dondurmaz, sonradan gelen çıktı da aynı okuyucu üzerinden kaybolmadan akar.
    """
    try:
        tavan = float(tavan_s)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("açılış işaret tavanı pozitif olmalı") from exc
    if not (0.0 < tavan < float("inf")):
        raise ValueError("açılış işaret tavanı pozitif olmalı")
    t0 = time.monotonic()
    print(f"[saha_baslat] {' '.join(komut)}", file=cikti, flush=True)
    cocuk = subprocess.Popen(komut, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace")
    ilk_kuyruk = queue.Queue(maxsize=1)
    yazma_kilidi = threading.Lock()

    def _aktar():
        ilk_goruldu = False
        try:
            for satir in cocuk.stdout:
                if not ilk_goruldu:
                    ilk_goruldu = True
                    try:
                        ilk_kuyruk.put_nowait(satir)
                    except queue.Full:
                        pass
                with yazma_kilidi:
                    print(satir, end="", file=cikti, flush=True)
        finally:
            if not ilk_goruldu:
                try:
                    ilk_kuyruk.put_nowait(None)
                except queue.Full:
                    pass

    threading.Thread(target=_aktar, name="saha-cikti-aktar",
                     daemon=True).start()
    try:
        ilk = ilk_kuyruk.get(timeout=tavan)
    except queue.Empty:
        ilk = None
    gecen = time.monotonic() - t0
    if ilk:
        with yazma_kilidi:
            print(f"[saha_baslat] AÇILIŞ {gecen:.1f} s "
                  f"(ilk işaret: {ilk.strip()!r})", file=cikti, flush=True)
    else:
        durum = ("süreç çıktı vermeden kapandı" if cocuk.poll() is not None
                 else "süreç çalışıyor (GUI sessiz)")
        with yazma_kilidi:
            print(f"[saha_baslat] ⚠ {gecen:.1f} s içinde çıktı işareti yok — "
                  f"{durum}; pencere/servis sağlığını doğrula",
                  file=cikti, flush=True)
    return cocuk


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("kip", nargs="?", choices=("yks", "ika"))
    ap.add_argument("--ika", help="IKA adresi host:port (yks kipinde)")
    ap.add_argument("--iha", help="IHA komut alicisi host:port (yks kipinde, "
                                  "UDP; iha_komut_alici --bind ucu — D-403: "
                                  "verilmezse PARASUT komutu aliciya ULASMAZ)")
    ap.add_argument("--yks", help="YKS adresi host:port (ika kipinde)")
    ap.add_argument("--serial", help="SiK seri portu (orn. COM5, /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=None)
    ap.add_argument("--kamera-url",
                    help="Jetson RAW kamera kökü (ayrı Wi-Fi/LAN; SiK değil)")
    ap.add_argument("--fda", action="store_true",
                    help="21 Eylül çoklu-rotor görev kipi (YKS için)")
    ap.add_argument("--tek-rota", action="store_true",
                    help="YKS tek-rota / koordinat / hareket incelemesi; --fda ile kendiliğinden açılır")
    ap.add_argument("--komutlar", action="store_true",
                    help="thazirlik kartini yazdir ve cik")
    ap.add_argument("--reset", action="store_true",
                    help="tekrar-firlatma yordamini yazdir ve cik")
    args = ap.parse_args(argv)

    if args.reset:
        print(RESET_YORDAMI)
        return 0
    if args.komutlar or not args.kip:
        print("SAHA AÇILIŞ KARTI (hazırlık — istasyon başına TEK komut):")
        print("  YKS FDA :", " ".join(komut_uret(
            "yks", ika=KART_IKA_HEDEF, iha=KART_IHA_HEDEF,
            kamera_url=KART_KAMERA_URL, fda=True)))
        print("  YKS YARIŞMA :", " ".join(komut_uret(
            "yks", ika=KART_IKA_HEDEF, iha=KART_IHA_HEDEF,
            kamera_url=KART_KAMERA_URL)))
        print("        (--iha = Jetson'daki iha_komut_alici --bind ucu; "
              "verilmezse PARAŞÜT alıcıya ULAŞMAZ — D-403)")
        print("  İKA :", " ".join(komut_uret("ika", yks=KART_YKS_HEDEF)))
        print("  SiK :", " ".join(komut_uret(
            "yks", serial="COM5", baud=57600,
            kamera_url=KART_KAMERA_URL, fda=True)))
        print("  Jetson: bkz. SAHA_RUNBOOK.md §3 (cihazda jetson_paket/)")
        return 0

    if args.serial and args.iha:
        ap.error("--serial (SiK) kipinde --iha kullanılamaz: yks_gui serialde "
                 "UDP adresi kabul etmez (komutlar seri hattan gider)")
    if args.fda and args.kip != "yks":
        ap.error("--fda yalnız YKS kipinde kullanılabilir")
    if args.tek_rota and args.kip != "yks":
        ap.error("--tek-rota yalnız YKS kipinde kullanılabilir")
    if args.kip == "yks" and not args.serial and not args.iha:
        ap.error("UDP YKS kipinde --iha HOST:PORT zorunlu; eyleyici komutlar "
                 "efemer heartbeat portuna gönderilemez")
    uyari = iha_eksik_uyarisi(args.kip, iha=args.iha, serial=args.serial)
    if uyari:
        print(f"[saha_baslat] {uyari}", file=sys.stderr, flush=True)

    komut = komut_uret(args.kip, ika=args.ika, yks=args.yks,
                       serial=args.serial, baud=args.baud, iha=args.iha,
                       kamera_url=args.kamera_url, fda=args.fda, tek_rota=args.tek_rota)
    cocuk = acilis_olc(komut)
    return cocuk.wait()


if __name__ == "__main__":
    sys.exit(main())
