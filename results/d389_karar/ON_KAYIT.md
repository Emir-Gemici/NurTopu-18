# ÖN KAYIT — D-389: İniş kanıtı ve irtifa okuyucusu sözleşme değişikliği

**Tarih:** 2026-09-02 (gece) · **Karar veren: Claude 2 — Fable 5, MİMAR
yetkisiyle** (kullanıcı 2026-09-02: "tüm yetkiyi veriyorum açıkça") ·
**Uygulama sonuçları görülmeden yazıldı** (D-107).

## 0. Karara bağlanan bulgular (D-387)

- **BULGU A:** `yerde_mi` alçalmada ilk IN_AIR örneğinde ANINDA False;
  `iha_inis_yayinci` tek çağrı + exit 3 → İHA_LANDED hiç yayınlanmaz.
  Temas SONRASI çağrı da soket birikintisindeki eski IN_AIR'lerle düşüyor.
- **BULGU B:** yabancı sysid trafiği `BagilIrtifaOkuyucu` erişilebilirliğini
  **0/193**'e indiriyor (yabancı paket önceki geçerli örneği de siliyor).

## 1. KARAR

### A → A1+A2 birlikte (D-387'deki amele önerisi kabul)

**A2 — `yerde_mi` son tarihe kadar bekler:** IN_AIR (ya da ON_GROUND dışı
herhangi bir meşru landed_state) örneği artık terminal DEĞİL; ilerlemeyi
sıfırlar (`dogrulanan=0`) ve okumaya devam edilir. "Art arda 3 temiz çift"
şartı AYNEN korunur; süre dolarsa False (fail-closed değişmedi).
Beklenen kaynaktan **bozuk alan** (bool/int dışı landed_state) terminal
kalır — bozuk veri "bekle"nmez, reddedilir.

**A1 — yayıncı son tarihe kadar yeniden dener:** `iha_inis_yayinci`,
`yerde_mi` False dönerse süre kalan olduğu sürece yeniden çağırır (geçici
istisna/bozuk paket tek atışta görevi öldürmesin).

### B → B1 (D-387'deki amele önerisi kabul)

**Yabancı/adsız kaynaklı paket KANIT DEĞİLDİR; cache'e DOKUNMAZ** (atlanır).
Gerekçe: yabancı paket bizim aracımız hakkında hiçbir bilgi taşımaz; onu
"kötü haber" saymak üçüncü bir tarafa bizi kör etme yetkisi verir (ölçüldü:
0/193). **Beklenen kaynaktan** bozuk alanlı paket ise cache'i geçersiz kılmayı
SÜRDÜRÜR (kendi hattımızdaki bozulma gerçek kötü haberdir). Sızıntı kapısı
(G5a) değişmez: değer asla yabancıdan gelmez.

### B'nin kardeşi: `yerde_mi` içindeki kaynak işleme (mimar genişletmesi)

D-387 B yalnız okuyucuyu ölçtü; aynı sınıf `yerde_mi`'de de var: yabancı bir
EXTENDED_SYS_STATE **iniş kanıtını da anında düşürüyor** (kaynak-pin'e
uymayan mesaj terminal). Tutarlı kural: pin'e uymayan kaynak **atlanır**,
terminal olmaz. Ek olarak `yerde_mi(beklenen_sysid=None)` parametresi açılır
ve `iha_inis_yayinci`'ye `--sysid` bayrağı eklenir: verilirse pin tahmine
değil beyana dayanır (ArduPilot varsayılanı 1). Verilmezse bugünkü
ilk-kaynak-pin davranışı sürer (kalıntı risk belgelendi).

## 2. Kapı ölçütleri (uygulama görülmeden yazıldı)

| # | senaryo | GEÇTİ ölçütü |
|---|---|---|
| K1 | D-387/G3 ÖZGÜN ölçüt | Alçalan profil + 10 s son tarih: `yerde_mi` **True** (P1 ön kaydının düştüğü haliyle, gevşetilmeden) |
| K2 | Soket birikintisi | Temas sonrası çağrı, birikmiş eski IN_AIR'lere rağmen **True** |
| K3 | Havada asla | Baştan sona IN_AIR akışında süre dolar, **False** (fail-closed korunmuş) |
| K4 | D-387/G5(2) ÖZGÜN ölçüt | Yabancı trafik altında erişilebilirlik ≥ %90 (ölçülmüştü: %0) ve sızıntı yine 0 |
| K5 | Yabancı EXTENDED | Yabancı sysid'in EXTENDED_SYS_STATE'i iniş kanıtını düşürmez (beklenen_sysid verilmiş halde **True**) |
| K6 | Bozuk alan terminal | Beklenen kaynaktan bozuk landed_state → False; bozuk irtifa alanı → cache silinir (eski davranış korunur) |
| K7 | Mevcut suit | `test_inis_kaniti.py` (güncellenen sözleşme testleriyle) + genel kapı 15/15 + tam suit OK |

**Bilerek güncellenecek testler** (D-387 §4'te ilan edilmişti):
`AcikBulgular` sınıfının iki karakterizasyon testi kaldırılır → yerine K1/K4
gate olur; `test_inis_kaniti.py` içinde "IN_AIR terminal" ve "yabancı kaynak
cache siler" varsayan testler yeni sözleşmeye çevrilir (her birine D-389
yorumu düşülür).

## 3. Denetim notu (madde 19)

Karar: mimar (Fable 5). Uygulama: aynı oturum (gece, kullanıcı uykuda, tam
yetki beyanıyla). "Yazanın onayıyla kapanmaz" kuralının gece karşılığı:
hakem ÖLÇÜMDÜR — ölçütler bu dosyada uygulamadan ÖNCE yazıldı, koşular ham
çıktıyla deftere geçer. Sabah kullanıcı denetimi için `D-389` kaydına
"kullanıcı onayı bekleyen kararlar" bölümü konur.
