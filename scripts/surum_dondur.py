#!/usr/bin/env python3
"""SURUM DONDURMA — yarisan yazilimin MUHURLENMESI (sartname SS6.1, D-403 Faz B).

NEDEN: Sartname SS6.1 yarisan yazilimin FDS/SGGS/UHDR beyaniyla BIREBIR ayni
olmasini ister; muhur sonrasi mudahale YOKTUR. "Ayni" iddiasi sozle degil
OLCUMLE kurulur: dondurma aninda Jetson paketinin (scripts/jetson_paket_hazirla
.py KOPYALAR hedefleri), uretim modelinin ve kayit defterinin sha256 ozetleri
bir KUNYEYE yazilir; sonrasinda `--dogrula` bugunku dosyalari kunyeyle
karsilastirir ve her farki ADIYLA listeler. Kapi (tests/test_faz_b_surum_
dondurma.py) kunye VARKEN bu karsilastirmayi her suit kosumunda yapar; muhur
ihlali sessiz kalamaz.

Dondurma ANI kullanici karari (plan ~18 Eylul); bu betik yalniz mekanizmadir.

Kullanim:
  surum_dondur.py --dondur --etiket v36-yarisma --tarih 2026-09-18
      -> config/DONDURMA_KUNYESI.json yazar. Kirli agacta (git status
         --porcelain bos degil) REDDEDER (exit 2); `--kirli-bilerek` ile
         asilir ve kirlilik kunyeye YAZILIR (gizlenmez).
  surum_dondur.py --dogrula
      -> kunye ile bugunku dosyalar: birebir -> exit 0; fark var -> fark
         listesi + exit 1; kunye yok -> "DONDURULMADI" + exit 3.
  surum_dondur.py --goster
      -> kunyeyi basar (yoksa exit 3).

FAIL-CLOSED red sebepleri (--dondur, exit 2):
  * git okunamiyor / agac kirli (bayraksiz)
  * kayit defteri okunamiyor, model dosyasi yok
  * diskteki model ozeti defterin sha256'si ile uyusmuyor (tutarsiz durum
    muhurlenmez; `model_kayit_dogrula` zaten yuklemeyi reddederdi)
  * paket hedefi eksik ya da kanonik kaynagindan FARKLI (bayat paket
    muhurlenmez; once scripts/jetson_paket_hazirla.py kosulur)

KAPSAM SINIRI (bilerek): kunye Jetson paketini, modeli ve defteri kapsar.
YKS (comms/yks_gui.py) ve IKA benzetimi baska makinede kosar, KOPYALAR'da
yoktur ve burada muhurlenmez; `git_head` bu yuzden BILGI alanidir, dogrulama
olcutu degildir (kunyenin kendisi commit edilince HEAD zaten degisir).

Ozetler standart hashlib (codes/model_registry._sha256 — tek kaynak), git
cagrilari subprocess (yorumlayiciden bagimsiz).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
for _y in (KOK / "codes", KOK / "scripts"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

# Ozet yardimcisi TEKRAR YAZILMAZ: defterin kullandigi ozetle ayni fonksiyon
# (ad ozel ama tek kaynak; gorev emri "varsa kullan").
from model_registry import ModelRegistryError, load_registry  # noqa: E402
from model_registry import _sha256 as sha256_hesapla  # noqa: E402
from jetson_paket_hazirla import KOK as PAKET_KOK, KOPYALAR  # noqa: E402

# ── sabitler (ciplak sayi/dizge cagri yerine yazilmaz) ──────────────────────
KUNYE_GORELI = Path("config") / "DONDURMA_KUNYESI.json"
DEFTER_GORELI = Path("config") / "model_registry.json"
KUNYE_SEMA_SURUMU = 1
TARIH_BICIMI = "YYYY-MM-DD"
GIT_ZAMAN_ASIMI_S = 60.0
ONEK = "[DONDURMA]"

# Cikis kodlari — kapi ve insan bunlari AYIRT EDER.
CIKIS_TAMAM = 0          # dondurma yazildi / dogrulama birebir
CIKIS_FARK = 1           # kunye var, dosyalar farkli (MUHUR IHLALI gorunur)
CIKIS_RED = 2            # dondurma reddedildi (kirli agac, tutarsiz durum, eksik)
CIKIS_DONDURULMADI = 3   # kunye yok — henuz dondurulmadi (kusur DEGIL, durum)

# Paketin resmi listesi jetson_paket_hazirla.KOPYALAR'dir; burada yalniz
# koke GORELI (posix) cifte cevrilir ki sahte kok altinda da (birim testi)
# ayni liste calissin.
PAKET_ESLEMESI = tuple(
    (kaynak.relative_to(PAKET_KOK).as_posix(), hedef.relative_to(PAKET_KOK).as_posix())
    for kaynak, hedef in KOPYALAR.items())

# Kunyede bulunmasi ZORUNLU alanlar (kapi bunlari okur).
KUNYE_ZORUNLU_ALANLAR = ("sema_surumu", "etiket", "tarih", "git_head", "git_kirli",
                         "kirli_bilerek", "model", "registry_sha256", "paket",
                         "test_komutu", "not")

DURUM_AYNI = "AYNI"
DURUM_FARKLI = "FARKLI"
DURUM_YOK = "YOK"


class DondurmaHatasi(RuntimeError):
    """Dondurma/dogrulama ILERLEYEMEZ — sebep mesajda; cagiran exit kodunu verir."""


# ── yardimcilar ─────────────────────────────────────────────────────────────

def _git(kok: Path, *args: str) -> str:
    komut = ["git", *args]
    try:
        r = subprocess.run(komut, cwd=str(kok), capture_output=True, text=True,
                           timeout=GIT_ZAMAN_ASIMI_S)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DondurmaHatasi(f"git calistirilamadi ({' '.join(args)}): {exc}") from exc
    if r.returncode != 0:
        raise DondurmaHatasi(
            f"git {' '.join(args)} basarisiz (kod {r.returncode}): {r.stderr.strip()}")
    return r.stdout


def git_bilgisi(kok: Path) -> dict:
    """{head, kirli, durum} — okunamazsa DondurmaHatasi (fail-closed)."""
    head = _git(kok, "rev-parse", "HEAD").strip()
    if not head:
        raise DondurmaHatasi("git rev-parse HEAD bos dondu")
    durum = [s for s in _git(kok, "status", "--porcelain").splitlines() if s.strip()]
    return {"head": head, "kirli": bool(durum), "durum": durum}


def _ozet_ya_da_none(yol: Path):
    return sha256_hesapla(yol) if yol.is_file() else None


def model_bilgisi(kok: Path) -> dict:
    """Etkin profilin modelini koke gore coz; DISK ozeti defterle kiyaslanir.

    `model_registry.resolve_model` sabit ROOT'a bagli oldugu icin burada
    kullanilamaz (sahte kok); ayni kural elle uygulanir: yol yoksa RED,
    disk ozeti defter sha256'siyla birebir degilse RED.
    """
    try:
        defter = load_registry(kok / DEFTER_GORELI)
    except ModelRegistryError as exc:
        raise DondurmaHatasi(f"kayit defteri okunamadi: {exc}") from exc
    profil_adi = defter.get("default_profile")
    profil = (defter.get("profiles") or {}).get(profil_adi)
    if not isinstance(profil, dict) or not profil.get("path"):
        raise DondurmaHatasi(f"defterde etkin profil cozulemedi: {profil_adi!r}")
    model_yolu = kok / profil["path"]
    artefakt = model_yolu / profil.get("artifact", "") if model_yolu.is_dir() else model_yolu
    if not artefakt.is_file():
        raise DondurmaHatasi(f"model artefakti yok: {artefakt} (profil {profil_adi!r})")
    disk_ozet = sha256_hesapla(artefakt)
    defter_ozet = profil.get("sha256")
    if disk_ozet != defter_ozet:
        raise DondurmaHatasi(
            "model ozeti defterle UYUSMUYOR - tutarsiz durum muhurlenmez: "
            f"defter={defter_ozet} disk={disk_ozet} ({artefakt.name})")
    return {"profil": profil_adi, "model_id": profil.get("model_id"),
            "yol": artefakt.relative_to(kok).as_posix(), "sha256": disk_ozet}


def paket_ozetleri(kok: Path) -> dict:
    """{hedef_goreli: sha256}. Hedef eksik ya da kaynagindan farkliysa RED."""
    eksik, bayat, ozetler = [], [], {}
    for kaynak_g, hedef_g in PAKET_ESLEMESI:
        hedef = kok / hedef_g
        kaynak = kok / kaynak_g
        if not hedef.is_file():
            eksik.append(hedef_g)
            continue
        hedef_ozet = sha256_hesapla(hedef)
        if not kaynak.is_file() or sha256_hesapla(kaynak) != hedef_ozet:
            bayat.append(f"{hedef_g}  (kaynak: {kaynak_g})")
        ozetler[hedef_g] = hedef_ozet
    if eksik or bayat:
        satirlar = [f"  EKSIK  {y}" for y in eksik] + [f"  BAYAT  {y}" for y in bayat]
        raise DondurmaHatasi(
            "paket kanonik kaynakla BIREBIR degil - bayat/eksik paket muhurlenmez; "
            "once `scripts/jetson_paket_hazirla.py` kosun:\n" + "\n".join(satirlar))
    return ozetler


def kunye_yolu(kok: Path) -> Path:
    return kok / KUNYE_GORELI


def kunye_oku(kok: Path):
    """Kunye yoksa None; varsa dict. Bozuk kunye DondurmaHatasi (fail-closed)."""
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
    return veri


def _tarih_dogrula(metin: str) -> str:
    try:
        return _dt.date.fromisoformat(metin).isoformat()
    except (TypeError, ValueError) as exc:
        raise DondurmaHatasi(f"--tarih {TARIH_BICIMI} olmali, verilen: {metin!r}") from exc


def test_komutu_metni() -> str:
    py = sys.executable
    return (f"{py} scripts/surum_dondur.py --dogrula  &&  "
            f"{py} -m unittest discover -s tests -p test_faz_b_surum_dondurma.py")


# ── dondur ──────────────────────────────────────────────────────────────────

def kunye_uret(kok: Path, *, etiket: str, tarih: str, kirli_bilerek: bool,
               not_metni: str) -> dict:
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
    model = model_bilgisi(kok)
    registry_sha = sha256_hesapla(kok / DEFTER_GORELI)
    paket = paket_ozetleri(kok)
    kunye = {
        "sema_surumu": KUNYE_SEMA_SURUMU,
        "etiket": etiket.strip(),
        "tarih": tarih,
        "uretim_zamani_utc": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat(),
        "git_head": git["head"],
        "git_kirli": git["kirli"],
        "kirli_bilerek": bool(kirli_bilerek),
        "git_durum": git["durum"],
        "model": model,
        "registry_sha256": registry_sha,
        "paket": paket,
        "test_komutu": test_komutu_metni(),
        "not": not_metni,
    }
    onceki = kunye_oku(kok)
    if onceki is not None:
        # Yeniden muhurleme GIZLENMEZ: eski muhrun kimligi yeni kunyede durur.
        kunye["onceki_muhur"] = {a: onceki.get(a) for a in ("etiket", "tarih", "git_head")}
    return kunye


def dondur(kok: Path, *, etiket: str, tarih: str, kirli_bilerek: bool,
           not_metni: str) -> int:
    try:
        kunye = kunye_uret(kok, etiket=etiket, tarih=tarih,
                           kirli_bilerek=kirli_bilerek, not_metni=not_metni)
    except DondurmaHatasi as exc:
        print(f"{ONEK} RED: {exc}")
        return CIKIS_RED
    yol = kunye_yolu(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(kunye, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if "onceki_muhur" in kunye:
        o = kunye["onceki_muhur"]
        print(f"{ONEK} UYARI: onceki muhur DEGISTIRILDI - {o.get('etiket')} / "
              f"{o.get('tarih')} / {str(o.get('git_head'))[:12]} (kunyede kayitli)")
    if kunye["git_kirli"]:
        print(f"{ONEK} UYARI: agac KIRLIYKEN donduruldu (--kirli-bilerek); "
              f"{len(kunye['git_durum'])} satir kunyeye yazildi")
    print(f"{ONEK} DONDURULDU: etiket={kunye['etiket']} tarih={kunye['tarih']} "
          f"git_head={kunye['git_head'][:12]} model={kunye['model']['yol']} "
          f"({kunye['model']['sha256'][:12]}...) paket={len(kunye['paket'])} dosya")
    print(f"{ONEK} kunye: {yol}")
    return CIKIS_TAMAM


# ── dogrula ─────────────────────────────────────────────────────────────────

def farklari_bul(kok: Path, kunye: dict) -> list:
    """[(kategori, yol, durum, beklenen, gercek)] — yalniz AYNI olmayanlar."""
    beklenenler = [("model", kunye["model"]["yol"], kunye["model"]["sha256"]),
                   ("defter", DEFTER_GORELI.as_posix(), kunye["registry_sha256"])]
    beklenenler += [("paket", y, o) for y, o in sorted(kunye["paket"].items())]
    farklar = []
    for kategori, goreli, beklenen in beklenenler:
        gercek = _ozet_ya_da_none(kok / goreli)
        if gercek is None:
            farklar.append((kategori, goreli, DURUM_YOK, beklenen, None))
        elif gercek != beklenen:
            farklar.append((kategori, goreli, DURUM_FARKLI, beklenen, gercek))
    return farklar


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
          f"git_head={str(kunye['git_head'])[:12]} kirli={kunye['git_kirli']}")
    try:
        git = git_bilgisi(kok)
        ayni = "AYNI" if git["head"] == kunye["git_head"] else "FARKLI (bilgi; olcut dosya ozetleridir)"
        print(f"{ONEK} git HEAD simdi={git['head'][:12]} -> {ayni}; agac "
              f"{'KIRLI' if git['kirli'] else 'temiz'}")
    except DondurmaHatasi as exc:
        print(f"{ONEK} git bilgisi okunamadi (bilgi): {exc}")
    farklar = farklari_bul(kok, kunye)
    toplam = 2 + len(kunye["paket"])
    if not farklar:
        print(f"{ONEK} BIREBIR: {toplam} dosya kunyeyle ayni (model + defter + "
              f"{len(kunye['paket'])} paket)")
        return CIKIS_TAMAM
    print(f"{ONEK} MUHUR IHLALI: {len(farklar)}/{toplam} dosya kunyeden sapiyor:")
    for kategori, yol, durum, beklenen, gercek in farklar:
        print(f"  {durum:6} {kategori:6} {yol}")
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
    p = argparse.ArgumentParser(description="NAVITAS surum dondurma (sartname SS6.1)")
    kip = p.add_mutually_exclusive_group(required=True)
    kip.add_argument("--dondur", action="store_true", help="kunye yaz (muhurle)")
    kip.add_argument("--dogrula", action="store_true", help="bugunku dosyalari kunyeyle kiyasla")
    kip.add_argument("--goster", action="store_true", help="kunyeyi bas")
    p.add_argument("--etiket", default=None, help="--dondur: surum etiketi (or. v36-yarisma)")
    p.add_argument("--tarih", default=None, help=f"--dondur: dondurma tarihi {TARIH_BICIMI}")
    p.add_argument("--kirli-bilerek", action="store_true",
                   help="--dondur: kirli agaci REDDETME, kirliligi kunyeye yaz")
    p.add_argument("--not", dest="not_metni", default="",
                   help="--dondur: kunyeye serbest not")
    p.add_argument("--kok", default=str(KOK),
                   help="depo koku (varsayilan: bu depo; birim testi sahte kok verir)")
    a = p.parse_args(argv)
    kok = Path(a.kok).resolve()
    if a.dondur:
        if a.etiket is None or a.tarih is None:
            p.error("--dondur icin --etiket ve --tarih zorunlu")
        return dondur(kok, etiket=a.etiket, tarih=a.tarih,
                      kirli_bilerek=a.kirli_bilerek, not_metni=a.not_metni)
    if a.dogrula:
        return dogrula(kok)
    return goster(kok)


if __name__ == "__main__":
    sys.exit(_cli())
