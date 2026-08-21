# CODEX GÖREV PROMPTLARI · 2026-08-20 · Veren: Claude 2 / Fable 5 (ustabaşı)
# Kullanım: her bloğu ilgili Codex ajanına AYNEN yapıştır. Sıra önemli değil —
# üç görev FARKLI dosyalara dokunur (kilit çakışması yok). T100 Codex'e
# VERİLMEDİ (yerel GPU/veri ister; ustabaşı koşacak — gerekçe kayıtta).

---

## CODEX-1 · T115 — TASK_QUEUE.md OKTAL KAÇIŞ ONARIMI

GOREV EMRI · Codex-1 · T115 — TASK_QUEUE.md OKTAL KACIS ONARIMI
Veren: Claude 2 / Fable 5 (ustabasi) · 2026-08-20 · zimmet: kuyrukta
[IN_PROGRESS: Codex-1] (commit 5d1fd43). Once CODEX_WORKERS.md'yi oku.
Master'in SON halinden basla.

SORUN (olculdu): TASK_QUEUE.md'de 21 satir literal "avitas" ile basliyor
(`grep -c '^avitas' TASK_QUEUE.md` -> 21). Bozulma:
`O:\navitas-local-train\NN_dosya.py` yollarinda `\n` GERCEK yeni satira,
`\NN` OKTAL kacisa donusmus:
  3125 "... · `O:" + SATIR SONU / 3126 "avitas-local-train)_sentetik_arena.py`"
     (\51 oktal = ')')
  5620 "avitas-local-train5_kabul_denetcisi.py:..."  (\65 oktal = '5')
Tersine cevrim MEKANIK: onceki satir "O:" ile bitiyor VE satir
"avitas-local-train" ile basliyorsa, orijinal =
  "O:\navitas-local-train\" + oct(ord(ilk_karakter))[2:] + kalan
(dogrulama: oct(ord(')'))=0o51 -> 51_sentetik_arena.py ✓)

IS:
1. `scripts/onarim/t115_oktal_onarim.py` yaz — onarim YALNIZ betikle:
   a. `^avitas` satirlarini + ONCEKI satirlarini bul;
   b. her vaka icin deseni OLC: uymayan vakayi ONARMA, "COZULEMEYEN" raporla;
   c. uyanlarda iki satiri tek satira birlestir (yukaridaki cevrim);
   d. JSON rapor: [{satir_no, once_1, once_2, sonra, cozulen_dosya_adi}]
      + cozulemeyenler.
2. Betigi kos, TASK_QUEUE.md'yi yamala. Sonra `grep -c '^avitas'` -> 0
   olmali (cozulemeyen kaldiysa sayiyi raporla, 0'i ZORLAMA).
3. Raporu `scripts/onarim/t115_rapor.json` olarak repoya birak.

DOKUNMA: 21 vaka disindaki hicbir satir; baska AI'in [IN_PROGRESS] gorevi;
insan gorevleri (madde 1). Yol VARLIK dogrulamasi (`test -f`) SENDE DEGIL —
O: surucusu yereldir, ustabasi dogrulayacak. Kapilari KOSMA (yerel
bagimlilik); raporuna "kapilar kosulMADI (yerel)" yaz.

TESLIM: tek commit, yazar Emir-Gemici, mesaj:
"T115: kuyruktaki 21 oktal-kacis yolu betikle onarildi (rapor:
scripts/onarim/t115_rapor.json)". HICBIR AI atfi YOK (Co-Authored-By /
Generated-with dahil). Gorevi [x] YAPMA; durum satirini
[REVIEW: ustabasi] yap.

---

## CODEX-2 · T107 — 56 BETIGININ BAYAT `AD` VARSAYILANI

GOREV EMRI · Codex-2 · T107 — 56_t53_gercek_karisim.py::AD bayat varsayilani
Veren: Claude 2 / Fable 5 (ustabasi) · 2026-08-20 · zimmet: kuyrukta
[IN_PROGRESS: Codex-2]. Once CODEX_WORKERS.md'yi oku. Master'in SON hali.

SORUN (olculdu, D-215/i=9): `scripts/olcum/56_t53_gercek_karisim.py` icinde
`AD = "v22_on10_gercek"` sabit varsayilani var; surum dizisi coktan v33/v34'e
gitti. Sonuc: v34'un kosum dizini "v23_t54_engelli" gibi YANLIS adla dogdu
(config/model_registry.json `_egitim` notu bunu kusur olarak kaydeder).
Bayat varsayilan bu projede tekrarlanan kusur sinifidir.

IS:
1. `--ad` argumanini ZORUNLU yap (required=True); `AD` sabitini ve ona
   dusen varsayilani kaldir. Hata mesaji yol gostersin: "kosum adini acikca
   ver (bayat varsayilan kusuru: T107/D-215)".
   ⚠ `RECETE` sozlugune ve baska HICBIR davranisa dokunma —
   `101_t121_ft_kosumu.py` RECETE'yi import eder, kirilmamali.
2. Koruyucu test yaz: `tests/test_t107_ad_varsayilani.py` — AST ile
   56 betiginde (a) modul duzeyinde bayat AD sabiti atanmadigini,
   (b) `--ad` add_argument cagrisinin required=True tasidigini dogrular.
   Elle metin arama degil AST (`ast.parse`) kullan.
3. Kendi degisikligini KENDIN onaylayamazsin — ustabasi denetleyecek.

DOKUNMA: scripts/olcum/56... ve yeni test dosyasi DISINDA hicbir dosya.
config/model_registry.json'a DOKUNMA. Canli ayna kopyasi (O:\navitas-local-
train\...) SENDE DEGIL — ustabasi senkronlayacak. Kapilari kosamazsan
"kosulMADI (yerel)" yaz.

TESLIM: tek commit, yazar Emir-Gemici, mesaj:
"T107: 56 betiginde bayat AD varsayilani kaldirildi, --ad zorunlu (AST
korumali test ile)". AI atfi YOK. [x] YAPMA; durum [REVIEW: ustabasi].

---

## CODEX-1 veya 2 (hangisi once biterse) · T120 BAGIMSIZ TEKRAR

GOREV EMRI · Codex · T120 BAGIMSIZ TEKRAR — tests/ kesif sayimi
Veren: Claude 2 / Fable 5 (ustabasi) · 2026-08-20.

BAGLAM: Bu olcum D-213'te ustabasi tarafindan YAPILDI. Sen BAGIMSIZ
tekrarsin: D-213'u OKUMADAN, kendi yonteminle olc. Amac capraz dogrulama —
ustabasi kendi olcumunu kendi onaylayamaz.

IS: tests/ altindaki HER .py dosyasi icin "unittest discover bu dosyadan
kac test topluyor" sayisini olc (kendi betiginle; scratch'te kalsin,
repoya betik ekleme). Sifir toplayanlari ve `test_` onekli olmayanlari
ayri isaretle. Rapor: `results/t120_bagimsiz_tekrar.json` —
[{dosya, toplanan, takim_deseninde_mi}] + ozet.
NOT: ortamda numpy/cv2/ultralytics kurulamazsa import hatalarini
"IMPORT_HATASI" olarak isaretle ve raporda belirt — sifir toplayan ile
karistirma. Hicbir test dosyasini DEGISTIRME/silme/tasima (karar mimarin).

TESLIM: tek commit, yazar Emir-Gemici, mesaj:
"T120 bagimsiz tekrar: tests/ kesif sayimi (rapor: results/
t120_bagimsiz_tekrar.json)". AI atfi YOK.
