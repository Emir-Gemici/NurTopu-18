"""T232 — ATOLYE TEST GUNU KAPISI (12 Eylul 2026): kagit yalan soylemesin, tahmin sonuc olmasin.

NEDEN: ATOLYE_TEST_GUNU_20260912.md ekibin mimar olmadan uygulayacagi test gunu planidir
(D-444). Olu komut (betik yok, bayrak degismis) ekibi atolyede durdurur (D-421 sinifi);
kaynaksiz beklenti tahmini sonuc gibi gosterir (D-444); geri alinmayan BATT_LOW_VOLT araci
yanlis esikle birakir. Bu kapi belgeyi degil ICERIGI olcer:

  K1  A1..A13 bolumleri sirayla VE tam (A14 yok); her bolumde TEK 'Kabul' satiri (kaynakli:
      dosya:satir, URL ya da 'ön kayıt'), TEK BEKLENTI satiri (dayanak turu + 'ölçüm değil' +
      kaynak; HESAP ise '=' ve sayi), Amaç, Beklenen görüntü, bir depo betigi komutu,
      'ÖLÇÜLECEK (12 Eylül atölye)' + KENDI numarasiyla results/atolye_20260912/A<n>_ sonuc
      dosyasi + foto/video, TEK OLCULDU/OLCULEMEDI kutusu
  K2  'GEÇTİ' kelimesi (her yazimi) belgede ve sonuc sablonunda YOK (D-444)
  K3  A3: gecici BATT_LOW_VOLT adimindan SONRA 'GERİ AL (zorunlu' adimi; ayni satirda
      dokumdeki deger (14.4), Write/Refresh Params ve yeniden baslatma; gun sonunda
      Compare Params
  K4  atif yapilan depo yollari var + git'te izleniyor; komut olarak cagrilan her .py
      --help ile 0; komutlar dogru yorumlayiciyla (PC '& $PY -B', Jetson 'python -B' /
      '/usr/bin/python3'); PC komutunda /dev/, Jetson komutunda COMx yok; A5/A6/A8/A9/A11'de
      iki uc da var; A5 girdisi rota.json iha_sender ayristiricisindan geciyor
  K5  dokum atiflari (`AD=DEGER` (döküm :N)) dokum satiriyla birebir; kod atiflari
      (`metin` (yol.py:N)) o satirda birebir; satir atiflari dosya boyunda; KAYNAK NOBETCISI:
      atif yapilan satirlar belgedeki sayilari gercekten tasiyor; benzer olcum sayilari
      kaynak JSON'dan yeniden yuvarlanip belgede aranir
  K6  HESAP satirlari yeniden hesaplanir (10 PWM kurali, zaman asimlari, seri sure, RTT alt
      siniri, kosegen, akis hizi, FOV, FPS esigi, gecikme toplami, itki orani, yuksuz akim)
      — girdi sabiti ya da sonuc degisirse DUSER
  K7  zaman butcesi: tablo 09:00'dan kesintisiz, 14:00'te biter; A1..A13 birer kez; her
      bolum basligindaki 'NN dk' tablodaki dilimle ayni
  K8  0..5 ana bolumleri; getirilecekler ve guvenlik (PERVANESİZ, hover ayri adim) tam;
      A11 kurulum sirasi (IP .25, .11/.12/.20 yasak, Camera 1, kopru + YKS komutu, T226
      notu, T230 fotograflari); A1-A4 MP adimlari (Messages, DataFlash indirme); <= 220 satir
  K9  SONUC_SABLONU: A1..A13 satirlari sirayla, her satirda bolumun ana sonuc dosyasi ve kutu
  K10 scripts/ucus_logu_devrilme.py --help -> 0 (A1-A4, A12 .bin ozeti); dosya yoksa 1
"""
from __future__ import annotations

import inspect
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
KAGIT = KOK / "ATOLYE_TEST_GUNU_20260912.md"
SONUC_DIZIN = "results/atolye_20260912/"
SABLON = KOK / SONUC_DIZIN / "SONUC_SABLONU.md"
DOKUM = KOK / "config" / "pixhawk" / "arducopter_fda_20260906.param"
H2_OZET = KOK / "results" / "fdr_sprint_20260910" / "H2" / "ozet.json"
JETSON_OZET = KOK / "results" / "jetson_20260906" / "jetson_fps_20260906_orin_nano" / "ozet.json"
ROTA_GIRDI = "results/fdr_sprint_20260910/H1/k3b/v1/harita_4_kolay/iha_scan/rota.json"
AZAMI_SATIR = 220
TEST_SAYISI = 13
ASGARI_BETIK = 8
ASGARI_DOKUM_ATFI = 15
ASGARI_KOD_ATFI = 8
IKI_UC_BOLUMLER = (5, 6, 8, 9, 11)
ORTAM = {**os.environ, "PYTHONIOENCODING": "utf-8"}

