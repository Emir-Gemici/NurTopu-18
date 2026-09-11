# H2e kararsızlığı — kök neden ve kanıt (12 Eylül 2026)

**İş:** `tests/test_yks_mk15_hakem_ekrani.py::H2e_RotaYokSonrasiAnaHarita`
tam süitte 6 alt testte düşüyor, tek başına geçiyor.
**Gözlem (mimar, ana ağaç):** `results/push_kapisi/20260912_011758/tam_suit.txt`
→ `Ran 2620 tests · FAILED (failures=6, skipped=12)`; iki hata biçimi
`:726` "NO_ROUTE yerleşimi OPEN_ROUTE'a sızdı" ve `:728`
`'.!frame3.!frame.!canvas' unexpectedly found in {...: (34, 189, 227)}`
(1,5 ölçekte `(51, 156, 243)`).

Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`.
Çalışma ağacı: `O:\navitas\.claude\worktrees\wf_56b658bb-aff-1`.

---

## 1. Yöntem

1. **Yeniden üretme denemesi.** Tam süit (`scripts/push_kapisi.py --kuru`)
   **3 kez** koşuldu. Üçü de H2e'yi düşürmedi:
   `results/push_kapisi/20260912_013837` (ortam eksikleri, H2e YOK),
   `20260912_015144` → `Ran 2616 · OK (skipped=22)`,
   `20260912_020233` → `Ran 2616 · OK (skipped=22)` (3. koşum H2e'ye geçici
   durum kaydı eklenmiş hâliyle).
   ⚠ İlk koşumdaki 21 düşüş H2e ile ilgisizdi: çalışma ağacında `models/`,
   `data/kuru_kosu_fikstur/images`, `data/arena_kompozit/images`,
   `jetson_paket/models` yoktu. Ana ağaçtaki (git dışı) dosyalar sabit bağ
   (hardlink/junction) ile ağaca getirildi; keşif sayısı 2620'ye döndü.
2. **Sıkıştırılmış bağlam (delta debugging).** `h2e_tani.py`:
   - `--tum-import` (2620 testin tamamı içe aktarılır, yalnız H2e koşar) ×3 → OK
     (`d1_tum_import.txt`),
   - H2e'den önce gelen **46 Tk/yks modülünün tamamı aynı süreçte koşturuldu**,
     sonra H2e ×2 → OK (`d2_tk_onek.txt`, `onceki_tk_moduller.txt`).
   Yani kusur ne içe aktarma sırasından ne de Tk modüllerinin bıraktığı
   durumdan geliyor.
3. **Ölçüm.** `_olculu_alan` değerleri gerçek Tk ile ölçüldü
   (`olcum_alan_yalniz.txt`, 742×450 tuval):
   | NO_ROUTE `detay` | OLCEK 1,0 | OLCEK 1,5 |
   |---|---|---|
   | boş / alan yok (tek satır bant) | **(34, 189, 227)** | **(51, 156, 243)** |
   | 624 karakter (uzun bant) | — | (51, 478, **0**) |
   Mimarın gördüğü iki değer **tam olarak "tek satırlık bant"** değerleridir.
4. **Provokasyon.** Yabancı bir `127.0.0.1` ucundan (ayrı soket) NO_ROUTE
   serpildi → düşüş yeniden üretildi.

## 2. Kök neden — FİKSTÜR (ürün kusuru DEĞİL)

İki kusur birlikte çalışıyor:

**(a) Kaynak kilidi bu fikstürde hiçbir şey ayırmıyor.**
`comms/yks_gui.py:739 mesaj_kaynagi_dogrula` İHA verisi (OPEN_ROUTE /
NO_ROUTE / IHA_LANDED) için **yalnız IP'ye** bakar — `adr[0] == iha_peer[0]`.
Bu **saha kuralıdır ve doğrudur** (Jetson'un algı yayıncısı efemer port
kullanır). Ama fikstür üç ucu da `127.0.0.1`'e bağlıyordu: aynı süreçte
koşan **herhangi** bir ucun gönderdiği tek bir NO_ROUTE datagramı hakem
ekranının `rota_yok` alanını eziyor.

**(b) Ölçüm öncesi bekleme SABİT UYKUYDU ve durumu EKSİK denetliyordu.**
`_mesaj_ver` OPEN_ROUTE'ta yalnız `rota.seq`e bakıyor, `rota_yok`un
temizlendiğine bakmıyordu; sonra körlemesine `_pompala(lambda: False, 0.15)`
ile 150 ms olay pompalıyordu. O pencerede işlenen bir NO_ROUTE:
`rota_yok` yeniden dolar → `_harita_ciz` ölçülü yerleşime girer →
`_olculu_alan[str(harita)]` yazılır → sonraki `_cizim()` OPEN_ROUTE
çizimini **ölçülü** üretir. Test bunu "ürün sızdırdı" diye okur. **Sızıntı
YOKTUR; ürünün önbellek yaşam döngüsü doğrudur** — `_harita_ciz` her
çizimde önbelleği ya yazar ya siler (`comms/yks_gui.py:1590-1594`), yani
NO_ROUTE sonrası OPEN_ROUTE çizimi önbelleği **kendisi temizler**.

**İmza eşleşmesi (bit düzeyinde).** Düzeltme öncesi fikstür + 300 ms
aralıkla `detay` alanı OLMAYAN yabancı NO_ROUTE (`mutasyon_M4.txt`):
```
FAIL ... (yol=2, olcek=1.5)
AssertionError: '.!frame3.!frame.!canvas' unexpectedly found in
                {'.!frame3.!frame.!canvas': (51, 156, 243)}
