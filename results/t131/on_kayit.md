# T131 · ÖN KAYIT — K0 taban geçmişi tek aletle yeniden ölçülür

> ⚠ Bu dosya **ölçümlerden ÖNCE** yazıldı (D-107). Aşağıdaki hüküm kuralları
> ölçüm sonucuna göre gevşetilmeyecek.

## 0. Defter araması (D-252 kuralı — her ön kaydın ilk satırı)
`REVIEW_LOG.md` + `TASK_QUEUE.md` içinde `kayma defteri · sürüm ötesi · drift ·
taban geçmişi · terfi geçmişi` arandı → **yalnız T131'in kendi satırı çıktı.**
Bu ölçüm daha önce yapılmamıştır. ("Arandı, bulunamadı" kaydın kendisidir.)

## 1. Neden yeniden ölçüyorum (metne güvenmiyorum)
Git geçmişinden çıkardığım tabloda K0 figür değeri v30'da **sayısal alan olarak
YOK**; yalnız `k0_korluk.olculen` düz metninde geçiyor: `"figur zemin %8,0"`.
D-180'in kusur sınıfı tam olarak budur (biçimli metinden sayı ayıklamak).
Bu yüzden metni **kanıt saymıyorum**; aynı figürü, aynı fonksiyonla, bugün
yeniden ölçeceğim.

## 2. Aletin değişmediği ÖLÇÜLDÜ (kıyasın ön koşulu)
- `_preprocess` · `_maskeleri_icerige_kirp` · `kaplama` → v30 dönemi (`865f591`)
  ile bugün **bayt-eş**.
- `CONF = 0.30` değişmedi · `INFER_SIZE = 512` (v30 döneminde çıplak sabit,
  bugün defterden türetiliyor, **etkin değer aynı**).
- Figür dosyası `data/arena_referans/sartname_s9_arena.png` v27'den beri
  **hiç değişmedi** (son commit `4ed3b8d`, D-83).
- Kabul kümesi `sentetik_arena_kadraj_t66` v27'den beri **aynı** (payda 260 sabit).
⇒ Sürümler arası kıyas **meşrudur**; ölçülen fark modeldendir, aletten değil.

## 3. Ölçüm
`65_kabul_denetcisi.kaplama()` **içe aktarılarak** (kopyalanarak DEĞİL) üretim
soyağacının her ağırlığında figür zemin oranı ölçülür: v17 · v20 · v21 · v24 ·
v27 · v30 · v34 · v35. Hepsi `INFER_SIZE=512` ile — yani **denetçinin sabit
aletiyle**. ⚠ v17/v20 dönemlerinde çıkarım 640 olabilir; onların sayısı
*alet-tutarlıdır ama dönem-tutarlı değildir* ve tabloda öyle işaretlenir.

## 4. HÜKÜM KURALLARI (önceden yazıldı)
**H1 — v34 aykırı değerdir:** eğer `figür(v30) ≥ 5 × figür(v34)` **ve**
`figür(v35) ≥ 5 × figür(v34)` ise, v34 kendinden önceki ve sonraki üretim
modellerinin ikisine göre de aykırıdır.
- **H1 doğrularsa:** T130'da ölçülen **18,43×** uyarısı "tehlikeli yön"ü değil
  **aykırı bir tabana olan uzaklığı** ölçmüştür. Bunu yazarım.
- **H1 çürürse** (v30 ≈ v34): düz metindeki "%8,0" yanlış ya da başka tabanlıdır;
  mimarın "kümülatif tek yönlü kayma" çerçevesi **ayakta kalır** ve ben
  D-256'daki yorumumu değil, bu ön kaydı yanlışlamış olurum. Onu da yazarım.

**H2 — uyarılar terstir:** her terfi için, oran **bir önceki üretim modeline**
göre hesaplanır ve denetçinin bandına (`0,5 ≤ oran ≤ 2,0`, `65:89-90`) sokulur.
- v34 terfisi bandın **ALTINA** düşer (`< 0,5` YETENEK uyarısı) **ve** v35
  terfisi v30 tabanıyla band **İÇİNDE** kalırsa → iki uyarı **yer değiştirmiştir**:
  kapı ateşlenmemesi gereken yerde ateşlenmiş, ateşlenmesi gereken yerde susmuştur.
- Aksi çıkarsa aksini yazarım.

## 5. YETKİM OLMAYAN ŞEYLER (T131 kısıtı · §9.2)
- `K0_ORAN_ALT` / `K0_ORAN_UST` **değiştirilmez**.
- **Kapı eklenmez, eşik konmaz.** Çıktı yalnız **görünürlüktür**.
- v35 terfisi bu görevle **geri alınmaz**; altı kapıyı geçti.
- `config/model_registry.json`'a **yazılmaz** — okunur.
