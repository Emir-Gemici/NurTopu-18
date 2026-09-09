# 12 · KUSUR TARİHÇESİ VE DERSLER — 441 kayıtlık defterden dönüm noktaları

> Kaynak: `REVIEW_LOG.md` (30 393 satır; 441 `### D-` başlığı; D-01 → D-436; 3 Ağu–7 Eyl 2026) · `ozet/E_review_log_tarihce.md` (40 kaydın ayrıntısı).
> Jüri "en büyük hatanız neydi, nasıl yakaladınız?" derse burası. Defterin ruhu: **hiçbir kayıt silinmez; yanlış çıkan iddianın üstü çizilir, düzeltmesi eklenir.**
> Sayı: Ağustos ~379, Eylül ~62 kayıt; zirve 20 Ağustos (52 kayıt); 80 kayıtta "düzeltme/yanlış/çürüdü/kendi hatam" ibaresi.

---

## Seviye 1 — Bir cümle ve büyük resim

Defter 3 Ağustos'ta "çalıştığı sanılan ama hiç kanıtlanmamış" halkaların listesiyle açılır ve beş hafta boyunca aynı birkaç kusur sınıfının tekrarını,
her tekrardan çıkan bir kuralla kapatır. En pahalı kusur: **saha kamera yolu her kareyi aynalıyordu** (D-349) — açık yol 1↔3 takas, 0 puan riski, ilk
commit'ten beri oradaydı, hiçbir kapı `run_camera`'dan geçmediği için görülmedi. En öğretici süreç kusuru: **kutusu açılmamış donanım hakkında varsayım**,
dört kez (microSD, PX4, künye, Orin Nano). Projenin kuralları bu tekrarlardan doğdu: ölçüm yolu = üretim yolu, pozitif kontrol, ön kayıt, üç durumlu kapı,
"beyan ≠ ölçüm", tek doğruluk kaynağı, kural insana değil betiğe.

## Seviye 2 — Dönemler

### 2.1 Ağustos başı (3–10): "hiçbir şey ölçülmemiş"
D-02 IKA_GO tek paket, ACK'siz · D-03 iniş kilidini açan taraf **yok** (kilit eklerken açanı da kanıtla → TEST_SPECS 4.6) · D-12 v17 gerçek karede tamamen kör
(11/12 boş) · D-15 anayasa madde 4 kapısı hiç çalışmamış (`grep -E` içinde `\|`, hep 0 → "sahte geçiş"; **pozitif kontrol** kuralı) · D-18 sentetik eğitim
gerçek dokuyu unutturdu · D-22 13 ajanlı tarama: saha kod yolu **dört yerden kopuk**, 58 testin hiçbiri görmüyor · D-24 `MORPH_CLOSE` oyulmuş engeli geri
kapatıyor (madde 15 ihlali) · D-25 `rota_bul` letterbox dolgusunu bilmiyor · D-26 v21'in "gerçek kare kapısı" kendi eğitim verisinde, val %100 sızıntılı ·
D-28 kullanıcı sahada buldu: waypoint kenarı engelin üstünden · D-33 zaten commit edilmiş görev 6 saat baştan yapıldı ("otorite depodur, kuyruk değil") ·
D-36 ilk Jetson FPS (14) vekil kartta, kanıtsız.

### 2.2 Ağustos ortası-1 (11–16): ölçüm zemini krizi, T66, v27→v30
D-49→D-51→D-53 mimar iki kez yanıldı; **Codex-2 görevi zorlamayıp itiraz yazdı ve haklı çıktı**: ölçüm zemini HTAB değil **otopark** · D-56 kompozit zemin kararı;
"gerçek arena başarımı doğrulanamaz" açıkça yazıldı · D-61 kullanıcı "çatıyı yol sanıyor" dedi, doğrulandı (v21 "araç mı değil mi" ayırıcısı) · D-67 kök: 2 sınıflı
dönüşüm çatı/ağaç/suyu etiketsiz bırakıyor · D-84 "gerçek arena karesi bulundu" → **D-99 büyük düzeltme: figür yapay zekâ ürünü**, kullanıcı sordu, mimar altyazıyı
okumamıştı; beş kaydın alanı daraltıldı, silinmedi · D-104 düşen kapı yanlış modelle ölçülmüş "geçersiz kıyas" · **D-107 ilk ön kayıt** (K0–K5, "sabah tartışılmayacak") ·
D-113 `best.pt` epoch 43'te donmuş, `last.pt` %21 daha iyi · D-116 v27 üretim · D-119 ONNX kararı binde-4 gürültüye kararsız · D-131 v29 ×12 gerçek 64/67 ama K5
3 px → ön kayıt RED · D-134 mimar kendi "öneri v30" cümlesini tutarsız bulup geri aldı; sevk kararı insana (D-133) · D-136 v30 · D-140 seed etkisiz, v31 = v30 bit-bit.

