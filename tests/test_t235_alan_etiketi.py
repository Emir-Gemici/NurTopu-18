"""T235-B/D kilitleri — alan-olcekli yol etiketi (A0), KBH izdusumu (A1), hiz kapisi,
tezgah negatif kontrolu (K3n), kapi/hukum mantigi ve tezgah ciktisinin tohumla bayt-es
yeniden uretimi.

On kayit: results/fdr_sprint_20260910/H1/t235/ON_KAYIT.md SS1, SS2, SS3, SS5, SS6.
Tezgah: simulation/mujoco/t235_etiket_tezgahi.py -> H1/t235/olcum/ (benzetim, saha olcumu degil).

Mutasyon hedefleri (gercek dosyada; hepsi yakalanmali): W/6 -> W/3 · x aynasi · kerteriz (beta)
isareti · montaj yaw isareti · hiz kapisinin kaldirilmasi (+ tezgah kapi/hukum mantigi).

D-453 (mimar kurali): belge kilitleri CIZILI ARALIKLAR AYIKLANMIS metinde arar
(`re.sub(r"~~.*?~~", "", m, flags=re.S)`). ON_KAYIT degerleri ayiklanmis metinden AYRISTIRILIR
ve KUME esitligiyle karsilastirilir: eski deger cizilip yenisi yazilirsa, ayni bolume celisen
ikinci bir deger eklenirse ya da kalin/tipografik bir varyantla baska deger yazilirsa kilit
DUSER. Olcum README'si kayitli JSON'lardan uretilen metne TAM esittir: cizili araliga alinip
"GECTI" yazilmis bir hukum de bir bayt degisikligidir ve kilidi dusurur.
"""

import json
import math
import re
import sys
import unittest
from pathlib import Path

import numpy as np

