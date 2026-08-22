#!/usr/bin/env bash
# T140 — DOSYA BASI GECIKME mi HAT mi? Kontrollu deney.
#
# SORU: olculen ~256 KB/s (data kademesi, ~1 MB'lik 1287 dosya) HATTIN tavani
# mi, yoksa DOSYA BASI kurulum maliyeti mi?
#
# AYIRT EDICI DENEY (ayni TOPLAM boyut, farkli DOSYA SAYISI):
#   A) 1 dosya x 50 MB   --transfers 1   -> tek akisin HAM hizi
#   B) 50 dosya x 1 MB   --transfers 16  -> cok kucuk dosyanin toplam hizi
#   C) 50 dosya x 1 MB   --transfers 4   -> paralellik etkisi
# A >> B  ise  DOSYA BASI GECIKME baskin.
# A ~= B  ise  HAT sinirli.
# C vs B  paralelligin gercekten ise yarayip yaramadigini gosterir
#         (ilk kosum 4 transferle HIC bayt gondermemisti — varsayim SINANIR).
#
# ⚠ ADIL OLSUN DIYE aktarim DURDURULMUS olmalidir; ayni hat paylasilirsa
#   olcum kirlenir. Cagiran once `yedek_surec_yonet.ps1 -Kip durdur` kosar.
# ⚠ Test dosyalari AYRI bir uzak dizine gider ve SONUNDA SILINIR.
#   Silinen sey YALNIZ bu betigin kendi urettigi test dizinidir; kullanicinin
#   hicbir dosyasina dokunulmaz ve `sync` KULLANILMAZ.
set -u
KOK="O:/navitas"
UZAK="drive:navitas_hiztest"
YEREL="$(mktemp -d)"
CIKTI="$KOK/results/yedek_hat_vs_gecikme.json"

RCLONE="$(command -v rclone || true)"
[ -z "$RCLONE" ] && RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
[ -z "$RCLONE" ] && { echo "rclone yok" >&2; exit 2; }

ORTAK="--drive-chunk-size 16M --timeout 120s --contimeout 30s --retries 1 --low-level-retries 3 --stats 0"

temizle () { "$RCLONE" purge "$UZAK" >/dev/null 2>&1 || true; rm -rf "$YEREL"; }
trap temizle EXIT

echo "test dosyalari uretiliyor..."
mkdir -p "$YEREL/buyuk" "$YEREL/kucuk"
# rastgele icerik: sikistirilamaz olsun, aksi halde hat olcumu YANILTIR
head -c 52428800 /dev/urandom > "$YEREL/buyuk/tek_50MB.bin"
for i in $(seq 1 50); do head -c 1048576 /dev/urandom > "$YEREL/kucuk/k$i.bin"; done
echo "  buyuk: $(du -sh "$YEREL/buyuk" | cut -f1) · kucuk: $(du -sh "$YEREL/kucuk" | cut -f1) (50 dosya)"

kos_test () {   # $1=ad  $2=yerel  $3=uzak_alt  $4=transfers
  "$RCLONE" purge "$UZAK/$3" >/dev/null 2>&1 || true
  local t0 t1 sn bayt
  t0=$(date +%s)
  "$RCLONE" copy "$2" "$UZAK/$3" --transfers "$4" --checkers "$4" $ORTAK
  t1=$(date +%s); sn=$((t1 - t0)); [ "$sn" -le 0 ] && sn=1
  bayt="$("$RCLONE" size "$UZAK/$3" --json 2>/dev/null | grep -o '"bytes":[0-9]*' | cut -d: -f2)"
  bayt="${bayt:-0}"
  # ⚠ `bc` BU MAKINEDE YOK (olculdu: "bc: command not found" -> hiz sutunlari
  #    0.0 basildi ve olcum OKUNAMAZ gorundu; sayilar ancak ham JSON'dan
  #    cikarilabildi). Kabuk aritmetigi kullanilir, dis bagimlilik YOK.
  printf '%-34s %5d sn · %6d MB · %7d KB/s\n' \
    "$1" "$sn" "$((bayt / 1048576))" "$((bayt / sn / 1024))"
  echo "{\"test\":\"$1\",\"saniye\":$sn,\"bayt\":$bayt,\"transfers\":$4}" >> "$CIKTI.tmp"
}

: > "$CIKTI.tmp"
echo ""
echo "── OLCUM (aktarim DURDURULMUS olmali) ──────────────────────────────"
# A: hattin HAM tek-akis tavani. B-E: paralellik MERDIVENI.
# Kullanicinin sorusu ("paralel yuklesek donmalar azalir mi, 1 gunde bitmeli")
# tam olarak burada cevaplanir: darbogaz HAT ise merdiven DUZ cikar,
# DOSYA BASI GECIKME ise merdiven TIRMANIR ve nerede DOYDUGU gorunur.
kos_test "A) 1x50MB   transfers 1"  "$YEREL/buyuk" "A" 1
kos_test "B) 50x1MB   transfers 4"  "$YEREL/kucuk" "B" 4
kos_test "C) 50x1MB   transfers 16" "$YEREL/kucuk" "C" 16
kos_test "D) 50x1MB   transfers 32" "$YEREL/kucuk" "D" 32

echo ""
python_json=$(cat "$CIKTI.tmp" | tr '\n' ',' | sed 's/,$//')
echo "{\"_ne\":\"T140 · dosya basi gecikme mi hat mi\",\"sonuc\":[$python_json]}" > "$CIKTI"
rm -f "$CIKTI.tmp"
echo "ham: $CIKTI"
