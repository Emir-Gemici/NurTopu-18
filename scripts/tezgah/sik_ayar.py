#!/usr/bin/env python3
"""TEZGAH: SiK/RFD900 telsiz parametrelerini Mission Planner OLMADAN oku/yaz (AT komutlari).

NEDEN: K8 olcumu bu Linux PC'de yapilacak ama Mission Planner yok; MAX_WINDOW normalde
MP'nin SiK ekranindan degistiriliyor. Ayrica denetim sarti: her olcumden ONCE ve SONRA
iki telsizin parametre DOKUMU alinmali ki "yalniz MAX_WINDOW degisti" KANITLANABILSIN
(D-479: ayarin degistigi VARSAYILDI, 131'de kalmisti, ustune kurulan teshis curudu).

URETIM KODU DEGILDIR. Ucus yoluna dokunmaz. Yalniz seri porttan AT komutu konusur.

GUVENLIK:
  * Varsayilan SALT OKUMA. Yazma icin --yaz gerekir.
  * Yazmadan once mevcut deger gosterilir; --yaz ile ayni degerse hicbir sey yapilmaz.
  * Her yazmadan sonra GERI ALMA komutu ekrana basilir.
  * Yerel (AT) ve uzak (RT) ayri ayri; ikisi de yazilmazsa telsizler ESLESMEZ ve
    baglanti tamamen kesilir — arac bunu acikca uyarir.

AT KOMUT OZETI (SiK firmware):
  +++      komut moduna gec (once/sonra 1 s sessizlik; "OK" doner)
  ATI5     yerel parametre dokumu     RTI5   uzak parametre dokumu
  ATS<n>=<v>  yerel yaz              RTS<n>=<v>  uzak yaz
  AT&W     kaydet (EEPROM)           RT&W   uzak kaydet
  ATZ      yeniden baslat            RTZ    uzak yeniden baslat
  ATO      veri moduna don

Kullanim:
  python scripts/tezgah/sik_ayar.py --port /dev/ttyUSB0 --dokum
  python scripts/tezgah/sik_ayar.py --port /dev/ttyUSB0 --dokum --cikti results/.../once.json
  python scripts/tezgah/sik_ayar.py --port /dev/ttyUSB0 --yaz MAX_WINDOW=33 --uzak-da
  python scripts/tezgah/sik_ayar.py --kuru --yaz MAX_WINDOW=33 --uzak-da   # port acmaz
"""
import argparse
import json
import re
import sys
import time

SESSIZLIK_S = 1.1           # +++ oncesi/sonrasi zorunlu sessizlik (SiK sarti)
OKUMA_ZAMAN_ASIMI_S = 2.0
SATIR = re.compile(r"^S(\d+):\s*([A-Z_0-9]+)=(-?\d+)\s*$")


def _seri_ac(port, baud):
    try:
        import serial
    except ImportError:
        raise SystemExit("pyserial yok: .venv/bin/python -m pip install pyserial")
    return serial.Serial(port, baud, timeout=0.3)


def _oku_hepsi(s, sure_s=OKUMA_ZAMAN_ASIMI_S):
    bas = time.monotonic()
    tampon = b""
    while time.monotonic() - bas < sure_s:
        veri = s.read(4096)
        if veri:
            tampon += veri
            bas = time.monotonic()          # veri geldikce uzat
    return tampon.decode("utf-8", "replace")


def komut_moduna_gec(s, log=print):
    s.reset_input_buffer()
    time.sleep(SESSIZLIK_S)
    s.write(b"+++")
    s.flush()
    time.sleep(SESSIZLIK_S)
    cevap = _oku_hepsi(s, 1.0)
    if "OK" not in cevap.upper():
        log("UYARI: '+++' sonrasi OK gorulmedi (cevap: %r) — zaten komut modunda olabilir" % cevap[-40:])
        return False
    return True


def at(s, komut, bekle_s=OKUMA_ZAMAN_ASIMI_S):
    s.reset_input_buffer()
    s.write((komut + "\r\n").encode())
    s.flush()
    return _oku_hepsi(s, bekle_s)


def dokum_coz(metin):
    """ATI5/RTI5 ciktisini {ad: (numara, deger)} sozluguna cevir."""
    p = {}
    for satir in metin.splitlines():
        m = SATIR.match(satir.strip())
        if m:
            p[m.group(2)] = (int(m.group(1)), int(m.group(3)))
    return p


def dokum_al(s, uzak=False, log=print):
    onek = "RT" if uzak else "AT"
    ham = at(s, onek + "I5", 3.0)
    p = dokum_coz(ham)
    if not p:
        log("UYARI: %sI5 dokumu cozulemedi (ham: %r)" % (onek, ham[:120]))
    return p, ham


