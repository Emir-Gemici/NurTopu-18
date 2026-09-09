# 11 · GELİŞTİRME SÜRECİ VE AJANLAR — yazılım nasıl yazıldı, kim neyi onaylar

> Kaynaklar: `CLAUDE.md` · `AGENTS.md` · `CLAUDE2_WORKER.md` · `CODEX_WORKERS.md` · `REDTEAM.md` · `QWEN_CLEANUP.md` · `LOCAL_LLM.md` · `HANDOFF.md` · `DEVAM.md` ·
> `YAZILIM_BITIRME_PLANI_20260901.md` · `KARAR_PAKETI_20260901.md` · `MIMAR_DIREKTIFLERI_20260903.md` · `PUSH_TALIMATI.md` · `TASK_QUEUE.md` · `git log` ·
> `ozet/I_surec_ajanlar_gorevler.md` (T1…T211 tam listesi orada).
> Jüri "yapay zekâ araçlarını nasıl kullandınız, doğruluğunu nasıl güvence altına aldınız?" derse cevap bu dosyadadır. Dürüst çerçeve: **kodu büyük ölçüde
> yapay zekâ ajanları yazdı; insan kararları (model terfisi, eşik, donanım, saha) ve ölçüm disiplini süreci ayakta tuttu.**

---

## Seviye 1 — Bir cümle ve büyük resim

Proje 6 Mayıs'ta klasik bir öğrenci deposu olarak başladı (Mayıs–Temmuz 35 commit); 3 Ağustos'ta **yazılı bir anayasa** (`CLAUDE.md`) ve
**rol ayrımlı çok-ajanlı düzen** kuruldu: bir **mimar** (Claude 1) kod yazmaz, plan/denetim yapar; bir **başamele** (Claude 2) üretim kodunu yazar
ve bulut **Codex** ajanlarına iş böler; yerel **red team** (gpt-oss-120b) çürütür; yerel **Qwen** temizlik yapar. Ağustos'ta 418, Eylül'ün ilk haftasında
153 commit atıldı (toplam 606). Süreci ayakta tutan şey model değil **yordam**: genel kapı, tam süit, ön kayıt, mutasyon kontrolü, çürütücü turu,
yalnız-eklenen kanıt defteri, betiğe bağlı push kapısı. Anayasa bunu açıkça yazar: *"İki tarafın anlaşması kanıt değildir; hakem hâlâ ölçümdür."*

## Seviye 2 — Düzen nasıl işliyor

### 2.1 Anayasa (`CLAUDE.md`, 105 satır) — özet
- **Herkes için (1–6):** başkasının `[IN_PROGRESS]` görevine dokunma; iş alırken kilitle; bitince **test yaz, kapıyı gerçekten koş, gerçek çıktıyı yapıştır**;
  yalnız OpenCV/NumPy/heapq; insan işi yalnız mimar açar; kusur `REVIEW_LOG.md`'ye **kanıtıyla**.
