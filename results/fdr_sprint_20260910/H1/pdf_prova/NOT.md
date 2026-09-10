# PDF provası — T214-B (10 Eylül 2026, ON_KAYIT H1-K9 / §5.8)

Komut (depo kökünden):

```
O:/navitas-local-train/venv/Scripts/python.exe -B scripts/fdr_pdf_uret.py --kip yazilim
```

Çıktı (üretecin satırı): `ÜRETİLDİ FDR\pdf\FDR_YAZILIM_KOLU_20260910.pdf · 198 sayfa · 6.4 MB · kaynak 54c7b0dc · yol: paged.js`
(kaynak = T214-A birleştirme commit'i + T214-B çalışma ağacı, commit öncesi).

| dosya | bayt | sha256 |
|---|---|---|
| `FDR/pdf/FDR_YAZILIM_KOLU_20260910.pdf` | 6 399 064 | `894ea799c6549c085c05fb631ca4b3eb973a9cee5e1e9dd69591b6ee99dda837` |
| `FDR/pdf/FDR_YAZILIM_KOLU_20260910.html` | 621 126 | `c581a982dc95b89afe2ff35e2876a22b243ca46cdd3688530718531dd91bf711` |

PDF ve HTML **commit'e alınmadı** (üretilen dosya, yeniden üretilebilir; tam PDF provası ON_KAYIT §5.8 uyarınca
19 Eylül). Aynı komut aynı kaynaktan yeniden üretir; Chrome/paged.js çıktısı bayt-eş olmayabilir.

## Gözle denetlenen sayfalar (Read ile, sayfa görüntüsü)

Sayfa yerleri `pypdf` metin aramasıyla bulundu: §3.3.3 başlığı s.28 · §3.3.3.1 s.30 · §3.3.3.2 s.32 ·
Şekil 3.3.3.1–2 s.34 · Şekil 3.3.3.3–4 s.35 · §3.3.3.3 s.36 · §3.3.4 s.37 · §4.7 s.103–104.

- **Tablolar taşmıyor:** kapı özeti (5 sütun, s.28–29), ortam/model tablosu (4 sütun, s.30–31), K3 tablosu
  (6 sütun, s.32), K4/K5 tablosu (11 sütun — hücre içinde satır kırıyor, sayfa kenarını aşmıyor, s.32–33),
  süre tablosu (6 sütun, s.33), video tablosu (2 sütun; sha256 hücre içinde kırılıyor, s.36), §4.7 özet tablosu (s.104).
- **Grafikler görünür:** 4 SVG (Şekil 3.3.3.1–3.3.3.4) tam genişlikte, eksen etiketleri, n/medyan etiketleri,
  SENTETİK etiketi ve "Veri: … · üreteç sim_grafik.py" alt yazısı okunur; italik şekil alt yazıları altta (s.34–35).
- **Üstü çizili eski metin** (3 Eylül Gazebo envanteri, ÖLÇÜLEMEDİ paragrafları, Gazebo gereksinim listesi)
  `<del>` olarak çizili görünür (s.29–31, s.36); içindeki `~~simulation/scripts/score.py~~` işareti bozulmadan
  (D-438 kilidi `tests/test_fdr_bolum4_6eylul_kaniti.py::T5a` yeşil).
- **Kusur bulundu ve düzeltildi (ilk üretim, aynı gün):** s.31 zincir madde 3'te `costmap A*` yıldızı sonraki
  `**üretim kare-bazlı boru hattı**` ile eşleşip metni italiğe çeviriyor ve başıboş `*` bırakıyordu. Kaynakta
  `A\*` yapıldı, PDF yeniden üretildi; s.31 doğru ("costmap A* → rota.json); (b) **üretim kare-bazlı boru hattı**").
  Yukarıdaki sha256 düzeltilmiş PDF'indir.
