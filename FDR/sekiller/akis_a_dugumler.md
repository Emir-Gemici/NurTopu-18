# Akış diyagramı (a) — düğüm → dosya:satır tablosu

Kaynak: `FDR/sekiller/akis_a.mmd` · koddan türetildi: commit `4ee70d9`, 2026-09-10 · üretici: `scripts/akis_diyagram_dogrula.py --tablo`

Düğüm kuralı: **fonksiyon** = `def ad()` ve satır o tanımın başı; **karar** = koşul metni koddan birebir; **blok** = deyim koddan birebir. Doğrulama sütunu: `tam` = tam satır, `±n` = n satır sapma (tolerans 3). Başka düğüm tipi yoktur.

| # | düğüm | tür | alt-grafik | metin | dosya:satır | doğrulama |
|---|---|---|---|---|---|---|
| 1 | `sA1` | fonksiyon | — | `def main()` | `codes/rpi_inference.py:2705` | tam |
| 2 | `a02` | karar | sA1 | `if not any([args.fps, args.image, args.video, args.camera]):` | `codes/rpi_inference.py:2709` | tam |
| 3 | `a03` | blok | sA1 | `parser.print_help()` | `codes/rpi_inference.py:2710` | tam |
| 4 | `a04` | fonksiyon | sA1 | `def _argumanlari_dogrula()` | `codes/rpi_inference.py:2672` | tam |
| 5 | `a05` | fonksiyon | sA1 | `def _ub_referansi_coz()` | `codes/rpi_inference.py:2583` | tam |
| 6 | `a06` | karar | sA1 | `if args.mavlink is not None:` | `codes/rpi_inference.py:2719` | tam |
| 7 | `a07` | fonksiyon | sA1 | `def CanliOlcekSaglayici.baglan()` | `codes/rpi_inference.py:316` | tam |
| 8 | `a08` | karar | sA1 | `if args.yks_hedef or args.ika_hedef or args.telsiz_seri:` | `codes/rpi_inference.py:2745` | tam |
| 9 | `a09` | fonksiyon | sA1 | `def yayinci_kur()` | `comms/iha_sender.py:514` | tam |
| 10 | `a10` | fonksiyon | sA1 | `def _durdurma_sinyallerini_kur()` | `codes/rpi_inference.py:2089` | tam |
| 11 | `a11` | fonksiyon | sA1 | `def load_model()` | `codes/rpi_inference.py:701` | tam |
| 12 | `a12` | karar | sA1 | `if args.arac_modeli is not None:` | `codes/rpi_inference.py:2789` | tam |
| 13 | `a13` | karar | sA1 | `elif args.camera:` | `codes/rpi_inference.py:2806` | tam |
| 14 | `sA2` | fonksiyon | — | `def run_camera()` | `codes/rpi_inference.py:2298` | tam |
| 15 | `a14` | fonksiyon | sA2 | `def kamera_kaynagi_coz()` | `codes/rpi_inference.py:555` | tam |
| 16 | `a15` | karar | sA2 | `if not cap.isOpened():` | `codes/rpi_inference.py:2316` | tam |
| 17 | `a16` | blok | sA2 | `return {"bitis": KAMERA_BITIS_ACILAMADI, "okunan": 0,` | `codes/rpi_inference.py:2318` | tam |
| 18 | `a17` | blok | sA2 | `yumusatici = KararYumusatici()` | `codes/rpi_inference.py:2329` | tam |
| 19 | `a18` | karar | sA2 | `for frame in kamera_kareleri(cap, ozet):` | `codes/rpi_inference.py:2335` | tam |
| 20 | `a19` | karar | sA2 | `if durdurma_istendi():` | `codes/rpi_inference.py:2339` | tam |
| 21 | `a20` | fonksiyon | sA2 | `def _preprocess()` | `codes/rpi_inference.py:1892` | tam |
| 22 | `a21` | blok | sA2 | `results = model.predict(small, imgsz=INFER_SIZE, conf=conf, verbose=False)` | `codes/rpi_inference.py:2360` | tam |
| 23 | `a22` | fonksiyon | sA2 | `def get_masks()` | `codes/rpi_inference.py:744` | tam |
| 24 | `a23` | fonksiyon | sA2 | `def _maskeleri_icerige_kirp()` | `codes/rpi_inference.py:1919` | tam |
| 25 | `a24` | fonksiyon | sA2 | `def kare_olcek_kahini()` | `codes/rpi_inference.py:453` | tam |
| 26 | `a25` | fonksiyon | sA2 | `def rota_olcek_reddi()` | `codes/karar_sozlesmesi.py:439` | tam |
| 27 | `a26` | fonksiyon | sA2 | `def analyze_path()` | `codes/rpi_inference.py:1352` | tam |
| 28 | `a27` | karar | sA2 | `if olcek_reddi is not None and karar_reddi is None:` | `codes/rpi_inference.py:2390` | tam |
| 29 | `a28` | blok | sA2 | `open_path, path_conf, waypoints = None, 0.0, []` | `codes/rpi_inference.py:2391` | tam |
| 30 | `a29` | fonksiyon | sA2 | `def _rota_kararini_esikle()` | `codes/rpi_inference.py:1779` | tam |
| 31 | `a30` | karar | sA2 | `if yumusatici.suz(open_path, karar_reddi):` | `codes/rpi_inference.py:2399` | tam |
| 32 | `a31` | fonksiyon | sA2 | `def KararYumusatici.suz()` | `codes/karar_sozlesmesi.py:2172` | ±1 |
| 33 | `a32` | fonksiyon | sA2 | `def _karari_yayinla()` | `codes/rpi_inference.py:285` | tam |
| 34 | `a33` | karar | sA2 | `if ekransiz:` | `codes/rpi_inference.py:2403` | tam |
| 35 | `a34` | fonksiyon | sA2 | `def draw_masks()` | `codes/rpi_inference.py:856` | tam |
| 36 | `a35` | karar | sA2 | `if cv2.waitKey(1) & 0xFF == ord("q"):` | `codes/rpi_inference.py:2420` | tam |
| 37 | `a36` | blok | sA2 | `cap.release()` | `codes/rpi_inference.py:2425` | tam |
| 38 | `a37` | fonksiyon | sA2 | `def kamera_bitis_raporu()` | `codes/rpi_inference.py:2485` | tam |
| 39 | `sA3` | fonksiyon | — | `def kamera_kareleri()` | `codes/rpi_inference.py:2432` | tam |
| 40 | `a40` | karar | sA3 | `if durdurma_istendi():` | `codes/rpi_inference.py:2459` | tam |
| 41 | `a41` | blok | sA3 | `ret, frame = cap.read()` | `codes/rpi_inference.py:2465` | tam |
| 42 | `a42` | karar | sA3 | `if not ret or frame is None:` | `codes/rpi_inference.py:2466` | tam |
| 43 | `a43` | karar | sA3 | `if ardisik >= ust_sinir:` | `codes/rpi_inference.py:2470` | tam |
| 44 | `a44` | blok | sA3 | `yield frame` | `codes/rpi_inference.py:2482` | tam |
| 45 | `sA4` | blok | — | `finally:` | `codes/rpi_inference.py:2817` | tam |
| 46 | `a50` | fonksiyon | sA4 | `def _durdurma_sinyallerini_geri_al()` | `codes/rpi_inference.py:2116` | tam |
| 47 | `a51` | karar | sA4 | `if yayinci is not None:` | `codes/rpi_inference.py:2819` | tam |
| 48 | `a52` | blok | sA4 | `yayinci.sender.link.close()` | `codes/rpi_inference.py:2825` | tam |
| 49 | `a53` | karar | sA4 | `if canli_olcek is not None:` | `codes/rpi_inference.py:2826` | tam |
| 50 | `a54` | fonksiyon | sA4 | `def CanliOlcekSaglayici.kapat()` | `codes/rpi_inference.py:375` | tam |
| 51 | `a01` | fonksiyon | — | `def _arguman_ayristirici()` | `codes/rpi_inference.py:2492` | tam |

Toplam 51 düğüm — blok: 10 · fonksiyon: 24 · karar: 17 · tam satır: 50/51
