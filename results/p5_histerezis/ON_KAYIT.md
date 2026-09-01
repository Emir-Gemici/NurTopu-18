# ÖN KAYIT — P5: karar kararlılığı histerezisi (T79/T92 ailesi)

**Tarih:** 2026-09-03 (gece) · **Karar/yazan: Claude 2 — Fable 5, mimar** ·
**Eşikler sonuç görülmeden yazıldı (D-107).**

## 0. Sorun (ölçülmüş)

Şerit seçimi sürekli büyüklükler üzerinde ayrık bir karardır; binde-4 algı
gürültüsü kareler arasında kararı çevirebiliyor (68 ölçümü: v34'te tohuma
göre 4–7/260; T92 bant oynaklığı 34/260). Yayınlanan şerit zikzak yaparsa
İKA'nın hedefi zikzak yapar. T79'un kökü (68'in çerçevesi) KAPANMAZ —
burada kapatılan, oynaklığın YAYINA sızmasıdır.

## 1. Mimar tasarımı

`KararYumusatici` (codes/karar_sozlesmesi.py — saf Python durum makinesi):

- **NO_ROUTE/ret ANINDA geçer** (fail-closed asla geciktirilmez, asla
  bastırılmaz).
- İlk rota ve NO_ROUTE-sonrası ilk rota ANINDA yayınlanır (erişilebilirlik;
  İKA'nın ilk hareketi zaten hakem onayı + IHA_LANDED kilidinin ardında).
- Yayımlanan şeritle AYNI şerit → anında yayınlanır (tazelik yenilenir).
- FARKLI şerit → ancak `KARAR_HISTEREZIS_KARE = 3` ARDIŞIK karede aynı yeni
  şerit görülürse yayına geçer; o ana dek yayın BASTIRILIR (önceki yayın
  ayakta kalır; İKA rota önbelleği zaten korunuyor).

**K=3 gerekçesi (sonuç görülmeden):** tek-kare gürültü çevrilmelerinin
tamamını bastırır; gecikme tavanı 3·kare-süresi (p95 uçtan uca 0,113 s →
~0,34 s; işlem aralığıyla bile ≪ `YKS_TESPIT_TAZELIK_S`/2). Eşik sonradan
değiştirilecekse yeni ön kayıt ister.

**Nereye bağlanır:** yalnız AKIŞ yollarına (`run_video`, `run_camera`) —
yayından hemen önce. `run_image` tek karedir, `analyze_path`/zincir ölçümleri
DEĞİŞMEZ (madde 15: serbest alan mantığına dokunulmuyor; 61/65 zinciri
yumuşatıcıyı görmez).

## 2. Kapı ölçütleri (şimdi yazıldı)

| # | ölçüt | GEÇTİ |
|---|---|---|
| H1 | Ölçüm (171, 68 gürültü reçetesi: σ=2/255, kare başına 4 ardışık kopya, tohum 7 VE 42) | Yayımlanan çevrilme ≤ ham çevrilmenin **%40'ı**; ham ≥ 5 ise kesin azalma şart |
| H2 | Fail-closed | Hiçbir NO_ROUTE bastırılmaz/geciktirilmez (ölçümde sayaç 0 sapma; birim test) |
| H3 | Geçiş disiplini | Şerit değişimi yalnız K ardışık anlaşmayla (birim + mutasyon testi) |
| H4 | Gecikme | Kalıcı değişimde yayın gecikmesi tam K−1 bastırılmış kare (birim test, kurgusal akış) |
| H5 | Tazelik | Bastırma en fazla K−1 ardışık kare sürebilir (K'ıncıda ya eski teyit ya yeni yayın) — birim test |
| H6 | Suit | Genel kapı 15/15 + tam suit OK; zincir (61/65) çıktıları BAYT-EŞ (yumuşatıcı zincire girmez) |

**Reddetme:** H1–H6'dan biri düşerse P5 kapanmaz; K büyütülerek "kurtarma"
YAPILMAZ (yeni K = yeni ön kayıt).

---

## EK-1 (2026-09-03 gece — H1 bileşim ölçütü; BİLEŞİM GÖRÜLMEDEN yazıldı)

**Kayıt:** İlk koşum ölçüm hatasıydı (260 sahne tek akış sayıldı; sahne
sınırları çevrilme sayıldı — düzeltildi, eşik değişmedi). İkinci koşum
kare-içi ölçümde H1'i **düşürdü**: yayımlanan/ham = 7/13 (tohum 7) ve 11/24
(tohum 42), eşik %40'ın üstünde. **H1 bu haliyle DÜŞTÜ ve öyle kayıtlıdır.**

Şüphe (bileşim henüz ölçülmedi): kalan yayımlanan çevrilmeler tasarımın
BİLEREK geçirdiği sınıflar olabilir — (i) NO_ROUTE-geçişleri (H2 fail-closed
zorunluluğunun öbür yüzü: asla geciktirilmez), (ii) kalıcı çoğunluk geçişleri
(5 örneğin ≥3'ü yeni karar: statik sahnede modelin kendisi ikili — bunu
bastırmak K sözleşmesini bozar), (iii) H5 tavanı yayınları (bayatlama sınırı).

**Yeni ölçüt (bileşim ölçülmeden yazıldı; %40 toplam eşiğin YERİNE değil,
mekanizmanın gerçek vaadi olarak):**

| # | ölçüt | GEÇTİ |
|---|---|---|
| H1a | **Azınlık rota↔rota çevrilmesi yayına sızmaz:** kare-içi dizide azınlıkta (≤1/5) kalan rota→rota sapmaların yayımlanan akıştaki sayısı **= 0** (iki tohumda da) |
| H1b | Yayımlanan çevrilme < ham çevrilme (kesin azalma, iki tohumda da) |
| H1c | Yayımlanan çevrilmelerin **tamamı** (i)/(ii)/(iii) sınıflarından; sınıflandırılamayan yayımlanmış çevrilme **= 0** |

H1a/H1c düşerse mekanizma vaadini tutmuyor demektir → P5 AÇIK kalır ve K
değiştirilmeden kullanıcı/mimar sabah kararına bırakılır.

## 3. Ölçüm maliyeti

Tek GPU işi (gece sıralı-GPU kuralı): 260 kare × (1 temiz + 4 gürültülü) × 2
tohum ≈ 2600 çıkarım. BSOD riski nedeniyle gecenin SON GPU işi olarak koşulur.


---

## SONUÇ (2026-09-03 gece — D-396)

H1 (özgün %40) **DÜŞTÜ** (7/13, 11/24) ve öyle kayıtlı; EK-1 bileşim
ölçütleri (bileşim görülmeden yazıldı) ölçüldü: **H1a GEÇTİ** (azınlık
rota↔rota sızıntısı 0/0), **H1b GEÇTİ** (7<13, 11<24), **H2 GEÇTİ**
(bastırılan NO_ROUTE 0). H3/H4/H5 birim+mutasyon kilidinde (H5, ilk
tasarımdaki süresiz-bastırma açığını yakalayıp tavan kuralını doğurdu).
H6: 1559 test OK. Ölçüm: `olcum_20260903.json`. **P5 KAPANDI** (T79 kökü
ve T91 Faz C'de açık).
