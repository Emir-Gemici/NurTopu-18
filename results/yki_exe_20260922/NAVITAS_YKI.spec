# -*- mode: python ; coding: utf-8 -*-
"""NEDEN: radyo YKI ve mevcut yerel video islemeyi tasinabilir paketlemek."""
import json
import os
from pathlib import Path
import shutil
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

KOK = Path(SPECPATH).resolve().parents[1]
datas = collect_data_files("ultralytics") + copy_metadata("ultralytics")
datas += copy_metadata("torch") + copy_metadata("torchvision")
a = Analysis(
    [str(Path(SPECPATH) / "navitas_yki_app.py")],
    pathex=[str(KOK / x) for x in ("comms", "codes", "scripts")],
    binaries=[], datas=datas,
    hiddenimports=["yks_gui", "yer_yonlendirici", "rpi_inference", "model_registry", "karar_sozlesmesi", "serial.tools.list_ports", "pymavlink.dialects.v20.ardupilotmega", "pymavlink.dialects.v10.ardupilotmega", "ultralytics", "psutil"],
    excludes=["IPython", "jupyter", "PyQt5", "PyQt6", "PySide2", "PySide6", "mujoco", "trimesh", "tensorflow", "tensorboard", "onnxruntime"],
    hookspath=[], runtime_hooks=[], noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="NAVITAS_YKI", debug=False, strip=False, upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="NAVITAS_YKI")
destination = Path(DISTPATH) / "NAVITAS_YKI"
registry = json.loads((KOK / "config/model_registry.json").read_text(encoding="utf-8"))
for rel in ("config/model_registry.json", "data/arena_referans/sartname_s9_arena.png", "data/arena_referans/KAYNAK.md", registry["profiles"][registry["default_profile"]]["path"]):
    target = destination / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(KOK / rel, target)
guncel_arena = KOK / "data/arena_referans/WhatsApp Image 2026-09-22 at 21.24.42.jpeg"
if guncel_arena.is_file():
    target = destination / "data/arena_referans" / guncel_arena.name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(guncel_arena, target)
# Existing demo source remains available without carrying the full training set.
arena_rel = registry["profiles"][registry["default_profile"]].get("kabul_kumesi")
arena = KOK / arena_rel
if arena.is_dir():
    shutil.copytree(arena, destination / arena_rel, dirs_exist_ok=True)
(destination / "results").mkdir(exist_ok=True)
