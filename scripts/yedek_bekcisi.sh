#!/usr/bin/env bash
# T140 — YEDEK BEKCISI. Donmayi DAKIKALAR icinde yakalar ve etkisiz kilar.
#
# 🔴 NEDEN AJAN DEGIL BETIK: gorev "donmalari TAMAMEN etkisiz hale getirsin"
# diyor ve yedek saatlerce surecek. Deterministik bir dongu saniyeler icinde
# tepki verir, jeton harcamaz, suruklenmez ve makine basinda kimse olmadan
# calisir. Karar KAYDA GECIRILDI (D-275) — sessizce baska bir sey yapilmadi.
#
# 🔴 TEK DURUST OLCUT UZAKTA NE OLDUGUDUR (D-267): ilk kosum "BITTI cikis=0"
# deyip TEK BAYT yuklememisti. Log satirina DEGIL, `rclone size` sonucuna
# bakilir.
#
# TOLERANS TAHMINLE DEGIL VERIDEN TURETILIR:
#   Uzak bayt, BUYUK bir dosya havadayken de SABIT gorunur (Drive dosyayi
#   ancak tamamlaninca gosterir). Bu yuzden "kac olcum sabit kalirsa donma"
#   sorusu sabit bir N ile cevaplanamaz. Kademedeki EN BUYUK yerel dosya ve
#   OLCULEN hiz ile hesaplanir:
#       tolerans = max(TABAN_TOLERANS, (en_buyuk_dosya / olculen_hiz) * 1.5)
#   Boylece kucuk dosyali kademede donma ~5 dakikada, buyuk dosyali kademede
#   dosyanin gercekten surebilecegi sureden sonra yakalanir.
#
# MUDAHALE: yalniz `rclone` sureci oldurulur. Yedek betiginin `while` dongusu
# `rclone copy`yi yeniden baslatir ve TAMAMLANMIS dosyalari ATLAR.
# ⚠ `sync` KULLANILMAZ, yalniz `copy` (uzaktaki baska dosyalar silinmesin).
set -u

KOK="O:/navitas"
UZAK="drive:navitas_yedek"
GUNLUK="$KOK/results/yedek_bekci_log.txt"
# 🔴 RCLONE GUNLUGU — yedek_drive.sh ile AYNI YOL OLMAK ZORUNDA.
#    OLCULDU 2026-08-22 22:52: burada `$KOK/results/rclone_gunluk.txt` yaziyordu.
#    O dosya VAR ama BAYAT: yedek betiginin ILK surumunun gunluguydu, 11:05'te
#    468.999 baytta dondu ve artik kimse yazmiyor. Yani `stat` BASARISIZ
#    OLMUYORDU — SABIT bir dosyayi okuyordu ve "$log_boyut != $onceki_log"
#    kosulu HIC dogru cikmadi. Ayirt edici OLU KODDU.
#    Sonuc: saglikli bir aktarim (792->884->979 MiB, 1,6 MiB/s) DONMA sanilip
#    OLDURULDU ve 979 MiB'lik is COPE GITTI.
#    ⚠ DERS: "dosya var ve okunuyor" ile "dosya CANLI" AYRI SEYLERDIR. Bu
#      yuzden canlilik artik BOYUTA degil DEGISIM ZAMANINA bakar; bayat bir
#      dosyanin boyutu da sabittir ve ayni tuzagi kurar.
RCLONE_GUNLUK="${TEMP:-/tmp}/navitas_rclone_gunluk.txt"
OLCUM="$KOK/results/yedek_bekci_olcum.jsonl"
ARALIK=120          # saniye · uzak bayt orneklemesi
TABAN_TOLERANS=300  # saniye · kucuk dosyali kademede en az bu kadar bekle

RCLONE="$(command -v rclone || true)"
if [ -z "$RCLONE" ]; then
  RCLONE="$(find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
fi
[ -z "$RCLONE" ] && { echo "rclone BULUNAMADI" >&2; exit 2; }

