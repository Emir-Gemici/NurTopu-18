"""
Navitas Autonomous Systems — RPi 5 Inference
Kullanim:
  python3 rpi_inference.py --fps
  python3 rpi_inference.py --image test.jpg
  python3 rpi_inference.py --image gorseller/
  python3 rpi_inference.py --video video.mp4
  python3 rpi_inference.py --video video.mp4 --no-save   (sadece izle, kaydetme)
  python3 rpi_inference.py --camera

Cikti (--image): results/<ad>_result.jpg  (orijinal cozunurluk)
                 results/<ad>_ika_map.jpg  (IKA navigasyon haritasi)
Cikti (--video): results/<ad>_result.mp4  (annotated video)

Dizin yapisi:
  navitas/
    rpi_inference.py
    best_ncnn_model/
"""

import argparse
import importlib
import json
import math
import os
import signal
import sys
import threading
import time
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# Gorus hatti rasterizasyonu TEK KAYNAKTAN alinir. Kopyalamak, rota_dogrula ile
# farkli yuvarlama uretip "burada guvenli, orada ihlal" celiskisine yol acardi;
# ayni kopyala-yapistir kusuru bu depoda zaten kayitli (test_rota_sentetik'in
# _tohum_merkezi kopyasi). costmap_path_finder yalniz cv2/numpy/heapq kullanir,
# dairesel import yoktur.
if __package__:
    from .costmap_path_finder import (R_GEREKLI_M, _bagli_mi,
                                      _bresenham_noktalari,
                                      _gorus_hatti, _maks_aralikla_bol,
                                      _tohum_plan_izgarasi, astar,
                                      plan_izgarasi, yol_duzelt)
    from .karar_sozlesmesi import (ALAN_YETERSIZ_SEBEBI,
                                   BILESEN_YOK_SEBEBI,
                                   GORUS_HATTI_KOPUK_SEBEBI,
                                   KENAR_GUVENSIZ_SEBEBI,
                                   MASKE_YOK_SEBEBI,
                                   OLCEK_YOK_SEBEBI,
                                   ROTA_PLAN_MAKS_HUCRE,
                                   TELEMETRI_IRTIFA_TAZELIK_S,
                                   ARAC_DURUM_TAZELIK_S,
                                   UC_BANT_TEMAS_YOK_SEBEBI,
                                   bant_temasi_gereken_px,
                                   bant_temasi_yeterli_mi,
                                   hedef_bant_yuksekligi, mpp_irtifadan,
                                   r_gerekli_piksel,
                                   zemin_maskesi_reddi,
                                   rota_darbogaz_guveni,
                                  rota_koridor_genisligi_reddi,
                                  BARIYER_ENGEL_SINIFI,
                                  ince_bariyer_maskesi,
                                  kapama_cekirdegi_px,
                                  INCE_BETON_SERIT_ETKIN,
                                  INCE_BETON_SERIT_ORTAM_DEGISKENI,
                                  ince_beton_serit_maskesi,
                                  hb_konumu,
                                  HB_SEKIL_ESIGI,
                                  KararYumusatici,
                                  SARTNAME_IHA_UB_KENAR_M,
                                  yerel_konum_m,
                                  hedef_yok_reddi,
                                   rota_guven_reddi,
                                   BERABERLIK_BANDI,
                                   OLCEK_GUVEN_CARPANI,
                                   beraber_adaylar,
                                   OLCEK_KAYNAK_TELEMETRI,
                                   OLCEK_KAYNAK_ARAC,
                                   SENARYO_BOYUTLARI_M,
                                   olcek_gecerli_mi,
                                   olcek_kahini,
                                   olcek_guveni_uygula,
                                   rota_olcek_reddi, serit_no,
                                   rota_serit_karari,
                                   KAMERA_DUSEN_KARE_UST_SINIRI,
                                   KAMERA_DUSEN_KARE_BEKLEME_S,
                                   KAMERA_BITIS_KULLANICI,
                                   KAMERA_BITIS_DUSEN_KARE,
                                   KAMERA_BITIS_ACILAMADI,
                                   KAMERA_BITIS_SINYAL,
                                   MODEL_TUREV_SHA_YER_TUTUCU)
else:
    from costmap_path_finder import (R_GEREKLI_M, _bagli_mi,
                                     _bresenham_noktalari,
                                     _gorus_hatti, _maks_aralikla_bol,
                                     _tohum_plan_izgarasi, astar,
                                     plan_izgarasi, yol_duzelt)
    from karar_sozlesmesi import (ALAN_YETERSIZ_SEBEBI,
                                  BILESEN_YOK_SEBEBI,
                                  GORUS_HATTI_KOPUK_SEBEBI,
                                  KENAR_GUVENSIZ_SEBEBI,
                                  MASKE_YOK_SEBEBI,
                                  OLCEK_YOK_SEBEBI,
                                  ROTA_PLAN_MAKS_HUCRE,
                                  TELEMETRI_IRTIFA_TAZELIK_S,
                                  ARAC_DURUM_TAZELIK_S,
                                  UC_BANT_TEMAS_YOK_SEBEBI,
                                  bant_temasi_gereken_px,
                                  bant_temasi_yeterli_mi,
                                  hedef_bant_yuksekligi, mpp_irtifadan,
                                  r_gerekli_piksel,
                                  zemin_maskesi_reddi,
                                  rota_darbogaz_guveni,
                                  rota_koridor_genisligi_reddi,
                                  BARIYER_ENGEL_SINIFI,
                                  ince_bariyer_maskesi,
                                  kapama_cekirdegi_px,
                                  INCE_BETON_SERIT_ETKIN,
                                  INCE_BETON_SERIT_ORTAM_DEGISKENI,
                                  ince_beton_serit_maskesi,
                                  hb_konumu,
                                  HB_SEKIL_ESIGI,
                                  KararYumusatici,
                                  SARTNAME_IHA_UB_KENAR_M,
                                  yerel_konum_m,
                                  hedef_yok_reddi,
                                  rota_guven_reddi,
                                  BERABERLIK_BANDI,
                                  OLCEK_GUVEN_CARPANI,
                                  beraber_adaylar,
                                  OLCEK_KAYNAK_TELEMETRI,
                                  OLCEK_KAYNAK_ARAC,
                                  SENARYO_BOYUTLARI_M,
                                  olcek_gecerli_mi,
                                  olcek_kahini,
                                  olcek_guveni_uygula,
                                  rota_olcek_reddi, serit_no,
                                  rota_serit_karari,
                                  KAMERA_DUSEN_KARE_UST_SINIRI,
                                  KAMERA_DUSEN_KARE_BEKLEME_S,
                                  KAMERA_BITIS_KULLANICI,
                                  KAMERA_BITIS_DUSEN_KARE,
                                  KAMERA_BITIS_ACILAMADI,
                                  KAMERA_BITIS_SINYAL,
                                  MODEL_TUREV_SHA_YER_TUTUCU)

_here = Path(__file__).parent
MODEL_DIR = next(
    (p for p in [
        _here / "best_ncnn_model",
        _here.parent / "models" / "best_ncnn_model",
        _here / "rescuenet_seg_v1_ncnn",
        _here.parent / "models" / "rescuenet_seg_v1_ncnn",
    ] if p.exists()),
    _here / "best_ncnn_model",
)
# T73: kayit defteri dogrulamasi VARSAYILAN OLARAK ZORUNLUDUR. Gevsetmek
# icin `--kayit-dogrulamasiz` acikca verilmelidir; sessiz gevseme YOKTUR.
MODEL_KAYIT_ZORUNLU = True
RESULTS_DIR = _here / "results"
SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".bmp"}
SUPPORTED_VIDEO_EXT = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
# ── CIKARIM BOYU (imgsz) — TEK KAYNAK KAYIT DEFTERIDIR (S5 · madde 16) ──────
# ⚠ ESKIDEN BURASI CIPLAK BIR SABITTI (`INFER_SIZE = 512`) ve kayit defterinin
# `imgsz` alaniyla HICBIR YERDE kiyaslanmiyordu. Defter 640'a cevrilse burasi
# 512'de kalirdi ve HICBIR YERDE SES CIKMAZDI — defterin KENDI notundaki
# D-116/5 kusurunun ("surum v27'ye gecince cevrilmedi") birebir aynisi.
#
# ⚠ ICE AKTARMA ANINDA DOSYA OKUMAK RISKLIDIR: defter yoksa modulun HIC
# yuklenememesi kabul edilemez (`jetson_paket/` altinda `config/` YOKTUR).
# Bu yuzden kural FAIL-CLOSED ama YUMUSAK: okunamazsa YEDEK degere dusulur ve
# STDERR'e uyari basilir — sessizce devam EDILMEZ. Yukleme karari yine
# `model_kayit_dogrula` + `load_model` tarafindan fail-closed verilir.
INFER_SIZE_YEDEK = 512     # defter okunamazsa son care; TEK KAYNAK DEGILDIR


def _uyar(mesaj):
    """Gorunur uyari — stdout'a DEGIL stderr'e. Sessiz kalmaz."""
    print(f"UYARI: {mesaj}", file=sys.stderr, flush=True)


def _kayittan_imgsz(kok=None):
    """Etkin profilin `imgsz`i; okunamazsa None. Istisna FIRLATMAZ."""
    taban = Path(kok) if kok is not None else _here.parent
    kayit = taban / "config" / "model_registry.json"
    try:
        veri = json.loads(kayit.read_text(encoding="utf-8"))
        return int(veri["profiles"][veri["default_profile"]]["imgsz"])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return None


def _baslangic_imgsz():
    deger = _kayittan_imgsz()
    if deger is None:
        _uyar("kayit defterinden `imgsz` okunamadi; INFER_SIZE yedek degere "
              f"dusuldu ({INFER_SIZE_YEDEK}). TEK KAYNAK "
              "config/model_registry.json'dur.")
        return INFER_SIZE_YEDEK
    return deger


INFER_SIZE = _baslangic_imgsz()


def cikarim_boyu(istenen=None, kok=None):
    """Etkin cikarim boyu — ve `istenen` defterdekinden FARKLIYSA UYARI.

    S5 kapisi: "imgsz varsayilan disina cikarildiginda uyari basildigini
    goster." Bugun `rpi_inference` CLI'sinde `--imgsz` bayragi YOKTUR ve bu
    gorevde EKLENMEDI — amaci imgsz'i SABITLEMEK olan bir ise yeni bir
    degistirme kolu takmak ters yonde bir adim olurdu. Bunun yerine
    ORTAK COZUCU burasidir: ileride bir CLI/API yolu acilirsa oradan da
    gecmek zorunda kalacagi tek nokta budur ve uyari BURADA basilir.
    """
    taban = _kayittan_imgsz(kok)
    if taban is None:
        taban = INFER_SIZE
    if istenen is None:
        return int(taban)
    istenen = int(istenen)
    if istenen != int(taban):
        _uyar(f"CIKARIM BOYU VARSAYILAN DISINA CIKARILDI: kayit defteri "
              f"{taban}, istenen {istenen}. Model bu boyda kalibre EDILMEDI; "
              "sonuclar kayit defterindeki olculerle KIYASLANAMAZ.")
    return istenen

CLASS_COLORS = {
    0: (0, 200, 0),    # traversable — yesil
    1: (0, 0, 200),    # blocked     — kirmizi
}


def _inis_kaniti_modulu():
    """Inis/irtifa okuyucusunu repo ve duz Jetson paketinde tembel yukle.

    Repo yerlesiminde okuyucu ``comms/inis_kaniti.py`` altindadir; Jetson
    paket ureticisi ise onu ``rpi_inference.py`` ile ayni dizine kopyalar.
    Tembel yukleme, yalniz goruntu/FPS araclarini pymavlink kurulmadan da ice
    aktarilabilir tutar.
    """
    repo_okuyucu = _here.parent / "comms" / "inis_kaniti.py"
    if repo_okuyucu.is_file():
        repo_koku = str(_here.parent)
        eklendi = repo_koku not in sys.path
        if eklendi:
            sys.path.insert(0, repo_koku)
        try:
            return importlib.import_module("comms.inis_kaniti")
        finally:
            if eklendi:
                try:
                    sys.path.remove(repo_koku)
                except ValueError:
                    pass
    return importlib.import_module("inis_kaniti")


def _iha_sender_modulu():
    """K1 · telsiz halkasi: `comms/iha_sender` (repo) ya da duz paket kopyasi.

    YALNIZ --yks-hedef/--ika-hedef/--telsiz-seri verilince cagrilir; gonderici
    istenmeyen kosumda bu modul HIC ice aktarilmaz (davranis bayt-es).
    """
    repo_comms = _here.parent / "comms"
    if (repo_comms / "iha_sender.py").is_file():
        yol = str(repo_comms)
        eklendi = yol not in sys.path
        if eklendi:
            sys.path.insert(0, yol)
        try:
            return importlib.import_module("iha_sender")
        finally:
            if eklendi:
                try:
                    sys.path.remove(yol)
                except ValueError:
                    pass
    return importlib.import_module("iha_sender")


def _karari_yayinla(yayinci, open_path, path_conf, waypoints, kare_mpp,
                    karar_reddi):
    """Kare karari -> telsiz (K1). `yayinci` None ise HICBIR SEY yapmaz.

    Fail-closed: ret sebebi olan ya da yolu olmayan karar NO_ROUTE olur;
    OPEN_ROUTE guven kapisi IhaSender.send_open_route icindedir (cogaltilmaz).
    """
    if yayinci is None:
        return
    yayinci.karar(open_path, path_conf, waypoints, kare_mpp, karar_reddi)


class CanliOlcekSaglayici:
    """Taze MAVLink bagil irtifasini kareye ozgu metre/piksele cevirir.

    Okuyucu tazelik ve kaynak kimligi otoritesidir. Bu sinif son bilinen
    irtifayi saklamaz: okuyucu her karede ``None`` verirse olcek de ``None``
    olur. Goruntu genisligi infer boyutu degil, ``_preprocess`` tarafindan
    dondurulen gercek icerik kutusunun genisligidir.
    """

    def __init__(self, okuyucu, *, yatay_fov_derece=None, odak_px=None,
                 baglanti=None):
        if (yatay_fov_derece is None) == (odak_px is None):
            raise ValueError("FOV ve odaktan tam olarak biri verilmelidir")
        self.okuyucu = okuyucu
        self.yatay_fov_derece = yatay_fov_derece
        self.odak_px = odak_px
        self._baglanti = baglanti

    @classmethod
    def baglan(cls, adres, *, yatay_fov_derece=None, odak_px=None,
               beklenen_sysid=None):
        """MAVLink ucunu ac ve ortak ``BagilIrtifaOkuyucu``yu sahiplen."""
        inis_kaniti = _inis_kaniti_modulu()
        baglanti = inis_kaniti.mavlink_baglantisi_ac(adres)
        okuyucu = None
        try:
            okuyucu = inis_kaniti.BagilIrtifaOkuyucu(
                baglanti,
                TELEMETRI_IRTIFA_TAZELIK_S,
                beklenen_sysid=beklenen_sysid,
                durum_tazelik_s=ARAC_DURUM_TAZELIK_S,
            )
            if okuyucu.baslat() is not True:
                raise RuntimeError(
                    "MAVLink irtifa okuyucusu baslatilamadi; akis baska tuketicide")
            return cls(
                okuyucu,
                yatay_fov_derece=yatay_fov_derece,
                odak_px=odak_px,
                baglanti=baglanti,
            )
        except Exception:
            # Poller baslatildiktan sonra saglayici kurucusu hata verse bile
            # bağlantıyı canlı thread'in altından çekme. Önce tek tüketiciyi
            # durdur; durduğu doğrulanamıyorsa kaynak sızıntısı fail-closed daha
            # güvenlidir.
            durdu = True
            durdur = getattr(okuyucu, "durdur", None)
            if callable(durdur):
                try:
                    durdu = durdur() is True
                except Exception:
                    durdu = False
            kapat = getattr(baglanti, "close", None)
            if durdu and callable(kapat):
                try:
                    kapat()
                except Exception:
                    pass
            raise

    def kare_mpp(self, icerik_genisligi_px):
        """Bu karenin taze irtifasiyla mpp uret; hata/bayatlikta ``None``."""
        try:
            irtifa_m = self.okuyucu.irtifa_m()
        except Exception:
            return None
        if irtifa_m is None:
            return None
        return mpp_irtifadan(
            irtifa_m,
            icerik_genisligi_px,
            yatay_fov_derece=self.yatay_fov_derece,
            odak_px=self.odak_px,
        )

    __call__ = kare_mpp

    def kapat(self):
        """Sahip olunan MAVLink baglantisini varsa kapat."""
        durdur = getattr(self.okuyucu, "durdur", None)
        if callable(durdur):
            try:
                durdu = durdur()
            except Exception:
                return False
            # Poller join olmadan alttaki baglantiyi kapatmak yarista recv
            # hatasi ve belirsiz sahiplik uretir. Kaynak sizintisi, canli bir
            # thread'in altindan baglantiyi cekmekten daha guvenlidir.
            if durdu is not True:
                return False
        kapat = getattr(self._baglanti, "close", None)
        if callable(kapat):
            try:
                kapat()
            except Exception:
                return False
        self._baglanti = None
        return True


def _kare_olcegi(mpp, canli_olcek, icerik):
    """Canli kaynak varsa onu tek otorite yap; yoksa eski statik yolu koru."""
    if canli_olcek is None:
        return mpp
    try:
        uret = getattr(canli_olcek, "kare_mpp", None)
        if not callable(uret) and callable(canli_olcek):
            uret = canli_olcek
        if not callable(uret):
            return None
        return uret(icerik[2])
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════════════════
# T86 · OLCEK KAHINI URETIM YOLUNA BAGLI      (CONTRACTS SS5.4 · REVIEW_LOG D-136)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (D-136, olculdu): hakem ekraninin 7 kaynagindan 5'i TEK ve AYNI
# sebepten dusuyordu — `OLCEK_YOK`. Kahin T83'te yazilmis (D-126) ama ayni
# kayitta "uretim cagri yerlerine ve EKRANA BAGLANMADI" diye not dusulmustu.
#
# 🔴 KAPI GEVSEMEZ. `rota_olcek_reddi` hala olcek YOKSA reddeder; degisen tek
# sey olcegin DAHA COK karede TURETILEBILMESIDIR. Katman atlandikca guven
# carpani duser (1.00 / 0.70 / 0.86) ve kaynak karar nesnesine yazilir.
def _arac_kisa_kenari(bgr, arac_modeli, conf):
    """(kisa_kenar_px, not) — dedektor yoksa/patlarsa SEBEBIYLE birlikte doner.

    Sessiz dusus yasak oldugu icin "arac yok" ile "dedektor yok" AYRI
    raporlanir; kahinin `denenen` dokumune bu metin yazilir.
    """
    if arac_modeli is None:
        return None, "arac dedektoru (DOTA OBB) VERILMEDI"
    if bgr is None:
        return None, "kare goruntusu cozucuye verilmedi"
    try:
        # Ic ice bagimlilik yaratmamak icin GECIKMELI import. `arac_maskesi`
        # T83 onarimina kadar saha paketinde YOKTU ve bu katman sahada olu
        # kaliyordu; artik KOPYALAR'da, tests/test_jetson_comms_paketi kilitler.
        if __package__:
            from .arac_maskesi import arac_olcek_kenari
        else:
            from arac_maskesi import arac_olcek_kenari
    except ImportError as exc:
        return None, f"arac_maskesi modulu yok ({exc.__class__.__name__})"
    try:
        # T89: TEK KAYNAK. Esik, cikarim cozunurlugu, toplama kurali ve sebep
        # metni `arac_maskesi.arac_olcek_kenari` icinde durur; burada hicbiri
        # TEKRARLANMAZ (madde 16). Dedektor tek kez kosar.
        kenar, _n, sebep = arac_olcek_kenari(bgr, arac_modeli, conf=conf)
    except Exception as exc:                       # fail-closed: olcek uydurma
        return None, f"arac tespiti HATA verdi: {type(exc).__name__}: {exc}"
    return kenar, sebep


