# MİMAR VEKÂLETİ 2 — 2026-08-26 gecesi (→ 2026-08-27)

> **Veren:** kullanıcı, 2026-08-26 00:5x: *"tüm kontrol sende, bugünlük başamele de
> mimar da sensin; projenin TEKNOFEST şartnamesine göre kusursuz çalışmasını
> istiyorum, bunun için her şeyi yap"* + *"tüm onayları veriyorum, onay bekleme,
> 9 saat yokum, boş durma."*
> **Alan:** Claude 2 (Fable 5). **Önceki vekâlet:** `mimar_vekaleti_20260825.md`
> (kapanış §5'i okundu; devir listesi bu gecenin girdisidir).

## 1. Bu vekâletin ÖNCEKİNDEN FARKI
| konu | 25 Ağustos | bu gece |
|---|---|---|
| kendi işimi kapatmak | yasak (§1) | **Codex denetimi** ile kapanır (D-278 kapandı, D-279…282 düzeltildi — D-285). Bu geceki kendi işim için Codex yok → **taze çürütücü ajan** + ölçüm; "kapandı" değil **"çürütülemedi"** yazılır. |
| eşik / sözleşme | yorumlar, değiştirmez | **"tüm onaylar"** kapsamında: yalnız **ön kayıtlı ölçümle** ve `CONTRACTS.md`'ye gerekçeli D kaydıyla değiştirilebilir. Sayıya bakıp eşik oynatmak yine YASAK (D-86'nın hatası). |
| terfi | yasak (D-133) | ön kayıtlı kapı (`gece_20260826/ON_KAYIT.md §4`) geçerse ve çürütücü kıramazsa **yapılır**; aksi hâlde aday kalır. |
| push | yasak | **yasak** (§5 açıkça kalkmadı). |
| insan görevi | kullanıcıya raporlanır | aynı. |

## 2. GECE PROGRAMI (ön kayıt: `results/gece_20260826/ON_KAYIT.md`)
- **GPU:** `gece_v2_v35taban` (t127 reçetesi birebir + dji ×20 + 0038 çift-konum val). Başladı 01:0x.
- **Dalga 1 (paralel, worktree):** S2 yönelim (K-A rota ekseni) · T143 (`.engine` + kamera) ·
  T144 (`len(l)`) · T145 (parlaklık alt sınırı) · T142/T135 eşik ÖLÇÜMÜ · şartname boşluk denetimi.
  Her kod teslimine bir çürütücü.
- **Dalga 2:** etiketleme (40 kare, 8 amele, `140` aracıyla, şartname §4b+EK-2/3/4) →
  uygunluk (138) + bant tanısı (137) → `gece_v3` eğitimi (zaman kalırsa).
- **Kapanış:** kabul zinciri + 29 test karesi + 67 gerçek kare + arena figürü; terfi kararı
  §4(d) kuralıyla; commit; bu dosyanın §4/§5'i doldurulur.

## 3. YAPILMAYACAKLAR
`git push` · `python` (Store saplaması) · SciPy/skimage · serbest alanı büyüten işlem ·
kullanıcı dosyası silme · sonucu görüp bant değiştirme.

## 4. ÖLÇÜLEBİLİR ÇIKTI (kapanışta doldurulur)
| iş | hedef | sonuç |
|---|---|---|
| Codex raporu | işlendi | ✅ D-285; D-278 KAPANDI, D-279…282 düzeltildi |
| eğitim v2 | kapı §4(a)+(b) | (a) GEÇTİ, (b) **FP 2** → terfi yok (D-286 §2) |
| eğitim v3 / v4 / v5 | §4 + §7/§8 | v3=v4: (a) GEÇTİ, ROTA 10, TP 9, FP 1, **MASKE_YOK 11 > 10** → yok; v5: (b) GEÇTİ (TP 10) ama **(a) DÜŞTÜ** → yok (D-287 §3) |
| S2 yönelim | test + ölçüm | ✅ birleşti (None bayt-eş); v35 maskesinde kazanç **0**, etiket tavanı +7 (D-287 §1) |
| T143 · T144 · T145 | kapı | ✅ üçü KAPANDI (çürütücü kıramadı) |
| T142/T135 | ölçüm + karar | ✅ **eşik (0,55/0,40)** CONTRACTS T142; T135 kapandı (iki kol da ölü bulgusu) |
| şartname boşluk | rapor + kritikler | ✅ 18 hüküm, 8 KRİTİK → T146–T151; **T146/T147/T148 KAPANDI** (dalga 2 + 2b), T149/T150/T151 açık |
| etiket dalga 2 (+3) | 40 kare | ✅ **160 kare** (40+120), madde 12, 3 denetçi; toplam gerçek etiket 320 |
| terfi | §4(d) | **YOK** — kural gereği (D-287 §5) |

## 5. KAPANIŞ KAYDI — 2026-08-27 05:1x
**Rol başameleye döner** (vekâlet 2 bitti). Sayılar: kapanan görev **8** (T135, T142, T143, T144, T145, T146, T147, T148), açılan **6** (T146–T151), defter kaydı D-285/286/287, CONTRACTS: T142 eşik, §6.5 (K1), §6.6 (K4+K8), §7.1 (K5+K6). Eğitim 5 koşum (v2, v3, v4, v5 + ölçümleri), etiket 160 kare, ajan ~9 M jeton. Kapı her birleştirmede 15/15; son: **896+ OK**. Push YOK.
**Yapılmayanlar:** terfi (kural); T149 (insan: İKA sürücüsü), T150 (HB — gerçek kırmızı H karesi gerek), T151 (tek karar yolu kararı); `saha_gunu_kontrol_listesi.md` (izlenmiyor) K5 komutu; çürütücülerin "dokunulmadı" listesi (D-287 §2); EK-6 etiket soruları.
**İnsan görevleri (madde 9):** H-A DOĞRULAMA uçuşu — arena benzeri saha, **kırmızı H yer işareti**, gimbal 90°, KB→HB ekseni boyunca uçuş; H-B hakem ekranı canlı prova (`--yks-hedef/--ika-hedef` ile, IKA_GO ACK + 2. onay kanıtı görülmeli); H-C İKA sürücü/konum donanım kararı (T149); H-D kamera x-ayna sorusu (`cv2.flip`, D-287 §2).
