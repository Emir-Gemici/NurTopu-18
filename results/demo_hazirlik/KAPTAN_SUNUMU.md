# KAPTAN SUNUMU — YKS HAKEM EKRANI (adım adım)

> Bu betik **prova edildi**: `results/demo_hazirlik/mutlu_yol.py` aynı akışı
> gerçek protokol yolları üzerinden uçtan uca koşar ve 8/8 adımı geçer
> (3 ardışık koşuda kararlı). Ekran görüntüleri: `06_normal.png`,
> `07_f4_batarya.png`.

---

## 0 · Başlatma

```
O:\navitas-local-train\venv\Scripts\python.exe comms\yks_gui.py --demo
```

`--demo` dahili İHA/İKA beslemesini açar: gerçek UDP, gerçek çerçeve biçimi,
gerçek ACK'ler. **Sahte olan yalnız uçağın kendisidir** — ekrandaki protokol
trafiği birebir yarışma günü yolundan geçer.

Süre sınırı **yoktur**: sunum ne kadar uzarsa uzasın besleme kesilmez.

Açılışta görülmesi gerekenler:
- Üst şerit: `HAZIRLIK ⏱ --:-- / 15:00 · İKA ⏱ --:-- / 10:00 · İHA ⏱ --:-- / 15:00`
- Zincir: `Kamera (İHA) → YOLOv8-seg → Rota Üretimi → 433 MHz TX → YKS (bu ekran) → İKA`
- Sağ altta canlı mesaj günlüğü akmaya başlar.

---

## 1 · Tespit gelir (≈3 sn)

**Hiçbir şeye basma.** Kendiliğinden olur:

| Ekranda | Anlamı |
|---|---|
| Sağ üstte büyük yeşil **`2 · ORTA`** | Üç güzergâhtan **açık olanı** (§2.1) |
| `seq=… · ref=(25.0, 2.0) m · 8 waypoint` | İKA'ya gidecek rotanın kimliği |
| `güven %91` çubuğu | Model güveni |
| Haritada yeşil koridor + kırmızı **KAPALI** şeritler | Serbest alan otoritedir; kırmızı = gidilemez |
| Sarı düğme: **`1) TESPİTİ DOĞRULA (§2.2.3)`** | Hakem onayı bekleniyor |

> **Söylenecek:** "Üç güzergâhtan hangisinin açık olduğuna model karar veriyor;
> yanlış güzergâh şartnamede **0 puan**. Bu yüzden karar tek başına yeterli
> değil — hakem onayına bağlı."

---

## 2 · Hakem onayı — 1. aşama

**`1) TESPİTİ DOĞRULA (§2.2.3)`** düğmesine bas.

- Günlük: `HAKEM 1/2: güzergâh TESPİTİ doğrulandı (§2.2.3)`
- Düğme, İKA'nın aktarım kanıtı gelene dek **2. aşamaya geçmez**.

> **Söylenecek:** "Şartname onayı **iki aşamalı** istiyor: önce tespitin
> doğruluğu, sonra İKA'ya **gerçekten aktarıldığının** teyidi."

---

## 3 · İKA aktarım kanıtı (kendiliğinden, ≈1 sn)

- Günlük: `İKA ALDI ✓ OPEN_ROUTE ACK ref=… (aktarım kanıtı ekranda)`
- Düğme **`2) İKA'YA AKTARIMI ONAYLA → ACK`** olur.
  (kanıt gelmeden `2) İKA ACK KANITI BEKLENİYOR` yazar)

> **Söylenecek:** "Bu satır İKA'nın kendi ACK'i. Ekranda 'gönderdim' değil,
> **'karşı taraf aldı'** yazıyor."

---

## 4 · Hakem onayı — 2. aşama

Düğmeye tekrar bas.

- Günlük: `HAKEM 2/2: İKA'ya aktarım doğrulandı → ACK ref=…`
- Etiket: `Hakem onayı tam — ACK(seq=…)`
- Tekrar gönderim durur (ACK geldi).

---

## 5 · İHA iner (kendiliğinden, onaydan ≈6 sn sonra)

- Günlük: `IHA_LANDED · üretim uçuşu iniş kanıtı alındı → ACK ref=…`
- Durum satırı: `LANDED 1`

> **Söylenecek:** "Şartname §2.2.5: **İHA yere temas etmeden İKA hareket
> edemez.** Bu bir yazı değil, ekranda **kilit**: kanıt gelmeden İKA BAŞLAT
> reddediyor."

**İsteğe bağlı gösteri:** Adım 5'ten **önce** `İKA BAŞLAT`'a basarsan günlükte
`KİLİT ✋ Üretim IHA_LANDED kanıtı alınmadan İKA hareket edemez (§2.2.5)`
çıkar. Kilidin gerçek olduğunu göstermenin en hızlı yolu budur.

---

## 6 · Alan girişi ve hazırlık (§6.2)

| Bas | Ekranda |
|---|---|
| **`ALAN GİRİŞİ`** | `HAZIRLIK ⏱` saymaya başlar (limit 15:00) |
| **`TAKIM HAZIR`** | Hazırlık süresi durur; `MÜDAHALE (−100)` açılır |

