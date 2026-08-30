# D-278–D-282 bağımsız denetim raporu

- Yeniden denetim tarihi: 2026-08-30
- Son hızlı doğrulama: 2026-08-31 · HEAD değişmedi; D-278/D-279/D-281/D-282
  yeniden koşuldu, D-280'in aynı HEAD'e ait ağır koşum kanıtı yeniden kullanıldı.
- Repo/HEAD: `O:\navitas` · `f0fd067`
- Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe`
- Yöntem: Defter kaydı, ham artefakt, yeniden üretim ve ham veriden bağımsız
  sayım ayrı ayrı karşılaştırıldı. Çalıştırılmayan veya hamdan çıkarılamayan
  sonuç `ÖLÇÜLEMEDİ` sayıldı.
- Yazma sınırı: Denetim çıktıları yalnız `results/codex_denetim/` altındadır.
  Kaynak kod, config, sözleşme ve dataset değiştirilmedi. D-278'in üreticisi
  geçici mutasyonlarını `finally` ile bayt-eş geri aldı. D-282/137 çıktısı
  önceki SHA-256 ile aynıdır. D-282/138, T145 sonrasında iki yeni ölçüt alanı
  ürettiği için eski JSON ile bayt-eş değildir; güncel çıktı denetim dizinine
  alındı ve görev dışı üretilen kopya HEAD baytlarına geri getirildi.
- Commit/push: yapılmadı.

## Hüküm özeti

| Kayıt | Hüküm | Kısa neden |
|---|---|---|
| D-278 | **KISMEN** | Davranış ve üç koruma doğrulandı; M2′ CRLF yüzünden uygulanmadı, betik yine exit 0 verdi. |
| D-279 | **KISMEN** | 708 sn ve 5,1 doğru; fakat yalnız 14/24 zamanlı kareyi ölçüyor. |
| D-280 | **KISMEN** | Kapı booleanları geçiyor; ham sayılar güncel HEAD'de kaydı tekrarlamıyor ve “net 6 kare” çıkarımı yanlış. |
| D-281 | **KISMEN** | Kural-kaldırma sonucu doğru; +3…+5 yalnız seçilmiş açılar ve nedensel kontrol eksik. |
| D-282 | **KISMEN** | +1 rota ve 0 piksel bozulma doğru; 0038 satırı yanlış, gürültü/kapsam hükümleri fazla güçlü. |

### D-278 — HÜKÜM: KISMEN

Koştuğum komutlar:

```text
O:\navitas-local-train\venv\Scripts\python.exe -B scripts/olcum/129_t141_mutasyon_olcumu.py
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_t141_rota_yoksa_surme.py" -v
O:\navitas-local-train\venv\Scripts\python.exe -B -m unittest discover -s tests -p "test_ika_surus_no_route.py" -v
```

Gerçek çıktı, kısaltılmış:

```text
POZITIF             T141 0/7 · mevcut 0/3
M1                  T141 1/7 · mevcut 1/3
M2 (ETKISIZ)        T141 0/7 · mevcut 0/3
M2'                 DESEN YOK ['ika_nav.py'] — UYGULANMADI
M3                  T141 3/7 · mevcut 0/3
M3b                 T141 1/7 · mevcut 0/3
GERI ALINDI         T141 0/7 · mevcut 0/3
bayt-es geri alindi: True
exit=0

test_t141_rota_yoksa_surme: Ran 7 tests ... OK
[KAPI T141] rota kapisi KAPALI · komut=5 · sifir-olmayan=0
exit=0

