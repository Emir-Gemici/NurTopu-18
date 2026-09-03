"""P5 (D-396) — HISTEREZIS OLCUMU: yayina sizan cevrilme ham cevrilmeye karsi.

ON KAYIT: results/p5_histerezis/ON_KAYIT.md (H1 esigi sonuc gorulmeden:
yayimlanan cevrilme <= ham cevrilmenin %40'i; ham >= 5 ise kesin azalma).

Yontem — 68'in gurultu recetesi KARE-ICI akisa cevrilir: her kare icin
[temiz, g1, g2, g3, g4] dizisi AYNI SAHNENIN pespese 5 karesinin vekilidir.
Dizi hem HAM hem `KararYumusatici`den gecirilerek oynatilir; sayilan yalniz
KARE-ICI (ayni sahne) cevrilmedir:

  ham cevrilme       : dizide karar (serit,red) degisim sayisi
  yayimlanan cevrilme : yumusatici True dedigi orneklerdeki degisim sayisi
  bastirilan NO_ROUTE : 0 OLMAK ZORUNDA (H2 — fail-closed)

⚠ ILK SURUM (ayni gece, D-396'da kayitli) 260 kareyi TEK akis saydi ve
sahne SINIRLARINDAKI mesru karar degisimlerini de "cevrilme" olarak
yumusaticiya yikti — kume ardisik ucus DEGIL, 260 bagimsiz sahnedir; 68'in
onculu "AYNI sahne, gurultu altinda"dir. Bu yuzden yumusatici kare basina
taze kurulur (sahneler arasi tasima olcumu kirletir). Esikler DEGISMEDI.

── H1c EKI (FDR/ACIK_KALEMLER §4b #24; olcut ON_KAYIT EK-1'de, sonuc
   gorulmeden yazildi) ────────────────────────────────────────────────────
H1c: "Yayimlanan cevrilmelerin TAMAMI (i)/(ii)/(iii) siniflarindan;
siniflandirilamayan yayimlanmis cevrilme = 0" — (i) NO_ROUTE gecisleri,
(ii) kalici cogunluk gecisleri (5 ornegin >=3'u yeni karar), (iii) H5 tavani
yayinlari (bayatlama siniri). Bu ek OLCUMDUR; esik/tanim DEGISTIRILMEDI.
"""
import argparse
import json
import sys
from importlib import import_module
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

from karar_sozlesmesi import (KARAR_HISTEREZIS_KARE,  # noqa: E402
                              KararYumusatici)

m68 = import_module("68_karar_kararliligi")
kabul_kumesi_yolu = import_module("65_kabul_denetcisi").kabul_kumesi_yolu

CONF = 0.30

# ── H1c · YAYIN GEREKCESI (mekanizma), KOMPOZISYON VEKILI DEGIL ─────────────
# NEDEN (olculen kusur): ON_KAYIT EK-1'in (iii) sinifi "H5 TAVANI YAYINLARI"
# dir — bu bir MEKANIZMA olayidir (bastirma tavani doldu, yayin daha fazla
# bayatlayamaz), kare kompozisyonu DEGILDIR. Ilk surumde (iii) icin
# `kimlik_sayilari[kimlik] == 2` VEKILI kullaniliyordu; o vekil ON_KAYIT'ta
# YAZMIYOR ve dort kovayi (no_route / cogunluk / h5_tavani / azinlik) INSA
# GEREGI tuketiyordu. Sonuc: "siniflandirilamayan = 0" olcutu, H1a'nin
# ("azinlik = 0") birebir kopyasina donusuyor ve H1c BOS KAPI oluyordu —
# kendi tanimiyla asla dusemeyen bir olcut olcum degildir. Bu yuzden H1c,
# yayin kararinin GEREKCESINI durum makinesinin CAGRI ONCESI durumundan
# turetir; turetim her cagrida `suz`un gercek donusuyle capraz denetlenir
# (uymazsa olcum DUSER, sessizce yanlis etiketlemez).
GEREKCE_FAIL_CLOSED = "fail_closed"     # ret/rotasizlik — aninda gecer
GEREKCE_ILK_ROTA = "ilk_rota"           # NO_ROUTE sonrasi ilk rota
GEREKCE_AYNI_SERIT = "ayni_serit"       # yayimlanan seridin tazelenmesi
GEREKCE_K_TEYIDI = "K_teyidi"           # K ardisik teyit
GEREKCE_H5_TAVANI = "h5_tavani"         # bastirma tavani doldu
GEREKCE_BASTIRILDI = "bastirildi"       # yayin yok

