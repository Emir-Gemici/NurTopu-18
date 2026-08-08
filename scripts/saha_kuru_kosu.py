"""SAHA KURU KOSUSU: Gazebo'suz, ROS'suz, gercek donanimsiz uctan uca zincir denetimi.

Kapi olcutu (TASK_QUEUE T22): CONTRACTS.md §11'deki ON halkayi sirayla dener ve
her biri icin GECTI / DUSTU / SAHIPSIZ / ATLANDI uretir. **Dusen halkada DURMAZ** —
amac dort kopuklugu AYNI kosuda gormek; ilk dususte cikmak bu betigin butun
degerini yok eder.

NEDEN var (REVIEW_LOG D-22): depodaki 58 testin tamami ya simulasyon yolunu ya
kutuphane sozlesmesini olcuyor. Saha kod yolunu (Jetson/Pi + kamera + SiK telsiz)
uctan uca sinayan tek bir test yok, bu yuzden dort ayri kopukluk ayni anda
gorunmuyor.

NEDEN simulasyon kaniti sayilmaz: navitas_sim.py `gz` ikilisinin, Gazebo
meta.txt'inin ve kendi urettigi IHA_LANDED'in varligini varsayar; sahada ucu de
yoktur. Bu yuzden bir halkanin sahibi simulation/ altindaysa halka SAHIPSIZ
sayilir (CONTRACTS.md §11.1 kural 1).

YASAKLAR (bu betikte gecmez): gz cagrisi, ROS, gercek kamera, gercek telsiz.
Ikameler: kamera -> data/raw_frames'ten gercek kare · aktarim -> loopback UDP
ve sahte seri · motor -> cagri sayan sahte surucu.

Kullanim:
    O:\\navitas-local-train\\venv\\Scripts\\python.exe -B scripts/saha_kuru_kosu.py
    ... --cikti <dizin>   ... --kare <yol>   ... --atla-cikarim
"""

from __future__ import annotations

import argparse
import ast
import json
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _yol in (KOK / "codes", KOK / "comms"):
    if str(_yol) not in sys.path:
        sys.path.insert(0, str(_yol))

# CONTRACTS.md §11.4 — halka adlari SOZLESMEDE tanimlidir, burada degistirilemez.
HALKALAR = (
    "kamera", "model_yukleme", "cikarim", "maske", "olcek",
    "hedef_konumu", "rota", "aktarim", "surus_izni", "motor",
)

GECTI, DUSTU, SAHIPSIZ, ATLANDI = "GECTI", "DUSTU", "SAHIPSIZ", "ATLANDI"


class Rapor:
    """Halka sonuclarini sirayla toplar. Dusen halkada kosu DURMAZ."""

    def __init__(self) -> None:
        self.satirlar: list[dict] = []

    def yaz(self, halka: str, durum: str, sebep: str,
            dosya: str | None = None, detay: dict | None = None,
            sure_ms: float | None = None) -> str:
        if halka not in HALKALAR:
            raise ValueError(f"sozlesmede olmayan halka adi: {halka}")
        self.satirlar.append({
            "halka": halka, "durum": durum, "sebep": sebep,
            "dosya": dosya, "detay": detay or {},
            "sure_ms": None if sure_ms is None else round(sure_ms, 1),
        })
        return durum

    def atla(self, halka: str, onceki: str) -> str:
        return self.yaz(halka, ATLANDI, f"onceki halka dustu: {onceki}")

    def durum(self, halka: str) -> str | None:
        for s in self.satirlar:
            if s["halka"] == halka:
                return s["durum"]
        return None


