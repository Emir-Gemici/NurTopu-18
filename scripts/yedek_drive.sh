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
# 🔴 --max-duration ARTIK KADEME BASINA (2026-08-22, OLCULDU).
#   20 dakikalik giyotin BEKCIDEN ONCEKI caredir. Bekci artik var ve
#   calistigini gosterdi (DONMA #1'i yakaladi, 14:31). Buyuk dosyada bu
#   giyotin gereksiz DEGIL, DOGRUDAN ZARARLI:
#     22:04:57 dji basladi · 3 MP4 (7,37 GiB) paralel
#     22:24:58 ERROR: max transfer duration reached  -> UCU DE "Failed to copy"
#              1.919 GiB aktarilmisti, HEPSI ATILDI
#     22:35:37 ikinci tur: 998 MiB / 7,368 GiB, ETA 1s32d  -> yine 20 dk'da olecek
#   1,2 MiB/s'de 7,37 GiB ~1,7 SAAT surer; 20 dakikada BITEMEZ, yani dosya
#   ASLA tamamlanmaz. Ustelik olcut (b) iki turda bayt ilerlemeyince kademeyi
#   "tamam" ilan edip GECERDI -> yeri doldurulamaz cekim yedeklenmemis halde
#   BASARI sayilirdi. (D-180 sinifi: YAPILMAYANI BASARI SAYMAK.)
BAYRAK="--transfers 16 --checkers 16 --drive-chunk-size 16M --timeout 120s \
--contimeout 30s --retries 3 --low-level-retries 10 \
--stats 1m --stats-one-line -v --log-file $GUNLUK"
# ⚠ --stats 1m (5m DEGIL): bekci CANLILIGI gunlugun BUYUMESINDEN anliyor.
#   Buyuk dosya yuklenirken uzak bayt SABIT gorunur (Drive dosyayi ancak
#   tamamlaninca sayar), tek canlilik sinyali gunluktur. 5 dakikalik aralik
#   bekcinin 300 sn'lik taban toleransiyla CAKISIYORDU -> yanlis "donma".

# Uzaktaki bayt sayisi — "ilerleme oldu mu" sorusunun tek DURUST cevabi.
uzak_bayt () {
  "$RCLONE" size "$UZAK/$1" --json 2>/dev/null \
    | grep -o '"bytes":[0-9]*' | cut -d: -f2
}

