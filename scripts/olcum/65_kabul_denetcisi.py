"""D-107 KABUL DENETCISI — onceden yazilmis olcutleri MEKANIK olarak kosar.

Esikler `REVIEW_LOG.md` D-107'de sonuc GORULMEDEN yazildi ve burada CIPLAK
SABIT olarak degil, tek bir yerde tanimli olarak durur. Sabah tartisma olmasin
diye karar kurali da koda gomulu: her olcut GECTI/DUSTU doner ve nihai verdikt
AND birlesimidir.

Kullanim:
  venv\\Scripts\\python.exe 65_kabul_denetcisi.py --model <yol> [--ad v27]
"""
import argparse
import hashlib
import json
import re
import statistics
import subprocess
import sys
from pathlib import Path, PureWindowsPath

import cv2
import numpy as np

from ayarlar import REPO

sys.path.insert(0, str(REPO / "codes"))

from rpi_inference import (INFER_SIZE, _maskeleri_icerige_kirp,  # noqa: E402
                           _preprocess, get_masks)

BURASI = Path(__file__).parent

# T168/T193 (D-378): kume beyanina dair OLCULMUS istisna notlari.
# HUKUM DEGISTIRMEZ — okuyani bilgilendirir. Kume donduruldugu icin manifest
# DEGISTIRILEMEZ; notlar sidecar dosyasinda yasar.
BILINEN_KARELER_YOLU = BURASI / "kabul_kumesi_bilinen_kareler.json"


def kume_bilinen_kareler():
    """Sidecar'i oku; yoksa/bozuksa BOS dondur (bilgi blogu hukum tasimaz)."""
    try:
        d = json.loads(BILINEN_KARELER_YOLU.read_text(encoding="utf-8"))
        return {k: v for k, v in d.items() if not k.startswith("_")}
    except Exception:
        return {}
FIGUR = REPO / "data" / "arena_referans" / "sartname_s9_arena.png"


def kabul_kumesi_yolu(kok=None):
    """KADRAJ'in TEK KAYNAGI: registry `profiles[default_profile].kabul_kumesi`.

    🔴 T125 (D-225 §5): eskiden `KADRAJ = BURASI / "calisma" / ...` idi —
    betigin KENDI KONUMUNDAN turetiliyordu. Ayna kopyasinda (scripts/olcum)
    o dizin YOK; denetci BOS kume uzerinden K1..K4'u "DUSTU" raporladi ve
    mimar az kalsin "model her kapida dustu" hukmu veriyordu. Registry'deki
    `_kabul_kumesi_notu` alanin neden orada durdugunu zaten anlatiyordu;
    denetci onu OKUMUYORDU ("iki kopya, biri zorlanmiyor" sinifi).

    Fail-closed: alan yoksa ya da gosterdigi dizin yoksa RuntimeError —
    bos kume uzerinden rapor URETILMEZ. CIPLAK YEDEK YOL YOKTUR (madde 16;
    S5/INFER_SIZE kalibinin sert cesidi: orada guvenli varsayilan vardi,
    burada yanlis kume "olculemeyeni DUSTU satmak" demektir).
    """
    depo = Path(kok) if kok is not None else REPO
    taban = depo / "config" / "model_registry.json"
    try:
        veri = json.loads(taban.read_text(encoding="utf-8"))
        profil = veri["default_profile"]
        deger = veri["profiles"][profil]["kabul_kumesi"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"kabul_kumesi registry'den okunamadi ({taban}): {exc}") from exc
    yol = _goreli_yolu_coz(deger, depo)
    if not yol.is_dir():
        raise RuntimeError(
            f"kabul kumesi dizini yok: {yol} "
            f"(kaynak: {taban} -> profiles.{profil}.kabul_kumesi)")
    return yol


def _goreli_yolu_coz(deger, depo):
    """Registry'deki kume yolu DEPO KOKUNE GORELI ise `depo` altina cozulur.

    T220 (K2/K10, 10 Eylul 2026): alan eskiden ciplak `O:/navitas-local-train/...`
    idi; Jetson'da (`~/navitas`) dizin bulunamiyor, K5/K5A kollari OLCULEMIYORDU
    (JETSON_OTURUM_DURUMU_20260909 SS5.1). Kumeler `data/kabul/` altina alindi ve
    yol depo kokune goreli yazildi (madde 16). Mutlak yol HALA kabul edilir
    (gecici registry'li testler, elle verilen kume). Fail-closed kalip degismedi:
    cozulen dizin yoksa cagiran RuntimeError verir.
    """
    yol = Path(deger)
    if not yol.is_absolute():
        yol = Path(depo) / yol
    return yol


def kabul_kumesi_acili_yolu(kok=None):
    """K5'in IKINCI kolu: ACILI bariyer nufusu (T189 · D-334/D-336).

    🔴 NEDEN: `kabul_kumesi` (yatay) T184'ten ONCE uretildi; manifestinde
    `bariyer_acisi` alani bile YOK ve icindeki HER bariyer yataydir. Bu
    yuzden K5, T184'un duzelttigi DONME KORLUGUNU ne YAKALAYABILIR ne de
    duzelmeyi DOGRULAYABILIRDI — TEST_SPECS SS4.1 anlaminda vakum kapi.

    Ayni fail-closed kalip: alan yoksa ya da dizin yoksa RuntimeError.
    CIPLAK YEDEK YOL YOKTUR (madde 16) — yanlis/bos kume "olculemeyeni
    GECTI satmak" demektir.
    """
    depo = Path(kok) if kok is not None else REPO
    taban = depo / "config" / "model_registry.json"
    try:
        veri = json.loads(taban.read_text(encoding="utf-8"))
        profil = veri["default_profile"]
        deger = veri["profiles"][profil]["kabul_kumesi_acili"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            f"kabul_kumesi_acili registry'den okunamadi ({taban}): {exc}") from exc
    yol = _goreli_yolu_coz(deger, depo)
    if not yol.is_dir():
        raise RuntimeError(f"acili kabul kumesi dizini yok: {yol}")
    return yol


try:
    # 93_t106 gibi ithalatcilar modul niteligi olarak okur; registry saglamsa
    # iki kosum baglaminda da AYNI mutlak yoldur. Bozuksa None kalir ve
    # main() acik hatayla durur — sessiz "bos kume raporu" yolu kapali.
    KADRAJ = kabul_kumesi_yolu()
except RuntimeError as _exc:
    print(f"UYARI: {_exc}", file=sys.stderr)
    KADRAJ = None
CONF = 0.30

