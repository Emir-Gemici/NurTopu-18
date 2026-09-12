"""T244 (D-462 A/D/E) — FDR Bölüm 3/4 İÇ ÇELİŞKİ NÖBETÇİSİ.

NEDEN (ölçülen kusur örüntüsü): FDR kendi **kapanmış** kalemlerini "açık kalem /
ölçülecek" diye gösteriyordu (D-462 A1–A6); bir ölçüm elde olduğu hâlde sonucu kötü
diye rapora hiç girmemişti (D-462 E); simülasyonun üretimde olmayan iki yardımı
sınırlar paragrafında yazılı değildi (D-462 D). Bu kapı, T244'te düzeltilen sekiz
yüzeyin her birini **kaynağından** (kod satırı, artefakt JSON, ikinci FDR belgesi)
yeniden bağlar ve çelişkinin sessizce geri gelmesini engeller.

  T1  §3.3.1.1.8 MAVLink tek-yazar kilidi: üç sürecin de kodda kilitli olduğu
      yazılı; eski "açık kalemdir" cümlesi YALNIZ çizili; atıflar gerçek kod
      satırlarıyla (`comms/inis_kaniti.py` + üç süreç) doğrulanır; 6 Eylül'de de
      koşulmadığı yazılı (ÖLÇÜLEMEDİ ≠ GEÇTİ)
  T2  §3.3.4.1.7 H1c damgası KOŞULDU/GEÇTİ; H1 %40 hükmü DÜŞTÜ KALIR; %40 ölçütü
      metinde TAM BİR KEZ (rakip eşik yok); sayılar `olcum_20260903.json`'dan
  T3  §3.3.4.2.1 künye + denklik notu + §3.4.1 A3 + Kanıt dizini: `.engine` sha
      kayıt defteriyle birebir; D-303 3/126 DÜŞTÜ hükmü üç yerde de olumluya
      çevrilmemiş; `DERLENINCE_YAZILIR` yalnız çizili
  T4  §4.4 girişi ölçülen/ölçülemeyen sayımıyla; 9 ekipman satırı; 6 Eylül
      hücreleri (döküm, ESC kalibrasyonu, pil, RC failsafe) dosya:satır ile
  T5  §4.8.3 · §4.1.3 · §4.13.3: "ölçülecek" cümleleri çizili, yerlerine 6 Eylül
      koşumları; systemd kipleri hâlâ ÖLÇÜLEMEDİ (yanlış kapanma yok)
  T6  §4.0 ↔ `YONERGE_HARITASI.md`: Y-4-M01…M12 durumları HİZALI (çelişki bir daha
      sessizce oluşamaz)
  T7  DÜRÜSTLÜK: simülasyonun iki yardımı + "İYİMSER ÜST SINIRDIR" cümlesi hem
      §3.3.3.2 hem §4.7'de ve ÇİZİLMEMİŞ; kod satırları doğrulanır
  T8  §3.3.4.2.8 (a) SENTETİK ışık/gölge kesiti: v2/v3 sayıları `k3b` artefaktından;
      "saha değil" ve D-441 öncesi yerleşim sınırı yazılı; §4.8 ve §4.8.4 tazelenmiş
  M1…M6  kurallar sentetik metinle iki yönde sınanır (boş kapı olmasın)

BELGE KİLİDİ (D-453 / D-460 / D-461): tüm aramalar **normalleştirilmiş** metinde
yapılır — çizili aralıklar (`~~…~~`, tek tilde, `<del>/<s>/<strike>`) **ayıklanır**
(içerik silinir), kalın/italik/kod işaretleri ve tipografik kesme/tırnak/tire
düzleştirilir, Türkçe harfler ASCII'ye katlanır, eş anlamlı geri dönüşler tek
belirtece indirilir. Beyaz liste: bu üç çizme sözdizimi dışında çizme işareti
kalırsa kilit DÜŞER (yeni sözdizimi kalıp eklemeden yakalanır). "≈/~" yaklaşık
işareti tek istisnadır ve ayrıca sınanır.

⚠ NOT: kanonik `tests/belge_kilidi.py` şu an T240 dalında yazılıyor ve master'da
YOK. Bu dosyadaki normalleştirme fonksiyonları **tek yerde** (aşağıdaki
"BELGE KİLİDİ" bloğu) toplanmıştır ve **T242 ile kanonik yardımcıya geçirilecektir**;
kalıcı bir ikinci normalleştirme kopyası bırakılmaz.
"""

import json
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
B3 = FDR / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"
B4 = FDR / "BOLUM_4_TEST_FAALIYETLERI.md"
YONERGE = FDR / "YONERGE_HARITASI.md"
KAYIT = KOK / "config" / "model_registry.json"
ENGINE_JSON = (KOK / "results" / "jetson_20260906" / "jetson_log_20260906"
               / "engine_karar_denkligi.json")
H1C_JSON = KOK / "results" / "p5_histerezis" / "olcum_20260903.json"
K3B = KOK / "results" / "fdr_sprint_20260910" / "H1" / "k3b"
INIS = KOK / "comms" / "inis_kaniti.py"
PARAM = KOK / "config" / "pixhawk" / "arducopter_fda_20260906.param"


# ─────────────────────────────────────────────────────────────────────────────
# BELGE KİLİDİ — normalleştirme (TEK YER; T242 ile tests/belge_kilidi.py'ye geçer)
# ─────────────────────────────────────────────────────────────────────────────

