# FDS (Final Değerlendirme Sunumu) — slayt planı ve süre bütçesi

> **Mimar, 13 Eylül 2026.** T259. Teslim **14.09.2026 – 17.00**. Süre **15 dk**
> (D-475 `[22:17]`), istenen üslup *"teknik ve ayrıntılı"* (`[09:28]`).
> Sayı uydurulmaz; her sayı `results/sunum_20260913/kanit_havuzu.md` üzerinden
> `dosya:satır` atfına bağlanır ve `tests/test_sunum_kanit.py` ile kilitlenir.
> ÖLÇÜLDÜ / ÖLÇÜLEMEDİ / BEYAN etiketleri FDR'den **aynen** taşınır, terfi ettirilmez.

## Süre bütçesi

18 içerik slaydı + 2 şablon slaydı. Ortalama **45–50 sn/slayt**. Anlatım sırası
raporun bölüm sırasını izler ki jüri raporla eşleştirebilsin.

| # | slayt | süre | kaynak bölüm | görsel |
|---|---|---|---|---|
| 1 | Kapak (şablon — düzeni değişmez) | — | — | şablon |
| 2 | Takım yapısı (şablon — **İNSAN doldurur**) | 30 sn | — | şablon |
| 3 | Ajanda + tek cümlede proje | 30 sn | BOLUM_1 | — |
| 4 | Görev ve senaryo: FDA akışı, şartname kısıtları | 60 sn | BOLUM_1, şartname | — |
| 5 | Sistem mimarisi: İHA + İKA + YKS veri akışı | 60 sn | BOLUM_3 §3.3 | `akis_a.svg` |
| 6 | İHA künyesi ve bağlantı şeması | 50 sn | BOLUM_3 §3.3.1.1 | `iha_baglanti.svg` |
| 7 | İKA künyesi ve bağlantı şeması | 40 sn | BOLUM_3 §3.2.2 | `ika_baglanti.svg` |
| 8 | Otonomi zinciri: kamera → algı → karar → rota → yayın | 60 sn | CONTRACTS §6 | `akis_b.svg` |
| 9 | Algı katmanı: model, veri, kabul kapıları | 60 sn | BOLUM_3 §3.3.2 | — |
| 10 | **Mimari ilke:** "serbest alan otoritedir" + rota kapısı | 60 sn | CLAUDE.md md.15, kapı çıktısı | kapı çıktısı |
| 11 | Jetson gerçek başarım: FPS, engine/pt, termal | 60 sn | BOLUM_3/4, D-431 | — |
| 12 | Haberleşme: MAVLink çoğullayıcı, tek-yazar kilidi, telsiz | 60 sn | BOLUM_3 §3.3.1.1.8 | — |
| 13 | Simülasyon sonuçları | 60 sn | BOLUM_3 §3.3.3 | `sim_*.png` |
| 14 | Yer ve uçuş testleri: ne ölçüldü, ne düştü | 60 sn | BOLUM_4 | — |
| 15 | Üretim faaliyetleri (15 puan) | 50 sn | BOLUM_5 | — |
| 16 | Gereksinim izlenebilirliği (10 puan) | 50 sn | BOLUM_6 | `uygunluk_pasta.svg` |
| 17 | Bütçe gerçekleme | 40 sn | BOLUM_7 | — |
| 18 | **Açık kalemler ve risk yönetimi** (dürüstlük slaydı) | 60 sn | ACIK_KALEMLER | — |
| 19 | FDA'ya kadar takvim ve sonraki adımlar | 40 sn | BOLUM_2 §2.2.8 | — |
| 20 | Teşekkürler (şablon) | — | — | şablon |

Toplam içerik: ~14,5 dk. Soru payı dışarıda.

## Anlatım ilkeleri (jüriye karşı duruş)

1. **Ölçülmüş olanı ölçüm, ölçülmemişi ölçülemedi diye söyle.** Raporun ayırt edici
   yanı budur; sunumda da aynı dil kullanılır. "Geçti" yazmadığımız yere "geçti" denmez.
2. **Her iddianın arkasında koşulmuş bir komut var.** Kapı çıktıları slaytta tarihiyle
   görünür (örn. rota üretim kapısı 13 Eylül koşumu).
3. **Zayıflıklar gizlenmez, sahibi ve kapanma yolu ile söylenir** (slayt 18). Jüri
   zaten raporda görecek; sunumda saklanması güven kaybettirir.
4. **İsim kuralı:** raporda kişisel veri yasak (yönerge Bölüm 2.1), **sunum şablonu
   slayt 2'de isim istiyor** — şablon ne istiyorsa o doldurulur, rapor kuralı taşınmaz.

## İNSAN doldurması gerekenler (depoda yok, uydurulmaz)

| alan | nerede | not |
|---|---|---|
| TAKIM ID | kapak | başvuru sisteminden |
| BAŞVURU ID | kapak | başvuru sisteminden |
| PROJE ADI / KONU BAŞLIĞI / TAKIM ADI | kapak | resmî başvurudaki yazımıyla |
| Danışman + kaptan + 5 üye: ad, görev, eğitim | slayt 2 | şablon zorunlu tutuyor |
| Kim sunacak, kim hangi bölümü anlatacak | slayt 2 notu | 15 dk bölüşümü |
