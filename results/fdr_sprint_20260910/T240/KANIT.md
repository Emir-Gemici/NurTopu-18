# T240 — Ortak belge kilidi yardımcısı ve üç test dosyasının geçirilmesi

**D-460 karar 2.** Bağımsız mimar denetimi T226-D2 · T228-D2 · T221-D3'ü REDDETTİ;
ortak gerekçe tekti: her test dosyası çizik ayıklamasını **kendi** yazmıştı ve üçü de
yalnız `~~...~~` biliyordu. Denetimde kurulan **19 gerçek dosya mutasyonunun 19'u
kaçmıştı**. Bu iş o 19 kaçışı kapatır ve kuralı tek yerden okutur.

Bu belge yalnız **koşulan** komutların çıktısını kaydeder. Ham çıktılar:
`kapi_ciktisi.txt` (kapı) ve `mutasyon_ciktisi.txt` / `mutasyon_kosum.raw.txt` (mutasyon).

---

## 1. Ne değişti

| dosya | ne |
|---|---|
| `tests/belge_kilidi.py` | **YENİ** — ortak yardımcı (yalnız stdlib): `cizikleri_ayikla`, `beyaz_liste_disi_cizik`, `normalize`, `olumlu_hukum_var`, `on_kayitli_metin_esit`, `hukum_cumleleri`. Her fonksiyonun docstring'inde **hangi kaçan mutant** için var olduğu yazılı. |
| `tests/test_belge_kilidi.py` | **YENİ** — yardımcının kendi kapısı, 42 test: her normalleştirme kuralı için **pozitif + negatif** vaka; uydurma çizme sözdizimi vakası. |
| `tests/test_yks_mk15_hakem_ekrani.py` | H4e (CONTRACTS §6.8) yardımcıdan geçti; §6.8 için beyaz liste, ön kayıtlı kaynak hükmü (örneği **koddan** doldurulur), kalın başlıklı hüküm paragrafı demeti ve paragraf komşuluğu kilidi eklendi. |
| `tests/test_isaretli_gosterici.py` | `_cizili_ayikla` / `_normal` / `_gecti_bul` artık yardımcıya bağlı ince kabuk; G8'e belge geneli **beyaz liste dışı çizik** kilidi eklendi. |
| `tests/test_faz_b_arduplane_sablon.py` | §6.6 başlığı ve `**Sonuç: … KOŞULMADI.**` cümlesi **ön kayıtlı metin eşitliği** ile bağlandı; ölçüm etiketleri, olumlu hüküm ailesi ve **kapalı hüküm cümlesi kümesi** kilidi eklendi; HTML kara listesi beyaz listeye çevrildi. Yeni meta-test `m18b` sekiz kaçanı birim düzeyinde kurar. |
| `scripts/belge_kilidi_denetle.py` | **YENİ** — depo denetimi (kapı DEĞİL, çıkış 0): `tests/` altında markdown okuyup dizge arayan testleri bulur, yardımcıyı **kullanmayanları** raporlar → `acik_kilitler.md`. |

**Ürün kodu değişmedi.** `git diff --stat HEAD` ürün/belge yollarında boş; üç belgenin
sha256'sı denetimdeki değerlerle aynı: `CONTRACTS.md 741a9ca2…`,
`GOSTERICI_KURULUM.md e01d16821d44…`, `config/pixhawk/README.md e2efd44838b6…`.

---

## 2. Kaçan 19 mutantın hepsi yeniden kuruldu ve DÜŞTÜ

Koşucu: `results/fdr_sprint_20260910/T240/mutasyon_t240.py`.
Her mutasyon **tek tek gerçek dosyaya** yazıldı, **ilgili süit gerçekten koşuldu**,
sonra dosya **sha256 ile bayt-eş** geri yüklendi.

```
## 0. Mutasyonsuz TABAN
  test_faz_b_arduplane_sablon.py         cikis=0  OK
  test_isaretli_gosterici.py             cikis=0  OK (skipped=1)
  test_yks_mk15_hakem_ekrani.py          cikis=0  OK
  TABAN: YESIL

## 2. OZET
  KACAN mutantlar   : 19/19 DUSTU
  KONTROL mutantlar : 4/4 DUSTU
  geri yukleme      : hepsi bayt-es
  HUKUM             : GECTI
```

