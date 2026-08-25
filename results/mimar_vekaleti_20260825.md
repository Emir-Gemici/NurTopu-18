# MİMAR VEKÂLETİ — 2026-08-25 → 2026-08-26 (1 gün)

> **Veren:** kullanıcı (Yunus), 2026-08-25: *"mimarlık görevini de 1 günlüğüne
> sana veriyorum."*
> **Alan:** Claude 2 (başamele) — bu süre boyunca **mimar vekili**.
> **Bitiş:** 2026-08-26 aynı saat; süre sonunda bu dosya kapanış kaydıyla
> güncellenir ve rol **kendiliğinden** başameleye döner.

## 1. 🔴 VEKÂLETİN YAPAMAYACAĞI ŞEYLER — baştan yazılı

| yasak | dayanak | neden vekâletle kalkmıyor |
|---|---|---|
| **Kendi yazdığım işi kendim kapatmak** | CLAUDE.md §19 bağımsızlık kuralı: *"bir iş, onu yazanın onayıyla kapanmaz"* | Bu kural **rol**e değil **kişi**ye bağlı. Vekil mimar olmam, D-278…D-282'yi yazanın ben olduğunu değiştirmez. |
| `git push` | §5 — *"kullanıcı açıkça kaldırana kadar"* | Vekâlet §5'i kaldıran açık bir cümle içermiyor. |
| Terfi / sevk | D-133 — *"seçim ve sevk insanındır"* | Mimar da terfi etmiyordu; mimar vekili hiç etmez. |
| İnsan görevi eklemek | madde 9 — *"yalnız sen [Claude 1], yalnız kullanıcıya"* | Bu yetki **mimarın**dır ve vekâlet mimarlık yetkisidir → **kullanabilirim**, ama yalnız kullanıcıya raporlayarak. |
| Anayasa / sözleşme değişikliği | §1, §16 | Vekil mimar sözleşmeyi **yorumlar**, **değiştirmez**. Değişiklik önerisi yazılır, karar kullanıcıya bırakılır. |

## 2. VEKÂLETİN YAPABİLECEĞİ ŞEYLER

- **Başkalarının** (Codex 1/2, önceki mimar) işini denetleyip kapatmak.
- Kuyruğu **triyaj** etmek: bayat, mükerrer, kanıtsız veya artık geçersiz
  görevleri kanıtla kapatmak / birleştirmek.
- Açık kararları vermek: **mimar hükmü bekleyen** öner-bekle kalemlerini
  karara bağlamak — **kendi yazdıklarım hariç** (§1).
- Yeni görev açmak, öncelik sırasını değiştirmek.
- İnsan görevlerini kuyruğa yazmak (madde 9 yetkisi).

## 3. KENDİ İŞİM İÇİN NE YAPILACAK — kullanıcı kararıyla GÜNCELLENDİ

> **Kullanıcı, 2026-08-25:** *"mimarımız kotada, o yüzden amelen olan Codex'e
> onaylatabilirsin."*

Bu, §1'in ilk yasağını **kaldırmaz, karşılar**: kendi işimi yine ben
onaylamıyorum — **Codex** onaylıyor. Ve bu, mimarın kendisinden **daha iyi**
bir denetçidir bir açıdan: CLAUDE.md §19 *"korelasyonlu kör nokta"* uyarısı
mimar ile benim aynı model olmamızdan geliyordu. **Codex farklı modeldir**;
aynı kör noktaları taşımaz.

**Yordam — "onaylat" demek "onayla" demek DEĞİLDİR:**
- Codex'e görev *"onayla"* diye **verilmez**; *"çürüt"* diye verilir. D-281'de
  bu yöntem benim iki nedensel iddiamı kırdı — çalışıyor.
- Codex her kaydın **ham çıktısını yeniden üretir** (komutu koşar, sayıyı
  kendi çıkarır) ve bulduğu her farkı yazar.
- **Kıramazsa** → kayıt *"Codex bağımsız denetiminden geçti"* olarak
  işaretlenir ve **kapanır** (kullanıcı yetkisi).
