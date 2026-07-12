# Navitas Teknik Sözlük — "5 yaşında gibi" anlatım
# Format: olan şey => ne yaptığı, ne işe yaradığı, projede nerede kullanıldığı

## MODEL / YAPAY ZEKÂ

- **YOLOv8n-seg** => Fotoğrafa bakıp "şu pikseller yol, şu pikseller moloz" diye boyayan yapay zekâ modeli. "n" = nano, ailenin en küçüğü (3,4 milyon parametre) — küçük bilgisayara sığsın diye seçildi. Bizde: `navitas_seg_v2_best.pt`, İHA görüntüsünden açık yolu bulur.
- **Segmentasyon** => Resmi boyama kitabı gibi bölgelere ayırma. Kutu çizmek yetmez, yolun tam ŞEKLİ lazım — çünkü İKA'nın rotasını o şeklin ortasından çıkarıyoruz.
- **Maske** => Modelin boyadığı alan. "Yol" boyası ve "moloz" boyası. Rota üretiminin hammaddesi.
- **Sınıf** => Modelin öğrendiği kategoriler. Bizde sadece 2 tane: `traversable` (geçilebilir) ve `blocked` (kapalı).
- **IoU** => İki boyamanın üst üste binme yüzdesi (kesişim ÷ birleşim). "Tahmin doğru sayılır mı?"nın cetveli. mAP hesabının içinde.
- **mAP50** => Modelin karne notu: IoU %50'yi geçen tahminler isabet sayılır, precision-recall eğrisinin altındaki alan alınır, sınıfların ortalaması çıkar. Bizde v1: 0,619 (yol 0,874 / moloz 0,363); v2 (sahadaki model): 0,595 — takım hedefi 0,60'ın hemen altında, v3 ile kapatılacak. Raporun "başarı oranları" tablosu.
- **mAP50-95** => Aynı karnenin zor versiyonu: örtüşme çıtası %50'den %95'e kadar tek tek kaldırılıp ortalanır. Bizde v1: 0,385 / v2: 0,344 — düşük görünmesi normal, herkes düşer.
- **Precision (kesinlik)** => "Yol dediklerinin kaçı gerçekten yoldu?" Yanlış alarm ölçüsü. Bizde v1: 0,674 / v2: 0,722.
- **Recall (yakalama)** => "Gerçek yolların kaçını bulabildin?" Kaçırma ölçüsü. Bizde v1: 0,604 / v2: 0,516.
- **Confidence (güven) eşiği** => Modelin "bundan eminim" barajı. Barajın altındaki tahminler çöpe. Bizde 0,15; hiçbir şey bulamazsa otomatik 0,05'e iner (hiç cevapsız kalmaktansa temkinli tahmin).
- **Epoch** => Ders kitabını (tüm veri setini) baştan sona 1 kez okumak. Bizde 100 epoch okundu.
- **Early stopping / patience** => Öğrenci 20 denemedir gelişmiyorsa dersi erken bitir. Bizde v1: patience=20, en iyi hâl 85. epoch'ta → `best.pt` oradan alındı; v2: patience=40.
- **Batch size** => Aynı anda masaya konan fotoğraf sayısı. Bizde 16. Büyük olursa hafıza yetmez, küçük olursa öğrenme sallanır.
- **Optimizer (AdamW)** => Öğretmenin öğretme yöntemi: her hatadan sonra modelin ayar düğmelerini hangi kurala göre çevireceği. AdamW = yaygın, dengeli bir yöntem.
- **Learning rate (lr0)** => Her düzeltmenin adım boyu. Çok büyük adım = hedefi ıskalar, çok küçük = yıl sürer. Bizde 0,001.
- **imgsz** => Modelin çalıştığı kare boyutu (piksel). Eğitimde 512, sahada/çıkarımda 1024.
- **Letterbox** => Resmi EZMEDEN kare yapma: sinema filmi televizyonda üstte-altta siyah bantla oynar ya, aynısı. Bu sayede kamera çözünürlüğü ne olursa olsun karar değişmiyor (614–3344 piksel testiyle kanıtlı).
- **Veri seti** => Ders kitabı: etiketli örnek fotoğraflar. Bizim kitap: RescueNet + FloodNet.
- **RescueNet** => Michael Kasırgası sonrası çekilmiş gerçek drone fotoğrafları + insan eliyle boyanmış cevap anahtarları. Ana ders kitabımız (2.964 görüntü).
- **FloodNet** => Sel sonrası drone veri seti. Moloz/kapalı örneği azdı diye v2 eğitimine takviye kitap olarak eklendi.
- **Train / val / test bölmesi** => Ders çalışma sayfaları / deneme sınavı / gerçek sınav. Model train'den öğrenir, val ile ayar seçilir, test'e hiç bakılmaz. Bizde 2.365 / 294 / 305.
- **Sınıf dengesizliği** => Kitapta bir konudan çok az örnek olması. Bizde moloz örneği yol örneğinin 3,5'te biri → moloz karnesi zayıf (0,363). Çözüm planı: FloodNet + dengeli fine-tune.
- **Augmentasyon** => Aynı fotoğrafı döndürüp, karartıp, kırparak bedava yeni örnekler türetme. Ezber yerine genelleme. Plan: v3'te perspektif (eğik açı) augmentasyonu — eğik bakışta çöküşü düzeltmek için.
- **Fine-tune** => Sıfırdan öğretmek yerine, zaten bilen modele kısa ek ders vermek. Moloz sınıfı için planlı.
- **Çıkarım (inference)** => Eğitim bitti, model artık sahada soru cevaplıyor. Dizüstünde ~540 ms/kare; RPi 5 ve Jetson hedefleri Bölüm 4'te.
- **NCNN** => Modeli Raspberry Pi gibi küçük bilgisayarda hızlı koşturan çevirici/motor. Bizim model NCNN'e çevrildi: 12,6 MB.
- **TensorRT** => Aynı işin NVIDIA (Jetson) versiyonu; GPU'da hızlandırır. İHA tarafının planı.
- **FPS** => Saniyede işlenen kare. Hedefler: RPi 5'te ≥10, Jetson'da ≥15.
- **Gamma düzeltme** => Parlaklık eğrisini bükerek karanlık fotoğrafı aydınlatma. Karanlık-normalizasyon adımında.
- **CLAHE** => Kontrastı bölge bölge açan akıllı filtre (tek düğmeyle her yeri patlatmaz). Gölge/loş ışık dayanıklılığı; `rpi_inference.py` içinde.
- **Morfoloji (açma/kapama)** => Boyadaki iğne deliği boşlukları doldurma, kıl payı çapakları silme. Maske temizliğinde.
- **En büyük bağlı bileşen** => Tek parça hâlindeki en büyük boya bölgesini tut, ufak kopuk lekeleri at. Gürültü lekesi yol kararını değiştiremesin diye.
- **Centroid** => Boyanın ağırlık merkezi (dengelendiği nokta). Koridorun üst bandındaki centroid sahanın hangi üçte-birindeyse karar odur: SOL / ORTA / SAĞ.
- **Distance transform** => Her yol pikselinin kenara uzaklığını ölçme. En uzak pikseller = yolun tam ortası → merkez hattı → waypoint'ler buradan örneklenir.
- **Waypoint** => Rotadaki uğrak noktası ("önce buraya, sonra şuraya"). İKA bunları sırayla gezer.