| # | mutant | dosya | kilidi düşüren |
|---|---|---|---|
| 1 | D1b `<del>` | CONTRACTS §6.8 | `cizikleri_ayikla` + `beyaz_liste_disi_cizik` |
| 2 | D1c tek tilde `~…~` | CONTRACTS §6.8 | aynı |
| 3 | D1d `<s>` | CONTRACTS §6.8 | aynı |
| 4 | D1e çelişkili ikinci hüküm | CONTRACTS §6.8 | kalın başlıklı hüküm paragrafı demeti (yapısal) |
| 5 | A3 tek tilde | GOSTERICI_KURULUM §5 | `cizikleri_ayikla` + beyaz liste |
| 6 | A4 `<del>` | GOSTERICI_KURULUM §9 | aynı |
| 7 | A5 `<s>` | GOSTERICI_KURULUM üst hüküm | aynı |
| 8 | A6 "**bir** ardışık" | GOSTERICI_KURULUM §5 | `normalize` sayı sözcüğü → rakam |
| 9 | A7 "**en az 1 saniye**" | GOSTERICI_KURULUM §5 | `normalize` birim + karşılaştırma eş anlamlısı |
| 10 | A8 "**teyit edildi** / **başarılı**" | GOSTERICI_KURULUM §5 | `olumlu_hukum_var` (genişletilmiş aile) |
| 11 | A9 "**6 saniyeyi aşan**" | GOSTERICI_KURULUM §5 | `normalize` sonek→önek karşılaştırma |
| 12 | W1 başlıkta `~ÖLÇÜLEMEDİ~` | README §6.6 | `on_kayitli_metin_esit` (başlık) + beyaz liste |
| 13 | W6 `~ÖLÇÜLEMEDİ~ · prova KANITLANDI` | README §6.6 | aynı |
| 14 | W2 "KANITLANDI" | README §6.6 | `olumlu_hukum_var` + cümle kümesi |
| 15 | W3 `_doğrulandı_` | README §6.6 | `normalize` vurgu sökme (`_` artık harf değil) |
| 16 | W4 `__koşuldu__` | README §6.6 | aynı |
| 17 | W7 "sorunsuz tamamlandı; … sağlanmış" | README §6.6 | `olumlu_hukum_var` + cümle kümesi |
| 18 | V1 numarasız çelişkili hüküm | README §6.6 | **kapalı hüküm cümlesi kümesi** (tek yakalayan) |
| 19 | V3 ikinci `**Sonuç …**` cümlesi | README §6.6 | ön kayıtlı Sonuç + cümle kümesi |

**Kontrol mutantları** (denetimde zaten düşenler; koşucunun kendisi sağlam mı):
D1 çift tilde, D1f tipografik tırnak, W5 düz DOĞRULANDI, W8 düz GEÇTİ → **4/4 DÜŞTÜ**.
V1 ve V3 hiçbir olumlu hüküm sözcüğü taşımaz ve numaralı ölçüt anmaz: kara liste onları
**ilkece** göremez, bu yüzden çözüm kara liste genişletmesi değil **kapalı cümle kümesi**dir.

---

## 3. Kapı (hepsi gerçekten koşuldu)

Yorumlayıcı `O:\navitas-local-train\venv\Scripts\python.exe -X utf8 -B`,
kök `O:\navitas\.claude\worktrees\wf_fabd3bac-230-1`. Ham çıktı: `kapi_ciktisi.txt`.

| adım | sonuç |
|---|---|
| `test_belge_kilidi.py` (YENİ) | Ran 42 tests · **OK** · çıkış 0 |
| `test_yks_mk15_hakem_ekrani.py` **üç ardışık** | 39/39 OK (21,1 s · 21,2 s · 21,0 s) · çıkış 0,0,0 |
| `test_isaretli_gosterici.py` | Ran 62 tests · **OK** (skipped=1) · çıkış 0 |
| `test_faz_b_arduplane_sablon.py` | Ran 44 tests · **OK** · çıkış 0 |
| `test_yks_*.py` | Ran 233 tests · **OK** · çıkış 0 |
| **GENEL KAPI** `codes/test_rota_sentetik.py` | `GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15` · çıkış 0 |
| `scripts/belge_kilidi_denetle.py` | çıkış 0 · rapor yazıldı |

