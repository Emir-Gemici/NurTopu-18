# S2 · `CONTRACTS.md §6.3` için ALT BÖLÜM ÖNERİSİ — K-A ve ROTA EKSENİ

> **ÖNERİDİR.** `CONTRACTS.md` değişmedi; sabitler (`HEDEF_BANT_ORANI = 0.08`,
> `BANT_TEMAS_MIN_ORANI = 0.02`) ve K-A'nın tanımı **aynen** kalır. Karar mimarındır.
> Yazan: Claude 2 (başamele) · 2026-08-26 · ön kayıt `results/gece_20260826/ON_KAYIT.md §5`.

---

## Önerilen metin — `#### K-A.1 · Uç bandın EKSENİ: rota ekseni, kadraj ekseni değil`

K-A "alt → üst bant teması" der. **Alt** ve **üst**, kadrajın değil **ROTANIN**
uçlarıdır: şartnamede rota İKA-KB → HB eksenindedir ve uçuş yönü (dolayısıyla
kadrajın dikeyi) bu eksene hizalı olmak zorunda değildir. Ölçüldü (D-281 §3):
0038 klibinde YAPISAL reddedilen 18 karede yol kadrajı **enine** kesiyor; sorun
zemin azlığı değil, K-A'nın kadraj dikeyini rota ekseni sanmasıdır.

**Uygulama:** `analyze_path(..., rota_ekseni_derece=None)`.

| parametre | anlam |
|---|---|
| `None` | mevcut davranış, **bayt-eş** (kadraj dikeyi = rota ekseni varsayımı) |
| `0` | rota alttan üste (None ile aynı karar; dönüşüm birim) |
| `+90` | rota **soldan sağa** (KB solda, HB sağda) |
| `-90` | rota sağdan sola |
| `180` | rota üstten alta |

Açı: görüntü "yukarı"sından **saat yönünde** derece. Maske (ve varsa engel maskesi,
HB görüntüsü) `cv2.warpAffine` + `INTER_NEAREST` ile döndürülür; K-A ve A*
döndürülmüş çerçevede koşar; waypoint'ler, temiz maske ve sebep metni orijinal
kare koordinatına geri çevrilir. 90'ın katlarında dönüşüm tam piksel
permütasyonudur.

**Madde 15 güvenceleri (kod zorlar, test kanıtlar — `tests/test_rota_ekseni.py`):**
1. Döndürmeyle kadraja giren boş köşeler **ENGEL (0)** sayılır.
2. Geri çevrilen temiz maske, döndürülmemiş çekirdek temizliğiyle **kesiştirilir**
   (serbest alan döndürme yoluyla büyüyemez).
3. Her geri çevrilen waypoint bu maskede olmak zorundadır; değilse
   `KENAR_GUVENSIZ` ile **fail-closed**.
4. İçerik kutusu döndürülmüş çerçevede yeniden hesaplanır; ara açılarda sınır kutusu
   köşelerde engel içerir → kapı **sıkılaşır**, gevşemez.

## Önerilen metin — `#### K-A.2 · Eksenin KAYNAĞI: operatör girdisi; otomatik seçim ÜRETİME GİRMEZ`

Üretimde `rota_ekseni_derece` **uydurulmaz**. Tek meşru kaynak:

```
rota_ekseni_derece = (KB→HB kerterizi, operatör girdisi, pusula/harita) − (araç yönü / gimbal yaw, telemetri)
```

- Kerteriz **görev başında** operatör tarafından girilir (şartname: KB ve HB konumları
  bilinir); araç yönü telemetriden okunur. İkisi de yoksa parametre **None** kalır,
  yani mevcut K-A aynen çalışır — sessiz gevşeme yok.
- ⛔ **"En iyi eksen" (0/90/… içinden rota üreten açıyı seçmek) üretime GİRMEZ.**
  Gerekçe: **fail-open** riski. Kapalı dikey koridorda K-A doğru olarak `NO_ROUTE`
  derken, eksen tarama enine rastgele bir zemin bandını "koridor" ilan edip
  `OPEN_ROUTE` üretebilir; şartname yanlış güzergâhı **0 puan** sayar (§6.3 giriş).
  "En iyi eksen" yalnız **ölçüm tavanı** olarak raporlanır (`results/s2_yonelim/olcum.md`).
- Döndürülmüş çerçevede koşan karar, sebep metnine `[rota ekseni N derece; ...]`
  ekler ve `olcum["rota_ekseni_derece"]` alanını doldurur: hakem ekranı ve günlük,
  kararın hangi eksende alındığını **görür**.

## Değişmeyenler (açıkça)
- `HEDEF_BANT_ORANI`, `BANT_TEMAS_MIN_ORANI`, `min_area_ratio`, K-B güven eşiği.
- `costmap_path_finder.rota_bul` — bu öneri yalnız `analyze_path` üretim yolunu kapsar;
  `rota_bul` için ayrı iş (aynı sarmalayıcı deseni uygulanabilir).
- `config/model_registry.json`.
