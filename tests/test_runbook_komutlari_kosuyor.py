"""D-421 — RUNBOOK KOMUTLARI GERÇEKTEN KOŞUYOR MU: kopyala-yapıştır kapısı.

NEDEN (ölçülen kusur, 4 Eylül): `SAHA_RUNBOOK.md` §3'ün kopyala-yapıştır bloğu
**ölmüştü**. Codex `iha_komut_alici`ya zorunlu `--izinli-kaynak HOST:PORT`
bayrağı ekledi; runbook'un satırı onu taşımıyordu ve süreç hiç kalkmıyordu:

    iha_komut_alici.py: error: --izinli-kaynak HOST:PORT saha komutlari icin
    zorunlu; kaynak pinsiz ARM/DISARM/PARACHUTE/RTL/LAND kabul edilmez
    EXIT=2

**Neden sinsi:** blok ASİMETRİK ölüyordu. Birinci satır (`iha_inis_yayinci`)
sorunsuz kalkıyor, ikinci satır ölüyordu. Sahada zincir *yarı canlı* görünür —
iniş kanıtı akar ama YKS'nin ARM/DISARM/RTL/LAND/PARAŞÜT düğmeleri hiçbir zaman
ACK almaz. Operatör bir şeyler çalıştığı için sorunu aramaz.

**Ve kusur zaten saha USB'sindeydi:** `scripts/bellek_hazirla.py` runbook'u
`belgeler/` altına kopyalar.

🔴 **Var olan kapı bunu YAKALAYAMADI.** `tests/test_p4_runbook.py` komut
satırlarını "kilitlediğini" ilan ediyordu ama yaptığı şey sabit bir jeton
listesiyle `assertIn` substring aramasıydı; listede `--izinli-kaynak` yoktu.
Komut ÖLÜYKEN kapı **22/22 yeşil** kaldı. (Aynı sınıf: D-415 yazım körlüğü,
D-419 §5 kalıtım körlüğü — ölçüm aletinin kendisi ölçülmemişti.)

Bu kapı substring aramaz: runbook'taki komutu **gerçekten koşar** ve argparse
onu reddediyor mu diye bakar. Bir bayrak zorunlu hâle gelirse ve belge
güncellenmezse kapı düşer.

  T1  runbook'un bash bloklarındaki her depo betiği çağrısı argparse tarafından
      REDDEDİLMİYOR (çıkış 2 + "error:" yok)
  T2  en az bir komut gerçekten sınanıyor (kapı boşa düşmesin — vakumluluk)
  T3  yer tutucu sözlüğü runbook'ta geçen tüm `<...>` biçimlerini kapsıyor
  T4  T1'in açtığı süreç AĞACI kapanıyor: koşumdan sonra nöbet portlarında
      (YKS/İKA/İHA uçları) YENİ UDP dinleyici yok (T210)

🔴 T210 (7 Eylül gecesi) — BU KAPI SÜREÇ SIZDIRIYORDU. T1, `saha_baslat.py yks …`
ve `saha_baslat.py ika …` satırlarını GERÇEKTEN koşar; bunlar `yks_gui` /
`ika_nav`'ı torun süreç olarak açar ve 6 s zaman aşımına kadar yaşar
("süreç KALKTI" = istenen sonuç). `subprocess.run(timeout=6)` zaman aşımında
YALNIZ doğrudan çocuğu öldürüyordu; Windows'ta venv `python.exe` bir
başlatıcı olduğu için torunlar (başlatıcı + gerçek `yks_gui`/`ika_nav`)
yetim kalıyor, UDP 5005/5006'yı tutuyor ve bir SONRAKİ süitte
`test_p8_sim_katmani.test_comms_loopback_gecer` `WinError 10013` ile
düşüyordu (D-427 ve D-430'da "ortam kusuru" sanılan şeyin kökü; kanıt:
`results/gece_20260907/sizinti_surecleri_0207.txt` — başlama saatleri süit
koşumlarıyla 6 s arayla çakışıyor). Artık her koşum `surec_nobetcisi.
kos_agac_kapat` ile yapılır: zaman aşımında ağaç `taskkill /T /F` ile
bütün olarak kapatılır; T4 bunu portla ÖLÇER. `--help` ile koşmak
yeterli DEĞİLDİR: argparse `-h`'yi zorunlu-bayrak denetiminden ÖNCE
işler ve 0 ile çıkar — "bayrak zorunlu oldu, belge güncellenmedi" kusuru
(D-421 §1) görünmez olurdu; kapının amacı korunmuştur.
"""

