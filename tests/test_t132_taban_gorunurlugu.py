"""T132 KAPISI: K0 tabaninin GECMISI ve KIMLIGI gorunur kalir (karar D-263).

NEDEN (olcum D-261). `figur_zemin_orani` tek bir SKALERDI ve her terfide
uzerine yaziliyordu. Sonucu olculdu: sayisal taban alani v34 terfisinden SONRA
dogdu ve **v34'un anomali degeriyle tohumlandi**; iki uyari yer degistirdi —
v30->v34 gecisi YETENEK uyarisi vermeliydi vermedi (alan henuz yoktu),
v34->v35 gecisi TEHLIKELI uyarisi verdi ama olctugu sey "tehlike" degil
AYKIRI BIR TABANA UZAKLIKTI (v30 tabaniyla oran 1,13x — band ici).

🔴 BU DOSYA BIR ESIK KAPISI DEGILDIR ve oyle bir seye CEVRILMEMELIDIR.
    D-186'nin REDDETTIGI : n=1 figure MODEL uzerinde sert kural/tavan
    BURADA SINANAN       : TABANIN gecmisi SILINMIYOR mu, KIMLIGI BASILIYOR
                           mu, ESKI SKALER bicim HALA CALISIYOR mu
Model hakkinda hukum YOKTUR. Bir gun biri "eksik kalmis" deyip buraya figur
degeri icin alt/ust sinir eklerse, reddedilmis bir fikri arka kapidan geri
getirmis olur (yetki mimarindir — AGENTS.md SS9.2).

SINANAN UC SEY (emrin kendi listesi) + iki tanesi emrin otesinde:
  a) terfide gecmis SILINMIYOR                     -> taban-kilitleme kalibi
  b) basilan satir tabanin KIMLIGINI iceriyor      -> `k0_taban_metni`
  c) SKALER bicimli defter HALA CALISIYOR          -> geriye uyumluluk
  d) taban "sonuncu"dan DEGIL `model_id`den secilir (siralamaya guvenilmez)
  e) DONEM-TUTARSIZ kayitlar medyana GIRMEZ ama kayitta DURUR

⚠ Model YUKLENMEZ: yalniz `65_kabul_denetcisi` icindeki SAF fonksiyonlar
sinanir. Gercek defter yalniz OKUNUR, asla MUTASYONA UGRATILMAZ (mutasyonlar
gecici dizinlerde; D-233'un "gercek dosyaya dokunma" kurali).
"""

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
_OLCUM = KOK / "scripts" / "olcum"
if str(_OLCUM) not in sys.path:
    sys.path.insert(0, str(_OLCUM))
_spec = importlib.util.spec_from_file_location(
    "kabul_denetcisi_t132", _OLCUM / "65_kabul_denetcisi.py")
K65 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(K65)

GERCEK_DEFTER = KOK / "config" / "model_registry.json"
PAKET_DEFTERI = KOK / "jetson_paket" / "config" / "model_registry.json"

# ── TABAN (a) ───────────────────────────────────────────────────────────────
# Bu kumeden bir surum EKSILIRSE kapi duser. BUYUME serbesttir (her terfi bir
# kayit ekler) — kilitlenen sey "gecmis SILINMEZ"dir, "gecmis DONMUSTUR" degil.
# Kaynak: D-261 olcumu (119_t131_k0_taban_gecmisi.py), T132'de deftere gocuruldu.
BEKLENEN_SURUMLER = frozenset({"v17", "v20", "v21", "v24", "v27", "v30",
                               "v34", "v35", "v36"})
DONEM_TUTARLI = frozenset({"v27", "v30", "v34", "v35", "v36"})


def _defter(dizin, *, model_id, figur_alani, kume=None):
    """Gecici SENTETIK defter. Gercek dosyaya DOKUNULMAZ."""
    cfg = Path(dizin) / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    profil = {"model_id": model_id, "path": "models/x.pt", "imgsz": 512,
              "metrics": {"k0_korluk": {"figur_zemin_orani": figur_alani}}}
    if kume is not None:
        profil["kabul_kumesi"] = str(kume)
    (cfg / "model_registry.json").write_text(json.dumps({
        "schema_version": 1, "default_profile": "sinama",
        "profiles": {"sinama": profil}}), encoding="utf-8")
    return dizin


def _kayit(surum, deger, donem=True):
    return {"surum": surum, "deger": deger, "donem_tutarli": donem,
            "kaynak": "sinama"}


