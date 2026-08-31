# B4 — "Kaç FPS yeterli?" · ön kayıt

Tarih: **2026-08-31**

Bu metin, **hiçbir `p` ölçümü ve hiçbir Jetson FPS sonucu üretilmeden önce**
yazılmıştır. Sonuç görüldükten sonra eşik, örneklem ya da geçme ölçütü
değiştirilmez (D-107).

---

## 0. Neden bu ön kayıt gerekiyor

`FDA_PLANI_20260829.md` §B4 şunu diyor:

> *"0,9–2,6 FPS verilemezse karar yeniden açılır."*

**Bu eşiğin nereden geldiği depoda hiçbir yerde yazılı değildir.** Eşik
türetilmeden Jetson'dan gelecek gerçek FPS sayısı **hükme bağlanamaz**:
ölçülür ama "geçti mi kaldı mı" denemez. `OLCULEMEDI != GECTI` kuralının
FPS'teki karşılığı budur.

---

## 1. Türetme — eşik şartnameden ve SÖZLEŞMEDEN gelir, tahminden değil

1. **Şartname §2.2.3 / §6.4:** açık güzergâh YKS'ye *gerçek zamanlı*
   aktarılmalı ve Alan Hakemi monitörden izlemelidir; **hakem onayı alınmayan
   tespit geçersizdir** → uçuş geçersiz.
2. **Sözleşme (`codes/karar_sozlesmesi.py:159`):** `YKS_TESPIT_TAZELIK_S = 5.0`.
   Karar kutusu 5 s tazelenmezse **onay düğmesi düşer** (D-317 / T169).
3. **Karar kare başınadır:** `_karari_yayinla` ana döngüde her karede çağrılır
   (`codes/rpi_inference.py:2101, 2207`). **Kareler arası uzlaşma/oylama
   mekanizması YOKTUR** — arandı, bulunamadı.

⇒ Gereken şey *işlenmiş kare* değil, **başarılı tespit**tir. `p` = bir karenin
geçerli rota yayınlama olasılığı ise:

```
GEREKLI_FPS  ≥  1 / (YKS_TESPIT_TAZELIK_S × p)  =  1 / (5 · p)
```

| p | gereken FPS |
|---:|---:|
| 1,00 | 0,20 |
| 0,50 | 0,40 |
| 0,25 | 0,80 |
| 0,10 | **2,00** |
| 0,05 | **4,00** |

⚠ Planın bandının alt ucu **0,9 FPS**. Yani `p < 0,22` ise **plandaki band
yetmez** ve FP16 kararı (D-371) FPS'ten bağımsız olarak yeniden açılır.
**Bu bağlantı planda yoktu.**

---

## 2. 🔴 FPS ARTIRMANIN ÇÖZEMEYECEĞİ HÂL — asıl ölçülecek şey bu

Yukarıdaki tablo, başarısızlıkların **örnekleme kaynaklı** ve kareler arası
**bağımsız** olduğunu varsayar. Gerçekte kareler yüksek bağıntılıdır: İHA'nın
model tarafından görülemeyen bir bölge üzerinde olduğu bir aralıkta, **daha
hızlı koşmak yeni bilgi getirmez** — aynı sahne daha çok kez düşer.

⇒ **Ayırt edici soru:** başarısızlık koşuları *sahne bağıntılı* mı, *örnekleme
bağıntılı* mı?

- **Örnekleme bağıntılıysa** → FPS artırmak çözer, B4 bir hız sorunudur.
- **Sahne bağıntılıysa** → FPS **çözmez**; sorun model/irtifa/yörüngededir ve
  Jetson ne kadar hızlı olursa olsun uçuş geçersiz olabilir.

Bu ayrım **Jetson'sız ölçülür** ve B4'ün gerçek riskidir.

---

## 3. Dondurulan ölçüm

