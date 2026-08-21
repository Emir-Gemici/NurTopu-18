#!/usr/bin/env bash
# NAVITAS -> Google Drive tam yedek (136 GB).
# Hazirlayan: Claude 1 (mimar) · 2026-08-21 · kullanici komutuyla
#
# NEDEN RCLONE, Drive for Desktop DEGIL:
#   O: diskinde 207 GB bos yer kaldi (%89 dolu). Drive for Desktop yerel ayna
#   tutmaya calisabilir ve diski doldurur. rclone aynasizdir, kesintiden devam
#   eder ve aktarimi HASH ile dogrular.
#
# KURULUM (bir kez):
#   winget install Rclone.Rclone
#   rclone config          # n -> ad: drive -> tur: drive -> tarayicidan yetkilendir
#
# KOSUM:
#   bash O:/navitas/scripts/yedek_drive.sh
#   Kesilirse AYNI komutu tekrar calistir; rclone kaldigi yerden devam eder.

set -u
# rclone yolu: winget PATH'i degistirir ama ACIK kabuklara yansimaz.
# Once PATH'te ara, yoksa winget paket dizininden coz. Ciplak yol YAZILMAZ.
RCLONE="$(command -v rclone || true)"
if [ -z "$RCLONE" ]; then
  RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
fi
if [ -z "$RCLONE" ]; then echo "rclone BULUNAMADI — kurulum yapildi mi?" >&2; exit 2; fi
echo "rclone: $RCLONE"

UZAK="drive:navitas_yedek"
KOK="O:/navitas"
# --transfers: es zamanli dosya · --checkers: karsilastirma is parcacigi
# --fast-list: Drive'da listeleme cagrisini azaltir · -P: ilerleme
# -P yerine --stats: gozetimsiz kosumda ANSI ilerleme cubugu logu okunamaz kilar.
# 2 dakikada bir TEK SATIR: aktarilan/toplam, hiz, kalan sure.
# 15 Mbit/s YUKLEME hattina gore ayarlandi (olculdu):
#  --transfers 2  : 4 es zamanli dosya 15 Mbit'i bolup her birini yavaslatiyor ve
#                   Drive oturumlarinin zaman asimina ugrama olasiligini artiriyor.
#  --drive-chunk-size 64M : daha az gidis-donus, daha az takilma noktasi.
#  --timeout / --contimeout : SESSIZ TAKILMA yerine HATA ver; ilk denemede rclone
#                   4 baglantiyi acip 27 dakika hic bayt akitmadan asili kaldi.
#  --log-file      :  boru hatti istatistik satirlarini tamponluyordu;
#                   gunluk artik DOGRUDAN dosyaya yazilir.
BAYRAK="--transfers 2 --checkers 4 --drive-chunk-size 64M --timeout 120s --contimeout 30s --retries 5 --low-level-retries 20 --stats 60s --stats-one-line -v --log-file $KOK/results/rclone_gunluk.txt"

kopyala () {   # $1 = yerel alt yol · $2 = uzak alt yol
  echo ""
  echo "=============================================================="
  echo "[$(date +%H:%M:%S)] $1  ->  $UZAK/$2"
  echo "=============================================================="
  "$RCLONE" copy "$KOK/$1" "$UZAK/$2" $BAYRAK
  echo "[$(date +%H:%M:%S)] BITTI cikis=$?  ·  $1"
}

# ── KADEME 1 · YERI DOLDURULAMAZ ─────────────────────────────────────────────
# Once bunlar: aktarim yarida kalirsa kaybi telafi edilemeyen sey gitmis olur.
kopyala "dji"                 "dji"          # 8,5 GB · o kosullar tekrar cekilemez
kopyala "models"              "models"       # 1,1 GB · uretim agirliklari (v35)
kopyala "results"             "results"      # 1,2 GB · olcum kanitlari
kopyala "data"                "data"         # 19 MB  · raw_frames + arena referansi

# ── KADEME 2 · PAHALI AMA YENIDEN URETILEBILIR ───────────────────────────────
kopyala "codes"               "codes"        # 51 GB · 51 egitim kosumu
kopyala "jetson_paket"        "jetson_paket" # 843 MB
kopyala "test_images"         "test_images"  # 355 MB
kopyala "rapor"               "rapor"        # 108 MB
kopyala "navitas-local-train" "navitas-local-train"   # 4,4 GB

# ── KADEME 3 · GENEL KUMELER (yeniden indirilebilir) ─────────────────────────
kopyala "dataset"             "dataset"        # 63 GB
kopyala "rescuenet-roads"     "rescuenet-roads" # 3,8 GB

# ── DEPONUN KENDISI ──────────────────────────────────────────────────────────
# Kod ve belgeler GitHub'da zaten var; bu, gecmisiyle birlikte TEK DOSYA yedegi.
echo ""
echo "[$(date +%H:%M:%S)] git bundle uretiliyor..."
git -C "$KOK" bundle create "$KOK/navitas_depo.bundle" --all \
  && "$RCLONE" copy "$KOK/navitas_depo.bundle" "$UZAK/depo" $BAYRAK

echo ""
echo "=============================================================="
echo "[$(date +%H:%M:%S)] TUM KADEMELER BITTI"
echo "Dogrulama icin: bash O:/navitas/scripts/yedek_dogrula.sh"
echo "=============================================================="