FAIL ... (yol=3, olcek=1.5)
AssertionError: Lists differ: [... .0, 156.0], ...] != [... .0, 144.0], ...]
```
— mimarın çıktısındaki **aynı iki hata biçimi, aynı 6 alt test, aynı sayılar**
(1,5'te 144 ↔ 156; önbellek `(51, 156, 243)`).
`detay` alanı olmayan NO_ROUTE sahada `iha_sender.send_no_route(sebep)`
(`comms/iha_sender.py:240`, `detay=None`) tarafından üretilir; süitte bu
biçimi üreten uçlar vardır.

⚠ **Açık kalan:** 12 Eylül 01:17 koşumunda o datagramı GÖNDEREN ucun kimliği
saptanamadı (3 tam süit koşumunda olay tekrar etmedi). Saptanan şey
**mekanizmadır** ve mekanizma enjeksiyonla birebir yeniden üretilmiştir.

## 3. Düzeltme (yalnız fikstür; ürün kodu DEĞİŞMEDİ)

`tests/test_yks_mk15_hakem_ekrani.py`:

1. `_GercekEkran.IHA_ADRESI = "127.0.0.2"`, `IKA_ADRESI = "127.0.0.3"` —
   İHA/İKA uçları **ayrı geri döngü adresinde**. Artık ürünün KENDİ kaynak
   kilidi yabancı çerçeveyi reddediyor. Gevşetme değil: saha kurulumunun
   (İHA ayrı IP) aynısı, üstelik kilit artık gerçekten ölçülüyor.
   (Bu makinede `127.0.0.0/8` bağlanabiliyor, kaynak adresi korunuyor —
   ölçüldü.)
2. `_mesaj_ver` **sabit uykusuz**: hazır koşulu (1) `app.gelen.empty()`
   (işlenmemiş çerçeve yok) **ve** (2) durumun çerçevenin tam karşılığı
   olması — OPEN_ROUTE'ta `rota.seq == seq` **ve** `rota_yok is None`.
   Koşul sağlandıktan sonra ölçüme kadar **hiç olay pompalanmıyor**, yani
   ölçüm penceresi kapalı.
3. `_yalniz_bizim_cerceveler` önkoşulu: sızıntı hükmünden önce ekranın
   **yalnız bu testin** çerçevelerini işlediği doğrulanır
   (`sayac[OPEN_ROUTE]`/`sayac[NO_ROUTE]`). Tutmazsa düşüş "YABANCI ÇERÇEVE"
   der — ürünü haksız yere suçlamaz.
4. H2e'deki `_pompala(lambda: False, 0.2)` yerine **gerçek yerleşim koşulu**:
   `winfo_ismapped()` **ve** tuval boyutu 742×450. (H1b'de aynı sınıf
   `d812b1e2` ile kapanmıştı.)

Hiçbir assert gevşetilmedi, kapsam daraltılmadı, `skip`/`expectedFailure`
kullanılmadı. Yeni bağımlılık yok.

## 4. Kanıt

| Ne | Dosya | Sonuç |
|---|---|---|
| Tam süit ×3 (düzeltme öncesi) | `results/push_kapisi/20260912_015144`, `…_020233` | H2e düşmedi (yeniden üretilemedi) |
| Tüm modüller içe aktarılmış ×3 | `d1_tum_import.txt` | OK |
| 46 Tk modülü önce koşuldu ×2 | `d2_tk_onek.txt` | OK |
| Alan ölçümü | `olcum_alan_yalniz.txt` | (34,189,227) / (51,156,243) = tek satır bant |
| Yabancı enjeksiyon, düzeltme ÖNCESİ | `d3_yabanci_enjeksiyon.txt` | 6 düşüş (aynı imza) |
| Yabancı enjeksiyon, düzeltme SONRASI | `d4_enjeksiyon_duzeltme_sonrasi.txt` | OK ×2, kabul edilen çerçeve 9/6 (tam) |
| Mutasyon M0–M4 | `mutasyon_ciktisi.txt`, `mutasyon_M*.txt` | **GECTI** (M1/M2/M4 kırmızı, M0/M3 yeşil) |
| Enjeksiyon altında 5 ardışık koşum | `ardisik_1..5.txt` | 5/5 OK, her koşumda 9 OPEN / 6 NO_ROUTE |
| Tam süit ×2 (düzeltme sonrası) | `kapi_kosum_A.txt`, `kapi_kosum_B.txt` | bkz. dosyalar |
| Genel kapı (madde 14) | aynı dosyalar | 15/15 |

### Mutasyon tablosu (`mutasyon_h2e.py` — gerçek dosyayı bozar, `finally` ile sha256 doğrulayarak geri yazar)

| # | Mutasyon | Beklenen | Gerçek |
|---|---|---|---|
| M0 | yok (enjeksiyon var) | 0 | 0 |
| M1 | ayrı geri döngü adresi geri alınır | 1 | 1 |
| M2 | hazır koşulu gevşetilir + 0,15 s sabit uyku geri gelir | 1 | 1 |
| M3 | yabancı çerçeve önkoşulu silinir (adres yalıtımı durur) | 0 | 0 |
| M4 | düzeltme öncesi fikstürün tamamı + seyrek enjeksiyon | 1 | 1 |

M3'ün yeşil olması tasarım gereğidir: yalıtım tek başına yeterlidir, sayaç
önkoşulu **tanıyı** verir (ikinci savunma hattı).

## 5. Mimarın dikkatine — ürün tarafında ayrı bir gözlem (bu görevin konusu DEĞİL)

Uzun `detay` taşıyan NO_ROUTE'ta ana haritanın arena alanı 742×450 tuvalde
`(51, 478, 0)` çıkıyor: **ölçek 0**, yani arena tamamen kayboluyor
(`_harita_olculu_yerlesim` üst bandı 12 tura kadar aşağı itiyor, alt sınır
yok). Hakem ekranında uzun bir ret gerekçesi haritayı yutabilir.
Ölçüm: `olcum_alan_yalniz.txt`. Karar mimarındır; bu görevde
**değiştirilmedi**.