# Beyaz liste: kabul edilen ÜÇ çizme sözdizimi. Çizili içerik AYIKLANIR (silinir),
# böylece çizilmiş bir iddia kilidi DOYURAMAZ.
_CIZIK_TILDE2 = re.compile(r"~~.+?~~", re.S)
_CIZIK_ETIKET = re.compile(r"<(del|s|strike)\b[^>]*>.*?</\1\s*>", re.S | re.I)
# Tek tilde (GFM yan-kanat kuralı): açan `~` boşlukla/satır başıyla önceli ve
# boşluksuz takipli; kapatan `~` boşluksuz öncelli. UZUNLUK SINIRI YOKTUR (D-461:
# `{1,40}` sınırı 40 karakterden uzun çiziği görmüyordu).
_CIZIK_TILDE1 = re.compile(r"(?<![~\w])~(?![~\s])[^\n~]+?(?<![~\s])~(?![~\w])")
# "yaklaşık" işareti çizme DEĞİLDİR: `~18:45`, `~%6`, `~1,35` — tek istisna.
_YAKLASIK = re.compile(r"(?<![\w~])~(?=[\d%.,])")
# Beyaz listede olmayan her çizme işareti (yeni sözdizimi kalıpsız yakalanır).
_CIZME_ARTIGI = re.compile(r"~|</?\s*(?:del|s|strike)\b", re.I)

_KATLAMA = str.maketrans("İIıĞğÜüŞşÖöÇçÂâÎî", "IIiGgUuSsOoCcAaIi")
_TIPOGRAFI = {
    "’": "'", "‘": "'", "“": '"', "”": '"',
    "–": "-", "—": "-", "−": "-", "­": "", "​": "",
    " ": " ", "…": "...",
}
# Eş anlamlı geri dönüşler tek belirtece iner (D-460 RED-2 / D-454 sınıfı).
_ESANLAM = (
    (r"\bEN AZ\b|≥|>=", " >= "),
    (r"\bASAN\b|\bASARSA\b", " > "),
    (r"\bOLCULMEDI\b|\bOLCULEMEZ\b|\bOLCUM YOK\b", "OLCULEMEDI"),
    (r"\bDOGRULANDI\b|\bKANITLANDI\b|\bTEYIT EDILDI\b|\bBASARILI OLDU\b|\bTUTAR\b|\bTUTUYOR\b",
     "OLUMLU_HUKUM"),
    (r"\bGECTI\b|\bGECER\b|\bSAGLANDI\b", "GECTI"),
)
# Kabul yüzeyinde ÇELİŞKİLİ İKİNCİ HÜKÜM sözcükleri (D-461 karar (d)).
CELISKI_SOZCUKLERI = (
    "GOZDEN GECIRILMIS", "GUNCELLENMIS KAPI", "KURAL KALDIRILDI",
    "ESIK GUNCELLENDI", "OLCUT GEVSETILDI", "YENIDEN DEGERLENDIRILDI",
    "BU KURAL UYGULANMAZ", "ARTIK GECERLI DEGIL",
)


def cizikleri_ayikla(metin):
    """Beyaz listedeki üç çizme sözdiziminin İÇERİĞİNİ siler."""
    metin = _CIZIK_TILDE2.sub(" ", metin)
    metin = _CIZIK_ETIKET.sub(" ", metin)
    return _CIZIK_TILDE1.sub(" ", metin)


def cizme_artiklari(metin):
    """Ayıklamadan sonra kalan çizme işaretleri (yaklaşık işareti hariç)."""
    kalan = _YAKLASIK.sub("", cizikleri_ayikla(metin))
    return _CIZME_ARTIGI.findall(kalan)


def katla(metin):
    """Türkçe harfleri ASCII'ye katlar ve büyütür (aramada yazım farkı kalmasın)."""
    return metin.translate(_KATLAMA).upper()


def normalles(metin, cizigi_at=True):
    """Kilit araması için kanonik metin: çizik ayıkla → tipografi → vurgu → katla.

    Satır yapısı KORUNUR (satır bazlı denetimler için). Alt çizgi SİLİNMEZ —
    `NO_ROUTE`, `BATT_VOLT_MULT`, `gorev_kosumu.py` gibi belirteçler bozulmasın.
    """
    if cizigi_at:
        metin = cizikleri_ayikla(metin)
    metin = metin.replace("\r\n", "\n")
    for a, b in _TIPOGRAFI.items():
        metin = metin.replace(a, b)
    metin = re.sub(r"[*`]+", "", metin)           # kalın/italik/kod işaretleri
    metin = katla(metin)
    for kalip, yerine in _ESANLAM:
        metin = re.sub(kalip, yerine, metin)
    return re.sub(r"[ \t]+", " ", metin)


def tekhat(metin, cizigi_at=True):
    """`normalles` + TÜM boşluk dizileri tek boşluğa iner (satır kırığı aramayı bozmasın)."""
    return re.sub(r"\s+", " ", normalles(metin, cizigi_at)).strip()