for _y in (KOK / "codes", KOK / "comms"):
    if str(_y) not in sys.path:
        sys.path.insert(0, str(_y))

import karar_sozlesmesi as ks  # noqa: E402

#: Rakam sinifi bilerek \d+: "### A14" eklenince liste 1..14 olur ve esitlik duser.
A_BASLIK = re.compile(r"^### A(\d+) — .*· (\d+) dk[ \t]*$", re.M)
ANA_BASLIK = re.compile(r"^## (\d+)\. ", re.M)
ALT_BASLIK = re.compile(r"^#{2,3} ", re.M)
KUTU = re.compile(r"\[ \] ÖLÇÜLDÜ\s+\[ \] ÖLÇÜLEMEDİ — neden:")
KABUL = re.compile(r"^- \*\*Kabul \(([^)\n]+)\):\*\*(.+)$", re.M)
BEKLENTI = re.compile(r"^- \*\*BEKLENTİ \(([^)\n]+)\):\*\*(.+)$", re.M)
SONUC = re.compile(r"^- \*\*Sonuç: ÖLÇÜLECEK \(12 Eylül atölye\)\*\* → "
                   r"`(results/atolye_20260912/A(\d+)_[^`]+)`(.*)$", re.M)
DAYANAK = re.compile(r"HESAP|ÜRETİCİ VERİSİ|BENZER ÖLÇÜM")
#: D-444: "GEÇTİ" program/kagitta HIC gecmez. Buyuk/kucuk, Turkce/ASCII her yazim.
YASAK = re.compile(r"[Gg][Ee][CcÇç][Tt][İIiı]")
SATIR_ATFI = re.compile(
    r"(?<![\w/\\.])((?:[\w\-]+/)*[\w\-]+\.(?:md|py|param|json)):(\d+)(?:-(\d+))?")
KOD_ATFI = re.compile(r"`([^`\n]+)` \(((?:codes|comms|scripts)/[\w/.\-]+\.py):(\d+)\)")
DOKUM_ATFI = re.compile(r"`([A-Z][A-Z0-9_]*)=([^`\s]+)` \(döküm :(\d+)")
SPAN = re.compile(r"`([^`\n]+)`")
BETIK_YOLU = re.compile(r"(?<![\w/\\])((?:scripts|codes|comms)/[\w.\-/]+\.py)")
DEPO_YOLU = re.compile(
    r"(?<![\w/\\])((?:scripts|codes|comms|jetson_paket|tests|config/pixhawk|FDR)/"
    r"[\w.\-/]+\.(?:py|sh|md|param|json))")
#: results/ altinda atolye klasoru CIKTIDIR (henuz yok); digerleri GIRDI/kanittir, olmali.
GIRDI_YOLU = re.compile(
    r"(?<![\w/\\])(results/(?!atolye_20260912/)[\w.\-/]+\.(?:json|md|txt))")
KOK_BELGE = re.compile(r"`([A-Za-z_0-9]+\.md)`")
URL = "https://"
PC_ONEK = "& $PY -B "
JETSON_ONEK = ("python -B ", "/usr/bin/python3 ")
FOTO_VIDEO = re.compile(r"\.(?:mp4|jpg|png)`")

