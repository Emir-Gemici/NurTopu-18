# CODEX DEVİR — 20 Eylül 2026, Adıyaman saha oturumu

> **Devreden:** mimar oturumu (Claude 1), 20 Eyl, Adıyaman KYK yurdu.
> **Devralan:** Codex.
> **Kullanıcı emri:** *"kalan işleri codex'e devrediyoruz, ona detaylı belgeler bilgiler aktar."*
>
> ⚠ **Komuta zinciri notu.** `CLAUDE.md §19` Codex prompt'unu **Claude 2 / Fable 5'in** yazmasını
> söyler (mimar → başamele → amele). Bu oturumda Fable 5 **koşmuyor** ve kullanıcı devri
> doğrudan istedi. Bu paket o boşluğu doldurur; Fable 5 döndüğünde denetim onda kalır.
> **Bir iş, onu yazanın onayıyla kapanmaz** — bu kural yürürlükte.

---

## 🔴 Önce bunları bil — yoksa yanlış yere bakarsın

### 1. Takvim: FDR'deki tarih BAYAT
FDR Bölüm 1 *"provası 21 Eylül Adıyaman; 30 Eylül–3 Ekim'de uçacak"* diyor. **YANLIŞ.**
İki bağımsız kaynak (teknofest.org + iki yerel gazete): **yarışma 21–25 Eylül, Adıyaman
Üniversitesi Stadyumu**; 23–25 Eylül ziyarete açık. 21 Eylül **programın birinci günü**.
Takımın kendi slotu hâlâ bilinmiyor — insan teyidi bekliyor. Ayrıntı: `../UYGUNLUK_OLCUMU.md` §0.

### 2. Saha yazılımı `master`'da YOK
Sahada çalışan kod **`origin/bilgilendirme-he`** dalındadır (taban `tunel-saha-20260918`).
`master`'da `scripts/yer_yonlendirici.py` **yok**, `comms/yks_gui.py`'de `tunel` kelimesi
**hiç geçmiyor** (0 eşleşme). YKİ **bu daldan** açılır. Tartışmaya kapalı.

Hazır çalışma kopyası: `/home/trs/projects/navitas-wt-bilgilendirme` (git worktree, 324ce42b).

### 3. Büyük dal birleştirme YAPILMAYACAK
Tünel çizgisi ile `origin/master` **108 ileri / 92 geri**. Çakışma beklenen yerler:
`comms/yks_gui.py`, `REVIEW_LOG.md`, `jetson_paket/`, `codes/rpi_inference.py`.
Yarışma arifesinde birleştirmek saha kodunu bozar. **Uçuş sonrasına.**

### 4. Jetson boot overlay'ine DOKUNMA
`extlinux.conf` etiketi "IMX219" der, yüklenen overlay `imx477-dual`. **Etiket bayat, overlay DOĞRU** —
donanım IMX477 (depoda 50+ yerde doğrulandı). Kamera bugün bu overlay ile **çalıştı**.
13–15 Eyl'de beş farklı overlay denenmiş; o denemeler mekanik bir arızayı yazılımda arıyordu.
**Altıncı tahmini yürütme.**

### 5. Commit kimliği
Yazar **`trs-1342 <socialmediaoftrs1342@gmail.com>`** (CLAUDE.md §17, kullanıcı kararı 2026-09-13).
⚠ `CODEX_WORKERS.md` içindeki `Emir-Gemici <yunusgemici2007@gmail.com>` **BAYATTIR**, kullanma.
**Hiçbir AI atfı eklenmez** — `Co-Authored-By`, `Generated with`, oturum bağlantısı: hepsi yasak.
Kullanıcının GitHub hesabı bir kez bu yüzden spam işareti aldı.

---

## ⚖ BİLİNEN BELGE ÇELİŞKİLERİ ve HÜKÜMLERİ

> Bu depoda birden fazla belge aynı konuyu farklı tarihlerde yazmış ve bazıları **bayat kalmış**.
> Aşağıdakiler **bilinen** çelişkilerdir; hükümleri verilmiştir. **Çelişki bulursan durma —
> ama tahminle çözme:** tarihe bak, `CLAUDE.md` (anayasa) üstündür, ve bulduğunu
> `REVIEW_LOG.md`'ye kanıtıyla yaz.

