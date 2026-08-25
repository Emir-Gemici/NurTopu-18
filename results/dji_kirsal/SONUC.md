# DJİ KIRSAL EĞİTİM TURU — SONUÇ

> **Ön kayıt:** `results/dji_20260822/egitim_on_kayit.md` (eğitim başlamadan yazıldı)
> **Yetki:** kullanıcı — *"otomatik karar ver, onay beklemeden eğitmeye başla."*
> ⛔ **TERFİ YOK** · registry'ye dokunulmadı · Jetson paketi değişmedi ·
> eşik/`CONTRACTS.md` değişmedi · **PUSH YOK**.
> Ham çıktı: `bakir_0038.json` · `bakir_0038_taban.json` · `kiyas_109.txt` ·
> `zincir_ozeti.json` · `scripts/olcum/results/t63/dji_kirsal_v1_kabul_verdikt.json`

## 1. ARENA KAPISI — **GEÇTİ (4/4)**, bantlar ön kayıttan

| ölçüt | bant | ölçülen | sonuç |
|---|---|---|---|
| kabul zinciri | VERDİKT True | **ÜRETİME ALINIR** (K0–K5 hepsi) | ✅ |
| K1 rota | ≥ 230/260 | **255/260** | ✅ |
| 67 gerçek karede red | ≤ 5 | **0/67** | ✅ |
| çatı kaçağı | ≤ 0,10 | **0,0158** | ✅ |

Çatı kaçağı **ölçülen tüm modellerin en iyisi**: v34 0,961 · v30 0,305 · t121_ft 0,131
· t127_temiz(=v35) 0,043 · t122ac 0,020 · **dji_kirsal_v1 0,0158**.

## 2. KIRSAL ÖLÇÜM (kapı DEĞİL) — **BÖLÜNDÜ**, biri iyi biri kötü

Bakır 0038, **aynı 59 kare**, üretim yolu:
```text
model                 MASKE_YOK        rota URETTI
v35 (uretim)        35/59 (59,3%)    11/59 (18,6%)
v34 (yedek)         41/59 (69,5%)    11/59 (18,6%)
dji_kirsal_v1       29/59 (49,2%)    10/59 (16,9%)
```
- `MASKE_YOK` **59,3% → 49,2%** = **İYİLEŞTİ** (10,1 puan, 6 kare)
- rota oranı **18,6% → 16,9%** = **KÖTÜLEŞTİ** (1 kare)

🔴 **Sebep dağılımı bunu açıklıyor:**
```text
model            MASKE_YOK  UC_BANT_TEMAS_YOK  rota
v35                 35            13            11
dji_kirsal_v1       29            20            10
```
Maske kazanan 6 kare **rotaya dönüşmedi**, `UC_BANT_TEMAS_YOK`'a kaydı (13 → 20).
⇒ **Model artık daha çok görüyor ama gördüğü zemin bantlara ulaşmıyor** —
parçalı/kopuk. Ön kayıt §3(b) böyle bir bölünmeyi öngörmemişti; ikisi de
raporlanıyor, iyi olan seçilip kötü olan gizlenmiyor.

## 3. 🔴 KAPININ DIŞINDA KALAN İKİ GERİLEME

Bunlar ön kayıttaki kapıda **yoktu** ama ölçüldüler ve saklanmıyorlar:

| ölçüt | v35 | dji_kirsal_v1 | yön |
|---|---|---|---|
| `figur_zemin_orani` | 0,1508 | **0,3900** | **2,6 kat KÖTÜ** |
| `kaplama67_icerik_medyan` | 0,5076 | **0,3829** | **12,5 puan DÜŞTÜ** |

- **Figür zemin:** D-249 §5 bu ekseni *"TEHLİKELİ yön"* diye işaretlemişti —
  model, engel olması gereken figürde zemin görüyor. K0 kendi eşiğini geçti
  ama sapma **büyüdü**.
- **Kaplama:** D-240'ın bağımsız tahmini gerçek otoparkta **%47–52** sürülebilir
  diyor. v35'in 0,5076'sı o aralığın **içinde**, yeni adayın 0,3829'u
  **altında** — yani gerçek karelerde **eksik görüyor**.

## 4. ADAY FİİLEN "v34 + 1 EPOCH"

```text
16 epoch kosuldu · EarlyStopping: son 15 epoch'ta iyilesme YOK
best.pt = EPOCH 1
mAP50(M):     epoch1 0,3244 · epoch10 0,3258 · epoch16 0,3138   -> DUZ
mAP50-95(M):  epoch1 0,1978 (EN YUKSEK) · epoch10 0,1960
```
Reçete `t127_temiz`'den aynen alındığı için başlangıç ağırlığı **v34**'tür
(t127 de v34'ten ince ayar yapılmıştı). Yani bu aday, **v34'ün üzerine karışımla
tek epoch**tur.

⚠ Val kümesi v35'inkiyle **aynıdır** (rescuenet + arena + copy_paste_t127;
`dji_kirsal` val'e bilerek konmadı). O yüzden şu kıyas geçerlidir:
**yeni epoch-1 mAP50-95(M) 0,1978 > v35'in en iyisi 0,1905.**
⚠ Ama bu **tek koşumdur** ve D-140 bu projede *"tohum etkisiz"* ölçmüştü;
tek koşumdan üstünlük iddia edilmez.

## 5. HÜKÜM

> **Kırsal veri arenayı BOZMADI** — dört kapı kalemi de geçti, çatı kaçağı
> ölçülen en iyi değer.
> **Kırsalda kısmen işe yaradı:** görme arttı (MASKE_YOK −10,1 puan), **rotaya
> dönüşmedi** (−1 kare).
> **İki eksende geriledi** (figür zemin 2,6 kat, kaplama 12,5 puan) ve bu
> eksenler kapıda yoktu.

⛔ **TERFİ ÖNERİSİ DEĞİLDİR** (D-133). Aday sabitlendi, seçim insanındır.

## 6. BUNDAN SONRASI — öner-bekle
1. **Rotaya dönüşmeyen görme** asıl sorundur: `UC_BANT_TEMAS_YOK` 13→20.
   Ölçülmesi gereken: maske **parçalı** mı, yoksa bantlar 30 m irtifada
   **yapısal olarak mı** karşılanamıyor? İkincisiyse etiket değil **hat** sorunu.
2. **Kaplama düşüşü** gerçek otoparkta ölçülüyor ve kırsal veri o domende yok —
   yani bu bir **transfer bedeli**. Karışım oranı ayarı ayrı bir tur ve ayrı bir
   ön kayıt ister (ön kayıt §3(c) bunu şimdiden yasakladı).
3. Kalan **546 kare** hâlâ etiketsiz. Bu sonuç, etiketlemeye devam etmenin
   **otomatik olarak doğru** olmadığını gösteriyor: 160 kare görmeyi artırdı ama
   rota üretmedi. Önce (1) ölçülmeli.