#: Kagidin dayandigi kaynak satirlar gercekten o sayiyi tasiyor mu (kaynak kayarsa DUSER).
KAYNAK_NOBETCISI = [
    ("SAHA_KOSUM_KAGIDI_20260910.md", 54, "≤ 2 s"),
    ("SAHA_KOSUM_KAGIDI_20260910.md", 20, "50–65°"),
    ("SAHA_KOSUM_KAGIDI_20260910.md", 31, ">%98, 300 m"),
    ("SAHA_KOSUM_KAGIDI_20260910.md", 11, "/dev/ttyTHS1"),
    ("SAHA_KOSUM_KAGIDI_20260910.md", 17, "jetson-io"),
    ("results/fdr_sprint_20260910/H9_MK15/TASARIM.md", 15, ".11 hava / .12 yer / .20 Android"),
    ("results/fdr_sprint_20260910/H9_MK15/TASARIM.md", 16, "192.168.144.25"),
    ("results/fdr_sprint_20260910/H9_MK15/TASARIM.md", 18, "130–250 ms"),
    ("results/fdr_sprint_20260910/H9_MK15/TASARIM.md", 18, "49–85 ms"),
    ("results/fdr_sprint_20260910/H9_MK15/TASARIM.md", 73, "≤ 1,0 s"),
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 304, "yüksüz 0,7 A/10 V"),
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 315, "38 A / 30 s"),
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 318, "4,8 A"),
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 319, "6,5 A"),
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 320, "8,7 A"),
    # T244 (12 Eylül 2026): §3.3.1.1.8 ve §3.3.4.x düzeltmeleri bu satırı 915 -> 929 kaydırdı
    # (D-462 A1/A2/A3 süpürgesi). Kaynak metin degismedi; yalniz satir numarasi tazelendi.
    ("FDR/BOLUM_3_SISTEM_SPESIFIKASYONLARI.md", 929, "0,61 FPS"),
    ("results/fdr_sprint_20260910/H2/ozet.json", 131, "1.3252"),
    ("results/fdr_sprint_20260910/H2/ozet.json", 132, "1.8318"),
    ("results/fdr_sprint_20260910/H2/ozet.json", 139, "16070"),
    ("results/fdr_sprint_20260910/H2/ozet.json", 143, "322.52"),
    ("results/fdr_sprint_20260910/H2/ozet.json", 189, "403.03"),
    ("results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json", 69, "739.076"),
    ("results/jetson_20260906/jetson_fps_20260906_orin_nano/ozet.json", 70, "942.15"),
    ("config/pixhawk/README.md", 143, "source-system"),
    ("config/pixhawk/README.md", 154, "EXTENDED_SYS_STATE"),
    ("scripts/sik_rf_olc.py", 39, "UYUMLU"),
    ("scripts/sik_rf_olc.py", 43, "Kayip icin esik YOK"),
]

GETIRILECEKLER = ("pens ampermetre", "SiK", "Jetson", "CSI kamera", "15→22", "Pixhawk USB",
                  "MK15 kumanda", "Air Unit Mini", "HDMI giriş dönüştürücü", "DP→HDMI",
                  "mini HDMI", "12 V", "yakalama kartı", "60 fps", "ölçü şeridi",
                  "iki işaret", "dolu pil", "Laptop YKS")
GUVENLIK = ("PERVANESİZ", "A1–A4", "A13", "ayrı adımda", "bağlı", "açık alan")


def _metin():
    return KAGIT.read_text(encoding="utf-8")


def _satirlar(yol):
    return (KOK / yol).read_text(encoding="utf-8").splitlines()


def _bolumler():
    """[(no, dk, metin)] — her '### A<n>' basligindan bir sonraki '##'/'###' basligina."""
    m = _metin()
    out = []
    for b in A_BASLIK.finditer(m):
        s = ALT_BASLIK.search(m, b.end())
        out.append((int(b.group(1)), int(b.group(2)), m[b.start():s.start() if s else len(m)]))
    return out


def _bolum(no):
    return {n: t for n, _, t in _bolumler()}[no]


def _ana_bolum(no):
    m = _metin()
    b = re.search(rf"^## {no}\. .*$", m, re.M)
    if b is None:
        raise AssertionError(f"'## {no}.' bolumu yok")
    s = ANA_BASLIK.search(m, b.end())
    return m[b.start():s.start() if s else len(m)]


def _dokum_satirlari():
    return DOKUM.read_text(encoding="utf-8").splitlines()


def _dokum_deger(ad):
    for s in _dokum_satirlari():
        if s.startswith(ad + ","):
            return s.split(",", 1)[1].strip()
    raise KeyError(ad)


def _tr(x, nd):
    """Turkce ondalik yazim (virgul)."""
    return f"{x:.{nd}f}".replace(".", ",")


def _komutlar(metin=None):
    """Depo betigi cagiran backtick'li komutlar (bosluk iceren span)."""
    return [s for s in SPAN.findall(metin if metin is not None else _metin())
            if " " in s and BETIK_YOLU.search(s)]