> `MÜDAHALE (−100)` ve `PARAŞÜT (manuel −50)` **ceza** düğmeleridir; sunumda
> basma — CEZA Σ artar. Var olmalarının sebebi, cezanın da ekrandan
> izlenebilir olması.

---

## 7 · İKA intikali

**`İKA BAŞLAT`**

- Günlük: `CMD → ika: IKA_GO (seq=…, ACK bekleniyor · 0.25 s × ≤20)`
- Günlük: `GÖREV · İKA İNTİKALİ BAŞLADI — kronometre limit 10:00 (kilit koşulları sağlandı ✓)`
- `İKA ⏱` saymaya başlar.
- ≈1 sn sonra: `İKA ALDI ✓ IKA_GO ACK ref=… · 1 gönderim` ve sağ altta `İKA ALDI ✓ <saat>`

> **Söylenecek:** "Komut ACK'siz teslim edilmiş sayılmıyor; ACK gelene kadar
> aynı seq ile en fazla 20 kez tekrarlanıyor."

---

## 8 · Görev tamam

**`HB TEMAS`**

- Günlük: `GÖREV · HB TEMAS — İKA süresi … dk → GÖREV BAŞARILI (P_görev = 600 puan)`

Sunumun bitiş cümlesi burasıdır.

---

## 9 · Arıza emniyeti tatbikatı (F1–F6) — istenirse

Her biri **tek tuş**. 6–7 sn sonra kendiliğinden normale döner.

| Tuş | Ekranda ne olur |
|---|---|
| **F1** RC kaybı | Bant sarı: `RC YOK — OTONOM GÖREVE DEVAM (AUTO)` |
| **F2** YKS kaybı | Bant kırmızı: `BAĞLANTI KAYBI — GÜVENLİ BÖLGEDE LOITER`; İHA düğümü söner, **sonra kendiliğinden geri gelir** |
| **F3** İKA kaybı | İKA düğümü söner; rota önbelleği korunur |
| **F4** Batarya | Bant kırmızı **ve panelde gerilim gerçekten düşer** (12.6 V → ~10.5 V) |
| **F5** GNSS | Bant sarı **ve uydu sayısı 0'a düşer**, konum donar |
| **F6** Algı aşımı | Bant sarı: tarama deseni yineleniyor |

> **Söylenecek:** "Bunlar metin değil: F4'e basınca **telemetri panelindeki
> gerilim de düşüyor.** Ekran kendi kendisiyle çelişmiyor."

Arka arkaya iki senaryoya basmak güvenlidir: geciken senaryo, sonrakinin
durumunu **bozmaz**.

---

## 10 · Elde tutulacak kurtarma tuşları

| Tuş | Ne yapar |
|---|---|
| **N** | Yeni tespit üretir (akış baştan) |
| **R** | Hakem onayını sıfırlar (onay akışını tekrar göstermek için) |
| **V** | Harita ↔ Canlı Algı görünümü |
| **K** | Canlı algı kaynağını değiştirir (yalnız CANLI ALGI görünümünde) |
| **←/→** | Algı görüntüleri arasında gezinir (yalnız CANLI ALGI görünümünde) |

> K veya ok tuşları harita görünümünde basılırsa **sessizce hiçbir şey olmaz
> demez** — günlüğe "yalnız CANLI ALGI görünümünde çalışır, V ile geçin"
> yazar.

---

## 11 · Canlı algı göstermek istersen

**V** → `Canlı Algı` görünümü. Model gerçek karelerde çalışır (v36, gerçek
çıkarım — canlandırma değil).

**Kaynak seçimi (2026-08-28 · D-325 ile GÜNCELLENDİ):**

| kaynak | ne gösterir | rota |
|---|---|---|
| `arena_kadraj` (açılış) | şartname kadraj kümesi — kabul dağılımı | **256/260 · %98,5** |
| `kompozit` | **kendi drone'umuzun gündüz karesi** üzerine kurulmuş arena | **49/88 · %56** |
| `drone` | otopark (arena DEĞİL) — alan boşluğunu gösterir | 14/40 |
| `dji_gece` | kendi gece prova uçuşumuz — nadir değil, arena yok | **0 (doğru ret)** |
| `gemini` · `test` · `val` | dış veri kümeleri, ölçek yok | **0 (`OLCEK_YOK` doğru)** |

⚠ Eski uyarı *"kompozitte rota çıkmaz"* **artık geçerli değildir** (T174 kapandı:
üreteç, karede araç yoksa kareyi atıyordu; kırsal zemin bu yüzden hiç
kurulamıyordu). Kompozit artık **K** ile gösterilebilir.

⚠ Son üç satırdaki sıfırlar **kusur değildir**: o kümelerde arena/koridor yok ya
da tek skaler ölçek yok. Orada rota üretmek başarı değil **yanlış pozitif**
olurdu (şartname §2.1: yanlış güzergâh = **0 puan**).

---

## 12 · Sunum öncesi 60 saniyelik kontrol

```
O:\navitas-local-train\venv\Scripts\python.exe results\demo_hazirlik\mutlu_yol.py
```

`SONUC: MUTLU YOL TAM` yazmalı. Yazmıyorsa sunuma girme — hangi adımın
düştüğünü satır satır söyler.