Üretim çağrı sırası birebir taklit edilir (D-351):
`_preprocess` → `model.predict(small, imgsz=INFER_SIZE, conf=0.30)` →
`get_masks(results, …)` (**results LİSTE**) → `_maskeleri_icerige_kirp` →
`analyze_path(...)`.

Model: **v36** (`navitas_seg_v36_best.pt`) — üretim modeli, defterden okunur.

**İki küme ayrı ayrı ölçülür ve ayrı ayrı raporlanır** (birleştirilmez):

| küme | ne | niçin |
|---|---|---|
| **S** | `sentetik_arena_kadraj_t66` kabul kümesi | göreve benzer, ama **sentetik** |
| **R** | `results/dji_20260822/kareler_1fps/` gerçek DJİ kareleri | **gerçek**, ama arenaya göre OOD |

Ölçülecekler (her küme için):
1. `p` = geçerli rota yayınlanan kare / toplam kare.
2. **Ardışık başarısız kare koşusu** dağılımı: `maks`, `p50`, `p95`.
3. R kümesi **1 fps** çıkarıldığı için orada **1 koşu karesi = 1 saniye**;
   koşu uzunluğu doğrudan saniye cinsinden tazelik boşluğudur.

---

## 4. Eşikler — SONUÇ GÖRÜLMEDEN yazıldı

- **G1 (taban):** R kümesinde en uzun başarısız koşu **< 5 kare (= 5 s)** ise,
  **1 FPS** tazelik kuralını o görüntü üzerinde karşılar; Jetson bandının alt
  ucu (0,9) bile sınıra oturur.
- **G2 (band yeterliliği):** `p ≥ 0,22` ise plandaki 0,9 FPS alt ucu yeter.
  `p < 0,22` ise **band yetersizdir** ve yeniden türetilir.
- **G3 (sahne bağıntısı):** en uzun koşu ≥ 5 ise, o koşunun kareleri **aynı
  uçuş bölgesinden mi** diye bakılır. Aynı bölgedense hüküm
  **SAHNE_BAGINTILI** olur → *FPS artırmak çözmez*, madde 6'daki kaldıraçlara
  gidilir.

⚠ **Sahadaki `p` ÖLÇÜLEMEDİ olarak kalır.** Ne S sentetiktir diye ne de R
arenaya OOD'dir diye saha değeri yerine geçebilir; maket çekimi
yapılmayacaktır (kullanıcı kararı). İki sayı **alt/üst çerçeve** olarak
raporlanır, saha değeri **tahmin edilmez**.

---

## 5. Jetson'sız kapanan / kapanmayan

| B4 alt sorusu | Jetson'sız |
|---|---|
| FP16 sayısal olarak güvenli mi (rota kararı FP32 ile aynı mı) | ✅ tam |
| Grafik TensorRT'ye dönüyor mu | 🟡 kısmi — ONNX var, PC'de TRT sağlayıcısı var; **`.engine` taşınmaz** |
| Cihazda gerçek FPS | ❌ hayır |
| **Kaç FPS gerekli** (bu ön kayıt) | ✅ **tam** |

Bu ön kayıt kapandığında Jetson ölçümü bir **keşif** olmaktan çıkıp
**önceden yazılmış bir eşiğe karşı doğrulama**ya döner.

---

## 6. G3 SAHNE_BAGINTILI çıkarsa kaldıraçlar (şimdiden yazılır, sonra seçilmez)

1. İrtifa/yörünge: aynı bölgeden **ikinci geçiş**.
2. `INFER_SIZE` büyütme (512 → 640) — FPS'i düşürür, `p`'yi artırabilir.
3. Hakem ekranında **son geçerli tespiti tazelik damgasıyla** gösterme
   (⚠ sözleşme değişikliğidir; **mimar kararı**, tek başıma yapmam).

---

## 7. Bu ön kaydın kendi kapısı

Ölçüm betiği yazıldığında: mutasyon kontrolü **kod üzerinde** (yorumda değil,
D-354/D-361), ve uygulanmayan mutasyon **exit 1** (D-370).
