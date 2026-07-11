# Dosya ve Kanıt Envanteri

## Ana kaynak grupları

- `codes/`: 5 model/eğitim/test scripti; yaklaşık 1.608 satır Python.
- `dataset/`: 7 indirme/dönüşüm/augmentasyon scripti ve dört JSON label seti.
- `simulation/scripts/`: dünya, algı, haritalama, navigasyon, hakem ve görev araçları.
- `simulation/plugins/`: Gazebo C++ animasyon ve kamera plugin'leri.
- `comms/`: newline JSON protokolü, UDP/serial link, sender/receiver/test.
- `drone/`: Raspberry Pi kamera/AI yayıncısı, PC izleyici ve uçtan uca ağ testi.
- `models/` ve `navitas_model/`: PT/NCNN model kopyaları.
- `doc/`: v1 model raporu, teknik sözlük, DDR metinleri ve PDF'ler.
- `results/`: gerçek görüntü/video algı artefaktları.

## Kanıt kalitesi

| İddia | Kanıt durumu |
|---|---|
| V2 PT/NCNN artefaktı var | Güçlü: dosya, metadata, commit, hash |
| V2 sınıfları 0/1 | Güçlü: metadata/YAML/kod |
| V1 mAP50 0.619 | Orta-güçlü: rapor; ham results.csv yok |
| V2 mAP | Yok |
| Gerçek video inference | Güçlü: MP4 + JSON sonuçları |
| RPi canlı yayın denemesi | Orta: kod/doküman; ham ölçüm logu sınırlı |
| 27.6 FPS | Zayıf: belge iddiası, benchmark yok |
| 300 m RF >%95 | Yok/plan |
| A* + sensör füzyonu | Yok/plan; sim farklı mekanizma kullanıyor |
| Ground-truth'suz sim haritalama | Orta: v15 log/artefakt; çoklu seed istatistiği yok |
| Tam otonom saha görevi | Yok |

## Git durumu

HEAD `594e1b0` v2 modeli ekler. Çalışma ağacı çok sayıda değiştirilmiş ve izlenmeyen dosya içerir. Rapor bu durumu değiştirmedi. Üretilmiş model, sonuç, kayıt, pycache ve doküman binary'lerinin karışması release izlenebilirliğini düşürür; model registry/release manifesti önerilir.
