# NAVITAS — SÜRÜ İLETİŞİM VE ÇAKIŞMA ÖNLEME PROTOKOLÜ

> Anayasa: `CLAUDE.md` · Sözleşmeler: `CONTRACTS.md` · Kapılar: `TEST_SPECS.md`
> Bu dosya **kimin nereye yazabileceğini** ve **çakışmanın nasıl önlendiğini** tanımlar.

---

## 1. Sürü kadrosu

| # | Ajan | Rol | Yöneten | Sistem prompt'u |
|---|---|---|---|---|
| 1 | **Claude 1** (Opus 5) | Başmimar, araştırmacı, denetçi | Kullanıcı | `CLAUDE.md` |
| 1b | **Claude 2** (**Fable 5**, 2026-08-20 → 09-20) | **Başamele** (üretim kodu) **+ mimarın denetçisi** | Claude 1 (iş) · Kullanıcı (itiraz) | `CLAUDE2_WORKER.md` |
| 2 | **Codex 1** | Amele kodlayıcı | **Claude 2 / Fable 5** (2026-08-20'den itibaren) | `CODEX_WORKERS.md` |
| 3 | **Codex 2** | Amele kodlayıcı (Codex 1 ile **eş yetkili yedek**) | **Claude 2 / Fable 5** | `CODEX_WORKERS.md` |
| 4 | **gpt-oss-120b** MXFP4 (yerel) | Red team, debugger, insan raporlayıcı | Claude 1 | `REDTEAM.md` |
| 5 | **Qwen3-Coder-Next Q6_K** (yerel) | Temizlik ve refactoring | Claude 1 | `QWEN_CLEANUP.md` |
| 7 | Gemini 3.6 Flash | — | **Kullanıcı (manuel)** | bu protokolün dışında |
| 8 | Qwopus 35B | — | **Kullanıcı (manuel)** | bu protokolün dışında |

**7–8 numaralı ajanlara Claude 1 müdahale etmez.** Onların ürettiği iş repoya girerse
Claude 1 yalnız **denetler**, yönlendirmez.

⚠ **4 ve 5 numaralı yerel modeller ASLA aynı anda yüklenmez.** Roller zaten ardışıktır
ve makine ikisini birden kaldırmıyor. Donanım ölçümleri ve çalıştırma ayarları:
`LOCAL_LLM.md`.

---

## 2. Dosya yazma matrisi

`Y` = yazabilir · `E` = yalnız **ekleyebilir** (mevcut satırı değiştiremez) · `D` = yalnız durum satırı · `—` = salt okuma

| Yol | Claude 1 | **Claude 2 (Fable 5)** | Codex 1/2 | Red team | Qwen3-Coder |
|---|---|---|---|---|---|
| `CLAUDE.md`, `AGENTS.md`, `CONTRACTS.md`, `ARCHITECT_PLAN.md`, `RESEARCH_NOTES.md`, `TEST_SPECS.md` | **Y** | — | — | — | — |
| `CODEX_WORKERS.md`, `REDTEAM.md`, `QWEN_CLEANUP.md`, `LOCAL_LLM.md` | **Y** | — | — | — | — |
| `TASK_QUEUE.md` | **Y** | **D** | **D** | — | **D** |
| `REVIEW_LOG.md` | **E** | **E** | **E** | **E** | **E** |
| `HANDOFF.md` | **Y** | **Y** | **Y** | **Y** | **Y** |
| `codes/`, `comms/`, `simulation/`, `scripts/`, `drone/` | *(madde 7 istisnası — **2026-08-20 KAPALI**)* | **Y** | **Y** | — | **Y** |
| `tests/` | *(istisna — **KAPALI**)* | **Y** | **Y** | — | **Y** |
| `models/`, `dataset/`, `data/`, `results/` | — | **Y** | **Y** | — | — |
| `auto_orchestrator.py`, `.codexrules` | **Y** | **Y** (görevle) | **Y** (görevle) | — | — |
| Kullanıcının belgeleri (`rapor/`, `*.docx`, `*.pdf`, `*.jpeg`, `*.mp4`) | — | — | — | — | — |

### Geçici rol devri

Bir ajan kotada veya erişilemez durumdayken **kullanıcı** başka bir ajana onun rolünü
geçici olarak verebilir. Devralan ajan, devraldığı rolün yazma yetkilerini **o görev
boyunca** kullanır — matris satırı değişmez, yetki **görev bazında** genişler.

⚠ **Devralan kendi ürettiği işi kendi denetleyemez.** Red team modeli amele rolünde
kod yazarsa o iş `PENDING_REDTEAM_REVIEW`'a **girmez** (kendi kendini onaylamış olurdu);
doğrudan `[STATUS: READY_FOR_REVIEW]` olur ve denetimi **Claude 1** yapar.
Aynı model o kodu ileride red team olarak da denetleyemez — bağımsızlık kalıcı olarak kaybolur.

Kayıt biçimi, görev satırının altına:
`- **Rol devri:** <tarih> · <ajan> ← <rol> · sebep: <ne> · denetim: <kim>`

**Mutlak yasaklar (istisnasız, herkes için):**
- Kullanıcının dosyalarını **silmek**.
- `REVIEW_LOG.md` içindeki mevcut kayıtları **değiştirmek veya silmek** — yalnız sona eklenir.
- Başka bir ajanın `[IN_PROGRESS]` görevine dokunmak (bkz. §3).
- İzinsiz `git commit` / `git push`.

---

## 3. Kilit protokolü

**Kilit birimi görevdir, dosya değil.** `TASK_QUEUE.md` içindeki durum işareti kilittir.

```
[ ]                          serbest — alınabilir
[IN_PROGRESS: <AI_Adı>]      KİLİTLİ — sahibi dışında kimse dokunamaz
[STATUS: PENDING_REDTEAM_REVIEW]    Qwen çıktısı, red team onayı bekliyor
[STATUS: READY_FOR_REVIEW]   mimarın denetimini bekliyor
[x]                          kapatıldı (mimar denetiminden geçti)
```

### İş alma
1. `TASK_QUEUE.md`'yi oku, **ilk** `[ ]` görevi seç.
2. Durumu `[IN_PROGRESS: <Senin_Adın>]` yap ve **hemen kaydet** — kaydetmeden kod yazma.
3. Görevin dokunduğu dosyalar o andan itibaren senin sorumluluğundadır.

### Çakışma önleme
- Bir görev `[IN_PROGRESS]` iken, o görevin **dosyalarına** başka ajan yazamaz.
- İki görev aynı dosyaya dokunuyorsa, ikincisi birincisi kapanana kadar **alınmaz**.
- Kuyruk yazarken Claude 1 bunu gözetir; aynı dosyaya dokunan görevleri **ardışık** dizer.

### ⚠ Bayat kilit serbest bırakma
Bir ajan kotaya takılır veya çökerse görevi sonsuza kadar kilitli kalır.
**Bu gerçekten yaşandı** (Codex-1 token'ı biterken T14 zimmetli kaldı).

- Kilidi **yalnız kullanıcı** veya **kullanıcının açık onayıyla Claude 1** serbest bırakır.
- Serbest bırakırken kilidin altına şu satır eklenir:
  `- **Kilit serbest bırakıldı:** <tarih> · önceki sahip <AI> · sebep: <kota/çökme> · yarım kalan iş: <ne>`
- Kilit alındığında yarım kalan işin **durumu doğrulanır**: genel kapı koşulur, çalışma ağacı bozuksa önce onarılır.

---

## 4. Yedekli çalışma (Codex 1 ↔ Codex 2)

Codex 1 ve Codex 2 **eş yetkilidir**. Biri kotaya takıldığında diğeri devralır:

1. Devralan ajan `HANDOFF.md`'yi okur.
2. Genel kapıyı koşar (`codes/test_rota_sentetik.py` → 15/15). Düşüyorsa **önce onu onarır**.
3. Bayat kilit varsa §3'e göre serbest bırakılmasını **ister** — kendi başına açmaz.
4. Sonraki `[ ]` görevi alır.

**Aynı görevi iki Codex asla paralel almaz.** Kuyruk tek sıradır; kilit tektir.

---

## 5. İş akışı zinciri

```
        Claude 1  ──►  TASK_QUEUE.md  ──►  Codex 1 / Codex 2
        (mimar)         (tek kuyruk)          (kod yazar)
            ▲                                      │
            │                                      ▼
            │                          [STATUS: READY_FOR_REVIEW]
            │                                      │
            └──────── denetim ◄────────────────────┘
                         │
                         ├─ kapı geçti ──► [x]
                         └─ kapı düştü ──► [ ] + REVIEW_LOG.md kaydı


   Bulut kotası bitti ──► Qwen3-Coder (refactoring)
                                 │
                                 ▼
                    [STATUS: PENDING_REDTEAM_REVIEW]
                                 │
                                 ▼
                 MODEL TAKASI (Qwen boşalt → gpt-oss yükle)
                                 │
                                 ▼
                       gpt-oss-120b (red team)
                                 │
                     ┌───────────┴───────────┐
                  onaylandı              reddedildi
                     │                       │
                     ▼                       ▼
          [STATUS: READY_FOR_REVIEW]   [ ] + REVIEW_LOG.md
```

**Qwen doğrudan master'a iş veremez.** Red team onayı zorunlu geçittir.

⚠ **Geçit bir model takası içerir.** İki yerel model aynı anda yüklenemez.
*Ölçüldü:* eşzamanlı yükleme makineyi %99,3 doluluğa itiyor, verimi **3,1× düşürüyor**
ve saniyede 77 bin hard fault üretiyor (`LOCAL_LLM.md` §3). Takas ~1–3 dk sürdüğü için
iş **toplu** yapılır: Qwen N görevi bitirir → takas → red team N görevi birden denetler.
Görev başına takas **yapılmaz**.

---

## 6. İnsan müdahalesi

- Fiziki insan emeği gerektiren işleri **yalnız Claude 1** kuyruğa ekler (anayasa madde 9).
- Etiket biçimi ve tuzakları: bkz. `CONTRACTS.md` § Orkestratör sözleşmesi.
  **Özet:** tek satır · metin içinde `]` **olamaz** · bu etiket `TASK_QUEUE.md` içinde
  yalnız **gerçek görev satırlarında** geçebilir. Düz yazıda örnek olarak yazılırsa
  orkestratör onu **hayalet görev** sanıp operatörü bloke eder (bu tuzağa bir kez düşüldü).
- Diğer ajanlar bu etiketli satırlara **dokunmaz**, onları **görev olarak almaz**.

---

## 7. Raporlama sözleşmesi

Her ajan işini bitirdiğinde şunu üretir:

| Ajan | Nereye | Ne |
|---|---|---|
| Codex 1/2 | `TASK_QUEUE.md` | Kapı komutu + **gerçek çıktı** + çıkış kodu |
| gpt-oss-120b (red team) | `REVIEW_LOG.md` | Kanıtlı bulgular + **HUMAN REPORT** (3 madde) |
| Qwen3-Coder | `TASK_QUEUE.md` | Değişiklik özeti + 15/15 kanıtı + `PENDING_REDTEAM_REVIEW` |
| Claude 1 | kullanıcıya | Denetim sonucu + hangi kapıların **gerçekten** koşulduğu |

**Ortak kural:** Çalıştırılmayan bir kapı "geçti" sayılmaz. Kanıt = komut + gerçek çıktı + çıkış kodu.

---

## 8. İtiraz protokolü — amelenin mimara itirazı

> Anayasa madde 19. **Yalnız Claude 2 (Fable 5) kullanır.** Diğer ameleler kusur bulursa
> `REVIEW_LOG.md`'ye kanıtıyla ekler; mimarın **kararına** itiraz kanalı bu değildir.

Mimarın bir kararı (karar kaydı `K-*`, görev tanımı, ön kayıt ölçütü, kapı eşiği) **yanlış**
görünüyorsa Fable 5 şunu üretir — ve **kod yazmadan önce** üretir:

```
İTİRAZ · <hangi karar> · <hangi dosya:satır veya D-numarası>
1. MİMARIN İDDİASI  : <tek cümle, mimarın kendi sözleriyle>
2. NEDEN YANLIŞ     : <tek cümle>
3. KANIT            : koşulan komut + GERÇEK çıktı  (veya alıntılanan kod)
4. ÖNERİ            : <ne yapılmalı>
5. YANILIYORSAM     : <bu itirazı çürütecek ölçüm ne olurdu>
```

**5. madde zorunludur.** Kendini çürütecek ölçümü söyleyemeyen itiraz **itiraz değil, tercihtir.**

### Mimarın işleyişi (bağlayıcı)
| Gelen | Mimar ne yapar |
|---|---|
| Kanıt **ölçüm** içeriyor | Ölçümü **kendi koşar**. Tutarsa karar **değişir**, `REVIEW_LOG.md`'ye D-kaydı düşer ve kaydın içinde **kusurun mimara ait olduğu** açıkça yazılır. |
| Kanıt yalnız **kod alıntısı** | Alıntı doğrulanır. Doğruysa aynı yol izlenir. |
| Kanıt **yok** / "bence" | **Reddedilir** — ama **reddin gerekçesi yazılır**. Sessiz ret yoktur. |
| İtiraz **haklı ama kapsam dışı** | Reddedilmez, **kuyruğa görev** olarak girer. |

⚠ **Otorite argümanı iki yönde de yasaktır.** "Ben mimarım" da, "ben Fable 5'im, Opus 5'ten
iyiyim" de kanıt değildir. Hüküm ölçümündür.

### İtirazın kapatılması
İtiraz `REVIEW_LOG.md`'ye **her hâlde** kaydedilir — kabul edilse de reddedilse de.
Kabul edilen itiraz görev açar; reddedilen itirazın gerekçesi bir sonraki itirazın zeminidir.
**Kaydedilmeyen itiraz tekrar eder.**

---

## 9. Üç kademeli hiyerarşi (2026-08-20, kullanıcı kararı)

```
        Claude 1 (mimar)          karar · mimari · denetim · insan görevi
             │  ne yapılacak
             ▼
   Claude 2 / Fable 5 (başamele)  iş bölme · üretim kodu · Codex'e prompt
             │  nasıl yapılacak
             ▼
        Codex 1 / Codex 2         parça iş
```

### 9.1 Kim kime prompt yazar
- Mimar **Codex'e doğrudan prompt yazmaz.** Fable 5'e **ne** istediğini söyler.
- Fable 5 işi böler, Codex'e **yapıştırılabilir** prompt üretir (`CODEX_WORKERS.md` disiplini geçerlidir).
- Codex çıktısını **Fable 5** toplar; mimara **tek elden** rapor gider.

### 9.2 🔴 YETKİ DEVRİ, KARAR DEVRİ DEĞİLDİR
Fable 5'e devredilen şey **iş dağıtımıdır**. Devredilmeyenler — bunlar mimarda kalır:

| Karar | Neden mimarda |
|---|---|
| Eşik değiştirme / kapıya çevirme | Bu projede kör sıkılaştırma dört kez patladı |
| Üretim modeli terfisi | Seçim **insanındır** (D-133); mimar sıralar |
| Mimari değişmezler (madde 15/16) | Anayasa |
| **İnsan görevi açmak** | Madde 9 tekeli — Fable 5 **brifing verir**, görev açmaz |
| Görev kapatma (`[x]`) | Denetim mimarın |

Fable 5 bunlardan birine ihtiyaç duyarsa **önerir ve bekler**; kendi başına uygulamaz.
Aciliyet gerekçe değildir.

### 9.3 Denetim zinciri — kimse kendi işini onaylamaz
```
Codex yazar      ->  Fable 5 denetler   (Fable 5 yazmadı: bağımsız)
Fable 5 yazar    ->  mimar denetler
mimar yazar      ->  Fable 5 denetler   (madde 19, YUKARI yön)
```
Bu zincir **kapalıdır**: her üretimin, onu üretmeyen bir denetleyicisi vardır.
⚠ Fable 5 Codex'e yazdırdığı kodu denetleyebilir; **kendi yazdığını denetleyemez.**
Bir görevin bir kısmını kendi yazıp kalanını Codex'e verdiyse, **kendi yazdığı kısım
mimara gider.**

### 9.4 Kilit ve çakışma — artık Fable 5'in sorumluluğu
- Kuyruk **tektir**, kilit **tektir** (§3 aynen geçerli).
- İki amele aynı dosyaya **aynı anda** yazamaz. Fable 5 görev dağıtırken bunu gözetir;
  aynı dosyaya dokunan görevleri **ardışık** verir.
- Codex'e verilen her görev kuyrukta `[IN_PROGRESS: Codex-1]` biçiminde görünür —
  Fable 5 kendi adına kilitleyip Codex'e devretmez.

### 9.5 Defter zorunluluğu — "kim ne yaptı" hatırlanmaz, YAZILIR
Her görevin altına, kapanışta:

    - **Yazan:** <ajan> · **Denetleyen:** <ajan> · **Kapı çıktısı:** <komut + sonuç>

Bu satır **zorunludur**. Gerekçesi ölçülmüştür: mimar bir turda görev yazarlarını
yanlış hatırladı (D-194 §1) ve iki gün önce kendi koşturduğu eğitimi unutup yeniden
istedi (D-200 §2). Üç kademede bu risk **artar**, azalmaz.
