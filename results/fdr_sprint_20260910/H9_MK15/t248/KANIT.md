# T248 — ÜRÜN KUSURU: NO_ROUTE'tan sonraki TEKRAR OPEN_ROUTE haritayı tazelemiyor

**Bulgu sahibi:** bağımsız çürütücü (D-464 KAYIT 1). **Sınıf:** bayat ekran —
hakem ekranı ile sistem durumu ayrışıyor. **Sahayı ilgilendirir.**

**Kusur:** `comms/yks_gui.py` `_mesaj_isle` OPEN_ROUTE kolunda
`self.rota_yok = None` ve `self.tespit_bayat = False` **koşulsuz** çalışır, ama
`self._harita_ciz()` `if yeni:` bloğunun **İÇİNDEDİR**. Sahada
`comms/iha_sender.py:171 _tekrarli_gonder(repeat=8, interval=0.25)` her
OPEN_ROUTE'u **sekiz kopya** yollar; NO_ROUTE'tan SONRA ulaşan bir kopya
(AYNI seq → `yeni = False`) durumu "rota kabul edildi"ye çevirir ama **haritayı
yeniden çizmez**: hakem ekranı "ROTA YOK — … · İKA GÜVENLİ DURUŞTA" bandını
göstermeye devam eder. Hakem rotayı **ekrandan** onayladığı için (§2.2.3) bu
doğrudan görev puanını etkiler.

Yorumlayıcı: `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`.

---

## 1. ÖNCE ÖLÇÜLDÜ (ürün DEĞİŞTİRİLMEDEN)