class GecmisSilinmiyorTests(unittest.TestCase):
    """(a) Terfide gecmis SILINMIYOR."""

    def setUp(self):
        self.veri = json.loads(GERCEK_DEFTER.read_text(encoding="utf-8"))
        self.profil = self.veri["profiles"][self.veri["default_profile"]]
        self.gecmis = self.profil["metrics"]["k0_korluk"]["figur_zemin_orani"]

    def test_gercek_defter_LISTE_bicimde(self):
        self.assertIsInstance(self.gecmis, list)
        self.assertTrue(all(isinstance(k, dict) for k in self.gecmis))

    def test_BEKLENEN_surumlerin_hicbiri_EKSILMEMIS(self):
        """Bir kayit silinirse BU test duser. Buyume serbest (yeni terfi)."""
        var = {k["surum"] for k in self.gecmis}
        eksik = sorted(BEKLENEN_SURUMLER - var)
        self.assertEqual(eksik, [], f"gecmisten kayit SILINMIS: {eksik}")

    def test_donem_tutarlilik_isareti_HER_KAYITTA_var(self):
        """Isaret kaybolursa 640 donemi sayilari DUZ KIYAS sanilir (D-261 §2)."""
        for k in self.gecmis:
            self.assertIn("donem_tutarli", k, f"{k.get('surum')}: isaret YOK")
            self.assertIsInstance(k["donem_tutarli"], bool)

    def test_donem_tutarli_kume_BEKLENDIGI_gibi(self):
        var = {k["surum"] for k in self.gecmis if k["donem_tutarli"]}
        self.assertEqual(var, set(DONEM_TUTARLI))

    def test_her_kaydin_KAYNAGI_yazili(self):
        """Geriye donuk doldurma UYDURMA olmasin: her sayinin kaynagi var."""
        for k in self.gecmis:
            self.assertTrue(str(k.get("kaynak", "")).strip(),
                            f"{k.get('surum')}: kaynak YOK")

    def test_paket_kopyasi_AYNI_bicimi_tasiyor(self):
        """Iki kopyadan biri zorlanmiyorsa ayrisma kacinilmazdir (4x tekrar)."""
        paket = json.loads(PAKET_DEFTERI.read_text(encoding="utf-8"))
        pp = paket["profiles"][paket["default_profile"]]
        self.assertEqual(pp["metrics"]["k0_korluk"]["figur_zemin_orani"],
                         self.gecmis)
        self.assertIn("kabul_kumesi_parmak_izi", pp)

    def test_MUTASYON_gecmisten_kayit_silinirse_kapi_DUSER(self):
        """POZITIF KONTROL: kural gercekten ayirt ediyor mu?"""
        eksiltilmis = [k for k in self.gecmis if k["surum"] != "v34"]
        var = {k["surum"] for k in eksiltilmis}
        self.assertTrue(BEKLENEN_SURUMLER - var,
                        "kayit silindigi halde fark EDILMEDI — kapi bos")


class TabanKimligiTests(unittest.TestCase):
    """(b) Basilan satir tabanin KIMLIGINI iceriyor."""

    def test_liste_biciminde_satir_KIMLIK_tasiyor(self):
        kayit = {"deger": 0.0049, "kimlik": "v34", "bicim": "liste",
                 "gecmis": []}
        metin = K65.k0_taban_metni(kayit, 18.29, 0.0049)
        self.assertIn("v34", metin)
        self.assertIn("%0.49", metin)

    def test_MUTASYON_kimlik_alani_kalkarsa_satirda_KIMLIK_YOK(self):
        """POZITIF KONTROL: kimlik uydurulmuyor, gercekten alandan geliyor."""
        kayit = {"deger": 0.0049, "kimlik": None, "bicim": "liste",
                 "gecmis": []}
        metin = K65.k0_taban_metni(kayit, 18.29, 0.0049)
        self.assertNotIn("v34", metin)

    def test_gercek_defterle_satir_URETIM_surumunu_yaziyor(self):
        kayit = K65.k0_taban_kaydi()
        oran, taban, notu = K65.k0_taban_orani(0.0903)
        metin = K65.k0_taban_metni(kayit, oran, taban, notu)
        self.assertEqual(kayit["kimlik"], "v36")
        self.assertIn("v36", metin)

    def test_oran_YOKSA_satir_sebebini_yazar_sayi_UYDURMAZ(self):
        metin = K65.k0_taban_metni({"deger": None}, None, None, "taban YOK")
        self.assertEqual(metin, "taban YOK")


