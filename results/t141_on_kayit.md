# T141 ÖN KAYIT — kilit YAZILMADAN önce yazıldı (D-107)

> Tarih: 2026-08-22 · Yazan: Claude 2 (başamele) · Görev: **T141** ·
> Karar dayanağı: `REVIEW_LOG.md` **D-277 §3-4** (mimar hükmü).
> ⛔ Bu turda: yeni model **aranmaz**, yeniden eğitim **yok**, eşik
> **değişmez**, terfi **yok**, `config/model_registry.json`'a **yazılmaz**.

## 1. NE İDDİA EDİLİYOR

Saha yordamına girecek cümle bir **davranış iddiasıdır**:

> *"Rota üretilmiyorsa model DEĞİŞTİRİLMEZ; İKA sürmez, sebep kaydedilir."*

T104/D-193'ün sınıfı tam olarak şudur: **kılavuz var olmayan bir davranışa
işaret eder.** Bu yüzden cümle yazılmadan önce iddianın kodda **doğru olup
olmadığı** koşularak sınanır; yanlışsa cümle yazılmaz, kusur bildirilir.

## 2. KİLİDİN YAKALAMASI GEREKEN ŞEY (önceden yazılı)

Kilit, **belgedeki kuralı** kaynak alıp **kodda icra ederek** doğrular.
Şu üç mutasyonun **her biri** en az bir testi düşürmelidir:

| # | mutasyon | düşmeli mi |
|---|---|---|
| M1 | `ika_nav.navigate` içindeki rota kapısı devre dışı (`rota_kapisi_acik` hep True) | **EVET** |
| M2 | `receiver_rota_gecerli` NO_ROUTE'u yok sayar (`no_route` kontrolü kaldırılır) | **EVET** |
| M3 | Kılavuzdan/listeden (b) yasağı cümlesi silinir | **EVET** |

⚠ **M3 kritik:** bugün M1/M2'yi `tests/test_ika_surus_no_route.py` zaten
yakalıyor. Yeni kilidin **eklediği** şey belge↔kod bağıdır. Eğer yeni kilit
yalnız M1/M2'yi yakalayıp M3'ü kaçırırsa, **eklediği değer yoktur** ve bunu
öyle yazarım.

## 3. BAŞARISIZLIK SAYILACAK SONUÇLAR

- Kod iddiayı **karşılamıyorsa** (NO_ROUTE'ta sıfır-olmayan motor komutu
  çıkıyorsa): cümle yazılmaz, **KUSUR** olarak bildirilir, görev kodu
  düzeltmeye döner. Yordamı "doğruymuş gibi" yazmak yasaktır.
- Üç mutasyondan biri **yakalanmıyorsa**: kilit eksiktir, `x/y` ile
  raporlanır ve eksikliği gizlenmez.
- Testi geçirmek için **iddia zayıflatılmaz** (ör. "sürmemeli" → "sürmemesi
  önerilir"). Cümle mimarın D-277 §4/2'de yazdığı hâliyle kalır.

## 4. KAPI

`codes/test_rota_sentetik.py` → **15/15** ·
`unittest discover -s tests -q` → **799 OK** + yeni testler.
Düşerse görev geri alınır (anayasa madde 14).
