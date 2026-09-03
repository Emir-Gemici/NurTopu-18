# DEVAM NOKTASI — 3 Eylül 2026, 12:30

> "devam" dendiğinde buradan sürülür. Son commit: `aa08581`.

## Nerede kaldık

Kullanıcı resmî FDR yönergesini (`FDR_2_qNiVF.pdf`) sağladı. Rapor o yapıya
taşınıyor. **Temel kondu ve commit'lendi**; bölüm dosyalarının taşınması
yarım kaldı.

## ✅ BİTEN (commit `aa08581`)

- `results/fdr_sablon/fdr_yonerge_metin.txt` — yönergenin tam metni
- `FDR/YONERGE_HARITASI.md` — zorunlu iskelet, her gereksinim `Y-…` kimliğiyle,
  DURUM sütunlu, bölüm bazlı boşluk özeti. **Raporun sözleşmesi budur.**
- `FDR/BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` — kapak, versiyonlar, 29 kısaltma
- `FDR/TAKIM_PROMPT.md` — **baştan yazıldı** (isim yasağı + beyan/mühendislik ayrımı)
- `FDR/README.md` — "TAKIM ARKADAŞLARI BURADAN BAŞLA" bölümü
- `FDR/ACIK_KALEMLER.md` — kalem 17 düştü, 16 yeniden açıldı, 19 yeni kalem (26–44)
- `tests/test_yarisma_adi_kapisi.py` — yarışma adı kapısı (3/3)
- Bayat artefaktlar tazelendi: kuru koşu, genel kapı; saha belleği 🔴 BAYAT işaretli

## ⏳ YARIM KALAN — ilk iş bu

**İki workflow arka planda koşuyordu; bittiyse sonuçları YERE İNMEMİŞ olabilir.**

1. **`wf_5016c26d-8b5` — FDR bölümlerinin yönerge iskeletine taşınması**
   (`FDR/BOLUM_1…7_*.md`, 7 ajan + 7 denetçi).
   `git status` ile bak: `BOLUM_*.md` değişmişse **ajanlar yazmış demektir** —
   diff'i oku, denetçi raporlarını `journal.jsonl`'dan çıkar, **içerik kaybı**
   (artefakta bağlı satır silinmiş mi) kontrol et, sonra commit'le.
   Sonuç dosyası: `subagents/workflows/wf_5016c26d-8b5/journal.jsonl`

2. **`wf_b0f33806-4ba` — yazılım borcu kapatma** (worktree'lerde):
   tek-yazar kilidi (`rpi_inference`, `iha_inis_yayinci`), T204 SIGTERM,
   T205 ölü VideoWriter, hakem kanıt olay kümesi + YKS başlık çakışması,
   kamera köprüsü beyaz liste, H1c damgası.
   Worktree'ler: `.claude/worktrees/wf_b0f33806-4ba-*`. Değişiklikler orada
   **commit'lenmemiş** bırakıldı; mimar birleştirecek.

## Sonraki adımlar (sırayla)

1. İki workflow sonucunu yere indir, denetle, commit'le
2. `YONERGE_HARITASI.md` DURUM sütununu taşıma sonrası **yeniden ölç**
3. `scripts/fdr_acik_kalem_cikar.py` koş (`--dogrula` çıkış 0 olmalı)
4. Kapılar: `codes/test_rota_sentetik.py` 15/15 + tam süit + adı kapısı
5. **D-417 defter kaydı** yazılmadı — yönerge bulgularını (isim yasağı, Bölüm 3
   iskeleti, simülasyon gereksinimi) deftere işle
6. Kullanıcı `FDR/` klasörünü **ortak sürücüye yükleyecek** — yükleme öncesi
   klasörün tutarlı olduğundan emin ol

## Kullanıcının beklediği

- FDR klasörü Drive'a yüklenmeye hazır olacak
- Arkadaşlar `TAKIM_PROMPT.md` ile kendi bölümlerini dolduracak
- Cumartesi 5 Eylül montaj; yazılım tarafı hazır (tıkayan iş yok)

## Açık uyarılar

- 🔴 Saha belleği bayat — cuma `bellek_hazirla.py` yeniden koşulmadan USB'ye kopyalanmaz
- 🔴 Jetson: microSD YOK, eMMC modül + M.2. Cumartesi ilk iş **aç ve bak**;
  eMMC boşsa **Ubuntu x86_64 host** gerekir (D-413)
- 🔴 Kol 1–2 / kol 3–4 farklı reçetelerle basıldı, gerekçesi kayıtta yok;
  yönerge "gerekliliği ispatlanmamış değişiklikler diskalifiye sebebi" diyor
- YKS başlığında "HAZIRLIK" etiketi çakışıyor (workflow 2'de kapatılıyor olabilir)
