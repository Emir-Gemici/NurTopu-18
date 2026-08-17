"""v33 — GURULTU DAYANIKLILIGI EGITIMI. v30 recetesi + TEK degisken: sensor gurultusu.

NEDEN (REVIEW_LOG D-142 · D-145, olculdu). Uretim modeli v30, gercekci
algilayici gurultusu altinda 260 karenin 8'inde KARARI CEVIRIYOR. Uc hipotez
olculdu ve UCU DE curudu:
  1. serit beraberligi (D-126)  -> 9/260 -> 8/260, ceviren 8'in 4'u TEK serit
  2. koridor varligi   (D-143)  -> ceviren 8 karenin 7'sinde envanter AYNI
  3. envanter kararliligi(D-145)-> envanter DAHA kararsiz (10/260 > 8/260)

Geriye kalan mekanizma: DEGISMEYEN bir koridor kumesi uzerinde kuresel A*'in
MALIYET BERABERLIGI. Rota, koridor kayboldugu icin degil, iki koridorun aciklik
agirlikli maliyeti birbirine cok yakin oldugu icin yer degistiriyor. Maliyet
`dt_px` alanindan, o da MASKEDEN gelir. Yani: maske gurultuye karsi ne kadar
DEGISMEZSE, beraberligi ceviren tedirginlik o kadar kucuk kalir.

D-142 "kararsizlik VERI tarafindan cozulemez" demisti; ama o olcum DOZ ekseninde
yapilmisti (gercek kare cogaltmasi 0x / 2x / 4x). GURULTU DAYANIKLILIGI AYRI BIR
EKSENDIR ve HIC denenmedi: v30 recetesinde HSV, dondurme, olcek, erasing var —
PIKSEL GURULTUSU YOK.

⚠ BU BIR IDDIA DEGIL, SINANACAK BIR HIPOTEZDIR. Kabul kurali sonuc gorulmeden
`calisma/olcum/v33_on_kayit.md` dosyasina yazilmistir (D-107 disiplini).

── TEK DEGISKEN ─────────────────────────────────────────────────────────────
Recete `56_t53_gercek_karisim.py`den AYNEN gelir (v30'un `args.yaml`i ile
dogrulandi: epochs=200 · imgsz=512 · batch=12 · seed=0 · cache=disk ·
workers=16 · model=v15_on10sinif/best.pt · data=karisim_gercek_otopark.yaml).
Bu betik receteyi KOPYALAMAZ, o betigi CAGIRIR — iki yerde iki recete
tutulmaz (madde 16).

Eklenen TEK sey: egitim orneklerinin yarisina Gauss piksel gurultusu.

── NEDEN KUTUPHANEYE DOKUNULMADI ────────────────────────────────────────────
Ultralytics'in piksel gurultusu hiperparametresi YOKTUR. `albumentations`
kurulsaydi Ultralytics KENDI varsayilan hattini da (Blur, MedianBlur, ToGray,
CLAHE) acardi — yani tek degisken olmaktan cikardi. Onun yerine
`BaseDataset.load_image` MODUL DUZEYINDE yamalanir; yama bu dosyada, surumlu
ve gorunurdur, kurulu pakete dokunmaz.

⚠ WINDOWS: DataLoader iscileri `spawn` ile AYRI SURECTIR ve ana modulu yeniden
ice aktarir; yama bu yuzden modul duzeyinde durur, `main()` icinde DEGIL. Yama
her surecte ILK ates ettiginde `calisma/olcum/v33_gurultu_kaniti.log` dosyasina
bir satir yazar — yamanin gercekten kostugunun KANITI budur, umut degil.

⚠ `cache=disk` gurultuyu ONBELLEGE YAZMAZ: Ultralytics diski
`cache_images_to_disk` ile `cv2.imread` uzerinden doldurur, `load_image`
uzerinden DEGIL. Onbellekte TEMIZ goruntu durur, gurultu her okumada YENIDEN
uretilir — yani her epoch farkli gurultu gorur.

VAL TARAFINA GURULTU VERILMEZ (`self.augment` False'tur): verilseydi en iyi
epoch secimi ve erken durdurma gurultulu bir olcute gore yapilirdi.
"""
import importlib.util
import os
import sys
from pathlib import Path

