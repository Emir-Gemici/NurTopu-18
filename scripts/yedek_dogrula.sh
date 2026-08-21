#!/usr/bin/env bash
# NAVITAS yedek DOGRULAMA — "yuklendi sanmak" ile "yuklendigini bilmek" ayri seylerdir.
# Bu projede kosulmayan kapi GECTI sayilmaz; ayni ilke yedek icin de gecerli.

set -u
RCLONE="$(command -v rclone || find "$LOCALAPPDATA/Microsoft/WinGet/Packages" -name rclone.exe -print -quit 2>/dev/null)"
UZAK="drive:navitas_yedek"
KOK="O:/navitas"

echo "=============================================================="
echo "1) RCLONE CHECK — her dosya, boyut ve HASH ile karsilastirilir"
echo "=============================================================="
# --one-way: uzakta fazladan dosya olmasi hata sayilmaz, YERELDE OLUP UZAKTA
# OLMAYAN aranir. Eksik varsa asagida listelenir.
for D in dji models results data codes jetson_paket test_images rapor \
         navitas-local-train dataset rescuenet-roads; do
  printf '%-22s ' "$D"
  "$RCLONE" check "$KOK/$D" "$UZAK/$D" --one-way --fast-list 2>&1 \
    | grep -E "^[0-9]{4}|ERROR|NOTICE" | tail -1
done

echo ""
echo "=============================================================="
echo "2) DJI PARMAK IZI — rclone'dan BAGIMSIZ ikinci kanit"
echo "=============================================================="
# Yerel dosyalarin sha256'lari cekim gunu olculdu (dji_parmak_izi.json).
# Burada YENIDEN olculur: yerel bozulma olduysa yedek de bozugu tasir.
O:/navitas-local-train/venv/Scripts/python.exe - <<'PY'
import hashlib, json
from pathlib import Path
kayit = json.loads(Path("O:/navitas/dji_parmak_izi.json").read_text(encoding="utf-8"))
tut = bozuk = 0
for k in kayit:
    f = Path("O:/navitas/dji") / k["ad"]
    if not f.is_file():
        print("EKSIK :", k["ad"]); bozuk += 1; continue
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for blok in iter(lambda: fh.read(1 << 22), b""):
            h.update(blok)
    if h.hexdigest() == k["sha256"]:
        tut += 1
    else:
        print("DEGISMIS:", k["ad"]); bozuk += 1
print(f"parmak izi: {tut} tuttu · {bozuk} sorunlu · toplam {len(kayit)}")
PY

echo ""
echo "=============================================================="
echo "3) DEPO YEDEGI — bundle gercekten acilabiliyor mu?"
echo "=============================================================="
# Bozuk bir bundle da dosya olarak vardir; ACILABILIRLIGI ayri sorudur.
if [ -f "$KOK/navitas_depo.bundle" ]; then
  git bundle verify "$KOK/navitas_depo.bundle" 2>&1 | tail -3
else
  echo "bundle YOK — yedek betigi kosuldu mu?"
fi
