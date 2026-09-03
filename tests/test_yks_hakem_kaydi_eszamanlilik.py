"""Hakem JSONL kaydında eşzamanlı kapanışın atomiklik kapıları.

NEDEN: Eski ``kapat`` açık-durum kontrolü, ``OTURUM_BITTI`` yazımı ve dosya
kapatma arasında kilidi bırakıyordu. Başka bir yazıcı bitiş satırının arkasına
olay sızdırabiliyor; iki kapatıcı da aynı oturumu bitirebiliyordu. Uçuş kanıtında
bitişten sonraki olay, yeniden oynatmanın sınırını belirsizleştirir.
"""

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path


KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

from hakem_kaydi import HakemKaydi  # noqa: E402


def _olaylar(yol):
    return [json.loads(s)["olay"] for s in
            Path(yol).read_text(encoding="utf-8").splitlines() if s.strip()]


class _EskiKapatmaAraliginiAcanKayit(HakemKaydi):
    """Eski ``kapat -> self.yaz(OTURUM_BITTI)`` aralığını deterministik aç."""

    def __init__(self, *args, **kwargs):
        self.bitis_yazildi = threading.Barrier(2)
        self.sizma_bitti = threading.Barrier(2)
        super().__init__(*args, **kwargs)

    def yaz(self, olay, **alanlar):
        kayit = super().yaz(olay, **alanlar)
        if olay == "OTURUM_BITTI":
            # Eski uygulama public yaz() dönüşü ile _kapali=True arasında burada
            # bekler. Atomik uygulama kapanışı public yaz() üzerinden yapmaz.
            self.bitis_yazildi.wait(timeout=1.0)
            self.sizma_bitti.wait(timeout=1.0)
        return kayit


class HakemKaydiEszamanlilik(unittest.TestCase):

    def test_mutasyon_eski_kapatma_araligina_olay_sizamaz(self):
        """Eski uygulamada BITTI ardından SIZINTI üretirdi; yeni yol kapalıdır."""
        with tempfile.TemporaryDirectory(dir=KOK) as gecici:
            yol = Path(gecici) / "hakem.jsonl"
            kayit = _EskiKapatmaAraliginiAcanKayit(yol)
            hatalar = []

            def kapatici():
                try:
                    kayit.kapat()
                except Exception as exc:  # pragma: no cover - tanı çıktısı
                    hatalar.append(exc)

            isci = threading.Thread(target=kapatici)
            isci.start()
            try:
                public_bitis_cagrildi = True
                try:
                    kayit.bitis_yazildi.wait(timeout=0.15)
                except threading.BrokenBarrierError:
                    public_bitis_cagrildi = False

                if public_bitis_cagrildi:
                    # Bu kol yalnız eski, yarışa açık kapat() uygulamasında
                    # ulaşılabilir: bitiş yazıldı ama kayıt hâlâ açıktır.
                    kayit.yaz("SIZINTI")
                    kayit.sizma_bitti.wait(timeout=1.0)
                else:
                    isci.join(timeout=1.0)
                    with self.assertRaises(RuntimeError):
                        kayit.yaz("SIZINTI")
            finally:
                # Bir assertion eski mutasyonda düşse bile iş parçacığını asma.
                if public_bitis_cagrildi:
                    try:
                        kayit.sizma_bitti.abort()
                    except threading.BrokenBarrierError:
                        pass
                isci.join(timeout=1.0)

            self.assertFalse(isci.is_alive())
            self.assertEqual([], hatalar)
            self.assertEqual(["OTURUM_BASLADI", "OTURUM_BITTI"], _olaylar(yol))

    def test_iki_eszamanli_kapatma_tek_bitis_uretir(self):
        with tempfile.TemporaryDirectory(dir=KOK) as gecici:
            yol = Path(gecici) / "hakem.jsonl"
            kayit = HakemKaydi(yol)
            basla = threading.Barrier(3)
            sonuclar = []
            hatalar = []

            def kapatici():
                basla.wait(timeout=1.0)
                try:
                    sonuclar.append(kayit.kapat())
                except Exception as exc:  # pragma: no cover - tanı çıktısı
                    hatalar.append(exc)

            isciler = [threading.Thread(target=kapatici) for _ in range(2)]
            for isci in isciler:
                isci.start()
            basla.wait(timeout=1.0)
            for isci in isciler:
                isci.join(timeout=1.0)

            self.assertTrue(all(not isci.is_alive() for isci in isciler))
            self.assertEqual([], hatalar)
            self.assertCountEqual([True, False], sonuclar)
            olaylar = _olaylar(yol)
            self.assertEqual(1, olaylar.count("OTURUM_BITTI"))
            self.assertEqual("OTURUM_BITTI", olaylar[-1])

    def test_yazici_kapanis_yarisi_bitis_sonrasina_sizmaz(self):
        with tempfile.TemporaryDirectory(dir=KOK) as gecici:
            yol = Path(gecici) / "hakem.jsonl"
            kayit = HakemKaydi(yol)
            basla = threading.Barrier(3)
            hatalar = []

            def yazici():
                basla.wait(timeout=1.0)
                try:
                    kayit.yaz("ESZAMANLI_OLAY")
                except RuntimeError:
                    pass  # kapanış kilidi önce aldı: beklenen kapalı sonuç
                except Exception as exc:  # pragma: no cover - tanı çıktısı
                    hatalar.append(exc)

            def kapatici():
                basla.wait(timeout=1.0)
                try:
                    kayit.kapat()
                except Exception as exc:  # pragma: no cover - tanı çıktısı
                    hatalar.append(exc)

            isciler = [threading.Thread(target=yazici),
                       threading.Thread(target=kapatici)]
            for isci in isciler:
                isci.start()
            basla.wait(timeout=1.0)
            for isci in isciler:
                isci.join(timeout=1.0)

            self.assertTrue(all(not isci.is_alive() for isci in isciler))
            self.assertEqual([], hatalar)
            olaylar = _olaylar(yol)
            self.assertEqual(1, olaylar.count("OTURUM_BITTI"))
            self.assertEqual("OTURUM_BITTI", olaylar[-1])


if __name__ == "__main__":
    unittest.main()
