# I · NAVITAS — Geliştirme Süreci, Ajan Düzeni ve Görev Yönetimi (kanıtlı özet)

> **Okuyucu:** projeye geri dönen takım üyesi; jüriye "yazılımı nasıl geliştirdiniz, kalite güvencesi nasıl?" sorularını cevaplayacak kişi.
> **Kaynak depo:** `/home/n4vitas/proje/navitas_tam/navitas` (git, 606 commit; `git log --oneline | wc -l`).
> **Yöntem:** Her iddia dosya (+satır) ile bağlanmıştır. Belgeden çıkarılamayan her şey **DOĞRULANAMADI** olarak işaretlenmiştir. Hazırlanış tarihi: 2026-09-10.

---

## 1. Anayasa (`CLAUDE.md`) — kim ne yapabilir, neler değişmez

`CLAUDE.md` her oturumda bağlama yüklenen, 105 satırlık "proje anayasası"dır (`CLAUDE.md:1-3`). Belge haritası (`CLAUDE.md:7-20`) on bir dosyanın sahibini tanımlar: `CLAUDE.md`, `AGENTS.md`, `CONTRACTS.md`, `ARCHITECT_PLAN.md`, `RESEARCH_NOTES.md`, `TEST_SPECS.md`, `CLAUDE2_WORKER.md`, `CODEX_WORKERS.md`, `REDTEAM.md`, `QWEN_CLEANUP.md`, `LOCAL_LLM.md` yalnız **Claude 1 (mimar)** yazar; `TASK_QUEUE.md`'yi mimar yazar, ameleler yalnız durum satırını günceller; `REVIEW_LOG.md`'ye "herkes ekler, kimse silmez"; `HANDOFF.md`'yi devreden ajan doldurur.

### 1.1 Tüm yapay zekâlar için bağlayıcı maddeler (1–6, `CLAUDE.md:26-31`)

1. Başka bir AI'ın `[IN_PROGRESS]` görevine ya da tamamlanmış insan görevine dokunulmaz.
2. İş alınırken ilk boş `[ ]` görev seçilir, `[IN_PROGRESS: <Ad>]` yapılır ve kaydedilir.
3. Görev bitince **koda test yazılır, kapı gerçekten koşulur, gerçek çıktı göreve yapıştırılır**.
4. Yalnız **OpenCV, NumPy ve saf Python `heapq`**; **SciPy / scikit-image yasak** (madde 4).
5. Manuel veri/etiket/kablo işleri insan etiketiyle kuyruğa eklenir — bunu **yalnız Claude 1** yapar.
6. Hata veya mantık riski `REVIEW_LOG.md`'ye **kanıtıyla** eklenir; "kanıtsız bulgu yazılmaz".

### 1.2 Claude 1 (mimar) direktifi (7–12, `CLAUDE.md:37-48`)

- **Madde 7:** Mimar "kod ameleliği yapmaz"; mimari, araştırma, algoritma tasarımı, görev bölme, kod denetimi ve doğrulama onundur. Tek istisna (tüm ameleler kotadayken ve iş tıkayıcıyken, insan onayıyla) **2026-08-20'de kapatıldı**; istisna açıkken yazılan kodun denetim borcu **T114** ile kapatıldı (`CLAUDE.md:39-40`; T114 `TASK_QUEUE.md:5494` `[x]`).
- **Madde 8 — "Kota bol, DOĞRULAMA kıt":** 2026-08-20'de 200 $/20× Pro üyelik alındı; dinamik workflow ve çok ajanlı akış serbest, ama "kısıt token değil doğrulama kapasitesidir: koşturduğun her ajanın çıktısı kanıtla denetlenmek zorundadır, ve denetleyen sensin. Denetleyemeyeceğin kadar ajan koşturma" (`CLAUDE.md:41-43`).
- **Madde 9 — İnsan müdahalesi tekeli:** fiziki insan emeği isteyen işleri yalnız mimar, yalnız kullanıcıya, `TASK_QUEUE.md` içinde insan etiketiyle raporlar (`CLAUDE.md:44`).
- **Madde 10 — Tek muhatap:** kullanıcı (Yunus) tek doğrudan muhatap; Gemini 3.6 Flash ve Qwopus 35B kullanıcının manuel denetimindedir; Claude 2 istisnadır (`CLAUDE.md:45-46`).
- **Madde 11 — Alt sürü:** Claude 2 (başamele) · Codex 1, Codex 2 (bulut) · Qwen3-Coder-Next Q6_K (yerel işçi) · gpt-oss-120b (yerel red team). "Yerel iki model asla aynı anda yüklenmez" (`CLAUDE.md:47`).
- **Madde 12 — Mimari özgürlük:** mimar kalite/modülerlik/token için ilave belge ve protokol tasarlayabilir (`CLAUDE.md:48`).

### 1.3 Değişmez teknik kurallar (13–18, `CLAUDE.md:54-62`)

| Madde | Kural | Kaynak |
|---|---|---|
| 13 | **Yorumlayıcı** `O:\navitas-local-train\venv\Scripts\python.exe`. Çıplak `python` Windows Store saplamasıdır: "sessizce hiçbir şey yapmaz, hata bile vermez" | `CLAUDE.md:54-55` |
| 14 | **Genel kapı:** her görevden sonra `codes/test_rota_sentetik.py` → **15/15**; düşerse görev geri alınır, nedeni `REVIEW_LOG.md`'ye yazılır | `CLAUDE.md:56-57` |
| 15 | **Mimari değişmez:** "Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR." `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)`; serbest alanı **büyüten** hiçbir işlem eklenmez | `CLAUDE.md:58-59` |
| 16 | **Sözleşmeler `CONTRACTS.md`'den okunur**; sınıf id, mesaj tipi, koordinat çerçevesi için koda çıplak sabit yazılmaz | `CLAUDE.md:60` |
| 17 | **Commit** izinsiz atılmaz; yazar **Emir-Gemici**; "Hiçbir AI atfı eklenmez (Claude, Codex, Co-Authored-By, 'Generated with')" | `CLAUDE.md:61` |
| 18 | **Kullanıcının dosyaları silinmez**; `doc/` klasörü repoda tutulmaz | `CLAUDE.md:62` |

**Not:** `CLAUDE.md`'de madde 16 sözleşme maddesidir; "depo kökü" konusu ayrı bir görevde (T161, D-300, `TASK_QUEUE.md:6481`) çözülmüştür. Madde 18 sahada da uygulandı: 6 Eylül'de operatör eski 56 GB yedeğin silinmesini istedi, mimar "CLAUDE.md md. 18 gereği silmedi — karar Yunus'un" (`DEVAM.md:20-21`).

### 1.4 Yeni çağ ve korelasyonlu kör nokta (madde 19, `CLAUDE.md:68-77`)

2026-08-20 kullanıcı kararıyla **Claude 2 başamele** oldu; model aynı gün Fable 5'ten Opus 5'e alındı, "ROL DEĞİŞMEDİ". Rol çift yönlüdür: **aşağı** (üretim kodu, kuyruktan iş alır, kapıyı gerçekten koşar; denetimi mimar yapar) ve **yukarı** (mimarın kararını sorgulayabilir, `AGENTS.md §8`). **Bağımsızlık kuralı:** "Bir iş, onu yazanın onayıyla kapanmaz." **Yan (ustabaşılık):** Codex 1/2'ye görev prompt'larını artık Claude 2 yazar; zincir "mimar → başamele → amele"; "Yetki devri KARAR devri DEĞİLDİR" (`CLAUDE.md:72-74`).

**Korelasyonlu kör nokta uyarısı (`CLAUDE.md:75-77`):** "Claude 2 artık seninle aynı model. Aynı modelin iki örneği aynı kör noktalara sahiptir; birbirini denetlemeleri, model-kaynaklı hatalarda zayıf kanıttır. İki tarafın ANLAŞMASI kanıt değildir. Hakem hâlâ ölçümdür: koşulan komut, gerçek çıktı, ön kayıt, mutasyon kontrolü." Aynı paragraf, yordamın model farkından bağımsız çalıştığının üç ölçülmüş örneğini verir: ham çıktının repoda durması bir kez yanlış hükmü engelledi (D-209, `REVIEW_LOG.md:16904`), ön kayıt bir kez eşik gevşetmesini engelledi (D-225, `REVIEW_LOG.md:17501`), 5 maddelik itiraz kalıbı bir GPU gecesi kurtardı (D-200, `REVIEW_LOG.md:16554`).

### 1.5 Push kuralları — dondurma ve kaldırılması (`CLAUDE.md:81-105`)

- **2026-08-21 → 2026-08-28:** `git push` **yasaktı**; uzak depo bilerek geride tutuldu, tek kopya `O:` diskindeydi (`CLAUDE.md:99-104`, ayrıntı-katlanmış blok). Commit 2026-08-21: "PUSH DONDURULDU (kullanıcı emri)".
- **2026-08-28:** kullanıcı emriyle kalktı: "push artık istediğin zaman yapabilirsin" (`CLAUDE.md:83-85`). Tablo: `git add/commit` devam, `git push` serbest (izin sorulmaz), `git pull/fetch` serbest (`CLAUDE.md:87-91`). Donma `e249b1b..dd73e0f` tek seferde itilerek kapandı (`CLAUDE.md:102-103`).
- **Serbestliğin sınırı:** "itilen şey kapıdan geçmiş olmalıdır — `codes/test_rota_sentetik.py` 15/15 **ve** tam suit. Kapı düşmüşken push yapılmaz" (`CLAUDE.md:93-95`). Drive yedeği (`yedek_drive.sh`) sürer (`CLAUDE.md:97`).
- **Push'un teknik engeli (`PUSH_TALIMATI.md`):** `1323fbb` commit'inde `git add -A` iki dev dosyayı (409 MB `.exe`, 290 MB `navitas_depo.bundle`) süpürmüştü; GitHub 100 MB sınırı (`PUSH_TALIMATI.md:9-27`). Çözüm: 138 commit güvenle itildi (`PUSH_TALIMATI.md:33-42`), kalan 28 için `filter-branch` reçetesi ve güvenlik dalı `yedek_push_oncesi_20260828` (`PUSH_TALIMATI.md:48-91`). Claude 2 bunu kendisi yapmadı: "git filter-branch ve git push bu oturumda izin katmanınca engellendi ... kararı insana bırakıyor" (`PUSH_TALIMATI.md:99-104`).
- **Uyumsuzluk notu:** `AGENTS.md:62-63` hâlâ "git push — 2026-08-21'den beri DONDURULDU" der; `CLAUDE.md §5` bunu 2026-08-28'de kaldırmıştır. `AGENTS.md`'deki satır güncellenmemiş görünüyor (belge bayatlığı; DOĞRULANAMADI: bilinçli mi bırakıldı).