def kare_olcek_kahini(mpp, canli_olcek, icerik, *, bgr=None, arac_modeli=None,
                      senaryo=None, arena_sinir_px=None, arac_conf=0.25):
    """Uretim karar yolunun OLCEK cozucusu. -> kahin sozlugu (ASLA None).

    Katman 1 ONCE denenir: `_kare_olcegi` canli telemetriyi ya da cagiricinin
    verdigi statik/manifest olcegini dondurur; bu, SS5.2 uyarinca OTORITEDIR
    ve davranisi T86'da DEGISMEDI. Uretmezse katman 2 (arena siniri, senaryo
    BEYAN EDILMISSE) ve katman 3 (arac referansi) denenir.
    """
    beyan = _kare_olcegi(mpp, canli_olcek, icerik)
    if olcek_gecerli_mi(beyan):
        return {"mpp": float(beyan),
                "kaynak": OLCEK_KAYNAK_TELEMETRI,
                "guven_carpani": OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_TELEMETRI],
                "detay": ("canli telemetri" if canli_olcek is not None
                          else "cagirici beyani (statik/manifest)"),
                "denenen": [(OLCEK_KAYNAK_TELEMETRI, "URETTI")]}

    kisa_kenar, arac_notu = _arac_kisa_kenari(bgr, arac_modeli, arac_conf)
    kahin = olcek_kahini(arena_sinir_px=arena_sinir_px, senaryo=senaryo,
                         arac_kisa_kenar_px=kisa_kenar)
    if kahin["kaynak"] != OLCEK_KAYNAK_ARAC:
        # Kahin "sahnede olculebilir arac YOK" der; oysa sebep dedektorun
        # olmamasi da olabilir. Hakem ikisini ayirt edebilmeli.
        kahin["denenen"] = [(k, arac_notu if k == OLCEK_KAYNAK_ARAC else n)
                            for k, n in kahin["denenen"]]
    return kahin


# ════════════════════════════════════════════════════════════════════════════
# T73 · SAHA KODU PARAMETRIK       (CONTRACTS SS11.3 · REVIEW_LOG D-106)
# ════════════════════════════════════════════════════════════════════════════
# KUSUR (saha kuru kosusu): iki halka DUSUK ve ikisi de ayni sinif —
#   kamera         : "uretim girisi kaynagi PARAMETRIK almiyor:
#                     cv2.VideoCapture(0) SABIT"
#   model_yukleme  : "yuklenen agirlik kayit defterindeki profille eslesmiyor
#                     ve --model argumani yok"
# Sartname SS2.2.1 sistemlerin goreve MUHURLU KUTULAR icinde intikal etmesini
# sart kosar; muhurler hakem nezaretinde acilir. Yarisma gunu kamera indeksi ya
# da model dosyasi degisirse KAYNAK DOSYA DUZENLEMEK prosedure aykiridir.
#
# ⚠ VARSAYILAN CIPLAK YAZILMAZ (madde 16). Model varsayilani Jetson uretim
# manifestindeki `asil_model_pt` alanindan okunur — T62'de `scripts/jetson_fps.py`
# ayni tek-kaynak yolunu izliyor. Bu modul saha paketine BIREBIR kopyalandigi
# icin okuyucu BURADA durur; `jetson_fps.py` kendi kopyasini tasiyor ve ileride
# buradan import etmelidir (ayri gorev — o dosya T73'un izin listesinde YOK).

JETSON_MANIFEST_ADI = "jetson_derleme_manifest.json"


