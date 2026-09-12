"""T243 NOBETCISI — paket boyutu tablosu ve gercek gorev veri hizi (D-462 C).

🔴 KORUNAN KUSURLAR
  1. BAYAT SAYI: FDR SS3.3.4.3.1/SS3.3.4.3.3'teki her sayi `paket_boyutu.json` ve
     `gorev_veri_hizi.json` dosyalarindan YENIDEN HESAPLANIR. Elle kopyalanmis
     ya da artefakt degisince bayatlamis bir sayi bu kapidan gecemez (D-462 B:
     ayni sinif kusur FDR'de 1896/2104/2620 test sayisiyla olculdu).
  2. SESSIZ PROTOKOL KAYMASI: boyut tablosu ayrica CANLI olculur — olcum betigi
     yeniden kosturulup `protocol.encode()` ile ayni baytlari verdigi
     dogrulanir. `comms/protocol.py`'ye bir alan eklenirse JSON ve FDR bayatlar
     ve bu test DUSER.
  3. URETILEN TABLO ELLE DUZENLENMESIN: `TABLO.md` iki JSON'dan yeniden
     uretilip dosyayla BAYT-ES karsilastirilir.
  4. BELGE KILIDI (D-453/D-460/D-461): ON_KAYIT ve README'deki hukumler cizili
     bicimlerle (~~...~~ satir asan, tek tilde, <del>/<s>/<strike>), vurgu ve
     tipografi varyantlariyla, es anlamli geri donusle ("en az / asan"),
     olcum hukmunun olumluya cevrilmesiyle ("dogrulandi / kanitlandi / teyit
     edildi / tutar") ya da KABUL OLCUTUNE CELISKILI IKINCI HUKUM eklenerek
     delinemez. Rapor olcutu normallestirilmis metinde TAM BIR KEZ gecmelidir
     ve ayni yuzeyde RAKIP bir esik bulunamaz.

⚠ Bu isin hukmu "olculdu / OLCULEMEDI"dir; bir KAPI degildir (ON_KAYIT SS4).
  Kapi olan sey, FDR'deki sayinin artefaktla AYNI kalmasidir.

⚠ Bu dosyadaki normallestirme fonksiyonlari TEK YERDE toplanmistir
  (`_cizili_ayikla`, `_normallestir`, `_tek_bosluk`, `_bosluksuz`,
  `_esik_degerleri`) ve **T242 ile kanonik yardimciya (`tests/belge_kilidi.py`)
  gecirilecektir** — kanonik yardimci T240 dalinda yaziliyor, master'da henuz
  yok (D-460 karar 2, D-461 siralama karari).
"""

import importlib.util as _u
import json
import re
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
BETIK = KOK / "scripts" / "paket_boyutu_olc.py"
DIZIN = KOK / "results" / "fdr_sprint_20260910" / "T243"
ON_KAYIT = DIZIN / "ON_KAYIT.md"
README = DIZIN / "README.md"
TABLO = DIZIN / "TABLO.md"
BOYUT_JSON = DIZIN / "paket_boyutu.json"
KARISIM_JSON = DIZIN / "gorev_veri_hizi.json"
FDR = KOK / "FDR" / "BOLUM_3_SISTEM_SPESIFIKASYONLARI.md"

