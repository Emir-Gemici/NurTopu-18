"""Kaynak DUSUNCE (acik-> kopmus) yeniden acma: A koprusu (dosya) -> B koprusu (URL=A/video).
A kapatilir: B kopmayi gorur mu, 1 s'de bir yeniden dener mi (CPU sicak dongu mu), /durum ne der;
A ayni portta geri gelince B kendiliginden acilir mi."""
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ortak import kk, cv2, sahte_avi, kopru, bekle, durum, http_kod  # noqa: E402


def cpu_olc(sure_s):
    c0, t0 = time.process_time(), time.monotonic()
    time.sleep(sure_s)
    return (time.process_time() - c0) / (time.monotonic() - t0)


def main():
    dizin = tempfile.TemporaryDirectory()
    avi = sahte_avi(dizin.name)
    A, uA, portA, logA = kopru(avi, fps_tavani=10.0)
    assert bekle(lambda: durum(portA)["kare_sayaci"] >= 1)
    B, uB, portB, logB = kopru(kk.video_url(portA), fps_tavani=10.0)
    print("A port", portA, "B port", portB, "B kaynak_turu", uB.kaynak_turu, "api", uB.kaynak_api)
    assert bekle(lambda: durum(portB)["kare_sayaci"] >= 5, 10.0), durum(portB)
    print("B acikken durum:", durum(portB))
    print("bos yuk CPU orani (A+B akarken, 2 s): %.3f" % cpu_olc(2.0))

    # --- A'yi kapat: B'nin kaynagi KOPAR ---
    t_kes = time.monotonic()
    kk.kopru_kapat(A, uA)
    print("\nA kapatildi t=0")
    ok = bekle(lambda: not durum(portB)["kaynak_acik"], 10.0)
    t_gordu = time.monotonic() - t_kes
    d = durum(portB)
    print("B kopmayi gordu=%s, %.2f s sonra; durum: %s" % (ok, t_gordu, d))
    fps_kopmus_sonra = d["fps"]
    deneme0 = d["acma_denemesi"]
    t0 = time.monotonic()
    oran = cpu_olc(5.0)
    d = durum(portB)
    print("5 s yeniden acma dongusu: acma_denemesi %d -> %d (%.1f/s) CPU orani %.3f" % (
        deneme0, d["acma_denemesi"], (d["acma_denemesi"] - deneme0) / (time.monotonic() - t0), oran))
    print("kopmus haldeyken /durum fps=%r son_kare_yasi_s=%r son_hata=%r kaynak_acik=%r" % (
        d["fps"], d["son_kare_yasi_s"], d["son_hata"], d["kaynak_acik"]))
    kod_v = http_kod(portB, "/video")[0]
    kod_k = http_kod(portB, "/kare.jpg")[0]
    print("kopmus haldeyken /video=%d /kare.jpg=%d" % (kod_v, kod_k))
    kirmizi = [(round(t - t_kes, 2), m) for t, k, m in logB if k]
    print("B KIRMIZI loglar (t rel A kapanis):", kirmizi[:6], "... toplam", len(kirmizi))

    # --- A ayni portta geri gelir ---
    A2, uA2, portA2, _ = kopru(avi, port=portA, fps_tavani=10.0)
    assert portA2 == portA
    t_geri = time.monotonic()
    ok = bekle(lambda: durum(portB)["kaynak_acik"] and durum(portB)["kare_sayaci"] > 5, 12.0)
    d = durum(portB)
    print("\nA geri geldi; B yeniden acildi=%s %.2f s sonra; acma_sayisi=%d acma_denemesi=%d kare=%d son_hata=%r" % (
        ok, time.monotonic() - t_geri, d["acma_sayisi"], d["acma_denemesi"], d["kare_sayaci"], d["son_hata"]))
    c = cv2.VideoCapture(kk.video_url(portB))
    okunan = sum(1 for _ in range(5) if c.read()[0])
    c.release()
    print("B'den cv2 ile %d/5 kare" % okunan)
    print("ACILDI loglari:", [m for _, k, m in logB if not k and "ACILDI" in m])

    # --- akan istemci varken kopus: istemci akisi kapanir mi (5 s), sonra tekrar baglanir mi ---
    c = cv2.VideoCapture(kk.video_url(portB)); assert c.isOpened()
    for _ in range(3): c.read()
    t_kes2 = time.monotonic()
    kk.kopru_kapat(A2, uA2)
    dusen = 0
    while dusen < 3 and time.monotonic() - t_kes2 < 15:
        ok, _ = c.read()
        if not ok:
            dusen += 1
    print("\nakan istemci: A tekrar kapatildi, cv2 read %d ardisik False, %.2f s sonra" % (dusen, time.monotonic() - t_kes2))
    c.release()
    print("B istemci_sayisi:", durum(portB)["istemci_sayisi"], "kaynak_acik:", durum(portB)["kaynak_acik"])
    print("B akis KIRMIZI:", [m for _, k, m in logB if k and "akis" in m][-2:])
    kk.kopru_kapat(B, uB)
    dizin.cleanup()

    # --- hic acilmayan kaynak: CPU ---
    C, uC, portC, logC = kopru(Path(dizin.name if False else tempfile.gettempdir()) / "yok_yok.avi")
    time.sleep(1.0)
    d0 = durum(portC)["acma_denemesi"]
    oran = cpu_olc(4.0)
    d1 = durum(portC)["acma_denemesi"]
    print("\nhic acilmayan dosya: 4 s'de deneme %d -> %d, CPU orani %.3f" % (d0, d1, oran))
    kk.kopru_kapat(C, uC)


if __name__ == "__main__":
    main()