# ── D-107 esikleri · SONUC GORULMEDEN yazildi, sabah DEGISTIRILMEYECEK ──────
ESIK = {
    "K1_rota_min": 230,          # / 260   (v24: 196 · yer gercegi: 260)
    "K2_basma_maks": 0.15,       #         (v24: %31,1 · taban: %9,2)
    "K3_agir_maks": 0.03,        #         (v24: %20,4 · taban: %0)
    "K4_arena_disi_maks": 0.05,  #         (v24: %13,3)
    # K6 · ON_KAYIT §12 (2026-08-27, sonuc gorulmeden): rota cizgisi yer gercegi
    # sinif 0 ustunde >= 0,90 VE sinif 1 ustunde 0 waypoint; tutmayan kare
    # YANLIS GUZERGAH. Oran esigi K4 ile ayni olcek. v35'in olculecek degerine
    # gore DEGISTIRILMEZ.
    "K6_yanlis_guzergah_maks": 0.05,
    # K7 · ON_KAYIT SS34 (2026-08-27, sonuc gorulmeden): YAYINLANAN SERIT
    # DOGRULUGU. Sartname SS2.1/SS5.3.2 yanlis guzergaha 0 PUAN verir ve hakem
    # NUMARAYI canli onaylar (SS2.2.3); K1 rota URETIMINI, K6 rotanin yol
    # USTUNDE olmasini olcer — NUMARAYI hicbiri olcmuyordu.
    # Olcum YALNIZ `config/k7_iyi_kosullu_kume.json` (88 kare) uzerinde yapilir:
    # serit numarasi ucte birlerden hesaplandigi icin kapi bir sinira denk
    # gelen karelerde etiket TANIM GEREGI belirsizdir (T101; D-312: kumenin
    # %54'u boyle ve ayrismanin %100'u oradan). Referans o alt kumede KESINDIR.
    "K7_serit_dogruluk_min": 0.95,
    # 🔴 PAYDA OYUNU YASAGI: bir model AZ rota ureterek yuksek oran elde
    # edemesin. Iki kosul BIRLIKTE saglanmali.
    "K7_rota_uretilen_min": 80,      # / 88
}


# ── T110 · K0 GORUNURLUGU (karar D-186) ─────────────────────────────────────
# K0'in cezalandirdigi yon (AZ zemin gormek) GUVENLI yondur — fail-closed.
# Tehlikeli yonu (COK zemin gormek) K0 olcmez; onu K2/K3 olcer (n=258).
# Yani K0 bir EMNIYET degil YETENEK kapisidir ve `> 0` olcutu DEGISMEZ.
# Asil sorun 16 kat dususun SESSIZ gecmesiydi; cozum esik degil GORUNURLUK.
#
# ⚠ ORAN BLOKLAMAZ: `gecti["K0"]`a girmez, verdikt AND birlesimini
# degistirmez. Yalnizca RAPORLAR.
K0_ORAN_ALT = 0.5     # bunun altinda YETENEK uyarisi (fail-closed yon)
K0_ORAN_UST = 2.0     # bunun ustunde TEHLIKELI yon — K2/K3'e ayrica bakilir


def surum_etiketi(model_id):
    """'navitas-seg-v35-512' -> 'v35'. Bulunamazsa None — UYDURULMAZ."""
    m = re.search(r"[-_](v\d+)[-_]", str(model_id))
    return m.group(1) if m else None


def k0_taban_kaydi(kok=None):
    """URETIM model_id'sine KARSILIK GELEN taban kaydi (T132 · D-263 §4.1).

    -> {"deger", "kimlik", "bicim", "gecmis", "not"}

    IKI BICIM de kabul edilir — geriye uyumluluk ZORUNLU:
      * SKALER (eski defter, saha paketi, `jetson_paket` kopyasi):
        `figur_zemin_orani: 0.0903` -> deger okunur, kimlik BILINMEZ.
      * LISTE (T132 bicimi):
        `figur_zemin_orani: [{"surum": "v35", "deger": 0.0903, ...}, ...]`

    🔴 LISTEDE "SONUNCU" DEGIL, URETIM `model_id`'sine KARSILIK GELEN kayit
    secilir. D-263 §4.1 "yine sonuncuyu kullanir" diyordu; kullanicinin T132
    emri bunu DARALTTI ve hakli: liste siralamasi bozulursa "sonuncu" YANLIS
    tabani secer ve bu, T131'in bulduğu kusurun (sessizce kayan referans)
    tam olarak tekrari olurdu. Siralamaya guvenmeyen tek dogru anahtar
    `model_id`dir.

    ⚠ Kayit YOKSA `deger=None` doner ve durum RAPORLANIR — yokluk ne BASARI
    ne BASARISIZLIK sayilir (D-180 dersi).
    """
    yol = (Path(kok) if kok is not None else REPO) / "config" / "model_registry.json"
    bos = {"deger": None, "kimlik": None, "bicim": None, "gecmis": [], "not": ""}
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        profil = veri["profiles"][veri["default_profile"]]
        ham = profil["metrics"]["k0_korluk"]["figur_zemin_orani"]
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return dict(bos, **{"not": "taban kayitli DEGIL — oran hesaplanamadi"})

    if isinstance(ham, (int, float)) and not isinstance(ham, bool):
        return {"deger": float(ham), "kimlik": None, "bicim": "skaler",
                "gecmis": [], "not": "eski SKALER bicim — taban KIMLIGI kayitli degil"}

    if not isinstance(ham, list):
        return dict(bos, **{"not": f"taban bicimi taninmiyor ({type(ham).__name__})"})

    surum = surum_etiketi(profil.get("model_id"))
    if surum is None:
        return {"deger": None, "kimlik": None, "bicim": "liste", "gecmis": ham,
                "not": f"model_id'den surum cikarilamadi ({profil.get('model_id')!r})"}
    for kayit in ham:
        if isinstance(kayit, dict) and kayit.get("surum") == surum:
            try:
                return {"deger": float(kayit["deger"]), "kimlik": surum,
                        "bicim": "liste", "gecmis": ham, "not": ""}
            except (KeyError, TypeError, ValueError):
                break
    return {"deger": None, "kimlik": None, "bicim": "liste", "gecmis": ham,
            "not": f"gecmiste {surum} kaydi YOK — oran hesaplanamadi"}


def k0_taban_orani(figur_kaplama, kok=None):
    """Figur kaplamasinin URETIM TABANINA orani. -> (oran|None, taban|None, not).

    🔴 TABAN SAYIDAN OKUNUR, METINDEN AYIKLANMAZ. Kayit defterindeki
    `metrics.k0_korluk.olculen` bicimli bir metindir
    ('figur zemin %0,49 · raw bos 0/8 ...'); ondan sayi cikarmak D-180'in
    kusur sinifidir (orada `None` sessizce "DUSTU" olmustu). Bu yuzden
    defterde AYRI ve SAYISAL bir alan tutulur: `figur_zemin_orani`.

    ⚠ IMZA DEGISMEDI (3'lu demet): `tests/test_k0_gorunurlugu.py` bu imzayi
    kullaniyor ve o kapi T110'dan beri koruyor. Kimlik/soyagaci isteyen
    `k0_taban_kaydi`yi cagirir.
    """
    kayit = k0_taban_kaydi(kok)
    taban = kayit["deger"]
    if taban is None:
        return None, None, kayit["not"] or "taban kayitli DEGIL — oran hesaplanamadi"
    if not (taban > 0.0) or figur_kaplama is None:
        return None, taban, "taban 0 ya da figur olculemedi — oran hesaplanamadi"
    return float(figur_kaplama) / taban, taban, ""


