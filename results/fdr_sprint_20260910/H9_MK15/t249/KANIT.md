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
(tuval genişliği × yüksekliği × kesişim sayısı; yalnız DEĞİŞİM noktaları):

```
olcek=1.0 road=1: 95 ornek, degisim noktalari=[(0.0, 742, 450, 0)]
olcek=1.0 road=3: 94 ornek, degisim noktalari=[(0.0, 742, 450, 1)]
olcek=1.5 road=3: 94 ornek, degisim noktalari=[(0.0, 945, 630, 1)]
```

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

Sonuç, aynı `tani_h2f.py` ile `--dpi` bayrağıyla ölçüldü:

```
[dpi] SetProcessDpiAwareness(1) -> 0
  olcek=1.5 road=1: [(0.0, 1142, 725, 0)]
  olcek=1.5 road=3: [(0.0, 1142, 725, 0)]     <- kalinti KAYBOLUYOR
```

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

Hiçbir assert gevşetilmedi (net assert **artışı**), kapsam daraltılmadı,
`skip`/`expectedFailure` yok, ön kayıtlı eşik değişmedi, yeni bağımlılık yok.

## 3. Mutasyon — kilidin GERÇEKTEN neye dayandığı

`mutasyon_t249.py` (bayt-tam bozma + `finally` içinde sha256 ile geri yazma),
koşum yüzeyi `kos_dpi.py` (DPI AÇIK = tam süitin durumu):

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
(`son_*_{1..5}.txt`): **15/15 yeşil**.

Toplam **45 ardışık koşum, 45 yeşil**. Dosyalar: `ardisik_*_{1..5}.txt`
(yüksüz), `yuklu_*_{1..5}.txt` (12 işlemlik CPU yükü), `son_*_{1..5}.txt`
(son ağaç). C yüzeyinin her çıktısı `[DPI] mujoco SONRASI = 2` satırını
taşır — yani kilit gerçekten farkındalık açıkken ölçüldü.

## 5. Dosyalar

| Dosya | Ne |
|---|---|
| `probe_yerlesim.py` · `probe_yerlesim_cikti.txt` | pencere/tuval yerleşiminin zaman izi (sabit uykunun bir şey beklemediğinin ölçümü) |
| `tani_h2f.py` | H2f ölçüm noktasının zaman izi (`--dpi`, `--yuk`) |
| `dpi_izi.py` · `dpi_izi_cikti.txt` | tam süitte farkındalık geçişinin ATFI |
| `kos_dpi.py` | modülü DPI farkındalığı AÇIKKEN koşar |
| `birlikte.py` | MuJoCo + hakem modülü aynı süreçte (tam süit sırası) |
| `mutasyon_t249.py` · `mutasyon_M0..M4.txt` | mutasyon matrisi |
| `ardisik_t249.py` · `ardisik_*`, `yuklu_*` | 30 ardışık koşum |

⚠ `dpi_izi_cikti.txt` koşumundaki 5 düşüş + 5 hata **ölçümle ilgisizdir**: o
koşum sürerken bu ajan aynı ağaçtaki `comms/yks_gui.py` ve test dosyasını
düzenliyordu (kaynağı AST ile okuyan testler yarı yazılmış dosyayı gördü). O
dosyadan alınan tek veri `[DPI]` satırlarıdır; temiz tam süit kanıtı
`results/push_kapisi/` altındadır.

## 6. Mimarın dikkatine — kapatılmayan iki kalem

1. **Aynı sınıf başka testlerde de olabilir.** `winfo_screenwidth()`e bağlı
   pencere boyutu bu dosyadaki H2c/H2f dışındaki Tk testlerini de etkileyebilir
   (H1, H2e, H6). H2e zaten çivili; H1/H6 boyut DEĞİL sıra/konum ölçtüğü için bu
   görevde dokunulmadı — ama **ölçülmedi de**. Ayrı görev önerilir.
2. **`test_sim_mujoco_arena`in süreç genelinde bıraktığı iz.** MuJoCo GL bağlamı
   geri alınamaz bir süreç ayarı değiştiriyor; bu, ileride başka Tk/DPI bağımlı
   her ölçümü sessizce bozabilir. Kalıcı çözüm o modülü AYRI BİR SÜREÇTE
   koşturmaktır. Bu görevin kapsamı değildir; karar mimarındır.

## 7. Kapı (T248 + T249 birlikte, son ağaç)

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

⚠ `results/push_kapisi/20260912_052020` koşumu **KIRMIZIDIR ve kayıtta öyle
durmalıdır**: T248'in ürün dosyasında yarattığı 14 satırlık kayma üç türev
kapıyı bayatlatmıştı (`ATOLYE_TEST_GUNU_20260912.md` kod atıfları,
`akis_d_dugumler.md`, `akis_d.svg`). Üçü de kapatıldıktan sonraki iki koşum
yukarıdaki gibi yeşildir.