# H1c'nin kabul ettigi UC sinif (ON_KAYIT EK-1). Bu esleme disinda kalan her
# yayimlanmis cevrilme "siniflandirilamayan"dir — yani H1c ihlali.
H1C_SINIF_ESLEMESI = {
    GEREKCE_FAIL_CLOSED: "no_route",    # (i)
    GEREKCE_ILK_ROTA: "no_route",       # (i) — fail-closed'in obur yuzu
    GEREKCE_K_TEYIDI: "cogunluk",       # (ii)
    GEREKCE_H5_TAVANI: "h5_tavani",     # (iii)
}
H1C_SINIFLANDIRILAMAYAN = "siniflandirilamayan"


def yayin_gerekcesi(yumusatici, yol, red):
    """`suz` CAGRILMADAN ONCEKI durumdan hangi kuralin atesleyecegini turet.

    Uretim koduna DOKUNULMAZ (bu bir olcum isidir): karar yine
    `KararYumusatici.suz` tarafindan verilir; burada yalnizca cagri oncesi
    durum okunup gerekce yeniden kurulur ve sonra gercek donusle karsilastirilir.
    """
    if yol is None or red is not None:
        return GEREKCE_FAIL_CLOSED
    if yumusatici._yayimlanan is None:
        return GEREKCE_ILK_ROTA
    if yol == yumusatici._yayimlanan:
        return GEREKCE_AYNI_SERIT
    sayac = yumusatici._aday_sayac + 1 if yol == yumusatici._aday else 1
    if sayac >= yumusatici._esik:
        return GEREKCE_K_TEYIDI
    if yumusatici._bastirilan_ardisik >= yumusatici._esik - 1:
        return GEREKCE_H5_TAVANI
    return GEREKCE_BASTIRILDI


def h1c_sinifi(gerekce, kimlik_sayisi, esik):
    """Yayimlanmis bir CEVRILMEYI ON_KAYIT EK-1 siniflarina yerlestir.

    (ii) icin ON_KAYIT'in KENDI kompozisyon sarti da aranir ("5 ornegin >=3'u
    yeni karar"): mekanizma K teyidi dese bile dizide o karar K'dan az
    goruluyorsa sinif TUTMAZ ve olcut ihlali yazilir. Bu sart olmadan esleme
    orten (exhaustive) olur ve H1c bos kapiya doner.
    """
    if gerekce in (GEREKCE_FAIL_CLOSED, GEREKCE_ILK_ROTA):
        return "no_route"
    if gerekce == GEREKCE_K_TEYIDI and kimlik_sayisi >= esik:
        return "cogunluk"
    if gerekce == GEREKCE_H5_TAVANI:
        return "h5_tavani"
    return H1C_SINIFLANDIRILAMAYAN


def gurultulu_kare(rng, img, sigma):
    """68'in gurultu recetesi — tohum verildiginde BIREBIR tekrar edilebilir."""
    g = rng.normal(0.0, sigma, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + g, 0, 255).astype(np.uint8)


