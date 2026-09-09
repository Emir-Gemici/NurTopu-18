# 01 · YARIŞMA VE GÖREV — şartname ne istiyor, puan nereden geliyor

> Kaynaklar: `Ileri_Otonom_Sistemler_Tasarım_ve_Operasyon_Yarismasi_Sartname_TR_Ltktw.pdf` (V2, 13.04.2026, 30 sayfa; metni
> `results/sartname_bosluk/sartname_metin.txt`) · `ARCHITECT_PLAN.md` §1–§3 · `FDR/README.md` · `results/sartname_bosluk/rapor.md`
> (yazılıma düşen 22 hükmün kod karşılığı) · `simulation/score.py` (puan formülü, Tablo 6 ile birebir doğrulandı).

---

## Seviye 1 — Bir cümle ve büyük resim

**Görev:** İHA, afet bölgesini simüle eden **50 × 50 m** Hedef Tespit Alan Bölgesi'nin (HTAB) üstünden uçar; alanda **üç
güzergâh** vardır, yalnız **biri açık**, ikisi fiziksel engellerle (bariyer, enkaz simülasyonu vb.) kapalıdır ve hangisinin açık
olduğu takıma **gizlidir**. İHA açık güzergâhı görüntü işlemeyle bulur, **havadayken** yer istasyonuna (YKS) ve kara
aracına (İKA) aktarır; alan hakemi YKS ekranında **canlı** onaylar; İHA iner; ancak İHA **yere temas ettikten sonra** ve
YKS'deki takım üyesi **manuel tetikleyince** İKA açık güzergâhtan hedef bölgeye (HB: 2 × 2 m, üzerinde **kırmızı H**)
otonom gider ve brandaya **fiziksel temas** eder.

**Puanın mantığı:** yanlış güzergâh söylemek **0 puan** (görevi sıfırlar); söyleyememek yalnız puan kaybettirir. Bu
asimetri yazılımın tüm tasarımını belirler: **çekimserlik ucuz, yanlış karar pahalı.**

**İki ayrı araç var, karıştırma:**

| | görev test uçuşu (§5.3.2) | yarışma görevi (§2.2, §6) |
|---|---|---|
| ne zaman | **30 Eylül – 3 Ekim 2026** (takım provası 21 Eylül Adıyaman) | Ağustos–Eylül **2027** |
| araç | **çoklu rotorlu drone** (3B baskı quad) | **sabit kanat** + **mancınık** fırlatma + **paraşüt** iniş |
| alan | **20 × 20 m**, asgari irtifa **30 m** | HTAB 50 × 50 m; İHA-UB 300 × 300 m |
| İKA | **yok** | var |
| süre | kalkış→iniş **≤ 10 dk** | İHA ≤ 15 dk · İKA ≤ 10 dk · hazırlık ≤ 15 dk |
| puan | `FDA = FDR × 0,85 + uçuş × 0,15`; 100 tam puan = hakem onayı + 10 dk içinde; yanlış tespit = 0 | Tablo 6 formülü (aşağıda) |

Algı, karar, haberleşme ve YKS **iki araçta da aynı koddur**; fark uçuş kontrolcüsü yapılandırması, gövde ve YKS'nin
`--fda` bayrağıdır.

## Seviye 2 — Nasıl işliyor: görev akışı ve şartname hükümleri

### 2.1 Yarışma günü akışı (§2.2)

