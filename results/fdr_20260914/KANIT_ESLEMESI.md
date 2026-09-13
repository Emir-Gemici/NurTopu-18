# FDR adım 1–2 — mevcut kanıt eşlemesi, 14 Eylül 2026

Yazan: Codex-1. Bağımsız denetim bekliyor. Kaynak `envanter.json`; yöntem dosya varlığı, SHA-256 ve XML okumasıdır. Yeni simülasyon veya saha ölçümü yapılmadı.

| Kanıt | Raporda kullanılacağı yer | Neyi karşılar / sınırı |
|---|---|---|
| Üç CAD dışa aktarım paketi ve `results/gazebo_model_onizleme_20260913/` | Bölüm 3 §3.1, §3.3.3.1 | CAD türevleri ve Gazebo önizlemesi mevcut. Uçuş/yapısal analiz veya CAD ile tam görev kanıtı değil. |
| `results/gazebo_realism_20260910/` | Bölüm 3 §3.3.3 | Zemin/moloz görselleri, sınırlı temas deneyleri mevcut. Statik aday; araç ve tüm saha fiziği kalibre edilmedi. |
| `results/fdr_sprint_20260910/H1/README_T214A.md` | Bölüm 3 §3.3.3.2, Bölüm 4 §4.7 | Tarihli MuJoCo ölçümleri: yer gerçeği 45/45; üretim modeli 9/45; üretim boru hattı 0/15. Sonuçlar ve eşikler değiştirilmez. |
| `results/fdr_sprint_20260910/video/OKUBENI.md` | Bölüm 3 §3.3.3.3 | 10 Eylül video üretim kaydı ve hash var; MP4 bu çalışma kopyasında belirtilen yolda yok. Dosyanın geri getirilmesi + hash doğrulaması + erişilebilir link açık. |
| `simulation/recordings/rv38/` | Bölüm 3 §3.3.3, Bölüm 4 §4.7 | 13 Eylül Gazebo denemesi tamamlanmamış; MP4 yok, hakem günlüğü 0 bayt, model yükleme FileNotFoundError. Üç seviye başarımı türetilemez. |

İKA URDF'sinin yazılı toplamı 7,5598 kg; bu dosya okuması tartı doğrulaması değildir. MuJoCo ölçümü 9,40 kg modelle üretildi. GAZEBO oturumunda 7,56 kg ardından “9,3 kg toplam” ifadesi var; nihai kütlenin kaynağı netleşmeden fizik girdileri veya eski sonuçlar değiştirilmez. Kütle merkezi için yalnız Z sayısının zarf yüksekliğinden büyük olması kusuru tek başına kanıtlamaz: link, mesh ve montaj koordinat dönüşümleri birlikte doğrulanmalıdır.

Başlangıçta mevcut FDR satır-atfı düzeltmeleri ve `tests/test_fdr_t244_ic_celiski.py` değişikliği korunmuştur; bu işe ait test yazarlığı olarak sayılmaz.
