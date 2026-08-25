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
| Codex raporu | işlendi | ✅ D-285; D-278 KAPANDI |
| eğitim v2 | kapı §4(a)+(b) | |
| S2 yönelim | test + ölçüm | |
| T143 · T144 · T145 | kapı | |
| T142/T135 | ölçüm + karar | |
| şartname boşluk | rapor + kritikler | |
| etiket dalga 2 | 40 kare | |
| terfi | §4(d) | |

## 5. KAPANIŞ KAYDI
(doldurulacak)
