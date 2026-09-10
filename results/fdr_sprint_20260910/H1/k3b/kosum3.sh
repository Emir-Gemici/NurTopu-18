#!/usr/bin/env bash
# T213-A K3-b tur 3 (10 Eyl, çürütücü düzeltmeleri + D-441 açık yol koridoru yerleşim düzeltmesi). GPU tek süreç, sıralı.
# 1) taban/v1/v2/v3: üretim (hb 0) detection.json'ları MEVCUT taramadan yeniden üretilir (--yeniden-tara YOK, ~3 s/harita).
#    Tur 1/2'de hb2.5 TEŞHİS geçişi aynı --kok'a yazıp 4 haritanın (v1 1 kolay, v1/v2/v3 5 orta) detection.json'unu
#    ezmişti. *_15harita.json sayıları DEĞİŞMEMELİ (kontrol: RAPOR §7).
# 2) hb2.5 TEŞHİS geçişleri ayrı köke: <v>_hb2.5/ (tarama <v>/'den okunur, --tarama-kaynak). detection.json artık
#    hb_yaricap_m / birlestirme alanlarını taşır (kanıt kendini etiketler).
# 3) D-441 yerleşim düzeltmesi sonrası v1 (varsayılan) 15 harita YENİDEN TARANIR → v1_yerlesim_d441/ (+ hb2.5 teşhisi).
#    Eski v1/ taraması (eski yerleşim) olduğu gibi kalır; tarama_ozeti.json'da mjcf_kanonik_sha256 alanı YOK = eski yerleşim.
cd "O:/navitas/.claude/worktrees/wf_e7381c6f-ab1-1" || exit 1
PY="O:/navitas-local-train/venv/Scripts/python.exe"
K="results/fdr_sprint_20260910/H1/k3b"
H15="1:kolay,1:orta,1:zor,2:kolay,2:orta,2:zor,3:kolay,3:orta,3:zor,4:kolay,4:orta,4:zor,5:kolay,5:orta,5:zor"
for v in taban v1 v2 v3; do
  echo "=== $v uretim (hb 0) yeniden, mevcut tarama $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/$v" --cikti "$K/${v}_15harita.json" --teshis-imgsz 512 2>&1 | grep "^\[K3\]"
  echo "=== $v TESHIS hb2.5 -> ${v}_hb2.5/ $(date +%H:%M:%S)"
  $PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant $v --kok "$K/${v}_hb2.5" --tarama-kaynak "$K/$v" --cikti "$K/${v}_15harita_hb2.5.json" --hb-yaricap 2.5 2>&1 | grep "^\[K3\] ÖZET"
done
echo "=== v1 YERLESIM D-441 (yeniden tarama, yeni yerlesim) $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant v1 --kok "$K/v1_yerlesim_d441" --cikti "$K/v1_15harita_yerlesim_d441.json" --yeniden-tara --teshis-imgsz 512 2>&1 | grep "^\[K3\]"
echo "=== v1 YERLESIM D-441 TESHIS hb2.5 $(date +%H:%M:%S)"
$PY simulation/mujoco/on_olcum_k3.py --haritalar "$H15" --varyant v1 --kok "$K/v1_yerlesim_d441_hb2.5" --tarama-kaynak "$K/v1_yerlesim_d441" --cikti "$K/v1_15harita_yerlesim_d441_hb2.5.json" --hb-yaricap 2.5 2>&1 | grep "^\[K3\] ÖZET"
echo "=== BITTI $(date +%H:%M:%S)"
