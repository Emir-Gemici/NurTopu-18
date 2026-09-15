#!/usr/bin/env bash
# Navitas — İKA "BİLİNEN ROTA" DEMO render'ı (host tarafı)
#
# ⚠ BU GERÇEK ALGI/MODEL ZİNCİRİ DEĞİLDİR. record.sh'deki İHA-haritalama
# izleyicisi (host .venv, gerçek model çıkarımı, dürüst zincir) burada
# ÇALIŞMAZ. İKA, world_generator.py'nin --record modunda zaten bastığı
# ground-truth ROUTE_XY koordinatlarıyla (navitas_anim.cc'nin İKA için
# beklediği /tmp/navitas_route dosyası, elle bu koordinatlarla dolduruluyor)
# yürütülür.
#
# Amaç: SADECE görsel demo/sunum kanıtı (FDR/TEKNOFEST sunumu) — "İKA zaten
# bildiği koordinattan yürüyor" gösterimi. Hakem/model doğruluğu KANITI
# DEĞİLDİR, record.sh üretim pipeline'ına karışmaz/dokunmaz.
#
# Kullanım:
#   ./demo_render_ika_bilinen_rota.sh kolay
#   ./demo_render_ika_bilinen_rota.sh orta --seed 260822 --map 1 --profile cx_teknofest_official
#   ./demo_render_ika_bilinen_rota.sh zor --duration 5400 --layout field   # --duration = DUVAR sınırı (sn)
#
# Çıktı: simulation/recordings/demo_bilinen_rota_<seviye>_<zaman>/
#   world.world, ground_truth_route.txt, frames/*.jpg, ETIKET_OKU.md, gzserver.log
set -e

cd "$(dirname "$0")"
SIM="$(cd .. && pwd)"
IMAGE="navitas-gazebo:11"

LEVEL="${1:?seviye gerekli: kolay|orta|zor}"; shift
case "$LEVEL" in kolay|orta|zor) ;; *) echo "Bilinmeyen seviye: $LEVEL (kolay|orta|zor)"; exit 1 ;; esac

SEED=42; MAP=1; PROFILE=""; TERRAIN=plain; LAYOUT=clean; DURATION=3600  # DUVAR sınırı (sn)
while [ $# -gt 0 ]; do
    case "$1" in
        --seed) SEED="$2"; shift ;;
        --map) MAP="$2"; shift ;;
        --profile) PROFILE="$2"; shift ;;
        --terrain) TERRAIN="$2"; shift ;;
        --layout) LAYOUT="$2"; shift ;;
        --duration) DURATION="$2"; shift ;;
        *) echo "Bilinmeyen argüman: $1"; exit 1 ;;
    esac
    shift
done

if ! podman image exists "$IMAGE"; then
    echo "[demo] İmaj yok: $IMAGE — önce ./record.sh bir kez çalıştırılmalı (imajı derler)."
    exit 1
fi

OUTDIR="$SIM/recordings/demo_bilinen_rota_${LEVEL}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR/frames"

GEN_ARGS=(--focus "$LEVEL" --seed "$SEED" --map "$MAP" --record --terrain "$TERRAIN" --layout "$LAYOUT" --output "$OUTDIR/world.world")
[ -n "$PROFILE" ] && GEN_ARGS+=(--profile "$PROFILE")

GEN_OUT="$(python3 "$SIM/scripts/world_generator.py" "${GEN_ARGS[@]}")"
echo "$GEN_OUT" | tee "$OUTDIR/world_generator.log"

ROUTE_XY=$(echo "$GEN_OUT" | sed -n 's/.*ROUTE_XY=\(.*\)$/\1/p')
[ -n "$ROUTE_XY" ] || { echo "[demo] ROUTE_XY üretilemedi (world_generator.py --record çıktısı beklenmiyordu)"; exit 1; }

ROUTE_FILE="$OUTDIR/ground_truth_route.txt"
NAVITAS_ROUTE_XY="$ROUTE_XY" python3 -c "
import os
pts = os.environ['NAVITAS_ROUTE_XY'].split(';')
with open('$ROUTE_FILE', 'w') as f:
    for p in pts:
        x, y = p.split(',')
        f.write(f'{x} {y}\n')
"

cat > "$OUTDIR/ETIKET_OKU.md" <<EOF2
# ⚠ BİLİNEN ROTA DEMO — GERÇEK ALGI DEĞİL

