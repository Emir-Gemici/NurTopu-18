# Yazılım uygunluk ölçümü — 20 Eylül 2026, Adıyaman

> **Soru:** "Yazılım gerçekten uygun mu?" (kullanıcı, 20 Eyl sabahı)
> **Ölçüt:** FDA görev akışının her halkası için → hangi kod → hangi kanıt → hüküm.
> Hüküm üç değerlidir: **ÖLÇÜLDÜ-GEÇTİ** · **ÖLÇÜLDÜ-DÜŞTÜ** · **ÖLÇÜLMEDİ**.
> "Çalışıyor gibi görünüyor" bir hüküm değildir; bu tabloya girmez.
>
> Kaynaklar: `BILGILENDIRME_HE/00–08` (Emir tarafı, dal `bilgilendirme-he`, 19 Eyl 21:38),
> `REVIEW_LOG.md` D-505…D-516, `results/push_kapisi/20260919_211422/`, FDR Bölüm 1.

## 0. Hangi uçuş, hangi araç

- **FDA görev test uçuşu aracı** = quadcopter. Paraşüt, mancınık, **İKA YOKTUR** (şartname §5.3.2).
- 🔴 **TAKVİM DÜZELTMESİ (20 Eyl, dış kaynak araştırması).** FDR Bölüm 1 şöyle diyor:
  *"30 Eylül – 3 Ekim'de uçacak olan budur; **provası 21 Eylül Adıyaman**."*
  **Bu satır BAYATTIR.** İki bağımsız kaynak aksini söylüyor:
  - TEKNOFEST resmî sayfası: **"FDR Sunumları: 21 Eylül – 3 Ekim 2026"**.
  - Yerel basın (iki ayrı gazete, aynı bilgi): *"İleri Otonom Sistemler Tasarım ve Operasyon
    Yarışması, **21–25 Eylül'de Adıyaman Üniversitesi Stadyumu'nda** yapılacak"*;
    **23–25 Eylül** ziyarete açık günler.
  - Yani **21 Eylül bir prova günü değil, Adıyaman programının BİRİNCİ GÜNÜDÜR.**
  - ⚠ **Bilmediğim:** takımın kendi slotu (hangi gün sunum, hangi gün uçuş). Bu KYS kaydında
    ve ekipte olan bir bilgidir, dış kaynaktan çıkarılamaz. **İnsan teyidi bekliyor.**
  - **Sonucu:** "yarın puan alınmıyor" varsayımı **düşürüldü**. Aşağıdaki iki 0-puan riski
    bugün kapatılmak zorundadır; ertelenecek gün yok.
- İKA'nın FDA'da olmaması bir eksik değil, **tasarım**: YKİ'nin `--fda` kipi İKA aktarım kanıtını
  aramaz, yoksa hakem onayı hiç tamamlanamazdı (FDR B1 §171-174).

## 1. Zincir ölçümü

