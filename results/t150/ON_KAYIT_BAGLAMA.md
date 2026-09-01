# T150 — HB TESPİTİNİN ÜRETİME BAĞLANMASI · ön kayıt (K2a — TEYİT BEKLİYOR)

Tarih: **2026-09-01** — kullanıcı K2a'yı onayladı: bağlama, K3 (HB renk/desen
teyidi) **cevaplanmadan yapılmaz**; bu ön kayıt teyit geldiğinde tek adım
kalsın diye şimdiden donduruldu.

## 1. Ön koşullar (hepsi sağlanmadan bağlanmaz)

- [ ] **K3 cevabı geldi** ve ped tasarımı biliniyor.
  - Kırmızı ise: mevcut zincir hazır (aşağı in).
  - Değilse: `hb_maskesi` renk anahtarı **ölçümle yeniden türetilir**
    (kendi ön kaydıyla) ve `168` yeniden koşulur; şekil kapısı renkten
    bağımsız kalır.
- [x] Ölçek kapısı (D-344) + şekil kapısı (D-379/D-383: en-yüksek-puan
  seçimi, eşleşme kuralı, NaN korumaları) yerinde.
- [x] A2 `karar_yas` altyapısı yerinde (hedef kaybında hakem görünürlüğü).

## 2. Değişiklik (tek nokta)

Üretim `analyze_path` çağrılarına (run_camera esas; run_image/run_video
aynı kalıp) `goruntu=frame` geçirilir ve HB tespiti
`hb_konumu(frame, mpp=kare_mpp, sekil_esigi=HB_SEKIL_ESIGI)` ile yapılır —
**ölçek + şekil birlikte** (yarım yapılandırma zaten fail-closed reddedilir).

## 3. Kabul (bağlamadan sonra, terfi zinciri gibi)

- Kabul zinciri **tamdan** yeniden koşulur (`65`): hedef seçimi rota
  geometrisini değiştirebilir → K1–K8 + K5A **aynı eşiklerle** yeniden
  ölçülür; tek eşik gevşetilmez (D-107).
- Genel kapı iki kol 15/15 + tam suit.
- `HEDEF_YOK` çekimserliği: HB bulunamayan karede davranış bugünküyle
  AYNI kalmalı (fark ölçülür, sıfır beklenir).

## 4. Bilinen sınırlar (bağlamayla birlikte sahaya taşınır)

- **Çerçeveli sahtekâr sınıfı** (D-383): kırmızı çerçeveli tabela/damalı
  örtü şekil kapısından geçebilir. Saha günü görsel kontrol maddesi:
  arena çevresinde ~2 m ölçekli çerçeveli kırmızı nesne var mı?
- Kusursuz dolu kırmızı kare geçer (D-379 bilinen sınırı, test kilitli).
