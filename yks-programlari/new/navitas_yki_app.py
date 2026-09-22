"""NEDEN: YKI Windows paketini Python veya terminal gerektirmeden baslatmak."""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import sys
import threading
import time
import traceback


FROZEN = bool(getattr(sys, "frozen", False))
ROOT = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parents[2]
for folder in ("comms", "codes", "scripts"):
    sys.path.insert(0, str(ROOT / folder))


def cleanup_router(router):
    if router is None:
        return
    router.dur.set()
    for thread in getattr(router, "_launcher_threads", ()):
        thread.join(timeout=1.5)
    with router.kilit:
        if router.ser is not None:
            router.ser.close()
    for _, sock, _ in router.hedefler:
        sock.close()


def start_radio(port, baud, tunnel):
    from yer_yonlendirici import Yonlendirici, udp_hedefler
    targets = udp_hedefler("127.0.0.1:14550", tunnel)
    try:
        router = Yonlendirici(port, baud, targets)
    except Exception:
        for _, sock, _ in targets:
            sock.close()
        raise
    before = set(threading.enumerate())
    router.baslat()
    router._launcher_threads = [t for t in threading.enumerate() if t not in before]
    return router


def connection_dialog():
    import tkinter as tk
    from tkinter import ttk, messagebox
    from serial.tools import list_ports

    window = tk.Tk()
    window.title("NAVITAS YKİ — Bağlantı")
    window.geometry("570x370")
    window.resizable(False, False)
    panel = ttk.Frame(window, padding=24)
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="NAVITAS YKİ", font=("Segoe UI", 21, "bold")).pack(anchor="w")
    ttk.Label(panel, text="Normal radyo telemetri bağlantısı", font=("Segoe UI", 11)).pack(anchor="w", pady=(2, 20))
    mode = tk.StringVar(value="radio")
    ttk.Radiobutton(panel, text="USB radyo telemetrisi", variable=mode, value="radio").pack(anchor="w")
    row = ttk.Frame(panel)
    row.pack(fill="x", pady=(8, 14))
    ttk.Label(row, text="COM portu").pack(side="left")
    ports = [p.device for p in list_ports.comports()]
    port = tk.StringVar(value="COM7" if "COM7" in ports else (ports[0] if ports else "COM7"))
    ttk.Combobox(row, textvariable=port, values=ports, width=12).pack(side="left", padx=(10, 22))
    ttk.Label(row, text="Baud").pack(side="left")
    baud = tk.StringVar(value="57600")
    ttk.Combobox(row, textvariable=baud, values=("57600", "115200"), width=10).pack(side="left", padx=10)
    ttk.Radiobutton(panel, text="Çalışan yer yönlendiricisine / MP aynasına bağlan", variable=mode, value="tunnel").pack(anchor="w")
    ttk.Label(panel, text="YKİ: 127.0.0.1:14590    ·    Mission Planner: UDP 14550").pack(anchor="w", pady=(8, 12))
    ttk.Label(panel, text="Video bağlantısı açılışta kapalıdır.").pack(anchor="w")
    result = []

    def connect():
        try:
            rate = int(baud.get())
            if rate <= 0 or not port.get().strip():
                raise ValueError
        except ValueError:
            messagebox.showerror("Bağlantı", "Geçerli bir COM portu ve baud girin.", parent=window)
            return
        result.append((mode.get(), port.get().strip(), rate))
        window.destroy()

    ttk.Button(panel, text="YKİ'yi aç", command=connect).pack(anchor="e", pady=(18, 0))
    window.mainloop()
    return result[0] if result else None


def self_test():
    import cv2
    import psutil
    import serial
    import tkinter
    import torch
    import ultralytics
    from pymavlink.dialects.v20 import ardupilotmega
    import yks_gui
    import radio_mode
    from model_registry import resolve_model
    model_path, spec = resolve_model()
    from rpi_inference import load_model
    model = load_model(str(model_path))
    import numpy as np
    prediction = model.predict(np.zeros((512, 512, 3), dtype=np.uint8), imgsz=spec["imgsz"], verbose=False)
    return {"ok": True, "root": str(ROOT), "model": spec["model_id"],
            "prediction_count": len(prediction), "opencv": cv2.__version__, "torch": torch.__version__}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    ROOT.joinpath("results", "launcher").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("YOLO_CONFIG_DIR", str(ROOT / "results" / "ultralytics"))
    log_path = ROOT / "results" / "launcher" / (time.strftime("%Y%m%d_%H%M%S") + f"_{os.getpid()}.log")
    router = None
    with log_path.open("a", encoding="utf-8", buffering=1) as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        try:
            if "--self-test" in args:
                report = self_test()
                (ROOT / "results" / "self_test.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
                print(json.dumps(report))
                return 0
            tunnel = "127.0.0.1:14590"
            if not args:
                choice = connection_dialog()
                if choice is None:
                    return 0
                mode, port, baud = choice
                if mode == "radio":
                    router = start_radio(port, baud, tunnel)
                args = ["--mavlink", "--tunel", tunnel, "--fda"]
            elif args[0] == "--radyo":
                import argparse
                parser = argparse.ArgumentParser()
                parser.add_argument("--radyo", required=True)
                parser.add_argument("--baud", type=int, default=57600)
                options, rest = parser.parse_known_args(args)
                if any(a in rest for a in ("--serial", "--demo", "--tunel", "--bind")):
                    parser.error("--radyo başka bir taşıyıcı seçeneği ile kullanılamaz")
                router = start_radio(options.radyo, options.baud, tunnel)
                args = ["--mavlink", "--tunel", tunnel, "--fda", *rest]
            direct_radio = "--mavlink" in args
            if direct_radio:
                args.remove("--mavlink")
                if "--demo" in args or "--serial" in args:
                    raise ValueError("Doğrudan MAVLink radyo kipi demo veya ham seri kip ile birleştirilemez")
            os.environ.pop("NAVITAS_KAMERA_URL", None)
            sys.argv = [str(ROOT / "NAVITAS_YKI.exe"), *args]
            import yks_gui
            if direct_radio:
                from radio_mode import install
                install(yks_gui)
            yks_gui.main()
            return 0
        except SystemExit as exc:
            return int(exc.code or 0)
        except Exception as exc:
            traceback.print_exc()
            if "--self-test" not in args:
                import tkinter as tk
                from tkinter import messagebox
                root = tk.Tk(); root.withdraw()
                messagebox.showerror("NAVITAS YKİ açılamadı", f"{exc}\n\nCOM portu meşgulse Mission Planner bağlantısını ayırın.\nYer yönlendiricisi zaten çalışıyorsa 'Çalışan yer yönlendiricisine bağlan' seçin.\n\nKayıt: {log_path}", parent=root)
                root.destroy()
            return 1
        finally:
            cleanup_router(router)


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    raise SystemExit(main())