def k5_durumu(kes):
    """K5'in UC DURUMU: GECTI / DUSTU / OLCULEMEDI (T105 · D-180).

    KUSUR: K5 alt betigin stdout'undan ayristiriliyor; satir basilmazsa
    `kes = None` kaliyordu ve `gecti[\"K5\"] = (kes == 0)` bunu DUSTU sayiyordu.
    `63_bariyer_kesisimi.py` TEK karede kosar; o karede rota cikmazsa kesisim
    OLCULEMEZ — bu \"rota bariyere BASTI\" demek DEGILDIR (yanlis atif).
    Olculdu (D-180): v22/v23/v30 UCU DE None'a dusuyordu; satir hicbir modeli
    ayirt etmiyordu.

    🔴 MIMARIN KISITI — DEGISTIRILEMEZ: OLCULEMEDI != GECTI.
    OLCULEMEDI terfiyi YINE BLOKLAR (fail-closed); yalnizca raporda DUSTU'den
    AYRI gorunur. \"Olculemeyeni gecir\" seklinde bir duzeltme KABUL EDILMEZ.
    """
    if kes is None:
        return "OLCULEMEDI"
    return "GECTI" if kes == 0 else "DUSTU"


def k5_gecti(kes):
    """Verdikt girdisi. YALNIZ 'GECTI' gecer — OLCULEMEDI de DUSTU de bloklar."""
    return k5_durumu(kes) == "GECTI"


def k0_gecti(figur, raw_bos, cp_bos):
    """K0 olcutu. DEGISMEDI (D-186): `figur > 0` VE hicbir kumede bos maske yok.

    🔴 ORAN BU FONKSIYONA PARAMETRE OLARAK BILE GIRMEZ. "Oran bloklamiyor"
    iddiasi boylece bir yorum degil, IMZANIN kendisidir: oranla cagrilamaz.
    """
    return (figur is not None and figur > 0.0
            and raw_bos == 0 and cp_bos == 0)


def k0_dikkat_satiri(oran):
    """Oran bandin disindaysa UYARI metni, degilse None. BLOKLAMAZ."""
    if oran is None or K0_ORAN_ALT <= oran <= K0_ORAN_UST:
        return None
    if oran > K0_ORAN_UST:
        yon = ("     > 2,0 ise TEHLIKELI yon (daha cok zemin) — "
               "K2/K3'e AYRICA bakin.")
    else:
        yon = ("     < 0,5 ise YETENEK uyarisi (daha az zemin) — "
               "fail-closed yon.")
    return (f"  🔴 DIKKAT: figur kaplamasi uretim tabanindan {oran:.2f} kat "
            f"sapiyor.\n{yon}")


# ── T132 · TABANIN KENDISI DE GORUNSUN (D-263 §5) ──────────────────────────
# 🔴 BURADA KURAL YOKTUR, SAYI VARDIR. Denetci bugune kadar ADAYI tabana gore
# sorguluyordu ama TABANI hic sorgulamiyordu; v34'un %0,49'u sorgusuz referans
# oldu (T131/D-261). Asagidaki fonksiyonlar tabanin soyagacina gore NEREDE
# durdugunu BASAR — esik koymaz, `gecti` sozlugune girmez, verdikti etkilemez.
#
# ⚠ BU, D-186'NIN REDDETTIGI SEY DEGILDIR ve yarin okuyan biri bunu kapiya
# CEVIRMESIN:
#     D-186'nin REDDETTIGI : n=1 figure MODEL uzerinde sert kural/tavan
#     BURADA YAPILAN       : TABANIN soyagacindaki yerinin BASILMASI
# Model hakkinda hukum YOKTUR. "Eksik kalmis" diye esik eklenmesi, reddedilmis
# bir fikri arka kapidan geri getirmek olur (§9.2: yetki mimarindir).

def soyagaci_donem_tutarli(gecmis):
    """Kiyaslanabilir kayitlar. Donem-tutarsizlar DISLANIR ama SILINMEZ.

    v17/v20/v21/v24 kendi URETIM DONEMLERINDE 640'ta kosuyordu (gecis v27 ile:
    JETSON_KILAVUZ SS0-T76). Sayilari ALET-TUTARLI ama DONEM-TUTARLI DEGIL
    (D-261 SS2); medyana katilirlarsa duz kiyas sanilir.
    """
    return [k for k in gecmis
            if isinstance(k, dict) and k.get("donem_tutarli") is True
            and isinstance(k.get("deger"), (int, float))]


def taban_medyan_uzakligi(taban, gecmis):
    """Tabanin soyagaci MEDYANINA uzakligi (kat). -> (uzaklik|None, medyan|None).

    Uzaklik YONSUZDUR: 16,1x hem "16 kat asagida" hem "16 kat yukarida"
    olabilir; hangi yon oldugu soyagaci satirinda zaten GORUNUR. Amac sira
    disiligi gostermek, yon hukmu vermek degil.
    """
    kayitlar = soyagaci_donem_tutarli(gecmis)
    if taban is None or not kayitlar:
        return None, None
    medyan = statistics.median([float(k["deger"]) for k in kayitlar])
    if medyan <= 0.0 or taban <= 0.0:
        return None, medyan
    oran = float(taban) / medyan
    return (oran if oran >= 1.0 else 1.0 / oran), medyan


def k0_soyagaci_satirlari(kayit):
    """K0 satirinin ALTINA basilacak GORUNURLUK satirlari. Kural YOK, sayi VAR."""
    gecmis = kayit.get("gecmis") or []
    if kayit.get("bicim") == "skaler":
        return ["     SOYAGACI: kayitli DEGIL (eski SKALER bicim; "
                "taban kimligi bilinmiyor)"]
    if not gecmis:
        return ["     SOYAGACI: kayitli DEGIL"]
    tutarli = soyagaci_donem_tutarli(gecmis)
    disarida = len(gecmis) - len(tutarli)
    govde = " · ".join(f"{k['surum']} %{100*float(k['deger']):.2f}" for k in tutarli)
    satirlar = [f"     SOYAGACI: {govde}"]
    if disarida:
        satirlar.append(f"{'':15s}(+{disarida} kayit DONEM-TUTARLI DEGIL — 640 "
                        f"donemi; kiyasa ve medyana GIRMEZ, kayitta DURUR)")
    uzaklik, medyan = taban_medyan_uzakligi(kayit.get("deger"), gecmis)
    if uzaklik is not None:
        satirlar.append(f"     TABAN, soyagaci medyanindan (%{100*medyan:.2f}) "
                        f"{uzaklik:.1f}x uzakta   <- SAYI, KURAL DEGIL")
    return satirlar


def stdout_utf8_yap(akis=None):
    """CLI ciktisini UTF-8'e sabitler. -> True/False (ZORLAMAZ, patlamaz).

    🔴 OLCULEN KUSUR (T132, emrin disinda bulundu). Bu betik BIR DOSYA olarak
    kosulup ciktisi YAKALANDIGINDA (pipe ya da yonlendirme) Windows'ta
    `sys.stdout.encoding` **cp1254** olur; rapordaki `🔴 DIKKAT` satiri
    `UnicodeEncodeError` firlatir ve DENETCI COKER.

        betik + pipe        -> enc cp1254 -> UnicodeEncodeError
        betik + yonlendirme -> enc cp1254 -> UnicodeEncodeError
        konsol              -> enc utf-8  -> sorunsuz  (mimar D-255'te boyle kostu)

    Yani uyari, TAM DA SOYLEYECEK SOZU OLDUGUNDA denetciyi olduruyordu; insan
    izlerken calisip otomasyon yakalarken duserdi. T110'un butun amaci o satiri
    GORUNUR kilmakti (D-186/D-188).

    ⚠ YALNIZ `main()` icinde cagrilir. Ice aktarma sirasinda cagrilsaydi, bu
    modulu import eden HER TEST'in stdout'unu degistirirdi — sinanan seyin
    disinda yan etki uretmek bu projenin kendi kuralina aykiri.
    `errors="replace"` : bilinmeyen bir kodlamada bile COKMEK yerine ISARET basar.
    """
    akis = sys.stdout if akis is None else akis
    try:
        akis.reconfigure(encoding="utf-8", errors="replace")
        return True
    except (AttributeError, ValueError, OSError):
        return False