test_ika_surus_no_route: Ran 3 tests ... OK
[KAPI] NO_ROUTE etkin komut=3 · sifir-olmayan=0
exit=0
```

Kayıttaki sayı / benim sayım:

- Mutasyonsuz, M1, M2, M3, M3b ve geri-alma satırları
  `results/t141/mutasyon_olcumu.txt` ile aynı. **M2′ aynı değildir:** ham
  artefakt `1/7 · 0/3`, güncel koşu `DESEN YOK — UYGULANMADI` verdi.
- Kesin neden satır sonudur: `ika_nav.py` çalışma kopyasında 658 CRLF ve 0
  çıplak LF var; üretici M2′ için LF-sonlu
  `current_no_route is None\n` bayt desenini arıyor. Desen yokluğunda da
  çıkış kodu `0`; dolayısıyla bu koşum M2′yi sınamış sayılmaz.
- Geçici olarak hedeflenen üç dosyanın SHA-256 değeri koşum öncesi/sonrası
  aynıydı.
- `simulation/scripts/ika_nav.py` içinde üç koruma gerçekten var:
  döngü/pose öncesinde `rota_kapisi_acik()` (`:329-342`, çağrı `:364-366`),
  sıfır-dışı motor çıkışından hemen önce ikinci denetim (`:397-402`) ve
  `receiver_korumali_hiz_gonder` üzerinden karar kilidi altında atomik
  gönderim (`:251-263`). Üretim zinciri üçünü `ika_nav.py:492-500` içinde
  bağlıyor; asıl `RLock` denetimi `comms/ika_receiver.py:80-100` içinde.

Çıkarım sorgusu:

- “Üç noktada koruyor” üretimde bağlı iki çağrı yolu için doğrudur. Genel
  `navigate` API'sinde callback'ler varsayılan olarak `None`; iddia bütün olası
  dış çağrılara genişletilemez.
- `129_t141_mutasyon_olcumu.py`, desen yokluğu veya beklenmedik tablo halinde
  yine `0` döndürüyor. Bu betik tek başına fail-closed CI kapısı değildir;
  tablosu yorumlanmalıdır. Davranış unittest'i ise başarısızlıkta düşer.
- M1 ortak yardımcı üzerinden ilk iki kapıyı birlikte etkiliyor; atomik üçüncü
  katmanı tek başına kaldıran bir mutasyon yok. Tablo üç katmanın bağımsız
  katkısını kanıtlamıyor.
- HIL/aktüatör teslimi değil, Python `send_vel` komut akışı sınandı.

Başamelenin görmediği: Güncel yeniden üretici EOL-dayanıksız ve desen yokluğunda
fail-open. Bu, ana “bağlı üretim yolunda NO_ROUTE sırasında sıfır-dışı komut
yok” davranışını çürütmüyor; fakat mutasyon kanıtını bütünüyle geçti saydırmıyor.

### D-279 — HÜKÜM: KISMEN

Koştuğum komut:

```text
O:\navitas-local-train\venv\Scripts\python.exe -B results/codex_denetim/bagimsiz_sayim.py
rg -n "F4 pilot|dji_20260822[/\\]f4|toplam_saniye" scripts results/dji_20260822 -g "*.py"
```

Gerçek çıktı, kısaltılmış:

```text
A: 8 zamanlı, 0 null · satır toplamı 7031,4 sn
B: 2 zamanlı, 6 null · toplam 1357,0 sn
C: 4 zamanlı, 4 null · toplam 1522,0 sn
toplam: 14 zamanlı / 24 · 10 null · 9910,4 sn
ortalama: 707,885714 sn/kare · 5,085567 kare/saat
min/medyan/maks: 117,0 / 523,5 / 3151,9 sn
exit=0