### Kapıda ölçülen tek engel ve kökü (gizlenmiyor)

İlk `test_yks_*.py` koşumu **KIRMIZI** geldi:
`test_yks_gui_uretim_hizasi.KompozitKaynakTests.test_kompozit_dizini_listeleniyor`
→ `AssertionError: [] is not true : kompozit kume bos listelendi`.

Kök neden **bu işle ilgisiz**: `data/arena_kompozit/images/` git'te **izlenmiyor**
(`git ls-files data/arena_kompozit/images` → 0 satır) ve `.gitignore` kapsamında;
worktree taze bir checkout olduğu için veri yoktu. 88 dosya (49,6 MB) ana kopyadan
(`O:\navitas\data\arena_kompozit\images`) worktree'ye kopyalandıktan sonra aynı süit
**55/55 OK** verdi ve tam kapı yeşile döndü. Kopya **izlenmiyor** — `git status --porcelain`
yalnız bu T240 dizinini ve yeni betiği gösteriyor, depoya hiçbir veri eklenmedi.

> Kapıyı bu worktree'de yeniden koşacak olan: veri zaten yerinde. Silinmişse
> `shutil.copytree(r"O:\navitas\data\arena_kompozit\images", <worktree>/data/arena_kompozit/images)`.

### Yan etki taraması (kapının dışında, ayrıca koşuldu)

`-m unittest discover -s tests -p "test_faz_b_*.py" -q` → **Ran 348 tests · OK (skipped=9)** ·
çıkış 0. Üç test dosyasına bağlı modül zinciri (`tests/test_faz_b_kamera_koprusu.py`,
`scripts/ardupilot_param_kaynak.py`, `scripts/isaretli_gosterici.py`) bu süpürmede yeşil.

---

## 4. Depo denetimi — hangi kilitler hâlâ açık

`acik_kilitler.md` (üretici `scripts/belge_kilidi_denetle.py`, salt okuma, AST, **kapı değil**):

| ölçüm | değer |
|---|---|
| taranan test dosyası | 204 |
| markdown okuyup dizge arayan | 55 |
| ortak yardımcıdan **geçen** | **3** (T240'ın geçirdiği üç dosya) |
| **AÇIK** (yardımcıyı kullanmayan) | **52** |
| AÇIK **ve** kaynağında çizme sözdizimi sabiti olan (ağır) | **4** |

Ağır dördü: `test_fdr_bolum4_6eylul_kaniti.py`, `test_fdr_sarkan_atif_kapisi.py`,
`test_gece_ika_baglanti_semasi.py`, `test_t220_jetson_istekleri.py` — dördü de kendi
`~~` kalıbını taşıyor, yani D-460'ta ölçülen kaçış sınıfına **açık olabilirler**.
Bu dört dosya **ölçülmedi**, yalnız listelendi: ÖLÇÜLEMEDİ ≠ GEÇTİ.

---

## 5. Sınırlar ve açık kalanlar

- **ÖLÇÜLMEDİ:** yukarıdaki 52 açık kilidin hiçbiri mutasyonla sınanmadı. Sayı,
  "hangi kilitler delinebilir" sorusunun **üst sınırıdır**, kusur sayısı değildir.
- `normalize` **belgelenmiş tek yön** seçer: sözcük → sembol (`saniye`→`s`,
  `milisaniye`→`ms`, `derece`→`°`). Birim kuralı **sayıya bağlıdır** (önünde rakam
  olmalı), yoksa "derecelendirme" birime dönerdi.
- `cizikleri_ayikla` tek tildede **belgelenmiş bir istisna** taşır: `~<rakam>`
  ("~3 s", "~8 Hz") yaklaşık işaretidir, çizgi değil. Üç belgede kod dışında kalan
  bütün tek tildelerin bu biçimde olduğu ölçüldü.
- `olumlu_hukum_var(haric=…)`: T221 §6.6'da "ölçüldü" iki **yapılmış** ölçümün
  etiketidir; `SITL_HUKUM_SAYIMI["ölçüldü"] == 2` **ve** iki etiket metni ayrıca ön
  kayıtlıdır. Kilit gevşemedi, **yer değiştirdi**.
- **Bağımsızlık (madde 19):** bu işi yazan ajan kendi işini KABUL ETMEZ; kapatma onayı
  ayrı bir denetimdedir.