def k0_taban_metni(kayit, oran, taban, oran_notu=""):
    """K0 satirindaki PARANTEZ metni — tabanin KIMLIGI burada gorunur.

    ⚠ SAF FONKSIYON OLARAK AYRILDI (T132). Metin `main()` icine gomulu
    kalsaydi "basilan satir kimligi iceriyor mu" sorusu ancak tum denetciyi
    (model yukleyerek) kosarak sinanabilirdi; bu projede o, sinanmayan bir
    iddia demektir. Simdi kapiya girer.
    """
    if oran is None or taban is None:
        return oran_notu or "oran YOK"
    if kayit.get("kimlik"):
        kimlik = f" = {kayit['kimlik']}'in degeri"
    elif kayit.get("bicim") == "skaler":
        kimlik = " (kimlik YOK · eski skaler bicim)"
    else:
        kimlik = ""
    return f"uretim tabani %{100*taban:.2f}{kimlik} · oran {oran:.2f}"


def kume_parmak_izi(kok):
    """Kabul kumesinin TURETILMIS parmak izi. Elle liste TUTULMAZ.

    Gerekce (D-263 §4.3): elle tutulan liste bu projede DORT kez bayatladi.
    Ozet, dosya ADI + BOYUTU uzerinden alinir (icerik degil): 284 goruntunun
    tamamini okumak denetciyi her kosumda yavaslatirdi ve yakalamak istedigimiz
    sey "kume DEGISTI mi" sorusudur — dosya eklenmesi/silinmesi/boyut degisimi
    bunu yakalar. ⚠ SINIRI ACIK: ayni boyutta icerik degisimi YAKALANMAZ.
    """
    kok = Path(kok)
    if not kok.is_dir():
        return {"n": 0, "ozet": None, "not": f"dizin yok: {kok}"}
    # Dondurulmus kayitlar Windows'ta uretildi: Path siralamasi orada
    # buyuk/kucuk harfe duyarsizdir. POSIX'te URETIM_KOMUTU.md farkli yere
    # geldigi icin ayni dosyalar farkli ozet veriyordu. Tarihi siralamayi
    # platformdan bagimsiz koru; es anahtarlari goreli adla kesinlestir.
    dosyalar = sorted(
        (p for p in kok.rglob("*") if p.is_file()),
        key=lambda p: (PureWindowsPath(p.relative_to(kok).as_posix()),
                       p.relative_to(kok).as_posix()))
    h = hashlib.sha256()
    for p in dosyalar:
        h.update(p.relative_to(kok).as_posix().encode("utf-8"))
        h.update(str(p.stat().st_size).encode("ascii"))
    return {"n": len(dosyalar), "ozet": f"sha256:{h.hexdigest()}",
            "yontem": "sorted(rglob) uzerinden ad+boyut; icerik OKUNMAZ"}


def kaplama(model, p):
    """K0 korluk olcumu. 🔴 PAYDA: LETTERBOX TUVALIDIR, icerik kutusu DEGIL.

    T116 · D-361 — BU FARK BILEREK YAZILIYOR, cunku ayni ad iki yerde iki
    farkli sey demek:

        buradaki `kaplama`            -> payda = `sq.shape` (letterbox TUVAL)
        `karar_sozlesmesi.zemin_kaplamasi` -> payda = ICERIK kutusu (iw*ih)

    Ve `ZEMIN_KAPLAMA_TAVANI = 0.55` **ICERIK** paydasina gore kalibredir
    (T142/D-286).

    OLCULDU (v36, data/raw_frames'ten 8 kare): iki sayinin orani SABIT
    **1,78x** (16:9 karenin kareye letterbox'lanmasi). Yani buradaki sayi
    sozlesmeninkinden 1,78 KAT KUCUKTUR.

    ⚠ BU SAYIYI `ZEMIN_KAPLAMA_TAVANI` ILE KIYASLAMAYIN. Kiyaslarsaniz
    tavani fiilen **0,98**'e cikarmis olursunuz (0,55 x 1,78) ve gercekte
    %98 zemin goren bir kare bile "tavan altinda" gorunur.
    Nobetci: `tests/test_t116_kaplama_paydasi.py`.
    """
    img = cv2.imread(str(p))
    if img is None:
        return None
    sq, small, icerik = _preprocess(img)
    h, w = sq.shape[:2]
    sonuc = model.predict(small, imgsz=INFER_SIZE, conf=CONF, verbose=False)
    mk = _maskeleri_icerige_kirp(get_masks(sonuc, h, w), icerik)
    return float((mk[0] > 0).mean())


def k14_durumlari(d, esik=None):
    """K1..K4'un UC DURUMU (T125 · D-225 §5) — T105'in K5 kalibinin AYNISI.

    d: `61_rota_moloza_basma.py` JSON'u (dict) ya da None (alt betik cokmus /
    JSON yok). Kural: girdi yok ya da payda 0 -> OLCULEMEDI; olculdu ve esigin
    altinda -> DUSTU. 🔴 ESIKLER DEGISMEZ — degisen yalniz OLCULEMEYENIN
    raporlanisi. OLCULEMEDI != GECTI: verdikt icin YINE bloklar (k5_gecti
    kalibi); "olculemeyeni gecir" seklinde bir okuma KABUL EDILMEZ.
    """
    e = ESIK if esik is None else esik
    if not d or int(d.get("n", 0)) == 0:
        return ({k: "OLCULEMEDI" for k in ("K1", "K2", "K3", "K4")},
                {"n": int(d.get("n", 0)) if d else 0, "rota_uretilen": 0,
                 "basan": 0, "agir": 0, "arena_disi": 0})
    n = int(d.get("n", 0))
    r = int(d.get("rota_uretilen", 0))
    basan = int(d.get("basan", 0))
    agir = int(d.get("agir", 0))
    disi = int(d.get("arena_disi", 0))
    durum = {"K1": "GECTI" if r >= e["K1_rota_min"] else "DUSTU"}
    if r == 0:
        # Rota hic uretilmemis: K1 OLCULDU ve dustu; K2..K4'un paydasi yok.
        durum.update(K2="OLCULEMEDI", K3="OLCULEMEDI", K4="OLCULEMEDI")
    else:
        durum["K2"] = "GECTI" if basan / r <= e["K2_basma_maks"] else "DUSTU"
        durum["K3"] = "GECTI" if agir / r <= e["K3_agir_maks"] else "DUSTU"
        durum["K4"] = "GECTI" if disi / r <= e["K4_arena_disi_maks"] else "DUSTU"
    return durum, {"n": n, "rota_uretilen": r, "basan": basan,
                   "agir": agir, "arena_disi": disi}


