"""T202 — JETSON KURULUM BLOGU, KILAVUZUN SONRAKI KOMUTLARINI BESLIYOR MU?

Kanit: REVIEW_LOG D-352.

🔴 NEDEN VAR. 30 Agustos'ta Jetson Nano NX'e kopyalanacak sey `jetson_paket/`
dizinidir. Kilavuz once bir KURULUM BLOGU ile paketi `~/navitas/{codes,comms,
scripts,models,config,data}` duzenine ACAR, sonraki adimlar da o duzendeki
yollari (`codes/...`, `scripts/...`) cagirir.

⚠ ILK YAZDIGIM KAPI YANLIS VARSAYIMLA KURULMUSTU: kilavuzun `codes/...`
demesini "paket yolu kirik" sandim. Degil — kurulum blogundan SONRAKI duzeni
tarif ediyor. Dogru degismez su:

    KURULUM BLOGU'nun kopyaladiklari, SONRAKI komutlarin kullandiklarini
    KAPSAMALIDIR. Kapsamiyorsa saha gunu o komut `No such file` ile coker.

30 Eylul testi TEK SEFERLIK oldugu icin "sahada fark ederiz" YOKTUR.
"""
import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
PAKET = KOK / "jetson_paket"
KILAVUZ = PAKET / "JETSON_KILAVUZ.md"

# Cihazda URETILEN / disaridan gelen — kurulum blogunun tasimasi BEKLENMEZ.
# ⚠ DAR tutulur: her ekleme kapinin bir parcasini kapatir.
MUAF = (
    ".engine",                          # TensorRT motoru Jetson'da derlenir (T109)
    "scripts/jetson_paket_hazirla.py",  # paketi URETEN betik, PC tarafi
    # Asagidaki IKISI JETSON'DA KOSMAZ — baska makinede kosar. Kilavuz bunu
    # artik ACIKCA yaziyor; pakete alinmalari YANLIS olurdu.
    "comms/yks_gui.py",                 # hakem ekrani: YER KONTROL ISTASYONU
    "simulation/scripts/ika_nav.py",    # IKA benzetimi: IKA bilgisayari
    # T204/D-355: kalibrasyon kumesini PC'DE yeniden ureten betik. Jetson'a
    # gitmez; kilavuzda yalniz "yeniden uretme" atifi olarak geciyor.
    "scripts/olcum/161_q8_kalibrasyon_kumesi.py",
)

# Kurulum blogunun ~/navitas altina KOPYALADIGI hedefleri cikar.
# ⚠ Satir sonunda ACIKLAMA YORUMU olabilir (`... ~/navitas/codes/   # neden`).
# Ilk yazimda `\s*$` ile bitiyordu ve yorumlu satirlari ISKALIYORDU — kapi
# "eksik" diyordu ama dosya aslinda kuruluyordu. Yorum istege bagli yapildi.
# ⚠ Hedef KOK olabilir (`... ~/navitas/`), o zaman yakalama grubu BOSTUR.
# Ilk yazimda `[A-Za-z0-9_/]+` bos hedefi eslemiyordu ve `cp -r kalibrasyon
# ~/navitas/` satiri GORUNMUYORDU — kapi "kurulmuyor" diyordu.
KURULUM = re.compile(
    r"^cp\s+(?:-r\s+)?(.+?)\s+~/navitas/([A-Za-z0-9_/]*)/?\s*(?:#.*)?$",
    re.MULTILINE)
# Sonraki komutlarin KULLANDIGI ~/navitas-goreli yollar.
KULLANIM = re.compile(
    r"(?:~/navitas/)?((?:codes|comms|scripts|models|config|data|simulation"
    r"|kalibrasyon)"
    r"/[A-Za-z0-9_./-]+\.(?:py|json|pt|engine|onnx|yaml))")


def _metin() -> str:
    return KILAVUZ.read_text(encoding="utf-8")


def _kurulan() -> set[str]:
    """Kurulum blogunun ~/navitas altinda OLUSTURDUGU dosya yollari."""
    kurulan = set()
    for kaynaklar, hedef_ham in KURULUM.findall(_metin()):
        hedef_dizin = hedef_ham.strip("/")   # `~/navitas/codes/` -> `codes`
        for k in kaynaklar.split():
            ad = k.split("/")[-1]
            # `cp -r <dizin>` — PAKETTEKI dizinin ICINDEKI dosyalari da say.
            # Yoksa kilavuzun `kalibrasyon/kalibrasyon.yaml` gibi bir DOSYAYI
            # kullanmasi "kurulmuyor" gorunur.
            kaynak_dizin = PAKET / k
            if kaynak_dizin.is_dir():
                onek = f"{hedef_dizin}/{ad}" if hedef_dizin else ad
                kurulan.add(onek)
                for f in kaynak_dizin.rglob("*"):
                    if f.is_file():
                        goreli = f.relative_to(kaynak_dizin).as_posix()
                        kurulan.add(f"{onek}/{goreli}")
                continue
            if ad == "*":                            # `cp models/*`
                kaynak_dizin = PAKET / k.rsplit("/", 1)[0]
                if kaynak_dizin.is_dir():
                    for p in kaynak_dizin.iterdir():
                        if p.is_file():
                            kurulan.add(f"{hedef_dizin}/{p.name}")
                continue
            kurulan.add(f"{hedef_dizin}/{ad}" if hedef_dizin else ad)
    return kurulan


