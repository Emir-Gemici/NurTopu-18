# K8 telsiz ölçümü — SONUÇ (Yunus PC, 19 Eyl 2026, 15:05–15:20)

Yöntem: `scripts/tezgah/telsiz_rtt_param.py` (PARAM_REQUEST_READ yankısı, 120 prob, 0,25 s aralık, 0,5 s zaman aşımı), yer RFD900A COM7, hava RFD900A Pixhawk TELEM1, Pixhawk pilde, MP kapalı, Jetson açık (TELEM2). Ön kayıt: `ON_KAYIT_PC_YUNUS.md`.

| # | durum (yer / hava MAX_WINDOW) | p50 | p90 | p95 | p99 | maks | kayıp | dosya |
|---|---|---|---|---|---|---|---|---|
| 2 | 33 / 131 (bulunduğu hâl) | 153,9 | 204,4 | **229,0** | 230,3 | 230,6 | %0 | 02_mevcut_mw33.json |
| 4 | 33 / 131 (tekrar; uzak yazım tutmamıştı) | 154,0 | 205,7 | 230,6 | 251,1 | 256,5 | %0 | 04_tekrar_yer33_hava131.json |
| 4 | 33 / 33 (yazıldı, yeniden başlatılmadı) | 153,2 | 205,3 | 230,3 | 255,1 | 256,1 | %0 | 04_mw33_ikisi.json |
| 4b | **33 / 33, ikisi yeniden başlatıldı, dökümle doğrulandı** | **128,5** | **179,8** | **204,9** | 230,4 | 230,9 | %0,83 (1/120) | 04b_mw33_ikisi_reboot.json |

- Referans (D-494 AYRIM-1, 131/131): p95 231 ms. Bugünkü 33/131 hâli de 229–231 → **tek tarafı değiştirmek etkisiz**; parametre ancak iki tarafta ve yeniden başlatmadan sonra etki eder.
- Etki: p50 −17 %, p95 **−11 %** (229 → 205). Ön kayıtlı beklenti (133–178) **tutmadı**; karar kuralı (≥ %20 düşüş) **sağlanmadı** → "sınırlı etki". Kapı 200 ms → **DÜŞTÜ (5 ms ile)**. Eşik gevşetilmedi.
- Dağılım: min 77, p50 128, p95 205, maks 231 → ~77 ms'lik basamaklar; taban telsiz TDM turu + Pixhawk cevap gecikmesi. MAX_WINDOW tek kaldıraç değil.
- Karar (kullanıcıya): 33/33 **kalsın** (kayıp artmadı, gecikme düştü). Geri alma: `RTS15=131`, `RT&W`, `RTZ`; sonra `ATS15=131`, `AT&W`, `ATZ`.
- Yan bulgular: RADIO_STATUS hiç enjekte edilmiyor (RSSI ölçülemez; loglarda RAD yok); RT okuması aralıklı (5 denemede 2 cevap yok, 8 s bekleme ile); `sik_ayar.py` ATO sonrası okuma döngüsünde asılı kalıyor (`_oku_hepsi` veri geldiği sürece süreyi uzatıyor; telemetri sürekli akıyor).
- **GCS failsafe testi (aynı oturum):** PC 5 s heartbeat gönderip kesti; 25 s'de "GCS Failsafe" YOK; telsizden Jetson MAVProxy heartbeat'i (sysid 255, comp 230) görünüyor → Jetson açıkken RFD boşlukları failsafe üretmez. **GEÇTİ.**
- **TUNNEL mesajı: 0** (toplam ~90 s dinleme) → Jetson tünel yayını yok. K8a/K8b, YKİ rota akışı ve tünel testi bu düzelmeden yapılamaz; Jetson'a ağ erişimi gerekir.