def _satir_atiflari():
    """{(yol, satir)} — araliklar (a-b) acilir."""
    out = set()
    for yol, a, b in SATIR_ATFI.findall(_metin()):
        for n in range(int(a), int(b or a) + 1):
            out.add((yol, n))
    return out


def _ana_sonuc_dosyasi(no):
    m = SONUC.search(_bolum(no))
    return m.group(1) if m else None


class K1_Bolumler(unittest.TestCase):
    def test_A1_A13_sirali_ve_tam(self):
        self.assertEqual(list(range(1, TEST_SAYISI + 1)), [n for n, _, _ in _bolumler()])
        self.assertNotRegex(_metin(), r"(?m)^### A(?:0|1[4-9]|[2-9]\d)\b")

    def test_her_bolumun_ogeleri(self):
        for no, _, b in _bolumler():
            with self.subTest(bolum=f"A{no}"):
                kabul = KABUL.findall(b)
                self.assertEqual(1, len(kabul), "tek 'Kabul' satiri olmali")
                kaynak, govde = kabul[0]
                satir = kaynak + govde
                self.assertTrue(SATIR_ATFI.search(satir) or URL in satir or "ön kayıt" in satir,
                                f"Kabul kaynaksiz: {satir[:120]}")
                bek = BEKLENTI.findall(b)
                self.assertEqual(1, len(bek), "tek BEKLENTI satiri olmali")
                dayanak, govde = bek[0]
                self.assertRegex(dayanak, DAYANAK)
                self.assertIn("ölçüm değil", dayanak)
                self.assertTrue(SATIR_ATFI.search(govde) or URL in govde
                                or KOD_ATFI.search(govde) or "(döküm :" in govde,
                                f"BEKLENTI kaynaksiz: {govde[:120]}")
                if "HESAP" in dayanak:
                    self.assertIn("=", govde, "HESAP formulsuz")
                    self.assertRegex(govde, r"\d")
                sonuc = SONUC.findall(b)
                self.assertEqual(1, len(sonuc), "tek 'Sonuç: ÖLÇÜLECEK' satiri olmali")
                self.assertEqual(str(no), sonuc[0][1], "sonuc dosyasi baska testin numarasini tasiyor")
                self.assertRegex(sonuc[0][0] + sonuc[0][2], FOTO_VIDEO, "foto/video kaniti yok")
                self.assertEqual(1, len(KUTU.findall(b)))
                self.assertIn("**Amaç:**", b)
                self.assertIn("Beklenen görüntü", b)
                self.assertTrue(_komutlar(b), "bolumde depo betigi komutu yok")

    def test_sonuc_klasoru_ve_kural_basligi(self):
        bas = "\n".join(_metin().splitlines()[:8])
        self.assertIn("D-444", bas)
        self.assertIn("tahmin SONUÇ değildir", bas)
        self.assertIn("ölçüm değil", bas)
        self.assertIn(SONUC_DIZIN, bas)
        self.assertIn("T231", bas)


class K2_YasakKelime(unittest.TestCase):
    def test_kagitta_yok(self):
        self.assertEqual([], YASAK.findall(_metin()))

    def test_sablonda_yok(self):
        self.assertEqual([], YASAK.findall(SABLON.read_text(encoding="utf-8")))


class K3_A3GeriAlma(unittest.TestCase):
    def test_geri_alma_adimi_gecici_adimdan_sonra(self):
        satirlar = _bolum(3).splitlines()
        gecici = [i for i, s in enumerate(satirlar) if "(GEÇİCİ)" in s and "BATT_LOW_VOLT" in s]
        geri = [i for i, s in enumerate(satirlar) if "GERİ AL (zorunlu" in s]
        self.assertTrue(gecici, "A3'te gecici BATT_LOW_VOLT adimi yok")
        self.assertEqual(1, len(geri), "A3'te 'GERİ AL (zorunlu' adimi yok")
        self.assertGreater(geri[0], max(gecici), "geri alma, gecici adimdan ONCE yazilmis")
        s = satirlar[geri[0]]
        for parca in ("BATT_LOW_VOLT", f"**{_dokum_deger('BATT_LOW_VOLT')}**", "Write Params",
                      "Refresh Params", "yeniden başlat"):
            with self.subTest(parca=parca):
                self.assertIn(parca, s)

    def test_kabul_geri_almayi_istiyor_ve_gun_sonu_karsilastiriyor(self):
        kabul = KABUL.findall(_bolum(3))[0][1]
        self.assertIn("geri alma kanıtı", kabul)
        self.assertIn(_dokum_deger("BATT_LOW_VOLT"), kabul)
        self.assertIn("Compare Params", _ana_bolum(4))


