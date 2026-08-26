# v7a çürütme — LENS 3: EĞİTİM/REFERANS MEŞRUİYETİ (GPU YOK)

Tarih: 2026-08-26 · Aday: `codes/runs/segment/gece_v7a_v35taban/weights/best.pt` · Üretim: `models/navitas_seg_v35_best.pt`
Varsayılan: aday terfi ETMEMELİ. Ham çıktılar bu klasörde: `sizinti_kesisim.txt`, `sizinti_kesisim2.txt`, `sizinti_kesisim3.txt`, `denetim_ozet.txt`, `ek_kontroller.txt`.

## (1) Sızıntı — SONUÇ: sızıntı YOK (kanıtlı)

Komut: `O:\navitas-local-train\venv\Scripts\python.exe` ile stem kesişimi + md5 karşılaştırması (kod `sizinti_kesisim*.txt` başında).

| kontrol | sonuç |
|---|---|
| `dataset/dji_v7/images/{train,val}` = 413 / 73; etiket klasörleri birebir aynı stem kümesi | ✅ |
| `v7_kume.json` val_listesi (73) == disk val | ✅ |
| train ∩ val | **0** |
| train ∩ test29 · train ∩ val82 · val ∩ test29 · val ∩ val82 | **0 · 0 · 0 · 0** |
| uçuş ön eki (dji_v7 tümü) | yalnız `dji_20260822170832_0037_d` ve `dji_20260822173231_0039_d`; `_0038_` **yok** (`grep 0038`'in 3 vuruşu `frame_000038` idi — yanlış pozitif) |
| md5: dji_v7 train/val/x5 görüntüleri vs 0038_v3 test/val görüntüleri | **0 eşleşme** |
| md5: x5 kopyaları vs dji_v7 val | **0 eşleşme** |
| `dji_v7_x5/images/train` = 2065 = 413 × 5 (`__x00..__x04`); taban kümesi == train (413), val ile kesişim **0** | ✅ |
| x5 etiketleri kaynak etiketle bayt-eş (2065/2065); ilk 50 görüntü kaynakla md5-eş | ✅ |
| `karisim_gece_v7a.yaml` train: rescuenet 7004 + sentetik 5400 + copy_paste_t127 344 + dji_v7_x5 2065 = 14 813; DJI payı **%13,9** (ON_KAYIT §14 "≈2.430, ≈%16" — 486×5 tahminiydi; val ayrılınca 413×5; sapma belgesel, sızıntı değil) | not |

**Kusur (küçük, sızıntı değil):** dji_v7 **val 73 karesinin 71'i** train'deki bir kareyle ±1 kare komşu (aynı uçuş, ~1 sn ara). Erken durdurma/best-epoch (2/17, mAP50-95(M) 0,155) neredeyse train'in kopyası bir küme üzerinden seçildi. ON_KAYIT §14 bunu "yalnız erken durdurma için" diye açıkça kabul etmiş; 0038'e dokunulmadı → CONTRACTS §12 ihlali yok. Ama D-293 §1'deki "önceki best epoch 1 val artefaktıydı" cümlesinin dayanağı olan v7 val'i de bir artefakttır (train'e yapışık); "epoch 2 en iyidir" hükmü zayıf kanıttır.

## (2) Etiket kalitesi — SONUÇ: örneklem tutarlı; kusur küçük

- 7 denetçi raporu (`etiket_dalga4/denetim_*.json`): incelenen 40+40+40+40+40+40+37 = **277**, düzeltilen **41 (%14,8)**. Türler: (a) çim/ot/mera yeşile girmiş → geri alındı; (b) yol tam genişlik değil → uzatıldı; (d) beton kanal kırmızı değildi → eklendi; 1 adet S4 (köprü tabliyesi). Düzeltmeler ops.json'a yazılıp `140 uret` ile yeniden üretilmiş, 40/40 `_uc.png` {0,1,2} doğrulanmış (raporlarda yazılı; dosya düzeyinde ben yeniden koşmadım — **ÖLÇÜLMEDİ**).
- Denetim ikinci tur YOK: düzeltmelerin kendisi bir başka denetçi tarafından görülmedi (tek geçişli denetim). Kusur olarak kayda geçer, kanıtlanmış hata değil.
- **6 boş etiket** (0 byte; tümü train, 0037 f21/f23/f25/f26/f28/f46): iki bindirme GÖRÜLDÜ (`D4_01/...f21`, `D4_54/...f46`): iş makinesi izli sürülmüş toprak/moloz; yol yok. Boş etiket = YOLO'da tamamen arka plan → madde 12 ile tutarlı (çiğ toprak sınıf 0 yapılmaz). f46'da sıkıştırılmış gri şerit (x 440–660) tartışmalı ama etiketsiz bırakmak muhafazakâr yön; kabul.
- **10 rastgele bindirme GÖRÜLDÜ** (tohum 20260826; liste `ek_kontroller` üstü, çıktıda): 0039 f134, 0037 f282, 0039 f12, 0037 f262, 0039 f172, 0039 f95, 0039 f4, 0037 f234, 0039 f142, 0039 f153. Hepsinde: beton kanal/oluk → kırmızı (İlke A), ana yol tam genişlik yeşil, sürülmüş tarla/mera etiketsiz, insan/direk/bitki kırmızı. Tutarsızlık bulunmadı. Küçük ihtiyat: 0039 f12'de yol y 350–460 arasında yeşil kesik (toprak rampa) — muhafazakâr, güvenli yön.
- Sınıf dağılımı (dji_v7 486 kare): sınıf 1 poligon 1852, sınıf 0 poligon 1221; sınıf 0 içermeyen kare 7 (6 boş + 1). Sınıf 1 vurgusu (kanal) eğitime gerçekten girmiş.

## (3) Karşılaştırma adaleti — SONUÇ: AYNI YOL, AYNI REFERANS, AYNI TAVAN

`gece_v7a_olcum.json` / `v35_ref3_olcum.json` (test29) ve `gece_v7a_val82_olcum.json` / `sizinti/val82_v35_olcum.json` (val82) alan alan karşılaştırıldı:

| alan | v35 | v7a |
|---|---|---|
| test_dizin | `dji_kirsal_0038_bolum_v3/images/test` (29) · `/val` (82) | aynı |
| tavan | `test29_etiket_tavani_v3.json` (tavan_rota 12) · `sizinti/val82_etiket_tavani.json` (43) | aynı |
| rota_yol etiket_dizin | `labels/test` · `labels/val` | aynı |
| kapı sabitleri | yol_payi ≥ 0,90, engel_wp ≤ 0 | aynı |
| 126 koşumu | `kare: 29/82 · model: 1 · imgsz 512` | aynı |
| kabul zinciri kümesi parmak izi | sha256:604c03…0586 (n=547) | aynı |

Koşum koşulu farkı **bulunmadı**. `sizinti/olcum.json` içindeki v35 val82 sayıları (rota 15 / yanlış 10 / FP 0) `val82_v35_olcum.json` ile birebir. D-293 tablosu (v35 21/15, v7a 38/7) JSON'lardan yeniden toplandı: v35 test29 6 rota/5 yanlış + val82 15/10 = 21/15 ✅; v7a 8/0 + 30/7 = 38/7 ✅; FP v7a 1+2 = 3 ✅.

**Kusur (yordamsal):** test29/val82, 2026-08-20'den bu yana **8 aday** (v2…v7b, ref2/ref3) üzerinde tekrar tekrar ölçüldü ve kapı tanımı (b-ek, b-ek2/K6) v35'in bu kümedeki hataları görüldükten SONRA eklendi (D-289 → §12). Eşikler ön kayıtlı ama küme artık "hiç görülmemiş" değil; 0038 ile ilgili öğrenilen bilgi (beton kanal = engel) dalga 4 etiket vurgusuna (§14 "vurgu: beton kanal → sınıf 1") girdi. Piksel sızıntısı yok; **bilgi sızıntısı** var ve yazılı değil. Terfi gerekçesindeki "yanlış güzergâh 15 → 7" iyileşmesinin bir kısmı, tam olarak bu kümede gözlenen hata tipine yönelik etiketleme olduğundan, başka sahaya genellenmesi kanıtlanmamıştır (D-287 "çeşitlilik" hükmüyle uyumlu; §15 buna değinmiyor).

## (4) Kullanıcı kararının defter metni — SONUÇ: eşik listesi doğru; "hiçbir eksende kötü değil" cümlesi YANLIŞ

Ön kayıt (§4(b), eğitim öncesi): "**Sayısal terfi eşiği: ROTA ≥ 10/29 ve MASKE_YOK ≤ 10/29.** Bu satır eğitim başlamadan yazıldı ve değişmez." §14: "(b) test29 (uzlaşı v3): ROTA ≥ 10, MASKE_YOK ≤ 10, FP ≤ 1, **YANLIŞ GÜZERGÂH = 0**". §4(d): "'Az farkla kaçırdı, verelim' **YAPILMAZ**."

Ölçülen (gece_v7a_olcum.json `kapi_b`): `rota_test29>=10 = False` (8) · `maske_yok_test29<=10 = False` (16) · `FP_test29<=1 = True` (1) · `yanlis_guzergah==0 = True` (0). `kapi_a`: hepsi True (K1 255, red67 0, çatı 0,023). `b_gecti = False`, `terfi_adayi = False`.
⇒ §15'teki "geçilmedi: ROTA ≥ 10 (8), MASKE_YOK ≤ 10 (16); geçilen: (a) tam, FP ≤ 1, YANLIŞ 0" listesi **doğru**. MASKE_YOK 16 = v35 ile **aynı** (iyileşme yok).

**§15'in "v7a hiçbir ölçülen eksende v35'ten kötü değil" cümlesi kayıtlı sayılarla ÇELİŞİYOR** (hepsi kapı içinde, ama "kötü değil" yanlış):

| eksen | v35 | v7a | kaynak |
|---|---:|---:|---|
| sentetik K1 rota | 256/260 | 255/260 | t63 `k6_v35` / `gece_v7a` kabul_verdikt |
| sentetik K3 ağır basma | **0** | **1** (sa_000190, basma 0,063, 2 wp engel üstünde) | aynı |
| sentetik K4 arena dışı | **1**/256 | **4**/255 (sa_13, 54, 76, 90: rota **tamamen** arena dışı, yol_payi 0,00) | aynı |
| sentetik K6 yanlış güzergâh | 5/256 (%1,95) | 7/255 (%2,75) | aynı |
| val82 FP (tavan rota üretmezken model rota) | **0** | **2** (f129: yol 0,00 etiketsiz 1,00; f223) | val82 olcum.json |
| 67 gerçek karede kaplama medyanı | 0,508 | 0,417 | k109 |
| figür/zemin oranı | 0,151 | 0,044 | k109 |

Sahaya bakan iki kalem: **K4 4 rota tamamen arena dışında** (v35'te 1) ve **val82'de 2 yeni FP** (referansa göre yolu olmayan karede rota; f129 rotası %100 etiketsiz zemin üstünde) — şartnamede "yanlış güzergâh = 0 puan" tam bu durumdur; §15 yalnız yol_payi-kapısı yanlışlarını sayıyor, FP'yi "yanlış güzergâh" saymıyor. 111 karede yanlış-rota toplamı (yanlış güzergâh + FP): v35 15+1 = 16/21, v7a 7+3 = 10/38 — oran yine v7a lehine (%76 → %26), ama "hiçbir eksende kötü değil" savı düşer.

**Anayasa/madde kapsamı:** madde 15 (serbest alan otoritesi; nesne katmanı yalnız çıkarır) bir **kod/işlem** kuralıdır; model ağırlığı değişimi bu maddeyi ihlal etmez (kabul zinciri K0–K6 korundu) → §15'in "anayasa ihlali yok" cümlesi doğru. D-133 "sevk insanındır" atfı doğru (insan kararı). "Kural dışı" ifadesinin doğru kapsamı: **ON_KAYIT §4(b)/§4(d)/§14 ön kayıt eşiklerinin ve CONTRACTS §12 "terfi için … ROTA ≥ 10/29, MASKE_YOK ≤ 10/29" cümlesinin kullanıcı kararıyla aşılması**; CONTRACTS §12'nin bu satırı **güncellenmeli ya da istisna açıkça yazılmalı** — aksi hâlde sözleşme ile registry çelişir (madde 16). Deftere yazılacak metin en az şunları içermeli: "ön kayıtlı ROTA ≥ 10 ve MASKE_YOK ≤ 10 geçilmedi (8/16; MASKE_YOK v35 ile aynı); sentetik K3/K4/K6 ve val82 FP v35'ten bir miktar kötü, kapı içinde; terfi kullanıcı kararı, §4(d) 'az farkla kaçırdı' yasağına istisna".

## Hüküm

- Sızıntı: yok (kanıt: kesişim 0, md5 0, uçuş öneki 0038 yok).
- Etiket: örneklemde tutarlı; boş 6 etiket madde 12'ye uygun; tek turlu denetim.
- Karşılaştırma: adil (aynı 126/142 yolu, aynı v3 referans, aynı tavan, aynı etiket dizini).
- Karar metni: eşik listesi doğru; **"hiçbir eksende kötü değil" yanlış** (K3 0→1, K4 1→4, K6 5→7, val82 FP 0→2, kaplama67 0,51→0,42).
- ÖLÇÜLMEDİ (GPU yok): v7a'nın engel→zemin sızıntı payı (sizinti/olcum.json'da yalnız v35/v3/v6 var); v7a FP karelerinin (val82 f129/f223) ve K4 arena-dışı 4 sentetik karenin görsel doğrulaması — `olcum`/`guvenlik` lensine düşer.

**curutuldu: true** (gerekçedeki bir sav çürüdü) · **terfi_engeli: false** — bu lensin bulguları ölçümün yanlışlığını ya da sahada v35'ten daha tehlikeli olduğunu KANITLAMIYOR; K4/FP artışı n küçük ve kapı içinde, görsel doğrulaması bu lensin dışında. Kullanıcı, §15 metnini düzelterek karar verebilir.
