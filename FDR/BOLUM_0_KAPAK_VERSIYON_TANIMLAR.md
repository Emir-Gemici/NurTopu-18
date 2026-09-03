# ÖN KISIM — Kapak · Versiyonlar · Tanımlar ve Kısaltmalar

> Yönergenin **puanlanan bölümlerden önce** gelen zorunlu kısmı
> (`FDR_2_qNiVF.pdf` s. 1–6). Haritadaki kimlikler: `Y-0-M01…M05`.
>
> ⚠ **Metin çıkarımı uyarısı.** `results/fdr_sablon/fdr_yonerge_metin.txt`
> dosyasında yazı tipi bağ-imi (ligature) yüzünden bazı `i` harfleri `g`
> olarak çıkmıştır ("Değerlendgrme", "glgşkgn"). Aşağıdaki kısaltma listesi
> **PDF sayfalarının kendisinden** okunmuştur, çıkarılmış metinden değil.
> Bu satırları çıkarılmış metinden kopyalamayın.

---

## Y-0-M01 · Kapak sayfası

```
              İLERİ OTONOM SİSTEMLER TASARIM VE
                    OPERASYON YARIŞMASI

            FİNAL DEĞERLENDİRME RAPORU (FDR)


   TAKIM ADI   : Navitas Autonomous Systems
   TAKIM ID    : 997827
   BAŞVURU ID  : 5329027
```

⚠ **DOĞRULANACAK (kaptan):** Bu üç alan `navitas-teknofest/references/
ddr_requirements.md` içinden, **DDR döneminde** alınmıştır. KYS (Kayıt Yönetim
Sistemi) kaydıyla teyit edilmeden nihai sayılmaz. Yönerge kapağında alan adı
**"BAŞVURU ID"**dir; bizim DDR belgemizde "başvuru no" yazıyor — teyitte bu da
kontrol edilecek.

**BEYAN GEREKLİ (insan):** Kapakta kullanılacak takım logosu / görseli (varsa).

---

## Y-0-M02 · Versiyonlar

| VERSİYON | TARİH | AÇIKLAMA |
|---|---|---|
| V 1 | 03.09.2026 | İlk taslak — yönerge iskeletine taşındı, ölçülmüş içerik bağlandı |

**BEYAN GEREKLİ (insan):** Teslim edilecek sürümün numarası ve tarihi
(21.09.2026 teslimi `V n` olarak buraya eklenecek). Ara sürümler bu tabloya
satır olarak eklenir; **satır silinmez**.

---

## Y-0-M03 · Tanımlar ve Kısaltmalar

### Yönergede tanımlananlar (birebir, s. 5–6)

| kısaltma | tanım |
|---|---|
| **DDK** | Danışma ve Değerlendirme Kurulu |
| **İHA** | İnsansız Hava Aracı |
| **İKA** | İnsansız Kara Aracı |
| **HTAB** | Hedef Tespit Alan Bölgesi |
| **İHA-FB** | İHA Fırlatma Bölgesi |
| **İHA-UB** | İHA Uçuş Bölgesi |
| **İKA-KB** | İKA Konumlanma Bölgesi |
| **HB** | Hedef Bölge |
| **İHA-İB** | İHA İniş Bölgesi |
| **ÖDR** | Ön Değerlendirme Raporu |
| **DDR** | Detay Değerlendirme Raporu |
| **FDR** | Final Değerlendirme Raporu |
| **FDA** | Final Değerlendirme Aşaması |
| **FDS** | Final Değerlendirme Sunumu |
| **SGGS** | Sistem Gözden Geçirme Sunumu Teslimi |
| **UHDR** | Uçuşa Hazırlık Değerlendirme Raporu |
| **K_zorluk** | Zorluk Katsayısı |
| **m_İHA** | İHA Hafiflik Puanı |
| **t_İHA** | İHA Görev Süresi Puanı |
| **t_hazırlık** | Hazırlık Süresi Puanı |
| **m_İKA** | İKA Hafiflik Puanı |
| **m_yük** | İKA Yük Puanı |
| **t_İKA** | İKA Görev Süresi Puanı |
| **P_görev** | Görev Başarısı |
| **P** | Katılım Başarısı Puanı |
| **P_TI** | Teknik Muayene Başarı Puanı |
| **P_uçuş** | Uçuş Başarı Puanı |
| **P_centilmenlik** | Centilmenlik Başarı Puanı |
| **C_ceza** | Ceza Puanı |

### Bu raporda kullanılan ek kısaltmalar (takım tanımı)

