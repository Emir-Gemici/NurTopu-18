# 05 · SÖZLEŞMELER VE KAPILAR — projeyi ayakta tutan yordamlar

> Kaynaklar: `CONTRACTS.md` (başlık ve §11–§12) · `CLAUDE.md` madde 13–18 · `TEST_SPECS.md` · `results/fdr/GORUNTU_ISLEME_KANIT.md` §5
> · `scripts/olcum/65_kabul_denetcisi.py` · `codes/test_rota_sentetik.py` · `results/saha_kuru_kosu_*/ozet.json`.
> Jüri "kalite güvenceniz ne, sayılarınıza neden güvenelim?" derse cevap bu dosyadadır.

---

## Seviye 1 — Bir cümle ve büyük resim

Bu projede ölçülen kusurların çoğu algoritma hatası değil, **iki modülün aynı sayıya farklı anlam vermesiydi** (sınıf 2 bir
dosyada hedef, diğerinde araç; şerit sınırları bir yerde tuvale, diğerinde içeriğe göre). Bu hatalar teste yakalanmaz çünkü
her modül kendi içinde tutarlıdır. Çözüm: **`CONTRACTS.md` tek doğruluk kaynağı** ve **hiçbir sabit koda çıplak yazılmaz**
(anayasa madde 16). Etrafına beş yordam örüldü:

| yordam | tek cümle |
|---|---|
| **Genel kapı** (madde 14) | her görevden sonra `codes/test_rota_sentetik.py` → 15/15; düşerse görev geri alınır |
| **Ön kayıt** | eşik, sonuç görülmeden yazılır ve sonradan gevşetilmez |
| **ÖLÇÜLEMEDİ ≠ GEÇTİ** | koşulmayan kapı "sorun çıkmadı" diye yazılmaz; paydası olmayan oran rapora girmez |
| **Mutasyon kontrolü** | kod bilerek bozulur, testin **düştüğü** gösterilir; düşmeyen test vakumdur |
| **Kanıt defteri** (`REVIEW_LOG.md`) | her kusur/karar D-numarasıyla, kanıtlı; yalnız eklenir, çürüyen iddia silinmez üstü çizilir |

## Seviye 2 — Sözleşmelerin haritası (`CONTRACTS.md` bölümleri)

| § | konu | en kritik cümle |
|---|---|---|
| 1 | Sınıf id | eğitim `ZEMIN=0 ENGEL=1 HEDEF=2`; costmap `KATMAN_ARAC=10`; tek otorite `sinif_semasi.py` |
| 2 | Katman monotonluğu | `serbest(K1∧¬K2) ⊆ serbest(K1)`; çıkarma en son; ince bariyer dedektörü yalnız ekler engele |
| 3 | Koordinat çerçevesi | kaynak / tuval / içerik; her oran içeriğe göre; waypoint'ler `ref_xy`'ye göreli metre, İKA saf öteleme |
| 4 | Geometri sabitleri | `R_GEREKLI_M = 1,10`; medial-axis yerine açıklık ağırlıklı A* |
| 5 | Ölçek `mpp` | canlı irtifa, 0,5 s tazelik; HB ikincil; çelişkide ortalama yok; mpp yoksa rota yok |
| 6 | Mesaj protokolü | `OPEN_ROUTE / NO_ROUTE / HEARTBEAT(karar_yas) / ACK(ref, ref_tip) / CMD`; bilinmeyen tip yok sayılır; NO_ROUTE son rotayı ezmez |
| 6.2–6.4 | road, karar geçerliliği, ret sebepleri | (bkz. 04) |
| 6.5 | Üretim algı yolu yayın (K1) | her karede tam mesaj; hedef yoksa gönderici yüklenmez; latest-wins tek yuva; heartbeat 1 Hz |
| 6.6 | ACK bağlama, `IKA_GO` tekrar | `ref_tip` ile eşleme; IKA_GO ACK gelene dek tekrar, üst sınırda kırmızı; 2. onay İKA ACK'siz açılmaz |
| 6.7 | FDA görev kipi `--fda` | süre 600 s; İKA kanıtı aranmaz; paraşüt/İKA düğmeleri fiilen kapalı; iniş kanıtı zorunlu |
| 6.8 | Hakem kanıt kaydı | JSONL, satır başına fsync; 17 olay tipi; yazma hatası uçuş düğmelerini kilitler, ARM/RTL/LAND açık kalır |
| 7 | Görev kapısı | `sür ⟺ OPEN_ROUTE ∧ İHA indi ∧ IKA_GO` |
| 7.1 | Süre limitleri | 900 / 600 / 900 s; İKA'da iki ayrı deadline |
| 7.2 | İKA sürücü arayüzü | `hiz_ver/konum_al/durdur/saglikli`; ardışık hata tavanı 3; `GercekSurucu` arka uçsuz kurulamaz |
| 7.3 | Varış = brandaya temas | son waypoint pedin kutusunda; `FINAL_WP_RADIUS 0,3 < 1,0` |
| 7.4 | MAVLink çoğullayıcı | Jetson'da seri portu yalnız çoğullayıcı açar; tüketiciler UDP 14550/14551/14552 |
| 7.5 | SiK hub | `/dev/ttyUSB0`'ı yalnız hub açar; tüketiciler UDP 5100/5007; datagram = çerçeve |
| 8 | Çözünürlük | `imgsz` registry'den (512); çıplak yazılmaz |
| 10 | Ölçüt hiyerarşisi | 1 karar doğruluğu · 2 moloza basma · mAP reddedildi · 0,04 altı gürültü |
| 11 | Saha zinciri | 10 halka, her halkanın **sahibi** dosya:satır; `simulation/` sahip olamaz; sahipsiz halka boş bırakılamaz |
| 12 | DOĞRULAMA kümesi + K7 | 0038 DJI kareleri eğitime girmez; K7 yayınlanan şerit ≥ %95 (84/85) |

