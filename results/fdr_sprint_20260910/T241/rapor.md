# T241 — `akis_b` ve `akis_e` alt grafik kapsam RAPORU (düzeltme YAPILMADI)

**Tarih:** 2026-09-12 · **İş:** T226-D3 (D-460 karar 3, madde 5) · **Kip:** RAPOR
**Karar:** T241 ayrı bir karardır. Bu belge YALNIZ ÖLÇÜMDÜR; `akis_b.mmd`,
`akis_e.mmd` ve bunların `_dugumler.md` / `.svg` dosyalarına **DOKUNULMADI**
(`git status` bu dalda bu dosyaları değiştirilmiş göstermiyor).

## Koşulan komut ve çıkış

```
O:/navitas-local-train/venv/Scripts/python.exe -X utf8 -B \
  results/fdr_sprint_20260910/H9_MK15/t226/akis_kapsam_t226d.py \
  --rapor --mmd FDR/sekiller/akis_b.mmd --mmd FDR/sekiller/akis_e.mmd
```

Ortam: `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`, depo kökü
`O:\navitas\.claude\worktrees\wf_fabd3bac-230-2`. **Çıkış kodu 0** (RAPOR kipi
tanım gereği 0 döner; `akis_d` için aynı betik VARSAYILAN kipte koşar ve
hatada 1 döner).

## Denetim nedir

`akis_kapsam_t226d.py`'nin T226-D3'te eklenen **ALTGRAFIK** denetimi: her
DEYİM düğümünün atıf satırının AST qualname'i, içinde durduğu `subgraph`
başlığının qualname'i ile aynı ya da onun altında olmalı. `def ad()` biçimli
ÇAĞRI düğümleri denetlenmez; bir deyim düğümü **hemen önündeki** ÇAĞRI
düğümünün kapsamına düşüyorsa `CAGRI_GOVDESI` diye bağışlanır (çağrılan
fonksiyonun gövdesini çağrı düğümünün ardına koyan çizim kuralı).

## Sonuç tablosu

| diyagram | deyim düğümü | ALTGRAFIK hatası | CAGRI_GOVDESI bağışık |
|---|---:|---:|---:|
| `akis_b.mmd` | 50 | **1** | 1 |
| `akis_e.mmd` | 45 | **4** | 5 |

D-460 denetçisinin kendi referans betiği (bağışıklık kuralı YOK) `akis_b` 2 ·
`akis_e` 9 uyuşmazlık basmıştı. Fark tam olarak bağışıklıklardır (2−1 = 1,
9−5 = 4), yani iki ölçüm **birbirini tutuyor**.

## Bulgular — tek tek (kodu açıp kenarları okuyarak doğrulandı)

Aşağıdaki "aday doğru satır" sütunu **ölçümdür** (AST fonksiyon sınırları +
diyagram kenarının anlamı), **karar değildir**; düzeltme T241'e aittir.

### 1. `akis_b` · b10 — GERÇEK kayma
`b10{"while not self._dur.is_set():<br/>comms/iha_komut_alici.py:822"}`
* 822 `IhaKomutAlici.calistir` içindedir (815–…), alt grafik
  `sB2["def IhaKomutAlici.poll()<br/>…:797"]` (797–813).
* Kenarlar: `b08 --> b10`, `b10 -->|"evet"| b11` (b11 = `poll`'un 803'ü),
  `b10 -->|"hayir / KeyboardInterrupt"| b09`, `b13 --> b10`.
* `poll` gövdesinde **hiç `while` yoktur**; döngü `calistir`'ındır. Yani burada
  yanlış olan tek bir satır değil, **alt grafik sınırının kendisi** olabilir
  (döngü `calistir`'a, gövdesi `poll`a ait). Aday doğru satır: **yok —
  T241'de `sB2`'nin `calistir`/`poll` ayrımı KARARA bağlanmalı.**

### 2. `akis_e` · e13 — GERÇEK kayma
`e13["send_vel(0, 0)<br/>simulation/scripts/ika_nav.py:450"]`
* 450 `navigate` içindedir (311–452), alt grafik
  `sE1["def ika_gorevi()<br/>…:477"]` (477–556).
* Kenarlar: `e12 -->|"finally"| e13`, `e13 --> e14`; e12 = 546, e14 = 554 —
  ikisi de `ika_gorevi`. Düğüm `ika_gorevi`'nin `finally` temizliğini anlatıyor.
* `ika_gorevi` içindeki tek `send_vel(0, 0)`: **551** (aday doğru satır).

### 3. `akis_e` · e40 — GERÇEK kayma
`e40["send_vel(0, 0)<br/>simulation/scripts/ika_nav.py:256"]`
* 256 `receiver_ika_go_bekle` içindedir (254–262), alt grafik
  `sE3["def receiver_surus_izni_bekle()<br/>…:265"]` (265–308).
* Kenarlar: `e05 -->|"hayir"| e40`, `e40 --> e41`.
* `receiver_surus_izni_bekle` içindeki tek `send_vel(0, 0)`: **276**
  (aday doğru satır).

### 4. `akis_e` · e53 — GERÇEK kayma
`e53["return False<br/>simulation/scripts/ika_nav.py:308"]`
* 308 `receiver_surus_izni_bekle`'nin SON satırıdır, alt grafik
  `sE4["def navigate()<br/>…:311"]` (311–452).
* Kenarlar: `e52 -->|"evet: sure doldu, GUVENLI DURMA"| e53`, `e53 --> e12`;
  e52 = 371 `if surus_deadline is not None and saat() >= surus_deadline:`
  (navigate içinde).
* O `if`in gövdesi: 372 `send_vel(0, 0)`, 375 `return False` → aday doğru
  satır **375**.

### 5. `akis_e` · e62 — KAYMA DEĞİL, **denetim kuralının ZİNCİR artığı**
`e62{"if route is None or no_route is not None:<br/>…ika_nav.py:220"}`
* 220 `receiver_rota_gecerli` içindedir (208–236), alt grafik `sE4` =
  `navigate`. Ama hemen önündeki `e61` (216) de aynı fonksiyonun gövdesidir ve
  o `CAGRI_GOVDESI` diye bağışlandı (ondan önce `e60["def
  receiver_rota_gecerli()<br/>…:208"]` var).
* Yani `e62`, çağrılan fonksiyonun gövdesinden çizilen **İKİNCİ** deyimdir.
  Bugünkü kural bağışıklığı bilerek "HEMEN önceki düğüm" ile sınırlıyor
  (T226-D3 belgesi: dar tutulmasının gerekçesi, bir kez görülen `def`
  düğümünün ardından gelen İLGİSİZ düğümleri bağışlamaması).
* ⚠ **T241'in kural kararı:** bağışıklık "zincir" hâline (aynı qualname'de
  ardışık gövde düğümleri) genişletilsin mi, yoksa diyagram mı `e60`ın
  gövdesini tek düğüme indirsin? İkisi de kapıyı sıkı bırakır; **bu görevde
  KARAR VERİLMEDİ.** `akis_d`'de bu vaka YOKTUR (d11 ve d96 tek deyimlik
  gövdelerdir), bu yüzden `akis_d` kapısı bu karardan etkilenmez.

