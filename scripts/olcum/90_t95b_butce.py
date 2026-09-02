"""T95-B · `rota_bul` ACIKLIK KORUMASI — MALIYET BUTCE BICIMINDE (FAZ 1).

⛔ D-402 (2026-09-03) — BU BETIK BUGUN GECERSIZ OLCUM URETIR: uretim artik
`yol_duzelt`e `dt_px` geciriyor (T95/D-164; costmap_path_finder.py:1259),
taban kolu (satir ~190) sizinti sayacini tetikler ve rapor "OLCUM GECERSIZ"
basar. Cagri imzasi ankorsuz, sayilar v30 (D-399). TARIHSEL KAYITTIR;
guncel olcum: scripts/olcum/173_t99_uretim_imzasi.py

IKINCI TUR NEDEN (D-159 · D-160 · D-161). Birinci turda koruma BUYUK kazanc
verdi (kayip medyani 3,00 -> 0,693 px · pay<3px kare 3 -> 0 · ACIK 31 -> 31 ·
`yol_no` 31/31 karede AYNI) ama (4) "duzelt suresi <= 2 kat" olcutunden dustu.
O olcutu ayakta tutan gerekce — "gercek girdi ortomozaiktir, dugum sayisi cok
daha buyuktur" — OLCULMEDEN yazilmisti ve D-161'de CURUDU: uretim plan
izgarasi 128x128, test kumesi 106x106; %21 buyuk, kat kat DEGIL.

Bu tur olcut ALT BILESEN ORANI degil BUTCE cinsindendir (on kayit
`scripts/olcum/t95b_on_kayit.md`):

    (4') rota_bul TOPLAM sure medyani  KORUMA <= 40 ms  VE  artis <= taban %20

⚠ BU BIR GEVSETME DEGILDIR ve iki yone de duser: birinci turda olculen mutlak
artis +1,88 ms'tir; toplam taban ~5 ms cikarsa %38 eder ve T95 YINE REDDEDILIR.

🔴 IKI AYRI KOSUM ZORUNLU (D-159 §4 dersi: kendi aletim olcutu kurtarmasin):
    kosum A  --yalniz-sure              -> (4') icin TEMIZ sure
    kosum B  --yalniz-sure --sayac      -> aciklik CAGRI SAYISI
Sayac `_polyline_asgari_aciklik`i sarar ve `yol_duzelt`in ICINDE calisir, yani
`sure_ms` penceresini KIRLETIR. B kosumundan SURE RAPORLANMAZ.

Kayip sayilari birinci turdan (D-159) tasinir, YENIDEN OLCULMEZ.

────────────────────────────────────────────────────────────────────────────
(Asagisi 89_t95_rota_bul_kayip.py'den devralinan sozlesmedir.)

T95 · `rota_bul` (KATMAN B) ACIKLIK KORUMASI — KAYIP OLCUMU (FAZ 1).

NEDEN (REVIEW_LOG D-158, bagimsiz denetim bulgusu 2). T94 `yol_duzelt`e
ACIKLIK KORUMA kurali ekledi:

    kiris_asgari >= (1 - kiris_bandi) * alt_yol_asgari

ve bunu YALNIZ `rpi_inference` (KATMAN A) yolunda devreye aldi. `rota_bul`
ayni fonksiyonu `dt_px` GECIRMEDEN cagiriyor (costmap_path_finder.py:1116),
oysa `sonuc["dt_px"]` bir satir once kapsamda (:1114). D-154'te olculen kusur
(string-pulling emniyet payini yiyor, medyan 4,00 px) bu yolda HALA CANLI.
Zincir: `rota_bul` -> simulation/scripts/iha_haritala.py:329 -> yayinlanan `road`.

KORLEMESINE TEK SATIR EKLENMEZ. Bu yolun `rpi_inference`tan IKI YAPISAL
FARKI var ve ikisi de kuralin davranisini degistirebilir:
  (a) `rota_bul` `yol_duzelt`i VARSAYILAN `aci_esigi_derece=15.0` ile cagirir;
      `rpi_inference` `0.0` kullanir. D-157'de asama 2 tam bu yuzden korumayi
      SILIYORDU; duzeltildi ama BU YOLDA hic olculmedi.
  (b) `rota_bul` `gecilebilir_tam` olarak C-UZAYINI (`dt_px >= r_gerekli_px`)
      verir; `rpi_inference` `koridor > 0` verir — kural C-uzayinda daha az
      serbestlik gorur.

────────────────────────────────────────────────────────────────────────────
OLCUM SOZLESMESI (D-139 dersi: uretimin yaptigi islemi atlayan olcum uretimi
olcmez).
  · Kume: calisma/sentetik_arena_kadraj_t66 (n=260), TEMIZ kare, CEKILIS YOK.
  · Model kare basina YALNIZ BIR KEZ kosar. Cikan AYNI `mk` maskeleri hem
    TABAN hem KORUMA kosumuna verilir. Iki ayri cikarim YASAK.
  · Taban ve koruma AYNI KOSUMDA olculur; mutlak sayi degil TABANLA kiyas.
  · Uretim kodu DEGISTIRILMEZ; `serbest_alan` ve `yol_duzelt` maymun-yamayla
    sarmalanir (87_t94_yumusak_kiris.py kalibi).

POZITIF KONTROLLER (D-15/K-04 — sifir olcum basari sayilmaz):
  1. TABAN modunda `dt_px` anahtari yol_duzelt'e HIC gecirilmemeli. Sizinti
     sayaci 0 degilse OLCUM GECERSIZDIR.
  2. KORUMA modunda enjeksiyon sayisi cagri sayisina ESIT olmali; degilse
     koruma bazi karelerde hic calismamis demektir.
  3. `mk` maskeleri iki kosum arasinda BOZULMAMALI (imza karsilastirmasi).
────────────────────────────────────────────────────────────────────────────

KABUL OLCUTLERI icin `scripts/olcum/t95_on_kayit.md` — mimar tarafindan, bu
olcum kosulmadan ONCE yazildi. Bu betik olcutu DEGERLENDIRIR, TANIMLAMAZ.
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from ayarlar import REPO, uretim_pt

BURASI = Path(__file__).parent
sys.path.insert(0, str(REPO / "codes"))

import costmap_path_finder as C                                      # noqa: E402
from costmap_path_finder import (_polyline_asgari_aciklik,           # noqa: E402
                                 olcek_px, rota_bul)
from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,      # noqa: E402
                           _preprocess, get_masks)

KUME = BURASI / "calisma" / "sentetik_arena_kadraj_t66"
# Surum adi CIPLAK SABIT degildir (madde 16) — kayit defteri tek kaynak.
MODEL = uretim_pt()
CONF = 0.30

_GERCEK_SERBEST = C.serbest_alan
_GERCEK_DUZELT = C.yol_duzelt
_GERCEK_ACIKLIK = C._polyline_asgari_aciklik

DURUM = {
    "dt_px": None,         # `serbest_alan`dan yakalanan TAM cozunurluk mesafesi
    "koru": False,         # KORUMA modu mu
    "olcum": None,         # son `yol_duzelt` cagrisinin kayip olcumu
    "cagri": 0,            # yol_duzelt cagri sayisi (mod basina sifirlanir)
    "enjekte": 0,          # dt_px enjekte edilen cagri sayisi
    "taban_sizintisi": 0,  # TABAN modunda dt_px gecen cagri — 0 OLMALI
    "olc_aciklik": True,   # False ise aciklik probu KAPALI (temiz zamanlama)
    "sayac": False,        # True ise _polyline_asgari_aciklik sayilir (kosum B)
    "aciklik_cagri": 0,    # o rota_bul cagrisindaki aciklik cagri sayisi
    # CAGRI YERINE GORE AYRIM (kosum B). Uc cagri yeri IMZALARINDAN ayirt
    # edilir — uretim koduna hicbir sey eklenmeden:
    #   :816 onek gecisi (`seg_asgari`)  -> 2 nokta, taban YOK   [SABIT, O(n)]
    #   :822 kiris kabulu                -> 2 nokta, taban VAR   [REDDETME]
    #   :875 asama-2 alt yol             -> 3 nokta, taban YOK   [ASAMA 2]
    # Asama-2 her denetimde once :875'i, sonra :822'yi cagirir; bu yuzden
    #   asama1_kiris = kiris_kabul - asama2_alt
    "site_n": None,
    "site_ms": None,
}

SITELER = ("onek_seg", "kiris_kabul", "asama2_alt")

# ── URETIM OLCEGI (T97) ─────────────────────────────────────────────────────
# `simulation/scripts/iha_haritala.py:64-66` mozaigi SABIT tutar:
#     MOZ_PX = 1024 · MOZ_M = 56,0 · MPP = 56/1024 = 0,0547
# `PLAN_M_HUCRE = 0,45` ile ds = round(0,45/0,0547) = 8 -> plan izgarasi
# 1024/8 = **128x128**. Kadraj kumesi ise 640 px / 50,0 m / mpp 0,0781 ->
# ds = 6 -> **106x106** (D-161'de olculdu).
#
# T97'nin sorusu "128x128 izgarada gercek maliyet nedir"dir. Kadraj kumesinde
# olculen sayi 106x106'nindir ve aradaki farki VARSAYIMLA kapatmak D-161'in
# yasakladigi seydir. Bu yuzden ayni FIZIKSEL sahne, uretimin piksel
# olceginde yeniden kurulur: maske ALGIDAN SONRA olceklenir (model yeniden
# KOSMAZ), 50 m arena 914 px'e gelir ve 1024'luk tuvale ortalanir — yani
# HTAB 50 m + kenar payi, tam da mozaigin yaptigi sey.
MOZ_PX = 1024
MOZ_M = 56.0
MOZ_MPP = MOZ_M / MOZ_PX


def _uretim_olcegine_tasi(mk, icerik, mpp):
    """Ayni fiziksel sahneyi uretim mozaiginin piksel olceginde kur."""
    h, w = next(iter(mk.values())).shape
    hedef = int(round(w * float(mpp) / MOZ_MPP))
    if hedef < 1 or hedef > MOZ_PX:
        return mk, icerik, mpp, None      # sigmiyorsa DOKUNMA (fail-safe)
    ofs = (MOZ_PX - hedef) // 2
    yeni = {}
    for c, m in mk.items():
        kucuk = cv2.resize(m, (hedef, hedef), interpolation=cv2.INTER_NEAREST)
        tuval = np.zeros((MOZ_PX, MOZ_PX), dtype=m.dtype)
        tuval[ofs:ofs + hedef, ofs:ofs + hedef] = kucuk
        yeni[c] = tuval
    o = hedef / float(w)
    x0, y0, iw, ih = icerik
    return (yeni,
            (int(round(x0 * o)) + ofs, int(round(y0 * o)) + ofs,
             int(round(iw * o)), int(round(ih * o))),
            MOZ_MPP, hedef)


# ── maymun-yamalar (uretim kodu DEGISMEZ) ───────────────────────────────────
def _serbest(maskeler, **kw):
    """`rota_bul`un ic `serbest_alan` cagrisini yakala; `dt_px`i sakla."""
    s = _GERCEK_SERBEST(maskeler, **kw)
    DURUM["dt_px"] = s["dt_px"]
    return s


def _aciklik(noktalar, dt):
    """< 2 nokta icin aciklik TANIMSIZDIR — inf yerine None doner."""
    p = list(noktalar)
    if dt is None or len(p) < 2:
        return None
    return float(_polyline_asgari_aciklik(p, dt))


def _duzelt(yol_px, gecilebilir_tam, **kw):
    """`yol_duzelt` sarmalayicisi: KORUMA modunda `dt_px` enjekte eder, her
    iki modda GIRDI/CIKTI acikligini olcer."""
    dt = DURUM["dt_px"]
    DURUM["cagri"] += 1
    if DURUM["koru"]:
        if dt is None:
            raise RuntimeError("KORUMA modunda dt_px yakalanamadi — olcum gecersiz")
        kw["dt_px"] = dt
        DURUM["enjekte"] += 1
    elif "dt_px" in kw:
        # POZITIF KONTROL 1: taban modunda enjeksiyon OLMAMALI
        DURUM["taban_sizintisi"] += 1

    t0 = time.perf_counter()
    sonuc = _GERCEK_DUZELT(yol_px, gecilebilir_tam, **kw)
    t1 = time.perf_counter()

    # 🔴 ZAMANLAMA KIPI: aciklik probu `rota_bul`un `sure_ms["duzelt"]`
    # PENCERESININ ICINDE calisir ve o sayiyi KIRLETIR (her iki modda sabit ek
    # yuk -> ORANI SIKISTIRIR, yani (4) olcutunu OLDUGUNDAN IYI gosterir).
    # `--yalniz-sure` kipinde prob KAPATILIR; o kosumdaki `sure_ms["duzelt"]`
    # uretimin KENDI suresidir.
    a_giris = _aciklik(yol_px, dt) if DURUM["olc_aciklik"] else None
    a_cikis = _aciklik(sonuc, dt) if DURUM["olc_aciklik"] else None
    DURUM["olcum"] = {
        "a_giris": (None if a_giris is None else round(a_giris, 3)),
        "a_cikis": (None if a_cikis is None else round(a_cikis, 3)),
        "kayip": (None if (a_giris is None or a_cikis is None)
                  else round(a_giris - a_cikis, 3)),
        "dugum_giris": len(list(yol_px)),
        "dugum": len(list(sonuc)),
        "duzelt_ms_ic": round((t1 - t0) * 1000, 2),
    }
    return sonuc


def _sayan_aciklik(noktalar, dt_px, taban=None):
    """`_polyline_asgari_aciklik` sayaci — YALNIZ kosum B'de devrededir.

    Uc cagri yeri de `yol_duzelt` icindedir (`:816` onek gecisi, `:822` kiris
    kabulu, `:875` asama-2 denetimi), baska yerde CAGRILMAZ; bu yuzden sayi
    dogrudan kuralin ic maliyetidir. Benim kendi `_aciklik()` yardimcim
    modulden DOGRUDAN ithal edilen referansi kullanir, sayilmaz.
    """
    p = list(noktalar)
    if len(p) >= 3:
        yer = "asama2_alt"
    elif taban is None:
        yer = "onek_seg"
    else:
        yer = "kiris_kabul"
    # Sure OLCUMU cagrinin KENDISINI sarar; sayac ek yuku disaridadir.
    # Toplam kosum suresi bu kosumda KIRLIDIR ama SITE PAYLARI temizdir.
    t0 = time.perf_counter()
    r = _GERCEK_ACIKLIK(noktalar, dt_px, taban)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    DURUM["aciklik_cagri"] += 1
    DURUM["site_n"][yer] += 1
    DURUM["site_ms"][yer] += dt_ms
    return r


def ac():
    C.serbest_alan = _serbest
    C.yol_duzelt = _duzelt
    if DURUM["sayac"]:
        C._polyline_asgari_aciklik = _sayan_aciklik


def kapat():
    C.serbest_alan = _GERCEK_SERBEST
    C.yol_duzelt = _GERCEK_DUZELT
    C._polyline_asgari_aciklik = _GERCEK_ACIKLIK


# ── tek cikarim sozlesmesi (75_koridor_envanteri.py ile ayni) ───────────────
def cikarim(model, img):
    sq, small, icerik = _preprocess(img)
    r = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(r, *sq.shape[:2]), icerik)
    return mk, icerik


def _kosum(mk, icerik, mpp, koru):
    """Tek bir `rota_bul` kosumu; kayip olcumu ile birlikte doner."""
    DURUM["koru"] = koru
    DURUM["olcum"] = None
    DURUM["dt_px"] = None
    DURUM["aciklik_cagri"] = 0
    DURUM["site_n"] = {s: 0 for s in SITELER}
    DURUM["site_ms"] = {s: 0.0 for s in SITELER}
    # 🔴 DUVAR SAATI SADECE `rota_bul` CAGRISINI SARAR. Payin (`pay_px`)
    # hesabi asagida, pencerenin DISINDA yapilir — aksi halde D-159 §4'teki
    # kirlilik hatasi tekrarlanirdi.
    t0 = time.perf_counter()
    r = rota_bul(mk, mpp=mpp, icerik=icerik)
    toplam_ms = (time.perf_counter() - t0) * 1000.0
    dt = DURUM["dt_px"]
    r_gerekli = float(olcek_px(mpp)["r_gerekli_px"])
    wp = r.get("waypoints_px") or []
    wp_aciklik = _aciklik(wp, dt)
    sure_ms = dict(r.get("sure_ms") or {})
    return {
        "durum": r["durum"],
        "yol_no": r["yol_no"],
        "wp": len(wp),
        "toplam_ms": round(toplam_ms, 3),
        "sure_ms": sure_ms,
        "aciklik_cagri": DURUM["aciklik_cagri"],
        "site_n": dict(DURUM["site_n"]),
        "site_ms": {s: round(v, 3) for s, v in DURUM["site_ms"].items()},
        "duzelt_ms": sure_ms.get("duzelt"),
        "r_gerekli_px": round(r_gerekli, 3),
        "wp_aciklik_px": (None if wp_aciklik is None else round(wp_aciklik, 3)),
        "pay_px": (None if wp_aciklik is None
                   else round(wp_aciklik - r_gerekli, 3)),
        "olcum": DURUM["olcum"],
    }


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 3) if xs else None


def _ozet(kayitlar, anahtar):
    """ACIK karelerde ozet. `anahtar` = 'taban' | 'koruma'."""
    acik = [k for k in kayitlar if k[anahtar]["durum"] == "ACIK"]
    duzelt_kosan = [k for k in kayitlar if k[anahtar]["olcum"] is not None]
    kayiplar = [k[anahtar]["olcum"]["kayip"] for k in acik
                if k[anahtar]["olcum"] is not None]
    paylar = [k[anahtar]["pay_px"] for k in acik]
    dugumler = [k[anahtar]["olcum"]["dugum"] for k in acik
                if k[anahtar]["olcum"] is not None]
    # ⚠ OLCUM KIRLILIGI (kendi duzenegimin): `rota_bul`un `sure_ms["duzelt"]`i
    # `yol_duzelt` CAGRISINI sarar; benim sarmalayicim `_polyline_asgari_aciklik`
    # olcumlerini o pencerenin ICINDE yapar. Bu sabit ek yuk her iki modda da
    # eklendigi icin ORANI SIKISTIRIR, yani (4) olcutunu OLDUGUNDAN IYI
    # gosterir. Bu yuzden (4) icin sarmalayicinin kendi IC olcumu
    # (`duzelt_ms_ic` — yalniz gercek cagriyi sarar) esas alinir; dis deger
    # seffaflik icin ayrica raporlanir.
    sureler = [k[anahtar]["olcum"]["duzelt_ms_ic"] for k in acik
               if k[anahtar]["olcum"] is not None]
    sureler_dis = [k[anahtar]["duzelt_ms"] for k in acik]
    dagilim = {}
    for k in kayitlar:
        d = k[anahtar]["durum"]
        dagilim[d] = dagilim.get(d, 0) + 1
    # T95-B: BUTCE DOKUMU. (4') ACIK altkumesinde degerlendirilir — orada
    # `rota_bul` A*'i da kosar, yani sure EN BUYUKTUR; ayrica korumanin
    # etkidigi tek altkume odur. ACIK OLMAYAN kareler dahil edilseydi hem
    # medyan duserdi hem artis orani SEYRELIRDI, yani olcut GEVSERDI.
    dokum = {}
    for alan in ("costmap", "koridor", "astar", "duzelt", "dogrulama"):
        dokum[alan] = med([k[anahtar]["sure_ms"].get(alan) for k in acik])
    # KATMAN AYRIMI — `costmap_path_finder.py:21-25` modulun KENDI sozlesmesi:
    #   KATMAN A (her karede, ~5 ms @384px): serbest_alan() + koridor_adaylari()
    #   KATMAN B (~2 Hz, ~30-40 ms)        : astar() + yol_duzelt() + rota_dogrula()
    # (4') esigi olan 40 ms BU SATIRDAN alindi ve o satir KATMAN B'yi tarif
    # eder. `rota_bul` TOPLAMI iki katmani da icerir. Ikisi de raporlanir;
    # hangisinin olcut olacagi MIMARIN kararidir — burada yorum YAPILMAZ.
    def _kat(alanlar):
        toplamlar = []
        for k in acik:
            s = k[anahtar]["sure_ms"]
            parcalar = [s.get(a) for a in alanlar]
            if any(p is None for p in parcalar):
                continue
            toplamlar.append(sum(parcalar))
        return med(toplamlar)
    dokum["KATMAN_A"] = _kat(("costmap", "koridor"))
    dokum["KATMAN_B"] = _kat(("astar", "duzelt", "dogrulama"))

    # CAGRI YERI DOKUMU (yalniz kosum B'de dolu)
    site = {}
    for s in SITELER:
        site[s] = {
            "n_medyan": med([k[anahtar]["site_n"].get(s) for k in acik]),
            "n_maks": max([k[anahtar]["site_n"].get(s, 0) for k in acik],
                          default=None),
            "ms_medyan": med([k[anahtar]["site_ms"].get(s) for k in acik]),
            "ms_toplam": round(sum(k[anahtar]["site_ms"].get(s, 0.0)
                                   for k in acik), 2),
        }
    # asama1_kiris = kiris_kabul - asama2_alt (asama 2 her denetimde ikisini
    # de cagirir); ayrimi imzadan turetmenin tek yolu budur.
    site["asama1_kiris_n_medyan"] = med(
        [k[anahtar]["site_n"].get("kiris_kabul", 0)
         - k[anahtar]["site_n"].get("asama2_alt", 0) for k in acik])
    dokum_site = site
    giris = [k[anahtar]["olcum"]["dugum_giris"] for k in acik
             if k[anahtar]["olcum"] is not None]
    cagrilar = [k[anahtar]["aciklik_cagri"] for k in acik]
    return {
        "acik": len(acik),
        "duzelt_kosan": len(duzelt_kosan),
        "toplam_ms_medyan": med([k[anahtar]["toplam_ms"] for k in acik]),
        "toplam_ms_maks": (round(max(k[anahtar]["toplam_ms"] for k in acik), 3)
                           if acik else None),
        "toplam_ms_medyan_tum": med([k[anahtar]["toplam_ms"] for k in kayitlar]),
        "sure_dokum": dokum,
        "site_dokum": dokum_site,
        "aciklik_cagri_medyan": med(cagrilar),
        "aciklik_cagri_min": (min(cagrilar) if cagrilar else None),
        "aciklik_cagri_maks": (max(cagrilar) if cagrilar else None),
        "dugum_giris_min": (min(giris) if giris else None),
        "dugum_giris_medyan": med(giris),
        "dugum_giris_maks": (max(giris) if giris else None),
        "kayip_medyan": med(kayiplar),
        "kayip_gt2": sum(1 for x in kayiplar if x is not None and x > 2.0),
        "kayip_n": len(kayiplar),
        "pay_lt3": sum(1 for x in paylar if x is not None and x < 3.0),
        "pay_medyan": med(paylar),
        "dugum_medyan": med(dugumler),
        "wp_medyan": med([k[anahtar]["wp"] for k in acik]),
        "duzelt_ms_medyan": med(sureler),
        "duzelt_ms_dis_medyan": med(sureler_dis),
        "durum_dagilimi": dagilim,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, default=MODEL)
    ap.add_argument("--kume", type=Path, default=KUME)
    ap.add_argument("--sinir", type=int, default=0, help="yalniz ilk N kare")
    ap.add_argument("--yalniz-sure", action="store_true",
                    help="aciklik probunu KAPAT — (4) icin KIRLENMEMIS zamanlama")
    ap.add_argument("--uretim-olcegi", action="store_true",
                    help="T97: maskeyi ALGIDAN SONRA mozaik olcegine tasi "
                         "(1024 px · mpp 0,0547 · ds 8 -> plan izgarasi 128x128)")
    ap.add_argument("--sayac", action="store_true",
                    help="KOSUM B: _polyline_asgari_aciklik cagrilarini say. "
                         "[!] Sayac sure_ms penceresini KIRLETIR — bu kosumdan "
                         "SURE RAPORLANMAZ.")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    DURUM["olc_aciklik"] = not args.yalniz_sure
    DURUM["sayac"] = bool(args.sayac)
    if args.sayac:
        print("[KOSUM B · SAYAC ACIK] [!] sure_ms ve toplam_ms bu kosumda "
              "KIRLIDIR — yalniz CAGRI SAYISI raporlanir.")
    if args.yalniz_sure:
        print("[YALNIZ SURE] aciklik probu KAPALI — sure_ms['duzelt'] "
              "uretimin KENDI suresidir (kayip sayilari bu kosumda YOKTUR).")

    man = json.loads((args.kume / "manifest.json").read_text(encoding="utf-8"))
    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")

    kayitlar = []
    maske_bozuldu = []
    sayaclar = {"taban": {"cagri": 0, "enjekte": 0},
                "koruma": {"cagri": 0, "enjekte": 0}}
    n = 0
    ac()
    try:
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
            if args.sinir and n >= args.sinir:
                break
            n += 1

            mk, icerik = cikarim(model, img)
            if args.uretim_olcegi:
                mk, icerik, mpp, hedef = _uretim_olcegine_tasi(mk, icerik, mpp)
                if n == 1:
                    o = olcek_px(mpp)
                    ds = max(1, int(round(o["plan_m_hucre"] / o["mpp"])))
                    print(f"[URETIM OLCEGI] tuval {MOZ_PX}px · arena {hedef}px "
                          f"· mpp {mpp:.4f} · ds {ds} · plan izgarasi "
                          f"{MOZ_PX // ds}x{MOZ_PX // ds}", flush=True)
            imza_once = (int(mk[0].sum()), int(mk[1].sum()))

            DURUM["cagri"] = DURUM["enjekte"] = 0
            taban = _kosum(mk, icerik, mpp, koru=False)
            sayaclar["taban"]["cagri"] += DURUM["cagri"]
            sayaclar["taban"]["enjekte"] += DURUM["enjekte"]

            DURUM["cagri"] = DURUM["enjekte"] = 0
            koruma = _kosum(mk, icerik, mpp, koru=True)
            sayaclar["koruma"]["cagri"] += DURUM["cagri"]
            sayaclar["koruma"]["enjekte"] += DURUM["enjekte"]

            imza_sonra = (int(mk[0].sum()), int(mk[1].sum()))
            if imza_once != imza_sonra:
                maske_bozuldu.append(f"{p.name} {imza_once}->{imza_sonra}")

            kayitlar.append({"kare": p.name, "taban": taban, "koruma": koruma})
            if n % 20 == 0:
                print(f"  ... {n} kare", flush=True)
    finally:
        kapat()

    t = _ozet(kayitlar, "taban")
    k = _ozet(kayitlar, "koruma")

    # ESLESTIRILMIS ALT KUME — ikisinde de ACIK olan kareler
    ortak = [x for x in kayitlar
             if x["taban"]["durum"] == "ACIK" and x["koruma"]["durum"] == "ACIK"
             and x["taban"]["olcum"] and x["koruma"]["olcum"]]
    e_taban = med([x["taban"]["olcum"]["kayip"] for x in ortak])
    e_koruma = med([x["koruma"]["olcum"]["kayip"] for x in ortak])

    kaybeden = [x["kare"] for x in kayitlar
                if x["taban"]["durum"] == "ACIK" and x["koruma"]["durum"] != "ACIK"]
    kazanan = [x["kare"] for x in kayitlar
               if x["taban"]["durum"] != "ACIK" and x["koruma"]["durum"] == "ACIK"]

    c = "=" * 78
    print(f"\n{c}\nT95 · rota_bul ACIKLIK KORUMASI — TABAN vs KORUMA (ayni kosum)")
    print(f"  model {args.model.name} · kume {args.kume.name} · n={n} · "
          f"TEMIZ kare (cekilis yok)\n{c}")
    print(f"{'olcum':34s}{'TABAN':>14s}{'KORUMA':>14s}")
    satirlar = [
        ("durum == ACIK", "acik"),
        ("yol_duzelt kosan kare", "duzelt_kosan"),
        ("kayip medyani (px)", "kayip_medyan"),
        ("kayip > 2 px olan ACIK kare", "kayip_gt2"),
        ("pay < 3 px olan ACIK kare", "pay_lt3"),
        ("pay medyani (px)", "pay_medyan"),
        ("yol_duzelt cikti dugum medyani", "dugum_medyan"),
        ("waypoint medyani", "wp_medyan"),
        ("duzelt suresi medyani (ms, IC)", "duzelt_ms_medyan"),
        ("  ayni, DIS (olcum kirli)", "duzelt_ms_dis_medyan"),
        ("--- BUTCE (T95-B) ---", None),
        ("rota_bul TOPLAM medyan (ms)", "toplam_ms_medyan"),
        ("rota_bul TOPLAM en buyuk (ms)", "toplam_ms_maks"),
        ("  ayni, TUM 260 kare (ms)", "toplam_ms_medyan_tum"),
        ("aciklik cagrisi medyan", "aciklik_cagri_medyan"),
        ("aciklik cagrisi min / maks", None),
        ("yol_duzelt GIRDI dugum medyan", "dugum_giris_medyan"),
        ("yol_duzelt GIRDI dugum min/maks", None),
    ]
    for ad, key in satirlar:
        if key is None:
            if ad.startswith("---"):
                print(f"{ad:34s}{'':>14s}{'':>14s}")
            elif "cagrisi min" in ad:
                print(f"{ad:34s}"
                      f"{str(t['aciklik_cagri_min']) + '/' + str(t['aciklik_cagri_maks']):>14s}"
                      f"{str(k['aciklik_cagri_min']) + '/' + str(k['aciklik_cagri_maks']):>14s}")
            else:
                print(f"{ad:34s}"
                      f"{str(t['dugum_giris_min']) + '/' + str(t['dugum_giris_maks']):>14s}"
                      f"{str(k['dugum_giris_min']) + '/' + str(k['dugum_giris_maks']):>14s}")
            continue
        print(f"{ad:34s}{str(t[key]):>14s}{str(k[key]):>14s}")

    print(f"\n  `sure_ms` DOKUMU (ACIK kareler, medyan ms)")
    print(f"    {'alan':12s}{'TABAN':>10s}{'KORUMA':>10s}")
    for alan in ("costmap", "koridor", "astar", "duzelt", "dogrulama",
                 "KATMAN_A", "KATMAN_B"):
        if alan == "KATMAN_A":
            print(f"    {'-' * 32}")
        print(f"    {alan:12s}{str(t['sure_dokum'][alan]):>10s}"
              f"{str(k['sure_dokum'][alan]):>10s}")
    print("    KATMAN_A = costmap+koridor (modul sozlesmesi: ~5 ms @384px)")
    print("    KATMAN_B = astar+duzelt+dogrulama (modul sozlesmesi: ~30-40 ms)")
    print("    (4')'un 40 ms'i `costmap_path_finder.py:25`ten alindi ve O SATIR")
    print("    KATMAN B'yi tarif eder; `rota_bul` TOPLAMI ikisini de icerir.")

    if k["aciklik_cagri_medyan"]:
        print(f"\n  MALIYET NEREDEN GELIYOR? (KORUMA · ACIK kareler · kosum B)")
        print(f"    {'cagri yeri':16s}{'n medyan':>10s}{'n maks':>9s}"
              f"{'ms medyan':>11s}{'ms toplam':>11s}{'pay':>7s}")
        sd = k["site_dokum"]
        top = sum(sd[s]["ms_toplam"] for s in SITELER) or 1.0
        adlar = {"onek_seg": ":816 onek", "kiris_kabul": ":822 kiris",
                 "asama2_alt": ":875 asama2"}
        for s in SITELER:
            d = sd[s]
            print(f"    {adlar[s]:16s}{str(d['n_medyan']):>10s}"
                  f"{str(d['n_maks']):>9s}{str(d['ms_medyan']):>11s}"
                  f"{str(d['ms_toplam']):>11s}"
                  f"{100 * d['ms_toplam'] / top:>6.1f}%")
        print(f"    -> asama-1 kiris denetimi (reddetmeler) n medyan: "
              f"{sd['asama1_kiris_n_medyan']}")
        print(f"    :816 SABITTIR (n-1 = {t['dugum_giris_medyan'] and t['dugum_giris_medyan'] - 1} cagri);"
              f" :822/:875 REDDETMELERLE oynar.")
    print(f"\n  ESLESTIRILMIS (ikisinde de ACIK, n={len(ortak)}) kayip medyani:"
          f"  taban {e_taban} · koruma {e_koruma}")

    print("\n  durum dagilimi TABAN : " + " · ".join(
        f"{a}={b}" for a, b in sorted(t["durum_dagilimi"].items(),
                                      key=lambda x: -x[1])))
    print("  durum dagilimi KORUMA: " + " · ".join(
        f"{a}={b}" for a, b in sorted(k["durum_dagilimi"].items(),
                                      key=lambda x: -x[1])))

    print(f"\n{c}\nKARARI CEVIREN KARELER\n{c}")
    print(f"  ACIK -> baska durum (KAYIP) : {len(kaybeden)}"
          + (("  -> " + ", ".join(kaybeden)) if kaybeden else ""))
    print(f"  baska durum -> ACIK (KAZANC): {len(kazanan)}"
          + (("  -> " + ", ".join(kazanan)) if kazanan else ""))
    for x in kayitlar:
        if x["taban"]["durum"] != x["koruma"]["durum"]:
            print(f"    {x['kare']}: {x['taban']['durum']} -> {x['koruma']['durum']}"
                  f"  (yol_no {x['taban']['yol_no']} -> {x['koruma']['yol_no']})")

    print(f"\n{c}\nPOZITIF KONTROLLER\n{c}")
    gecerli = True
    print(f"  1. TABAN modunda dt_px sizintisi : {DURUM['taban_sizintisi']}"
          f"   (0 OLMALI)")
    if DURUM["taban_sizintisi"] != 0:
        gecerli = False
    print(f"  2. TABAN  yol_duzelt cagri/enjekte: "
          f"{sayaclar['taban']['cagri']}/{sayaclar['taban']['enjekte']}"
          f"   (enjekte 0 OLMALI)")
    if sayaclar["taban"]["enjekte"] != 0:
        gecerli = False
    print(f"     KORUMA yol_duzelt cagri/enjekte: "
          f"{sayaclar['koruma']['cagri']}/{sayaclar['koruma']['enjekte']}"
          f"   (ESIT OLMALI)")
    if sayaclar["koruma"]["cagri"] != sayaclar["koruma"]["enjekte"]:
        gecerli = False
    print(f"  3. mk maskesi bozulan kare       : {len(maske_bozuldu)}   (0 OLMALI)")
    if maske_bozuldu:
        gecerli = False
    print(f"  -> OLCUM {'GECERLI' if gecerli else 'GECERSIZ'}")

    # ── ON KAYIT OLCUTLERI (t95_on_kayit.md) — betik TANIMLAMAZ, DEGERLENDIRIR
    print(f"\n{c}\nON KAYIT OLCUTLERI (scripts/olcum/t95b_on_kayit.md)\n{c}")
    o1 = k["acik"] >= t["acik"]
    # (2) BIRINCI TURDAN TASINIR (D-159: 3,00 -> 0,693 · kazanc 2,307 px).
    # Bu kosumda aciklik probu KAPALI oldugu icin kayip OLCULMEZ; yeniden
    # olculmesi emirde de YASAKLANDI.
    kazanc = (None if (t["kayip_medyan"] is None or k["kayip_medyan"] is None)
              else round(t["kayip_medyan"] - k["kayip_medyan"], 3))
    o2 = (kazanc is not None and kazanc >= 1.00)
    o3 = k["pay_lt3"] <= t["pay_lt3"]

    # (4') BUTCE BICIMI — iki yarim birden tutmali.
    tb, kb = t["toplam_ms_medyan"], k["toplam_ms_medyan"]
    o4a = kb is not None and kb <= 40.0
    artis = None if (tb is None or kb is None) else round(kb - tb, 3)
    artis_yuzde = (None if (tb in (None, 0) or artis is None)
                   else round(100.0 * artis / tb, 1))
    o4b = artis_yuzde is not None and artis_yuzde <= 20.0
    o4 = o4a and o4b

    # (5') D-160'ta tabandan yeniden turetildi: taban + 2.
    esik5 = None if t["wp_medyan"] is None else t["wp_medyan"] + 2
    o5 = k["wp_medyan"] is not None and esik5 is not None and k["wp_medyan"] <= esik5

    for ad, tamam, deger in [
            ("(1) ACIK >= taban", o1, f"{k['acik']} >= {t['acik']}"),
            ("(2) kayip medyani kazanci >= 1,00 px",
             None if kazanc is None else o2,
             (f"{kazanc}" if kazanc is not None
              else "bu kosumda OLCULMEDI (prob kapali) — D-159: 2,307 TUTTU")),
            ("(3) pay<3 ACIK kare <= taban", o3,
             f"{k['pay_lt3']} <= {t['pay_lt3']}"),
            ("(4'a) TOPLAM sure <= 40 ms", o4a, f"{kb} <= 40"),
            ("(4'b) artis <= taban %20", o4b,
             f"+{artis} ms = %{artis_yuzde}  (taban {tb})"),
            ("(5') waypoint medyani <= taban+2", o5,
             f"{k['wp_medyan']} <= {esik5}   (TABAN {t['wp_medyan']})")]:
        isaret = "TASINDI" if tamam is None else ("TUTTU " if tamam else "DUSTU ")
        print(f"  {isaret:7s} {ad:38s} {deger}")
    print("  (6) test_rota_sentetik.py ve (7) unittest AYRI kosulur — FAZ 2.")
    # MUTLAK esikli olcut: TABAN da sagliyor mu? Saglamayan bir esik
    # DEGISIKLIGI AYIRT EDEMEZ (D-146/D-157/D-159 kusur sinifi, D-160 kurali).
    if tb is not None and tb > 40.0:
        print(f"\n  [!] (4'a) MUTLAK bir esiktir ve TABAN da saglamiyor "
              f"(taban toplam medyan {tb} ms > 40). Bu yari degisikligi "
              f"AYIRT ETMEZ; olcut GEVSETILMEDI, olgu bildirilir.")
        # OLGU — YORUM DEGIL: 40 ms'in alindigi satir KATMAN B'yi tarif eder.
        kb_t, kb_k = t["sure_dokum"]["KATMAN_B"], k["sure_dokum"]["KATMAN_B"]
        ka_t, ka_k = t["sure_dokum"]["KATMAN_A"], k["sure_dokum"]["KATMAN_A"]
        print(f"      OLGU: esigin alindigi `:25` satiri KATMAN B'yi "
              f"(astar+duzelt+dogrulama) tarif eder.")
        print(f"      KATMAN B medyani  TABAN {kb_t} ms · KORUMA {kb_k} ms  "
              f"(esik 30-40 ms)")
        print(f"      KATMAN A medyani  TABAN {ka_t} ms · KORUMA {ka_k} ms  "
              f"(ayri sozlesme: ~5 ms @384px; bu kume 640px)")
        print(f"      Hangi kapsamin olcut olacagi MIMARIN karidir; olcut "
              f"BURADA DEGISTIRILMEDI.")
    if t["wp_medyan"] is not None and esik5 is not None and t["wp_medyan"] > esik5:
        print(f"\n  [!] (5') TABAN da saglamiyor — olgu bildirilir.")
    print(c)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps({
            "model": str(args.model), "kume": str(args.kume), "n": n,
            "conf": CONF, "taban": t, "koruma": k,
            "eslestirilmis": {"n": len(ortak), "taban": e_taban,
                              "koruma": e_koruma},
            "acik_kaybeden": kaybeden, "acik_kazanan": kazanan,
            "kontrol": {"taban_sizintisi": DURUM["taban_sizintisi"],
                        "sayaclar": sayaclar,
                        "maske_bozuldu": maske_bozuldu,
                        "gecerli": gecerli},
            "olcutler": {"1_acik": o1, "2_kayip_kazanci": o2, "2_deger": kazanc,
                         "3_pay_lt3": o3, "4_sure": o4, "5_wp": o5},
            "kayitlar": kayitlar,
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"\njson -> {args.json}")


if __name__ == "__main__":
    main()