class K4_Komutlar(unittest.TestCase):
    def test_depo_yollari_var_ve_izleniyor(self):
        m = _metin()
        yollar = sorted(set(DEPO_YOLU.findall(m)) | set(GIRDI_YOLU.findall(m))
                        | set(KOK_BELGE.findall(m)))
        self.assertGreaterEqual(len(yollar), 10, yollar)
        eksik = [y for y in yollar if not (KOK / y).is_file()]
        self.assertEqual([], eksik)
        git = shutil.which("git")
        if git is None:
            self.skipTest("git yok")
        r = subprocess.run([git, "ls-files", "--error-unmatch", "--", *yollar], cwd=str(KOK),
                           capture_output=True, text=True, timeout=60)
        self.assertEqual(0, r.returncode, r.stderr[-600:])

    def test_satir_atiflari_dosya_boyunda(self):
        atiflar = _satir_atiflari()
        self.assertGreaterEqual(len({y for y, _ in atiflar}), 6)
        for yol, n in sorted(atiflar):
            with self.subTest(atif=f"{yol}:{n}"):
                self.assertTrue((KOK / yol).is_file(), yol)
                self.assertLessEqual(n, len(_satirlar(yol)))

    def test_cagrilan_betikler_help_sifir(self):
        betikler = sorted({y for s in _komutlar() for y in BETIK_YOLU.findall(s)})
        self.assertGreaterEqual(len(betikler), ASGARI_BETIK, betikler)
        for y in betikler:
            with self.subTest(betik=y):
                r = subprocess.run([sys.executable, "-B", str(KOK / y), "--help"], cwd=str(KOK),
                                   env=ORTAM, capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=180)
                self.assertEqual(0, r.returncode, r.stderr[-600:])
                self.assertTrue(r.stdout.strip(), "--help bos basti")

    def test_yorumlayici_ve_uc_ayrimi(self):
        for s in _komutlar():
            with self.subTest(komut=s[:70]):
                self.assertTrue(s.startswith(PC_ONEK) or s.startswith(JETSON_ONEK),
                                "komut dogru yorumlayiciyla baslamiyor")
                if s.startswith(PC_ONEK):
                    self.assertNotIn("/dev/", s, "PC komutunda Linux aygiti")
                else:
                    self.assertNotRegex(s, r"\bCOM[xy0-9]", "Jetson komutunda Windows portu")
        self.assertNotRegex(_metin(), r"`python (?!-B)", "ciplak python (PC'de Store saplamasi)")

    def test_iki_uclu_bolumlerde_pc_ve_jetson_komutu(self):
        for no in IKI_UC_BOLUMLER:
            with self.subTest(bolum=f"A{no}"):
                k = _komutlar(_bolum(no))
                self.assertTrue(any(s.startswith(PC_ONEK) for s in k), "PC komutu yok")
                self.assertTrue(any(s.startswith(JETSON_ONEK) for s in k), "Jetson komutu yok")

    def test_rota_girdisi_iha_sender_ayristiricisindan_gecer(self):
        self.assertIn(ROTA_GIRDI, _bolum(5))
        import iha_sender
        road, conf, _ref, _wp = iha_sender.rota_json_oku(str(KOK / ROTA_GIRDI))
        self.assertIn(road, (1, 2, 3))
        self.assertGreater(conf, 0.0)


