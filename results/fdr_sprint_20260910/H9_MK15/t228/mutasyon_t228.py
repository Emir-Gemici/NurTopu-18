"""T228 mutasyon kosucusu — her mutasyonu uygular, `tests/test_isaretli_gosterici.py`'yi kosar,
dosyalari BAYT-ES geri yukler (sha256 ile dogrulanir).

Gosterici mutasyonlari `scripts/isaretli_gosterici.py` kanonik kopyasina VE
`jetson_paket/kod/isaretli_gosterici.py` aynasina BIRLIKTE uygulanir (ayna bayt-es testi mutanti
bos yere yakalamasin — hedef test DUSMELI). Betik mutasyonlari `jetson_paket/jetson_baslat.sh`'e.
Satir sonu korunur (calisma kopyasi autocrlf ile CRLF olabilir).

Her mutasyonun HEDEF testi yazilidir: "YAKALANDI" yalniz hedef test dustuyse yazilir; baska
testlerin dusmesi ayrica listelenir. M5 (DISPLAY denetimi yok) Windows'ta 0,5 s tam ekran pencere
acar — beklenen.

KOSUM (depo kokunden; baska surec bu dosyalari okurken KOSMA):
  O:/navitas-local-train/venv/Scripts/python.exe -B \
      results/fdr_sprint_20260910/H9_MK15/t228/mutasyon_t228.py
"""
import hashlib
import re
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
KOK = Path(__file__).resolve().parents[4]
PY = sys.executable
TEST = "test_isaretli_gosterici.py"
GOSTERICI = (KOK / "scripts" / "isaretli_gosterici.py",
             KOK / "jetson_paket" / "kod" / "isaretli_gosterici.py")
BETIK = (KOK / "jetson_paket" / "jetson_baslat.sh",)

MUTASYONLAR = [
    ("M1 bayat esigi kaldirildi (BAYAT dali hic calismaz)", GOSTERICI,
     "    if yas > bayat_esigi_s:\n        return EkranDurumu(DURUM_BAYAT,",
     "    if False:\n        return EkranDurumu(DURUM_BAYAT,",
     "test_G1_taze_bayat_yok"),
    ("M2 yasak IP kontrolu kaldirildi (SIYI .11/.12/.20/.25 kabul)", GOSTERICI,
     "    if s in SIYI_SABIT_IP:\n",
     "    if False:\n",
     "test_G5_SIYI_sabitleri_REDDEDILIR"),
    ("M3 GORUNTU YOK ekrani eski kareyi ciziyor", GOSTERICI,
     "    tuval = np.empty((yukseklik, genislik, 3), np.uint8)\n    tuval[:] = KIRMIZI_ZEMIN\n",
     "    tuval = np.empty((yukseklik, genislik, 3), np.uint8)\n    tuval[:] = KIRMIZI_ZEMIN\n"
     "    if kare is not None:\n        tuval = sigdir(kare, genislik, yukseklik)\n",
     "test_G2_GORUNTU_YOK_eski_kareyi_ASLA_cizmez"),
    ("M4 ayni sira/govde tazeligi uzatiyor", GOSTERICI,
     "                onceki_hata, self.hata = self.hata, None\n                self.basari += 1\n"
     "            if onceki_hata is not None:\n                self.log(\"yayin yanit veriyor",
     "                onceki_hata, self.hata = self.hata, None\n                self.basari += 1\n"
     "                self.son_taze_t = self.saat()\n"
     "            if onceki_hata is not None:\n                self.log(\"yayin yanit veriyor",
     "test_G3_ayni_sira_tazelik_UZATMAZ_bayat_sonra_yok"),
    ("M5 x11 DISPLAY denetimi yok", GOSTERICI,
     "    if ortam.get(\"DISPLAY\"):\n        return None\n    ek = \"\"\n",
     "    return None\n    ek = \"\"\n",
     "test_G6_x11_DISPLAY_yoksa_cikis_2_pencere_acilmaz"),
    ("M6 drm gozetmeni BAYAT'ta video borusunu durdurmuyor", GOSTERICI,
     "            if (d2.durum == DURUM_CANLI) != canli:\n",
     "            if (d2.durum != DURUM_YOK) != canli:\n",
     "test_G7_yok_kirmizi_canli_video_bayatta_video_DURUR"),
    ("M7 jetson_baslat --isaretli-yayin bayragini vermiyor", BETIK,
     "if [ \"$GOSTERICI_KIP\" != kapali ]; then RPI_EK_ARGS=\"$RPI_EK_ARGS --isaretli-yayin "
     "$ISARETLI_YAYIN\"; fi\n",
     ":\n",
     "test_G10_x11_T227siz_paket_YOK_exit_3_bayrak_verilir"),
    ("M8 --kur/--dogrudan T227 denetimi yok", BETIK,
     "    isaretli_destek_var \"$y\" \\\n      || hata \"GOSTERICI_KIP=",
     "    true \\\n      || hata \"GOSTERICI_KIP=",
     "test_G10_kur_T227siz_kurulu_rpi_HATA_hicbir_systemctl_yok"),
    ("M9 ISARETLI_YAYIN loopback denetimi yok", BETIK,
     "  *) hata \"ISARETLI_YAYIN='$ISARETLI_YAYIN': yalniz 127.0.0.1:<port>",
     "  *) _iy_port=8081; : \"ISARETLI_YAYIN='$ISARETLI_YAYIN': yalniz 127.0.0.1:<port>",
     "test_G10_gecersiz_kip_yayin_port_cakismasi_fail_closed"),
    ("M10 kuru gosterici [YOK] satirlarini saymiyor", BETIK,
     "  yok=$((yok + $(printf '%s\\n' \"$g\" | grep -c '^\\[YOK\\]' || true)))\n",
     "  :\n",
     "test_G10_x11_T227siz_paket_YOK_exit_3_bayrak_verilir"),
]


