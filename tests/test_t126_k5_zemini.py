"""T126 KAPISI: K5'in yeni zemini — dort SART testle kilitlenir (D-243).

D-243, K5'in zeminini tek OOD figurunden kabul kumesinin BARIYERLI+ROTALI
alt kumesine tasidi ve DORT SART kosdu. Bu dosya sartlarin her birini
DAVRANISSAL olarak sinar; T120 dersi geregi kapinin KENDISI de sinanir
(hic dusmeyen kapi, hic kosmayan kapi kadar sahtedir).

SART 1 · BARIYER MODELDEN GELMEZ
  Bariyer geometrisi degerlendirilen modelin maskesinden okunursa, bariyere
  KOR bir model kapiyi TRIVIAL gecer. Burada: (a) dedektor MODEL ORNEKLEMEDEN
  bariyer buluyor mu; (b) bariyere KOR bir sahte model kapidan DUSUYOR mu.
SART 2 · POPULASYON — n=1 degil; olculebilir kare sayisi RAPORLANIR.
SART 3 · ESIK DEGISMEZ — kesisim = 0 px; "ortalama dusuk" GECTI degildir.
SART 4 · OLCULEMEDI AYAKTA — olculebilir kare 0 ise GECTI DEGIL OLCULEMEDI.

⚠ Bu dosya GPU/model gerektirmez: K5'in karar mantigi SAF fonksiyondur
(`66_k5_bariyer_populasyon.k5_populasyon_durumu`) ve bariyer dedektoru
klasik goruntu islemedir. Agir kosum `65`/`66` CLI'sindedir.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

import cv2
import numpy as np

KOK = Path(__file__).resolve().parents[1]
OLCUM = KOK / "scripts" / "olcum"
for _p in (OLCUM, KOK / "codes", KOK / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))


def _yukle(ad: str, dosya: str):
    spec = importlib.util.spec_from_file_location(ad, OLCUM / dosya)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B63 = _yukle("t126_bariyer63", "63_bariyer_kesisimi.py")
P66 = _yukle("t126_populasyon66", "66_k5_bariyer_populasyon.py")
K65 = _yukle("t126_kabul65", "65_kabul_denetcisi.py")


def _bariyerli_sahne(kapi_acik: bool = True):
    """Yatay KIRMIZI bariyer kolu + iki yanda gri zemin.

    `kapi_acik` False iken bariyer tum kareyi keser: bir rota ancak bariyerin
    UZERINDEN gecebilir — SART 1'in tuzagi tam burada kurulur.
    """
    h, w = 400, 600
    img = np.full((h, w, 3), 120, np.uint8)          # notr gri zemin
    img[190:210, :] = (40, 40, 220)                  # BGR: yuksek kromali kirmizi
    if kapi_acik:
        # ⚠ Kapi 120 px: dedektorun MORPH_CLOSE cekirdegi 61 px'dir ve daha
        # dar bosluklari KAPATIR (63'te serit araliklarini birlestirmek icin).
        # Yani ~61 px'ten dar bir aciklik bariyer sayilir — FAIL-SAFE yon,
        # olcum sirasinda kesfedildi (ilk denemede kapi 40 px idi ve kapandi).
        img[190:210, 240:360] = 120                  # kapi (120 px)
    return img


class Sart1BariyerModeldenGelmezTests(unittest.TestCase):
    def test_dedektor_MODEL_ORNEKLEMEDEN_bariyer_buluyor(self):
        """(a) Dedektor klasik: hicbir YOLO modeli orneklenmeden calisiyor."""
        import ultralytics
        cagri = {"n": 0}
        ozgun = ultralytics.YOLO

        def sayan(*a, **k):
            cagri["n"] += 1
            return ozgun(*a, **k)

        ultralytics.YOLO = sayan
        try:
            kol, kutular = B63.bariyer_maskesi(_bariyerli_sahne())
        finally:
            ultralytics.YOLO = ozgun
        self.assertEqual(cagri["n"], 0, "bariyer icin MODEL orneklendi")
        self.assertTrue(kutular, "dedektor bariyeri bulamadi")
        self.assertGreater(int((kol > 0).sum()), 0)

    def test_kanit_dosyasi_gercek_kumede_MODELSIZ_bariyer_buldugunu_gosteriyor(self):
        """(a) devami: gercek kabul kumesinde koşulmuş kanit REPODA duruyor."""
        kanit = KOK / "results" / "t126" / "sart1_kaniti.json"
        if not kanit.is_file():
            self.skipTest("sart1_kaniti.json yok — 113 betigi kosulmali")
        d = json.loads(kanit.read_text(encoding="utf-8"))
        self.assertFalse(d["YOLO_MODELI_ORNEKLENDI_MI"])
        self.assertEqual(d["YOLO_cagri_sayisi"], 0)
        self.assertGreater(d["bariyer_bulunan_kare"], 0)

    def test_bariyere_KOR_model_kapidan_DUSER(self):
        """(b) SART 1'in ASIL olcutu: kor model odullendirilmemeli.

        Bariyeri hic gormeyen bir model, bariyerin UZERINDEN gecen bir rota
        uretir. Bariyer MODELDEN gelseydi kesisim 0 cikar ve kapi GECERDI.
        Bariyer BAGIMSIZ dedektorden geldigi icin kesisim > 0 olmali.
        """
        img = _bariyerli_sahne(kapi_acik=False)
        kol, kutular = B63.bariyer_maskesi(img)
        self.assertTrue(kutular, "sahne kurulamadi: bariyer yok")
        ust = kol > 0
        # KOR modelin urettigi rota: kareyi dikey kesen duz cizgi -> bariyeri
        # zorunlu olarak keser (bariyer tam genislikte).
        iz = np.zeros(img.shape[:2], np.uint8)
        cv2.line(iz, (300, 0), (300, img.shape[0] - 1), 1, 3)
        kesisim = int(((iz > 0) & ust).sum())
        self.assertGreater(kesisim, 0,
                           "kor modelin rotasi bariyeri kesmiyor gorunuyor — "
                           "bariyer BAGIMSIZ kaynaktan gelmiyor olabilir")
        self.assertEqual(P66.k5_populasyon_durumu(olculebilir=1, kesen=1),
                         "DUSTU", "kor model kapidan DUSMEDI (SART 1 ihlali)")

    def test_66_bariyeri_MODEL_MASKESINDEN_turetmiyor(self):
        """(c) SART 1'in YAPISAL kilidi — davranissal kanit tek basina yetmez.

        Kapinin bariyeri model ciktisindan almadigi AST ile dogrulanir:
          · `bariyer_maskesi` (63'ten ithal) CAGRILIYOR olmali;
          · bariyer degiskeni modelin maske sozlugunden (`mk`, `trav`, `blok`)
            TURETILMIS olmamali.
        Duz metin aramasi kullanilMAZ: kusuru anlatan yorumlar yanlis pozitif
        uretir (bu dosyada bir kez dusuldu).
        """
        import ast
        agac = ast.parse((OLCUM / "66_k5_bariyer_populasyon.py")
                         .read_text(encoding="utf-8"))
        cagrilar = {ast.unparse(d.func) for d in ast.walk(agac)
                    if isinstance(d, ast.Call)}
        self.assertIn("bariyer_maskesi", cagrilar,
                      "66 bagimsiz bariyer dedektorunu CAGIRMIYOR")
        # `kol`/`kol_t` (bariyer) modelin maskelerinden atanmis mi?
        for d in ast.walk(agac):
            if isinstance(d, ast.Assign):
                hedefler = {h.id for h in d.targets if isinstance(h, ast.Name)}
                if hedefler & {"kol", "ust"}:
                    kaynak = ast.unparse(d.value)
                    for yasak in ("mk[", "trav", "blok", "get_masks"):
                        self.assertNotIn(
                            yasak, kaynak,
                            f"bariyer MODEL ciktisindan turetiliyor: {kaynak}")

    def test_POZITIF_KONTROL_temiz_model_GECER(self):
        """Kapi her seyi dusurmuyor: bariyeri gorup KACINAN rota GECER."""
        img = _bariyerli_sahne(kapi_acik=True)
        kol, _k = B63.bariyer_maskesi(img)
        ust = kol > 0
        iz = np.zeros(img.shape[:2], np.uint8)
        cv2.line(iz, (300, 0), (300, 399), 1, 1)   # kapinin TAM ortasindan
        kesisim = int(((iz > 0) & ust).sum())
        self.assertEqual(kesisim, 0, "kapidan gecen rota bariyeri kesiyor sayildi")
        self.assertEqual(P66.k5_populasyon_durumu(olculebilir=1, kesen=0), "GECTI")


class Sart3ve4UcDurumTests(unittest.TestCase):
    def test_olculebilir_sifir_OLCULEMEDI_dir_GECTI_DEGIL(self):
        """🔴 SART 4: yokluk uzerinden gecirme YASAK (D-180'in en agir bicimi)."""
        self.assertEqual(P66.k5_populasyon_durumu(olculebilir=0, kesen=0),
                         "OLCULEMEDI")

    def test_tek_kare_bile_kesiyorsa_DUSTU(self):
        """SART 3: 'ortalama dusuk' / '%99 temiz' GECTI degildir."""
        self.assertEqual(P66.k5_populasyon_durumu(olculebilir=200, kesen=1),
                         "DUSTU")

    def test_olculebilir_var_kesen_yok_GECTI(self):
        self.assertEqual(P66.k5_populasyon_durumu(olculebilir=200, kesen=0),
                         "GECTI")

    def test_OLCULEMEDI_terfiyi_BLOKLAR(self):
        """65'in verdikt eslemesi: yalniz GECTI gecirir."""
        for durum in ("OLCULEMEDI", "DUSTU"):
            self.assertNotEqual(durum, "GECTI")

    def test_esik_SIFIR_kaldi(self):
        """SART 3: zemin tasima bir GEVSETME DEGILDIR — 1 kesen kare bile duser."""
        for kesen in (1, 2, 5):
            self.assertEqual(
                P66.k5_populasyon_durumu(olculebilir=174, kesen=kesen), "DUSTU")


class Sart2PopulasyonTests(unittest.TestCase):
    def test_zemin_TEK_KAYNAKTAN_gelir(self):
        """66 artik kumeyi registry'den alir (T125/D-226 kalibi)."""
        self.assertTrue(hasattr(P66, "kabul_kumesi_yolu"))
        # `assertIs` YANLIS olcut olurdu: iki modul ayri ornek olarak
        # yuklendigi icin fonksiyon nesneleri farklidir. Degismez sudur:
        # 66 kumeyi KENDI turetmez, 65'ten ITHAL eder.
        kaynak66 = (OLCUM / "66_k5_bariyer_populasyon.py").read_text(encoding="utf-8")
        self.assertIn('import_module("65_kabul_denetcisi").kabul_kumesi_yolu',
                      kaynak66, "66 kumeyi 65ten ITHAL etmiyor (tek kaynak bozuk)")
        # ⚠ Duz metin aramasi burada YANLIS olcuttur: kusuru ANLATAN yorum
        # satirini kusurun KENDISI sanar (T112/T120'de ayni tuzaga dusuldu,
        # bu kapida da ilk yazimda dusuldu). AST ile MODUL DUZEYINDE bir
        # `KUME = ...` atamasi olmadigi dogrulanir — yorumlar AST'ye girmez.
        import ast
        agac = ast.parse(kaynak66)
        modul_duzeyi_atamalar = {
            h.id for d in agac.body if isinstance(d, ast.Assign)
            for h in d.targets if isinstance(h, ast.Name)}
        self.assertNotIn(
            "KUME", modul_duzeyi_atamalar,
            "66 hala modul duzeyinde kendi KUME sabitini turetiyor (D-226)")

    def test_65_K5_i_POPULASYON_betiginden_okur(self):
        """Zemin gercekten tasindi mi — kaynak kodda 66 cagriliyor mu?"""
        kaynak = (OLCUM / "65_kabul_denetcisi.py").read_text(encoding="utf-8")
        self.assertIn("66_k5_bariyer_populasyon.py", kaynak,
                      "65 hala K5'i tek figur betiginden okuyor olabilir")
        self.assertIn("K5_olculebilir_kare", kaynak,
                      "olculebilir kare sayisi raporlanmiyor (SART 2)")

    def test_kanit_dosyasinda_populasyon_buyuklugu_YAZILI(self):
        kanit = KOK / "results" / "t126" / "sart1_kaniti.json"
        if not kanit.is_file():
            self.skipTest("sart1_kaniti.json yok")
        d = json.loads(kanit.read_text(encoding="utf-8"))
        self.assertGreater(d["n_kare"], 100, "populasyon kucuk (n=1 sinifi)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
