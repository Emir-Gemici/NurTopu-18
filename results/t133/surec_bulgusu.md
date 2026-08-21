# T133 · ASIL SORU: 39 birikme NASIL oldu? — ÖNER-BEKLE

> Bu bölüm **süreç** bulgusudur; temizlik onu çözmez. Süreç değişikliği
> **mimarın kararıdır** (§9.2). Aşağıdakiler ölçüm + öneridir, uygulama değil.

## 1. ÖLÇÜM — sızıntı mı, patlama mı?

`scripts/olcum/122_t133_bekleme_yasi.py` · `results/t133/bekleme_yasi.json`
(TASK_QUEUE.md'nin **111 commit'i** tarandı; her commit'te
`READY_FOR_REVIEW` durumundaki görev kimlikleri çıkarıldı.)

```text
bugun READY_FOR_REVIEW : 39
yas (gun)              : en eski 14 · ortanca 10 · en yeni 1
adet zaman icinde      : 2026-08-07 -> 15
                         2026-08-15 -> 36
                         2026-08-20 -> 39
14 gunde: GIRIS ~ +31   CIKIS ~ -7   (net +24)
```

**Bu bir SIZINTI, patlama değil.** Sayı 14 gün boyunca **tekdüze arttı**;
yalnız üç kez düştü (−5, −1, −1). Giriş/çıkış oranı ≈ **4,4 : 1**.

⚠ **Yaşlar ALT SINIRDIR.** İlk taranan commit'te (2026-08-07) zaten 15 görev
bu durumdaydı; onlar daha eski olabilir. "14 gün" en az 14 gün demektir.

**Neden bu ayrım önemli:** patlama olsaydı çare "o turda kırılan yordamı
bul"du. Sızıntı olduğu için çare **hız/kapasite dengesidir** — ve temizlik
yaparsak birikme **yeniden başlar**. Görevin kendi uyarısı doğru çıktı.

## 2. KÖK NEDEN — durumun GİRİŞİ tanımlı, ÇIKIŞI SAHİPSİZ

`TASK_QUEUE.md` kullanım kuralları (dosyanın başı, 7 madde):
- **Kural 1:** *"İlk `[ ]` durumundaki görevi al, `[IN_PROGRESS: <Adın>]` yap."*
  → İş **çekmek** için açık bir kural var.
- **Kural 4:** *"İş bitince test yaz, durumu `[STATUS: READY_FOR_REVIEW]` yap."*
  → Duruma **girmek** için açık bir kural var.
- 🔴 **`READY_FOR_REVIEW`'den iş ÇEKMEYİ söyleyen bir kural YOK.**

`AGENTS.md` durum makinesini **çiziyor** (satır 122-128:
`READY_FOR_REVIEW → denetim → [x]` ya da `→ [ ]`) ve §9.3 **kimin** denetlediğini
söylüyor. Ama hiçbiri **ne zaman**ını söylemiyor: tetik yok, sıra kuralı yok,
sahip yok. Ameleler `[ ]` kuyruğundan çeker; **`READY_FOR_REVIEW` kuyruğundan
kimse çekmez** — mimar başka işlerin arasında sırası gelirse bakar.

Bir durumun girişi kuralla, çıkışı iyi niyetle işliyorsa **kuyruk büyür.**

## 3. ÜÇ YAPISAL ÇARPAN (ölçülmüş, iddia değil)

1. **İŞARET NE SAHİP NE TARİH TAŞIYOR.** `[IN_PROGRESS: <ad>]` en azından
   **sahip** taşır; `[STATUS: READY_FOR_REVIEW]` **hiçbiri**. Bu yüzden
   "T1 iki haftadır bekliyor" cümlesi **kuyruktan okunamaz** — ben bu sayıyı
   git geçmişinden çıkarmak zorunda kaldım. **Görünmeyen bekleme birikir.**
   Bu, D-194'ün ("kim ne yaptı BELLEKTEN okunmaz") **zaman eksenindeki** hâli.
2. **ÜRETİCİ 3, TÜKETİCİ 1.** Fable 5 + Codex-1 + Codex-2 üretir; §9.3 gereği
   Fable 5'in işini **yalnız mimar** denetleyebilir. Üretim kapasitesi tasarım
   gereği denetim kapasitesinin katıdır. 4,4:1 oranı sürprizle değil
   **hiyerarşinin şekliyle** açıklanıyor.
3. **TAVAN YOK.** Denetim bekleyen iş sayısına hiçbir sınır konmamış. Sınırsız
   kuyruk, en yavaş halkanın hızına **hiç geri baskı yapmaz**.

## 4. ÖNERİLER — ÖNER-BEKLE (hiçbiri uygulanmadı, kararı mimarın)

1. **İşaret TARİH taşısın:** `[STATUS: READY_FOR_REVIEW · 2026-08-07]`.
   Tek satırlık değişiklik; bekleme süresi kuyruğun **kendisinden** okunur.
   ⚠ Bu bir eşik değildir, **görünürlüktür** — T132'nin dersi birebir aynı:
   *kaydı tek skaler tutup üzerine yazmak geçmişi yok eder.*
2. **Çıkışa da bir kural yazılsın** (kural 1'in aynadaki karşılığı):
   *"Denetleyen, en ESKİ `READY_FOR_REVIEW` görevini alır."* Sıra = yaş.
   Bugün sıra **yok**, bu yüzden en eskiler en uzun bekliyor.
3. **Denetim yükünün bir kısmı devredilebilir mi?** §9.3 kapalı bir zincir ve
   bu **doğru**; ama Codex'in yazdığı işi Fable 5 zaten denetliyor. Mimarın
   darboğazı **yalnız Fable 5'in işidir**. Codex'e "çapraz denetim" turları
   (D-259, T130) mimarın yükünü fiilen azalttı ve **işe yaradı** — bu, kural
   hâline getirilebilir: *Fable 5'in işi önce Codex çapraz denetiminden geçer,
   mimar onun raporu üzerinden karar verir.*
   ⚠ Bu **kararı devretmek değildir** (§9.2); mimar yine kapatır, ama önüne
   ham iş yerine **kanıt tablosu** gelir.
4. **Tavan konsun mu?** Örneğin *"20'yi aşarsa yeni görev alınmaz, önce
   denetim"*. 🔴 **Bunu ÖNERMİYORUM, sadece seçenek olarak yazıyorum** —
   üretimi durdurmanın maliyeti 30 Eylül takvimiyle çakışır (D-211). Karar
   mimarın.

## 5. BU TURUN KENDİSİ BİR ÖLÇÜM

T133'ün triyajı birikmeyi **bir kez** temizler. Yukarıdaki 2. ve 3. bölüm
düzeltilmezse sayı yeniden büyür ve görevin kendi uyarısı gerçekleşir:
*"bir sonraki sefer 39 değil 80 olur."*
