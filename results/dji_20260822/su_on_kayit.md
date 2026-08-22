# SU ETİKETLEME — ÖN KAYIT (D-107)

> **Yazıldığı an:** 2026-08-22, **hiçbir maske çizilmeden önce.**
> **Yazan:** Claude 2 (başamele) · **Şartnameyi onaylayan:** kullanıcı (Yunus),
> 2026-08-22, `SU_ETIKETLEME_PLANI.md §4b`.
> ⛔ Bu dosyadaki bantlar **sonuca göre değiştirilmez.** Değiştirilirse ölçüm
> geçersizdir ve öyle yazılır.

---

## 1. NE SINANIYOR

**F3 şartname kapısı:** onaylanan şartname, birbirinden habersiz üç amelenin
**aynı** maskeyi çizmesine yetiyor mu?

D-273'te ölçülen kusur şuydu: üç ajan birbiriyle **0,88**, referansla **0,55**
uyuştu — ve ajanlar **haklıydı**; belirsiz olan şartnameydi. Yani *"ajanlar
birbiriyle uyuşuyor"* tek başına **kanıt değildir**; belirsizlik **tutarlı**
çözülebilir. Bu yüzden iki eksen birden ölçülür.

## 2. BANTLAR — önceden yazılı

| ölçüt | GEÇTİ | DÜŞTÜ | anlamı |
|---|---|---|---|
| **U1** ameleler arası IoU medyanı | ≥ 0,75 | < 0,75 | şartname okunabilir mi |
| **U2** referansa göre IoU medyanı | ≥ 0,70 | < 0,70 | şartname **doğru** mu |
| **U3** sınıf-1 (su/kıyı) tek başına IoU | ≥ 0,65 | < 0,65 | asıl hedef sınıf |

🔴 **KARAR KURALI (D-273'ün dersi, mekanik uygulanır):**
- **U1 GEÇTİ + U2 GEÇTİ** → şartname sağlam → **F4 pilot başlar.**
- **U1 GEÇTİ + U2 DÜŞTÜ** → 🔴 *"tutarlı ama yanlış"* — **şartname hâlâ
  belirsizdir.** Cümle düzeltilir, **pilot BAŞLAMAZ.** (D-273'te aynen bu çıktı.)
- **U1 DÜŞTÜ** → şartname okunamıyor; cümle düzeltilir, **pilot BAŞLAMAZ.**
- U2 düşerse **önce referansın kendisi sorgulanır** (D-273'te ajanlar haklıydı):
  fark bölgesi **2,5× büyütmede gözle** incelenir ve hangi tarafın haklı olduğu
  **yazılır**. Referans yanlışsa **referans** düzeltilir, ameleler suçlanmaz.

⚠ **Bant gevşetme yasağı:** U2 0,68 çıkarsa bant 0,65'e **indirilmez**.

## 3. REFERANS — kim, ne zaman, neden önce

Referansı **ustabaşı (ben)** çizerim ve **amelelerden ÖNCE** çizerim.
Sonra çizersem onların yorumuna kayarım; o durumda U2 ölçülemez hâle gelir.
Referans çizildikten sonra **değiştirilmez** (§2'nin son maddesi hariç: gözle
inceleme haklı çıkarsa düzeltme **ayrıca kaydedilir**).

## 4. KARE SEÇİMİ — elle yazılmaz

🔴 D-273 §5'te kendi hatam: 8 karenin **5'i diskte yoktu**, dizin adlarını
**uydurmuştum**. Bu turda kare listesi **diskten türetilir**, her dosyanın
varlığı **doğrulanır** ve liste `su_pilot_atama.json`'a yazılır. Ameleler
atamalarını **o dosyadan** okur; ben prompt'a kare adı **yazmam**.

Seçim ölçütü: 8 kare, şartnamenin **S1–S6** sorularını kapsayacak biçimde
(açık su · su+sazlık sınırı · gölge/su bitişikliği · menfez tabliyesi ·
yol+su birlikte · dar ark). Kapsama **görsel olarak doğrulanır** (D-80).

## 5. BAŞARISIZLIK SAYILACAK SONUÇLAR

- Herhangi bir amele **boş maske** döndürür ve bunu *"su yok"* diye sunarsa:
  ⚠ D-273'te ameleler *"boş liste 'çatı yok' değil 'kare yok' demektir"* diyerek
  sahte bir uyumu önlemişti. Boş maske **ayrıca** soruşturulur, ortalamaya
  sessizce **katılmaz**.
- Ameleler arası IoU **1,00'a çok yakın** çıkarsa (> 0,97): şüphelidir —
  bağımsız çalışmamış olabilirler. Prompt'ların ayrı olduğu **doğrulanır**.
- Çözünürlük altı bölgeler: amele **"olabilir" diye işaretlerse** bu D-210
  ihlalidir ve kayda geçer. Doğru davranış **etiketsiz bırakmaktır**.

## 6. BU TURDA YAPILMAYACAKLAR

`dataset/` altına **kalıcı küme yazılmaz** · `config/model_registry.json`'a
**dokunulmaz** · `CONTRACTS.md` **değişmez** (su = sınıf 1, nc=2) · eşik
**değişmez** · eğitim **yok** (F6 ayrı tur) · terfi **yok** · **push YOK**.

## 7. KAPI

`codes/test_rota_sentetik.py` → **15/15** ·
`unittest discover -s tests -q` → **806 OK** (mevcut sayı).
Etiketleme kodu üretim koduna dokunmaz; kapı yine de koşulur.