| # | Halka | Kod | Kanıt | Hüküm |
|---|---|---|---|---|
| L1 | Kamera → model → şerit kararı | `codes/rpi_inference.py` + model | Genel kapı **15/15 kol1 · 15/15 kol2** (`results/push_kapisi/20260919_211422/genel_kapi.txt`) — ama bu **sentetik, kusursuz maske**. Kullanıcı beyanı (20 Eyl): model **gerçek arena zemininde HİÇ denenmedi** | 🔴🔴 **ZİNCİR KOPUK (20 Eyl ölçümü)** — Jetson'da `/dev/video*` YOK, her iki CSI I2C bus'ı boş; CSI konnektörünün ZIF mandalı kırık. Kamera yoksa şerit kararı da rota da yok. Bkz. D-520 |
| L2 | Rota üretimi (costmap → waypoint) | `costmap_path_finder.rota_bul` | aynı kapı, kol 1 | ÖLÇÜLDÜ-GEÇTİ |
| L3 | **Kamera montaj açısı (montaj_yaw)** | karar görüntü çerçevesinde; `--montaj-yaw` yalnız görev üreticisinde | **hiç ölçülmedi (A9 yapılmadı).** Kamera montaja 90° çevrilerek sığdı | ✅ **ÖLÇÜLDÜ 20 Eyl: montaj_yaw = +90°** (ok testi; burun görüntüde **solda**). Görev üreteci zinciri koşuldu, β=0 → CONDITION_YAW 270 ✓. Uçuşta ekrandan teyit: rota aşağıdan yukarı akmalı. D-521 |
| L4 | Jetson → telsiz → YKİ taşıma | `comms/mavlink_tunel.py`, `seri_hub`, `scripts/yer_yonlendirici.py` | Gerçek boyda rota 414 B / 4 parça, **ilk gönderimde 0,40 s** (D-514) | ÖLÇÜLDÜ-GEÇTİ |
| L5 | **Hakem 2 adımlı onayı → ACK** | `comms/yks_gui.py` (dal `bilgilendirme-he`) | ACK 0,22 s'de Jetson'da (D-514). **Ama** 19 Eyl akşamı bulunan hata: yeni seq onayı siliyordu. Düzeltme `a2e69b9b`+`db692109`, yalnız masada test edildi | ⚠ **KULLANICI BEYANI: Emir YKS testini yaptı (20 Eyl)** — ancak `hakem_log.jsonl` ve hüküm bu pakette **YOK**. Kanıtsız beyan tabloyu kapatmaz (md. 6). **AÇIK kalıyor**; kanıt gelince ya da `CODEX_DEVIR/03` §3 provası geçince kapanır |
| L6 | Hız kapısı K8 (p95 < 200 ms) | telsiz + TELEM1 turu | K8a **212,4 ms** · K8b **278 ms** · Jetson hiç yokken bile **204,9 ms** (D-509, D-511) | ❌ **ÖLÇÜLDÜ-DÜŞTÜ** — eşik gevşetilmedi |
| L7 | Telemetri dürüstlüğü (0/0 konum, 890 m irtifa) | YKİ: `21ae2f5f`+`eb6a0c20` · Jetson: `c9ee27f0` | YKİ tarafı denetlendi ve kuruldu. **Jetson tarafı yazıldı, denetlendi, KURULMADI** | ⚠ **YARIM** |
| L8 | Yer bağlantısı dayanıklılığı (USB çek-tak) | `185c2f97` | Canlı: 8,0 s'de kendiliğinden geri bağlandı (D-514) | ÖLÇÜLDÜ-GEÇTİ |
| L9 | Jetson güç sürekliliği | — (donanım) | 18:10 ve 18:21'de **iki ani kapanma**, güç kesintisi imzası; dokunulmayınca 52 dk temiz (D-512) | 🔴 **AÇIK RİSK — yazılım değil, İNSAN işi** |
| L10 | GCS failsafe davranışı | `FS_GCS_ENABLE 5` | Jetson açıkken 25 s heartbeat boşluğunda failsafe çıkmadı; Jetson kapalıyken MP 5 s koparsa LAND (iki kez yaşandı) | ÖLÇÜLDÜ-GEÇTİ (kural: **yazılımla uçuş yalnız Jetson açıkken**) |
| L11 | Tam test süiti | 3119 test | **KIRMIZI**: 21 failure + 11 error. Taban (eb6a0c20) temiz klasörde **33** kırmızı, bu dalda **32** | ⚠ **BORÇ — yeni gerileme yok**, ama anayasa §5'e aykırı durum kayıtlı |
| L12 | **Alan ihlali denetimi** (şartname SS6.2/SS6.4) | `rpi_inference --ub-referans` | Jetson günlüğünde her açılışta: *"--ub-referans verilmedi … HEARTBEAT'e x,y EKLENMEZ; YKS ALAN IHLALI denetimi YAPILAMAZ"*. `/etc/navitas.env` → `RPI_EK_ARGS` içinde `--ub-referans` **yok** | 🔴 **YAPILAMIYOR** — kod hatası değil, eksik parametre. Kaynak: `JETSON_GERCEK_DURUM.md` §6 |
| L13 | Jetson'a saha erişimi | `l4tbr0` USB aygıt kipi | 19 Eyl dökümü: `l4tbr0 DOWN 192.168.55.1/24` — köprü **kurulu**, yalnız kablo yoktu | ✅ **YOL VAR** — USB veri kablosu yeter; ethernet/wifi/dongle gerekmez |

## 2. Hüküm

