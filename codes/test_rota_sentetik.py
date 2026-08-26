"""KORIDOR SECIMI DOGRULAMASI — sentetik, KUSURSUZ maske, 15 belirlenimci durum.

NEDEN SENTETIK: otopark verisinde 3 guzergah yok, bu yuzden sol/orta/sag kararini
DOGRULAYAMAZ. simulation/scripts/arena.py TAM yer gercegini zaten uretiyor:
harita(id, senaryo) -> 3 yol poligonu + KB + HB + "open" (GIZLI cevap), 5 harita
x 3 senaryo = 15 deterministik saha.

Yollar ve bariyerler PIKSEL PIKSEL rasterlestirilip costmap_path_finder.rota_bul()
kusursuz maskeyle sinanir. 15/15 dogru olmali — kusursuz maskede hata varsa bu
MANTIK hatasidir, algi (model) hatasi degil.

Sonra kademeli bozulma taramasi: bariyer piksellerinin bir kismi silinir (model
kacirdigini simule eder), kararin hangi noktada dondugu olculur — modelin GERCEK
recall gereksinimi boylece TURETILIR, varsayilmaz.

🔴 IKI KOL (T156 · 2026-08-26 · CONTRACTS SS11.2-EK / ON_KAYIT SS18-B)
  Bu kapi 2026-08-26'ya kadar YALNIZ `costmap_path_finder.rota_bul`u zorluyordu.
  Ama URETIM yolu `rpi_inference.analyze_path`tir (D-295): Jetson/RPi cikarim
  hatti, `comms` yayini ve YKS etiketi oradan gelir. Yani genel kapi, sartname
  SS2.1 topolojisinde (uc guzergahtan biri acik) URETIM yolunu HIC sinamiyordu —
  T155 (D-296) tam bu delikten girdi: uretim yolu 15 sahnenin 9'unda YANLIS
  serit numarasi yayinlarken kapi 15/15 yesil yaniyordu.
  Bu yuzden ayni 15 belirlenimci sahne artik IKI kolda kosulur:
    KOL 1 (tanisal) `rota_bul`      — 15/15 sart (degismedi, madde 14)
    KOL 2 (URETIM)  `analyze_path`  — rota URETILIYOR mu + YAYINLANAN serit
                                      yer gercegiyle uyusuyor mu; esik
                                      >= 14/15 (ON_KAYIT SS18-B, taban 15/15)
  Cikis kodu IKI kolun birlikte gecmesine baglidir; "SONUC: n/n dogru" satiri
  ve "[OK] TUM DETERMINISTIK SAHNELER GECTI" cumlesi KOL 1'in ciktisi olarak
  AYNEN durur (baska betikler bu metni okuyor olabilir).

Kullanim:
  venv/Scripts/python.exe codes/test_rota_sentetik.py
  venv/Scripts/python.exe codes/test_rota_sentetik.py --bozulma
"""
import argparse
import sys
import zlib
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "simulation" / "scripts"))

from costmap_path_finder import rota_bul, olcek_px
import arena
from world_generator import DIFF

MPP = 0.10                 # 10 cm/piksel — HTAB 50x50 m -> 500x500 px canvas yeter
EKSTENT_M = 25.0           # local koordinat yarisi (HTAB_HALF ile ayni)
N = int(round(2 * EKSTENT_M / MPP))   # 500

# T156 — URETIM YOLU KOLUNUN KAPI ESIGI (ON_KAYIT SS18-B, SONUCA GORE
# DEGISTIRILMEZ). 15 sahnenin en az bu kadarinda hem rota URETILECEK hem de
# YAYINLANAN serit yer gercegiyle uyusacak. Olculen taban 15/15'tir
# (results/t156/rapor.md); esik T155 SS17 disipliniyle ayni: >= 14.
URETIM_KAPI_ESIGI = 14


def _px(local_xy):
    x, y = local_xy
    col = int(round((x + EKSTENT_M) / MPP))
    row = int(round((EKSTENT_M - y) / MPP))   # KUZEY YUKARI (bottom->top ile tutarli)
    return col, row


def _daire(mask, merkez_local, yaricap_m):
    cx, cy = _px(merkez_local)
    r = max(1, int(round(yaricap_m / MPP)))
    cv2.circle(mask, (cx, cy), r, 1, -1)


def _tohum_merkezi(mask):
    """Costmap'in fiziksel KB/HB ankora sabitlemesi icin beklenen piksel."""
    dt = cv2.distanceTransform(mask.astype(np.uint8), cv2.DIST_L2,
                               cv2.DIST_MASK_PRECISE)
    y, x = np.unravel_index(int(np.argmax(dt)), dt.shape)
    return int(x), int(y)