class SkalerGeriyeUyumlulukTests(unittest.TestCase):
    """(c) ESKI SKALER bicim HALA calisir (eski defter + saha paketi)."""

    def test_skaler_defter_okunur(self):
        with tempfile.TemporaryDirectory() as d:
            _defter(d, model_id="navitas-seg-v35-512", figur_alani=0.0903)
            kayit = K65.k0_taban_kaydi(kok=d)
        self.assertEqual(kayit["deger"], 0.0903)
        self.assertEqual(kayit["bicim"], "skaler")
        self.assertIsNone(kayit["kimlik"])

    def test_skaler_defterde_ORAN_hala_hesaplanir(self):
        with tempfile.TemporaryDirectory() as d:
            _defter(d, model_id="navitas-seg-v35-512", figur_alani=0.05)
            oran, taban, _ = K65.k0_taban_orani(0.10, kok=d)
        self.assertAlmostEqual(oran, 2.0)
        self.assertAlmostEqual(taban, 0.05)

    def test_skaler_biciminde_satir_KIMLIK_YOK_diye_yazar(self):
        """Sessiz kalmaz: kimligin YOKLUGU da bir bilgidir (D-180 dersi)."""
        kayit = {"deger": 0.0903, "kimlik": None, "bicim": "skaler",
                 "gecmis": []}
        self.assertIn("kimlik YOK", K65.k0_taban_metni(kayit, 1.0, 0.0903))

    def test_MUTASYON_skaler_bozulursa_deger_NONE_ve_sebep_yazilir(self):
        with tempfile.TemporaryDirectory() as d:
            _defter(d, model_id="navitas-seg-v35-512", figur_alani="0,0903")
            kayit = K65.k0_taban_kaydi(kok=d)
        self.assertIsNone(kayit["deger"])
        self.assertTrue(kayit["not"])


class ModelIdIleAnahtarlamaTests(unittest.TestCase):
    """(d) Taban SONUNCUDAN degil `model_id`den secilir.

    D-263 §4.1 "denetci yine sonuncuyu kullanir" diyordu; T132 emri bunu
    DARALTTI. Gerekce: siralama bozulursa "sonuncu" YANLIS tabani secer ve bu,
    T131'in buldugu kusurun (sessizce kayan referans) birebir tekraridir.
    """

    def test_siralama_BOZUK_olsa_da_dogru_taban_secilir(self):
        karisik = [_kayit("v35", 0.0903), _kayit("v27", 0.0784),
                   _kayit("v34", 0.0049), _kayit("v30", 0.0796)]
        with tempfile.TemporaryDirectory() as d:
            _defter(d, model_id="navitas-seg-v34-512", figur_alani=karisik)
            kayit = K65.k0_taban_kaydi(kok=d)
        self.assertEqual(kayit["deger"], 0.0049)
        self.assertEqual(kayit["kimlik"], "v34")

    def test_MUTASYON_sonuncuyu_secseydi_YANLIS_taban_gelirdi(self):
        """POZITIF KONTROL: (d) bos bir iddia degil — iki cevap FARKLI."""
        karisik = [_kayit("v35", 0.0903), _kayit("v27", 0.0784),
                   _kayit("v34", 0.0049), _kayit("v30", 0.0796)]
        self.assertNotEqual(karisik[-1]["deger"], 0.0049,
                            "sonuncu ile model_id ayni sonucu veriyorsa bu "
                            "test hicbir seyi ayirt etmez")

    def test_uretim_surumunun_kaydi_YOKSA_fail_closed(self):
        """Yokluk ne BASARI ne BASARISIZLIK: deger None, sebep YAZILI."""
        with tempfile.TemporaryDirectory() as d:
            _defter(d, model_id="navitas-seg-v99-512",
                    figur_alani=[_kayit("v35", 0.0903)])
            kayit = K65.k0_taban_kaydi(kok=d)
        self.assertIsNone(kayit["deger"])
        self.assertIn("v99", kayit["not"])

    def test_surum_etiketi_cikarilamazsa_UYDURULMAZ(self):
        self.assertIsNone(K65.surum_etiketi("adsiz-model"))
        self.assertEqual(K65.surum_etiketi("navitas-seg-v35-512"), "v35")


