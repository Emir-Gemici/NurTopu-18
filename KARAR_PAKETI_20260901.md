# KARAR PAKETİ — 2026-09-01

> Amaç: önünde biriken kararların her birini **tek oturuşta** verebilmen.
> Her madde: bağlam → kanıt → seçenekler → önerim → onaylarsan ne olacak.
> Hiçbiri onaysız uygulanmayacak (ÖNER-BEKLE). Kanıtların tamamı defterde.

## K1 · Hakem ekranına tazelik damgası (51 s körlüğünün kaldıracı 3)

**Bağlam.** D-374: sahne bağıntılı 51 s'lik kör aralık ölçüldü; FPS ve
çözünürlük çözmüyor (D-377). Kör aralıkta hakem ekranındaki karar kutusu
5 s sonra boşalıyor — hakem, sistemin az önce ne gördüğünü göremiyor.

**Öneri.** Karar kutusu bayatlayınca **boşalmasın**; son geçerli tespit
**yaş damgasıyla** görünsün (*"AÇIK GÜZERGÂH — 2 · 37 sn önce"*).
⚠ **Onay kapısı DEĞİŞMEZ**: BAYAT tespite ACK zaten üretilmiyor (T169) ve
bayatlık simetrik (T176) — değişen yalnız görüntülemedir; hakem bayat
tespiti onaylayamaz, sadece görür. Codex'teki **A2** (`karar_yas`
HEARTBEAT'e) bunun veri altyapısıdır.

**Seçenekler.** (a) Onayla → A2 teslimi sonrası ön kayıtla uygulanır,
ekran kapıları + tatbikat senaryolarıyla sınanır. (b) Reddet → bugünkü
davranış kalır (boş kutu). **Önerim: (a)** — her senaryoda bilgi kazandırır,
hiçbir senaryoda güvenlik kaybettirmez.

## K2 · T150 — HB tespitini üretime bağlama (K3'e bağlı)

**Bağlam.** Rotalar bugün HB hedefi olmadan üretiliyor; HB dedektörü
bilerek bağlanmadı (D-295: kırmızı otomobil 67/67 HB sanılıyordu).
O boşluk artık iki kapıyla kapalı: fiziksel ölçek (D-344) + **şekil
doğrulaması (D-379: otomobil FP %100 → %4,5, 260/260 ped korunuyor)**.

**Kalan engel: renk.** Şartname metni *"kırmızı H"*, figürü **akromatik**
ped gösteriyor. Yanlış renge bağlarsak dedektör sahada ya %0 bulur
(fail-closed, rota hedefsiz kalır — bugünkü durumla aynı) ya da yanlış
nesneye kilitlenir. **K3 cevaplanmadan bağlanmamalı.**

**Seçenekler.** (a) K3 teyidi gelene dek BEKLE (bağlama ön kaydını şimdi
yazayım, teyit gelince tek adım kalsın). (b) Teyitsiz bağla. **Önerim: (a).**

## K3 · İNSAN GÖREVİ — TEKNOFEST'e HB rengi sorusu (H-E)

Sormadan çözülemez; başka hiçbir ölçüm yerine geçmez (D-295). Taslak soru:

> *"Şartname §2.1 Hedef Bölgeyi 'üzerinde kırmızı H harfi bulunan 2×2 m
> bölge' olarak tanımlıyor; Şekil'deki görselde ise ped koyu zeminli ve H
> açık renkli görünüyor. Sahada kullanılacak HB pedinin zemin ve harf
> renklerini teyit edebilir misiniz? Ped, takımlarca mı organizasyonca mı
> temin edilecek?"*

Cevap gelince: kırmızıysa mevcut zincir hazır; değilse `hb_maskesi`'nin
renk anahtarı ölçümle yeniden türetilir (şekil kapısı renkten bağımsız).

## K4 · T194 — K0 körlük kapısının zemini (mimar kararı)

**Bağlam.** K0, tek bir YZ figürüne dayanıyor; şartname figür için *"gerçek
alanı yansıtmaz"* diyor (D-99) ve D-368 hedefi figürden kaldırdı (figür
artık **gerileme nöbetçisi**). D-331'de bir aday iki popülasyon ölçümünde
daha iyiyken tek figürde düşüp RED yedi.

**Seçenekler.** (a) K0 aynen kalsın (en muhafazakâr; v36 üretimde, aktif
zarar yok). (b) Ön kayıtlı yeni karar: K0'ın figür kolu **bilgi**ye dönsün,
kapı popülasyon kollarında kalsın (raw 0/67 + cp 0/393 boş-maske kolları
zaten var). (c) Şimdi karar verme — bir sonraki model adayı gündeme
geldiğinde ön kayıtla ele al. **Önerim: (c)** — bugün aktif bir aday yok;
kapı kararı adaya tepki olarak değil, ihtiyaç doğmadan sakin zamanda da
değil, *aday süreci başlarken* ön kayıtla verilmeli.

## K5 · T190 — 579 MB birebir kopya dizin (senin kararın, madde 18)

`data/dji_prova` ile `data/dji_prova_kareler` bayt-eş (md5 25/25 doğrulandı);
`data/dji_prova`'yı okuyan kod yok. (a) Sil → 579 MB. (b) Kalsın.
**Önerim: (a)** — ama madde 18 gereği yalnız senin emrinle.

## K6 · "Aynı bölgeden ikinci geçiş" (kaldıraç 2) — dürüst değerlendirme

⚠ Önerdiğimde ölçülmemişti; şimdi ölçüm **aleyhine işaret ediyor**: körlük
sahne bağıntılı (D-374) ve hiçbir görüntü dönüşümü kurtarmıyor (D-367 —
kusur "dağılım dışına özgü ve MUTLAK"). Aynı kör bölgeden ikinci geçiş
büyük olasılıkla **aynı körlüğü** verir. Uçuş planına koymanın maliyeti
süre (10 dk bütçesinden); beklenen kazanım **düşük**. **Önerim:
uçuş planına ZORUNLU adım olarak girmesin**; sahada operatör inisiyatifine
kalsın. (İstersen B2'nin 10 dk bütçe ölçümünden sonra yeniden bakarız.)

## K7 · T124 kapanış onayı (verdikt hazır, imza senin)

"En çok gören model" kalıbı her iki registry kopyasında da **yok**; yerine
ters disiplin yazılı; defterdeki geçişler kalıbı eleştiren kayıtlar
(D-376 §6'da ölçüldü). D-284 bir vekil kapatmayı yıkmıştı; bu yüzden
kapatma imzası sana bırakıldı. **Önerim: kapat.**

## K8 · T192 / S8 — figür-hedef sorusunun kalıntıları

D-368 hedefi yeniden hizaladı: figür **hedef değil**, K0/K8'de gerileme
nöbetçisi; T199'un kalan 2 deneme hakkı kullanılmayacak. T192 ("figürde
rota üretilemiyor") ve S8 ("FDA profili üretece girmemiş") bu hizaya göre
**amaçsız kalmıştır**. **Önerim:** ikisini D-368'e bağlayarak kapat;
figür nöbetçi rolünü zaten K0/K8 taşıyor.

---

### Onay biçimi

Tek satır yeter, örnek: `K1a K2a K4c K5a K6 tamam K7 kapat K8 kapat`.
K3 insan görevi — soruyu iletmen yeterli, cevabını bana yazarsın.
