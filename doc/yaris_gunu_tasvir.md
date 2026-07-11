# YARIŞ GÜNÜ TASVİRİ — TEKNOFEST İleri Otonom Sistemler Tasarım ve Operasyon Yarışması

**Takım:** Navitas Autonomous Systems (Takım ID 997827, Başvuru ID 5329027)
**Kaynaklar:** `doc/İleri_Otonom_Sistemler..._ÖDR_Şablonu_TR_13.04.pdf` (kavramsal tasarım, süre/başarı kriterleri) + resmi şartname (V2, 13.04.2026) özeti. Bağlayıcı olan şartname PDF'idir; bu metin operasyonel hazırlık ve simülasyon referansı içindir.

---

## 0. Büyük Resim: 6 Gün, 3 Periyot, 3 Senaryo

Yarışma **6 güne** yayılır ve **3 görev periyoduna** (her biri 2 gün) bölünür. Her periyotta
farklı zorlukta **bir senaryo** koşulur: **Kolay (K=1.0) → Orta (K=1.5) → Zor (K=2.0)**.
Zorluk katsayısı görev puanını doğrudan çarpar; yani zor senaryoda başarı, kolaydakinin
iki katı değerindedir.

Her periyotta takımın **yalnızca 1 uçuş hakkı** vardır — toplam 3. Kullanılmayan hak bir
sonraki periyoda **devretmez**; o turdan 0 puan yazılır. Bu yüzden yarış günü stratejisinin
özü şudur: *hakkını yakma, süreyi aşma, geçersizlik maddelerine düşme.*

### Saha Geometrisi

| Alan | Boyut | İşlev |
|---|---|---|
| İHA-UB (uçuş bölgesi) | 300×300 m | İHA'nın çıkamayacağı sınır — dışına taşmak uçuşu GEÇERSİZ kılar |
| HTAB (moloz alanı) | 50×50 m | Afet enkazı simülasyonu; içinde 3 yol, İKA burada sürer |
| İKA-KB (İKA kalkış bölgesi) | 1×1 m | İKA'nın başlangıç karesi |
| HB (hedef bölgesi) | 2×2 m | Kırmızı **H** — İKA buraya girince görev başarılı (P_görev=600) |
| İHA-İB (iniş bölgesi) | 30×30 m | Mavi alan — paraşütle iniş buraya; sapma metre başına −5 puan |

HTAB içinde İKA-KB'den HB'ye giden **3 yol** vardır. Her periyotta bunların **1'i açık,
2'si molozla kapalıdır** ve hangisinin açık olduğu **gizlidir** — açık yolu bulmak tamamen
İHA'nın işi, oraya ulaşmak tamamen İKA'nın işidir. Ekipten kimse yolu göremez/söyleyemez;
sistem uçtan uca otonom çalışmak zorundadır.

---

## 1. Sabah: Teknik Muayene ve Sahaya Giriş

