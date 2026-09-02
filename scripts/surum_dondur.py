#!/usr/bin/env python3
"""SURUM DONDURMA v2 — yarisan yazilimin MUHURLENMESI (sartname SS6.1, D-403/D-405 Faz B).

NEDEN: Sartname SS6.1 yarisan yazilimin FDS/SGGS/UHDR beyaniyla BIREBIR ayni
olmasini ister; muhur sonrasi mudahale YOKTUR. "Ayni" iddiasi sozle degil
OLCUMLE kurulur: dondurma aninda kapsamdaki dosyalarin ozetleri bir KUNYEYE
yazilir; sonrasinda `--dogrula` bugunku dosyalari kunyeyle karsilastirir ve
her farki ADIYLA listeler. Kapi (tests/test_faz_b_surum_dondurma.py) kunye
VARKEN bu karsilastirmayi her suit kosumunda yapar; muhur ihlali sessiz kalamaz.

Dondurma ANI kullanici karari (plan ~18 Eylul); bu betik yalniz mekanizmadir.

v2 (D-405, curutucu "MUHUR ATLATMA" bulgulari — her biri olculdu):
  S6 KRITIK  Ozet ICERIK-KANONIK: v1 ham bayt ozetliyordu; ayni commit'in CRLF
             (Windows autocrlf=true) ve LF (Linux/Jetson) checkout'lari 18/19
             dosyada "MUHUR IHLALI" diyordu. Artik metin dosyalari CRLF->LF
             normalize edilip ozetlenir, ikililer ham (`OZET_YONTEMI`, kunyede
             `ozet_yontemi`). Olculdu: normalize sonrasi iki klon 17/17 + defter esit.
  S1 ONEMLI  Ek kapsam: Jetson davranisini belirleyen ama KOPYALAR'da olmayan
             dosyalar (`SAHA_YAPILANDIRMA`: jetson_baslat.sh, systemd/*.service
             [glob: diskteki ek birimler de alinir], requirements_rpi.txt,
             kalibrasyon) ve MIMAR KARARIYLA "yarisan yazilim"in uc istasyonu
             (`YKS_IKA`: YKS + IKA benzetimi + saha_baslat) kunyeye girer.
             Dosya yoksa "YOK" yazilir (RED degil); sonradan belirirse
             --dogrula "BELIRDI" ile duser.
  S4 ONEMLI  Jetson'a GIDEN model kopyalari (jetson_paket/models — gitignore'lu)
             `paket_modelleri` olarak kunyede; --dondur'da kanonik/defterle
             bayt-es degilse RED.
  S2 ONEMLI  Ayna (jetson_paket/kod) yaninda KAYNAK yollari da (`paket_kaynak`)
             kunyede; --dogrula ikisini de kiyaslar.
  S3 ONEMLI  Kunye git'e BAGLI: --dogrula fail-closed — kunye HEAD'de degilse
             "KUNYE COMMIT EDILMEMIS", HEAD'dekiyle ayni degilse "KUNYE
             DEGISTIRILMIS", kunyedeki yollarda `git status --porcelain` bos
             degilse "IZLENEN YOLLAR KIRLI"; hepsi exit 1.
  SIRA ONEMLI Muhur sirasi: etkin profilin tensorrt turevi kayitsizsa (yer tutucu)
             --dondur "engine kayitsiz - muhur erken" ile RED; `--engine-
             kayitsiz-bilerek` asar ve kunyeye YAZILIR.

Kullanim:
  surum_dondur.py --dondur --etiket v36-yarisma --tarih 2026-09-18
      -> config/DONDURMA_KUNYESI.json yazar. Kirli agacta REDDEDER (exit 2);
         `--kirli-bilerek` ile asilir ve kirlilik kunyeye YAZILIR (gizlenmez).
         Ardindan kunye COMMIT EDILMELIDIR (cikti soyler).
  surum_dondur.py --dogrula
      -> kunye ile bugunku dosyalar + git bagi: birebir -> exit 0; fark/sorun
         -> liste + exit 1; kunye yok -> "DONDURULMADI" + exit 3.
  surum_dondur.py --goster
      -> kunyeyi basar (yoksa exit 3).

FAIL-CLOSED red sebepleri (--dondur, exit 2):
  * git okunamiyor / agac kirli (bayraksiz)
  * kayit defteri okunamiyor, model dosyasi yok
  * diskteki model ozeti defterin sha256'si ile uyusmuyor
  * paket hedefi eksik ya da kanonik kaynagindan FARKLI (once jetson_paket_hazirla.py)
  * Jetson'a giden model kopyasi eksik / kanonik ya da defterle farkli / kayitsiz
  * etkin profilin tensorrt turevi kayitsiz (bayraksiz)

Ozetler standart hashlib (ikili: codes/model_registry._sha256 — tek kaynak),
git cagrilari subprocess (yorumlayiciden bagimsiz).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

# Ozet yardimcisi TEKRAR YAZILMAZ: defterin kullandigi ozetle ayni fonksiyon
# (ad ozel ama tek kaynak; gorev emri "varsa kullan"). Turev semasi da
# defterden okunur (backend adlari, uzantilar, yer tutucu kurali) — uydurulmaz.
from model_registry import (ModelRegistryError, TUREV_BACKEND,  # noqa: E402
                            TUREV_UZANTILARI, load_registry, sha256_dogrulanmis_mi)
from model_registry import _sha256 as sha256_hesapla  # noqa: E402
from jetson_paket_hazirla import KOK as PAKET_KOK, KOPYALAR  # noqa: E402

# ── sabitler (ciplak sayi/dizge cagri yerine yazilmaz) ──────────────────────
KUNYE_GORELI = Path("config") / "DONDURMA_KUNYESI.json"
DEFTER_GORELI = Path("config") / "model_registry.json"
# v2: icerik-kanonik ozet + ek kapsam + git bagi. v1 kunye bu betikle
# DOGRULANMAZ (fail-closed: eski kunye yeni kapsami tasimiyor) — yeniden muhurlenir.
KUNYE_SEMA_SURUMU = 2
TARIH_BICIMI = "YYYY-MM-DD"
GIT_ZAMAN_ASIMI_S = 60.0
ONEK = "[DONDURMA]"

# Cikis kodlari — kapi ve insan bunlari AYIRT EDER.
CIKIS_TAMAM = 0          # dondurma yazildi / dogrulama birebir
CIKIS_FARK = 1           # kunye var, dosyalar farkli ya da git bagi kopuk (MUHUR IHLALI gorunur)
CIKIS_RED = 2            # dondurma reddedildi (kirli agac, tutarsiz durum, eksik, erken)
CIKIS_DONDURULMADI = 3   # kunye yok — henuz dondurulmadi (kusur DEGIL, durum)

# ── S6 · ozet yontemi ───────────────────────────────────────────────────────
# NEDEN (D-405 S6): git autocrlf checkout'ta metin dosyalarinin baytini
# degistirir; ham sha256 ayni commit'i iki makinede FARKLI gosterir. Metin
# uzantili ve NUL icermeyen dosya CRLF->LF normalize edilerek ozetlenir;
# ikililer (.pt .onnx .engine .npz .png ...) ham. Uzanti listesi mimar karari.
OZET_YONTEMI = "sha256 v2: metin lf-normalize | ikili ham"
METIN_UZANTILARI = frozenset({".py", ".sh", ".service", ".md", ".yaml", ".yml",
                              ".json", ".txt", ".cfg", ".ini"})
CRLF = b"\r\n"
LF = b"\n"
NUL = b"\x00"

# ── kapsam listeleri ────────────────────────────────────────────────────────
# Paketin resmi listesi jetson_paket_hazirla.KOPYALAR'dir; burada yalniz
# koke GORELI (posix) cifte cevrilir ki sahte kok altinda da (birim testi)
# ayni liste calissin.
PAKET_ESLEMESI = tuple(
    (kaynak.relative_to(PAKET_KOK).as_posix(), hedef.relative_to(PAKET_KOK).as_posix())
    for kaynak, hedef in KOPYALAR.items())

# NEDEN (D-405 S1): bu dosyalar KOPYALAR'da degildir ama Jetson'in fiili
# davranisini belirler — jetson_baslat.sh (SYSID/KIP/portlar -> /etc/navitas.env),
# systemd ExecStart uclari (CONTRACTS 7.4), requirements (kurulan surum),
# kalibrasyon (INT8/Q8). Adlar 2026-09-02'de `ls` ile dogrulandi (6 birim);
# olmayan dosya kunyeye "YOK" yazilir, RED edilmez. Mimar listesi
# "systemd/*.service" bir GLOB'dur: listede olmayan bir birim diskte belirirse
# --dondur onu da kunyeye alir, --dogrula "BELIRDI" ile duser (servis_dosyalari).
KATEGORI_SAHA = "saha_yapilandirma"
KATEGORI_YKS_IKA = "yks_ika"
SYSTEMD_DIZINI = "jetson_paket/systemd"
SERVIS_UZANTISI = ".service"
SAHA_YAPILANDIRMA = (
    "jetson_paket/jetson_baslat.sh",
    "jetson_paket/systemd/navitas-cogullayici.service",
    "jetson_paket/systemd/navitas-iha-inis-yayinci.service",
    "jetson_paket/systemd/navitas-iha-komut-alici.service",
    "jetson_paket/systemd/navitas-kamera-koprusu.service",
    "jetson_paket/systemd/navitas-rpi-inference.service",
    "jetson_paket/systemd/navitas-seri-hub.service",
    "jetson_paket/kod/requirements_rpi.txt",
    "jetson_paket/kalibrasyon/kalibrasyon.yaml",
    "jetson_paket/kalibrasyon/dogruluk_kapisi_kareleri.json",
)
# NEDEN (D-405 S1, MIMAR KARARI §2 madde 2): sartname SS6.1 "yarisan yazilim"
# yalniz Jetson degil, UC istasyondur — YKS (PARACHUTE/ARM/IKA_GO komutlari
# buradan cikar), IKA benzetimi (rota tuketimi, surus izni) ve saha baslatici.
# Liste mimarin verdigi 9 addir; protocol/link/iha_sender KOPYALAR kaynagi
# olarak `paket_kaynak`ta da durur (ayni ozet, iki kategori — kasitli).
YKS_IKA = (
    "comms/yks_gui.py",
    "comms/komut_tekrar.py",
    "comms/protocol.py",
    "comms/link.py",
    "comms/iha_sender.py",
    "comms/ika_receiver.py",
    "simulation/scripts/ika_nav.py",
    "simulation/scripts/ika_surucu.py",
    "scripts/saha_baslat.py",
)
EK_KAPSAM = {KATEGORI_SAHA: SAHA_YAPILANDIRMA, KATEGORI_YKS_IKA: YKS_IKA}

# NEDEN (D-405 S4): Jetson'a giden agirliklar `jetson_paket/models` altindadir
# ve .gitignore'ludur (git status GORMEZ); kilavuz `cp models/* ~/navitas/models/`
# der. Kunye disi kalirlarsa sahte .pt/.onnx ile --dogrula BIREBIR derdi (olculdu).
PAKET_MODEL_DIZINI = "jetson_paket/models"
KANONIK_MODEL_DIZINI = "models"
# .engine Jetson'da derlenir, PC'den GITMEZ; PC'den giden turev .onnx'tir.
# Uzantilar defterin turev semasindan (model_registry.TUREV_UZANTILARI) gelir.
ENGINE_UZANTISI = ".engine"
PAKET_TUREV_UZANTISI = ".onnx"
for _u in (ENGINE_UZANTISI, PAKET_TUREV_UZANTISI):
    if _u not in TUREV_UZANTILARI:      # defter semasi degisirse burasi SESSIZ kalmaz
        raise ImportError(f"model_registry.TUREV_UZANTILARI {_u!r} icermiyor: {sorted(TUREV_UZANTILARI)}")
ENGINE_BACKEND = TUREV_BACKEND[ENGINE_UZANTISI]          # "tensorrt" — tek kaynak
ENGINE_YOK_NOTU = "(profilde tensorrt turevi kayitli degil)"

# Kunyede dosya->ozet sozlugu tasiyan kategoriler (siralama cikti sirasidir).
KUNYE_DOSYA_KATEGORILERI = ("paket", "paket_kaynak", "paket_modelleri",
                            KATEGORI_SAHA, KATEGORI_YKS_IKA)

# Kunyede bulunmasi ZORUNLU alanlar (kapi bunlari okur). v2'de eklenenler:
# ozet_yontemi, engine_kayitsiz_bilerek, engine_kayitsiz, paket_kaynak,
# paket_modelleri, saha_yapilandirma, yks_ika — eski kunye yeni betikle
# SESSIZ gecemez (curutucu onerisi).
KUNYE_ZORUNLU_ALANLAR = ("sema_surumu", "ozet_yontemi", "etiket", "tarih", "git_head",
                         "git_kirli", "kirli_bilerek", "engine_kayitsiz_bilerek",
                         "engine_kayitsiz", "model", "registry_sha256",
                         *KUNYE_DOSYA_KATEGORILERI, "test_komutu", "not")

# Kunyenin test_komutu bu UC suiti kosar (D-405 karar 6): dondurma kapisi +
# ayna==kaynak bayt kilidi (test_jetson_comms_paketi) + paket/GUI/manifest
# model hizasi (test_uretim_modeli_hizasi).
TEST_DOSYALARI = ("test_faz_b_surum_dondurma.py", "test_jetson_comms_paketi.py",
                  "test_uretim_modeli_hizasi.py")

DURUM_AYNI = "AYNI"
DURUM_FARKLI = "FARKLI"
DURUM_YOK = "YOK"          # kunyede ozet var, diskte dosya yok  (ya da dondurmada: dosya yoktu)
DURUM_BELIRDI = "BELIRDI"  # kunyede YOK, diskte dosya var (muhur sonrasi eklendi)

KATEGORI_GENISLIGI = 18
DURUM_GENISLIGI = 7
OZET_KISA = 12


class DondurmaHatasi(RuntimeError):
    """Dondurma/dogrulama ILERLEYEMEZ — sebep mesajda; cagiran exit kodunu verir."""


# ── yardimcilar ─────────────────────────────────────────────────────────────

def _git_ham(kok: Path, *args: str) -> bytes:
    """git ciktisini BAYT olarak dondur (blob kiyasi icin); hata -> DondurmaHatasi."""
    komut = ["git", *args]
    try:
        r = subprocess.run(komut, cwd=str(kok), capture_output=True, timeout=GIT_ZAMAN_ASIMI_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DondurmaHatasi(f"git calistirilamadi ({' '.join(args)}): {exc}") from exc
    if r.returncode != 0:
        hata = r.stderr.decode("utf-8", errors="replace").strip()
        raise DondurmaHatasi(f"git {' '.join(args)} basarisiz (kod {r.returncode}): {hata}")
    return r.stdout


def _git(kok: Path, *args: str) -> str:
    return _git_ham(kok, *args).decode("utf-8", errors="replace")


def git_bilgisi(kok: Path) -> dict:
    """{head, kirli, durum} — okunamazsa DondurmaHatasi (fail-closed)."""
    head = _git(kok, "rev-parse", "HEAD").strip()
    if not head:
        raise DondurmaHatasi("git rev-parse HEAD bos dondu")
    durum = [s for s in _git(kok, "status", "--porcelain").splitlines() if s.strip()]
    return {"head": head, "kirli": bool(durum), "durum": durum}


def _lf(veri: bytes) -> bytes:
    """CRLF -> LF. Yalniz satir sonu; icerik baytina dokunmaz."""
    return veri.replace(CRLF, LF)


def sha256_kanonik(yol: Path) -> str:
    """OZET_YONTEMI: metin uzantili ve NUL icermeyen dosya LF-normalize edilip
    ozetlenir; digerleri ham (akisli — 54 MB .pt bellege alinmaz)."""
    if yol.suffix.lower() not in METIN_UZANTILARI:
        return sha256_hesapla(yol)
    veri = yol.read_bytes()
    if NUL in veri:                  # uzanti metin ama icerik ikili: ham (fail-safe)
        return hashlib.sha256(veri).hexdigest()
    return hashlib.sha256(_lf(veri)).hexdigest()


def _ozet_ya_da_none(yol: Path):
    return sha256_kanonik(yol) if yol.is_file() else None


def defter_profili(kok: Path) -> tuple:
    """(profil_adi, profil) — etkin profil; okunamazsa DondurmaHatasi."""
    try:
        defter = load_registry(kok / DEFTER_GORELI)
    except ModelRegistryError as exc:
        raise DondurmaHatasi(f"kayit defteri okunamadi: {exc}") from exc
    profil_adi = defter.get("default_profile")
    profil = (defter.get("profiles") or {}).get(profil_adi)
    if not isinstance(profil, dict) or not profil.get("path"):
        raise DondurmaHatasi(f"defterde etkin profil cozulemedi: {profil_adi!r}")
    return profil_adi, profil


def model_bilgisi(kok: Path, profil_adi: str, profil: dict) -> dict:
    """Etkin profilin modelini koke gore coz; DISK ozeti defterle kiyaslanir.

    `model_registry.resolve_model` sabit ROOT'a bagli oldugu icin burada
    kullanilamaz (sahte kok); ayni kural elle uygulanir: yol yoksa RED,
    disk ozeti defter sha256'siyla birebir degilse RED.
    """
    model_yolu = kok / profil["path"]
    artefakt = model_yolu / profil.get("artifact", "") if model_yolu.is_dir() else model_yolu
    if not artefakt.is_file():
        raise DondurmaHatasi(f"model artefakti yok: {artefakt} (profil {profil_adi!r})")
    disk_ozet = sha256_kanonik(artefakt)       # ikili -> ham; defterle ayni yontem
    defter_ozet = profil.get("sha256")
    if disk_ozet != defter_ozet:
        raise DondurmaHatasi(
            "model ozeti defterle UYUSMUYOR - tutarsiz durum muhurlenmez: "
            f"defter={defter_ozet} disk={disk_ozet} ({artefakt.name})")
    return {"profil": profil_adi, "model_id": profil.get("model_id"),
            "yol": artefakt.relative_to(kok).as_posix(), "sha256": disk_ozet}


def engine_kayitsizlari(profil: dict) -> list:
    """Etkin profilin tensorrt turevlerinden sha256'si DOGRULANMAMIS olanlarin
    adlari; hic tensorrt turevi yoksa [ENGINE_YOK_NOTU]. Bos liste = engine kayitli.

    NEDEN (D-405 sira bulgusu): defter bugun `DERLENINCE_YAZILIR` tasir; muhur
    engine kaydindan ONCE basilirsa Jetson engine'i fail-closed yuklemez ve
    kayit sonrasi defter+ayna degisip muhur ihlali dogar. Sira: once Jetson'da
    derle + --turev-kaydet, defteri PC'ye tasi + commit, SONRA --dondur.
    """
    turevler = profil.get("turevler")
    if not isinstance(turevler, dict):
        return [ENGINE_YOK_NOTU]
    engineler = {ad: k for ad, k in turevler.items()
                 if isinstance(k, dict) and k.get("backend") == ENGINE_BACKEND}
    if not engineler:
        return [ENGINE_YOK_NOTU]
    return sorted(ad for ad, k in engineler.items() if not sha256_dogrulanmis_mi(k.get("sha256")))


def paket_ozetleri(kok: Path) -> tuple:
    """({hedef_goreli: sha}, {kaynak_goreli: sha}). Hedef eksik ya da
    kaynagindan (icerik-kanonik) farkliysa RED. Kaynak ozetleri de kunyeye
    girer (D-405 S2): ayna sabit kalip kaynak degisirse --dogrula soyler."""
    eksik, bayat, hedefler, kaynaklar = [], [], {}, {}
    for kaynak_g, hedef_g in PAKET_ESLEMESI:
        hedef = kok / hedef_g
        kaynak = kok / kaynak_g
        if not hedef.is_file():
            eksik.append(hedef_g)
            continue
        hedef_ozet = sha256_kanonik(hedef)
        kaynak_ozet = sha256_kanonik(kaynak) if kaynak.is_file() else None
        if kaynak_ozet != hedef_ozet:
            bayat.append(f"{hedef_g}  (kaynak: {kaynak_g})")
        hedefler[hedef_g] = hedef_ozet
        kaynaklar[kaynak_g] = kaynak_ozet if kaynak_ozet is not None else DURUM_YOK
    if eksik or bayat:
        satirlar = [f"  EKSIK  {y}" for y in eksik] + [f"  BAYAT  {y}" for y in bayat]
        raise DondurmaHatasi(
            "paket kanonik kaynakla BIREBIR degil - bayat/eksik paket muhurlenmez; "
            "once `scripts/jetson_paket_hazirla.py` kosun:\n" + "\n".join(satirlar))
    return hedefler, kaynaklar


def paket_model_ozetleri(kok: Path, profil: dict, model: dict) -> dict:
    """{'jetson_paket/models/<ad>': sha | YOK} — Jetson'a giden agirliklar (D-405 S4).

    .pt  : ZORUNLU; kanonik model (defterle zaten dogrulandi) ile bayt-es degilse RED.
    .onnx: profilin `turevler` icindeki .onnx adlari; pakette varsa defterin
           turev sha256'si ile (ve AYNI ADLI kanonik `models/` kopyasi varsa
           onunla) bayt-es olmali, degilse RED; defterde yer tutucuysa RED
           (kayitsiz turev muhurlenmez); pakette yoksa "YOK" yazilir.
           NEDEN ad-bagimsiz defter kiyasi: 2026-09-02 olcumu — paket
           `navitas_seg_v36_best_512_fp16.onnx`, kanonik ad `navitas_seg_v36_
           best.onnx`, ikisi ve defter turev sha'si f4c9f5fe... AYNI; defter
           `--turev-kaydet` ile gercek dosyadan yazildigi icin kanonik baglayicidir.
    """
    sorunlar, ozetler = [], {}
    pt_ad = Path(model["yol"]).name
    pt_goreli = f"{PAKET_MODEL_DIZINI}/{pt_ad}"
    paket_pt = kok / pt_goreli
    if not paket_pt.is_file():
        sorunlar.append(f"EKSIK    {pt_goreli}  (kanonik: {model['yol']})")
    else:
        ozet = sha256_kanonik(paket_pt)
        if ozet != model["sha256"]:
            sorunlar.append(f"FARKLI   {pt_goreli}  (kanonik: {model['yol']} "
                            f"{model['sha256'][:OZET_KISA]}... paket {ozet[:OZET_KISA]}...)")
        ozetler[pt_goreli] = ozet
    turevler = profil.get("turevler")
    turevler = turevler if isinstance(turevler, dict) else {}
    for ad in sorted(turevler):
        if Path(ad).suffix.lower() != PAKET_TUREV_UZANTISI:
            continue
        goreli = f"{PAKET_MODEL_DIZINI}/{ad}"
        paket_t = kok / goreli
        if not paket_t.is_file():
            ozetler[goreli] = DURUM_YOK
            continue
        ozet = sha256_kanonik(paket_t)
        kayit = turevler[ad] if isinstance(turevler[ad], dict) else {}
        kayit_sha = kayit.get("sha256")
        if not sha256_dogrulanmis_mi(kayit_sha):
            sorunlar.append(f"KAYITSIZ {goreli}  (defter turev sha256 yer tutucu - "
                            "once `codes/model_registry.py --turev-kaydet`)")
        elif ozet != kayit_sha:
            sorunlar.append(f"FARKLI   {goreli}  (defter turev sha256 {kayit_sha[:OZET_KISA]}... "
                            f"paket {ozet[:OZET_KISA]}...)")
        kanonik = kok / KANONIK_MODEL_DIZINI / ad
        if kanonik.is_file() and sha256_kanonik(kanonik) != ozet:
            sorunlar.append(f"FARKLI   {goreli}  (kanonik: {KANONIK_MODEL_DIZINI}/{ad})")
        ozetler[goreli] = ozet
    if sorunlar:
        raise DondurmaHatasi(
            "Jetson'a giden model kopyalari (paket_modelleri) kanonik/defterle BIREBIR "
            "degil - sahaya giden agirlik dogrulanmadan muhurlenmez:\n  " + "\n  ".join(sorunlar))
    return ozetler


def servis_dosyalari(kok: Path) -> list:
    """`jetson_paket/systemd/*.service` — diskte BUGUN olan birimler (koke goreli, sirali).

    NEDEN: mimar listesi glob'dur; sabit liste yalniz bilinen 5 birimi tasir.
    Listede olmayan bir birim (yeni bir surec) Jetson davranisini degistirir —
    --dondur kunyeye alir, --dogrula kunyede yoksa BELIRDI der.
    """
    dizin = kok / SYSTEMD_DIZINI
    if not dizin.is_dir():
        return []
    return sorted(p.relative_to(kok).as_posix()
                  for p in dizin.glob(f"*{SERVIS_UZANTISI}") if p.is_file())


def ek_kapsam_ozetleri(kok: Path) -> dict:
    """{kategori: {yol: sha | YOK}} — S1 listeleri; olmayan dosya YOK (RED degil).
    saha_yapilandirma'ya diskteki ek .service birimleri de eklenir (glob)."""
    ozetler = {}
    for kat, liste in EK_KAPSAM.items():
        yollar = list(liste)
        if kat == KATEGORI_SAHA:
            yollar += [y for y in servis_dosyalari(kok) if y not in yollar]
        ozetler[kat] = {y: (sha256_kanonik(kok / y) if (kok / y).is_file() else DURUM_YOK)
                        for y in yollar}
    return ozetler