def _uretim_manifesti(kok=None):
    """Depo ve Jetson paketi topolojisinde AYNI uretim manifestini oku.

    Fail-closed: manifest yoksa, tekil degilse ya da bozuksa RuntimeError.
    Sessiz varsayilan URETILMEZ — sahada yanlis modelle ucmak bundan dogar.
    """
    import json as _json
    taban = Path(kok) if kok is not None else _here.parent
    adaylar = (
        taban / "models" / JETSON_MANIFEST_ADI,
        taban / "jetson_paket" / "models" / JETSON_MANIFEST_ADI,
        _here / JETSON_MANIFEST_ADI,          # saha paketi: kod/ ile yan yana
        _here.parent / "models" / JETSON_MANIFEST_ADI,
    )
    bulunan = []
    for yol in adaylar:
        if yol.is_file() and yol not in bulunan:
            bulunan.append(yol)
    if not bulunan:
        raise RuntimeError(
            f"Jetson uretim manifesti bulunamadi ({JETSON_MANIFEST_ADI}); "
            "model varsayilani turetilemez.")
    try:
        veri = _json.loads(bulunan[0].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise RuntimeError(
            f"Jetson uretim manifesti okunamadi: {bulunan[0]}") from exc
    if not isinstance(veri, dict):
        raise RuntimeError("Jetson uretim manifesti JSON nesnesi olmali")
    return veri, bulunan[0]


def varsayilan_model_yolu(kok=None):
    """`asil_model_pt` -> diskteki agirlik yolu. Ciplak ad YAZILMAZ."""
    veri, manifest = _uretim_manifesti(kok)
    ad = veri.get("asil_model_pt")
    if not isinstance(ad, str) or not ad.strip():
        raise RuntimeError(
            f"Uretim manifestinde `asil_model_pt` yok/gecersiz: {manifest}")
    ad = ad.strip()
    if Path(ad).name != ad or Path(ad).suffix.lower() != ".pt":
        raise RuntimeError(
            f"Uretim manifestinde `asil_model_pt` guvensiz/gecersiz: {ad!r}")
    for aday in (manifest.parent / ad, _here.parent / "models" / ad,
                 _here / ad):
        if aday.is_file():
            return aday
    raise RuntimeError(
        f"Manifest `{ad}` diyor ama agirlik diskte YOK "
        f"(bakilan: {manifest.parent}, {_here.parent / 'models'}).")


def kamera_kaynagi_coz(deger):
    """Kamera kaynagini coz: INDEKS (int) · CIHAZ YOLU · DOSYA.

    `cv2.VideoCapture` int ve str'yi farkli yorumlar; donusum TEK YERDE yapilir
    ki cagri yerleri "0" metnini cihaz dosyasi sanmasin.
    Fail-closed: None -> varsayilan indeks 0 (geriye uyum).
    """
    if deger is None:
        return 0
    if isinstance(deger, bool):
        raise ValueError("kamera kaynagi bool olamaz")
    if isinstance(deger, int):
        return int(deger)
    metin = str(deger).strip()
    if not metin:
        return 0
    try:
        return int(metin)                    # "0", "2" -> indeks
    except ValueError:
        return metin                         # /dev/video1 · rtsp:// · dosya


def model_kayit_dogrula(model_yolu, kok=None, calisan_imgsz=None):
    """Yuklenen agirligi `config/model_registry.json` ile KIYASLA.

    -> (uyumlu: bool, detay: dict). Karar VERMEZ; karari `load_model` verir.
    Kayit defteri YOKSA "dogrulanamadi" doner — yoklugu UYUM SAYMAZ.

    ⚠ S5: ARTIK `imgsz` DE KIYASLANIR. Eskiden yalniz dosya ADI kiyaslaniyordu;
    defterin `imgsz`i 640'a cekilse `INFER_SIZE` 512'de kalir ve HICBIR YERDE
    ses cikmazdi. `path` hangi fail-closed mantikla ele aliniyorsa `imgsz` de
    ayni sekilde ele alinir: alan YOKSA ya da UYUSMUYORSA `uyumlu=False`.
    `calisan_imgsz` verilmezse modulun etkin `INFER_SIZE`i kullanilir.
    """
    import json as _json
    taban = Path(kok) if kok is not None else _here.parent
    kayit = taban / "config" / "model_registry.json"
    detay = {"kayit_defteri": str(kayit), "yuklenen": str(model_yolu)}
    if not kayit.is_file():
        detay["durum"] = "kayit_defteri_yok"
        return False, detay
    try:
        veri = _json.loads(kayit.read_text(encoding="utf-8"))
        profil_adi = veri["default_profile"]
        profil = veri["profiles"][profil_adi]
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        detay["durum"] = f"kayit_defteri_okunamadi: {exc}"
        return False, detay
    beklenen = profil.get("path")
    beklenen_imgsz = profil.get("imgsz")
    calisan = INFER_SIZE if calisan_imgsz is None else calisan_imgsz
    detay.update({"profil": profil_adi, "beklenen": beklenen,
                  "beklenen_sha256": profil.get("sha256"),
                  "beklenen_imgsz": beklenen_imgsz,
                  "calisan_imgsz": calisan})
    if not isinstance(beklenen, str):
        detay["durum"] = "profilde `path` yok"
        return False, detay
    if beklenen_imgsz is None:
        detay["durum"] = "profilde `imgsz` yok"
        return False, detay
    try:
        imgsz_uyumlu = int(beklenen_imgsz) == int(calisan)
    except (TypeError, ValueError):
        detay["durum"] = "profilde `imgsz` gecersiz"
        return False, detay
    ad_uyumlu = Path(beklenen).name == Path(model_yolu).name
    if not ad_uyumlu:
        # T143 (D-284): ad uymuyorsa ANINDA red YOK — once profilin `turevler`
        # sozlugune bakilir (.engine/.onnx ayni soy). Eskiden her .engine
        # "ESLESMIYOR" ile reddediliyor, Jetson'da TensorRT ancak
        # --kayit-dogrulamasiz ile (fail-closed KAPATILARAK) yukleniyordu.
        return _turev_kayit_dogrula(profil, model_yolu, calisan, detay)
    if not imgsz_uyumlu:
        detay["durum"] = "IMGSZ ESLESMIYOR"
    else:
        detay["durum"] = "eslesti"
    return imgsz_uyumlu, detay


def _sha256_dosya(yol):
    import hashlib
    ozet = hashlib.sha256()
    with Path(yol).open("rb") as akis:
        for parca in iter(lambda: akis.read(1024 * 1024), b""):
            ozet.update(parca)
    return ozet.hexdigest()


def _sha256_dogrulanmis_mi(ozet):
    """Yer tutucu / bos / bicimsiz ozet DOGRULANMAMIS sayilir (fail-closed)."""
    if not isinstance(ozet, str) or ozet == MODEL_TUREV_SHA_YER_TUTUCU or len(ozet) != 64:
        return False
    try:
        int(ozet, 16)
    except ValueError:
        return False
    return True


def _turev_kayit_dogrula(profil, model_yolu, calisan_imgsz, detay):
    """T143: `.engine`/`.onnx` turevini profilin `turevler` kaydiyla kiyasla.

    `codes/model_registry.py::turev_dogrula` ile AYNI kural (saha paketinde
    o modul yoktur; ikisi `tests/test_t143_turev_ve_kamera.py`de ayni
    girdilerde ayni hukmu vermeye zorlanir). Fail-closed siralamasi:
      kayitsiz ad -> ESLESMIYOR · yetim kaynak -> TUREV KAYNAGI ESLESMIYOR ·
      yer tutucu -> TUREV SHA YER TUTUCU · imgsz -> IMGSZ ESLESMIYOR ·
      disk ozeti farkli -> TUREV SHA ESLESMIYOR · hepsi tamam -> turev_eslesti
    """
    yol = Path(model_yolu)
    turevler = profil.get("turevler")
    detay["turev"] = yol.name
    if not isinstance(turevler, dict) or yol.name not in turevler:
        detay["durum"] = "ESLESMIYOR"
        return False, detay
    kayit = turevler[yol.name]
    detay.update({"beklenen_sha256": kayit.get("sha256"),
                  "beklenen_imgsz": kayit.get("imgsz"),
                  "kaynak": kayit.get("kaynak")})
    if kayit.get("kaynak") != profil.get("path") or \
            kayit.get("kaynak_sha256") != profil.get("sha256"):
        detay["durum"] = "TUREV KAYNAGI ESLESMIYOR"
        return False, detay
    if not _sha256_dogrulanmis_mi(kayit.get("sha256")):
        detay["durum"] = "TUREV SHA YER TUTUCU (dogrulanmamis)"
        return False, detay
    try:
        if int(kayit.get("imgsz")) != int(calisan_imgsz):
            detay["durum"] = "IMGSZ ESLESMIYOR"
            return False, detay
    except (TypeError, ValueError):
        detay["durum"] = "turevde `imgsz` gecersiz"
        return False, detay
    if not yol.is_file():
        detay["durum"] = "turev dosyasi yok"
        return False, detay
    gercek = _sha256_dosya(yol)
    detay["gercek_sha256"] = gercek
    if gercek != kayit["sha256"]:
        detay["durum"] = "TUREV SHA ESLESMIYOR"
        return False, detay
    detay["durum"] = "turev_eslesti"
    return True, detay


def load_model(model_yolu=None, kok=None, kayit_zorunlu=None, ayrinti=False):
    """Uretim agirligini yukle. Varsayilan MANIFESTTEN gelir (madde 16).

    ⚠ FAIL-CLOSED (T73/3): yuklenen agirlik kayit defterindeki etkin profille
    UYUSMUYORSA SESSIZCE DEVAM EDILMEZ. Sessiz devam, sahada YANLIS MODELLE
    ucmak demektir; D-89'un besinci ucu tam bu siniftandi.
    `kayit_zorunlu=False` verilirse uyari basilir ama devam edilir — bu kapi
    yalniz ACIKCA istenerek gevsetilebilir, varsayilan olarak DEGIL.
    """
    if model_yolu is None:
        yol = varsayilan_model_yolu(kok)
    else:
        yol = Path(model_yolu)
    if not yol.exists():
        raise RuntimeError(f"Model agirligi bulunamadi: {yol}")

    uyumlu, detay = model_kayit_dogrula(yol, kok)
    if kayit_zorunlu is None:
        kayit_zorunlu = MODEL_KAYIT_ZORUNLU
    if not uyumlu:
        mesaj = (
            "MODEL KAYIT DOGRULAMASI BASARISIZ — fail-closed.\n"
            f"  yuklenmek istenen : {yol}\n"
            f"  kayit defteri     : {detay.get('kayit_defteri')}\n"
            f"  etkin profil      : {detay.get('profil')}\n"
            f"  profilin bekledigi: {detay.get('beklenen')}\n"
            f"  profilin imgsz'i  : {detay.get('beklenen_imgsz')}\n"
            f"  calisan imgsz     : {detay.get('calisan_imgsz')}\n"
            f"  durum             : {detay.get('durum')}\n"
            "Iki bildirim CELISIYOR. Sahada hangi agirligin uctugunu bilmeden\n"
            "devam etmek yasaktir; ya kayit defterini ya --model'i duzeltin."
        )
        if kayit_zorunlu:
            raise RuntimeError(mesaj)
        print("UYARI: " + mesaj)
    model = YOLO(str(yol), task="segment")
    # ⚠ GERIYE UYUM: donus degeri MODELDIR. `codes/test_batch.py:139`,
    # `drone/rpi_yayin.py:415` gibi cagri yerleri `load_model()` deyip modeli
    # bekliyor; arity degistirmek onlari SESSIZCE bozardi (bir mevcut test bunu
    # zaten yakaladi). Ek bilgi ACIKCA istenir: `ayrinti=True`.
    return (model, yol, detay) if ayrinti else model


def get_masks(results, h, w, min_conf=None, sinif_idler=(0, 1),
              ince_beton_serit=None):
    """Her sinif icin (h, w) cozunurlugunde binary mask doner.
    min_conf verilirse yalniz guveni >= min_conf tespitler dahil edilir → model DUSUK
    esikle BIR KEZ kosturulup ayni sonuctan farkli esikler suzulebilir (2. predict yok).

    sinif_idler: maskesi uretilecek sinif idleri. Varsayilan (0, 1) ESKI DAVRANISIN
    BIREBIR AYNISIDIR — hicbir mevcut cagri yeri degismez. Costmap hatti ek engel
    siniflari icin genisletir (or. COCO araba/kamyon: sinif_idler=(0,1,2,5,7)).
    Eskiden {0,1} sabit kodluydu ve id >= 2 olan her maske SESSIZCE atiliyordu.

    ince_beton_serit (T153, ON_KAYIT §13): None -> ortam degiskeni
    `INCE_BETON_SERIT_ORTAM_DEGISKENI` ("1"/"0"), o da yoksa sozlesme sabiti
    `INCE_BETON_SERIT_ETKIN` (varsayilan KAPALI). Kapaliyken cikti T153
    oncesiyle BAYT-ES aynidir (tests/test_t153_ince_beton_serit.py)."""
    masks = {int(c): np.zeros((h, w), dtype=np.uint8) for c in sinif_idler}
    r = results[0]
    if r.masks is not None:
        confs = r.boxes.conf
        for i, cls in enumerate(r.boxes.cls):
            cls_id = int(cls)
            if cls_id not in masks:
                continue
            if min_conf is not None and float(confs[i]) < min_conf:
                continue
            m = r.masks.data[i].cpu().numpy()
            m_up = cv2.resize(m, (w, h))
            masks[cls_id] = np.maximum(masks[cls_id],
                                       (m_up > 0.5).astype(np.uint8))
    # T67 (REVIEW_LOG D-92, D-93): KATMAN 2 ince bariyer dedektoru.
    # Model bariyeri GORMUYOR (gercek arenada %0,0) ve OGRENEMEZ de: uretec
    # bariyeri yalniz ZATEN KAPALI seritlere koyuyor (D-93). Klasik dedektor
    # bu yuzden buraya, ENGEL katmanina eklenir. Maske uretimi `r.masks is
    # None` dalinda da CALISIR — model hicbir sey gormese bile bariyer engel
    # olarak isaretlenmelidir.
    _ince_bariyeri_ekle(masks, r, h, w)
    # T153 (ON_KAYIT §13, D-289/D-290): KATMAN 2 ince beton serit cikaricisi.
    # Model beton drenaj kanalini ZEMIN sayiyor ve rota kanalin ustune dusuyor.
    # T67 ile AYNI kalip: yalniz ENGEL katmanina OR — serbest alan yalniz
    # kuculur. Varsayilan KAPALI; acikken bir kez stderr'e yazilir ki olcum
    # loglari hangi kipte kosuldugunu KANITLASIN.
    if _ince_beton_serit_etkin(ince_beton_serit):
        _ince_beton_seridi_ekle(masks, r, h, w)
    return masks


def _ince_beton_serit_etkin(istek=None):
    """T153 acik mi? Oncelik: parametre > ortam degiskeni > sozlesme sabiti."""
    if istek is not None:
        return bool(istek)
    ortam = os.environ.get(INCE_BETON_SERIT_ORTAM_DEGISKENI)
    if ortam is not None and ortam.strip() != "":
        return ortam.strip() == "1"
    return bool(INCE_BETON_SERIT_ETKIN)


_INCE_BETON_BILDIRILDI = False


def _ince_beton_seridi_ekle(masks, r, h, w):
    """Ince beton seritleri ENGEL maskesine EKLE (madde 15: yalniz buyutur).

    `_ince_bariyeri_ekle` ile birebir ayni fail-safe: goruntu yoksa ya da
    dedektor None donerse HICBIR SEY eklenmez, hicbir sey cikarilmaz.
    """
    global _INCE_BETON_BILDIRILDI
    engel = int(BARIYER_ENGEL_SINIFI)
    if engel not in masks:
        return
    goruntu = getattr(r, "orig_img", None)
    if goruntu is None:
        return
    goruntu = np.asarray(goruntu)
    if goruntu.ndim != 3 or goruntu.shape[2] != 3 or goruntu.size == 0:
        return
    if not _INCE_BETON_BILDIRILDI:
        _INCE_BETON_BILDIRILDI = True
        print("T153: ince beton serit cikaricisi ACIK (get_masks -> engel OR)",
              file=sys.stderr, flush=True)
    serit = ince_beton_serit_maskesi(goruntu)
    if serit is None or serit.size == 0 or not serit.any():
        return
    if serit.shape != (h, w):
        serit = cv2.resize(serit, (w, h), interpolation=cv2.INTER_NEAREST)
    masks[engel] = np.maximum(masks[engel], (serit > 0).astype(np.uint8))


def _ince_bariyeri_ekle(masks, r, h, w):
    """Bariyer kollarini ENGEL maskesine EKLE (madde 15: yalniz buyutur).

    Engel katmanini buyutmek serbest alani (`zemin AND NOT engel`) yalniz
    KUCULTUR — CONTRACTS SS2'nin monotonluk sozlesmesine uygundur.
    Goruntu yoksa (sahte model, eski sonuc nesnesi) SESSIZCE atlanir; bu
    fail-safe'tir: hicbir sey EKLENMEZ, hicbir sey CIKARILMAZ.
    """
    engel = int(BARIYER_ENGEL_SINIFI)
    if engel not in masks:
        return
    goruntu = getattr(r, "orig_img", None)
    if goruntu is None:
        return
    goruntu = np.asarray(goruntu)
    if goruntu.ndim != 3 or goruntu.shape[2] != 3 or goruntu.size == 0:
        return
    kol = ince_bariyer_maskesi(goruntu)
    if kol is None or kol.size == 0 or not kol.any():
        return
    if kol.shape != (h, w):
        kol = cv2.resize(kol, (w, h), interpolation=cv2.INTER_NEAREST)
    masks[engel] = np.maximum(masks[engel], (kol > 0).astype(np.uint8))


def draw_masks(image_bgr, masks):
    """Traversable=yesil, blocked=kirmizi renkli maske overlay."""
    vis = image_bgr.copy()
    overlay = vis.copy()
    for cls_id, mask in masks.items():
        if mask.sum() == 0:
            continue
        color = CLASS_COLORS.get(cls_id, (128, 128, 128))
        overlay[mask > 0] = color
    return cv2.addWeighted(vis, 0.5, overlay, 0.5, 0)


def _bandda_gorunur_en_genis(band, y0, onceki, gecilebilir, k=64):
    """Bantta, ONCEKI waypoint'ten GORUNEN en genis noktayi sec.

    NEDEN (REVIEW_LOG D-28): eski kod her bandin distance-transform argmax'ini
    korlemesine waypoint yapiyordu. Ardisik iki bandin maksimumu iki AYRI
    koridora dusebiliyor ve aralarindaki dogru engelin ustunden geciyordu —
    olculdu: waypoint 3 (122,399) sol koridorda, waypoint 4 (520,240) sag
    koridorda, aradaki kenar 119 engel pikselinin uzerinden geciyordu.

    Adaylar aciklik sirasina gore denenir; ilk GORUNEN secilir. Hicbiri gorunmuyorsa
    None doner — bu bant onceki waypoint'e bagli degildir.
    """
    duz = band.ravel()
    n = min(int(k), duz.size)
    if n <= 0:
        return None
    idx = np.argpartition(duz, -n)[-n:]
    idx = idx[np.argsort(duz[idx])[::-1]]      # aciklik: buyukten kucuge
    genislik = band.shape[1]
    for j in idx:
        if duz[j] <= 0.5:
            break                               # kalanlar zaten koridor disi
        ly, lx = divmod(int(j), genislik)
        aday = (int(lx), int(y0 + ly))
        if _gorus_hatti(onceki, aday, gecilebilir):
            return aday

    # top-K YANLIS NEGATIF olabilir: bandin en genis k pikseli uzak bir koridorda
    # toplanmissa, onceki waypoint'in tam ustundeki gecerli nokta kacirilir ve
    # halka gereksiz yere "karar yok" der. Duz devam eden koridor icin ucuz bir
    # ikinci sans: onceki waypoint'e x'te EN YAKIN koridor pikselini dene.
    satir = int(np.argmax(band.max(axis=1) > 0.5)) if (band > 0.5).any() else None
    if satir is None:
        return None
    for satir_no in (satir, band.shape[0] // 2, band.shape[0] - 1):
        sutunlar = np.flatnonzero(band[satir_no] > 0.5)
        if sutunlar.size == 0:
            continue
        en_yakin = int(sutunlar[np.argmin(np.abs(sutunlar - onceki[0]))])
        aday = (en_yakin, int(y0 + satir_no))
        if _gorus_hatti(onceki, aday, gecilebilir):
            return aday
    return None


def _kenarlar_guvenli(waypoints, gecilebilir, engel_ham=None):
    """Her ARDISIK waypoint cifti gercekten baglantili mi?

    D-28'in son kapisi: iki ucu serbest olan bir kenar yine de engelin ustunden
    gecebilir. `_gorus_hatti` cizgideki HER pikselin serbest oldugunu dogrular;
    engel maskesi verilmisse ayrica HAM engele temas denetlenir (rota_dogrula
    ile ayni olcut).
    """
    for a, b in zip(waypoints, waypoints[1:]):
        if not _gorus_hatti(a, b, gecilebilir):
            return False
        if engel_ham is None:
            continue
        h, w = engel_ham.shape
        sol, sag = min(a[0], b[0]), max(a[0], b[0])
        ust, alt = min(a[1], b[1]), max(a[1], b[1])
        if not (0 <= sol and sag < w and 0 <= ust and alt < h):
            return False
        cizgi = np.zeros((alt - ust + 1, sag - sol + 1), np.uint8)
        cv2.line(cizgi, (a[0] - sol, a[1] - ust), (b[0] - sol, b[1] - ust),
                 1, thickness=1, lineType=cv2.LINE_8)
        if bool((engel_ham[ust:alt + 1, sol:sag + 1][cizgi > 0] > 0).any()):
            return False
    return True


def _uc_bant_temas_genisligi(koridor, icerik, taraf):
    """Icerik uc bandinda temas edilen benzersiz x sutunu sayisini dondur."""
    x0, y0, genislik, yukseklik = icerik
    bant_h = hedef_bant_yuksekligi(yukseklik)
    if taraf == "ust":
        bant = koridor[y0:y0 + bant_h, x0:x0 + genislik]
    elif taraf == "alt":
        bant = koridor[y0 + yukseklik - bant_h:y0 + yukseklik,
                       x0:x0 + genislik]
    else:
        raise ValueError(f"bilinmeyen uc bant tarafi: {taraf}")
    if bant.size == 0:
        return 0
    return int(np.count_nonzero(np.any(bant > 0, axis=0)))


def _uc_bant_temasi_yeterli(koridor, icerik, taraf):
    """Koridorun icerik uc bandina yeterli GENISLIKTE temasini denetle.

    Tek piksel temas guvenlik kaniti degildir. CONTRACTS.md SS6.3/K-A geregi
    temas, bant icinde gorulen farkli x sutunlarinin icerik genisligine oranidir.
    ``taraf`` yalniz ``ust`` (hedef) veya ``alt`` (baslangic) olabilir.
    """
    genislik = icerik[2]
    temas_genisligi = _uc_bant_temas_genisligi(koridor, icerik, taraf)
    return bant_temasi_yeterli_mi(temas_genisligi, genislik)


def _koridor_alani_yeterli(koridor, icerik_w, icerik_h, min_area_ratio):
    """Alan esigini letterbox tuvaliyle degil gercek icerikle karsilastir."""
    return int(koridor.sum()) >= min_area_ratio * icerik_w * icerik_h


def _uc_tohum_maskeleri(koridor, icerik):
    """Ayni koridorun alt baslangic ve ust hedef tohumu maskelerini uret."""
    x0, y0, genislik, yukseklik = icerik
    bant_h = hedef_bant_yuksekligi(yukseklik)
    alt = np.zeros_like(koridor, dtype=np.uint8)
    ust = np.zeros_like(koridor, dtype=np.uint8)
    alt[y0 + yukseklik - bant_h:y0 + yukseklik,
        x0:x0 + genislik] = koridor[
            y0 + yukseklik - bant_h:y0 + yukseklik,
            x0:x0 + genislik] > 0
    ust[y0:y0 + bant_h, x0:x0 + genislik] = (
        koridor[y0:y0 + bant_h, x0:x0 + genislik] > 0)
    return alt, ust


def _plan_hucre_sayisi(sekil, adim):
    """MIN-havuzlu plan izgarasinin gercek hucre sayisini dondur."""
    h, w = sekil
    return (h // adim) * (w // adim)


def _plan_adimlari(ilk_adim, sekil, hucre_butcesi=ROTA_PLAN_MAKS_HUCRE):
    """A* denemelerini baglayici toplam hucre butcesi icinde uret.

    Once morfolojik acma olceginden turetilen adim denenir. Bu izgara bile
    butceyi asiyorsa adim kabalastirilir. Kalan butce varsa, mevcut adimdan daha
    ince ve butceye sigan EN INCE ikinci izgara secilir. Boylece dar koridor icin
    bir iyilestirme sansi korunur; tam cozunurluge kosulsuz inilip GUI worker'i
    saniyelerce bloke edilmez.
    """
    h, w = map(int, sekil)
    butce = max(1, int(hucre_butcesi))
    adim = max(1, int(ilk_adim))
    en_buyuk_adim = max(1, min(h, w))
    while (adim <= en_buyuk_adim
           and _plan_hucre_sayisi((h, w), adim) > butce):
        adim += 1
    if adim > en_buyuk_adim:
        return []

    adimlar = []
    kalan = butce
    while adim >= 1:
        hucre = _plan_hucre_sayisi((h, w), adim)
        if hucre < 1 or hucre > kalan:
            break
        adimlar.append(adim)
        kalan -= hucre
        if adim == 1 or kalan < 1:
            break

        # Bir sonraki denemede kalan butceye sigan en ince (en kucuk) adimi
        # sec. Aday mutlaka mevcut adimdan daha ince olmali.
        sonraki = next(
            (aday for aday in range(1, adim)
             if 0 < _plan_hucre_sayisi((h, w), aday) <= kalan),
            None,
        )
        if sonraki is None:
            break
        adim = sonraki
    return adimlar


def _tohum_hucresi_ankoru(tohum, dist, hucre, adim):
    """Plan hucresindeki gercek uc-band pikselini waypoint ankru olarak sec."""
    r, c = hucre
    y0, y1 = r * adim, min((r + 1) * adim, tohum.shape[0])
    x0, x1 = c * adim, min((c + 1) * adim, tohum.shape[1])
    aday = tohum[y0:y1, x0:x1] > 0
    if not aday.any():
        return None
    yerel_y, yerel_x = np.nonzero(aday)
    aciklik = dist[y0:y1, x0:x1][yerel_y, yerel_x]
    secilen = int(np.argmax(aciklik))
    return x0 + int(yerel_x[secilen]), y0 + int(yerel_y[secilen])


def _bagli_koridor_yolu(koridor, icerik, dist, ilk_plan_adimi,
                        hedef_tohumu=None):
    """Uclari bagli koridorda, ornekleme sayisindan bagimsiz guvenli yol kur.

    ``_bagli_mi`` karari tam cozunurlukte verir. A* yalniz bu baglantinin somut
    piksel zincirini uretir. Plan izgarasi MIN-havuzlandigi icin kaba hucre ancak
    tum pikselleri serbestse kullanilir; kalan hucre butcesi varsa daha ince bir
    izgara da denenir. Boylece ``n_waypoints`` guvenlik kararina girmez ve GUI
    worker'i sinirsiz tam-cozunurluk A* ile bloke edilmez.
    """
    alt_tohum, ust_tohum = _uc_tohum_maskeleri(koridor, icerik)
    # T72: HB bulunduysa A* HEDEFI ust bant DEGIL, HB BOLGESIDIR. Sartname
    # SS2.2.6 gorevi "IKA'nin HB SINIRLARI ICINE girmesi" diye tanimlar; ust
    # banda varmak gorevi tamamlamaz. Tohum koridorla KESISTIRILIR: HB
    # koridora bagli degilse baglanti kapisi zaten reddeder (uydurma yapilmaz).
    if hedef_tohumu is not None:
        kesisim = (np.asarray(hedef_tohumu) > 0) & (koridor > 0)
        if kesisim.any():
            ust_tohum = kesisim.astype(np.uint8)
    alt_px = int(np.count_nonzero(alt_tohum))
    ust_px = int(np.count_nonzero(ust_tohum))
    if not _bagli_mi(koridor, alt_tohum, ust_tohum):
        return None, (
            "Baslangic ve hedef tohumlari ayni koridor bileseninde degil; "
            f"olculen alt_tohum={alt_px}px, ust_tohum={ust_px}px."
        )

    ys, xs = np.nonzero(koridor)
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    roi_dist = dist[y0:y1, x0:x1]
    roi_alt = alt_tohum[y0:y1, x0:x1]
    roi_ust = ust_tohum[y0:y1, x0:x1]
    roi_h, roi_w = roi_dist.shape
    denenen = []
    plan_adimlari = _plan_adimlari(
        ilk_plan_adimi, (roi_h, roi_w), ROTA_PLAN_MAKS_HUCRE)

    for adim in plan_adimlari:
        plan_hucre = _plan_hucre_sayisi((roi_h, roi_w), adim)
        denenen.append((adim, plan_hucre))
        dt_plan, _ = plan_izgarasi(roi_dist, None, adim)
        if dt_plan.size == 0:
            continue
        gecilebilir_plan = dt_plan > 0
        hp, wp = gecilebilir_plan.shape
        baslangic_plan = (
            _tohum_plan_izgarasi(roi_alt, hp, wp, adim)
            & gecilebilir_plan)
        hedef_plan = (
            _tohum_plan_izgarasi(roi_ust, hp, wp, adim)
            & gecilebilir_plan)
        if not baslangic_plan.any() or not hedef_plan.any():
            continue

        yol_izgara = astar(
            gecilebilir_plan, dt_plan, hedef_plan, baslangic_plan,
            adim_m=float(adim), r_gerekli_m=0.0,
            doyum_m=max(1.0, float(dt_plan.max())),
        )
        if not yol_izgara:
            continue

        bas_ankor = _tohum_hucresi_ankoru(
            roi_alt, roi_dist, yol_izgara[0], adim)
        hedef_ankor = _tohum_hucresi_ankoru(
            roi_ust, roi_dist, yol_izgara[-1], adim)
        if bas_ankor is None or hedef_ankor is None:
            continue

        yol_px = [
            (x0 + min(roi_w - 1, int((c + 0.5) * adim)),
             y0 + min(roi_h - 1, int((r + 0.5) * adim)))
            for r, c in yol_izgara
        ]
        bas_ankor = (x0 + bas_ankor[0], y0 + bas_ankor[1])
        hedef_ankor = (x0 + hedef_ankor[0], y0 + hedef_ankor[1])
        if yol_px[0] != bas_ankor:
            yol_px.insert(0, bas_ankor)
        if yol_px[-1] != hedef_ankor:
            yol_px.append(hedef_ankor)
        # yol_duzelt'in string-pulling asamasi her kisayolu gorus hattiyla
        # kanitlar. Aci esigi 0, ara koseyi ikinci kez korlemesine atlamaz.
        kanonik = yol_duzelt(
            yol_px, koridor > 0,
            wp_aralik_px=float(max(koridor.shape) * 2),
            aci_esigi_derece=0.0,
            maks_wp=max(2, len(yol_px)),
            # T94 (D-154/D-156/D-157): kiris, yerine gectigi alt yoldan
            # BELIRGIN olarak daha dar olmamali. `dist` TAM COZUNURLUK mesafe
            # donusumudur ve `yol_px` de tam goruntu koordinatlarindadir.
            # Verilmezse string-pulling rotayi tek duz kirise indirip emniyet
            # payini yiyordu (260 karenin 213'unde 2 dugum; kayip medyan 4 px).
            dt_px=dist,
        )
        ilk_x, ilk_y = kanonik[0] if kanonik else (-1, -1)
        son_x, son_y = kanonik[-1] if kanonik else (-1, -1)
        uclar_ankorlu = (
            0 <= ilk_y < alt_tohum.shape[0]
            and 0 <= ilk_x < alt_tohum.shape[1]
            and bool(alt_tohum[ilk_y, ilk_x])
            and 0 <= son_y < ust_tohum.shape[0]
            and 0 <= son_x < ust_tohum.shape[1]
            and bool(ust_tohum[son_y, son_x])
        )
        if (len(kanonik) >= 2 and uclar_ankorlu
                and _kenarlar_guvenli(kanonik, koridor)):
            return kanonik, None

    return None, (
        "Koridor uclari bagli, ancak dogrulanmis waypoint zinciri "
        f"kurulamadi; olculen alt_tohum={alt_px}px, ust_tohum={ust_px}px, "
        f"plan_hucre_butcesi={ROTA_PLAN_MAKS_HUCRE}, "
        f"denenen_plan_adim_hucre={denenen}."
    )


def _rotayi_ornekle(kanonik, n_waypoints, koridor):
    """Kanonik guvenli yolu karari degistirmeden istenen yogunluga getir."""
    hedef = max(2, int(n_waypoints))
    if len(kanonik) >= hedef:
        return list(kanonik)

    # _maks_aralikla_bol guvenli segmentlerin KENDI LINE_8 piksellerinden
    # ornekler. Ikili arama yalniz cikti yogunlugunu ayarlar; karar kanonik
    # yol uzerinde daha once verilmistir.
    alt = 1.0
    ust = float(np.hypot(*koridor.shape)) * 2.0 + 1.0
    en_iyi = list(kanonik)
    iterasyon = max(1, int(np.ceil(np.log2(max(2.0, ust - alt)))))
    for _ in range(iterasyon):
        orta = (alt + ust) / 2.0
        aday = _maks_aralikla_bol(
            kanonik, orta, int(koridor.size), koridor)
        if len(aday) > hedef:
            alt = orta
        else:
            en_iyi = aday
            ust = orta
    if len(en_iyi) >= 2 and _kenarlar_guvenli(en_iyi, koridor):
        return en_iyi
    return list(kanonik)


def _rota_pikselleri(rota):
    """Rotanin LINE_8 piksel dizisi — waypoint DUGUMLERI degil, tum cizgi.

    Karar ornekleme sayisindan bagimsiz olmalidir (CONTRACTS SS6.4/5).
    Dugumlerden ornekleseydik `n_waypoints` degisince olcum de degisirdi;
    segmentlerin kendi rasterizasyonu ayni polyline icin degismez.
    Rasterizasyon `_gorus_hatti` / `rota_dogrula` ile AYNI kaynaktan
    (`_bresenham_noktalari`) gelir — ikinci bir yuvarlama uretilmez.
    """
    if not rota:
        return []
    pikseller = [(int(rota[0][0]), int(rota[0][1]))]
    for a, b in zip(rota, rota[1:]):
        pikseller.extend(_bresenham_noktalari(a, b)[1:])
    return pikseller


def _rota_serit_olcumu(rota, dist, icerik):
    """Serit ve darbogazi ROTANIN KENDISINDEN olc (T31 / T32).

    NEDEN (REVIEW_LOG D-41): `open_path` ve `confidence` koridorun UST %30
    bandindan turetiliyordu. Olculdu: 67 gercek karenin 67'sinde yayinlanan
    etiket rotanin GERCEKTEN gectigi seritle uyusmuyordu (etiket hep 2; rota
    32 karede serit 1, 35 karede serit 3). `road` yalnizca ekran etiketi
    degil, IKA'nin planlama girdisidir (`comms/ika_receiver.py:11`), bu
    yuzden rotanin kendisinden okunur.

    🔴 YAYIN ALANI DEGISTI (T155 · 2026-08-26 · REVIEW_LOG D-296).
    `road` artik `serit_karari`dir (`karar_sozlesmesi.rota_serit_karari`,
    rotanin govdesi). `darbogaz_serit` TANI alani olarak kalir. Gerekce ve
    olculen sayilar ortak fonksiyonun docstring'indedir; ozeti: yer gercekli
    15 sahnede `darbogaz_serit` 6/15, `serit_karari` 15/15.

    Doner (rota olculemezse ``None``):
      serit_karari   : rotanin GOVDESINI tasiyan serit  -> yayinlanan `road`
      darbogaz_serit : rotanin EN DAR gectigi serit (TANI — artik yayinlanmaz)
      baskin_serit   : `serit_karari` ile AYNI sayi, istatistigin kendi adi
      seritler       : serit basina rota pikseli sayisi (n1, n2, n3)
      darbogaz_px    : rota boyunca olculen en kucuk aciklik (dt yaricapi)
      darbogaz_xy    : o acikligin olculdugu piksel
      serit_min_px   : serit basina en kucuk aciklik (None = rota o seritte yok)
      cok_seritli    : rota birden fazla seride giriyor mu
    """
    icerik_x0, _, icerik_w, _ = icerik
    h, w = dist.shape
    pikseller = _rota_pikselleri(rota)
    if not pikseller:
        return None
    # Kirpma bir kez yapilir ve serit sayimi ile darbogaz olcumu AYNI piksel
    # listesini gorur; yoksa iki olcu farkli koordinatlardan turer.
    kirpilmis = [(min(w - 1, max(0, int(px))), min(h - 1, max(0, int(py))))
                 for px, py in pikseller]
    # TEK TANIM (madde 16): yayinlanan serit karari burada URETILMEZ, ortak
    # fonksiyondan gelir — `rota_bul` tarafi da ayni fonksiyonu cagirir.
    serit_karari, sayim = rota_serit_karari(kirpilmis, icerik_x0, icerik_w)
    sayim = list(sayim)
    serit_min = [None, None, None]
    darbogaz_px = float("inf")
    darbogaz_xy = None
    for xx, yy in kirpilmis:
        aciklik = float(dist[yy, xx])
        s = serit_no(xx, icerik_x0, icerik_w) - 1
        if serit_min[s] is None or aciklik < serit_min[s]:
            serit_min[s] = aciklik
        if aciklik < darbogaz_px:
            darbogaz_px = aciklik
            darbogaz_xy = (xx, yy)
    mevcut = [i for i in range(3) if sayim[i] > 0]
    if not mevcut:
        return None
    # DARBOGAZ SERIDI: en kucuk acikligi tasiyan serit.
    # T79 (D-122): `serit_min` SUREKLI bir olcudur. Iki serit projenin OLCULMUS
    # gurultu tabanindan (0,04 · D-112) daha yakinsa argmin OLCUMU degil
    # GURULTUYU izler; `sa_000232`de iki serit 23,00/23,00, `sa_000258`de
    # 18,00/17,98 olculdu. Band icindeki adaylar arasinda secim DETERMINISTIK
    # yapilir: once daha COK rota pikseli tasiyan, esitlikte kucuk indis.
    # Band disinda davranis DEGISMEZ (tek aday kalir -> eski sonuc).
    adaylar = [i for i in beraber_adaylar(
        [serit_min[i] if i in mevcut else None for i in range(3)]) if i in mevcut]
    if not adaylar:
        adaylar = mevcut
    darbogaz_serit = min(adaylar, key=lambda i: (-sayim[i], i)) + 1
    return {
        "serit_karari": int(serit_karari),
        "darbogaz_serit": int(darbogaz_serit),
        "baskin_serit": int(serit_karari),
        "seritler": tuple(sayim),
        "darbogaz_px": float(darbogaz_px),
        "darbogaz_xy": darbogaz_xy,
        "serit_min_px": tuple(serit_min),
        "cok_seritli": len(mevcut) > 1,
        "rota_px": len(pikseller),
    }


def _rota_ekseni_donusumu(sekil, derece):
    """Rota eksenini goruntude ALT->UST'e getiren afin donusumu kur.

    ``derece`` isaret sozlesmesi (S2 · CONTRACTS SS6.3 onerisi):
      goruntu "yukari" yonunden SAAT YONUNDE olculen rota (KB->HB) acisi.
        0   = rota alttan uste (mevcut K-A varsayimi, donusum yok)
       +90  = rota SOLDAN SAGA (KB solda, HB sagda)
       -90  = rota SAGDAN SOLA
       180  = rota ustten alta
    Donus tuvali dondurulmus dikdortgeni tamamen icine alacak boyuttadir;
    kadraja giren bos koseler ENGEL (0) kalir. 90'in katlarinda donusum tam
    piksel permutasyonudur (yuvarlama kaybi yok).

    Doner: (M, M_ters, (yeni_w, yeni_h)).
    """
    h, w = int(sekil[0]), int(sekil[1])
    aci = math.radians(float(derece))
    c, sn = abs(math.cos(aci)), abs(math.sin(aci))
    yeni_w = int(math.ceil(w * c + h * sn - 1e-9))
    yeni_h = int(math.ceil(w * sn + h * c - 1e-9))
    merkez = ((w - 1) / 2.0, (h - 1) / 2.0)
    M = cv2.getRotationMatrix2D(merkez, float(derece), 1.0)
    M[0, 2] += (yeni_w - 1) / 2.0 - merkez[0]
    M[1, 2] += (yeni_h - 1) / 2.0 - merkez[1]
    M_ters = cv2.invertAffineTransform(M)
    return M, M_ters, (yeni_w, yeni_h)


def _dondur_en_yakin(dizi, M, boyut):
    """INTER_NEAREST + sinir 0: yeni deger uretmez, koseler engel kalir."""
    return cv2.warpAffine(np.ascontiguousarray(dizi), M, boyut,
                          flags=cv2.INTER_NEAREST,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def _icerik_kutusunu_dondur(icerik, M, boyut):
    """Icerik kutusunun dondurulmus cercevedeki EKSENE HIZALI SINIR kutusu.

    90'in katlarinda kutu birebir donusur. Ara acilarda sinir kutusu
    dondurulmus icerigin koselerinde engel (0) bolge icerir; uc bant temasi
    o koselerde OLCULEMEZ -> kapi sikilasir (fail-closed), gevsemez.
    """
    x0, y0, w, h = icerik
    koseler = np.array([[x0, y0], [x0 + w - 1, y0],
                        [x0, y0 + h - 1], [x0 + w - 1, y0 + h - 1]],
                       dtype=np.float64)
    don = koseler @ M[:, :2].T + M[:, 2]
    xmin = max(0, int(round(don[:, 0].min())))
    ymin = max(0, int(round(don[:, 1].min())))
    xmax = min(boyut[0] - 1, int(round(don[:, 0].max())))
    ymax = min(boyut[1] - 1, int(round(don[:, 1].max())))
    return (xmin, ymin, max(0, xmax - xmin + 1), max(0, ymax - ymin + 1))


def _noktalari_geri_cevir(noktalar, M_ters):
    """Dondurulmus cercevedeki (x, y) listesini orijinal kareye tasi."""
    if not noktalar:
        return []
    pts = np.array(noktalar, dtype=np.float64)
    geri = pts @ M_ters[:, :2].T + M_ters[:, 2]
    return [(int(round(x)), int(round(y))) for x, y in geri]


def analyze_path(trav_mask, n_waypoints=8, return_clean=False,
                 min_area_ratio=0.01, *, icerik=None, engel_mask=None,
                 mpp=None, return_reason=False, return_olcum=False,
                 goruntu=None, olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI,
                 rota_ekseni_derece=None):
    """
    rota_ekseni_derece (S2 · yonelim): ``None`` ise davranis BAYT-ES aynidir
      (cekirdek dogrudan cagrilir). Deger verilirse maske (ve engel/goruntu)
      `_rota_ekseni_donusumu` ile dondurulur ki rota ekseni goruntude
      ALT->UST olsun; K-A + A* dondurulmus cercevede kosar; waypoint'ler,
      temiz maske ve sebep metni ORIJINAL kare koordinatina geri cevrilir.
      Isaret: goruntu "yukari"sindan SAAT YONUNDE derece; +90 = rota soldan
      saga, -90 = sagdan sola, 180 = ustten alta.
      MADDE 15: dondurme INTER_NEAREST'tir, kadraja giren koseler ENGEL'dir,
      geri cevrilen temiz maske dondurulmemis cekirdek temizligiyle KESISTIRILIR
      ve her waypoint bu maskede olmak zorundadir (degilse fail-closed
      KENAR_GUVENSIZ). Serbest alan hicbir adimda buyumez.
      Uretimde eksen UYDURULMAZ: kaynak operatorun KB->HB kerterizi + arac
      yonudur; otomatik "en iyi eksen" secimi uretime GIRMEZ.

    Algoritma:
      1. Morfolojik temizleme (gurultu, kucuk blob)
      1b. engel_mask verilmisse CIKARMA — kapama sonrasi, EN SON (madde 15)
      2. Ayni bilesenin baslangic ve hedef uc bantlarina temasi; degilse KARAR YOK
      3. Alt/ust tohumlarin baglantisi + muhafazakar A* witness yolu
      4. Dogrulanmis yol uzerinde n_waypoints yalniz cikti yogunlugu olarak
      5. Kenar guvenligi: ardisik waypoint'ler baglantili degilse KARAR YOK
      6. Serit (open_path) ve guven, DOGRULANMIS ROTANIN uzerinden olculur
         (T31/T32 · D-41) — koridorun ust bandindan DEGIL

    engel_mask: engel sinifi maskesi (opsiyonel, geriye uyumlu). Verilirse
      morfolojiden SONRA cikarilir — cikarma en son islemdir, sonrasinda serbest
      alani buyuten hicbir sey yapilmaz (CLAUDE.md madde 15). Verilmezse eski
      davranis korunur; kenar denetimi yine de kosar (D-28 kusuru engel zaten
      zeminden dusulmus olsa bile olusabiliyordu).

    min_area_ratio: ana koridor letterbox'taki gercek icerik alaninin bu
      oranindan KUCUKse karar VERME (None doner). Dusuk-esik fallback'te
      gurultuden yol uydurmayi onler — yanlis yonlendirmektense "tespit yok"
      demek gorev guvenligi geregi.

    icerik: letterbox tuvalindeki gercek goruntu dikdortgeni ``(x0,y0,w,h)``.
      Sol/orta/sag sinirlari kare tuvalden degil bu yatay icerik araligindan
      hesaplanir. ``None`` geriye uyumlu olarak tum maskeyi icerik sayar.

    Returns:
      open_path  : 1=sol, 2=orta, 3=sag (None = tespit yok / alan yetersiz)
                   ROTANIN EN DAR gectigi serit (T31 · D-41)
      confidence : rotanin darbogaz acikligindan turetilen [0,1] guven
                   (T32 · D-41); eski "ust bant piksel orani" DEGIL
      waypoints  : [(x, y), ...] alt→ust sirali, goruntu koordinatlari
      (return_clean=True ise sonraki eleman: kararin kullandigi TEMIZ koridor
       maskesi — gorsellestirme ham maske yerine bunu basmali)
      (return_reason=True ise sonraki eleman: ``None`` veya CONTRACTS SS6.4
       kanonik ``(sebep, detay)`` cifti)
      (return_olcum=True ise SON eleman: ``None`` veya `_rota_serit_olcumu`
       sozlugu — darbogaz, serit dagilimi, cok-seritlilik. Hakem ekrani
       kanit satirini buradan basar.)
      Bayraklar birlikte verilirse sira: clean, reason, olcum.
    """
    if rota_ekseni_derece is None:
        return _analyze_path_cekirdek(
            trav_mask, n_waypoints, return_clean, min_area_ratio,
            icerik=icerik, engel_mask=engel_mask, mpp=mpp,
            return_reason=return_reason, return_olcum=return_olcum,
            goruntu=goruntu, olcek_kaynagi=olcek_kaynagi)
    return _analyze_path_yonelimli(
        trav_mask, n_waypoints, return_clean, min_area_ratio,
        icerik=icerik, engel_mask=engel_mask, mpp=mpp,
        return_reason=return_reason, return_olcum=return_olcum,
        goruntu=goruntu, olcek_kaynagi=olcek_kaynagi,
        rota_ekseni_derece=float(rota_ekseni_derece))


def _analyze_path_yonelimli(trav_mask, n_waypoints, return_clean,
                            min_area_ratio, *, icerik, engel_mask, mpp,
                            return_reason, return_olcum, goruntu,
                            olcek_kaynagi, rota_ekseni_derece):
    """Sarmalayici: dondur -> cekirdek -> geri cevir. Belgesi `analyze_path`."""
    h, w = trav_mask.shape
    derece = float(rota_ekseni_derece)
    M, M_ters, boyut = _rota_ekseni_donusumu((h, w), derece)
    trav_d = _dondur_en_yakin(trav_mask, M, boyut)
    engel_d = None
    if engel_mask is not None:
        engel_mask = np.asarray(engel_mask)
        if engel_mask.shape != trav_mask.shape:
            raise ValueError(
                f"engel_mask sekli {engel_mask.shape} trav_mask "
                f"{trav_mask.shape} ile uyusmuyor")
        engel_d = _dondur_en_yakin((engel_mask > 0).astype(np.uint8), M, boyut)
    goruntu_d = None
    if goruntu is not None:
        goruntu_d = _dondur_en_yakin(goruntu, M, boyut)
    icerik_d = _icerik_kutusunu_dondur(
        (0, 0, w, h) if icerik is None else icerik, M, boyut)

    yol, guven, wps_d, clean_d, sebep, olcum = _analyze_path_cekirdek(
        trav_d, n_waypoints, True, min_area_ratio,
        icerik=icerik_d, engel_mask=engel_d, mpp=mpp,
        return_reason=True, return_olcum=True,
        goruntu=goruntu_d, olcek_kaynagi=olcek_kaynagi)

    # GERI CEVIRME. Temiz maske dondurulmemis cekirdek temizligiyle KESISTIRILIR:
    # ara acilarda en-yakin ornekleme siniri 1 px kaydirabilir; kesisim
    # serbest alanin dondurme yoluyla buyumesini kesin olarak engeller.
    clean_geri = _dondur_en_yakin(clean_d, M_ters, (w, h))
    if np.any(clean_geri):
        # bos maskede kesisim zaten bos: 3840^2 tuvalde ~8 sn'lik morfoloji
        # gereksiz yere odenmesin (sonuc DEGISMEZ, yalniz sure).
        clean_ref = _koridor_temizle(trav_mask, engel_mask, mpp)
        clean_geri = np.where(clean_ref > 0, clean_geri, 0).astype(
            clean_geri.dtype)
    waypoints = _noktalari_geri_cevir(wps_d, M_ters)
    ek = f" [rota ekseni {derece:g} derece; olcum dondurulmus cercevede]"
    if isinstance(sebep, tuple) and len(sebep) == 2:
        sebep = (sebep[0], str(sebep[1]) + ek)
    if isinstance(olcum, dict):
        olcum = dict(olcum)
        olcum["rota_ekseni_derece"] = derece

    if waypoints:
        disari = [
            (x, y) for x, y in waypoints
            if not (0 <= x < w and 0 <= y < h and clean_geri[y, x] > 0)]
        if disari:
            yol, guven, waypoints = None, 0.0, []
            sebep = (KENAR_GUVENSIZ_SEBEBI,
                     f"Geri cevrilen {len(disari)} waypoint orijinal temiz "
                     f"maskenin disinda kaldi{ek}")
            olcum = None

    sonuc = (yol, guven, waypoints)
    if return_clean:
        sonuc += (clean_geri,)
    if return_reason:
        sonuc += (sebep,)
    if return_olcum:
        sonuc += (olcum,)
    return sonuc


def _koridor_temizle(trav_mask, engel_mask, mpp=None):
    """Cekirdegin morfoloji + engel cikarma adimi (ayni kernel, ayni sira).

    `mpp` verilirse KAPAMA cekirdegi fiziksel tavanla sinirlanir (T188,
    `karar_sozlesmesi.kapama_cekirdegi_px`). Cekirdek yalnizca KUCULEBILIR,
    bu yuzden serbest alan yalnizca KUCULUR (madde 15). `mpp` yoksa davranis
    BIREBIR ESKISIDIR.
    """
    h, w = trav_mask.shape
    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    _kx = kapama_cekirdegi_px(max(7, w // 30), mpp)
    _ky = kapama_cekirdegi_px(max(7, h // 30), mpp)
    k_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (_kx, _ky))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)
    if engel_mask is not None:
        clean = clean.copy()
        clean[np.asarray(engel_mask) > 0] = 0
    return clean


def _analyze_path_cekirdek(trav_mask, n_waypoints=8, return_clean=False,
                           min_area_ratio=0.01, *, icerik=None,
                           engel_mask=None, mpp=None, return_reason=False,
                           return_olcum=False, goruntu=None,
                           olcek_kaynagi=OLCEK_KAYNAK_TELEMETRI):
    """`analyze_path` cekirdegi — govde DEGISMEDI (S2: yalniz ad ve sarmalayici)."""
    h, w = trav_mask.shape

    def _don(open_path, confidence, waypoints, clean, ret=None, olcum=None):
        sonuc = (open_path, confidence, waypoints)
        if return_clean:
            sonuc += (clean,)
        if return_reason:
            sonuc += (ret,)
        if return_olcum:
            sonuc += (olcum,)
        return sonuc

    bos = np.zeros_like(trav_mask)
    girdi_px = int(np.count_nonzero(trav_mask))
    if girdi_px == 0:
        return _don(
            None, 0.0, [], bos,
            (MASKE_YOK_SEBEBI,
             "Zemin maskesi 0 piksel; rota analizi yapilamadi."),
        )

    if icerik is None:
        icerik_x0, icerik_y0, icerik_w, icerik_h = 0, 0, w, h
    else:
        icerik_x0 = max(0, min(w, int(icerik[0])))
        icerik_y0 = max(0, min(h, int(icerik[1])))
        icerik_w = max(0, min(w - icerik_x0, int(icerik[2])))
        icerik_h = max(0, min(h - icerik_y0, int(icerik[3])))
        if icerik_w == 0 or icerik_h == 0:
            return _don(
                None, 0.0, [], bos,
                (ALAN_YETERSIZ_SEBEBI,
                 f"Icerik kutusu bos: {icerik_w}x{icerik_h}; "
                 f"girdi maskesi {girdi_px} piksel."),
            )

    # ── ZEMIN MASKESI SAGLAMLIK KAPISI (T48) ───────────────────────────────
    # Rotadan ONCE. v21 catiyi/cimi de zemin sayabiliyor; maske "dolu"
    # gorundugu icin K-A, C-uzayi ve K-B'nin hicbiri bunu yakalayamaz.
    # Olcum HAM zemin maskesi uzerinde yapilir — esik o dagilimdan turetildi
    # (morfoloji/engel cikarma SONRASI degil).
    zemin_reddi = zemin_maskesi_reddi(trav_mask, (icerik_x0, icerik_y0,
                                                  icerik_w, icerik_h))
    if zemin_reddi is not None:
        return _don(None, 0.0, [], bos, zemin_reddi)

    k_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(3, w // 60), max(3, h // 60)))
    # 🔴 T188 (D-326): kapama cekirdegi FIZIKSEL tavanla sinirlanir. Eskiden
    # `max(7, w // 30)` idi — goruntu genisliginin orani, METRIK DEGIL; mpp
    # 0,05'te 0,85 m'lik bir bosluğu dolduruyordu ve duba sirasi zemin
    # maskesinde yalniz DELIK biraktiginda serit ACIK cikiyordu (guven 1.00).
    # Cekirdek yalnizca KUCULEBILIR -> serbest alan yalnizca KUCULUR.
    k_close = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (kapama_cekirdegi_px(max(7, w // 30), mpp),
                            kapama_cekirdegi_px(max(7, h // 30), mpp)))
    clean = cv2.morphologyEx(trav_mask, cv2.MORPH_OPEN, k_open)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, k_close)

    # CIKARMA EN SON (CLAUDE.md madde 15). MORPH_CLOSE extensive'dir ve oyulmus
    # engelin ustunu geri kapatir (REVIEW_LOG D-24: 7 px engelin %99'u geri
    # doldu). Bu yuzden engel maskesi kapamadan SONRA dusulur; bundan sonra
    # serbest alani buyuten hicbir islem yapilmaz.
    if engel_mask is not None:
        engel_mask = (np.asarray(engel_mask) > 0)
        if engel_mask.shape != clean.shape:
            raise ValueError(
                f"engel_mask sekli {engel_mask.shape} trav_mask {clean.shape} ile uyusmuyor")
        # Dogrudan sifirlama: maskenin DEGER ALANINI korur. bitwise_not(...)//255
        # kalibi 0/255 bir girdiyi sessizce 0/1'e indiriyordu.
        clean = clean.copy()
        clean[engel_mask] = 0

    if clean.sum() == 0:
        return _don(
            None, 0.0, [], clean,
            (BILESEN_YOK_SEBEBI,
             f"Girdi maskesi {girdi_px} piksel; morfoloji/engel cikarma "
             "sonrasi bagli bilesen 0 piksel."),
        )

    # EN BUYUK bagli bileseni ANA KORIDOR say → kopuk gurultu bloblari lane kararini
    # ceviremez (girdi cozunurlugu degisince sol/orta/sag ziplamasini onler).
    n_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(clean, 8)
    if n_lbl > 2:  # >1 gercek bilesen (0=arkaplan)
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        clean = (labels == largest).astype(np.uint8)

    # UC BAGLANTISI (CONTRACTS.md SS6.3/K-A): en buyuk parcanin yalniz kendi
    # "ust %30"una bakmak, ortadaki bariyerle kopmus bir yariyi tam koridor
    # sanabiliyordu. Olculen bariyer sahnesinde OpenCV esit parcalardan UST
    # olani seciyordu: hedefe temas VAR, baslangica temas YOK, yine yol=2.
    # Bu nedenle AYNI bilesen hem alt baslangic hem ust hedef bandina yeterli
    # genislikte temas etmelidir. Iki bant da icerik kutusuna gore hesaplanir.
    icerik_kutusu = (icerik_x0, icerik_y0, icerik_w, icerik_h)
    alt_ok = _uc_bant_temasi_yeterli(clean, icerik_kutusu, "alt")
    ust_ok = _uc_bant_temasi_yeterli(clean, icerik_kutusu, "ust")
    if not alt_ok or not ust_ok:
        alt_px = _uc_bant_temas_genisligi(clean, icerik_kutusu, "alt")
        ust_px = _uc_bant_temas_genisligi(clean, icerik_kutusu, "ust")
        gereken_px = bant_temasi_gereken_px(icerik_w)
        eksik = "/".join(
            taraf for taraf, uygun in (("alt", alt_ok), ("ust", ust_ok))
            if not uygun)
        return _don(
            None, 0.0, [], clean,
            (UC_BANT_TEMAS_YOK_SEBEBI,
             f"Koridor {eksik} uc bandina yeterli temas etmiyor; "
             f"olculen alt={alt_px}/{icerik_w}px, "
             f"ust={ust_px}/{icerik_w}px; gereken >= {gereken_px}px."),
        )

    # ALAN DENETIMI: dolgu degil, gercek letterbox icerigi paydaya girer.
    if not _koridor_alani_yeterli(clean, icerik_w, icerik_h, min_area_ratio):
        alan_px = int(clean.sum())
        icerik_alani = max(1, icerik_w * icerik_h)
        alan_orani = alan_px / float(icerik_alani)
        return _don(
            None, 0.0, [], np.zeros_like(clean),
            (ALAN_YETERSIZ_SEBEBI,
             f"Koridor alan orani {alan_orani:.6f}; gereken >= "
             f"{float(min_area_ratio):.6f} "
             f"({alan_px}/{icerik_alani} piksel)."),
        )

    # T30: Guvenlik karari yatay bant orneklerine bagli olamaz. Once tam
    # koridorda alt->ust baglantinin gercek witness yolunu kur; n_waypoints'i
    # ancak bundan SONRA cikti yogunlugu olarak uygula.
    dist = cv2.distanceTransform(clean, cv2.DIST_L2, 5)

    # ── C-UZAYI (T43 · REVIEW_LOG D-59) ────────────────────────────────────
    # Olculdu: kusursuz yer gercegi maskesiyle bile arena kompozitinde 6
    # karenin 4'unde rotanin darbogazi 1,0 px cikiyordu ve darbogaz noktalari
    # goruntu kenarindan 117-214 px ICERIDE — yani kenar artefakti DEGIL, rota
    # gercekten molozu siyiriyordu. Sebep: `yol_duzelt`in gorus-hatti kisayogu
    # pikselin SERBEST olmasini ariyor, ACIKLIGINI degil.
    #
    # Cozum `rota_bul`'da ZATEN vardi (`:313` `gecilebilir = dt_px >=
    # r_gerekli_px`); buraya YENIDEN YAZILMADI, tasindi. Olcek yoksa kisit
    # UYGULANAMAZ — o zaman "kisit yok" degil, "olceksiz kip" kaydedilir ve
    # gorev cagri yerleri `rota_olcek_reddi` ile fail-closed doner.
    #
    # MADDE 15 — BU ISLEM ANTI-EXTENSIVE: {dist >= r} her zaman {dist > 0}
    # altkumesidir, yani serbest alan yalniz DARALIR, asla buyumez.
    r_gerekli_px = r_gerekli_piksel(mpp, R_GEREKLI_M)
    if r_gerekli_px is not None and r_gerekli_px > 0.0:
        gecilebilir = (dist >= float(r_gerekli_px)).astype(np.uint8)
        olceksiz = False
    else:
        gecilebilir = clean
        olceksiz = True

    if int(gecilebilir.sum()) == 0:
        return _don(
            None, 0.0, [], clean,
            (GORUS_HATTI_KOPUK_SEBEBI,
             f"C-uzayi bos: koridorda {float(r_gerekli_px):.2f} px govde "
             f"acikligini saglayan tek piksel yok (mpp={mpp!r}, "
             f"R_GEREKLI_M={R_GEREKLI_M:.2f})."),
        )

    # T72 · HEDEF KONUMU (CONTRACTS SS6.4 · REVIEW_LOG D-105).
    # `goruntu` VERILMEZSE davranis DEGISMEZ: hedef eskisi gibi ust banttir ve
    # tum mevcut cagri yerleri (olcum betikleri dahil) aynen calisir.
    # `goruntu` VERILIRSE cagiran "varis noktasini HB'den al" demis olur; HB
    # bulunamazsa UYDURULMAZ, `HEDEF_YOK` ile cekimser kalinir.
    hb_tohumu = None
    if goruntu is not None:
        # T198 · D-344: olcek BILINIYORSA fiziksel denetim acilir. HB 2 m x
        # 2 m'dir; bandin disindaki aday HB SAYILMAZ. mpp yoksa davranis
        # AYNEN eskisi gibi (geriye donuk uyum).
        # T150/D-386: uretim yapilandirmasi OLCEK + SEKIL CIFTIDIR — kirmizi
        # otomobil olcek bandini gecebiliyor (D-351), sekil kapisi (D-379/
        # D-383) onu duşuruyor. `mpp` varsa sekil esigi de acilir; mpp yoksa
        # hb_konumu zaten eslesme kurali geregi fail-closed None doner —
        # yarim yapilandirma buradan da ACILMAZ.
        hb = hb_konumu(goruntu, mpp=mpp,
                       sekil_esigi=HB_SEKIL_ESIGI if mpp is not None else None)
        if hb is None:
            return _don(None, 0.0, [], clean, hedef_yok_reddi(), None)
        hx, hy, hw, hh = hb["kutu"]
        hb_tohumu = np.zeros(clean.shape, dtype=np.uint8)
        hb_tohumu[max(0, hy):hy + hh, max(0, hx):hx + hw] = 1

    kanonik_yol, kopuk_detay = _bagli_koridor_yolu(
        gecilebilir, icerik_kutusu, dist, min(k_open.shape),
        hedef_tohumu=hb_tohumu)
    if kanonik_yol is None:
        return _don(
            None, 0.0, [], clean,
            (GORUS_HATTI_KOPUK_SEBEBI, kopuk_detay),
        )
    waypoints = _rotayi_ornekle(kanonik_yol, n_waypoints, gecilebilir)

    # SON KAPI: iki ucu serbest olan bir kenar yine de engelin ustunden gecebilir.
    if len(waypoints) >= 2 and not _kenarlar_guvenli(waypoints, gecilebilir,
                                                     engel_mask):
        return _don(
            None, 0.0, [], clean,
            (KENAR_GUVENSIZ_SEBEBI,
             f"{len(waypoints) - 1} ardisik waypoint kenarindan en az biri "
             "gecilemez alana veya ham engele temas ediyor."),
        )

    # T31 + T32 (REVIEW_LOG D-41): SERIT ve GUVEN artik ROTANIN KENDISINDEN
    # okunur. Eskiden ikisi de koridorun UST %30 bandindan turetiliyordu:
    #   · etiket, 67 gercek karenin 67'sinde rotanin gectigi seritle uyusmuyordu;
    #   · guven, enjekte-kapi deneyinde kapi sol/orta/sag gezerken hic
    #     degismiyordu (0,326 / 0,326 / 0,326) ve tespit KOTULESTIKCE yukseliyordu.
    # Olcum KANONIK yol uzerinde yapilir; `n_waypoints` karara giremez (SS6.4/5).
    olcum = _rota_serit_olcumu(kanonik_yol, dist, icerik_kutusu)
    if olcum is None:
        return _don(
            None, 0.0, [], clean,
            (GORUS_HATTI_KOPUK_SEBEBI,
             "Dogrulanmis rota uzerinde tek piksel olculemedi; serit ve "
             "darbogaz turetilemiyor."),
            None,
        )
    # Olcek durumu KARAR CIKTISINA yazilir: "C-uzayi uygulandi mi" sorusu
    # ekranda ve gunlukte gorunur olmali (olceksiz kip sessiz kalamaz).
    olcum["mpp"] = float(mpp) if r_gerekli_px is not None else None
    olcum["r_gerekli_px"] = (float(r_gerekli_px)
                             if r_gerekli_px is not None else None)
    olcum["olceksiz"] = bool(olceksiz)

    # T69 (REVIEW_LOG D-94, D-96): KORIDOR GENISLIK TAVANI.
    # Karar yolunun ARENA SINIRI kavrami yoktur: uretec arena disina bilerek
    # etiketsiz duz zemin cizer, model orayi HAKLI OLARAK zemin isaretler ve
    # burasi tum kareyi ucte bolup o bos kenari gecerli guzergah sayardi.
    # `sa_000070`: darbogaz 304 px. AYNI KUSUR GERCEK KAREDE DE VAR.
    # Sinir GORUNTUDEN YERELLESTIRILEMEDI (D-94: uc aday imza da guvenilmez,
    # ucu de gercek karede coktu; ustelik gercek arena siniri PERSPEKTIF YAMUK).
    # Bu yuzden sinir DEGIL koridorun kendisi sinanir: bir seridin tamamindan
    # genis aciklik guzergah degil ACIK ARAZIDIR. Esik `serit_no`nun kendi
    # bolusumunden gelir; ciplak sayi yoktur (madde 16).
    # Madde 15: yalniz REDDEDER — maskeye dokunmaz, serbest alani buyutmez.
    kg_reddi = rota_koridor_genisligi_reddi(olcum["darbogaz_px"], icerik_w)
    if kg_reddi is not None:
        return _don(None, 0.0, [], clean, kg_reddi, olcum)

    # T155 (REVIEW_LOG D-296): YAYINLANAN alan `serit_karari`dir.
    # Eski `darbogaz_serit` olcum sozlugunde TANI olarak durur ama
    # YAYINLANMAZ: yer gercekli 15 sahnede 6/15 dogruydu (tek pikselden
    # okunuyordu, 13 sahnede o piksel rotanin UCUNDA — guzergahlarin
    # birlestigi, serit kimliginin tanimsiz oldugu yerde).
    open_path = olcum["serit_karari"]
    # T83: OLCEK KAYNAGI KARAR NESNESINE YAZILIR ve GUVENE YANSIR.
    # Sessiz dusus yasak: olcek telemetri disi bir katmandan geldiyse rota
    # telemetriyle AYNI guvende sunulamaz. Varsayilan `telemetri` ve carpani
    # 1.00'dir — mevcut cagri yerlerinin davranisi BIREBIR korunur.
    olcum["olcek_kaynagi"] = olcek_kaynagi
    olcum["olcek_guven_carpani"] = OLCEK_GUVEN_CARPANI.get(olcek_kaynagi, 0.0)
    confidence = olcek_guveni_uygula(
        rota_darbogaz_guveni(olcum["darbogaz_px"], icerik_w), olcek_kaynagi)

    return _don(open_path, confidence, waypoints, clean, None, olcum)


def _rota_kararini_esikle(open_path, confidence, waypoints, karar_reddi=None):
    """Ham analyze_path kararini CONTRACTS SS6.3/K-B ile fail-closed filtrele.

    Ham guven olcum icin korunur; esik altinda yol ve yayina-hazir waypointler
    temizlenir. Donen son eleman ``None`` veya ``(NO_ROUTE sebebi, detay)``dir.
    """
    if karar_reddi is not None:
        return None, confidence, [], karar_reddi
    if open_path is None:
        return open_path, confidence, waypoints, None
    ret = rota_guven_reddi(confidence)
    if ret is not None:
        return None, confidence, [], ret
    return open_path, confidence, waypoints, None


def generate_ika_map(waypoints, open_path, confidence, src_h, src_w, map_size=512):
    """
    IKA icin navigasyon haritasi. Gercek goruntu yok.
    Sadece centerline, waypoint koordinatlari, hedef noktasi.

    IKA bu haritayi alir + kendi kamerasini kullanarak eslestirir.
    """
    canvas = np.full((map_size, map_size, 3), 22, dtype=np.uint8)

    # Grid
    step = map_size // 8
    for i in range(0, map_size + 1, step):
        cv2.line(canvas, (i, 0), (i, map_size), (42, 42, 42), 1)
        cv2.line(canvas, (0, i), (map_size, i), (42, 42, 42), 1)

    # Uc bolge siniri (sol/orta/sag)
    for x in [map_size // 3, 2 * map_size // 3]:
        cv2.line(canvas, (x, 0), (x, map_size), (60, 60, 60), 1)
    for j, label in enumerate(["SOL", "ORTA", "SAG"]):
        lx = j * map_size // 3 + map_size // 12
        color = (0, 220, 0) if (j + 1 == open_path) else (60, 60, 60)
        cv2.putText(canvas, label, (lx, map_size - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1)

    # IKA baslangic
    start = (map_size // 2, map_size - 20)
    cv2.circle(canvas, start, 7, (0, 200, 255), -1)
    cv2.putText(canvas, "IKA", (start[0] + 10, start[1] + 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 200, 255), 1)

    if waypoints:
        sx = map_size / src_w
        sy = map_size / src_h
        scaled = [(int(x * sx), int(y * sy)) for x, y in waypoints]

        # Yol cizgisi
        pts = np.array(scaled, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(canvas, [pts], False, (0, 210, 0), 3)

        # Waypoint noktalar + seyrek koordinat etiketi
        for j, ((px, py), (ox, oy)) in enumerate(zip(scaled, waypoints)):
            cv2.circle(canvas, (px, py), 4, (80, 255, 80), -1)
            if j % 2 == 0:
                cv2.putText(canvas, f"({ox},{oy})", (px + 5, py - 3),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.26, (150, 150, 150), 1)

        # Hedef
        tx, ty = scaled[-1]
        cv2.circle(canvas, (tx, ty), 10, (0, 255, 255), 2)
        cv2.circle(canvas, (tx, ty), 4, (0, 255, 255), -1)
        cv2.putText(canvas, "HEDEF", (tx + 12, ty + 4),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, (0, 255, 255), 1)

        # Ok yonu (son segment)
        if len(scaled) >= 2:
            cv2.arrowedLine(canvas, scaled[-2], scaled[-1],
                            (0, 255, 120), 2, tipLength=0.4)

        # Baslangictan ilk waypoint'e kesikli bag
        cv2.line(canvas, start, scaled[0], (80, 80, 200), 1)

    direction = {1: "SOL", 2: "ORTA", 3: "SAG"}.get(open_path, "?")
    cv2.putText(canvas, f"ACIK YOL: {open_path} ({direction})  GUVEN: {confidence:.2f}",
                (8, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(canvas, f"WP: {len(waypoints)}  KAYNAK: {src_w}x{src_h}px",
                (8, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.37, (140, 140, 140), 1)

    return canvas


DARK_L_MEAN = 80.0   # LAB L ortalamasi bunun altindaysa goruntu KARANLIK sayilir


def is_dark(img):
    """Goruntu los/golgeli mi? (LAB L ortalamasina gore)"""
    return float(cv2.cvtColor(img, cv2.COLOR_BGR2LAB)[:, :, 0].mean()) < DARK_L_MEAN


def normalize_light(img):
    """Isik normalizasyonu — model golge/los isikta cokuyor (bilinen zayiflik).
    Karanlik goruntuyu acar: gamma (ortalamayi ~125'e ceker) + CLAHE (LAB L —
    golge altindaki dokuyu lokal esitler). Normal pozlanmis goruntu AYNEN doner.
    NOT: tek basina kullanma — normalizasyon bazi goruntulerde tespiti BOZAR;
    dogru kullanim orijinalle YARISTIRMAK (bkz. iha_perceive._infer)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    mean = float(lab[:, :, 0].mean())
    if mean >= DARK_L_MEAN:
        return img
    # gamma = log(hedef)/log(mevcut) → ortalamayi ~125'e tasi (asiri patlatmaz)
    gamma = max(0.35, min(1.0, np.log(125.0 / 255.0) / np.log(max(mean, 1.0) / 255.0)))
    lut = ((np.arange(256) / 255.0) ** gamma * 255.0).clip(0, 255).astype(np.uint8)
    out = cv2.LUT(img, lut)
    lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
    lab[:, :, 0] = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(lab[:, :, 0])
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def _preprocess(img):
    """Kare LETTERBOX (dolgu) + isik normalizasyonu.
    (kare_tuval, 512x512_infer, icerik_dikdortgeni) doner.

    NEDEN CROP DEGIL PAD: onceki surum MERKEZI KARE CROP yapiyordu. 1024x576 bir
    drone karesinde bu x=[224,800] araligini birakip genisligin %56'sini ATIYORDU
    → soldaki ve sagdaki guzergah, karar verilmeden once yok oluyordu. Sartname
    HTAB icinde 3 guzergah tanimliyor ve gunun birinde SOL veya SAG acik olabilir;
    o yuzden kenarlari atmak gorevi dogrudan kaybettirir.
    Ayni cozumu simulation/scripts/iha_perceive.py:52 zaten uyguluyordu.

    icerik_dikdortgeni = (x0, y0, w, h): gercek goruntunun tuval icindeki yeri.
    Dolgu bolgesinden gelen sahte tespitleri elemek icin
    _maskeleri_icerige_kirp() ile birlikte kullanilir.
    """
    h, w = img.shape[:2]
    # Isik normalizasyonu DOLGUDAN ONCE: gri dolgu LAB ortalamasini kaydirip
    # is_dark() kararini bozardi.
    norm = normalize_light(img)
    yan = max(h, w)
    tuval = np.full((yan, yan, 3), 114, dtype=np.uint8)
    x0, y0 = (yan - w) // 2, (yan - h) // 2
    tuval[y0:y0 + h, x0:x0 + w] = norm
    small = cv2.resize(tuval, (INFER_SIZE, INFER_SIZE))
    return tuval, small, (x0, y0, w, h)


def _maskeleri_icerige_kirp(masks, icerik):
    """Letterbox dolgusuna dusen maske pikselleri sifirlanir (sahte tespit onlemi)."""
    x0, y0, w, h = icerik
    for k in list(masks):
        kirpik = np.zeros_like(masks[k])
        kirpik[y0:y0 + h, x0:x0 + w] = masks[k][y0:y0 + h, x0:x0 + w]
        masks[k] = kirpik
    return masks


def _draw_waypoints(vis, waypoints):
    if len(waypoints) < 1:
        return vis
    for j in range(len(waypoints) - 1):
        cv2.line(vis, waypoints[j], waypoints[j + 1], (0, 255, 255), 2)
    for wp in waypoints[:-1]:
        cv2.circle(vis, wp, 4, (0, 255, 255), -1)
    # Hedef noktasi
    cv2.circle(vis, waypoints[-1], 9, (0, 255, 255), -1)
    cv2.circle(vis, waypoints[-1], 12, (0, 0, 0), 2)
    return vis


def run_fps(model, n=30):
    dummy = np.zeros((INFER_SIZE, INFER_SIZE, 3), dtype=np.uint8)
    model.predict(dummy, imgsz=INFER_SIZE, verbose=False)

    start = time.perf_counter()
    for _ in range(n):
        model.predict(dummy, imgsz=INFER_SIZE, verbose=False)
    elapsed = time.perf_counter() - start

    fps = n / elapsed
    ms = elapsed / n * 1000
    print(f"\n=== FPS Olcumu ({n} kare) ===")
    print(f"FPS      : {fps:.1f}")
    print(f"ms/kare  : {ms:.0f}")
    print(f"Hedef    : >=10 FPS")
    print("Sonuc    :", "BASARILI" if fps >= 10 else "YETERSIZ — imgsz=256 ile tekrar dene")


def run_image(model, path_str, conf, mpp=None, canli_olcek=None,
              arac_modeli=None, senaryo=None):
    path = Path(path_str)
    RESULTS_DIR.mkdir(exist_ok=True)

    if path.is_dir():
        files = sorted(f for f in path.iterdir() if f.suffix.lower() in SUPPORTED_EXT)
        if not files:
            print(f"Klasorde gorsel bulunamadi: {path}")
            return
        print(f"{len(files)} gorsel isleniyor -> {RESULTS_DIR}/")
    elif path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXT:
            print(f"Desteklenmeyen format: {path.suffix}  (desteklenen: jpg png bmp)")
            return
        files = [path]
    else:
        print(f"Dosya/klasor bulunamadi: {path}")
        return

    for img_path in files:
        img = cv2.imread(str(img_path))
        if img is None:
            print(f"Okunamadi: {img_path}")
            continue

        sq, small, icerik = _preprocess(img)
        orig_h, orig_w = sq.shape[:2]

        results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
        masks = get_masks(results, orig_h, orig_w)
        masks = _maskeleri_icerige_kirp(masks, icerik)
        # Telemetriyi inference SONRASINDA sorgula: karar verildigi anda taze
        # olmayan bir ornek, model gecikmesi boyunca sessizce yaslanmamalidir.
        # T86: olcek artik TEK katmandan gelmiyor — kahin katman 1/2/3'u
        # sirayla dener ve KAYNAGINI beyan eder (D-126/D-136).
        olcek = kare_olcek_kahini(mpp, canli_olcek, icerik, bgr=img,
                                  arac_modeli=arac_modeli, senaryo=senaryo)
        kare_mpp = olcek["mpp"]
        # T43 · HALKA 5: olcek yoksa GOREV yolunda rota URETILMEZ. Sessiz
        # `mpp=1.0` varsayimi govde acikligini ~11 kat kuculuyordu (D-59).
        # 🔴 KAPI GEVSEMEDI: kahin uretemezse `kare_mpp` yine None'dur.
        olcek_reddi = rota_olcek_reddi(kare_mpp)
        open_path, path_conf, waypoints, karar_reddi = analyze_path(
            masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=kare_mpp,
            return_reason=True, olcek_kaynagi=olcek["kaynak"],
            # T150 BAGLANDI (D-386, kullanici onayi K2a + renk teyidi):
            # varis noktasi HB'den alinir; olcek+sekil kapilari
            # analyze_path icindeki tek noktadan. HB gorunmeyen
            # karede HEDEF_YOK cekimserligi (sozlesme, T72/D-105;
            # sonda 259/260 dogruladi). Olculen maliyet SIFIR:
            # p 0,9846=0,9846, serit yayini ayni 195/256, hedef
            # 253/256 dogru pedde (results/t150/baglama_olcumu).
            goruntu=sq)
        # ONCELIK (CONTRACTS SS6.4/3): YAPISAL ret ezilmez. analyze_path zaten
        # reddettiyse sebebi KORUNUR; olcek eksikligi yapilandirma boslugudur,
        # ZEMIN_MASKESI_SUPHELI ise ALGI ARIZASIDIR.
        if olcek_reddi is not None and karar_reddi is None:
            open_path, path_conf, waypoints = None, 0.0, []
            karar_reddi = olcek_reddi
        open_path, path_conf, waypoints, karar_reddi = _rota_kararini_esikle(
            open_path, path_conf, waypoints, karar_reddi)
        vis = draw_masks(sq, masks)

        if open_path:
            vis = _draw_waypoints(vis, waypoints)
            info = f"Acik yol: {open_path}  guven: {path_conf:.2f}"
            ika_data = {
                "open_path": open_path,
                "confidence": path_conf,
                "waypoints": waypoints,
                "timestamp": int(time.time()),
            }
        elif karar_reddi is not None:
            info = f"NO_ROUTE: {karar_reddi[0]} - {karar_reddi[1]}"
            ika_data = None
        else:
            info = "Tespit yok"
            ika_data = None

        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        out_path = RESULTS_DIR / f"{img_path.stem}_result.jpg"
        cv2.imwrite(str(out_path), vis)
        print(f"{img_path.name:30s}  {info}  ({orig_w}x{orig_h}) -> {out_path.name}")

        if ika_data:
            ika_map = generate_ika_map(waypoints, open_path, path_conf, orig_h, orig_w)
            ika_map_path = RESULTS_DIR / f"{img_path.stem}_ika_map.jpg"
            cv2.imwrite(str(ika_map_path), ika_map)
            print(f"{'':30s}  IKA harita -> {ika_map_path.name}")
            print(f"{'':30s}  payload: {json.dumps(ika_data)}")


# ── T204 · EKRANSIZ KIPTE KONTROLLU DURDURMA (D-404 §8 KUCUK-2) ─────────────
# KUSUR (TASK_QUEUE T204): `signal` HIC islenmiyordu. `systemctl stop
# navitas-rpi-inference` SIGTERM yollar; Python varsayilani surecin ANINDA
# olmesidir — `run_camera`/`run_video` icindeki `cap.release()` ve `main()`
# finally'si (`yayinci.stop`, `link.close`, `canli_olcek.kapat`) HIC kosmaz.
# Ekranli kipte 'q' bu yolu sagliyordu; EKRANSIZ kipte 'q' YOKTUR, tek dogal
# bitis 30 ardisik dusen karedir — yani pratikte hicbir temiz cikis yolu yok.
#
# Cozum `comms/seri_hub.py` (D-405) kalibinin AYNISI: isleyici YALNIZ bayrak
# kurar; dongu bir tur icinde cikar, `finally` kosar, cikis kodu 0.
# 🔴 Isleyiciden `KeyboardInterrupt` FIRLATMAK bilerek SECILMEDI: istisna
# rasgele bir bytecode sinirinda — temizligin ORTASINDA da — dogabilir ve
# `cap.release()`i bolebilir. Bayrak deterministiktir.
# systemd sozlesmesi DEGISMEZ: temiz cikis zaten kod 0'dir ve `systemctl stop`
# `Restart=always` birimini yeniden baslatmaz; `TimeoutStopSec=5` icin bir tur
# (bir kare suresi ya da dusen-kare beklemesi) fazlasiyla yeter.
_DURDURMA = threading.Event()
_DURDURMA_SINYALLERI = ("SIGTERM", "SIGINT")


def durdurma_istendi():
    """Kontrollu durdurma sinyali geldi mi? (dongu kapisi)"""
    return _DURDURMA.is_set()


def durdurmayi_iste():
    """Bayragi kur — sinyal isleyicisi ve testler icin tek giris."""
    _DURDURMA.set()


def durdurma_bayragini_sifirla():
    """Bayragi temizle (surec ici yeniden kosum ve test hijyeni)."""
    _DURDURMA.clear()


def _durdurma_sinyallerini_kur():
    """SIGTERM/SIGINT -> bayrak. Onceki isleyicileri dondurur (geri alma icin).

    `signal.signal` yalniz ANA IPLIKTE ve sinyali olan platformda calisir;
    kurulamazsa KIRMIZI not basilir ve isleyici kurulmaz — SESSIZ gecis YOK
    (kontrollu durdurmanin olmadigini sahada gormek gerekir).
    """
    durdurma_bayragini_sifirla()

    def isleyici(signum, frame):        # noqa: ARG001 — imza signal'indir
        durdurmayi_iste()

    eskiler = {}
    for ad in _DURDURMA_SINYALLERI:
        sig = getattr(signal, ad, None)
        if sig is None:
            continue
        try:
            eskiler[sig] = signal.signal(sig, isleyici)
        except (ValueError, OSError, RuntimeError) as exc:
            print(f"KIRMIZI: {ad} isleyicisi kurulamadi "
                  f"({type(exc).__name__}: {exc}) — kontrollu durdurma YOK; "
                  f"kamera serbest birakilmayabilir",
                  file=sys.stderr, flush=True)
    return eskiler


def _durdurma_sinyallerini_geri_al(eskiler):
    """main() cikarken onceki isleyicileri geri koy (test/kutuphane hijyeni)."""
    for sig, eski in (eskiler or {}).items():
        try:
            signal.signal(sig, eski)
        except (ValueError, OSError, TypeError, RuntimeError):
            pass


def run_video(model, path_str, conf, save=True, mpp=None, canli_olcek=None,
              arac_modeli=None, senaryo=None, yayinci=None, *, ekransiz=False):
    # D-404: `ekransiz=True` -> pencere/waitKey YOK (systemd, DISPLAY'siz Jetson).
    # Karar yolu (analyze_path, esikleme, histerezis, yayin) BAYT-ES aynidir;
    # yalniz gorsellestirme ve 'q' ile durdurma atlanir (SIGINT/SIGTERM calisir).
    path = Path(path_str)
    if not path.is_file():
        print(f"Dosya bulunamadi: {path}")
        return
    if path.suffix.lower() not in SUPPORTED_VIDEO_EXT:
        print(f"Desteklenmeyen format: {path.suffix}  (desteklenen: {', '.join(SUPPORTED_VIDEO_EXT)})")
        return

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"Video acilamadi: {path}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    src_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    src_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    side = max(src_w, src_h)   # letterbox KARE tuval — crop degil, pad (bkz. _preprocess)

    writer = None
    out_path = None
    if save:
        RESULTS_DIR.mkdir(exist_ok=True)
        out_path = RESULTS_DIR / f"{path.stem}_result.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, src_fps, (side, side))
        # T205 (D-404 §8 KUCUK-3): `cv2.VideoWriter` ASLA None DONMEZ — codec
        # ya da yazma izni yoksa nesne yine uretilir ve `bool(writer)` TRUE
        # kalir. Eski kod her kareyi bu OLU yaziciya yaziyor, sonda
        # "Kaydedildi:" basiyordu: KAYIT SESSIZCE KAYBOLUYORDU. Ustelik
        # ekransiz kipin "gorsel HIC uretilmez" vaadi de bozuluyordu
        # (`if ekransiz and not writer` yanlis dalda kaliyordu).
        #
        # SECIM (TASK_QUEUE T205 on-kaydi, gerekce): sureci OLDURMEK yerine
        # KAYIT KIPINI KAPAT. --video cevrimdisi analiz/gosterim yoludur;
        # kaydin yapilamamasi karar uretimini durdurmaz ve --video ile
        # telsiz halkasi da kurulabilir (yayin kesilmemeli). Ama SESSIZ
        # OLAMAZ: stderr'e KIRMIZI uyari, `writer=None`, ve sonda
        # "Kaydedildi:" satiri BASILMAZ — "kayit yok" gorunur.
        if not writer.isOpened():
            print(f"KIRMIZI: VideoWriter ACILAMADI ({out_path}; fourcc=mp4v "
                  f"{src_fps:.1f} fps {side}x{side}) — codec yok ya da yol "
                  f"yazilamiyor. KAYIT KAPATILDI, karar yolu surer.",
                  file=sys.stderr, flush=True)
            try:
                writer.release()
            except cv2.error:
                pass
            writer = None
            save = False

    print(f"Video: {path.name}  {src_w}x{src_h}  {src_fps:.1f}fps  {total_frames} kare")
    print(f"Cikti: {out_path if writer else 'kayit yok'}  — izlemek icin 'q'")

    fps_buf = []
    frame_idx = 0
    # P5 (D-396): yayin histerezisi — yalniz AKIS yollarinda, yayindan hemen
    # once. Analiz katmani ve zincir olcumleri (61/65) DEGISMEZ (madde 15).
    yumusatici = KararYumusatici()

    # T204: dongu ARTIK try/finally icinde. SIGTERM/SIGINT bayragi
    # kurulunca bir tur icinde cikilir; `cap.release()`/`writer.release()`
    # her yolda (istisna, KeyboardInterrupt, sinyal) KOSAR.
    try:
        while True:
            # T204: kontrollu durdurma — sinyal geldiyse bu tur ISLENMEZ,
            # dongu biter ve `finally` temizligi kosar.
            if durdurma_istendi():
                print("KONTROLLU DURDURMA: sinyal alindi, video dongusu "
                      "kapaniyor.", flush=True)
                break
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            sq, small, icerik = _preprocess(frame)
            orig_h, orig_w = sq.shape[:2]

            t0 = time.perf_counter()
            results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
            fps_buf.append(time.perf_counter() - t0)
            if len(fps_buf) > 30:
                fps_buf.pop(0)

            masks = get_masks(results, orig_h, orig_w)
            masks = _maskeleri_icerige_kirp(masks, icerik)
            # T86: olcek artik TEK katmandan gelmiyor — kahin katman 1/2/3'u
            # sirayla dener ve KAYNAGINI beyan eder (D-126/D-136).
            olcek = kare_olcek_kahini(mpp, canli_olcek, icerik, bgr=frame,
                                      arac_modeli=arac_modeli, senaryo=senaryo)
            kare_mpp = olcek["mpp"]
            # T43 · HALKA 5: olcek yoksa GOREV yolunda rota URETILMEZ. Sessiz
            # `mpp=1.0` varsayimi govde acikligini ~11 kat kuculuyordu (D-59).
            # 🔴 KAPI GEVSEMEDI: kahin uretemezse `kare_mpp` yine None'dur.
            olcek_reddi = rota_olcek_reddi(kare_mpp)
            open_path, path_conf, waypoints, karar_reddi = analyze_path(
                masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=kare_mpp,
                return_reason=True, olcek_kaynagi=olcek["kaynak"],
                # T150 BAGLANDI (D-386, kullanici onayi K2a + renk teyidi):
                # varis noktasi HB'den alinir; olcek+sekil kapilari
                # analyze_path icindeki tek noktadan. HB gorunmeyen
                # karede HEDEF_YOK cekimserligi (sozlesme, T72/D-105;
                # sonda 259/260 dogruladi). Olculen maliyet SIFIR:
                # p 0,9846=0,9846, serit yayini ayni 195/256, hedef
                # 253/256 dogru pedde (results/t150/baglama_olcumu).
                goruntu=sq)
            # ONCELIK (CONTRACTS SS6.4/3): YAPISAL ret ezilmez. analyze_path zaten
            # reddettiyse sebebi KORUNUR; olcek eksikligi yapilandirma boslugudur,
            # ZEMIN_MASKESI_SUPHELI ise ALGI ARIZASIDIR.
            if olcek_reddi is not None and karar_reddi is None:
                open_path, path_conf, waypoints = None, 0.0, []
                karar_reddi = olcek_reddi
            open_path, path_conf, waypoints, karar_reddi = _rota_kararini_esikle(
                open_path, path_conf, waypoints, karar_reddi)
            # K1 (sartname SS2.2.3): kare karari YKS'ye ve IKA'ya telsizle gider.
            # D-396: farkli serit ancak K ardisik karede teyitlenirse yayina
            # gecer; NO_ROUTE ve ayni-serit ANINDA gecer (`KararYumusatici`).
            if yumusatici.suz(open_path, karar_reddi):
                _karari_yayinla(yayinci, open_path, path_conf, waypoints,
                                kare_mpp, karar_reddi)
            # D-404: gorsel yalniz kayit ya da ekran icin uretilir; ekransiz ve
            # kayitsiz kosumda hic cizilmez (karar yukarida zaten yayinlandi).
            if ekransiz and not writer:
                continue
            vis = draw_masks(sq, masks)

            if open_path:
                vis = _draw_waypoints(vis, waypoints)
                label = f"Yol: {open_path}  guven: {path_conf:.2f}"
            elif karar_reddi is not None:
                label = f"NO_ROUTE: {karar_reddi[0]} ({path_conf:.3f})"
            else:
                label = "Tespit yok"

            live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
            progress = f"{frame_idx}/{total_frames}" if total_frames > 0 else str(frame_idx)
            cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(vis, f"FPS: {live_fps:.1f}  Kare: {progress}",
                        (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

            if writer:
                writer.write(vis)

            if ekransiz:
                continue
            cv2.imshow("Navitas", vis)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("Kullanici durdurdu.")
                break

    finally:
        cap.release()
        if writer:
            writer.release()
        if not ekransiz:
            cv2.destroyAllWindows()

    # T204: kontrollu durdurma ILK KAREDEN ONCE gelirse `fps_buf` BOSTUR;
    # eski satir orada ZeroDivisionError ile cokuyordu — kontrollu cikis
    # yolu cokerek bitemez (cikis kodu 0 kalmali: systemd sozlesmesi).
    ort_fps = (1.0 / (sum(fps_buf) / len(fps_buf))) if fps_buf else 0.0
    print(f"\n{frame_idx} kare islendi  —  ortalama {ort_fps:.1f} FPS")
    # T205: olu yazicida `writer` None'dir -> "Kaydedildi:" YALANI yok.
    if writer:
        print(f"Kaydedildi: {out_path}")


def run_camera(model, conf, mpp=None, canli_olcek=None, kaynak=None,
               arac_modeli=None, senaryo=None, yayinci=None, *, ekransiz=False):
    # D-404 (Faz B, Gorev C olcumu): systemd altinda DISPLAY yokken kosulsuz
    # cv2.imshow ILK KAREDE cokup Restart dongusune giriyordu (hands-off
    # ihlali). `ekransiz=True` pencere/waitKey'i atlar; karar yolu ve yayin
    # BAYT-ES aynidir (tests/test_faz_b_rpi_ekransiz.py). 'q' ile durdurma
    # yoktur; SIGINT/SIGTERM (systemctl stop) ile durur.
    # Imza geriye uyumludur; ancak canli kamera kararinda statik mpp artik
    # otorite degildir. Eski bir cagirici mpp verse bile telemetri yoksa
    # `_kare_olcegi` None doner ve rota OLCEK_YOK ile fail-closed kalir.
    if mpp is not None:
        print("UYARI: kamera kipinde statik --mpp yok sayildi; canli telemetri gerekir.")
    # T73: kaynak PARAMETRIK. Eskiden `cv2.VideoCapture(0)` SABITTI ve yarisma
    # gunu kamera indeksi degisirse KAYNAK DOSYA duzenlemek gerekiyordu — bu
    # muhurlu kutu prosedurune (SS2.2.1) aykiridir.
    # Varsayilan DEGISMEDI: `kaynak` verilmezse yine indeks 0.
    coz = kamera_kaynagi_coz(kaynak)
    cap = cv2.VideoCapture(coz)
    if not cap.isOpened():
        print(f"Kamera acilamadi (kaynak={coz!r}).")
        return {"bitis": KAMERA_BITIS_ACILAMADI, "okunan": 0,
                "dusen_toplam": 0, "dusen_ardisik_maks": 0}

    if ekransiz:
        print("EKRANSIZ kip: pencere yok, karar yayini surer (durdurma: SIGINT/SIGTERM)")
    else:
        print("Kamera acik — cikmak icin 'q'")
    fps_buf = []
    ozet = {"bitis": None, "okunan": 0, "dusen_toplam": 0, "dusen_ardisik_maks": 0}
    # P5 (D-396): yayin histerezisi — yalniz AKIS yollarinda, yayindan hemen
    # once. Analiz katmani ve zincir olcumleri (61/65) DEGISMEZ (madde 15).
    yumusatici = KararYumusatici()

    # T143 (D-284): eskiden `if not ret: break` — ilk dusen karede SESSIZ bitis.
    # T204: dongu try/finally icinde — sinyal, istisna ve KeyboardInterrupt
    # dahil HER yolda kamera serbest birakilir (D-404 §8 KUCUK-2).
    try:
        for frame in kamera_kareleri(cap, ozet):
            # T204: kontrollu durdurma — SIGTERM/SIGINT bayragi kuruluysa
            # bu kare ISLENMEZ; `finally` cap.release()'i GARANTI eder.
            # Ekransiz kipte 'q' yoktur; bu, tek gercek temiz cikistir.
            if durdurma_istendi():
                ozet["bitis"] = KAMERA_BITIS_SINYAL
                print("KONTROLLU DURDURMA: sinyal alindi, kamera dongusu "
                      "kapaniyor.", flush=True)
                break
            # 🔴 D-349: BURADA `frame = cv2.flip(frame, 1)` VARDI ve KALDIRILDI.
            # Projenin ILK commit'inden (17258f8) geliyordu, aciklamasi yoktu —
            # muhtemelen dizustu web kamerasinda goruntunun "dogal" gorunmesi icin
            # konmus bir AYNA kolayligi. Ama bu SAHA YOLUDUR (jetson_paket'te de
            # var, CONTRACTS izlenebilirlik tablosu satir 1) ve kareyi aynalamak
            # SOL ile SAGI takas eder. OLCULDU (kabul kumesi, v36, uretim cagri
            # sirasi): acik yol 1 ya da 3 olan 16 karenin 15'i (%93,8) TAKAS
            # oluyordu (1->3: 9 kare, 3->1: 6 kare); orta serit aynaya simetrik
            # oldugu icin etkilenmiyordu.
            # Sahada acik guzergah SOL ise IKA SAGA yonlendirilirdi.
            # Sartname SS2.1: yanlis guzergah = 0 PUAN.
            # ⚠ GERI KOYMAYIN. Nobetci: tests/test_t201_kamera_yonu.py
            sq, small, icerik = _preprocess(frame)
            orig_h, orig_w = sq.shape[:2]

            t0 = time.perf_counter()
            results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)
            fps_buf.append(time.perf_counter() - t0)
            if len(fps_buf) > 30:
                fps_buf.pop(0)

            masks = get_masks(results, orig_h, orig_w)
            masks = _maskeleri_icerige_kirp(masks, icerik)
            # T86: olcek artik TEK katmandan gelmiyor — kahin katman 1/2/3'u
            # sirayla dener ve KAYNAGINI beyan eder (D-126/D-136).
            olcek = kare_olcek_kahini(None, canli_olcek, icerik, bgr=frame,
                                      arac_modeli=arac_modeli, senaryo=senaryo)
            kare_mpp = olcek["mpp"]
            # T43 · HALKA 5: olcek yoksa GOREV yolunda rota URETILMEZ. Sessiz
            # `mpp=1.0` varsayimi govde acikligini ~11 kat kuculuyordu (D-59).
            # 🔴 KAPI GEVSEMEDI: kahin uretemezse `kare_mpp` yine None'dur.
            olcek_reddi = rota_olcek_reddi(kare_mpp)
            open_path, path_conf, waypoints, karar_reddi = analyze_path(
                masks[0], icerik=icerik, engel_mask=masks.get(1), mpp=kare_mpp,
                return_reason=True, olcek_kaynagi=olcek["kaynak"],
                # T150 BAGLANDI (D-386, kullanici onayi K2a + renk teyidi):
                # varis noktasi HB'den alinir; olcek+sekil kapilari
                # analyze_path icindeki tek noktadan. HB gorunmeyen
                # karede HEDEF_YOK cekimserligi (sozlesme, T72/D-105;
                # sonda 259/260 dogruladi). Olculen maliyet SIFIR:
                # p 0,9846=0,9846, serit yayini ayni 195/256, hedef
                # 253/256 dogru pedde (results/t150/baglama_olcumu).
                goruntu=sq)
            # ONCELIK (CONTRACTS SS6.4/3): YAPISAL ret ezilmez. analyze_path zaten
            # reddettiyse sebebi KORUNUR; olcek eksikligi yapilandirma boslugudur,
            # ZEMIN_MASKESI_SUPHELI ise ALGI ARIZASIDIR.
            if olcek_reddi is not None and karar_reddi is None:
                open_path, path_conf, waypoints = None, 0.0, []
                karar_reddi = olcek_reddi
            open_path, path_conf, waypoints, karar_reddi = _rota_kararini_esikle(
                open_path, path_conf, waypoints, karar_reddi)
            # K1 (sartname SS2.2.3): kare karari YKS'ye ve IKA'ya telsizle gider.
            # `yayinci` None ise (hedef verilmedi) davranis bayt-es aynidir.
            # D-396: farkli serit ancak K ardisik karede teyitlenirse yayina
            # gecer; NO_ROUTE ve ayni-serit ANINDA gecer (`KararYumusatici`).
            if yumusatici.suz(open_path, karar_reddi):
                _karari_yayinla(yayinci, open_path, path_conf, waypoints,
                                kare_mpp, karar_reddi)
            # D-404: ekransiz kipte gorsel HIC uretilmez (karar yukarida yayinlandi).
            if ekransiz:
                continue
            vis = draw_masks(sq, masks)

            if open_path:
                vis = _draw_waypoints(vis, waypoints)
                label = f"Yol: {open_path}  guven: {path_conf:.2f}"
            elif karar_reddi is not None:
                label = f"NO_ROUTE: {karar_reddi[0]} ({path_conf:.3f})"
            else:
                label = "Tespit yok"

            live_fps = 1.0 / (sum(fps_buf) / len(fps_buf))
            cv2.putText(vis, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(vis, f"FPS: {live_fps:.1f}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow("Navitas", vis)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                ozet["bitis"] = KAMERA_BITIS_KULLANICI
                break

    finally:
        cap.release()
        if not ekransiz:
            cv2.destroyAllWindows()
    print(kamera_bitis_raporu(ozet))
    return ozet


def kamera_kareleri(cap, ozet, *, ust_sinir=None, bekleme_s=None,
                    bekle=None, log=print):
    """Canli kaynaktan kare uret; dusen kareyi SAY, sinirli YENIDEN DENE, LOGLA.

    T143 (D-284, T18 curutucusu): eski dongu `if not ret: break` idi — USB /
    DroidCam hattinda TEK kare kaybi algi hattini sessizce kapatiyordu.
    Simdi:
      * `ret=False` -> `dusen_toplam` ve ardisik sayac artar, `bekleme_s`
        beklenir, tekrar denenir; basarili okuma ardisik sayaci SIFIRLAR.
      * ardisik dusen kare `ust_sinir`a ulasinca dongu KONTROLLU biter:
        `ozet["bitis"] = KAMERA_BITIS_DUSEN_KARE`, log basilir.
    Sabitler `karar_sozlesmesi`nden (KAMERA_DUSEN_KARE_*) gelir; parametreler
    yalniz test icindir. `ozet` cagiranin sozlugudur: okunan / dusen_toplam /
    dusen_ardisik_maks / bitis alanlari yerinde guncellenir (YKS/loga rapor).
    """
    if ust_sinir is None:
        ust_sinir = KAMERA_DUSEN_KARE_UST_SINIRI
    if bekleme_s is None:
        bekleme_s = KAMERA_DUSEN_KARE_BEKLEME_S
    if bekle is None:
        bekle = time.sleep
    ardisik = 0
    while True:
        # T204: yeniden deneme dongusu SIGTERM'i BEKLEYEMEZ — kamera koptuysa
        # burada 30 x bekleme kadar oyalanilir ve `systemctl stop` o sure
        # boyunca cevapsiz kalirdi. Bayrak kuruluysa uretici KONTROLLU biter;
        # bitis nedeni ayri (`KAMERA_BITIS_SINYAL`), cagiranin `finally`si kosar.
        if durdurma_istendi():
            ozet["bitis"] = KAMERA_BITIS_SINYAL
            log("KAMERA: kontrollu durdurma sinyali — kare uretimi bitiyor. "
                f"toplam dusen={ozet.get('dusen_toplam', 0)} "
                f"okunan={ozet.get('okunan', 0)}")
            return
        ret, frame = cap.read()
        if not ret or frame is None:
            ardisik += 1
            ozet["dusen_toplam"] = ozet.get("dusen_toplam", 0) + 1
            ozet["dusen_ardisik_maks"] = max(ozet.get("dusen_ardisik_maks", 0), ardisik)
            if ardisik >= ust_sinir:
                ozet["bitis"] = KAMERA_BITIS_DUSEN_KARE
                log(f"KAMERA: {ardisik} ardisik dusen kare (ust sinir {ust_sinir}) "
                    f"— hat KOPTU sayildi, dongu kontrollu bitiyor. "
                    f"toplam dusen={ozet['dusen_toplam']} okunan={ozet.get('okunan', 0)}")
                return
            log(f"KAMERA: kare dusdu ({ardisik}/{ust_sinir} ardisik, "
                f"toplam {ozet['dusen_toplam']}) — yeniden deneniyor")
            bekle(bekleme_s)
            continue
        ardisik = 0
        ozet["okunan"] = ozet.get("okunan", 0) + 1
        yield frame


def kamera_bitis_raporu(ozet):
    """Bitis satiri (log/YKS): neden + okunan + dusen (toplam / ardisik maks)."""
    return (f"KAMERA BITIS: neden={ozet.get('bitis')} okunan={ozet.get('okunan', 0)} "
            f"dusen_toplam={ozet.get('dusen_toplam', 0)} "
            f"dusen_ardisik_maks={ozet.get('dusen_ardisik_maks', 0)}")


def _arguman_ayristirici():
    parser = argparse.ArgumentParser(description="Navitas RPi Inference")
    parser.add_argument("--fps", action="store_true", help="FPS olcumu")
    parser.add_argument("--image", type=str, help="Gorsel dosya veya klasor yolu")
    parser.add_argument("--video", type=str, help="Video dosyasi (.mp4 .avi .mov ...)")
    parser.add_argument("--camera", action="store_true", help="Canli kamera")
    # T73 · SS11.3: giris kaynagi ve agirlik ELLE DOSYA DUZENLEMEDEN degismeli.
    parser.add_argument(
        "--kaynak", type=str, default=None,
        help=("Kamera kaynagi: indeks (0, 2), cihaz yolu (/dev/video1) veya "
              "dosya. Verilmezse indeks 0 (eski davranis)."))
    parser.add_argument(
        "--model", type=str, default=None,
        help=("Model agirligi (.pt) ya da kayit defterinde `turevler` altinda "
              "DOGRULANMIS sha256 ile kayitli .engine/.onnx turevi (T143). "
              "Verilmezse Jetson uretim manifestindeki `asil_model_pt` "
              "alanindan turetilir — ciplak varsayilan YOK."))
    parser.add_argument(
        "--kayit-dogrulamasiz", dest="kayit_dogrulamasiz", action="store_true",
        help=("Kayit defteri (config/model_registry.json) uyusmazliginda "
              "DURMA. Varsayilan FAIL-CLOSED'dir; bu bayrak guvenligi acikca "
              "gevsetir ve gerekcesi kayda gecmelidir."))
    parser.add_argument("--no-save", action="store_true", help="Video modunda ciktiyi kaydetme")
    # D-404: systemd/ekransiz Jetson icin — pencere ve waitKey yok; karar yayini
    # ve (video kipinde) kayit aynen surer. --image/--fps'te etkisizdir.
    parser.add_argument("--ekransiz", action="store_true",
                        help="Pencere acma (systemd/ekransiz Jetson); karar yayini ve kayit aynen surer")
    parser.add_argument("--conf", type=float, default=0.30, help="Guven esigi (varsayilan: 0.30)")
    # T43 · HALKA 5 (CONTRACTS SS5): olcek SAHA YOLUNDA uretilebilir olmali.
    # Kaynak (a) irtifa + FOV/odak — MAVLink GLOBAL_POSITION_INT.relative_alt
    # zaten okunuyor (comms/inis_kaniti.py:143). Kaynak (b) bilinen olcekli
    # nesne (2x2 m H brandasi) BUGUN URETILEMEZ: uretim modeli 2 sinifli
    # ({0: traversable, 1: blocked}) ve hedef dedektoru YOK (D-23, olculdu).
    parser.add_argument("--mpp", type=float, default=None,
                        help="Yalniz cevrimdisi gorsel/video icin metre/piksel")
    parser.add_argument(
        "--mavlink", type=str, default=None,
        help=("Canli irtifa MAVLink adresi — COGULLAYICI UCU "
              "(orn. udp:127.0.0.1:14550); seri Pixhawk tek sahiplidir, "
              "dogrudan /dev/ttyACM0 VERILMEZ"))
    parser.add_argument(
        "--mav-sysid", type=int, default=None,
        help="Zorunlu beklenen Pixhawk sistem kimligi (1..255)")
    # FDR/ACIK_KALEMLER §4b #23 · CONTRACTS §7.4 (D-403): seri Pixhawk TEK
    # SAHIPLIDIR. Kilit `iha_komut_alici`da vardi, burada YOKTU — ayni
    # mekanizma (bayrak adi, yardim ve red metni) `inis_kaniti`den okunur,
    # kopyalanmaz. Modul pymavlink'e dokunmaz; --fps/--image yolu bozulmaz.
    _inis_kaniti_modulu().seri_pixhawk_bayragini_ekle(parser)
    geometri = parser.add_mutually_exclusive_group()
    geometri.add_argument("--fov", type=float, default=None,
                          help="Kameranin YATAY gorus acisi (derece)")
    geometri.add_argument("--odak", type=float, default=None,
                          help="Odak uzakligi (piksel); --fov ile birlikte verilmez")
    # T86 · OLCEK KAHINI KATMAN 2 ve 3 (CONTRACTS SS5.4 · D-126/D-136).
    # Ikisi de VARSAYILAN OLARAK KAPALIDIR: verilmezlerse davranis T86
    # oncesiyle BIREBIR aynidir (telemetri yoksa OLCEK_YOK).
    parser.add_argument(
        "--arac-modeli", type=Path, default=None,
        help=("Katman 3 icin DOTA OBB agirligi (orn. yolov8m-obb.pt). "
              "Verilirse telemetri yokken olcek SAHNEDEKI ARACLARDAN "
              "turetilir ve guven 0.86 ile carpilir"))
    parser.add_argument(
        "--senaryo", type=str, default=None, choices=sorted(SENARYO_BOYUTLARI_M),
        help=("Katman 2 icin arena senaryosu — BEYAN EDILIR, tahmin edilmez. "
              "Yanlis senaryo 2,5 kat olcek hatasidir (50 m / 20 m)"))
    # K1 · sartname SS2.2.3 · CONTRACTS SS6.5: uretim algi yolu telsiz halkasi.
    # Hicbiri verilmezse gonderici KURULMAZ; --camera/--video davranisi
    # hedefsiz kosumla bayt-es aynidir.
    parser.add_argument(
        "--yks-hedef", type=str, default=None, metavar="IP:PORT",
        help="YKS UDP hedefi; her karede OPEN_ROUTE/NO_ROUTE + surekli HEARTBEAT")
    parser.add_argument(
        "--ika-hedef", type=str, default=None, metavar="IP:PORT",
        help="IKA UDP hedefi; rota road sozlesmesi (yerel metre waypoint) ile gider")
    parser.add_argument(
        "--telsiz-seri", type=str, default=None, metavar="PORT",
        help="SiK telsiz seri portu (saha yayin; ACK beklenmez)")
    parser.add_argument("--telsiz-baud", type=int, default=57600)
    # T162 (ON_KAYIT SS28 · sartname SS6.2/SS6.4): IHA-UB ALAN IHLALI denetimi
    # YKS'de VARDI ama uretimde `x,y` ureten yol YOKTU — kapi sahada OLUYDU.
    # Referans, IHA-UB'nin KOSESIDIR (yerel cerceve 0..kenar). BEYAN EDILIR,
    # tahmin EDILMEZ: verilmezse konum yayinlanmaz (fail-closed) ve bu ekrana
    # yazilir; "bilinmiyor" ile "0,0" ayni sey degildir.
    parser.add_argument(
        "--ub-referans", type=str, default=None, metavar="LAT,LON",
        help=("IHA-UB kose referansi (ondalik derece). Verilirse her "
              "HEARTBEAT'e yerel x,y (metre) eklenir ve YKS sartname "
              "SS6.2 ALAN IHLALI denetimini yapabilir"))
    return parser


def _ub_referansi_coz(parser, metin):
    """`LAT,LON` -> (lat, lon); gecersizse parser.error (fail-closed)."""
    if metin is None:
        return None
    parcalar = [p.strip() for p in metin.split(",")]
    if len(parcalar) != 2:
        parser.error("--ub-referans 'LAT,LON' bicimindedir")
    try:
        lat, lon = float(parcalar[0]), float(parcalar[1])
    except ValueError:
        parser.error("--ub-referans sayisal olmalidir (ondalik derece)")
    if not (abs(lat) <= 90.0 and abs(lon) <= 180.0):
        parser.error("--ub-referans bandi disi: |lat|<=90, |lon|<=180")
    return (lat, lon)


def _ub_konum_saglayici(canli_olcek, referans):
    """HEARTBEAT icin `() -> (x, y) | None` uret (T162).

    Konum, olcek ile AYNI okuyucudan gelir — ikinci bir telemetri yolu
    ACILMAZ (`karar_sozlesmesi.mpp_irtifadan` sozlesmesi). Okuyucuda konum
    yoksa ya da referans verilmemisse `None` doner ve alan YAZILMAZ.
    """
    if referans is None or canli_olcek is None:
        return None
    okuyucu = getattr(canli_olcek, "okuyucu", None)
    if okuyucu is None or not callable(getattr(okuyucu, "konum_derece", None)):
        return None

    def _saglayici():
        konum = okuyucu.konum_derece()
        if konum is None:
            return None
        return yerel_konum_m(referans[0], referans[1], konum[0], konum[1])

    return _saglayici


def _irtifa_saglayici(canli_olcek):
    """HEARTBEAT icin `() -> irtifa_m | None` (T171 · ON_KAYIT SS38).

    Sartname SS5.3.2 tespiti ASGARI 30 m irtifadan ister. Hakem ekrani bunu
    gorebilmeliydi ama URETIM heartbeat'e irtifa KOYMUYORDU — YKS `alt` alanini
    okuyor olmasina ragmen o alani ureten hicbir yol yoktu. Irtifa, konumla
    AYNI okuyucudan gelir; ikinci bir telemetri yolu ACILMAZ.
    """
    if canli_olcek is None:
        return None
    okuyucu = getattr(canli_olcek, "okuyucu", None)
    if okuyucu is None or not callable(getattr(okuyucu, "irtifa_m", None)):
        return None
    return okuyucu.irtifa_m


def _telemetri_saglayici(canli_olcek, referans=None):
    """Tek atomik okuyucu snapshot'ını HEARTBEAT alanlarına dönüştür.

    Ham ``lat``/``lon`` YKİ'de sayısal GNSS kanıtıdır; semantik haritanın
    koordinatı değildir. ``referans`` beyan edilmişse aynı snapshot'tan ayrıca
    IHA-UB yerel ``x``/``y`` üretilir. Okuyucu yoksa ikinci bir MAVLink
    tüketicisi açılmaz; ``None`` dönülür.
    """
    if canli_olcek is None:
        return None
    okuyucu = getattr(canli_olcek, "okuyucu", None)
    snapshot_al = getattr(okuyucu, "telemetri_snapshot", None)
    if not callable(snapshot_al):
        return None

    def _saglayici():
        ham = snapshot_al()
        if not isinstance(ham, dict):
            return {}
        cikti = {
            ad: ham[ad]
            for ad in ("lat", "lon", "alt", "hiz", "yon", "gps_fix",
                       "uydu", "bat", "armed", "mod", "pixhawk_canli")
            if ad in ham
        }
        if (referans is not None and "lat" in cikti and "lon" in cikti):
            x, y = yerel_konum_m(
                referans[0], referans[1], cikti["lat"], cikti["lon"])
            cikti["x"], cikti["y"] = x, y
        return cikti

    return _saglayici


def _argumanlari_dogrula(parser, args):
    """Canli kamera yolunda statik olcek/irtifa bypassini kapat."""
    if (args.mav_sysid is not None
            and not 1 <= args.mav_sysid <= 255):
        parser.error("--mav-sysid 1..255 tamsayi olmalidir")
    if args.camera and args.mpp is not None:
        parser.error("--camera statik --mpp kabul etmez; canli MAVLink gerekir")
    if args.camera and args.mavlink is None:
        parser.error("--camera icin --mavlink zorunludur")
    if args.mavlink is not None:
        # CONTRACTS §7.4: seri cihaz yolu REDDEDILIR (cikis 2). Fail-closed —
        # bayrak yoksa (elle kurulmus namespace) kilit ACIK sayilmaz.
        _inis_kaniti_modulu().seri_pixhawk_kilidini_uygula(
            parser, args.mavlink,
            getattr(args, "seri_pixhawk_bilerek", False))
        if args.mpp is not None:
            parser.error("--mavlink ile statik --mpp birlikte kullanilamaz")
        if args.mav_sysid is None:
            parser.error("--mavlink icin --mav-sysid zorunludur")
        if args.fov is None and args.odak is None:
            parser.error("--mavlink icin --fov veya --odak zorunludur")
    elif args.fov is not None or args.odak is not None:
        parser.error("--fov/--odak yalniz --mavlink ile kullanilir")
    telsiz = (args.yks_hedef, args.ika_hedef, args.telsiz_seri)
    if any(telsiz) and not (args.camera or args.video):
        parser.error("--yks-hedef/--ika-hedef/--telsiz-seri yalniz --camera "
                     "veya --video ile kullanilir")
    for hedef in (args.yks_hedef, args.ika_hedef):
        if hedef is not None and (":" not in hedef
                                  or not hedef.rsplit(":", 1)[1].isdigit()):
            parser.error(f"hedef ip:port bicminde olmali: {hedef!r}")


def main():
    parser = _arguman_ayristirici()
    args = parser.parse_args()

    if not any([args.fps, args.image, args.video, args.camera]):
        parser.print_help()
        return

    _argumanlari_dogrula(parser, args)
    # T162: referans BEYAN EDILIR; bicim/bant hatasi fail-closed (parser.error).
    ub_referans = _ub_referansi_coz(parser, args.ub_referans)

    mpp = args.mpp
    canli_olcek = None
    if args.mavlink is not None:
        try:
            canli_olcek = CanliOlcekSaglayici.baglan(
                args.mavlink,
                yatay_fov_derece=args.fov,
                odak_px=args.odak,
                beklenen_sysid=args.mav_sysid,
            )
        except Exception as exc:
            # Baglanti kurulamamasi olcege donusturulmez. Maske goruntulenebilir,
            # fakat her kare OLCEK_YOK ile rota yayinlamadan kalir.
            print(f"UYARI: canli irtifa okunamadi ({exc}) -> {OLCEK_YOK_SEBEBI}")
    if (mpp is None and canli_olcek is None and not args.fps
            and args.arac_modeli is None and args.senaryo is None):
        # Sessiz varsayilan YOK: kullanici olcegin uretilemedigini GORUR.
        # T86: kahinin 2. ve 3. katmani da acilmamissa bu uyari HALA gecerlidir.
        print("UYARI: olcek (mpp) turetilemedi -> gorev yolunda her kare "
              f"{OLCEK_YOK_SEBEBI} ile reddedilecek. Cevrimdisi kipte "
              "--mpp; canli kipte --mavlink ile --fov/--odak verin. "
              "Telemetrisiz goruntude --arac-modeli (katman 3) ya da "
              "--senaryo (katman 2) olcegi kurtarabilir.")

    # K1: telsiz halkasi YALNIZ hedef verilince kurulur. Kurulamiyorsa
    # (port/seri yok) sessiz devam YOK — kosum durur; hakem ekrani ve IKA
    # sessiz kalan bir IHA'yi baglanti kaybi sanir.
    yayinci = None
    if args.yks_hedef or args.ika_hedef or args.telsiz_seri:
        _konum_saglayici = _ub_konum_saglayici(canli_olcek, ub_referans)
        _irtifa_s = _irtifa_saglayici(canli_olcek)
        _telemetri_s = _telemetri_saglayici(canli_olcek, ub_referans)
        _yayinci_kw = {
            "yks": args.yks_hedef,
            "ika": args.ika_hedef,
            "seri": args.telsiz_seri,
            "baud": args.telsiz_baud,
            "konum_saglayici": _konum_saglayici,
            "irtifa_saglayici": _irtifa_s,
            "telemetri_saglayici": _telemetri_s,
        }
        yayinci = _iha_sender_modulu().yayinci_kur(**_yayinci_kw).start()
        print(f"telsiz halkasi: yks={args.yks_hedef} ika={args.ika_hedef} "
              f"seri={args.telsiz_seri} · heartbeat "
              f"{yayinci.heartbeat_aralik:g} s")
        # SESSIZ DUSUS YASAK: alan ihlali denetiminin acik mi kapali mi oldugu
        # sahada EKRANDAN gorulmelidir (sartname SS6.2 hakem gozetimi).
        if _konum_saglayici is None:
            print("UYARI: --ub-referans verilmedi ya da canli telemetri yok — "
                  "HEARTBEAT'e x,y EKLENMEZ; YKS ALAN IHLALI denetimi "
                  "YAPILAMAZ (sartname SS6.2/SS6.4).")
        else:
            print(f"IHA-UB referansi: {ub_referans[0]:.7f},{ub_referans[1]:.7f} "
                  f"· kenar {SARTNAME_IHA_UB_KENAR_M:.0f} m")

    # T204 (D-404 §8 KUCUK-2): SIGTERM/SIGINT -> kontrollu durdurma bayragi.
    # Isleyici dongu BASLAMADAN kurulur ve asagidaki `finally`de GERI ALINIR;
    # boylece `systemctl stop` artik `cap.release()` / `yayinci.stop()` /
    # `canli_olcek.kapat()` yollarini atlamaz (eski davranis: aninda olum).
    _eski_sinyaller = _durdurma_sinyallerini_kur()
    try:
        # T73: agirlik ARTIK argumandan gelir; verilmezse uretim manifestinden
        # turetilir. Kayit defteri uyusmazliginda `load_model` FAIL-CLOSED
        # yukselir — sessiz devam YOK (D-89 sinifi kusur).
        model, model_yolu, kayit_detay = load_model(
            args.model, kayit_zorunlu=not args.kayit_dogrulamasiz,
            ayrinti=True)
        print(f"model: {model_yolu.name} · kayit dogrulamasi: "
              f"{kayit_detay.get('durum')}")
        # T86: katman 3 dedektoru YALNIZ istenirse yuklenir — Jetson'da
        # ikinci bir 53 MB agirligi sessizce yuklemek kabul edilemez.
        arac_modeli = None
        if args.arac_modeli is not None:
            from ultralytics import YOLO as _YOLO
            arac_modeli = _YOLO(str(args.arac_modeli), task="obb")
            print(f"olcek katman 3: arac dedektoru {args.arac_modeli.name} "
                  f"yuklendi (guven carpani "
                  f"{OLCEK_GUVEN_CARPANI[OLCEK_KAYNAK_ARAC]:.2f})")
        if args.fps:
            run_fps(model)
        elif args.image:
            run_image(model, args.image, args.conf, mpp=mpp,
                      canli_olcek=canli_olcek, arac_modeli=arac_modeli,
                      senaryo=args.senaryo)
        elif args.video:
            run_video(model, args.video, args.conf, save=not args.no_save,
                      mpp=mpp, canli_olcek=canli_olcek,
                      arac_modeli=arac_modeli, senaryo=args.senaryo,
                      yayinci=yayinci, ekransiz=args.ekransiz)
        elif args.camera:
            run_camera(model, args.conf, canli_olcek=canli_olcek,
                       kaynak=args.kaynak, arac_modeli=arac_modeli,
                       senaryo=args.senaryo, yayinci=yayinci,
                       ekransiz=args.ekransiz)
    except KeyboardInterrupt:
        # Isleyici kurulamadiginda (ana iplik degil) ya da SIGINT isleyiciden
        # ONCE geldiginde hala buraya duseriz. run_* finally'leri kamerayi
        # zaten birakti; asagidaki finally telsiz halkasini kapatir. Cikis
        # kodu 0 kalir — kontrollu durdurma bir HATA degildir.
        print("KONTROLLU DURDURMA: KeyboardInterrupt.", flush=True)
    finally:
        _durdurma_sinyallerini_geri_al(_eski_sinyaller)
        if yayinci is not None:
            if yayinci.stop() is not True:
                print("UYARI: telsiz yayinci is parcacigi durmadi.")
            if yayinci.hata:
                print(f"UYARI: telsiz yayin hatalari ({len(yayinci.hata)}): "
                      f"{yayinci.hata[-1]}")
            yayinci.sender.link.close()
        if canli_olcek is not None:
            if canli_olcek.kapat() is not True:
                print("UYARI: irtifa poller'i durmadi; MAVLink baglantisi "
                      "thread altindan kapatilmadi.")


if __name__ == "__main__":
    main()
