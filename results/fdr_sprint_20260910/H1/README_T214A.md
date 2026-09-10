# H1 · T214-A — Ölçüm zinciri: K3 (mozaik 512 / üretim boru hattı), K5 (gt / model / uretim), K6 süreler ve grafikler

> **SENTETİK** (D-441 d): MuJoCo simülasyonu; saha kanıtı değildir. **ÖLÇÜLEMEDİ ≠ GEÇTİ**; eşikler ön kayıttan (`results/fdr_sprint_20260910/ON_KAYIT.md` H1-K3/K4/K5/K6) ve **gevşetilmedi**. Üretim modeli v36 (`sha 1d1caca6f6da…`, kayıt defteriyle eş: 90/90 ölçüm) **değişmedi**; sim'e özel eğitim YOK. Bu belge `simulation/mujoco/t214a_rapor.py` ile JSON'lardan üretilir, elle düzenlenmez (nöbetçi: `tests/test_sim_mujoco_olcum.py::G_Readme`).
> Özet tarihleri: koşum `2026-09-10 16:36` · K3 üretim boru hattı `2026-09-10 15:31`.

## 0. Sonuç tablosu

| kapı | ölçüm | eşik (ön kayıt) | hüküm |
|---|---|---|---|
| H1-K3 · mozaik zinciri (`iha_haritala`, çıkarım imgsz **512** kayıt defterinden, tohum 42) | rota bulundu 6/15 · **doğru etiket 6/15** · yanlış 0 · güven kapısı sonrası yayımlanan doğru OPEN_ROUTE 5/15 | ≥ 12/15 | **DÜŞTÜ** |
| H1-K3 · üretim kare-bazlı boru hattı (`rpi_inference.run_camera` dosya kaynağı, kerteriz beslemesi, tohum 42) | **doğru (ön kayıt) 1/15** · OPEN_ROUTE yayını olan harita 5 · yanlış yol yayını olan 4 | ≥ 12/15 | **DÜŞTÜ** |
| H1-K4 · aktarım (gt kolu) | OPEN_ROUTE ACK [ika,yks] 45/45 · IKA_GO ACK 45/45 · harita 15 | 15/15 | **GEÇTİ** |
| H1-K5 · YER GERÇEĞİ (gt) | başarı **45/45** · harita (3/3 tohum) **15/15** | ≥ 12/15 harita × 3 tohum | **GEÇTİ** |
| H1-K5 · ÜRETİM MODELİ · mozaik zinciri (model) | başarı **9/45** · harita (3/3 tohum) **0/15** | ≥ 12/15 harita × 3 tohum | **DÜŞTÜ** |
| H1-K5 · ÜRETİM BORU HATTI · kare-bazlı (uretim) | başarı **0/15** · harita (3/3 tohum) **0/15** (yalnız K3'te OPEN_ROUTE üreten 5 harita koşuldu; kalan 10 harita NO_ROUTE → başarısız sayılır) | ≥ 12/15 harita × 3 tohum | **DÜŞTÜ** |
| H1-K6 · sanal görev süresi + grafikler | koşum tablosu §9 (105 koşum) · grafik 4/4 (SVG + PNG) | 45 koşum tablo + 4 grafik | **ÜRETİLDİ** |

Başarı tanımı (K5, TEK tanım `gorev_kosumu.basari_hesapla`): çıkış 0 ∧ rota bulundu ∧ HB 2×2 m karesi içinde ∧ temas 0 ∧ sürüş ≤ 600 s (sim saati).

## 1. H1-K3 — mozaik zinciri (`iha_haritala`, imgsz kayıt defterinden)

D-441 (a): çıkarım boyu `config/model_registry.json` etkin profilinden okunur (`iha_haritala.INFER_SIZE`, `cikarim_boyu()`; eskiden `_infer(..., MOZ_PX=1024)` çıplaktı). Mozaik tuvali 1024 px'te kalır, maskeler en-yakın-komşu ile tuvale büyütülür (costmap/MPP/tohum geometrisi değişmez). HB tohumu 0 (üretim; D-441 b). Her koşum kendi taramasını render eder (GPU render kareleri ~%50 bayt-eş — tohum 42 taraması K3 üretim hattının taramasıyla aynı dosya değildir).

| harita | senaryo | açık yol | zincir durumu | rota yolu | doğru | güven | darboğaz m | tel tipi | başarı |
|---|---|---|---|---|---|---|---|---|---|
| 1 | kolay | 1 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 1 | orta | 2 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 1 | zor | 3 | BELIRSIZ_COKLU | — | ✗ | — | — | NO_ROUTE | ✗ |
| 2 | kolay | 1 | ACIK | 1 | ✓ | 1.000 | 2.492 | OPEN_ROUTE | ✓ |
| 2 | orta | 1 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 2 | zor | 3 | ACIK | 3 | ✓ | 0.141 | 1.255 | NO_ROUTE | ✗ |
| 3 | kolay | 3 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 3 | orta | 2 | ACIK | 2 | ✓ | 0.937 | 2.131 | OPEN_ROUTE | ✓ |
| 3 | zor | 1 | ACIK | 1 | ✓ | 1.000 | 2.234 | OPEN_ROUTE | ✓ |
| 4 | kolay | 3 | BELIRSIZ_TEK_KAPI | — | ✗ | — | — | NO_ROUTE | ✗ |
| 4 | orta | 3 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 4 | zor | 1 | BELIRSIZ_TEK_KAPI | — | ✗ | — | — | NO_ROUTE | ✗ |
| 5 | kolay | 3 | KAPALI_DAR | — | ✗ | — | — | NO_ROUTE | ✗ |
| 5 | orta | 3 | ACIK | 3 | ✓ | 0.891 | 2.080 | OPEN_ROUTE | ✓ |
| 5 | zor | 2 | ACIK | 2 | ✓ | 0.703 | 1.873 | OPEN_ROUTE | ✓ |

| tohum | rota bulundu | doğru etiket | yanlış etiket | güven kapısı reddi (conf < 0,20 → NO_ROUTE) | yayımlanan doğru OPEN_ROUTE | sürüş başarısı |
|---|---|---|---|---|---|---|
| 42 | 6/15 | 6/15 | 0 | 1 | 5/15 | 5/15 |
| 43 | 1/15 | 1/15 | 0 | 0 | 1/15 | 1/15 |
| 44 | 3/15 | 3/15 | 0 | 0 | 3/15 | 3/15 |

Karşılaştırma (aynı zincir, **imgsz 1024**, ayrı render; `results/fdr_sprint_20260910/H1/k3b/v1_15harita_yerlesim_d441.json`, D-441 ek): rota 7/15, doğru 7/15. İki ölçüm aynı tarama kareleri üzerinde değildir; fark çıkarım boyu ile render değişkenliğini birlikte içerir.

## 2. H1-K3 — üretim kare-bazlı boru hattı (D-441 c)

Zincir (üretim kodu DEĞİŞTİRİLMEDEN, `simulation/mujoco/sim_karar_toplayici.py`): tarama kareleri (`scan_%05d` + `poses.csv`) → `rpi_inference.run_camera(kaynak=<dosya dizisi>, ekransiz=True)` = `--camera --kaynak` kipi (`kamera_kaynagi_coz` → dosya) → letterbox → v36 (imgsz 512) → `get_masks` → `kare_olcek_kahini` (Katman 1: `CanliOlcekSaglayici` ← sim irtifası `poses.csv` z, FOV sim kamerası) → `analyze_path` (Katman A/B, HB tespiti) → `_rota_kararini_esikle` → `KararYumusatici` (D-396) → `KararYayinci` → UDP (ephemeral) → `IkaReceiver` (İKA ucu, gerçek alıcı) + YKS dinleyicisi (ACK). Kamera köprüsü (MJPEG) atlanır; kare döngüsü üretimdir. **Kerteriz beslemesi (BİRİNCİL):** kare poz yaw'ına göre çeyrek tur döndürülerek (np.rot90, kayıpsız) kuzey-yukarı (KB→HB yukarı) verilir — üretim `analyze_path` rotayı ALT→ÜST arar, `run_camera` eksen parametresi geçirmez; döndürme SİM TARAFINDADIR. **Ham** besleme TEŞHİS'tir (kapı değil).

Hüküm tanımı (ön kayıt, toplayıcı modül başı): dogru = İKA ucuna ≥ 1 OPEN_ROUTE ulaştı ∧ ulaşan her OPEN_ROUTE'un yolu açık yol (yanlış yol yayını 0).

| harita | senaryo | açık yol | OPEN_ROUTE kareleri (kare: yayınlanan etiket → dünyada izlenen yol) | yanlış etiket yayını | dünya yolu doğru OR var | son yayın | NO_ROUTE sebepleri (ilk 3) | hüküm (ön kayıt) |
|---|---|---|---|---|---|---|---|---|
| 1 | kolay | 1 | k9: 2→1 · k15: 1→1 | 1 | ✓ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 18, ZEMIN_MASKESI_SUPHELI 9, MASKE_YOK 7 | ✗ |
| 1 | orta | 2 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 16, ZEMIN_MASKESI_SUPHELI 8, MASKE_YOK 7 | ✗ |
| 1 | zor | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 18, ZEMIN_MASKESI_SUPHELI 9, MASKE_YOK 7 | ✗ |
| 2 | kolay | 1 | k9: 2→1 | 1 | ✓ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 15, MASKE_YOK 9, ZEMIN_MASKESI_SUPHELI 9 | ✗ |
| 2 | orta | 1 | k15: 1→1 | 0 | ✓ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 19, ZEMIN_MASKESI_SUPHELI 8, MASKE_YOK 7 | ✓ |
| 2 | zor | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 18, ZEMIN_MASKESI_SUPHELI 10, MASKE_YOK 7 | ✗ |
| 3 | kolay | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 17, ZEMIN_MASKESI_SUPHELI 9, MASKE_YOK 6 | ✗ |
| 3 | orta | 2 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 14, ZEMIN_MASKESI_SUPHELI 10, MASKE_YOK 8 | ✗ |
| 3 | zor | 1 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 19, ZEMIN_MASKESI_SUPHELI 8, MASKE_YOK 7 | ✗ |
| 4 | kolay | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 15, ZEMIN_MASKESI_SUPHELI 10, MASKE_YOK 7 | ✗ |
| 4 | orta | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 17, ZEMIN_MASKESI_SUPHELI 9, MASKE_YOK 8 | ✗ |
| 4 | zor | 1 | k9: 2→1 | 1 | ✓ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 17, MASKE_YOK 8, ZEMIN_MASKESI_SUPHELI 8 | ✗ |
| 5 | kolay | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 18, MASKE_YOK 8, ZEMIN_MASKESI_SUPHELI 8 | ✗ |
| 5 | orta | 3 | — | 0 | ✗ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 19, ZEMIN_MASKESI_SUPHELI 10, MASKE_YOK 7 | ✗ |
| 5 | zor | 2 | k9: 3→2 · k15: 2→2 · k20: 1→2 | 2 | ✓ | NO_ROUTE MASKE_YOK | UC_BANT_TEMAS_YOK 17, ZEMIN_MASKESI_SUPHELI 9, MASKE_YOK 6 | ✗ |

- **kerteriz**: doğru (ön kayıt) **1/15** · OPEN_ROUTE yayını olan harita 5 · yanlış yol yayını olan 4 · ilk OPEN_ROUTE doğru 1 · son OPEN_ROUTE doğru 2 · son yayın NO_ROUTE 15/15 · OPEN_ROUTE kare 8/585 · hizalı 15/15 · ACK eksik 0.
  TEŞHİS (hüküm dışı): OPEN_ROUTE karelerinin **8/8**'i dünyada açık yolu izliyor, yayınlanan etiket = dünya yolu 3/8; dünya yolu doğru OPEN_ROUTE'u olan harita 5/15; KB ile HB **aynı karede: 0/225** tarama-bacağı karesi (KB karede 105, HB karede 90); kare kaydı ↔ İKA ucu OPEN_ROUTE sayısı tutarlı 15/15.
- **ham**: doğru (ön kayıt) **0/15** · OPEN_ROUTE yayını olan harita 1 · yanlış yol yayını olan 1 · ilk OPEN_ROUTE doğru 0 · son OPEN_ROUTE doğru 0 · son yayın NO_ROUTE 15/15 · OPEN_ROUTE kare 1/585 · hizalı 15/15 · ACK eksik 0.
  TEŞHİS (hüküm dışı): OPEN_ROUTE karelerinin **1/1**'i dünyada açık yolu izliyor, yayınlanan etiket = dünya yolu 0/1; dünya yolu doğru OPEN_ROUTE'u olan harita 1/15; KB ile HB **aynı karede: 0/225** tarama-bacağı karesi (KB karede 105, HB karede 90); kare kaydı ↔ İKA ucu OPEN_ROUTE sayısı tutarlı 15/15.

| NO_ROUTE sebebi (kare) | kerteriz | ham |
|---|---|---|
| UC_BANT_TEMAS_YOK | 257 | 238 |
| ZEMIN_MASKESI_SUPHELI | 134 | 194 |
| MASKE_YOK | 109 | 116 |
| HEDEF_YOK | 60 | 35 |
| GORUS_HATTI_KOPUK | 17 | 0 |

**İki koşu (aynı tarama kareleri):** ilk koşu (`kosum_tur3.sh`, 12:39–12:43) ↔ devam koşusu — 30 harita·besleme, 1170 kare, kare kararı farkı **0** (`k3_uretim_boru/iki_kosu_karsilastirma.json`; karar izi `kosu1_karar_izi.json`, ilk özet `kosu1_ozet_k3_uretim.json`).

## 3. H1-K4 — aktarım (tel tipinden sayım, `gorev_kosumu.tel_tipi`)

| kaynak | n | OPEN_ROUTE yayını (tel) | ACK [ika,yks] | NO_ROUTE yayını (tel) | ACK [ika,yks] | güven kapısı reddi | IKA_GO ACK | link kaybı olan |
|---|---|---|---|---|---|---|---|---|
| gt | 45 | 45 | 45 | 0 | 0 | 0 | 45 | 0 |
| model | 45 | 9 | 9 | 36 | 36 | 1 | 9 | 0 |
| uretim | 15 | 12 | 12 | 3 | 3 | 0 | 12 | 0 |

Not: `send_open_route` güven eşiği (0,20) altındaki rotayı NO_ROUTE(DUSUK_GUVEN) olarak gönderir (CONTRACTS §6.3, K-B). İlk koşunun ham `iha_gonderim.tip` alanı ÇAĞRILAN yöntemi yazıyordu; sayım hakem kaydından (TEL) yapılır (§6.3).

## 4. H1-K5 — İKA otonom sürüş (MuJoCo fizik, `ika_nav` + `MuJoCoSurucu`, sim saati)

| kaynak | n | rota bulundu | rota doğru | OPEN_ROUTE (tel) | IKA_GO ACK | HB içinde | temas var | süre aşımı (kod 4) | **BAŞARI** | harita (3/3 tohum) | eşik |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gt | 45 | 45 | 45 | 45 | 45 | 45 | 0 | 0 | **45/45 (1.0)** | 15/15 | ≥ 12/15 |
| model | 45 | 10 | 10 | 9 | 9 | 9 | 0 | 0 | **9/45 (0.2)** | 0/15 | ≥ 12/15 |
| uretim | 15 | 12 | 3 | 12 | 12 | 0 | 12 | 12 | **0/15 (0.0)** | 0/5 | ≥ 12/15 |

| kaynak | senaryo | n | başarı | HB içinde | temas var |
|---|---|---|---|---|---|
| gt | kolay | 15 | 15 | 15 | 0 |
| gt | orta | 15 | 15 | 15 | 0 |
| gt | zor | 15 | 15 | 15 | 0 |
| model | kolay | 15 | 4 | 4 | 0 |
| model | orta | 15 | 2 | 2 | 0 |
| model | zor | 15 | 3 | 3 | 0 |
| uretim | kolay | 6 | 0 | 0 | 6 |
| uretim | orta | 3 | 0 | 0 | 1 |
| uretim | zor | 6 | 0 | 0 | 5 |

Harita düzeyi (başarılı tohum / koşulan tohum):

| harita_senaryo | gt | model | uretim |
|---|---|---|---|
| 1_kolay | 3/3 | 1/3 | 0/3 |
| 1_orta | 3/3 | 0/3 | — |
| 1_zor | 3/3 | 0/3 | — |
| 2_kolay | 3/3 | 2/3 | 0/3 |
| 2_orta | 3/3 | 0/3 | 0/3 |
| 2_zor | 3/3 | 0/3 | — |
| 3_kolay | 3/3 | 0/3 | — |
| 3_orta | 3/3 | 1/3 | — |
| 3_zor | 3/3 | 1/3 | — |
| 4_kolay | 3/3 | 1/3 | — |
| 4_orta | 3/3 | 0/3 | — |
| 4_zor | 3/3 | 1/3 | 0/3 |
| 5_kolay | 3/3 | 0/3 | — |
| 5_orta | 3/3 | 1/3 | — |
| 5_zor | 3/3 | 1/3 | 0/3 |

Karşılaştırma: T213-B (`results/fdr_sprint_20260910/H1/kosum/ozet_kosum.json`, **eski yerleşim**, D-441 öncesi) YER GERÇEĞİ 33/45, harita 10/15 — yeni yerleşim (açık yol koridoru ≥ 1,45 m engelsiz) ile 45/45, harita 15/15. Sürücü ve kontrol kodu değişmedi.

**Üretim boru hattıyla sürüş (uretim):** İKA'ya İKA ucuna ulaşan SON OPEN_ROUTE verilir; üretimde `ref_xy` daima [0,0] ve İKA SAF ÖTELEME yapar (CONTRACTS §3.2/§6.5) → rotanın ilk noktası İKA'nın bulunduğu KB sayılır. `ankor KB` = rotanın pozdan hesaplanan gerçek başlangıcının KB'ye uzaklığı (TEŞHİS).

| harita | senaryo | tohum | OPEN_ROUTE (son etiket) | doğru | son OR dünya yolu | ankor KB m | rota sonu → HB m | KB–HB aynı kare | kod | temas | varış m | takip maks m | başarı |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | kolay | 42 | 1 | ✓ | 1 | 18.11 | 1.37 | 0 | 4 | 5024 | 38.52 | 5.03 | ✗ |
| 1 | kolay | 43 | 1 | ✓ | 1 | 17.87 | 1.37 | 0 | 4 | 7179 | 38.52 | 4.71 | ✗ |
| 1 | kolay | 44 | 2 | ✗ | 1 | 15.82 | 1.25 | 0 | 4 | 7462 | 38.52 | 4.66 | ✗ |
| 2 | kolay | 42 | 2 | ✗ | 1 | 18.46 | 0.86 | 0 | 4 | 7 | 39.79 | 5.13 | ✗ |
| 2 | kolay | 43 | 2 | ✗ | 1 | 18.39 | 0.93 | 0 | 4 | 10 | 39.77 | 5.05 | ✗ |
| 2 | kolay | 44 | 2 | ✗ | 1 | 18.32 | 1.32 | 0 | 4 | 10 | 39.77 | 5.05 | ✗ |
| 2 | orta | 42 | 1 | ✓ | 1 | 20.19 | 1.08 | 0 | 4 | 12839 | 35.66 | 9.05 | ✗ |
| 2 | orta | 43 | — | ✗ | — | — | — | 0 | 2 | 0 | 44.71 | — | ✗ |
| 2 | orta | 44 | — | ✗ | — | — | — | 0 | 2 | 0 | 44.71 | — | ✗ |
| 4 | zor | 42 | 2 | ✗ | 1 | 17.80 | 0.89 | 0 | 4 | 3 | 40.61 | 5.75 | ✗ |
| 4 | zor | 43 | — | ✗ | — | — | — | 0 | 2 | 0 | 45.22 | — | ✗ |
| 4 | zor | 44 | 2 | ✗ | 1 | 17.63 | 1.12 | 0 | 4 | 11 | 40.04 | 6.77 | ✗ |
| 5 | zor | 42 | 1 | ✗ | 2 | 6.90 | 0.96 | 0 | 4 | 74 | 31.37 | 4.18 | ✗ |
| 5 | zor | 43 | 1 | ✗ | 2 | 7.38 | 0.79 | 0 | 4 | 7607 | 31.70 | 4.72 | ✗ |
| 5 | zor | 44 | 1 | ✗ | 2 | 7.38 | 0.79 | 0 | 4 | 2704 | 40.24 | 3.80 | ✗ |

Ankor KB uzaklığı (uretim, OPEN_ROUTE alan koşumlar): n=12 · min 6.9 · medyan 17.84 · ort 15.35 · maks 20.19 m.

Kesilen ilk koşu (`kosum_tur3/kesilen_kosu/`, 6 koşum, 12:57–12:59, kullanım kredisi bitince yarıda kaldı): başarı 0/6, ankor KB n=6 · min 15.82 · medyan 18.21 · ort 17.83 · maks 18.46 m. Devam koşusu 15 koşumun hepsini tek kod sürümüyle yeniden koştu (üstteki tablo); ilk koşu silinmedi.

## 5. H1-K6 — sanal görev süresi, takip hatası, varış

Süreler SİM SAATİ (`MjData.time`, ON_KAYIT §5.3); İHA kolu kinematik profil süresidir (aerodinamik yok); haritala/çıkarım hesap süresi sim saatine eklenmez. Takip hatası: sürüş boyunca her `bekle()` adımında İKA konumu → arena AÇIK YOL merkez hattı uzaklığı, **ilk temastan önce** (`takip_hatasi_*`); `plan_takip_*` = komut edilen rotaya uzaklık (sürücü hatasını planlayıcı sapmasından ayırır).

| kaynak | İKA sürüş sim-s (başarılı) | toplam görev sim-s (başarılı) | takip maks m (sürülen) | takip maks m (başarılı) | plan takip maks m | varış m (hepsi) |
|---|---|---|---|---|---|---|
| gt | n=45 · min 64.1 · medyan 71.3 · ort 77.3 · maks 98.4 | n=45 · min 101.3 · medyan 108.6 · ort 114.5 · maks 135.7 | n=45 · min 0.24 · medyan 0.498 · ort 0.475 · maks 0.563 | n=45 · min 0.24 · medyan 0.498 · ort 0.475 · maks 0.563 | n=45 · min 0.161 · medyan 0.5 · ort 0.441 · maks 0.563 | n=45 · min 0.1 · medyan 0.2 · ort 0.2 · maks 0.2 |
| model | n=9 · min 63.4 · medyan 67.6 · ort 69.4 · maks 88.5 | n=9 · min 100.7 · medyan 104.9 · ort 106.7 · maks 125.8 | n=9 · min 0.975 · medyan 1.564 · ort 1.517 · maks 2.367 | n=9 · min 0.975 · medyan 1.564 · ort 1.517 · maks 2.367 | n=9 · min 0.146 · medyan 0.241 · ort 0.249 · maks 0.38 | n=45 · min 0.2 · medyan 44.7 · ort 36.0 · maks 45.8 |
| uretim | — | — | n=12 · min 3.802 · medyan 5.041 · ort 5.325 · maks 9.048 | — | n=12 · min 0.055 · medyan 0.138 · ort 0.137 · maks 0.218 | n=15 · min 31.4 · medyan 39.8 · ort 39.3 · maks 45.2 |

Grafikler (`simulation/mujoco/sim_grafik.py`, JSON'dan; nöbetçi `tests/test_sim_mujoco_olcum.py::F`):

- `FDR/sekiller/sim_basari_orani.svg` · `.png` — başarı oranı — rota kaynağı × seviye (çubuk). Veri: `results/fdr_sprint_20260910/H1/kosum_tur3/ozet_kosum.json` (kaynaklar.<k>.senaryo, harita düzeyi); alt başlıkta K3: model koşum JSON'ları (tohum 42) ve `results/fdr_sprint_20260910/H1/k3_uretim_boru/ozet_k3_uretim.json`.
- `FDR/sekiller/sim_gorev_suresi.svg` · `.png` — görev süresi dağılımı — sürüş ve toplam görev, sim s (kutu + nokta). Veri: `results/fdr_sprint_20260910/H1/kosum_tur3/<kaynak>_<h>_<lv>_<tohum>.json` (sure_sim_ika, sure_sim_gorev; basari=True).
- `FDR/sekiller/sim_takip_hatasi.svg` · `.png` — takip hatası (ilk temastan önce) ve varış mesafesi (kutu + nokta). Veri: `results/fdr_sprint_20260910/H1/kosum_tur3/<kaynak>_<h>_<lv>_<tohum>.json` (takip_hatasi_maks_m, varis_mesafesi_m).
- `FDR/sekiller/sim_sistem_tepkileri.svg` · `.png` — sistem tepkileri — OPEN_ROUTE/NO_ROUTE/ACK/IKA_GO/temas olay sayıları. Veri: `results/fdr_sprint_20260910/H1/kosum_tur3/ozet_kosum.json` (kaynaklar.<k>.olaylar; tel tipinden).

## 6. Bulgular (kanıtlı; üretim kodu DEĞİŞTİRİLMEDİ — karar mimarın)

1. **Üretim yol etiketi KARE-GÖRELİ.** `analyze_path` → `_rota_serit_olcumu` → `karar_sozlesmesi.rota_serit_karari`: `road` rotanın gövdesinin karenin genişliğinin hangi üçte birinde olduğundan okunur. Tarama kareleri HTAB'a ortalanmadığında (bacaklar x = −18/−6/+6/+18 m) etiket dünyadaki yoldan ayrışır: kerteriz OPEN_ROUTE karelerinde yayınlanan etiket = dünya yolu **3/8**, rota dünyada açık yolu izliyor **8/8**. Ön kayıtlı hüküm yayınlanan etiketle kurulur (İKA'nın aldığı değer) ve DEĞİŞMEDİ; teşhis, K3 düşüşünün bir kısmının algıdan değil etiket semantiğinden geldiğini gösterir. Sahada kare HTAB'a ortalanmazsa aynı sapma beklenir (ÖLÇÜLMEDİ).
2. **Tek kare KB ile HB'yi birlikte görmüyor → üretim rotası KB'ye ankorlanamıyor.** Sim arenasında KB–HB 44.5–45.8 m; sim kamerası 30 m'de 45,6 m kare (hfov 74,5°). Kerteriz tarama-bacağı karelerinde KB ile HB aynı karede **0/225**. Üretim rotası karenin alt bandından başlar; İKA saf öteleme yaptığı için rota KB'den `ankor KB` kadar kaymış sürülür (§4 tablosu) → temas/varamama. Gerçek kamera (IMX477 + 6 mm, hfov ~55°, ÖLÇÜLMEDİ) 30 m'de ~31 m iz verir (TAHMİN) — daha dar. Gerçek arenada KB/HB konumu **BEYAN GEREKLİ**.
3. **Ölçüm zinciri kusuru — güven kapısı dönüşümü OPEN_ROUTE sayılıyordu (düzeltildi).** `gorev_kosumu` ilk koşuda `iha_gonderim.tip` = çağrılan yöntem; `send_open_route` conf < 0,20'de NO_ROUTE(DUSUK_GUVEN) gönderir. model_2_zor_42: rota doğru (conf 0,141), telde NO_ROUTE, kod 2. Düzeltme: `tel_tipi` (hakem kaydından), `iha_gonderim.tel_tipi`, `guven_kapisi_reddi`; özet olay sayıları tel tipinden. Ölçüm dosyaları değiştirilmedi (eski JSON'lar hakem alanlarından çözülür).
4. **WIP kusuru — `sim_karar_toplayici.ozet_hesapla` "YAZMAZ" diyip yazıyordu (düzeltildi).** Diskteki özeti yeniden hesapla karşılaştıran nöbetçi, karşılaştırmadan önce dosyayı ezdiği için BOŞ kapı olurdu (D-370 sınıfı). Artık yazmaz; test `Path.write_text` yamasıyla denetler (mutasyon M10).

