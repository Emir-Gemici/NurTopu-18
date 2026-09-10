# H3 · T217 kanıtları — İKA entegrasyon planı (yazılım kolu) · Y-3.2.1-T06 fonksiyonel tablo · İKA renk kodlu şema (DDR tasarımı)

Ön kayıt: `results/fdr_sprint_20260910/ON_KAYIT.md` H3; kapsam kararı D-439 §3 (FDR'de yalnız yazılım),
İKA hattı beyanı D-439 §2 ("kod neyse o"). Bu görevde **üretim kodu değişmedi**; CONTRACTS §4 ve
`ika_nav.py` T213-B'nin (dokunulmadı). Tümü ölçümden yazılır; elle düzenlenmez.

## Koşum komutları (venv python)

```
python -B scripts/ika_surucu_kabul.py --surucu sahte  --json-dosya results/fdr_sprint_20260910/H3/ika_surucu_kabul_sahte.json
python -B scripts/ika_surucu_kabul.py --surucu gazebo      # gz PATH'te yok -> DUSTU (exit 1), kaydedildi
python -B scripts/ika_surucu_kabul.py --surucu gercek      # DONANIM_YOK -> SURUCU_KURULAMADI (exit 2), kaydedildi
python -B scripts/fdr_ika_baglanti_svg.py                  # FDR/sekiller/ika_baglanti.svg + ika_baglanti_kaynaklar.md
python -B scripts/fdr_ika_baglanti_svg.py --dogrula        # disk == üretim (0/1)
python -B -m unittest discover -s tests -p test_gece_ika_baglanti_semasi.py
python -B scripts/fdr_acik_kalem_cikar.py                  # ACIK_KALEMLER_HAM.md yeniden sayım
```

| dosya | ne |
|---|---|
| `ika_surucu_kabul_sahte.txt` / `.json` | K1–K6 kabul turu, SahteSurucu: **6/6 GEÇTİ, exit 0** (10 Eylül; sabah yeniden koşuldu, JSON bayt-eş) |
| `ika_surucu_kabul_gazebo_gz_yok.txt` | aynı tur GazeboSurucu: `gz` yok → K1/K3/K4/K6 DÜŞTÜ, K5 ATLANDI, **exit 1** (düştüğü gibi yazıldı) |
| `ika_surucu_kabul_gercek_donanim_yok.txt` | aynı tur GercekSurucu: arka uç yok → **DONANIM_YOK, exit 2**, tur başlamadı |
| `../../../FDR/sekiller/ika_baglanti.svg` | İKA şeması — 16 hat, **hepsi kesik "DDR tasarımı, tedarik yok"**, ölçülmüş 0 |
| `../../../FDR/sekiller/ika_baglanti_kaynaklar.md` | hat başına DDR şekil/tablo atfı; DDR içi çelişkiler ⚠ (K06, K07, K12, K13, kart adı) |

## FDR'ye giren metin

- `FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` §3.3.1.1: eski "İKA için şema yoktur" ~~çizili~~, şema gömülü, ÖLÇÜLEMEDİ/BEYAN satırları.
- §3.3.1.3.3: eski BEYAN ~~çizili~~; (1) katman zinciri tablosu (dosya:satır), (2) kabul turu çıktısı birebir, (3) donanım gelince 6 adım, (4) protokol beyanı DDR MAVLink ↔ kod NAVITAS çerçeve (gerekçe + H2 ölçümü).
- §3.3.1.3.4 (yeni): Y-3.2.1-T06 fonksiyonel arayüz tablosu F1–F11 (fiziksel satırlar F9–F11 BEYAN GEREKLİ); §3.2.1.4 / §3.2.2 / §3.2.3 `T06` satırları KISMEN + bu tabloya işaret.
- §3.4.2 ASCII bloğu ve Kanıt dizini (3 satır); `FDR/YONERGE_HARITASI.md` Y-3.3.1-M01 / M03 / Y-3.2.1-T06 + boşluk özeti 3.2 satırı; `FDR/ACIK_KALEMLER.md` kalem 31.

## Doğrulama notu (DDR okuması)

`rapor/3.3.1-2-3-4_SON.docx` içindeki 24 görsel sırayla çıkarıldı; Şekil 3.3.1.5 (İKA Bağlantı Şeması),
Şekil 3.3.2.10 (kart şematiği) ve Şekil 3.3.3.2 (güç dağıtımı) görsel olarak okundu — pin adları
(PA9/PA10 ↔ GPIO14/15, PA2/PA3 ↔ SiK, PB6/PB7/PC5 ↔ MPU6050, PC0–PC3 ↔ HC-SR04, PA5 ADC1_IN5, ECHO1/2
1k/2k bölücü, XL4015E1 buck, "Vet36") şemayla uyuştu. Metin iddiaları (Tablo 3.3.5.9 Hat-3 115200,
Tablo 3.3.5.13 0xAA 0x55/CRC8, Tablo 3.3.3.3 12/18/22/24 AWG ve 13,21 / 3,75 A, "5 saniye" hat kaybı,
"İKA'da RC alıcısı bulunmadığından", Tablo 3.3.5.19 Vet36/Vet06 · IMX477/IMX708 · PA2/PA3) python-docx
metin aramasıyla bulundu. Görseller repoya konmadı (kullanıcı belgesi, salt okunur).

SINIRLAR: İKA fizikte sürülmedi (H1-K5 → T213-B MuJoCo); RF hattı ölçülmedi; kabul turu SahteSurucu
ile sözleşme kanıtıdır, araç kanıtı değil; `MAX_SPEED=2.0` çıktıda kalır (T213-B 1,3'e çekiyor).
