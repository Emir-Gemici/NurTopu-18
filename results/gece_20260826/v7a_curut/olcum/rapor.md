# v7a ÇÜRÜTME — LENS 1: ÖLÇÜM YENİDEN ÜRETİMİ (2026-08-26)

Varsayım: aday terfi ETMEMELİ. Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`.
Ham çıktılar bu klasörde: `yeniden_say.py` / `yeniden_say.json` (JSON'lardan bağımsız sayım),
`v7a_curut_test29.json` + `v7a_curut_126.log` (kendi 126 koşumum, GPU, tek süreç).

## 1. Kayıtlı sayıların ham kaynaktan yeniden sayımı — HEPSİ TUTUYOR
Kaynak: 126 kare-kare JSON'ları + `test29_etiket_tavani_v3.json` / `sizinti/val82_etiket_tavani.json`
+ `rota_yol_olcumu.py` tanımıyla (uzlaşı etiketleri `dji_kirsal_0038_bolum_v3/labels/{test,val}`) kendi sayımım:

| küme | model | sebep | ROTA | TP/FP/FN | YANLIŞ GÜZERGÂH | kayıtlı ile |
|---|---|---|---:|---|---:|---|
| test29 | v7a | MASKE_YOK 16 · UC_BANT 5 · None 8 | 8 | 7/1/5 (FP: f218) | **0** | aynı |
| test29 | v35 | MASKE_YOK 16 · UC_BANT 7 · None 6 | 6 | 5/1/7 (FP: f124) | 5 (124, 135, 152, 196, 202) | aynı |
| val82 | v7a | MASKE_YOK 35 · UC_BANT 17 · None 30 | 30 | 28/2/15 (FP: f129, f223) | 7 (064, 129, 140, 168, 208, 210, 223) | aynı |
| val82 | v35 | MASKE_YOK 49 · UC_BANT 18 · None 15 | 15 | 15/0/28 | 10 | aynı |
111 kare toplamı: v35 21 rota / 15 yanlış (%71) · v7a 38 / 7 (%18) — D-293 sayıları doğru.
Kabul zinciri (t63 verdikt JSON): v7a K1 255/260 · K2 15/255 · K3 1/255 · K4 4/255 · K5 kesen 0 · K6 7/255 (%2,7) · VERDİKT True;
v35 K1 256 · K2 18 · K3 0 · K4 1 · K6 5/256 (%1,95). 109: çatı 0,023 (v35 0,043), 67'de red 0.

## 2. Deterministiklik — kendi 126 koşumum (GPU)
Komut: `126_t138_gece_kumesi.py --kareler dataset/dji_kirsal_0038_bolum_v3/images/test --modeller <best.pt> --cikti results/gece_20260826/v7a_curut/olcum --dosya v7a_curut_test29.json`
Çıktı: `ROTA URETILEN olceksiz 8 · sebep {'MASKE_YOK': 16, None: 8, 'UC_BANT_TEMAS_YOK': 5}` (180 sn).
Kayıtlı `gece_v7a_test29.json` ile kare kare karşılaştırma: **29/29 kare, 0 farklı alan** (sebep, wp, waypoint listeleri dâhil bayt-eş).
Yeniden sayım: rota 8 · TP 7 / FP 1 / FN 5 · yanlış güzergâh 0. Ölçüm deterministik ve doğru.

## 3. Aynı 29 karede v35 ↔ v7a kare kare
| kare | v7a | v35 | tavan | yorum |
|---|---|---|---|---|
| 062 | ROTA (yol 1,00) | MASKE_YOK | var | v7a kazanç |
| 120 | **MASKE_YOK** | **ROTA (yol 0,97, doğru)** | var | 🔴 **v7a'nın KAYBETTİĞİ tek doğru rota** |
| 124 | MASKE_YOK | ROTA (FP, yanlış) | yok | v7a kazanç (FP kalktı) |
| 135 | ROTA (yol 0,99) | ROTA (yol 0,88, yanlış) | var | v7a kazanç |
| 139 | ROTA (1,00) | MASKE_YOK | var | v7a kazanç |
| 152 | ROTA (1,00) | ROTA (yol 0,58, yanlış) | var | v7a kazanç |
| 160 | ROTA (0,99) | UC_BANT | var | v7a kazanç |
| 196 | UC_BANT | ROTA (engel 1,0 — kanal, 8/8 wp) | var | v7a kazanç (kanal rotası kalktı) |
| 202 | ROTA (1,00) | ROTA (engel 0,93, 7 wp) | var | v7a kazanç |
| 215 | ROTA (1,00) | UC_BANT | var | v7a kazanç |
| 218 | **ROTA (FP, yol 0,94)** | MASKE_YOK | **yok** | 🔴 v7a'nın yeni FP'si (rota yol üstünde ama tavan "yol yok") |
Diğer 18 kare: ikisi de rota üretmiyor (025/053/094: sebep farklı, sonuç aynı). v35'in 6 rotasından 5'i v7a'da ya doğru rotaya döndü ya kalktı; 1'i (f120, doğru) kaybedildi.

## 4. sha256 / reçete / results.csv
- `best.pt` sha256 `1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911` (v35: `e00f6b8e…438b`, farklı); best.pt = last.pt boyut (54.788.636 B) — ultralytics strip; best.pt ckpt tarihi 16:02:11 (eğitim 15:57 başladı, ~2,3 dk/epoch → epoch 2 ile uyumlu).
- args.yaml: model v35 · imgsz 512 · lr0 0,001 · warmup_epochs 5 · epochs 40 · patience 15 · batch 12 · seed 0 · deterministic · workers 8 → §14/t127 reçetesiyle uyuşuyor. Val yalnız `dji_v7/images/val` (73 kare); eğitimde `_0038_` dosyası **0** (`grep -c 0038` = 3 çıktı, ama üçü 0037/0039'un `frame_000038` kareleri — sızıntı YOK).
- results.csv 17 epoch; fitness (0,1·mAP50 + 0,9·mAP50-95, B+M) epoch 2'de en yüksek (0,4803) → best epoch 2 doğru; mask mAP50-95(M) epoch 2 = 0,1552 (D-293 "0,155" doğru).

## 5. Bulunan kusurlar (gerekçeyi kırmaz ama yazılır)
1. **K0 figür zemin oranı 0,294** (v7a arena figüründe 0,0266 vs v35 0,0903): `65`'in K0_ORAN_ALT 0,5 "yetenek uyarısı" eşiğinin altında — bloklamaz (D-186: az görmek fail-closed yön) ama `oran_notu` boş yazılmış; uyarı JSON'a düşmemiş. 109'da da figur_zemin 0,044 (v35 0,151), kaplama67 0,417 (v35 0,508). Yani v7a arenada/otoparkta v35'ten belirgin **daha az zemin görüyor** — yetenek gerilemesi, emniyet değil.
2. Sentetik zincirde v7a **K3 1/255 (v35 0), K4 4/255 (v35 1), K6 7/255 (v35 5)** — üçü eşik altı ama üçü de v35'ten kötü yönde.
3. Gerçek karede v7a **FP 3/111 (v35 1/111)**: f218 (test), f129 ve f223 (val); f129 ve f223'te rota çizgisi tamamen etiketsiz/engel üstünde (yol_payi 0,0; f223'te 1 wp sınıf 1'de). v35 bu üç karede rota üretmiyor. Yeni "yol yokken yol" davranışı 2 karede vardır.
4. test29'da v7a **1 doğru rotayı kaybediyor** (f120; v35 yol 0,97). Kayıp 1, kazanç 9 — net lehte ama kayıp sıfır değil.
5. Ön kayıtlı kapı (b) geçilmedi: ROTA 8 < 10, MASKE_YOK 16 > 10 (v35 ile aynı körlük). Terfi gerekçesi ön kayıtlı eşiğe değil yanlış güzergâh oranına dayanıyor — bu bir ölçüm hatası değil, kullanıcının açıkça "kurala rağmen" verdiği karardır.

## 6. Hüküm
Ölçüm **doğru ve deterministik**; yeniden sayım ve yeniden koşum kayıtlı sayıların tamamını üretti. "Sahada v35'ten daha tehlikeli" iddiası için kanıt bulunamadı: rota üretilen karelerde sınıf-1 üstünde waypoint'li rota v35'te 9/21, v7a'da 3/38; v7a'nın 2 yeni "etiketsiz zemine rota" FP'si var ama v35'in kanal-üstü rotaları (196, 202, val 8 kare) kalkıyor. Çürütülemedi. Terfi engeli: HAYIR — ama madde 1–3 (görme yeteneği gerilemesi + 2 yeni etiketsiz-zemin FP'si) terfi kaydına yazılmalı.