## 7. Sınırlar (FDR'ye aynen taşınır)

- **SENTETİK** ölçüm: MuJoCo render, dokular gerçek kare kırpması (yol şeridi zeminden AYRI doku; şartname arenasında zemin ile güzergâh aynı sıkıştırılmış topraktır — T213-A §6).
- İHA uçuşu **KİNEMATİK** (mocap, aerodinamik yok); tarama bacağında yatış 0 (T213-A düzeltmesi).
- Hakem onayı sim'de **OTOMATİK** (`sim_hakem`, `sim=true`, CONTRACTS §6.7.1 istisnası; saha kanıtı sayılmaz).
- İKA iz genişliği 0,39 m **TAHMİN**; teker armature 0,01 TAHMİN; motor tork sınırı yok (DDR'de yok).
- Kamera: sim hfov 74,5° (gerçek ~55°, ÖLÇÜLMEDİ); irtifa `poses.csv` z (gürültüsüz, MAVLink `relative_alt` yerine); kamera köprüsü (MJPEG) atlandı.
- Kerteriz beslemesinde kare döndürme SİM tarafındadır (üretim `run_camera` eksen parametresi geçirmez); ham besleme teşhis olarak ayrıca ölçüldü.
- Senkron yayın: toplayıcı her karardan sonra gönderimi bekler (latest-wins kaybı yok); Jetson ~1,35 FPS (D-431) ile kare hızı farkı modellenmez.
- OBB araç maskesi sim'de kapalı (sim'de araç yok).

