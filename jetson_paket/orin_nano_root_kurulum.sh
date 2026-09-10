#!/usr/bin/env bash
# NAVITAS — Jetson Orin Nano 4GB (JetPack 7.2.1) ROOT kurulum adimlari · 6 Eylul 2026
#
# NEDEN: paket Jetson Nano (JetPack 4.6) icin hazirlanmisti; kart Orin Nano DevKit
# (L4T R39.2.1, Ubuntu 24.04, Python 3.12). wheels/ (cp38) burada kurulmaz; CUDA,
# TensorRT ve Python araclari apt ile gelir. Bu betik YALNIZ root isteyen adimlari
# toplar; venv/torch/ultralytics kurulumu ayri (kullanici alani) betiktedir.
#
# KULLANIM:  sudo bash orin_nano_root_kurulum.sh
# Her adim idempotent: ikinci kosumda atlar ya da zararsiz tekrar eder.
set -euo pipefail
HEDEF_KULLANICI="${SUDO_USER:-n4vitas}"
SWAP_BOYUT="${SWAP_BOYUT:-8G}"

echo "== [1/5] apt update"
apt-get update

echo "== [2/5] JetPack bilesenleri (CUDA 13.2, TensorRT 10.16, cuDNN) + Python araclari"
DEBIAN_FRONTEND=noninteractive apt-get install -y \
  nvidia-jetpack \
  python3-pip python3-venv python3-dev \
  python3-opencv python3-numpy \
  gstreamer1.0-tools gstreamer1.0-plugins-good \
  git

echo "== [3/5] Swap ${SWAP_BOYUT} (/swapfile, NVMe)"
if swapon --show | grep -q '^/swapfile'; then
  echo "   swap zaten acik"
else
  if [ ! -f /swapfile ]; then
    fallocate -l "$SWAP_BOYUT" /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
  fi
  swapon /swapfile
fi
grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab

echo "== [4/5] Gruplar: $HEDEF_KULLANICI -> dialout (Pixhawk/SiK), video (kamera)"
usermod -aG dialout,video "$HEDEF_KULLANICI"

echo "== [5/5] Guc kipi azami (0 = 10W) + jetson_clocks"
nvpmodel -m 0 || true
jetson_clocks || true

echo
echo "== KAPI"
echo "-- nvcc:";      /usr/local/cuda/bin/nvcc --version 2>/dev/null | tail -1 || echo "   nvcc YOK"
echo "-- tensorrt:";  dpkg -l tensorrt python3-libnvinfer 2>/dev/null | awk '/^ii/{print "   "$2, $3}'
echo "-- python3:";   python3 --version; python3 -m pip --version 2>/dev/null | head -1 || echo "   pip YOK"
# T220 (ON_KAYIT §5.10): eski denetim `'GStreamer' in cv2.getBuildInformation()` HER ZAMAN True idi —
# derleme bilgisi GStreamer'siz OpenCV'de de "GStreamer: NO" satiri tasir (PC'de olculdu: satir NO, naif True).
# Dogru denetim: "GStreamer:" satirinin degeri YES mi.
echo "-- cv2 (sistem):"; python3 -c "import cv2,re;_b=cv2.getBuildInformation();_m=re.search(r'^\s*GStreamer:\s*(\S+)',_b,re.M);print('  ',cv2.__version__,'GStreamer',(_m.group(1).upper()=='YES') if _m else 'BILINMIYOR')" 2>&1
echo "-- swap:";      free -h | awk '/Swap/{print "   "$0}'
echo "-- nvpmodel:";  nvpmodel -q 2>/dev/null | head -1
echo
echo "TAMAM. Yeni grup uyeligi icin oturumu kapatip acmak gerekir (dialout/video)."
