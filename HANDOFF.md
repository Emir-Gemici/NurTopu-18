# NAVITAS — DEVİR PROTOKOLÜ

## Devir 2026-09-11 · Onaylı birleşim tamam, tam süit yeşil

**Yetki:** kullanıcının "onay" mesajı, üç hazır dalın commit ve master'a
birleştirilmesi içindir. Push yapılmadı. Ara WIP geçmişi `--no-ff` ile korundu.

- Devir kayıtları: `307cb314`.
- T226-D2: dal commit'i `72e516f5`, master birleşimi `f80fec8d`.
- T228-D2: dal commit'i `6b9c862c`, master birleşimi `8d3c3fc2`.
- T221-D3: dal commit'i `fe63c69b`, master birleşimi `d02e3b63`.
- Birleşim doğrulaması düzenlemesi: `d812b1e2`. Atölye belgesindeki iki YKS
  satır atfı tazelendi; H1b testinde DPI açık kuruldu ve sabit uyku yerine
  gerçek çizim hazır koşulu beklendi. Ürün kodu/eşikler bu adımda değişmedi.

**Son gerçek kapı** (`O:\navitas`, test edilen HEAD `d812b1e2`):
`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1` ortamında
`O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B scripts/push_kapisi.py --kuru`
→ `Ran 2620 tests in 538.782s / OK (skipped=13)`;
`GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`;
`BIRLESIM_KAPI_EXIT=0`. Ham kanıt: `results/push_kapisi/20260911_161757/`.

İlk birleşim koşusu 3 başarısızlıkla kırmızıydı; ham kayıt
`results/push_kapisi/20260911_155724/` altında korunuyor. İki bayat atıf düzeldi;
ilk H1b sıfır-genişlik hatasının kesin tetikleyicisi saptanmadı. Son fikstür,
800 ms geciken çizimde geçti; Configure bağı kaldırılınca yine düştü.
Komutlar ve sınırlar: `results/birlesim_20260911/KANIT.md`, defter D-456.

**Durum:** üç görev `READY_FOR_REVIEW`; resmi bağımsız Claude denetimi bekliyor,
hiçbiri kendi üreticisinin onayıyla `[x]` yapılmadı. ArduPlane SITL ve fiziksel
MK15/Jetson ölçümü KOŞULMADI. Kullanıcının CAD, saha logu, rapor ve izlenmeyen
dosyaları korunuyor; T107 kilidine dokunulmadı.

**Devralanın ilk işi:** üç birleşimin bağımsız incelemesi; ardından aşağıdaki
önceki devirde listelenen **yedi kesinti işi**. O dallar bu birleşime alınmadı.
T236 sürüm/yaw kararı ile ATOLYE-2 kabul metni kararı hâlâ açık.

---

## Devir 2026-09-11 · Claude'un kesilen işi → Codex-1

**Yetki:** kullanıcının "claude un yarım bıraktığı işi devral" talebi. İlk devralma paketindeki
T226-D2, T228-D2, T221-D3 tamamlandı ve `READY_FOR_REVIEW` olarak kaydedildi. Resmi Claude
denetimi ve ana ağaca birleştirme yapılmadı. Kod/kanıt çalışma dallarında duruyor; ana ağaca
bu turda yalnız görev ve devir/inceleme kayıtları yazıldı. Commit/push yapılmadı.