class SoyagaciGorunurlugunuTests(unittest.TestCase):
    """(e) DONEM-TUTARSIZ kayitlar medyana GIRMEZ ama kayitta DURUR."""

    def test_donem_tutarsizlar_medyana_GIRMEZ(self):
        gecmis = [_kayit("v21", 0.0, donem=False), _kayit("v24", 0.3464, donem=False),
                  _kayit("v27", 0.0784), _kayit("v30", 0.0796),
                  _kayit("v34", 0.0049)]
        uzaklik, medyan = K65.taban_medyan_uzakligi(0.0049, gecmis)
        self.assertAlmostEqual(medyan, 0.0784)          # v21/v24 disarida
        self.assertAlmostEqual(uzaklik, 0.0784 / 0.0049, places=3)

    def test_soyagaci_satiri_DISARIDAKI_kayit_sayisini_yazar(self):
        gecmis = [_kayit("v21", 0.0, donem=False), _kayit("v27", 0.0784),
                  _kayit("v34", 0.0049)]
        satirlar = K65.k0_soyagaci_satirlari(
            {"deger": 0.0049, "kimlik": "v34", "bicim": "liste", "gecmis": gecmis})
        govde = "\n".join(satirlar)
        self.assertIn("v27", govde)
        self.assertIn("+1 kayit", govde)
        self.assertNotIn("v21 %0.00", govde)

    def test_uzaklik_YONSUZ_hep_1in_ustunde(self):
        gecmis = [_kayit("v27", 0.0784), _kayit("v30", 0.0796)]
        for taban in (0.0049, 0.9000):
            uzaklik, _ = K65.taban_medyan_uzakligi(taban, gecmis)
            self.assertGreaterEqual(uzaklik, 1.0)

    def test_skaler_bicimde_soyagaci_YOK_diye_yazilir(self):
        satirlar = K65.k0_soyagaci_satirlari(
            {"deger": 0.0903, "kimlik": None, "bicim": "skaler", "gecmis": []})
        self.assertIn("kayitli DEGIL", "\n".join(satirlar))

    def test_gercek_defterde_KARSI_OLGUSAL_v34_gunu_16x_gorunurdu(self):
        """T131'in cekirdek iddiasi: bu satir O GUN olsaydi aykirilik gorunurdu.

        ⚠ "O GUN" = v34 terfisinin gunu; v34'ten SONRAKI her surum (v35, v36...)
        soyagacindan CIKARILIR. Terfi geldikce buraya surum eklenir — aksi hâlde
        karsi-olgusal kendi gelecegini de sayar ve iddia sulanir.
        """
        veri = json.loads(GERCEK_DEFTER.read_text(encoding="utf-8"))
        gecmis = (veri["profiles"][veri["default_profile"]]
                  ["metrics"]["k0_korluk"]["figur_zemin_orani"])
        o_gun = [k for k in gecmis if k["surum"] not in ("v35", "v36")]
        uzaklik, _ = K65.taban_medyan_uzakligi(0.0049, o_gun)
        self.assertGreater(uzaklik, 10.0)