### 2.3 Ağustos ortası-2 (17–22): kararsızlık, K5, çatı, v35
D-150 K5 sıkı kapıda iki model de düşüyor; v30'un 0/173'ü şanslı çekiliş (tek çekilişte sıfır sıfır değildir) · D-154 darlık `yol_duzelt` string-pulling'inden ·
D-180 kabul denetçisi `None`'ı "düştü" sayıyor → D-197 **üç durumlu kapı**: GEÇTİ/DÜŞTÜ/ÖLÇÜLEMEDİ, ÖLÇÜLEMEDİ terfiyi bloklar · D-182 v34; terfi yarım kalınca 8 test
düştü ("sistem tasarlandığı gibi çalıştı") · D-210 model çatıyı öğrenmiş ama gerçek karelerin **kendi etiketi** "zemin" diyor (448/448) · D-225 ön kayıt eşik
gevşetmesini engelledi · D-233 val %100 kirli (55/55) · D-238 kazananın dürüst bedeli: zemin kaybı %39,7 · D-243 K5'te **bariyer modelden gelmeyecek** · D-255
ilk kez tam zinciri geçen model; "kanıt kendi koşumum" · D-256 v35 · D-272 gece karesinde `YOL=2 · güven=1,000` yayınlandı — ön kayıttaki ağır hüküm ateşledi.

### 2.4 Ağustos sonu (25–31): gerçek veri, K6–K8, v36, saha yolu kusurları
D-279 etiketleme kapasitesi 5,1 kare/saat (19,9 değil) · D-284 10 kapatma adayının 8'i çürüdü ("yap satırı sınandı, asıl iddia sınanmadı") · D-289 hiçbir aday
"rota yol üstünde" kapısını geçmedi, v35 de · D-294 **v36 eşik geçmeden kullanıcı kararıyla** · D-296 yayınlanan şerit 9/15 yanlıştı (darboğaz pikseli) → tek tanım 15/15 ·
D-303 pt↔onnx 259/260 · D-313 K7 tam eşikte 84/88 ("marj sıfır, sınırda geçti") · D-319 asgari 30 m irtifa şartı hiç uygulanmıyordu ve rapor uygulandığını iddia ediyordu;
D-320 düzeltirken heartbeat susturma kusuru üretildi, süit kilitlenince yakalandı · D-332 v37 zinciri geçti, figürde çöktü → K8 · **D-349 kamera aynalama** ·
D-352–D-360 Jetson kurulum bloğu, `git add -A` 1589 dosya, yanlış e-posta, **kapı kırmızıyken push** · D-368 şartname kaynağından yeniden okundu · D-370 mutasyon
betiği CRLF'e takılıyordu (mutasyon uygulanmadan "ölçüldü") · D-371 FP16 kararı.

### 2.5 Eylül (1–7): gerçek bayt akışı, Faz B, saha
D-374 FPS sorusu kapandı; 51 s kör aralık · D-375 FP16 denkliği **vakumdu** (`half` yok sayıldı, 893/893 bit-eş → "farksızlık ≠ denklik") · D-376 R'nin %62'si eğitim
kümesi · D-377 640 RED · D-383 çürütücü: 308 ms soket sabiti · D-387/388 MAVLink ve SiK **ilk kez gerçek çerçeve/bayt** · D-403 paraşüt komutu alıcıya hiç ulaşmıyordu ·
D-405 mühür CRLF'ye bağlıydı (18/19 sahte ihlal) · D-410 21 Eylül uçuş günü değil · D-412 mimarın belge commit'i yarım işi süpürdü (YKS her kurulumda ölüyordu) ·
D-417 FDR yönergesi okundu: yanlış iskelet, isim yasağı · D-421 "cumartesiye hazır mıyız": 13 tıkayıcı, runbook bloğu ölü · D-422 saat kilidi kalıcı red ·
D-424 Pixhawk PX4 ile · D-425 4.7.1'de 9 parametre yok · D-426 künye üç yerde yanlış · D-427/430/432 süit üretim portlarına bind, kırmızıyken push, süreç sızıntısı ·
D-428 RC failsafe düştü, uçuş yok · D-429 üç devrilme · D-431 Orin Nano · D-433 RC6_OPTION · D-434 pilot temiz · D-435/436 motor künyesi.

