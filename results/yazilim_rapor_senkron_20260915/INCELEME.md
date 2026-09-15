# Yazılım raporu ve senkronizasyon incelemesi — 15 Eylül 2026

> İkinci kontrol notu: [IKINCI_INCELEME.md](ikinci_kontrol/IKINCI_INCELEME.md). Özellikle 7/15 tarihsel sonucun 1024 piksel çıkarıma ait olduğu ve precision değerlerinin etiketli alanla sınırlı olduğu netleştirilmiştir. Önceki Word için bu ek düzeltme notları geçerlidir.

Birleşik rapor eski deneyleri içeriyor; fakat bunların yeni başarılı bir toplu testle geçersizleştiğine dair kanıt bulunmadı. Doğrulanan sorun, deney tarihçesi ile rapor/devir güncellemelerinin birlikte ilerlememesi. Yerel kod, GitHub kodu, yerel model ağırlıkları ve Word belgeleri ayrı sürüm durumlarında.

Kapsam: NAVITAS_FDR_BIRLESIK.docx yazılım/simülasyon anlatımı, ilgili yerel deney kayıtları, model kayıt defteri, Git geçmişi, yerel reflog ve canlı uzak master kimliği. Bu inceleme tüm üretim kodunun eksiksiz hata denetimi veya yeni model kabul deneyi değildir. Emir'in bilgisayarı ve Google Docs sürüm geçmişi incelenmedi; kişiye hata atfedilmedi.

## 1. Doğrulanmış bulgular ve uygulanan düzeltmeler