def kare_oynat(dizi, esik=None):
    """Tek sahnenin ornek dizisini HAM ve YAYIN akisi olarak oynat.

    Saf (GPU'suz, modelsiz) — determinizm testi bu fonksiyonu kosar.
    `dizi`: `68_karar_kararliligi.karar` ciktilarindan olusan liste; ilk iki
    alan (serit, red) karar KIMLIGIDIR.
    """
    if esik is None:
        esik = KARAR_HISTEREZIS_KARE
    yumusatici = KararYumusatici(esik=esik)
    son_ham = son_yayin = ("BASLANGIC",)
    kare_ham = kare_yayin = 0
    bastirilan = bastirilan_no_route = 0
    siniflar, h1c_siniflar = {}, {}
    kimlik_sayilari = {}
    for k in dizi:
        kimlik_sayilari[tuple(k[:2])] = kimlik_sayilari.get(tuple(k[:2]), 0) + 1
    for k in dizi:
        kimlik = tuple(k[:2])                  # (serit, red)
        if son_ham != ("BASLANGIC",) and kimlik != son_ham:
            kare_ham += 1
        son_ham = kimlik

        gerekce = yayin_gerekcesi(yumusatici, k[0], k[1])
        yayimla = yumusatici.suz(k[0], k[1])
        if yayimla != (gerekce != GEREKCE_BASTIRILDI):
            # Turetim durum makinesinden SAPTI: etiket guvenilmez, olcum durur.
            raise AssertionError(
                f"yayin_gerekcesi durum makinesiyle uyusmadi: gerekce={gerekce} "
                f"ama suz()={yayimla} (kimlik={kimlik})")
        if yayimla:
            if son_yayin != ("BASLANGIC",) and kimlik != son_yayin:
                kare_yayin += 1
                # ── H1a vekil siniflandirmasi (D-396 gecesinde kayitli; bilesim
                # gorulmeden yazildi). DEGISTIRILMEDI: H1a bu sayimla GECTI.
                no_route_gecisi = (
                    k[0] is None or k[1] is not None
                    or son_yayin[0] is None or son_yayin[1] is not None)
                if no_route_gecisi:
                    sinif = "no_route"          # (i) fail-closed
                elif kimlik_sayilari[kimlik] >= KARAR_HISTEREZIS_KARE:
                    sinif = "cogunluk"          # (ii) kalici karar
                elif kimlik_sayilari[kimlik] == 2:
                    sinif = "h5_tavani"         # (iii) bayatlama siniri
                else:
                    sinif = "azinlik"           # H1a IHLALI
                siniflar[sinif] = siniflar.get(sinif, 0) + 1
                # ── H1c: GEREKCEYE dayali siniflandirma (yukaridaki NEDEN)
                hs = h1c_sinifi(gerekce, kimlik_sayilari[kimlik], esik)
                h1c_siniflar[hs] = h1c_siniflar.get(hs, 0) + 1
            son_yayin = kimlik
        else:
            bastirilan += 1
            if k[0] is None or k[1] is not None:
                bastirilan_no_route += 1       # H2 ihlali — 0 olmali
    return {"ham": kare_ham, "yayin": kare_yayin, "bastirilan": bastirilan,
            "bastirilan_no_route": bastirilan_no_route, "siniflar": siniflar,
            "h1c_siniflar": h1c_siniflar}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=uretim_pt())
    ap.add_argument("--kume", type=Path, default=None)
    ap.add_argument("--sigma", type=float, default=2.0)
    ap.add_argument("--tekrar", type=int, default=4)
    ap.add_argument("--tohumlar", type=int, nargs="+", default=[7, 42])
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()
    if args.kume is None:
        args.kume = kabul_kumesi_yolu()

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    sonuclar = {}
    for tohum in args.tohumlar:
        rng = np.random.default_rng(tohum)
        n = 0
        ham_cevrilme = yayin_cevrilme = 0
        ham_kararsiz_kare = yayin_kararsiz_kare = 0
        bastirilan = bastirilan_no_route = 0
        siniflar = {}
        h1c_siniflar = {}

        for ornek in man["ornekler"]:
            if ornek.get("durum") != "YAZILDI" or not ornek.get("arena"):
                continue
            p = args.kume / ornek["cikti"]
            mpp = ornek["arena"].get("mpp")
            if not p.is_file() or not mpp:
                continue
            img = cv2.imread(str(p))
            if img is None:
                continue
            n += 1

            dizi = [m68.karar(model, img, mpp)]
            for _ in range(args.tekrar):
                dizi.append(m68.karar(
                    model, gurultulu_kare(rng, img, args.sigma), mpp))

            # AYNI sahnenin 5 ornegi = kare-ici akis; yumusatici taze kurulur
            k_sonuc = kare_oynat(dizi)
            ham_cevrilme += k_sonuc["ham"]
            yayin_cevrilme += k_sonuc["yayin"]
            ham_kararsiz_kare += 1 if k_sonuc["ham"] else 0
            yayin_kararsiz_kare += 1 if k_sonuc["yayin"] else 0
            bastirilan += k_sonuc["bastirilan"]
            bastirilan_no_route += k_sonuc["bastirilan_no_route"]
            for ad, adet in k_sonuc["siniflar"].items():
                siniflar[ad] = siniflar.get(ad, 0) + adet
            for ad, adet in k_sonuc["h1c_siniflar"].items():
                h1c_siniflar[ad] = h1c_siniflar.get(ad, 0) + adet

        sonuclar[str(tohum)] = {
            "n_kare": n, "ornek_per_kare": args.tekrar + 1,
            "ham_cevrilme": ham_cevrilme,
            "yayimlanan_cevrilme": yayin_cevrilme,
            "ham_kararsiz_kare": ham_kararsiz_kare,
            "yayin_kararsiz_kare": yayin_kararsiz_kare,
            "bastirilan": bastirilan,
            "bastirilan_no_route": bastirilan_no_route,
            "yayin_cevrilme_siniflari": siniflar,
            # H1c (ON_KAYIT EK-1) — GEREKCEYE dayali siniflandirma
            "h1c_yayin_cevrilme_siniflari": h1c_siniflar,
            "h1c_siniflandirilamayan": h1c_siniflar.get(
                H1C_SINIFLANDIRILAMAYAN, 0),
        }
        print(f"tohum {tohum:>3}: n={n} · ham={ham_cevrilme} "
              f"({ham_kararsiz_kare} karede) · yayimlanan={yayin_cevrilme} "
              f"({yayin_kararsiz_kare} karede) · bastirilan={bastirilan} · "
              f"bastirilan_NO_ROUTE={bastirilan_no_route}")
        print(f"           siniflar (H1a vekili): {siniflar}")
        print(f"           siniflar (H1c gerekce): {h1c_siniflar}")

    # ON_KAYIT H1/H2 verdikti
    h1 = all(
        (s["yayimlanan_cevrilme"] <= 0.40 * s["ham_cevrilme"])
        and (s["ham_cevrilme"] < 5 or s["yayimlanan_cevrilme"] < s["ham_cevrilme"])
        for s in sonuclar.values())
    h2 = all(s["bastirilan_no_route"] == 0 for s in sonuclar.values())
    # EK-1 (bilesim gorulmeden yazildi): mekanizmanin gercek vaadi
    h1a = all(s["yayin_cevrilme_siniflari"].get("azinlik", 0) == 0
              for s in sonuclar.values())
    h1b = all(s["yayimlanan_cevrilme"] < s["ham_cevrilme"]
              for s in sonuclar.values())
    # H1c: siniflandirilamayan yayimlanmis cevrilme = 0 (iki tohumda da).
    # Ayrica toplam denkligi aranir: siniflar yayimlanan cevrilmeyi TAM
    # ortmelidir — eksik ortme "olculemedi"dir, "gecti" degil.
    h1c = all(
        s["h1c_siniflandirilamayan"] == 0
        and sum(s["h1c_yayin_cevrilme_siniflari"].values())
        == s["yayimlanan_cevrilme"]
        for s in sonuclar.values())
    print(f"\nH1 (toplam %40 esigi — OZGUN): {'GECTI' if h1 else 'DUSTU'}")
    print(f"H1a (azinlik rota-rota sizinti = 0): {'GECTI' if h1a else 'DUSTU'}")
    print(f"H1b (kesin azalma): {'GECTI' if h1b else 'DUSTU'}")
    print(f"H1c (siniflandirilamayan yayin = 0): {'GECTI' if h1c else 'DUSTU'}")
    print(f"H2 (NO_ROUTE bastirilmadi): {'GECTI' if h2 else 'DUSTU'}")

    cikti = {"_on_kayit": "results/p5_histerezis/ON_KAYIT.md",
             "_model": str(args.model), "sigma": args.sigma,
             "esik_K": KARAR_HISTEREZIS_KARE,
             "tohumlar": sonuclar, "H1_ozgun": h1, "H1a": h1a,
             "H1b": h1b, "H1c": h1c, "H2": h2}
    hedef = args.json or (REPO / "results" / "p5_histerezis"
                          / "olcum_20260903.json")
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(json.dumps(cikti, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    print(f"json -> {hedef}")
    return 0 if (h1a and h1b and h1c and h2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