### 2.1 Genel kapı — tam olarak ne ölçer
`codes/test_rota_sentetik.py`: `simulation/scripts/arena.py → sahne_uret` ile **15 belirlenimci arena sahnesi** (kusursuz maske,
yer gerçeği = üretecin açık bıraktığı güzergâh). **İki kol:**
- KOL 1 (tanısal): `costmap_path_finder.rota_bul` → **15/15 tam puan** şart.
- KOL 2 (üretim): `rpi_inference.analyze_path` → (a) rota üretiliyor (ret yok, ≥ 2 waypoint) **ve** (b) yayınlanan `road` yer
  gerçeğiyle uyuşuyor — her ikisi ≥ **14/15** (`URETIM_KAPI_ESIGI`, ÖN KAYIT §18-B). Mutasyon: yayın hattı `darbogaz_serit`'e
  çevrilince KOL 2 6/15'e düşer, KOL 1 yeşil kalır — T155'in deliği artık kapıda.
Çıkış kodu `kapi_karari()` ile iki kola bağlı. Ölçülen taban 15/15 · 15/15 (PC 7 Eyl, Jetson 9 Eyl).

### 2.2 Kabul kapıları K0–K8 (sentetik arena T66, n=260; `65_kabul_denetcisi.py`)
| kapı | ne ölçer | eşik | v36 (26 Ağu / 1 Eyl üretim kipi) |
|---|---|---|---|
| K0 | körlük yok (boş maske üretmiyor) | figür > 0, boş maske yok | GEÇTİ (raw boş 0/67, cp boş 0/393) |
| K1 | rota üretilen kare | ≥ 230 | 255/260 · 256/260 |
| K2 | rotanın molozdan geçmesi | ≤ 15 | 5,88 · 6/256 |
| K3 | ağır moloz teması | ≤ 3 | 0,39 · 0/256 |
| K4 | arena dışına taşma | ≤ 5 | 1,57 · 2/256 |
| K5 / K5A | bariyer kesişimi (yatay / açılı küme) | = 0 | 0 · 0 px |
| K6 | yanlış güzergâh | ≤ 5 | 2,75 · 2/256 |
| K7 | yayınlanan şerit doğruluğu (dondurulmuş 88 kare) | ≥ %95 ve rota üretilen ≥ 80/88 | **84/85 = %98,8** · 85/88 |
| K8 | (üretim kipi kapısı) | — | 10/10 GEÇTİ |

⚠ Registry'nin kendi cümlesi: *"ARENA ÖLÇÜMLERİNİN TAMAMI SENTETİKTİR; gerçek arena karesi YOKTUR — K0..K6 SAHA BAŞARIMI İDDİA
ETMEZ."* Jüriye böyle söylenir.

