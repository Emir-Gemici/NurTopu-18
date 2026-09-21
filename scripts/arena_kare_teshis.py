"""Arena karesi teshisi — tek kareden UCUS ONCESI go/no-go (21 Eyl 2026, saha araci).

NEDEN: 20 Eylul oturumunda 4371 karar denemesinin tamami dustu ve sebebin hangi
halkada oldugu ancak ertesi gun cevrimdisi ayristirilabildi (D-524). Halkalar
SIRALIDIR ve onceki halka dusunce sonraki hic denenmez: zemin maskesi 0 piksel
ise `analyze_path` HB bloguna VARMADAN doner (`codes/rpi_inference.py:1534` vs
`:1687`). Bu yuzden sahada "MASKE_YOK goruyorum" demek, HB/olcek tarafinin SAGLAM
oldugu anlamina GELMEZ — yalnizca sira oraya gelmedigi anlamina gelir.

Bu arac zinciri tek karede BASTAN SONA kosar ve her halkanin hukmunu AYRI yazar:

    odak  ->  olcek  ->  HB  ->  model/maske  ->  rota

Boylece bir halka duserse, ondan SONRAKI halkalarin durumu da (mumkun oldugunca)
raporlanir; operator tek duzeltmeden sonra ikinci bir duvara carpmaz.

KULLANIM
    python scripts/arena_kare_teshis.py --dosya kare.jpg --irtifa 30
    python scripts/arena_kare_teshis.py --url http://127.0.0.1:8080/kare.jpg --irtifa 30

CIKIS KODU
    0  zincirin tamami gecti (rota uretildi)
    1  bir halka dustu (hangisi ciktida yazili)
    2  kare okunamadi / arac calistirilamadi

SINIR: Bu arac TESHISTIR, kabul kapisi DEGILDIR. Esik ve sabitlerin tek kaynagi
`codes/karar_sozlesmesi.py`dir (madde 16); burada hicbir esik yeniden tanimlanmaz
ve hicbir karar yolu degistirilmez.
"""

import argparse
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
for yol in (KOK, KOK / "codes"):
    if str(yol) not in sys.path:
        sys.path.insert(0, str(yol))

import cv2
import numpy as np

GECTI = "GECTI"
DUSTU = "DUSTU"
BILINMIYOR = "BILINMIYOR"


def _kareyi_al(dosya, url, zaman_asimi_s):
    if dosya:
        kare = cv2.imread(str(dosya))
        if kare is None:
            raise SystemExit(f"HATA: kare okunamadi: {dosya}")
        return kare, str(dosya)
    import urllib.request
    with urllib.request.urlopen(url, timeout=zaman_asimi_s) as cevap:
        ham = np.frombuffer(cevap.read(), np.uint8)
    kare = cv2.imdecode(ham, cv2.IMREAD_COLOR)
    if kare is None:
        raise SystemExit(f"HATA: koprunun dondurdugu veri cozulemedi: {url}")
    return kare, url


