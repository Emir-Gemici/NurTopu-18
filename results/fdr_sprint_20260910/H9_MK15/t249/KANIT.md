# T249 — H2f kararsızlığı: kök neden SABİT UYKU DEĞİL, SÜREÇ DPI FARKINDALIĞI

**İş:** `tests/test_yks_mk15_hakem_ekrani.py::H2c_EtiketCakismasi`
(`_ana_open_route_kalinti`, H2f kilidi) tam süitte KIRMIZI, modül tek
başınayken YEŞİL.
**Çürütücü gözlemi (D-464 KAYIT 2):**
`AssertionError: 1 != 0 : ana road3 1142x725: KALINTI KESİŞİM SAYISI DEĞİŞTİ
(beklenen 1, ölçülen 0): []` — amelenin diff'i OLMADAN da yeniden üretildi.
**Mimarın hipotezi:** ölçümden önceki `self._pompala(lambda: False, 0.2)`
sabit uykusu; yeniden çizim 0,2 s'de bitmezse ölçüm çizim öncesini görür.

Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`.
Çalışma ağacı: `O:\navitas\.claude\worktrees\wf_56b658bb-aff-1`.

---

## 1. ÖLÇÜM: mimarın hipotezi YANLIŞ ÇIKTI (ve doğrusu bulundu)

### 1.1 Sabit uyku hiçbir şey beklemiyordu

`tani_h2f.py` H2f ölçüm noktasını **2 s boyunca 20 ms aralıkla** örnekledi
(tuval genişliği × yüksekliği × kesişim sayısı; yalnız DEĞİŞİM noktaları).
Ham çıktı **repodadır**: `tani_h2f_cikti.txt` (çürütücü KUSUR 3 üzerine
12 Eyl 06:4x'te yeniden koşuldu; `--dpi`li ikizi `tani_h2f_dpi_cikti.txt`):

```
olcek=1.0 road=1: 95 ornek, degisim noktalari=[(0.0, 742, 450, 0)]
olcek=1.0 road=2: 94 ornek, degisim noktalari=[(0.0, 742, 450, 0)]
olcek=1.0 road=3: 94 ornek, degisim noktalari=[(0.0, 742, 450, 1)]
olcek=1.5 road=1: 95 ornek, degisim noktalari=[(0.0, 945, 630, 0)]
olcek=1.5 road=2: 93 ornek, degisim noktalari=[(0.0, 945, 630, 0)]
olcek=1.5 road=3: 93 ornek, degisim noktalari=[(0.0, 945, 630, 1)]
```

⚠ Alıntıdaki `N ornek` sayısı (93–95) koşum hızına bağlıdır ve koşumdan koşuma
±2 oynar — ölçümün İDDİASI o sayı değil, **değişim noktası listesinin tek
elemanlı ve `t = 0,000`'da olmasıdır**. Yukarıdaki üç satır
`tani_h2f_cikti.txt`ten alınmıştır (sayılar o dosyadaki koşumun sayılarıdır).

Altı durumun **altısında da** doğru değer daha `t = 0,000`'da hazır ve 2 s
boyunca **hiç değişmiyor**. Sebebi ürün kaynağındadır: `_harita_ciz()`
`_mesaj_isle` içinde **eşzamanlı** koşar (`comms/yks_gui.py:1968`) ve
`_mesaj_ver` çerçeve işlenene dek bekler. Yani çizim, `_mesaj_ver`
döndüğünde **bitmiştir**; 0,2 s uyku hiçbir şey eklemiyordu.

### 1.2 Asıl değişken TUVAL BOYUTU; onu da SÜREÇ DPI FARKINDALIĞI belirliyor

`YksArayuz._arayuz_kur` (`comms/yks_gui.py:973`) pencereyi **ekran
boyutundan** türetir:

```python
sw, sh = self.kok.winfo_screenwidth(), self.kok.winfo_screenheight()
w, h = min(S(1240), int(sw * 0.92)), min(S(940), int(sh * 0.90))
```

`winfo_screenwidth()` süreç DPI farkındalığına bağlıdır (bu makinede ölçüldü):

| süreç farkındalığı | ekran | `winfo_fpixels('1i')` |
|---|---|---|
| 0 (UNAWARE) | 1707 × 1067 | 95,9 |
| 1/2 (AWARE) | **2560 × 1600** | 143,9 |

Sonuç ilk olarak `tani_h2f.py --dpi` ile, **DÜZELTME ÖNCESİ ağaçta** ölçüldü:
ana tuval 1,5 ölçekte `1142 × 725` çıkıyor ve H2f kalıntısı kayboluyordu.

⚠ **ATIF DÜZELTMESİ (12 Eyl, çürütücü KUSUR 3).** Ağaç artık ÇİVİLİ olduğu için
`tani_h2f.py --dpi` bugün 1142 × 725 DEĞİL `945 × 630` yazar — bu, çivilemenin
işe yaradığının kendisidir, ama §1.2'nin dayanağı olamaz. O yüzden bu bölümün
dayanağı **repodaki üç dosyaya** çevrildi (üçü de 1142 × 725'i BUGÜNKÜ ağaçta
yeniden üretir):

| Dosya | Nasıl üretildi | Alıntı |
|---|---|---|
| `mutasyon_M1.txt` | çivileme + sabit uyku TAM GERİ ALINIR, DPI AÇIK | `AssertionError: 1 != 0 : ana road3 1142x725: KALINTI KESİŞİM SAYISI DEĞİŞTİ (beklenen 1, ölçülen 0): []` |
| `kapsam_izi_dpili_cikti.txt` | `kapsam_izi.py --dpi` (SetProcessDpiAwareness taklidi) | `olcek=1.5 ad='no_route_uzun DOĞAL' tuval=1142x725 civili=False` |
| `kapsam_izi_mujoco_cikti.txt` | `kapsam_izi.py --mujoco` — **gerçek mekanizma**: MuJoCo modülü önce koşar, `[DPI] mujoco SONRASI = 2` | `olcek=1.5 ad='no_route DOĞAL' tuval=1142x725 civili=False` |

Bugünkü çivili ağacın `--dpi` koşumu (`tani_h2f_dpi_cikti.txt`) ise
`olcek=1.5 road=3: ... [(0.001, 945, 630, 1)]` yazar: DPI açıkken bile tuval
945 × 630, kalıntı sayısı 1 — **çivilemenin ölçümü**.

1142 × 725 — **çürütücünün gördüğü boyutun ta kendisi**. Ana harita büyüyünce
"İKA-KB" ↔ "ref" kalıntı kesişimi kayboluyor ve `beklenen 1, ölçülen 0` düşüşü
oluşuyor. Ölçek 1,0 etkilenmiyor (`min(1240, 2355) = 1240` her iki durumda da
aynı), bu yüzden düşüş yalnız 1,5'te görünüyordu.

### 1.3 Farkındalığı KİM değiştiriyor: tam süit izi

`dpi_izi.py` tam süiti koşarken her testin öncesinde ve sonrasında
`GetProcessDpiAwareness` okur. 2734 testlik koşumda **tek bir geçiş** var
(`dpi_izi_cikti.txt`):

```
[DPI] baslangic = 0
[DPI] 0 -> 2  (SONRA: test_sim_mujoco_arena.KameraYonSozlesmesi.test_kuzeye_bakan_karede_ib_altta)
[DPI] bitis = 2
```

`tests/test_sim_mujoco_arena.py:278` `mujoco.Renderer(m, 160, 160)` bir OpenGL
bağlamı açar; MuJoCo'nun Windows GL arka ucu süreç DPI farkındalığını **süreç
genelinde ve GERİ ALINAMAZ** biçimde PER_MONITOR (2) yapar. Alfabetik keşif
sırasında `test_sim_mujoco_arena` (**s**) hakem ekranından (**y**) ÖNCE gelir —
yani tam süitte hakem ekranı **her zaman** farkındalık açıkken koşar, modül tek
başına koşarken **hiç** açık değildir.

⚠ Bu yüzden kusur **kararsız değil, BAĞLAM-BELİRLENİMLİDİR**: tam süitte her
seferinde kırmızı, tek başına her seferinde yeşil. Mimarın "master'ta tek başına
3/3 yeşil" ölçümü ile çürütücünün "tam süitte kırmızı" ölçümü **çelişmiyor**;
ikisi farklı süreç durumunu ölçüyordu.

⚠ Kusur aynı zamanda bir **taşınabilirlik kusurudur**: MuJoCo kurulu olmayan bir
makinede (modül atlanır) aynı kilit YEŞİL olur. Yani kapı, ilgisiz bir testin
varlığına bağlıydı.

## 2. Düzeltme (yalnız test; bu görevde ürün kodu DEĞİŞMEDİ)

`tests/test_yks_mk15_hakem_ekrani.py`:

1. **ANA TUVAL ÇİVİLENDİ** — `H2c.ANA_TUVAL = {1.0: (742, 450), 1.5: (945, 630)}`
   ve `_ana_tuvali_civile(olcek)`: `pack_configure(expand=False, fill="none")` +
   `configure(width, height)` + gerçek yerleşim koşulu (`winfo_ismapped` **ve**
   boyut tam eşit). Ölçüm yüzeyi artık ekran çözünürlüğünden ve süreç DPI
   durumundan **bağımsız**. Kilit **gevşemedi**: `ANA_OPEN_ROUTE_KALINTI`
   değerleri (road1 `[]`, road2 `[]`, road3 `[("İKA-KB","ref")]`) **aynen
   duruyor**; yalnız ölçüldükleri tuval artık **beyan edilmiş**.
   Çivilemenin ardından `self.app._harita_ciz()` çağrılır: ana haritanın
   `<Configure>` bağı YOKTUR, yani boyut değişince ürün kendiliğinden yeniden
   çizmez ve eski boyuta göre hesaplanmış yerleşim ölçülürdü (bu, çivilemenin
   ilk denemesinde GERÇEKTEN düşüş verdi — ölçüldü, düzeltildi).

   🔴 **KAPSAM BEYANI (T250 — çürütücü KUSUR 2 üzerine, 12 Eyl).** Çivilemenin
   ilk sürümü `_ana_denetle`i DE çivilenmiş tuvale taşımıştı; bedeli, ana
   haritanın ROTA YOK yerleşiminin **ekrandan TÜREYEN** tuvalde (süreç DPI
   farkındalığı açıkken 1,5 ölçekte ölçüldü: **1142 × 725**) artık hiç
   ölçülmemesiydi — hakemin sahada gerçekten gördüğü yüzey odur. Bu daralma
   **beyan edilmemişti**; çürütücü RED gerekçesi yaptı ve haklıydı.

   **Kapanış (a şıkkı — kapsam GERİ KAZANILDI, bırakılmadı):** `_h2c` artık
   `_ana_denetle`i İKİ yüzeyde koşar — ÖNCE ekrandan türeyen DOĞAL tuvalde
   (`ana_no_route_uzun_DOGAL`, `ana_no_route_DOGAL`), SONRA çivilenmiş tuvalde
   (`ana_no_route_uzun`, `ana_no_route`). H2f kalıntı SAYI kilidi hükmünü
   **yalnız çivilenmiş** tuvalde verir (sayı kilidi ölçek-bağımlıdır);
   `_ana_denetle`in üç iddiası (kesişen çift YOK, taşma YOK, tek ROTA YOK
   bandı) ölçek-BAĞIMSIZDIR, o yüzden iki yüzeyde de koşabilir.

   **Ölçüm (`kapsam_izi.py`, `_ana_denetle` sarmalanıp tuval boyutu yazdırıldı):**

   | Koşum | dosya | 1,0 yüzeyleri | 1,5 yüzeyleri |
   |---|---|---|---|
   | DPI KAPALI | `kapsam_izi_dpisiz_cikti.txt` | 742×450 | 945×630 |
   | DPI AÇIK (taklit) | `kapsam_izi_dpili_cikti.txt` | 742×450 | **945×630 + 1142×725** |
   | **MuJoCo** (gerçek mekanizma, `[DPI] mujoco SONRASI = 2`) | `kapsam_izi_mujoco_cikti.txt` | 742×450 | **945×630 + 1142×725** |

   Üç koşum da YEŞİL; `TOPLAM _ana_denetle cagrisi = 8` (RED'den önce 4'tü).

   **Kapsam noktası GERÇEKTEN ölçüyor mu? (`kapsam_mutasyonu.py`)** Sağlam
   üründe yeşil koşmak tek başına bir şey kanıtlamaz. Bu yüzden YALNIZ geniş
   tuvalde görünen sentetik bir ürün kusuru enjekte edildi (ana haritada tuval
   ≥ 1000 px ise ikinci, sahte bir `ROTA YOK — …` metni çizilir; enjeksiyon
   süreç içindedir, ürün kaynağı DEĞİŞMEZ) ve iki kurgu karşılaştırıldı:

   | Kurgu | Ne | Sonuç |
   |---|---|---|
   | `YENI` | HEAD: `_ana_denetle` doğal + çivili | **KIRMIZI** — `ana no_route_uzun DOĞAL 1142x725` ve `ana no_route DOĞAL 1142x725` |
   | `ESKI` | RED edilen hâl: yalnız çivili 945×630 | **YEŞİL** — kusuru HİÇ göremiyor |

   `KAPSAM_MUTASYON_SONUC GECTI` (`kapsam_mutasyonu_cikti.txt`). Yani daralan
   yüzey gerçek bir kör noktaydı ve kapatıldı — T252'ye devredilmedi.
2. **DÖRT SABİT UYKU KALDIRILDI** (`_pompala(lambda: False, …)`):
   - `_olcekli_kur`: 0,2 s ve 0,3 s → `_yerlesim_durdu(...)`
   - `_ana_open_route_kalinti`: 0,2 s → çivilenmiş tuval koşulu
   - `H6_GorunumDonusSirasi._ilk` ve `_harita_don`: 0,2 s ×2 → `_yerlesim_durdu`

   Dosyada `_pompala(lambda: False, …)` kalıbı **kalmadı** (kalan tek geçiş bir
   yorum satırıdır).
3. **`_GercekEkran._yerlesim_durdu(w)`** — sabit uyku değil, FİKS NOKTA: parça
   haritalanmış, boyutu 2×2'den büyük **ve** ardışık iki olay pompasında
   DEĞİŞMEMİŞ. (Ölçüm: pencere `deiconify()` sonrası İLK pompada nihai boyuta
   oturuyor ve 1,5 s boyunca değişmiyor — yani uyku hiçbir şey eklemiyor, yalnız
   ölçümü zamana bağlıyordu.)

Hiçbir assert gevşetilmedi (net assert **artışı**), `skip`/`expectedFailure`
yok, ön kayıtlı eşik değişmedi, yeni bağımlılık yok.

⚠ **Kapsam hakkında ölçülene çekilmiş beyan.** Bu belgenin RED'den önceki
sürümü burada "kapsam daraltılmadı" diyordu; bu **YANLIŞTI** — §2.1'deki
KAPSAM BEYANI'na bakınız. Bugünkü doğru cümle: ana haritanın ROTA YOK
yerleşimi artık **iki** yüzeyde ölçülüyor (doğal + çivilenmiş), yani kapsam
RED öncesi master'a göre DARALMADI, **genişledi**; H2f kalıntı sayı kilidi ise
beyan edilmiş tek bir yüzeyde (çivilenmiş) hüküm veriyor.

## 3. Mutasyon — kilidin GERÇEKTEN neye dayandığı

`mutasyon_t249.py` (bayt-tam bozma + `finally` içinde sha256 ile geri yazma),
koşum yüzeyi `kos_dpi.py` (DPI AÇIK = tam süitin durumu). T250'den sonra
`CIVILEME_GERI` deseni YALNIZ `_ana_tuvali_civile(olcek)` çağrısını hedefler
(doğal kapsam noktası yerinde kalır) ve **matris bu ağaçta yeniden koşuldu**:

| # | Mutasyon | Beklenen | Gerçek | Ne öğretir |
|---|---|---|---|---|
| M0 | yok (DPI AÇIK) | 0 | **0** | düzeltme tam süitin ortamında yeşil |
| M1 | TAM GERİ ALMA (çivileme yok + sabit uyku geri) | 1 | **1** | çürütücünün düşüşü **birebir** geri geliyor |
| M2 | yalnız ÇİVİLEME geri (gerçek hazır koşulu kalır) | 1 | **1** | **yükü taşıyan parça çivilemedir** |
| M3 | yalnız SABİT UYKU geri (çivileme kalır) | 0 | **0** | 🔴 **sabit uyku kök neden DEĞİLDİ** |
| M4 | yok (DPI KAPALI, denetim) | 0 | **0** | denetim koşumu |

`MUTASYON_SONUC GECTI` — aynı matris **12 işlemlik CPU yükü altında** da birebir
tekrarlandı (`mutasyon_M1_yuk_altinda.txt`, `mutasyon_M2_yuk_altinda.txt`).

M1'in çıktısı (`mutasyon_M1.txt`) çürütücünün satırının aynısıdır:

```
AssertionError: 1 != 0 : ana road3 1142x725: KALINTI KESİŞİM SAYISI DEĞİŞTİ (beklenen 1, ölçülen 0): []
```

⚠ **M3 kayda geçmelidir:** mimarın hipotezi (sabit uyku) ölçümle **çürüdü**.
Sabit uyku yine de kaldırıldı — ölçümü zamana bağlayan ve bir gün gerçekten
kararsızlık üretecek bir kalıptı — ama H2f'i tam süitte kırmızı yapan şey o
DEĞİLDİ.

## 4. Ardışık koşumlar (yüklü ve yüksüz)

`ardisik_t249.py` üç yüzeyi beşer kez koşar:

| Yüzey | Ne | Yüksüz | 12 işlemlik CPU yükü altında |
|---|---|---|---|
| A | modül tek başına, DPI KAPALI | 5/5 OK | 5/5 OK |
| B | modül tek başına, DPI AÇIK | 5/5 OK | 5/5 OK |
| C | `test_sim_mujoco_arena` + hakem modülü **AYNI SÜREÇTE** (tam süitin sırası) | 5/5 OK | 5/5 OK |

Ağaç son hâline geldikten sonra aynı üçlü bir kez daha koşuldu
(`son_*_{1..5}.txt`): **15/15 yeşil**. **T250 kapsam düzeltmesinden sonra
aynı üçlü bir kez daha koşuldu (`t250_*_{1..5}.txt`): yine 15/15 yeşil
(A 17,3–19,1 s · B 17,3–19,5 s · C 35,9–43,7 s), modül artık **42 test**
(T248c eklendi) ve C yüzeyinin beş çıktısının beşinde de
`[DPI] mujoco SONRASI = 2`.**

Toplam **60 ardışık koşum, 60 yeşil**. Dosyalar: `ardisik_*_{1..5}.txt`
(yüksüz), `yuklu_*_{1..5}.txt` (12 işlemlik CPU yükü), `son_*_{1..5}.txt`
(T249 son ağacı), `t250_*_{1..5}.txt` (T250 ağacı). C yüzeyinin her çıktısı
`[DPI] mujoco SONRASI = 2` satırını taşır — yani kilit gerçekten farkındalık
açıkken ölçüldü.

## 5. Dosyalar

| Dosya | Ne |
|---|---|
| `probe_yerlesim.py` · `probe_yerlesim_cikti.txt` | pencere/tuval yerleşiminin zaman izi (sabit uykunun bir şey beklemediğinin ölçümü) |
| `tani_h2f.py` · `tani_h2f_cikti.txt` · `tani_h2f_dpi_cikti.txt` | H2f ölçüm noktasının zaman izi (`--dpi`, `--yuk`) — §1.1'in ham çıktısı (çürütücü KUSUR 3 üzerine 12 Eyl'de yeniden koşuldu) |
| `kapsam_izi.py` · `kapsam_izi_dpisiz_cikti.txt` · `kapsam_izi_dpili_cikti.txt` · `kapsam_izi_mujoco_cikti.txt` | **T250**: `_ana_denetle` hangi tuval boyutlarında koşuyor — kapsamın geri kazanıldığının ölçümü (§2.1) |
| `kapsam_mutasyonu.py` · `kapsam_mutasyonu_cikti.txt` | **T250**: geri kazanılan kapsam noktası gerçekten ölçüyor mu — sentetik geniş-tuval kusuru enjeksiyonu (YENI KIRMIZI / ESKI YEŞİL) |
| `dpi_izi.py` · `dpi_izi_cikti.txt` | tam süitte farkındalık geçişinin ATFI |
| `kos_dpi.py` | modülü DPI farkındalığı AÇIKKEN koşar |
| `birlikte.py` | MuJoCo + hakem modülü aynı süreçte (tam süit sırası) |
| `mutasyon_t249.py` · `mutasyon_M0..M4.txt` | mutasyon matrisi |
| `ardisik_t249.py` · `ardisik_*`, `yuklu_*`, `son_*`, `t250_*` | 60 ardışık koşum (3 yüzey × 5 × 4 tur) |

⚠ `dpi_izi_cikti.txt` koşumundaki 5 düşüş + 5 hata **ölçümle ilgisizdir**: o
koşum sürerken bu ajan aynı ağaçtaki `comms/yks_gui.py` ve test dosyasını
düzenliyordu (kaynağı AST ile okuyan testler yarı yazılmış dosyayı gördü). O
dosyadan alınan tek veri `[DPI]` satırlarıdır; temiz tam süit kanıtı
`results/push_kapisi/` altındadır.

## 6. Mimarın dikkatine — kapatılan bir, kapatılmayan iki kalem

1. **Aynı sınıf başka testlerde de olabilir.** `winfo_screenwidth()`e bağlı
   pencere boyutu bu dosyadaki H2c/H2f dışındaki Tk testlerini de etkileyebilir
   (H1, H2e, H6). H2e zaten çivili; H1/H6 boyut DEĞİL sıra/konum ölçtüğü için bu
   görevde dokunulmadı — ama **ölçülmedi de**. Ayrı görev önerilir.
2. **`test_sim_mujoco_arena`in süreç genelinde bıraktığı iz.** MuJoCo GL bağlamı
   geri alınamaz bir süreç ayarı değiştiriyor; bu, ileride başka Tk/DPI bağımlı
   her ölçümü sessizce bozabilir. Kalıcı çözüm o modülü AYRI BİR SÜREÇTE
   koşturmaktır. Bu görevin kapsamı değildir; karar mimarındır.
3. ✅ **KAPANDI — kapsam daralması (çürütücü KUSUR 2).** T250'de `_ana_denetle`
   iki yüzeyde koşacak biçimde düzeltildi, ölçüldü (`kapsam_izi_*`) ve kapsam
   noktasının gerçekten ölçtüğü mutasyonla gösterildi (`kapsam_mutasyonu.py`).
   §2.1'deki KAPSAM BEYANI'na bakınız. **T252'ye devredilmedi.**

## 7. Kapı (T248 + T249 + T250, son ağaç)

| Kapı | Sonuç |
|---|---|
| `test_yks_mk15_hakem_ekrani` tek başına | **41/41 OK** (39 + T248'in 2 yeni testi) |
| beş ardışık koşum × 3 yüzey (son ağaç) | **15/15 OK** (`son_*`) |
| `test_yks_*.py` (235 test) | OK |
| `comms/test_comms.py` | GEÇTİ |
| ayna testleri + jetson paketi | OK |
| `scripts/akis_diyagram_dogrula.py` | `TÜM DÜĞÜMLER TUTTU` (akis_d 100/100) |
| genel kapı (madde 14) | **kol1 15/15 · kol2 şerit 15/15** |
| `scripts/push_kapisi.py --kuru` #1 | `Ran 2736 · OK (skipped=19)` + kapı 15/15 — `results/push_kapisi/20260912_053049` |
| `scripts/push_kapisi.py --kuru` #2 | `Ran 2736 · OK (skipped=19)` + kapı 15/15 — `results/push_kapisi/20260912_054022` |


### 7.1 T250 (çürütücü RED'i üzerine) — YENİDEN KOŞULAN kapılar

Ölçüm tarafına dokunulmadı; yalnız DEĞİŞEN dosyaların kapıları tekrarlandı
(değişenler: `tests/test_yks_mk15_hakem_ekrani.py`, `tests/belge_kilidi.py`
docstring'i ve kanıt dizinleri).

| Kapı | Sonuç |
|---|---|
| `ardisik_t249.py --tur 5 --onek t250` (3 yüzey × 5) | **15/15 OK** · `ARDISIK_SONUC GECTI` · modül 42 test |
| `test_yks_*.py` | `Ran 236 · OK` |
| `comms/test_comms.py` | EXIT 0 — `✓ TEST GEÇTİ` |
| `scripts/akis_diyagram_dogrula.py` | akis_a 51 · akis_b 68 · akis_c 62 · akis_d **100/100** · akis_e 70 · `SONUÇ: TÜM DÜĞÜMLER TUTTU` |
| `scripts/jetson_paket_hazirla.py` | EXIT 0 |
| ayna/türev kapıları (9 modül) | `test_olcum_ayna_senkronu` 6 · `test_t202_jetson_paket_butunlugu` 7 · `test_jetson_paket_defteri` 6 · `test_imgsz_tek_kaynak` 9 · `test_t191_veri_kaynaklari_taze` 11 · `test_akis_kapsam_korumasi` 59 · `test_fdr_sarkan_atif_kapisi` 11 · `test_gece_akis_diyagramlari` 13 · `test_atolye_test_gunu` 39 — **hepsi OK** |
| `test_t120_sahte_kapi_yasagi.py` | `Ran 15 · OK` (master'dan miras kırmızı kapatıldı — `../t250_master_kirmizisi/KANIT.md`) |
| `test_belge_kilidi.py` + `belge_kilidi`yi içe alan 4 modül | 74 / 63 / 45 / 57 / 42 — hepsi OK |
| `codes/test_rota_sentetik.py` (madde 14) | **kol1 15/15 · kol2 şerit 15/15** |
| `scripts/push_kapisi.py --kuru` #1 (T250 ağacı, master `46ffb503` üzerinde) | `Ran 2816 · OK (skipped=19)` + kapı 15/15 — `results/push_kapisi/20260912_071749` |
| `scripts/push_kapisi.py --kuru` #2 (SON ağaç, master `dd7cd12a` dâhil) | `Ran 2816 · FAILED (failures=2)` — **ikisi de master'ın D-373 kusuru**, ürün/test kaynağıyla ilgisiz — `results/push_kapisi/20260912_072913` |
| `scripts/push_kapisi.py --kuru` #3 (SON ağaç, master `dd7cd12a` deltası yalıtılmış) | **`Ran 2816 · OK (skipped=19)`** + kapı 15/15 — `results/push_kapisi/20260912_074950`; yöntem ve gerekçe: `../t250_master_kirmizisi/KANIT.md` §9 |
| `kapsam_mutasyonu.py` | `KAPSAM_MUTASYON_SONUC GECTI` |
| `mutasyon_t249.py` (yeni ağaçta yeniden) | `MUTASYON_SONUC GECTI` (yüksüz **ve** 12 işlemlik CPU yükü altında) |
| `t248/mutasyon_t248.py` (N0–N3) | `MUTASYON_SONUC GECTI` |
| `t248/akis_kapsam_beklenen.py --mutasyon` | `AKIS_KAPSAM_BEKLENEN GECTI` |

⚠ `results/push_kapisi/20260912_070314` koşumu **KIRMIZIDIR ve kayıtta öyle
durmalıdır**: tek düşüşü master'ın `46ffb503` commit'inden miras alınan T120
kusuruydu (`tests/belge_kilidi.py` muafiyet işareti yok). Kusur ayrı bir
worktree'de master üzerinde ÖLÇÜLDÜ ve kapatıldıktan sonraki koşum
(`20260912_071749`) yeşildir. Ayrıntı: `../t250_master_kirmizisi/KANIT.md`.

⚠ `results/push_kapisi/20260912_052020` koşumu **KIRMIZIDIR ve kayıtta öyle
durmalıdır**: T248'in ürün dosyasında yarattığı 14 satırlık kayma üç türev
kapıyı bayatlatmıştı (`ATOLYE_TEST_GUNU_20260912.md` kod atıfları,
`akis_d_dugumler.md`, `akis_d.svg`). Üçü de kapatıldıktan sonraki iki koşum
yukarıdaki gibi yeşildir.
