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
OUT="${2:-/sim/recordings/navitas_tum_seviyeler.mp4}"
LEVELS="${3:-kolay orta zor}"
RT="${4:-0}"                   # süre modu: 1=gerçekçi+limit, 0=süresiz
LAYOUT="${5:-field}"          # arena: field=gerçekçi saha (vars.), clean=seyrek
CLIP_LIMIT="${6:-1500}"        # klip başına güvenlik üst sınırı (sn) — şartname: İHA 15dk + İKA 10dk
MAP="${NAVITAS_MAP:-1}"        # gerçekçi harita no (record.sh --map ile gelir)
MAP_SET="${NAVITAS_MAP_SET:-0}"
PROFILE="${NAVITAS_PROFILE:-}" # scenario profile id (boşsa legacy focus/map akışı)
TERRAIN="${NAVITAS_TERRAIN:-plain}"  # zemin/arazi modu: plain|textured|relief
LAST_ACTUAL_MAP="$MAP"
FAST_RECORD="${NAVITAS_FAST_RECORD:-1}" # 1=6 sunum kamerasi dusuk render yuku; kamera sayisi degismez
RECORDING_INCOMPLETE=0

W=1280; H=720; FPS=30
SIMDIR=/sim
GAZEBO_RESOURCE_ROOT="${NAVITAS_GAZEBO_RESOURCE_ROOT:?record.sh kaynak kökünü aktarmalı}"
OUTDIR="$(dirname "$OUT")"
LOG="$OUTDIR/hakem_log.txt"
EXTRA_CAM_DIRS="overview side_north side_south side_east side_west"

