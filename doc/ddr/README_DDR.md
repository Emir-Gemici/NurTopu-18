# DDR — SENİN YAPACAKLARIN (basit kontrol listesi)

Teslim: **15 Temmuz 2026** · DDR = rapor puanının %25'i · Bölüm 3 = 60/100 puan.

## Bu klasörde ne var?

| Dosya | Şablonda gideceği yer |
|---|---|
| `bolum1_ozet_otonomi.md` | Bölüm 1 Özet'in otonomi/yazılım paragrafı |
| `bolum3_3_1_gorev_akis_ariza.md` | Bölüm 3.3.1 (görev akışları + arıza emniyet — yazılım kısmı) |
| `bolum3_3_5_yazilim.md` | **Bölüm 3.3.5'in TAMAMI** (Yazılım Altyapısı + Görüntü İşleme + Haberleşme) |
| `bolum4_test_yazilim.md` | Bölüm 4'ün yazılım/algı/haberleşme/sim test tabloları |
| `bolum5_moc_yazilim.md` | Bölüm 5 izlenebilirlik matrisinin yazılım satırları |
| `gorseller/*.png` | Metinlerde [GÖRSEL: ...] işaretli yerlere (5 hazır şema) |

## Adım adım (sırayla, ~yarım gün)

1. **Word şablonunu aç**, yukarıdaki 5 dosyayı ilgili bölümlere kopyala-yapıştır
   (Markdown tabloları Word'e yapıştırınca tablo olur; olmazsa "Metni Tabloya
   Dönüştür").
2. ~~`[DOLDUR]` işaretleri~~ → **v4.1'de kapatıldı** (11 Tem):
   - v2 gerçek metrikleri model dosyasının içinden çıkarıldı (mask mAP50 0,595);
     eğitim ayarları (AdamW/0,001, imgsz 512) checkpoint'ten doğrulandı.
   - REQ numaraları takım şartname özetinden eşlendi; **kalan 4 "REQ-__" satırı**
     resmî gereksinim setinden doldurulacak + eşlenenler son kontrol edilecek.
3. **Görselleri ekle:** `gorseller/` içindeki 5 şema + şunların ekran görüntüleri:
   - `simulation/harita_onizleme/haritalar_orta.png` (test sahaları)
   - v15 `iha_scan_kolay/ortomozaik.jpg` + `algi.jpg` (İHA haritası + model kararı)
   - RPi canlı yayın fotoğrafı (telefonla ekran fotoğrafı yeterli)
4. **Mekanik/aviyonik ekibe BUGÜN ilet** (onların bölümleri bizden büyük):
   - Bölüm 3.1 (12 alt başlık, CS-VLA hesapları!) + 3.2 (yapısal/FEM/BOM,
     mancınık enerji denklemi + yay sabiti) + 3.3.2–3.3.4 (donanım/kablo/güç).
   - Bölüm 2.1 org şemasında **İSİM OLMAYACAK** (rol bazlı) — ÖDR'dekini
     kopyalama, isimleri sil.
5. Bitmiş Word'ü PDF yap → **Drive'a yükle** → takım kontrolü → teslim sistemine.

## Dikkat (puan yakmasın)
- Haberleşme frekansı raporda **433 MHz** yazacak (takım kararı 12.07; resmî
  şartname bant belirtmiyor — eski "şartname uyarınca 915" ifadeleri düzeltildi).
- Bölüm 2.2'de "ÖDR takvimine uygunluk teyit edilmiştir" cümlesi + varsa
  değişiklikler gerekçeli.
- Bölüm 5'e pasta grafik şart (hazır: `gorseller/moc_pasta.png` — 5 karşılandı / 6 sürüyor / 1 planlandı; v2 metrik düzeltmesi sonrası güncellendi).

## Sürüm düzeni (11 Tem itibarıyla)
- Her sürüm kendi klasöründe: `word/v4/`, `word/v4.1/`, `word/v4.2/` ...
- **GÜNCEL TESLİMAT: `word/v4.2/Navitas_DDR_Yazilim_v4.2.odt`** (20 sf; .html
  kaynak + .pdf önizleme yanında). v4.2 = bağımsız v2 yeniden ölçümü
  (11.07.2026, Colab): sınıf bazlı metrikler (traversable 0,868 / blocked
  0,322), FloodNet dürüstlük notu, kanıt klasörü `results/v2_val_20260711/`.
  v4.1 farkı: gerçek v2 metrikleri, REQ numaraları, oran-korumalı görseller.