## Seviye 3 — Tekrarlayan örüntüler → kurallar (jüriye "ne öğrendiniz" cevabı)

| örüntü | tekrarlar | doğan kural |
|---|---|---|
| **Ölçüm yolu ≠ üretim yolu** | D-22, D-51 (mimar yolu yeniden kurdu), D-58, D-165, **D-349** | kabul zinciri ve genel kapı `run_camera` çağrı sırasıyla koşar (T156, D-299); üretim yolu tek tanımlı |
| **Kapı/doğrulayıcı yalan söyledi** (sahte geçiş, vakum) | D-15, D-32, D-180, D-284, D-335, D-357, D-370, D-375, D-412, D-415, D-423 | pozitif kontrol; mutasyon kontrolü; "farksızlık ≠ denklik"; üç durumlu kapı; ÖLÇÜLEMEDİ ≠ GEÇTİ ≠ DÜŞTÜ |
| **Ölçüt sonuçtan sonra seçildi** | D-85/86, D-90, D-104 → D-107; D-157, D-163, D-345 (ön kaydın kendisi yanlış yazıldı) | ön kayıt: eşik, karar sırası, "hangi dal ateşlerse ne olur" koşumdan önce; ihlal istisna adıyla sözleşmeye (D-294) |
| **Ölçüm zemini/kaynağı yanlış** | D-53 (otopark), D-62, **D-99** (figür YZ), D-201, D-233, D-339–342, D-346, D-376, D-377 | eğitim/doğrulama ayrıklığı her ölçümde beyan; resmî belge kaynağından okunur (D-99, D-368, D-410, D-417); "bakir küme" tanımı yazılı (D-292) |
| **Kutusu açılmamış donanım varsayımı** | D-36, D-413, D-424, D-425, D-426, **D-431**, D-435, D-436 | "üzerinde ne var?" ön kayıtla; **beyan ≠ ölçüm**; kutu açılınca ilk komut künyeyi ölçer (`/proc/device-tree/model`, MP Messages); "ne göreceksin" yazılıp sayı istenir |
| **İki kopya, yalnız biri denetleniyor / ayna bayatlığı** | D-01, D-55, D-89, D-106/116, D-188, D-189–192, D-352, D-418, D-421 | ayna testle kilitlenir; KOPYALAR listesi; terfi = altı hizalama noktası tek commit; tek doğruluk kaynağı (madde 16) |
| **Fail-dangerous** | D-92 ("bizi koruyan bir kapı değil bir eksiklik"), D-146, D-272, D-320, D-349, D-422 (ters yön), D-428 | kilit eklerken açan taraf kanıtlanır (D-03); failsafe döngüsünde yayın zorunlu, bilgi ek (D-320); kör modelin düştüğü kapı (D-243) |
| **Süreç: kendi işini onaylama, kural insana** | D-33, D-255/257/269, D-360, D-430 | yazan denetleyemez; "aynı model uyuşması kanıt değil"; push kapısı betiğe (D-430) |

**Numara çakışmaları da kayıttır:** eşzamanlı ajanlar aynı numarayı aldı; D-39/40/41/61/62 ikişer kez, D-60b var, **D-416 yok**; benim 6 Eylül kaydım D-428 → D-431.
Kural: kendi kaydını taşı, başkasınınkine dokunma.

**Üretim modeli zinciri (defterden):** v4 (15 Tem) → v21 (D-20) → v24 (D-83) → v27 (D-116) → v30 (D-136) → v34 (D-182) → v35 (D-256) → v36 (D-294).
Reddedilenler: v25, v29, v32, v33, v8, v37 adayı, T199 adayı. Test süiti: 58 (D-22) → 962 (D-294) → 2121 (D-431).

### 3.1 En çok soru gelecek beş kayıt (ezberle)
1. **D-349 kamera aynalama.** `cv2.flip(frame, 1)` ilk commit'ten; 16 karenin 15'i sol-sağ takas; §2.1 → 0 puan. 53 ajanlı taramanın en üst bulgusu; ajana
   güvenilmedi, kabul kümesinde her kare özgün ve aynalı koşularak **ölçüldü**; satır kaldırıldı, asimetrik kare nöbetçisi, genel kapı üretim yolunu zorlar.
