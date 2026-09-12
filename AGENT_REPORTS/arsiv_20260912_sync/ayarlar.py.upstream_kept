"""Navitas v3 yerel eğitim — ortak ayarlar ve yardımcılar.

Kod O:\\navitas reposunda kalır (tek doğru kaynak); bu klasör yalnızca
çalışma alanıdır (venv, log, kanıt çıktıları). Colab eşleniği:
navitas-model-guclendirme.ipynb — buradaki 01→04 akışı onun birebir yerelidir.
"""
import json
import os
import subprocess
from pathlib import Path

def _depo_koku(baslangic):
    """Depo kokunu `__file__`den TURET — ciplak mutlak yol YAZILMAZ (madde 16).

    T161 (ON_KAYIT SS22 · REVIEW_LOG D-300): burada depo koku CIPLAK MUTLAK YOL
    olarak yaziliydi. 36 olcum betigi bu sabiti alip
    `sys.path.insert(0, REPO / "codes")` yaptigi icin, bir worktree'de (ya da
    deponun herhangi bir kopyasinda) kosan kapilar KENDI kodunu degil ANA
    DEPONUNKINI import ediyordu — yani ajanin yazdigi kod OLCULMEDEN yesil
    gorunebiliyordu (D-15 sinifi vakum kapi).

    ISARETCI: `CLAUDE.md` VE `codes/` tasiyan dizin. Uc kademe, bu sirayla:
      1. `NAVITAS_DEPO` ortam degiskeni (isaretci dogrulanir) — elle ezme yolu;
      2. `__file__`den YUKARI dogru ilk isaretcili dizin — worktree/kopya bunu
         bulur ve KENDI agacini gosterir (T161'in asil derdi);
      3. bu dosya deponun DISINDA calisiyorsa (canli calisma klasoru
         `olcum_ayna.py` ile buraya kopyalanir) ust dizinlerin KARDESLERINDE
         isaretcili dizin aranir; TEK aday varsa kabul edilir, BIRDEN COKSA
         reddedilir — ad tahmin edilmez.
    Hicbiri tutmazsa FAIL-CLOSED: sessizce eski sabit varsayilmaz.
    """
    import os

    def _isaretci(d):
        return (d / "CLAUDE.md").is_file() and (d / "codes").is_dir()

    ortam = os.environ.get("NAVITAS_DEPO")
    if ortam:
        aday = Path(ortam).expanduser().resolve()
        if _isaretci(aday):
            return aday
        raise ImportError(
            f"NAVITAS_DEPO isaretci tasimiyor: {aday} (CLAUDE.md + codes/)")

    baslangic = Path(baslangic).resolve()
    for aday in (baslangic, *baslangic.parents):
        if _isaretci(aday):
            return aday

    adaylar = []
    for ust in baslangic.parents:
        try:
            adaylar = sorted(d for d in ust.iterdir() if d.is_dir() and _isaretci(d))
        except OSError:
            adaylar = []
        if adaylar:
            break
    if len(adaylar) == 1:
        return adaylar[0]
    raise ImportError(
        f"depo koku bulunamadi ({baslangic}); isaretci: CLAUDE.md + codes/; "
        f"kardes aday sayisi: {len(adaylar)}. Ciplak yol varsayilmadi (T161).")


REPO    = _depo_koku(__file__)
BURASI  = Path(__file__).parent
CALISMA = BURASI / "calisma"          # log + kanıt dosyaları buraya
CALISMA.mkdir(exist_ok=True)
LOG     = CALISMA / "konsol.log"

DATA_YAML   = REPO / "dataset" / "rescuenet_yolo" / "data.yaml"
RUN_NAME    = "navitas_seg_v3"
BEST        = REPO / "codes" / "runs" / "segment" / RUN_NAME / "weights" / "best.pt"
MODEL_HEDEF = REPO / "models" / "navitas_seg_v3_best.pt"


def uretim_pt() -> Path:
    """Üretim `.pt` yolunu KAYIT DEFTERİNDEN çöz (anayasa madde 16).

    T85: ölçüm betikleri sürüm adını çıplak sabit olarak taşıyordu
    (`navitas_seg_v27_best.pt`). Sürüm v30'a geçince bu varsayılanlar
    çevrilmeseydi, argümansız koşan bir ölçüm ESKİ modeli ölçüp sonucu
    üretim modelinin sayısı diye kaydeder — D-58/D-60/D-116 kusur sınıfı.
    Tek kaynak `config/model_registry.json`'dur; bulunamazsa **düşülür**,
    sessizce bir yedeğe kaçılmaz.
    """
    kayit = REPO / "config" / "model_registry.json"
    if not kayit.is_file():
        raise RuntimeError(f"model kayit defteri yok: {kayit}")
    veri = json.loads(kayit.read_text(encoding="utf-8"))
    profil = veri["profiles"][veri["default_profile"]]
    yol = REPO / profil["path"]
    if not yol.is_file():
        raise RuntimeError(f"kayit defterinin gosterdigi model diskte yok: {yol}")
    return yol


def uretim_onnx() -> Path:
    """Sahaya giden ONNX yolunu PAKET KÜNYESİNDEN çöz (T85, madde 16)."""
    mf = REPO / "jetson_paket" / "models" / "jetson_derleme_manifest.json"
    if not mf.is_file():
        raise RuntimeError(f"jetson derleme manifesti yok: {mf}")
    ad = json.loads(mf.read_text(encoding="utf-8"))["asil_model"]
    yol = REPO / "jetson_paket" / "models" / ad
    if not yol.is_file():
        raise RuntimeError(f"manifestin `asil_model` dosyasi pakette yok: {yol}")
    return yol


def logla(*p):
    s = " ".join(str(x) for x in p)
    print(s)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(s + "\n")


def komut(args, cwd=None):
    """Alt komutu koştur; çıktıyı ekrana VE konsol.log'a akıt."""
    logla(f"\n$ {' '.join(str(a) for a in args)}")
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    pr = subprocess.Popen([str(a) for a in args], cwd=cwd, env=env,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace")
    for satir in pr.stdout:
        logla(satir.rstrip("\n").split("\r")[-1])
    pr.wait()
    logla(f"[çıkış: {pr.returncode}]")
    return pr.returncode