| # | Çelişki | Hüküm |
|---|---|---|
| Ç1 | `AGENTS.md:62` *"git push 2026-08-21'den beri DONDURULDU"* ↔ `CLAUDE.md §5` *"push SERBEST (2026-08-28)"* | 🔴 **AGENTS.md BAYATTI, 23 gün.** 2026-09-20'de düzeltildi. **Push serbest**, ama kapı kırmızıyken push yok; kapı koşulamıyorsa **eksiklik yazılır** ve push **kullanıcı onayına** bağlanır. Bu çelişkiyi Codex yakaladı (20 Eyl) |
| Ç2 | `CODEX_WORKERS.md` commit yazarı `Emir-Gemici <yunusgemici2007@gmail.com>` ↔ `CLAUDE.md §17` `trs-1342 <socialmediaoftrs1342@gmail.com>` | **CLAUDE.md geçerli.** CODEX_WORKERS bayat (D-356 sonrası kullanıcı kararı 2026-09-13) |
| Ç3 | `CODEX_WORKERS.md` repo yolu `O:\navitas` (Windows) | Bu oturum **Linux**'ta. Yollar ve yorumlayıcı farklı — bkz. `01_ORTAM_VE_ERISIM.md` |
| Ç4 | FDR Bölüm 1 *"prova 21 Eylül / uçuş 30 Eyl–3 Ekim"* ↔ resmî kaynaklar | **FDR bayat.** Yarışma **21–25 Eylül, Adıyaman Üniv. Stadyumu** (D-517) |
| Ç5 | Jetson `extlinux.conf` etiketi *"IMX219 Dual"* ↔ yüklenen `imx477-dual.dtbo` | **Etiket bayat, overlay DOĞRU.** Donanım IMX477. **Dokunma** (D-520) |
| Ç6 | Belgelerde *"kırmızı ≤ 4 s"* ↔ koddaki sarı 3 s / kırmızı 5 s | **Kod geçerli.** Belgeler güncellenmedi (T-L) |
| Ç7 | `REVIEW_LOG.md`'de **iki farklı D-505** (master çizgisi ↔ tünel çizgisi) | Birleştirmede biri yeniden numaralanacak (T-H). Bu paketteki **D-517…D-522 GEÇİCİDİR** |
| Ç8 | `CLAUDE.md §19` Codex prompt'unu **Fable 5** yazar der ↔ bu paketi mimar yazdı | Fable 5 koşmuyordu, kullanıcı devri doğrudan istedi. **Denetim yine Fable 5'te**; *bir iş, onu yazanın onayıyla kapanmaz* |

---

## 🎯 ASIL AMAÇ — bu paket yeterli DEĞİL

Kullanıcının bu oturumdaki asıl sorusu şuydu: **"yazılım gerçekten çalışıyor mu?"**
Bu paket o sorunun bugün ölçülebilen kısmını kapatır, **tamamını değil**.

`SAHA_20260920/` yalnız **bugünün** işidir. Projenin tamamını okumadan hüküm verme.
Okuma sırası:

1. `CLAUDE.md` — anayasa (**çelişkide bu üstündür**)
2. `AGENTS.md` — yazma matrisi, kilit protokolü, push kuralı (20 Eyl'de düzeltildi)
3. `CONTRACTS.md` — sınıf id, mesaj tipi, koordinat çerçevesi (**koda çıplak sabit yazılmaz**)
4. `TEST_SPECS.md` — kapılar ve doğrulama parametreleri
5. `BILGILENDIRME_HE/00…08` (dal `bilgilendirme-he`) — 19 Eyl saha günü devri, **8 belge**
6. `REVIEW_LOG.md` sonu — D-505…D-516 (tünel çizgisi), sonra bu paketin D-517…D-522'si
7. `SAHA_20260920/UYGUNLUK_OLCUMU.md` — L1…L13 zincir tablosu, **ne ölçüldü ne ölçülmedi**
8. `TASK_QUEUE.md` — iş kuyruğu (kilit kuralı: ilk boş `- [ ]`, hemen `[IN_PROGRESS: ...]` yap ve **kaydet**)

**YKS'nin gerçekten çalıştığı, ancak canlı ölçümle söylenir.** Bugüne kadar kanıtlananlar ve
kanıtlanmayanlar `UYGUNLUK_OLCUMU.md`'de halka halka yazılıdır; "çalışıyor gibi görünüyor"
o tabloya girmez.

---

## Bugün ne yapıldı (hepsi kanıtlı)

| # | İş | Kanıt |
|---|---|---|
| 1 | Uygunluk ölçümü — 13 halkalı zincir tablosu | `../UYGUNLUK_OLCUMU.md` |
| 2 | Takvim varsayımı çürütüldü | D-517 |
| 3 | Canlı onay testi aracı + kendi kanıtı (**3/3 mutant**) | D-518, `../kanit/b2_kendi_testi_20260920.txt` |
| 4 | Bu Linux PC **yedek yer istasyonu** oldu | D-519, `../kanit/yki_linux_20260920.png` |
| 5 | **Jetson'a erişim kuruldu**, kamera kök nedeni bulundu | D-520 |
| 6 | Bekleyen telemetri kapısı kurulumu (`c9ee27f0`) **koşuldu** | aşağıda §Jetson |
| 7 | **montaj_yaw ölçüldü: +90°**, zincir doğrulandı | D-521, `../MONTAJ_YAW.md` |

Kanıt defteri: `../KANIT_DEFTERI.md` (**D-517 … D-521**, numaralar GEÇİCİ — iki çizgide
D-numara çakışması var, birleştirmede doğrulanacak).

## Dosya haritası

| Dosya | İçerik |
|---|---|
| `../UYGUNLUK_OLCUMU.md` | "Yazılım uygun mu?" — L1…L13 zincir ölçümü, hüküm |
| `../PLAN_20260920.md` | Günün planı, fazlar, bu makinenin sınırları |
| `../KANIT_DEFTERI.md` | D-517…D-521, ham kanıt atıflarıyla |
| `../JETSON_GERCEK_DURUM.md` | Jetson'ın durumu, servisler, üç python, tuzaklar, ilk SSH sırası |
| `../MONTAJ_YAW.md` | montaj_yaw = +90, görev üretme komutu, pilot kartı, doğrulama |
| `01_ORTAM_VE_ERISIM.md` | makine, python, SSH, Jetson'ın bugünkü hâli |
| `02_GOREVLER.md` | **kalan işler + ön kayıtlı geçme ölçütleri** |
| `03_PRATIK_SAHA_TESTI.md` | 🔴 **ÖNCELİKLİ** — sahada terminal açmadan, ekrandan yürütülen gerçek test |