üretici araması: yalnız F4'ü başlatan ön-kapı ile genel dji_hatti.py bulundu;
F4 insan-maskelerini baştan üreten betik bulunmadı · exit=0
```

Kayıttaki sayı / benim sayım:

- `9.910 sn`, `708 sn/kare` ve `5,1 kare/saat` doğru yuvarlamadır.
- A raporunun üst düzey `toplam_saniye=7031,3` alanı ile sekiz satırın
  `7031,4` toplamı arasında maddi olmayan `0,1 sn` fark var.
- 10 `null` süre gerçekten ortalamaya katılmamış. Bunları sıfır süre gibi
  payda 24'e katma karşı-olgusu `412,933 sn/kare`, `8,718 kare/saat` verir;
  fakat bu geçerli tahmin değildir, çünkü `null` sıfır değil bilinmeyendir.
- Ölçülen alt kümenin paralel cebiri `14*3600/7031,4 = 7,168 kare/saat` ve
  `200/7,168 = 27,90 saat` verir; kayıttaki 7,2/27,8 yuvarlamasına yakındır.
  JSON'larda eşzamanlı oturum başlangıç/bitiş damgası olmadığı için bunun
  gerçek duvar saati olduğu ayrıca doğrulanamıyor.
- 24 maskenin tümü 960×540 `uint8`, yalnız `{0,255}`; 24 farklı MD5 ve bozuk
  maske sayısı 0. F4 maskelerini baştan üretecek tek ve yeniden çalıştırılabilir
  üretici artefaktlarda bulunmadı: üretici yeniden koşumu **ÖLÇÜLEMEDİ**.

Çıkarım sorgusu:

- 5,1 değeri yalnız 14 zamanlı kare için ölçülmüştür. Eksik 10 kare B/C'nin
  önceki oturumlarından geldiği için eksiklik rastgele değildir; bu sayı bütün
  24 kareye veya gelecekteki 200 kareye koşulsuz “kapasite” diye taşınamaz.
- Dolayısıyla aritmetik kayıt kalabilir, başlık ve tarih tahmini “14 zamanlı
  karelik pilot alt kümesi” koşuluyla yazılmalıdır.

Başamelenin görmediği: En yavaş ve en hızlı kare arasında 26,9 kat fark var;
ortalama küçük ve sansürlü bir örneklemde kuyruk duvar saatini kararlı biçimde
tahmin etmiyor.

### D-280 — HÜKÜM: KISMEN

Koştuğum komutlar:

```text
NAVITAS_DEPO=O:\navitas
O:\navitas-local-train\venv\Scripts\python.exe -B results/codex_denetim/d280_shadow/scripts/olcum/65_kabul_denetcisi.py --model O:\navitas\codes\runs\segment\dji_kirsal_v1\weights\best.pt --ad codex_denetim
O:\navitas-local-train\venv\Scripts\python.exe -B results/codex_denetim/bagimsiz_sayim.py
O:\navitas-local-train\venv\Scripts\python.exe -c "... best.pt train_metrics ..."
```

İlk komut, denetçinin sabit çıktı yolunun ana ham artefaktı kirletmemesi için
aynı bayt betikler ve asıl modele bağlı güvenli gölge repoda çalıştırıldı.
`NAVITAS_DEPO` açıkça asıl salt-okunur depoyu gösterdi; bütün yazılar gölge
altında kaldı. Kalıcı çıktılar `results/codex_denetim/d280/` altına alındı.
Konsol kanıtı `guncel_65_kabul_20260830.log`, tam verdikt ise
`guncel_20260830_codex_denetim_kabul_verdikt.json` dosyasındadır. Geçici gölge
koşumdan sonra silindi.

Gerçek çıktı, kısaltılmış:

```text
K0 GECTI · figur %23,35 · raw bos 0/67 · cp bos 0/393 · güncel tabana oran 8,776928
K1 GECTI 257/260
K2 GECTI 10/257
K3 GECTI 0/257
K4 GECTI 1/257
K5 GECTI kesen 0/178 · toplam 0 px
sonradan eklenen K5A/K6/K7/K8 de GECTI
VERDIKT: URETIME ALINIR
exit=0
```

Kayıttaki sayı / benim sayım:

- Altı boolean hem tarihî artefaktta hem güncel koşuda `true`; dolayısıyla
  D-280'in kategorik “arena kapısı geçti” sonucu yeniden oluşuyor. **Ham
  sayılar ise birebir oluşmuyor:** K1 `255/260 -> 257/260`, K2
  `12/255 -> 10/257`, K3 `0/255 -> 0/257`, K4 `0/255 -> 1/257`, K5
  `0/171 -> 0/178`. K0 figür/raw/copy-paste aynı; K0 oranı
  `2,585452 -> 8,776928`, çünkü güncel denetçi tabanı artık v36'dan okuyor.
- Güncel `65` sonradan eklenen K5A/K6/K7/K8'i de koşuyor ve hepsi geçti.
  Bunlar 25 Ağustos D-280 hükmünün parçası değildir; tarihî altı kapıyla
  karıştırılmadı.
- `results.csv` 16 epoch içeriyor. `best.pt` içindeki `train_metrics`, CSV'nin
  epoch 1 satırıyla sıfır farkla eşleşiyor; mAP50-95(M) maksimumu epoch 1'de
  `0,19783`. mAP50(M) epoch 1/10/16 sırasıyla
  `0,32436 / 0,32584 / 0,31380`.
- `kiyas_109.txt`: v35/t127 figür zemin `0,15084`, aday `0,38997`;
  oran `2,585322` yani 2,6×. İçerik kaplama `0,5076 -> 0,3829`
  (`-12,47` puan). Bu sayılar kayıtla uyumlu.
- Bakır toplulaştırması da doğru: v35 `MASKE_YOK=35`, `ROTA=11`,
  `UC_BANT=13`; aday `29 / 10 / 20`.

Çıkarım sorgusu:

Kayıttaki “maske kazanan 6 kare rotaya dönüşmedi” açıklaması frame düzeyinde
yanlıştır. Aynı 59 karenin gerçek geçiş matrisi:

```text
v35 MASKE_YOK -> aday MASKE_YOK 24 · ROTA 2 · UC_BANT 9
v35 ROTA      -> aday MASKE_YOK  2 · ROTA 6 · UC_BANT 3
v35 UC_BANT   -> aday MASKE_YOK  3 · ROTA 2 · UC_BANT 8
```

`35 -> 29` yalnız net farktır: 11 kare maskesiz durumdan çıktı ve bunların
2'si rota kazandı; başka 5 kare maskesiz duruma geriledi. Ayrıca eski
rotalardan 3'ü UC_BANT'a düşerken eski UC_BANT'lardan 2'si rota kazandı.
Bu yüksek churn, “altı tekil maske kazanan ama hiçbiri rotaya dönmeyen kare”
şeklindeki monoton/nedensel hikâyeyi çürütür.

Başamelenin görmediği: Arena kabulü ve 2,6× risk sinyali sayısal olarak
doğrudur; fakat kırsal neden açıklaması düzeltilmeden kayıt bütünüyle kapanamaz.
Ayrıca komut, kabul betiği/karar yolu/üretim tabanı revizyonu sabitlenmediği
için tarihî ham sayıları bugünkü HEAD'de birebir yeniden üretmiyor; yalnız
kategorik geçiş ayakta kalıyor.

### D-281 — HÜKÜM: KISMEN

Koştuğum komut:

```text
O:\navitas-local-train\venv\Scripts\python.exe -B results/codex_denetim/bagimsiz_sayim.py
```

Gerçek çıktı, kısaltılmış:

```text
m4 n=59 · kural kalkınca yeni ROTA=0
PARCALILIK=11 · kural yokken GORUS_HATTI_KOPUK=11
açı farkları (döndürülmüş - yalnız küçültülmüş):
0,-6,+1,+4,+5,0,-1,0,+3,+3,+4,+3,+4,0,+4,+5,+5,+2
tam aralık=-6..+5 · ortalama=+2 · medyan=+3 kare
exit=0
```

Kayıttaki sayı / benim sayım:

- “En büyük bileşen kuralı kalkınca rota kazanan 0/59” doğrudur.
- 11 PARCALILIK karesinin 11'i
  `UC_BANT_TEMAS_YOK -> GORUS_HATTI_KOPUK` geçişi yapıyor; kural aynı kopuk
  topolojiyi başka aşamada görünür kılıyor.
- Kayıtta seçilen 30/40/90/120/160 dereceler gerçekten `+4/+5/+3/+4/+5`.
  Ancak bütün süpürme `-6..+5`; 10 derecede `-6`, 60 derecede `-1`, dört
  açıda `0` var.
- Alan ve eksen birlikteliği hamda yeniden görülüyor; aynı irtifa aralığı
  grupları ayırmıyor. Bu, “irtifa tek başına açıklamıyor” sonucunu destekler.

Çıkarım sorgusu:

- Önceden belirlenmiş bir açı veya açı-seçim politikası yok. Aynı 59 karede
  yalnız olumlu açıları seçip “net +3…+5” demek in-sample/oracle seçimidir;
  bütün deneyin sonucu bu aralık değildir.
- “Yalnız küçültülmüş” kontrol ölçek/kırpma kaybının bir bölümünü ayırıyor,
  fakat döndürme interpolasyonunu, topoloji değişimini ve gerçek uçuşta kadraja
  girecek yeni içeriği ayırmıyor. Görüntü döndürme, fiziksel uçuş yönünün tam
  nedensel karşı-olgusu değildir.
- “Hiçbir eksende geçmeyen 7 kare” cümlesi kapsam belirtmiyor. Hamda hiç
  `GECER` olmayan 11 kare var; iki `SINIF0_YOK` çıkarılırsa 9 kalıyor. Yedi,
  yalnız `en_iyi=PARCALILIK` alt kümesi olarak yeniden üretilebiliyor.

Başamelenin görmediği: Yönelim güçlü bir birliktelik ve aday müdahaledir;
“tek çalışan kaldıraç” veya %5–8 beklenen saha kazancı olarak kurulabilmesi için
ön kayıtlı uçuş politikası ve gerçek kadraj karşı-olgusu gerekir.

### D-282 — HÜKÜM: KISMEN

Koştuğum komutlar:

```text
O:\navitas-local-train\venv\Scripts\python.exe -B scripts/olcum/137_bant_bosluk_tanisi.py
O:\navitas-local-train\venv\Scripts\python.exe -B scripts/olcum/138_kare_uygunluk_denetimi.py --cikti results/codex_denetim/d282/kare_uygunluk_yeniden_20260830.json
O:\navitas-local-train\venv\Scripts\python.exe -B results/codex_denetim/bagimsiz_sayim.py
```

Gerçek çıktı, kısaltılmış:

```text
137: maske 160
     ZATEN_YETER 129 · KURTARILABILIR 26 · ZAYIF 1 · ENGEL 4
     iş listesi 27 · eksik bant 30 · etiketsiz medyan 0,80
     exit=0