Bu klasördeki render, İKA'nın world_generator.py'nin zaten ürettiği
ground-truth ROUTE_XY koordinatlarıyla yürütüldüğü bir DEMO'dur.
record.sh'deki gerçek İHA-haritalama modeli (dürüst zincir, iha_haritala.py)
BURADA ÇALIŞMADI. Hakem/model doğruluğu kanıtı olarak KULLANILAMAZ — yalnız
görsel sunum/FDR amaçlıdır.

Seviye: $LEVEL · seed=$SEED · map=$MAP · layout=$LAYOUT · terrain=$TERRAIN
ROUTE_XY: $ROUTE_XY
EOF2

echo "[demo] gzserver başlıyor (~${DURATION}s render, seviye=$LEVEL)…"
podman run --rm \
    -v "$SIM":/sim:z \
    -v "$SIM/media":/navitas_res/media:z \
    -v "$OUTDIR":/check:z \
    -v "$OUTDIR/frames":/tmp/frames:z \
    --shm-size=1g \
    -e GAZEBO_MODEL_PATH=/sim/models:/usr/share/gazebo-11/models \
    -e LIBGL_ALWAYS_SOFTWARE=1 -e GALLIUM_DRIVER=llvmpipe \
    "$IMAGE" bash -c "
set -e
Xvfb :99 -screen 0 1280x720x24 &
sleep 2
export DISPLAY=:99
cp /check/ground_truth_route.txt /tmp/navitas_route
rm -f /tmp/navitas_model_log.csv /tmp/navitas_simtime
gzserver --verbose /check/world.world > /check/gzserver.log 2>&1 &
GZPID=\$!
# Bekleme SİM saatine bağlı (duvar saati değil — llvmpipe altında sim ~15x yavaş).
# İKA durum=BITTI → +TAIL sim-sn kuyruk; ROTA_YOK → hata; --duration = DUVAR sınırı.
TAIL=5; W=0; SON=YOK; BITIS=-1
while [ \$W -lt $DURATION ]; do
    sleep 5; W=\$((W+5))
    kill -0 \$GZPID 2>/dev/null || { SON=GZSERVER_OLDU; break; }
    ST=\$(head -1 /tmp/navitas_simtime 2>/dev/null || true); ST=\${ST:-0}   # set -e: dosya henüz yok
    L=\$(grep '^ika_' /tmp/navitas_simtime 2>/dev/null | tail -1 || true)
    case \"\$L\" in *durum=ROTA_YOK*) SON=ROTA_YOK; break ;; esac
    case \"\$L\" in *durum=BITTI*) [ \$BITIS -lt 0 ] && BITIS=\$ST ;; esac
    if [ \$BITIS -ge 0 ] && [ \$ST -ge \$((BITIS+TAIL)) ]; then SON=BITTI; break; fi
done
[ \$W -ge $DURATION ] && [ \$SON = YOK ] && SON=DUVAR_SINIRI || true
ST=\$(head -1 /tmp/navitas_simtime 2>/dev/null || true); ST=\${ST:-0}
kill \$GZPID 2>/dev/null || true
sleep 2
cp /tmp/navitas_model_log.csv /check/model_log.csv 2>/dev/null || true
printf 'SON_DURUM=%s\nSIM_T=%s\nWALL_SECONDS=%s\n' \"\$SON\" \"\$ST\" \"\$W\" > /check/meta.txt
echo \"[demo] SON_DURUM=\$SON sim=\${ST}s duvar=\${W}s\"
# Video: GERÇEK-ZAMAN hız (efektif fps = kare / sim-sn; sabit fps hızlandırır).
NF=\$(ls /tmp/frames/*.jpg 2>/dev/null | wc -l)
if [ \$NF -gt 3 ] && [ \$ST -gt 0 ]; then
    FPS_EFF=\$NF/\$ST   # tam oran (yuvarlama %3+ hızlandırıyordu)
    ffmpeg -y -loglevel warning -framerate \$FPS_EFF -pattern_type glob -i '/tmp/frames/*.jpg' \
        -r 30 -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p /check/ika_${LEVEL}.mp4
    echo \"[demo] video: \$NF kare / \${ST}s sim → \${FPS_EFF}fps\"
fi
[ \$SON = BITTI ]
"

echo "[demo] Tamam → $OUTDIR (ika_${LEVEL}.mp4, frames/, meta.txt, model_log.csv, gzserver.log)"