| No | Bulgu | Kanıt / sınır | Yapılan işlem |
|---|---|---|---|
| Y01 | Model v36 ile sahne v1/v2/v3 adları kolay karışıyor. | Birleşik §3.3.4; kaynak RAPOR_K3B.md modeli değiştirmeden sahneyi değiştiriyor. | Yeni kopyada model, sahne ve rv kayıt adları açıkça ayrıldı. |
| Y02 | 12/15 iki farklı bağlamda geçiyor; genel model başarısı değil. | Kabul eşiği; ayrıca kare tabanlı seride rota ACK sayısı 12/15, görev 0/15. | Eşik, alındı onayı, doğru etiket ve görev ayrı açıklandı. |
| Y03 | Eski sahne sonuçları var, sonraki yerleşim düzeltmesi yok. | v1_15harita_yerlesim_d441.json: tarih 10 Eylül 11:37, v36 SHA eş, 7/15 doğru. | Ayrı tarihsel deney olarak 7/15 eklendi. 3/15 silinmedi, 105 koşuma eklenmedi. |
| Y04 | Sonraki rv41 sonucu birleşik raporun tarihçesinde yok. | rv41/detections.json: kolay, 0 waypoint, MASKE_YOK. | 14 Eylül kaydı ve tek değerlendirilen sahnenin sonucu eklendi. |
| Y05 | D-486 başlığı ve sonraki yorumlar üç seviyeyi algı başarısızlığı gibi topluyor. | iha_haritala.log: orta ve zor 1800 s sonunda atlanmış. Model bu iki seviyeyi değerlendirmemiş. | Kolay: rota yok; orta/zor: değerlendirme tamamlanmadı ayrımı eklendi. Eski REVIEW_LOG satırları değiştirilmedi. |
| Y06 | Görev başarısızlığını yalnız segmentasyona yüklemek ölçümü aşar. | T235 analiz_c.md: kareye göre etiket, KB başlangıç kayması, KB/HB görünürlüğü ve 12 temaslı koşunun geometri incelemesi. | Çok aşamalı nedenler yazıldı; karşı-olgu hesapları yeni test diye sunulmadı. |
| Y07 | Tek başarılı CAD videosu ile toplu model başarısı ayrımı belirgin değil. | Birleşik K20: 42 nokta, 99,88 s, 0 temas; kendi kayıtlı girdisiyle ayrı koşu. | Ayrı satırda gösterildi; oranları değiştirmediği belirtildi. |
| Y08 | En yeni Gazebo demosu gerçek algı testi değil. | 15 Eylül ETIKET_OKU.md: ROUTE_XY ground truth, model burada çalışmadı. | Deney tarihçesine bilinen rota gösterimi olarak eklendi. |
| Y09 | Model hâlâ eksikmiş gibi okunan devir/üretim kaynağı var. | HANDOFF 14 Eylül gece ve /tmp/navitas_fdr_icerik_uret.py; daha sonra D-485 ve 397f46be ile kurtarma. Diskte v36 SHA kayıt defteriyle bu incelemede eşleşti. | Düzeltilmiş raporda geçerli durum yazıldı; eski kayıtların tarihsel olduğu belirtildi. |
| Y10 | Piksel oranlarının paydası ve eksik precision/recall sunumu. | Ham 29 kare matrisi. Gerçek engelde %75,87 engel, %0,65 zemin, %23,48 tahmin yok. | Precision/recall ve paydalar eklendi. Etiketli zemin tahminleri içindeki engel payı %6,18 olarak ayrıldı. |
| Y11 | Bazı kanıt yolları bu çalışma kopyasında çözülemiyor. | K20/K22/K27/K28/K31 içindeki cad_video_arena_rev1_v2, sunum_rev6/rev6_kunye.json, results/fdr_33_20260914 yolları bu kopyada bulunamadı. | Mevcut kanıt iddiaları tarihli kaynak beyanı olarak korundu; burada yeniden doğrulanmış gibi gösterilmedi. Eksik kaynaklar aşağıdaki teslim kaydında açık. |
| Y12 | Gerçek kayıt izleyicisinde 1800 s duvar-saati sınırı var. | simulation/scripts/iha_haritala.py watch(); orta/zor gerçek logları. | Belgeye kayıt/işleme kusuru olarak işlendi. Süreyi körlemesine artıran üretim kodu değişikliği yapılmadı. |
| Y13 | Yerel master uzak masterın 7 commit gerisinde. | Canlı ls-remote: 0a043107; yerel HEAD: ab906f3a. | Salt okunur fark listesi ve kaynak kimlikleri kanit.json'a kaydedildi. |
| Y14 | Yerelde commit edilmemiş üretim değişiklikleri var. | navitas_anim.cc +43/-1; world_generator.py +10/-3. D-488 hız/log değişiklikleriyle ilişkili. | Mevcut katkılar korundu; rapor değişiklikleri kodla karıştırılmadı. |
| Y15 | Word dosyaları ve yeni demo/varlıkların önemli kısmı Git dışında. | Birleşik ve REV2/3/4/6/7 dosyaları untracked; model .pt dosyaları ignored. | Dosya SHA, mtime ve tracked durumu kanit.json'a alındı; ortak teslimin yalnız commit SHA ile tanımlanamayacağı belirtildi. |

## 2. Yazım, commit ve push/erişim zaman çizelgesi

Saatler Türkiye saati (+03:00). “Commit” Git commit zamanıdır. “Push” yalnız yerel reflog açıkça `update by push` diyorsa yazılmıştır. `fetch` zamanı uzak commitin bu kopyada ilk gözlendiği zamandır, gerçek sunucu push zamanı değildir. Dosya mtime değeri son yerel yazma/kopyalama zamanıdır; belgeyi kimin yazdığını veya ilk üretim anını kanıtlamaz.