### 2.3 Gerçek kare kapısı (`CONTRACTS.md` §12) — geçilmeyen eşik nasıl yazıldı
Doğrulama kümesi `dji/DOGRULAMA/` = DJI 0038 (test 29 + val 82 kare, iki bağımsız **kör** etiketin uzlaşısı). Terfi ölçütleri:
ROTA ≥ 10/29, MASKE_YOK ≤ 10/29, FP ≤ 1, **YANLIŞ GÜZERGÂH = 0**. v36: ROTA **8** (eşik 10), MASKE_YOK **16** (eşik 10), FP 1 ✔,
yanlış 0 ✔. Terfi **kullanıcı kararıyla** yapıldı (D-293, ON_KAYIT §15 "izin veriyorum kurala rağmen"), gerekçe: gerçek karede
yanlış güzergâh 15/21 → 7/38, engel üstü waypoint 79 → 3; bedel sentetik K3 0→1, K4 1→4, K6 5→7. **Eşikler değiştirilmedi**,
sonraki terfileri bağlar; v35 silinmedi, yedek. FDR bunu "geçmeyen kapı geçmedi diye yazılır" kuralının örneği olarak sunar.

### 2.4 Saha zinciri: 10 halka (`CONTRACTS.md` §11; `scripts/saha_kuru_kosu.py`)
`kamera · model_yukleme · cikarim · maske · olcek · hedef_konumu · rota · aktarim · surus_izni · motor`. Her halkanın sahibi
sahada gerçekten koşan dosya; `simulation/` sahip olamaz. Son kuru koşu (2–3 Eyl): **GEÇTİ 9 · DÜŞTÜ 0 · SAHİPSİZ 1 (motor)**,
çıkış kodu 1 (zincir kendini "hazır" ilan etmez). Ölçek halkası sahte MAVLink yayınıyla geçti; gerçek Pixhawk ÖLÇÜLMEDİ.

## Seviye 3 — Yordamların işlediğinin kanıtı

- **Ön kayıt işe yaradı (D-377):** çözünürlük artırma denemesinde umut verici bir ara sayı (%21,6) vardı; ön kayıt "I2 düşerse RED,
  I1 ne olursa olsun" demişti; sentetik 0,9846 → 0,7808 düştü → RED. Sonuç görüldükten sonra eşik oynatılmadı.
- **Ham çıktının depoda durması bir yanlış hükmü engelledi (D-209 §4)**; ön kayıt bir eşik gevşetmesini engelledi (D-225 §3);
  5 maddelik itiraz kalıbı bir GPU gecesi kurtardı (D-200). `CLAUDE.md` madde 19 bunları "denetimi işleten şey model farkı değil
  YORDAM" diye kaydeder.
- **Çürütücü turu (red team):** bağımsız ajanlar iddiaları çürütmeye çalışır. Örnek: uçtan uca gecikme p95 0,458 s ölçülmüştü,
  "telsiz + ACK ≈ 308 ms" görünüyordu; çürütücü bunun bir **soket zaman aşımı sabiti** olduğunu buldu (D-383); düzeltme sonrası
  p95 **0,113 s**, telsiz payı ~2 ms. Yanlış sayı silinmedi, üstü çizildi.
- **Doğrulayıcı yalan söyledi (D-… 24 Ağu):** başarısız ölçümü 0 sayıp "hiç yüklenmedi" diyen bir doğrulayıcı üçüncü kez aynı
  kusur sınıfını üretti → "ÖLÇÜLEMEDİ ≠ GEÇTİ" kuralı sertleşti.
- **Sızıntı yakalandı (D-376):** gerçek-kare havuzunun %62'si eğitim kümesindeydi; sızıntısız `p` 0,3457'ye indi (kirli okuma daha
  iyimserdi). Gereken FPS 0,579 buradan.
