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

🔴 **İki workflow da oturum kapanınca DURDU** (12:30 sonrası, tamamlama kaydı yok).
Aşağıdaki durum **ölçüldü**, tahmin değil.

### 1. `wf_5016c26d-8b5` — FDR bölümlerinin yönerge iskeletine taşınması

**7 bölümün 2'si yazıldı, 5'i hiç başlamadı. Yazılan 2'si DENETLENMEDİ.**

Çalışma ağacında **commit'lenmemiş** duruyor:

| dosya | değişim | durum |
|---|---|---|
| `FDR/BOLUM_1_OZET.md` | +581 satır | ⚠ ajan yazdı, **denetçi koşmadı** |
| `FDR/BOLUM_7_BUTCE_GERCEKLEME.md` | +625 satır | ⚠ ajan yazdı, **denetçi koşmadı** |
| `BOLUM_2, 3, 4, 5, 6` | — | hiç yazılmadı |

⚠ **Bu iki dosyayı denetlemeden commit'leme.** Denetçi aşaması tam da şunu
arayacaktı: (a) **içerik kaybı** — artefakta bağlı satır (dosya yolu, JSON,
`D-NNN`, komut çıktısı) silindi mi, (b) başlıklar yönergeyle **birebir** mi,
(c) **uydurma sayı** girdi mi, (d) **isim sızıntısı** var mı.
`git diff -- FDR/BOLUM_1_OZET.md` ile başla.

**Sürdürme:** `Workflow({scriptPath: ".../navitas-fdr-yonergeye-tasima-wf_5016c26d-8b5.js",
resumeFromRunId: "wf_5016c26d-8b5"})` — biten ajanlar önbellekten döner, kalan
5 bölüm canlı koşar. Ama önce yazılan 2 dosyaya karar ver: denetleyip tutmak mı,
`git checkout -- FDR/BOLUM_1_OZET.md FDR/BOLUM_7_BUTCE_GERCEKLEME.md` ile geri
alıp temiz koşmak mı. **Temiz koşmak daha güvenli** — yarım tur bırakılmış iş.

### 2. `wf_b0f33806-4ba` — yazılım borcu kapatma

**Worktree'lerin dördü de `baeca14`'te, yani hiçbir ajan yazmadı.**
(`git worktree list` ile ölçüldü; 1 ve 2 numaralı worktree `locked`.)
Kapatılacaklardı: tek-yazar kilidi (`rpi_inference`, `iha_inis_yayinci`),
T204 SIGTERM, T205 ölü VideoWriter, hakem kanıt olay kümesi + YKS başlık
çakışması, kamera köprüsü beyaz liste, H1c damgası.

**Sürdürme:** `resumeFromRunId: "wf_b0f33806-4ba"` — ya da temiz yeniden başlat;
kayıp iş yok. Kilitli worktree'ler önce çözülmeli (`git worktree unlock`).

⚠ Bu borçların **hiçbiri cumartesiyi tıkamıyor** — hepsi 17 Eylül mühründen
önce kapanması gereken kalemler.

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