import re
import sys
import time
import unittest
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
RUNBOOK = KOK / "SAHA_RUNBOOK.md"
PY = Path(sys.executable)

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import surec_nobetcisi  # noqa: E402

#: Süreç "kalktı ve dinliyor" sayılmadan önce beklenen süre (s). Tk GUI'nin
#: açılışı birkaç saniye alır; argparse reddi ise anında gelir.
KALKIS_ZAMAN_ASIMI_S = 6
#: Ağaç kapatıldıktan sonra portun serbest kalması için tanınan azami süre (s).
#: Sızıntı KALICIDIR; bu süre yalnız kapanış gecikmesini sızıntıdan ayırır.
PORT_SERBEST_BEKLEME_S = 5.0

# Runbook yer tutucuları → sınama değerleri. Gerçek adres değil, argparse'ın
# kabul edeceği BİÇİMDE değerler; kapı bağlantı değil SÖZ DİZİMİ ölçer.
YER_TUTUCU = {
    "<YKS_IP>": "10.0.0.1",
    "<IKA_IP>": "10.0.0.2",
    "<IHA_IP>": "10.0.0.3",
    "<JETSON_IP>": "10.0.0.4",
    "<COMx>": "COM5",
    "1455N": "14550",
}

# Bu betikler runbook'ta çağrılır ve argparse'ı sınanır.
DEPO_BETIKLERI = re.compile(
    r"(?:python3?\s+)?((?:jetson_paket/kod|comms|codes|scripts|simulation/scripts)"
    r"/[\w/]+\.py)")


def _bash_bloklari(metin: str):
    """Runbook'taki ```bash ... ``` blokları."""
    return re.findall(r"```bash\n(.*?)```", metin, re.S)


def _komutlar(metin: str):
    """Depo betiği çağıran, satır devamları birleştirilmiş komutlar."""
    bulunan = []
    for blok in _bash_bloklari(metin):
        # ters bölü ile satır devamlarını birleştir
        duz = re.sub(r"\\\s*\n\s*", " ", blok)
        for satir in duz.splitlines():
            satir = satir.strip()
            if not satir or satir.startswith("#"):
                continue
            m = DEPO_BETIKLERI.search(satir)
            if m and (KOK / m.group(1)).is_file():
                bulunan.append((m.group(1), satir))
    return bulunan


def _argumanlar(satir: str, betik: str):
    """Komut satırından betikten SONRAKİ argümanlar, yer tutucular çözülmüş."""
    kuyruk = satir.split(betik, 1)[1]
    # Satır sonu yorumu argüman DEĞİLDİR: `--komutlar   # kartı yazdır`
    # kabuğa gitmez ama naif bölme onu argparse'a yollar ve yanlış alarm üretir.
    kuyruk = re.split(r"\s#", kuyruk, maxsplit=1)[0]
    for k, v in YER_TUTUCU.items():
        kuyruk = kuyruk.replace(k, v)
    return [x for x in kuyruk.split() if x]