KOK = Path(__file__).resolve().parents[1]
for _p in (KOK / "codes", KOK / "simulation" / "mujoco", KOK / "simulation" / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import karar_sozlesmesi as ks  # noqa: E402

ON_KAYIT = KOK / "results" / "fdr_sprint_20260910" / "H1" / "t235" / "ON_KAYIT.md"

# Tipografik kesme/tirnak tek bicime (D-453: "’ ´ ` kesme" varyantlari kilidi delemez).
_KESME = str.maketrans({"’": "'", "‘": "'", "´": "'", "`": "'", "ʼ": "'",
                        "“": '"', "”": '"'})
_SAYI = r"(\d+(?:[.,]\d+)?)"
# D-453 + 12 Eylul genislemesi: cizili aralik bicimleri. Tek tilde GFM kuralindadir (sinir
# tildesinin ic yani bosluk OLAMAZ) — yoksa ON_KAYIT'taki "e_c ~ N(0, σ_c²)" dagilim tildeleri
# yanlislikla aralik sayilirdi.
_CIZILI = re.compile(r"~~.*?~~|~(?!\s)[^~\n]*?(?<!\s)~"
                     r"|<del\b[^>]*>.*?</del>|<s\b[^>]*>.*?</s>", re.S | re.I)
# Kalin/italik isaretleri. `_` yalniz MARKDOWN vurgusu oldugunda silinir: σ_c, kosum_tur3_uretim
# gibi tanimlayicilardaki alt cizgi KORUNUR.
_YILDIZ = re.compile(r"\*+")
_ALTCIZGI = re.compile(r"(?<!\w)_{1,2}(?=\S)|(?<=\S)_{1,2}(?!\w)")


def _tezgah():
    import t235_etiket_tezgahi as t
    return t


def _cizili_ayikla(metin):
    """D-453 (+12 Eylul): ~~...~~ (satir asan), tek tilde ~...~, <del>...</del> ve <s>...</s>
    araliklari metinden CIKARILIR. Ic ice sarmalar icin sabit noktaya kadar yinelenir."""
    onceki = None
    while onceki != metin:
        onceki, metin = metin, _CIZILI.sub("", metin)
    return metin


def _normallestir(metin):
    """Belge kilitlerinin aradigi NORMALLESTIRILMIS metin (D-453 + 12 Eylul genislemesi):
    cizili araliklar ayiklanir, kalin/italik isaretleri (**, *, _) kaldirilir, tipografik
    kesme/tirnak duz karsiligina cevrilir. Boylece "≥ %**98**,0" ya da "≥ %98,0" varyantlari
    ayni degeri verir ve kilit ikisini de yakalar."""
    m = _cizili_ayikla(metin).translate(_KESME)
    return _ALTCIZGI.sub("", _YILDIZ.sub("", m))


def _on_kayit_bolum(no):
    """ON_KAYIT "## <no>." bolum(ler)inin NORMALLESTIRILMIS metni (bkz. `_normallestir`).
    Ayni numarali birden cok bolum varsa HEPSI birlestirilir (sonradan eklenen celisen bir
    bolum de ayristirmaya girer)."""
    m = _normallestir(ON_KAYIT.read_text(encoding="utf-8"))
    bolumler = re.findall(rf"^## {no}\.(.*?)(?=^## |\Z)", m, flags=re.S | re.M)
    if not bolumler:
        raise AssertionError(f"ON_KAYIT SS{no} bulunamadi")
    return "\n".join(bolumler)


def _sayi(s):
    return float(s.replace(",", ".").replace("°", "").strip())


def _sayilar(desen, metin):
    return {_sayi(v) for v in re.findall(desen, metin)}


def _liste(grup):
    return tuple(_sayi(v) for v in grup.split(";"))


def _kip_h(metin):
    return [(k, _sayi(h)) for k, h in re.findall(r"(4:3|16:9)[^,()]*,\s*" + _SAYI, metin)]


def _kbh(px, py, **kw):
    ortak = dict(merkez_px=(256.0, 256.0), mpp=0.1, iha_dogu_m=0.0, iha_kuzey_m=0.0,
                 hdg_derece=0.0, montaj_yaw_derece=0.0, kerteriz_derece=0.0)
    ortak.update(kw)
    return ks.kbh_donustur(px, py, **ortak)


class Sabitler(unittest.TestCase):

    def test_alan_genislikleri_sartname_ve_tek_kaynakla_es(self):
        self.assertEqual(20.0, ks.FDA_ALAN_GENISLIK_M)
        self.assertEqual(50.0, ks.HTAB_ALAN_GENISLIK_M)
        self.assertEqual(ks.SENARYO_BOYUTLARI_M["FDA"], ks.FDA_ALAN_GENISLIK_M)
        self.assertEqual(ks.SENARYO_BOYUTLARI_M["HTAB"], ks.HTAB_ALAN_GENISLIK_M)
        import arena
        self.assertEqual(arena.HTAB, ks.HTAB_ALAN_GENISLIK_M)

    def test_hiz_ve_tazelik_esikleri(self):
        self.assertEqual(1.0, ks.ALAN_ETIKETI_HIZ_ESIGI_M_S)
        self.assertEqual(0.5, ks.ALAN_ETIKETI_TAZELIK_S)

    def test_orta_serit_yari_genisligi_W_bolu_6(self):
        self.assertAlmostEqual(20.0 / 6.0, ks.alan_serit_yari_genisligi_m(20.0), places=12)
        self.assertAlmostEqual(50.0 / 6.0, ks.alan_serit_yari_genisligi_m(50.0), places=12)
        for kotu in (None, 0.0, -20.0, float("nan"), float("inf"), True, "20"):
            self.assertIsNone(ks.alan_serit_yari_genisligi_m(kotu), kotu)


class OnKayitKilitleri(unittest.TestCase):
    """Kod ve tezgah sabitleri ON_KAYIT'tan (cizili araliklar ayiklanmis, D-453) AYRISTIRILAN
    degerlerle es. Kume esitligi: ayni bolumdeki her deger sayilir."""

    def test_normallestirme_cizili_bicimlerini_ayiklar(self):
        """D-453 + 12 Eylul genislemesi: ~~...~~ (satir asan), tek tilde, <del>, <s>."""
        self.assertEqual("a  c", _cizili_ayikla("a ~~b\nx~~ c"))
        for bicim in ("~~20260910~~", "~20260910~", "<del>20260910</del>",
                      '<s class="x">20260910</s>', "<S>2026<del>09</del>0910</S>"):
            self.assertEqual("tohum 42", _cizili_ayikla("tohum " + bicim + "42"), bicim)

    def test_normallestirme_dagilim_tildesini_ve_alt_cizgiyi_KORUR(self):
        """Tek tilde GFM kuralindadir (sinir tildesinin ic yani bosluk olamaz): ON_KAYIT'taki
        "e_c ~ N(0, s^2)" dagilim tildeleri silinmez. Tanimlayici alt cizgisi de korunur."""
        metin = "e_c ~ N(0, \u03c3_c\u00b2) her eksende, \u03c3_c \u2208 {0,5; 1,0} m ~ N(0, \u03c3_g\u00b2)"
        self.assertEqual(metin, _normallestir(metin))
        self.assertEqual("kosum_tur3_uretim", _normallestir("kosum_tur3_uretim"))
        b2 = _on_kayit_bolum(2)
        self.assertIn("\u03c3_c", b2)
        self.assertIn("tohum 20260910", b2)

    def test_normallestirme_kalin_italik_ve_kesme_varyantlarini_duzler(self):
        """Ayni deger kalin/italik/tipografik varyantla yazilirsa kilit ayni sayiyi gormeli
        (sozdizimsel varyant kilidi delemez)."""
        for varyant in ("\u2265 %**98**,0", "\u2265 %*98*,0", "\u2265 %_98_,0",
                        "\u2265 %98,0", "\u2265 %__98__,0"):
            self.assertEqual({98.0}, _sayilar(r"\u2265\s*%\s*" + _SAYI, _normallestir(varyant)), varyant)
        self.assertEqual("FDA'da 'kod' \"alinti\"", _normallestir("FDA\u2019da `kod` \u201calinti\u201d"))

    def test_SS1_A0_siniri_W_bolu_6_ve_FDA_20_m(self):
        b1 = _on_kayit_bolum(1)
        self.assertEqual({str(2 * ks.SERIT_SAYISI)}, set(re.findall(r"±\(W/(\d+)\)/mpp", b1)))
        self.assertEqual({ks.FDA_ALAN_GENISLIK_M}, _sayilar(r"FDA\s+" + _SAYI + r"\s*m\b", b1))

    def test_SS5_hiz_ve_tazelik_kapisi(self):
        b5 = _on_kayit_bolum(5)
        self.assertEqual({ks.ALAN_ETIKETI_HIZ_ESIGI_M_S}, _sayilar(_SAYI + r"\s*m/s", b5))
        self.assertEqual({ks.ALAN_ETIKETI_TAZELIK_S},
                         _sayilar(r"tazelik\s*(?:≤|<=|=<|⩽|<)?\s*" + _SAYI + r"\s*s\b", b5))
        # esitlik DAHIL (≤): fonksiyon `v <= esik`, `yas <= tazelik` kullanir
        self.assertRegex(b5, r"yer hızı\s*≤\s*\d")
        self.assertRegex(b5, r"tazelik\s*≤\s*\d")
        self.assertIn("aksi hâlde KARE", b5)

    def test_SS2_izgara_hata_modeli_kapi_tezgahta_aynen(self):
        t = _tezgah()
        b2 = _on_kayit_bolum(2)
        # Izgara
        self.assertEqual([t.S_DEGERLERI_M],
                         [_liste(g) for g in re.findall(r"\bs\s*∈\s*\{([^}]*)\}\s*m\b", b2)])
        izg = re.findall(r"\(kip, h\)\s*∈\s*\{(.*?)\}\s*\+\s*bilgi hücresi\s*\(([^)]*)\)", b2)
        self.assertEqual(1, len(izg), izg)
        self.assertEqual(list(t.KIP_H), _kip_h(izg[0][0]) + _kip_h(izg[0][1]))
        self.assertEqual(list(t.BILGI_KIP_H), _kip_h(izg[0][1]))
        self.assertEqual({round(t.HFOV_DERECE, 1)}, _sayilar(r"HFOV\s*" + _SAYI + r"\s*°", b2))
        self.assertEqual({t.ODAK_MM, t.SENSOR_GENISLIK_MM}, _sayilar(_SAYI + r"\s*mm\b", b2))
        # Hata modeli
        self.assertEqual({t.TOHUM}, {int(v) for v in re.findall(r"tohum\s+(\d+)", b2)})
        self.assertEqual({t.CEKILIS_N}, {int(v) for v in re.findall(r"hücre başına\s+(\d+)", b2)})
        self.assertEqual([t.SIGMA_C_M], [_liste(g) for g in re.findall(r"σ_c\s*∈\s*\{([^}]*)\}", b2)])
        self.assertEqual([t.SIGMA_PSI_DERECE], [_liste(g) for g in re.findall(r"σ_ψ\s*∈\s*\{([^}]*)\}", b2)])
        self.assertEqual([t.SIGMA_G_M], [_liste(g) for g in re.findall(r"σ_g\s*∈\s*\{([^}]*)\}", b2)])
        self.assertEqual([t.EGIM_ARALIGI_DERECE],
                         [tuple(_sayi(v) for v in g.split(",")) for g in re.findall(r"eğim düzgün\s*\[([^\]]*)\]", b2)])
        self.assertIn("üç yöntem aynı çekilişlerle", b2)
        # Kapi — nominal hucreler
        nom = re.findall(r"nominal hücrelerde\s*—\s*(.*?)\s*—\s*doğru oranı", b2)
        self.assertEqual(1, len(nom), nom)
        self.assertEqual([t.NOMINAL_S_M], [_liste(g) for g in re.findall(r"\bs\s*∈\s*\{([^}]*)\}", nom[0])])
        self.assertEqual({t.NOMINAL_SIGMA_C_M}, _sayilar(r"σ_c\s*=\s*" + _SAYI, nom[0]))
        self.assertEqual({t.NOMINAL_SIGMA_PSI_DERECE}, _sayilar(r"σ_ψ\s*=\s*" + _SAYI, nom[0]))
        self.assertEqual({t.NOMINAL_SIGMA_G_M}, _sayilar(r"σ_g\s*=\s*" + _SAYI, nom[0]))
        self.assertEqual(list(t.NOMINAL_KIP_H), _kip_h(nom[0]))
        # Kapi — esikler
        self.assertEqual({t.KAPI_ORAN_YUZDE}, _sayilar(r"≥\s*%\s*" + _SAYI, b2))
        self.assertEqual({t.KAPI_KARE_FARK_PUAN}, _sayilar(r"KARE'den\s*" + _SAYI + r"\s*puan", b2))
        self.assertEqual(set(t.KAPI_DISI_S_M),
                         _sayilar(r"\bs\s*=\s*" + _SAYI + r"\s*m hücreleri raporlanır, kapıya girmez", b2))
        self.assertEqual({t.ALAN_SIGMA_ASGARI_PAY_M}, _sayilar(r"pay\s*<\s*" + _SAYI + r"\s*m\b", b2))
        # Negatif kontrol K3n
        k3n = re.findall(r"KARE tanımı\s*s\s*=\s*" + _SAYI + r"\s*m, merkezli, hatasız karede\s*\[([^\]]*)\]", b2)
        self.assertEqual([(t.K3N_S_M, t.K3N_KARE_BEKLENEN)],
                         [(_sayi(s), [int(v) for v in g.split(",")]) for s, g in k3n])
        self.assertIn("tezgâh boş sayılır ve hüküm verilmez", b2)
        # Karar kurali (onceden yazili)
        for cumle in ("A0 kapıyı geçerse FDA'da A0 bayrakla açılır.",
                      "A0 düşer A1 geçerse A1 yalnız T235-C poz kolu + tezgâh/SITL kanıtı 21 Eylül'den önce "
                      "hazırsa açılır; değilse KARE kalır.",
                      "Hiçbiri geçmezse KARE kalır."):
            self.assertIn(cumle, b2)

    def test_SS2_tezgah_sabitleri_sayi_olarak(self):
        """Ikinci kilit: ON_KAYIT ve kod BIRLIKTE degistirilse de on kayitli degerler degismez."""
        t = _tezgah()
        self.assertEqual(20260910, t.TOHUM)
        self.assertEqual(2000, t.CEKILIS_N)
        self.assertEqual((5.0, 6.67, 8.0), t.S_DEGERLERI_M)
        self.assertEqual((0.5, 1.0), t.SIGMA_C_M)
        self.assertEqual((2.0, 5.0), t.SIGMA_PSI_DERECE)
        self.assertEqual((1.0, 2.0), t.SIGMA_G_M)
        self.assertEqual((2.0, 3.0), t.EGIM_ARALIGI_DERECE)
        self.assertEqual(99.0, t.KAPI_ORAN_YUZDE)
        self.assertEqual(0.5, t.KAPI_KARE_FARK_PUAN)
        self.assertEqual(1.0, t.ALAN_SIGMA_ASGARI_PAY_M)
        self.assertEqual((("4:3", 32.0), ("16:9", 40.0), ("16:9", 32.0)), t.KIP_H)
        self.assertEqual((("4:3", 32.0), ("16:9", 40.0)), t.NOMINAL_KIP_H)
        self.assertEqual((1.0, 5.0, 2.0), (t.NOMINAL_SIGMA_C_M, t.NOMINAL_SIGMA_PSI_DERECE, t.NOMINAL_SIGMA_G_M))
        self.assertAlmostEqual(55.3, t.HFOV_DERECE, places=1)

    def test_SS3_K1_beklenenleri(self):
        t = _tezgah()
        b3 = _on_kayit_bolum(3)
        self.assertEqual({(28, 28), (3, 8), (6, 20)}, {(int(a), int(b)) for a, b in re.findall(r"(\d+)/(\d+)", b3)})
        self.assertRegex(b3, r"kosum_tur3'?\s*20\s*\+\s*kerteriz\s*8\b")
        self.assertEqual((28, 28), t.K1_BEKLENEN_A1)
        self.assertEqual({"kerteriz": (3, 8), "kosum_tur3_uretim": (6, 20)}, t.K1_BEKLENEN_KARE)


class A0AlanSeritKarari(unittest.TestCase):
    # mpp 0,05 m/px, W = 20 m -> b = (20/6)/0,05 = 66,667 px; merkez 256 -> sinirlar 189,33 / 322,67
    X0, W, MPP = 0, 512, 0.05

    def _k(self, xs, **kw):
        pix = [(x, 100) for x in xs]
        return ks.alan_serit_karari(pix, kw.get("x0", self.X0), kw.get("w", self.W),
                                    kw.get("mpp", self.MPP), kw.get("alan", ks.FDA_ALAN_GENISLIK_M))

    def test_W6_sinirlari_merkezden(self):
        self.assertEqual(1, self._k([189])[0])
        self.assertEqual(2, self._k([190])[0])
        self.assertEqual(2, self._k([322])[0])
        self.assertEqual(3, self._k([323])[0])
        _k, _s, pay = self._k([256])
        self.assertAlmostEqual(256.0 - 200.0 / 3.0, pay["sol_sinir_px"], places=9)
        self.assertAlmostEqual(256.0 + 200.0 / 3.0, pay["sag_sinir_px"], places=9)

    def test_tam_sinirda_orta_kapali_ve_ayna_simetrik(self):
        """W 24 m -> W/6 = 4 m; mpp 0,0625 -> b = 64 px TAM; merkez 256 -> sinirlar 192 / 320 TAM.
        Orta serit KAPALI (A1: |x| <= W/6 -> 2 ile ayni): sinir pikselinin iki yani da 2."""
        def f(x):
            return ks.alan_serit_karari([(x, 0)], 0, 512, 0.0625, 24.0)[0]
        self.assertEqual((1, 2, 2, 3), (f(191), f(192), f(320), f(321)))
        for x in range(0, 513):
            self.assertEqual({1: 3, 2: 2, 3: 1}[f(x)], f(512 - x), x)

    def test_sinirlar_icerik_kutusunun_merkezini_izler(self):
        # icerik 100..1124 (w 1024): merkez 612 -> sinirlar 545,33 / 678,67
        self.assertEqual(1, self._k([545], x0=100, w=1024)[0])
        self.assertEqual(2, self._k([546], x0=100, w=1024)[0])
        self.assertEqual(2, self._k([678], x0=100, w=1024)[0])
        self.assertEqual(3, self._k([679], x0=100, w=1024)[0])

    def test_kare_genisligine_bagli_DEGIL_KARE_ise_bagli(self):
        """Merkezden 4 m sagdaki rota: A0 her genislikte 3; KARE 512'de 2, 256'da 3."""
        for w in (256, 512, 1024):
            x = w / 2.0 + 4.0 / self.MPP
            self.assertEqual(3, self._k([x], w=w)[0], w)
        self.assertEqual(2, ks.rota_serit_karari([(256 + 80, 0)], 0, 512)[0])

    def test_x_aynasi_simetri(self):
        rng = np.random.default_rng(7)
        for _ in range(200):
            xs = rng.integers(0, 512, rng.integers(1, 40)).astype(float) + 0.25
            k, s, _p = self._k(xs.tolist())
            ka, sa, _pa = self._k((512.0 - xs).tolist())   # merkez 256'ya gore ayna
            self.assertEqual(tuple(reversed(s)), sa)
            # Etiket aynasi yalniz TEKIL cogunlukta beklenir: beraberlik kurali (kucuk serit,
            # rota_serit_karari ile ayni) tanim geregi ayna-simetrik DEGILDIR.
            if sorted(s)[-1] != sorted(s)[-2]:
                self.assertEqual({1: 3, 2: 2, 3: 1}[k], ka)

    def test_cogunluk_ve_beraberlik_kucuk_serit(self):
        k, s, _p = self._k([100, 110, 250, 260, 400])
        self.assertEqual((2, 2, 1), s)
        self.assertEqual(1, k)
        self.assertEqual(2, self._k([100, 250, 260])[0])

    def test_pay_bilgisi(self):
        self.assertAlmostEqual(20.0 / 6.0, self._k([256])[2]["pay_m"], places=9)
        self.assertAlmostEqual(1.0, self._k([256 + 200.0 / 3.0 + 20.0])[2]["pay_m"], places=9)
        self.assertAlmostEqual(0.5, self._k([256 - 200.0 / 3.0 - 10.0])[2]["pay_m"], places=9)
        # medyan kazanan seridin DISINDA -> negatif pay
        k, _s, pay = self._k([100, 110, 120, 250, 260, 400, 410])
        self.assertEqual(1, k)
        self.assertLess(pay["pay_m"], 0.0)

    def test_liste_ve_numpy_ayni(self):
        pix = [(190, 3), (400, 5), (401, 9), (20, 2)]
        a = ks.alan_serit_karari(pix, 0, 512, 0.05)
        b = ks.alan_serit_karari(np.array(pix), 0, 512, 0.05)
        self.assertEqual(a[:2], b[:2])
        self.assertEqual(a[2], b[2])

    def test_fail_closed(self):
        bos = (None, (0, 0, 0), None)
        self.assertEqual(bos, self._k([]))
        for mpp in (None, 0.0, -0.1, float("nan"), True):
            self.assertEqual(bos, self._k([256], mpp=mpp), mpp)
        self.assertEqual(bos, self._k([256], w=0))
        self.assertEqual(bos, self._k([256], alan=0.0))
        self.assertEqual(bos, ks.alan_serit_karari([(float("nan"), 1)], 0, 512, 0.05))

    def test_fail_closed_sayisal_olmayan_piksel_istisna_firlatmaz(self):
        for kotu in ([("a", 1)], [(1,)], [[1, 2], [3]], None, 5, [(None, 2)]):
            self.assertEqual((None, (0, 0, 0), None), ks.alan_serit_karari(kotu, 0, 512, 0.05), kotu)
            self.assertEqual((None, (0, 0, 0)), ks.kbh_serit_karari(kotu, **A1KbhSeritKarari.KW), kotu)


class A1KbhDonustur(unittest.TestCase):

    def test_kimlik_ve_x_aynasi(self):
        x, y = _kbh(266, 256)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246)      # goruntu-yukari = ileri
        self.assertAlmostEqual(0.0, x, places=12)
        self.assertAlmostEqual(1.0, y, places=12)
        x, y = _kbh(246, 256, iha_dogu_m=2.0, iha_kuzey_m=3.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(3.0, y, places=12)

    def test_kerteriz_isareti(self):
        # Baslangic -> Hedef = DOGU (beta 90): gozlemcinin sagi GUNEY.
        x, y = _kbh(256, 256, iha_dogu_m=0.0, iha_kuzey_m=-2.0, kerteriz_derece=90.0)
        self.assertAlmostEqual(2.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246, hdg_derece=90.0, kerteriz_derece=90.0)   # ileri piksel = dogu = +y
        self.assertAlmostEqual(0.0, x, places=12)
        self.assertAlmostEqual(1.0, y, places=12)
        # genel: goruntu-yukari = beta ise piksel ekseni KBH ekseniyle cakisir
        for beta in (37.0, 123.0, 250.0, -65.0):
            x, y = _kbh(256 + 50, 256 - 20, hdg_derece=beta - 90.0, montaj_yaw_derece=90.0,
                        kerteriz_derece=beta)
            self.assertAlmostEqual(5.0, x, places=9, msg=beta)
            self.assertAlmostEqual(2.0, y, places=9, msg=beta)

    def test_montaj_yaw_isareti(self):
        # hdg 30 + montaj 60 = goruntu-yukari DOGU; beta 0 -> ileri piksel KBH +x
        x, y = _kbh(256, 246, hdg_derece=30.0, montaj_yaw_derece=60.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)
        x, y = _kbh(256, 246, hdg_derece=0.0, montaj_yaw_derece=90.0)
        self.assertAlmostEqual(1.0, x, places=12)
        self.assertAlmostEqual(0.0, y, places=12)

    def test_sim_izdusumuyle_es(self):
        """Bagimsiz kod: sim_karar_toplayici.piksel_dunya (kerteriz K1 kurali: hdg = 90 - yaw,
        montaj = teta - 90, beta 0, orijin HTAB merkezi)."""
        import sim_karar_toplayici as skt
        rng = np.random.default_rng(20260910)
        for _ in range(300):
            x, y, yaw, teta = rng.uniform(-20, 20), rng.uniform(-20, 20), rng.uniform(-180, 180), rng.choice([0, 90, 180, 270])
            mpp = rng.uniform(0.02, 0.1)
            px, py = rng.uniform(0, 1280), rng.uniform(0, 1280)
            ref = skt.piksel_dunya(px, py, (0, 0.0, x, y, 30.0, math.radians(yaw)), 1280, 1280, mpp,
                                   math.radians(teta))
            kx, ky = ks.kbh_donustur(px, py, merkez_px=(640.0, 640.0), mpp=mpp, iha_dogu_m=x,
                                     iha_kuzey_m=y, hdg_derece=90.0 - yaw,
                                     montaj_yaw_derece=teta - 90.0, kerteriz_derece=0.0)
            self.assertAlmostEqual(ref[0], kx, places=9)
            self.assertAlmostEqual(ref[1], ky, places=9)

    def test_uzaklik_korunur_ve_dizi_skaler_ayni(self):
        kw = dict(iha_dogu_m=4.0, iha_kuzey_m=-7.0, hdg_derece=211.0, montaj_yaw_derece=-33.0,
                  kerteriz_derece=77.0)
        xs = np.array([10.0, 300.0, 511.0])
        ys = np.array([40.0, 256.0, 499.0])
        dx, dy = _kbh(xs, ys, **kw)
        for i in range(3):
            sx, sy = _kbh(float(xs[i]), float(ys[i]), **kw)
            self.assertAlmostEqual(sx, dx[i], places=12)
            self.assertAlmostEqual(sy, dy[i], places=12)
        self.assertAlmostEqual(math.hypot(dx[0] - dx[1], dy[0] - dy[1]),
                               0.1 * math.hypot(xs[0] - xs[1], ys[0] - ys[1]), places=9)

    def test_fail_closed(self):
        self.assertIsNone(_kbh(1, 1, mpp=0.0))
        self.assertIsNone(_kbh(1, 1, mpp=None))
        self.assertIsNone(_kbh(1, 1, hdg_derece=float("nan")))
        self.assertIsNone(_kbh(1, 1, kerteriz_derece=None))
        self.assertIsNone(_kbh(1, 1, iha_dogu_m=True))
        self.assertIsNone(_kbh(1, 1, merkez_px=None))
        self.assertIsNone(_kbh(1, 1, merkez_px=(1.0,)))


class A1KbhSeritKarari(unittest.TestCase):
    # mpp 1/30 m/px, W 20 m -> W/6 = 3,333 m = 100 px
    KW = dict(merkez_px=(256.0, 256.0), mpp=1.0 / 30.0, iha_dogu_m=0.0, iha_kuzey_m=0.0,
              hdg_derece=0.0, montaj_yaw_derece=0.0, kerteriz_derece=0.0)

    def _k(self, xs, **kw):
        a = dict(self.KW)
        a.update(kw)
        return ks.kbh_serit_karari([(x, 256) for x in xs], **a)

    def test_W6_sinirlari_ortasi_kapali(self):
        self.assertEqual(1, self._k([256 - 101])[0])
        self.assertEqual(2, self._k([256 - 100])[0])
        self.assertEqual(2, self._k([256 + 100])[0])
        self.assertEqual(3, self._k([256 + 101])[0])

    def test_alan_genisligi_olcekler(self):
        self.assertEqual(3, self._k([256 + 101])[0])
        self.assertEqual(2, self._k([256 + 101], alan_genislik_m=ks.HTAB_ALAN_GENISLIK_M)[0])
        self.assertEqual(3, self._k([256 + 251], alan_genislik_m=ks.HTAB_ALAN_GENISLIK_M)[0])

    def test_iha_konumu_etiketi_kaydirir(self):
        # IHA alan merkezinin 4 m SOLUNDA (beta 0 -> bati), rota goruntu merkezinde -> sol serit
        self.assertEqual(1, self._k([256], iha_dogu_m=-4.0)[0])
        self.assertEqual(3, self._k([256], iha_dogu_m=4.0)[0])

    def test_cogunluk_beraberlik(self):
        k, s = self._k([100, 110, 256, 257])
        self.assertEqual((2, 2, 0), s)
        self.assertEqual(1, k)

    def test_fail_closed(self):
        self.assertEqual((None, (0, 0, 0)), self._k([]))
        self.assertEqual((None, (0, 0, 0)), self._k([256], mpp=float("nan")))
        self.assertEqual((None, (0, 0, 0)), self._k([256], alan_genislik_m=-1.0))


class HizKapisi(unittest.TestCase):

    def test_sinirlar(self):
        f = ks.alan_etiketi_kullanilabilir_mi
        self.assertTrue(f(1.0, 0.5))
        self.assertTrue(f(0.0, 0.0))
        self.assertTrue(f(0.3, 0.2))
        self.assertFalse(f(math.nextafter(1.0, 2.0), 0.5))
        self.assertFalse(f(1.0, math.nextafter(0.5, 1.0)))
        self.assertFalse(f(3.0, 0.1), "kose bacagi hizi (3 m/s) alan etiketine GIREMEZ")
        self.assertFalse(f(0.5, 0.8), "bayat hiz ornegi")

    def test_fail_closed(self):
        f = ks.alan_etiketi_kullanilabilir_mi
        for v, t in ((None, 0.1), (0.1, None), (float("nan"), 0.1), (0.1, float("nan")),
                     (float("inf"), 0.1), (True, 0.1), (0.1, False), (-0.1, 0.1), (0.1, -0.01),
                     ("0.1", 0.1)):
            self.assertFalse(f(v, t), (v, t))


class TezgahNegatifKontrol(unittest.TestCase):

    def test_K3n_KARE_s5_merkezli_hatasiz_222(self):
        k3n = _tezgah().k3n_kos()
        self.assertTrue(k3n["gecti"])
        for s in k3n["yapilandirmalar"]:
            self.assertEqual([2, 2, 2], s["KARE"], s)
            self.assertEqual([1, 2, 3], s["A0"], s)
            self.assertEqual([1, 2, 3], s["A1"], s)

    def test_tezgah_sabit_uretec_degil(self):
        """KARE s = 8 m'de (32 m, orta ucte-bir |x| < 5,59 m) [1,2,3] vermeli: tezgah ayirt eder."""
        t = _tezgah()
        out = [t.sahne_etiketleri(8.0, "4:3", 32.0, yol, (0, 0), 0.0, (0, 0), [(0, 0)])["KARE"]
               for yol in (1, 2, 3)]
        self.assertEqual([1, 2, 3], out)


class TezgahKameraModeli(unittest.TestCase):

    def test_alan_piksel_ile_kbh_donustur_tur_donus(self):
        """Tezgahin FIZIKSEL kamerasi (alan -> piksel) ile uretim izdusumu (piksel -> KBH) ayni
        isaret sozlesmesinde: gercek pozu ve gercek yaw'i (kerteriz + psi) bilen izdusum her alan
        noktasini geri verir. psi yonu, x aynasi, kerteriz ya da montaj isareti ayrisirsa duser."""
        t = _tezgah()
        rng = np.random.default_rng(11)
        for kip, h in t.KIP_H:
            icerik = t.icerik_kutusu(kip)
            x0, y0, w, hh = icerik
            mpp = t.kare_mpp(kip, h)
            for _ in range(40):
                merkez = rng.uniform(-3.0, 3.0, 2)
                psi = float(rng.uniform(-10.0, 10.0))
                kerteriz = float(rng.uniform(0.0, 360.0))
                montaj = float(rng.choice([0.0, 90.0, 180.0, -90.0, 37.0]))
                noktalar = rng.uniform(-10.0, 10.0, (20, 2))
                pix = t.alan_piksel(noktalar, merkez, psi, mpp, icerik)
                dogu, kuzey = t.alan_to_enu(float(merkez[0]), float(merkez[1]), kerteriz)
                kx, ky = ks.kbh_donustur(pix[:, 0], pix[:, 1], merkez_px=(x0 + w / 2.0, y0 + hh / 2.0),
                                         mpp=mpp, iha_dogu_m=dogu, iha_kuzey_m=kuzey,
                                         hdg_derece=kerteriz - montaj + psi, montaj_yaw_derece=montaj,
                                         kerteriz_derece=kerteriz)
                np.testing.assert_allclose(kx, noktalar[:, 0], atol=1e-9)
                np.testing.assert_allclose(ky, noktalar[:, 1], atol=1e-9)


def _hc(ad, nominal, kapiya, kare, a0, a1_1, a1_2, n=6000):
    def blok(d):
        return {"dogru": d, "sahne_n": n, "oran_yuzde": round(100.0 * d / n, 3)}
    return {"hucre": ad, "nominal": nominal, "kapiya_girer": kapiya, "KARE": blok(kare), "A0": blok(a0),
            "A1": {"sigma_g=1": blok(a1_1), "sigma_g=2": blok(a1_2)}}


class KapiVeHukumMantigi(unittest.TestCase):
    """ON_KAYIT SS2 kapisi ve karar kurali YAPAY hucrelerle, sinir degerlerinde (kayitli olcum
    her dali sinamaz: orada A0 ve A1 ikisi de dusmustur)."""

    def test_kosul1_sinir_tam_yuzde_99_gecer(self):
        t = _tezgah()
        k = t.kapi_degerlendir([_hc("n", True, True, 5000, 5940, 0, 5940)])
        self.assertTrue(k["A0"]["kosul1_gecti"])
        self.assertTrue(k["A1"]["kosul1_gecti"])
        k = t.kapi_degerlendir([_hc("n", True, True, 5000, 5939, 6000, 5939)])
        self.assertFalse(k["A0"]["kosul1_gecti"])
        self.assertFalse(k["A1"]["kosul1_gecti"])

    def test_kosul1_A1_yalniz_sigma_g_2_kosul2_her_sigma_g(self):
        t = _tezgah()
        k = t.kapi_degerlendir([_hc("n", True, True, 5000, 6000, 1000, 5940)])
        self.assertTrue(k["A1"]["kosul1_gecti"], "s_g = 1 nominal degil")
        self.assertFalse(k["A1"]["kosul2_gecti"], "s_g = 1 blogu KARE'den cok kotu: ihlal")
        self.assertEqual(["sigma_g=1"], [v["blok"] for v in k["A1"]["kosul2_ihlaller"]])
        self.assertFalse(k["A1"]["gecti"])

    def test_kosul2_sinir_tam_yarim_puan_gecer(self):
        t = _tezgah()
        # n = 6000: 0,5 puan = 30 sahne
        k = t.kapi_degerlendir([_hc("k", False, True, 5000, 4970, 4970, 4970)])
        self.assertTrue(k["A0"]["kosul2_gecti"])
        self.assertTrue(k["A1"]["kosul2_gecti"])
        k = t.kapi_degerlendir([_hc("k", False, True, 5000, 4969, 4970, 4969)])
        self.assertFalse(k["A0"]["kosul2_gecti"])
        self.assertEqual([-0.517], [v["fark_puan"] for v in k["A0"]["kosul2_ihlaller"]])
        self.assertEqual(["sigma_g=2"], [v["blok"] for v in k["A1"]["kosul2_ihlaller"]])

    def test_kosul2_kapi_disi_hucre_denetlenmez(self):
        t = _tezgah()
        k = t.kapi_degerlendir([_hc("s=5", False, False, 6000, 0, 0, 0)])
        self.assertTrue(k["A0"]["kosul2_gecti"])
        self.assertEqual(0, k["A0"]["kosul2_denetlenen_blok_n"])
        self.assertEqual(0, k["A1"]["kosul2_denetlenen_blok_n"])

    def test_nominal_hucre_yoksa_kapi_gecmez(self):
        t = _tezgah()
        k = t.kapi_degerlendir([_hc("k", False, True, 0, 6000, 6000, 6000)])
        self.assertFalse(k["A0"]["kosul1_gecti"], "bos nominal kume GECMEZ (fail-closed)")
        self.assertFalse(k["A0"]["gecti"])

    def test_kapi_iki_kosulun_VE_si(self):
        t = _tezgah()
        hucreler = [_hc("n", True, True, 5000, 6000, 6000, 6000),
                    _hc("k", False, True, 6000, 5900, 6000, 6000)]     # A0 kosul 2: -1,67 puan
        k = t.kapi_degerlendir(hucreler)
        self.assertTrue(k["A0"]["kosul1_gecti"])
        self.assertFalse(k["A0"]["kosul2_gecti"])
        self.assertFalse(k["A0"]["gecti"])
        self.assertTrue(k["A1"]["gecti"])

    def test_karar_kurali_dort_durum_ve_bos_tezgah(self):
        t = _tezgah()
        sigma = [{"kip": "4:3", "h_m": 32.0, "fda_kullanilir": True},
                 {"kip": "16:9", "h_m": 32.0, "fda_kullanilir": False}]

        def kapi(a0, a1):
            return {"A0": {"gecti": a0}, "A1": {"gecti": a1}}
        h = t.hukum_kur({"gecti": False}, kapi(True, True), sigma)
        self.assertTrue(h["tezgah_bos"])
        self.assertEqual((None, None), (h["A0"], h["A1"]))
        self.assertIn("HUKUM YOK", h["karar"])
        h = t.hukum_kur({"gecti": True}, kapi(True, False), sigma)
        self.assertEqual(("GECTI", "DUSTU"), (h["A0"], h["A1"]))
        self.assertIn("A0 bayrakla acilir", h["karar"])
        h = t.hukum_kur({"gecti": True}, kapi(True, True), sigma)
        self.assertIn("A0 bayrakla acilir", h["karar"], "A0 gecerse A1'e bakilmaz")
        self.assertNotIn("T235-C", h["karar"])
        h = t.hukum_kur({"gecti": True}, kapi(False, True), sigma)
        self.assertEqual(("DUSTU", "GECTI"), (h["A0"], h["A1"]))
        self.assertIn("T235-C poz kolu", h["karar"])
        self.assertIn("degilse KARE kalir", h["karar"])
        h = t.hukum_kur({"gecti": True}, kapi(False, False), sigma)
        self.assertEqual("A0 DUSTU, A1 DUSTU -> KARE kalir (ON_KAYIT SS2).", h["karar"])
        self.assertEqual(["16:9@32m"], h["alan_sigma_ile_fda_disi_yapilandirma"])
        self.assertIn("YKS", h["her_durumda"])

    def test_hucre_siniflari_izgarada(self):
        t = _tezgah()
        izg = t.izgara()
        self.assertEqual(3 * 3 * 2 * 2, len(izg))
        bayrak = {c: t.hucre_bayraklari(*c) for c in izg}
        self.assertEqual({(6.67, "4:3", 32.0, 1.0, 5.0), (6.67, "16:9", 40.0, 1.0, 5.0),
                          (8.0, "4:3", 32.0, 1.0, 5.0), (8.0, "16:9", 40.0, 1.0, 5.0)},
                         {c for c in izg if bayrak[c]["nominal"]})
        kapiya = {c for c in izg if bayrak[c]["kapiya_girer"]}
        self.assertEqual({c for c in izg if c[0] != 5.0 and (c[1], c[2]) != ("16:9", 32.0)}, kapiya)
        self.assertEqual(16, len(kapiya))
        self.assertEqual({c for c in izg if (c[1], c[2]) == ("16:9", 32.0)},
                         {c for c in izg if bayrak[c]["bilgi_hucresi"]})


class TezgahYenidenUretim(unittest.TestCase):
    """Kapiyi belirleyen 4 NOMINAL hucre tohumla yeniden uretilir ve kayitli tabloyla BAYT-ES
    (kayit ayri bir surecte uretildi); kayitli kapi ve hukum on kayitli kuralla tablodan yeniden
    kurulur. Boylece tablo, kapi, hukum ya da README elle degistirilemez."""

    @classmethod
    def setUpClass(cls):
        t = _tezgah()
        cls.t = t
        cls.kayit = json.loads((t.CIKTI_DIZIN / t.K3_JSON).read_text(encoding="utf-8"))
        cls.nominal = [c for c in t.izgara() if t.hucre_bayraklari(*c)["nominal"]]
        cls.a = t.tezgah_kos(cls.nominal)

    def test_nominal_hucreler_kayitli_tabloyla_bayt_es(self):
        kayitli = {h["hucre"]: h for h in self.kayit["hucreler"]}
        self.assertEqual(4, len(self.a["hucreler"]))
        for h in self.a["hucreler"]:
            self.assertEqual(self.t.json_metni(kayitli[h["hucre"]]).encode("utf-8"),
                             self.t.json_metni(h).encode("utf-8"), h["hucre"])
        for anahtar in ("k3n", "alan_sigma", "parametreler", "etiket", "on_kayit"):
            self.assertEqual(self.t.json_metni(self.kayit[anahtar]), self.t.json_metni(self.a[anahtar]), anahtar)

    def test_kayitli_hucre_kumesi_ve_bayraklar(self):
        t = self.t
        self.assertEqual([t.hucre_anahtari(*c) for c in t.izgara()], [h["hucre"] for h in self.kayit["hucreler"]])
        for c, h in zip(t.izgara(), self.kayit["hucreler"]):
            b = t.hucre_bayraklari(*c)
            self.assertEqual((b["bilgi_hucresi"], b["kapiya_girer"], b["nominal"]),
                             (h["bilgi_hucresi"], h["kapiya_girer"], h["nominal"]), h["hucre"])
            self.assertEqual(t.ETIKET, h["etiket"])
            self.assertEqual(3 * t.CEKILIS_N, h["sahne_n"])

    def test_kayitli_kapi_ve_hukum_on_kayit_kuralindan(self):
        """Hukum tablodan on kayitli kuralla yeniden kurulur; elle yazilmis bir hukum yoktur."""
        t = self.t
        kapi = t.kapi_degerlendir(self.kayit["hucreler"])
        self.assertEqual(self.kayit["kapi"], json.loads(json.dumps(kapi)))
        self.assertEqual(self.kayit["hukum"],
                         json.loads(json.dumps(t.hukum_kur(self.kayit["k3n"], kapi, self.kayit["alan_sigma"]))))

    def test_duyarlilik_kayitli_tablodan_TURETILIR_bayt_es(self):
        """🔴 `kapi_duyarliligi.json` bir OLCUM DEGILDIR: kayitli k3 tablosunun SAF
        fonksiyonudur (cekilis, rasterleme, rastgelelik yok). Yeniden turetim BAYT-ES olmali;
        elle yazilmis ya da baska bir kosumdan gelmis tek satir kalamaz."""
        t = self.t
        mevcut = (t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8")
        self.assertEqual(mevcut, t.json_metni(t.kapi_duyarliligi(self.kayit)))

    def test_duyarlilik_kapiya_giren_16_hucre_sayilari_kayittan_KOPYA(self):
        t = self.t
        duy = json.loads((t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8"))
        self.assertTrue(duy["yeni_olcum_yok"])
        self.assertEqual(16, len(duy["hucreler"]))
        self.assertEqual(len(t.izgara()) - 16, duy["kapi_disi_hucre_n"])
        kayitli = {h["hucre"]: h for h in self.kayit["hucreler"]}
        for h in duy["hucreler"]:
            c = t.izgara()[h["izgara_indeksi"]]
            self.assertEqual(t.hucre_anahtari(*c), h["hucre"])
            self.assertTrue(t.hucre_bayraklari(*c)["kapiya_girer"], h["hucre"])
            self.assertEqual(t.json_metni(kayitli[h["hucre"]]),
                             t.json_metni({k: v for k, v in h.items() if k != "izgara_indeksi"}),
                             h["hucre"])
        kapi = t.kapi_degerlendir(duy["hucreler"])
        self.assertEqual(duy["kapi"], json.loads(json.dumps(kapi)))
        self.assertEqual(("DUSTU" if not kapi["A0"]["gecti"] else "GECTI",
                          "DUSTU" if not kapi["A1"]["gecti"] else "GECTI"), (duy["A0"], duy["A1"]))
        # Duyarlilik hukmu: kapi disi 20 hucre (s = 5 m + bilgi hucresi) hukmu TASIMADI.
        self.assertTrue(duy["tam_tablo_kapisiyla_ayni"])
        self.assertEqual(self.kayit["kapi"], duy["kapi"])

    def test_D457_kosullu_on_kayit_kayitli_tablodan_TURETILIR(self):
        """D-457 ön kaydi (kamera kipi olculmeden once yazildi): 4:3 olculurse A0 kosullu
        ACILIR; 16:9 olculurse ve kip olculemezse KARE kalir. Uc hukum de kayitli tablodan
        AYNI esikle turetilir — elle yazilmis degil."""
        t = self.t
        duy = json.loads((t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8"))
        d = duy["d457_kosullu"]["kip_olculurse"]
        self.assertEqual({"4:3", "16:9"}, set(d))
        self.assertEqual({"yapilandirma": "4:3@32m", "A0": "GECTI", "A1": "DUSTU",
                          "fda_etiketi": "A0", "a0_bayrakla_acilir": True}, d["4:3"])
        self.assertEqual({"yapilandirma": "16:9@40m", "A0": "DUSTU", "A1": "DUSTU",
                          "fda_etiketi": "KARE", "a0_bayrakla_acilir": False}, d["16:9"])
        self.assertEqual({"fda_etiketi": "KARE", "a0_bayrakla_acilir": False},
                         duy["d457_kosullu"]["kip_olculemezse"])
        # Bugunku hukum: A0 ve A1 DUSTU -> KARE kalir, T235-C poz kolu ACILMAZ.
        self.assertEqual({"A0": "DUSTU", "A1": "DUSTU", "fda_etiketi": "KARE",
                          "t235c_poz_kolu_acilir": False}, duy["bugunku_hukum"])
        self.assertEqual({"DUSTU"}, {v["A1"] for v in d.values()})
        # Yapilandirma kapisi AYNI kapi_degerlendir ile, yalniz hucre kumesi dar.
        for kip, h in t.NOMINAL_KIP_H:
            y = duy["yapilandirma_basina"][f"{kip}@{h:g}m"]
            alt = [c for c in self.kayit["hucreler"] if f"|{kip}@{h:g}m|" in c["hucre"]]
            self.assertEqual(len(alt), y["hucre_n"])
            self.assertEqual(y["kapi"], json.loads(json.dumps(t.kapi_degerlendir(alt))))

    def test_D457_esik_gevsetilmedi(self):
        """Kosullu yeniden hukum bir GEVSETME degildir: esikler ON_KAYIT SS2 sabitleridir ve
        kosullu dalda da aynen kullanilir (bkz. `test_SS2_tezgah_sabitleri_sayi_olarak`)."""
        t = self.t
        duy = json.loads((t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8"))
        y43 = duy["yapilandirma_basina"]["4:3@32m"]["kapi"]["A0"]
        oranlar = [sat["oran_yuzde"] for sat in y43["kosul1_nominal_oran"]]
        self.assertEqual(2, len(oranlar))
        self.assertTrue(all(o >= t.KAPI_ORAN_YUZDE for o in oranlar), oranlar)
        self.assertEqual([], y43["kosul2_ihlaller"])
        # 16:9@40m'de nominal orandan EN AZ biri esigin altinda -> kosullu A0 orada acilmaz.
        y169 = duy["yapilandirma_basina"]["16:9@40m"]["kapi"]["A0"]
        self.assertTrue(any(sat["oran_yuzde"] < t.KAPI_ORAN_YUZDE
                            for sat in y169["kosul1_nominal_oran"]))

    def test_README_kayitli_jsonlardan_uretilen_metne_tam_esit(self):
        """README elle duzenlenemez: kayitli uc JSON'dan uretilen metne TAM esit (satir sonu
        normallesmis — autocrlf checkout'ta da es). Cizili araliga alinip yerine "GECTI" yazilmis
        bir hukum de bir farktir ve kilidi dusurur (D-453)."""
        t = self.t
        k1 = json.loads((t.CIKTI_DIZIN / t.K1_JSON).read_text(encoding="utf-8"))
        duy = json.loads((t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8"))
        mevcut = (t.CIKTI_DIZIN / "README.md").read_text(encoding="utf-8")
        self.assertEqual(t.readme_metni(self.kayit, k1, duy), mevcut)
        # ek okuma: NORMALLESTIRILMIS metinde hukum JSON'daki hukumdur. Hukum sozcugu cizilip
        # ("~~DUSTU~~ GECTI", "<del>DUSTU</del>") yerine bir baskasi yazilirsa bu kilit DUSER.
        duy = json.loads((t.CIKTI_DIZIN / t.DUY_JSON).read_text(encoding="utf-8"))
        ayik = _normallestir(mevcut)
        self.assertIn(f'A0: {self.kayit["hukum"]["A0"]}', ayik)
        self.assertIn(f'A1: {self.kayit["hukum"]["A1"]}', ayik)
        self.assertIn(self.kayit["hukum"]["karar"], ayik)
        bh = duy["bugunku_hukum"]
        self.assertIn("FDA'da yayınlanan yol etiketi: " + bh["fda_etiketi"] + ".", ayik)
        self.assertIn("AÇILMAZ" if not bh["t235c_poz_kolu_acilir"] else "AÇILIR", ayik)
        self.assertNotIn("T235-C (poz kolu / A1'in üretime bağlanması) AÇILIR", ayik)
        # D-457 kosullu satirlari README'de JSON'daki hukumle ayni
        for kip, v in duy["d457_kosullu"]["kip_olculurse"].items():
            self.assertRegex(ayik, rf'\| {re.escape(kip)} \| {re.escape(v["yapilandirma"])} \|'
                                   rf'[^|]*\|[^|]*\| {v["A0"]} \| {v["fda_etiketi"]}')
        self.assertIn("tezgâh yeniden koşulmadı, yeni çekiliş üretilmedi", ayik)


class K1Uygulama(unittest.TestCase):
    """ON_KAYIT SS3 (uygulama testi, bagimsiz kanit DEGIL): A1 yer gercegi pozla 28/28; KARE 3/8 ve
    6/20'yi yeniden uretir. Kosum_tur3 + kerteriz JSON'larindan YENIDEN hesaplanir ve kayitla bayt-es."""

    @classmethod
    def setUpClass(cls):
        t = _tezgah()
        cls.t = t
        cls.kayit_metin = (t.CIKTI_DIZIN / t.K1_JSON).read_text(encoding="utf-8")
        cls.yeni = t.k1_kos()

    def test_yeniden_uretim_kayitla_bayt_es(self):
        self.assertEqual(self.kayit_metin, self.t.json_metni(self.yeni))

    def test_K1_hukmu(self):
        k1 = self.yeni
        self.assertEqual([28, 28], k1["A1_dunya"])
        self.assertTrue(k1["KARE_negatif_kontrol_uretildi"])
        self.assertTrue(k1["KARE_yayin_yeniden_uretildi"])
        self.assertEqual({"kerteriz": [3, 8], "kosum_tur3_uretim": [6, 20]},
                         {k: [o["KARE=dunya"], o["n"]] for k, o in k1["ozet"].items()})
        self.assertLess(k1["kbh_sim_geri_donus_maks_m"], 1e-6)
        self.assertTrue(k1["gecti"])
        self.assertFalse(k1["tezgah_bos"])


if __name__ == "__main__":
    unittest.main()
