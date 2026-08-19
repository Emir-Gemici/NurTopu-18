# FILO1 LANE 3/15 — T118 payda sozlesmesi · scripts/olcum/65_kabul_denetcisi.py
# Kosum: 2026-08-20, statik iz surme + 2 olcum kosumu (goruntu boyutlari):
#   sartname_s9_arena.png = 634x1059 (KARE DEGIL; letterbox 1059^2, icerik/tuval = 0,599)
#   raw_frames = 67 adet, 576x1024 (icerik/tuval = 0,5625)
# Yorumlayici: O:\navitas-local-train\venv\Scripts\python.exe

| dosya:satir | PAYDA NE | esige/kapiya karsi mi | esik hangi paydada kalibre |
|---|---|---|---|
| 65:126-134 `kaplama()` | LETTERBOX karesi: `mk[0].mean()` tuvalin TAMAMI uzerinde alinir; `_maskeleri_icerige_kirp` dolgu piksellerini SIFIRLAR ama dizi boyu tuval kalir. ICERIK kutusu paydasi DEGIL (karar_sozlesmesi.zemin_kaplamasi'ndan FARKLI). | Dogrudan hicbir sayisal esige degil; ciktisi K0 zincirine girer (asagida). | — |
| 65:157 `k0["figur"]` | LETTERBOX karesi (kaplama() ciktisi, FIGUR kare degil: gercek ICERIK degerinin ~0,60 kati). | Evet: `k0_gecti` icinde `figur > 0` (65:108) ve `k0_taban_orani` payi (65:75). | `>0` olcutu payda-BAGIMSIZ (0 her paydada 0). Oran icin bkz. 65:75 satiri. |
| 65:166 `oranlar` (raw_frames + copy_paste) | LETTERBOX karesi (kaplama() ciktisi). | Evet: `bos = (o <= 0)` sayimi, K0 olcutu `bos == 0` (65:108-109, D-107/D-186). | `<=0` olcutu payda-BAGIMSIZ. UYUSMAZLIK YOK. |
| 65:53-75 `k0_taban_orani` | Oran = figur_kaplama / taban. Pay: LETTERBOX karesi (65:157). Taban: `config/model_registry.json` `figur_zemin_orani=0.0049` — defterdeki `olculen` metni ("figur zemin %0,49 · raw bos 0/67 · cp bos 0/393") 65'in KENDI K0 kosumunun cikti bicimidir (n=67/393 tam kume, T110 sonrasi) => taban da AYNI `kaplama()` yolundan, yani LETTERBOX paydasinda. Pay ve payda AYNI paydada — oran tutarli. | Evet: K0_ORAN_ALT=0.5 / K0_ORAN_UST=2.0 bandi (65:49-50). | Bant OLCUMLE KALIBRE EDILMEDI — REVIEW_LOG (T110 dogrulama notu): "oran esikleri (0,5/2,0) olcumle turetilmedi, emirde verilen degerlerdir". Statusu: BELIRSIZ/verilmis; ama SADECE RAPORLAR, `gecti`ye girmez (65:47-48, 65:105-109 imza geregi oranla cagrilamaz). UYUSMAZLIK degil (pay/taban ayni payda + bloklamayan bant). |
| 65:73 `taban > 0` | Kaplama degil (defter alani sifir-kontrolu) — tek satirla gecildi. | — | — |
| 65:122 dikkat satiri | Kaplama degil (rapor metni; orani basar) — tek satirla gecildi. | Hayir (BLOKLAMAZ, D-186). | — |
| 65:207, 65:218 | Kaplama degil (rapor/JSON alan atamasi; 157/75'teki degerleri tasir) — tek satirla gecildi. | Hayir. | — |
| 65:54, 65:60, 65:69 | Kaplama degil (docstring/defter okuma; taban izi yukaridaki 53-75 satirinda) — tek satirla gecildi. | — | — |

## Capraz-payda notu (uyusmazlik DEGIL ama T118 icin onemli)
65'in `kaplama()` degeri (LETTERBOX) ile uretimin `zemin_kaplamasi()` degeri (ICERIK,
codes/karar_sozlesmesi.py:426-443) AYNI ISIMLE anilir ama paydalari FARKLIDIR:
sartname figuru icin fark carpani 0,599 (634*1059 / 1059^2), raw_frames icin 0,5625.
65 icinde bu deger hicbir ICERIK-paydali esige (or. ZEMIN_KAPLAMA_TAVANI=0.67,
karar_sozlesmesi.py:423, ICERIK paydasinda kalibre) karsi KULLANILMADIGI icin
[UYUSMAZLIK] dogmuyor; K0'in tum bloklayan olcutleri (>0, bos==0) payda-bagimsiz,
oranin pay/tabani ayni paydada. AMA 65'in bastigi "figur zemin %X" sayisi ICERIK
paydasindaki gercek kaplamanin ~0,60 kati olarak OKUNMAMALIDIR — baska bir betik bu
sayiyi ICERIK-paydali bir esikle kiyaslarsa uyusmazlik ORADA dogar (93_t106 bunu
bilerek ayni yolu ice aktarir ve ORAN kullanir; oranda payda sadelesir).

ANA BULGU: 65_kabul_denetcisi.kaplama() LETTERBOX-karesi paydasinda olcer (icerik/tuval carpani figur 0,599, raw 0,5625) ama K0'in bloklayan olcutleri (>0, bos==0) payda-bagimsiz ve 0,5/2,0 orani pay-taban ayni paydada oldugu icin dosya icinde 0 [UYUSMAZLIK] var; 0,5/2,0 bandinin kendisi olcumle kalibre edilmemis (BELIRSIZ/verilmis, bloklamayan).
ETIKET: [BILGILENDIRICI]