# ⚠ YALNIZ DOSYAYA yazar. Onceki surum `tee -a` kullaniyordu VE cagiran
# stdout'u AYNI dosyaya yonlendiriyordu -> her satir IKI KEZ dusuyordu.
# Bunu "iki bekci ornegi kosuyor" diye yanlis yorumlamistim; sebep tee idi.
yaz () { echo "[$(date +%H:%M:%S)] $*" >> "$GUNLUK"; }

uzak_bayt () {   # $1 = alt yol ("" ise tum yedek)
  local hedef="$UZAK"; [ -n "${1:-}" ] && hedef="$UZAK/$1"
  "$RCLONE" size "$hedef" --json 2>/dev/null \
    | grep -o '"bytes":[0-9]*' | cut -d: -f2
}

guncel_kademe () {
  grep -o 'KADEME: [a-zA-Z0-9_/-]*' "$KOK/results/yedek_drive_log.txt" 2>/dev/null \
    | tail -1 | cut -d' ' -f2
}

en_buyuk_dosya () {   # $1 = alt yol -> bayt
  local d="$KOK/$1"
  [ -d "$d" ] || { echo 0; return; }
  find "$d" -type f -printf '%s\n' 2>/dev/null | sort -rn | head -1
}

yedek_kosuyor_mu () {
  powershell -NoProfile -Command \
    "if (Get-Process rclone -ErrorAction SilentlyContinue) { 'VAR' } else { 'YOK' }" 2>/dev/null \
    | tr -d '\r' | head -1
}

rclone_oldur () {
  powershell -NoProfile -Command \
    "Get-Process rclone -ErrorAction SilentlyContinue | Stop-Process -Force" 2>/dev/null
}

# ── TEKILLIK KILIDI ────────────────────────────────────────────────────────
# 🔴 OLCULDU: `nohup bash ... &` cagrilari birikince IKI bekci ayni anda kostu
# ve gunluge CIFT satir yazdi (11:19:36 iki kez). Iki bekci ayni anda "donma"
# deyip rclone'u iki kez oldurebilir. Kilit bunu IMKANSIZ kilar.
KILIT="$KOK/results/.bekci.kilit"
if [ -e "$KILIT" ]; then
  eski_pid="$(cat "$KILIT" 2>/dev/null || echo)"
  if [ -n "$eski_pid" ] && kill -0 "$eski_pid" 2>/dev/null; then
    echo "[$(date +%H:%M:%S)] BEKCI ZATEN KOSUYOR (PID $eski_pid) — bu ornek CIKIYOR"
    exit 0
  fi
  echo "[$(date +%H:%M:%S)] bayat kilit temizlendi (PID $eski_pid yok)"
fi
echo $$ > "$KILIT"
trap 'rm -f "$KILIT"' EXIT INT TERM

yaz "════════ BEKCI BASLADI · PID $$ · aralik ${ARALIK}sn · taban tolerans ${TABAN_TOLERANS}sn"
onceki_bayt=-1
sabit_basladi=0
mudahale=0
kayip_sn=0
son_kademe=""
bas_zaman=$(date +%s)
bas_bayt="$(uzak_bayt "")"; bas_bayt="${bas_bayt:-0}"
yaz "baslangic uzak toplam: $((bas_bayt / 1048576)) MB"

