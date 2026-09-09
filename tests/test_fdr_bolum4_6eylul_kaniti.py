"""T218 (H5, D-438) — FDR Bölüm 4 6 EYLÜL KANIT NÖBETÇİSİ: rapora yazılan sayı artefakttan gelir.

NEDEN (ölçülen kusur örüntüsü): FDR'ye elle kopyalanan sayı, artefakt değişince
SESSİZCE bayatlar (D-256 SS3 · D-372 · D-376 · D-415). 10 Eylül'de §4.6'ya 6 Eylül
parametre dökümünün ofsetleri, §4.10.5'e tlog analizlerinin pitch/arm sayıları,
§4.12'ye RC failsafe hükmü yazıldı. Bu kapı her birini KAYNAK DOSYADAN yeniden okur:

  T1  §4.6 tablosundaki her `PARAM` değeri ve `:satır` atfı
      `config/pixhawk/arducopter_fda_20260906.param` ile BİREBİR aynı
  T2  §4.10.5 devrilme tablosundaki pencere pitch min/max değerleri
      `results/ucus_loglari/20260906/pitch_kolu_analizi.txt` ile aynı
  T3  §4.10.5 arm sayıları (41 pencere, 56 CH6 çevirme) ham çıktıyla aynı
  T4  §4.12 RC kaybı satırının 6 EYLÜL HÜCRESİ "ÖLÇÜLDÜ" + "DÜŞTÜ" + D-428
      taşıyor; Y-4-M12 "karşılanmadı" açıkça yazılı; ÖLÇÜLEMEDİ ≠ GEÇTİ (RC
      satırında "GEÇTİ" yok). T4c: öteki senaryoların 6 Eylül HÜCRESİ
      "tetiklenmedi" — satırın tamamı değil; 5 Eylül hücresi doyuramaz (M4)
  T5  bayat satırlar: `simulation/scripts/score.py` yalnız üstü çizili;
      README "ekip isimleri" üstü çizili; YONERGE Y-4-M06 artık "YOK" değil
  T6  §4.3.3 takvimi ölçülen olayları ve D-kayıtlarını taşıyor; hover BEYAN
  T7  eski metin SİLİNMEMİŞ: §4.6 ve §4.12'nin eski ÖLÇÜLEMEDİ cümleleri ~~ içinde
  M1/M2  kural sentetik veriyle iki yönde sınanır (boş kapı olmasın): yanlış
      değer YAKALANIR, doğru değer YAKALANMAZ
"""

import re
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
FDR = KOK / "FDR"
B4 = FDR / "BOLUM_4_TEST_FAALIYETLERI.md"
PARAM = KOK / "config" / "pixhawk" / "arducopter_fda_20260906.param"
LOGDIR = KOK / "results" / "ucus_loglari" / "20260906"
PITCH = LOGDIR / "pitch_kolu_analizi.txt"
DEVRILME = LOGDIR / "2026-09-06 19-52-44_devrilme.txt"
ARM_DETAY = LOGDIR / "arm_analizi_detay.txt"

# §4.6 tablosunda dosyadan birebir yazılması ZORUNLU parametreler
ZORUNLU = [
    "INS_ACCOFFS_X", "INS_ACCOFFS_Y", "INS_ACCOFFS_Z",
    "INS_ACCSCAL_X", "INS_ACCSCAL_Y", "INS_ACCSCAL_Z",
    "INS_GYROFFS_X", "INS_GYROFFS_Y", "INS_GYROFFS_Z",
    "AHRS_TRIM_X", "AHRS_TRIM_Y",
    "COMPASS_OFS_X", "COMPASS_OFS_Y", "COMPASS_OFS_Z",
    "COMPASS_OFS2_X", "COMPASS_OFS2_Y", "COMPASS_OFS2_Z",
]