**Taşıma zinciri ve karar zinciri ayaktadır.** İHA'nın kararı, GPS'i ve gerçek boyda rotası
telsizle YKİ'ye geliyor; hakemin onayı Jetson'a dönüyor; hepsi ethernetsiz ölçüldü.

**Ama uygunluk, ölçülmemiş iki halkada askıdadır** ve ikisi de **0 puan** sınıfıdır:

1. **L3 — kamera montaj açısının işareti.** Ölçülmemiş bir işaret, yanlış şerit demektir.
   Kapatma maliyeti: **2 dakika** (ok testi, 05).
2. **L5 — hakem onayının canlı kalıcılığı.** Düzeltme var, canlı kanıt yok. Üretim her saniye
   yeni seq üretiyor; masadaki test hep aynı seq'i yolladığı için hatayı görmedi.
   Kapatma maliyeti: **bir test betiği + 5 dakika prova.**

**K8 düştü ama görevi tıkamıyor.** Gerekçe ölçümledir, iyimserlik değil: rota ilk gönderimde
0,40 s'de, ACK 0,22 s'de ulaştı. Darboğaz telsizin TDM turudur (Jetson hiç yokken de p95 205 ms),
yani yazılımla kapanmaz. Hüküm: **eşik gevşetilmez, kapı DÜŞTÜ olarak kalır**; görev akışı
tekrar mekanizmasıyla sürer. K8'in yazılım kaldıracı (aynı kararı 1 Hz'de gönder) **uçuş sonrası** iştir.

**Bugün eklenen üçüncü açık (L12):** YKS alan ihlali denetimini **yapamıyor**, çünkü İHA heartbeat'ine x,y konmuyor. Bu ölçülmemiş bir risk değil, **bilinen bir eksiktir** ve şartnamenin iki maddesine dokunur. Düzeltmesi bir parametredir (`--ub-referans`), ama referans noktasının **sahada ölçülmesi** gerekir — yani insan işidir.

**L1'in sınırı dürüstçe yazılmalıdır:** genel kapı sentetik ve kusursuz maskeyle koşuyor.
Modelin **gerçek Adıyaman zemininde** ne yaptığı hiç ölçülmedi. Gazebo'da düz/dokusuz zeminde
model karelerin %93'ünü "blocked" saymıştı (memory: gazebo-algi-boslugu-olculdu). Bu yüzden
yarının provasındaki **en değerli ölçüm, gerçek zeminden gelen ham kare ve model çıktısıdır.**

## 3. Bilinmeyenler — 20 Eyl akşamı durumu

| Soru | Durum |
|---|---|
| 21 Eyl prova mı, puanlı mı? | ✅ **Araştırıldı:** Adıyaman programı 21–25 Eyl, stadyumda. Prova değil. **Takımın kendi slotu hâlâ insan teyidi bekliyor** |
| Model gerçek arena zemininde denendi mi? | ✅ **Cevaplandı: HAYIR** (kullanıcı, 20 Eyl). L1 hükmü buna göre düşürüldü |
| Zemin nasıl (asfalt/toprak/çizgili)? | ⏳ **Açık.** Ekip 20 Eyl öğleden sonra Adıyaman'a vardı, alana henüz yerleşilmedi |

### L1 için bugünün en ucuz ölçümü

Jetson + kamera ayağa kalkar kalkmaz, **gerçek zeminden ham kare al** (kamera köprüsü
`kare.jpg`) ve modeli o kare üzerinde **çevrimdışı** koştur. Uçuşa gerek yok, arenaya bile
gerek yok — stadyum zemini yeterli. Ölçülecek tek şey: model bu zemini "serbest" görüyor mu,
yoksa Gazebo'daki gibi "blocked" mu sayıyor.
**Bu ölçüm yapılmadan L1 hakkında söylenen her şey tahmindir.**

## 4. Kaynaklar (takvim araştırması)

- teknofest.org → İleri Otonom Sistemler Tasarım ve Operasyon Yarışması (FDR Sunumları 21 Eyl – 3 Ekim 2026)
- gunebakisgazetesi.com · isikgazetesi.com — "21–25 Eylül, Adıyaman Üniversitesi Stadyumu; 23–25 Eylül ziyarete açık"