def _yaz_tek(s, ad, deger, mevcut, uzak, log):
    onek = "RT" if uzak else "AT"
    etiket = "UZAK" if uzak else "YEREL"
    if ad not in mevcut:
        log("HATA: %s telsizde '%s' parametresi yok — yazilmadi" % (etiket, ad))
        return False
    no, eski = mevcut[ad]
    if eski == deger:
        log("%s %s zaten %d — dokunulmadi" % (etiket, ad, deger))
        return True
    log("%s %s: %d -> %d  (S%d)" % (etiket, ad, eski, deger, no))
    log("   cevap: %r" % at(s, "%sS%d=%d" % (onek, no, deger)).strip()[:60])
    log("   kaydet: %r" % at(s, onek + "&W").strip()[:60])
    log("   ⟲ GERI ALMA: %sS%d=%d  sonra  %s&W  sonra  %sZ" % (onek, no, eski, onek, onek))
    return True


def main(argv=None):
    ap = argparse.ArgumentParser(description="SiK/RFD telsiz parametresi oku/yaz (MP gerekmez)")
    ap.add_argument("--port", help="yer telsizi seri portu (or. /dev/ttyUSB0)")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--dokum", action="store_true", help="yerel + uzak parametreleri oku ve yaz")
    ap.add_argument("--yaz", metavar="AD=DEGER", action="append", default=[],
                    help="parametre yaz (or. MAX_WINDOW=33). Varsayilan YEREL")
    ap.add_argument("--uzak-da", action="store_true",
                    help="--yaz degerlerini UZAK telsize de uygula (ESLESME icin ZORUNLU)")
    ap.add_argument("--yeniden-baslat", action="store_true", help="yazma sonrasi ATZ/RTZ")
    ap.add_argument("--cikti", help="dokumu JSON olarak buraya yaz")
    ap.add_argument("--kuru", action="store_true", help="port ACMA, yalnizca ne yapacagini yaz")
    a = ap.parse_args(argv)

    istekler = []
    for m in a.yaz:
        if "=" not in m:
            ap.error("--yaz 'AD=DEGER' bicimindedir: %r" % m)
        ad, _, d = m.partition("=")
        try:
            istekler.append((ad.strip().upper(), int(d)))
        except ValueError:
            ap.error("--yaz degeri tamsayi olmali: %r" % m)

    if a.kuru:
        print("KURU KOSUM — port acilmayacak")
        print("  +++  (once/sonra %.1f s sessizlik)" % SESSIZLIK_S)
        print("  ATI5 / RTI5   (dokum)")
        for ad, d in istekler:
            print("  ATS<no>=%d  + AT&W        # %s (no, ATI5 dokumunden bulunur)" % (d, ad))
            if a.uzak_da:
                print("  RTS<no>=%d  + RT&W        # %s UZAK" % (d, ad))
        if a.yeniden_baslat:
            print("  ATZ" + (" / RTZ" if a.uzak_da else ""))
        if istekler and not a.uzak_da:
            print("\n⚠ UYARI: yalniz YEREL yazilirsa telsizler ESLESMEZ ve baglanti KESILIR.")
        return 0

    if not a.port:
        ap.error("--port gerekli (ya da --kuru)")
    s = _seri_ac(a.port, a.baud)
    try:
        komut_moduna_gec(s)
        yerel, yerel_ham = dokum_al(s, uzak=False)
        uzak, uzak_ham = dokum_al(s, uzak=True)
        print("=== YEREL (%d parametre) ===" % len(yerel))
        for ad, (no, d) in sorted(yerel.items(), key=lambda kv: kv[1][0]):
            print("  S%-2d %-16s = %d" % (no, ad, d))
        print("=== UZAK (%d parametre) ===" % len(uzak))
        for ad, (no, d) in sorted(uzak.items(), key=lambda kv: kv[1][0]):
            print("  S%-2d %-16s = %d" % (no, ad, d))

        farklar = [ad for ad in yerel if ad in uzak and yerel[ad][1] != uzak[ad][1]]
        if farklar:
            print("\n⚠ YEREL/UZAK FARKLI: %s" % ", ".join(sorted(farklar)))

        if a.cikti:
            with open(a.cikti, "w", encoding="utf-8") as f:
                json.dump({"t": time.time(), "port": a.port, "baud": a.baud,
                           "yerel": {k: v[1] for k, v in yerel.items()},
                           "uzak": {k: v[1] for k, v in uzak.items()},
                           "yerel_ham": yerel_ham, "uzak_ham": uzak_ham,
                           "yerel_uzak_farki": farklar}, f, ensure_ascii=False, indent=2)
            print("\ndokum yazildi: %s" % a.cikti)

        if istekler:
            if not a.uzak_da:
                print("\n⚠ UYARI: --uzak-da verilmedi. Yalniz yerel yazilirsa telsizler ESLESMEZ "
                      "ve baglanti KESILIR. Devam ediliyor (istenen buysa).")
            print()
            for ad, d in istekler:
                _yaz_tek(s, ad, d, yerel, uzak=False, log=print)
                if a.uzak_da:
                    _yaz_tek(s, ad, d, uzak, uzak=True, log=print)
            if a.yeniden_baslat:
                if a.uzak_da:
                    print("RTZ: %r" % at(s, "RTZ").strip()[:40])
                    time.sleep(2)
                print("ATZ: %r" % at(s, "ATZ").strip()[:40])
        else:
            at(s, "ATO")     # veri moduna don (yazma yoksa)
    finally:
        s.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
