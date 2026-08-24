#!/usr/bin/env bash
# KADEME DOGRULAMA — "cikis kodu 0" ile "is yapildi" AYRI SEYLERDIR.
#
# 🔴 NEDEN VAR (olculdu, 2026-08-21): yedek betiginin ilk kosumunda rclone
#    `BITTI cikis=0 · dji` yazdi ve Drive'a TEK BAYT yuklememisti (0 nesne,
#    27 dakika). Betik cikis koduna guvendi, SONUCA bakmadi. Bu, projenin
#    tekrar eden kusuru: YAPILMAYANI BASARI SAYMAK (D-180 sinifi).
#
# 🔴 2026-08-24 — BU BETIGIN KENDISI AYNI KUSURU TASIYORDU:
#      un=${un:-0} ; if [ "$un" -eq 0 ] ...; then durum="HIC YUKLENMEDI"
#    `rclone size` API hatasi/kota yuzunden BOS donunce bu satir onu 0 SAYIP
#    "HIC YUKLENMEDI" hukmu veriyordu. Olculdu: betik uc kademe icin
#    "HIC YUKLENMEDI (0 dosya)" dedi; ayni anda elle sorguldugunda
#      navitas-local-train 16.467 nesne · dataset 5.007 · egitim_calisma_alani 9.851
#    cikti. Yani VERI YERINDEYDI, OLCUM BASARISIZDI.
#    Bu zincirde ayni sinifin UCUNCU ornegi (yedek betigi, bekci, dogrulayici).
#    CARE: OLCULEMEDI bir DEGER DEGILDIR — ayri raporlanir, 0 sayilmaz,
#    ve olcum 3 kez DENENIR.
#
# ⚠ HARIC TUTULAN KADEMELER: bazi kademeler `--exclude` ile yedeklenir
#    (or. venv). Yereli `find` ile saymak o kademelerde HER ZAMAN "EKSIK"
#    gosterir. Bu yuzden harici olan kademelerde YEREL taraf da rclone ile
#    AYNI filtreyle olculur — elmayla elma.
#
# Kullanim:  bash scripts/yedek_kademe_dogrula.sh [kademe...]

set -u
RCLONE="$(command -v rclone || find "$LOCALAPPDATA/Microsoft/WinGet/Packages" \
          -name rclone.exe -print -quit 2>/dev/null)"
[ -z "$RCLONE" ] && { echo "rclone BULUNAMADI" >&2; exit 2; }
UZAK="drive:navitas_yedek"
KOK="O:/navitas"

# kademe -> "yerel_yol|haric_deseni"   (bos haric = filtre yok)
yerel_yolu () {
  case "$1" in
    egitim_calisma_alani) echo "O:/navitas-local-train|venv/**" ;;
    navitas-local-train)  echo "$KOK/navitas-local-train|venv/**" ;;
    codes)                echo "$KOK/codes|**/epoch*.pt" ;;
    *)                    echo "$KOK/$1|" ;;
  esac
}

# rclone size -> "count bytes"  · basarisizsa BOS doner (3 deneme)
uzak_olc () {
  local hedef="$1" j n b
  for _ in 1 2 3; do
    j=$("$RCLONE" size "$hedef" --json 2>/dev/null)
    n=$(echo "$j" | grep -o '"count":[0-9]*' | cut -d: -f2)
    b=$(echo "$j" | grep -o '"bytes":[0-9]*' | cut -d: -f2)
    if [ -n "$n" ] && [ -n "$b" ]; then echo "$n $b"; return 0; fi
    sleep 5
  done
  return 1
}

KADEMELER=("$@")
[ ${#KADEMELER[@]} -eq 0 ] && KADEMELER=(dji egitim_calisma_alani models results \
    data codes jetson_paket test_images rapor navitas-local-train dataset rescuenet-roads)

printf '%-22s %10s %10s %10s %10s  %s\n' KADEME "yerel_n" "uzak_n" "yerel_GB" "uzak_GB" DURUM
eksik=0; olculemedi=0
for D in "${KADEMELER[@]}"; do
  bilgi="$(yerel_yolu "$D")"
  yol="${bilgi%%|*}"; har="${bilgi##*|}"
  [ -d "$yol" ] || continue

  if [ -n "$har" ]; then
    j=$("$RCLONE" size "$yol" --exclude "$har" --json 2>/dev/null)
    yn=$(echo "$j" | grep -o '"count":[0-9]*' | cut -d: -f2)
    yb=$(echo "$j" | grep -o '"bytes":[0-9]*' | cut -d: -f2)
  else
    yn=$(find "$yol" -type f 2>/dev/null | wc -l)
    yb=$(du -sb "$yol" 2>/dev/null | cut -f1)
  fi
  yn=${yn:-}; yb=${yb:-}
  if [ -z "$yn" ] || [ -z "$yb" ]; then
    printf '%-22s %10s %10s %10s %10s  %s\n' "$D" "?" "?" "?" "?" \
      "🔴 YEREL OLCULEMEDI (0 SAYILMADI)"
    olculemedi=$((olculemedi+1)); continue
  fi

  if u="$(uzak_olc "$UZAK/$D")"; then
    un="${u% *}"; ub="${u#* }"
  else
    printf '%-22s %10s %10s %10.2f %10s  %s\n' "$D" "$yn" "?" \
      "$(echo "$yb" | awk '{print $1/1073741824}')" "?" \
      "🔴 UZAK OLCULEMEDI (3 deneme) — 0 SAYILMADI, hukum YOK"
    olculemedi=$((olculemedi+1)); continue
  fi

  if   [ "$un" -eq 0 ] && [ "$yn" -gt 0 ]; then durum="HIC YUKLENMEDI"
  elif [ "$un" -lt "$yn" ]; then durum="EKSIK ($((yn-un)) dosya)"
  elif [ "$ub" -lt "$yb" ]; then durum="BAYT EKSIK"
  else durum="TAM"; fi
  [ "$durum" != "TAM" ] && eksik=$((eksik+1))

  printf '%-22s %10s %10s %10.2f %10.2f  %s%s\n' "$D" "$yn" "$un" \
     "$(echo "$yb" | awk '{print $1/1073741824}')" \
     "$(echo "$ub" | awk '{print $1/1073741824}')" "$durum" \
     "$([ -n "$har" ] && echo "  [haric: $har]")"
done

echo ""
[ "$olculemedi" -gt 0 ] && echo "⚠ $olculemedi kademe OLCULEMEDI — bu 'eksik' DEMEK DEGILDIR, hukum verilmedi."
if [ "$eksik" -eq 0 ] && [ "$olculemedi" -eq 0 ]; then
  echo "TUM KADEMELER TAM. (Hash dogrulamasi ayri: scripts/yedek_dogrula.sh)"
else
  [ "$eksik" -gt 0 ] && echo "🔴 $eksik KADEME EKSIK — ayni komutu tekrar kosmak yeterlidir."
  exit 1
fi
