# 5 EYLÜL — JETSON GÜN-1 KONTROL LİSTESİ (B4)

> 🟢 **6 Eylül 2026 sonucu — Jetson Orin Nano Developer Kit 4 GB (D-431).** Kart Nano değil Orin
> Nano çıktı (JetPack 7.2.1 / Python 3.12); liste bu kartta koşuldu, ham çıktılar paket `kanit/`
> (depoda `results/jetson_20260906/`): §1 sürümler kaydedildi (`ORTAM_KUNYESI.txt`) · §3 engine
> **`.pt`'den** derlendi (⚠ ONNX'ten `yolo export … format=engine` **çalışmaz**), 57 283 989 B,
> sha256 `bb9bd868…0300`, deftere `--turev-kaydet` ile yazıldı · §4 denklik: F1 **0** · F2 **0,9953**
> GEÇTİ, D-303 oransal **3/126 DÜŞTÜ** (küme `arena_kompozit_v2`, T66 değil) → **uçuş `.pt`**, engine
> üretime alınmadı · §5 FPS (120 örnek): pt p50/p95 **1,35/1,06** · engine **1,58/1,33** ≥ 0,61 GEÇTİ
> · §6 10 dk sürekli koşum tamamlandı (900 örnek; toplam p50/p95 pt 770/922 ms · engine 649/765 ms,
> `rapor.md`; termal hüküm tutanak §5) · §7 kamera **ÖLÇÜLEMEDİ** (CSI kamera takılı değildi) ·
> Pixhawk **ÖLÇÜLEMEDİ**. Tutanak: `JETSON_ORIN_NANO_KURULUM.md`.

> Amaç: kartın geldiği gün **keşif yapılmaz**. Her adım önceden yazılmış bir
> eşiğe karşı **doğrulamadır**. Ayrıntı `JETSON_KILAVUZ.md`'de; bu liste sıra
> ve kapıdır. Bir kapı düşerse **durulur ve düşüş raporlanır** — sonraki adıma
> "belki düzelir" diye geçilmez.
>
> Eşiklerin kaynağı: `results/b4_fps/ON_KAYIT.md` (2026-08-31, D-107) ve
> ölçülen `results/b4_fps/p_ve_kosu_20260901.json`. FPS eşiği artık plandaki
> gerekçesiz "0,9–2,6" bandı DEĞİLDİR; `GEREKLI_FPS = 1/(5·p)` türetimidir.

## SIFIRINCI kapı — karta dokunmadan önce (PC'de, 5 Eylül'den ÖNCE bitmiş olacak)

- [x] `p` ölçümü kapandı, hüküm defterde (**D-374**: FPS sorusu kapandı —
      gereken 0,41, band 0,9; G1 sahne bağıntılı 51 s körlük ÖNER-BEKLE).
- [x] FP16 ↔ FP32 **rota kararı** denkliği PC'de ölçüldü (**D-375**: F1/F2
      GEÇTİ; ilk ölçümün vakum çıkışı yakalandı, koruma artık kodda).
