# DEVAM NOKTASI — 4 Eylül 2026, 01:40 (gece çalışması sürüyor)

> Kullanıcı gece izni verdi ve uyumaya gitti. **Hedef: cumartesi 5 Eylül'e
> her şeyle hazır olmak.** Son commit: `8117c24`.

## Bu gece ne oldu

Kullanıcı "cumartesiye hazır mısın, emin ol" dedi. Ezberden cevap vermek
yerine cuma kartındaki listeyi **bugünkü kodla baştan koştum** (kartın
kanıtları bayattı — `jetson_baslat.sh`, `saha_baslat.py`, `kamera_koprusu.py`
4 Eylül'de değişti) ve ayrıca **"hazırız" iddiasını çürüten** bir tur başlattım.

🔴 **Çürütücü 13 tıkayıcı buldu.** En ağırları aşağıda.

## ✅ Bu gece kapananlar

**1. Runbook §3'ün kopyala-yapıştır bloğu ÖLÜYDÜ.** Codex `iha_komut_alici`ya
zorunlu `--izinli-kaynak` ekledi; runbook satırı onu taşımıyordu → argparse
çıkış 2. **Asimetrik ölüyordu**: `iha_inis_yayinci` kalkıyor, komut alıcı
ölüyor → sahada zincir *yarı canlı* görünür, iniş kanıtı akar ama ARM/PARAŞÜT
hiç ACK almaz. Düzeltildi + bayrağın ne olduğu runbook'a açıkça yazıldı +
çelişkili `--serial` maddesi düzeltildi.

**2. Bunu yakalaması gereken kapı 22/22 YEŞİLDİ.** `test_p4_runbook.py` sabit
bir jeton listesiyle substring arıyordu; `--izinli-kaynak` listede yoktu.
Yeni kapı **`tests/test_runbook_komutlari_kosuyor.py`** (3 test) runbook'un
bash bloklarındaki komutları **gerçekten koşar** ve argparse reddediyor mu
diye bakar. Mutasyon: bayrak runbook'tan çıkarılınca T1 düştü, dosya `cmp`
ile bayt-eş geri yüklendi.
*(Aynı sınıfın dördüncü tekrarı: D-415 yazım körlüğü, D-419 §5 kalıtım
körlüğü, sahte-kapı dedektörü, şimdi bu.)*

**3. D-413 bayatlıkları temizlendi.** `scripts/bellek_hazirla.py` hâlâ
"JetPack SD imajını microSD'ye balenaEtcher ile yaz" diyordu ve bu satır
**saha USB'sine gidiyordu**; kartta microSD yuvası YOK. `FAZ_B_GUN_PLANI.md`
(basılacak üç belgeden biri) aynı bayatlığı taşıyordu. İkisi de düzeltildi.

**4. Yazdırma listesi `SAHA_RUNBOOK.md`'yi atlıyordu** — hem de tüm başlatma
komutları oradayken. Eklendi.

**5. Cuma kartı §A 4 Eylül ölçümleriyle baştan yazıldı** ve **iki yanlış sayı**
bulundu: model dosyaları "54,8/54,6 MB" (ölçülen 52,3/52,0), tekerlekler
"51 dosya" (ölçülen 48). §B'deki 🛒/✅ satırlarına "**kullanıcı beyanıdır,
artefaktı yoktur**" notu düşüldü.

**6. Saha belleği iki kez tazelendi** — son hâli 01:38, HEAD `8117c24`,
405 dosya, 1268,5 MB, eksik zorunlu 0. Düzeltilmiş runbook içinde (2 kez
`--izinli-kaynak`), MANIFEST'te ölü microSD yordamı 0.

## ⏳ KOŞAN: saat kilidi onarımı (`wf_af878804-c1b`)

🔴 **En ağır bulgu ve gerçek bir uçuş emniyeti kilidi.**
`comms/iha_komut_alici.py` `_ornekle`: `abs(ham) > KOMUT_SAAT_SAPMA_TAVANI_S`
(1800 s) olan örneği **atıyor**. Ofset bilinmiyorken `ham` iki saatin farkıdır
— yani sapma 30 dakikayı aşarsa **öğrenmek için gereken örneğin kendisi
eleniyor** → ofset asla öğrenilmiyor → **ARM/DISARM/RTL/LAND/PARAŞÜT kalıcı
olarak reddediliyor**. RTC pili olmayan Jetson 1970'e açılabilir; sapma
saatler/yıllar olur. Sabitin yorumu "NTP'siz Jetson'ın makul sapma bandı"
diyor — bu varsayım yanlış.

İkinci kusur: ofset öğrenildikten sonra saat **basamaklı** düzelirse (NTP
adımı) eski örnekler 60 saniye boyunca eski ofseti tutuyor → o süre kritik
komutlar ölü.

**Mimarın kararı** (workflow'a verildi): tekrar savunması `(oturum, seq, cmd)`
anahtarıdır, saat kapısının işi **tazeliktir**. Tavan artık *öğrenmeyi* değil
*kaymayı* engeller: ofset bilinmiyorken büyük sapma örnek alınır ama tek bir
çerçeve kestirim kuramaz (≥N destekleyen örnek + dayanıklı özet); ofset
bilindikten sonra tavan **öğrenilen ofsete göreli** uygulanır. Saat adımı
algılanınca pencere boşaltılır. Ofset öğrenimi ve adım **görünür loglanır**.

İki çürütücü koşuyor: biri "saldırgan ardışık sahte damgalarla ofseti
çekebiliyor mu", diğeri "Jetson 1970'e açıldı, operatör kaç kez ARM'a basmalı".

## 🔴 Kapatılmayan çürütücü bulguları (sıradaki iş)

1. **USB, Jetson'a dosya götürmenin BELGELENMİŞ TEK yolu.** `scp`/`ssh`/
   ethernet alternatifi hiçbir kılavuzda yok; `JETSON_NANO_KURULUM` §3.4/§5
   doğrudan `/media/navitas/<BELLEK>/...` diyor. USB takılı değil.
   → Kuruluma **ethernet/scp alternatifi** yazılmalı.
2. **Nano'da `python3.8` kurulumu internete bağlı, çevrimdışı yedeği yok.**
   Zincir: sistem Python 3.6 → ultralytics kurulamaz → venv38 şart →
   `apt install python3.8` şart → apt internet ister. Cumartesinin en derin
   tek nokta arızası ve hiçbir insan listesinde yok.
3. **Taşıyıcı kartın MODELİ depoda hiçbir yerde yazmıyor** — kılavuz "temin
   edildi" işaretli ama ne repoda ne bellekte. eMMC boş çıkarsa FC REC pini
   tahmin edilemez.
4. **SDK Manager yolunun gerçek uzun kalemleri listede yok:** ~20 GB indirme,
   NVIDIA developer hesabı, micro-USB kablo.
5. **Kaynak pininin IP yarısı doğrulanmıyor** ve yanlışlığı YKS'de görünmüyor;
   `YKS_IP` `navitas.env`'de elle beyan ediliyor, DHCP ile değişirse tüm
   komutlar sessizce reddedilir (alıcı loglar, YKS görmez).
6. **`FDR/ACIK_KALEMLER.md` §1** sekiz kalemi koşulsuz "cumartesi kapanır"
   diyor; üçü **açılmış bir Jetson** gerektiriyor.

## Sonraki adımlar (sırayla)

1. `wf_af878804-c1b` sonucunu denetle, `cmp` ile delta bul, birleştir, ayna tazele
2. Yukarıdaki 1–6'yı kapat (1, 2, 3, 4 belge işi; 5 kod+belge; 6 kart hizası)
3. Tam süit + genel kapı → yeşilse commit + push
4. Belleği **son bir kez** tazele (runbook/kurulum değişirse)
5. `DEVAM.md`'yi kapanışta güncelle

## Kullanıcının beklediği

- **Cumartesi 5 Eylül'e her şeyle hazır olmak.** Kargo: UBEC, JST-GH kablo
  (sipariş edildi); Ubuntu host ve taşıyıcı kılavuzu "ayarlandı/temin edildi"
  (kullanıcı beyanı, artefaktsız).
- Ekran+klavye+ethernet, multimetre+tartı, kablolama sarfı **hazır** (beyan).
- `O:\navitas_bellek` → USB **tek eksik**; klasör hazır, USB takılı değil.
- `FDR/` klasörü ortak sürücüye yüklenecek (taşıma bitti, `8117c24`).

## Açık uyarılar

- ⚠ **Codex ana ağaca canlı yazıyor.** Bu gece de yazdı (`hakem_kaydi`,
  `inis_kaniti`, `protocol`, `yks_gui`, `rpi_inference` + 2 yeni test).
  Birleştirmeden önce `git status` ve mtime kontrol et; **yarım işi süpürme**
  (D-412 dersi).
- 🔴 Kol 1–2 / kol 3–4 farklı reçetelerle basıldı, gerekçesi kayıtta yok;
  yönerge "gerekliliği ispatlanmamış değişiklikler diskalifiye sebebi" diyor.