def kunye_yolu(kok: Path) -> Path:
    return kok / KUNYE_GORELI


def kunye_oku(kok: Path):
    """Kunye yoksa None; varsa dict. Bozuk/eksik/eski semali kunye DondurmaHatasi (fail-closed)."""
    yol = kunye_yolu(kok)
    if not yol.is_file():
        return None
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DondurmaHatasi(f"kunye okunamadi/bozuk: {yol}: {exc}") from exc
    if not isinstance(veri, dict):
        raise DondurmaHatasi(f"kunye bir JSON nesnesi degil ({type(veri).__name__}): {yol}")
    eksik = [a for a in KUNYE_ZORUNLU_ALANLAR if a not in veri]
    if eksik:
        raise DondurmaHatasi(f"kunye eksik alanli: {eksik} ({yol})")
    if veri["sema_surumu"] != KUNYE_SEMA_SURUMU:
        raise DondurmaHatasi(
            f"kunye sema surumu uyumsuz: {veri['sema_surumu']!r} (beklenen {KUNYE_SEMA_SURUMU}) - "
            f"eski kunye yeni kapsami tasimaz, yeniden muhurleyin ({yol})")
    bozuk = [a for a in KUNYE_DOSYA_KATEGORILERI if not isinstance(veri[a], dict)]
    if bozuk or not isinstance(veri["model"], dict):
        raise DondurmaHatasi(f"kunye kategori alanlari sozluk degil: {bozuk or ['model']} ({yol})")
    return veri