def sahne_uret(harita_id, scenario, moloz_orani=1.0):
    """H, zemin, engel, baslangic, hedef dondurur.
    moloz_orani < 1.0 ise bariyer pikselleri kismen silinir (bozulma taramasi)."""
    H = arena.harita(harita_id, scenario)
    lane_w = DIFF[scenario]["lane_w"]

    zemin = np.zeros((N, N), np.uint8)
    for road in (1, 2, 3):
        pts = np.array([_px(p) for p in H["paths"][road]], dtype=np.int32)
        kalinlik = max(1, int(round(lane_w / MPP)))
        cv2.polylines(zemin, [pts], False, 1, thickness=kalinlik, lineType=cv2.LINE_8)

    engel = np.zeros((N, N), np.uint8)
    # Python'in hash tuzu surecler arasinda degisir; bozulma testi gercekten
    # deterministik olsun diye sabit bir CRC tabanli tohum kullan.
    seed = zlib.crc32(f"{harita_id}:{scenario}".encode("utf-8"))
    rng = np.random.RandomState(seed)
    for road in (1, 2, 3):
        if road == H["open"]:
            continue
        path = H["paths"][road]
        bi = int(len(path) * 0.40)
        (bx, by), (nx, ny) = path[bi], path[min(bi + 1, len(path) - 1)]
        yon = np.array([nx - bx, ny - by])
        if np.linalg.norm(yon) < 1e-6:
            yon = np.array([0.0, 1.0])
        yon = yon / np.linalg.norm(yon)
        normal = np.array([-yon[1], yon[0]])   # yola DIK

        yari_genislik = (lane_w + 1.0) / 2.0
        p1 = (bx + normal[0] * yari_genislik, by + normal[1] * yari_genislik)
        p2 = (bx - normal[0] * yari_genislik, by - normal[1] * yari_genislik)
        px1, px2 = _px(p1), _px(p2)
        kalinlik_engel = max(1, int(round(1.5 / MPP)))   # bariyer boyu ekseninde ~1.5 m
        tekli_engel = np.zeros((N, N), np.uint8)
        cv2.line(tekli_engel, px1, px2, 1, thickness=kalinlik_engel)

        if moloz_orani < 1.0:
            ys, xs = np.nonzero(tekli_engel)
            n_sil = int(len(ys) * (1.0 - moloz_orani))
            if n_sil > 0:
                idx = rng.choice(len(ys), size=n_sil, replace=False)
                tekli_engel[ys[idx], xs[idx]] = 0

        engel = np.maximum(engel, tekli_engel)

    baslangic = np.zeros((N, N), np.uint8)
    hedef = np.zeros((N, N), np.uint8)
    _daire(baslangic, H["kb"], 1.5)
    _daire(hedef, H["hb"], 1.5)

    return H, zemin, engel, baslangic, hedef


def uretim_yolu_kolu():
    """KOL 2 — URETIM yolu (`rpi_inference.analyze_path`) ayni 15 sahnede.

    NEDEN AYRI FONKSIYON: `tests/test_t156_genel_kapi_uretim_kolu.py` kapinin
    KENDISINI bu fonksiyondan sinar; sahne ve olcu KOPYALANMAZ (kopya, sahne
    degisince testi sessizce alakasiz kilardi — D-15).

    `analyze_path` import'u ICERIDE yapilir: modul `ultralytics`i cekiyor ve bu
    dosyayi yalnizca `sahne_uret` icin import eden betikler (tests/,
    scripts/olcum/124_...) o bedeli odememeli.

    Her sahne icin doner:
      rota_var   : ret YOK, karar URETILDI ve >= 2 waypoint yayina hazir
      serit_ok   : rota_var VE yayinlanan `road` == yer gercegi H["open"]
    """
    from rpi_inference import analyze_path

    satirlar = []
    for harita_id in range(1, arena.HARITA_N + 1):
        for scenario in arena.SCENARIOS:
            H, zemin, engel, _b, _h = sahne_uret(harita_id, scenario)
            # Cagri T151/T155 ile BIREBIR ayni (results/t155/serit_kapisi.py):
            # baslangic/hedef maskeleri VERILMEZ — uretim yolu uc bantlarini
            # maskenin kendisinden turetir, kapi da onu oyle zorlamalidir.
            yol, guven, wps, ret, olcum = analyze_path(
                zemin, icerik=None, engel_mask=engel, mpp=MPP,
                return_reason=True, return_olcum=True)
            rota_var = ret is None and yol is not None and len(wps) >= 2
            satirlar.append({
                "harita": harita_id,
                "senaryo": scenario,
                "yer_gercegi": int(H["open"]),
                "yayinlanan_road": yol,
                "guven": float(guven),
                "wp": len(wps),
                "ret": (ret[0] if isinstance(ret, tuple) else ret),
                "rota_var": bool(rota_var),
                "serit_ok": bool(rota_var and yol == H["open"]),
                # TANI (kapiya girmez): T155 oncesi YAYINLANAN alan buydu.
                "tani_darbogaz_serit": (olcum or {}).get("darbogaz_serit"),
            })
    return satirlar


