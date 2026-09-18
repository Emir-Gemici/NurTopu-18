# 19 EYLÜL — MİMAR TARAFI NOTLARI (Emir ekibi için)

**Dal:** `master` (uzak: `origin/master`) · **Yazan:** Claude 1 (mimar) · Halil tarafı
**Okuma sırası:** bu dosya → `DAL_CAKISMA_RAPORU_20260918.md` → `ONARIM/ONARIM-00_LISTE.md`

Aşağıdakilerin hepsi **ölçülmüştür**; ölçülmeyen her satırda "BEYAN" ya da "ÖLÇÜLMEDİ" yazar.

---

## 1. ⚠ DÜZELTME (00:55): "Jetson zaten güncel" iddiam **YANLIŞTI**

19 Eylül 00:20'de Jetson'a (`10.21.8.7`) bağlanıp ölçtüm:

| Kontrol | Sonuç |
|---|---|
| `~/navitas_tunel_staging/jetson_paket/kod/*.py` ↔ koşan `~/navitas/...` | **Tamamı birebir aynı** (`cmp`, tek fark yok) |
| `codes/rpi_inference.py` md5 | `eae1f19114…` = `origin/tunel-saha-20260918` ile **eş** |
| Servisler | 6 birim `active`, tünel kipinde (`seri_hub --tunel 127.0.0.1:14553 --tunel-kimlik hava`) |
| `iha_inis_yayinci` | `--kalkis-bekle` ile koşuyor (D-495 düzeltmesi kurulu) |

**🔴 Bu karşılaştırma yanlış referansa dayanıyordu.** Emir tarafı haklı olarak düzeltti:
staging dizini **dünkü** paketti (`e33b592a`); bekleyen güncelleme ise bu gece denetimden geçen
**`8a483ade`** sürümüydü (iniş kanıtı ACK gelmezse 60 kez yeniden yayın + alçalma sırasında
yeniden başlama düzeltmesi). Ben staging'i "en yeni" varsaydım; o varsayımı ölçmemiştim.
Emir tarafı 00:45'te tek dosyayı (`comms/iha_inis_yayinci.py`) kurdu, servis `active`,
"kalkış kanıtı bekleniyor" diyor. **Kalem onlar tarafından kapatıldı.**

**İkinci düzeltme — "staging systemd şablonları sistemi bozar" uyarım da eksikti.** Şablonlar
**elle** `/etc/systemd`'ye kopyalanırsa bozar (bu doğru), ama kurulum öyle yapılmıyor:
`jetson_baslat.sh` şablonları kurarken kullanıcı adını ve Python yolunu ortam değişkenlerinden
yeniden yazıyor. Ben kurulu birim ile şablonu karşılaştırıp aradaki farkı "kurulum bozar" diye
yorumladım; doğrusu **"elle kopyalamayın, kurulum `jetson_baslat.sh` ile yapılsın"**.

**Ders (kendime):** bir dizinin "en güncel" olduğu ölçülmedikçe varsayılmaz; referansın kendisi
doğrulanmalıydı.

## 2. `codes/rpi_inference.py` master sürümüne alındı (görev kaydı geri geldi)

**Neden:** tünel dalındaki sürümde **ONARIM-03 görev kaydı yok**. Yani uçuşta kare başına kalıcı
kanıt tutulmuyordu — 17 Eylül düşüşünden sonra en çok eksikliği çekilen şey buydu.

**Risk ölçüldü, sıfıra yakın:** master sürümü tünel dalınınkinin **üst kümesi**.
`git diff` ile argüman farkı **yalnız iki tane**: `--gorev-kaydi`, `--isaretli-yayin`.
Karar mantığı, model çağrısı, eşikler, tünel yolu **değişmedi** (bu dosya tünelle ilgilenmez;
tüneli `seri_hub` yapar). Eklenenler: JSONL kayıt satırları ve FPS/p95 özeti.