def oku(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def kesit(metin, bas, son=None):
    """`bas` çapasından `son` çapasına kadar olan HAM metin (son yoksa dosya sonu)."""
    i = metin.index(bas)
    j = metin.index(son, i + len(bas)) if son else len(metin)
    return metin[i:j]


def adet(metin, aranan):
    """Normalleştirilmiş (tek hatlı) metinde `aranan`ın geçiş sayısı."""
    return tekhat(metin).count(tekhat(aranan))


def eksikler(metin, gerekli):
    """gerekli = ((metin, tam_adet), ...) → kural ihlali listesi."""
    kusur = []
    for aranan, bekleyen in gerekli:
        bulunan = adet(metin, aranan)
        if bulunan != bekleyen:
            kusur.append("{!r}: {} kez (beklenen {})".format(aranan[:60], bulunan, bekleyen))
    return kusur


def yasaklar(metin, yasak):
    """Normalleştirilmiş metinde bulunmaması gereken ifadeler."""
    n = tekhat(metin)
    return ["{!r} normalleşmiş metinde VAR".format(y[:60]) for y in yasak if tekhat(y) in n]


def celiskili_ikinci_hukum(metin):
    n = tekhat(metin)
    return [s for s in CELISKI_SOZCUKLERI if s in n]


# ─────────────────────────────────────────────────────────────────────────────
# Kilitlenen yüzeyler
# ─────────────────────────────────────────────────────────────────────────────

def b3(bas, son=None):
    return kesit(oku(B3), bas, son)


def b4(bas, son=None):
    return kesit(oku(B4), bas, son)


# T244'ün kilitlediği YÜZEYLER — beyaz liste ve çelişkili ikinci hüküm denetimi
# hepsinde TOPLUCA koşar (yeni bir yüzey eklenince kapı da kendiliğinden kapsar).
def kilitli_yuzeyler():
    return (("3.3.1.1.8", b3("##### 3.3.1.1.8 ", "##### 3.3.1.1.9 ")),
            ("3.3.3.2", b3("#### 3.3.3.2 ", "#### 3.3.3.3 ")),
            ("3.3.4.1.7", b3("##### 3.3.4.1.7 ", "##### 3.3.4.1.8 ")),
            ("3.3.4.2.1", b3("##### 3.3.4.2.1 ", "##### 3.3.4.2.2 ")),
            ("3.3.4.2.8", b3("##### 3.3.4.2.8 ", "#### 3.3.4.3 ")),
            ("3.4.1", b3("### 3.4.1 ", "### 3.4.2 ")),
            ("4.0", b4("## 4.0 ", "## 4.1 ")),
            ("4.1.3", b4("### 4.1.3 ", "## 4.2 ")),
            ("4.4", b4("## 4.4 ", "## 4.5 ")),
            ("4.7", b4("## 4.7 ", "## 4.8 ")),
            ("4.8 girişi", b4("## 4.8 ", "### 4.8.1 ")),
            ("4.8.3", b4("### 4.8.3 ", "### 4.8.4 ")),
            ("4.8.4", b4("### 4.8.4 ", "## 4.9 ")),
            ("4.13.3", b4("### 4.13.3 ", "#### 4.13.3.1 ")))


class T0_CapaDosyalar(unittest.TestCase):
    def test_capa_dosyalar_var(self):
        for p in (B3, B4, YONERGE, KAYIT, ENGINE_JSON, H1C_JSON, INIS, PARAM):
            self.assertTrue(p.is_file(), p)
        for ad in ("taban_15harita.json", "v1_15harita.json", "v2_15harita.json",
                   "v3_15harita.json", "v1_15harita_yerlesim_d441.json", "ozet_k3b.json"):
            self.assertTrue((K3B / ad).is_file(), K3B / ad)

    def test_cizme_isareti_beyaz_liste(self):
        """Kilitli yüzeylerde beyaz listede OLMAYAN çizme işareti kalmamalı."""
        for ad, m in kilitli_yuzeyler():
            self.assertEqual([], cizme_artiklari(m), ad)

    def test_celiskili_ikinci_hukum_HICBIR_yuzeyde_yok(self):
        """D-461 (d): kabul yüzeyine çelişkili/gevşetici ikinci hüküm yazılamaz."""
        for ad, m in kilitli_yuzeyler():
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)


class T1_MavlinkTekYazarKilidi(unittest.TestCase):
    def _b(self):
        return b3("##### 3.3.1.1.8 ", "##### 3.3.1.1.9 ")

    def test_T1_uc_surecte_de_kodlu_yazili(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("kilit ÜÇ SÜREÇTE DE KODLUDUR", 1),
            ("tests/test_seri_pixhawk_kilidi.py", 1),
            ("13/13", 1),
        )))
        # Eski "açık kalem" hükmü YALNIZ çizili olabilir: ayıklanmış metinde olmamalı
        self.assertEqual([], yasaklar(m, ("açık kalemdir", "hâlâ kabul eder")))

    def test_T1b_atiflar_gercek_kod_satirlariyla(self):
        """Rapordaki `dosya:satır` atıfları kaynakta gerçekten o satırda."""
        m = tekhat(self._b())
        inis = oku(INIS).splitlines()
        for ad, satir in (("SERI_PIXHAWK_BILEREK_BAYRAGI", 101),
                          ("def seri_pixhawk_yolu_mu", 107),
                          ("def seri_pixhawk_kilit_metni", 122),
                          ("def seri_pixhawk_bayragini_ekle", 129),
                          ("def seri_pixhawk_kilidini_uygula", 136)):
            self.assertTrue(inis[satir - 1].startswith(ad), (ad, satir, inis[satir - 1][:40]))
        self.assertIn("COMMS/INIS_KANITI.PY:101-143", m)
        for dosya, ekle, uygula in (
                (KOK / "codes" / "rpi_inference.py", 2539, 2684),
                (KOK / "comms" / "iha_inis_yayinci.py", 432, 475),
                (KOK / "comms" / "iha_komut_alici.py", 855, 899)):
            satirlar = oku(dosya).splitlines()
            self.assertIn("seri_pixhawk_bayragini_ekle", satirlar[ekle - 1], (dosya.name, ekle))
            self.assertIn("seri_pixhawk_kilidini_uygula", satirlar[uygula - 1], (dosya.name, uygula))
            self.assertIn(":{}".format(ekle), m, (dosya.name, ekle))
            self.assertIn(":{}".format(uygula), m, (dosya.name, uygula))

    def test_T1c_6_eylul_de_kosulmadi_gecti_yazilmaz(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("6 Eylül'de de", 1),
            ("jetson_baslat.sh --kuru", 1),
            ("çıkış 3", 1),
        )))
        n = tekhat(m)
        self.assertIn("OLCULEMEDI", n)
        self.assertNotIn("MAVLINK_DOGRULA 3/3 GECTI", n)
        self.assertEqual([], celiskili_ikinci_hukum(m))