---

## 2. Ajan düzeni — roller, protokol, yazma matrisi, kilit, itiraz, workflow

### 2.1 Sürü kadrosu (`AGENTS.md:10-26`)

| # | Ajan | Rol | Yöneten | Sistem prompt'u |
|---|---|---|---|---|
| 1 | Claude 1 (Opus 5) | Başmimar, araştırmacı, denetçi | Kullanıcı | `CLAUDE.md` |
| 1b | Claude 2 (Opus 5; 2026-08-20'de Fable 5'ten geçirildi) | Başamele + mimarın denetçisi + Codex'in ustabaşısı | Claude 1 (iş) · Kullanıcı (itiraz) | `CLAUDE2_WORKER.md` |
| 2–3 | Codex 1, Codex 2 (bulut) | Amele kodlayıcı, eş yetkili yedek | Claude 2 | `CODEX_WORKERS.md` |
| 4 | gpt-oss-120b MXFP4 (yerel) | Red team, debugger, insan raporlayıcı | Claude 1 | `REDTEAM.md` |
| 5 | Qwen3-Coder-Next Q6_K (yerel) | Temizlik ve refactoring | Claude 1 | `QWEN_CLEANUP.md` |
| 7–8 | Gemini 3.6 Flash, Qwopus 35B | — | Kullanıcı (manuel) | protokol dışı |

`SYSTEM_STATE.md` (Ağustos 2026) o dönemin geçici kipini anlatır: "1 Cloud Claude + 1 Cloud Codex + Local Swarm Mode" ve kotalar yenilenince "8-AI Sürü Mimarisine geri dön" talimatı (`SYSTEM_STATE.md:3-10`). Red team kayıtlarının eski kısmı MiniMax M2.5 imzalıdır; 2026-08-06'dan sonrası gpt-oss-120b (`SYSTEM_STATE.md:16`; `REDTEAM.md:3-4`).

**Not:** `MIMAR_DIREKTIFLERI_20260903.md:3-4` ve `FAZ_B_GUN_PLANI.md:3` belgelerinde "Yazan: Claude 2 — Fable 5, mimar / Fable 5.1, mimar" ifadesi geçer; yani 3 Eylül itibarıyla mimar rolü Fable 5'e, amelelik Opus 5'e geçmiştir ("Amelelik Opus 5'te yürür"; `YAZILIM_BITIRME_PLANI_20260901.md:195-196`: "Model geçişi: Faz A/C ameleliği Opus 5; ön kayıt/eşik/sözleşme/dondurma kararlarında kullanıcıya 'Fable 5'e al' denir"). `AGENTS.md` kadro tablosu bu son takası yansıtmıyor (belge bayatlığı).

### 2.2 Dosya yazma matrisi (`AGENTS.md:30-45`)

`Y` = yazabilir, `E` = yalnız ekler, `D` = yalnız durum satırı, `—` = salt okuma:

- Anayasa/mimari/sözleşme belgeleri ve alt-sürü prompt'ları: yalnız Claude 1 **Y**, diğer herkes **—**.
- `TASK_QUEUE.md`: Claude 1 **Y**; Claude 2, Codex, Qwen **D**; red team **—**.
- `REVIEW_LOG.md`: herkes **E** (yalnız ekleme).
- `HANDOFF.md`: herkes **Y**.
- `codes/ comms/ simulation/ scripts/ drone/ tests/`: Claude 2, Codex, Qwen **Y**; Claude 1 için madde 7 istisnası "2026-08-20 KAPALI"; red team **—**.
- `models/ dataset/ data/ results/`: Claude 2 ve Codex **Y**.
- Kullanıcının belgeleri (`rapor/`, `*.docx`, `*.pdf`, `*.jpeg`, `*.mp4`): herkes **—**.

**Geçici rol devri (`AGENTS.md:47-59`):** kullanıcı bir ajana başkasının rolünü görev bazında verebilir; "Devralan kendi ürettiği işi kendi denetleyemez"; red team amele rolünde kod yazarsa `PENDING_REDTEAM_REVIEW`'a girmez, doğrudan mimara gider ve "aynı model o kodu ileride red team olarak da denetleyemez — bağımsızlık kalıcı olarak kaybolur". Kayıt biçimi: `- **Rol devri:** <tarih> · <ajan> ← <rol> · sebep · denetim: <kim>`.

**Mutlak yasaklar (`AGENTS.md:61-67`):** kullanıcı dosyası silmek; `REVIEW_LOG.md`'deki mevcut kaydı değiştirmek/silmek; başkasının `[IN_PROGRESS]` görevine dokunmak; izinsiz commit/push.

### 2.3 Kilit protokolü (`AGENTS.md:71-100`)

"Kilit birimi görevdir, dosya değil." Durum işaretleri: `[ ]` serbest · `[IN_PROGRESS: <AI>]` kilitli · `[STATUS: PENDING_REDTEAM_REVIEW]` Qwen çıktısı red team bekliyor · `[STATUS: READY_FOR_REVIEW]` mimar denetimi bekliyor · `[x]` kapatıldı (`AGENTS.md:75-81`). İş alma: ilk `[ ]` görevi seç, hemen kaydet, "kaydetmeden kod yazma" (`AGENTS.md:84-86`). Çakışma: aynı dosyaya dokunan iki görev ardışık dizilir (`AGENTS.md:89-91`). **Bayat kilit:** "Bu gerçekten yaşandı (Codex-1 token'ı biterken T14 zimmetli kaldı)"; kilidi yalnız kullanıcı veya onun onayıyla mimar açar, altına `Kilit serbest bırakıldı: <tarih> · önceki sahip · sebep · yarım kalan iş` satırı eklenir (`AGENTS.md:93-100`; olay `HANDOFF.md:109-116` ve `HANDOFF.md:124-157`).

### 2.4 İş akışı zinciri ve raporlama (`AGENTS.md:117-182`)

Ana zincir: Claude 1 → `TASK_QUEUE.md` → Codex 1/2 → `READY_FOR_REVIEW` → mimar denetimi → `[x]` veya `[ ]` + `REVIEW_LOG.md` (`AGENTS.md:119-129`). Bulut kotası bitince: Qwen3-Coder → `PENDING_REDTEAM_REVIEW` → **model takası** → red team onay/ret (`AGENTS.md:132-150`); "Qwen doğrudan master'a iş veremez." Takas 1–3 dk sürdüğü için iş toplu yapılır; eşzamanlı yükleme "%99,3 doluluk, 3,1× yavaşlama, 77 bin hard fault/s" ölçümüyle yasak (`AGENTS.md:152-156`, `LOCAL_LLM.md:71-79`).

Raporlama sözleşmesi (`AGENTS.md:173-182`): Codex → `TASK_QUEUE.md`'ye kapı komutu + gerçek çıktı + çıkış kodu; red team → `REVIEW_LOG.md`'ye kanıtlı bulgu + 3 maddelik HUMAN REPORT; Qwen → değişiklik özeti + 15/15 kanıtı; Claude 1 → kullanıcıya "hangi kapıların gerçekten koşulduğu". **Ortak kural:** "Çalıştırılmayan bir kapı 'geçti' sayılmaz. Kanıt = komut + gerçek çıktı + çıkış kodu."

### 2.5 İtiraz sistemi — 5 maddelik itiraz (`AGENTS.md:186-224`)

Yalnız Claude 2 kullanır; diğer ameleler kusuru `REVIEW_LOG.md`'ye yazar. Mimarın bir kararı (K-kaydı, görev tanımı, ön kayıt ölçütü, kapı eşiği) yanlış görünüyorsa, **kod yazmadan önce** şu kalıp üretilir:

```
İTİRAZ · <hangi karar> · <dosya:satır veya D-numarası>
1. MİMARIN İDDİASI  : <tek cümle, mimarın kendi sözleriyle>
2. NEDEN YANLIŞ     : <tek cümle>
3. KANIT            : koşulan komut + GERÇEK çıktı  (veya alıntılanan kod)
4. ÖNERİ            : <ne yapılmalı>
5. YANILIYORSAM     : <bu itirazı çürütecek ölçüm ne olurdu>
```

"5. madde zorunludur. Kendini çürütecek ölçümü söyleyemeyen itiraz itiraz değil, tercihtir" (`AGENTS.md:203`). Mimarın işleyişi bağlayıcıdır (`AGENTS.md:205-211`): kanıt ölçüm içeriyorsa mimar ölçümü kendi koşar, tutarsa karar değişir ve D-kaydında "kusurun mimara ait olduğu" açıkça yazılır; kanıtsız itiraz reddedilir ama "reddin gerekçesi yazılır. Sessiz ret yoktur"; haklı ama kapsam dışı itiraz kuyruğa görev olur. "Otorite argümanı iki yönde de yasaktır" (`AGENTS.md:213-214`). İtiraz kabul edilse de reddedilse de `REVIEW_LOG.md`'ye yazılır: "Kaydedilmeyen itiraz tekrar eder" (`AGENTS.md:221-224`).

**Kullanım kanıtı:** protokolün ilk kullanımı D-199/D-200 (2026-08-20): "MIMAR HUKMU · ITIRAZ KABUL (protokolün ILK kullanımı) — T54 adım 4 ZATEN koşulmuştu ve koşumu BEN başlatmıştım" (`REVIEW_LOG.md:16554`). `REVIEW_LOG.md`'de başlığında "ITIRAZ" geçen 2 D-kaydı var (D-199 `REVIEW_LOG.md:16417`, D-200). Bundan fazla resmi itiraz DOĞRULANAMADI.

### 2.6 Üç kademeli hiyerarşi (`AGENTS.md:228-284`)