def kunye_beklenenleri(kunye: dict) -> list:
    """[(kategori, yol, beklenen_ozet|YOK)] — kunyenin kapsadigi HER dosya."""
    b = [("model", kunye["model"]["yol"], kunye["model"]["sha256"]),
         ("defter", DEFTER_GORELI.as_posix(), kunye["registry_sha256"])]
    for kat in KUNYE_DOSYA_KATEGORILERI:
        b += [(kat, y, o) for y, o in sorted(kunye[kat].items())]
    return b


def _tarih_dogrula(metin: str) -> str:
    try:
        return _dt.date.fromisoformat(metin).isoformat()
    except (TypeError, ValueError) as exc:
        raise DondurmaHatasi(f"--tarih {TARIH_BICIMI} olmali, verilen: {metin!r}") from exc


def test_komutu_metni() -> str:
    py = sys.executable
    parcalar = [f"{py} scripts/surum_dondur.py --dogrula"]
    parcalar += [f"{py} -m unittest discover -s tests -p {d}" for d in TEST_DOSYALARI]
    return "  &&  ".join(parcalar)


# ── dondur ──────────────────────────────────────────────────────────────────

def kunye_uret(kok: Path, *, etiket: str, tarih: str, kirli_bilerek: bool,
               not_metni: str, engine_kayitsiz_bilerek: bool = False) -> dict:
    """Kunye sozlugunu URETIR (yazmaz). Red kosullari DondurmaHatasi."""
    if not etiket or not etiket.strip():
        raise DondurmaHatasi("--etiket bos olamaz")
    tarih = _tarih_dogrula(tarih)
    git = git_bilgisi(kok)
    if git["kirli"] and not kirli_bilerek:
        raise DondurmaHatasi(
            "calisma agaci KIRLI (git status --porcelain bos degil) - "
            "commit edilmemis durum muhurlenmez. Ya commit edin ya da "
            "`--kirli-bilerek` ile kirliligi kunyeye YAZDIRARAK gecin:\n  "
            + "\n  ".join(git["durum"]))
    profil_adi, profil = defter_profili(kok)
    model = model_bilgisi(kok, profil_adi, profil)
    engine_kayitsiz = engine_kayitsizlari(profil)
    if engine_kayitsiz and not engine_kayitsiz_bilerek:
        raise DondurmaHatasi(
            "engine kayitsiz - muhur erken: etkin profilin tensorrt turevi defterde "
            f"dogrulanmis sha256 tasimiyor {engine_kayitsiz}. Sira: Jetson'da derle + "
            "`codes/model_registry.py --turev-kaydet`, defteri PC'ye tasi + commit, SONRA "
            "--dondur. Bilerek erken muhurlemek icin `--engine-kayitsiz-bilerek` "
            "(kunyeye YAZILIR).")
    registry_sha = sha256_kanonik(kok / DEFTER_GORELI)
    paket, paket_kaynak = paket_ozetleri(kok)
    paket_modelleri = paket_model_ozetleri(kok, profil, model)
    ek = ek_kapsam_ozetleri(kok)
    kunye = {
        "sema_surumu": KUNYE_SEMA_SURUMU,
        "ozet_yontemi": OZET_YONTEMI,
        "etiket": etiket.strip(),
        "tarih": tarih,
        "uretim_zamani_utc": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "git_head": git["head"],
        "git_kirli": git["kirli"],
        "kirli_bilerek": bool(kirli_bilerek),
        "git_durum": git["durum"],
        "engine_kayitsiz_bilerek": bool(engine_kayitsiz_bilerek),
        "engine_kayitsiz": engine_kayitsiz,
        "model": model,
        "registry_sha256": registry_sha,
        "paket": paket,
        "paket_kaynak": paket_kaynak,
        "paket_modelleri": paket_modelleri,
        **ek,
        "test_komutu": test_komutu_metni(),
        "not": not_metni,
    }
    # Yeniden muhurleme GIZLENMEZ: eski muhrun kimligi yeni kunyede durur;
    # eski kunye okunamiyorsa (v1 sema vb.) o da yazilir, muhur engellenmez.
    try:
        onceki = kunye_oku(kok)
    except DondurmaHatasi as exc:
        onceki = {"okunamadi": str(exc)}
    if onceki is not None:
        kunye["onceki_muhur"] = ({"okunamadi": onceki["okunamadi"]} if "okunamadi" in onceki
                                 else {a: onceki.get(a) for a in ("etiket", "tarih", "git_head")})
    return kunye


