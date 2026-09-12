# Belge kilidi denetimi — ACIK KILITLER (T240, D-460 karar 2)

Uretici: `scripts/belge_kilidi_denetle.py` (salt okuma, AST). **KAPI DEGILDIR** —
cikis her zaman 0. Her markdown dizgesi bir HUKUM kilidi degildir; liste,
`tests/belge_kilidi.py` ortak yardimcisindan GECMEYEN belge taramalarini gorunur kilar.

| olcum | deger |
|---|---|
| taranan test dosyasi | 206 |
| markdown okuyup dizge arayan | 58 |
| ortak yardimcidan GECEN | 5 |
| ACIK (yardimci kullanmayan) | 53 |
| ACIK **ve** kendi cizik kalibi olan (agir) | 4 |

## 1. Ortak yardimcidan gecenler

- `tests/test_belge_kilidi.py`
- `tests/test_faz_b_arduplane_sablon.py`
- `tests/test_isaretli_gosterici.py`
- `tests/test_t235_alan_etiketi.py`
- `tests/test_yks_mk15_hakem_ekrani.py`

## 2. ACIK kilitler — kendi cizik/hukum kalibini tasiyanlar (once bunlar)

Bu dosyalar markdown okuyup dizge ariyor **ve** kaynaginda cizme sozdizimi gecen bir
sabit var: D-460'ta olculen kacis sinifina (`~~` disindaki cizikler) acik olabilirler.

| test | kendi cizik izi | tarama |
|---|---|---|
| `tests/test_fdr_bolum4_6eylul_kaniti.py` | `~~` | `assertIn`, `assertNotIn`, `assertRegex`, `findall`, `in` |
| `tests/test_fdr_sarkan_atif_kapisi.py` | `~~` | `count`, `findall`, `finditer`, `in`, `match` |
| `tests/test_gece_ika_baglanti_semasi.py` | `~~` | `assertIn`, `assertNotRegex`, `assertRegex`, `find`, `findall` |
| `tests/test_t220_jetson_istekleri.py` | `~~` | `assertIn`, `assertNotIn`, `assertNotRegex`, `assertRegex`, `in` |

## 3. ACIK kilitler — digerleri

Cogu yol adi / komut ornegi / baslik navigasyonu olabilir; hukum kilidi olanlar
ayri ayri incelenip yardimciya gecirilmelidir.