def uretim_kolu_sayimi(satirlar):
    """(rota_dogru, serit_dogru, toplam) — kapi bu uc sayidan karar verir."""
    return (sum(1 for s in satirlar if s["rota_var"]),
            sum(1 for s in satirlar if s["serit_ok"]),
            len(satirlar))


def kapi_karari(kol1_dogru, kol1_toplam, uretim_rota, uretim_serit,
                uretim_toplam):
    """Kapinin CIKIS KODU — tek yerde tanimli (madde 16).

    KOL 1 (`rota_bul`) sozlesmesi DEGISMEDI: tam puan sart.
    KOL 2 (`analyze_path`) ON_KAYIT SS18-B: rota uretimi ve serit numarasi
    AYRI AYRI >= URETIM_KAPI_ESIGI olmali.
    0 = gecti, 1 = dustu.
    """
    kol1_ok = kol1_toplam > 0 and kol1_dogru == kol1_toplam
    kol2_ok = (uretim_toplam > 0
               and uretim_rota >= URETIM_KAPI_ESIGI
               and uretim_serit >= URETIM_KAPI_ESIGI)
    return 0 if (kol1_ok and kol2_ok) else 1


def _uretim_kolunu_yazdir(satirlar):
    """KOL 2 tablosunu basar ve (rota_dogru, serit_dogru, toplam) dondurur."""
    print("\n" + "=" * 78)
    print("KOL 2 — URETIM YOLU (rpi_inference.analyze_path) · AYNI 15 SAHNE")
    print("=" * 78)
    print(f"{'harita':>6} {'senaryo':>8} {'gercek':>7} {'yayin':>7} {'guven':>6} "
          f"{'wp':>4} {'ret':>16} {'darbogaz':>9}  sonuc")
    for s in satirlar:
        if s["rota_var"] and s["serit_ok"]:
            sonuc = "OK"
        elif not s["rota_var"]:
            sonuc = "FAIL(rota)"
        else:
            sonuc = "FAIL(serit)"
        print(f"{s['harita']:>6} {s['senaryo']:>8} {s['yer_gercegi']:>7} "
              f"{str(s['yayinlanan_road']):>7} {s['guven']:>6.3f} {s['wp']:>4} "
              f"{str(s['ret']):>16} {str(s['tani_darbogaz_serit']):>9}  {sonuc}")
    rota_dogru, serit_dogru, toplam = uretim_kolu_sayimi(satirlar)
    print("-" * 78)
    print(f"URETIM YOLU: rota uretimi {rota_dogru}/{toplam} · "
          f"yayinlanan serit {serit_dogru}/{toplam} "
          f"(esik >= {URETIM_KAPI_ESIGI}/{toplam}, ON_KAYIT SS18-B)")
    if rota_dogru >= URETIM_KAPI_ESIGI and serit_dogru >= URETIM_KAPI_ESIGI:
        print("[OK] URETIM YOLU KOLU GECTI")
    else:
        print("[FAIL] URETIM YOLU KOLU DUSTU — uretimde yayinlanan karar "
              "yer gercegiyle uyusmuyor")
    return rota_dogru, serit_dogru, toplam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bozulma", action="store_true",
                    help="bariyer piksellerini kademeli sil, karar nerede doner olc")
    ap.add_argument("--gorsel", action="store_true", help="basarisiz sahnelerin gorselini yaz")
    args = ap.parse_args()

    print("=" * 78)
    print("KORIDOR SECIMI — 15 DETERMINISTIK SENTETIK SAHNE (kusursuz maske)")
    print("=" * 78)
    print("KOL 1 — TANISAL YOL (costmap_path_finder.rota_bul) · sart: TAM PUAN")
    print(f"{'harita':>6} {'senaryo':>8} {'gercek':>7} {'tahmin':>7} {'guven':>6} "
          f"{'durum':>18} {'wp':>4}  sonuc")

    dogru = 0
    toplam = 0
    basarisizlar = []
    for harita_id in range(1, arena.HARITA_N + 1):
        for scenario in arena.SCENARIOS:
            H, zemin, engel, baslangic, hedef = sahne_uret(harita_id, scenario)
            cikti = rota_bul({0: zemin, 1: engel}, mpp=MPP,
                              baslangic=baslangic, hedef=hedef, plan=True)
            toplam += 1
            waypoints = cikti["waypoints_px"]
            baslangic_ankor = _tohum_merkezi(baslangic)
            hedef_ankor = _tohum_merkezi(hedef)
            en_uzun_adim_px = max(
                (float(np.hypot(x2 - x1, y2 - y1))
                 for (x1, y1), (x2, y2) in zip(waypoints, waypoints[1:])),
                default=0.0,
            )
            rota_ok = (
                cikti["durum"] == "ACIK"
                and len(waypoints) >= 2
                and not cikti["ihlaller"]
                and en_uzun_adim_px <= olcek_px(MPP)["wp_aralik_px"] + 1.0
                and tuple(waypoints[0]) == baslangic_ankor
                and tuple(waypoints[-1]) == hedef_ankor
            )
            ok = cikti["yol_no"] == H["open"] and rota_ok
            dogru += int(ok)
            print(f"{harita_id:>6} {scenario:>8} {H['open']:>7} "
                  f"{str(cikti['yol_no']):>7} {cikti['guven']:>6.3f} "
                  f"{cikti['durum']:>18} {len(waypoints):>4}  {'OK' if ok else 'FAIL'}")
            if not ok:
                basarisizlar.append((harita_id, scenario, H, cikti, zemin, engel))

    print("-" * 78)
    print(f"SONUC: {dogru}/{toplam} dogru")
    if dogru == toplam:
        print("[OK] TUM DETERMINISTIK SAHNELER GECTI")
    else:
        print(f"[FAIL] {toplam - dogru} sahne basarisiz — bu bir MANTIK hatasidir (kusursuz maske)")

    # T156 — KOL 2: URETIM yolu ayni sahnelerde zorlanir (CONTRACTS SS11.2-EK).
    uretim_satirlari = uretim_yolu_kolu()
    uretim_rota, uretim_serit, uretim_toplam = _uretim_kolunu_yazdir(
        uretim_satirlari)
    kod = kapi_karari(dogru, toplam, uretim_rota, uretim_serit, uretim_toplam)
    print("-" * 78)
    print(f"GENEL KAPI (madde 14): {'GECTI' if kod == 0 else 'DUSTU'} — "
          f"kol1 {dogru}/{toplam} · kol2 serit {uretim_serit}/{uretim_toplam}")

    if args.gorsel and basarisizlar:
        cikti_dir = Path(__file__).parent.parent / "results" / "test_rota_sentetik"
        cikti_dir.mkdir(parents=True, exist_ok=True)
        for harita_id, scenario, H, cikti, zemin, engel in basarisizlar:
            vis = np.zeros((N, N, 3), np.uint8)
            vis[zemin > 0] = (60, 60, 60)
            vis[engel > 0] = (0, 0, 220)
            for road in (1, 2, 3):
                renk = (0, 220, 0) if road == H["open"] else (0, 0, 0)
                pts = np.array([_px(p) for p in H["paths"][road]], np.int32)
                cv2.polylines(vis, [pts], False, renk, 1)
            cv2.putText(vis, f"gercek={H['open']} tahmin={cikti['yol_no']} {cikti['durum']}",
                       (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            yol = cikti_dir / f"harita{harita_id}_{scenario}.jpg"
            cv2.imwrite(str(yol), vis)
        print(f"\nBasarisiz sahne gorselleri: {cikti_dir}")

    if args.bozulma:
        print("\n" + "=" * 78)
        print("BOZULMA TARAMASI — bariyer pikselleri kademeli silinirken karar")
        print("=" * 78)
        oranlar = [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]
        print(f"{'moloz%':>7} {'dogru/toplam':>14} {'oran':>7}")
        for oran in oranlar:
            d, t = 0, 0
            for harita_id in range(1, arena.HARITA_N + 1):
                for scenario in arena.SCENARIOS:
                    H, zemin, engel, baslangic, hedef = sahne_uret(harita_id, scenario, oran)
                    cikti = rota_bul({0: zemin, 1: engel}, mpp=MPP,
                                     baslangic=baslangic, hedef=hedef, plan=False)
                    t += 1
                    d += int(cikti["yol_no"] == H["open"])
            print(f"{oran * 100:>6.0f}% {d:>6}/{t:<6}     {d / t:>6.2f}")
        print("\nYORUM: oran dustukce dogruluk NEREDE cokuyorsa, modelin bariyeri")
        print("gormesi gereken GERCEK recall esigi budur — varsayim degil, olcum.")

    return kod


if __name__ == "__main__":
    sys.exit(main())
