"""ONARIM-03: YKS <-> Jetson eslestirme araci ("Bluetooth mantigi").

  YKS PC'sinde (bir kez):
    python scripts/yks_eslestir.py yeni --dosya ~/.config/navitas/yks_eslesme.json [--ad YKS-PC]
      -> kimlik + anahtar uretir, ESLESME KODU'nu basar.
  Jetson'da:
    python3 scripts/yks_eslestir.py tara [--sure 5] [--dosya /etc/navitas/yks_eslesme.json]
      -> agdaki YKS duyurularini listeler (kimlik, IP, port, imza dogru mu).
    python3 scripts/yks_eslestir.py esle --kimlik <KIMLIK> --anahtar <HEX> --dosya /etc/navitas/yks_eslesme.json
      -> secilen YKS'yi kaydeder ve ESLESME KODU'nu basar; iki ekrandaki kod AYNI olmali.
    (ya da YKS'deki dosya guvenli kanaldan — USB/scp — kopyalanir.)
"""
import argparse
import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "comms"))
import yks_kesif as yk  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    alt = ap.add_subparsers(dest="komut", required=True)
    y = alt.add_parser("yeni")
    y.add_argument("--dosya", type=Path, required=True)
    y.add_argument("--ad", default=None)
    y.add_argument("--tur", choices=yk.DUGUM_TURLERI, default="YKS",
                   help="YKS (hakem PC'si) ya da IKA (Raspberry Pi) — ONARIM-03c")
    y.add_argument("--uzerine-yaz", action="store_true")
    t = alt.add_parser("tara")
    t.add_argument("--sure", type=float, default=5.0)
    t.add_argument("--dosya", type=Path, default=None, help="varsa imza dogrulanir")
    t.add_argument("--port", type=int, default=yk.DUYURU_PORT)
    e = alt.add_parser("esle")
    e.add_argument("--kimlik", required=True)
    e.add_argument("--anahtar", required=True)
    e.add_argument("--dosya", type=Path, required=True)
    e.add_argument("--tur", choices=yk.DUGUM_TURLERI, default="YKS")
    a = ap.parse_args(argv)

    if a.komut == "yeni":
        if a.dosya.exists() and not a.uzerine_yaz:
            es = yk.eslesme_oku(a.dosya)
            print(f"MEVCUT eslesme korunuyor: {a.dosya}")
        else:
            es = yk.eslesme_uret(a.ad or a.tur, a.tur)
            yk.eslesme_yaz(a.dosya, es)
            print(f"YENI eslesme yazildi: {a.dosya}")
        print(f"tur    : {es.get('tur', 'YKS')}\nkimlik : {es['kimlik']}\nanahtar: {es['anahtar']}\nESLESME KODU: {yk.eslesme_kodu(es)}")
        return 0

    if a.komut == "esle":
        es = {"kimlik": a.kimlik, "anahtar": a.anahtar.strip().lower(), "ad": a.kimlik.split("-")[0],
              "tur": a.tur}
        bytes.fromhex(es["anahtar"])
        yk.eslesme_yaz(a.dosya, es)
        print(f"eslesme kaydedildi: {a.dosya}\nESLESME KODU: {yk.eslesme_kodu(es)} (YKS ekranindakiyle AYNI olmali)")
        return 0

    secici = yk.YksSecici(yk.eslesme_oku(a.dosya)) if a.dosya else None
    s = yk.dinleyici_soketi(("0.0.0.0", a.port))
    s.settimeout(0.3)
    bitis = time.monotonic() + a.sure
    gorulen = {}
    while time.monotonic() < bitis:
        try:
            veri, adr = s.recvfrom(2048)
        except socket.timeout:
            continue
        m = yk.duyuru_coz(veri)
        if m is None:
            continue
        sonuc = secici.isle(veri, adr[0]) if secici else "IMZA_DENETLENMEDI"
        gorulen[(f"{m['tur']}:{m['kimlik']}", adr[0], m["port"])] = sonuc
    s.close()
    if not gorulen:
        print(f"{a.sure:g} s icinde YKS duyurusu YOK (port {a.port}; YKS acik mi, ayni agda mi, guvenlik duvari?)")
        return 2
    print(f"{'TUR:KIMLIK':<28} {'IP':<16} {'PORT':<6} DURUM")
    for (kimlik, ip, port), sonuc in sorted(gorulen.items()):
        isaret = " <- SECILEN" if sonuc in ("KABUL", "ADRES_DEGISTI") else ""
        print(f"{kimlik:<28} {ip:<16} {port:<6} {sonuc}{isaret}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
