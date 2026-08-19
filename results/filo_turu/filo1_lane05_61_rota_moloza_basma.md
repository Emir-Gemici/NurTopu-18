# FILO1 TARAMA LANE 5/15 — T118 payda sozlesmesi
# Dosya: scripts/olcum/61_rota_moloza_basma.py (grup 5, 0-indeksli, filo1_adaylar.json)
# Inceleyen: olcum/tani ajani · 2026-08-20 · yontem: statik kod okumasi (kod kosulmadi)
# On kayit okundu ve uygulandi (results/filo_turu/on_kayit.md)

Genel baglam: bu betikte ZEMIN KAPLAMASI HIC HESAPLANMAZ. Iki oran vardir ve
ikisinin de PAYDASI ayni seydir: `alan = float(iz.sum())` = r_gerekli_px ile
kalinlastirilmis ROTA IZI alani, OZGUN kare cozunurlugunde (satir 113-116:
tuvalde cizilir, icerikten kirpilir, w0×h0'a resize edilir — GT ile ayni cerceve).
Yani payda ne ICERIK kutusu, ne LETTERBOX karesi, ne ham goruntu, ne maske
toplami — "kalin rota alani"dir (kaplama-degil).

| dosya:satir | PAYDA NE | esige/kapiya karsi kullanim | esik hangi paydada kalibre |
|---|---|---|---|
| 61_rota_moloza_basma.py:18 | docstring: basma_orani = (kalin rota ∩ GT engel)/(kalin rota) — payda KALIN ROTA (kaplama-degil) | tanim satiri, esik yok | — |
| 61_rota_moloza_basma.py:102 | kayit alanlarinin None ile ilklenmesi (kaplama-degil, deger yok) | yok | — |
| 61_rota_moloza_basma.py:118 | basma_orani; payda `alan` = kalin rota (ozgun kare w0×h0) | dolayli: 128-129'daki >0.0 ve >0.05 esiklerine girer | ayni payda (asagida) |
| 61_rota_moloza_basma.py:123 | arena_disi_orani; payda AYNI `alan` (kalin rota) | dolayli: 130'daki >0.10 | ayni payda (asagida) |
| 61_rota_moloza_basma.py:127 | filtre: basma_orani is not None (kaplama-degil) | yok | — |
| 61_rota_moloza_basma.py:128 | basma_orani > 0.0 — "MOLOZA BASIYOR" siniflamasi; payda kalin rota | esik 0.0, BU DOSYADA satir 128'de tanimli; hedef "SIFIR OLMALI" (satir 137) mimarin `arena-olcum-araci` notu + D-90 bulgu 2'ye dayanir | esik kavramsal (temas=kotu), payda-bagimsiz sifir; D-90'da AYNI betik/AYNI payda ile olculdu → UYUMLU |
| 61_rota_moloza_basma.py:129 | basma_orani > 0.05 — "AGIR BASMA"; payda kalin rota | esik 0.05, BU DOSYADA satir 129'da tanimli; sonradan K3 kapisi olarak kullanildi ("AGIR BASMA (>%5) <= %3", REVIEW_LOG ~7259-7260, T68 doneminde) | K3 kapisi bu betigin D-90/D-104 kosumlarindaki degerlerle (v24 %2,4 → taban) konuldu — AYNI payda (kalin rota) → UYUMLU. 0.05 sayisinin ilk secim gerekcesi kayitlarda BELIRSIZ (D-90'da rapor kutusu olarak dogar) |
| 61_rota_moloza_basma.py:130 | arena_disi_orani > 0.10 — "ARENA DISINDA"; payda kalin rota | esik 0.10, BU DOSYADA satir 130'da tanimli; REVIEW_LOG D-90 bulgu 3 ve K4-tipi izlemede ayni betikle raporlanir | AYNI betik/AYNI payda ile izlendi → UYUMLU; 0.10 sayisinin ilk secim gerekcesi BELIRSIZ (D-90'da rapor kutusu) |
| 61_rota_moloza_basma.py:143-147 | ort/medyan/maks istatistikleri, ayni basma_orani/arena_disi_orani dizileri (kaplama-degil, salt rapor) | esik yok | — |

UYUSMAZLIK: BULUNMADI. Betigin iki oraninin pay ve paydasi ayni cercevede
(ozgun kare, kalin rota paydasi); GT maskesi de ayni w0×h0 cercevesinde uretiliyor
(satir 88 vs 114-115). Esikler (0 / 0.05 / 0.10) bu betigin kendi ciktilariyla
(D-90, D-104, T68 K2/K3 kapilari) ayni paydada kalibre edilmis. ZEMIN_KAPLAMA_TAVANI
(0.67, ICERIK paydasi) bu dosyada gecmiyor — T118'in ana suphesiyle kesisim yok.
NOT (bilgilendirici): 0.05 ve 0.10 sayilarinin ILK secim gerekcesi izlenemedi
(BELIRSIZ); ama kalibrasyon-kullanim payda tutarliligi saglam.