## HARİTALAMA / İHA ALGISI

- **Nadir kamera** => Tam dik aşağı bakan kamera (kuş gözü). Tarama uçuşunda 1 saniyede 1 kare çeker.
- **Poz (pose)** => Aracın o anki yeri + duruşu (x, y, z, yaw). Her kare, çekildiği ANDAKİ pozla eşlenir — bu eşleme 1 sn kayınca harita çorba olmuştu (v15 dersi), artık aynı olayda birlikte yazılıyor (`navitas_scan_cam` eklentisi).
- **Yaw** => Burnun pusulada hangi yöne döndüğü. Kareyi haritaya doğru açıyla oturtmak için şart.
- **HFOV** => Kameranın yatay görüş açısı (bizde 1,3 radyan). "30 m yükseklikten bir kare yerde kaç metre eder?" hesabının anahtarı (~45,6 m).
- **Ortomozaik** => Kareleri, Google Haritalar uydu görüntüsü gibi kuzeyi yukarı bakan TEK büyük resimde birleştirme. Model kararını tek kareye değil bu bütün haritaya bakarak verir.
- **MPP (metre/piksel)** => Haritada 1 pikselin gerçekte kaç metre olduğu (bizde ~0,055 m). Piksel koordinatını metreye çeviren çarpan.
- **Serpantin tarama** => Tarlayı biçer gibi S çizerek uçma (4 paralel hat). Alanın her karışı en az bir kez görülsün diye.
- **Referans noktası (ref_xy)** => İHA'nın "haritamın sıfır noktası burası" ilanı. İKA tüm rotayı bu noktaya göre oturtur. Artık haberleşme mesajının (OPEN_ROUTE) içinde alan olarak var.
- **Yerel koordinat** => Adres yerine "referanstan 3 sağ, 5 ileri" tarifi. Mutlak GPS hatası ikisini birden kaydırır ama BİRBİRLERİNE göre tarif bozulmaz — bu yüzden rotayı yerel gönderiyoruz.
- **Sağlamlık süzgeci** => Rotadaki saçma noktaları eleyen kontrol: saha dışı, başlangıcın gerisi, akışa ters. 3'ten az nokta kalırsa rota HİÇ gönderilmez — İKA'yı yanlış yönlendirmektense sustur.