## Ham çıktı

```
  HATA b10 [ALTGRAFIK]: comms/iha_komut_alici.py:822 [IhaKomutAlici.calistir] 'while not self._dur.is_set():'
       altgrafik sB2 comms/iha_komut_alici.py:797 [IhaKomutAlici.poll] KAPSAMINDA DEGIL
  CAGRI_GOVDESI b44 (comms/iha_komut_alici.py:513 [IhaKomutAlici._aktar]): altgrafik sB3 [IhaKomutAlici.isle] disinda ama HEMEN onceki cagri dugumu b43 [IhaKomutAlici._aktar] bu kapsami gosteriyor
FDR/sekiller/akis_b.mmd: ALTGRAFIK 1 (50 deyim dugumu denetlendi, 1 CAGRI_GOVDESI bagisik) [RAPOR kipi: cikis 0]
  HATA e13 [ALTGRAFIK]: simulation/scripts/ika_nav.py:450 [navigate] 'send_vel(0, 0)'
       altgrafik sE1 simulation/scripts/ika_nav.py:477 [ika_gorevi] KAPSAMINDA DEGIL
  HATA e40 [ALTGRAFIK]: simulation/scripts/ika_nav.py:256 [receiver_ika_go_bekle] 'send_vel(0, 0)'
       altgrafik sE3 simulation/scripts/ika_nav.py:265 [receiver_surus_izni_bekle] KAPSAMINDA DEGIL
  CAGRI_GOVDESI e42 (comms/ika_receiver.py:127 [IkaReceiver.wait_surus_izni]): altgrafik sE3 [receiver_surus_izni_bekle] disinda ama HEMEN onceki cagri dugumu e41 [IkaReceiver.wait_surus_izni] bu kapsami gosteriyor
  CAGRI_GOVDESI e44 (comms/ika_receiver.py:134 [IkaReceiver._surus_izni_gecerli_unlocked]): altgrafik sE3 [receiver_surus_izni_bekle] disinda ama HEMEN onceki cagri dugumu e43 [IkaReceiver._surus_izni_gecerli_unlocked] bu kapsami gosteriyor
  HATA e53 [ALTGRAFIK]: simulation/scripts/ika_nav.py:308 [receiver_surus_izni_bekle] 'return False'
       altgrafik sE4 simulation/scripts/ika_nav.py:311 [navigate] KAPSAMINDA DEGIL
  CAGRI_GOVDESI e61 (simulation/scripts/ika_nav.py:216 [receiver_rota_gecerli]): altgrafik sE4 [navigate] disinda ama HEMEN onceki cagri dugumu e60 [receiver_rota_gecerli] bu kapsami gosteriyor
  HATA e62 [ALTGRAFIK]: simulation/scripts/ika_nav.py:220 [receiver_rota_gecerli] 'if route is None or no_route is not None:'
       altgrafik sE4 simulation/scripts/ika_nav.py:311 [navigate] KAPSAMINDA DEGIL
  CAGRI_GOVDESI e71 (comms/ika_receiver.py:96 [IkaReceiver.run_if_route_valid]): altgrafik sE4 [navigate] disinda ama HEMEN onceki cagri dugumu e70 [IkaReceiver.run_if_route_valid] bu kapsami gosteriyor
  CAGRI_GOVDESI e76 (simulation/scripts/ika_nav.py:64 [surucu]): altgrafik sE5 [send_vel] disinda ama HEMEN onceki cagri dugumu e75 [surucu] bu kapsami gosteriyor
FDR/sekiller/akis_e.mmd: ALTGRAFIK 4 (45 deyim dugumu denetlendi, 5 CAGRI_GOVDESI bagisik) [RAPOR kipi: cikis 0]
```

## Ölçülemeyenler / açık kalan

* `akis_a` ve `akis_c` bu raporun kapsamında değildi (görev yalnız b ve e
  dedi). D-460 denetçisinin referans ölçümü ikisi için de 0 uyuşmazlık
  basmıştı; **bu görevde yeniden ölçülmedi → ÖLÇÜLEMEDİ, GEÇTİ değil.**
* Bu raporda hiçbir `.mmd`/`.svg`/`_dugumler.md` **düzeltilmedi**; rakamlar
  düzeltme sonrası değil, **bugünkü hâlin** ölçümüdür.