class T2_H1cDamgasi(unittest.TestCase):
    def _b(self):
        return b3("##### 3.3.4.1.7 ", "##### 3.3.4.1.8 ")

    def test_T2_h1c_kosuldu_ve_gecti(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("H1c 3 Eylül 2026'da KOŞULDU ve GEÇTİ", 1),
            ("H1 %40 hükmü DÜŞTÜ olarak KALIR", 1),
            ("tests/test_p5_h1c_damgasi.py", 1),
            ("23/23", 1),
        )))
        self.assertEqual([], yasaklar(m, ("damgalanmadı",)))
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T2b_sayilar_artefakttan(self):
        d = json.loads(H1C_JSON.read_text(encoding="utf-8"))
        self.assertTrue(d["H1c"])
        self.assertFalse(d["H1_ozgun"])
        m = tekhat(self._b())
        for tohum in ("7", "42"):
            t = d["tohumlar"][tohum]
            self.assertEqual(0, t["h1c_siniflandirilamayan"], tohum)
            siniflar = t["h1c_yayin_cevrilme_siniflari"]
            self.assertEqual(t["yayimlanan_cevrilme"], sum(siniflar.values()), tohum)
            for ad, sayi in siniflar.items():
                self.assertIn("{} {}".format(katla(ad), sayi), m, (tohum, ad))

    def test_T2c_esik_TEKLIGI_rakip_esik_yok(self):
        """D-461: ön kayıtlı ölçüt metinde TAM BİR KEZ; ikinci/gevşek eşik yasak."""
        n = tekhat(self._b())
        self.assertEqual(1, n.count("HAM CEVRILMENIN %40'I"), "H1 ölçütü tam bir kez geçmeli")
        oranlar = set(re.findall(r"HAM CEVRILMENIN %(\d+)", n))
        self.assertEqual({"40"}, oranlar, "rakip eşik (ikinci yüzde) var")


class T3_EngineDenkligi(unittest.TestCase):
    def _kunye(self):
        return b3("##### 3.3.4.2.1 ", "##### 3.3.4.2.2 ")

    def _a3(self):
        satir = [s for s in oku(B3).splitlines() if s.startswith("| A3 |")]
        self.assertEqual(1, len(satir), "§3.4.1 A3 satırı tek olmalı")
        return satir[0]

    def _kanit(self):
        return b3("### Model künyesi ve denklik", "### Zamanlama ve gecikme")

    def test_T3_engine_sha_kayit_defteriyle(self):
        d = json.loads(KAYIT.read_text(encoding="utf-8"))
        turev = d["profiles"]["competition"]["turevler"]["navitas_seg_v36_best_512_fp16.engine"]
        sha = turev["sha256"]
        self.assertNotEqual("DERLENINCE_YAZILIR", sha)
        self.assertEqual(d["profiles"]["competition"]["sha256"], turev["kaynak_sha256"])
        n = tekhat(self._kunye())
        self.assertIn(sha.upper(), n, "künye tablosu engine sha'sını taşımıyor")
        self.assertIn(sha[:8].upper(), tekhat(self._kanit()), "Kanıt dizini engine sha'sız")

    def test_T3b_yer_tutucu_hukmu_yalniz_cizili(self):
        for ad, m in (("künye", self._kunye()), ("A3", self._a3()), ("kanıt", self._kanit())):
            self.assertEqual([], yasaklar(m, ("DERLENINCE_YAZILIR",)), ad)

    def test_T3c_d303_dustu_uc_yerde_de_olumluya_CEVRILMEMIS(self):
        d = json.loads(ENGINE_JSON.read_text(encoding="utf-8"))
        h = d["hukum"]
        self.assertEqual("DUSTU", h["D303_S"]["durum"])
        self.assertEqual(3, h["D303_S"]["uyusmazlik"])
        self.assertEqual(126, h["D303_S"]["n"])
        self.assertEqual("GECTI", h["F1"]["durum"])
        self.assertEqual("GECTI", h["F2"]["durum"])
        for ad, m in (("künye", self._kunye()), ("A3", self._a3()),
                      ("kanıt", self._kanit()), ("§4.8.3", b4("### 4.8.3 ", "### 4.8.4 "))):
            n = tekhat(m)
            self.assertIn("3/126", n, ad)
            self.assertIn("DUSTU", n, ad)
            # D-303 hükmünün geçtiği satır olumlu hükümle çevrilmemiş olmalı
            for satir in [s for s in n.splitlines() if "D-303" in s and "3/126" in s]:
                self.assertNotIn("OLUMLU_HUKUM", satir, (ad, satir[:80]))
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)

    def test_T3d_f2_ve_esik_artefaktla(self):
        d = json.loads(ENGINE_JSON.read_text(encoding="utf-8"))
        f2 = d["hukum"]["F2"]["uyusma"]
        n = tekhat(self._kunye()) + tekhat(b4("### 4.8.3 ", "### 4.8.4 "))
        self.assertIn(str(f2).replace(".", ","), n, "F2 uyuşması artefakttan yazılmamış")