## 8. Yeniden üretim ve kanıt

- İlk koşu: `kosum_tur3/kosum_tur3.sh` → ham çıktı `kosum_tur3/kosum_tur3_log.txt` (git `42ca7b8f` + çalışma ağacı; K3 üretim 15 harita × 2 besleme, gt 45, model 45, uretim 6/15'te kesildi).
- Devam: `kosum_tur3/kosum_tur3_devam.sh` → `kosum_tur3/kosum_tur3_devam_log.txt` (git `3132c503` + çalışma ağacı, 10 Eyl 15:27–15:37; K3 üretim aynı taramalarla yeniden + teşhis alanları, karar izi karşılaştırması, uretim 15 koşum). gt/model kolları yeniden koşulmadı: sürüş/rota kod yolları değişmedi (yalnız özet, tel-tipi ve takip örnekleme kancası `takip_ornekle` — davranış eş).
- Tarama kareleri / mozaik / besleme PNG'leri git dışıdır (`.gitignore`; `--hepsi` içerik-eş yeniden üretir). Depoda: tüm ölçüm JSON'ları, `detection.json`, `rota.json`, `karar_toplayici.json`. `poses.csv` yalnız `k3_uretim_boru/tarama/` altında depodadır; `kosum_tur3` koşumlarının tarama pozları git dışıdır (T214-B düzeltmesi, çürütücü RED-1); `uretim` koşumlarında kare pozları `karar_toplayici.json` `kareler[].x/y/z/yaw_derece` alanındadır.
- Özetler: `gorev_kosumu.ozet_kur` (`ozet_kosum.json`), `sim_karar_toplayici.ozet_kur` (`ozet_k3_uretim.json`); grafikler `sim_grafik.py`; bu belge `t214a_rapor.py`. Nöbetçiler ve mutasyonlar: `tests/test_sim_mujoco_olcum.py`, `results/fdr_sprint_20260910/H1/t214a/mutasyon_t214a.py` → `mutasyon_ciktisi.txt`.

## 9. Koşum tablosu (her satır bir JSON, `kosum_tur3/<kaynak>_<harita>_<senaryo>_<tohum>.json`)

| kaynak | harita | senaryo | tohum | rota | doğru | tel | wp | açıklık m | kod | HB | varış m | temas | sürüş sim-s | görev sim-s | takip maks m | başarı |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gt | 1 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 41 | 2.706 | 0 | ✓ | 0.21 | 0 | 64.3 | 101.6 | 0.498 | **✓** |
| gt | 1 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 41 | 2.843 | 0 | ✓ | 0.21 | 0 | 64.3 | 101.6 | 0.498 | **✓** |
| gt | 1 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 41 | 2.945 | 0 | ✓ | 0.21 | 0 | 64.3 | 101.6 | 0.498 | **✓** |
| gt | 1 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 46 | 1.689 | 0 | ✓ | 0.16 | 0 | 69.2 | 106.5 | 0.401 | **✓** |
| gt | 1 | orta | 43 | ✓ | ✓ | OPEN_ROUTE | 46 | 2.161 | 0 | ✓ | 0.16 | 0 | 69.2 | 106.5 | 0.401 | **✓** |
| gt | 1 | orta | 44 | ✓ | ✓ | OPEN_ROUTE | 46 | 2.119 | 0 | ✓ | 0.16 | 0 | 69.2 | 106.5 | 0.401 | **✓** |
| gt | 1 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.802 | 0 | ✓ | 0.18 | 0 | 95.6 | 132.9 | 0.504 | **✓** |
| gt | 1 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.541 | 0 | ✓ | 0.18 | 0 | 95.6 | 132.9 | 0.504 | **✓** |
| gt | 1 | zor | 44 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.464 | 0 | ✓ | 0.18 | 0 | 95.6 | 132.9 | 0.504 | **✓** |
| gt | 2 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.157 | 0 | ✓ | 0.17 | 0 | 67.9 | 105.2 | 0.513 | **✓** |
| gt | 2 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.264 | 0 | ✓ | 0.17 | 0 | 67.9 | 105.2 | 0.513 | **✓** |
| gt | 2 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.059 | 0 | ✓ | 0.17 | 0 | 67.9 | 105.2 | 0.513 | **✓** |
| gt | 2 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 63 | 2.050 | 0 | ✓ | 0.22 | 0 | 98.4 | 135.7 | 0.515 | **✓** |
| gt | 2 | orta | 43 | ✓ | ✓ | OPEN_ROUTE | 63 | 2.058 | 0 | ✓ | 0.22 | 0 | 98.4 | 135.7 | 0.515 | **✓** |
| gt | 2 | orta | 44 | ✓ | ✓ | OPEN_ROUTE | 63 | 1.932 | 0 | ✓ | 0.22 | 0 | 98.4 | 135.7 | 0.515 | **✓** |
| gt | 2 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.460 | 0 | ✓ | 0.20 | 0 | 92.1 | 129.4 | 0.563 | **✓** |
| gt | 2 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.460 | 0 | ✓ | 0.20 | 0 | 92.1 | 129.4 | 0.563 | **✓** |
| gt | 2 | zor | 44 | ✓ | ✓ | OPEN_ROUTE | 61 | 1.460 | 0 | ✓ | 0.20 | 0 | 92.1 | 129.4 | 0.563 | **✓** |
| gt | 3 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 44 | 2.810 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.494 | **✓** |
| gt | 3 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 44 | 3.336 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.494 | **✓** |
| gt | 3 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 44 | 2.763 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.494 | **✓** |
| gt | 3 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.532 | 0 | ✓ | 0.20 | 0 | 69.1 | 106.4 | 0.422 | **✓** |
| gt | 3 | orta | 43 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.459 | 0 | ✓ | 0.20 | 0 | 69.1 | 106.4 | 0.422 | **✓** |
| gt | 3 | orta | 44 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.461 | 0 | ✓ | 0.20 | 0 | 69.1 | 106.4 | 0.422 | **✓** |
| gt | 3 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 58 | 1.651 | 0 | ✓ | 0.16 | 0 | 90.3 | 127.6 | 0.475 | **✓** |
| gt | 3 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 58 | 1.447 | 0 | ✓ | 0.16 | 0 | 90.3 | 127.6 | 0.475 | **✓** |
| gt | 3 | zor | 44 | ✓ | ✓ | OPEN_ROUTE | 58 | 1.493 | 0 | ✓ | 0.16 | 0 | 90.3 | 127.6 | 0.475 | **✓** |
| gt | 4 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.147 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.516 | **✓** |
| gt | 4 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.147 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.516 | **✓** |
| gt | 4 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.147 | 0 | ✓ | 0.14 | 0 | 67.2 | 104.5 | 0.516 | **✓** |
| gt | 4 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 51 | 1.513 | 0 | ✓ | 0.12 | 0 | 84.2 | 121.5 | 0.513 | **✓** |
| gt | 4 | orta | 43 | ✓ | ✓ | OPEN_ROUTE | 51 | 1.505 | 0 | ✓ | 0.12 | 0 | 84.2 | 121.5 | 0.513 | **✓** |
| gt | 4 | orta | 44 | ✓ | ✓ | OPEN_ROUTE | 51 | 1.487 | 0 | ✓ | 0.12 | 0 | 84.2 | 121.5 | 0.513 | **✓** |
| gt | 4 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 47 | 1.509 | 0 | ✓ | 0.15 | 0 | 75.2 | 112.4 | 0.493 | **✓** |
| gt | 4 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 47 | 1.602 | 0 | ✓ | 0.15 | 0 | 75.2 | 112.5 | 0.493 | **✓** |
| gt | 4 | zor | 44 | ✓ | ✓ | OPEN_ROUTE | 47 | 1.511 | 0 | ✓ | 0.15 | 0 | 75.2 | 112.4 | 0.493 | **✓** |
| gt | 5 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 53 | 1.619 | 0 | ✓ | 0.22 | 0 | 82.8 | 120.1 | 0.520 | **✓** |
| gt | 5 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 53 | 2.225 | 0 | ✓ | 0.22 | 0 | 82.8 | 120.1 | 0.520 | **✓** |
| gt | 5 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 53 | 1.465 | 0 | ✓ | 0.22 | 0 | 82.8 | 120.1 | 0.520 | **✓** |
| gt | 5 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.494 | 0 | ✓ | 0.18 | 0 | 71.3 | 108.6 | 0.464 | **✓** |
| gt | 5 | orta | 43 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.839 | 0 | ✓ | 0.18 | 0 | 71.3 | 108.6 | 0.464 | **✓** |
| gt | 5 | orta | 44 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.704 | 0 | ✓ | 0.18 | 0 | 71.3 | 108.6 | 0.464 | **✓** |
| gt | 5 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.758 | 0 | ✓ | 0.23 | 0 | 64.1 | 101.4 | 0.240 | **✓** |
| gt | 5 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.497 | 0 | ✓ | 0.23 | 0 | 64.1 | 101.3 | 0.240 | **✓** |
| gt | 5 | zor | 44 | ✓ | ✓ | OPEN_ROUTE | 44 | 1.928 | 0 | ✓ | 0.23 | 0 | 64.1 | 101.4 | 0.240 | **✓** |
| model | 1 | kolay | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.24 | 0 | — | 932.5 | — | ✗ |
| model | 1 | kolay | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.24 | 0 | — | 932.5 | — | ✗ |
| model | 1 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 43 | 2.784 | 0 | ✓ | 0.27 | 0 | 63.4 | 100.7 | 1.012 | **✓** |
| model | 1 | orta | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.49 | 0 | — | 932.5 | — | ✗ |
| model | 1 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.49 | 0 | — | 932.5 | — | ✗ |
| model | 1 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.49 | 0 | — | 932.5 | — | ✗ |
| model | 1 | zor | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.17 | 0 | — | 932.5 | — | ✗ |
| model | 1 | zor | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.17 | 0 | — | 932.5 | — | ✗ |
| model | 1 | zor | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.17 | 0 | — | 932.5 | — | ✗ |
| model | 2 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 47 | 2.179 | 0 | ✓ | 0.28 | 0 | 67.6 | 104.9 | 1.564 | **✓** |
| model | 2 | kolay | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.16 | 0 | — | 932.5 | — | ✗ |
| model | 2 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 48 | 2.338 | 0 | ✓ | 0.28 | 0 | 69.3 | 106.6 | 1.329 | **✓** |
| model | 2 | orta | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.71 | 0 | — | 932.5 | — | ✗ |
| model | 2 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.71 | 0 | — | 932.5 | — | ✗ |
| model | 2 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.71 | 0 | — | 932.5 | — | ✗ |
| model | 2 | zor | 42 | ✓ | ✓ | NO_ROUTE | 62 | 1.866 | 2 | ✗ | 44.53 | 0 | — | 932.5 | — | ✗ |
| model | 2 | zor | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.53 | 0 | — | 932.5 | — | ✗ |
| model | 2 | zor | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.53 | 0 | — | 932.5 | — | ✗ |
| model | 3 | kolay | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.31 | 0 | — | 932.5 | — | ✗ |
| model | 3 | kolay | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.31 | 0 | — | 932.5 | — | ✗ |
| model | 3 | kolay | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.31 | 0 | — | 932.5 | — | ✗ |
| model | 3 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 47 | 1.759 | 0 | ✓ | 0.26 | 0 | 65.8 | 103.1 | 1.751 | **✓** |
| model | 3 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.77 | 0 | — | 932.5 | — | ✗ |
| model | 3 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.77 | 0 | — | 932.5 | — | ✗ |
| model | 3 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 58 | 1.232 | 0 | ✓ | 0.21 | 0 | 88.5 | 125.8 | 1.790 | **✓** |
| model | 3 | zor | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.77 | 0 | — | 932.5 | — | ✗ |
| model | 3 | zor | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.77 | 0 | — | 932.5 | — | ✗ |
| model | 4 | kolay | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.27 | 0 | — | 932.5 | — | ✗ |
| model | 4 | kolay | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.27 | 0 | — | 932.5 | — | ✗ |
| model | 4 | kolay | 44 | ✓ | ✓ | OPEN_ROUTE | 47 | 2.648 | 0 | ✓ | 0.22 | 0 | 66.8 | 104.1 | 0.975 | **✓** |
| model | 4 | orta | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.65 | 0 | — | 932.5 | — | ✗ |
| model | 4 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.65 | 0 | — | 932.5 | — | ✗ |
| model | 4 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.65 | 0 | — | 932.5 | — | ✗ |
| model | 4 | zor | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.22 | 0 | — | 932.5 | — | ✗ |
| model | 4 | zor | 43 | ✓ | ✓ | OPEN_ROUTE | 48 | 0.593 | 0 | ✓ | 0.24 | 0 | 69.3 | 106.6 | 2.367 | **✓** |
| model | 4 | zor | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.22 | 0 | — | 932.5 | — | ✗ |
| model | 5 | kolay | 42 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.66 | 0 | — | 932.5 | — | ✗ |
| model | 5 | kolay | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.66 | 0 | — | 932.5 | — | ✗ |
| model | 5 | kolay | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.66 | 0 | — | 932.5 | — | ✗ |
| model | 5 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 47 | 2.136 | 0 | ✓ | 0.26 | 0 | 70.4 | 107.7 | 1.243 | **✓** |
| model | 5 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.78 | 0 | — | 932.5 | — | ✗ |
| model | 5 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.78 | 0 | — | 932.5 | — | ✗ |
| model | 5 | zor | 42 | ✓ | ✓ | OPEN_ROUTE | 42 | 1.948 | 0 | ✓ | 0.26 | 0 | 63.6 | 100.9 | 1.626 | **✓** |
| model | 5 | zor | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.55 | 0 | — | 932.5 | — | ✗ |
| model | 5 | zor | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.55 | 0 | — | 932.5 | — | ✗ |
| uretim | 1 | kolay | 42 | ✓ | ✓ | OPEN_ROUTE | 19 | 0.000 | 4 | ✗ | 38.52 | 5024 | 600.1 | 637.4 | 5.034 | ✗ |
| uretim | 1 | kolay | 43 | ✓ | ✓ | OPEN_ROUTE | 20 | 0.000 | 4 | ✗ | 38.52 | 7179 | 600.1 | 637.4 | 4.712 | ✗ |
| uretim | 1 | kolay | 44 | ✓ | ✗ | OPEN_ROUTE | 22 | 0.000 | 4 | ✗ | 38.52 | 7462 | 600.1 | 637.4 | 4.664 | ✗ |
| uretim | 2 | kolay | 42 | ✓ | ✗ | OPEN_ROUTE | 23 | 0.000 | 4 | ✗ | 39.79 | 7 | 600.1 | 637.4 | 5.128 | ✗ |
| uretim | 2 | kolay | 43 | ✓ | ✗ | OPEN_ROUTE | 22 | 0.000 | 4 | ✗ | 39.77 | 10 | 600.1 | 637.4 | 5.048 | ✗ |
| uretim | 2 | kolay | 44 | ✓ | ✗ | OPEN_ROUTE | 22 | 0.000 | 4 | ✗ | 39.77 | 10 | 600.1 | 637.4 | 5.048 | ✗ |
| uretim | 2 | orta | 42 | ✓ | ✓ | OPEN_ROUTE | 33 | 0.000 | 4 | ✗ | 35.66 | 12839 | 600.1 | 637.4 | 9.048 | ✗ |
| uretim | 2 | orta | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.71 | 0 | — | 932.5 | — | ✗ |
| uretim | 2 | orta | 44 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 44.71 | 0 | — | 932.5 | — | ✗ |
| uretim | 4 | zor | 42 | ✓ | ✗ | OPEN_ROUTE | 24 | 0.000 | 4 | ✗ | 40.61 | 3 | 600.1 | 637.4 | 5.748 | ✗ |
| uretim | 4 | zor | 43 | ✗ | ✗ | NO_ROUTE | 0 | — | 2 | ✗ | 45.22 | 0 | — | 932.5 | — | ✗ |
| uretim | 4 | zor | 44 | ✓ | ✗ | OPEN_ROUTE | 26 | 0.000 | 4 | ✗ | 40.04 | 11 | 600.1 | 637.4 | 6.774 | ✗ |
| uretim | 5 | zor | 42 | ✓ | ✗ | OPEN_ROUTE | 29 | 0.000 | 4 | ✗ | 31.37 | 74 | 600.1 | 637.4 | 4.182 | ✗ |
| uretim | 5 | zor | 43 | ✓ | ✗ | OPEN_ROUTE | 27 | 0.000 | 4 | ✗ | 31.70 | 7607 | 600.1 | 637.4 | 4.718 | ✗ |
| uretim | 5 | zor | 44 | ✓ | ✗ | OPEN_ROUTE | 27 | 0.000 | 4 | ✗ | 40.24 | 2704 | 600.1 | 637.3 | 3.802 | ✗ |