class K5_Kaynaklar(unittest.TestCase):
    def test_dokum_atiflari_satirla_birebir(self):
        atiflar = DOKUM_ATFI.findall(_metin())
        self.assertGreaterEqual(len(atiflar), ASGARI_DOKUM_ATFI)
        satirlar = _dokum_satirlari()
        for ad, deger, n in atiflar:
            with self.subTest(atif=f"{ad}={deger} :{n}"):
                self.assertEqual(f"{ad},{deger}", satirlar[int(n) - 1].strip())

    def test_kod_atiflari_satirda_birebir(self):
        atiflar = KOD_ATFI.findall(_metin())
        self.assertGreaterEqual(len(atiflar), ASGARI_KOD_ATFI)
        for metin, yol, n in atiflar:
            with self.subTest(atif=f"{yol}:{n}"):
                self.assertIn(metin, _satirlar(yol)[int(n) - 1])

    def test_kaynak_nobetcisi(self):
        atiflar = _satir_atiflari()
        for yol, n, parca in KAYNAK_NOBETCISI:
            with self.subTest(kaynak=f"{yol}:{n}"):
                self.assertIn((yol, n), atiflar, "kagit bu satira atif yapmiyor")
                self.assertIn(parca, _satirlar(yol)[n - 1])

    def test_benzer_olcum_sayilari_kaynaktan(self):
        h2 = json.loads(H2_OZET.read_text(encoding="utf-8"))["kosumlar"]
        ika = h2["tcp_seri_koprusu_ikago"]
        par = h2["tcp_seri_koprusu_parasut"]
        a6 = _bolum(6)
        self.assertIn(f"{_tr(ika['rtt_ms']['p50'], 2)}/{_tr(ika['rtt_ms']['p95'], 2)} ms", a6)
        self.assertIn(f"{_tr(ika['veri_hizi']['gonderilen_bayt_s'], 1)} B/s", a6)
        self.assertIn(f"{par['veri_hizi']['gonderilen_bayt_s']:.0f} B/s", a6)
        cerceve = ika["veri_hizi"]["gonderilen_bayt"] / h2["tcp_seri_koprusu_ikago"]["rtt_ms"]["ornek"]
        self.assertIn(f"≈ {cerceve:.0f} B", a6)
        vakalar = json.loads(JETSON_OZET.read_text(encoding="utf-8"))["vakalar"]
        pt = [v for v in vakalar if v["ad"] == "pt"]
        self.assertEqual(1, len(pt), "6 Eylul ozetinde tek pt vakasi bekleniyordu")
        toplam = pt[0]["metrikler_ms"]["toplam_ms"]
        p50, p95 = toplam["p50"], toplam["p95"]
        a10 = _bolum(10)
        self.assertIn(f"{p50:.0f}/{p95:.0f} ms", a10)
        self.assertIn(f"{_tr(1000 / p50, 2)}/{_tr(1000 / p95, 2)} FPS", a10)
        # A10 komutundaki model yolu 6 Eylul'de Jetson'da gercekten kosulan dosyayla ayni
        # (depo kokune gore goreli). Once 'models/...' yazilmisti — Jetson'da orada degildi.
        model = pt[0]["model"]
        goreli = model[model.index("jetson_paket/"):]
        self.assertIn(f"--model {goreli} ", a10)