class RunbookKomutlari(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metin = RUNBOOK.read_text(encoding="utf-8")
        cls.komutlar = _komutlar(cls.metin)
        # T4 için taban: koşumdan ÖNCE nöbet portlarını kim dinliyor?
        # (Kullanıcının canlı YKS'si buradaysa taban ona sahiptir; nöbetçi
        # yalnız YENİ dinleyiciyi sızıntı sayar.)
        cls.dinleyenler_once = surec_nobetcisi.udp_dinleyenler()

    def test_T1_hicbir_runbook_komutu_argparse_tarafindan_REDDEDILMIYOR(self):
        olu = []
        for betik, satir in self.komutlar:
            args = _argumanlar(satir, betik)
            # Zaman aşımı = süreç KALKTI ve dinlemeye başladı (çıkış 124) —
            # istediğimiz budur; ağaç `kos_agac_kapat` içinde KESİN kapanır.
            cikis, _out, hata = surec_nobetcisi.kos_agac_kapat(
                [str(PY), "-B", str(KOK / betik), *args],
                timeout=KALKIS_ZAMAN_ASIMI_S, cwd=str(KOK))
            if cikis == 2 and "error:" in hata:
                ilk = next((x for x in hata.splitlines()
                            if "error:" in x), hata[:160])
                olu.append(f"{betik}\n      args: {' '.join(args)}\n"
                           f"      {ilk.strip()[:150]}")
        self.assertEqual(
            [], olu,
            "SAHA_RUNBOOK.md'deki komut(lar) BUGÜN KOŞMUYOR — bir bayrak "
            "zorunlu hâle gelmiş ve belge güncellenmemiş:\n    "
            + "\n    ".join(olu))

    def test_T2_kapi_bos_degil_en_az_uc_komut_sinaniyor(self):
        """Vakumluluk: blok ayrıştırıcı bozulursa kapı sessizce boşalmasın."""
        self.assertGreaterEqual(
            len(self.komutlar), 3,
            f"runbook'tan yalnız {len(self.komutlar)} komut çıkarıldı — "
            "blok ayrıştırıcı bozulmuş olabilir")
        betikler = {b for b, _ in self.komutlar}
        self.assertIn("jetson_paket/kod/iha_komut_alici.py", betikler,
                      "kusurun çıktığı komut kapının kapsamında DEĞİL")

    def test_T3_yer_tutucular_kapsamli(self):
        """Runbook'ta çözülemeyen `<...>` yer tutucusu kalmamalı."""
        eksik = set()
        for betik, satir in self.komutlar:
            for x in _argumanlar(satir, betik):
                for m in re.findall(r"<[^>\s]+>", x):
                    if m not in YER_TUTUCU:
                        eksik.add(f"{betik}: {m}")
        self.assertEqual(
            set(), eksik,
            "runbook'ta sözlükte olmayan yer tutucu var; kapı onu argparse'a "
            "ham gönderir ve yanlış alarm/yanlış geçiş üretir:\n  "
            + "\n  ".join(sorted(eksik)))

    def test_T4_kosum_sonrasi_nobet_portlarinda_YENI_dinleyici_YOK(self):
        """T210: T1'in açtığı `yks_gui`/`ika_nav` torunları ölmüş olmalı.

        Yöntem sayım değil KÜME farkıdır (`netstat -ano -p udp`): koşumdan
        önce olmayan (adres, PID) çifti varsa sızıntıdır. Sızıntı kalıcı
        olduğu için kısa bir kapanış beklemesi onu gizleyemez.
        """
        if self.dinleyenler_once is None:
            self.skipTest("netstat -ano yalnız Windows'ta ölçülür — ÖLÇÜLEMEDİ")
        son = time.monotonic() + PORT_SERBEST_BEKLEME_S
        while True:
            yeni = surec_nobetcisi.udp_dinleyenler() - self.dinleyenler_once
            if not yeni or time.monotonic() >= son:
                break
            time.sleep(0.25)
        rapor = [f"{adr} PID {pid}: {surec_nobetcisi.surec_komutu(pid)[:160]}"
                 for adr, pid in sorted(yeni)]
        self.assertEqual(
            [], rapor,
            "runbook kapısı süreç SIZDIRDI — koşumdan sonra nöbet portlarında "
            "yeni UDP dinleyici var (bir sonraki süit WinError 10013 ile "
            "düşer; D-427/D-430 kökü):\n  " + "\n  ".join(rapor))


if __name__ == "__main__":
    unittest.main()