class T4_EkipmanKabulTablosu(unittest.TestCase):
    def _b(self):
        return b4("## 4.4 ", "## 4.5 ")

    def _ekipman_satirlari(self):
        """`| ekipman | koşulacak kabul kapısı | bugünkü sonuç |` tablosunun veri satırları."""
        tablo = kesit(self._b(), "| ekipman | koşulacak kabul kapısı | bugünkü sonuç |")
        satirlar = []
        for s in tablo.splitlines()[2:]:          # başlık + hizalama satırı atlanır
            if not s.startswith("|"):
                break
            satirlar.append(s)
        return satirlar

    def test_T4_giris_olculen_olculemeyen_sayimi(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("KISMEN — ekipman kabul testleri bugün tamamlanmış DEĞİLDİR", 1),
            ("9 ekipman", 1),
            ("2/9", 2), ("4/9", 1), ("1/9", 1),
        )))
        # Eski "hiçbir sayı yoktur" hükmü yalnız çizili olabilir
        self.assertEqual([], yasaklar(m, (
            "hiçbir ekipmanın fiziksel kabul testi yapılmadı",
            "Sağ sütunda bugün hiçbir sayı yoktur",
            "Donanım kutusu\n5 Eylül 2026'da açılacak",
        )))
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T4b_ekipman_satiri_sayisi_dokuz(self):
        """Girişteki 2+4+1+2 = 9 sayımı, tablonun GERÇEK satır sayısıyla tutmalı."""
        satirlar = self._ekipman_satirlari()
        self.assertEqual(9, len(satirlar), "\n".join(satirlar))
        n = tekhat(self._b())
        toplam = sum(int(a) for a in re.findall(r"\b(\d)/9\b", n))
        self.assertEqual(9, toplam, "giriş sayımı 9'a tamamlanmıyor")
        # her satırın SON hücresi doludur (boş bırakılmaz)
        for s in satirlar:
            son = [h.strip() for h in s.strip().strip("|").split("|")][-1]
            self.assertTrue(son, s)

    def test_T4c_6_eylul_hucreleri_dosya_satirla(self):
        m = self._b()
        self.assertEqual([], eksikler(m, (
            ("config/pixhawk/arducopter_fda_20260906.param", 1),
            ("6 Eylül 20:22 dökümü repoda", 1),
            ("Hobbywing Skywalker 60A V2", 2),
            ("6 Eylül: RC failsafe ÖLÇÜLDÜ ve DÜŞTÜ", 1),
        )))
        # pil satırındaki sayı dökümden
        params = {}
        for s in oku(PARAM).splitlines():
            if "," in s and not s.startswith("#"):
                ad, _, deger = s.partition(",")
                params[ad.strip()] = deger.strip()
        self.assertEqual("18.18", params["BATT_VOLT_MULT"])
        self.assertIn("BATT_VOLT_MULT,18.18", normalles(m).replace(" ", ""))

    def test_T4d_olculmeyen_hucreler_GECTI_yazmaz(self):
        n = normalles(self._b())
        for anahtar in ("MAVLINK_DOGRULA.PY 3/3", "MENZIL"):
            for satir in [s for s in n.splitlines() if anahtar in s]:
                self.assertIn("OLCULEMEDI", satir, satir[:90])
        # pervane 6 Eylül'de takıldı ama akım/VIBE hâlâ ölçülemedi
        self.assertIn("TAM YUKTE AKIM VE VIBE HALA OLCULEMEDI", tekhat(self._b()))


class T5_OlculmusAmaOlcuelecekDiyenler(unittest.TestCase):
    def test_T5a_483_engine_olculdu_ve_dustu(self):
        m = b4("### 4.8.3 ", "### 4.8.4 ")
        self.assertEqual([], eksikler(m, (
            ("Jetson Orin Nano'da ÖLÇÜLDÜ ve DÜŞTÜ", 1),
            ("scripts/olcum/170_engine_karar_denkligi.py", 1),
        )))
        self.assertEqual([], yasaklar(m, ("Jetson'da `.engine` ile ölçülecektir",)))
        # eşik TEKLİĞİ (D-461): D-303 kabul ölçütü metinde TAM BİR KEZ, tek değerde
        n = tekhat(m)
        self.assertEqual(1, n.count("5/260"), "D-303 eşiği tam bir kez geçmeli")
        self.assertEqual(1, n.count("%1,92"), "D-303 eşik yüzdesi tam bir kez geçmeli")
        # RAKİP EŞİK YASAĞI: bölümde `≤ n/m = %x,y` biçiminde BAŞKA kabul ölçütü olamaz
        self.assertEqual(["5/260 = %1,92"],
                         re.findall(r"≤\s*(\d+/\d+\s*=\s*%\d+,\d+)", n),
                         "rakip/gevşetilmiş ikinci eşik var")
        self.assertEqual([], celiskili_ikinci_hukum(m))
        self.assertIn("%2,38", n)

    def test_T5b_413_jetson_baslat_ve_tensorrt(self):
        m = b4("### 4.1.3 ", "## 4.2 ")
        self.assertEqual([], eksikler(m, (
            ("kartın kendisinde koştu", 1),
            ("jetson_baslat_kuru.log", 1),
            ("ölçüm **Jetson Orin Nano'da koşuldu**", 1),
        )))
        self.assertEqual([], yasaklar(m, (
            "Jetson'daki ilk koşum ilk kanıt olacak",
        )))
        # systemd kipleri HÂLÂ ölçülemedi — yanlış kapanma yok
        n = normalles(m)
        self.assertIn("HALA KOSULMADI", n)
        self.assertIn("OLCULEMEDI", n)

    def test_T5c_4133_denetim_borcu_acik_kalir(self):
        m = b4("### 4.13.3 ", "#### 4.13.3.1 ")
        self.assertEqual([], eksikler(m, (
            ("6 Eylül'de kartta gerçek koşum yapıldı", 1),
            ("systemd kipleri (`--kur` / `--kapi` / `--dogrudan`) hâlâ KOŞULMADI", 1),
            ("genel kapı **15/15 · 15/15**", 1),
        )))
        self.assertEqual([], yasaklar(m, (
            "5 Eylül'de Jetson'daki ilk gerçek koşum",
            "Jetson'daki ilk koşum ilk kanıttır",
        )))
        n = tekhat(m)
        self.assertIn("BORC ACIK", n)
        self.assertIn("OLCULEMEDI ≠ GECTI", n)