- **Kırarsa** → kusur kayda geçer, düzeltilir, **yeniden** denetlenir.
- Codex'in *"geçti"* demesi **tek başına** yetmez: çıktısında **koşulan komut ve
  gerçek sayı** olmak zorunda (D-267: çıkış kodu kanıt değildir). Ham çıktısız
  onay **geçersizdir**.

Kapsam: D-278 · D-279 · D-280 · D-281 · D-282 + T141 + F5/eğitim turu.

## 3-eski. (İLK YAZILAN — geçersiz, tarih için tutuluyor)

D-278 · D-279 · D-280 · D-281 · D-282 ve F5/eğitim turu **benim** işim.
Bunları **onaylamayacağım**. Yerine:
- Her biri için **bağımsız denetim** koşulacak: taze bir ajan, *"ustabaşı
  yanılıyor"* varsayımıyla, ölçüm yeniden üretilerek. D-281'de bu yöntem
  benim iki nedensel iddiamı **kırdı**; yani çalışıyor.
- Denetim **geçerse** kayıt *"bağımsız denetimden geçti — mimar onayı hâlâ
  bekliyor"* olarak işaretlenir. **Kapanmaz.** Kapanış kullanıcıya/mimara kalır.
- Denetim **düşerse** kusur kayda geçer ve düzeltilir.

## 3b. 🔴 ÖLÇÜLDÜ: BEKLEYEN 19 ÖNER-BEKLE KARARININ 18'İ BENİM

Vekâletin "mimar kararı bekleyen kalemleri karara bağla" yetkisini kullanmadan
önce saydım (`REVIEW_LOG.md`, D-255 sonrası):
```text
oner-bekle iceren kayit   : 19
  yazan Claude-2 (ben)    : 18   -> §1 geregi KENDIM karara BAGLAYAMAM
  yazan mimar (D-263)     :  1   -> mimarin kendi notu, karar degil
```
⇒ Vekâletin "karar ver" kısmı **fiilen boş**: bağlayabileceğim tek bir karar
bile başkasının değil. Bu bir eksiklik değil, **§1'in doğru çalışması**:
vekâlet, kendi önerilerimi kendime onaylatmanın yolu olmamalı.
Bu 18 kalem **Codex denetiminden** geçerse kapanır (§3).

## 4. ÖLÇÜLEBİLİR ÇIKTI (süre sonunda bu tablo doldurulur)

| iş | hedef | sonuç (2026-08-26) |
|---|---|---|
| kuyruk triyajı | 44 READY_FOR_REVIEW + 27 açık → her biri hükümlü | **44 RFR:** 35 taze doğrulama (`results/t133/taze_dogrulama_35.json`) → **20 KAPANDI (vekil)**, kanıt satırlarıyla; 9'u KAPANMAZ (gerçek kusur gömüyor). **27 açık:** triyaj (`acik_27_triyaj.json`) → 10 kapatma adayı → **çürütme turu: 8 YIKILDI, 2 KAPANDI** (T33, T46) — **D-284**. ⚠ Triyajın kalan 17 hükmü (3 BLOKE_CİHAZ T15/16/17, T109→T16 birleştirme, 13 GEÇERLİ_AÇIK öncelik notu) **kuyruğa İŞLENMEDİ** — tablo `results/t133/triyaj_tablosu.md`'de; ve D-284 gösterdi ki triyaj hükmü tek başına %80 yanlış, bunlar da çürütmeden geçmeden yazılmamalı. |
| başkalarının işi | kanıtla kapat / geri çevir | 3 onarım worktree'den **birleştirildi** ve kapıyla doğrulandı: T83 (paket `arac_maskesi` + test), S9 (`iha_perceive` kayıt defterine bağlı), T59 (test MODEL'i kayıt defterinden). T59 birleşimi **D-283**'ü ortaya çıkardı (sabit v24'e çivili, v24 çökmüş). |
| kendi işim | bağımsız denetimden geçir (kapatma YOK) | Codex çürütme prompt'u hazır: `results/codex_denetim_prompt_20260825.md`. **Kullanıcı henüz yapıştırmadı → D-278…D-282 AÇIK, kapanmadı.** Kendi işimi kapatmadım (§1). |
| bekleyen mimar kararları | karara bağla (kendi öner-bekle'lerim hariç) | **0 karar** — §3b: 18/19 benim; bağlayabileceğim başkasına ait karar yoktu. Yeni bir **eşik kararı** açıldı ve **verilmedi**: **T142** (0,67 kaplama / 0,50 kenar, v35'e kalibre edilmemiş). |
| insan görevleri | kuyruğa yaz | Kuyruğa **yazılmadı**; §5'te kullanıcıya raporlanıyor (2 görev). |
| **yeni bulgular** | — | **D-283** (0,67 tavanının gerekçesi çökmüş maskeydi; v35 tek arena karesinde yol=None), **D-284** (çürütme turu). Yeni görev: **T142** (eşik), **T143** (`.engine` kayıt reddi + sessiz kamera bitişi — 30 Eylül), **T144** (`len(l)` kırpması %32-90 engel alanı atıyor). |

