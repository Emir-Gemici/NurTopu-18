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

| iş | hedef | sonuç |
|---|---|---|
| kuyruk triyajı | 44 READY_FOR_REVIEW + 27 açık → her biri hükümlü | |
| başkalarının işi | kanıtla kapat / geri çevir | |
| kendi işim | bağımsız denetimden geçir (kapatma YOK) | |
| bekleyen mimar kararları | karara bağla (kendi öner-bekle'lerim hariç) | |
| insan görevleri | kuyruğa yaz | |

## 5. KAPANIŞ KAYDI
*(süre sonunda doldurulacak)*
