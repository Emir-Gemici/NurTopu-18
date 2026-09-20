# Kamera → model teşhisi — 20 Eylül 2026

## Sonuç

Bu aşamada kod değişikliği yapılmadı. Sorun moiré olarak doğrulanmadı.
Kamera köprüsü `/kare.jpg` üzerinden gerçek kare veriyor ve aynı Jetson Python/OpenCV
ortamında `/video` açılıp kare okunabiliyor. Model süreci daha sonra kare işlemeye
başladı; buna rağmen görev kayıtlarında sürekli `MASKE_YOK`, `yol: null` ve
`guven: 0.0` görülüyor.

## Kanıt

- Kamera köprüsü: `kaynak_acik: true`, `1280x720`, yaklaşık `10 FPS`.
- Doğrudan OpenCV denemesi: `VideoCapture("http://127.0.0.1:8080/video")` →
  `opened True`; üç ardışık kare `True`, `(720, 1280, 3)`.
- Model süreci: `navitas-rpi-inference` active, `NRestarts=0`; güncel kayıtta
  kare sayacı ilerliyor.
- Güncel görev kayıtlarında örnek: `red: MASKE_YOK`, `zemin_px: 0`, `yol: null`.
- Tek kare görselinde merkezi yol ve çevresindeki molozlar görünür; düzenli,
  baskın bir moiré ızgarası gözlenmedi. Mor kenar bandı/renk kayması optik veya
  ISP kalibrasyonu şüphesini açık bırakıyor.
- Bir erken açılışta `KAMERA_BEKLIYOR / KAMERA_ACILAMADI` kaydı oluştu; köprü
  hazır olmadan başlayan inference süreci için yeniden bağlanma davranışı ayrıca
  incelenmeli. Sonraki süreçte kare işleme başladı.

## Emir'in incelemesi için açık ayrımlar

1. `MASKE_YOK` gerçekten modelin bu kadrajı reddetmesi mi, yoksa inference'ın
   kullandığı `/video` karelerinin `/kare.jpg` ile aynı nesil olup olmadığı mı?
2. Güncel tek kare üzerinde v36 modelinin düşük güven çıktıları ve maske sayısı
   doğrudan yazdırılmalı; yalnız üretim özetindeki `MASKE_YOK` yeterli ayrım değil.
3. Kamera köprüsü hazır olmadan inference başlatılıyorsa, systemd bağımlılığı veya
   tüketici yeniden denemesi ölçülmeli.
4. Mor kenar bandı, odak ve lens gölgeleme kalibrasyonu aynı sahnede ayrı ayrı
   ölçülmeli; moiré hükmü bu kontroller yapılmadan verilmemeli.

Bu kayıt teşhistir; üretim kodu, Jetson servisi ve eşikler değiştirilmemiştir.
