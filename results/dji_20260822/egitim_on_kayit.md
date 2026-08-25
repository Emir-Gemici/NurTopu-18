# DJİ KIRSAL EĞİTİM TURU — ÖN KAYIT (D-107)

> **Yazıldığı an:** 2026-08-25, **hiçbir eğitim başlamadan önce.**
> **Yetki:** kullanıcı, *"işin bitince otomatik karar ver ve onay beklemeden
> çalışmaya ya da model eğitmeye başla."*
> ⛔ Bantlar **sonuca göre değiştirilmez.**

## 0. YETKİNİN SINIRLARI (bu turda korunanlar)
- **PUSH YOK** — CLAUDE.md §5 yürürlükte; kullanıcı açıkça kaldırmadı.
- **TERFİ YOK** — D-133: seçim ve sevk insanındır. Aday üretilir, `config/
  model_registry.json`'a **dokunulmaz**, Jetson paketi **değişmez**.
- **EŞİK / SÖZLEŞME DEĞİŞMEZ** — `CONTRACTS.md`, kabul zinciri eşikleri sabit.
- Görev kapatma yetkisi **mimarındır**.

## 1. NE SINANIYOR

*"Kırsal DJİ karelerini eğitime katmak, (a) arenayı BOZUYOR mu, (b) kırsal
domende İYİLEŞTİRİYOR mu?"*

Ölçülen taban (`uretim_yolu_olcumu.json`, 768 kare):
```text
v35 (uretim)  MASKE_YOK 395/768 = %51,4   rota URETTI 238/768 = %31,0
```

## 2. BÖLÜM — kaynak düzeyinde, ÖLÇÜLMÜŞ alan ayrımıyla

GPS ölçümü (`SU_ETIKETLEME_PLANI.md §1d`):
```text
0037 ∩ 0039 = 0037'nin %100'u  -> AYNI ALAN
0037 ∩ 0038 = 0 m²             -> HIC ORTUSMUYOR
0038 ∩ 0039 = 0038'in %1,5'i
```
⇒ **EĞİTİM: 0037 + 0039** · **BAKIR ÖLÇÜM: 0038**
⚠ Bu bir **alan ayrımıdır, oturum ayrımı DEĞİLDİR** — aynı gün, aynı kamera,
aynı operatör. Ayrı bir doğrulama uçuşunun yerini **tutmaz** ve raporda öyle
yazılır (D-256 §5). Terfi kararına tek başına dayanak olmaz.

## 3. BANTLAR — önceden yazılı

### (a) ARENA BOZULMADI mı — KAPI
| ölçüt | GEÇTİ | kaynak |
|---|---|---|
| kabul zinciri K0–K5 | **VERDİKT: True** | `65_kabul_denetcisi.py` |
| K1 rota | ≥ 230/260 | v35 tabanı 256 |
| 67 gerçek karede red | ≤ 5 | v35 tabanı 0 |
| çatı kaçağı | ≤ 0,10 | v35 tabanı 0,043 |

🔴 **Herhangi biri düşerse aday DÜŞER.** Eşik gevşetilmez, "az farkla" denmez.

### (b) KIRSALDA İYİLEŞTİ mi — ÖLÇÜM (kapı değil)
Bakır 0038 karelerinde, üretim yolundan:
| ölçüt | iyileşme sayılır |
|---|---|
| `MASKE_YOK` oranı | v35'ten **düşük** |
| rota üretilen kare oranı | v35'ten **yüksek** |

⚠ Bu bir **kapı değildir**: (a) geçip (b) iyileşmezse sonuç *"arenayı bozmadı
ama kırsalda da işe yaramadı"* diye yazılır. Başarısızlık gizlenmez.

### (c) 🔴 BAŞARISIZLIK SAYILACAK SONUÇLAR
- (a)'nın herhangi bir kalemi düşerse → **aday düştü**, kayda geçer.
- Kırsal veri arenayı bozarsa bu **beklenen bir risktir** (plan §8'de yazılı) ve
  öyle raporlanır; *"karışım oranını ayarlayıp tekrar deneyelim"* bu turda
  **yapılmaz** — o ayrı bir tur ve ayrı bir ön kayıt gerektirir.
- Etiketsiz oranı yüksek (parti 1'de %27–46). Eğer eğitim çöker ya da model
  hiçbir şey öğrenmezse, sebep **etiketsiz alanların anotasyon üretmemesi**
  olabilir; bu ihtimal **şimdiden yazılıdır** ve sonuç ona göre okunur.

## 4. ZİNCİR — tek betik, elle adım YOK
`scripts/olcum/135_dji_kirsal_zincir.py`
1. **kume** — üç durumlu maskeler → YOLO segment etiketi (etiketsiz = anotasyon YOK)
2. **bolum** — kaynak düzeyinde; fail-closed: *"kaynağı eğitimde de olan val = 0"*
3. **yaml** — mevcut karışıma **ek** bileşen (arena + RescueNet + copy_paste DEĞİŞMEZ)
4. **egit** — t127_temiz reçetesi **aynen** (farklı reçete değil; D-276'nın dersi)
5. **olcum** — kabul zinciri + bakır 0038 + 67 gerçek kare

## 5. KAPI
`codes/test_rota_sentetik.py` → **15/15** · `discover -s tests -q` → **811 OK**
Düşerse tur geri alınır (anayasa madde 14).
