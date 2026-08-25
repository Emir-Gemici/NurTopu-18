# CODEX DENETİM GÖREVİ — D-278…D-282 · yapıştırılabilir prompt

> **Yazan:** Claude 2 (mimar vekili, 2026-08-25). **Zincir:** mimar vekili → Codex.
> **Kullanıcı kararı:** *"mimarımız kotada, o yüzden amelen olan Codex'e
> onaylatabilirsin."* Bu görev o kararın uygulamasıdır.
> ⚠ Bu prompt Codex-1 **veya** Codex-2'ye verilir (eş yetkili). Aşağıdaki blok
> Codex oturumuna olduğu gibi yapıştırılır.

```
# GOREV: BAGIMSIZ DENETIM — Codex-<1 veya 2>
Repo: O:\navitas (Windows, git branch master)

## YORUMLAYICI — HER ZAMAN bu tam yol
  O:\navitas-local-train\venv\Scripts\python.exe
"python" komutu Windows Store saplamasidir; SESSIZCE hicbir sey yapmaz.

## ROLUN: CURUTUCU. ONAYLAYICI DEGIL.
Basamele (Claude 2) bes defter kaydi yazdi: REVIEW_LOG.md D-278, D-279, D-280,
D-281, D-282. Mimar kotada; kullanici bu kayitlarin BAGIMSIZ denetimini sana
verdi. Sen basameleyle FARKLI bir modelsin — onun kor noktalarini tasimazsin.
CLAUDE.md §19 bunu acikca degerli sayar.

Varsayilan tutumun: "BASAMELE YANILIYOR." Her kaydi KIRMAYA calis. Kiramazsan
gecer. Onaylamak icin degil, yikmak icin okuyacaksin.

## NE YAPACAKSIN — her kayit icin AYNI yordam
1. Kaydi oku (REVIEW_LOG.md, `### D-2xx` basligindan sonraki `---`ya kadar).
2. Kaydin DAYANDIGI ham ciktiyi bul (her kayitta "Ham cikti repoda:" satiri var).
3. O ciktiyi URETEN BETIGI KOS ve sayiyi KENDIN cikar. Kayittaki sayiyla
   KARSILASTIR. Fark varsa YAZ. Betik yoksa/kosmuyorsa BUNU yaz — bu da bulgudur.
4. Kaydin CIKARIMLARINI sorgula: sayi dogru olsa bile hukum ondan cikiyor mu?
   Alternatif aciklama var mi? Basamele gormedigi bir sey var mi?
5. Hukum ver: GECTI / KISMEN / DUSTU — ve her hukmun yaninda KOSTUGUN KOMUT +
   GERCEK CIKTI.

## KAYITLAR VE YENIDEN URETICILERI
D-278 (T141, rota-yoksa-surme kapisi)
  yeniden uret: python scripts/olcum/129_t141_mutasyon_olcumu.py
  beklenen    : results/t141/mutasyon_olcumu.txt ile ayni tablo
  ayrica kos  : python -m unittest discover -s tests -p "test_t141_rota_yoksa_surme.py" -v
  sorgula     : "kod uc noktada koruyor" iddiasi — simulation/scripts/ika_nav.py
                satir ~309-393'u OKU ve dogrula.

D-279 (F4 pilot, kapasite 5,1 kare/saat)
  ham cikti   : results/dji_20260822/f4/{A,B,C}/rapor.json
  yeniden uret: rapor.json'lardaki `saniye` alanlarini topla, kare basina
                ortalamayi KENDIN hesapla. 708 sn/kare cikiyor mu?
  sorgula     : 14 kare "olculen", 10 kare null — null'lar ortalamaya
                KATILMAMIS mi? Katilsaydi ne olurdu?