138: referans 67 · keskinlik min/p05/p50/p95/maks
     405,94/465,27/606,62/888,10/960,94
     sonuç 160 · temiz 152 · ETIKET_COK_SEYREK 8
     exit=0

SHA-256:
bant_bosluk.json   9c569392e4a048d6df414e1b7dff3fd9af7f957a58ab07bd42340bafb726f60a
kare_uygunluk (güncel üretim)
                   42a7b5f5f976e0229395b0f4e88d3e1e29e0c6b96097c6658f695d940a28eb6c
```

`138`in güncel SHA'sı tarihî commitli JSON'dan farklıdır: T145 sonrasında
`parlaklik_alt=85,0` ve `gurultu_orani_ust=3,5` alanları eklendi. Buna rağmen
160 karedeki semantik sonuç değişmedi: eski ve yeni çıktıda `temiz=152`,
`ETIKET_COK_SEYREK=8`; kare bazında bayrak farkı `0`.

Kayıttaki sayı / benim sayım:

- `KURTARILABILIR 26 + ZAYIF 1 = 27`; 8 seyrek kareyle kesişim 4 olduğundan
  birleşim iş listesi `27+8-4=31`. Kayıtla uyumlu.
- Etki JSON'u: 160 karede `GECER 98->99`, `PARCALILIK 31->45`,
  `YAPISAL 29->15`, `SINIF0_YOK 2->1`; tek kazanan
  `...0037...frame_000146_000005910`, kaybeden 0.
- 31/31 yeni maske bir eski maskeyle eşleşti. `(m0 != 0) => (m1 == m0)`
  ihlali `0 piksel`. Eklenen sınıf 0 `593.683`, sınıf 1 `46.812`, toplam
  `640.495 piksel`.
- Defterdeki `BAKIR 0038 (60 kare): GECER 29->29` satırı yanlıştır. Etki
  JSON'unda 0038 **59 kare** ve `GECER 28->28`dir.

Gürültü mutasyonları:

```text
temel:          keskinlik 3718,12 · gök 0,0249 · bayrak []
Gauss bulanık:  keskinlik 1,41    · bayrak [BULANIK]
üst %8 gök:     gök 0,0950        · bayrak [NADIR_SUPHELI]
karanlık+noise: keskinlik 521,30  · parlaklık 15,99 · kırpma 0
                gürültü oranı 7,785 · bayrak [KARANLIK, GURULTULU]
