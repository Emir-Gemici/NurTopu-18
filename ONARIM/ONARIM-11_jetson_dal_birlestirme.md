# ONARIM-11 — Jetson dalı `jetson/tek-yol-20260912` master'a birleştirildi; D-numara çakışması çözüldü

**Durum:** KAPANDI (depo) · Jetson'daki çalışan paket ağacı (`~/navitas`) ile depo senkronu ayrı madde (ONARIM-10/11b)
**Tarih:** 17 Eylül 2026 · **Liste:** `ONARIM-00_LISTE.md` madde 11

## Sorun
- Dal `origin/jetson/tek-yol-20260912` (`abea98cb`, 13 Eylül) master'a hiç girmemişti: 9 commit, 19 dosya (+11 362 satır; çoğu `results/jetson_20260913/k2_denklik_kabul_20260913.json`).
- İçindeki kararlar master'da yoktu: **D-481 telsiz bandı kararı (433 MHz, RFD900A kullanılmayacak)**, **D-482 `.engine` ≡ `.pt` kabul kümesinde denk**, D-484/T261 tek yol + açık arazi riski, CLAUDE.md madde 17 yazar kimliği `trs-1342`.
- Numara çakışması: dal D-477…D-484 ↔ master D-477…D-484 (Gazebo/FDR); dal T261 ↔ master T261 (mesh yolu).

## Çözüm
- `git merge --no-ff origin/jetson/tek-yol-20260912`; çakışan iki dosya elle, betikle çözüldü:
  - `REVIEW_LOG.md`: master içeriği aynen + dalın 3 geri-işaret notu (D-303, D-356, D-431 altına) + dalın 8 kaydı **dosya sonuna**, numaralar **D-477…D-484 → D-495…D-502**, `T261 → T265`. Kayıtların önüne "İKİNCİ NUMARA DÜZELTMESİ" notu (tam eşleme tablosu; ilk D-469…472 eşlemesiyle zincir).
  - `TASK_QUEUE.md`: dalın "Jetson acil devir" bölümü sona, `T261 → T265`, D-numaraları eşlemeli.
  - `CLAUDE.md` dalın madde 17'si alındı; içindeki "(D-471)" → "(D-497; dalda D-479, ilk yazımda D-471)".
- Dal commit mesajları ve `results/jetson_20260913/`, `results/codex_jetson_20260912/` ham dosyaları **değiştirilmedi** (eski numaraları anar; eşleme notta).

## Kanıt — dokunulan testler, birleştirme ÖNCESİ (master) ↔ SONRASI (temiz worktree)
| test | önce | sonra |
|---|---|---|
| genel kapı `codes/test_rota_sentetik.py` | 15/15 · 15/15 | **15/15 · 15/15** |
| `test_d373_defter_geri_isaret` | FAIL 2 | FAIL 2 (aynı: D-438←D-488, D-470←D-472) |
| `test_defter_butunlugu` · `test_monotonluk` · `test_belge_kilidi` · `test_k6_rota_yol_ustunde` · `test_faz_b_jetson_baslat` · `test_onarim03_gorev_kaydi` | OK | OK |
| `test_t220_jetson_istekleri` | FAIL 2 | **FAIL 1** (düzelen 1) |
| `test_faz_b_protocol_dayaniklilik` | ERROR 1 | **OK** |
| `test_d370_mutasyon_satir_sonu` | FAIL 1 | **OK** |
| `test_gece_karisiklik_matrisi` | FAIL 1 | **OK** |
| `test_jetson_paket_defteri` | FAIL 1 | FAIL 1 |
Yeni kırmızı **yok**.

## Sonuçları
- **ONARIM-13 (telsiz frekansı):** dalın D-499'u (eski D-481) kullanıcı kararını kayda geçirmiş: **433 MHz kullanılacak, RFD900A (900 MHz) kullanılmayacak**. Depodaki 433 MHz metinleri bu kararla tutarlı; gövdede RFD900A takılıysa değişmesi **donanım işi**.
- Emir'in yerel deposundaki D-490/491/492 (düşüş analizleri) hâlâ push edilmedi; gelince D-503+ numara alır.