def kos():
    p = subprocess.run([PY, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", "tests",
                        "-p", TEST], cwd=KOK, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", timeout=1200)
    cikti = p.stdout + p.stderr
    ran = re.search(r"Ran (\d+) tests?", cikti)
    satirlar = [s for s in cikti.strip().splitlines() if s.strip()]
    son = satirlar[-1] if satirlar else "?"
    dusen = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+)", cikti, re.M)))
    return p.returncode, (ran.group(1) if ran else "?"), son, dusen


def uygula(dosyalar, eski, yeni, orijinal):
    for yol in dosyalar:
        ham = orijinal[yol]
        metin = ham.decode("utf-8")
        crlf = "\r\n" in metin
        n = metin.replace("\r\n", "\n")
        sayi = n.count(eski)
        if sayi != 1:
            raise RuntimeError("{}: mutasyon metni {} kez bulundu (1 olmali)".format(yol.name, sayi))
        n = n.replace(eski, yeni, 1)
        yol.write_bytes((n.replace("\n", "\r\n") if crlf else n).encode("utf-8"))


tum = sorted({y for _a, ds, _e, _y, _h in MUTASYONLAR for y in ds})
orijinal = {y: y.read_bytes() for y in tum}
sha0 = {y: hashlib.sha256(b).hexdigest() for y, b in orijinal.items()}
yakalanan = 0
try:
    for ad, dosyalar, eski, yeni, hedef in MUTASYONLAR:
        try:
            uygula(dosyalar, eski, yeni, orijinal)
        except RuntimeError as exc:
            print("{}: UYGULANAMADI — {}".format(ad, exc))
            continue
        try:
            kod, ran, son, dusen = kos()
        finally:
            for y in dosyalar:
                y.write_bytes(orijinal[y])
        tuttu = hedef in dusen
        yakalanan += 1 if tuttu else 0
        print("{}: cikis={} ran={} son={!r} -> {}; hedef={} ({}); dusen={}".format(
            ad, kod, ran, son, "YAKALANDI" if tuttu else "KACTI", hedef,
            "DUSTU" if tuttu else "GECTI", dusen), flush=True)
finally:
    for y, b in orijinal.items():
        y.write_bytes(b)
esit = all(hashlib.sha256(y.read_bytes()).hexdigest() == sha0[y] for y in tum)
print("geri yukleme sha esit: {} ({})".format(
    esit, ", ".join("{}={}".format(y.name, sha0[y][:12]) for y in tum)))
print("OZET: {}/{} mutasyon hedef testle yakalandi".format(yakalanan, len(MUTASYONLAR)))
kod, ran, son, dusen = kos()
print("TEMIZ KOSUM (mutasyonsuz): cikis={} ran={} son={!r} dusen={}".format(kod, ran, son, dusen))
