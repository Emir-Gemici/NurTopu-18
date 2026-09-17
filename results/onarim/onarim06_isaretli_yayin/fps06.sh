#!/bin/bash
# ONARIM-06 FPS etkisi: ayni dosya kaynagi, isaretli yayin kapali/acik, sirayla 2'ser kosu
cd ~/navitas
ls -la /tmp/onarim04_dji.avi >/dev/null || exit 3
O=/tmp/onarim06_fps; rm -rf $O; mkdir -p $O
/usr/bin/python3 scripts/kamera_koprusu.py --kaynak /tmp/onarim04_dji.avi --host 127.0.0.1 --port 8080 --fps 10 > $O/kopru.log 2>&1 &
KP=$!; sleep 4
kos() { # $1 ad, $2.. ek arg
  ad=$1; shift
  ~/venv312/bin/python -u codes/rpi_inference.py --camera --kaynak http://127.0.0.1:8080/video --mavlink udp:127.0.0.1:14550 --mav-sysid 1 --fov 63 --ekransiz "$@" > $O/$ad.log 2>&1 &
  P=$!
  for i in $(seq 1 120); do sleep 1; if [ "$ad" != "${ad#acik}" ] && [ ! -f $O/$ad.jpg ]; then curl -s -m 2 -o $O/$ad.jpg http://127.0.0.1:8081/kare.jpg || true; [ -s $O/$ad.jpg ] || rm -f $O/$ad.jpg; fi; done
  kill -INT $P; wait $P
  grep "KAMERA BITIS" $O/$ad.log
}
kos kapali1; kos acik1 --isaretli-yayin 127.0.0.1:8081; kos kapali2; kos acik2 --isaretli-yayin 127.0.0.1:8081
curl -s -m 2 http://127.0.0.1:8081/durum > /dev/null; kill -TERM $KP; wait $KP 2>/dev/null
grep -h "isaretli yayin" $O/acik1.log | head -2
ls -la $O/*.jpg