Gerçek Tk + gerçek UDP ile senaryo kuruldu
(`tests/test_yks_mk15_hakem_ekrani.py::H2g_TekrarliOpenRouteHaritayiTazeler`,
ana tuval 742×450'ye çivili, sabit uyku yok):

1. `OPEN_ROUTE seq=N` → bant yok (önkoşul ölçüldü),
2. `NO_ROUTE seq=N+1` → bant **var** (önkoşul ölçüldü),
3. **aynı** `OPEN_ROUTE seq=N` tekrar (sahadaki 8 kopyanın biri).

Düzeltme ÖNCESİ ölçüm (`dogrulama_duzeltme_oncesi.txt`):

```
AssertionError: Lists differ: [] != ['ROTA YOK — KORIDOR_DEGIL · İKA GÜVENLİ D[35 chars]ldı']
First extra element 0:
'ROTA YOK — KORIDOR_DEGIL · İKA GÜVENLİ DURUŞTA\nkoridor genişlik tavanı aşıldı'
 : T248: durum 'rota kabul' derken ana harita hâlâ ROTA YOK bandını gösteriyor
```

Aynı anda `app.rota_yok is None` — yani **durum ile ekran ayrışmış** durumda.
`_olculu_alan` da dolu kalıyor (ROTA YOK ölçülü yerleşimi OPEN_ROUTE çizimine
taşınabilir hâle geliyor).

Tekrarın gerçekten işlendiğini ölçen sayaç `rx_alim[seq]`dir
(`comms/yks_gui.py:1918`, her KABUL EDİLEN kopyada artar) — test `_tekrar_ver`
yardımcısında bu sayacı + boş kuyruğu bekler, **sabit uyku kullanmaz**.
(`_mesaj_ver`in hazır koşulu tekrar çerçevesi için gönderimden ÖNCE de doğru
olduğu için burada kullanılamaz; bu ayrım testin belgesinde yazılıdır.)

## 2. Düzeltme — DAR

`comms/yks_gui.py`, OPEN_ROUTE kolu:

```python
rota_yok_temizlendi = self.rota_yok is not None   # `rota_yok = None`den ÖNCE
...
if yeni:
    ...
    self._harita_ciz()
    ...
elif rota_yok_temizlendi:
    self._harita_ciz()
```

- Çizim **yalnız DURUM DEĞİŞTİYSE** yapılır. Sekiz kopyanın tamamında çizmek
  8 kat gereksiz yük demektir; kapı bunu da kilitler (aşağıda N2).
- `tespit_bayat` bilerek kapsam dışıdır: onu `_durum_tazele` her tikte yeniden
  türetir (`comms/yks_gui.py:4308-4331`) ve haritayı etkilemez.
- NO_ROUTE kolunda aynı kusur **yoktur**: OPEN_ROUTE `rota_yok`u `None` yaptığı
  için sonraki NO_ROUTE'ta `onceki_seq is None` olur ve `yeni` True çıkar
  (okundu, `comms/yks_gui.py:1989-1993`).

Düzeltme sonrası: `dogrulama_duzeltme_sonrasi.txt` → `Ran 2 tests … OK`.

## 3. Kapı iki yönlüdür

`H2g_TekrarliOpenRouteHaritayiTazeler`:

| Test | Ne kilitler |
|---|---|
| `test_T248_no_route_sonrasi_tekrarli_open_route_haritayi_tazeler` | durum DEĞİŞTİYSE ekran TAZELENİR (bant gider, `_olculu_alan` boşalır) |
| `test_T248b_durum_degismeyen_tekrar_haritayi_yeniden_cizmez` | durum DEĞİŞMEDİYSE **8 tekrar kopyası için hiç çizim yapılmaz** |
| `test_T248c_kamera_gorunumunde_kucuk_harita_da_tazelenir` | **T250 (çürütücü kapsam gözlemi)**: düzeltme `_harita_ciz()`i ARGÜMANSIZ çağırdığı için kamera görünümündeki KÜÇÜK harita da tazelenir (`comms/yks_gui.py:1561-1565`); bu yol RED'e kadar ölçülmüyordu |

## 4. Mutasyon

`mutasyon_t248.py` (bayt-tam bozma + `finally` içinde sha256 ile geri yazma):

| # | Mutasyon | Beklenen | Gerçek |
|---|---|---|---|
| N0 | yok | 0 | **0** |
| N1 | ÜRÜN: `elif rota_yok_temizlendi: self._harita_ciz()` SİLİNİR (düzeltme öncesi) | 1 | **1** |
| N2 | ÜRÜN: çizim KOŞULSUZ (`else:`) — her tekrarda yeniden çiz | 1 | **1** |
| N3 | **T250**: ÜRÜN: tazeleme YALNIZ ana tuvale daraltılır (`_harita_ciz(self.harita)`) — küçük harita bayat kalır | 1 | **1** |

`MUTASYON_SONUC GECTI`. N1 kusurun yakalandığını, N2 "gereksiz yeniden çizim
yapma" kuralının da gerçekten ölçüldüğünü gösterir — yani kapı tek yönlü bir
"her ihtimale karşı çiz" çözümünü kabul etmez.

**N3 neyi öğretir (T250).** N3 ana harita yolunu BOZMAZ: T248 ve T248b o
koşumda **YEŞİL** kalır, yalnız T248c düşer —
`AssertionError: Lists differ: [] != ['ROTA YOK — KORIDOR_DEGIL · İKA GÜVENLİ D…ldı']`
(`mutasyon_N3.txt`). Yani T248c ayrı bir ürün yolunu ölçüyor; küçük harita
tazelemesi artık ölçülmemiş değil, **kilitli**.

## 5. `comms/` değişikliğinin yan kapıları

| Kapı | Sonuç |
|---|---|
| `scripts/jetson_paket_hazirla.py` | EXIT 0, izlenen dosyada değişiklik yok |
| ayna testleri (`test_olcum_ayna_senkronu`, `test_t202_jetson_paket_butunlugu`, `test_jetson_paket_defteri`, `test_imgsz_tek_kaynak`, `test_t191_veri_kaynaklari_taze`) | hepsi OK |
| `scripts/akis_diyagram_dogrula.py` | satır kayması yüzünden BAYATLADI → `akis_satir_tazele.py --taban 776f0254~1` (75 düğüm tazelendi, `akis_satir_tazele.txt`) + d47 elle düzeltildi → `SONUÇ: TÜM DÜĞÜMLER TUTTU` |
| `FDR/sekiller/akis_d.mmd` | yeni ürün dalı için **iki düğüm eklendi** (`d59` karar, `d59b` çizim); okuma notu `akis_kapsam_OKUBENI.md` |
| `akis_kapsam_t226d.py --taban 776f0254~1` **EXIT=1 beklentisi** | **T250**: düzyazı beyan ÖN KAYDA bağlandı — `akis_kapsam_beklenen.py` `[YENI]` kümesinin TAM OLARAK `{d59→yks_gui.py:1973, d59b→yks_gui.py:1981}` olduğunu, diğer tüm hata türlerinin 0 olduğunu ve çıkışın 1 olduğunu denetler; `--mutasyon` ile pin'in boş olmadığı gösterildi (d59b düğümü silinince küme değişti, pin YAKALADI). Çıktı: `akis_kapsam_beklenen_cikti.txt` → `AKIS_KAPSAM_BEKLENEN GECTI` |
| `tests/test_akis_kapsam_korumasi.py`, `test_fdr_sarkan_atif_kapisi.py` | OK |

## 6. Mimarın dikkatine — kapatılmayan bir kalem

Tekrar kopyası `tespit_bayat`ı `False` yapıyor ama `_onay_dugmesini_tazele()`
çağırmıyor; ekranda "BAYAT TESPİT — ONAY KAPALI" yazısı bir sonraki
`_durum_tazele` turuna kadar (ve tespit gerçekten tazeyse **kalıcı olarak**)
asılı kalabilir. Bu ayrı bir yoldur, haritayı ilgilendirmez ve bu görevde
**değiştirilmedi** — ölçülmedi de. Ayrı görev önerilir.
