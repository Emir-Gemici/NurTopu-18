"""YKS saha olaylarını dayanıklı, makinece okunur JSONL kanıtına yazar.

Ekrandaki kayan metin uçuş sonrası kanıt değildir. Bu sınıf her kaydı UTF-8
JSON satırı olarak yazar, ``flush`` + ``fsync`` ile işletim sistemi tamponundan
diske iter ve aynı dosyada birden çok oturumu açık kimlikle ayırır.
"""

import json
import math
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


KAYIT_SURUMU = 1


def varsayilan_hakem_log_yolu(proje_koku=None, simdi=None, pid=None):
    """Çakışmayan varsayılan prova yolunu üret; dosyayı henüz oluşturma."""
    kok = (Path(proje_koku) if proje_koku is not None
           else Path(__file__).resolve().parents[1])
    an = datetime.now().astimezone() if simdi is None else simdi
    if not isinstance(an, datetime):
        raise TypeError("simdi datetime olmalı")
    if an.tzinfo is None:
        an = an.replace(tzinfo=timezone.utc).astimezone()
    kimlik = os.getpid() if pid is None else int(pid)
    damga = an.strftime("%Y%m%d_%H%M%S")
    return kok / "results" / "prova" / f"{damga}_{kimlik}" / "hakem_log.jsonl"


class HakemKaydi:
    """Thread-safe JSONL yazıcı; yazma hatasını asla yutmaz."""

    def __init__(self, yol, *, saat=time.time, monotonic=time.monotonic,
                 fsync=os.fsync, oturum_id=None):
        self.yol = Path(yol)
        if self.yol.name in ("", ".", ".."):
            raise ValueError("hakem kayıt yolu bir dosya olmalı")
        if not callable(saat) or not callable(monotonic) or not callable(fsync):
            raise TypeError("saat/monotonic/fsync çağrılabilir olmalı")
        self._saat = saat
        self._monotonic = monotonic
        self._fsync = fsync
        self._kilit = threading.Lock()
        self._kapali = False
        self.oturum_id = str(oturum_id or uuid.uuid4())
        self.yol.parent.mkdir(parents=True, exist_ok=True)
        self._dosya = self.yol.open("a", encoding="utf-8", newline="\n")
        try:
            self.yaz("OTURUM_BASLADI")
        except Exception:
            self._dosya.close()
            self._kapali = True
            raise

    @staticmethod
    def _zaman_iso(saniye):
        if isinstance(saniye, bool):
            raise ValueError("duvar saati sonlu olmalı")
        deger = float(saniye)
        if not math.isfinite(deger):
            raise ValueError("duvar saati sonlu olmalı")
        return datetime.fromtimestamp(deger, timezone.utc).astimezone().isoformat(
            timespec="milliseconds")

    def yaz(self, olay, **alanlar):
        olay = str(olay).strip()
        if not olay:
            raise ValueError("olay adı boş olamaz")
        mono = float(self._monotonic())
        if not math.isfinite(mono):
            raise ValueError("monotonic saat sonlu olmalı")
        kayit = {
            "v": KAYIT_SURUMU,
            "ts": self._zaman_iso(self._saat()),
            "monotonic_s": round(mono, 6),
            "oturum": self.oturum_id,
            "olay": olay,
        }
        kayit.update(alanlar)
        satir = json.dumps(kayit, ensure_ascii=False, separators=(",", ":"),
                           allow_nan=False)
        with self._kilit:
            if self._kapali:
                raise RuntimeError("hakem kaydı kapalı")
            self._dosya.write(satir + "\n")
            self._dosya.flush()
            self._fsync(self._dosya.fileno())
        return kayit

    def kapat(self):
        with self._kilit:
            if self._kapali:
                return False
        # ``yaz`` kilidi kendi alır; kapatma olayı gerçekten diske gittikten
        # sonra tutamaç kapanır.
        self.yaz("OTURUM_BITTI")
        with self._kilit:
            self._kapali = True
            self._dosya.close()
        return True

    def __enter__(self):
        return self

    def __exit__(self, _tur, _deger, _iz):
        self.kapat()
