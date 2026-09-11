# T226-D2 devir kanıtı · 11 Eylül 2026

Çalışma ağacı: `O:\navitas\.claude\worktrees\wf_61640005-665-1`, HEAD `73f62435`.
Claude'un iki kaydedilmemiş değişikliği korunarak tamamlandı. Resmi mimar denetimi bekleniyor.

H2e, gerçek Tk ve UDP ile 1,0/1,5 ölçeklerde kısa/uzun NO_ROUTE sonrası üç OPEN_ROUTE
güzergâhının çizimini önceki temiz çizimle karşılaştırır; fontun gerçek özellikleri de dahildir.
H4e çizili sözleşme metnini dışlar; H2c HB etiketinin kırmızı H kutusuyla kesişmesini reddeder.
Akış denetimi tam çağrı metnini, kapsamını, tekrar sırasını, ret nedenini, silinen düğümleri ve
değiştirilen kenarları doğrular. `d78` İKA ACK reddine, `d83` bayat tespit reddine bağlandı;
tablo ve SVG de tazelendi. Ürün kodu bu turda değiştirilmedi.

## Gerçek koşular

Yorumlayıcı bütün komutlarda `O:\navitas-local-train\venv\Scripts\python.exe`.

```text
-X utf8 -B results/fdr_sprint_20260910/H9_MK15/t226/mutasyon_t226d2.py
N11..N17: 7/7 YAKALANDI (her mutant exit 1)
GERI YUKLEME SHA256 ESIT: True
TEMIZ ONCE: Ran 39 tests in 23.128s / OK / exit 0
TEMIZ SONRA: Ran 39 tests in 21.857s / OK / exit 0
SONUC: 7 mutasyon; hata=0
exit 0

-X utf8 -B results/fdr_sprint_20260910/H9_MK15/t226/kapi_t226d.py --ayna-denetle --cikti results/fdr_sprint_20260910/H9_MK15/t226/kapi_devralma_20260911.txt
Ekran: üç ardışık koşu 39/39 OK (22.369s, 21.821s, 21.706s), her biri exit 0.
İlk geniş koşu exit 1: YKS testinde 88 kompozit görsel, T202'de altı model eksikti.
İlk hata kanıtı kapi_devralma_20260911.txt ve .raw.txt içinde korunuyor.
```

Eksik 88 gerçek görsel (49.650.735 bayt) ana deponun `data/arena_kompozit/images` ağacından,
altı gerçek model (328.162.444 bayt) `jetson_paket/models` dizininden yalnız eksik hedeflere
kopyalandı. Modellerin her biri kaynakla SHA256 eş; ana kaynaklarda değişiklik yok.

Değiştirilmemiş testlerin gerçek tekrarları:

```text
-X utf8 -B -m unittest discover -s tests -p 'test_yks_*.py' -q
Ran 233 tests in 35.263s
OK
exit 0

-X utf8 -B -m unittest discover -s tests -p test_t202_jetson_paket_butunlugu.py -q
Ran 7 tests in 5.069s
OK
exit 0
```

İlk geniş koşudaki diğer kalemler: kamera köprüsü 12 OK, Jetson comms 7 OK, kamera içerik 8 OK,
ayna 6 test OK (2 atlama), diyagram testleri 13 OK; comms loopback `TEST GEÇTİ`; genel kapı
`GENEL KAPI (madde 14): GECTI — kol1 15/15 · kol2 serit 15/15`; beş diyagram `TÜM DÜĞÜMLER TUTTU`;
akış d `98 dugum · AYNI 96 · DUZELTILDI 2 · kapsam HATASI 0`, ret kenarları 3/3. Her komut exit 0.
Atlanan iki ayna testi yerel eğitim deposu ortamı ister; bu sonuçlar koşulmuş gibi sayılmadı.

`git diff --check` exit 0. Tam depo süiti, fiziksel MK15/web kamera deneyi ve Jetson ölçümü bu
turda koşulmadı. Önceki uçtan uca kanıtlar korunuyor. Commit/merge/push yapılmadı.

Son kaynak SHA256:

- `tests/test_yks_mk15_hakem_ekrani.py`: `985e9883775529597fc89a9d6391daee48469e3ad34aefd76a4a0b971323f1d5`
- `akis_kapsam_t226d.py`: `2b9650174b4debbba111638699157d12bf52bc6aa592ae39f723b7ea3f6603f2e`
- `FDR/sekiller/akis_d.mmd`: `ee3ee394ef7a8201815a51d80519a31f7c988d9eefd619b48cdb5e7c8a581904`.