**Kurulum:** `codes/rpi_inference.py`, `codes/kare_keskinligi.py`, `codes/isaretli_yayin.py`
kopyalandı; sözdizimi ve `--help` Jetson'da doğrulandı.
**Geri alma (tek komut):** `cp ~/navitas/codes/rpi_inference.py.yedek_20260919 ~/navitas/codes/rpi_inference.py && sudo systemctl restart navitas-rpi-inference`
**Etkinleştirme:** `/etc/navitas.env` içine
`RPI_EK_ARGS=--gorev-kaydi /home/n4vitas/navitas/results/jetson_log/gorev` + servis restart.

## 3. 🔴 Alan ihlali denetimi ŞU AN KAPALI

Jetson günlüğünde her açılışta:

```
UYARI: --ub-referans verilmedi ya da canli telemetri yok — HEARTBEAT'e x,y EKLENMEZ;
YKS ALAN IHLALI denetimi YAPILAMAZ
```

Yani YKİ'nin alan ihlali kontrolü çalışmıyor. Tek argümanla çözülür (`--ub-referans <lat,lon>`),
ama **referans noktasını sizin vermeniz gerekir** (uçuş alanının başlangıç noktası). Şartname
kalemi olduğu için uçuştan önce kararlaştırılmalı.

## 4. FOV — hesap doğru ama **kullanılan sensör modu tam alan DEĞİL** (19 Eyl 01:00, ölçüldü)

Emir tarafının hesabı **tam sensör alanı için doğrudur**: IMX477 aktif alan 4056×3040 px ×
1,55 µm = 6,287 × 4,712 mm; 6 mm lensle yatay **55,3°**, dikey 42,9°, köşegen 66,4°.

**Ama Jetson'daki sürücü tam alanı hiç sunmuyor.** Kamera köprüsünün açılış günlüğü (ölçüldü):

```
GST_ARGUS: Available Sensor modes :
  3840 x 2160 FR = 29.999999 fps
  1920 x 1080 FR = 59.999999 fps
Camera mode = 1            ← kullanılan: 1920x1080
```

4056×3040 modu **listede yok**. Dolayısıyla **55,3° bir ÜST SINIRDIR**, gerçek değer değil:

| Mod 1 nasıl üretiliyorsa | Aktif genişlik | Gerçek yatay FOV |
|---|---|---|
| 3840×2160'ın 2×2 binning'i (FOV korunur) | 3840 px → 5,95 mm | **≈ 52,8°** |
| Sensör merkezinden ek kırpma | 1920 px → 2,98 mm | **≈ 27,9°** |

30 m irtifada bu, **31 m genişlik** ile **15 m genişlik** arasındaki farktır — rota koordinatları
iki kat ölçekte kayar. Datasheet'ten ayırt **edilemez**, ölçülmelidir.

**Ölçüm yordamı (yerde, drone gerekmez, ~5 dk):** duvara `W = 2,00 m` aralıkla iki işaret;
kamera tam karşıdan `D = 3,00 m`; `/kare.jpg`'de işaretler arası piksel `p`;
`FOV_yatay = 2·atan( (W/2)·(1280/p) / D )`. ~53° → binning, ~28° → kırpma.

**Şimdilik:** `FOV=55`, `FOV=63`'ten daha savunulabilir (63 hiçbir hesaba dayanmıyor), ama
**ikisi de tahmindir** ve ölçüm yapılana dek öyle etiketlenmelidir. ONARIM-05 açık kalır.

## 5. K8 / telsiz konusunda mutabıkız — iki düzeltmenizi kabul ediyorum

- **`SR1_*` parametresini elle yazmak tutmaz**, MP her bağlanışta kendi hızlarını ister; ayar
  `Config → Planner` ekranından yapılır. Bizim ilk önerimiz bu noktada eksikti.
- **Air Speed 128 → 250 yapılmamalı**: menzili düşürür, menzil hiç ölçülmedi (T271).
- Max Window'un gecikme tabanı olduğu ölçümünüz (Pixhawk yolu olmadan p95 231 ms) bizim
  "TELEM2 baud'unu yükselt" önerimizi de geçersiz kılıyor. Sıranız doğru.