**Tamamlanan üç çalışma ağacı** (ortak kök `O:\navitas\.claude\worktrees\`):

- `wf_61640005-665-1` / HEAD `73f62435`: T226-D2, önceki iki yarım değişiklik korunarak
  H2e/H4e/H2c ve semantik akış denetimi tamamlandı; d78/d83 ret çağrıları ve SVG tazelendi.
  `results/fdr_sprint_20260910/H9_MK15/t226/kapi_devralma_20260911_devam.md` tam kanıttır.
  YKS 233 test OK; MK15 39 test üç ardışık OK; yeni mutasyon 7/7; T202 gerçek tekrar 7/7.
- `wf_c1992b9f-d1a-1` / HEAD `5a597f99`: T228-D2, mevcut ürün/test WIP'i korundu;
  kanıt koşucularının hata çıkışı ve hedef assert sayımı tamamlandı. `H9_MK15/t228d/`
  altındaki `mutasyon_devralma_20260911.txt` ve `kapi_devralma_20260911*.txt` kanıttır.
  54/54 mutasyon; 14 kalıp 263 test (259 başarılı, 4 atlama); gerçek T202 tekrar 7/7.
- `wf_b9bb9db5-4d7-2` / HEAD `874ad16b`: T221-D3, yarım A18 ön kayıt sabitleri bağlandı;
  çizili/çelişkili hüküm ve ölçüt varyantları kilitlendi. `H8/T221/kapi_d3_20260911.md`
  ve `mutasyon_cikti_d3_20260911.txt` kanıttır. 43 ArduPlane + 16 Pixhawk test OK;
  38/38 mutasyon. ArduPlane SITL hâlâ KOŞULMADI/ÖLÇÜLEMEDİ.

Üç dalda da genel kapı gerçekten koşuldu: `O:\navitas-local-train\venv\Scripts\python.exe
-X utf8 -B codes/test_rota_sentetik.py` → `GENEL KAPI (madde 14): GECTI — kol1 15/15 ·
kol2 serit 15/15`, exit 0. Mutasyonlardan sonra asıl dosyaların bayt eşliği doğrulandı.
Tam depo süiti ve fiziksel MK15/Jetson ölçümü bu turda koşulmadı; platform/varlık atlamaları
kanıt dosyalarında açık. T226/T228'de ilk geniş koşudaki eksik varlık hataları korunuyor;
ana depodan yalnız eksik hedeflere gerçek dosyalar kopyalanarak testler tekrar geçirildi.
Ek disk: her dalda altı model 328.162.444 bayt; T226'da ayrıca 88 görsel 49.650.735 bayt.

**Kalan kesinti işleri — tamamlanmış sayılmayacak:** son `devam-3` journal'ı
`C:\Users\yunus\.claude-navitas\projects\O--navitas\3e104177-9b44-4ec7-a18f-1f32ed2c3f72\subagents\workflows\wf_cf0ac6ff-d81\journal.jsonl`
(10 Eylül 22:26:58; 7 amele kesilmiş, 3 denetçi RED). Eski HANDOFF bu turu içermiyordu.

- **T235-E/T236**, `wf_d450cb9f-ba7-9`, HEAD `9dfc5e15`: gerçek SITL sonucu var.
  `H1/t235/sitl/ozet.json`: ArduCopter **4.7.1** ön kayıt planı (yaw LOITER sonrası)
  yaw 0/499 **DÜŞTÜ**; konum/irtifa 499/499. LOITER öncesi karşı deney 500/500 GEÇTİ.
  Üretim hedefi 4.5.7; kaynak sürüm karşılaştırması yarım, üreteç hâlâ LOITER sonrası
  yazıyor. Bu ölçüm ArduPlane T221 değildir; kararı ve üretim sürümünü doğrulamadan bağlanmaz.
- **T235-B/D**, `wf_d450cb9f-ba7-8`, HEAD `c559c97c`: dört yarım dosya; `DUY_JSON`
  yok, `readme_metni` argümanları testle uyuşmuyor. Mevcut sentetik ölçüm A0/A1 DÜŞTÜ;
  nominal A0 16:9@40 m %98,33 < %99, K1 28/28. T235-C'ye geçilmez.
- **ATOLYE-2**, `wf_290ebb2b-6b8-1`, HEAD `4cd13ce2`: RED, 8/13 mutasyon kaçmış;
  CH5→Land eşanlamlıları, A12 akım/VIBE, A10 p50, A7 video kilitleri açık.
  Master ile TASARIM.md çatışması ve A12 ikincil koşulları kararı bekliyor.
- **T227-D**, `wf_61640005-665-2`, HEAD `86550f7f`: README/zamanlama JSON'u yarım;
  yeni CPU zamanlama ölçümü geçse de **FPS v2 yok**. Eski FPS DÜŞTÜ sonucu korunur.
- **AKIS-D2**, `wf_61640005-665-3`, HEAD `6e4aa437`: RED; son dosya commit'i yanlış
  taban seçebiliyor, altı ek mutant kaçıyor. Düğüm bazında köken denetimi gerekli.
- **T229-D2**, `wf_c1992b9f-d1a-2`, HEAD `08cd8ea8`: RED; lot eşanlamlıları,
  GECTI tipografisi ve video kopması hükmüyle beş yeni mutant kaçıyor.
- **T214A-D2**, `wf_b9bb9db5-4d7-1`, HEAD `664df054`: test docstring'ine 13 satır
  plan eklenmiş; vaat edilen kilitler uygulanmamış.

**Devralanın ilk işi:** üç hazır dalın yukarıdaki kanıtlarını ve `git diff`lerini resmi
bağımsız incelemeye almak; kendi üretimini kendi onayıyla `[x]` yapmamak. Sonraki üretim
öncesinde T236 sürüm/yaw bulgusunu ve ATOLYE-2 kabul metni kararını çözmek. Hazır dallar
birleştirilirse kesinti WIP commit'leri korunur (D-454); birleştirme sonrası tam depo süiti
ana varlıklarla gerçekten koşulur. Ana ağaçta kullanıcının CAD, saha logu, rapor ve izlenmeyen
dosyaları var; korunmuştur. T107'nin başka ajana ait kilidine dokunulmadı.

---

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

## GECE KOSUMU · 2026-08-21 (KAPANIS) · Claude 2 (Opus 5, basamele)

**KOSAN IS YOK — tum zincirler bitti, GPU bosta.**

**BITEN ISLER (hepsi push edildi):**
- **T127** temiz bolum zinciri — D-249. On kayit kurali 1 SAGLANDI: kirli
  bolum kazanani SISMEMIS (cati kacagi 0,043 · 67 karede red 0 · K0-K5 gecti).
  Temiz val'de egitim 18 epoch'ta durdu, en iyi epoch 27 -> 10.
- **T115** ustabasi denetimi — D-247 (DOGRU AMA EKSIK; kapiyi ustabasi kostu)
  + D-250 (13 satirin 10'u guvenle onarilabilir). Onarim Codex'in isi;
  genisletilmis kural prompt'u verildi. Bagimsizlik geregi ben onarmiyorum.
- **T129** — D-248: cati korlugu KAYNAK KALITESINE bagli (v34 videoda %96,
  ham fotografta %46). Siralama DEGISMIYOR.
- **T128 / T128-B** — D-251, D-253: `--tohum` VE `deterministic=False`
  ikisi de ATIL; egitim hatti bu recetede TAM TEKRARLANABILIR (bit-es).
  Kosum-ici varyans HALA olculmedi. 🔴 UCUNCU DENEME KOSULMADI (D-253):
  bu soruya ~8,6 saat GPU gitti; yama gerekiyorsa once 2-3 epochluk kucuk
  kosuyla dogrulanmali — karar mimarin.
- **D-252** (kendi hatam): T128'i kosmadan once defteri aramadim, ayni deney
  v31'de zaten yapilmisti. Kalici duzeltme: her on kaydin ilk satiri
  "daha once olculdu mu" aramasi olacak (T128-B'de uygulandi).
- **Kanit dosyasi**: `results/uretim_adayi_kanit_dosyasi.md` — secim kanitlari
  tek yerde (karar DEGIL, derleme).

**KAPI DURUMU (tum degisikliklerden SONRA kosuldu):**
`codes/test_rota_sentetik.py` -> 15/15 ·
`unittest discover -s tests -q` -> Ran 715 · OK · olcum aynasi 77 cift senkron

**DISKTE DURAN AMA COMMIT EDILMEYEN (runs/ gitignore'da):**
`codes/runs/segment/t122ac_tohum42` ve `t122ac_belirsiz` (113'er MB) —
t122ac ile BIT-ES olduklari olculdu; D-251/D-253'un kaniti olarak duruyorlar.
Silinmediler; gerekirse silinebilir (uretim degeri yok).

**MIMARIN MASASINDA:** T122/T127 secim karari (D-237 -> D-239 -> D-240 ->
D-249 birlikte okunur, derleme kanit dosyasinda) · T126 denetimi (D-244) ·
T115 devami (Codex'te) · T124 sinir cumleleri (D-224) · T118 adlandirma
(D-214) · D-233 kume yeniden uretimi · D-245 kuyruk boslugu · D-253 yama karari.

**INSANI BEKLEYEN (madde 9, mimarin acmasi gerek):** DJI cekimi — alan-disi
genelleme sorusu bunsuz KAPANMIYOR (T111/D-198 duvari).

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
