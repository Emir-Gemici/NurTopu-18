# LENS 2 — REFERANS MEŞRUİYETİ (v6 çürütme) · 2026-08-26

Varsayılan: aday terfi ETMEMELİ. Sonuç: **çürütülemedi** — referans değişimi v6'ya
adaya özgü avantaj sağlamıyor; ama kusurlar aşağıda.

## Koşulan komutlar (ham çıktılar bu klasörde)
- `kare_bazli_kiyas.txt`: tavan v1/v2 × v6 eski/yeni × v35 yeni, kare kare (venv python, json okuma).
- `140_uc_maske_araci.py goster/buyut` → `frame_000205_*`, `frame_000218_*`, `frame_000053_*`, `frame_000100_*`, `frame_000116_*` (taban vs yeni), `f205_solust_buyut.jpg`, `f205_sagust_buyut.jpg`, `f218_sagalt_buyut.jpg`.
- grep (model|v6|v35|fp|aday|rota|maske_yok) test29_referans/**/*.json → yalnız atama.json "_ne" ("MODEL CIKTISI GOSTERILMEZ") ve komut yolları; model çıktısı/FP/kare ipucu YOK.

## (1) Körlük
- Amele prompt'u (test29-referans-wf_93cfb1bd-112.js): model, FP, aday, v6/v35, 205/218 geçmiyor. Amele yalnız kare + taban maskesi görüyor. 29 karenin tamamı işlenmiş (6 grup × ≤5).
- rapor.json / denetim_*.json / *_ops.json: model ipucu yok (grep boş).
- **Kusur K1 (yön bias'ı):** prompt "önceki turda 'yol kare kenarına kadar çizilmemiş' diye eleştirildi" + izinli değişiklik (1) "kenara KADAR uzat". Bu, tavanda "rota yok → rota var" dönüşümünü (yani FP'nin düşmesini) teşvik eden tek yönlü bir talimattır; ON_KAYIT §10 bunu açıkça beklediğini yazmış ("FP'nin düşmesi beklenir"). Modelden bağımsız ve 29 kareye eşit uygulanmış; adaya özgü sızıntı değil.
- **Kusur K2 (ön kayıttan sapma):** ON_KAYIT §10 izinli değişiklikleri yalnız EKLEME (sınıf 0 uzat/ekle, sınıf 1 ekle) olarak yazdı; sınıf 0 SİLME izinli listede yok. Workflow'un denetçi prompt'u (a)/(c) ile sınıf 0 geri alma ekledi → 9 karede sınıf 0 azaldı (025, 039, 048 → 0,0; 053, 152, 160, 196, 202, 215 daralt). D amelesi rapor.json'da "silme izni yok" diye bırakmış, denetçi silmiş. Etkisi: 053 tavanı rota True→False. Ne v6 ne v35 053'te rota üretmediğinden TP/FP'ye etkisi 0. Yön: bu sapma tarlaya rota üreten adayı CEZALANDIRIR, v6'ya yaramaz.