import numpy as np

BURASI = Path(__file__).parent
sys.path.insert(0, str(BURASI))

# ── AYARLAR ─────────────────────────────────────────────────────────────────
GURULTU_OLASILIGI = 0.5
# Kararlilik kapisi sigma=2/255 ile olcer (68_karar_kararliligi.py). Egitim
# araligi onu KAPSAR ve ustune cikar; tek bir sigmaya asiri uydurmamak icin
# aralik verilir.
SIGMA_ARALIGI = (0.0, 6.0)          # 0-255 olceginde
TOHUM = 20260817

KANIT = BURASI / "calisma" / "olcum" / "v33_gurultu_kaniti.log"


# ── YAMA ────────────────────────────────────────────────────────────────────
from ultralytics.data.base import BaseDataset            # noqa: E402

_ORIJINAL_LOAD_IMAGE = BaseDataset.load_image
_RNG = {}
_KANIT_YAZILDI = set()


def _rng():
    """Isci basina AYRI ve DETERMINISTIK uretec."""
    try:
        import torch.utils.data as tud
        bilgi = tud.get_worker_info()
        anahtar = 0 if bilgi is None else int(bilgi.id) + 1
    except Exception:
        anahtar = 0
    if anahtar not in _RNG:
        _RNG[anahtar] = np.random.default_rng(TOHUM + anahtar)
    return _RNG[anahtar]


def _kaniti_yaz(sigma):
    """Yamanin bu SURECTE gercekten atesledigini bir kez dosyaya yaz."""
    pid = os.getpid()
    if pid in _KANIT_YAZILDI:
        return
    _KANIT_YAZILDI.add(pid)
    try:
        KANIT.parent.mkdir(parents=True, exist_ok=True)
        with open(KANIT, "a", encoding="utf-8") as f:
            f.write(f"pid={pid} yama ATESLEDI ilk_sigma={sigma:.3f}\n")
    except Exception:
        pass                      # kanit yazilamamasi egitimi DURDURMAZ


def _gurultulu_load_image(self, i, rect_mode=True, resize_short=False):
    im, hw0, hw = _ORIJINAL_LOAD_IMAGE(self, i, rect_mode, resize_short)
    # `augment` yalniz TRAIN yukleyicisinde True'dur — val'e gurultu girmez.
    if im is None or not getattr(self, "augment", False):
        return im, hw0, hw
    rng = _rng()
    if rng.random() >= GURULTU_OLASILIGI:
        return im, hw0, hw
    sigma = float(rng.uniform(*SIGMA_ARALIGI))
    if sigma <= 0.0:
        return im, hw0, hw
    # standard_normal(dtype=float32) `normal`den belirgin hizlidir; D-108
    # egitimin GPU'ya degil VERI HATTINA bagli oldugunu olctu, yani buradaki
    # her milisaniye epoch suresine DOGRUDAN biner.
    g = rng.standard_normal(im.shape, dtype=np.float32) * sigma
    im = np.clip(im.astype(np.float32) + g, 0.0, 255.0).astype(np.uint8)
    _kaniti_yaz(sigma)
    return im, hw0, hw


BaseDataset.load_image = _gurultulu_load_image


# ── RECETEYI CAGIR (kopyalama) ──────────────────────────────────────────────
def main():
    if os.environ.get("FOR_DISABLE_CONSOLE_CTRL_HANDLER") != "1":
        print("!! FOR_DISABLE_CONSOLE_CTRL_HANDLER=1 AYARLI DEGIL — konsol "
              "kapaninca egitim IZSIZ olur (D: egitimi olduren konsol olayi).",
              flush=True)
    print(f"[v33] GURULTU YAMASI KURULDU · p={GURULTU_OLASILIGI} · "
          f"sigma~U{SIGMA_ARALIGI} · kanit -> {KANIT}", flush=True)

    yol = BURASI / "56_t53_gercek_karisim.py"
    spec = importlib.util.spec_from_file_location("recete56", yol)
    recete = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recete)          # `__main__` degil -> kendi kosmaz
    recete.main()


if __name__ == "__main__":
    main()
