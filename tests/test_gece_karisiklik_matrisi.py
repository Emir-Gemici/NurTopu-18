"""NOBETCI — sinif bazli karisiklik matrisi artefakti (ON_KAYIT gece 7 Eylul 2026 · G3).

Y-3.3.4-M02 / Y-4-M08 "dogruluk matrisleri" FDR'de OLCULEMEDI idi. Artefakt
`results/gece_20260907/karisiklik/piksel_karisiklik_test29.json` bu bosluğu
`scripts/olcum/176_piksel_karisiklik_matrisi.py` ile kapatir. Bu test artefaktin
IC TUTARLILIGINI kilitler — sayilara esik KOYMAZ (esik koymak terfi kararidir,
D-133; bu bir olcumdur):

  1. JSON var ve 29 kareyi tasir (DOGRULAMA kumesi test29, CONTRACTS §12);
  2. 3x3 matrisin satir/sutun toplamlari = toplam piksel; kare matrislerinin
     toplami = toplam matris; her kare matrisi = o karenin h*w'si;
  3. IoU'lar 0..1 araliginda (iki payda: etiketli / tum);
  4. model sha256 = kayit defterindeki uretim modeli (v36) — bayat sayi tasinmaz;
  5. CONF 65_kabul_denetcisi.CONF ile, imgsz kayit defteriyle ayni; device cpu;
  6. ornek duzeyi (ultralytics val) matrisinin SINIF sutun toplamlari = etiket
     dosyalarindaki poligon sayilari (ultralytics her etiket satirini bir yer
     gercegi ornegi sayar; FDR §3.3.4.2 ayni kilidi egitim matrisi icin kullanir);
  7. `dataset/test29_v3.yaml` sinif adlari CONTRACTS §1.1 / sinif_semasi ile
     birebir, train ve val ikisi de test dizinini gosterir (0038 egitime girmez).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
JSON_YOLU = KOK / "results" / "gece_20260907" / "karisiklik" / "piksel_karisiklik_test29.json"
YAML_YOLU = KOK / "dataset" / "test29_v3.yaml"
ETIKET_DIZIN = KOK / "dataset" / "dji_kirsal_0038_bolum_v3" / "labels" / "test"
BEKLENEN_KARE = 29

for _y in (KOK / "codes",):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

from model_registry import load_registry  # noqa: E402
from sinif_semasi import ENGEL, IKI_SINIF_ADLARI, ZEMIN  # noqa: E402


def _kabul_denetcisi_conf() -> float:
    yol = KOK / "scripts" / "olcum" / "65_kabul_denetcisi.py"
    if str(yol.parent) not in sys.path:
        sys.path.insert(0, str(yol.parent))
    spec = importlib.util.spec_from_file_location("kabul_denetcisi_65_nobetci", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return float(m.CONF)


def _poligon_sayilari() -> dict[int, int]:
    sayi = {ZEMIN: 0, ENGEL: 0}
    for txt in sorted(ETIKET_DIZIN.glob("*.txt")):
        for satir in txt.read_text(encoding="utf-8").splitlines():
            v = satir.split()
            if len(v) < 7:
                continue
            c = int(v[0])
            if c in sayi:
                sayi[c] += 1
    return sayi


class KarisiklikMatrisiNobetci(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(JSON_YOLU.is_file(), f"artefakt YOK: {JSON_YOLU} — 176 kosulmadi")
        cls.veri = json.loads(JSON_YOLU.read_text(encoding="utf-8"))

    # ── 1. kume boyutu ───────────────────────────────────────────────────────
    def test_kare_sayisi_29(self):
        v = self.veri
        self.assertEqual(v["kume"]["n_kare"], BEKLENEN_KARE)
        self.assertEqual(v["toplam"]["n_kare"], BEKLENEN_KARE)
        self.assertEqual(len(v["kareler"]), BEKLENEN_KARE)
        self.assertEqual(len({k["kare"] for k in v["kareler"]}), BEKLENEN_KARE, "kare adlari tekrar ediyor")

    # ── 2. toplamlar ─────────────────────────────────────────────────────────
    def _matris_tutarli(self, m: dict, beklenen_px: int, ad: str):
        M = m["matris"]
        self.assertEqual(len(M), 3, ad)
        self.assertTrue(all(len(s) == 3 for s in M), ad)
        self.assertTrue(all(isinstance(x, int) and x >= 0 for s in M for x in s), f"{ad}: negatif/tam olmayan hucre")
        self.assertEqual(sum(sum(s) for s in M), beklenen_px, f"{ad}: matris toplami != piksel")
        self.assertEqual(m["toplam_px"], beklenen_px, ad)
        self.assertEqual(m["satir_toplam"], [sum(s) for s in M], f"{ad}: satir toplamlari")
        self.assertEqual(m["sutun_toplam"], [sum(M[r][c] for r in range(3)) for c in range(3)], f"{ad}: sutun toplamlari")
        self.assertEqual(sum(m["satir_toplam"]), beklenen_px, ad)
        self.assertEqual(sum(m["sutun_toplam"]), beklenen_px, ad)

    def test_toplam_matris_satir_sutun_toplamlari_piksel_sayisina_esit(self):
        t = self.veri["toplam"]
        toplam_px = sum(k["px"] for k in self.veri["kareler"])
        self.assertEqual(t["toplam_px"], toplam_px)
        self._matris_tutarli(t["uretim"], toplam_px, "toplam.uretim")
        self._matris_tutarli(t["yalniz_model"], toplam_px, "toplam.yalniz_model")

    def test_kare_matrisleri_toplami_toplam_matrise_esit(self):
        for anahtar in ("uretim", "yalniz_model"):
            birikim = [[0] * 3 for _ in range(3)]
            for k in self.veri["kareler"]:
                self.assertEqual(k["px"], k["h"] * k["w"], k["kare"])
                self._matris_tutarli(k[anahtar], k["px"], f"{k['kare']}.{anahtar}")
                for r in range(3):
                    for c in range(3):
                        birikim[r][c] += k[anahtar]["matris"][r][c]
            self.assertEqual(birikim, self.veri["toplam"][anahtar]["matris"], anahtar)

    def test_eksenler_sabit(self):
        m = self.veri["toplam"]["uretim"]
        self.assertEqual(m["satir_ekseni_tahmin"], ["zemin", "engel", "yok"])
        self.assertEqual(m["sutun_ekseni_gercek"], ["zemin", "engel", "etiketsiz"])

    # ── 3. IoU araligi ───────────────────────────────────────────────────────
    def test_iou_0_1_araliginda(self):
        for anahtar in ("uretim", "yalniz_model"):
            m = self.veri["toplam"][anahtar]
            for sinif in ("zemin", "engel"):
                for payda in ("iou_etiketli", "iou_tum"):
                    deger = m[sinif][payda]
                    self.assertIsNotNone(deger, f"{anahtar}.{sinif}.{payda} OLCULEMEDI cikti")
                    self.assertGreaterEqual(deger, 0.0, f"{anahtar}.{sinif}.{payda}")
                    self.assertLessEqual(deger, 1.0, f"{anahtar}.{sinif}.{payda}")
                # etiketli payda tum paydadan KUCUK OLAMAZ (FP alt kumesi)
                self.assertGreaterEqual(m[sinif]["iou_etiketli"], m[sinif]["iou_tum"], f"{anahtar}.{sinif}")
                # IoU tanimi hucrelerle tutarli mi (yeniden hesapla)
                M = m["matris"]
                c = 0 if sinif == "zemin" else 1
                tp = M[c][c]
                fn = sum(M[r][c] for r in range(3)) - tp
                fp_tum = sum(M[c]) - tp
                fp_etk = M[c][0] + M[c][1] - tp
                self.assertAlmostEqual(m[sinif]["iou_tum"], tp / (tp + fp_tum + fn), places=12)
                self.assertAlmostEqual(m[sinif]["iou_etiketli"], tp / (tp + fp_etk + fn), places=12)
            pd = m["piksel_dogrulugu_etiketli"]
            self.assertIsNotNone(pd)
            self.assertTrue(0.0 <= pd <= 1.0)

    # ── 4. model kimligi ─────────────────────────────────────────────────────
    def test_model_sha256_kayit_defteriyle_ayni(self):
        defter = load_registry()
        profil = defter["profiles"][defter["default_profile"]]
        m = self.veri["model"]
        self.assertEqual(m["sha256_defter"], profil["sha256"])
        self.assertEqual(m["sha256_disk"], profil["sha256"], "diskteki agirlik defterdekinden farkli")
        self.assertEqual(m["model_id"], profil["model_id"])
        self.assertEqual(Path(m["path"]).name, Path(profil["path"]).name)
        self.assertEqual(m["imgsz_defter"], int(profil["imgsz"]))

    # ── 5. calisma noktasi ───────────────────────────────────────────────────
    def test_conf_imgsz_device_uretimle_ayni(self):
        v = self.veri
        self.assertEqual(v["conf"], _kabul_denetcisi_conf())
        defter = load_registry()
        profil = defter["profiles"][defter["default_profile"]]
        self.assertEqual(v["imgsz"], int(profil["imgsz"]))
        self.assertEqual(v["device"], "cpu")
        self.assertFalse(v["makine"]["torch_cuda_kullanildi"])
        if v.get("ornek_duzeyi"):
            self.assertEqual(v["ornek_duzeyi"]["conf"], v["conf"])
            self.assertEqual(v["ornek_duzeyi"]["imgsz"], v["imgsz"])
            self.assertEqual(v["ornek_duzeyi"]["device"], "cpu")

    def test_t67_katmani_engeli_yalniz_buyutur(self):
        """Madde 15: uretim engel sutunu >= yalniz-model engel; zemin satiri AYNI."""
        for k in self.veri["kareler"]:
            self.assertGreaterEqual(k["t67_ek_engel_px"], 0, k["kare"])
            u, h = k["uretim"]["matris"], k["yalniz_model"]["matris"]
            self.assertGreaterEqual(u[1][0] + u[1][1] + u[1][2], h[1][0] + h[1][1] + h[1][2], k["kare"])
            # zemin satiri: uretimde zemin, yalniz-modelde zemin olup uretimde engele giden dahil
            self.assertEqual(sum(u[0]) + (sum(u[1]) - sum(h[1])), sum(h[0]) + (sum(h[2]) - sum(u[2])), k["kare"])

    # ── 6. ornek duzeyi ──────────────────────────────────────────────────────
    def test_ornek_duzeyi_sutun_toplamlari_poligon_sayilariyla_ayni(self):
        o = self.veri.get("ornek_duzeyi")
        self.assertIsNotNone(o, "ornek duzeyi matris YOK (--ornek-duzeyi-atla ile kosulmus)")
        M = o["matris"]
        self.assertEqual(len(M), 3)
        self.assertTrue(all(len(s) == 3 for s in M))
        self.assertEqual(o["satir_toplam"], [sum(s) for s in M])
        self.assertEqual(o["sutun_toplam"], [sum(M[r][c] for r in range(3)) for c in range(3)])
        self.assertEqual(o["sinif_adlari"][:2], [IKI_SINIF_ADLARI[ZEMIN], IKI_SINIF_ADLARI[ENGEL]])
        poli = _poligon_sayilari()
        self.assertEqual(o["sutun_toplam"][0], poli[ZEMIN], "zemin sutunu != etiket poligon sayisi")
        self.assertEqual(o["sutun_toplam"][1], poli[ENGEL], "engel sutunu != etiket poligon sayisi")
        self.assertEqual(M[2][2], 0, "arka plan x arka plan hucresi tanim geregi 0")
        self.assertEqual(o["silinen_gorsel_yiginlari"] is not None, True)

    # ── 7. yaml ──────────────────────────────────────────────────────────────
    def test_yaml_sinif_adlari_ve_dizinleri(self):
        import yaml
        d = yaml.safe_load(YAML_YOLU.read_text(encoding="utf-8"))
        self.assertEqual(d["nc"], 2)
        self.assertEqual({int(k): v for k, v in d["names"].items()}, dict(IKI_SINIF_ADLARI))
        self.assertEqual(d["train"], d["val"], "train ve val ikisi de test dizinini gostermeli (0038 egitime girmez)")
        self.assertTrue(str(d["val"]).replace("\\", "/").endswith("images/test"))
        kok = Path(d["path"])
        self.assertEqual(kok.name, "dji_kirsal_0038_bolum_v3")
        self.assertEqual(len(list(ETIKET_DIZIN.glob("*.txt"))), BEKLENEN_KARE)
        self.assertEqual(self.veri["ornek_duzeyi"]["yaml"], YAML_YOLU.relative_to(KOK).as_posix())


if __name__ == "__main__":
    unittest.main()