def _oku(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def bolum(metin, bas, son):
    """`## bas` başlığından `## son` başlığına kadar olan metin."""
    i = metin.index(f"\n## {bas} ")
    j = metin.index(f"\n## {son} ", i)
    return metin[i:j]


def param_satirlari(metin):
    """`AD,DEGER` satırları → {AD: (satır_no, DEGER_ham)}."""
    d = {}
    for i, s in enumerate(metin.splitlines(), 1):
        if "," in s and not s.startswith("#"):
            ad, _, deger = s.partition(",")
            d[ad.strip()] = (i, deger.strip())
    return d


def normalize(metin):
    """Rapor yazımı → karşılaştırılabilir ASCII: unicode eksi, virgül ondalık."""
    metin = metin.replace("−", "-").replace("‑", "-")
    return re.sub(r"(?<=\d),(?=\d)", ".", metin)


SATIR_ATFI = re.compile(r":(\d+)(?:\s*[–-]\s*(\d+))?")


def atif_araliklari(rapor_metni):
    """Rapordaki `:477` ve `:477–479` atıfları → [(477, 477), (477, 479), ...]."""
    return [(int(a), int(b or a)) for a, b in SATIR_ATFI.findall(rapor_metni)]


def eksik_degerler(rapor_metni, params, adlar):
    """Raporda dosyadaki ham değeri ya da `:satır` atfı olmayan parametreler.

    Atıf tek satır (`:263`) ya da aralık (`:477–479`) olabilir; parametrenin
    dosya satırı bir aralığın İÇİNDE ise atıf var sayılır.
    """
    araliklar = atif_araliklari(rapor_metni)
    eksik = []
    for ad in adlar:
        satir, deger = params[ad]
        if f"`{deger}`" not in rapor_metni:
            eksik.append(f"{ad}={deger} (değer raporda yok)")
        if not any(a <= satir <= b for a, b in araliklar):
            eksik.append(f"{ad} satır :{satir} (atıf raporda yok)")
    return eksik


def hucreler(satir):
    """Markdown tablo satırı → hücre listesi. `| a | b | c |` → ['a', 'b', 'c']."""
    return [h.strip() for h in satir.strip().strip("|").split("|")]


def son_hucre_kusurlari(satir, gerekli=(), yasak=()):
    """Satırın SON hücresi (§4.12'de 6 Eylül ÖLÇÜM sütunu) için eksik/yasak metinler.

    Neden hücre: satırın tamamına `assertIn` uygulanınca 5 Eylül sütunundaki
    eski "tetiklenmedi" / "ÖLÇÜLEMEDİ" eşleşmeyi doyurur ve 6 Eylül hücresi
    "GEÇTİ" yapılsa da kapı sessiz kalır (T218 çürütücü bulgusu, madde 7).
    """
    h = hucreler(satir)[-1]
    kusur = [f"'{g}' son hücrede yok" for g in gerekli if g not in h]
    kusur += [f"'{y}' son hücrede VAR" for y in yasak if y in h]
    return kusur


# §4.12 tablosunda "tetiklenmedi" satırları için 6 Eylül hücresi kuralı
TETIKLENMEDI_GEREKLI = ("tetiklenmedi",)
TETIKLENMEDI_YASAK = ("GEÇTİ", "ÖLÇÜLDÜ —")
# RC kaybı satırı için 6 Eylül hücresi kuralı
RC_GEREKLI = ("ÖLÇÜLDÜ", "DÜŞTÜ", "D-428", "kumanda failsafe ayarı")
RC_YASAK = ("GEÇTİ",)


def pencere_pitch(metin):
    """pitch_kolu_analizi.txt → {'P19': (min, max), ...}."""
    sonuc, p = {}, None
    for s in metin.splitlines():
        m = re.match(r"=== (P\d+) ", s)
        if m:
            p = m.group(1)
        m = re.match(r"\s*pitch min (-?[\d.]+)°\s+max (-?[\d.]+)°", s)
        if m and p:
            sonuc[p] = (float(m.group(1)), float(m.group(2)))
    return sonuc


def eksik_pitch(rapor_metni, pencereler):
    """Raporda geçmeyen pencere pitch değerleri."""
    r = normalize(rapor_metni)
    eksik = []
    for p, (mn, mx) in pencereler.items():
        # P37 için raporda min..max aralığı (+1,4 … +1,9) yazılır; ötekilerde min
        hedef = f"{mn:.1f}" if mn < 0 else f"+{mn:.1f}"
        if hedef not in r:
            eksik.append(f"{p} pitch min {hedef}")
    return eksik


class T1_ParamDegerleriDosyadan(unittest.TestCase):
    def test_capa_dosyalar_var(self):
        for p in (B4, PARAM, PITCH, DEVRILME, ARM_DETAY):
            self.assertTrue(p.is_file(), p)

    def test_T1_46_tablosu_dokumle_birebir(self):
        params = param_satirlari(_oku(PARAM))
        b46 = bolum(_oku(B4), "4.6", "4.7")
        self.assertEqual([], eksik_degerler(b46, params, ZORUNLU),
                         "§4.6 tablosu 6 Eylül dökümünden sapmış — bayat sayı")

    def test_T1b_pitot_kapsam_disi_dokumle(self):
        params = param_satirlari(_oku(PARAM))
        self.assertEqual("0", params["ARSPD_ENABLE"][1])
        b46 = bolum(_oku(B4), "4.6", "4.7")
        self.assertIn("ARSPD_ENABLE,0", b46)
        self.assertIn("KAPSAM DIŞI", b46.upper().replace("I", "I"))


class T2_T3_TlogSayilari(unittest.TestCase):
    def test_T2_devrilme_pitch_degerleri_ham_ciktiyla(self):
        pencereler = pencere_pitch(_oku(PITCH))
        self.assertEqual({"P19", "P20", "P26", "P37"}, set(pencereler),
                         "pitch_kolu_analizi.txt beklenen 4 pencereyi taşımıyor")
        b410 = bolum(_oku(B4), "4.10", "4.11")
        self.assertEqual([], eksik_pitch(b410, pencereler))

    def test_T3_arm_sayilari_ham_ciktiyla(self):
        dev = _oku(DEVRILME)
        m = re.search(r"## 3\. Arm pencereleri \(HEARTBEAT armed\): (\d+)", dev)
        self.assertIsNotNone(m)
        arm_n = m.group(1)
        m2 = re.search(r"toplam (\d+) çevirme", _oku(ARM_DETAY))
        self.assertIsNotNone(m2)
        ch6_n = m2.group(1)
        b410 = bolum(_oku(B4), "4.10", "4.11")
        self.assertIn(f"**{arm_n}** arm penceresi", b410)
        self.assertIn(f"**{ch6_n}** çevirme", b410)
        # tlog son PARAM_VALUE pusula ofsetleri §4.6'da birebir
        b46 = bolum(_oku(B4), "4.6", "4.7")
        for ad in ("COMPASS_OFS_X", "COMPASS_OFS_Y", "COMPASS_OFS_Z"):
            m3 = re.search(rf"^\s*{ad}\s*=\s*(-?[\d.]+)", dev, re.M)
            self.assertIsNotNone(m3, ad)
            self.assertIn(f"`{m3.group(1)}`", b46,
                          f"tlog son {ad} raporda yok")


class T4_RcFailsafeHukmu(unittest.TestCase):
    def _b412(self):
        b412 = bolum(_oku(B4), "4.12", "4.13")
        # "son hücre = 6 Eylül (ÖLÇÜM)" varsayımı tablo başlığına bağlanır:
        # sütun eklenir/yer değiştirirse kapı sessizce yanlış hücreye bakmasın
        baslik = [s for s in b412.splitlines() if s.startswith("| arıza senaryosu |")]
        self.assertEqual(1, len(baslik), "§4.12 arıza tablosu başlığı tek olmalı")
        self.assertIn("6 Eylül", hucreler(baslik[0])[-1],
                      "§4.12 tablosunun son sütunu 6 Eylül (ÖLÇÜM) değil")
        self.assertIn("5 Eylül", hucreler(baslik[0])[-2])
        return b412

    def test_T4_rc_kaybi_satiri_olculdu_ve_dustu(self):
        b412 = self._b412()
        satir = [s for s in b412.splitlines()
                 if s.startswith("| RC kaybı (kumanda kapatma)")]
        self.assertEqual(1, len(satir), "RC kaybı satırı tek olmalı")
        s = satir[0]
        # 6 Eylül (ÖLÇÜM) hücresi: ÖLÇÜLDÜ + DÜŞTÜ + D-428 + düzeltme; GEÇTİ yok
        self.assertEqual([], son_hucre_kusurlari(s, RC_GEREKLI, RC_YASAK))
        # 5 Eylül hücresindeki eski ÖLÇÜLEMEDİ korunmuş (T7 ile tutarlı)
        self.assertIn("ÖLÇÜLEMEDİ", hucreler(s)[-2])
        self.assertNotIn("GEÇTİ", s, "ÖLÇÜLEMEDİ/DÜŞTÜ satırında GEÇTİ olamaz")

    def test_T4b_y4m12_sahada_sarti_karsilanmadi(self):
        b412 = bolum(_oku(B4), "4.12", "4.13")
        self.assertRegex(b412, r"Y-4-M12`?[^\n]{0,80}KARŞILANMADI")

    def test_T4c_diger_senaryolar_tetiklenmedi(self):
        b412 = self._b412()
        for sen in ("YKS/Jetson bağlantı kaybı", "Düşük pil", "Geofence"):
            # hücre TAM eşleşir: "| Geofence |" — yazılım yolu tablosundaki
            # "| Geofence ihlali |" satırı bu kapının konusu değil
            satir = [s for s in b412.splitlines() if s.startswith(f"| {sen} |")]
            self.assertEqual(1, len(satir), sen)
            # 6 Eylül (ÖLÇÜM) hücresine bakılır — satırın tamamına değil;
            # 5 Eylül hücresindeki "tetiklenmedi" 6 Eylül'ü doyuramaz
            self.assertEqual([], son_hucre_kusurlari(
                satir[0], TETIKLENMEDI_GEREKLI, TETIKLENMEDI_YASAK), sen)
            self.assertIn("tetiklenmedi", hucreler(satir[0])[-2], f"{sen} 5 Eylül")


class T5_BayatSatirlar(unittest.TestCase):
    def test_T5a_score_py_yolu(self):
        self.assertTrue((KOK / "simulation" / "score.py").is_file())
        for p in sorted(FDR.glob("*.md")):
            for i, s in enumerate(_oku(p).splitlines(), 1):
                if "simulation/scripts/score.py" in s:
                    self.assertIn("~~`simulation/scripts/score.py`~~", s,
                                  f"{p.name}:{i} bayat yol üstü çizili değil")

    def test_T5b_readme_ekip_isimleri_dustu(self):
        satirlar = [s for s in _oku(FDR / "README.md").splitlines()
                    if "ekip isimleri" in s]
        self.assertTrue(satirlar, "README ekip isimleri satırı silinmiş — eski metin korunmalı")
        for s in satirlar:
            self.assertIn("~~ekip isimleri ve rol ataması~~", s)

    def test_T5c_yonerge_y4m06_artik_yok_degil(self):
        satir = [s for s in _oku(FDR / "YONERGE_HARITASI.md").splitlines()
                 if s.startswith("| `Y-4-M06`")]
        self.assertEqual(1, len(satir))
        self.assertIn("~~YOK (5 Eylül)~~", satir[0])
        self.assertIn("KISMEN", satir[0])


class T6_T7_TakvimVeEskiMetin(unittest.TestCase):
    def test_T6_takvim_olculen_olaylar(self):
        b43 = bolum(_oku(B4), "4.3", "4.4")
        for anahtar in ("5 Eylül 14:52", "6 Eylül 17:05", "6 Eylül 18:30",
                        "6 Eylül 20:45", "7 Eylül", "10 Eylül",
                        "D-426", "D-428", "D-429", "D-431", "D-433", "D-434", "D-438"):
            self.assertIn(anahtar, b43, anahtar)
        hover = [s for s in b43.splitlines() if "hover yapabiliyoruz" in s]
        self.assertEqual(1, len(hover))
        self.assertIn("BEYAN", hover[0])
        self.assertIn("D-439", hover[0])

    def test_T7_eski_metin_ustu_cizili_korunmus(self):
        m = _oku(B4)
        b46 = bolum(m, "4.6", "4.7")
        self.assertIn("~~🔴 **ÖLÇÜLEMEDİ: 5 Eylül 2026'da Pixhawk 6C ele alındı", b46)
        b412 = bolum(m, "4.12", "4.13")
        self.assertIn("~~hiçbir arıza emniyet tepkisi sahada test edilmedi.~~", b412)
        b43 = bolum(m, "4.3", "4.4")
        self.assertIn("~~ilk gerçek sayı 6–19 Eylül prova uçuşlarından", b43)


class MutasyonKontrolu(unittest.TestCase):
    """Kural sentetik veriyle iki yönde sınanır — boş kapı olmasın (D-370)."""

    def test_M1_yanlis_param_degeri_YAKALANIR(self):
        params = {"INS_ACCOFFS_X": (477, "0.01807415")}
        dogru = "| `INS_ACCOFFS_*` | `0.01807415` | … | :477–479 |"
        self.assertEqual([], eksik_degerler(dogru, params, ["INS_ACCOFFS_X"]))
        yanlis = dogru.replace("0.01807415", "0.01807416")
        self.assertNotEqual(dogru, yanlis, "MUTASYON UYGULANMADI")
        self.assertEqual(1, len(eksik_degerler(yanlis, params, ["INS_ACCOFFS_X"])))
        # satır atfı kayınca da yakalanır
        self.assertEqual(1, len(eksik_degerler(
            dogru.replace(":477–479", ":478–479"), params, ["INS_ACCOFFS_X"])))

    def test_M2_yanlis_pitch_YAKALANIR_dogru_YAKALANMAZ(self):
        pencereler = {"P19": (-43.8, 2.0), "P37": (1.4, 1.9)}
        dogru = "| **19** | … | **−43,8°** | … |\n| 37 | … | **+1,4 … +1,9°** |"
        self.assertEqual([], eksik_pitch(dogru, pencereler))
        self.assertEqual(["P19 pitch min -43.8"],
                         eksik_pitch(dogru.replace("−43,8", "−43,9"), pencereler))

    def test_M3_bolum_kesici_gercek_basliklarla(self):
        m = _oku(B4)
        for bas, son in (("4.3", "4.4"), ("4.6", "4.7"), ("4.10", "4.11"), ("4.12", "4.13")):
            b = bolum(m, bas, son)
            self.assertTrue(b.startswith(f"\n## {bas} "))
            self.assertNotIn(f"\n## {son} ", b)

    def test_M4_6eylul_hucresi_GECTI_YAKALANIR_5eylul_doyuramaz(self):
        """T218 çürütücü bulgusu (madde 7): 5 Eylül 'tetiklenmedi', 6 Eylül 'GEÇTİ'."""
        dogru = ("| Geofence | `FENCE_ENABLE,1` | tetiklenmedi; dökümsüz "
                 "| tetiklenmedi. Kart: `FENCE_ENABLE,1` (`:361`) |")
        self.assertEqual(["Geofence", "`FENCE_ENABLE,1`", "tetiklenmedi; dökümsüz",
                          "tetiklenmedi. Kart: `FENCE_ENABLE,1` (`:361`)"], hucreler(dogru))
        self.assertEqual([], son_hucre_kusurlari(dogru, TETIKLENMEDI_GEREKLI, TETIKLENMEDI_YASAK))
        mutant = dogru.replace("| tetiklenmedi. Kart:", "| GEÇTİ. Kart:")
        self.assertNotEqual(dogru, mutant, "MUTASYON UYGULANMADI")
        # eski yöntem (satırın tamamı) mutanta KÖRDÜR — 5 Eylül hücresi doyurur
        self.assertIn("tetiklenmedi", mutant)
        # yeni yöntem (son hücre) YAKALAR: tetiklenmedi yok + GEÇTİ var
        self.assertEqual(["'tetiklenmedi' son hücrede yok", "'GEÇTİ' son hücrede VAR"],
                         son_hucre_kusurlari(mutant, TETIKLENMEDI_GEREKLI, TETIKLENMEDI_YASAK))
        # "ÖLÇÜLDÜ — GEÇTİ" biçimi de yakalanır
        mutant2 = dogru.replace("| tetiklenmedi. Kart:", "| tetiklenmedi; ÖLÇÜLDÜ — GEÇTİ. Kart:")
        self.assertEqual(2, len(son_hucre_kusurlari(mutant2, TETIKLENMEDI_GEREKLI, TETIKLENMEDI_YASAK)))
        # RC satırı: 5 Eylül ÖLÇÜLEMEDİ, 6 Eylül GEÇTİ → YAKALANIR; doğru → YAKALANMAZ
        rc_dogru = ("| RC kaybı (kumanda kapatma) | `FS_THR_ENABLE,1` | **ÖLÇÜLEMEDİ** — gelmedi "
                    "| **ÖLÇÜLDÜ — DÜŞTÜ** (D-428 §2); **düzeltme: kumanda failsafe ayarı** |")
        self.assertEqual([], son_hucre_kusurlari(rc_dogru, RC_GEREKLI, RC_YASAK))
        self.assertIn("ÖLÇÜLEMEDİ", hucreler(rc_dogru)[-2])
        rc_mutant = rc_dogru.replace("**ÖLÇÜLDÜ — DÜŞTÜ** (D-428 §2)", "**GEÇTİ** (D-428 §2)")
        self.assertNotEqual(rc_dogru, rc_mutant, "MUTASYON UYGULANMADI")
        self.assertEqual(["'ÖLÇÜLDÜ' son hücrede yok", "'DÜŞTÜ' son hücrede yok",
                          "'GEÇTİ' son hücrede VAR"],
                         son_hucre_kusurlari(rc_mutant, RC_GEREKLI, RC_YASAK))


if __name__ == "__main__":
    unittest.main()
