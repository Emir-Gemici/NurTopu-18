# -*- mode: python ; coding: utf-8 -*-
# NAVITAS YKİ (yks_gui) tek klasörlük Windows paketi — PyInstaller spec.
# Kurulum: tools/yki_paket/paketle.bat  → dist/YKS/YKS.exe
# NEDEN onedir (onefile değil): yks_gui `Path(__file__).parents[1]` altına
# results/prova/<tarih>/hakem_log.jsonl yazar; onefile'da bu geçici dizine
# gider ve kanıt kaybolur. onedir'de kök = dist/YKS/ ve kalıcıdır.
import os
from PyInstaller.utils.hooks import collect_submodules

KOK = os.path.abspath(os.path.join(SPECPATH, "..", ".."))
COMMS = os.path.join(KOK, "comms")
CODES = os.path.join(KOK, "codes")

a = Analysis(
    [os.path.join(COMMS, "yks_gui.py")],
    pathex=[COMMS, CODES],
    binaries=[],
    datas=[],
    hiddenimports=["karar_sozlesmesi", "model_registry", "yks_monitor", "serial", "serial.tools.list_ports"]
                  + collect_submodules("pymavlink.dialects.v20"),
    hookspath=[],
    runtime_hooks=[],
    # Canlı algı (rpi_inference → ultralytics/torch) YKİ paketine girmez;
    # çıkarım Jetson'da koşar. Bunlar dışarıda bırakılınca paket ~10× küçülür.
    excludes=["torch", "torchvision", "ultralytics", "matplotlib", "scipy",
              "pandas", "IPython", "jupyter", "PyQt5", "PyQt6", "PySide2",
              "PySide6", "mujoco", "trimesh", "sklearn", "onnxruntime",
              "tensorboard", "rpi_inference"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="YKS",
    debug=False,
    strip=False,
    upx=False,
    console=True,          # konsol açık kalır: hata ve log satırları görünür
    icon=None,
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="YKS")

# --- Depo kökünden okunan dosyalar: _internal'a değil, kökün (dist/YKS) altına ---
# yks_gui `_PROJE_KOKU = parents[1]` = dist/YKS. PyInstaller `datas` `..` hedefi
# almaz; bu yüzden kopya burada, COLLECT bittikten sonra yapılır.
import shutil
_DIST = os.path.join(DISTPATH, "YKS")
for _kaynak, _hedef in (
    ("config/model_registry.json", "config/model_registry.json"),   # açılışta ZORUNLU (madde 16)
    ("data/arena_referans/sartname_s9_arena.png", "data/arena_referans/sartname_s9_arena.png"),
    ("data/arena_referans/KAYNAK.md", "data/arena_referans/KAYNAK.md"),
):
    _s = os.path.join(KOK, _kaynak); _h = os.path.join(_DIST, _hedef)
    os.makedirs(os.path.dirname(_h), exist_ok=True); shutil.copy2(_s, _h)
os.makedirs(os.path.join(_DIST, "results", "prova"), exist_ok=True)