## 5. KAPANIŞ KAYDI — 2026-08-26

**Rol başameleye döndü.** Vekâlet süresi doldu; bu dosyadan sonra mimar yetkisi
kullanılmaz (görev açma/kapama dâhil — kuyruk satırı yalnız durum güncellemesi).

### Sayılar
- Kapanan görev: **22** (20 taze-doğrulamalı RFR + T33 + T46). Açılan: **3** (T142–T144).
- Kapatma **reddi**: 8 (D-284) + 9 (T133 taze doğrulama) = **17 görev "zaten yapılmış" sanılıp yapılmamıştı.**
- Defter kaydı: D-283, D-284. Kapı: **15/15 · 819 test OK (2 gerekçeli skip)**.
- Ölçüm ajanı: 10 çürütücü (1,0 M token, 270 araç çağrısı) + 35 taze doğrulama + 27 triyaj.

### Yapılmayanlar (dürüst liste)
1. D-278…D-282 **kapanmadı** — Codex prompt'u kullanıcının elinde.
2. Triyajın 17 hükmü kuyruğa işlenmedi (gerekçe §4).
3. D-284'ün ortaya çıkardığı, T142–T144 dışındaki gömülü kusurlar **açık görevlerin içinde** duruyor (T53 hipotez çürümesi, T47 çim/toprak %37, T100 işlenmemiş koşum, T124 v35 registry cümlesi, T52 kenar 0,5004, T54 mutasyon deliği) — her biri o görevin `🔴 VEKİL KAPATMA REDDİ` satırında; **ayrı görev açılmadı**, çünkü görev zaten açık.
4. Vekâlet §3'ün *"bağlayabileceğim karar"* kısmı boş çıktı; bu bir başarısızlık değil §1'in çalışmasıdır — ama mimar döndüğünde 19 öner-bekle + T142 onu bekliyor.

### Kullanıcıya raporlanan İNSAN görevleri (madde 9 — kuyruğa yazılmadı, buradan)
- **H-A · DOĞRULAMA uçuşu (arena, gündüz, gimbal 90°):** tek gerçek arena karesi n=1 ve v35 onda yol=None (D-283). Bu sayı ancak yeni kareyle büyür.
- **H-B · Hakem ekranı saha doğrulaması:** T46 ölçümle kapandı (36/67 rota, v35) ama kullanıcının 2026-08-11 bildirimi *"asla düzgün çalışmıyor"* insan gözlemidir; v35 ile **yeniden bakılmalı**.

### Mimara devir (ilk okunacak)
1. **T142** — eşik kararı (0,67/0,50 v35'e kalibre değil; D-283 §3-4). Eşiğe dokunmadım.
2. **T143** — 30 Eylül sahası için KRİTİK: `.engine` kayıt defterinden geçmiyor.
3. **D-284 kalıp 1** — "Yap sınandı, iddia sınanmadı": triyaj yordamı iki turlu olmalı.
4. `results/codex_denetim_prompt_20260825.md` — kullanıcı yapıştırınca D-278…D-282 kapanır ya da düzelir.