class K6_Hesaplar(unittest.TestCase):
    def _icerir(self, no, *parcalar):
        b = _bolum(no)
        for p in parcalar:
            with self.subTest(bolum=f"A{no}", parca=p):
                self.assertIn(p, b)

    def test_A1_on_pwm_kurali(self):
        fs = int(_dokum_deger("FS_THR_VALUE"))
        self._icerir(1, f"{fs} − 10 = {fs - 10}", f"{fs} + 10 = {fs + 10}",
                     f"`RC_FS_TIMEOUT` = {_dokum_deger('RC_FS_TIMEOUT')} s")

    def test_A2_A3_zaman_asimlari(self):
        t = int(float(_dokum_deger("FS_GCS_TIMEOUT")))
        self._icerir(2, f"{t} − (0…1) = {t - 1}–{t} s", f"≤ {t + 2} s (= {t} s + 2 s pay)")
        lt = int(float(_dokum_deger("BATT_LOW_TIMER")))
        self._icerir(3, f"≤ {lt + 2} s (= `BATT_LOW_TIMER` {lt} s + 2 s pay)")

    def test_A5_heartbeat_penceresi(self):
        import ika_receiver
        hb = inspect.signature(ika_receiver.IkaReceiver.__init__).parameters["hb_timeout"].default
        ar = ks.IHA_HEARTBEAT_ARALIK_S
        self._icerir(5, f"{hb:g} − (0…{ar:g}) = {hb - ar:g}–{hb:g} s", f"≤ {hb + 1:g} s")

    def test_A6_seri_ve_rtt(self):
        bayt_ms = 10 / 57600 * 1000
        seri = 80 * bayt_ms
        self._icerir(6, f"10 / 57600 = {_tr(bayt_ms, 3)} ms/bayt",
                     f"80 × {_tr(bayt_ms, 3)} = {_tr(seri, 1)} ms",
                     f"80 × 8 / 64000 = {80 * 8 / 64000 * 1000:.0f} ms",
                     f"= {_tr(2 * (seri + 10 + seri), 1)} ms", f"ECC ile {_tr(2 * (seri + 20 + seri), 1)} ms",
                     f"80 / {ks.IKA_GO_TEKRAR_ARALIGI_S:g}".replace(".", ",") + f" = {80 / ks.IKA_GO_TEKRAR_ARALIGI_S:.0f} B/s",
                     f"80 / {ks.PARASUT_TEKRAR_ARALIGI_S:g}".replace(".", ",") + f" = {80 / ks.PARASUT_TEKRAR_ARALIGI_S:.0f} B/s",
                     f"= {min(ks.IKA_GO_TEKRAR_ARALIGI_S, ks.PARASUT_TEKRAR_ARALIGI_S) * 1000:.0f} ms")

    def test_A7_gereken_mesafe(self):
        k = ks.SARTNAME_IHA_UB_KENAR_M
        kosegen = k * math.sqrt(2)
        egik = math.hypot(kosegen, 32.0)
        self._icerir(7, f"{k:.0f} × √2 = {_tr(kosegen, 1)} m",
                     f"√({_tr(kosegen, 1)}² + 32²) = {_tr(egik, 1)} m",
                     f"√({k:.0f}² + {k / 2:.0f}²) = {_tr(math.hypot(k, k / 2), 1)} m",
                     f"≥ {_tr(egik, 1)} m")

    def test_A8_istek_hizlari(self):
        c = ks.MAVLINK_AKIS_ISTEK_HIZ_CARPANI
        self._icerir(8, f"{ks.MAVLINK_KONUM_ASGARI_HZ:g} × {c} = {ks.MAVLINK_KONUM_ASGARI_HZ * c:g} Hz",
                     f"{ks.MAVLINK_DURUM_ASGARI_HZ:g} × {c} = {ks.MAVLINK_DURUM_ASGARI_HZ * c:g} Hz")

    def test_A9_fov(self):
        t = 6.287 / 12
        self._icerir(9, f"2 · atan({_tr(t, 4)}) = {_tr(2 * math.degrees(math.atan(t)), 1)}°",
                     f"= {_tr(640 / t * 1.00 / 2.00, 1)} px")

    def test_A10_fps_esigi(self):
        self._icerir(10, f"1000 / 0,61 = {1000 / 0.61:.0f} ms")

    def test_A11_gecikme_toplami(self):
        self._icerir(11, f"130 + 49 = {130 + 49} ms", f"250 + 85 = {250 + 85} ms",
                     f"0,335 + 0,5 = {_tr(0.335 + 0.5, 3)} s")

    def test_A12_itki_orani(self):
        oranlar = " / ".join(f"%{_tr(m / 4 / 2130 * 100, 1)}" for m in (2000, 2500, 3000))
        self._icerir(12, f"m / (4 × 2130 g) = {oranlar}", "2,0 kg → 500 g", "2,5 kg → 625 g",
                     "3,0 kg → 750 g")

    def test_A13_yuksuz_akim(self):
        self._icerir(13, f"4 × 0,7 = {_tr(4 * 0.7, 1)} A")


class K7_ZamanButcesi(unittest.TestCase):
    SATIR = re.compile(r"^\| (\d\d):(\d\d)–(\d\d):(\d\d) \| ([^|]*)\|", re.M)

    def test_tablo_kesintisiz_ve_bolum_sureleriyle_ayni(self):
        satirlar = self.SATIR.findall(_ana_bolum(2))
        self.assertTrue(satirlar, "zaman tablosu bos")
        dk = [(int(a) * 60 + int(b), int(c) * 60 + int(d), is_) for a, b, c, d, is_ in satirlar]
        self.assertEqual(9 * 60, dk[0][0], "gun 09:00'da baslamiyor")
        self.assertEqual(14 * 60, dk[-1][1], "gun 14:00'te bitmiyor")
        for (b1, s1, _), (b2, _, is2) in zip(dk, dk[1:]):
            self.assertEqual(s1, b2, f"bosluk/cakisma: {is2.strip()[:40]}")
        dilim = {}
        for bas, son, is_ in dk:
            self.assertGreater(son, bas)
            for n in re.findall(r"\bA(\d{1,2})\b", is_):
                self.assertNotIn(int(n), dilim, f"A{n} tabloda iki kez")
                dilim[int(n)] = son - bas
        self.assertEqual(set(range(1, TEST_SAYISI + 1)), set(dilim))
        for no, sure, _ in _bolumler():
            with self.subTest(bolum=f"A{no}"):
                self.assertEqual(dilim[no], sure, "baslik suresi tablodaki dilimle ayni degil")


