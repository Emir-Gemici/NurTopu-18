# DOGRULAMA oturumu — kullanici karari (2026-08-26)

Kullanici: "sen dogrulama ucusu olarak al bazi frameleri sikinti yok."

Secilen: **DJI_20260822172613_0038_D** (22 Agustos, 0038). Gerekce (olculmus):
- 0037/0039 ile GPS ortusmesi 0 m2 / %1,5 (SU_ETIKETLEME_PLANI §1d) -> ALAN ayrik
- hicbir egitim/erken-durdurma kararina girmedi (ON_KAYIT §2; test29 hicbir karara girmez,
  val82 yalniz erken durdurmada) — bu dosyayla birlikte val82 de artik EGITIME GIRMEZ
- referansi iki bagimsiz kor gecisle uzlastirildi (T152, D-289): sinif0 = A∧B, sinif1 = A∨B
- SINIR: ayni gun, ayni kamera, ayni operator, ayni saha turu (kirsal); ARENA degil.
  Yani "alan disi" sorusunu KISMEN kapatir (D-256 §5, T111) — kullanici bu siniri bilerek kabul etti.

Diger adaylar elendi (results/gece_20260826/dogrulama_adaylari.jpg): 20 Agustos DJI
fotograflari gece/yer seviyesi (L≈28); WhatsApp gorselleri = data/raw_frames otopark kareleri
(copy_paste_t127 ile EGITIMDE).

Gercek-kare kapisi: `scripts/olcum/142_gece_olcum.py --test-dizin dataset/dji_kirsal_0038_bolum_v3/images/{test,val}
--etiket-dizin .../labels/{test,val} --tavan results/gece_20260826/test29_etiket_tavani_v3.json`
(CONTRACTS §12). Bu klasordeki video/SRT `dji/` kokundekinin sabit baglantisidir (ayni bayt).