def _satir(ad, hukum, detay):
    isaret = {GECTI: "[OK]  ", DUSTU: "[DUS] ", BILINMIYOR: "[?]   "}[hukum]
    print(f"{isaret}{ad:<26} {detay}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Arena karesinden ucus oncesi zincir teshisi (odak, olcek, HB, maske, rota).")
    kaynak = ap.add_mutually_exclusive_group(required=True)
    kaynak.add_argument("--dosya", help="Yerel kare dosyasi (jpg/png)")
    kaynak.add_argument("--url", help="Kamera koprusu kare adresi (or. http://127.0.0.1:8080/kare.jpg)")
    ap.add_argument("--irtifa", type=float, default=None,
                    help="Kare cekildigi irtifa (m). Olcek BUNDAN turer; verilmezse HB'nin "
                         "boyut ve sekil kapilari ACILMAZ (fail-open uyarisi basilir).")
    ap.add_argument("--fov", type=float, default=54.0,
                    help="Yatay FOV derece (Jetson /etc/navitas.env varsayilani: 54)")
    ap.add_argument("--conf", type=float, default=0.30, help="Model guven esigi (uretim: 0.30)")
    ap.add_argument("--zaman-asimi", type=float, default=5.0, help="--url icin saniye")
    a = ap.parse_args(argv)

    import karar_sozlesmesi as ks
    from kare_keskinligi import kare_keskinligi, keskinlik_bandi, KESKINLIK_NET_ESIK
    import rpi_inference as ri

    kare, kaynak_adi = _kareyi_al(a.dosya, a.url, a.zaman_asimi)
    h_px, w_px = kare.shape[:2]
    print(f"kare  : {kaynak_adi}  ({w_px}x{h_px})")
    print(f"ayar  : irtifa={a.irtifa if a.irtifa is not None else 'YOK'} m · fov={a.fov}° · conf={a.conf}")
    print("-" * 78)

    dusenler = []

    # ── HALKA 1: ODAK ────────────────────────────────────────────────────────
    keskinlik = kare_keskinligi(kare)
    band = keskinlik_bandi(keskinlik)
    odak_ok = band == "NET"
    _satir("1. odak", GECTI if odak_ok else DUSTU,
           f"keskinlik {keskinlik:.1f} → {band}  (NET esigi {KESKINLIK_NET_ESIK:.0f})")
    if not odak_ok:
        dusenler.append("odak")
        print("        → lens halkasini cevirip TEPE degeri ara; bulanik karede model "
              "zemini kaybedip kareyi ENGEL sayar (ONARIM-04).")

    # ── HALKA 2: OLCEK ───────────────────────────────────────────────────────
    mpp = None
    if a.irtifa is not None:
        mpp = ks.mpp_irtifadan(a.irtifa, w_px, yatay_fov_derece=a.fov)
    if mpp is None:
        _satir("2. olcek (mpp)", BILINMIYOR, "irtifa verilmedi ya da turetilemedi")
        print("        → HB'nin BOYUT ve SEKIL kapilari acilmaz; kirmizi herhangi bir "
              "cisim hedef sanilabilir (D-351).")
    else:
        _satir("2. olcek (mpp)", GECTI,
               f"{mpp:.5f} m/px · kare zemini {mpp*w_px:.1f} x {mpp*h_px:.1f} m · "
               f"HB 2 m = {ks.HB_KENAR_M/mpp:.0f} px")

    # ── HALKA 3: HB (varis bolgesi) ──────────────────────────────────────────
    sq, small, icerik = ri._preprocess(kare)
    sekil_esigi = ks.HB_SEKIL_ESIGI if mpp is not None else None
    hb = ks.hb_konumu(sq, mpp=mpp, sekil_esigi=sekil_esigi)
    if hb is None:
        gevsek = ks.hb_konumu(sq, mpp=None, sekil_esigi=None)
        if gevsek is None:
            _satir("3. HB (kirmizi H)", DUSTU, "kadrajda kirmizi aday YOK")
            print("        → HB kadraja girmeden rota URETILMEZ (rpi_inference.py:1696). "
                  "Ya kadraj HB'yi kapsamiyor ya ped cok solmus.")
        else:
            _satir("3. HB (kirmizi H)", DUSTU,
                   f"aday VAR ama kapidan gecmedi · kenar {gevsek['kenar_px']:.1f} px"
                   + (f" · sekil {gevsek.get('sekil_puani', float('nan')):.3f}"
                      if gevsek.get("sekil_puani") is not None else ""))
            if mpp is not None:
                alt, ust = ks.HB_OLCEK_BANDI
                bekl = ks.HB_KENAR_M / mpp
                print(f"        → boyut bandi {alt*bekl:.1f}–{ust*bekl:.1f} px bekliyor "
                      f"(ped 2,00 m varsayimi). Ped gercekten 2 m mi, irtifa dogru mu?")
            print(f"        → sekil esigi {ks.HB_SEKIL_ESIGI:.5f}; ped solduysa tespit "
                  "UCURUMDAN duser (D-524 ek 2, %50 → %60 arasi).")
        dusenler.append("HB")
    else:
        detay = f"bulundu · kutu {hb['kutu']} · kenar {hb['kenar_px']:.1f} px"
        if hb.get("sekil_puani") is not None:
            detay += f" · sekil {hb['sekil_puani']:.3f} (esik {ks.HB_SEKIL_ESIGI:.3f})"
        _satir("3. HB (kirmizi H)", GECTI, detay)

    # ── HALKA 4: MODEL / MASKE ───────────────────────────────────────────────
    model = ri.load_model()
    sonuc = model.predict(small, imgsz=ri.INFER_SIZE, conf=a.conf, verbose=False)
    maskeler = ri.get_masks(sonuc, sq.shape[0], sq.shape[1])
    ri._maskeleri_icerige_kirp(maskeler, icerik)
    zemin, engel = maskeler[0], maskeler[1]
    ic_px = icerik[2] * icerik[3]
    zemin_px = int(np.count_nonzero(zemin))
    engel_px = int(np.count_nonzero(engel))
    maske_ok = zemin_px > 0
    _satir("4. maske (v36)", GECTI if maske_ok else DUSTU,
           f"zemin {zemin_px} px (%{100*zemin_px/ic_px:.2f}) · "
           f"engel {engel_px} px (%{100*engel_px/ic_px:.2f})")
    if not maske_ok:
        dusenler.append("maske")
        print("        → zemin 0 piksel: karar MASKE_YOK olur ve sonraki halkalar HIC "
              "denenmez. Once odak, sonra bu satir.")

    # ── HALKA 5: ROTA (URETIM cagri bicimi) ──────────────────────────────────
    yol, guven, waypointler, ret, _olcum = ri.analyze_path(
        zemin, icerik=icerik, engel_mask=engel, mpp=mpp,
        return_reason=True, return_olcum=True, goruntu=sq)
    sebep = ret[0] if isinstance(ret, tuple) else ret
    rota_var = ret is None and yol is not None and len(waypointler) >= 2
    _satir("5. rota (uretim yolu)", GECTI if rota_var else DUSTU,
           (f"serit {yol} · guven {guven:.3f} · {len(waypointler)} waypoint"
            if rota_var else f"red: {sebep}"))
    if not rota_var:
        dusenler.append("rota")
        if isinstance(ret, tuple) and len(ret) > 1:
            print(f"        → {ret[1]}")

    print("-" * 78)
    if not dusenler:
        print("HUKUM: zincirin tamami GECTI — bu kareden rota uretiliyor.")
        return 0
    print(f"HUKUM: DUSTU — ilk kopan halka: {dusenler[0]}  (tumu: {', '.join(dusenler)})")
    print("NOT  : halkalar siralidir; onceki duzeltilmeden sonrakinin hukmu kesin degildir.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as exc:  # arac sahada calisiyor: sessiz olme
        print(f"HATA: teshis kosulamadi: {type(exc).__name__}: {exc}")
        sys.exit(2)