2. **D-99 figür yapay zekâ.** Tek "gerçek arena" sanılan görsel şartnamenin kendi altyazısıyla YZ ürünü; kullanıcı sordu; beş kaydın alanı daraltıldı, hiçbiri silinmedi.
3. **D-294 v36 kural dışı terfi.** Eşik geçilmedi, kullanıcı kararı, istisna sözleşmeye adıyla, eşik değişmedi, v35 yedek (06).
4. **D-375 vakum ölçüm.** 893/893 bit-eş çıkınca araçtan şüphelenildi: `half` yok sayılmış; kural "%100 eşlik önce aracı şüpheli kılar".
5. **D-431 Orin Nano.** Dördüncü tekrar; "beyan ≠ ölçüm" kuralı; kazanım: TensorRT/CUDA apt ile, engine derlendi; bedel: 246 MB tekerlek + belge geçersiz.

---

## Jüriye 30 saniyede

> "En büyük hatamız saha kamera yolunun her kareyi aynalamasıydı: açık yol sol-sağ yer değiştiriyordu, bu şartnamede sıfır puan. Kabul
> kapılarımız üretim döngüsünden geçmediği için aylarca görülmedi. Yakalayınca satırı kaldırmakla kalmadık, genel kapıyı üretim yolunu
> zorlar hâle getirdik. Bu defterde 436 kayıt var; seksenden fazlası kendi yanlışımızın düzeltmesi. Sentetik arena figürünün yapay zekâ ürünü
> olduğunu bile kayda geçirdik. Kuralımız: kayıt silinmez, üstü çizilir; her tekrar eden hata bir kural doğurur."

## Kendini sına

1. D-349'da kusur neydi, neden görülmedi, ne değişti?
2. D-99 nedir; hangi kayıtlar etkilendi, silindi mi?
3. "Kutusu açılmamış donanım" örüntüsünün dört tekrarı ve kuralı?
4. D-180 → D-197: hangi kusur, hangi kural?
5. Ön kayıt kuralı hangi üç hatadan doğdu (D-107)?
6. D-375'te "farksızlık ≠ denklik" ne anlatır?
7. Codex-2'nin itirazı (D-50/51/53) neyi buldu?
8. D-320: bir düzeltme nasıl yeni kusur üretti, nasıl yakalandı?
9. Numara çakışmaları neden var; D-416 neden yok?
10. Üretim modeli zincirini D-numaralarıyla say.

<details><summary>Cevaplar</summary>

1. `cv2.flip(frame,1)` her kareyi aynalıyordu (ilk commit'ten); kabul zinciri `analyze_path`'i doğrudan çağırıyor, `run_camera`'dan geçmiyordu; satır kaldırıldı, asimetrik kare nöbetçi testi, genel kapı üretim kolu. 2. Şartname Şekil 1 altyazısı "tamamen yapay zekâ ile oluşturulmuştur"; D-84/87/88/92/95 geçerlilik alanı daraltıldı, silinmedi. 3. microSD (D-413), PX4 (D-424), künye (D-426), Orin Nano (D-431) [+ motor D-435]; beyan ≠ ölçüm, ilk komut künyeyi ölçer. 4. Kabul denetçisi `None`'ı "düştü" sayıp her modeli reddediyordu → üç durumlu kapı, ÖLÇÜLEMEDİ terfiyi bloklar. 5. D-85 eşiği alt kümenin azamisine oturtmak, D-90 tanıma bağlı %92,7, D-104 yanlış modelle kapı. 6. İki kolun %100 aynı çıkması ölçümün çalıştığını değil aracın bozuk olabileceğini gösterir; `half` uygulanmamıştı. 7. Kusurlu yol `iha_perceive` değil `rota_bul`; ölçüm zemini otopark, arena değil; mimar üç noktada yanlıştı. 8. Asgari irtifa düzeltmesi heartbeat'i susturdu (aynı try içinde); süit 20 dk kilitlenince yakalandı; kural: failsafe döngüsünde yayın zorunlu, bilgi ek. 9. Eşzamanlı ajanlar aynı numarayı aldı; kural "kendi kaydını taşı"; D-416 atlanmış. 10. v21 D-20 → v24 D-83 → v27 D-116 → v30 D-136 → v34 D-182 → v35 D-256 → v36 D-294.
</details>

## Kaynaklar
`REVIEW_LOG.md` (başlıklar: `grep -n "^### D-" REVIEW_LOG.md`) · `ozet/E_review_log_tarihce.md` · `CLAUDE.md` madde 19 · `TEST_SPECS.md` §4.