| Tarih/saat | Olay | Senkronizasyonla ilişkisi |
|---|---|---|
| 10 Eylül 11:37 | v1 yerleşim düzeltmesi ölçümü 7/15; JSON deney tarihi. | Eski 3/15'in ardından ayrı deney var; model yine v36. |
| 10 Eylül 17:22:53 | 28e935ef: MuJoCo video/rapor sonuçlarının commit'i. | 9/45, 0/15 ve tarihli testler rapor kaynaklarına bu dönemde girmiş. |
| 10 Eylül 18:17:32 | origin/master fetch gözlemi. | Sunucu push anı bu satırdan çıkmaz. |
| 12 Eylül 14:20:09 | Uzak geçmiş bu kopyaya fetch edilmiş. D-469 senkronizasyon/çatışma kaydı. | Daha önce yüzlerce commitlik ayrışma olduğu belgelenmiş. |
| 12 Eylül | D-473: yerel iha_haritala katkısının terk edilmiş araştırma mimarisinden geldiği kararı. | Eski kod dalının yeni çalışma ağacına sızması daha önce gerçekten yaşanmış; yeniden birleştirmek çözüm değil. |
| 14 Eylül 02:10:50 / 02:13:53 | 8bb7b45d commit / yerel reflogda push. | FDR yazılım belgesi, v36 dosyası kurtarılmadan önce hazırlanmış. |
| 14 Eylül 02:58:12 / 02:58:14 | db405856 commit / push: FDR_YZLM_003H. | Belge kimliği düzeltilmiş; bu içerik anında model dosyası hâlâ eksik sayılıyor. |
| 14 Eylül 09:53:56 / 09:54:00 | 397f46be commit / push: v36 kurtarma + unpause düzeltmesi. | Sonraki teknik durum, eski devir/üretim metninden ayrışıyor. .pt dosyaları Git'e girmiyor. |
| 14 Eylül 12:29:45 / 12:29:48 | ab906f3a commit / push: rv41 sonuç kaydı. | Yeni kayıt yayımlanmış; birleşik rapor bu tarihçeyi kapsamıyor. |
| 14 Eylül 13:02–13:16 | Uzakta 7 commit: no-op ve 18,65 m/s İHA hız kaynakları/başlatıcıları. | Yeni bir 12/15 model ölçümü yok; yerel HEAD bu commitleri içermiyor. |
| 14 Eylül 13:14:57 ve 13:22:11 | Uzak değişiklikler fetch edilmiş; origin/master 0a043107. | Fetch yapılmış fakat yerel master ilerletilmemiş. |
| 14 Eylül 13:18 / 14:17 / 14:59 / 16:34 | Yerel FINAL / REV2 / REV3 / REV4 mtime. | Dosyalar Git dışında. REV4 kontrol kaydı tablo metinlerinin korunduğunu söylüyor. |
| 14 Eylül 22:03 / 22:31 | Yerel REV6 / REV7 mtime. | Eski deney tablosu bu revizyonlarda da mevcut. |
| 15 Eylül 11:43 kayıt adı | Bilinen rota Gazebo demosu. | Model kabul deneyi değil; yeni video ≠ yeni model başarı ölçümü. |
| 15 Eylül 17:27:56 | Birleşik DOCX yerel mtime. | Güncel tarihli belge, 10 Eylül testleri + ayrı 14 Eylül video kaydını taşıyor. |
| Bu inceleme | Canlı uzak SHA = 0a0431078d18990b2c6839899aeff9ca1dc6c0f0. | Yerel origin/master güncel; çalışma dalı 7 commit geride. |

## 3. Eski dosya şüphesinin hükmü

**Kısmen doğrulandı:** eski ölçüm metinleri yeni DOCX revizyonlarında korunmuş. `results/fdr_rev4_20260914/content_verification.json`, `all_table_texts_preserved: true` ve `source_prose_preserved_except_revision_and_diagram_legend: true` diyor. Yerel DOCX'lerdeki ilgili pasajların dökümü `kanit.json` içindedir. Bu, metin sürekliliğini destekler; bütün birleştirme adımlarının kesin kaynak zinciri veya belirli bir kişinin kopyalama işlemi kanıtlanmış değildir.

