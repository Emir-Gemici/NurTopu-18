# NAVITAS — DEVİR PROTOKOLÜ

> **Bu dosya neden var:** Bu projede iş defalarca **kota bitişiyle** yarıda kaldı.
> Bir Codex token'ı biterken bir görev zimmetli kaldı; denetim iş akışlarında 25'ten
> fazla ajan oturum limitine takıldı. Yarım kalan iş, **bırakıldığı yeri anlatmazsa**
> kaybolur; devralan sıfırdan keşfe başlar.
>
> **Kural: kotaya yaklaşan her ajan, durmadan önce bu dosyayı doldurur.**

---

## Devreden ajan için — doldurma sırası

1. **Kod yazmayı bırak.** Yarım bir düzeltme, hiç başlamamış bir düzeltmeden tehlikelidir.
2. **Genel kapıyı koş** ve sonucunu buraya yaz — ağacın sağlam olup olmadığı devralanın ilk bilmesi gereken şeydir.
3. Aşağıdaki şablonu **en üste** ekle (eski devirler altta kalsın).
4. Görevi `[IN_PROGRESS]` olarak **bırak**. Kilidi kendin **açma** — `AGENTS.md` §3.

---

## GECE KOSUMU · 2026-08-21 (GUNCEL) · Claude 2 (Opus 5, basamele)

**BITEN ISLER (hepsi push edildi):**
- **T127** temiz bolum zinciri — D-249. On kayit kurali 1 SAGLANDI: kirli
  bolum kazanani SISMEMIS (cati kacagi 0,043 · 67 karede red 0 · K0-K5 gecti).
  Temiz val'de egitim 18 epoch'ta durdu, en iyi epoch 27 -> 10.
- **T115** ustabasi denetimi — D-247 (DOGRU AMA EKSIK; kapiyi ustabasi kostu)
  + D-250 (13 satirin 10'u guvenle onarilabilir; onarim Codex'in isi —
  bagimsizlik geregi ben yapmiyorum, prompt verildi).
- **T129** — D-248: cati korlugu KAYNAK KALITESINE bagli (v34 videoda %96,
  ayni sahnenin ham fotografinda %46; v30 %31 -> %8). Siralama DEGISMIYOR.
- **T128** — D-251: `--tohum` bu recetede ETKISIZ (tohum 0 ile 42 bit-es
  agirlik; mekanizma `ultralytics/data/build.py:359` sabit tohum).
  D-252: bu deney ZATEN v31'de kosulmustu; defteri aramadan tekrarladim,
  1,18 saat GPU bosa gitti. Kalici duzeltme: her on kaydin ilk satiri
  "daha once olculdu mu" aramasi olacak.

**KOSAN IS: T128-B** (deterministic=False, OLCUM kosumu)
- Betik: `scripts/olcum/105_t122_ft_kosumu.py --kip ac --belirsiz`
- Gunluk: `results/t122/ft_ac_belirsiz_log.txt`
- Zincir gunlugu: `results/t122/t128b_zincir_log.txt`
  (egitim bitince kabul zinciri OTOMATIK kosar -> `results/t122/t128b_kabul.txt`)
- On kayit: `results/t128b_on_kayit.md` — DEFTER ARAMASI dahil (tekrar DEGIL)
- ⚠ Beklenen sinir: veri sirasini DEGISTIRMEZ (build.py:359 sabit tohum),
  yalniz SAYISAL belirsizligi olcer. Sonuc bu sinirla raporlanacak;
  "varyans olculdu" diye YAZILMAYACAK.

**KAPI DURUMU (ustabasi kostu):** `codes/test_rota_sentetik.py` -> 15/15 ·
`unittest discover -s tests -q` -> Ran 715 · OK

**MIMARIN MASASINDA:** T122/T127 secim karari (D-237 -> D-239 -> D-240 -> D-249
birlikte okunur) · T126 denetimi (D-244) · T115 devami · T124 sinir cumleleri
(D-224) · T118 adlandirma (D-214) · D-233 kume yeniden uretimi · D-245 kuyruk
boslugu · D-248 (cati korlugu kosullu).