def dondur(kok: Path, *, etiket: str, tarih: str, kirli_bilerek: bool,
           not_metni: str, engine_kayitsiz_bilerek: bool = False) -> int:
    try:
        kunye = kunye_uret(kok, etiket=etiket, tarih=tarih, kirli_bilerek=kirli_bilerek,
                           not_metni=not_metni, engine_kayitsiz_bilerek=engine_kayitsiz_bilerek)
    except DondurmaHatasi as exc:
        print(f"{ONEK} RED: {exc}")
        return CIKIS_RED
    yol = kunye_yolu(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    # LF ile yazilir: diskteki kunye HEAD blob'uyla bayt-es kalsin (S3 kiyasi
    # yine de LF-normalize eder; autocrlf checkout'u CRLF'e cevirebilir).
    with yol.open("w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(kunye, indent=1, ensure_ascii=False) + "\n")
    if "onceki_muhur" in kunye:
        o = kunye["onceki_muhur"]
        print(f"{ONEK} UYARI: onceki muhur DEGISTIRILDI - {o.get('etiket')} / "
              f"{o.get('tarih')} / {str(o.get('git_head'))[:OZET_KISA]} (kunyede kayitli)")
    if kunye["git_kirli"]:
        print(f"{ONEK} UYARI: agac KIRLIYKEN donduruldu (--kirli-bilerek); "
              f"{len(kunye['git_durum'])} satir kunyeye yazildi")
    if kunye["engine_kayitsiz"]:
        print(f"{ONEK} UYARI: engine KAYITSIZKEN donduruldu (--engine-kayitsiz-bilerek): "
              f"{kunye['engine_kayitsiz']} (kunyede kayitli)")
    kapsam = " + ".join(f"{k} {len(kunye[k])}" for k in KUNYE_DOSYA_KATEGORILERI)
    print(f"{ONEK} DONDURULDU: etiket={kunye['etiket']} tarih={kunye['tarih']} "
          f"git_head={kunye['git_head'][:OZET_KISA]} model={kunye['model']['yol']} "
          f"({kunye['model']['sha256'][:OZET_KISA]}...) kapsam: {kapsam}")
    print(f"{ONEK} kunye: {yol}  ozet_yontemi: {OZET_YONTEMI}")
    print(f"{ONEK} SIMDI: git add {KUNYE_GORELI.as_posix()} && git commit  "
          "(kunye commit edilmeden --dogrula 'KUNYE COMMIT EDILMEMIS' ile DUSER)")
    return CIKIS_TAMAM


# ── dogrula ─────────────────────────────────────────────────────────────────

def farklari_bul(kok: Path, kunye: dict) -> list:
    """[(kategori, yol, durum, beklenen, gercek)] — yalniz AYNI olmayanlar."""
    farklar = []
    for kategori, goreli, beklenen in kunye_beklenenleri(kunye):
        gercek = _ozet_ya_da_none(kok / goreli)
        if beklenen == DURUM_YOK:
            if gercek is not None:
                farklar.append((kategori, goreli, DURUM_BELIRDI, beklenen, gercek))
        elif gercek is None:
            farklar.append((kategori, goreli, DURUM_YOK, beklenen, None))
        elif gercek != beklenen:
            farklar.append((kategori, goreli, DURUM_FARKLI, beklenen, gercek))
    # systemd birimi muhur sonrasi EKLENDIYSE (kunyede hic adi yok): BELIRDI.
    bilinen = set(kunye[KATEGORI_SAHA])
    for goreli in servis_dosyalari(kok):
        if goreli not in bilinen:
            farklar.append((KATEGORI_SAHA, goreli, DURUM_BELIRDI, DURUM_YOK, sha256_kanonik(kok / goreli)))
    return farklar


def kunye_git_bagi(kok: Path, kunye: dict) -> list:
    """S3 · kunyenin git'e bagi; sorun listesi (bos = baglı). git okunamazsa DondurmaHatasi.

    (a) kunye HEAD'de olmali ve HEAD blob'uyla (LF-normalize) ayni olmali —
        elle guncellenmis ya da commit edilmemis kunye muhur DEGILDIR;
    (b) kunyedeki yollarda `git status --porcelain` bos olmali — izlenen bir
        dosyanin commit'siz degisikligi muhur sonrasi mudahaledir.
    """
    sorunlar = []
    kunye_g = KUNYE_GORELI.as_posix()
    try:
        head_blob = _git_ham(kok, "show", f"HEAD:{kunye_g}")
    except DondurmaHatasi as exc:
        sorunlar.append(f"KUNYE COMMIT EDILMEMIS: {kunye_g} HEAD'de yok - "
                        f"`git add {kunye_g} && git commit` ({exc})")
    else:
        if _lf(head_blob) != _lf(kunye_yolu(kok).read_bytes()):
            sorunlar.append(f"KUNYE DEGISTIRILMIS: diskteki {kunye_g} HEAD'deki ile ayni degil - "
                            "elle guncellenmis kunye muhur degildir")
    # systemd dizini de pathspec'tedir: muhur sonrasi eklenen (untracked) birim
    # "??" ile burada da gorunur (BELIRDI ile cift kilit).
    yollar = [y for _, y, _ in kunye_beklenenleri(kunye)] + [SYSTEMD_DIZINI]
    durum = [s for s in _git(kok, "status", "--porcelain", "--", *yollar).splitlines() if s.strip()]
    if durum:
        sorunlar.append("IZLENEN YOLLAR KIRLI (git status --porcelain, kunye kapsami):\n  "
                        + "\n  ".join(durum))
    return sorunlar


def dogrula(kok: Path) -> int:
    try:
        kunye = kunye_oku(kok)
    except DondurmaHatasi as exc:
        # Bozuk muhur = dogrulanamayan muhur -> kapi DUSER (fail-closed).
        print(f"{ONEK} {DURUM_FARKLI}: {exc}")
        return CIKIS_FARK
    if kunye is None:
        print(f"{ONEK} DONDURULMADI: kunye yok ({kunye_yolu(kok)}) - henuz muhur basilmadi")
        return CIKIS_DONDURULMADI
    print(f"{ONEK} kunye: etiket={kunye['etiket']} tarih={kunye['tarih']} "
          f"git_head={str(kunye['git_head'])[:OZET_KISA]} kirli={kunye['git_kirli']} "
          f"sema={kunye['sema_surumu']} ozet_yontemi={kunye['ozet_yontemi']}")
    try:
        git = git_bilgisi(kok)
        ayni = "AYNI" if git["head"] == kunye["git_head"] else "FARKLI (bilgi; olcut dosya ozetleri + git bagidir)"
        print(f"{ONEK} git HEAD simdi={git['head'][:OZET_KISA]} -> {ayni}; agac "
              f"{'KIRLI' if git['kirli'] else 'temiz'}")
        sorunlar = kunye_git_bagi(kok, kunye)
    except DondurmaHatasi as exc:
        # git yoksa muhrun git bagi kurulamaz -> FAIL-CLOSED (v1'de yalniz bilgiydi; D-405 S3).
        sorunlar = [f"GIT OKUNAMADI - git bagi kurulamiyor, dogrulama fail-closed: {exc}"]
    for s in sorunlar:
        print(f"{ONEK} GIT BAGI: {s}")
    farklar = farklari_bul(kok, kunye)
    beklenenler = kunye_beklenenleri(kunye)
    toplam = len(beklenenler)
    if not farklar and not sorunlar:
        kapsam = " + ".join(f"{k} {len(kunye[k])}" for k in KUNYE_DOSYA_KATEGORILERI)
        print(f"{ONEK} BIREBIR: {toplam} dosya kunyeyle ayni (model + defter + {kapsam}); "
              "kunye HEAD'de, izlenen yollar temiz")
        return CIKIS_TAMAM
    print(f"{ONEK} MUHUR IHLALI: {len(farklar)}/{toplam} dosya kunyeden sapiyor, "
          f"{len(sorunlar)} git bagi sorunu:")
    for kategori, yol, durum, beklenen, gercek in farklar:
        print(f"  {durum:{DURUM_GENISLIGI}} {kategori:{KATEGORI_GENISLIGI}} {yol}")
        print(f"         kunye={beklenen}")
        print(f"         disk ={gercek}")
    return CIKIS_FARK


def goster(kok: Path) -> int:
    try:
        kunye = kunye_oku(kok)
    except DondurmaHatasi as exc:
        print(f"{ONEK} {DURUM_FARKLI}: {exc}")
        return CIKIS_FARK
    if kunye is None:
        print(f"{ONEK} DONDURULMADI: kunye yok ({kunye_yolu(kok)})")
        return CIKIS_DONDURULMADI
    print(json.dumps(kunye, indent=1, ensure_ascii=False))
    return CIKIS_TAMAM


# ── CLI ─────────────────────────────────────────────────────────────────────

def _cli(argv=None) -> int:
    p = argparse.ArgumentParser(description="NAVITAS surum dondurma v2 (sartname SS6.1)")
    kip = p.add_mutually_exclusive_group(required=True)
    kip.add_argument("--dondur", action="store_true", help="kunye yaz (muhurle)")
    kip.add_argument("--dogrula", action="store_true", help="bugunku dosyalari + git bagini kunyeyle kiyasla")
    kip.add_argument("--goster", action="store_true", help="kunyeyi bas")
    p.add_argument("--etiket", default=None, help="--dondur: surum etiketi (or. v36-yarisma)")
    p.add_argument("--tarih", default=None, help=f"--dondur: dondurma tarihi {TARIH_BICIMI}")
    p.add_argument("--kirli-bilerek", action="store_true",
                   help="--dondur: kirli agaci REDDETME, kirliligi kunyeye yaz")
    p.add_argument("--engine-kayitsiz-bilerek", action="store_true",
                   help="--dondur: tensorrt turevi kayitsizken REDDETME, kunyeye yaz (muhur erken)")
    p.add_argument("--not", dest="not_metni", default="",
                   help="--dondur: kunyeye serbest not")
    p.add_argument("--kok", default=str(KOK),
                   help="depo koku (varsayilan: bu depo; birim testi sahte kok verir)")
    a = p.parse_args(argv)
    kok = Path(a.kok).resolve()
    if a.dondur:
        if a.etiket is None or a.tarih is None:
            p.error("--dondur icin --etiket ve --tarih zorunlu")
        return dondur(kok, etiket=a.etiket, tarih=a.tarih, kirli_bilerek=a.kirli_bilerek,
                      not_metni=a.not_metni, engine_kayitsiz_bilerek=a.engine_kayitsiz_bilerek)
    if a.dogrula:
        return dogrula(kok)
    return goster(kok)


if __name__ == "__main__":
    sys.exit(_cli())