| test | tarama cagrilari |
|---|---|
| `tests/test_163_b4_olcum_nobetcisi.py` | `assertIn`, `assertNotIn`, `count`, `in` |
| `tests/test_164_fp16_nobetcisi.py` | `assertIn`, `count` |
| `tests/test_166_infer_size_nobetcisi.py` | `assertIn`, `assertNotIn`, `count` |
| `tests/test_167_fdr_kanit_nobetcisi.py` | `assertIn`, `assertNotIn`, `count` |
| `tests/test_akis_kapsam_korumasi.py` | `assertIn`, `assertNotIn`, `assertRegex`, `count`, `match` |
| `tests/test_atolye_test_gunu.py` | `assertIn`, `assertNotIn`, `assertNotRegex`, `assertRegex`, `findall`, `finditer` |
| `tests/test_b2_fda_butcesi.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_conf_esigi_supurmesi.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_d373_defter_geri_isaret.py` | `assertIn`, `count`, `findall`, `in`, `match`, `search` |
| `tests/test_defter_butunlugu.py` | `findall` |
| `tests/test_depo_koku_turetilir.py` | `assertIn`, `assertNotIn`, `in`, `search` |
| `tests/test_faz_b_bellek_hazirla.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_faz_b_jetson_baslat.py` | `assertIn`, `assertNotIn`, `assertRegex`, `find`, `findall`, `in` |
| `tests/test_faz_b_kamera_koprusu.py` | `assertIn`, `assertNotIn`, `in`, `search` |
| `tests/test_faz_b_nano_kurulum.py` | `assertIn`, `assertNotIn`, `count`, `findall`, `in`, `index` |
| `tests/test_faz_b_pixhawk_sablon.py` | `assertIn`, `assertNotIn`, `find`, `findall`, `in`, `match` |
| `tests/test_faz_b_surum_dondurma.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_faz_b_yks_fda_kipi.py` | `assertIn`, `in` |
| `tests/test_fdr_takvim_kapisi.py` | `assertIn`, `assertRegex`, `in`, `index`, `search` |
| `tests/test_gece_akis_diyagramlari.py` | `assertIn`, `assertNotIn`, `in`, `match` |
| `tests/test_gece_baglanti_semasi.py` | `assertIn`, `assertNotRegex`, `find`, `findall`, `in`, `index` |
| `tests/test_gece_sekiller.py` | `assertIn`, `assertRegex`, `find`, `findall`, `in`, `index` |
| `tests/test_k1_tazelik_damgasi.py` | `assertIn`, `assertNotIn`, `in`, `search` |
| `tests/test_kilavuz_gecis_yordami.py` | `assertIn`, `find`, `findall`, `in`, `index` |
| `tests/test_kilavuz_kurulum_yordami.py` | `assertIn`, `in`, `search` |
| `tests/test_p3_ika_surucu.py` | `assertIn`, `in` |
| `tests/test_p4_runbook.py` | `assertIn`, `assertNotIn`, `in`, `index` |
| `tests/test_p5_h1c_damgasi.py` | `assertIn`, `assertNotIn`, `index` |
| `tests/test_p5_histerezis.py` | `assertNotIn`, `count`, `find`, `in` |
| `tests/test_pixhawk_firmware_yolu.py` | `assertIn`, `assertNotRegex`, `assertRegex` |
| `tests/test_runbook_komutlari_kosuyor.py` | `assertIn`, `findall`, `in`, `search` |
| `tests/test_saha_kosum_kagidi.py` | `assertIn`, `assertNotIn`, `assertNotRegex`, `assertRegex`, `find`, `findall` |
| `tests/test_sim_mujoco_olcum.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_sim_mujoco_video.py` | `assertIn`, `in` |
| `tests/test_sim_mujoco_zincir.py` | `assertIn`, `assertNotIn`, `in`, `index`, `search` |
| `tests/test_t123_gecis_provasi.py` | `assertIn`, `assertNotIn`, `find`, `findall`, `in`, `search` |
| `tests/test_t132_taban_gorunurlugu.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_t141_rota_yoksa_surme.py` | `assertIn`, `find`, `match`, `search` |
| `tests/test_t143_turev_ve_kamera.py` | `assertIn`, `in` |
| `tests/test_t158_kilavuz_kapisi_dongu.py` | `assertIn`, `assertNotIn`, `in` |
| `tests/test_t163_cozunurluk_sozlesmesi.py` | `assertIn`, `findall`, `in`, `index` |
| `tests/test_t191_veri_kaynaklari_taze.py` | `assertIn`, `findall`, `in`, `search` |
| `tests/test_t202_jetson_paket_butunlugu.py` | `assertIn`, `assertNotIn`, `findall`, `in` |
| `tests/test_uretim_modeli_hizasi.py` | `assertIn`, `assertNotIn`, `findall`, `in`, `match`, `search` |
| `tests/test_wheels_sayisi_belgelerle_tutarli.py` | `assertIn`, `assertNotRegex`, `in`, `search` |
| `tests/test_yarisma_adi_kapisi.py` | `assertIn`, `assertRegex`, `in`, `search` |
| `tests/test_yks_gui_uretim_hizasi.py` | `assertIn`, `assertNotIn`, `findall`, `in` |
| `tests/test_yks_hakem_kanit_olaylari.py` | `assertIn`, `findall`, `in`, `index` |
| `tests/test_yks_sik_yordami.py` | `assertIn`, `index`, `search` |

