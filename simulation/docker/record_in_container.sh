#!/usr/bin/env bash
# Navitas — Konteyner İÇİNDE çalışan kayıt orkestrasyonu
# Akış: Xvfb (sanal ekran) → gzserver → gzclient → ffmpeg → görev → mp4
#
# Kullanım (record.sh tarafından çağrılır):
#   bash record_in_container.sh <senaryo> <seed> <çıktı.mp4> [süre_limiti_sn]
set -u

SCENARIO="${1:-orta}"
SEED="${2:-42}"
OUT="${3:-/out/navitas_${SCENARIO}.mp4}"
HARD_LIMIT="${4:-180}"      # güvenlik: en fazla bu kadar saniye kayıt

W=1280; H=720; FPS=30
SIMDIR=/sim                 # simulation/ buraya mount edilir

export DISPLAY=:99
export GAZEBO_MODEL_PATH="$SIMDIR/models:${GAZEBO_MODEL_PATH:-}"
export QT_X11_NO_MITSHM=1

FFMPEG_PID=""; GZCLIENT_PID=""; GZSERVER_PID=""; XVFB_PID=""; WATCHDOG_PID=""

cleanup() {
    echo "[rec] temizlik..."
    [ -n "$FFMPEG_PID" ]   && kill -INT "$FFMPEG_PID"   2>/dev/null && wait "$FFMPEG_PID" 2>/dev/null
    [ -n "$WATCHDOG_PID" ] && kill "$WATCHDOG_PID"      2>/dev/null
    pkill -f gzclient 2>/dev/null
    pkill -f gzserver 2>/dev/null
    [ -n "$XVFB_PID" ]     && kill "$XVFB_PID"          2>/dev/null
}
trap cleanup EXIT

echo "════════════════════════════════════════════"
echo "  Navitas kayıt — senaryo=$SCENARIO seed=$SEED"
echo "  çözünürlük=${W}x${H}@${FPS}  →  $OUT"
echo "════════════════════════════════════════════"

# 1) Sanal ekran + pencere yöneticisi (fullscreen'in çalışması için)
echo "[rec] Xvfb :99 + openbox başlatılıyor..."
Xvfb :99 -screen 0 ${W}x${H}x24 -nolisten tcp &
XVFB_PID=$!
sleep 2
openbox &
sleep 1

# 2) Dünya dosyasını üret (kayıt modu = animasyon plugin'i gömülü)
cd "$SIMDIR"
WORLD="worlds/rec_${SCENARIO}.world"
echo "[rec] Dünya üretiliyor: $WORLD"
GEN_OUT=$(python3 scripts/world_generator.py --difficulty "$SCENARIO" --seed "$SEED" --record --output "$WORLD")
echo "$GEN_OUT"
# Plugin'in önerdiği kayıt süresi (+buffer dahili)
REC_SECONDS=$(echo "$GEN_OUT" | sed -n 's/.*RECORD_SECONDS=\([0-9]*\).*/\1/p')
[ -z "$REC_SECONDS" ] && REC_SECONDS=50
echo "[rec] Kayıt süresi: ${REC_SECONDS}s"

# 3) gzserver — DURAKLATILMIŞ başlat (kayıt t=0'da, İHA fırlatmasından yakalansın)
echo "[rec] gzserver (duraklatılmış) başlatılıyor..."
gzserver --pause "$WORLD" &
GZSERVER_PID=$!
for i in $(seq 1 30); do
    if gz stats -d 1 2>/dev/null | grep -qi "real"; then
        echo "[rec] gzserver hazır (${i}s)"; break
    fi
    sleep 1
done
sleep 2

# 4) gzclient (GUI) — kayıt modu dünyası fullscreen, openbox boyutlandırır
echo "[rec] gzclient başlatılıyor..."
gzclient &
GZCLIENT_PID=$!
sleep 7

# 5) Kayıt başlat
echo "[rec] ffmpeg kaydı başlıyor..."
ffmpeg -y -loglevel warning -f x11grab -video_size ${W}x${H} -framerate $FPS -i :99 \
    -codec:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$OUT" &
FFMPEG_PID=$!

# güvenlik watchdog: HARD_LIMIT geçilirse kaydı kes
( sleep "$HARD_LIMIT"; echo "[rec] süre limiti — durduruluyor"; kill -INT "$FFMPEG_PID" 2>/dev/null ) &
WATCHDOG_PID=$!
sleep 1

# 6) Görev otonom oynar (animasyon plugin'i İHA + İKA'yı sürer).
#    Simülasyonun başladığından emin ol, sonra süre boyunca kaydet.
echo "[rec] ── Görev oynatılıyor (İHA uçuşu + İKA navigasyonu) ──"
gz world -p 0 2>/dev/null || true   # duraklatılmışsa başlat
sleep "$REC_SECONDS"

# 7) Kaydı düzgün kapat
echo "[rec] görev süresi doldu"
echo "[rec] görev tamam, kayıt kapatılıyor"
kill "$WATCHDOG_PID" 2>/dev/null
kill -INT "$FFMPEG_PID" 2>/dev/null
wait "$FFMPEG_PID" 2>/dev/null
FFMPEG_PID=""

if [ -f "$OUT" ]; then
    echo "[rec] ✓ Video yazıldı: $OUT ($(du -h "$OUT" | cut -f1))"
else
    echo "[rec] ✗ Video oluşmadı!"
    exit 1
fi
