"""KAMERA ODAK OLCER — lens odak halkasini ayarlarken canli keskinlik gostergesi (ONARIM-04).

NEDEN: canli IMX477 + 6 mm karelerinin keskinligi 1,5-2,3 cikti (sigma~10 bulaniklik
esdegeri); bu bolgede model zemini tamamen kaybedip kareyi ENGEL sayiyor -> her karar
MASKE_YOK. Olcu ve bantlar: codes/kare_keskinligi.py (on kayitli).

KULLANIM
  # Jetson'da kopru acikken (kamera_koprusu --kaynak nvargus ...):
  python3 scripts/kamera_odak_olcer.py --url http://127.0.0.1:8080/kare.jpg
  #   -> her ~0,5 s: keskinlik, bant (NET/SUPHELI/BULANIK), oturumun en iyisi.
  #   Kamerayi >= 10 m uzaga (pencere disi / saha) cevir, halkayi yavasca dondur,
  #   deger TEPE yaptigi yerde birak ve vidayi sik.
  python3 scripts/kamera_odak_olcer.py --dosya kare1.jpg kare2.jpg   # kayitli kareler

Cikis kodu (--sure ya da --dosya ile): 0 son olcum NET · 1 SUPHELI/BULANIK · 2 olculemedi.
"""
import argparse
import sys
import time
import urllib.request
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codes"))
from kare_keskinligi import KESKIN_NET, kare_keskinligi, keskinlik_bandi  # noqa: E402

CIKIS_NET, CIKIS_DEGIL, CIKIS_OLCULEMEDI = 0, 1, 2


def urlden_kare(url, zaman_asimi=3.0):
    with urllib.request.urlopen(url, timeout=zaman_asimi) as yanit:
        veri = np.frombuffer(yanit.read(), np.uint8)
    kare = cv2.imdecode(veri, cv2.IMREAD_COLOR)
    if kare is None:
        raise ValueError("JPEG cozulemedi")
    return kare


def satir(deger, en_iyi):
    return (f"keskinlik {deger:9.1f}  {keskinlik_bandi(deger):8s}  "
            f"en iyi {en_iyi:9.1f}  " + "#" * min(60, int(np.log10(max(deger, 1.0)) * 15)))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="kopru kare ucu, or. http://127.0.0.1:8080/kare.jpg")
    g.add_argument("--dosya", nargs="+", type=Path, help="kayitli kare(ler)")
    ap.add_argument("--aralik", type=float, default=0.5, help="URL yoklama araligi s")
    ap.add_argument("--sure", type=float, default=None, help="URL kipinde toplam sure s (yoksa Ctrl+C)")
    a = ap.parse_args(argv)

    if a.dosya:
        kod = CIKIS_NET
        for yol in a.dosya:
            kare = cv2.imread(str(yol))
            if kare is None:
                print(f"OLCULEMEDI {yol}")
                kod = max(kod, CIKIS_OLCULEMEDI)
                continue
            d = kare_keskinligi(kare)
            print(f"{yol.name}: {satir(d, d)}")
            if keskinlik_bandi(d) != KESKIN_NET:
                kod = max(kod, CIKIS_DEGIL)
        return kod

    en_iyi, son, bitis = 0.0, None, (time.monotonic() + a.sure) if a.sure else None
    try:
        while bitis is None or time.monotonic() < bitis:
            try:
                son = kare_keskinligi(urlden_kare(a.url))
                en_iyi = max(en_iyi, son)
                print(satir(son, en_iyi), flush=True)
            except Exception as exc:
                print(f"OLCULEMEDI: {exc!r}", flush=True)
            time.sleep(a.aralik)
    except KeyboardInterrupt:
        pass
    if son is None:
        return CIKIS_OLCULEMEDI
    return CIKIS_NET if keskinlik_bandi(son) == KESKIN_NET else CIKIS_DEGIL


if __name__ == "__main__":
    sys.exit(main())
