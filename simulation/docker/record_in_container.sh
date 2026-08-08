#!/usr/bin/env bash
# Navitas — Konteyner İÇİNDE çalışan kayıt orkestrasyonu (SIRALI seviyeler)
#
# Akış: Xvfb+openbox → her seviye için (dünya üret → gazebo → ffmpeg klip → hakem log)
#        → klipleri tek videoya birleştir.
#
# Kullanım (record.sh çağırır):
#   bash record_in_container.sh <seed> <çıktı.mp4> "<seviyeler>"
#     seviyeler: "kolay orta zor" (varsayılan) veya tek "orta"
set -u

SEED="${1:-42}"
OUT="${2:-/sim/recordings/navitas.mp4}"
LEVELS="${3:-kolay orta zor}"
RT="${4:-0}"                   # süre modu: 1=gerçekçi+limit, 0=süresiz
LAYOUT="${5:-field}"          # arena: field=gerçekçi saha (vars.), clean=seyrek
CLIP_LIMIT="${6:-1500}"        # klip başına güvenlik üst sınırı (sn) — şartname: İHA 15dk + İKA 10dk
MAP="${NAVITAS_MAP:-}"         # yalnız açık --map override verilirse dolu
PROFILE="${NAVITAS_PROFILE:-baseline}"

W=1280; H=720; FPS=30
SIMDIR=/sim
OUTDIR="$(dirname "$OUT")"
LOG="$OUTDIR/hakem_log.txt"

export DISPLAY=:99
export GAZEBO_MODEL_PATH="$SIMDIR/models:${GAZEBO_MODEL_PATH:-}"
export QT_X11_NO_MITSHM=1
ulimit -c 0   # gz CLI ara sıra SIGABRT verir (zararsız) — host abrt bildirimini sustur

XVFB_PID=""
cleanup() {
    echo "[rec] temizlik..."
    pkill -f ffmpeg 2>/dev/null
    pkill -f gzclient 2>/dev/null; pkill -f gzserver 2>/dev/null; pkill -f gazebo 2>/dev/null
    [ -n "$XVFB_PID" ] && kill "$XVFB_PID" 2>/dev/null
}
trap cleanup EXIT

echo "════════════════════════════════════════════"
echo "  Navitas SIRALI kayıt — profil=$PROFILE | seviyeler: $LEVELS | seed=$SEED | layout=${LAYOUT:-profil}"
echo "  ${W}x${H}@${FPS}  →  $OUT"
echo "════════════════════════════════════════════"

# Sanal ekran — SADECE kamera sensörünün GL context'i için (gzclient YOK)
echo "[rec] Xvfb :99 (kamera sensörü GL context)..."
Xvfb :99 -screen 0 ${W}x${H}x24 -nolisten tcp &
XVFB_PID=$!
sleep 2

cd "$SIMDIR"
mkdir -p /tmp/clips