kopyala () {   # $1 = yol · $2 = HARIC · $3 = sure · $4 = TAM · $5 = UZAK AD
  ad="$1"; haric="${2:-}"; sure="${3:-20m}"; tam_sart="${4:-0}"; uzak_zorla="${5:-}"
  onceki=-1; tur=0
  # 🔴 MUTLAK YOL DESTEGI (2026-08-23): `O:/navitas-local-train` KOK'un ALTINDA
  #    DEGIL, KARDESI. Kademe listesi hep `$KOK/$ad` varsaydigi icin o dizin
  #    HIC YEDEKLENMIYORDU — icinde 129 egitim betigi ve venv disi 9.850 dosya
  #    (2.148 MB) var ve HICBIRI depoda izlenmiyor. Uretim modellerini ureten
  #    kod, tek kopya diskteydi.
  #    🔴 UZAK AD CAKISMASI (ilk denemede YAPTIM, 07:09'da yakalandi):
  #      `$KOK/navitas-local-train` DIYE AYRI BIR DIZIN VAR (saplama: 7 betik +
  #      kendi venv'i). `basename "O:/navitas-local-train"` de AYNI adi verir,
  #      yani ikisi AYNI uzak klasore yaziyordu ve icerikleri karisiyordu;
  #      dogrulayici da yanlis kiyaslardi. `basename`'e GUVENILMEZ — uzak ad
  #      $5 ile ACIKCA verilir.
  case "$ad" in
    [A-Za-z]:*|/*) kaynak="$ad"; uzak_ad="${uzak_zorla:-$(basename "$ad")}" ;;
    *)             kaynak="$KOK/$ad"; uzak_ad="${uzak_zorla:-$ad}" ;;
  esac
  case "$sure" in
    *h) sure_sn=$(( ${sure%h} * 3600 )) ;;
    *m) sure_sn=$(( ${sure%m} * 60 )) ;;
    *)  sure_sn=1200 ;;
  esac
  esik=$(( sure_sn - 60 ))
  # 🔴 TAM SARTI ile HARIC BIRLIKTE KULLANILAMAZ: `du -sb` yerel agacin
  #    TAMAMINI sayar, disladigimiz dosyalar dahil. O yuzden uzak ASLA yerele
  #    erisemez ve kademe SONSUZ DONER (40 tur x sure). Fail-loud kapatilir.
  if [ -n "$haric" ] && [ "$tam_sart" = "1" ]; then
    echo "[$(date +%H:%M:%S)] [!] $uzak_ad · TAM sarti HARIC ile birlikte" \
         "kullanilamaz (du yerelin TAMAMINI sayar) -> TAM sarti KAPATILDI"
    tam_sart=0
  fi
  echo ""
  echo "=============================================================="
  echo "[$(date +%H:%M:%S)] KADEME: $uzak_ad   (kaynak: $kaynak)"
  echo "=============================================================="
  while [ "$tur" -lt 40 ]; do
    tur=$((tur + 1))
    t0=$(date +%s)
    # `$haric` TIRNAKLI gecirilir: tirnaksiz birakilirsa kabuk `venv/**`
    # desenini CWD'ye gore glob'lamaya calisir.
    if [ -n "$haric" ]; then
      "$RCLONE" copy "$kaynak" "$UZAK/$uzak_ad" $BAYRAK \
        --max-duration "$sure" --exclude "$haric"
    else
      "$RCLONE" copy "$kaynak" "$UZAK/$uzak_ad" $BAYRAK --max-duration "$sure"
    fi
    gecen=$(( $(date +%s) - t0 ))
    simdi="$(uzak_bayt "$uzak_ad")"
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
    if [ "$gecen" -lt "$esik" ]; then
      #  🔴 c) TAM SARTI: "sure sinirina takilmadi" ile "is bitti" AYRI
      #     SEYLERDIR. Yeri doldurulamaz ve DEGISMEYEN kademelerde (dji)
      #     uzak >= yerel aranir; degilse tur TEKRARLANIR. Degisen dizinlerde
      #     (results/) bu sart ARANMAZ, orada bayt esitligi asla saglanmaz.
      if [ "$tam_sart" = "1" ]; then
        yerel="$(du -sb "$kaynak" 2>/dev/null | cut -f1)"
        if [ -n "$yerel" ] && [ "$simdi" -lt "$yerel" ]; then
          echo "[$(date +%H:%M:%S)] $ad · sure sinirina takilmadi AMA uzak" \
               "$((simdi / 1048576)) MB < yerel $((yerel / 1048576)) MB -> DEVAM"
          onceki="$simdi"
          continue
        fi
      fi
      echo "[$(date +%H:%M:%S)] $ad · sure sinirina TAKILMADI -> kademe tamam"
      break
    fi
    #  b) BAYT: degismiyorsa ilerleme yok.
    if [ "$simdi" = "$onceki" ]; then
      if [ "$tam_sart" = "1" ]; then
        yerel="$(du -sb "$kaynak" 2>/dev/null | cut -f1)"
        if [ -n "$yerel" ] && [ "$simdi" -lt "$yerel" ]; then
          echo "[$(date +%H:%M:%S)] 🔴 $ad · ILERLEME YOK ve kademe EKSIK" \
               "(uzak $((simdi / 1048576)) MB < yerel $((yerel / 1048576)) MB)" \
               "-> kademe BITIRILIYOR ama EKSIK; dogrulayiciyi kosun"
          break
        fi
      fi
      echo "[$(date +%H:%M:%S)] $ad · iki turda ilerleme YOK -> kademe tamam"
      break
    fi
    onceki="$simdi"
  done
}

# ── KADEME 1 · YERI DOLDURULAMAZ ─────────────────────────────────────────────
# dji: 2-3 GB'lik HAM CEKIMLER. 1,2 MiB/s'de tek tur ~1,7 saat surer -> 4h.
#      TAM sarti 1: bu kademe YERI DOLDURULAMAZ ve DEGISMEZ; uzak < yerel
#      iken "tamam" denmez. (2026-08-22'de tam bu yuzden 7,38 GiB eksik kaldi.)
# 🔴 EGITIM CALISMA ALANI — 2026-08-23'e kadar HIC YEDEKLENMEMISTI.
#   `O:/navitas-local-train` KOK'un kardesi oldugu icin kademe listesine hic
#   girmemis. Icinde 129 numarali egitim betigi (01_kontrol.py .. 102_*.py) ve
#   venv disi 9.850 dosya / 2.148 MB var. Ornekleme ile dogrulandi: bu
#   betiklerin HICBIRI git'te izlenmiyor. Yani uretim modellerini ureten kod
#   ne depoda ne yedekte, TEK KOPYA disktedir — ve push DONDURULMUS durumda
#   (CLAUDE.md §5), yani depo da makine disi yedek degil.
#   2,1 GB'lik bu betikler, `codes/`'un eksik 28 GB'lik kosum ciktisindan
#   (yeniden uretilebilir) kat kat degerlidir; bu yuzden KADEME 1'e, dji'den
#   HEMEN SONRA kondu.
#   venv HARIC: tarifi `results/t140/venv_tarifi_pip_freeze.txt`.
kopyala "dji" "" "4h" 1
#   ⚠ UZAK AD ACIKCA verilir: `$KOK/navitas-local-train` saplamasi da ayni
#     basename'e sahip ve ayni klasore yazardi (07:09'da yakalandi).
kopyala "O:/navitas-local-train" "venv/**" "40m" 0 "egitim_calisma_alani"
kopyala "models" "" "20m" 1
kopyala "results"                 # DEGISEN dizin — TAM sarti ARANMAZ
kopyala "data" "" "40m" 1

# ── KADEME 2 · PAHALI AMA YENIDEN URETILEBILIR ───────────────────────────────
# 🔴 codes/: ARA KONTROL NOKTALARI HARIC (olculdu 2026-08-24).
#   Eksik 451 dosya = 27,87 GB. Bunun %84'u (23,51 GB) `epochN.pt`, yani
#   egitim sirasinda her N epoch'ta bir atilan ARA agirlik — ne dagitima
#   girer ne bir olcumu yeniden uretir. Kalan 4,36 GB (37 best/last.pt +
#   grafikler + csv/yaml) hangi modelin nasil davrandiginin KAYDIDIR ve
#   TUTULUR.
#   ✅ Uretim adaylarinin agirliklari ZATEN UZAKTA (dogrulandi):
#      t127_temiz/best.pt (=v35) · t122ac_daralt_cati/best.pt · t121_etiket_ft/best.pt
#   ⚠ Geri almak icin: bu satirdaki `--exclude` desenini kaldirip yeniden kos.
#   ⚠ TAM sarti VERILEMEZ (haric ile birlikte calismaz — betikte fail-loud).
kopyala "codes" "**/epoch*.pt" "40m" 0
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
