r"""T248 mutasyon kapısı — H2g kilidinin iki yönünü de ölçer.

N0  mutasyon yok                                            -> YEŞİL (0)
N1  ÜRÜN: `elif rota_yok_temizlendi: self._harita_ciz()` SİLİNİR
    (düzeltme öncesi davranış)                              -> KIRMIZI (1)
N2  ÜRÜN: çizim KOŞULSUZ yapılır (`else:`) — her tekrar kopyasında
    yeniden çizim                                           -> KIRMIZI (1)
    (T248b: 8 kopya için 8 kat yük kilidi gerçekten ölçüyor mu?)
N3  ÜRÜN: tazeleme YALNIZ ana tuvale daraltılır — küçük harita bayat
    kalır                                                   -> KIRMIZI (1)
    (T248c: kamera görünümündeki küçük harita yolu ölçülüyor mu?)

Kaynak dosya bayt düzeyinde bozulur ve `finally` içinde sha256 doğrulanarak
aynen geri yazılır (satır sonu dâhil).
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[4]
CIK = Path(__file__).resolve().parent
URUN = KOK / "comms" / "yks_gui.py"
PY = sys.executable

BLOK = (
    "            elif rota_yok_temizlendi:\n"
    "                # 🔴 T248: NO_ROUTE'tan SONRA gelen TEKRAR kopyasi (sahada\n"
    "                # `iha_sender._tekrarli_gonder(repeat=8, interval=0.25)`\n"
    "                # tam olarak bunu uretir) durumu \"rota kabul\"e cevirir; harita\n"
    "                # cizilmezse hakem ekraninda \"ROTA YOK\" bandi ASILI KALIR ve\n"
    "                # hakem rotayi EKRANDAN onayladigi icin gorev puani etkilenir.\n"
    "                # DAR kosul: yalniz DURUM DEGISTIYSE cizilir — 8 kopyanin\n"
    "                # tamaminda cizmek 8 kat gereksiz yuktur (kapi: H2g/T248b).\n"
    "                self._harita_ciz()\n"
)

MUTASYONLAR = [
    ("N0 mutasyon yok", [], 0),
    ("N1 urun: tekrar gonderimde cizim YOK (duzeltme oncesi)", [(BLOK, "")], 1),
    ("N2 urun: cizim KOSULSUZ (her tekrarda yeniden ciz)",
     [(BLOK, BLOK.replace("elif rota_yok_temizlendi:", "else:"))], 1),
    # N3 (curutucu KAPSAM KENARI gozlemi): duzeltme `_harita_ciz()`i ARGUMANSIZ
    # cagirdigi icin kamera gorunumundeki KUCUK haritayi da tazeliyor
    # (yks_gui.py:1561-1565). Bu mutasyon tazelemeyi YALNIZ ana tuvale daraltir:
    # ana harita dogru kalir (T248/T248b YESIL), kucuk harita bayat kalir ->
    # yalnizca T248c duser. Yani T248c'nin ayri bir yolu olctugunun kaniti.
    ("N3 urun: tazeleme yalniz ANA tuval (kucuk harita bayat kalir)",
     [(BLOK, BLOK.replace("self._harita_ciz()", "self._harita_ciz(self.harita)"))], 1),
]


def main():
    ham = URUN.read_bytes()
    ozet = hashlib.sha256(ham).hexdigest()
    ss = "\r\n" if b"\r\n" in ham else "\n"
    sonuc = []
    for ad, degs, beklenen in MUTASYONLAR:
        metin = ham
        for eski, yeni in degs:
            e = eski.replace("\n", ss).encode("utf-8")
            y = yeni.replace("\n", ss).encode("utf-8")
            if metin.count(e) != 1:
                raise SystemExit(f"DESEN TEK DEGIL ({ad}): {metin.count(e)}")
            metin = metin.replace(e, y, 1)
        try:
            if metin != ham:
                URUN.write_bytes(metin)
            p = subprocess.run(
                [PY, "-X", "utf8", "-B", "-m", "unittest", "discover",
                 "-s", "tests", "-p", "test_yks_mk15_hakem_ekrani.py", "-v",
                 "-k", "H2g_TekrarliOpenRouteHaritayiTazeler"],
                cwd=str(KOK), capture_output=True, text=True,
                encoding="utf-8", errors="replace")
            kod = p.returncode
            (CIK / f"mutasyon_{ad.split()[0]}.txt").write_text(
                p.stdout + p.stderr, encoding="utf-8")
        finally:
            URUN.write_bytes(ham)
            if hashlib.sha256(URUN.read_bytes()).hexdigest() != ozet:
                raise SystemExit(f"GERI YAZILAMADI {URUN}")
        print(f"{ad}: beklenen={beklenen} gercek={kod}", flush=True)
        sonuc.append((ad, beklenen, kod))
    hepsi = all(b == k for _, b, k in sonuc)
    print("MUTASYON_SONUC", "GECTI" if hepsi else "DUSTU")
    return 0 if hepsi else 1


if __name__ == "__main__":
    raise SystemExit(main())