for _p in (KOK / "codes", KOK / "comms", KOK / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

_spec = _u.spec_from_file_location("t243_olc", BETIK)
M = _u.module_from_spec(_spec)
_spec.loader.exec_module(M)


# ══ BELGE KILIDI YARDIMCILARI — TEK YER (T242 ile tests/belge_kilidi.py'ye) ══

#: Cizili aralik bicimleri (D-453 + D-460 genislemesi). Tek tilde GFM
#: kuralindadir: sinir tildesinin ic yani bosluk OLAMAZ; `[^~\n]` satir
#: asmayi engeller (yoksa "~200 B" gibi tek tildeler yanlis eslesir).
_CIZILI = re.compile(
    r"~~.*?~~"
    r"|~(?!\s)[^~\n]*?(?<!\s)~"
    r"|<del\b[^>]*>.*?</del>"
    r"|<s\b[^>]*>.*?</s>"
    r"|<strike\b[^>]*>.*?</strike>", re.S | re.I)
#: Kalin/italik isaretleri. `_` yalniz MARKDOWN vurgusuyken silinir.
_YILDIZ = re.compile(r"\*+")
_ALTCIZGI = re.compile(r"(?<!\w)_{1,2}(?=\S)|(?<=\S)_{1,2}(?!\w)")
#: Tipografik kesme/tirnak -> duz karsiligi.
_KESME = str.maketrans({"’": "'", "‘": "'", "´": "'",
                        "`": "'", "ʼ": "'",
                        "“": '"', "”": '"'})
#: Beyaz liste DISI cizme isaretleri (D-460 karar 2): normallestirmeden sonra
#: metinde kalmamalidir; kalirsa yeni bir sozdizimi denenmis demektir.
_KALAN_CIZME = re.compile(r"</?(?:del|s|strike)\b|~", re.I)

#: Esik ifadeleri — es anlamli geri donusleri de yakalar ("en az", "asan", ">=").
_ESIK = re.compile(
    r"(?:yuzde|%)\s*(\d+(?:[.,]\d+)?)\s*"
    r"(?:ya da uzeri|ve uzeri|uzerinde|ustunde|veya daha fazla|asarsa|asan)"
    r"|(?:>=|≥|en az|asan|asarsa)\s*(?:yuzde|%)\s*(\d+(?:[.,]\d+)?)",
    re.I)
#: Olcum hukmunu olumluya ceviren sozcukler (D-460 RED-2 kanonik vakasi).
_OLUMLU_CEVIRME = ("dogrulandi", "kanitlandi", "teyit edildi", "tutar",
                   "basarili", "gecti", "saglandi")
#: Kabul yuzeyinde yasak celiskili ikinci hukum sozcukleri (D-461 karar d).
_CELISKILI_IKINCI_HUKUM = ("gozden gecirilmis", "guncellenmis kapi",
                           "kaldirildi", "gecersiz", "yalniz sunlarla verilir")


#: Kod cercevesi: uclu cit blogu ve satir ici `kod` araligi. Markdown'da
#: `<del>` ya da `~x~` bir KOD araligi icindeyken cizmez — belgeleme ornegidir.
_KOD = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def _kod_ayikla(metin):
    """Kod bloklarini ve satir ici kod araliklarini cikarir (cizme taramasi
    once bunu uygular: kod icindeki `<del>` metni GIZLEYEMEZ)."""
    return _KOD.sub(" ", metin)


def _cizili_ayikla(metin):
    """Cizili araliklari metinden CIKARIR; ic ice sarmalar icin sabit noktaya
    kadar yinelenir (D-453, D-460)."""
    onceki = None
    while onceki != metin:
        onceki, metin = metin, _CIZILI.sub("", metin)
    return metin


def _normallestir(metin):
    """Belge kilidinin aradigi NORMALLESTIRILMIS metin: cizili araliklar
    ayiklanir, vurgu isaretleri (**, *, _) kaldirilir, tipografik
    kesme/tirnak duzlenir."""
    m = _cizili_ayikla(metin).translate(_KESME)
    return _ALTCIZGI.sub("", _YILDIZ.sub("", m))


def _tek_bosluk(metin):
    """Satir sonu ve coklu bosluk tek boslugа iner — satir kirilimi kilidi
    delmesin."""
    return re.sub(r"\s+", " ", metin).strip()


def _bosluksuz(metin):
    """Rakam gruplarindaki bosluklari kaldirir: '1 550 097' -> '1550097'."""
    onceki = None
    while onceki != metin:
        onceki = metin
        metin = re.sub(r"(?<=\d)[   ](?=\d)", "", metin)
    return metin


def _sadelestir(metin):
    """Turkce aksanlari duzleyip kucuk harfe indirir (es anlamli/varyant
    aramalari icin). Satir sonlari KORUNUR — bolum sinirlari icin gerekli."""
    tablo = str.maketrans("çğıİöşüÇĞÖŞÜÂÎÛâîû", "cgiiosucgosuaiuaiu")
    return metin.translate(tablo).lower()


def _ara(metin):
    """Kilidin TEK karsilastirma yuzeyi: aksan duzlenir, ok/tire varyantlari
    ('→', '–', '—', '−') tek bicime iner, tirnak ve ters tirnak atilir,
    bosluklar tek bosluga iner, rakam gruplarindaki bosluklar kaldirilir.
    Boylece '**HEARTBEAT** 273 B', '`HEARTBEAT` 273 B' ve satira bolunmus
    hali AYNI dizgeyi verir; bicim oyunlariyla kilit delinemez."""
    s = _sadelestir(metin)
    for a, b in (("→", "->"), ("–", "-"), ("—", "-"), ("−", "-")):
        s = s.replace(a, b)
    s = s.replace("'", "").replace('"', "").replace("`", "")
    return _bosluksuz(_tek_bosluk(s))


def _esik_degerleri(metin):
    """Metindeki ESIK ifadelerinin sayisal degerleri (kume)."""
    d = set()
    for a, b in _ESIK.findall(_ara(metin)):
        ham = a or b
        if ham:
            d.add(float(ham.replace(",", ".")))
    return d


def _kez(metin, ifade):
    """`ifade`nin normallestirilmis metinde kac kez gectigi."""
    return _ara(metin).count(_ara(ifade))


# ══ Artefaktlar ══════════════════════════════════════════════════════════════

B = json.loads(BOYUT_JSON.read_text(encoding="utf-8"))
K = json.loads(KARISIM_JSON.read_text(encoding="utf-8"))
EGRI = B["N2_open_route_egrisi"]
TR = M.tr

#: FDR "12 Eylul" tablosundaki satir etiketi -> JSON kosum anahtari.
FDR_KOSUM = {
    "`saha` · 1,353 Hz": "saha_jetson_olculmus",
    "`saha` · 2,0 Hz": "saha_tavan",
    "`udp` · 1,353 Hz": "udp_jetson_olculmus",
    "`udp` · 2,0 Hz": "udp_tavan",
}
TIPLER = ("IHA_LANDED", "ACK", "NO_ROUTE", "CMD", "HEARTBEAT", "OPEN_ROUTE")


def _fdr_bolum(bas, son):
    m = FDR.read_text(encoding="utf-8")
    i, j = m.index(bas), m.index(son)
    return m[i:j]


def _tablo_satirlari(bolum):
    for ham in bolum.splitlines():
        s = ham.strip()
        if not s.startswith("|"):
            continue
        yield [h.strip() for h in s.strip("|").split("|")]


def _metin(bolum):
    """Bolumun normallestirilmis, tek bosluklu, rakam-bosluklari kaldirilmis
    hali — FDR sayilari bunun uzerinde aranir."""
    return _ara(_normallestir(bolum))


BOLUM_1 = _fdr_bolum("##### 3.3.4.3.1", "##### 3.3.4.3.2")
BOLUM_3 = _fdr_bolum("##### 3.3.4.3.3", "##### 3.3.4.3.4")
METIN_1, METIN_3 = _metin(BOLUM_1), _metin(BOLUM_3)


# ══ BAGIMSIZ DUYARLILIK HESABI (D-466) ═══════════════════════════════════════
# 🔴 Curutucunun bulgusu: eski nobetci FDR'deki duyarlilik sayisini, o sayiyi
#    URETEN fonksiyonu (`M.tavan_waypoint_duyarliligi`) yeniden kosarak
#    dogruluyordu — fonksiyon yanlissa kilit de yanlisi onaylar (udp kolunda
#    250 yerine 200 cerceve). Buradaki hesap betige DOKUNMAZ: iki JSON'dan
#    elle yazilmis aritmetiktir ve capraz kilidi kendi esigiyle kurar.

#: Capraz kilidin ON KAYITLI bagil tolerans tavani. Gevsetilemez (D-466).
KILIT_TOLERANS = 0.02


def _bagimsiz(anahtar):
    """FDR/TABLO sayilarinin BAGIMSIZ karsiligi — yalniz JSON aritmetigi."""
    r = K["kosumlar"][anahtar]
    v, h = r["veri_hizi"], r["hat_yuku"]
    hb_cerceve = r["heartbeat_sayisi"] * len(r["akranlar"])
    cerceve = v["gonderilen_paket"] - hb_cerceve
    olculen = B["N1_tip_basina_bayt"]["OPEN_ROUTE"]
    ima = (v["gonderilen_bayt"]
           - hb_cerceve * B["N1_tip_basina_bayt"]["HEARTBEAT"]) / cerceve
    sapma = ima / olculen - 1.0
    tavan = str(EGRI["sozlesme_tavani_waypoint"])
    fark = EGRI["uretim_yolu"][tavan] - olculen
    bayt_s = h["gonderilen_bayt_s"] + (fark * cerceve) / h["sure_s"]
    return {
        "hb_cerceve": hb_cerceve,
        "cerceve": cerceve,
        "ima_edilen_bayt": ima,
        "bagil_sapma": sapma,
        "tuttu": abs(sapma) <= KILIT_TOLERANS,
        "waypoint_farki_bayt": fark,
        "hat_bayt_s": bayt_s,
        "paylasimli_yuzde": 100.0 * bayt_s / 5760.0,
        "ecc_acikken_paylasimli_yuzde": 100.0 * bayt_s / 2880.0,
    }


#: FDR duyarlilik araliginin kaynagi: iki TAVAN kosumu.
DUYARLILIK_KOSUMLARI = ("saha_tavan", "udp_tavan")


def _paragraf(bolum, bas):
    """Bolumun `bas` ile baslayan PARAGRAFI — HAM metin.

    D-465: olcum hukmu tasiyan yuzeyde cizik/varlik/vurgu AYIKLAMASI YOKTUR;
    normallestirme yalniz bosluk/satir sonu icindir.
    """
    for par in re.split(r"\n[ \t]*\n", bolum):
        if par.strip().startswith(bas):
            return _bosluk(par)
    raise AssertionError(f"paragraf bulunamadi: {bas!r}")


def _bosluk(metin):
    """D-465 normallestirmesi: YALNIZ bosluk/satir sonu."""
    return re.sub(r"\s+", " ", metin).strip()


class Capa(unittest.TestCase):
    def test_artefaktlar_yerinde(self):
        for y in (BETIK, ON_KAYIT, README, TABLO, BOYUT_JSON, KARISIM_JSON):
            self.assertTrue(y.is_file(), f"eksik artefakt: {y}")

    def test_on_kayit_olcumden_once_commitlendi(self):
        """ON_KAYIT olcum betiginden ONCE ayri commit'lenmis olmali."""
        import subprocess
        def ilk(yol):
            c = subprocess.run(
                ["git", "log", "--reverse", "--format=%ct", "--", str(yol)],
                cwd=str(KOK), capture_output=True, text=True)
            satir = [s for s in c.stdout.split() if s.strip()]
            return int(satir[0]) if satir else None
        a, b = ilk(ON_KAYIT), ilk(BETIK)
        if a is None or b is None:
            self.skipTest("git gecmisi yok (ornegin disa aktarilmis agac)")
        self.assertLessEqual(a, b, "ON_KAYIT olcum betiginden SONRA eklenmis")


class BoyutCanliOlculur(unittest.TestCase):
    """JSON'daki boyutlar `protocol.encode()` ile HALA ayni mi (kusur 2)."""

    @classmethod
    def setUpClass(cls):
        cls.taze = M.boyut_olc()

    def test_tip_basina_bayt_ayni(self):
        self.assertEqual(self.taze["N1_tip_basina_bayt"],
                         B["N1_tip_basina_bayt"])
        self.assertEqual(self.taze["N1_asgari_bayt"], B["N1_asgari_bayt"])

    def test_egri_ve_alan_maliyetleri_ayni(self):
        self.assertEqual(self.taze["N2_open_route_egrisi"], EGRI)
        self.assertEqual(self.taze["N3_heartbeat"], B["N3_heartbeat"])
        self.assertEqual(self.taze["N4_alan_marjinal_bayt"],
                         B["N4_alan_marjinal_bayt"])
        self.assertEqual(self.taze["N4_conf_ondalik_bayt"],
                         B["N4_conf_ondalik_bayt"])
        self.assertEqual(self.taze["N5_seq_basamak_bayt"],
                         B["N5_seq_basamak_bayt"])

    def test_heartbeat_alan_kumesi_sozlesmeyle_ayni(self):
        """Sozlesmeye alan eklenirse olcum SESSIZCE bayatlamaz."""
        import protocol
        self.assertEqual(set(M.TAM_TELEMETRI),
                         set(protocol.HEARTBEAT_TELEMETRI_ALANLARI))
        self.assertEqual(B["N3_heartbeat"]["tam_telemetri_alan_sayisi"],
                         len(protocol.HEARTBEAT_TELEMETRI_ALANLARI))

    def test_gercek_saat_bandi_sabit_saatle_tutarli(self):
        g = B["N5_gercek_saat_bayt"]
        self.assertEqual(g["maks"], B["N3_heartbeat"]["tam_telemetri_bayt"])
        self.assertGreaterEqual(g["min"], g["maks"] - 3)
        self.assertEqual(g["ornek"], M.SAAT_ORNEK)

    def test_cerceve_donusu_bayt_es(self):
        self.assertTrue(B["cerceve_donusu_bayt_es"])
        self.assertTrue(self.taze["cerceve_donusu_bayt_es"])


class _SahteLink:
    """Sayaci sinamak icin gercek link yerine gecen en kucuk yuzey."""

    def __init__(self, gelen=()):
        self.yazilan = []
        self._gelen = list(gelen)

    def send(self, data, peer=None):
        self.yazilan.append(data)

    def recv(self, *a, **kw):
        return self._gelen.pop(0) if self._gelen else (None, None)

    def close(self):
        pass


class _Saat:
    """Deterministik monotonik saat: her cagrida siradaki degeri verir."""

    def __init__(self, degerler):
        self.d = list(degerler)

    def __call__(self):
        return self.d.pop(0) if len(self.d) > 1 else self.d[0]


class OlcumMantigiKilitli(unittest.TestCase):
    """Karisim olcumunun SAYMA mantigi — JSON yeniden uretilmeden kilitlenir.

    🔴 Bu sinif, ilk kosumda gercekten olusmus kusurun (ortak ortamdaki ACK
    baytlarinin sayilmamasi, `kosum_ciktisi_v1_eksik.txt`) geri gelmesini
    engeller: 4 dakikalik olcumu yeniden kosmadan, sayaclarin uzerinde.
    """

    def test_sayan_link_bayt_paket_ve_tepe_kovasi(self):
        link = _SahteLink(gelen=[(b"x" * 40, ("127.0.0.1", 1)), (None, None)])
        s = M.SayanLink(link, saat=_Saat([0.0, 0.5, 1.2, 2.4, 2.4, 2.4]))
        s.send(b"a" * 100)
        s.send(b"b" * 50)
        s.send(b"c" * 10)
        s.send(b"d" * 30)
        self.assertEqual([100, 50, 10, 30], [len(x) for x in link.yazilan])
        self.assertEqual(190, s.gonderilen_bayt)
        self.assertEqual(4, s.gonderilen_paket)
        self.assertEqual((b"x" * 40, ("127.0.0.1", 1)), s.recv())
        self.assertEqual(40, s.alinan_bayt)
        self.assertEqual(1, s.alinan_paket)
        h = s.hiz()
        # sure 2,4 s -> tam kova 0 (150 B) ve 1 (10 B); yarim kova 2 disarida.
        self.assertEqual(2, h["kova_sayisi"])
        self.assertEqual(150, h["tepe_gonderilen_bayt_s"])

    def test_hat_yuku_TUM_UCLARIN_gonderdigini_toplar(self):
        """M14 kusuru: yalniz IHA sayilirsa ortak ortam yuku EKSIK cikar."""
        iha = M.SayanLink(_SahteLink(), saat=_Saat([0.0, 10.0]))
        ika = M.SayanLink(_SahteLink(), saat=_Saat([1.0, 9.0]))
        iha.send(b"i" * 600)
        iha.send(b"i" * 400)
        ika.send(b"k" * 120)
        ika.send(b"k" * 80)
        hat = M.hat_yuku({"iha": iha, "ika": ika})
        self.assertEqual(1200, hat["gonderilen_bayt"])
        self.assertEqual(4, hat["gonderilen_paket"])
        self.assertNotEqual(iha.gonderilen_bayt, hat["gonderilen_bayt"],
                            "hat yuku yalniz IHA'yi sayiyor (eksik olcum)")
        self.assertEqual(10.0, hat["sure_s"])       # min t0 -> maks t_son
        self.assertEqual(120.0, hat["gonderilen_bayt_s"])
        self.assertEqual(0, hat["alinan_bayt"])     # cift sayma yok

    def test_doluluk_paylasimli_sutunu_HAT_YUKUNDEN_gelir(self):
        hiz = {"gonderilen_bayt_s": 1000.0, "alinan_bayt_s": 50.0}
        hat = {"gonderilen_bayt_s": 1400.0}
        d = M.doluluk(hiz, hat)
        self.assertAlmostEqual(100.0 * 1000.0 / M.HAM_BAYT_S, d["tek_yon_yuzde"],
                               places=2)
        self.assertAlmostEqual(100.0 * 1400.0 / M.HAM_BAYT_S,
                               d["paylasimli_yuzde"], places=2)
        self.assertAlmostEqual(2 * 100.0 * 1400.0 / M.HAM_BAYT_S,
                               d["ecc_acikken_paylasimli_yuzde"], places=2)
        self.assertEqual("OLCULEMEDI", d["ecc_durumu"])
        self.assertEqual(5760.0, M.HAM_BAYT_S)

    def test_gorev_sureleri_SOZLESMEDEN_okunuyor(self):
        import karar_sozlesmesi as ks
        g = M.gorev_toplami({"gonderilen_bayt_s": 1000.0})
        self.assertEqual(float(ks.SARTNAME_IHA_GOREV_SURESI_S),
                         g["iha_gorev_suresi_s"])
        self.assertEqual(float(ks.SARTNAME_IKA_GOREV_SURESI_S),
                         g["ika_gorev_suresi_s"])
        self.assertEqual(int(1000.0 * ks.SARTNAME_IHA_GOREV_SURESI_S),
                         g["iha_toplam_bayt"])
        self.assertIn("EKSTRAPOLASYON", g["yontem"])

    def test_karisim_heartbeat_araligi_sozlesmeden(self):
        import karar_sozlesmesi as ks
        for r in K["kosumlar"].values():
            self.assertEqual(float(ks.IHA_HEARTBEAT_ARALIK_S),
                             r["heartbeat_araligi_s"])

    def test_kosumlarda_yayinci_hatasi_yok(self):
        for ad, r in K["kosumlar"].items():
            self.assertEqual([], r["yayinci_hatalari"], ad)


class TabloUretilir(unittest.TestCase):
    def test_tablo_json_lardan_yeniden_uretilir(self):
        """TABLO.md elle duzenlenmemis: iki JSON'dan bayt-es uretiliyor."""
        beklenen = M.tablo_uret(B, K)
        mevcut = TABLO.read_text(encoding="utf-8").replace("\r\n", "\n")
        self.assertEqual(beklenen, mevcut,
                         "TABLO.md JSON'lardan uretilene esit degil "
                         "(elle duzenlenmis ya da JSON degismis)")


class FdrBoyutTablosu(unittest.TestCase):
    """FDR SS3.3.4.3.1 — her hucre `paket_boyutu.json`'dan yeniden hesaplanir."""

    def setUp(self):
        self.satir = {s[0]: s for s in _tablo_satirlari(BOLUM_1)
                      if s[0].strip("`") in TIPLER}

    def test_tablo_tam_ve_bayt_esit(self):
        self.assertEqual(set(self.satir), {f"`{t}`" for t in TIPLER},
                         "FDR boyut tablosunda satir eksik ya da fazla")
        for tip in TIPLER:
            s = self.satir[f"`{tip}`"]
            self.assertEqual(s[1], str(B["N1_asgari_bayt"][tip]),
                             f"{tip} asgari bayt FDR'de bayat")
            self.assertEqual(s[2], str(B["N1_tip_basina_bayt"][tip]),
                             f"{tip} ornek cerceve bayti FDR'de bayat")

    def test_egim_ve_egri_sayilari(self):
        u, g = EGRI["uretim_yolu"], EGRI["en_genis"]
        egim_u = (u["20"] - u["10"]) / 10.0
        egim_g = (g["20"] - g["10"]) / 10.0
        tavan = str(EGRI["sozlesme_tavani_waypoint"])
        for ifade in (
            f"uretim yolunda {TR(egim_u, 1)} B/waypoint",
            f"en genis ondalik gosterimde {TR(egim_g, 1)} B/waypoint",
            f"1 waypoint {u['1']} B, 20 waypoint {u['20']} B",
            f"{tavan} waypoint {u[tavan]} B",
            f"en genis gosterimde {g[tavan]} B",
        ):
            self.assertIn(_ara(ifade), METIN_1, ifade)

    def test_conf_ve_alan_maliyetleri(self):
        c = B["N4_conf_ondalik_bayt"]
        marj = B["N4_alan_marjinal_bayt"]
        hb = B["N3_heartbeat"]
        g = B["N5_gercek_saat_bayt"]
        for ifade in (
            f"{c['kisa']} -> {c['float32_genisleyen']} B",
            f"pixhawk_canli {marj['pixhawk_canli']} B",
            f"karar_yas / lat / lon {marj['lat']} B",
            f"asgari HEARTBEAT {hb['asgari_bayt']} B",
            f"{g['min']}–{g['maks']} B",
        ):
            self.assertIn(_ara(ifade), METIN_1, ifade)
        self.assertEqual(marj["lat"], marj["lon"])
        self.assertEqual(marj["lat"], marj["karar_yas"])

    def test_tasarim_notu_yanlislanmis_diye_yaziliyor(self):
        """~200 B tasarim notu ile OLCULEN iki cerceve celisiyor; FDR bunu
        OLUMLU bir hukumle ortmemeli."""
        s = METIN_1
        self.assertIn("yanlislandi", s)
        for tip in ("HEARTBEAT", "OPEN_ROUTE"):
            self.assertIn(_ara(f"{tip} {B['N1_tip_basina_bayt'][tip]} B"), s)
        for sozcuk in _OLUMLU_CEVIRME:
            self.assertNotIn(_ara(f"200 B cerceve tasarim notu {sozcuk}"), s)


class FdrVeriHiziTablosu(unittest.TestCase):
    """FDR SS3.3.4.3.3 "12 Eylul" tablosu — `gorev_veri_hizi.json`'dan."""

    def setUp(self):
        self.satir = {s[0]: s for s in _tablo_satirlari(BOLUM_3)
                      if s[0] in FDR_KOSUM}

    def test_kosum_satirlari_tam(self):
        self.assertEqual(set(self.satir), set(FDR_KOSUM),
                         "12 Eylul tablosunda kosum satiri eksik ya da fazla")

    def test_her_hucre_jsondan_yeniden_hesaplanir(self):
        for etiket, anahtar in FDR_KOSUM.items():
            r = K["kosumlar"][anahtar]
            v, h, d = r["veri_hizi"], r["hat_yuku"], r["doluluk"]
            beklenen = [
                etiket,
                str(r["beslenen_karar"]),
                str(r["yayinlanan_karar"]),
                str(r["heartbeat_sayisi"]),
                TR(v["gonderilen_bayt_s"], 1),
                TR(v["gonderilen_paket_s"], 3),
                str(v["tepe_gonderilen_bayt_s"]),
                TR(v["alinan_bayt_s"], 1),
                TR(h["gonderilen_bayt_s"], 1),
                f"%{TR(d['paylasimli_yuzde'], 2)}",
            ]
            self.assertEqual(self.satir[etiket], beklenen,
                             f"{etiket} satiri JSON ile uyusmuyor (bayat sayi)")

    def test_kadans_etiketi_jsonla_tutarli(self):
        for etiket, anahtar in FDR_KOSUM.items():
            hz = K["kosumlar"][anahtar]["karar_kadansi_hz"]
            basamak = 3 if K["kosumlar"][anahtar]["kadans_adi"] != "tavan" else 1
            self.assertIn(f"{TR(hz, basamak)} Hz", etiket)

    def test_gorev_toplami_ekstrapolasyon_araligi(self):
        gt = [K["kosumlar"][a]["gorev_toplami"] for a in FDR_KOSUM.values()]
        iha = [g["iha_toplam_bayt"] for g in gt]
        ika = [g["ika_toplam_bayt"] for g in gt]
        for ifade in (f"IHA 900 s'de {min(iha)} – {max(iha)} B",
                      f"IKA 600 s'de {min(ika)} – {max(ika)} B"):
            self.assertIn(_ara(ifade), METIN_3, ifade)
        self.assertIn("ekstrapolasyon", METIN_3)
        self.assertIn(_ara("900 s'lik kosum yapilmadi"), METIN_3)

    def test_hat_butcesi_ve_ecc_sayilari(self):
        d = K["kosumlar"]["saha_tavan"]["doluluk"]
        ecc = [K["kosumlar"][a]["doluluk"]["ecc_acikken_paylasimli_yuzde"]
               for a in FDR_KOSUM.values()]
        for ifade in (f"ham {TR(d['ham_bayt_s'], 0)} B/s",
                      f"bayt basina {TR(d['ms_basina_bayt'], 3)} ms",
                      f"%{TR(min(ecc), 2)} – %{TR(max(ecc), 2)}"):
            self.assertIn(_ara(ifade), METIN_3, ifade)

    def test_duyarlilik_satiri_BAGIMSIZ_HESAPTAN(self):
        """D-466: sayilar hesabi URETEN fonksiyondan bagimsiz dogrulanir."""
        du = [_bagimsiz(a) for a in DUYARLILIK_KOSUMLARI]
        bs = sorted(x["hat_bayt_s"] for x in du)
        yz = sorted(x["paylasimli_yuzde"] for x in du)
        ec = sorted(x["ecc_acikken_paylasimli_yuzde"] for x in du)
        for ifade in (f"{TR(bs[0], 1)} – {TR(bs[1], 1)} B/s",
                      f"%{TR(yz[0], 2)} – %{TR(yz[1], 2)}",
                      f"%{TR(ec[0], 2)} – %{TR(ec[1], 2)}",
                      f"({du[0]['waypoint_farki_bayt']} B)"):
            self.assertIn(_ara(ifade), METIN_3, ifade)
        self.assertIn(_ara("HESAP, olcum degil"), METIN_3)

    def test_yayin_tavani_bulgusu_sayilariyla_duruyor(self):
        """Olcumun asil bulgusu (kotu haber) rapordan dusmemeli.

        Sayilar ASIL BULGU paragrafinda aranir: D-466 ile eklenen "Sonuc"
        paragrafi ayni sayilari tasidigi icin bolum geneli aramak, bulgunun
        asil yerinden silinmesini gizlerdi (M4 kacisi).
        """
        s = _ara(_normallestir(_paragraf(BOLUM_3, "🔴 **Bu ölçümün asıl")))
        for a, b in (("saha_jetson_olculmus", "saha_tavan"),
                     ("udp_jetson_olculmus", "udp_tavan")):
            ilk = K["kosumlar"][a]["yayinlanan_karar"]
            son = K["kosumlar"][b]["yayinlanan_karar"]
            self.assertEqual(ilk, son, "kadans degisince yayin degismedi "
                                       "iddiasi artefaktla celisiyor")
            etiket = a.split("_")[0]
            self.assertIn(_ara(f"{etiket} {ilk} -> {son}"), s)
        yks = K["kosumlar"]["udp_tavan"]["yks_gorulen_tipler"]["OPEN_ROUTE"]
        self.assertIn(_ara(f"{yks} OPEN_ROUTE cercevesi gordu"), s)

    def test_fdr_bolumlerinde_cizme_ETIKETI_kalmamis(self):
        """FDR'de yeni bir cizme ETIKETI (<del>/<s>/<strike>) ayiklanmadan
        kalirsa kilit duser. (Tilde taramasi burada YOK: FDR prozunda mesru
        '~200 B' gecer; etiketler icin boyle bir mesru kullanim yoktur.)"""
        etiket = re.compile(r"</?(?:del|s|strike)\b", re.I)
        for ad, bolum in (("SS3.3.4.3.1", BOLUM_1), ("SS3.3.4.3.3", BOLUM_3)):
            kalan = etiket.search(_cizili_ayikla(_kod_ayikla(bolum)))
            self.assertIsNone(kalan, f"FDR {ad}: ayiklanmamis cizme etiketi "
                                     f"{kalan!r}")

    def test_rf_hukmu_degismedi(self):
        s = METIN_3
        self.assertIn(_ara("Bu alt bolumdeki hicbir sayi RF olcumu degildir"), s)
        self.assertIn(_ara("Telsizin ECC ayari OLCULEMEDI"), s)
        self.assertIsNone(
            re.search(r"ecc[^.]{0,120}?(dogrulan|kanitlan|teyit edildi|olculdu)",
                      s),
            "ECC hukmu olumluya cevrilmis")


class DuyarlilikBagimsizKilit(unittest.TestCase):
    """🔴 D-466 — KORUNAN KUSUR: `udp` kolunda cerceve sayisi 250 yerine 200.

    Eski nobetci bunu yakalayamiyordu cunku TABLO/FDR sayisini AYNI hatali
    fonksiyonu yeniden kosarak uretiyordu (bayat sayi kilidi vardi, YANLIS
    sayi kilidi yoktu). Buradaki testler betigin hesabini kullanmaz.
    """

    def test_cerceve_sayisi_OLCUMDEN_tek_formul(self):
        """cerceve = gonderilen_paket - HEARTBEAT x akran; dal YOK."""
        for ad, r in K["kosumlar"].items():
            bek = (r["veri_hizi"]["gonderilen_paket"]
                   - r["heartbeat_sayisi"] * len(r["akranlar"]))
            self.assertEqual(bek, _bagimsiz(ad)["cerceve"], ad)
            self.assertEqual(bek, M.open_route_cerceve_sayisi(r),
                             f"{ad}: betik cerceve sayisi bagimsiz formulden "
                             f"farkli (yapilandirma dali geri mi geldi?)")

    def test_udp_kolunda_YKS_sayaci_KULLANILMAZ(self):
        """YKS sayaci yalniz YKS'ye ulasani sayar; hatta giden daha fazladir."""
        r = K["kosumlar"]["udp_tavan"]
        yks = r["yks_gorulen_tipler"]["OPEN_ROUTE"]
        hat = _bagimsiz("udp_tavan")["cerceve"]
        self.assertGreater(hat, yks,
                           "udp kolunda hatta giden cerceve, YKS'nin gordugu "
                           "cerceveden az olamaz")
        self.assertEqual(hat - yks, r["yayinlanan_karar"],
                         "aradaki fark IKA'ya giden cerceve sayisi olmali")

    def test_capraz_kilit_HER_kosumda_tutuyor(self):
        """Ima edilen B/cerceve, olculen OPEN_ROUTE boyutuna +-%2 icinde."""
        for ad in K["kosumlar"]:
            d = _bagimsiz(ad)
            self.assertLessEqual(
                abs(d["bagil_sapma"]), KILIT_TOLERANS,
                f"{ad}: capraz kilit TUTMADI — ima edilen "
                f"{d['ima_edilen_bayt']:.1f} B/cerceve, olculen "
                f"{B['N1_tip_basina_bayt']['OPEN_ROUTE']} B")
            self.assertTrue(d["tuttu"], ad)

    def test_betigin_hesabi_bagimsiz_hesapla_ayni(self):
        """Betik ile bagimsiz aritmetik AYNI sayiyi vermeli (aksi: sapma)."""
        for ad in DUYARLILIK_KOSUMLARI:
            bet = M.tavan_waypoint_duyarliligi(B, K["kosumlar"][ad])
            bag = _bagimsiz(ad)
            self.assertIsNotNone(bet, ad)
            self.assertEqual(bag["cerceve"], bet["open_route_cerceve_sayisi"],
                             ad)
            for alan in ("hat_bayt_s", "paylasimli_yuzde",
                         "ecc_acikken_paylasimli_yuzde"):
                self.assertAlmostEqual(bag[alan], bet[alan], places=6,
                                       msg=f"{ad}/{alan}")

    def test_capraz_kilit_GEVSETILEMEZ(self):
        """Esik gevsetilirse YANLIS cerceve sayisi kabul edilir -> bu test duser.

        Sentetik prob: `udp_tavan` kosumunun cerceve sayisi elle 250 -> 200
        yapilir (eski kusur). Kilit bunu REDDETMELI ve duyarlilik hesabi
        OLCULEMEDI'ye dusmeli.
        """
        self.assertLessEqual(M.CAPRAZ_KILIT_TOLERANS, KILIT_TOLERANS,
                             "betikteki capraz kilit toleransi ON KAYITLI "
                             "tavandan gevsek")
        r = json.loads(json.dumps(K["kosumlar"]["udp_tavan"]))
        yanlis = r["yks_gorulen_tipler"]["OPEN_ROUTE"]          # 200
        dogru = M.open_route_cerceve_sayisi(r)                  # 250
        self.assertNotEqual(yanlis, dogru)
        # Cerceve sayisini elle yanlis degere cek (paket sayisini dusurerek).
        r["veri_hizi"]["gonderilen_paket"] -= (dogru - yanlis)
        self.assertEqual(yanlis, M.open_route_cerceve_sayisi(r))
        kilit = M.capraz_kilit(B, r)
        self.assertFalse(kilit["tuttu"],
                         "capraz kilit YANLIS cerceve sayisini kabul etti — "
                         "esik gevsetilmis olabilir "
                         f"(sapma %{100 * kilit['bagil_sapma']:.2f}, "
                         f"tolerans %{100 * kilit['tolerans']:.2f})")
        self.assertIsNone(M.tavan_waypoint_duyarliligi(B, r),
                          "kilit tutmadan hesap yapildi (sessiz yanlis sayi)")

    def test_kilit_tutmazsa_TABLODA_OLCULEMEDI(self):
        """Sessiz yanlis sayi yerine ACIK BOSLUK: tabloya OLCULEMEDI girer."""
        k2 = json.loads(json.dumps(K))
        r = k2["kosumlar"]["udp_tavan"]
        r["veri_hizi"]["gonderilen_paket"] -= 50
        metin = M.tablo_uret(B, k2)
        satir = [x for x in metin.splitlines()
                 if x.startswith("| `udp_tavan` |") and "OLCULEMEDI" in x]
        self.assertTrue(satir, "kilit tutmadigi halde tabloda sayi duruyor")

    def test_TABLO_capraz_kilit_tablosu_bagimsiz_hesapla_ayni(self):
        """TABLO.md §8 kilit tablosunun her hucresi bagimsiz hesapla dogrulanir."""
        ham = TABLO.read_text(encoding="utf-8")
        satirlar = {s[0].strip("`"): s for s in _tablo_satirlari(ham)}
        for ad in K["kosumlar"]:
            d = _bagimsiz(ad)
            self.assertIn(ad, satirlar, f"TABLO §8 kilit satiri yok: {ad}")
            hucre = satirlar[ad]
            self.assertEqual(
                [str(d["hb_cerceve"]), str(d["cerceve"]),
                 TR(d["ima_edilen_bayt"], 1),
                 str(B["N1_tip_basina_bayt"]["OPEN_ROUTE"]),
                 f"%{TR(100.0 * d['bagil_sapma'], 2)}", "TUTTU"],
                hucre[1:], f"{ad}: TABLO §8 kilit satiri bagimsiz hesapla "
                           "uyusmuyor")

    def test_duyarlilik_satiri_TABLOda_bagimsiz_hesapla_ayni(self):
        ham = TABLO.read_text(encoding="utf-8")
        satirlar = [s for s in _tablo_satirlari(ham)
                    if s[0].strip("`") in DUYARLILIK_KOSUMLARI and len(s) == 6]
        self.assertEqual(2, len(satirlar), "TABLO §8 duyarlilik satirlari eksik")
        for hucre in satirlar:
            d = _bagimsiz(hucre[0].strip("`"))
            self.assertEqual(
                [str(d["waypoint_farki_bayt"]), str(d["cerceve"]),
                 TR(d["hat_bayt_s"], 1), f"%{TR(d['paylasimli_yuzde'], 2)}",
                 f"%{TR(d['ecc_acikken_paylasimli_yuzde'], 2)}"],
                hucre[1:], hucre[0])


class DuyarlilikMetinKilidi(unittest.TestCase):
    """D-465 — olcum hukmu tasiyan blok ON KAYITLI METIN ESITLIGINE baglidir.

    Cizik/varlik/vurgu ayiklamasi YOK; normallestirme yalniz bosluk/satir
    sonudur. Bloktaki CANLI sayilar `_bagimsiz()` hesabindan doldurulur, eski
    (cizili) sayilar tarihsel sabit olarak durur — bir sozcuk degisirse test
    duser, hangi sozdizimiyle degistigi onemsizdir.
    """

    DUYARLILIK = (
        "⚠ **Duyarlılık (HESAP, ölçüm değil):** rota sözleşme tavanındaki "
        "waypoint sayısına (`MAX_WAYPOINTS` = {tavan_wp}) çıkarsa ortak ortam "
        "yükü ~~**3715,4 – 4003,6 B/s**'ye taşınır (paylaşımlı "
        "%64,50 – %69,51)~~ — **12 Eylül düzeltmesi (D-466)** — "
        "**{bs0} – {bs1} B/s**'ye taşınır (paylaşımlı **%{yz0} – %{yz1}**) ve "
        "ECC açık varsayımıyla ham bütçe **aşılır** (**%{ec0} – %{ec1}**). "
        "Bu bir ölçüm değildir: ölçülen çerçeve boyutu farkı ({fark} B) × "
        "ölçülen çerçeve sayısıdır. Düzeltmenin sebebi: ilk hesap `udp` "
        "kolunda hatta giden **{udp_cerceve}** `OPEN_ROUTE` çerçevesinin "
        "yalnız YKS'ye ulaşan **{yks}**'ünü saymıştı (İKA'ya giden {atlanan} "
        "çerçeve atlanmıştı); çerçeve sayısı artık iki yapılandırmada da tek "
        "ölçüm formülüyle (`gönderilen_paket − HEARTBEAT_sayısı × "
        "akran_sayısı`) bulunur ve ölçülen bayt/çerçeve ile çapraz kilitlenir "
        "— kilit tutmazsa hesap yapılmaz, satıra **OLCULEMEDI** yazılır "
        "(`TABLO.md` §8)."
    )

    SONUC = (
        "**Sonuç (D-466 · ÖLÇÜM):** karar **yayın tavanı ≈ 1 karar/s**'dir; "
        "besleme kadansı {k1} → {k2} Hz'e çıkarıldığında **yayınlanan karar "
        "sayısı DEĞİŞMEDİ** (`saha` {s1} → {s2}, `udp` {u1} → {u2}) ve sebebi "
        "hat değil `IhaSender._tekrarli_gonder` tasarımıdır. **Algı hızlanırsa "
        "yayın hızlanmaz.** Bu bir kusur beyanı değil, ölçülmüş sınırdır."
    )

    def test_duyarlilik_paragrafi_ON_KAYITLI_METNE_ESIT(self):
        du = {a: _bagimsiz(a) for a in DUYARLILIK_KOSUMLARI}
        bs = sorted(x["hat_bayt_s"] for x in du.values())
        yz = sorted(x["paylasimli_yuzde"] for x in du.values())
        ec = sorted(x["ecc_acikken_paylasimli_yuzde"] for x in du.values())
        u = K["kosumlar"]["udp_tavan"]
        beklenen = _bosluk(self.DUYARLILIK.format(
            tavan_wp=EGRI["sozlesme_tavani_waypoint"],
            bs0=TR(bs[0], 1), bs1=TR(bs[1], 1),
            yz0=TR(yz[0], 2), yz1=TR(yz[1], 2),
            ec0=TR(ec[0], 2), ec1=TR(ec[1], 2),
            fark=du["saha_tavan"]["waypoint_farki_bayt"],
            udp_cerceve=du["udp_tavan"]["cerceve"],
            yks=u["yks_gorulen_tipler"]["OPEN_ROUTE"],
            atlanan=du["udp_tavan"]["cerceve"]
                    - u["yks_gorulen_tipler"]["OPEN_ROUTE"]))
        self.assertEqual(beklenen, _paragraf(BOLUM_3, "⚠ **Duyarlılık"),
                         "FDR §3.3.4.3.3 duyarlılık bloğu ön kayıtlı metinden "
                         "farklı (D-465: metin eşitliği)")

    def test_yayin_tavani_SONUC_paragrafi_ON_KAYITLI_METNE_ESIT(self):
        kj = K["kosumlar"]["udp_jetson_olculmus"]["karar_kadansi_hz"]
        kt = K["kosumlar"]["udp_tavan"]["karar_kadansi_hz"]
        beklenen = _bosluk(self.SONUC.format(
            k1=TR(kj, 3), k2=TR(kt, 1),
            s1=K["kosumlar"]["saha_jetson_olculmus"]["yayinlanan_karar"],
            s2=K["kosumlar"]["saha_tavan"]["yayinlanan_karar"],
            u1=K["kosumlar"]["udp_jetson_olculmus"]["yayinlanan_karar"],
            u2=K["kosumlar"]["udp_tavan"]["yayinlanan_karar"]))
        self.assertEqual(beklenen, _paragraf(BOLUM_3, "**Sonuç (D-466"),
                         "FDR §3.3.4.3.3 'Sonuç (D-466)' bloğu ön kayıtlı "
                         "metinden farklı (D-465: metin eşitliği)")


class BelgeKilidi(unittest.TestCase):
    """ON_KAYIT / README kilidi — D-453, D-460, D-461."""

    OLCUT = ("Hat doluluk orani yuzde 80,0 ya da uzeri cikarsa kirmizi risk "
             "satiri acilir.")

    def setUp(self):
        self.on = ON_KAYIT.read_text(encoding="utf-8")
        self.rm = README.read_text(encoding="utf-8")

    def test_olcut_her_belgede_TAM_BIR_KEZ(self):
        """D-461: olcutun VARLIGI degil TEKLIGI korunur."""
        for ad, metin in (("ON_KAYIT", self.on), ("README", self.rm)):
            self.assertEqual(
                1, _kez(_normallestir(metin), self.OLCUT),
                f"{ad}: rapor olcutu normallestirilmis metinde tam bir kez "
                "gecmeli (cizilip yeniden yazilmis ya da ikinci kez eklenmis)")

    def test_rakip_esik_yok(self):
        """Ayni yuzeyde ikinci/gevsetilmis bir esik bulunamaz."""
        on4 = self._yuzey(self.on, "## 4.")
        rm = self._yuzey(self.rm, "## rapor olcutunun karsiligi")
        for ad, metin in (("ON_KAYIT SS4", on4), ("README olcut bolumu", rm)):
            self.assertEqual({M.RAPOR_DOLULUK_ESIGI_YUZDE},
                             _esik_degerleri(metin),
                             f"{ad}: rakip ya da eksik esik")

    def test_celiskili_ikinci_hukum_yok(self):
        on4 = self._yuzey(self.on, "## 4.")
        rm = self._yuzey(self.rm, "## rapor olcutunun karsiligi")
        for sozcuk in _CELISKILI_IKINCI_HUKUM:
            self.assertNotIn(sozcuk, on4, f"ON_KAYIT SS4: '{sozcuk}'")
            self.assertNotIn(sozcuk, rm, f"README olcut bolumu: '{sozcuk}'")

    def test_kapi_degil_hukmu_duruyor(self):
        for ad, metin in (("ON_KAYIT", self.on), ("README", self.rm)):
            self.assertIn("kapi degildir", _ara(_normallestir(metin)), ad)

    def test_olculemedi_hukumleri_olumluya_cevrilmemis(self):
        for ad, metin in (("ON_KAYIT", self.on), ("README", self.rm)):
            s = _ara(_normallestir(metin))
            self.assertIn("ecc durumu: olculemedi", s, f"{ad}: ECC hukmu yok")
            for sozcuk in _OLUMLU_CEVIRME:
                self.assertIsNone(
                    re.search(rf"ecc[^.]{{0,120}}?{re.escape(sozcuk)}", s),
                    f"{ad}: ECC hukmu '{sozcuk}' ile olumluya cevrilmis")

    def test_beyaz_liste_disi_cizme_isareti_yok(self):
        """D-460 karar 2: bilinmeyen bir cizme sozdizimi sessizce gecemez."""
        for ad, metin in (("ON_KAYIT", self.on), ("README", self.rm)):
            kalan = _KALAN_CIZME.search(_cizili_ayikla(_kod_ayikla(metin)))
            self.assertIsNone(kalan, f"{ad}: beyaz listede olmayan cizme "
                                     f"isareti: {kalan!r}")

    def test_kanonik_yardimciya_gecis_beyani(self):
        """T242 borcunun beyani her iki belgede ve bu testte durmali."""
        for ad, metin in (("ON_KAYIT", self.on), ("README", self.rm),
                          ("nobetci", Path(__file__).read_text(encoding="utf-8"))):
            s = _ara(metin)
            self.assertIn("t242", s, ad)
            self.assertIn("belge_kilidi.py", s, ad)

    @staticmethod
    def _yuzey(metin, bas):
        """Bir `## ` baslikli KABUL YUZEYININ normallestirilmis metni.
        Satir sonlari korunur; sinir bir sonraki `## ` basligidir."""
        m = _sadelestir(_normallestir(metin))
        i = m.index(_sadelestir(bas))
        j = m.find("\n## ", i + 1)
        return m[i:j if j > 0 else len(m)]


class KilitYordamiKendiniSiniyor(unittest.TestCase):
    """Normallestirme gercekten deliyor mu — mutasyonlar TEK TEK denenir."""

    OLCUT = BelgeKilidi.OLCUT

    def test_cizili_bicimleri_ayiklanir(self):
        for bicim in ("~~80,0~~", "~80,0~", "<del>80,0</del>",
                      "<s class='x'>80,0</s>", "<STRIKE>80,0</STRIKE>",
                      "<S>80,<del>0</del>0</S>"):
            self.assertNotIn("80,0", _cizili_ayikla(bicim), bicim)

    def test_satir_asan_cizik_ayiklanir(self):
        self.assertEqual("a  c", _cizili_ayikla("a ~~b\nx~~ c"))

    def test_tek_tilde_satir_asmaz(self):
        """'~200 B' gibi tek tildeler yanlislikla cizik sayilmamali."""
        metin = "olcum ~200 B cerceve\nbaska satir ~3,3/s yayin"
        self.assertEqual(metin, _cizili_ayikla(metin))

    def test_vurgu_ve_tipografi_duzlenir(self):
        for varyant in ("yuzde **80,0**", "yuzde _80,0_", "yuzde 80,0"):
            self.assertIn("yuzde 80,0", _normallestir(varyant))
        self.assertEqual("FDA'da 'kod' \"alinti\"",
                         _normallestir("FDA’da `kod` “alinti”"))

    def test_es_anlamli_geri_donus_esik_olarak_gorulur(self):
        for varyant in ("doluluk en az %80,0 ise", "doluluk %80,0 asarsa",
                        "doluluk ≥ %80,0", "doluluk yuzde 80,0 ve uzeri"):
            self.assertEqual({80.0}, _esik_degerleri(varyant), varyant)

    def test_ikinci_gevsetilmis_esik_YAKALANIR(self):
        metin = ("Hat doluluk orani yuzde 80,0 ya da uzeri cikarsa risk. "
                 "Gozden gecirilmis olcut: doluluk en az %90,0 ise risk.")
        self.assertEqual({80.0, 90.0}, _esik_degerleri(metin))

    def test_olcut_cizilip_yeniden_yazilirsa_sayim_bir_kalir_ama_ikinci_kopya_yakalanir(self):
        tek = f"a {self.OLCUT} b"
        self.assertEqual(1, _kez(_normallestir(tek), self.OLCUT))
        cift = f"a {self.OLCUT} b {self.OLCUT} c"
        self.assertEqual(2, _kez(_normallestir(cift), self.OLCUT))
        cizili = f"a ~~{self.OLCUT}~~ b"
        self.assertEqual(0, _kez(_normallestir(cizili), self.OLCUT))

    def test_kalan_cizme_isareti_bulunur(self):
        self.assertIsNotNone(_KALAN_CIZME.search(_cizili_ayikla("<strike>a")))
        self.assertIsNone(_KALAN_CIZME.search(_cizili_ayikla("~~a~~ duz metin")))

    def test_kod_araligindaki_cizme_ornegi_yanlis_alarm_vermez(self):
        """Belgeleme ornegi (`<del>`) kilidi dusurmemeli; KOD DISI olan dusurur."""
        ornek = "bicimler: `<del>` ve `~x~` sayilir"
        self.assertIsNone(
            _KALAN_CIZME.search(_cizili_ayikla(_kod_ayikla(ornek))))
        gercek = "olcum <del>OLCULEMEDI</del> tamam"
        self.assertNotIn("OLCULEMEDI",
                         _cizili_ayikla(_kod_ayikla(gercek)))
        self.assertIsNotNone(
            _KALAN_CIZME.search(_cizili_ayikla(_kod_ayikla("olcum <strike>x"))))

    def test_rakam_bosluklari_kaldirilir(self):
        self.assertEqual("1550097 B", _bosluksuz("1 550 097 B"))
        self.assertEqual("60 s'de 200", _bosluksuz("60 s'de 200"))


class ReadmeSayilariArtefakttan(unittest.TestCase):
    def setUp(self):
        self.s = _ara(_normallestir(README.read_text(encoding="utf-8")))

    def test_cerceve_boyutlari(self):
        for tip in TIPLER:
            self.assertIn(_ara(f"{tip} {B['N1_tip_basina_bayt'][tip]} B"),
                          self.s, tip)

    def test_egri_sayilari(self):
        u = EGRI["uretim_yolu"]
        tavan = str(EGRI["sozlesme_tavani_waypoint"])
        for ifade in (f"{TR((u['20'] - u['10']) / 10.0, 1)} B/waypoint",
                      f"{TR((EGRI['en_genis']['20'] - EGRI['en_genis']['10']) / 10.0, 1)} B/waypoint",
                      f"{u[tavan]} B'ye cikar"):
            self.assertIn(_ara(ifade), self.s, ifade)

    def test_veri_hizi_araligi(self):
        def aralik(al, basamak=1):
            d = [al(K["kosumlar"][a]) for a in FDR_KOSUM.values()]
            return f"{TR(min(d), basamak)}–{TR(max(d), basamak)}"
        for ifade in (
            aralik(lambda r: r["veri_hizi"]["gonderilen_bayt_s"]) + " B/s",
            aralik(lambda r: r["hat_yuku"]["gonderilen_bayt_s"]) + " B/s",
            aralik(lambda r: r["veri_hizi"]["gonderilen_paket_s"]) + " pkt/s",
            aralik(lambda r: r["veri_hizi"]["tepe_gonderilen_bayt_s"], 0)
            + " B/s",
            aralik(lambda r: r["gorev_toplami"]["iha_toplam_bayt"], 0) + " B",
            aralik(lambda r: r["gorev_toplami"]["ika_toplam_bayt"], 0) + " B",
        ):
            self.assertIn(_ara(ifade), self.s, ifade)

    def test_yayin_tavani_bulgusu_readmede(self):
        for a, b in (("saha_jetson_olculmus", "saha_tavan"),
                     ("udp_jetson_olculmus", "udp_tavan")):
            ilk = K["kosumlar"][a]["yayinlanan_karar"]
            son = K["kosumlar"][b]["yayinlanan_karar"]
            self.assertIn(_ara(f"{a.split('_')[0]} {ilk}/{son}"), self.s)
        self.assertIn(_ara("1 karar/s"), self.s)

    def test_en_yuksek_doluluk_ve_hukum(self):
        d = max(K["kosumlar"][a]["doluluk"]["paylasimli_yuzde"]
                for a in FDR_KOSUM.values())
        self.assertIn(_ara(f"%{TR(d, 2)}"), self.s)
        self.assertLess(d, M.RAPOR_DOLULUK_ESIGI_YUZDE)
        self.assertIn("risk satiri acilmadi", self.s)

    def test_kapi_ciktilari_yerinde_ve_hukumleri_dosyadan(self):
        """README'deki kapi hukumleri `kapi/` ham ciktilarindan dogrulanir."""
        kapi = DIZIN / "kapi"
        beklenen = {
            "genel_kapi.txt": "GENEL KAPI (madde 14): GECTI",
            "test_fdr.txt": "OK",
            "test_faz_b_protocol.txt": "OK",
            "test_sik_genis.txt": "OK",
            "test_comms.txt": "OK",
            "test_iha_sender.txt": "OK",
            "test_ika.txt": "OK",
            "akis_diyagram.txt": "TÜM DÜĞÜMLER TUTTU",
            "taban_kiyas.txt": "T243 kaynakli YENI dusuk YOK",
        }
        for ad, imza in beklenen.items():
            yol = kapi / ad
            self.assertTrue(yol.is_file(), f"kapi ciktisi yok: {yol}")
            self.assertIn(_ara(imza), _ara(yol.read_text(encoding="utf-8")), ad)
        self.assertTrue((kapi / "tam_suit.txt").is_file())
        self.assertIn("kapi/", self.s)

    def test_tam_suit_dusukleri_GIZLENMEMIS(self):
        """Kotu haber rapordan dusmesin: suit temiz DEGIL diye yazili olmali."""
        self.assertIn(_ara("Tam suit bu worktreede temiz DEGILDIR"), self.s)
        self.assertIn(_ara("taban_kiyas"), self.s)
        for sozcuk in _OLUMLU_CEVIRME:
            self.assertNotIn(_ara(f"tam suit {sozcuk}"), self.s)

    def test_h2c_dusugu_OLCUMLE_raporlanmis(self):
        """Birlesimden sonra gorunen H2c dusugu ve ucuncu olcum kayitli olmali."""
        kapi = DIZIN / "kapi"
        for ad in ("tam_suit.txt", "tam_suit_2.txt", "tam_suit_t243siz.txt"):
            self.assertTrue((kapi / ad).is_file(), f"kanit dosyasi yok: {ad}")
        t243siz = (kapi / "tam_suit_t243siz.txt").read_text(encoding="utf-8")
        self.assertIn("test_H2c_olcek_1_5_hakem_ekrani", t243siz,
                      "T243'suz kosumda H2c dusugu yok — README'deki hukum "
                      "artefaktla celisiyor")
        self.assertIn(_ara("T243'ten DEGIL"), self.s)
        self.assertIn(_ara("tam_suit_t243siz.txt"), self.s)

    def test_D466_SONRASI_tam_suit_te_T243_dusugu_YOK(self):
        """D-466 duzeltmesinden sonraki tam suit kosumu: T243 modulu temiz.

        Tam kume esitligi KILIT DEGILDIR: suit ici kararsizlik olculdu
        (kapi/kararsiz_faz_b_iha_komut_alici.txt). Olculen sey sudur — bu isin
        DOKUNDUGU modul tam suit icinde hic dusuk uretmiyor. Kume farki
        README'de ham dosyalarla sayilarak yazilir.
        """
        kapi = DIZIN / "kapi"
        yol = kapi / "tam_suit_5.txt"
        self.assertTrue(yol.is_file(), "kanit dosyasi yok: tam_suit_5.txt")
        metin = yol.read_text(encoding="utf-8")
        self.assertIsNotNone(re.search(r"^Ran \d+ tests? in ", metin, re.M),
                             "tam_suit_5.txt yarim (kosum tamamlanmamis)")
        self.assertIsNotNone(re.search(r"^(OK|FAILED)\b", metin, re.M),
                             "tam_suit_5.txt yarim (ozet satiri yok)")
        t243 = [x.strip() for x in metin.splitlines()
                if x.startswith(("FAIL:", "ERROR:"))
                and "test_t243_paket_boyutu" in x]
        self.assertEqual([], t243,
                         "tam suit icinde T243 nobetcisi dusuyor")
        for ad in ("tam_suit_3.txt", "tam_suit_4.txt",
                   "kararsiz_faz_b_iha_komut_alici.txt"):
            self.assertTrue((kapi / ad).is_file(), f"kanit dosyasi yok: {ad}")
        for ifade in ("tam_suit_5.txt", "kararsiz_faz_b_iha_komut_alici.txt"):
            self.assertIn(_ara(ifade), self.s, ifade)

    def test_ilk_kosumun_eksikligi_yazili(self):
        """Yeniden kosum SEBEBI ve yonu (sayi KOTULESTI) rapordan dusmemeli."""
        self.assertIn("kosum_ciktisi_v1_eksik.txt", self.s)
        self.assertIn("kotulestirdi", self.s)
        self.assertTrue((DIZIN / "kosum_ciktisi_v1_eksik.txt").is_file())


if __name__ == "__main__":
    unittest.main()