def _argparse_secenekleri(yol: Path) -> set[str]:
    """Bir betigin argparse ile tanimladigi uzun secenekleri AST ile cikar.

    NEDEN AST: betigi import etmek modeli yukler ve yan etki uretir; metin
    aramasi ise yorum satirlarina takilir. AST ikisinden de bagimsizdir.
    """
    try:
        agac = ast.parse(yol.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set()
    bulunan: set[str] = set()
    for dugum in ast.walk(agac):
        if not isinstance(dugum, ast.Call):
            continue
        f = dugum.func
        if not (isinstance(f, ast.Attribute) and f.attr == "add_argument"):
            continue
        for arg in dugum.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value.startswith("--"):
                    bulunan.add(arg.value)
    return bulunan


# CONTRACTS.md §11.1/1: simulation/ altindaki hicbir dosya SAHIP olamaz.
# Bir halkanin sahibi yalniz bu dizinlerde aranir.
SAHA_DIZINLERI = ("codes", "comms", "drone", "jetson_paket", "scripts")


def _gosterilebilir_yol(yol: Path, kok: Path = KOK) -> str:
    """Rapor icin yol metni. Depo disi yollarda relative_to ValueError firlatir;
    kuru kosu TEK BIR yolda bile cokmemelidir (docstring satir 4-6)."""
    try:
        return yol.relative_to(kok).as_posix()
    except ValueError:
        return str(yol)


def _modul_sembolleri(yol: Path) -> set[str]:
    """Bir modulun tanimladigi ust duzey fonksiyon/sinif/atama adlari (AST).

    NEDEN: dosya ADININ varligi o modulun ise yaradigini gostermez. Bos bir
    `iha_sender.py` stub'i da ayni ada sahiptir.
    """
    try:
        agac = ast.parse(yol.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set()
    adlar: set[str] = set()
    for dugum in agac.body:
        if isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            adlar.add(dugum.name)
        elif isinstance(dugum, ast.Assign):
            for h in dugum.targets:
                if isinstance(h, ast.Name):
                    adlar.add(h.id)
    return adlar


def _sinif_metotlari(yol: Path, sinif_adi: str) -> set[str]:
    try:
        agac = ast.parse(yol.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set()
    for dugum in ast.walk(agac):
        if isinstance(dugum, ast.ClassDef) and dugum.name == sinif_adi:
            return {g.name for g in dugum.body
                    if isinstance(g, (ast.FunctionDef, ast.AsyncFunctionDef))}
    return set()


def _motor_surucusu_bul(kok: Path, dizinler=SAHA_DIZINLERI) -> list[str]:
    """Saha kod yolunda GERCEK bir motor aktuasyon sahibi var mi? AST ile ara.

    Olcut IKI kosulu AYNI dosyada arar:
      (a) bir surucu kutuphanesi ICE AKTARILIYOR, ve
      (b) bir motor/hiz komut FONKSIYONU tanimlaniyor.

    NEDEN (b) de gerekli: yalniz (a)'ya bakmak `comms/link.py`yi motor surucusu
    sayiyordu — orasi SiK telsiz TASIYICISI, `import serial` yapiyor ama hicbir
    tekerlek dondurmuyor. Olculdu: (a)-tek olcut halkayi yanlislikla GECTI yapti.

    NEDEN AST: duz altdizgi aramasi yorumlari da sayiyordu — kusuru ITIRAF eden
    bir `# TODO: mavlink eklenecek` satiri halkayi GECTI yapiyordu; ayrica "CAN"
    altdizgisi "scan"/"canli" gibi masum kelimelerde eslesiyordu.
    """
    surucu_modulleri = {
        "serial", "pyserial", "RPi", "gpiozero", "smbus", "smbus2",
        "pymavlink", "mavutil", "dronekit", "can", "pigpio", "Jetson",
    }
    motor_adlari = ("send_vel", "set_vel", "motor", "tekerlek", "drive",
                    "surucu", "throttle")
    bulunan = []
    for dizin in dizinler:
        taban = kok / dizin
        if not taban.exists():
            continue
        for py in sorted(taban.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            try:
                agac = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            surucu: set[str] = set()
            satir = None
            motor_fn = None
            for dugum in ast.walk(agac):
                kokler: set[str] = set()
                if isinstance(dugum, ast.Import):
                    kokler = {a.name.split(".")[0] for a in dugum.names}
                elif isinstance(dugum, ast.ImportFrom) and dugum.module:
                    kokler = {dugum.module.split(".")[0]}
                elif isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if any(a in dugum.name.lower() for a in motor_adlari):
                        motor_fn = motor_fn or f"{dugum.name}:{dugum.lineno}"
                ortak = kokler & surucu_modulleri
                if ortak:
                    surucu |= ortak
                    satir = satir or dugum.lineno
            if surucu and motor_fn:
                bulunan.append(
                    f"{_gosterilebilir_yol(py, kok)}:{satir} "
                    f"({','.join(sorted(surucu))} + {motor_fn})")
    return bulunan


def _irtifadan_mpp_ureticisi_bul(kok: Path = KOK) -> str | None:
    """Irtifa/FOV'dan mpp tureten bir FONKSIYON var mi? AST ile ara.

    Olcut: fonksiyon adinda ya da donus degiskeninde `mpp` gecmeli VE parametre
    adlarindan en az biri irtifa/yukseklik/FOV ailesinden olmali. Yorum ve
    docstring metni sayilmaz — bir halkayi belgeledigi icin degil, YAPTIGI is
    icin GECTI isaretleriz.
    """
    irtifa_adlari = {"irtifa", "yukseklik", "altitude", "alt_m", "agl",
                     "fov", "fov_deg", "fov_yatay", "hfov", "vfov"}
    for aday in (kok / "codes", kok / "jetson_paket" / "kod", kok / "scripts"):
        if not aday.exists():
            continue
        for py in sorted(aday.rglob("*.py")):
            try:
                agac = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            for dugum in ast.walk(agac):
                if not isinstance(dugum, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                params = {a.arg.lower() for a in dugum.args.args}
                params |= {a.arg.lower() for a in dugum.args.kwonlyargs}
                if not (params & irtifa_adlari):
                    continue
                if "mpp" in dugum.name.lower() or "olcek" in dugum.name.lower():
                    return f"{py.relative_to(kok).as_posix()}:{dugum.lineno}"
    return None


# ─────────────────────────────────────────────────────────── halka 1: kamera
def halka_kamera(rapor: Rapor, kare_yolu: Path | None) -> tuple[str, np.ndarray | None]:
    """Olcut (§11.3): kaynak PARAMETRIK olacak ve ilk kare okunacak."""
    t0 = time.perf_counter()
    uretim = KOK / "codes" / "rpi_inference.py"
    secenekler = _argparse_secenekleri(uretim)
    parametrik = bool({"--kaynak", "--source", "--kamera", "--girdi"} & secenekler)

    if kare_yolu is None:
        adaylar = sorted(
            p for p in (KOK / "data" / "raw_frames").rglob("*")
            if p.suffix.lower() in (".jpg", ".jpeg", ".png")
        )
        kare_yolu = adaylar[0] if adaylar else None

    kare = cv2.imread(str(kare_yolu)) if kare_yolu else None
    sure = (time.perf_counter() - t0) * 1000

    if kare is None:
        rapor.yaz("kamera", DUSTU, "okunabilir kare bulunamadi (data/raw_frames bos?)",
                  "codes/rpi_inference.py:505", sure_ms=sure)
        return DUSTU, None

    if not parametrik:
        rapor.yaz(
            "kamera", DUSTU,
            "uretim girisi kaynagi PARAMETRIK almiyor: cv2.VideoCapture(0) sabit",
            "codes/rpi_inference.py:505",
            {"argparse_secenekleri": sorted(secenekler),
             "calisan_referans": "jetson_paket/kod/kamera_dogrula.py:57 (--kaynak)",
             "kare": _gosterilebilir_yol(kare_yolu), "sekil": list(kare.shape)},
            sure)
        return DUSTU, kare

    rapor.yaz("kamera", GECTI, "kaynak parametrik, kare okundu",
              "codes/rpi_inference.py:505",
              {"kare": _gosterilebilir_yol(kare_yolu), "sekil": list(kare.shape)}, sure)
    return GECTI, kare


# ──────────────────────────────────────────────────── halka 2: model yukleme
def halka_model(rapor: Rapor, kok: Path = KOK) -> tuple[str, object | None]:
    """Olcut (§11.3): yuklenen agirlik model_registry'deki etkin profille eslesecek."""
    t0 = time.perf_counter()
    try:
        import rpi_inference
    except ImportError as exc:
        rapor.yaz("model_yukleme", DUSTU, f"rpi_inference ice aktarilamadi: {exc}",
                  "codes/rpi_inference.py:32-40")
        return DUSTU, None

    model_dir = Path(rpi_inference.MODEL_DIR)
    secenekler = _argparse_secenekleri(kok / "codes" / "rpi_inference.py")

    beklenen = None
    kayit = kok / "config" / "model_registry.json"
    if kayit.exists():
        try:
            veri = json.loads(kayit.read_text(encoding="utf-8"))
            profil = veri["profiles"][veri["default_profile"]]
            beklenen = profil.get("path")
        except (json.JSONDecodeError, KeyError, OSError):
            beklenen = None

    eslesme = beklenen is not None and Path(beklenen).name == model_dir.name
    detay = {
        "yuklenen": str(model_dir.relative_to(KOK)) if model_dir.exists() else str(model_dir),
        "kayit_defteri_bekleneni": beklenen,
        "model_argumani_var": "--model" in secenekler,
        "infer_size": getattr(rpi_inference, "INFER_SIZE", None),
    }
    sure = (time.perf_counter() - t0) * 1000

    if not model_dir.exists():
        rapor.yaz("model_yukleme", DUSTU, f"model yolu diskte yok: {model_dir}",
                  "codes/rpi_inference.py:32-40", detay, sure)
        return DUSTU, None

    # Agirlik yuklense bile YANLIS agirlik yukluyorsa olcut karsilanmaz.
    durum = GECTI if (eslesme and "--model" in secenekler) else DUSTU
    sebep = ("kayit defteriyle eslesen agirlik yuklendi" if durum == GECTI else
             "yuklenen agirlik kayit defterindeki profille eslesmiyor "
             "ve --model argumani yok")
    rapor.yaz("model_yukleme", durum, sebep, "codes/rpi_inference.py:32-40", detay, sure)
    return durum, model_dir


# ───────────────────────────────────────────── halka 3-4: cikarim ve maske
def halka_cikarim_ve_maske(rapor: Rapor, kare: np.ndarray, model_dir,
                           atla: bool) -> tuple[str, dict | None, tuple | None]:
    """Olcut (§11.3): tek kare cikarimi istisnasiz tamamlanacak; maskeler {0,1}."""
    if atla:
        rapor.yaz("cikarim", ATLANDI, "--atla-cikarim verildi")
        rapor.yaz("maske", ATLANDI, "--atla-cikarim verildi")
        return ATLANDI, None, None
    if model_dir is None:
        rapor.atla("cikarim", "model_yukleme")
        rapor.atla("maske", "model_yukleme")
        return ATLANDI, None, None

    import rpi_inference
    t0 = time.perf_counter()
    try:
        model = rpi_inference.load_model()
        kare_sq, _kucuk, icerik = rpi_inference._preprocess(kare)
        sonuc = model.predict(kare_sq, imgsz=rpi_inference.INFER_SIZE,
                              conf=0.25, verbose=False)
    # GENIS yakalama BILINCLIDIR: ultralytics/NCNN saha ortaminda ModuleNotFoundError,
    # AssertionError, KeyError, cv2.error gibi cok cesitli tur firlatiyor. Dar bir
    # demet, betigin kendi garantisini ("dusen halkada DURMAZ") tam da tasarlandigi
    # ortamda bozuyordu: ncnn wheel'i olmayan taze bir Jetson'da butun kosu
    # traceback ile oluyor ve ozet.json hic yazilmiyordu.
    except (Exception, SystemExit) as exc:
        rapor.yaz("cikarim", DUSTU, f"cikarim istisna verdi: {type(exc).__name__}: {exc}",
                  "codes/rpi_inference.py:57")
        rapor.atla("maske", "cikarim")
        return DUSTU, None, None
    sure = (time.perf_counter() - t0) * 1000
    rapor.yaz("cikarim", GECTI, "tek kare cikarimi tamamlandi",
              "codes/rpi_inference.py:57",
              {"imgsz": rpi_inference.INFER_SIZE, "tuval": list(kare_sq.shape)}, sure)

    t1 = time.perf_counter()
    h, w = kare_sq.shape[:2]
    maskeler = rpi_inference.get_masks(sonuc, h, w)
    sure2 = (time.perf_counter() - t1) * 1000
    oranlar = {str(k): round(float(v.sum()) / (h * w), 4) for k, v in maskeler.items()}
    if set(maskeler) != {0, 1}:
        rapor.yaz("maske", DUSTU, f"beklenen anahtarlar {{0,1}}, gelen {set(maskeler)}",
                  "codes/rpi_inference.py:60-83", {"oranlar": oranlar}, sure2)
        return DUSTU, None, icerik
    rapor.yaz("maske", GECTI, "{0,1} anahtarli maskeler uretildi",
              "codes/rpi_inference.py:60-83", {"piksel_orani": oranlar}, sure2)
    return GECTI, maskeler, icerik


# ──────────────────────────────────────────────────────────── halka 5: olcek
def halka_olcek(rapor: Rapor, kok: Path = KOK) -> tuple[str, float | None]:
    """Olcut (§11.3): mpp irtifa + FOV'dan TURETILECEK; turetilemezse rota uretilmeyecek.

    Bu halka SAHIPSIZ cunku sahada mpp ureten hicbir kod yok. Simulasyondaki
    iha_haritala.py:66 sabiti §11.1/1 geregi sahip sayilmaz.
    """
    # DIKKAT: burada metin aramasi YAPILMAZ. "irtifa"/"fov"/"mpp" kelimeleri
    # costmap_path_finder.py'nin YORUMLARINDA geciyor ve duz grep bu dosyayi
    # sahip sanip halkayi yanlislikla GECTI yapiyordu. Olcut bir FONKSIYONUN
    # varligidir: mpp donduren ve parametrelerinde irtifa/FOV alan bir callable.
    uretici = _irtifadan_mpp_ureticisi_bul(kok)

    if uretici:
        rapor.yaz("olcek", GECTI, "irtifa+FOV tabanli mpp ureticisi bulundu", uretici)
        return GECTI, None

    # Kritik: olcek_px(None) sessizce 1 m/piksel varsayiyor — bunu OLCUP raporla.
    detay = {}
    try:
        from costmap_path_finder import R_GEREKLI_M, olcek_px
        detay = {
            "mpp_none_r_gerekli_px": round(float(olcek_px(None)["r_gerekli_px"]), 3),
            "mpp_0.0547_r_gerekli_px": round(float(olcek_px(0.0546875)["r_gerekli_px"]), 3),
            "R_GEREKLI_M": R_GEREKLI_M,
            "not": "mpp=None sessizce 1 m/piksel varsayiliyor, uyari basilmiyor",
        }
    except (ImportError, KeyError, TypeError):
        pass
    rapor.yaz("olcek", SAHIPSIZ,
              "sahada mpp ureten kod yok; iha_haritala.py:66 sabiti simulation/ altinda",
              None, detay)
    return SAHIPSIZ, None


# ───────────────────────────────────────────────────── halka 6: hedef konumu
def halka_hedef(rapor: Rapor, kok: Path = KOK) -> str:
    """Olcut (§11.3): HB konumu saha kaynagindan (algi ya da --hb) gelecek."""
    # (a) Dis girdi: --hb SAHA dizinlerinde aranir. simulation/scripts/iha_haritala.py'ye
    #     --hb eklemek bu halkayi ACMAZ — §11.1/1 o dosyayi sahip saymayi yasakliyor
    #     ve sahada Gazebo haritalayicisi zaten kosmaz.
    cli_sahibi = None
    for dizin in SAHA_DIZINLERI:
        taban = kok / dizin
        if not taban.exists():
            continue
        for py in sorted(taban.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            if {"--hb", "--hb-xy", "--hedef"} & _argparse_secenekleri(py):
                cli_sahibi = _gosterilebilir_yol(py, kok)
                break
        if cli_sahibi:
            break

    # (b) Algi: yalniz ETKIN profil sayilir. Atil/deneysel 3 sinifli bir profil
    #     kaydetmek uretimde hedefi gorunur kilmaz (halka_model de default_profile
    #     okuyor; iki halka ayni kaynaktan okumali).
    hedef_sinifi = False
    etkin_profil = None
    kayit = kok / "config" / "model_registry.json"
    if kayit.exists():
        try:
            veri = json.loads(kayit.read_text(encoding="utf-8"))
            etkin_profil = veri.get("default_profile")
            profil = veri.get("profiles", {}).get(etkin_profil, {})
            hedef_sinifi = len(profil.get("classes", {})) >= 3
        except (json.JSONDecodeError, OSError, TypeError):
            pass

    # Gazebo tarafi yalniz TANI amaciyla raporlanir, karara GIRMEZ.
    haritala = kok / "simulation" / "scripts" / "iha_haritala.py"
    gazebo_secenekleri = _argparse_secenekleri(haritala) if haritala.exists() else set()

    detay = {"saha_cli_sahibi": cli_sahibi, "etkin_profil": etkin_profil,
             "etkin_profilde_hedef_sinifi": hedef_sinifi,
             "gazebo_haritalayici_argparse": sorted(gazebo_secenekleri),
             "meta_okuyucu": "simulation/scripts/iha_haritala.py:507",
             "meta_yazici": "simulation/scripts/world_generator.py:590",
             "kayit": "REVIEW_LOG.md D-23"}

    if cli_sahibi or hedef_sinifi:
        return rapor.yaz("hedef_konumu", GECTI,
                         "HB saha kaynagindan alinabiliyor",
                         cli_sahibi or f"config/model_registry.json:{etkin_profil}",
                         detay)
    return rapor.yaz(
        "hedef_konumu", SAHIPSIZ,
        "HB'nin tek kaynagi Gazebo meta.txt; saha kod yolunda --hb girisi yok ve "
        "etkin model profili 2 sinifli (kirmizi H'yi goren bilesen yok)",
        None, detay)


# ───────────────────────────────────────────────────────────── halka 7: rota
def halka_rota(rapor: Rapor, maskeler: dict | None, icerik: tuple | None,
               onceki: str) -> tuple[str, dict | None]:
    """Olcut (§11.3): letterbox'li girdide de ICERIK kutusuna gore karar."""
    if maskeler is None:
        return rapor.atla("rota", onceki), None
    try:
        from costmap_path_finder import rota_bul
    except ImportError as exc:
        return rapor.yaz("rota", DUSTU, f"costmap_path_finder ice aktarilamadi: {exc}",
                         "codes/costmap_path_finder.py:729"), None

    t0 = time.perf_counter()
    sonuc = rota_bul(maskeler, mpp=None)
    sure = (time.perf_counter() - t0) * 1000

    # Ayni maske ICERIGE kirpilinca karar degisiyor mu? Degisiyorsa tohum bandi
    # dolguya dusuyor demektir (D-25) ve rota halkasi letterbox'ta kordur.
    kirpik_durum = None
    if icerik:
        x0, y0, w, h = icerik
        kirpik = {k: v[y0:y0 + h, x0:x0 + w] for k, v in maskeler.items()}
        try:
            kirpik_durum = rota_bul(kirpik, mpp=None)["durum"]
        except (ValueError, IndexError):
            kirpik_durum = None

    detay = {
        "durum": sonuc["durum"], "yol_no": sonuc.get("yol_no"),
        "kirpik_durum": kirpik_durum,
        "icerik_parametresi_var": "icerik" in rota_bul.__code__.co_varnames,
    }
    if kirpik_durum is not None and kirpik_durum != sonuc["durum"]:
        return rapor.yaz(
            "rota", DUSTU,
            f"letterbox'li girdide durum={sonuc['durum']}, ayni maske kirpilinca "
            f"durum={kirpik_durum} — tohum bandi dolguya dusuyor",
            "codes/costmap_path_finder.py:232-242", detay, sure), sonuc
    if sonuc["durum"] != "ACIK":
        return rapor.yaz("rota", DUSTU, f"rota uretilemedi: durum={sonuc['durum']}",
                         "codes/costmap_path_finder.py:729", detay, sure), sonuc
    return rapor.yaz("rota", GECTI, f"rota uretildi: yol_no={sonuc.get('yol_no')}",
                     "codes/costmap_path_finder.py:729", detay, sure), sonuc


# ─────────────────────────────────────────────────────────── halka 8: aktarim
def halka_aktarim(rapor: Rapor, kok: Path = KOK) -> str:
    """Olcut (§11.3): SAHA PAKETINDEN OPEN_ROUTE gonderilip ACK alinabilecek.

    Aktarimin kutuphane tarafi (comms/) calisiyor; sinanmasi gereken sey
    saha paketinin bu kodu TASIYIP tasimadigidir.
    """
    paket = kok / "jetson_paket" / "kod"
    gerekli = {"protocol.py", "iha_sender.py", "link.py"}
    mevcut = {p.name for p in paket.glob("*.py")} if paket.exists() else set()
    eksik = sorted(gerekli - mevcut)

    req = paket / "requirements_rpi.txt"
    req_metin = req.read_text(encoding="utf-8", errors="replace") if req.exists() else ""
    pyserial_var = "pyserial" in req_metin.lower() or "serial" in req_metin.lower()

    # Dosya ADI yetmez: bos bir stub da ayni ada sahiptir. Paketlenen modullerin
    # gercekten gerekli API'yi TANIMLADIGINI AST ile dogrula.
    beklenen_semboller = {
        "protocol.py": {"open_route", "rota_yok", "iha_landed", "encode", "decode"},
        "iha_sender.py": {"IhaSender"},
        "link.py": {"UDPLink", "SerialLink"},
    }
    eksik_semboller: dict[str, list[str]] = {}
    for ad, gerekli_semboller in beklenen_semboller.items():
        dosya = paket / ad
        if not dosya.exists():
            continue
        yok = sorted(gerekli_semboller - _modul_sembolleri(dosya))
        if ad == "iha_sender.py" and not yok:
            metotlar = _sinif_metotlari(dosya, "IhaSender")
            yok = sorted({"send_open_route", "send_no_route"} - metotlar)
        if yok:
            eksik_semboller[ad] = yok

    detay = {"paket_icerigi": sorted(mevcut), "eksik_moduller": eksik,
             "eksik_semboller": eksik_semboller,
             "pyserial_bagimliligi": pyserial_var,
             # DIKKAT: bu prob DEPO comms/ dizinini olcer, saha paketini DEGIL.
             # Adi bilerek boyle; "aktarim calisiyor" diye okunmamali.
             "depo_comms_loopback": None}

    # Kutuphane tarafi (depo comms/) gercekten calisiyor mu? Loopback UDP ile OLCEK.
    try:
        from ika_receiver import IkaReceiver
        from iha_sender import IhaSender
        from link import UDPLink
        alici_link = UDPLink(bind=("127.0.0.1", 0))
        rx = IkaReceiver(alici_link).start()
        adres = alici_link.sock.getsockname()
        tx = IhaSender(UDPLink(), {"ika": adres})
        seq, acked = tx.send_open_route(2, 0.9, [(0.0, 0.0), (0.0, 2.0)], (0.0, 0.0),
                                        repeat=4, interval=0.1, wait_ack=True)
        detay["depo_comms_loopback"] = {"seq": seq, "ack": sorted(acked),
                                        "alindi": rx.latest is not None}
        rx.stop()
        alici_link.close()
        tx.link.close()
    except (ImportError, OSError, socket.error, AttributeError) as exc:
        detay["depo_comms_loopback"] = f"HATA: {type(exc).__name__}: {exc}"

    if eksik or eksik_semboller or not pyserial_var:
        parcalar = []
        if eksik:
            parcalar.append(f"eksik modul: {', '.join(eksik)}")
        if eksik_semboller:
            parcalar.append(f"bos/eksik stub: {json.dumps(eksik_semboller, ensure_ascii=False)}")
        if not pyserial_var:
            parcalar.append("pyserial bagimliligi yok")
        return rapor.yaz(
            "aktarim", SAHIPSIZ,
            f"saha paketi haberlesme kodunu tasimiyor ({'; '.join(parcalar)})",
            None, detay)
    return rapor.yaz("aktarim", GECTI,
                     "saha paketi haberlesme kodunu ve gerekli API'yi tasiyor",
                     "jetson_paket/kod/iha_sender.py", detay)


def _surus_kapisi_probu() -> dict:
    """Surus izni kapisi GERCEKTEN iki latch'i birden mi ariyor? Mesaj enjekte et.

    NEDEN yeniden yazildi: onceki prob `IkaReceiver(link)` kurup hic `.start()`
    etmiyor ve hicbir mesaj gondermiyordu; `wait_surus_izni()` bu yuzden her
    kosulda False donuyordu. Kapi gecerlilik kontrolu tumuyle kaldirilarak
    mutasyona ugratildiginda bile prob ayni sonucu basiyordu — yani hicbir sey
    olcmuyordu. Simdi uc gozlem yapilir ve UCU BIRDEN dogru olmali:
      bos -> kapali · yalniz IKA_GO -> KAPALI · IKA_GO + IHA_LANDED -> ACIK
    """
    try:
        from ika_receiver import IkaReceiver
        from link import UDPLink
        from protocol import command, encode, iha_landed
    except ImportError as exc:
        return {"hata": f"{type(exc).__name__}: {exc}"}

    alici_link = tx = None
    rx = None
    try:
        alici_link = UDPLink(bind=("127.0.0.1", 0))
        rx = IkaReceiver(alici_link).start()
        adres = alici_link.sock.getsockname()
        tx = UDPLink()

        gozlem = {"bos_kapali": not rx.wait_surus_izni(timeout=0.2)}

        tx.send(encode(command("IKA_GO", "ika")), adres)
        time.sleep(0.3)
        gozlem["yalniz_ika_go_kapali"] = not rx.wait_surus_izni(timeout=0.2)
        gozlem["ika_go_alindi"] = bool(getattr(rx, "ika_go", False))

        tx.send(encode(iha_landed()), adres)
        time.sleep(0.3)
        gozlem["iki_latch_ile_acik"] = bool(rx.wait_surus_izni(timeout=0.5))
        gozlem["iha_landed_alindi"] = bool(getattr(rx, "iha_landed", False))

        # Prob ancak UCUNU birden dogrulayabilirse anlamlidir.
        gozlem["prob_gecerli"] = (gozlem["bos_kapali"]
                                  and gozlem["yalniz_ika_go_kapali"]
                                  and gozlem["iki_latch_ile_acik"])
        return gozlem
    except (OSError, socket.error, AttributeError, ValueError) as exc:
        return {"hata": f"{type(exc).__name__}: {exc}"}
    finally:
        for kaynak in (rx, alici_link, tx):
            try:
                if kaynak is rx and rx is not None:
                    rx.stop()
                elif kaynak is not None:
                    kaynak.close()
            except (OSError, AttributeError):
                pass


# ──────────────────────────────────────────────────────── halka 9: surus izni
def halka_surus_izni(rapor: Rapor, kok: Path = KOK) -> str:
    """Olcut (§11.3): uc kosul da SAHA kaynagindan gelecek.

    Kapi dogru yazilmis (ika_receiver); sinanmasi gereken sey beslemesidir.
    """
    # Yalniz URETIM dizinleri taranir. tests/ disaridadir: test fixture'lari
    # icinde gecen `send_iha_landed(` bir saha ureticisi DEGILDIR — bu tam olarak
    # T23'un yakaladigi yanlis pozitifti (kendi test dosyasi saha ureticisi sanildi).
    uretim_dizinleri = ("codes", "comms", "drone", "jetson_paket", "scripts",
                        "simulation")
    uretenler = []
    for dizin in uretim_dizinleri:
        taban = kok / dizin
        if not taban.exists():
            continue
        for py in sorted(taban.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            # AST: gercek CAGRI dugumu aranir. Duz metin aramasi yorum satirini
            # da uretici sayiyordu (bu betigin kendi yorumu dahil) — T23 yakaladi.
            try:
                agac = ast.parse(py.read_text(encoding="utf-8", errors="replace"))
            except (OSError, SyntaxError):
                continue
            for dugum in ast.walk(agac):
                if (isinstance(dugum, ast.Call)
                        and isinstance(dugum.func, ast.Attribute)
                        and dugum.func.attr == "send_iha_landed"):
                    uretenler.append(
                        f"{py.relative_to(kok).as_posix()}:{dugum.lineno}")

    saha_ureticileri = [u for u in uretenler if not u.startswith("simulation/")]
    detay = {"tum_ureticiler": uretenler, "saha_ureticileri": saha_ureticileri}

    detay["kapi_probu"] = _surus_kapisi_probu()

    if saha_ureticileri:
        return rapor.yaz("surus_izni", GECTI,
                         "IHA_LANDED saha kod yolunda uretiliyor",
                         saha_ureticileri[0], detay)
    return rapor.yaz(
        "surus_izni", DUSTU,
        "kapi dogru ama beslemesi kopuk: IHA_LANDED yalnizca simulation/ altinda "
        "uretiliyor, saha kod yolunda uretici yok",
        "comms/ika_receiver.py:119-121", detay)


# ─────────────────────────────────────────────────────────── halka 10: motor
def halka_motor(rapor: Rapor, kok: Path = KOK) -> str:
    """Olcut (§11.3): gercek surucuye komut gidecek; gz yalnizca bir arka uc olacak."""
    # Surucu SAHA dizinlerinde aranir (§11.1/1). simulation/scripts/ika_nav.py'ye
    # surucu eklemek bu halkayi ACMAZ; sahada o dosya Gazebo'ya baglidir.
    surucu_yerleri = _motor_surucusu_bul(kok)

    nav = kok / "simulation" / "scripts" / "ika_nav.py"
    metin = nav.read_text(encoding="utf-8", errors="replace") if nav.exists() else ""
    gz_var = '"gz"' in metin or "'gz'" in metin
    detay = {"gz_subprocess": gz_var,
             "saha_surucu_importlari": surucu_yerleri,
             "taranan_dizinler": list(SAHA_DIZINLERI),
             "simulasyon_sahibi": "simulation/scripts/ika_nav.py:90-99",
             "not": "capture_output=True oldugu icin gz yoksa hata YUTULUYOR"}

    if surucu_yerleri:
        return rapor.yaz("motor", GECTI,
                         f"saha kod yolunda gercek surucu import'u bulundu: "
                         f"{surucu_yerleri[0]}",
                         surucu_yerleri[0].split(" ")[0], detay)
    return rapor.yaz(
        "motor", SAHIPSIZ,
        "gercek motor surucusu yok; send_vel yalnizca gz subprocess'i "
        "ve ika_nav simulation/ altinda",
        None, detay)


def kosuyu_yap(kare_yolu: Path | None, atla_cikarim: bool) -> Rapor:
    rapor = Rapor()
    kamera_durum, kare = halka_kamera(rapor, kare_yolu)

    if kare is None:
        for h in ("model_yukleme", "cikarim", "maske"):
            rapor.atla(h, "kamera")
        maskeler = icerik = model_dir = None
    else:
        _model_durum, model_dir = halka_model(rapor)
        _c, maskeler, icerik = halka_cikarim_ve_maske(rapor, kare, model_dir, atla_cikarim)

    halka_olcek(rapor)
    halka_hedef(rapor)
    halka_rota(rapor, maskeler, icerik, "maske")
    halka_aktarim(rapor)
    halka_surus_izni(rapor)
    halka_motor(rapor)
    return rapor


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cikti", type=Path, default=None,
                    help="sonuc dizini (varsayilan results/saha_kuru_kosu_<tarih>)")
    ap.add_argument("--kare", type=Path, default=None,
                    help="kullanilacak kare; verilmezse data/raw_frames'ten ilk kare")
    ap.add_argument("--atla-cikarim", action="store_true",
                    help="model cikarimini atla (hizli kosum; cikarim/maske ATLANDI olur)")
    args = ap.parse_args()

    rapor = kosuyu_yap(args.kare, args.atla_cikarim)

    genislik = max(len(h) for h in HALKALAR)
    print("=" * 78)
    print("SAHA KURU KOSUSU — CONTRACTS.md §11 · Gazebo YOK · donanim YOK")
    print("=" * 78)
    for s in rapor.satirlar:
        sure = "" if s["sure_ms"] is None else f"  [{s['sure_ms']:.0f} ms]"
        print(f"  {s['halka']:<{genislik}}  {s['durum']:<9}  {s['sebep']}{sure}")
        if s["dosya"]:
            print(f"  {'':<{genislik}}  {'':<9}  -> {s['dosya']}")
    print("-" * 78)

    sayim = {d: sum(1 for s in rapor.satirlar if s["durum"] == d)
             for d in (GECTI, DUSTU, SAHIPSIZ, ATLANDI)}
    kopuk = [s["halka"] for s in rapor.satirlar if s["durum"] in (DUSTU, SAHIPSIZ)]
    print(f"GECTI {sayim[GECTI]} · DUSTU {sayim[DUSTU]} · "
          f"SAHIPSIZ {sayim[SAHIPSIZ]} · ATLANDI {sayim[ATLANDI]}")
    if kopuk:
        print(f"KOPUK HALKALAR ({len(kopuk)}): {', '.join(kopuk)}")
        print("Zincir saha kosumunda TAMAMLANMAZ.")
    else:
        print("[GECTI] Saha zincirinin on halkasi da olcutunu karsiliyor.")

    damga = datetime.now().strftime("%Y%m%d_%H%M%S")
    cikti = args.cikti or (KOK / "results" / f"saha_kuru_kosu_{damga}")
    cikti.mkdir(parents=True, exist_ok=True)
    ozet = {
        "tarih": damga,
        "sozlesme": "CONTRACTS.md §11",
        "halka_sirasi": list(HALKALAR),
        "satirlar": rapor.satirlar,
        "sayim": sayim,
        "kopuk_halkalar": kopuk,
        "cikis_kodu": 1 if kopuk else 0,
    }
    (cikti / "ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Cikti: {cikti}")
    return 1 if kopuk else 0


if __name__ == "__main__":
    sys.exit(main())
