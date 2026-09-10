# T235 Aşama 0 — FDA yol etiketi: ön kayıt (D-451, mimar)

**Tarih:** 10 Eylül 2026. **Ölçümden ÖNCE yazıldı; eşikler sonradan gevşetilmez.** Tasarım: `TASARIM_TASLAK.md` (tasarımcı taslağı) + `CURUTUCU_HUKMU.md` ("DÜZELTMELİ"); karar D-451.

## 0. Kapsam
Drone ile Görev Test Uçuşu (FDA; şartname `results/sartname_bosluk/sartname_metin.txt:726-745`: çoklu rotor, 20×20 m alan, Başlangıç Alanı → Hedef Alanı, ≥ 30 m, ≤ 10 dk, **İKA yok**, yanlış güzergâh 0 puan) için yayınlanan yol etiketinin doğruluğu. `results/fdr_sprint_20260910/ON_KAYIT.md` H1-K3/K5 eşikleri **aynen** kalır; T235 kapıları H1 hükmünü çeviremez. Rota–KB kayması (risk b) İKA'lı ana göreve (2027) aittir, bu ön kaydın konusu değildir.

## 1. Karşılaştırılan etiket tanımları
- **KARE** (bugünkü): `karar_sozlesmesi.serit_no` — içerik genişliğinin üçte birleri.
- **A0** (alan-ölçekli, merkez referanslı): sınırlar içerik merkezinden ±(W/6)/mpp; W = alan genişliği (FDA 20 m). Varsayım: İHA alan merkezinde bekler ve görüntü-yukarısı = Başlangıç→Hedef (T235-E: `CONDITION_YAW`, kamera montaj yaw'ı düzeltmesiyle). Poz, `hdg`, lat/lon gerekmez.
- **A1** (poz izdüşümü): İHA GPS + `hdg` + montaj yaw ile alan çerçevesine (KBH) izdüşüm; alan merkezi köşelerden. Yalnız tezgâhta karşılaştırma için; üretime bağlanması (T235-C poz kolu) ancak §2 karar kuralıyla.

## 2. Tezgâh T235-K3 (sentetik maske, render yok — benzetim/HESAP, saha ölçümü DEĞİL)
- **Izgara:** yol aralığı s ∈ {5; 6,67; 8} m · (kip, h) ∈ {(4:3, 32 m), (16:9 kırpma, 40 m)} + bilgi hücresi (16:9, 32 m) · HFOV 55,3° (HQ 6 mm, 6,287 mm) · açık yol ∈ {sol, orta, sağ} eşit.
- **Hata modeli** (bağımsız çekilişler, tohum 20260910, hücre başına 2000): bekleme konum hatası e_c ~ N(0, σ_c²) her eksende, σ_c ∈ {0,5; 1,0} m · yaw hatası ~ N(0, σ_ψ²), σ_ψ ∈ {2°; 5°} · eğim düzgün [2°, 3°], yön düzgün → yer kayması h·tan(eğim) · yalnız A1 için ek GPS kestirim hatası (e_f − e_s) ~ N(0, σ_g²) her eksende, σ_g ∈ {1,0; 2,0} m.
- **Metrik:** hücre başına doğru etiket oranı (üç yöntem **aynı çekilişlerle**).
- **Kapı (bir yöntemin FDA'da açılması):** nominal hücrelerde — s ∈ {6,67; 8}, σ_c = 1,0 m, σ_ψ = 5°, (4:3, 32) ve (16:9, 40) [A1 için σ_g = 2,0] — doğru oranı **≥ %99,0**, **VE** hiçbir hücrede KARE'den 0,5 puandan fazla kötü değil. s = 5 m hücreleri raporlanır, kapıya girmez (aralık şartnamede yok; sonuç olduğu gibi yazılır).
- **Alan sığma:** her (kip, h) için 20×20 alanın karede kalma payı raporlanır; pay < 1,0 m olan yapılandırma FDA'da kullanılmaz.
- **Negatif kontrol K3n:** KARE tanımı s = 5 m, merkezli, hatasız karede [2, 2, 2] üretmeli; üretmezse tezgâh boş sayılır ve hüküm verilmez.
- **Karar kuralı (önceden):** A0 kapıyı geçerse FDA'da A0 bayrakla açılır. A0 düşer A1 geçerse A1 yalnız T235-C poz kolu + tezgâh/SITL kanıtı 21 Eylül'den önce hazırsa açılır; değilse KARE kalır. Hiçbiri geçmezse KARE kalır. Her durumda YKS etiketin çerçevesini niteler (T235-A).

## 3. Uygulama testi T235-K1 (bağımsız kanıt DEĞİL)
A1 saf fonksiyonu yer gerçeği pozla `kosum_tur3` 20 + kerteriz 8 OPEN_ROUTE karesinde dünya yoluyla **28/28** eşleşir (Analiz C karşı-olgusunun yeniden üretimi); KARE tanımı aynı tezgâhta **3/8** ve **6/20**'yi yeniden üretir (negatif kontrol; üretmezse tezgâh boş).

## 4. FDA görev planı (T235-E) ve SITL (T236)
- Görev üreteci: 4 köşe + Başlangıç kenarı + montaj yaw → merkez = köşe ortalaması; β = Başlangıç kenarı ortası → Hedef kenarı ortası kerterizi; `NAV_LOITER_TIME` **merkezde**; `CONDITION_YAW(β − montaj_yaw)` `LOITER_TIME`'dan **SONRA** (ArduCopter DO/CONDITION komutları önceki NAV komutu sürerken koşar; `WP_YAW_BEHAVIOR=2` yeni NAV'da yaw'ı sıfırlar — çürütücü bulgusu 2). İrtifa (kip, h) seçimine göre, `FENCE` 50 m altında.
- **T236 SITL kapısı** (Windows SITL ikilisi bulunursa): bekleme süresince (ilk 10 s hariç) yatay konum merkezden **≤ 2,0 m** ve yaw β'dan **≤ ±5°** zamanın **≥ %90**'ında; irtifa hedeften **±1,0 m**. SITL koşulamazsa **ÖLÇÜLEMEDİ** (GEÇTİ değil) ve plan ilk kalkıştan önce Mission Planner simülasyonunda insanca doğrulanır (BEYAN).

## 5. Hız kapısı (T235-C'de uygulanır; ölçüt burada)
Alan-göreli etiket yalnız yer hızı **≤ 1,0 m/s** iken (karar anındaki telemetri anlık görüntüsü, tazelik ≤ 0,5 s) kullanılır; aksi hâlde KARE ve `road_cerceve = "KARE"`.

## 6. Mutasyon hedefleri (en az 7; hepsi yakalanmalı)
W/6 → W/3 · x aynası · β işareti · montaj yaw işareti · `CONDITION_YAW`'ın `LOITER_TIME` öncesine taşınması · merkez = 5. köşe · hız kapısının kaldırılması (T235-C).

## 7. FDR'ye yazım
Tezgâh sonuçları "benzetim (sentetik maske), saha ölçümü değil" etiketiyle; SITL koşulamazsa ÖLÇÜLEMEDİ. "Düzeltildi" ya da "GEÇTİ" yalnız ilgili kapı koşulduktan sonra.