- **Mimar için (7–12):** kod ameleliği yapmaz (istisna 20 Ağu'da kapandı, denetim borcu T114); "kota bol, **doğrulama kıt**": denetleyemeyeceğin kadar ajan
  koşturma; insan müdahalesi tekeli; tek muhatap kullanıcı (Yunus); alt sürü: Claude 2, Codex 1/2, Qwen, gpt-oss.
- **Değişmez teknik (13–18):** PC yorumlayıcısı tam yol (`python` Windows Store saplaması sessizce hiçbir şey yapmaz); genel kapı 15/15; serbest alan
  otoritedir; sözleşmeler `CONTRACTS.md`'den; commit izinsiz atılmaz, yazar Emir-Gemici, **AI atfı yok**; kullanıcının dosyaları silinmez.
- **Madde 19 (20 Ağu):** Claude 2 başamele; rol çift yönlü (aşağı iş, yukarı itiraz); "bir iş, onu yazanın onayıyla kapanmaz"; Codex prompt'larını Claude 2 yazar;
  **korelasyonlu kör nokta**: aynı modelin iki örneği birbirini denetlerse zayıf kanıt → hakem ölçüm.
- **§5 Push (28 Ağu):** serbest, ama yalnız genel kapı + tam süit yeşilken. 21–28 Ağu arası dondurulmuştu (uzak depo geride; `PUSH_TALIMATI.md`: 409 MB `.exe` +
  290 MB bundle GitHub 100 MB sınırına takılmıştı; 138 commit itildi, kalan 28 için filter-branch reçetesi).

### 2.2 Ajan kadrosu ve yazma matrisi (`AGENTS.md`)
| ajan | rol | yöneten | prompt |
|---|---|---|---|
| Claude 1 | başmimar, araştırmacı, denetçi | kullanıcı | `CLAUDE.md` |
| Claude 2 | başamele + mimarın denetçisi + Codex ustabaşısı | Claude 1 (iş) / kullanıcı (itiraz) | `CLAUDE2_WORKER.md` |
| Codex 1, 2 (bulut) | amele kodlayıcı | Claude 2 | `CODEX_WORKERS.md` |
| gpt-oss-120b (yerel) | red team, debugger, insan raporlayıcı | Claude 1 | `REDTEAM.md` |
| Qwen3-Coder-Next Q6_K (yerel) | temizlik/refactor (davranış değişmez) | Claude 1 | `QWEN_CLEANUP.md` |
| Gemini 3.6 Flash, Qwopus 35B | protokol dışı | kullanıcı manuel | — |
Yazma matrisi: anayasa/mimari/sözleşme belgeleri yalnız mimar; `TASK_QUEUE.md` mimar yazar, ameleler yalnız durum satırı; `REVIEW_LOG.md` herkes **ekler**;
kod dizinleri Claude 2/Codex/Qwen; kullanıcının belgeleri (`rapor/`, docx, pdf, jpeg) herkes salt okuma. Mutlak yasaklar: kullanıcı dosyası silmek,
defterde mevcut kaydı değiştirmek, başkasının kilidine dokunmak, izinsiz commit/push. Not: 3 Eylül'den itibaren mimar rolü Fable 5'e, amelelik Opus 5'e
geçti (`MIMAR_DIREKTIFLERI_20260903.md`); `AGENTS.md` tablosu ve push satırı bayat (tutarsızlık, kayıtlı).

### 2.3 Kilit, iş akışı, raporlama
Kilit birimi **görev**; durumlar `[ ]` · `[IN_PROGRESS: X]` · `[STATUS: PENDING_REDTEAM_REVIEW]` · `[STATUS: READY_FOR_REVIEW]` · `[x]`. "Kaydetmeden kod yazma."
Bayat kilit gerçekten yaşandı (Codex-1 token'ı biterken T14 zimmetli kaldı); yalnız kullanıcı/mimar açar, kayıt satırı eklenir. Ana zincir: mimar →
`TASK_QUEUE.md` → Codex → `READY_FOR_REVIEW` → mimar denetimi → `[x]` ya da `[ ]` + D-kaydı. Bulut kotası bitince Qwen → red team (model takası 1–3 dk;
iki yerel model aynı anda **yasak**: %99,3 doluluk, 3,1× yavaşlama, 77 bin hard fault/s ölçüldü). Raporlama: "Çalıştırılmayan bir kapı 'geçti' sayılmaz.
Kanıt = komut + gerçek çıktı + çıkış kodu." Her görevin altına `Yazan · Denetleyen · Kapı çıktısı` (gerekçe ölçülmüş: mimar bir turda yazarları yanlış
hatırladı, D-194; kendi başlattığı eğitimi unutup yeniden istedi, D-200).

### 2.4 İtiraz sistemi — 5 maddelik itiraz (`AGENTS.md` §8)
```
İTİRAZ · <hangi karar> · <dosya:satır veya D-no>
1. MİMARIN İDDİASI · 2. NEDEN YANLIŞ · 3. KANIT (koşulan komut + gerçek çıktı) · 4. ÖNERİ · 5. YANILIYORSAM (beni çürütecek ölçüm)
```
"5. madde zorunludur; kendini çürütecek ölçümü söyleyemeyen itiraz itiraz değil, tercihtir." Mimar ölçümü kendi koşar; tutarsa karar değişir ve D-kaydında
"kusur mimara ait" yazılır; kanıtsız itiraz reddedilir ama gerekçesi yazılır ("sessiz ret yok"); otorite argümanı iki yönde yasak. İlk kullanım D-199/D-200
(20 Ağu): mimarın istediği eğitim zaten koşulmuştu; itiraz kabul, bir GPU gecesi kurtuldu. Codex-2'nin görevi zorlamayıp itiraz yazdığı ve haklı çıktığı
üç olay (D-50/51/53) bu protokolün öncülüdür.

### 2.5 Üç kademe ve devredilmeyenler (`AGENTS.md` §9)
Claude 1 (karar, mimari, denetim, insan görevi) → Claude 2 (iş bölme, üretim kodu, Codex prompt'u) → Codex (parça iş). **Devredilmeyenler:** eşik
değiştirme/kapıya çevirme ("kör sıkılaştırma dört kez patladı"), üretim modeli terfisi ("seçim insanındır", D-133), mimari değişmezler, insan görevi açmak,
görev kapatma. **Denetim zinciri kapalı:** Codex yazar → Claude 2 denetler; Claude 2 yazar → mimar; mimar yazar → Claude 2.

### 2.6 Alt sürü prompt'ları — ortak disiplin ve tuzak listeleri
Ortak çekirdek: yorumlayıcı tam yolu, okuma sırası (CLAUDE → AGENTS → CONTRACTS → TASK_QUEUE → TEST_SPECS), kilit, "KAPIYI GERÇEKTEN KOŞ", AI atfı yasağı,
kota bitince `HANDOFF.md`. `CLAUDE2_WORKER.md` ölçülmüş tekrar eden kusur sınıfları: kopyalanmış mutlak eşik (5×), iki kopya yalnız biri zorlanıyor (4×),
ölçülemeyen "düştü" sayılıyor, kapı var ama koşmuyor, elle liste bayatlıyor (4×), yanlış kâhin, `python` saplaması. `CODEX_WORKERS.md` tuzakları: kapıyı
koşmadan onay, kardeş dosyayı unutmak, ACK'siz IKA_GO, tuval↔içerik karışması ("0 puan"); **ikiz dosya kontrolü** zorunlu. `QWEN_CLEANUP.md`: yalnız
davranışı koruyan dönüşümler; yeni algoritma/eşik/silme/commit yasak ("en pahalı hata: kimsenin fark etmediği sessiz davranış değişikliği").
`REDTEAM.md`: salt okuma; Faz A mekanik tarama K1–K6 (yasaklı bağımlılık **pozitif kontrolle**, monotonluk, sınıf-id, kâhin, araç üstünden rota, yutulan hata)
+ Faz B K7–K8 (kapı var ama açan yok; ikiz dosya); her bulgu dosya:satır + komut + çıktı; "muhtemelen/görünüyor ki" yasak; sonunda 3 maddelik HUMAN REPORT.

### 2.7 Workflow / worktree kullanımı
39 commit `worktree-wf_*` izi taşır (14 workflow); ilk 26 Ağu, son 7 Eyl. En yoğun günler 26 Ağu (89 commit: v36, K0–K7, T142–T157 paralel dalgalar) ve 2 Eyl
(72 commit: Faz A/B araçları). Tur büyüklükleri: "DÖRT FİLO TURU (198 ajan)" (20 Ağu), "Etiket dalga 4: 277 kare (56 kör amele + 7 denetçi, 5,0 M jeton)" (26 Ağu),
53 ajanlı şartname risk taraması (D-349'u buldu). Yan etkisi ölçülüp düzeltildi: worktree'de kapılar **ana depoyu** ölçüyordu → depo kökü `__file__`'dan
(T161/D-300). "Codex ana ağaca canlı yazıyor olabilir; birleştirmeden önce `git status` ve mtime" (D-412 dersi).

## Seviye 3 — Kalite güvence yordamları ve sayılar

| yordam | kural | kanıt |
|---|---|---|
| Genel kapı | her görevden sonra 15/15; iki kol (T156) | `codes/test_rota_sentetik.py` |
| Tam süit | 58 test (4 Ağu) → 655 (20 Ağu) → 793 (26) → 1559 (2 Eyl) → 1826 (3) → 2104 (4) → 2138 (7 Eyl) → 2204 (Jetson 9 Eyl); 188 test dosyası | `HANDOFF.md`, commit'ler, `results/push_kapisi/` |
| Ön kayıt | eşik sonuç görülmeden `ON_KAYIT`'a; gevşetilmez; 36 artefakt; ilk D-107 (14 Ağu) | `results/**/ON_KAYIT*.md` |
| Mutasyon | kusuru geri koy, test düşsün; rapor satırı `mutasyon: … → kaç test düştü`; aracın kendisi de denetlendi (D-370 CRLF) | `CLAUDE2_WORKER.md` |
| Çürütücü turu | bağımsız ajan iddiaları kırar; D-284 (10 kapatma adayının 8'i yıkıldı), D-383 (4 kusur), D-405 (1 KRİTİK + 14 ÖNEMLİ), D-411 (71 bulgu), D-421 (13 tıkayıcı) | `REVIEW_LOG.md` |
| Push kapısı | UDP 5005/5006 doluysa başlamaz; tam süit OK ∧ genel kapı GEÇTİ → push; kanıt `results/push_kapisi/<zaman>/` | `scripts/push_kapisi.py` (D-430) |
| Kanıt defteri | 441 `### D-` başlığı, 435 benzersiz + D-60b; yalnız eklenir; 80 kayıt "düzeltme/çürüdü/kendi hatam" ibareli; "KENDİ HATAM" 5 | `REVIEW_LOG.md` |
| HANDOFF | kota bitince: kapıyı koş, şablonu yaz, görevi `[IN_PROGRESS]` bırak; devralan "devredenin yazdığına güvenme, kapıyı kendin koş" | `HANDOFF.md`, `DEVAM.md` |
| Commit yazarı | Emir-Gemici 577, trs-1342 27; e-posta ezme kuralı (D-356: yanlış e-posta GitHub'da navitas26'ya bağlandı) | `git log` |

**Planlar:** `YAZILIM_BITIRME_PLANI_20260901.md` v2 — Faz A (1–4 Eyl: P1 MAVLink canlı, P2 SiK, P3 İKA sürücü, P4 runbook, P5 histerezis K=3, P8 yks_monitor,
P9a–e), Faz B (5–6 Eyl donanım), Faz C (7–20 Eyl provalar, mühür ~17–18, FDR). `KARAR_PAKETI_20260901.md` "ÖNER-BEKLE": K1–K9 kullanıcıya soruldu, beşi
uygulandı (D-385). 3 Eylül kapsam kararı: TEKNOFEST'e soru iletilmeyecek (fail-safe yorumlar kalıcı), DroidCam çekimi yok, **model döngüsü veri-bloklu: v36 son**.

**TASK_QUEUE sayıları:** 235 görev satırı; 156 `[x]`, 24 `[ ]`, 24 `READY_FOR_REVIEW` (çoğu fiilen kapandı, işaret bayat), 9 `HUMAN_COMPLETED`. Açık kritikler:
**T79** (koridor seçimi gürültüye kararsız; histerezis belirtiyi kapattı, kök Faz C), **T199** (üretece arena profili — yeni gerçek veri gerek), **T47** (v21 "geçilebilir"
anlamsız — veri-bloklu), **T149** (gerçek İKA sürücüsü, insan+mimar), **T211** (motor künyesi, insan). T16/T17/T109 satırları D-431 ile fiilen kapandı ama `[ ]` (bayat).

**Yerel LLM (`LOCAL_LLM.md`):** Core Ultra 9 275HX, 95 GiB RAM, RTX 5080 16 GiB; işçi Qwen3-Coder-Next Q6_K (61 GiB), red team gpt-oss-120b MXFP4 (59 GiB);
iki büyük model aynı anda yasak (3,1× yavaşlama); pagefile "10 kat" beklentisi gerçekte 1,8× ("Ben '~10 kat' demiştim, gerçek ~1,8"); harness dersleri: "görev
~6 saatte bitti, büyük kısmı model hızı değil harness tasarım hatalarımdı".

---

## Jüriye 30 saniyede

> "Yazılımı yapay zekâ ajanlarıyla yazdık ama kuralı yazılı bir anayasaya bağladık: mimar kod yazmaz, denetler; yazan kendi işini onaylayamaz;
> her görev sonunda kapı gerçekten koşulur ve gerçek çıktı yapıştırılır; eşikler sonuç görülmeden yazılır; her yeni test, kod bilerek bozularak
> sınanır; bağımsız çürütücü turları iddialarımızı kırmaya çalışır ve kırdıklarını sildirmez, üstünü çizdirir. Aynı modelin iki örneğinin
> birbirini onaylamasını kanıt saymıyoruz; hakem ölçüm. Bu düzen 436 kayıtlık bir kusur defteri ve 2 bin 200 testlik bir süit üretti."

## Kendini sına

1. Mimar kod yazar mı? İstisna ne zaman kapandı?
2. "Kota bol, doğrulama kıt" ne demek?
3. Denetim zinciri neden "kapalı"; aynı model sorunu nasıl ele alınıyor?
4. 5 maddelik itirazın 5. maddesi neden zorunlu? İlk kullanımı?
5. Devredilmeyen beş şey?
6. Push kuralı; neden betiğe bağlandı?
7. Bayat kilit olayı ve kuralı?
8. Ön kayıt, mutasyon, çürütücü: her biri için bir ölçülmüş "işe yaradı" örneği.
9. TASK_QUEUE'de açık kritikler?
10. Commit'lerde AI atfı neden yok; yazar kim?

<details><summary>Cevaplar</summary>

1. Hayır (madde 7); tıkayıcı işlerde insan onayıyla istisna 20 Ağustos'ta kapandı, denetim borcu T114. 2. Kısıt token değil doğrulama kapasitesi; denetleyemeyeceğin kadar ajan koşturma (madde 8). 3. Codex→Claude 2, Claude 2→mimar, mimar→Claude 2; aynı modelin iki örneğinin anlaşması zayıf kanıt (korelasyonlu kör nokta) → hakem ölçüm, ön kayıt, mutasyon. 4. Kendini çürütecek ölçümü söyleyemeyen itiraz tercihtir; D-199/D-200: istenen eğitim zaten koşulmuştu, bir GPU gecesi kurtuldu. 5. Eşik değiştirme, model terfisi, mimari değişmezler, insan görevi açma, görev kapatma. 6. Genel kapı + tam süit yeşilken; mimar iki kez kırmızıyken push etti (D-360, D-430) → `push_kapisi.py`. 7. Codex-1 token'ı biterken T14 zimmetli kaldı; kilidi yalnız kullanıcı/mimar açar, kayıt satırı eklenir. 8. Ön kayıt: 640 denemesi umut verici ara sayıya rağmen RED (D-377); mutasyon: yayın hattı bozulunca KOL 2 6/15 düştü, KOL 1 yeşil (T156); çürütücü: 308 ms soket sabiti (D-383). 9. T79, T199, T47, T149, T211. 10. Anayasa madde 17: yazar Emir-Gemici, Claude/Codex/Co-Authored-By yasak.
</details>

## Kaynaklar
`CLAUDE.md` · `AGENTS.md` · `CLAUDE2_WORKER.md` · `CODEX_WORKERS.md` · `REDTEAM.md` · `QWEN_CLEANUP.md` · `LOCAL_LLM.md` · `HANDOFF.md` · `YAZILIM_BITIRME_PLANI_20260901.md` ·
`KARAR_PAKETI_20260901.md` · `PUSH_TALIMATI.md` · `scripts/push_kapisi.py` · `ozet/I_surec_ajanlar_gorevler.md`.