export DISPLAY=:99
export GAZEBO_MODEL_PATH="$SIMDIR/models:${GAZEBO_MODEL_PATH:-}"
export GAZEBO_RESOURCE_PATH="$GAZEBO_RESOURCE_ROOT${GAZEBO_RESOURCE_PATH:+:$GAZEBO_RESOURCE_PATH}"
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
echo "  Navitas SIRALI kayıt — seviyeler: $LEVELS | seed=$SEED | layout=$LAYOUT | profile=${PROFILE:-baseline}"
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
    local gen map_label
    map_label="$MAP"
    local gen_args=(python3 scripts/world_generator.py --focus "$level" --seed "$SEED" --record
                    --layout "$LAYOUT" --terrain "$TERRAIN" --output "$world")
    if [ -z "$PROFILE" ] || [ "$MAP_SET" = "1" ]; then
        gen_args+=(--map "$MAP")
    elif [ -n "$PROFILE" ]; then
        map_label="profile"
    fi
    if [ -n "$PROFILE" ]; then
        gen_args+=(--profile "$PROFILE")
    fi
    gen=$("${gen_args[@]}")
    echo "$gen"
    # Yedi kayıt kamerasının SAYISI korunur: ana + tüm saha + 4 kenar + İHA gözü.
    # Yalnız altı sunum kamerasının render yükü düşürülür; İHA'nın 640x640 algı
    # kamerası ve 10 Hz örneklemesi değişmez. Son MP4'ler aşağıda 1280x720'ye
    # ölçeklenir. Piksel/s yükü yaklaşık 36,9 -> 4,8 MP/s (sunum kameraları),
    # yedi kameranın toplamında 41,0 -> 8,9 MP/s olur (yaklaşık %78 azalma).
    if [ "$FAST_RECORD" = "1" ]; then
        sed -i \
            -e 's#<image><width>1280</width><height>720</height><format>R8G8B8</format></image>#<image><width>640</width><height>360</height><format>R8G8B8</format></image>#g' \
            -e 's#<update_rate>6</update_rate>#<update_rate>3</update_rate>#g' \
            -e 's#<update_rate>4</update_rate>#<update_rate>3</update_rate>#g' \
            -e 's#<update_rate>12</update_rate>#<update_rate>6</update_rate>#g' \
            "$world"
        local tuned_cams
        tuned_cams=$(grep -c '<image><width>640</width><height>360</height><format>R8G8B8</format></image>' "$world")
        if [ "$tuned_cams" -eq 6 ]; then
            echo "[rec] hizli kamera kipi: 6/6 sunum kamerasi 640x360 (ana 6fps, tum saha+4 kenar 3fps); IHA gozu 640x640@10Hz korundu"
        else
            echo "[rec] UYARI: hizli kamera ayari 6 yerine ${tuned_cams} kameraya uygulandi; kamera sayisi/RTF mimar tarafindan dogrulanmali" >&2
        fi
    fi
    local secs open scan_end htab kbxy hbxy actual_map iha_path_m ika_path_m ika_drive_t route_road route_xy
    secs=$(echo "$gen" | sed -n 's/.*RECORD_SECONDS=\([0-9]*\).*/\1/p'); [ -z "$secs" ] && secs=30
    [ "$secs" -gt "$CLIP_LIMIT" ] && secs="$CLIP_LIMIT"
    open=$(echo "$gen" | sed -n 's/.*OPEN_ROAD=\([a-z]*\).*/\1/p'); [ -z "$open" ] && open="?"
    scan_end=$(echo "$gen" | sed -n 's/.*SCAN_END_T=\([0-9]*\).*/\1/p'); [ -z "$scan_end" ] && scan_end=9999
    htab=$(echo "$gen" | sed -n 's/.*HTAB_CENTER=\([0-9.,-]*\).*/\1/p')
    actual_map=$(echo "$gen" | sed -n 's/.*MAP=\([0-9]*\).*/\1/p'); [ -z "$actual_map" ] && actual_map="$MAP"
    LAST_ACTUAL_MAP="$actual_map"
    kbxy=$(echo "$gen" | sed -n 's/.*KB_XY=\([0-9.,-]*\).*/\1/p')
    hbxy=$(echo "$gen" | sed -n 's/.*HB_XY=\([0-9.,-]*\).*/\1/p')
    iha_path_m=$(echo "$gen" | sed -n 's/.*IHA_PATH_M=\([0-9.]*\).*/\1/p')
    ika_path_m=$(echo "$gen" | sed -n 's/.*IKA_PATH_M=\([0-9.]*\).*/\1/p')
    ika_drive_t=$(echo "$gen" | sed -n 's/.*IKA_DRIVE_T=\([0-9.]*\).*/\1/p')
    route_road=$(echo "$gen" | sed -n 's/.*ROUTE_ROAD=\([0-9]*\).*/\1/p')
    route_xy=$(echo "$gen" | sed -n 's/.*ROUTE_XY=\(.*\)$/\1/p')
    echo "[rec] $level: harita=${actual_map} ground-truth açık yol=${open} (GİZLİ — model kendisi bulacak), tarama bitişi ~${scan_end}s"

    # İHA-haritalama köprü dizini (host'taki iha_haritala.py buradan okur/buraya yazar)
    local L="$OUTDIR/iha_scan_${level}"
    rm -rf "$L"; mkdir -p "$L/kareler"
    { echo "LEVEL=$level"; echo "HTAB_CENTER=$htab"; echo "SCAN_END_T=$scan_end"
      echo "SEED=$SEED"; echo "LAYOUT=$LAYOUT"; echo "MAP=$actual_map"; echo "PROFILE=${PROFILE:-baseline}"
      echo "KB_XY=$kbxy"; echo "HB_XY=$hbxy"; echo "IHA_PATH_M=$iha_path_m"
      echo "IKA_PATH_M=$ika_path_m"; echo "IKA_DRIVE_T=$ika_drive_t"
      echo "ROUTE_ROAD=$route_road"; echo "ROUTE_XY=$route_xy"; } > "$L/meta.txt"

    # gzserver SADECE (gzclient YOK) — dünyadaki top-down kamera SENSÖRÜ kareleri
    # /tmp/frames'e kaydeder. Sensör pozu SDF'de sabit → DETERMİNİSTİK 90° dik.
    # İHA tarama kamerası navitas_scan_cam plugin'iyle kare+pozu SENKRON yazar:
    # /tmp/iha_scan/scan_N.jpg + /tmp/iha_scan/poses.csv (n,t,x,y,z,yaw — birebir).
    # İKA rotası /tmp/navitas_route'tan okunur.
    rm -rf /tmp/frames /tmp/frames_overview /tmp/frames_side_north /tmp/frames_side_south \
        /tmp/frames_side_east /tmp/frames_side_west /tmp/iha_scan /tmp/navitas_simtime /tmp/navitas_route
    mkdir -p /tmp/frames /tmp/frames_overview /tmp/frames_side_north /tmp/frames_side_south \
        /tmp/frames_side_east /tmp/frames_side_west /tmp/iha_scan
    gzserver --pause "$world" >/dev/null 2>&1 &
    # NOT: gz stats DURAKLATILMIŞ dünyada çıktı vermez — hazır olmayı topic listesiyle anla
    for i in $(seq 1 30); do
        timeout 5 gz topic -l 2>/dev/null | grep -q world_stats && break
        sleep 1
    done
    sleep 3
    echo "[rec] $level görevi oynatılıyor (${secs} SİM saniyesi)..."
    # UNPAUSE GÜVENİLİRLİK DÜZELTMESİ (14 Eylül, D-485): tek seferlik "gz world -p 0"
    # bazen dünyayı gerçekten duraklatılmamış hale getirmiyordu (fizik hiç ilerlemiyor,
    # /tmp/navitas_simtime hiç yazılmıyor, kareler hiç üretilmiyor — rv40'ta 30+ dk
    # boşa gitti). Artık /tmp/navitas_simtime dosyası belirene kadar (fizik gerçekten
    # adım attığının kanıtı) unpause komutu tekrar tekrar denenir.
    rm -f /tmp/navitas_simtime
    unpause_ok=0
    for i in $(seq 1 15); do
        gz world -p 0 2>/dev/null || true
        sleep 2
        if [ -s /tmp/navitas_simtime ]; then unpause_ok=1; break; fi
    done
    if [ "$unpause_ok" = "0" ]; then
        echo "[rec] UYARI: $level için unpause 30s içinde doğrulanamadı (navitas_simtime hâlâ boş) — devam ediliyor, aşağıdaki asıl döngü de simt=0 görürse zamanla dolabilir"
    fi
    # SİM zamanını bekle (duvar saati DEĞİL): render yavaşsa (RTF<1) görev yarım
    # kalmasın. Ölçülen yaklaşık 0,07 RTF için 144 sim s ≈ 2150 duvar s;
    # 20x+120 bütçe 3000 s verir. Bu da dolarsa sessiz başarı YASAKTIR.
    # SİM saatini plugin'in yazdığı /tmp/navitas_simtime'dan izle (gz stats yük
    # altında sessiz kalıyor / SIGABRT veriyordu — dosya güvenilir).
    local wall_max=$(( secs * 20 + 120 )) waited=0 simt=0
    local cut_reason="" terminal="" terminal_line="" terminal_simt=""
    while [ "$waited" -lt "$wall_max" ]; do
        if ! pgrep gzserver >/dev/null; then
            cut_reason="GZSERVER_DURDU"
            break
        fi
        simt=$(cat /tmp/navitas_simtime 2>/dev/null | head -1); simt=${simt:-0}
        terminal_line=$(grep '^ika_' /tmp/navitas_simtime 2>/dev/null | tail -n1 || true)
        terminal=""
        case "$terminal_line" in
            *durum=ROTA_YOK*) terminal="ROTA_YOK" ;;
            *durum=TIKANDI*) terminal="TIKANDI" ;;
            *durum=BITTI*) terminal="BITTI" ;;
        esac
        # İKA'nın gerçek terminal sonucu görüldüyse 5 SİM saniyesi pay bırakıp kes.
        # Duvar saniyesi kullanmak 0,07 RTF'de videoya yalnız ~0,4 sn ekliyordu.
        if [ -n "$terminal" ]; then
            [ -z "$terminal_simt" ] && terminal_simt="$simt"
            if [ "$simt" -ge $(( terminal_simt + 5 )) ] 2>/dev/null; then
                cut_reason="GOREV_TAMAMLANDI"
                echo "[rec] görev sonucu görüldü: ${terminal} (sim ${terminal_simt}s) — 5 sim sn pay sonrası klip kesiliyor (sim ${simt}s)"
                break
            fi
        else
            terminal_simt=""
        fi
        # ── İHA-HARİTALAMA KÖPRÜSÜ (canlı): kareler+pozlar DIŞARI, model rotası İÇERİ ──
        cp -u /tmp/iha_scan/scan_*.jpg "$L/kareler/" 2>/dev/null
        cp -f /tmp/iha_scan/poses.csv "$L/poses.csv" 2>/dev/null
        if [ "$simt" -ge "$scan_end" ] 2>/dev/null && [ ! -f "$L/SCAN_DONE" ]; then
            touch "$L/SCAN_DONE"
            echo "[rec] tarama bitti (sim ${simt}s) → host İHA-haritalama tetiklendi"
        fi
        if [ -f "$L/route.txt" ] && [ ! -f /tmp/navitas_route ]; then
            # Host rota dosyasini atomik yayinlar; yine de konteyner tarafinda
            # ara hedefe kopyalayip tek hamlede yayinla ki plugin yarim dosya
            # okumaya baslamasin.
            route_tmp="/tmp/navitas_route.$$"
            if cp -f "$L/route.txt" "$route_tmp" && mv -f "$route_tmp" /tmp/navitas_route; then
                echo "[rec] İHA rota dosyası alındı → İKA koordinat waypoint'lerini sürecek"
            else
                rm -f "$route_tmp"
            fi
        fi
        # Kayıt hedefi görev terminalinden önce dolarsa bunu da başarı sayma.
        if [ -z "$terminal" ] && [ "$simt" -ge "$secs" ] 2>/dev/null; then
            cut_reason="SIM_SINIRI"
            break
        fi
        sleep 2; waited=$(( waited + 2 ))
    done
    if [ -z "$cut_reason" ]; then
        cut_reason="DUVAR_SINIRI"
    fi
    pkill -f gzserver 2>/dev/null; sleep 2
    simt=$(cat /tmp/navitas_simtime 2>/dev/null | head -1); simt=${simt:-0}
    terminal_line=$(grep '^ika_' /tmp/navitas_simtime 2>/dev/null | tail -n1 || true)
    if [ -z "$terminal" ]; then
        case "$terminal_line" in
            *durum=ROTA_YOK*) terminal="ROTA_YOK" ;;
            *durum=TIKANDI*) terminal="TIKANDI" ;;
            *durum=BITTI*) terminal="BITTI" ;;
            *) terminal="YOK" ;;
        esac
    fi
    echo "[rec] sim ${simt}s'e ulaşıldı (duvar ~${waited}s)"
    {
        echo "SEBEP=$cut_reason"
        echo "SON_DURUM=$terminal"
        echo "SIM_T=$simt"
        echo "RECORD_SECONDS=$secs"
        echo "WALL_SECONDS=$waited"
        echo "WALL_LIMIT=$wall_max"
    } >> "$L/meta.txt"
    if [ "$cut_reason" = "DUVAR_SINIRI" ]; then
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
        echo "[rec] HATA: DUVAR SINIRI DOLDU — KAYIT YARIDA KESILDI (sim ${simt}s / hedef ${secs}s, duvar ${waited}/${wall_max}s)" >&2
        echo "[rec] HATA: hakem logu bu kosumu BASARILI saymayacak" >&2
        echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" >&2
        RECORDING_INCOMPLETE=1
    elif [ "$cut_reason" != "GOREV_TAMAMLANDI" ]; then
        echo "[rec] HATA: kayıt görev sonucu görülmeden bitti — SEBEP=${cut_reason} (sim ${simt}s / hedef ${secs}s)" >&2
        RECORDING_INCOMPLETE=1
    fi
    # son senkron + emniyet işareti (tarama bitmeden kayıt kapandıysa da host işlesin)
    cp -u /tmp/iha_scan/scan_*.jpg "$L/kareler/" 2>/dev/null
    cp -f /tmp/iha_scan/poses.csv "$L/poses.csv" 2>/dev/null
    [ -f "$L/SCAN_DONE" ] || touch "$L/SCAN_DONE"

    local nf; nf=$(ls /tmp/frames/*.jpg 2>/dev/null | wc -l)
    local ns; ns=$(ls /tmp/iha_scan/*.jpg 2>/dev/null | wc -l)
    # GERÇEK-ZAMAN kodlama: kamera 30fps'e yetişemeyip kare düşürürse videoyu
    # 30fps saymak HIZLANDIRIR (İHA ışınlanmış görünür). Efektif fps = kare/simsn.
    local fps_eff fps_simt="$simt"
    # Yalnız video zaman tabanı için sıfıra bölmeyi önle; canlı SIM_T meta verisini
    # hedef süreyle ezip tamamlanmış gibi gösterme.
    [ "$fps_simt" -lt 1 ] 2>/dev/null && fps_simt=1
    fps_eff=$(python3 -c "print(max(1,round($nf/max($fps_simt,1))))" 2>/dev/null); fps_eff=${fps_eff:-$FPS}
    echo "[rec] $nf kare / ${simt}s sim → ${fps_eff}fps gerçek-zaman (İHA tarama: $ns kare)"

    # İHA GÖZÜ videosu — tarama kamerasının gördüğü kareler, gerçek sim süre hızında.
    if [ "$ns" -gt 3 ]; then
        local scan_fps_eff
        scan_fps_eff=$(python3 -c "print(max(1,round($ns/max($fps_simt,1))))" 2>/dev/null); scan_fps_eff=${scan_fps_eff:-10}
        ffmpeg -y -loglevel warning -framerate "$scan_fps_eff" -pattern_type glob -i "$L/kareler/*.jpg" \
            -r "$FPS" -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p \
            "$OUTDIR/iha_gozu_${level}.mp4" \
            && echo "[rec] ✓ İHA gözü: iha_gozu_${level}.mp4 ($ns kare, ${scan_fps_eff}fps kaynak)"
    fi

    # MODEL kararı (host iha_haritala.py'nin SİM TARAMASINDAN verdiği gerçek karar)
    local mlabel="YOK" mconf="?" mroad=0 m_ika="IKA GUVENLI DURMA (dinamik model rotasi yok)"
    if [ -f "$L/detection.json" ]; then
        mlabel=$(python3 -c "import json;print((json.load(open('$L/detection.json')).get('label') or 'yok').upper())" 2>/dev/null); mlabel=${mlabel:-YOK}
        mconf=$(python3 -c "import json;c=json.load(open('$L/detection.json')).get('conf');print(c if c is not None else '?')" 2>/dev/null); mconf=${mconf:-?}
        mroad=$(python3 -c "import json;print(json.load(open('$L/detection.json')).get('road') or 0)" 2>/dev/null); mroad=${mroad:-0}
    fi
    if [ -f "$L/route.txt" ]; then
        if grep -q '"rota_kaynak": "iha_koordinat_yedegi"' "$L/detection.json" 2>/dev/null; then
            m_ika="IKA IHA KOORDINAT ROTASINI suruyor"
        else
            m_ika="IKA MODELIN haritasini suruyor"
        fi
    fi

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
        -vf "scale=${W}:${H},${VF}" -r "$FPS" -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p "$clip"
    [ -f "$clip" ] && echo "[rec] ✓ klip: $clip ($(du -h "$clip" | cut -f1))" || echo "[rec] ✗ klip yok: $level"

    for cam in $EXTRA_CAM_DIRS; do
        local cam_dir="/tmp/frames_${cam}" cam_n cam_fps
        local cam_out="$cam"
        case "$cam" in
            overview) cam_out="tum_saha" ;;
            side_north) cam_out="kuzey_kenar" ;;
            side_south) cam_out="guney_kenar" ;;
            side_east) cam_out="dogu_kenar" ;;
            side_west) cam_out="bati_kenar" ;;
        esac
        cam_n=$(ls "$cam_dir"/*.jpg 2>/dev/null | wc -l)
        if [ "$cam_n" -gt 3 ]; then
            cam_fps=$(python3 -c "print(max(1,round($cam_n/max($fps_simt,1))))" 2>/dev/null); cam_fps=${cam_fps:-$FPS}
            ffmpeg -y -loglevel warning -framerate "$cam_fps" -pattern_type glob -i "$cam_dir/*.jpg" \
                -vf "scale=${W}:${H}" -r "$FPS" -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p \
                "$OUTDIR/${cam_out}_${level}.mp4" \
                && echo "[rec] ✓ kamera ${cam_out}: ${cam_out}_${level}.mp4 ($cam_n kare)"
        fi
    done
}

: > "$LOG"

CLIPS=()
for lv in $LEVELS; do
    clip="/tmp/clips/${lv}.mp4"
    record_one "$lv" "$clip"
    [ -f "$clip" ] && CLIPS+=("$clip")
done

# Hakem/model logu (tek oturum — kaydedilen seviyeler için)
echo "[rec] hakem/model logu üretiliyor → $LOG"
DET="$OUTDIR/detections.json"
if [ "$(echo $LEVELS | wc -w)" -eq 1 ]; then
    python3 scripts/hakem_log.py --level "$LEVELS" --map "$LAST_ACTUAL_MAP" --detections "$DET" --realtime "$RT" --out "$LOG" >/dev/null 2>&1 || echo "[rec] (log üretilemedi)"
else
    python3 scripts/hakem_log.py --all --map "$LAST_ACTUAL_MAP" --detections "$DET" --realtime "$RT" --out "$LOG" >/dev/null 2>&1 || echo "[rec] (log üretilemedi)"
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
    if [ "$RECORDING_INCOMPLETE" -ne 0 ]; then
        echo "[rec] HATA: en az bir klip görev sonucu görülmeden kesildi; SEBEP/SIM_T ayrıntısı iha_scan_<seviye>/meta.txt içinde" >&2
        exit 2
    fi
else
    echo "[rec] ✗ Video oluşmadı!"; exit 1
fi