class T6_YonergeHizasi(unittest.TestCase):
    """§4.0 kapsama tablosu ile YONERGE_HARITASI Y-4-M01…M12 durumları HİZALI."""

    KIMLIKLER = tuple("Y-4-M{:02d}".format(i) for i in range(1, 13))
    # Kanonik durum sözcükleri (normalleşmiş); çizili olan ESKİ değer sayılmaz.
    DURUMLAR = ("VAR", "KISMEN", "YOK")

    @classmethod
    def durum_coz(cls, hucre):
        """Bir tablo hücresindeki GÜNCEL durum (çizili eski değer AYIKLANMIŞ).

        Hücrenin İLK durum sözcüğü alınır — sıralama sözcük listesinden değil
        METİNDEKİ KONUMDAN gelir; yoksa gerekçe metnindeki "…var" / "…yok"
        kelimeleri hükmü kaçırırdı (kapının kendi çürütücü bulgusu).
        """
        n = tekhat(hucre)
        bulunanlar = [(m.start(), d) for d in cls.DURUMLAR
                      for m in re.finditer(r"\b{}\b".format(d), n)]
        return min(bulunanlar)[1] if bulunanlar else None

    @classmethod
    def b4_durumlari(cls):
        sonuc = {}
        for s in b4("## 4.0 ", "## 4.1 ").splitlines():
            m = re.match(r"\|\s*`?(Y-4-M\d\d)`?\s*\|(.*)\|\s*$", s)
            if m:
                hucreler = [h.strip() for h in m.group(2).split("|")]
                sonuc[m.group(1)] = cls.durum_coz(hucreler[-1])
        return sonuc

    @classmethod
    def yonerge_durumlari(cls):
        sonuc = {}
        for s in oku(YONERGE).splitlines():
            m = re.match(r"\|\s*`?(Y-4-M\d\d)`?\s*\|(.*)\|\s*$", s)
            if m:
                hucreler = [h.strip() for h in m.group(2).split("|")]
                sonuc[m.group(1)] = cls.durum_coz(hucreler[-1])
        return sonuc

    def test_T6_iki_belge_ayni_kimlikleri_tasir(self):
        self.assertEqual(set(self.KIMLIKLER), set(self.b4_durumlari()))
        self.assertEqual(set(self.KIMLIKLER), set(self.yonerge_durumlari()))

    def test_T6b_durumlar_HIZALI(self):
        a, b = self.b4_durumlari(), self.yonerge_durumlari()
        fark = {k: (a[k], b[k]) for k in self.KIMLIKLER if a[k] != b[k]}
        self.assertEqual({}, fark,
                         "§4.0 ↔ YONERGE_HARITASI çelişkisi (D-462 A6 bir daha oluştu)")

    def test_T6c_m04_m06_kismen_eski_deger_cizili(self):
        satirlar = {s.split("|")[1].strip().strip("`"): s
                    for s in b4("## 4.0 ", "## 4.1 ").splitlines()
                    if re.match(r"\|\s*`?Y-4-M\d\d`?\s*\|", s)}
        for kimlik in ("Y-4-M04", "Y-4-M06"):
            s = satirlar[kimlik]
            self.assertIn("~~YOK~~", s, kimlik)          # eski değer SİLİNMEDİ
            self.assertEqual("KISMEN", self.durum_coz(s.split("|")[-2]), kimlik)


class T7_Durustluk(unittest.TestCase):
    CUMLE = "bu yüzden üretim sayıları sahaya göre İYİMSER ÜST SINIRDIR"

    def _yuzeyler(self):
        return (("§3.3.3.2", b3("#### 3.3.3.2 ", "#### 3.3.3.3 ")),
                ("§4.7", b4("## 4.7 ", "## 4.8 ")))

    def test_T7_cumle_iki_yerde_ve_CIZILMEMIS(self):
        for ad, m in self._yuzeyler():
            self.assertEqual([], eksikler(m, ((self.CUMLE, 1),)), ad)
            # çizili varyant kilidi doyuramaz: ham metinde ~~…~~ içinde olmamalı
            for kalip in (_CIZIK_TILDE2, _CIZIK_TILDE1, _CIZIK_ETIKET):
                for cizik in kalip.findall(m):
                    parca = cizik if isinstance(cizik, str) else cizik[0]
                    self.assertNotIn(normalles(self.CUMLE, cizigi_at=False),
                                     normalles(parca, cizigi_at=False), (ad, parca[:60]))

    def test_T7b_iki_yardim_kod_satiriyla(self):
        gorev = oku(KOK / "simulation" / "mujoco" / "gorev_kosumu.py").splitlines()
        toplayici = oku(KOK / "simulation" / "mujoco" / "sim_karar_toplayici.py").splitlines()
        self.assertIn('kb = H["kb"]', gorev[311])                 # :312
        self.assertIn("ref = [round(float(kb[0]), 2)", gorev[312])  # :313
        self.assertIn("k = ceyrek_tur(yaw)", toplayici[182])      # :183
        self.assertIn("np.rot90(img, k)", toplayici[183])         # :184
        self.assertTrue(any("def ceyrek_tur" in s for s in toplayici))
        for ad, m in self._yuzeyler():
            n = tekhat(m)
            self.assertIn("GOREV_KOSUMU.PY:313", n, ad)
            self.assertIn("SIM_KARAR_TOPLAYICI.PY:183-184", n, ad)
            self.assertEqual([], celiskili_ikinci_hukum(m), ad)