- **Vakum kapı yasağı (D-15 sınıfı):** ölçtüğü şey tanım gereği belirsiz olan kapı kurulmaz; K7 bu yüzden dondurulmuş 88 karede
  (kabul kümesinin %54'ü koridor sınırına denk geldiği için dışlandı).
- **Mutasyon uygulanmadıysa başarı sayılmaz (D-370).**
- **Push kapısı (D-430, 7 Eyl):** mimar süit kırmızıyken push etti; kural `scripts/push_kapisi.py` betiğine bağlandı (genel kapı +
  tam süit; kırmızıyken push yok). Sonra D-432: süitin kendisi yer tutucu IP'li süreç sızdırıyordu, kök neden orada.

### 3.1 Anayasanın değişmez teknik kuralları (`CLAUDE.md` §3)
13 yorumlayıcı PC'de `O:\navitas-local-train\venv\Scripts\python.exe` (`python` Windows Store saplaması, sessizce hiçbir şey yapmaz) ·
14 genel kapı 15/15 · 15 mimari değişmez (serbest alan otoritedir) · 16 sözleşmeler `CONTRACTS.md`'den, çıplak sabit yok ·
17 commit izinsiz atılmaz, yazar Emir-Gemici, **AI atfı yok** · 18 kullanıcının dosyaları silinmez.

### 3.2 Test süiti sayıları (bayatlamaya dikkat)
3 Eyl 1896 · 7 Eyl 2138 OK (PC, push kapısı) · 9 Eyl Jetson 2204 (32 ortam kırmızısı: `O:/` Windows yolları vb.). Test dosyası
190 (`tests/*.py`). Jüriye sayı verirken **tarihini** söyle.

---

## Jüriye 30 saniyede

> "Kalite güvencemiz dört yordam: eşikleri sonuç görülmeden yazarız ve gevşetmeyiz; ölçemediğimizi geçti saymayız; her
> kapıyı kodu bilerek bozarak sınarız, düşmüyorsa kapı sayılmaz; ve her kusuru kanıtıyla 436 kayıtlık bir deftere yazar,
> silmeyiz. Bu yordamlar iş gördü: bir çözünürlük denemesini ön kayıt reddetti, bir gecikme sayısının aslında soket zaman
> aşımı olduğunu bağımsız çürütücü buldu, üretim modelinin geçmediği iki eşiği raporda açıkça yazdık."

## Kendini sına

1. `CONTRACTS.md` neden var? (Kusurların ortak yapısı ne?)
2. Genel kapı kaç sahne, kaç kol, eşikleri ne?
3. K5 ile K7 neyi ölçer? K7 neden 88 karede?
4. v36 hangi iki eşiği geçemedi, nasıl terfi etti, eşiklere ne oldu?
5. "Vakum kapı" nedir? Mutasyon kontrolü neyi kanıtlar?
6. D-383'te ne yanlıştı, nasıl bulundu, düzeltilince p95 kaç oldu?
7. Saha zincirinin kaç halkası var; hangisi sahipsiz; `simulation/` neden sahip olamaz?
8. Kabul kapıları saha başarımı iddia eder mi? Cümleyi kur.
9. Push kapısı kuralı nedir, hangi kayıtla betiğe bağlandı?
10. Anayasa madde 16 ne der; ihlal edilirse ne olur (bir örnek)?

<details><summary>Cevaplar</summary>

1. Kusurların çoğu iki modülün aynı sayıya farklı anlam vermesi; modüller kendi içinde tutarlı olduğundan test yakalamaz; tek doğruluk kaynağı ve çıplak sabit yasağı. 2. 15 sahne; iki kol: `rota_bul` 15/15 ve `analyze_path` (rota üretimi ≥14/15 ve yayınlanan road ≥14/15). 3. K5 bariyer kesişimi = 0; K7 yayınlanan şerit doğruluğu ≥ %95 (84/85); kabul kümesinin %54'ü şerit sınırına denk gelip tanım gereği belirsiz olduğu için dondurulmuş iyi-koşullu 88 karede. 4. ROTA ≥10 (8) ve MASKE_YOK ≤10 (16); kullanıcı kararıyla (D-293), gerçek karede yanlış güzergâh 15/21→7/38 gerekçesiyle; eşikler değişmedi, sonraki terfileri bağlar. 5. Tanım gereği belirsiz şeyi ölçüyormuş gibi yapan kapı; mutasyon, kapının ayırt edici olduğunu (bozulunca düştüğünü) kanıtlar. 6. 308 ms "telsiz+ACK" bir soket zaman aşımı sabitiydi; bağımsız çürütücü buldu; p95 0,458 → 0,113 s. 7. 10; motor (gerçek sürücü yok); `navitas_sim.py` gz/meta.txt/kendi IHA_LANDED'ını varsayar, sahada üçü de yok. 8. Hayır: "Arena ölçümlerinin tamamı sentetiktir (T66, n=260); gerçek arena karemiz yoktur; K0–K6 saha başarımı iddia etmez." 9. Genel kapı 15/15 ve tam süit yeşilken push; D-430 ile `scripts/push_kapisi.py`. 10. Sınıf id / mesaj tipi / koordinat çerçevesi kodda çıplak yazılmaz, sözleşmeden okunur; örnek: sınıf 2 çakışması H brandasını engel yapıp P_görev=0 yapacaktı (S2/D-35); `imgsz` sözleşmede 640 yazıp üretim 512 koşuyordu (D-308).
</details>

## Kaynaklar
`CONTRACTS.md` · `CLAUDE.md` · `TEST_SPECS.md` · `codes/test_rota_sentetik.py` · `tests/test_t156_genel_kapi_uretim_kolu.py` ·
`scripts/olcum/65_kabul_denetcisi.py` · `results/fdr/GORUNTU_ISLEME_KANIT.md` · `scripts/push_kapisi.py` · `REVIEW_LOG.md` D-107, D-293, D-370, D-376, D-377, D-383, D-430.