Gün, pist kenarındaki teknik muayene çadırında başlar. Hakemler İHA'yı tartar
(**MTOW ≤ 25 kg** — hedefimiz 8–12 kg), İKA'yı tartar (**≤ 10 kg**, yük hariç; taşınan
yük **min. 200 gr**), beyan edilen sistemle (ÖDR/DDR/FDR'da yazanla) sahaya getirilenin
aynı olduğunu doğrular. **Beyandan farklı sistem = eleme.** Acil güç kesme anahtarları
(İtki + Aviyonik, REQ-25–28) dış yüzeyde, alet gerektirmeden erişilir olmalı; hakem
≤2 sn'de kapanmayı test edebilir. Paraşütün mekanik güvenlik kilidi ve mancınığın çift
kademeli emniyeti (fiziksel pin + elektronik kilit, REQ-59) kontrol edilir; Armed/Disarmed
LED+bayrak göstergesi (REQ-60) görünür olmalı.

Sahaya **en fazla 8 üye** girer — hepsi **baret + reflektif yelek** giymiş halde.
**Danışman sahaya giremez** ve saha içindeyken dışarıdaki danışmanla iletişim kurmak
**diskalifiye** sebebidir. Telefonlar cepte kalır.

---

## 2. Hazırlık: 15 Dakikanın Anatomisi

Hakem "süre başladı" dediği anda **15 dakikalık hazırlık** kronometresi işler. Bu süre
aşılırsa **o periyodun uçuş hakkı iptal olur** — daha havalanmadan 0 puan. Puanlama
formülünde hazırlık süresi de ödüllendirilir: `(900 − t_hazırlık)/30` puan; yani her
30 saniye erken bitirme +1 puan. Hedefimiz ~10 dk (ÖDR §6.1).

Kareografi önceden ezberlenmiş olmalı (roller kişiye atanmış, kim ne taşıyor belli):

1. **Mancınık kurulumu** (2 kişi): Alüminyum 6061-T6 ray açılır, yay+bungee kord gerilir,
   ray yönü rüzgâra göre hizalanır. Emniyet pini TAKILI kalır.
2. **İHA hazırlığı** (2 kişi): Çıkartmalı-takmalı modüler kanatlar gövdeye kilitlenir
   (tüm erişim panelleri kilitli — REQ-62), paraşüt bölmesi kontrol, batarya takılır.
3. **Aviyonik/yazılım** (2 kişi): Jetson Orin NX açılır, kamera pipeline'ı canlı doğrulanır,
   Pixhawk 6x GNSS fix bekler, 915 MHz RF telemetri YKS ile el sıkışır (<100 ms gecikme,
   300 m menzil). İKA tarafında RPi5 + GNSS+IMU+encoder füzyonu ayağa kalkar.
4. **İKA yerleştirme** (1 kişi): İKA, 1×1 m İKA-KB karesine konur, 200 gr yük kilitlenir,
   bekleme modunda (İHA inmeden hareket YASAK).
5. **Takım kaptanı**: kontrol listesini yürütür, her istasyondan "hazır" alınca hakeme
   **"TAKIM HAZIR"** der. Kronometre bu sözle durur.

⚠️ **"Takım Hazır" dendikten sonra sisteme her müdahale = +100 ceza puanı + süre eklenir.**
Yani emin olmadan "hazır" deme; ama gereksiz de oyalanma — ikisi de puan yakar.

Hakem heyeti son kontrolü yapar ve **"Uçuşa Uygunluk"** onayını verir. Güvenlik pilotu
kumandayı eline alır (yalnızca acil durum için — **manuel moda geçerse uçuş GEÇERSİZ**).

---

## 3. Fırlatma: Mancınık Anı

Elle atma, pistten kalkış, dikey kalkış — hepsi **YASAK**; tek meşru yöntem **mancınık**.
Hakem işareti ile emniyet pini çekilir, elektronik kilit açılır (Armed göstergesi yanar),
tetik bırakılır. İHA raydan **stall hızının en az 1.15 katıyla** (REQ-188) ayrılır.

**İHA görev kronometresi fırlatma ânında başlar: 15 dakika.** Aşarsa uçuş **GEÇERSİZ**.
Ama formül hızı da ödüllendirir: `(900 − t_İHA)/5` — her 5 saniye erken bitiş +1 puan.
Gerçekçi hedefimiz: tüm uçuş (fırlatma→tarama→aktarım→paraşüt) **3–5 dakikada** bitmeli.

---

## 4. Keşif Uçuşu: Açık Yolu Bulmak

İHA tam otonom tırmanır ve **~30 m irtifada** HTAB üzerine girer. Aşağı bakan geniş açı
kamera + Jetson üzerindeki **YOLOv8 segmentasyon modeli** ile 50×50 m alanı **serpantin
deseniyle 20–30 saniyede** tarar (ÖDR §6.2). Model her karede molozu ve geçilebilir
zemini ayırır; kararlar kare-üstü birleştirilir:

- **Tespit süresi hedefi:** açık yol sınıflandırması < 60 sn
- **Güzergah tespiti (toplam):** < 5 dk şartı, hedef 2–3 dk
- **Sınıflandırma doğruluğu:** ≥ %90 (test kriteri, Faz 3)

Çıktı: hangi yol açık (SOL/ORTA/SAĞ) + güven skoru + İKA'nın izleyeceği
**waypoint koordinat haritası** (İKA-KB referans çerçevesinde x,y noktaları).

---

## 5. Veri Aktarımı: Havadayken, Hakem Gözü Önünde

Kritik kural: **veri aktarımı İHA HAVADAYKEN yapılmalı ve hakem canlı olarak
doğrulamalıdır.** İnişten sonra aktarılan veri geçersizdir; hakem tespit teyidini/veri
akışını göremezse uçuş **GEÇERSİZ** (§6.4-3).

İHA, açık yol kararını + koordinat haritasını **915 MHz RF üzerinden MAVLink** ile hem
**YKS'ye** hem **İKA'ya** yayınlar (>%95 aktarım doğruluğu; hedef >%98). YKS ekranında
hakem şunu görür: açık yol etiketi, güven skoru, waypoint listesi, canlı telemetri
(≤200 ms güncelleme — REQ-22,23,24). Hakem "veri alındı" onayını verir.

Risk azaltma (ÖDR §6.3): iletişim koparsa yedek RF kanalı + MAVLink kalp atışı izleme +
otomatik failsafe; yanlış tespit riskine karşı güven eşiği + hakem onayı zorunluluğu.

---

## 6. Paraşütle İniş

Aktarım onayı gelince İHA, HTAB doğusundaki **30×30 m mavi İHA-İB** alanına yönelir,
irtifa keser ve **paraşüt otonom açılır** (barometre+GPS tetikli; REQ-12 mekanik kılavuz
paraşütün pervane/kanat/antene dolanmasını önler). Çöküş hızı **< 7 m/s** olmalı.

- Paraşüt hiç açılmaz + sert iniş → uçuş **GEÇERSİZ** (§6.4-6)
- Paraşütü **manuel** açmak zorunda kalırsak → **−50 puan** (uçuş geçerli kalır)
- İniş noktası İHA-İB merkezinden saparsa → **metre başına −5 puan**
- Gövde kırımı/yapısal bütünlük kaybı → GEÇERSİZ (**pervane kırılması hariç** — tek af budur)

Paraşüt yere değdiği an **İHA kronometresi durur** ve İKA fazının kapısı açılır.

---

## 7. İKA Görevi: Moloz Arasında 10 Dakika

Şartname §2.2.5: **İKA, İHA yere inmeden hareket edemez.** İniş teyidinden sonra YKS
operatörü İKA'ya **manuel başlat** komutunu verir (izin verilen tek insan dokunuşu) —
sonrası tamamen otonom. **İKA kronometresi: 10 dakika**; aşarsa görev başarısız.
Formül yine hızı öder: `(600 − t_İKA)/15`.

İKA, İHA'dan aldığı koordinat haritasını kendi konum tahminiyle
(**GNSS + IMU + encoder + kamera füzyonu**) çakıştırır, **A\* path planning** ile açık
yol üzerinde rota üretir ve diferansiyel sürüşle (4× 24V redüktörlü encoderli motor,
12–15 cm teker) moloz arasından ilerler. Engel haritası İHA verisinden kurulur (§5.3);
kamera yol takibini destekler, watchdog timer + güvenli durma modu navigasyon hatasına
karşı bekler. Gerçekçi hız ~1.0–1.5 m/s → ~65–80 m'lik kıvrımlı rota 1–2 dakikada biter.

İKA'nın gövdesi 2×2 m kırmızı **H**'nin içine girdiği an: **GÖREV BAŞARILI — P_görev = 600.**
Saha kenarında nefesler o an bırakılır.

---

## 8. Puanlama: Neden Hafif + Hızlı + Zor Kazanır

```
TOPLAM = 0.65·Puan2 + 0.20·P + 0.15·Puan1

Puan2 = K_zorluk · [ P_görev(600)
                     + (25000 − m_İHA)/10        ← İHA hafifliği (gram)
                     + (900 − t_İHA)/5           ← İHA hızı (saniye)
                     + (900 − t_hazırlık)/30     ← hazırlık hızı
                     + (10000 − m_İKA)/15        ← İKA hafifliği
                     + m_yük · 0.01              ← taşınan yük (gram)
                     + (600 − t_İKA)/15          ← İKA hızı
                     − cezalar ]
```

- **P** = teknik inceleme + uçuş performansı + centilmenlik puanları
- **Puan1** = rapor puanları (0.1·ÖDR + 0.25·DDR + 0.55·FDA + 0.1·UHDR) — FDA en ağır kalem
- **K_zorluk** parantezin TAMAMINI çarpar → zor senaryoda hafiflik/hız bonusları da 2×
  değerlenir. 10 kg İHA yerine 8 kg İHA, zor senaryoda tek başına +400 puan farktır.

---

## 9. Kırmızı Çizgiler — Tek Bakışta

**UÇUŞU GEÇERSİZ kılar (o tur 0 puan):**
1. İHA görevi > 15 dk
2. Güvenlik pilotunun manuel moda geçmesi
3. Hakemin tespit teyidini/veri akışını görememesi
4. İHA-UB (300×300) dışına çıkma
5. Kırım / yapısal bütünlük kaybı (pervane hariç)
6. Paraşüt açılmadan sert iniş

**DİSKALİFİYE ettirir (yarışmadan atar):**
- Hazır ticari / kopya tasarım kullanımı
- Sahadayken dışarıdaki danışmanla iletişim
- Hakeme/görevliye müdahale

**Puan yakar ama devam ettirir:**
- Manuel paraşüt −50 · "Takım Hazır" sonrası müdahale +100 ceza · iniş sapması −5/m

---

## 10. Günün Zaman Çizelgesi (İdeal Koşu)

| t | Olay |
|---|---|
| −60 dk | Teknik muayene, tartı, AAK/emniyet kontrolleri |
| 0 | Sahaya giriş, hazırlık süresi başlar (limit 15:00) |
| ~10:00 | "TAKIM HAZIR" — kronometre durur |
| +2 dk | Hakem "Uçuşa Uygunluk" onayı |
| T0 | **MANCINIK FIRLATMA** — İHA süresi başlar (limit 15:00) |
| T0+0:40 | 30 m irtifa, tarama başlangıcı |
| T0+1:10 | Serpantin tarama biter (~25 sn), model kararı oluşur |
| T0+1:30 | Açık yol + koordinat haritası YKS+İKA'ya aktarılır, hakem canlı onaylar |
| T0+2:30 | İHA-İB üzerinde paraşüt açılır (<7 m/s) |
| T0+3:00 | İniş — İHA süresi durur (~3 dk / 15 dk limit) |
| T0+3:30 | YKS'den İKA manuel başlat — İKA süresi başlar (limit 10:00) |
| T0+5:00 | İKA açık yolu izleyerek HB'ye girer — **P_görev 600** |
| sonrası | Log teslimi, hakem raporu, alandan çıkış |

Bu ideal akışta toplam saha operasyonu ~15 dakikadır ve süre bonuslarının neredeyse
tamamı alınır. Simülasyonun birebir bu akışı üretmesi hedeflenmektedir
(`simulation/` — mancınık→serpantin→aktarım→paraşüt→İKA→HB zinciri).