## HABERLEŞME

- **UDP** => Posta kutusuna zarf atmak: hızlı, ama "ulaştı mı?" garantisi yok. Garanti işini üstte biz çözüyoruz (ACK). Geliştirme/simülasyon taşıyıcımız.
- **Seri (serial) hat** => Tek telden byte'ların sıra sıra akması. Telsiz modülle konuşma biçimi.
- **SiK telsiz** => Uçuş dünyasının yaygın telsiz modülü; "şeffaf seri köprü" — bir uçtan yazdığın diğer uçtan çıkar. Testlerde de sahada da 433 MHz (takım kararı 12.07.2026; raporlar 433'e güncellendi).
- **433 MHz** => Kullandığımız radyo frekans bandı. Şartname bant belirtmez; 433 MHz hem BTK kısa mesafe düzenlemesine uygun hem satın alınan SiK modüllerin bandı.
- **JSON** => Verinin insan da okuyabildiği yazımı: `{"road":2,"conf":0.91}`. Mesajlarımızın dili — hakem ekranda çıplak gözle doğrulayabilir.
- **Newline çerçeveleme** => Her mesaj = tek satır. Satır bozuk geldiyse sadece o satır çöpe gider, akış devam eder. Telsiz parazitine dayanıklılık.
- **seq (sıra numarası)** => Her mesaja artan numara. Alıcı "5'ten sonra 7 geldi, 6 kayıp" veya "5 iki kez geldi, birini at" diyebilir.
- **ACK** => "Aldım" makbuzu. İKA ve YKS, açık yol mesajını alınca İHA'ya makbuz döner.
- **Tekrar gönderim** => Makbuz gelmediyse mesajı tekrar at (8 deneme, 0,25 sn arayla). ÖDR'de beyan ettiğimiz >%95 aktarım doğruluğu hedefi böyle tutturulur.
- **HEARTBEAT** => "Yaşıyorum" sinyali, kalp atışı gibi düzenli atılır. Atışlar kesilirse karşı taraf bağlantının koptuğunu anlar.
- **Timeout (zaman aşımı)** => "Bu kadar bekledim, yeter" süresi. İKA'da 3 sn hiç mesaj gelmezse bağlantı KAYIP sayılır.
- **Failsafe (arıza emniyeti)** => Bir şey ters gidince aracın kendini güvene alması. Bizde: bağlantı koparsa İKA DURUR, rota hafızada tutulur, bağlantı dönünce kaldığı waypoint'ten devam (test_comms ile birim testli).
- **MAVLink** => Otopilotların standart konuşma dili. Uçuş telemetrisi (konum/tutum/batarya) bu dilde; görev verimiz ise ayrı JSON kanalında — iki akış birbirini boğmasın diye.
- **Telemetri** => Aracın anlık durum raporu (neredeyim, hızım ne, pilim ne). YKS ekranına akar.
- **YKS** => Yer Kontrol İstasyonu: yerdeki bilgisayar/ekran. Hakem, açık yol verisinin geldiğini burada canlı görür.

## ARAÇ ÜSTÜ / SİSTEM

- **Raspberry Pi 5** => İKA'nın beyni: avuç içi bilgisayar. Kamera yayını + model çıkarımı gerçek donanımda test edildi (kablo çekme testinde kendini toparladı).
- **Jetson Orin NX** => İHA'nın beyni: GPU'lu (grafik işlemcili) küçük bilgisayar; model burada çok daha hızlı koşar. Henüz elimizde test edilmedi — Bölüm 4 gelecek testlerde.
- **systemd servisi** => Bilgisayar açılınca programı kendiliğinden başlatan, çökerse ayağa kaldıran bekçi. RPi'deki kamera yayını böyle çalışıyor.
- **Watchdog** => "Hâlâ çalışıyor musun?" diye düzenli dürten zamanlayıcı; cevap gelmezse yeniden başlat/durdur. Hem serviste hem İKA "ilerleme yok" tespitinde fikir olarak kullanılıyor.
- **GNSS** => GPS ve kardeşlerinin (GLONASS, Galileo...) ortak adı: uydudan konum.
- **IMU** => İvme + dönüş sensörü; aracın iç kulağı. "Sarsıldım mı, döndüm mü?"
- **Enkoder** => Tekerin kaç tur döndüğünü sayan sayaç. "Şu kadar tur = şu kadar metre."
- **Sensör füzyonu** => GNSS + IMU + enkoderi harmanlayıp tek sağlam konum tahmini çıkarmak: üç şaşı tanık, bir sağlam ifade. İKA'nın rota oturtması için PLAN (kodu FDR'ye kadar yazılacak).
- **A\*** ("A-yıldız") => Labirentte en kısa yolu bulan klasik arama algoritması. İKA engelle karşılaşınca yerel yeniden planlama için PLAN (kodu henüz yok).
- **Diferansiyel sürüş** => Tank gibi dönmek: sağ teker hızlı + sol yavaş = sola dönüş. Direksiyon yok. İKA'nın sürüş biçimi.

