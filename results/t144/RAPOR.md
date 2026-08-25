# T144 — poligon tavani ALAN sirali (2026-08-26)

Kod: `dataset/download_and_convert.py` — `poligon_alani()`, `alana_gore_kirp()`; `process_split` artik tavani asan maskeleri sayar ve bolum sonunda loglar (`*_tavan_asan`, `*_atilan_alan_px`, `*_atilan_poligon`, `*_alan_px`).
Test: `tests/test_t144_kirpma.py` (4 test; mutasyon `key=len(t[1])` -> 2 test duser).

## Olcum (rescuenet_ham TAM kume, 512x512 NEAREST, salt okuma) — `olcum_kirpma.py` -> `olcum_kirpma.json`
| bolum | blocked tavan(15) asan | etiket degisen | ters sira | atilan alan len(l) | atilan alan ALAN |
|---|---|---|---|---|---|
| train | 21/3595 | 21 | 21/21 | %31,6 | %1,1 |
| val | 0/449 | 0 | 0 | – | – |
| test | 3/450 | 3 | 3/3 | %38,2 | %0,5 |
road tavani (30) hicbir bolumde asilmadi. En kotu: 13077_lab.png %90,4 (94.997 px'in 85.895'i); test 13076_lab.png %91,2. D-284 sayilari bire bir yeniden uretildi.

## (4) HF girdisi — `hf_girdi_kontrol.py` -> `hf_girdi_kontrol.json` (cevrimdisi onbellek, 3 bolum x ~200 ornek)
Etiket degerleri yalniz {0, 7, 8}; 512x512. Yani betigin GERCEK girdisinde bina/agac/su/arac id'leri YOK -> T54 eslemesi (BLOCKED_HAM 9 id) fiilen yalniz 8'i yakalar; "bilinmeyen -> engel" dersi HF girdisinde TETIKLENMEZ (o sinif pikselleri 0=arka plan, etiketsiz kalir). D-284'un notu DOGRU. T54'un hedefi icin girdi rescuenet_ham (41+57 zinciri) olmali.

## Yeniden uretim (KOSULMADI — egitim GPU'da)
`rescuenet_2sinif_engelli` 41+57 zinciriyle uretilir ve 41 zaten alan sirali -> T144 degisikligi o kumeyi ETKILEMEZ. Etkilenen tek cikti `rescuenet_yolo`dur:
`O:\navitas-local-train\venv\Scripts\python.exe dataset\download_and_convert.py --temizle`
Beklenen etki: HF girdisinde tavani asan maskeler icin (train ~21, test ~3; HF'de yalniz sinif 8 engel oldugu icin sayi daha dusuk olabilir) buyuk engel poligonlari korunur; diger tum etiketler bayt-es kalir. Tarihsel karisimlarin (v21-v27) girdisi oldugundan --temizle karari mimarindir.