def _kullanilan() -> set[str]:
    return {y for y in KULLANIM.findall(_metin()) if not y.endswith(MUAF)
            and y not in MUAF}


class KurulumBlogu(unittest.TestCase):
    def test_capa_KURULUM_BLOGU_AYRISTIRILIYOR(self):
        """Capa: blok okunamazsa asagidaki test BOSA doner."""
        self.assertTrue(KILAVUZ.is_file(), f"kilavuz yok: {KILAVUZ}")
        k = _kurulan()
        self.assertGreater(len(k), 8,
                           f"kurulum blogundan yalniz {len(k)} dosya cikti — "
                           "desen bozulmus olabilir")
        self.assertIn("codes/rpi_inference.py", k)

    def test_capa_KULLANIM_AYRISTIRILIYOR(self):
        self.assertGreater(len(_kullanilan()), 5,
                           "kilavuzda hic ~/navitas yolu kullanilmiyor gorunuyor")

    def test_KULLANILAN_HER_YOL_KURULUYOR(self):
        eksik = sorted(_kullanilan() - _kurulan())
        self.assertEqual(
            [], eksik,
            "Kilavuz, KURULUM BLOGUNUN TASIMADIGI dosyalari kullaniyor — saha "
            "gunu bu komutlar `No such file` ile coker (D-352). Eksik:\n  "
            + "\n  ".join(eksik)
            + "\n\nCare: ya kurulum blogunа eklensin, ya komut degistirilsin. "
              "Dosya pakette de yoksa ONCE pakete alinmali "
              "(scripts/jetson_paket_hazirla.py KOPYALAR).")

    def test_MUTASYON_kurulmayan_yol_YAKALANIR(self):
        """Kapi bos degil: kurulum blogundan bir satir dusse YAKALANMALI."""
        metin = _metin()
        mutant = metin.replace(
            "cp kod/jetson_fps.py ~/navitas/scripts/", "", 1)
        self.assertNotEqual(metin, mutant, "mutasyon uygulanamadi")
        kurulan = set()
        for kaynaklar, hedef_ham in KURULUM.findall(mutant):
            hedef = hedef_ham.strip("/")
            for k in kaynaklar.split():
                if k.endswith("*") or k.startswith("test_goruntuleri"):
                    continue
                kurulan.add(f"{hedef}/{k.split('/')[-1]}")
        self.assertNotIn("scripts/jetson_fps.py", kurulan,
                         "satir silindigi hâlde kapi hâlâ 'kuruluyor' diyor")

    def test_MUAF_LISTESI_DAR(self):
        self.assertLessEqual(len(MUAF), 5,
                             "MUAF buyudu — her ekleme kapinin bir parcasini "
                             "kapatir; gerekcesi D-352'ye yazilmali")

    def test_GIRDI_YOLLARI_KURULUM_DUZENIYLE_UYUMLU(self):
        """`--girdi` yollari, kurulum blogunun OLUSTURDUGU duzende bulunmali.

        🔴 D-353: kurulum blogu `cp -r test_goruntuleri ~/navitas/data/` yapar,
        yani kareler `data/test_goruntuleri/...` altina duser. Ama SS5 "ASIL
        TEST" komutu `cd ~/navitas` sonrasi `--girdi test_goruntuleri/...`
        diyordu — `data/` oneki EKSIKTI ve 30 Agustos'un AMIRAL komutu
        `No such file` ile cokerdi.
        """
        kurulan_dizinler = {y.rsplit("/", 1)[0] for y in _kurulan()}
        kotu = []
        for satir in _metin().splitlines():
            s2 = satir.strip()
            if not s2.startswith("--girdi"):
                continue
            yol = s2.split()[1].rstrip("\\").strip()
            if yol.startswith("~") or yol.startswith("/"):
                continue                      # mutlak yol: kurulum duzeni disi
            kok = yol.split("/")[0]
            if kok not in {d.split("/")[0] for d in kurulan_dizinler}:
                kotu.append(yol)
        self.assertEqual(
            [], kotu,
            "`--girdi` yolu kurulum duzeninde YOK — saha gunu komut coker "
            "(D-353). Kurulum su dizinleri olusturuyor: "
            f"{sorted({d.split('/')[0] for d in kurulan_dizinler})}. Kotu: {kotu}")

    def test_PAKET_KODU_KENDI_BASINA_ITHAL_EDILEBILIYOR(self):
        import subprocess
        import sys
        kod = PAKET / "kod"
        for m in ("rpi_inference", "karar_sozlesmesi", "jetson_fps",
                  "kamera_dogrula", "costmap_path_finder"):
            r = subprocess.run(
                [sys.executable, "-c",
                 f"import sys; sys.path.insert(0, r'{kod}'); import {m}"],
                capture_output=True, text=True, cwd=str(kod))
            self.assertEqual(r.returncode, 0,
                             f"paket modulu ithal EDILEMIYOR: {m}\n{r.stderr[-400:]}")


if __name__ == "__main__":
    unittest.main()