class T8_IsikGolgeKesiti(unittest.TestCase):
    def _b3(self):
        return b3("##### 3.3.4.2.8 ", "#### 3.3.4.3 ")

    def _varyant_satirlari(self):
        """Işık/gölge sonuç tablosunun SATIRLARI: {varyant: [hücreler]}.

        Satır bazlıdır — bölümün başka bir yerindeki aynı sayı bir hücre sapmasını
        DOYURAMAZ (kapının kendi mutasyon bulgusu M8).
        """
        sonuc = {}
        for s in self._b3().splitlines():
            if not s.startswith("| "):
                continue
            hucreler = [h.strip() for h in s.strip().strip("|").split("|")]
            n0 = tekhat(hucreler[0])
            for varyant in ("TABAN", "V1", "V2", "V3"):
                if len(hucreler) == 7 and re.match(r"^{}\b".format(varyant), n0):
                    sonuc.setdefault(varyant.lower(), hucreler)
        return sonuc

    def test_T8_varyant_sayilari_artefakttan(self):
        satirlar = self._varyant_satirlari()
        self.assertEqual({"taban", "v1", "v2", "v3"}, set(satirlar), sorted(satirlar))
        ozet = json.loads((K3B / "ozet_k3b.json").read_text(encoding="utf-8"))
        ozetler = {v["varyant"]: v for v in ozet["varyantlar"]}
        self.assertAlmostEqual(0.1314, ozetler["v1"]["htab_engel_ort"], places=4)
        self.assertAlmostEqual(0.2380, ozetler["v2"]["htab_engel_ort"], places=4)
        for dosya, varyant in (("taban_15harita.json", "taban"), ("v1_15harita.json", "v1"),
                               ("v2_15harita.json", "v2"), ("v3_15harita.json", "v3")):
            o = json.loads((K3B / dosya).read_text(encoding="utf-8"))["ozet"]
            self.assertEqual(15, o["harita_n"], varyant)
            h = satirlar[varyant]
            # sütunlar: varyant | rota bulunan | doğru etiket | engel | geçilebilir | açık yol | durumlar
            self.assertEqual("{}/15".format(o["rota_bulunan"]), tekhat(h[1]), (varyant, "rota"))
            self.assertEqual("{}/15".format(o["dogru_etiket"]), tekhat(h[2]), (varyant, "doğru"))
            for sutun, alan in ((3, "htab_engel_ort"), (4, "htab_gecilebilir_ort"),
                                (5, "acik_yol_gecilebilir_ort")):
                beklenen = ("%.4f" % ozetler[varyant][alan]).replace(".", ",")
                self.assertEqual(beklenen, tekhat(h[sutun]), (varyant, alan))

    def test_T8b_isik_parametreleri_koddan(self):
        arena = oku(KOK / "simulation" / "mujoco" / "arena_mjcf.py")
        self.assertIn('"v2": ("-0.62 0.45 -0.64", "0.85 0.83 0.78", "0.18 0.18 0.19"', arena)
        self.assertIn('"taban": ("-0.35 0.25 -0.90", "0.58 0.58 0.55", "0.30 0.30 0.30"', arena)
        self.assertIn('castshadow="true"', arena)
        m = tekhat(self._b3())
        for deger in ("-0.62 0.45 -0.64", "-0.35 0.25 -0.90", "0.85 0.83 0.78",
                      "0.18 0.18 0.19", "0.30 0.30 0.30"):
            self.assertIn(katla(deger), m, deger)

    def test_T8c_saha_degil_ve_yerlesim_siniri(self):
        m = self._b3()
        self.assertEqual([], eksikler(m, (
            ("saha değil, SENTETİK render", 1),
            ("D-441 ÖNCESİ", 1),
            ("v2 ve v3 yeni yerleşimle yeniden ölçülmedi", 1),
        )))
        # eski "ayrı bir ölçüm yapılmamıştır" hükmü YALNIZ çizili
        self.assertEqual([], yasaklar(m, (
            "Farklı ışık açısı ve gölge kesitlerinde\nayrı bir ölçüm yapılmamıştır",)))
        n = tekhat(m)
        self.assertIn("OLCULEMEDI", n)
        self.assertEqual([], celiskili_ikinci_hukum(m))

    def test_T8d_bolum4_48_ve_484_tazelendi(self):
        giris = b4("## 4.8 ", "### 4.8.1 ")
        self.assertEqual([], eksikler(giris, (
            ("SENTETİK ışık/gölge kesiti ÖLÇÜLMÜŞTÜR", 1),
            ("0,1314 → 0,2380", 1),
        )))
        self.assertEqual([], yasaklar(giris, (
            "sentetiktir ve farklı ışık açısı /\ngölge çeşitliliği içermez",)))
        sinir = b4("### 4.8.4 ", "## 4.9 ")
        self.assertEqual([], eksikler(sinir, (("karışıklık matrisi değildir", 1),)))
        self.assertIn("OLCULEMEDI", tekhat(sinir))