1. **Hazırlık** (≤ 15 dk; her 30 s'lik erken bitirme +1 puan): takım "hazır" der, kronometre durur.
2. **Fırlatma**: mancınıkla (§2.2.2); İHA **tam otonom** uçuşa geçer (fırlatmadan inişe insan müdahalesi yok, §6.2).
3. **Tespit** (§2.2.2): İHA HTAB üstünde görüntü işlemeyle açık güzergâhı bulur.
4. **Aktarım** (§2.2.3): güzergâh bilgisi kablosuz olarak **YKS'ye ve İKA'ya**, **İHA havadayken** iletilir. Alan hakemi
   YKS monitöründen tespitin yapıldığını **ve** İKA'ya aktarıldığını **onaylar**. Onaysız tespit geçersizdir (§6.2).
5. **İniş** (§2.2.4): paraşütle; paraşüt komutu otonomdur, manuel tetik **ceza** getirir (−50).
6. **İKA intikali** (§2.2.5): İHA yere temas etmeden İKA hareket **edemez** (ederse görev başarısız). İntikal YKS'deki takım
   üyesince **manuel tetiklenir**, sonrası tam otonom. Otonom hareket etmeyen İKA'nın görevi başarısız.
7. **Varış** (§2.2.6): İKA yükünü eksiksiz taşıyarak HB'ye ulaşır; yapısal bütünlük korunmalı; puan **brandaya temasla**
   (sınıra girmek yetmez, SS7).

### 2.2 Mutlak kesiciler (puan değil, sıfırlama) — `ARCHITECT_PLAN.md` §3

- Yanlış güzergâh tespiti → **0 puan** (§5.3.2, §6.2)
- Hakem onayı alınmayan tespit **geçersiz** (§6.2)
- Veri akışı sağlanamazsa uçuş **geçersiz** (§6.4)
- İHA yere temas etmeden İKA hareket ederse görev **başarısız** (§2.2.5)
- Otonom hareket etmeyen İKA'nın görevi **başarısız** (§2.2.5)
- İHA-UB (300 × 300 m) dışına taşma = alan ihlali (§6.2)
- Paraşüt açılmadan sert iniş → geçersiz (§6.4); süre aşımı → geçersiz
- Güvenlik pilotu manuel moda alırsa → başarısız (§6.4); hakem müdahalesi −100 ceza, süre hazırlığa eklenir

### 2.3 Puan formülü (Tablo 6; `simulation/score.py` birebir uyguluyor)

```
Puan  = 0,65 × Puan₂ + 0,20 × P + 0,15 × Puan₁
Puan₂ = K_zorluk × [ P_görev + (25000 − m_İHA)/10 + (900 − t_İHA)/5 + (900 − t_hazırlık)/30
                     + (10000 − m_İKA)/15 + (m_yük × 0,01) + (600 − t_İKA)/15 − C_ceza ]
K_zorluk = 1,0 (Kolay) · 1,5 (Orta) · 2,0 (Zor)      ← açık olan güzergâhın zorluğu, bizim seçimimiz değil
P     = P_TI + P_uçuş + P_centilmenlik
Puan₁ = 0,10×ÖDR + 0,25×DDR + 0,55×FDA + 0,10×UHDR
```

Yazılımın **doğrudan** etkilediği terimler: `P_görev` (600, K=2'de 1200: doğru güzergâh + brandaya temas),
`(900 − t_İHA)/5` (en çok 180: tespitin hızı), `(600 − t_İKA)/15` (en çok 40), `P_uçuş`. Yazılımın etkilemediği ama
**baskın** terim: `(25000 − m_İHA)/10` — 10 kg'lık İHA 1500 puan getirir, görev puanından büyük. Yani ağırlık düşürmek,
algoritma iyileştirmekten çok puan getirir; bu mimarın kaptana notudur (`ARCHITECT_PLAN.md` §3).

### 2.4 Takvim (şartname Tablo 1 — tek doğru kaynak)

| tarih | ne |
|---|---|
| 15.07.2026 | DDR teslim (sonuç 29.07) |
| **21.09.2026 17:00** | **FDR son teslim** — uçuş günü DEĞİL; takım o gün Adıyaman'da kendi provasını yapar |
| **30.09 – 03.10.2026** | Final Değerlendirme Aşaması: FDS sunumu + **drone ile görev test uçuşu** (tek atış) |
| 04.10.2026 | FDR sonuçları + maddi destek |
| 05.02.2027 | SGGS (sistem gözden geçirme sunumu) — üretim değişikliklerinde tutarlılık kontrolü |
| 16.04.2027 | UHDR (uçuşa hazırlık raporu) |
| 21.05.2027 | uçuş testleri · Ağustos–Eylül 2027 yarışma |

Projede bir kez "21 Eylül uçuş günü" sanıldı ve düzeltildi (D-410). Jüriye takvimi **doğru** söylemek önemli.

### 2.5 Yazılıma düşen 22 hüküm — nerede karşılanıyor (özet; ayrıntı `results/sartname_bosluk/rapor.md`)

| hüküm | kod karşılığı | durum (26 Ağu → bugün) |
|---|---|---|
| §2.1 üç güzergâhtan açık olanın tespiti | `rpi_inference.analyze_path` (üretim), `costmap_path_finder.rota_bul` (tanısal) | KANITLI (genel kapı iki kol 15/15) |
| §2.2.3 aktarım YKS + İKA, havadayken | `comms/iha_sender.KararYayinci` (her karede OPEN/NO_ROUTE, ACK'li) | KAPANDI (T146); SiK gerçek hat **ÖLÇÜLMEDİ** |
| §2.2.3 hakem canlı onay | `yks_gui` 2 aşamalı onay; 2/2 için İKA ACK kanıtı şart | KANITLI |
| §2.2.5 İHA inmeden İKA hareket edemez | `ika_receiver` üçlü kilit; iniş kanıtı Pixhawk'tan (`inis_kaniti.yerde_mi`) | KANITLI |
| §2.2.5 manuel tetik `IKA_GO` | ACK'li tekrar, üst sınırda kırmızı uyarı, düğme yeniden açık | KAPANDI (T147) |
| §2.2.5 İKA otonom sürüş | sürücü arayüzü hazır; **gerçek motor sürücüsü YOK** | AÇIK (T149, donanım) |
| §2.2.6 HB'ye varış = temas | son waypoint pedin kutusunda (253/256); İKA `FINAL_WP_RADIUS` 0,3 m < 1,0 m | kilitli; Gazebo teması ÖLÇÜLEMEDİ |
| §5.3.2 / §6.2 yanlış güzergâh 0 puan → fail-closed | güven eşiği, uç-bant, ölçek reddi, kaplama tavanı, koridor genişliği | KANITLI |
| §6.2 / §6.4 süre limitleri | `SARTNAME_IHA_GOREV_SURESI_S=900`, `SARTNAME_IKA_GOREV_SURESI_S=600`, hazırlık 900 | KAPANDI (T148) |
| §6.2 alan ihlali (İHA-UB) | heartbeat yerel `x,y` + YKS denetimi (`SARTNAME_IHA_UB_KENAR_M`) | yazılım kapandı (T162); Pixhawk geofence repo dışı |
| §6.4 veri akışı kesilirse | heartbeat 1 Hz, `link_lost` → güvenli duruş | KANITLI |
| §2.2.4 paraşüt | otonom: uçuş kontrolcüsü; manuel: YKS `PARACHUTE` komutu −50 ceza, ACK'li | FDA aracında paraşüt yok |

## Seviye 3 — Ayrıntılar ve sayılar

### 3.1 Alan tanımları (§2.1, s.7–8; kısaltmalar FDR Bölüm 0'da)
- **HTAB** 50 × 50 m: moloz yığınları, engeller; üç güzergâh (Kolay/Orta/Zor zorluk katsayılı).
- **İHA-FB** fırlatma bölgesi (ölçü verilmemiş) · **İHA-UB** uçuş bölgesi 300 × 300 m · **İHA-İB** iniş bölgesi **30 × 30 m mavi** ·
  **İKA-KB** İKA başlangıç bölgesi **1 × 1 m** · **HB** hedef bölge 2 × 2 m, kırmızı H.
- Şartname Şekil 1'deki arena görseli **yapay zekâ ile üretilmiş** bir illüstrasyondur (altyazısı öyle der; D-99); gerçek arenayı
  yansıtmaz. Bu yüzden takım "gerçek arena karemiz yok" der ve sentetik ölçümü saha başarımı diye sunmaz.
- **Ana şartnamede İHA için irtifa sınırı yoktur** (yalnız yatay İHA-UB); asgari 30 m yalnız görev test uçuşunda (§5.3.2).
- Yarışma **6 gün**, ardışık 2'şer günlük **3 görev periyodu**; her periyotta **1 uçuş hakkı** (toplam 3), kullanılmayan hak yanar.
- Sahaya en fazla **8 takım üyesi**; danışman giremez; baret ve yelek zorunlu (§6.2). Teknik muayene ilk denemede 100, ikincide 50.
- Şartnamede **olmayanlar** (jüri sorarsa "şartnamede belirtilmemiştir"): haberleşme frekansı/bandı (433 MHz takımın seçimi),
  batarya kimyası/gerilim sınırı, araç boyut sınırı, "kill switch" terimi, FDS sunum süresi/formatı, üç turun puan birleştirme
  yöntemi, İKA yük tanımı ("teknik gereksinimler listesi" PDF'lerde yok). `ozet/H_sartname.md` bunları sayfa numarasıyla listeler.

### 3.1a ⚠ "Üçüncü senaryo" PDF'si BU YARIŞMAYA AİT DEĞİL
Depo kökündeki `2026_TEKNOFEST_TYDA_SARTNAME_Ucuncu_Senaryo_TR_2_NoDue.pdf` **Yapay Zekâ Dil Ajanları Yarışması**'nın (Bilişim
Vadisi, video analiz/LLM) şartnamesidir; İHA/İKA yarışmasıyla ilgisi yoktur. Ana şartnamede "Senaryo 3" = **K_zorluk 2,0 (Zor
güzergâh)** periyodudur. Jüri "üçüncü senaryo" derse kastı budur; TYDA belgesine atıf yapılmaz.

### 3.1b Puan kalemleri ve cezalar (Tablo 6, s.24–26)
`P_görev` 600 (brandaya fiziksel temas) · `m_İHA` 25 000 g altındaki her 10 g = 1 · `t_İHA` 900 s'den her 5 s = 1 · `t_hazırlık`
900 s'den her 30 s = 1 · `m_İKA` 10 000 g altındaki her 15 g = 1 · `m_yük` her 100 g = 1 · `t_İKA` 600 s'den her 15 s = 1 ·
`P_TI` 100/50/0 · `P_uçuş` senaryo başına 200 (kırım yok + hedef tespit + İKA hareket) · `P_centilmenlik` ≤ 50 ·
**Cezalar:** iniş sapması **−5/m** (İHA-İB dışı), yeniden başlatma (hands-off sonrası müdahale) **−100**, manuel paraşüt **−50**.
Not: `simulation/score.py` formülü birebir uygular ama §6.4 geçersiz uçuş hâllerinde `Puan₂`'yi **sıfırlamaz** ve üç turu
birleştirmez; "Senaryo 1/2/3 = Kolay/Orta/Zor" eşlemesi koddaki varsayımdır, PDF'de açık yazmaz.

### 3.2 Görev test uçuşu (§5.3.2) — 30 Eylül
- Çoklu rotor, 20 × 20 m alan, asgari 30 m irtifa, kalkış + tespit + aktarım + iniş ≤ 10 dk.
- **100 tam puan**: gerçek zamanlı güzergâh tespitinin alan hakemince doğrulanıp onaylanması ve süre içinde bitmesi.
  Kriterlerden biri sağlanmazsa, süre aşılırsa **veya yanlış güzergâh** tespit edilirse **0 puan**.
- FDA'nın uçuş bacağı toplamın %15'i; **FDR %85**. Yani 21 Eylül'deki rapor, uçuşun kendisinden ağır.

### 3.3 Puan duyarlılığı — jüri "neden hız değil doğruluk?" derse
- Gereken kare hızı kapsama hesabından **0,9–2,6 FPS** (30 m irtifa, %80 örtüşme, 5–15 m/s). Tazelik penceresinden
  türetilen alt sınır **0,61 FPS** (`GEREKLI_FPS ≥ 1/(5·p)`, en kötü uçuş). 15 FPS hiçbir zaman şartname şartı değildi;
  kullanıcı kararıyla (18 Ağustos) hedef **3 FPS**, kabul edilen asgari **1 FPS** oldu (`ARCHITECT_PLAN.md` K-8).
- Yanlış güzergâh **sıfırladığı** için karar doğruluğu ölçüt hiyerarşisinde **1.** sıradadır; mAP **reddedilmiştir**
  (`CONTRACTS.md` §10): mAP lideri model (v13) arenada en kötüydü (%37,7 moloza basma).

### 3.4 DDR'den gelen gereksinim kimlikleri (jüri REQ numarasıyla sorabilir; `navitas-teknofest/references/ddr_requirements.md`)
REQ-1 İKA ≤ 10 kg · REQ-3 İKA ≥ 200 g yük · REQ-5 İHA ≤ 15 dk · REQ-6 hazırlık ≤ 15 dk · REQ-7 sabit kanat · REQ-8 mancınık ·
REQ-9 paraşüt · REQ-13 HTAB'de güzergâh tespiti · REQ-15 güzergâh İKA'ya · REQ-16 aktarım inişten önce · REQ-19 İKA tam otonom ·
REQ-20 İHA tam otonom · REQ-25–34 acil güç kesme · REQ-58 mancınık ray geometrisi · REQ-137 T/W ≥ 0,20 · REQ-158 MTOW ≤ 25 kg ·
REQ-185 havada kalış ≥ 0,5 sa · REQ-186 iniş dikey hız < 7 m/s · REQ-188 fırlatma sonrası ≥ 1,15 V_stall.
Yazılım tarafında kod ve testle kilitli olanlar: REQ-13, 15, 16, 19 zinciri. Yapısal/uçuş bilimleri REQ'ları
(137, 158, 185, 186, 188) **ölçülmedi** (final aracı üretilmedi) — FDR bunu açıkça yazar (Bölüm 1 §Y-1-M03).

### 3.5 Şartname yükümlülüklerinden **açık kalanlar** (dürüst cevap için)
1. Gerçek İKA motor sürücüsü yok (T149) — donanım kararı.
2. HB dedektörü üretime bağlı değil: gerçek inişte pedde %0 isabet ölçüldü (D-295 §2); bağlanırsa her kare `HEDEF_YOK`.
   Rota hedefi bugün karenin üst bandı; HB konumu İKA'ya `waypoints[-1]` olarak gidiyor (sentetik 253/256).
3. SiK 433 MHz gerçek hat hiç ölçülmedi; tüm aktarım kanıtı UDP loopback. DDR'deki ">%98 teslim, 300 m" iddiasının kanıtı yok.
4. Ölçek (mpp) gerçek Pixhawk telemetrisiyle sahada ölçülmedi (sahte yayınla GEÇTİ).
5. Karar kararlılığı: v36 v35'ten daha çok "rota VAR/YOK" çevriyor (D-295 §3); histerezis eklendi (D-396) ama `H1_ozgun=false`.

---

## Jüriye 30 saniyede

> "Şartnamenin bize düşen kalbi §2.2.3–2.2.5: tespiti havadayken YKS ve İKA'ya aktarmak, hakemin canlı onayı, İHA inmeden
> İKA'nın kıpırdamaması ve intikalin manuel tetiklenmesi. Bunların hepsi kodda kilit ve testle korunuyor. Yanlış güzergâh
> sıfır puan olduğu için sistem fail-closed: emin değilse rota yayınlamaz, sebebini yazar. 30 Eylül'deki test uçuşu
> çoklu rotorla, İKA'sız, 20×20 m ve 10 dakika; yarışma 2027'de sabit kanatla. Puanın büyük kısmı FDR'de (%85)."

## Kendini sına

1. Üç güzergâhtan kaçı açıktır ve bunu kim bilir?
2. İKA'nın hareket edebilmesi için şartnamede geçen **iki** koşul nedir? (Kodda üçüncü koşul hangisi?)
3. Yanlış güzergâh tespitinin puan sonucu nedir? Tespit yapamamanın?
4. 21 Eylül 2026 ne günüdür, ne günü değildir?
5. FDA puanında FDR'nin ağırlığı nedir?
6. Görev test uçuşu ile yarışma görevi arasındaki dört fark?
7. Puan formülünde yazılımın etkilemediği ama en büyük terim hangisi?
8. Hakem hangi iki şeyi onaylar?
9. Manuel paraşüt tetiğinin cezası kaçtır? Hakem müdahalesinin?
10. K_zorluk kimin seçimidir?

<details><summary>Cevaplar</summary>

1. Yalnız biri; hangisi olduğu takıma gizlidir, hakem bilir. 2. İHA yere temas etmiş olmalı (§2.2.5) ve YKS'deki takım üyesi manuel tetiklemeli; kodda üçüncü koşul geçerli bir `OPEN_ROUTE` olmasıdır (`sür ⟺ OPEN_ROUTE ∧ İHA indi ∧ IKA_GO`). 3. Yanlış tespit 0 puan (görev sıfır); tespit yapamama yalnız `P_görev`'i kaybettirir, diğer terimler kalır. 4. FDR son teslim günü ve takımın Adıyaman'daki kendi provası; resmî uçuş günü DEĞİL (o 30 Eyl–3 Eki). 5. %85 (uçuş %15). 6. Araç (quad / sabit kanat+mancınık+paraşüt), alan (20×20 / 50×50), İKA (yok / var), süre (10 dk / 15+10 dk). 7. `(25000 − m_İHA)/10`, İHA hafifliği. 8. Tespitin canlı yapıldığını ve İKA'ya aktarıldığını (2 aşama). 9. −50; −100 (ve süre hazırlığa eklenir). 10. Kimsenin; açık olan güzergâhın zorluğudur.
</details>

## Kaynaklar
`ARCHITECT_PLAN.md` §1–3 · `FDR/README.md` · `FDR/BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` (kısaltmalar) · `results/sartname_bosluk/rapor.md` ·
`codes/karar_sozlesmesi.py` (`SARTNAME_*` sabitleri) · `simulation/score.py` · `CONTRACTS.md` §6.7, §7, §7.1.
