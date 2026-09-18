# 19 EYLÜL — MİMAR TARAFI NOTLARI (Emir ekibi için)

**Dal:** `master` (uzak: `origin/master`) · **Yazan:** Claude 1 (mimar) · Halil tarafı
**Okuma sırası:** bu dosya → `DAL_CAKISMA_RAPORU_20260918.md` → `ONARIM/ONARIM-00_LISTE.md`

Aşağıdakilerin hepsi **ölçülmüştür**; ölçülmeyen her satırda "BEYAN" ya da "ÖLÇÜLMEDİ" yazar.

---

## 1. 🔴 ÖNEMLİ: Jetson **zaten güncel** — `navitas_tunel_staging` KURULMASIN

19 Eylül 00:20'de Jetson'a (`10.21.8.7`) bağlanıp ölçtüm:

| Kontrol | Sonuç |
|---|---|
| `~/navitas_tunel_staging/jetson_paket/kod/*.py` ↔ koşan `~/navitas/...` | **Tamamı birebir aynı** (`cmp`, tek fark yok) |
| `codes/rpi_inference.py` md5 | `eae1f19114…` = `origin/tunel-saha-20260918` ile **eş** |
| Servisler | 6 birim `active`, tünel kipinde (`seri_hub --tunel 127.0.0.1:14553 --tunel-kimlik hava`) |
| `iha_inis_yayinci` | `--kalkis-bekle` ile koşuyor (D-495 düzeltmesi kurulu) |

**Yani "Jetson güncellemesi bekliyor" kalemi fiilen kapalı.** Kod güncel; eksik olan yalnızca
systemd birimleriydi ve onlar da **kurulu hâliyle doğru**:

```
staging şablonu:  User=navitas      ExecStart=/usr/bin/python3 /home/navitas/navitas/...
kurulu (DOĞRU):   User=n4vitas      ExecStart=/opt/navitas/python/bin/python /home/n4vitas/navitas/...
```

⚠ **Staging'deki systemd dosyaları kurulursa sistem çöker** — kullanıcı adı ve yorumlayıcı yolu
yanlış. `/opt/navitas/python` bilerek kuruldu (ONARIM-10: venv bağımlılığı kaldırıldı, torch orada).

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

## 4. FOV **beyandır, ölçülmedi**

Servis `--fov 63` ile koşuyor. Bu değer `SAHA` kayıtlarında **BEYAN** olarak duruyor; IMX477 +
6 mm lens için 20–30 m'de gerçek ölçüm hiç yapılmadı (ONARIM-05 açık). FOV yanlışsa rota
koordinatları ölçekli olarak kayar. Ölçüm aracı hazır, yerde 10 dakikalık iş.

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

## 7. Bizden bekleyenler (Halil tarafı)

- Ethernet kablosu + 4S şarj: **kullanıcıda**, drone toplanıyor.
- Jetson erişimi açık, SSH ile çalışılabiliyor (`10.21.8.7`).