while true; do
  kademe="$(guncel_kademe)"
  [ -z "$kademe" ] && kademe="?"
  simdi_sn=$(date +%s)
  toplam="$(uzak_bayt "")"
  # 🔴 KENDI KUSURUM (11:08:45 kaydinda gorunur): basarisiz `rclone size` BOS
  #    doner ve ":-0" onu 0 SAYIYORDU -> uzak_toplam=0, hiz=-37.957.971 B/s.
  #    Yedek betiginde AYNI kusuru duzeltirken kendi bekcimde tasiyordum.
  #    OLCULEMEDI bir DEGER DEGILDIR: ornek ATLANIR, `onceki_bayt` DOKUNULMAZ,
  #    donma sayaci ILERLEMEZ (yanlis mudahale = gereksiz kesinti).
  if [ -z "$toplam" ]; then
    yaz "uzak bayt OLCULEMEDI -> ornek ATLANDI (donma sayaci ilerlemedi)"
    sleep "$ARALIK"
    continue
  fi
  kademe_bayt="$(uzak_bayt "$kademe")"; kademe_bayt="${kademe_bayt:-0}"

  gecen=$((simdi_sn - bas_zaman))
  artis=$((toplam - bas_bayt))
  hiz_bps=0
  [ "$gecen" -gt 0 ] && hiz_bps=$((artis / gecen))

  printf '{"t":"%s","kademe":"%s","uzak_toplam":%s,"kademe_bayt":%s,"hiz_Bps":%s,"mudahale":%s}\n' \
    "$(date +%H:%M:%S)" "$kademe" "$toplam" "$kademe_bayt" "$hiz_bps" "$mudahale" >> "$OLCUM"

  if [ "$kademe" != "$son_kademe" ]; then
    yaz "KADEME -> $kademe · uzak toplam $((toplam / 1048576)) MB"
    son_kademe="$kademe"; onceki_bayt=-1; sabit_basladi=0
  fi

  # ── TOLERANSI VERIDEN TURET ────────────────────────────────────────────
  buyuk="$(en_buyuk_dosya "$kademe")"; buyuk="${buyuk:-0}"
  tol="$TABAN_TOLERANS"
  # 🔴 OLCULDU 2026-08-22 22:52: bu turetme TAM GEREKTIGI ANDA COKUYORDU.
  #    `hiz_bps` UZAK BAYT artisindan hesaplaniyor; buyuk dosya havadayken
  #    uzak bayt SABIT -> artis 0 -> hiz 0 -> `-gt 0` korumasi duser ->
  #    tolerans 300'de kalir. Yani "buyuk dosyayi koru" formulunu BUYUK DOSYA
  #    devre disi birakiyordu. Dairesel kusur; 2809 MB'lik dosyada tolerans
  #    2633sn olmaliyken 300sn kullanildi ve saglikli aktarim olduruldu.
  #    CARE: hiz olculemiyorsa TABAN HIZ varsayilir. 0,5 MiB/s bu hatta
  #    OLCULEN en dusuk degerin (1,0 MiB/s) yarisidir — muhafazakar.
  taban_hiz=$((512 * 1024))
  hiz_tol="$hiz_bps"
  [ "$hiz_tol" -lt "$taban_hiz" ] && hiz_tol="$taban_hiz"
  if [ "$buyuk" -gt 0 ]; then
    dosya_sn=$(( buyuk / hiz_tol ))
    aday=$(( dosya_sn * 3 / 2 ))
    [ "$aday" -gt "$tol" ] && tol="$aday"
  fi

  # ── 🔴 YANLIS POZITIF KORUMASI (11:34 olcumu) ────────────────────────────
  # OLCULDU: `results` kademesinde uzak bayt 21 DAKIKA sabit kaldi — ama
  # DONMA DEGILDI: kademe zaten yuklenmisti, rclone yalniz surekli degisen
  # gunluk dosyalarini yeniden yaziyordu (net bayt degismez). Bekci bunu
  # donma sanip rclone'u OLDURSEYDI sonsuz yeniden baslatma dongusu olurdu.
  #
  # AYIRT EDICI: rclone LOGU BUYUYOR MU?
  #   uzak sabit + log BUYUYOR  -> rclone CALISIYOR (yeni bayt yok) -> BEKLE
  #   uzak sabit + log SABIT    -> GERCEK DONMA -> MUDAHALE
  # (Mimarin olctugu ariza tam da bu ikincisiydi: "surec CANLI, logda 0 ERROR,
  #  bayt sayaci 4 DAKIKA SABIT" — orada log da ilerlemiyordu.)
  # CANLILIK = gunlugun SON DEGISIM ZAMANI (boyut DEGIL — bayat dosya tuzagi).
  log_mtime=$(stat -c %Y "$RCLONE_GUNLUK" 2>/dev/null || echo 0)
  if [ "$log_mtime" -eq 0 ]; then
    # ⚠ Gunluk OKUNAMIYORSA bu bir DEGER DEGILDIR (D-180 sinifi): "sabit"
    #   sayilmaz. Ayirt edici KULLANILAMAZ ilan edilir ve MUDAHALE EDILMEZ;
    #   koru-kapali degil, dokunma-kapali.
    yaz "[!] rclone gunlugu OKUNAMADI ($RCLONE_GUNLUK) -> ayirt edici YOK, mudahale EDILMEZ"
    onceki_bayt="$toplam"
    sleep "$ARALIK"
    continue
  fi
  # ⚠ `simdi_sn` DONGU BASINDA alinir; arada iki `rclone size` cagrisi var ve
  #   OLCULDU: 23:02:57 -> 23:07:56 arasi 299sn, yani cagrilar ~180sn suruyor.
  #   Bayat saatle hesaplayinca yas NEGATIF cikti (-176sn) ve gunluge oyle
  #   yazildi. Hukum dogruydu ama SAYI yanlisti; taze saatle hesaplanir.
  log_yas=$(( $(date +%s) - log_mtime ))
  # Gunluk SON ORNEKLEME ARALIGI icinde yazildiysa rclone CALISIYOR — uzak
  # bayt sabit olsa bile. Buyuk dosya havadayken Drive dosyayi ancak
  # TAMAMLANINCA sayar; tek canlilik sinyali budur.
  # (yedek_drive.sh `--stats 1m` ile dakikada bir satir yazar; ARALIK=120sn.)
  if [ "$log_yas" -lt "$ARALIK" ]; then
    if [ "$toplam" = "$onceki_bayt" ]; then
      yaz "uzak bayt sabit AMA rclone logu ${log_yas}sn once yazilmis -> CALISIYOR, mudahale YOK"
    fi
    sabit_basladi=0
  fi

  if [ "$toplam" = "$onceki_bayt" ] && true; then
    [ "$sabit_basladi" -eq 0 ] && sabit_basladi=$simdi_sn
    sabit_sure=$((simdi_sn - sabit_basladi))
    if [ "$sabit_sure" -ge "$tol" ]; then
      mudahale=$((mudahale + 1))
      kayip_sn=$((kayip_sn + sabit_sure))
      yaz "🔴 DONMA #$mudahale · kademe=$kademe · uzak $((toplam / 1048576)) MB · ${sabit_sure}sn SABIT (tolerans ${tol}sn, en buyuk dosya $((buyuk / 1048576)) MB) -> rclone OLDURULUYOR"
      rclone_oldur
      sleep 10
      yaz "   rclone oldurulda; yedek betiginin dongusu yeniden baslatacak (copy tamamlanmisi ATLAR)"
      sabit_basladi=0; onceki_bayt=-1
    fi
  else
    sabit_basladi=0
  fi
  onceki_bayt="$toplam"

  if [ "$(yedek_kosuyor_mu)" = "YOK" ]; then
    sleep 60
    if [ "$(yedek_kosuyor_mu)" = "YOK" ]; then
      yaz "rclone sureci YOK (2 kez) — yedek bitmis olabilir. BEKCI DURUYOR."
      break
    fi
  fi
  sleep "$ARALIK"
done

son="$(uzak_bayt "")"; son="${son:-0}"
gecen=$(( $(date +%s) - bas_zaman ))
yaz "════════ BEKCI BITTI · sure $((gecen / 60)) dk · uzak $((son / 1048576)) MB"
yaz "mudahale: $mudahale · toplam sabit-kalma $((kayip_sn / 60)) dk"