class MutasyonKontrolu(unittest.TestCase):
    """Kurallar sentetik metinle İKİ YÖNDE sınanır — boş kapı olmasın (D-370).

    Gerçek dosya mutasyonları ayrıca `results/fdr_sprint_20260910/T244/mutasyon_t244.py`
    ile koşulur (10 mutant; ham çıktı `mutasyon_ciktisi.txt`).
    """

    def test_M1_cizili_iddia_kilidi_DOYURAMAZ(self):
        dogru = "Kilit **üç süreçte de kodludur** (D-419)."
        self.assertEqual([], eksikler(dogru, (("üç süreçte de kodludur", 1),)))
        for mutant in ("~~Kilit **üç süreçte de kodludur** (D-419).~~",
                       "~Kilit **üç süreçte de kodludur** (D-419).~",
                       "<del>Kilit **üç süreçte de kodludur** (D-419).</del>",
                       "<s>Kilit **üç süreçte de kodludur** (D-419).</s>",
                       "<strike>Kilit **üç süreçte de kodludur** (D-419).</strike>"):
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            self.assertEqual(1, len(eksikler(mutant, (("üç süreçte de kodludur", 1),))), mutant)

    def test_M2_tek_tilde_UZUN_metinde_de_yakalanir(self):
        """D-461: `{1,40}` sınırı 40 karakterden uzun tek tilde çiziği görmüyordu."""
        uzun = "Kilit üç süreçte de kodludur ve bu satır kırk karakterden çok daha uzundur"
        self.assertGreater(len(uzun), 40)
        mutant = "~" + uzun + "~"
        self.assertEqual(1, len(eksikler(mutant, (("üç süreçte de kodludur", 1),))))

    def test_M3_yaklasik_isareti_cizme_SAYILMAZ(self):
        metin = "bağlantı ~18:45 kuruldu; HTAB geçilebilir ~%6; pt ~1,35 FPS ve ölçüm DÜŞTÜ"
        self.assertEqual([], cizme_artiklari(metin))
        self.assertIn("DUSTU", normalles(metin))
        self.assertIn("~18:45", metin)

    def test_M4_olumlu_hukme_CEVIRME_yakalanir(self):
        dogru = "| D-303 oransal 3/126 | **DÜŞTÜ** |"
        n = normalles(dogru)
        self.assertIn("DUSTU", n)
        self.assertNotIn("OLUMLU_HUKUM", n)
        for kelime in ("doğrulandı", "kanıtlandı", "teyit edildi", "tutar",
                       "dogrulandı", "Doğ**rulan**dı", "doğ­rulandı"):
            mutant = dogru.replace("**DÜŞTÜ**", "~~**DÜŞTÜ**~~ " + kelime)
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            nm = normalles(mutant)
            self.assertNotIn("DUSTU", nm, kelime)
            self.assertIn("OLUMLU_HUKUM", nm, kelime)

    def test_M5_CELISKILI_IKINCI_HUKUM_yakalanir(self):
        dogru = "Eşik ≥ 12/15; ölçüm 0/15 → DÜŞTÜ."
        self.assertEqual([], celiskili_ikinci_hukum(dogru))
        for ek in (" Sahada **gözden geçirilmiş** kapı ≥ 6/15 alınır.",
                   " Bu kural kaldırıldı.",
                   " Eşik güncellendi: en az 6/15.",
                   " Ölçüt gevşetildi."):
            mutant = dogru + ek
            self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
            self.assertTrue(celiskili_ikinci_hukum(mutant), ek)

    def test_M6_ESIK_TEKLIGI_ikinci_esik_yakalanir(self):
        dogru = "Ön kayıt: yayımlanan çevrilme ≤ ham çevrilmenin %40'ı."
        n = normalles(dogru)
        self.assertEqual(1, n.count("HAM CEVRILMENIN %40'I"))
        self.assertEqual({"40"}, set(re.findall(r"HAM CEVRILMENIN %(\d+)", n)))
        mutant = dogru + " Gözden geçirilmiş ölçüt: ham çevrilmenin %60'ı."
        nm = normalles(mutant)
        self.assertEqual({"40", "60"}, set(re.findall(r"HAM CEVRILMENIN %(\d+)", nm)))
        # eş anlamlı geri dönüş de yakalanır: "en az" → ">="
        self.assertIn(">=", normalles("eşik en az 12/15"))
        self.assertIn(">=", normalles("eşik ≥ 12/15"))

    def test_M7_esanlamli_OLCULMEDI_geri_donusu_tek_belirtec(self):
        for varyant in ("ÖLÇÜLEMEDİ", "ölçülmedi", "ölçüm yok", "ölçülemez"):
            self.assertIn("OLCULEMEDI", normalles(varyant), varyant)

    def test_M8_bilinmeyen_cizme_sozdizimi_beyaz_liste_disi(self):
        self.assertEqual([], cizme_artiklari("düz metin, çizik yok"))
        self.assertTrue(cizme_artiklari("<del>yarım etiket"))
        self.assertTrue(cizme_artiklari("kapanmayan ~çizik"))


if __name__ == "__main__":
    unittest.main()
