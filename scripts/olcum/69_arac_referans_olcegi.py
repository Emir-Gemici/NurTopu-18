"""OLCEK KAHINI — telemetri YOKKEN sahnedeki ARACtan metre/piksel cikar.

NEDEN. Otopark karelerinde rota HIC uretilmiyor ve sebebi cati degil OLCEK
YOKLUGUDUR (D-118 + mimar olcumu): `ölçek YOK (drone kumesinde telemetri/olcek
yok — irtifa+FOV bilinmiyor) · C-uzayi UYGULANAMADI`. Olcek bilinmezse iki
arac arasindaki bosluğun 1,1 m mi 30 cm mi oldugu bilinemez; IKA'nin sigip
sigmadigi hesaplanamiyorken cizilen rota kumar olur ve sistem — dogru olarak —
reddeder.

Bu karelerde olcek USTVERIDEN gelemez: WhatsApp videolarindan cikarilmislar ve
EXIF alan sayisi **0** (olculdu). Geriye tek yol kalir: SAHNEDE BOYUTU BILINEN
NESNE.

Otoparkta yuzlerce arac var. Proje araç kahini olarak K-6'da DOTA OBB'yi
secmisti (ayni fotografta COCO 2 arac, DOTA OBB 93 arac). YONLU kutunun KISA
kenari, tepeden bakista aracin GENISLIGIDIR.

    mpp = ARAC_GENISLIGI_M / (kisa kenar, piksel)

BU BETIK OLCER, KARAR VERMEZ. Sorulan tek sey: dagilim, kullanilabilir bir
olcek verecek kadar dar mi? Genis cikarsa bu yol KAPANIR ve boyle yazilir.

⚠ Bu bir YEDEK olcek kaynagidir. Arenada arac YOKTUR ve orada olcek
TELEMETRIDEN gelir (D-98/T69). Telemetri varsa bu kahin ASLA devreye girmemeli.
"""
import argparse
import json
from pathlib import Path

import numpy as np

# T161: kok `ayarlar`dan gelir — ciplak yol yazilmaz; kopya
# agacta (worktree) KENDI deposunu gosterir (ON_KAYIT SS22).
from ayarlar import REPO  # noqa: E402
BURASI = Path(__file__).parent

# Binek arac gercek genisligi (ayna haric). Kaynak: TS/EU M1 sinifi tipik
# govde genisligi 1,70-1,90 m. Orta deger alinir; duyarlilik asagida raporlanir.
ARAC_GENISLIGI_M = 1.80
ARAC_GENISLIGI_ALT = 1.70
ARAC_GENISLIGI_UST = 1.90


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kok", type=Path,
                    default=REPO / "data" / "raw_frames")
    ap.add_argument("--model", type=Path, default=REPO / "yolov8m-obb.pt")
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--azami-kare", type=int, default=24)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    from ultralytics import YOLO
    import sys
    # Arac sinif kumesi TEK KAYNAKTAN gelir (madde 16): `codes/arac_maskesi.py`.
    # Dikkat: bu kume sinif ADLARINI tutar (id degil) — DOTA sinif indisleri
    # modele gore degisebildigi icin ad uzerinden eslenir.
    sys.path.insert(0, str(REPO / "codes"))
    from arac_maskesi import ARAC_SINIFLERI          # noqa: E402

    model = YOLO(str(args.model), task="obb")
    kareler = sorted(args.kok.rglob("*.jpg"))
    adim = max(1, len(kareler) // args.azami_kare)
    kareler = kareler[::adim][:args.azami_kare]

    kare_kayit = []
    tum_kisa = []
    for p in kareler:
        r = model.predict(str(p), conf=args.conf, verbose=False)[0]
        if r.obb is None or len(r.obb) == 0:
            kare_kayit.append({"kare": p.name, "arac": 0, "mpp": None})
            continue
        sinif = r.obb.cls.cpu().numpy().astype(int)
        xywhr = r.obb.xywhr.cpu().numpy()          # (x, y, w, h, radyan)
        adlar = r.names
        secili = np.array([adlar.get(int(s), str(s)) in ARAC_SINIFLERI
                           for s in sinif])
        if not secili.any():
            kare_kayit.append({"kare": p.name, "arac": 0, "mpp": None})
            continue
        wh = xywhr[secili][:, 2:4]
        kisa = np.minimum(wh[:, 0], wh[:, 1])      # kisa kenar = govde genisligi
        tum_kisa.append(kisa)
        med = float(np.median(kisa))
        kare_kayit.append({"kare": p.name, "arac": int(secili.sum()),
                           "kisa_medyan_px": med,
                           "mpp": ARAC_GENISLIGI_M / med if med > 0 else None})

    hepsi = np.concatenate(tum_kisa) if tum_kisa else np.array([])
    kare_mpp = np.array([k["mpp"] for k in kare_kayit if k["mpp"]])

    print(f"\n{'=' * 68}\nARAC REFERANS OLCEGI · kok={args.kok.name}\n{'=' * 68}")
    print(f"  taranan kare            : {len(kareler)}")
    print(f"  arac BULUNAN kare       : {len(kare_mpp)}")
    print(f"  toplam arac tespiti     : {len(hepsi)}")
    if not len(hepsi):
        print("  arac bulunamadi — bu yol KAPALI")
        return
    print("-" * 68)
    print(f"  kisa kenar (px)  medyan {np.median(hepsi):.1f} · "
          f"%25 {np.percentile(hepsi, 25):.1f} · %75 {np.percentile(hepsi, 75):.1f}")
    dagilim = (np.percentile(hepsi, 75) - np.percentile(hepsi, 25)) / np.median(hepsi)
    print(f"  ceyrekler arasi yayilim / medyan = {dagilim:.3f}")
    print("-" * 68)
    print(f"  KARE BASINA mpp  medyan {np.median(kare_mpp):.5f} m/px")
    print(f"                   en dusuk {kare_mpp.min():.5f} · "
          f"en yuksek {kare_mpp.max():.5f}")
    kv = (kare_mpp.max() - kare_mpp.min()) / np.median(kare_mpp)
    print(f"  kareler arasi bagil aralik = {kv:.3f}")
    print("-" * 68)
    med_mpp = float(np.median(kare_mpp))
    print(f"  ARAC GENISLIGI DUYARLILIGI (govde 1,70-1,90 m):")
    for g in (ARAC_GENISLIGI_ALT, ARAC_GENISLIGI_M, ARAC_GENISLIGI_UST):
        m = g / float(np.median(hepsi))
        print(f"    {g:.2f} m -> mpp {m:.5f}  ·  r_gerekli = {1.10 / m:5.1f} px")
    print("=" * 68)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(
            {"kok": str(args.kok), "model": str(args.model),
             "kare": len(kareler), "arac_bulunan_kare": len(kare_mpp),
             "arac_tespiti": int(len(hepsi)),
             "kisa_kenar_medyan_px": float(np.median(hepsi)),
             "iqr_orani": float(dagilim),
             "mpp_medyan": med_mpp,
             "mpp_min": float(kare_mpp.min()), "mpp_maks": float(kare_mpp.max()),
             "kareler": kare_kayit}, ensure_ascii=False, indent=1),
            encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
