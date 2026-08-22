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
# 🔴 GUNLUK YEDEKLENEN AGACIN DISINDA DURUR. Ilk denemede results/ icindeydi ve
#    rclone KENDI LOGUNU kopyalamaya calisti: dosya transfer sirasinda buyuyor,
#    md5 tutmuyor -> "corrupted on transfer" (16 hata) VE results/ boyutu her
#    turda degistigi icin "ilerleme yok -> bitti" kontrolu HIC atesleyemedi
#    (7 tur bosa dondu, exit 255). Yedek kendi ciktisini yedekleyemez.
GUNLUK="${TEMP:-/tmp}/navitas_rclone_gunluk.txt"
echo "gunluk: $GUNLUK"
BAYRAK="--transfers 16 --checkers 16 --drive-chunk-size 16M --timeout 120s \
--contimeout 30s --retries 3 --low-level-retries 10 --max-duration 20m \
--stats 5m --stats-one-line -v --log-file $GUNLUK"

# Uzaktaki bayt sayisi — "ilerleme oldu mu" sorusunun tek DURUST cevabi.
uzak_bayt () {
  "$RCLONE" size "$UZAK/$1" --json 2>/dev/null \
    | grep -o '"bytes":[0-9]*' | cut -d: -f2
}

kopyala () {   # $1 = alt yol · $2 = HARIC tutulacak desen (istege bagli)
  ad="$1"; haric="${2:-}"; onceki=-1; tur=0
  echo ""
  echo "=============================================================="
  echo "[$(date +%H:%M:%S)] KADEME: $ad"
  echo "=============================================================="
  while [ "$tur" -lt 40 ]; do
    tur=$((tur + 1))
    t0=$(date +%s)
    # `$haric` TIRNAKLI gecirilir: tirnaksiz birakilirsa kabuk `venv/**`
    # desenini CWD'ye gore glob'lamaya calisir.
    if [ -n "$haric" ]; then
      "$RCLONE" copy "$KOK/$ad" "$UZAK/$ad" $BAYRAK --exclude "$haric"
    else
      "$RCLONE" copy "$KOK/$ad" "$UZAK/$ad" $BAYRAK
    fi
    gecen=$(( $(date +%s) - t0 ))
    simdi="$(uzak_bayt "$ad")"
    # T140: OLCULEMEDI != 0 (D-180 sinifi). Olculdu 11:05:49 —
    #   `uzak_bayt` BOS dondu, betik 0 sayip "uzakta 0 MB" yazdi;
    #   oysa uzakta 1218 MB vardi. Bos olcum (b) olcutunu YANLIS
    #   ateslerdi. Artik tur TEKRARLANIR.
    if [ -z "$simdi" ]; then
      echo "[$(date +%H:%M:%S)] $ad · tur $tur · uzak bayt OLCULEMEDI -> tekrar"
      sleep 15
      continue
    fi
    echo "[$(date +%H:%M:%S)] $ad · tur $tur · ${gecen}sn · uzakta $((simdi / 1048576)) MB"
    # 🔴 IKI OLCUT, IKISI DE CIKIS KODUNDAN BAGIMSIZ (D-267: ilk kosum
    #    "BITTI cikis=0" deyip TEK BAYT yuklememisti).
    #  a) SURE: rclone --max-duration 20m'e TAKILMADIYSA isini bitirmistir.
    #     Bu, sürekli DEGISEN dizinlerde (results/) de calisan tek olcuttur —
    #     bayt esitligi orada asla saglanmaz.
    if [ "$gecen" -lt 1140 ]; then
      echo "[$(date +%H:%M:%S)] $ad · sure sinirina TAKILMADI -> kademe tamam"
      break
    fi
    #  b) BAYT: degismiyorsa ilerleme yok.
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
# 🔴 venv/ HARIC — kullanici karari 2026-08-22 21:40, OLCUMLE alindi.
#   Olculen: venv 42.817 dosya / 5,25 GB · kademe hizi 0,80 DOSYA/sn (bayt
#   degil dosya sinirli; son 23 dk'da 2,2 MB ama 1.447 dosya kopyalandi).
#   Kalan is venv ile 41.866 dosya = 14,5 saat · venv'siz 14.787 = 5,1 saat.
#   Kullanicinin 1 gun kisiti venv ile TUTMUYORDU.
#   YENIDEN URETILEBILIR: tarif `results/t140/venv_tarifi_pip_freeze.txt`
#   (70 paket · Python 3.13.7 AMD64 · torch 2.11.0+cu128 · ultralytics 8.4.92).
#   ⚠ SINIR: pip freeze paket surumlerini verir, torch'un CUDA tekerlegi icin
#     ek indeks gerekir (+cu128). Kurulum tarifi tek satirda degildir.
#   ⚠ Drive'a ONCEDEN yuklenmis 15.776 venv dosyasi SILINMEDI, orada duruyor;
#     `copy` kullaniliyor, `sync` DEGIL (kullanici kisiti) — yani dislama
#     yalnizca BUNDAN SONRASINI etkiler, mevcut yedegi BOZMAZ.
kopyala "navitas-local-train" "venv/**"

# ── KADEME 3 · dataset — SECICI (kullanici karari 2026-08-22) ────────────────
# 🔴 dataset/ 63 GB ve KULLANICI ONU YEDEKTEN CIKARDI (sure kisiti).
#    AMA TUMU ATILAMAZ: copy_paste_* ailesi URETIM MODELININ EGITIM KUMESIDIR.
#    dataset/karisim_t127.yaml -> copy_paste_t127 = URETIMDEKI v35'in
#    egitim verisi. Kaybedilirse v35'in NASIL egitildigi bir daha uretilemez
#    ve denetlenemez. Toplam 1,5 GB — sureye etkisi YOK.
#
#    ATILAN (61,5 GB, hepsi YENIDEN URETILEBILIR):
#      rescuenet_ham 44G (halka acik indirme) · rescuenet_2sinif_engelli 8,7G
#      (57 betigi uretir) · sentetik_arena 3,9G (51 betigi uretir) ·
#      rescuenet_11sinif 2,0G (41 betigi uretir) · rescuenet_1024/yolo/kirpik/
#      yolo_256 · gercek_otopark(_2x) (raw_frames'ten turer — raw_frames YEDEKTE)
#    ⚠ sentetik_arena'nin yeniden uretimi TOHUMA baglidir; tohum sabit degilse
#      birebir ayni kume gelmez. Bu bir SINIRDIR, kayda geciyor.
for K in copy_paste_gercek copy_paste_t121 copy_paste_t122a copy_paste_t122ac          copy_paste_t127 copy_paste_smoke gercek_kompozit; do
  [ -d "$KOK/dataset/$K" ] && kopyala "dataset/$K"
done
# karisim yaml'lari kucuk ama kumeleri TARIF EDER — onlarsiz kume anlamsizdir
"$RCLONE" copy "$KOK/dataset" "$UZAK/dataset" --include "*.yaml" --include "*.json" --max-depth 1 $BAYRAK
# 🔴 T140 OLCUMU: atilan kumelerin URETIM TARIFI alt dizindeki data.yaml
#    icinde duruyor ve --max-depth 1 onu KACIRIYORDU. Ornek (olculdu):
#      dataset/sentetik_arena/data.yaml ilk satiri:
#      "51_sentetik_arena.py (seed=7, ayni_malzeme=0.45, dar=0.28, kadraj=False)"
#    Ureteci denetledim: satir 1531-1532 HEM `random.Random(args.seed)` HEM
#    `np.random.seed(args.seed)` ile tohumlanir -> uretim DETERMINISTIKTIR.
#    Yani tarif yedeklenirse 61,5 GB atmak GUVENLIDIR; tarif kaybolursa
#    kume bir daha BIREBIR uretilemez. Tarifler birkac KB.
"$RCLONE" copy "$KOK/dataset" "$UZAK/dataset" --include "*/data.yaml" --include "*/*.json" --max-depth 2 $BAYRAK
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
