# 05 — Kamera 90° dönük montaj: yazılıma etkisi ve çözüm (KOD DEĞİŞMEDEN)

Kullanıcı notu (19 Eyl): kamera montaja ancak 90° sağa çevrilince sığdı. Kullanıcı kararı: **kod değiştirilmeyecek**, yalnız inceleme yapılacak.
Bu belge incelemenin sonucudur. Kodda hiçbir şey değiştirilmedi.

## Yazılım görüntüyü nasıl okuyor

- Üretimdeki şerit kararı **yalnız görüntü çerçevesinde** verilir.
  `codes/karar_sozlesmesi.py` şu varsayımı açıkça yazar: *"İHA alan MERKEZİNDE bekler ve görüntünün yukarısı Başlangıç → Hedef'tir. Poz, hdg, enlem/boylam GEREKMEZ."*
- Rota görüntüde **aşağıdan yukarıya** aranır. Şeritler görüntünün x ekseninde soldan sağa **1 / 2 / 3** diye numaralanır.
- Üretim karar yolunda aracın yönü (heading) **kullanılmaz**. Heading + montaj açısı kullanan `kbh_donustur` yalnız tezgâh içindir ve üretime bağlı değildir.
- Görüntü **aynalanmaz**. Eski kodda `cv2.flip` vardı ve 1 ile 3 numaralı şeritleri takas ediyordu; kaldırıldı (D-349).
  Nöbetçi test `tests/test_t201_kamera_yonu.py`. Yanlış şerit seçmek şartnamede 0 puan demektir.
- `rota_ekseni_derece` diye döndürülmüş rota ekseni desteği kodda var, ama üretim bu değeri `None` geçiriyor. Kullanmak kod değişikliği ister.
- Ölçek irtifadan ve yatay görüş açısından gelir (`--fov 54`; Halil ölçtü: 53–54°). **Kamerayı döndürmek ölçeği değiştirmez.**

## 90° montajın sonucu

Kamera araca göre 90° dönük. Araç burnu hedefe bakarak beklerse rota görüntüde **yatay** görünür.
Şerit arama aşağıdan yukarıya yapıldığı için karar anlamsızlaşır: ya rota bulunmaz ya yanlış şerit çıkar.
Açının işareti ters alınırsa (+90 yerine −90) görüntü 180° ters olur. O zaman **sol ile sağ yer değiştirir: yanlış şerit, 0 puan.**

**Çözüm (kod değişmez): aracı döndür, kamerayı değil.** Görüntünün üstü Başlangıç'tan Hedef'e baksın.

- Bekleme sırasında gereken burun yönü: **hdg = β − montaj_yaw**.
  - β = Başlangıç'tan Hedef'e kerteriz.
  - montaj_yaw = kameranın "görüntü üstü" yönünün burna göre saat yönünde açısı.
- montaj_yaw **+90** ise burun rotanın 90° **soluna** bakar; aracın **sağ yanı** hedefe döner.
- montaj_yaw **−90** ise burun rotanın 90° **sağına** bakar; aracın **sol yanı** hedefe döner.
- Görev dosyası üreticisi bunu zaten yapıyor: `scripts/fda_gorev_uret.py --montaj-yaw <derece>`.
  Bu dosya origin/master'da (Halil'in çizgisi), bu dalda yok.
  `CONDITION_YAW` komutunu `LOITER_TIME`'dan önce "β − montaj_yaw" olarak yazar. Bu sıra SITL'de 500/500 tuttu (D-457).
  Montaj açısı daha önce hiç ölçülmedi (A9 yapılmadı), varsayılan 0'dır. **Artık ±90 verilmeli.**
- Pilot elle konumlandırıyorsa (Loiter) burnu aynı kurala göre çevirir.
  Onaydan önce YKİ haritasında rota aşağıdan yukarı akmalı.

## Ok testi — montaj açısının işaretini belirler (2 dk, Jetson açık)

1. Kağıda kalın bir ok çiz, yanına büyük harflerle **ÖN** yaz. Oku aracın **burnuna** doğru çevirip kameranın 0,5–1 m altına koy.
2. Ham kareyi al:
   - Yolu 1: YKİ kamera görünümü (`--kamera-url`, yalnız ethernet varken).
   - Yolu 2: SSH yönlendirme `results/telsiz_20260919/betikler/ssh_yonlendir.py 10.21.8.7 18080 8080` açılır. Sonra tarayıcıda `http://127.0.0.1:18080/kare.jpg` açılır.
3. Görüntüde okun yönünü oku:

| Görüntüde ok | Anlamı | montaj_yaw |
|---|---|---|
| **yukarı** | görüntü üstü = burun (normal montaj) | 0 |
| **sola** | görüntü üstü = aracın SAĞI | **+90** |
| **sağa** | görüntü üstü = aracın SOLU | **−90** (= 270) |
| aşağı | görüntü üstü = kuyruk | 180 |

4. **"ÖN" yazısı düz okunmalı.** Ayna gibi ters okunuyorsa görüntü aynalanıyor demektir. Bu olmamalı; olursa uçulmaz, önce incelenir.
5. Sonucu hem görev üreticisine (`--montaj-yaw`) hem pilot kartına yazın.

Hatırlatma: kamera aşağı bakınca görüntü, yukarıdan bakılan bir harita gibidir. "Görüntü üstü aracın sağı" ise
aracın burnu görüntüde **solda** görünür. Tablo buna göre kuruldu (`kbh_donustur`: görüntü üstü kerterizi = hdg + montaj_yaw).

## Neden yazılımda döndürmedik

Tek satırlık bir `cv2.rotate` ile görüntü "düz" gösterilebilirdi. Ama bu saha kamera yolunda bir değişiklik olurdu,
yarışmadan bir gün önce yapılmış olurdu ve yönün işareti yine ölçülmek zorunda kalırdı.
Aynı yoldaki eski `cv2.flip` hatası 16 karenin 15'inde şeritleri takas ediyordu (D-349).
Kullanıcı kararı: kod değişmeyecek. Aracı döndürmek aynı sonucu kodsuz verir.
Uçuş sonrası kalıcı çözüm olarak `rota_ekseni_derece` ya da montaj açısı parametresi değerlendirilebilir.