- [x] ONNX → TRT dönüşüm provası: **ÖLÇÜLEMEDİ** (PC'de TRT çalışma zamanı
      yok; ORT CPU'ya düştü ve betik bunu "döndü" saymadı). Bu ön koşul
      PC'de ÜRETİLEMEZ — dönüşüm kanıtı bütünüyle §3'ün (T16) işidir ve
      Gün-1'i bloklamaz.
- [ ] Yukarıdaki ilk iki madde işaretli değilse Gün-1 **başlamaz**.

## 1 · İlk 10 dakika — sürümler ve güç (KILAVUZ §1)

- [ ] JetPack/L4T, TensorRT, CUDA/cuDNN sürümleri not edildi (§1a–1c).
- [ ] **Güç modu MAKSİMUM** (§1 "güç modunu maksimum yap") — yoksa her FPS
      sayısı yalan söyler.
- [ ] `tegrastats` açık bir pencerede akıyor (termal için kanıt).

## 2 · Paket ve bütünlük (KILAVUZ §2–3)

- [ ] Paket kopyalandı; `test_t202_jetson_paket_butunlugu` mantığındaki
      dosya listesi elle kontrol edildi.
- [ ] `navitas_seg_v36_best.pt` sha256 == defterdeki
      `1d1caca6...cac46911` (registry `profiles.competition.sha256`).
- [ ] `navitas_seg_v36_best_512_fp16.onnx` mevcut.

## 3 · `.engine` derleme — T16 (KILAVUZ §4)

- [ ] FP16 engine derlendi (D-371 kararı: **FP16**; INT8 Gün-1'de YOK,
      KILAVUZ §6 "sırayla" kuralı).
- [ ] Kapı T16: `.engine` oluştu **ve** tek kare çıkarım hatasız (§4 sonu).
- [ ] 🔴 Registry'ye yaz: `turevler["navitas_seg_v36_best_512_fp16.engine"].sha256` (6 Eylül'de YAZILDI: `bb9bd868…0300`, D-431; FP32 girdisi defterden çıkarıldı, K4)
      alanındaki `DERLENINCE_YAZILIR` gerçek sha256 ile değiştirildi.
      ⚠ 6 Eylül (D-431): yazılan girdi **`navitas_seg_v36_best_512_fp16.engine`** (derlenen
      FP16); FP32 `navitas_seg_v36_best.engine` girdisi 7 Eylül'de defterden ÇIKARILDI (D-431 K4; derlenmedi, gerekmiyor) — mühür artık bunu istemez
      defterden çıkarılır ya da derlenir (D-431 K4, mimar kararı).
- [ ] `jetson_fps.py` fail-closed denetimi yeniden koşuldu → `eslesti`.

## 4 · Doğruluk — hız ölçmeden ÖNCE (sıra bilinçli: yanlış cevabı hızlı vermek başarı değil)

- [ ] `test_goruntuleri/` üzerinde `.engine` çıktısı ↔ PC referans kararları:
      **rota kararı (şerit no) birebir aynı mı?** Maske IoU değil, KARAR.
- [ ] Uyuşmazlık varsa: sayı kaydedilir, Gün-1 FPS'e geçilir ama hüküm
      "DOĞRULUK DÜŞTÜ" olarak açılır; FP16 kararı (D-371) yeniden açılır.

## 5 · FPS — T17 (KILAVUZ §5) · eşik ÖNCEDEN YAZILDI

- [ ] `jetson_fps.py` uçtan uca (kare okuma + çıkarım + get_masks + costmap).
- [ ] Karşılaştırma **yalnız** şu eşiğe karşı:
      `hukum.gerekli_fps_R` ve `hukum.gerekli_fps_S`
      (`results/b4_fps/p_ve_kosu_20260901.json`).
      İki sayının BÜYÜĞÜ esas alınır (kötümser taraf).
- [ ] p50 ve p95 FPS ayrı yazılır — tek ortalama D-373'ün dersi gereği yasak
      (tek kare ortalamayı %36 oynatabiliyor).

## 6 · Sürekli koşum — şartname görev süresi

- [ ] **10 dakika kesintisiz** koşum (şartname üst sınırı) · `tegrastats`
      kaydı ile.
- [ ] İlk 1 dk FPS'i ↔ son 1 dk FPS'i: düşüş > %15 ise TERMAL bayrağı.

## 7 · Kamera hattı (varsa) — H3 (KILAVUZ §6B)

- [ ] `kamera_dogrula.py` koşuldu.
- [ ] 🔴 **AYNA TESTİ** (D-349/T201): kadraja SOL kenardan bir nesne sokulur,
      ekranda SOL kenarda görünmek ZORUNDA. Ters görünüyorsa hiçbir şey
      koşulmaz — flip kusuru şartname §2.1'de sıfır puandır.

## 8 · Rapor (KILAVUZ §7)

- [ ] JSON çıktılar + `tegrastats` kaydı + registry diff'i geri getirilir.
- [ ] Defter kaydı: her kapının GEÇTİ/DÜŞTÜ/ÖLÇÜLEMEDİ durumu — üçlü durum,
      `OLCULEMEDI != GECTI`.

## Gün-1'de YAPILMAYACAKLAR (KILAVUZ §9 + B4 ekleri)

- INT8/Q8 denemesi (D-371: FP16; INT8 ancak FP16 eşiği geçemezse ve AYRI günde).
- Model değiştirme/yeniden eğitim kararı.
- Eşik gevşetme: sayı eşiği geçmiyorsa **geçmiyordur** (D-107).