Yönergedeki listeye ek olarak, raporun teknik bölümlerinde şu kısaltmalar
geçmektedir. Hepsi bu takımın kendi teknik terimidir; **yönergeden gelmez**
ve bir hüküm ifade etmez.

| kısaltma | tanım | nerede geçer |
|---|---|---|
| **YKS** | Yer Kontrol İstasyonu — hakem ekranı yazılımı (`comms/yks_gui.py`) | 3.3, 4 |
| **ACK** | Onay çerçevesi; `ref` (sıra no) ve `ref_tip` (hangi mesaja ait) taşır | 3.3, 4 |
| **OPEN_ROUTE / NO_ROUTE** | Açık güzergâh bulundu / bulunamadı kararı | 3.3, 4 |
| **IHA_LANDED** | İniş kanıtı çerçevesi (MAVLink `EXTENDED_SYS_STATE` kaynaklı) | 3.3, 4 |
| **HEARTBEAT** | Hat canlılık çerçevesi; `karar_yas` (algı kararının yaşı) taşır | 3.3, 4 |
| **K0…K8, K5A** | Karar zinciri kabul kapıları (sentetik arena, n=260) | 3.3, 4, 6 |
| **SiK** | 433 MHz telemetri radyo bağlantısı | 3.3 |
| **HB dedektörü** | Hedef Bölge (kırmızı branda) tespit modülü | 3.3 |
| **D-NNN** | Bu projenin kanıt defteri kaydı (`REVIEW_LOG.md`) | her yerde |
| **Ön kayıt** | Ölçüm eşiğinin **sonuç görülmeden** yazıldığı belge | 4, 6 |
| **Mutasyon kontrolü** | Kodu bilerek bozup testin düştüğünü doğrulama | 4 |

⚠ **Karışmasın:** yönergedeki **FDA** = *Final Değerlendirme Aşaması*. Bu raporun
teknik bölümlerinde `--fda` bir **yazılım bayrağıdır** ve şartname §5.3.2 "Drone
ile Görev Test Uçuşu" görev kipini açar. Aynı harfler, farklı şeyler.

---

## Y-0-M04 · İçindekiler

| bölüm | konu | puan | dosya |
|---|---|---|---|
| — | Kapak · Versiyonlar · Tanımlar ve Kısaltmalar | — | `BOLUM_0_KAPAK_VERSIYON_TANIMLAR.md` |
| **1** | Özet | 5 | `BOLUM_1_OZET.md` |
| **2** | Organizasyonel Yapı ve Proje Takvimi | 5 | `BOLUM_2_ORGANIZASYON_VE_TAKVIM.md` |
| **3** | Genel Sistem Spesifikasyonları | **40** | `BOLUM_3_SISTEM_SPESIFIKASYONLARI.md` |
| **4** | Test Faaliyetleri | 15 | `BOLUM_4_TEST_FAALIYETLERI.md` |
| **5** | Üretim Faaliyetleri | 15 | `BOLUM_5_URETIM_FAALIYETLERI.md` |
| **6** | Gereksinim İzlenebilirliği ve Değerlendirme | 10 | `BOLUM_6_GEREKSINIM_IZLENEBILIRLIGI.md` |
| **7** | Bütçe Gerçekleme Analizi | 10 | `BOLUM_7_BUTCE_GERCEKLEME.md` |
| | **TOPLAM** | **100** | |

Yardımcı dosyalar (rapora **girmez**, çalışma belgesidir):
`YONERGE_HARITASI.md` (zorunlu iskelet + boşluk analizi) ·
`ACIK_KALEMLER.md` (elle ayıklanmış açık kalemler) ·
`ACIK_KALEMLER_HAM.md` (üretilen ham liste) ·
`TAKIM_PROMPT.md` (takım üyeleri için bölüm doldurma prompt'u) ·
`README.md` (kapak notu ve yazım kuralları).

---

## Y-0-M05 · Sayfa düzeni

Yönergenin her sayfasında üstte ve altta **TASNİF DIŞI** ibaresi ve sağ altta
sayfa numarası bulunur. Bu, **PDF dizgisi** aşamasında uygulanacaktır; markdown
kaynak dosyalarında sayfa başlığı/altlığı yoktur.

**ÖLÇÜLEMEDİ:** Dizgi henüz yapılmadı. Dizgi 17 Eylül sürüm dondurmasından
sonra, 18–20 Eylül aralığında yapılacak; TASNİF DIŞI başlık/altlık, sayfa
numarası, kapak ve içindekiler o aşamada üretilecektir.
