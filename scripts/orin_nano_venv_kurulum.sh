#!/usr/bin/env bash
# NAVITAS — Jetson Orin Nano (JetPack 7.2.1, Python 3.12) KULLANICI ALANI kurulumu · 6 Eylul 2026
#
# NEDEN: paketin `wheels/` dizini cp38 (Jetson Nano / Py3.8) icindir ve bu kartta kurulmaz.
# Bu betik ~/venv312 altinda, sistem paketlerini GOREN bir venv kurar (python3-libnvinfer
# ve python3-opencv apt'tan gelir, venv icinden import edilir) ve Jetson'a ozel torch'u
# jetson-ai-lab sbsa/cu130 dizininden alir. Basarisiz olursa PyPI torch'a duser.
#
# KULLANIM:  bash orin_nano_venv_kurulum.sh          (root ISTEMEZ; once orin_nano_root_kurulum.sh kosmus olmali)
# KAPI: sonda torch.cuda.is_available() True + import tensorrt + ultralytics import.
set -euo pipefail
VENV="${VENV:-$HOME/venv312}"
JAI="${JAI:-https://pypi.jetson-ai-lab.io/sbsa/cu130}"
NAVITAS_KOK="${NAVITAS_KOK:-$HOME/navitas}"

echo "== [1/5] venv: $VENV (sistem paketleri gorunur)"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv --system-site-packages "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
python -m pip install --upgrade pip wheel setuptools >/dev/null
python -V; pip --version

echo "== [2/5] torch (jetson-ai-lab $JAI), olmazsa PyPI"
if ! python -c "import torch" 2>/dev/null; then
  if ! pip install --extra-index-url "$JAI" "torch==2.11.*" torchvision; then
    echo "   jetson-ai-lab torch kurulamadi -> PyPI torch deneniyor"
    pip install torch torchvision
  fi
fi

echo "== [3/5] ultralytics + haberlesme paketleri (requirements_nano.txt kumesi, cp38 tekerleksiz)"
pip install "ultralytics" "numpy<2" pyserial pymavlink MAVProxy lxml future onnx onnxslim

echo "== [4/5] onnxruntime (ONNX ile ucus secenegi)"
pip install --extra-index-url "$JAI" onnxruntime-gpu || pip install onnxruntime

echo "== [5/5] KAPI"
python - <<'PY'
import sys
print("python", sys.version.split()[0])
# T220 (ON_KAYIT §5.10): `"GStreamer" in getBuildInformation()` HER ZAMAN True idi (GStreamer'siz derlemede
# de "GStreamer: NO" satiri var). Dogru denetim: "GStreamer:" satirinin degeri YES mi.
import numpy, cv2, re; _g = re.search(r"^\s*GStreamer:\s*(\S+)", cv2.getBuildInformation(), re.M); print("numpy", numpy.__version__, "| cv2", cv2.__version__, "| GStreamer", (_g.group(1).upper() == "YES") if _g else "BILINMIYOR")
import torch; print("torch", torch.__version__, "| cuda", torch.cuda.is_available(), "|", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "-")
if torch.cuda.is_available():
    a = torch.randn(256, 256, device="cuda"); print("gpu matmul", float((a @ a).sum()) == float((a @ a).sum()))
try:
    import tensorrt; print("tensorrt", tensorrt.__version__)
except Exception as e:
    print("tensorrt YOK:", e)
import ultralytics; print("ultralytics", ultralytics.__version__)
import pymavlink; print("pymavlink", pymavlink.__version__)
try:
    import onnxruntime as ort; print("onnxruntime", ort.__version__, ort.get_available_providers())
except Exception as e:
    print("onnxruntime YOK:", e)
PY
which mavproxy.py
echo
echo "TAMAM. Etkinlestir: source $VENV/bin/activate   (paket koku: $NAVITAS_KOK)"