- **Parça boyu bulgunuz (93 bayt sınırı → 128 baytlık parçalar 2 pakete bölünüyor)** kritik ve
  kayıp oranıyla birebir uyuşuyor. T287'nin uçuş sonrasına bırakılması doğru; bu, sözleşme +
  test + benzetim değişikliğidir, gece yapılmaz.

## 6. Dal durumu

`master` ile `tunel-saha-20260918` hâlâ ayrı ve **REVIEW_LOG D-469…D-486 numaraları çakışıyor**.
Ayrıntı ve birleştirme sırası: `DAL_CAKISMA_RAPORU_20260918.md`. Uçuş sonrasına bırakılması
konusunda hemfikiriz.

**Master'da olup dalda olmayan, sahayı ilgilendirebilecek işler:**

| İş | Durum |
|---|---|
| ONARIM-03 görev kaydı (kare başına JSONL, fsync) | Jetson'a taşındı (§2) |
| ONARIM-18 heartbeat akış kimliği + kalkış kapısı | Dal kendi çözümünü uygulamış (D-495); master'ınki bağımsız denetimden geçti (D-504) |
| ONARIM-19 video kaynağı keşfi (`yks_gui --video-tara`) | Yalnız master'da; video kapsam dışı olduğu için saha etkilenmiyor |
| ONARIM-16/17 YKS/İKA eşleşme keşfi | `yks_kesif.py` Jetson'da var |

## 7. 🔴 ÖLÇÜLDÜ (00:47): canlı kamerada 518/518 kare `MASKE_YOK` — **ama bu bir arıza değil**

Görev kaydı açıldıktan sonra ilk gerçek ölçüm (`results/jetson_log/gorev/20260919_004640_612b01f7_8539/`):

| Ölçüt | Değer |
|---|---|
| Kare | 518 |
| Sonuç | **518/518 `MASKE_YOK`** |
| `zemin_px` | **0 — beş yüz on sekiz karenin hepsinde** |
| `engel_px` | ort. 894.960 (1280×1280'in ~%55'i) |
| Keskinlik (Laplacian var.) | ort. **13,2** (min 12,9 · maks 13,6) → BULANIK bandı (< 20) |
| Çıkarım süresi | ort. 142 ms (~7 FPS), medyan 135 ms |

**Kareyi indirip baktım:** kamera **tavana** bakıyor (kullanıcı teyidi) — düz, dokusuz bir yüzey
ve tavan lambası yansıması. Görüntüde yol olmadığı için modelin `MASKE_YOK` demesi **doğru
davranıştır** (fail-closed).

⚠ **Keskinlik 13,2 değeri bu sahnede "lens bulanık" anlamına GELMEZ.** Laplacian varyansı
**dokuya** duyarlıdır; düz beyaz tavanda ölçülecek detay olmadığı için değer kusursuz bir lensle
de düşük çıkar. Odak hakkında hüküm ancak **dokulu** bir hedefte (zemin, asfalt, test kartı)
verilebilir. 17 Eylül'deki 350–550 ölçümü dokulu hedefteydi; ikisi karşılaştırılamaz.

⚠ **Dolayısıyla bu ölçüm ne modelin sahadaki başarısı ne de lensin odağı hakkında bir şey söyler.** ONARIM-04
(canlı `MASKE_YOK` kök nedeni) **hâlâ açıktır**: kameranın ≥ 5 m uzağa, tercihen gerçek zemine
baktığı bir koşulda tekrarlanmalı. Artık görev kaydı açık olduğu için tekrar ölçüm 2 dakikalık iştir.

## 8. Bizden bekleyenler (Halil tarafı)

- Ethernet kablosu + 4S şarj: **kullanıcıda**, drone toplanıyor.
- Jetson erişimi açık, SSH ile çalışılabiliyor (`10.21.8.7`).
