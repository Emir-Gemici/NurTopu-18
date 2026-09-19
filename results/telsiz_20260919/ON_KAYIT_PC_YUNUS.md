# K8 telsiz ölçümü — ÖN KAYIT (Yunus PC, 19 Eyl 2026, ~15:00)

**Amaç:** RFD900A MAX_WINDOW 131 → 33 değişikliğinin gidiş-dönüş gecikmesine etkisini, Jetson olmadan,
Pixhawk yankısıyla (PARAM_REQUEST_READ) ölçmek. Halil'in araçları: `scripts/tezgah/sik_ayar.py`,
`scripts/tezgah/telsiz_rtt_param.py` (origin/master 950b2a07, 7aec0a1a; bu PC'ye 15:0x'te alındı).

**Ön kayıtlı beklenti (Halil, K8_NEDIR_VE_COZUMU_20260919.md §4.2):** MW33 ile p95 **133–178 ms**.
**Kapı:** p95 < **200 ms** (K8 eşiği; ölçüm K8a'nın kendisi DEĞİL, D-494 AYRIM-1'in tekrarı — tünel/Jetson zincirde yok).
**Karar kuralı:** MW33 p95, referans p95'ten en az %20 düşük değilse "etkisi yok" yazılır; eşik gevşetilmez.

**Düzen:** yer RFD900A → bu PC USB (FTDI, COMx); hava RFD900A → Pixhawk TELEM1; Pixhawk **pilden** beslenir
(USB'den değil: TX tepesi ~1 A); **pervaneler sökülü**; Mission Planner **kapalı** (COM tek sahipli);
Pixhawk USB (COM11/12) takılı kalabilir ama MP açık olmayacak.

**Sıra (her adımın çıktısı bu klasöre):**
0. `list_ports` → yeni COM (VID 0403 FTDI) not edilir.
1. `sik_ayar.py --port COMx --dokum --cikti 01_once.json` — yerel+uzak tam döküm (kanıt: yalnız MAX_WINDOW değişecek).
2. `telsiz_rtt_param.py --port COMx --n 120 --etiket referans_MW131 --json --cikti 02_referans.json`
3a. `sik_ayar.py --port COMx --yaz MAX_WINDOW=33 --uzak-da` — **yeniden başlatma YOK** (araç RT yazma cevabını
    doğrulamıyor; ATZ'den önce kontrol şart — D-479 dersi).
3b. `sik_ayar.py --port COMx --dokum --cikti 03a_yazim_sonrasi.json` — yerel VE uzak MAX_WINDOW=33 görülmeden 3c'ye geçilmez.
3c. `sik_ayar.py --port COMx --yaz MAX_WINDOW=33 --uzak-da --yeniden-baslat` — değerler zaten 33 → yalnız RTZ + ATZ.
    Geri alma: `--yaz MAX_WINDOW=131 --uzak-da` (aynı 3a/3b/3c sırası).
4. `sik_ayar.py --port COMx --dokum --cikti 03_sonra.json` + `telsiz_rtt_param.py ... --etiket MW33 --cikti 04_mw33.json`
5. Fark tablosu: p50/p90/p95/p99/maks/kayıp — referans vs MW33. Yorum ön kayıtla karşılaştırılır.

**Kapsam dışı (ayrı test):** video telemetri telsizden geçmez (Jetson Wi-Fi/LAN HTTP 8080 → `yks_gui --kamera-url`).