def k6_durumu(d, esik=None):
    """K6 'ROTA YOL USTUNDE' UC DURUMU (ON_KAYIT §12) — T105/T125 kalibi.

    d: `61_rota_moloza_basma.py` JSON'u ya da None. Payda = yanlis_guzergah
    hesaplanan (rota uretilen) kare. Girdi yok / eski 61 ciktisi (alan yok) /
    payda 0 -> OLCULEMEDI; aksi halde oran <= esik -> GECTI, degilse DUSTU.
    OLCULEMEDI != GECTI: verdikt icin YINE bloklar.
    -> (durum, {"yol_olculen", "yanlis_guzergah", "oran"})
    """
    e = ESIK if esik is None else esik
    bos = {"yol_olculen": 0, "yanlis_guzergah": 0, "oran": None}
    if not d or "yanlis_guzergah" not in d or "yol_olculen" not in d:
        return "OLCULEMEDI", bos
    r = int(d.get("yol_olculen", 0))
    y = int(d.get("yanlis_guzergah", 0))
    if r == 0:
        return "OLCULEMEDI", dict(bos, yanlis_guzergah=y)
    oran = y / r
    durum = "GECTI" if oran <= e["K6_yanlis_guzergah_maks"] else "DUSTU"
    return durum, {"yol_olculen": r, "yanlis_guzergah": y, "oran": oran}


def k7_durumu(d, esik=None):
    """K7 'YAYINLANAN SERIT DOGRULUGU' UC DURUMU (ON_KAYIT SS34) — K6 kalibi.

    d: `151_k7_serit_dogrulugu.py` JSON'unun `ozet` govdesi ya da None.
    Payda = alt kumede ROTA URETILEN kare. Rota uretilememesi bir SERIT HATASI
    DEGILDIR (fail-closed davranistir) ve onu zaten K1 olcer; iki kapi birlikte
    tam ortuyor. Ama payda oyununa karsi ikinci kosul vardir: alt kumede rota
    uretilen kare `K7_rota_uretilen_min` altina duserse K7 DUSER.

    Girdi yok / alan eksik / payda 0 -> OLCULEMEDI (verdikt icin YINE bloklar).
    -> (durum, {"rota_uretilen", "dogru", "yanlis", "dogruluk"})
    """
    e = ESIK if esik is None else esik
    bos = {"rota_uretilen": 0, "dogru": 0, "yanlis": 0, "dogruluk": None}
    if not d or "rota_uretilen" not in d or "dogru" not in d:
        return "OLCULEMEDI", bos
    r = int(d.get("rota_uretilen", 0))
    dg = int(d.get("dogru", 0))
    if r == 0:
        return "OLCULEMEDI", dict(bos, dogru=dg)
    oran = dg / r
    detay = {"rota_uretilen": r, "dogru": dg, "yanlis": r - dg, "dogruluk": oran}
    yeterli_payda = r >= e["K7_rota_uretilen_min"]
    durum = ("GECTI" if (oran >= e["K7_serit_dogruluk_min"] and yeterli_payda)
             else "DUSTU")
    detay["payda_yeterli"] = bool(yeterli_payda)
    return durum, detay


def kos(betik, ek):
    """Alt betigi kosar; (stdout, basarili_mi) dondurur.

    🔴 T125: cikis kodu artik KONTROL EDILIR. Alt betik coktuyse bu
    OLCULEMEDI'dir — "0 rota uretti" DEGILDIR. Eski hali cikis kodunu
    yutuyordu ve cokme, dort kapinin "DUSTU"su olarak raporlaniyordu.
    """
    p = subprocess.run([sys.executable, "-B", str(BURASI / betik)] + ek,
                       capture_output=True, text=True, encoding="utf-8",
                       errors="replace")
    if p.returncode != 0:
        kuyruk = (p.stderr or "").strip().splitlines()[-3:]
        print(f"  UYARI: {betik} exit={p.returncode} — ciktisi OLCULEMEDI "
              "sayilacak.", file=sys.stderr)
        for s in kuyruk:
            print(f"    {s}", file=sys.stderr)
        return p.stdout or "", False
    return p.stdout or "", True


