"""T58 KAPISI: hakem ekrani ile SAHA PAKETI ayni modelde mi?

Kusur sinifi (D-58/D-60): iki uctan biri cevrilir, digeri unutulur; ekran ile
donanim SESSIZCE farkli modele duser ve hakemde gorulen karar sahada uretilmez.
Bu tam olarak `jetson_paket/models/jetson_derleme_manifest.json`'in basina geldi:
2026-08-05'ten 2026-08-13'e kadar `pc_modeli` **v17** diyordu, oysa pakette
**v21** ONNX vardi. Manifest paket icerigine BAKMIYORDU, kimse fark etmedi
(REVIEW_LOG D-83).

Bu paket bes ucu TEK KAYNAGA baglar ve kaymayi mekanik olarak yakalar:
  1. `comms/yks_gui.py` `ALGI_MODEL_DOSYA`      — hakem ekraninin yukledigi .pt
  2. `jetson_paket/models/`                      — sahaya giden dosyalar
  3. `jetson_paket/models/jetson_derleme_manifest.json` — paketin kunyesi
  4. HER IKI `JETSON_KILAVUZ.md`                 — "ASIL - bunu derle" satiri
  5. `scripts/jetson_fps.py` varsayilanlari      — saha FPS olcumunun modeli/esigi

Model AGIRLIGI YUKLENMEZ; yalniz bayt ve metin kimligi sinanir, boylece kapi
GPU'suz ve saniyeler icinde kosar.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import re
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

KOK = Path(__file__).resolve().parents[1]
if str(KOK / "comms") not in sys.path:
    sys.path.insert(0, str(KOK / "comms"))

import yks_gui  # noqa: E402

PAKET = KOK / "jetson_paket" / "models"
MANIFEST = PAKET / "jetson_derleme_manifest.json"
KILAVUZLAR = (KOK / "JETSON_KILAVUZ.md", KOK / "jetson_paket" / "JETSON_KILAVUZ.md")
JETSON_FPS_YOLU = KOK / "scripts" / "jetson_fps.py"

SURUM_DESENI = re.compile(r"navitas_seg_(v\d+)_best")


def _jetson_fps_modulu():
    spec = importlib.util.spec_from_file_location("navitas_jetson_fps_t62", JETSON_FPS_YOLU)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"jetson_fps modulu yuklenemedi: {JETSON_FPS_YOLU}")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


JETSON_FPS = _jetson_fps_modulu()

# Agirliklar `.gitignore:132` ile depo disinda tutulur (`*.pt`, `*.onnx`).
# Temiz bir klonda bayt kapilari dosya YOKLUGUNDAN duserdi — bu YANLIS sebeple
# kirmizi yanmaktir. Bayt kapilari agirlik varsa kosar; METIN kapilari
# (manifest alanlari, kilavuz `ASIL` satiri) her zaman kosar cunku o dosyalar
# depoda izlenir. Manifest `paket_icerigi` sayesinde temiz klonda bile paketin
# NE OLMASI GEREKTIGI git'te kayitlidir.
AGIRLIK_VAR = any((KOK / "models").glob("*.pt")) and any(PAKET.glob("*.pt"))
AGIRLIK_YOK_SEBEBI = ("model agirliklari diskte yok (.gitignore:132) — bayt "
                      "kapisi atlandi, metin kapilari yine kosuldu")


def _sha(yol: Path) -> str:
    ozet = hashlib.sha256()
    with open(yol, "rb") as fh:
        for blok in iter(lambda: fh.read(1 << 20), b""):
            ozet.update(blok)
    return ozet.hexdigest()


def _surum(ad: str):
    """`navitas_seg_v24_best.pt` -> `v24`. Eslesmezse None."""
    m = SURUM_DESENI.search(ad)
    return m.group(1) if m else None


def _asil_satirlari(metin: str):
    """Kilavuzda `ASIL` isaretli model satirlari."""
    return [s for s in metin.splitlines() if "ASIL" in s and "navitas_seg_" in s]


class UretimModeliKimligiTests(unittest.TestCase):
    """Ekranin yukledigi model gercekten var ve surumu okunabilir mi?"""

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_gui_modeli_depoda_VAR(self):
        yol = KOK / "models" / yks_gui.YksArayuz.ALGI_MODEL_DOSYA
        self.assertTrue(yol.is_file(),
                        f"hakem ekrani var olmayan modeli gosteriyor: {yol}")

    def test_gui_modelinin_surumu_OKUNABILIR(self):
        self.assertIsNotNone(
            _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA),
            "model adi `navitas_seg_vNN_best` kalibina uymuyor; bu kapinin "
            "geri kalani surumu karsilastiramaz")


@unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
class PaketHizasiTests(unittest.TestCase):
    """IRAKSAMA KAPISI — ekran ile sahaya giden dosya AYNI olmali."""

    def setUp(self):
        self.ad = yks_gui.YksArayuz.ALGI_MODEL_DOSYA
        self.surum = _surum(self.ad)

    def test_gui_modeli_PAKETTE_de_var_ve_BAYT_ESIT(self):
        depo = KOK / "models" / self.ad
        paket = PAKET / self.ad
        self.assertTrue(
            paket.is_file(),
            f"hakem ekrani {self.ad} yukluyor ama saha paketinde YOK — "
            f"ekran ile donanim farkli modele duser (D-58/D-60 sinifi)")
        self.assertEqual(_sha(depo), _sha(paket),
                         f"{self.ad} depo ve paket kopyalari FARKLI")

    def test_paketteki_ONNX_ayni_SURUMDEN(self):
        onnxler = [p for p in PAKET.glob("*.onnx")
                   if _surum(p.name) == self.surum]
        self.assertTrue(
            onnxler,
            f"pakette {self.surum} ONNX'i yok; Jetson eski surumu derler")

    def test_paketteki_ONNX_depodan_TURETILMIS(self):
        """Elle duzenlenmis/yeniden uretilmis ONNX yakalanir."""
        depo_ozetleri = {_sha(p) for p in (KOK / "models").glob("*.onnx")}
        for p in KOK.glob("results/onnx_export_*/**/*.onnx"):
            depo_ozetleri.add(_sha(p))
        for p in PAKET.glob("*.onnx"):
            if _surum(p.name) != self.surum:
                continue
            with self.subTest(onnx=p.name):
                self.assertIn(
                    _sha(p), depo_ozetleri,
                    f"{p.name} depodaki hicbir ONNX ile ayni degil")


class ManifestBayATLIGI_Tests(unittest.TestCase):
    """Manifest paketin KENDISINI tarif ediyor mu — yoksa eski kosuyu mu?"""

    def setUp(self):
        self.mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.surum = _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)

    def test_manifest_URETIM_surumunu_gosteriyor(self):
        for alan in ("pc_modeli", "asil_model", "asil_model_pt"):
            with self.subTest(alan=alan):
                self.assertEqual(
                    self.surum, _surum(str(self.mf.get(alan, ""))),
                    f"manifest `{alan}` uretim surumu {self.surum} degil — "
                    f"2026-08-05 bayatliginin tekrari")

    def test_manifest_paket_icerigini_TASIYOR(self):
        self.assertTrue(self.mf.get("paket_icerigi"),
                        "manifest paket icerigini listelemiyor; bayatlik "
                        "yeniden GORUNMEZ olur")

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_manifest_ozetleri_GERCEK_dosyalarla_ESLESIYOR(self):
        for kayit in self.mf["paket_icerigi"]:
            p = PAKET / kayit["dosya"]
            with self.subTest(dosya=kayit["dosya"]):
                self.assertTrue(p.is_file(), "manifestte var, pakette YOK")
                self.assertEqual(kayit["bayt"], p.stat().st_size)
                self.assertEqual(kayit["sha256"], _sha(p))

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_manifest_DISINDA_dosya_kalmamis(self):
        listelenen = {k["dosya"] for k in self.mf["paket_icerigi"]}
        artik = sorted(p.name for p in PAKET.iterdir()
                       if p.name != MANIFEST.name and p.name not in listelenen)
        self.assertEqual([], artik,
                         f"manifest bu dosyalari tarif etmiyor: {artik}")


class SahaOlcumVarsayilanlariTests(unittest.TestCase):
    """T62: FPS betigi uretim manifesti/yorumlayicisindan sapamasin."""

    def setUp(self):
        self.mf = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.args = JETSON_FPS.argumanlar([])

    def test_model_varsayilanlari_manifestin_ASIL_dosyalaridir(self):
        self.assertEqual(self.mf["asil_model_pt"], self.args.pt.name)
        self.assertEqual(self.mf["asil_model"], self.args.onnx.name)
        self.assertEqual(PAKET.resolve(), self.args.pt.parent.resolve())
        self.assertEqual(PAKET.resolve(), self.args.onnx.parent.resolve())

    @unittest.skipUnless(AGIRLIK_VAR, AGIRLIK_YOK_SEBEBI)
    def test_varsayilan_model_yollari_GERCEKTEN_VAR(self):
        self.assertTrue(self.args.pt.is_file(), f"PT varsayilani yok: {self.args.pt}")
        self.assertTrue(self.args.onnx.is_file(), f"ONNX varsayilani yok: {self.args.onnx}")
        if self.args.engine is not None:
            self.assertTrue(self.args.engine.is_file(),
                            f"engine varsayilani olmayan dosyayi gosteriyor: {self.args.engine}")

    def test_engine_yoklugu_HAYALI_yolla_gizlenmiyor(self):
        beklenen = (PAKET / self.mf["asil_model"]).with_suffix(".engine")
        if beklenen.is_file():
            self.assertEqual(beklenen.resolve(), self.args.engine.resolve())
        else:
            self.assertIsNone(
                self.args.engine,
                "Jetson'da derlenmemis engine icin var olmayan varsayilan yol yazilmis",
            )

    def test_engine_yokken_TensorRT_vakasi_ACIKCA_ATLANIYOR(self):
        class SahteAkis:
            def kapat(self):
                pass

        args = SimpleNamespace(
            girdi=KOK / "tests" / "t62_sahte_girdi",
            pt=self.args.pt,
            onnx=self.args.onnx,
            engine=None,
            imgsz=[JETSON_FPS.INFER_SIZE],
            isinma=0,
            tekrar=1,
            conf=self.args.conf,
            cihaz=None,
            video_adim=1,
            cikti=KOK / "tests" / "t62_sahte_cikti",
        )
        vaka = lambda ad, *_args, **_kwargs: {  # noqa: E731
            "tur": ad, "imgsz": JETSON_FPS.INFER_SIZE, "durum": "OK"
        }
        yazilan: dict[str, str] = {}
        stdout = io.StringIO()
        with (
            mock.patch.object(JETSON_FPS, "argumanlar", return_value=args),
            mock.patch.object(JETSON_FPS, "KareAkisi", return_value=SahteAkis()),
            mock.patch.object(JETSON_FPS, "vaka_calistir", side_effect=vaka),
            mock.patch.object(JETSON_FPS, "ortam_bilgisi", return_value={}),
            mock.patch.object(JETSON_FPS, "markdown_raporu", return_value="rapor\n"),
            mock.patch.object(type(args.cikti), "mkdir", return_value=None),
            mock.patch.object(
                JETSON_FPS,
                "atomik_yaz",
                side_effect=lambda yol, metin: yazilan.__setitem__(yol.name, metin),
            ),
            redirect_stdout(stdout),
        ):
            kod = JETSON_FPS.main()

        self.assertEqual(0, kod)
        self.assertIn("ATLANDI: tensorrt_fp16", stdout.getvalue())
        ozet = json.loads(yazilan["ozet.json"])
        self.assertEqual("tensorrt_fp16", ozet["atlanan_vakalar"][0]["tur"])
        self.assertEqual(["pt", "onnx"], [v["tur"] for v in ozet["vakalar"]])
        rapor = JETSON_FPS.markdown_raporu(
            [], {}, [{"tur": "tensorrt_fp16", "sebep": "engine yok"}]
        )
        self.assertIn("ATLANDI: engine yok", rapor)

    def test_conf_varsayilani_URETIM_yorumlayicisiyla_AYNI(self):
        uretim_conf = JETSON_FPS._arguman_ayristirici().get_default("conf")
        self.assertEqual(uretim_conf, self.args.conf)

    def test_imgsz_manifest_ve_URETIM_boyutlarindan_turetiliyor(self):
        beklenen = list(dict.fromkeys([*self.mf["imgsz"], JETSON_FPS.INFER_SIZE]))
        self.assertEqual(beklenen, self.args.imgsz)
        self.assertIn(JETSON_FPS.INFER_SIZE, self.args.imgsz)


class KilavuzHizasiTests(unittest.TestCase):
    """Sahadaki insan hangi dosyayi derleyecek — kilavuz ne diyor?"""

    def setUp(self):
        self.surum = _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)

    def test_IKI_kilavuz_da_ASIL_satiri_TASIYOR(self):
        for k in KILAVUZLAR:
            with self.subTest(kilavuz=k.name, yol=str(k.parent.name)):
                self.assertTrue(k.is_file())
                self.assertTrue(_asil_satirlari(k.read_text(encoding="utf-8")),
                                "kilavuzda `ASIL` isaretli model satiri yok")

    def test_ASIL_satiri_URETIM_surumunu_gosteriyor(self):
        for k in KILAVUZLAR:
            for satir in _asil_satirlari(k.read_text(encoding="utf-8")):
                with self.subTest(kilavuz=k.parent.name, satir=satir.strip()):
                    self.assertEqual(
                        self.surum, _surum(satir),
                        "kilavuz baska surumu ASIL gosteriyor; sahadaki kisi "
                        "hakem ekraninda gorulmeyen modeli derler")

    def test_derleme_komutu_URETIM_surumunu_kullaniyor(self):
        """`yolo export ... format=engine` satiri asil surumu gostermeli."""
        for k in KILAVUZLAR:
            satirlar = [s for s in k.read_text(encoding="utf-8").splitlines()
                        if "format=engine" in s and "navitas_seg_" in s]
            with self.subTest(kilavuz=k.parent.name):
                self.assertTrue(satirlar, "engine derleme komutu bulunamadi")
                self.assertIn(
                    self.surum, [_surum(s) for s in satirlar],
                    f"hicbir derleme komutu {self.surum} kullanmiyor")

    def test_FPS_komutu_URETIM_conf_esigini_kullaniyor(self):
        uretim_conf = JETSON_FPS._arguman_ayristirici().get_default("conf")
        for k in KILAVUZLAR:
            satirlar = [s for s in k.read_text(encoding="utf-8").splitlines()
                        if "--isinma 15 --tekrar 120 --conf" in s]
            with self.subTest(kilavuz=k.parent.name):
                self.assertTrue(satirlar, "ASIL FPS komutunda conf satiri yok")
                self.assertTrue(
                    any(f"--conf {uretim_conf:.2f}" in s for s in satirlar),
                    f"ASIL FPS komutu uretim conf={uretim_conf:.2f} kullanmiyor",
                )


# ---------------------------------------------------------------------------
# T154 · KOMUT SATIRI HIZASI — D-294 §4'te olculen KOR NOKTA
# ---------------------------------------------------------------------------
# Yukaridaki `KilavuzHizasiTests` yalniz IKI satir tipine bakiyordu: icinde
# `ASIL` gecen satirlar ve `format=engine` gecen satirlar. Sahadaki insanin
# GERCEKTEN yapistiracagi komutlarin geri kalani -- `trtexec --saveEngine=`,
# `jetson_fps.py --engine`, `--cikti results/..._vNN_...` -- HICBIR kapi
# tarafindan denetlenmiyordu. Sonuc olculdu (REVIEW_LOG D-294 SS4): bu satirlar
# 11 GUN boyunca `v30` dedi; v30 en son 2026-08-15'te uretimdi, yani IKI surum
# bayat kaldi ve kapilarin hepsi yesil yandi.
#
# Bu bolum kurali TERSINE cevirir: kilavuzda model agirligi/turevi adi ya da
# surumlu bir cikti yolu gecen HER satir uretim surumunu tasimak ZORUNDADIR.
# Eski surum adi ancak ASAGIDA ACIKCA ve GEREKCESIYLE tanimli bir istisnaya
# duserse mesrudur; liste disi her eski ad kapiyi dusurur (fail-closed).

MODEL_DOSYA_DESENI = re.compile(
    r"navitas_seg_(v\d+)[A-Za-z0-9_]*\.(?:pt|onnx|engine)")
CIKTI_SURUM_DESENI = re.compile(r"_(v\d+)(?=[_/\s]|$)")
AGAC_SATIRI_DESENI = re.compile(
    r"^[\s│├└─]*[├└]──\s")

# Agac listesinde eski surumu MESRU kilan etiketler (kucuk harfe indirgenmis
# olarak aranir). Etiketsiz eski surum = sessiz bayatlik = kapi duser.
MESRU_AGAC_ETIKETLERI = ("asil", "yedek", "eski as", "referans", "kıyas",
                         "ölçülmedi")

# 🔴 ISTISNA LISTESI — her kaydin GEREKCESI yazilidir (T154 sarti).
# `baslik_icerir`: satirin bagli oldugu en yakin markdown basliginda BULUNMASI
#   gereken alt dizgilerin TAMAMI. Baslik degisirse istisna DUSER (fail-closed).
# `surumler`: bu bolumde mesru sayilan eski surumler. None ise izinli kume
#   defterden turetilir (`surum_kaynagi`), yani elle tutulmaz.
ISTISNA_KURALLARI = (
    {
        "ad": "SS0-T76 (ASILDI)",
        "baslik_icerir": ("0-T76", "AŞILDI"),
        "surumler": ("v27",),
        "gerekce": (
            "Baslikta ACIKCA `(SS0-T85 ile ASILDI)` yazar: bu bolum 2026-08-14 "
            "terfisinin OLCUM KAYDIDIR, kosulacak komut degil. SS0-T85 ayni "
            "kilavuzda 'bugun derlenecek ve kosulacak model' satirini uretim "
            "surumuyle tasir; kayitlar bilerek SILINMEZ (SS0-T85 metni)."),
    },
    {
        "ad": "SS0-T58 (ASILDI)",
        "baslik_icerir": ("0-T58", "AŞILDI"),
        "surumler": ("v24",),
        "gerekce": (
            "Baslikta ACIKCA `(SS0-T76 ile ASILDI)` yazar; 2026-08-13 "
            "terfisinin olcum kaydidir. Gerekce SS0-T76 ile birebir aynidir."),
    },
    {
        "ad": "Domain kontrolu (B1 tekrari)",
        "baslik_icerir": ("Domain kontrolü",),
        "surumler": ("v17",),
        "gerekce": (
            "Bu blogun AMACI B1 bulgusunu (v17 gercek drone karelerinde KOR, "
            "SS0/B1) Jetson'da tekrarlamaktir. Uretim modeliyle kosulursa "
            "olculmek istenen sey OLCULEMEZ. Blogun hemen altindaki beklenti "
            "tablosu v17/v20/v21/v24'u ADIYLA anar; komut ile tablo ayni "
            "surumu gostermek zorundadir."),
    },
    {
        "ad": "SS6C birincil->yedek gecis yordami",
        "baslik_icerir": ("6C.", "YEDEK"),
        "surumler": None,
        "surum_kaynagi": ("config/model_registry.json :: "
                          "profiles.competition._yedek_surumler"),
        "gerekce": (
            "'Yedek' baglami surum adini mesru kilan TEK yerdir (T154 sarti): "
            "SS6C saha gunu birincil modelden yedege gecis yordamidir ve "
            "yedegin adini YAZMAK ZORUNDADIR. Istisna yine de bos degildir -- "
            "izinli kume DEFTERDEN gelir (`_yedek_surumler`), yani kilavuzda "
            "defterde YEDEK OLARAK KAYITLI OLMAYAN bir surum yazilamaz "
            "(D-294 SS3 ile ayni kanca)."),
    },
    {
        "ad": "Paket agac listesi (etiketli)",
        "agac": True,
        "gerekce": (
            "SS2'deki `jetson_paket/` agaci KOMUT DEGILDIR, paketin icindekini "
            "listeler; eski agirliklar pakette BILEREK durur (yedek + karar "
            "kiyasi). Istisna bos degildir: eski surumlu her agac satiri "
            "`<- YEDEK / eski asil / referans / kiyas` gibi bir etiket tasimak "
            "ZORUNDADIR ve `<- ASIL` satiri uretim surumune baglidir "
            "(`test_ASIL_satiri_URETIM_surumunu_gosteriyor`)."),
    },
)


def _defterdeki_yedek_surumler():
    """`competition._yedek_surumler` anahtarlari (ornegin ('v34', 'v35'))."""
    defter = json.loads((KOK / "config" / "model_registry.json")
                        .read_text(encoding="utf-8"))
    yedekler = defter["profiles"]["competition"].get("_yedek_surumler", {})
    return tuple(sorted(k for k in yedekler if not k.startswith("_")))


def _bolumlu_satirlar(metin: str):
    """(satir_no, satir, BASLIK YOLU) uretir.

    Baslik yolu, satirin uzerindeki TUM seviyelerin baslikaridir (`## 6C. ...`
    + `### G4 · ...`), cunku istisnalar ust bolume baglidir: SS6C'nin v35
    satirlari `### G4` alt basliginin altindadir ve yalniz EN YAKIN basliga
    bakan bir eslesme onlari kaciririr.

    Kod cercevesi (``` ) icindeki `# ...` satirlari BASLIK SAYILMAZ; kilavuzda
    `# 1a — JetPack ve L4T surumu` gibi kabuk yorumlari var ve bunlar bolum
    sinirini kaydirirsa istisnalar yanlis satirlara uyar.
    """
    basliklar: dict[int, str] = {}
    cerceve = False
    for no, satir in enumerate(metin.splitlines(), 1):
        kirpik = satir.strip()
        if kirpik.startswith("```"):
            cerceve = not cerceve
            continue
        if not cerceve and kirpik.startswith("#"):
            seviye = len(kirpik) - len(kirpik.lstrip("#"))
            basliklar = {s: b for s, b in basliklar.items() if s < seviye}
            basliklar[seviye] = kirpik
        yield no, satir, " ⟩ ".join(basliklar[s] for s in sorted(basliklar))


def _cikti_surumleri(satir: str):
    """`--cikti <yol>` icindeki `_vNN` damgalari."""
    if "--cikti" not in satir:
        return []
    kuyruk = satir.split("--cikti", 1)[1]
    return CIKTI_SURUM_DESENI.findall(kuyruk)


def _denetlenen_surumler(satir: str):
    """Bu satirda URETIM SURUMU TASIMASI GEREKEN her surum adi."""
    return MODEL_DOSYA_DESENI.findall(satir) + _cikti_surumleri(satir)


def _istisna_bul(baslik: str, satir: str, surum: str):
    """Eski surum tasiyan satir icin GECERLI istisna kaydi (yoksa None)."""
    for kural in ISTISNA_KURALLARI:
        if kural.get("agac"):
            if AGAC_SATIRI_DESENI.match(satir) and "←" in satir:
                return kural
            continue
        if not all(p in baslik for p in kural["baslik_icerir"]):
            continue
        izinli = kural["surumler"]
        if izinli is None:
            izinli = _defterdeki_yedek_surumler()
        if surum in izinli:
            return kural
    return None


def _sapmalar(yol: Path, uretim: str):
    """(satir_no, satir, surum, istisna) listesi — istisna None ise KUSUR."""
    cikti = []
    for no, satir, baslik in _bolumlu_satirlar(yol.read_text(encoding="utf-8")):
        for surum in _denetlenen_surumler(satir):
            if surum == uretim:
                continue
            cikti.append((no, satir, surum, _istisna_bul(baslik, satir, surum)))
    return cikti


class KilavuzKomutSatirlariTests(unittest.TestCase):
    """T154 · Kilavuzdaki HER model/cikti satiri uretim surumunu tasiyor mu?"""

    def setUp(self):
        self.uretim = _surum(yks_gui.YksArayuz.ALGI_MODEL_DOSYA)

    def test_model_dosyasi_gecen_satirlar_URETIM_surumunu_TASIYOR(self):
        for k in KILAVUZLAR:
            kusurlu = [(no, s.strip(), v) for no, s, v, ist in
                       _sapmalar(k, self.uretim) if ist is None]
            with self.subTest(kilavuz=k.parent.name):
                self.assertEqual(
                    [], kusurlu,
                    f"kilavuzda uretim disi surum adi geciyor ve HICBIR "
                    f"istisnaya dusmuyor (uretim={self.uretim}); sahadaki kisi "
                    f"hakem ekraninda gorulmeyen modeli derler/kosar — "
                    f"D-294 SS4 kor noktasi")

    def test_KOR_NOKTA_satir_tipleri_GERCEKTEN_denetleniyor(self):
        """Kapi bos olmasin: uc satir tipi de en az bir kez denetime girmeli."""
        for k in KILAVUZLAR:
            metin = k.read_text(encoding="utf-8")
            for isaret in ("--saveEngine=", "--engine ", "--cikti "):
                satirlar = [s for s in metin.splitlines()
                            if isaret in s and _denetlenen_surumler(s)]
                with self.subTest(kilavuz=k.parent.name, isaret=isaret.strip()):
                    self.assertTrue(
                        satirlar,
                        f"`{isaret.strip()}` satiri ya yok ya da icinde surum "
                        f"damgasi kalmadi — kapi bu satir tipinde KOR olur "
                        f"(D-294 SS4'te 11 gun boyunca olan tam buydu)")

    def test_kor_noktanin_UC_satir_tipi_URETIM_surumunde(self):
        """`--saveEngine=`, `--engine`, `--cikti` — adiyla ve ayri ayri."""
        for k in KILAVUZLAR:
            metin = k.read_text(encoding="utf-8")
            for isaret in ("--saveEngine=", "--engine ", "--cikti "):
                for no, satir, baslik in _bolumlu_satirlar(metin):
                    if isaret not in satir:
                        continue
                    for surum in _denetlenen_surumler(satir):
                        if surum == self.uretim:
                            continue
                        with self.subTest(kilavuz=k.parent.name,
                                          isaret=isaret.strip(), satir=no):
                            self.assertIsNotNone(
                                _istisna_bul(baslik, satir, surum),
                                f"{k.parent.name}:{no} `{isaret.strip()}` "
                                f"satiri {surum} diyor, uretim {self.uretim}")

    def test_YEDEK_istisnasi_DEFTERDEKI_yedegi_gosteriyor(self):
        """SS6C'de yazilan surum defterde YEDEK olarak kayitli olmali."""
        defter_yedekleri = _defterdeki_yedek_surumler()
        self.assertTrue(defter_yedekleri,
                        "defterde `_yedek_surumler` yok; SS6C geri donus "
                        "yordami dayanaksiz kalir (D-294 SS3)")
        gorulen = set()
        for k in KILAVUZLAR:
            for no, _satir, surum, ist in _sapmalar(k, self.uretim):
                if ist is not None and ist["ad"].startswith("SS6C"):
                    gorulen.add(surum)
                    with self.subTest(kilavuz=k.parent.name, satir=no):
                        self.assertIn(
                            surum, defter_yedekleri,
                            f"SS6C {surum} diyor ama defterde yedek degil")
        self.assertTrue(gorulen, "SS6C istisnasi hicbir satira uymadi — "
                                 "yordam degistiyse istisna KALDIRILMALI")

    def test_agac_kaydindaki_ESKI_surum_ETIKETSIZ_kalamaz(self):
        for k in KILAVUZLAR:
            for no, satir, surum, ist in _sapmalar(k, self.uretim):
                if ist is None or not ist.get("agac"):
                    continue
                kucuk = satir.lower()
                with self.subTest(kilavuz=k.parent.name, satir=no):
                    self.assertTrue(
                        any(e in kucuk for e in MESRU_AGAC_ETIKETLERI),
                        f"agac satiri {surum} listeliyor ama neden orada "
                        f"oldugunu SOYLEMIYOR: {satir.strip()}")
                    self.assertNotIn(
                        "← ASIL", satir,
                        f"agacta `← ASIL` isaretli satir {surum} gosteriyor; "
                        f"uretim {self.uretim}")

    def test_ISTISNA_kurallarinin_HEPSI_CANLI(self):
        """Olu istisna birikmesin — her kural en az bir satira uymali."""
        kullanilan = set()
        for k in KILAVUZLAR:
            for _no, _s, _v, ist in _sapmalar(k, self.uretim):
                if ist is not None:
                    kullanilan.add(ist["ad"])
        olu = [kural["ad"] for kural in ISTISNA_KURALLARI
               if kural["ad"] not in kullanilan]
        self.assertEqual(
            [], olu,
            "bu istisnalar artik hicbir satira uymuyor; kilavuz degistiyse "
            "istisna da KALDIRILMALI (liste sessizce buyurse kapi korlesir)")

    def test_her_ISTISNAYA_gerekce_yazili(self):
        for kural in ISTISNA_KURALLARI:
            with self.subTest(istisna=kural["ad"]):
                self.assertGreaterEqual(
                    len(kural.get("gerekce", "").strip()), 80,
                    "T154 sarti: istisna ACIKCA VE GEREKCESIYLE tanimlanir")


if __name__ == "__main__":
    unittest.main(verbosity=2)
