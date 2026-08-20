"""NEDEN: T64 arena kaynaklarını gerçek v24 ile ekran ve log kanıtına bağlar.

KESIF MUAFIYETI: GUI/görsel kanıt üreten ELLE araç; çıktısı PNG ve log
  dosyasıdır, assert'i yoktur — otomatik kapıya çevrilemez, GÖZLE okunur.
KOSUM: O:\\navitas-local-train\\venv\\Scripts\\python.exe -B tests/t64_hakem_ekrani_kapisi.py --cikti tests/artifacts/t64

Bu betik karar algoritması kurmaz. ``YksArayuz._algi_kos`` üretim yolunu çağırır,
GUI'nin göstereceği iki paneli PNG'ye ve gerçek sonuç satırlarını UTF-8 loga yazar.
"""

from __future__ import annotations

import argparse
import queue
import sys
from pathlib import Path

import cv2
import numpy as np


KOK = Path(__file__).resolve().parents[1]
for _alt in ("codes", "comms"):
    if str(KOK / _alt) not in sys.path:
        sys.path.insert(0, str(KOK / _alt))

from karar_sozlesmesi import OLCEK_YOK_SEBEBI  # noqa: E402
from yks_gui import YksArayuz  # noqa: E402


ROTA_RENGI_BGR = np.asarray((0, 220, 255), np.uint8)
ARENA_KADRAJ_BEKLENEN_KARE = 260


def _sonuc(arayuz: YksArayuz):
    """Kuyruktaki tek gerçek sonuç paketini döndür; hata/eksikliği yükselt."""
    paketler = list(arayuz.algi_kuyruk.queue)
    hatalar = [p for p in paketler if p[0] == "hata"]
    sonuc = next((p for p in paketler if p[0] == "sonuc"), None)
    if sonuc is None or hatalar:
        raise RuntimeError(f"algı sonucu yok/bozuk: sonuc={sonuc} hata={hatalar}")
    return sonuc


def _kaynagi_kos(arayuz: YksArayuz, kaynak: str):
    """Seçili kaynağın ilk karesini GUI'nin gerçek worker'ında çalıştır."""
    arayuz.algi_kaynak = kaynak
    arayuz.algi_kuyruk = queue.Queue()
    arayuz.algi_mesgul = True
    gorseller = arayuz._algi_gorseller()
    if not gorseller:
        raise RuntimeError(f"kaynak boş: {kaynak}")
    arayuz._algi_kos(gorseller[0])
    return gorseller, _sonuc(arayuz)


def _baslikli(gorsel: np.ndarray, baslik: str) -> np.ndarray:
    """GUI panelinin üstüne yalnız kanıt başlığı ekle."""
    pay = 56
    kart = np.full((gorsel.shape[0] + pay, gorsel.shape[1], 3), 238, np.uint8)
    kart[pay:] = gorsel
    cv2.putText(kart, baslik, (18, 37), cv2.FONT_HERSHEY_SIMPLEX,
                0.85, (25, 25, 25), 2, cv2.LINE_AA)
    return kart


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cikti", type=Path,
                    default=KOK / "tests" / "artifacts" / "t64")
    args = ap.parse_args()

    arayuz = YksArayuz.__new__(YksArayuz)
    arayuz.algi_model = None
    arayuz.algi_kuyruk = queue.Queue()
    arayuz.algi_mesgul = True

    kadraj_yollari, kadraj = _kaynagi_kos(arayuz, "arena_kadraj")
    if len(kadraj_yollari) != ARENA_KADRAJ_BEKLENEN_KARE:
        raise RuntimeError(
            f"arena_kadraj kare sayısı {len(kadraj_yollari)}, "
            f"beklenen {ARENA_KADRAJ_BEKLENEN_KARE}")
    kadraj_yolu = kadraj_yollari[0]
    kadraj_sari = int(np.count_nonzero(np.all(
        kadraj[1] == ROTA_RENGI_BGR, axis=2)))
    if "ROTA YOK" in kadraj[2] or kadraj_sari <= 0:
        raise RuntimeError(
            f"arena_kadraj rota çizmedi: sari={kadraj_sari} bilgi={kadraj[2]}")

    gercek_yollari, gercek = _kaynagi_kos(arayuz, "arena_gercek")
    if len(gercek_yollari) != 1:
        raise RuntimeError(f"arena_gercek kare sayısı {len(gercek_yollari)}, beklenen 1")
    gercek_yolu = gercek_yollari[0]
    gercek_sari = int(np.count_nonzero(np.all(
        gercek[1] == ROTA_RENGI_BGR, axis=2)))
    if (f"ROTA YOK · {OLCEK_YOK_SEBEBI}" not in gercek[2]
            or gercek_sari != 0
            or "segmentasyon maskesi (rota değil)" not in gercek[2]):
        raise RuntimeError(
            f"arena_gercek fail-closed değil: sari={gercek_sari} bilgi={gercek[2]}")

    args.cikti.mkdir(parents=True, exist_ok=True)
    kadraj_karti = _baslikli(kadraj[1], "ARENA KADRAJ - ROTA CIZILDI")
    gercek_karti = _baslikli(gercek[1], "ARENA GERCEK - OLCEK_YOK")
    yukseklik = max(kadraj_karti.shape[0], gercek_karti.shape[0])
    def _uyarla(kart):
        olcek = yukseklik / kart.shape[0]
        return cv2.resize(
            kart, (int(round(kart.shape[1] * olcek)), yukseklik),
            interpolation=cv2.INTER_AREA)
    kadraj_karti, gercek_karti = _uyarla(kadraj_karti), _uyarla(gercek_karti)
    pano = cv2.hconcat((kadraj_karti, gercek_karti))
    ekran = args.cikti / "t64_hakem_ekrani.png"
    log = args.cikti / "t64_hakem_ekrani.log"
    if not cv2.imwrite(str(ekran), pano):
        raise RuntimeError(f"ekran görüntüsü yazılamadı: {ekran}")
    log.write_text(
        f"KAYNAK={kadraj_yolu}\n{kadraj[3]}\n{kadraj[2]}\n\n"
        f"KAYNAK={gercek_yolu}\n{gercek[3]}\n{gercek[2]}\n",
        encoding="utf-8")

    print(f"[T64_ARENA_KADRAJ] kare={len(kadraj_yollari)} | {kadraj[3]} | "
          f"sari_rota_px={kadraj_sari}")
    print(f"[T64_ARENA_GERCEK] {gercek[3]} | "
          f"sari_rota_px={gercek_sari} | maske=GORUNUR")
    print(f"[T64_EKRAN] {ekran}")
    print(f"[T64_LOG] {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
