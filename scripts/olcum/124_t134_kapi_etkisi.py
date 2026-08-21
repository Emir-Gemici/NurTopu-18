"""T134 ADIM 1 — kapi `rota_bul` icine konsaydi NE REDDEDILIRDI? (kod DEGISTIRMEDEN)

🔴 SIRA BAGLAYICI (gorev emri): OLC -> YER SEC -> UYGULA. Bu betik ADIM 1'dir
ve HICBIR SEY DEGISTIRMEZ; yalnizca uretimin KENDI kapi fonksiyonunu
(`karar_sozlesmesi.zemin_maskesi_reddi`) ICE AKTARIP her cagri yerinin
maskesine uygular ve "kapi konsaydi ne olurdu" sorusunu SAYIYLA cevaplar.

OLCULEN CAGRI YERLERI:
  1. `codes/test_rota_sentetik.py` — 🔴 GENEL KAPI (15/15). `rota_bul`u
     DOGRUDAN cagirir (:134, :196) ve `icerik` GECMEZ (tuval = icerik).
     Kapi (b) buraya da uygulanirdi. Sahneler `sahne_uret()` ile birebir
     yeniden kurulur — testin KENDI ureticisi ice aktarilir, kopyalanmaz.
  2. `codes/test_rota_guvenlik.py` sahneleri (varsa ayni yontemle).

⚠ Kabul zinciri (K1..K5) BU OLCUMUN DISINDADIR ve bu bir BULGUDUR:
`61_rota_moloza_basma.py:96` · `63_bariyer_kesisimi.py:71` ·
`66_k5_bariyer_populasyon.py:141` UCU DE `analyze_path` cagirir, `rota_bul`
DEGIL. Yani kabul zinciri kapidan ZATEN geciyor ve (b) onu DEGISTIRMEZ.

CIKTI: results/t134/kapi_etkisi.json
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[2]
CIKTI = KOK / "results" / "t134"


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):
        pass

    sys.path.insert(0, str(KOK / "codes"))
    sys.path.insert(0, str(KOK / "simulation" / "scripts"))
    from karar_sozlesmesi import (ZEMIN_KAPLAMA_TAVANI,          # noqa: E402
                                  ZEMIN_KENAR_DAYANMA_TAVANI,
                                  zemin_kaplamasi, zemin_kenar_dayanmasi,
                                  zemin_maskesi_reddi)
    import test_rota_sentetik as T                                # noqa: E402
    import arena                                                  # noqa: E402

    print(f"tavanlar: kaplama {ZEMIN_KAPLAMA_TAVANI} · "
          f"kenar {ZEMIN_KENAR_DAYANMA_TAVANI}   (OKUNDU, degistirilmedi)")
    print(f"sahne kaynagi: codes/test_rota_sentetik.sahne_uret "
          f"(ICE AKTARILDI) · harita {arena.HARITA_N} × senaryo "
          f"{len(arena.SCENARIOS)}\n")

    satirlar = []
    for harita_id in range(1, arena.HARITA_N + 1):
        for senaryo in arena.SCENARIOS:
            _H, zemin, engel, _b, _h = T.sahne_uret(harita_id, senaryo)
            # 🔴 test `icerik` GECMIYOR -> tuval = icerik (rota_bul varsayilani)
            kaplama = zemin_kaplamasi(zemin > 0, None)
            kenar = zemin_kenar_dayanmasi(zemin > 0, None)
            red = zemin_maskesi_reddi(zemin > 0, None)
            satirlar.append({
                "sahne": f"harita{harita_id}/{senaryo}",
                "kaplama_icerik": kaplama, "kenar_dayanmasi": kenar,
                "reddedilir": red is not None,
                "sebep": (red[0] if red else None),
            })

    red_sayisi = sum(1 for s in satirlar if s["reddedilir"])
    kaps = [s["kaplama_icerik"] for s in satirlar]
    kenarlar = [s["kenar_dayanmasi"] for s in satirlar]

    print(f"{'sahne':22s} {'kaplama':>9s} {'kenar':>8s}  kapi")
    for s in satirlar:
        print(f"{s['sahne']:22s} {s['kaplama_icerik']:9.4f} "
              f"{s['kenar_dayanmasi']:8.4f}  "
              f"{'REDDEDER' if s['reddedilir'] else 'gecirir'}")
    print(f"\nGENEL KAPI (15/15) sahnelerinde REDDEDILEN: {red_sayisi}/{len(satirlar)}")
    print(f"kaplama: min {min(kaps):.4f} · maks {max(kaps):.4f} "
          f"(tavan {ZEMIN_KAPLAMA_TAVANI})")
    print(f"kenar  : min {min(kenarlar):.4f} · maks {max(kenarlar):.4f} "
          f"(tavan {ZEMIN_KENAR_DAYANMA_TAVANI})")
    pay_k = ZEMIN_KAPLAMA_TAVANI - max(kaps)
    pay_e = ZEMIN_KENAR_DAYANMA_TAVANI - max(kenarlar)
    print(f"PAY    : kaplama {pay_k:+.4f} · kenar {pay_e:+.4f}  "
          f"(ret icin IKISI DE asilmali)")

    CIKTI.mkdir(parents=True, exist_ok=True)
    io.open(CIKTI / "kapi_etkisi.json", "w", encoding="utf-8").write(
        json.dumps({
            "_ne": "T134 ADIM 1 · kapi rota_bul'a konsaydi ne reddedilirdi",
            "_tavanlar": {"kaplama": ZEMIN_KAPLAMA_TAVANI,
                           "kenar": ZEMIN_KENAR_DAYANMA_TAVANI},
            "_not": ("Kabul zinciri (K1..K5) BU OLCUMUN DISINDA: 61/63/66 ucu de "
                      "analyze_path cagirir, rota_bul DEGIL — kapidan zaten geciyor."),
            "genel_kapi_sahneleri": satirlar,
            "reddedilen": red_sayisi, "toplam": len(satirlar),
        }, ensure_ascii=False, indent=1))
    print(f"\nyazildi: {CIKTI / 'kapi_etkisi.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