class ParmakIziTuretilirTests(unittest.TestCase):
    """(3) Kabul kumesinin parmak izi TURETILIR — elle liste TUTULMAZ."""

    def test_ayni_dizin_AYNI_ozeti_verir(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.txt").write_text("x", encoding="utf-8")
            self.assertEqual(K65.kume_parmak_izi(d)["ozet"],
                             K65.kume_parmak_izi(d)["ozet"])

    def test_MUTASYON_dosya_eklenince_ozet_DEGISIR(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.txt").write_text("x", encoding="utf-8")
            once = K65.kume_parmak_izi(d)
            (Path(d) / "b.txt").write_text("y", encoding="utf-8")
            sonra = K65.kume_parmak_izi(d)
        self.assertNotEqual(once["ozet"], sonra["ozet"])
        self.assertEqual((once["n"], sonra["n"]), (1, 2))

    def test_MUTASYON_dosya_boyutu_degisince_ozet_DEGISIR(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "a.txt"
            p.write_text("x", encoding="utf-8")
            once = K65.kume_parmak_izi(d)
            p.write_text("xxxx", encoding="utf-8")
        self.assertNotEqual(once["ozet"], K65.kume_parmak_izi(d)["ozet"])

    def test_dizin_YOKSA_patlamaz_sebebini_yazar(self):
        pi = K65.kume_parmak_izi(KOK / "olmayan_dizin_t132")
        self.assertEqual(pi["n"], 0)
        self.assertIsNone(pi["ozet"])
        self.assertIn("dizin yok", pi["not"])

    def test_gercek_defterde_parmak_izi_KAYITLI(self):
        veri = json.loads(GERCEK_DEFTER.read_text(encoding="utf-8"))
        pi = veri["profiles"][veri["default_profile"]]["kabul_kumesi_parmak_izi"]
        self.assertGreater(pi["n"], 0)
        self.assertTrue(str(pi["ozet"]).startswith("sha256:"))


class UyariSatiriCokertmemeliTests(unittest.TestCase):
    """🔴 T132'de EMRIN DISINDA bulunan kusur: uyari, denetciyi OLDURUYORDU.

    OLCULDU: bu betik BIR DOSYA olarak kosulup ciktisi yakalandiginda
    (pipe ya da yonlendirme) `sys.stdout.encoding` Windows'ta **cp1254** olur
    ve `k0_dikkat_satiri`nin 🔴 karakteri `UnicodeEncodeError` firlatir ->
    DENETCI COKER. Konsolda kosarken utf-8 oldugu icin insan izlerken CALISIR,
    otomasyon yakalarken DUSER. T110'un butun amaci o satiri gorunur kilmakti.
    """

    def test_DIKKAT_satiri_cp1254e_SIGMIYOR_yani_risk_GERCEK(self):
        """Once riskin var oldugunu sabitle — yoksa koruma bos bir tedbirdir."""
        satir = K65.k0_dikkat_satiri(18.29)
        with self.assertRaises(UnicodeEncodeError):
            satir.encode("cp1254")

    def test_stdout_utf8_yap_akisi_UTF8e_alir(self):
        class Sahte:
            def __init__(self): self.cagri = None
            def reconfigure(self, **kw): self.cagri = kw
        s = Sahte()
        self.assertTrue(K65.stdout_utf8_yap(s))
        self.assertEqual(s.cagri, {"encoding": "utf-8", "errors": "replace"})

    def test_reconfigure_YOKSA_patlamaz_False_doner(self):
        self.assertFalse(K65.stdout_utf8_yap(object()))

    def test_reconfigure_HATA_verirse_patlamaz(self):
        class Kizgin:
            def reconfigure(self, **kw): raise ValueError("olmaz")
        self.assertFalse(K65.stdout_utf8_yap(Kizgin()))

    def test_ICE_AKTARMA_sirasinda_stdout_DEGISTIRILMEZ(self):
        """Yan etki yasagi: modulu import eden testin stdout'u bozulmamali."""
        kaynak = (KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py").read_text(
            encoding="utf-8")
        govde = kaynak.split("def main():")[0]
        self.assertNotIn("stdout_utf8_yap()", govde,
                         "cagri modul govdesinde — ice aktarmada yan etki uretir")
        self.assertIn("stdout_utf8_yap()", kaynak.split("def main():")[1])


class ESIK_DEGISMEDI_Tests(unittest.TestCase):
    """🔴 T132 gorunurluk isiydi. Bu kapi ESIK DEGISMEDIGINI de sabitler.

    Gorunurluk isi yaparken "madem olcuyoruz bir de sinir koyalim" cazibesi
    bu projede gercek bir risk (D-186 bir kez reddetti). Asagidaki iki sayi
    degisirse kapi kirmizi yanar ve degisiklik MIMARIN karari olmadan gecmez.
    """

    def test_K0_oran_bandi_DEGISMEDI(self):
        self.assertEqual(K65.K0_ORAN_ALT, 0.5)
        self.assertEqual(K65.K0_ORAN_UST, 2.0)

    def test_oran_k0_gecti_fonksiyonuna_PARAMETRE_olarak_bile_giremez(self):
        """T110'un imza kilidi: "oran bloklamiyor" bir YORUM degil, IMZA."""
        import inspect
        parametreler = list(inspect.signature(K65.k0_gecti).parameters)
        self.assertEqual(parametreler, ["figur", "raw_bos", "cp_bos"])

    def test_soyagaci_satirlari_YALNIZ_metin_dondurur(self):
        """Gorunurluk fonksiyonu bir KARAR dondurse verdikte sizabilirdi."""
        satirlar = K65.k0_soyagaci_satirlari(
            {"deger": 0.05, "kimlik": "v9", "bicim": "liste",
             "gecmis": [_kayit("v9", 0.05)]})
        self.assertTrue(all(isinstance(s, str) for s in satirlar))


if __name__ == "__main__":
    unittest.main(verbosity=2)