```

Güncel `138` saf ölçüm/karar fonksiyonuyla ağır bulanıklık `BULANIK`, üst %8
gök bandı `NADIR_SUPHELI` üretti. 26 Ağustos denetiminde dört eski bayraktan
kaçan karanlık+gürültülü karşı örnek de artık T145'in iki yeni kapısıyla
`KARANLIK, GURULTULU` alıyor. Görseller ve ham sonuçlar
`results/codex_denetim/d282/` altındadır.

Çıkarım sorgusu:

- `kirpik_ust=0,20` ve `gok_ust=0,05` kaba yapay bozulmalara duyarlıdır;
  bulanıklık ve gök pozitif kontrolleri bunu gösteriyor. Fakat eşikler kusurlu
  karelerden oluşan etiketli bir doğrulama kümesine karşı kalibre edilmemiştir;
  sıfır bayrak, gürültünün yokluğunun kanıtı değildir. Tarihî false-negative
  T145 ile giderilmiş olsa da D-282'nin çıkarımı geriye dönük olarak güçlenmez.
- Yalnız eksik uç bantlar tamamlandı; iç bağlantı ve bütün maske kapsamı
  tamamlanmadı. D-281'in kural-kaldırma deneyi tamamlama öncesi yalnız 0038'in
  59 maskesinde yapılmıştı; D-282 sonrası 160 maskede yeniden koşulmadı.
  Bu nedenle “bu bant-tamamlama müdahalesi +1 getirdi” kanıtlıdır;
  “etiket kapsamı bağlayıcı değil” ve “daha fazla etiketleme önerilmez” daha
  geniş hükümleri kanıtlanmamıştır.

Başamelenin görmediği: 0038 tablosundaki 60/29 sayısı ham artefaktla uyuşmuyor;
ayrıca bir denetçinin hiçbir bayrak üretmemesi, ölçülmeyen kusur sınıflarının
yokluğunu kanıtlamaz. Bu ikinci boşluğun somut karanlık/gürültü örneği daha
sonra T145'te kapatılmıştır.

## Kapanış

- Bu yeniden koşuma göre koşulsuz kapanabilecek kayıt: **yok**.
- **D-278** ana davranış açısından ayakta; fakat M2′ üreticisinin CRLF üzerinde
  uygulanması ve desen yokluğunda nonzero çıkması gerekir.
- **D-279–D-282** kayıtları düzeltme/kapsam notu ister: D-279'da sansürlü pilot
  kapsamı; D-280'de kare-geçiş açıklaması; D-281'de açı seçimi ve nedensellik;
  D-282'de 0038 sayısı ile gürültü/etiket genellemesi.

Ek genel kapı:

```text
O:\navitas-local-train\venv\Scripts\python.exe -B codes/test_rota_sentetik.py
KOL 1: 15/15 · KOL 2 rota 15/15 · yayınlanan şerit 15/15
GENEL KAPI: GECTI
EXIT_CODE=0
```

Ham bağımsız sayımlar: `results/codex_denetim/bagimsiz_sayim.json`.