---

## Şablon

```markdown
## Devir <TARİH SAAT> · <Devreden AI> → <Devralan veya "belirsiz">

**Sebep:** kota / çökme / oturum limiti / kullanıcı durdurdu

**Görev:** <T veya S numarası + başlık>
**Durum:** <ne bitti / ne bitmedi — somut>

**Dokunulan dosyalar:**
- `yol/dosya.py` — <ne değişti>

**Genel kapı son durumu:**
```
<komut>
<gerçek çıktı>
exit=<kod>
```

**Çalışma ağacı temiz mi:** evet / hayır — <hayırsa ne yarım kaldı>

**Devralanın İLK yapması gereken:**
<tek somut eylem>

**Tuzaklar:** <devralanın bilmezse zaman kaybedeceği şey>
```

---

## Devralan ajan için — açılış listesi

1. Bu dosyanın **en üstündeki** devir kaydını oku.
2. **Genel kapıyı kendin koş.** Devredenin yazdığına güvenme — ağaç arada değişmiş olabilir.
   ```
   O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
   ```
   Düşüyorsa **yeni görev alma**; önce onu onar.
3. `git status --porcelain` ile çalışma ağacını kontrol et. Yarım değişiklik varsa
   devir kaydıyla karşılaştır; kayıtta olmayan bir değişiklik varsa **dur ve bildir**.
4. Bayat kilit varsa **serbest bırakılmasını iste** — kendin açma (`AGENTS.md` §3).
5. Sonraki `[ ]` görevi al.

---

## Bayat kilit — bilinen olay

Codex-1 token'ı biterken **T14** görevi `[IN_PROGRESS: Codex-1]` durumunda kaldı.
Kod aşamasına hiç geçmemişti (yalnız zimmetlemişti), çalışma ağacı temizdi ve genel
kapı 15/15 geçiyordu — ama kilit hâlâ oradaydı ve kuyruğu tıkıyordu.

**Ders:** Zimmetlemek ile iş yapmak farklı şeylerdir. Devir kaydı, kilidin **arkasında
gerçekte ne olduğunu** söylemelidir.

---

# DEVİR KAYITLARI

*(en yeni en üstte)*

## Devir 2026-08-04 · Codex-1 → belirsiz

**Sebep:** kota (token bitti)

**Görev:** T14 — FDA parametrizasyonu: 20×20 m alan, ≥30 m irtifa
**Durum:** Görev zimmetlendi ama **kod aşamasına hiç geçilmedi.** FDA profiliyle ilgili
hiçbir dosyaya dokunulmadı. Son dokunulan kod dosyaları T13'e aittir; ardından yalnız
belgeler güncellenmiştir.

**Dokunulan dosyalar:** T14 kapsamında **yok**.

**Genel kapı son durumu:** *(mimar tarafından doğrulandı)*
```
O:\navitas-local-train\venv\Scripts\python.exe codes/test_rota_sentetik.py
SONUC: 15/15 dogru
[OK] TUM DETERMINISTIK SAHNELER GECTI
exit=0

-B -m unittest discover -s tests
Ran 58 tests in 7.569s
OK
```

**Çalışma ağacı temiz mi:** evet — T14 açısından. (Diğer görevlerin commit edilmemiş
değişiklikleri mevcut, bu beklenen durumdur.)

**Devralanın İLK yapması gereken:** T14 kilidinin serbest bırakılmasını iste
(`AGENTS.md` §3). Kilit açıldıktan sonra T14 **temiz devralınabilir** — hiçbir yarım
iş yoktur.

**Tuzaklar:**
- T1–T13 `READY_FOR_REVIEW` durumunda ve mimar denetiminden geçti. **6'sı KISMİ** —
  ayrıntı `REVIEW_LOG.md`'de. Yeni iş almadan önce oraya bak, aynı kusuru tekrar üretme.
- `S1` görevi **TIKAYICI**: veri üreteci araçları "zemin" olarak etiketliyor.
  **S1 düzeltilmeden hiçbir veri üretimi veya eğitim koşusu başlatılmaz.**
