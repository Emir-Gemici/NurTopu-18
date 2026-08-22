#!/usr/bin/env bash
# NAVITAS -> Google Drive tam yedek · DONMAYA DAYANIKLI SURUM (2026-08-22)
#
# 🔴 NEDEN YENIDEN YAZILDI — OLCULDU:
#   Ilk kosum 22 saatte 31 GB gonderdi (0,4 MB/s), oysa erken olcum 1,31 MiB/s
#   idi. Fark HIZ DEGIL DONMA. Olculen belirti:
#     surec CANLI · 2 baglanti ACIK · 20 sn'de 0 bayt okundu · logda 0 ERROR
#     bayt sayaci 4 DAKIKA SABIT · hiz 40 B/s -> 0 B/s · ETA "25 yil"
#   `--timeout 120s` bunu ATESLEMIYOR. Kok neden bulunamadi; care onu BEKLEMEK
#   yerine MALIYETINI DUSURMEK:
#
#   1. --max-duration 20m : rclone her 20 dakikada TEMIZ cikar, dongu yeniden
#      baslatir. Donma en fazla 20 dakikaya mal olur, SAATLERE degil.
#      `copy` bitmis dosyalari ATLAR -> yeniden baslatma UCUZDUR.
#   2. --transfers 16     : kalan is (codes/runs, dataset) COK SAYIDA KUCUK
#      DOSYA; bunlar bant genisligi degil GECIKME sinirlidir, tek care
#      paralelliktir. Ayrica 16'da bir baglanti donarsa kayip 1/16, 1/2 degil.
#   3. --drive-chunk-size 16M : 64M x 16 = 1 GB RAM olurdu; ayrica donan parca
#      ne kadar buyukse o kadar cok is bosa gider.
#
# NEDEN RCLONE, Drive for Desktop DEGIL:
#   O: diskinde 207 GB bos kaldi (%89 dolu); Drive for Desktop yerel ayna
#   tutmaya calisip diski doldurabilir. rclone aynasizdir ve HASH ile dogrular.
#
# KOSUM:  bash O:/navitas/scripts/yedek_drive.sh
#   Kesilirse AYNI komut; kaldigi yerden devam eder.

set -u
RCLONE="$(command -v rclone || true)"
if [ -z "$RCLONE" ]; then
  RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
fi
if [ -z "$RCLONE" ]; then echo "rclone BULUNAMADI — kurulum yapildi mi?" >&2; exit 2; fi
echo "rclone: $RCLONE"

UZAK="drive:navitas_yedek"
KOK="O:/navitas"
BAYRAK="--transfers 16 --checkers 16 --drive-chunk-size 16M --timeout 120s \
--contimeout 30s --retries 3 --low-level-retries 10 --max-duration 20m \
--stats 5m --stats-one-line -v --log-file $KOK/results/rclone_gunluk.txt"

# Uzaktaki bayt sayisi — "ilerleme oldu mu" sorusunun tek DURUST cevabi.
uzak_bayt () {
  "$RCLONE" size "$UZAK/$1" --json 2>/dev/null \
    | grep -o '"bytes":[0-9]*' | cut -d: -f2
}

kopyala () {   # $1 = alt yol
  ad="$1"; onceki=-1; tur=0
  echo ""
  echo "=============================================================="
  echo "[$(date +%H:%M:%S)] KADEME: $ad"
  echo "=============================================================="
  while [ "$tur" -lt 40 ]; do
    tur=$((tur + 1))
    "$RCLONE" copy "$KOK/$ad" "$UZAK/$ad" $BAYRAK
    simdi="$(uzak_bayt "$ad")"; simdi="${simdi:-0}"
    echo "[$(date +%H:%M:%S)] $ad · tur $tur · uzakta $((simdi / 1048576)) MB"
    # 🔴 "BITTI MI" SORUSU CIKIS KODUNA DEGIL SONUCA SORULUR.
    #    D-267: ilk kosum "BITTI cikis=0" deyip TEK BAYT yuklememisti.
    if [ "$simdi" = "$onceki" ]; then
      echo "[$(date +%H:%M:%S)] $ad · iki turda ilerleme YOK -> kademe tamam"
      break
    fi
    onceki="$simdi"
  done
}

# ── KADEME 1 · YERI DOLDURULAMAZ ─────────────────────────────────────────────
kopyala "dji"
kopyala "models"
kopyala "results"
kopyala "data"

# ── KADEME 2 · PAHALI AMA YENIDEN URETILEBILIR ───────────────────────────────
kopyala "codes"
kopyala "jetson_paket"
kopyala "test_images"
kopyala "rapor"
kopyala "navitas-local-train"

# ── KADEME 3 · GENEL KUMELER — YENIDEN INDIRILEBILIR ─────────────────────────
# ⚠ Bu iki kademe 48 GB'dir ve halka acik kaynaklardan yeniden indirilebilir.
#    Sure onemliyse betigi BURADA durdurmak MESRUDUR.
kopyala "dataset"
kopyala "rescuenet-roads"

# ── DEPONUN KENDISI ──────────────────────────────────────────────────────────
echo ""
echo "[$(date +%H:%M:%S)] git bundle uretiliyor..."
git -C "$KOK" bundle create "$KOK/navitas_depo.bundle" --all \
  && "$RCLONE" copy "$KOK/navitas_depo.bundle" "$UZAK/depo" $BAYRAK

echo ""
echo "=============================================================="
echo "[$(date +%H:%M:%S)] TUM KADEMELER BITTI"
echo "Dogrulama: bash O:/navitas/scripts/yedek_kademe_dogrula.sh"
echo "=============================================================="