## (2) Değişiklik yönü (fark.json)
- Sınıf 1: hiçbir karede azalmadı (0/29; 202'de +0,0001). geri_konan_px>0 olan 6 karede taban kırmızısı geri yüklenmiş.
- Sınıf 0 arttı: 14 kare; azaldı: 9 kare; aynı: 6.
- Tavan rota değişimi: 053 (1→0), 100 (0→1), 116 (0→1), 205 (0→1). Toplam 13 → 15.
- 205: sınıf 0 0,109 → 0,314 (tek poligon, x0–960 üst bant). **Gözle:** taban yeşili kanal boyunca ince şeritti; yeni poligon kanalın üstündeki geniş gri sıkıştırılmış toprak yolu kapsıyor. Büyütme (`f205_solust_buyut.jpg`): x 0–240'ta gri yol y=0 kenarına kadar sürüyor → üst uç bant teması GERÇEK. Sağ üst (`f205_sagust_buyut.jpg`): x 700–960, y 80–100 kuru ot/çiğ toprak poligona kısmen giriyor (madde 8/12 küçük ihlal) — rota var/yok hükmünü değiştirmez. **205'in FP'den çıkması yalnız referansın kenara/üst banda uzatılmasıyla; v6 çıktısı eski/yeni kümede birebir aynı (kare_bazli_kiyas: `eski==yeni True`).**
- 218: sınıf 0 0,148 → 0,153 (alt-sağ uç küçük poligon). **Gözle:** yol sol kenardan (y 40–240) alt-sağ kenara (x 820–930) diyagonal iner, alt kenara ulaşıyor; ÜST kenara ulaşmıyor → tavan hâlâ UC_BANT_TEMAS_YOK. v6 burada rota üretiyor; yolun üstündeki çiğ toprak şevi (x 0–600, y 0–200) geçmeden üst banda ulaşılamaz → FP gerçek görünüyor. FP olarak KALDI (doğru).

## (3) Eski vs yeni fark
- v6: eski tavanla TP 10 FP 2 FN 3 → yeni TP 11 FP 1 FN 4. Yeniden hesapladım (kare_bazli_kiyas.txt): aynı sayılar. Fark **yalnız 205**'ten (FP→TP); FN +1 = 100 ve 116 tavana girdi (v6 MASKE_YOK / ZEMIN_MASKESI_SUPHELI), 053 tavandan çıktı (−1 FN). 
- Eski referansta 205 "rota yok" (UC_BANT_TEMAS_YOK) YANLIŞTI: geniş gri yol üst kenara ulaşıyor, eski etiket yolun tam genişliğini çizmemişti.

## (4) v35 aynı biçimde ölçüldü mü
- `olcum_v35_ref2.log` + `v35_ref2_olcum.json`: aynı `142 --test-dizin v2 --tavan v2`, tavan_rota 15, TP 6 FP 0 FN 9. Kare kare: v35 FN 7→9 artışı 100 ve 116'dan (her ikisinde v35 MASKE_YOK; v6 de rota üretmiyor). 205'te v35 UC_BANT_TEMAS_YOK — referans değişiminden yalnız v6 kazandı çünkü yalnız v6 orada rota üretiyor; bu "avantaj" değil, gerçek yolun sayılmasıdır. Simetrik ölçüm.

## Ek kusurlar
- K3: `gece_v6_ref2_olcum.json` içinde `kapi_a.verdikt=null`, `a_gecti=false`, `terfi_adayi=false` — ref2 koşusunda 65_kabul KOŞULMADI (OLCULMEDI). (a) hükmü eski `gece_v6_v35taban_olcum.json`'a dayanıyor (aynı ağırlık; verdikt True, K1 257). Kayıtlı "terfi adayı" dosyası bunu söylemiyor.
- K4: FP=1 ≤ 1 tam sınırda; kapı tek bir karenin (205) referans yorumuna bağlı. Sıfır pay.
- K5 (ÖLÇÜLEMEDİ): TP tanımı "ikisi de rota üretti"; v6'nın 205'teki rotasının yol üstünde olup olmadığı ölçülmedi (126 çıktısında `olceksiz_yol` geometri değil sayı).
- K6: referans, v6 FP kareleri bilindikten SONRA tamamlandı (§10 kendisi yazıyor). Ameleler kör olsa da tasarımcı (mimar/başamele) kör değildi; tek yönlü "kenara uzat" talimatı bu bilgiyle yazıldı. Yapısal, kanıtlanabilir sızıntı YOK; ama bağımsız değil.

## Hüküm
Referans değişimi model-kör, sınıf 1 korunmuş, v35 aynı yordamla ölçülmüş; 205'teki tek dönüşüm gözle haklı. **Bu lens iddiayı çürütemedi.** Terfi engeli bu lensten çıkmıyor; K2/K3/K4 diğer lenslerle birlikte değerlendirilmeli.