D-280 (DJI kirsal egitim, arena kapisi 4/4)
  ham cikti   : scripts/olcum/results/t63/dji_kirsal_v1_kabul_verdikt.json
                results/dji_kirsal/bakir_0038.json + bakir_0038_taban.json
  yeniden uret: python scripts/olcum/65_kabul_denetcisi.py --model codes/runs/segment/dji_kirsal_v1/weights/best.pt --ad codex_denetim
                (K0..K5 sayilari kayittakiyle ayni mi?)
  sorgula     : "best.pt = epoch 1" iddiasi — codes/runs/segment/dji_kirsal_v1/results.csv'yi
                AC ve dogrula. "figur_zemin 2,6 kat kotu" — results/dji_kirsal/kiyas_109.txt'de
                v35 ve dji_kirsal_v1 satirlarini karsilastir.

D-281 (adversaryal denetim, iki nedensel iddia yanlis)
  ham cikti   : results/dji_kirsal/curut_{yapisal,hat,ucus}/*.json
  yeniden uret: results/dji_kirsal/curut_hat/m4_kural_kaldirilirsa.json'dan
                "kural kalkinca ROTA kazanan" sayisini KENDIN say (0 mi?).
                results/dji_kirsal/curut_ucus/kontrol_kuculme.json'dan donuk-kontrol
                farkini KENDIN hesapla (+3..+5 mi?).
  sorgula     : Basamele "net kazanc %5-8" dedi. Kontrol yontemi (donuk vs yalniz
                kucultulmus) DOGRU bir kontrol mu? Baska bir karistirici var mi?

D-282 (bant tamamlama, +1 kare)
  ham cikti   : results/dji_kirsal/bant_tamamlama_etkisi.json
  yeniden uret: python scripts/olcum/137_bant_bosluk_tanisi.py
                python scripts/olcum/138_kare_uygunluk_denetimi.py
                ve etkisi.json'daki "kazanan" listesini KENDIN say.
  sorgula     : "mevcut etiket bozulmadi: 0 piksel" — results/dji_20260822/f5_olcek/*/
                ile results/dji_kirsal/bant_tamamlama/*/ maskelerini KENDIN
                karsilastir (m0!=0 olan piksellerde m1==m0 mi?).
                "kumede gurultu yok" — 138'in MUTLAK esikleri (kirpik %20,
                gok %5) makul mu, yoksa cok gevsek mi? Gercekten kotu bir
                kare bu esiklerden gecer miydi? SINA: bir kareyi yapay olarak
                boz (bulaniklastir / gok ekle) ve betigin yakalayip
                yakalamadigini olc.

## KURALLAR
- Yalniz OpenCV + NumPy + saf Python. SciPy/scikit-image YASAK.
- Sayilari UYDURMA. Olcemedigin seye "olculemedi" de (D-180).
- Kodda, config/, CONTRACTS.md, dataset/ icinde HICBIR SEYI DEGISTIRME.
  Yalniz OKU ve KOS. Kendi ciktilarini results/codex_denetim/ altina yaz.
- git commit YAPMA, git push YAPMA.
- Basamelenin cumlelerini TEKRAR ETME; kendi sayini yaz.
- Anlasmak kanit degildir. "Kayit makul gorunuyor" bir hukum DEGILDIR;
  kostugun komut ve cikti olmadan verdigin her hukum GECERSIZDIR.

## CIKTI — results/codex_denetim/rapor.md
Her kayit icin:
  ### D-2xx — HUKUM: GECTI | KISMEN | DUSTU
  kostugum komut(lar):
  gercek cikti (kisaltilmis):
  kayittaki sayi vs benim sayim:
  cikarim sorgusu:
  basamelenin gormedigi (varsa):
Sonda: hangi kayitlar KAPANABILIR (GECTI), hangileri DUZELTME ister.
```

## Vekilin notu
Codex'in *"GEÇTİ"* dediği kayıtlar **kapanır** — kullanıcı yetkisi. *"KISMEN"*
ve *"DÜŞTÜ"* olanlar düzeltilir ve **yeniden** Codex'e gider. Codex'in ham
çıktısız verdiği hüküm **sayılmaz**; o durumda görev geri gönderilir.