Claude 1 (karar · mimari · denetim · insan görevi) → Claude 2 (iş bölme · üretim kodu · Codex'e prompt) → Codex 1/2 (parça iş). **9.2 — devredilmeyenler:** eşik değiştirme/kapıya çevirme ("bu projede kör sıkılaştırma dört kez patladı"), üretim modeli terfisi ("seçim insanındır, D-133"), mimari değişmezler, insan görevi açmak, görev kapatma (`AGENTS.md:245-257`). **9.3 — denetim zinciri kapalıdır:** "Codex yazar → Fable 5 denetler; Fable 5 yazar → mimar denetler; mimar yazar → Fable 5 denetler" (`AGENTS.md:259-268`). **9.5 — defter zorunluluğu:** her görevin altına `Yazan · Denetleyen · Kapı çıktısı` satırı; gerekçe ölçülmüş: "mimar bir turda görev yazarlarını yanlış hatırladı (D-194 §1) ve iki gün önce kendi koşturduğu eğitimi unutup yeniden istedi (D-200 §2)" (`AGENTS.md:277-284`).

Codex prompt'larının başamele tarafından yazıldığının izi beş dosyadır ("Veren: Claude 2 / Fable 5 (ustabaşı)"): `CODEX_PROMPTLARI_20260820.md` (T115, T107, T120), `..._20260821.md` (D-226 sınıf taraması, T132), `..._20260829.md` (A1 hakem rotası, B3 yaw/kadraj), `..._20260831.md` ve `..._20260901.md` (A2 `karar_yas`, B2 10 dk bütçe/T15); ayrıca `CODEX_GOREV_YKS_FDA.md` (FDA görev kipi).

### 2.7 Alt sürü sistem prompt'ları — ortak disiplin

`CLAUDE2_WORKER.md`, `CODEX_WORKERS.md`, `REDTEAM.md`, `QWEN_CLEANUP.md` "yapıştırılabilir prompt" bloğu içerir. Ortak çekirdek: yorumlayıcı tam yolu, okuma sırası (CLAUDE → AGENTS → CONTRACTS → TASK_QUEUE → TEST_SPECS), iş alma/kilit, "KAPIYI GERÇEKTEN KOŞ — EN ÖNEMLİ KURAL", AI atfı yasağı, kotaya yaklaşınca `HANDOFF.md`. `.codexrules` bu disiplinin dört maddelik kısa hatırlatıcısıdır; çelişkide `CODEX_WORKERS.md` geçerlidir (`.codexrules:3-16`).

Ayırt edici parçalar:
- `CLAUDE2_WORKER.md:125-142` "ölçülmüş tekrar eden kusur sınıfları": kopyalanmış mutlak eşik (5×), iki kopya yalnız biri zorlanıyor (4×), ölçülemeyen "düştü" sayılıyor, kapı var ama koşmuyor (D-170), elle yazılmış liste bayatlıyor (4×), yanlış kâhin, `python` saplaması (≥2×).
- `CODEX_WORKERS.md:120-136` tuzak tablosu: kapıyı koşmadan onaylamak; kardeş dosyayı unutmak ("aynı girdide biri exit 1 diğeri exit 0"); kapı üretimi kilitlemek; ACK'siz `IKA_GO`; tuval↔içerik karışması ("0 puan"). "İKİZ DOSYA KONTROLÜ" zorunlu (`CODEX_WORKERS.md:69-71`).
- `QWEN_CLEANUP.md:43-57`: yalnız davranışı koruyan dönüşümler; yeni algoritma/kapı, eşik değeri, dosya silme, commit/push **yasak**. Gerekçe: "denetim kapasitesi en düşükken" çalışır; "en pahalı hata sınıfı: kimsenin fark etmediği sessiz davranış değişikliği" (`QWEN_CLEANUP.md:34-41`).

### 2.8 Workflow ve worktree kullanımı

Commit geçmişinde `worktree-wf_*` izi taşıyan **39 commit** var (`git log --format=%s | grep -c worktree-wf_`); 14 ayrı workflow kimliği. İlk iz 2026-08-26 ("Birleştir: worktree-wf_b3397c57-d76-37 (mimar vekili onarımı, worktree izolasyonu)"), sonuncusu 2026-09-07 ("T211 birleştirme ... worktree-wf_a26f19cd-919-5"). En yoğun günler: 26 Ağustos (wf_0c06347c, wf_46c3db35, wf_b3397c57 vb. — aynı gün 89 commit) ve 2 Eylül (wf_2d055c88, wf_80327e1a, wf_315c64ce, wf_83dc8b89 — 72 commit, "Faz B Görev A/C/D/N/P" paralel dalları). 7 Eylül gecesi FDR G-serisi (G0b, G1, G1b, G2, G4, G5, G6) `wf_604a2e17` altında ayrı worktree'lerde üretilip birleştirildi.

Yan etkisi ölçülüp düzeltildi: T161 "worktree'de kapılar ANA DEPOYU ölçüyordu — depo kökü artık `__file__`den türetiliyor" (D-300, commit 2026-08-27). Bazı workflow'lar oturumla birlikte durdu (commit 2026-09-03 "workflow durumu ÖLÇÜLDÜ"). Bitirme planı v2'nin dayanağı "3 kollu workflow analizi (wf_5c5e6d65)" (`YAZILIM_BITIRME_PLANI_20260901.md:6-9`). Tur büyüklükleri commit başlıklarında: "DÖRT FİLO TURU (198 ajan)" (2026-08-20), "Etiket dalga 4: 277 kare (56 kör amele + 7 denetçi, 5,0 M jeton)" (2026-08-26). Uyarı: "Codex ana ağaca canlı yazıyor olabilir; birleştirmeden önce `git status` ve mtime (D-412 dersi)" (`DEVAM.md:86-87`).

---

## 3. Kalite güvence yordamları

### 3.1 Genel kapı ve tam süit

- **Genel kapı:** `codes/test_rota_sentetik.py` → 15/15 (`CLAUDE.md:56-57`; `TASK_QUEUE.md:14-16`). 2026-08-26'da T156 ile kapıya "ÜRETİM yolu (analyze_path) kolu" eklendi: "genel kapı (madde 14) artık ÜRETİM yolunu da zorluyor" (commit 2026-08-26; `TASK_QUEUE.md:6471` T156 `[x]`).
- **Tam süit:** `python -m unittest discover -s tests -q` (`CLAUDE2_WORKER.md:74`). Büyüme izi: 58 test (2026-08-04, `HANDOFF.md:143-144`) → 655 (D-209, 2026-08-20) → 715 (`HANDOFF.md:47`, 2026-08-21) → 793 (T143, 2026-08-26) → 1559 (2 Eylül gecesi, `YAZILIM_BITIRME_PLANI_20260901.md:166`) → 1826 (3 Eylül, `...:167`) → **2104 OK** ("Cumartesi sabahı doğrulama koşumu: tam suit 2104 OK", commit 2026-09-04). `tests/` dizininde 188 `.py` dosyası var (`ls tests/*.py | wc -l`).
- **Ortam tuzağı:** `PYTHONIOENCODING=utf-8` ve uzun koşumlarda `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` ("bu değişken olmadan uzun koşumlar konsol kapanınca İZSİZ oluyor — ölçüldü"; `CLAUDE2_WORKER.md:75-77`, `ARCHITECT_PLAN.md:458` R6).

### 3.2 Ön kayıt (D-107)

"ÖLÇÜM YAPIYORSAN: ÖN KAYIT ZORUNLU (D-107). Kabul ölçütünü SONUCU GÖRMEDEN önce yaz (`results/<görev>_on_kayit.md`). Sonucu gördükten sonra ölçüt GEVŞETİLMEZ. Gevşetmen gerekiyorsa bu bir bulgudur, ayrı yazılır" (`CLAUDE2_WORKER.md:86-89`). Kural, mimarın kendi hatalarından türetildi: "Bu projede tekrarlanan hata ölçütü SAYIYI GÖRDÜKTEN SONRA yorumlamak oldu: D-85'te alt kümenin azamisine eşik oturttum (D-86 çürüttü), D-90'da tanıma bağlı bir ölçütle %92,7 rapor etmek üzereydim, D-104'te kapıyı yanlış modelle ölçtürdüm" (D-107, `REVIEW_LOG.md:7242-7250`). Kanıt dosyaları: `results/t121_on_kayit.md`, `t122_`, `t127_`, `t128_`, `t128b_on_kayit.md` (6 dosya, `ls results | grep on_kayit`); `REVIEW_LOG.md`'de başlığında "ÖN KAYIT" geçen 17 D-kaydı. D-252 dersiyle ön kaydın ilk satırı "daha önce ölçüldü mü" araması oldu (`HANDOFF.md:39-41`).

### 3.3 Mutasyon kontrolü

"YENİ KAPI EKLİYORSAN: MUTASYON KONTROLÜ ZORUNLU. Yeni bir test yazdıysan, KUSURU GERİ KOY ve testin GERÇEKTEN düştüğünü göster. Düşmüyorsa test bir şey korumuyordur" (`CLAUDE2_WORKER.md:79-84`); raporda `mutasyon: <ne bozuldum> -> <kaç test düştü>` ve `geri alındı: evet` satırları zorunlu. Gerekçe D-170: `test_monotonluk.py` `codes/` altındaydı, test keşfi görmüyordu — "test VARDI ama hiç koşmuyordu" (`REVIEW_LOG.md:13503`). `REVIEW_LOG.md`'de "mutasyon" 248 kez geçer. Mutasyon aracının kendisi de denetlendi: D-370 "MUTASYON ÖLÇÜM BETİĞİ CRLF'e TAKILIYORDU — M2' hiç uygulanmadan 'ölçüldü' sayılıyordu" (commit 2026-08-31); D-405 hub sertleştirmesi "24/25 + 14/14 mutant" ile kapandı (`YAZILIM_BITIRME_PLANI_20260901.md:167`).

### 3.4 Çürütücü (red team) turu

İki katman vardır. **(a) Yerel red team** (`REDTEAM.md`): gpt-oss-120b, salt okuma, yalnız `REVIEW_LOG.md`'nin sonuna ekler (`REDTEAM.md:5-6`). Prompt iki fazlıdır: **Faz A mekanik tarama K1–K6** (yasaklı bağımlılık — pozitif kontrol zorunlu; monotonluk ihlali; sınıf-id sözleşmesi; kâhin uyumsuzluğu; araç üstünden geçen rota; sessiz yutulan hata/ölü kod) ve **Faz B derin çıkarım K7–K8** (kapı var ama açan yok; ikiz dosya) (`REDTEAM.md:153-293`). Gerekçe ölçülmüş: "T3–T13 denetiminde çıkan üç KRİTİK bulgunun ikisi tam olarak bu iki kontrolden geldi — D-03 (iniş kapısı var, sinyali üreten yok → P_görev = 0) ve D-01 (ikiz dosya, aynı girdide zıt çıkış kodu)" (`REDTEAM.md:46-49`). Çıktı sözleşmesi: her bulgu `dosya:satır` + gerçek satır + koşulan komut + gerçek çıktı; veremiyorsa "DOĞRULANAMADI: <ne>"; "muhtemelen/görünüyor ki/olabilir" yasak (`REDTEAM.md:89-97`). Raporun sonunda zorunlu **HUMAN REPORT** (3 madde: kritik hata var mı, kilitlenen yer, eylem önerisi) — "Rapor bu üç madde olmadan teslim edilmiş sayılmaz" (`REDTEAM.md:321-345`). Prompt'un kendi tuzakları da ölçülüp yazıldı: BRE/ERE `|` alternasyonu yüzünden K7 denetiminin tamamı bir kez boşa gitti (`REDTEAM.md:137-147`); yasak-paket grep'inin `\|` biçimi "HER ZAMAN 0 döndürür", pozitif kontrolle düzeltildi (`REDTEAM.md:172-178`).

**(b) Bulut "çürütücü" turları:** Ağustos sonundan itibaren "çürütücü" adıyla anılan bağımsız ajan turları (`TASK_QUEUE.md`'de 51, `REVIEW_LOG.md`'de 53 geçiş). Örnekler: "T133 TRİYAJ: 39 görev kanıtla ayrıldı ve ÇÜRÜTÜCÜ 35 'KAPANMALI' verdiktinin 17'sini YIKTI" (2026-08-21); "D-383: çürütücü hasadı — 4 gerçek kusur" (2026-09-01); "D-405 ÇÜRÜTÜCÜ: 5 mercek, 1 KRİTİK (mühür özeti CRLF'ye bağlıydı), 14 ÖNEMLİ" (`YAZILIM_BITIRME_PLANI_20260901.md:167`); "'Cumartesiye hazır mıyız' ÇÜRÜTME turu: 13 tıkayıcı bulgu — runbook komutu ÖLÜYDÜ" (2026-09-04). Çürütücü mimarın kendi aracını da vurdu (D-415, `REVIEW_LOG.md:28664`). Mimari planın kusur bölümü de böyle yazıldı: "bağımsız çürütme ajanlarıyla 11 kusur ayakta kaldı, 0 tanesi çürütüldü" (`ARCHITECT_PLAN.md:398-399`).

### 3.5 `push_kapisi` — kural insana değil betiğe bağlandı

7 Eylül ~02:00'de mimar süit `FAILED (failures=1)` iken push etti (D-430, `REVIEW_LOG.md:30155`); daha önce 2026-08-28'de aynı hata (D-360, `REVIEW_LOG.md:25266`: "suit komutunu commit/push ile aynı zincirde koştum"). Çözüm `scripts/push_kapisi.py` (`scripts/push_kapisi.py:1-19`): (1) UDP 5005/5006 doluysa (canlı `yks_gui`/`ika_nav`) hiç başlamaz — "'kırmızı ama ortam' yorumu yapılmaz, beklenir"; (2) tam süit son satırı `OK` ve çıkış 0; (3) genel kapı `GENEL KAPI (madde 14): GECTI`; (4) ikisi de yeşilse `git push origin master`, değilse çıkış 3; çıktılar `results/push_kapisi/<zaman>/` altına kanıt olarak yazılır; `--kuru` yalnız ölçer. Süit ve kapı ard arda koşar: "paralel koşum mutasyon testleriyle sahte IndentationError üretir — 4 Eylül'de ölçüldü" (D-432, `REVIEW_LOG.md:30170-30178`). "Bundan sonra mimarın elle `git push` yazması yordam dışıdır." Aynı gün "push_kapisi: GENEL KAPI hükmü son satırda değil her yerde aranır" düzeltmesi girdi (commit 2026-09-07). Commit yazarı kuralı da bir hatadan sonra sertleşti: D-356 "commit'lerde YANLIŞ E-POSTA kullandım — GitHub onları navitas26'ya bağladı" (`REVIEW_LOG.md:25094`) → "`git -c user.email=...` ile EZME" (`CLAUDE2_WORKER.md:27-29`). Git yazar dağılımı: Emir-Gemici 577, trs-1342 27, trs 1, navitas-colab 1 (`git log --format=%an | sort | uniq -c`).

### 3.6 REVIEW_LOG kültürü

`REVIEW_LOG.md` 1,72 MB; 441 `### D-` başlığı, 296 bölüm; son kayıt D-436 (7 Eylül). Kurallar: herkes ekler, kimse silmez (`CLAUDE.md:16`, `AGENTS.md:65`); kanıtsız bulgu yazılmaz; ölçülemeyen "DOĞRULANAMADI" yazılır (`REDTEAM.md:95`; 131 geçiş). Ayırt edici özellik **öz-suçlama kayıtları**: başlığında "KENDİ HATAM" geçen 5 D-kaydı (D-252, D-356, D-360, D-412, D-430). Numara çakışmaları da kayıt olur (D-83 "dördüncü çakışma", 2026-08-13; D-431 çakışma yüzünden D-428'den yeniden numaralandı). Denetimler `MIMAR DENETIMI` etiketiyle commit'lenir (14 commit). 2026-08-21'de "Defter/kuyruk bütünlüğü: 3 kural, 3 mutasyon" ile defter teste bağlandı; 2026-08-27'de bu kapı bozuk bir yol dizgisini yakaladı ("14 > 13 taban"). Belge bayatlığına karşı "belge kapısı": T154 ilk koşuda "ALTI SÜRÜM bayatlığı" yakaladı (2026-08-26); `SAHA_RUNBOOK.md` "kanonik + belge kapılı" (`YAZILIM_BITIRME_PLANI_20260901.md:79`).

### 3.7 HANDOFF (devir protokolü)

"Bu projede iş defalarca kota bitişiyle yarıda kaldı. Bir Codex token'ı biterken bir görev zimmetli kaldı; denetim iş akışlarında 25'ten fazla ajan oturum limitine takıldı" (`HANDOFF.md:3-8`). Devreden: kod yazmayı bırak, genel kapıyı koş ve sonucunu yaz, şablonu en üste ekle, görevi `[IN_PROGRESS]` bırak, kilidi kendin açma (`HANDOFF.md:12-17`). Şablon: sebep, görev, durum, dokunulan dosyalar, genel kapı gerçek çıktısı + exit, çalışma ağacı temiz mi, devralanın ilk yapması gereken, tuzaklar (`HANDOFF.md:64-90`). Devralan: "Genel kapıyı kendin koş. Devredenin yazdığına güvenme" (`HANDOFF.md:94-105`). Örnek kayıt: 2026-08-21 gece koşumu kapanışı (T127/T115/T129/T128/T128-B; "KAPI DURUMU: 15/15 · Ran 715 · OK"; "MİMARIN MASASINDA" ve "İNSANI BEKLEYEN" listeleri; `HANDOFF.md:21-60`). Eylül'de aynı işlevi `DEVAM.md` üstlendi (6 Eylül 21:00 devam noktası: Jetson paketi, saha oturumu ölçümleri, mimar kararı bekleyenler, sabah sırası; `DEVAM.md:1-80`).

---

## 4. Proje fazları ve takvim

### 4.1 ARCHITECT_PLAN — mimari kararlar ve riskler (v1.0, 3 Ağustos 2026)

**Takvim gerçeği (`ARCHITECT_PLAN.md:16-32`):** DDR 15.07.2026'da teslim edildi, sonuçları 29.07'de açıklandı; FDR son teslim **21.09.2026 17:00**, FDA test uçuşu **30.09–03.10.2026**, yarışma Ağustos–Eylül 2027. "Kuyruğun sıralaması FDA'ya (58 gün) göre yapılır."

**FDA ≠ yarışma (`ARCHITECT_PLAN.md:36-58`):** FDA çoklu rotorlu VTOL, 20×20 m, ≥30 m irtifa, ≤10 dk; yarışma sabit kanat + mancınık, 50×50 m HTAB. "Yanlış güzergâh tespiti yapan takım 0 puan alır." Açık risk R1: VTOL drone "yok/belirsiz".

**Puanlama duyarlılığı (`ARCHITECT_PLAN.md:62-105`):** `simulation/score.py` şartname formülünü birebir uygular; P_görev = 600 (K=2.0'da 1200); ağırlık terimi `(25000 − m_İHA)/10` görev puanından büyük — "ağırlık düşürme, algoritma iyileştirmesinden daha çok puan getirir".

**Mimari veri akışı (`ARCHITECT_PLAN.md:109-148`):** kamera → `codes/rpi_inference.py` (letterbox, YOLOv8-seg 512, maske) → `codes/costmap_path_finder.py` (serbest alan = zemin AND NOT engel, distanceTransform, açıklık ağırlıklı A*, C-space doğrulama; durumlar ACIK / KAPALI_DAR / KAPALI_KOPUK / DOGRULAMA_BASARISIZ / HEDEF_YOK / MASKE_YOK) → `comms/protocol.py` (JSON, UDP/SiK 433 MHz) → YKS (`comms/yks_gui.py`, hakem onayı, ACK + IKA_GO) ve İKA (`comms/ika_receiver.py`, `ika_nav`).

**Üç katman ve monotonluk (`ARCHITECT_PLAN.md:150-181`):** "Karar (4 Ağustos 2026): Yaklaşım C." Katman 1 otorite (zemin), Katman 2 emniyet ağı (engel + DOTA OBB araç, yalnız çıkarır), Katman 3 geometri (`R_GEREKLI_M = 1,10 m`). Neden A değil: şartname "vb." der, sayılamaz küme → fail-dangerous. Neden saf B değil: molozu zemin sanma v13 %37,7, v16 %31,6.

**Karar kayıtları (`ARCHITECT_PLAN.md:289-392`):** K-1 ROS2 yok; K-2 sınıf-id sözleşmesi tek yerde (`codes/sinif_semasi.py`, import anında `dogrula()`); K-3 model seçimi mAP'e göre yapılmaz ("mAP arena sıralamasını tersine çeviriyor"); K-4 ölçüm yolu üretim yolundan ayrışmaz; K-6 araç kâhini DOTA OBB (COCO 2 / DOTA 93 araç); K-7 çoklu sınıf yalnız ön-eğitim; K-8 arena IoU yetmez, "gerçek nadir karede zemin" kapısı şart; kare hızı 3 FPS hedef / 1 FPS asgari (Yunus, 2026-08-18; `ARCHITECT_PLAN.md:229-252`).

**Riskler (`ARCHITECT_PLAN.md:447-458`):** R1 VTOL yok; R2 gerçek arena test kümesi yok; R7 eğitim verisi araçları zemin etiketliyor; R8 sınıf 2 çakışması (gerçekleşti, S2 ile kapandı); R3 Jetson TensorRT sürümü; R4 çözünürlük kırılganlığı; R6 eğitimler izsiz ölüyor. **Faz planı (`ARCHITECT_PLAN.md:462-478`):** Faz 0 insan → 1 kusurlar → 2 şartname → 3 donanım → 0-B → 4 serbest alan mimarisi (S1–S8); "Eğitim sırası ZORUNLU: S1 → S2 → veri üretimi → eğitim".

### 4.2 YAZILIM_BITIRME_PLANI (v2, 1 Eylül) ve KARAR_PAKETI

**Plan (`YAZILIM_BITIRME_PLANI_20260901.md:1-9`):** "aviyonikler 5 Eylül Cumartesi geliyor; 21 Eylül'de KESİN HAZIR; gerçek test 30 Eylül TEK ATIŞ." Dayanak 45 maddelik şartname yükümlülük çıkarımı. §0 şartnadede karşılığı olmayan 8 yükümlülük (manuel paraşüt P9a, arming P9b, aktarım-havada kilidi P9c, t_hazırlık ≤ 900 s P9d, branda temas P9e, sürüm dondurma Faz C, UHDR video kanıtı) (`...:11-30`). **Faz A (1–4 Eylül) sonuçları:** P1 MAVLink canlı (D-387/389: `yerde_mi` 0,002 s'de düşüyordu, yabancı sysid irtifayı kesiyordu), P2 SerialLink (D-388: `FrameReader` tamponu sınırsızdı), P3 İKA sürücü soyutlaması (D-390: zaman aşımında çöküyordu → fail-closed), P4 runbook, P5 histerezis K=3, P8 `yks_monitor` kilidi, P9a-e — hepsi kapandı (`...:50-134`). **Faz B (5–6 Eylül):** `.engine`, gerçek FPS, Pixhawk, SiK RF, `GercekSurucu` (`...:136-143`). **Faz C (7–20 Eylül):** provalar, model döngüsü (veri-bloklu), sürüm dondurma (~18 Eylül), FDR/UHDR (`...:145-159`). **Mimar kararları:** pymavlink+pyserial kurulur (madde 4 üretim koduna dairdir), fail-closed sürücü, histerezis ön kayıtla, sim betikleri duman-testi ("kapı enflasyonu yapılmaz") (`...:183-196`).

**Karar paketi (`KARAR_PAKETI_20260901.md`):** "Hiçbiri onaysız uygulanmayacak (ÖNER-BEKLE)" (`:3-6`). K1 hakem ekranına tazelik damgası; K2 HB tespitini üretime bağlama (K3'e bağlı); K3 TEKNOFEST'e HB rengi sorusu (insan görevi); K4 K0 körlük kapısının zemini (öneri: aday süreci başlarken ön kayıtla); K5 579 MB kopya dizin silme ("madde 18 gereği yalnız senin emrinle"); K6 "aynı bölgeden ikinci geçiş" — "dürüst değerlendirme: ölçüm aleyhine işaret ediyor"; K7 T124 kapanış imzası; K8 T192/S8 kapatma; K9 T14 FDA arena iç yerleşimi. Onay biçimi tek satır (`:119-122`). Sonuç: "D-385: kullanıcı onay turu (K1-K9) — beş iş uygulandı" (commit 2026-09-01); T190 K5a ile silindi (`TASK_QUEUE.md:6535`), T124 K7 ile, T192 K8 ile kapandı. 3 Eylül'de kapsam değişti: "TEKNOFEST soruları İLETİLMEYECEK → fail-safe yorumlar KALICI; Cuma DroidCam/DJI çekimi YOK → P6 iptal; model döngüsü VERİ-BLOKLU: v36 son modeldir" (`MIMAR_DIREKTIFLERI_20260903.md:6-12`, `YAZILIM_BITIRME_PLANI_20260901.md:174-179`).

**Mimar direktifleri 3 Eylül (`MIMAR_DIREKTIFLERI_20260903.md`):** üç ölçüm işi (T99 üretim imzasıyla yeniden koşum, T101 gerçek kadrajda koridor sayısı, T61 iç-tutarlılık keşfi) — "ölçüm koşulmadan HİÇBİR kod değişmez", "EŞİK YAZILMAZ", sıralı GPU ("paralel GPU işi yok — BSOD örüntüsü"; `:13-57`). Üçü de aynı gün ölçülüp kapandı (D-399/D-400/D-401, commit 2026-09-02).

### 4.3 Faz B (saha) planı

`FAZ_B_GUN_PLANI.md` (5 Eylül): "Göz kararı yok: her adımın bir aracı ve bir çıkış kodu var"; değişmezler: "üretim kodu bu gün DEĞİŞMEZ", "ölçülen her sayı ham çıktısıyla `results/faz_b_20260905/`", "**ÖLÇÜLEMEDİ ≠ GEÇTİ**" (`FAZ_B_GUN_PLANI.md:3-11`). §0 cuma akşamı kontrol listesi (genel kapı + süit, kuru koşu, paket aynası, mühür `--dogrula` → exit 3 beklenen). §1 ilk karar: MAVLink çoğullayıcı — üç üretim süreci tek seri portu paylaşamaz; "çoğullayıcı kurulmadan hiçbir MAVLink işi başlamaz" (`:30-49`). §2 saat sırası; 6 Eylül sonuçları tabloya işlenmiş: `.engine` `.pt`'den derlendi; T17 FPS **GEÇTİ** (pt p50/p95 1,35/1,06 · engine 1,58/1,33 FPS, eşik 0,61); engine↔pt denklik D-303 oransal 3/126 **DÜŞTÜ** → "uçuş `.pt`" (`FAZ_B_GUN_PLANI.md:60-63`; D-431). Donanım sürprizi: kart "Nano 4GB / JetPack 4.6" değil **Orin Nano 4GB / JetPack 7.2.1 / Python 3.12** çıktı (D-431; `SAHA_HAZIRLIK_PLANI_20260903.md:138` GEÇERSİZ bandı).

`SAHA_HAZIRLIK_PLANI_20260903.md` ("Adıyaman'a 19 Gün"): iki tarih (21 Eylül FDR + prova, 30 Eylül–3 Ekim resmî uçuş), cumartesi montaj/kablolama/Pixhawk/Jetson saat planı, 6–19 Eylül uçuş testleri ("tek pil → günde ≤ 2 uçuş"), "KESİN HAZIR" tanımı (`:17-252`). D-410: "21 Eylül UÇUŞ GÜNÜ DEĞİL, FDR SON TESLİM günü" (2026-09-03). 6 Eylül saha oturumu: 7 Pixhawk kalemi kapandı, **RC failsafe düştü**, "uçuş yapılmadı (üç kez istendi, reddedildi)" (`DEVAM.md:3-7, 24-44`).

### 4.4 Commit tarihçesinin ay ay teması (606 commit)

| Ay | Commit | Ana tema (commit başlıklarından) |
|---|---|---|
| **2026-05** | 4 | Kuruluş: "start project" (6 Mayıs), FloodNet entegrasyonu, eğitim optimizasyonu, test altyapısı, repo temizliği |
| **2026-06** | 4 | Colab eğitimi: `navitas_seg_v2` (RescueNet+FloodNet, 100 ep); Drive dolunca GitHub'a yönelim; simülasyon iyileştirme |
| **2026-07** | 27 | DDR dönemi (11–15 Temmuz, yazar trs-1342): `comms` İHA→İKA/YKS aktarım modülü (ACK+seq, heartbeat failsafe), `sim` dürüst zincir + 5 kıvrımlı harita üreteci, `rpi_inference`, RPi canlı yayın, YKS GUI canlı algı paneli + 2.2.5 kilidi, model v3 (mask mAP50 0,627) ve v4, DDR v4.1→v4.3 belgeleri, `doc/` repo dışına; 30 Temmuz sentetik arena karışım kümesi |
| **2026-08** | 418 | Çok ajanlı düzen ve ölçüm kültürü. 1–3: anayasa/plan; 7–14: T-görevleri (letterbox, arena, zemin kapısı, v24/v27, hakem ekranı); 15–19: model kabul ön kayıtları (v28–v34), K-8 FPS kararı, S3/S5/S7; **20–21 (43+49 commit):** "YENİ ÇAĞ", üç kademeli hiyerarşi, ilk itiraz kabulü, T121/T122 çatı körlüğü, v35, push dondurması, T133 triyaj; 22–25: DJI hattı provası, yedek betiği, etiketleme kapasitesi (F4/F5), mimar vekâleti; **26 (89 commit):** worktree'li paralel dalgalar, v36, kabul zinciri K0–K7, T142–T157; 27–28: T158–T203, push serbest, D-360; 29–31: FDA planı, Codex A1/B3/A2/B2, D-371 FP16 |
| **2026-09** | 153 | Bitirme ve saha. 1: karar paketi, D-374 51 s körlük, T150; **2 (72 commit):** Faz A gece vardiyası (P1–P9), Faz B araçları (SiK hub, komut alıcı, `jetson_baslat`, `surum_dondur`), D-403–D-408; 3–4: FDR yönerge iskeleti, D-410, D-412, "cumartesiye hazır mıyız" çürütme turu, süit 2104 OK; 5–6: Pixhawk 6C (PX4→ArduCopter 4.5.7), saha tutanağı D-426; 7 (34): D-430/D-432 push kapısı, Orin Nano paketi D-431, FDR G-serisi birleştirmeleri, T211, D-436 |

---

## 5. TASK_QUEUE — sayılar, T1…T211 akışı, açık kritikler

### 5.1 Sayılar (`TASK_QUEUE.md`, 791 KB)

- Görev satırı (`grep -n "^- \[" | wc -l`): **235**.
- `[x]` içeren satır (`grep -c "\[x\]"`): **158**; bunların **156**'sı `- [x]` görev satırı.
- Durum dağılımı (görev satırı işaretine göre): `- [x]` 156 · `- [ ]` **24** · `[STATUS: READY_FOR_REVIEW]` **24** · `[STATUS: KAPANDI]` 17 (+1 "T66 ile birleşti") · `[IN_PROGRESS: Codex-2]` 1 (T107) · `[REVIEW: mimar]` 1 (T122) · `[ÖLÇÜLDÜ …]` 1 (T118) · `[BIRLESTIRILDI → T25]` 1 (T28) · `[HUMAN_COMPLETED: …]` 9.
- Bölümler (`grep -n "^## "`): Kullanım kuralları (6) · FAZ 0 İnsan müdahalesi (22) · FAZ 0-B gerçekten açık insan işleri (36) · FAZ 5 Saha kuru koşusu — EN YÜKSEK ÖNCELİK (81) · FAZ 7 Üretim karar yolunun güvenliği (294) · FAZ 6 Saha kopukluklarının onarımı (974) · FAZ 1 Doğrulanmış kusurlar (988) · FAZ 2 Şartname uyumu (1723) · FAZ 3 Donanım entegrasyonu (1899) · FAZ 4 Serbest alan mimarisi (2202) · TAMAMLANANLAR (9635).
- Kullanım kuralları (`TASK_QUEUE.md:8-18`): sıra = öncelik; `[HUMAN_COMPLETED]` satırlarına dokunulmaz (`auto_orchestrator.py` yönetir; `auto_orchestrator.py:6-17` insan uyarısı + ENTER bekler); her görevden sonra 15/15; SciPy yasak; `python` saplaması.
- **Dikkat:** `READY_FOR_REVIEW` durumundaki 24 görevin çoğu fiilen kapanmıştır; 2026-08-26 "VEKİL KAPATMA: 20 READY_FOR_REVIEW görevi KAPANDI" commit'i ve T133 ("39 görev DENETİM BEKLİYOR ama defterde yalnız 12 mimar denetimi var — kuyruk gerçeği anlatmıyor", `TASK_QUEUE.md:6068`) bu durum işaretlerinin defter (D-kayıtları) kadar güncel olmadığını gösterir. Aşağıdaki listede durum, satırdaki işarete göre verilmiştir.

### 5.2 Açık `[ ]` görevler (24; `grep -n "^- \[ \]"`)

| Satır | Görev | Şiddet |
|---|---|---|
| 44 | `[REQUIRES_HUMAN]` DJI Neo nadir 90° çekim, 7 zorunlu sahne (çatı EN KRİTİK) | insan |
| 1883 | T14 FDA parametrizasyonu 20×20 m — "MİMAR KARARINA BAĞLANDI (K9)" | ÖNEMLİ |
| 1903 | T204 `rpi_inference` ekransız kipte kontrollü durdurma yok | KÜÇÜK |
| 1911 | T205 `run_video --save` açılamayan `VideoWriter` sessiz | KÜÇÜK |
| 1928 | T208 üç küçük kilit borcu (D-407 §3) | küçük |
| 1932 | T16 Jetson TensorRT `.engine` derlemesi (6 Eylül'de fiilen derlendi — D-431; satır güncellenmemiş) | — |
| 1936 | T17 Jetson gerçek FPS (6 Eylül'de GEÇTİ — D-431; satır güncellenmemiş) | — |
| 1965 | T18 DroidCam kaynağı algı hattına (P6 iptal edildi) | — |
| 3381 | T88 arena sınırı dedektörü (ölçek kâhini 2. katman) | ÖNEMLİ |
| 4374 | **T79 koridor seçimi binde-4 gürültüye kararsız (`.pt`/`.onnx` 28 m ayrı rota)** | **KRİTİK** |
| 4544 | T91 iki şeride yayılan kapının `road` numarası tanımsız | ÖNEMLİ |
| 4626 | T92 bant seçimi gürültüye kararsız (41/260) | ÖNEMLİ |
| 6444 | **T149 İNSAN+MİMAR · gerçek İKA motor sürücüsü ve konum kaynağı yok** (P3 soyutlaması D-390 ile kapandı; `GercekSurucu` Faz B) | insan+mimar |
| 6456 | T153 KISMEN — Katman 2 şerit çıkarıcı; kalan iş model/veri | kısmen |
| 6503 | **T199 üretece arena profili — sentetik dağılım arenanın yapısını taşımıyor** | **KRİTİK — §2.1 puanı** |
| 6512 | T197 İNSAN: 36 gündüz DJI karesine üç durumlu maske | insan |
| 6514 | T194 K0 körlük kapısının zemini tek YZ görüntüsüne dayanıyor (K4c: ertelendi) | — |
| 6557 | T174 üreteç kurgusu ↔ `analyze_path` kabul ölçütü ayrışıyor | — |
| 6934 | T109 üretim modelinin `.engine`i (6 Eylül'de derlendi; satır bayat) | — |
| 7312 | T75 İHA-İB yerleşimi yanlış | KÜÇÜK |
| 7322 | T61 VERİ-BLOKLU (D-401/D-402) | — |
| 8484 | **T47 v21'in "geçilebilir" sınıfı bu alanda anlamsız** (model/veri; veri-bloklu) | **TIKAYICI** |
| 9420 | S6 `hedef` sınıfı hedef tohumu olarak bağlı değil | ÖNEMLİ |
| 9639 | **T211 motor künyesi düzeltmesi + itki bütçesi kapısı (D-435)** — insan (Yunus) etiket teyidi | KRİTİK (saha) |

**Açık KRİTİK/TIKAYICI özeti:** T79 (karar kararlılığı; P5 histerezisi belirtisini kapattı, "T79 kökü Faz C'de", `YAZILIM_BITIRME_PLANI_20260901.md:86`), T199 ve T47 (ikisi de yeni gerçek veri gerektiriyor — veri-bloklu), T149 (gerçek İKA sürücüsü donanımı), T211 (motor künyesi, insan beyanı bekliyor). T16/T17/T109 satırları 6 Eylül ölçümüne göre bayat (D-431'de kapandı, kuyruk işareti güncellenmemiş).

### 5.3 T1…T211 akışı (her T numarası; ilk kelimeler · durum)

Durum kısaltmaları: **K** = `[x]` kapalı · **K*** = `[STATUS: KAPANDI]` özgün kayıt · **D** = `READY_FOR_REVIEW` (denetim bekliyor işareti) · **A** = `[ ]` açık · **S** = sürüyor. Kaynak satır numaraları `TASK_QUEUE.md` içindir.

1. T1 · Letterbox düzeltmesi commit'e girmemiş · K (993)
2. T2 · Tek geçici NO_ROUTE görevi kalıcı iptal ediyor · K (1001)
3. T3 · Güvenlik testi 0/18 karede rota üretemiyor · D (1062)
4. T4 · Geçme ölçütü çekimserliği denetlemiyor · D (1214)
5. T5 · Şerit sınırları dolgulu tuvale göre · K (1290)
6. T6 · Sürüş sırasında gelen NO_ROUTE yok sayılıyor · K (1342)
7. T7 · `min_area_ratio` dolgulu tuval alanına göre · K (1404)
8. T8 · Iraksak `analyze_path` kopyası · K (1456)
9. T9 · `mpp=None` olduğunda ihlal eşiği · K (1525)
10. T10 · Erken `return`: çökmüş thread'de exit 0 · K (1608)
11. T11 · `--no-route` adres bayrağı olmadan TypeError · D (1662)
12. T12 · `IKA_GO` gönderiliyor ama tüketilmiyor · K (1725)
13. T13 · İKA, İHA'nın inişini beklemiyor · K (1798)
14. T14 · FDA parametrizasyonu 20×20 m · A (1883)
15. T15 · FDA 10 dk bütçesi uçtan uca (D-382) · K (1891)
16. T16 · Jetson TensorRT `.engine` derlemesi · A (1932; fiilen D-431)
17. T17 · Jetson gerçek uçtan uca FPS · A (1936; fiilen D-431 GEÇTİ)
18. T18 · DroidCam kaynağı algı hattına · A (1965)
19. T19 · yalnız H3 insan satırında anılıyor · kuyrukta görev satırı yok (29)
20. T20 / T20-b · IHA_LANDED saha uçuşunda üretilmiyor; kilit geçerli inişi reddediyor · K (1974, 2134)
21. T21 · Saha zinciri halka sözleşmesi · D (103)
22. T22 · `saha_kuru_kosu.py` Gazebo'suz uçtan uca koşucu · D (150)
23. T23 · Kuru koşunun pozitif kontrolü ve mutasyon kanıtı · D (205)
24. T24 · `analyze_path` waypoint'leri bağlantısız · K (303)
25. T25 (+T28) · Güven eşiği hiçbir yerde uygulanmıyor · K (465)
26. T26 · Koridorun hedefe ulaştığı doğrulanmıyor · K (400)
27. T27 · Jetson saha paketi karar güvenliği düzeltmeleri · K (907)
28. T28 · Hakem ekranı "karar yok" ile "kapı yok" ayrımı · T25'e birleştirildi (587)
29. T29 · GUI varsayılan algı kaynağı · K (856)
30. T30 · `KENAR_GUVENSIZ` örnekleme parametresine duyarlı · K (767)
31. T31 · `road` etiketi rotanın şeridine uymuyor · K (619)
32. T32 · Güven metriği yanlış yerden ölçülüyor · K (696)
33. T33 · Araç katmanı (vekil) · K (2355)
34. T34 · Hakem ekranı doğrulamadığı §6.4 iddiasını "✓" · K (2378)
35. T35 · `rota_bul` letterbox içerik sözleşmesini taşımıyor · K + K* (9137, 9173)
36. T36 / T36b · Hakem ekranı çıkarım parametrelerini çıplak; beklenen şerit satırı · K + K* (2502, 2529, 8598)
37. T37 · Gönderilemeyen komut ekranda başarılı görünüyor · K (2432)
38. T38 · Kuru koşu halka 7 kök kare · K (9020)
39. T39 · Jetson paket üreteci parite testi · K + K* (9048, 9065)
40. T40 · Kompozit arena zemini · K + K* (8808, 8847)
41. T41 · İçerik sözleşmesi çağrı yerlerine bağlanmadı · K + K* (8666, 8692)
42. T42 · D-397 mimar hükmü · K (9002)
43. T43 · Ölçek halkası (Halka 5) · K (8941)
44. T44 · T43 hakem ekranının hizasını bozdu · K + K* (2575, 2609)
45. T45 · Kompozit arena tam içerik kutusuna yayılmıyor · K (8559)
46. T46 · (eski: BLOKE) vekil · K (8510)
47. T47 · v21 "geçilebilir" sınıfı bu alanda anlamsız · **A, TIKAYICI** (8484)
48. T48 · Zemin maskesi sağlamlık · K (2683)
49. T49 · Sentetik arenada 11/12 · K (2769)
50. T50 · Zemin sınıfı otorite · K (8357)
51. T51 · Sentetik arena kadraja oturmuyor · K + K* (8266, 8294)
52. T52 · Kaplama tavanı ayırt edici değil (D-398 DOĞRULANAMADI) · K (2975, 8245)
53. T53 · 11-sınıf ön-eğitim + gerçek hücre · K (2896)
54. T54 · Adım 1-3 kabul, adım 4 · K (3082)
55. T55 · Kadraj kümesi açık şerit · K (8184)
56. T56 · Kadraj kipi şartnameye sadık değil · D (8139)
57. T57 · Prosedürel zemin dokusu · K (8074)
58. T58 · Üretim modelini v24'e geçir · K* (7991)
59. T59 · Kaplama tavanı 0,55 → 0,67 · D (7919)
60. T60 · Üreteci şartnameye sadık kıl · K* (3194)
61. T61 · İç-tutarlılık — VERİ-BLOKLU · A (7322)
62. T62 · Saha ölçüm betiği v20'de kalmış · K* (7338)
63. T63 · Karar doğruluğu şartnameye sadık zeminde · K (7432)
64. T64 · Hakem ekranına arena kaynağı ve ölçeği · K* (7450)
65. T65 · Karar yolunun arena sınırı kavramı yok · K* (7825)
66. T66 · Üreteç geometrisi arenaya benzemiyor · K* (4277)
67. T67 · Gerçek arenada rota bariyerin içinden geçiyor · D (7617)
68. T68 · Üreteç bariyeri açık zemine koymuyor · T66 ile birleşti (7593)
69. T69 · T65 kısıtını devreye bağla · K* (7742)
70. T70 · Ölçek halkası sabit başlangıç sayısına bağlı · K* (7501)
71. T71 · Şartname otoritedir: figür YZ ürünü · K* (4174)
72. T72 · Hedef konumu halkası sahipsiz · K* (4097)
73. T73 · Saha kodu parametrik değil · D (4017)
74. T74 · Kusursuz algıyla bile (vekil) · K (4658)
75. T75 · İHA-İB yerleşimi yanlış · A (7312)
76. T76 · v27'yi üretim zincirine al · D (3942)
77. T77 · Hakem ekranı kabul zeminini göstersin · D (3883)
78. T78 · Zemin kapısı v27 ile yeniden ölç · D (3813)
79. T79 · Koridor seçimi gürültüye kararsız · **A, KRİTİK** (4374)
80. T80 · Hakem ekranı istenen (vekil) · K (3751)
81. T81 · Canlı algı görünümü (vekil) · K (3679)
82. T82 · Açık alanı çökmüş (vekil) · K (3617)
83. T83 · Ölçek kâhini hiyerarşisi · D (3584)
84. T84 · kuyrukta görev satırı yok (DOĞRULANAMADI)
85. T85 · v30'u üretim zincirine al · D (3513)
86. T86 · Ölçek kâhinini üretime (vekil) · K (3429)
87. T87 · `kompozit` kaynağında rota · D (3291)
88. T88 · Arena sınırı dedektörü · A (3381)
89. T89 · kuyrukta satır yok; commit 2026-08-16 "T89 asgari araç koruması — bağımsız denetim ALTI kusur buldu"
90. T90 · İki etiketleme otoritesi · K (4470)
91. T91 · İki şeride yayılan kapının `road` numarası · A (4544)
92. T92 · Bant seçimi gürültüye kararsız · A (4626)
93. T93 · K5 kapısı tek temiz çekilişte · K (4570)
94. T94 · Planlayıcı en iyi darboğazın medyanı · K (4730)
95. T95 · `rota_bul` açıklık koruması · K (4869)
96. T96 · İki kollu sahnede `road` çatal · K (7156)
97. T97 · Önermesi üretim ölçeğinde çürüdü · K (5110)
98. T98 · 3 FPS hedefiyle tıkayıcı değil · K (5148)
99. T99 · D-399 ölçüm + karar · K (7133)
100. T100 · v36 ile (D-378) · K (7150)
101. T101 · D-400 ölçüm + karar · K (7289)
102. T102 · `serbest ⊆ zemin` kapıya · K (5270)
103. T103 · Saha paketi `model_registry.json` taşıyor · K (5361)
104. T104 · Kurulum yordamı testle kilitlendi · K (5459)
105. T105 · K5 üç durumlu: OLCULEMEDI · K (6660)
106. T106 · Figür çöküşü güven çöküşü · K (6682)
107. T107 · Eğitim betiğinin `AD` varsayılanı bayat · **S** `[IN_PROGRESS: Codex-2]` (6926)
108. T108 · kuyrukta satır yok (DOĞRULANAMADI)
109. T109 · Üretim modelinin `.engine`i · A (6934; fiilen D-431)
110. T110 · K0 örneklemesi kaldırıldı · K (6817)
111. T111 · Bakırlık envanteri · K (6798)
112. T112 · Ölçüm aynası senkronu testle · K (6940)
113. T113 · 14 betik arşivlendi · K (7066)
114. T114 · T104 denetimi geçti · K (5494)
115. T115 · Kuyruğun 21 satırında oktal kaçış · K (6613)
116. T116 · T54 hedefine ulaşmamış (D-201/202) · K (5512)
117. T117 · Model çatıyı öğrenmiş, etiket "zemin" diyor · D (5811)
118. T118 · Payda sözleşmesi · `[ÖLÇÜLDÜ … MİMARIN ADLANDIRMA KARARI]` (5755)
119. T119 · Yayınlanan `road` sözleşmesi 655 testte · K (5819)
120. T120 · Sahte kapı yasağı · K (5844)
121. T121 · Belirleyici koşum: çatı 0,011 → 0,989 · D (5878)
122. T122 · Yeni veri düzeltilmemiş hatta girerse · `[REVIEW: mimar]` (5911)
123. T123 · "Yedek hangi arızaya karşı" · K (5942)
124. T124 · Kullanıcı onayı K7 · K (6592)
125. T125 · Denetçi ölçemediğini "DÜŞTÜ" sayamıyor · K (5555)
126. T126 · K5'in zemini popülasyona · K (5587)
127. T127 · Temiz bölüm kazananı geçerli · K (5593)
128. T128 / T128-B · tohum ve `deterministic=False` etkisiz (`HANDOFF.md:34-38`) · kuyrukta satır yok, defterde kapalı
129. T129 · çatı körlüğü kaynak kalitesine bağlı (`HANDOFF.md:32-33`) · kuyrukta satır yok, defterde kapalı
130. T130 · Üretim modeli v34 → v35 · K (5648)
131. T131 · Hareket kümülatif kayma (ölçüm) · K (5703)
132. T132 · K0 tabanı artık kim olduğunu söylüyor · K (6002)
133. T133 · 39 görev denetim bekliyor · D (6068)
134. T134 · Zemin sağlamlık kapısı `rota_bul`a · K (6126)
135. T135 · `kamera_dogrula` içerik geçirir · K (6198)
136. T136 · DJI hattı prova edilecek · D (6214)
137. T137 · Etiketleme kapasitesi ve kalitesi · D (6284)
138. T138 · gece kareleri eğitime uygun değil (commit 2026-08-21; `TASK_QUEUE.md:6436` atıf) · kuyrukta satır yok
139. T139 · Üretim yolunda görünürlük kavramı yok · D (6341)
140. T140 · yedek/Drive kota kök nedeni (commit 2026-08-22) · kuyrukta satır yok
141. T141 · Model değil prosedür · D (6397)
142. T142 · Mimar vekili 2 · K (6418)
143. T143 · Çürütücü kıramadı (D-286) · K (6424)
144. T144 · Çürütücü kıramadı (D-286) · K (6430)
145. T145 · Çürütücü kıramadı (D-286) · K (6435)
146. T146 · Çürütücü + 2b · K (6438)
147. T147 · Çürütücünün iki tıkayıcı bulgusu · K (6440)
148. T148 · Çıkış kodu 4 testle · K (6442)
149. T149 · Gerçek İKA motor sürücüsü yok · **A, İNSAN+MİMAR** (6444)
150. T150 · D-386, K2a onayı (HB üretime) · K (6446)
151. T151 · Mimar vekili kararı · K (6450)
152. T152 · İkinci kör geçiş (D-289) · K (6452)
153. T153 · Kısmen — Katman 2 şerit çıkarıcı · A (kısmen) (6456)
154. T154 · D-295 §4; çürütücü · K (6459)
155. T155 · Yayınlanan `road` (D-296) · K (6467)
156. T156 · Genel kapıya üretim kolu (D-299) · K (6471)
157. T157 · Beş delik (D-296 §4) · K (6474)
158. T158 · Kapı artık (D-304) · K (6590)
159. T159 · "GUI arena_kadraj dışında" (D-298) · K (6476)
160. T160 · Saha (D-298 §5b) · K (6479)
161. T161 · Depo kökü `__file__` (D-300) · K (6481)
162. T162 · Şartname §6.2/§6.4 alan ihlali (D-307) · K (6588)
163. T163 · CONTRACTS §8 (D-308) · K (6585)
164. T164 · "D-309 / T164 ÖLÇÜLDÜ, T165 AÇILDI" (commit 2026-08-27) · kuyrukta satır yok
165. T165 · Referansın kesin olduğu 88 kare (D-313) · K (6572)
166. T166 · 260 karenin (D-311) · K (6577)
167. T167 · Kök bulundu (D-312) · K (6581)
168. T168 · Şerit 3 (D-378) · K (6484)
169. T169 · Hakem ekranı bayat tespit (D-317) · K (6567)
170. T170 · §5.3.2 10 dk limiti (D-318) · K (6564)
171. T171 · Asgari 30 m irtifa (D-319/320) · K (6560)
172. T172 · Tazelik kusuru (D-321) · K (6489)
173. T173 · Kısmen (D-322, kullanıcı isteği) · K (6492)
174. T174 · Kompozit kümede rota 0/12 → 50/88 (D-325) · K (6494) — ikinci satır A (6557)
175. T175 · Görevin ikinci yarısı demo kipinde (D-323 §1) · K (6539)
176. T176 · Bayatlık simetrik (D-323 §2) · K (6541)
177. T177 · Tatbikat (D-323 §3) · K (6543)
178. T178 · Senaryo (D-323 §4) · K (6545)
179. T179 · Demo (D-323 §5) · K (6547)
180. T180 · §5.3.2 (D-323 §6) · K (6549)
181. T181 · Üç (D-323 §7) · K (6551)
182. T182 · `--help` (D-323 §8) · K (6553)
183. T183 · Kaptan (D-323 §10–11) · K (6555)
184. T184 · KATMAN (D-324 §2) · K (6522)
185. T185 · Üreteç (D-324 §6) · K (6524)
186. T186 · Eğitim (D-324 §5/§10) · K (6526)
187. T187 · Kullanıcı (D-324 §7) · K (6528)
188. T188 · "Duba sırası" (D-326) · K (6530)
189. T189 · K5 yer gerçeği yalnız yatay · K (6499, 6532)
190. T190 · `data/dji_prova` silindi (K5a) · K (6535)
191. T191 · Kendini "tek yetkili" ilan eden belge (D-327) · K (6537)
192. T192 · Kullanıcı onayı K8 · K (6520)
193. T193 · Kümenin fiili (D-378) · K (6516)
194. T194 · K0 körlük kapısının zemini · A (6514)
195. T195 · Kabul zinciri tamamen sentetik · K (6496)
196. T196 · K7 mutasyon testi sessizce etkisizleşmiş · K (6513)
197. T197 · İNSAN: 36 DJI karesine üç durumlu maske · A (6512)
198. T198 · HB şekil kapısı (D-379) · K (6508)
199. T199 · Üretece arena profili · **A, KRİTİK** (6503)
200. T200 · Gerçek kümelerde 189 gizli kopya · K (6506)
201. T201 · Saha kamera yolu her kareyi aynalıyordu · K (6502)
202. T202 · Jetson kurulum bloğu kılavuzu beslemiyordu · K (6501)
203. T203 · `jetson_fps.py` kayıt defterini sormuyordu · K (6500)
204. T204 · `rpi_inference` ekransız durdurma · A (1903)
205. T205 · `run_video --save` sessiz VideoWriter · A (1911)
206. T206 · `IhaSender` ref_tip (D-406) · K (1916)
207. T207 · `AkisIstekcisi` EXTENDED_SYS_STATE (D-406 §3) · K (1925)
208. T208 · Üç küçük kilit borcu (D-407 §3) · A (1928)
209. T209 · `test_comms` 5005/5006 bind → ephemeral (D-427/D-432) · K (9600)
210. T210 · Test süiti süreç sızdırıyor · K (9613)
211. T211 · Motor künyesi + itki bütçesi kapısı (D-435) · A (9639)

Eksik numaralar (T19, T84, T89, T108, T128, T129, T138, T140, T164): kuyrukta `- [` görev satırı yok; bir kısmı "prompt'la verilen" görevlerdir (D-245: "T126 kuyrukta yok (prompt'la verildi) — kuyruğa görev yazmak mimarın", commit 2026-08-20) ve defter/commit'te izlenir; T84/T108 için hiçbir iz bulunamadı — DOĞRULANAMADI.

---

## 6. Yerel LLM ölçümleri (`LOCAL_LLM.md`, tek paragraf)

Donanım ölçüldü: Core Ultra 9 275HX, **95,38 GiB** RAM (DDR5-5600), RTX 5080 Laptop **15,63 GiB** VRAM, sistem tabanı 11,03 GiB → model bütçesi 84,35 GiB (`LOCAL_LLM.md:12-26, 99`). En kritik ayar `mmap`: mmap açıkken sayfalama `.gguf`'a karşı yapıldı, hard fault tepe **77 558/s** (`:58-59`). Eşzamanlı iki büyük model **yasak**: Qwopus tek başına 48,36 tok/s, Qwen Q8 ile birlikte 15,43 (**3,1× yavaşlama**), available 0,67 GiB, kullanım %99,3 (`:65-79`). Süreç öldüren sınır RAM değil **commit limiti**: Qwen Q8 @32K'da commit 101,28/102,38 GiB, Windows üç arka plan görevini öldürdü; 32 GiB sabit pagefile "~10 kat hızlanır" beklentisiyle uygulandı, gerçek ~1,8× (1,11 → 1,97 tok/s) — "Ben '~10 kat hızlanır' demiştim. Gerçek ~1,8 kat" (`:293-330`). Seçimler: işçi Qwen3-Coder-Next **Q6_K** (61,03 GiB, pay 23,3 GiB; Q8_0'dan geri alındı — "GERİ ALINAN ELEME", `:250-266`), red team **gpt-oss-120b MXFP4** (59,03 GiB, pay 25,3 GiB, iki reasoning kipi; MiniMax M2.5 1,97 tok/s ile arka plan görevlerini öldürdüğü için değiştirildi, SWE-bench kaybı "kabul edilen gerileme", `REDTEAM.md:349-363`). Elenenler gerekçeli: DeepSeek V4-Flash (~2 bit uzmanlar, "bozulma tam K7/K8'in olduğu yerde"), abliterated Qwopus 122B ("reddetme yönü silinmiş; red team'in en değerli çıktısı DOĞRULANAMADI, yani bir reddetmedir"), Laguna-S ("yanlış yuva") (`:201-218`). §11 harness dersleri (gpt-oss ile S9 görevi, 2026-08-09): 10 ölçülmüş kural — görevi tek değişikliklik adımlara böl, `max_tokens ≥ 32K`, satır aralıklı düzenleme aracı, kodu satır numaralı gömme, başarı ölçütü dosya içeriği olsun, her değişiklikten sonra derle; "Görev ~6 saatte bitti; bunun büyük kısmı model hızı değil, harness tasarım hatalarımdı" (`:501-540`).

---

## 7. Muhtemel jüri soruları ve belgeye dayanan cevaplar

**1. "Yapay zekâ araçlarını nasıl kullandınız?"**
Yazılı bir anayasa (`CLAUDE.md`) ve iletişim protokolü (`AGENTS.md`) altında rol ayrımlı çok ajanlı düzen: mimar (Claude 1) kod yazmaz, plan/denetim yapar (`CLAUDE.md:37`); başamele (Claude 2) üretim kodunu yazar ve Codex'e prompt üretir (`CLAUDE.md:68-74`); Codex 1/2 parça iş; yerel gpt-oss-120b red team, Qwen3-Coder refactoring (`AGENTS.md:10-19`). Her ajanın yapıştırılabilir sistem prompt'u repoda (`CLAUDE2_WORKER.md`, `CODEX_WORKERS.md`, `REDTEAM.md`, `QWEN_CLEANUP.md`). Commit tarihçesinde 39 `worktree-wf_*` izli paralel dal birleştirmesi görülür.

**2. "AI'ın yazdığı kodun doğruluğunu nasıl güvence altına aldınız?"**
Üç mekanik kapı: genel kapı `codes/test_rota_sentetik.py` 15/15 (`CLAUDE.md:56-57`), tam süit (2104 test OK, commit 2026-09-04), yeni kapılar için mutasyon kontrolü (`CLAUDE2_WORKER.md:79-84`). "Çalıştırılmayan bir kapı 'geçti' sayılmaz. Kanıt = komut + gerçek çıktı + çıkış kodu" (`AGENTS.md:182`). Push betiğe bağlı (`scripts/push_kapisi.py`).

**3. "AI kendi hatasını onaylamasın diye ne yaptınız?"**
"Bir iş, onu yazanın onayıyla kapanmaz" (`CLAUDE.md:71`); kapalı denetim zinciri: Codex → Claude 2 → mimar → Claude 2 (`AGENTS.md:259-268`). Qwen çıktısı farklı model ailesinden red team onayı olmadan master'a giremez (`QWEN_CLEANUP.md:180-183`). Geçici rol devrinde "devralan kendi ürettiği işi kendi denetleyemez" (`AGENTS.md:53-56`).

**4. "İki AI aynı modelse birbirini denetlemesi anlamlı mı?"**
Belge bunu açıkça "korelasyonlu kör nokta" olarak kabul eder: "İki tarafın ANLAŞMASI kanıt değildir. Hakem hâlâ ölçümdür" (`CLAUDE.md:75-77`). Bu yüzden itiraz kalıbının 5. maddesi ("yanılıyorsam beni çürütecek ölçüm") zorunludur (`AGENTS.md:203, 216-219`).

**5. "Ölçütleri sonuca göre esnetmediğinizi nereden biliyoruz?"**
Ön kayıt disiplini: kabul ölçütü sonuç görülmeden `results/<görev>_on_kayit.md`'ye yazılır, sonra gevşetilmez (`CLAUDE2_WORKER.md:86-89`; D-107 `REVIEW_LOG.md:7242`). Örnek: T121'de sonuç iyi olmasına rağmen K0 ön kayıt bandının altında kaldığı için "SONUÇ 2: TAKAS" verdikti (D-225); v37'ye geçiş kabul zincirini geçti ama gerçek arena karesi reddetti, geri alındı (D-332, commit 2026-08-28). Üretim model terfileri "kullanıcı kararı"dır (`AGENTS.md:252`; v34→v35, v35→v36 commit'leri).

**6. "Hata kayıtlarınızı nasıl tutuyorsunuz?"**
`REVIEW_LOG.md`: 441 D-kaydı, yalnız ekleme, her bulgu dosya:satır + gerçek satır + komut + çıktı (`REDTEAM.md:89-97`). Mimarın kendi hataları da başlıkla kayıtlı ("KENDİ HATAM" 5 kayıt: D-252, D-356, D-360, D-412, D-430). Belirsizlik "DOĞRULANAMADI" olarak yazılır (131 geçiş).

**7. "Kesintilerde (kota, çökme) iş kaybı oldu mu?"**
Oldu ve protokolleşti: T14 bayat kilit vakası (`HANDOFF.md:109-116`), "25'ten fazla ajan oturum limitine takıldı" (`HANDOFF.md:3-8`). Karşılık: `HANDOFF.md` devir şablonu ve devralanın "genel kapıyı kendin koş" listesi; Eylül'de `DEVAM.md` devam noktaları; `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` kuralı (`CLAUDE2_WORKER.md:76-77`).

**8. "Test verisi/sentetik veriye ne kadar güveniyorsunuz?"**
Sınır açıkça yazılı: "Gerçek 30 m arena karesi olmadan modelin gerçek arenadaki başarımı doğrulanamaz ... T40 karar mantığını sınanabilir kılar; model başarımını sınamaz. Bu ayrım her raporda yazılacak" (`TASK_QUEUE.md:65-71`). Sim betikleri "sahada kanıt sayılmaz" (CONTRACTS §11.1, `YAZILIM_BITIRME_PLANI_20260901.md:192-193`). K-8: arena IoU tek başına yetmez, gerçek nadir karede zemin kapısı şart (`ARCHITECT_PLAN.md:353-356`).

**9. "Yerel modelleri neden ve nasıl seçtiniz?"**
Ölçümle: RAM/VRAM/commit limiti tabloları, 3,1× yavaşlama, 77 bin hard fault (`LOCAL_LLM.md:63-79, 293-330`). Bağımsızlık ölçütü (red team ≠ işçi modeli), sığma payı, reasoning kipi (`REDTEAM.md:349-357`); elenenlerin gerekçesi yazılı (`LOCAL_LLM.md:201-218`). Harness hataları da dürüstçe kayıtlı (`LOCAL_LLM.md:530-540`).

**10. "Projeyi takvime nasıl bağladınız ve saha gerçeğiyle nasıl yüzleştiniz?"**
`ARCHITECT_PLAN.md:16-32` takvimi şartname Tablo 1'e bağlar; `YAZILIM_BITIRME_PLANI_20260901.md` 21 Eylül "KESİN HAZIR" hedefiyle Faz A/B/C; `KARAR_PAKETI` "ÖNER-BEKLE" ile insan onayı. Sahada varsayımlar ölçümle çürüdü ve kayda geçti: kart Nano değil Orin Nano çıktı (D-431), 21 Eylül uçuş günü değil FDR teslimi (D-410), RC failsafe düştü ve uçuş yapılmadı (`DEVAM.md:3-7`), motor künyesi beyanı değişti (T211/D-435/D-436). "ÖLÇÜLEMEDİ ≠ GEÇTİ" (`FAZ_B_GUN_PLANI.md:11`).

---

## Ek · Bu özetin sınırları (DOĞRULANAMADI listesi)

- `AGENTS.md:62` push dondurma satırının bilinçli mi bırakıldığı.
- T84 ve T108 numaralı görevlerin hiç açılıp açılmadığı.
- `READY_FOR_REVIEW` işaretli 24 görevin her biri için fiilî kapanış tarihi (vekil kapatma commit'i toplu; tek tek eşleme yapılmadı).
- Gemini 3.6 Flash ve Qwopus 35B'nin (kullanıcı manuel denetimi) repoya katkı miktarı.
- 3 Eylül sonrası "Fable 5 mimar / Opus 5 amele" takasının `AGENTS.md`/`CLAUDE.md`'ye yazılıp yazılmadığı (bu iki belgede iz yok; yalnız `MIMAR_DIREKTIFLERI_20260903.md:3` ve `FAZ_B_GUN_PLANI.md:3`'te).
