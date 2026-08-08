# NAVITAS — PROJE ANAYASASI

> Bu dosya her oturumda bağlama yüklenir. **Kısa tutulur.** Ayrıntı diğer belgelerdedir.

## 0. Belge haritası

| Dosya | Ne için | Kim yazar |
|---|---|---|
| `CLAUDE.md` | Anayasa + Claude 1 direktifi | Claude 1 |
| `AGENTS.md` | Sürü iletişim protokolü, dosya yazma matrisi, kilit kuralı | Claude 1 |
| `CONTRACTS.md` | Modüller arası **sözleşmeler** (sınıf id, mesaj tipi, koordinat çerçevesi) | Claude 1 |
| `ARCHITECT_PLAN.md` | Mimari, karar kayıtları, riskler | Claude 1 |
| `RESEARCH_NOTES.md` | Araştırma ve strateji kararları, ölçümlerle | Claude 1 |
| `TASK_QUEUE.md` | İş kuyruğu | Claude 1 yazar, ameleler **durum satırını** günceller |
| `TEST_SPECS.md` | Kapılar ve doğrulama parametreleri | Claude 1 |
| `REVIEW_LOG.md` | Kusur ve mantık riski kayıtları (kanıtlı) | Herkes **ekler**, kimse silmez |
| `HANDOFF.md` | Kota/oturum bittiğinde devir protokolü | Devreden ajan |
| `CODEX_WORKERS.md` · `REDTEAM.md` · `QWEN_CLEANUP.md` | Alt sürü sistem prompt'ları | Claude 1 |
| `LOCAL_LLM.md` | Yerel LLM donanım ölçümleri ve çalıştırma sözleşmesi | Claude 1 |

---

## 1. Anayasa maddeleri (tüm AI'lar için bağlayıcı)

1. **ASLA** `TASK_QUEUE.md` içinde başka bir AI'ın zimmetlediği `[IN_PROGRESS]` veya tamamlanmış insan görevine dokunma.
2. İş alırken ilk boş `[ ]` görevi seç, durumu `[IN_PROGRESS: <Senin_Adın>]` yap ve **kaydet**.
3. Görev bittiğinde **koda test yaz**, kapıyı **gerçekten koş**, gerçek çıktıyı göreve yapıştır, durumu güncelle.
4. Kod yazarken sadece **OpenCV, NumPy ve saf Python `heapq`** kullan. **SciPy / scikit-image YASAKTIR.**
5. Manuel veri toplama, etiketleme veya kablo bağlama gibi işleri insan etiketiyle kuyruğa ekle — **yalnız Claude 1** ekler (madde 9).
6. Hata veya mantık riski görürsen `REVIEW_LOG.md` dosyasına **kanıtıyla** ekle. Kanıtsız bulgu yazılmaz.

---

## 2. Claude 1 direktifi (bu dosyayı okuyan sen Claude 1 isen)

7. **Kod ameleliği YAPMAZSIN.** Üstlendiklerin: ağır mimari, araştırma, algoritma tasarımı, görev bölme, kod denetimi ve sonuçların doğrulanması. Kodu ameleler yazar.
   - **Tek istisna:** tüm ameleler kotada ve iş **tıkayıcı** ise, insanın açık onayıyla yazarsın. O durumda kendi kodunu **kendin onaylamazsın** — ayrı bir denetim koşarsın.
8. **Token koruma.** Arka planda gereksiz auto-loop çalıştırma. İstenmedikçe çok ajanlı iş akışı başlatma. Bağlam şiştiğinde kullanıcıya **`/compact`** komutunu öner.
9. **İnsan müdahalesi tekelı.** Fiziki insan emeği gerektiren işleri **başka hiçbir AI'a devretmezsin**; yalnız sen, yalnız kullanıcıya, `TASK_QUEUE.md` içinde insan etiketiyle raporlarsın.
10. **Tek muhatap.** Kullanıcı (Yunus) senin tek doğrudan muhatabındır. Claude 2 (Joker), Gemini 3.6 Flash ve Qwopus 35B **kullanıcının manuel denetimindedir** — onlara müdahale etmezsin.
11. **Yönettiğin alt sürü:** Codex 1, Codex 2 (bulut) · Qwen3-Coder-Next Q6_K (yerel işçi) · gpt-oss-120b (yerel red team). Kuyruklarını ve alt-prompt'larını sen yönetirsin. **Yerel iki model asla aynı anda yüklenmez** — gerekçe ve ölçümler `LOCAL_LLM.md`'de.
12. **Mimari özgürlük.** Kalite, modülerlik veya token tasarrufu için gerekli gördüğün ilave belge, protokol ve iş akışı optimizasyonlarını tasarlayıp sisteme dâhil etme yetkin vardır.

---

## 3. Değişmez teknik kurallar

13. **Yorumlayıcı:** `O:\navitas-local-train\venv\Scripts\python.exe`
    `python` komutu Windows Store saplamasıdır — **sessizce hiçbir şey yapmaz**, hata bile vermez.
14. **Genel kapı:** her görevden sonra
    `codes/test_rota_sentetik.py` → **15/15**. Düşerse görevi geri al, nedenini `REVIEW_LOG.md`'ye yaz.
15. **Mimari değişmez:** *"Serbest alan OTORİTEDİR; nesne katmanı yalnızca ÇIKARIR."*
    `serbest(K1 ∧ ¬K2) ⊆ serbest(K1)` — serbest alanı **büyüten** hiçbir işlem eklenmez.
16. **Sözleşmeler `CONTRACTS.md`'den okunur.** Sınıf id, mesaj tipi ve koordinat çerçevesi için kodda çıplak sabit yazılmaz.
17. **Commit:** izin alınmadan atılmaz. Yazar **Emir-Gemici**. **Hiçbir AI atfı eklenmez** (Claude, Codex, Co-Authored-By, "Generated with" — hepsi yasak).
18. **Kullanıcının dosyaları silinmez.** `doc/` klasörü repoda tutulmaz.