# ── Tek seviyeyi kaydet ───────────────────────────────────────────────────────
record_one() {
    local level="$1" clip="$2"
    local world="worlds/rec_${level}.world"
    echo ""
    echo "──────── SEVİYE: $level ────────"
    # DÜRÜST ZİNCİR: dünya SADECE ground-truth ile kurulur (model tespiti dünyaya
    # GERİ BESLENMEZ — eski --road akışı tersine nedensellikti ve kaldırıldı).
    # Modelin kararı KAYIT SIRASINDA, İHA'nın kendi tarama karelerinden verilir
    # (host: iha_haritala.py) ve İKA'ya /tmp/navitas_route ile ulaşır.
    local gen
    local layout_args=()
    local map_args=()
    [ -n "$LAYOUT" ] && layout_args=(--layout "$LAYOUT")
    [ -n "$MAP" ] && map_args=(--map "$MAP")
    gen=$(python3 scripts/world_generator.py --focus "$level" --seed "$SEED" --record \
          --profile "$PROFILE" "${layout_args[@]}" "${map_args[@]}" --output "$world")
    echo "$gen"
    local secs open actual_map actual_seed scan_altitude scan_end land_t route_delay packet_loss htab kbxy hbxy
    secs=$(echo "$gen" | sed -n 's/.*RECORD_SECONDS=\([0-9]*\).*/\1/p'); [ -z "$secs" ] && secs=30
    [ "$secs" -gt "$CLIP_LIMIT" ] && secs="$CLIP_LIMIT"
    open=$(echo "$gen" | sed -n 's/.*OPEN_ROAD=\([a-z]*\).*/\1/p'); [ -z "$open" ] && open="?"
    actual_map=$(echo "$gen" | sed -n 's/.*MAP=\([0-9]*\).*/\1/p'); [ -z "$actual_map" ] && { echo "MAP metadata yok"; return 1; }
    actual_seed=$(echo "$gen" | sed -n 's/.*SEED=\([0-9-]*\).*/\1/p'); [ -z "$actual_seed" ] && { echo "SEED metadata yok"; return 1; }
    scan_altitude=$(echo "$gen" | sed -n 's/.*SCAN_ALTITUDE_M=\([0-9.]*\).*/\1/p'); [ -z "$scan_altitude" ] && { echo "SCAN_ALTITUDE_M metadata yok"; return 1; }
    scan_end=$(echo "$gen" | sed -n 's/.*SCAN_END_T=\([0-9]*\).*/\1/p'); [ -z "$scan_end" ] && scan_end=9999
    land_t=$(echo "$gen" | sed -n 's/.*LAND_T=\([0-9]*\).*/\1/p'); [ -z "$land_t" ] && land_t=9999
    route_delay=$(echo "$gen" | sed -n 's/.*ROUTE_DELAY_S=\([0-9.]*\).*/\1/p'); [ -z "$route_delay" ] && route_delay=0
    packet_loss=$(echo "$gen" | sed -n 's/.*PACKET_LOSS_PERCENT=\([0-9]*\).*/\1/p'); [ -z "$packet_loss" ] && packet_loss=0
    htab=$(echo "$gen" | sed -n 's/.*HTAB_CENTER=\([0-9.,-]*\).*/\1/p')
    kbxy=$(echo "$gen" | sed -n 's/.*KB_XY=\([0-9.,-]*\).*/\1/p')
    hbxy=$(echo "$gen" | sed -n 's/.*HB_XY=\([0-9.,-]*\).*/\1/p')
    echo "[rec] $level: harita=$actual_map seed=$actual_seed ground-truth açık yol=${open} (GİZLİ), tarama bitişi ~${scan_end}s"

    # İHA-haritalama köprü dizini (host'taki iha_haritala.py buradan okur/buraya yazar)
    local L="$OUTDIR/iha_scan_${level}"
    rm -rf "$L"; mkdir -p "$L/kareler"
    { echo "LEVEL=$level"; echo "HTAB_CENTER=$htab"; echo "SCAN_END_T=$scan_end"
      echo "SEED=$actual_seed"; echo "LAYOUT=${LAYOUT:-profil}"; echo "MAP=$actual_map"; echo "PROFILE=$PROFILE"
      echo "SCAN_ALTITUDE_M=$scan_altitude"
      echo "LAND_T=$land_t"; echo "ROUTE_DELAY_S=$route_delay"; echo "PACKET_LOSS_PERCENT=$packet_loss"
      echo "KB_XY=$kbxy"; echo "HB_XY=$hbxy"; } > "$L/meta.txt"

    # gzserver SADECE (gzclient YOK) — dünyadaki top-down kamera SENSÖRÜ kareleri
    # /tmp/frames'e kaydeder. Sensör pozu SDF'de sabit → DETERMİNİSTİK 90° dik.
    # İHA tarama kamerası navitas_scan_cam plugin'iyle kare+pozu SENKRON yazar:
    # /tmp/iha_scan/scan_N.jpg + /tmp/iha_scan/poses.csv (n,t,x,y,z,yaw — birebir).
    # İKA rotası /tmp/navitas_route'tan okunur.
    rm -rf /tmp/frames /tmp/iha_scan /tmp/navitas_simtime /tmp/navitas_route /tmp/navitas_ika_trigger
    mkdir -p /tmp/frames /tmp/iha_scan
    gzserver --pause "$world" >/dev/null 2>&1 &
    # NOT: gz stats DURAKLATILMIŞ dünyada çıktı vermez — hazır olmayı topic listesiyle anla
    for i in $(seq 1 30); do
        timeout 5 gz topic -l 2>/dev/null | grep -q world_stats && break
        sleep 1
    done
    sleep 3
    echo "[rec] $level görevi oynatılıyor (${secs} SİM saniyesi)..."
    gz world -p 0 2>/dev/null || true
    # SİM zamanını bekle (duvar saati DEĞİL): render yavaşsa (RTF<1) görev yarım
    # kalmasın. Üst sınır: 5× duvar süresi.
    # SİM saatini plugin'in yazdığı /tmp/navitas_simtime'dan izle (gz stats yük
    # altında sessiz kalıyor / SIGABRT veriyordu — dosya güvenilir).
    local wall_max=$(( secs * 6 + 90 )) waited=0 simt=0 bitti_pad=0 route_attempt=0
    local route_ready_at route_drop_n
    route_ready_at=$(python3 -c "print(int(float('$scan_end') + float('$route_delay')))" 2>/dev/null); route_ready_at=${route_ready_at:-$scan_end}
    route_drop_n=$(( (packet_loss + 19) / 20 ))
    while [ "$waited" -lt "$wall_max" ]; do
        pgrep gzserver >/dev/null || break
        simt=$(cat /tmp/navitas_simtime 2>/dev/null | head -1); simt=${simt:-0}
        # İKA son waypoint'e ulaştıysa (plugin 'durum=BITTI') birkaç sn pay bırakıp kes
        if grep -q "durum=BITTI" /tmp/navitas_simtime 2>/dev/null; then
            bitti_pad=$(( bitti_pad + 2 ))
            if [ "$bitti_pad" -ge 6 ]; then
                echo "[rec] görev tamamlandı (sim ${simt}s) — klip erken kesiliyor"
                break
            fi
        fi
        if grep -q "durum=TIKANDI" /tmp/navitas_simtime 2>/dev/null; then
            touch "$L/TIKANDI"
            echo "[rec] görev başarısız: İKA 15 sim-saniye ilerleme göstermedi (TIKANDI)"
            break
        fi
        if grep -q "durum=ROTA_YOK" /tmp/navitas_simtime 2>/dev/null; then
            touch "$L/ROTA_YOK"
            echo "[rec] görev başarısız: güvenilir model rotası alınamadı, İKA güvenli duruşta (ROTA_YOK)"
            break
        fi
        # ── İHA-HARİTALAMA KÖPRÜSÜ (canlı): kareler+pozlar DIŞARI, model rotası İÇERİ ──
        cp -u /tmp/iha_scan/scan_*.jpg "$L/kareler/" 2>/dev/null
        cp -f /tmp/iha_scan/poses.csv "$L/poses.csv" 2>/dev/null
        if [ "$simt" -ge "$scan_end" ] 2>/dev/null && [ ! -f "$L/SCAN_DONE" ]; then
            touch "$L/SCAN_DONE"
            echo "[rec] tarama bitti (sim ${simt}s) → host İHA-haritalama tetiklendi"
        fi
        if [ -f "$L/route.txt" ] && [ ! -f /tmp/navitas_route ] && [ "$simt" -ge "$route_ready_at" ] 2>/dev/null; then
            route_attempt=$(( route_attempt + 1 ))
            if [ "$packet_loss" -ge 100 ]; then
                touch "$L/COMMS_TOTAL_LOSS"
                echo "[rec] haberleşme stresi: %100 kayıp, rota paketi #$route_attempt teslim edilmedi"
            elif [ "$route_attempt" -le "$route_drop_n" ]; then
                echo "[rec] haberleşme stresi: rota paketi #$route_attempt deterministik düşürüldü"
            else
                # Host rota dosyasini atomik yayinlar; plugin yarim dosya okumaya baslamasin.
                route_tmp="/tmp/navitas_route.$$"
                if cp -f "$L/route.txt" "$route_tmp" && mv -f "$route_tmp" /tmp/navitas_route; then
                    echo "[rec] MODEL rotası deneme #$route_attempt ile teslim edildi → İKA model haritasını sürecek"
                    if [ "$simt" -ge "$land_t" ] 2>/dev/null; then
                        touch "$L/COMMS_LATE"
                        echo "[rec] GÖREV İHLALİ: rota İHA inişinden sonra teslim edildi (sim=${simt}, iniş=${land_t})"
                    else
                        touch "$L/COMMS_BEFORE_LANDING"
                        echo "[rec] haberleşme sırası uygun: rota İHA havadayken teslim edildi"
                    fi
                else
                    rm -f "$route_tmp"
                fi
            fi
        fi
        if [ "$simt" -ge $(( land_t + 2 )) ] 2>/dev/null && [ ! -f /tmp/navitas_ika_trigger ]; then
            touch /tmp/navitas_ika_trigger
            echo "[rec] YKS operatörü manuel İKA görev tetikleme olayı verdi (sim ${simt}s)"
        fi
        [ "$simt" -ge "$secs" ] 2>/dev/null && break
        sleep 2; waited=$(( waited + 2 ))
    done
    pkill -f gzserver 2>/dev/null; sleep 2
    simt=$(cat /tmp/navitas_simtime 2>/dev/null | head -1); simt=${simt:-0}
    echo "[rec] sim ${simt}s'e ulaşıldı (duvar ~${waited}s)"
    # son senkron + emniyet işareti (tarama bitmeden kayıt kapandıysa da host işlesin)
    cp -u /tmp/iha_scan/scan_*.jpg "$L/kareler/" 2>/dev/null
    cp -f /tmp/iha_scan/poses.csv "$L/poses.csv" 2>/dev/null
    [ -f "$L/SCAN_DONE" ] || touch "$L/SCAN_DONE"

    local nf; nf=$(ls /tmp/frames/*.jpg 2>/dev/null | wc -l)
    local ns; ns=$(ls /tmp/iha_scan/*.jpg 2>/dev/null | wc -l)
    # GERÇEK-ZAMAN kodlama: kamera 30fps'e yetişemeyip kare düşürürse videoyu
    # 30fps saymak HIZLANDIRIR (İHA ışınlanmış görünür). Efektif fps = kare/simsn.
    [ "$simt" -lt 5 ] 2>/dev/null && simt="$secs"   # stats okunamadıysa: görev süresi varsay
    local fps_eff
    fps_eff=$(python3 -c "print(max(1,round($nf/max($simt,1))))" 2>/dev/null); fps_eff=${fps_eff:-$FPS}
    echo "[rec] $nf kare / ${simt}s sim → ${fps_eff}fps gerçek-zaman (İHA tarama: $ns kare/1Hz)"

    # İHA GÖZÜ videosu — nadir tarama kamerasının gördüğü (1 Hz kare, gerçek süre hızında)
    if [ "$ns" -gt 3 ]; then
        ffmpeg -y -loglevel warning -framerate 1 -pattern_type glob -i "$L/kareler/*.jpg" \
            -r "$FPS" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p \
            "$OUTDIR/iha_gozu_${level}.mp4" \
            && echo "[rec] ✓ İHA gözü: iha_gozu_${level}.mp4 ($ns kare)"
    fi

    # MODEL kararı (host iha_haritala.py'nin SİM TARAMASINDAN verdiği gerçek karar)
    local mlabel="YOK" mconf="?" mroad=0 m_ika="IKA GUVENLI DURMA (dinamik model rotasi yok)"
    if [ -f "$L/detection.json" ]; then
        mlabel=$(python3 -c "import json;print((json.load(open('$L/detection.json')).get('label') or 'yok').upper())" 2>/dev/null); mlabel=${mlabel:-YOK}
        mconf=$(python3 -c "import json;c=json.load(open('$L/detection.json')).get('conf');print(c if c is not None else '?')" 2>/dev/null); mconf=${mconf:-?}
        mroad=$(python3 -c "import json;print(json.load(open('$L/detection.json')).get('road') or 0)" 2>/dev/null); mroad=${mroad:-0}
    fi
    [ -f "$L/route.txt" ] && m_ika="IKA MODELIN haritasini suruyor"

    # Gerçekçi görev süreleri (mission_time — şartname limitleri içinde)
    local IHAT IKAT
    read -r IHAT IKAT <<EOF2
$(python3 -c "import sys;sys.path.insert(0,'scripts');import mission_time as mt
r=${mroad:-0}
T=mt.realistic('$level', r if r in (1,2,3) else None, harita_id=$actual_map)
print(mt.fmt(T['iha']), mt.fmt(T['ika']))" 2>/dev/null)
EOF2
    [ -z "$IHAT" ] && IHAT="--.--"; [ -z "$IKAT" ] && IKAT="--.--"
    # drawtext metninde ':' opsiyon ayıracı sayıldığından gösterimi '.' yap
    IHAT=${IHAT//:/.}; IKAT=${IKAT//:/.}
    local STARTT; STARTT=$(date +%H.%M.%S)

    # ── HUD (hakem/YKS ekranı) ──
    local FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf
    local LVU OPU
    LVU=$(echo "$level" | tr 'a-z' 'A-Z'); OPU=$(echo "$open" | tr 'a-z' 'A-Z')
    local VF="drawtext=fontfile=${FONT}:text='NAVITAS HTAB   SEVIYE ${LVU}':x=24:y=20:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=9"
    VF="${VF},drawtext=fontfile=${FONT}:text='MODEL TESPIT (sim taramadan)  ACIK YOL ${mlabel}  guven ${mconf}   |   GERCEK ${OPU}   |   comms OK':x=24:y=60:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=7:enable='gte(t,6)'"
    VF="${VF},drawtext=fontfile=${FONT}:text='${m_ika}  ->  HB':x=24:y=96:fontsize=22:fontcolor=cyan:box=1:boxcolor=black@0.6:boxborderw=7:enable='gte(t,16)'"
    VF="${VF},drawtext=fontfile=${FONT}:text='SAAT ${STARTT}   VIDEO %{pts\\:hms}':x=w-tw-24:y=20:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=7"
    if [ "$RT" = "1" ]; then
        VF="${VF},drawtext=fontfile=${FONT}:text='GOREV SURELERI (gercekci)    IHA ${IHAT} / 15.00  GECERLI       IKA ${IKAT} / 10.00  GECERLI':x=24:y=h-46:fontsize=22:fontcolor=0x9CFF9C:box=1:boxcolor=black@0.6:boxborderw=7:enable='gte(t,16)'"
    else
        VF="${VF},drawtext=fontfile=${FONT}:text='SURE MODU: KAPALI (suresiz)':x=24:y=h-44:fontsize=20:fontcolor=0xCCCCCC:box=1:boxcolor=black@0.55:boxborderw=6"
    fi

    ffmpeg -y -loglevel warning -framerate "$fps_eff" -pattern_type glob -i '/tmp/frames/*.jpg' \
        -vf "$VF" -r "$FPS" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$clip"
    [ -f "$clip" ] && echo "[rec] ✓ klip: $clip ($(du -h "$clip" | cut -f1))" || echo "[rec] ✗ klip yok: $level"
}

: > "$LOG"

CLIPS=()
for lv in $LEVELS; do
    clip="/tmp/clips/${lv}.mp4"
    record_one "$lv" "$clip"
    [ -f "$clip" ] && CLIPS+=("$clip")
done

# Hakem/model logu (tek oturum — profil zon-map kimliklerini kendi çözer)
echo "[rec] hakem/model logu üretiliyor → $LOG"
DET="$OUTDIR/detections.json"
LOG_MAP_ARGS=()
[ -n "$MAP" ] && LOG_MAP_ARGS=(--map "$MAP")
if [ "$(echo $LEVELS | wc -w)" -eq 1 ]; then
    python3 scripts/hakem_log.py --level "$LEVELS" --profile "$PROFILE" "${LOG_MAP_ARGS[@]}" --detections "$DET" --realtime "$RT" --out "$LOG" >/dev/null 2>&1 || echo "[rec] (log üretilemedi)"
else
    python3 scripts/hakem_log.py --all --profile "$PROFILE" "${LOG_MAP_ARGS[@]}" --detections "$DET" --realtime "$RT" --out "$LOG" >/dev/null 2>&1 || echo "[rec] (log üretilemedi)"
fi

# ── Birleştir ─────────────────────────────────────────────────────────────────
if [ "${#CLIPS[@]}" -eq 0 ]; then
    echo "[rec] ✗ hiç klip üretilmedi!"; exit 1
elif [ "${#CLIPS[@]}" -eq 1 ]; then
    cp "${CLIPS[0]}" "$OUT"
else
    list=/tmp/clips/list.txt; : > "$list"
    for c in "${CLIPS[@]}"; do echo "file '$c'" >> "$list"; done
    echo "[rec] klipler birleştiriliyor → $OUT"
    ffmpeg -y -loglevel warning -f concat -safe 0 -i "$list" -c copy "$OUT"
fi

if [ -f "$OUT" ]; then
    echo "[rec] ✓ VİDEO: $OUT ($(du -h "$OUT" | cut -f1))"
    echo "[rec] ✓ LOG  : $LOG"
else
    echo "[rec] ✗ Video oluşmadı!"; exit 1
fi