**Doğrulanmadı:** “Eski başarısız model sonuçları yanlışlıkla yazılmış; yeni model 12/15 başarılı.” Üretim modeli hem eski deneylerde hem kayıt defterinde v36. Yeni toplu 12/15 model başarısı bulunmadı. Güncel rv41 orta/zor da bir model başarımı ölçümü değildir; işleme tamamlanmamıştır. Eski testleri silmek yerine model SHA'sı, deney tarihi, sahne/kayıt kimliği ve metrik ayrılmalıdır.

**Kök neden çıkarımı:** kaynak kodu, ağırlık dosyası, deney çıktısı ve Word belgesi için tek ortak teslim künyesi kullanılmadığından “güncel” sözcüğü farklı dosyalar için farklı anlama geliyor. Bu çıkarım yukarıdaki sürüm ayrışmasına dayanıyor; Emir'in ayrı çalışma kopyası görülmeden onun elindeki durum hakkında hüküm verilemez.

## 4. Uygulanan ve açık kalan işler

- Yeni DOCX kopyasında yazılım deney tarihçesi, v36/sahne/rv ayrımı, 7/15 ayrı kaydı, rv41 zaman aşımı ayrımı, bilinen rota demo etiketi, precision/recall ve metrik kapsamları işlendi. Tarihsel test sayıları değiştirilmedi.
- Önceden istenen donanım/elektrik düzeltmelerinde yalnız beyan/varsayım ayrımı yapıldı; yeni motor için itki/akım/uçuş süresi üretilmedi. Kart hedefi veya üretim konfigürasyonu teknik olarak onaylanmadı.
- Kaynak DOCX korundu; yeni çıktı ayrı ad taşıyor. Üretim kodu, git dalı, uzak geçmiş ve başka ajanın kilitleri değiştirilmedi. Commit/push yapılmadı.
- Genel kapı gerçekten çalıştırıldı: `/home/trs/projects/navitas-unified-20260822/.venv/bin/python codes/test_rota_sentetik.py`; çıkış 0, `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`. Bu kusursuz maskeli yazılım kapısıdır; görüntü işleme modelinin 15/15 saha/simülasyon başarısı değildir.
- Yeni GPU çıkarımı, yeni MuJoCo/Gazebo görevi, HIL veya saha testi çalıştırılmadı. Bu inceleme yeni performans sonucu üretmez.

## 5. Bir sonraki ortak teslim için sıra

1. Aynı kod tabanı üzerinde çalışılacak SHA seçilmeli; 7 uzak commit yerel hız/log değişiklikleriyle birlikte incelenmeli. Fetch yapılmış olması yerel kodun güncellendiği anlamına gelmez.
2. Ayrı dosya aktarımı gereken varlıklar (model, video, Word) için SHA ve paylaşılan konum birlikte kaydedilmeli. Modelin kayıtlı SHA'sı: `1d1caca6f6da19ea35e69186a048da960ca5188be6ee6d49d6106457cac46911`.
3. Her deneyde kod SHA + kirli çalışma ağacı durumu, model SHA, sahne parametreleri, komut, tarih, ham sonuç yolu ve başarı paydası aynı künyede tutulmalı.
4. Her Word revizyonu kullandığı deney künyelerini ve önceki belge SHA'sını listelemeli; yalnız dosya adına “FINAL” eklemek yeterli değil.
5. Eksik K20/K22/K27/K28/K31 kanıtları ortak konuma alınmalı. Videonun bulunması, onu üreten JSON/kodun da iki tarafta bulunduğu anlamına gelmez.
6. İzleyici zaman aşımı için ayrı kod düzeltmesi yapılırken yavaş ama ilerleyen tarama, hiç başlamayan tarama ve çöken üretici ayrı test edilmeli. T235 koordinat/görünürlük problemi mevcut mimari karar ve kilitlere uygun ayrı iş olarak ele alınmalı.

Makinece okunabilir kanıt: `kanit.json`. Düzenleme kaydı ve belge doğrulaması, aynı klasöre eklenen teslim künyesinde listelenir.
