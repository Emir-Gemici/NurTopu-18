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

## GECE KOSUMU · 2026-08-21 · Claude 2 (Opus 5, basamele) → devralan varsa

> Bu bir DEVIR DEGIL, KOSAN ZINCIRIN DURUM KAYDIDIR. Kullanici uyuyor, PC acik.
> Zincir koparsa devralan buradan devam eder.

**KOSAN IS: T127 temiz bolum zinciri** — TEK betik, elle adim YOK.
- Betik: `scripts/olcum/116_t127_temiz_bolum_zinciri.py` (aynali)
- Gunluk: `results/t127_zincir_log.txt`
- On kayit (KILITLI, D-107): `results/t127_on_kayit.md`
- **Adim 1 BITTI ve fail-closed kapisini gecti:** train 344 · val 96 ·
  **KIRLI val 0** · ikiye bolunen kaynak 0
  (kume `dataset/copy_paste_t127`, yaml `dataset/karisim_t127.yaml`)
- **Adim 3 (egitim `t127_temiz`) KOSUYOR.** Bitince adim 4 AYNI betikte
  otomatik kosar: 65 kabul zinciri · 109 kiyas · 115 bakir kare kiyasi ->
  ciktilar `results/t127_temiz/` altina.
- Zincir coker ve devralan gerekirse ayni betik bastan kosulabilir: adim 1
  kumeyi yeniden kurar, egitim `exist_ok=True` ile ayni dizine yazar.
- ⚠ Kosum ortami ZORUNLU: `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` ve
  `PYTHONIOENCODING=utf-8` (olmadan egitim izsiz kalir — olculdu).

**DURDURULAN IS: T128 (tohum gurultusu, D-135).** Kendi girisimimdi; T127
oncelikli oldugu icin epoch 3/40'ta durduruldu. On kayit yazili ve GECERLI:
`results/t128_on_kayit.md`. Yeniden baslatma:
`scripts/olcum/105_t122_ft_kosumu.py --kip ac --tohum 42`.
⚠ Yarim agirlik `codes/runs/segment/t122ac_tohum42/` altinda olabilir —
40 epoch tamamlanmadigi icin KIYASA SOKULMAZ.

**KAPI DURUMU (ustabasi kostu, bu kayit aninda):**
`codes/test_rota_sentetik.py` -> **15/15** ·
`unittest discover -s tests -q` -> **Ran 715 · OK**

**MIMARIN MASASINDA BEKLEYENLER:** T122 secim karari (D-237 -> D-239 -> D-240
birlikte okunur) · T126 denetimi (D-244) · T115 eksigi ve bagimliligi (D-247) ·
T124 sinir cumleleri (D-224) · D-233 kume yeniden uretimi · D-245 kuyruk-prompt
boslugu · D-248 (cati korlugu kaynak kalitesine bagli).

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