def main():
    # 🔴 ILK IS: cikti yakalandiginda uyari satiri denetciyi COKERTMESIN
    # (T132'de olculdu; gerekce `stdout_utf8_yap` docstringinde).
    stdout_utf8_yap()
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", type=Path, required=True)
    ap.add_argument("--ad", default=None)
    ap.add_argument("--kok", type=Path, default=None,
                    help="registry koku (varsayilan REPO; T125 senaryo "
                         "testleri icin)")
    args = ap.parse_args()
    ad = args.ad or args.model.parent.parent.name

    # T125: girdi kumesi MODEL YUKLENMEDEN dogrulanir — kume yoksa denetci
    # ACIK HATAYLA durur; bos kume uzerinden verdikt URETILMEZ (D-225 §5).
    kume = kabul_kumesi_yolu(args.kok)

    from ultralytics import YOLO
    model = YOLO(str(args.model), task="segment")
    sonuc, gecti = {}, {}

    # ── K0 · KORLUK YOK (v25'in olum sebebi) ────────────────────────────────
    k0 = {}
    k0["figur"] = kaplama(model, FIGUR)
    for ad_k, kok, desen in (
            ("raw_frames", REPO / "data" / "raw_frames", "*.jpg"),
            ("copy_paste", REPO / "dataset" / "copy_paste_gercek" / "images" / "train", "*.jpg")):
        # 🔴 ORNEKLEME KALDIRILDI (T110 · D-186). Eskiden 8 kare orneklenirdi:
        #     raw_frames  67 -> 8  (%11,9)   ·   copy_paste  393 -> 8  (%2,0)
        # `bos == 0` olcutu DEGISMEDI; ayni olcut artik TAM KUMEDE uygulanir.
        # (`rglob` de iki kez cagriliyordu; tek cagriya indirildi.)
        yollar = sorted(kok.rglob(desen))
        oranlar = [kaplama(model, p) for p in yollar]
        oranlar = [o for o in oranlar if o is not None]
        k0[ad_k] = {"n": len(oranlar), "bos": sum(1 for o in oranlar if o <= 0.0),
                    "ort": float(np.mean(oranlar)) if oranlar else 0.0}
    gecti["K0"] = k0_gecti(k0["figur"], k0["raw_frames"]["bos"],
                           k0["copy_paste"]["bos"])
    sonuc["K0"] = k0

    # ── K1..K4 · rota / basma / arena disi ──────────────────────────────────
    jj = BURASI / "results" / "t63" / f"{ad}_kabul.json"
    jj.parent.mkdir(parents=True, exist_ok=True)
    jj.unlink(missing_ok=True)          # T125: BAYAT json yeniden okunmasin
    # T150/D-386: zincir URETIM yapilandirmasiyla kosar (varis HB'den,
    # olcek+sekil kapili) — uretim baglandiktan sonra HB'siz olcum
    # uretimi yansitmazdi (D-351 sinifi).
    _, alt_ok = kos("61_rota_moloza_basma.py",
                    ["--model", str(args.model),
                     "--kume", str(kume), "--json", str(jj),
                     "--hb-hedefli"])
    d = (json.loads(jj.read_text(encoding="utf-8"))
         if alt_ok and jj.is_file() else None)
    k14, sayilar = k14_durumlari(d)
    n, r = sayilar["n"], sayilar["rota_uretilen"]
    basan, agir, disi = sayilar["basan"], sayilar["agir"], sayilar["arena_disi"]
    sonuc["K1_rota"] = f"{r}/{n}"
    sonuc["K2_basma"] = f"{basan}/{r}" if r else "-"
    sonuc["K3_agir"] = f"{agir}/{r}" if r else "-"
    sonuc["K4_arena_disi"] = f"{disi}/{r}" if r else "-"
    sonuc["K14_durum"] = k14
    gecti["K1"] = k14["K1"] == "GECTI"
    gecti["K2"] = k14["K2"] == "GECTI"      # OLCULEMEDI de bloklar (T105 kalibi)
    gecti["K3"] = k14["K3"] == "GECTI"
    gecti["K4"] = k14["K4"] == "GECTI"

    # ── K6 · ROTA YOL USTUNDE (ON_KAYIT §12) — ayni 61 JSON'undan ─────────────
    k6, k6s = k6_durumu(d)
    sonuc["K6_yanlis_guzergah"] = (f"{k6s['yanlis_guzergah']}/{k6s['yol_olculen']}"
                                   if k6s["yol_olculen"] else "-")
    sonuc["K6_oran"] = k6s["oran"]
    sonuc["K6_durum"] = k6
    sonuc["K6_yanlis_kareler"] = list((d or {}).get("yanlis_kareler", []))
    gecti["K6"] = k6 == "GECTI"             # OLCULEMEDI de bloklar (T105 kalibi)

    # ── K7 · YAYINLANAN SERIT DOGRULUGU (ON_KAYIT SS34/SS35 · D-314/D-316) ───
    # Sartname SS2.1/SS5.3.2 yanlis guzergaha 0 PUAN verir; hakem NUMARAYI canli
    # onaylar (SS2.2.3). K1 rota URETIMINI, K6 rotanin yol USTUNDE olmasini
    # olcer — numarayi hicbiri olcmuyordu.
    # 🔴 OLCUM ZINCIRIN KENDI KOSUMUNDA URETILIR: disaridan elle beslenen bir
    # JSON'a guvenilmez (bayat/baska modelin sayisi terfi gecirebilirdi).
    j7 = BURASI / "results" / "t63" / f"{ad}_k7.json"
    j7.unlink(missing_ok=True)          # BAYAT json yeniden okunmasin (T125)
    _c7, k7_ok = kos("151_k7_serit_dogrulugu.py",
                     ["--agirlik", str(args.model), "--kume", str(kume),
                      "--cikti", str(j7)])
    d7 = (json.loads(j7.read_text(encoding="utf-8")).get("ozet")
          if k7_ok and j7.is_file() else None)
    k7, k7s = k7_durumu(d7)
    sonuc["K7_serit"] = (f"{k7s['dogru']}/{k7s['rota_uretilen']}"
                         if k7s["rota_uretilen"] else "-")
    sonuc["K7_dogruluk"] = k7s["dogruluk"]
    sonuc["K7_rota_uretilen"] = k7s["rota_uretilen"]
    sonuc["K7_durum"] = k7
    sonuc["K7_yanlis_kareler"] = list((d7 or {}).get("yanlis_kareler", []))
    gecti["K7"] = k7 == "GECTI"             # OLCULEMEDI de bloklar (T105 kalibi)

    # ── K8 · GERCEK KARE (T195 · D-332 §5) ─────────────────────────────────
    # 🔴 NEDEN EKLENDI: bu zincir TAMAMEN SENTETIKTIR ve 2026-08-28'de bunun
    # bedeli olculdu — v37 adayi K0..K7'nin HEPSINI gecip "URETIME ALINIR"
    # verdikti aldi, ama elimizdeki tek gercekci karede zemin kaplamasi
    # %4,4 -> %56,1 cikip uretim karar yolunu ZEMIN_MASKESI_SUPHELI ile
    # kirdi. Bunu yakalayan tek sey `tests/test_gercek_arena_kapisi.py` idi
    # ve o ZINCIRIN ICINDE DEGILDI: suit kosulmasaydi model sessizce terfi
    # edebilirdi.
    # ⚠ YENI ESIK YOK: uretimde ZATEN VAR OLAN zemin saglamlik kapisi gercek
    # kare uzerinde kosulur. n = 1'dir ve alt betik bunu acikca yazar.
    j8 = BURASI / "results" / "t63" / f"{ad}_k8.json"
    j8.parent.mkdir(parents=True, exist_ok=True)
    j8.unlink(missing_ok=True)                 # bayat json okunmasin (T125)
    _c8, k8_ok = kos("155_gercek_kare_kapisi.py",
                     ["--agirlik", str(args.model), "--json", str(j8)])
    d8 = (json.loads(j8.read_text(encoding="utf-8"))
          if k8_ok and j8.is_file() else None)
    sonuc["K8_durum"] = (d8 or {}).get("durum", "OLCULEMEDI")
    sonuc["K8_zemin_kaplamasi"] = (d8 or {}).get("zemin_kaplamasi")
    sonuc["K8_karar_yolu_reddi"] = (d8 or {}).get("karar_yolu_reddi")
    gecti["K8"] = sonuc["K8_durum"] == "GECTI"   # OLCULEMEDI de bloklar

    # ── K5 · bariyer kesisimi — ZEMIN: POPULASYON (T126 · D-243) ────────────
    # 🔴 ZEMIN TASINDI: eskiden `63_bariyer_kesisimi` TEK OOD figurunde kosardu
    # ve UC modelde de OLCULEMEDI donuyordu (D-231): o figurde hicbir model rota
    # uretmiyor. Yeni zemin, kabul kumesinin BARIYERLI + OLCEKLI + ROTALI
    # karelerdir (`66_k5_bariyer_populasyon.py`, D-243 SART 2).
    # SART 1 (bariyer MODELDEN GELMEZ): 66, bariyer maskesini `63`ten ITHAL
    # eder ve LAB a* esigiyle TEMIZ GORUNTUDEN hesaplar — degerlendirilen
    # modelin maskesi kullanilmaz. Kanit: `results/t126/sart1_kaniti.json`
    # (dedektor model YUKLENMEDEN kosuldu) ve bariyere KOR sahte model bu
    # kapidan DUSER (`tests/test_t126_k5_zemini.py`).
    # SART 3: esik DEGISMEDI — olculebilir HER karede kesisim 0 px.
    # SART 4: olculebilir kare 0 ise OLCULEMEDI (yokluk GECTI degildir).
    k5j = BURASI / "results" / "t63" / f"{ad}_k5_populasyon.json"
    k5j.parent.mkdir(parents=True, exist_ok=True)
    k5j.unlink(missing_ok=True)                 # bayat json okunmasin (T125)
    _c5, k5_ok = kos("66_k5_bariyer_populasyon.py",
                     ["--model", str(args.model), "--json", str(k5j)])
    k5d = json.loads(k5j.read_text(encoding="utf-8")) \
        if k5_ok and k5j.is_file() else None
    if k5d is None:
        # Alt betik cokmus/JSON yok -> OLCULEMEDI (D-226 kalibi: cokme "0 kesen"
        # DEGILDIR).
        sonuc["K5_durum"] = "OLCULEMEDI"
        sonuc["K5_olculebilir_kare"] = 0
        sonuc["K5_kesen_kare"] = None
        sonuc["K5_kesisim_px"] = None
    else:
        sonuc["K5_durum"] = k5d["K5_durum"]     # 66'nin SAF fonksiyonu uretti
        sonuc["K5_olculebilir_kare"] = k5d["olculebilir_kare"]
        sonuc["K5_kesen_kare"] = k5d["kesen"]
        sonuc["K5_kesisim_px"] = k5d["kesisim_px"]
        sonuc["K5_bariyerli_kare"] = k5d["bariyerli"]
        sonuc["K5_kume"] = k5d["kume"]
    gecti["K5"] = sonuc["K5_durum"] == "GECTI"  # OLCULEMEDI de bloklar

    # ── K5A · ACILI BARIYER NUFUSU (T189 · ON_KAYIT D-334/D-336) ───────────
    # 🔴 NEDEN: yukaridaki K5 nufusunda HER bariyer YATAYDIR (kume T184'ten
    # once uretildi). Yani K5, T184'un duzelttigi DONME KORLUGUNU ne
    # yakalayabilir ne de duzelmeyi dogrulayabilirdi. Bu kol ayni olcutu
    # (kesisim 0 px) ACIDAN BAGIMSIZ bir nufusta kosar.
    # ⚠ YENI ESIK YOK: gecme kosulu K5 ile BIREBIR AYNI.
    # AYIRT EDICILIK MUTASYONLA KANITLANDI (t189_ayirt_edicilik.json):
    # T184 oncesi dedektor acili nufusta 185->48 kare (52,7 puan) duserken
    # yatay nufusta 181->181 HIC dusmuyor.
    k5aj = BURASI / "results" / "t63" / f"{ad}_k5a_acili.json"
    k5aj.unlink(missing_ok=True)                # bayat json okunmasin (T125)
    try:
        acili_kume = kabul_kumesi_acili_yolu()
    except RuntimeError as exc:
        acili_kume = None
        print(f"  (K5A kumesi cozulemedi: {exc})")
    if acili_kume is None:
        k5ad = None
        _c5a = ""
    else:
        _c5a, k5a_ok = kos("66_k5_bariyer_populasyon.py",
                           ["--model", str(args.model), "--kume", str(acili_kume),
                            "--json", str(k5aj)])
        k5ad = (json.loads(k5aj.read_text(encoding="utf-8"))
                if k5a_ok and k5aj.is_file() else None)
    if k5ad is None:
        sonuc["K5A_durum"] = "OLCULEMEDI"       # cokme "0 kesen" DEGILDIR
        sonuc["K5A_olculebilir_kare"] = 0
        sonuc["K5A_kesen_kare"] = None
        sonuc["K5A_kesisim_px"] = None
    else:
        sonuc["K5A_durum"] = k5ad["K5_durum"]
        sonuc["K5A_olculebilir_kare"] = k5ad["olculebilir_kare"]
        sonuc["K5A_kesen_kare"] = k5ad["kesen"]
        sonuc["K5A_kesisim_px"] = k5ad["kesisim_px"]
        sonuc["K5A_bariyerli_kare"] = k5ad["bariyerli"]
        sonuc["K5A_kume"] = k5ad["kume"]
    gecti["K5A"] = sonuc["K5A_durum"] == "GECTI"  # OLCULEMEDI de bloklar

    # BILGI (kapi DEGIL, D-243): tek figurdeki eski olcum korunur.
    c, _figur_ok = kos("63_bariyer_kesisimi.py", ["--model", str(args.model)])
    kes = None
    for s in c.splitlines():
        if "ROTA x BARIYER kesisimi" in s:
            try:
                kes = int(s.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                pass
    sonuc["K5_figur_bilgi_px"] = kes
    sonuc["K5_figur_bilgi_durum"] = k5_durumu(kes)

    # ── RAPOR ───────────────────────────────────────────────────────────────
    print(f"\n{'='*66}\nKABUL DENETIMI · {ad}\n  esikler: REVIEW_LOG D-107 "
          f"(sonuc gorulmeden yazildi)\n{'='*66}")
    # T132: kume parmak izi HER KOSUMDA basilir — hangi kume olculdu sorusu
    # rapordan okunabilsin (D-263 §4.3; TURETILIR, elle tutulmaz).
    pi = kume_parmak_izi(kume)
    print(f"  kabul kumesi: {kume}\n{'':16s}parmak izi n={pi['n']} · "
          f"{pi.get('ozet') or pi.get('not')}")
    sonuc["kabul_kumesi"] = str(kume)
    sonuc["kabul_kumesi_parmak_izi"] = pi

    f = sonuc["K0"]["figur"]
    # ⚠ `args.kok` GECIRILIYOR: kume T125'te --kok'a baglanmisti ama taban
    # okumasi baglanmamisti; --kok verildiginde denetci kumeyi bir defterden,
    # tabani BASKA defterden okuyordu. Tek satirlik tutarlilik onarimi (T132).
    kayit = k0_taban_kaydi(args.kok)
    oran, taban, oran_notu = k0_taban_orani(f, kok=args.kok)
    taban_metni = k0_taban_metni(kayit, oran, taban, oran_notu)
    print(f"  K0 KORLUK YOK        {'GECTI' if gecti['K0'] else 'DUSTU':<6} "
          f"figur zemin %{100*f:.2f} ({taban_metni})")
    print(f"{'':23s}raw bos {k0['raw_frames']['bos']}/{k0['raw_frames']['n']} "
          f"· cp bos {k0['copy_paste']['bos']}/{k0['copy_paste']['n']}")
    # ⚠ BLOKLAMAZ — `gecti` sozlugune DOKUNMAZ, yalniz basar (D-186).
    dikkat = k0_dikkat_satiri(oran)
    if dikkat:
        print(dikkat)
    # T132 · D-263 §5: TABANIN kendisi de gorunsun. Kural degil, SAYI.
    for satir in k0_soyagaci_satirlari(kayit):
        print(satir)
    sonuc["K0"]["figur_orani"] = oran
    sonuc["K0"]["figur_tabani"] = taban
    sonuc["K0"]["figur_taban_kimligi"] = kayit.get("kimlik")
    sonuc["K0"]["figur_taban_bicimi"] = kayit.get("bicim")
    sonuc["K0"]["soyagaci"] = kayit.get("gecmis")
    sonuc["K0"]["oran_notu"] = oran_notu
    print(f"  K1 ROTA >= {ESIK['K1_rota_min']}       {k14['K1']:<11} "
          f"{sonuc['K1_rota']}")
    print(f"  K2 BASMA <= %{100*ESIK['K2_basma_maks']:.0f}      {k14['K2']:<11} "
          f"{sonuc['K2_basma']}   (taban %9,2)")
    print(f"  K3 AGIR  <= %{100*ESIK['K3_agir_maks']:.0f}       {k14['K3']:<11} "
          f"{sonuc['K3_agir']}   (taban %0)")
    print(f"  K4 ARENA DISI <= %{100*ESIK['K4_arena_disi_maks']:.0f}  {k14['K4']:<11} "
          f"{sonuc['K4_arena_disi']}")
    if "OLCULEMEDI" in k14.values():
        print("     (girdi kumesi / alt betik sorunu: OLCULEMEDI — bu 'DUSTU'"
              " DEGILDIR ama terfi YINE bloklanir: OLCULEMEDI != GECTI."
              " T125 · D-225 §5.)")
    print(f"  K6 ROTA YOL USTUNDE <= %{100*ESIK['K6_yanlis_guzergah_maks']:.0f}  "
          f"{sonuc['K6_durum']:<11} yanlis guzergah {sonuc['K6_yanlis_guzergah']}"
          f"   [ON_KAYIT §12: yol_payi >= 0,90 ve engel_wp == 0]")
    if sonuc["K6_durum"] == "OLCULEMEDI":
        print("     (rota yok ya da 61 ciktisinda K6 alanlari yok: OLCULEMEDI —"
              " terfi YINE bloklanir: OLCULEMEDI != GECTI.)")
    k5d = sonuc["K5_durum"]
    olc = sonuc.get("K5_olculebilir_kare", 0)
    kesen_k = sonuc.get("K5_kesen_kare")
    print(f"  K5 BARIYER = 0 px    {k5d:<11} "
          f"kesen {kesen_k if kesen_k is not None else '-'}/{olc} kare"
          f" · toplam {sonuc.get('K5_kesisim_px')} px"
          f"  [zemin: POPULASYON, T126/D-243]")
    print(f"{'':23s}bilgi (kapi DEGIL): tek figur "
          f"{sonuc.get('K5_figur_bilgi_durum')} "
          f"({sonuc.get('K5_figur_bilgi_px')} px)")
    _k5ak = sonuc.get("K5A_kesen_kare")
    print(f"  K5A ACILI BARIYER    {sonuc.get('K5A_durum', 'OLCULEMEDI'):<11} "
          f"kesen {_k5ak if _k5ak is not None else '-'}/"
          f"{sonuc.get('K5A_olculebilir_kare', 0)} kare"
          f" · toplam {sonuc.get('K5A_kesisim_px')} px"
          f"  [T189 · acidan bagimsiz nufus, esik K5 ile AYNI]")
    _k7d = sonuc.get("K7_durum", "OLCULEMEDI")
    _k7o = sonuc.get("K7_dogruluk")
    print(f"  K7 SERIT DOGRULUGU   {_k7d:<6} {sonuc.get('K7_serit', '-')} "
          f"({'-' if _k7o is None else f'%{100 * _k7o:.1f}'}"
          f" · esik %{100 * ESIK['K7_serit_dogruluk_min']:.0f}"
          f" · payda {sonuc.get('K7_rota_uretilen', 0)}"
          f"/{ESIK['K7_rota_uretilen_min']} asgari)")
    if _k7d == "OLCULEMEDI":
        print("     (olcum uretilemedi: alt betik coktu ya da alt kume okunamadi."
              " Bu 'dogru serit yayinladi' DEMEK DEGILDIR — kanit yoktur."
              " Terfi YINE bloklanir: OLCULEMEDI != GECTI.)")
    elif sonuc.get("K7_yanlis_kareler"):
        print(f"     yanlis: {sonuc['K7_yanlis_kareler']}")
        print("     ⚠ K7 dususu dogrudan 'model yanlis gordu' DEMEK DEGILDIR:"
              " referans ETIKETSIZ alani gecilemez sayar (D-315). Once ETIKET"
              " KAPSAMI denetlenir.")
        # T168/D-378: bazi kareler icin o denetim YAPILDI — olculmus hukmu
        # yazdir ki ayni soru her kosumda yeniden acilmasin.
        _bk = kume_bilinen_kareler()
        for _kare in sonuc["K7_yanlis_kareler"]:
            # D-386: K7 yanlis kaydi [ad, yayin, gt] LISTESI olabilir —
            # ilk kosum tam burada 'unhashable type: list' ile coktu ve
            # verdikt JSON'u yazilamadi (fail-closed kaldi, dogru yon).
            if isinstance(_kare, (list, tuple)) and _kare:
                _kare = _kare[0]
            _n = _bk.get(_kare) or _bk.get(str(_kare) + ".jpg")
            if _n:
                print(f"     · {_kare}: [{_n['tur']}] {_n['ozet'][:150]}..."
                      f" ({_n['kanit']})")
    if k5d == "OLCULEMEDI":
        print("     (olculebilir kare YOK: bariyerli+olcekli karelerde rota"
              " uretilmedi ya da alt betik cokTU. Bu 'carpmadi' DEMEK"
              " DEGILDIR — kanit yoktur. Terfi YINE bloklanir:"
              " OLCULEMEDI != GECTI. D-243 SART 4.)")
    _k8k = sonuc.get("K8_zemin_kaplamasi")
    print(f"  K8 GERCEK KARE       {sonuc['K8_durum']}  "
          + (f"zemin kaplamasi {_k8k:.4f} · karar yolu "
             f"{sonuc.get('K8_karar_yolu_reddi')}"
             if _k8k is not None else "olculemedi")
          + "  [T195 · n=1 · YZ figuru, 'sahada calisir' DEMEZ]")
    if sonuc["K8_durum"] == "DUSTU":
        print("     🔴 Model, elimizdeki TEK gercekci karede uretim yolunu"
              " KIRIYOR (D-332).")
    print("-" * 66)
    if not gecti["K0"]:
        print("  VERDIKT: RED — K0 dustu. v25 ile AYNI sebep, tartisma yok.")
    elif all(gecti.values()):
        print("  VERDIKT: URETIME ALINIR — D-107'nin alti olcutu + K6 + K7"
              " + K5A (acili nufus) + K8 (gercek kare) saglandi.")
    else:
        durumlar = dict(sonuc.get("K14_durum", {}))
        durumlar["K5"] = sonuc.get("K5_durum")
        durumlar["K6"] = sonuc.get("K6_durum")
        durumlar["K7"] = sonuc.get("K7_durum")
        durumlar["K5A"] = sonuc.get("K5A_durum")
        durumlar["K8"] = sonuc.get("K8_durum")
        d_ = [(k + "(OLCULEMEDI)" if durumlar.get(k) == "OLCULEMEDI" else k)
              for k, v in gecti.items() if not v]
        print(f"  VERDIKT: URETIME ALINMAZ — dusen: {', '.join(d_)}")
        print("           kok nedene baglanip TEK duzeltme turu kosulur.")
    print("=" * 66)
    _tavan = [(k, v) for k, v in kume_bilinen_kareler().items()
              if isinstance(v, dict) and v.get("tur") == "TAVAN"]
    for _k, _v in _tavan:
        print(f"  ℹ KUME TAVANI ({_k}): {_v['ozet'][:150]}... ({_v['kanit']})")
    print("\n⚠ Bu olcumlerin tamami SENTETIKTIR. Hicbiri 'sahada calisir'")
    print("  anlamina gelmez (D-88 + D-99, kalici kisit).")

    cj = BURASI / "results" / "t63" / f"{ad}_kabul_verdikt.json"
    cj.parent.mkdir(parents=True, exist_ok=True)
    cj.write_text(json.dumps({"model": str(args.model), "esikler": ESIK,
                              "olcum": sonuc, "gecti": gecti,
                              "verdikt": all(gecti.values())},
                             ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\njson -> {cj}")


if __name__ == "__main__":
    main()