## SİMÜLASYON

- **Gazebo** => Fizik kurallı sanal dünya: yerçekimi, çarpışma, kamera hepsi sahte ama kurallı. Görev provalarımızın sahnesi (Classic 11 sürümü).
- **Podman / konteyner** => Programı tüm kurulumuyla taşınabilir bir kutuya koyma. "Bende çalışıyordu" derdi biter — Gazebo her makinede aynı kutuda koşar.
- **Plugin (eklenti)** => Gazebo'ya taktığımız kendi C++ parçalarımız. `navitas_anim` = İKA'nın rota sürüşü; `navitas_scan_cam` = kare + pozu AYNI ANDA kaydeden kamera (v15'teki 1 sn kayma hatasının kökten çözümü).
- **SITL** => "Software In The Loop": gerçek donanım yokken yazılımı simülasyonla test etme yaklaşımı. Bölüm 4'te test metodolojimizin adı.
- **Dürüst zincir** => Testte cevabı sisteme sızdırmamak: saha gizli kurulur, algı yalnız İHA'nın kendi kamerasından, İKA yalnız modelin rotasını sürer. Model yanılırsa görev simülasyonda da BAŞARISIZ — testin gerçek riski ölçmesi böyle garanti edilir.
- **Headless** => Ekransız/görüntüsüz çalıştırma. Fizik testlerini hızlıca, video kaydı olmadan koşmak için.

## RAPOR / GEREKSİNİM YÖNETİMİ

- **Gereksinim (REQ / ister)** => Yarışmanın "sisteminiz ŞUNU yapmak zorunda" cümleleri. Şartnamede her biri numaralıdır (REQ-19 = İKA tam otonom olacak gibi). Numara, herkesin aynı cümleden bahsettiğini garanti eden adres etiketidir — "otonomi maddesi" dersen karışır, "REQ-19" dersen karışmaz.
- **Gereksinim izlenebilirliği** => Her REQ'in "bunu nerede karşıladık, nasıl kanıtladık?" sorusuna dosya üzerinde takip edilebilir cevap vermesi. DDR Bölüm 5'in tek konusu bu: hakem tabloya bakıp herhangi bir gereksinimin kanıtına ulaşabilmeli.
- **İzlenebilirlik matrisi** => O tablo işte: satır = gereksinim, sütunlar = REQ no / doğrulama yöntemi / durum / kanıt. "Matris" lafı korkutmasın, Excel tablosundan farkı yok.
- **MoC (Means of Compliance)** => "Uyum kanıtlama yöntemi": her gereksinimi HANGİ yöntemle kanıtlayacağını baştan ilan etme metodolojisi. Havacılık sertifikasyonundan gelir; şablon bunu ZORUNLU kılıyor. 4 standart yöntemi var (aşağıda).
- **Analiz / Test / Muayene / Demonstrasyon** => MoC'un 4 kanıt yöntemi. Analiz = hesapla göster (batarya ömrü hesabı). Test = ölç, sayı üret (mAP ölçümü, menzil testi). Muayene = gözle/dokümanla kontrol et (kilit kodda var mı?). Demonstrasyon = canlı çalıştırıp göster (uçtan uca görev koşusu). Her MoC satırında en az biri seçilir.
- **Karşılandı / Sürüyor / Planlandı** => MoC durum sütununun 3 hâli: kanıt tamam / kanıt kısmen var, doğrulama devam ediyor / test henüz yapılmadı, programda. Şablon bu dağılımın pasta grafiğini ister (Şekil 7).
- **Checkpoint (.pt) içi metrikler** => Eğitim, model dosyasının (best.pt) İÇİNE o anki doğrulama sonuçlarını gömer. v2'nin gerçek mAP değerlerini (0,595) buradan çıkardık — Colab kapansa bile kanıt modelin içinde taşınır. Doğrulamak için: `torch.load(...)['train_metrics']`.