class K8_BicimVeIcerik(unittest.TestCase):
    def test_ana_bolumler_sirali(self):
        self.assertEqual([str(i) for i in range(6)], ANA_BASLIK.findall(_metin()))

    def test_satir_siniri(self):
        n = len(_metin().splitlines())
        self.assertLessEqual(n, AZAMI_SATIR, f"kagit {n} satir > {AZAMI_SATIR}")

    def test_getirilecekler_tam(self):
        b = _ana_bolum(0)
        for p in GETIRILECEKLER:
            with self.subTest(kalem=p):
                self.assertIn(p, b)

    def test_guvenlik(self):
        b = _ana_bolum(1)
        for p in GUVENLIK:
            with self.subTest(parca=p):
                self.assertIn(p, b)
        self.assertIn("ARMING_CHECK", b)
        self.assertIn("ön koşul", _bolum(12).lower())

    def test_A11_kurulum_sirasi(self):
        b = _bolum(11)
        for p in ("192.168.144.25", "192.168.144.11 / .12 / .20 kullanılmaz", "Camera 1",
                  "--kaynak <indeks> --port 8080", "--kamera-url http://127.0.0.1:8080",
                  "T226", "--kamera-etiket", "bugün YOK", "T230", "Air Unit Mini", "Link Status",
                  "DP→HDMI", "USB HDMI yakalama kartı"):
            with self.subTest(parca=p):
                self.assertIn(p, b)
        self.assertLess(b.index("192.168.144.25"), b.index("Camera 1"))
        self.assertLess(b.index("Camera 1"), b.index("--kamera-url"))

    def test_mp_adimlari_A1_A4(self):
        m = _metin()
        self.assertIn("Flight Data → DataFlash Logs → Download DataFlash Log Via Mavlink", m)
        self.assertIn("Flight Data → Messages", m)
        for no in (1, 2, 3, 4):
            with self.subTest(bolum=f"A{no}"):
                b = _bolum(no)
                self.assertIn("M3", b)
                self.assertIn(".bin", b)
                self.assertTrue("Messages" in b or "MSG" in b)


class K9_Sablon(unittest.TestCase):
    SATIR = re.compile(r"^\| A(\d+) \|(.*)$", re.M)

    def test_satirlar_sirali_ve_dosyalar_eslesiyor(self):
        m = SABLON.read_text(encoding="utf-8")
        satirlar = self.SATIR.findall(m)
        self.assertEqual(list(range(1, TEST_SAYISI + 1)), [int(n) for n, _ in satirlar])
        for n, govde in satirlar:
            with self.subTest(satir=f"A{n}"):
                ana = _ana_sonuc_dosyasi(int(n))
                self.assertIsNotNone(ana)
                self.assertIn(Path(ana).name, govde, "sablon bolumun ana sonuc dosyasini anmiyor")
                self.assertIn("[ ] ÖLÇÜLDÜ", govde)
                self.assertIn("[ ] ÖLÇÜLEMEDİ", govde)

    def test_kagit_sablona_isaret_ediyor(self):
        self.assertIn(SONUC_DIZIN + "SONUC_SABLONU.md", _metin())
        self.assertIn(KAGIT.name, SABLON.read_text(encoding="utf-8"))


class K10_UcusLoguYardim(unittest.TestCase):
    BETIK = KOK / "scripts" / "ucus_logu_devrilme.py"

    def test_help_sifir(self):
        r = subprocess.run([sys.executable, "-B", str(self.BETIK), "--help"], cwd=str(KOK),
                           env=ORTAM, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        self.assertEqual(0, r.returncode, r.stdout[-400:])
        self.assertIn("KULLANIM", r.stdout)
        self.assertNotIn("YOK: --help", r.stdout)

    def test_dosya_yoksa_bir(self):
        with tempfile.TemporaryDirectory() as d:
            yok = Path(d) / "yok.bin"
            r = subprocess.run([sys.executable, "-B", str(self.BETIK), str(yok)], cwd=str(KOK),
                               env=ORTAM, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=60)
        self.assertEqual(1, r.returncode)
        self.assertIn("YOK:", r.stdout)


if __name__ == "__main__":
    unittest.main()
